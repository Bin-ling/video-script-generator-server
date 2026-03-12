# -*- coding: utf-8 -*-
"""
合并提示词工具 - 将同类型模块的提示词合并，减少API调用次数
"""

def create_merged_video_prompt(modules, config_manager):
    sections = []
    
    for module_id in modules:
        module_config = config_manager.get_analysis_module(module_id)
        module_name = module_config.get('name', module_id)
        prompt_template = module_config.get('config', {}).get('input_prompt_template', '')
        
        sections.append(f'''
=== {module_name} ===
{prompt_template}
=== {module_name} 结束 ===
''')
    
    merged_prompt = f'''请依次分析以下视频模块，每个模块独立输出结果：

{''.join(sections)}

注意：每个模块的分析结果必须完整、详细，用 "=== 模块名称 ===" 和 "=== 模块名称 结束 ===" 包裹。'''
    
    return merged_prompt


def create_merged_image_prompt(modules, config_manager):
    sections = []
    
    for module_id in modules:
        module_config = config_manager.get_analysis_module(module_id)
        module_name = module_config.get('name', module_id)
        prompt_template = module_config.get('config', {}).get('input_prompt_template', '')
        
        sections.append(f'''
=== {module_name} ===
{prompt_template}
=== {module_name} 结束 ===
''')
    
    merged_prompt = f'''请依次分析以下图片模块，每个模块独立输出结果：

{''.join(sections)}

注意：每个模块的分析结果必须完整、详细，用 "=== 模块名称 ===" 和 "=== 模块名称 结束 ===" 包裹。'''
    
    return merged_prompt


def create_merged_text_prompt(modules, config_manager, stats, duration):
    data_info = f'''
视频数据：
- 播放量：{stats.get('play', 0)}
- 点赞数：{stats.get('like', 0)}
- 评论数：{stats.get('comment', 0)}
- 收藏数：{stats.get('collect', 0)}
- 分享数：{stats.get('share', 0)}
- 时长：{duration}秒
'''
    
    sections = []
    
    for module_id in modules:
        module_config = config_manager.get_analysis_module(module_id)
        module_name = module_config.get('name', module_id)
        prompt_template = module_config.get('config', {}).get('input_prompt_template', '')
        
        try:
            prompt = prompt_template.format(
                play=stats.get('play', 0),
                like=stats.get('like', 0),
                comment=stats.get('comment', 0),
                collect=stats.get('collect', 0),
                share=stats.get('share', 0),
                duration=duration
            )
        except:
            prompt = prompt_template
        
        sections.append(f'''
=== {module_name} ===
{prompt}
=== {module_name} 结束 ===
''')
    
    merged_prompt = f'''请依次分析以下模块，每个模块独立输出结果：

{data_info}

{''.join(sections)}

注意：每个模块的分析结果必须完整、详细，用 "=== 模块名称 ===" 和 "=== 模块名称 结束 ===" 包裹。'''
    
    return merged_prompt


def parse_merged_result(result_text, modules):
    import re
    
    results = {}
    
    module_name_map = {}
    from config_manager import config_manager
    for module_id in modules:
        module_config = config_manager.get_analysis_module(module_id)
        module_name_map[module_id] = module_config.get('name', module_id)
    
    parsed_count = 0
    for module_id in modules:
        module_name = module_name_map.get(module_id, module_id)
        
        pattern = rf'===\s*{re.escape(module_name)}\s*===\s*\n?(.*?)\s*===\s*{re.escape(module_name)}\s*结束\s*==='
        match = re.search(pattern, result_text, re.DOTALL)
        
        if match:
            results[module_id] = match.group(1).strip()
            parsed_count += 1
        else:
            results[module_id] = ""
    
    if parsed_count == 0:
        parts = re.split(r'\n(?=\d+\.\s)', result_text)
        if len(parts) >= len(modules):
            for i, module_id in enumerate(modules):
                if i < len(parts):
                    results[module_id] = parts[i].strip()
        else:
            if modules:
                results[modules[0]] = result_text.strip()
                for module_id in modules[1:]:
                    results[module_id] = "分析结果未正确拆分，请单独运行该模块"
    
    return results


def group_modules_by_type(enabled_modules, config_manager):
    grouped = {
        'video_analysis': [],
        'image_analysis': [],
        'text_analysis': []
    }
    
    for module_id in enabled_modules:
        module_config = config_manager.get_analysis_module(module_id)
        module_type = module_config.get('type', 'text_analysis')
        if module_type in grouped:
            grouped[module_type].append(module_id)
    
    return grouped
