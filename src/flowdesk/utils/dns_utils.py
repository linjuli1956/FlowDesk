# -*- coding: utf-8 -*-
"""
DNS工具函数｜专门负责DNS服务器相关的验证和推荐功能
"""
import logging
from typing import Dict, List
from .ip_validation_utils import validate_ip_address

# 获取日志记录器
logger = logging.getLogger(__name__)


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
    DNS工具模块测试代码
    
    运行此文件可以测试所有DNS相关函数。
    """
    print("🌐 DNS工具函数测试")
    print("=" * 50)
    
    # 测试DNS服务器验证
    test_dns = ["8.8.8.8", "1.1.1.1", "223.5.5.5", "invalid.dns"]
    print("DNS服务器验证测试:")
    for dns in test_dns:
        valid = validate_dns_server(dns)
        status = "✅ 有效" if valid else "❌ 无效"
        print(f"  {dns}: {status}")
    print()
    
    # 测试推荐DNS服务器
    print("推荐DNS服务器列表:")
    dns_servers = get_recommended_dns_servers()
    for provider, servers in dns_servers.items():
        print(f"  {provider}: {', '.join(servers)}")
    print()
    
    print("=" * 50)
    print("✅ DNS工具函数测试完成")
