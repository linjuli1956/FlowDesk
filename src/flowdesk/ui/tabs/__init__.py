"""
Tab页面组件

包含FlowDesk主窗口的四个核心功能页面。
每个Tab页面都是独立的QWidget，负责特定功能模块的用户界面。

Tab页面列表：
- NetworkConfigTab: 网络配置页面，网卡选择、IP配置、状态显示
- NetworkToolsTab: 网络工具页面，连通性测试、9宫格系统工具
- RdpTab: 远程桌面页面，RDP连接管理和历史记录
- HardwareTab: 硬件信息页面，实时硬件监控和悬浮窗控制

设计特点：
- 每个Tab都遵循UI四大铁律
- 使用卡片式布局和彩色按钮设计
- 支持自适应布局和最小宽度保护
- 通过信号槽与服务层通信
"""

from .network_config_tab import NetworkConfigTab
from .network_tools_tab import NetworkToolsTab
from .rdp_tab import RdpTab
from .hardware_tab import HardwareTab

__all__ = [
    'NetworkConfigTab',
    'NetworkToolsTab', 
    'RdpTab',
    'HardwareTab'
]
