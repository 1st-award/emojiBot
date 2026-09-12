import io
import os
import requests
from easy_pil import Font, Editor, load_image_async

font_path = os.getcwd() + '\\apex.otf'
bg_path = os.getcwd() + '\\crafting.png'


def _get_json(endpoint, **params):
    """APEX API의 endpoint에 쿼리 params를 전달하고 JSON 응답을 반환한다.

    APEX_API_TOKEN 환경 변수가 필요하며 요청 제한 시간은 15초이다.
    키 누락·통신·HTTP 상태 오류는 RuntimeError로 전달한다.
    """
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
    """APEX API에서 한국어 뉴스 JSON 데이터를 조회해 반환한다."""
    return _get_json("news", lang="ko")


def get_rotation_map():
    """APEX API에서 (현재 맵 정보, 다음 맵 정보) 튜플을 조회해 반환한다."""
    rotation = _get_json("maprotation")
    return rotation["current"], rotation["next"]


def get_crafts():
    """APEX API 제작 목록의 첫 두 항목을 (일간 제작, 주간 제작) 튜플로 반환한다."""
    crafts = _get_json("crafting")
    return crafts[0], crafts[1]


async def create_rotation_craft_img(daily_craft, weekly_craft):
    """일간·주간 제작 항목의 아이콘과 비용을 배경 이미지에 합성한다.

    API 항목의 bundleContent를 사용하며 result_craft.png에 저장한 뒤
    그 상대 경로를 반환한다. 같은 이름의 기존 결과 파일은 덮어쓴다.
    """
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
