# -*- coding: utf-8 -*-
"""
基于psutil的网卡配置获取器｜专门处理未连接网卡的静态IP配置获取
"""

import logging
import ipaddress
from typing import Dict, Any, Optional, List
from .network_service_base import NetworkServiceBase

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class AdapterPsutilConfigRetriever(NetworkServiceBase):
    """
    基于psutil的网卡配置获取器
    
    这个类专门解决未连接网卡的静态IP配置获取问题。
    psutil能够直接从系统获取网络接口配置，不依赖于网卡的连接状态，
    这使得它能够获取到已配置但未连接的网卡的静态IP信息。
    
    技术优势：
    - 不依赖网卡连接状态：能获取未连接网卡的配置
    - 跨平台兼容：psutil支持Windows、Linux、macOS
    - 性能优秀：直接系统调用，无需解析命令行输出
    - 数据准确：直接从内核获取网络接口信息
    
    主要功能：
    - 获取网卡IPv4/IPv6地址配置
    - 获取子网掩码和广播地址
    - 获取网卡状态信息（启用/禁用、速度等）
    - 提供统一的配置数据格式
    """
    
    def __init__(self, parent=None):
        """
        初始化psutil配置获取器
        
        Args:
            parent: PyQt父对象，用于内存管理
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 检查psutil可用性
        if not PSUTIL_AVAILABLE:
            self.logger.warning("psutil模块未安装，无法使用psutil配置获取功能")
    
    def get_config_via_psutil(self, adapter_name: str) -> Optional[Dict[str, Any]]:
        """
        使用psutil获取网卡配置信息
        
        这个方法通过psutil.net_if_addrs()和psutil.net_if_stats()
        获取网卡的完整配置信息，包括未连接网卡的静态配置。
        
        技术实现流程：
        1. 使用psutil.net_if_addrs()获取所有网络接口地址
        2. 使用psutil.net_if_stats()获取网络接口状态信息
        3. 过滤和格式化IPv4/IPv6地址信息
        4. 提取子网掩码、广播地址等配置
        5. 构造标准化的配置数据字典
        
        Args:
            adapter_name (str): 网卡连接名称，如"WLAN"、"以太网"
            
        Returns:
            Optional[Dict[str, Any]]: 包含完整配置信息的字典，包括：
                - ip_addresses: IPv4地址列表
                - ipv6_addresses: IPv6地址列表
                - subnet_masks: 子网掩码列表
                - broadcast_addresses: 广播地址列表
                - is_up: 网卡启用状态
                - speed: 网卡速度（如果可用）
                - mtu: 最大传输单元
        """
        if not PSUTIL_AVAILABLE:
            self.logger.error("psutil模块不可用，无法获取网卡配置")
            return None
        
        # 初始化配置字典，提供默认值确保数据结构完整性
        config = {
            'ip_addresses': [],
            'ipv6_addresses': [],
            'subnet_masks': [],
            'broadcast_addresses': [],
            'is_up': False,
            'speed': 0,
            'mtu': 0,
            'duplex': 'unknown'
        }
        
        try:
            self.logger.debug(f"开始使用psutil获取网卡 {adapter_name} 的配置信息")
            
            # 获取所有网络接口地址信息
            net_if_addrs = psutil.net_if_addrs()
            if adapter_name not in net_if_addrs:
                self.logger.warning(f"psutil中未找到网卡接口: {adapter_name}")
                return None
            
            # 获取指定网卡的地址信息
            addresses = net_if_addrs[adapter_name]
            self.logger.debug(f"网卡 {adapter_name} 找到 {len(addresses)} 个地址配置")
            
            # 解析IPv4和IPv6地址
            ipv4_addresses = []
            ipv6_addresses = []
            subnet_masks = []
            broadcast_addresses = []
            
            for addr in addresses:
                if addr.family == 2:  # AF_INET (IPv4)
                    if addr.address and addr.address != '0.0.0.0' and not self._is_apipa_address(addr.address):
                        ipv4_addresses.append(addr.address)
                        if addr.netmask:
                            subnet_masks.append(addr.netmask)
                        if addr.broadcast:
                            broadcast_addresses.append(addr.broadcast)
                        
                        self.logger.debug(f"找到有效IPv4地址: {addr.address}/{addr.netmask}")
                    elif self._is_apipa_address(addr.address):
                        self.logger.debug(f"过滤APIPA地址: {addr.address}")
                
                elif addr.family == 23:  # AF_INET6 (IPv6)
                    if addr.address and not addr.address.startswith('fe80::'):
                        # 过滤掉链路本地地址
                        ipv6_addresses.append(addr.address)
                        self.logger.debug(f"找到IPv6地址: {addr.address}")
            
            # 获取网卡状态信息
            net_if_stats = psutil.net_if_stats()
            if adapter_name in net_if_stats:
                stats = net_if_stats[adapter_name]
                config['is_up'] = stats.isup
                config['speed'] = stats.speed if stats.speed > 0 else 0
                config['mtu'] = stats.mtu
                config['duplex'] = self._format_duplex(stats.duplex)
                
                self.logger.debug(f"网卡状态: 启用={stats.isup}, 速度={stats.speed}Mbps, MTU={stats.mtu}")
            
            # 更新配置字典
            config['ip_addresses'] = ipv4_addresses
            config['ipv6_addresses'] = ipv6_addresses
            config['subnet_masks'] = subnet_masks
            config['broadcast_addresses'] = broadcast_addresses
            
            # 记录获取结果
            if ipv4_addresses:
                self.logger.info(f"psutil成功获取网卡 {adapter_name} 的IPv4配置: {len(ipv4_addresses)} 个地址")
            else:
                self.logger.info(f"网卡 {adapter_name} 无IPv4配置或地址为空")
            
            return config
            
        except Exception as e:
            self.logger.error(f"psutil获取网卡 {adapter_name} 配置失败: {str(e)}")
            return None
    
    def _format_duplex(self, duplex_value) -> str:
        """
        格式化双工模式值
        
        Args:
            duplex_value: psutil返回的双工模式值
            
        Returns:
            str: 格式化的双工模式字符串
        """
        duplex_map = {
            0: 'unknown',
            1: 'half',
            2: 'full'
        }
        return duplex_map.get(duplex_value, 'unknown')
    
    def _is_apipa_address(self, ip_address: str) -> bool:
        """
        检查IP地址是否为APIPA（自动专用IP地址）
        
        APIPA地址范围：169.254.0.1 到 169.254.255.254
        这些地址是Windows在无法获取DHCP地址时自动分配的链路本地地址，
        不是用户真正配置的静态IP地址，应该被过滤掉。
        
        Args:
            ip_address (str): 要检查的IP地址
            
        Returns:
            bool: 如果是APIPA地址返回True，否则返回False
        """
        if not ip_address:
            return False
        
        try:
            # 检查是否为169.254.x.x格式
            parts = ip_address.split('.')
            if len(parts) == 4:
                return parts[0] == '169' and parts[1] == '254'
        except Exception:
            pass
        
        return False
    
    def get_all_interfaces_config(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有网络接口的配置信息
        
        这个方法用于调试和全局网卡配置获取。
        返回系统中所有网络接口的详细配置信息。
        
        Returns:
            Dict[str, Dict[str, Any]]: 以接口名为键的配置字典
        """
        if not PSUTIL_AVAILABLE:
            return {}
        
        all_configs = {}
        
        try:
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            
            for interface_name in net_if_addrs.keys():
                config = self.get_config_via_psutil(interface_name)
                if config:
                    all_configs[interface_name] = config
            
            self.logger.debug(f"获取到 {len(all_configs)} 个网络接口的配置信息")
            
        except Exception as e:
            self.logger.error(f"获取所有接口配置失败: {str(e)}")
        
        return all_configs
    
    def is_psutil_available(self) -> bool:
        """
        检查psutil是否可用
        
        Returns:
            bool: psutil可用性状态
        """
        return PSUTIL_AVAILABLE
    
    def get_interface_names(self) -> List[str]:
        """
        获取所有网络接口名称列表
        
        Returns:
            List[str]: 网络接口名称列表
        """
        if not PSUTIL_AVAILABLE:
            return []
        
        try:
            return list(psutil.net_if_addrs().keys())
        except Exception as e:
            self.logger.error(f"获取接口名称列表失败: {str(e)}")
            return []
