import os
import discord
import numpy as np
import matplotlib.pyplot as plt
from keras.models import load_model
from PIL import Image, ImageOps

# Graph Font Set
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# Load the model
model = load_model('keras/keras_model.h5')

# Create the array of the right shape to feed into the keras model
# The 'length' or number of images you can put into the array is
# determined by the first position in the shape tuple, in this case 1.
data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)


async def save_image(_image: discord.Attachment):
    file_type = _image.content_type.split("/")
    file_name = f"{str(_image.id)}.{file_type[1]}"
    file_path = f"keras/{file_name}"

    print("image save...")
    await _image.save(file_path)
    print("image save complete")

    return file_path, file_name


def remove_image(image_path):
    print("image remove...")
    os.remove(image_path)
    print("image remove complete...")


def resize_image(image, image_path):
    try:
        data = np.ndarray(shape=(1, 224, 224, 4), dtype=np.float32)
        image_array = np.asarray(image)
        normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
        data[0] = normalized_image_array
    except ValueError:
        remove_image(image_path)


async def predict_image(image: discord.Attachment):
    image_path, image_name = await save_image(image)
    # Replace this with the path to your image
    image = Image.open(image_path)
    # resize the image to a 224x224 with the same strategy as in TM2:
    # resizing the image to be at least 224x224 and then cropping from the center
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.ANTIALIAS)

    # turn the image into a numpy array
    image_array = np.asarray(image)
    # Normalize the image
    normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
    # Load the image into the array
    try:
        data[0] = normalized_image_array
    except ValueError:
        resize_image(image, image_path)

    # run the inference
    prediction = model.predict(data)
    prediction = list(map(lambda x: x * 100, prediction))
    save_predict_result_graph(prediction[0], image_path)
    discord_image = discord.File(image_path, filename=image_name)
    return discord_image, image_path


def create_color_arr(length):
    color_list = ["#E67701", "#D84C6F", "#794AEF", "#1967D2"]
    bar_color = []
    for cnt in range(0, length):
        bar_color.append(color_list[cnt % len(color_list)])
    return bar_color


def draw_value_bar_top(result_val_arr, y):
    for i, v in enumerate(result_val_arr):
        if v < 1.0:
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
