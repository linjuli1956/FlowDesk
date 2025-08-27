#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FlowDesk 网络工具函数模块

作用说明：
这个模块提供网络相关的实用工具函数，主要用于：
1. IP地址和子网掩码的验证和格式化
2. 网络配置参数的校验
3. 网络连通性测试和诊断
4. 网络接口信息的解析和处理

面向新手的设计说明：
- 所有函数都有详细的参数说明和返回值描述
- 提供丰富的使用示例和错误处理
- 支持IPv4和IPv6地址处理
- 包含网络配置的常用验证规则
- 采用纯Python实现，无外部依赖

设计原则：
- 输入验证：严格验证所有网络参数的格式和有效性
- 异常安全：所有函数都有完整的异常处理
- 跨平台兼容：使用标准库实现，支持所有平台
- 性能优化：使用高效的正则表达式和算法
"""

import re
import socket
import ipaddress
import logging
from typing import Optional, List, Dict, Tuple, Union
from dataclasses import dataclass

# 获取日志记录器
logger = logging.getLogger(__name__)


@dataclass
class NetworkInterface:
    """
    网络接口信息数据类
    
    作用说明：
    封装网络接口的所有相关信息，便于在UI中显示和管理。
    
    属性说明：
        name: 接口名称（如"本地连接"、"以太网"）
        description: 接口描述信息
        mac_address: MAC地址
        ip_address: IP地址
        subnet_mask: 子网掩码
        gateway: 默认网关
        dns_servers: DNS服务器列表
        dhcp_enabled: 是否启用DHCP
        status: 接口状态（已连接/已断开）
    """
    name: str
    description: str = ""
    mac_address: str = ""
    ip_address: str = ""
    subnet_mask: str = ""
    gateway: str = ""
    dns_servers: List[str] = None
    dhcp_enabled: bool = True
    status: str = "未知"
    
    def __post_init__(self):
        if self.dns_servers is None:
            self.dns_servers = []


def validate_ip_address(ip: str) -> bool:
    """
    验证IP地址格式是否正确
    
    作用说明：
    检查用户输入的IP地址是否符合IPv4或IPv6格式规范。
    用于网络配置界面的输入验证，防止用户输入无效的IP地址。
    
    参数说明：
        ip (str): 要验证的IP地址字符串
        
    返回值：
        bool: True表示IP地址格式正确，False表示格式错误
        
    使用示例：
        # 验证IPv4地址
        if validate_ip_address("192.168.1.100"):
            print("✅ IP地址格式正确")
        else:
            print("❌ IP地址格式错误")
            
        # 验证IPv6地址
        if validate_ip_address("2001:db8::1"):
            print("✅ IPv6地址格式正确")
        else:
            print("❌ IPv6地址格式错误")
    """
    if not ip or not isinstance(ip, str):
        return False
    
    try:
        # 使用Python标准库验证IP地址
        ipaddress.ip_address(ip.strip())
        return True
    except ValueError:
        logger.debug(f"无效的IP地址格式: {ip}")
        return False


def validate_subnet_mask(mask: str) -> bool:
    """
    验证子网掩码格式是否正确
    
    作用说明：
    检查子网掩码是否符合标准格式，支持点分十进制和CIDR两种格式。
    例如：255.255.255.0 或 /24 都是有效的子网掩码。
    
    参数说明：
        mask (str): 要验证的子网掩码字符串
        
    返回值：
        bool: True表示子网掩码格式正确，False表示格式错误
        
    使用示例：
        # 验证点分十进制格式
        if validate_subnet_mask("255.255.255.0"):
            print("✅ 子网掩码格式正确")
            
        # 验证CIDR格式
        if validate_subnet_mask("/24"):
            print("✅ CIDR格式正确")
        else:
            print("❌ 子网掩码格式错误")
    """
    if not mask or not isinstance(mask, str):
        return False
    
    mask = mask.strip()
    
    try:
        # 检查CIDR格式 (如 /24)
        if mask.startswith('/'):
            cidr = int(mask[1:])
            return 0 <= cidr <= 32
        
        # 检查点分十进制格式 (如 255.255.255.0)
        if validate_ip_address(mask):
            # 验证是否为有效的子网掩码
            mask_int = int(ipaddress.IPv4Address(mask))
            # 子网掩码必须是连续的1后跟连续的0
            # 例如：11111111.11111111.11111111.00000000 (255.255.255.0)
            binary = bin(mask_int)[2:].zfill(32)
            return re.match(r'^1*0*$', binary) is not None
        
        return False
        
    except (ValueError, ipaddress.AddressValueError):
        logger.debug(f"无效的子网掩码格式: {mask}")
        return False


def validate_mac_address(mac: str) -> bool:
    """
    验证MAC地址格式是否正确
    
    作用说明：
    检查MAC地址是否符合标准格式，支持多种分隔符。
    例如：AA:BB:CC:DD:EE:FF 或 AA-BB-CC-DD-EE-FF 都是有效格式。
    
    参数说明：
        mac (str): 要验证的MAC地址字符串
        
    返回值：
        bool: True表示MAC地址格式正确，False表示格式错误
        
    使用示例：
        if validate_mac_address("AA:BB:CC:DD:EE:FF"):
            print("✅ MAC地址格式正确")
        else:
            print("❌ MAC地址格式错误")
    """
    if not mac or not isinstance(mac, str):
        return False
    
    # MAC地址的正则表达式模式
    # 支持 AA:BB:CC:DD:EE:FF 和 AA-BB-CC-DD-EE-FF 格式
    mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
    
    return bool(re.match(mac_pattern, mac.strip()))


def cidr_to_subnet_mask(cidr: int) -> str:
    """
    将CIDR表示法转换为点分十进制子网掩码
    
    作用说明：
    将网络前缀长度（如24）转换为标准的子网掩码格式（如255.255.255.0）。
    便于在UI中显示和用户理解。
    
    参数说明：
        cidr (int): CIDR值（0-32）
        
    返回值：
        str: 点分十进制格式的子网掩码，无效输入返回空字符串
        
    使用示例：
        mask = cidr_to_subnet_mask(24)
        print(f"CIDR /24 对应的子网掩码: {mask}")  # 输出: 255.255.255.0
        
        mask = cidr_to_subnet_mask(16)
        print(f"CIDR /16 对应的子网掩码: {mask}")  # 输出: 255.255.0.0
    """
    if not isinstance(cidr, int) or not (0 <= cidr <= 32):
        logger.warning(f"无效的CIDR值: {cidr}")
        return ""
    
    try:
        # 创建网络对象并获取子网掩码
        network = ipaddress.IPv4Network(f"0.0.0.0/{cidr}", strict=False)
        return str(network.netmask)
    except ValueError as e:
        logger.error(f"CIDR转换失败: {e}")
        return ""


def subnet_mask_to_cidr(mask: str) -> int:
    """
    将点分十进制子网掩码转换为CIDR表示法
    
    作用说明：
    将标准子网掩码格式转换为网络前缀长度，便于网络计算和配置。
    
    参数说明：
        mask (str): 点分十进制格式的子网掩码
        
    返回值：
        int: CIDR值（0-32），无效输入返回-1
        
    使用示例：
        cidr = subnet_mask_to_cidr("255.255.255.0")
        print(f"子网掩码 255.255.255.0 对应的CIDR: /{cidr}")  # 输出: /24
        
        cidr = subnet_mask_to_cidr("255.255.0.0")
        print(f"子网掩码 255.255.0.0 对应的CIDR: /{cidr}")  # 输出: /16
    """
    if not validate_subnet_mask(mask):
        logger.warning(f"无效的子网掩码: {mask}")
        return -1
    
    try:
        # 将子网掩码转换为整数，然后计算前缀长度
        mask_int = int(ipaddress.IPv4Address(mask))
        # 计算二进制中1的个数
        return bin(mask_int).count('1')
    except ValueError as e:
        logger.error(f"子网掩码转换失败: {e}")
        return -1


def calculate_network_info(ip: str, mask: str) -> Dict[str, str]:
    """
    计算网络信息（网络地址、广播地址、主机范围等）
    
    作用说明：
    根据IP地址和子网掩码计算完整的网络信息，用于网络配置的验证和显示。
    
    参数说明：
        ip (str): IP地址
        mask (str): 子网掩码（支持点分十进制和CIDR格式）
        
    返回值：
        Dict[str, str]: 包含网络信息的字典，包含以下键：
        - network: 网络地址
        - broadcast: 广播地址
        - first_host: 第一个可用主机地址
        - last_host: 最后一个可用主机地址
        - total_hosts: 总主机数
        - usable_hosts: 可用主机数
        
    使用示例：
        info = calculate_network_info("192.168.1.100", "255.255.255.0")
        print(f"网络地址: {info['network']}")
        print(f"广播地址: {info['broadcast']}")
        print(f"可用主机范围: {info['first_host']} - {info['last_host']}")
        print(f"可用主机数: {info['usable_hosts']}")
    """
    result = {}
    
    try:
        # 处理CIDR格式的子网掩码
        if mask.startswith('/'):
            cidr = int(mask[1:])
            network_str = f"{ip}/{cidr}"
        else:
            cidr = subnet_mask_to_cidr(mask)
            if cidr == -1:
                raise ValueError("无效的子网掩码")
            network_str = f"{ip}/{cidr}"
        
        # 创建网络对象
        network = ipaddress.IPv4Network(network_str, strict=False)
        
        # 计算网络信息
        result['network'] = str(network.network_address)
        result['broadcast'] = str(network.broadcast_address)
        result['netmask'] = str(network.netmask)
        result['cidr'] = f"/{network.prefixlen}"
        
        # 计算主机地址范围
        hosts = list(network.hosts())
        if hosts:
            result['first_host'] = str(hosts[0])
            result['last_host'] = str(hosts[-1])
            result['usable_hosts'] = str(len(hosts))
        else:
            # 对于/31和/32网络
            result['first_host'] = str(network.network_address)
            result['last_host'] = str(network.broadcast_address)
            result['usable_hosts'] = "0" if network.prefixlen == 32 else "2"
        
        result['total_hosts'] = str(network.num_addresses)
        
        logger.debug(f"网络信息计算完成: {network_str}")
        
    except (ValueError, ipaddress.AddressValueError) as e:
        logger.error(f"网络信息计算失败: {e}")
        result = {
            'network': '错误',
            'broadcast': '错误',
            'netmask': '错误',
            'cidr': '错误',
            'first_host': '错误',
            'last_host': '错误',
            'total_hosts': '0',
            'usable_hosts': '0'
        }
    
    return result


def is_private_ip(ip: str) -> bool:
    """
    判断IP地址是否为私有地址
    
    作用说明：
    检查IP地址是否属于私有网络范围，用于网络配置的安全性提示。
    私有IP范围：10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
    
    参数说明：
        ip (str): 要检查的IP地址
        
    返回值：
        bool: True表示私有IP，False表示公网IP
        
    使用示例：
        if is_private_ip("192.168.1.1"):
            print("这是私有IP地址")
        else:
            print("这是公网IP地址")
    """
    if not validate_ip_address(ip):
        return False
    
    try:
        ip_obj = ipaddress.IPv4Address(ip)
        return ip_obj.is_private
    except ValueError:
        return False


def is_valid_port(port: Union[str, int]) -> bool:
    """
    验证端口号是否有效
    
    作用说明：
    检查端口号是否在有效范围内（1-65535），用于远程桌面等功能的配置验证。
    
    参数说明：
        port (Union[str, int]): 要验证的端口号
        
    返回值：
        bool: True表示端口号有效，False表示无效
        
    使用示例：
        if is_valid_port(3389):
            print("✅ 端口号有效")
        else:
            print("❌ 端口号无效")
    """
    try:
        port_int = int(port)
        return 1 <= port_int <= 65535
    except (ValueError, TypeError):
        return False


def format_mac_address(mac: str, separator: str = ":") -> str:
    """
    格式化MAC地址
    
    作用说明：
    将MAC地址统一格式化为指定的分隔符格式，便于显示和比较。
    
    参数说明：
        mac (str): 原始MAC地址
        separator (str): 分隔符（默认为":"）
        
    返回值：
        str: 格式化后的MAC地址，无效输入返回原字符串
        
    使用示例：
        formatted = format_mac_address("aa-bb-cc-dd-ee-ff", ":")
        print(formatted)  # 输出: AA:BB:CC:DD:EE:FF
    """
    if not validate_mac_address(mac):
        return mac
    
    try:
        # 移除所有分隔符并转换为大写
        clean_mac = re.sub(r'[:-]', '', mac.upper())
        # 重新添加分隔符
        formatted = separator.join([clean_mac[i:i+2] for i in range(0, 12, 2)])
        return formatted
    except Exception as e:
        logger.warning(f"MAC地址格式化失败: {e}")
        return mac


def get_default_gateway_for_network(network_ip: str, subnet_mask: str) -> str:
    """
    获取网络的默认网关地址（通常是第一个可用IP）
    
    作用说明：
    根据网络地址和子网掩码推算默认网关地址，用于自动配置网络参数。
    
    参数说明：
        network_ip (str): 网络中的任意IP地址
        subnet_mask (str): 子网掩码
        
    返回值：
        str: 推荐的网关地址，计算失败返回空字符串
        
    使用示例：
        gateway = get_default_gateway_for_network("192.168.1.100", "255.255.255.0")
        print(f"推荐网关: {gateway}")  # 输出: 192.168.1.1
    """
    try:
        network_info = calculate_network_info(network_ip, subnet_mask)
        if network_info['first_host'] != '错误':
            return network_info['first_host']
        return ""
    except Exception as e:
        logger.error(f"网关地址计算失败: {e}")
        return ""


def validate_dns_server(dns: str) -> bool:
    """
    验证DNS服务器地址是否有效
    
    作用说明：
    检查DNS服务器地址格式，确保网络配置的正确性。
    
    参数说明：
        dns (str): DNS服务器地址
        
    返回值：
        bool: True表示DNS地址有效，False表示无效
        
    使用示例：
        if validate_dns_server("8.8.8.8"):
            print("✅ DNS服务器地址有效")
        else:
            print("❌ DNS服务器地址无效")
    """
    return validate_ip_address(dns)


def parse_ipconfig_output(output: str) -> List[NetworkInterface]:
    """
    解析ipconfig命令的输出，提取网络接口信息
    
    作用说明：
    将ipconfig /all命令的输出解析为结构化的网络接口信息，
    用于在UI中显示当前的网络配置状态。
    
    参数说明：
        output (str): ipconfig命令的输出文本
        
    返回值：
        List[NetworkInterface]: 网络接口信息列表
        
    使用示例：
        from .subprocess_helper import run_command
        result = run_command("ipconfig /all")
        if result.success:
            interfaces = parse_ipconfig_output(result.output)
            for interface in interfaces:
                print(f"接口: {interface.name}")
                print(f"IP地址: {interface.ip_address}")
    """
    interfaces = []
    current_interface = None
    
    try:
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 检测新的网络适配器
            if '适配器' in line or 'adapter' in line.lower():
                if current_interface:
                    interfaces.append(current_interface)
                
                # 提取适配器名称
                adapter_name = line.split(':')[0].strip()
                current_interface = NetworkInterface(name=adapter_name)
                continue
            
            if not current_interface:
                continue
            
            # 解析各种网络参数
            if 'IPv4' in line and '地址' in line:
                ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if ip_match:
                    current_interface.ip_address = ip_match.group(1)
            
            elif '子网掩码' in line or 'Subnet Mask' in line:
                mask_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if mask_match:
                    current_interface.subnet_mask = mask_match.group(1)
            
            elif '默认网关' in line or 'Default Gateway' in line:
                gateway_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if gateway_match:
                    current_interface.gateway = gateway_match.group(1)
            
            elif 'DNS' in line and '服务器' in line:
                dns_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if dns_match:
                    current_interface.dns_servers.append(dns_match.group(1))
            
            elif '物理地址' in line or 'Physical Address' in line:
                mac_match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', line)
                if mac_match:
                    current_interface.mac_address = mac_match.group(0)
            
            elif 'DHCP' in line and ('启用' in line or 'Enabled' in line):
                current_interface.dhcp_enabled = '是' in line or 'Yes' in line
        
        # 添加最后一个接口
        if current_interface:
            interfaces.append(current_interface)
        
        logger.info(f"解析到 {len(interfaces)} 个网络接口")
        
    except Exception as e:
        logger.error(f"ipconfig输出解析失败: {e}")
    
    return interfaces


# 常用的DNS服务器地址
COMMON_DNS_SERVERS = {
    "Google DNS": ["8.8.8.8", "8.8.4.4"],
    "Cloudflare DNS": ["1.1.1.1", "1.0.0.1"],
    "阿里DNS": ["223.5.5.5", "223.6.6.6"],
    "腾讯DNS": ["119.29.29.29", "182.254.116.116"],
    "百度DNS": ["180.76.76.76"],
    "114DNS": ["114.114.114.114", "114.114.115.115"]
}


def get_recommended_dns_servers() -> Dict[str, List[str]]:
    """
    获取推荐的DNS服务器列表
    
    返回值：
        Dict[str, List[str]]: DNS服务器提供商及其地址列表
    """
    return COMMON_DNS_SERVERS.copy()


# 模块测试代码
if __name__ == "__main__":
    """
    模块测试代码
    
    运行此文件可以测试所有网络工具函数。
    """
    print("🌐 FlowDesk 网络工具函数测试")
    print("=" * 50)
    
    # 测试IP地址验证
    test_ips = ["192.168.1.1", "256.256.256.256", "10.0.0.1", "invalid"]
    print("IP地址验证测试:")
    for ip in test_ips:
        valid = validate_ip_address(ip)
        status = "✅ 有效" if valid else "❌ 无效"
        print(f"  {ip}: {status}")
    print()
    
    # 测试子网掩码验证
    test_masks = ["255.255.255.0", "/24", "255.255.0.0", "/16", "invalid"]
    print("子网掩码验证测试:")
    for mask in test_masks:
        valid = validate_subnet_mask(mask)
        status = "✅ 有效" if valid else "❌ 无效"
        print(f"  {mask}: {status}")
    print()
    
    # 测试网络信息计算
    print("网络信息计算测试:")
    info = calculate_network_info("192.168.1.100", "255.255.255.0")
    for key, value in info.items():
        print(f"  {key}: {value}")
    print()
    
    # 测试CIDR转换
    print("CIDR转换测试:")
    print(f"  /24 -> {cidr_to_subnet_mask(24)}")
    print(f"  255.255.255.0 -> /{subnet_mask_to_cidr('255.255.255.0')}")
    print()
    
    print("=" * 50)
    print("✅ 网络工具函数测试完成")
