# -*- coding: utf-8 -*-
"""
网络操作进度对话框｜提供统一的网络操作进度反馈界面
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QProgressBar, QFrame, QApplication)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QMovie, QPixmap
import logging
from typing import Optional, Callable, Any
import time

class NetworkProgressDialog(QDialog):
    """网络操作进度对话框
    
    职责: 为网络操作提供统一的进度反馈界面
    特点: 模态对话框，支持取消操作，Claymorphism设计风格
    """
    
    # 信号定义
    operation_cancelled = pyqtSignal()  # 操作取消信号
    dialog_closed = pyqtSignal()        # 对话框关闭信号
    
    def __init__(self, operation_name: str, adapter_name: str = "", parent=None):
        """初始化网络进度对话框
        
        Args:
            operation_name: 操作名称（如"修改MAC地址"、"启用网卡"等）
            adapter_name: 网卡名称（可选）
            parent: 父窗口
        """
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 基本属性
        self.operation_name = operation_name
        self.adapter_name = adapter_name
        self.is_cancelled = False
        self.start_time = time.time()
        
        # 初始化UI
        self._setup_ui()
        self._setup_timer()
        self._center_on_parent()
        
        self.logger.info(f"创建网络进度对话框: {operation_name} - {adapter_name}")
    
    def _setup_ui(self):
        """初始化UI组件"""
        # 设置对话框属性
        self.setObjectName("network_progress_dialog")
        self.setModal(True)
        self.setFixedSize(400, 200)
        self.setWindowTitle("正在执行操作")
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 20, 24, 20)
        
        # 创建内容区域
        content_frame = self._create_content_section()
        main_layout.addWidget(content_frame)
        
        # 创建进度区域
        progress_frame = self._create_progress_section()
        main_layout.addWidget(progress_frame)
        
        # 创建按钮区域
        button_frame = self._create_button_section()
        main_layout.addWidget(button_frame)
        
        # 连接信号
        self._connect_signals()
    
    def _create_content_section(self) -> QFrame:
        """创建内容区域"""
        frame = QFrame()
        frame.setObjectName("content_section_frame")
        layout = QVBoxLayout(frame)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 操作标题
        title_text = f"{self.operation_name}"
        if self.adapter_name:
            title_text += f" - {self.adapter_name}"
        
        self.title_label = QLabel(title_text)
        self.title_label.setObjectName("operation_title_label")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        # 状态描述
        self.status_label = QLabel("正在准备...")
        self.status_label.setObjectName("operation_status_label")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # 耗时显示
        self.time_label = QLabel("耗时: 0秒")
        self.time_label.setObjectName("operation_time_label")
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)
        
        return frame
    
    def _create_progress_section(self) -> QFrame:
        """创建进度区域"""
        frame = QFrame()
        frame.setObjectName("progress_section_frame")
        layout = QVBoxLayout(frame)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("network_progress_bar")
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        return frame
    
    def _create_button_section(self) -> QFrame:
        """创建按钮区域"""
        frame = QFrame()
        frame.setObjectName("button_section_frame")
        layout = QHBoxLayout(frame)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 8, 0, 0)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 取消按钮
        self.cancel_button = QPushButton("取消操作")
        self.cancel_button.setObjectName("dialog_cancel_button")
        self.cancel_button.setMinimumSize(100, 36)
        layout.addWidget(self.cancel_button)
        
        # 添加弹性空间
        layout.addStretch()
        
        return frame
    
    def _setup_timer(self):
        """设置计时器"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_elapsed_time)
        self.timer.start(1000)  # 每秒更新一次
    
    def _connect_signals(self):
        """连接信号槽"""
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
    
    def _center_on_parent(self):
        """居中到父窗口"""
        if self.parent():
            parent_rect = self.parent().geometry()
            dialog_rect = self.geometry()
            x = parent_rect.x() + (parent_rect.width() - dialog_rect.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - dialog_rect.height()) // 2
            self.move(x, y)
        else:
            # 居中到屏幕
            screen = QApplication.desktop().screenGeometry()
            dialog_rect = self.geometry()
            x = (screen.width() - dialog_rect.width()) // 2
            y = (screen.height() - dialog_rect.height()) // 2
            self.move(x, y)
    
    @pyqtSlot()
    def _on_cancel_clicked(self):
        """处理取消按钮点击"""
        self.is_cancelled = True
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("正在取消...")
        self.status_label.setText("正在取消操作，请稍候...")
        self.operation_cancelled.emit()
        self.logger.info(f"用户取消操作: {self.operation_name}")
    
    @pyqtSlot()
    def _update_elapsed_time(self):
        """更新耗时显示"""
        elapsed = int(time.time() - self.start_time)
        self.time_label.setText(f"耗时: {elapsed}秒")
    
    def update_progress(self, progress: int, status_text: str = ""):
        """更新进度
        
        Args:
            progress: 进度百分比 (0-100)
            status_text: 状态描述文本
        """
        if self.is_cancelled:
            return
            
        self.progress_bar.setValue(progress)
        if status_text:
            self.status_label.setText(status_text)
        
        self.logger.debug(f"进度更新: {progress}% - {status_text}")
    
    def set_indeterminate_progress(self, status_text: str = "正在处理..."):
        """设置不确定进度模式
        
        Args:
            status_text: 状态描述文本
        """
        if self.is_cancelled:
            return
            
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # 不确定进度模式
        if status_text:
            self.status_label.setText(status_text)
    
    def complete_operation(self, success: bool, message: str = ""):
        """完成操作
        
        Args:
            success: 操作是否成功
            message: 完成消息
        """
        self.timer.stop()
        
        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText(message or "操作完成")
            self.cancel_button.setText("关闭")
            self.cancel_button.setObjectName("dialog_ok_button")  # 切换为确定按钮样式
            
            # 成功时2秒后自动关闭
            self.auto_close_timer = QTimer(self)
            self.auto_close_timer.setSingleShot(True)  # 只触发一次
            self.auto_close_timer.timeout.connect(self.accept)
            self.auto_close_timer.start(2000)  # 2秒后自动关闭
            
            # 更新状态显示倒计时
            self.close_countdown = 2
            self.countdown_timer = QTimer(self)
            self.countdown_timer.timeout.connect(self._update_countdown)
            self.countdown_timer.start(1000)  # 每秒更新倒计时
            
        else:
            self.status_label.setText(message or "操作失败")
            self.cancel_button.setText("关闭")
            self.cancel_button.setObjectName("dialog_cancel_button")
        
        self.cancel_button.setEnabled(True)
        self.cancel_button.clicked.disconnect()  # 断开原有连接
        self.cancel_button.clicked.connect(self._on_manual_close)  # 连接到手动关闭处理
        
        elapsed = int(time.time() - self.start_time)
        result = "成功" if success else "失败"
        self.logger.info(f"操作{result}: {self.operation_name} - 耗时{elapsed}秒")
    
    def _update_countdown(self):
        """更新倒计时显示"""
        if hasattr(self, 'close_countdown') and self.close_countdown > 0:
            self.status_label.setText(f"操作完成，{self.close_countdown}秒后自动关闭...")
            self.close_countdown -= 1
        else:
            if hasattr(self, 'countdown_timer'):
                self.countdown_timer.stop()
    
    def _on_manual_close(self):
        """处理手动关闭"""
        # 停止自动关闭计时器
        if hasattr(self, 'auto_close_timer') and self.auto_close_timer.isActive():
            self.auto_close_timer.stop()
        if hasattr(self, 'countdown_timer') and self.countdown_timer.isActive():
            self.countdown_timer.stop()
        self.accept()
    
    def closeEvent(self, event):
        """对话框关闭事件处理"""
        if self.timer.isActive():
            self.timer.stop()
        
        # 清理自动关闭相关的计时器
        if hasattr(self, 'auto_close_timer') and self.auto_close_timer.isActive():
            self.auto_close_timer.stop()
        if hasattr(self, 'countdown_timer') and self.countdown_timer.isActive():
            self.countdown_timer.stop()
        
        self.dialog_closed.emit()
        self.logger.info(f"网络进度对话框关闭: {self.operation_name}")
        super().closeEvent(event)


