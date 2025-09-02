# -*- coding: utf-8 -*-
"""
网络状态事件处理器：负责网络状态显示、错误反馈、操作进度相关的UI事件处理
"""

from PyQt5.QtWidgets import QMessageBox
from ....utils.logger import get_logger
from ...dialogs.operation_result_dialog import OperationResultDialog


class NetworkStatusEvents:
    """
    网络状态事件处理器
    
    负责处理网络状态显示、错误反馈、操作进度更新等UI事件。
    专注于状态相关的事件处理，符合单一职责原则。
    
    设计原则：
    - 单一职责：专门处理网络状态相关的UI事件转换
    - 封装性：将状态处理逻辑封装在独立方法中
    - 依赖倒置：依赖于服务层抽象接口，不依赖具体实现
    """
    
    def __init__(self, main_window, network_service=None):
        """
        初始化网络状态事件处理器
        
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
        连接网络服务的状态相关信号到事件处理方法
        """
        if not self.network_service:
            return
            
        # 连接状态相关信号
        self.network_service.network_info_copied.connect(self._on_network_info_copied)
        self.network_service.error_occurred.connect(self._on_network_error)
        self.network_service.adapter_info_updated.connect(self._on_adapter_info_updated_for_status_bar)
        self.network_service.operation_completed.connect(self._on_operation_completed)
        
        self.logger.debug("NetworkStatusEvents信号连接完成")
    
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
                self.logger.debug(f"状态栏已更新网卡切换最终状态: {status_message}")
            else:
                self.logger.error("无法访问状态栏服务")
            
        except Exception as e:
            self.logger.error(f"更新网卡切换状态栏时发生异常: {str(e)}")
    
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
            # 记录操作进度的详细信息（避免日志递归）
            print(f"操作进度: {progress_message}")
            
            # 这里可以添加用户友好的进度提示逻辑
            # 例如进度条、状态栏消息、加载动画等
            # 当前版本通过日志记录，后续版本可扩展UI进度显示
            
        except Exception as e:
            print(f"网卡选择处理异常: {str(e)}")  # 避免日志递归
    
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
