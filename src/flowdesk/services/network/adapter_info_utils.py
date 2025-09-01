# -*- coding: utf-8 -*-
"""
网卡信息工具函数｜提供网卡信息处理相关的纯函数工具
"""
from typing import Optional


def get_interface_type(description: str) -> str:
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


def prefix_to_netmask(prefix_length: int) -> str:
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
