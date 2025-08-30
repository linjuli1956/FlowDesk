# -*- coding: utf-8 -*-
"""
网卡性能监控专用服务模块。这个文件在FlowDesk网络管理架构中扮演"性能检测器"角色，专门负责获取网络适配器的性能指标信息。
它解决了网卡链路速度获取复杂、多网卡类型支持和性能数据格式化的问题，通过多重查询策略（wmic nic命令、netsh wlan命令）确保不同类型网卡的性能信息获取准确性。
UI层依赖此服务提供的性能数据来显示网卡速度和连接质量，其他服务通过此模块获得网卡硬件能力判断。该服务严格遵循单一职责原则，将性能监控逻辑完全独立封装。
"""
import subprocess
import re
from typing import Dict, Any, Optional

from .network_service_base import NetworkServiceBase


class AdapterPerformanceService(NetworkServiceBase):
    """
    网络适配器性能监控服务
    
    专门负责网络适配器性能指标获取的核心服务。
    此服务封装了复杂的性能数据获取逻辑，支持多种网卡类型。
    
    主要功能：
    - 通过wmic nic命令获取网卡链路速度信息
    - 专门处理无线网卡的netsh wlan速度查询
    - 实现网卡描述与友好名称的映射查询
    - 提供性能数据的标准化格式输出
    
    输入输出：
    - 输入：网卡友好名称或适配器基本信息
    - 输出：格式化的性能指标数据（链路速度、信号强度等）
    
    可能异常：
    - subprocess.CalledProcessError：性能查询命令执行失败
    - Exception：性能数据解析错误或系统调用异常
    """
    
    def __init__(self, parent=None):
        """
        初始化网络适配器性能监控服务
        
        Args:
            parent: PyQt父对象，用于内存管理
        """
        super().__init__(parent)
        self._log_operation_start("AdapterPerformanceService初始化")
    
    # region 核心性能监控方法
    
    def get_link_speed_info(self, adapter_name: str) -> str:
        """
        获取网卡链路速度信息的主入口方法
        
        这是性能监控服务的核心方法，实现了多重策略的链路速度获取机制。
        使用wmic nic命令直接通过网卡描述匹配获取速度，这种方法对所有网卡类型都有效。
        遵循面向对象架构的单一职责原则，专门负责链路速度的获取和格式化。
        
        技术实现：
        - 使用wmic nic where "NetEnabled=true"查询所有启用的网卡
        - 通过网卡描述精确匹配目标网卡
        - 将比特/秒转换为用户友好的Mbps/Gbps格式
        - 实现异常安全的查询机制，确保不影响主流程
        
        Args:
            adapter_name (str): 网卡连接名称，如"vEthernet (泰兴)"
            
        Returns:
            str: 格式化的链路速度字符串，如"1.0 Gbps"或"未知"
        """
        try:
            self._log_operation_start("获取链路速度", adapter_name=adapter_name)
            
            # 首先需要根据adapter_name找到对应的网卡描述
            # 因为wmic nic使用的是Description，而不是NetConnectionID
            adapter_description = self._get_adapter_description_by_name(adapter_name)
            if not adapter_description:
                self.logger.debug(f"无法获取网卡 {adapter_name} 的描述，尝试备用方法")
                # 如果无法获取描述，直接尝试netsh备用方法
                if adapter_name.upper() == 'WLAN' or '无线' in adapter_name:
                    wlan_speed = self._get_wireless_link_speed(adapter_name)
                    if wlan_speed:
                        self._log_operation_success("获取链路速度", f"无线速度: {wlan_speed}")
                        return wlan_speed
                return '未知'
            
            # 使用wmic nic命令查询所有启用网卡的Name和Speed
            result = subprocess.run(
                ['wmic', 'nic', 'where', 'NetEnabled=true', 'get', 'Name,Speed', '/format:csv'],
                capture_output=True, text=True, timeout=10, encoding='cp936', errors='replace'
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                lines = [line for line in output.split('\n') if line.strip() and not line.startswith('Node,')]
                
                self.logger.debug(f"wmic nic输出行数: {len(lines)}")
                self.logger.debug(f"目标网卡描述: '{adapter_description}'")
                
                for i, line in enumerate(lines):
                    parts = line.split(',')
                    self.logger.debug(f"第{i+1}行解析: parts数量={len(parts)}")
                    
                    if len(parts) >= 3:  # Node,Name,Speed
                        name = parts[1].strip()
                        speed_str = parts[2].strip()
                        
                        self.logger.debug(f"网卡名称: '{name}', 速度: '{speed_str}'")
                        
                        # 多重匹配策略：描述匹配 或 关键字匹配
                        is_match = False
                        if adapter_description:
                            # 策略1：完整描述匹配
                            if adapter_description.lower() == name.lower():
                                is_match = True
                                self.logger.debug(f"完整描述匹配成功")
                            # 策略2：描述包含匹配
                            elif adapter_description.lower() in name.lower() or name.lower() in adapter_description.lower():
                                is_match = True  
                                self.logger.debug(f"描述包含匹配成功")
                        
                        # 策略3：针对WLAN的关键字匹配（备用策略）
                        if not is_match and adapter_name.upper() == 'WLAN':
                            if 'wireless' in name.lower() or '802.11' in name.lower() or 'wlan' in name.lower():
                                is_match = True
                                self.logger.debug(f"WLAN关键字匹配成功")
                        
                        if is_match:
                            self.logger.debug(f"网卡匹配成功! 名称: {name}")
                            if speed_str and speed_str.isdigit():
                                # 将比特/秒转换为用户友好的格式
                                speed_bps = int(speed_str)
                                formatted_speed = self._format_speed(speed_bps)
                                
                                self._log_operation_success("获取链路速度", f"wmic解析: {formatted_speed}")
                                return formatted_speed
                            else:
                                self.logger.debug(f"匹配的网卡速度为空或无效: '{speed_str}'")
                
                self.logger.debug("wmic nic方法未找到匹配的网卡或速度信息")
            else:
                self.logger.debug(f"wmic nic命令执行失败: return code {result.returncode}")
            
            # 如果wmic nic失败，尝试使用netsh wlan作为备用方法
            if adapter_name.upper() == 'WLAN' or '无线' in adapter_name:
                self.logger.debug(f"wmic nic未获取到速度，尝试netsh wlan方法作为备用")
                wlan_speed = self._get_wireless_link_speed(adapter_name)
                if wlan_speed:
                    self._log_operation_success("获取链路速度", f"netsh备用: {wlan_speed}")
                    return wlan_speed
                
            # 如果无法获取具体速度，设置为未知
            self._log_operation_success("获取链路速度", "未知")
            return '未知'
                
        except Exception as e:
            self._log_operation_error("获取链路速度", e)
            return '未知'
    
    def get_adapter_description_by_name(self, adapter_name: str) -> Optional[str]:
        """
        通过网卡连接名称获取对应的硬件描述信息的公开方法
        
        Args:
            adapter_name: 网卡友好名称
            
        Returns:
            Optional[str]: 网卡硬件描述，未找到返回None
        """
        return self._get_adapter_description_by_name(adapter_name)
    
    def get_wireless_link_speed(self, adapter_name: str) -> Optional[str]:
        """
        获取无线网卡链路速度的公开方法
        
        Args:
            adapter_name: 无线网卡名称
            
        Returns:
            Optional[str]: 无线链路速度，失败返回None
        """
        return self._get_wireless_link_speed(adapter_name)
    
    # endregion
    
    # region 私有实现方法
    
    def _get_adapter_description_by_name(self, adapter_name: str) -> Optional[str]:
        """
        通过网卡连接名称获取对应的硬件描述信息
        
        这个方法是链路速度获取架构的关键组件，负责建立友好名称与硬件描述之间的映射关系。
        采用Windows Management Instrumentation Commands (wmic) 查询Win32_NetworkAdapter类，
        实现从用户可见的连接名称到系统内部硬件描述的精确转换。
        
        架构设计原则：
        - 单一职责原则：专门负责名称-描述映射转换
        - 封装性原则：封装wmic命令执行和CSV格式解析逻辑
        - 异常安全性：提供完整的错误处理和超时保护机制
        - 开闭原则：支持未来扩展其他网卡信息查询方式
        
        技术实现：
        - 使用wmic path win32_networkadapter查询网卡对象
        - 通过NetConnectionID字段精确匹配连接名称
        - 解析CSV格式输出获取Description字段值
        - 实现编码兼容性处理，支持中文系统环境
        
        Args:
            adapter_name (str): 网卡连接的友好名称，如"WLAN"、"以太网"等系统显示名称
            
        Returns:
            Optional[str]: 网卡的硬件描述字符串，如"Realtek 8188GU Wireless LAN 802.11n USB NIC"，
                          查询失败时返回None
        """
        try:
            self._log_operation_start("查询网卡描述", adapter_name=adapter_name)
            
            # 构建wmic查询命令，使用NetConnectionID字段进行精确匹配
            # 这里使用win32_networkadapter类来查询物理和虚拟网络适配器的完整信息
            # 
            # 关键修复：使用shell=True和正确的引号转义来解决编码兼容性问题
            # 在Windows环境下，subprocess对复杂引号处理存在编码差异，需要特殊处理
            command_str = f'wmic path win32_networkadapter where "NetConnectionID=\'{adapter_name}\'" get Description /format:csv'
            
            self.logger.debug(f"执行wmic查询命令: {command_str}")
            
            result = subprocess.run(
                command_str,
                shell=True,  # 使用shell=True来正确处理引号和编码
                capture_output=True, text=True, timeout=8, encoding='gbk', errors='replace'  # 改用gbk编码
            )
            
            self.logger.debug(f"wmic查询返回码: {result.returncode}")
            
            if result.returncode == 0:
                output = result.stdout.strip()
                # 过滤掉空行和CSV头部，只保留数据行
                lines = [line for line in output.split('\n') if line.strip() and not line.startswith('Node,')]
                
                self.logger.debug(f"解析到 {len(lines)} 行有效数据")
                
                if lines:
                    for i, line in enumerate(lines):
                        self.logger.debug(f"处理第 {i+1} 行数据")
                        parts = line.split(',')
                        if len(parts) >= 2:
                            description = parts[1].strip()
                            if description:
                                self._log_operation_success("查询网卡描述", f"找到描述: {description}")
                                return description
                            else:
                                self.logger.debug(f"第 {i+1} 行描述字段为空")
                        else:
                            self.logger.debug(f"第 {i+1} 行数据格式不正确，字段数: {len(parts)}")
                else:
                    self.logger.warning(f"wmic查询 {adapter_name} 返回空数据")
            else:
                self.logger.warning(f"wmic查询 {adapter_name} 失败，返回码: {result.returncode}")
                if result.stderr:
                    self.logger.warning(f"wmic查询错误信息: {result.stderr}")
            
            return None
            
        except Exception as e:
            self._log_operation_error("查询网卡描述", e)
            return None
    
    def _get_wireless_link_speed(self, adapter_name: str) -> Optional[str]:
        """
        获取无线网卡链路速度的专用方法
        
        使用netsh wlan show interface命令获取无线网卡的连接速度信息，
        这是针对无线网卡Speed属性经常为空的专门解决方案。
        
        技术实现：
        - 执行netsh wlan show interface命令获取无线接口信息
        - 使用多种正则表达式模式匹配不同格式的速率信息
        - 支持中英文Windows系统的速率字段解析
        - 提供统一的Mbps格式输出
        
        Args:
            adapter_name (str): 无线网卡连接名称，如"WLAN"
            
        Returns:
            Optional[str]: 格式化的链路速度字符串，如"72.2 Mbps"，失败时返回None
        """
        try:
            self._log_operation_start("获取无线链路速度", adapter_name=adapter_name)
            
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'interface'],
                capture_output=True, text=True, timeout=8, encoding='cp936', errors='replace'
            )
            
            if result.returncode == 0:
                output = result.stdout
                self.logger.debug(f"netsh wlan命令执行成功，输出长度: {len(output)} 字符")
                
                # 解析接收速率，支持多种格式
                # 格式1: "接收速率(Mbps)     : 72.2"  
                # 格式2: "接收速率          : 72.2 Mbps"
                # 格式3: "接收速率          : 72.2"
                # 格式4: 英文版本
                speed_patterns = [
                    r'接收速率\(Mbps\)\s*[:：]\s*([\d.]+)',
                    r'接收速率\s*[:：]\s*([\d.]+)\s*\(?Mbps\)?',
                    r'接收速率\s*[:：]\s*([\d.]+)',
                    r'Receive\s+rate\s*\(Mbps\)\s*[:：]\s*([\d.]+)',
                    r'Receive\s+rate\s*[:：]\s*([\d.]+)\s*\(?Mbps\)?'
                ]
                
                for i, pattern in enumerate(speed_patterns, 1):
                    match = re.search(pattern, output, re.IGNORECASE)
                    if match:
                        speed_value = match.group(1)
                        speed_formatted = f"{speed_value} Mbps"
                        self._log_operation_success("获取无线链路速度", f"解析成功: {speed_formatted}")
                        return speed_formatted
                
                self.logger.debug("netsh wlan所有模式都未匹配到速率信息")
                
            else:
                self.logger.debug(f"netsh wlan命令执行失败: return code {result.returncode}")
                
        except subprocess.TimeoutExpired:
            self.logger.debug(f"netsh wlan查询超时")
        except Exception as e:
            self._log_operation_error("获取无线链路速度", e)
            
        return None
    
    def _format_speed(self, speed_bps: int) -> str:
        """
        将比特/秒速度值格式化为用户友好的显示格式
        
        这个工具方法实现了网络速度的标准化格式转换，遵循用户体验设计原则。
        根据速度数值自动选择合适的单位（bps/Mbps/Gbps），提供清晰易读的显示效果。
        
        Args:
            speed_bps (int): 以比特/秒为单位的网络速度值
            
        Returns:
            str: 格式化后的速度字符串，如"1.0 Gbps"、"100.0 Mbps"
        """
        if speed_bps >= 1000000000:  # >= 1 Gbps
            speed_formatted = f"{speed_bps / 1000000000:.1f} Gbps"
        elif speed_bps >= 1000000:  # >= 1 Mbps
            speed_formatted = f"{speed_bps / 1000000:.1f} Mbps"
        else:
            speed_formatted = f"{speed_bps} bps"
        
        return speed_formatted
    
    def _clean_command_output_for_logging(self, output: str, max_length: int = 200) -> str:
        """
        清理命令输出用于安全的日志记录
        
        这个工具方法用于处理可能包含乱码或敏感信息的命令输出，
        确保日志记录的安全性和可读性。
        
        Args:
            output (str): 原始命令输出
            max_length (int): 最大输出长度，默认200字符
            
        Returns:
            str: 清理后的输出文本，适合日志记录
        """
        if not output:
            return "空输出"
        
        # 替换换行符为可见字符
        cleaned = output.replace('\n', '\\n').replace('\r', '\\r')
        
        # 截断过长的输出
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length] + "..."
        
        return cleaned
    
    # endregion
