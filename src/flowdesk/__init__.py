"""
FlowDesk - Windows系统管理工具

这是FlowDesk应用程序的主包，提供网络配置、网络工具、远程桌面和硬件监控功能。
采用分层架构设计：UI层、服务层、模型层、工具层，确保代码的可维护性和可扩展性。

主要功能模块：
- 网络配置：网卡管理、IP配置、DNS设置
- 网络工具：连通性测试、系统工具集成
- 远程桌面：RDP连接管理、历史记录
- 硬件监控：实时硬件信息、悬浮窗显示

技术栈：Python 3.8+, PyQt5, Windows 10/11
"""

__version__ = "1.0.0"
__author__ = "FlowDesk Team"
__description__ = "Windows系统管理工具"
