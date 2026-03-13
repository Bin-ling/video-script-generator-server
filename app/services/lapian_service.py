from flask import request, jsonify
import os
import time
import uuid
import json
import shutil
from database import lapian_db
from app.utils.logger import logger
from modules.video_processor.processor import get_video_info, extract_frames
from modules.utils.file_utils import create_output_folder
from modules.analysis.analyzer import LargeLanguageModel
from config_manager import config_manager

def upload_lapian_video():
    try:
        file = request.files.get('file') or request.files.get('video')
        if not file:
            logger.error("[拉片上传] 没有上传文件")
            return jsonify({'success': False, 'error': '没有上传文件，请选择文件'}), 400
        
        filename = file.filename
        if not filename or filename == '':
            logger.error("[拉片上传] 文件名为空")
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.filename.endswith(('.mp4', '.avi', '.mov', '.wmv', '.mkv', '.webm')):
            logger.error(f"[拉片上传] 不支持的文件格式: {file.filename}")
            return jsonify({'success': False, 'error': 'Unsupported file format'}), 400
        
        task_id = str(uuid.uuid4())
        
        output_dir = create_output_folder(f'lapian_{task_id[:8]}')
        logger.info(f"[拉片上传] 创建输出目录: {output_dir}")
        
        video_path = os.path.join(output_dir, 'video.mp4')
        file.save(video_path)
        logger.info(f"[拉片上传] 视频保存到: {video_path}")
        
        video_info = get_video_info(video_path)
        logger.info(f"[拉片上传] 视频信息: {video_info}")
        
        record_id = lapian_db.insert_lapian({
            'task_id': task_id,
            'filename': filename,
            'video_path': video_path,
            'output_dir': output_dir,
            'duration': video_info.get('duration', 0),
            'status': 'uploaded'
        })
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'file_path': video_path,
            'output_dir': output_dir,
            'record_id': record_id,
            'video_info': video_info
        })
    except Exception as e:
        logger.error(f"[拉片上传] 上传失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def process_lapian():
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        video_path = data.get('video_path')
        extract_shots = data.get('extractShots', True)
        
        logger.info(f"[拉片处理] 开始处理: task_id={task_id}, video_path={video_path}, extract_shots={extract_shots}")
        
        if not task_id or not video_path:
            logger.error("[拉片处理] 缺少参数")
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400
        
        if not os.path.exists(video_path):
            logger.error(f"[拉片处理] 视频文件不存在: {video_path}")
            return jsonify({'success': False, 'error': 'Video file not found'}), 404
        
        output_dir = os.path.dirname(video_path)
        
        video_info = get_video_info(video_path)
        logger.info(f"[拉片处理] 视频信息: {video_info}")
        
        frames = []
        if extract_shots:
            frames_dir = os.path.join(output_dir, 'frames')
            os.makedirs(frames_dir, exist_ok=True)
            
            logger.info(f"[拉片处理] 开始提取关键帧到: {frames_dir}")
            frames = extract_frames(
                video_path, 
                interval=2, 
                max_frames=50, 
                output_dir=output_dir
            )
            logger.info(f"[拉片处理] 提取了 {len(frames)} 个关键帧")
        
        lapian_db.update_lapian(task_id, {
            'status': 'processed',
            'frames_count': len(frames),
            'duration': video_info.get('duration', 0)
        })
        
        return jsonify({
            'success': True,
            'message': 'Processing completed',
            'video_info': video_info,
            'frames_count': len(frames),
            'output_dir': output_dir
        })
    except Exception as e:
        logger.error(f"[拉片处理] 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

def get_lapian_status(task_id):
    try:
        record = lapian_db.get_lapian_by_task_id(task_id)
        if record:
            return jsonify({
                'status': record.get('status', 'unknown'),
                'progress': 100 if record.get('status') == 'processed' else 0
            })
        return jsonify({
            'status': 'not_found',
            'progress': 0
        })
    except Exception as e:
        logger.error(f"[拉片状态] 获取状态失败: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

def get_lapian_result(task_id):
    try:
        record = lapian_db.get_lapian_by_task_id(task_id)
        if record:
            return jsonify({
                'success': True,
                'record': record
            })
        return jsonify({'success': False, 'error': 'Record not found'}), 404
    except Exception as e:
        logger.error(f"[拉片结果] 获取结果失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def get_lapian_history():
    try:
        records = lapian_db.get_all_lapian()
        return jsonify({'success': True, 'records': records})
    except Exception as e:
        logger.error(f"[拉片历史] 获取历史失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def get_lapian_record(record_id):
    try:
        record = lapian_db.get_lapian_by_id(record_id)
        if record:
            return jsonify({'success': True, 'record': record})
        return jsonify({'success': False, 'error': 'Record not found'}), 404
    except Exception as e:
        logger.error(f"[拉片记录] 获取记录失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def delete_lapian_record(record_id):
    try:
        record = lapian_db.get_lapian_by_id(record_id)
        if record and record.get('output_dir'):
            output_dir = record['output_dir']
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir, ignore_errors=True)
                logger.info(f"[拉片删除] 删除输出目录: {output_dir}")
        
        success = lapian_db.delete_lapian(record_id)
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"[拉片删除] 删除失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
