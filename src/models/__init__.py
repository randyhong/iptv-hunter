"""数据模型模块"""

from .channel import Channel
from .link import Link, LinkStatus
from .check_result import CheckResult

__all__ = ["Channel", "Link", "LinkStatus", "CheckResult"]