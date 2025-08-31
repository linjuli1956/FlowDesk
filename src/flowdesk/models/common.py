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


@dataclass(frozen=True)
class Capabilities:
    """
    功能能力模型
    
    用于表示系统或组件的功能支持情况。
    """
    network_config: bool = True
    network_tools: bool = False
    rdp_management: bool = False
    hardware_monitoring: bool = False


@dataclass(frozen=True)
class AggregatedAdapterInfo:
    """
    聚合网卡信息模型
    
    用于网络UI协调器中聚合多个服务的网卡信息。
    """
    adapter_id: str
    basic_info: Optional[object] = None
    detailed_info: Optional[object] = None
    status_info: Optional[object] = None
    performance_info: Optional['PerformanceInfo'] = None


@dataclass(frozen=True)
class PerformanceInfo:
    """
    网卡性能信息模型
    
    用于表示网卡的性能相关数据。
    """
    link_speed: Optional[str] = None


@dataclass(frozen=True)
class NetworkCapabilities:
    """
    网络工具能力信息模型
    
    用于表示各种网络工具的可用性状态。
    """
    ping: bool = False
    tracert: bool = False
    netstat: bool = False
    ipconfig: bool = False
    nslookup: bool = False


@dataclass(frozen=True)
class HardwareMonitorCapabilities:
    """
    硬件监控能力信息模型
    
    用于表示硬件监控工具的可用性信息。
    """
    dll_path: str
    available: bool = False


@dataclass(frozen=True)
class PlatformInfo:
    """
    平台信息模型
    
    用于表示操作系统和硬件平台信息。
    """
    system: str
    release: str
    version: str
    machine: str
    processor: str


@dataclass(frozen=True)
class PythonVersionInfo:
    """
    Python版本信息模型
    
    用于表示Python环境版本信息。
    """
    major: int
    minor: int
    micro: int
    full: str


@dataclass(frozen=True)
class WindowsVersionInfo:
    """
    Windows版本信息模型
    
    用于表示Windows系统的详细版本信息。
    """
    major: Optional[int] = None
    minor: Optional[int] = None
    build: Optional[str] = None
    display_version: Optional[str] = None


@dataclass(frozen=True)
class SystemCapabilities:
    """
    系统能力信息模型
    
    用于表示完整的系统能力检测结果。
    """
    platform: PlatformInfo
    python_version: PythonVersionInfo
    admin_privileges: bool
    pyqt_available: bool
    network_tools: NetworkCapabilities
    hardware_monitor: HardwareMonitorCapabilities
    windows_version: Optional[WindowsVersionInfo] = None


@dataclass(frozen=True)
class AdapterStatusInfo:
    """
    网卡状态信息模型
    
    用于表示网卡的管理状态和连接状态。
    """
    admin_status: str = '未知'
    connect_status: str = '未知'
    interface_name: str = ''


@dataclass(frozen=True)
class AdapterConfigInfo:
    """
    网卡配置信息模型
    
    用于表示网卡的IP配置详细信息。
    """
    ip_addresses: list = None
    ipv6_addresses: list = None
    subnet_masks: list = None
    gateways: list = None
    dns_servers: list = None
    dhcp_enabled: bool = False
    
    def __post_init__(self):
        # 确保列表字段不为None
        if self.ip_addresses is None:
            object.__setattr__(self, 'ip_addresses', [])
        if self.ipv6_addresses is None:
            object.__setattr__(self, 'ipv6_addresses', [])
        if self.subnet_masks is None:
            object.__setattr__(self, 'subnet_masks', [])
        if self.gateways is None:
            object.__setattr__(self, 'gateways', [])
        if self.dns_servers is None:
            object.__setattr__(self, 'dns_servers', [])


@dataclass(frozen=True)
class AdapterDiscoveryInfo:
    """
    网卡发现信息模型
    
    用于表示网卡发现过程中的基础信息。
    """
    node: str
    description: str
    guid: str
    net_connection_id: Optional[str] = None
    display_name: Optional[str] = None
