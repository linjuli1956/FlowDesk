"""
远程桌面会话数据模型

定义远程桌面连接的会话信息和目标配置。
这是一个占位符模块，为后续RDP功能开发预留接口。
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RdpSession:
    """
    远程桌面会话信息模型
    
    用于表示一个远程桌面连接会话的基本信息。
    """
    session_id: str
    target_host: str
    username: Optional[str] = None
    is_connected: bool = False


@dataclass
class RdpTarget:
    """
    远程桌面目标配置模型
    
    用于表示远程桌面连接的目标主机配置信息。
    """
    host: str
    port: int = 3389
    username: Optional[str] = None
    display_name: Optional[str] = None
