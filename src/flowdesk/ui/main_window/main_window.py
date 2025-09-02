# -*- coding: utf-8 -*-
"""
FlowDesk主窗口拼装类：组合各功能组件的主入口类

这是一个轻量级的主窗口拼装类，采用组合模式将复杂的主窗口功能
分解为四个独立的模块组件，实现高内聚低耦合的模块化架构。

架构设计原则：
- 单一职责：每个组件专注于特定功能领域
- 依赖注入：通过构造函数注入依赖关系
- 接口分离：各组件通过清晰的接口进行交互
- 开闭原则：易于扩展新功能，无需修改现有代码
"""

from ...utils.logger import get_logger
from .main_window_base import MainWindowBase
from .service_coordinator import ServiceCoordinator
from .network_event_handler import NetworkEventHandler
from .ui_state_manager import UIStateManager


class MainWindow(MainWindowBase):
    """
    FlowDesk主窗口拼装类
    
    组合四个功能模块的轻量级主窗口类：
    - MainWindowBase: 窗口基础功能和UI结构
    - ServiceCoordinator: 服务层初始化和信号连接
    - NetworkEventHandler: 网络配置事件处理
    - UIStateManager: UI状态更新管理
    
    采用组合模式实现模块化架构，提高可维护性和并行开发能力。
    严格遵循企业级软件架构的分层设计原则。
    """
    
    def __init__(self):
        """
        初始化主窗口及各功能组件
        
        按照依赖注入的设计模式，依次初始化各个功能组件，
        确保组件间的依赖关系正确建立，避免循环依赖问题。
        """
        # 初始化日志记录器
        self.logger = get_logger(__name__)
        self.logger.info("开始初始化主窗口拼装类")
        
        # 调用基础窗口初始化
        super().__init__()
        
        # 初始化各功能组件
        self._init_components()
        
        self.logger.info("主窗口拼装类初始化完成")
    
    def _init_components(self):
        """
        初始化各功能组件
        
        按照组件依赖关系的正确顺序进行初始化：
        1. 服务协调器：负责服务层的统一管理
        2. 网络事件处理器：处理网络相关的UI事件
        3. UI状态管理器：管理界面状态的同步更新
        4. 执行服务初始化：启动所有服务并建立信号连接
        """
        try:
            # 初始化服务协调器：统一管理所有服务层组件
            self.service_coordinator = ServiceCoordinator(self)
            
            # 初始化网络事件处理器：需要传递network_service参数
            # 注意：此时network_service还未初始化，先传递None，稍后在服务初始化后设置
            self.network_event_handler = NetworkEventHandler(self, None)
            
            # 初始化UI状态管理器：负责界面状态的统一管理
            self.ui_state_manager = UIStateManager(self)
            
            # 执行服务初始化：仅创建服务实例，不连接信号
            self.service_coordinator.initialize_services()
            
            # 设置network_event_handler的network_service引用并连接信号
            self.network_event_handler.set_network_service(self.service_coordinator.network_service)
            
            # 延迟注入：连接信号并启动服务功能
            self.service_coordinator.inject_and_connect()
            
            self.logger.info("所有功能组件初始化完成")
            
        except Exception as e:
            self.logger.error(f"组件初始化失败: {e}")
            raise
    
    def closeEvent(self, event):
        """
        窗口关闭事件处理
        
        当用户关闭主窗口时，发射窗口关闭信号供系统托盘服务处理。
        这样可以实现最小化到托盘而不是直接退出程序的功能。
        """
        try:
            # 发射窗口关闭信号，由系统托盘服务决定是否真正关闭
            self.close_requested.emit()
            
            # 忽略关闭事件，让系统托盘服务处理
            event.ignore()
            
            self.logger.info("主窗口关闭请求已发射信号")
            
        except Exception as e:
            self.logger.error(f"窗口关闭事件处理失败: {e}")
            # 发生异常时允许正常关闭
            event.accept()
    
    def changeEvent(self, event):
        """
        窗口状态变更事件处理
        
        当窗口最小化时，发射最小化信号供系统托盘服务处理。
        实现最小化到托盘的用户体验。
        """
        try:
            from PyQt5.QtCore import QEvent
            
            if event.type() == QEvent.WindowStateChange:
                from PyQt5.QtCore import Qt
                
                if self.windowState() & Qt.WindowMinimized:
                    # 发射最小化到托盘信号
                    self.minimize_to_tray_requested.emit()
                    self.logger.info("主窗口最小化请求已发射信号")
            
            # 调用父类的事件处理
            super().changeEvent(event)
            
        except Exception as e:
            self.logger.error(f"窗口状态变更事件处理失败: {e}")
            super().changeEvent(event)
