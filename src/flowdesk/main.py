#!/usr/bin/env python3
"""
FlowDesk应用程序入口文件

这是FlowDesk Windows系统管理工具的主入口点。
负责初始化应用程序、创建主窗口、设置系统托盘等核心功能。

主要功能：
- 应用程序初始化和配置
- 主窗口创建和显示
- 系统托盘集成
- 异常处理和日志记录
- 单实例运行保护
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from src.flowdesk.ui.main_window import MainWindow
from src.flowdesk.services.system_tray_service import SystemTrayService
from src.flowdesk.utils.logger import get_logger
from src.flowdesk.utils.resource_path import resource_path


class FlowDeskApplication:
    """
    FlowDesk应用程序主类
    
    负责管理整个应用程序的生命周期，包括初始化、
    主窗口管理、系统托盘集成等功能。
    """
    
    def __init__(self):
        """
        初始化FlowDesk应用程序
        
        创建QApplication实例，设置应用程序属性，
        初始化日志系统和主要组件。
        """
        # 创建QApplication实例
        self.app = QApplication(sys.argv)
        
        # 设置应用程序属性
        self.setup_application_properties()
        
        # 初始化日志记录器
        self.logger = get_logger(__name__)
        
        # 主窗口实例
        self.main_window = None
        
        # 系统托盘服务实例
        self.tray_service = None
        
        self.logger.info("FlowDesk应用程序初始化完成")
    
    def setup_application_properties(self):
        """
        设置应用程序的基本属性
        
        配置应用程序名称、版本、图标等基础信息。
        这些属性会影响系统托盘、任务栏显示等。
        """
        # 设置应用程序基本信息
        self.app.setApplicationName("FlowDesk")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("FlowDesk Team")
        self.app.setOrganizationDomain("flowdesk.local")
        
        # 设置应用程序图标
        icon_path = resource_path("assets/icons/flowdesk.ico")
        if os.path.exists(icon_path):
            self.app.setWindowIcon(QIcon(icon_path))
        
        # 设置应用程序样式
        self.app.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # 高DPI支持
        self.app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)     # 高DPI图标支持
    
    def create_main_window(self):
        """
        创建主窗口实例
        
        初始化MainWindow对象并设置相关的信号连接。
        主窗口创建后不会立即显示，需要调用show()方法。
        """
        try:
            # 创建主窗口实例
            self.main_window = MainWindow()
            
            self.logger.info("主窗口创建成功")
            
        except Exception as e:
            self.logger.error(f"创建主窗口失败: {e}")
            self.show_error_message("初始化错误", f"无法创建主窗口：{e}")
            return False
        
        return True
    
    def create_tray_service(self):
        """
        创建系统托盘服务
        
        初始化SystemTrayService并设置与主窗口的信号连接。
        如果系统托盘不可用，会记录警告但不影响程序运行。
        """
        try:
            # 创建系统托盘服务实例
            self.tray_service = SystemTrayService(self.main_window)
            
            # 初始化托盘服务
            if self.tray_service.initialize():
                self.logger.info("系统托盘服务创建成功")
                return True
            else:
                self.logger.warning("系统托盘服务初始化失败，但程序将继续运行")
                return False
                
        except Exception as e:
            self.logger.error(f"创建系统托盘服务失败: {e}")
            return False
    
    def handle_window_close(self):
        """
        处理主窗口关闭请求
        
        当用户点击窗口关闭按钮时的处理逻辑。
        现在通过系统托盘服务处理高级关闭逻辑。
        """
        self.logger.info("收到窗口关闭请求")
        
        # 如果有托盘服务，让托盘服务处理关闭逻辑
        # 托盘服务会显示询问对话框，用户可选择退出/最小化/取消
        if self.tray_service:
            # 托盘服务已经连接了主窗口的close_requested信号
            # 这里不需要额外处理，信号会自动传递给托盘服务
            pass
        else:
            # 如果没有托盘服务，直接退出
            self.quit_application()
    
    def show_error_message(self, title, message):
        """
        显示错误消息对话框
        
        在发生严重错误时向用户显示友好的错误信息。
        
        参数:
            title: 对话框标题
            message: 错误消息内容
        """
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
    
    def run(self):
        """
        运行应用程序主循环
        
        创建主窗口、显示界面并启动Qt事件循环。
        这是应用程序的主要执行方法。
        
        返回:
            int: 应用程序退出代码
        """
        try:
            # 创建主窗口
            if not self.create_main_window():
                return 1
            
            # 创建系统托盘服务
            self.create_tray_service()
            
            # 显示主窗口
            self.main_window.show()
            
            self.logger.info("FlowDesk应用程序启动成功")
            
            # 启动Qt事件循环
            return self.app.exec_()
            
        except Exception as e:
            self.logger.error(f"应用程序运行失败: {e}")
            self.show_error_message("运行错误", f"应用程序运行时发生错误：{e}")
            return 1
    
    def quit_application(self):
        """
        退出应用程序
        
        执行清理工作并正常退出应用程序。
        包括保存设置、关闭资源等操作。
        """
        self.logger.info("正在退出FlowDesk应用程序")
        
        # 执行清理工作
        try:
            if self.main_window:
                self.main_window.save_settings()
            
            # 清理系统托盘服务
            if self.tray_service:
                self.tray_service.cleanup()
                
        except Exception as e:
            self.logger.error(f"清理资源失败: {e}")
        
        # 退出应用程序
        self.app.quit()


def main():
    """
    应用程序主入口函数
    
    创建FlowDeskApplication实例并运行应用程序。
    处理命令行参数和异常情况。
    """
    try:
        # 创建应用程序实例
        app = FlowDeskApplication()
        
        # 运行应用程序
        exit_code = app.run()
        
        # 返回退出代码
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n应用程序被用户中断")
        sys.exit(0)
        
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
