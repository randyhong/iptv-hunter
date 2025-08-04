"""数据库初始化工具"""

import os
from loguru import logger
from config.settings import get_settings


def init_database():
    """初始化数据库"""
    settings = get_settings()
    
    # 确保数据目录存在
    os.makedirs(settings.data_dir, exist_ok=True)
    
    try:
        # 导入模型以确保表定义被加载
        from src.models import Channel, Link, CheckResult
        from src.models.base import create_tables, engine
        
        # 创建所有表
        create_tables()
        
        logger.info("数据库初始化成功")
        logger.info(f"数据库连接: {settings.database.url}")
        
        # 测试数据库连接
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
            if result:
                logger.info("数据库连接测试成功")
            else:
                logger.warning("数据库连接测试失败")
        
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False


def backup_database(backup_path: str = None):
    """备份数据库"""
    settings = get_settings()
    
    if backup_path is None:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(settings.data_dir, f"backup_{timestamp}.db")
    
    try:
        if settings.database.url.startswith("sqlite"):
            # SQLite备份
            import shutil
            db_path = settings.database.url.replace("sqlite:///", "")
            shutil.copy2(db_path, backup_path)
            logger.info(f"数据库备份完成: {backup_path}")
        else:
            logger.warning("当前只支持SQLite数据库备份")
        
        return backup_path
        
    except Exception as e:
        logger.error(f"数据库备份失败: {e}")
        return None


def restore_database(backup_path: str):
    """恢复数据库"""
    settings = get_settings()
    
    try:
        if settings.database.url.startswith("sqlite"):
            # SQLite恢复
            import shutil
            db_path = settings.database.url.replace("sqlite:///", "")
            shutil.copy2(backup_path, db_path)
            logger.info(f"数据库恢复完成: {backup_path}")
        else:
            logger.warning("当前只支持SQLite数据库恢复")
        
        return True
        
    except Exception as e:
        logger.error(f"数据库恢复失败: {e}")
        return False


def get_database_info():
    """获取数据库信息"""
    try:
        from src.models.base import engine
        from src.models import Channel, Link, CheckResult
        
        with engine.connect() as conn:
            # 获取表信息
            from sqlalchemy import text
            tables_info = {}
            
            # 频道表统计
            result = conn.execute(text("SELECT COUNT(*) FROM channels")).fetchone()
            tables_info["channels"] = result[0] if result else 0
            
            # 链接表统计
            result = conn.execute(text("SELECT COUNT(*) FROM links")).fetchone()
            tables_info["links"] = result[0] if result else 0
            
            # 检测结果表统计
            result = conn.execute(text("SELECT COUNT(*) FROM check_results")).fetchone()
            tables_info["check_results"] = result[0] if result else 0
            
            # 数据库大小（仅SQLite）
            settings = get_settings()
            if settings.database.url.startswith("sqlite"):
                db_path = settings.database.url.replace("sqlite:///", "")
                if os.path.exists(db_path):
                    size_mb = os.path.getsize(db_path) / (1024 * 1024)
                    tables_info["database_size_mb"] = round(size_mb, 2)
            
            return tables_info
            
    except Exception as e:
        logger.error(f"获取数据库信息失败: {e}")
        return {}