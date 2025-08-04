"""M3U播放列表生成器"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session

from src.models import Channel, Link, LinkStatus
from src.models.base import SessionLocal
from config.settings import get_settings


class M3UGenerator:
    """M3U播放列表生成器"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def generate_m3u_playlist(self, 
                             output_path: Optional[str] = None,
                             include_invalid: bool = False,
                             min_quality_score: int = 0,
                             categories: Optional[List[str]] = None) -> str:
        """生成M3U播放列表"""
        
        if output_path is None:
            output_path = self.settings.m3u.output_path
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        db = SessionLocal()
        try:
            # 获取频道和链接数据
            channels_data = self._get_channels_with_links(
                db, include_invalid, min_quality_score, categories
            )
            
            # 生成M3U内容
            m3u_content = self._build_m3u_content(channels_data)
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            
            logger.info(f"M3U播放列表已生成: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"生成M3U播放列表失败: {e}")
            raise
        finally:
            db.close()
    
    def _get_channels_with_links(self, 
                                db: Session,
                                include_invalid: bool,
                                min_quality_score: int,
                                categories: Optional[List[str]]) -> List[Dict[str, Any]]:
        """获取频道和链接数据"""
        
        # 查询频道
        channel_query = db.query(Channel).filter(Channel.is_active == True)
        
        if categories:
            channel_query = channel_query.filter(Channel.category.in_(categories))
        
        if self.settings.m3u.sort_by_category:
            channels = channel_query.order_by(Channel.category, Channel.priority.desc(), Channel.name).all()
        else:
            channels = channel_query.order_by(Channel.priority.desc(), Channel.name).all()
        
        channels_data = []
        
        for channel in channels:
            # 查询有效链接
            link_query = db.query(Link).filter(Link.channel_id == channel.id)
            
            if not include_invalid:
                link_query = link_query.filter(Link.is_valid == True)
            
            if min_quality_score > 0:
                link_query = link_query.filter(Link.quality_score >= min_quality_score)
            
            # 按质量评分排序，取最佳链接
            links = link_query.order_by(
                Link.quality_score.desc(),
                Link.response_time.asc(),
                Link.last_success.desc()
            ).all()
            
            if links:
                # 取第一个（最佳）链接
                best_link = links[0]
                channels_data.append({
                    'channel': channel,
                    'link': best_link,
                    'alternatives': links[1:5]  # 保留备用链接
                })
        
        return channels_data
    
    def _build_m3u_content(self, channels_data: List[Dict[str, Any]]) -> str:
        """构建M3U内容"""
        lines = ["#EXTM3U"]
        
        # 添加播放列表信息
        lines.append(f"#PLAYLIST:IPTV Hunter - Generated at {datetime.now().isoformat()}")
        
        current_category = None
        
        for data in channels_data:
            channel = data['channel']
            link = data['link']
            
            # 添加分类注释
            if self.settings.m3u.include_group and channel.category != current_category:
                current_category = channel.category
                lines.append(f"")
                lines.append(f"# === {current_category} ===")
            
            # 构建EXTINF行
            extinf_parts = []
            
            # 时长（默认-1表示直播）
            extinf_parts.append("#EXTINF:-1")
            
            # 频道信息
            channel_info = []
            
            if self.settings.m3u.include_logo and channel.logo:
                channel_info.append(f'tvg-logo="{channel.logo}"')
            
            if self.settings.m3u.include_group and channel.category:
                channel_info.append(f'group-title="{channel.category}"')
            
            # 添加额外信息
            if link.resolution:
                channel_info.append(f'tvg-name="{channel.name} ({link.resolution})"')
            else:
                channel_info.append(f'tvg-name="{channel.name}"')
            
            # 质量信息
            if link.quality_score and link.quality_score > 0:
                channel_info.append(f'tvg-id="quality_{link.quality_score}"')
            
            if channel_info:
                extinf_parts.append(" ".join(channel_info))
            
            # 频道名称
            channel_name = channel.name
            if link.resolution:
                channel_name += f" ({link.resolution})"
            if link.quality_score and link.quality_score > 0:
                channel_name += f" [Q{link.quality_score}]"
            
            extinf_parts.append(f",{channel_name}")
            
            lines.append("".join(extinf_parts))
            lines.append(link.url)
            
            # 添加备用链接（注释形式）
            alternatives = data.get('alternatives', [])
            if alternatives:
                lines.append(f"# Alternatives for {channel.name}:")
                for i, alt_link in enumerate(alternatives[:3], 1):  # 最多3个备用
                    quality_info = f" [Q{alt_link.quality_score}]" if alt_link.quality_score else ""
                    lines.append(f"# Alt{i}{quality_info}: {alt_link.url}")
        
        return "\n".join(lines)
    
    def generate_json_playlist(self, output_path: Optional[str] = None) -> str:
        """生成JSON格式的播放列表"""
        import json
        
        if output_path is None:
            output_path = self.settings.m3u.output_path.replace('.m3u', '.json')
        
        db = SessionLocal()
        try:
            channels_data = self._get_channels_with_links(db, False, 0, None)
            
            playlist = {
                "name": "IPTV Hunter Playlist",
                "generated_at": datetime.now().isoformat(),
                "channels": []
            }
            
            for data in channels_data:
                channel = data['channel']
                link = data['link']
                
                channel_info = {
                    "id": channel.id,
                    "name": channel.name,
                    "logo": channel.logo,
                    "category": channel.category,
                    "priority": channel.priority,
                    "url": link.url,
                    "quality_score": link.quality_score,
                    "resolution": link.resolution,
                    "response_time": link.response_time,
                    "last_checked": link.last_checked.isoformat() if link.last_checked else None,
                    "alternatives": [
                        {
                            "url": alt.url,
                            "quality_score": alt.quality_score,
                            "resolution": alt.resolution,
                            "response_time": alt.response_time
                        }
                        for alt in data.get('alternatives', [])
                    ]
                }
                
                playlist["channels"].append(channel_info)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(playlist, f, ensure_ascii=False, indent=2)
            
            logger.info(f"JSON播放列表已生成: {output_path}")
            return output_path
            
        finally:
            db.close()
    
    def generate_by_category(self, base_output_dir: Optional[str] = None) -> Dict[str, str]:
        """按分类生成多个M3U文件"""
        
        if base_output_dir is None:
            base_output_dir = os.path.dirname(self.settings.m3u.output_path)
        
        db = SessionLocal()
        try:
            # 获取所有分类
            categories = db.query(Channel.category).filter(
                Channel.category.isnot(None),
                Channel.is_active == True
            ).distinct().all()
            
            generated_files = {}
            
            for (category,) in categories:
                if category:
                    # 生成分类专用的M3U文件
                    output_path = os.path.join(base_output_dir, f"{category}.m3u")
                    self.generate_m3u_playlist(
                        output_path=output_path,
                        categories=[category]
                    )
                    generated_files[category] = output_path
            
            # 生成总的播放列表
            all_output_path = os.path.join(base_output_dir, "all_channels.m3u")
            self.generate_m3u_playlist(output_path=all_output_path)
            generated_files["all"] = all_output_path
            
            return generated_files
            
        finally:
            db.close()
    
    def get_playlist_stats(self) -> Dict[str, Any]:
        """获取播放列表统计信息"""
        db = SessionLocal()
        try:
            stats = {
                "total_channels": 0,
                "valid_channels": 0,
                "categories": {},
                "quality_distribution": {},
                "resolution_distribution": {},
                "total_links": 0,
                "valid_links": 0,
            }
            
            # 频道统计
            channels = db.query(Channel).filter(Channel.is_active == True).all()
            stats["total_channels"] = len(channels)
            
            for channel in channels:
                # 分类统计
                if channel.category:
                    if channel.category not in stats["categories"]:
                        stats["categories"][channel.category] = 0
                    stats["categories"][channel.category] += 1
                
                # 有效链接统计
                valid_links = db.query(Link).filter(
                    Link.channel_id == channel.id,
                    Link.is_valid == True
                ).all()
                
                if valid_links:
                    stats["valid_channels"] += 1
                    stats["valid_links"] += len(valid_links)
                    
                    # 质量分布
                    for link in valid_links:
                        if link.quality_score:
                            score_range = f"{link.quality_score//2*2}-{link.quality_score//2*2+1}"
                            if score_range not in stats["quality_distribution"]:
                                stats["quality_distribution"][score_range] = 0
                            stats["quality_distribution"][score_range] += 1
                        
                        # 分辨率分布
                        if link.resolution:
                            if link.resolution not in stats["resolution_distribution"]:
                                stats["resolution_distribution"][link.resolution] = 0
                            stats["resolution_distribution"][link.resolution] += 1
                
                # 总链接数
                total_links = db.query(Link).filter(Link.channel_id == channel.id).count()
                stats["total_links"] += total_links
            
            return stats
            
        finally:
            db.close()