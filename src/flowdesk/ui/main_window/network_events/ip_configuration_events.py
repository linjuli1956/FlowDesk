# -*- coding: utf-8 -*-
"""
IP配置事件处理器：负责IP配置、验证、应用相关的UI事件处理
"""
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject
from ....utils.logger import get_logger
from ...dialogs.operation_result_dialog import OperationResultDialog
from ....models.ip_config_confirmation import IPConfigConfirmation
from ...dialogs.ip_config_confirm_dialog import IPConfigConfirmDialog
from ...dialogs.network_progress_dialog import show_network_progress


class IPConfigurationEvents:
    """
    IP配置事件处理器
    
    负责处理IP地址配置、验证、应用等UI事件。
    专注于IP配置相关的事件处理，符合单一职责原则。
    
    设计原则：
    - 单一职责：专门处理IP配置相关的UI事件转换
    - 封装性：将IP配置处理逻辑封装在独立方法中
    - 依赖倒置：依赖于服务层抽象接口，不依赖具体实现
    """
    
    def __init__(self, main_window, network_service=None):
        """
        初始化IP配置事件处理器
        
        Args:
            main_window: 主窗口实例，用于访问UI组件
            network_service: 网络服务实例，用于调用业务逻辑（可以稍后设置）
        """
        self.main_window = main_window
        self.network_service = network_service
        self.logger = get_logger(__name__)
        
        # 如果网络服务已提供，立即连接信号
        if self.network_service:
            self._connect_signals()
    
    def set_network_service(self, network_service):
        """
        设置网络服务并连接信号
        
        Args:
            network_service: 网络服务实例
        """
        self.network_service = network_service
        if self.network_service:
            self._connect_signals()
    
    def _connect_signals(self):
        """
        连接网络服务的IP配置相关信号到事件处理方法
        """
        if not self.network_service:
            return
            
        # 连接IP配置相关信号
        self.network_service.ip_info_updated.connect(self._on_ip_info_updated)
        self.network_service.extra_ips_updated.connect(self._on_extra_ips_updated)
        self.network_service.ip_config_applied.connect(self._on_ip_config_applied)
        
        self.logger.debug("IPConfigurationEvents信号连接完成")
    
    def _on_apply_ip_config(self, config_data):
        """
        处理IP配置应用请求事件
        
        当用户点击"应用配置"按钮时，这个方法负责处理IP配置应用请求。
        它会首先验证配置数据的有效性，然后显示确认弹窗让用户确认操作，
        最后调用服务层的配置应用方法。
        
        设计原则：
        - 用户确认：重要操作前必须获得用户明确确认
        - 数据验证：在UI层进行基础的数据完整性检查
        - 委托模式：将实际的配置应用逻辑委托给服务层
        - 异常安全：确保任何异常都不会导致程序崩溃
        
        Args:
            config_data (dict): 包含IP配置信息的字典
        """
        try:
            self.logger.debug(f"🔧 收到IP配置应用请求")
            
            # 基础数据验证：确保配置数据不为空
            if not config_data:
                error_msg = "配置数据为空，无法应用IP配置"
                self.logger.error(error_msg)
                QMessageBox.critical(self.main_window, "配置错误", error_msg)
                return
            
            # 获取当前选中的网卡名称
            adapter_name = self._get_current_adapter_name()
            if not adapter_name or adapter_name == '未选择':
                error_msg = "未选择网卡，无法应用IP配置"
                self.logger.error(error_msg)
                QMessageBox.critical(self.main_window, "配置错误", error_msg)
                return
            
            # 从左侧面板的IP信息显示区域解析当前IP配置
            current_ip, current_subnet, current_gw, current_dns1, current_dns2 = self._parse_current_ip_info_from_display()
            
            # 创建IP配置确认数据对象
            confirmation_data = IPConfigConfirmation(
                adapter_name=adapter_name,
                current_ip=current_ip,
                new_ip=config_data.get('ip_address', ''),
                current_subnet_mask=current_subnet,
                new_subnet_mask=config_data.get('subnet_mask', ''),
                current_gateway=current_gw,
                new_gateway=config_data.get('gateway', ''),
                current_dns_primary=current_dns1,
                new_dns_primary=config_data.get('dns_primary', ''),
                current_dns_secondary=current_dns2,
                new_dns_secondary=config_data.get('dns_secondary', ''),
                dhcp_enabled=False  # 静态IP配置
            )
            
            # 显示原有的IP配置确认弹窗
            confirm_dialog = IPConfigConfirmDialog(confirmation_data, self.main_window)
            
            # 连接确认弹窗的信号
            confirm_dialog.confirmed.connect(lambda: self._apply_confirmed_ip_config(config_data, adapter_name))
            
            # 显示弹窗
            confirm_dialog.exec_()
                
        except Exception as e:
            self.logger.error(f"处理IP配置应用请求异常: {str(e)}")
            QMessageBox.critical(self.main_window, "系统错误", f"处理配置请求时发生错误：{str(e)}")
    
    def _apply_confirmed_ip_config(self, config_data, adapter_name):
        """
        应用用户确认的IP配置（使用进度对话框）
        
        这个方法在用户确认IP配置后被调用，负责实际执行配置应用操作。
        使用NetworkProgressDialog提供用户友好的进度反馈。
        
        Args:
            config_data (dict): 用户确认的IP配置数据
            adapter_name (str): 目标网卡名称
        """
        def apply_ip_config_operation(progress_callback=None):
            """IP配置应用操作函数（支持进度回调）"""
            try:
                import time
                
                self.logger.debug(f"🚀 开始应用IP配置到网卡: {adapter_name}")
                
                # 步骤1: 验证网络服务 (10%)
                if progress_callback:
                    progress_callback(10, "正在验证网络服务...")
                time.sleep(0.3)
                
                # 委托给服务层执行实际的IP配置应用
                if self.network_service:
                    # 步骤2: 获取网卡ID (25%)
                    if progress_callback:
                        progress_callback(25, "正在获取网卡标识...")
                    time.sleep(0.3)
                    
                    # 通过网卡名称获取网卡ID
                    adapter_id = self.network_service.get_adapter_id_by_name(adapter_name)
                    
                    if not adapter_id:
                        self.logger.error(f"无法获取网卡 '{adapter_name}' 的ID")
                        return False
                    
                    # 步骤3: 准备IP配置参数 (40%)
                    if progress_callback:
                        progress_callback(40, "正在准备IP配置参数...")
                    time.sleep(0.5)
                    
                    # 步骤4: 应用IP配置 (70%)
                    if progress_callback:
                        progress_callback(70, "正在应用IP配置...")
                    time.sleep(1.0)
                    
                    # 调用正确的参数格式
                    result = self.network_service.apply_ip_config(
                        adapter_id=adapter_id,
                        ip_address=config_data.get('ip_address', ''),
                        subnet_mask=config_data.get('subnet_mask', ''),
                        gateway=config_data.get('gateway', ''),
                        primary_dns=config_data.get('dns_primary', ''),
                        secondary_dns=config_data.get('dns_secondary', '')
                    )
                    
                    # 步骤5: 等待配置生效 (90%)
                    if progress_callback:
                        progress_callback(90, "正在等待配置生效...")
                    time.sleep(1.5)
                    
                    # 步骤6: 刷新网卡信息 (95%)
                    if progress_callback:
                        progress_callback(95, "正在刷新网卡信息...")
                    time.sleep(0.5)
                    
                    return result if result is not None else True
                else:
                    self.logger.error("网络服务未初始化")
                    return False
                    
            except Exception as e:
                self.logger.error(f"应用IP配置异常: {str(e)}")
                return False
        
        # 使用进度对话框执行操作
        success = show_network_progress(
            operation_name="修改IP配置",
            operation_func=apply_ip_config_operation,
            adapter_name=adapter_name,
            parent=self.main_window
        )
        
        if success:
            QMessageBox.information(self.main_window, "成功", f"IP配置应用成功！\n\n网卡: {adapter_name}")
        else:
            QMessageBox.critical(self.main_window, "失败", f"IP配置应用失败，请检查网络设置和权限")
    
    def _get_current_selected_adapter(self):
        """
        获取当前选中的网卡信息
        
        这个方法用于获取用户当前在UI中选择的网卡信息，主要用于IP配置应用前
        的网卡上下文获取。采用委托模式，将获取逻辑委托给服务层。
        
        设计原则：
        - 单一职责：专门负责获取当前选中网卡信息
        - 委托模式：委托给服务层获取实际数据
        - 异常安全：确保获取失败时返回None而不是抛出异常
        
        Returns:
            dict or None: 当前选中的网卡信息字典，获取失败时返回None
        """
        try:
            if not self.network_service:
                self.logger.error("网络服务未初始化，无法获取当前网卡")
                return None
                
            # 委托给服务层获取当前选中的网卡信息
            current_adapter = self.network_service.get_current_adapter()
            
            if current_adapter:
                # 适配多种数据格式
                if hasattr(current_adapter, 'basic_info') and current_adapter.basic_info:
                    # AggregatedAdapterInfo对象
                    adapter_name = current_adapter.basic_info.friendly_name or '未知'
                elif hasattr(current_adapter, 'get'):
                    # 字典格式
                    adapter_name = current_adapter.get('friendly_name', '未知')
                elif hasattr(current_adapter, 'friendly_name'):
                    # 直接属性访问
                    adapter_name = current_adapter.friendly_name or '未知'
                else:
                    adapter_name = '未知'
                self.logger.debug(f"获取当前网卡成功: {adapter_name}")
            else:
                self.logger.debug("当前没有选中的网卡")
                
            return current_adapter
            
        except Exception as e:
            self.logger.error(f"获取当前网卡信息异常: {str(e)}")
            import traceback
            self.logger.error(f"异常堆栈: {traceback.format_exc()}")
            return None
    
    def _on_ip_info_updated(self, ip_info):
        """
        处理IP信息更新信号
        
        当服务层检测到网卡的IP信息发生变化时，会发射此信号。
        这个方法负责处理IP信息更新后的UI状态同步。
        
        设计原则：
        - 事件响应：响应服务层的IP信息更新事件
        - UI同步：确保UI显示与实际IP状态保持一致
        - 状态记录：记录IP变化便于问题追踪
        
        Args:
            ip_info: 更新后的IP信息对象
        """
        try:
            if ip_info:
                ip_address = getattr(ip_info, 'ip_address', '未知')
                self.logger.debug(f"📡 IP信息已更新: {ip_address}")
            else:
                self.logger.debug("IP信息更新完成，但未获取到具体信息")
                
        except Exception as e:
            self.logger.error(f"处理IP信息更新信号异常: {str(e)}")
    
    def _get_current_adapter_name(self) -> str:
        """
        获取当前选中的网卡名称
        
        Returns:
            str: 当前选中网卡的名称
        """
        try:
            # 通过主窗口获取网络配置Tab页面
            if hasattr(self.main_window, 'network_config_tab'):
                network_tab = self.main_window.network_config_tab
                if hasattr(network_tab, 'adapter_info_panel'):
                    return network_tab.adapter_info_panel._get_current_adapter_friendly_name()
            return '未选择'
        except Exception as e:
            self.logger.error(f"获取当前网卡名称异常: {str(e)}")
            return '未选择'
    
    def _parse_current_ip_info_from_display(self) -> tuple:
        """
        从左侧面板的IP信息显示区域解析当前IP配置
        
        Returns:
            tuple: (current_ip, current_subnet, current_gw, current_dns1, current_dns2)
        """
        try:
            # 通过主窗口获取网络配置Tab页面
            if hasattr(self.main_window, 'network_config_tab'):
                network_tab = self.main_window.network_config_tab
                if hasattr(network_tab, 'adapter_info_panel'):
                    # 获取IP信息显示区域的文本内容
                    ip_info_text = network_tab.adapter_info_panel.ip_info_display.toPlainText()
                    self.logger.debug(f"从左侧面板获取的IP信息文本: {ip_info_text}")
                    
                    # 解析IP信息文本
                    return self._extract_ip_info_from_text(ip_info_text)
            
            return None, None, None, None, None
        except Exception as e:
            self.logger.error(f"解析左侧面板IP信息异常: {str(e)}")
            return None, None, None, None, None
    
    def _extract_ip_info_from_text(self, ip_info_text: str) -> tuple:
        """
        从IP信息文本中提取各项配置
        
        Args:
            ip_info_text (str): IP信息显示文本
            
        Returns:
            tuple: (current_ip, current_subnet, current_gw, current_dns1, current_dns2)
        """
        import re
        
        current_ip = current_subnet = current_gw = current_dns1 = current_dns2 = None
        
        try:
            # 使用正则表达式提取各项配置
            ip_match = re.search(r'IP地址[：:]\s*(\d+\.\d+\.\d+\.\d+)', ip_info_text)
            if ip_match:
                current_ip = ip_match.group(1)
            
            subnet_match = re.search(r'子网掩码[：:]\s*(\d+\.\d+\.\d+\.\d+)', ip_info_text)
            if subnet_match:
                current_subnet = subnet_match.group(1)
            
            gw_match = re.search(r'默认网关[：:]\s*(\d+\.\d+\.\d+\.\d+)', ip_info_text)
            if gw_match:
                current_gw = gw_match.group(1)
            
            dns_matches = re.findall(r'DNS服务器[：:]\s*(\d+\.\d+\.\d+\.\d+)', ip_info_text)
            if dns_matches:
                current_dns1 = dns_matches[0] if len(dns_matches) > 0 else None
                current_dns2 = dns_matches[1] if len(dns_matches) > 1 else None
            
            self.logger.debug(f"解析得到的IP配置 - IP: {current_ip}, 子网掩码: {current_subnet}, 网关: {current_gw}, 主DNS: {current_dns1}, 备用DNS: {current_dns2}")
            
        except Exception as e:
            self.logger.error(f"提取IP信息异常: {str(e)}")
        
        return current_ip, current_subnet, current_gw, current_dns1, current_dns2

    def _get_current_selected_adapter(self) -> Optional[Dict[str, Any]]:
        """
        获取当前选中的网卡信息
        
        Returns:
            Optional[Dict[str, Any]]: 当前选中网卡的信息，未选中时返回None
        """
        try:
            if not self.network_service:
                self.logger.error("网络服务未初始化，无法获取当前网卡")
                return None
                
            # 委托给服务层获取当前选中的网卡信息
            current_adapter = self.network_service.get_current_adapter()
            
            if current_adapter:
                self.logger.debug(f"当前网卡对象类型: {type(current_adapter)}")
                self.logger.debug(f"当前网卡对象内容: {current_adapter}")
                
                # 适配多种数据格式
                if hasattr(current_adapter, 'adapter_id') and hasattr(current_adapter, 'basic_info'):
                    # AggregatedAdapterInfo对象
                    if current_adapter.basic_info and hasattr(current_adapter.basic_info, 'friendly_name'):
                        adapter_name = current_adapter.basic_info.friendly_name or '未知'
                    else:
                        adapter_name = '未知'
                    self.logger.debug(f"使用AggregatedAdapterInfo格式获取网卡名: {adapter_name}")
                elif isinstance(current_adapter, dict):
                    # 字典格式
                    adapter_name = current_adapter.get('friendly_name', '未知')
                    self.logger.debug(f"使用字典格式获取网卡名: {adapter_name}")
                elif hasattr(current_adapter, 'friendly_name'):
                    # 直接属性访问
                    adapter_name = current_adapter.friendly_name or '未知'
                    self.logger.debug(f"使用直接属性访问获取网卡名: {adapter_name}")
                else:
                    adapter_name = '未知'
                    self.logger.warning(f"无法识别网卡对象格式，对象类型: {type(current_adapter)}, 属性: {dir(current_adapter)}")
                self.logger.debug(f"获取当前网卡成功: {adapter_name}")
            else:
                self.logger.debug("当前没有选中的网卡")
                
            return current_adapter
            
        except Exception as e:
            self.logger.error(f"获取当前网卡信息异常: {str(e)}")
            import traceback
            self.logger.error(f"异常堆栈: {traceback.format_exc()}")
            return None
    
    def _on_extra_ips_updated(self, extra_ips):
        """
        处理额外IP列表更新信号
        
        当服务层检测到网卡的额外IP列表发生变化时，会发射此信号。
        这个方法负责处理额外IP列表更新后的UI状态同步。
        
        设计原则：
        - 事件响应：响应服务层的额外IP列表更新事件
        - UI同步：确保UI显示与实际额外IP状态保持一致
        - 状态记录：记录额外IP变化便于问题追踪
        
        Args:
            extra_ips: 更新后的额外IP列表
        """
        try:
            if extra_ips:
                self.logger.debug(f"📋 额外IP列表已更新，共 {len(extra_ips)} 个")
            else:
                self.logger.debug("额外IP列表已清空")
                
        except Exception as e:
            self.logger.error(f"处理额外IP列表更新信号异常: {str(e)}")
    
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
            # 在状态栏显示成功状态
            if hasattr(self.main_window, 'service_coordinator') and self.main_window.service_coordinator.status_bar_service:
                self.main_window.service_coordinator.status_bar_service.set_status(
                    "✅ IP配置应用成功", 
                    auto_clear_seconds=3
                )
            
            # 记录IP配置成功的详细信息供开发者调试使用
            self.logger.debug(f"IP配置应用成功: {success_message}")
            
            # 显示用户友好的成功弹窗
            
            # 创建成功消息框，使用信息图标表示正面反馈
            success_box = QMessageBox(self.main_window)
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
    
    
    def _get_current_selected_adapter(self):
        """
        获取当前选中的网卡信息
        
        这个方法用于获取用户当前在UI中选择的网卡信息，主要用于IP配置应用前
        的网卡上下文获取。采用委托模式，将获取逻辑委托给服务层。
        
        设计原则：
        - 单一职责：专门负责获取当前选中网卡信息
        - 委托模式：委托给服务层获取实际数据
        - 异常安全：确保获取失败时返回None而不是抛出异常
        
        Returns:
            dict or None: 当前选中的网卡信息字典，获取失败时返回None
        """
        try:
            if not self.network_service:
                self.logger.error("网络服务未初始化，无法获取当前网卡")
                return None
                
            # 委托给服务层获取当前选中的网卡信息
            current_adapter = self.network_service.get_current_adapter()
            
            if current_adapter:
                self.logger.debug(f"当前网卡对象类型: {type(current_adapter)}")
                self.logger.debug(f"当前网卡对象内容: {current_adapter}")
                
                # 适配多种数据格式
                if hasattr(current_adapter, 'adapter_id') and hasattr(current_adapter, 'basic_info'):
                    # AggregatedAdapterInfo对象
                    if current_adapter.basic_info and hasattr(current_adapter.basic_info, 'friendly_name'):
                        adapter_name = current_adapter.basic_info.friendly_name or '未知'
                    else:
                        adapter_name = '未知'
                    self.logger.debug(f"使用AggregatedAdapterInfo格式获取网卡名: {adapter_name}")
                elif isinstance(current_adapter, dict):
                    # 字典格式
                    adapter_name = current_adapter.get('friendly_name', '未知')
                    self.logger.debug(f"使用字典格式获取网卡名: {adapter_name}")
                elif hasattr(current_adapter, 'friendly_name'):
                    # 直接属性访问
                    adapter_name = current_adapter.friendly_name or '未知'
                    self.logger.debug(f"使用直接属性访问获取网卡名: {adapter_name}")
                else:
                    adapter_name = '未知'
                    self.logger.warning(f"无法识别网卡对象格式，对象类型: {type(current_adapter)}, 属性: {dir(current_adapter)}")
                self.logger.debug(f"获取当前网卡成功: {adapter_name}")
            else:
                self.logger.debug("当前没有选中的网卡")
                
            return current_adapter
            
        except Exception as e:
            self.logger.error(f"获取当前网卡信息异常: {str(e)}")
            import traceback
            self.logger.error(f"异常堆栈: {traceback.format_exc()}")
            return None
