#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import os

def check_netsh_status():
    """直接检查netsh命令输出"""
    try:
        result = subprocess.run(
            ['netsh', 'interface', 'show', 'interface'],
            capture_output=True,
            text=True,
            encoding='gbk',
            timeout=10
        )
        
        if result.returncode == 0:
            print("netsh interface show interface 输出:")
            print(result.stdout)
            print("\n" + "="*50)
            
            # 查找以太网 2
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if '以太网 2' in line or 'ASIX' in line:
                    print(f"找到以太网 2相关行: {line}")
                    parts = line.split()
                    if len(parts) >= 4:
                        admin_state = parts[0]
                        connect_state = parts[1]
                        print(f"管理状态: {admin_state}")
                        print(f"连接状态: {connect_state}")
        else:
            print(f"命令失败: {result.stderr}")
            
    except Exception as e:
        print(f"异常: {e}")

if __name__ == "__main__":
    check_netsh_status()
