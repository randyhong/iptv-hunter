#!/usr/bin/env python3
"""IPTV Hunter 安装脚本"""

import os
import sys
import subprocess
import shutil

def main():
    """安装IPTV Hunter"""
    print("🔧 IPTV Hunter 安装程序")
    print("=" * 50)
    
    # 设置项目路径
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print(f"❌ Python版本过低: {python_version.major}.{python_version.minor}")
        print("   需要Python 3.8或更高版本")
        return False
    
    print(f"✓ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查虚拟环境
    venv_path = os.path.join(project_root, 'venv')
    if os.path.exists(venv_path):
        print("📦 虚拟环境已存在，跳过创建...")
    else:
        # 创建新的虚拟环境
        print("📦 创建虚拟环境...")
        try:
            subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
            print("✓ 虚拟环境创建成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ 创建虚拟环境失败: {e}")
            return False
    
    # 获取虚拟环境中的Python路径
    if os.name == 'nt':  # Windows
        venv_python = os.path.join(venv_path, 'Scripts', 'python.exe')
        venv_pip = os.path.join(venv_path, 'Scripts', 'pip.exe')
    else:  # Unix/Linux/macOS
        venv_python = os.path.join(venv_path, 'bin', 'python')
        venv_pip = os.path.join(venv_path, 'bin', 'pip')
    
    # 升级pip
    print("⬆️  升级pip...")
    try:
        subprocess.run([venv_python, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
        print("✓ pip升级成功")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  pip升级失败: {e}")
    
    # 安装依赖
    print("📚 安装Python依赖...")
    
    # 检测CentOS 7并使用兼容的requirements文件
    requirements_file = 'requirements.txt'
    if os.name != 'nt':  # 非Windows系统
        try:
            # 检查是否为CentOS 7
            if os.path.exists('/etc/redhat-release'):
                with open('/etc/redhat-release', 'r') as f:
                    release_info = f.read()
                    if 'CentOS Linux release 7' in release_info or 'Red Hat Enterprise Linux Server release 7' in release_info:
                        if os.path.exists('requirements-centos7.txt'):
                            print("📦 检测到CentOS 7，使用兼容的依赖版本...")
                            requirements_file = 'requirements-centos7.txt'
        except Exception:
            pass
    
    try:
        subprocess.run([venv_python, '-m', 'pip', 'install', '-r', requirements_file], check=True)
        print("✓ 依赖安装成功")
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False
    
    # 创建必要目录
    print("📁 创建目录结构...")
    dirs = ['data', 'logs', 'output']
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"✓ {dir_name}/")
    
    # 创建.env文件
    env_file = '.env'
    if not os.path.exists(env_file):
        print("⚙️  创建配置文件...")
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
        print("✓ .env文件创建成功")
    
    # 测试安装
    print("\n🧪 测试安装...")
    try:
        result = subprocess.run([venv_python, 'test_imports.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ 模块导入测试通过")
        else:
            print("⚠️  模块导入测试失败:")
            print(result.stdout)
            print(result.stderr)
    except Exception as e:
        print(f"⚠️  测试失败: {e}")
    
    print("\n🎉 安装完成！")
    print("=" * 50)
    print("📖 使用方法:")
    print("   python quickstart.py     # 快速开始")
    print("   python run.py --help     # 查看命令")
    print("   python run.py run        # 运行完整流程")
    print("\n💡 提示:")
    print("   - 编辑 config/channels.yaml 来配置频道")
    print("   - 生成的播放列表在 output/ 目录中")
    print("   - 日志文件在 logs/ 目录中")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ 安装失败，请检查错误信息")
        sys.exit(1)