"""
分析模块基类
"""

from abc import ABC, abstractmethod
from config_manager import config_manager

class AnalysisModule(ABC):
    """分析模块基类"""
    
    def __init__(self, module_id):
        self.module_id = module_id
        self.module_config = config_manager.get_analysis_module(module_id)
        self.config = self.module_config.get('config', {})
    
    @abstractmethod
    def analyze(self, **kwargs):
        """执行分析
        
        Args:
            **kwargs: 分析参数
            
        Returns:
            分析结果
        """
        pass
    
    def get_config(self):
        """获取模块配置
        
        Returns:
            模块配置字典
        """
        return self.config
    
    def update_config(self, new_config):
        """更新模块配置
        
        Args:
            new_config: 新的配置字典
        """
        self.config.update(new_config)
        self.module_config['config'] = self.config
        config_manager.update_analysis_module(self.module_id, self.module_config)
    
    def is_enabled(self):
        """检查模块是否启用
        
        Returns:
            bool: 是否启用
        """
        return self.module_config.get('enabled', False)
    
    def enable(self):
        """启用模块"""
        self.module_config['enabled'] = True
        config_manager.update_analysis_module(self.module_id, self.module_config)
    
    def disable(self):
        """禁用模块"""
        self.module_config['enabled'] = False
        config_manager.update_analysis_module(self.module_id, self.module_config)
    
    def get_name(self):
        """获取模块名称
        
        Returns:
            str: 模块名称
        """
        return self.module_config.get('name', self.module_id)
    
    def get_description(self):
        """获取模块描述
        
        Returns:
            str: 模块描述
        """
        return self.module_config.get('description', '')
    
    def get_type(self):
        """获取模块类型
        
        Returns:
            str: 模块类型
        """
        return self.module_config.get('type', 'text_analysis')
    
    def render_prompt(self, template, **kwargs):
        """渲染提示词模板
        
        Args:
            template: 提示词模板
            **kwargs: 模板参数
            
        Returns:
            str: 渲染后的提示词
        """
        prompt = template
        for key, value in kwargs.items():
            if isinstance(value, list):
                value_str = '\n'.join([f"{i+1}. {item}" for i, item in enumerate(value)])
                prompt = prompt.replace(f"{{{key}}}", value_str)
            else:
                prompt = prompt.replace(f"{{{key}}}", str(value))
        return prompt
    
    def resolve_path(self, path_template, **kwargs):
        """解析路径模板
        
        Args:
            path_template: 路径模板
            **kwargs: 模板参数
            
        Returns:
            str: 解析后的路径
        """
        path = path_template
        for key, value in kwargs.items():
            path = path.replace(f"${{{key}}}", str(value))
        return path
