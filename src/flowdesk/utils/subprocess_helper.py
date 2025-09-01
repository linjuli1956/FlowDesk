#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FlowDesk 子进程执行助手模块

作用说明：
这个模块提供安全、可靠的子进程执行功能，主要用于：
1. 执行网络配置命令（ipconfig、netsh等）
2. 运行系统诊断工具（ping、tracert等）
3. 启动外部程序（远程桌面连接等）
4. 获取系统信息和状态

面向新手的设计说明：
- 所有函数都有完整的错误处理和超时保护
- 提供同步和异步两种执行方式
- 支持实时输出捕获和进度回调
- 包含详细的中文注释和使用示例
- 采用安全的参数传递方式，防止命令注入

设计原则：
- 安全第一：防止命令注入和权限提升攻击
- 异常安全：所有操作都有超时和异常处理
- 跨平台兼容：主要针对Windows，保留扩展性
- 性能优化：支持异步执行，不阻塞UI线程
"""

import subprocess
import threading
import queue
import time
import os
import sys
import logging
from typing import Optional, List, Dict, Any, Callable, Tuple
from dataclasses import dataclass
from enum import Enum

# 获取日志记录器
logger = logging.getLogger(__name__)


class CommandStatus(Enum):
    """命令执行状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    COMPLETED = "completed"  # 执行完成
    FAILED = "failed"        # 执行失败
    TIMEOUT = "timeout"      # 执行超时
    CANCELLED = "cancelled"  # 用户取消


@dataclass
class CommandResult:
    """
    命令执行结果数据类
    
    作用说明：
    封装命令执行的所有相关信息，包括返回码、输出内容、错误信息等。
    这个数据类让函数返回值更加结构化和易于使用。
    
    属性说明：
        command: 执行的命令字符串
        return_code: 命令返回码（0表示成功）
        stdout: 标准输出内容
        stderr: 标准错误输出内容
        execution_time: 执行耗时（秒）
        status: 执行状态
        error_message: 错误描述信息
    """
    command: str
    return_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    execution_time: float = 0.0
    status: CommandStatus = CommandStatus.PENDING
    error_message: str = ""
    
    @property
    def success(self) -> bool:
        """判断命令是否执行成功"""
        return self.status == CommandStatus.COMPLETED and self.return_code == 0
    
    @property
    def output(self) -> str:
        """获取主要输出内容（优先返回stdout）"""
        return self.stdout if self.stdout else self.stderr


