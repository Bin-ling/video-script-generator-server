import os
import base64
import httpx
from openai import OpenAI


class LargeLanguageModel:
    def __init__(self, api_key, base_url, model_name):
        """初始化大模型
        
        Args:
            api_key: API Key
            base_url: API 端点地址
            model_name: 模型名称
        """
        # 显式创建httpx.Client，避免自动创建时传递proxies参数
        # 视频分析需要更长超时时间（5分钟）
        print(f"初始化API: base_url={base_url}, model={model_name}")
        
        http_client = httpx.Client(
            base_url=base_url,
            timeout=httpx.Timeout(300.0)
        )
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=http_client
        )
        self.model_name = model_name
        print(f"API客户端初始化完成")
    
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
    
    def analyze_video_directly(self, video_path, prompt, save_result=True, output_dir=None):
        """直接分析视频（不提取帧）
        
        Args:
            video_path: 本地视频路径
            prompt: 分析指令（由外部填写使用）
            save_result: 是否保存分析结果
            output_dir: 输出目录（可选）
            
        Returns:
            完整的视频分析报告，以及保存的文件路径（如果save_result为True）
        """
        # 步骤1：直接分析视频
        print("正在直接分析视频...")
        try:
            # 检查视频文件大小（限制50MB）
            file_size = os.path.getsize(video_path)
            file_size_mb = file_size / (1024 * 1024)
            print(f"视频文件大小：{file_size_mb:.2f} MB")
            
            if file_size_mb > 50:
                return "视频文件过大，超过50MB限制，请使用更小的视频文件进行视频分析", None
            
            # 视频转Base64
            video_base64 = self.video_to_base64(video_path)
            print("视频转Base64成功")
            
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
            
            # 调用模型API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.1,
                max_tokens=3000
            )
            result = response.choices[0].message.content
            print("视频分析完成！")
            
            return result, None
        except Exception as e:
            print(f"视频分析错误: {str(e)}")
            import traceback
            traceback.print_exc()
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
