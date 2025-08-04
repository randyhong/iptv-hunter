# IPTV Helper 使用指南

## 目录

- [快速开始](#快速开始)
- [命令行界面](#命令行界面)
- [配置说明](#配置说明)
- [工作流程](#工作流程)
- [高级用法](#高级用法)
- [故障排除](#故障排除)

## 快速开始

### 1. 安装项目

```bash
# 克隆项目
git clone <your-repo-url>
cd iptv-helper

# 运行安装脚本
chmod +x scripts/install.sh
./scripts/install.sh
```

### 2. 配置频道

编辑 `config/channels.yaml` 文件，添加您想要监控的频道：

```yaml
channels:
  - name: "CCTV1"
    logo: "https://live.fanmingming.com/tv/CCTV1.png"
    keywords: ["CCTV1", "央视一套", "中央一套"]
    category: "央视"
    priority: 10
```

### 3. 运行程序

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行完整流程（推荐）
python src/main.py run

# 或者分步执行
python src/main.py sync-channels  # 同步频道配置
python src/main.py collect        # 收集链接
python src/main.py check          # 检测链接
python src/main.py generate       # 生成播放列表
```

## 命令行界面

### 主要命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `run` | 执行完整的更新流程 | `python src/main.py run` |
| `sync-channels` | 同步频道配置到数据库 | `python src/main.py sync-channels` |
| `collect` | 收集频道链接 | `python src/main.py collect` |
| `check` | 检测链接可用性 | `python src/main.py check` |
| `generate` | 生成播放列表 | `python src/main.py generate` |
| `stats` | 显示统计信息 | `python src/main.py stats` |
| `backup` | 备份数据库 | `python src/main.py backup` |

### 命令选项

#### collect 命令
```bash
# 收集指定频道的链接
python src/main.py collect --channel "CCTV1"

# 收集指定分类的所有频道
python src/main.py collect --category "央视"
```

#### check 命令
```bash
# 检测指定频道的链接
python src/main.py check --channel "CCTV1"

# 限制检测数量
python src/main.py check --max-links 100
```

#### generate 命令
```bash
# 生成到指定文件
python src/main.py generate --output ./my_playlist.m3u

# 生成指定分类
python src/main.py generate --category "央视"

# 设置最低质量评分
python src/main.py generate --min-quality 5

# 生成JSON格式
python src/main.py generate --format json
```

### 全局选项

```bash
# 启用调试模式
python src/main.py --debug <command>

# 指定配置文件
python src/main.py --config /path/to/config.yaml <command>
```

## 配置说明

### 环境变量配置 (.env)

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

主要配置项：

- `DEBUG`: 调试模式 (true/false)
- `LOG_LEVEL`: 日志级别 (DEBUG/INFO/WARNING/ERROR)
- `DATABASE__URL`: 数据库连接字符串
- `CRAWLER__TIMEOUT`: 爬虫超时时间（秒）
- `CHECKER__CONCURRENT_CHECKS`: 并发检测数量

### 频道配置 (config/channels.yaml)

```yaml
channels:
  - name: "频道名称"              # 必填：频道显示名称
    logo: "logo_url"             # 可选：频道Logo URL
    keywords: ["关键字1", "关键字2"]  # 必填：搜索关键字列表
    category: "分类名称"          # 可选：频道分类
    priority: 5                  # 可选：优先级 (1-10)
    description: "频道描述"       # 可选：频道描述

settings:
  max_links_per_channel: 10      # 每个频道最大链接数
  check_interval: 6              # 检测间隔（小时）
  link_expire_hours: 24          # 链接过期时间（小时）
  auto_update: true              # 是否启用自动更新
```

## 工作流程

### 1. 频道同步

从 YAML 配置文件读取频道信息并同步到数据库：

```bash
python src/main.py sync-channels
```

### 2. 链接收集

基于频道关键字从配置的数据源收集流媒体链接：

- 支持的数据源：
  - iptv-search.com
  - tonkiang.us
  - 可扩展更多源

```bash
python src/main.py collect
```

### 3. 链接检测

对收集到的链接进行多层检测：

- **HTTP检测**：检查链接可访问性
- **FFmpeg检测**：分析流媒体内容质量
- **质量评分**：基于分辨率、码率、稳定性等指标

```bash
python src/main.py check
```

### 4. 播放列表生成

基于有效链接生成 M3U 播放列表：

- 自动选择最佳链接
- 支持分类和排序
- 包含备用链接信息

```bash
python src/main.py generate
```

## 高级用法

### 1. 定时任务

使用 cron 设置定时更新：

```bash
# 每6小时运行一次完整更新
0 */6 * * * cd /path/to/iptv-helper && source venv/bin/activate && python src/main.py run
```

### 2. Docker 部署

```bash
# 构建镜像
docker build -t iptv-helper .

# 运行容器
docker-compose up -d
```

### 3. 按分类生成

```bash
# 生成分类专用播放列表
python src/main.py generate-by-category --output-dir ./output/categories/
```

### 4. 数据库备份

```bash
# 手动备份
python src/main.py backup --output ./backups/backup_$(date +%Y%m%d).db

# 定时备份
0 2 * * * cd /path/to/iptv-helper && python src/main.py backup
```

### 5. 自定义数据源

扩展 `LinkCollector` 类以支持新的数据源：

```python
class CustomCollector(LinkCollector):
    async def _collect_from_custom_source(self, keyword: str) -> Set[str]:
        # 实现自定义收集逻辑
        pass
```

## 故障排除

### 常见问题

#### 1. FFmpeg 未找到

**错误**: `FileNotFoundError: ffprobe`

**解决**: 安装 FFmpeg
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# 下载 https://ffmpeg.org/download.html 并添加到 PATH
```

#### 2. 数据库连接失败

**错误**: `Database connection failed`

**解决**: 
1. 检查数据库路径权限
2. 确保 `data/` 目录存在
3. 检查 `.env` 文件中的数据库配置

#### 3. 网络连接超时

**错误**: `Request timeout`

**解决**:
1. 增加超时时间配置
2. 检查网络连接
3. 使用代理（如需要）

#### 4. 内存使用过高

**解决**:
1. 减少并发数量：`CHECKER__CONCURRENT_CHECKS=10`
2. 限制处理的链接数量：`--max-links 100`
3. 增加检测间隔：`CRAWLER__DELAY=2.0`

### 日志调试

启用详细日志：

```bash
# 临时启用调试
python src/main.py --debug run

# 永久启用调试
# 在 .env 中设置：
DEBUG=true
LOG_LEVEL=DEBUG
```

查看日志文件：

```bash
# 实时查看日志
tail -f logs/iptv_helper.log

# 查看错误日志
tail -f logs/error.log
```

### 性能优化

1. **并发调优**：
   ```bash
   # 高性能服务器
   CRAWLER__CONCURRENT_REQUESTS=20
   CHECKER__CONCURRENT_CHECKS=50
   
   # 低配置设备
   CRAWLER__CONCURRENT_REQUESTS=5
   CHECKER__CONCURRENT_CHECKS=10
   ```

2. **数据库优化**：
   - 使用 PostgreSQL 替代 SQLite（大数据量）
   - 定期清理过期数据
   - 创建索引优化查询

3. **缓存策略**：
   - 设置合理的检测间隔
   - 避免重复检测相同链接

### 获取帮助

- 查看命令帮助：`python src/main.py --help`
- 查看子命令帮助：`python src/main.py <command> --help`
- 查看项目文档：[GitHub Issues](your-repo-url/issues)
- 提交问题报告：包含错误日志和配置信息