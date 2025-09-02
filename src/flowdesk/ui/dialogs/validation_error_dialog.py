#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FlowDesk 输入验证错误提示对话框模块

作用说明：
本模块提供用户友好的输入验证错误提示对话框，当用户输入不符合格式要求的
网络参数时，显示清晰的错误说明和正确格式示例。采用非阻塞式设计，
不影响用户继续操作，同时提供详细的格式指导。

核心功能：
1. 显示具体的输入错误类型和原因
2. 提供正确格式的示例和说明
3. 支持不同类型的网络参数验证错误
4. 用户友好的图标和颜色提示

设计原则：
- 遵循UI四大铁律：禁止样式重复、自适应布局、最小宽度保护、智能组件缩放
- 非模态设计：不阻塞用户操作，允许用户查看提示后继续修改
- 信息丰富：提供错误原因、正确格式、示例等完整信息
- 视觉友好：使用图标和颜色区分不同类型的提示
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap
from flowdesk.utils.logger import get_logger


class ValidationErrorDialog(QDialog):
    """
    输入验证错误提示对话框类
    
    作用说明：
    专门用于显示网络参数输入验证错误的友好提示对话框。当用户输入
    不符合格式要求的IP地址、子网掩码、DNS等参数时，显示详细的
    错误说明和正确格式指导，帮助用户快速纠正输入错误。
    
    核心特性：
    - 非模态设计：不阻塞主界面操作
    - 自动关闭：可设置自动关闭时间
    - 类型化提示：针对不同参数类型提供专门的错误说明
    - 示例丰富：提供多种正确格式的示例
    
    信号接口：
    - dialog_closed: 对话框关闭时发射
    """
    
    # 信号定义
    dialog_closed = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        初始化验证错误提示对话框
        
        作用说明：
        构造函数负责创建对话框的完整UI界面，设置非模态行为，
        配置自适应布局和用户友好的视觉效果。
        
        参数说明：
            parent: 父窗口对象，用于对话框的正确定位
        """
        super().__init__(parent)
        self.setObjectName("validation_error_dialog")
        
        # 初始化日志记录器
        self.logger = get_logger(self.__class__.__name__)
        
        # 设置对话框基本属性
        self._setup_dialog_properties()
        
        # 创建UI组件
        self._create_ui_components()
        
        # 设置布局
        self._setup_layout()
        
        # 连接信号
        self._connect_signals()
        
        # 应用尺寸策略
        self._apply_size_policies()
        
        # 初始化自动关闭定时器
        self._setup_auto_close_timer()
    
    def _setup_dialog_properties(self):
        """
        设置对话框的基本属性
        
        作用说明：
        配置对话框为非模态窗口，设置合适的尺寸和窗口标志。
        非模态设计允许用户在查看错误提示的同时继续操作主界面。
        """
        self.setWindowTitle("⚠️ 输入格式提示")
        self.setModal(False)  # 非模态，不阻塞主界面
        
        # 设置足够的尺寸以完整显示内容，无需滚动条
        self.setMinimumSize(520, 480)
        self.setMaximumSize(650, 600)
        self.setFixedSize(580, 520)  # 足够高度确保两个QTextEdit区域完整显示
        
        # 设置窗口标志
        self.setWindowFlags(
            Qt.Dialog | 
            Qt.WindowTitleHint | 
            Qt.WindowCloseButtonHint |
            Qt.WindowStaysOnTopHint  # 保持在顶层，确保用户能看到
        )
    
    def _create_ui_components(self):
        """
        创建对话框的所有UI组件
        
        作用说明：
        创建标题、图标、错误信息显示区域、示例区域和按钮等
        所有界面元素，每个组件都设置了合适的objectName用于样式控制。
        """
        # 错误标题（居中显示，无图标）
        self.error_title = QLabel()
        self.error_title.setObjectName("error_title")
        self.error_title.setAlignment(Qt.AlignCenter)
        self.error_title.setMaximumHeight(30)  # 减少标题高度
        
        # 错误描述文本区域
        self.error_description = QTextEdit()
        self.error_description.setObjectName("error_description")
        self.error_description.setReadOnly(True)
        self.error_description.setMaximumHeight(120)
        self.error_description.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 正确格式示例区域
        self.format_examples = QTextEdit()
        self.format_examples.setObjectName("format_examples")
        self.format_examples.setReadOnly(True)
        self.format_examples.setMaximumHeight(220)
        self.format_examples.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 分隔线
        self.separator = QFrame()
        self.separator.setObjectName("dialog_separator")
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        
        # 按钮
        self.got_it_button = QPushButton("✅ 我知道了")
        self.got_it_button.setObjectName("close_error_dialog_btn")
        
        self.close_timer_label = QLabel()
        self.close_timer_label.setObjectName("close_timer_label")
        self.close_timer_label.setAlignment(Qt.AlignCenter)
    
    def _setup_layout(self):
        """
        设置对话框的布局管理器
        
        作用说明：
        采用垂直布局作为主布局，合理安排各个组件的位置和间距。
        遵循自适应布局原则，确保在不同尺寸下都能保持良好效果。
        """
        # 主垂直布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(12)
        
        # 添加各个组件到主布局
        main_layout.addWidget(self.error_title)
        main_layout.addWidget(self.error_description)
        main_layout.addWidget(self.separator)
        main_layout.addWidget(self.format_examples)
        
        # 底部按钮区域
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.close_timer_label, 1)
        button_layout.addWidget(self.got_it_button)
        
        main_layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """
        连接信号槽
        
        作用说明：
        建立按钮点击和对话框关闭事件的信号连接。
        """
        self.got_it_button.clicked.connect(self._handle_got_it_clicked)
    
    def _apply_size_policies(self):
        """
        应用智能组件缩放策略
        
        作用说明：
        根据UI四大铁律设置各组件的尺寸策略，确保布局的自适应性。
        """
        from PyQt5.QtWidgets import QSizePolicy
        
        # 文本区域可垂直扩展
        text_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.error_description.setSizePolicy(text_policy)
        self.format_examples.setSizePolicy(text_policy)
        
        # 按钮固定尺寸
        button_policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.got_it_button.setSizePolicy(button_policy)
    
    def _setup_auto_close_timer(self):
        """
        设置自动关闭定时器
        
        作用说明：
        创建定时器用于自动关闭对话框和更新倒计时显示。
        提供用户友好的自动关闭功能，避免对话框长时间占用屏幕空间。
        """
        self.auto_close_timer = QTimer()
        self.auto_close_timer.timeout.connect(self._update_close_countdown)
        
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self._auto_close_dialog)
        
        self.remaining_seconds = 0
    
    def show_subnet_mask_error(self, invalid_input: str, auto_close_seconds: int = 10):
        """
        显示子网掩码输入错误提示
        
        作用说明：
        专门用于显示子网掩码格式错误的详细提示，包括错误原因分析
        和正确格式示例。支持自动关闭功能。
        
        参数说明：
            invalid_input (str): 用户输入的无效子网掩码
            auto_close_seconds (int): 自动关闭倒计时秒数，0表示不自动关闭
        """
        # 设置错误标题（居中显示）
        self.error_title.setText("⚠️ 子网掩码格式错误")
        
        # 分析错误原因并生成描述
        error_reason = self._analyze_subnet_mask_error(invalid_input)
        
        error_html = f"""
        <div style='color: #e74c3c; font-size: 14px; line-height: 1.4;'>
            <b>输入内容：</b><span style='color: #c0392b; font-family: monospace;'>{invalid_input}</span><br><br>
            <b>错误原因：</b>{error_reason}
        </div>
        """
        
        self.error_description.setHtml(error_html)
        
        # 设置正确格式示例
        examples_html = """
        <div style='color: #27ae60; font-size: 13px; line-height: 1.5;'>
            <b>✅ 正确格式示例：</b><br>
            • <span style='font-family: monospace; background: #ecf0f1; padding: 2px 4px;'>255.255.255.0</span> （点分十进制格式）<br>
            • <span style='font-family: monospace; background: #ecf0f1; padding: 2px 4px;'>/24</span> （CIDR格式，带斜杠）<br>
            • <span style='font-family: monospace; background: #ecf0f1; padding: 2px 4px;'>24</span> （纯数字CIDR格式）<br>
            • <span style='font-family: monospace; background: #ecf0f1; padding: 2px 4px;'>255.255.0.0</span> 或 <span style='font-family: monospace; background: #ecf0f1; padding: 2px 4px;'>/16</span><br>
            • <span style='font-family: monospace; background: #ecf0f1; padding: 2px 4px;'>255.0.0.0</span> 或 <span style='font-family: monospace; background: #ecf0f1; padding: 2px 4px;'>/8</span>
        </div>
        """
        
        self.format_examples.setHtml(examples_html)
        
        # 移除自动关闭功能，用户手动关闭
        self.close_timer_label.setText("")
        
        # 显示对话框
        self.show()
        self.raise_()  # 确保对话框在最前面
        self.activateWindow()
        
        self.logger.info(f"显示子网掩码错误提示: {invalid_input}")
    
    def show_ip_address_error(self, invalid_input: str, auto_close_seconds: int = 10):
        """
        显示IP地址输入错误提示
        
        作用说明：
        专门用于显示IP地址格式错误的详细提示。
        
        参数说明：
            invalid_input (str): 用户输入的无效IP地址
            auto_close_seconds (int): 自动关闭倒计时秒数
        """
        self.error_title.setText("🌐 IP地址格式错误")
        
        error_reason = self._analyze_ip_address_error(invalid_input)
        
        error_html = f"""
        <div style='color: #e74c3c; font-size: 14px; line-height: 1.4;'>
            <b>输入内容：</b><span style='color: #c0392b; font-family: monospace;'>{invalid_input}</span><br><br>
            <b>错误原因：</b>{error_reason}
        </div>
        """
        
        self.error_description.setHtml(error_html)
        
        examples_html = """
        <div style='color: #27ae60; font-size: 13px; line-height: 1.5;'>
            <b>✅ 正确格式示例：</b><br>
            • <span style='font-family: monospace; background: #ecf0f1; padding: 2px 4px;'>192.168.1.100</span> （私有网络地址）<br>
            • <span style='font-family: monospace; background: #ecf0f1; padding: 2px 4px;'>10.0.0.1</span> （A类私有地址）<br>
            • <span style='font-family: monospace; background: #ecf0f1; padding: 2px 4px;'>172.16.0.1</span> （B类私有地址）<br>
            • <span style='font-family: monospace; background: #ecf0f1; padding: 2px 4px;'>8.8.8.8</span> （公共DNS服务器）
        </div>
        """
        
        self.format_examples.setHtml(examples_html)
        
        # 移除自动关闭功能，用户手动关闭
        self.close_timer_label.setText("")
        
        self.show()
        self.raise_()
        self.activateWindow()
        
        self.logger.info(f"显示IP地址错误提示: {invalid_input}")
    
    def _analyze_subnet_mask_error(self, invalid_input: str) -> str:
        """
        分析子网掩码输入错误的具体原因
        
        作用说明：
        根据用户的错误输入，分析可能的错误类型并返回友好的错误说明。
        
        参数说明：
            invalid_input (str): 用户输入的无效子网掩码
            
        返回值：
            str: 错误原因的详细说明
        """
        if not invalid_input:
            return "输入为空，请输入子网掩码"
        
        if invalid_input.endswith('.'):
            return "格式不完整，点分十进制格式需要4个数字段（如：255.255.255.0）"
        
        if invalid_input.startswith('/'):
            cidr_part = invalid_input[1:]
            if not cidr_part:
                return "CIDR格式不完整，请输入0-32之间的数字（如：/24）"
            elif not cidr_part.isdigit():
                return "CIDR格式只能包含数字（如：/24）"
            elif int(cidr_part) > 32:
                return "CIDR值超出范围，有效范围是0-32"
        
        if '.' in invalid_input:
            octets = invalid_input.split('.')
            if len(octets) > 4:
                return "点分十进制格式最多只能有4个数字段"
            elif len(octets) < 4:
                return "点分十进制格式需要4个完整的数字段"
            else:
                for i, octet in enumerate(octets):
                    if not octet:
                        return f"第{i+1}段为空，每段都需要输入0-255之间的数字"
                    elif not octet.isdigit():
                        return f"第{i+1}段包含非数字字符，只能输入0-255之间的数字"
                    elif int(octet) > 255:
                        return f"第{i+1}段数值{octet}超出范围，每段只能是0-255之间的数字"
                
                return "不是有效的子网掩码（必须是连续的1后跟连续的0）"
        
        # 检查是否是纯数字（无斜杠的CIDR）
        if invalid_input.isdigit():
            if int(invalid_input) > 32:
                return "CIDR值超出范围，有效范围是0-32"
            else:
                return "格式正确，但可能在其他地方有问题"
        
        return "包含无效字符，请使用点分十进制格式（如：255.255.255.0）或CIDR格式（如：/24）"
    
    def _analyze_ip_address_error(self, invalid_input: str) -> str:
        """
        分析IP地址输入错误的具体原因
        
        参数说明：
            invalid_input (str): 用户输入的无效IP地址
            
        返回值：
            str: 错误原因的详细说明
        """
        if not invalid_input:
            return "输入为空，请输入IP地址"
        
        if invalid_input.endswith('.'):
            return "格式不完整，IP地址需要4个数字段（如：192.168.1.100）"
        
        if '.' in invalid_input:
            octets = invalid_input.split('.')
            if len(octets) > 4:
                return "IP地址最多只能有4个数字段"
            elif len(octets) < 4:
                return "IP地址需要4个完整的数字段"
            else:
                for i, octet in enumerate(octets):
                    if not octet:
                        return f"第{i+1}段为空，每段都需要输入0-255之间的数字"
                    elif not octet.isdigit():
                        return f"第{i+1}段包含非数字字符"
                    elif int(octet) > 255:
                        return f"第{i+1}段数值{octet}超出范围，每段只能是0-255之间的数字"
        
        return "包含无效字符或格式错误，请使用标准IP地址格式（如：192.168.1.100）"
    
    def _start_auto_close(self, seconds: int):
        """
        启动自动关闭倒计时
        
        参数说明：
            seconds (int): 倒计时秒数
        """
        self.remaining_seconds = seconds
        self.close_timer_label.setText(f"⏰ {seconds}秒后自动关闭")
        
        # 启动1秒间隔的更新定时器
        self.auto_close_timer.start(1000)
        
        # 启动总倒计时定时器
        self.countdown_timer.start(seconds * 1000)
    
    def _update_close_countdown(self):
        """更新关闭倒计时显示"""
        self.remaining_seconds -= 1
        if self.remaining_seconds > 0:
            self.close_timer_label.setText(f"⏰ {self.remaining_seconds}秒后自动关闭")
        else:
            self.auto_close_timer.stop()
            self.close_timer_label.setText("正在关闭...")
    
    def _auto_close_dialog(self):
        """自动关闭对话框"""
        self.countdown_timer.stop()
        self.auto_close_timer.stop()
        self.close()
    
    def _handle_got_it_clicked(self):
        """处理"我知道了"按钮点击"""
        # 停止自动关闭定时器
        self.countdown_timer.stop()
        self.auto_close_timer.stop()
        
        # 关闭对话框
        self.close()
    
    def closeEvent(self, event):
        """重写关闭事件"""
        # 停止所有定时器
        self.countdown_timer.stop()
        self.auto_close_timer.stop()
        
        # 发射关闭信号
        self.dialog_closed.emit()
        
        # 接受关闭事件
        event.accept()
        
        self.logger.debug("验证错误提示对话框已关闭")
