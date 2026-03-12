import sqlite3
import os
import json
from threading import Lock

class Database:
    def __init__(self, db_path='video_analysis.db'):
        self.db_path = db_path
        self._create_tables()
        self._lock = Lock()
    
    def _create_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            title TEXT,
            output_dir TEXT,
            info TEXT,
            stats TEXT,
            content_ana TEXT,
            data_ana TEXT,
            script_ana TEXT,
            storyboard TEXT,
            photo_ana TEXT,
            color_ana TEXT,
            bgm TEXT,
            topic TEXT,
            analysis_title TEXT,
            cover TEXT,
            best_time TEXT,
            enabled_modules TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_created_at ON analysis_records(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_url ON analysis_records(url)')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prompts_name ON prompts(name)')
        
        default_prompts = [
            ('SHORT_ANALYSIS', '请分析以下视频内容，提供简洁的分析报告，包括内容概述、亮点和改进建议。\n\n{text}'),
            ('LONG_ANALYSIS', '请详细分析以下视频内容，提供全面的分析报告，包括内容概述、结构分析、拍摄技巧、剪辑手法、音效使用、受众反应等方面。\n\n{text}'),
            ('DATA_ANALYSIS', '请基于以下数据对视频进行数据分析，包括播放量、点赞数、评论数、收藏数、分享数和时长等指标，分析视频的表现并提供优化建议。\n\n播放量: {play}\n点赞数: {like}\n评论数: {comment}\n收藏数: {collect}\n分享数: {share}\n时长: {duration}秒'),
            ('SCRIPT_WITH_FRAME', '请基于以下视频内容和{frame_count}张关键帧截图，生成逐镜脚本，包括镜头编号、画面描述、台词/旁白、音乐音效等信息。\n\n{text}'),
            ('STORYBOARD_PROMPT', '请基于以下视频内容，生成标准分镜表，包括镜号、景别、镜头运动、画面内容、音效、时长等信息。\n\n{text}'),
            ('PHOTO_ANALYSIS', '请分析以下视频的摄影运镜技巧，包括镜头类型、运动方式、构图方法、光线运用等方面，并提供专业评价。\n\n{text}'),
            ('COLOR_ANALYSIS', '请分析以下视频的色彩风格，包括色调、饱和度、对比度、色彩搭配等方面，并提供达芬奇调色参数建议。\n\n{text}'),
            ('BGM_PROMPT', '请分析以下视频的背景音乐使用，并推荐适合的可商用背景音乐。\n\n{text}'),
            ('TOPIC_PROMPT', '请基于以下视频内容，推荐相关的热门选题方向。\n\n{text}'),
            ('TITLE_PROMPT', '请基于以下视频内容，生成5个爆款标题。\n\n{text}'),
            ('COVER_PROMPT', '请基于以下视频内容，生成封面文案建议。\n\n{text}'),
            ('TIME_PROMPT', '请基于以下视频内容，分析最佳发布时间。\n\n{text}')
        ]
        
        for name, content in default_prompts:
            cursor.execute('''
            INSERT OR IGNORE INTO prompts (name, content) VALUES (?, ?)
            ''', (name, content))
        
        conn.commit()
        conn.close()
    
    def insert_analysis(self, data):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO analysis_records (
                url, title, output_dir, info, stats, content_ana, data_ana, 
                script_ana, storyboard, photo_ana, color_ana, bgm, topic, 
                analysis_title, cover, best_time, enabled_modules
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('url'),
                data.get('title'),
                data.get('output_dir'),
                json.dumps(data.get('info', {})),
                json.dumps(data.get('stats', {})),
                data.get('content_ana'),
                data.get('data_ana'),
                data.get('script_ana'),
                data.get('storyboard'),
                data.get('photo_ana'),
                data.get('color_ana'),
                data.get('bgm'),
                data.get('topic'),
                data.get('analysis_title'),
                data.get('cover'),
                data.get('best_time'),
                json.dumps(data.get('enabled_modules', []))
            ))
            
            record_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return record_id
    
    def get_all_analyses(self):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, url, title, output_dir, created_at 
            FROM analysis_records 
            ORDER BY created_at DESC
            ''')
            
            records = []
            for row in cursor.fetchall():
                records.append({
                    'id': row[0],
                    'url': row[1],
                    'title': row[2],
                    'output_dir': row[3],
                    'created_at': row[4]
                })
            
            conn.close()
            return records
    
    def get_analysis_by_id(self, analysis_id):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM analysis_records WHERE id = ?
            ''', (analysis_id,))
            
            row = cursor.fetchone()
            if row:
                record = {
                    'id': row[0],
                    'url': row[1],
                    'title': row[2],
                    'output_dir': row[3],
                    'info': json.loads(row[4]),
                    'stats': json.loads(row[5]),
                    'content_ana': row[6],
                    'data_ana': row[7],
                    'script_ana': row[8],
                    'storyboard': row[9],
                    'photo_ana': row[10],
                    'color_ana': row[11],
                    'bgm': row[12],
                    'topic': row[13],
                    'analysis_title': row[14],
                    'cover': row[15],
                    'best_time': row[16],
                    'enabled_modules': json.loads(row[17]) if row[17] else [],
                    'created_at': row[18]
                }
                conn.close()
                return record
            
            conn.close()
            return None
    
    def delete_analysis(self, analysis_id):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            DELETE FROM analysis_records WHERE id = ?
            ''', (analysis_id,))
            
            affected_rows = cursor.rowcount
            conn.commit()
            conn.close()
            return affected_rows > 0
    
    def get_all_prompts(self):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, name, content FROM prompts ORDER BY name
            ''')
            
            prompts = []
            for row in cursor.fetchall():
                prompts.append({
                    'id': row[0],
                    'name': row[1],
                    'content': row[2]
                })
            
            conn.close()
            return prompts
    
    def update_prompt(self, prompt_id, content):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            UPDATE prompts SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
            ''', (content, prompt_id))
            
            affected_rows = cursor.rowcount
            conn.commit()
            conn.close()
            return affected_rows > 0
    
    def get_prompt_by_name(self, name):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT content FROM prompts WHERE name = ?
            ''', (name,))
            
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None

