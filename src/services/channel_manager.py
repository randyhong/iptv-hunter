"""频道管理服务"""

import yaml
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from loguru import logger

from src.models import Channel
from src.models.base import SessionLocal
from config.settings import get_settings


class ChannelManager:
    """频道管理器"""
    
    def __init__(self):
        self.settings = get_settings()
        
    def load_channels_from_yaml(self, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """从YAML文件加载频道配置"""
        if file_path is None:
            file_path = self.settings.channels_file
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data.get('channels', [])
        except FileNotFoundError:
            logger.error(f"频道配置文件不存在: {file_path}")
            return []
        except yaml.YAMLError as e:
            logger.error(f"解析YAML文件失败: {e}")
            return []
    
    def save_channels_to_yaml(self, channels: List[Dict[str, Any]], file_path: Optional[str] = None):
        """保存频道配置到YAML文件"""
        if file_path is None:
            file_path = self.settings.channels_file
            
        data = {
            'channels': channels,
            'settings': {
                'max_links_per_channel': 10,
                'check_interval': 6,
                'link_expire_hours': 24,
                'auto_update': True
            }
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"频道配置已保存到: {file_path}")
        except Exception as e:
            logger.error(f"保存YAML文件失败: {e}")
    
    def sync_channels_to_database(self) -> int:
        """同步频道配置到数据库"""
        channels_data = self.load_channels_from_yaml()
        if not channels_data:
            logger.warning("没有找到频道配置数据")
            return 0
        
        db = SessionLocal()
        try:
            synced_count = 0
            for channel_data in channels_data:
                # 检查频道是否已存在
                existing_channel = db.query(Channel).filter(
                    Channel.name == channel_data.get('name')
                ).first()
                
                if existing_channel:
                    # 更新现有频道
                    existing_channel.logo = channel_data.get('logo')
                    existing_channel.keywords = channel_data.get('keywords', [])
                    existing_channel.category = channel_data.get('category')
                    existing_channel.priority = channel_data.get('priority', 5)
                    logger.info(f"更新频道: {existing_channel.name}")
                else:
                    # 创建新频道
                    new_channel = Channel.from_dict(channel_data)
                    db.add(new_channel)
                    logger.info(f"新增频道: {new_channel.name}")
                    
                synced_count += 1
            
            db.commit()
            logger.info(f"成功同步 {synced_count} 个频道到数据库")
            return synced_count
            
        except Exception as e:
            db.rollback()
            logger.error(f"同步频道到数据库失败: {e}")
            return 0
        finally:
            db.close()
    
    def get_channels(self, category: Optional[str] = None, active_only: bool = True) -> List[Channel]:
        """获取频道列表"""
        db = SessionLocal()
        try:
            query = db.query(Channel)
            
            if active_only:
                query = query.filter(Channel.is_active == True)
            
            if category:
                query = query.filter(Channel.category == category)
            
            return query.order_by(Channel.priority.desc(), Channel.name).all()
            
        finally:
            db.close()
    
    def get_channel_by_id(self, channel_id: int) -> Optional[Channel]:
        """根据ID获取频道"""
        db = SessionLocal()
        try:
            return db.query(Channel).filter(Channel.id == channel_id).first()
        finally:
            db.close()
    
    def get_channel_by_name(self, name: str) -> Optional[Channel]:
        """根据名称获取频道"""
        db = SessionLocal()
        try:
            return db.query(Channel).filter(Channel.name == name).first()
        finally:
            db.close()
    
    def create_channel(self, channel_data: Dict[str, Any]) -> Optional[Channel]:
        """创建新频道"""
        db = SessionLocal()
        try:
            # 检查是否已存在同名频道
            existing = db.query(Channel).filter(Channel.name == channel_data.get('name')).first()
            if existing:
                logger.warning(f"频道 '{channel_data.get('name')}' 已存在")
                return None
            
            channel = Channel.from_dict(channel_data)
            db.add(channel)
            db.commit()
            db.refresh(channel)
            
            logger.info(f"成功创建频道: {channel.name}")
            return channel
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建频道失败: {e}")
            return None
        finally:
            db.close()
    
    def update_channel(self, channel_id: int, update_data: Dict[str, Any]) -> bool:
        """更新频道信息"""
        db = SessionLocal()
        try:
            channel = db.query(Channel).filter(Channel.id == channel_id).first()
            if not channel:
                logger.warning(f"频道 ID {channel_id} 不存在")
                return False
            
            # 更新字段
            for key, value in update_data.items():
                if hasattr(channel, key):
                    setattr(channel, key, value)
            
            db.commit()
            logger.info(f"成功更新频道: {channel.name}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"更新频道失败: {e}")
            return False
        finally:
            db.close()
    
    def delete_channel(self, channel_id: int) -> bool:
        """删除频道"""
        db = SessionLocal()
        try:
            channel = db.query(Channel).filter(Channel.id == channel_id).first()
            if not channel:
                logger.warning(f"频道 ID {channel_id} 不存在")
                return False
            
            channel_name = channel.name
            db.delete(channel)
            db.commit()
            
            logger.info(f"成功删除频道: {channel_name}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"删除频道失败: {e}")
            return False
        finally:
            db.close()
    
    def get_channel_statistics(self) -> Dict[str, Any]:
        """获取频道统计信息"""
        db = SessionLocal()
        try:
            stats = {
                'total_channels': db.query(Channel).count(),
                'active_channels': db.query(Channel).filter(Channel.is_active == True).count(),
                'categories': {},
                'total_links': 0,
                'valid_links': 0,
            }
            
            # 按分类统计
            categories = db.query(Channel.category).distinct().all()
            for (category,) in categories:
                if category:
                    count = db.query(Channel).filter(Channel.category == category).count()
                    stats['categories'][category] = count
            
            # 链接统计
            channels = db.query(Channel).all()
            for channel in channels:
                stats['total_links'] += channel.total_links or 0
                stats['valid_links'] += channel.valid_links or 0
            
            return stats
            
        finally:
            db.close()
    
    def update_channel_stats(self, channel_id: int):
        """更新频道统计信息"""
        db = SessionLocal()
        try:
            from src.models import Link
            
            channel = db.query(Channel).filter(Channel.id == channel_id).first()
            if not channel:
                return
            
            # 统计链接数量
            total_links = db.query(Link).filter(Link.channel_id == channel_id).count()
            valid_links = db.query(Link).filter(
                Link.channel_id == channel_id,
                Link.is_valid == True
            ).count()
            
            channel.total_links = total_links
            channel.valid_links = valid_links
            
            db.commit()
            logger.debug(f"更新频道 {channel.name} 统计信息: 总数={total_links}, 有效={valid_links}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"更新频道统计失败: {e}")
        finally:
            db.close()