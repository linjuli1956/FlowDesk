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
from .logger import get_logger
from ..models import (
    SystemCapabilities, PlatformInfo, PythonVersionInfo, 
    WindowsVersionInfo, NetworkCapabilities, HardwareMonitorCapabilities
)
logger = get_logger(__name__)


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
        # 创建平台信息数据类
        platform_info = PlatformInfo(
            system=platform.system(),
            release=platform.release(),
            version=platform.version(),
            machine=platform.machine(),
            processor=platform.processor()
        )
        
        # 创建Python版本信息数据类
        python_version_info = PythonVersionInfo(
            major=sys.version_info.major,
            minor=sys.version_info.minor,
            micro=sys.version_info.micro,
            full=sys.version
        )
        
        # 权限状态检测
        admin_privileges = check_admin_privileges()
        
        # Windows特定信息
        windows_version_info = None
        if platform.system() == "Windows":
            windows_version_info = _get_windows_version()
        
        # PyQt5可用性检测
        pyqt_available = _check_pyqt_availability()
        
        # 网络工具可用性检测
        network_tools = _check_network_tools()
        
        # 硬件监控可用性检测
        hardware_monitor = _check_hardware_monitor()
        
        # 创建系统能力数据类
        capabilities = SystemCapabilities(
            platform=platform_info,
            python_version=python_version_info,
            admin_privileges=admin_privileges,
            pyqt_available=pyqt_available,
            network_tools=network_tools,
            hardware_monitor=hardware_monitor,
            windows_version=windows_version_info
        )
        
        logger.info("系统能力检测完成")
        return capabilities
        
    except Exception as e:
        logger.error(f"系统能力检测失败: {e}")
        # 返回最小可用的能力信息
        return SystemCapabilities(
            platform=PlatformInfo(
                system=platform.system(),
                release='unknown',
                version='unknown', 
                machine='unknown',
                processor='unknown'
            ),
            python_version=PythonVersionInfo(
                major=sys.version_info.major,
                minor=0,
                micro=0,
                full='unknown'
            ),
            admin_privileges=False,
            pyqt_available=False,
            network_tools=NetworkCapabilities(),
            hardware_monitor=HardwareMonitorCapabilities(dll_path='', available=False)
        )


def _get_windows_version() -> WindowsVersionInfo:
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
        
        major = None
        minor = None
        build = None
        display_version = None
        
        try:
            # 读取主要版本号
            major = winreg.QueryValueEx(key, "CurrentMajorVersionNumber")[0]
            minor = winreg.QueryValueEx(key, "CurrentMinorVersionNumber")[0]
        except FileNotFoundError:
            # Windows 7及更早版本使用不同的注册表项
            version = winreg.QueryValueEx(key, "CurrentVersion")[0]
            version_parts = version.split('.')
            major = int(version_parts[0])
            minor = int(version_parts[1]) if len(version_parts) > 1 else 0
        
        # 读取构建号
        try:
            build = winreg.QueryValueEx(key, "CurrentBuildNumber")[0]
        except FileNotFoundError:
            build = "未知"
        
        # 读取产品名称作为显示版本
        try:
            display_version = winreg.QueryValueEx(key, "ProductName")[0]
        except FileNotFoundError:
            display_version = "Windows"
        
        winreg.CloseKey(key)
        
        # 创建Windows版本信息数据类
        return WindowsVersionInfo(
            major=major,
            minor=minor,
            build=build,
            display_version=display_version
        )
        
    except Exception as e:
        logger.warning(f"Windows版本检测失败: {e}")
        return WindowsVersionInfo(
            major=10,  # 默认假设为Windows 10
            minor=0,
            build="未知",
            display_version="Windows"
        )


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
        # 移除PyQt依赖，基于系统平台判断
        import platform
        system = platform.system().lower()
        
        # Windows和Linux通常支持系统托盘，macOS需要特殊处理
        if system in ['windows', 'linux']:
            return True
        elif system == 'darwin':  # macOS
            return True  # macOS通常支持系统托盘
        else:
            return False  # 其他系统保守返回False
        
    except Exception:
        return False


def _check_network_tools() -> NetworkCapabilities:
    """
    检测网络工具的可用性
    
    内部函数，用于检测各种网络诊断工具的可用性。
    这些工具用于网络配置和诊断功能。
    
    返回值：
        Dict[str, bool]: 网络工具可用性状态
    """
    # 检测各种网络工具的可用性
    ping_available = _check_command_availability('ping')
    tracert_available = _check_command_availability('tracert')
    netstat_available = _check_command_availability('netstat')
    ipconfig_available = _check_command_availability('ipconfig')
    nslookup_available = _check_command_availability('nslookup')
    
    return NetworkCapabilities(
        ping=ping_available,
        tracert=tracert_available,
        netstat=netstat_available,
        ipconfig=ipconfig_available,
        nslookup=nslookup_available
    )


def _check_hardware_monitor() -> HardwareMonitorCapabilities:
    """
    检测硬件监控功能的可用性
    
    内部函数，用于检测硬件监控相关的工具和权限。
    检测结果用于硬件信息页面的功能启用。
    
    返回值：
        Dict[str, Any]: 硬件监控可用性信息
    """
    # 检测LibreHardwareMonitor DLL文件
    dll_path = os.path.join(os.path.dirname(__file__), 
                           '..', '..', '..', 'assets', 'LibreHardwareMonitor')
    
    dll_available = os.path.exists(os.path.join(dll_path, 'LibreHardwareMonitorLib.dll'))
    
    return HardwareMonitorCapabilities(
        dll_path=dll_path,
        available=dll_available
    )


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