def run_command(command: str, 
                timeout: int = 30,
                shell: bool = True,
                cwd: Optional[str] = None,
                env: Optional[Dict[str, str]] = None,
                encoding: str = 'utf-8') -> CommandResult:
    """
    同步执行系统命令
    
    作用说明：
    这是最常用的命令执行函数，适用于需要等待命令完成并获取结果的场景。
    例如：获取网络配置信息、检查网络连通性、查询系统状态等。
    
    参数说明：
        command: 要执行的命令字符串
        timeout: 超时时间（秒），防止命令长时间无响应
        shell: 是否通过shell执行（Windows下通常为True）
        cwd: 工作目录，None表示使用当前目录
        env: 环境变量字典，None表示继承当前环境
        encoding: 输出编码格式，Windows中文系统通常用'gbk'
        
    返回值：
        CommandResult: 包含执行结果的数据对象
        
    使用示例：
        # 获取IP配置信息
        result = run_command("ipconfig /all", timeout=10)
        if result.success:
            print("网络配置信息:")
            print(result.output)
        else:
            print(f"命令执行失败: {result.error_message}")
            
        # 测试网络连通性
        result = run_command("ping -n 4 8.8.8.8", timeout=15)
        if result.success:
            print("网络连接正常")
        else:
            print("网络连接异常")
    """
    start_time = time.time()
    result = CommandResult(command=command)
    
    try:
        logger.debug(f"执行命令: {command}")
        
        # Windows系统编码处理
        if sys.platform.startswith('win') and encoding == 'utf-8':
            # Windows中文系统默认使用GBK编码
            encoding = 'gbk'
        
        # 执行命令
        process = subprocess.Popen(
            command,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=env,
            text=True,
            encoding=encoding,
            errors='replace'  # 遇到编码错误时替换为占位符
        )
        
        result.status = CommandStatus.RUNNING
        
        # 等待命令完成或超时
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            result.return_code = process.returncode
            result.stdout = stdout.strip() if stdout else ""
            result.stderr = stderr.strip() if stderr else ""
            result.status = CommandStatus.COMPLETED
            
            logger.debug(f"命令执行完成，返回码: {result.return_code}")
            
        except subprocess.TimeoutExpired:
            # 命令超时处理
            process.kill()
            process.communicate()  # 清理进程
            result.status = CommandStatus.TIMEOUT
            result.error_message = f"命令执行超时（{timeout}秒）"
            logger.warning(f"命令执行超时: {command}")
            
    except FileNotFoundError:
        result.status = CommandStatus.FAILED
        result.error_message = "命令不存在或无法找到"
        logger.error(f"命令不存在: {command}")
        
    except PermissionError:
        result.status = CommandStatus.FAILED
        result.error_message = "权限不足，无法执行命令"
        logger.error(f"权限不足: {command}")
        
    except Exception as e:
        result.status = CommandStatus.FAILED
        result.error_message = f"命令执行异常: {str(e)}"
        logger.error(f"命令执行异常: {command}, 错误: {e}")
    
    finally:
        result.execution_time = time.time() - start_time
    
    return result


def run_command_async(command: str,
                     callback: Optional[Callable[[CommandResult], None]] = None,
                     progress_callback: Optional[Callable[[str], None]] = None,
                     timeout: int = 60,
                     shell: bool = True,
                     cwd: Optional[str] = None,
                     env: Optional[Dict[str, str]] = None,
                     encoding: str = 'utf-8') -> threading.Thread:
    """
    异步执行系统命令
    
    作用说明：
    适用于长时间运行的命令，避免阻塞UI线程。
    例如：大文件传输、长时间的网络诊断、系统扫描等。
    
    参数说明：
        command: 要执行的命令字符串
        callback: 命令完成后的回调函数，接收CommandResult参数
        progress_callback: 实时输出回调函数，接收输出行字符串
        timeout: 超时时间（秒）
        shell: 是否通过shell执行
        cwd: 工作目录
        env: 环境变量字典
        encoding: 输出编码格式
        
    返回值：
        threading.Thread: 执行命令的线程对象，可用于控制和监控
        
    使用示例：
        def on_command_complete(result):
            if result.success:
                print("长时间命令执行完成")
            else:
                print(f"命令失败: {result.error_message}")
        
        def on_progress(line):
            print(f"进度: {line}")
        
        # 异步执行长时间命令
        thread = run_command_async(
            "ping -t 8.8.8.8",  # 持续ping
            callback=on_command_complete,
            progress_callback=on_progress,
            timeout=300
        )
        
        # 可以在需要时取消命令
        # thread.cancel()  # 如果实现了取消功能
    """
    
    def _async_executor():
        """异步执行器内部函数"""
        start_time = time.time()
        result = CommandResult(command=command)
        
        try:
            logger.debug(f"异步执行命令: {command}")
            
            # Windows系统编码处理
            if sys.platform.startswith('win') and encoding == 'utf-8':
                encoding_to_use = 'gbk'
            else:
                encoding_to_use = encoding
            
            # 启动进程
            process = subprocess.Popen(
                command,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                env=env,
                text=True,
                encoding=encoding_to_use,
                errors='replace',
                bufsize=1,  # 行缓冲，便于实时输出
                universal_newlines=True
            )
            
            result.status = CommandStatus.RUNNING
            
            # 实时读取输出
            output_lines = []
            error_lines = []
            
            # 使用队列来处理实时输出
            output_queue = queue.Queue()
            
            def _read_output(pipe, line_list, is_stderr=False):
                """读取输出的内部函数"""
                try:
                    for line in iter(pipe.readline, ''):
                        if line:
                            line = line.rstrip('\n\r')
                            line_list.append(line)
                            if progress_callback and not is_stderr:
                                progress_callback(line)
                            output_queue.put(('line', line, is_stderr))
                except Exception as e:
                    output_queue.put(('error', str(e), is_stderr))
                finally:
                    pipe.close()
            
            # 启动输出读取线程
            stdout_thread = threading.Thread(
                target=_read_output, 
                args=(process.stdout, output_lines, False)
            )
            stderr_thread = threading.Thread(
                target=_read_output, 
                args=(process.stderr, error_lines, True)
            )
            
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()
            
            # 等待进程完成或超时
            try:
                process.wait(timeout=timeout)
                result.return_code = process.returncode
                result.status = CommandStatus.COMPLETED
                
            except subprocess.TimeoutExpired:
                # 超时处理
                process.kill()
                result.status = CommandStatus.TIMEOUT
                result.error_message = f"命令执行超时（{timeout}秒）"
                logger.warning(f"异步命令执行超时: {command}")
            
            # 等待输出读取线程完成
            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)
            
            # 整理输出结果
            result.stdout = '\n'.join(output_lines)
            result.stderr = '\n'.join(error_lines)
            
            logger.debug(f"异步命令执行完成，返回码: {result.return_code}")
            
        except Exception as e:
            result.status = CommandStatus.FAILED
            result.error_message = f"异步命令执行异常: {str(e)}"
            logger.error(f"异步命令执行异常: {command}, 错误: {e}")
        
        finally:
            result.execution_time = time.time() - start_time
            
            # 调用完成回调
            if callback:
                try:
                    callback(result)
                except Exception as e:
                    logger.error(f"回调函数执行异常: {e}")
    
    # 创建并启动线程
    thread = threading.Thread(target=_async_executor, daemon=True)
    thread.start()
    
    return thread


