from modules.video_processor.processor import get_video_info, extract_frames, asr_text, convert_video, extract_audio
from modules.utils.file_utils import create_output_folder
from modules.analysis.analyzer import LargeLanguageModel
from modules.analysis.modules.manager import module_manager
from app.services.llm_service import execute_analysis
from app.services.database_service import insert_analysis
from app.utils.progress_manager import progress
from app.utils.logger import logger
from config_manager import config_manager
import os
import time
import json

llm = None

def init_llm(api_key, base_url, model_name):
    global llm
    try:
        if api_key and api_key != "your_api_key_here":
            llm = LargeLanguageModel(
                api_key=api_key,
                base_url=base_url,
                model_name=model_name
            )
            module_manager.set_llm(llm)
            logger.info("大语言模型初始化成功")
        else:
            logger.warning("大语言模型未初始化：请设置API密钥")
            llm = None
    except Exception as e:
        logger.error(f"大语言模型初始化失败：{e}")
        llm = None

def get_llm_instance():
    global llm
    if llm is None:
        llm = module_manager.get_llm()
    return llm

def process_video(url, path, data_file, video_dir, stats, results, frame_interval=2, video_title=None, video_data_json=None, enabled_modules=None, max_frames=15):
    logger.info(f"开始处理视频: {url}")
    logger.info(f"视频文件路径: {path}")
    logger.info(f"数据文件路径: {data_file}")
    logger.info(f"视频目录: {video_dir}")
    logger.info(f"视频统计数据: {stats}")
    
    if enabled_modules is None:
        try:
            from app.services.module_service import get_enabled_modules
            enabled_modules = get_enabled_modules()
            logger.info(f"从模块服务获取启用的模块: {enabled_modules}")
        except Exception as e:
            logger.error(f"获取启用模块失败: {e}")
            enabled_modules = ['content_analysis', 'data_analysis', 'script_analysis', 'storyboard_analysis']
            logger.info(f"使用默认启用的模块: {enabled_modules}")
    else:
        logger.info(f"传入的启用模块: {enabled_modules}")
    
    module_file_map = {
        'content_analysis': 'content_analysis.json',
        'data_analysis': 'data_analysis.json',
        'script_analysis': 'script_analysis.json',
        'storyboard_analysis': 'storyboard_analysis.json',
        'photo_analysis': 'photo_analysis.json',
        'color_analysis': 'color_analysis.json',
        'bgm_analysis': 'bgm_analysis.json',
        'topic_analysis': 'topic_analysis.json',
        'title_analysis': 'title_analysis.json',
        'cover_analysis': 'cover_analysis.json',
        'publish_time_analysis': 'publish_time_analysis.json'
    }
    
    def save_module_result(module_name, result_data):
        if module_name in module_file_map:
            import time
            import os
            module_file = module_file_map[module_name]
            module_path = os.path.join(output_dir, module_file)
            
            module_config = config_manager.get_analysis_module(module_name)
            analysis_type = module_config.get('type', 'text_analysis')
            module_name_display = module_config.get('name', module_name)
            
            if analysis_type == 'video_analysis':
                output_data = {
                    "timestamp": int(time.time()),
                    "type": "video",
                    "analysis_module": module_name_display,
                    "prompt": module_config.get('config', {}).get('input_prompt_template', ''),
                    "video": {
                        "video_path": os.path.join(output_dir, 'video.mp4'),
                        "analysis_content": result_data
                    },
                    "analysis_method": "api_direct",
                    "analysis_type": "content"
                }
            elif analysis_type == 'image_analysis':
                output_data = {
                    "timestamp": int(time.time()),
                    "type": "image",
                    "analysis_module": module_name_display,
                    "prompt": module_config.get('config', {}).get('input_prompt_template', ''),
                    "frame": {
                        "frames_path": os.path.join(output_dir, 'frames'),
                        "analysis_content": result_data
                    },
                    "analysis_method": "api"
                }
            else:
                output_data = {
                    "timestamp": int(time.time()),
                    "type": "text",
                    "analysis_module": module_name_display,
                    "prompt": module_config.get('config', {}).get('input_prompt_template', ''),
                    "text": {
                        "analysis_content": result_data
                    },
                    "analysis_method": "api",
                    "analysis_type": "text"
                }
            
            with open(module_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            logger.info(f"{module_name} 结果已保存到: {module_file}")
    
    progress["percentage"] = 0
    progress["status"] = "开始处理视频"
    
    logger.info("获取视频信息")
    info = get_video_info(path)
    logger.info(f"视频信息: {info}")
    progress["percentage"] = 10
    progress["status"] = "获取视频信息"
    
    video_data = {}
    if video_data_json:
        video_data = video_data_json
        logger.info("使用传入的视频数据JSON")
    elif data_file and os.path.exists(data_file):
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    video_data = json.load(f)
                logger.info("从数据文件读取视频数据成功")
            except Exception as e:
                logger.error(f'读取视频数据错误: {e}')
    
    progress["percentage"] = 20
    progress["status"] = "创建输出文件夹"
    description = video_data.get('desc', video_title or 'video')
    output_dir = create_output_folder(description)
    logger.info(f"创建输出文件夹: {output_dir}")
    
    progress["percentage"] = 30
    progress["status"] = "提取关键帧"
    logger.info("开始提取关键帧")
    frames = extract_frames(path, interval=frame_interval, max_frames=max_frames, output_dir=output_dir)
    logger.info(f"提取关键帧完成，共提取 {len(frames)} 帧")
    
    progress["percentage"] = 40
    progress["status"] = "提取音频文本"
    text = asr_text(path)
    dur = info['duration']

    frame_paths = []
    for frame in frames:
        relative_path = os.path.relpath(frame, 'output')
        frame_paths.append(relative_path)

    if video_data.get('desc'):
        text = f"视频标题：{video_data['desc']}\n{text}"
    
    text += f"\n\n视频统计数据："
    text += f"\n播放量：{stats.get('play', 0)}"
    text += f"\n点赞数：{stats.get('like', 0)}"
    text += f"\n评论数：{stats.get('comment', 0)}"
    text += f"\n收藏数：{stats.get('collect', 0)}"
    text += f"\n分享数：{stats.get('share', 0)}"
    text += f"\n时长：{dur}秒"

    frame_info = "\n".join([f"帧 {i+1}: {path}" for i, path in enumerate(frame_paths)])
    logger.info(f"视频分析准备了 {len(frame_paths)} 个帧截图路径用于大模型分析")

    analysis_results = {}
    analysis_htmls = {}
    
    from app.services.module_service import get_module_info
    
    progress_mapping = {
        'content_analysis': 50,
        'data_analysis': 55,
        'script_analysis': 60,
        'storyboard_analysis': 65,
        'photo_analysis': 70,
        'color_analysis': 75,
        'bgm_analysis': 80,
        'topic_analysis': 85,
        'title_analysis': 90,
        'cover_analysis': 90,
        'publish_time_analysis': 90
    }
    
    def default_html_parser(content):
        return f"<div>{content}</div>"
    
    html_parsers = {
        'content_analysis': default_html_parser,
        'data_analysis': default_html_parser,
        'script_analysis': default_html_parser,
        'storyboard_analysis': default_html_parser,
        'photo_analysis': default_html_parser,
        'color_analysis': default_html_parser,
        'bgm_analysis': default_html_parser,
        'topic_analysis': default_html_parser,
        'title_analysis': default_html_parser,
        'cover_analysis': default_html_parser,
        'publish_time_analysis': default_html_parser
    }
    
    def analyze_module(module_id):
        module = module_manager.get_module(module_id)
        if not module or not module.is_enabled():
            return module_id, "模块已禁用", f"<div>模块已禁用</div>"
        
        module_name = module.get_name()
        logger.info(f"分析开始 {module_name} 分析")
        
        result = module.analyze(
            video_path=path,
            frames=frames,
            text=text,
            output_dir=output_dir,
            stats=stats,
            duration=dur,
            desc=video_data.get('desc', ''),
            hashtag_names=video_data.get('hashtag_names', []),
            comments=video_data.get('comments', [])
        )
        
        if module_id in html_parsers:
            html_result = html_parsers[module_id](result)
        else:
            html_result = f"<div>{result}</div>"
        
        save_module_result(module_id, result)
        logger.info(f"分析 {module_name} 分析完成")
        
        return module_id, result, html_result
    
    def analyze_merged_modules(module_ids, module_type):
        from app.utils.merged_prompt import (
            create_merged_video_prompt, 
            create_merged_image_prompt, 
            create_merged_text_prompt,
            parse_merged_result
        )
        
        results = {}
        
        current_llm = get_llm_instance()
        if current_llm is None:
            logger.error("大语言模型未初始化，无法进行分析")
            for mid in module_ids:
                results[mid] = "分析失败: 大语言模型未初始化，请检查 API_KEY 配置"
            return results
        
        if module_type == 'video_analysis' and module_ids:
            merged_prompt = create_merged_video_prompt(module_ids, config_manager)
            logger.info(f"合并分析视频模块: {module_ids}")
            
            try:
                result, _ = current_llm.analyze_video_directly(path, merged_prompt, save_result=False)
                results = parse_merged_result(result, module_ids)
            except Exception as e:
                logger.error(f"合并视频分析失败: {e}")
                for mid in module_ids:
                    results[mid] = f"分析失败: {str(e)}"
                    
        elif module_type == 'image_analysis' and module_ids:
            merged_prompt = create_merged_image_prompt(module_ids, config_manager)
            logger.info(f"合并分析图片模块: {module_ids}")
            
            try:
                if frames:
                    result, _ = current_llm.analyze_image(frames[0], merged_prompt, save_result=False)
                    results = parse_merged_result(result, module_ids)
                else:
                    for mid in module_ids:
                        results[mid] = "无关键帧可供分析"
            except Exception as e:
                logger.error(f"合并图片分析失败: {e}")
                for mid in module_ids:
                    results[mid] = f"分析失败: {str(e)}"
                    
        elif module_type == 'text_analysis' and module_ids:
            merged_prompt = create_merged_text_prompt(module_ids, config_manager, stats, dur)
            logger.info(f"合并分析文本模块: {module_ids}")
            
            try:
                result, _ = current_llm.analyze_text(text, merged_prompt, save_result=False)
                results = parse_merged_result(result, module_ids)
            except Exception as e:
                logger.error(f"合并文本分析失败: {e}")
                for mid in module_ids:
                    results[mid] = f"分析失败: {str(e)}"
        
        return results
    
    from app.utils.merged_prompt import group_modules_by_type
    grouped_modules = group_modules_by_type(enabled_modules, config_manager)
    
    logger.info(f"模块分组: {grouped_modules}")
    
    total_groups = sum(1 for v in grouped_modules.values() if v)
    if total_groups > 0:
        progress_step = 45 / total_groups
        current_progress = 50
    
    module_results = []
    
    if grouped_modules['video_analysis']:
        progress["status"] = "分析视频内容..."
        merged_results = analyze_merged_modules(grouped_modules['video_analysis'], 'video_analysis')
        for module_id, result in merged_results.items():
            html_result = html_parsers.get(module_id, default_html_parser)(result)
            save_module_result(module_id, result)
            module_results.append((module_id, result, html_result))
        current_progress += progress_step
        progress["percentage"] = min(current_progress, 95)
    
    if grouped_modules['image_analysis']:
        progress["status"] = "分析关键帧..."
        merged_results = analyze_merged_modules(grouped_modules['image_analysis'], 'image_analysis')
        for module_id, result in merged_results.items():
            html_result = html_parsers.get(module_id, default_html_parser)(result)
            save_module_result(module_id, result)
            module_results.append((module_id, result, html_result))
        current_progress += progress_step
        progress["percentage"] = min(current_progress, 95)
    
    if grouped_modules['text_analysis']:
        progress["status"] = "分析数据..."
        merged_results = analyze_merged_modules(grouped_modules['text_analysis'], 'text_analysis')
        for module_id, result in merged_results.items():
            html_result = html_parsers.get(module_id, default_html_parser)(result)
            save_module_result(module_id, result)
            module_results.append((module_id, result, html_result))
        current_progress += progress_step
        progress["percentage"] = min(current_progress, 95)
    
    for module_id, result, html_result in module_results:
        if module_id and result:
            analysis_results[module_id] = result
            analysis_htmls[module_id] = html_result


    progress["percentage"] = 95
    progress["status"] = "保存分析结果"
    frames_dir = os.path.join(output_dir, 'frames')
    os.makedirs(frames_dir, exist_ok=True)
    
    video_output_path = os.path.join(output_dir, 'video.mp4')
    os.rename(path, video_output_path)
    
    try:
        temp_video_path = os.path.join(output_dir, 'video_temp.mp4')
        success = convert_video(video_output_path, temp_video_path)
        if success and os.path.exists(temp_video_path):
            os.remove(video_output_path)
            os.rename(temp_video_path, video_output_path)
            logger.info('Video converted to H.264 format successfully')
    except Exception as e:
        logger.error(f'Error converting video to H.264: {e}')
    
    audio_output_path = os.path.join(output_dir, 'audio.wav')
    try:
        extract_audio(video_output_path, audio_output_path)
    except Exception as e:
        logger.error(f'Error extracting audio: {e}')
    
    raw_data = {
        'url': url,
        'video_data': video_data,
        'info': info,
        'stats': stats
    }
    raw_data_path = os.path.join(output_dir, 'raw_data.json')
    with open(raw_data_path, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)
    
    modules_data = {}
    for module_id in enabled_modules:
        module_config = config_manager.get_module_config(module_id)
        analysis_type = module_config.get('type', 'text_analysis')
        modules_data[module_id] = {
            'result': analysis_results.get(module_id, ''),
            'analysis_type': analysis_type
        }
    
    analysis_report = {
        'modules': modules_data,
        'metadata': {
            'video_url': url,
            'video_title': video_data.get('desc', '视频分析'),
            'video_duration': dur,
            'frame_count': len(frames),
            'timestamp': int(time.time()),
            'format': 'json'
        }
    }
    report_path = os.path.join(output_dir, 'analysis_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_report, f, ensure_ascii=False, indent=2)

    analysis_data = {
        'url': url,
        'title': video_data.get('desc', '视频分析'),
        'output_dir': output_dir,
        'info': info,
        'stats': stats,
        'enabled_modules': enabled_modules
    }
    
    for module_id in enabled_modules:
        field_mapping = {
            'content_analysis': 'content_ana',
            'data_analysis': 'data_ana',
            'script_analysis': 'script_ana',
            'storyboard_analysis': 'storyboard',
            'photo_analysis': 'photo_ana',
            'color_analysis': 'color_ana',
            'bgm_analysis': 'bgm',
            'topic_analysis': 'topic',
            'title_analysis': 'analysis_title',
            'cover_analysis': 'cover',
            'publish_time_analysis': 'best_time'
        }
        field_name = field_mapping.get(module_id, module_id)
        analysis_data[field_name] = analysis_results.get(module_id, '')
    
    insert_analysis(analysis_data)
    
    progress["percentage"] = 100
    progress["status"] = "分析完成"
    
    frame_urls = []
    for frame in frames:
        relative_path = os.path.relpath(frame, 'output')
        frame_url = f'/output/{relative_path.replace(os.path.sep, "/")}'
        frame_urls.append(frame_url)
    
    if video_dir and os.path.exists(video_dir):
        try:
            for root, dirs, files in os.walk(video_dir):
                for file in files:
                    src_path = os.path.join(root, file)
                    rel_path = os.path.relpath(src_path, video_dir)
                    dst_path = os.path.join(output_dir, 'video_data', rel_path)
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    if os.path.exists(dst_path):
                        os.remove(dst_path)
                    os.rename(src_path, dst_path)
                    logger.info(f"已移动文件: {src_path} → {dst_path}")
            
            if not os.listdir(video_dir):
                os.rmdir(video_dir)
                logger.info(f"已清理空目录: {video_dir}")
        except Exception as e:
            logger.error(f"Error moving video data files: {e}")
    
    result_item = {
        'url': url, 'info': info, 'stats': stats, 'frames': frame_urls,
        'type': '短视频' if dur <= 180 else '长视频',
        'output_dir': output_dir
    }
    
    for module_id in enabled_modules:
        field_mapping = {
            'content_analysis': 'content_ana',
            'data_analysis': 'data_ana',
            'script_analysis': 'script_ana',
            'storyboard_analysis': 'storyboard',
            'photo_analysis': 'photo_ana',
            'color_analysis': 'color_ana',
            'bgm_analysis': 'bgm',
            'topic_analysis': 'topic',
            'title_analysis': 'analysis_title',
            'cover_analysis': 'cover',
            'publish_time_analysis': 'best_time'
        }
        field_name = field_mapping.get(module_id, module_id)
        result_item[field_name] = analysis_results.get(module_id, '')
    
    html_field_mapping = {
        'content_analysis': 'content_ana',
        'data_analysis': 'data_ana',
        'script_analysis': 'script_ana',
        'storyboard_analysis': 'storyboard',
        'photo_analysis': 'photo_ana',
        'color_analysis': 'color_ana',
        'bgm_analysis': 'bgm',
        'topic_analysis': 'topic',
        'title_analysis': 'title',
        'cover_analysis': 'cover',
        'publish_time_analysis': 'best_time'
    }
    
    for module_id in enabled_modules:
        field_name = html_field_mapping.get(module_id, module_id)
        result_item[field_name] = analysis_htmls.get(module_id, '')
    
    results.append(result_item)


def load_analysis_result(request):
    data = request.get_json()
    file_name = data.get('file_name')
    
    if not file_name or not os.path.exists(file_name):
        return {'error': '文件不存在'}
    
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        return analysis_data
    except Exception as e:
        return {'error': str(e)}
