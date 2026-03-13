import os
import sys
import json
import argparse
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.video_downloader.downloader import download_video, get_video_data
from modules.video_processor.processor import get_video_info, extract_frames, asr_text, extract_audio
from modules.analysis.analyzer import LargeLanguageModel
from modules.analysis.modules.manager import module_manager
from config_manager import config_manager
from dotenv import load_dotenv

load_dotenv()


class VideoAnalysisAPI:
    def __init__(self):
        self.llm = None
        self._init_llm()
    
    def _init_llm(self):
        api_key = os.getenv("API_KEY")
        base_url = os.getenv("BASE_URL")
        model_name = os.getenv("MODEL_NAME")
        
        if api_key and api_key != "your_api_key_here":
            self.llm = LargeLanguageModel(
                api_key=api_key,
                base_url=base_url,
                model_name=model_name
            )
            module_manager.set_llm(self.llm)
            print("大语言模型初始化成功")
        else:
            print("警告: API密钥未配置")
    
    def download_video(self, url, output_dir=None, max_comments=100):
        result = download_video(url, output_dir=output_dir, max_comments=max_comments)
        return result
    
    def get_video_info(self, video_path):
        return get_video_info(video_path)
    
    def extract_frames(self, video_path, output_dir=None, interval=2, max_frames=15):
        return extract_frames(video_path, interval=interval, max_frames=max_frames, output_dir=output_dir)
    
    def extract_audio(self, video_path, output_path=None):
        if output_path is None:
            video_name = Path(video_path).stem
            output_path = f"output/{video_name}_audio.wav"
        return extract_audio(video_path, output_path)
    
    def transcribe_audio(self, video_path):
        return asr_text(video_path)
    
    def analyze_video(self, video_path, prompt, output_dir=None):
        if not self.llm:
            return {"error": "大语言模型未初始化"}
        result, _ = self.llm.analyze_video_directly(video_path, prompt, save_result=True, output_dir=output_dir)
        return result
    
    def analyze_image(self, image_path, prompt, output_dir=None):
        if not self.llm:
            return {"error": "大语言模型未初始化"}
        result, _ = self.llm.analyze_image(image_path, prompt, save_result=True, output_dir=output_dir)
        return result
    
    def analyze_text(self, text, prompt, output_dir=None):
        if not self.llm:
            return {"error": "大语言模型未初始化"}
        result, _ = self.llm.analyze_text(text, prompt, save_result=True, output_dir=output_dir)
        return result
    
    def analyze_frame(self, frame_path, module_id="content_analysis"):
        module = module_manager.get_module(module_id)
        if not module:
            return {"error": f"模块 {module_id} 不存在"}
        if not module.is_enabled():
            return {"error": f"模块 {module_id} 未启用"}
        result = module.analyze(frames=[frame_path])
        return result
    
    def analyze_all_modules(self, video_path, frames, text, stats=None, **kwargs):
        if not self.llm:
            return {"error": "大语言模型未初始化"}
        
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
    
    def get_enabled_modules(self):
        modules = module_manager.get_enabled_modules()
        return [m.module_id for m in modules]
    
    def get_all_modules(self):
        modules = module_manager.get_all_modules()
        return {k: {"name": v.get_name(), "enabled": v.is_enabled(), "type": v.config.get("type", "text_analysis")} for k, v in modules.items()}


def main():
    parser = argparse.ArgumentParser(description="视频分析 API 命令行工具")
    parser.add_argument("action", choices=["download", "info", "frames", "audio", "transcribe", "analyze-video", "analyze-image", "analyze-text", "modules", "full-analysis"], help="要执行的操作")
    parser.add_argument("--url", type=str, help="视频URL (用于下载)")
    parser.add_argument("--path", type=str, help="文件路径 (视频/图片/音频)")
    parser.add_argument("--prompt", type=str, help="分析提示词")
    parser.add_argument("--output", type=str, help="输出目录")
    parser.add_argument("--interval", type=int, default=2, help="关键帧提取间隔 (秒)")
    parser.add_argument("--max-frames", type=int, default=15, help="最大关键帧数量")
    parser.add_argument("--module", type=str, default="content_analysis", help="分析模块ID")
    
    args = parser.parse_args()
    
    api = VideoAnalysisAPI()
    
    if args.action == "download":
        if not args.url:
            print("错误: 下载操作需要 --url 参数")
            return
        result = api.download_video(args.url, args.output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.action == "info":
        if not args.path:
            print("错误: 获取视频信息需要 --path 参数")
            return
        result = api.get_video_info(args.path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.action == "frames":
        if not args.path:
            print("错误: 提取关键帧需要 --path 参数")
            return
        result = api.extract_frames(args.path, args.output, args.interval, args.max_frames)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.action == "audio":
        if not args.path:
            print("错误: 提取音频需要 --path 参数")
            return
        result = api.extract_audio(args.path, args.output)
        print(json.dumps({"output_path": result}, ensure_ascii=False, indent=2))
    
    elif args.action == "transcribe":
        if not args.path:
            print("错误: 转录音频需要 --path 参数")
            return
        result = api.transcribe_audio(args.path)
        print(json.dumps({"text": result}, ensure_ascii=False, indent=2))
    
    elif args.action == "analyze-video":
        if not args.path or not args.prompt:
            print("错误: 分析视频需要 --path 和 --prompt 参数")
            return
        result = api.analyze_video(args.path, args.prompt, args.output)
        print(json.dumps({"result": result}, ensure_ascii=False, indent=2))
    
    elif args.action == "analyze-image":
        if not args.path or not args.prompt:
            print("错误: 分析图片需要 --path 和 --prompt 参数")
            return
        result = api.analyze_image(args.path, args.prompt, args.output)
        print(json.dumps({"result": result}, ensure_ascii=False, indent=2))
    
    elif args.action == "analyze-text":
        if not args.path or not args.prompt:
            print("错误: 分析文本需要 --path(文本内容) 和 --prompt 参数")
            return
        result = api.analyze_text(args.path, args.prompt, args.output)
        print(json.dumps({"result": result}, ensure_ascii=False, indent=2))
    
    elif args.action == "modules":
        modules = api.get_all_modules()
        print(json.dumps(modules, ensure_ascii=False, indent=2))
    
    elif args.action == "full-analysis":
        if not args.path:
            print("错误: 完整分析需要 --path 参数(视频路径)")
            return
        
        print("1. 提取视频信息...")
        info = api.get_video_info(args.path)
        
        print("2. 提取关键帧...")
        frames = api.extract_frames(args.path, args.output, args.interval, args.max_frames)
        
        print("3. 转录音频...")
        text = api.transcribe_audio(args.path)
        
        print("4. 执行所有分析模块...")
        results = api.analyze_all_modules(args.path, frames, text, info.get("stats", {}))
        
        full_result = {
            "info": info,
            "frames": frames,
            "text": text,
            "analysis_results": results
        }
        print(json.dumps(full_result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
