#!/bin/bash

# IPTV Helper 安装脚本

set -e

echo "开始安装 IPTV Helper..."

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "错误: 需要 Python 3.8 或更高版本，当前版本: $python_version"
    exit 1
fi

echo "Python 版本检查通过: $python_version"

# 检查 ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "警告: 未找到 ffmpeg，某些功能可能无法正常工作"
    echo "请安装 ffmpeg:"
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  CentOS/RHEL: sudo yum install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo "  Windows: 下载并安装 https://ffmpeg.org/download.html"
else
    echo "ffmpeg 检查通过"
fi

# 创建虚拟环境
echo "创建虚拟环境..."
python3 -m venv venv

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo "升级 pip..."
pip install --upgrade pip

# 安装依赖
echo "安装 Python 依赖..."
pip install -r requirements.txt

# 创建必要的目录
echo "创建目录结构..."
mkdir -p data logs output

# 复制配置文件
if [ ! -f .env ]; then
    echo "创建环境配置文件..."
    cp .env.example .env
    echo "请编辑 .env 文件以配置您的设置"
fi

# 初始化数据库
echo "初始化数据库..."
python src/main.py sync-channels

echo "安装完成！"
echo ""
echo "使用方法:"
echo "1. 激活虚拟环境: source venv/bin/activate"
echo "2. 编辑频道配置: config/channels.yaml"
echo "3. 同步频道配置: python src/main.py sync-channels"
echo "4. 运行完整流程: python src/main.py run"
echo "5. 查看帮助: python src/main.py --help"
echo ""
echo "生成的播放列表将保存在 output/ 目录中"