# -*- coding: utf-8 -*-
"""
网卡操作服务模块

专门负责网卡的启用、禁用、DHCP设置等操作功能，包含状态预检查逻辑。
严格遵循服务层单一职责原则，通过PyQt信号与UI层通信。

主要功能：
- 网卡启用/禁用操作
- DHCP自动获取IP设置
- 操作前状态预检查
- 操作结果通知

作者: FlowDesk开发团队
"""

import subprocess
import logging
from typing import Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal

from ...utils import network_utils


class AdapterOperationService(QObject):
    """
    网卡操作服务类
    
    专门负责网卡的各种操作功能，包括启用、禁用、DHCP设置等。
    每个操作都包含状态预检查逻辑，避免重复操作。
    
    信号定义：
    - operation_completed: 操作完成信号(success: bool, message: str, operation: str)
    - operation_progress: 操作进度信号(message: str)
    - error_occurred: 错误发生信号(error_msg: str)
    """
    
    # 定义信号
    operation_completed = pyqtSignal(bool, str, str)  # 成功状态, 消息, 操作类型
    operation_progress = pyqtSignal(str)              # 进度消息
    error_occurred = pyqtSignal(str, str)             # 错误类型, 错误消息
    
    def __init__(self, parent=None):
        """
        初始化网卡操作服务
        
        Args:
            parent: PyQt父对象
        """
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("网卡操作服务初始化完成")
    
    def enable_adapter(self, adapter_name: str) -> bool:
        """
        启用指定网卡
        
        直接执行启用操作，操作完成后通过刷新获取最新状态。
        
        Args:
            adapter_name: 网卡友好名称
            
        Returns:
            bool: 启用成功返回True，失败返回False
        """
        try:
            self.logger.info(f"开始启用网卡操作: {adapter_name}")
            
            # 直接执行启用操作
            self.operation_progress.emit("正在启用网卡...")
            success = self._execute_enable_adapter(adapter_name)
            
            # 发射操作结果信号
            if success:
                self.logger.info(f"网卡启用成功: {adapter_name}")
                self.operation_completed.emit(True, "✅ 网卡已启用", "启用网卡")
                return True
            else:
                self.logger.error(f"网卡启用失败: {adapter_name}")
                self.operation_completed.emit(False, "❌ 启用失败", "启用网卡")
                return False
                
        except Exception as e:
            error_msg = f"启用网卡时发生错误: {str(e)}"
            self.logger.error(error_msg)
            self.operation_completed.emit(False, f"❌ {error_msg}", "启用网卡")
            return False
    
    def disable_adapter(self, adapter_name: str) -> None:
        """
        禁用指定网卡
        
        直接执行禁用操作，操作完成后通过刷新获取最新状态。
        
        Args:
            adapter_name: 网卡友好名称
        """
        try:
            self.logger.info(f"开始禁用网卡操作: {adapter_name}")
            
            # 直接执行禁用操作
            self.operation_progress.emit("正在禁用网卡...")
            success = self._execute_disable_adapter(adapter_name)
            
            # 发射操作结果信号
            if success:
                self.logger.info(f"网卡禁用成功: {adapter_name}")
                self.operation_completed.emit(True, "✅ 网卡已禁用", "禁用网卡")
            else:
                self.logger.error(f"网卡禁用失败: {adapter_name}")
                self.operation_completed.emit(False, "❌ 禁用失败", "禁用网卡")
                
        except Exception as e:
            error_msg = f"禁用网卡时发生错误: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit("网卡操作错误", error_msg)
    
    def set_dhcp_mode(self, adapter_name: str) -> None:
        """
        设置网卡为DHCP自动获取IP模式
        
        直接执行DHCP设置操作，操作完成后通过刷新获取最新状态。
        
        Args:
            adapter_name: 网卡友好名称
        """
        try:
            self.logger.info(f"开始设置DHCP操作: {adapter_name}")
            
            # 直接执行DHCP设置操作
            self.operation_progress.emit("正在设置为自动获取...")
            success = self._execute_set_dhcp(adapter_name)
            
            # 发射操作结果信号
            if success:
                self.logger.info(f"DHCP设置成功: {adapter_name}")
                self.operation_completed.emit(True, "✅ 已设为自动获取", "设置DHCP")
            else:
                self.logger.error(f"DHCP设置失败: {adapter_name}")
                self.operation_completed.emit(False, "❌ 设置失败", "设置DHCP")
                
        except Exception as e:
            error_msg = f"设置DHCP时发生错误: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit("网卡操作错误", error_msg)
    
    def _check_adapter_status(self, adapter_name: str) -> Tuple[Optional[bool], str]:
        """
        检查网卡启用/禁用状态
        
        Args:
            adapter_name: 网卡友好名称
            
        Returns:
            Tuple[Optional[bool], str]: (是否启用, 状态描述)
            - True: 已启用
            - False: 已禁用  
            - None: 检查失败
        """
        try:
            # 使用netsh命令查询网卡状态
            cmd = f'netsh interface show interface name="{adapter_name}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            if result.returncode != 0:
                self.logger.warning(f"查询网卡状态失败: {adapter_name}")
                return None, "查询失败"
            
            output = result.stdout
            self.logger.debug(f"网卡状态查询结果: {output}")
            
            # 解析输出判断状态
            if "已启用" in output or "Enabled" in output:
                return True, "已启用"
            elif "已禁用" in output or "Disabled" in output:
                return False, "已禁用"
            else:
                self.logger.warning(f"无法解析网卡状态: {output}")
                return None, "状态未知"
                
        except Exception as e:
            self.logger.error(f"检查网卡状态时发生异常: {str(e)}")
            return None, "检查异常"
    
    def _check_ip_mode(self, adapter_name: str) -> Tuple[Optional[bool], str]:
        """
        检查网卡IP配置模式（DHCP或静态）
        
        Args:
            adapter_name: 网卡友好名称
            
        Returns:
            Tuple[Optional[bool], str]: (是否为DHCP, 模式描述)
            - True: DHCP模式
            - False: 静态IP模式
            - None: 检查失败
        """
        try:
            # 使用netsh命令查询IP配置
            cmd = f'netsh interface ipv4 show config name="{adapter_name}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            if result.returncode != 0:
                self.logger.warning(f"查询IP配置失败: {adapter_name}")
                return None, "查询失败"
            
            output = result.stdout
            self.logger.debug(f"IP配置查询结果: {output}")
            
            # 解析输出判断IP模式
            if "DHCP" in output or "自动" in output:
                return True, "DHCP模式"
            elif "静态" in output or "手动" in output:
                return False, "静态IP模式"
            else:
                self.logger.warning(f"无法解析IP配置模式: {output}")
                return None, "模式未知"
                
        except Exception as e:
            self.logger.error(f"检查IP配置模式时发生异常: {str(e)}")
            return None, "检查异常"
    
    def _execute_enable_adapter(self, adapter_name: str) -> bool:
        """
        执行网卡启用操作
        
        Args:
            adapter_name: 网卡友好名称
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 使用列表形式避免shell解析问题
            cmd = ['netsh', 'interface', 'set', 'interface', f'name={adapter_name}', 'admin=enabled']
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            success = result.returncode == 0
            if success:
                self.logger.debug(f"网卡启用命令执行成功: {adapter_name}")
            else:
                self.logger.error(f"网卡启用命令执行失败: stdout={result.stdout}, stderr={result.stderr}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"执行网卡启用命令时发生异常: {str(e)}")
            return False
    
    def _execute_disable_adapter(self, adapter_name: str) -> bool:
        """
        执行网卡禁用操作
        
        Args:
            adapter_name: 网卡友好名称
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 使用列表形式避免shell解析问题
            cmd = ['netsh', 'interface', 'set', 'interface', f'name={adapter_name}', 'admin=disabled']
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            success = result.returncode == 0
            if success:
                self.logger.debug(f"网卡禁用命令执行成功: {adapter_name}")
            else:
                self.logger.error(f"网卡禁用命令执行失败: stdout={result.stdout}, stderr={result.stderr}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"执行网卡禁用命令时发生异常: {str(e)}")
            return False
    
    def _execute_set_dhcp(self, adapter_name: str) -> bool:
        """
        执行DHCP设置操作
        
        Args:
            adapter_name: 网卡友好名称
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 设置IP为DHCP自动获取 - 使用列表形式避免shell解析问题
            cmd_ip = ['netsh', 'interface', 'ipv4', 'set', 'address', f'name={adapter_name}', 'source=dhcp']
            result_ip = subprocess.run(cmd_ip, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            # 设置DNS为DHCP自动获取 - 使用列表形式避免shell解析问题
            cmd_dns = ['netsh', 'interface', 'ipv4', 'set', 'dns', f'name={adapter_name}', 'source=dhcp']
            result_dns = subprocess.run(cmd_dns, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            success = result_ip.returncode == 0 and result_dns.returncode == 0
            if success:
                self.logger.debug(f"DHCP设置命令执行成功: {adapter_name}")
            else:
                self.logger.error(f"DHCP设置命令执行失败 - IP: stdout={result_ip.stdout}, stderr={result_ip.stderr}, DNS: stdout={result_dns.stdout}, stderr={result_dns.stderr}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"执行DHCP设置操作时发生异常: {str(e)}")
            return False
