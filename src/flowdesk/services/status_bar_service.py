# -*- coding: utf-8 -*-
"""
状态栏管理服务

负责管理主窗口状态栏的信息更新和状态跟踪。
通过PyQt信号机制与UI层通信，提供实时的应用状态和用户操作反馈。
严格遵循Service层单职责原则，只负责状态数据的管理和分发。
"""

import logging
from typing import Optional
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from ..models.status_bar_info import StatusBarInfo, StatusBarTheme
from ..utils.version_utils import get_version_info, format_version_display


class StatusBarService(QObject):
    """
    状态栏信息管理服务
    
    负责管理和维护主窗口状态栏显示的所有信息，包括：
    - 应用程序运行状态管理
    - 用户操作状态跟踪
    - 版本信息获取和缓存
    - 状态变更通知分发
    
    通过PyQt信号与UI层解耦，确保状态更新的实时性和准确性。
    """
    
    # 状态更新信号 - UI层通过连接此信号接收状态变更通知
    status_updated = pyqtSignal(object)  # 参数类型: StatusBarInfo
    
    # 版本信息更新信号 - UI层通过连接此信号接收版本信息变更通知
    version_updated = pyqtSignal(str)  # 参数类型: str (格式化的版本信息)
    
    def __init__(self, parent: Optional[QObject] = None):
        """
        初始化状态栏管理服务
        
        Args:
            parent: PyQt父对象，用于内存管理
        """
        super().__init__(parent)
        
        # 初始化日志记录器
        self.logger = logging.getLogger(self.__class__.__module__)
        
        # 获取版本信息并缓存
        self._version, self._build_date = get_version_info()
        
        # 初始化当前状态信息
        self._current_status = StatusBarInfo.create_default(
            version=self._version,
            build_date=self._build_date
        )
        
        # 状态自动恢复定时器 - 用于临时状态的自动恢复
        self._status_timer = QTimer()
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(self._restore_ready_status)
        
        # 发射初始版本信息更新信号
        version_text = format_version_display(self._version, self._build_date)
        self.version_updated.emit(version_text)
        
        self.logger.debug("状态栏管理服务初始化完成")
    
    def get_current_status(self) -> StatusBarInfo:
        """
        获取当前状态信息
        
        Returns:
            StatusBarInfo: 当前的状态栏信息
        """
        return self._current_status
    
    def update_app_status(self, status: str, auto_restore: bool = False, restore_delay: int = 3000):
        """
        更新应用程序状态
        
        Args:
            status: 新的应用状态，如 "🟢 就绪", "⚠️ 警告", "❌ 错误"
            auto_restore: 是否自动恢复到就绪状态
            restore_delay: 自动恢复延迟时间(毫秒)
        """
        try:
            # 创建新的状态信息实例
            new_status = self._current_status.with_app_status(status)
            self._update_status(new_status)
            
            # 设置自动恢复
            if auto_restore:
                self._status_timer.start(restore_delay)
                
            self.logger.debug(f"应用状态已更新: {status}")
            
        except Exception as e:
            self.logger.error(f"更新应用状态失败: {str(e)}")
    
    def update_user_action(self, action: str, auto_clear: bool = False, clear_delay: int = 5000):
        """
        更新用户操作状态
        
        Args:
            action: 用户操作描述，如 "📡 获取网卡信息", "⚙️ 配置网络"
            auto_clear: 是否自动清除操作状态
            clear_delay: 自动清除延迟时间(毫秒)
        """
        try:
            # 创建新的状态信息实例
            new_status = self._current_status.with_user_action(action)
            self._update_status(new_status)
            
            # 设置自动清除（默认关闭，保持最后操作状态）
            if auto_clear:
                QTimer.singleShot(clear_delay, lambda: self._clear_user_action())
                
            self.logger.debug(f"用户操作状态已更新: {action}")
            
        except Exception as e:
            self.logger.error(f"更新用户操作状态失败: {str(e)}")
    
    def set_ready_status(self):
        """设置就绪状态"""
        self.update_app_status("🟢 就绪")
        # 移除自动设置"等待操作"，保持上次操作状态
    
    def set_busy_status(self, operation: str):
        """
        设置忙碌状态
        
        Args:
            operation: 正在执行的操作描述
        """
        self.update_app_status("🔄 处理中")
        self.update_user_action(f"⚙️ {operation}")
    
    def set_error_status(self, error_msg: str):
        """
        设置错误状态
        
        Args:
            error_msg: 错误信息
        """
        self.update_app_status("❌ 错误", auto_restore=True)
        self.update_user_action(f"⚠️ {error_msg}")
    
    def set_success_status(self, success_msg: str):
        """
        设置成功状态
        
        Args:
            success_msg: 成功信息
        """
        self.update_app_status("✅ 完成", auto_restore=True)
        self.update_user_action(f"✨ {success_msg}")
    
    def set_status(self, status_text: str, auto_clear_seconds: int = 0):
        """
        设置状态栏显示文本的统一接口
        
        这是一个便捷方法，用于快速设置状态栏显示内容。
        状态文本应包含Emoji和描述，如 "🔄 正在切换网卡"。
        
        Args:
            status_text: 要显示的状态文本，包含Emoji和描述
            auto_clear_seconds: 自动清除时间(秒)，0表示不自动清除
        """
        try:
            # 解析状态文本，提取Emoji和描述
            if " " in status_text:
                emoji_part = status_text.split(" ")[0]
                desc_part = " ".join(status_text.split(" ")[1:])
            else:
                emoji_part = "🔄"
                desc_part = status_text
            
            # 更新用户操作状态
            auto_clear = auto_clear_seconds > 0
            clear_delay = auto_clear_seconds * 1000 if auto_clear else 0
            
            self.update_user_action(
                f"{emoji_part} {desc_part}", 
                auto_clear=auto_clear, 
                clear_delay=clear_delay
            )
            
            self.logger.debug(f"状态已设置: {status_text}")
            
        except Exception as e:
            self.logger.error(f"设置状态失败: {str(e)}")
            # 回退到基本状态显示
            self.update_user_action("⚠️ 状态更新失败")
    
    def _update_status(self, new_status: StatusBarInfo):
        """
        内部状态更新方法
        
        Args:
            new_status: 新的状态信息
        """
        self._current_status = new_status
        self.logger.debug(f"🚀 StatusBarService发射status_updated信号: {new_status.user_action}")
        self.status_updated.emit(new_status)
    
    def _restore_ready_status(self):
        """恢复就绪状态"""
        self.update_app_status("🟢 就绪")
    
    def _clear_user_action(self):
        """清除用户操作状态（已废弃，保持最后操作状态）"""
        # 不再自动清除到"等待操作"，保持最后一次操作的状态
        pass
    
    # 预定义的常用状态更新方法
    
    def on_network_operation_start(self, operation: str):
        """网络操作开始"""
        self.set_busy_status(f"📡 {operation}")
    
    def on_network_operation_success(self, operation: str):
        """网络操作成功"""
        self.set_success_status(f"网络操作完成: {operation}")
    
    def on_network_operation_error(self, operation: str, error: str):
        """网络操作失败"""
        self.set_error_status(f"网络操作失败: {operation} - {error}")
    
    def on_ip_config_start(self):
        """IP配置开始"""
        self.set_busy_status("配置IP地址")
    
    def on_ip_config_success(self):
        """IP配置成功"""
        self.set_success_status("IP配置已应用")
    
    def on_adapter_refresh_start(self):
        """网卡刷新开始"""
        self.set_busy_status("刷新网卡信息")
    
    def on_adapter_refresh_success(self):
        """网卡刷新成功"""
        self.set_success_status("网卡信息已更新")
    
    def on_app_startup_complete(self):
        """应用启动完成"""
        self.update_app_status("🟢 就绪")
        # 不设置用户操作状态，让启动时的状态保持
        self.logger.debug("应用启动完成，状态栏就绪")
