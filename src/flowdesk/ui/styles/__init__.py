"""
样式管理模块

提供FlowDesk应用程序的样式表管理和颜色方案定义。
负责在应用启动时加载合适的QSS样式表，并提供颜色常量定义。

主要组件：
- StylesheetManager: 样式表管理器，负责加载和应用QSS文件
- ColorScheme: 颜色方案定义，提供统一的颜色常量

功能特点：
- 自动检测Windows版本，选择合适的样式表
- 支持开发环境和打包环境的资源路径解析
- 提供颜色预处理和变量替换功能
- 统一的颜色语义管理
"""

from .stylesheet_manager import StylesheetManager
from .color_scheme import ColorScheme

__all__ = [
    'StylesheetManager',
    'ColorScheme'
]
