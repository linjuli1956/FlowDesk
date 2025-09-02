# -*- coding: utf-8 -*-
"""
网络IP配置专用服务模块

这个文件在FlowDesk网络管理架构中扮演"IP配置执行器"角色，专门负责将用户输入的IP配置信息应用到指定的网络适配器上。
它解决了Windows网络配置API调用复杂、多步骤操作协调和错误处理困难的问题，通过标准化的netsh命令封装确保IP和DNS配置的准确应用。
UI层依赖此服务实现网卡的静态IP配置功能，其他服务通过此模块执行网络参数的实际修改操作。
该服务严格遵循单一职责原则，将IP配置应用逻辑完全独立封装。
"""

import subprocess
from typing import Optional, Dict, Any, List

from .network_service_base import NetworkServiceBase


class IPConfigurationService(NetworkServiceBase):
    """
    网络IP配置应用服务
    
    专门负责网络适配器IP配置应用的核心服务。
    此服务封装了复杂的Windows网络配置逻辑，提供统一的IP和DNS配置接口。
    
    主要功能：
    - 通过netsh命令应用静态IP地址配置
    - 实现IP地址、子网掩码、网关的统一设置
    - 提供主DNS和辅助DNS的独立配置功能
    - 支持分步骤的网络配置操作和进度反馈
    
    输入输出：
    - 输入：网卡标识符和完整的IP配置参数
    - 输出：配置应用的成功状态和详细结果信息
    
    可能异常：
    - subprocess.CalledProcessError：网络配置命令执行失败
    - subprocess.TimeoutExpired：配置操作超时
    - Exception：参数验证错误或系统权限不足
    """
    
    def __init__(self, parent=None):
        """
        初始化网络IP配置应用服务
        
        Args:
            parent: PyQt父对象，用于内存管理
        """
        super().__init__(parent)
        self._log_operation_start("IPConfigurationService初始化")
    
    # region 核心IP配置方法
    
    def apply_ip_config(self, adapter_id: str, ip_address: str, subnet_mask: str, 
                       gateway: str = '', primary_dns: str = '', secondary_dns: str = '') -> bool:
        """
        应用完整的IP配置到指定网络适配器的主入口方法
        
        这是IP配置服务的核心方法，实现了完整的网络配置应用流程。
        采用分步骤执行策略，先配置IP地址和网关，再配置DNS服务器，确保配置的原子性。
        遵循面向对象架构的单一职责原则，专门负责IP配置的应用和验证。
        
        技术实现：
        - 使用网卡GUID查找对应的连接名称
        - 通过netsh interface ipv4命令执行静态IP配置
        - 实现IP配置和DNS配置的分离处理
        - 提供完整的进度反馈和错误处理机制
        
        Args:
            adapter_id (str): 目标网卡的GUID标识符
            ip_address (str): 要设置的IP地址
            subnet_mask (str): 子网掩码
            gateway (str, optional): 默认网关地址，可选
            primary_dns (str, optional): 主DNS服务器地址，可选
            secondary_dns (str, optional): 辅助DNS服务器地址，可选
            
        Returns:
            bool: 配置应用成功返回True，失败返回False
        """
        try:
            # 发射操作开始信号，通知UI层显示进度指示器
            self.operation_progress.emit("开始应用IP配置...")
            self._log_operation_start("应用IP配置", adapter_id=adapter_id, ip=ip_address)
            
            # 查找目标网卡的连接名称，netsh命令需要使用连接名而非GUID
            adapter_info = self._find_adapter_basic_info(adapter_id)
            if not adapter_info:
                error_msg = f"未找到网卡 {adapter_id}"
                self.logger.error(error_msg)
                self.error_occurred.emit("网卡查找失败", error_msg)
                return False
            
            # 获取网卡的友好连接名称，用于netsh命令
            connection_name = adapter_info.get('NetConnectionID', '')
            if not connection_name:
                error_msg = f"网卡 {adapter_id} 缺少连接名称"
                self.logger.error(error_msg)
                self.error_occurred.emit("网卡配置错误", error_msg)
                return False
            
            # 记录网卡信息用于调试
            self._log_operation_start("网卡配置准备", connection_name=connection_name)
            
            # 第一步：配置IP地址和子网掩码
            self.operation_progress.emit("正在配置IP地址...")
            ip_success = self._apply_ip_address(connection_name, ip_address, subnet_mask, gateway)
            
            if not ip_success:
                error_msg = "IP地址配置失败"
                self.logger.error(error_msg)
                self.error_occurred.emit("IP配置失败", error_msg)
                return False
            
            # 第二步：配置DNS服务器（如果提供了DNS地址）
            if primary_dns or secondary_dns:
                self.operation_progress.emit("正在配置DNS服务器...")
                dns_success = self._apply_dns_config(connection_name, primary_dns, secondary_dns)
                
                if not dns_success:
                    # DNS配置失败不影响整体操作，但需要记录警告
                    self.logger.warning("DNS配置失败，但IP配置已成功应用")
            
            # 第三步：发射成功信号，通知UI层配置已完成
            success_msg = f"网卡 {connection_name} 的IP配置已成功应用"
            self._log_operation_success("应用IP配置", success_msg)
            self.ip_config_applied.emit(success_msg)
            self.operation_progress.emit("IP配置应用完成")
            
            return True
            
        except Exception as e:
            # 捕获所有未预期的异常，确保方法的异常安全性
            self._log_operation_error("应用IP配置", e)
            error_msg = f"应用IP配置时发生异常: {str(e)}"
            self.error_occurred.emit("系统异常", error_msg)
            return False
    
    def apply_ip_address(self, connection_name: str, ip_address: str, subnet_mask: str, gateway: str = '') -> bool:
        """
        应用IP地址配置的公开方法
        
        Args:
            connection_name: 网络连接名称
            ip_address: IP地址
            subnet_mask: 子网掩码
            gateway: 网关地址，可选
            
        Returns:
            bool: 配置成功返回True，失败返回False
        """
        return self._apply_ip_address(connection_name, ip_address, subnet_mask, gateway)
    
    def apply_dns_config(self, connection_name: str, primary_dns: str, secondary_dns: str = '') -> bool:
        """
        应用DNS配置的公开方法
        
        Args:
            connection_name: 网络连接名称
            primary_dns: 主DNS服务器地址
            secondary_dns: 辅助DNS服务器地址，可选
            
        Returns:
            bool: DNS配置成功返回True，失败返回False
        """
        return self._apply_dns_config(connection_name, primary_dns, secondary_dns)
    
    # endregion
    
    # region 私有实现方法
    
    def _apply_ip_address(self, connection_name: str, ip_address: str, subnet_mask: str, gateway: str = '') -> bool:
        """
        网络接口IP地址配置的核心业务逻辑实现
        
        这个方法是网络配置服务层的核心组件，专门负责通过Windows系统的netsh工具
        来设置网络适配器的静态IP地址配置。设计遵循面向对象的单一职责原则，
        将IP地址配置与DNS配置分离，确保每个方法只负责一个特定的网络配置任务。
        
        Args:
            connection_name (str): Windows系统中网络连接的显示名称
            ip_address (str): 要设置的IPv4地址，格式为点分十进制
            subnet_mask (str): 子网掩码，定义网络和主机部分
            gateway (str, optional): 默认网关地址，用于跨网段通信
            
        Returns:
            bool: 配置操作的执行结果，True表示成功，False表示失败
        """
        try:
            # 智能处理子网掩码格式，转换为netsh命令要求的点分十进制格式
            from ...utils.ip_validation_utils import normalize_subnet_mask_for_netsh
            normalized_mask = normalize_subnet_mask_for_netsh(subnet_mask)
            
            # 构建Windows netsh命令的参数列表
            cmd = [
                'netsh', 'interface', 'ipv4', 'set', 'address',
                connection_name, 'static', ip_address, normalized_mask
            ]
            
            # 条件性添加网关参数
            if gateway and gateway.strip():
                cmd.append(gateway)
            
            # 记录即将执行的完整命令
            cmd_str = ' '.join(f'"{arg}"' if ' ' in str(arg) else str(arg) for arg in cmd)
            self.logger.debug(f"执行IP配置命令: {cmd_str}")
            
            # 执行系统命令
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=15,
                encoding='gbk', errors='replace'
            )
            
            # 记录命令执行结果
            self.logger.debug(f"netsh命令执行完成 - 返回码: {result.returncode}")
            if result.stderr.strip():
                self.logger.warning(f"命令错误输出: {result.stderr.strip()}")
            
            # 检查命令执行结果
            if result.returncode == 0:
                success_msg = f"✅ IP地址配置成功应用到网卡 '{connection_name}'"
                self.logger.debug(success_msg)
                return True
            else:
                # 命令执行失败，分析具体原因
                error_msg = f"❌ IP地址配置失败 - 网卡: '{connection_name}'"
                if result.stderr:
                    stderr_lower = result.stderr.lower()
                    if 'access is denied' in stderr_lower or '拒绝访问' in result.stderr:
                        error_msg += "\n🔐 错误原因: 权限不足，需要管理员权限"
                    elif 'not found' in stderr_lower or '找不到' in result.stderr:
                        error_msg += f"\n🔍 错误原因: 找不到网络连接 '{connection_name}'"
                    else:
                        error_msg += f"\n❗ 系统错误: {result.stderr.strip()}"
                
                self.logger.error(error_msg)
                return False
                
        except subprocess.TimeoutExpired:
            error_msg = f"⏰ IP配置命令执行超时 (>30秒) - 网卡: '{connection_name}'"
            self.logger.error(error_msg)
            return False
        except Exception as e:
            error_msg = f"💥 IP配置过程中发生未预期异常 - 网卡: '{connection_name}' - {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False
    
    def _apply_dns_config(self, connection_name: str, primary_dns: str, secondary_dns: str = '') -> bool:
        """
        网络接口DNS服务器配置的专用业务逻辑实现
        
        Args:
            connection_name (str): Windows网络连接的显示名称
            primary_dns (str): 主DNS服务器的IPv4地址
            secondary_dns (str, optional): 辅助DNS服务器地址
            
        Returns:
            bool: DNS配置操作的执行结果
        """
        try:
            success_count = 0
            total_operations = 0
            
            # 第一步：配置主DNS服务器
            if primary_dns and primary_dns.strip():
                total_operations += 1
                
                cmd_primary = [
                    'netsh', 'interface', 'ipv4', 'set', 'dnsservers',
                    connection_name, 'static', primary_dns
                ]
                
                self.logger.debug(f"执行主DNS配置: {primary_dns}")
                
                result_primary = subprocess.run(
                    cmd_primary, capture_output=True, text=True, timeout=5,
                    encoding='gbk', errors='replace'
                )
                
                if result_primary.returncode == 0:
                    success_count += 1
                    self.logger.debug(f"✅ 主DNS服务器配置成功: {primary_dns}")
                else:
                    error_msg = f"❌ 主DNS服务器配置失败 - 连接: '{connection_name}'"
                    if result_primary.stderr:
                        error_msg += f"\n错误: {result_primary.stderr.strip()}"
                    self.logger.error(error_msg)
                    return False  # 主DNS失败则整个DNS配置失败
            
            # 第二步：配置辅助DNS服务器
            if secondary_dns and secondary_dns.strip() and success_count > 0:
                total_operations += 1
                
                cmd_secondary = [
                    'netsh', 'interface', 'ipv4', 'add', 'dnsservers',
                    connection_name, secondary_dns, 'index=2'
                ]
                
                self.logger.debug(f"执行辅助DNS配置: {secondary_dns}")
                
                result_secondary = subprocess.run(
                    cmd_secondary, capture_output=True, text=True, timeout=8,
                    encoding='gbk', errors='replace'
                )
                
                if result_secondary.returncode == 0:
                    success_count += 1
                    self.logger.debug(f"✅ 辅助DNS服务器配置成功: {secondary_dns}")
                else:
                    warning_msg = f"⚠️ 辅助DNS服务器配置失败 - 连接: '{connection_name}'"
                    self.logger.warning(warning_msg)
            
            # 评估DNS配置的整体结果
            if success_count > 0:
                self.logger.debug(f"DNS配置成功，共配置 {success_count}/{total_operations} 个DNS服务器")
                return True
            else:
                self.logger.error("DNS配置完全失败")
                return False
                
        except subprocess.TimeoutExpired:
            error_msg = f"⏰ DNS配置命令执行超时 - 网卡: '{connection_name}'"
            self.logger.error(error_msg)
            return False
        except Exception as e:
            error_msg = f"💥 DNS配置过程中发生异常 - 网卡: '{connection_name}' - {str(e)}"
            self.logger.error(error_msg)
            return False
    
    def _find_adapter_basic_info(self, adapter_id: str) -> Optional[Dict[str, Any]]:
        """
        根据网卡GUID查找基本信息的核心匹配方法
        
        Args:
            adapter_id: 网卡GUID标识符，格式如{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}
            
        Returns:
            Optional[dict]: 匹配的网卡基本信息字典，包含GUID、Name、NetConnectionID等字段
        """
        try:
            # 重新获取最新的网卡基本信息，确保数据的实时性和准确性
            basic_adapters = self._get_adapters_basic_info()
            
            # 遍历所有网卡，使用GUID进行精确匹配
            for adapter in basic_adapters:
                if adapter.get('GUID') == adapter_id:
                    self.logger.debug(f"成功找到网卡基本信息: {adapter.get('NetConnectionID', 'Unknown')}")
                    return adapter
            
            # 如果没有找到匹配的网卡，记录调试信息
            self.logger.warning(f"未找到GUID为 {adapter_id} 的网卡基本信息")
            return None
            
        except Exception as e:
            # 异常安全处理，确保方法调用不会导致系统崩溃
            self.logger.error(f"查找网卡基本信息时发生异常: {str(e)}")
            return None
    
    def _get_adapters_basic_info(self) -> List[Dict[str, Any]]:
        """
        获取网卡基本信息列表
        
        通过wmic命令获取所有网卡的基本信息，
        包括名称、描述、MAC地址、状态等。
        
        Returns:
            List[Dict[str, Any]]: 网卡基本信息列表
        """
        try:
            # 执行wmic命令获取网卡基本信息，指定编码避免中文乱码
            result = subprocess.run(
                ['wmic', 'path', 'win32_networkadapter', 'where', 'NetConnectionID is not null', 'get', 
                 'Name,Description,NetConnectionID,GUID,MACAddress,NetConnectionStatus', '/format:csv'],
                capture_output=True, text=True, timeout=10, encoding='cp936', errors='replace'
            )
            
            if result.returncode != 0:
                raise Exception(f"wmic命令执行失败: {result.stderr}")
            
            # 解析CSV输出并添加调试信息
            lines = result.stdout.strip().split('\n')
            self.logger.debug(f"WMIC原始输出行数: {len(lines)}")
            
            # 清理空行和无效行
            valid_lines = [line for line in lines if line.strip() and not line.startswith('Node,')]
            self.logger.debug(f"有效行数: {len(valid_lines)}")
            
            if len(valid_lines) < 1:
                return []
            
            # 手动解析，因为CSV格式可能不标准
            adapters = []
            for line in valid_lines:
                if not line.strip():
                    continue
                
                # 按逗号分割，但要处理可能的空字段
                parts = line.split(',')
                if len(parts) >= 6:  # 至少需要6个字段
                    # 提取字段：Node, Description, GUID, MACAddress, Name, NetConnectionID, NetConnectionStatus
                    node = parts[0].strip()
                    description = parts[1].strip() if len(parts) > 1 else ''
                    guid = parts[2].strip() if len(parts) > 2 else ''
                    mac_address = parts[3].strip() if len(parts) > 3 else ''
                    name = parts[4].strip() if len(parts) > 4 else ''
                    net_connection_id = parts[5].strip() if len(parts) > 5 else ''
                    net_connection_status = parts[6].strip() if len(parts) > 6 else '0'
                    
                    # 网卡过滤逻辑 - 包含所有网卡，包括禁用的网卡
                    if description and description != '':  # 只要有描述信息就处理
                        # 对于禁用的网卡，使用Description作为显示名称
                        display_name = net_connection_id if net_connection_id else description
                        
                        adapter_dict = {
                            'Node': node,
                            'Description': description,
                            'GUID': guid,
                            'MACAddress': mac_address,
                            'Name': name,
                            'NetConnectionID': display_name,  # 使用显示名称确保禁用网卡也能显示
                            'NetConnectionStatus': net_connection_status
                        }
                        self.logger.debug(f"解析的网卡数据 (状态码: {net_connection_status}): {adapter_dict}")
                        adapters.append(adapter_dict)
            
            return adapters
            
        except Exception as e:
            self.logger.error(f"获取网卡基本信息失败: {str(e)}")
            raise
    
    # endregion
