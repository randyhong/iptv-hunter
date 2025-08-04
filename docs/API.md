# IPTV Helper API 文档

## 概述

本文档描述了 IPTV Helper 的核心 API 接口，适用于二次开发和集成。

## 目录

- [服务类](#服务类)
- [数据模型](#数据模型)
- [工具函数](#工具函数)
- [配置管理](#配置管理)
- [使用示例](#使用示例)

## 服务类

### ChannelManager

频道管理服务，负责频道的增删改查和配置同步。

```python
from services import ChannelManager

manager = ChannelManager()
```

#### 方法

##### `sync_channels_to_database() -> int`
将 YAML 配置中的频道同步到数据库。

**返回**: 同步的频道数量

```python
count = manager.sync_channels_to_database()
print(f"同步了 {count} 个频道")
```

##### `get_channels(category=None, active_only=True) -> List[Channel]`
获取频道列表。

**参数**:
- `category`: 频道分类筛选
- `active_only`: 是否只返回活跃频道

```python
# 获取所有央视频道
cctv_channels = manager.get_channels(category="央视")

# 获取所有频道（包括未激活）
all_channels = manager.get_channels(active_only=False)
```

##### `create_channel(channel_data: Dict[str, Any]) -> Optional[Channel]`
创建新频道。

```python
channel_data = {
    "name": "新频道",
    "keywords": ["关键字1", "关键字2"],
    "category": "分类",
    "priority": 5
}
channel = manager.create_channel(channel_data)
```

### LinkCollector

链接收集服务，从各个数据源收集流媒体链接。

```python
from services import LinkCollector

async def collect_example():
    async with LinkCollector() as collector:
        # 收集单个频道的链接
        links = await collector.collect_links_for_channel(channel)
        
        # 保存到数据库
        saved_count = await collector.save_links_to_database(channel, links)
```

#### 方法

##### `collect_links_for_channel(channel: Channel) -> List[str]`
为指定频道收集链接。

**参数**:
- `channel`: 频道对象

**返回**: 链接列表

##### `collect_all_channels() -> Dict[str, int]`
收集所有活跃频道的链接。

**返回**: 频道名称到保存链接数的映射

### LinkChecker

链接检测服务，验证链接可用性和质量。

```python
from services import LinkChecker

async def check_example():
    async with LinkChecker() as checker:
        # 检测单个链接
        result = await checker.check_link(link)
        
        # 批量检测
        results = await checker.check_links_batch(links)
```

#### 方法

##### `check_link(link: Link) -> CheckResult`
检测单个链接。

**参数**:
- `link`: 链接对象

**返回**: 检测结果对象

##### `check_links_batch(links: List[Link]) -> Dict[str, Any]`
批量检测链接。

**返回**: 包含成功/失败统计的字典

### M3UGenerator

M3U 播放列表生成器。

```python
from services import M3UGenerator

generator = M3UGenerator()
```

#### 方法

##### `generate_m3u_playlist(output_path=None, **kwargs) -> str`
生成 M3U 播放列表。

**参数**:
- `output_path`: 输出文件路径
- `include_invalid`: 是否包含无效链接
- `min_quality_score`: 最低质量评分
- `categories`: 指定分类列表

**返回**: 输出文件路径

```python
# 生成高质量播放列表
path = generator.generate_m3u_playlist(
    min_quality_score=7,
    categories=["央视", "卫视"]
)
```

##### `generate_json_playlist(output_path=None) -> str`
生成 JSON 格式播放列表。

##### `get_playlist_stats() -> Dict[str, Any]`
获取播放列表统计信息。

## 数据模型

### Channel

频道模型，表示一个电视频道。

```python
from models import Channel

# 创建频道
channel = Channel(
    name="CCTV1",
    logo="http://example.com/logo.png",
    keywords=["CCTV1", "央视一套"],
    category="央视",
    priority=10
)
```

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键ID |
| `name` | str | 频道名称 |
| `logo` | str | Logo URL |
| `keywords` | List[str] | 搜索关键字 |
| `category` | str | 频道分类 |
| `priority` | int | 优先级 (1-10) |
| `total_links` | int | 总链接数 |
| `valid_links` | int | 有效链接数 |
| `is_active` | bool | 是否启用 |

#### 方法

##### `to_dict() -> Dict[str, Any]`
转换为字典格式。

##### `from_dict(data: Dict[str, Any]) -> Channel`
从字典创建实例（类方法）。

### Link

链接模型，表示一个流媒体链接。

```python
from models import Link

link = Link(
    channel_id=1,
    url="http://example.com/stream.m3u8",
    source="iptv-search.com"
)
```

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键ID |
| `channel_id` | int | 所属频道ID |
| `url` | str | 链接地址 |
| `source` | str | 来源网站 |
| `status` | LinkStatus | 链接状态 |
| `response_time` | float | 响应时间 |
| `quality_score` | int | 质量评分 |
| `is_valid` | bool | 是否有效 |

#### 方法

##### `success_rate -> float`
获取成功率属性。

##### `update_stats(success: bool)`
更新统计信息。

### CheckResult

检测结果模型。

```python
from models import CheckResult

# 创建成功结果
result = CheckResult.create_success(
    link_id=1,
    check_type="http",
    response_time=0.5
)

# 创建失败结果
result = CheckResult.create_failure(
    link_id=1,
    check_type="http",
    error_message="连接超时"
)
```

## 工具函数

### 验证工具

```python
from utils.validators import validate_url, validate_channel_data, validate_stream_url

# URL验证
is_valid = validate_url("http://example.com")

# 流媒体URL验证
result = validate_stream_url("http://example.com/stream.m3u8")
print(result["type"])  # "hls"

# 频道数据验证
result = validate_channel_data({
    "name": "测试频道",
    "keywords": ["测试"]
})
```

### 数据库工具

```python
from utils.database import init_database, backup_database, get_database_info

# 初始化数据库
init_database()

# 备份数据库
backup_path = backup_database("./backup.db")

# 获取数据库信息
info = get_database_info()
```

### 日志工具

```python
from utils.logger import setup_logger

# 设置日志
logger = setup_logger()
logger.info("日志消息")
```

## 配置管理

### Settings

全局配置管理。

```python
from config.settings import get_settings

settings = get_settings()
print(settings.database.url)
print(settings.crawler.timeout)
```

#### 配置结构

```python
class Settings:
    app_name: str
    debug: bool
    log_level: str
    
    database: DatabaseConfig
    crawler: CrawlerConfig
    checker: CheckerConfig
    m3u: M3UConfig
    source: SourceConfig
```

## 使用示例

### 完整工作流程

```python
import asyncio
from services import ChannelManager, LinkCollector, LinkChecker, M3UGenerator

async def main():
    # 1. 同步频道配置
    channel_manager = ChannelManager()
    channel_manager.sync_channels_to_database()
    
    # 2. 获取活跃频道
    channels = channel_manager.get_channels(active_only=True)
    
    # 3. 收集链接
    async with LinkCollector() as collector:
        for channel in channels:
            links = await collector.collect_links_for_channel(channel)
            await collector.save_links_to_database(channel, links)
    
    # 4. 检测链接
    async with LinkChecker() as checker:
        results = await checker.check_all_links()
    
    # 5. 生成播放列表
    generator = M3UGenerator()
    playlist_path = generator.generate_m3u_playlist()
    
    print(f"播放列表已生成: {playlist_path}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 自定义数据源

```python
from services.link_collector import LinkCollector

class CustomLinkCollector(LinkCollector):
    async def _collect_from_custom_source(self, keyword: str):
        """实现自定义数据源"""
        links = set()
        
        # 自定义收集逻辑
        # ...
        
        return links
    
    async def collect_links_for_channel(self, channel):
        """覆盖默认方法以包含自定义源"""
        all_links = set()
        
        # 调用父类方法获取默认源的链接
        default_links = await super().collect_links_for_channel(channel)
        all_links.update(default_links)
        
        # 添加自定义源的链接
        for keyword in channel.keywords:
            custom_links = await self._collect_from_custom_source(keyword)
            all_links.update(custom_links)
        
        return list(all_links)
```

### 自定义检测器

```python
from services.link_checker import LinkChecker

class CustomLinkChecker(LinkChecker):
    async def _custom_check(self, link):
        """自定义检测逻辑"""
        # 实现特殊的检测逻辑
        pass
    
    async def check_link(self, link):
        """扩展检测功能"""
        # 调用默认检测
        result = await super().check_link(link)
        
        # 添加自定义检测
        if result.is_success:
            custom_result = await self._custom_check(link)
            # 合并结果
        
        return result
```

### 事件监听

```python
from loguru import logger

class EventHandler:
    def on_channel_synced(self, channel):
        logger.info(f"频道已同步: {channel.name}")
    
    def on_links_collected(self, channel, count):
        logger.info(f"频道 {channel.name} 收集到 {count} 个链接")
    
    def on_link_checked(self, link, result):
        if result.is_success:
            logger.info(f"链接检测成功: {link.url[:50]}")
        else:
            logger.warning(f"链接检测失败: {link.url[:50]} - {result.error_message}")
```

### 扩展M3U生成器

```python
from services.m3u_generator import M3UGenerator

class CustomM3UGenerator(M3UGenerator):
    def _build_extinf_line(self, channel, link):
        """自定义EXTINF行格式"""
        extinf = f"#EXTINF:-1"
        
        # 添加自定义属性
        if channel.logo:
            extinf += f' tvg-logo="{channel.logo}"'
        
        if channel.category:
            extinf += f' group-title="{channel.category}"'
        
        # 添加质量信息
        if link.quality_score:
            extinf += f' tvg-id="q{link.quality_score}"'
        
        extinf += f",{channel.name}"
        
        return extinf
```

## 错误处理

### 异常类型

- `DatabaseError`: 数据库操作错误
- `NetworkError`: 网络连接错误
- `ValidationError`: 数据验证错误
- `ConfigurationError`: 配置错误

### 错误处理示例

```python
from loguru import logger

try:
    async with LinkChecker() as checker:
        result = await checker.check_link(link)
except asyncio.TimeoutError:
    logger.error("检测超时")
except Exception as e:
    logger.error(f"检测失败: {e}")
```