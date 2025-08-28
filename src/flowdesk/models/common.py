"""
通用数据模型

定义项目中通用的数据结构和类型。
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProgressInfo:
    """
    操作进度信息模型
    
    用于表示长时间操作的进度状态。
    """
    current: int = 0
    total: int = 100
    message: str = ""
    completed: bool = False


@dataclass
class ErrorInfo:
    """
    错误信息封装模型
    
    用于统一的错误信息传递。
    """
    title: str
    message: str
    error_code: Optional[str] = None


@dataclass
class Capabilities:
    """
    功能能力模型
    
    用于表示系统或组件的功能支持情况。
    """
    network_config: bool = True
    network_tools: bool = False
    rdp_management: bool = False
    hardware_monitoring: bool = False
