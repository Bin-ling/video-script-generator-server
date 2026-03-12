from flask import request, jsonify, send_file
import os
import json

def export_analysis():
    try:
        data = request.get_json()
        analysis_id = data.get('analysis_id')
        format_type = data.get('format', 'json')
        
        from app.services.database_service import get_analysis_by_id
        analysis = get_analysis_by_id(analysis_id)
        
        if not analysis:
            return jsonify({'success': False, 'error': 'Analysis not found'})
        
        if format_type == 'json':
            return jsonify({'success': True, 'data': analysis})
        
        return jsonify({'success': False, 'error': 'Unsupported format'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
