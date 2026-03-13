from flask import request, jsonify
import os
import time
import uuid
import json
from database import lapian_db

def upload_lapian_video():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if not file.filename.endswith(('.mp4', '.avi', '.mov', '.wmv')):
            return jsonify({'success': False, 'error': 'Unsupported file format'})
        
        task_id = str(uuid.uuid4())
        video_dir = f'video_downloads/lapian_{task_id}'
        os.makedirs(video_dir, exist_ok=True)
        
        video_path = os.path.join(video_dir, file.filename)
        file.save(video_path)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'file_path': video_path
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def process_lapian():
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        video_path = data.get('video_path')
        
        if not task_id or not video_path:
            return jsonify({'success': False, 'error': 'Missing parameters'})
        
        return jsonify({
            'success': True,
            'message': 'Processing started'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def get_lapian_status(task_id):
    return jsonify({
        'status': 'completed',
        'progress': 100
    })

def get_lapian_result(task_id):
    return jsonify({'success': False, 'error': 'Not implemented'})

def get_lapian_history():
    records = lapian_db.get_all_lapian()
    return jsonify({'success': True, 'records': records})

def get_lapian_record(record_id):
    record = lapian_db.get_lapian_by_id(record_id)
    if record:
        return jsonify({'success': True, 'record': record})
    return jsonify({'success': False, 'error': 'Record not found'})

def delete_lapian_record(record_id):
    success = lapian_db.delete_lapian(record_id)
    return jsonify({'success': success})
