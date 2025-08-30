# -*- coding: utf-8 -*-
"""
网络服务兼容门面模块

这个文件是FlowDesk网络管理架构中的"兼容门面"，专门负责保持与原有NetworkService接口的完全兼容性。
它解决了大规模重构后的向后兼容问题，通过门面模式将原有的单体服务接口委托给拆包后的专业服务模块。
UI层和其他组件可以无缝地继续使用原有的方法调用，而底层实现已经完全模块化和专业化。
该门面严格遵循开闭原则，在不修改现有调用代码的前提下，实现了架构的彻底改进。
"""

from typing import List, Dict, Any, Optional
from PyQt5.QtCore import QObject

from .network_service_base import NetworkServiceBase
from .adapter_discovery_service import AdapterDiscoveryService
from .adapter_info_service import AdapterInfoService
from .adapter_status_service import AdapterStatusService
from .adapter_performance_service import AdapterPerformanceService
from .ip_configuration_service import IPConfigurationService
from .extra_ip_management_service import ExtraIPManagementService
from .network_ui_coordinator_service import NetworkUICoordinatorService


class NetworkService(NetworkServiceBase):
    """
    网络服务兼容门面类
    
    这是FlowDesk网络管理系统的统一入口点，保持与原有NetworkService完全相同的接口。
    通过门面模式将所有网络操作委托给相应的专业服务模块，实现了代码的模块化重构。
    
    架构优势：
    - 向后兼容：UI层无需修改任何调用代码
    - 模块化：底层实现完全解耦和专业化
    - 可维护：每个专业服务职责清晰，便于维护
    - 可扩展：新功能可通过添加新服务模块实现
    
    主要功能：
    - 网卡发现与枚举
    - 网卡详细信息获取
    - 网卡状态判断
    - 网卡性能监控
    - IP配置应用
    - 额外IP管理
    - UI事件协调
    """
    
    def __init__(self, parent: QObject = None):
        """
        初始化网络服务门面
        
        创建所有专业服务实例并建立服务间的依赖关系。
        通过依赖注入模式确保各服务之间的松耦合协作。
        
        Args:
            parent: PyQt父对象，用于内存管理
        """
        super().__init__(parent)
        self._log_operation_start("NetworkService门面初始化")
        
        # 创建专业服务实例
        self._discovery_service = AdapterDiscoveryService(parent=self)
        self._info_service = AdapterInfoService(parent=self)
        self._status_service = AdapterStatusService(parent=self)
        self._performance_service = AdapterPerformanceService(parent=self)
        self._ip_config_service = IPConfigurationService(parent=self)
        self._extra_ip_service = ExtraIPManagementService(parent=self)
        self._ui_coordinator = NetworkUICoordinatorService(parent=self)
        
        # 建立服务间的依赖关系
        self._setup_service_dependencies()
        
        # 连接各服务的信号到门面信号
        self._connect_service_signals()
        
        # 缓存当前选中的网卡信息（保持原有接口兼容性）
        self._current_adapter_id = None
        self._adapters = []
        
        self.logger.info("网络服务门面初始化完成，所有专业服务已就绪")
    
    # region 服务初始化
    
    def _setup_service_dependencies(self):
        """
        建立各专业服务之间的依赖关系
        
        通过依赖注入模式确保UI协调器能够访问所有必要的服务，
        实现统一的操作协调和状态管理。
        """
        # 为UI协调器注入所有专业服务
        self._ui_coordinator.set_discovery_service(self._discovery_service)
        self._ui_coordinator.set_info_service(self._info_service)
        self._ui_coordinator.set_status_service(self._status_service)
        self._ui_coordinator.set_performance_service(self._performance_service)
        self._ui_coordinator.set_ip_config_service(self._ip_config_service)
        self._ui_coordinator.set_extra_ip_service(self._extra_ip_service)
        
        self.logger.info("服务依赖关系建立完成")
    
    def _connect_service_signals(self):
        """
        连接各专业服务的信号到门面的统一信号
        
        这确保了UI层继续能够接收到所有原有的信号通知，
        保持了完整的向后兼容性。
        """
        # 连接UI协调器的信号（作为主要信号源）
        self._ui_coordinator.adapters_updated.connect(self.adapters_updated)
        self._ui_coordinator.adapters_updated.connect(self._update_adapters_cache)  # 添加缓存同步
        self._ui_coordinator.adapter_info_updated.connect(self._debug_adapter_info_signal)  # 添加调试日志
        self._ui_coordinator.adapter_info_updated.connect(self.adapter_info_updated)
        
        # 连接IP配置和额外IP相关信号（修复信号转发缺失问题）
        self._ui_coordinator.ip_info_updated.connect(self.ip_info_updated)
        self._ui_coordinator.extra_ips_updated.connect(self.extra_ips_updated)
        
        # 连接通用操作信号
        self._ui_coordinator.operation_progress.connect(self.operation_progress)
        self._ui_coordinator.error_occurred.connect(self.error_occurred)
        
        # 连接IP配置服务的信号
        self._ip_config_service.ip_config_applied.connect(self.ip_config_applied)
        
        # 连接额外IP管理服务的信号
        self._extra_ip_service.extra_ips_added.connect(self.extra_ips_added)
        self._extra_ip_service.extra_ips_removed.connect(self.extra_ips_removed)
        
        self.logger.info("网络服务信号连接完成")
    
    def _debug_adapter_info_signal(self, aggregated_info):
        """调试adapter_info_updated信号转发"""
        self.logger.info(f"NetworkService收到adapter_info_updated信号 - 网卡ID: {aggregated_info.get('adapter_id', 'Unknown')}")
        self.logger.info(f"NetworkService即将转发adapter_info_updated信号给UI层")
        # 手动发射信号确保转发
        self.logger.info(f"手动发射adapter_info_updated信号")
        self.adapter_info_updated.emit(aggregated_info)
    
    def _update_adapters_cache(self, adapters):
        """
        更新NetworkService facade的网卡缓存
        
        这个方法响应UI协调器的adapters_updated信号，
        确保facade层的_adapters缓存与实际发现的网卡列表保持同步。
        这是修复网卡选择匹配失败问题的关键方法。
        
        Args:
            adapters: 网卡对象列表
        """
        try:
            self._adapters = adapters if adapters else []
            self.logger.info(f"网卡缓存已更新，当前缓存网卡数量: {len(self._adapters)}")
            
            # 调试输出缓存的网卡信息
            for adapter in self._adapters:
                self.logger.debug(f"缓存网卡: name='{adapter.name}', friendly_name='{adapter.friendly_name}', description='{adapter.description}'")
                
        except Exception as e:
            self.logger.error(f"更新网卡缓存失败: {str(e)}")
    
    # endregion
    
    # region 网卡发现与枚举接口（兼容原有方法）
    
    def discover_all_adapters(self) -> List[Dict[str, Any]]:
        """
        发现所有网络适配器的兼容接口方法
        
        委托给AdapterDiscoveryService执行实际的网卡发现逻辑。
        保持与原有方法完全相同的接口和返回值格式。
        
        Returns:
            List[Dict[str, Any]]: 网卡信息列表，每个元素包含网卡的基本信息
        """
        try:
            self._log_operation_start("发现所有网卡")
            
            # 委托给专业发现服务
            adapters = self._discovery_service.discover_all_adapters()
            
            # 更新本地缓存以保持兼容性
            if adapters is not None:
                self._adapters = adapters
                # 同时更新额外IP管理服务的缓存
                self._extra_ip_service.set_adapters_cache(adapters)
                self._log_operation_success("发现所有网卡", f"成功发现{len(adapters)}个网卡")
            
            return adapters
            
        except Exception as e:
            self._log_operation_error("发现所有网卡", e)
            return []
    
    def refresh_adapters_list(self):
        """
        刷新网卡列表的兼容接口方法
        
        委托给UI协调器执行统一的刷新逻辑。
        """
        try:
            self._log_operation_start("刷新网卡列表")
            
            # 委托给UI协调器
            self._ui_coordinator.refresh_adapters_list()
            
        except Exception as e:
            self._log_operation_error("刷新网卡列表", e)
    
    def get_all_adapters(self):
        """
        获取所有网络适配器信息 - 主要UI初始化接口
        
        这是MainWindow初始化时调用的关键方法，负责启动网卡发现流程。
        委托给UI协调器执行完整的网卡获取和信号发射逻辑。
        """
        try:
            self._log_operation_start("获取所有网卡信息")
            
            # 委托给UI协调器执行完整的网卡列表刷新流程
            self._ui_coordinator.refresh_adapters_list()
            
        except Exception as e:
            self._log_operation_error("获取所有网卡信息", e)
    
    def copy_adapter_info(self):
        """
        复制网卡信息的兼容接口方法
        
        委托给UI协调器执行网卡信息复制操作。
        """
        try:
            self._log_operation_start("复制网卡信息")
            
            # 委托给UI协调器
            self._ui_coordinator.copy_current_adapter_info()
            
        except Exception as e:
            self._log_operation_error("复制网卡信息", e)
    
    def get_adapters(self) -> List[Dict[str, Any]]:
        """
        获取当前缓存的网卡列表
        
        Returns:
            List[Dict[str, Any]]: 当前缓存的网卡信息列表
        """
        return self._adapters.copy()
    
    def select_adapter(self, adapter_id: str):
        """
        选择指定网络适配器的facade接口方法
        
        这是UI层选择网卡时调用的关键方法，负责设置当前活动网卡
        并触发相关信息的获取和显示更新。委托给UI协调器执行。
        
        Args:
            adapter_id (str): 网络适配器GUID标识符
        """
        try:
            self._log_operation_start("选择网卡", adapter_id=adapter_id)
            
            # 委托给UI协调器执行网卡选择逻辑
            self._ui_coordinator.set_current_adapter(adapter_id)
            
            # 更新本地状态
            self._current_adapter_id = adapter_id
            
        except Exception as e:
            self._log_operation_error("选择网卡", e)
    
    # endregion
    
    # region 网卡信息获取接口（兼容原有方法）
    
    def get_adapter_detailed_info(self, adapter_id: str) -> Optional[Dict[str, Any]]:
        """
        获取网卡详细信息的兼容接口方法
        
        Args:
            adapter_id: 网卡GUID标识符
            
        Returns:
            Optional[Dict[str, Any]]: 网卡详细信息，获取失败返回None
        """
        try:
            self._log_operation_start("获取网卡详细信息", adapter_id=adapter_id)
            
            # 委托给专业信息服务
            detailed_info = self._info_service.get_adapter_detailed_info(adapter_id)
            
            if detailed_info:
                self._log_operation_success("获取网卡详细信息", "信息获取成功")
            
            return detailed_info
            
        except Exception as e:
            self._log_operation_error("获取网卡详细信息", e)
            return None
    
    def get_adapter_status(self, adapter_id: str) -> str:
        """
        获取网卡状态的兼容接口方法
        
        Args:
            adapter_id: 网卡GUID标识符
            
        Returns:
            str: 网卡状态描述
        """
        try:
            self._log_operation_start("获取网卡状态", adapter_id=adapter_id)
            
            # 委托给专业状态服务
            status = self._status_service.get_adapter_status(adapter_id)
            
            self._log_operation_success("获取网卡状态", f"状态: {status}")
            return status
            
        except Exception as e:
            self._log_operation_error("获取网卡状态", e)
            return "未知"
    
    def get_link_speed_info(self, adapter_name: str) -> str:
        """
        获取网卡链路速度的兼容接口方法
        
        Args:
            adapter_name: 网卡友好名称
            
        Returns:
            str: 格式化的链路速度字符串
        """
        try:
            self._log_operation_start("获取链路速度", adapter_name=adapter_name)
            
            # 委托给专业性能服务
            speed = self._performance_service.get_link_speed_info(adapter_name)
            
            self._log_operation_success("获取链路速度", f"速度: {speed}")
            return speed
            
        except Exception as e:
            self._log_operation_error("获取链路速度", e)
            return "未知"
    
    # endregion
    
    # region IP配置管理接口（兼容原有方法）
    
    def apply_ip_config(self, adapter_id: str, ip_address: str, subnet_mask: str, 
                       gateway: str = '', primary_dns: str = '', secondary_dns: str = '') -> bool:
        """
        应用IP配置的兼容接口方法
        
        Args:
            adapter_id: 目标网卡的GUID标识符
            ip_address: 要设置的IP地址
            subnet_mask: 子网掩码
            gateway: 默认网关地址，可选
            primary_dns: 主DNS服务器地址，可选
            secondary_dns: 辅助DNS服务器地址，可选
            
        Returns:
            bool: 配置应用成功返回True，失败返回False
        """
        try:
            self._log_operation_start("应用IP配置", adapter_id=adapter_id)
            
            # 委托给UI协调器执行统一的配置流程
            self._ui_coordinator.apply_ip_configuration(
                adapter_id, ip_address, subnet_mask, gateway, primary_dns, secondary_dns
            )
            
            return True
            
        except Exception as e:
            self._log_operation_error("应用IP配置", e)
            return False
    
    def add_selected_extra_ips(self, adapter_name: str, ip_configs: List[str]):
        """
        批量添加额外IP的兼容接口方法
        
        Args:
            adapter_name: 目标网卡的友好名称
            ip_configs: IP配置字符串列表
        """
        try:
            self._log_operation_start("批量添加额外IP", adapter_name=adapter_name)
            
            # 委托给UI协调器执行统一的添加流程
            self._ui_coordinator.add_extra_ips(adapter_name, ip_configs)
            
        except Exception as e:
            self._log_operation_error("批量添加额外IP", e)
    
    def remove_selected_extra_ips(self, adapter_name: str, ip_configs: List[str]):
        """
        批量删除额外IP的兼容接口方法
        
        Args:
            adapter_name: 目标网卡的友好名称
            ip_configs: 待删除的IP配置列表
        """
        try:
            self._log_operation_start("批量删除额外IP", adapter_name=adapter_name)
            
            # 委托给UI协调器执行统一的删除流程
            self._ui_coordinator.remove_extra_ips(adapter_name, ip_configs)
            
        except Exception as e:
            self._log_operation_error("批量删除额外IP", e)
    
    # endregion
    
    # region 当前网卡管理接口（兼容原有方法）
    
    def set_current_adapter(self, adapter_id: str):
        """
        设置当前选中网卡的兼容接口方法
        
        Args:
            adapter_id: 选中的网卡GUID标识符
        """
        try:
            self._log_operation_start("设置当前网卡", adapter_id=adapter_id)
            
            # 更新本地缓存
            self._current_adapter_id = adapter_id
            
            # 委托给UI协调器执行统一的切换流程
            self._ui_coordinator.set_current_adapter(adapter_id)
            
        except Exception as e:
            self._log_operation_error("设置当前网卡", e)
    
    def refresh_current_adapter(self):
        """
        刷新当前网卡信息的兼容接口方法
        """
        try:
            self._log_operation_start("刷新当前网卡信息")
            
            # 委托给UI协调器执行统一的刷新流程
            self._ui_coordinator.refresh_current_adapter()
            
        except Exception as e:
            self._log_operation_error("刷新当前网卡信息", e)
    
    def get_current_adapter_id(self) -> Optional[str]:
        """
        获取当前选中的网卡ID
        
        Returns:
            Optional[str]: 当前网卡ID，未选择时返回None
        """
        return self._current_adapter_id
    
    # endregion
    
    # region 服务状态查询接口
    
    def is_service_ready(self) -> bool:
        """
        检查网络服务是否已就绪
        
        Returns:
            bool: 所有专业服务都已初始化时返回True
        """
        return self._ui_coordinator.is_service_ready()
    
    def get_service_status(self) -> Dict[str, bool]:
        """
        获取各专业服务的状态
        
        Returns:
            Dict[str, bool]: 各服务的可用状态字典
        """
        return self._ui_coordinator.get_service_status()
    
    # endregion
