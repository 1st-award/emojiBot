import discord
import os
import shutil
from imgpy import Img
from PIL import Image


async def emoji_save(_emoji: discord.Attachment, _guildID: int):
    print("emoji save...")
    await _emoji.save(f"Emoji/{_guildID}/{_emoji.filename}")
    print("emoji save complete")

    if not _emoji.filename.endswith(".gif"):
        emoji_resize_normal(_emoji.filename, _guildID)
    else:
        emoji_resize_gif(_emoji.filename, _guildID)


async def emoji_remove(_emoji_filename: str, _guildID: int):
    print("emoji remove...")
    os.remove(f"Emoji/{_guildID}/{_emoji_filename}")
    print("emoji remove complete...")


async def emoji_dir_remove(_guildID: int):
    print(f"removing emoji dir {_guildID}...")
    shutil.rmtree(f"Emoji/{_guildID}")
    print(f"remove {_guildID} complete")


def emoji_resize_normal(_emoji_filename: str, _guildID: int):
    print(f"normal resizing {_emoji_filename}...")
    img = Image.open(f'Emoji/{_guildID}/{_emoji_filename}')
    img_resize = img.resize((int(128), int(128)))
    img_resize.save(f'Emoji/{_guildID}/{_emoji_filename}')
    print(f"normal resizing {_emoji_filename} complete...")


def emoji_resize_gif(_emoji_filename: str, _guildID: int):
    print(f"gif resizing {_emoji_filename}...")
    gif = Img(fp=f'Emoji/{_guildID}/{_emoji_filename}')
    gif.thumbnail(size=(128, 128))
    gif.save(fp=f'Emoji/{_guildID}/{_emoji_filename}')
    print(f"gif resizing {_emoji_filename} complete...")


def is_support_format(_emoji_filename: str):
    support_format_list = ["jpg", "png", "gif"]

    for support_format in support_format_list:
        if _emoji_filename.endswith(support_format):
            return True

    raise NotImplementedError("지원하지 않는 파일입니다.")
