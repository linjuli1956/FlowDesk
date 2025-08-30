# -*- coding: utf-8 -*-
"""
网卡发现与枚举专用服务模块。这个文件在FlowDesk网络管理架构中扮演"硬件发现引擎"角色，专门负责从Windows系统中发现并枚举所有可用的网络适配器。
它解决了网卡信息获取效率和数据一致性问题，通过WMIC命令快速获取网卡基本信息，并实现智能优先级排序算法。
UI层通过连接此服务的信号接收网卡列表更新通知，其他网络服务依赖此服务提供的标准化网卡数据进行后续处理。该服务严格遵循单一职责原则，确保网卡发现逻辑的独立性和可测试性。
"""
import subprocess
import logging
from typing import List, Optional, Dict, Any

from .network_service_base import NetworkServiceBase
from ...models.adapter_info import AdapterInfo


class AdapterDiscoveryService(NetworkServiceBase):
    """
    网络适配器发现与枚举服务
    
    专门负责从Windows系统发现和枚举网络适配器的核心服务。
    此服务封装了网卡硬件发现逻辑，提供快速的网卡基本信息获取能力。
    
    主要功能：
    - 通过WMIC命令获取系统中所有网络适配器的基本信息
    - 实现智能优先级排序算法，确保已连接网卡优先显示
    - 提供轻量级网卡对象创建，优化启动性能
    - 缓存网卡列表，避免重复系统调用
    
    输入输出：
    - 输入：无需外部参数，直接从系统获取
    - 输出：排序后的AdapterInfo对象列表
    
    可能异常：
    - subprocess.CalledProcessError：WMIC命令执行失败
    - json.JSONDecodeError：WMIC输出格式解析错误
    - Exception：其他系统级异常
    """
    
    def __init__(self, parent=None):
        """
        初始化网络适配器发现服务
        
        Args:
            parent: PyQt父对象，用于内存管理
        """
        super().__init__(parent)
        
        # region 服务状态管理
        # 网卡列表缓存，避免频繁系统调用提升性能
        self._cached_adapters: List[AdapterInfo] = []
        self._cache_valid = False  # 缓存有效性标识
        # endregion
        
        self._log_operation_start("AdapterDiscoveryService初始化")
    
    # region 核心发现方法
    
    def discover_all_adapters(self) -> List[AdapterInfo]:
        """
        发现并返回所有网络适配器的快速枚举方法
        
        这是网卡发现服务的主入口方法，实现了高效的网卡枚举策略。
        采用"快速启动"理念：启动时只获取基本信息，详细配置按需加载。
        
        业务逻辑设计：
        - 启动时只获取网卡基本信息（名称、状态、MAC地址）
        - 详细IP配置采用按需加载，用户选择网卡时才获取
        - 减少系统命令调用次数，提升启动速度
        - 保持UI响应性，避免长时间阻塞
        
        面向对象设计：
        - 单一职责：专门负责网卡信息的快速获取和缓存管理
        - 开闭原则：支持后续扩展更多优化策略
        - 依赖倒置：通过信号机制与UI层解耦
        
        Returns:
            List[AdapterInfo]: 按优先级排序的网络适配器列表
            
        Raises:
            Exception: 网卡信息获取失败时抛出异常
        """
        try:
            self._log_operation_start("发现网络适配器", cache_valid=self._cache_valid)
            
            # 只获取网卡基本信息，大幅减少启动时间
            adapters_info = self._get_adapters_basic_info()
            
            # 创建轻量级适配器对象，不包含详细IP配置
            # 这样可以快速显示网卡列表，详细信息按需加载
            lightweight_adapters = []
            for adapter_basic in adapters_info:
                # 创建最小化的AdapterInfo对象，只包含必要的显示信息
                # 修复字段映射：使用正确的字典键名匹配wmic输出格式
                lightweight_adapter = AdapterInfo(
                    id=adapter_basic.get('GUID', ''),
                    name=adapter_basic.get('Name', ''),
                    friendly_name=adapter_basic.get('NetConnectionID', ''),
                    description=adapter_basic.get('Description', ''),
                    mac_address=adapter_basic.get('MACAddress', ''),
                    status=self._get_status_display(adapter_basic.get('NetConnectionStatus', '0')),
                    is_connected=adapter_basic.get('NetConnectionStatus', '0') == '2',
                    # 详细配置信息留空，按需加载
                    ip_addresses=[],
                    subnet_masks=[],
                    gateway='',
                    dns_servers=[],
                    dhcp_enabled=False,
                    ipv6_addresses=[]
                )
                lightweight_adapters.append(lightweight_adapter)
            
            # 智能排序网卡列表：连接的网卡优先显示
            # 这确保了UI显示顺序与服务层选择优先级完全一致
            # 解决启动时下拉框选中网卡与显示信息不匹配的根本问题
            sorted_adapters = self._sort_adapters_by_priority(lightweight_adapters)
            
            # 更新内部缓存
            self._cached_adapters = sorted_adapters
            self._cache_valid = True
            
            # 发射信号通知UI层快速更新
            self.adapters_updated.emit(self._cached_adapters)
            
            self._log_operation_success("发现网络适配器", f"共找到 {len(self._cached_adapters)} 个网卡")
            return self._cached_adapters
            
        except Exception as e:
            self._log_operation_error("发现网络适配器", e)
            self.operation_status.emit("网卡枚举错误", False)
            return []
    
    def find_adapter_by_id(self, adapter_id: str) -> Optional[AdapterInfo]:
        """
        根据GUID查找指定网络适配器
        
        Args:
            adapter_id: 网络适配器GUID标识符
            
        Returns:
            Optional[AdapterInfo]: 找到的适配器对象，未找到返回None
        """
        for adapter in self._cached_adapters:
            if adapter.id == adapter_id:
                return adapter
        return None
    
    def get_adapter_basic_info(self, adapter_id: str) -> Optional[Dict[str, str]]:
        """
        获取指定网卡的基本信息（为UI协调器提供的接口）
        
        Args:
            adapter_id: 网络适配器GUID标识符
            
        Returns:
            Optional[Dict[str, str]]: 网卡基本信息字典，未找到返回None
        """
        return self._find_adapter_basic_info(adapter_id)
    
    def invalidate_cache(self) -> None:
        """
        使网卡缓存失效，强制下次重新获取
        
        当网卡硬件变化或需要刷新时调用此方法。
        """
        self._cache_valid = False
        self._cached_adapters.clear()
    
    # endregion
    
    # region 私有实现方法
    
    def _get_adapters_basic_info(self) -> List[Dict[str, str]]:
        """
        使用WMIC获取网络适配器基本信息的底层方法
        
        恢复原始的WMIC命令和解析逻辑，确保网卡名称正确显示。
        使用win32_networkadapter表和CSV格式以保证与原始代码的兼容性。
        
        Returns:
            List[Dict[str, str]]: 网络适配器基本信息字典列表
            
        Raises:
            subprocess.CalledProcessError: WMIC命令执行失败
        """
        try:
            # 恢复原始的WMIC命令 - 使用win32_networkadapter表和CSV格式
            result = subprocess.run(
                ['wmic', 'path', 'win32_networkadapter', 'where', 'NetConnectionID is not null', 'get', 
                 'Name,Description,NetConnectionID,GUID,MACAddress,NetConnectionStatus', '/format:csv'],
                capture_output=True, text=True, timeout=30, encoding='cp936', errors='replace'
            )
            
            if result.returncode != 0:
                raise Exception(f"wmic命令执行失败: {result.stderr}")
            
            # 解析CSV输出并添加调试信息
            lines = result.stdout.strip().split('\n')
            self.logger.debug(f"WMIC原始输出行数: {len(lines)}")
            
            # 清理空行和无效行
            valid_lines = [line for line in lines if line.strip() and not line.startswith('Node,')]
            self.logger.debug(f"有效行数: {len(valid_lines)}")
            
            if len(valid_lines) < 1:
                return []
            
            # 手动解析，因为CSV格式可能不标准
            adapters = []
            for line in valid_lines:
                if not line.strip():
                    continue
                
                # 按逗号分割，但要处理可能的空字段
                parts = line.split(',')
                if len(parts) >= 6:  # 至少需要6个字段
                    # 提取字段：Node, Description, GUID, MACAddress, Name, NetConnectionID, NetConnectionStatus
                    node = parts[0].strip()
                    description = parts[1].strip() if len(parts) > 1 else ''
                    guid = parts[2].strip() if len(parts) > 2 else ''
                    mac_address = parts[3].strip() if len(parts) > 3 else ''
                    name = parts[4].strip() if len(parts) > 4 else ''
                    net_connection_id = parts[5].strip() if len(parts) > 5 else ''
                    net_connection_status = parts[6].strip() if len(parts) > 6 else '0'
                    
                    # 网卡过滤逻辑 - 包含所有网卡，包括禁用的网卡
                    # 禁用的网卡可能NetConnectionID为空，但仍需要在界面中显示
                    if description and description != '':  # 只要有描述信息就处理
                        # 对于禁用的网卡，使用Description作为显示名称
                        display_name = net_connection_id if net_connection_id else description
                        
                        adapter_dict = {
                            'Node': node,
                            'Description': description,
                            'GUID': guid,
                            'MACAddress': mac_address,
                            'Name': name,
                            'NetConnectionID': display_name,  # 使用显示名称确保禁用网卡也能显示
                            'NetConnectionStatus': net_connection_status
                        }
                        self.logger.debug(f"解析的网卡数据 (状态码: {net_connection_status}): {adapter_dict}")
                        adapters.append(adapter_dict)
            
            return adapters
            
        except subprocess.TimeoutExpired:
            self.logger.error("WMIC命令执行超时")
            raise Exception("获取网卡信息超时，请检查系统状态")
        except Exception as e:
            self.logger.error(f"获取网卡基本信息失败: {str(e)}")
            raise
    
    def _sort_adapters_by_priority(self, adapters: List[AdapterInfo]) -> List[AdapterInfo]:
        """
        按优先级智能排序网卡列表的核心排序方法
        
        这个方法解决了启动时网卡信息不匹配的根本问题，通过统一的排序逻辑
        确保UI显示顺序与服务层选择优先级完全一致。该方法体现了面向对象
        架构中业务逻辑封装的重要原则，将复杂的排序策略集中管理。
        
        面向对象架构特点：
        - 封装性：将复杂的网卡优先级排序逻辑完全封装在独立方法中
        - 单一职责：专门负责网卡列表的优先级排序，不涉及其他业务逻辑
        - 开闭原则：可以通过修改排序规则扩展功能，不影响调用方代码
        - 依赖倒置：依赖于AdapterInfo抽象数据模型，不依赖具体实现
        
        排序优先级策略：
        1. 已连接的网卡优先级最高（is_connected=True）
        2. 已连接网卡内部按友好名称字母序排序
        3. 未连接的网卡排在后面（is_connected=False）
        4. 未连接网卡内部按友好名称字母序排序
        
        这样确保了用户最常使用的连接网卡始终显示在下拉框顶部，
        同时保持了相同状态网卡之间的稳定排序，提供一致的用户体验。
        
        Args:
            adapters (List[AdapterInfo]): 未排序的AdapterInfo对象列表
            
        Returns:
            List[AdapterInfo]: 按优先级排序后的AdapterInfo对象列表
        """
        try:
            # 使用Python内置的sorted函数进行多级排序
            # key函数返回元组，Python会按元组元素顺序进行排序
            sorted_adapters = sorted(adapters, key=lambda adapter: (
                # 第一级排序：连接状态（False排在True前面，所以用not取反）
                # 这样is_connected=True的网卡会排在前面
                not adapter.is_connected,
                
                # 第二级排序：友好名称字母序（相同连接状态内部排序）
                # 使用lower()确保大小写不敏感的排序
                (adapter.friendly_name or adapter.name or adapter.description or "").lower()
            ))
            
            # 记录排序结果便于调试和监控
            connected_count = sum(1 for a in sorted_adapters if a.is_connected)
            self.logger.debug(f"网卡排序完成：已连接 {connected_count} 个，未连接 {len(sorted_adapters) - connected_count} 个")
            
            return sorted_adapters
            
        except Exception as e:
            # 异常处理：排序失败时返回原列表，确保功能不受影响
            self.logger.error(f"网卡排序失败，使用原始顺序: {str(e)}")
            return adapters
    
    def _find_adapter_basic_info(self, adapter_id: str) -> Optional[Dict[str, str]]:
        """
        根据网卡GUID查找基本信息的核心匹配方法（直接复制backup文件逻辑）
        
        这个方法实现了网卡信息检索的核心逻辑，通过GUID精确匹配网卡。
        重新获取最新的网卡基本信息，确保数据时效性，然后从中找到匹配项。
        
        Args:
            adapter_id (str): 网卡GUID标识符
            
        Returns:
            Optional[Dict[str, str]]: 匹配的网卡基本信息字典，未找到返回None
        """
        try:
            # 重新获取最新的网卡基本信息，确保数据的实时性和准确性
            # 这是解决"刷新时找不到网卡"问题的关键步骤
            basic_adapters = self._get_adapters_basic_info()
            
            # 遍历所有网卡，使用GUID进行精确匹配
            # GUID是网卡的唯一标识符，比Index或Name更可靠
            for adapter in basic_adapters:
                # 关键修复：使用GUID字段进行匹配，而不是Index字段
                # 这解决了刷新时"未找到网卡基本信息"的核心问题
                if adapter.get('GUID') == adapter_id:
                    self.logger.debug(f"成功找到网卡基本信息: {adapter.get('NetConnectionID', 'Unknown')}")
                    return adapter
            
            # 如果没有找到匹配的网卡，记录调试信息帮助排查问题
            self.logger.warning(f"未找到GUID为 {adapter_id} 的网卡基本信息")
            return None
            
        except Exception as e:
            # 异常安全处理，确保方法调用不会导致系统崩溃
            self.logger.error(f"查找网卡基本信息时发生异常: {str(e)}")
            return None
    
    def _get_status_display(self, status_code: str) -> str:
        """
        将WMIC网卡状态码转换为用户友好的状态显示文本
        
        Windows网络连接状态码映射表，提供标准化的状态文本显示。
        这个方法封装了Windows网卡状态码的业务逻辑，便于维护和修改。
        
        Args:
            status_code (str): WMIC返回的NetConnectionStatus数值字符串
            
        Returns:
            str: 用户友好的状态描述文本
        """
        # Windows网络连接状态码标准映射表
        # 参考：https://docs.microsoft.com/en-us/windows/win32/cimwin32prov/win32-networkadapter
        status_map = {
            '0': '已断开连接',      # Disconnected
            '1': '正在连接',        # Connecting  
            '2': '已连接',          # Connected
            '3': '正在断开连接',    # Disconnecting
            '4': '硬件不存在',      # Hardware not present
            '5': '硬件已禁用',      # Hardware disabled
            '6': '硬件故障',        # Hardware malfunction
            '7': '媒体断开连接',    # Media disconnected
            '8': '正在验证身份',    # Authenticating
            '9': '验证成功',        # Authentication succeeded
            '10': '验证失败',       # Authentication failed
            '11': '地址无效',       # Invalid address
            '12': '凭据需要'        # Credentials required
        }
        
        # 返回映射的状态文本，未知状态码返回默认值
        return status_map.get(status_code, '未知状态')
    
    # endregion
