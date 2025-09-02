# -*- coding: utf-8 -*-
"""
网络计算工具｜专门负责网络信息计算、ipconfig解析和网络接口数据处理
"""
import re
import ipaddress
import logging
from typing import Optional, List, Dict
from dataclasses import dataclass
from .ip_validation_utils import validate_ip_address, subnet_mask_to_cidr

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
        
        logger.debug(f"解析到 {len(interfaces)} 个网络接口")
        
    except Exception as e:
        logger.error(f"ipconfig输出解析失败: {e}")
    
    return interfaces


# 模块测试代码
if __name__ == "__main__":
    """
    网络计算工具模块测试代码
    
    运行此文件可以测试所有网络计算相关函数。
    """
    print("🧮 网络计算工具函数测试")
    print("=" * 50)
    
    # 测试网络信息计算
    print("网络信息计算测试:")
    info = calculate_network_info("192.168.1.100", "255.255.255.0")
    for key, value in info.items():
        print(f"  {key}: {value}")
    print()
    
    # 测试网关地址推算
    print("网关地址推算测试:")
    gateway = get_default_gateway_for_network("192.168.1.100", "255.255.255.0")
    print(f"  推荐网关: {gateway}")
    print()
    
    print("=" * 50)
    print("✅ 网络计算工具函数测试完成")
