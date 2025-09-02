# -*- coding: utf-8 -*-
"""
网络适配器事件处理器：负责网卡选择、切换、刷新相关的UI事件处理
"""

from PyQt5.QtWidgets import QMessageBox
from ....utils.logger import get_logger


class NetworkAdapterEvents:
    """
    网络适配器事件处理器
    
    负责处理网卡选择、切换、刷新等UI事件。
    专注于适配器相关的事件处理，符合单一职责原则。
    
    设计原则：
    - 单一职责：专门处理网络适配器相关的UI事件转换
    - 封装性：将适配器处理逻辑封装在独立方法中
    - 依赖倒置：依赖于服务层抽象接口，不依赖具体实现
    """
    
    def __init__(self, main_window, network_service=None):
        """
        初始化网络适配器事件处理器
        
        Args:
            main_window: 主窗口实例，用于访问UI组件
            network_service: 网络服务实例，用于调用业务逻辑（可以稍后设置）
        """
        self.main_window = main_window
        self.network_service = network_service
        self.logger = get_logger(__name__)
        
        # 初始化处理状态标志
        self._processing_selection = False
        
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
        print(f"NetworkAdapterEvents: 网络服务已设置 - {network_service is not None}")
        if self.network_service:
            self._connect_signals()
    
    def _connect_signals(self):
        """
        连接网络服务的适配器相关信号到事件处理方法
        """
        if not self.network_service:
            return
            
        # 连接适配器相关信号
        self.network_service.adapters_updated.connect(self._on_adapters_updated)
        self.network_service.adapter_selected.connect(self._on_adapter_selected)
        self.network_service.adapter_refreshed.connect(self._on_adapter_refreshed)
        
        self.logger.debug("NetworkAdapterEvents信号连接完成")
    
    def _on_adapter_combo_changed(self, display_name):
        """
        处理网卡下拉框选择变化事件
        
        当用户在网卡下拉框中选择不同的网卡时，这个方法负责处理选择变化事件。
        它会调用服务层的网卡选择方法，并更新状态栏显示当前操作状态。
        
        设计原则：
        - UI层职责：仅负责事件转换，不包含业务逻辑
        - 委托模式：将实际的网卡选择逻辑委托给服务层
        - 用户反馈：通过状态栏提供实时的操作状态反馈
        
        Args:
            display_name (str): 用户选择的网卡显示名称
        """
        try:
            # 防护机制：避免重复处理同一网卡选择
            if hasattr(self, '_processing_selection') and self._processing_selection:
                return
            self._processing_selection = True
            
            # 严格检查网络服务状态
            if not self.network_service:
                print("网络服务未初始化，跳过网卡选择处理")
                return
            
            # 获取网卡列表并进行严格的空值检查
            adapters = self.network_service.get_all_adapters()
            if not adapters or len(adapters) == 0:
                print("网卡列表为空或未获取到，跳过网卡选择处理")
                return
                
            # 通过display_name查找对应的adapter_id - 增强匹配逻辑
            adapter_id = None
            print(f"正在查找网卡: {display_name}")
            
            for adapter in adapters:
                # 多种匹配策略：friendly_name, name, description
                matches = [
                    hasattr(adapter, 'friendly_name') and adapter.friendly_name == display_name,
                    hasattr(adapter, 'name') and adapter.name == display_name,
                    hasattr(adapter, 'description') and adapter.description == display_name
                ]
                
                if any(matches):
                    adapter_id = adapter.id
                    print(f"匹配成功: {display_name} -> {adapter_id}")
                    break
                else:
                    # 调试信息：显示可用的网卡名称
                    friendly = getattr(adapter, 'friendly_name', 'N/A')
                    name = getattr(adapter, 'name', 'N/A')
                    desc = getattr(adapter, 'description', 'N/A')
                    print(f"  候选网卡: friendly='{friendly}', name='{name}', desc='{desc}'")
            
            if adapter_id:
                self.network_service.select_adapter(adapter_id)
                print(f"网卡选择成功: {display_name} -> {adapter_id}")
            else:
                print(f"未找到匹配的网卡: {display_name}")
                print(f"可用网卡数量: {len(adapters)}")
                
        except Exception as e:
            print(f"网卡选择处理异常: {str(e)}")
            # 在状态栏显示错误状态（如果可用）
            try:
                if hasattr(self.main_window, 'service_coordinator') and self.main_window.service_coordinator.status_bar_service:
                    self.main_window.service_coordinator.status_bar_service.set_status(
                        f"网卡切换失败: {str(e)}", 
                        auto_clear_seconds=5
                    )
            except:
                pass  # 避免状态栏更新失败影响主流程
        finally:
            # 重置处理状态标志
            self._processing_selection = False
    
    def _get_current_selected_adapter(self):
        """
        获取当前选中的网卡信息
        
        这个方法用于获取用户当前在UI中选择的网卡信息，主要用于其他事件处理方法
        中需要获取当前网卡上下文的场景。采用委托模式，将获取逻辑委托给服务层。
        
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
                self.logger.debug(f"获取当前网卡成功: {current_adapter.get('friendly_name', '未知')}")
            else:
                self.logger.debug("当前没有选中的网卡")
                
            return current_adapter
            
        except Exception as e:
            self.logger.error(f"获取当前网卡信息异常: {str(e)}")
            return None
    
    def _on_adapters_updated(self, adapters):
        """
        处理网卡列表更新信号
        
        当网络服务检测到系统中的网卡列表发生变化时，会发射此信号。
        这个方法负责更新UI中的网卡下拉框选项，确保用户看到最新的网卡列表。
        
        设计原则：
        - 响应式更新：自动响应系统网卡变化
        - UI同步：确保UI显示与系统状态保持一致
        - 异常安全：更新失败不影响主程序运行
        
        Args:
            adapters (list): 更新后的网卡列表
        """
        try:
            print(f"网卡列表已更新，共 {len(adapters)} 个网卡")
            
            # 这里可以添加UI更新逻辑
            # 例如更新网卡下拉框的选项列表
            # 当前版本通过日志记录，实际UI更新由主窗口负责
            
        except Exception as e:
            print(f"处理网卡列表更新异常: {str(e)}")
    
    def _on_adapter_selected(self, adapter_info):
        """
        处理网卡选择信号
        
        当服务层完成网卡选择操作后，会发射此信号通知UI层更新显示。
        这个方法负责处理网卡选择完成后的UI状态更新。
        
        设计原则：
        - 事件响应：响应服务层的网卡选择完成事件
        - UI更新：更新相关UI组件显示选中状态
        - 状态同步：确保UI状态与服务层状态保持一致
        
        Args:
            adapter_info: 选中的网卡信息对象
        """
        try:
            if adapter_info:
                adapter_name = getattr(adapter_info, 'friendly_name', '未知网卡')
                print(f"网卡选择完成: {adapter_name}")
            else:
                print("网卡选择完成，但未获取到网卡信息")
                
        except Exception as e:
            print(f"处理网卡选择信号异常: {str(e)}")
    
    def _on_adapter_refreshed(self, adapter_info):
        """
        处理网卡刷新完成信号
        
        当服务层完成网卡信息刷新操作后，会发射此信号通知UI层。
        这个方法负责处理网卡刷新完成后的UI反馈和状态更新。
        
        设计原则：
        - 事件响应：响应服务层的网卡刷新完成事件
        - 用户反馈：提供刷新操作的结果反馈
        - 状态更新：更新UI显示最新的网卡状态
        
        Args:
            adapter_info: 刷新后的网卡信息对象
        """
        try:
            if adapter_info:
                adapter_name = getattr(adapter_info, 'friendly_name', '未知网卡')
                print(f"网卡刷新完成: {adapter_name}")
                
                # 在状态栏显示刷新成功状态
                if hasattr(self.main_window, 'service_coordinator') and self.main_window.service_coordinator.status_bar_service:
                    self.main_window.service_coordinator.status_bar_service.set_status(
                        f"✅ {adapter_name} 信息已刷新", 
                        auto_clear_seconds=3
                    )
            else:
                print("网卡刷新完成，但未获取到网卡信息")
                
        except Exception as e:
            print(f"处理网卡刷新信号异常: {str(e)}")
