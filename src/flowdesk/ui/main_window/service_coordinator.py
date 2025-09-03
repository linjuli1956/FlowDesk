# -*- coding: utf-8 -*-
"""
服务层协调器：负责服务初始化和信号连接管理
"""

from ...utils.logger import get_logger
from ...services import NetworkService, StatusBarService
from ...services.network.adapter_status_service import AdapterStatusService


class ServiceCoordinator:
    """
    服务层协调器
    
    负责服务初始化和信号槽连接管理，实现UI层与服务层的双向通信：
    1. UI信号 -> 服务层方法：用户操作触发业务逻辑
    2. 服务层信号 -> UI更新方法：业务逻辑完成后更新界面
    
    严格遵循分层架构：UI层零业务逻辑，服务层零UI操作。
    """
    
    def __init__(self, main_window):
        """
        初始化服务协调器
        
        Args:
            main_window: 主窗口实例，用于访问UI组件和连接信号
        """
        self.main_window = main_window
        self.logger = get_logger(__name__)
        
        # 初始化服务层组件
        self.network_service = None
        self.status_bar_service = None
        self.adapter_status_service = None
    
    def initialize_services(self):
        """
        初始化所有服务层组件（仅创建服务实例，不连接信号）
        
        拆包后需要延迟注入：先创建服务实例，等network_event_handler设置完成后
        再通过inject_and_connect()方法连接信号并启动服务功能。
        """
        self._initialize_services_only()
    
    def inject_and_connect(self):
        """
        延迟注入接口：在network_event_handler设置network_service后调用
        
        连接所有信号槽并启动服务功能，确保事件处理器已准备就绪。
        """
        self._connect_all_signals()
        self._start_services()
    
    def _initialize_services_only(self):
        """
        仅初始化服务实例，不连接信号不启动功能
        
        创建NetworkService实例等服务组件，但不触发任何可能发射信号的操作。
        这样可以确保在network_event_handler设置network_service前不会触发事件。
        """
        try:
            # 创建网络服务实例
            self.network_service = NetworkService()
            self.logger.info("网络服务初始化完成")
            
            # 创建状态栏服务实例
            self.status_bar_service = StatusBarService()
            self.logger.info("状态栏服务初始化完成")
            
            # 创建网卡状态服务实例
            self.adapter_status_service = AdapterStatusService()
            self.logger.info("网卡状态服务初始化完成")
            
            # 将服务实例设置到主窗口，供其他组件使用
            self.main_window.network_service = self.network_service
            self.main_window.status_bar_service = self.status_bar_service
            
        except Exception as e:
            error_msg = f"服务层初始化失败: {str(e)}"
            self.logger.error(error_msg)
            # 服务初始化失败不影响UI显示，但功能会受限
    
    def _connect_all_signals(self):
        """
        连接所有信号槽，在network_service设置完成后安全执行
        """
        try:
            # 连接网络配置Tab的信号槽
            self._connect_network_config_signals()
            
            # 连接状态栏的信号槽
            self._connect_status_bar_signals()
            
            self.logger.info("所有信号连接完成")
            
        except Exception as e:
            error_msg = f"信号连接失败: {str(e)}"
            self.logger.error(error_msg)
    
    def _start_services(self):
        """
        启动服务功能，在信号连接完成后安全触发初始数据加载
        """
        try:
            # 现在可以安全地触发网卡数据加载，因为事件处理器已准备就绪
            self.network_service.get_all_adapters()
            
            # 启动状态栏初始化：显示应用启动状态
            self.status_bar_service.set_status("🚀 应用启动完成", auto_clear_seconds=3)
            
            self.logger.info("所有服务核心功能启动完成")
            
        except Exception as e:
            error_msg = f"服务启动失败: {str(e)}"
            self.logger.error(error_msg)
    
    def _connect_network_config_signals(self):
        """
        连接网络配置Tab的信号槽通信
        
        实现UI层与服务层的双向通信：
        1. UI信号 -> 服务层方法：用户操作触发业务逻辑
        2. 服务层信号 -> UI更新方法：业务逻辑完成后更新界面
        
        严格遵循分层架构：UI层零业务逻辑，服务层零UI操作。
        """
        # 获取事件处理器和状态管理器的引用
        event_handler = getattr(self.main_window, 'network_event_handler', None)
        state_manager = getattr(self.main_window, 'ui_state_manager', None)
        
        # === UI信号连接到服务层方法 ===
        
        # 网卡选择变更：UI下拉框选择 -> 事件处理器转换 -> 服务层选择网卡
        self.main_window.network_config_tab.adapter_selected.connect(
            event_handler._on_adapter_combo_changed if event_handler else self._fallback_adapter_combo_changed
        )
        
        # 刷新网卡列表：UI刷新按钮 -> 服务层刷新当前网卡
        self.main_window.network_config_tab.refresh_adapters.connect(
            self.network_service.refresh_current_adapter
        )
        
        # 复制网卡信息：UI复制按钮 -> 服务层复制信息到剪贴板
        self.main_window.network_config_tab.copy_adapter_info.connect(
            self.network_service.copy_adapter_info
        )
        
        # IP配置应用：UI修改IP按钮 -> 事件处理器转换 -> 服务层应用IP配置
        self.main_window.network_config_tab.apply_ip_config.connect(
            event_handler._on_apply_ip_config if event_handler else self._fallback_apply_ip_config
        )
        
        # 批量添加选中IP：UI添加选中按钮 -> 事件处理器 -> 服务层批量添加额外IP
        self.main_window.network_config_tab.add_selected_ips.connect(
            event_handler._on_add_selected_extra_ips if event_handler else self._fallback_add_selected_ips
        )
        
        # 批量删除选中IP：UI删除选中按钮 -> 服务层批量删除额外IP
        self.main_window.network_config_tab.remove_selected_ips.connect(
            self.network_service.remove_selected_extra_ips
        )
        
        # === 网卡操作信号连接 ===
        
        # 启用网卡：UI启用按钮 -> 服务层启用网卡
        self.main_window.network_config_tab.enable_adapter.connect(
            self.network_service.enable_adapter
        )
        
        # 禁用网卡：UI禁用按钮 -> 服务层禁用网卡
        self.main_window.network_config_tab.disable_adapter.connect(
            self.network_service.disable_adapter
        )
        
        # 设置DHCP：UI DHCP按钮 -> 服务层设置DHCP模式
        self.main_window.network_config_tab.set_dhcp.connect(
            self.network_service.set_dhcp_mode
        )
        
        # 修改MAC地址：UI修改MAC按钮 -> 事件处理器处理
        self.main_window.network_config_tab.modify_mac_address.connect(
            event_handler._on_modify_mac_address if event_handler else self._fallback_modify_mac_address
        )
        
        # === 服务层信号连接到UI更新方法 ===
        
        # 网卡列表更新：服务层获取网卡完成 -> UI更新下拉框
        self.network_service.adapters_updated.connect(
            state_manager._on_adapters_updated if state_manager else self._fallback_adapters_updated
        )
        
        # 网卡选择完成：服务层选择网卡完成 -> UI更新显示信息
        self.network_service.adapter_selected.connect(
            state_manager._on_adapter_selected if state_manager else self._fallback_adapter_selected
        )
        
        # 网卡信息更新完成：服务层刷新网卡信息完成 -> UI更新IP信息显示和状态徽章
        self.network_service.adapter_info_updated.connect(
            state_manager._on_adapter_info_updated if state_manager else self._fallback_adapter_info_updated
        )
        
        # IP配置信息更新：服务层解析IP配置 -> UI更新输入框和信息显示
        self.network_service.ip_info_updated.connect(
            state_manager._on_ip_info_updated if state_manager else self._fallback_ip_info_updated
        )
        
        # 额外IP列表更新：服务层解析额外IP -> UI更新额外IP列表
        self.network_service.extra_ips_updated.connect(
            state_manager._on_extra_ips_updated if state_manager else self._fallback_extra_ips_updated
        )
        
        # 网卡刷新完成：服务层刷新完成 -> UI显示刷新成功提示
        self.network_service.adapter_refreshed.connect(
            state_manager._on_adapter_refreshed if state_manager else self._fallback_adapter_refreshed
        )
        
        # 信息复制完成：服务层复制完成 -> UI显示复制成功提示
        self.network_service.network_info_copied.connect(
            state_manager._on_info_copied if state_manager else self._fallback_info_copied
        )
        
        # 状态徽章更新：Service层格式化完成 -> UI直接显示
        self.network_service.status_badges_updated.connect(
            self.main_window.network_config_tab.adapter_info_panel.update_status_badges
        )
        
        # 错误处理：服务层发生错误 -> UI显示错误信息
        self.network_service.error_occurred.connect(
            event_handler._on_service_error if event_handler else self._fallback_service_error
        )
        
        # IP配置应用完成：服务层配置完成 -> UI显示成功提示
        self.network_service.ip_config_applied.connect(
            event_handler._on_ip_config_applied if event_handler else self._fallback_ip_config_applied
        )
        
        # 操作进度更新：服务层操作进度 -> UI显示进度信息
        self.network_service.operation_progress.connect(
            event_handler._on_operation_progress if event_handler else self._fallback_operation_progress
        )
        
        # 批量额外IP添加完成：服务层批量添加完成 -> UI显示操作结果
        self.network_service.extra_ips_added.connect(
            event_handler._on_extra_ips_added if event_handler else self._fallback_extra_ips_added
        )
        
        # 批量额外IP删除完成：服务层批量删除完成 -> UI显示操作结果
        self.network_service.extra_ips_removed.connect(
            event_handler._on_extra_ips_removed if event_handler else self._fallback_extra_ips_removed
        )
        
        # 网卡操作完成：服务层网卡操作完成 -> UI显示操作结果弹窗
        self.network_service.operation_completed.connect(
            event_handler._on_operation_completed if event_handler else self._fallback_operation_completed
        )
    
    def _connect_status_bar_signals(self):
        """
        连接状态栏的信号槽通信
        
        实现状态栏服务与UI组件的信号连接：
        - 状态信息更新信号 -> 状态栏UI更新
        - 版本信息更新信号 -> 状态栏版本显示更新
        """
        # 状态信息更新：服务层状态变更 -> UI状态栏更新状态显示
        self.status_bar_service.status_updated.connect(
            self.main_window.status_bar.update_status
        )
        
        # 版本信息更新：服务层版本变更 -> UI状态栏更新版本显示
        self.status_bar_service.version_updated.connect(
            self.main_window.status_bar.update_version
        )
    
    def cleanup_services(self):
        """
        清理服务层资源
        
        在应用程序退出时清理服务层资源，确保优雅关闭。
        """
        try:
            if self.network_service:
                # 这里可以添加网络服务清理逻辑
                self.logger.debug("网络服务资源已清理")
            
            if self.status_bar_service:
                # 清理状态栏服务资源
                self.status_bar_service.cleanup()
                self.logger.debug("状态栏服务资源已清理")
                
        except Exception as e:
            self.logger.error(f"清理服务层资源失败: {e}")
    
    # === 回退方法：在组件未初始化时提供基本功能 ===
    
    def _fallback_adapter_combo_changed(self, display_name):
        """网卡选择变更的回退处理"""
        self.logger.warning("事件处理器未初始化，使用回退方法处理网卡选择")
        # 基本的网卡选择逻辑
        pass
    
    def _fallback_apply_ip_config(self, config_data):
        """事件处理器不可用时的IP配置应用回退方法"""
        self.logger.warning("事件处理器不可用，使用回退方法处理IP配置应用")
        
        # 直接调用UI协调器的IP配置方法
        if self.network_service and hasattr(self.network_service, '_ui_coordinator'):
            try:
                # 获取当前选中的网卡ID
                current_adapter_text = getattr(self.main_window.network_config_tab.adapter_info_panel.adapter_combo, 'currentText', lambda: '')()
                if not current_adapter_text:
                    self.logger.error("未选择网卡，无法应用IP配置")
                    return
                
                # 从网卡映射中获取真实的网卡ID
                adapter_name_mapping = getattr(self.main_window.network_config_tab, '_adapter_name_mapping', {})
                adapter_id = adapter_name_mapping.get(current_adapter_text, current_adapter_text)
                
                # 提取配置数据
                ip_address = config_data.get('ip_address', '')
                subnet_mask = config_data.get('subnet_mask', '')
                gateway = config_data.get('gateway', '')
                primary_dns = config_data.get('primary_dns', '')
                secondary_dns = config_data.get('secondary_dns', '')
                
                self.logger.info(f"回退方法应用IP配置: 网卡={adapter_id}, IP={ip_address}")
                
                # 调用UI协调器的IP配置应用方法
                self.network_service._ui_coordinator.apply_ip_config(
                    adapter_id, ip_address, subnet_mask, gateway, primary_dns, secondary_dns
                )
                
            except Exception as e:
                self.logger.error(f"回退方法应用IP配置失败: {str(e)}")
        else:
            self.logger.error("网络服务或UI协调器不可用，无法应用IP配置")
    
    def _fallback_add_selected_ips(self, adapter_name: str, ip_configs: list):
        """事件处理器不可用时的添加额外IP回退方法"""
        self.logger.warning("事件处理器不可用，使用回退方法处理添加额外IP")
        if self.network_service:
            self.network_service.add_selected_extra_ips(adapter_name, ip_configs)
        pass
    
    def _fallback_adapters_updated(self, adapters):
        """网卡列表更新的回退处理"""
        self.logger.warning("状态管理器未初始化，使用回退方法处理网卡列表更新")
        # 基本的网卡列表更新逻辑
        pass
    
    def _fallback_adapter_selected(self, adapter_info):
        """网卡选择完成的回退处理"""
        self.logger.warning("状态管理器未初始化，使用回退方法处理网卡选择完成")
        # 基本的网卡选择完成逻辑
        pass
    
    def _fallback_adapter_info_updated(self, aggregated_info):
        """网卡信息更新的回退处理"""
        self.logger.warning("状态管理器未初始化，使用回退方法处理网卡信息更新")
        # 基本的网卡信息更新逻辑
        pass
    
    def _fallback_ip_info_updated(self, ip_config):
        """IP配置信息更新的回退处理"""
        self.logger.warning("状态管理器未初始化，使用回退方法处理IP配置更新")
        # 基本的IP配置更新逻辑
        pass
    
    def _fallback_extra_ips_updated(self, extra_ips):
        """额外IP列表更新的回退处理"""
        self.logger.warning("状态管理器未初始化，使用回退方法处理额外IP更新")
        # 基本的额外IP更新逻辑
        pass
    
    def _fallback_adapter_refreshed(self, adapter_info):
        """网卡刷新完成的回退处理"""
        self.logger.warning("状态管理器未初始化，使用回退方法处理网卡刷新")
        # 基本的网卡刷新逻辑
        pass
    
    def _fallback_info_copied(self, copied_text):
        """信息复制完成的回退处理"""
        self.logger.warning("状态管理器未初始化，使用回退方法处理信息复制")
        # 基本的信息复制逻辑
        pass
    
    def _fallback_service_error(self, error_title, error_message):
        """服务层错误的回退处理"""
        self.logger.warning("事件处理器未初始化，使用回退方法处理服务错误")
        self.logger.error(f"{error_title}: {error_message}")
    
    def _fallback_ip_config_applied(self, success_message):
        """IP配置应用成功的回退处理"""
        self.logger.warning("事件处理器未初始化，使用回退方法处理IP配置成功")
        self.logger.debug(f"IP配置应用成功: {success_message}")
    
    def _fallback_operation_progress(self, progress_message):
        """操作进度更新的回退处理"""
        self.logger.warning("事件处理器未初始化，使用回退方法处理操作进度")
        self.logger.debug(f"操作进度: {progress_message}")
    
    def _fallback_extra_ips_added(self, success_message):
        """批量额外IP添加的回退处理"""
        self.logger.warning("事件处理器未初始化，使用回退方法处理IP添加")
        self.logger.debug(f"批量添加IP成功: {success_message}")
    
    def _fallback_extra_ips_removed(self, success_message):
        """批量额外IP删除的回退处理"""
        self.logger.warning("事件处理器未初始化，使用回退方法处理IP删除")
        self.logger.debug(f"批量删除IP成功: {success_message}")
    
    def _fallback_modify_mac_address(self, adapter_name):
        """修改MAC地址的回退处理"""
        self.logger.warning("事件处理器未初始化，使用回退方法处理MAC地址修改")
        self.logger.debug(f"修改MAC地址请求: {adapter_name}")
        # 这里可以添加基本的静态IP设置逻辑或显示提示
    
    def _fallback_operation_completed(self, success, message, operation):
        """网卡操作完成的回退处理"""
        self.logger.warning("事件处理器未初始化，使用回退方法处理操作完成")
        if success:
            self.logger.info(f"操作成功: {operation} - {message}")
        else:
            self.logger.error(f"操作失败: {operation} - {message}")
