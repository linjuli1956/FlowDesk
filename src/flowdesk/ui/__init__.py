"""
用户界面层 (UI)

FlowDesk应用程序的纯视图层，负责界面展示和用户交互。
UI层严格遵循零业务逻辑原则，只负责响应用户操作和订阅服务层信号更新界面。

主要组件：
- MainWindow: 主窗口类，660×645像素布局，包含四个Tab页面
- Tabs: 四个主要功能页面（网络配置、网络工具、远程桌面、硬件信息）
- Dialogs: 各种对话框（RDP连接、添加IP、用户管理等）
- Widgets: 自定义控件（状态徽章、悬浮窗、硬件卡片等）
- QSS: 外置样式表，实现卡片式彩色按钮设计

UI四大铁律：
🚫 禁止样式重复 - 统一使用外置QSS样式表
🔄 严格自适应布局 - 使用QLayout布局管理器
📏 最小宽度保护 - 设置minimumSize保护

设计原则：
- 使用布局管理器实现响应式设计
- 应用外置QSS样式，禁止内联样式
- 通过信号槽机制与服务层通信
- 支持Windows 10/11主题，兼容Windows 7
"""

# 导入主窗口 - 当前阶段只需要主窗口
from .main_window import MainWindow

# 导入样式管理器 - UI必需
from .styles import StylesheetManager, ColorScheme

# 其他组件将在后续开发阶段逐步添加
# from .tabs import *
# from .dialogs import *  
# from .widgets import *

__all__ = [
    'MainWindow',
    'StylesheetManager', 'ColorScheme'
]
