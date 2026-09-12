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
    file_type = _image.content_type.split("/")
    file_name = f"{str(_image.id)}.{file_type[1]}"
    file_path = f"keras/{file_name}"

    logger.debug('%s', "image save...")
    await _image.save(file_path)
    logger.debug('%s', "image save complete")

    return file_path, file_name


def remove_image(image_path):
    logger.debug('%s', "image remove...")
    os.remove(image_path)
    logger.debug('%s', "image remove complete...")


def resize_image(image, image_path=None):
    image = ImageOps.fit(image.convert("RGB"), (224, 224), Image.Resampling.LANCZOS)
    return np.expand_dims(np.asarray(image, dtype=np.float32) / 127.0 - 1, axis=0)


async def predict_image(image: discord.Attachment):
    image_path, image_name = await save_image(image)
    with Image.open(image_path) as source:
        data = resize_image(source)
    prediction = model.predict(data) * 100
    save_predict_result_graph(prediction[0], image_path)
    return discord.File(image_path, filename=image_name), image_path


def create_color_arr(length):
    color_list = ["#E67701", "#D84C6F", "#794AEF", "#1967D2"]
    return [color_list[i % len(color_list)] for i in range(length)]


def draw_value_bar_top(result_val_arr, y):
    for i, v in enumerate(result_val_arr):
        if v < 0.9:
            continue
        plt.text(v, y[i], result_val_arr[i],  # 좌표 (x축 = v, y축 = y[0]..y[1], 표시 = y[0]..y[1])
                 fontsize=9,
                 color='black',
                 horizontalalignment='center',  # horizontalalignment (left, center, right)
                 verticalalignment='bottom')  # verticalalignment (top, center, bottom)


def save_predict_result_graph(result_val_arr, save_path):
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
