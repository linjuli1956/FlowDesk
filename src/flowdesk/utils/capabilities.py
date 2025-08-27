#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FlowDesk 系统能力检测工具模块

作用说明：
这个模块负责检测当前系统的各种能力和权限状态，为应用程序提供环境适配支持。
主要功能包括：
1. 检测管理员权限状态
2. 获取系统版本和兼容性信息
3. 检测网络功能可用性
4. 验证硬件监控权限

面向新手的设计说明：
- 所有函数都有详细的返回值说明和异常处理
- 使用简单的布尔值和字典返回结果，便于理解
- 提供了丰富的中文注释和使用示例
- 采用防御性编程，确保在各种环境下都能正常工作

设计原则：
- 单一职责：每个函数只负责一种能力检测
- 异常安全：所有函数都有异常处理，不会导致程序崩溃
- 跨平台兼容：主要针对Windows，但保留扩展性
- 性能优化：检测结果可以缓存，避免重复检测
"""

import os
import sys
import platform
import ctypes
from typing import Dict, Any, Optional
import logging

# 获取日志记录器
logger = logging.getLogger(__name__)


def check_admin_privileges() -> bool:
    """
    检测当前程序是否以管理员权限运行
    
    作用说明：
    许多网络配置操作（如修改IP地址、DNS设置）需要管理员权限。
    这个函数帮助我们提前检测权限状态，以便：
    1. 在需要时提示用户以管理员身份运行
    2. 禁用需要管理员权限的功能按钮
    3. 显示权限状态指示器
    
    返回值：
        bool: True表示有管理员权限，False表示普通用户权限
        
    使用示例：
        if check_admin_privileges():
            print("✅ 当前具有管理员权限，可以修改网络配置")
        else:
            print("⚠️ 当前为普通用户权限，部分功能可能受限")
    """
    try:
        # Windows系统权限检测
        if platform.system() == "Windows":
            # 使用Windows API检测管理员权限
            # ctypes.windll.shell32.IsUserAnAdmin() 返回非零值表示管理员权限
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            # 非Windows系统（Linux/macOS）权限检测
            # 检测有效用户ID是否为0（root用户）
            return os.geteuid() == 0
            
    except Exception as e:
        # 权限检测失败时记录错误并返回False（安全默认值）
        logger.warning(f"管理员权限检测失败: {e}")
        return False


def get_system_capabilities() -> Dict[str, Any]:
    """
    获取系统能力和环境信息的综合报告
    
    作用说明：
    这个函数收集系统的各种能力信息，帮助应用程序：
    1. 选择合适的功能实现方式
    2. 显示系统兼容性状态
    3. 调整UI和功能可用性
    4. 生成诊断报告
    
    返回值：
        Dict[str, Any]: 包含系统能力信息的字典，包含以下键：
        - 'platform': 操作系统平台信息
        - 'python_version': Python版本信息
        - 'admin_privileges': 管理员权限状态
        - 'windows_version': Windows版本信息（仅Windows）
        - 'pyqt_available': PyQt5可用性状态
        - 'network_tools': 网络工具可用性
        - 'hardware_monitor': 硬件监控可用性
        
    使用示例：
        caps = get_system_capabilities()
        print(f"系统平台: {caps['platform']['system']}")
        print(f"管理员权限: {'是' if caps['admin_privileges'] else '否'}")
        if caps['windows_version']['major'] < 10:
            print("⚠️ 建议升级到Windows 10以获得最佳体验")
    """
    try:
        capabilities = {}
        
        # 基础平台信息
        capabilities['platform'] = {
            'system': platform.system(),           # 操作系统名称 (Windows/Linux/Darwin)
            'release': platform.release(),         # 系统版本号
            'version': platform.version(),         # 详细版本信息
            'machine': platform.machine(),         # 硬件架构 (AMD64/x86)
            'processor': platform.processor()      # 处理器信息
        }
        
        # Python环境信息
        capabilities['python_version'] = {
            'major': sys.version_info.major,       # Python主版本号
            'minor': sys.version_info.minor,       # Python次版本号
            'micro': sys.version_info.micro,       # Python修订版本号
            'full': sys.version                    # 完整版本字符串
        }
        
        # 权限状态检测
        capabilities['admin_privileges'] = check_admin_privileges()
        
        # Windows特定信息
        if platform.system() == "Windows":
            capabilities['windows_version'] = _get_windows_version()
        
        # PyQt5可用性检测
        capabilities['pyqt_available'] = _check_pyqt_availability()
        
        # 网络工具可用性检测
        capabilities['network_tools'] = _check_network_tools()
        
        # 硬件监控可用性检测
        capabilities['hardware_monitor'] = _check_hardware_monitor()
        
        logger.info("系统能力检测完成")
        return capabilities
        
    except Exception as e:
        logger.error(f"系统能力检测失败: {e}")
        # 返回最小可用的能力信息
        return {
            'platform': {'system': platform.system()},
            'python_version': {'major': sys.version_info.major},
            'admin_privileges': False,
            'pyqt_available': False,
            'network_tools': {},
            'hardware_monitor': {}
        }


def _get_windows_version() -> Dict[str, Any]:
    """
    获取详细的Windows版本信息
    
    内部函数，用于检测Windows系统的详细版本信息。
    这些信息用于：
    1. 选择合适的QSS样式表（Win7/Win10兼容性）
    2. 启用或禁用特定功能
    3. 显示系统兼容性警告
    
    返回值：
        Dict[str, Any]: Windows版本信息字典
    """
    try:
        import winreg
        
        # 从注册表读取Windows版本信息
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                           r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
        
        version_info = {}
        
        try:
            # 读取主要版本号
            version_info['major'] = winreg.QueryValueEx(key, "CurrentMajorVersionNumber")[0]
            version_info['minor'] = winreg.QueryValueEx(key, "CurrentMinorVersionNumber")[0]
        except FileNotFoundError:
            # Windows 7及更早版本使用不同的注册表项
            version = winreg.QueryValueEx(key, "CurrentVersion")[0]
            version_parts = version.split('.')
            version_info['major'] = int(version_parts[0])
            version_info['minor'] = int(version_parts[1]) if len(version_parts) > 1 else 0
        
        # 读取构建号
        try:
            version_info['build'] = winreg.QueryValueEx(key, "CurrentBuildNumber")[0]
        except FileNotFoundError:
            version_info['build'] = "未知"
        
        # 读取产品名称
        try:
            version_info['product_name'] = winreg.QueryValueEx(key, "ProductName")[0]
        except FileNotFoundError:
            version_info['product_name'] = "Windows"
        
        winreg.CloseKey(key)
        
        # 判断Windows版本类别
        if version_info['major'] >= 10:
            version_info['category'] = 'modern'  # Windows 10/11
        elif version_info['major'] == 6 and version_info['minor'] >= 1:
            version_info['category'] = 'legacy'  # Windows 7/8/8.1
        else:
            version_info['category'] = 'unsupported'  # Windows Vista及更早
        
        return version_info
        
    except Exception as e:
        logger.warning(f"Windows版本检测失败: {e}")
        return {
            'major': 10,  # 默认假设为Windows 10
            'minor': 0,
            'build': "未知",
            'product_name': "Windows",
            'category': 'modern'
        }


def _check_pyqt_availability() -> Dict[str, Any]:
    """
    检测PyQt5的可用性和版本信息
    
    内部函数，用于验证GUI框架的可用性。
    检测结果用于：
    1. 确认应用程序可以正常启动
    2. 显示PyQt版本信息
    3. 检测特定功能的支持情况
    
    返回值：
        Dict[str, Any]: PyQt5可用性信息
    """
    try:
        import PyQt5.QtCore
        import PyQt5.QtWidgets
        import PyQt5.QtGui
        
        return {
            'available': True,
            'version': PyQt5.QtCore.QT_VERSION_STR,
            'pyqt_version': PyQt5.QtCore.PYQT_VERSION_STR,
            'modules': {
                'QtCore': True,
                'QtWidgets': True,
                'QtGui': True,
                'QtNetwork': _check_module('PyQt5.QtNetwork'),
                'QtSystemTrayIcon': _check_system_tray()
            }
        }
        
    except ImportError as e:
        logger.error(f"PyQt5不可用: {e}")
        return {
            'available': False,
            'error': str(e),
            'modules': {}
        }


def _check_module(module_name: str) -> bool:
    """检测指定模块是否可用"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def _check_system_tray() -> bool:
    """检测系统托盘功能是否可用"""
    try:
        from PyQt5.QtWidgets import QApplication, QSystemTrayIcon
        
        # 需要QApplication实例才能检测系统托盘
        app = QApplication.instance()
        if app is None:
            # 如果没有QApplication实例，假设系统托盘可用
            return True
        
        return QSystemTrayIcon.isSystemTrayAvailable()
        
    except Exception:
        return False


