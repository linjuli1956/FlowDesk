#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能子网掩码处理功能测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.flowdesk.utils.ip_validation_utils import (
    smart_validate_subnet_mask, 
    normalize_subnet_mask_for_netsh
)

def test_smart_subnet_mask():
    """测试智能子网掩码验证和标准化功能"""
    print("🧪 智能子网掩码处理功能测试")
    print("=" * 60)
    
    # 测试用例：涵盖1-32所有CIDR值和各种格式
    test_cases = [
        # 纯数字格式 (1-32)
        ("1", True, "128.0.0.0"),
        ("8", True, "255.0.0.0"),
        ("16", True, "255.255.0.0"),
        ("20", True, "255.255.240.0"),
        ("24", True, "255.255.255.0"),
        ("28", True, "255.255.255.240"),
        ("30", True, "255.255.255.252"),
        ("32", True, "255.255.255.255"),
        
        # CIDR格式
        ("/8", True, "255.0.0.0"),
        ("/16", True, "255.255.0.0"),
        ("/24", True, "255.255.255.0"),
        
        # 点分十进制格式
        ("255.255.255.0", True, "255.255.255.0"),
        ("255.255.0.0", True, "255.255.0.0"),
        ("255.0.0.0", True, "255.0.0.0"),
        
        # 无效格式
        ("0", False, "0"),
        ("33", False, "33"),
        ("invalid", False, "invalid"),
        ("", False, ""),
    ]
    
    print("测试格式 | 验证结果 | 标准化结果")
    print("-" * 60)
    
    success_count = 0
    total_count = len(test_cases)
    
    for mask_input, expected_valid, expected_normalized in test_cases:
        try:
            # 测试验证功能
            is_valid = smart_validate_subnet_mask(mask_input)
            
            # 测试标准化功能
            normalized = normalize_subnet_mask_for_netsh(mask_input)
            
            # 检查结果
            validation_ok = (is_valid == expected_valid)
            normalization_ok = (normalized == expected_normalized)
            
            if validation_ok and normalization_ok:
                status = "✅"
                success_count += 1
            else:
                status = "❌"
            
            print(f"{mask_input:12} | {is_valid:8} | {normalized:15} {status}")
            
        except Exception as e:
            print(f"{mask_input:12} | ERROR   | {str(e):15} ❌")
    
    print("-" * 60)
    print(f"测试结果: {success_count}/{total_count} 通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！智能子网掩码处理功能正常工作")
        return True
    else:
        print("⚠️  部分测试失败，请检查实现")
        return False

if __name__ == "__main__":
    test_smart_subnet_mask()
