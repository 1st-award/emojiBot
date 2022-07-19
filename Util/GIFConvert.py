from PIL import Image


class ResizeFrame:
    def __init__(self, length, gif, scale, actual_frames):
        self.current = 0
        self.stop = length
        self.gif = gif
        self.scale = scale
        self.actual_frames = actual_frames

    def __anext__(self):
        return self

    async def __anext__(self):
        print(f"run async for... current {self.current} until {self.stop}")
        if self.current < self.stop:
            self.gif.seek(self.actual_frames[self.current])
            new_frame = Image.new('RGBA', self.gif.size)
            new_frame.paste(self.gif)
            return new_frame.thumbnail(self.scale, Image.ANTIALIAS)
        else:
            raise StopAsyncIteration


def scale_gif(path, scale, new_path=None):
    gif = Image.open(path)
    if not new_path:
        new_path = path
    old_gif_information = {
        'loop': bool(gif.info.get('loop', 1)),
        'duration': gif.info.get('duration', 40),
        'background': gif.info.get('background', 223),
        'extension': gif.info.get('extension', (b'NETSCAPE2.0')),
        'transparency': gif.info.get('transparency', 223)
    }
    new_frames = get_new_frames(gif, scale)
    save_new_gif(new_frames, old_gif_information, new_path)


def get_new_frames(gif, scale):
    new_frames = []
    actual_frames = gif.n_frames
    for frame in range(actual_frames):
        gif.seek(frame)
        new_frame = Image.new('RGBA', gif.size)
        new_frame.paste(gif)
        new_frame.thumbnail(scale, Image.ANTIALIAS)
        new_frames.append(new_frame)
    return new_frames


def save_new_gif(new_frames, old_gif_information, new_path):
    new_frames[0].save(new_path,
                       save_all=True,
                       append_images=new_frames[1:],
                       duration=old_gif_information['duration'],
                       loop=old_gif_information['loop'],
                       background=old_gif_information['background'],
                       extension=old_gif_information['extension'],
                       transparency=old_gif_information['transparency'])
