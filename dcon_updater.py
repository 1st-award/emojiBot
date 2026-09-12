import json
import re
import sqlite3
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests


# ============================================================
# 설정
# ============================================================

URL = "https://www.funzinnu.com/stream/dccon.js?ts=1787223951307"

DB_PATH = Path(
    "/data/data/com.termux/files/home/Desktop/"
    "discord_emoji_bot/Emoji/emoji.db"
)

# Global_Icon 폴더
ICON_DIR = Path(
    "/data/data/com.termux/files/home/Desktop/"
    "discord_emoji_bot/Emoji/Global_Icon"
)

# HTTP 요청 설정
REQUEST_TIMEOUT = 30

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ============================================================
# dccon.js 다운로드
# ============================================================

def download_dccon_data():
    print("dccon.js 다운로드 중...")

    response = requests.get(
        URL,
        timeout=REQUEST_TIMEOUT,
        headers=HEADERS
    )

    response.raise_for_status()

    # 서버의 인코딩 정보가 불확실한 경우 대비
    response.encoding = response.apparent_encoding

    print(
        f"다운로드 완료: "
        f"{len(response.content):,} bytes"
    )

    return response.text


# ============================================================
# dccon.js 파싱
# ============================================================

def parse_dccon_data(text):
    """
    dccon.js의 dcConsData를 파싱한다.

    입력 예시:

    dcConsData = [{
        "name": "팝콘.gif",
        "uri": "https://funzinnu.com/stream/cdn/dccon/팝콘.gif",
        "keywords": ["팝콘"],
        "tags": ["미지정"]
    }, {
        ...
    }]

    결과:

    [
        {
            "name": "팝콘.gif",
            "uri": "https://funzinnu.com/stream/cdn/dccon/팝콘.gif",
            "command": "팝콘"
        }
    ]
    """

    # --------------------------------------------------------
    # dcConsData = [...] 추출
    # --------------------------------------------------------

    match = re.search(
        r"dcConsData\s*=\s*(\[.*\])\s*;?\s*$",
        text,
        re.DOTALL
    )

    if not match:
        raise ValueError(
            "dcConsData 배열을 찾을 수 없습니다."
        )

    json_text = match.group(1)

    # --------------------------------------------------------
    # JSON 파싱
    # --------------------------------------------------------

    try:
        dccon_data = json.loads(json_text)

    except json.JSONDecodeError as e:
        raise ValueError(
            f"dcConsData JSON 파싱 실패: {e}"
        ) from e

    result = []

    # --------------------------------------------------------
    # 데이터 처리
    # --------------------------------------------------------

    for item in dccon_data:

        if not isinstance(item, dict):
            continue

        # ----------------------------------------------------
        # name
        # ----------------------------------------------------

        name = item.get("name")

        if not name:
            continue

        name = str(name).strip()

        if not name:
            continue

        # ----------------------------------------------------
        # uri
        # ----------------------------------------------------

        uri = item.get("uri")

        if not uri:
            continue

        uri = str(uri).strip()

        if not uri:
            continue

        # ----------------------------------------------------
        # keywords
        # ----------------------------------------------------

        keywords = item.get("keywords")

        if not isinstance(keywords, list):
            continue

        commands = []

        for keyword in keywords:

            if keyword is None:
                continue

            keyword = str(keyword).strip()

            if not keyword:
                continue

            commands.append(keyword)

        # ----------------------------------------------------
        # 유효한 keyword가 없으면 스킵
        # ----------------------------------------------------

        if not commands:
            continue

        # ----------------------------------------------------
        # command 생성
        # ----------------------------------------------------

        command = ", ".join(commands)

        result.append(
            {
                "name": name,
                "uri": uri,
                "command": command
            }
        )

    return result


# ============================================================
# 파일명 안전성 검사
# ============================================================

def sanitize_filename(name):
    """
    name을 실제 파일명으로 사용할 수 있도록 정리한다.

    예:

        팝콘.gif
        =>
        팝콘.gif

    위험한 문자:

        /
        \\
        :
        *
        ?
        "
        <
        >
        |
    """

    name = str(name).strip()

    # 경로 구분자 제거
    name = name.replace("/", "_")
    name = name.replace("\\", "_")

    # Windows에서도 문제가 되는 문자 제거
    name = re.sub(
        r'[:*?"<>|]',
        "_",
        name
    )

    # 현재 디렉터리 / 상위 디렉터리 방지
    name = name.replace("..", "_")

    if not name:
        raise ValueError(
            "유효하지 않은 파일명입니다."
        )

    return name


# ============================================================
# 이미지 다운로드
# ============================================================

