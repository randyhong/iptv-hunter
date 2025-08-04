#!/usr/bin/env python3
"""IPTV Hunter 启动脚本"""

import os
import sys
import subprocess

def main():
    """主函数"""
    # 设置 PYTHONPATH
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # 设置环境变量
    os.environ['PYTHONPATH'] = project_root
    
    # 创建必要的目录
    dirs = ['data', 'logs', 'output']
    for dir_name in dirs:
        dir_path = os.path.join(project_root, dir_name)
        os.makedirs(dir_path, exist_ok=True)
    
    # 检查 .env 文件
    env_file = os.path.join(project_root, '.env')
    if not os.path.exists(env_file):
        print("创建 .env 配置文件...")
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("""# IPTV Hunter 环境配置
APP_NAME=IPTV Hunter
DEBUG=false
LOG_LEVEL=INFO
DATABASE__URL=sqlite:///./data/iptv_hunter.db
CHANNELS_FILE=./config/channels.yaml
DATA_DIR=./data
OUTPUT_DIR=./output
LOG_DIR=./logs
""")
        print("已创建 .env 文件")
    
    # 确保使用虚拟环境中的Python
    venv_python = os.path.join(project_root, 'venv', 'bin', 'python')
    if not os.path.exists(venv_python):
        print("❌ 虚拟环境不存在，请先运行以下命令:")
        print("   python3 -m venv venv")
        print("   source venv/bin/activate") 
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    # 运行主程序
    main_script = os.path.join(project_root, 'src', 'main.py')
    
    if len(sys.argv) > 1:
        # 传递命令行参数
        cmd = [venv_python, main_script] + sys.argv[1:]
    else:
        # 显示帮助
        cmd = [venv_python, main_script, '--help']
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"程序运行失败: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)

if __name__ == "__main__":
    main()