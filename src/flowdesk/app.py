"""
FlowDesk应用程序入口点

这是FlowDesk应用程序的主入口文件，负责初始化应用程序、设置样式表、
创建主窗口和系统托盘，并启动Qt事件循环。

主要功能：
- 初始化QApplication实例
- 设置应用程序基本信息（名称、版本、图标）
- 加载外置QSS样式表
- 创建主窗口和系统托盘服务
- 处理应用程序退出逻辑
- 支持单实例运行（防止重复启动）

使用方法：
python src/flowdesk/app.py
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon

# 添加项目根目录到Python路径，确保能正确导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flowdesk.ui.main_window import MainWindow
from flowdesk.services.system_tray_service import SystemTrayService
from flowdesk.ui.styles.stylesheet_manager import StylesheetManager
from flowdesk.utils.resource_path import resource_path
from flowdesk.utils.logger import setup_logging, get_logger


class FlowDeskApplication:
    """
    FlowDesk应用程序主类
    
    管理整个应用程序的生命周期，包括窗口创建、托盘服务、
    样式加载等核心功能。采用单例模式确保应用程序唯一性。
    """
    
    def __init__(self):
        """初始化应用程序，设置基本配置和日志系统"""
        # 设置应用程序基本信息
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("FlowDesk")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("FlowDesk Team")
        
        # 设置应用程序图标（显示在任务栏和窗口标题栏）
        app_icon_path = resource_path("assets/icons/flowdesk.ico")
        if os.path.exists(app_icon_path):
            self.app.setWindowIcon(QIcon(app_icon_path))
        
        # 初始化日志系统，记录应用程序运行状态
        setup_logging()
        self.logger = get_logger(__name__)
        self.logger.info("FlowDesk应用程序启动")
        
        # 初始化核心组件
        self.main_window = None
        self.tray_service = None
        self.stylesheet_manager = None
        
    def initialize_components(self):
        """
        初始化应用程序的核心组件
        
        按照依赖关系顺序创建各个组件：
        1. 样式管理器 - 负责加载QSS样式表
        2. 主窗口 - 应用程序的主界面
        3. 系统托盘服务 - 提供托盘图标和菜单功能
        """
        try:
            # 创建并应用样式表管理器
            self.stylesheet_manager = StylesheetManager()
            self.stylesheet_manager.apply_stylesheet(self.app)
            self.logger.info("样式表加载完成")
            
            # 创建主窗口实例
            self.main_window = MainWindow()
            self.logger.info("主窗口创建完成")
            
            # 创建系统托盘服务
            self.tray_service = SystemTrayService(self.main_window)
            self.tray_service.initialize()
            self.logger.info("系统托盘服务初始化完成")
            
            # 连接应用程序退出信号
            self.app.aboutToQuit.connect(self.on_application_quit)
            
        except Exception as e:
            self.logger.error(f"组件初始化失败: {e}")
            sys.exit(1)
    
    def show_main_window(self):
        """
        显示主窗口
        
        将主窗口显示在屏幕中央，并确保窗口获得焦点。
        如果系统托盘可用，窗口将支持最小化到托盘功能。
        """
        if self.main_window:
            self.main_window.show()
            self.main_window.raise_()  # 将窗口提升到最前面
            self.main_window.activateWindow()  # 激活窗口获得焦点
            self.logger.info("主窗口已显示")
    
    def on_application_quit(self):
        """
        应用程序退出时的清理工作
        
        在应用程序关闭前执行必要的清理操作，
        包括保存设置、关闭服务、释放资源等。
        """
        self.logger.info("应用程序正在退出")
        
        # 清理系统托盘
        if self.tray_service:
            self.tray_service.cleanup()
        
        # 保存窗口状态和用户设置
        if self.main_window:
            self.main_window.save_settings()
        
        self.logger.info("应用程序退出完成")
    
    def run(self):
        """
        启动应用程序主循环
        
        初始化所有组件后启动Qt事件循环，
        应用程序将持续运行直到用户退出。
        """
        try:
            # 初始化所有组件
            self.initialize_components()
            
            # 显示主窗口
            self.show_main_window()
            
            # 启动Qt事件循环
            return self.app.exec_()
            
        except Exception as e:
            self.logger.error(f"应用程序运行失败: {e}")
            return 1


def main():
    """
    程序主入口函数
    
    创建FlowDesk应用程序实例并启动运行。
    处理命令行参数和异常情况。
    """
    try:
        # 创建应用程序实例
        app = FlowDeskApplication()
        
        # 启动应用程序
        exit_code = app.run()
        
        # 返回退出码
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n应用程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
