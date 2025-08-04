"""应用配置管理"""
from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import os


class DatabaseConfig(BaseModel):
    """数据库配置"""
    url: str = Field(default="sqlite:///./data/iptv_hunter.db")
    echo: bool = Field(default=False)
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)


class CrawlerConfig(BaseModel):
    """爬虫配置"""
    timeout: int = Field(default=30)
    retries: int = Field(default=3)
    delay: float = Field(default=1.0)
    user_agent: str = Field(default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    concurrent_requests: int = Field(default=10)


class CheckerConfig(BaseModel):
    """链接检测配置"""
    timeout: int = Field(default=10)
    retries: int = Field(default=2)
    ping_timeout: int = Field(default=5)
    ffmpeg_timeout: int = Field(default=15)
    concurrent_checks: int = Field(default=20)
    min_response_time: float = Field(default=0.1)
    max_response_time: float = Field(default=5.0)


class M3UConfig(BaseModel):
    """M3U生成配置"""
    output_path: str = Field(default="./output/playlist.m3u")
    include_logo: bool = Field(default=True)
    include_group: bool = Field(default=True)
    sort_by_category: bool = Field(default=True)


class SourceConfig(BaseModel):
    """数据源配置"""
    iptv_search_url: str = Field(default="https://iptv-search.com")
    tonkiang_url: str = Field(default="https://tonkiang.us")
    search_delay: float = Field(default=2.0)
    max_links_per_channel: int = Field(default=50)


class Settings(BaseSettings):
    """应用主配置"""
    # 基础配置
    app_name: str = Field(default="IPTV Hunter")
    debug: bool = Field(default=False)
    log_level: str = Field(default="DEBUG")
    
    # 模块配置
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    crawler: CrawlerConfig = Field(default_factory=CrawlerConfig)
    checker: CheckerConfig = Field(default_factory=CheckerConfig)
    m3u: M3UConfig = Field(default_factory=M3UConfig)
    source: SourceConfig = Field(default_factory=SourceConfig)
    
    # 文件路径
    channels_file: str = Field(default="./config/channels.yaml")
    data_dir: str = Field(default="./data")
    output_dir: str = Field(default="./output")
    log_dir: str = Field(default="./logs")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


# 全局设置实例
settings = Settings()


def get_settings() -> Settings:
    """获取设置实例"""
    return settings


def ensure_directories():
    """确保必要的目录存在"""
    for directory in [settings.data_dir, settings.output_dir, settings.log_dir]:
        os.makedirs(directory, exist_ok=True)