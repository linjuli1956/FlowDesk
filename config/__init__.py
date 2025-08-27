"""
配置管理模块

提供FlowDesk应用程序的配置管理功能。
支持开发环境和生产环境的配置分离，以及统一的设置管理。

配置文件：
- settings.py: 默认配置，包含应用程序的基础设置
- development.py: 开发环境配置，启用调试功能
- production.py: 生产环境配置，优化性能设置
- logging.conf: 日志配置文件，定义日志格式和输出

配置特点：
- 环境配置分离，支持不同部署场景
- 类型安全的配置访问
- 支持配置热重载和动态更新
- 统一的默认值管理
"""

from .settings import Settings, get_settings
from .development import DevelopmentConfig
from .production import ProductionConfig

__all__ = [
    'Settings',
    'get_settings',
    'DevelopmentConfig',
    'ProductionConfig'
]
