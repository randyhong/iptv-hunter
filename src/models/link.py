"""链接模型"""

from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class LinkStatus(str, Enum):
    """链接状态枚举"""
    UNKNOWN = "unknown"          # 未知
    ACTIVE = "active"            # 活跃
    INACTIVE = "inactive"        # 不活跃
    ERROR = "error"              # 错误
    TIMEOUT = "timeout"          # 超时
    FORBIDDEN = "forbidden"      # 禁止访问


class Link(Base):
    """链接表"""
    
    __tablename__ = "links"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)
    url = Column(String(1000), nullable=False, index=True, comment="链接地址")
    source = Column(String(100), comment="来源网站")
    
    # 检测结果
    status = Column(String(20), default=LinkStatus.UNKNOWN, comment="链接状态")
    response_time = Column(Float, comment="响应时间(秒)")
    http_status = Column(Integer, comment="HTTP状态码")
    content_type = Column(String(100), comment="内容类型")
    
    # 流媒体信息
    resolution = Column(String(20), comment="分辨率")
    codec = Column(String(50), comment="编码格式")
    bitrate = Column(Integer, comment="比特率")
    fps = Column(Float, comment="帧率")
    
    # 质量评分 (0-100)
    quality_score = Column(Integer, default=0, comment="质量评分")
    
    # 统计信息
    check_count = Column(Integer, default=0, comment="检测次数")
    success_count = Column(Integer, default=0, comment="成功次数")
    fail_count = Column(Integer, default=0, comment="失败次数")
    
    # 状态
    is_valid = Column(Boolean, default=False, comment="是否有效")
    is_favorite = Column(Boolean, default=False, comment="是否收藏")
    
    # 时间戳
    first_found = Column(DateTime, default=func.now(), comment="首次发现时间")
    last_checked = Column(DateTime, comment="最后检测时间")
    last_success = Column(DateTime, comment="最后成功时间")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 备注
    notes = Column(Text, comment="备注信息")
    error_message = Column(Text, comment="错误信息")
    
    # 关联关系
    channel = relationship("Channel", back_populates="links")
    check_results = relationship("CheckResult", back_populates="link", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Link(id={self.id}, url='{self.url[:50]}...', status='{self.status}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "channel_id": self.channel_id,
            "url": self.url,
            "source": self.source,
            "status": self.status,
            "response_time": self.response_time,
            "http_status": self.http_status,
            "content_type": self.content_type,
            "resolution": self.resolution,
            "codec": self.codec,
            "bitrate": self.bitrate,
            "fps": self.fps,
            "quality_score": self.quality_score,
            "check_count": self.check_count,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "is_valid": self.is_valid,
            "is_favorite": self.is_favorite,
            "first_found": self.first_found.isoformat() if self.first_found else None,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "notes": self.notes,
            "error_message": self.error_message,
        }
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.check_count == 0:
            return 0.0
        return (self.success_count / self.check_count) * 100
    
    def update_stats(self, success: bool):
        """更新统计信息"""
        self.check_count += 1
        if success:
            self.success_count += 1
            self.last_success = func.now()
        else:
            self.fail_count += 1
        self.last_checked = func.now()