class NetworkOperationWorker(QThread):
    """网络操作工作线程
    
    职责: 在后台执行网络操作，避免阻塞UI，支持实时进度更新
    """
    
    # 信号定义
    progress_updated = pyqtSignal(int, str)    # 进度更新信号
    operation_completed = pyqtSignal(bool, str)  # 操作完成信号
    
    def __init__(self, operation_func: Callable, *args, **kwargs):
        """初始化工作线程
        
        Args:
            operation_func: 要执行的操作函数
            *args, **kwargs: 传递给操作函数的参数
        """
        super().__init__()
        self.operation_func = operation_func
        self.args = args
        self.kwargs = kwargs
        self.is_cancelled = False
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def emit_progress(self, progress: int, status: str):
        """发射进度更新信号的回调函数
        
        Args:
            progress: 进度百分比 (0-100)
            status: 状态描述
        """
        if not self.is_cancelled:
            self.progress_updated.emit(progress, status)
    
    def run(self):
        """执行网络操作"""
        try:
            # 检查操作函数是否支持进度回调
            import inspect
            sig = inspect.signature(self.operation_func)
            
            if 'progress_callback' in sig.parameters:
                # 如果操作函数支持进度回调，传入回调函数
                result = self.operation_func(*self.args, progress_callback=self.emit_progress, **self.kwargs)
            else:
                # 如果不支持进度回调，使用原有方式执行
                result = self.operation_func(*self.args, **self.kwargs)
            
            if not self.is_cancelled:
                if result:
                    self.operation_completed.emit(True, "操作成功完成")
                else:
                    self.operation_completed.emit(False, "操作执行失败")
        except Exception as e:
            self.logger.error(f"网络操作异常: {str(e)}")
            if not self.is_cancelled:
                self.operation_completed.emit(False, f"操作异常: {str(e)}")
    
    def cancel_operation(self):
        """取消操作"""
        self.is_cancelled = True
        self.logger.info("网络操作被取消")


def show_network_progress(operation_name: str, operation_func: Callable, 
                         adapter_name: str = "", parent=None, *args, **kwargs) -> bool:
    """显示网络操作进度对话框的便捷函数
    
    Args:
        operation_name: 操作名称
        operation_func: 要执行的操作函数
        adapter_name: 网卡名称（可选）
        parent: 父窗口
        *args, **kwargs: 传递给操作函数的参数
        
    Returns:
        bool: 操作是否成功
    """
    # 创建进度对话框
    dialog = NetworkProgressDialog(operation_name, adapter_name, parent)
    
    # 创建工作线程
    worker = NetworkOperationWorker(operation_func, *args, **kwargs)
    
    # 连接信号
    worker.progress_updated.connect(dialog.update_progress)
    worker.operation_completed.connect(dialog.complete_operation)
    dialog.operation_cancelled.connect(worker.cancel_operation)
    
    # 启动工作线程
    worker.start()
    
    # 显示对话框
    result = dialog.exec_()
    
    # 等待线程结束
    worker.wait(5000)  # 最多等待5秒
    
    return result == QDialog.Accepted
