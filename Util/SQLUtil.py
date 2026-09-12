"""SQLite access with bound parameters and per-operation transactions."""
import logging
import random
import sqlite3
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)
DB_PATH = Path(__file__).resolve().parents[1] / "Emoji" / "emoji.db"
GLOBAL_GUILD_ID = -1


@contextmanager
def connection():
    # Fail on missing databases instead of silently creating an empty one.
    """외래 키 검사를 활성화한 SQLite 연결을 제공하는 컨텍스트 관리자이다.

    기존 DB만 열며 정상 종료 시 커밋, 예외 시 롤백하고 항상 연결을 닫는다.
    SQLite 오류는 로그에 기록한 뒤 호출자에게 다시 전달한다.
    """
    db = sqlite3.connect(Path(DB_PATH).resolve().as_uri() + "?mode=rw", uri=True, timeout=5)
    try:
        db.execute("PRAGMA foreign_keys = ON")
        with db:
            yield db
    except sqlite3.Error:
        logger.exception("SQLite operation failed")
        raise
    finally:
        db.close()


def set_foreign_key():
    """기존 호출과의 호환성을 위해 연결을 열고 닫는다. 모든 연결은 이미 외래 키를 활성화한다."""
    with connection():
        pass


def insert_guild(_guildID: int):
    """서버 ID를 guild 테이블에 등록한다. 이미 등록된 서버는 그대로 유지한다."""
    with connection() as db:
        db.execute("INSERT INTO guild(guild) VALUES(?) ON CONFLICT(guild) DO NOTHING", (_guildID,))
    logger.info("Guild registered: guild_id=%s", _guildID)


def remove_guild(_guildID: int):
    """서버 행을 삭제하고 외래 키의 연쇄 삭제 규칙에 따라 관련 DB 데이터를 제거한다."""
    with connection() as db:
        db.execute("DELETE FROM guild WHERE guild=?", (_guildID,))
    logger.info("Guild removed: guild_id=%s", _guildID)


def register_emoji(_filename: str, _emoji_command: str, _guildID: int):
    """서버에 파일명과 명령어의 매핑을 등록한다. 실제 이미지 파일은 수정하지 않는다.

    빈 명령어는 ValueError, 정확히 일치하는 중복 명령어는 FileExistsError로
    거부한다. 중복 확인과 삽입은 하나의 쓰기 트랜잭션에서 수행한다.
    """
    if not _emoji_command.strip():
        raise ValueError("명령어를 입력해주세요.")
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT 1 FROM emoji WHERE guild=? AND command=?", (_guildID, _emoji_command)).fetchone():
            raise FileExistsError("이미 등록된 명령어입니다.")
        db.execute("INSERT INTO emoji(guild, path, command) VALUES(?, ?, ?)", (_guildID, _filename, _emoji_command))
    logger.info("Emoji registered: guild_id=%s", _guildID)


def emoji_remove(_emoji_command: str, _guildID: int):
    """서버 ID와 명령어가 정확히 일치하는 DB 행을 삭제한다. 실제 이미지 파일은 유지한다."""
    with connection() as db:
        db.execute("DELETE FROM emoji WHERE guild=? AND command=?", (_guildID, _emoji_command))
    logger.info("Emoji removed: guild_id=%s", _guildID)


def emoji_search_exact(_emoji_command: str, _guildID: int):
    """서버에서 명령어가 정확히 일치하는 (파일명,) 튜플을 찾는다. 없으면 None을 반환한다."""
    with connection() as db:
        return db.execute("SELECT path FROM emoji WHERE guild=? AND command=?", (_guildID, _emoji_command)).fetchone()


