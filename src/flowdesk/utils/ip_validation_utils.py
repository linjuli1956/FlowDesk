# -*- coding: utf-8 -*-
"""
IP地址验证工具｜专门负责IP地址、子网掩码、MAC地址等网络地址的验证和格式化
"""
import re
import ipaddress
import logging
from typing import Union

# 获取日志记录器
logger = logging.getLogger(__name__)


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


def smart_validate_subnet_mask(mask: str) -> bool:
    """
    智能验证子网掩码格式，支持多种输入格式
    
    作用说明：
    支持三种子网掩码格式的智能验证：
    1. 纯数字格式：1-32 (自动识别为CIDR)
    2. CIDR格式：/1 到 /32
    3. 点分十进制格式：255.255.255.0
    
    参数说明：
        mask (str): 要验证的子网掩码字符串
        
    返回值：
        bool: True表示格式有效，False表示格式无效
        
    使用示例：
        # 支持纯数字CIDR
        if smart_validate_subnet_mask("24"):
            print("✅ 纯数字CIDR格式有效")
            
        # 支持标准CIDR格式
        if smart_validate_subnet_mask("/24"):
            print("✅ 标准CIDR格式有效")
            
        # 支持点分十进制格式
        if smart_validate_subnet_mask("255.255.255.0"):
            print("✅ 点分十进制格式有效")
    """
    if not mask or not isinstance(mask, str):
        return False
    
    mask = mask.strip()
    
    try:
        # 检查纯数字格式 (如 24)
        if mask.isdigit():
            cidr = int(mask)
            return 1 <= cidr <= 32
        
        # 使用原有的验证逻辑处理CIDR和点分十进制格式
        return validate_subnet_mask(mask)
        
    except (ValueError, TypeError):
        logger.debug(f"智能子网掩码验证失败: {mask}")
        return False


def normalize_subnet_mask_for_netsh(mask: str) -> str:
    """
    为netsh命令标准化子网掩码格式
    
    作用说明：
    将各种子网掩码输入格式统一转换为netsh命令要求的点分十进制格式。
    支持智能识别纯数字、CIDR和点分十进制三种输入格式。
    
    参数说明：
        mask (str): 原始子网掩码字符串
        
    返回值：
        str: 点分十进制格式的子网掩码，转换失败返回原字符串
        
    使用示例：
        # 纯数字转换
        result = normalize_subnet_mask_for_netsh("24")
        print(result)  # 输出: 255.255.255.0
        
        # CIDR转换
        result = normalize_subnet_mask_for_netsh("/16")
        print(result)  # 输出: 255.255.0.0
        
        # 点分十进制保持不变
        result = normalize_subnet_mask_for_netsh("255.255.255.0")
        print(result)  # 输出: 255.255.255.0
    """
    if not mask or not isinstance(mask, str):
        logger.warning(f"无效的子网掩码输入: {mask}")
        return mask
    
    mask = mask.strip()
    
    try:
        # 处理纯数字格式 (如 24)
        if mask.isdigit():
            cidr = int(mask)
            if 1 <= cidr <= 32:
                converted = cidr_to_subnet_mask(cidr)
                logger.debug(f"纯数字CIDR转换: {mask} -> {converted}")
                return converted
            else:
                logger.warning(f"无效的CIDR值: {mask}")
                return mask
        
        # 处理CIDR格式 (如 /24)
        if mask.startswith('/'):
            cidr = int(mask[1:])
            if 1 <= cidr <= 32:
                converted = cidr_to_subnet_mask(cidr)
                logger.debug(f"CIDR格式转换: {mask} -> {converted}")
                return converted
            else:
                logger.warning(f"无效的CIDR值: {mask}")
                return mask
        
        # 已经是点分十进制格式，验证后直接返回
        if validate_subnet_mask(mask):
            logger.debug(f"点分十进制格式保持不变: {mask}")
            return mask
        else:
            logger.warning(f"无效的点分十进制子网掩码: {mask}")
            return mask
            
    except (ValueError, TypeError) as e:
        logger.error(f"子网掩码标准化失败: {mask}, 错误: {e}")
        return mask


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


# 模块测试代码
if __name__ == "__main__":
    """
    IP验证工具模块测试代码
    
    运行此文件可以测试所有IP验证相关函数。
    """
    print("🔍 IP验证工具函数测试")
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
    
    # 测试CIDR转换
    print("CIDR转换测试:")
    print(f"  /24 -> {cidr_to_subnet_mask(24)}")
    print(f"  255.255.255.0 -> /{subnet_mask_to_cidr('255.255.255.0')}")
    print()
    
    print("=" * 50)
    print("✅ IP验证工具函数测试完成")
