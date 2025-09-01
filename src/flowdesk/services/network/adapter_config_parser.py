# -*- coding: utf-8 -*-
"""
网卡配置解析器｜专门负责IP配置信息的解析和处理
"""
import subprocess
import re
import logging
from typing import Dict, Any, List
from .adapter_info_utils import prefix_to_netmask


class AdapterConfigParser:
    """
    网卡配置解析器
    
    专门负责IP配置信息的解析和处理，实现多重数据源的IP配置获取策略。
    通过netsh和ipconfig命令组合获取网卡配置，确保数据的完整性和准确性。
    
    主要功能：
    - 使用netsh命令获取详细的IP配置信息
    - 使用ipconfig命令作为补充数据源
    - 解析IPv4和IPv6地址、子网掩码、网关、DNS等配置
    - 实现智能的编码处理，支持中英文系统
    """
    
    def __init__(self):
        """初始化配置解析器"""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_adapter_ip_config(self, adapter_name: str) -> Dict[str, Any]:
        """
        获取指定网卡IP配置信息的核心实现方法
        
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
                            subnet_mask = prefix_to_netmask(prefix_len)
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
            self.logger.debug(f"成功使用ipconfig补充网卡 {adapter_name} 的完整配置信息")
        
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
                                    subnet_mask = prefix_to_netmask(prefix_len)
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
                    self.logger.debug(f"成功获取网卡 {adapter_name} 链路速度: {link_speed}")
                    
            else:
                self.logger.warning(f"ipconfig命令执行失败，返回码: {result.returncode}")
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"ipconfig命令执行超时，无法补充网卡 {adapter_name} 信息")
        except Exception as e:
            self.logger.error(f"使用ipconfig补充网卡配置失败: {str(e)}")
    
    def parse_network_config(self, adapter_name: str) -> Dict[str, Any]:
        """
        解析网络配置的公共入口方法
        
        Args:
            adapter_name (str): 网卡连接名称
            
        Returns:
            Dict[str, Any]: 完整的网络配置信息
        """
        return self.get_adapter_ip_config(adapter_name)
