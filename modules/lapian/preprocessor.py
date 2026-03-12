import subprocess
import os
import json
import time
from modules.lapian.config import FFMPEG_PATH, FFPROBE_PATH, DEFAULT_FRAME_FPS, DEFAULT_AUDIO_SAMPLE_RATE, DEFAULT_AUDIO_CHANNELS


def get_video_info(video_path):
    try:
        cmd = [
            FFPROBE_PATH, '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=False, timeout=30)

        if result.returncode == 0:
            data = json.loads(result.stdout.decode('utf-8'))
            duration = float(data['format'].get('duration', 0))
            size_mb = round(os.path.getsize(video_path) / 1024 / 1024, 2)

            width = 1920
            height = 1080
            fps = 30

            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    width = int(stream.get('width', 1920))
                    height = int(stream.get('height', 1080))
                    if 'r_frame_rate' in stream:
                        num, den = stream['r_frame_rate'].split('/')
                        if int(den) != 0:
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
                'size_mb': round(os.path.getsize(video_path) / 1024 / 1024, 2)
            }
    except Exception as e:
        print(f"获取视频信息失败: {e}")
        return {'duration': 0, 'fps': 30, 'width': 1920, 'height': 1080, 'size_mb': 0}


def extract_audio(video_path, output_path=None, sample_rate=None, channels=None):
    if sample_rate is None:
        sample_rate = DEFAULT_AUDIO_SAMPLE_RATE
    if channels is None:
        channels = DEFAULT_AUDIO_CHANNELS

    if output_path is None:
        base_name = os.path.splitext(video_path)[0]
        output_path = base_name + '.wav'

    try:
        cmd = [
            FFMPEG_PATH, '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le',
            '-ar', str(sample_rate),
            '-ac', str(channels),
            '-y', output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=False, timeout=120)

        if result.returncode == 0 and os.path.exists(output_path):
            return output_path
        else:
            return None
    except Exception as e:
        return None


def extract_frames(video_path, output_dir, fps=None):
    if fps is None:
        fps = DEFAULT_FRAME_FPS

    frames_dir = os.path.join(output_dir, 'frames')
    os.makedirs(frames_dir, exist_ok=True)

    try:
        output_pattern = os.path.join(frames_dir, 'frame_%04d.jpg')

        cmd = [
            FFMPEG_PATH, '-i', video_path,
            '-vf', f'fps={fps}',
            '-q:v', '2',
            '-y', output_pattern
        ]

        result = subprocess.run(cmd, capture_output=True, text=False, timeout=120)

        if result.returncode == 0:
            frames = sorted([
                os.path.join(frames_dir, f)
                for f in os.listdir(frames_dir)
                if f.endswith('.jpg')
            ])
            return frames
        else:
            return []
    except Exception as e:
        return []


def transcribe_audio(audio_path, model_size="base", language="zh"):
    try:
        import whisper
    except ImportError:
        print("Whisper未安装，请运行: pip install openai-whisper")
        return None

    try:
        model = whisper.load_model(model_size)
        result = model.transcribe(audio_path, language=language)

        text = result.get('text', '')
        segments = []

        for seg in result.get('segments', []):
            segments.append({
                'start': seg.get('start', 0),
                'end': seg.get('end', 0),
                'text': seg.get('text', '').strip()
            })

        return {
            'text': text,
            'segments': segments
        }
    except Exception as e:
        print(f"语音转写错误: {e}")
        return None


def generate_srt(segments, output_path):
    def format_time(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(segments, 1):
                start_time = format_time(seg['start'])
                end_time = format_time(seg['end'])
                text = seg['text']

                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")

        return output_path
    except Exception as e:
        return None


def preprocess_video(video_path, output_dir, fps=None, transcribe=True, model_size="base"):
    os.makedirs(output_dir, exist_ok=True)

    result = {
        'video_path': video_path,
        'output_dir': output_dir,
        'video_info': None,
        'audio_path': None,
        'frames': [],
        'transcription': None,
        'srt_path': None
    }

    video_info = get_video_info(video_path)
    result['video_info'] = video_info

    audio_path = extract_audio(video_path, os.path.join(output_dir, 'audio.wav'))
    result['audio_path'] = audio_path

    frames = extract_frames(video_path, output_dir, fps)
    result['frames'] = frames

    if transcribe and audio_path:
        transcription = transcribe_audio(audio_path, model_size)
        if transcription:
            result['transcription'] = transcription

            srt_path = os.path.join(output_dir, 'subtitle.srt')
            srt_result = generate_srt(transcription['segments'], srt_path)
            result['srt_path'] = srt_result

            txt_path = os.path.join(output_dir, 'script.txt')
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(transcription['text'])

    return result
