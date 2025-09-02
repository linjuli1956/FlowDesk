# -*- coding: utf-8 -*-
"""
主窗口模块统一导出：提供FlowDesk主窗口的完整功能组件

更新说明：
- NetworkEventHandler已重构为协调器模式
- 新增network_events子模块，包含专业事件处理器
- 保持向后兼容性，外部调用无需修改
"""

from .main_window_base import MainWindowBase
from .service_coordinator import ServiceCoordinator
from .network_event_handler import NetworkEventHandler
from .ui_state_manager import UIStateManager
from .main_window import MainWindow

# 导出专业事件处理器（可选，供高级用户直接使用）
from .network_events import (
    NetworkAdapterEvents,
    IPConfigurationEvents, 
    NetworkStatusEvents
)

__all__ = [
    'MainWindow',
    'MainWindowBase',
    'ServiceCoordinator', 
    'NetworkEventHandler',
    'UIStateManager',
    # 专业事件处理器
    'NetworkAdapterEvents',
    'IPConfigurationEvents',
    'NetworkStatusEvents'
]
