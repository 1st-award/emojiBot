import io
import os
import requests
from easy_pil import Font, Editor, load_image_async

token = os.environ['APEX_TOKEN']
font_path = os.getcwd() + '\\apex.otf'
bg_path = os.getcwd() + '\\crafting.png'


def get_news():
    global token
    news_list = requests.get(f"https://api.mozambiquehe.re/news?auth={token}&lang=ko").json()
    return news_list


def get_rotation_map():
    global token
    rotation_map = requests.get(f"https://api.mozambiquehe.re/maprotation?auth={token}").json()
    current_map = rotation_map['current']
    next_map = rotation_map['next']
    return current_map, next_map


def get_crafts():
    global token
    craft_list = requests.get(f"https://api.mozambiquehe.re/crafting?auth={token}").json()
    daily_craft = craft_list[0]
    weekly_craft = craft_list[1]
    return daily_craft, weekly_craft


async def create_rotation_craft_img(daily_craft, weekly_craft):
    font = Font(font_path, 10)
    frame = Editor(bg_path)
    x = 170
    y = 115
    crafts = daily_craft['bundleContent'] + weekly_craft['bundleContent']
    i = 0
    for craft in crafts:
        asset = await load_image_async(craft['itemType']['asset'])
        asset = asset.resize((40, 40))
        frame.paste(asset, (x + (110 * i), y))
        frame.text(((x + 10) + (110 * i), y + 80), str(craft['cost']),
                   color=(143, 221, 223),
                   font=font,
                   align='center')
        i += 1

    frame.save('result_craft.png')

    return 'result_craft.png'
