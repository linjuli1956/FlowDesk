"""
对话框组件

包含FlowDesk应用程序的各种弹出对话框。
所有对话框都采用模态设计，提供清晰的用户交互和数据输入界面。

对话框列表：
- RdpConnectDialog: RDP连接配置对话框，设置连接参数和凭据
- AddIpDialog: 添加IP地址对话框，配置额外的IP地址
- UserManagementDialog: 用户管理对话框，创建和管理系统用户
- FloatWindowSettingsDialog: 悬浮窗设置对话框，配置硬件监控悬浮窗
- ConfirmDialog: 通用确认对话框，用于重要操作确认

设计特点：
- 采用卡片式设计风格
- 合理的对话框尺寸和布局
- 清晰的按钮颜色语义（蓝色确认、红色取消、绿色应用）
- 支持键盘快捷键操作
- 数据验证和错误提示
"""

from .add_ip_dialog import AddIPDialog
from .operation_result_dialog import OperationResultDialog
from .network_progress_dialog import NetworkProgressDialog, NetworkOperationWorker, show_network_progress

__all__ = [
    'AddIPDialog',
    'OperationResultDialog',
    'NetworkProgressDialog',
    'NetworkOperationWorker',
    'show_network_progress'
]
