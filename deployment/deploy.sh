#!/bin/bash

echo "=== 视频分析工具服务器部署脚本 ==="
echo ""

echo "步骤 1: 安装依赖"
pip install -r requirements.txt

echo ""
echo "步骤 2: 创建必要的目录"
mkdir -p logs static/frames output video_downloads

echo ""
echo "步骤 3: 初始化配置文件"
if [ ! -f .env ]; then
    cp .env.example .env
    echo "请编辑 .env 文件配置 API 密钥"
fi

echo ""
echo "步骤 4: 启动服务"
echo "开发环境运行: python main.py"
echo "生产环境运行: gunicorn -w 4 -b 0.0.0.0:5000 main:app"
echo ""
echo "部署完成!"
