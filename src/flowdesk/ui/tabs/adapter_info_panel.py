# -*- coding: utf-8 -*-
"""
网卡信息面板模块

负责创建和管理网络配置Tab页面左侧的网卡信息显示面板，包括：
- 网卡选择下拉框和刷新按钮
- IP信息显示区域
- 网卡状态徽章
- 网卡操作按钮组

严格遵循UI四大铁律：
1. 🚫 禁止样式重复 - 通过objectName设置，样式在QSS中统一定义
2. 🔄 严格自适应布局 - 使用QVBoxLayout和QHBoxLayout实现响应式设计
3. 📏 最小宽度保护 - 设置合理的最小宽度防止控件重叠
4. ⚙️ 智能组件缩放 - 下拉框可拉伸，按钮固定尺寸，信息区域自适应

作者: FlowDesk开发团队
创建时间: 2024年
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, 
    QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from ..widgets.custom_text_edit import NoContextMenuTextEdit


class AdapterInfoPanel(QWidget):
    """
    网卡信息面板类
    
    继承自QWidget，封装左侧网卡信息面板的所有UI组件和布局。
    作为独立的面板组件，提供完整的网卡信息显示和操作功能。
    
    主要功能：
    - 网卡选择和刷新
    - IP信息详细显示
    - 网卡状态徽章显示
    - 网卡操作按钮组
    
    信号定义：
    - adapter_selected: 网卡选择变更信号
    - refresh_adapters: 刷新网卡列表信号
    - enable_adapter: 启用网卡信号
    - disable_adapter: 禁用网卡信号
    - set_static_ip: 设置静态IP信号
    - set_dhcp: 设置DHCP信号
    - copy_adapter_info: 复制网卡信息信号
    """
    
    # 定义信号 - 用于与服务层通信
    adapter_selected = pyqtSignal(str)  # 网卡选择变更
    refresh_adapters = pyqtSignal()     # 刷新网卡列表
    enable_adapter = pyqtSignal(str)    # 启用网卡
    disable_adapter = pyqtSignal(str)   # 禁用网卡
    set_static_ip = pyqtSignal(str)     # 设置静态IP
    set_dhcp = pyqtSignal(str)          # 设置DHCP
    copy_adapter_info = pyqtSignal()    # 复制网卡信息
    
    def __init__(self, parent=None):
        """
        初始化网卡信息面板
        
        创建所有UI组件并设置布局，遵循自适应设计原则。
        
        Args:
            parent: 父容器对象
        """
        super().__init__(parent)
        
        # 创建所有UI组件
        self._create_components()
        
        # 设置布局
        self._setup_layout()
        
        # 连接信号槽
        self.setup_signals()
        
        # 设置悬停提示
        self._setup_adapter_combo_hover_tooltip()
    
    def _create_components(self):
        """
        创建左侧面板的所有UI组件
        
        按照设计规范创建网卡选择、信息显示、状态徽章和操作按钮等组件。
        每个组件都设置了objectName用于QSS样式控制。
        """
        # 网卡选择下拉框 - 支持水平拉伸
        self.adapter_combo = QComboBox()
        self.adapter_combo.setObjectName("adapter_combo")
        self.adapter_combo.setToolTip("选择要配置的网络适配器")
        self.adapter_combo.setMinimumWidth(200)  # 最小宽度保护
        
        # 刷新按钮 - 固定尺寸，不随窗口缩放
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.setObjectName("refresh_btn")
        self.refresh_btn.setToolTip("刷新网卡列表和状态信息")
        self.refresh_btn.setFixedSize(80, 30)  # 固定按钮尺寸
        
        # IP信息展示区域 - 支持智能缩放，高度可随容器调整
        self.ip_info_display = NoContextMenuTextEdit()
        self.ip_info_display.setObjectName("ip_info_display")
        self.ip_info_display.setReadOnly(True)  # 设置为只读
        self.ip_info_display.setPlaceholderText("选择网卡后将显示详细信息...")
        
        # 连接状态徽章 - 显示网卡连接状态
        self.connection_status_badge = QLabel("未知")
        self.connection_status_badge.setObjectName("connection_status_badge")
        self.connection_status_badge.setAlignment(Qt.AlignCenter)
        self.connection_status_badge.setFixedSize(80, 25)
        
        # IP模式徽章 - 显示DHCP或静态IP模式
        self.ip_mode_badge = QLabel("未知")
        self.ip_mode_badge.setObjectName("ip_mode_badge")
        self.ip_mode_badge.setAlignment(Qt.AlignCenter)
        self.ip_mode_badge.setFixedSize(80, 25)
        
        # 链路速度徽章 - 显示网卡速度
        self.link_speed_badge = QLabel("未知")
        self.link_speed_badge.setObjectName("link_speed_badge")
        self.link_speed_badge.setAlignment(Qt.AlignCenter)
        self.link_speed_badge.setFixedSize(80, 25)
        
        # 网卡操作按钮组
        self.enable_adapter_btn = QPushButton("🔌 启用")
        self.enable_adapter_btn.setObjectName("enable_adapter_btn")
        self.enable_adapter_btn.setFixedSize(80, 30)
        
        self.disable_adapter_btn = QPushButton("🚫 禁用")
        self.disable_adapter_btn.setObjectName("disable_adapter_btn")
        self.disable_adapter_btn.setFixedSize(80, 30)
        
        self.set_static_btn = QPushButton("🔧 静态IP")
        self.set_static_btn.setObjectName("set_static_btn")
        self.set_static_btn.setFixedSize(80, 30)
        
        self.set_dhcp_btn = QPushButton("🔄 DHCP")
        self.set_dhcp_btn.setObjectName("set_dhcp_btn")
        self.set_dhcp_btn.setFixedSize(80, 30)
        
        self.copy_info_btn = QPushButton("📋 复制当前网卡信息")
        self.copy_info_btn.setObjectName("copy_info_btn")
        # 移除固定尺寸，让按钮可以自适应宽度
    
    def _setup_layout(self):
        """
        设置左侧面板的布局结构
        
        使用垂直布局作为主布局，包含网卡选择区、信息显示区、状态徽章区和操作按钮区。
        严格遵循自适应布局原则，确保在不同窗口尺寸下都能正常显示。
        """
        # 主布局 - 垂直排列
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 网卡选择区域 - 水平布局
        adapter_selection_layout = QHBoxLayout()
        adapter_selection_layout.addWidget(self.adapter_combo, 1)  # 下拉框可拉伸
        adapter_selection_layout.addWidget(self.refresh_btn, 0)    # 按钮固定尺寸
        main_layout.addLayout(adapter_selection_layout)
        
        # IP信息显示区域 - 占据主要空间
        main_layout.addWidget(self.ip_info_display, 1)
        
        # 状态徽章区域 - 水平排列
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.connection_status_badge)
        status_layout.addWidget(self.ip_mode_badge)
        status_layout.addWidget(self.link_speed_badge)
        main_layout.addLayout(status_layout)
        
        # 操作按钮区域 - 垂直排列
        button_layout = QVBoxLayout()
        
        # 第一行按钮
        button_row1 = QHBoxLayout()
        button_row1.addWidget(self.enable_adapter_btn)
        button_row1.addWidget(self.disable_adapter_btn)
        button_layout.addLayout(button_row1)
        
        # 第二行按钮
        button_row2 = QHBoxLayout()
        button_row2.addWidget(self.set_static_btn)
        button_row2.addWidget(self.set_dhcp_btn)
        button_layout.addLayout(button_row2)
        
        # 第三行按钮 - 复制按钮占满一整行
        button_row3 = QHBoxLayout()
        button_row3.addWidget(self.copy_info_btn, 1)  # 设置为1让按钮占满整行宽度
        button_layout.addLayout(button_row3)
        
        main_layout.addLayout(button_layout)
    
    def _setup_adapter_combo_hover_tooltip(self):
        """
        设置网络适配器下拉框的悬停提示功能
        
        这个方法的设计目标是解决用户体验问题：
        - 问题：网卡名称通常很长，在下拉框中显示时会被截断，用户看不到完整名称
        - 解决方案：当鼠标悬停在下拉框上时，动态显示当前选中网卡的完整名称
        """
        # 安装事件过滤器，让父容器来处理下拉框的鼠标事件
        self.adapter_combo.installEventFilter(self)
        
        # 保存默认的工具提示文本，用于鼠标离开时恢复
        self._default_adapter_tooltip = "选择要配置的网络适配器"
    
    def setup_signals(self):
        """
        连接左侧面板组件的信号槽
        
        将UI事件连接到面板自身的信号，供父容器转发给服务层。
        """
        # 网卡选择变更
        self.adapter_combo.currentTextChanged.connect(self.adapter_selected.emit)
        
        # 刷新网卡列表
        self.refresh_btn.clicked.connect(self.refresh_adapters.emit)
        
        # 网卡操作按钮
        self.enable_adapter_btn.clicked.connect(
            lambda: self.enable_adapter.emit(self.adapter_combo.currentText())
        )
        self.disable_adapter_btn.clicked.connect(
            lambda: self.disable_adapter.emit(self.adapter_combo.currentText())
        )
        self.set_static_btn.clicked.connect(
            lambda: self.set_static_ip.emit(self.adapter_combo.currentText())
        )
        self.set_dhcp_btn.clicked.connect(
            lambda: self.set_dhcp.emit(self.adapter_combo.currentText())
        )
        
        # 复制网卡信息
        self.copy_info_btn.clicked.connect(self.copy_adapter_info.emit)
    
    def update_adapter_list(self, adapter_names):
        """
        更新网卡下拉框列表
        
        Args:
            adapter_names (list): 网卡名称列表
        """
        self.adapter_combo.clear()
        self.adapter_combo.addItems(adapter_names)
    
    def update_ip_info_display(self, formatted_info):
        """
        更新IP信息展示区域
        
        Args:
            formatted_info (str): 格式化的网卡信息文本
        """
        self.ip_info_display.setPlainText(formatted_info)
    
    def update_status_badges(self, connection_status, ip_mode, link_speed):
        """
        更新状态徽章显示
        
        Args:
            connection_status (str): 连接状态
            ip_mode (str): IP模式
            link_speed (str): 链路速度
        """
        self.connection_status_badge.setText(connection_status)
        self.ip_mode_badge.setText(ip_mode)
        self.link_speed_badge.setText(link_speed)
