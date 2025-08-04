# IPTV Hunter

一个开源的IPTV频道管理系统，用于维护可用的IPTV频道列表并自动检测频道可用性。

## 功能特性

- 🎯 **频道管理**: 维护频道列表（名称、Logo、关键字等）
- 🔍 **智能收集**: 自动从多个源收集频道链接
- ✅ **可用性检测**: 自动检测链接可用性和延迟
- 🎬 **内容验证**: 使用FFmpeg验证流媒体内容
- 💾 **数据库管理**: 完整的数据存储和管理
- 📺 **M3U生成**: 生成标准M3U播放列表

## 项目结构

```
iptv-hunter/
├── README.md
├── requirements.txt
├── setup.py
├── config/                 # 配置文件
│   ├── settings.py
│   └── channels.yaml
├── src/                    # 源代码
│   ├── models/            # 数据模型
│   ├── services/          # 业务逻辑
│   ├── utils/             # 工具函数
│   └── main.py           # 主程序
├── tests/                 # 测试代码
├── scripts/               # 脚本工具
├── data/                  # 数据文件
└── output/                # 输出文件
```

## 快速开始

### 方法一：一键启动（推荐）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 快速开始（自动配置并运行）
python quickstart.py
```

### 方法二：使用start.sh脚本（最简便）

```bash
# 运行完整流程（默认）
./start.sh
```

这会执行完整的工作流程：
1. 同步频道配置
2. 收集所有频道链接
3. 检测链接可用性
4. 生成 M3U 播放列表

### 方法三：手动安装

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 检查项目完整性
python test_imports.py

# 3. 运行程序
python run.py --help           # 查看帮助
python run.py sync-channels    # 同步频道配置
python run.py run              # 运行完整流程
```

### 配置频道

编辑 `config/channels.yaml` 文件，添加你想要监控的频道：

```yaml
channels:
  - name: "CCTV1"
    logo: "https://live.fanmingming.com/tv/CCTV1.png"
    keywords: ["CCTV1", "央视一套", "中央一套"]
    category: "央视"
    priority: 10
```

## 详细使用指南

### start.sh 脚本使用

#### 最简单的用法
```bash
# 运行完整流程（默认）
./start.sh
```

#### 按模式运行
```bash
# 仅收集链接
./start.sh --mode collect

# 仅检测链接可用性
./start.sh --mode check

# 仅生成播放列表
./start.sh --mode generate

# 查看统计信息
./start.sh --mode stats
```

#### 按频道/分类运行
```bash
# 收集央视频道链接
./start.sh --mode collect --category 央视

# 收集特定频道链接
./start.sh --mode collect --channel CCTV1

# 检测体育频道链接
./start.sh --mode check --category 体育 --max-links 100
```

#### 自定义输出
```bash
# 生成JSON格式播放列表
./start.sh --mode generate --format json

# 指定输出文件路径
./start.sh --mode generate --output ./my_playlist.m3u

# 设置最低质量评分
./start.sh --mode generate --min-quality 50
```

#### 调试和强制执行
```bash
# 启用调试模式
./start.sh --debug

# 跳过确认直接执行
./start.sh --force

# 调试模式 + 强制执行
./start.sh --debug --force
```

### 支持的频道分类

- **央视**: CCTV1-17 等央视频道
- **卫视**: 湖南卫视、东方卫视、江苏卫视等
- **体育**: CCTV5、CCTV5+、五星体育等
- **新闻**: CCTV新闻、凤凰卫视等
- **娱乐**: 各类娱乐频道

