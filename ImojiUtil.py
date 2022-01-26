import discord
import GIFConvert
import os
import shutil
from PIL import Image


async def emoji_save(_emoji: discord.Attachment, _guildID: int):
    print("emoji save...")
    await _emoji.save(f"Emoji/{_guildID}/{_emoji.filename}")
    print("emoji save complete")

    if not _emoji.filename.endswith(".gif"):
        emoji_resize_normal(_emoji.filename, _guildID)
    else:
        emoji_resize_gif(_emoji.filename, _guildID)


def emoji_remove(_emoji_filename: str, _guildID: int):
    print("emoji remove...")
    os.remove(f"Emoji/{_guildID}/{_emoji_filename}")
    print("emoji remove complete...")


def emoji_dir_remove(_guildID: int):
    print(f"removing emoji dir {_guildID}...")
    shutil.rmtree(f"Emoji/{_guildID}")
    print(f"remove {_guildID} complete")


# TODO 일반 사진도 변환 후 3MB가 넘어갈 수 있으므로 검사하는 함수 만들기
def emoji_resize_normal(_emoji_filename: str, _guildID: int):
    print(f"normal resizing {_emoji_filename}...")
    img = Image.open(f'Emoji/{_guildID}/{_emoji_filename}')
    img_resize = img.resize((int(128), int(128)))
    img_resize.save(f'Emoji/{_guildID}/{_emoji_filename}')
    print(f"normal resizing {_emoji_filename} complete...")


# TODO 위에 적어놨듯이 사진도 변환후 3MB가 넘어갈 수 있으니 확인하는 함수 만들면서 밑에 확인하는 if문 제거 및 코드 정리 하기
# 1. 해상도는 높으나 크기가 적은 파일 2. 해상도는 낮으나 크기가 큰 파일
def emoji_resize_gif(_emoji_filename: str, _guildID: int):
    print(f"gif resizing {_emoji_filename}...")
    im = Image.open(f'Emoji/{_guildID}/{_emoji_filename}')
    file_size = os.stat(f'Emoji/{_guildID}/{_emoji_filename}').st_size / pow(1024, 2)
    w_size = im.size[0]
    h_size = im.size[1]
    print(w_size, h_size)
    # 3mb이하는 resizing pass
    if file_size <= 3:
        return
    # 3mb초과는 resizing 필요
    else:
        # 해상도와 크기가 큰 파일 ->  350, 350으로 고정
        if w_size > 350 or h_size > 350:
            w_size = h_size = 350
        # 해상도가 350 350이하이며 최소크기(128 128)보다 큰파일 -> 128, 128로 고정
        elif w_size > 128 or h_size > 128:
            w_size, h_size = 128
        # 해상도가 128이하이고 크기가 3mb가 넘어갈 때
        else:
            raise ValueError(f"GIF가 조건에 맞지 않습니다. `조건: 크기(3MB이하) 해상도(128X128이상)`\n"
                             f"`업로드한 파일크기: {round(file_size, 2)}MB`\t`해상도: {w_size}X{h_size}`")
    print(w_size, h_size)
    GIFConvert.scale_gif(f'Emoji/{_guildID}/{_emoji_filename}', (w_size, h_size))
    file_size = os.stat(f'Emoji/{_guildID}/{_emoji_filename}').st_size / pow(1024, 2)
    print(f"gif resizing {_emoji_filename} complete... {file_size}MB")
    # 변환은 했지만 여전히 파일 크기가 3MB이상 일 때
    if file_size > 3:
        # Permission 에러 방지를 위해 im 변수 메모리에서 제거
        del im
        raise ValueError(f"크기 변경에는 성공했지만 조건에 만족하지 못해 실패했습니다.")


def is_support_format(_emoji_filename: str):
    support_format_list = ["jpg", "png", "gif"]

    for support_format in support_format_list:
        if _emoji_filename.endswith(support_format):
            return True

    raise NotImplementedError("지원하지 않는 파일입니다.")
