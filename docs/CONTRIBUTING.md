# 贡献指南

感谢您对 IPTV Helper 项目的关注！本指南将帮助您了解如何为项目做出贡献。

## 目录

- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [测试](#测试)
- [文档](#文档)
- [问题报告](#问题报告)
- [功能请求](#功能请求)

## 开发环境设置

### 1. 克隆仓库

```bash
git clone <your-repo-url>
cd iptv-helper
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate.bat  # Windows
```

### 3. 安装依赖

```bash
# 安装运行时依赖
pip install -r requirements.txt

# 安装开发依赖
pip install pytest pytest-asyncio black isort flake8 mypy
```

### 4. 配置开发环境

```bash
# 复制配置文件
cp .env.example .env

# 编辑配置（启用调试模式）
# DEBUG=true
# LOG_LEVEL=DEBUG
```

### 5. 初始化数据库

```bash
python src/main.py sync-channels
```

## 代码规范

### Python 代码风格

我们使用以下工具来保持代码风格一致：

- **Black**: 代码格式化
- **isort**: 导入排序
- **flake8**: 代码检查
- **mypy**: 类型检查

### 运行代码检查

```bash
# 格式化代码
black src/ tests/
isort src/ tests/

# 检查代码风格
flake8 src/ tests/

# 类型检查
mypy src/
```

### 代码风格要求

1. **函数和变量命名**: 使用 snake_case
2. **类命名**: 使用 PascalCase
3. **常量**: 使用 UPPER_SNAKE_CASE
4. **文档字符串**: 使用 Google 风格
5. **类型注解**: 为公共 API 添加类型注解

### 示例代码

```python
from typing import List, Optional
from loguru import logger


class ChannelManager:
    """频道管理器
    
    负责频道的增删改查和配置同步。
    """
    
    def __init__(self):
        """初始化频道管理器"""
        self.settings = get_settings()
    
    def get_channels(self, 
                    category: Optional[str] = None, 
                    active_only: bool = True) -> List[Channel]:
        """获取频道列表
        
        Args:
            category: 频道分类筛选
            active_only: 是否只返回活跃频道
            
        Returns:
            频道列表
            
        Raises:
            DatabaseError: 数据库查询失败时抛出
        """
        logger.debug(f"获取频道列表: category={category}, active_only={active_only}")
        
        try:
            # 实现逻辑
            pass
        except Exception as e:
            logger.error(f"获取频道列表失败: {e}")
            raise DatabaseError(f"查询失败: {e}")
```

## 提交规范

### 提交消息格式

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### 提交类型

- `feat`: 新功能
- `fix`: 错误修复
- `docs`: 文档更新
- `style`: 代码格式调整（不影响功能）
- `refactor`: 代码重构
- `test`: 添加或修改测试
- `chore`: 构建过程或辅助工具的变动

### 示例

```bash
# 新功能
git commit -m "feat(collector): 添加新的数据源支持"

# 错误修复
git commit -m "fix(checker): 修复FFmpeg检测超时问题"

# 文档更新
git commit -m "docs: 更新API文档和使用示例"

# 重构
git commit -m "refactor(models): 优化数据库模型结构"
```

### 分支策略

- `main`: 主分支，稳定版本
- `develop`: 开发分支
- `feature/*`: 功能分支
- `fix/*`: 修复分支
- `docs/*`: 文档分支

### 工作流程

1. 从 `develop` 分支创建功能分支
2. 在功能分支上开发
3. 提交 Pull Request 到 `develop`
4. 代码审查通过后合并
5. 定期从 `develop` 合并到 `main`

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行指定测试文件
pytest tests/test_basic.py

# 运行测试并显示覆盖率
pytest --cov=src

# 运行异步测试
pytest -v tests/
```

### 编写测试

#### 单元测试示例

```python
import pytest
from unittest.mock import Mock, AsyncMock
from src.services.channel_manager import ChannelManager


class TestChannelManager:
    """测试频道管理器"""
    
    @pytest.fixture
    def channel_manager(self):
        """创建频道管理器实例"""
        return ChannelManager()
    
    def test_validate_channel_data(self, channel_manager):
        """测试频道数据验证"""
        valid_data = {
            "name": "测试频道",
            "keywords": ["测试"],
            "category": "测试分类"
        }
        
        result = channel_manager.validate_channel_data(valid_data)
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_collect_links(self):
        """测试链接收集"""
        # 使用模拟对象
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = "<html>...</html>"
        
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        # 测试收集逻辑
        # ...
```

#### 集成测试示例

```python
import pytest
import tempfile
import os
from src.main import cli
from click.testing import CliRunner


class TestCLI:
    """测试命令行界面"""
    
    def test_sync_channels(self):
        """测试频道同步命令"""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建临时配置文件
            config_file = os.path.join(tmpdir, "channels.yaml")
            with open(config_file, "w") as f:
                f.write("""
channels:
  - name: "测试频道"
    keywords: ["测试"]
    category: "测试"
""")
            
            # 运行命令
            result = runner.invoke(cli, ['sync-channels', '--file', config_file])
            assert result.exit_code == 0
```

### 测试覆盖率

目标测试覆盖率：80% 以上

```bash
# 生成覆盖率报告
pytest --cov=src --cov-report=html

# 查看报告
open htmlcov/index.html
```

## 文档

### 文档结构

- `README.md`: 项目概述和快速开始
- `docs/USAGE.md`: 详细使用指南
- `docs/API.md`: API 文档
- `docs/CONTRIBUTING.md`: 贡献指南

### 文档规范

1. **使用 Markdown 格式**
2. **添加目录导航**
3. **提供代码示例**
4. **保持文档同步更新**

### 代码文档

使用 Google 风格的文档字符串：

```python
def collect_links_for_channel(self, channel: Channel) -> List[str]:
    """为指定频道收集链接
    
    通过频道的关键字在配置的数据源中搜索可用的流媒体链接。
    
    Args:
        channel: 频道对象，包含搜索关键字等信息
        
    Returns:
        收集到的链接列表，已去重处理
        
    Raises:
        NetworkError: 网络连接失败时抛出
        ValidationError: 频道数据无效时抛出
        
    Example:
        >>> manager = ChannelManager()
        >>> channel = manager.get_channel_by_name("CCTV1")
        >>> links = await collector.collect_links_for_channel(channel)
        >>> print(f"收集到 {len(links)} 个链接")
    """
```

## 问题报告

### 报告 Bug

在创建问题报告时，请包含以下信息：

1. **问题描述**: 清晰描述遇到的问题
2. **重现步骤**: 详细的重现步骤
3. **预期行为**: 描述期望的正确行为
4. **实际行为**: 描述实际发生的情况
5. **环境信息**: Python 版本、操作系统等
6. **日志输出**: 相关的错误日志
7. **配置文件**: 相关的配置信息（脱敏后）

### 模板

```markdown
**问题描述**
简要描述遇到的问题

**重现步骤**
1. 执行命令 `python src/main.py ...`
2. 查看输出 '...'
3. 发现错误 '...'

**预期行为**
应该 ...

**实际行为**
实际 ...

**环境信息**
- OS: [e.g. Ubuntu 20.04]
- Python: [e.g. 3.9.7]
- IPTV Helper: [e.g. v0.1.0]

**日志输出**
```
粘贴相关日志
```

**配置信息**
```yaml
相关配置（请脱敏）
```
```

## 功能请求

### 提交功能请求

1. **检查现有 Issues**: 确认功能未被提议
2. **详细描述**: 清晰描述功能需求
3. **使用场景**: 说明功能的使用场景
4. **实现建议**: 如有想法可提供实现建议

### 模板

```markdown
**功能描述**
希望添加的功能是 ...

**问题解决**
这个功能可以解决 ... 问题

**使用场景**
在 ... 情况下，我希望能够 ...

**实现建议**
可以考虑 ... 方式实现

**替代方案**
目前的替代方案是 ...
```

## 代码审查

### 审查清单

- [ ] 代码风格符合规范
- [ ] 添加了必要的测试
- [ ] 测试通过
- [ ] 更新了相关文档
- [ ] 提交消息符合规范
- [ ] 没有引入安全问题
- [ ] 性能没有明显下降

### 审查重点

1. **功能正确性**: 代码是否实现了预期功能
2. **代码质量**: 是否遵循最佳实践
3. **测试覆盖**: 是否有足够的测试
4. **性能影响**: 是否影响系统性能
5. **安全考虑**: 是否存在安全风险

## 发布流程

### 版本号规范

使用 [Semantic Versioning](https://semver.org/) 规范：

- `MAJOR.MINOR.PATCH` (如 1.2.3)
- `MAJOR`: 不兼容的 API 变更
- `MINOR`: 向下兼容的功能性新增
- `PATCH`: 向下兼容的问题修正

### 发布步骤

1. 更新版本号
2. 更新 CHANGELOG
3. 创建 Release Tag
4. 构建和测试
5. 发布到 PyPI（如适用）

## 社区

### 行为准则

- 尊重他人
- 建设性沟通
- 欢迎新手
- 分享知识

### 获取帮助

- GitHub Issues: 报告问题和功能请求
- Discussions: 一般讨论和问题
- 邮件: [维护者邮箱]

感谢您的贡献！🎉