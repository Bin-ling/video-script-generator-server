import os
import json
import re
from modules.lapian.config import SHOT_TYPES, CAMERA_MOVEMENTS
from modules.analysis.analyzer import LargeLanguageModel
from dotenv import load_dotenv


def get_lapian_llm():
    """获取拉片分析专用的大模型实例"""
    try:
        from app.services.settings_service import get_module_config
        config = get_module_config("lapian")
        if config.get("api_key") and config.get("base_url") and config.get("model_name"):
            print(f"使用拉片专用模型: {config.get('model_name')}")
            return LargeLanguageModel(
                api_key=config.get("api_key"),
                base_url=config.get("base_url"),
                model_name=config.get("model_name")
            )
    except Exception as e:
        print(f"获取拉片模型配置失败: {e}")
    
    try:
        from app.services.settings_service import get_module_config
        config = get_module_config("default")
    except:
        load_dotenv()
        config = {
            "api_key": os.getenv("API_KEY"),
            "base_url": os.getenv("BASE_URL"),
            "model_name": os.getenv("MODEL_NAME")
        }
    
    print(f"使用默认模型: {config.get('model_name')}")
    return LargeLanguageModel(
        api_key=config.get("api_key"),
        base_url=config.get("base_url"),
        model_name=config.get("model_name")
    )


