"""
数据模型层 (Models)

定义FlowDesk应用程序中所有的数据结构和类型。
模型层作为UI层和服务层之间的数据契约，确保类型安全和数据一致性。

主要模型类：
- AdapterInfo: 网络适配器信息
- IPConfigInfo: IP配置信息  
- DnsConfig: DNS配置信息
- RdpSession: 远程桌面会话信息
- HardwareMetrics: 硬件监控数据
- ProgressInfo: 操作进度信息
- ErrorInfo: 错误信息封装

设计原则：
- 提供基本的数据验证和转换
- 避免使用原始字典传递数据
- 支持序列化和反序列化
"""

from .adapter_info import AdapterInfo, IPConfigInfo, DnsConfig
from .rdp_session import RdpSession, RdpTarget
from .hardware_metrics import HardwareMetrics, HardwareInfo, FloatWindowSettings
from .network_tools import PingResult, TracertHop, SystemToolResult
from .common import (
    ProgressInfo, ErrorInfo, Capabilities,
    AggregatedAdapterInfo, PerformanceInfo, 
    NetworkCapabilities, HardwareMonitorCapabilities,
    PlatformInfo, PythonVersionInfo, WindowsVersionInfo, SystemCapabilities,
    AdapterStatusInfo, AdapterConfigInfo, AdapterDiscoveryInfo
)

__all__ = [
    'AdapterInfo', 'IPConfigInfo', 'DnsConfig',
    'RdpSession', 'RdpTarget', 
    'HardwareMetrics', 'HardwareInfo', 'FloatWindowSettings',
    'PingResult', 'TracertHop', 'SystemToolResult',
    'ProgressInfo', 'ErrorInfo', 'Capabilities',
    'AggregatedAdapterInfo', 'PerformanceInfo',
    'NetworkCapabilities', 'HardwareMonitorCapabilities',
    'PlatformInfo', 'PythonVersionInfo', 'WindowsVersionInfo', 'SystemCapabilities',
    'AdapterStatusInfo', 'AdapterConfigInfo', 'AdapterDiscoveryInfo'
]