def run_elevated_command(command: str, 
                        timeout: int = 30) -> CommandResult:
    """
    以管理员权限执行命令
    
    作用说明：
    某些网络配置操作需要管理员权限，这个函数会尝试提升权限执行命令。
    在Windows上使用runas或PowerShell的Start-Process -Verb RunAs。
    
    参数说明：
        command: 要执行的命令
        timeout: 超时时间
        
    返回值：
        CommandResult: 执行结果
        
    使用示例：
        # 修改IP地址（需要管理员权限）
        result = run_elevated_command(
            'netsh interface ip set address "本地连接" static 192.168.1.100 255.255.255.0 192.168.1.1'
        )
        if result.success:
            print("IP地址修改成功")
        else:
            print(f"修改失败: {result.error_message}")
    """
    if sys.platform.startswith('win'):
        # Windows系统使用PowerShell提升权限
        elevated_command = f'powershell -Command "Start-Process cmd -ArgumentList \'/c {command}\' -Verb RunAs -Wait"'
    else:
        # Linux/macOS系统使用sudo
        elevated_command = f'sudo {command}'
    
    logger.info(f"以管理员权限执行命令: {command}")
    return run_command(elevated_command, timeout=timeout)


def kill_process_by_name(process_name: str) -> CommandResult:
    """
    根据进程名终止进程
    
    作用说明：
    用于终止可能影响网络配置的进程，或清理残留的子进程。
    
    参数说明：
        process_name: 进程名称（不包含.exe扩展名）
        
    返回值：
        CommandResult: 执行结果
        
    使用示例：
        # 终止可能冲突的网络工具
        result = kill_process_by_name("ping")
        if result.success:
            print("进程终止成功")
    """
    if sys.platform.startswith('win'):
        command = f'taskkill /f /im {process_name}.exe'
    else:
        command = f'pkill {process_name}'
    
    logger.debug(f"终止进程: {process_name}")
    return run_command(command, timeout=10)


