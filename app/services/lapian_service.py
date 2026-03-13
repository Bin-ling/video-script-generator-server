from flask import request, jsonify
import os
import time
import uuid
import json
import shutil
from database import lapian_db
from app.utils.logger import logger
from modules.utils.file_utils import create_output_folder
from modules.lapian.main import VideoLapianTool
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
        
        file_size = os.path.getsize(video_path) / (1024 * 1024)
        logger.info(f"[拉片上传] 视频大小: {file_size:.2f} MB")
        
        record_id = lapian_db.insert_lapian({
            'task_id': task_id,
            'filename': filename,
            'video_path': video_path,
            'output_dir': output_dir,
            'status': 'uploaded'
        })
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'file_path': video_path,
            'output_dir': output_dir,
            'record_id': record_id,
            'file_size': file_size
        })
    except Exception as e:
        logger.error(f"[拉片上传] 上传失败: {str(e)}")
        import traceback
        traceback.print_exc()
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
        
        lapian_db.update_lapian(task_id, {'status': 'processing'})
        
        lapian_tool = VideoLapianTool()
        result = lapian_tool.process(video_path, output_dir, extract_shots=extract_shots)
        
        logger.info(f"[拉片处理] 处理结果: {result.get('status')}")
        
        if result.get('status') == 'completed':
            report = result.get('report', {})
            shots = report.get('shots', [])
            
            lapian_db.update_lapian(task_id, {
                'status': 'completed',
                'total_shots': len(shots),
                'total_duration': report.get('video_info', {}).get('duration', 0),
                'shots_data': shots,
                'report_data': report
            })
            
            return jsonify({
                'success': True,
                'message': 'Processing completed',
                'output_dir': output_dir,
                'total_shots': len(shots),
                'report_file': os.path.join(output_dir, 'lapian_report.json'),
                'markdown_file': os.path.join(output_dir, 'lapian_report.md')
            })
        else:
            error_msg = result.get('error', 'Unknown error')
            lapian_db.update_lapian(task_id, {'status': 'failed'})
            return jsonify({'success': False, 'error': error_msg}), 500
            
    except Exception as e:
        logger.error(f"[拉片处理] 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if task_id:
            lapian_db.update_lapian(task_id, {'status': 'failed'})
        return jsonify({'success': False, 'error': str(e)}), 500

def get_lapian_status(task_id):
    try:
        record = lapian_db.get_lapian_by_task_id(task_id)
        if record:
            return jsonify({
                'status': record.get('status', 'unknown'),
                'progress': 100 if record.get('status') == 'completed' else 50 if record.get('status') == 'processing' else 0
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
            output_dir = record.get('output_dir')
            result = {
                'success': True,
                'record': record
            }
            
            if output_dir:
                report_file = os.path.join(output_dir, 'lapian_report.json')
                if os.path.exists(report_file):
                    with open(report_file, 'r', encoding='utf-8') as f:
                        result['report'] = json.load(f)
                
                md_file = os.path.join(output_dir, 'lapian_report.md')
                if os.path.exists(md_file):
                    with open(md_file, 'r', encoding='utf-8') as f:
                        result['markdown'] = f.read()
            
            return jsonify(result)
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
            output_dir = record.get('output_dir')
            result = {
                'success': True,
                'record': record
            }
            
            if output_dir:
                report_file = os.path.join(output_dir, 'lapian_report.json')
                if os.path.exists(report_file):
                    with open(report_file, 'r', encoding='utf-8') as f:
                        result['report'] = json.load(f)
            
            return jsonify(result)
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
