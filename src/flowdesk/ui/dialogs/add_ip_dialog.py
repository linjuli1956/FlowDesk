#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FlowDesk 添加IP地址对话框模块

作用说明：
本模块提供网络配置Tab中"添加额外IP"功能的专用对话框界面。
该对话框允许用户输入新的IP地址和子网掩码，用于为当前选择的网卡
添加额外的IP配置。采用模态对话框设计，确保用户专注于IP配置输入。

核心功能：
1. 提供IP地址和子网掩码的专用输入界面
2. 集成实时输入验证，防止无效网络参数输入
3. 支持用户友好的默认值预填充（子网掩码默认255.255.255.0）
4. 提供明确的确定/取消操作反馈

设计原则：
- 遵循面向对象封装原则，将对话框逻辑完全独立
- 严格遵循UI四大铁律：禁止样式重复、自适应布局、最小宽度保护、智能组件缩放
- 集成QValidator实时验证系统，提供无干扰的输入体验
- 通过信号槽机制与父组件通信，保持低耦合设计
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QLabel, QPushButton, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from flowdesk.utils.logger import get_logger

from ..widgets.validators import IPAddressValidator, SubnetMaskValidator


class AddIPDialog(QDialog):
    """
    添加IP地址专用对话框类
    
    作用说明：
    这是一个专门用于添加额外IP地址的模态对话框。它提供了标准化的
    网络参数输入界面，包含IP地址和子网掩码两个必要字段。对话框
    采用表单布局设计，确保标签和输入框的整齐对齐。
    
    核心特性：
    - 模态对话框设计，阻止用户操作其他界面直到完成输入
    - 集成实时输入验证，确保用户只能输入有效的网络参数
    - 智能默认值预填充，提升用户体验和输入效率
    - 标准化的确定/取消按钮布局，符合Windows设计规范
    
    信号接口：
    - ip_added: 当用户点击确定且输入有效时发射，携带IP和子网掩码数据
    
    面向对象设计：
    - 封装性：所有UI逻辑和数据验证逻辑封装在类内部
    - 单一职责：专门负责IP地址添加的用户交互
    - 开闭原则：可扩展支持更多网络参数而无需修改现有代码
    """
    
    # 信号定义：IP添加完成信号，携带IP地址和子网掩码
    ip_added = pyqtSignal(str, str)  # (ip_address, subnet_mask)
    
    def __init__(self, parent=None):
        """
        初始化添加IP对话框
        
        作用说明：
        构造函数负责创建对话框的完整UI界面，包括标题设置、控件创建、
        布局管理、验证器集成等所有初始化工作。采用分步骤初始化模式，
        确保每个组件都能正确设置和配置。
        
        参数说明：
            parent: 父窗口对象，用于模态对话框的正确显示和居中定位
        """
        super().__init__(parent)
        self.setObjectName("add_ip_dialog")
        
        # 初始化日志记录器
        self.logger = get_logger(self.__class__.__name__)
        
        
        # 设置对话框基本属性
        self._setup_dialog_properties()
        
        # 创建并配置所有UI组件
        self._create_ui_components()
        
        # 设置布局管理器，遵循自适应布局原则
        self._setup_layout()
        
        # 集成实时输入验证器
        self._setup_validators()
        
        # 连接信号槽，建立交互逻辑
        self._connect_signals()
        
        # 应用智能组件缩放策略
        self._apply_size_policies()
        
        # 设置默认值和焦点
        self._set_default_values()
        
    def apply_global_stylesheet(self):
        """
        样式表应用已由StylesheetService统一管理
        
        作用说明：
        对话框会自动继承应用程序级别的样式表，无需在对话框级别重复应用。
        StylesheetService在应用启动时已将完整的样式表应用到QApplication，
        所有子组件（包括对话框）都会自动继承这些样式。重复调用setStyleSheet
        会违反"禁止内联样式"规范，并可能导致样式冲突。
        
        技术原理：
        PyQt5的样式继承机制确保子组件自动获得父级样式，对话框作为QApplication
        的子组件，会自动应用通过app.setStyleSheet()设置的全局样式表。
        """
        self.logger.info("样式表由StylesheetService统一管理，对话框自动继承全局样式")

    def _setup_dialog_properties(self):
        """
        设置对话框的基本属性和窗口特性
        
        作用说明：
        配置对话框的标题、大小、模态行为等基础属性。设置合适的
        最小尺寸以确保所有控件都能正常显示，同时启用模态行为
        防止用户在输入过程中操作其他界面。
        """
        self.setWindowTitle("🆕 添加额外IP地址")
        self.setModal(True)  # 设置为模态对话框，阻止操作其他界面
        
        # 设置最小尺寸保护，确保所有控件可见（UI四大铁律）
        self.setMinimumSize(320, 180)
        self.setMaximumSize(400, 200)  # 限制最大尺寸，保持紧凑
        
        # 设置窗口标志，禁用最大化按钮，只保留关闭按钮
        self.setWindowFlags(
            Qt.Dialog | 
            Qt.WindowTitleHint | 
            Qt.WindowCloseButtonHint
        )

    def _create_ui_components(self):
        """
        创建对话框的所有UI组件
        
        作用说明：
        负责创建IP地址输入框、子网掩码输入框、标签以及按钮等
        所有用户界面元素。每个组件都设置了合适的objectName
        用于QSS样式控制，并配置了用户友好的占位符文本。
        """
        # IP地址输入相关组件
        self.ip_label = QLabel("IP地址：")
        self.ip_label.setObjectName("dialog_label")
        
        self.ip_input = QLineEdit()
        self.ip_input.setObjectName("dialog_ip_input")
        self.ip_input.setPlaceholderText("例如：192.168.1.100")
        self.ip_input.setToolTip("请输入有效的IPv4地址")
        
        # 子网掩码输入相关组件
        self.mask_label = QLabel("子网掩码：")
        self.mask_label.setObjectName("dialog_label")
        
        self.mask_input = QLineEdit()
        self.mask_input.setObjectName("dialog_mask_input")
        self.mask_input.setPlaceholderText("例如：255.255.255.0 或 /24")
        self.mask_input.setToolTip("支持点分十进制格式或CIDR格式")
        
        # 标准对话框按钮组
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.setObjectName("dialog_button_box")
        
        # 获取确定和取消按钮的引用，用于后续配置
        self.ok_button = self.button_box.button(QDialogButtonBox.Ok)
        self.cancel_button = self.button_box.button(QDialogButtonBox.Cancel)
        
        # 设置按钮文本为中文
        self.ok_button.setText("✅ 确定")
        self.cancel_button.setText("❌ 取消")
        
        # 设置按钮的objectName用于样式控制
        self.ok_button.setObjectName("dialog_ok_button")
        self.cancel_button.setObjectName("dialog_cancel_button")

    def _setup_layout(self):
        """
        设置对话框的布局管理器
        
        作用说明：
        采用垂直布局作为主布局，内部使用表单布局来实现标签和输入框
        的整齐对齐。这种布局方式遵循严格自适应布局原则，确保在不同
        尺寸下都能保持良好的视觉效果。
        
        布局结构：
        - 主布局（QVBoxLayout）
          - 表单布局（QFormLayout）：IP地址和子网掩码输入
          - 按钮布局（QDialogButtonBox）：确定和取消按钮
        """
        # 创建主垂直布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)  # 设置合适的边距
        main_layout.setSpacing(15)  # 组件间距
        
        # 创建表单布局用于输入字段
        form_layout = QFormLayout()
        form_layout.setHorizontalSpacing(10)  # 标签和输入框间距
        form_layout.setVerticalSpacing(12)    # 行间距
        
        # 添加表单行：标签在左，输入框在右，自动对齐
        form_layout.addRow(self.ip_label, self.ip_input)
        form_layout.addRow(self.mask_label, self.mask_input)
        
        # 将表单布局添加到主布局
        main_layout.addLayout(form_layout)
        
        # 添加按钮组到主布局底部
        main_layout.addWidget(self.button_box)

    def _setup_validators(self):
        """
        为输入框设置实时验证器
        
        作用说明：
        为IP地址和子网掩码输入框分别设置专门的QValidator验证器，
        实现实时输入验证功能。这确保用户只能输入有效的网络参数，
        从根本上杜绝无效数据的产生。
        
        验证器配置：
        - IP地址输入框：使用IPAddressValidator进行IPv4格式验证
        - 子网掩码输入框：使用SubnetMaskValidator支持多种格式验证
        """
        # 创建验证器实例
        ip_validator = IPAddressValidator()
        mask_validator = SubnetMaskValidator()
        
        # 为输入框设置验证器，启用实时验证
        self.ip_input.setValidator(ip_validator)
        self.mask_input.setValidator(mask_validator)

    def _connect_signals(self):
        """
        连接信号槽，建立组件间的交互逻辑
        
        作用说明：
        建立按钮点击事件与对应处理方法的连接关系。采用信号槽机制
        实现松耦合的事件处理，确保用户操作能够触发正确的业务逻辑。
        """
        # 连接标准对话框按钮的信号
        self.button_box.accepted.connect(self._handle_ok_clicked)
        self.button_box.rejected.connect(self.reject)  # 取消按钮直接关闭对话框

    def _apply_size_policies(self):
        """
        应用智能组件缩放策略
        
        作用说明：
        根据UI四大铁律中的"智能组件缩放"原则，为不同类型的控件
        设置合适的尺寸策略。确保输入框能够适应对话框宽度变化，
        而按钮保持固定尺寸不变形。
        """
        from PyQt5.QtWidgets import QSizePolicy
        
        # 输入框：水平方向可拉伸，垂直方向固定
        input_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.ip_input.setSizePolicy(input_policy)
        self.mask_input.setSizePolicy(input_policy)
        
        # 标签：保持内容尺寸
        label_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.ip_label.setSizePolicy(label_policy)
        self.mask_label.setSizePolicy(label_policy)

    def _set_default_values(self):
        """
        设置默认值和初始焦点
        
        作用说明：
        为子网掩码输入框预填充常用的默认值，提升用户体验。
        同时设置初始焦点到IP地址输入框，引导用户按逻辑顺序输入。
        """
        # 设置子网掩码默认值为最常用的C类网络掩码
        self.mask_input.setText("255.255.255.0")
        
        # 设置初始焦点到IP地址输入框
        self.ip_input.setFocus()


    def _handle_ok_clicked(self):
        """
        处理确定按钮点击事件
        
{{ ... }}
        当用户点击确定按钮时，验证输入数据的完整性和有效性。
        只有当IP地址和子网掩码都输入且格式正确时，才发射ip_added
        信号并关闭对话框。否则保持对话框打开状态，允许用户继续修改。
        
        验证逻辑：
        1. 检查IP地址和子网掩码是否都有输入
        2. 通过验证器检查格式是否正确
        3. 发射携带数据的信号给父组件
        4. 关闭对话框
        """
        # 获取用户输入的数据
        ip_address = self.ip_input.text().strip()
        subnet_mask = self.mask_input.text().strip()
        
        # 验证输入完整性
        if not ip_address or not subnet_mask:
            # 如果有空字段，设置焦点到第一个空字段
            if not ip_address:
                self.ip_input.setFocus()
            else:
                self.mask_input.setFocus()
            return  # 不关闭对话框，允许用户继续输入
        
        # 通过验证器检查格式正确性
        # 验证器已经在输入过程中进行了实时验证，这里主要确保最终状态
        ip_validator = IPAddressValidator()
        mask_validator = SubnetMaskValidator()
        
        ip_state, _, _ = ip_validator.validate(ip_address, 0)
        mask_state, _, _ = mask_validator.validate(subnet_mask, 0)
        
        # 只有当两个字段都处于Acceptable状态时才继续
        if (ip_state == ip_validator.Acceptable and 
            mask_state == mask_validator.Acceptable):
            
            # 发射信号，携带用户输入的IP配置数据
            self.ip_added.emit(ip_address, subnet_mask)
            
            # 接受对话框并关闭
            self.accept()
        else:
            # 如果验证失败，设置焦点到有问题的字段
            if ip_state != ip_validator.Acceptable:
                self.ip_input.setFocus()
            else:
                self.mask_input.setFocus()

    def get_ip_config(self):
        """
        获取用户输入的IP配置信息
        
        作用说明：
        提供公共接口供外部获取用户在对话框中输入的IP地址和子网掩码。
        这个方法通常在对话框被接受后调用，用于获取用户的输入结果。
        
        返回值：
            tuple: (ip_address, subnet_mask) 用户输入的IP配置元组
        """
        return (
            self.ip_input.text().strip(),
            self.mask_input.text().strip()
        )
