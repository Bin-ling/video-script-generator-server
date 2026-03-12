"""
视频分析模块
"""

from .base import AnalysisModule
from app.services.llm_service import execute_analysis
from modules.analysis.analyzer import LargeLanguageModel
import os

class VideoAnalysisModule(AnalysisModule):
    """视频分析模块"""
    
    def __init__(self, module_id):
        super().__init__(module_id)
        self.llm = None
    
    def set_llm(self, llm):
        """设置大模型
        
        Args:
            llm: 大模型实例
        """
        self.llm = llm
    
    def analyze(self, **kwargs):
        """执行视频分析
        
        Args:
            **kwargs: 分析参数
                - video_path: 视频路径
                - frames: 帧路径列表
                - text: 视频文本内容
                - output_dir: 输出目录
                - stats: 视频统计数据
                - analysis_result: 分析结果
            
        Returns:
            分析结果
        """
        if not self.is_enabled():
            return "模块已禁用"
        
        video_path = kwargs.get('video_path')
        frames = kwargs.get('frames', [])
        text = kwargs.get('text', '')
        output_dir = kwargs.get('output_dir')
        stats = kwargs.get('stats', {})
        analysis_result = kwargs.get('analysis_result')
        
        # 解析配置
        input_prompt_template = self.config.get('input_prompt_template', '')
        output_keywords = self.config.get('output_keywords', [])
        
        # 构建增强文本
        enhanced_text = text
        
        # 构建帧信息
        frame_info = "\n".join([f"帧 {i+1}: {path}" for i, path in enumerate(frames)])
        
        # 渲染提示词
        prompt = self.render_prompt(
            input_prompt_template,
            module_name=self.get_name(),
            output_keywords=output_keywords,
            text=enhanced_text,
            frame_count=len(frames),
            frame_info=frame_info,
            play=stats.get('play', 0),
            like=stats.get('like', 0),
            comment=stats.get('comment', 0),
            collect=stats.get('collect', 0),
            share=stats.get('share', 0),
            duration=kwargs.get('duration', 0),
            desc=kwargs.get('desc', ''),
            video_path=video_path,
            frames_path=frames,
            hashtag_names=kwargs.get('hashtag_names', []),
            comments=kwargs.get('comments', [])
        )
        
        # 执行分析
        if self.llm and video_path:
            # 分析视频
            try:
                # 使用配置中的提示词或默认提示词
                video_prompt = self.config.get('input_prompt_template', '详细分析这个视频，总结主要内容、关键场景和核心信息')
                # 分析视频
                result, _ = self.llm.analyze_video_directly(video_path, video_prompt, output_dir=output_dir)
            except Exception as e:
                # 如果视频分析失败，返回错误信息
                result = f"分析失败：{str(e)}"
        else:
            # 没有视频或模型，返回错误信息
            result = "没有提供视频或模型未初始化"
        
        return result
