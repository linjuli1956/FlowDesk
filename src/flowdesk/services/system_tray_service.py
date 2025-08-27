"""
系统托盘服务

提供FlowDesk应用程序的系统托盘功能，包括托盘图标显示、右键菜单、
双击交互和高级关闭逻辑处理。

主要功能：
- 系统托盘图标显示和管理
- 托盘右键菜单（显示窗口、退出程序）
- 双击托盘图标显示/隐藏主窗口
- 高级关闭逻辑（询问用户：彻底退出/最小化到托盘/取消）
- 托盘消息通知功能
- 与主窗口的信号通信

设计特点：
- 采用PyQt信号槽机制与主窗口通信
- 支持系统托盘不可用时的降级处理
- 提供用户友好的交互体验
- 集成外置QSS样式系统
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
    
    当用户点击窗口关闭按钮时显示的询问对话框，
    提供三个选项：彻底退出、最小化到托盘、取消操作。
    """
    
    # 定义用户选择结果的常量
    RESULT_EXIT = 1      # 彻底退出程序
    RESULT_MINIMIZE = 2  # 最小化到系统托盘
    RESULT_CANCEL = 3    # 取消关闭操作
    
    def __init__(self, parent=None):
        """
        初始化退出确认对话框
        
        创建包含三个按钮的对话框，按钮颜色遵循语义化设计：
        - Yes（红色）：彻底退出程序
        - No（绿色）：最小化到系统托盘
        - Cancel（蓝色）：取消关闭操作
        """
        super().__init__(parent)
        
        self.logger = get_logger(__name__)
        self.user_choice = self.RESULT_CANCEL  # 默认选择取消
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """
        创建对话框用户界面
        
        构建包含提示文本和三个操作按钮的对话框布局。
        按钮采用语义化颜色设计，提供清晰的视觉指导。
        """
        # 设置对话框基本属性
        self.setWindowTitle("FlowDesk - 关闭确认")
        self.setFixedSize(400, 150)
        self.setModal(True)  # 模态对话框，阻塞其他窗口操作
        self.setObjectName("tray_exit_dialog")
        
        # 设置对话框图标
        icon_path = resource_path("assets/icons/flowdesk.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 创建提示文本标签
        message_label = QLabel("是否最小化到系统托盘？")
        message_label.setObjectName("tray_exit_message")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        main_layout.addWidget(message_label)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # 最小化按钮 - 最小化到系统托盘
        # 使用绿色渐变样式，表示安全的操作（程序继续运行）
        self.minimize_button = QPushButton("最小化")
        self.minimize_button.setObjectName("tray_exit_no_btn")
        
        # 取消按钮 - 取消关闭操作
        # 使用蓝色渐变样式，表示中性的操作（返回原状态）
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setObjectName("tray_exit_cancel_btn")
        
        # 退出按钮 - 彻底退出程序
        # 使用红色渐变样式，表示危险操作（程序完全关闭）
        self.exit_button = QPushButton("退出程序")
        self.exit_button.setObjectName("tray_exit_yes_btn")
        
        # 设置按钮尺寸
        button_size = (90, 32)
        for button in [self.minimize_button, self.cancel_button, self.exit_button]:
            button.setFixedSize(*button_size)
        
        # 添加按钮到布局（顺序：最小化、取消、退出程序）
        button_layout.addStretch()  # 左侧弹性空间
        button_layout.addWidget(self.minimize_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.exit_button)
        button_layout.addStretch()  # 右侧弹性空间
        
        # 添加组件到主布局
        main_layout.addWidget(message_label)
        main_layout.addLayout(button_layout)
    
    def setup_connections(self):
        """
        设置按钮信号连接
        
        连接三个按钮的点击信号到对应的处理方法。
        """
        self.minimize_button.clicked.connect(self.on_minimize_clicked)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        self.exit_button.clicked.connect(self.on_exit_clicked)
    
    def on_minimize_clicked(self):
        """处理最小化按钮点击 - 最小化到系统托盘"""
        self.user_choice = self.RESULT_MINIMIZE
        self.accept()
    
    def on_exit_clicked(self):
        """处理退出按钮点击 - 彻底退出程序"""
        self.user_choice = self.RESULT_EXIT
        self.accept()
    
    def on_cancel_clicked(self):
        """处理取消按钮点击 - 取消关闭操作"""
        self.user_choice = self.RESULT_CANCEL
        self.reject()
    
    def get_user_choice(self):
        """获取用户选择结果"""
        return self.user_choice


class SystemTrayService(QObject):
    """
    系统托盘服务类
    
    管理系统托盘图标、菜单和用户交互。
    提供完整的托盘功能包括显示/隐藏窗口、退出程序等。
    """
    
    # 定义信号用于与主窗口通信
    show_window_requested = pyqtSignal()    # 请求显示主窗口
    hide_window_requested = pyqtSignal()    # 请求隐藏主窗口
    exit_application_requested = pyqtSignal()  # 请求退出应用程序
    
    def __init__(self, main_window=None):
        """
        初始化系统托盘服务
        
        参数:
            main_window: 主窗口实例，用于信号连接和交互
        """
        super().__init__()
        
        self.logger = get_logger(__name__)
        self.main_window = main_window
        self.tray_icon = None
        self.tray_menu = None
        
        # 检查系统托盘可用性
        self.tray_available = QSystemTrayIcon.isSystemTrayAvailable()
        
        if not self.tray_available:
            self.logger.warning("系统托盘不可用")
    
    def initialize(self):
        """
        初始化系统托盘组件
        
        创建托盘图标、菜单和信号连接。
        如果系统托盘不可用，则跳过初始化。
        """
        if not self.tray_available:
            self.logger.warning("跳过系统托盘初始化 - 系统托盘不可用")
            return False
        
        try:
            # 创建系统托盘图标
            self.create_tray_icon()
            
            # 创建托盘菜单
            self.create_tray_menu()
            
            # 设置信号连接
            self.setup_connections()
            
            # 显示托盘图标
            self.tray_icon.show()
            
            self.logger.info("系统托盘服务初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"系统托盘初始化失败: {e}")
            return False
    
    def create_tray_icon(self):
        """
        创建系统托盘图标
        
        使用应用程序图标创建系统托盘图标，
        设置工具提示文本和基本属性。
        """
        # 创建托盘图标实例
        self.tray_icon = QSystemTrayIcon()
        
        # 设置托盘图标
        icon_path = resource_path("assets/icons/flowdesk.ico")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # 如果图标文件不存在，使用默认图标
            self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
        
        # 设置托盘图标工具提示
        self.tray_icon.setToolTip("FlowDesk - Windows系统管理工具")
    
    def create_tray_menu(self):
        """
        创建系统托盘右键菜单
        
        创建包含"显示窗口"和"退出"选项的右键菜单。
        菜单项使用图标和快捷键提升用户体验。
        """
        # 创建托盘菜单
        self.tray_menu = QMenu()
        self.tray_menu.setObjectName("tray_menu")
        
        # 创建"显示窗口"菜单项
        show_action = QAction("显示窗口", self)
        show_action.setObjectName("tray_show_action")
        show_action.triggered.connect(self.on_show_window_clicked)
        
        # 创建分隔线
        self.tray_menu.addSeparator()
        
        # 创建"退出"菜单项
        exit_action = QAction("退出", self)
        exit_action.setObjectName("tray_exit_action")
        exit_action.triggered.connect(self.on_exit_clicked)
        
        # 添加菜单项到菜单
        self.tray_menu.addAction(show_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(exit_action)
        
        # 设置托盘图标的右键菜单
        self.tray_icon.setContextMenu(self.tray_menu)
    
    def setup_connections(self):
        """
        设置信号连接
        
        连接托盘图标的各种信号到对应的处理方法，
        包括双击、右键菜单等交互。
        """
        if self.tray_icon:
            # 连接托盘图标激活信号（双击、单击等）
            self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        if self.main_window:
            # 连接主窗口的关闭请求信号
            self.main_window.close_requested.connect(self.handle_close_request)
            
            # 连接服务信号到主窗口方法
            self.show_window_requested.connect(self.main_window.show_from_tray)
            self.hide_window_requested.connect(self.main_window.hide_to_tray)
            self.exit_application_requested.connect(QApplication.quit)
    
    def on_tray_icon_activated(self, reason):
        """
        处理托盘图标激活事件
        
        根据不同的激活原因执行相应操作：
        - 双击：显示/隐藏主窗口
        - 单击：显示主窗口
        - 右键：显示上下文菜单（自动处理）
        
        参数:
            reason: 激活原因（QSystemTrayIcon.ActivationReason枚举）
        """
        if reason == QSystemTrayIcon.DoubleClick:
            # 双击托盘图标 - 切换窗口显示状态
            self.toggle_main_window()
            self.logger.info("托盘图标双击 - 切换窗口显示状态")
            
        elif reason == QSystemTrayIcon.Trigger:
            # 单击托盘图标 - 显示主窗口
            self.show_main_window()
            self.logger.info("托盘图标单击 - 显示主窗口")
    
    def on_show_window_clicked(self):
        """处理"显示窗口"菜单项点击"""
        self.show_main_window()
        self.logger.info("托盘菜单 - 显示窗口")
    
    def on_exit_clicked(self):
        """处理"退出"菜单项点击"""
        self.exit_application()
        self.logger.info("托盘菜单 - 退出程序")
    
    def show_main_window(self):
        """显示主窗口"""
        if self.main_window:
            self.show_window_requested.emit()
    
    def hide_main_window(self):
        """隐藏主窗口到托盘"""
        if self.main_window:
            self.hide_window_requested.emit()
    
    def toggle_main_window(self):
        """切换主窗口显示状态"""
        if self.main_window:
            if self.main_window.isVisible():
                self.hide_main_window()
            else:
                self.show_main_window()
    
    def handle_close_request(self):
        """
        处理主窗口关闭请求
        
        显示高级关闭逻辑对话框，根据用户选择执行相应操作：
        - 彻底退出：关闭应用程序
        - 最小化到托盘：隐藏窗口到托盘
        - 取消：不执行任何操作
        """
        # 创建退出确认对话框
        dialog = TrayExitDialog(self.main_window)
        
        # 显示对话框并获取用户选择
        dialog.exec_()
        choice = dialog.get_user_choice()
        
        if choice == TrayExitDialog.RESULT_EXIT:
            # 用户选择彻底退出
            self.exit_application()
            self.logger.info("用户选择彻底退出程序")
            
        elif choice == TrayExitDialog.RESULT_MINIMIZE:
            # 用户选择最小化到托盘
            self.hide_main_window()
            self.show_tray_message("FlowDesk已最小化到系统托盘", 
                                 "程序将继续在后台运行，双击托盘图标可重新显示窗口。")
            self.logger.info("用户选择最小化到系统托盘")
            
        else:
            # 用户选择取消或关闭对话框
            self.logger.info("用户取消关闭操作")
    
    def exit_application(self):
        """退出应用程序"""
        self.exit_application_requested.emit()
    
    def show_tray_message(self, title, message, icon=QSystemTrayIcon.Information, timeout=3000):
        """
        显示系统托盘消息通知
        
        参数:
            title: 通知标题
            message: 通知内容
            icon: 通知图标类型
            timeout: 显示时长（毫秒）
        """
        if self.tray_icon and self.tray_available:
            self.tray_icon.showMessage(title, message, icon, timeout)
    
    def cleanup(self):
        """
        清理系统托盘资源
        
        在应用程序退出前清理托盘图标和相关资源。
        """
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon = None
        
        if self.tray_menu:
            self.tray_menu = None
        
        self.logger.info("系统托盘服务已清理")
    
    def is_available(self):
        """检查系统托盘是否可用"""
        return self.tray_available
