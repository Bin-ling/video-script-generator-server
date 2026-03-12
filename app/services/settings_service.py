from flask import request, jsonify

def get_model_config():
    return {}

def save_model_config(request):
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        base_url = data.get('base_url')
        model_name = data.get('model_name')
        
        if api_key and base_url and model_name:
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(f"API_KEY={api_key}\n")
                f.write(f"BASE_URL={base_url}\n")
                f.write(f"MODEL_NAME={model_name}\n")
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Missing required fields'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def get_all_configs():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    return {
        'api_key': os.getenv('API_KEY', ''),
        'base_url': os.getenv('BASE_URL', ''),
        'model_name': os.getenv('MODEL_NAME', '')
    }

def get_module_config(module_name):
    from config_manager import config_manager
    return config_manager.get_analysis_module(module_name)
