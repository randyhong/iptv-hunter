@echo off
REM IPTV Helper Windows 安装脚本

echo 开始安装 IPTV Helper...

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python 检查通过

REM 检查 ffmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo 警告: 未找到 ffmpeg，某些功能可能无法正常工作
    echo 请下载并安装 ffmpeg: https://ffmpeg.org/download.html
    echo 并将其添加到系统 PATH 中
)

REM 创建虚拟环境
echo 创建虚拟环境...
python -m venv venv

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 升级 pip
echo 升级 pip...
python -m pip install --upgrade pip

REM 安装依赖
echo 安装 Python 依赖...
pip install -r requirements.txt

REM 创建必要的目录
echo 创建目录结构...
if not exist data mkdir data
if not exist logs mkdir logs
if not exist output mkdir output

REM 复制配置文件
if not exist .env (
    echo 创建环境配置文件...
    copy .env.example .env
    echo 请编辑 .env 文件以配置您的设置
)

REM 初始化数据库
echo 初始化数据库...
python src\main.py sync-channels

echo 安装完成！
echo.
echo 使用方法:
echo 1. 激活虚拟环境: venv\Scripts\activate.bat
echo 2. 编辑频道配置: config\channels.yaml
echo 3. 同步频道配置: python src\main.py sync-channels
echo 4. 运行完整流程: python src\main.py run
echo 5. 查看帮助: python src\main.py --help
echo.
echo 生成的播放列表将保存在 output\ 目录中

pause