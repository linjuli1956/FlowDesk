#!/usr/bin/env python3
"""
管理员权限工具模块 - FlowDesk权限管理核心

这个模块提供Windows UAC权限检查和申请功能，确保FlowDesk能够以管理员权限运行，
从而执行需要提升权限的网络配置操作（如netsh命令）。

主要功能：
1. 检查当前进程是否具有管理员权限
2. 以管理员权限重新启动应用程序
3. 提供用户友好的权限申请提示

设计原则：
- 遵循Windows安全最佳实践
- 提供清晰的用户提示信息
- 确保权限申请的透明性和安全性
"""

import sys
import os
import ctypes
import subprocess


def is_admin() -> bool:
    """
    检查当前进程是否具有管理员权限
    
    使用Windows API检查当前用户令牌是否具有管理员权限。
    这是确定是否需要UAC提升的关键方法。
    
    Returns:
        bool: True表示具有管理员权限，False表示普通用户权限
        
    Raises:
        无直接异常抛出，权限检查失败时返回False
    """
    try:
        # 使用ctypes调用Windows API检查管理员权限
        # shell32.IsUserAnAdmin()返回非零值表示具有管理员权限
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        # 权限检查失败时，假设没有管理员权限，确保安全
        return False


def run_as_admin(script_path: str = None) -> bool:
    """
    以管理员权限重新启动当前应用程序
    
    使用Windows ShellExecute API以管理员权限重新启动程序。
    这会触发UAC对话框，要求用户确认权限提升。
    
    Args:
        script_path (str, optional): 要以管理员权限运行的脚本路径
                                   如果为None，则使用当前脚本路径
    
    Returns:
        bool: True表示成功启动管理员进程，False表示启动失败或用户拒绝
        
    Note:
        成功启动管理员进程后，当前进程应该退出
    """
    try:
        # 确定要重新启动的脚本路径
        if script_path is None:
            script_path = sys.argv[0]
        
        # 获取Python解释器路径
        python_exe = sys.executable
        
        # 构建命令行参数
        # 保持原有的命令行参数，确保程序行为一致
        params = ' '.join([f'"{script_path}"'] + sys.argv[1:])
        
        # 使用ShellExecute API以管理员权限启动进程
        # "runas"动词会触发UAC权限提升对话框
        result = ctypes.windll.shell32.ShellExecuteW(
            None,                    # hwnd: 父窗口句柄
            "runas",                # lpOperation: 操作类型（runas表示以管理员身份运行）
            python_exe,             # lpFile: 要执行的程序
            params,                 # lpParameters: 命令行参数
            None,                   # lpDirectory: 工作目录
            1                       # nShowCmd: 显示方式（1=SW_SHOWNORMAL）
        )
        
        # ShellExecute返回值大于32表示成功
        return result > 32
        
    except Exception as e:
        print(f"以管理员权限启动失败: {e}")
        return False


def ensure_admin_privileges() -> bool:
    """
    确保应用程序具有管理员权限的核心控制方法
    
    这个方法是FlowDesk权限管理的入口点，负责检查当前权限状态，
    并在需要时引导用户进行权限提升。采用用户友好的交互设计，
    确保权限申请过程的透明性。
    
    工作流程：
    1. 检查当前是否已具有管理员权限
    2. 如果没有权限，显示友好提示信息
    3. 尝试以管理员权限重新启动应用程序
    4. 退出当前进程，等待管理员进程启动
    
    Returns:
        bool: True表示已具有管理员权限，False表示权限获取失败
        
    Note:
        如果成功启动管理员进程，此方法不会返回（进程会退出）
    """
    # 首先检查当前是否已经具有管理员权限
    if is_admin():
        print("✅ 已具有管理员权限，可以执行网络配置操作")
        return True
    
    print("⚠️  FlowDesk需要管理员权限来修改网络配置")
    print("📋 将要执行的操作：")
    print("   • 修改网卡IP地址配置")
    print("   • 设置DNS服务器")
    print("   • 配置网关信息")
    print()
    print("🔒 正在申请管理员权限...")
    print("   请在UAC对话框中点击\"是\"以继续")
    
    # 尝试以管理员权限重新启动应用程序
    if run_as_admin():
        print("✅ 管理员权限申请成功，正在重新启动...")
        # 成功启动管理员进程后，当前进程应该退出
        # 这避免了同时运行两个实例的问题
        sys.exit(0)
    else:
        print("❌ 管理员权限申请失败或被用户拒绝")
        print("💡 提示：")
        print("   • 请确保以管理员身份运行此程序")
        print("   • 或者在UAC对话框中点击\"是\"")
        print("   • 没有管理员权限将无法修改网络配置")
        return False


def check_network_admin_capability() -> bool:
    """
    检查网络管理能力的专用验证方法
    
    通过尝试执行一个安全的netsh命令来验证是否具有网络配置权限。
    这比简单的管理员权限检查更准确，因为某些企业环境可能有特殊的权限策略。
    
    Returns:
        bool: True表示具有网络配置权限，False表示权限不足
    """
    try:
        # 执行一个安全的netsh查询命令来测试权限
        # 这个命令不会修改任何配置，只是查询接口列表
        result = subprocess.run(
            ['netsh', 'interface', 'ipv4', 'show', 'interfaces'],
            capture_output=True,
            text=True,
            timeout=10,
            encoding='gbk',
            errors='replace'
        )
        
        # 如果命令成功执行，说明具有基本的网络查询权限
        # 通常具有查询权限的用户也具有配置权限（在管理员模式下）
        return result.returncode == 0
        
    except Exception:
        # 命令执行失败，可能是权限不足或系统问题
        return False


def get_elevation_status_message() -> str:
    """
    获取当前权限状态的用户友好描述信息
    
    Returns:
        str: 权限状态描述文本
    """
    if is_admin():
        if check_network_admin_capability():
            return "✅ 管理员权限 - 可以修改网络配置"
        else:
            return "⚠️  管理员权限 - 网络配置功能受限"
    else:
        return "❌ 普通用户权限 - 需要管理员权限才能修改网络配置"


if __name__ == "__main__":
    """
    权限工具的独立测试入口
    
    可以直接运行此模块来测试权限检查和申请功能
    """
    print("FlowDesk 权限管理工具测试")
    print("=" * 40)
    
    print(f"当前权限状态: {get_elevation_status_message()}")
    print(f"管理员权限: {'是' if is_admin() else '否'}")
    print(f"网络配置能力: {'是' if check_network_admin_capability() else '否'}")
    
    if not is_admin():
        print("\n测试权限申请功能...")
        ensure_admin_privileges()
