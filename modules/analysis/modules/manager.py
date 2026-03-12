"""
分析模块管理器
"""

from config_manager import config_manager
from .video_analysis import VideoAnalysisModule
from .image_analysis import ImageAnalysisModule
from .text_analysis import TextAnalysisModule

class ModuleManager:
    """分析模块管理器"""
    
    def __init__(self):
        self.modules = {}
        self.llm = None
        self._load_modules()
    
    def _load_modules(self):
        """加载所有分析模块"""
        modules_config = config_manager.get_all_modules()
        for module_id, module_info in modules_config.items():
            module_type = module_info.get('type', 'text_analysis')
            if module_type == 'video_analysis':
                self.modules[module_id] = VideoAnalysisModule(module_id)
            elif module_type == 'image_analysis':
                self.modules[module_id] = ImageAnalysisModule(module_id)
            elif module_type == 'text_analysis':
                self.modules[module_id] = TextAnalysisModule(module_id)
    
    def set_llm(self, llm):
        """设置大语言模型
        
        Args:
            llm: 大语言模型实例
        """
        self.llm = llm
        # 为所有需要大语言模型的模块设置模型
        for module in self.modules.values():
            if hasattr(module, 'set_llm'):
                module.set_llm(llm)
    
    def get_module(self, module_id):
        """获取模块实例
        
        Args:
            module_id: 模块ID
            
        Returns:
            模块实例
        """
        return self.modules.get(module_id)
    
    def get_all_modules(self):
        """获取所有模块
        
        Returns:
            模块字典
        """
        return self.modules
    
    def get_enabled_modules(self):
        """获取所有启用的模块
        
        Returns:
            启用的模块列表
        """
        return [module for module in self.modules.values() if module.is_enabled()]
    
    def analyze(self, module_id, **kwargs):
        """执行模块分析
        
        Args:
            module_id: 模块ID
            **kwargs: 分析参数
            
        Returns:
            分析结果
        """
        module = self.get_module(module_id)
        if module:
            return module.analyze(**kwargs)
        return "模块不存在"
    
    def analyze_all(self, **kwargs):
        """执行所有启用模块的分析
        
        Args:
            **kwargs: 分析参数
            
        Returns:
            分析结果字典
        """
        results = {}
        for module in self.get_enabled_modules():
            results[module.module_id] = module.analyze(**kwargs)
        return results
    
    def enable_module(self, module_id):
        """启用模块
        
        Args:
            module_id: 模块ID
        """
        module = self.get_module(module_id)
        if module:
            module.enable()
    
    def disable_module(self, module_id):
        """禁用模块
        
        Args:
            module_id: 模块ID
        """
        module = self.get_module(module_id)
        if module:
            module.disable()
    
    def toggle_module(self, module_id):
        """切换模块启用状态
        
        Args:
            module_id: 模块ID
            
        Returns:
            bool: 切换后的状态
        """
        module = self.get_module(module_id)
        if module:
            if module.is_enabled():
                module.disable()
            else:
                module.enable()
            return module.is_enabled()
        return False
    
    def update_module_config(self, module_id, config):
        """更新模块配置
        
        Args:
            module_id: 模块ID
            config: 新的配置字典
        """
        module = self.get_module(module_id)
        if module:
            module.update_config(config)
    
    def add_module(self, module_id, module_config):
        """添加新模块
        
        Args:
            module_id: 模块ID
            module_config: 模块配置字典
        """
        # 添加到配置
        config_manager.add_analysis_module(module_id, module_config)
        # 重新加载模块
        self._load_modules()
        # 设置大语言模型
        if self.llm:
            module = self.get_module(module_id)
            if hasattr(module, 'set_llm'):
                module.set_llm(self.llm)
    
    def remove_module(self, module_id):
        """移除模块
        
        Args:
            module_id: 模块ID
        """
        # 从配置中移除
        config_manager.remove_analysis_module(module_id)
        # 从模块字典中移除
        if module_id in self.modules:
            del self.modules[module_id]


# 全局模块管理器实例
module_manager = ModuleManager()
