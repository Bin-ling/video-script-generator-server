# 视频分析工具服务器部署说明

## 目录结构

```
video-script-generator-server/
├── app/
│   ├── routes/          # 路由
│   ├── services/       # 服务层
│   └── utils/          # 工具类
├── configs/            # 配置文件
├── deployment/         # 部署脚本
│   ├── Dockerfile      # Docker镜像
│   ├── deploy.sh       # Linux部署脚本
│   ├── deploy.bat      # Windows部署脚本
│   ├── nginx.conf     # Nginx配置
│   └── video-analysis.service  # systemd服务
├── logs/               # 日志目录
├── static/             # 静态文件
├── templates/          # HTML模板
├── main.py            # 应用入口
├── config_manager.py  # 配置管理
├── database.py        # 数据库
├── llm.py            # 大语言模型
└── requirements.txt   # 依赖清单
```

## 快速部署

### 方式一：直接运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件填入API密钥

# 3. 启动服务
python main.py
```

### 方式二：使用Gunicorn（生产环境推荐）

```bash
# 启动服务
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 main:app
```

### 方式三：使用Docker

```bash
# 构建镜像
docker build -t video-analysis-server -f deployment/Dockerfile .

# 运行容器
docker run -d -p 5000:5000 -v $(pwd):/app --name video-analysis video-analysis-server
```

### 方式四：使用Systemd（Linux）

```bash
# 复制服务文件
sudo cp deployment/video-analysis.service /etc/systemd/system/

# 启动服务
sudo systemctl start video-analysis
sudo systemctl enable video-analysis
```

### 方式五：使用Nginx反向代理

```bash
# 复制Nginx配置
sudo cp deployment/nginx.conf /etc/nginx/sites-available/video-analysis
sudo ln -s /etc/nginx/sites-available/video-analysis /etc/nginx/sites-enabled/

# 测试并重载Nginx
sudo nginx -t
sudo systemctl reload nginx
```

## 配置说明

### 环境变量

在 `.env` 文件中配置：

- `API_KEY`: 大模型API密钥
- `BASE_URL`: API端点地址
- `MODEL_NAME`: 模型名称
- `LOG_LEVEL`: 日志级别（INFO/DEBUG）
- `SERVER_PORT`: 服务端口（默认5000）

### 系统要求

- Python 3.10+
- FFmpeg（用于视频处理）
- 4GB+ RAM
- 20GB+ 磁盘空间

## 安全建议

1. 使用强API密钥
2. 配置防火墙规则
3. 启用HTTPS（使用Let's Encrypt）
4. 定期备份数据库
5. 监控日志文件大小

## 维护

### 查看日志

```bash
# 实时日志
tail -f logs/video_analysis.log

# 历史日志
ls -la logs/
```

### 备份数据

```bash
# 备份数据库
cp video_analysis.db backup_video_analysis_$(date +%Y%m%d).db

# 备份配置
tar -czf config_backup.tar.gz configs/ .env
```

### 更新部署

```bash
# 拉取新代码
git pull

# 重启服务
sudo systemctl restart video-analysis
```
