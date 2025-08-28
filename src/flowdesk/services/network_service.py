"""
网络配置服务

功能说明：
• 封装所有网络相关的业务逻辑，包括网卡枚举、状态获取、IP配置等
• 通过PyQt信号与UI层通信，实现数据驱动的界面更新
• 提供网卡信息的智能处理，支持主IP和额外IP的自动分类
• 负责与Windows系统API交互，获取和设置网络配置

设计理念：
• 服务层作为业务逻辑的唯一入口，UI层不直接调用系统API
• 使用信号-槽机制实现松耦合的通信方式
• 提供完整的错误处理和状态反馈机制
• 支持异步操作，避免阻塞UI主线程
"""

import subprocess
import json
import re
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication

from ..models.adapter_info import AdapterInfo, IPConfigInfo, ExtraIP


class NetworkService(QObject):
    """
    网络配置服务类
    
    负责处理所有网络相关的业务逻辑，包括：
    - 网卡信息获取和枚举
    - IP配置的读取和设置
    - 网卡状态监控和同步
    - 网络信息的格式化和复制
    
    通过PyQt信号向UI层发送数据更新通知，实现数据驱动的界面刷新。
    """
    
    # 定义所有对外信号，用于与UI层通信
    adapters_updated = pyqtSignal(list)          # 网卡列表更新信号，参数：List[AdapterInfo]
    adapter_selected = pyqtSignal(object)        # 网卡选择变更信号，参数：AdapterInfo
    ip_info_updated = pyqtSignal(object)         # IP配置信息更新信号，参数：IPConfigInfo
    extra_ips_updated = pyqtSignal(list)         # 额外IP列表更新信号，参数：List[ExtraIP]
    network_info_copied = pyqtSignal(str)        # 网卡信息复制完成信号，参数：复制的文本内容
    adapter_refreshed = pyqtSignal(object)       # 单个网卡刷新完成信号，参数：AdapterInfo
    error_occurred = pyqtSignal(str, str)        # 错误发生信号，参数：(错误类型, 错误消息)
    
    def __init__(self):
        """
        初始化网络服务
        
        设置日志记录器，初始化内部状态变量，
        为后续的网络操作做准备。
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 内部状态管理
        self._adapters: List[AdapterInfo] = []      # 缓存的网卡信息列表
        self._current_adapter: Optional[AdapterInfo] = None  # 当前选中的网卡
        
        self.logger.info("网络配置服务初始化完成")
    
    def get_all_adapters(self) -> None:
        """
        获取所有网络适配器信息
        
        通过Windows系统命令获取所有网卡的详细信息，
        包括IP配置、连接状态、硬件信息等，
        处理完成后发射adapters_updated信号通知UI层更新。
        
        这是启动初始化的核心方法，会自动选中第一个网卡。
        """
        try:
            self.logger.info("开始获取网络适配器信息")
            
            # 获取网卡基本信息
            adapters_info = self._get_adapters_basic_info()
            
            # 获取每个网卡的详细IP配置
            detailed_adapters = []
            for adapter_basic in adapters_info:
                detailed_adapter = self._get_adapter_detailed_info(adapter_basic)
                if detailed_adapter:
                    detailed_adapters.append(detailed_adapter)
            
            # 更新内部缓存
            self._adapters = detailed_adapters
            
            # 发射信号通知UI层
            self.adapters_updated.emit(self._adapters)
            
            # 自动选中第一个网卡（启动初始化逻辑）
            if self._adapters:
                self.select_adapter(self._adapters[0].id)
            
            self.logger.info(f"网络适配器信息获取完成，共找到 {len(self._adapters)} 个网卡")
            
        except Exception as e:
            error_msg = f"获取网络适配器信息失败: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit("网卡枚举错误", error_msg)
    
    def select_adapter(self, adapter_id: str) -> None:
        """
        选择指定网络适配器并自动获取最新信息的智能选择方法
        
        这个方法实现了网卡选择的完整业务逻辑，遵循面向对象架构的单一职责原则。
        不仅完成网卡选择，还自动获取最新的网卡详细信息，确保显示数据的准确性。
        这是解决"选择网卡后信息不准确"问题的核心方法。
        
        业务流程：
        1. 查找并选择指定的网卡
        2. 自动获取该网卡的最新详细信息
        3. 更新缓存中的网卡数据
        4. 发射信号通知UI层更新显示
        
        Args:
            adapter_id (str): 网络适配器GUID标识符
        """
        try:
            # 第一步：在适配器列表中查找指定ID的网卡
            selected_adapter = None
            for adapter in self._adapters:
                if adapter.id == adapter_id:
                    selected_adapter = adapter
                    break
            
            if not selected_adapter:
                raise Exception(f"未找到ID为 {adapter_id} 的网络适配器")
            
            # 第二步：自动获取该网卡的最新详细信息
            # 这是解决信息不准确问题的关键步骤
            basic_info = self._find_adapter_basic_info(adapter_id)
            if basic_info:
                # 获取最新的详细信息，包括实时的IP配置
                refreshed_adapter = self._get_adapter_detailed_info(basic_info)
                if refreshed_adapter:
                    # 更新缓存中的网卡信息，确保数据一致性
                    for i, adapter in enumerate(self._adapters):
                        if adapter.id == refreshed_adapter.id:
                            self._adapters[i] = refreshed_adapter
                            break
                    
                    # 使用最新的网卡信息作为选中的网卡
                    selected_adapter = refreshed_adapter
                    self.logger.info(f"已自动刷新网卡信息: {selected_adapter.friendly_name}")
                else:
                    self.logger.warning(f"无法获取网卡 {selected_adapter.friendly_name} 的最新信息，使用缓存数据")
            else:
                self.logger.warning(f"无法找到网卡 {selected_adapter.friendly_name} 的基本信息，使用缓存数据")
            
            # 第三步：更新当前选中的网卡
            self._current_adapter = selected_adapter
            
            # 第四步：发射网卡选择信号，通知UI层更新
            self.adapter_selected.emit(selected_adapter)
            
            # 第五步：构造并发射IP配置信息信号
            ip_config = IPConfigInfo(
                adapter_id=selected_adapter.id,
                ip_address=selected_adapter.get_primary_ip(),
                subnet_mask=selected_adapter.get_primary_subnet_mask(),
                gateway=selected_adapter.gateway,
                dns_primary=selected_adapter.get_primary_dns(),
                dns_secondary=selected_adapter.get_secondary_dns(),
                dhcp_enabled=selected_adapter.dhcp_enabled
            )
            self.ip_info_updated.emit(ip_config)
            
            # 第六步：构造并发射额外IP信息信号
            extra_ips = []
            for ip, mask in selected_adapter.get_extra_ips():
                extra_ips.append(ExtraIP(ip_address=ip, subnet_mask=mask))
            self.extra_ips_updated.emit(extra_ips)
            
            self.logger.info(f"网卡选择完成: {selected_adapter.friendly_name}")
            
        except Exception as e:
            error_msg = f"选择网卡失败: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit("网卡选择错误", error_msg)
    
    def refresh_current_adapter(self) -> None:
        """
        刷新当前选中网卡的信息
        
        重新获取当前选中网卡的最新信息，
        更新缓存并通知UI层刷新显示。
        
        这是"刷新按钮"功能的核心实现。
        """
        if not self._current_adapter:
            self.logger.warning("没有选中的网卡，无法刷新")
            return
        
        try:
            self.logger.info(f"开始刷新网卡信息: {self._current_adapter.friendly_name}")
            
            # 重新获取当前网卡的详细信息
            basic_info = self._find_adapter_basic_info(self._current_adapter.id)
            if basic_info:
                refreshed_adapter = self._get_adapter_detailed_info(basic_info)
                if refreshed_adapter:
                    # 更新缓存中的网卡信息
                    for i, adapter in enumerate(self._adapters):
                        if adapter.id == refreshed_adapter.id:
                            self._adapters[i] = refreshed_adapter
                            break
                    
                    # 更新当前选中的网卡
                    self._current_adapter = refreshed_adapter
                    
                    # 发射刷新完成信号
                    self.adapter_refreshed.emit(refreshed_adapter)
                    
                    # 重新选择当前网卡以触发界面更新
                    self.select_adapter(refreshed_adapter.id)
                    
                    self.logger.info(f"网卡信息刷新完成: {refreshed_adapter.friendly_name}")
                else:
                    raise Exception("获取网卡详细信息失败")
            else:
                raise Exception("未找到网卡基本信息")
                
        except Exception as e:
            error_msg = f"刷新网卡信息失败: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit("网卡刷新错误", error_msg)
    
    def copy_adapter_info(self) -> None:
        """
        复制当前网卡信息到剪贴板
        
        将当前选中网卡的完整信息格式化为文本，
        复制到系统剪贴板，并发射复制完成信号。
        """
        if not self._current_adapter:
            self.logger.warning("没有选中的网卡，无法复制信息")
            return
        
        try:
            # 格式化网卡信息
            formatted_info = self._current_adapter.format_for_copy()
            
            # 复制到剪贴板
            clipboard = QApplication.clipboard()
            clipboard.setText(formatted_info)
            
            # 发射复制完成信号
            self.network_info_copied.emit(formatted_info)
            
            self.logger.info(f"网卡信息已复制到剪贴板: {self._current_adapter.friendly_name}")
            
        except Exception as e:
            error_msg = f"复制网卡信息失败: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit("信息复制错误", error_msg)
    
    def _get_adapters_basic_info(self) -> List[Dict[str, Any]]:
        """
        获取网卡基本信息列表
        
        通过wmic命令获取所有网卡的基本信息，
        包括名称、描述、MAC地址、状态等。
        
        Returns:
            List[Dict[str, Any]]: 网卡基本信息列表
        """
        try:
            # 执行wmic命令获取网卡基本信息，指定编码避免中文乱码
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
                    # 这里不仅处理有NetConnectionID的网卡，也要处理禁用状态的网卡
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
            
        except Exception as e:
            self.logger.error(f"获取网卡基本信息失败: {str(e)}")
            raise
    
    def _get_adapter_detailed_info(self, basic_info: Dict[str, Any]) -> Optional[AdapterInfo]:
        """
        获取网卡详细信息
        
        基于网卡基本信息，进一步获取IP配置、DNS设置等详细信息，
        构造完整的AdapterInfo对象。
        
        Args:
            basic_info (Dict[str, Any]): 网卡基本信息字典
            
        Returns:
            Optional[AdapterInfo]: 完整的网卡信息对象，失败时返回None
        """
        try:
            adapter_name = basic_info.get('NetConnectionID', '')
            if not adapter_name:
                return None
            
            # 获取IP配置信息
            ip_config = self._get_adapter_ip_config(adapter_name)
            
            # 网卡连接状态解析逻辑
            # 根据Windows网络连接状态代码映射到用户友好的中文描述
            # 这个映射表基于Windows WMI NetConnectionStatus枚举值
            status_code = basic_info.get('NetConnectionStatus', '0')
            status_map = {
                '0': '已禁用',        # 网卡被用户或系统禁用
                '1': '正在连接',      # 网卡正在尝试建立连接
                '2': '已连接',        # 网卡已成功连接到网络
                '3': '正在断开',      # 网卡正在断开连接过程中
                '4': '硬件不存在',    # 网卡硬件设备不存在或未检测到
                '5': '硬件已禁用',    # 网卡硬件被禁用（通常在设备管理器中）
                '6': '硬件故障',      # 网卡硬件出现故障
                '7': '媒体断开',      # 网线未连接或无线信号断开
                '8': '正在验证',      # 网卡正在进行身份验证
                '9': '验证失败',      # 网络身份验证失败
                '10': '验证成功',     # 网络身份验证成功
                '11': '正在获取地址'  # 网卡正在通过DHCP获取IP地址
            }
            status = status_map.get(status_code, '未知状态')
            
            # 网卡启用状态判断逻辑 - 基于Windows网络连接状态的精确判断
            # 这个逻辑用于区分网卡是被禁用还是仅仅未连接到网络
            # 状态码0表示网卡被用户禁用，状态码4、5表示硬件层面的禁用或不存在
            # 状态码7表示媒体断开（如网线未插或WiFi未连接），这种情况网卡是启用的但未连接
            is_adapter_enabled = (status_code not in ['0', '4', '5'])
            
            # 网卡连接状态判断逻辑 - 严格区分连接状态和启用状态
            # 只有状态码2表示网卡真正连接到网络并可以传输数据
            # 状态码7（媒体断开）、状态码0（已禁用）等都视为未连接状态
            is_adapter_connected = (status_code == '2')
            
            # 调试日志 - 帮助开发者理解状态判断逻辑
            self.logger.debug(f"网卡 {adapter_name} 状态分析: 状态码={status_code}, 状态描述={status}, 启用={is_adapter_enabled}, 连接={is_adapter_connected}")
            
            # 构造完整的网卡信息对象
            # 采用面向对象设计，将所有网卡相关数据封装在AdapterInfo类中
            adapter_info = AdapterInfo(
                id=basic_info.get('GUID', ''),                    # 网卡全局唯一标识符
                name=basic_info.get('Name', ''),                  # 网卡完整名称（系统内部使用）
                friendly_name=adapter_name,                       # 网卡友好名称（用户界面显示）
                description=basic_info.get('Description', ''),    # 网卡硬件描述信息
                mac_address=basic_info.get('MACAddress', ''),     # 网卡物理MAC地址
                status=status,                                     # 网卡当前连接状态的中文描述
                is_enabled=is_adapter_enabled,                    # 网卡是否处于启用状态
                is_connected=is_adapter_connected,                # 网卡是否已连接到网络
                ip_addresses=ip_config.get('ip_addresses', []),
                ipv6_addresses=ip_config.get('ipv6_addresses', []),
                subnet_masks=ip_config.get('subnet_masks', []),
                gateway=ip_config.get('gateway', ''),
                dns_servers=ip_config.get('dns_servers', []),
                dhcp_enabled=ip_config.get('dhcp_enabled', True),
                link_speed=ip_config.get('link_speed', ''),
                interface_type=self._get_interface_type(basic_info.get('Description', '')),
                last_updated=datetime.now()
            )
            
            return adapter_info
            
        except Exception as e:
            self.logger.error(f"获取网卡详细信息失败: {str(e)}")
            return None
    
    def _get_adapter_ip_config(self, adapter_name: str) -> Dict[str, Any]:
        """
        获取指定网卡IP配置信息的增强版本
        
        这个方法实现了多重数据源的IP配置获取策略，遵循面向对象架构的开闭原则。
        通过多种命令组合获取网卡配置，确保数据的完整性和准确性，
        解决"显示未知、未配置"等信息不准确的问题。
        
        技术实现：
        - 使用netsh命令获取基础IP配置信息
        - 使用ipconfig命令作为补充数据源
        - 实现智能的编码处理，支持中英文系统
        - 采用正则表达式精确解析网络配置参数
        
        Args:
            adapter_name (str): 网卡连接名称，如"vEthernet (泰兴)"
            
        Returns:
            Dict[str, Any]: 包含完整IP配置信息的字典，包括IP地址、子网掩码、网关、DNS等
        """
        # 初始化配置字典，提供默认值确保数据结构完整性
        config = {
            'ip_addresses': [],
            'ipv6_addresses': [],
            'subnet_masks': [],
            'gateway': '',
            'dns_servers': [],
            'dhcp_enabled': True,
            'link_speed': ''
        }
        
        try:
            # 第一步：使用netsh命令获取详细的IP配置信息
            # 这是主要的数据获取方式，支持IPv4配置的完整信息
            result = subprocess.run(
                ['netsh', 'interface', 'ipv4', 'show', 'config', f'name={adapter_name}'],
                capture_output=True, text=True, timeout=15, encoding='gbk', errors='ignore'
            )
            
            if result.returncode == 0:
                output = result.stdout
                self.logger.debug(f"netsh命令输出: {output[:200]}...")  # 记录前200字符用于调试
                
                # 解析DHCP启用状态
                if "DHCP 已启用" in output or "DHCP enabled" in output:
                    config['dhcp_enabled'] = True
                elif "静态配置" in output or "Statically Configured" in output:
                    config['dhcp_enabled'] = False
                
                # 使用增强的正则表达式解析IP地址和子网掩码
                # 支持多种格式的IP地址显示
                ip_patterns = [
                    r'IP 地址:\s*(\d+\.\d+\.\d+\.\d+)',
                    r'IP Address:\s*(\d+\.\d+\.\d+\.\d+)',
                    r'静态 IP 地址:\s*(\d+\.\d+\.\d+\.\d+)'
                ]
                
                mask_patterns = [
                    r'子网前缀长度:\s*(\d+)',
                    r'Subnet Prefix Length:\s*(\d+)',
                    r'子网掩码:\s*(\d+\.\d+\.\d+\.\d+)'
                ]
                
                # 尝试多种模式匹配IP地址
                ip_matches = []
                for pattern in ip_patterns:
                    matches = re.findall(pattern, output)
                    if matches:
                        ip_matches.extend(matches)
                        break
                
                # 尝试多种模式匹配子网掩码
                mask_matches = []
                for pattern in mask_patterns:
                    matches = re.findall(pattern, output)
                    if matches:
                        mask_matches.extend(matches)
                        break
                
                config['ip_addresses'] = ip_matches if ip_matches else []
                
                # 将前缀长度转换为子网掩码
                config['subnet_masks'] = []
                for mask_value in mask_matches:
                    try:
                        # 如果是前缀长度（数字），转换为子网掩码
                        if mask_value.isdigit():
                            prefix_len = int(mask_value)
                            subnet_mask = self._prefix_to_netmask(prefix_len)
                            config['subnet_masks'].append(subnet_mask)
                        else:
                            # 如果已经是子网掩码格式，直接使用
                            config['subnet_masks'].append(mask_value)
                    except (ValueError, TypeError):
                        continue
                
                # 解析默认网关，支持多种语言格式
                gateway_patterns = [
                    r'默认网关[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',
                    r'Default Gateway[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',
                    r'网关[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)'
                ]
                
                for pattern in gateway_patterns:
                    gateway_match = re.search(pattern, output)
                    if gateway_match:
                        config['gateway'] = gateway_match.group(1)
                        break
                
                # 解析DNS服务器，支持多种格式
                dns_patterns = [
                    r'静态配置的 DNS 服务器:\s*(\d+\.\d+\.\d+\.\d+)',
                    r'DNS Servers:\s*(\d+\.\d+\.\d+\.\d+)',
                    r'DNS 服务器:\s*(\d+\.\d+\.\d+\.\d+)'
                ]
                
                for pattern in dns_patterns:
                    dns_matches = re.findall(pattern, output)
                    if dns_matches:
                        config['dns_servers'] = dns_matches
                        break
            
            # 第二步：优先使用ipconfig作为主要数据源，因为它更准确
            # 对于复杂的网络配置（多IP、多子网掩码），ipconfig比netsh更可靠
            self._supplement_config_with_ipconfig(adapter_name, config)
            
            return config
            
        except Exception as e:
            self.logger.error(f"获取IP配置失败: {str(e)}")
            return config
    
    def _supplement_config_with_ipconfig(self, adapter_name: str, config: Dict[str, Any]) -> None:
        """
        使用ipconfig命令补充网卡配置信息的增强版本
        
        这个方法实现了完整的ipconfig输出解析，专门处理多IP地址、多子网掩码的复杂网络配置。
        遵循面向对象架构的单一职责原则，将ipconfig解析逻辑完全封装，
        确保能够准确获取Windows系统的真实网络配置信息。
        
        技术实现：
        - 精确匹配网卡配置段落，支持中英文系统
        - 处理多个IPv4地址和对应的子网掩码
        - 解析DHCP状态、网关、DNS服务器等完整配置
        - 实现容错机制，确保解析的稳定性
        
        Args:
            adapter_name (str): 网卡连接名称，如"vEthernet (泰兴)"
            config (Dict[str, Any]): 需要补充的配置字典
        """
        try:
            # 使用ipconfig /all命令获取系统完整的网络配置信息
            result = subprocess.run(
                ['ipconfig', '/all'],
                capture_output=True, text=True, timeout=15, encoding='gbk', errors='ignore'
            )
            
            if result.returncode == 0:
                output = result.stdout
                self.logger.debug(f"ipconfig输出长度: {len(output)} 字符")
                
                # 构建更精确的网卡段落匹配模式
                # 匹配从网卡名称开始到下一个网卡或文件结束的完整段落
                adapter_pattern = rf'以太网适配器\s+{re.escape(adapter_name)}:(.*?)(?=\n以太网适配器|\n无线局域网适配器|\nPPP 适配器|\Z)'
                adapter_match = re.search(adapter_pattern, output, re.DOTALL | re.IGNORECASE)
                
                if adapter_match:
                    adapter_section = adapter_match.group(1)
                    self.logger.debug(f"找到网卡 {adapter_name} 的配置段落，长度: {len(adapter_section)} 字符")
                    
                    # 解析多个IPv4地址
                    # 支持"IPv4 地址 . . . . . . . . . . . . : 172.2.208.10(首选)"格式
                    ip_pattern = r'IPv4 地址[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)'
                    ip_matches = re.findall(ip_pattern, adapter_section, re.IGNORECASE)
                    if ip_matches:
                        config['ip_addresses'] = ip_matches
                        self.logger.debug(f"解析到IPv4地址: {ip_matches}")
                    
                    # IPv6地址解析逻辑 - 支持多种IPv6地址格式的识别和提取
                    # 这个正则表达式用于从ipconfig输出中提取IPv6地址信息
                    # 支持标准IPv6格式、链路本地地址、临时地址等多种类型
                    ipv6_patterns = [
                        r'IPv6 地址[.\s]*:\s*([0-9a-fA-F:]+(?:%\d+)?)',           # 标准IPv6地址格式
                        r'临时 IPv6 地址[.\s]*:\s*([0-9a-fA-F:]+(?:%\d+)?)',      # 临时IPv6地址
                        r'链接本地 IPv6 地址[.\s]*:\s*([0-9a-fA-F:]+(?:%\d+)?)',  # 链路本地IPv6地址
                        r'本地链接 IPv6 地址[.\s]*:\s*([0-9a-fA-F:]+(?:%\d+)?)'   # 本地链接IPv6地址（不同Windows版本的表述）
                    ]
                    
                    # 使用多个正则模式匹配不同类型的IPv6地址
                    # 这种设计遵循开闭原则，便于后续扩展支持更多IPv6地址类型
                    ipv6_addresses = []
                    for pattern in ipv6_patterns:
                        matches = re.findall(pattern, adapter_section, re.IGNORECASE)
                        ipv6_addresses.extend(matches)
                    
                    # 去重并保存IPv6地址列表
                    # 使用集合去重后转回列表，保持数据结构一致性
                    if ipv6_addresses:
                        config['ipv6_addresses'] = list(set(ipv6_addresses))
                        self.logger.debug(f"解析到IPv6地址: {config['ipv6_addresses']}")
                    else:
                        config['ipv6_addresses'] = []
                        self.logger.debug("未找到IPv6地址配置")
                    
                    # 解析对应的子网掩码
                    # 支持"子网掩码  . . . . . . . . . . . . : 255.255.0.0"格式
                    mask_pattern = r'子网掩码[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)'
                    mask_matches = re.findall(mask_pattern, adapter_section, re.IGNORECASE)
                    if mask_matches:
                        config['subnet_masks'] = mask_matches
                        self.logger.debug(f"解析到子网掩码: {mask_matches}")
                    
                    # 解析默认网关 - 支持多行格式
                    # 格式1: "默认网关. . . . . . . . . . . . . : 172.2.0.1"
                    # 格式2: "默认网关. . . . . . . . . . . . . : fe80::xxx%4\n                                    172.2.0.1"
                    gateway_pattern = r'默认网关[.\s]*:\s*([^\n]*(?:\n\s*\d+\.\d+\.\d+\.\d+)?)'
                    gateway_match = re.search(gateway_pattern, adapter_section, re.IGNORECASE)
                    if gateway_match:
                        gateway_text = gateway_match.group(1).strip()
                        # 查找IPv4地址（优先使用IPv4网关）
                        ipv4_pattern = r'(\d+\.\d+\.\d+\.\d+)'
                        ipv4_matches = re.findall(ipv4_pattern, gateway_text)
                        if ipv4_matches:
                            config['gateway'] = ipv4_matches[0]  # 使用第一个IPv4地址
                            self.logger.debug(f"解析到IPv4网关: {ipv4_matches[0]}")
                        else:
                            config['gateway'] = ''
                            self.logger.debug("未找到IPv4网关，网关未配置")
                    
                    # 解析DNS服务器
                    # 支持"DNS 服务器  . . . . . . . . . . . : 114.114.114.114"格式
                    dns_pattern = r'DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)'
                    dns_matches = re.findall(dns_pattern, adapter_section, re.IGNORECASE)
                    if dns_matches:
                        config['dns_servers'] = dns_matches
                        self.logger.debug(f"解析到DNS服务器: {dns_matches}")
                    
                    # 解析DHCP状态
                    # 支持"DHCP 已启用 . . . . . . . . . . . : 否"格式
                    dhcp_pattern = r'DHCP 已启用[.\s]*:\s*(是|否)'
                    dhcp_match = re.search(dhcp_pattern, adapter_section, re.IGNORECASE)
                    if dhcp_match:
                        config['dhcp_enabled'] = (dhcp_match.group(1) == '是')
                        self.logger.debug(f"解析到DHCP状态: {config['dhcp_enabled']}")
                    
                    # 解析链路速度信息
                    # 通过wmic命令获取网卡的链路速度，这是ipconfig无法提供的信息
                    self._get_link_speed_info(adapter_name, config)
                    
                    self.logger.info(f"成功使用ipconfig补充网卡 {adapter_name} 的完整配置信息")
                else:
                    self.logger.warning(f"在ipconfig输出中未找到网卡 {adapter_name} 的配置段落")
                
        except Exception as e:
            self.logger.error(f"使用ipconfig补充配置信息失败: {str(e)}")
    
    def _get_link_speed_info(self, adapter_name: str, config: Dict[str, Any]) -> None:
        """
        获取网卡链路速度信息的专用方法
        
        这个方法实现了网卡链路速度的精确获取，遵循面向对象架构的单一职责原则。
        通过wmic命令查询网卡的物理连接速度，补充ipconfig无法提供的硬件层面信息。
        
        技术实现：
        - 使用wmic查询Win32_NetworkAdapter获取Speed属性
        - 将字节速度转换为用户友好的Mbps/Gbps格式
        - 实现异常安全的查询机制，确保不影响主流程
        
        Args:
            adapter_name (str): 网卡连接名称
            config (Dict[str, Any]): 配置字典，用于存储链路速度信息
        """
        try:
            # 使用wmic命令查询网卡的链路速度信息
            # Speed属性返回的是每秒比特数，需要转换为用户友好的格式
            result = subprocess.run(
                ['wmic', 'path', 'win32_networkadapter', 'where', f'NetConnectionID="{adapter_name}"', 
                 'get', 'Speed', '/format:csv'],
                capture_output=True, text=True, timeout=10, encoding='cp936', errors='replace'
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                lines = [line for line in output.split('\n') if line.strip() and not line.startswith('Node,')]
                
                if lines:
                    # 解析CSV格式的输出，提取Speed字段
                    for line in lines:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            speed_str = parts[1].strip()
                            if speed_str and speed_str.isdigit():
                                # 将比特/秒转换为用户友好的格式
                                speed_bps = int(speed_str)
                                if speed_bps >= 1000000000:  # >= 1 Gbps
                                    speed_formatted = f"{speed_bps / 1000000000:.1f} Gbps"
                                elif speed_bps >= 1000000:  # >= 1 Mbps
                                    speed_formatted = f"{speed_bps / 1000000:.0f} Mbps"
                                else:
                                    speed_formatted = f"{speed_bps} bps"
                                
                                config['link_speed'] = speed_formatted
                                self.logger.debug(f"解析到链路速度: {speed_formatted}")
                                return
                
                # 如果无法获取具体速度，设置为未知
                config['link_speed'] = '未知'
                
        except Exception as e:
            self.logger.warning(f"获取网卡 {adapter_name} 链路速度失败: {str(e)}")
            config['link_speed'] = '未知'
    
    def _find_adapter_basic_info(self, adapter_id: str) -> Optional[Dict[str, Any]]:
        """
        根据网卡GUID查找基本信息的核心匹配方法
        
        这个方法实现了网卡信息检索的核心逻辑，通过GUID精确匹配网卡。
        遵循面向对象架构的封装性原则，将复杂的查找逻辑封装在独立方法中，
        确保数据访问的一致性和可靠性。
        
        技术实现：
        - 重新获取最新的网卡基本信息，确保数据时效性
        - 使用GUID进行精确匹配，避免名称变化导致的匹配失败
        - 实现异常安全的查找逻辑，确保系统稳定性
        
        Args:
            adapter_id (str): 网卡GUID标识符，格式如{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}
            
        Returns:
            Optional[Dict[str, Any]]: 匹配的网卡基本信息字典，包含GUID、Name、NetConnectionID等字段
                                   未找到匹配项时返回None
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
    
    def _prefix_to_netmask(self, prefix_length: int) -> str:
        """
        将子网前缀长度转换为子网掩码
        
        Args:
            prefix_length (int): 前缀长度（如24）
            
        Returns:
            str: 子网掩码（如255.255.255.0）
        """
        mask = (0xffffffff >> (32 - prefix_length)) << (32 - prefix_length)
        return f"{(mask >> 24) & 0xff}.{(mask >> 16) & 0xff}.{(mask >> 8) & 0xff}.{mask & 0xff}"
    
    def _get_interface_type(self, description: str) -> str:
        """
        根据网卡描述判断接口类型
        
        Args:
            description (str): 网卡描述信息
            
        Returns:
            str: 接口类型（如"以太网"、"无线"等）
        """
        description_lower = description.lower()
        
        if 'wireless' in description_lower or 'wi-fi' in description_lower or '无线' in description_lower:
            return '无线'
        elif 'ethernet' in description_lower or '以太网' in description_lower:
            return '以太网'
        elif 'bluetooth' in description_lower or '蓝牙' in description_lower:
            return '蓝牙'
        elif 'virtual' in description_lower or '虚拟' in description_lower:
            return '虚拟'
        else:
            return '其他'
