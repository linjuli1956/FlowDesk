# -*- coding: utf-8 -*-
"""
IP配置确认弹窗：在应用IP配置前展示变更详情并询问用户确认
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QFrame
from PyQt5.QtCore import Qt, pyqtSignal, QPoint

from ...models.ip_config_confirmation import IPConfigConfirmation


class IPConfigConfirmDialog(QDialog):
    """
    IP配置确认弹窗组件
    
    展示即将应用的IP配置变更详情，让用户确认是否继续执行修改操作。
    严格遵循UI四大铁律：无内联样式、自适应布局、最小宽度保护、智能组件缩放。
    
    Signals:
        confirmed: 用户确认修改信号
        cancelled: 用户取消修改信号
    """
    
    # 定义信号
    confirmed = pyqtSignal()  # 用户确认修改
    cancelled = pyqtSignal()  # 用户取消修改
    
    def __init__(self, confirmation_data: IPConfigConfirmation, parent=None):
        """
        初始化IP配置确认弹窗
        
        Args:
            confirmation_data: IP配置确认数据对象
            parent: 父窗口组件
        """
        super().__init__(parent)
        self.confirmation_data = confirmation_data
        
        # 拖拽相关变量
        self.drag_position = QPoint()
        
        # 设置弹窗基本属性
        self.setup_dialog_properties()
        
        # 创建用户界面
        self.setup_ui()
        
        # 连接信号槽
        self.setup_signals()
    
    def setup_dialog_properties(self):
        """设置弹窗基本属性"""
        self.setObjectName("ip_config_confirm_dialog")
        self.setModal(True)  # 模态弹窗
        
        # 设置窗口标志：无标题栏但支持拖拽的弹窗
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        # 设置最小尺寸而不是固定尺寸，避免多显示器DPI问题
        self.setMinimumSize(520, 380)
        self.setMaximumSize(600, 450)  # 允许一定的尺寸弹性
        self.resize(520, 380)  # 设置初始尺寸
        
        # 居中显示
        if self.parent():
            parent_geometry = self.parent().geometry()
            x = parent_geometry.x() + (parent_geometry.width() - 520) // 2
            y = parent_geometry.y() + (parent_geometry.height() - 380) // 2
            self.move(x, y)
    
    def setup_ui(self):
        """创建用户界面组件"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 移除标题区域，直接显示网卡信息
        
        # 网卡信息区域
        self.create_adapter_info_section(main_layout)
        
        # 配置变更详情区域
        self.create_changes_section(main_layout)
        
        # 按钮区域
        self.create_button_section(main_layout)
    
    
    def create_adapter_info_section(self, parent_layout):
        """创建网卡信息区域"""
        adapter_frame = QFrame()
        adapter_frame.setObjectName("adapter_info_frame")
        adapter_frame.setFrameStyle(QFrame.StyledPanel)
        
        adapter_layout = QVBoxLayout(adapter_frame)
        adapter_layout.setContentsMargins(12, 8, 12, 8)
        
        # 网卡名称标签
        adapter_label = QLabel(f"🌐 目标网卡：{self.confirmation_data.adapter_name}")
        adapter_label.setObjectName("adapter_name_label")
        adapter_layout.addWidget(adapter_label)
        
        # DHCP状态标签
        dhcp_status = "启用" if self.confirmation_data.dhcp_enabled else "禁用"
        dhcp_label = QLabel(f"🔧 DHCP状态：{dhcp_status}")
        dhcp_label.setObjectName("dhcp_status_label")
        adapter_layout.addWidget(dhcp_label)
        
        parent_layout.addWidget(adapter_frame)
    
    def create_changes_section(self, parent_layout):
        """创建配置变更详情区域"""
        changes_label = QLabel("📋 配置变更详情：")
        changes_label.setObjectName("changes_title_label")
        parent_layout.addWidget(changes_label)
        
        # 变更详情文本框
        self.changes_text = QTextEdit()
        self.changes_text.setObjectName("changes_detail_text")
        self.changes_text.setReadOnly(True)
        self.changes_text.setMinimumHeight(150)
        self.changes_text.setMaximumHeight(180)
        
        # 填充变更详情内容，支持HTML格式显示
        if self.confirmation_data.has_changes():
            changes_content = self.confirmation_data.get_changes_summary()
        else:
            changes_content = '<span style="color: #fd7e14; font-size: 13px; font-weight: bold;">⚠️ 检测到无实际配置变更，请检查输入内容</span>'
        
        self.changes_text.setHtml(changes_content)
        parent_layout.addWidget(self.changes_text)
        
        # 警告提示
        warning_label = QLabel("⚠️ 修改网络配置可能会暂时中断网络连接，请确认后继续")
        warning_label.setObjectName("warning_label")
        warning_label.setWordWrap(True)
        parent_layout.addWidget(warning_label)
    
    def create_button_section(self, parent_layout):
        """创建按钮区域"""
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # 左侧弹性空间
        
        # 取消按钮
        self.cancel_btn = QPushButton("❌ 取消")
        self.cancel_btn.setObjectName("dialog_cancel_button")
        self.cancel_btn.setMinimumWidth(80)
        button_layout.addWidget(self.cancel_btn)
        
        # 间距
        button_layout.addSpacing(12)
        
        # 确认按钮
        self.confirm_btn = QPushButton("✅ 确认修改")
        self.confirm_btn.setObjectName("dialog_confirm_button")
        self.confirm_btn.setMinimumWidth(100)
        
        # 如果没有实际变更，禁用确认按钮
        if not self.confirmation_data.has_changes():
            self.confirm_btn.setEnabled(False)
            self.confirm_btn.setText("⚠️ 无变更")
        
        button_layout.addWidget(self.confirm_btn)
        
        parent_layout.addLayout(button_layout)
    
    def setup_signals(self):
        """连接信号槽"""
        self.confirm_btn.clicked.connect(self.on_confirm_clicked)
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)
    
    def on_confirm_clicked(self):
        """处理确认按钮点击"""
        self.confirmed.emit()
        self.accept()  # 关闭弹窗并返回接受状态
    
    def on_cancel_clicked(self):
        """处理取消按钮点击"""
        self.cancelled.emit()
        self.reject()  # 关闭弹窗并返回拒绝状态
    
    def closeEvent(self, event):
        """处理弹窗关闭事件"""
        # 无标题栏时通过ESC键或代码关闭等同于取消操作
        self.cancelled.emit()
        super().closeEvent(event)
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件 - 开始拖拽"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件 - 执行拖拽"""
        if event.buttons() == Qt.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPos() - self.drag_position)
            event.accept()
