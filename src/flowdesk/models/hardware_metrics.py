"""
硬件监控数据模型

定义硬件监控相关的数据结构。
这是一个占位符模块，为后续硬件监控功能开发预留接口。
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class HardwareMetrics:
    """
    硬件监控数据模型
    
    用于表示系统硬件的监控数据。
    """
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_usage: float = 0.0


@dataclass
class HardwareInfo:
    """
    硬件信息模型
    
    用于表示系统硬件的基本信息。
    """
    cpu_name: Optional[str] = None
    memory_total: Optional[int] = None
    disk_total: Optional[int] = None


@dataclass
class FloatWindowSettings:
    """
    浮动窗口设置模型
    
    用于表示硬件监控浮动窗口的配置信息。
    """
    x: int = 0
    y: int = 0
    width: int = 200
    height: int = 100
    always_on_top: bool = True