### start.sh 完整参数列表

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--mode` | 运行模式 | full | collect, check, generate, full, stats |
| `--channel` | 指定频道名称 | 无 | CCTV1, 湖南卫视 |
| `--category` | 指定频道分类 | 无 | 央视, 卫视, 体育 |
| `--output` | 输出文件路径 | 默认路径 | ./my_playlist.m3u |
| `--format` | 输出格式 | m3u | m3u, json |
| `--max-links` | 限制检测链接数量 | 不限制 | 50, 100 |
| `--min-quality` | 最低质量评分 | 0 | 0-100 |
| `--debug` | 启用调试模式 | false | - |
| `--force` | 跳过确认 | false | - |
| `--help` | 显示帮助 | - | - |
| `--version` | 显示版本 | - | - |

### 命令行工具使用

#### 主要命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `run` | 执行完整的更新流程 | `python run.py run` |
| `sync-channels` | 同步频道配置到数据库 | `python run.py sync-channels` |
| `collect` | 收集频道链接 | `python run.py collect` |
| `check` | 检测链接可用性 | `python run.py check` |
| `generate` | 生成播放列表 | `python run.py generate` |
| `stats` | 显示统计信息 | `python run.py stats` |
| `backup` | 备份数据库 | `python run.py backup` |

#### 命令选项

**collect 命令**
```bash
# 收集指定频道的链接
python run.py collect --channel "CCTV1"

# 收集指定分类的所有频道
python run.py collect --category "央视"
```

**check 命令**
```bash
# 检测指定频道的链接
python run.py check --channel "CCTV1"

# 限制检测数量
python run.py check --max-links 100
```

**generate 命令**
```bash
# 生成到指定文件
python run.py generate --output ./my_playlist.m3u

# 生成指定分类
python run.py generate --category "央视"

# 设置最低质量评分
python run.py generate --min-quality 5

# 生成JSON格式
python run.py generate --format json
```

## 输出文件

脚本执行后会在以下位置生成文件：

```
output/
├── playlist.m3u              # 主播放列表
├── playlist.json             # JSON格式播放列表
├── categories/               # 按分类生成的播放列表
│   ├── 央视.m3u
│   ├── 卫视.m3u
│   └── 体育.m3u
└── ...
```

## 技术栈

- **Python 3.8+**
- **数据库**: SQLite / PostgreSQL
- **Web爬虫**: requests + BeautifulSoup
- **异步处理**: asyncio + aiohttp
- **流媒体检测**: ffmpeg-python
- **配置管理**: pydantic
- **日志系统**: loguru

## 支持的平台

- Linux
- macOS
- Windows
- Docker容器

## 支持的流媒体格式

- HLS (.m3u8)
- FLV
- MP4
- TS segments
- RTMP
- RTSP

## 故障排除

### 虚拟环境问题
```bash
# 如果提示虚拟环境不存在
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 权限问题
```bash
# 添加执行权限
chmod +x start.sh
```

### 网络连接问题
```bash
# 使用调试模式查看详细信息
./start.sh --debug --mode collect --channel CCTV1
```

### 首次运行注意事项

1. **首次运行**: 确保已安装依赖 `pip install -r requirements.txt`
2. **虚拟环境**: 脚本会自动使用 `venv/` 目录下的虚拟环境
3. **网络状况**: tonkiang.us 可能偶尔返回503错误，这是正常现象
4. **执行时间**: 完整流程可能需要几分钟时间，请耐心等待
5. **权限问题**: 确保脚本有执行权限 `chmod +x start.sh`

## 高级用法

### 组合使用
```bash
# 先收集央视频道，再生成高质量播放列表
./start.sh --mode collect --category 央视
./start.sh --mode check --category 央视 --max-links 200
./start.sh --mode generate --category 央视 --min-quality 70
```

### 批量处理
```bash
# 分别处理不同分类
for category in 央视 卫视 体育; do
    ./start.sh --mode collect --category "$category" --force
    ./start.sh --mode check --category "$category" --max-links 50 --force
done
./start.sh --mode generate --force
```

## 更多文档

- 📖 **[详细使用指南](docs/USAGE.md)** - 高级用法、故障排除、性能优化
- 🔧 **[API文档](docs/API.md)** - 开发者API接口说明
- 🤝 **[贡献指南](docs/CONTRIBUTING.md)** - 如何为项目做贡献

## 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境设置

1. **克隆仓库**
```bash
git clone <your-repo-url>
cd iptv-hunter
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate.bat  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **代码规范**
我们使用以下工具来保持代码风格一致：
- **Black**: 代码格式化
- **isort**: 导入排序
- **flake8**: 代码检查
- **mypy**: 类型检查

## 许可证

MIT License