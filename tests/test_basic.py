"""基础测试用例"""

import pytest
import os
import sys

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.validators import validate_url, validate_channel_data, validate_stream_url


class TestValidators:
    """测试验证函数"""
    
    def test_validate_url(self):
        """测试URL验证"""
        # 有效URL
        assert validate_url("http://example.com") == True
        assert validate_url("https://example.com") == True
        assert validate_url("https://example.com/path") == True
        
        # 无效URL
        assert validate_url("") == False
        assert validate_url("not_a_url") == False
        assert validate_url("ftp://example.com") == True  # 技术上有效，但不是http(s)
        assert validate_url(None) == False
    
    def test_validate_stream_url(self):
        """测试流媒体URL验证"""
        # HLS流
        result = validate_stream_url("http://example.com/stream.m3u8")
        assert result["valid"] == True
        assert result["type"] == "hls"
        
        # RTMP流
        result = validate_stream_url("rtmp://example.com/live/stream")
        assert result["valid"] == True
        assert result["type"] == "rtmp"
        
        # 无效URL
        result = validate_stream_url("invalid_url")
        assert result["valid"] == False
        assert len(result["errors"]) > 0
    
    def test_validate_channel_data(self):
        """测试频道数据验证"""
        # 有效数据
        valid_data = {
            "name": "测试频道",
            "logo": "http://example.com/logo.png",
            "keywords": ["测试", "频道"],
            "category": "测试分类",
            "priority": 5
        }
        result = validate_channel_data(valid_data)
        assert result["valid"] == True
        assert len(result["errors"]) == 0
        
        # 缺少必填字段
        invalid_data = {
            "logo": "http://example.com/logo.png"
        }
        result = validate_channel_data(invalid_data)
        assert result["valid"] == False
        assert len(result["errors"]) > 0
        
        # 无效优先级
        invalid_priority = {
            "name": "测试频道",
            "priority": 15  # 超出范围
        }
        result = validate_channel_data(invalid_priority)
        assert result["valid"] == False


class TestChannelManager:
    """测试频道管理器"""
    
    @pytest.fixture
    def channel_manager(self):
        """创建频道管理器实例"""
        from services.channel_manager import ChannelManager
        return ChannelManager()
    
    def test_load_channels_from_yaml(self, channel_manager):
        """测试从YAML加载频道"""
        # 测试默认配置文件
        channels = channel_manager.load_channels_from_yaml()
        assert isinstance(channels, list)
        
        # 如果配置文件存在，应该有频道数据
        if channels:
            for channel in channels:
                assert "name" in channel
                assert isinstance(channel["name"], str)


if __name__ == "__main__":
    pytest.main([__file__])