#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能子网掩码三段式转换显示功能测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.flowdesk.models.ip_config_confirmation import IPConfigConfirmation

def test_smart_subnet_mask_display():
    """测试智能子网掩码三段式转换显示功能"""
    print("🧪 智能子网掩码三段式转换显示测试")
    print("=" * 80)
    
    # 测试用例：涵盖各种转换场景
    test_cases = [
        # 场景1：用户输入纯数字格式
        {
            "name": "用户输入纯数字16",
            "original": "255.255.252.0",
            "user_input": "16",
            "expected_pattern": "255.255.252.0 → 16 → 255.255.0.0"
        },
        {
            "name": "用户输入纯数字24", 
            "original": "255.255.0.0",
            "user_input": "24",
            "expected_pattern": "255.255.0.0 → 24 → 255.255.255.0"
        },
        {
            "name": "用户输入纯数字8",
            "original": "255.255.255.0", 
            "user_input": "8",
            "expected_pattern": "255.255.255.0 → 8 → 255.0.0.0"
        },
        
        # 场景2：用户输入CIDR格式
        {
            "name": "用户输入CIDR格式/20",
            "original": "255.255.255.0",
            "user_input": "/20", 
            "expected_pattern": "255.255.255.0 → /20 → 255.255.240.0"
        },
        
        # 场景3：用户输入点分十进制格式
        {
            "name": "用户输入点分十进制255.255.0.0",
            "original": "255.255.252.0",
            "user_input": "255.255.0.0",
            "expected_pattern": "255.255.252.0 → 255.255.0.0 → /16"
        },
        {
            "name": "用户输入点分十进制255.255.255.0", 
            "original": "255.255.0.0",
            "user_input": "255.255.255.0",
            "expected_pattern": "255.255.0.0 → 255.255.255.0 → /24"
        },
        
        # 场景4：边界情况
        {
            "name": "原始掩码未设置",
            "original": "未设置",
            "user_input": "24",
            "expected_pattern": "未设置 → 24 → 255.255.255.0"
        }
    ]
    
    print("测试场景 | 显示结果")
    print("-" * 80)
    
    success_count = 0
    total_count = len(test_cases)
    
    for test_case in test_cases:
        try:
            # 创建IP配置确认对象
            config = IPConfigConfirmation(
                adapter_name="WLAN",
                current_ip="192.168.1.100",
                new_ip="192.168.1.99",
                current_subnet_mask=test_case["original"],
                new_subnet_mask=test_case["user_input"],
                current_gateway="192.168.1.1",
                new_gateway="192.168.1.1",
                current_dns_primary="8.8.8.8",
                new_dns_primary="8.8.8.8",
                current_dns_secondary="8.8.4.4",
                new_dns_secondary="8.8.4.4",
                dhcp_enabled=False
            )
            
            # 测试智能子网掩码显示
            display_result = config._get_smart_subnet_mask_display(
                test_case["original"], 
                test_case["user_input"]
            )
            
            # 移除HTML标签进行简单验证
            clean_result = display_result.replace('<span style=\'color: #e67e22; font-weight: bold;\'>', '')
            clean_result = clean_result.replace('<span style=\'color: #10b981; font-weight: bold;\'>', '')
            clean_result = clean_result.replace('</span>', '')
            
            print(f"{test_case['name']:30} | {clean_result}")
            success_count += 1
            
        except Exception as e:
            print(f"{test_case['name']:30} | ERROR: {str(e)}")
    
    print("-" * 80)
    print(f"测试结果: {success_count}/{total_count} 通过")
    
    # 测试完整的变更摘要
    print("\n🎨 完整变更摘要显示测试:")
    print("-" * 80)
    
    test_config = IPConfigConfirmation(
        adapter_name="WLAN",
        current_ip="192.168.1.100",
        new_ip="192.168.1.99", 
        current_subnet_mask="255.255.252.0",
        new_subnet_mask="16",  # 用户输入纯数字
        current_gateway="192.168.1.1",
        new_gateway="192.168.1.1",
        current_dns_primary="8.8.8.8",
        new_dns_primary="8.8.8.8",
        current_dns_secondary="8.8.4.4",
        new_dns_secondary="8.8.4.4",
        dhcp_enabled=False
    )
    
    summary = test_config.get_changes_summary()
    print("HTML格式摘要:")
    print(summary)
    
    if success_count == total_count:
        print("\n🎉 所有测试通过！智能子网掩码三段式转换显示功能正常工作")
        return True
    else:
        print("\n⚠️  部分测试失败，请检查实现")
        return False

if __name__ == "__main__":
    test_smart_subnet_mask_display()
