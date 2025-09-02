# -*- coding: utf-8 -*-
"""
网络配置事件处理器：负责UI事件转换为服务层调用和用户反馈处理
"""

from PyQt5.QtWidgets import QMessageBox
from ...utils.logger import get_logger
from ...models.ip_config_confirmation import IPConfigConfirmation
from ..dialogs.ip_config_confirm_dialog import IPConfigConfirmDialog
from ..dialogs.operation_result_dialog import OperationResultDialog


class NetworkEventHandler:
    """
    网络配置事件处理器
    
    负责UI事件转换为服务层调用，将用户在界面上的操作转换为
    服务层能够处理的业务逻辑调用。同时处理用户反馈显示。
    
    设计原则：
    - 单一职责：专门处理网络配置相关的UI事件转换
    - 封装性：将复杂的事件转换逻辑封装在独立方法中
    - 依赖倒置：依赖于服务层抽象接口，不依赖具体实现
    """
    
    def __init__(self, main_window, network_service=None):
        """
        初始化网络事件处理器
        
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
        连接网络服务的信号到事件处理方法
        """
        if not self.network_service:
            return
            
        # 连接网络服务的信号到事件处理方法
        self.network_service.adapters_updated.connect(self._on_adapters_updated)
        self.network_service.adapter_selected.connect(self._on_adapter_selected)
        self.network_service.ip_info_updated.connect(self._on_ip_info_updated)
        self.network_service.extra_ips_updated.connect(self._on_extra_ips_updated)
        self.network_service.adapter_refreshed.connect(self._on_adapter_refreshed)
        self.network_service.network_info_copied.connect(self._on_network_info_copied)
        self.network_service.error_occurred.connect(self._on_network_error)
        
        # 连接adapter_info_updated信号，用于网卡切换后的状态栏最终更新
        self.network_service.adapter_info_updated.connect(self._on_adapter_info_updated_for_status_bar)
        
        # 连接网卡操作信号
        self.network_service.operation_completed.connect(self._on_operation_completed)
        
        self.logger.debug("NetworkEventHandler信号连接完成，包括adapter_info_updated和operation_completed信号")
    
    def _on_adapters_updated(self, adapters):
        """
        处理网卡列表更新事件
        
        Args:
            adapters: 更新后的网卡列表
        """
        try:
            self.logger.debug(f"网卡列表已更新，共 {len(adapters)} 个网卡")
        except Exception as e:
            self.logger.error(f"处理网卡列表更新事件时发生异常: {str(e)}")
    
    def _on_adapter_selected(self, adapter_info):
        """
        处理网卡选择事件
        
        Args:
            adapter_info: 选中的网卡信息
        """
        try:
            self.logger.debug(f"网卡已选择: {adapter_info}")
        except Exception as e:
            self.logger.error(f"处理网卡选择事件时发生异常: {str(e)}")
    
    def _on_ip_info_updated(self, ip_info):
        """
        处理IP信息更新事件
        
        Args:
            ip_info: 更新后的IP信息
        """
        try:
            self.logger.debug(f"IP信息已更新: {ip_info}")
        except Exception as e:
            self.logger.error(f"处理IP信息更新事件时发生异常: {str(e)}")
    
    def _on_extra_ips_updated(self, extra_ips):
        """
        处理额外IP列表更新事件
        
        Args:
            extra_ips: 更新后的额外IP列表
        """
        try:
            self.logger.debug(f"额外IP列表已更新，共 {len(extra_ips)} 个IP")
        except Exception as e:
            self.logger.error(f"处理额外IP列表更新事件时发生异常: {str(e)}")
    
    def _on_adapter_refreshed(self, adapter_info):
        """
        处理网卡刷新事件
        
        Args:
            adapter_info: 刷新后的网卡信息
        """
        try:
            self.logger.debug(f"网卡信息已刷新: {adapter_info}")
        except Exception as e:
            self.logger.error(f"处理网卡刷新事件时发生异常: {str(e)}")
    
    def _on_network_info_copied(self, success_message):
        """
        处理网络信息复制事件
        
        Args:
            success_message: 复制成功消息
        """
        try:
            self.logger.debug(f"网络信息复制成功: {success_message}")
        except Exception as e:
            self.logger.error(f"处理网络信息复制事件时发生异常: {str(e)}")
    
    def _on_network_error(self, error_title, error_message):
        """
        处理网络错误事件
        
        Args:
            error_title: 错误标题
            error_message: 错误消息
        """
        try:
            self.logger.error(f"网络错误 - {error_title}: {error_message}")
        except Exception as e:
            self.logger.error(f"处理网络错误事件时发生异常: {str(e)}")
    
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
        5. 在状态栏显示网卡切换状态
        
        Args:
            display_name (str): UI下拉框中选中的完整显示名称，格式为"描述 (友好名称)"
        """
        self.logger.debug(f"🔄 网卡切换事件触发 - 选择的网卡: '{display_name}'")
        try:
            if not self.network_service or not display_name:
                return
            
            # 现在显示名称直接是description，需要根据description查找对应的网卡
            # 在服务层的网卡缓存中查找匹配的网卡对象
            # 这里访问服务层的内部数据是为了实现UI与服务层的协调工作
            self.logger.debug(f"查找网卡匹配，显示名称: '{display_name}'")
            self.logger.debug(f"当前缓存网卡数量: {len(self.network_service._adapters) if self.network_service._adapters else 0}")
            
            for adapter in self.network_service._adapters:
                self.logger.debug(f"🔍 检查网卡匹配: name='{adapter.name}', description='{adapter.description}', friendly_name='{adapter.friendly_name}'")
                # 现在匹配name字段（完整名称带序号）
                if adapter.name == display_name or adapter.description == display_name or adapter.friendly_name == display_name:
                    # 找到匹配的网卡，立即更新状态徽章以减少卡顿感
                    # 先使用缓存的网卡信息快速更新状态徽章
                    self.logger.debug(f"找到匹配网卡，立即更新状态徽章: {adapter.id}")
                    
                    # 移除立即更新逻辑，避免显示过时的缓存数据
                    # 直接依赖服务层的完整刷新流程，确保显示最新的链路速度信息
                    
                    # 在状态栏显示网卡切换状态
                    if hasattr(self.main_window, 'service_coordinator') and self.main_window.service_coordinator.status_bar_service:
                        self.main_window.service_coordinator.status_bar_service.set_status(
                            f"🔄 正在切换到网卡: {adapter.friendly_name}", 
                            auto_clear_seconds=2
                        )
                    
                    # 然后调用服务层的选择方法进行完整刷新
                    # 这将触发一系列的信号发射，最终更新UI显示
                    self.logger.debug(f"调用select_adapter进行完整刷新: {adapter.id}")
                    self.network_service.select_adapter(adapter.id)
                    self.logger.debug(f"用户选择网卡：{display_name}")
                    return
            
            # 如果没有找到匹配的网卡，记录警告信息便于调试
            self.logger.warning(f"无法找到匹配的网卡，显示名称: '{display_name}'")
                
        except Exception as e:
            # 异常处理：确保网卡选择错误不会导致程序崩溃
            # 详细记录错误信息，便于开发人员快速定位问题
            self.logger.error(f"网卡选择处理失败，错误详情: {str(e)}")
            # 在生产环境中，这里应该向用户显示友好的错误提示
    
    def _get_current_selected_adapter(self):
        """
        获取当前选中的网卡信息（复用现有数据）
        
        从网络配置Tab的适配器信息面板获取当前选中的网卡对象，
        避免重复查找网卡信息，提高代码复用性。
        
        Returns:
            AdapterInfo: 当前选中的网卡信息对象，如果未找到返回None
        """
        try:
            current_adapter_text = self.main_window.network_config_tab.adapter_info_panel.adapter_combo.currentText()
            if not current_adapter_text:
                return None
            
            # 从服务层缓存中查找匹配的网卡对象
            for adapter in self.network_service._adapters:
                if (adapter.name == current_adapter_text or 
                    adapter.description == current_adapter_text or 
                    adapter.friendly_name == current_adapter_text):
                    return adapter
            return None
        except Exception as e:
            self.logger.error(f"获取当前选中网卡失败: {str(e)}")
            return None

    def _on_apply_ip_config(self, config_data):
        """
        处理IP配置应用请求的核心方法
        
        这个方法接收来自UI层的IP配置数据，进行验证和预处理，
        然后调用服务层执行实际的网络配置操作。
        
        Args:
            config_data (dict): IP配置数据字典，包含ip_address、subnet_mask等字段
        """
        try:
            # 添加调试日志，确认方法被调用
            self.logger.info(f"🔥 网络事件处理器收到IP配置应用请求: {config_data}")
            self.logger.info("🔥 开始执行网卡状态检测和IP配置流程")
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
            
            # 获取当前UI中实际选择的网卡
            current_adapter_text = self.main_window.network_config_tab.adapter_info_panel.adapter_combo.currentText()
            if not current_adapter_text:
                self.logger.warning("未选择网卡，无法应用IP配置")
                return
            
            # 直接从网络配置Tab获取当前选中的网卡信息（复用现有数据）
            target_adapter = self._get_current_selected_adapter()
            
            if not target_adapter:
                self.logger.error(f"无法找到匹配的网卡: {current_adapter_text}")
                return
            
            # 🔥 关键修复：在任何验证之前先检查网卡状态并自动启用
            # 获取最新的网卡状态，而不是使用缓存中的旧状态
            if hasattr(self.main_window, 'service_coordinator') and self.main_window.service_coordinator.adapter_status_service:
                current_status, is_enabled, is_connected = self.main_window.service_coordinator.adapter_status_service.get_adapter_status(target_adapter.friendly_name)
                self.logger.info(f"🔥 检查网卡状态 - 网卡: {target_adapter.friendly_name}, 最新状态: '{current_status}', 启用: {is_enabled}")
                adapter_disabled = not is_enabled
            else:
                # 备用方案：使用缓存状态
                self.logger.info(f"🔥 检查网卡状态 - 网卡: {target_adapter.friendly_name}, 缓存状态: '{target_adapter.status}'")
                adapter_disabled = (target_adapter.status == "已禁用" or 
                                  target_adapter.status == "Disabled" or
                                  "禁用" in target_adapter.status)
            
            # 如果网卡禁用，先自动启用网卡
            if adapter_disabled:
                self.logger.info(f"🔥 网卡 {target_adapter.friendly_name} 处于禁用状态，需要先启用网卡")
                
                # 显示启用网卡的提示对话框
                from PyQt5.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self.main_window,
                    "网卡状态提示",
                    f"网卡 '{target_adapter.friendly_name}' 当前处于 {target_adapter.status} 状态。\n\n"
                    f"需要先启用网卡才能修改IP配置。\n\n"
                    f"是否自动启用网卡？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    # 启用网卡
                    enable_success = self.network_service.enable_adapter(target_adapter.friendly_name)
                    if not enable_success:
                        self.logger.error(f"启用网卡失败: {target_adapter.friendly_name}")
                        QMessageBox.critical(
                            self.main_window,
                            "网卡启用失败",
                            f"无法启用网卡 {target_adapter.friendly_name}，请检查网络设置。"
                        )
                        return
                    else:
                        self.logger.info(f"🔥 网卡启用成功: {target_adapter.friendly_name}")
                        # 等待网卡启用完成
                        import time
                        time.sleep(3)
                        # 重新获取网卡信息
                        self.network_service.refresh_current_adapter()
                        QMessageBox.information(
                            self.main_window,
                            "网卡启用成功",
                            f"网卡 {target_adapter.friendly_name} 已成功启用，现在继续修改IP配置。"
                        )
                        # 重新获取更新后的网卡信息
                        target_adapter = self._get_current_selected_adapter()
                else:
                    self.logger.info("用户取消启用网卡，IP配置操作终止")
                    return
            
            # 提取可选配置参数
            gateway = config_data.get('gateway', '').strip()
            primary_dns = config_data.get('primary_dns', '').strip()
            secondary_dns = config_data.get('secondary_dns', '').strip()
            
            # 从左侧IP信息显示区域解析当前配置，因为左侧显示是正确的
            try:
                network_tab = self.main_window.network_config_tab
                ip_info_text = network_tab.ip_info_display.toPlainText()
                
                # 解析IP信息文本获取当前配置
                current_ip = ""
                current_subnet = ""
                current_gateway = ""
                current_dns1 = ""
                current_dns2 = ""
                
                lines = ip_info_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if '主IP地址:' in line and current_ip == "":
                        current_ip = line.split(':', 1)[1].strip()
                    elif '子网掩码:' in line:
                        current_subnet = line.split(':', 1)[1].strip()
                    elif '默认网关:' in line:
                        current_gateway = line.split(':', 1)[1].strip()
                    elif '主DNS服务器:' in line:
                        current_dns1 = line.split(':', 1)[1].strip()
                    elif '备用DNS服务器:' in line:
                        current_dns2 = line.split(':', 1)[1].strip()
                    elif 'DNS服务器:' in line and current_dns1 == "":
                        # 兼容旧格式的DNS显示
                        dns_part = line.split(':', 1)[1].strip()
                        if ',' in dns_part:
                            dns_list = [dns.strip() for dns in dns_part.split(',')]
                            current_dns1 = dns_list[0] if len(dns_list) > 0 else ""
                            current_dns2 = dns_list[1] if len(dns_list) > 1 else ""
                        else:
                            current_dns1 = dns_part
                
                self.logger.debug(f"从左侧信息区域解析当前配置 - IP: '{current_ip}', 子网: '{current_subnet}', "
                               f"网关: '{current_gateway}', DNS1: '{current_dns1}', DNS2: '{current_dns2}'")
            except Exception as e:
                self.logger.error(f"从信息显示区域解析配置失败: {e}")
                # 回退到网卡对象获取
                current_ip = target_adapter.get_primary_ip()
                current_subnet = target_adapter.get_primary_subnet_mask()
                current_gateway = target_adapter.gateway or ""
                current_dns1 = target_adapter.get_primary_dns()
                current_dns2 = target_adapter.get_secondary_dns()
            
            self.logger.debug(f"当前网卡配置 - IP: '{current_ip}', 子网: '{current_subnet}', "
                            f"网关: '{current_gateway}', DNS1: '{current_dns1}', DNS2: '{current_dns2}'")
            self.logger.debug(f"网卡原始信息 - ip_addresses: {target_adapter.ip_addresses}, "
                            f"subnet_masks: {target_adapter.subnet_masks}, "
                            f"gateway: '{target_adapter.gateway}', "
                            f"dns_servers: {target_adapter.dns_servers}")
            
            # 提取新配置数据
            new_ip = config_data.get('ip_address', '').strip()
            new_subnet = config_data.get('subnet_mask', '').strip()
            new_gateway = gateway or ""
            new_dns1 = primary_dns or ""
            new_dns2 = secondary_dns or ""
            
            # 记录新旧配置对比
            self.logger.debug(f"配置对比 - 当前IP: '{current_ip}' vs 新IP: '{new_ip}'")
            self.logger.debug(f"配置对比 - 当前子网: '{current_subnet}' vs 新子网: '{new_subnet}'")
            self.logger.debug(f"配置对比 - 当前网关: '{current_gateway}' vs 新网关: '{new_gateway}'")
            self.logger.debug(f"配置对比 - 当前DNS1: '{current_dns1}' vs 新DNS1: '{new_dns1}'")
            self.logger.debug(f"配置对比 - 当前DNS2: '{current_dns2}' vs 新DNS2: '{new_dns2}'")
            
            # 检查网卡是否禁用，如果禁用则先自动启用
            self.logger.debug(f"确认弹窗前网卡状态检查 - 网卡: {target_adapter.friendly_name}, 状态: '{target_adapter.status}'")
            adapter_disabled = (target_adapter.status == "已禁用" or 
                              target_adapter.status == "Disabled" or
                              "禁用" in target_adapter.status)
            
            # 如果网卡禁用，先自动启用网卡
            if adapter_disabled:
                self.logger.info(f"网卡 {target_adapter.friendly_name} 处于禁用状态，先启用网卡")
                
                # 显示启用网卡的提示对话框
                from PyQt5.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self.main_window,
                    "网卡状态提示",
                    f"网卡 '{target_adapter.friendly_name}' 当前处于禁用状态。\n\n"
                    f"需要先启用网卡才能修改IP配置。\n\n"
                    f"是否自动启用网卡？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    # 启用网卡
                    enable_success = self.network_service.enable_adapter(target_adapter.friendly_name)
                    if not enable_success:
                        self.logger.error(f"启用网卡失败: {target_adapter.friendly_name}")
                        QMessageBox.critical(
                            self.main_window,
                            "网卡启用失败",
                            f"无法启用网卡 {target_adapter.friendly_name}，请检查网络设置。"
                        )
                        return
                    else:
                        self.logger.info(f"网卡启用成功: {target_adapter.friendly_name}")
                        # 等待网卡启用完成
                        import time
                        time.sleep(2)
                        # 重新获取网卡信息
                        self.network_service.refresh_current_adapter()
                        QMessageBox.information(
                            self.main_window,
                            "网卡启用成功",
                            f"网卡 {target_adapter.friendly_name} 已成功启用，现在可以修改IP配置。"
                        )
                else:
                    self.logger.info("用户取消启用网卡，IP配置操作终止")
                    return
            
            # 创建IP配置确认数据模型
            confirmation_data = IPConfigConfirmation(
                adapter_name=target_adapter.friendly_name or target_adapter.name,
                dhcp_enabled=False,
                current_ip=current_ip,
                current_subnet_mask=current_subnet,
                current_gateway=current_gateway,
                current_dns_primary=current_dns1,
                current_dns_secondary=current_dns2,
                new_ip=new_ip,
                new_subnet_mask=new_subnet,
                new_gateway=new_gateway,
                new_dns_primary=primary_dns or "",
                new_dns_secondary=secondary_dns or ""
            )
            
            # 检查是否有实际变更
            if not confirmation_data.has_changes():
                self.logger.debug("检测到无实际配置变更，仍显示确认弹窗")
            
            # 显示IP配置确认弹窗
            confirm_dialog = IPConfigConfirmDialog(confirmation_data, self.main_window)
            
            # 如果网卡禁用，在弹窗中添加额外提示
            if adapter_disabled:
                # 在变更详情中添加网卡启用提示
                original_html = confirm_dialog.changes_text.toHtml()
                additional_info = """
                <div style='background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 8px; margin: 8px 0; border-radius: 4px;'>
                    <span style='color: #856404; font-weight: bold;'>⚠️ 重要提示：</span><br>
                    <span style='color: #856404;'>检测到网卡处于禁用状态，系统将先自动启用网卡，然后应用IP配置。</span>
                </div>
                """
                confirm_dialog.changes_text.setHtml(original_html + additional_info)
            
            # 连接确认信号到实际的IP配置应用方法
            confirm_dialog.confirmed.connect(
                lambda: self._apply_confirmed_ip_config(
                    target_adapter.id, ip_address, subnet_mask, 
                    gateway, primary_dns, secondary_dns, current_adapter_text,
                    target_adapter  # 传递完整的adapter对象用于状态检查
                )
            )
            
            # 连接取消信号到日志记录
            confirm_dialog.cancelled.connect(
                lambda: self.logger.debug(f"用户取消IP配置修改: {current_adapter_text}")
            )
            
            # 显示弹窗（模态）
            self.logger.debug(f"显示IP配置确认弹窗: {current_adapter_text}")
            confirm_dialog.exec_()
                
        except Exception as e:
            # 异常处理：确保IP配置错误不会导致程序崩溃
            # 记录详细错误信息便于开发人员快速定位问题
            self.logger.error(f"处理IP配置应用请求失败，错误详情: {str(e)}")
            # 在生产环境中，这里应该向用户显示友好的错误提示
    
    def _apply_confirmed_ip_config(self, adapter_id, ip_address, subnet_mask, 
                                 gateway, primary_dns, secondary_dns, adapter_display_name, adapter_info=None):
        """
        应用用户确认的IP配置
        
        这个方法在用户通过确认弹窗确认修改后被调用，执行实际的IP配置应用操作。
        将确认逻辑与实际应用逻辑分离，符合单一职责原则。
        
        增强版本：在实际应用前进行最终验证，如果发现无效输入则显示用户友好的错误提示。
        
        Args:
            adapter_id: 网卡标识符
            ip_address: IP地址
            subnet_mask: 子网掩码
            gateway: 网关地址
            primary_dns: 主DNS服务器
            secondary_dns: 辅助DNS服务器
            adapter_display_name: 网卡显示名称（用于日志）
        """
        try:
            # 最终验证：在应用配置前验证所有输入的有效性
            from ...utils.ip_validation_utils import validate_ip_address, smart_validate_subnet_mask
            from ..dialogs.validation_error_dialog import ValidationErrorDialog
            
            # 验证IP地址
            if not validate_ip_address(ip_address):
                self.logger.warning(f"最终验证发现无效IP地址: {ip_address}")
                error_dialog = ValidationErrorDialog("ip_address", ip_address, self.main_window)
                error_dialog.show()
                return
            
            # 验证子网掩码 - 使用智能验证支持简写格式
            if not smart_validate_subnet_mask(subnet_mask):
                self.logger.warning(f"最终验证发现无效子网掩码: {subnet_mask}")
                error_dialog = ValidationErrorDialog("subnet_mask", subnet_mask, self.main_window)
                error_dialog.show()
                return
            
            # 验证网关地址（如果提供）
            if gateway and not validate_ip_address(gateway):
                self.logger.warning(f"最终验证发现无效网关地址: {gateway}")
                error_dialog = ValidationErrorDialog("ip_address", gateway, self.main_window)
                error_dialog.show()
                return
            
            # 验证DNS服务器地址（如果提供）
            if primary_dns and not validate_ip_address(primary_dns):
                self.logger.warning(f"最终验证发现无效主DNS地址: {primary_dns}")
                error_dialog = ValidationErrorDialog("ip_address", primary_dns, self.main_window)
                error_dialog.show()
                return
                
            if secondary_dns and not validate_ip_address(secondary_dns):
                self.logger.warning(f"最终验证发现无效辅助DNS地址: {secondary_dns}")
                error_dialog = ValidationErrorDialog("ip_address", secondary_dns, self.main_window)
                error_dialog.show()
                return
            # 在状态栏显示IP配置应用状态
            if hasattr(self.main_window, 'service_coordinator') and self.main_window.service_coordinator.status_bar_service:
                self.main_window.service_coordinator.status_bar_service.set_status(
                    f"⚙️ 正在应用IP配置到: {adapter_display_name}", 
                    auto_clear_seconds=5
                )
            
            # 网卡状态检测已在确认弹窗前完成，此处直接执行IP配置
            
            # 记录IP配置应用操作的开始
            self.logger.debug(f"用户确认后开始应用IP配置到网卡 {adapter_display_name}: "
                           f"IP={ip_address}, 掩码={subnet_mask}")
            
            # 调用服务层的IP配置应用方法
            # 这将触发实际的网络配置修改操作
            success = self.network_service.apply_ip_config(
                adapter_id=adapter_id,
                ip_address=ip_address,
                subnet_mask=subnet_mask,
                gateway=gateway,
                primary_dns=primary_dns,
                secondary_dns=secondary_dns
            )
            
            if success:
                self.logger.debug(f"IP配置应用成功: {adapter_display_name}")
            else:
                self.logger.warning(f"IP配置应用失败: {adapter_display_name}")
                
        except Exception as e:
            # 异常处理：确保IP配置错误不会导致程序崩溃
            self.logger.error(f"应用确认的IP配置失败，错误详情: {str(e)}")
            # 显示错误弹窗
            QMessageBox.critical(
                self.main_window,
                "配置应用失败",
                f"应用IP配置时发生错误：\n\n{str(e)}\n\n请检查网络设置或联系管理员。"
            )
    
    def _on_service_error(self, error_title, error_message):
        """
        处理服务层错误信号并显示错误弹窗
        
        作用说明：
        当网络配置操作发生错误时，这个方法负责向用户显示明确的错误信息弹窗。
        采用面向对象设计原则，将错误处理逻辑封装在独立方法中，
        确保用户能够及时了解错误原因并获得解决问题的指导。
        
        面向对象设计特点：
        - 单一职责：专门负责错误信息的UI显示
        - 封装性：将错误处理逻辑封装在方法内部
        - 用户体验：提供清晰的错误描述和解决建议
        
        Args:
            error_title (str): 错误标题，简要描述错误类型
            error_message (str): 详细错误信息，包含具体错误原因和建议
        """
        try:
            # 在状态栏显示错误状态
            if hasattr(self.main_window, 'service_coordinator') and self.main_window.service_coordinator.status_bar_service:
                self.main_window.service_coordinator.status_bar_service.set_status(
                    f"❌ 操作失败: {error_title}", 
                    auto_clear_seconds=5
                )
            
            # 记录错误信息供开发者调试使用
            self.logger.error(f"服务层错误 - {error_title}: {error_message}")
            
            # 显示用户友好的错误弹窗
            
            # 创建错误消息框，使用警告图标吸引用户注意
            error_box = QMessageBox(self.main_window)
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
            self.logger.debug(f"操作进度: {progress_message}")
            
            # 这里可以添加用户友好的进度提示逻辑
            # 例如进度条、状态栏消息、加载动画等
            # 当前版本通过日志记录，后续版本可扩展UI进度显示
            
        except Exception as e:
            self.logger.error(f"网卡选择处理异常: {str(e)}")
    
    def _on_add_selected_extra_ips(self, adapter_id, selected_ips):
        """
        处理添加选中额外IP事件
        
        Args:
            adapter_id (str): 网卡ID
            selected_ips (List[str]): 选中的IP地址列表
        """
        try:
            self.logger.debug(f"🔄 开始添加选中的额外IP - 网卡: {adapter_id}, IP数量: {len(selected_ips)}")
            
            # 在状态栏显示操作状态
            if hasattr(self.main_window, 'service_coordinator') and self.main_window.service_coordinator.status_bar_service:
                self.main_window.service_coordinator.status_bar_service.set_status(
                    f"🔄 正在添加 {len(selected_ips)} 个额外IP地址...", 
                    auto_clear_seconds=0  # 不自动清除，等待操作完成
                )
            
            # 调用服务层方法添加额外IP
            self.network_service.add_selected_extra_ips(adapter_id, selected_ips)
            
        except Exception as e:
            self.logger.error(f"处理添加选中额外IP事件时发生异常: {str(e)}")
            # 在状态栏显示错误状态
            if hasattr(self.main_window, 'service_coordinator') and self.main_window.service_coordinator.status_bar_service:
                self.main_window.service_coordinator.status_bar_service.set_status(
                    f"❌ 添加额外IP失败: {str(e)}", 
                    auto_clear_seconds=5
                )

    def _on_adapter_info_updated_for_status_bar(self, aggregated_info):
        """
        处理网卡信息更新事件，专门用于状态栏最终状态更新
        
        当网卡切换完成后，基于最新的网卡信息更新状态栏显示最终状态。
        这确保了网卡切换操作的完整性和用户体验的连贯性。
        
        Args:
            aggregated_info: 聚合的网卡信息对象
        """
        try:
            self.logger.debug(f"🎯 收到adapter_info_updated信号，开始更新状态栏")
            
            if not aggregated_info or not aggregated_info.detailed_info:
                self.logger.debug("网卡信息不完整，跳过状态栏更新")
                return
                
            detailed_info = aggregated_info.detailed_info
            
            # 获取网卡友好名称用于显示
            adapter_name = getattr(detailed_info, 'friendly_name', '') or getattr(detailed_info, 'name', '未知网卡')
            
            # 获取连接状态（使用正确的字段名）
            connection_status = getattr(detailed_info, 'status', '未知')
            
            self.logger.debug(f"📊 网卡信息 - 名称: {adapter_name}, 状态: {connection_status}")
            
            # 根据连接状态设置状态栏消息
            if connection_status == '已连接' or connection_status == 'Up':
                status_message = f"✅ 已切换到 {adapter_name} (已连接)"
            elif connection_status == '已断开' or connection_status == 'Down':
                status_message = f"🔌 已切换到 {adapter_name} (已断开)"
            else:
                status_message = f"🔄 已切换到 {adapter_name}"
            
            # 更新状态栏显示最终状态
            if hasattr(self.main_window, 'service_coordinator') and self.main_window.service_coordinator.status_bar_service:
                self.main_window.service_coordinator.status_bar_service.set_status(
                    status_message, 
                    auto_clear_seconds=0  # 不自动清除，保持显示
                )
                self.logger.debug(f"✅ 状态栏已更新网卡切换最终状态: {status_message}")
            else:
                self.logger.error("❌ 无法访问状态栏服务")
            
        except Exception as e:
            self.logger.error(f"更新网卡切换状态栏时发生异常: {str(e)}")
    
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
                self.main_window,
                "操作成功",
                success_message,
                QMessageBox.Ok
            )
            
            # 记录成功操作日志，便于运维监控和问题追踪
            self.logger.debug(f"批量添加额外IP操作成功: {success_message}")
            
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
                self.main_window,
                "操作成功",
                success_message,
                QMessageBox.Ok
            )
            
            # 记录成功操作日志，便于运维监控和问题追踪
            self.logger.debug(f"批量删除额外IP操作成功: {success_message}")
            
        except Exception as e:
            # 异常处理：确保弹窗显示失败不会影响主程序运行
            # 详细记录错误信息，便于开发人员快速定位问题
            self.logger.error(f"处理批量删除IP成功信号失败: {str(e)}")
            # 如果弹窗显示失败，至少记录日志保证成功信息不丢失
    
    def _on_operation_completed(self, success: bool, message: str, operation: str):
        """
        处理网卡操作完成信号
        
        显示统一的操作结果弹窗，提供用户友好的操作反馈。
        操作成功后自动刷新网卡信息以更新状态显示。
        异常时使用备用QMessageBox确保用户获得操作反馈。
        
        Args:
            success: 操作是否成功
            message: 操作结果消息
            operation: 操作类型描述
        """
        try:
            # 显示操作结果弹窗
            if success:
                OperationResultDialog.show_success(message, operation, self.main_window)
                # 操作成功后自动刷新网卡信息，更新状态显示
                if self.network_service:
                    self.logger.debug(f"{operation}成功，自动刷新网卡信息")
                    self.network_service.refresh_current_adapter()
            else:
                OperationResultDialog.show_error(message, operation, self.main_window)
                
        except Exception as e:
            self.logger.error(f"显示操作结果弹窗失败: {e}")
            # 备用弹窗处理
            try:
                from PyQt5.QtWidgets import QMessageBox
                if success:
                    QMessageBox.information(self.main_window, f"✅ {operation}成功", message)
                    # 即使弹窗失败，也要刷新网卡信息
                    if self.network_service:
                        self.network_service.refresh_current_adapter()
                else:
                    QMessageBox.critical(self.main_window, f"❌ {operation}失败", message)
            except Exception as fallback_error:
                self.logger.error(f"备用弹窗也失败: {fallback_error}")
    
    def _on_set_static_ip(self, adapter_name: str):
        """
        处理设置静态IP信号
        
        复用现有的IP配置修改逻辑，通过触发IP配置应用来实现静态IP设置。
        这样可以保持代码的一致性和复用性。
        
        Args:
            adapter_name: 要设置静态IP的网卡名称
        """
        try:
            self.logger.info(f"处理静态IP设置请求: {adapter_name}")
            
            # 获取当前网卡的IP配置信息
            current_config = self.main_window.network_config_tab.ip_config_panel.get_current_ip_config()
            
            if current_config:
                # 添加网卡信息到配置数据中
                current_config['adapter'] = adapter_name
                # 触发IP配置应用，实现静态IP设置
                self._on_apply_ip_config(current_config)
            else:
                self.logger.warning(f"无法获取网卡 {adapter_name} 的当前IP配置")
                # 显示错误提示
                try:
                    OperationResultDialog.show_error(
                        "无法获取当前IP配置信息，请检查网卡状态", 
                        "设置静态IP", 
                        self.main_window
                    )
                except Exception:
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.warning(self.main_window, "设置静态IP", "无法获取当前IP配置信息")
                    
        except Exception as e:
            self.logger.error(f"处理静态IP设置失败: {e}")
            try:
                OperationResultDialog.show_error(
                    f"设置静态IP时发生错误: {str(e)}", 
                    "设置静态IP", 
                    self.main_window
                )
            except Exception:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self.main_window, "设置静态IP失败", f"操作失败: {str(e)}")
