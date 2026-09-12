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
    """Compatibility entry point; every connection already enforces foreign keys."""
    with connection():
        pass


def insert_guild(_guildID: int):
    with connection() as db:
        db.execute("INSERT INTO guild(guild) VALUES(?) ON CONFLICT(guild) DO NOTHING", (_guildID,))
    logger.info("Guild registered: guild_id=%s", _guildID)


def remove_guild(_guildID: int):
    with connection() as db:
        db.execute("DELETE FROM guild WHERE guild=?", (_guildID,))
    logger.info("Guild removed: guild_id=%s", _guildID)


def register_emoji(_filename: str, _emoji_command: str, _guildID: int):
    if not _emoji_command.strip():
        raise ValueError("명령어를 입력해주세요.")
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT 1 FROM emoji WHERE guild=? AND command=?", (_guildID, _emoji_command)).fetchone():
            raise FileExistsError("이미 등록된 명령어입니다.")
        db.execute("INSERT INTO emoji(guild, path, command) VALUES(?, ?, ?)", (_guildID, _filename, _emoji_command))
    logger.info("Emoji registered: guild_id=%s", _guildID)


def emoji_remove(_emoji_command: str, _guildID: int):
    with connection() as db:
        db.execute("DELETE FROM emoji WHERE guild=? AND command=?", (_guildID, _emoji_command))
    logger.info("Emoji removed: guild_id=%s", _guildID)


def emoji_search_exact(_emoji_command: str, _guildID: int):
    with connection() as db:
        return db.execute("SELECT path FROM emoji WHERE guild=? AND command=?", (_guildID, _emoji_command)).fetchone()


def emoji_search(_emoji_command: str, _guildID: int):
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
    return emoji_search_all(GLOBAL_GUILD_ID, allow_empty=True)


def emoji_global_emoji_search(_emoji_command):
    return emoji_search(_emoji_command, GLOBAL_GUILD_ID)


def emoji_search_all(_guildID: int, *, allow_empty=False):
    with connection() as db:
        rows = db.execute("SELECT guild, path, command FROM emoji WHERE guild=? ORDER BY command", (_guildID,)).fetchall()
    if not rows and not allow_empty:
        raise FileNotFoundError("등록된 이모지가 없습니다. `/등록`으로 등록해주세요.")
    return rows


def random_emoji(_guildID: int):
    with connection() as db:
        rows = db.execute("SELECT path, guild FROM emoji WHERE guild IN (?, ?)", (_guildID, GLOBAL_GUILD_ID)).fetchall()
    return random.choice(rows) if rows else None


def emoji_insert_all(_guildID: int, emoji_args: list):
    if any(row[0] != _guildID for row in emoji_args):
        raise ValueError("대상 서버가 일치하지 않습니다.")
    with connection() as db:
        db.executemany("INSERT INTO emoji(guild, path, command) VALUES(?, ?, ?)", emoji_args)
    logger.info("Emojis inserted: guild_id=%s count=%s", _guildID, len(emoji_args))


def replace_emoji(_guildID: int, emoji_args: list):
    if any(row[0] != _guildID for row in emoji_args):
        raise ValueError("대상 서버가 일치하지 않습니다.")
    with connection() as db:
        db.execute("DELETE FROM emoji WHERE guild=?", (_guildID,))
        db.executemany("INSERT INTO emoji(guild, path, command) VALUES(?, ?, ?)", emoji_args)
    logger.info("Emojis replaced: guild_id=%s count=%s", _guildID, len(emoji_args))
