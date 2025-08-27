"""
自定义控件组件

包含FlowDesk应用程序的各种自定义UI控件。
这些控件提供特定的功能和视觉效果，增强用户体验。

自定义控件列表：
- FloatWindow: 硬件监控悬浮窗，显示CPU温度、风扇转速等实时数据
- StatusBadge: 状态徽章控件，显示连接状态、DHCP/静态模式等
- PingResultWidget: Ping测试结果显示控件，展示网络连通性测试结果
- HardwareCard: 硬件信息卡片控件，显示CPU、GPU、内存等硬件信息
- ColorButton: 彩色功能按钮，支持不同颜色语义的操作按钮

设计特点：
- 遵循卡片式彩色按钮设计风格
- 支持自适应布局和智能缩放
- 提供丰富的视觉反馈和状态指示
- 集成外置QSS样式系统
- 支持实时数据更新和动画效果
"""

from .float_window import FloatWindow
from .status_badge import StatusBadge
from .ping_result_widget import PingResultWidget
from .hardware_card import HardwareCard
from .color_button import ColorButton

__all__ = [
    'FloatWindow',
    'StatusBadge',
    'PingResultWidget',
    'HardwareCard',
    'ColorButton'
]
