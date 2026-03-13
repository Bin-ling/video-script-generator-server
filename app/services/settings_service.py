from flask import request, jsonify
import os
import json

def get_model_config():
    return {}

def save_model_config(request):
    try:
        data = request.get_json()
        
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
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(f"API_KEY={api_key}\n")
                f.write(f"BASE_URL={base_url}\n")
                f.write(f"MODEL_NAME={model_name}\n")
            
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
    
    models = {}
    if os.path.exists('model_config.json'):
        try:
            with open('model_config.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'models' in data:
                    models = data['models']
        except Exception:
            pass
    
    api_key = os.getenv('API_KEY', '')
    base_url = os.getenv('BASE_URL', '')
    model_name = os.getenv('MODEL_NAME', '')
    
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
    """获取模块配置"""
    from dotenv import load_dotenv
    load_dotenv()
    
    models_data = get_all_configs()
    models = models_data.get('models', {})
    
    if module_name in models:
        return models[module_name]
    
    return models.get('default', {
        'api_key': os.getenv('API_KEY', ''),
        'base_url': os.getenv('BASE_URL', ''),
        'model_name': os.getenv('MODEL_NAME', '')
    })
