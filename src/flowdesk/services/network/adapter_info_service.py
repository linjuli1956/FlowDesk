# -*- coding: utf-8 -*-
"""
网卡详细信息获取服务｜重构后的轻量级协调器，委托给专业组件处理
"""
from typing import Dict, Any, Optional

from .network_service_base import NetworkServiceBase
from .adapter_info_retriever import AdapterInfoRetriever
from ...models import AdapterInfo


class AdapterInfoService(NetworkServiceBase):
    """
    网络适配器详细信息获取服务｜轻量级协调器
    
    重构后的轻量级协调器，委托给AdapterInfoRetriever处理具体业务逻辑。
    保持原有公共API接口不变，确保向后兼容性。
    
    主要功能：
    - 委托AdapterInfoRetriever获取网卡详细信息
    - 保持原有API接口向后兼容
    - 提供轻量级服务协调
    
    重构优势：
    - 模块化设计，职责分离
    - 降低代码复杂度
    - 提高可维护性
    """
    
    def __init__(self, discovery_service=None):
        """
        初始化网卡详细信息服务
        
        Args:
            discovery_service: 网卡发现服务实例，用于获取基础信息
        """
        super().__init__()
        # 创建专业的信息获取器
        self._retriever = AdapterInfoRetriever(discovery_service)
        self.logger.info("网卡详细信息服务已初始化（轻量级协调器模式）")
    
    # region 核心信息获取方法
    
    def get_adapter_detailed_info(self, adapter_id: str) -> Optional[AdapterInfo]:
        """
        获取网络适配器详细信息的主入口方法
        
        这个方法是获取网卡完整信息的核心入口，整合了多个数据源的信息获取能力。
        基于网卡GUID，首先获取基本信息，再进一步获取IP配置、DNS设置等详细信息，
        构造完整的AdapterInfo对象。
        
        技术架构特点：
        - 多重数据源：结合netsh和ipconfig命令的优势
        - 增强DNS获取：使用专门的DNS配置获取逻辑
        - 状态精确判断：结合管理状态和连接状态的双重判断
        - 完整对象构造：创建包含所有必要信息的AdapterInfo对象
        
        Args:
            adapter_id (str): 网卡GUID标识符
            
        Returns:
            Optional[AdapterInfo]: 完整的网卡信息对象，失败时返回None
        """
        try:
            # 委托给专业的信息获取器处理
            return self._retriever.get_adapter_detailed_info(adapter_id)
            
        except Exception as e:
            self._log_operation_error("获取网卡详细信息", e)
            return None
    
    def get_adapter_ip_config(self, adapter_name: str) -> Dict[str, Any]:
        """
        获取指定网卡IP配置信息｜委托给专业组件处理
        
        Args:
            adapter_name (str): 网卡连接名称
            
        Returns:
            Dict[str, Any]: 包含完整IP配置信息的字典
        """
        return self._retriever.get_adapter_ip_config(adapter_name)
    
    # endregion
