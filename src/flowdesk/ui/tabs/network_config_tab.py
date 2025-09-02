#!/usr/bin/env python3
"""
网络配置Tab页面 - FlowDesk网络管理核心界面（重构版）

这个模块实现网络配置的用户界面，采用左右分栏布局设计：
- 左侧(300px)：网卡选择、IP信息展示、状态徽章、网卡操作按钮
- 右侧(340px)：IP配置输入、额外IP管理功能

重构后的架构设计：
1. 主容器类：负责布局组装和信号连接
2. 功能面板：AdapterInfoPanel（左侧）、IPConfigPanel（右侧）
3. 事件处理：NetworkConfigHandlers处理所有业务逻辑
4. 严格遵循UI四大铁律和面向对象设计原则
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout
from PyQt5.QtCore import pyqtSignal, QEvent

from .adapter_info_panel import AdapterInfoPanel
from .ip_config_panel import IPConfigPanel
from .network_config_handlers import NetworkConfigHandlers




class NetworkConfigTab(QWidget):
    """
    网络配置Tab页面主容器类 - 重构后的简洁版本
    
    重构设计原则：
    - 主容器负责面板组装和信号转发
    - 左右面板功能完全独立封装
    - 事件处理逻辑委托给专用处理器
    - 保持原有布局和信号接口不变
    """
    
    # 信号定义：与服务层通信的接口（保持不变）
    adapter_selected = pyqtSignal(str)  # 网卡选择变更信号
    refresh_adapters = pyqtSignal()     # 刷新网卡列表信号
    apply_ip_config = pyqtSignal(dict)  # 应用IP配置信号
    enable_adapter = pyqtSignal(str)    # 启用网卡信号
    disable_adapter = pyqtSignal(str)   # 禁用网卡信号
    set_static_ip = pyqtSignal(str)     # 设置静态IP信号
    set_dhcp = pyqtSignal(str)          # 设置DHCP信号
    copy_adapter_info = pyqtSignal()    # 复制网卡信息信号
    add_extra_ip = pyqtSignal(str, str) # 添加额外IP信号
    remove_extra_ip = pyqtSignal(list)  # 删除额外IP信号
    add_selected_ips = pyqtSignal(str, list)  # 添加选中的额外IP到网卡信号
    remove_selected_ips = pyqtSignal(str, list)  # 从网卡删除选中的额外IP信号

    def __init__(self, parent=None):
        """
        初始化网络配置Tab页面主容器
        
        重构后的初始化流程：
        1. 创建左右面板实例
        2. 设置主布局（保持原有尺寸）
        3. 初始化事件处理器
        4. 连接所有信号转发
        """
        super().__init__(parent)
        self.setObjectName("network_config_tab")
        
        # 设置最小尺寸保护，防止界面压缩变形
        self.setMinimumSize(648, 533)  # Tab页面可用空间
        
        # 初始化面板和处理器
        self._init_panels()
        self._setup_main_layout()
        self._init_handlers()
        self._connect_panel_signals()
        
        # 添加调试日志
        import logging
        self._logger = logging.getLogger(__name__)
        self._logger.debug("NetworkConfigTab重构版初始化完成")

    def _init_panels(self):
        """
        初始化左右功能面板
        
        创建AdapterInfoPanel和IPConfigPanel实例，
        保持原有的UI组件结构和objectName设置。
        """
        # 创建左侧网卡信息面板
        self.adapter_info_panel = AdapterInfoPanel()
        
        # 创建右侧IP配置面板
        self.ip_config_panel = IPConfigPanel()
        
        # 为了保持向后兼容，创建组件引用
        self._create_component_references()
    
    def _create_component_references(self):
        """
        创建组件引用以保持向后兼容性
        
        为了确保主窗口和其他模块能够正常访问UI组件，
        创建对面板内部组件的引用。
        """
        # 左侧面板组件引用
        self.adapter_combo = self.adapter_info_panel.adapter_combo
        self.refresh_btn = self.adapter_info_panel.refresh_btn
        self.ip_info_display = self.adapter_info_panel.ip_info_display
        self.connection_status_badge = self.adapter_info_panel.connection_status_badge
        self.ip_mode_badge = self.adapter_info_panel.ip_mode_badge
        self.link_speed_badge = self.adapter_info_panel.link_speed_badge
        self.enable_adapter_btn = self.adapter_info_panel.enable_adapter_btn
        self.disable_adapter_btn = self.adapter_info_panel.disable_adapter_btn
        self.set_static_btn = self.adapter_info_panel.set_static_btn
        self.set_dhcp_btn = self.adapter_info_panel.set_dhcp_btn
        self.copy_info_btn = self.adapter_info_panel.copy_info_btn
        
        # 右侧面板组件引用
        self.ip_address_input = self.ip_config_panel.ip_address_input
        self.subnet_mask_input = self.ip_config_panel.subnet_mask_input
        self.gateway_input = self.ip_config_panel.gateway_input
        self.primary_dns_input = self.ip_config_panel.primary_dns_input
        self.secondary_dns_input = self.ip_config_panel.secondary_dns_input
        self.current_adapter_label = self.ip_config_panel.current_adapter_label
        self.apply_config_btn = self.ip_config_panel.apply_config_btn
        self.extra_ip_list = self.ip_config_panel.extra_ip_list
        self.add_selected_ip_btn = self.ip_config_panel.add_selected_ip_btn
        self.remove_selected_ip_btn = self.ip_config_panel.remove_selected_ip_btn
        self.add_extra_ip_btn = self.ip_config_panel.add_extra_ip_btn
    
    def _setup_main_layout(self):
        """
        设置主容器布局（保持原有布局结构）
        
        采用水平布局，左右面板固定宽度，
        严格保持原有的300px+340px布局设计。
        """
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 8, 2, 8)  # 保持原有边距
        main_layout.setSpacing(0)   # 保持原有间距
        
        # 添加左右面板到主布局
        main_layout.addWidget(self.adapter_info_panel)
        main_layout.addWidget(self.ip_config_panel)
    
    def _init_handlers(self):
        """
        初始化事件处理器
        
        创建NetworkConfigHandlers实例，用于处理所有业务逻辑。
        """
        self.handlers = NetworkConfigHandlers()
    
    def _connect_panel_signals(self):
        """
        连接面板信号到主容器信号（信号转发）
        
        将各面板的内部信号转发到主容器的对外信号，
        保持原有的信号接口不变。
        """
        # 左侧面板信号转发
        self.adapter_info_panel.adapter_selected.connect(self.adapter_selected.emit)
        self.adapter_info_panel.refresh_adapters.connect(self.refresh_adapters.emit)
        self.adapter_info_panel.enable_adapter.connect(self.enable_adapter.emit)
        self.adapter_info_panel.disable_adapter.connect(self.disable_adapter.emit)
        self.adapter_info_panel.set_static_ip.connect(self.set_static_ip.emit)
        self.adapter_info_panel.set_dhcp.connect(self.set_dhcp.emit)
        self.adapter_info_panel.copy_adapter_info.connect(self.copy_adapter_info.emit)
        
        # 添加实时标签更新：网卡选择变更时立即更新当前网卡标签
        # 需要从完整描述映射到友好名称
        self.adapter_info_panel.adapter_combo.currentTextChanged.connect(
            self._update_current_adapter_label_from_description
        )
        
        # 存储网卡映射关系：完整描述 -> 友好名称
        self._adapter_name_mapping = {}
        
        # 右侧面板信号转发
        self.ip_config_panel.ip_config_applied.connect(self.apply_ip_config.emit)
        self.ip_config_panel.add_extra_ip.connect(
            lambda: self.handlers.show_add_ip_dialog(self)
        )
        self.ip_config_panel.add_selected_ips.connect(self.add_selected_ips.emit)
        self.ip_config_panel.remove_selected_ips.connect(self.remove_selected_ips.emit)

    # === 保持向后兼容的方法 ===
    
    def _on_adapter_combo_changed(self, text):
        """
        网卡选择下拉框变更事件处理方法（保持兼容）
        
        委托给左侧面板处理，保持原有的信号发射逻辑。
        """
        self._logger.debug(f"NetworkConfigTab._on_adapter_combo_changed调用 - 选择的网卡: '{text}'")
        self.adapter_selected.emit(text)
        self._logger.debug(f"已发射adapter_selected信号 - 网卡: '{text}'")

    # === 公共接口方法：供服务层调用更新UI ===

    def update_adapter_list(self, adapter_names):
        """
        更新网卡下拉框列表的核心UI数据同步方法
        
        委托给左侧面板处理，保持原有的更新逻辑。
        
        Args:
            adapter_names (list): 网卡名称列表
        """
        self.adapter_info_panel.update_adapter_list(adapter_names)

    def update_ip_info_display(self, formatted_info):
        """
        更新IP信息展示区域的核心显示逻辑
        
        委托给左侧面板处理，保持原有的显示逻辑。
        
        Args:
            formatted_info (str): 经过格式化处理的网卡详细信息文本
        """
        self.adapter_info_panel.update_ip_info_display(formatted_info)

    def update_status_badges(self, connection_status, ip_mode, link_speed):
        """
        更新多个状态徽章的批量显示方法
        
        委托给左侧面板处理，保持原有的状态更新逻辑。
        
        Args:
            connection_status (str): 连接状态描述
            ip_mode (str): IP配置模式
            link_speed (str): 网络链路速度
        """
        self.adapter_info_panel.update_status_badges(connection_status, ip_mode, link_speed)

    def update_ip_config_inputs(self, config_data):
        """
        更新IP配置输入框的显示内容
        
        委托给右侧面板处理，保持原有的输入框更新逻辑。
        
        Args:
            config_data (dict): IP配置数据字典
        """
        self.ip_config_panel.update_ip_config_inputs(config_data)

    def update_current_adapter_label(self, adapter_name):
        """
        更新当前网卡显示标签
        
        委托给右侧面板处理，保持原有的标签更新逻辑。
        
        Args:
            adapter_name (str): 网卡简称
        """
        self.ip_config_panel.update_current_adapter_label(adapter_name)

    def update_extra_ip_list(self, ip_list):
        """
        更新额外IP列表
        
        委托给右侧面板处理，保持原有的列表更新逻辑。
        
        Args:
            ip_list (list): 额外IP地址列表
        """
        self.ip_config_panel.update_extra_ip_list(ip_list)

    def _update_current_adapter_label_from_description(self, adapter_description):
        """
        根据网卡完整描述更新当前网卡标签为友好名称
        
        Args:
            adapter_description (str): 网卡完整描述（下拉框显示的内容）
        """
        # 从映射表获取友好名称
        friendly_name = self._adapter_name_mapping.get(adapter_description, adapter_description)
        self.ip_config_panel.update_current_adapter_label(friendly_name)

    def update_adapter_list_with_mapping(self, adapters):
        """
        更新网卡列表并建立描述到友好名称的映射
        
        Args:
            adapters (list): AdapterInfo对象列表
        """
        # 清空旧的映射关系
        self._adapter_name_mapping.clear()
        
        # 构建显示名称列表和映射关系
        adapter_display_names = []
        for adapter in adapters:
            # 下拉框显示完整描述
            display_name = adapter.name or adapter.description or adapter.friendly_name or "未知网卡"
            adapter_display_names.append(display_name)
            
            # 建立映射：完整描述 -> 友好名称
            self._adapter_name_mapping[display_name] = adapter.friendly_name or adapter.name or "未知"
        
        # 更新下拉框并传递映射关系
        self.adapter_info_panel.update_adapter_list(adapter_display_names, self._adapter_name_mapping)

    def eventFilter(self, obj, event):
        """
        事件过滤器方法 - 专门处理网络适配器下拉框的鼠标悬停事件（保持兼容）
        
        委托给左侧面板处理，保持原有的悬停提示功能。
        
        Args:
            obj: 事件源对象
            event: 事件对象
            
        Returns:
            bool: 事件是否被处理
        """
        return self.adapter_info_panel.eventFilter(obj, event)

