from moviepy.video.VideoClip import ImageClip, TextClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.fx.resize import resize
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

from . import utils, log_util

def is_image(name):
    return name.split('.')[-1].upper() in ['GIF', 'PNG', 'JPG', 'JPEG']

def is_gif(name):
    return name.split('.')[-1].upper() == 'GIF'

def get_image_type(name):
    return name.split('.')[-1].upper()

def is_gif_animated(name):
    clip = VideoFileClip(name)
    count = 0
    for f in clip.iter_frames():
        count += 1

    return count > 1

def get_image_meta(img_path):
    try:
        meta = {}
        meta['timestamp'] = str(os.path.getctime(img_path))
        meta['file_size'] = os.path.getsize(img_path)
        if get_image_type(img_path) == "GIF":
            vi = VideoFileClip(full_path)
            meta['width'] = vi.size[0]
            meta['height'] = vi.size[1]
            meta['duration'] = int(vi.duration * 1000) # in ms
        else:
            # static image
            im = ImageClip(img_path)
            meta['width'] = im.size[0]
            meta['height'] = im.size[1]
        log_util.debug("image meta: %s", meta)
        return meta
    except Exception as e:
        log_util.error("get image meta data fail: %s", str(e))
        raise


def calc_quality(full_path):
    try:
        cmd = 'identify -format "%Q \n" ' + "\"" + full_path + "\""
        score = int(subprocess.getoutput(cmd))
        return score
    except Exception as e:
        print("calc quality fail: %s" %str(e))
        return 0