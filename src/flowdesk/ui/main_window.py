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
                            QTabWidget, QLabel, QApplication, QMessageBox)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QCloseEvent

from ..utils.resource_path import resource_path
from ..utils.logger import get_logger
from .tabs.network_config_tab import NetworkConfigTab
from ..services import NetworkService


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
        
        # IP配置应用：UI修改IP按钮 -> 服务层应用IP配置
        self.network_config_tab.apply_ip_config.connect(
            self._on_apply_ip_config
        )
        
        # 批量添加选中IP：UI添加选中按钮 -> 服务层批量添加额外IP
        self.network_config_tab.add_selected_ips.connect(
            self.network_service.add_selected_extra_ips
        )
        
        # 批量删除选中IP：UI删除选中按钮 -> 服务层批量删除额外IP
        self.network_config_tab.remove_selected_ips.connect(
            self.network_service.remove_selected_extra_ips
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
        
        # 网卡信息更新完成：服务层刷新网卡信息完成 -> UI更新IP信息显示和状态徽章
        self.network_service.adapter_info_updated.connect(
            self._on_adapter_info_updated
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
        
        # IP配置应用完成：服务层配置完成 -> UI显示成功提示
        self.network_service.ip_config_applied.connect(
            self._on_ip_config_applied
        )
        
        # 操作进度更新：服务层操作进度 -> UI显示进度信息
        self.network_service.operation_progress.connect(
            self._on_operation_progress
        )
        
        # 批量额外IP添加完成：服务层批量添加完成 -> UI显示操作结果
        self.network_service.extra_ips_added.connect(
            self._on_extra_ips_added
        )
        
        # 批量额外IP删除完成：服务层批量删除完成 -> UI显示操作结果
        self.network_service.extra_ips_removed.connect(
            self._on_extra_ips_removed
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
                    # 找到匹配的网卡，立即更新状态徽章以减少卡顿感
                    # 先使用缓存的网卡信息快速更新状态徽章
                    self.logger.info(f"找到匹配网卡，立即更新状态徽章: {adapter.id}")
                    
                    # 移除立即更新逻辑，避免显示过时的缓存数据
                    # 直接依赖服务层的完整刷新流程，确保显示最新的链路速度信息
                    
                    # 然后调用服务层的选择方法进行完整刷新
                    # 这将触发一系列的信号发射，最终更新UI显示
                    self.logger.info(f"调用select_adapter进行完整刷新: {adapter.id}")
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
    
    def _on_apply_ip_config(self, config_data):
        """
        处理IP配置应用请求的核心业务逻辑转换方法
        
        这个方法是"修改IP地址"按钮功能的关键桥梁，负责将UI层收集的
        配置数据转换为服务层能够处理的格式，并调用相应的业务方法。
        采用面向对象的设计原则，将UI事件转换逻辑封装在独立方法中。
        
        工作流程：
        1. 接收UI层传递的配置数据字典
        2. 验证必要的配置参数是否完整
        3. 获取当前选中的网卡标识符
        4. 调用服务层的IP配置应用方法
        5. 处理可能的异常情况并记录日志
        
        参数说明：
            config_data (dict): UI层收集的IP配置数据，包含：
                - ip_address: IP地址
                - subnet_mask: 子网掩码
                - gateway: 网关地址（可选）
                - primary_dns: 主DNS服务器（可选）
                - secondary_dns: 辅助DNS服务器（可选）
                - adapter: 网卡显示名称
        """
        try:
            # 验证服务层是否已正确初始化
            if not self.network_service:
                self.logger.error("网络服务未初始化，无法应用IP配置")
                return
            
            # 验证必要的配置参数
            ip_address = config_data.get('ip_address', '').strip()
            subnet_mask = config_data.get('subnet_mask', '').strip()
            
            if not ip_address or not subnet_mask:
                self.logger.warning("IP地址或子网掩码为空，无法应用配置")
                return
            
            # 获取当前选中的网卡ID
            # 需要通过显示名称查找对应的网卡对象
            adapter_display_name = config_data.get('adapter', '')
            if not adapter_display_name:
                self.logger.warning("未选择网卡，无法应用IP配置")
                return
            
            # 在服务层的网卡缓存中查找匹配的网卡对象
            target_adapter_id = None
            for adapter in self.network_service._adapters:
                if (adapter.name == adapter_display_name or 
                    adapter.description == adapter_display_name or 
                    adapter.friendly_name == adapter_display_name):
                    target_adapter_id = adapter.id
                    break
            
            if not target_adapter_id:
                self.logger.error(f"无法找到匹配的网卡: {adapter_display_name}")
                return
            
            # 提取可选配置参数
            gateway = config_data.get('gateway', '').strip()
            primary_dns = config_data.get('primary_dns', '').strip()
            secondary_dns = config_data.get('secondary_dns', '').strip()
            
            # 记录IP配置应用操作的开始
            self.logger.info(f"开始应用IP配置到网卡 {adapter_display_name}: "
                           f"IP={ip_address}, 掩码={subnet_mask}")
            
            # 调用服务层的IP配置应用方法
            # 这将触发实际的网络配置修改操作
            success = self.network_service.apply_ip_config(
                adapter_id=target_adapter_id,
                ip_address=ip_address,
                subnet_mask=subnet_mask,
                gateway=gateway,
                primary_dns=primary_dns,
                secondary_dns=secondary_dns
            )
            
            if success:
                self.logger.info(f"IP配置应用成功: {adapter_display_name}")
            else:
                self.logger.warning(f"IP配置应用失败: {adapter_display_name}")
                
        except Exception as e:
            # 异常处理：确保IP配置错误不会导致程序崩溃
            # 记录详细错误信息便于开发人员快速定位问题
            self.logger.error(f"处理IP配置应用请求失败，错误详情: {str(e)}")
            # 在生产环境中，这里应该向用户显示友好的错误提示
    
    def _sync_adapter_combo_selection(self, adapter_info):
        """
        同步下拉框选择状态与服务层数据的核心同步方法
        
        这个方法解决了启动时网卡信息不匹配的根本问题，确保UI下拉框的选择
        状态与服务层当前选中的网卡完全一致。该方法体现了面向对象架构中
        数据一致性维护的重要原则，通过精确的匹配逻辑保证UI状态同步。
        
        面向对象架构特点：
        - 封装性：将复杂的下拉框同步逻辑封装在独立方法中
        - 单一职责：专门负责UI选择状态与数据状态的同步
        - 依赖倒置：依赖于AdapterInfo抽象数据模型，不依赖具体实现
        - 接口分离：提供清晰的同步接口，与其他UI更新操作分离
        
        工作原理：
        1. 遍历下拉框中的所有选项，寻找与当前网卡匹配的项目
        2. 使用多重匹配策略：name、description、friendly_name三重保障
        3. 临时阻断信号发射，避免触发循环选择事件
        4. 更新下拉框选中索引，确保UI显示与数据一致
        
        Args:
            adapter_info (AdapterInfo): 服务层当前选中的网卡信息对象
        """
        try:
            # 临时阻断下拉框的信号发射，避免触发循环选择事件
            # 这是防止UI事件与服务层事件相互干扰的关键技术
            self.network_config_tab.adapter_combo.blockSignals(True)
            
            # 遍历下拉框中的所有选项，寻找与当前网卡匹配的项目
            combo_box = self.network_config_tab.adapter_combo
            for index in range(combo_box.count()):
                item_text = combo_box.itemText(index)
                
                # 使用多重匹配策略确保准确匹配
                # 支持name、description、friendly_name三种标识符的匹配
                if (item_text == adapter_info.name or 
                    item_text == adapter_info.description or 
                    item_text == adapter_info.friendly_name):
                    
                    # 找到匹配项，更新下拉框选中状态
                    combo_box.setCurrentIndex(index)
                    self.logger.debug(f"下拉框同步完成，选中索引: {index}, 网卡: {item_text}")
                    break
            else:
                # 如果没有找到匹配项，记录警告信息便于调试
                self.logger.warning(f"下拉框中未找到匹配的网卡选项: {adapter_info.name}")
            
        except Exception as e:
            # 异常处理：确保同步错误不影响核心功能
            self.logger.error(f"下拉框同步失败: {str(e)}")
        finally:
            # 恢复下拉框的信号发射，确保后续用户操作正常
            # 使用finally确保信号状态始终能够正确恢复
            self.network_config_tab.adapter_combo.blockSignals(False)
    
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
            self.network_config_tab.update_adapter_list_with_mapping(adapters)
            
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
            # 第一步：同步下拉框选择状态，确保UI与服务层数据一致
            # 这是解决启动时信息不匹配问题的关键步骤
            self._sync_adapter_combo_selection(adapter_info)
            
            # 第二步：更新当前网卡标签，让用户清楚知道正在操作哪个网卡
            self.network_config_tab.update_current_adapter_label(adapter_info.friendly_name)
            
            # 第三步：网卡状态显示逻辑 - 根据实际网卡状态显示准确的状态信息
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
            self.logger.info(f"状态徽章更新 - 链路速度: '{link_speed}' (原始值: '{adapter_info.link_speed}') - 网卡: {adapter_info.friendly_name}")
            self.network_config_tab.update_status_badges(status_text, ip_mode, link_speed)
            self.logger.info(f"已调用update_status_badges - 状态: {status_text}, IP模式: {ip_mode}, 链路速度: {link_speed}")
            
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
    
    def _on_adapter_info_updated(self, aggregated_info):
        """
        处理网卡信息更新信号的统一协调方法
        
        这个方法作为网卡信息更新的统一入口，负责协调状态徽章和IP信息显示的更新。
        严格遵循单一职责原则，将不同类型的UI更新分发到专门的处理方法。
        
        数据流程：
        1. 接收服务层聚合的网卡信息
        2. 提取详细信息对象
        3. 分别调用状态徽章和IP信息显示更新方法
        
        Args:
            aggregated_info: 包含网卡各类信息的聚合字典
        """
        try:
            self.logger.debug(f"[调试] _on_adapter_info_updated被调用，aggregated_info类型: {type(aggregated_info)}")
            
            # 提取详细信息对象
            detailed_info = aggregated_info.get('detailed_info')
            if not detailed_info:
                self.logger.warning("聚合信息中缺少详细信息，跳过UI更新")
                return
            
            self.logger.debug(f"[调试] 提取到detailed_info，类型: {type(detailed_info)}")
            self.logger.debug(f"[调试] detailed_info属性: status={getattr(detailed_info, 'status', 'N/A')}, link_speed={getattr(detailed_info, 'link_speed', 'N/A')}, dhcp_enabled={getattr(detailed_info, 'dhcp_enabled', 'N/A')}")
            
            # 更新状态徽章：提取状态信息并更新UI显示
            self.logger.debug("[调试] 即将调用_update_status_badges_from_info")
            self._update_status_badges_from_info(detailed_info)
            
            # 更新IP信息展示区域：格式化详细信息并更新显示
            self.logger.debug("[调试] 即将调用_update_ip_info_display_from_info")
            self._update_ip_info_display_from_info(detailed_info)
            
            self.logger.info(f"网卡信息UI更新完成: {getattr(detailed_info, 'name', '未知网卡')}")
            
        except Exception as e:
            self.logger.error(f"网卡信息更新处理失败: {str(e)}")
            import traceback
            self.logger.error(f"异常堆栈: {traceback.format_exc()}")

    def _update_status_badges_from_info(self, detailed_info):
        """
        从详细信息中提取状态数据并更新状态徽章
        
        这个方法专门负责状态徽章的更新逻辑，将业务数据转换为UI显示格式。
        严格遵循单一职责原则，只处理状态徽章相关的UI更新。
        
        Args:
            detailed_info: 网卡详细信息对象
        """
        try:
            self.logger.debug(f"[调试] _update_status_badges_from_info开始执行")
            
            # 提取连接状态：优先使用服务层判断的状态
            connection_status = detailed_info.status if hasattr(detailed_info, 'status') else "未知"
            self.logger.debug(f"[调试] 提取连接状态: {connection_status}")
            
            # 提取IP模式：基于DHCP启用状态判断
            ip_mode = "DHCP" if (hasattr(detailed_info, 'dhcp_enabled') and detailed_info.dhcp_enabled) else "静态IP"
            self.logger.debug(f"[调试] 提取IP模式: {ip_mode}")
            
            # 提取链路速度：优先使用性能服务获取的速度信息
            link_speed = detailed_info.link_speed if (hasattr(detailed_info, 'link_speed') and detailed_info.link_speed) else "未知"
            self.logger.debug(f"[调试] 提取链路速度: {link_speed}")
            
            # 调用UI组件更新状态徽章
            self.logger.debug(f"[调试] 即将调用network_config_tab.update_status_badges")
            self.network_config_tab.update_status_badges(connection_status, ip_mode, link_speed)
            
            self.logger.info(f"状态徽章已更新 - 连接状态: {connection_status}, IP模式: {ip_mode}, 链路速度: {link_speed}")
            
        except Exception as e:
            self.logger.error(f"状态徽章更新失败: {str(e)}")
            import traceback
            self.logger.error(f"状态徽章更新异常堆栈: {traceback.format_exc()}")
    
    def _update_ip_info_display_from_info(self, detailed_info):
        """
        从详细信息中格式化IP信息并更新显示区域
        
        这个方法专门负责IP信息展示区域的更新，将网卡详细信息
        格式化为用户友好的显示格式并更新UI组件。
        
        Args:
            detailed_info: 网卡详细信息对象
        """
        try:
            # 格式化网卡信息为显示文本
            formatted_info = self._format_adapter_info_for_display(detailed_info)
            
            # 更新IP信息展示区域
            self.network_config_tab.update_ip_info_display(formatted_info)
            
            self.logger.info("IP信息展示区域已更新")
            
        except Exception as e:
            self.logger.error(f"IP信息显示更新失败: {str(e)}")
            import traceback
            self.logger.error(f"异常堆栈: {traceback.format_exc()}")
    
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
            self.logger.info(f"[调试] 准备更新IP配置输入框，数据: {config_data}")
            self.network_config_tab.update_ip_config_inputs(config_data)
            self.logger.info(f"[调试] IP配置输入框更新完成")
            
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
            # 检查数据类型并相应处理
            if extra_ips and isinstance(extra_ips[0], str):
                # 如果接收到的是字符串列表（格式："ip/mask"），直接使用
                ip_list = extra_ips
                self.logger.info(f"接收到字符串格式的额外IP列表: {ip_list}")
            else:
                # 如果接收到的是ExtraIP对象列表，格式化为字符串
                ip_list = []
                for extra_ip in extra_ips:
                    if hasattr(extra_ip, 'ip_address') and hasattr(extra_ip, 'subnet_mask'):
                        ip_info = f"{extra_ip.ip_address}/{extra_ip.subnet_mask}"
                        ip_list.append(ip_info)
                self.logger.info(f"格式化ExtraIP对象为字符串列表: {ip_list}")
            
            # 更新额外IP列表
            self.network_config_tab.update_extra_ip_list(ip_list)
            
            self.logger.info(f"额外IP列表已更新，共 {len(extra_ips)} 个")
            
        except Exception as e:
            self.logger.error(f"更新额外IP列表失败: {str(e)}")
            import traceback
            self.logger.error(f"异常堆栈: {traceback.format_exc()}")
    
    
    def _update_ip_display_from_detailed_info(self, adapter_info):
        """
        从详细网卡信息更新IP配置显示
        
        Args:
            adapter_info (AdapterInfo): 网卡详细信息对象
        """
        try:
            # 构建IP配置数据字典
            config_data = {
                'ip_address': adapter_info.get_primary_ip() or '',
                'subnet_mask': adapter_info.get_primary_subnet_mask() or '',
                'gateway': adapter_info.gateway or '',
                'dns_primary': adapter_info.get_primary_dns() or '',
                'dns_secondary': adapter_info.get_secondary_dns() or ''
            }
            
            # 使用正确的批量更新方法
            self.network_config_tab.update_ip_config_inputs(config_data)
            
            # 更新IP信息展示区域
            self._update_ip_info_display(adapter_info)
            
            self.logger.debug(f"IP显示更新完成: {adapter_info.friendly_name}")
            
        except Exception as e:
            self.logger.error(f"更新IP显示失败: {str(e)}")
    
    def _update_extra_ip_list_display(self, adapter_info):
        """
        更新额外IP管理容器的IP列表显示
        
        Args:
            adapter_info (AdapterInfo): 网卡详细信息对象
        """
        try:
            extra_ips = adapter_info.get_extra_ips()
            ip_list = []
            
            for ip, mask in extra_ips:
                ip_info = f"{ip}/{mask}"
                ip_list.append(ip_info)
            
            # 更新额外IP列表
            self.network_config_tab.update_extra_ip_list(ip_list)
            
            self.logger.debug(f"额外IP列表已更新，共 {len(extra_ips)} 个")
            
        except Exception as e:
            self.logger.error(f"更新额外IP列表失败: {str(e)}")
    
    def _update_ip_info_display(self, adapter_info):
        """
        更新左侧IP信息展示区域显示
        
        参照源文件格式，完整展示网卡信息包括硬件信息、IP配置、IPv6等。
        
        Args:
            adapter_info (AdapterInfo): 网卡详细信息对象
        """
        try:
            from datetime import datetime
            info_lines = []
            
            # 基本硬件信息
            info_lines.append(f"网卡描述: {adapter_info.description}")
            info_lines.append(f"友好名称: {adapter_info.friendly_name}")
            info_lines.append(f"物理地址: {adapter_info.mac_address}")
            info_lines.append(f"连接状态: {'已连接' if adapter_info.is_connected else '未连接'}")
            
            # 接口类型和链路速度
            interface_type = getattr(adapter_info, 'interface_type', '以太网')
            info_lines.append(f"接口类型: {interface_type}")
            
            link_speed = getattr(adapter_info, 'link_speed', '未知')
            info_lines.append(f"链路速度: {link_speed}")
            info_lines.append("")
            
            # === IP配置信息 ===
            info_lines.append("=== IP配置信息 ===")
            primary_ip = adapter_info.get_primary_ip()
            if primary_ip:
                info_lines.append(f"主IP地址: {primary_ip}")
                
                primary_mask = adapter_info.get_primary_subnet_mask()
                if primary_mask:
                    info_lines.append(f"子网掩码: {primary_mask}")
                
                # 额外IPv4地址
                extra_ips = adapter_info.get_extra_ips()
                if extra_ips:
                    info_lines.append("")
                    info_lines.append("额外IPv4地址:")
                    for ip, mask in extra_ips:
                        info_lines.append(f"• {ip}/{mask}")
            else:
                info_lines.append("未配置IP地址")
            
            info_lines.append("")
            
            # === 网络配置 ===
            info_lines.append("=== 网络配置 ===")
            if adapter_info.gateway:
                info_lines.append(f"默认网关: {adapter_info.gateway}")
            
            dhcp_status = "启用" if adapter_info.dhcp_enabled else "禁用"
            info_lines.append(f"DHCP状态: {dhcp_status}")
            
            # DNS服务器
            primary_dns = adapter_info.get_primary_dns()
            if primary_dns:
                info_lines.append(f"主DNS服务器: {primary_dns}")
            
            secondary_dns = adapter_info.get_secondary_dns()
            if secondary_dns:
                info_lines.append(f"备用DNS服务器: {secondary_dns}")
            else:
                info_lines.append("备用DNS服务器: 未配置")
            
            info_lines.append("")
            
            # === IPv6配置信息 ===
            info_lines.append("=== IPv6配置信息 ===")
            if adapter_info.ipv6_addresses:
                # 主IPv6地址（通常是第一个）
                info_lines.append(f"主IPv6地址: {adapter_info.ipv6_addresses[0]}")
                
                # 额外IPv6地址
                if len(adapter_info.ipv6_addresses) > 1:
                    for ipv6_addr in adapter_info.ipv6_addresses[1:]:
                        info_lines.append(f"额外IPv6地址: {ipv6_addr}")
            else:
                info_lines.append("未配置IPv6地址")
            
            info_lines.append("")
            
            # 最后更新时间
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            info_lines.append(f"最后更新: {current_time}")
            
            # 更新显示
            formatted_text = "\n".join(info_lines)
            self.network_config_tab.update_ip_info_display(formatted_text)
            
            self.logger.debug(f"IP信息展示更新完成: {adapter_info.friendly_name}")
            
        except Exception as e:
            self.logger.error(f"更新IP信息展示失败: {str(e)}")
    
    def _on_adapter_refreshed(self, adapter_info):
        """
        处理网卡刷新完成信号的UI同步更新逻辑
        
        网卡刷新是获取网卡最新信息的操作，需要同步更新UI显示内容，
        确保用户看到的是最新的网卡状态和配置信息。
        
        核心功能：
        1. 更新当前网卡标签显示
        2. 根据最新状态更新状态徽章
        3. 刷新IP配置信息显示
        4. 刷新额外IP列表
        5. 显示刷新成功提示
        
        Args:
            adapter_info (AdapterInfo): 刷新后的网卡完整信息对象
        """
        try:
            # 更新当前网卡标签，确保显示最新的网卡标识
            # 直接传递友好名称，由Tab组件统一添加前缀
            self.network_config_tab.update_current_adapter_label(adapter_info.friendly_name)
            
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
            self.logger.info(f"刷新状态徽章 - 链路速度: '{link_speed}' (原始值: '{adapter_info.link_speed}') - 网卡: {adapter_info.friendly_name}")
            self.network_config_tab.update_status_badges(status_text, ip_mode, link_speed)
            self.logger.info(f"已调用update_status_badges(刷新) - 状态: {status_text}, IP模式: {ip_mode}, 链路速度: {link_speed}")
            
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
        处理服务层错误信号并显示错误弹窗
        
        作用说明：
        当网络配置操作失败时，这个方法负责向用户显示明确的错误信息弹窗。
        采用面向对象设计原则，将错误处理逻辑封装在独立方法中，
        确保用户能够及时了解操作失败的具体原因和解决建议。
        
        面向对象设计特点：
        - 单一职责：专门负责错误信息的UI显示
        - 封装性：将复杂的错误处理逻辑封装在方法内部
        - 用户体验：提供直观的错误信息和操作建议
        
        Args:
            error_title (str): 错误标题，用于弹窗标题栏显示
            error_message (str): 详细的错误信息，包含原因分析和解决建议
        """
        try:
            # 记录错误日志供开发者调试使用
            self.logger.error(f"{error_title}: {error_message}")
            
            # 显示用户友好的错误弹窗
            
            # 创建错误消息框，使用警告图标吸引用户注意
            error_box = QMessageBox(self)
            error_box.setIcon(QMessageBox.Critical)  # 使用严重错误图标
            error_box.setWindowTitle(f"操作失败 - {error_title}")
            error_box.setText(error_message)
            
            # 设置按钮文本为中文，提升用户体验
            error_box.setStandardButtons(QMessageBox.Ok)
            error_box.button(QMessageBox.Ok).setText("确定")
            
            # 显示弹窗并等待用户确认
            error_box.exec_()
            
        except Exception as e:
            self.logger.error(f"处理服务层错误信号失败: {str(e)}")
            # 如果弹窗显示失败，至少记录日志保证错误信息不丢失
    
    def _on_ip_config_applied(self, success_message):
        """
        处理IP配置应用成功信号并显示成功弹窗
        
        作用说明：
        当网络配置操作成功完成时，这个方法负责向用户显示明确的成功确认弹窗。
        采用面向对象设计原则，将成功反馈逻辑封装在独立方法中，
        确保用户能够及时了解操作结果并获得积极的成功反馈。
        
        面向对象设计特点：
        - 单一职责：专门负责成功信息的UI显示
        - 封装性：将成功处理逻辑封装在方法内部
        - 用户体验：提供直观的成功确认和操作结果展示
        
        Args:
            success_message (str): 服务层传递的成功消息，包含配置详情
        """
        try:
            # 记录IP配置成功的详细信息供开发者调试使用
            self.logger.info(f"IP配置应用成功: {success_message}")
            
            # 显示用户友好的成功弹窗
            
            # 创建成功消息框，使用信息图标表示正面反馈
            success_box = QMessageBox(self)
            success_box.setIcon(QMessageBox.Information)  # 使用信息图标
            success_box.setWindowTitle("配置成功")
            
            # 构建用户友好的成功消息内容
            success_text = f"✅ 网络配置已成功应用！\n\n{success_message}"
            success_text += "\n\n📝 提示：新的网络配置已生效，您可以在左侧信息面板中查看更新后的配置。"
            
            success_box.setText(success_text)
            
            # 设置按钮文本为中文，提升用户体验
            success_box.setStandardButtons(QMessageBox.Ok)
            success_box.button(QMessageBox.Ok).setText("确定")
            
            # 显示弹窗并等待用户确认
            success_box.exec_()
            
        except Exception as e:
            self.logger.error(f"处理IP配置成功信号失败: {str(e)}")
            # 如果弹窗显示失败，至少记录日志保证成功信息不丢失
    
    def _on_operation_progress(self, progress_message):
        """
        处理操作进度更新信号的UI反馈逻辑
        
        这个方法负责在长时间操作过程中向用户提供实时的进度反馈。
        采用面向对象的设计原则，将进度显示逻辑封装在独立方法中，
        提升用户体验和操作透明度。
        
        功能特点：
        1. 实时显示操作进度信息
        2. 让用户了解当前操作状态
        3. 为将来扩展进度条功能预留接口
        
        Args:
            progress_message (str): 服务层传递的进度消息文本
        """
        try:
            # 记录操作进度的详细信息
            self.logger.info(f"操作进度: {progress_message}")
            
            # 这里可以添加用户友好的进度提示逻辑
            # 例如进度条、状态栏消息、加载动画等
            # 当前版本通过日志记录，后续版本可扩展UI进度显示
            
        except Exception as e:
            self.logger.error(f"处理操作进度信号失败: {str(e)}")
    
    def _on_extra_ips_added(self, success_message):
        """
        处理批量额外IP添加成功信号并显示成功弹窗
        
        当服务层完成批量添加额外IP操作后，会发射此信号通知UI层显示操作结果。
        这个方法负责将服务层的成功消息转换为用户友好的界面反馈，采用统一的
        弹窗样式和交互逻辑，确保用户体验的一致性。
        
        设计原则：
        - 单一职责：专门处理批量添加IP的成功反馈
        - 用户友好：提供清晰的操作结果提示
        - 异常安全：确保弹窗显示失败不影响主程序运行
        - 日志记录：详细记录操作结果便于问题追踪
        
        Args:
            success_message (str): 服务层传递的成功消息文本
        """
        try:
            if not success_message:
                success_message = "批量添加额外IP成功"
            
            # 显示成功弹窗，使用统一的样式和交互逻辑
            # 弹窗会自动应用Claymorphism设计风格
            QMessageBox.information(
                self,
                "操作成功",
                success_message,
                QMessageBox.Ok
            )
            
            # 记录成功操作日志，便于运维监控和问题追踪
            self.logger.info(f"批量添加额外IP操作成功: {success_message}")
            
        except Exception as e:
            # 异常处理：确保弹窗显示失败不会影响主程序运行
            # 详细记录错误信息，便于开发人员快速定位问题
            self.logger.error(f"处理批量添加IP成功信号失败: {str(e)}")
            # 如果弹窗显示失败，至少记录日志保证成功信息不丢失
    
    def _on_extra_ips_removed(self, success_message):
        """
        处理批量额外IP删除成功信号并显示成功弹窗
        
        当服务层完成批量删除额外IP操作后，会发射此信号通知UI层显示操作结果。
        这个方法负责将服务层的成功消息转换为用户友好的界面反馈，采用统一的
        弹窗样式和交互逻辑，确保用户体验的一致性。
        
        设计原则：
        - 单一职责：专门处理批量删除IP的成功反馈
        - 用户友好：提供清晰的操作结果提示
        - 异常安全：确保弹窗显示失败不影响主程序运行
        - 日志记录：详细记录操作结果便于问题追踪
        
        Args:
            success_message (str): 服务层传递的成功消息文本
        """
        try:
            if not success_message:
                success_message = "批量删除额外IP成功"
            
            # 显示成功弹窗，使用统一的样式和交互逻辑
            # 弹窗会自动应用Claymorphism设计风格
            QMessageBox.information(
                self,
                "操作成功",
                success_message,
                QMessageBox.Ok
            )
            
            # 记录成功操作日志，便于运维监控和问题追踪
            self.logger.info(f"批量删除额外IP操作成功: {success_message}")
            
        except Exception as e:
            # 异常处理：确保弹窗显示失败不会影响主程序运行
            # 详细记录错误信息，便于开发人员快速定位问题
            self.logger.error(f"处理批量删除IP成功信号失败: {str(e)}")
            # 如果弹窗显示失败，至少记录日志保证成功信息不丢失
    
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
            # 智能状态显示：优先显示禁用状态，其次显示连接状态
            # 这确保了用户能够准确了解网卡的真实工作状态
            if not adapter_info.is_enabled:
                connection_status = "已禁用"
            elif adapter_info.is_connected:
                connection_status = "已连接"
            else:
                connection_status = "未连接"
            info_lines.append(f"连接状态: {connection_status}")
            
            info_lines.append(f"接口类型: {adapter_info.interface_type or '未知'}")
            
            # 链路速度显示：避免重复添加单位，因为link_speed已包含单位信息
            # 支持Gbps、Mbps等不同速度单位的正确显示
            if adapter_info.link_speed and adapter_info.link_speed != '未知':
                info_lines.append(f"链路速度: {adapter_info.link_speed}")
            else:
                info_lines.append("链路速度: 未知")
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
