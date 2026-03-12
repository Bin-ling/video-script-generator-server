"""
图像分析模块
"""

from .base import AnalysisModule
from modules.analysis.analyzer import LargeLanguageModel
import os

class ImageAnalysisModule(AnalysisModule):
    """图像分析模块"""
    
    def __init__(self, module_id):
        super().__init__(module_id)
        self.llm = None
    
    def set_llm(self, llm):
        """设置大语言模型
        
        Args:
            llm: 大语言模型实例
        """
        self.llm = llm
    
    def analyze(self, **kwargs):
        """执行图像分析
        
        Args:
            **kwargs: 分析参数
                - frames: 帧路径列表
                - text: 视频文本内容
                - output_dir: 输出目录
                - analysis_result: 分析结果
            
        Returns:
            分析结果
        """
        if not self.is_enabled():
            return "模块已禁用"
        
        frames = kwargs.get('frames', [])
        text = kwargs.get('text', '')
        output_dir = kwargs.get('output_dir')
        analysis_result = kwargs.get('analysis_result')
        
        # 解析配置
        input_prompt_template = self.config.get('input_prompt_template', '')
        output_keywords = self.config.get('output_keywords', [])
        
        # 构建增强文本
        enhanced_text = text
        
        # 渲染提示词
        prompt = self.render_prompt(
            input_prompt_template,
            module_name=self.get_name(),
            output_keywords=output_keywords,
            text=enhanced_text,
            desc=kwargs.get('desc', ''),
            video_path=kwargs.get('video_path', ''),
            frames_path=frames,
            hashtag_names=kwargs.get('hashtag_names', []),
            comments=kwargs.get('comments', [])
        )
        
        # 执行分析
        if self.llm and frames:
            # 分析图片
            try:
                # 分析第一张图片
                frame_path = frames[0]
                # 使用配置中的提示词或默认提示词
                frame_prompt = self.config.get('input_prompt_template', '分析这张图片的内容和场景')
                # 分析图片
                result, _ = self.llm.analyze_image(frame_path, frame_prompt, output_dir=output_dir)
            except Exception as e:
                # 如果图片分析失败，返回错误信息
                result = f"分析失败：{str(e)}"
        else:
            # 没有图片或模型，返回错误信息
            result = "没有提供图片或模型未初始化"
        
        return result
