FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
COPY src/ ./src/
COPY config/ ./config/
COPY setup.py .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建必要的目录
RUN mkdir -p data logs output

# 设置环境变量
ENV PYTHONPATH=/app/src
ENV DATABASE__URL=sqlite:///./data/iptv_helper.db

# 暴露端口 (如果需要 web 服务)
# EXPOSE 8000

# 设置用户
RUN useradd -m -u 1000 iptv && chown -R iptv:iptv /app
USER iptv

# 默认命令
CMD ["python", "src/main.py", "run"]