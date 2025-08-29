#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNS获取直接测试脚本

这个脚本专门用于测试DNS服务器获取的核心问题，通过直接执行系统命令
并分析输出，帮助我们快速定位为什么DNS服务器显示"未配置"。

面向对象设计原则：
- 单一职责：每个方法专门负责一种测试场景
- 开闭原则：便于扩展新的测试方法和命令格式
- 异常安全：确保测试过程不会因为单个命令失败而中断
"""

import subprocess
import re
from typing import List, Dict, Any

def test_netsh_syntax():
    """
    测试netsh命令的正确语法格式
    
    这个函数专门测试不同的netsh命令语法，找出能够正确获取DNS配置的格式。
    基于Windows官方文档和实际使用经验设计多种可能的语法组合。
    """
    print("=== 测试netsh命令语法 ===")
    adapter_name = "以太网 2"
    
    # 定义多种netsh命令语法格式进行测试
    # 这些格式涵盖了Windows不同版本可能支持的语法变体
    test_commands = [
        (['netsh', 'interface', 'ipv4', 'show', 'config', f'"{adapter_name}"'], "引号包围格式"),
        (['netsh', 'interface', 'ipv4', 'show', 'config', adapter_name], "无引号格式"),
        (['netsh', 'interface', 'ipv4', 'show', 'config', f'name="{adapter_name}"'], "name=引号格式"),
        (['netsh', 'interface', 'ipv4', 'show', 'config', f'name={adapter_name}'], "name=无引号格式"),
        (['netsh', 'interface', 'ipv4', 'show', 'configs', f'"{adapter_name}"'], "configs复数格式"),
    ]
    
    for cmd, description in test_commands:
        print(f"\n--- 测试{description}: {' '.join(cmd)} ---")
        
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=15, 
                encoding='gbk', errors='ignore'
            )
            
            print(f"返回码: {result.returncode}")
            
            if result.returncode == 0:
                output = result.stdout
                if output.strip():
                    # 检查输出是否包含错误信息
                    if "此命令提供的语法不正确" in output or "用法:" in output:
                        print("❌ 语法错误")
                        print(f"错误信息: {output[:100]}...")
                    elif "IP 地址" in output or "DNS" in output or "配置" in output:
                        print("✅ 语法正确，包含配置信息")
                        print(f"输出长度: {len(output)} 字符")
                        
                        # 测试DNS解析
                        dns_found = test_dns_patterns_in_text(output, f"netsh-{description}")
                        if dns_found:
                            print(f"🎯 此语法成功获取到DNS配置！")
                        else:
                            print("⚠️ 语法正确但未找到DNS配置")
                    else:
                        print("⚠️ 语法正确但输出内容不明确")
                        print(f"输出预览: {output[:200]}...")
                else:
                    print("⚠️ 命令成功但无输出")
            else:
                print(f"❌ 命令执行失败")
                if result.stderr:
                    print(f"错误信息: {result.stderr}")
                    
        except Exception as e:
            print(f"❌ 执行异常: {str(e)}")

def test_ipconfig_full():
    """
    测试ipconfig /all的完整DNS解析功能
    
    这个函数专门分析ipconfig /all的输出，验证我们的DNS正则表达式
    是否能够正确匹配实际的DNS服务器配置信息。
    """
    print("\n=== 测试ipconfig /all DNS解析 ===")
    
    try:
        result = subprocess.run(
            ['ipconfig', '/all'], capture_output=True, text=True, 
            timeout=15, encoding='gbk', errors='ignore'
        )
        
        if result.returncode == 0:
            output = result.stdout
            print(f"ipconfig输出总长度: {len(output)} 字符")
            
            # 分割成不同的网卡配置段落
            sections = output.split('\n\n')
            print(f"找到 {len(sections)} 个配置段落")
            
            # 查找目标网卡段落
            target_section = None
            for i, section in enumerate(sections):
                if ("以太网 2" in section or 
                    "以太网适配器 以太网 2" in section or
                    "ASIX USB to Gigabit Ethernet" in section):
                    target_section = section
                    print(f"✅ 在段落 {i+1} 找到目标网卡配置")
                    break
            
            if target_section:
                print("\n--- 目标网卡配置段落 ---")
                print(target_section)
                print("-" * 50)
                
                # 测试DNS解析
                dns_found = test_dns_patterns_in_text(target_section, "ipconfig")
                
                if not dns_found:
                    print("\n🔍 进行深度分析...")
                    # 查看是否有任何IP地址
                    all_ips = re.findall(r'(\d+\.\d+\.\d+\.\d+)', target_section)
                    print(f"段落中的所有IP地址: {all_ips}")
                    
                    # 查看是否有DNS相关的行
                    lines = target_section.split('\n')
                    dns_lines = [line.strip() for line in lines if 'DNS' in line.upper()]
                    if dns_lines:
                        print("包含DNS的行:")
                        for line in dns_lines:
                            print(f"  {line}")
                    else:
                        print("❌ 段落中没有包含DNS的行")
                        
            else:
                print("❌ 未找到目标网卡配置段落")
                print("\n可用的网卡段落标题:")
                for i, section in enumerate(sections[:8], 1):
                    if section.strip():
                        first_line = section.split('\n')[0].strip()
                        if first_line:
                            print(f"  段落{i}: {first_line}")
                            
        else:
            print(f"❌ ipconfig命令执行失败: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 执行异常: {str(e)}")

def test_dns_patterns_in_text(text: str, source: str) -> bool:
    """
    在指定文本中测试DNS正则表达式匹配
    
    这个函数专门用于测试各种DNS正则表达式模式，验证哪些模式
    能够成功匹配实际的DNS配置输出，返回是否找到DNS配置。
    
    Args:
        text (str): 要测试的文本内容
        source (str): 文本来源标识
        
    Returns:
        bool: 是否成功找到DNS配置
    """
    print(f"\n--- 测试{source}的DNS解析模式 ---")
    
    # 定义所有可能的DNS匹配模式
    # 这些模式基于实际Windows系统的各种DNS配置输出格式设计
    dns_patterns = [
        (r'DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)', "标准DNS格式"),
        (r'通过 DHCP 配置的 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)', "DHCP DNS格式"),
        (r'静态配置的 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)', "静态DNS格式"),
        (r'首选 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)', "首选DNS格式"),
        (r'备用 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)', "备用DNS格式"),
        (r'Primary DNS Server[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)', "英文主DNS"),
        (r'Secondary DNS Server[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)', "英文备用DNS"),
        (r'主 DNS 后缀[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)', "主DNS后缀"),
        (r'备用 DNS 后缀[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)', "备用DNS后缀"),
    ]
    
    found_dns = False
    all_dns_servers = []
    
    # 逐个测试每种DNS匹配模式
    for pattern, description in dns_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        if matches:
            print(f"  ✅ {description}: {matches}")
            all_dns_servers.extend(matches)
            found_dns = True
        else:
            print(f"  ❌ {description}: 无匹配")
    
    # 如果标准模式都没有匹配，尝试多行DNS配置解析
    if not found_dns:
        print("\n  🔍 尝试多行DNS配置解析...")
        dns_section_pattern = r'DNS 服务器[^:]*:([^\n]*(?:\n\s+[^\n]*)*)'
        dns_section_match = re.search(dns_section_pattern, text, re.IGNORECASE)
        if dns_section_match:
            dns_section = dns_section_match.group(1)
            print(f"  找到DNS配置段落: {repr(dns_section[:100])}")
            
            # 从DNS配置段落中提取IP地址
            ip_addresses = re.findall(r'(\d+\.\d+\.\d+\.\d+)', dns_section)
            if ip_addresses:
                print(f"  ✅ 多行DNS解析成功: {ip_addresses}")
                all_dns_servers.extend(ip_addresses)
                found_dns = True
    
    # 最后尝试宽松的IP地址匹配（排除明显不是DNS的地址）
    if not found_dns:
        print("\n  🔍 尝试宽松IP地址匹配...")
        all_ips = re.findall(r'(\d+\.\d+\.\d+\.\d+)', text)
        potential_dns = []
        
        for ip in all_ips:
            # 过滤掉明显不是DNS的IP地址
            if not (ip.startswith('127.') or ip.startswith('0.') or 
                   ip.endswith('.0') or ip.endswith('.255') or 
                   ip == '255.255.255.255' or ip.startswith('169.254.')):
                # 进一步过滤：如果是192.168或10.x网段，可能是路由器DNS
                if (ip.startswith('192.168.') or ip.startswith('10.') or 
                    ip.startswith('172.') or not ip.startswith('192.168.1.')):
                    potential_dns.append(ip)
        
        if potential_dns:
            print(f"  ⚠️ 可能的DNS地址: {potential_dns}")
            # 不算作成功找到，因为这只是猜测
        else:
            print(f"  ❌ 未找到任何可能的DNS地址")
            print(f"  所有IP地址: {all_ips}")
    
    if found_dns:
        # 去重DNS服务器列表
        unique_dns = list(dict.fromkeys(all_dns_servers))  # 保持顺序的去重
        print(f"\n  🎯 最终找到的DNS服务器: {unique_dns}")
    else:
        print(f"\n  ❌ 所有DNS解析模式都失败")
    
    return found_dns

def main():
    """
    主测试函数
    
    执行完整的DNS获取测试流程，系统性地测试netsh和ipconfig命令，
    帮助快速定位DNS服务器显示"未配置"的根本原因。
    """
    print("FlowDesk DNS获取问题专项诊断")
    print("=" * 60)
    
    # 测试netsh命令的不同语法格式
    test_netsh_syntax()
    
    # 测试ipconfig命令的DNS解析
    test_ipconfig_full()
    
    print("\n" + "=" * 60)
    print("🔧 诊断完成！")
    print("\n建议的修复方案:")
    print("1. 如果netsh语法测试成功，更新NetworkService中的命令格式")
    print("2. 如果ipconfig解析成功，检查正则表达式匹配逻辑")
    print("3. 如果都失败，可能需要使用其他方法获取DNS配置")

if __name__ == "__main__":
    main()
