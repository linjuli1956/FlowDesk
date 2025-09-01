# -*- coding: utf-8 -*-
"""
业务服务层 (Services)

封装FlowDesk应用程序的所有业务逻辑和系统调用。
服务层通过PyQt信号与UI层通信，处理长时间运行的任务，提供错误处理和进度反馈。

主要服务类：
- NetworkService: 网络管理服务，处理网卡配置、IP设置
- NetworkToolsService: 网络工具服务，提供ping、tracert等功能
- RdpService: 远程桌面服务，管理RDP连接和历史记录
- HardwareMonitorService: 硬件监控服务，集成LibreHardwareMonitor
- SettingsService: 配置管理服务，处理用户偏好设置
- SystemTrayService: 系统托盘服务，管理托盘图标和菜单
- ValidationService: 输入验证服务，提供统一的验证规则

设计原则：
- 通过信号与UI层通信，避免直接依赖UI组件
- 封装所有系统API调用和外部依赖
- 提供统一的错误处理和进度反馈机制
- 支持异步操作和任务取消
"""
# 导入核心服务 - 当前阶段需要系统托盘服务、样式表服务和网络服务
from .system_tray_service import SystemTrayService
from .stylesheet_service import StylesheetService
from .status_bar_service import StatusBarService
# 从网络模块导入NetworkService门面
from .network import NetworkService

# 其他服务将在后续开发阶段逐步添加
# from .base_service import BaseService
# from .hardware_monitor_service import HardwareMonitorService
# from .rdp_service import RdpService
# from .settings_service import SettingsService

__all__ = [
    'SystemTrayService',
    'StylesheetService',
    'StatusBarService',
    'NetworkService'
]
