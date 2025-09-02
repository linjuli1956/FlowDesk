#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试网卡状态获取问题
检查"以太网 2"的实际状态判断逻辑
"""

import subprocess
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flowdesk.services.network.adapter_status_analyzer import AdapterStatusAnalyzer
from flowdesk.services.network.adapter_discovery_service import AdapterDiscoveryService

def debug_adapter_status():
    """调试网卡状态获取"""
    print("🔍 开始调试网卡状态获取...")
    
    # 1. 直接运行netsh命令查看原始输出
    print("\n📋 1. netsh interface show interface 原始输出:")
    try:
        result = subprocess.run(
            ['netsh', 'interface', 'show', 'interface'],
            capture_output=True,
            text=True,
            encoding='gbk'
        )
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"命令失败: {result.stderr}")
    except Exception as e:
        print(f"执行命令异常: {e}")
    
    # 2. 使用状态分析器获取"以太网 2"状态
    print("\n🔍 2. 使用状态分析器获取'以太网 2'状态:")
    analyzer = AdapterStatusAnalyzer()
    status_info = analyzer._get_interface_status_info("以太网 2")
    print(f"状态信息: {status_info}")
    
    if status_info['admin_status'] != '未知':
        final_status, is_enabled, is_connected = analyzer.determine_final_status(
            status_info['admin_status'], 
            status_info['connect_status']
        )
        print(f"最终状态: {final_status}, 是否启用: {is_enabled}, 是否连接: {is_connected}")
    
    # 3. 获取所有网卡列表查看状态
    print("\n📋 3. 获取所有网卡状态:")
    discovery = AdapterDiscoveryService()
    adapters = discovery.get_all_adapters()
    
    for adapter in adapters:
        if "以太网" in adapter.friendly_name or "WLAN" in adapter.friendly_name:
            print(f"网卡: {adapter.friendly_name}")
            print(f"  - 状态: {adapter.status}")
            print(f"  - 描述: {adapter.description}")
            print(f"  - GUID: {adapter.adapter_id}")
            print()

if __name__ == "__main__":
    debug_adapter_status()
