# -*- coding: utf-8 -*-
"""
网络配置事件处理器：负责UI事件转换为服务层调用和用户反馈处理
"""

from PyQt5.QtWidgets import QMessageBox
from ...utils.logger import get_logger
from ...models.ip_config_confirmation import IPConfigConfirmation
from ..dialogs.ip_config_confirm_dialog import IPConfigConfirmDialog


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
        
        增强版本：集成IP配置确认弹窗，在应用配置前展示变更详情并询问用户确认。
        这个方法是"修改IP地址"按钮功能的关键桥梁，负责将UI层收集的
        配置数据转换为服务层能够处理的格式，并调用相应的业务方法。
        
        工作流程：
        1. 接收UI层传递的配置数据字典
        2. 验证必要的配置参数是否完整
        3. 获取当前选中的网卡标识符和当前配置
        4. 创建IP配置确认数据模型
        5. 显示确认弹窗，等待用户确认
        6. 用户确认后调用服务层的IP配置应用方法
        7. 处理可能的异常情况并记录日志
        
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
            
            # 获取当前选中的网卡ID和网卡对象
            adapter_display_name = config_data.get('adapter', '')
            if not adapter_display_name:
                self.logger.warning("未选择网卡，无法应用IP配置")
                return
            
            # 在服务层的网卡缓存中查找匹配的网卡对象
            target_adapter = None
            for adapter in self.network_service._adapters:
                if (adapter.name == adapter_display_name or 
                    adapter.description == adapter_display_name or 
                    adapter.friendly_name == adapter_display_name):
                    target_adapter = adapter
                    break
            
            if not target_adapter:
                self.logger.error(f"无法找到匹配的网卡: {adapter_display_name}")
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
                
                self.logger.info(f"从左侧信息区域解析当前配置 - IP: '{current_ip}', 子网: '{current_subnet}', "
                               f"网关: '{current_gateway}', DNS1: '{current_dns1}', DNS2: '{current_dns2}'")
            except Exception as e:
                self.logger.error(f"从信息显示区域解析配置失败: {e}")
                # 回退到网卡对象获取
                current_ip = target_adapter.get_primary_ip()
                current_subnet = target_adapter.get_primary_subnet_mask()
                current_gateway = target_adapter.gateway or ""
                current_dns1 = target_adapter.get_primary_dns()
                current_dns2 = target_adapter.get_secondary_dns()
            
            self.logger.info(f"当前网卡配置 - IP: '{current_ip}', 子网: '{current_subnet}', "
                            f"网关: '{current_gateway}', DNS1: '{current_dns1}', DNS2: '{current_dns2}'")
            self.logger.info(f"网卡原始信息 - ip_addresses: {target_adapter.ip_addresses}, "
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
            self.logger.info(f"配置对比 - 当前IP: '{current_ip}' vs 新IP: '{new_ip}'")
            self.logger.info(f"配置对比 - 当前子网: '{current_subnet}' vs 新子网: '{new_subnet}'")
            self.logger.info(f"配置对比 - 当前网关: '{current_gateway}' vs 新网关: '{new_gateway}'")
            self.logger.info(f"配置对比 - 当前DNS1: '{current_dns1}' vs 新DNS1: '{new_dns1}'")
            self.logger.info(f"配置对比 - 当前DNS2: '{current_dns2}' vs 新DNS2: '{new_dns2}'")
            
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
                self.logger.info("检测到无实际配置变更，仍显示确认弹窗")
            
            # 显示IP配置确认弹窗
            confirm_dialog = IPConfigConfirmDialog(confirmation_data, self.main_window)
            
            # 连接确认信号到实际应用方法
            confirm_dialog.confirmed.connect(
                lambda: self._apply_confirmed_ip_config(
                    target_adapter.id, ip_address, subnet_mask, 
                    gateway, primary_dns, secondary_dns, adapter_display_name
                )
            )
            
            # 连接取消信号到日志记录
            confirm_dialog.cancelled.connect(
                lambda: self.logger.info(f"用户取消IP配置修改: {adapter_display_name}")
            )
            
            # 显示弹窗（模态）
            self.logger.info(f"显示IP配置确认弹窗: {adapter_display_name}")
            confirm_dialog.exec_()
                
        except Exception as e:
            # 异常处理：确保IP配置错误不会导致程序崩溃
            # 记录详细错误信息便于开发人员快速定位问题
            self.logger.error(f"处理IP配置应用请求失败，错误详情: {str(e)}")
            # 在生产环境中，这里应该向用户显示友好的错误提示
    
    def _apply_confirmed_ip_config(self, adapter_id, ip_address, subnet_mask, 
                                 gateway, primary_dns, secondary_dns, adapter_display_name):
        """
        应用用户确认的IP配置
        
        这个方法在用户通过确认弹窗确认修改后被调用，执行实际的IP配置应用操作。
        将确认逻辑与实际应用逻辑分离，符合单一职责原则。
        
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
            # 记录IP配置应用操作的开始
            self.logger.info(f"用户确认后开始应用IP配置到网卡 {adapter_display_name}: "
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
                self.logger.info(f"IP配置应用成功: {adapter_display_name}")
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
            # 记录IP配置成功的详细信息供开发者调试使用
            self.logger.info(f"IP配置应用成功: {success_message}")
            
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
                self.main_window,
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
                self.main_window,
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
