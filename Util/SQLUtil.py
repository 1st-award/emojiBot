import os
import sqlite3

back_slash = "\\"
conn = sqlite3.connect(f"{os.getcwd().replace(back_slash, '/')}/Emoji/emoji.db", isolation_level=None)
cursor = conn.cursor()


def insert_guild(_guildID: int):
    print(f"insert {_guildID}...")
    cursor.execute("INSERT INTO guild(guild) VALUES(?)", (_guildID,))
    print(f"insert success")


def remove_guild(_guildID: int):
    print(f"remove {_guildID}...")
    cursor.execute("DELETE FROM guild WHERE guild=?", (_guildID,))
    print(f"remove success")


def register_emoji(_filename: str, _emoji_command: str, _guildID: int):
    print("searching before register...")
    search_result = emoji_search(_emoji_command, _guildID)
    print("searching result: ", type(search_result))
    if search_result is not None:
        raise FileExistsError("이미 등록되어있는 명령어입니다.")
    print(f"{_filename} insert to emoji table...")
    cursor.execute("INSERT INTO emoji(guild, path, command) VALUES(?, ?, ?)", (_guildID, _filename, _emoji_command))
    print(f"{_filename} insert success")


def emoji_remove(_emoji_command: str, _guildID: int):
    print(f"remove {_emoji_command} of {_guildID}...")
    cursor.execute("DELETE FROM emoji WHERE guild=? AND command=?", (_guildID, _emoji_command))
    print("remove success")


def emoji_search(_emoji_command, _guildID: int):
    cursor.execute("SELECT path FROM emoji WHERE guild=? AND command LIKE ?", (_guildID, f"%{_emoji_command}%"))
    search_result = cursor.fetchone()
    print("return search result...")
    print(search_result)
    return search_result


def load_emoji_global_emoji(_guildID: int):
    cursor.execute("SELECT * FROM emoji WHERE guild=?", _guildID)
    result_arg = cursor.fetchall()
    print("return ")
    return result_arg


def emoji_global_emoji_search(_emoji_command):
    print(f"global_emoji.db searching {_emoji_command}...")
    cursor.execute("SELECT path FROM emoji WHERE guild=-1 and command='%s'" % _emoji_command)
    result_arg = cursor.fetchone()
    print(f"global_emoji.db search complete and close...")
    print("return tuple...")
    return result_arg


def emoji_search_all(_guildID: int):
    print(f"{_guildID}.db searching all emoji...")
    cursor.execute("SELECT * FROM emoji WHERE guild=?", (_guildID,))
    result_arg = cursor.fetchall()
    if len(result_arg) == 0:
        raise FileNotFoundError("등록된 이모지 명령어가 없습니다. `!등록`을 통해 이모지를 등록해주세요.")
    print("return tuple list...")
    return result_arg
