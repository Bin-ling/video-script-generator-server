"""
模块管理路由
"""

from flask import Blueprint, render_template, request, jsonify
from modules.analysis.modules.manager import module_manager
from config_manager import config_manager

module_bp = Blueprint('module', __name__)

@module_bp.route('/modules', methods=['GET'])
def modules():
    modules = module_manager.get_all_modules()
    return render_template('modules.html', modules=modules)

@module_bp.route('/api/modules', methods=['GET'])
def get_modules():
    modules = module_manager.get_all_modules()
    modules_data = []
    for module_id, module in modules.items():
        modules_data.append({
            'id': module_id,
            'name': module.get_name(),
            'description': module.get_description(),
            'type': module.get_type(),
            'enabled': module.is_enabled(),
            'config': module.get_config()
        })
    return jsonify({'success': True, 'modules': modules_data})

@module_bp.route('/api/modules/<module_id>/toggle', methods=['POST'])
def toggle_module(module_id):
    try:
        status = module_manager.toggle_module(module_id)
        return jsonify({'success': True, 'enabled': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@module_bp.route('/api/modules/<module_id>/config', methods=['GET'])
def get_module_config(module_id):
    module = module_manager.get_module(module_id)
    if module:
        module_data = {
            'id': module.module_id,
            'name': module.get_name(),
            'description': module.get_description(),
            'type': module.get_type(),
            'enabled': module.is_enabled(),
            'config': module.get_config()
        }
        return jsonify({'success': True, 'config': module_data})
    return jsonify({'success': False, 'error': '模块不存在'})

@module_bp.route('/api/modules/<module_id>/config', methods=['PUT'])
def update_module_config(module_id):
    try:
        data = request.get_json()
        config = data.get('config', {})
        module = module_manager.get_module(module_id)
        if module:
            if 'name' in config:
                module.module_config['name'] = config['name']
            if 'description' in config:
                module.module_config['description'] = config['description']
            if 'type' in config:
                module.module_config['type'] = config['type']
            if 'enabled' in config:
                module.module_config['enabled'] = config['enabled']
            if 'config' in config:
                module_manager.update_module_config(module_id, config['config'])
            else:
                module_manager.update_module_config(module_id, config)
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': '模块不存在'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@module_bp.route('/api/modules', methods=['POST'])
def add_module():
    try:
        data = request.get_json()
        module_id = data.get('id')
        module_config = data.get('config', {})
        if not module_config.get('name'):
            module_config['name'] = module_id
        if not module_config.get('description'):
            module_config['description'] = f"{module_config.get('name', module_id)}模块"
        if not module_config.get('type'):
            module_config['type'] = 'text_analysis'
        if 'enabled' not in module_config:
            module_config['enabled'] = True
        if not module_config.get('config'):
            module_config['config'] = {
                'input_prompt_template': f"你是专业的{module_config.get('name', module_id)}分析师。根据以下内容，分析：\n{{output_keywords}}",
                'output_keywords': ["分析要点1", "分析要点2", "分析要点3"]
            }
        module_manager.add_module(module_id, module_config)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@module_bp.route('/api/modules/<module_id>', methods=['DELETE'])
def remove_module(module_id):
    try:
        module_manager.remove_module(module_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
