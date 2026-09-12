import logging
logger = logging.getLogger(__name__)
import os
import discord
import numpy as np
import matplotlib.pyplot as plt
from keras.models import load_model
from PIL import Image, ImageOps

back_slash = "\\"

# Graph Font Set
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# Load the model
model = load_model(f'{os.getcwd().replace(back_slash, "/")}/keras/keras_model.h5')

async def save_image(_image: discord.Attachment):
    """Discord 이미지 첨부를 keras 폴더에 저장하고 (파일 경로, 파일명)을 반환한다."""
    file_type = _image.content_type.split("/")
    file_name = f"{str(_image.id)}.{file_type[1]}"
    file_path = f"keras/{file_name}"

    logger.debug('%s', "image save...")
    await _image.save(file_path)
    logger.debug('%s', "image save complete")

    return file_path, file_name


def remove_image(image_path):
    """image_path의 이미지 파일을 삭제한다. 파일 접근 오류는 호출자에게 전달한다."""
    logger.debug('%s', "image remove...")
    os.remove(image_path)
    logger.debug('%s', "image remove complete...")


def resize_image(image, image_path=None):
    """PIL 이미지를 RGB로 변환·중앙 자르기하여 모델 입력 배열을 반환한다.

    반환값은 (1, 224, 224, 3) 형태의 float32 배열이며 값 범위는 -1부터 1이다.
    image_path는 기존 호출과의 호환성을 위한 인자로 사용하지 않는다.
    """
    image = ImageOps.fit(image.convert("RGB"), (224, 224), Image.Resampling.LANCZOS)
    return np.expand_dims(np.asarray(image, dtype=np.float32) / 127.0 - 1, axis=0)


async def predict_image(image: discord.Attachment):
    """첨부 이미지를 저장·분류하고 예측 그래프를 생성한다.

    그래프는 저장한 이미지 경로에 덮어쓴다. (Discord 첨부 파일, 경로)를 반환하며
    반환 파일 닫기와 디스크 파일 정리는 호출자가 담당한다.
    """
    image_path, image_name = await save_image(image)
    with Image.open(image_path) as source:
        data = resize_image(source)
    prediction = model.predict(data) * 100
    save_predict_result_graph(prediction[0], image_path)
    return discord.File(image_path, filename=image_name), image_path


def create_color_arr(length):
    """네 가지 기본 색을 반복하여 length개 막대에 사용할 색상 문자열 목록을 반환한다."""
    color_list = ["#E67701", "#D84C6F", "#794AEF", "#1967D2"]
    return [color_list[i % len(color_list)] for i in range(length)]


def draw_value_bar_top(result_val_arr, y):
    """현재 그래프에 예측값을 표시한다. y는 항목별 위치이며 0.9 미만의 값은 생략한다."""
    for i, v in enumerate(result_val_arr):
        if v < 0.9:
            continue
        plt.text(v, y[i], result_val_arr[i],  # 좌표 (x축 = v, y축 = y[0]..y[1], 표시 = y[0]..y[1])
                 fontsize=9,
                 color='black',
                 horizontalalignment='center',  # horizontalalignment (left, center, right)
                 verticalalignment='bottom')  # verticalalignment (top, center, bottom)


def save_predict_result_graph(result_val_arr, save_path):
    """여섯 분류 항목의 예측값을 가로 막대 그래프로 save_path에 저장한다.

    result_val_arr 길이가 분류 항목 수와 다르면 ValueError를 발생시키고,
    저장 후 현재 그래프를 비운다.
    """
    val_name = ["육회", "회", "떡볶이", "치킨", "지도", "etc"]
    if len(result_val_arr) != len(val_name):
        raise ValueError("목록이 일치하지 않습니다")
    bar_color = create_color_arr(len(result_val_arr))
    y = np.arange(len(result_val_arr))
    draw_value_bar_top(result_val_arr, y)
    plt.title("사진 예측 결과")
    plt.barh(y, result_val_arr, color=bar_color)
    plt.yticks(y, val_name)
    plt.gca().invert_yaxis()
    plt.savefig(save_path)
    plt.clf()
