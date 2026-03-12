import os
import json
from datetime import datetime


def format_time_display(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:05.2f}"


def format_time_range(start_time, end_time):
    return f"{format_time_display(start_time)} - {format_time_display(end_time)}"


def calculate_statistics(shots):
    if not shots:
        return {}

    total_duration = sum(shot.get('duration', 0) for shot in shots)

    shot_types = {}
    for shot in shots:
        shot_type = shot.get('shot_type', '未知')
        shot_types[shot_type] = shot_types.get(shot_type, 0) + 1

    camera_movements = {}
    for shot in shots:
        movement = shot.get('camera_movement', '固定')
        camera_movements[movement] = camera_movements.get(movement, 0) + 1

    durations = [shot.get('duration', 0) for shot in shots]
    avg_duration = sum(durations) / len(durations) if durations else 0
    min_duration = min(durations) if durations else 0
    max_duration = max(durations) if durations else 0

    return {
        'total_shots': len(shots),
        'total_duration': round(total_duration, 2),
        'avg_duration': round(avg_duration, 2),
        'min_duration': round(min_duration, 2),
        'max_duration': round(max_duration, 2),
        'shot_types': shot_types,
        'camera_movements': camera_movements
    }


def generate_report(video_path, shots, extraction_results=None, video_info=None, script_text=""):
    report = {
        'report_type': '视频拉片报告',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'video': {
            'path': video_path,
            'name': os.path.basename(video_path),
            'info': video_info or {}
        },
        'summary': {},
        'shots': [],
        'statistics': {},
        'script': script_text[:1000] if script_text else ""
    }

    shot_list = []
    for shot in shots:
        shot_id = shot.get('shot_id', 0)
        start_time = shot.get('start_time', 0)
        end_time = shot.get('end_time', 0)

        file_path = ""
        if extraction_results:
            for extracted in extraction_results.get('extracted_shots', []):
                if extracted.get('shot_id') == shot_id:
                    file_path = extracted.get('file_path', '')
                    break

        shot_info = {
            'shot_id': shot_id,
            'time_range': format_time_range(start_time, end_time),
            'start_time': start_time,
            'end_time': end_time,
            'duration': round(end_time - start_time, 3),
            'shot_type': shot.get('shot_type', '未知'),
            'camera_movement': shot.get('camera_movement', '固定'),
            'content': shot.get('content', ''),
            'key_elements': shot.get('key_elements', []),
            'file_path': file_path
        }

        shot_list.append(shot_info)

    report['shots'] = shot_list

    stats = calculate_statistics(shot_list)
    report['statistics'] = stats
    report['summary'] = {
        'total_shots': stats.get('total_shots', 0),
        'total_duration': stats.get('total_duration', 0),
        'avg_shot_duration': stats.get('avg_duration', 0),
        'main_shot_type': max(stats.get('shot_types', {}).items(), key=lambda x: x[1])[0] if stats.get('shot_types') else '未知',
        'main_camera_movement': max(stats.get('camera_movements', {}).items(), key=lambda x: x[1])[0] if stats.get('camera_movements') else '未知'
    }

    return report


def save_report(report, output_path):
    try:
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return output_path
    except Exception as e:
        return None


def generate_markdown_report(report, output_path):
    lines = []

    lines.append(f"# 视频拉片报告")
    lines.append("")
    lines.append(f"**生成时间**: {report.get('generated_at', '')}")
    lines.append(f"**视频文件**: {report.get('video', {}).get('name', '')}")
    lines.append("")

    summary = report.get('summary', {})
    lines.append("## 概览")
    lines.append("")
    lines.append(f"| 指标 | 数值 |")
    lines.append(f"| --- | --- |")
    lines.append(f"| 镜头总数 | {summary.get('total_shots', 0)} |")
    lines.append(f"| 总时长 | {summary.get('total_duration', 0)}秒 |")
    lines.append(f"| 平均镜头时长 | {summary.get('avg_shot_duration', 0)}秒 |")
    lines.append(f"| 主要景别 | {summary.get('main_shot_type', '未知')} |")
    lines.append(f"| 主要运镜 | {summary.get('main_camera_movement', '未知')} |")
    lines.append("")

    stats = report.get('statistics', {})
    if stats.get('shot_types'):
        lines.append("### 景别分布")
        lines.append("")
        for shot_type, count in stats['shot_types'].items():
            lines.append(f"- {shot_type}: {count} 个")
        lines.append("")

    if stats.get('camera_movements'):
        lines.append("### 运镜分布")
        lines.append("")
        for movement, count in stats['camera_movements'].items():
            lines.append(f"- {movement}: {count} 个")
        lines.append("")

    lines.append("## 镜头详情")
    lines.append("")
    lines.append("| 编号 | 时间段 | 时长 | 景别 | 运镜 | 内容 |")
    lines.append("| --- | --- | --- | --- | --- | --- |")

    for shot in report.get('shots', []):
        lines.append(f"| {shot.get('shot_id', '')} | {shot.get('time_range', '')} | {shot.get('duration', '')}秒 | {shot.get('shot_type', '')} | {shot.get('camera_movement', '')} | {shot.get('content', '')[:30]} |")

    lines.append("")

    script = report.get('script', '')
    if script:
        lines.append("## 脚本内容")
        lines.append("")
        lines.append(f"```\n{script}\n```")
        lines.append("")

    content = '\n'.join(lines)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return output_path
    except Exception as e:
        return None
