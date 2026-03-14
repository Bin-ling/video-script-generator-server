#!/usr/bin/env python3
"""
配置管理器 - 管理分析模块配置
"""

import json
import os
from dotenv import load_dotenv

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, analysis_modules_file='configs/analysis_modules.json'):
        load_dotenv()
        self.analysis_modules_file = analysis_modules_file
        self.config = self._get_default_config()
        self.analysis_modules = self._load_analysis_modules()
        self.full_config = self._load_full_config()
    
    def _load_full_config(self):
        """加载完整配置文件"""
        if os.path.exists(self.analysis_modules_file):
            try:
                with open(self.analysis_modules_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载完整配置失败：{e}")
                return {}
        return {}
    
    def _load_analysis_modules(self):
        """加载分析模块配置"""
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
        """获取默认配置"""
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
        """获取默认分析模块配置"""
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
                    "frames_path": "${output_dir}/frames"
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
            }
        }
    
    def get_module_config(self, module_id):
        """获取模块配置
        
        Args:
            module_id: 模块ID
            
        Returns:
            模块配置字典
        """
        module = self.analysis_modules.get(module_id, {})
        return module.get('config', {})
    
    def get_all_modules(self):
        """获取所有模块配置
        
        Returns:
            所有模块配置字典
        """
        return self.analysis_modules
    
    def get_analysis_module(self, module_id):
        """获取分析模块配置
        
        Args:
            module_id: 模块ID
            
        Returns:
            模块配置字典
        """
        return self.analysis_modules.get(module_id, {})
    
    def add_module(self, module_id, module_config):
        """添加新模块
        
        Args:
            module_id: 模块ID
            module_config: 模块配置字典
            
        Returns:
            bool: 是否添加成功
        """
        if module_id in self.analysis_modules:
            print(f"模块 {module_id} 已存在")
            return False
        
        required_fields = ['id', 'name', 'type', 'enabled', 'config']
        for field in required_fields:
            if field not in module_config:
                print(f"模块配置缺少必需字段: {field}")
                return False
        
        module_config['id'] = module_id
        self.analysis_modules[module_id] = module_config
        self._save_analysis_modules()
        print(f"模块 {module_id} 添加成功")
        return True
    
    def remove_module(self, module_id):
        """移除模块
        
        Args:
            module_id: 模块ID
            
        Returns:
            bool: 是否移除成功
        """
        if module_id not in self.analysis_modules:
            print(f"模块 {module_id} 不存在")
            return False
        
        del self.analysis_modules[module_id]
        self._save_analysis_modules()
        print(f"模块 {module_id} 移除成功")
        return True
    
    def update_module(self, module_id, module_config):
        """更新模块配置
        
        Args:
            module_id: 模块ID
            module_config: 模块配置字典
            
        Returns:
            bool: 是否更新成功
        """
        if module_id not in self.analysis_modules:
            print(f"模块 {module_id} 不存在")
            return False
        
        self.analysis_modules[module_id].update(module_config)
        self._save_analysis_modules()
        print(f"模块 {module_id} 更新成功")
        return True
    
    def update_analysis_module(self, module_id, module_config):
        """更新分析模块配置（兼容旧方法）
        
        Args:
            module_id: 模块ID
            module_config: 模块配置字典
        """
        self.analysis_modules[module_id] = module_config
        self._save_analysis_modules()
    
    def add_analysis_module(self, module_id, module_config):
        """添加分析模块（兼容旧方法）
        
        Args:
            module_id: 模块ID
            module_config: 模块配置字典
        """
        self.analysis_modules[module_id] = module_config
        self._save_analysis_modules()
    
    def remove_analysis_module(self, module_id):
        """移除分析模块（兼容旧方法）
        
        Args:
            module_id: 模块ID
        """
        if module_id in self.analysis_modules:
            del self.analysis_modules[module_id]
            self._save_analysis_modules()
    
    def get_analysis_modules_settings(self):
        """获取分析模块类型设置
        
        Returns:
            分析模块类型设置字典
        """
        return self.full_config.get('analysis_modules', {})
    
    def get_multimodal_settings(self):
        """获取多模态设置
        
        Returns:
            多模态设置字典
        """
        return self.full_config.get('multimodal_settings', {
            'enabled': True,
            'parallel_processing': True,
            'max_concurrent_tasks': 4,
            'timeout': 300,
            'retry_attempts': 3,
            'retry_delay': 5,
            'cache_enabled': True,
            'cache_ttl': 3600
        })
    
    def get_module_type_config(self, module_type):
        """获取特定类型模块的配置
        
        Args:
            module_type: 模块类型 (video_analysis, image_analysis, text_analysis)
            
        Returns:
            该类型模块的配置字典
        """
        analysis_modules = self.get_analysis_modules_settings()
        return analysis_modules.get(module_type, {})
    
    def is_module_enabled(self, module_id):
        """检查模块是否启用
        
        Args:
            module_id: 模块ID
            
        Returns:
            bool: 模块是否启用
        """
        module = self.analysis_modules.get(module_id, {})
        return module.get('enabled', False)
    
    def enable_module(self, module_id):
        """启用模块
        
        Args:
            module_id: 模块ID
            
        Returns:
            bool: 是否启用成功
        """
        if module_id not in self.analysis_modules:
            print(f"模块 {module_id} 不存在")
            return False
        
        self.analysis_modules[module_id]['enabled'] = True
        self._save_analysis_modules()
        print(f"模块 {module_id} 已启用")
        return True
    
    def disable_module(self, module_id):
        """禁用模块
        
        Args:
            module_id: 模块ID
            
        Returns:
            bool: 是否禁用成功
        """
        if module_id not in self.analysis_modules:
            print(f"模块 {module_id} 不存在")
            return False
        
        self.analysis_modules[module_id]['enabled'] = False
        self._save_analysis_modules()
        print(f"模块 {module_id} 已禁用")
        return True
    
    def get_modules_by_type(self, module_type):
        """按类型获取模块
        
        Args:
            module_type: 模块类型
            
        Returns:
            该类型的模块列表
        """
        return {
            module_id: module 
            for module_id, module in self.analysis_modules.items()
            if module.get('type') == module_type
        }
    
    def get_enabled_modules(self):
        """获取所有启用的模块
        
        Returns:
            启用的模块ID列表
        """
        return [
            module_id for module_id, module in self.analysis_modules.items()
            if module.get('enabled', False)
        ]
    
    def _save_analysis_modules(self):
        """保存分析模块配置到文件"""
        try:
            self.full_config['modules'] = self.analysis_modules
            with open(self.analysis_modules_file, 'w', encoding='utf-8') as f:
                json.dump(self.full_config, f, ensure_ascii=False, indent=2)
            print(f"分析模块配置已保存到 {self.analysis_modules_file}")
        except Exception as e:
            print(f"保存分析模块配置失败：{e}")
    
    def get_system_settings(self):
        """获取系统设置
        
        Returns:
            系统设置字典
        """
        return self.config.get('system_settings', {})
    
    def reload_config(self):
        """重新加载配置"""
        self.analysis_modules = self._load_analysis_modules()
        self.full_config = self._load_full_config()
        print("配置已重新加载")
    
    def get_model_config(self, model_type: str = "default") -> dict:
        """获取模型配置
        
        Args:
            model_type: 模型类型，如 default, video_analysis, image_analysis 等
            
        Returns:
            模型配置字典
        """
        model_config_file = 'model_config.json'
        if os.path.exists(model_config_file):
            try:
                with open(model_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    models = config.get('models', {})
                    return models.get(model_type, {})
            except Exception as e:
                print(f"加载模型配置失败：{e}")
                return {}
        return {}
    
    def get_upload_settings(self) -> dict:
        """获取上传设置
        
        Returns:
            上传设置字典
        """
        model_config_file = 'model_config.json'
        if os.path.exists(model_config_file):
            try:
                with open(model_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('upload_settings', {})
            except Exception as e:
                print(f"加载上传设置失败：{e}")
                return {}
        return {}


config_manager = ConfigManager()
