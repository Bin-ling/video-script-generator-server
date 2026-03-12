from config_manager import config_manager

_module_instances = {}

def get_module_info(module_id):
    return config_manager.get_analysis_module(module_id)

def get_enabled_modules():
    modules = config_manager.get_all_modules()
    enabled = []
    for module_id, module in modules.items():
        if module.get('enabled', True):
            enabled.append(module_id)
    return enabled

def get_modules():
    return config_manager.get_all_modules()

def enable_modules(request):
    from flask import jsonify
    data = request.get_json()
    module_ids = data.get('module_ids', [])
    for module_id in module_ids:
        module_config = config_manager.get_analysis_module(module_id)
        if module_config:
            module_config['enabled'] = True
            config_manager.update_analysis_module(module_id, module_config)
    return jsonify({'success': True})

def toggle_module(request):
    from flask import jsonify
    data = request.get_json()
    module_id = data.get('module_id')
    if module_id:
        module_config = config_manager.get_analysis_module(module_id)
        if module_config:
            current_enabled = module_config.get('enabled', True)
            module_config['enabled'] = not current_enabled
            config_manager.update_analysis_module(module_id, module_config)
            return jsonify({'success': True, 'enabled': module_config['enabled']})
    return jsonify({'success': False})
