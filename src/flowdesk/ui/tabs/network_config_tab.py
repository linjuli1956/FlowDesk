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

from ..widgets.validators import IPAddressValidator, SubnetMaskValidator, DNSValidator
from ..dialogs import AddIPDialog


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
        self._setup_validators()
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
        self.ip_info_display.setText("请选择网络适配器以查看详细信息...")  # 设置初始提示文本
        
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
        # 网络管理标题 - 遵循严格自适应布局原则
        self.network_mgmt_title = QLabel("⚙️ 网络管理")
        self.network_mgmt_title.setObjectName("network_mgmt_title")
        self.network_mgmt_title.setWordWrap(True)   # 启用文字换行，避免内容被截断
        
        # IP配置容器 - 遵循严格自适应布局原则，设置最小高度适应间距
        self.ip_config_frame = QGroupBox()
        self.ip_config_frame.setObjectName("ip_config_frame")
        self.ip_config_frame.setMinimumHeight(280)  # 设置最小高度确保间距显示
        
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
        
        # 额外IP管理标题 - 遵循严格自适应布局原则
        self.extra_ip_title = QLabel("🔍 当前额外IP管理")
        self.extra_ip_title.setObjectName("extra_ip_title")
        self.extra_ip_title.setWordWrap(True)   # 启用文字换行，避免内容被截断
        
        # 额外IP列表容器 - 支持滚动和多选，遵循严格自适应布局原则
        self.extra_ip_list = QListWidget()
        self.extra_ip_list.setObjectName("extra_ip_list")
        self.extra_ip_list.setToolTip("额外IP地址列表，可多选进行批量操作")
        self.extra_ip_list.setMinimumHeight(100)  # 设置最小高度，保证内容可见性
        
        # 额外IP操作按钮组 - 缩短文字内容减少按钮宽度
        self.add_selected_ip_btn = QPushButton("➕ 添加选中")
        self.add_selected_ip_btn.setObjectName("add_selected_ip_btn")
        
        self.remove_selected_ip_btn = QPushButton("➖ 删除选中")
        self.remove_selected_ip_btn.setObjectName("remove_selected_ip_btn")
        
        self.add_extra_ip_btn = QPushButton("🆕 添加IP")
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
        main_layout.setContentsMargins(4, 8, 2, 8)  # 最小化左右边距，极致压缩空白区域
        main_layout.setSpacing(0)   # 设置左右分栏间距为0，最小化中间空白区域
        
        # 左侧布局区域
        left_layout = self._create_left_layout()
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setMinimumWidth(300)  # 最小宽度保护
        left_widget.setMaximumWidth(300)  # 固定宽度，不随窗口缩放
        
        # 右侧布局区域 - 严格控制宽度防止溢出
        right_layout = self._create_right_layout()
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        right_widget.setMinimumWidth(340)  # 最小宽度保护（UI四大铁律）
        right_widget.setMaximumWidth(340)  # 最大宽度限制，防止在660px窗口中溢出
        
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
        layout.setSpacing(4)  # 减少左侧内部控件间距
        
        # 第一行：网卡选择 + 刷新按钮
        top_row_layout = QHBoxLayout()
        top_row_layout.addWidget(self.adapter_combo, 1)  # 拉伸因子1，占据大部分空间
        top_row_layout.addWidget(self.refresh_btn, 0)    # 拉伸因子0，保持固定尺寸
        layout.addLayout(top_row_layout)
        
        # IP信息标题
        layout.addWidget(self.ip_info_title)
        
        # IP信息展示容器 - 占据主要空间（315px）
        layout.addWidget(self.ip_info_display, 1)  # 拉伸因子1，随窗口高度调整
        
        # 状态徽章区域 - 调整布局避免重叠
        badges_layout = QHBoxLayout(self.status_badges_frame)
        badges_layout.setContentsMargins(0, 0, 0, 0)  # 移除容器边距
        badges_layout.setSpacing(0)  # 减少徽章间距，让网速徽章往前移
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
        layout.setSpacing(4)  # 减少右侧内部控件间距
        
        # 网络管理标题
        layout.addWidget(self.network_mgmt_title)
        
        # IP配置区域 - 使用QVBoxLayout确保间距生效
        ip_config_layout = QVBoxLayout(self.ip_config_frame)
        ip_config_layout.setSpacing(8)  # 设置容器间距
        
        # 创建5行表单，每行使用QHBoxLayout
        for i, (label, input_widget) in enumerate([
            (self.ip_address_label, self.ip_address_input),
            (self.subnet_mask_label, self.subnet_mask_input), 
            (self.gateway_label, self.gateway_input),
            (self.primary_dns_label, self.primary_dns_input),
            (self.secondary_dns_label, self.secondary_dns_input)
        ]):
            # 创建每行的水平布局
            row_layout = QHBoxLayout()
            row_layout.addWidget(label)
            row_layout.addWidget(input_widget, 1)  # 输入框拉伸
            
            # 添加到垂直布局，每行之间添加间距
            ip_config_layout.addLayout(row_layout)
            if i < 4:  # 前4行后面添加间距
                ip_config_layout.addSpacing(20)  # 20px垂直间距，确保明显的视觉分离
        
        # 添加更大的垂直间距，将当前网卡和按钮向下移动
        ip_config_layout.addSpacing(24)
        
        # 当前网卡显示
        ip_config_layout.addWidget(self.current_adapter_label)
        
        # 确定修改按钮 - 居中对齐
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.apply_config_btn)
        btn_layout.addStretch()
        ip_config_layout.addLayout(btn_layout)
        
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

    def _setup_validators(self):
        """
        为网络配置输入框设置实时验证器
        
        作用说明：
        这个方法负责为右侧的五个网络配置输入框设置对应的实时验证器，
        实现"实时禁止"无效输入的功能。每个输入框都配置了专门的验证器，
        确保用户只能输入符合网络参数规范的内容。
        
        验证器配置：
        - IP地址输入框：IPAddressValidator - 验证IPv4地址格式
        - 子网掩码输入框：SubnetMaskValidator - 验证子网掩码格式（支持点分十进制和CIDR）
        - 网关输入框：IPAddressValidator - 验证网关IP地址格式
        - 主DNS输入框：DNSValidator - 验证DNS服务器IP地址格式
        - 备用DNS输入框：DNSValidator - 验证备用DNS服务器IP地址格式
        
        设计原则：
        - 遵循面向对象封装原则，将验证逻辑封装在独立的验证器类中
        - 实现代码复用，IP地址和DNS地址使用相同的验证器
        - 确保UI层零业务逻辑，验证逻辑完全委托给验证器类
        """
        # 创建验证器实例
        # IP地址验证器：用于IP地址和网关输入框
        ip_validator = IPAddressValidator()
        
        # 子网掩码验证器：专门处理子网掩码格式
        subnet_mask_validator = SubnetMaskValidator()
        
        # DNS验证器：用于主DNS和备用DNS输入框
        dns_validator = DNSValidator()
        
        # 为输入框设置对应的验证器
        # 这些验证器会在用户输入时实时工作，阻止无效字符的输入
        self.ip_address_input.setValidator(ip_validator)
        self.subnet_mask_input.setValidator(subnet_mask_validator)
        self.gateway_input.setValidator(ip_validator)  # 网关也是IP地址，复用IP验证器
        self.primary_dns_input.setValidator(dns_validator)
        self.secondary_dns_input.setValidator(dns_validator)

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
        显示添加额外IP地址对话框
        
        作用说明：
        当用户点击"添加IP"按钮时，弹出专用的IP地址配置对话框。
        该对话框提供标准化的IP地址和子网掩码输入界面，集成了
        实时输入验证功能，确保用户只能输入有效的网络参数。
        
        设计特点：
        - 使用模态对话框，确保用户专注于IP配置输入
        - 集成QValidator实时验证，防止无效输入
        - 通过信号槽机制处理用户输入结果
        - 遵循面向对象设计，对话框逻辑完全封装
        
        交互流程：
        1. 创建AddIPDialog实例并显示
        2. 用户在对话框中输入IP地址和子网掩码
        3. 实时验证确保输入格式正确
        4. 用户点击确定后，对话框发射ip_added信号
        5. 处理信号，将新IP信息传递给服务层
        """
        # 创建添加IP对话框实例，设置当前窗口为父窗口确保正确的模态行为
        dialog = AddIPDialog(self)
        
        # 连接对话框的ip_added信号到处理方法
        # 当用户成功添加IP时，对话框会发射此信号携带IP配置数据
        dialog.ip_added.connect(self._handle_ip_added)
        
        # 显示模态对话框
        # exec_()方法会阻塞程序执行，直到对话框被关闭
        # 返回值指示用户是点击了确定(QDialog.Accepted)还是取消(QDialog.Rejected)
        result = dialog.exec_()
        
        # 注意：这里不需要手动处理返回值，因为ip_added信号已经处理了确定的情况
        # 如果用户取消或关闭对话框，不会有任何操作，这是期望的行为

    def _handle_ip_added(self, ip_address: str, subnet_mask: str):
        """
        处理添加IP对话框的确认操作
        
        作用说明：
        当用户在添加IP对话框中输入有效的IP配置并点击确定时，此方法负责
        将新的IP配置直接添加到右侧的额外IP列表中。新添加的IP会显示在
        列表的第一位，确保用户能够立即看到刚刚添加的内容。
        
        这个方法体现了UI层的直接响应性设计原则：用户的操作应该立即在
        界面上得到反馈，而不需要等待后端处理。同时，它也会将IP配置
        信息传递给服务层进行实际的网络配置操作。
        
        参数说明：
            ip_address (str): 用户输入的IP地址（如：192.168.1.100）
            subnet_mask (str): 用户输入的子网掩码（如：255.255.255.0或/24）
        
        处理逻辑：
        1. 格式化IP地址和子网掩码为标准显示格式
        2. 创建新的列表项并添加到额外IP列表的第一位
        3. 设置复选框状态，允许用户后续选择操作
        4. 同时发射信号给服务层进行实际的网络配置
        """
        # 格式化IP配置为标准显示格式
        # 统一使用 "IP地址 / 子网掩码" 的格式显示
        ip_config_text = f"{ip_address} / {subnet_mask}"
        
        # 创建新的列表项用于显示额外IP
        # QListWidgetItem封装了列表项的数据和显示属性
        new_item = QListWidgetItem(ip_config_text)
        new_item.setFlags(new_item.flags() | Qt.ItemIsUserCheckable)  # 设置可勾选
        new_item.setCheckState(Qt.Unchecked)  # 默认未选中状态
        
        # 将新项目插入到列表的第一位（索引0）
        # 这确保了最新添加的IP配置总是显示在最顶部，用户可以立即看到
        self.extra_ip_list.insertItem(0, new_item)
        
        # 自动滚动到列表顶部，确保新添加的项目在可视区域内
        self.extra_ip_list.scrollToTop()
        
        # 获取当前选择的网卡名称，用于服务层处理
        current_adapter = self.adapter_combo.currentText()
        
        # 同时发射信号给服务层进行实际的网络配置操作
        # 这保持了UI层与服务层的解耦，UI负责界面更新，服务层负责业务逻辑
        self.add_extra_ip.emit(current_adapter, ip_config_text)

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
    
    def update_adapter_list(self, adapter_names):
        """
        更新网卡下拉框列表
        
        这个方法负责将服务层传递的网卡名称列表更新到UI下拉框中。
        遵循项目架构原则，所有样式控制通过QSS文件管理，
        此方法只负责数据更新，不涉及任何样式设置。
        
        Args:
            adapter_names (list): 网卡名称列表，包含完整的网卡描述信息
        """
        # 清空现有的下拉框项目，准备加载新的网卡列表
        self.adapter_combo.clear()
        
        # 将网卡名称列表添加到下拉框中
        # 下拉列表的显示效果完全由QSS样式文件控制
        self.adapter_combo.addItems(adapter_names)

    def update_ip_info_display(self, formatted_info):
        """
        更新IP信息展示区域的核心显示逻辑
        
        这个方法负责将服务层传递的格式化网卡信息显示在右侧的信息展示区域。
        采用面向对象的设计原则，将UI更新逻辑封装在独立方法中，确保界面
        显示与数据状态的实时同步。这是解决"IP信息展示容器不更新"问题的
        关键UI组件更新方法。
        
        功能特点：
        1. 接收主窗口传递的完整格式化信息
        2. 直接更新文本显示组件的内容
        3. 确保用户能够看到最新的网卡配置信息
        4. 支持实时刷新，响应网卡选择和刷新操作
        
        Args:
            formatted_info (str): 经过格式化处理的网卡详细信息文本，
                                包含IP地址、子网掩码、网关、DNS等完整配置
        """
        # 直接更新文本显示组件，确保信息的实时同步
        # 这里使用setText方法完全替换现有内容，避免信息累积或残留
        self.ip_info_display.setText(formatted_info)
        
        # 确保文本显示区域滚动到顶部，便于用户查看完整信息
        # 这提供了更好的用户体验，特别是在信息较长时
        cursor = self.ip_info_display.textCursor()
        cursor.movePosition(cursor.Start)
        self.ip_info_display.setTextCursor(cursor)

    def update_status_badge(self, status_text, is_connected):
        """
        更新网卡连接状态徽章的显示内容和样式
        
        该方法负责根据网卡的实际连接状态，动态更新状态徽章的显示效果。
        通过改变徽章的文本内容和CSS类名，实现图形化的状态区分，替代纯文本显示。
        
        设计理念：
        - 使用图形化徽章替代纯文本，提升视觉识别度
        - 通过QSS样式表实现不同状态的背景色和文字色
        - 支持动态切换连接和断开状态的显示样式
        
        Args:
            status_text (str): 状态显示文本，如"已连接"、"未连接"
            is_connected (bool): 连接状态标识，True表示已连接，False表示未连接
        """
        # 更新状态徽章的显示文本，去除emoji图标，使用纯文本
        # 图形化效果通过QSS背景色实现，而非文本图标
        clean_text = status_text.replace("🔗 ", "").strip()
        self.connection_status_badge.setText(clean_text)
        
        # 根据连接状态设置不同的样式类名
        # 已连接：绿色背景徽章；未连接：灰色背景徽章
        if is_connected:
            self.connection_status_badge.setObjectName("status_badge_connected")
        else:
            self.connection_status_badge.setObjectName("status_badge_disconnected")
        
        # 强制刷新样式，确保objectName变更立即生效
        # 调用style().unpolish()和style().polish()确保样式重新应用
        self.connection_status_badge.style().unpolish(self.connection_status_badge)
        self.connection_status_badge.style().polish(self.connection_status_badge)

    def update_status_badges(self, connection_status, ip_mode, link_speed):
        """
        更新多个状态徽章的批量显示方法
        
        该方法用于一次性更新所有状态徽章的显示内容，
        包括连接状态、IP配置模式、链路速度等关键网络参数。
        
        Args:
            connection_status (str): 连接状态描述
            ip_mode (str): IP配置模式（如DHCP、静态IP）
            link_speed (str): 网络链路速度
        """
        self.connection_status_badge.setText(f"🔗 {connection_status}")
        self.ip_mode_badge.setText(f"🌐 {ip_mode}")
        self.link_speed_badge.setText(f"⚡ {link_speed}")

    def update_ip_config_inputs(self, config_data):
        """
        更新IP配置输入框的显示内容
        
        Args:
            config_data (dict): IP配置数据字典，包含各项网络配置参数
        """
        self.ip_address_input.setText(config_data.get('ip_address', ''))
        self.subnet_mask_input.setText(config_data.get('subnet_mask', ''))
        self.gateway_input.setText(config_data.get('gateway', ''))
        self.primary_dns_input.setText(config_data.get('dns_primary', ''))
        self.secondary_dns_input.setText(config_data.get('dns_secondary', ''))

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
