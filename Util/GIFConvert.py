import logging
logger = logging.getLogger(__name__)
from PIL import Image


def scale_gif(path, scale, new_path=None):
    """GIF를 scale=(최대 너비, 최대 높이)에 맞춰 축소해 저장한다.

    반복 횟수와 프레임별 재생 시간을 유지하며, new_path가 없으면 원본을 덮어쓴다.
    처리 후 생성한 프레임을 모두 닫는다.
    """
    with Image.open(path) as gif:
        information = {"loop": gif.info.get("loop", 0)}
        frames = get_new_frames(gif, scale)
        information["duration"] = [frame.info.get("duration", 40) for frame in frames]
    try:
        save_new_gif(frames, information, new_path or path)
    finally:
        for frame in frames:
            frame.close()


def get_new_frames(gif, scale):
    """열린 GIF의 프레임을 비율을 유지하며 scale 범위로 축소한 RGBA 이미지 목록으로 반환한다.

    각 프레임의 재생 시간을 info에 보관하며 반환 이미지들은 호출자가 닫아야 한다.
    """
    new_frames = []
    actual_frames = gif.n_frames
    for frame in range(actual_frames):
        gif.seek(frame)
        new_frame = Image.new('RGBA', gif.size)
        new_frame.paste(gif)
        new_frame.thumbnail(scale, Image.Resampling.LANCZOS)
        new_frame.info["duration"] = gif.info.get("duration", 40)
        new_frames.append(new_frame)
    return new_frames


def save_new_gif(new_frames, old_gif_information, new_path):
    """프레임 목록을 재생 시간·반복 정보와 함께 new_path에 GIF로 저장한다.

    new_frames는 비어 있지 않아야 하며 old_gif_information에 duration과 loop가 필요하다.
    """
    new_frames[0].save(new_path,
                       save_all=True,
                       append_images=new_frames[1:],
                       duration=old_gif_information['duration'],
                       loop=old_gif_information['loop'])
