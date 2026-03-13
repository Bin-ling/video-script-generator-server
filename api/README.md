# 视频分析 API

为 OpenClaw 等外部系统提供视频分析核心功能的 Python API。

## 功能列表

| 功能 | 说明 |
|------|------|
| 视频下载 | 从抖音等平台下载视频 |
| 视频信息 | 获取视频元数据（时长、分辨率等） |
| 关键帧提取 | 按间隔提取视频关键帧 |
| 音频提取 | 提取视频中的音频 |
| 语音转文字 | 视频语音识别 |
| 视频分析 | 使用 AI 分析视频内容 |
| 图片分析 | 使用 AI 分析图片内容 |
| 文本分析 | 使用 AI 分析文本内容 |
| 完整分析 | 一键执行所有分析模块 |

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

在项目根目录创建 `.env` 文件：

```env
API_KEY=your_api_key_here
BASE_URL=https://ark.cn-beijing.volces.com/api/coding/v3
MODEL_NAME=Doubao-Seed-2.0-pro
```

## 使用方法

### 方法 1: 命令行

```bash
# 下载视频
python -m api download --url "https://example.com/video"

# 获取视频信息
python -m api info --path "video.mp4"

# 提取关键帧
python -m api frames --path "video.mp4" --interval 2 --max-frames 15

# 提取音频
python -m api audio --path "video.mp4"

# 语音转文字
python -m api transcribe --path "video.mp4"

# 分析视频
python -m api analyze-video --path "video.mp4" --prompt "分析这个视频的内容"

# 分析图片
python -m api analyze-image --path "image.jpg" --prompt "描述这张图片"

# 分析文本
python -m api analyze-text --path "文本内容" --prompt "总结这段文本"

# 查看可用模块
python -m api modules

# 完整分析
python -m api full-analysis --path "video.mp4"
```

### 方法 2: Python 代码

```python
from api.client import VideoAnalysisClient

# 初始化客户端
client = VideoAnalysisClient()

# 下载视频
video_info = client.download_video("https://example.com/video")
video_path = video_info.get("video_path")

# 视频分析
result = client.analyze_video(video_path, "分析这个视频的内容")

# 图片分析
result = client.analyze_photo("image.jpg")

# 脚本分析
result = client.analyze_script(video_path)

# 内容分析
result = client.analyze_content(video_path)

# 完整分析
result = client.full_analysis(video_path)
```

## API 详细说明

### VideoAnalysisClient

#### 初始化

```python
client = VideoAnalysisClient(
    api_key="your_api_key",      # 可选，默认从环境变量读取
    base_url="https://...",       # 可选
    model_name="model_name"       # 可选
)
```

#### 方法

| 方法 | 参数 | 返回值 |
|------|------|--------|
| `download_video` | url, output_dir, max_comments | dict |
| `get_video_info` | video_path | dict |
| `extract_frames` | video_path, output_dir, interval, max_frames | list |
| `extract_audio` | video_path, output_path | str |
| `transcribe` | video_path | str |
| `analyze_video` | video_path, prompt, output_dir | str |
| `analyze_image` | image_path, prompt, output_dir | str |
| `analyze_text` | text, prompt, output_dir | str |
| `analyze_script` | video_path, prompt | str |
| `analyze_photo` | image_path, prompt | str |
| `analyze_content` | video_path, prompt | str |
| `analyze_all_modules` | video_path, frames, text, stats, **kwargs | dict |
| `full_analysis` | video_path, output_dir, interval, max_frames | dict |
| `get_enabled_modules` | - | list |
| `get_all_modules` | - | dict |

## 扩展新功能

如需添加新的分析模块，只需继承 `AnalysisModule` 基类：

```python
from modules.analysis.modules.base import AnalysisModule

class MyCustomModule(AnalysisModule):
    def analyze(self, **kwargs):
        # 自定义分析逻辑
        return "分析结果"
```

然后在 `configs/analysis_modules.json` 中注册模块即可。
