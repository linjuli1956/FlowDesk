# -*- coding: utf-8 -*-
"""
网卡状态分析器｜专门负责网卡状态的精确判断和分析
"""
import subprocess
import logging
from typing import Dict, Tuple


class AdapterStatusAnalyzer:
    """
    网卡状态分析器
    
    专门负责网卡状态的精确判断和分析，实现双重状态判断机制。
    通过netsh命令获取管理状态和连接状态，提供比wmic更准确的状态信息。
    
    主要功能：
    - 使用netsh interface show interface命令获取精确状态
    - 实现双重状态判断逻辑（管理状态+连接状态）
    - 提供wmic状态码的备用判断机制
    - 支持多种网卡类型的状态分析
    """
    
    def __init__(self):
        """初始化状态分析器"""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_interface_status_info(self, adapter_name: str) -> Dict[str, str]:
        """
        获取网卡精确的启用和连接状态信息
        
        Args:
            adapter_name (str): 网卡连接名称
            
        Returns:
            Dict[str, str]: 包含管理状态、连接状态和接口名称的字典
        """
        # 初始化状态字典，提供默认值确保数据结构完整性
        status_info = {
            'admin_status': '未知',      # 管理状态：网卡是否被启用
            'connect_status': '未知',    # 连接状态：网卡是否已连接到网络
            'interface_name': ''         # 接口名称：用于验证匹配结果
        }
        
        try:
            # 执行netsh interface show interface命令获取所有网卡的状态表格
            # 尝试多种编码方式确保中文正确显示
            encodings_to_try = ['gbk', 'cp936', 'utf-8', 'ansi']
            result = None
            
            for encoding in encodings_to_try:
                try:
                    result = subprocess.run(
                        ['netsh', 'interface', 'show', 'interface'],
                        capture_output=True, text=True, timeout=15, 
                        encoding=encoding, errors='replace'
                    )
                    if result.returncode == 0 and '接口名称' in result.stdout:
                        self.logger.debug(f"成功使用编码 {encoding} 解析netsh输出")
                        break
                except:
                    continue
            
            if not result:
                result = subprocess.run(
                    ['netsh', 'interface', 'show', 'interface'],
                    capture_output=True, text=True, timeout=15, encoding='gbk', errors='ignore'
                )
            
            if result.returncode == 0:
                output = result.stdout
                
                # 调试：输出完整的netsh命令结果
                self.logger.debug(f"netsh interface show interface 完整输出:\n{output}")
                
                # 按行分割输出，查找目标网卡的状态信息
                lines = output.strip().split('\n')
                
                # 调试：显示所有解析的行
                self.logger.debug(f"解析到 {len(lines)} 行输出，目标网卡: '{adapter_name}'")
                
                # 提取所有可用的接口名称用于调试
                available_interfaces = []
                for line in lines:
                    line = line.strip()
                    if not line or '---' in line or line.startswith('管理员状态') or line.startswith('Admin State'):
                        continue
                    line_parts = line.split()
                    if len(line_parts) >= 4:
                        interface_name = ' '.join(line_parts[3:])
                        available_interfaces.append(interface_name)
                
                self.logger.debug(f"🔍 可用接口列表: {available_interfaces}")
                
                # 跳过表头，查找包含目标网卡名称的行
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line or '---' in line:  # 跳过空行和分隔线
                        continue
                    
                    # 检查当前行是否包含目标网卡名称
                    line_parts = line.split()
                    if len(line_parts) >= 4:
                        interface_name = ' '.join(line_parts[3:])  # 接口名称是第4列及之后的所有内容
                        
                        # 调试：显示每行的解析结果
                        self.logger.debug(f"第{i}行解析: 接口名称='{interface_name}', 完整行='{line}'")
                        
                        # 多种匹配策略：完全匹配、包含匹配、反向包含匹配
                        if (adapter_name == interface_name or 
                            adapter_name in interface_name or 
                            interface_name in adapter_name):
                            
                            # 匹配成功，解析状态信息
                            admin_state = line_parts[0]  # 管理状态
                            operational_state = line_parts[1]  # 连接状态
                            
                            self.logger.debug(f"✅ 匹配成功: 网卡 '{adapter_name}' -> 接口 '{interface_name}': "
                                            f"管理状态={admin_state}, 连接状态={operational_state}")
                            
                            # 映射管理状态
                            if admin_state == '已启用':
                                status_info['admin_status'] = '已启用'
                            elif admin_state == '已禁用':
                                status_info['admin_status'] = '已禁用'
                            else:
                                status_info['admin_status'] = '未知'
                            
                            # 映射连接状态
                            if operational_state == '已连接':
                                status_info['connect_status'] = '已连接'
                            elif operational_state == '已断开连接':
                                status_info['connect_status'] = '未连接'
                            else:
                                status_info['connect_status'] = '未知'
                            
                            status_info['interface_name'] = interface_name
                            
                            self.logger.debug(f"网卡 {adapter_name} 状态解析成功: 管理状态={status_info['admin_status']}, 连接状态={status_info['connect_status']}")
                            break
                else:
                    # 如果没有找到匹配的网卡，记录警告信息
                    self.logger.warning(f"在netsh interface show interface输出中未找到网卡: {adapter_name}")
            else:
                # 命令执行失败时的错误处理
                self.logger.error(f"netsh interface show interface命令执行失败: {result.stderr}")
                
        except Exception as e:
            # 异常安全处理，确保方法调用不会导致系统崩溃
            self.logger.error(f"获取网卡 {adapter_name} 状态信息时发生异常: {str(e)}")
        
        return status_info
    
    def determine_final_status(self, admin_status: str, connect_status: str) -> Tuple[str, bool, bool]:
        """
        基于管理状态和连接状态确定网卡的最终状态
        
        Args:
            admin_status (str): 管理状态（已启用/已禁用/未知）
            connect_status (str): 连接状态（已连接/未连接/未知）
            
        Returns:
            Tuple[str, bool, bool]: (最终状态描述, 是否启用, 是否连接)
        """
        # 第一层判断：检查管理状态（网卡是否被用户或系统启用）
        if admin_status == '已禁用':
            # 网卡被禁用时，无论连接状态如何，都视为禁用状态
            final_status = '已禁用'
            is_enabled = False
            is_connected = False
            self.logger.debug(f"状态判断结果: 网卡已禁用")
            
        elif admin_status == '已启用':
            # 网卡已启用时，需要进一步判断连接状态
            is_enabled = True
            
            # 第二层判断：检查连接状态（网卡是否实际连接到网络）
            if connect_status == '已连接':
                # 已启用且已连接：网卡正常工作，可以传输数据
                final_status = '已连接'
                is_connected = True
                self.logger.debug(f"状态判断结果: 网卡已启用且已连接")
                
            elif connect_status == '已断开连接':
                # 已启用但未连接：网卡启用但无网络连接（如网线未插、WiFi未连接）
                final_status = '未连接'
                is_connected = False
                self.logger.debug(f"状态判断结果: 网卡已启用但未连接")
                
            else:
                # 连接状态未知：无法确定具体连接情况
                final_status = '未知状态'
                is_connected = False
                self.logger.debug(f"状态判断结果: 网卡已启用但连接状态未知")
        else:
            # 管理状态未知：无法确定网卡的基本启用状态
            final_status = '未知状态'
            is_enabled = False
            is_connected = False
            self.logger.debug(f"状态判断结果: 管理状态未知")
            
        return final_status, is_enabled, is_connected
    
    def analyze_adapter_status(self, adapter_name: str, basic_info: Dict) -> Tuple[str, bool, bool]:
        """
        分析网卡状态的公共入口方法
        
        整合netsh和wmic两种状态获取方式，提供完整的状态分析能力。
        
        Args:
            adapter_name (str): 网卡连接名称
            basic_info (Dict): 网卡基本信息字典
            
        Returns:
            Tuple[str, bool, bool]: (最终状态描述, 是否启用, 是否连接)
        """
        # 获取精确的网卡状态信息 - 使用netsh interface show interface命令
        # 这是新增的双重状态判断机制，提供比wmic状态码更准确的状态信息
        interface_status = self.get_interface_status_info(adapter_name)
        
        # 应用双重状态判断逻辑 - 结合管理状态和连接状态
        # 这个逻辑遵循面向对象架构的单一职责原则，专门处理状态判断
        final_status, is_adapter_enabled, is_adapter_connected = self.determine_final_status(
            interface_status['admin_status'], 
            interface_status['connect_status']
        )
        
        # 备用状态判断机制 - 当netsh命令获取失败时使用wmic状态码
        # 遵循依赖倒置原则，提供多种状态获取方式的抽象
        if interface_status['admin_status'] == '未知' and interface_status['connect_status'] == '未知':
            self.logger.debug(f"网卡 {adapter_name} netsh状态获取失败，使用wmic状态码作为备用方案")
            
            # 原有的wmic状态码解析逻辑作为备用方案
            status_code = basic_info.get('NetConnectionStatus', '0')
            
            # 添加调试日志以分析WLAN状态码
            self.logger.debug(f"网卡 {adapter_name} wmic状态码: {status_code}")
            
            status_map = {
                '0': '已禁用',        # 网卡被用户或系统禁用
                '1': '正在连接',      # 网卡正在尝试建立连接
                '2': '已连接',        # 网卡已成功连接到网络
                '3': '正在断开',      # 网卡正在断开连接过程中
                '4': '已禁用',        # 修复：WLAN禁用时也返回状态码4，应显示为已禁用
                '5': '硬件已禁用',    # 网卡硬件被禁用（通常在设备管理器中）
                '6': '硬件故障',      # 网卡硬件出现故障
                '7': '媒体断开',      # 网线未连接或无线信号断开
                '8': '正在验证',      # 网卡正在进行身份验证
                '9': '验证失败',      # 网络身份验证失败
                '10': '验证成功',     # 网络身份验证成功
                '11': '正在获取地址'  # 网卡正在通过DHCP获取IP地址
            }
            final_status = status_map.get(status_code, '未知状态')
            
            # 备用状态判断逻辑 - 修复WLAN禁用状态判断
            is_adapter_enabled = (status_code not in ['0', '4', '5'])
            is_adapter_connected = (status_code == '2')
            
            # 特殊处理：如果是WLAN且状态码为4，根据netsh结果判断是否真的禁用
            if 'WLAN' in adapter_name and status_code == '4':
                is_adapter_enabled = False  # WLAN禁用时设为False
            
            self.logger.debug(f"网卡 {adapter_name} 备用状态分析: 状态码={status_code}, 最终状态={final_status}")
        else:
            self.logger.debug(f"网卡 {adapter_name} 精确状态分析: 管理状态={interface_status['admin_status']}, 连接状态={interface_status['connect_status']}, 最终状态={final_status}")
        
        return final_status, is_adapter_enabled, is_adapter_connected
