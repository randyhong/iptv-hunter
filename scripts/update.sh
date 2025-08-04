#!/bin/bash

# IPTV Helper 更新脚本

set -e

echo "开始更新 IPTV Helper..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "错误: 未找到虚拟环境，请先运行安装脚本"
    exit 1
fi

# 激活虚拟环境
. venv/bin/activate

# 备份数据库
echo "备份数据库..."
python src/main.py backup

# 更新代码 (如果是 git 仓库)
if [ -d ".git" ]; then
    echo "更新代码..."
    git pull
fi

# 更新依赖
echo "更新依赖..."
pip install --upgrade -r requirements.txt

# 同步频道配置
echo "同步频道配置..."
python src/main.py sync-channels

# 运行完整更新流程
echo "运行更新流程..."
python src/main.py run

echo "更新完成！"