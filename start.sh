#!/bin/bash

# 启动视频脚本生成器服务器

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 检查是否已安装依赖
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    echo "安装依赖..."
    venv/bin/pip install -r requirements.txt
fi

# 激活虚拟环境
source venv/bin/activate

# 创建必要的目录
mkdir -p static/frames
mkdir -p output

# 启动应用
echo "启动应用程序..."
echo "应用程序将在 http://0.0.0.0:5000 上运行"
python main.py
