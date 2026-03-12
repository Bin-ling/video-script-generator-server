#!/usr/bin/env python3

import json
import os
from dotenv import load_dotenv

class ConfigManager:
    
    def __init__(self, analysis_modules_file='configs/analysis_modules.json'):
        load_dotenv()
        self.analysis_modules_file = analysis_modules_file
        self.config = self._get_default_config()
        self.analysis_modules = self._load_analysis_modules()
    
    def _load_analysis_modules(self):
        if os.path.exists(self.analysis_modules_file):
            try:
                with open(self.analysis_modules_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('modules', {})
            except Exception as e:
                print(f"加载分析模块配置失败：{e}")
                return self._get_default_analysis_modules()
        else:
            print(f"分析模块配置文件 {self.analysis_modules_file} 不存在，使用默认配置")
            return self._get_default_analysis_modules()
    
    def _get_default_config(self):
        config = {
            "system_settings": {
                "max_file_size": 500 * 1024 * 1024,
                "max_comments": 1000,
                "max_replies": 20,
                "thread_pool_size": os.cpu_count() * 2 if os.cpu_count() else 8
            }
        }
        return config
    
    def _get_default_analysis_modules(self):
        return {
            "content_analysis": {
                "id": "content_analysis",
                "name": "内容分析",
                "description": "分析视频内容、主题、受众等",
                "type": "video_analysis",
                "enabled": True,
                "config": {
                    "input_prompt_template": "你是专业的{module_name}分析师。根据以下视频内容和关键帧信息，分析：\n{output_keywords}",
                    "output_keywords": ["主题与受众", "情绪节奏与爆点", "文案钩子", "爆款逻辑", "优化建议"],
                    "video_path": "${output_dir}/video.mp4",
                    "frames_path": "${output_dir}/frames",
                }
            },
            "data_analysis": {
                "id": "data_analysis",
                "name": "数据表现",
                "description": "分析播放量、点赞、评论等数据",
                "type": "text_analysis",
                "enabled": True,
                "config": {
                    "input_prompt_template": "播放：{play}  点赞：{like}  评论：{comment}  收藏：{collect}  分享：{share}  时长：{duration}s\n\n分析：\n{output_keywords}",
                    "output_keywords": ["数据评级", "互动率", "完播预估", "受众匹配", "优化方向"]
                }
            },
            "script_analysis": {
                "id": "script_analysis",
                "name": "逐镜脚本",
                "description": "生成视频逐镜脚本",
                "type": "video_analysis",
                "enabled": True,
                "config": {
                    "input_prompt_template": "你是专业的{module_name}分析师。根据以下视频内容和关键帧信息，生成逐镜脚本：\n{output_keywords}",
                    "output_keywords": ["逐镜脚本", "脚本节奏结构", "仿写脚本"],
                    "video_path": "${output_dir}/video.mp4",
                    "frames_path": "${output_dir}/frames",
                }
            },
            "storyboard_analysis": {
                "id": "storyboard_analysis",
                "name": "分镜表",
                "description": "生成视频分镜表",
                "type": "video_analysis",
                "enabled": True,
                "config": {
                    "input_prompt_template": "你是专业的{module_name}分析师。根据以下视频内容和关键帧信息，生成分镜表：\n{output_keywords}",
                    "output_keywords": ["分镜表"],
                    "video_path": "${output_dir}/video.mp4",
                    "frames_path": "${output_dir}/frames",
                }
            },
            "photo_analysis": {
                "id": "photo_analysis",
                "name": "摄影运镜",
                "description": "分析视频摄影运镜技巧",
                "type": "image_analysis",
                "enabled": True,
                "config": {
                    "input_prompt_template": "你是专业的{module_name}分析师。分析以下帧画面的摄影运镜技巧：\n{output_keywords}",
                    "output_keywords": ["拍摄方案", "镜头类型", "构图方法", "光线运用"],
                    "frames_path": "${output_dir}/frames",
                }
            },
            "color_analysis": {
                "id": "color_analysis",
                "name": "色彩风格",
                "description": "分析视频色彩风格",
                "type": "image_analysis",
                "enabled": True,
                "config": {
                    "input_prompt_template": "你是专业的{module_name}分析师。分析以下帧画面的色彩风格：\n{output_keywords}",
                    "output_keywords": ["整体色彩风格", "画面色彩特征", "达芬奇仿色参数", "LUT 风格参考"],
                    "frames_path": "${output_dir}/frames",
                }
            },
            "bgm_analysis": {
                "id": "bgm_analysis",
                "name": "BGM推荐",
                "description": "推荐适合视频的背景音乐",
                "type": "text_analysis",
                "enabled": True,
                "config": {
                    "input_prompt_template": "你是专业的{module_name}分析师。根据以下视频内容，推荐适合的背景音乐：\n{output_keywords}",
                    "output_keywords": ["匹配风格", "BGM 列表", "版权说明"]
                }
            },
            "topic_analysis": {
                "id": "topic_analysis",
                "name": "选题分析",
                "description": "分析视频选题并推荐相关选题",
                "type": "text_analysis",
                "enabled": True,
                "config": {
                    "input_prompt_template": "你是专业的{module_name}分析师。根据以下视频内容，分析选题并推荐相关高流量选题：\n{output_keywords}",
                    "output_keywords": ["高流量选题"]
                }
            },
            "title_analysis": {
                "id": "title_analysis",
                "name": "标题生成",
                "description": "生成视频爆款标题",
                "type": "text_analysis",
                "enabled": True,
                "config": {
                    "input_prompt_template": "你是专业的{module_name}分析师。根据以下视频内容，生成爆款标题：\n{output_keywords}",
                    "output_keywords": ["爆款标题"]
                }
            },
            "cover_analysis": {
                "id": "cover_analysis",
                "name": "封面文案",
                "description": "生成视频封面文案",
                "type": "text_analysis",
                "enabled": True,
                "config": {
                    "input_prompt_template": "你是专业的{module_name}分析师。根据以下视频内容，生成封面文案：\n{output_keywords}",
                    "output_keywords": ["封面文案"]
                }
            },
            "publish_time_analysis": {
                "id": "publish_time_analysis",
                "name": "发布时间",
                "description": "分析最佳发布时间",
                "type": "text_analysis",
                "enabled": True,
                "config": {
                    "input_prompt_template": "你是专业的{module_name}分析师。根据以下视频内容，分析最佳发布时间：\n{output_keywords}",
                    "output_keywords": ["最佳发布时间"]
                }
            },
        }
    
    def get_module_config(self, module_id):
        module = self.analysis_modules.get(module_id, {})
        return module.get('config', {})
    
    def get_all_modules(self):
        return self.analysis_modules
    
    def get_analysis_module(self, module_id):
        return self.analysis_modules.get(module_id, {})
    
    def update_analysis_module(self, module_id, module_config):
        self.analysis_modules[module_id] = module_config
        self._save_analysis_modules()
    
    def add_analysis_module(self, module_id, module_config):
        self.analysis_modules[module_id] = module_config
        self._save_analysis_modules()
    
    def remove_analysis_module(self, module_id):
        if module_id in self.analysis_modules:
            del self.analysis_modules[module_id]
            self._save_analysis_modules()
    
    def _save_analysis_modules(self):
        try:
            with open(self.analysis_modules_file, 'w', encoding='utf-8') as f:
                json.dump({'modules': self.analysis_modules}, f, ensure_ascii=False, indent=2)
            print(f"分析模块配置已保存到 {self.analysis_modules_file}")
        except Exception as e:
            print(f"保存分析模块配置失败：{e}")
    
    def get_system_settings(self):
        return self.config.get('system_settings', {})


config_manager = ConfigManager()
