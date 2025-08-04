#!/usr/bin/env python3
"""测试所有模块是否能正常导入"""

import os
import sys

# 设置项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """测试所有模块导入"""
    tests = []
    
    # 测试配置模块
    try:
        from config.settings import get_settings
        tests.append(("✓", "config.settings"))
    except Exception as e:
        tests.append(("✗", f"config.settings - {e}"))
    
    # 测试数据模型
    try:
        from src.models import Channel, Link, CheckResult
        tests.append(("✓", "src.models"))
    except Exception as e:
        tests.append(("✗", f"src.models - {e}"))
    
    # 测试服务模块
    try:
        from src.services import ChannelManager, LinkCollector, LinkChecker, M3UGenerator
        tests.append(("✓", "src.services"))
    except Exception as e:
        tests.append(("✗", f"src.services - {e}"))
    
    # 测试工具模块
    try:
        from src.utils.logger import setup_logger
        from src.utils.database import init_database
        from src.utils.validators import validate_url
        tests.append(("✓", "src.utils"))
    except Exception as e:
        tests.append(("✗", f"src.utils - {e}"))
    
    # 显示结果
    print("模块导入测试结果:")
    print("=" * 40)
    for status, message in tests:
        print(f"{status} {message}")
    
    # 统计
    success_count = sum(1 for status, _ in tests if status == "✓")
    total_count = len(tests)
    
    print("=" * 40)
    print(f"成功: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 所有模块导入成功！")
        return True
    else:
        print("❌ 部分模块导入失败，请检查错误信息")
        return False

def test_basic_functionality():
    """测试基本功能"""
    print("\n基本功能测试:")
    print("=" * 40)
    
    try:
        # 测试配置
        from config.settings import get_settings
        settings = get_settings()
        print(f"✓ 配置加载成功 - {settings.app_name}")
        
        # 测试数据库模型
        from src.models.base import Base
        print("✓ 数据库模型加载成功")
        
        # 测试服务类
        from src.services.channel_manager import ChannelManager
        manager = ChannelManager()
        print("✓ 频道管理器创建成功")
        
        print("🎉 基本功能测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🧪 IPTV Hunter 项目完整性检查")
    print("=" * 50)
    
    # 检查必要文件
    required_files = [
        'config/channels.yaml',
        'requirements.txt',
        'src/main.py',
        'src/models/__init__.py',
        'src/services/__init__.py',
        'src/utils/__init__.py',
    ]
    
    print("必要文件检查:")
    print("-" * 20)
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} (缺失)")
    
    print()
    
    # 测试导入
    import_success = test_imports()
    
    if import_success:
        functionality_success = test_basic_functionality()
        
        if functionality_success:
            print("\n🎯 项目检查完成 - 一切正常！")
            print("你现在可以运行:")
            print("  python quickstart.py    # 快速开始")
            print("  python run.py --help    # 查看命令")
        else:
            print("\n⚠️  项目检查完成 - 存在功能问题")
    else:
        print("\n❌ 项目检查失败 - 存在导入问题")

if __name__ == "__main__":
    main()