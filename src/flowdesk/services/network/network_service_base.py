# -*- coding: utf-8 -*-
"""
FlowDesk网络服务基类模块

网络服务模块的公共基类和信号定义文件。这个文件在整个网络服务架构中扮演基础设施角色，
为所有网络相关服务提供统一的PyQt信号通信机制、日志记录器和异常处理框架。
它解决了服务间重复代码的问题，确保所有网络服务都有一致的错误处理和日志输出格式。
UI层通过连接这些标准化信号来接收网络状态变化通知，其他网络服务继承此基类获得统一的通信能力，
实现了面向对象的代码复用和规范化设计。
"""

import logging
import subprocess
from typing import List, Optional, Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal


class NetworkServiceBase(QObject):
    """
    网络服务基类
    
    为所有网络相关服务提供统一的PyQt信号通信机制和基础功能。
    所有网络服务都应继承此基类以确保一致的通信接口和错误处理。
    
    主要功能：
    - 定义标准化的PyQt信号用于与UI层通信
    - 提供统一的日志记录器初始化
    - 封装通用的异常处理逻辑
    
    继承此类的服务可以：
    - 使用标准信号向UI层发送数据更新通知
    - 获得一致的日志输出格式
    - 复用通用的错误处理机制
    """
    
    # region 标准化PyQt信号定义
    # 这些信号为所有网络服务提供统一的UI通信接口
    
    # 网卡相关信号
    adapters_updated = pyqtSignal(list)          # 网卡列表更新信号，参数：List[AdapterInfo]
    adapter_selected = pyqtSignal(object)        # 网卡选择变更信号，参数：AdapterInfo
    adapter_refreshed = pyqtSignal(object)       # 单个网卡刷新完成信号，参数：AdapterInfo
    adapter_info_updated = pyqtSignal(object)    # 网卡详细信息更新信号，参数：AdapterInfo
    
    # IP配置相关信号
    ip_info_updated = pyqtSignal(object)         # IP配置信息更新信号，参数：IPConfigInfo
    ip_config_applied = pyqtSignal(object)       # IP配置应用成功信号，参数：AdapterInfo
    extra_ips_updated = pyqtSignal(list)         # 额外IP列表更新信号，参数：List[ExtraIP]
    extra_ips_added = pyqtSignal(str)            # 额外IP添加成功信号，参数：成功消息
    extra_ips_removed = pyqtSignal(str)          # 额外IP删除成功信号，参数：成功消息
    
    # UI交互相关信号
    network_info_copied = pyqtSignal(str)        # 网卡信息复制完成信号，参数：复制的文本内容
    status_badges_updated = pyqtSignal(str, str, str, str, str)  # 状态徽章更新信号，参数：连接显示文本, 连接属性, IP模式显示文本, IP模式属性, 链路速度显示文本
    operation_status = pyqtSignal(str, bool)     # 操作状态反馈信号，参数：操作描述, 成功标识
    operation_progress = pyqtSignal(str)         # 操作进度更新信号，参数：进度描述
    error_occurred = pyqtSignal(str, str)        # 错误发生信号，参数：错误类型, 错误描述
    
    # endregion
    
    def __init__(self, parent=None):
        """
        初始化网络服务基类
        
        Args:
            parent: 父对象，用于PyQt的内存管理
        """
        super().__init__(parent)
        
        # region 日志记录器初始化
        # 为每个继承的服务类创建专用的日志记录器，便于调试和监控
        self.logger = logging.getLogger(self.__class__.__module__)
        # endregion
        
        # region 服务状态管理
        # 用于跟踪服务的初始化状态和运行状态
        self._is_initialized = False
        self._service_name = self.__class__.__name__
        # endregion
    
    def _log_operation_start(self, operation_name: str, **kwargs) -> None:
        """
        记录操作开始的标准日志
        
        提供统一的操作日志格式，便于调试和监控。
        所有继承服务在执行重要操作前都应调用此方法。
        
        Args:
            operation_name: 操作名称描述
            **kwargs: 操作相关的参数信息
        """
        # 格式化参数信息用于日志记录
        params_str = ', '.join([f"{k}={v}" for k, v in kwargs.items()]) if kwargs else "无参数"
        self.logger.debug(f"[{self._service_name}] 开始执行操作: {operation_name} ({params_str})")
    
    def _log_operation_success(self, operation_name: str, result_summary: str = "") -> None:
        """
        记录操作成功的标准日志
        
        Args:
            operation_name: 操作名称描述
            result_summary: 操作结果的简要描述
        """
        summary_text = f" - {result_summary}" if result_summary else ""
        self.logger.debug(f"[{self._service_name}] 操作成功完成: {operation_name}{summary_text}")
    
    def _log_operation_error(self, operation_name: str, error: Exception) -> None:
        """
        记录操作失败的标准日志
        
        Args:
            operation_name: 操作名称描述
            error: 异常对象
        """
        self.logger.error(f"[{self._service_name}] 操作执行失败: {operation_name} - {str(error)}")
    
    def _handle_subprocess_error(self, cmd: List[str], result: subprocess.CompletedProcess) -> Dict[str, Any]:
        """
        处理subprocess命令执行错误的统一方法
        
        为所有网络服务提供一致的命令行工具调用错误处理逻辑。
        
        Args:
            cmd: 执行的命令列表
            result: subprocess.run()的返回结果
            
        Returns:
            Dict[str, Any]: 包含错误信息的字典，键包括：
                - success: False
                - error_code: 返回码
                - error_message: 错误描述
                - command: 执行的命令
        """
        cmd_str = ' '.join(cmd)  # 将命令列表转换为字符串用于记录
        error_output = result.stderr.strip() if result.stderr else "无错误输出"
        
        # 记录详细的命令执行失败信息
        self.logger.error(f"命令执行失败: {cmd_str}")
        self.logger.error(f"返回码: {result.returncode}")
        self.logger.error(f"错误输出: {error_output}")
        
        return {
            'success': False,
            'error_code': result.returncode,
            'error_message': error_output,
            'command': cmd_str
        }
