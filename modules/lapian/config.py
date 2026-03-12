import os
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FFMPEG_PATH = os.path.join(os.path.dirname(BASE_DIR), 'FFmpeg', 'ffmpeg.exe')
FFPROBE_PATH = os.path.join(os.path.dirname(BASE_DIR), 'FFmpeg', 'ffprobe.exe')

if not os.path.exists(FFMPEG_PATH):
    found = shutil.which('ffmpeg')
    if found:
        FFMPEG_PATH = found
    else:
        FFMPEG_PATH = 'ffmpeg'
        
if not os.path.exists(FFPROBE_PATH):
    found = shutil.which('ffprobe')
    if found:
        FFPROBE_PATH = found
    else:
        FFPROBE_PATH = 'ffprobe'

DEFAULT_FRAME_FPS = 0.5
DEFAULT_AUDIO_SAMPLE_RATE = 16000
DEFAULT_AUDIO_CHANNELS = 1

SHOT_TYPES = [
    "全景", "中景", "近景", "特写", "大特写", "远景", "中近景"
]

CAMERA_MOVEMENTS = [
    "固定", "推镜", "拉镜", "摇镜", "跟镜", "移镜", "升降", "环绕", "甩镜"
]