class ShotAnalyzer:
    def __init__(self, llm=None):
        self.llm = llm
        if self.llm is None:
            self.llm = get_lapian_llm()

    def analyze_frame(self, frame_path, timestamp, script_context=""):
        return {
            "shot_type": "未知",
            "camera_movement": "固定",
            "content": "帧分析未启用",
            "key_elements": [],
            "lighting": "未知",
            "color_tone": "未知",
            "timestamp": timestamp,
            "frame_path": frame_path
        }

    def detect_shot_boundaries(self, frame_analyses):
        if not frame_analyses:
            return []
        return [0]

    def analyze_video_shots(self, frames, script_text="", frame_interval=2):
        return {
            'total_frames': len(frames),
            'frame_interval': frame_interval,
            'total_shots': 0,
            'shots': [],
            'frame_analyses': [],
            'script_text': script_text
        }

    def save_analysis_result(self, result, output_path):
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            return output_path
        except Exception as e:
            return None

    def _get_video_duration(self, video_path):
        """获取视频时长"""
        from modules.lapian.preprocessor import get_video_info
        try:
            info = get_video_info(video_path)
            return info.get('duration', 0)
        except:
            return 0

    def _parse_shots_from_text(self, text):
        """手动从文本中解析 shots 数组"""
        shots = []
        
        shots_match = re.search(r'"shots"\s*:\s*\[(.*?)\]', text, re.DOTALL)
        if not shots_match:
            return shots
            
        shots_text = shots_match.group(1)
        
        shot_pattern = re.compile(r'\{([^}]+)\}')
        for shot_match in shot_pattern.finditer(shots_text):
            shot_data = shot_match.group(1)
            shot = {}
            
            m = re.search(r'"shot_id"\s*:\s*(\d+)', shot_data)
            if m:
                shot['shot_id'] = int(m.group(1))
            
            m = re.search(r'"start_time"\s*:\s*([\d.]+)', shot_data)
            if m:
                shot['start_time'] = float(m.group(1))
            
            m = re.search(r'"end_time"\s*:\s*([\d.]+)', shot_data)
            if m:
                shot['end_time'] = float(m.group(1))
            
            m = re.search(r'"shot_type"\s*:\s*"([^"]*)"', shot_data)
            if m:
                shot['shot_type'] = m.group(1)
            
            m = re.search(r'"camera_movement"\s*:\s*"([^"]*)"', shot_data)
            if m:
                shot['camera_movement'] = m.group(1)
            
            m = re.search(r'"content"\s*:\s*"([^"]*)"', shot_data)
            if m:
                shot['content'] = m.group(1)
            
            m = re.search(r'"key_elements"\s*:\s*\[(.*?)\]', shot_data)
            if m:
                key_elements_text = m.group(1)
                shot['key_elements'] = []
                for item in re.finditer(r'"([^"]+)"', key_elements_text):
                    shot['key_elements'].append(item.group(1))
            
            if shot.get('shot_id'):
                shots.append(shot)
        
        return shots

    def _parse_json_response(self, text):
        """JSON 解析"""
        if not text:
            return None
        
        text = text.strip()
        text = text.replace('\x00', '').replace('\ufeff', '')
        
        if text.startswith('{'):
            text = '{' + text[1:].lstrip()
        
        try:
            result = json.loads(text)
            if result:
                return result
        except:
            pass
        
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            json_str = json_match.group()
            
            for attempt in range(6):
                try:
                    result = json.loads(json_str)
                    if result:
                        return result
                except:
                    if attempt == 0:
                        json_str = re.sub(r',\s*\}', '}', json_str)
                        json_str = re.sub(r',\s*\]', ']', json_str)
                    elif attempt == 1:
                        json_str = json_str.rstrip()
                        if json_str.endswith(','):
                            json_str = json_str[:-1]
                    elif attempt == 2:
                        json_str = json_str.replace("'", '"')
                    elif attempt == 3:
                        json_str = json_str.replace(''', '"').replace(''', '"')
                    elif attempt == 4:
                        shots = self._parse_shots_from_text(json_str)
                        if shots:
                            return {
                                "total_shots": len(shots),
                                "shots": shots,
                                "summary": {}
                            }
                    elif attempt == 5:
                        shots = self._parse_shots_from_text(text)
                        if shots:
                            return {
                                "total_shots": len(shots),
                                "shots": shots,
                                "summary": {}
                            }
        
        shots = self._parse_shots_from_text(text)
        if shots:
            return {
                "total_shots": len(shots),
                "shots": shots,
                "summary": {}
            }
        
        return None

    def _check_complete(self, result, video_duration):
        """检查分析结果是否完整"""
        if not result:
            return False, "结果为空"
        
        shots = result.get('shots', [])
        if not shots:
            return False, "没有镜头数据"
        
        last_shot = shots[-1]
        last_end_time = last_shot.get('end_time', 0)
        
        # 如果最后一个镜头的结束时间接近视频时长，认为是完整的
        # 允许 2 秒的误差
        if video_duration > 0 and abs(last_end_time - video_duration) < 2:
            return True, "完整"
        
        # 如果最后一个镜头结束时间小于视频时长，认为不完整
        if last_end_time < video_duration:
            return False, f"不完整: 最后镜头结束时间 {last_end_time}s < 视频时长 {video_duration}s"
        
        # 如果最后一个镜头结束时间超过视频时长，认为不完整
        if last_end_time > video_duration:
            return False, f"不完整: 最后镜头结束时间 {last_end_time}s > 视频时长 {video_duration}s"
        
        return True, "完整"

    def analyze_video_directly(self, video_path, prompt=None, script_text="", save_result=True, output_dir=None):
        file_size = os.path.getsize(video_path) / (1024 * 1024)
        print(f"视频文件大小: {file_size:.2f} MB")

        if file_size > 20:
            print("警告: 视频文件较大")

        # 获取视频时长
        video_duration = self._get_video_duration(video_path)
        print(f"视频时长: {video_duration} 秒")

        if prompt is None:
            prompt = f"""请分析这个视频，从专业影视拉片角度进行详细分析。

请按以下JSON格式返回分析结果（只返回JSON，不要其他文字）：
{{
    "total_shots": 镜头总数,
    "shots": [
        {{
            "shot_id": 1,
            "start_time": 开始时间(秒),
            "end_time": 结束时间(秒),
            "shot_type": "景别",
            "camera_movement": "运镜方式",
            "content": "画面内容描述",
            "key_elements": ["关键元素1", "关键元素2"]
        }}
    ],
    "summary": {{
        "main_shot_type": "主要景别",
        "main_camera_movement": "主要运镜方式",
        "total_duration": 总时长(秒)
    }}
}}

可选景别: {', '.join(SHOT_TYPES)}
可选运镜: {', '.join(CAMERA_MOVEMENTS)}

重要提示: 请分析完整的视频，确保最后一个镜头的 end_time 等于视频总时长 {video_duration} 秒!
相关脚本内容: {script_text[:500] if script_text else '无'}"""

        max_retries = 3
        retry_count = 0
        all_shots = []
        
        while retry_count < max_retries:
            try:
                if retry_count == 0:
                    current_prompt = prompt
                else:
                    # 继续请求，要求补充剩余镜头
                    current_prompt = f"""请继续分析这个视频的剩余部分。

视频总时长: {video_duration} 秒
已分析的镜头数: {len(all_shots)}
最后一个已分析镜头的结束时间: {all_shots[-1].get('end_time', 0) if all_shots else 0} 秒

请继续从最后一个镜头结束时间开始分析，补充剩余的镜头。
确保最后一个镜头的 end_time 等于 {video_duration} 秒!

请按以下JSON格式返回:
{{
    "shots": [
        {{
            "shot_id": 镜头序号,
            "start_time": 开始时间,
            "end_time": 结束时间,
            "shot_type": "景别",
            "camera_movement": "运镜方式",
            "content": "内容描述",
            "key_elements": ["关键元素"]
        }}
    ]
}}
只返回JSON，不要其他文字!"""

                result_text, _ = self.llm.analyze_video_directly(
                    video_path, 
                    current_prompt, 
                    save_result=False
                )
                
                print(f"AI返回结果长度: {len(result_text) if result_text else 0} 字符")
                
                # 解析结果
                parsed = self._parse_json_response(result_text)
                
                if parsed:
                    new_shots = parsed.get('shots', [])
                    if new_shots:
                        # 调整 shot_id
                        start_id = len(all_shots) + 1
                        for shot in new_shots:
                            shot['shot_id'] = start_id
                            all_shots.append(shot)
                            start_id += 1
                        
                        print(f"已获取 {len(all_shots)} 个镜头")
                        
                        # 检查是否完整
                        is_complete, msg = self._check_complete({"shots": all_shots}, video_duration)
                        print(f"完整性检查: {msg}")
                        
                        if is_complete:
                            break
                    else:
                        print("没有获取到新镜头")
                
                retry_count += 1
                
            except Exception as e:
                print(f"分析失败: {e}")
                import traceback
                traceback.print_exc()
                break
        
        # 构建最终结果
        result = {
            "total_shots": len(all_shots),
            "shots": all_shots,
            "summary": {}
        }
        
        if len(all_shots) > 0:
            print(f"JSON解析成功! 共{len(all_shots)}个镜头")
        else:
            print(f"JSON解析失败")
            result["raw_result"] = "解析失败"
        
        print("视频分析完成!")

        if save_result and output_dir:
            # 保存原始响应（如果需要）
            raw_output_path = os.path.join(output_dir, 'ai_raw_response.txt')
            try:
                with open(raw_output_path, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(result, ensure_ascii=False, indent=2))
            except:
                pass
            
            # 保存解析后的结果
            output_path = os.path.join(output_dir, 'direct_analysis_result.json')
            self.save_analysis_result(result, output_path)

        return result
