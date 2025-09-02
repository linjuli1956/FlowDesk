# -*- coding: utf-8 -*-
"""
网络UI协调专用服务模块

这个文件在FlowDesk网络管理架构中扮演"UI事件协调器"角色，专门负责网络服务与UI层之间的事件协调和状态同步。
它解决了复杂的UI更新时序、多服务协调和用户反馈机制的问题，通过统一的事件分发和状态管理确保UI与底层服务的一致性。
UI层依赖此服务获得统一的网络操作接口，其他服务通过此模块实现与界面的解耦通信。
该服务严格遵循单一职责原则，将UI协调逻辑完全独立封装。
"""

from typing import Optional, Dict, Any, List

from .network_service_base import NetworkServiceBase
from ...models.common import AggregatedAdapterInfo, PerformanceInfo


class NetworkUICoordinatorService(NetworkServiceBase):
    """
    网络UI协调服务
    
    专门负责网络服务与UI层协调的核心服务。
    此服务封装了复杂的UI更新逻辑，提供统一的事件分发和状态同步机制。
    
    主要功能：
    - 协调多个网络服务之间的数据共享和状态同步
    - 提供UI层统一的网络操作接口和事件订阅
    - 实现网卡信息刷新和缓存管理的协调机制
    - 处理复杂的UI更新时序和依赖关系
    
    输入输出：
    - 输入：UI层的操作请求和其他服务的状态变更事件
    - 输出：协调后的UI更新信号和统一的操作结果反馈
    
    设计模式：
    - 使用观察者模式实现服务间的松耦合通信
    - 采用中介者模式协调多个网络服务的交互
    - 通过代理模式为UI层提供简化的操作接口
    """
    
    def __init__(self, parent=None):
        """
        初始化网络UI协调服务
        
        Args:
            parent: PyQt父对象，用于内存管理
        """
        super().__init__(parent)
        self._log_operation_start("NetworkUICoordinatorService初始化")
        
        # 缓存当前选中的网卡信息，用于UI状态保持
        self._current_adapter_id = None
        self._current_adapter_info = None
        
        # 网络服务组件引用（在实际集成时注入）
        self._discovery_service = None
        self._info_service = None
        self._status_service = None
        self._performance_service = None
        self._ip_config_service = None
        self._extra_ip_service = None
    
    # region 服务依赖注入
    
    def set_discovery_service(self, service):
        """
        注入网卡发现服务
        
        Args:
            service: AdapterDiscoveryService实例
        """
        self._discovery_service = service
        self.logger.debug("已注入网卡发现服务")
    
    def set_info_service(self, service):
        """
        注入网卡信息服务
        
        Args:
            service: AdapterInfoService实例
        """
        self._info_service = service
        self.logger.debug("已注入网卡信息服务")
    
    def set_status_service(self, service):
        """
        注入网卡状态服务
        
        Args:
            service: AdapterStatusService实例
        """
        self._status_service = service
        self.logger.debug("已注入网卡状态服务")
    
    def set_performance_service(self, service):
        """
        注入网卡性能服务
        
        Args:
            service: AdapterPerformanceService实例
        """
        self._performance_service = service
        self.logger.debug("已注入网卡性能服务")
    
    def set_ip_config_service(self, service):
        """
        注入IP配置服务
        
        Args:
            service: IPConfigurationService实例
        """
        self._ip_config_service = service
        self.logger.debug("已注入IP配置服务")
    
    def set_extra_ip_service(self, service):
        """
        注入额外IP管理服务
        
        Args:
            service: ExtraIPManagementService实例
        """
        self._extra_ip_service = service
        self.logger.debug("已注入额外IP管理服务")
    
    # endregion
    
    # region 核心协调方法
    
    def refresh_adapters_list(self):
        """
        刷新网卡列表的协调方法
        
        这是UI协调服务的核心方法之一，负责协调网卡发现服务获取最新的网卡列表，
        并通过信号机制通知UI层更新界面显示。该方法封装了复杂的服务调用逻辑，
        为UI层提供简单统一的刷新接口。
        
        技术实现：
        - 调用AdapterDiscoveryService获取网卡列表
        - 更新额外IP管理服务的网卡缓存
        - 发射adapters_updated信号通知UI更新
        - 处理刷新过程中的异常情况
        
        设计原则：
        - 单一职责：专门负责网卡列表刷新的协调工作
        - 封装性：隐藏多个服务之间的复杂交互逻辑
        - 异常安全：确保刷新失败时不影响系统稳定性
        """
        try:
            self.operation_progress.emit("正在刷新网卡列表...")
            self._log_operation_start("刷新网卡列表")
            
            if not self._discovery_service:
                error_msg = "网卡发现服务未初始化"
                self.logger.error(error_msg)
                self.error_occurred.emit("服务错误", error_msg)
                return
            
            # 调用网卡发现服务获取最新网卡列表
            adapters = self._discovery_service.discover_all_adapters()
            
            if adapters is not None:
                # 更新额外IP管理服务的网卡缓存
                if self._extra_ip_service:
                    self._extra_ip_service.set_adapters_cache(adapters)
                
                # 发射网卡列表更新信号
                self.adapters_updated.emit(adapters)
                
                # 自动选择第一个网卡（已修复UI更新时的信号循环问题）
                if adapters and not self._current_adapter_id:
                    self.logger.debug(f"自动选择第一个网卡: {adapters[0].friendly_name}")
                    self.set_current_adapter(adapters[0].id)
                
                self._log_operation_success("刷新网卡列表", f"成功获取{len(adapters)}个网卡")
                self.operation_progress.emit("网卡列表刷新完成")
            else:
                error_msg = "获取网卡列表失败"
                self.logger.error(error_msg)
                self.error_occurred.emit("刷新失败", error_msg)
                
        except Exception as e:
            self._log_operation_error("刷新网卡列表", e)
            error_msg = f"刷新网卡列表时发生异常: {str(e)}"
            self.error_occurred.emit("系统异常", error_msg)
    
    def refresh_current_adapter(self):
        """
        刷新当前选中网卡信息的协调方法
        
        这个方法负责协调多个网络服务获取当前选中网卡的完整信息，
        包括基本信息、详细配置、状态和性能数据，并统一发射更新信号。
        
        技术实现：
        - 协调AdapterInfoService获取详细信息
        - 协调AdapterStatusService获取状态信息
        - 协调AdapterPerformanceService获取性能数据
        - 聚合所有信息并发射adapter_info_updated信号
        
        设计优势：
        - 数据一致性：确保UI显示的所有信息都是同一时刻的快照
        - 性能优化：批量获取信息，减少UI更新频率
        - 错误处理：部分信息获取失败时仍能显示可用数据
        """
        try:
            if not self._current_adapter_id:
                self.logger.warning("未选择当前网卡，无法刷新")
                return
                
            self.operation_progress.emit("正在刷新网卡信息...")
            self._log_operation_start("刷新当前网卡", adapter_id=self._current_adapter_id)
            
            # 获取基本信息（如果有发现服务）
            basic_info = None
            if self._discovery_service:
                basic_info = self._discovery_service.get_adapter_basic_info(self._current_adapter_id)
            
            # 获取详细信息（如果有信息服务）
            detailed_info = None
            if self._info_service:
                detailed_info = self._info_service.get_adapter_detailed_info(self._current_adapter_id)
            
            # 创建性能信息数据类
            performance_info = None
            if detailed_info and hasattr(detailed_info, 'link_speed'):
                link_speed = detailed_info.link_speed
                performance_info = PerformanceInfo(link_speed=link_speed)
                self.logger.debug(f"从详细信息中提取链路速度: {link_speed}")
            else:
                self.logger.warning("详细信息中没有链路速度信息")
            
            # 创建聚合信息数据类
            aggregated_info = AggregatedAdapterInfo(
                adapter_id=self._current_adapter_id,
                basic_info=basic_info,
                detailed_info=detailed_info,
                status_info=None,  # 状态信息已集成到详细信息中
                performance_info=performance_info
            )
            
            # 缓存当前网卡信息
            self._current_adapter_info = aggregated_info
            
            # 发射聚合信息更新信号
            self.logger.debug(f"发射adapter_info_updated信号 - 网卡ID: {aggregated_info.adapter_id}")
            self.adapter_info_updated.emit(aggregated_info)
            
            # 发射格式化的状态徽章信息（Service层负责业务逻辑）
            if detailed_info:
                badge_info = self._format_status_badges_for_ui(detailed_info)
                self.status_badges_updated.emit(*badge_info)
            
            # 如果有详细信息，处理IP配置和额外IP信息
            if detailed_info:
                # 创建IP配置数据
                from ...models import IPConfigInfo
                ip_config_data = IPConfigInfo(
                    adapter_id=self._current_adapter_id,
                    ip_address=detailed_info.get_primary_ip() or '',
                    subnet_mask=detailed_info.get_primary_subnet_mask() or '',
                    gateway=detailed_info.gateway or '',
                    dns_primary=detailed_info.dns_servers[0] if detailed_info.dns_servers else '',
                    dns_secondary=detailed_info.dns_servers[1] if len(detailed_info.dns_servers) > 1 else '',
                    dhcp_enabled=detailed_info.dhcp_enabled
                )
                
                # 发射IP配置信息更新信号，用于填充右侧输入框
                self.logger.debug("发射ip_info_updated信号，用于更新右侧输入框")
                self.ip_info_updated.emit(ip_config_data)
                
                # 发射额外IP列表更新信号，用于显示额外IP
                # 使用get_extra_ips()方法获取额外IP列表
                if hasattr(detailed_info, 'get_extra_ips'):
                    extra_ips = detailed_info.get_extra_ips()
                    if extra_ips:
                        # 格式化额外IP信息为UI显示格式
                        formatted_extra_ips = []
                        for ip, mask in extra_ips:
                            formatted_extra_ips.append(f"{ip}/{mask}")
                        
                        self.logger.debug(f"发射extra_ips_updated信号，共{len(extra_ips)}个额外IP: {formatted_extra_ips}")
                        self.extra_ips_updated.emit(formatted_extra_ips)
                    else:
                        # 如果没有额外IP，发射空列表清空显示
                        self.logger.debug("发射空的extra_ips_updated信号，清空额外IP显示")
                        self.extra_ips_updated.emit([])
                else:
                    # 如果没有get_extra_ips方法，发射空列表
                    self.logger.debug("AdapterInfo对象没有get_extra_ips方法，发射空列表")
                    self.extra_ips_updated.emit([])
            
            self._log_operation_success("刷新当前网卡", "信息更新完成")
            self.operation_progress.emit("网卡信息刷新完成")
            
        except Exception as e:
            self._log_operation_error("刷新当前网卡", e)
            error_msg = f"刷新网卡信息时发生异常: {str(e)}"
            self.error_occurred.emit("系统异常", error_msg)
    
    def copy_current_adapter_info(self):
        """
        复制当前网卡信息的协调方法
        
        将当前选中网卡的详细信息格式化为文本并复制到剪贴板。
        这个方法为UI层提供网卡信息复制功能的统一接口。
        """
        try:
            self._log_operation_start("复制网卡信息")
            
            # 调试信息：检查当前网卡信息状态
            self.logger.debug(f"当前网卡ID: {self._current_adapter_id}")
            self.logger.debug(f"当前网卡信息是否为空: {self._current_adapter_info is None}")
            if self._current_adapter_info:
                self.logger.debug(f"当前网卡信息类型: {type(self._current_adapter_info)}")
                self.logger.debug(f"当前网卡信息键: {list(self._current_adapter_info.keys()) if isinstance(self._current_adapter_info, dict) else 'Not a dict'}")
            
            if not self._current_adapter_info:
                self.logger.warning("未选择当前网卡，无法复制信息")
                self.error_occurred.emit("操作失败", "请先选择一个网卡")
                return
            
            # 格式化网卡信息为可读文本
            info_text = self._format_adapter_info_for_copy(self._current_adapter_info)
            
            # 调试信息：检查格式化后的文本
            self.logger.debug(f"格式化后的信息文本: {info_text[:200]}...")  # 只显示前200个字符
            
            # 发射复制完成信号，由UI层处理剪贴板操作
            self.network_info_copied.emit(info_text)
            self._log_operation_success("复制网卡信息", "信息已复制到剪贴板")
            
        except Exception as e:
            self._log_operation_error("复制网卡信息", e)
            error_msg = f"复制网卡信息时发生异常: {str(e)}"
            self.error_occurred.emit("系统异常", error_msg)
    
    def _format_adapter_info_for_copy(self, adapter_info) -> str:
        """
        格式化网卡信息为可复制的文本格式
        
        与容器内展示的格式完全一致，使用相同的显示逻辑。
        
        Args:
            adapter_info: 聚合的网卡信息字典，包含 basic_info, detailed_info 等子对象
            
        Returns:
            str: 格式化的网卡信息文本，与容器内展示一致
        """
        if not adapter_info:
            return "无网卡信息"
            
        # 从聚合信息中提取 detailed_info
        detailed_info = adapter_info.get('detailed_info') if isinstance(adapter_info, dict) else getattr(adapter_info, 'detailed_info', None)
        
        if not detailed_info:
            return "网卡详细信息不可用"
        
        # Service层负责格式化业务逻辑，避免UI层依赖
        try:
            return self._format_adapter_info_for_display(detailed_info)
        except Exception as e:
            self.logger.error(f"格式化网卡信息失败: {str(e)}")
            return "网卡信息格式化失败"
    
    def format_adapter_info_for_display(self, adapter_info):
        """
        公共方法：格式化网卡信息用于UI显示
        
        供UI层调用的公共接口，将网卡信息格式化为显示文本。
        
        Args:
            adapter_info: AdapterInfo对象或聚合信息字典
            
        Returns:
            str: 格式化后的显示文本
        """
        try:
            # 从聚合信息中提取详细信息
            if isinstance(adapter_info, dict):
                detailed_info = adapter_info.get('detailed_info')
            else:
                detailed_info = getattr(adapter_info, 'detailed_info', adapter_info)
            
            if not detailed_info:
                return "网卡信息不可用"
            
            return self._format_adapter_info_for_display(detailed_info)
            
        except Exception as e:
            self.logger.error(f"格式化网卡信息失败: {str(e)}")
            return "网卡信息格式化失败"
    
    def _format_adapter_info_for_display(self, adapter_info):
        """
        格式化网卡信息用于UI显示
        
        将AdapterInfo对象格式化为用户友好的文本格式，
        供UI层在信息展示区域显示使用。
        
        Args:
            adapter_info: AdapterInfo对象
            
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
            if not adapter_info.is_enabled:
                connection_status = "已禁用"
            elif adapter_info.is_connected:
                connection_status = "已连接"
            else:
                connection_status = "未连接"
            info_lines.append(f"连接状态: {connection_status}")
            
            info_lines.append(f"接口类型: {adapter_info.interface_type or '未知'}")
            
            # 链路速度显示
            if adapter_info.link_speed and adapter_info.link_speed != '未知':
                info_lines.append(f"链路速度: {adapter_info.link_speed}")
            else:
                info_lines.append("链路速度: 未知")
            info_lines.append("")
            
            # IP配置信息
            info_lines.append("=== IP配置信息 ===")
            primary_ip = adapter_info.get_primary_ip()
            primary_mask = adapter_info.get_primary_subnet_mask()
            if primary_ip:
                info_lines.append(f"主IP地址: {primary_ip}")
                info_lines.append(f"子网掩码: {primary_mask}")
            else:
                info_lines.append("主IP地址: 未配置")
            
            # 额外IPv4地址
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
            
            # IPv6地址信息
            if adapter_info.ipv6_addresses:
                info_lines.append("")
                info_lines.append("=== IPv6配置信息 ===")
                for i, ipv6_addr in enumerate(adapter_info.ipv6_addresses):
                    if i == 0:
                        info_lines.append(f"主IPv6地址: {ipv6_addr}")
                    else:
                        info_lines.append(f"IPv6地址{ i + 1 }: {ipv6_addr}")
            
            # 添加时间戳
            info_lines.append("")
            info_lines.append(f"最后更新: {adapter_info.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
            
            return "\n".join(info_lines)
            
        except Exception as e:
            self.logger.error(f"格式化网卡信息失败: {str(e)}")
            # 备用方案：简化的格式化
            def safe_get(obj, attr, default='未知'):
                if obj is None:
                    return default
                if isinstance(obj, dict):
                    return obj.get(attr, default)
                else:
                    return getattr(obj, attr, default)
            
            info_lines = [
                f"网卡描述: {safe_get(detailed_info, 'description')}",
                f"友好名称: {safe_get(detailed_info, 'friendly_name')}",
                f"物理地址: {safe_get(detailed_info, 'mac_address')}",
                f"连接状态: {safe_get(detailed_info, 'status')}",
                f"接口类型: {safe_get(detailed_info, 'interface_type')}",
                f"链路速度: {safe_get(detailed_info, 'link_speed')}"
            ]
            
            return "\n".join(info_lines)
    
    def _format_status_badges_for_ui(self, adapter_info):
        """
        格式化状态徽章信息供UI层显示
        
        Service层负责所有业务逻辑判断，包括Emoji图标选择和状态属性映射。
        UI层只需要接收格式化好的显示文本和属性值。
        
        Args:
            adapter_info: AdapterInfo对象
            
        Returns:
            tuple: (连接显示文本, 连接属性, IP模式显示文本, IP模式属性, 链路速度显示文本)
        """
        # 连接状态格式化（Service层业务逻辑）
        if not adapter_info.is_enabled:
            connection_display = "🚫 已禁用"
            connection_attr = "disabled"
        elif adapter_info.is_connected:
            connection_display = "🔌 已连接"
            connection_attr = "connected"
        else:
            connection_display = "🔌 未连接"
            connection_attr = "disconnected"
        
        # IP模式格式化（Service层业务逻辑）
        if adapter_info.dhcp_enabled:
            ip_mode_display = "🔄 DHCP"
            ip_mode_attr = "dhcp"
        else:
            ip_mode_display = "🔧 静态IP"
            ip_mode_attr = "static"
        
        # 链路速度格式化（Service层业务逻辑）
        if adapter_info.link_speed and adapter_info.link_speed != "未知":
            link_speed_display = f"⚡ {adapter_info.link_speed}"
        else:
            link_speed_display = "⚡ 未知"
        
        return (connection_display, connection_attr, ip_mode_display, ip_mode_attr, link_speed_display)
    
    def set_current_adapter(self, adapter_id: str):
        """
        设置当前选中的网卡并刷新其信息
        
        这个方法负责响应UI层的网卡选择事件，设置当前活动的网卡，
        并触发该网卡详细信息的获取和显示更新。
        
        Args:
            adapter_id (str): 选中的网卡GUID标识符
        """
        try:
            self._log_operation_start("设置当前网卡", adapter_id=adapter_id)
            
            # 更新当前网卡ID
            self._current_adapter_id = adapter_id
            
            # 立即刷新选中网卡的信息
            self.refresh_current_adapter()
            
            self._log_operation_success("设置当前网卡", f"已切换到网卡: {adapter_id}")
            
        except Exception as e:
            self._log_operation_error("设置当前网卡", e)
            error_msg = f"设置当前网卡时发生异常: {str(e)}"
            self.error_occurred.emit("系统异常", error_msg)
    
    # endregion
    
    # region IP配置协调方法
    
    def apply_ip_configuration(self, adapter_id: str, ip_address: str, subnet_mask: str, 
                             gateway: str = '', primary_dns: str = '', secondary_dns: str = ''):
        """
        协调IP配置应用的统一接口方法
        
        这个方法是IP配置功能的协调入口，负责调用IPConfigurationService
        进行实际的配置应用，并在配置完成后刷新网卡信息以更新UI显示。
        
        Args:
            adapter_id (str): 目标网卡的GUID标识符
            ip_address (str): 要设置的IP地址
            subnet_mask (str): 子网掩码
            gateway (str, optional): 默认网关地址
            primary_dns (str, optional): 主DNS服务器地址
            secondary_dns (str, optional): 辅助DNS服务器地址
        """
        try:
            self._log_operation_start("协调IP配置应用", adapter_id=adapter_id)
            
            if not self._ip_config_service:
                error_msg = "IP配置服务未初始化"
                self.logger.error(error_msg)
                self.error_occurred.emit("服务错误", error_msg)
                return
            
            # 调用IP配置服务执行实际配置
            success = self._ip_config_service.apply_ip_config(
                adapter_id, ip_address, subnet_mask, gateway, primary_dns, secondary_dns
            )
            
            if success:
                # 配置成功后刷新网卡信息
                self.refresh_current_adapter()
                self._log_operation_success("协调IP配置应用", "配置应用成功并已刷新信息")
            else:
                self.logger.error("IP配置应用失败")
                
        except Exception as e:
            self._log_operation_error("协调IP配置应用", e)
            error_msg = f"协调IP配置应用时发生异常: {str(e)}"
            self.error_occurred.emit("系统异常", error_msg)
    
    def add_extra_ips(self, adapter_name: str, ip_configs: List[str]):
        """
        协调批量添加额外IP的统一接口方法
        
        Args:
            adapter_name (str): 目标网卡的友好名称
            ip_configs (List[str]): IP配置列表
        """
        try:
            self._log_operation_start("协调批量添加额外IP", adapter_name=adapter_name)
            
            if not self._extra_ip_service:
                error_msg = "额外IP管理服务未初始化"
                self.logger.error(error_msg)
                self.error_occurred.emit("服务错误", error_msg)
                return
            
            # 调用额外IP管理服务执行批量添加
            self._extra_ip_service.add_selected_extra_ips(adapter_name, ip_configs)
            
            # 操作完成后刷新当前网卡信息
            self.refresh_current_adapter()
            self._log_operation_success("协调批量添加额外IP", "操作完成并已刷新信息")
            
        except Exception as e:
            self._log_operation_error("协调批量添加额外IP", e)
            error_msg = f"协调批量添加额外IP时发生异常: {str(e)}"
            self.error_occurred.emit("系统异常", error_msg)
    
    def add_selected_extra_ips(self, adapter_name: str, ip_configs: List[str]):
        """
        协调批量添加选中额外IP的接口方法（兼容性别名）
        
        这是add_extra_ips方法的别名，用于保持与UI层信号连接的兼容性。
        
        Args:
            adapter_name (str): 目标网卡的友好名称
            ip_configs (List[str]): IP配置列表
        """
        # 直接委托给add_extra_ips方法
        self.add_extra_ips(adapter_name, ip_configs)
    
    def remove_extra_ips(self, adapter_name: str, ip_configs: List[str]):
        """
        协调批量删除额外IP的统一接口方法
        
        Args:
            adapter_name (str): 目标网卡的友好名称
            ip_configs (List[str]): 待删除的IP配置列表
        """
        try:
            self._log_operation_start("协调批量删除额外IP", adapter_name=adapter_name)
            
            if not self._extra_ip_service:
                error_msg = "额外IP管理服务未初始化"
                self.logger.error(error_msg)
                self.error_occurred.emit("服务错误", error_msg)
                return
            
            # 调用额外IP管理服务执行批量删除
            self._extra_ip_service.remove_selected_extra_ips(adapter_name, ip_configs)
            
            # 操作完成后刷新当前网卡信息
            self.refresh_current_adapter()
            self._log_operation_success("协调批量删除额外IP", "操作完成并已刷新信息")
            
        except Exception as e:
            self._log_operation_error("协调批量删除额外IP", e)
            error_msg = f"协调批量删除额外IP时发生异常: {str(e)}"
            self.error_occurred.emit("系统异常", error_msg)
    
    def remove_selected_extra_ips(self, adapter_name: str, ip_configs: List[str]):
        """
        协调批量删除选中额外IP的接口方法（兼容性别名）
        
        这是remove_extra_ips方法的别名，用于保持与UI层信号连接的兼容性。
        
        Args:
            adapter_name (str): 目标网卡的友好名称
            ip_configs (List[str]): 待删除的IP配置列表
        """
        # 直接委托给remove_extra_ips方法
        self.remove_extra_ips(adapter_name, ip_configs)
    
    # endregion
    
    # region 状态查询方法
    
    def get_current_adapter_id(self) -> Optional[str]:
        """
        获取当前选中的网卡ID
        
        Returns:
            Optional[str]: 当前网卡ID，未选择时返回None
        """
        return self._current_adapter_id
    
    def get_current_adapter_info(self) -> Optional[Dict[str, Any]]:
        """
        获取当前选中网卡的缓存信息
        
        Returns:
            Optional[Dict[str, Any]]: 当前网卡的聚合信息，未选择时返回None
        """
        return self._current_adapter_info
    
    def is_service_ready(self) -> bool:
        """
        检查协调服务是否已就绪
        
        Returns:
            bool: 所有必要的服务都已注入时返回True
        """
        required_services = [
            self._discovery_service,
            self._info_service,
            self._status_service
        ]
        
        return all(service is not None for service in required_services)
    
    def get_service_status(self) -> Dict[str, bool]:
        """
        获取各个服务的注入状态
        
        Returns:
            Dict[str, bool]: 各服务的可用状态字典
        """
        return {
            'discovery_service': self._discovery_service is not None,
            'info_service': self._info_service is not None,
            'status_service': self._status_service is not None,
            'performance_service': self._performance_service is not None,
            'ip_config_service': self._ip_config_service is not None,
            'extra_ip_service': self._extra_ip_service is not None
        }
    
    # endregion
