"""
网络适配器信息数据模型

功能说明：
• 定义网络适配器的完整信息结构，包括基本信息、IP配置、状态等
• 提供数据验证和类型安全，避免在UI和服务层之间传递原始字典
• 支持智能IP分类：根据网关判断主IP和额外IP
• 为网络配置功能提供标准化的数据契约

设计理念：
• 数据模型作为UI层和服务层之间的桥梁，确保数据传递的一致性
• 包含完整的网卡状态信息，支持实时状态同步和界面更新
• 提供便捷的数据访问方法，简化业务逻辑实现
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import ipaddress


@dataclass
class AdapterInfo:
    """
    网络适配器完整信息模型
    
    包含网卡的所有基本信息、IP配置、连接状态等，
    用于在UI层和服务层之间传递网卡数据，确保数据结构的一致性和类型安全。
    """
    
    # 网卡基本标识信息
    id: str                              # 网卡唯一标识符（GUID或接口索引）
    name: str                           # 网卡内部名称（如"以太网"）
    friendly_name: str                  # 网卡友好显示名称（用于下拉框显示）
    description: str                    # 网卡详细描述信息
    mac_address: str                    # MAC物理地址
    
    # 网卡连接状态信息
    status: str                         # 连接状态："已连接"、"已禁用"、"未连接"
    is_enabled: bool = True            # 网卡是否启用
    is_connected: bool = False         # 网卡是否已连接
    
    # IP配置信息
    ip_addresses: List[str] = field(default_factory=list)     # 所有IPv4地址列表
    ipv6_addresses: List[str] = field(default_factory=list)   # 所有IPv6地址列表
    subnet_masks: List[str] = field(default_factory=list)     # 对应的子网掩码列表
    gateway: str = ""                                          # 默认网关地址
    dns_servers: List[str] = field(default_factory=list)      # DNS服务器列表
    dhcp_enabled: bool = True                                  # 是否启用DHCP自动获取IP
    
    # 网络性能信息
    link_speed: str = ""               # 连接速度（如"1 Gbps"）
    interface_type: str = ""           # 接口类型（如"以太网"、"无线"）
    
    # 时间戳信息
    last_updated: datetime = field(default_factory=datetime.now)  # 最后更新时间
    
    def get_primary_ip(self) -> str:
        """
        获取主要IP地址
        
        根据智能IP显示逻辑，返回与默认网关同网段的IP地址作为主IP。
        如果没有网关或无法判断，则返回第一个IP地址。
        
        Returns:
            str: 主要IP地址，如果没有IP则返回空字符串
        """
        if not self.ip_addresses:
            return ""
            
        if not self.gateway:
            # 没有网关时，返回第一个IP作为主IP
            return self.ip_addresses[0]
        
        try:
            # 解析网关地址，找到与网关同网段的IP
            gateway_ip = ipaddress.IPv4Address(self.gateway)
            
            for i, ip_str in enumerate(self.ip_addresses):
                if i < len(self.subnet_masks):
                    try:
                        ip = ipaddress.IPv4Address(ip_str)
                        mask = ipaddress.IPv4Address(self.subnet_masks[i])
                        
                        # 计算网络地址，判断是否与网关在同一网段
                        ip_network = ipaddress.IPv4Network(f"{ip_str}/{self.subnet_masks[i]}", strict=False)
                        if gateway_ip in ip_network:
                            return ip_str
                    except (ipaddress.AddressValueError, ValueError):
                        continue
            
            # 如果没有找到同网段的IP，返回第一个IP
            return self.ip_addresses[0]
            
        except (ipaddress.AddressValueError, ValueError):
            # 网关地址无效时，返回第一个IP
            return self.ip_addresses[0] if self.ip_addresses else ""
    
    def get_primary_subnet_mask(self) -> str:
        """
        获取主要IP对应的子网掩码
        
        Returns:
            str: 主要IP的子网掩码，如果没有则返回空字符串
        """
        primary_ip = self.get_primary_ip()
        if not primary_ip or not self.subnet_masks:
            return ""
        
        try:
            primary_index = self.ip_addresses.index(primary_ip)
            if primary_index < len(self.subnet_masks):
                return self.subnet_masks[primary_index]
        except ValueError:
            pass
        
        # 如果找不到对应的掩码，返回第一个掩码
        return self.subnet_masks[0] if self.subnet_masks else ""
    
    def get_extra_ips(self) -> List[tuple]:
        """
        获取额外IP地址列表
        
        返回除主IP外的所有其他IP地址及其对应的子网掩码。
        
        Returns:
            List[tuple]: 额外IP列表，每个元素为(ip_address, subnet_mask)元组
        """
        primary_ip = self.get_primary_ip()
        extra_ips = []
        
        for i, ip_str in enumerate(self.ip_addresses):
            if ip_str != primary_ip:
                subnet_mask = self.subnet_masks[i] if i < len(self.subnet_masks) else ""
                extra_ips.append((ip_str, subnet_mask))
        
        return extra_ips
    
    def get_primary_dns(self) -> str:
        """
        获取主DNS服务器地址
        
        Returns:
            str: 主DNS服务器地址，如果没有则返回空字符串
        """
        return self.dns_servers[0] if self.dns_servers else ""
    
    def get_secondary_dns(self) -> str:
        """
        获取备用DNS服务器地址
        
        Returns:
            str: 备用DNS服务器地址，如果没有则返回空字符串
        """
        return self.dns_servers[1] if len(self.dns_servers) > 1 else ""
    
    def format_for_copy(self) -> str:
        """
        格式化网卡信息用于复制到剪贴板
        
        生成包含完整网卡信息的格式化文本，包含时间戳，
        用于"复制网卡信息"功能。
        
        Returns:
            str: 格式化的网卡信息文本
        """
        lines = [
            "-----------------------------------------------------------",
            f"适配器名称: {self.friendly_name}",
            f"MAC地址: {self.mac_address}",
            f"适配器状态: {self.status}",
            f"连接速度: {self.link_speed}",
            f"接口类型: {self.interface_type}",
            "",
            "IP配置信息:",
            f"DHCP启用: {'是' if self.dhcp_enabled else '否'}",
            f"默认网关: {self.gateway}",
            f"主DNS: {self.get_primary_dns()}",
            f"备用DNS: {self.get_secondary_dns()}",
            "",
            "IP地址列表:"
        ]
        
        # 添加主IP信息
        primary_ip = self.get_primary_ip()
        primary_mask = self.get_primary_subnet_mask()
        if primary_ip:
            lines.append(f"主IP: {primary_ip} / {primary_mask}")
        
        # 添加额外IP信息
        extra_ips = self.get_extra_ips()
        for i, (ip, mask) in enumerate(extra_ips, 1):
            lines.append(f"额外IP{i}: {ip} / {mask}")
        
        # 添加时间戳
        lines.extend([
            "",
            f"信息获取时间: {self.last_updated.strftime('%Y-%m-%d %H:%M:%S')}",
            "-----------------------------------------------------------"
        ])
        
        return "\n".join(lines)


@dataclass(frozen=True)
class IPConfigInfo:
    """
    IP配置信息模型
    
    用于在UI层和服务层之间传递IP配置数据，
    支持静态IP配置和DHCP模式切换。
    """
    
    adapter_id: str                     # 目标网卡ID
    ip_address: str                     # IP地址
    subnet_mask: str                    # 子网掩码
    gateway: str                        # 默认网关
    dns_primary: str                    # 主DNS服务器
    dns_secondary: str = ""             # 备用DNS服务器
    dhcp_enabled: bool = False          # 是否使用DHCP


@dataclass(frozen=True)
class ExtraIP:
    """
    额外IP地址信息模型
    
    用于表示网卡上配置的额外IP地址信息，
    包括IP地址和对应的子网掩码。
    """
    ip_address: str      # IP地址
    subnet_mask: str     # 子网掩码


@dataclass(frozen=True)
class DnsConfig:
    """
    DNS配置信息模型
    
    用于表示网卡的DNS服务器配置信息，
    包括主DNS和备用DNS服务器地址。
    """
    primary_dns: Optional[str] = None    # 主DNS服务器
    secondary_dns: Optional[str] = None  # 备用DNS服务器
