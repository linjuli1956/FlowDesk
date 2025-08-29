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
    
    def get_all_adapters(self) -> List[AdapterInfo]:
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
            return self._adapters
            
        except Exception as e:
            error_msg = f"获取网络适配器信息失败: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit("网卡枚举错误", error_msg)
            return []
    
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
            # 使用与界面显示一致的格式化方法
            # 确保复制的内容与左侧IP信息容器显示的内容完全一致
            from flowdesk.ui.main_window import MainWindow
            main_window = None
            
            # 查找MainWindow实例以使用其格式化方法
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                for widget in app.allWidgets():
                    if isinstance(widget, MainWindow):
                        main_window = widget
                        break
            
            if main_window:
                # 使用MainWindow的格式化方法，确保与界面显示一致
                formatted_info = main_window._format_adapter_info_for_display(self._current_adapter)
            else:
                # 备用方案：使用原有的格式化方法
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
            
            # 增强DNS配置获取 - 使用netsh命令作为补充数据源
            # 遵循开闭原则，通过新增功能而不修改现有逻辑来增强DNS获取能力
            enhanced_dns = self._get_enhanced_dns_config(adapter_name)
            if enhanced_dns:
                # 如果netsh获取到了DNS信息，优先使用或合并到现有DNS列表中
                existing_dns = ip_config.get('dns_servers', [])
                # 合并DNS服务器列表，去重并保持顺序
                combined_dns = enhanced_dns.copy()
                for dns in existing_dns:
                    if dns not in combined_dns:
                        combined_dns.append(dns)
                ip_config['dns_servers'] = combined_dns
                self.logger.debug(f"网卡 {adapter_name} DNS配置已增强: {combined_dns}")
            
            # 获取精确的网卡状态信息 - 使用netsh interface show interface命令
            # 这是新增的双重状态判断机制，提供比wmic状态码更准确的状态信息
            interface_status = self._get_interface_status_info(adapter_name)
            
            # 应用双重状态判断逻辑 - 结合管理状态和连接状态
            # 这个逻辑遵循面向对象架构的单一职责原则，专门处理状态判断
            final_status, is_adapter_enabled, is_adapter_connected = self._determine_final_status(
                interface_status['admin_status'], 
                interface_status['connect_status']
            )
            
            # 备用状态判断机制 - 当netsh命令获取失败时使用wmic状态码
            # 遵循依赖倒置原则，提供多种状态获取方式的抽象
            if interface_status['admin_status'] == '未知' and interface_status['connect_status'] == '未知':
                self.logger.info(f"网卡 {adapter_name} netsh状态获取失败，使用wmic状态码作为备用方案")
                
                # 原有的wmic状态码解析逻辑作为备用方案
                status_code = basic_info.get('NetConnectionStatus', '0')
                
                # 添加调试日志以分析WLAN状态码
                self.logger.debug(f"网卡 {adapter_name} wmic状态码: {status_code}")
                
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
                is_adapter_enabled = (status_code not in ['0', '4', '5'])
                is_adapter_connected = (status_code == '2')
                
                # 特殊处理：如果是WLAN且状态码为4，根据netsh结果判断是否真的禁用
                if 'WLAN' in adapter_name and status_code == '4':
                    is_adapter_enabled = False  # WLAN禁用时设为False
                
                self.logger.debug(f"网卡 {adapter_name} 备用状态分析: 状态码={status_code}, 最终状态={final_status}")
            else:
                self.logger.debug(f"网卡 {adapter_name} 精确状态分析: 管理状态={interface_status['admin_status']}, 连接状态={interface_status['connect_status']}, 最终状态={final_status}")
            
            # 构造完整的网卡信息对象
            # 采用面向对象设计，将所有网卡相关数据封装在AdapterInfo类中
            adapter_info = AdapterInfo(
                id=basic_info.get('GUID', ''),                    # 网卡全局唯一标识符
                name=basic_info.get('Name', ''),                  # 网卡完整名称（系统内部使用）
                friendly_name=adapter_name,                       # 网卡友好名称（用户界面显示）
                description=basic_info.get('Description', ''),    # 网卡硬件描述信息
                mac_address=basic_info.get('MACAddress', ''),     # 网卡物理MAC地址
                status=final_status,                              # 网卡当前连接状态的中文描述（使用增强的状态判断结果）
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
                    
                    # 解析默认网关
                    # 支持"默认网关 . . . . . . . . . . . . : 192.168.1.1"格式
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
                    
                    # 解析DNS服务器配置 - 增强的DNS解析逻辑
                    # 这是解决"DNS服务器获取不准确"问题的关键代码，支持更多DNS配置格式
                    dns_patterns = [
                        r'DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',                    # 标准DNS格式
                        r'通过 DHCP 配置的 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',  # DHCP DNS格式
                        r'静态配置的 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',          # 静态DNS格式
                        r'首选 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',              # 首选DNS格式
                        r'备用 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',              # 备用DNS格式
                        r'Primary DNS Server[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',           # 英文主DNS
                        r'Secondary DNS Server[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',         # 英文备用DNS
                    ]
                    
                    dns_servers_found = []
                    # 逐个尝试所有DNS匹配模式，确保不遗漏任何可能的DNS配置
                    for i, pattern in enumerate(dns_patterns, 1):
                        dns_matches = re.findall(pattern, adapter_section, re.IGNORECASE)
                        if dns_matches:
                            dns_servers_found.extend(dns_matches)
                            self.logger.debug(f"ipconfig DNS模式{i}匹配成功: {dns_matches}")
                    
                    # 如果标准模式都没有找到DNS，尝试多行DNS配置解析
                    if not dns_servers_found:
                        self.logger.debug("尝试多行DNS配置解析")
                        # 查找DNS服务器配置行，然后提取后续行中的IP地址
                        dns_section_pattern = r'DNS 服务器[^:]*:([^\n]*(?:\n\s+[^\n]*)*)'  
                        dns_section_match = re.search(dns_section_pattern, adapter_section, re.IGNORECASE)
                        if dns_section_match:
                            dns_section = dns_section_match.group(1)
                            # 从DNS配置段落中提取所有IP地址
                            ip_addresses = re.findall(r'(\d+\.\d+\.\d+\.\d+)', dns_section)
                            if ip_addresses:
                                dns_servers_found.extend(ip_addresses)
                                self.logger.debug(f"多行DNS解析成功: {ip_addresses}")
                    
                    if dns_servers_found:
                        # 去重并保持顺序，确保DNS服务器列表的唯一性和正确性
                        unique_dns = []
                        seen = set()
                        for dns in dns_servers_found:
                            # 过滤掉无效的DNS地址（如0.0.0.0或本地地址）
                            if dns not in seen and not dns.startswith('0.') and not dns.startswith('127.'):
                                seen.add(dns)
                                unique_dns.append(dns)
                        config['dns_servers'] = unique_dns
                        self.logger.debug(f"ipconfig最终解析到DNS服务器: {unique_dns}")
                    else:
                        self.logger.debug(f"ipconfig未能解析到DNS服务器，网卡段落内容: {adapter_section[:300]}...")
                    
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
    
    def _get_interface_status_info(self, adapter_name: str) -> Dict[str, str]:
        """
        获取网卡精确的启用和连接状态信息
        
        这个方法通过netsh interface show interface命令获取网卡的精确状态信息，
        遵循面向对象架构的单一职责原则，专门负责状态信息的获取和解析。
        相比wmic命令的状态码，这种方式能够更准确地区分网卡的启用状态和连接状态。
        
        技术实现：
        - 使用netsh interface show interface命令获取所有网卡的状态表格
        - 通过友好名称精确匹配目标网卡
        - 解析"管理状态"和"状态"两个关键字段
        - 支持中英文系统的状态文本识别
        
        状态说明：
        - 管理状态：已启用/已禁用（用户或系统设置的启用状态）
        - 状态：已连接/已断开连接（实际的网络连接状态）
        
        Args:
            adapter_name (str): 网卡友好名称，如"以太网"、"WLAN"等
            
        Returns:
            Dict[str, str]: 包含状态信息的字典，键包括：
                - admin_status: 管理状态（已启用/已禁用/未知）
                - connect_status: 连接状态（已连接/已断开连接/未知）
                - interface_name: 接口名称（用于验证匹配正确性）
        """
        # 初始化状态字典，提供默认值确保数据结构完整性
        status_info = {
            'admin_status': '未知',      # 管理状态：网卡是否被启用
            'connect_status': '未知',    # 连接状态：网卡是否已连接到网络
            'interface_name': ''         # 接口名称：用于验证匹配结果
        }
        
        try:
            # 执行netsh interface show interface命令获取所有网卡的状态表格
            # 这个命令返回系统中所有网络接口的详细状态信息
            result = subprocess.run(
                ['netsh', 'interface', 'show', 'interface'],
                capture_output=True, text=True, timeout=15, encoding='gbk', errors='ignore'
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # 按行分割输出，查找目标网卡的状态信息
                lines = output.strip().split('\n')
                
                # 跳过表头，查找包含目标网卡名称的行
                for line in lines:
                    line = line.strip()
                    if not line or '---' in line:  # 跳过空行和分隔线
                        continue
                    
                    # 检查当前行是否包含目标网卡名称
                    # 使用多种匹配策略，因为netsh输出的名称可能与友好名称略有差异
                    line_parts = line.split()
                    if len(line_parts) >= 4:
                        interface_name = ' '.join(line_parts[3:])  # 接口名称是第4列及之后的所有内容
                        
                        # 多种匹配策略：完全匹配、包含匹配、反向包含匹配
                        if (adapter_name == interface_name or 
                            adapter_name in interface_name or 
                            interface_name in adapter_name):
                            
                            # 解析状态行的格式：管理状态 状态 类型 接口名称
                            # 典型格式："已启用     已连接     专用         以太网"
                            admin_status_raw = line_parts[0].strip()      # 管理状态
                            connect_status_raw = line_parts[1].strip()    # 连接状态
                            
                            # 解析管理状态（第一列）- 网卡是否被启用
                            if '已启用' in admin_status_raw or 'Enabled' in admin_status_raw:
                                status_info['admin_status'] = '已启用'
                            elif '已禁用' in admin_status_raw or 'Disabled' in admin_status_raw:
                                status_info['admin_status'] = '已禁用'
                            else:
                                status_info['admin_status'] = '未知'
                            
                            # 解析连接状态（第二列）- 网卡是否已连接
                            if '已连接' in connect_status_raw or 'Connected' in connect_status_raw:
                                status_info['connect_status'] = '已连接'
                            elif '已断开连接' in connect_status_raw or 'Disconnected' in connect_status_raw or '未连接' in connect_status_raw or 'Not connected' in connect_status_raw:
                                status_info['connect_status'] = '已断开连接'
                            else:
                                status_info['connect_status'] = '未知'
                            
                            self.logger.debug(f"网卡 {adapter_name} 状态解析成功: 管理状态={status_info['admin_status']}, 连接状态={status_info['connect_status']}")
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
    
    def _determine_final_status(self, admin_status: str, connect_status: str) -> tuple:
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
            tuple: 包含三个元素的元组：
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
    
    def _get_enhanced_dns_config(self, adapter_name: str) -> List[str]:
        """
        使用netsh命令增强DNS服务器信息获取
        
        这个方法通过正确的netsh命令语法获取DNS配置信息，解决之前语法错误的问题。
        遵循面向对象架构的开闭原则，作为现有DNS获取方式的补充和增强。
        
        技术实现：
        - 使用正确的netsh interface ipv4 show config "接口名称"语法
        - 专门解析DNS服务器配置段落，支持多种输出格式
        - 实现异常安全的DNS解析机制
        - 与现有DNS获取方式进行数据融合
        
        Args:
            adapter_name (str): 网卡友好名称，如"以太网"、"WLAN"等
            
        Returns:
            List[str]: DNS服务器IP地址列表，按优先级排序
        """
        dns_servers = []
        
        try:
            # 修复netsh命令语法：使用正确的参数格式
            # 正确语法：netsh interface ipv4 show config "接口名称"
            # 错误语法：netsh interface ipv4 show config name="接口名称"
            cmd = ['netsh', 'interface', 'ipv4', 'show', 'config', f'"{adapter_name}"']
            self.logger.debug(f"执行修复后的netsh DNS获取命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=15, encoding='gbk', errors='ignore'
            )
            
            # 详细的调试日志，帮助诊断DNS获取问题
            self.logger.debug(f"netsh命令返回码: {result.returncode}")
            if result.stdout:
                # 显示更多输出内容以便调试
                self.logger.debug(f"netsh命令完整输出: {result.stdout}")
            if result.stderr:
                self.logger.debug(f"netsh命令错误输出: {result.stderr}")
            
            if result.returncode == 0 and result.stdout.strip():
                output = result.stdout
                
                # 检查输出是否包含错误信息或帮助信息
                if "此命令提供的语法不正确" in output or "用法:" in output:
                    self.logger.warning(f"netsh命令语法仍然不正确，输出: {output[:100]}...")
                    return dns_servers
                
                # 增强的DNS正则表达式模式，支持更多格式
                # 这些模式基于实际的Windows netsh输出格式设计
                dns_patterns = [
                    r'通过 DHCP 配置的 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',  # DHCP DNS格式
                    r'DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',                    # 标准DNS格式
                    r'静态配置的 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',          # 静态DNS格式
                    r'DNS Servers[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',                   # 英文系统格式
                    r'主 DNS 后缀[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',                   # 主DNS后缀格式
                    r'备用 DNS 后缀[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',                 # 备用DNS后缀格式
                ]
                
                # 逐个尝试所有DNS匹配模式
                # 这种设计确保能够捕获各种可能的DNS配置格式
                for i, pattern in enumerate(dns_patterns, 1):
                    matches = re.findall(pattern, output, re.IGNORECASE | re.MULTILINE)
                    if matches:
                        dns_servers.extend(matches)
                        self.logger.debug(f"DNS模式{i}匹配成功: {matches}")
                
                # 如果标准模式都没有匹配，尝试更宽松的IP地址匹配
                if not dns_servers:
                    self.logger.debug("标准DNS模式未匹配，尝试宽松IP地址匹配")
                    # 查找所有可能的IP地址，然后过滤掉明显不是DNS的地址
                    ip_pattern = r'(\d+\.\d+\.\d+\.\d+)'
                    all_ips = re.findall(ip_pattern, output)
                    # 过滤掉本地地址和广播地址
                    for ip in all_ips:
                        if not (ip.startswith('127.') or ip.startswith('0.') or 
                               ip.endswith('.0') or ip.endswith('.255') or ip == '255.255.255.255'):
                            dns_servers.append(ip)
                            self.logger.debug(f"通过宽松匹配找到可能的DNS: {ip}")
                
                # 去重并保持顺序，确保DNS服务器列表的唯一性
                seen = set()
                unique_dns = []
                for dns in dns_servers:
                    if dns not in seen:
                        seen.add(dns)
                        unique_dns.append(dns)
                dns_servers = unique_dns
                
            else:
                self.logger.warning(f"netsh DNS配置命令执行失败或无输出: 返回码={result.returncode}, 错误={result.stderr}")
                
        except Exception as e:
            # 异常安全处理，确保DNS获取失败不影响主流程
            self.logger.error(f"使用netsh获取网卡 {adapter_name} DNS配置时发生异常: {str(e)}")
        
        return dns_servers

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
