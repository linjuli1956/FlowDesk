# -*- coding: utf-8 -*-
"""
网卡信息获取主协调器｜整合各专业服务，提供网卡详细信息获取的统一入口
"""
import logging
from typing import Optional
from datetime import datetime

from .network_service_base import NetworkServiceBase
from .adapter_status_analyzer import AdapterStatusAnalyzer
from .adapter_config_parser import AdapterConfigParser
from .adapter_dns_enhancer import AdapterDnsEnhancer
from .adapter_info_utils import get_interface_type
from flowdesk.models import AdapterInfo


class AdapterInfoRetriever(NetworkServiceBase):
    """
    网卡信息获取主协调器
    
    作为网卡详细信息获取的统一入口，协调各个专业服务组件。
    遵循面向对象设计原则，通过依赖注入和服务组合实现功能。
    
    主要功能：
    - 协调状态分析器、配置解析器、DNS增强器等专业服务
    - 整合多重数据源，构造完整的AdapterInfo对象
    - 提供统一的错误处理和日志记录机制
    - 确保链路速度等性能信息的完整获取
    
    架构优势：
    - 单一职责：专注于服务协调，不包含具体业务逻辑
    - 依赖注入：各专业服务可独立测试和替换
    - 开闭原则：新增功能通过扩展服务组件实现
    """
    
    def __init__(self, parent=None):
        """
        初始化网卡信息获取协调器
        
        Args:
            parent: PyQt父对象，用于内存管理
        """
        super().__init__(parent)
        
        # 初始化专业服务组件
        self.status_analyzer = AdapterStatusAnalyzer()
        self.config_parser = AdapterConfigParser()
        self.dns_enhancer = AdapterDnsEnhancer()
        
        # 初始化发现服务依赖，用于获取网卡基本信息
        from .adapter_discovery_service import AdapterDiscoveryService
        self._discovery_service = AdapterDiscoveryService(self)
        
        self._log_operation_start("AdapterInfoRetriever初始化")
    
    def get_adapter_detailed_info(self, adapter_id: str) -> Optional[AdapterInfo]:
        """
        获取网络适配器详细信息的主入口方法
        
        这个方法是获取网卡完整信息的核心入口，整合了多个专业服务的信息获取能力。
        基于网卡GUID，首先获取基本信息，再通过各专业服务获取详细配置，
        构造完整的AdapterInfo对象。
        
        技术架构特点：
        - 服务协调：统一调度各专业服务组件
        - 多重数据源：结合netsh和ipconfig命令的优势
        - 增强DNS获取：使用专门的DNS配置获取逻辑
        - 状态精确判断：结合管理状态和连接状态的双重判断
        - 完整对象构造：创建包含所有必要信息的AdapterInfo对象
        
        Args:
            adapter_id (str): 网卡GUID标识符
            
        Returns:
            Optional[AdapterInfo]: 完整的网卡信息对象，失败时返回None
        """
        try:
            # 首先根据GUID获取网卡基本信息
            basic_info = self._discovery_service.get_adapter_basic_info(adapter_id)
            if not basic_info:
                self.logger.warning(f"无法获取网卡基本信息: {adapter_id}")
                return None
            
            adapter_name = basic_info.get('NetConnectionID', '')
            if not adapter_name:
                return None
            
            self._log_operation_start("获取网卡详细信息", adapter_name=adapter_name)
            
            # 使用配置解析器获取IP配置信息
            ip_config = self.config_parser.get_adapter_ip_config(adapter_name)
            
            # 确保链路速度信息在创建AdapterInfo对象前已获取
            if not ip_config.get('link_speed'):
                # 直接通过性能服务获取链路速度，确保数据完整性
                from .adapter_performance_service import AdapterPerformanceService
                performance_service = AdapterPerformanceService()
                link_speed = performance_service.get_link_speed_info(adapter_name)
                ip_config['link_speed'] = link_speed
                self.logger.debug(f"补充获取网卡 {adapter_name} 链路速度: {link_speed}")
            
            # 使用DNS增强器增强DNS配置
            enhanced_dns = self.dns_enhancer.enhance_dns_config(
                adapter_name, 
                ip_config.get('dns_servers', [])
            )
            ip_config['dns_servers'] = enhanced_dns
            
            # 使用状态分析器获取精确的网卡状态
            final_status, is_adapter_enabled, is_adapter_connected = self.status_analyzer.analyze_adapter_status(
                adapter_name, 
                basic_info
            )
            
            # 构造完整的网卡信息对象
            # 采用面向对象设计，将所有网卡相关数据封装在AdapterInfo类中
            adapter_info = AdapterInfo(
                id=basic_info.get('GUID', ''),                    # 网卡全局唯一标识符
                name=basic_info.get('Name', ''),                  # 网卡完整名称（系统内部使用）
                friendly_name=adapter_name,                       # 网卡友好名称（用户界面显示）
                description=basic_info.get('Description', ''),    # 网卡硬件描述信息
                mac_address=basic_info.get('MACAddress', ''),     # 网卡物理MAC地址
                status=final_status,                              # 网卡当前连接状态的中文描述
                is_enabled=is_adapter_enabled,                    # 网卡是否处于启用状态
                is_connected=is_adapter_connected,                # 网卡是否已连接到网络
                ip_addresses=ip_config.get('ip_addresses', []),
                ipv6_addresses=ip_config.get('ipv6_addresses', []),
                subnet_masks=ip_config.get('subnet_masks', []),
                gateway=ip_config.get('gateway', ''),
                dns_servers=ip_config.get('dns_servers', []),
                dhcp_enabled=ip_config.get('dhcp_enabled', True),
                link_speed=ip_config.get('link_speed', ''),
                interface_type=get_interface_type(basic_info.get('Description', '')),
                last_updated=datetime.now()
            )
            
            self._log_operation_success("获取网卡详细信息", f"网卡: {adapter_name}")
            return adapter_info
            
        except Exception as e:
            self._log_operation_error("获取网卡详细信息", e)
            return None
    
    def get_adapter_ip_config(self, adapter_name: str) -> dict:
        """
        获取指定网卡IP配置信息的公共接口
        
        这个方法提供向后兼容的接口，委托给配置解析器处理。
        
        Args:
            adapter_name (str): 网卡连接名称，如"vEthernet (泰兴)"
            
        Returns:
            dict: 包含完整IP配置信息的字典
        """
        return self.config_parser.get_adapter_ip_config(adapter_name)
