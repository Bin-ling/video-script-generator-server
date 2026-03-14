import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from llm import chat, get_model_config, get_video_fps
from modules.analysis.analyzer import LargeLanguageModel
from config_manager import config_manager

llm_instance = None

def get_llm_instance(model_type: str = "default") -> Optional[LargeLanguageModel]:
    global llm_instance
    
    if llm_instance is not None:
        return llm_instance
    
    model_config = config_manager.get_model_config(model_type)
    
    if not model_config:
        model_config = get_model_config().get('models', {}).get(model_type, {})
    
    api_key = model_config.get('api_key') or os.getenv('API_KEY')
    base_url = model_config.get('base_url') or os.getenv('BASE_URL')
    model_name = model_config.get('model_name') or os.getenv('MODEL_NAME')
    video_fps = model_config.get('video_fps', get_video_fps())
    
    if not api_key or not base_url or not model_name:
        print(f"[LLM服务] 缺少必要的配置: api_key={bool(api_key)}, base_url={bool(base_url)}, model_name={bool(model_name)}")
        return None
    
    try:
        llm_instance = LargeLanguageModel(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            video_fps=video_fps
        )
        print(f"[LLM服务] 初始化成功: model={model_name}, fps={video_fps}")
        return llm_instance
    except Exception as e:
        print(f"[LLM服务] 初始化失败: {e}")
        return None

def execute_analysis(prompt: str) -> str:
    try:
        result = chat(prompt)
        return result
    except Exception as e:
        print(f"[LLM分析] 执行出错: {e}")
        return f"分析失败: {str(e)}"

def analyze_video(video_path: str, prompt: str, fps: Optional[float] = None) -> Dict[str, Any]:
    llm = get_llm_instance("video_analysis")
    if not llm:
        return {"success": False, "error": "LLM实例初始化失败"}
    
    try:
        result, _ = llm.analyze_video_directly(video_path, prompt, fps=fps)
        return {"success": True, "result": result}
    except Exception as e:
        print(f"[视频分析] 执行出错: {e}")
        return {"success": False, "error": str(e)}

def analyze_image(image_path: str, prompt: str) -> Dict[str, Any]:
    llm = get_llm_instance("image_analysis")
    if not llm:
        return {"success": False, "error": "LLM实例初始化失败"}
    
    try:
        result, _ = llm.analyze_image(image_path, prompt)
        return {"success": True, "result": result}
    except Exception as e:
        print(f"[图片分析] 执行出错: {e}")
        return {"success": False, "error": str(e)}

def analyze_text(text: str, prompt: str) -> Dict[str, Any]:
    llm = get_llm_instance("text_analysis")
    if not llm:
        return {"success": False, "error": "LLM实例初始化失败"}
    
    try:
        result, _ = llm.analyze_text(text, prompt)
        return {"success": True, "result": result}
    except Exception as e:
        print(f"[文本分析] 执行出错: {e}")
        return {"success": False, "error": str(e)}

def get_upload_settings() -> Dict[str, Any]:
    settings = config_manager.get_upload_settings()
    if not settings:
        config = get_model_config()
        settings = config.get('upload_settings', {})
    return settings

def get_fps_range() -> Dict[str, float]:
    settings = get_upload_settings()
    fps_range = settings.get('fps_range', {})
    return {
        "min": fps_range.get('min', 0.2),
        "max": fps_range.get('max', 5.0),
        "default": fps_range.get('default', 1.0)
    }
