# -*- coding: utf-8 -*-
"""
操作结果弹窗模块

统一的操作结果提示弹窗，用于显示网卡操作的成功/失败结果。
严格遵循弹窗专项UI注意事项和UI四大铁律。

主要功能：
- 统一的成功/失败结果显示
- 自动居中显示
- 渐变色按钮样式
- 模态对话框设计

作者: FlowDesk开发团队
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class OperationResultDialog(QDialog):
    """
    操作结果弹窗类
    
    用于显示网卡操作（启用、禁用、DHCP设置等）的执行结果。
    采用模态对话框设计，确保用户看到操作结果后再继续其他操作。
    
    特点：
    - 统一的成功/失败样式
    - 自动根据结果类型调整图标和文案
    - 渐变色确定按钮
    - 严格遵循Claymorphism设计风格
    """
    
    # 定义信号
    dialog_closed = pyqtSignal()  # 对话框关闭信号
    
    def __init__(self, success: bool, message: str, operation: str, parent=None):
        """
        初始化操作结果弹窗
        
        Args:
            success: 操作是否成功
            message: 结果消息文本
            operation: 操作类型（如"启用网卡"、"禁用网卡"等）
            parent: 父窗口对象
        """
        super().__init__(parent)
        
        # 设置对话框属性
        self.setObjectName("operation_result_dialog")
        self.setModal(True)  # 模态对话框
        self.setFixedSize(400, 200)  # 固定尺寸
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        
        # 保存参数
        self.success = success
        self.message = message
        self.operation = operation
        
        # 设置窗口标题
        self._set_window_title()
        
        # 创建UI组件
        self._create_components()
        
        # 设置布局
        self._setup_layout()
        
        # 连接信号
        self._connect_signals()
        
        # 居中显示
        self._center_on_parent()
    
    def _set_window_title(self):
        """
        根据操作结果设置窗口标题
        """
        if self.success:
            title = f"✅ {self.operation}成功"
        else:
            title = f"❌ {self.operation}失败"
        
        self.setWindowTitle(title)
    
    def _create_components(self):
        """
        创建弹窗的所有UI组件
        
        根据操作结果创建相应的图标、消息文本和按钮。
        """
        # 结果图标标签
        self.icon_label = QLabel()
        self.icon_label.setObjectName("result_icon")
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        # 设置图标和样式
        if self.success:
            icon_text = "✅"
            self.icon_label.setProperty("result_type", "success")
        else:
            icon_text = "❌"
            self.icon_label.setProperty("result_type", "error")
        
        # 设置图标字体大小
        icon_font = QFont()
        icon_font.setPointSize(32)
        self.icon_label.setFont(icon_font)
        self.icon_label.setText(icon_text)
        
        # 消息文本标签
        self.message_label = QLabel(self.message)
        self.message_label.setObjectName("result_message")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)  # 支持文本换行
        
        # 设置消息字体
        message_font = QFont()
        message_font.setPointSize(12)
        message_font.setBold(True)
        self.message_label.setFont(message_font)
        
        # 确定按钮
        self.ok_button = QPushButton("我知道了")
        self.ok_button.setObjectName("dialog_ok_button")
        self.ok_button.setFixedSize(100, 35)
        self.ok_button.setDefault(True)  # 设为默认按钮
    
    def _setup_layout(self):
        """
        设置弹窗布局
        
        使用垂直布局排列图标、消息和按钮。
        """
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 图标区域
        main_layout.addWidget(self.icon_label)
        
        # 消息区域
        main_layout.addWidget(self.message_label)
        
        # 添加弹性空间
        main_layout.addStretch()
        
        # 按钮区域 - 居中布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """
        连接信号槽
        """
        self.ok_button.clicked.connect(self.accept)
    
    def _center_on_parent(self):
        """
        将对话框居中显示在父窗口上
        """
        if self.parent():
            parent_geometry = self.parent().geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(x, y)
    
    def closeEvent(self, event):
        """
        对话框关闭事件处理
        
        Args:
            event: 关闭事件对象
        """
        self.dialog_closed.emit()
        super().closeEvent(event)
    
    @staticmethod
    def show_success(message: str, operation: str, parent=None):
        """
        显示成功结果弹窗的静态方法
        
        Args:
            message: 成功消息
            operation: 操作类型
            parent: 父窗口
            
        Returns:
            OperationResultDialog: 弹窗实例
        """
        dialog = OperationResultDialog(True, message, operation, parent)
        dialog.exec_()
        return dialog
    
    @staticmethod
    def show_error(message: str, operation: str, parent=None):
        """
        显示失败结果弹窗的静态方法
        
        Args:
            message: 失败消息
            operation: 操作类型
            parent: 父窗口
            
        Returns:
            OperationResultDialog: 弹窗实例
        """
        dialog = OperationResultDialog(False, message, operation, parent)
        dialog.exec_()
        return dialog
