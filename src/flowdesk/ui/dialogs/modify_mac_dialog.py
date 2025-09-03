"""
MAC地址修改弹窗组件

功能说明：
- 提供用户友好的MAC地址修改界面
- 支持多种MAC地址输入格式的实时验证和预览
- 包含恢复初始MAC地址功能
- 遵循项目UI四大铁律和Claymorphism设计风格

架构原则：
- UI层：纯界面展示，无业务逻辑
- 信号驱动：通过PyQt信号与服务层通信
- 数据验证：实时验证用户输入的MAC地址格式
- 用户体验：提供清晰的视觉反馈和操作指引
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QFrame, QSpacerItem, 
                            QSizePolicy)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont

from ...utils.mac_address_utils import MacAddressUtils, MacValidationResult


class ModifyMacDialog(QDialog):
    """MAC地址修改弹窗类"""
    
    # 信号定义：与服务层通信的接口
    mac_modify_requested = pyqtSignal(str, str)  # (adapter_name, new_mac)
    mac_restore_requested = pyqtSignal(str)      # (adapter_name)
    
    def __init__(self, adapter_name: str, current_mac: str, original_mac: str = None, parent=None):
        """
        初始化MAC地址修改弹窗
        
        Args:
            adapter_name: 网卡名称
            current_mac: 当前MAC地址
            original_mac: 初始MAC地址（出厂MAC）
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 存储网卡信息
        self.adapter_name = adapter_name
        self.current_mac = current_mac
        self.original_mac = original_mac or current_mac
        
        # 初始化UI组件
        self._init_ui()
        self._setup_connections()
        self._update_preview()
        
        # 设置弹窗属性
        self.setModal(True)
        self.setFixedSize(480, 320)
        self.setWindowTitle("修改MAC地址")
        self.setObjectName("modify_mac_dialog")
    
    def _init_ui(self):
        """初始化用户界面组件"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 20, 24, 20)
        
        # 标题标签
        title_label = QLabel("修改MAC地址")
        title_label.setObjectName("dialog_title")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 网卡信息区域
        info_frame = self._create_info_section()
        main_layout.addWidget(info_frame)
        
        # MAC地址输入区域
        input_frame = self._create_input_section()
        main_layout.addWidget(input_frame)
        
        # 预览区域
        preview_frame = self._create_preview_section()
        main_layout.addWidget(preview_frame)
        
        # 按钮区域
        button_frame = self._create_button_section()
        main_layout.addWidget(button_frame)
        
        # 添加弹性空间
        main_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
    
    def _create_info_section(self) -> QFrame:
        """创建网卡信息显示区域"""
        frame = QFrame()
        frame.setObjectName("info_section_frame")
        layout = QVBoxLayout(frame)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # 当前网卡标签
        adapter_label = QLabel(f"当前网卡: {self.adapter_name}")
        adapter_label.setObjectName("adapter_info_label")
        layout.addWidget(adapter_label)
        
        # 当前MAC地址标签
        current_mac_label = QLabel(f"当前MAC: {self.current_mac}")
        current_mac_label.setObjectName("current_mac_label")
        layout.addWidget(current_mac_label)
        
        # 初始MAC地址标签（如果与当前不同）
        if self.original_mac != self.current_mac:
            original_mac_label = QLabel(f"初始MAC: {self.original_mac} (出厂)")
            original_mac_label.setObjectName("original_mac_label")
            layout.addWidget(original_mac_label)
        
        return frame
    
    def _create_input_section(self) -> QFrame:
        """创建MAC地址输入区域"""
        frame = QFrame()
        frame.setObjectName("input_section_frame")
        layout = QVBoxLayout(frame)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # 输入标签
        input_label = QLabel("新MAC地址:")
        input_label.setObjectName("input_label")
        layout.addWidget(input_label)
        
        # MAC地址输入框
        self.mac_input = QLineEdit()
        self.mac_input.setObjectName("mac_address_input")
        self.mac_input.setPlaceholderText("支持格式: 00:1A:2B:3C:4D:5E 或 00-1A-2B-3C-4D-5E 等")
        self.mac_input.setMaxLength(17)  # 最长格式的字符数
        layout.addWidget(self.mac_input)
        
        # 格式提示标签
        hint_label = QLabel("支持多种格式：冒号分隔、连字符分隔、连续输入等")
        hint_label.setObjectName("format_hint_label")
        layout.addWidget(hint_label)
        
        return frame
    
    def _create_preview_section(self) -> QFrame:
        """创建预览区域"""
        frame = QFrame()
        frame.setObjectName("preview_section_frame")
        layout = QVBoxLayout(frame)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # 预览标签
        preview_title = QLabel("预览:")
        preview_title.setObjectName("preview_title_label")
        layout.addWidget(preview_title)
        
        # 预览内容标签
        self.preview_label = QLabel(f"{self.current_mac} → (请输入新MAC地址)")
        self.preview_label.setObjectName("preview_content_label")
        self.preview_label.setWordWrap(True)
        layout.addWidget(self.preview_label)
        
        return frame
    
    def _create_button_section(self) -> QFrame:
        """创建按钮区域"""
        frame = QFrame()
        frame.setObjectName("button_section_frame")
        layout = QHBoxLayout(frame)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 8, 0, 0)
        
        # 恢复初始按钮
        self.restore_button = QPushButton("恢复初始")
        self.restore_button.setObjectName("dialog_restore_button")
        self.restore_button.setMinimumSize(80, 36)
        # 恢复初始按钮始终可点击，用于恢复真正的原始MAC地址
        self.restore_button.setEnabled(True)
        layout.addWidget(self.restore_button)
        
        # 添加弹性空间
        layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setObjectName("dialog_cancel_button")
        self.cancel_button.setMinimumSize(80, 36)
        layout.addWidget(self.cancel_button)
        
        # 确定按钮
        self.confirm_button = QPushButton("确定并重启")
        self.confirm_button.setObjectName("dialog_ok_button")
        self.confirm_button.setMinimumSize(120, 36)
        self.confirm_button.setEnabled(False)  # 初始状态禁用
        layout.addWidget(self.confirm_button)
        
        return frame
    
    def _setup_connections(self):
        """设置信号连接"""
        # 输入框文本变化时实时验证和预览
        self.mac_input.textChanged.connect(self._on_input_changed)
        
        # 按钮点击事件
        self.restore_button.clicked.connect(self._on_restore_clicked)
        self.cancel_button.clicked.connect(self.reject)
        self.confirm_button.clicked.connect(self._on_confirm_clicked)
        
        # 回车键确认
        self.mac_input.returnPressed.connect(self._on_confirm_clicked)
    
    def _on_input_changed(self):
        """处理输入框内容变化"""
        self._update_preview()
        self._update_button_states()
    
    def _on_restore_clicked(self):
        """处理恢复初始按钮点击"""
        # 直接发射恢复初始MAC信号，不需要通过输入框
        self.mac_restore_requested.emit(self.adapter_name)
        # 关闭弹窗
        self.accept()
    
    def _on_confirm_clicked(self):
        """处理确定按钮点击"""
        if not self.confirm_button.isEnabled():
            return
        
        # 获取验证后的MAC地址
        input_text = self.mac_input.text().strip()
        validation_result = MacAddressUtils.normalize_mac_address(input_text)
        
        if validation_result.is_valid:
            new_mac = validation_result.normalized_mac
            
            # 检查是否为恢复初始MAC的操作
            if new_mac.upper() == self.original_mac.upper():
                # 发射恢复初始MAC信号
                self.mac_restore_requested.emit(self.adapter_name)
            else:
                # 发射修改MAC信号
                self.mac_modify_requested.emit(self.adapter_name, new_mac)
            
            # 关闭弹窗
            self.accept()
    
    def _update_preview(self):
        """更新预览显示"""
        input_text = self.mac_input.text().strip()
        
        if not input_text:
            # 输入为空时显示提示
            self.preview_label.setText(f"{self.current_mac} → (请输入新MAC地址)")
            self.preview_label.setObjectName("preview_content_label")
            return
        
        # 验证输入的MAC地址
        validation_result = MacAddressUtils.normalize_mac_address(input_text)
        
        if validation_result.is_valid:
            # 有效MAC地址，显示绿色预览
            new_mac = validation_result.normalized_mac
            if new_mac.upper() == self.original_mac.upper():
                # 恢复初始MAC的特殊提示
                self.preview_label.setText(f"{self.current_mac} → {new_mac} (恢复初始)")
                self.preview_label.setObjectName("preview_content_restore")
            else:
                # 普通修改预览
                self.preview_label.setText(f"{self.current_mac} → {new_mac}")
                self.preview_label.setObjectName("preview_content_valid")
        else:
            # 无效MAC地址，显示红色错误提示
            self.preview_label.setText(f"{self.current_mac} → 格式错误")
            self.preview_label.setObjectName("preview_content_error")
        
        # 强制刷新样式
        self.preview_label.style().unpolish(self.preview_label)
        self.preview_label.style().polish(self.preview_label)
    
    def _update_button_states(self):
        """更新按钮状态"""
        input_text = self.mac_input.text().strip()
        
        if not input_text:
            # 输入为空时禁用确定按钮
            self.confirm_button.setEnabled(False)
            return
        
        # 验证MAC地址格式
        validation_result = MacAddressUtils.normalize_mac_address(input_text)
        
        if validation_result.is_valid:
            new_mac = validation_result.normalized_mac
            
            # 检查是否与当前MAC相同且不是恢复初始MAC的操作
            if (new_mac.upper() == self.current_mac.upper() and 
                new_mac.upper() != self.original_mac.upper()):
                # 与当前MAC相同但不是恢复初始MAC，禁用确定按钮
                self.confirm_button.setEnabled(False)
            else:
                # 有效的MAC地址（包括恢复初始MAC的情况），启用确定按钮
                self.confirm_button.setEnabled(True)
        else:
            # 无效MAC地址，禁用确定按钮
            self.confirm_button.setEnabled(False)
    
    def get_validation_result(self) -> MacValidationResult:
        """获取当前输入的验证结果"""
        input_text = self.mac_input.text().strip()
        return MacAddressUtils.normalize_mac_address(input_text)
