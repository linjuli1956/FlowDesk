#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNS获取调试脚本

这个临时调试脚本用于分析为什么DNS服务器显示"未配置"的问题。
通过直接执行netsh和ipconfig命令，查看实际的命令输出格式，
帮助我们完善DNS解析的正则表达式匹配模式。

技术目标：
1. 执行netsh interface ipv4 show config命令查看DNS配置输出格式
2. 执行ipconfig /all命令查看完整网络配置输出
3. 分析实际输出与现有正则表达式的匹配情况
4. 为完善DNS解析逻辑提供数据支持

面向对象设计：
- 使用类封装调试功能，遵循单一职责原则
- 每个方法专门负责一种命令的执行和分析
- 提供清晰的输出格式便于问题诊断
"""

import subprocess
import re
from typing import List, Dict, Any

class DNSDebugger:
    """
    DNS获取调试器类
    
    这个类专门用于调试DNS服务器获取问题，通过执行系统命令
    并分析输出格式，帮助识别DNS解析逻辑中的问题。
    
    设计原则：
    - 单一职责：专门负责DNS调试功能
    - 开闭原则：便于扩展新的调试方法
    - 异常安全：确保调试过程不影响主程序
    """
    
    def __init__(self):
        """初始化DNS调试器"""
        self.adapter_name = "以太网 2"  # 目标网卡名称
    
    def debug_netsh_dns_config(self) -> None:
        """
        调试netsh命令的DNS配置输出
        
        执行netsh interface ipv4 show config命令，查看实际的DNS配置输出格式。
        这个方法帮助我们理解为什么现有的正则表达式无法正确匹配DNS服务器。
        """
        print("=== 调试netsh DNS配置命令 ===")
        
        try:
            # 执行netsh命令获取IPv4配置
            cmd = ['netsh', 'interface', 'ipv4', 'show', 'config', f'name="{self.adapter_name}"']
            print(f"执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=15, encoding='gbk', errors='ignore'
            )
            
            print(f"返回码: {result.returncode}")
            
            if result.returncode == 0:
                print("命令输出:")
                print("-" * 50)
                print(result.stdout)
                print("-" * 50)
                
                # 测试现有的DNS正则表达式
                self._test_dns_patterns(result.stdout)
                
            else:
                print(f"命令执行失败: {result.stderr}")
                
        except Exception as e:
            print(f"执行netsh命令时发生异常: {str(e)}")
    
    def debug_ipconfig_output(self) -> None:
        """
        调试ipconfig命令的完整输出
        
        执行ipconfig /all命令，查看完整的网络配置输出格式。
        重点关注DNS服务器配置的显示方式。
        """
        print("\n=== 调试ipconfig完整输出 ===")
        
        try:
            # 执行ipconfig /all命令
            cmd = ['ipconfig', '/all']
            print(f"执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=15, encoding='gbk', errors='ignore'
            )
            
            print(f"返回码: {result.returncode}")
            
            if result.returncode == 0:
                # 查找目标网卡的配置段落
                output = result.stdout
                adapter_sections = output.split('\n\n')
                
                for section in adapter_sections:
                    if self.adapter_name in section or "以太网适配器 以太网 2" in section:
                        print("找到目标网卡配置段落:")
                        print("-" * 50)
                        print(section)
                        print("-" * 50)
                        
                        # 测试DNS解析模式
                        self._test_ipconfig_dns_patterns(section)
                        break
                else:
                    print(f"未找到网卡 {self.adapter_name} 的配置段落")
                    print("所有可用的网卡段落:")
                    for i, section in enumerate(adapter_sections[:5]):  # 只显示前5个段落
                        print(f"段落 {i+1}:")
                        print(section[:200] + "..." if len(section) > 200 else section)
                        print("-" * 30)
                
            else:
                print(f"命令执行失败: {result.stderr}")
                
        except Exception as e:
            print(f"执行ipconfig命令时发生异常: {str(e)}")
    
    def _test_dns_patterns(self, output: str) -> None:
        """
        测试netsh输出的DNS正则表达式匹配
        
        使用现有的DNS正则表达式模式测试实际的netsh命令输出，
        帮助识别哪些模式有效，哪些需要改进。
        
        Args:
            output (str): netsh命令的输出内容
        """
        print("\n--- 测试netsh DNS正则表达式匹配 ---")
        
        # 现有的DNS正则表达式模式
        dns_patterns = [
            r'通过 DHCP 配置的 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',
            r'DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',
            r'静态配置的 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',
            r'DNS Servers[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',
        ]
        
        for i, pattern in enumerate(dns_patterns, 1):
            print(f"模式 {i}: {pattern}")
            matches = re.findall(pattern, output, re.IGNORECASE | re.MULTILINE)
            if matches:
                print(f"  ✓ 匹配成功: {matches}")
            else:
                print(f"  ✗ 无匹配")
        
        # 尝试更宽松的匹配模式
        print("\n--- 尝试更宽松的匹配模式 ---")
        loose_patterns = [
            r'DNS[^:]*:\s*(\d+\.\d+\.\d+\.\d+)',
            r'(\d+\.\d+\.\d+\.\d+)',  # 所有IP地址
        ]
        
        for i, pattern in enumerate(loose_patterns, 1):
            print(f"宽松模式 {i}: {pattern}")
            matches = re.findall(pattern, output, re.IGNORECASE | re.MULTILINE)
            if matches:
                print(f"  ✓ 匹配到: {matches[:5]}...")  # 只显示前5个
            else:
                print(f"  ✗ 无匹配")
    
    def _test_ipconfig_dns_patterns(self, section: str) -> None:
        """
        测试ipconfig输出的DNS正则表达式匹配
        
        Args:
            section (str): ipconfig中目标网卡的配置段落
        """
        print("\n--- 测试ipconfig DNS正则表达式匹配 ---")
        
        # 现有的DNS正则表达式模式
        dns_patterns = [
            r'DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',
            r'通过 DHCP 配置的 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',
            r'静态配置的 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',
        ]
        
        for i, pattern in enumerate(dns_patterns, 1):
            print(f"模式 {i}: {pattern}")
            matches = re.findall(pattern, section, re.IGNORECASE)
            if matches:
                print(f"  ✓ 匹配成功: {matches}")
            else:
                print(f"  ✗ 无匹配")

def main():
    """
    主调试函数
    
    执行完整的DNS获取调试流程，包括netsh和ipconfig命令的输出分析。
    这个函数提供了系统化的调试方法，帮助快速定位DNS获取问题。
    """
    print("DNS获取问题调试工具")
    print("=" * 50)
    
    debugger = DNSDebugger()
    
    # 调试netsh命令
    debugger.debug_netsh_dns_config()
    
    # 调试ipconfig命令
    debugger.debug_ipconfig_output()
    
    print("\n调试完成！请查看上述输出，分析DNS解析问题的原因。")

if __name__ == "__main__":
    main()
