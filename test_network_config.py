#!/usr/bin/env python3
"""
网络配置Tab核心功能测试脚本

测试网络配置Tab与NetworkService的集成功能：
1. 启动初始化：自动获取网卡信息
2. 智能IP显示：主IP显示在输入框，额外IP显示在列表
3. 网卡状态同步：选择网卡时同步更新界面
4. 刷新按钮：刷新当前网卡信息
5. 信息复制：复制网卡信息到剪贴板
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flowdesk.services.network_service import NetworkService
from flowdesk.models.adapter_info import AdapterInfo

def test_network_service():
    """测试NetworkService核心功能"""
    print("=== 测试NetworkService核心功能 ===")
    
    try:
        # 创建应用程序实例（PyQt5需要）
        app = QApplication(sys.argv)
        
        # 创建网络服务实例
        network_service = NetworkService()
        print("✓ NetworkService创建成功")
        
        # 测试获取网卡信息
        print("\n1. 测试获取所有网卡信息...")
        network_service.get_all_adapters()
        
        # 等待异步操作完成
        QTimer.singleShot(2000, lambda: test_adapter_operations(network_service, app))
        
        # 启动事件循环
        app.exec_()
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

def test_adapter_operations(network_service, app):
    """测试网卡操作功能"""
    try:
        print(f"✓ 找到 {len(network_service._adapters)} 个网卡")
        
        if network_service._adapters:
            # 测试选择网卡
            print("\n2. 测试选择网卡...")
            first_adapter = network_service._adapters[0]
            print(f"选择网卡: {first_adapter.friendly_name}")
            network_service.select_adapter(first_adapter.id)
            print("✓ 网卡选择完成")
            
            # 测试刷新网卡
            print("\n3. 测试刷新网卡...")
            network_service.refresh_current_adapter()
            print("✓ 网卡刷新完成")
            
            # 测试复制信息
            print("\n4. 测试复制网卡信息...")
            network_service.copy_adapter_info()
            print("✓ 信息复制完成")
            
            # 显示网卡详细信息
            print(f"\n=== 网卡详细信息 ===")
            print(f"网卡名称: {first_adapter.friendly_name}")
            print(f"物理地址: {first_adapter.physical_address}")
            print(f"连接状态: {'已连接' if first_adapter.is_connected else '未连接'}")
            print(f"主IP地址: {first_adapter.get_primary_ip()}")
            print(f"默认网关: {first_adapter.gateway}")
            print(f"DHCP状态: {'启用' if first_adapter.dhcp_enabled else '禁用'}")
            
            extra_ips = first_adapter.get_extra_ips()
            if extra_ips:
                print(f"额外IP地址: {len(extra_ips)}个")
                for ip, mask in extra_ips:
                    print(f"  {ip}/{mask}")
        else:
            print("✗ 未找到任何网卡")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"✗ 网卡操作测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 退出应用程序
    app.quit()

if __name__ == "__main__":
    test_network_service()
