"""
FFmpeg 配置模块
支持 Windows 和 Linux 系统的跨平台 FFmpeg 路径检测
"""

import os
import sys
import shutil
import platform


def get_system_type():
    """获取操作系统类型"""
    return platform.system().lower()


def is_windows():
    """判断是否为 Windows 系统"""
    return get_system_type() == 'windows'


def is_linux():
    """判断是否为 Linux 系统"""
    return get_system_type() == 'linux'


def is_macos():
    """判断是否为 macOS 系统"""
    return get_system_type() == 'darwin'


def get_project_root():
    """获取项目根目录"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(current_dir)


def get_ffmpeg_paths():
    """
    获取 FFmpeg 可执行文件路径列表（按优先级排序）
    
    Returns:
        list: FFmpeg 路径列表
    """
    project_root = get_project_root()
    system = get_system_type()
    
    paths = []
    
    if system == 'windows':
        # Windows 系统
        # 1. 项目内的 ffmpeg-8.0.1-essentials_build 目录
        ffmpeg_build_path = os.path.join(project_root, 'ffmpeg-8.0.1-essentials_build', 'bin', 'ffmpeg.exe')
        if os.path.exists(ffmpeg_build_path):
            paths.append(ffmpeg_build_path)
        
        # 2. 上级目录的 FFmpeg 文件夹
        parent_ffmpeg = os.path.join(os.path.dirname(project_root), 'FFmpeg', 'ffmpeg.exe')
        if os.path.exists(parent_ffmpeg):
            paths.append(parent_ffmpeg)
        
    elif system == 'linux':
        # Linux 系统
        # 1. 项目内的 FFmpeg 目录
        ffmpeg_linux = os.path.join(project_root, 'FFmpeg', 'ffmpeg')
        if os.path.exists(ffmpeg_linux):
            paths.append(ffmpeg_linux)
        
        # 2. 上级目录的 FFmpeg 文件夹
        parent_ffmpeg = os.path.join(os.path.dirname(project_root), 'FFmpeg', 'ffmpeg')
        if os.path.exists(parent_ffmpeg):
            paths.append(parent_ffmpeg)
        
    elif system == 'darwin':
        # macOS 系统
        # 1. 项目内的 FFmpeg 目录
        ffmpeg_mac = os.path.join(project_root, 'FFmpeg', 'ffmpeg')
        if os.path.exists(ffmpeg_mac):
            paths.append(ffmpeg_mac)
        
        # 2. 上级目录的 FFmpeg 文件夹
        parent_ffmpeg = os.path.join(os.path.dirname(project_root), 'FFmpeg', 'ffmpeg')
        if os.path.exists(parent_ffmpeg):
            paths.append(parent_ffmpeg)
    
    return paths


def get_ffprobe_paths():
    """
    获取 FFprobe 可执行文件路径列表（按优先级排序）
    
    Returns:
        list: FFprobe 路径列表
    """
    project_root = get_project_root()
    system = get_system_type()
    
    paths = []
    
    if system == 'windows':
        # Windows 系统
        # 1. 项目内的 ffmpeg-8.0.1-essentials_build 目录
        ffprobe_build_path = os.path.join(project_root, 'ffmpeg-8.0.1-essentials_build', 'bin', 'ffprobe.exe')
        if os.path.exists(ffprobe_build_path):
            paths.append(ffprobe_build_path)
        
        # 2. 上级目录的 FFmpeg 文件夹
        parent_ffprobe = os.path.join(os.path.dirname(project_root), 'FFmpeg', 'ffprobe.exe')
        if os.path.exists(parent_ffprobe):
            paths.append(parent_ffprobe)
        
    elif system == 'linux':
        # Linux 系统
        # 1. 项目内的 FFmpeg 目录
        ffprobe_linux = os.path.join(project_root, 'FFmpeg', 'ffprobe')
        if os.path.exists(ffprobe_linux):
            paths.append(ffprobe_linux)
        
        # 2. 上级目录的 FFmpeg 文件夹
        parent_ffprobe = os.path.join(os.path.dirname(project_root), 'FFmpeg', 'ffprobe')
        if os.path.exists(parent_ffprobe):
            paths.append(parent_ffprobe)
        
    elif system == 'darwin':
        # macOS 系统
        # 1. 项目内的 FFmpeg 目录
        ffprobe_mac = os.path.join(project_root, 'FFmpeg', 'ffprobe')
        if os.path.exists(ffprobe_mac):
            paths.append(ffprobe_mac)
        
        # 2. 上级目录的 FFmpeg 文件夹
        parent_ffprobe = os.path.join(os.path.dirname(project_root), 'FFmpeg', 'ffprobe')
        if os.path.exists(parent_ffprobe):
            paths.append(parent_ffprobe)
    
    return paths


def get_ffmpeg_path():
    """
    获取 FFmpeg 可执行文件路径
    
    Returns:
        str: FFmpeg 可执行文件路径
    """
    # 1. 优先使用项目内的 FFmpeg
    paths = get_ffmpeg_paths()
    if paths:
        return paths[0]
    
    # 2. 尝试从系统 PATH 中查找
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        return ffmpeg_path
    
    # 3. 返回默认值
    return 'ffmpeg'


def get_ffprobe_path():
    """
    获取 FFprobe 可执行文件路径
    
    Returns:
        str: FFprobe 可执行文件路径
    """
    # 1. 优先使用项目内的 FFprobe
    paths = get_ffprobe_paths()
    if paths:
        return paths[0]
    
    # 2. 尝试从系统 PATH 中查找
    ffprobe_path = shutil.which('ffprobe')
    if ffprobe_path:
        return ffprobe_path
    
    # 3. 返回默认值
    return 'ffprobe'


def check_ffmpeg():
    """
    检查 FFmpeg 是否可用
    
    Returns:
        bool: FFmpeg 是否可用
    """
    import subprocess
    
    ffmpeg_path = get_ffmpeg_path()
    try:
        result = subprocess.run(
            [ffmpeg_path, '-version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception as e:
        print(f"FFmpeg 检查失败: {e}")
        return False


def check_ffprobe():
    """
    检查 FFprobe 是否可用
    
    Returns:
        bool: FFprobe 是否可用
    """
    import subprocess
    
    ffprobe_path = get_ffprobe_path()
    try:
        result = subprocess.run(
            [ffprobe_path, '-version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception as e:
        print(f"FFprobe 检查失败: {e}")
        return False


def print_ffmpeg_info():
    """打印 FFmpeg 配置信息"""
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"项目根目录: {get_project_root()}")
    print(f"FFmpeg 路径: {get_ffmpeg_path()}")
    print(f"FFprobe 路径: {get_ffprobe_path()}")
    print(f"FFmpeg 可用: {check_ffmpeg()}")
    print(f"FFprobe 可用: {check_ffprobe()}")


# 导出配置变量
FFMPEG_PATH = get_ffmpeg_path()
FFPROBE_PATH = get_ffprobe_path()

# 默认配置
DEFAULT_FRAME_FPS = 0.5
DEFAULT_AUDIO_SAMPLE_RATE = 16000
DEFAULT_AUDIO_CHANNELS = 1

# 镜头类型
SHOT_TYPES = [
    "全景", "中景", "近景", "特写", "大特写", "远景", "中近景"
]

# 运镜方式
CAMERA_MOVEMENTS = [
    "固定", "推镜", "拉镜", "摇镜", "跟镜", "移镜", "升降", "环绕", "甩镜"
]


if __name__ == "__main__":
    print_ffmpeg_info()