def _check_network_tools() -> Dict[str, bool]:
    """
    检测网络工具的可用性
    
    内部函数，用于检测各种网络诊断工具的可用性。
    这些工具用于网络配置和诊断功能。
    
    返回值：
        Dict[str, bool]: 网络工具可用性状态
    """
    tools = {}
    
    # 检测Windows网络命令
    network_commands = [
        'ping',      # 网络连通性测试
        'ipconfig',  # IP配置查看和修改
        'netsh',     # 网络配置工具
        'nslookup',  # DNS查询工具
        'tracert',   # 路由跟踪
        'arp',       # ARP表管理
        'netstat'    # 网络连接状态
    ]
    
    for cmd in network_commands:
        tools[cmd] = _check_command_availability(cmd)
    
    return tools


def _check_hardware_monitor() -> Dict[str, Any]:
    """
    检测硬件监控功能的可用性
    
    内部函数，用于检测硬件监控相关的工具和权限。
    检测结果用于硬件信息页面的功能启用。
    
    返回值：
        Dict[str, Any]: 硬件监控可用性信息
    """
    monitor_info = {}
    
    # 检测LibreHardwareMonitor DLL文件
    dll_path = os.path.join(os.path.dirname(__file__), 
                           '..', '..', '..', 'assets', 'LibreHardwareMonitor')
    
    monitor_info['libre_hardware_monitor'] = {
        'dll_path': dll_path,
        'available': os.path.exists(os.path.join(dll_path, 'LibreHardwareMonitorLib.dll'))
    }
    
    # 检测WMI可用性（Windows Management Instrumentation）
    monitor_info['wmi_available'] = _check_module('wmi') if platform.system() == "Windows" else False
    
    # 检测psutil可用性（跨平台系统监控）
    monitor_info['psutil_available'] = _check_module('psutil')
    
    return monitor_info


