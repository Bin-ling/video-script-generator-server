import subprocess
import os
import json
import time


def get_ffmpeg_path():
    """获取 FFmpeg 可执行文件路径
    
    Returns:
        str: FFmpeg 可执行文件路径
    """
    # 尝试从上级目录的 FFmpeg 文件夹获取
    ffmpeg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'FFmpeg', 'ffmpeg.exe')
    if not os.path.exists(ffmpeg_path):
        # 尝试直接使用系统路径中的 ffmpeg
        ffmpeg_path = 'ffmpeg'
    return ffmpeg_path


def get_ffprobe_path():
    """获取 FFprobe 可执行文件路径
    
    Returns:
        str: FFprobe 可执行文件路径
    """
    # 尝试从上级目录的 FFmpeg 文件夹获取
    ffprobe_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'FFmpeg', 'ffprobe.exe')
    if not os.path.exists(ffprobe_path):
        # 尝试直接使用系统路径中的 ffprobe
        ffprobe_path = 'ffprobe'
    return ffprobe_path


def get_video_info(path):
    """获取视频信息
    
    Args:
        path: 视频文件路径
        
    Returns:
        dict: 包含 duration, fps, width, height, size_mb 的字典
    """
    try:
        ffprobe_path = get_ffprobe_path()
        
        cmd = [
            ffprobe_path, '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', path
        ]
        result = subprocess.run(cmd, capture_output=True, text=False, timeout=30)
        
        if result.returncode == 0:
            data = json.loads(result.stdout.decode('utf-8'))
            duration = float(data['format'].get('duration', 0))
            size_mb = round(os.path.getsize(path) / 1024 / 1024, 2)
            
            width = 1920
            height = 1080
            fps = 30
            
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    width = int(stream.get('width', 1920))
                    height = int(stream.get('height', 1080))
                    if 'r_frame_rate' in stream:
                        num, den = stream['r_frame_rate'].split('/')
                        fps = round(int(num) / int(den), 2)
            
            return {
                'duration': round(duration, 2),
                'fps': fps,
                'width': width,
                'height': height,
                'size_mb': size_mb
            }
        else:
            return {
                'duration': 0,
                'fps': 30,
                'width': 1920,
                'height': 1080,
                'size_mb': round(os.path.getsize(path) / 1024 / 1024, 2)
            }
    except:
        return {'duration': 0, 'fps': 30, 'width': 1920, 'height': 1080, 'size_mb': 0}


def extract_frames(path, interval=2, max_frames=15, output_dir=None):
    """从视频中提取帧
    
    Args:
        path: 视频文件路径
        interval: 提取间隔（秒）
        max_frames: 最大帧数
        output_dir: 输出目录
        
    Returns:
        list: 提取的帧文件路径列表
    """
    try:
        if output_dir:
            frames_dir = os.path.join(output_dir, 'frames')
        else:
            frames_dir = 'static/frames'
        
        os.makedirs(frames_dir, exist_ok=True)
        
        if output_dir:
            folder_name = os.path.basename(output_dir)
            prefix = folder_name.split('_')[0]
        else:
            prefix = str(int(time.time()))
        
        frame_list = []
        info = get_video_info(path)
        duration = info.get('duration', 0)
        
        actual_frames = min(max_frames, int(duration / interval) + 1)
        if actual_frames < 1:
            actual_frames = 1
        
        ffmpeg_path = get_ffmpeg_path()
        
        try:
            for i in range(actual_frames):
                timestamp_point = i * interval
                fname = os.path.join(frames_dir, f'frame_{prefix}_{i}.jpg')
                cmd = [
                    ffmpeg_path, '-i', path,
                    '-ss', str(timestamp_point),
                    '-vframes', '1',
                    '-q:v', '2',
                    '-y',
                    fname
                ]
                result = subprocess.run(cmd, capture_output=True, text=False, timeout=30)
                if result.returncode == 0 and os.path.exists(fname):
                    frame_list.append(fname)
            
            if frame_list:
                print(f'Successfully extracted {len(frame_list)} frames using FFmpeg')
                return frame_list
        except Exception as e:
            print(f'FFmpeg extraction failed: {e}')
            print('Trying alternative methods...')
        
        try:
            import cv2
            print('Trying OpenCV for frame extraction...')
            
            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                raise Exception('Cannot open video file')
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            frame_interval = int(fps * interval)
            if frame_interval < 1:
                frame_interval = 1
            
            current_frame = 0
            frame_count = 0
            
            while cap.isOpened() and frame_count < actual_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if current_frame % frame_interval == 0:
                    fname = os.path.join(frames_dir, f'frame_{prefix}_{frame_count}.jpg')
                    cv2.imwrite(fname, frame)
                    frame_list.append(fname)
                    frame_count += 1
                
                current_frame += 1
            
            cap.release()
            
            if frame_list:
                print(f'Successfully extracted {len(frame_list)} frames using OpenCV')
                return frame_list
        except Exception as e:
            print(f'OpenCV extraction failed: {e}')
        
        try:
            import imageio
            print('Trying imageio for frame extraction...')
            
            reader = imageio.get_reader(path)
            fps = reader.get_meta_data().get('fps', 30)
            total_frames = len(reader)
            
            frame_interval = int(fps * interval)
            if frame_interval < 1:
                frame_interval = 1
            
            frame_count = 0
            for i, frame in enumerate(reader):
                if i % frame_interval == 0 and frame_count < actual_frames:
                    fname = os.path.join(frames_dir, f'frame_{prefix}_{frame_count}.jpg')
                    imageio.imwrite(fname, frame)
                    frame_list.append(fname)
                    frame_count += 1
                
                if frame_count >= actual_frames:
                    break
            
            if frame_list:
                print(f'Successfully extracted {len(frame_list)} frames using imageio')
                return frame_list
        except Exception as e:
            print(f'imageio extraction failed: {e}')
        
        print('All frame extraction methods failed')
        return []
    except Exception as e:
        print(f'Error extracting frames: {e}')
        return []


