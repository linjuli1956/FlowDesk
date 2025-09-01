# -*- coding: utf-8 -*-
"""
状态栏UI组件

主窗口底部状态栏的UI实现，负责显示应用状态、用户操作和版本信息。
严格遵循UI层只负责界面展示的原则，通过槽函数接收Service层的状态更新信号。
"""

import logging
from typing import Optional
from PyQt5.QtWidgets import QStatusBar, QLabel, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont

from ...models.status_bar_info import StatusBarInfo


class StatusBarWidget(QStatusBar):
    """
    主窗口状态栏组件
    
    显示应用程序运行状态、用户操作状态和版本信息的UI组件。
    左侧显示带Emoji的状态信息(加粗字体)，右侧显示版本信息(淡蓝色)。
    
    UI层职责：
    - 纯界面显示，无业务逻辑
    - 通过槽函数接收状态更新
    - 响应式布局设计
    - 遵循UI四大铁律
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化状态栏组件
        
        Args:
            parent: 父窗口组件
        """
        super().__init__(parent)
        
        # 初始化日志记录器
        self.logger = logging.getLogger(self.__class__.__module__)
        
        # 设置objectName用于QSS样式控制
        self.setObjectName("main_status_bar")
        
        # 创建UI组件
        self._setup_ui()
        
        self.logger.debug("状态栏UI组件初始化完成")
    
    def _setup_ui(self):
        """
        设置UI组件布局
        
        创建左侧状态标签和右侧版本标签，设置合适的样式和布局。
        遵循UI四大铁律：禁止样式重复、严格自适应布局、最小宽度保护、智能组件缩放。
        """
        # 创建左侧状态显示标签
        self._status_label = QLabel("🟢 就绪 | ⏳ 初始化中...")
        self._status_label.setObjectName("status_label")
        
        # 设置状态标签字体为加粗
        status_font = self._status_label.font()
        status_font.setBold(True)
        self._status_label.setFont(status_font)
        
        # 创建右侧版本信息标签
        self._version_label = QLabel("v1.0.0 (2025-09-01)")
        self._version_label.setObjectName("version_label")
        
        # 设置版本标签对齐方式
        self._version_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # 添加标签到状态栏
        # 左侧状态信息占用主要空间
        self.addWidget(self._status_label, 1)
        
        # 右侧版本信息固定宽度
        self.addPermanentWidget(self._version_label)
        
        # 创建但不添加到布局的标签（用于兼容性）
        self.app_status_label = QLabel()
        self.user_action_label = QLabel()
        
        self.setFixedHeight(25)  # 最小宽度保护
        
        self.logger.debug("状态栏UI布局设置完成")
    
    @pyqtSlot(object)
    def update_status(self, status_info):
        """
        更新状态栏显示内容
        
        槽函数，响应StatusBarService的status_updated信号。
        纯UI更新操作，无任何业务逻辑。
        
        Args:
            status_info (StatusBarInfo): 状态栏信息对象
        """
        try:
            # 添加调试日志
            from ...utils.logger import get_logger
            logger = get_logger(__name__)
            logger.debug(f"🎯 StatusBarWidget收到status_updated信号: {status_info.user_action}")
            
            # 更新应用状态显示
            if hasattr(status_info, 'app_status'):
                self.app_status_label.setText(status_info.app_status)
                logger.debug(f"📱 应用状态已更新: {status_info.app_status}")
            
            # 更新用户操作状态显示
            if hasattr(status_info, 'user_action'):
                self.user_action_label.setText(status_info.user_action)
                logger.debug(f"👤 用户操作状态已更新: {status_info.user_action}")
            
            # 更新主状态标签显示（这是界面上主要显示的状态）
            if hasattr(status_info, 'app_status') and hasattr(status_info, 'user_action'):
                combined_status = f"{status_info.app_status} | {status_info.user_action}"
                self._status_label.setText(combined_status)
                logger.debug(f"🎯 主状态标签已更新: {combined_status}")
            
        except Exception as e:
            # 异常处理：确保状态栏更新失败不会影响主程序运行
            self.app_status_label.setText("⚠️ 状态更新异常")
            self.user_action_label.setText("请重试操作")
            # 设置默认显示内容
            self._status_label.setText("🟢 就绪 | ⏸️ 等待操作")
    
    def set_default_status(self):
        """
        设置默认状态显示
        
        用于初始化或错误恢复时的默认状态显示。
        """
        try:
            self._status_label.setText("🟢 就绪 | ⏸️ 等待操作")
            self._version_label.setText("v1.0.0 (2025-09-01)")
            
        except Exception as e:
            self.logger.error(f"设置默认状态失败: {str(e)}")
    
    def get_status_text(self) -> str:
        """
        获取当前状态文本
        
        Returns:
            str: 当前显示的状态文本
        """
        try:
            return self._status_label.text()
        except Exception as e:
            self.logger.error(f"获取状态文本失败: {str(e)}")
            return "未知状态"
    
    
    def update_version(self, version_info):
        """
        更新版本信息的槽方法
        
        这是连接到StatusBarService.version_updated信号的槽方法，
        接收版本信息并更新UI显示。
        
        Args:
            version_info: 包含版本和构建日期的字符串
        """
        try:
            self._version_label.setText(version_info)
            self.logger.debug(f"版本信息已更新: {version_info}")
            
        except Exception as e:
            self.logger.error(f"版本信息更新失败: {str(e)}")
            self._version_label.setText("v1.0.0 (未知日期)")
    
    def get_version_text(self) -> str:
        """
        获取当前版本文本
        
        Returns:
            str: 当前显示的版本文本
        """
        return self._version_label.text()
