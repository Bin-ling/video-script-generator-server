from flask import render_template, request, make_response, send_file, jsonify
from app.services.analysis_service import process_video
from app.services.video_service import download_video
from app.services.module_service import get_modules, enable_modules, toggle_module
from app.services.analysis_service import load_analysis_result
from app.services.database_service import get_all_analyses, get_analysis_by_id, delete_analysis
from app.services.settings_service import get_model_config, save_model_config, get_all_configs, get_module_config
from app.services.cookie_service import save_cookies
from app.utils.progress_manager import progress
from app.utils.task_manager import async_tasks, task_lock, executor
import time
import os

def register_routes(app):
    @app.route('/', methods=['GET', 'POST'])
    def index():
        from app.services.module_service import get_enabled_modules
        
        results = []
        if request.method == 'POST':
            try:
                urls = [u.strip() for u in request.form.get('urls', '').splitlines() if u.strip()]
                files = request.files.getlist('files')
                
                if not urls and not files:
                    results.append({
                        'url': '输入错误', 'error': '请提供视频URL或上传视频文件', 'frames': [],
                        'info': {'duration': 0}, 'stats': {'play':0,'like':0,'comment':0,'collect':0,'share':0},
                        'type': '失败', 'content_ana':'', 'data_ana':'', 'script_ana':'', 'storyboard':'',
                        'photo_ana':'', 'color_ana':'', 'bgm':'', 'topic':'', 'title':'', 'cover':'', 'best_time':''
                    })
                    return render_template('index.html', results=results, enumerate=enumerate)
                
                try:
                    frame_interval = float(request.form.get('frame_interval', 2))
                    if frame_interval <= 0 or frame_interval > 10:
                        frame_interval = 2
                except ValueError:
                    frame_interval = 2
                
                try:
                    max_comments = int(request.form.get('max_comments', 100))
                    if max_comments <= 0 or max_comments > 1000:
                        max_comments = 100
                except ValueError:
                    max_comments = 100
                
                try:
                    max_replies = int(request.form.get('max_replies', 5))
                    if max_replies <= 0 or max_replies > 20:
                        max_replies = 5
                except ValueError:
                    max_replies = 5
                
                try:
                    max_frames = int(request.form.get('max_frames', 15))
                    if max_frames <= 0 or max_frames > 50:
                        max_frames = 15
                except ValueError:
                    max_frames = 15
                
                enabled_modules = get_enabled_modules()
                
                for url in urls:
                    try:
                        if not url.startswith(('http://', 'https://')):
                            results.append({
                                'url': url, 'error': '无效的URL格式', 'frames': [],
                                'info': {'duration': 0}, 'stats': {'play':0,'like':0,'comment':0,'collect':0,'share':0},
                                'type': '失败', 'content_ana':'', 'data_ana':'', 'script_ana':'', 'storyboard':'',
                                'photo_ana':'', 'color_ana':'', 'bgm':'', 'topic':'', 'title':'', 'cover':'', 'best_time':''
                            })
                            continue
                        
                        path, data_file, video_dir, stats, video_title, video_data_json = download_video(url, max_comments=max_comments, max_replies=max_replies)
                        process_video(url, path, data_file, video_dir, stats, results, frame_interval, video_title, video_data_json, enabled_modules, max_frames)
                    except Exception as e:
                        results.append({
                            'url': url, 'error': f'处理失败: {str(e)}', 'frames': [],
                            'info': {'duration': 0}, 'stats': {'play':0,'like':0,'comment':0,'collect':0,'share':0},
                            'type': '失败', 'content_ana':'', 'data_ana':'', 'script_ana':'', 'storyboard':'',
                            'photo_ana':'', 'color_ana':'', 'bgm':'', 'topic':'', 'title':'', 'cover':'', 'best_time':''
                        })
                
                for file in files:
                    if file and file.filename.endswith(('.mp4', '.avi', '.mov', '.wmv')):
                        try:
                            file.seek(0, os.SEEK_END)
                            file_size = file.tell()
                            file.seek(0)
                            
                            if file_size > 500 * 1024 * 1024:
                                results.append({
                                    'url': file.filename, 'error': '文件大小超过限制（500MB）', 'frames': [],
                                    'info': {'duration': 0}, 'stats': {'play':0,'like':0,'comment':0,'collect':0,'share':0},
                                    'type': '失败', 'content_ana':'', 'data_ana':'', 'script_ana':'', 'storyboard':'',
                                    'photo_ana':'', 'color_ana':'', 'bgm':'', 'topic':'', 'title':'', 'cover':'', 'best_time':''
                                })
                                continue
                            
                            fn = f'tmp_{int(time.time())}_{file.filename}'
                            file.save(fn)
                            stats = {'play': 0, 'like': 0, 'comment': 0, 'collect': 0, 'share': 0}
                            process_video(file.filename, fn, None, None, stats, results, frame_interval, max_frames=max_frames)
                        except Exception as e:
                            results.append({
                                'url': file.filename, 'error': f'处理失败: {str(e)}', 'frames': [],
                                'info': {'duration': 0}, 'stats': {'play':0,'like':0,'comment':0,'collect':0,'share':0},
                                'type': '失败', 'content_ana':'', 'data_ana':'', 'script_ana':'', 'storyboard':'',
                                'photo_ana':'', 'color_ana':'', 'bgm':'', 'topic':'', 'title':'', 'cover':'', 'best_time':''
                            })
                    else:
                        results.append({
                            'url': file.filename if file else '未知文件', 'error': '不支持的文件格式', 'frames': [],
                            'info': {'duration': 0}, 'stats': {'play':0,'like':0,'comment':0,'collect':0,'share':0},
                            'type': '失败', 'content_ana':'', 'data_ana':'', 'script_ana':'', 'storyboard':'',
                            'photo_ana':'', 'color_ana':'', 'bgm':'', 'topic':'', 'title':'', 'cover':'', 'best_time':''
                        })
            except Exception as e:
                results.append({
                    'url': '系统错误', 'error': f'系统错误: {str(e)}', 'frames': [],
                    'info': {'duration': 0}, 'stats': {'play':0,'like':0,'comment':0,'collect':0,'share':0},
                    'type': '失败', 'content_ana':'', 'data_ana':'', 'script_ana':'', 'storyboard':'',
                    'photo_ana':'', 'color_ana':'', 'bgm':'', 'topic':'', 'title':'', 'cover':'', 'best_time':''
                })
        return render_template('index.html', results=results, enumerate=enumerate)

    @app.route('/get_cookies')
    def get_cookies_page():
        return render_template('get_cookies.html')

    @app.route('/save_cookies', methods=['POST'])
    def save_cookies_route():
        return save_cookies(request)

    @app.route('/output/<path:filename>')
    def serve_output_file(filename):
        file_path = os.path.join('output', filename)
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return '文件不存在', 404

    @app.route('/settings')
    def settings():
        config = get_all_configs()
        return render_template('settings.html', config=config)

    @app.route('/api/save_model_config', methods=['POST'])
    def save_model_config_route():
        return save_model_config(request)

    @app.route('/api/model_configs')
    def model_configs_route():
        return jsonify(get_all_configs())

    @app.route('/api/module_config/<module_name>')
    def module_config_route(module_name):
        return jsonify(get_module_config(module_name))

    @app.route('/history')
    def history():
        analyses = get_all_analyses()
        return render_template('history.html', analyses=analyses)

    @app.route('/modules')
    def modules_page():
        return render_template('modules.html')

    @app.route('/analysis')
    def analysis_results():
        return render_template('analysis_results.html')

    @app.route('/api/analysis/load', methods=['POST'])
    def load_analysis_result_route():
        return load_analysis_result(request)

    @app.route('/api/modules/config')
    def get_modules_config():
        from modules.analysis.modules.manager import module_manager
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

    @app.route('/api/modules')
    def get_modules_route():
        from modules.analysis.modules.manager import module_manager
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

    @app.route('/api/modules/<module_id>/toggle', methods=['POST'])
    def toggle_module_route(module_id):
        from modules.analysis.modules.manager import module_manager
        try:
            status = module_manager.toggle_module(module_id)
            return jsonify({'success': True, 'enabled': status})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/modules/enable', methods=['POST'])
    def enable_modules_route():
        return enable_modules(request)

    @app.route('/api/get_analysis/<int:analysis_id>')
    def get_analysis_route(analysis_id):
        analysis = get_analysis_by_id(analysis_id)
        
        from config_manager import config_manager
        modules_config = config_manager.get_all_modules()
        
        if analysis and analysis.get('output_dir'):
            output_dir = analysis['output_dir']
            if not output_dir.startswith('output'):
                output_dir = os.path.join('output', output_dir)
            
            module_file_map = {
                'content_analysis': 'content_analysis.json',
                'data_analysis': 'data_analysis.json',
                'script_analysis': 'script_analysis.json',
                'storyboard_analysis': 'storyboard_analysis.json',
                'photo_analysis': 'photo_analysis.json',
                'color_analysis': 'color_analysis.json',
                'bgm_analysis': 'bgm_analysis.json',
                'topic_analysis': 'topic_analysis.json',
                'title_analysis': 'title_analysis.json',
                'cover_analysis': 'cover_analysis.json',
                'publish_time_analysis': 'publish_time_analysis.json'
            }
            
            module_field_map = {
                'content_analysis': 'content_ana',
                'data_analysis': 'data_ana',
                'script_analysis': 'script_ana',
                'storyboard_analysis': 'storyboard',
                'photo_analysis': 'photo_ana',
                'color_analysis': 'color_ana',
                'bgm_analysis': 'bgm',
                'topic_analysis': 'topic',
                'title_analysis': 'analysis_title',
                'cover_analysis': 'cover',
                'publish_time_analysis': 'best_time'
            }
            
            module_type_map = {}
            for module_id, module_info in modules_config.items():
                module_type_map[module_id] = {
                    'type': module_info.get('type', 'text_analysis'),
                    'name': module_info.get('name', module_id)
                }
            
            analysis['modules_info'] = module_type_map
            
            enabled_modules = analysis.get('enabled_modules', [])
            for module_id in enabled_modules:
                if module_id in module_file_map:
                    json_file = os.path.join(output_dir, module_file_map[module_id])
                    if os.path.exists(json_file):
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                result = None
                                if 'video' in data and 'analysis_content' in data['video']:
                                    result = data['video']['analysis_content']
                                elif 'frame' in data and 'analysis_content' in data['frame']:
                                    result = data['frame']['analysis_content']
                                elif 'text' in data and 'analysis_content' in data['text']:
                                    result = data['text']['analysis_content']
                                elif 'result' in data:
                                    result = data['result']
                                
                                if result:
                                    field_name = module_field_map.get(module_id, module_id)
                                    analysis[field_name] = result
                        except Exception as e:
                            pass
        
        return jsonify(analysis)

    @app.route('/api/delete_analysis/<int:analysis_id>')
    def delete_analysis_route(analysis_id):
        success = delete_analysis(analysis_id)
        return jsonify({'success': success})

    @app.route('/api/progress')
    def get_progress():
        return jsonify(progress)
    
    @app.route('/api/check_cookies')
    def check_cookies():
        cookies_exists = os.path.exists('cookies.txt')
        if cookies_exists:
            with open('cookies.txt', 'r', encoding='utf-8') as f:
                content = f.read().strip()
                cookies_exists = len(content) > 0
        return jsonify({'status': 'success', 'exists': cookies_exists, 'message': 'Cookies checked'})

    @app.route('/api/analyze', methods=['POST'])
    def start_analysis():
        global progress
        
        try:
            if not request.is_json:
                return jsonify({'success': False, 'error': '请求数据必须为JSON格式'}), 400
            
            data = request.get_json()
            url = data.get('url')
            
            if not url:
                return jsonify({'success': False, 'error': '请提供视频链接'}), 400
            
            url = url.strip().strip('`')
            
            import re
            url_match = re.search(r'https?://.+', url)
            if url_match:
                url = url_match.group(0)
                url = re.sub(r'[\s\r\n\t`]+$', '', url)
            
            if not url.startswith(('http://', 'https://')):
                return jsonify({'success': False, 'error': '无效的URL格式'}), 400
            
            try:
                frame_interval = float(data.get('frame_interval', 2))
                if frame_interval <= 0 or frame_interval > 10:
                    frame_interval = 2
            except ValueError:
                frame_interval = 2
            
            try:
                max_comments = int(data.get('max_comments', 100))
                if max_comments <= 0 or max_comments > 1000:
                    max_comments = 100
            except ValueError:
                max_comments = 100
            
            try:
                max_replies = int(data.get('max_replies', 5))
                if max_replies <= 0 or max_replies > 20:
                    max_replies = 5
            except ValueError:
                max_replies = 5
            
            try:
                max_frames = int(data.get('max_frames', 15))
                if max_frames <= 0 or max_frames > 50:
                    max_frames = 15
            except ValueError:
                max_frames = 15
            
            task_id = int(time.time())
            
            with task_lock:
                async_tasks[task_id] = {
                    'status': 'running',
                    'progress': 0,
                    'message': '开始分析...',
                    'result': None,
                    'error': None
                }
            
            progress["percentage"] = 0
            progress["status"] = "开始分析"
            
            def run_analysis():
                global progress
                try:
                    with task_lock:
                        async_tasks[task_id]['progress'] = 5
                        async_tasks[task_id]['message'] = '下载视频...'
                    progress["percentage"] = 5
                    progress["status"] = "下载视频"
                    
                    path, data_file, video_dir, stats, video_title, video_data_json = download_video(
                        url, max_comments=max_comments, max_replies=max_replies
                    )
                    
                    with task_lock:
                        async_tasks[task_id]['progress'] = 10
                        async_tasks[task_id]['message'] = '处理视频...'
                    progress["percentage"] = 10
                    progress["status"] = "处理视频"
                    
                    from app.services.module_service import get_enabled_modules
                    enabled_modules = get_enabled_modules()
                    
                    results = []
                    process_video(url, path, data_file, video_dir, stats, results, frame_interval, video_title, video_data_json, enabled_modules, max_frames=max_frames)
                    
                    if results:
                        result = results[0]
                        
                        with task_lock:
                            async_tasks[task_id]['progress'] = 100
                            async_tasks[task_id]['message'] = '分析完成'
                            async_tasks[task_id]['status'] = 'completed'
                            async_tasks[task_id]['result'] = result
                        progress["percentage"] = 100
                        progress["status"] = "分析完成"
                    else:
                        raise Exception('分析结果为空')
                        
                except Exception as e:
                    error_msg = f'分析失败: {str(e)}'
                    with task_lock:
                        async_tasks[task_id]['status'] = 'failed'
                        async_tasks[task_id]['error'] = error_msg
                    progress["status"] = error_msg
            
            executor.submit(run_analysis)
            
            return jsonify({
                'success': True,
                'task_id': task_id
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': f'系统错误: {str(e)}'}), 500
    
    @app.route('/api/analyze/<int:task_id>')
    def get_analysis_status(task_id):
        with task_lock:
            if task_id in async_tasks:
                task = async_tasks[task_id]
                task['progress'] = progress.get("percentage", task.get('progress', 0))
                task['message'] = progress.get("status", task.get('message', ''))
                return jsonify(task)
            else:
                return jsonify({
                    'status': 'not_found',
                    'message': '任务不存在'
                })

    @app.route('/lapian')
    def lapian_page():
        return render_template('lapian.html')

    @app.route('/api/lapian/upload', methods=['POST'])
    def lapian_upload():
        from app.services.lapian_service import upload_lapian_video
        return upload_lapian_video()

    @app.route('/api/lapian/process', methods=['POST'])
    def lapian_process():
        from app.services.lapian_service import process_lapian
        return process_lapian()

    @app.route('/api/lapian/status/<task_id>')
    def lapian_status(task_id):
        from app.services.lapian_service import get_lapian_status
        return get_lapian_status(task_id)

    @app.route('/api/lapian/download/<task_id>')
    def lapian_download(task_id):
        from app.services.lapian_service import get_lapian_result
        return get_lapian_result(task_id)

    @app.route('/api/lapian/history')
    def lapian_history():
        from app.services.lapian_service import get_lapian_history
        return get_lapian_history()

    @app.route('/api/lapian/record/<int:record_id>')
    def lapian_record(record_id):
        from app.services.lapian_service import get_lapian_record
        return get_lapian_record(record_id)

    @app.route('/api/lapian/record/<int:record_id>', methods=['DELETE'])
    def lapian_record_delete(record_id):
        from app.services.lapian_service import delete_lapian_record
        return delete_lapian_record(record_id)
