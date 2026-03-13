"""
拉片模块配置
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from modules.utils.ffmpeg_config import (
    FFMPEG_PATH, FFPROBE_PATH,
    DEFAULT_FRAME_FPS, DEFAULT_AUDIO_SAMPLE_RATE, DEFAULT_AUDIO_CHANNELS,
    SHOT_TYPES, CAMERA_MOVEMENTS,
    print_ffmpeg_info
)

__all__ = [
    'FFMPEG_PATH', 'FFPROBE_PATH',
    'DEFAULT_FRAME_FPS', 'DEFAULT_AUDIO_SAMPLE_RATE', 'DEFAULT_AUDIO_CHANNELS',
    'SHOT_TYPES', 'CAMERA_MOVEMENTS',
    'print_ffmpeg_info'
]
