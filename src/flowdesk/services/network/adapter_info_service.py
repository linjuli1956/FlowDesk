# -*- coding: utf-8 -*-
"""
网卡详细信息获取专用服务模块。这个文件在FlowDesk网络管理架构中扮演"信息收集器"角色，专门负责获取单个网络适配器的完整详细配置信息。
它解决了网卡IP配置、DNS设置、IPv6地址等复杂网络信息的精确获取问题，通过多重数据源（netsh、ipconfig）确保信息的完整性和准确性。
UI层通过此服务获得准确的网卡详细信息用于显示，其他服务依赖此模块提供的标准化网卡数据进行配置操作。该服务严格遵循单一职责和开闭原则，提供可扩展的网卡信息获取框架。
"""
import subprocess
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from .network_service_base import NetworkServiceBase
from ...models.adapter_info import AdapterInfo


class AdapterInfoService(NetworkServiceBase):
    """
    网络适配器详细信息获取服务
    
    专门负责获取网络适配器完整详细信息的核心服务。
    此服务封装了复杂的网卡配置信息获取逻辑，支持多重数据源。
    
    主要功能：
    - 通过netsh和ipconfig命令获取网卡IP配置详细信息
    - 解析IPv4和IPv6地址、子网掩码、网关、DNS等配置
    - 实现多重数据源合并策略，确保信息完整性
    - 提供DNS配置增强获取和链路速度信息
    
    输入输出：
    - 输入：网卡基本信息字典或网卡GUID
    - 输出：完整的AdapterInfo对象或配置信息字典
    
    可能异常：
    - subprocess.CalledProcessError：网络命令执行失败
    - Exception：配置信息解析错误或系统调用异常
    """
    
    def __init__(self, parent=None):
        """
        初始化网络适配器信息获取服务
        
        Args:
            parent: PyQt父对象，用于内存管理
        """
        super().__init__(parent)
        # 初始化发现服务依赖，用于获取网卡基本信息
        from .adapter_discovery_service import AdapterDiscoveryService
        self._discovery_service = AdapterDiscoveryService(self)
        self._log_operation_start("AdapterInfoService初始化")
    
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
            # 首先根据GUID获取网卡基本信息
            basic_info = self._discovery_service.get_adapter_basic_info(adapter_id)
            if not basic_info:
                self.logger.warning(f"无法获取网卡基本信息: {adapter_id}")
                return None
            
            adapter_name = basic_info.get('NetConnectionID', '')
            if not adapter_name:
                return None
            
            self._log_operation_start("获取网卡详细信息", adapter_name=adapter_name)
            
            # 获取IP配置信息（包含链路速度）
            ip_config = self._get_adapter_ip_config(adapter_name)
            
            # 确保链路速度信息在创建AdapterInfo对象前已获取
            if not ip_config.get('link_speed'):
                # 直接通过性能服务获取链路速度，确保数据完整性
                from .adapter_performance_service import AdapterPerformanceService
                performance_service = AdapterPerformanceService()
                link_speed = performance_service.get_link_speed_info(adapter_name)
                ip_config['link_speed'] = link_speed
                self.logger.info(f"补充获取网卡 {adapter_name} 链路速度: {link_speed}")
            
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
            
            self._log_operation_success("获取网卡详细信息", f"网卡: {adapter_name}")
            return adapter_info
            
        except Exception as e:
            self._log_operation_error("获取网卡详细信息", e)
            return None
    
    def get_adapter_ip_config(self, adapter_name: str) -> Dict[str, Any]:
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
        return self._get_adapter_ip_config(adapter_name)
    
    # endregion
    
    # region 状态判断方法（来自源文件）
    
    def _get_interface_status_info(self, adapter_name: str) -> Dict[str, str]:
        """
        获取网卡精确的启用和连接状态信息
        """
        # 初始化状态字典，提供默认值确保数据结构完整性
        status_info = {
            'admin_status': '未知',      # 管理状态：网卡是否被启用
            'connect_status': '未知',    # 连接状态：网卡是否已连接到网络
            'interface_name': ''         # 接口名称：用于验证匹配结果
        }
        
        try:
            # 执行netsh interface show interface命令获取所有网卡的状态表格
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
                    line_parts = line.split()
                    if len(line_parts) >= 4:
                        interface_name = ' '.join(line_parts[3:])  # 接口名称是第4列及之后的所有内容
                        
                        # 多种匹配策略：完全匹配、包含匹配、反向包含匹配
                        if (adapter_name == interface_name or 
                            adapter_name in interface_name or 
                            interface_name in adapter_name):
                            
                            # 解析状态行的格式：管理状态 状态 类型 接口名称
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
            self.logger.debug(f"状态判断结果: 管理状态未知")
            
        return final_status, is_enabled, is_connected
    
    # endregion
    
    # region 私有实现方法
    
    def _get_adapter_ip_config(self, adapter_name: str) -> Dict[str, Any]:
        """
        获取指定网卡IP配置信息的核心实现方法
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
                self.logger.debug(f"netsh命令执行成功，输出长度: {len(output)} 字符")  # 避免记录可能乱码的原始输出
                
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
                            # 已经是子网掩码格式，直接使用
                            config['subnet_masks'].append(mask_value)
                    except (ValueError, IndexError):
                        self.logger.warning(f"子网掩码转换失败: {mask_value}")
                        continue
                
                # 解析默认网关
                gateway_patterns = [
                    r'默认网关:\s*(\d+\.\d+\.\d+\.\d+)',
                    r'Default Gateway:\s*(\d+\.\d+\.\d+\.\d+)'
                ]
                
                for pattern in gateway_patterns:
                    gateway_match = re.search(pattern, output)
                    if gateway_match:
                        config['gateway'] = gateway_match.group(1)
                        break
                
                # 解析DNS服务器
                dns_patterns = [
                    r'DNS 服务器:\s*(\d+\.\d+\.\d+\.\d+)',
                    r'DNS Servers:\s*(\d+\.\d+\.\d+\.\d+)'
                ]
                
                for pattern in dns_patterns:
                    dns_matches = re.findall(pattern, output)
                    if dns_matches:
                        config['dns_servers'] = dns_matches
                        break
                
            else:
                self.logger.warning(f"netsh命令执行失败，返回码: {result.returncode}")
            
            # 第二步：使用ipconfig命令补充和验证配置信息
            # 这提供了第二重数据源保障，确保信息的准确性和完整性
            self._supplement_config_with_ipconfig(adapter_name, config)
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"获取网卡 {adapter_name} IP配置超时")
        except Exception as e:
            self.logger.error(f"获取网卡 {adapter_name} IP配置失败: {str(e)}")
        
        # 记录最终获取到的配置信息
        if config['ip_addresses'] or config['ipv6_addresses']:
            self.logger.info(f"成功使用ipconfig补充网卡 {adapter_name} 的完整配置信息")
        
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
                capture_output=True, text=True, timeout=6, encoding='gbk', errors='ignore'
            )
            
            if result.returncode == 0:
                output = result.stdout
                self.logger.debug(f"ipconfig输出长度: {len(output)} 字符")
                
                # 构建更精确的网卡段落匹配模式，支持无线、以太网和虚拟网卡适配器
                # 匹配从网卡名称开始到下一个网卡或文件结束的完整段落
                adapter_patterns = [
                    rf'无线局域网适配器\s+{re.escape(adapter_name)}:(.*?)(?=\n以太网适配器|\n无线局域网适配器|\nPPP 适配器|\nTunnel adapter|\Z)',
                    rf'以太网适配器\s+{re.escape(adapter_name)}:(.*?)(?=\n以太网适配器|\n无线局域网适配器|\nPPP 适配器|\nTunnel adapter|\Z)',
                    rf'PPP 适配器\s+{re.escape(adapter_name)}:(.*?)(?=\n以太网适配器|\n无线局域网适配器|\nPPP 适配器|\nTunnel adapter|\Z)',
                    rf'Tunnel adapter\s+{re.escape(adapter_name)}:(.*?)(?=\n以太网适配器|\n无线局域网适配器|\nPPP 适配器|\nTunnel adapter|\Z)'
                ]
                
                adapter_match = None
                for pattern in adapter_patterns:
                    adapter_match = re.search(pattern, output, re.DOTALL | re.IGNORECASE)
                    if adapter_match:
                        break
                
                if adapter_match:
                    adapter_section = adapter_match.group(1)
                    self.logger.debug(f"找到网卡 {adapter_name} 的配置段落，长度: {len(adapter_section)} 字符")
                else:
                    # 如果精确匹配失败，尝试更宽松的匹配策略
                    self.logger.debug(f"精确匹配失败，尝试宽松匹配网卡 {adapter_name}")
                    
                    # 构建宽松匹配模式，处理网卡名称变体
                    loose_patterns = [
                        rf'适配器\s+[^:]*{re.escape(adapter_name)}[^:]*:(.*?)(?=\n.*适配器|\Z)',  # 通用适配器匹配
                        rf'{re.escape(adapter_name)}[^:]*:(.*?)(?=\n.*适配器|\Z)',               # 直接名称匹配
                    ]
                    
                    for pattern in loose_patterns:
                        adapter_match = re.search(pattern, output, re.DOTALL | re.IGNORECASE)
                        if adapter_match:
                            adapter_section = adapter_match.group(1)
                            self.logger.debug(f"宽松匹配成功，找到网卡 {adapter_name} 的配置段落")
                            break
                    
                    if not adapter_match:
                        self.logger.warning(f"在ipconfig输出中未找到网卡 {adapter_name} 的配置信息")
                        return
                
                # 处理找到的adapter_section
                if adapter_match and adapter_section:
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
                    
                    # 解析对应的子网掩码 - 增强版本支持多种格式
                    # 支持"子网掩码  . . . . . . . . . . . . : 255.255.0.0"格式
                    # 支持"子网前缀长度 . . . . . . . . . . : 24"格式
                    mask_patterns = [
                        r'子网掩码[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',
                        r'子网前缀长度[.\s]*:\s*(\d+)'
                    ]
                    
                    mask_matches = []
                    for pattern in mask_patterns:
                        matches = re.findall(pattern, adapter_section, re.IGNORECASE)
                        if matches:
                            mask_matches.extend(matches)
                            break
                    
                    if mask_matches:
                        config['subnet_masks'] = []
                        for mask_value in mask_matches:
                            try:
                                # 如果是前缀长度（数字），转换为子网掩码
                                if mask_value.isdigit():
                                    prefix_len = int(mask_value)
                                    subnet_mask = self._prefix_to_netmask(prefix_len)
                                    config['subnet_masks'].append(subnet_mask)
                                else:
                                    # 已经是子网掩码格式，直接使用
                                    config['subnet_masks'].append(mask_value)
                            except (ValueError, IndexError):
                                self.logger.warning(f"子网掩码转换失败: {mask_value}")
                                continue
                        self.logger.debug(f"解析到子网掩码: {config['subnet_masks']}")
                    
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
                            config['gateway'] = ipv4_matches[0]  # 使用第一个IPv4网关
                            self.logger.debug(f"解析到默认网关: {config['gateway']}")
                    
                    # 解析DNS服务器配置 - 增强的DNS解析逻辑
                    # 支持多种DNS配置格式，包括DHCP和静态配置
                    dns_patterns = [
                        r'DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',                    # 标准DNS格式
                        r'通过 DHCP 配置的 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',  # DHCP DNS格式
                        r'静态配置的 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',          # 静态DNS格式
                        r'首选 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',              # 首选DNS格式
                        r'备用 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)'               # 备用DNS格式
                    ]
                    
                    # 使用多个正则模式匹配不同类型的DNS配置
                    dns_servers = []
                    for pattern in dns_patterns:
                        matches = re.findall(pattern, adapter_section, re.IGNORECASE)
                        dns_servers.extend(matches)
                    
                    # 如果标准模式都没有匹配，尝试更宽松的多行DNS匹配
                    if not dns_servers:
                        dns_multiline_pattern = r'DNS 服务器[.\s]*:\s*([^\n]*(?:\n\s*\d+\.\d+\.\d+\.\d+)*)'
                        dns_match = re.search(dns_multiline_pattern, adapter_section, re.IGNORECASE)
                        if dns_match:
                            dns_text = dns_match.group(1)
                            # 从DNS文本中提取所有IPv4地址
                            ipv4_dns_pattern = r'(\d+\.\d+\.\d+\.\d+)'
                            dns_servers = re.findall(ipv4_dns_pattern, dns_text)
                    
                    # 去重并保存DNS服务器列表
                    if dns_servers:
                        # 去重但保持顺序
                        seen = set()
                        unique_dns = []
                        for dns in dns_servers:
                            if dns not in seen:
                                seen.add(dns)
                                unique_dns.append(dns)
                        config['dns_servers'] = unique_dns
                        self.logger.debug(f"解析到DNS服务器: {unique_dns}")
                    
                    # 解析DHCP启用状态
                    # 查找"DHCP 已启用"或"已启用 DHCP"等表述
                    dhcp_patterns = [
                        r'DHCP[.\s]*已启用',
                        r'已启用[.\s]*DHCP',
                        r'DHCP[.\s]*Enabled',
                        r'Enabled[.\s]*DHCP'
                    ]
                    
                    dhcp_enabled = False
                    for pattern in dhcp_patterns:
                        if re.search(pattern, adapter_section, re.IGNORECASE):
                            # 进一步检查是否为"否"
                            if '否' not in adapter_section:
                                dhcp_enabled = True
                            break
                    
                    config['dhcp_enabled'] = dhcp_enabled
                    self.logger.debug(f"解析到DHCP状态: {'已启用' if dhcp_enabled else '已禁用'}")
                    
                    # 获取链路速度信息 - 修复拆包后缺失的功能
                    # 通过性能服务获取网卡的链路速度信息
                    from .adapter_performance_service import AdapterPerformanceService
                    performance_service = AdapterPerformanceService()
                    link_speed = performance_service.get_link_speed_info(adapter_name)
                    config['link_speed'] = link_speed
                    self.logger.info(f"成功获取网卡 {adapter_name} 链路速度: {link_speed}")
                    
            else:
                self.logger.warning(f"ipconfig命令执行失败，返回码: {result.returncode}")
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"ipconfig命令执行超时，无法补充网卡 {adapter_name} 信息")
        except Exception as e:
            self.logger.error(f"使用ipconfig补充网卡配置失败: {str(e)}")
    
    def _get_enhanced_dns_config(self, adapter_name: str) -> Optional[List[str]]:
        """
        使用netsh命令增强获取DNS配置信息
        
        这个方法专门用于通过netsh命令获取更准确的DNS服务器配置信息。
        作为ipconfig命令的补充，提供更可靠的DNS信息获取能力。
        
        Args:
            adapter_name (str): 网卡连接名称
            
        Returns:
            Optional[List[str]]: DNS服务器地址列表，失败时返回None
        """
        try:
            # 使用netsh命令查询DNS服务器配置
            result = subprocess.run(
                ['netsh', 'interface', 'ipv4', 'show', 'dns', f'name={adapter_name}'],
                capture_output=True, text=True, timeout=10, encoding='gbk', errors='ignore'
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # 解析DNS服务器地址
                dns_pattern = r'(\d+\.\d+\.\d+\.\d+)'
                dns_servers = re.findall(dns_pattern, output)
                
                if dns_servers:
                    self.logger.debug(f"netsh获取到网卡 {adapter_name} 的DNS服务器: {dns_servers}")
                    return dns_servers
                else:
                    self.logger.debug(f"netsh未找到网卡 {adapter_name} 的DNS配置")
                    return None
            else:
                self.logger.warning(f"netsh DNS查询失败，返回码: {result.returncode}")
                return None
                
        except Exception as e:
            self.logger.error(f"增强DNS配置获取失败: {str(e)}")
            return None
    
    def _get_interface_type(self, description: str) -> str:
        """
        根据网卡描述判断接口类型
        
        通过网卡硬件描述信息智能判断网卡类型，为UI显示提供友好的分类标识。
        
        Args:
            description (str): 网卡硬件描述
            
        Returns:
            str: 接口类型标识（以太网/无线/虚拟/其他）
        """
        if not description:
            return '其他'
        
        description_lower = description.lower()
        
        # 无线网卡识别
        wireless_keywords = ['wireless', 'wifi', 'wlan', '无线', '802.11']
        if any(keyword in description_lower for keyword in wireless_keywords):
            return '无线'
        
        # 以太网卡识别
        ethernet_keywords = ['ethernet', 'gigabit', 'fast ethernet', '以太网']
        if any(keyword in description_lower for keyword in ethernet_keywords):
            return '以太网'
        
        # 虚拟网卡识别
        virtual_keywords = ['virtual', 'hyper-v', 'vmware', 'virtualbox', '虚拟']
        if any(keyword in description_lower for keyword in virtual_keywords):
            return '虚拟'
        
        return '其他'
    
    def _prefix_to_netmask(self, prefix_length: int) -> str:
        """
        将CIDR前缀长度转换为点分十进制子网掩码
        
        这个工具方法实现了网络前缀长度到子网掩码的标准转换算法。
        支持IPv4网络的所有有效前缀长度（0-32）。
        
        Args:
            prefix_length (int): CIDR前缀长度（0-32）
            
        Returns:
            str: 点分十进制格式的子网掩码
            
        Raises:
            ValueError: 前缀长度超出有效范围时抛出异常
        """
        if not (0 <= prefix_length <= 32):
            raise ValueError(f"前缀长度必须在0-32范围内，当前值: {prefix_length}")
        
        # 创建32位掩码，前prefix_length位为1，其余为0
        mask = (0xFFFFFFFF << (32 - prefix_length)) & 0xFFFFFFFF
        
        # 将32位整数转换为4个字节的点分十进制格式
        return f"{(mask >> 24) & 0xFF}.{(mask >> 16) & 0xFF}.{(mask >> 8) & 0xFF}.{mask & 0xFF}"
    
    # endregion
