import logging
logger = logging.getLogger(__name__)
import asyncio
from pathlib import Path
import discord
from Util import GIFConvert
import os
import shutil
import filecmp
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from easy_pil import Editor, Canvas, Font



async def save_emoji(_emoji: discord.Attachment, _guildID: int):
    """Discord 첨부 파일을 서버 폴더에 저장하고 형식에 맞게 크기를 조정한다.

    _emoji는 첨부 파일, _guildID는 저장할 서버 ID이다. 변환은 작업 스레드에서
    수행하며 실패 시 예외를 전달한다. DB 등록과 실패 파일 정리는 호출자가 담당한다.
    """
    file_name = attachment_filename(_emoji)
    emoji_dir_create(_guildID)

    logger.debug('%s', "emoji save...")
    await _emoji.save(emoji_path(file_name, _guildID))
    logger.debug('%s', "emoji save complete")

    if not file_name.endswith(".gif"):
        await asyncio.to_thread(emoji_resize_normal, file_name, _guildID)
    else:
        await asyncio.to_thread(emoji_resize_gif, file_name, _guildID)


def emoji_remove(_emoji_filename: str, _guildID: int):
    """서버 ID와 파일명으로 지정한 이모지 파일을 삭제한다. 파일이 없어도 오류를 내지 않는다."""
    logger.debug('%s', "emoji remove...")
    emoji_path(_emoji_filename, _guildID).unlink(missing_ok=True)
    logger.debug('%s', "emoji remove complete...")


def emoji_dir_create(_guildID: int):
    """서버 ID에 해당하는 이모지 폴더와 필요한 상위 폴더를 생성한다. 기존 폴더는 유지한다."""
    logger.debug('%s', f"create Emoji/{_guildID} folder...")
    emoji_path("placeholder", _guildID).parent.mkdir(parents=True, exist_ok=True)
    logger.debug('%s', f"create folder complete")


def emoji_dir_remove(_guildID: int):
    """서버 ID에 해당하는 이모지 폴더와 내부 파일을 모두 삭제한다. 없는 폴더는 무시한다."""
    logger.debug('%s', f"removing emoji dir {_guildID}...")
    directory = emoji_path("placeholder", _guildID).parent
    if directory.exists():
        shutil.rmtree(directory)
    logger.debug('%s', f"remove {_guildID} complete")


def emoji_dir_copy(toGuildID: int, fromGuildID: int):
    """원본 서버의 이모지 파일을 대상 서버 폴더에 복사한다.

    기존 인자 이름과 달리 toGuildID가 원본, fromGuildID가 대상이다.
    같은 서버, 하위 폴더·심볼릭 링크, 내용이 다른 동일 파일명은 예외로 거부한다.
    DB는 수정하지 않으며 복사 실패 시 이미 복사한 파일은 남을 수 있다.
    """
    logger.debug('%s', "try to copy")
    if toGuildID == fromGuildID:
        raise ValueError("같은 서버로 복사할 수 없습니다.")
    source = emoji_path("placeholder", toGuildID).parent
    destination = emoji_path("placeholder", fromGuildID).parent
    for source_file in source.iterdir():
        target = destination / source_file.name
        if source_file.is_dir() or source_file.is_symlink():
            raise ValueError("이모지 폴더에는 일반 파일만 허용됩니다.")
        if target.exists() and not filecmp.cmp(source_file, target, shallow=False):
            raise FileExistsError("대상 서버에 내용이 다른 같은 이름의 파일이 있습니다.")
    shutil.copytree(source, destination, dirs_exist_ok=True)
    logger.debug('%s', "copy success")


# TODO 일반 사진도 변환 후 3MB가 넘어갈 수 있으므로 검사하는 함수 만들기
def emoji_resize_normal(_emoji_filename: str, _guildID: int):
    """서버 폴더의 지정 이미지를 128×128 픽셀로 변경해 원래 경로에 저장한다."""
    logger.debug('%s', f"normal resizing {_emoji_filename}...")
    with Image.open(emoji_path(_emoji_filename, _guildID)) as img:
        img_resize = img.resize((128, 128))
    img_resize.save(emoji_path(_emoji_filename, _guildID))
    logger.debug('%s', f"normal resizing {_emoji_filename} complete...")


