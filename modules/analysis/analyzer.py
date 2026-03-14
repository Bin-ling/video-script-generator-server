import os
import base64
import httpx
import logging
from openai import OpenAI

# 配置日志
logger = logging.getLogger(__name__)


class LargeLanguageModel:
    def __init__(self, api_key, base_url, model_name):
        """初始化大模型
        
        Args:
            api_key: API Key
            base_url: API 端点地址
            model_name: 模型名称
        """
        logger.info(f"初始化API: base_url={base_url}, model={model_name}")
        
        # 视频分析需要更长超时时间（10分钟）
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
        logger.info(f"API客户端初始化完成")
    
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
    
    def analyze_image(self, image_path, prompt, save_result=True, output_dir=None):
        """分析图片
        
        Args:
            image_path: 本地图片路径
            prompt: 分析指令（由外部填写使用）
            save_result: 是否保存分析结果
            output_dir: 输出目录（可选）
            
        Returns:
            模型返回的分析结果，以及保存的文件路径（如果save_result为True）
        """
        # 图片转Base64
        img_base64 = self.image_to_base64(image_path)
        
        # 调用模型API
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
            
            return result, None
        except Exception as e:
            raise Exception(f"API调用失败：{str(e)}")
    
    def analyze_video_directly(self, video_path, prompt, save_result=True, output_dir=None, max_retries=3):
        """直接分析视频（不提取帧），支持流式输出和重试
        
        Args:
            video_path: 本地视频路径
            prompt: 分析指令（由外部填写使用）
            save_result: 是否保存分析结果
            output_dir: 输出目录（可选）
            max_retries: 最大重试次数
            
        Returns:
            完整的视频分析报告，以及保存的文件路径（如果save_result为True）
        """
        logger.info("=" * 50)
        logger.info("[视频分析] 开始直接分析视频")
        
        # 检查视频文件大小
        file_size = os.path.getsize(video_path)
        file_size_mb = file_size / (1024 * 1024)
        logger.info(f"[视频分析] 视频文件大小：{file_size_mb:.2f} MB")
        
        if file_size_mb > 50:
            logger.warning("[视频分析] 视频文件过大，超过50MB限制")
            return "视频文件过大，超过50MB限制，请使用更小的视频文件进行视频分析", None
        
        # 视频转Base64
        logger.info("[视频分析] 正在将视频转换为Base64...")
        video_base64 = self.video_to_base64(video_path)
        logger.info(f"[视频分析] 视频转Base64成功，长度: {len(video_base64)} 字符")
        
        # 构建请求消息
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "video_url",
                        "video_url": {
                            "url": f"data:video/mp4;base64,{video_base64}"
                        }
                    }
                ]
            }
        ]
        
        # 重试机制
        for attempt in range(max_retries):
            try:
                logger.info(f"[视频分析] 第 {attempt + 1}/{max_retries} 次尝试")
                logger.info("[视频分析] 发送请求到模型API...")
                
                # 使用流式输出
                result_chunks = []
                chunk_count = 0
                
                stream = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=8000,  # 增加max_tokens
                    stream=True  # 启用流式输出
                )
                
                logger.info("[视频分析] 开始接收流式响应...")
                
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        result_chunks.append(content)
                        chunk_count += 1
                        
                        # 每100个chunk打印一次进度
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
                    import time
                    wait_time = (attempt + 1) * 5  # 递增等待时间
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
        # 导入processor模块中的extract_frames函数
        from modules.video_processor.processor import extract_frames
        
        # 使用processor.py中的extract_frames函数提取帧并保存到指定文件夹
        frames = extract_frames(video_path, interval=frame_interval, max_frames=15, output_dir=output_dir)
        
        # 打印提取结果
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
        # 步骤1：分析文本
        print("正在分析文本...")
        try:
            # 构建完整的提示词，包含自定义关键词
            full_prompt = prompt
            if keywords:
                keywords_str = ", ".join(keywords)
                full_prompt = f"{prompt}\n\n请特别关注以下关键词：{keywords_str}"
            
            # 构建请求消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{full_prompt}\n\n文本内容：{text}"}
                    ]
                }
            ]
            
            # 调用模型API
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
