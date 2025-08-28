"""
样式管理模块

提供FlowDesk应用程序的样式表管理和颜色方案定义。
负责在应用启动时加载合适的QSS样式表，并提供颜色常量定义。

主要组件：
- ColorScheme: 颜色方案定义，提供统一的颜色常量

功能特点：
- 统一的颜色语义管理
- 支持主题色彩配置
- 提供颜色常量定义

注意：样式表管理已迁移到服务层的StylesheetService
"""

from .color_scheme import ColorScheme

__all__ = [
    'ColorScheme'
]