db = Database()


class LapianDatabase:
    def __init__(self, db_path='video_analysis.db'):
        self.db_path = db_path
        self._create_tables()
        self._lock = Lock()
    
    def _create_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS lapian_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE,
            video_name TEXT,
            video_path TEXT,
            output_dir TEXT,
            total_shots INTEGER,
            total_duration REAL,
            main_shot_type TEXT,
            main_camera_movement TEXT,
            shots_data TEXT,
            report_data TEXT,
            shot_files TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lapian_created_at ON lapian_records(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lapian_task_id ON lapian_records(task_id)')
        
        conn.commit()
        conn.close()
    
    def insert_lapian(self, data):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT OR REPLACE INTO lapian_records (
                task_id, video_name, video_path, output_dir, total_shots,
                total_duration, main_shot_type, main_camera_movement,
                shots_data, report_data, shot_files
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('task_id'),
                data.get('video_name'),
                data.get('video_path'),
                data.get('output_dir'),
                data.get('total_shots', 0),
                data.get('total_duration', 0),
                data.get('main_shot_type', ''),
                data.get('main_camera_movement', ''),
                json.dumps(data.get('shots_data', [])),
                json.dumps(data.get('report_data', {})),
                json.dumps(data.get('shot_files', []))
            ))
            
            record_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return record_id
    
    def get_all_lapian(self, limit=50):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, task_id, video_name, total_shots, total_duration,
                   main_shot_type, main_camera_movement, created_at
            FROM lapian_records 
            ORDER BY created_at DESC
            LIMIT ?
            ''', (limit,))
            
            records = []
            for row in cursor.fetchall():
                records.append({
                    'id': row[0],
                    'task_id': row[1],
                    'video_name': row[2],
                    'total_shots': row[3],
                    'total_duration': row[4],
                    'main_shot_type': row[5],
                    'main_camera_movement': row[6],
                    'created_at': row[7]
                })
            
            conn.close()
            return records
    
    def get_lapian_by_id(self, record_id):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM lapian_records WHERE id = ?
            ''', (record_id,))
            
            row = cursor.fetchone()
            if row:
                record = {
                    'id': row[0],
                    'task_id': row[1],
                    'video_name': row[2],
                    'video_path': row[3],
                    'output_dir': row[4],
                    'total_shots': row[5],
                    'total_duration': row[6],
                    'main_shot_type': row[7],
                    'main_camera_movement': row[8],
                    'shots_data': json.loads(row[9]) if row[9] else [],
                    'report_data': json.loads(row[10]) if row[10] else {},
                    'shot_files': json.loads(row[11]) if row[11] else [],
                    'created_at': row[12]
                }
                conn.close()
                return record
            
            conn.close()
            return None
    
    def get_lapian_by_task_id(self, task_id):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM lapian_records WHERE task_id = ?
            ''', (task_id,))
            
            row = cursor.fetchone()
            if row:
                record = {
                    'id': row[0],
                    'task_id': row[1],
                    'video_name': row[2],
                    'video_path': row[3],
                    'output_dir': row[4],
                    'total_shots': row[5],
                    'total_duration': row[6],
                    'main_shot_type': row[7],
                    'main_camera_movement': row[8],
                    'shots_data': json.loads(row[9]) if row[9] else [],
                    'report_data': json.loads(row[10]) if row[10] else {},
                    'shot_files': json.loads(row[11]) if row[11] else [],
                    'created_at': row[12]
                }
                conn.close()
                return record
            
            conn.close()
            return None
    
    def update_lapian(self, record_id, data):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            UPDATE lapian_records SET
                total_shots = ?,
                total_duration = ?,
                main_shot_type = ?,
                main_camera_movement = ?,
                shots_data = ?,
                report_data = ?,
                shot_files = ?
            WHERE id = ?
            ''', (
                data.get('total_shots', 0),
                data.get('total_duration', 0),
                data.get('main_shot_type', ''),
                data.get('main_camera_movement', ''),
                json.dumps(data.get('shots_data', [])),
                json.dumps(data.get('report_data', {})),
                json.dumps(data.get('shot_files', [])),
                record_id
            ))
            
            affected_rows = cursor.rowcount
            conn.commit()
            conn.close()
            return affected_rows > 0
    
    def delete_lapian(self, record_id):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            DELETE FROM lapian_records WHERE id = ?
            ''', (record_id,))
            
            affected_rows = cursor.rowcount
            conn.commit()
            conn.close()
            return affected_rows > 0
    
    def delete_lapian_by_task_id(self, task_id):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            DELETE FROM lapian_records WHERE task_id = ?
            ''', (task_id,))
            
            affected_rows = cursor.rowcount
            conn.commit()
            conn.close()
            return affected_rows > 0


lapian_db = LapianDatabase()