def emoji_search(_emoji_command: str, _guildID: int):
    """서버 내 명령어를 부분 검색해 (파일명,) 튜플 또는 None을 반환한다.

    빈 검색어는 무시하고 SQL 와일드카드는 일반 문자로 취급한다. 정확한 일치를
    우선하며 나머지는 명령어 순서로 정렬해 첫 결과를 선택한다.
    """
    if not _emoji_command:
        return None
    # Keep substring/alias search, treating SQL wildcard characters literally.
    pattern = "%" + _emoji_command.replace("!", "!!").replace("%", "!%").replace("_", "!_") + "%"
    with connection() as db:
        result = db.execute(
            "SELECT path FROM emoji WHERE guild=? AND command LIKE ? ESCAPE '!' "
            "ORDER BY (command=?) DESC, command LIMIT 1",
            (_guildID, pattern, _emoji_command),
        ).fetchone()
    logger.debug("Emoji lookup: guild_id=%s found=%s", _guildID, result is not None)
    return result


def load_emoji_global_emoji():
    """공용 서버(-1)의 (서버 ID, 파일명, 명령어) 목록을 반환한다. 없으면 빈 목록을 반환한다."""
    return emoji_search_all(GLOBAL_GUILD_ID, allow_empty=True)


def emoji_global_emoji_search(_emoji_command):
    """공용 이모지 명령어를 부분 검색해 (파일명,) 튜플 또는 None을 반환한다."""
    return emoji_search(_emoji_command, GLOBAL_GUILD_ID)


def emoji_search_all(_guildID: int, *, allow_empty=False):
    """서버의 (서버 ID, 파일명, 명령어) 행을 명령어순으로 반환한다.

    목록이 비어 있으면 기본적으로 FileNotFoundError를 발생시킨다.
    allow_empty=True이면 빈 목록을 그대로 반환한다.
    """
    with connection() as db:
        rows = db.execute("SELECT guild, path, command FROM emoji WHERE guild=? ORDER BY command", (_guildID,)).fetchall()
    if not rows and not allow_empty:
        raise FileNotFoundError("등록된 이모지가 없습니다. `/등록`으로 등록해주세요.")
    return rows


def random_emoji(_guildID: int):
    """서버와 공용 이모지에서 무작위 (파일명, 서버 ID)를 반환한다. 후보가 없으면 None이다."""
    with connection() as db:
        rows = db.execute("SELECT path, guild FROM emoji WHERE guild IN (?, ?)", (_guildID, GLOBAL_GUILD_ID)).fetchall()
    return random.choice(rows) if rows else None


def emoji_insert_all(_guildID: int, emoji_args: list):
    """(서버 ID, 파일명, 명령어) 행 목록을 하나의 트랜잭션으로 추가한다.

    모든 행의 서버 ID가 _guildID와 같아야 하며, 다르면 ValueError를 발생시킨다.
    삽입 도중 실패하면 이번 작업의 삽입 전체를 롤백한다.
    """
    if any(row[0] != _guildID for row in emoji_args):
        raise ValueError("대상 서버가 일치하지 않습니다.")
    with connection() as db:
        db.executemany("INSERT INTO emoji(guild, path, command) VALUES(?, ?, ?)", emoji_args)
    logger.info("Emojis inserted: guild_id=%s count=%s", _guildID, len(emoji_args))


def replace_emoji(_guildID: int, emoji_args: list):
    """대상 서버의 이모지 매핑을 emoji_args 행 목록으로 일괄 교체한다.

    행 형식은 (서버 ID, 파일명, 명령어)이며 대상이 다르면 ValueError를 발생시킨다.
    삭제와 삽입은 함께 롤백할 수 있고 길드 행·점수·이미지 파일은 수정하지 않는다.
    """
    if any(row[0] != _guildID for row in emoji_args):
        raise ValueError("대상 서버가 일치하지 않습니다.")
    with connection() as db:
        db.execute("DELETE FROM emoji WHERE guild=?", (_guildID,))
        db.executemany("INSERT INTO emoji(guild, path, command) VALUES(?, ?, ?)", emoji_args)
    logger.info("Emojis replaced: guild_id=%s count=%s", _guildID, len(emoji_args))
