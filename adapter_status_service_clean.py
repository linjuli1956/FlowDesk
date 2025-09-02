# -*- coding: utf-8 -*-
"""
网卡状态判断专用服务模块 - 清理版本
"""
from typing import Dict, Tuple

from .network_service_base import NetworkServiceBase


class AdapterStatusService(NetworkServiceBase):
    """
    网络适配器状态判断服务 - 委托给AdapterStatusAnalyzer
    """
    
    def __init__(self, parent=None):
        """初始化网络适配器状态判断服务"""
        super().__init__(parent)
        # 初始化发现服务依赖，用于GUID到连接名称的转换
        from .adapter_discovery_service import AdapterDiscoveryService
        from .adapter_status_analyzer import AdapterStatusAnalyzer
        self._discovery_service = AdapterDiscoveryService(self)
        self._status_analyzer = AdapterStatusAnalyzer()
        self._log_operation_start("AdapterStatusService初始化")
    
    def get_adapter_status(self, adapter_id_or_name: str, backup_status_code: str = '0') -> Tuple[str, bool, bool]:
        """
        获取网络适配器完整状态信息的主入口方法
        
        Args:
            adapter_id_or_name (str): 网卡GUID或友好名称
            backup_status_code (str): 备用的wmic状态码，默认为'0'
            
        Returns:
            Tuple[str, bool, bool]: (状态描述, 是否启用, 是否连接)
        """
        try:
            # 转换GUID为连接名称
            if adapter_id_or_name.startswith('{') and adapter_id_or_name.endswith('}'):
                adapter_info = self._discovery_service.get_adapter_by_guid(adapter_id_or_name)
                if adapter_info:
                    adapter_name = adapter_info.friendly_name
                else:
                    self.logger.warning(f"无法从GUID获取连接名称: {adapter_id_or_name}")
                    adapter_name = adapter_id_or_name
            else:
                adapter_name = adapter_id_or_name
                
            self._log_operation_start("获取网卡状态", adapter_name=adapter_name)
            
            # 委托给状态分析器获取精确状态
            interface_status = self._status_analyzer._get_interface_status_info(adapter_name)
            
            # 应用双重状态判断逻辑
            if interface_status['admin_status'] != '未知' or interface_status['connect_status'] != '未知':
                final_status, is_enabled, is_connected = self._status_analyzer.determine_final_status(
                    interface_status['admin_status'], 
                    interface_status['connect_status']
                )
                self.logger.debug(f"网卡 {adapter_name} 精确状态分析: 管理状态={interface_status['admin_status']}, 连接状态={interface_status['connect_status']}, 最终状态={final_status}")
            else:
                # netsh获取失败，使用备用wmic状态码方案
                self.logger.debug(f"网卡 {adapter_name} netsh状态获取失败，使用wmic状态码作为备用方案")
                final_status, is_enabled, is_connected = self._parse_wmic_status_code(backup_status_code, adapter_name)
            
            self._log_operation_success("获取网卡状态", f"网卡 {adapter_name}: {final_status}")
            return final_status, is_enabled, is_connected
            
        except Exception as e:
            self._log_operation_error("获取网卡状态", e)
            return '未知状态', False, False
    
    def get_interface_status_info(self, adapter_name: str) -> Dict[str, str]:
        """获取网卡接口状态信息的公开方法"""
        return self._status_analyzer._get_interface_status_info(adapter_name)
    
    def determine_final_status(self, admin_status: str, connect_status: str) -> Tuple[str, bool, bool]:
        """基于管理状态和连接状态确定最终状态的公开方法"""
        return self._status_analyzer.determine_final_status(admin_status, connect_status)
    
    def _parse_wmic_status_code(self, status_code: str, adapter_name: str) -> Tuple[str, bool, bool]:
        """解析wmic状态码的备用方案"""
        return self._status_analyzer._parse_wmic_status_code(status_code, adapter_name)
