"""
OpenClaw 视频分析客户端

使用方法:
    from api.client import VideoAnalysisClient
    
    client = VideoAnalysisClient()
    
    # 下载视频
    video_path = client.download_video("https://example.com/video")
    
    # 视频分析
    result = client.analyze_video("video.mp4", "分析这个视频的内容")
    
    # 图片分析
    result = client.analyze_image("image.jpg", "描述这张图片")
    
    # 文本分析
    result = client.analyze_text("要分析的文本", "总结这段文本")
    
    # 完整分析
    result = client.full_analysis("video.mp4")
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, List, Any, Union

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.video_downloader.downloader import download_video, get_video_data
from modules.video_processor.processor import get_video_info, extract_frames, asr_text, extract_audio
from modules.analysis.analyzer import LargeLanguageModel
from modules.analysis.modules.manager import module_manager
from config_manager import config_manager
from dotenv import load_dotenv

load_dotenv()


class VideoAnalysisClient:
    def __init__(self, api_key: str = None, base_url: str = None, model_name: str = None):
        self.llm = None
        self._init_llm(api_key, base_url, model_name)
    
    def _init_llm(self, api_key=None, base_url=None, model_name=None):
        api_key = api_key or os.getenv("API_KEY")
        base_url = base_url or os.getenv("BASE_URL")
        model_name = model_name or os.getenv("MODEL_NAME")
        
        if api_key and api_key != "your_api_key_here":
            self.llm = LargeLanguageModel(
                api_key=api_key,
                base_url=base_url,
                model_name=model_name
            )
            module_manager.set_llm(self.llm)
            return True
        return False
    
    def download_video(self, url: str, output_dir: str = None, max_comments: int = 100) -> Dict[str, Any]:
        return download_video(url, output_dir=output_dir, max_comments=max_comments)
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        return get_video_info(video_path)
    
    def extract_frames(self, video_path: str, output_dir: str = None, interval: int = 2, max_frames: int = 15) -> List[str]:
        return extract_frames(video_path, interval=interval, max_frames=max_frames, output_dir=output_dir)
    
    def extract_audio(self, video_path: str, output_path: str = None) -> str:
        if output_path is None:
            video_name = Path(video_path).stem
            output_path = f"output/{video_name}_audio.wav"
        return extract_audio(video_path, output_path)
    
    def transcribe(self, video_path: str) -> str:
        return asr_text(video_path)
    
    def analyze_video(self, video_path: str, prompt: str, output_dir: str = None) -> str:
        if not self.llm:
            raise RuntimeError("大语言模型未初始化，请配置 API 密钥")
        result, _ = self.llm.analyze_video_directly(video_path, prompt, save_result=True, output_dir=output_dir)
        return result
    
    def analyze_image(self, image_path: str, prompt: str, output_dir: str = None) -> str:
        if not self.llm:
            raise RuntimeError("大语言模型未初始化，请配置 API 密钥")
        result, _ = self.llm.analyze_image(image_path, prompt, save_result=True, output_dir=output_dir)
        return result
    
    def analyze_text(self, text: str, prompt: str, output_dir: str = None) -> str:
        if not self.llm:
            raise RuntimeError("大语言模型未初始化，请配置 API 密钥")
        result, _ = self.llm.analyze_text(text, prompt, save_result=True, output_dir=output_dir)
        return result
    
    def analyze_frame(self, frame_path: str, module_id: str = "content_analysis") -> str:
        module = module_manager.get_module(module_id)
        if not module:
            raise ValueError(f"模块 {module_id} 不存在")
        if not module.is_enabled():
            raise ValueError(f"模块 {module_id} 未启用")
        return module.analyze(frames=[frame_path])
    
    def analyze_all_modules(self, video_path: str = None, frames: List[str] = None, text: str = None, stats: Dict = None, **kwargs) -> Dict[str, str]:
        if not self.llm:
            raise RuntimeError("大语言模型未初始化，请配置 API 密钥")
        
        enabled_modules = module_manager.get_enabled_modules()
        results = {}
        
        for module in enabled_modules:
            try:
                result = module.analyze(
                    video_path=video_path,
                    frames=frames,
                    text=text,
                    stats=stats or {},
                    **kwargs
                )
                results[module.module_id] = result
            except Exception as e:
                results[module.module_id] = f"分析失败: {str(e)}"
        
        return results
    
    def get_enabled_modules(self) -> List[str]:
        modules = module_manager.get_enabled_modules()
        return [m.module_id for m in modules]
    
    def get_all_modules(self) -> Dict[str, Dict]:
        modules = module_manager.get_all_modules()
        return {
            k: {
                "name": v.get_name(),
                "enabled": v.is_enabled(),
                "type": v.config.get("type", "text_analysis")
            } 
            for k, v in modules.items()
        }
    
    def full_analysis(self, video_path: str, output_dir: str = None, interval: int = 2, max_frames: int = 15) -> Dict[str, Any]:
        info = self.get_video_info(video_path)
        frames = self.extract_frames(video_path, output_dir, interval, max_frames)
        text = self.transcribe(video_path)
        results = self.analyze_all_modules(video_path, frames, text, info.get("stats", {}))
        
        return {
            "info": info,
            "frames": frames,
            "text": text,
            "analysis_results": results
        }
    
    def analyze_script(self, video_path: str, prompt: str = None) -> str:
        if not prompt:
            prompt = "分析这个视频的脚本结构，包括开场白，内容展开、结尾等部分"
        return self.analyze_video(video_path, prompt)
    
    def analyze_photo(self, image_path: str, prompt: str = None) -> str:
        if not prompt:
            prompt = "描述这张图片的内容、构图和风格特点"
        return self.analyze_image(image_path, prompt)
    
    def analyze_content(self, video_path: str, prompt: str = None) -> str:
        if not prompt:
            prompt = "详细分析这个视频的内容主题、目标和受众"
        return self.analyze_video(video_path, prompt)


__all__ = ["VideoAnalysisClient"]
