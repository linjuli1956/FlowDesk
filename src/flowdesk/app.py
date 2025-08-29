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
from flowdesk.services.stylesheet_service import StylesheetService
from flowdesk.utils.resource_path import resource_path
from flowdesk.utils.logger import setup_logging, get_logger
from flowdesk.utils.admin_utils import ensure_admin_privileges, get_elevation_status_message


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
        self.stylesheet_service = None
        
    def _load_styles(self):
        """
        加载样式表
        
        加载外置QSS样式表，应用到整个应用程序。
        """
        try:
            # 创建并应用新的样式表管理服务
            self.stylesheet_service = StylesheetService()
            self.stylesheet_service.apply_stylesheets(self.app)
            self.logger.info("样式表加载完成")
        except Exception as e:
            self.logger.error(f"样式表加载失败: {e}")
    
    def run(self):
        """
        启动应用程序主循环
        
        按照正确的顺序初始化各个组件，确保应用程序能够正常运行。
        包括权限检查、样式加载、主窗口创建、托盘服务启动等关键步骤。
        """
        try:
            # 第一步：检查并申请管理员权限
            # 这必须在任何UI组件创建之前进行，因为权限申请可能会重启应用程序
            self.logger.info("正在检查管理员权限...")
            if not ensure_admin_privileges():
                self.logger.warning("未获得管理员权限，网络配置功能将受限")
                # 注意：如果权限申请成功，ensure_admin_privileges会重启程序并退出当前进程
                # 只有权限申请失败时才会继续执行到这里
            else:
                self.logger.info("已获得管理员权限，网络配置功能可正常使用")
            
            # 设置应用程序基本信息
            self.app.setApplicationName("FlowDesk")
            self.app.setApplicationVersion("1.0.0")
            self.app.setOrganizationName("FlowDesk Team")
            
            # 设置应用程序图标
            icon_path = resource_path("assets/icons/flowdesk.ico")
            if os.path.exists(icon_path):
                self.app.setWindowIcon(QIcon(icon_path))
            
            # 加载样式表
            self._load_styles()
            
            # 创建主窗口
            self.main_window = MainWindow()
            
            # 创建并初始化系统托盘服务
            self.tray_service = SystemTrayService(self.main_window)
            self.tray_service.initialize()
            
            # 显示主窗口
            self.main_window.show()
            
            # 记录权限状态信息
            status_msg = get_elevation_status_message()
            self.logger.info(f"应用程序启动完成 - {status_msg}")
            
            # 启动应用程序事件循环
            return self.app.exec_()
            
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


def main():
    """
    程序主入口函数
    
    创建FlowDesk应用程序实例并启动运行。
    处理命令行参数和异常情况。
    """
    try:
        # 创建应用程序实例
        app = FlowDeskApplication()
        
        # 运行应用程序
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
