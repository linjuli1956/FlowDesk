#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FlowDesk 网络工具函数模块 - 向后兼容层

作用说明：
这个模块已经按照FlowDesk项目标准进行了拆包重构，原有的631行代码
已拆分为三个专业模块：ip_validation_utils、dns_utils、network_calculation_utils

为了确保向后兼容性，本文件保留所有原有函数的重新导出。
现有代码可以继续使用原有的导入方式，无需修改。

拆分后的模块结构：
1. ip_validation_utils.py - IP地址、子网掩码、MAC地址验证和格式化
2. dns_utils.py - DNS服务器验证和推荐列表
3. network_calculation_utils.py - 网络信息计算和ipconfig解析

面向新手的使用说明：
- 新代码建议直接导入专业模块，获得更好的代码组织
- 现有代码可以继续使用本模块，保证100%向后兼容
- 所有函数功能和接口完全保持不变
"""

# 向后兼容：重新导出所有拆分后的函数和类
from .ip_validation_utils import (
    validate_ip_address,
    validate_subnet_mask, 
    validate_mac_address,
    cidr_to_subnet_mask,
    subnet_mask_to_cidr,
    is_private_ip,
    is_valid_port,
    format_mac_address,
    smart_validate_subnet_mask,
    normalize_subnet_mask_for_netsh
)

from .dns_utils import (
    validate_dns_server,
    get_recommended_dns_servers,
    COMMON_DNS_SERVERS
)

from .network_calculation_utils import (
    NetworkInterface,
    calculate_network_info,
    get_default_gateway_for_network,
    parse_ipconfig_output
)

import logging

# 获取日志记录器
logger = logging.getLogger(__name__)


# 模块测试代码 - 向后兼容
if __name__ == "__main__":
    """
    网络工具函数模块测试代码 - 向后兼容版本
    
    运行此文件可以测试所有网络工具函数，验证拆包后的向后兼容性。
    """
    print("🌐 FlowDesk 网络工具函数测试 - 拆包后兼容性验证")
    print("=" * 60)
    
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
    
    # 测试DNS服务器
    print("DNS服务器测试:")
    dns_servers = get_recommended_dns_servers()
    for provider, servers in list(dns_servers.items())[:2]:  # 只显示前两个
        print(f"  {provider}: {', '.join(servers)}")
    print()
    
    print("=" * 60)
    print("✅ 网络工具函数拆包后兼容性测试完成")

