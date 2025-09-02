# -*- coding: utf-8 -*-
"""
网络事件处理器模块：负责网络相关UI事件的分类处理

这个模块将原本的巨型网络事件处理器拆分为三个专业的事件处理器：
- NetworkAdapterEvents: 处理网卡选择、切换、刷新相关事件
- IPConfigurationEvents: 处理IP配置、验证、应用相关事件  
- NetworkStatusEvents: 处理网络状态显示、错误反馈、进度更新相关事件

采用面向对象设计原则，每个处理器专注于单一职责，提高代码的可维护性和扩展性。
"""

from .network_adapter_events import NetworkAdapterEvents
from .ip_configuration_events import IPConfigurationEvents
from .network_status_events import NetworkStatusEvents

__all__ = [
    'NetworkAdapterEvents',
    'IPConfigurationEvents',
    'NetworkStatusEvents'
]
