# -*- coding: utf-8 -*-
"""
自定义文本编辑控件模块

提供专用的文本编辑控件，支持特定的用户交互需求。

主要控件：
- NoContextMenuTextEdit: 禁用右键菜单的只读文本编辑框

严格遵循UI四大铁律和面向对象设计原则。

作者: FlowDesk开发团队
创建时间: 2024年
"""

from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import Qt


class NoContextMenuTextEdit(QTextEdit):
    """
    无右键菜单的文本编辑框
    
    继承QTextEdit并重写右键菜单事件，实现：
    - 禁用右键上下文菜单显示
    - 保留文本选择功能（鼠标拖拽选中）
    - 保留键盘复制功能（Ctrl+C快捷键）
    - 维持原有的只读和显示功能
    
    设计目的：
    为IP信息显示容器提供纯净的文本展示体验，避免用户误操作
    右键菜单中的粘贴、剪切等功能，同时保留核心的复制功能。
    """
    
    def contextMenuEvent(self, event):
        """
        重写右键菜单事件处理方法
        
        通过忽略右键菜单事件，禁用上下文菜单的显示。
        用户仍然可以通过鼠标选择文本和Ctrl+C快捷键复制文本，
        但无法通过右键菜单进行任何操作。
        
        Args:
            event (QContextMenuEvent): 右键菜单事件对象
        """
        # 直接忽略右键菜单事件，不显示任何菜单
        # 这样既禁用了右键菜单，又不影响其他功能
        event.ignore()
