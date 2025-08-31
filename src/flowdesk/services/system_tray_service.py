"""
系统托盘业务逻辑服务

提供FlowDesk应用程序的系统托盘业务逻辑，不包含任何UI操作。
UI操作由TrayUIService处理，本服务只负责业务逻辑协调。

主要功能：
- 托盘服务状态管理
- 业务逻辑协调
- 与其他服务的通信
- 托盘功能的启用/禁用控制

设计特点：
- 严格遵循分层架构，无UI依赖
- 采用PyQt信号槽机制进行通信
- 支持系统托盘不可用时的降级处理
- 提供业务逻辑的统一管理
"""

from PyQt5.QtCore import QObject, pyqtSignal
from ..utils.logger import get_logger
from ..utils.capabilities import get_system_capabilities


class SystemTrayService(QObject):
    """
    系统托盘业务逻辑服务
    
    负责系统托盘功能的业务逻辑管理，不包含任何UI操作。
    所有UI相关操作由TrayUIService处理。
    """
    
    # 信号定义
    tray_available_changed = pyqtSignal(bool)  # 托盘可用状态变化
    show_window_requested = pyqtSignal()       # 请求显示窗口
    exit_requested = pyqtSignal()              # 请求退出程序
    minimize_to_tray_requested = pyqtSignal()  # 请求最小化到托盘
    show_exit_dialog_requested = pyqtSignal()  # 请求显示退出选择对话框
    
    def __init__(self, parent=None):
        """初始化系统托盘服务"""
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self._is_tray_enabled = False
        self._is_tray_available = False
        
    def initialize(self) -> bool:
        """
        初始化托盘服务
        
        检查系统托盘可用性，设置服务状态。
        
        Returns:
            bool: 初始化成功返回True
        """
        try:
            # 检查系统能力
            capabilities = get_system_capabilities()
            # 系统托盘功能基于PyQt可用性判断
            # pyqt_available是字典类型，需要提取available字段
            if isinstance(capabilities.pyqt_available, dict):
                self._is_tray_available = capabilities.pyqt_available.get('available', False)
            else:
                self._is_tray_available = bool(capabilities.pyqt_available)
            
            if self._is_tray_available:
                self._is_tray_enabled = True
                self.logger.debug("系统托盘服务初始化成功")
            else:
                self.logger.warning("系统托盘不可用，服务将以降级模式运行")
            
            self.tray_available_changed.emit(self._is_tray_available)
            return True
            
        except Exception as e:
            self.logger.error(f"系统托盘服务初始化失败: {e}")
            return False
    
    def is_tray_available(self) -> bool:
        """检查系统托盘是否可用"""
        return self._is_tray_available
    
    def is_tray_enabled(self) -> bool:
        """检查托盘服务是否启用"""
        return self._is_tray_enabled
    
    def enable_tray(self):
        """启用托盘服务"""
        if self._is_tray_available:
            self._is_tray_enabled = True
            self.logger.debug("托盘服务已启用")
    
    def disable_tray(self):
        """禁用托盘服务"""
        self._is_tray_enabled = False
        self.logger.debug("托盘服务已禁用")
    
    def handle_window_close_request(self) -> str:
        """
        处理窗口关闭请求
        
        根据托盘可用性决定关闭行为：
        - 托盘可用：显示退出选择对话框
        - 托盘不可用：直接退出
        
        Returns:
            str: 处理结果 ('dialog', 'exit')
        """
        if self._is_tray_enabled and self._is_tray_available:
            self.show_exit_dialog_requested.emit()
            return 'dialog'
        else:
            self.exit_requested.emit()
            return 'exit'
    
    def handle_show_window_request(self):
        """处理显示窗口请求"""
        self.show_window_requested.emit()
        self.logger.debug("发射显示窗口请求信号")
    
    def handle_exit_request(self):
        """处理退出请求"""
        self.exit_requested.emit()
        self.logger.debug("发射退出程序请求信号")
