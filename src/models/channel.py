"""频道模型"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Channel(Base):
    """频道表"""
    
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True, comment="频道名称")
    logo = Column(String(500), comment="频道Logo URL")
    keywords = Column(JSON, comment="搜索关键字列表")
    category = Column(String(50), index=True, comment="频道分类")
    priority = Column(Integer, default=5, comment="优先级(1-10)")
    description = Column(Text, comment="频道描述")
    
    # 统计信息
    total_links = Column(Integer, default=0, comment="总链接数")
    valid_links = Column(Integer, default=0, comment="有效链接数")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    last_updated = Column(DateTime, default=func.now(), comment="最后更新时间")
    last_checked = Column(DateTime, comment="最后检测时间")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    links = relationship("Link", back_populates="channel", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Channel(id={self.id}, name='{self.name}', category='{self.category}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "logo": self.logo,
            "keywords": self.keywords,
            "category": self.category,
            "priority": self.priority,
            "description": self.description,
            "total_links": self.total_links,
            "valid_links": self.valid_links,
            "is_active": self.is_active,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        return cls(
            name=data.get("name"),
            logo=data.get("logo"),
            keywords=data.get("keywords", []),
            category=data.get("category"),
            priority=data.get("priority", 5),
            description=data.get("description"),
            is_active=data.get("is_active", True),
        )