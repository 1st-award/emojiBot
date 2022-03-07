# TODO asqlite 또는 asqlite3 이용해서 비동기 db접근 만들기
import sqlite3
import os


def new_guild_join(_guildID: int):
    print(f"{_guildID}.db 생성")
    f = open(f"Guilds/{_guildID}.db", 'w')
    print(f"{_guildID}.db 생성 완료")
    f.close()

    print(f"Emoji/{_guildID}폴더 생성")
    os.mkdir(f"Emoji/{_guildID}")
    print(f"Emoji/{_guildID}폴더 생성 완료")

    print(f"{_guildID}.db 초기 설정")
    new_db_setting(_guildID)


def new_db_setting(_guildID: int):
    print(f"{_guildID}.db open...")
    conn = sqlite3.connect(f"Guilds/{_guildID}.db", isolation_level=None)
    cursor = conn.cursor()

    print(f"{_guildID}.db table create...")
    cursor.execute("CREATE TABLE IF NOT EXISTS emoji \
                   (name text, command text PRIMARY KEY)")
    print(f"{_guildID}.db close...")
    conn.close()


def emoji_register(_filename: str, _emoji_command: str, _guildID: int):
    print("searching before register...")
    search_result = emoji_search(_emoji_command, _guildID)
    print("searching result: ", type(search_result))
    if search_result is not None:
        raise FileExistsError("이미 등록되어있는 명령어입니다.")

    print(f"{_guildID}.db open...")
    conn = sqlite3.connect(f"Guilds/{_guildID}.db", isolation_level=None)
    cursor = conn.cursor()

    print(f"{_guildID}.db insert arguments...")
    cursor.execute("INSERT INTO emoji(name, command) \
                    VALUES(?,?)", (_filename, _emoji_command))

    print(f"{_guildID}.db insert complete and close...")
    conn.close()


def emoji_remove(_emoji_command: str, _guildID: int):
    print(f"{_guildID}.db open...")
    conn = sqlite3.connect(f"Guilds/{_guildID}.db", isolation_level=None)
    cursor = conn.cursor()

    print(f"{_guildID}.db delete arguments...")
    cursor.execute("DELETE FROM emoji WHERE command=:command", {'command': _emoji_command})

    print(f"{_guildID}.db delete complete and close...")
    conn.close()


def emoji_search(_emoji_command, _guildID: int):
    print(f"{_guildID}.db open...")
    conn = sqlite3.connect(f"Guilds/{_guildID}.db", isolation_level=None)
    cursor = conn.cursor()

    print(f"{_guildID}.db searching {_emoji_command}...")
    cursor.execute("SELECT * FROM emoji WHERE command='%s'" % _emoji_command)
    result_arg = cursor.fetchone()

    print(f"{_guildID}.db search complete and close...")
    conn.close()

    print("return tuple...")
    return result_arg


def emoji_global_emoji_search(_emoji_command):
    print("global_emoji.db open...")
    conn = sqlite3.connect("")

    conn = sqlite3.connect(f"Guilds/funzEmoji.db", isolation_level=None)
    cursor = conn.cursor()

    print(f"global_emoji.db searching {_emoji_command}...")
    cursor.execute("SELECT * FROM emoji WHERE command='%s'" % _emoji_command)
    result_arg = cursor.fetchone()

    print(f"global_emoji.db search complete and close...")
    conn.close()

    print("return tuple...")
    return result_arg


def emoji_search_all(_guildID: int):
    print(f"{_guildID}.db open...")
    conn = sqlite3.connect(f"Guilds/{_guildID}.db", isolation_level=None)
    cursor = conn.cursor()

    print(f"{_guildID}.db searching all emoji...")
    cursor.execute("SELECT * FROM emoji")
    result_arg = cursor.fetchall()

    print(f"{_guildID}.db search complete and close...")
    conn.close()

    if len(result_arg) == 0:
        raise FileNotFoundError("등록된 이모지 명령어가 없습니다. `!등록`을 통해 이모지를 등록해주세요.")

    print("return tuple list...")
    return result_arg


async def emoji_db_remove(_guildID: int):
    print(f"removing {_guildID}.db...")
    os.remove(f"Guilds/{_guildID}.db")
    print(f"remove {_guildID}.db complete")
