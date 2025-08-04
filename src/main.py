"""IPTV Hunter 主程序"""

import asyncio
import click
from typing import Optional
from loguru import logger

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logger import setup_logger
from src.utils.database import init_database, get_database_info, backup_database
from src.utils.validators import validate_config_file
from src.services import ChannelManager, LinkCollector, LinkChecker, M3UGenerator
from config.settings import get_settings, ensure_directories


@click.group()
@click.option('--debug', is_flag=True, help='启用调试模式')
@click.option('--config', type=str, help='指定配置文件路径')
def cli(debug: bool, config: Optional[str]):
    """IPTV Hunter - IPTV频道管理工具"""
    # 设置调试模式
    if debug:
        settings = get_settings()
        settings.debug = True
        settings.log_level = "DEBUG"
    
    # 确保必要的目录存在
    ensure_directories()
    
    # 初始化日志
    setup_logger()
    
    # 初始化数据库
    if not init_database():
        logger.error("数据库初始化失败，程序退出")
        exit(1)
    
    logger.info("IPTV Hunter 已启动")


@cli.command()
@click.option('--file', type=str, help='频道配置文件路径')
def sync_channels(file: Optional[str]):
    """同步频道配置到数据库"""
    logger.info("开始同步频道配置")
    
    # 验证配置文件
    config_file = file or get_settings().channels_file
    validation_result = validate_config_file(config_file)
    
    if not validation_result["valid"]:
        logger.error("配置文件验证失败:")
        for error in validation_result["errors"]:
            logger.error(f"  - {error}")
        return
    
    if validation_result["warnings"]:
        logger.warning("配置文件警告:")
        for warning in validation_result["warnings"]:
            logger.warning(f"  - {warning}")
    
    # 同步频道
    channel_manager = ChannelManager()
    synced_count = channel_manager.sync_channels_to_database()
    
    if synced_count > 0:
        logger.info(f"成功同步 {synced_count} 个频道")
    else:
        logger.warning("没有频道被同步")


@cli.command()
@click.option('--channel', type=str, help='指定频道名称')
@click.option('--category', type=str, help='指定频道分类')
def collect(channel: Optional[str], category: Optional[str]):
    """收集频道链接"""
    async def _collect():
        logger.info("开始收集频道链接")
        
        channel_manager = ChannelManager()
        
        # 获取要处理的频道
        if channel:
            channels = [channel_manager.get_channel_by_name(channel)]
            channels = [c for c in channels if c is not None]
        else:
            channels = channel_manager.get_channels(category=category, active_only=True)
        
        if not channels:
            logger.warning("没有找到要处理的频道")
            return
        
        logger.info(f"将处理 {len(channels)} 个频道")
        
        # 收集链接
        async with LinkCollector() as collector:
            results = {}
            for ch in channels:
                try:
                    links = await collector.collect_links_for_channel(ch)
                    saved_count = await collector.save_links_to_database(ch, links)
                    results[ch.name] = {"collected": len(links), "saved": saved_count}
                    logger.info(f"频道 {ch.name}: 收集 {len(links)} 个链接，保存 {saved_count} 个新链接")
                except Exception as e:
                    logger.error(f"处理频道 {ch.name} 失败: {e}")
                    results[ch.name] = {"collected": 0, "saved": 0}
        
        # 输出总结
        total_collected = sum(r["collected"] for r in results.values())
        total_saved = sum(r["saved"] for r in results.values())
        logger.info(f"收集完成: 总共收集 {total_collected} 个链接，保存 {total_saved} 个新链接")
    
    asyncio.run(_collect())


@cli.command()
@click.option('--channel', type=str, help='指定频道名称')
@click.option('--category', type=str, help='指定频道分类')
@click.option('--max-links', type=int, default=0, help='限制检测的链接数量')
def check(channel: Optional[str], category: Optional[str], max_links: int):
    """检测链接可用性"""
    async def _check():
        logger.info("开始检测链接可用性")
        
        from src.models import Link
        from src.models.base import SessionLocal
        
        db = SessionLocal()
        try:
            query = db.query(Link)
            
            # 根据参数筛选
            if channel:
                channel_manager = ChannelManager()
                ch = channel_manager.get_channel_by_name(channel)
                if ch:
                    query = query.filter(Link.channel_id == ch.id)
                else:
                    logger.error(f"未找到频道: {channel}")
                    return
            
            if category:
                from src.models import Channel
                channel_ids = db.query(Channel.id).filter(Channel.category == category)
                query = query.filter(Link.channel_id.in_(channel_ids))
            
            # 获取需要检测的链接
            links = query.limit(max_links if max_links > 0 else 1000).all()
            
            if not links:
                logger.warning("没有找到需要检测的链接")
                return
            
            logger.info(f"将检测 {len(links)} 个链接")
            
            # 执行检测
            async with LinkChecker() as checker:
                results = await checker.check_links_batch(links)
                
            logger.info(f"检测完成: 成功 {results['success']}, 失败 {results['failed']}, "
                       f"成功率 {results['success_rate']:.1f}%")
        
        finally:
            db.close()
    
    asyncio.run(_check())


