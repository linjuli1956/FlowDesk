# -*- coding: utf-8 -*-
"""
IP配置面板模块

负责创建和管理网络配置Tab页面右侧的IP配置面板，包括：
- 网络管理标题和IP配置输入框组
- 当前网卡显示和确定修改按钮
- 额外IP管理列表和操作按钮组
- 实时输入验证器设置

严格遵循UI四大铁律：
1. 🚫 禁止样式重复 - 通过objectName设置，样式在QSS中统一定义
2. 🔄 严格自适应布局 - 使用QVBoxLayout和QHBoxLayout实现响应式设计
3. 📏 最小宽度保护 - 设置合理的最小宽度防止控件重叠
4. ⚙️ 智能组件缩放 - 输入框可拉伸，按钮固定尺寸，列表自适应

作者: FlowDesk开发团队
创建时间: 2024年
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QPushButton, QLineEdit, QListWidget, QFrame, QListWidgetItem, QGroupBox,
    QAbstractItemView
)
from PyQt5.QtCore import pyqtSignal, Qt

from ..widgets.validators import IPAddressValidator, SubnetMaskValidator, DNSValidator


class IPConfigPanel(QWidget):
    """
    IP配置面板类
    
    继承自QWidget，封装右侧IP配置面板的所有UI组件和布局。
    作为独立的面板组件，提供完整的IP配置输入和额外IP管理功能。
    
    主要功能：
    - IP配置输入和验证
    - 当前网卡显示
    - 额外IP管理
    - 配置应用操作
    
    信号定义：
    - ip_config_applied: IP配置应用信号
    - add_extra_ip: 添加额外IP信号
    - add_selected_ips: 添加选中IP信号
    - remove_selected_ips: 删除选中IP信号
    """
    
    # 定义信号 - 用于与服务层通信
    ip_config_applied = pyqtSignal(dict)  # IP配置应用
    add_extra_ip = pyqtSignal()           # 添加额外IP
    add_selected_ips = pyqtSignal(str, list)   # 添加选中IP (adapter_name, ip_list)
    remove_selected_ips = pyqtSignal(str, list) # 删除选中IP (adapter_name, ip_list)
    
    def __init__(self, parent=None):
        """
        初始化IP配置面板
        
        创建所有UI组件并设置布局，遵循自适应设计原则。
        
        Args:
            parent: 父容器对象
        """
        super().__init__(parent)
        
        # 创建所有UI组件
        self._create_components()
        
        # 设置布局
        self._setup_layout()
        
        # 设置验证器
        self._setup_validators()
        
        # 连接信号槽
        self.setup_signals()
    
    def _create_components(self):
        """
        创建右侧面板的所有UI组件
        
        按照设计规范创建IP配置输入、验证器、额外IP管理等组件。
        每个组件都设置了objectName用于QSS样式控制。
        """
        # 网络管理标题 - 遵循严格自适应布局原则
        self.network_mgmt_title = QLabel("⚙️ 网络管理")
        self.network_mgmt_title.setObjectName("network_mgmt_title")
        self.network_mgmt_title.setWordWrap(True)   # 启用文字换行，避免内容被截断
        
        # IP配置容器 - 遵循严格自适应布局原则，移除固定高度限制
        self.ip_config_frame = QGroupBox()
        self.ip_config_frame.setObjectName("ip_config_frame")
        # 移除最小高度限制，让弹性布局生效
        
        # IP配置输入框组 - 支持智能缩放，统一标签宽度确保对齐
        self.ip_address_label = QLabel("🌐 IP地址：")
        self.ip_address_label.setObjectName("config_label")
        # 移除固定宽度设置，让标签自然宽度
        # 移除硬编码高度，由QSS统一控制样式
        self.ip_address_input = QLineEdit()
        self.ip_address_input.setObjectName("ip_address_input")
        self.ip_address_input.setPlaceholderText("例如：192.168.1.100")
        # 移除硬编码高度，由QSS统一控制样式
        
        self.subnet_mask_label = QLabel("🔢 子网掩码：")
        self.subnet_mask_label.setObjectName("config_label")
        # 移除固定宽度设置，让标签自然宽度
        # 移除硬编码高度，由QSS统一控制样式
        self.subnet_mask_input = QLineEdit()
        self.subnet_mask_input.setObjectName("subnet_mask_input")
        self.subnet_mask_input.setPlaceholderText("例如：255.255.255.0")
        # 移除硬编码高度，由QSS统一控制样式
        
        self.gateway_label = QLabel("📶🖧  网关：")
        self.gateway_label.setObjectName("config_label")
        # 移除固定宽度设置，让标签自然宽度
        # 移除硬编码高度，由QSS统一控制样式
        self.gateway_input = QLineEdit()
        self.gateway_input.setObjectName("gateway_input")
        self.gateway_input.setPlaceholderText("例如：192.168.1.1")
        # 移除硬编码高度，由QSS统一控制样式
        
        self.primary_dns_label = QLabel("🌍 主DNS：")
        self.primary_dns_label.setObjectName("config_label")
        # 移除固定宽度设置，让标签自然宽度
        # 移除硬编码高度，由QSS统一控制样式
        self.primary_dns_input = QLineEdit()
        self.primary_dns_input.setObjectName("primary_dns_input")
        self.primary_dns_input.setPlaceholderText("例如：8.8.8.8")
        # 移除硬编码高度，由QSS统一控制样式
        
        self.secondary_dns_label = QLabel("🌏 备用DNS：")
        self.secondary_dns_label.setObjectName("config_label")
        # 移除固定宽度设置，让标签自然宽度
        # 移除硬编码高度，由QSS统一控制样式
        self.secondary_dns_input = QLineEdit()
        self.secondary_dns_input.setObjectName("secondary_dns_input")
        self.secondary_dns_input.setPlaceholderText("例如：8.8.4.4")
        # 移除硬编码高度，由QSS统一控制样式
        
        # 当前网卡显示
        self.current_adapter_label = QLabel("🌤️ 当前网卡：本地连接")
        self.current_adapter_label.setObjectName("current_adapter_label")
        # 移除固定高度，使用弹性布局
        
        # 确定修改按钮 - 居中显示
        self.apply_config_btn = QPushButton("✅ 修改IP地址")
        self.apply_config_btn.setObjectName("apply_config_btn")
        # 移除固定高度，使用弹性布局
        
        # 额外IP管理标题 - 遵循严格自适应布局原则
        self.extra_ip_title = QLabel("🔍 当前额外IP管理")
        self.extra_ip_title.setObjectName("extra_ip_title")
        self.extra_ip_title.setWordWrap(True)   # 启用文字换行，避免内容被截断
        
        # 额外IP列表容器 - 支持滚动和多选，遵循严格自适应布局原则
        self.extra_ip_list = QListWidget()
        self.extra_ip_list.setObjectName("extra_ip_list")
        self.extra_ip_list.setMinimumHeight(120)
        self.extra_ip_list.setMaximumHeight(150)
        self.extra_ip_list.setSelectionMode(QAbstractItemView.MultiSelection)
        
        # 额外IP操作按钮组 - 缩短文字内容减少按钮宽度
        self.add_selected_ip_btn = QPushButton("➕ 添加选中")
        self.add_selected_ip_btn.setObjectName("add_selected_ip_btn")
        
        self.remove_selected_ip_btn = QPushButton("➖ 删除选中")
        self.remove_selected_ip_btn.setObjectName("remove_selected_ip_btn")
        
        self.add_extra_ip_btn = QPushButton("🆕 添加IP")
        self.add_extra_ip_btn.setObjectName("add_extra_ip_btn")
    
    def _setup_layout(self):
        """
        设置右侧面板的布局结构
        
        使用垂直布局作为主布局，包含网络管理标题、IP配置区域、当前网卡显示、
        确定按钮和额外IP管理区域。严格遵循自适应布局原则。
        """
        # 主布局 - 垂直排列
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 3, 8, 3)  # 进一步压缩上下边距
        main_layout.setSpacing(4)  # 进一步减少组件间距
        
        # 网络管理标题
        main_layout.addWidget(self.network_mgmt_title)
        
        # IP配置区域 - 使用垂直布局
        config_layout = QVBoxLayout(self.ip_config_frame)
        config_layout.setSpacing(5)  # 进一步压缩容器内间距
        config_layout.setContentsMargins(6, 5, 6, 3)  # 进一步压缩内边距
        
        # IP配置输入表单
        form_layout = QFormLayout()
        form_layout.setSpacing(20)  # 增加输入框间距以分散显示
        form_layout.setVerticalSpacing(20)  # 设置更大的垂直间距
        # 移除样式设置，由QSS统一管理对齐和间距
        form_layout.setRowWrapPolicy(QFormLayout.DontWrapRows)  # 确保行不换行
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)  # 输入框可扩展
        form_layout.setContentsMargins(0, 0, 0, 0)  # 移除表单内边距
        form_layout.addRow(self.ip_address_label, self.ip_address_input)
        form_layout.addRow(self.subnet_mask_label, self.subnet_mask_input)
        form_layout.addRow(self.gateway_label, self.gateway_input)
        form_layout.addRow(self.primary_dns_label, self.primary_dns_input)
        form_layout.addRow(self.secondary_dns_label, self.secondary_dns_input)
        
        config_layout.addLayout(form_layout)
        
        # 添加固定间距，将标签和按钮与输入框分开
        config_layout.addSpacing(15)  # 减少到10px固定间距，让备用DNS与当前网卡标签更贴近
        
        # 将标签和按钮组合在一个垂直布局中，移除间距
        bottom_layout = QVBoxLayout()
        bottom_layout.setSpacing(0)  # 移除标签和按钮间的间距
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.addWidget(self.current_adapter_label)
        bottom_layout.addWidget(self.apply_config_btn)
        
        config_layout.addLayout(bottom_layout)
        
        main_layout.addWidget(self.ip_config_frame)
        
        # 额外IP管理标题
        main_layout.addWidget(self.extra_ip_title)
        
        # 额外IP列表
        main_layout.addWidget(self.extra_ip_list, 1)  # 占据剩余空间
        
        # 额外IP操作按钮区域
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_extra_ip_btn)
        button_layout.addWidget(self.add_selected_ip_btn)
        button_layout.addWidget(self.remove_selected_ip_btn)
        main_layout.addLayout(button_layout)
    
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
    
    def setup_signals(self):
        """
        连接右侧面板组件的信号槽
        
        将UI事件连接到面板自身的信号，供父容器转发给服务层。
        """
        # IP配置应用 - 收集配置信息并发射信号
        self.apply_config_btn.clicked.connect(self._emit_ip_config)
        
        # 额外IP操作
        self.add_extra_ip_btn.clicked.connect(self.add_extra_ip.emit)
        
        # 额外IP批量管理操作
        self.add_selected_ip_btn.clicked.connect(self._emit_add_selected_ips)
        self.remove_selected_ip_btn.clicked.connect(self._emit_remove_selected_ips)
    
    def _emit_ip_config(self):
        """
        收集IP配置信息并发射信号
        
        从输入框收集所有IP配置信息，组装成字典格式发射给服务层。
        需要通过父容器获取当前选中的网卡信息。
        """
        # 获取父容器的网卡选择信息
        parent_tab = self.parent()
        if hasattr(parent_tab, 'adapter_info_panel') and hasattr(parent_tab.adapter_info_panel, 'adapter_combo'):
            current_adapter = parent_tab.adapter_info_panel.adapter_combo.currentText()
        else:
            current_adapter = ''
        
        config = {
            'ip_address': self.ip_address_input.text().strip(),
            'subnet_mask': self.subnet_mask_input.text().strip(),
            'gateway': self.gateway_input.text().strip(),
            'primary_dns': self.primary_dns_input.text().strip(),
            'secondary_dns': self.secondary_dns_input.text().strip(),
            'adapter': current_adapter  # 添加网卡信息
        }
        self.ip_config_applied.emit(config)
    
    def _emit_add_selected_ips(self):
        """
        发射添加选中IP信号
        
        获取额外IP列表中选中的项目并发射信号。
        """
        # 获取父容器的网卡选择信息
        parent_tab = self.parent()
        if hasattr(parent_tab, 'adapter_info_panel') and hasattr(parent_tab.adapter_info_panel, 'adapter_combo'):
            current_adapter = parent_tab.adapter_info_panel.adapter_combo.currentText()
        else:
            current_adapter = ''
            
        selected_items = self.extra_ip_list.selectedItems()
        selected_ips = [item.text() for item in selected_items]
        self.add_selected_ips.emit(current_adapter, selected_ips)
    
    def _emit_remove_selected_ips(self):
        """
        发射删除选中IP信号
        
        获取额外IP列表中勾选的项目并发射信号。
        """
        # 获取父容器的网卡选择信息
        parent_tab = self.parent()
        if hasattr(parent_tab, 'adapter_info_panel') and hasattr(parent_tab.adapter_info_panel, 'adapter_combo'):
            current_adapter = parent_tab.adapter_info_panel.adapter_combo.currentText()
        else:
            current_adapter = ''
            
        checked_ips = []
        for i in range(self.extra_ip_list.count()):
            item = self.extra_ip_list.item(i)
            if item.checkState() == Qt.Checked:
                checked_ips.append(item.text())
        self.remove_selected_ips.emit(current_adapter, checked_ips)
    
    def update_ip_config_inputs(self, ip_config_info):
        """
        更新IP配置输入框的显示内容
        
        Args:
            ip_config_info (IPConfigInfo): IP配置信息对象（frozen dataclass）
        """
        self.ip_address_input.setText(ip_config_info.ip_address or '')
        self.subnet_mask_input.setText(ip_config_info.subnet_mask or '')
        self.gateway_input.setText(ip_config_info.gateway or '')
        self.primary_dns_input.setText(ip_config_info.dns_primary or '')
        self.secondary_dns_input.setText(ip_config_info.dns_secondary or '')
    
    def update_current_adapter_label(self, adapter_name):
        """
        更新当前网卡显示标签
        
        Args:
            adapter_name (str): 网卡简称
        """
        self.current_adapter_label.setText(f"🌤️ 当前网卡：{adapter_name}")
    
    def update_extra_ip_list(self, ip_list):
        """
        更新额外IP列表（带复选框）
        
        Args:
            ip_list (list): 额外IP地址列表
        """
        self.extra_ip_list.clear()
        for ip_info in ip_list:
            if isinstance(ip_info, dict):
                display_text = f"{ip_info.get('ip', '')} / {ip_info.get('subnet_mask', '')}"
            else:
                display_text = str(ip_info)
            
            # 创建带复选框的列表项
            item = QListWidgetItem(display_text)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.extra_ip_list.addItem(item)
