# -*- coding: utf-8 -*-
"""

网卡状态判断专用服务模块。这个文件在FlowDesk网络管理架构中扮演"状态检测器"角色，专门负责精确判断网络适配器的连接和管理状态。
它解决了网卡状态信息不准确的问题，通过双重状态判断机制（netsh命令获取管理状态和连接状态，wmic状态码作为备用）确保状态判断的准确性。
UI层依赖此服务提供的状态信息来正确显示网卡状态徽章和连接指示，其他网络服务通过此模块获得可靠的网卡可用性判断。该服务严格遵循单一职责原则，将复杂的状态判断逻辑完全封装。
"""
import subprocess
import re
from typing import Dict, Tuple, Optional

from flowdesk.utils.logger import get_logger
from flowdesk.models import AdapterStatusInfo
from .network_service_base import NetworkServiceBase


class AdapterStatusService(NetworkServiceBase):
    """
    网络适配器状态判断服务
    
    专门负责网络适配器状态精确判断的核心服务。
    此服务实现了双重状态判断机制，确保状态信息的准确性。
    
    主要功能：
    - 通过netsh命令获取网卡管理状态和连接状态
    - 实现双重状态判断逻辑，区分启用状态和连接状态
    - 提供wmic状态码作为备用状态判断方案
    - 支持中英文Windows系统的状态解析
    
    输入输出：
    - 输入：网卡友好名称或基本信息
    - 输出：最终状态文本、启用标识、连接标识
    
    可能异常：
    - subprocess.CalledProcessError：状态查询命令执行失败
    - Exception：状态解析错误或系统调用异常
    """
    
    def __init__(self, parent=None):
        """
        初始化网络适配器状态判断服务
        
        Args:
            parent: PyQt父对象，用于内存管理
        """
        super().__init__(parent)
        # 初始化发现服务依赖，用于GUID到连接名称的转换
        from .adapter_discovery_service import AdapterDiscoveryService
        self._discovery_service = AdapterDiscoveryService(self)
        self._log_operation_start("AdapterStatusService初始化")
    
    # region 核心状态判断方法
    
    def get_adapter_status(self, adapter_id_or_name: str, backup_status_code: str = '0') -> Tuple[str, bool, bool]:
        """
        获取网络适配器完整状态信息的主入口方法
        
        这个方法是状态判断服务的核心入口，实现了完整的双重状态判断策略。
        首先尝试使用netsh命令获取精确的状态信息，如果失败则回退到wmic状态码。
        
        双重判断机制：
        1. 首选：netsh命令获取管理状态和连接状态，支持中英文解析
        2. 备用：wmic状态码解析，确保兼容性和可用性
        3. 状态合成：基于双重状态信息生成最终显示状态
        
        Args:
            adapter_id_or_name (str): 网卡GUID或友好名称，如"{GUID}"或"WLAN"
            backup_status_code (str): 备用的wmic状态码，默认为'0'
            
        Returns:
            Tuple[str, bool, bool]: 包含三个元素的元组：
                - final_status (str): 最终显示状态文本
                - is_enabled (bool): 网卡是否启用
                - is_connected (bool): 网卡是否已连接
        """
        try:
            # 检查传入的是GUID还是连接名称
            if adapter_id_or_name.startswith('{') and adapter_id_or_name.endswith('}'):
                # 是GUID，需要转换为连接名称
                basic_info = self._discovery_service.get_adapter_basic_info(adapter_id_or_name)
                if basic_info and basic_info.get('NetConnectionID'):
                    adapter_name = basic_info['NetConnectionID']
                else:
                    self.logger.warning(f"无法从GUID获取连接名称: {adapter_id_or_name}")
                    adapter_name = adapter_id_or_name
            else:
                # 已经是连接名称
                adapter_name = adapter_id_or_name
                
            self._log_operation_start("获取网卡状态", adapter_name=adapter_name)
            
            # 第一步：尝试使用netsh命令获取精确状态
            interface_status = self._get_interface_status_info(adapter_name)
            
            # 第二步：应用双重状态判断逻辑
            if interface_status['admin_status'] != '未知' or interface_status['connect_status'] != '未知':
                # netsh命令获取成功，使用精确状态判断
                final_status, is_enabled, is_connected = self._determine_final_status(
                    interface_status['admin_status'], 
                    interface_status['connect_status']
                )
                self.logger.debug(f"网卡 {adapter_name} 精确状态分析: 管理状态={interface_status['admin_status']}, 连接状态={interface_status['connect_status']}, 最终状态={final_status}")
            else:
                # 第三步：netsh获取失败，使用备用wmic状态码方案
                self.logger.info(f"网卡 {adapter_name} netsh状态获取失败，使用wmic状态码作为备用方案")
                final_status, is_enabled, is_connected = self._parse_wmic_status_code(backup_status_code, adapter_name)
            
            self._log_operation_success("获取网卡状态", f"网卡 {adapter_name}: {final_status}")
            return final_status, is_enabled, is_connected
            
        except Exception as e:
            self._log_operation_error("获取网卡状态", e)
            # 异常情况下返回安全的默认状态
            return '未知状态', False, False
    
    def get_interface_status_info(self, adapter_name: str) -> Dict[str, str]:
        """
        获取网卡接口状态信息的公开方法
        
        Args:
            adapter_name: 网卡友好名称
            
        Returns:
            Dict[str, str]: 包含admin_status和connect_status的状态字典
        """
        return self._get_interface_status_info(adapter_name)
    
    def determine_final_status(self, admin_status: str, connect_status: str) -> Tuple[str, bool, bool]:
        """
        基于管理状态和连接状态确定最终状态的公开方法
        
        Args:
            admin_status: 管理状态
            connect_status: 连接状态
            
        Returns:
            Tuple[str, bool, bool]: 最终状态、启用标识、连接标识
        """
        return self._determine_final_status(admin_status, connect_status)
    
    # endregion
    
    # region 私有实现方法
    
    def _get_interface_status_info(self, adapter_name: str) -> Dict[str, str]:
        """
        使用netsh命令获取网卡接口状态信息的核心实现
        
        这个方法通过netsh interface show interface命令获取网卡的精确状态信息。
        相比wmic状态码，netsh提供了更详细的管理状态和连接状态区分，
        能够准确反映网卡的真实工作状态。
        
        技术实现：
        - 执行netsh interface show interface命令获取所有接口状态
        - 使用多种匹配策略查找目标网卡（完全匹配、包含匹配、反向匹配）
        - 解析状态行格式：管理状态 连接状态 类型 接口名称
        - 支持中英文Windows系统的状态文本解析
        
        Args:
            adapter_name (str): 网卡友好名称，如"vEthernet (泰兴)"
            
        Returns:
            Dict[str, str]: 包含以下键的状态信息字典：
                - admin_status: 管理状态（已启用/已禁用/未知）
                - connect_status: 连接状态（已连接/已断开连接/未知）
        """
        # 初始化状态信息，默认为未知状态
        status_info = AdapterStatusInfo(
            admin_status='未知',
            connect_status='未知',
            interface_name=''
        )
        
        try:
            # 执行netsh命令获取所有网络接口的状态信息
            # 这个命令返回系统中所有网络接口的详细状态表格
            result = subprocess.run(
                ['netsh', 'interface', 'show', 'interface'],
                capture_output=True, text=True, timeout=10, encoding='gbk', errors='ignore'
            )
            
            if result.returncode == 0:
                output = result.stdout
                self.logger.debug(f"netsh命令执行成功，输出行数: {len(output.splitlines())}")
                
                # 解析netsh输出的状态表格
                # 典型输出格式：
                # 管理状态     状态          类型             接口名称
                # --------------------------------------------------------------------------------
                # 已启用       已连接        专用             以太网
                # 已禁用       已断开连接    专用             WLAN
                
                for line in output.split('\n'):
                    line = line.strip()
                    if not line or '---' in line or '管理状态' in line or 'Admin State' in line:
                        continue  # 跳过空行、分隔线和表头
                    
                    # 将状态行按空格分割，但要处理接口名称可能包含空格的情况
                    line_parts = line.split()
                    if len(line_parts) >= 4:  # 至少需要4个部分：管理状态 连接状态 类型 接口名称
                        # 提取接口名称（可能包含多个单词，所以从第4个部分开始合并）
                        interface_name = ' '.join(line_parts[3:])
                        
                        # 多种匹配策略：完全匹配、包含匹配、反向包含匹配
                        if (adapter_name == interface_name or 
                            adapter_name in interface_name or 
                            interface_name in adapter_name):
                            
                            # 解析状态行的格式：管理状态 状态 类型 接口名称
                            # 典型格式："已启用     已连接     专用         以太网"
                            admin_status_raw = line_parts[0].strip()      # 管理状态
                            connect_status_raw = line_parts[1].strip()    # 连接状态
                            
                            # 解析管理状态（第一列）- 网卡是否被启用
                            admin_status = '未知'
                            if '已启用' in admin_status_raw or 'Enabled' in admin_status_raw:
                                admin_status = '已启用'
                            elif '已禁用' in admin_status_raw or 'Disabled' in admin_status_raw:
                                admin_status = '已禁用'
                            
                            # 解析连接状态（第二列）- 网卡是否已连接
                            connect_status = '未知'
                            if '已连接' in connect_status_raw or 'Connected' in connect_status_raw:
                                connect_status = '已连接'
                            elif '已断开连接' in connect_status_raw or 'Disconnected' in connect_status_raw or '未连接' in connect_status_raw or 'Not connected' in connect_status_raw:
                                connect_status = '已断开连接'
                            
                            # 创建新的状态信息实例
                            status_info = AdapterStatusInfo(
                                admin_status=admin_status,
                                connect_status=connect_status,
                                interface_name=interface_name
                            )
                            
                            self.logger.debug(f"网卡 {adapter_name} 状态解析成功: 管理状态={status_info.admin_status}, 连接状态={status_info.connect_status}")
                            break
                else:
                    # 如果没有找到匹配的网卡，记录警告信息
                    self.logger.warning(f"在netsh interface show interface输出中未找到网卡: {adapter_name}")
            else:
                # 命令执行失败时的错误处理
                self.logger.error(f"netsh interface show interface命令执行失败: {result.stderr}")
                
        except Exception as e:
            # 异常安全处理，确保方法调用不会导致系统崩溃
            self.logger.error(f"获取网卡 {adapter_name} 状态信息时发生异常: {str(e)}")
        
        return status_info
    
    def _determine_final_status(self, admin_status: str, connect_status: str) -> Tuple[str, bool, bool]:
        """
        基于管理状态和连接状态确定网卡的最终状态
        
        这个方法实现了双重状态判断逻辑，遵循面向对象架构的单一职责原则。
        通过组合分析网卡的管理状态（启用/禁用）和连接状态（连接/断开），
        得出用户界面显示的最终状态和相应的布尔标志。
        
        判断逻辑：
        1. 已禁用 → 最终状态：已禁用，is_enabled=False, is_connected=False
        2. 已启用 + 已连接 → 最终状态：已连接，is_enabled=True, is_connected=True
        3. 已启用 + 已断开连接 → 最终状态：未连接，is_enabled=True, is_connected=False
        4. 其他情况 → 最终状态：未知状态，is_enabled=False, is_connected=False
        
        Args:
            admin_status (str): 管理状态（已启用/已禁用/未知）
            connect_status (str): 连接状态（已连接/已断开连接/未知）
            
        Returns:
            Tuple[str, bool, bool]: 包含三个元素的元组：
                - final_status (str): 最终显示状态
                - is_enabled (bool): 网卡是否启用
                - is_connected (bool): 网卡是否已连接
        """
        # 第一层判断：检查管理状态（网卡是否被用户或系统启用）
        if admin_status == '已禁用':
            # 网卡被禁用时，无论连接状态如何，都视为禁用状态
            final_status = '已禁用'
            is_enabled = False
            is_connected = False
            self.logger.debug(f"状态判断结果: 网卡已禁用")
            
        elif admin_status == '已启用':
            # 网卡已启用时，需要进一步判断连接状态
            is_enabled = True
            
            # 第二层判断：检查连接状态（网卡是否实际连接到网络）
            if connect_status == '已连接':
                # 已启用且已连接：网卡正常工作，可以传输数据
                final_status = '已连接'
                is_connected = True
                self.logger.debug(f"状态判断结果: 网卡已启用且已连接")
                
            elif connect_status == '已断开连接':
                # 已启用但未连接：网卡启用但无网络连接（如网线未插、WiFi未连接）
                final_status = '未连接'
                is_connected = False
                self.logger.debug(f"状态判断结果: 网卡已启用但未连接")
                
            else:
                # 连接状态未知：无法确定具体连接情况
                final_status = '未知状态'
                is_connected = False
                self.logger.debug(f"状态判断结果: 网卡已启用但连接状态未知")
        else:
            # 管理状态未知：无法确定网卡的基本启用状态
            final_status = '未知状态'
            is_enabled = False
            is_connected = False
            self.logger.debug(f"状态判断结果: 网卡管理状态未知")
        
        return final_status, is_enabled, is_connected
    
    def _parse_wmic_status_code(self, status_code: str, adapter_name: str = '') -> Tuple[str, bool, bool]:
        """
        解析wmic网卡状态码的备用状态判断方法
        
        当netsh命令获取状态失败时，使用这个方法作为备用方案。
        基于Windows系统的标准网卡状态码进行状态判断。
        
        Args:
            status_code (str): wmic返回的NetConnectionStatus状态码
            adapter_name (str): 网卡名称，用于特殊处理和日志记录
            
        Returns:
            Tuple[str, bool, bool]: 最终状态、启用标识、连接标识
        """
        try:
            self._log_operation_start("解析wmic状态码", status_code=status_code, adapter_name=adapter_name)
            
            # Windows网络连接状态码标准映射表
            # 参考：https://docs.microsoft.com/en-us/windows/win32/cimwin32prov/win32-networkadapter
            status_map = {
                '0': '已禁用',        # 网卡被用户或系统禁用
                '1': '正在连接',      # 网卡正在尝试建立连接
                '2': '已连接',        # 网卡已成功连接到网络
                '3': '正在断开',      # 网卡正在断开连接过程中
                '4': '已禁用',        # 修复：WLAN禁用时也返回状态码4，应显示为已禁用
                '5': '硬件已禁用',    # 网卡硬件被禁用（通常在设备管理器中）
                '6': '硬件故障',      # 网卡硬件出现故障
                '7': '媒体断开',      # 网线未连接或无线信号断开
                '8': '正在验证',      # 网卡正在进行身份验证
                '9': '验证失败',      # 网络身份验证失败
                '10': '验证成功',     # 网络身份验证成功
                '11': '正在获取地址'  # 网卡正在通过DHCP获取IP地址
            }
            
            final_status = status_map.get(status_code, '未知状态')
            
            # 备用状态判断逻辑 - 修复WLAN禁用状态判断
            is_enabled = (status_code not in ['0', '4', '5'])
            is_connected = (status_code == '2')
            
            # 特殊处理：如果是WLAN且状态码为4，根据netsh结果判断是否真的禁用
            if 'WLAN' in adapter_name and status_code == '4':
                is_enabled = False  # WLAN禁用时设为False
            
            self.logger.debug(f"网卡 {adapter_name} 备用状态分析: 状态码={status_code}, 最终状态={final_status}")
            self._log_operation_success("解析wmic状态码", f"状态码 {status_code}: {final_status}")
            
            return final_status, is_enabled, is_connected
            
        except Exception as e:
            self._log_operation_error("解析wmic状态码", e)
            return '未知状态', False, False
    
    def _get_status_display(self, status_code: str) -> str:
        """
        将网卡状态码转换为中文显示文本的简化版本
        
        这个方法将Windows系统的网卡连接状态码转换为用户友好的中文显示文本。
        遵循面向对象架构的单一职责原则，专门负责状态码的转换逻辑。
        
        Args:
            status_code (str): 网卡连接状态码
            
        Returns:
            str: 中文状态显示文本
        """
        status_map = {
            '0': '已断开连接',
            '1': '正在连接',
            '2': '已连接',
            '3': '正在断开连接',
            '4': '硬件不存在',
            '5': '硬件已禁用',
            '6': '硬件故障',
            '7': '媒体已断开连接',
            '8': '正在验证身份',
            '9': '验证已成功',
            '10': '验证失败',
            '11': '正在获取地址'
        }
        
        return status_map.get(status_code, '未知状态')
    
    # endregion
