"""数据验证工具"""

import re
from typing import Dict, Any, List
from urllib.parse import urlparse
from loguru import logger


def validate_url(url: str) -> bool:
    """验证URL格式"""
    if not url or not isinstance(url, str):
        return False
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_stream_url(url: str) -> Dict[str, Any]:
    """验证流媒体URL"""
    result = {
        "valid": False,
        "protocol": None,
        "type": None,
        "errors": []
    }
    
    if not validate_url(url):
        result["errors"].append("无效的URL格式")
        return result
    
    try:
        parsed = urlparse(url)
        protocol = parsed.scheme.lower()
        result["protocol"] = protocol
        
        # 检查支持的协议
        if protocol not in ["http", "https", "rtmp", "rtsp"]:
            result["errors"].append(f"不支持的协议: {protocol}")
            return result
        
        # 检查流媒体类型
        url_lower = url.lower()
        if ".m3u8" in url_lower:
            result["type"] = "hls"
        elif ".flv" in url_lower:
            result["type"] = "flv"
        elif ".mp4" in url_lower:
            result["type"] = "mp4"
        elif ".ts" in url_lower:
            result["type"] = "ts"
        elif protocol in ["rtmp", "rtsp"]:
            result["type"] = protocol
        else:
            result["type"] = "unknown"
        
        result["valid"] = True
        
    except Exception as e:
        result["errors"].append(f"URL解析错误: {str(e)}")
    
    return result


def validate_channel_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """验证频道数据"""
    result = {
        "valid": False,
        "errors": [],
        "warnings": []
    }
    
    # 必填字段检查
    required_fields = ["name"]
    for field in required_fields:
        if field not in data or not data[field]:
            result["errors"].append(f"缺少必填字段: {field}")
    
    # 频道名称检查
    if "name" in data:
        name = data["name"]
        if not isinstance(name, str) or len(name.strip()) == 0:
            result["errors"].append("频道名称不能为空")
        elif len(name) > 100:
            result["errors"].append("频道名称过长（最大100字符）")
    
    # Logo URL检查
    if "logo" in data and data["logo"]:
        if not validate_url(data["logo"]):
            result["warnings"].append("Logo URL格式无效")
    
    # 关键字检查
    if "keywords" in data:
        keywords = data["keywords"]
        if not isinstance(keywords, list):
            result["errors"].append("关键字必须是列表格式")
        elif len(keywords) == 0:
            result["warnings"].append("建议添加搜索关键字")
        else:
            for keyword in keywords:
                if not isinstance(keyword, str) or len(keyword.strip()) == 0:
                    result["errors"].append("关键字不能为空字符串")
    
    # 分类检查
    if "category" in data and data["category"]:
        category = data["category"]
        if not isinstance(category, str):
            result["errors"].append("分类必须是字符串")
        elif len(category) > 50:
            result["errors"].append("分类名称过长（最大50字符）")
    
    # 优先级检查
    if "priority" in data:
        priority = data["priority"]
        if not isinstance(priority, int) or priority < 1 or priority > 10:
            result["errors"].append("优先级必须是1-10之间的整数")
    
    result["valid"] = len(result["errors"]) == 0
    return result


def validate_m3u_content(content: str) -> Dict[str, Any]:
    """验证M3U内容格式"""
    result = {
        "valid": False,
        "channels": 0,
        "errors": [],
        "warnings": []
    }
    
    if not content or not isinstance(content, str):
        result["errors"].append("M3U内容不能为空")
        return result
    
    lines = content.strip().split('\n')
    
    # 检查M3U头部
    if not lines or not lines[0].strip().startswith('#EXTM3U'):
        result["errors"].append("缺少M3U文件头 #EXTM3U")
        return result
    
    # 解析频道
    channel_count = 0
    i = 1
    
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('#EXTINF:'):
            # 找到频道信息行
            if i + 1 < len(lines):
                url_line = lines[i + 1].strip()
                if url_line and not url_line.startswith('#'):
                    if validate_url(url_line):
                        channel_count += 1
                    else:
                        result["warnings"].append(f"无效的URL: {url_line[:50]}...")
                else:
                    result["warnings"].append(f"#EXTINF后缺少URL: 行{i+1}")
                i += 2
            else:
                result["warnings"].append("文件末尾的#EXTINF缺少对应URL")
                i += 1
        else:
            i += 1
    
    result["channels"] = channel_count
    result["valid"] = len(result["errors"]) == 0
    
    if channel_count == 0:
        result["warnings"].append("没有找到有效的频道")
    
    return result


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除非法字符"""
    # 移除或替换非法字符
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        filename = filename.replace(char, '_')
    
    # 移除连续的空格和下划线
    filename = re.sub(r'[_\s]+', '_', filename)
    
    # 移除开头和结尾的空格、点号、下划线
    filename = filename.strip(' ._')
    
    # 限制长度
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename


def validate_config_file(config_path: str) -> Dict[str, Any]:
    """验证配置文件"""
    result = {
        "valid": False,
        "errors": [],
        "warnings": []
    }
    
    try:
        import yaml
        import os
        
        if not os.path.exists(config_path):
            result["errors"].append(f"配置文件不存在: {config_path}")
            return result
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not isinstance(config, dict):
            result["errors"].append("配置文件格式无效")
            return result
        
        # 检查频道配置
        if "channels" in config:
            channels = config["channels"]
            if not isinstance(channels, list):
                result["errors"].append("频道配置必须是列表格式")
            else:
                for i, channel in enumerate(channels):
                    channel_result = validate_channel_data(channel)
                    if not channel_result["valid"]:
                        result["errors"].extend([
                            f"频道{i+1}: {error}" for error in channel_result["errors"]
                        ])
                    result["warnings"].extend([
                        f"频道{i+1}: {warning}" for warning in channel_result["warnings"]
                    ])
        else:
            result["warnings"].append("配置文件中没有频道配置")
        
        result["valid"] = len(result["errors"]) == 0
        
    except yaml.YAMLError as e:
        result["errors"].append(f"YAML解析错误: {str(e)}")
    except Exception as e:
        result["errors"].append(f"配置文件验证失败: {str(e)}")
    
    return result