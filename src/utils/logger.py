"""日志配置工具"""

import os
import sys
from loguru import logger
from config.settings import get_settings


def setup_logger():
    """设置日志配置"""
    settings = get_settings()
    
    # 移除默认日志处理器
    logger.remove()
    
    # 确保日志目录存在
    os.makedirs(settings.log_dir, exist_ok=True)
    
    # 控制台日志
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        colorize=True,
    )
    
    # 文件日志 - 信息日志
    logger.add(
        os.path.join(settings.log_dir, "iptv_hunter.log"),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
    )
    
    # 文件日志 - 错误日志
    logger.add(
        os.path.join(settings.log_dir, "error.log"),
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 week",
        retention="8 weeks",
        compression="zip",
        encoding="utf-8",
    )
    
    # 如果是调试模式，添加调试日志
    if settings.debug:
        logger.add(
            os.path.join(settings.log_dir, "debug.log"),
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="1 day",
            retention="7 days",
            encoding="utf-8",
        )
    
    logger.info(f"日志系统已初始化，级别: {settings.log_level}")
    return logger