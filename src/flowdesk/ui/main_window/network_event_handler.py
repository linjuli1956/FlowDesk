# -*- coding: utf-8 -*-
"""
网络配置事件处理器：协调各类网络事件处理器的主入口

重构说明：
原本的巨型事件处理器已拆分为三个专业处理器：
- NetworkAdapterEvents: 网卡选择、切换、刷新事件
- IPConfigurationEvents: IP配置、验证、应用事件
- NetworkStatusEvents: 网络状态、错误反馈、进度事件

本文件现在作为协调器，保持向后兼容的统一接口，采用门面模式委托给专业处理器。
"""

from PyQt5.QtWidgets import QMessageBox
from ...utils.logger import get_logger
from ...models.ip_config_confirmation import IPConfigConfirmation
from ..dialogs.ip_config_confirm_dialog import IPConfigConfirmDialog
from ..dialogs.operation_result_dialog import OperationResultDialog

# 导入拆分后的专业事件处理器
from .network_events.network_adapter_events import NetworkAdapterEvents
from .network_events.ip_configuration_events import IPConfigurationEvents
from .network_events.network_status_events import NetworkStatusEvents


class NetworkEventHandler:
    """
    网络配置事件处理器主协调器
    
    重构后的协调器模式实现，将原本的巨型事件处理器拆分为三个专业处理器：
    - adapter_events: 处理网卡选择、切换、刷新事件
    - ip_config_events: 处理IP配置、验证、应用事件  
    - status_events: 处理网络状态、错误反馈、进度事件
    
    设计原则：
    - 门面模式：提供统一接口，委托给专业处理器
    - 向后兼容：保持原有方法签名不变
    - 单一职责：每个专业处理器专注于特定事件类型
    """
    
    def __init__(self, main_window, network_service=None):
        """
        初始化网络事件处理器协调器
        
        Args:
            main_window: 主窗口实例，用于访问UI组件
            network_service: 网络服务实例，用于调用业务逻辑（可以稍后设置）
        """
        self.main_window = main_window
        self.network_service = network_service
        self.logger = get_logger(__name__)
        
        # 初始化专业事件处理器
        self.adapter_events = NetworkAdapterEvents(main_window, network_service)
        self.ip_config_events = IPConfigurationEvents(main_window, network_service)
        self.status_events = NetworkStatusEvents(main_window, network_service)
        
        # 如果网络服务已提供，立即连接信号
        if self.network_service:
            self._connect_signals()
    
    def set_network_service(self, network_service):
        """
        设置网络服务并连接信号
        
        Args:
            network_service: 网络服务实例
        """
        self.network_service = network_service
        print(f"NetworkEventHandler: 设置网络服务 - {network_service is not None}")
        
        # 为所有专业处理器设置网络服务
        self.adapter_events.set_network_service(network_service)
        self.ip_config_events.set_network_service(network_service)
        self.status_events.set_network_service(network_service)
        
        if self.network_service:
            self._connect_signals()
            print("NetworkEventHandler: 信号连接完成")
    
    def _connect_signals(self):
        """
        协调器模式的信号连接：委托给专业处理器
        
        注意：专业处理器已经在各自的_connect_signals方法中处理了信号连接，
        这里只需要确保它们都正确连接即可。
        """
        if not self.network_service:
            return
        
        # 专业处理器已经在初始化时连接了各自的信号
        # 这里只需要确认连接状态
        self.logger.debug("NetworkEventHandler协调器信号连接完成，委托给专业处理器")
    
    # ==================== 委托给专业处理器的方法 ====================
    # 以下方法保持向后兼容，委托给对应的专业处理器处理
    
    def _on_adapters_updated(self, adapters):
        """委托给适配器事件处理器"""
        return self.adapter_events._on_adapters_updated(adapters)
    
    def _on_adapter_selected(self, adapter_info):
        """委托给适配器事件处理器"""
        return self.adapter_events._on_adapter_selected(adapter_info)
    
    def _on_adapter_refreshed(self, adapter_info):
        """委托给适配器事件处理器"""
        return self.adapter_events._on_adapter_refreshed(adapter_info)
    
    def _on_ip_info_updated(self, ip_info):
        """委托给IP配置事件处理器"""
        return self.ip_config_events._on_ip_info_updated(ip_info)
    
    def _on_extra_ips_updated(self, extra_ips):
        """委托给IP配置事件处理器"""
        return self.ip_config_events._on_extra_ips_updated(extra_ips)
    
    def _on_ip_config_applied(self, success_message):
        """委托给IP配置事件处理器"""
        return self.ip_config_events._on_ip_config_applied(success_message)
    
    def _on_network_info_copied(self, success_message):
        """委托给状态事件处理器"""
        return self.status_events._on_network_info_copied(success_message)
    
    def _on_network_error(self, error_title, error_message):
        """委托给状态事件处理器"""
        return self.status_events._on_network_error(error_title, error_message)
    
    def _on_service_error(self, error_title, error_message):
        """委托给状态事件处理器"""
        return self.status_events._on_service_error(error_title, error_message)
    
    def _on_adapter_info_updated_for_status_bar(self, aggregated_info):
        """委托给状态事件处理器"""
        return self.status_events._on_adapter_info_updated_for_status_bar(aggregated_info)
    
    def _on_operation_completed(self, success, message, operation):
        """委托给状态事件处理器"""
        return self.status_events._on_operation_completed(success, message, operation)
    
    def _on_operation_progress(self, progress_message):
        """委托给状态事件处理器"""
        return self.status_events._on_operation_progress(progress_message)
    
    def _on_extra_ips_added(self, success_message):
        """委托给状态事件处理器"""
        return self.status_events._on_extra_ips_added(success_message)
    
    def _on_extra_ips_removed(self, success_message):
        """委托给状态事件处理器"""
        return self.status_events._on_extra_ips_removed(success_message)
    
    def _on_adapter_combo_changed(self, display_name):
        """委托给适配器事件处理器"""
        return self.adapter_events._on_adapter_combo_changed(display_name)
    
    def _get_current_selected_adapter(self):
        """委托给适配器事件处理器"""
        return self.adapter_events._get_current_selected_adapter()

    def _on_apply_ip_config(self, config_data):
        """委托给IP配置事件处理器"""
        return self.ip_config_events._on_apply_ip_config(config_data)
    
    def _apply_confirmed_ip_config(self, adapter_id, ip_address, subnet_mask, 
                                 gateway, primary_dns, secondary_dns, adapter_display_name, adapter_info=None):
        """委托给IP配置事件处理器的内部方法"""
        # 这个方法需要特殊处理，因为它在IP配置事件处理器中被调用
        # 为了保持兼容性，我们需要确保它能正确委托
        if hasattr(self.ip_config_events, '_apply_confirmed_ip_config'):
            return self.ip_config_events._apply_confirmed_ip_config(
                adapter_id, ip_address, subnet_mask, gateway, 
                primary_dns, secondary_dns, adapter_display_name, adapter_info
            )
        else:
            self.logger.error("IP配置事件处理器中未找到_apply_confirmed_ip_config方法")
    
    # ==================== 复杂业务逻辑方法的委托 ====================
    
    def _on_add_selected_extra_ips(self, adapter_id, selected_ips):
        """委托给IP配置事件处理器（如果有此方法）"""
        if hasattr(self.ip_config_events, '_on_add_selected_extra_ips'):
            return self.ip_config_events._on_add_selected_extra_ips(adapter_id, selected_ips)
        else:
            # 备用实现：直接调用服务层
            try:
                self.logger.debug(f"🔄 开始添加选中的额外IP - 网卡: {adapter_id}, IP数量: {len(selected_ips)}")
                if self.network_service:
                    self.network_service.add_selected_extra_ips(adapter_id, selected_ips)
            except Exception as e:
                self.logger.error(f"处理添加选中额外IP事件时发生异常: {str(e)}")