# TODO 위에 적어놨듯이 사진도 변환후 3MB가 넘어갈 수 있으니 확인하는 함수 만들면서 밑에 확인하는 if문 제거 및 코드 정리 하기
# 1. 해상도는 높으나 크기가 적은 파일 2. 해상도는 낮으나 크기가 큰 파일
def emoji_resize_gif(_emoji_filename: str, _guildID: int):
    """서버 폴더의 GIF가 3MiB를 초과하면 해상도에 따라 축소해 덮어쓴다.

    축소할 수 없거나 변환 후에도 용량 제한을 초과하면 ValueError를 발생시킨다.
    """
    logger.debug('%s', f"gif resizing {_emoji_filename}...")
    with Image.open(emoji_path(_emoji_filename, _guildID)) as im:
        w_size, h_size = im.size
    file_size = os.stat(emoji_path(_emoji_filename, _guildID)).st_size / pow(1024, 2)
    logger.debug('%s %s', w_size, h_size)
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
            w_size = h_size = 128
        # 해상도가 128이하이고 크기가 3mb가 넘어갈 때
        else:
            raise ValueError(f"GIF가 조건에 맞지 않습니다. `조건: 크기(3MB이하) 해상도(128X128이상)`\n"
                             f"`업로드한 파일크기: {round(file_size, 2)}MB`\t`해상도: {w_size}X{h_size}`")
    logger.debug('%s %s', w_size, h_size)
    GIFConvert.scale_gif(emoji_path(_emoji_filename, _guildID), (w_size, h_size))
    file_size = os.stat(emoji_path(_emoji_filename, _guildID)).st_size / pow(1024, 2)
    logger.debug('%s', f"gif resizing {_emoji_filename} complete... {file_size}MB")
    # 변환은 했지만 여전히 파일 크기가 3MB이상 일 때
    if file_size > 3:
        # Permission 에러 방지를 위해 im 변수 메모리에서 제거
        del im
        raise ValueError(f"크기 변경에는 성공했지만 조건에 만족하지 못해 실패했습니다.")


def is_support_format(_emoji_filename: str):
    """파일명이 jpg, png, gif 중 하나로 끝나면 True를 반환한다.

    현재 검사는 대소문자를 구분하며, 미지원 형식이면 NotImplementedError를 발생시킨다.
    """
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
    """텍스트를 배경색 위에 그린 100×100 PNG의 BytesIO를 반환한다.

    text는 표시할 글자, background_color는 배경색이다. font_path와 font_size는
    글꼴 및 초기 크기, spacing은 글자 간격이다. 공백과 다섯 글자 단위로
    줄을 나누고 크기를 조정한다. 반환 버퍼의 읽기 위치는 처음으로 설정한다.
    """
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
        """주어진 글꼴로 각 줄을 측정해 전체 너비·높이와 글자별 배치 정보 목록을 반환한다."""
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

EMOJI_ROOT = Path(__file__).resolve().parents[1] / "Emoji"


def emoji_path(filename, guild_id):
    """서버 폴더 내부의 파일 절대 경로를 Path로 반환한다.

    guild_id가 -1이면 공용 폴더를 사용한다. 빈 파일명이나 폴더를 벗어나는
    경로는 ValueError로 거부하며, 실제 파일의 존재 여부는 확인하지 않는다.
    """
    directory = EMOJI_ROOT / ("Global_Icon" if guild_id == -1 else str(int(guild_id)))
    path = (directory / filename).resolve()
    if path.parent != directory.resolve() or not filename or Path(filename).name != filename:
        raise ValueError("잘못된 이미지 경로입니다.")
    return path


def attachment_filename(attachment):
    """첨부 파일 ID와 MIME 형식으로 저장 파일명을 생성한다.

    JPEG·PNG·GIF를 지원하며, MIME 형식이 없거나 미지원이면 NotImplementedError를 발생시킨다.
    """
    extension = {"image/jpeg": "jpg", "image/png": "png", "image/gif": "gif"}.get(attachment.content_type)
    if extension is None:
        raise NotImplementedError("지원하지 않는 파일입니다.")
    return f"{attachment.id}.{extension}"
