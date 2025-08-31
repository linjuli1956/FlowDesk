# -*- coding: utf-8 -*-
"""
UI状态更新管理器：负责服务层信号触发的UI更新逻辑
"""

from PyQt5.QtWidgets import QApplication
from ...utils.logger import get_logger


class UIStateManager:
    """
    UI状态更新管理器
    
    负责服务层信号触发的UI更新逻辑，将服务层传递的数据
    转换为UI层可以显示的格式并更新相应的界面组件。
    
    设计原则：
    - 单一职责：专门处理UI状态更新逻辑
    - 封装性：将UI更新逻辑封装在独立方法中
    - 数据流单向性：只接收服务层数据，不进行业务逻辑处理
    """
    
    def __init__(self, main_window):
        """
        初始化UI状态管理器
        
        Args:
            main_window: 主窗口实例，用于访问UI组件
        """
        self.main_window = main_window
        self.logger = get_logger(__name__)
    
    def _on_adapters_updated(self, adapters):
        """
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
            self.main_window.network_config_tab.update_adapter_list_with_mapping(adapters)
            
            # 记录成功操作的详细信息，便于系统监控和问题排查
            self.logger.debug(f"网卡列表更新完成：成功加载 {len(adapters)} 个网络适配器到下拉框")
            
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
            self.main_window.network_config_tab.update_current_adapter_label(adapter_info.friendly_name)
            
            # 状态徽章更新已由Service层通过status_badges_updated信号直接处理
            # UI层不再包含任何状态判断逻辑
            self.logger.debug("状态徽章更新由Service层直接处理，UI层跳过业务逻辑")
            
            # 构建并更新IP信息展示区域
            # 这是解决"IP信息展示容器不更新"问题的关键代码
            if hasattr(self.main_window, 'network_service') and self.main_window.network_service:
                formatted_info = self.main_window.network_service._ui_coordinator.format_adapter_info_for_display(adapter_info)
                self.main_window.network_config_tab.update_ip_info_display(formatted_info)
            
            # 记录网卡选择操作的完成状态，便于系统监控和调试
            self.logger.debug(f"网卡选择界面更新完成: {adapter_info.friendly_name}")
            
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
            detailed_info = getattr(aggregated_info, 'detailed_info', None)
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
            
            self.logger.debug(f"网卡信息UI更新完成: {getattr(detailed_info, 'name', '未知网卡')}")
            
        except Exception as e:
            self.logger.error(f"网卡信息更新处理失败: {str(e)}")
            import traceback
            self.logger.error(f"异常堆栈: {traceback.format_exc()}")

    def _update_status_badges_from_info(self, detailed_info):
        """
        已废弃：状态徽章更新现在由Service层直接处理
        
        Service层通过status_badges_updated信号直接发送格式化好的显示文本，
        UI层不再需要进行任何业务逻辑判断。
        
        Args:
            detailed_info: 网卡详细信息对象（已不使用）
        """
        # 此方法已被Service层的status_badges_updated信号替代
        # UI层不再处理任何状态判断逻辑
        self.logger.debug("状态徽章更新已由Service层直接处理，跳过UI层处理")
    
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
            if hasattr(self.main_window, 'network_service') and self.main_window.network_service:
                formatted_info = self.main_window.network_service._ui_coordinator.format_adapter_info_for_display(detailed_info)
                
                # 更新IP信息展示区域
                self.main_window.network_config_tab.update_ip_info_display(formatted_info)
                
                self.logger.debug("IP信息展示区域已更新")
            
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
            # 直接传递IPConfigInfo对象到UI层，符合架构规范
            # UI层只接收数据对象，不进行业务逻辑处理
            self.logger.debug(f"[调试] 准备更新IP配置输入框，IPConfigInfo对象: {ip_config}")
            self.main_window.network_config_tab.update_ip_config_inputs(ip_config)
            self.logger.debug(f"[调试] IP配置输入框更新完成")
            
            # 记录IP配置更新的成功状态，便于系统监控和调试
            self.logger.debug(f"IP配置界面更新完成: {ip_config.ip_address or '无IP地址'}")
            
        except Exception as e:
            # 异常处理：确保IP配置更新错误不影响其他功能
            # 记录详细错误信息便于开发人员快速定位和解决问题
            self.logger.error(f"IP配置界面更新失败，错误详情: {str(e)}")
            # 在生产环境中，这里应该向用户显示友好的错误提示
    
    def _on_extra_ips_updated(self, extra_ips):
        """
        处理额外IP列表更新信号
        
        当服务层解析额外IP完成后，更新右侧额外IP列表显示。
        
        Args:
            extra_ips (list): ExtraIP对象列表
        """
        try:
            # 检查数据类型并相应处理
            if extra_ips and isinstance(extra_ips[0], str):
                # 如果接收到的是字符串列表（格式："ip/mask"），直接使用
                ip_list = extra_ips
                self.logger.debug(f"接收到字符串格式的额外IP列表: {ip_list}")
            else:
                # 如果接收到的是ExtraIP对象列表，格式化为字符串
                ip_list = []
                for extra_ip in extra_ips:
                    if hasattr(extra_ip, 'ip_address') and hasattr(extra_ip, 'subnet_mask'):
                        ip_info = f"{extra_ip.ip_address}/{extra_ip.subnet_mask}"
                        ip_list.append(ip_info)
                self.logger.debug(f"格式化ExtraIP对象为字符串列表: {ip_list}")
            
            # 更新额外IP列表
            self.main_window.network_config_tab.update_extra_ip_list(ip_list)
            
            self.logger.debug(f"额外IP列表已更新，共 {len(extra_ips)} 个")
            
        except Exception as e:
            self.logger.error(f"更新额外IP列表失败: {str(e)}")
            import traceback
            self.logger.error(f"异常堆栈: {traceback.format_exc()}")
    
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
            self.main_window.network_config_tab.update_current_adapter_label(adapter_info.friendly_name)
            
            # 状态徽章更新已由Service层通过status_badges_updated信号直接处理
            # UI层不再包含任何状态判断逻辑
            self.logger.debug("刷新时状态徽章更新由Service层直接处理，UI层跳过业务逻辑")
            
            # 构建并更新IP信息展示区域 - 这是修复刷新问题的关键代码
            # 确保刷新操作后用户能够看到最新的网卡配置信息
            if hasattr(self.main_window, 'network_service') and self.main_window.network_service:
                formatted_info = self.main_window.network_service._ui_coordinator.format_adapter_info_for_display(adapter_info)
                self.main_window.network_config_tab.update_ip_info_display(formatted_info)
            
            # 记录刷新操作的成功完成状态，便于系统监控和调试
            self.logger.debug(f"网卡刷新界面更新完成: {adapter_info.friendly_name}")
            
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
            # 实际复制到剪贴板
            clipboard = QApplication.clipboard()
            clipboard.setText(copied_text)
            
            # 显示复制成功提示
            self.logger.info("网卡信息已复制到剪贴板")
            
        except Exception as e:
            self.logger.error(f"处理信息复制信号失败: {str(e)}")
    
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
            self.main_window.network_config_tab.adapter_combo.blockSignals(True)
            
            # 遍历下拉框中的所有选项，寻找与当前网卡匹配的项目
            combo_box = self.main_window.network_config_tab.adapter_combo
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
            self.main_window.network_config_tab.adapter_combo.blockSignals(False)