def download_icon(name, uri):
    """
    uri의 이미지를

        Emoji/Global_Icon/name

    으로 저장한다.

    이미 파일이 존재하면 다운로드하지 않는다.

    반환값:

        True  = 다운로드 성공 또는 이미 존재
        False = 다운로드 실패
    """

    safe_name = sanitize_filename(name)

    file_path = ICON_DIR / safe_name

    # --------------------------------------------------------
    # 폴더 생성
    # --------------------------------------------------------

    ICON_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # 이미 파일이 있으면 다운로드 생략
    # --------------------------------------------------------

    if file_path.exists():
        print(
            f"[SKIP] 이미 존재: {safe_name}"
        )

        return True

    # --------------------------------------------------------
    # 다운로드
    # --------------------------------------------------------

    print(
        f"[DOWNLOAD] {safe_name}"
    )

    try:
        response = requests.get(
            uri,
            timeout=REQUEST_TIMEOUT,
            headers=HEADERS
        )

        response.raise_for_status()

        # ----------------------------------------------------
        # 파일 저장
        # ----------------------------------------------------

        with open(
            file_path,
            "wb"
        ) as file:

            file.write(
                response.content
            )

        print(
            f"[OK] 저장 완료: "
            f"{file_path}"
        )

        return True

    except requests.RequestException as e:

        print(
            f"[ERROR] 다운로드 실패: "
            f"{name}"
        )

        print(
            f"        URI: {uri}"
        )

        print(
            f"        오류: {e}"
        )

        return False


# ============================================================
# 기존 path에서 name 추출
# ============================================================

def extract_name_from_path(path):
    """
    기존 DB의 path에서 파일명을 추출한다.

    처리 예:

        https://funzinnu.com/stream/cdn/dccon/팝콘.gif
        =>
        팝콘.gif

        /Emoji/Global_Icon/팝콘.gif
        =>
        팝콘.gif

        팝콘.gif
        =>
        팝콘.gif
    """

    if path is None:
        return None

    path = str(path).strip()

    if not path:
        return None

    # --------------------------------------------------------
    # URL인 경우
    # --------------------------------------------------------

    if path.startswith(
        (
            "http://",
            "https://"
        )
    ):
        parsed = urlparse(path)

        filename = Path(
            unquote(
                parsed.path
            )
        ).name

        return filename or None

    # --------------------------------------------------------
    # 로컬 경로인 경우
    # --------------------------------------------------------

    path = path.replace("\\", "/")

    filename = Path(path).name

    if filename:
        return unquote(filename)

    return None


# ============================================================
# 기존 DB path를 name으로 변경
# ============================================================

def update_existing_paths(cursor):
    """
    기존 guild=-1 데이터의 path를 전부 name으로 변경한다.

    예:

        path =
        https://funzinnu.com/stream/cdn/dccon/팝콘.gif

    =>
        path =
        팝콘.gif
    """

    print()
    print("기존 guild=-1 데이터의 path 확인 중...")

    cursor.execute("""
        SELECT rowid, path
        FROM emoji
        WHERE guild = -1
    """)

    rows = cursor.fetchall()

    updated = 0
    skipped = 0

    update_sql = """
        UPDATE emoji
        SET path = ?
        WHERE rowid = ?
    """

    for rowid, path in rows:

        name = extract_name_from_path(path)

        if not name:
            skipped += 1
            continue

        # 이미 name 형태라면 UPDATE할 필요 없음
        if path == name:
            skipped += 1
            continue

        cursor.execute(
            update_sql,
            (
                name,
                rowid
            )
        )

        updated += 1

    print(
        f"기존 path 변경 완료: "
        f"{updated:,}개"
    )

    if skipped:
        print(
            f"변경할 필요 없음/추출 실패: "
            f"{skipped:,}개"
        )

    return updated


# ============================================================
# DB 데이터 삽입
# ============================================================