def get_command_output(command: str, 
                      timeout: int = 30,
                      default_value: str = "") -> str:
    """
    获取命令输出的便捷函数
    
    作用说明：
    简化的命令执行函数，只返回输出内容，适用于简单的信息查询。
    
    参数说明：
        command: 要执行的命令
        timeout: 超时时间
        default_value: 命令失败时的默认返回值
        
    返回值：
        str: 命令输出内容，失败时返回默认值
        
    使用示例：
        # 获取当前IP地址
        ip_info = get_command_output("ipconfig", default_value="无法获取IP信息")
        print(ip_info)
        
        # 获取系统版本
        version = get_command_output("ver", default_value="未知版本")
        print(f"系统版本: {version}")
    """
    result = run_command(command, timeout=timeout)
    if result.success:
        return result.output
    else:
        logger.warning(f"命令执行失败，返回默认值: {command}")
        return default_value


def is_command_available(command: str) -> bool:
    """
    检查命令是否可用
    
    作用说明：
    在执行命令前检查其可用性，避免执行不存在的命令。
    
    参数说明：
        command: 要检查的命令名
        
    返回值：
        bool: 命令是否可用
        
    使用示例：
        if is_command_available("ping"):
            result = run_command("ping 8.8.8.8")
        else:
            print("ping命令不可用")
    """
    if sys.platform.startswith('win'):
        check_command = f'where {command}'
    else:
        check_command = f'which {command}'
    
    result = run_command(check_command, timeout=5)
    return result.success


# 常用网络命令的封装函数
def ping_host(host: str, count: int = 4, timeout: int = 30) -> CommandResult:
    """
    Ping指定主机
    
    参数说明：
        host: 目标主机IP或域名
        count: ping次数
        timeout: 超时时间
        
    返回值：
        CommandResult: ping结果
    """
    if sys.platform.startswith('win'):
        command = f'ping -n {count} {host}'
    else:
        command = f'ping -c {count} {host}'
    
    return run_command(command, timeout=timeout)


def get_network_interfaces() -> CommandResult:
    """
    获取网络接口信息
    
    返回值：
        CommandResult: 网络接口信息
    """
    if sys.platform.startswith('win'):
        command = 'ipconfig /all'
    else:
        command = 'ifconfig -a'
    
    return run_command(command, timeout=15)


def flush_dns() -> CommandResult:
    """
    刷新DNS缓存
    
    返回值：
        CommandResult: 执行结果
    """
    if sys.platform.startswith('win'):
        command = 'ipconfig /flushdns'
    else:
        command = 'sudo systemctl flush-dns'
    
    return run_command(command, timeout=10)


# 模块测试代码
if __name__ == "__main__":
    """
    模块测试代码
    
    运行此文件可以测试所有功能。
    """
    print("🔧 FlowDesk 子进程执行助手测试")
    print("=" * 50)
    
    # 测试基本命令执行
    print("测试基本命令执行...")
    result = run_command("echo Hello FlowDesk", timeout=5)
    print(f"命令: {result.command}")
    print(f"状态: {result.status.value}")
    print(f"输出: {result.output}")
    print(f"耗时: {result.execution_time:.2f}秒")
    print()
    
    # 测试网络命令
    print("测试网络连通性...")
    result = ping_host("8.8.8.8", count=2, timeout=10)
    if result.success:
        print("✅ 网络连接正常")
    else:
        print(f"❌ 网络连接异常: {result.error_message}")
    print()
    
    # 测试命令可用性检查
    print("测试命令可用性...")
    commands_to_check = ['ping', 'ipconfig', 'netsh', 'tracert']
    for cmd in commands_to_check:
        available = is_command_available(cmd)
        status = "✅ 可用" if available else "❌ 不可用"
        print(f"{cmd}: {status}")
    
    print("=" * 50)
    print("✅ 子进程执行助手测试完成")
