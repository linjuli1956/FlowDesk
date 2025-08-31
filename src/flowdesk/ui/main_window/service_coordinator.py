# -*- coding: utf-8 -*-
"""
服务层协调器：负责服务初始化和信号连接管理
"""

from ...utils.logger import get_logger
from ...services import NetworkService


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
    
    def initialize_services(self):
        """
        初始化服务层组件并连接信号槽
        
        创建NetworkService实例，连接UI层与服务层的信号槽通信，
        实现网络配置Tab的核心功能逻辑。
        """
        try:
            # 创建网络服务实例
            self.network_service = NetworkService()
            self.logger.info("网络服务初始化完成")
            
            # 将网络服务实例设置到主窗口，供其他组件使用
            self.main_window.network_service = self.network_service
            
            # 连接网络配置Tab的信号槽
            self._connect_network_config_signals()
            
            # 启动初始化：自动获取网卡信息
            self.network_service.get_all_adapters()
            self.logger.info("网络配置Tab核心功能连接完成")
            
        except Exception as e:
            error_msg = f"服务层初始化失败: {str(e)}"
            self.logger.error(error_msg)
            # 服务初始化失败不影响UI显示，但功能会受限
    
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
        
        # 批量添加选中IP：UI添加选中按钮 -> 服务层批量添加额外IP
        self.main_window.network_config_tab.add_selected_ips.connect(
            self.network_service.add_selected_extra_ips
        )
        
        # 批量删除选中IP：UI删除选中按钮 -> 服务层批量删除额外IP
        self.main_window.network_config_tab.remove_selected_ips.connect(
            self.network_service.remove_selected_extra_ips
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
    
    def cleanup_services(self):
        """
        清理服务层资源
        
        在应用程序退出时清理服务层资源，确保优雅关闭。
        """
        try:
            if self.network_service:
                # 这里可以添加服务层清理逻辑
                self.logger.info("网络服务资源已清理")
                
        except Exception as e:
            self.logger.error(f"清理服务层资源失败: {e}")
    
    # === 回退方法：在组件未初始化时提供基本功能 ===
    
    def _fallback_adapter_combo_changed(self, display_name):
        """网卡选择变更的回退处理"""
        self.logger.warning("事件处理器未初始化，使用回退方法处理网卡选择")
        # 基本的网卡选择逻辑
        pass
    
    def _fallback_apply_ip_config(self, config_data):
        """IP配置应用的回退处理"""
        self.logger.warning("事件处理器未初始化，使用回退方法处理IP配置")
        # 基本的IP配置逻辑
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
        self.logger.info(f"IP配置应用成功: {success_message}")
    
    def _fallback_operation_progress(self, progress_message):
        """操作进度更新的回退处理"""
        self.logger.warning("事件处理器未初始化，使用回退方法处理操作进度")
        self.logger.info(f"操作进度: {progress_message}")
    
    def _fallback_extra_ips_added(self, success_message):
        """批量额外IP添加的回退处理"""
        self.logger.warning("事件处理器未初始化，使用回退方法处理IP添加")
        self.logger.info(f"批量添加IP成功: {success_message}")
    
    def _fallback_extra_ips_removed(self, success_message):
        """批量额外IP删除的回退处理"""
        self.logger.warning("事件处理器未初始化，使用回退方法处理IP删除")
        self.logger.info(f"批量删除IP成功: {success_message}")
