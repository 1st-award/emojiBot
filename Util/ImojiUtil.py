import discord
from Util import GIFConvert
import os
import shutil
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from easy_pil import Editor, Canvas, Font



async def save_emoji(_emoji: discord.Attachment, _guildID: int):
    file_type = _emoji.content_type.split("/")
    file_name = str(_emoji.id) + "." + file_type[1]

    print("emoji save...")
    await _emoji.save(f"Emoji/{_guildID}/{file_name}")
    print("emoji save complete")

    if not _emoji.filename.endswith(".gif"):
        emoji_resize_normal(file_name, _guildID)
    else:
        emoji_resize_gif(file_name, _guildID)


def emoji_remove(_emoji_filename: str, _guildID: int):
    print("emoji remove...")
    os.remove(f"Emoji/{_guildID}/{_emoji_filename}")
    print("emoji remove complete...")


def emoji_dir_create(_guildID: int):
    print(f"create Emoji/{_guildID} folder...")
    os.mkdir(f"Emoji/{_guildID}")
    print(f"create folder complete")


def emoji_dir_remove(_guildID: int):
    print(f"removing emoji dir {_guildID}...")
    shutil.rmtree(f"Emoji/{_guildID}")
    print(f"remove {_guildID} complete")


def emoji_dir_copy(toGuildID: int, fromGuildID: int):
    print("try to copy")
    emoji_dir_remove(fromGuildID)
    shutil.copytree(f"Emoji/{toGuildID}", f"Emoji/{fromGuildID}")
    print("copy success")


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


def create_image(
    text: str,
    background_color: str,
    font_path: str = "Fonts/NotoSansKR.ttf",
    font_size: int = 40,
    spacing: int = -2,
):
    IMAGE_SIZE = 100
    PADDING = 5

    # ========================================================
    # 이미지 생성
    # ========================================================
    image = Image.new(
        "RGB",
        (IMAGE_SIZE, IMAGE_SIZE),
        background_color
    )

    draw = ImageDraw.Draw(image)

    # ========================================================
    # 글자 색상
    # ========================================================
    if background_color.lower() == "#ffffff":
        font_color = "#000000"
    else:
        font_color = "#ffffff"

    # ========================================================
    # 줄바꿈
    #
    # - 스페이스 → 줄바꿈
    # - 한 줄 5글자 → 줄바꿈
    # - 스페이스는 제거
    # ========================================================
    lines = []
    current_line = ""

    for char in text:
        if char == " ":
            if current_line:
                lines.append(current_line)
                current_line = ""
            continue

        current_line += char

        if len(current_line) == 5:
            lines.append(current_line)
            current_line = ""

    if current_line:
        lines.append(current_line)

    if not lines:
        lines = [""]

    # ========================================================
    # 폰트 크기에 따른 실제 텍스트 크기 계산
    # ========================================================
    def calculate_text_size(font):
        line_data = []

        for line in lines:
            if not line:
                continue

            char_data = []

            min_y = float("inf")
            max_y = float("-inf")
            width = 0

            for char in line:
                bbox = draw.textbbox(
                    (0, 0),
                    char,
                    font=font
                )

                char_width = bbox[2] - bbox[0]

                width += char_width

                min_y = min(min_y, bbox[1])
                max_y = max(max_y, bbox[3])

                char_data.append(
                    (char, bbox, char_width)
                )

            # 자간
            if len(line) > 1:
                width += spacing * (len(line) - 1)

            height = max_y - min_y

            line_data.append({
                "width": width,
                "height": height,
                "min_y": min_y,
                "max_y": max_y,
                "chars": char_data
            })

        if not line_data:
            return 0, 0, []

        # 가장 긴 줄의 너비
        total_width = max(
            line["width"]
            for line in line_data
        )

        # 전체 높이
        total_height = sum(
            line["height"]
            for line in line_data
        )

        return total_width, total_height, line_data

    # ========================================================
    # 폰트 크기 자동 조절
    #
    # 글자가 많아서 100×100을 벗어나면
    # 폰트 크기를 1씩 줄인다.
    # ========================================================
    current_font_size = font_size

    while current_font_size > 5:

        font = ImageFont.truetype(
            font_path,
            current_font_size
        )

        text_width, text_height, line_data = (
            calculate_text_size(font)
        )

        available_size = IMAGE_SIZE - (PADDING * 2)

        if (
            text_width <= available_size
            and text_height <= available_size
        ):
            break

        current_font_size -= 1

    # ========================================================
    # 최종 텍스트 크기
    # ========================================================
    text_width, text_height, line_data = (
        calculate_text_size(font)
    )

    # ========================================================
    # 전체 텍스트의 세로 시작 위치
    # ========================================================
    current_y = (
        (IMAGE_SIZE - text_height) / 2
    )

    # ========================================================
    # 텍스트 그리기
    # ========================================================
    for line in line_data:

        line_width = line["width"]

        # --------------------------------------------
        # 현재 줄 가로 중앙 정렬
        # --------------------------------------------
        current_x = (
            (IMAGE_SIZE - line_width) / 2
        )

        # --------------------------------------------
        # 실제 글자의 위쪽 기준
        # --------------------------------------------
        base_y = (
            current_y - line["min_y"]
        )

        # --------------------------------------------
        # 글자 하나씩 그리기
        # --------------------------------------------
        for char, bbox, char_width in line["chars"]:

            draw.text(
                (
                    current_x - bbox[0],
                    base_y
                ),
                char,
                font=font,
                fill=font_color
            )

            current_x += char_width + spacing

        # --------------------------------------------
        # 다음 줄
        # --------------------------------------------
        current_y += line["height"]

    # ========================================================
    # PNG 반환
    # ========================================================
    output = BytesIO()

    image.save(
        output,
        format="PNG"
    )

    output.seek(0)

    return output