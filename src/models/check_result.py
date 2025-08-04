"""检测结果模型"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class CheckResult(Base):
    """检测结果表"""
    
    __tablename__ = "check_results"
    
    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, ForeignKey("links.id"), nullable=False, index=True)
    
    # 检测信息
    check_type = Column(String(50), nullable=False, comment="检测类型(ping/http/ffmpeg)")
    status = Column(String(20), nullable=False, comment="检测状态")
    
    # 网络指标
    response_time = Column(Float, comment="响应时间(秒)")
    download_speed = Column(Float, comment="下载速度(KB/s)")
    packet_loss = Column(Float, comment="丢包率(%)")
    
    # HTTP信息
    http_status = Column(Integer, comment="HTTP状态码")
    http_headers = Column(JSON, comment="HTTP响应头")
    content_length = Column(Integer, comment="内容长度")
    content_type = Column(String(100), comment="内容类型")
    
    # 流媒体信息 (FFmpeg检测)
    video_codec = Column(String(50), comment="视频编码")
    audio_codec = Column(String(50), comment="音频编码")
    resolution = Column(String(20), comment="分辨率")
    bitrate = Column(Integer, comment="比特率")
    fps = Column(Float, comment="帧率")
    duration = Column(Float, comment="持续时间(秒)")
    
    # 质量评估
    video_quality = Column(Integer, comment="视频质量(1-10)")
    audio_quality = Column(Integer, comment="音频质量(1-10)")
    stability_score = Column(Integer, comment="稳定性评分(1-10)")
    overall_score = Column(Integer, comment="综合评分(1-10)")
    
    # 错误信息
    error_code = Column(String(50), comment="错误代码")
    error_message = Column(Text, comment="错误信息")
    error_details = Column(JSON, comment="错误详情")
    
    # 地理位置和网络信息
    ip_address = Column(String(45), comment="IP地址")
    country = Column(String(50), comment="国家")
    region = Column(String(50), comment="地区")
    city = Column(String(50), comment="城市")
    isp = Column(String(100), comment="ISP")
    
    # 状态标识
    is_success = Column(Boolean, default=False, comment="是否成功")
    is_timeout = Column(Boolean, default=False, comment="是否超时")
    
    # 时间戳
    check_time = Column(DateTime, default=func.now(), comment="检测时间")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    
    # 关联关系
    link = relationship("Link", back_populates="check_results")
    
    def __repr__(self):
        return f"<CheckResult(id={self.id}, link_id={self.link_id}, status='{self.status}', check_time='{self.check_time}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "link_id": self.link_id,
            "check_type": self.check_type,
            "status": self.status,
            "response_time": self.response_time,
            "download_speed": self.download_speed,
            "packet_loss": self.packet_loss,
            "http_status": self.http_status,
            "http_headers": self.http_headers,
            "content_length": self.content_length,
            "content_type": self.content_type,
            "video_codec": self.video_codec,
            "audio_codec": self.audio_codec,
            "resolution": self.resolution,
            "bitrate": self.bitrate,
            "fps": self.fps,
            "duration": self.duration,
            "video_quality": self.video_quality,
            "audio_quality": self.audio_quality,
            "stability_score": self.stability_score,
            "overall_score": self.overall_score,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "error_details": self.error_details,
            "ip_address": self.ip_address,
            "country": self.country,
            "region": self.region,
            "city": self.city,
            "isp": self.isp,
            "is_success": self.is_success,
            "is_timeout": self.is_timeout,
            "check_time": self.check_time.isoformat() if self.check_time else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def create_success(cls, link_id: int, check_type: str, response_time: float, **kwargs):
        """创建成功的检测结果"""
        return cls(
            link_id=link_id,
            check_type=check_type,
            status="success",
            response_time=response_time,
            is_success=True,
            **kwargs
        )
    
    @classmethod
    def create_failure(cls, link_id: int, check_type: str, error_message: str, **kwargs):
        """创建失败的检测结果"""
        return cls(
            link_id=link_id,
            check_type=check_type,
            status="failed",
            error_message=error_message,
            is_success=False,
            **kwargs
        )