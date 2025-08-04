#!/usr/bin/env python3
"""IPTV Hunter 快速开始脚本"""

import os
import sys
import subprocess

def main():
    """快速开始"""
    print("🎯 IPTV Hunter 快速开始")
    print("=" * 50)
    
    # 设置项目路径
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    # 设置 Python 路径
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # 创建必要目录
    dirs = ['data', 'logs', 'output']
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"✓ 创建目录: {dir_name}/")
    
    # 创建 .env 文件
    env_file = '.env'
    if not os.path.exists(env_file):
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("""# IPTV Hunter 环境配置
APP_NAME=IPTV Hunter
DEBUG=true
LOG_LEVEL=INFO
DATABASE__URL=sqlite:///./data/iptv_hunter.db
CHANNELS_FILE=./config/channels.yaml
DATA_DIR=./data
OUTPUT_DIR=./output
LOG_DIR=./logs
""")
        print(f"✓ 创建配置文件: {env_file}")
    
    print("\n🚀 开始运行程序...")
    print("=" * 50)
    
    # 设置环境变量并运行
    env = os.environ.copy()
    env['PYTHONPATH'] = project_root
    
    # 确保使用虚拟环境中的Python
    venv_python = os.path.join(project_root, 'venv', 'bin', 'python')
    if not os.path.exists(venv_python):
        print("❌ 虚拟环境不存在，请先创建虚拟环境:")
        print("   python3 -m venv venv")
        print("   source venv/bin/activate") 
        print("   pip install -r requirements.txt")
        return
    
    try:
        # 1. 同步频道配置
        print("📡 步骤 1: 同步频道配置...")
        result = subprocess.run([
            venv_python, 'src/main.py', 'sync-channels'
        ], env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ 频道配置同步成功")
        else:
            print(f"✗ 频道配置同步失败: {result.stderr}")
            return
        
        # 2. 显示统计信息
        print("\n📊 步骤 2: 显示统计信息...")
        result = subprocess.run([
            venv_python, 'src/main.py', 'stats'
        ], env=env)
        
        print("\n🎉 快速开始完成！")
        print("=" * 50)
        print("💡 接下来你可以：")
        print("   python run.py collect    # 收集频道链接")
        print("   python run.py check      # 检测链接可用性") 
        print("   python run.py generate   # 生成播放列表")
        print("   python run.py run        # 运行完整流程")
        print("   python run.py --help     # 查看所有命令")
        
    except Exception as e:
        print(f"✗ 运行失败: {e}")
        print("\n🔧 故障排除：")
        print("1. 确保已安装所有依赖: pip install -r requirements.txt")
        print("2. 检查 Python 版本 >= 3.8")
        print("3. 检查频道配置文件: config/channels.yaml")

if __name__ == "__main__":
    main()