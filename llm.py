import os
import requests
from dotenv import load_dotenv

os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['ALL_PROXY'] = ''

load_dotenv()

api_key = os.getenv('API_KEY')
base_url = os.getenv('BASE_URL')
model_name = os.getenv('MODEL_NAME')

def chat(prompt):
    try:
        url = f"{base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 4096
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f'模型错误：{str(e)}'

def get_model_config():
    """获取模型配置"""
    import json
    config_file = 'model_config.json'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载模型配置失败：{e}")
    return {}

def get_video_fps():
    """获取视频fps配置"""
    config = get_model_config()
    upload_settings = config.get('upload_settings', {})
    fps_range = upload_settings.get('fps_range', {})
    return fps_range.get('default', 1.0)
