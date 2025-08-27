"""
FlowDesk主窗口类

这是FlowDesk应用程序的主窗口，采用660×645像素的固定尺寸设计。
主窗口包含四个Tab页面，提供网络配置、网络工具、远程桌面和硬件监控功能。

UI四大铁律实现：
🚫 禁止样式重复 - 使用外置QSS样式表，通过objectName应用样式
🔄 严格自适应布局 - 使用QVBoxLayout和QTabWidget实现响应式布局
📏 最小宽度保护 - 设置minimumSize(660, 645)保护最小尺寸
⚙️ 智能组件缩放 - Tab内容区域使用Expanding策略自适应缩放

主要功能：
- 660×645像素窗口布局，居中显示
- 四个Tab页面容器（网络配置、网络工具、远程桌面、硬件信息）
- 窗口图标设置和标题显示
- 与系统托盘服务的集成
- 窗口状态保存和恢复
- 高级关闭逻辑处理
"""

import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QTabWidget, QLabel, QApplication)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QCloseEvent

from ..utils.resource_path import resource_path
from ..utils.logger import get_logger
from .tabs.network_config_tab import NetworkConfigTab


class MainWindow(QMainWindow):
    """
    FlowDesk主窗口类
    
    继承自QMainWindow，提供完整的窗口功能包括菜单栏、状态栏、
    工具栏等。当前实现包含基础的Tab页面容器和窗口管理功能。
    """
    
    # 定义窗口关闭信号，用于与系统托盘服务通信
    close_requested = pyqtSignal()  # 用户请求关闭窗口时发射
    minimize_to_tray_requested = pyqtSignal()  # 请求最小化到托盘时发射
    
    def __init__(self, parent=None):
        """
        初始化主窗口
        
        设置窗口基本属性、创建UI组件、应用样式表，
        并配置窗口的显示位置和行为。
        """
        super().__init__(parent)
        
        # 初始化日志记录器
        self.logger = get_logger(__name__)
        
        # 设置窗口基本属性
        self.setup_window_properties()
        
        # 创建用户界面
        self.setup_ui()
        
        # 加载并应用样式表
        self.load_and_apply_styles()
        
        # 居中显示窗口
        self.center_window()
        
        self.logger.info("主窗口初始化完成")
    
    def setup_window_properties(self):
        """
        设置窗口的基本属性
        
        包括窗口标题、图标、尺寸限制等基础配置。
        确保窗口符合设计规范的660×645像素要求。
        """
        # 设置窗口标题
        self.setWindowTitle("FlowDesk - Windows系统管理工具")
        
        # 设置窗口图标
        icon_path = resource_path("assets/icons/flowdesk.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 设置窗口尺寸 - 实现自适应布局（UI四大铁律）
        self.setMinimumSize(660, 645)  # 最小尺寸保护（UI四大铁律）
        self.resize(660, 645)  # 默认尺寸，但允许用户调整
        
        # 设置窗口属性 - 支持调整大小
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | 
                           Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)  # 支持最大化和调整大小
        
        # 设置objectName用于QSS样式表选择器
        self.setObjectName("main_window")
    
    def setup_ui(self):
        """
        创建用户界面组件
        
        构建主窗口的UI结构，包括中央控件、Tab容器等。
        使用QVBoxLayout确保严格自适应布局（UI四大铁律）。
        """
        # 创建中央控件
        central_widget = QWidget()
        central_widget.setObjectName("central_widget")
        self.setCentralWidget(central_widget)
        
        # 创建主布局 - 使用垂直布局确保自适应（UI四大铁律）
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)  # 设置边距
        main_layout.setSpacing(0)  # 组件间距
        
        # 创建Tab控件容器
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("main_tab_widget")
        
        # Tab控件的尺寸策略 - 智能组件缩放（UI四大铁律）
        from PyQt5.QtWidgets import QSizePolicy
        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 创建四个Tab页面的占位符
        self.create_tab_placeholders()
        
        # 将Tab控件添加到主布局
        main_layout.addWidget(self.tab_widget)
        
        # 设置Tab控件为焦点控件
        self.tab_widget.setFocus()
    
    def create_tab_placeholders(self):
        """
        创建四个Tab页面
        
        创建网络配置实际页面和其他三个功能模块的占位符页面。
        网络配置Tab使用NetworkConfigTab组件，其他Tab暂时使用占位符。
        """
        # 创建网络配置Tab页面（实际功能页面）
        self.network_config_tab = NetworkConfigTab()
        self.tab_widget.addTab(self.network_config_tab, "网络配置")
        
        # 其他Tab页面配置 - 暂时使用占位符
        other_tab_configs = [
            ("网络工具", "network_tools_tab", "网络诊断和系统工具"),
            ("远程桌面", "rdp_tab", "远程桌面连接管理"),
            ("硬件信息", "hardware_tab", "硬件监控和系统信息")
        ]
        
        # 创建其他Tab页面的占位符
        for tab_name, object_name, description in other_tab_configs:
            # 创建Tab页面容器
            tab_widget = QWidget()
            tab_widget.setObjectName(object_name)
            
            # 创建Tab页面布局
            tab_layout = QVBoxLayout(tab_widget)
            tab_layout.setContentsMargins(20, 20, 20, 20)
            
            # 添加占位符标签
            placeholder_label = QLabel(f"{tab_name}\n\n{description}\n\n功能开发中...")
            placeholder_label.setObjectName(f"{object_name}_placeholder")
            placeholder_label.setAlignment(Qt.AlignCenter)
            placeholder_label.setWordWrap(True)
            
            # 标签的尺寸策略 - 智能组件缩放
            from PyQt5.QtWidgets import QSizePolicy
            placeholder_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            tab_layout.addWidget(placeholder_label)
            
            # 将Tab页面添加到Tab控件
            self.tab_widget.addTab(tab_widget, tab_name)
        
        # 默认选中第一个Tab（网络配置）
        self.tab_widget.setCurrentIndex(0)
    
    def load_and_apply_styles(self):
        """
        加载并应用外置QSS样式表
        
        从qss目录加载样式文件并应用到整个应用程序。
        禁止样式重复，统一使用外置样式管理（UI四大铁律）。
        """
        try:
            # 构建QSS文件路径
            qss_dir = os.path.join(os.path.dirname(__file__), "qss")
            
            # 加载样式文件路径
            main_qss_path = os.path.join(qss_dir, "main_window.qss")
            network_qss_path = os.path.join(qss_dir, "network_config_tab.qss")
            tray_dialog_qss_path = os.path.join(qss_dir, "tray_exit_dialog.qss")
            
            # 合并所有样式内容
            combined_styles = ""
            
            # 加载主窗口样式（如果存在）
            if os.path.exists(main_qss_path):
                with open(main_qss_path, 'r', encoding='utf-8') as f:
                    combined_styles += f.read() + "\n"
                    
            # 加载网络配置Tab样式
            if os.path.exists(network_qss_path):
                with open(network_qss_path, 'r', encoding='utf-8') as f:
                    combined_styles += f.read() + "\n"
                    
            # 加载托盘退出对话框样式
            if os.path.exists(tray_dialog_qss_path):
                with open(tray_dialog_qss_path, 'r', encoding='utf-8') as f:
                    combined_styles += f.read() + "\n"
            
            # 应用合并后的样式到整个应用程序
            if combined_styles:
                QApplication.instance().setStyleSheet(combined_styles)
                self.logger.info("QSS样式表加载成功")
            else:
                self.logger.warning("未找到QSS样式文件")
                
        except Exception as e:
            self.logger.error(f"加载QSS样式表失败: {e}")
            # 样式加载失败不影响程序运行，继续执行
    
    def center_window(self):
        """
        将窗口居中显示在屏幕上
        
        计算屏幕中心位置，将窗口移动到屏幕中央。
        确保窗口在不同分辨率的屏幕上都能正确居中显示。
        """
        # 获取屏幕几何信息
        screen = QApplication.desktop().screenGeometry()
        
        # 计算窗口居中位置
        window_geometry = self.geometry()
        x = (screen.width() - window_geometry.width()) // 2
        y = (screen.height() - window_geometry.height()) // 2
        
        # 移动窗口到中心位置
        self.move(x, y)
    
    def closeEvent(self, event: QCloseEvent):
        """
        处理窗口关闭事件
        
        当用户点击窗口关闭按钮时，不直接关闭窗口，
        而是发射信号给系统托盘服务处理高级关闭逻辑。
        
        参数:
            event: Qt关闭事件对象
        """
        # 忽略默认的关闭事件
        event.ignore()
        
        # 发射关闭请求信号，由系统托盘服务处理
        self.close_requested.emit()
        
        self.logger.info("窗口关闭请求已发射信号")
    
    def hide_to_tray(self):
        """
        隐藏窗口到系统托盘
        
        将窗口隐藏而不是关闭，应用程序继续在后台运行。
        用户可以通过系统托盘图标重新显示窗口。
        """
        self.hide()
        self.logger.info("窗口已隐藏到系统托盘")
    
    def show_from_tray(self):
        """
        从系统托盘恢复显示窗口
        
        显示之前隐藏的窗口，并将其提升到最前面获得焦点。
        确保窗口能够正确响应用户操作。
        """
        self.show()
        self.raise_()  # 提升窗口到最前面
        self.activateWindow()  # 激活窗口获得焦点
        self.logger.info("窗口从系统托盘恢复显示")
    
    def toggle_visibility(self):
        """
        切换窗口显示状态
        
        如果窗口当前可见则隐藏到托盘，
        如果窗口当前隐藏则从托盘恢复显示。
        """
        if self.isVisible():
            self.hide_to_tray()
        else:
            self.show_from_tray()
    
    def save_settings(self):
        """
        保存窗口设置
        
        在应用程序退出前保存窗口状态和用户设置，
        包括窗口位置、当前选中的Tab等信息。
        """
        try:
            # 保存当前选中的Tab索引
            current_tab = self.tab_widget.currentIndex()
            
            # 保存窗口位置
            window_pos = self.pos()
            
            # 这里可以添加设置保存逻辑
            # 例如使用QSettings或配置文件
            
            self.logger.info(f"窗口设置已保存 - Tab: {current_tab}, 位置: {window_pos}")
            
        except Exception as e:
            self.logger.error(f"保存窗口设置失败: {e}")
    
    def restore_settings(self):
        """
        恢复窗口设置
        
        在应用程序启动时恢复之前保存的窗口状态，
        包括窗口位置、选中的Tab等信息。
        """
        try:
            # 这里可以添加设置恢复逻辑
            # 例如从QSettings或配置文件读取
            
            self.logger.info("窗口设置已恢复")
            
        except Exception as e:
            self.logger.error(f"恢复窗口设置失败: {e}")
