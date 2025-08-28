"""
网络工具数据模型

定义网络诊断工具相关的数据结构。
这是一个占位符模块，为后续网络工具功能开发预留接口。
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PingResult:
    """
    Ping测试结果模型
    
    用于表示ping命令的测试结果。
    """
    target_host: str
    success: bool = False
    response_time: Optional[float] = None
    packet_loss: float = 0.0


@dataclass
class TracertHop:
    """
    路由跟踪跳点模型
    
    用于表示tracert命令中的一个跳点信息。
    """
    hop_number: int
    host: Optional[str] = None
    response_time: Optional[float] = None


@dataclass
class SystemToolResult:
    """
    系统工具执行结果模型
    
    用于表示系统工具命令的执行结果。
    """
    command: str
    success: bool = False
    output: str = ""
    error: str = ""