@cli.command()
@click.option('--output', type=str, help='输出文件路径')
@click.option('--category', type=str, help='指定频道分类')
@click.option('--min-quality', type=int, default=0, help='最低质量评分')
@click.option('--format', type=click.Choice(['m3u', 'json']), default='m3u', help='输出格式')
def generate(output: Optional[str], category: Optional[str], min_quality: int, format: str):
    """生成播放列表"""
    logger.info(f"开始生成 {format.upper()} 播放列表")
    
    generator = M3UGenerator()
    
    try:
        if format == 'm3u':
            categories = [category] if category else None
            output_path = generator.generate_m3u_playlist(
                output_path=output,
                min_quality_score=min_quality,
                categories=categories
            )
        else:  # json
            output_path = generator.generate_json_playlist(output_path=output)
        
        logger.info(f"播放列表生成完成: {output_path}")
        
        # 显示统计信息
        stats = generator.get_playlist_stats()
        logger.info(f"统计信息: {stats['valid_channels']}/{stats['total_channels']} 个有效频道, "
                   f"{stats['valid_links']} 个有效链接")
    
    except Exception as e:
        logger.error(f"生成播放列表失败: {e}")


@cli.command()
@click.option('--output-dir', type=str, help='输出目录')
def generate_by_category(output_dir: Optional[str]):
    """按分类生成多个播放列表"""
    logger.info("开始按分类生成播放列表")
    
    generator = M3UGenerator()
    
    try:
        generated_files = generator.generate_by_category(output_dir)
        
        logger.info(f"生成完成，共生成 {len(generated_files)} 个文件:")
        for category, file_path in generated_files.items():
            logger.info(f"  {category}: {file_path}")
    
    except Exception as e:
        logger.error(f"按分类生成播放列表失败: {e}")


@cli.command()
def run():
    """执行完整的更新流程"""
    async def _run():
        logger.info("开始执行完整更新流程")
        
        try:
            # 1. 同步频道配置
            logger.info("步骤 1/4: 同步频道配置")
            channel_manager = ChannelManager()
            synced_count = channel_manager.sync_channels_to_database()
            logger.info(f"同步了 {synced_count} 个频道")
            
            # 2. 收集链接
            logger.info("步骤 2/4: 收集频道链接")
            async with LinkCollector() as collector:
                results = await collector.collect_all_channels()
            
            total_saved = sum(results.values())
            logger.info(f"收集完成，保存 {total_saved} 个新链接")
            
            # 3. 检测链接
            logger.info("步骤 3/4: 检测链接可用性")
            async with LinkChecker() as checker:
                check_results = await checker.check_all_links()
            
            logger.info(f"检测完成: 成功 {check_results['success']}, 失败 {check_results['failed']}")
            
            # 4. 生成播放列表
            logger.info("步骤 4/4: 生成播放列表")
            generator = M3UGenerator()
            
            # 生成主播放列表
            m3u_path = generator.generate_m3u_playlist()
            json_path = generator.generate_json_playlist()
            
            # 按分类生成
            category_files = generator.generate_by_category()
            
            logger.info("完整更新流程执行完成")
            logger.info(f"主播放列表: {m3u_path}")
            logger.info(f"JSON播放列表: {json_path}")
            logger.info(f"分类播放列表: {len(category_files)} 个文件")
            
            # 显示统计信息
            stats = generator.get_playlist_stats()
            logger.info(f"最终统计: {stats['valid_channels']}/{stats['total_channels']} 个有效频道")
        
        except Exception as e:
            logger.error(f"完整更新流程失败: {e}")
    
    asyncio.run(_run())


@cli.command()
def stats():
    """显示统计信息"""
    logger.info("获取系统统计信息")
    
    try:
        # 数据库信息
        db_info = get_database_info()
        logger.info("数据库统计:")
        for key, value in db_info.items():
            logger.info(f"  {key}: {value}")
        
        # 频道统计
        channel_manager = ChannelManager()
        channel_stats = channel_manager.get_channel_statistics()
        logger.info("频道统计:")
        for key, value in channel_stats.items():
            if key == "categories":
                logger.info(f"  {key}:")
                for cat, count in value.items():
                    logger.info(f"    {cat}: {count}")
            else:
                logger.info(f"  {key}: {value}")
        
        # 播放列表统计
        generator = M3UGenerator()
        playlist_stats = generator.get_playlist_stats()
        logger.info("播放列表统计:")
        for key, value in playlist_stats.items():
            if isinstance(value, dict):
                logger.info(f"  {key}:")
                for k, v in value.items():
                    logger.info(f"    {k}: {v}")
            else:
                logger.info(f"  {key}: {value}")
    
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")


@cli.command()
@click.option('--output', type=str, help='备份文件路径')
def backup(output: Optional[str]):
    """备份数据库"""
    logger.info("开始备份数据库")
    
    try:
        backup_path = backup_database(output)
        if backup_path:
            logger.info(f"数据库备份完成: {backup_path}")
        else:
            logger.error("数据库备份失败")
    
    except Exception as e:
        logger.error(f"备份数据库失败: {e}")


# 异步命令包装器
def async_command(f):
    """装饰器：将异步函数包装为同步CLI命令"""
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    wrapper.__name__ = f.__name__
    wrapper.__doc__ = f.__doc__
    return wrapper


if __name__ == "__main__":
    cli()