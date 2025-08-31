# -*- coding: utf-8 -*-
"""
系统托盘UI服务 - 专门处理托盘相关的UI操作和对话框显示
"""

import os
from PyQt5.QtWidgets import (QSystemTrayIcon, QMenu, QAction, QApplication,
                            QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
                            QLabel, QPushButton, QWidget)
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QIcon, QPixmap

from ..utils.resource_path import resource_path
from ..utils.logger import get_logger


class TrayExitDialog(QDialog):
    """
    托盘退出确认对话框
    
    当用户尝试关闭主窗口时显示的确认对话框，
    提供三个选项：彻底退出、最小化到托盘、取消操作。
    """
    
    def __init__(self, parent=None):
        """
        初始化退出确认对话框
        
        创建包含三个按钮的对话框界面，设置合适的窗口属性和布局。
        对话框采用模态显示，确保用户必须做出选择。
        """
        super().__init__(parent)
        self.user_choice = None
        self.logger = get_logger(__name__)
        
        self._setup_dialog()
        self._create_layout()
        self._connect_signals()
        
        self.logger.debug("托盘退出对话框初始化完成")
    
    def _setup_dialog(self):
        """设置对话框基本属性"""
        self.setWindowTitle("FlowDesk - 要走了吗？")
        self.setModal(True)
        self.setFixedSize(480, 220)
        
        # 设置对话框图标
        icon_path = resource_path("assets/icons/flowdesk.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 设置objectName用于QSS样式
        self.setObjectName("tray_exit_dialog")
    
    def _create_layout(self):
        """创建对话框布局和控件"""
        layout = QVBoxLayout(self)
        
        # 添加顶部间距
        layout.addSpacing(15)
        
        # 主标题
        title_label = QLabel("🤔 等等，真的要离开吗？")
        title_label.setObjectName("tray_exit_title")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # 副标题提示
        subtitle_label = QLabel("FlowDesk 还在默默守护您的网络呢~")
        subtitle_label.setObjectName("tray_exit_subtitle")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)
        
        # 按钮容器
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setSpacing(12)
        
        # 第一行：最小化到托盘（推荐选项）
        self.minimize_button = QPushButton("🏠 让我安静地待在托盘里")
        self.minimize_button.setObjectName("tray_exit_no_btn")
        self.minimize_button.setMinimumHeight(45)
        button_layout.addWidget(self.minimize_button)
        
        # 第二行按钮组
        second_row = QHBoxLayout()
        second_row.setSpacing(15)
        
        # 取消按钮
        self.cancel_button = QPushButton("💙 我再想想")
        self.cancel_button.setObjectName("tray_exit_cancel_btn")
        self.cancel_button.setMinimumHeight(40)
        second_row.addWidget(self.cancel_button)
        
        # 彻底退出按钮
        self.exit_button = QPushButton("💔 真的要离开")
        self.exit_button.setObjectName("tray_exit_yes_btn")
        self.exit_button.setMinimumHeight(40)
        second_row.addWidget(self.exit_button)
        
        button_layout.addLayout(second_row)
        layout.addWidget(button_container)
        
        # 底部间距
        layout.addSpacing(15)
    
    def _connect_signals(self):
        """连接按钮信号"""
        self.exit_button.clicked.connect(lambda: self._handle_choice("exit"))
        self.minimize_button.clicked.connect(lambda: self._handle_choice("minimize"))
        self.cancel_button.clicked.connect(lambda: self._handle_choice("cancel"))
    
    def _handle_choice(self, choice: str):
        """处理用户选择"""
        self.user_choice = choice
        self.logger.debug(f"用户选择: {choice}")
        self.accept()
    
    def get_user_choice(self) -> str:
        """获取用户选择结果"""
        return self.user_choice


class TrayUIService(QObject):
    """
    系统托盘UI服务
    
    专门处理系统托盘相关的UI操作，包括托盘图标、菜单、
    消息通知和退出确认对话框等。
    """
    
    # 信号定义
    show_window_requested = pyqtSignal()
    exit_requested = pyqtSignal()
    minimize_to_tray_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        """初始化托盘UI服务"""
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.tray_icon = None
        self.tray_menu = None
        
    def setup_system_tray(self) -> bool:
        """
        设置系统托盘图标和菜单
        
        Returns:
            bool: 设置成功返回True，失败返回False
        """
        try:
            # 检查系统托盘是否可用
            if not QSystemTrayIcon.isSystemTrayAvailable():
                self.logger.warning("系统托盘不可用")
                return False
            
            # 创建托盘图标
            icon_path = resource_path("assets/icons/flowdesk.ico")
            if not os.path.exists(icon_path):
                self.logger.error(f"托盘图标文件不存在: {icon_path}")
                return False
            
            self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self)
            
            # 创建托盘菜单
            self._create_tray_menu()
            
            # 连接信号
            self.tray_icon.activated.connect(self._on_tray_activated)
            
            # 显示托盘图标
            self.tray_icon.show()
            
            self.logger.debug("系统托盘设置成功")
            return True
            
        except Exception as e:
            self.logger.error(f"设置系统托盘失败: {e}")
            return False
    
    def _create_tray_menu(self):
        """创建托盘右键菜单"""
        self.tray_menu = QMenu()
        
        # 显示窗口菜单项
        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self.show_window_requested.emit)
        self.tray_menu.addAction(show_action)
        
        self.tray_menu.addSeparator()
        
        # 退出菜单项
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self._handle_exit_request)
        self.tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
    
    def _on_tray_activated(self, reason):
        """处理托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window_requested.emit()
    
    def _handle_exit_request(self):
        """处理退出请求"""
        self.show_exit_dialog()
    
    def show_exit_dialog(self):
        """显示退出选择对话框"""
        dialog = TrayExitDialog(self.parent())
        if dialog.exec_() == dialog.Accepted:
            choice = dialog.get_user_choice()
            if choice == 'exit':
                self.exit_requested.emit()
            elif choice == 'minimize':
                self.minimize_to_tray_requested.emit()
            # cancel选择不需要处理
    
    def show_message(self, title: str, message: str, icon=QSystemTrayIcon.Information, timeout=3000):
        """显示托盘消息通知"""
        if self.tray_icon and self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, message, icon, timeout)
    
    def hide_tray_icon(self):
        """隐藏托盘图标"""
        if self.tray_icon:
            self.tray_icon.hide()
    
    def is_tray_available(self) -> bool:
        """检查系统托盘是否可用"""
        return QSystemTrayIcon.isSystemTrayAvailable()
