from flask import request, jsonify
import os
import json

def get_model_config():
    return {}

def save_model_config(request):
    try:
        data = request.get_json()
        
        # 支持两种数据格式
        if 'models' in data:
            models = data['models']
            default_config = models.get('default', {})
            api_key = default_config.get('api_key')
            base_url = default_config.get('base_url')
            model_name = default_config.get('model_name')
        else:
            api_key = data.get('api_key')
            base_url = data.get('base_url')
            model_name = data.get('model_name')
        
        if api_key and base_url and model_name:
            # 保存到 .env 文件
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(f"API_KEY={api_key}\n")
                f.write(f"BASE_URL={base_url}\n")
                f.write(f"MODEL_NAME={model_name}\n")
            
            # 如果前端发送了完整的 models 配置，保存到 model_config.json
            if 'models' in data:
                with open('model_config.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Missing required fields'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def get_all_configs():
    from dotenv import load_dotenv
    load_dotenv()
    
    # 尝试从 model_config.json 读取
    models = {}
    if os.path.exists('model_config.json'):
        try:
            with open('model_config.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'models' in data:
                    models = data['models']
        except Exception:
            pass
    
    # 从 .env 填充默认配置
    api_key = os.getenv('API_KEY', '')
    base_url = os.getenv('BASE_URL', '')
    model_name = os.getenv('MODEL_NAME', '')
    
    # 如果 models 为空，填充默认配置
    if not models:
        models = {
            'default': {
                'name': '默认模型',
                'api_key': api_key,
                'base_url': base_url,
                'model_name': model_name,
                'temperature': 0.7,
                'max_tokens': 2000
            }
        }
    
    return {'models': models}

def get_module_config(module_name):
    from config_manager import config_manager
    return config_manager.get_analysis_module(module_name)
