"""
FlowDesk 工具函数包

作用说明：
这个包包含了FlowDesk应用程序所需的基础工具函数。
当前阶段只包含UI运行必需的核心模块。

包含的核心模块：
- resource_path: 资源路径管理，处理图标和样式文件路径
- logger: 基础日志管理，记录应用运行状态

设计原则：
- 最小依赖：只导入UI运行必需的模块
- 渐进开发：随着功能开发逐步添加其他工具模块
- 异常安全：所有工具函数都有完整的错误处理

面向新手的使用说明：
工具层提供应用程序的基础支撑功能，当前阶段专注于：
1. 正确加载应用图标和样式文件
2. 记录应用启动和运行日志
"""

# 资源路径管理 - UI必需
from .resource_path import resource_path, get_app_data_dir, get_logs_dir

# 日志管理 - 调试必需
from .logger import get_logger, setup_logging, log_exception

__all__ = [
    'get_logger', 'setup_logging', 'log_exception',
    'resource_path', 'get_app_data_dir', 'get_logs_dir'
]
