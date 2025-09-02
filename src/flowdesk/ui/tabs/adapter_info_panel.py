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
    - modify_mac_address: 修改MAC地址信号
    - set_dhcp: 设置DHCP信号
    - copy_adapter_info: 复制网卡信息信号
    """
    
    # 定义信号 - 用于与服务层通信
    adapter_selected = pyqtSignal(str)  # 网卡选择变更
    refresh_adapters = pyqtSignal()     # 刷新网卡列表
    enable_adapter = pyqtSignal(str)    # 启用网卡
    disable_adapter = pyqtSignal(str)   # 禁用网卡
    modify_mac_address = pyqtSignal(str)     # 修改MAC地址
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
        
        # 网卡描述到友好名称的映射字典
        self._adapter_name_mapping = {}
        
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
        
        # 当前IP信息标题标签
        self.ip_info_label = QLabel("📋 当前IP信息")
        self.ip_info_label.setObjectName("ip_info_label")
        
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
        self.enable_adapter_btn = QPushButton("🔌 启用网卡")
        self.enable_adapter_btn.setObjectName("enable_adapter_btn")
        self.enable_adapter_btn.setFixedSize(90, 30)
        
        self.disable_adapter_btn = QPushButton("🚫 禁用网卡")
        self.disable_adapter_btn.setObjectName("disable_adapter_btn")
        self.disable_adapter_btn.setFixedSize(90, 30)
        
        self.set_static_btn = QPushButton("🔧 修改MAC")
        self.set_static_btn.setObjectName("set_static_btn")
        self.set_static_btn.setFixedSize(90, 30)
        
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
        main_layout.setSpacing(8)  # 减少整体间距为标题腾出空间
        
        # 网卡选择区域 - 水平布局
        adapter_selection_layout = QHBoxLayout()
        adapter_selection_layout.addWidget(self.adapter_combo, 1)  # 下拉框可拉伸
        adapter_selection_layout.addWidget(self.refresh_btn, 0)    # 按钮固定尺寸
        main_layout.addLayout(adapter_selection_layout)
        
        # 当前IP信息标题标签 - 紧贴网卡选择区域
        main_layout.addWidget(self.ip_info_label)
        
        # IP信息显示区域 - 占据主要空间，保持原有高度
        main_layout.addWidget(self.ip_info_display, 1)
        
        # 添加弹性空间，将状态徽章和按钮区域推到底部
        main_layout.addStretch(0)
        
        # 状态徽章区域 - 水平排列，固定在底部区域
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
        # 网卡选择变更 - 传递友好名称而不是描述
        self.adapter_combo.currentTextChanged.connect(self._on_adapter_selection_changed)
        
        # 刷新网卡列表
        self.refresh_btn.clicked.connect(self.refresh_adapters.emit)
        
        # 网卡操作按钮 - 传递友好名称而不是描述
        self.enable_adapter_btn.clicked.connect(
            lambda: self.enable_adapter.emit(self._get_current_adapter_friendly_name())
        )
        self.disable_adapter_btn.clicked.connect(
            lambda: self.disable_adapter.emit(self._get_current_adapter_friendly_name())
        )
        self.set_static_btn.clicked.connect(
            lambda: self.modify_mac_address.emit(self._get_current_adapter_friendly_name())
        )
        self.set_dhcp_btn.clicked.connect(
            lambda: self.set_dhcp.emit(self._get_current_adapter_friendly_name())
        )
        
        # 复制网卡信息
        self.copy_info_btn.clicked.connect(self.copy_adapter_info.emit)
    
    def _on_adapter_selection_changed(self, description):
        """
        处理网卡选择变更事件
        
        Args:
            description (str): 网卡描述（下拉框显示的文本）
        """
        friendly_name = self._get_current_adapter_friendly_name()
        self.adapter_selected.emit(friendly_name)
    
    def _get_current_adapter_friendly_name(self):
        """
        获取当前选中网卡的友好名称
        
        Returns:
            str: 网卡友好名称，如果未找到则返回描述
        """
        current_description = self.adapter_combo.currentText()
        return self._adapter_name_mapping.get(current_description, current_description)
    
    def update_adapter_list(self, adapter_names, name_mapping=None):
        """
        更新网卡下拉框列表
        
        Args:
            adapter_names (list): 网卡名称列表
            name_mapping (dict): 描述到友好名称的映射字典
        """
        # 记住当前选中的网卡
        current_selection = self.adapter_combo.currentText()
        
        # 临时阻塞信号，避免UI更新时触发adapter_selected信号导致无限循环
        self.adapter_combo.blockSignals(True)
        try:
            self.adapter_combo.clear()
            self.adapter_combo.addItems(adapter_names)
            
            # 恢复之前的选择（如果该网卡仍在列表中）
            if current_selection and current_selection in adapter_names:
                index = adapter_names.index(current_selection)
                self.adapter_combo.setCurrentIndex(index)
                
        finally:
            # 恢复信号，确保用户后续操作能正常触发事件
            self.adapter_combo.blockSignals(False)
        
        # 更新映射关系
        if name_mapping:
            self._adapter_name_mapping.update(name_mapping)
    
    def update_ip_info_display(self, formatted_info):
        """
        更新IP信息展示区域
        
        Args:
            formatted_info (str): 格式化的网卡信息文本
        """
        self.ip_info_display.setPlainText(formatted_info)
    
    def update_status_badges(self, connection_display_text, connection_status_attr, 
                           ip_mode_display_text, ip_mode_attr, link_speed_display_text):
        """
        更新网络状态徽章显示
        
        UI层只负责接收Service层格式化好的显示文本和属性，直接设置到控件上。
        不包含任何业务逻辑判断，严格遵循UI层只收信号的原则。
        
        Args:
            connection_display_text (str): Service层格式化的连接状态显示文本（含Emoji）
            connection_status_attr (str): 连接状态属性值（用于QSS选择器）
            ip_mode_display_text (str): Service层格式化的IP模式显示文本（含Emoji）
            ip_mode_attr (str): IP模式属性值（用于QSS选择器）
            link_speed_display_text (str): Service层格式化的链路速度显示文本（含Emoji）
        """
        # 直接设置Service层格式化好的显示文本
        self.connection_status_badge.setText(connection_display_text)
        self.connection_status_badge.setProperty("status", connection_status_attr)
        
        self.ip_mode_badge.setText(ip_mode_display_text)
        self.ip_mode_badge.setProperty("mode", ip_mode_attr)
        
        self.link_speed_badge.setText(link_speed_display_text)
        
        # 刷新样式以应用新的属性选择器
        self.connection_status_badge.style().unpolish(self.connection_status_badge)
        self.connection_status_badge.style().polish(self.connection_status_badge)
        self.ip_mode_badge.style().unpolish(self.ip_mode_badge)
        self.ip_mode_badge.style().polish(self.ip_mode_badge)
