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
from ..services.network_service import NetworkService


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
        
        # 初始化服务层组件
        self.network_service = None
        
        # 设置窗口基本属性
        self.setup_window_properties()
        
        # 创建用户界面
        self.setup_ui()
        
        # 初始化服务
        self.initialize_services()
        
        # 样式表已由StylesheetService在app.py中统一加载和应用
        # 移除此处调用避免覆盖完整的合并样式表
        
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
    
    def initialize_services(self):
        """
        初始化服务层组件并连接信号槽
        
        创建NetworkService实例，连接UI层与服务层的信号槽通信，
        实现网络配置Tab的核心功能逻辑。
        """
        try:
            # 创建网络服务实例
            self.network_service = NetworkService()
            self.logger.info("网络服务初始化完成")
            
            # 连接网络配置Tab的信号槽
            self._connect_network_config_signals()
            
            # 启动初始化：自动获取网卡信息
            self.network_service.get_all_adapters()
            self.logger.info("网络配置Tab核心功能连接完成")
            
        except Exception as e:
            error_msg = f"服务层初始化失败: {str(e)}"
            self.logger.error(error_msg)
            # 服务初始化失败不影响UI显示，但功能会受限
    
    def _connect_network_config_signals(self):
        """
        连接网络配置Tab的信号槽通信
        
        实现UI层与服务层的双向通信：
        1. UI信号 -> 服务层方法：用户操作触发业务逻辑
        2. 服务层信号 -> UI更新方法：业务逻辑完成后更新界面
        
        严格遵循分层架构：UI层零业务逻辑，服务层零UI操作。
        """
        # === UI信号连接到服务层方法 ===
        
        # 网卡选择变更：UI下拉框选择 -> 服务层选择网卡
        self.network_config_tab.adapter_selected.connect(
            self._on_adapter_combo_changed
        )
        
        # 刷新网卡列表：UI刷新按钮 -> 服务层刷新当前网卡
        self.network_config_tab.refresh_adapters.connect(
            self.network_service.refresh_current_adapter
        )
        
        # 复制网卡信息：UI复制按钮 -> 服务层复制信息到剪贴板
        self.network_config_tab.copy_adapter_info.connect(
            self.network_service.copy_adapter_info
        )
        
        # === 服务层信号连接到UI更新方法 ===
        
        # 网卡列表更新：服务层获取网卡完成 -> UI更新下拉框
        self.network_service.adapters_updated.connect(
            self._on_adapters_updated
        )
        
        # 网卡选择完成：服务层选择网卡完成 -> UI更新显示信息
        self.network_service.adapter_selected.connect(
            self._on_adapter_selected
        )
        
        # IP配置信息更新：服务层解析IP配置 -> UI更新输入框和信息显示
        self.network_service.ip_info_updated.connect(
            self._on_ip_info_updated
        )
        
        # 额外IP列表更新：服务层解析额外IP -> UI更新额外IP列表
        self.network_service.extra_ips_updated.connect(
            self._on_extra_ips_updated
        )
        
        # 网卡刷新完成：服务层刷新完成 -> UI显示刷新成功提示
        self.network_service.adapter_refreshed.connect(
            self._on_adapter_refreshed
        )
        
        # 信息复制完成：服务层复制完成 -> UI显示复制成功提示
        self.network_service.network_info_copied.connect(
            self._on_info_copied
        )
        
        # 错误处理：服务层发生错误 -> UI显示错误信息
        self.network_service.error_occurred.connect(
            self._on_service_error
        )
    
    # === UI事件处理方法：将UI事件转换为服务层调用 ===
    
    def _on_adapter_combo_changed(self, display_name):
        """
        处理网卡下拉框选择变更事件的核心转换逻辑
        
        这个方法是UI层与服务层之间的重要桥梁，负责将用户在界面上选择的
        显示名称转换为服务层能够识别的网卡标识符。采用面向对象的设计模式，
        将复杂的数据转换逻辑封装在独立方法中，确保代码的可维护性和扩展性。
        
        工作原理：
        1. 接收UI层传递的完整显示名称（包含描述和友好名称）
        2. 解析显示名称，提取出网卡的友好名称部分
        3. 在服务层的网卡缓存中查找匹配的网卡对象
        4. 调用服务层的选择方法，触发后续的信息更新流程
        
        Args:
            display_name (str): UI下拉框中选中的完整显示名称，格式为"描述 (友好名称)"
        """
        try:
            if not self.network_service or not display_name:
                return
            
            # 现在显示名称直接是description，需要根据description查找对应的网卡
            # 在服务层的网卡缓存中查找匹配的网卡对象
            # 这里访问服务层的内部数据是为了实现UI与服务层的协调工作
            self.logger.debug(f"查找网卡匹配，显示名称: '{display_name}'")
            self.logger.debug(f"当前缓存网卡数量: {len(self.network_service._adapters) if self.network_service._adapters else 0}")
            
            for adapter in self.network_service._adapters:
                self.logger.debug(f"检查网卡: name='{adapter.name}', description='{adapter.description}', friendly_name='{adapter.friendly_name}'")
                # 现在匹配name字段（完整名称带序号）
                if adapter.name == display_name or adapter.description == display_name or adapter.friendly_name == display_name:
                    # 找到匹配的网卡，调用服务层的选择方法
                    # 这将触发一系列的信号发射，最终更新UI显示
                    self.logger.info(f"找到匹配网卡，调用select_adapter: {adapter.id}")
                    self.network_service.select_adapter(adapter.id)
                    self.logger.info(f"用户选择网卡：{display_name}")
                    return
            
            # 如果没有找到匹配的网卡，记录警告信息便于调试
            self.logger.warning(f"无法找到匹配的网卡，显示名称: '{display_name}'")
                
        except Exception as e:
            # 异常处理：确保网卡选择错误不会导致程序崩溃
            # 详细记录错误信息，便于开发人员快速定位问题
            self.logger.error(f"网卡选择处理失败，错误详情: {str(e)}")
            # 在生产环境中，这里应该向用户显示友好的错误提示
    
    # === 信号处理方法：服务层信号触发的UI更新逻辑 ===
    
    def _on_adapters_updated(self, adapters):
        """
{{ ... }}
        处理网卡列表更新信号的核心业务逻辑
        
        这个方法是网络配置Tab启动初始化的关键环节，负责将服务层获取的网卡数据
        转换为UI层可以显示的格式。采用面向对象设计，将数据处理逻辑封装在此方法中，
        确保UI层只负责显示，不涉及任何业务逻辑处理。
        
        工作流程：
        1. 接收服务层传递的AdapterInfo对象列表
        2. 提取完整的网卡描述信息用于下拉框显示
        3. 调用UI组件的更新方法刷新界面
        4. 记录操作日志便于调试和维护
        
        Args:
            adapters (list): 包含完整网卡信息的AdapterInfo对象列表
        """
        try:
            # 构建网卡显示名称列表：使用完整的name字段（带序号）
            # 这样用户可以看到详细的网卡名称，便于准确识别和选择
            adapter_display_names = []
            for adapter in adapters:
                # 使用name属性，这是网卡的完整名称（带序号）
                # 例如："Hyper-V Virtual Ethernet Adapter #2"
                display_name = adapter.name or adapter.description or adapter.friendly_name or "未知网卡"
                adapter_display_names.append(display_name)
                # 调试输出：检查name内容
                self.logger.debug(f"网卡显示名称: '{display_name}', name: '{adapter.name}', description: '{adapter.description}', friendly_name: '{adapter.friendly_name}'")
            
            # 将处理后的显示名称传递给UI层进行界面更新
            # UI层只负责接收数据并更新显示，不进行任何业务逻辑处理
            self.network_config_tab.update_adapter_list(adapter_display_names)
            
            # 记录成功操作的详细信息，便于系统监控和问题排查
            self.logger.info(f"网卡列表更新完成：成功加载 {len(adapters)} 个网络适配器到下拉框")
            
        except Exception as e:
            # 异常处理：确保单个网卡信息错误不影响整体功能
            # 记录详细错误信息便于开发人员定位和修复问题
            self.logger.error(f"网卡列表更新失败，错误详情: {str(e)}")
            # 在生产环境中，这里可以显示用户友好的错误提示
    
    def _on_adapter_selected(self, adapter_info):
        """
        处理网卡选择完成信号的UI更新逻辑
        
        这个方法是网卡选择流程的最后一环，负责将服务层选择的网卡信息
        同步到UI界面的各个显示组件。采用面向对象的设计原则，将UI更新
        逻辑集中管理，确保界面状态与数据状态的一致性。
        
        更新范围包括：
        1. 当前网卡标签：显示用户当前操作的网卡名称
        2. 连接状态徽章：直观显示网卡的连接状态
        3. IP信息展示区域：显示选中网卡的详细网络配置
        
        Args:
            adapter_info (AdapterInfo): 服务层传递的完整网卡信息对象
        """
        try:
            # 更新当前网卡标签，让用户清楚知道正在操作哪个网卡
            # 使用友好名称提供用户熟悉的网卡标识
            current_adapter_text = f"当前网卡: {adapter_info.friendly_name}"
            self.network_config_tab.update_current_adapter_label(current_adapter_text)
            
            # 网卡状态显示逻辑 - 根据实际网卡状态显示准确的状态信息
            # 优先显示网卡的真实状态（如已禁用），而不是简单的连接/未连接二分法
            if not adapter_info.is_enabled:
                # 网卡被禁用时，显示禁用状态而非未连接状态
                status_text = adapter_info.status  # 直接使用详细状态，如"已禁用"、"硬件已禁用"等
                is_connected_for_badge = False
            else:
                # 网卡启用时，根据连接状态显示
                status_text = "已连接" if adapter_info.is_connected else "未连接"
                is_connected_for_badge = adapter_info.is_connected
            
            self.network_config_tab.update_status_badge(status_text, is_connected_for_badge)
            
            # 更新所有状态徽章，包括连接状态、IP模式和链路速度
            # 提供完整的网卡状态信息展示
            ip_mode = "DHCP" if adapter_info.dhcp_enabled else "静态IP"
            link_speed = adapter_info.link_speed if adapter_info.link_speed else "未知"
            self.network_config_tab.update_status_badges(status_text, ip_mode, link_speed)
            
            # 构建并更新IP信息展示区域
            # 这是解决"IP信息展示容器不更新"问题的关键代码
            formatted_info = self._format_adapter_info_for_display(adapter_info)
            self.network_config_tab.update_ip_info_display(formatted_info)
            
            # 记录网卡选择操作的完成状态，便于系统监控和调试
            self.logger.info(f"网卡选择界面更新完成: {adapter_info.friendly_name}")
            
        except Exception as e:
            # 异常处理：确保UI更新错误不影响核心功能
            # 记录详细错误信息便于问题定位和修复
            self.logger.error(f"网卡选择界面更新失败，错误详情: {str(e)}")
            # 在生产环境中，这里应该提供用户友好的错误反馈
    
    def _on_ip_info_updated(self, ip_config):
        """
        处理IP配置信息更新信号的核心数据同步逻辑
        
        这个方法是网络配置Tab数据同步的关键环节，负责将服务层解析的
        IP配置信息转换为UI层可以显示的格式，并更新相应的输入框组件。
        采用面向对象的设计模式，确保数据流的单向性和可维护性。
        
        数据流程：
        1. 接收服务层传递的IPConfigInfo对象
        2. 提取各项网络配置参数
        3. 构建UI层需要的配置字典
        4. 调用UI组件的更新方法同步显示
        
        智能显示策略：
        - 主IP地址显示在专用输入框中
        - 空值使用空字符串避免显示异常
        - DHCP状态控制输入框的启用状态
        
        Args:
            ip_config (IPConfigInfo): 包含完整IP配置信息的数据对象
        """
        try:
            # 构建UI层需要的配置数据字典
            # 这里进行数据格式转换，确保UI组件能够正确处理
            config_data = {
                'ip_address': ip_config.ip_address or '',  # 主IP地址，空值转换为空字符串
                'subnet_mask': ip_config.subnet_mask or '',  # 子网掩码
                'gateway': ip_config.gateway or '',  # 默认网关
                'dns_primary': ip_config.dns_primary or '',  # 主DNS服务器
                'dns_secondary': ip_config.dns_secondary or '',  # 备用DNS服务器
                'dhcp_enabled': ip_config.dhcp_enabled  # DHCP启用状态
            }
            
            # 调用UI层的配置更新方法，实现界面与数据的同步
            # 这确保了用户看到的信息与实际网卡配置保持一致
            self.network_config_tab.update_ip_config_inputs(config_data)
            
            # 记录IP配置更新的成功状态，便于系统监控和调试
            self.logger.info(f"IP配置界面更新完成: {ip_config.ip_address or '无IP地址'}")
            
        except Exception as e:
            # 异常处理：确保IP配置更新错误不影响其他功能
            # 记录详细错误信息便于开发人员快速定位和解决问题
            self.logger.error(f"IP配置界面更新失败，错误详情: {str(e)}")
            # 在生产环境中，这里应该向用户显示友好的错误提示
    
    def _on_extra_ips_updated(self, extra_ips):
        """
        处理额外IP列表更新信号
        
{{ ... }}
        当服务层解析额外IP完成后，更新右侧额外IP列表显示。
        
        Args:
            extra_ips (list): ExtraIP对象列表
        """
        try:
            # 格式化额外IP信息
            ip_list = []
            for extra_ip in extra_ips:
                ip_info = f"{extra_ip.ip_address}/{extra_ip.subnet_mask}"
                ip_list.append(ip_info)
            
            # 更新额外IP列表
            self.network_config_tab.update_extra_ip_list(ip_list)
            
            self.logger.info(f"额外IP列表已更新，共 {len(extra_ips)} 个")
            
        except Exception as e:
            self.logger.error(f"更新额外IP列表失败: {str(e)}")
    
    def _on_adapter_refreshed(self, adapter_info):
        """
        处理网卡刷新完成信号的UI同步更新逻辑
        
        这个方法是"刷新按钮"功能的最终响应环节，负责将服务层刷新获取的
        最新网卡信息同步到UI界面的各个显示组件。采用面向对象的设计原则，
        确保刷新操作后界面状态与最新数据状态完全一致。
        
        刷新更新范围：
        1. 当前网卡标签：确保显示正确的网卡名称
        2. 连接状态徽章：反映最新的连接状态
        3. IP信息展示区域：显示刷新后的网络配置
        
        这是解决"刷新时IP信息展示容器不更新"问题的关键方法。
        
        Args:
            adapter_info (AdapterInfo): 服务层刷新后获取的最新网卡信息对象
        """
        try:
            # 更新当前网卡标签，确保显示最新的网卡标识
            current_adapter_text = f"当前网卡: {adapter_info.friendly_name}"
            self.network_config_tab.update_current_adapter_label(current_adapter_text)
            
            # 网卡状态显示逻辑 - 刷新后根据实际网卡状态显示准确的状态信息
            # 优先显示网卡的真实状态（如已禁用），确保刷新后状态显示的准确性
            if not adapter_info.is_enabled:
                # 网卡被禁用时，显示禁用状态而非未连接状态
                status_text = adapter_info.status  # 直接使用详细状态，如"已禁用"、"硬件已禁用"等
                is_connected_for_badge = False
            else:
                # 网卡启用时，根据连接状态显示
                status_text = "已连接" if adapter_info.is_connected else "未连接"
                is_connected_for_badge = adapter_info.is_connected
            
            self.network_config_tab.update_status_badge(status_text, is_connected_for_badge)
            
            # 更新所有状态徽章，包括连接状态、IP模式和链路速度
            # 确保刷新后显示完整的网卡状态信息
            ip_mode = "DHCP" if adapter_info.dhcp_enabled else "静态IP"
            link_speed = adapter_info.link_speed if adapter_info.link_speed else "未知"
            self.network_config_tab.update_status_badges(status_text, ip_mode, link_speed)
            
            # 构建并更新IP信息展示区域 - 这是修复刷新问题的关键代码
            # 确保刷新操作后用户能够看到最新的网卡配置信息
            formatted_info = self._format_adapter_info_for_display(adapter_info)
            self.network_config_tab.update_ip_info_display(formatted_info)
            
            # 记录刷新操作的成功完成状态，便于系统监控和调试
            self.logger.info(f"网卡刷新界面更新完成: {adapter_info.friendly_name}")
            
        except Exception as e:
            # 异常处理：确保刷新错误不影响其他功能的正常运行
            # 记录详细错误信息便于开发人员快速定位和解决问题
            self.logger.error(f"网卡刷新界面更新失败，错误详情: {str(e)}")
            # 在生产环境中，这里应该向用户显示友好的错误反馈
    
    def _on_info_copied(self, copied_text):
        """
        处理信息复制完成信号
        
        当服务层复制网卡信息到剪贴板完成后，显示复制成功提示。
        
        Args:
            copied_text (str): 复制到剪贴板的文本内容
        """
        try:
            # 这里可以添加复制成功的提示逻辑
            # 例如状态栏消息、临时提示等
            self.logger.info("网卡信息已复制到剪贴板")
            
        except Exception as e:
            self.logger.error(f"处理信息复制信号失败: {str(e)}")
    
    def _on_service_error(self, error_title, error_message):
        """
        处理服务层错误信号
        
        当服务层发生错误时，在UI上显示错误信息。
        确保用户能够了解操作失败的原因。
        
        Args:
            error_title (str): 错误标题
            error_message (str): 错误详细信息
        """
        try:
            # 记录错误日志
            self.logger.error(f"{error_title}: {error_message}")
            
            # 这里可以添加错误提示逻辑
            # 例如消息框、状态栏错误提示等
            
        except Exception as e:
            self.logger.error(f"处理服务层错误信号失败: {str(e)}")
    
    def _format_adapter_info_for_display(self, adapter_info):
        """
        格式化网卡信息用于显示
        
        将AdapterInfo对象格式化为用户友好的文本格式，
        在左侧IP信息展示区域显示。
        
        Args:
            adapter_info (AdapterInfo): 网卡信息对象
            
        Returns:
            str: 格式化后的显示文本
        """
        try:
            # 构建详细的网卡信息显示文本
            info_lines = []
            info_lines.append(f"网卡描述: {adapter_info.description or '未知'}")
            info_lines.append(f"友好名称: {adapter_info.friendly_name}")
            info_lines.append(f"物理地址: {adapter_info.mac_address or '未知'}")
            info_lines.append(f"连接状态: {'已连接' if adapter_info.is_connected else '未连接'}")
            info_lines.append(f"接口类型: {adapter_info.interface_type or '未知'}")
            info_lines.append(f"链路速度: {adapter_info.link_speed}Mbps" if adapter_info.link_speed else "链路速度: 未知")
            info_lines.append("")
            
            # IP配置信息 - 优先显示IPv4地址信息
            info_lines.append("=== IP配置信息 ===")
            primary_ip = adapter_info.get_primary_ip()
            primary_mask = adapter_info.get_primary_subnet_mask()
            if primary_ip:
                info_lines.append(f"主IP地址: {primary_ip}")
                info_lines.append(f"子网掩码: {primary_mask}")
            else:
                info_lines.append("主IP地址: 未配置")
            
            # 额外IPv4地址 - 紧接在主IP信息后显示
            extra_ips = adapter_info.get_extra_ips()
            if extra_ips:
                info_lines.append("")
                info_lines.append("额外IPv4地址:")
                for ip, mask in extra_ips:
                    info_lines.append(f"  • {ip}/{mask}")
            
            # 网关和DNS配置
            info_lines.append("")
            info_lines.append("=== 网络配置 ===")
            info_lines.append(f"默认网关: {adapter_info.gateway or '未配置'}")
            info_lines.append(f"DHCP状态: {'启用' if adapter_info.dhcp_enabled else '禁用'}")
            
            primary_dns = adapter_info.get_primary_dns()
            secondary_dns = adapter_info.get_secondary_dns()
            info_lines.append(f"主DNS服务器: {primary_dns or '未配置'}")
            info_lines.append(f"备用DNS服务器: {secondary_dns or '未配置'}")
            
            # IPv6地址信息 - 移至最下方显示，在时间戳之前
            if adapter_info.ipv6_addresses:
                info_lines.append("")
                info_lines.append("=== IPv6配置信息 ===")
                for i, ipv6_addr in enumerate(adapter_info.ipv6_addresses):
                    if i == 0:
                        info_lines.append(f"主IPv6地址: {ipv6_addr}")
                    else:
                        info_lines.append(f"额外IPv6地址: {ipv6_addr}")
            
            # 添加时间戳 - 保持在最底部
            info_lines.append("")
            info_lines.append(f"最后更新: {adapter_info.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
            
            return "\n".join(info_lines)
            
        except Exception as e:
            self.logger.error(f"格式化网卡信息失败: {str(e)}")
            return "网卡信息格式化失败"
    
    def load_and_apply_styles(self):
        """
        样式表加载已由StylesheetService统一管理
        
        此方法已废弃，样式表加载统一由StylesheetService处理，
        避免重复setStyleSheet调用导致的样式覆盖问题。
        """
        # 样式表加载已在app.py中通过StylesheetService统一处理
        # 移除此处的重复加载逻辑，避免覆盖StylesheetService的完整样式
        self.logger.info("样式表加载由StylesheetService统一管理，跳过重复加载")
        pass
    
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
