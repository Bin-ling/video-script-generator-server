import subprocess
import os
import json
import time
import shutil


def format_time_ms(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def get_ffmpeg_path():
    """获取 FFmpeg 路径"""
    from modules.lapian.config import FFMPEG_PATH
    
    if os.path.exists(FFMPEG_PATH):
        return FFMPEG_PATH
    
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        return ffmpeg_path
    
    return 'ffmpeg'


def check_ffmpeg():
    """检查 FFmpeg 是否可用"""
    ffmpeg = get_ffmpeg_path()
    try:
        result = subprocess.run(
            [ffmpeg, '-version'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False


def extract_shot(video_path, start_time, end_time, output_path, copy_streams=True):
    try:
        start_str = format_time_ms(start_time)
        duration = end_time - start_time

        if duration <= 0:
            print(f"  时长无效: {duration}")
            return False

        ffmpeg = get_ffmpeg_path()

        cmd = [ffmpeg, '-y', '-hide_banner', '-loglevel', 'error']

        cmd.extend(['-ss', start_str])
        cmd.extend(['-i', video_path])
        cmd.extend(['-t', str(duration)])

        if copy_streams:
            cmd.extend(['-c:v', 'copy', '-c:a', 'copy'])
        else:
            cmd.extend(['-c:v', 'libx264', '-crf', '23', '-preset', 'fast'])
            cmd.extend(['-c:a', 'aac', '-b:a', '128k'])

        cmd.append(output_path)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0 and os.path.exists(output_path):
            return True
        else:
            if result.stderr:
                print(f"  错误: {result.stderr[:200]}")
            return False

    except Exception as e:
        print(f"  异常: {e}")
        return False


def extract_all_shots(video_path, shots, output_dir, copy_streams=True):
    shots_dir = os.path.join(output_dir, 'shots')
    os.makedirs(shots_dir, exist_ok=True)

    results = {
        'video_path': video_path,
        'output_dir': shots_dir,
        'total_shots': len(shots),
        'extracted_shots': [],
        'failed_shots': [],
        'total_time': 0
    }

    print(f"\n开始提取 {len(shots)} 个镜头...")

    if not check_ffmpeg():
        print("警告: FFmpeg 未安装或不在 PATH 中")
        print("镜头提取将被跳过")
        return results

    start_total = time.time()

    for i, shot in enumerate(shots):
        shot_id = shot.get('shot_id', i + 1)
        start_time = shot.get('start_time', 0)
        end_time = shot.get('end_time', 0)

        output_filename = f"shot_{shot_id:03d}.mp4"
        output_path = os.path.join(shots_dir, output_filename)

        print(f"\n提取镜头 {shot_id}/{len(shots)}: {format_time_ms(start_time)} - {format_time_ms(end_time)}")

        success = extract_shot(video_path, start_time, end_time, output_path, copy_streams)

        if success:
            file_size = os.path.getsize(output_path) / 1024 / 1024
            shot_result = {
                'shot_id': shot_id,
                'start_time': start_time,
                'end_time': end_time,
                'duration': round(end_time - start_time, 3),
                'file_path': output_path,
                'file_name': output_filename,
                'file_size_mb': round(file_size, 2),
                'shot_type': shot.get('shot_type', '未知'),
                'camera_movement': shot.get('camera_movement', '固定'),
                'content': shot.get('content', '')
            }
            results['extracted_shots'].append(shot_result)
            print(f"  ✓ 成功 ({file_size:.2f}MB)")
        else:
            results['failed_shots'].append({
                'shot_id': shot_id,
                'start_time': start_time,
                'end_time': end_time,
                'error': '提取失败'
            })
            print(f"  ✗ 失败")

    results['total_time'] = round(time.time() - start_total, 2)

    print(f"\n镜头提取完成! 成功: {len(results['extracted_shots'])} 个, 失败: {len(results['failed_shots'])} 个")

    return results


def extract_shot_with_frame(video_path, start_time, end_time, output_path, thumbnail_path=None):
    result = {
        'success': False,
        'video_path': output_path,
        'thumbnail_path': None
    }

    if extract_shot(video_path, start_time, end_time, output_path):
        result['success'] = True

        if thumbnail_path:
            mid_time = (start_time + end_time) / 2
            ffmpeg = get_ffmpeg_path()
            cmd = [
                ffmpeg, '-y', '-ss', format_time_ms(mid_time),
                '-i', video_path,
                '-vframes', '1',
                '-q:v', '2',
                '-vf', 'scale=320:-1',
                thumbnail_path
            ]

            try:
                subprocess.run(cmd, capture_output=True, timeout=30)
                if os.path.exists(thumbnail_path):
                    result['thumbnail_path'] = thumbnail_path
            except:
                pass

    return result
