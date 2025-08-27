#!/usr/bin/env python3
"""
网络配置Tab页面 - FlowDesk网络管理核心界面

这个模块实现网络配置的用户界面，采用左右分栏布局设计：
- 左侧(300px)：网卡选择、IP信息展示、状态徽章、网卡操作按钮
- 右侧(340px)：IP配置输入、额外IP管理功能

设计原则：
1. 严格遵循UI四大铁律：禁止样式重复、自适应布局、最小宽度保护、智能组件缩放
2. 纯UI层实现，零业务逻辑，通过信号槽与服务层通信
3. 所有样式通过外置QSS文件控制，禁止内联样式
4. 智能组件缩放：输入框可拉伸，按钮固定尺寸，容器自适应
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QFormLayout,
    QComboBox, QPushButton, QLineEdit, QTextEdit, QLabel, 
    QGroupBox, QFrame, QScrollArea, QCheckBox, QListWidget,
    QListWidgetItem, QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont


class NetworkConfigTab(QWidget):
    """
    网络配置Tab页面主类
    
    负责网络配置界面的布局和交互，采用面向对象设计：
    - 封装所有UI组件的创建和布局逻辑
    - 提供信号接口供服务层连接
    - 实现响应式布局和智能缩放
    """
    
    # 信号定义：与服务层通信的接口
    adapter_selected = pyqtSignal(str)  # 网卡选择变更信号
    refresh_adapters = pyqtSignal()     # 刷新网卡列表信号
    apply_ip_config = pyqtSignal(dict)  # 应用IP配置信号
    enable_adapter = pyqtSignal(str)    # 启用网卡信号
    disable_adapter = pyqtSignal(str)   # 禁用网卡信号
    set_static_ip = pyqtSignal(str)     # 设置静态IP信号
    set_dhcp = pyqtSignal(str)          # 设置DHCP信号
    copy_adapter_info = pyqtSignal()    # 复制网卡信息信号
    add_extra_ip = pyqtSignal(str, str) # 添加额外IP信号
    remove_extra_ip = pyqtSignal(list)  # 删除额外IP信号

    def __init__(self, parent=None):
        """
        初始化网络配置Tab页面
        
        创建左右分栏布局，初始化所有UI组件，设置智能缩放策略。
        严格遵循660×645主窗口尺寸约束和UI四大铁律。
        """
        super().__init__(parent)
        self.setObjectName("network_config_tab")
        
        # 设置最小尺寸保护，防止界面压缩变形
        self.setMinimumSize(648, 533)  # Tab页面可用空间
        
        # 初始化UI组件
        self._init_ui()
        self._setup_layouts()
        self._connect_signals()
        self._apply_size_policies()

    def _init_ui(self):
        """
        初始化所有UI组件
        
        创建左右两侧的所有控件，设置objectName用于QSS样式控制。
        每个控件都有明确的作用和语义化的命名。
        """
        # === 左侧区域组件 ===
        self._init_left_side_components()
        
        # === 右侧区域组件 ===
        self._init_right_side_components()

    def _init_left_side_components(self):
        """
        初始化左侧区域的所有组件
        
        包括网卡选择、IP信息展示、状态徽章、操作按钮等。
        每个组件都设置了合适的objectName用于QSS样式定位。
        """
        # 网卡选择下拉框 - 支持智能缩放，宽度可随容器调整
        self.adapter_combo = QComboBox()
        self.adapter_combo.setObjectName("adapter_combo")
        self.adapter_combo.setToolTip("选择要配置的网络适配器")
        
        # 刷新按钮 - 固定尺寸，不随窗口缩放
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.setObjectName("refresh_btn")
        self.refresh_btn.setToolTip("刷新网络适配器列表")
        
        # IP信息标题标签
        self.ip_info_title = QLabel("📊 当前IP信息")
        self.ip_info_title.setObjectName("ip_info_title")
        
        # IP信息展示容器 - 可选中文字但不可编辑，支持Ctrl+C复制
        self.ip_info_display = QTextEdit()
        self.ip_info_display.setObjectName("ip_info_display")
        self.ip_info_display.setReadOnly(True)  # 只读模式，支持文字选择和复制
        self.ip_info_display.setToolTip("网卡详细信息，可选中文字并使用Ctrl+C复制")
        
        # 状态徽章容器 - 放置在IP信息容器底部
        self.status_badges_frame = QFrame()
        self.status_badges_frame.setObjectName("status_badges_frame")
        
        # 三个状态徽章 - 圆角设计，颜色语义化
        self.connection_status_badge = QLabel("🔗 已连接")
        self.connection_status_badge.setObjectName("connection_status_badge")
        
        self.ip_mode_badge = QLabel("🌐 静态IP")
        self.ip_mode_badge.setObjectName("ip_mode_badge")
        
        self.link_speed_badge = QLabel("⚡ 1000Mbps")
        self.link_speed_badge.setObjectName("link_speed_badge")
        
        # 网卡操作按钮组 - 渐变色设计
        self.enable_adapter_btn = QPushButton("⚡ 启用网卡")
        self.enable_adapter_btn.setObjectName("enable_adapter_btn")
        
        self.disable_adapter_btn = QPushButton("🚫 禁用网卡")
        self.disable_adapter_btn.setObjectName("disable_adapter_btn")
        
        self.set_static_btn = QPushButton("🌐 设置静态IP")
        self.set_static_btn.setObjectName("set_static_btn")
        
        self.set_dhcp_btn = QPushButton("🌐 设置DHCP")
        self.set_dhcp_btn.setObjectName("set_dhcp_btn")
        
        self.copy_info_btn = QPushButton("📋 复制网卡信息")
        self.copy_info_btn.setObjectName("copy_info_btn")

    def _init_right_side_components(self):
        """
        初始化右侧区域的所有组件
        
        包括网络管理标题、IP配置输入区域、额外IP管理等。
        输入框支持智能缩放，标签固定尺寸。
        """
        # 网络管理标题
        self.network_mgmt_title = QLabel("⚙️ 网络管理")
        self.network_mgmt_title.setObjectName("network_mgmt_title")
        
        # IP配置容器
        self.ip_config_frame = QGroupBox()
        self.ip_config_frame.setObjectName("ip_config_frame")
        
        # IP配置输入框组 - 支持智能缩放
        self.ip_address_label = QLabel("IP地址：")
        self.ip_address_label.setObjectName("config_label")
        self.ip_address_input = QLineEdit()
        self.ip_address_input.setObjectName("ip_address_input")
        self.ip_address_input.setPlaceholderText("例如：192.168.1.100")
        
        self.subnet_mask_label = QLabel("子网掩码：")
        self.subnet_mask_label.setObjectName("config_label")
        self.subnet_mask_input = QLineEdit()
        self.subnet_mask_input.setObjectName("subnet_mask_input")
        self.subnet_mask_input.setPlaceholderText("例如：255.255.255.0")
        
        self.gateway_label = QLabel("网关：")
        self.gateway_label.setObjectName("config_label")
        self.gateway_input = QLineEdit()
        self.gateway_input.setObjectName("gateway_input")
        self.gateway_input.setPlaceholderText("例如：192.168.1.1")
        
        self.primary_dns_label = QLabel("主DNS：")
        self.primary_dns_label.setObjectName("config_label")
        self.primary_dns_input = QLineEdit()
        self.primary_dns_input.setObjectName("primary_dns_input")
        self.primary_dns_input.setPlaceholderText("例如：8.8.8.8")
        
        self.secondary_dns_label = QLabel("备用DNS：")
        self.secondary_dns_label.setObjectName("config_label")
        self.secondary_dns_input = QLineEdit()
        self.secondary_dns_input.setObjectName("secondary_dns_input")
        self.secondary_dns_input.setPlaceholderText("例如：8.8.4.4")
        
        # 当前网卡显示
        self.current_adapter_label = QLabel("当前网卡：本地连接")
        self.current_adapter_label.setObjectName("current_adapter_label")
        
        # 确定修改按钮 - 居中显示
        self.apply_config_btn = QPushButton("✅ 确定修改IP")
        self.apply_config_btn.setObjectName("apply_config_btn")
        
        # 额外IP管理区域
        self.extra_ip_title = QLabel("📝 当前额外IP管理")
        self.extra_ip_title.setObjectName("extra_ip_title")
        
        # 额外IP列表容器 - 支持滚动和多选
        self.extra_ip_list = QListWidget()
        self.extra_ip_list.setObjectName("extra_ip_list")
        self.extra_ip_list.setToolTip("额外IP地址列表，可多选进行批量操作")
        
        # 额外IP操作按钮组
        self.add_selected_ip_btn = QPushButton("➕ 添加选中IP")
        self.add_selected_ip_btn.setObjectName("add_selected_ip_btn")
        
        self.remove_selected_ip_btn = QPushButton("➖ 删除选中IP")
        self.remove_selected_ip_btn.setObjectName("remove_selected_ip_btn")
        
        self.add_extra_ip_btn = QPushButton("🆕 添加额外IP")
        self.add_extra_ip_btn.setObjectName("add_extra_ip_btn")

    def _setup_layouts(self):
        """
        设置布局管理器
        
        采用响应式布局设计，严格遵循UI四大铁律：
        1. 使用QLayout实现自适应布局，禁止绝对定位
        2. 设置最小宽度保护，防止控件重叠
        3. 智能组件缩放：输入框可拉伸，按钮保持固定尺寸
        """
        # 主布局：水平分栏（左300px + 右340px）
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)  # 设置边距
        main_layout.setSpacing(12)  # 设置左右分栏间距
        
        # 左侧布局区域
        left_layout = self._create_left_layout()
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setMinimumWidth(300)  # 最小宽度保护
        left_widget.setMaximumWidth(300)  # 固定宽度，不随窗口缩放
        
        # 右侧布局区域
        right_layout = self._create_right_layout()
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        right_widget.setMinimumWidth(340)  # 最小宽度保护
        
        # 添加到主布局
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)

    def _create_left_layout(self):
        """
        创建左侧区域布局
        
        垂直布局，从上到下依次排列各个功能区域。
        合理分配空间，确保在533px高度内不会产生遮挡。
        """
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # 第一行：网卡选择 + 刷新按钮
        top_row_layout = QHBoxLayout()
        top_row_layout.addWidget(self.adapter_combo, 1)  # 拉伸因子1，占据大部分空间
        top_row_layout.addWidget(self.refresh_btn, 0)    # 拉伸因子0，保持固定尺寸
        layout.addLayout(top_row_layout)
        
        # IP信息标题
        layout.addWidget(self.ip_info_title)
        
        # IP信息展示容器 - 占据主要空间（315px）
        layout.addWidget(self.ip_info_display, 1)  # 拉伸因子1，随窗口高度调整
        
        # 状态徽章区域
        badges_layout = QHBoxLayout(self.status_badges_frame)
        badges_layout.addWidget(self.connection_status_badge)
        badges_layout.addWidget(self.ip_mode_badge)
        badges_layout.addWidget(self.link_speed_badge)
        badges_layout.addStretch()  # 添加弹性空间
        layout.addWidget(self.status_badges_frame)
        
        # 操作按钮组 - 分三行排列
        # 第一行：启用/禁用按钮
        btn_row1_layout = QHBoxLayout()
        btn_row1_layout.addWidget(self.enable_adapter_btn)
        btn_row1_layout.addWidget(self.disable_adapter_btn)
        layout.addLayout(btn_row1_layout)
        
        # 第二行：静态IP/DHCP按钮
        btn_row2_layout = QHBoxLayout()
        btn_row2_layout.addWidget(self.set_static_btn)
        btn_row2_layout.addWidget(self.set_dhcp_btn)
        layout.addLayout(btn_row2_layout)
        
        # 第三行：复制信息按钮
        layout.addWidget(self.copy_info_btn)
        
        return layout

    def _create_right_layout(self):
        """
        创建右侧区域布局
        
        垂直布局，包含网络管理标题、IP配置区域、额外IP管理区域。
        使用FormLayout实现标签和输入框的对齐。
        """
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # 网络管理标题
        layout.addWidget(self.network_mgmt_title)
        
        # IP配置区域
        ip_config_layout = QFormLayout(self.ip_config_frame)
        ip_config_layout.setSpacing(8)
        ip_config_layout.addRow(self.ip_address_label, self.ip_address_input)
        ip_config_layout.addRow(self.subnet_mask_label, self.subnet_mask_input)
        ip_config_layout.addRow(self.gateway_label, self.gateway_input)
        ip_config_layout.addRow(self.primary_dns_label, self.primary_dns_input)
        ip_config_layout.addRow(self.secondary_dns_label, self.secondary_dns_input)
        
        # 当前网卡显示
        ip_config_layout.addRow(self.current_adapter_label)
        
        # 确定修改按钮 - 居中对齐
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.apply_config_btn)
        btn_layout.addStretch()
        ip_config_layout.addRow(btn_layout)
        
        layout.addWidget(self.ip_config_frame)
        
        # 额外IP管理区域
        layout.addWidget(self.extra_ip_title)
        layout.addWidget(self.extra_ip_list, 1)  # 拉伸因子1，占据剩余空间
        
        # 额外IP操作按钮 - 水平排列
        extra_ip_btn_layout = QHBoxLayout()
        extra_ip_btn_layout.addWidget(self.add_selected_ip_btn)
        extra_ip_btn_layout.addWidget(self.remove_selected_ip_btn)
        extra_ip_btn_layout.addWidget(self.add_extra_ip_btn)
        layout.addLayout(extra_ip_btn_layout)
        
        return layout

    def _apply_size_policies(self):
        """
        应用智能组件缩放策略
        
        根据UI四大铁律中的"智能组件缩放"原则：
        - 输入框：水平Expanding，随窗口宽度调整
        - 按钮：Fixed/Preferred，保持固定尺寸不变形
        - 容器：Expanding，充分利用可用空间
        - 标签：Fixed，保持内容尺寸
        """
        # 输入框 - 水平可拉伸，垂直固定
        input_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.adapter_combo.setSizePolicy(input_policy)
        self.ip_address_input.setSizePolicy(input_policy)
        self.subnet_mask_input.setSizePolicy(input_policy)
        self.gateway_input.setSizePolicy(input_policy)
        self.primary_dns_input.setSizePolicy(input_policy)
        self.secondary_dns_input.setSizePolicy(input_policy)
        
        # 按钮 - 保持固定尺寸，不随窗口变形
        button_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        for btn in [self.refresh_btn, self.enable_adapter_btn, self.disable_adapter_btn,
                   self.set_static_btn, self.set_dhcp_btn, self.copy_info_btn,
                   self.apply_config_btn, self.add_selected_ip_btn, 
                   self.remove_selected_ip_btn, self.add_extra_ip_btn]:
            btn.setSizePolicy(button_policy)
        
        # 容器 - 充分利用可用空间
        expanding_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ip_info_display.setSizePolicy(expanding_policy)
        self.extra_ip_list.setSizePolicy(expanding_policy)

    def _connect_signals(self):
        """
        连接信号槽
        
        将UI事件连接到对应的信号，供服务层监听和处理。
        遵循面向对象架构原则：UI层只负责发射信号，不处理业务逻辑。
        """
        # 网卡选择变更
        self.adapter_combo.currentTextChanged.connect(
            lambda text: self.adapter_selected.emit(text)
        )
        
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
        
        # IP配置应用
        self.apply_config_btn.clicked.connect(self._emit_ip_config)
        
        # 额外IP操作
        self.add_extra_ip_btn.clicked.connect(self._show_add_ip_dialog)
        self.remove_selected_ip_btn.clicked.connect(self._remove_selected_ips)

    def _emit_ip_config(self):
        """
        发射IP配置信号
        
        收集所有输入框的数据，组装成字典格式发射给服务层。
        UI层只负责数据收集，不进行验证和处理。
        """
        config_data = {
            'ip_address': self.ip_address_input.text().strip(),
            'subnet_mask': self.subnet_mask_input.text().strip(),
            'gateway': self.gateway_input.text().strip(),
            'primary_dns': self.primary_dns_input.text().strip(),
            'secondary_dns': self.secondary_dns_input.text().strip(),
            'adapter': self.adapter_combo.currentText()
        }
        self.apply_ip_config.emit(config_data)

    def _show_add_ip_dialog(self):
        """
        显示添加额外IP对话框
        
        这里只是占位方法，实际的对话框实现会在dialogs模块中。
        遵循分层架构：UI组件各司其职。
        """
        # TODO: 实现添加IP对话框
        pass

    def _remove_selected_ips(self):
        """
        删除选中的额外IP
        
        获取列表中选中的项目，发射删除信号给服务层处理。
        """
        selected_items = self.extra_ip_list.selectedItems()
        selected_ips = [item.text() for item in selected_items]
        if selected_ips:
            self.remove_extra_ip.emit(selected_ips)

    # === 公共接口方法：供服务层调用更新UI ===
    
    def update_adapter_list(self, adapters):
        """
        更新网卡列表
        
        Args:
            adapters (list): 网卡名称列表
        """
        self.adapter_combo.clear()
        self.adapter_combo.addItems(adapters)

    def update_ip_info(self, info_text):
        """
        更新IP信息显示
        
        Args:
            info_text (str): 格式化的IP信息文本
        """
        self.ip_info_display.setPlainText(info_text)

    def update_status_badges(self, connection_status, ip_mode, link_speed):
        """
        更新状态徽章显示
        
        Args:
            connection_status (str): 连接状态
            ip_mode (str): IP模式
            link_speed (str): 链路速度
        """
        self.connection_status_badge.setText(f"🔗 {connection_status}")
        self.ip_mode_badge.setText(f"🌐 {ip_mode}")
        self.link_speed_badge.setText(f"⚡ {link_speed}")

    def update_ip_config_inputs(self, config_data):
        """
        更新IP配置输入框
        
        Args:
            config_data (dict): IP配置数据
        """
        self.ip_address_input.setText(config_data.get('ip_address', ''))
        self.subnet_mask_input.setText(config_data.get('subnet_mask', ''))
        self.gateway_input.setText(config_data.get('gateway', ''))
        self.primary_dns_input.setText(config_data.get('primary_dns', ''))
        self.secondary_dns_input.setText(config_data.get('secondary_dns', ''))

    def update_current_adapter_label(self, adapter_name):
        """
        更新当前网卡显示标签
        
        Args:
            adapter_name (str): 网卡简称
        """
        self.current_adapter_label.setText(f"当前网卡：{adapter_name}")

    def update_extra_ip_list(self, ip_list):
        """
        更新额外IP列表
        
        Args:
            ip_list (list): 额外IP地址列表
        """
        self.extra_ip_list.clear()
        for ip_info in ip_list:
            item = QListWidgetItem(ip_info)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.extra_ip_list.addItem(item)
