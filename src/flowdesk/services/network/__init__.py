# -*- coding: utf-8 -*-
"""
FlowDesk网络服务模块导出

这个__init__.py文件是FlowDesk网络管理架构的统一导出入口，负责向外部提供所有网络相关的服务类和组件。
它解决了模块化架构中的导入复杂性问题，通过统一的导出接口简化了其他模块对网络服务的使用。
外部模块可以通过简单的导入语句获取所需的网络服务组件，而无需了解内部的模块结构细节。
该导出模块严格遵循Python模块化设计原则，提供清晰的API边界和版本控制。
"""

# 公共基类和信号定义
from .network_service_base import NetworkServiceBase

# 专业服务模块
from .adapter_discovery_service import AdapterDiscoveryService
from .adapter_info_service import AdapterInfoService
from .adapter_status_service import AdapterStatusService
from .adapter_performance_service import AdapterPerformanceService
from .ip_configuration_service import IPConfigurationService
from .extra_ip_management_service import ExtraIPManagementService
from .network_ui_coordinator_service import NetworkUICoordinatorService

# 拆分后的专业组件
from .adapter_info_retriever import AdapterInfoRetriever
from .adapter_status_analyzer import AdapterStatusAnalyzer
from .adapter_config_parser import AdapterConfigParser
from .adapter_dns_enhancer import AdapterDnsEnhancer
from .adapter_info_utils import get_interface_type, prefix_to_netmask

# 兼容门面（主要对外接口）
from .network_service import NetworkService

# 模块版本信息
__version__ = "2.0.0"
__author__ = "FlowDesk Team"
__description__ = "FlowDesk网络管理服务模块 - 模块化重构版本"

# 公开导出的类列表
__all__ = [
    # 基类
    'NetworkServiceBase',
    
    # 专业服务类
    'AdapterDiscoveryService',
    'AdapterInfoService', 
    'AdapterStatusService',
    'AdapterPerformanceService',
    'IPConfigurationService',
    'ExtraIPManagementService',
    'NetworkUICoordinatorService',
    
    # 拆分后的专业组件
    'AdapterInfoRetriever',
    'AdapterStatusAnalyzer',
    'AdapterConfigParser',
    'AdapterDnsEnhancer',
    'get_interface_type',
    'prefix_to_netmask',
    
    # 主要对外接口
    'NetworkService',
]

# 模块初始化日志
import logging
logger = logging.getLogger(__name__)
logger.debug(f"FlowDesk网络服务模块已加载 - 版本 {__version__}")
logger.debug(f"可用服务类数量: {len(__all__)}")

# 向后兼容性说明
"""
向后兼容性指南：

对于现有代码，推荐的导入方式：
```python
# 推荐：使用兼容门面（完全向后兼容）
from flowdesk.services.network import NetworkService
network_service = NetworkService()

# 高级：直接使用专业服务（需要手动协调）
from flowdesk.services.network import (
    AdapterDiscoveryService,
    AdapterInfoService,
    NetworkUICoordinatorService
)
```

迁移建议：
1. 现有UI代码无需修改，继续使用NetworkService
2. 新功能开发可考虑直接使用专业服务
3. 大型重构时可逐步切换到专业服务架构

兼容性保证：
- NetworkService保持与原有接口100%兼容
- 所有原有方法签名和返回值保持不变
- 所有原有信号名称和参数保持一致
"""

# 依赖关系图
"""
模块依赖关系：

NetworkService (门面)
├── NetworkUICoordinatorService (协调器)
│   ├── AdapterDiscoveryService (网卡发现)
│   ├── AdapterInfoService (详细信息)
│   ├── AdapterStatusService (状态判断)
│   ├── AdapterPerformanceService (性能监控)
│   ├── IPConfigurationService (IP配置)
│   └── ExtraIPManagementService (额外IP管理)
└── NetworkServiceBase (公共基类)

所有服务继承自 NetworkServiceBase，共享：
- 统一的PyQt信号定义
- 标准化的日志记录机制
- 一致的异常处理模式
- 通用的操作状态追踪
"""