def extract_audio(path, output_path=None, sample_rate=16000, channels=1):
    """从视频中提取音频
    
    Args:
        path: 视频文件路径
        output_path: 输出音频文件路径（默认为视频文件名替换为.wav）
        sample_rate: 采样率（默认16000）
        channels: 声道数（默认1）
        
    Returns:
        str: 提取的音频文件路径，失败返回None
    """
    try:
        if output_path is None:
            output_path = path.replace('.mp4', '.wav')
        
        ffmpeg_path = get_ffmpeg_path()
        
        cmd = [
            ffmpeg_path, '-i', path,
            '-vn', '-acodec', 'pcm_s16le', '-ar', str(sample_rate), '-ac', str(channels),
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=False, timeout=60)
        
        if result.returncode == 0 and os.path.exists(output_path):
            print(f'Successfully extracted audio to: {output_path}')
            return output_path
        else:
            print(f'Audio extraction failed with return code: {result.returncode}')
            return None
    except Exception as e:
        print(f'Error extracting audio: {e}')
        return None


def extract_subtitle(path):
    """提取视频字幕
    
    Args:
        path: 视频文件路径
        
    Returns:
        str: 字幕文本，失败返回None
    """
    try:
        vtt_path = path.replace('.mp4', '.zh-CN.vtt')
        if os.path.exists(vtt_path):
            with open(vtt_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = []
                for line in content.split('\n'):
                    if '-->' not in line and not line.strip().isdigit() and line.strip() and 'WEBVTT' not in line:
                        lines.append(line.strip())
                return ' '.join(lines)
        return None
    except Exception as e:
        print(f'Error extracting subtitle: {e}')
        return None


def asr_text(path):
    """提取视频音频并进行语音识别（占位符实现）
    
    Args:
        path: 视频文件路径
        
    Returns:
        str: 识别的文本或错误信息
    """
    try:
        subtitle = extract_subtitle(path)
        if subtitle:
            return subtitle
        
        audio_path = extract_audio(path)
        if audio_path:
            try:
                result_text = 'Audio extracted, ASR not implemented yet. Video content analysis based on visual features.'
                os.remove(audio_path)
                return result_text
            except Exception as e:
                print(f'Error removing temporary audio file: {e}')
                return 'Auto subtitle failed: Audio processing failed'
        else:
            return 'Auto subtitle failed: Audio extraction failed'
    except Exception as e:
        print(f'Error in asr_text: {e}')
        return 'Subtitle failed'


def convert_video(input_path, output_path, codec='libx264', crf=23, preset='medium'):
    """转换视频格式
    
    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        codec: 视频编码器（默认libx264）
        crf: 质量参数（默认23）
        preset: 编码预设（默认medium）
        
    Returns:
        bool: 转换是否成功
    """
    try:
        ffmpeg_path = get_ffmpeg_path()
        
        cmd = [
            ffmpeg_path, '-i', input_path,
            '-c:v', codec, '-crf', str(crf), '-preset', preset,
            '-c:a', 'aac', '-b:a', '128k',
            '-y', output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=False, timeout=300)
        
        if result.returncode == 0 and os.path.exists(output_path):
            print(f'Successfully converted video to: {output_path}')
            return True
        else:
            print(f'Video conversion failed with return code: {result.returncode}')
            return False
    except Exception as e:
        print(f'Error converting video: {e}')
        return False


def get_thumbnail(path, output_path=None, timestamp=0, width=320, height=180):
    """获取视频缩略图
    
    Args:
        path: 视频文件路径
        output_path: 输出图片路径（默认为视频文件名替换为.jpg）
        timestamp: 截取时间点（秒，默认0）
        width: 缩略图宽度（默认320）
        height: 缩略图高度（默认180）
        
    Returns:
        str: 缩略图文件路径，失败返回None
    """
    try:
        if output_path is None:
            output_path = path.replace('.mp4', '_thumb.jpg')
        
        ffmpeg_path = get_ffmpeg_path()
        
        cmd = [
            ffmpeg_path, '-i', path,
            '-ss', str(timestamp),
            '-vframes', '1',
            '-vf', f'scale={width}:{height}',
            '-q:v', '2',
            '-y', output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=False, timeout=30)
        
        if result.returncode == 0 and os.path.exists(output_path):
            print(f'Successfully created thumbnail: {output_path}')
            return output_path
        else:
            print(f'Thumbnail creation failed with return code: {result.returncode}')
            return None
    except Exception as e:
        print(f'Error creating thumbnail: {e}')
        return None
