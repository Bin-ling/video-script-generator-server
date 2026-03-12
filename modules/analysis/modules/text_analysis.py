"""
文本分析模块
"""

from .base import AnalysisModule
from modules.analysis.analyzer import LargeLanguageModel
import os

class TextAnalysisModule(AnalysisModule):
    """文本分析模块"""
    
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
        """执行文本分析
        
        Args:
            **kwargs: 分析参数
                - text: 视频文本内容
                - stats: 视频统计数据
                - output_dir: 输出目录
                - analysis_result: 分析结果
            
        Returns:
            分析结果
        """
        if not self.is_enabled():
            return "模块已禁用"
        
        text = kwargs.get('text', '')
        stats = kwargs.get('stats', {})
        output_dir = kwargs.get('output_dir')
        analysis_result = kwargs.get('analysis_result')
        
        # 解析配置
        input_prompt_template = self.config.get('input_prompt_template', '')
        output_keywords = self.config.get('output_keywords', [])
        
        # 构建增强文本
        enhanced_text = text
        if analysis_result:
            enhanced_text = f"视频内容分析：{analysis_result}\n\n原始文本：{text}"
        
        # 渲染提示词
        prompt = self.render_prompt(
            input_prompt_template,
            module_name=self.get_name(),
            output_keywords=output_keywords,
            text=enhanced_text,
            play=stats.get('play', 0),
            like=stats.get('like', 0),
            comment=stats.get('comment', 0),
            collect=stats.get('collect', 0),
            share=stats.get('share', 0),
            duration=kwargs.get('duration', 0),
            desc=kwargs.get('desc', ''),
            video_path=kwargs.get('video_path', ''),
            frames_path=kwargs.get('frames', []),
            hashtag_names=kwargs.get('hashtag_names', []),
            comments=kwargs.get('comments', [])
        )
        
        # 执行分析
        if self.llm and text:
            # 分析文本
            try:
                # 使用渲染后的提示词
                text_prompt = prompt
                # 分析文本，使用增强文本包含统计数据
                result, _ = self.llm.analyze_text(text=enhanced_text, prompt=text_prompt, output_dir=output_dir)
            except Exception as e:
                # 如果文本分析失败，返回错误信息
                result = f"分析失败：{str(e)}"
        else:
            # 没有文本或模型，返回错误信息
            result = "没有提供文本或模型未初始化"
        
        return result
