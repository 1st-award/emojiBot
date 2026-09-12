import io
import os
import requests
from easy_pil import Font, Editor, load_image_async

font_path = os.getcwd() + '\\apex.otf'
bg_path = os.getcwd() + '\\crafting.png'


def _get_json(endpoint, **params):
    token = os.getenv("APEX_API_TOKEN")
    if not token:
        raise RuntimeError("APEX_API_TOKEN 환경 변수가 필요합니다.")
    try:
        response = requests.get(f"https://api.mozambiquehe.re/{endpoint}",
                                params={"auth": token, **params}, timeout=15)
    except requests.RequestException:
        raise RuntimeError("APEX API 연결 실패") from None
    with response:
        if not response.ok:
            # Do not expose the URL containing the API token in an exception.
            raise RuntimeError(f"APEX API 요청 실패: HTTP {response.status_code}")
        return response.json()


def get_news():
    return _get_json("news", lang="ko")


def get_rotation_map():
    rotation = _get_json("maprotation")
    return rotation["current"], rotation["next"]


def get_crafts():
    crafts = _get_json("crafting")
    return crafts[0], crafts[1]


async def create_rotation_craft_img(daily_craft, weekly_craft):
    font = Font(font_path, 10)
    frame = Editor(bg_path)
    x = 170
    y = 115
    crafts = daily_craft['bundleContent'] + weekly_craft['bundleContent']
    for i, craft in enumerate(crafts):
        asset = await load_image_async(craft['itemType']['asset'])
        asset = asset.resize((40, 40))
        frame.paste(asset, (x + (110 * i), y))
        frame.text(((x + 10) + (110 * i), y + 80), str(craft['cost']),
                   color=(143, 221, 223),
                   font=font,
                   align='center')

    frame.save('result_craft.png')

    return 'result_craft.png'
