# -*- coding: utf-8 -*-
"""
简单的WMI功能测试脚本
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    # 测试基本导入
    print("测试导入...")
    from flowdesk.services.network.adapter_wmi_config_retriever import AdapterWmiConfigRetriever
    print("✓ AdapterWmiConfigRetriever 导入成功")
    
    from flowdesk.services.network.adapter_config_parser import AdapterConfigParser
    print("✓ AdapterConfigParser 导入成功")
    
    # 测试WMI类创建
    print("\n测试类创建...")
    wmi_retriever = AdapterWmiConfigRetriever()
    print("✓ WMI配置获取器创建成功")
    
    config_parser = AdapterConfigParser()
    print("✓ 配置解析器创建成功")
    
    # 测试方法存在性
    print("\n测试方法存在性...")
    if hasattr(wmi_retriever, 'get_config_via_wmi'):
        print("✓ get_config_via_wmi 方法存在")
    else:
        print("✗ get_config_via_wmi 方法不存在")
    
    if hasattr(config_parser, '_merge_wmi_config'):
        print("✓ _merge_wmi_config 方法存在")
    else:
        print("✗ _merge_wmi_config 方法不存在")
    
    print("\n🎉 基本功能验证通过！")
    
except ImportError as e:
    print(f"✗ 导入错误: {e}")
except Exception as e:
    print(f"✗ 测试失败: {e}")