def _check_command_availability(command: str) -> bool:
    """
    检测系统命令是否可用
    
    参数：
        command (str): 要检测的命令名称
        
    返回值：
        bool: 命令是否可用
    """
    try:
        import subprocess
        
        # 使用where命令（Windows）或which命令（Unix）检测命令是否存在
        if platform.system() == "Windows":
            result = subprocess.run(['where', command], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
        else:
            result = subprocess.run(['which', command], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
        
        return result.returncode == 0
        
    except Exception:
        return False


# 模块使用示例和测试代码
if __name__ == "__main__":
    """
    模块测试代码
    
    运行此文件可以测试所有功能并显示系统能力报告。
    这对于调试和验证系统兼容性非常有用。
    """
    print("🔍 FlowDesk 系统能力检测报告")
    print("=" * 50)
    
    # 检测管理员权限
    admin = check_admin_privileges()
    print(f"管理员权限: {'✅ 是' if admin else '❌ 否'}")
    
    # 获取完整系统能力报告
    capabilities = get_system_capabilities()
    
    # 显示平台信息
    platform_info = capabilities['platform']
    print(f"操作系统: {platform_info['system']} {platform_info['release']}")
    print(f"硬件架构: {platform_info['machine']}")
    
    # 显示Python信息
    python_info = capabilities['python_version']
    print(f"Python版本: {python_info['major']}.{python_info['minor']}.{python_info['micro']}")
    
    # 显示PyQt5信息
    pyqt_info = capabilities['pyqt_available']
    if pyqt_info['available']:
        print(f"PyQt5版本: {pyqt_info['version']}")
        print("✅ GUI框架可用")
    else:
        print("❌ PyQt5不可用")
    
    # 显示网络工具状态
    network_tools = capabilities['network_tools']
    available_tools = [tool for tool, available in network_tools.items() if available]
    print(f"可用网络工具: {', '.join(available_tools) if available_tools else '无'}")
    
    print("=" * 50)
    print("✅ 系统能力检测完成")
