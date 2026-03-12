import os
import re
import datetime


def ensure_directory(directory):
    """确保目录存在，如果不存在则创建
    
    Args:
        directory: 目录路径
    """
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def create_output_folder(description):
    """创建按时间+简易标题命名的文件夹
    
    Args:
        description: 视频描述
        
    Returns:
        str: 创建的文件夹路径
    """
    # 获取当前时间（使用更紧凑的格式）
    current_time = datetime.datetime.now().strftime('%y%m%d_%H%M')
    
    # 生成简易标题（取前15个字符，去除特殊字符，包括URL特殊字符）
    simple_title = re.sub(r'[\\/:*?"<>|#]', '_', description[:15])
    simple_title = simple_title.strip()
    
    # 如果标题为空，使用默认值
    if not simple_title:
        simple_title = 'video'
    
    # 构建文件夹名称
    folder_name = f"{current_time}_{simple_title}"
    
    # 创建文件夹
    output_dir = os.path.join('output', folder_name)
    os.makedirs(output_dir, exist_ok=True)
    
    return output_dir


def get_relative_path(file_path, base_dir):
    """获取文件相对于基础目录的路径
    
    Args:
        file_path: 文件路径
        base_dir: 基础目录
        
    Returns:
        str: 相对路径
    """
    return os.path.relpath(file_path, base_dir)


def get_file_extension(file_path):
    """获取文件扩展名
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 文件扩展名
    """
    return os.path.splitext(file_path)[1]


def get_file_name(file_path):
    """获取文件名（不含扩展名）
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 文件名
    """
    return os.path.splitext(os.path.basename(file_path))[0]


def join_paths(*paths):
    """安全地连接多个路径
    
    Args:
        *paths: 路径部分
        
    Returns:
        str: 连接后的路径
    """
    return os.path.join(*paths)


def get_parent_directory(file_path):
    """获取父目录
    
    Args:
        file_path: 文件或目录路径
        
    Returns:
        str: 父目录路径
    """
    return os.path.dirname(os.path.abspath(file_path))


def file_exists(file_path):
    """检查文件是否存在
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 文件是否存在
    """
    return os.path.exists(file_path)


def get_file_size(file_path):
    """获取文件大小（MB）
    
    Args:
        file_path: 文件路径
        
    Returns:
        float: 文件大小（MB）
    """
    if not os.path.exists(file_path):
        return 0
    return round(os.path.getsize(file_path) / 1024 / 1024, 2)
