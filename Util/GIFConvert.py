import logging
logger = logging.getLogger(__name__)
from PIL import Image


def scale_gif(path, scale, new_path=None):
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
    new_frames[0].save(new_path,
                       save_all=True,
                       append_images=new_frames[1:],
                       duration=old_gif_information['duration'],
                       loop=old_gif_information['loop'])