def insert_database(data):
    """
    guild=-1 데이터를 DB에 삽입한다.

    DB 구조:

        guild
        command
        path

    path에는 URI가 아니라 name을 저장한다.

    예:

        guild   = -1
        command = "팝콘"
        path    = "팝콘.gif"

    UNIQUE(guild, command)

    따라서 같은 command가 이미 존재하면
    path가 다르더라도 INSERT하지 않는다.
    """

    print("emoji.db 연결 중...")

    conn = sqlite3.connect(
        DB_PATH
    )

    try:
        cursor = conn.cursor()

        # ----------------------------------------------------
        # 기존 데이터 path를 name으로 변경
        # ----------------------------------------------------

        update_existing_paths(cursor)

        # ----------------------------------------------------
        # 기존 guild=-1 데이터 가져오기
        # ----------------------------------------------------

        print()
        print("기존 guild=-1 데이터 읽는 중...")

        cursor.execute("""
            SELECT guild, command
            FROM emoji
            WHERE guild = -1
        """)

        existing = set(
            cursor.fetchall()
        )

        print(
            f"기존 데이터: "
            f"{len(existing):,}개"
        )

        # ----------------------------------------------------
        # INSERT SQL
        # ----------------------------------------------------

        insert_sql = """
            INSERT INTO emoji (
                guild,
                command,
                path
            )
            VALUES (?, ?, ?)
        """

        inserted = 0
        skipped = 0
        download_failed = 0

        # ----------------------------------------------------
        # 데이터 처리
        # ----------------------------------------------------

        for item in data:

            name = item["name"]
            uri = item["uri"]
            command = item["command"]

            # ------------------------------------------------
            # 안전한 파일명
            # ------------------------------------------------

            safe_name = sanitize_filename(
                name
            )

            # ------------------------------------------------
            # 이미지 다운로드
            # ------------------------------------------------

            download_success = download_icon(
                safe_name,
                uri
            )

            if not download_success:
                download_failed += 1

                # 다운로드 실패해도 DB에 넣을 것인지 여부
                #
                # 여기서는 이미지가 없는 상태의 DB 등록을
                # 방지하기 위해 INSERT하지 않는다.
                continue

            # ------------------------------------------------
            # 중복 검사
            # ------------------------------------------------

            key = (
                -1,
                command
            )

            if key in existing:

                skipped += 1

                continue

            # ------------------------------------------------
            # INSERT
            #
            # path에는 URI가 아니라 name을 저장
            # ------------------------------------------------

            cursor.execute(
                insert_sql,
                (
                    -1,
                    command,
                    safe_name
                )
            )

            # ------------------------------------------------
            # 메모리에도 추가
            #
            # dccon.js 자체에 동일 command가 여러 번 있어도
            # 한 번만 INSERT
            # ------------------------------------------------

            existing.add(key)

            inserted += 1

        # ----------------------------------------------------
        # 저장
        # ----------------------------------------------------

        conn.commit()

        # ----------------------------------------------------
        # 결과 출력
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("DB 작업 완료")
        print("=" * 60)

        print(
            f"파싱된 데이터       : "
            f"{len(data):,}개"
        )

        print(
            f"새로 추가           : "
            f"{inserted:,}개"
        )

        print(
            f"기존 데이터 스킵    : "
            f"{skipped:,}개"
        )

        print(
            f"다운로드 실패       : "
            f"{download_failed:,}개"
        )

        print(
            f"최종 데이터 수      : "
            f"{len(existing):,}개"
        )

        print(
            f"아이콘 저장 위치    : "
            f"{ICON_DIR}"
        )

        print("=" * 60)

    except Exception:

        # ----------------------------------------------------
        # 오류 발생 시 전체 롤백
        # ----------------------------------------------------

        conn.rollback()

        print()
        print(
            "DB 작업 중 오류가 발생했습니다."
        )

        print(
            "변경사항을 롤백합니다."
        )

        raise

    finally:
        conn.close()


# ============================================================
# 메인
# ============================================================

def main():

    # --------------------------------------------------------
    # 1. dccon.js 다운로드
    # --------------------------------------------------------

    text = download_dccon_data()

    # --------------------------------------------------------
    # 2. 데이터 파싱
    # --------------------------------------------------------

    print()
    print("dccon 데이터 파싱 중...")

    data = parse_dccon_data(
        text
    )

    print(
        f"파싱 완료: "
        f"{len(data):,}개"
    )

    # --------------------------------------------------------
    # 추가할 데이터가 없는 경우
    # --------------------------------------------------------

    if not data:

        print(
            "추가할 데이터가 없습니다."
        )

        return

    # --------------------------------------------------------
    # 3. 데이터 샘플 출력
    # --------------------------------------------------------

    print()
    print("데이터 샘플")
    print("-" * 60)

    for item in data[:10]:

        print(
            f"name={item['name']}\n"
            f"command={item['command']}\n"
            f"uri={item['uri']}\n"
            f"path={sanitize_filename(item['name'])}\n"
        )

    if len(data) > 10:

        print(
            f"... 외 "
            f"{len(data) - 10:,}개"
        )

    # --------------------------------------------------------
    # 4. DB 삽입
    # --------------------------------------------------------

    print()

    insert_database(
        data
    )


# ============================================================
# 프로그램 시작
# ============================================================

if __name__ == "__main__":
    main()