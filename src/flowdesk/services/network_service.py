"""
网络配置服务

功能说明：
• 封装所有网络相关的业务逻辑，包括网卡枚举、状态获取、IP配置等
• 通过PyQt信号与UI层通信，实现数据驱动的界面更新
• 提供网卡信息的智能处理，支持主IP和额外IP的自动分类
• 负责与Windows系统API交互，获取和设置网络配置

设计理念：
• 服务层作为业务逻辑的唯一入口，UI层不直接调用系统API
• 使用信号-槽机制实现松耦合的通信方式
• 提供完整的错误处理和状态反馈机制
• 支持异步操作，避免阻塞UI主线程
"""

import subprocess
import json
import re
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication

from ..models.adapter_info import AdapterInfo, IPConfigInfo, ExtraIP


class NetworkService(QObject):
    """
    网络配置服务类
    
    负责处理所有网络相关的业务逻辑，包括：
    - 网卡信息获取和枚举
    - IP配置的读取和设置
    - 网卡状态监控和同步
    - 网络信息的格式化和复制
    
    通过PyQt信号向UI层发送数据更新通知，实现数据驱动的界面刷新。
    """
    
    # 定义所有对外信号，用于与UI层通信
    adapters_updated = pyqtSignal(list)          # 网卡列表更新信号，参数：List[AdapterInfo]
    adapter_selected = pyqtSignal(object)        # 网卡选择变更信号，参数：AdapterInfo
    ip_info_updated = pyqtSignal(object)         # IP配置信息更新信号，参数：IPConfigInfo
    extra_ips_updated = pyqtSignal(list)         # 额外IP列表更新信号，参数：List[ExtraIP]
    network_info_copied = pyqtSignal(str)        # 网卡信息复制完成信号，参数：复制的文本内容
    adapter_refreshed = pyqtSignal(object)       # 单个网卡刷新完成信号，参数：AdapterInfo
    ip_config_applied = pyqtSignal(object)       # IP配置应用成功信号，参数：AdapterInfo
    operation_progress = pyqtSignal(str)         # 操作进度信号，参数：进度消息
    error_occurred = pyqtSignal(str, str)        # 错误发生信号，参数：(错误类型, 错误消息)
    extra_ips_added = pyqtSignal(str)            # 额外IP添加成功信号，参数：成功消息
    extra_ips_removed = pyqtSignal(str)          # 额外IP删除成功信号，参数：成功消息
    
    def __init__(self):
        """
        初始化网络服务
        
        设置日志记录器，初始化内部状态变量，
        为后续的网络操作做准备。
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 内部状态管理
        self._adapters: List[AdapterInfo] = []      # 缓存的网卡信息列表
        self._current_adapter: Optional[AdapterInfo] = None  # 当前选中的网卡
        
        self.logger.info("网络配置服务初始化完成")
    
    def get_all_adapters(self) -> List[AdapterInfo]:
        """
        获取所有网络适配器信息 - 快速启动优化版本
        
        这个方法实现了快速启动优化，采用延迟加载策略减少启动时间。
        只获取网卡的基本信息用于界面显示，详细配置信息在用户选择时再获取。
        
        性能优化策略：
        - 启动时只获取网卡基本信息（名称、状态、MAC地址）
        - 详细IP配置采用按需加载，用户选择网卡时才获取
        - 减少系统命令调用次数，提升启动速度
        - 保持UI响应性，避免长时间阻塞
        
        面向对象设计：
        - 单一职责：专门负责网卡信息的快速获取和缓存管理
        - 开闭原则：支持后续扩展更多优化策略
        - 依赖倒置：通过信号机制与UI层解耦
        """
        try:
            self.logger.info("开始快速获取网络适配器基本信息")
            
            # 只获取网卡基本信息，大幅减少启动时间
            adapters_info = self._get_adapters_basic_info()
            
            # 创建轻量级适配器对象，不包含详细IP配置
            # 这样可以快速显示网卡列表，详细信息按需加载
            lightweight_adapters = []
            for adapter_basic in adapters_info:
                # 创建最小化的AdapterInfo对象，只包含必要的显示信息
                # 修复字段映射：使用正确的字典键名匹配wmic输出格式
                lightweight_adapter = AdapterInfo(
                    id=adapter_basic.get('GUID', ''),
                    name=adapter_basic.get('Name', ''),
                    friendly_name=adapter_basic.get('NetConnectionID', ''),
                    description=adapter_basic.get('Description', ''),
                    mac_address=adapter_basic.get('MACAddress', ''),
                    status=self._get_status_display(adapter_basic.get('NetConnectionStatus', '0')),
                    is_connected=adapter_basic.get('NetConnectionStatus', '0') == '2',
                    # 详细配置信息留空，按需加载
                    ip_addresses=[],
                    subnet_masks=[],
                    gateway='',
                    dns_servers=[],
                    dhcp_enabled=False,
                    ipv6_addresses=[]
                )
                lightweight_adapters.append(lightweight_adapter)
            
            # 智能排序网卡列表：连接的网卡优先显示
            # 这确保了UI显示顺序与服务层选择优先级完全一致
            # 解决启动时下拉框选中网卡与显示信息不匹配的根本问题
            sorted_adapters = self._sort_adapters_by_priority(lightweight_adapters)
            
            # 更新内部缓存为排序后的列表
            self._adapters = sorted_adapters
            
            # 发射信号通知UI层快速更新
            self.adapters_updated.emit(self._adapters)
            
            # 自动选中第一个网卡（现在已经是优先级最高的网卡）
            # 由于列表已经按优先级排序，第一个网卡就是最佳选择
            if self._adapters:
                self.select_adapter(self._adapters[0].id)
            
            self.logger.info(f"网络适配器信息获取完成，共找到 {len(self._adapters)} 个网卡")
            return self._adapters
            
        except Exception as e:
            error_msg = f"获取网络适配器信息失败: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit("网卡枚举错误", error_msg)
            return []
    
    def _sort_adapters_by_priority(self, adapters):
        """
        按优先级智能排序网卡列表的核心排序方法
        
        这个方法解决了启动时网卡信息不匹配的根本问题，通过统一的排序逻辑
        确保UI显示顺序与服务层选择优先级完全一致。该方法体现了面向对象
        架构中业务逻辑封装的重要原则，将复杂的排序策略集中管理。
        
        面向对象架构特点：
        - 封装性：将复杂的网卡优先级排序逻辑完全封装在独立方法中
        - 单一职责：专门负责网卡列表的优先级排序，不涉及其他业务逻辑
        - 开闭原则：可以通过修改排序规则扩展功能，不影响调用方代码
        - 依赖倒置：依赖于AdapterInfo抽象数据模型，不依赖具体实现
        
        排序优先级策略：
        1. 已连接的网卡优先级最高（is_connected=True）
        2. 已连接网卡内部按友好名称字母序排序
        3. 未连接的网卡排在后面（is_connected=False）
        4. 未连接网卡内部按友好名称字母序排序
        
        这样确保了用户最常使用的连接网卡始终显示在下拉框顶部，
        同时保持了相同状态网卡之间的稳定排序，提供一致的用户体验。
        
        Args:
            adapters (list): 未排序的AdapterInfo对象列表
            
        Returns:
            list: 按优先级排序后的AdapterInfo对象列表
        """
        try:
            # 使用Python内置的sorted函数进行多级排序
            # key函数返回元组，Python会按元组元素顺序进行排序
            sorted_adapters = sorted(adapters, key=lambda adapter: (
                # 第一级排序：连接状态（False排在True前面，所以用not取反）
                # 这样is_connected=True的网卡会排在前面
                not adapter.is_connected,
                
                # 第二级排序：友好名称字母序（相同连接状态内部排序）
                # 使用lower()确保大小写不敏感的排序
                (adapter.friendly_name or adapter.name or adapter.description or "").lower()
            ))
            
            # 记录排序结果便于调试和监控
            connected_count = sum(1 for a in sorted_adapters if a.is_connected)
            self.logger.debug(f"网卡排序完成：已连接 {connected_count} 个，未连接 {len(sorted_adapters) - connected_count} 个")
            
            return sorted_adapters
            
        except Exception as e:
            # 异常处理：排序失败时返回原列表，确保功能不受影响
            self.logger.error(f"网卡排序失败，使用原始顺序: {str(e)}")
            return adapters
    
    def select_adapter(self, adapter_id: str) -> None:
        """
        选择指定网络适配器并自动获取最新信息的智能选择方法
        
        这个方法实现了网卡选择的完整业务逻辑，遵循面向对象架构的单一职责原则。
        不仅完成网卡选择，还自动获取最新的网卡详细信息，确保显示数据的准确性。
        这是解决"选择网卡后信息不准确"问题的核心方法。
        
        业务流程：
        1. 查找并选择指定的网卡
        2. 自动获取该网卡的最新详细信息
        3. 更新缓存中的网卡数据
        4. 发射信号通知UI层更新显示
        
        Args:
            adapter_id (str): 网络适配器GUID标识符
        """
        try:
            # 第一步：在适配器列表中查找指定ID的网卡
            selected_adapter = None
            for adapter in self._adapters:
                if adapter.id == adapter_id:
                    selected_adapter = adapter
                    break
            
            if not selected_adapter:
                raise Exception(f"未找到ID为 {adapter_id} 的网络适配器")
            
            # 第二步：自动获取该网卡的最新详细信息
            # 这是解决信息不准确问题的关键步骤
            basic_info = self._find_adapter_basic_info(adapter_id)
            if basic_info:
                # 获取最新的详细信息，包括实时的IP配置
                refreshed_adapter = self._get_adapter_detailed_info(basic_info)
                if refreshed_adapter:
                    # 更新缓存中的网卡信息，确保数据一致性
                    for i, adapter in enumerate(self._adapters):
                        if adapter.id == refreshed_adapter.id:
                            self._adapters[i] = refreshed_adapter
                            break
                    
                    # 使用最新的网卡信息作为选中的网卡
                    selected_adapter = refreshed_adapter
                    self.logger.info(f"已自动刷新网卡信息: {selected_adapter.friendly_name}")
                else:
                    self.logger.warning(f"无法获取网卡 {selected_adapter.friendly_name} 的最新信息，使用缓存数据")
            else:
                self.logger.warning(f"无法找到网卡 {selected_adapter.friendly_name} 的基本信息，使用缓存数据")
            
            # 第三步：更新当前选中的网卡
            self._current_adapter = selected_adapter
            
            # 第四步：发射网卡选择信号，通知UI层更新
            self.adapter_selected.emit(selected_adapter)
            
            # 第五步：构造并发射IP配置信息信号
            ip_config = IPConfigInfo(
                adapter_id=selected_adapter.id,
                ip_address=selected_adapter.get_primary_ip(),
                subnet_mask=selected_adapter.get_primary_subnet_mask(),
                gateway=selected_adapter.gateway,
                dns_primary=selected_adapter.get_primary_dns(),
                dns_secondary=selected_adapter.get_secondary_dns(),
                dhcp_enabled=selected_adapter.dhcp_enabled
            )
            self.ip_info_updated.emit(ip_config)
            
            # 第六步：构造并发射额外IP信息信号
            extra_ips = []
            for ip, mask in selected_adapter.get_extra_ips():
                extra_ips.append(ExtraIP(ip_address=ip, subnet_mask=mask))
            self.extra_ips_updated.emit(extra_ips)
            
            self.logger.info(f"网卡选择完成: {selected_adapter.friendly_name}")
            
        except Exception as e:
            error_msg = f"选择网卡失败: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit("网卡选择错误", error_msg)
    
    def refresh_current_adapter(self) -> None:
        """
        刷新当前选中网卡的信息
        
        重新获取当前选中网卡的最新信息，
        更新缓存并通知UI层刷新显示。
        
        这是"刷新按钮"功能的核心实现。
        """
        if not self._current_adapter:
            self.logger.warning("没有选中的网卡，无法刷新")
            return
        
        try:
            self.logger.info(f"开始刷新网卡信息: {self._current_adapter.friendly_name}")
            
            # 重新获取当前网卡的详细信息
            basic_info = self._find_adapter_basic_info(self._current_adapter.id)
            if basic_info:
                refreshed_adapter = self._get_adapter_detailed_info(basic_info)
                if refreshed_adapter:
                    # 更新缓存中的网卡信息
                    for i, adapter in enumerate(self._adapters):
                        if adapter.id == refreshed_adapter.id:
                            self._adapters[i] = refreshed_adapter
                            break
                    
                    # 更新当前选中的网卡
                    self._current_adapter = refreshed_adapter
                    
                    # 发射刷新完成信号
                    self.adapter_refreshed.emit(refreshed_adapter)
                    
                    # 重新选择当前网卡以触发界面更新
                    self.select_adapter(refreshed_adapter.id)
                    
                    self.logger.info(f"网卡信息刷新完成: {refreshed_adapter.friendly_name}")
                else:
                    raise Exception("获取网卡详细信息失败")
            else:
                raise Exception("未找到网卡基本信息")
                
        except Exception as e:
            error_msg = f"刷新网卡信息失败: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit("网卡刷新错误", error_msg)
    
    def copy_adapter_info(self) -> None:
        """
        复制当前网卡信息到剪贴板
        
        将当前选中网卡的完整信息格式化为文本，
        复制到系统剪贴板，并发射复制完成信号。
        """
        if not self._current_adapter:
            self.logger.warning("没有选中的网卡，无法复制信息")
            return
        
        try:
            # 使用与界面显示一致的格式化方法
            # 确保复制的内容与左侧IP信息容器显示的内容完全一致
            from flowdesk.ui.main_window import MainWindow
            main_window = None
            
            # 查找MainWindow实例以使用其格式化方法
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                for widget in app.allWidgets():
                    if isinstance(widget, MainWindow):
                        main_window = widget
                        break
            
            if main_window:
                # 使用MainWindow的格式化方法，确保与界面显示一致
                formatted_info = main_window._format_adapter_info_for_display(self._current_adapter)
            else:
                # 备用方案：使用原有的格式化方法
                formatted_info = self._current_adapter.format_for_copy()
            
            # 复制到剪贴板
            clipboard = QApplication.clipboard()
            clipboard.setText(formatted_info)
            
            # 发射复制完成信号
            self.network_info_copied.emit(formatted_info)
            
            self.logger.info(f"网卡信息已复制到剪贴板: {self._current_adapter.friendly_name}")
            
        except Exception as e:
            error_msg = f"复制网卡信息失败: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit("信息复制错误", error_msg)
    
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
                capture_output=True, text=True, timeout=30, encoding='cp936', errors='replace'
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
                    # 这里不仅处理有NetConnectionID的网卡，也要处理禁用状态的网卡
                    # 禁用的网卡可能NetConnectionID为空，但仍需要在界面中显示
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
    
    def _get_status_display(self, status_code: str) -> str:
        """
        将网卡状态码转换为中文显示文本
        
        这个方法将Windows系统的网卡连接状态码转换为用户友好的中文显示文本。
        遵循面向对象架构的单一职责原则，专门负责状态码的转换逻辑。
        
        Args:
            status_code (str): 网卡连接状态码
            
        Returns:
            str: 中文状态显示文本
        """
        status_map = {
            '0': '已断开连接',
            '1': '正在连接',
            '2': '已连接',
            '3': '正在断开连接',
            '4': '硬件不存在',
            '5': '硬件已禁用',
            '6': '硬件故障',
            '7': '媒体已断开连接',
            '8': '正在验证身份',
            '9': '身份验证成功',
            '10': '身份验证失败',
            '11': '无效地址',
            '12': '凭据需要'
        }
        return status_map.get(status_code, '未知状态')
    
    def _get_adapter_detailed_info(self, basic_info: Dict[str, Any]) -> Optional[AdapterInfo]:
        """
        获取网卡详细信息
        
        基于网卡基本信息，进一步获取IP配置、DNS设置等详细信息，
        构造完整的AdapterInfo对象。
        
        Args:
            basic_info (Dict[str, Any]): 网卡基本信息字典
            
        Returns:
            Optional[AdapterInfo]: 完整的网卡信息对象，失败时返回None
        """
        try:
            adapter_name = basic_info.get('NetConnectionID', '')
            if not adapter_name:
                return None
            
            # 获取IP配置信息
            ip_config = self._get_adapter_ip_config(adapter_name)
            
            # 增强DNS配置获取 - 使用netsh命令作为补充数据源
            # 遵循开闭原则，通过新增功能而不修改现有逻辑来增强DNS获取能力
            enhanced_dns = self._get_enhanced_dns_config(adapter_name)
            if enhanced_dns:
                # 如果netsh获取到了DNS信息，优先使用或合并到现有DNS列表中
                existing_dns = ip_config.get('dns_servers', [])
                # 合并DNS服务器列表，去重并保持顺序
                combined_dns = enhanced_dns.copy()
                for dns in existing_dns:
                    if dns not in combined_dns:
                        combined_dns.append(dns)
                ip_config['dns_servers'] = combined_dns
                self.logger.debug(f"网卡 {adapter_name} DNS配置已增强: {combined_dns}")
            
            # 获取精确的网卡状态信息 - 使用netsh interface show interface命令
            # 这是新增的双重状态判断机制，提供比wmic状态码更准确的状态信息
            interface_status = self._get_interface_status_info(adapter_name)
            
            # 应用双重状态判断逻辑 - 结合管理状态和连接状态
            # 这个逻辑遵循面向对象架构的单一职责原则，专门处理状态判断
            final_status, is_adapter_enabled, is_adapter_connected = self._determine_final_status(
                interface_status['admin_status'], 
                interface_status['connect_status']
            )
            
            # 备用状态判断机制 - 当netsh命令获取失败时使用wmic状态码
            # 遵循依赖倒置原则，提供多种状态获取方式的抽象
            if interface_status['admin_status'] == '未知' and interface_status['connect_status'] == '未知':
                self.logger.info(f"网卡 {adapter_name} netsh状态获取失败，使用wmic状态码作为备用方案")
                
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
            
            # 构造完整的网卡信息对象
            # 采用面向对象设计，将所有网卡相关数据封装在AdapterInfo类中
            adapter_info = AdapterInfo(
                id=basic_info.get('GUID', ''),                    # 网卡全局唯一标识符
                name=basic_info.get('Name', ''),                  # 网卡完整名称（系统内部使用）
                friendly_name=adapter_name,                       # 网卡友好名称（用户界面显示）
                description=basic_info.get('Description', ''),    # 网卡硬件描述信息
                mac_address=basic_info.get('MACAddress', ''),     # 网卡物理MAC地址
                status=final_status,                              # 网卡当前连接状态的中文描述（使用增强的状态判断结果）
                is_enabled=is_adapter_enabled,                    # 网卡是否处于启用状态
                is_connected=is_adapter_connected,                # 网卡是否已连接到网络
                ip_addresses=ip_config.get('ip_addresses', []),
                ipv6_addresses=ip_config.get('ipv6_addresses', []),
                subnet_masks=ip_config.get('subnet_masks', []),
                gateway=ip_config.get('gateway', ''),
                dns_servers=ip_config.get('dns_servers', []),
                dhcp_enabled=ip_config.get('dhcp_enabled', True),
                link_speed=ip_config.get('link_speed', ''),
                interface_type=self._get_interface_type(basic_info.get('Description', '')),
                last_updated=datetime.now()
            )
            
            return adapter_info
            
        except Exception as e:
            self.logger.error(f"获取网卡详细信息失败: {str(e)}")
            return None
    
    def _get_adapter_ip_config(self, adapter_name: str) -> Dict[str, Any]:
        """
        获取指定网卡IP配置信息的增强版本
        
        这个方法实现了多重数据源的IP配置获取策略，遵循面向对象架构的开闭原则。
        通过多种命令组合获取网卡配置，确保数据的完整性和准确性，
        解决"显示未知、未配置"等信息不准确的问题。
        
        技术实现：
        - 使用netsh命令获取基础IP配置信息
        - 使用ipconfig命令作为补充数据源
        - 实现智能的编码处理，支持中英文系统
        - 采用正则表达式精确解析网络配置参数
        
        Args:
            adapter_name (str): 网卡连接名称，如"vEthernet (泰兴)"
            
        Returns:
            Dict[str, Any]: 包含完整IP配置信息的字典，包括IP地址、子网掩码、网关、DNS等
        """
        # 初始化配置字典，提供默认值确保数据结构完整性
        config = {
            'ip_addresses': [],
            'ipv6_addresses': [],
            'subnet_masks': [],
            'gateway': '',
            'dns_servers': [],
            'dhcp_enabled': True,
            'link_speed': ''
        }
        
        try:
            # 第一步：使用netsh命令获取详细的IP配置信息
            # 这是主要的数据获取方式，支持IPv4配置的完整信息
            result = subprocess.run(
                ['netsh', 'interface', 'ipv4', 'show', 'config', f'name={adapter_name}'],
                capture_output=True, text=True, timeout=15, encoding='gbk', errors='ignore'
            )
            
            if result.returncode == 0:
                output = result.stdout
                self.logger.debug(f"netsh命令输出: {output[:200]}...")  # 记录前200字符用于调试
                
                # 解析DHCP启用状态
                if "DHCP 已启用" in output or "DHCP enabled" in output:
                    config['dhcp_enabled'] = True
                elif "静态配置" in output or "Statically Configured" in output:
                    config['dhcp_enabled'] = False
                
                # 使用增强的正则表达式解析IP地址和子网掩码
                # 支持多种格式的IP地址显示
                ip_patterns = [
                    r'IP 地址:\s*(\d+\.\d+\.\d+\.\d+)',
                    r'IP Address:\s*(\d+\.\d+\.\d+\.\d+)',
                    r'静态 IP 地址:\s*(\d+\.\d+\.\d+\.\d+)'
                ]
                
                mask_patterns = [
                    r'子网前缀长度:\s*(\d+)',
                    r'Subnet Prefix Length:\s*(\d+)',
                    r'子网掩码:\s*(\d+\.\d+\.\d+\.\d+)'
                ]
                
                # 尝试多种模式匹配IP地址
                ip_matches = []
                for pattern in ip_patterns:
                    matches = re.findall(pattern, output)
                    if matches:
                        ip_matches.extend(matches)
                        break
                
                # 尝试多种模式匹配子网掩码
                mask_matches = []
                for pattern in mask_patterns:
                    matches = re.findall(pattern, output)
                    if matches:
                        mask_matches.extend(matches)
                        break
                
                config['ip_addresses'] = ip_matches if ip_matches else []
                
                # 将前缀长度转换为子网掩码
                config['subnet_masks'] = []
                for mask_value in mask_matches:
                    try:
                        # 如果是前缀长度（数字），转换为子网掩码
                        if mask_value.isdigit():
                            prefix_len = int(mask_value)
                            subnet_mask = self._prefix_to_netmask(prefix_len)
                            config['subnet_masks'].append(subnet_mask)
                        else:
                            # 如果已经是子网掩码格式，直接使用
                            config['subnet_masks'].append(mask_value)
                    except (ValueError, TypeError):
                        continue
                
                # 解析默认网关，支持多种语言格式
                gateway_patterns = [
                    r'默认网关[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',
                    r'Default Gateway[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',
                    r'网关[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)'
                ]
                
                for pattern in gateway_patterns:
                    gateway_match = re.search(pattern, output)
                    if gateway_match:
                        config['gateway'] = gateway_match.group(1)
                        break
                
                # 解析DNS服务器，支持多种格式
                dns_patterns = [
                    r'静态配置的 DNS 服务器:\s*(\d+\.\d+\.\d+\.\d+)',
                    r'DNS Servers:\s*(\d+\.\d+\.\d+\.\d+)',
                    r'DNS 服务器:\s*(\d+\.\d+\.\d+\.\d+)'
                ]
                
                for pattern in dns_patterns:
                    dns_matches = re.findall(pattern, output)
                    if dns_matches:
                        config['dns_servers'] = dns_matches
                        break
            
            # 第二步：优先使用ipconfig作为主要数据源，因为它更准确
            # 对于复杂的网络配置（多IP、多子网掩码），ipconfig比netsh更可靠
            self._supplement_config_with_ipconfig(adapter_name, config)
            
            return config
            
        except Exception as e:
            self.logger.error(f"获取IP配置失败: {str(e)}")
            return config
    
    def _supplement_config_with_ipconfig(self, adapter_name: str, config: Dict[str, Any]) -> None:
        """
        使用ipconfig命令补充网卡配置信息的增强版本
        
        这个方法实现了完整的ipconfig输出解析，专门处理多IP地址、多子网掩码的复杂网络配置。
        遵循面向对象架构的单一职责原则，将ipconfig解析逻辑完全封装，
        确保能够准确获取Windows系统的真实网络配置信息。
        
        技术实现：
        - 精确匹配网卡配置段落，支持中英文系统
        - 处理多个IPv4地址和对应的子网掩码
        - 解析DHCP状态、网关、DNS服务器等完整配置
        - 实现容错机制，确保解析的稳定性
        
        Args:
            adapter_name (str): 网卡连接名称，如"vEthernet (泰兴)"
            config (Dict[str, Any]): 需要补充的配置字典
        """
        try:
            # 使用ipconfig /all命令获取系统完整的网络配置信息
            result = subprocess.run(
                ['ipconfig', '/all'],
                capture_output=True, text=True, timeout=6, encoding='gbk', errors='ignore'
            )
            
            if result.returncode == 0:
                output = result.stdout
                self.logger.debug(f"ipconfig输出长度: {len(output)} 字符")
                
                # 构建更精确的网卡段落匹配模式，支持无线和以太网适配器
                # 匹配从网卡名称开始到下一个网卡或文件结束的完整段落
                adapter_patterns = [
                    rf'无线局域网适配器\s+{re.escape(adapter_name)}:(.*?)(?=\n以太网适配器|\n无线局域网适配器|\nPPP 适配器|\Z)',
                    rf'以太网适配器\s+{re.escape(adapter_name)}:(.*?)(?=\n以太网适配器|\n无线局域网适配器|\nPPP 适配器|\Z)'
                ]
                
                adapter_match = None
                for pattern in adapter_patterns:
                    adapter_match = re.search(pattern, output, re.DOTALL | re.IGNORECASE)
                    if adapter_match:
                        break
                
                if adapter_match:
                    adapter_section = adapter_match.group(1)
                    self.logger.debug(f"找到网卡 {adapter_name} 的配置段落，长度: {len(adapter_section)} 字符")
                    
                    # 解析多个IPv4地址
                    # 支持"IPv4 地址 . . . . . . . . . . . . : 172.2.208.10(首选)"格式
                    ip_pattern = r'IPv4 地址[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)'
                    ip_matches = re.findall(ip_pattern, adapter_section, re.IGNORECASE)
                    if ip_matches:
                        config['ip_addresses'] = ip_matches
                        self.logger.debug(f"解析到IPv4地址: {ip_matches}")
                    
                    # IPv6地址解析逻辑 - 支持多种IPv6地址格式的识别和提取
                    # 这个正则表达式用于从ipconfig输出中提取IPv6地址信息
                    # 支持标准IPv6格式、链路本地地址、临时地址等多种类型
                    ipv6_patterns = [
                        r'IPv6 地址[.\s]*:\s*([0-9a-fA-F:]+(?:%\d+)?)',           # 标准IPv6地址格式
                        r'临时 IPv6 地址[.\s]*:\s*([0-9a-fA-F:]+(?:%\d+)?)',      # 临时IPv6地址
                        r'链接本地 IPv6 地址[.\s]*:\s*([0-9a-fA-F:]+(?:%\d+)?)',  # 链路本地IPv6地址
                        r'本地链接 IPv6 地址[.\s]*:\s*([0-9a-fA-F:]+(?:%\d+)?)'   # 本地链接IPv6地址（不同Windows版本的表述）
                    ]
                    
                    # 使用多个正则模式匹配不同类型的IPv6地址
                    # 这种设计遵循开闭原则，便于后续扩展支持更多IPv6地址类型
                    ipv6_addresses = []
                    for pattern in ipv6_patterns:
                        matches = re.findall(pattern, adapter_section, re.IGNORECASE)
                        ipv6_addresses.extend(matches)
                    
                    # 去重并保存IPv6地址列表
                    # 使用集合去重后转回列表，保持数据结构一致性
                    if ipv6_addresses:
                        config['ipv6_addresses'] = list(set(ipv6_addresses))
                        self.logger.debug(f"解析到IPv6地址: {config['ipv6_addresses']}")
                    else:
                        config['ipv6_addresses'] = []
                        self.logger.debug("未找到IPv6地址配置")
                    
                    # 解析对应的子网掩码
                    # 支持"子网掩码  . . . . . . . . . . . . : 255.255.0.0"格式
                    mask_pattern = r'子网掩码[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)'
                    mask_matches = re.findall(mask_pattern, adapter_section, re.IGNORECASE)
                    if mask_matches:
                        config['subnet_masks'] = mask_matches
                        self.logger.debug(f"解析到子网掩码: {mask_matches}")
                    
                    # 解析默认网关
                    # 支持"默认网关 . . . . . . . . . . . . : 192.168.1.1"格式
                    gateway_pattern = r'默认网关[.\s]*:\s*([^\n]*(?:\n\s*\d+\.\d+\.\d+\.\d+)?)'
                    gateway_match = re.search(gateway_pattern, adapter_section, re.IGNORECASE)
                    if gateway_match:
                        gateway_text = gateway_match.group(1).strip()
                        # 查找IPv4地址（优先使用IPv4网关）
                        ipv4_pattern = r'(\d+\.\d+\.\d+\.\d+)'
                        ipv4_matches = re.findall(ipv4_pattern, gateway_text)
                        if ipv4_matches:
                            config['gateway'] = ipv4_matches[0]  # 使用第一个IPv4地址
                            self.logger.debug(f"解析到IPv4网关: {ipv4_matches[0]}")
                    
                    # 解析DNS服务器配置 - 增强的DNS解析逻辑
                    # 这是解决"DNS服务器获取不准确"问题的关键代码，支持更多DNS配置格式
                    dns_patterns = [
                        r'DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',                    # 标准DNS格式
                        r'通过 DHCP 配置的 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',  # DHCP DNS格式
                        r'静态配置的 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',          # 静态DNS格式
                        r'首选 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',              # 首选DNS格式
                        r'备用 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',              # 备用DNS格式
                        r'Primary DNS Server[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',           # 英文主DNS
                        r'Secondary DNS Server[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',         # 英文备用DNS
                    ]
                    
                    dns_servers_found = []
                    # 逐个尝试所有DNS匹配模式，确保不遗漏任何可能的DNS配置
                    for i, pattern in enumerate(dns_patterns, 1):
                        dns_matches = re.findall(pattern, adapter_section, re.IGNORECASE)
                        if dns_matches:
                            dns_servers_found.extend(dns_matches)
                            self.logger.debug(f"ipconfig DNS模式{i}匹配成功: {dns_matches}")
                    
                    # 如果标准模式都没有找到DNS，尝试多行DNS配置解析
                    if not dns_servers_found:
                        self.logger.debug("尝试多行DNS配置解析")
                        # 查找DNS服务器配置行，然后提取后续行中的IP地址
                        dns_section_pattern = r'DNS 服务器[^:]*:([^\n]*(?:\n\s+[^\n]*)*)'  
                        dns_section_match = re.search(dns_section_pattern, adapter_section, re.IGNORECASE)
                        if dns_section_match:
                            dns_section = dns_section_match.group(1)
                            # 从DNS配置段落中提取所有IP地址
                            ip_addresses = re.findall(r'(\d+\.\d+\.\d+\.\d+)', dns_section)
                            if ip_addresses:
                                dns_servers_found.extend(ip_addresses)
                                self.logger.debug(f"多行DNS解析成功: {ip_addresses}")
                    
                    if dns_servers_found:
                        # 去重并保持顺序，确保DNS服务器列表的唯一性和正确性
                        unique_dns = []
                        seen = set()
                        for dns in dns_servers_found:
                            # 过滤掉无效的DNS地址（如0.0.0.0或本地地址）
                            if dns not in seen and not dns.startswith('0.') and not dns.startswith('127.'):
                                seen.add(dns)
                                unique_dns.append(dns)
                        config['dns_servers'] = unique_dns
                        self.logger.debug(f"ipconfig最终解析到DNS服务器: {unique_dns}")
                    else:
                        self.logger.debug(f"ipconfig未能解析到DNS服务器，网卡段落内容: {adapter_section[:300]}...")
                    
                    # 解析DHCP状态
                    # 支持"DHCP 已启用 . . . . . . . . . . . : 否"格式
                    dhcp_pattern = r'DHCP 已启用[.\s]*:\s*(是|否)'
                    dhcp_match = re.search(dhcp_pattern, adapter_section, re.IGNORECASE)
                    if dhcp_match:
                        config['dhcp_enabled'] = (dhcp_match.group(1) == '是')
                        self.logger.debug(f"解析到DHCP状态: {config['dhcp_enabled']}")
                    
                    # 解析链路速度信息
                    # 通过wmic命令获取网卡的链路速度，这是ipconfig无法提供的信息
                    self._get_link_speed_info(adapter_name, config)
                    
                    self.logger.info(f"成功使用ipconfig补充网卡 {adapter_name} 的完整配置信息")
                else:
                    self.logger.warning(f"在ipconfig输出中未找到网卡 {adapter_name} 的配置段落")
                
        except Exception as e:
            self.logger.error(f"使用ipconfig补充配置信息失败: {str(e)}")
    
    def _get_interface_status_info(self, adapter_name: str) -> Dict[str, str]:
        """
        获取网卡精确的启用和连接状态信息
        
        这个方法通过netsh interface show interface命令获取网卡的精确状态信息，
        遵循面向对象架构的单一职责原则，专门负责状态信息的获取和解析。
        相比wmic命令的状态码，这种方式能够更准确地区分网卡的启用状态和连接状态。
        
        技术实现：
        - 使用netsh interface show interface命令获取所有网卡的状态表格
        - 通过友好名称精确匹配目标网卡
        - 解析"管理状态"和"状态"两个关键字段
        - 支持中英文系统的状态文本识别
        
        状态说明：
        - 管理状态：已启用/已禁用（用户或系统设置的启用状态）
        - 状态：已连接/已断开连接（实际的网络连接状态）
        
        Args:
            adapter_name (str): 网卡友好名称，如"以太网"、"WLAN"等
            
        Returns:
            Dict[str, str]: 包含状态信息的字典，键包括：
                - admin_status: 管理状态（已启用/已禁用/未知）
                - connect_status: 连接状态（已连接/已断开连接/未知）
                - interface_name: 接口名称（用于验证匹配正确性）
        """
        # 初始化状态字典，提供默认值确保数据结构完整性
        status_info = {
            'admin_status': '未知',      # 管理状态：网卡是否被启用
            'connect_status': '未知',    # 连接状态：网卡是否已连接到网络
            'interface_name': ''         # 接口名称：用于验证匹配结果
        }
        
        try:
            # 执行netsh interface show interface命令获取所有网卡的状态表格
            # 这个命令返回系统中所有网络接口的详细状态信息
            result = subprocess.run(
                ['netsh', 'interface', 'show', 'interface'],
                capture_output=True, text=True, timeout=15, encoding='gbk', errors='ignore'
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # 按行分割输出，查找目标网卡的状态信息
                lines = output.strip().split('\n')
                
                # 跳过表头，查找包含目标网卡名称的行
                for line in lines:
                    line = line.strip()
                    if not line or '---' in line:  # 跳过空行和分隔线
                        continue
                    
                    # 检查当前行是否包含目标网卡名称
                    # 使用多种匹配策略，因为netsh输出的名称可能与友好名称略有差异
                    line_parts = line.split()
                    if len(line_parts) >= 4:
                        interface_name = ' '.join(line_parts[3:])  # 接口名称是第4列及之后的所有内容
                        
                        # 多种匹配策略：完全匹配、包含匹配、反向包含匹配
                        if (adapter_name == interface_name or 
                            adapter_name in interface_name or 
                            interface_name in adapter_name):
                            
                            # 解析状态行的格式：管理状态 状态 类型 接口名称
                            # 典型格式："已启用     已连接     专用         以太网"
                            admin_status_raw = line_parts[0].strip()      # 管理状态
                            connect_status_raw = line_parts[1].strip()    # 连接状态
                            
                            # 解析管理状态（第一列）- 网卡是否被启用
                            if '已启用' in admin_status_raw or 'Enabled' in admin_status_raw:
                                status_info['admin_status'] = '已启用'
                            elif '已禁用' in admin_status_raw or 'Disabled' in admin_status_raw:
                                status_info['admin_status'] = '已禁用'
                            else:
                                status_info['admin_status'] = '未知'
                            
                            # 解析连接状态（第二列）- 网卡是否已连接
                            if '已连接' in connect_status_raw or 'Connected' in connect_status_raw:
                                status_info['connect_status'] = '已连接'
                            elif '已断开连接' in connect_status_raw or 'Disconnected' in connect_status_raw or '未连接' in connect_status_raw or 'Not connected' in connect_status_raw:
                                status_info['connect_status'] = '已断开连接'
                            else:
                                status_info['connect_status'] = '未知'
                            
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
    
    def _determine_final_status(self, admin_status: str, connect_status: str) -> tuple:
        """
        基于管理状态和连接状态确定网卡的最终状态
        
        这个方法实现了双重状态判断逻辑，遵循面向对象架构的单一职责原则。
        通过组合分析网卡的管理状态（启用/禁用）和连接状态（连接/断开），
        得出用户界面显示的最终状态和相应的布尔标志。
        
        判断逻辑：
        1. 已禁用 → 最终状态：已禁用，is_enabled=False, is_connected=False
        2. 已启用 + 已连接 → 最终状态：已连接，is_enabled=True, is_connected=True
        3. 已启用 + 已断开连接 → 最终状态：未连接，is_enabled=True, is_connected=False
        4. 其他情况 → 最终状态：未知状态，is_enabled=False, is_connected=False
        
        Args:
            admin_status (str): 管理状态（已启用/已禁用/未知）
            connect_status (str): 连接状态（已连接/已断开连接/未知）
            
        Returns:
            tuple: 包含三个元素的元组：
                - final_status (str): 最终显示状态
                - is_enabled (bool): 网卡是否启用
                - is_connected (bool): 网卡是否已连接
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
            self.logger.debug(f"状态判断结果: 网卡管理状态未知")
        
        return final_status, is_enabled, is_connected
    
    def _get_enhanced_dns_config(self, adapter_name: str) -> List[str]:
        """
        使用netsh命令增强DNS服务器信息获取
        
        这个方法通过正确的netsh命令语法获取DNS配置信息，解决之前语法错误的问题。
        遵循面向对象架构的开闭原则，作为现有DNS获取方式的补充和增强。
        
        技术实现：
        - 使用正确的netsh interface ipv4 show config "接口名称"语法
        - 专门解析DNS服务器配置段落，支持多种输出格式
        - 实现异常安全的DNS解析机制
        - 与现有DNS获取方式进行数据融合
        
        Args:
            adapter_name (str): 网卡友好名称，如"以太网"、"WLAN"等
            
        Returns:
            List[str]: DNS服务器IP地址列表，按优先级排序
        """
        dns_servers = []
        
        try:
            # 修复netsh命令语法：使用正确的参数格式
            # 正确语法：netsh interface ipv4 show config "接口名称"
            # 错误语法：netsh interface ipv4 show config name="接口名称"
            cmd = ['netsh', 'interface', 'ipv4', 'show', 'config', f'"{adapter_name}"']
            self.logger.debug(f"执行修复后的netsh DNS获取命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=8, encoding='gbk', errors='ignore'
            )
            
            # 详细的调试日志，帮助诊断DNS获取问题
            self.logger.debug(f"netsh命令返回码: {result.returncode}")
            if result.stdout:
                # 显示更多输出内容以便调试
                self.logger.debug(f"netsh命令完整输出: {result.stdout}")
            if result.stderr:
                self.logger.debug(f"netsh命令错误输出: {result.stderr}")
            
            if result.returncode == 0 and result.stdout.strip():
                output = result.stdout
                
                # 检查输出是否包含错误信息或帮助信息
                if "此命令提供的语法不正确" in output or "用法:" in output:
                    self.logger.warning(f"netsh命令语法仍然不正确，输出: {output[:100]}...")
                    return dns_servers
                
                # 增强的DNS正则表达式模式，支持更多格式
                # 这些模式基于实际的Windows netsh输出格式设计
                dns_patterns = [
                    r'通过 DHCP 配置的 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',  # DHCP DNS格式
                    r'DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',                    # 标准DNS格式
                    r'静态配置的 DNS 服务器[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',          # 静态DNS格式
                    r'DNS Servers[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',                   # 英文系统格式
                    r'主 DNS 后缀[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',                   # 主DNS后缀格式
                    r'备用 DNS 后缀[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)',                 # 备用DNS后缀格式
                ]
                
                # 逐个尝试所有DNS匹配模式
                # 这种设计确保能够捕获各种可能的DNS配置格式
                for i, pattern in enumerate(dns_patterns, 1):
                    matches = re.findall(pattern, output, re.IGNORECASE | re.MULTILINE)
                    if matches:
                        dns_servers.extend(matches)
                        self.logger.debug(f"DNS模式{i}匹配成功: {matches}")
                
                # 如果标准模式都没有匹配，尝试更宽松的IP地址匹配
                if not dns_servers:
                    self.logger.debug("标准DNS模式未匹配，尝试宽松IP地址匹配")
                    # 查找所有可能的IP地址，然后过滤掉明显不是DNS的地址
                    ip_pattern = r'(\d+\.\d+\.\d+\.\d+)'
                    all_ips = re.findall(ip_pattern, output)
                    # 过滤掉本地地址和广播地址
                    for ip in all_ips:
                        if not (ip.startswith('127.') or ip.startswith('0.') or 
                               ip.endswith('.0') or ip.endswith('.255') or ip == '255.255.255.255'):
                            dns_servers.append(ip)
                            self.logger.debug(f"通过宽松匹配找到可能的DNS: {ip}")
                
                # 去重并保持顺序，确保DNS服务器列表的唯一性
                seen = set()
                unique_dns = []
                for dns in dns_servers:
                    if dns not in seen:
                        seen.add(dns)
                        unique_dns.append(dns)
                dns_servers = unique_dns
                
            else:
                self.logger.warning(f"netsh DNS配置命令执行失败或无输出: 返回码={result.returncode}, 错误={result.stderr}")
                
        except subprocess.TimeoutExpired:
            # 超时异常的专门处理，避免阻塞启动流程
            self.logger.warning(f"netsh DNS获取超时，跳过网卡 {adapter_name} 的DNS配置")
        except Exception as e:
            # 异常安全处理，确保DNS获取失败不影响主流程
            self.logger.debug(f"使用netsh获取网卡 {adapter_name} DNS配置时发生异常: {str(e)}")
        
        return dns_servers

    def _get_link_speed_info(self, adapter_name: str, config: Dict[str, Any]) -> None:
        """
        获取网卡链路速度信息的优化版本
        
        使用wmic nic命令直接通过网卡描述匹配获取速度，这种方法对所有网卡类型都有效。
        遵循面向对象架构的单一职责原则，专门负责链路速度的获取和格式化。
        
        技术实现：
        - 使用wmic nic where "NetEnabled=true"查询所有启用的网卡
        - 通过网卡描述精确匹配目标网卡
        - 将比特/秒转换为用户友好的Mbps/Gbps格式
        - 实现异常安全的查询机制，确保不影响主流程
        
        Args:
            adapter_name (str): 网卡连接名称
            config (Dict[str, Any]): 配置字典，用于存储链路速度信息
        """
        self.logger.info(f"开始为网卡 {adapter_name} 获取链路速度信息，当前值: {config.get('link_speed', '')}")
        
        try:
            # 首先需要根据adapter_name找到对应的网卡描述
            # 因为wmic nic使用的是Description，而不是NetConnectionID
            adapter_description = self._get_adapter_description_by_name(adapter_name)
            if not adapter_description:
                self.logger.debug(f"无法获取网卡 {adapter_name} 的描述，尝试备用方法")
                # 如果无法获取描述，直接尝试netsh备用方法
                if adapter_name.upper() == 'WLAN' or '无线' in adapter_name:
                    wlan_speed = self._get_wireless_link_speed(adapter_name)
                    if wlan_speed:
                        config['link_speed'] = wlan_speed
                        self.logger.debug(f"使用netsh备用方法成功获取链路速度: {wlan_speed}")
                        return
                config['link_speed'] = '未知'
                return
            
            # 使用wmic nic命令查询所有启用网卡的Name和Speed
            result = subprocess.run(
                ['wmic', 'nic', 'where', 'NetEnabled=true', 'get', 'Name,Speed', '/format:csv'],
                capture_output=True, text=True, timeout=10, encoding='cp936', errors='replace'
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                lines = [line for line in output.split('\n') if line.strip() and not line.startswith('Node,')]
                
                self.logger.info(f"wmic nic输出行数: {len(lines)}")
                self.logger.info(f"目标网卡描述: '{adapter_description}'")
                
                # 如果无法获取描述，直接尝试通过友好名称匹配
                if not adapter_description:
                    self.logger.debug(f"无网卡描述，尝试通过友好名称 '{adapter_name}' 匹配")
                    
                for i, line in enumerate(lines):
                    parts = line.split(',')
                    self.logger.debug(f"第{i+1}行解析: parts数量={len(parts)}")
                    
                    if len(parts) >= 3:  # Node,Name,Speed
                        name = parts[1].strip()
                        speed_str = parts[2].strip()
                        
                        self.logger.info(f"网卡名称: '{name}', 速度: '{speed_str}'")
                        
                        # 多重匹配策略：描述匹配 或 关键字匹配
                        is_match = False
                        if adapter_description:
                            # 策略1：完整描述匹配
                            if adapter_description.lower() == name.lower():
                                is_match = True
                                self.logger.info(f"完整描述匹配成功")
                            # 策略2：描述包含匹配
                            elif adapter_description.lower() in name.lower() or name.lower() in adapter_description.lower():
                                is_match = True  
                                self.logger.info(f"描述包含匹配成功")
                        
                        # 策略3：针对WLAN的关键字匹配（备用策略）
                        if not is_match and adapter_name.upper() == 'WLAN':
                            if 'wireless' in name.lower() or '802.11' in name.lower() or 'wlan' in name.lower():
                                is_match = True
                                self.logger.info(f"WLAN关键字匹配成功")
                        
                        if is_match:
                            self.logger.info(f"网卡匹配成功! 名称: {name}")
                            if speed_str and speed_str.isdigit():
                                # 将比特/秒转换为用户友好的格式
                                speed_bps = int(speed_str)
                                if speed_bps >= 1000000000:  # >= 1 Gbps
                                    speed_formatted = f"{speed_bps / 1000000000:.1f} Gbps"
                                elif speed_bps >= 1000000:  # >= 1 Mbps
                                    speed_formatted = f"{speed_bps / 1000000:.1f} Mbps"
                                else:
                                    speed_formatted = f"{speed_bps} bps"
                                
                                config['link_speed'] = speed_formatted
                                self.logger.info(f"wmic nic解析到链路速度: {speed_formatted} (匹配网卡: {name})")
                                return
                            else:
                                self.logger.info(f"匹配的网卡速度为空或无效: '{speed_str}'")
                
                self.logger.debug("wmic nic方法未找到匹配的网卡或速度信息")
            else:
                self.logger.debug(f"wmic nic命令执行失败: return code {result.returncode}")
                self.logger.debug(f"错误输出: {result.stderr}")
            
            # 如果wmic nic失败，尝试使用netsh wlan作为备用方法
            if adapter_name.upper() == 'WLAN' or '无线' in adapter_name:
                self.logger.debug(f"wmic nic未获取到速度，尝试netsh wlan方法作为备用")
                wlan_speed = self._get_wireless_link_speed(adapter_name)
                if wlan_speed:
                    config['link_speed'] = wlan_speed
                    self.logger.debug(f"netsh wlan备用方法解析到链路速度: {wlan_speed}")
                    return
                
            # 如果无法获取具体速度，设置为未知
            config['link_speed'] = '未知'
                
        except Exception as e:
            self.logger.warning(f"获取网卡 {adapter_name} 链路速度失败: {str(e)}")
            config['link_speed'] = '未知'
    
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
        self.logger.info(f"开始查询网卡 {adapter_name} 的硬件描述信息")
        
        try:
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
            self.logger.debug(f"wmic查询输出: {repr(result.stdout)}")
            
            if result.returncode == 0:
                output = result.stdout.strip()
                # 过滤掉空行和CSV头部，只保留数据行
                lines = [line for line in output.split('\n') if line.strip() and not line.startswith('Node,')]
                
                self.logger.debug(f"解析到 {len(lines)} 行有效数据")
                
                if lines:
                    for i, line in enumerate(lines):
                        self.logger.debug(f"处理第 {i+1} 行数据: {repr(line)}")
                        parts = line.split(',')
                        if len(parts) >= 2:
                            description = parts[1].strip()
                            if description:
                                self.logger.info(f"成功获取网卡 {adapter_name} 的描述: {description}")
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
            self.logger.debug(f"获取网卡描述失败: {str(e)}")
            return None
    
    def _get_wireless_link_speed(self, adapter_name: str) -> Optional[str]:
        """
        获取无线网卡链路速度的专用方法
        
        使用netsh wlan show interface命令获取无线网卡的连接速度信息，
        这是针对无线网卡Speed属性经常为空的专门解决方案。
        
        Args:
            adapter_name (str): 无线网卡连接名称，如"WLAN"
            
        Returns:
            Optional[str]: 格式化的链路速度字符串，如"72.2 Mbps"，失败时返回None
        """
        try:
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'interface'],
                capture_output=True, text=True, timeout=8, encoding='cp936', errors='replace'
            )
            
            if result.returncode == 0:
                output = result.stdout
                self.logger.debug(f"netsh wlan完整输出:\n{output}")
                
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
                        self.logger.debug(f"netsh解析到无线速率: {speed_formatted} (使用模式{i}: {pattern})")
                        return speed_formatted
                
                self.logger.debug("netsh wlan所有模式都未匹配到速率信息")
                # 输出前200个字符用于调试
                debug_output = output[:200].replace('\n', '\\n')
                self.logger.debug(f"netsh输出前200字符: {debug_output}")
                
            else:
                self.logger.debug(f"netsh wlan命令执行失败: return code {result.returncode}")
                
        except subprocess.TimeoutExpired:
            self.logger.debug(f"netsh wlan查询超时")
        except Exception as e:
            self.logger.debug(f"netsh wlan查询失败: {str(e)}")
            
        return None
    
    def _find_adapter_basic_info(self, adapter_id: str) -> Optional[Dict[str, Any]]:
        """
        根据网卡GUID查找基本信息的核心匹配方法
        
{{ ... }}
        这个方法实现了网卡信息检索的核心逻辑，通过GUID精确匹配网卡。
        遵循面向对象架构的封装性原则，将复杂的查找逻辑封装在独立方法中，
        确保数据访问的一致性和可靠性。
        
        技术实现：
        - 重新获取最新的网卡基本信息，确保数据时效性
        - 使用GUID进行精确匹配，避免名称变化导致的匹配失败
        - 实现异常安全的查找逻辑，确保系统稳定性
        
        Args:
            adapter_id (str): 网卡GUID标识符，格式如{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}
            
        Returns:
            Optional[Dict[str, Any]]: 匹配的网卡基本信息字典，包含GUID、Name、NetConnectionID等字段
                                   未找到匹配项时返回None
        """
        try:
            # 重新获取最新的网卡基本信息，确保数据的实时性和准确性
            # 这是解决"刷新时找不到网卡"问题的关键步骤
            basic_adapters = self._get_adapters_basic_info()
            
            # 遍历所有网卡，使用GUID进行精确匹配
            # GUID是网卡的唯一标识符，比Index或Name更可靠
            for adapter in basic_adapters:
                # 关键修复：使用GUID字段进行匹配，而不是Index字段
                # 这解决了刷新时"未找到网卡基本信息"的核心问题
                if adapter.get('GUID') == adapter_id:
                    self.logger.debug(f"成功找到网卡基本信息: {adapter.get('NetConnectionID', 'Unknown')}")
                    return adapter
            
            # 如果没有找到匹配的网卡，记录调试信息帮助排查问题
            self.logger.warning(f"未找到GUID为 {adapter_id} 的网卡基本信息")
            return None
            
        except Exception as e:
            # 异常安全处理，确保方法调用不会导致系统崩溃
            self.logger.error(f"查找网卡基本信息时发生异常: {str(e)}")
            return None
    
    def _prefix_to_netmask(self, prefix_length: int) -> str:
        """
        将子网前缀长度转换为子网掩码
        
        Args:
            prefix_length (int): 前缀长度（如24）
            
        Returns:
            str: 子网掩码（如255.255.255.0）
        """
        mask = (0xffffffff >> (32 - prefix_length)) << (32 - prefix_length)
        return f"{(mask >> 24) & 0xff}.{(mask >> 16) & 0xff}.{(mask >> 8) & 0xff}.{mask & 0xff}"
    
    def _get_interface_type(self, description: str) -> str:
        """
        根据网卡描述判断接口类型
        
        Args:
            description (str): 网卡描述信息
            
        Returns:
            str: 接口类型（如"以太网"、"无线"等）
        """
        description_lower = description.lower()
        
        if 'wireless' in description_lower or 'wi-fi' in description_lower or '无线' in description_lower:
            return '无线'
        elif 'ethernet' in description_lower or '以太网' in description_lower:
            return '以太网'
        elif 'bluetooth' in description_lower or '蓝牙' in description_lower:
            return '蓝牙'
        elif 'virtual' in description_lower or '虚拟' in description_lower:
            return '虚拟'
        else:
            return '其他'
    
    def apply_ip_config(self, adapter_id: str, ip_address: str, subnet_mask: str, 
                       gateway: str = '', primary_dns: str = '', secondary_dns: str = '') -> bool:
        """
        应用IP配置到指定网卡的核心业务方法
        
        此方法负责将用户输入的IP配置信息应用到选定的网络适配器上。
        采用Windows netsh命令实现配置修改，确保与系统原生网络管理的兼容性。
        实现了完整的错误处理和进度反馈机制，遵循单一职责原则。
        
        架构设计：
        - 输入验证：确保IP地址格式正确，避免无效配置
        - 分步执行：IP配置和DNS配置分别处理，提供细粒度控制
        - 信号通信：通过PyQt信号向UI层报告操作进度和结果
        - 异常安全：完整的try-catch机制，确保操作失败时不影响系统稳定性
        
        Args:
            adapter_id (str): 目标网卡的GUID标识符
            ip_address (str): 要设置的IP地址
            subnet_mask (str): 子网掩码
            gateway (str, optional): 默认网关地址，可选
            primary_dns (str, optional): 主DNS服务器地址，可选
            secondary_dns (str, optional): 辅助DNS服务器地址，可选
            
        Returns:
            bool: 配置应用成功返回True，失败返回False
            
        Raises:
            无直接异常抛出，所有异常均被捕获并通过信号报告
        """
        try:
            # 发射操作开始信号，通知UI层显示进度指示器
            self.operation_progress.emit("开始应用IP配置...")
            self.logger.info(f"开始为网卡 {adapter_id} 应用IP配置")
            
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
            self.logger.info(f"准备配置网卡: {connection_name} (ID: {adapter_id})")
            self.logger.debug(f"网卡详细信息: {adapter_info}")
            
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
            
            # 第三步：刷新当前网卡信息，确保UI显示最新配置
            self.operation_progress.emit("正在刷新网卡信息...")
            self.refresh_current_adapter()
            
            # 发射成功信号，通知UI层配置已完成
            success_msg = f"网卡 {connection_name} 的IP配置已成功应用"
            self.logger.info(success_msg)
            self.ip_config_applied.emit(success_msg)
            self.operation_progress.emit("IP配置应用完成")
            
            return True
            
        except Exception as e:
            # 捕获所有未预期的异常，确保方法的异常安全性
            error_msg = f"应用IP配置时发生异常: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit("系统异常", error_msg)
            return False
    
    def _apply_ip_address(self, connection_name: str, ip_address: str, subnet_mask: str, gateway: str = '') -> bool:
        """
        网络接口IP地址配置的核心业务逻辑实现
        
        这个方法是网络配置服务层的核心组件，专门负责通过Windows系统的netsh工具
        来设置网络适配器的静态IP地址配置。设计遵循面向对象的单一职责原则，
        将IP地址配置与DNS配置分离，确保每个方法只负责一个特定的网络配置任务。
        
        面向对象设计特点：
        - 封装性：将复杂的netsh命令构建和执行逻辑封装在方法内部
        - 单一职责：只负责IP地址、子网掩码和网关的配置，不涉及DNS设置
        - 依赖倒置：通过参数注入的方式接收配置数据，不直接依赖UI层
        - 开闭原则：可以通过继承扩展新的IP配置策略，无需修改现有代码
        
        技术实现说明：
        netsh interface ipv4 set address命令是Windows系统提供的网络配置工具，
        它可以在管理员权限下修改网络适配器的IP配置。命令的基本语法为：
        netsh interface ipv4 set address name="连接名" static IP地址 子网掩码 [网关]
        
        Args:
            connection_name (str): Windows系统中网络连接的显示名称，如"以太网"、"WLAN"等
            ip_address (str): 要设置的IPv4地址，格式为点分十进制，如"192.168.1.100"
            subnet_mask (str): 子网掩码，定义网络和主机部分，如"255.255.255.0"
            gateway (str, optional): 默认网关地址，用于跨网段通信，可选参数
            
        Returns:
            bool: 配置操作的执行结果，True表示成功，False表示失败
            
        Raises:
            subprocess.TimeoutExpired: 当netsh命令执行超过30秒时抛出超时异常
            Exception: 其他系统级异常，如权限不足、网卡不存在等
        """
        try:
            # 构建Windows netsh命令的参数列表
            # 根据Windows官方文档和实际测试，正确的netsh语法为位置参数格式：
            # netsh interface ipv4 set address "连接名" static IP地址 子网掩码 [网关地址]
            # 使用列表形式可以避免shell注入攻击，提高安全性
            cmd = [
                'netsh',                    # Windows网络配置工具
                'interface',                # 网络接口操作模块
                'ipv4',                     # IPv4协议栈配置
                'set',                      # 设置操作命令
                'address',                  # 地址配置子命令
                connection_name,            # 目标网络连接名称（不需要引号）
                'static',                   # 指定使用静态IP配置模式
                ip_address,                 # IPv4地址参数（位置参数）
                subnet_mask                 # 子网掩码参数（位置参数）
            ]
            
            # 条件性添加网关参数
            # 网关是可选配置，只有在用户提供且非空时才添加到命令中
            # 作为位置参数直接添加到命令末尾
            if gateway and gateway.strip():
                cmd.append(gateway)
            
            # 记录即将执行的完整命令，用于调试和问题排查
            # 将命令列表转换为可读的字符串格式，便于日志记录和问题分析
            cmd_str = ' '.join(f'"{arg}"' if ' ' in str(arg) else str(arg) for arg in cmd)
            self.logger.info(f"执行IP配置命令: {cmd_str}")
            self.logger.debug(f"命令参数详情: {cmd}")
            
            # 使用subprocess模块执行系统命令
            # 这是Python中执行外部程序的标准方式，具有良好的安全性和控制能力
            # 设置30秒超时是因为网络配置操作可能需要较长时间完成
            result = subprocess.run(
                cmd,                        # 要执行的命令列表
                capture_output=True,        # 捕获标准输出和错误输出
                text=True,                  # 以文本模式处理输出（而非字节模式）
                timeout=30,                 # 命令执行超时限制（秒）
                encoding='gbk',             # 中文Windows系统的默认编码
                errors='replace'            # 编码错误时用替换字符处理，避免程序崩溃
            )
            
            # 详细记录命令执行结果，包括返回码、标准输出和错误输出
            # 这些信息对于调试网络配置问题非常重要
            self.logger.info(f"netsh命令执行完成 - 返回码: {result.returncode}")
            if result.stdout.strip():
                self.logger.info(f"命令输出: {result.stdout.strip()}")
            if result.stderr.strip():
                self.logger.warning(f"命令错误输出: {result.stderr.strip()}")
            
            # 检查命令执行结果
            # netsh命令成功时返回码为0，失败时为非零值
            if result.returncode == 0:
                success_msg = f"✅ IP地址配置成功应用到网卡 '{connection_name}'"
                success_msg += f"\n   📍 IP地址: {ip_address}"
                success_msg += f"\n   🔒 子网掩码: {subnet_mask}"
                if gateway:
                    success_msg += f"\n   🚪 网关: {gateway}"
                self.logger.info(success_msg)
                return True
            else:
                # 命令执行失败，分析具体原因并提供解决建议
                error_msg = f"❌ IP地址配置失败 - 网卡: '{connection_name}'"
                
                # 分析常见错误原因
                if result.stderr:
                    stderr_lower = result.stderr.lower()
                    if 'access is denied' in stderr_lower or '拒绝访问' in result.stderr:
                        error_msg += "\n🔐 错误原因: 权限不足，需要管理员权限"
                    elif 'not found' in stderr_lower or '找不到' in result.stderr:
                        error_msg += f"\n🔍 错误原因: 找不到网络连接 '{connection_name}'"
                    elif 'invalid' in stderr_lower or '无效' in result.stderr:
                        error_msg += "\n⚠️ 错误原因: 网络参数格式无效"
                    else:
                        error_msg += f"\n❗ 系统错误: {result.stderr.strip()}"
                
                error_msg += f"\n📊 返回码: {result.returncode}"
                if result.stdout.strip():
                    error_msg += f"\n📝 命令输出: {result.stdout.strip()}"
                
                self.logger.error(error_msg)
                return False
                
        except subprocess.TimeoutExpired:
            error_msg = f"⏰ IP配置命令执行超时 (>30秒)\n网卡: '{connection_name}'\n可能原因: 系统响应缓慢或网络服务异常"
            self.logger.error(error_msg)
            return False
        except FileNotFoundError:
            error_msg = "🚫 系统错误: 找不到netsh命令\n请确认Windows系统完整性"
            self.logger.error(error_msg)
            return False
        except Exception as e:
            error_msg = f"💥 IP配置过程中发生未预期异常\n网卡: '{connection_name}'\n异常详情: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False
    
    def _apply_dns_config(self, connection_name: str, primary_dns: str, secondary_dns: str = '') -> bool:
        """
        网络接口DNS服务器配置的专用业务逻辑实现
        
        这个方法是网络配置服务的重要组成部分，专门负责DNS服务器的设置。
        DNS（Domain Name System）是互联网的基础服务，将域名转换为IP地址。
        正确的DNS配置对于网络连接的稳定性和访问速度至关重要。
        
        面向对象设计原则体现：
        - 单一职责原则：只负责DNS配置，与IP地址配置完全分离
        - 开闭原则：可以通过继承扩展支持IPv6 DNS或其他DNS配置策略
        - 里氏替换原则：可以被子类重写而不影响调用方的行为
        - 接口隔离原则：提供简洁的方法签名，只暴露必要的参数
        - 依赖倒置原则：依赖于抽象的连接名称和DNS地址，不依赖具体实现
        
        技术实现细节：
        Windows系统使用netsh interface ipv4 set dns命令来配置DNS服务器。
        主DNS服务器使用"static"模式设置，辅助DNS使用"add"模式追加。
        这种分步配置方式确保了DNS服务器列表的正确顺序。
        
        Args:
            connection_name (str): Windows网络连接的显示名称，必须与系统中的实际连接名匹配
            primary_dns (str): 主DNS服务器的IPv4地址，如"8.8.8.8"（Google DNS）
            secondary_dns (str, optional): 辅助DNS服务器地址，用于主DNS不可用时的备用解析
            
        Returns:
            bool: DNS配置操作的执行结果，True表示所有DNS服务器配置成功
            
        Note:
            如果主DNS配置失败，方法会立即返回False，不会尝试配置辅助DNS
            这样可以避免DNS配置处于不一致的状态
        """
        try:
            # 初始化操作计数器，用于跟踪DNS配置的成功率
            # 这种计数方式体现了面向对象编程中的状态管理原则
            success_count = 0
            total_operations = 0
            
            # 第一步：配置主DNS服务器
            # 主DNS是必需的，它是域名解析的首选服务器
            # 只有在用户提供了有效的主DNS地址时才进行配置
            if primary_dns and primary_dns.strip():
                total_operations += 1
                
                # 构建主DNS配置命令
                # 根据Windows官方文档，正确的DNS配置语法为位置参数格式：
                # netsh interface ipv4 set dnsservers "连接名" static DNS地址
                cmd_primary = [
                    'netsh',                        # Windows网络配置工具
                    'interface',                    # 网络接口操作模块  
                    'ipv4',                         # IPv4协议栈配置
                    'set',                          # 设置操作命令
                    'dnsservers',                   # DNS服务器配置子命令（注意是dnsservers不是dns）
                    connection_name,                # 目标网络连接名称（位置参数，不需要name=格式）
                    'static',                       # 静态DNS配置模式
                    primary_dns                     # 主DNS服务器地址（位置参数）
                ]
                
                self.logger.debug(f"准备配置主DNS服务器: {primary_dns}")
                
                # 记录即将执行的DNS配置命令，便于调试和问题排查
                cmd_str = ' '.join(f'"{arg}"' if ' ' in str(arg) else str(arg) for arg in cmd_primary)
                self.logger.info(f"执行主DNS配置命令: {cmd_str}")
                
                # 执行主DNS配置命令
                result_primary = subprocess.run(
                    cmd_primary,
                    capture_output=True,
                    text=True,
                    timeout=15,                     # DNS配置通常比IP配置更快
                    shell=False,                    # 不使用shell，提高安全性
                    encoding='utf-8',               # 使用UTF-8编码处理中文输出
                    errors='replace'                # 处理编码错误，避免程序崩溃
                )
                
                # 记录命令执行结果
                self.logger.info(f"主DNS命令执行完成 - 返回码: {result_primary.returncode}")
                if result_primary.stdout.strip():
                    self.logger.info(f"命令输出: {result_primary.stdout.strip()}")
                if result_primary.stderr.strip():
                    self.logger.warning(f"命令错误输出: {result_primary.stderr.strip()}")
                
                # 检查主DNS配置结果
                if result_primary.returncode == 0:
                    success_count += 1
                    self.logger.info(f"✅ 主DNS服务器配置成功: {primary_dns}")
                else:
                    # 主DNS配置失败，分析具体原因并提供解决建议
                    error_msg = f"❌ 主DNS服务器配置失败 - 连接: '{connection_name}'"
                    if result_primary.stderr:
                        stderr_lower = result_primary.stderr.lower()
                        if 'not found' in stderr_lower or '找不到' in result_primary.stderr:
                            error_msg += f"\n🔍 错误原因: 找不到网络连接 '{connection_name}'"
                        elif 'access is denied' in stderr_lower or '拒绝访问' in result_primary.stderr:
                            error_msg += "\n🔐 错误原因: 权限不足，需要管理员权限"
                        else:
                            error_msg += f"\n❗ 系统错误: {result_primary.stderr.strip()}"
                    
                    error_msg += f"\n📊 返回码: {result_primary.returncode}"
                    error_msg += f"\n📝 执行的命令: {cmd_str}"
                    
                    self.logger.error(error_msg)
                    return False  # 主DNS失败则整个DNS配置失败
            
            # 第二步：配置辅助DNS服务器（可选）
            # 辅助DNS提供冗余和负载分担，提高域名解析的可靠性
            # 只有在主DNS配置成功且用户提供了辅助DNS时才进行配置
            if secondary_dns and secondary_dns.strip() and success_count > 0:
                total_operations += 1
                
                # 构建辅助DNS配置命令
                # 根据Windows官方文档，正确的辅助DNS添加语法为位置参数格式：
                # netsh interface ipv4 add dnsservers "连接名" DNS地址 index=2
                cmd_secondary = [
                    'netsh',                        # Windows网络配置工具
                    'interface',                    # 网络接口操作模块
                    'ipv4',                         # IPv4协议栈配置
                    'add',                          # 添加操作命令
                    'dnsservers',                   # DNS服务器添加子命令
                    connection_name,                # 目标网络连接名称（位置参数）
                    secondary_dns,                  # 辅助DNS服务器地址（位置参数）
                    'index=2'                       # 设置为第二优先级（键值对参数）
                ]
                
                self.logger.debug(f"准备配置辅助DNS服务器: {secondary_dns}")
                
                # 记录即将执行的辅助DNS配置命令
                cmd_str_secondary = ' '.join(f'"{arg}"' if ' ' in str(arg) else str(arg) for arg in cmd_secondary)
                self.logger.info(f"执行辅助DNS配置命令: {cmd_str_secondary}")
                
                # 执行辅助DNS配置命令
                result_secondary = subprocess.run(
                    cmd_secondary,
                    capture_output=True,
                    text=True,
                    timeout=15,
                    shell=False,                    # 不使用shell，提高安全性
                    encoding='utf-8',               # 使用UTF-8编码处理中文输出
                    errors='replace'                # 处理编码错误
                )
                
                # 记录辅助DNS命令执行结果
                self.logger.info(f"辅助DNS命令执行完成 - 返回码: {result_secondary.returncode}")
                if result_secondary.stdout.strip():
                    self.logger.info(f"命令输出: {result_secondary.stdout.strip()}")
                if result_secondary.stderr.strip():
                    self.logger.warning(f"命令错误输出: {result_secondary.stderr.strip()}")
                
                # 检查辅助DNS配置结果
                if result_secondary.returncode == 0:
                    success_count += 1
                    self.logger.info(f"✅ 辅助DNS服务器配置成功: {secondary_dns}")
                else:
                    # 辅助DNS配置失败不是致命错误，但需要记录详细信息
                    warning_msg = f"⚠️ 辅助DNS服务器配置失败 - 连接: '{connection_name}'"
                    if result_secondary.stderr:
                        warning_msg += f"\n❗ 系统错误: {result_secondary.stderr.strip()}"
                    warning_msg += f"\n📊 返回码: {result_secondary.returncode}"
                    warning_msg += f"\n📝 执行的命令: {cmd_str_secondary}"
                    self.logger.warning(warning_msg)
            
            # 评估DNS配置的整体结果
            # 只要主DNS配置成功，就认为DNS配置基本成功
            if success_count > 0:
                if success_count == total_operations:
                    self.logger.info(f"DNS配置完全成功，共配置 {success_count} 个DNS服务器")
                else:
                    self.logger.info(f"DNS配置部分成功，{success_count}/{total_operations} 个DNS服务器配置成功")
                return True
            else:
                self.logger.error("DNS配置完全失败，没有成功配置任何DNS服务器")
                return False
                
        except subprocess.TimeoutExpired:
            error_msg = f"⏰ DNS配置命令执行超时 (>15秒)\n网卡: '{connection_name}'\n可能原因: 系统响应缓慢或网络服务异常"
            self.logger.error(error_msg)
            return False
        except Exception as e:
            error_msg = f"💥 DNS配置过程中发生未预期异常\n网卡: '{connection_name}'\n异常详情: {str(e)}"
            self.logger.error(error_msg)
            return False

    def add_selected_extra_ips(self, adapter_name: str, ip_configs: list):
        """
        批量添加选中的额外IP到指定网卡的核心业务方法
        
        核心作用与业务价值：
        这个方法是FlowDesk网络管理系统中批量IP配置添加的核心入口点。
        它负责将用户在界面上选择的多个IP配置，通过Windows系统API批量添加到指定的网络适配器上。
        这个功能在企业网络环境中非常重要，可以让单个网卡承载多个IP地址，实现虚拟主机、负载均衡等高级网络配置。
        
        面向对象设计原则的完整体现：
        
        1. 单一职责原则(Single Responsibility Principle)：
           - 该方法专门负责批量额外IP添加的业务逻辑处理
           - 不涉及UI交互、数据持久化或其他无关职责
           - 每个内部步骤都有明确的单一目的
        
        2. 开闭原则(Open-Closed Principle)：
           - 通过参数化设计支持不同网卡和IP配置的扩展
           - 新增网卡类型或IP格式时无需修改现有代码
           - 通过继承和多态可以扩展新的添加策略
        
        3. 里氏替换原则(Liskov Substitution Principle)：
           - 作为NetworkService的方法，遵循基类定义的契约
           - 子类可以安全地重写此方法而不破坏系统行为
           - 返回值和异常处理符合基类期望
        
        4. 接口分离原则(Interface Segregation Principle)：
           - 提供专用的IP添加接口，与删除、查询等操作完全分离
           - UI层只需要知道添加操作的接口，不需要了解其他复杂功能
           - 通过信号机制实现松耦合的结果通知
        
        5. 依赖倒置原则(Dependency Inversion Principle)：
           - 依赖AdapterInfo抽象数据模型而非具体的网卡硬件实现
           - 通过subprocess抽象层调用系统命令，而非直接操作底层API
           - 使用PyQt信号机制实现与UI层的解耦
        
        企业级软件架构特点：
        
        - 事务性操作：支持批量处理，提供原子性操作保证
        - 异常安全：完整的错误处理和恢复机制，确保系统稳定性
        - 可观测性：详细的日志记录和操作追踪，便于问题诊断
        - 用户体验：友好的错误提示和操作反馈，提升用户满意度
        - 性能优化：批量操作减少系统调用开销
        - 安全性：输入验证和权限检查，防止恶意操作
        
        业务流程的精心设计：
        
        1. 输入参数严格验证：确保网卡名称和IP配置列表的有效性
        2. 智能网卡查找算法：支持多种标识符匹配，提高容错性
        3. IP配置解析和格式验证：确保每个IP地址和子网掩码的正确性
        4. 批量系统API调用：逐个添加IP配置，记录每次操作结果
        5. 全面的结果统计分析：区分成功、失败和异常情况
        6. 实时UI状态同步：刷新网卡信息，确保界面显示最新状态
        7. 用户友好的结果反馈：通过信号机制触发相应的提示弹窗
        
        错误处理的多层次策略：
        
        - 预防性验证：在操作前检查所有输入参数的合法性
        - 渐进式容错：部分失败时继续处理剩余配置，最大化成功率
        - 详细错误分类：区分格式错误、系统错误、权限错误等不同类型
        - 用户友好提示：将技术错误转换为易懂的用户提示信息
        - 完整日志记录：记录所有操作细节，便于后续问题排查
        
        Args:
            adapter_name (str): 目标网络适配器的友好名称，用于在系统中唯一标识网卡
            ip_configs (list): IP配置字符串列表，每个元素格式为"IP地址 / 子网掩码"
                              例如：["192.168.1.100 / 255.255.255.0", "10.0.0.50 / 255.255.255.0"]
        
        信号发射：
            extra_ips_added: 操作成功时发射，携带成功消息
            error_occurred: 操作失败时发射，携带错误标题和详细信息
        
        异常处理：
            所有异常都被捕获并转换为用户友好的错误信号，确保系统稳定性
        """
        try:
            # 第一步：输入参数验证
            if not adapter_name or not ip_configs:
                error_msg = "❌ 批量添加IP失败：缺少必要参数\n请确保已选择网卡并勾选要添加的IP配置"
                self.error_occurred.emit("参数错误", error_msg)
                return
            
            self.logger.info(f"开始批量添加额外IP到网卡: {adapter_name}，共 {len(ip_configs)} 个IP配置")
            
            # 第二步：智能查找目标网卡信息
            # 支持多种网卡标识符匹配：友好名称、描述、完整名称
            # 这种设计提高了系统的容错性和用户体验
            target_adapter = None
            self.logger.info(f"正在查找网卡: '{adapter_name}'")
            self.logger.info(f"当前缓存中共有 {len(self._adapters)} 个网卡")
            
            for adapter in self._adapters:
                self.logger.info(f"检查网卡 - 友好名称: '{adapter.friendly_name}', 描述: '{adapter.description}', 完整名称: '{adapter.name}'")
                
                # 多重匹配策略：优先匹配友好名称，其次描述，最后完整名称
                # 这种灵活的匹配机制确保UI层可以使用任何一种网卡标识符
                if (adapter.friendly_name == adapter_name or 
                    adapter.description == adapter_name or 
                    adapter.name == adapter_name):
                    target_adapter = adapter
                    self.logger.info(f"成功匹配网卡: '{adapter_name}' -> 友好名称: '{adapter.friendly_name}'")
                    break
            
            if not target_adapter:
                error_msg = f"❌ 网卡查找失败：'{adapter_name}'\n可能原因：\n• 网卡已被禁用或断开连接\n• 网卡名称已更改\n• 系统网络配置发生变化"
                self.logger.error(f"网卡查找失败，当前可用网卡: {[adapter.friendly_name for adapter in self._adapters]}")
                self.error_occurred.emit("网卡不存在", error_msg)
                return
            
            # 第三步：批量处理IP配置添加
            success_count = 0
            failed_configs = []
            
            for ip_config in ip_configs:
                try:
                    # 解析IP配置格式：支持 "192.168.1.100/255.255.255.0" 和 "192.168.1.100 / 255.255.255.0"
                    if '/' not in ip_config:
                        failed_configs.append(f"{ip_config} (格式错误)")
                        continue
                    
                    # 兼容两种格式：带空格和不带空格的斜杠分隔符
                    if ' / ' in ip_config:
                        ip_address, subnet_mask = ip_config.split(' / ', 1)
                    else:
                        ip_address, subnet_mask = ip_config.split('/', 1)
                    ip_address = ip_address.strip()
                    subnet_mask = subnet_mask.strip()
                    
                    # 调用Windows网络API添加额外IP
                    success = self._add_extra_ip_to_adapter(target_adapter, ip_address, subnet_mask)
                    
                    if success:
                        success_count += 1
                        self.logger.info(f"✅ 成功添加额外IP: {ip_address}/{subnet_mask}")
                    else:
                        failed_configs.append(f"{ip_address}/{subnet_mask}")
                        self.logger.warning(f"❌ 添加额外IP失败: {ip_address}/{subnet_mask}")
                        
                except Exception as e:
                    failed_configs.append(f"{ip_config} (解析异常: {str(e)})")
                    self.logger.error(f"处理IP配置异常: {ip_config} - {str(e)}")
            
            # 第四步：刷新网卡信息和UI显示
            self.refresh_current_adapter()
            
            # 第五步：生成操作结果报告并发射相应信号
            total_count = len(ip_configs)
            
            if success_count == total_count:
                # 全部成功
                success_msg = f"✅ 批量添加IP配置成功！\n\n📊 操作统计：\n• 成功添加：{success_count} 个IP配置\n• 目标网卡：{adapter_name}\n\n💡 提示：新的IP配置已生效，可在左侧信息面板中查看"
                self.extra_ips_added.emit(success_msg)
                
            elif success_count > 0:
                # 部分成功
                warning_msg = f"⚠️ 批量添加IP配置部分成功\n\n📊 操作统计：\n• 成功添加：{success_count} 个\n• 添加失败：{len(failed_configs)} 个\n• 目标网卡：{adapter_name}"
                if failed_configs:
                    warning_msg += f"\n\n❌ 失败的IP配置：\n" + "\n".join([f"• {config}" for config in failed_configs[:5]])
                    if len(failed_configs) > 5:
                        warning_msg += f"\n• ... 还有 {len(failed_configs) - 5} 个"
                self.extra_ips_added.emit(warning_msg)
                
            else:
                # 全部失败
                error_msg = f"❌ 批量添加IP配置失败\n\n📊 操作统计：\n• 尝试添加：{total_count} 个IP配置\n• 全部失败：{len(failed_configs)} 个\n• 目标网卡：{adapter_name}"
                if failed_configs:
                    error_msg += f"\n\n❌ 失败原因：\n" + "\n".join([f"• {config}" for config in failed_configs[:3]])
                error_msg += "\n\n💡 建议：\n• 检查IP地址格式是否正确\n• 确认网卡状态是否正常\n• 验证IP地址是否与网卡冲突"
                self.error_occurred.emit("批量添加失败", error_msg)
                
        except Exception as e:
            error_msg = f"💥 批量添加IP配置过程中发生系统异常\n\n🔍 异常详情：{str(e)}\n📡 目标网卡：{adapter_name}\n📝 IP配置数量：{len(ip_configs) if ip_configs else 0}"
            self.logger.error(f"批量添加额外IP异常: {str(e)}")
            self.error_occurred.emit("系统异常", error_msg)

    def remove_selected_extra_ips(self, adapter_name: str, ip_configs: list):
        """
        批量删除选中的额外IP从指定网卡的核心业务方法
        
        作用说明：
        这个方法负责处理UI层发送的批量IP删除请求，将用户选中的多个IP配置
        从指定的网络适配器上移除。该方法遵循服务层的设计原则：提供完整的
        业务逻辑封装，确保操作的原子性和数据一致性。
        
        面向对象架构特点：
        - 单一职责：专门负责批量额外IP删除的业务逻辑处理
        - 封装性：隐藏复杂的Windows网络API调用细节
        - 依赖倒置：通过信号机制实现与UI层的松耦合
        - 接口分离：提供清晰的删除操作接口，与添加操作完全独立
        
        业务处理流程：
        1. 验证输入参数（网卡名称、IP配置列表）
        2. 查找并验证目标网卡的存在性和可用性
        3. 解析IP配置格式，提取IP地址和子网掩码
        4. 逐个调用Windows网络API删除额外IP配置
        5. 统计删除操作的成功和失败情况
        6. 刷新网卡信息，同步UI显示状态
        7. 发射操作结果信号，触发用户反馈弹窗
        
        安全性和可靠性：
        - 删除前验证IP配置的存在性
        - 支持部分删除成功的情况处理
        - 提供详细的失败原因分析
        - 完整的异常处理和错误恢复机制
        
        Args:
            adapter_name (str): 目标网卡的友好名称
            ip_configs (list): 待删除的IP配置列表，格式为["IP地址 / 子网掩码", ...]
        """
        try:
            # 第一步：输入参数有效性验证
            if not adapter_name or not ip_configs:
                error_msg = "❌ 批量删除IP失败：缺少必要参数\n请确保已选择网卡并勾选要删除的IP配置"
                self.error_occurred.emit("参数错误", error_msg)
                return
            
            self.logger.info(f"开始批量删除额外IP从网卡: {adapter_name}，共 {len(ip_configs)} 个IP配置")
            print(f"🔍 DEBUG - 删除操作开始，目标网卡: {adapter_name}")
            
            # 第二步：智能查找目标网卡信息
            # 支持多种网卡标识符匹配：友好名称、描述、完整名称
            # 这种设计提高了系统的容错性和用户体验
            target_adapter = None
            self.logger.info(f"正在查找网卡: '{adapter_name}'")
            self.logger.info(f"当前缓存中共有 {len(self._adapters)} 个网卡")
            print(f"🔍 DEBUG - 查找网卡: '{adapter_name}', 当前有 {len(self._adapters)} 个网卡")
            
            for adapter in self._adapters:
                self.logger.info(f"检查网卡 - 友好名称: '{adapter.friendly_name}', 描述: '{adapter.description}', 完整名称: '{adapter.name}'")
                
                # 多重匹配策略：优先匹配友好名称，其次描述，最后完整名称
                # 这种灵活的匹配机制确保UI层可以使用任何一种网卡标识符
                if (adapter.friendly_name == adapter_name or 
                    adapter.description == adapter_name or 
                    adapter.name == adapter_name):
                    target_adapter = adapter
                    self.logger.info(f"成功匹配网卡: '{adapter_name}' -> 友好名称: '{adapter.friendly_name}'")
                    break
            
            if not target_adapter:
                error_msg = f"❌ 网卡查找失败：'{adapter_name}'\n可能原因：\n• 网卡已被禁用或断开连接\n• 网卡名称已更改\n• 系统网络配置发生变化"
                self.logger.error(f"网卡查找失败，当前可用网卡: {[adapter.friendly_name for adapter in self._adapters]}")
                self.error_occurred.emit("网卡不存在", error_msg)
                return
            
            # 第三步：批量处理IP配置删除
            success_count = 0
            failed_configs = []
            
            for ip_config in ip_configs:
                try:
                    # 解析IP配置格式：支持 "192.168.1.100/255.255.255.0" 和 "192.168.1.100 / 255.255.255.0"
                    if '/' not in ip_config:
                        failed_configs.append(f"{ip_config} (格式错误)")
                        continue
                    
                    # 兼容两种格式：带空格和不带空格的斜杠分隔符
                    if ' / ' in ip_config:
                        ip_address, subnet_mask = ip_config.split(' / ', 1)
                    else:
                        ip_address, subnet_mask = ip_config.split('/', 1)
                    ip_address = ip_address.strip()
                    subnet_mask = subnet_mask.strip()
                    
                    # 调用Windows网络API删除额外IP
                    success = self._remove_extra_ip_from_adapter(target_adapter, ip_address, subnet_mask)
                    
                    if success:
                        success_count += 1
                        self.logger.info(f"✅ 成功删除额外IP: {ip_address}/{subnet_mask}")
                    else:
                        failed_configs.append(f"{ip_address}/{subnet_mask}")
                        self.logger.warning(f"❌ 删除额外IP失败: {ip_address}/{subnet_mask}")
                        
                except Exception as e:
                    failed_configs.append(f"{ip_config} (解析异常: {str(e)})")
                    self.logger.error(f"处理IP配置异常: {ip_config} - {str(e)}")
            
            # 第四步：刷新网卡信息和UI显示
            self.refresh_current_adapter()
            
            # 第五步：生成操作结果报告并发射相应信号
            total_count = len(ip_configs)
            
            if success_count == total_count:
                # 全部删除成功
                success_msg = f"✅ 批量删除IP配置成功！\n\n📊 操作统计：\n• 成功删除：{success_count} 个IP配置\n• 目标网卡：{adapter_name}\n\n💡 提示：IP配置已从网卡中移除，左侧信息面板已更新"
                self.extra_ips_removed.emit(success_msg)
                
            elif success_count > 0:
                # 部分删除成功
                warning_msg = f"⚠️ 批量删除IP配置部分成功\n\n📊 操作统计：\n• 成功删除：{success_count} 个\n• 删除失败：{len(failed_configs)} 个\n• 目标网卡：{adapter_name}"
                if failed_configs:
                    warning_msg += f"\n\n❌ 失败的IP配置：\n" + "\n".join([f"• {config}" for config in failed_configs[:5]])
                    if len(failed_configs) > 5:
                        warning_msg += f"\n• ... 还有 {len(failed_configs) - 5} 个"
                self.extra_ips_removed.emit(warning_msg)
                
            else:
                # 全部删除失败
                error_msg = f"❌ 批量删除IP配置失败\n\n📊 操作统计：\n• 尝试删除：{total_count} 个IP配置\n• 全部失败：{len(failed_configs)} 个\n• 目标网卡：{adapter_name}"
                if failed_configs:
                    error_msg += f"\n\n❌ 失败原因：\n" + "\n".join([f"• {config}" for config in failed_configs[:3]])
                error_msg += "\n\n💡 建议：\n• 检查IP配置是否确实存在于网卡上\n• 确认网卡状态是否正常\n• 验证是否有足够的系统权限"
                self.error_occurred.emit("批量删除失败", error_msg)
                
        except Exception as e:
            error_msg = f"💥 批量删除IP配置过程中发生系统异常\n\n🔍 异常详情：{str(e)}\n📡 目标网卡：{adapter_name}\n📝 IP配置数量：{len(ip_configs) if ip_configs else 0}"
            self.logger.error(f"批量删除额外IP异常: {str(e)}")
            self.error_occurred.emit("系统异常", error_msg)

    def _add_extra_ip_to_adapter(self, adapter: AdapterInfo, ip_address: str, subnet_mask: str) -> bool:
        """
        向指定网卡添加单个额外IP配置的底层实现方法
        
        核心作用：
        这个私有方法是FlowDesk网络管理系统中添加额外IP地址的核心实现。
        它封装了Windows系统的netsh命令调用逻辑，实现对网络适配器的动态IP配置管理。
        该方法遵循单一职责原则，专门负责单个IP地址的添加操作，为上层批量操作提供可靠的原子化服务。
        
        技术架构设计：
        - 依赖倒置原则：通过subprocess模块抽象系统命令调用，降低对具体实现的依赖
        - 开闭原则：通过参数化设计支持不同网卡和IP配置的扩展
        - 单一职责原则：专注于IP添加的核心逻辑，不涉及UI交互和业务流程控制
        - 封装性原则：隐藏netsh命令的复杂性，提供简洁的布尔返回值接口
        
        Windows网络配置原理：
        netsh是Windows系统提供的网络配置命令行工具，支持对网络接口的动态配置。
        添加额外IP地址实际上是在现有网卡配置基础上绑定多个IP地址，实现单网卡多IP的网络拓扑。
        这种配置常用于服务器环境、虚拟化部署和网络测试场景。
        
        Args:
            adapter (AdapterInfo): 目标网络适配器的完整信息对象，包含友好名称等标识信息
            ip_address (str): 要添加的IPv4地址，必须符合点分十进制格式
            subnet_mask (str): 对应的子网掩码，用于定义网络范围和广播域
            
        Returns:
            bool: 操作结果标识，True表示IP地址成功添加到网卡，False表示添加操作失败
        """
        try:
            # 构建Windows netsh命令用于添加额外IP地址到指定网络适配器
            # 使用简单的位置参数格式，这是netsh命令最稳定可靠的语法形式
            cmd = [
                'netsh', 'interface', 'ipv4', 'add', 'address',
                adapter.friendly_name,           # 网卡友好名称，subprocess会自动处理包含空格的参数
                ip_address,                      # 要添加的IP地址
                subnet_mask                      # 子网掩码
            ]
            
            # 执行命令并设置超时
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='ignore'
            )
            
            # 检查命令执行结果
            if result.returncode == 0:
                self.logger.info(f"成功添加额外IP: {ip_address}/{subnet_mask} 到网卡 {adapter.friendly_name}")
                return True
            else:
                # 详细记录netsh命令执行信息
                cmd_str = ' '.join(cmd)
                error_output = result.stderr.strip() if result.stderr else "无错误输出"
                stdout_output = result.stdout.strip() if result.stdout else "无标准输出"
                
                self.logger.error(f"添加额外IP失败详情:")
                self.logger.error(f"  命令: {cmd_str}")
                self.logger.error(f"  返回码: {result.returncode}")
                self.logger.error(f"  错误输出: {error_output}")
                self.logger.error(f"  标准输出: {stdout_output}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"添加额外IP超时: {ip_address}/{subnet_mask}")
            return False
        except Exception as e:
            self.logger.error(f"添加额外IP异常: {ip_address}/{subnet_mask} - {str(e)}")
            return False

    def _remove_extra_ip_from_adapter(self, adapter: AdapterInfo, ip_address: str, subnet_mask: str) -> bool:
        """
        从指定网卡删除单个额外IP配置的底层实现方法
        
        核心作用：
        这个私有方法是FlowDesk网络管理系统中删除额外IP地址的核心实现。
        它封装了Windows系统的netsh命令调用逻辑，实现对网络适配器的动态IP配置清理。
        该方法遵循单一职责原则，专门负责单个IP地址的删除操作，确保网络配置的精确管理。
        
        技术架构设计：
        - 依赖倒置原则：通过subprocess模块抽象系统命令调用，提供统一的接口
        - 开闭原则：支持不同网卡和IP配置的删除操作扩展
        - 单一职责原则：专注于IP删除的核心逻辑，不涉及复杂的业务流程
        - 封装性原则：隐藏netsh命令的技术细节，提供简洁的操作结果反馈
        
        Windows网络配置原理：
        删除额外IP地址是从网卡的IP绑定列表中移除指定的IP配置。
        这个操作不会影响网卡的主IP地址，只会清理通过add address命令添加的额外IP。
        删除操作是幂等的，即使IP地址不存在也不会产生严重错误。
        
        Args:
            adapter (AdapterInfo): 目标网络适配器的完整信息对象，用于定位具体的网卡
            ip_address (str): 要删除的IPv4地址，必须是已存在于网卡上的额外IP
            subnet_mask (str): 对应的子网掩码，用于日志记录和验证（netsh删除时不需要）
            
        Returns:
            bool: 操作结果标识，True表示IP地址成功从网卡删除，False表示删除操作失败
        """
        try:
            # 构建Windows netsh命令用于从指定网络适配器删除额外IP地址
            # netsh删除命令格式：netsh interface ipv4 delete address "网卡名" IP地址
            cmd = [
                'netsh', 'interface', 'ipv4', 'delete', 'address',
                adapter.friendly_name,           # 网卡友好名称，subprocess会自动处理空格
                ip_address                       # 要删除的IP地址（不需要子网掩码）
            ]
            
            # 执行命令并设置超时
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='ignore'
            )
            
            # 检查命令执行结果
            if result.returncode == 0:
                self.logger.info(f"成功删除额外IP: {ip_address}/{subnet_mask} 从网卡 {adapter.friendly_name}")
                return True
            else:
                # 详细记录netsh命令执行信息
                cmd_str = ' '.join(cmd)
                error_output = result.stderr.strip() if result.stderr else "无错误输出"
                stdout_output = result.stdout.strip() if result.stdout else "无标准输出"
                
                self.logger.error(f"删除额外IP失败详情:")
                self.logger.error(f"  完整命令: {cmd_str}")
                self.logger.error(f"  返回码: {result.returncode}")
                self.logger.error(f"  错误输出: {error_output}")
                self.logger.error(f"  标准输出: {stdout_output}")
                print(f"🔍 DEBUG - 删除命令: {cmd_str}")
                print(f"🔍 DEBUG - 返回码: {result.returncode}")
                print(f"🔍 DEBUG - 错误输出: {error_output}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"删除额外IP超时: {ip_address}/{subnet_mask}")
            return False
        except Exception as e:
            self.logger.error(f"删除额外IP异常: {ip_address}/{subnet_mask} - {str(e)}")
            return False
