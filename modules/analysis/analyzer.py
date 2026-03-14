import os
import base64
import httpx
import logging
import time
from openai import OpenAI
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

VIDEO_BASE64_THRESHOLD_MB = 50
IMAGE_BASE64_THRESHOLD_MB = 50
MAX_VIDEO_SIZE_MB = 512
MAX_IMAGE_SIZE_MB = 512


class LargeLanguageModel:
    def __init__(self, api_key, base_url, model_name, video_fps: float = 1.0):
        """初始化大模型
        
        Args:
            api_key: API Key
            base_url: API 端点地址
            model_name: 模型名称
            video_fps: 视频分析fps参数，控制视频理解的精细度，默认1.0，范围0.2-5
        """
        logger.info(f"初始化API: base_url={base_url}, model={model_name}")
        
        http_client = httpx.Client(
            base_url=base_url,
            timeout=httpx.Timeout(600.0, connect=60.0)
        )
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=http_client
        )
        self.model_name = model_name
        self.video_fps = max(0.2, min(5.0, video_fps))
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        logger.info(f"API客户端初始化完成，视频fps: {self.video_fps}")
    
    def image_to_base64(self, image_path):
        """将本地图片转换为Base64编码
        
        Args:
            image_path: 本地图片路径
            
        Returns:
            Base64编码字符串
        """
        try:
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            raise Exception(f"图片转Base64失败：{str(e)}")
    
    def video_to_base64(self, video_path):
        """将本地视频转换为Base64编码
        
        Args:
            video_path: 本地视频路径
            
        Returns:
            Base64编码字符串
        """
        try:
            with open(video_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            raise Exception(f"视频转Base64失败：{str(e)}")
    
    def get_file_size_mb(self, file_path: str) -> float:
        """获取文件大小（MB）
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件大小（MB）
        """
        file_size = os.path.getsize(file_path)
        return file_size / (1024 * 1024)
    
    def upload_file_via_files_api(self, file_path: str, file_type: str = "video") -> Optional[str]:
        """通过Files API上传文件
        
        Args:
            file_path: 本地文件路径
            file_type: 文件类型，"video" 或 "image"
            
        Returns:
            文件ID，失败返回None
        """
        logger.info(f"[Files API] 开始上传文件: {file_path}")
        
        try:
            with open(file_path, "rb") as f:
                files_payload = {
                    "file": f,
                    "purpose": (None, "user_data"),
                }
                
                if file_type == "video":
                    data_payload = {
                        "preprocess_configs[video][fps]": str(self.video_fps)
                    }
                else:
                    data_payload = {}
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                upload_url = f"{self.base_url}/files"
                logger.info(f"[Files API] 上传URL: {upload_url}")
                
                response = httpx.post(
                    upload_url,
                    headers=headers,
                    files=files_payload,
                    data=data_payload,
                    timeout=300.0
                )
                
                if response.status_code != 200:
                    logger.error(f"[Files API] 上传失败: {response.status_code} - {response.text}")
                    return None
                
                result = response.json()
                file_id = result.get("id")
                logger.info(f"[Files API] 文件上传成功，file_id: {file_id}")
                
                return file_id
                
        except Exception as e:
            logger.error(f"[Files API] 上传异常: {str(e)}")
            return None
    
    def wait_for_file_processing(self, file_id: str, max_wait_seconds: int = 300) -> bool:
        """等待文件处理完成
        
        Args:
            file_id: 文件ID
            max_wait_seconds: 最大等待时间（秒）
            
        Returns:
            处理是否成功
        """
        logger.info(f"[Files API] 等待文件处理完成: {file_id}")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        start_time = time.time()
        while time.time() - start_time < max_wait_seconds:
            try:
                retrieve_url = f"{self.base_url}/files/{file_id}"
                response = httpx.get(retrieve_url, headers=headers, timeout=30.0)
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status")
                    logger.info(f"[Files API] 文件状态: {status}")
                    
                    if status == "processed":
                        logger.info(f"[Files API] 文件处理完成")
                        return True
                    elif status == "error":
                        logger.error(f"[Files API] 文件处理失败")
                        return False
                
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"[Files API] 查询文件状态异常: {str(e)}")
                time.sleep(2)
        
        logger.error(f"[Files API] 等待文件处理超时")
        return False
    
    def analyze_image(self, image_path, prompt, save_result=True, output_dir=None):
        """分析图片，自动选择Base64或Files API上传方式
        
        Args:
            image_path: 本地图片路径
            prompt: 分析指令（由外部填写使用）
            save_result: 是否保存分析结果
            output_dir: 输出目录（可选）
            
        Returns:
            模型返回的分析结果，以及保存的文件路径（如果save_result为True）
        """
        logger.info("=" * 50)
        logger.info("[图片分析] 开始分析图片")
        
        file_size_mb = self.get_file_size_mb(image_path)
        logger.info(f"[图片分析] 图片文件大小：{file_size_mb:.2f} MB")
        
        if file_size_mb > MAX_IMAGE_SIZE_MB:
            logger.error(f"[图片分析] 图片文件过大，超过{MAX_IMAGE_SIZE_MB}MB限制")
            return f"图片文件过大，超过{MAX_IMAGE_SIZE_MB}MB限制", None
        
        use_files_api = file_size_mb > IMAGE_BASE64_THRESHOLD_MB
        
        if use_files_api:
            logger.info(f"[图片分析] 文件大小超过{IMAGE_BASE64_THRESHOLD_MB}MB，使用Files API上传")
            
            file_id = self.upload_file_via_files_api(image_path, file_type="image")
            if not file_id:
                return "Files API上传失败", None
            
            if not self.wait_for_file_processing(file_id):
                return "文件处理超时", None
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"file://{image_path}"
                                    }
                                }
                            ]
                        }
                    ],
                    temperature=0.1,
                    max_tokens=2000
                )
                result = response.choices[0].message.content
                logger.info("[图片分析] 图片分析完成！")
                logger.info("=" * 50)
                return result, None
                
            except Exception as e:
                logger.error(f"[图片分析] API调用失败：{str(e)}")
                return f"API调用失败：{str(e)}", None
        else:
            logger.info(f"[图片分析] 文件大小小于{IMAGE_BASE64_THRESHOLD_MB}MB，使用Base64编码")
            
            img_base64 = self.image_to_base64(image_path)
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{img_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    temperature=0.1,
                    max_tokens=2000
                )
                result = response.choices[0].message.content
                logger.info("[图片分析] 图片分析完成！")
                logger.info("=" * 50)
                return result, None
                
            except Exception as e:
                logger.error(f"[图片分析] API调用失败：{str(e)}")
                return f"API调用失败：{str(e)}", None
    
    def analyze_video_directly(self, video_path, prompt, save_result=True, output_dir=None, max_retries=3, fps=None):
        """直接分析视频（不提取帧），自动选择Base64或Files API上传方式，支持流式输出和重试
        
        Args:
            video_path: 本地视频路径
            prompt: 分析指令（由外部填写使用）
            save_result: 是否保存分析结果
            output_dir: 输出目录（可选）
            max_retries: 最大重试次数
            fps: 视频fps参数，控制视频理解的精细度，默认使用初始化时的设置，范围0.2-5
            
        Returns:
            完整的视频分析报告，以及保存的文件路径（如果save_result为True）
        """
        logger.info("=" * 50)
        logger.info("[视频分析] 开始直接分析视频")
        
        video_fps = fps if fps is not None else self.video_fps
        video_fps = max(0.2, min(5.0, video_fps))
        logger.info(f"[视频分析] 使用fps参数: {video_fps}")
        
        file_size_mb = self.get_file_size_mb(video_path)
        logger.info(f"[视频分析] 视频文件大小：{file_size_mb:.2f} MB")
        
        if file_size_mb > MAX_VIDEO_SIZE_MB:
            logger.error(f"[视频分析] 视频文件过大，超过{MAX_VIDEO_SIZE_MB}MB限制")
            return f"视频文件过大，超过{MAX_VIDEO_SIZE_MB}MB限制，请使用更小的视频文件", None
        
        use_files_api = file_size_mb > VIDEO_BASE64_THRESHOLD_MB
        
        if use_files_api:
            logger.info(f"[视频分析] 文件大小超过{VIDEO_BASE64_THRESHOLD_MB}MB，使用Files API上传")
            
            original_fps = self.video_fps
            self.video_fps = video_fps
            file_id = self.upload_file_via_files_api(video_path, file_type="video")
            self.video_fps = original_fps
            
            if not file_id:
                return "Files API上传失败", None
            
            if not self.wait_for_file_processing(file_id):
                return "文件处理超时", None
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "video_url",
                            "video_url": {
                                "url": f"file://{video_path}"
                            }
                        }
                    ]
                }
            ]
        else:
            logger.info(f"[视频分析] 文件大小小于{VIDEO_BASE64_THRESHOLD_MB}MB，使用Base64编码")
            
            logger.info("[视频分析] 正在将视频转换为Base64...")
            video_base64 = self.video_to_base64(video_path)
            logger.info(f"[视频分析] 视频转Base64成功，长度: {len(video_base64)} 字符")
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "video_url",
                            "video_url": {
                                "url": f"data:video/mp4;base64,{video_base64}",
                                "fps": video_fps
                            }
                        }
                    ]
                }
            ]
        
        for attempt in range(max_retries):
            try:
                logger.info(f"[视频分析] 第 {attempt + 1}/{max_retries} 次尝试")
                logger.info("[视频分析] 发送请求到模型API...")
                
                result_chunks = []
                chunk_count = 0
                
                stream = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=8000,
                    stream=True
                )
                
                logger.info("[视频分析] 开始接收流式响应...")
                
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        result_chunks.append(content)
                        chunk_count += 1
                        
                        if chunk_count % 100 == 0:
                            logger.info(f"[视频分析] 已接收 {chunk_count} 个数据块，当前长度: {len(''.join(result_chunks))} 字符")
                
                result = ''.join(result_chunks)
                logger.info(f"[视频分析] 流式响应完成，共 {chunk_count} 个数据块")
                logger.info(f"[视频分析] 响应总长度: {len(result)} 字符")
                logger.info("[视频分析] 视频分析完成！")
                logger.info("=" * 50)
                
                return result, None
                
            except Exception as e:
                logger.error(f"[视频分析] 第 {attempt + 1} 次尝试失败: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    logger.info(f"[视频分析] 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error("[视频分析] 所有重试均失败")
                    return f"视频分析失败：{str(e)}", None
    
    def extract_video_frames(self, video_path, output_dir="./video_frames", frame_interval=2):
        """视频提取关键帧
        
        Args:
            video_path: 本地视频路径
            output_dir: 帧文件存储目录
            frame_interval: 拆帧间隔（秒）
            
        Returns:
            所有帧文件的路径列表
        """
        from modules.video_processor.processor import extract_frames
        
        frames = extract_frames(video_path, interval=frame_interval, max_frames=15, output_dir=output_dir)
        
        if frames:
            print(f"成功提取{len(frames)}帧，保存至：{os.path.join(output_dir, 'frames')}")
        else:
            print("提取帧失败")
        
        return frames
         
    def analyze_text(self, text, prompt, keywords=None, save_result=True, output_dir=None):
        """分析文本
        
        Args:
            text: 要分析的文本内容
            prompt: 分析指令
            keywords: 自定义关键词列表（可选）
            save_result: 是否保存分析结果
            output_dir: 输出目录（可选）
            
        Returns:
            模型返回的分析结果，以及保存的文件路径（如果save_result为True）
        """
        print("正在分析文本...")
        try:
            full_prompt = prompt
            if keywords:
                keywords_str = ", ".join(keywords)
                full_prompt = f"{prompt}\n\n请特别关注以下关键词：{keywords_str}"
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{full_prompt}\n\n文本内容：{text}"}
                    ]
                }
            ]
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.1,
                max_tokens=3000
            )
            result = response.choices[0].message.content
            print("文本分析完成！")
            
            return result, None
        except Exception as e:
            return f"文本分析失败：{str(e)}", None
