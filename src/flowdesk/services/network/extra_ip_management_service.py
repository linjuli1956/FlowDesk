# -*- coding: utf-8 -*-
"""
额外IP管理专用服务模块

这个文件在FlowDesk网络管理架构中扮演"额外IP管理器"角色，专门负责网络适配器的额外IP地址管理功能。
它解决了多IP配置的批量操作、复杂的Windows netsh命令调用和操作状态跟踪的问题，通过标准化的API封装确保额外IP的准确添加和删除。
UI层依赖此服务实现网卡的多IP配置功能，其他服务通过此模块执行IP地址的动态管理操作。
该服务严格遵循单一职责原则，将额外IP管理逻辑完全独立封装。
"""

import subprocess
from typing import List, Dict, Any

from .network_service_base import NetworkServiceBase


class ExtraIPManagementService(NetworkServiceBase):
    """
    额外IP管理服务
    
    专门负责网络适配器额外IP地址管理的核心服务。
    此服务封装了复杂的多IP配置逻辑，提供批量操作和单个操作的统一接口。
    
    主要功能：
    - 批量添加选中的额外IP配置到指定网卡
    - 批量删除选中的额外IP配置从指定网卡
    - 提供单个IP地址的添加和删除底层操作
    - 实现操作结果的详细统计和用户反馈
    """
    
    def __init__(self, parent=None):
        """
        初始化额外IP管理服务
        
        Args:
            parent: PyQt父对象，用于内存管理
        """
        super().__init__(parent)
        self._log_operation_start("ExtraIPManagementService初始化")
        
        # 存储网卡信息的缓存，需要从adapter_discovery_service获取
        self._adapters = []
    
    # region 公开接口方法
    
    def add_selected_extra_ips(self, adapter_name: str, ip_configs: List[str]):
        """
        批量添加选中的额外IP到指定网卡的核心业务方法
        
        这个方法是FlowDesk网络管理系统中批量IP配置添加的核心入口点。
        它负责将用户在界面上选择的多个IP配置，通过Windows系统API批量添加到指定的网络适配器上。
        
        Args:
            adapter_name (str): 目标网络适配器的友好名称
            ip_configs (List[str]): IP配置字符串列表，格式为"IP地址 / 子网掩码"
        """
        try:
            # 第一步：输入参数验证
            if not adapter_name or not ip_configs:
                error_msg = "❌ 批量添加IP失败：缺少必要参数\n请确保已选择网卡并勾选要添加的IP配置"
                self.error_occurred.emit("参数错误", error_msg)
                return
            
            self._log_operation_start("批量添加额外IP", adapter_name=adapter_name, count=len(ip_configs))
            
            # 第二步：智能查找目标网卡信息
            target_adapter = self._find_target_adapter(adapter_name)
            if not target_adapter:
                error_msg = f"❌ 网卡查找失败：'{adapter_name}'\n可能原因：\n• 网卡已被禁用或断开连接\n• 网卡名称已更改\n• 系统网络配置发生变化"
                self.error_occurred.emit("网卡不存在", error_msg)
                return
            
            # 第三步：批量处理IP配置添加
            success_count = 0
            failed_configs = []
            
            for ip_config in ip_configs:
                try:
                    # 解析IP配置格式
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
            
            # 第四步：生成操作结果报告并发射相应信号
            total_count = len(ip_configs)
            
            if success_count == total_count:
                # 全部成功
                success_msg = f"✅ 批量添加IP配置成功！\n\n📊 操作统计：\n• 成功添加：{success_count} 个IP配置\n• 目标网卡：{adapter_name}\n\n💡 提示：新的IP配置已生效"
                self._log_operation_success("批量添加额外IP", f"成功添加{success_count}个IP")
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
            self._log_operation_error("批量添加额外IP", e)
            error_msg = f"💥 批量添加IP配置过程中发生系统异常\n\n🔍 异常详情：{str(e)}\n📡 目标网卡：{adapter_name}"
            self.error_occurred.emit("系统异常", error_msg)

    def remove_selected_extra_ips(self, adapter_name: str, ip_configs: List[str]):
        """
        批量删除选中的额外IP从指定网卡的核心业务方法
        
        Args:
            adapter_name (str): 目标网卡的友好名称
            ip_configs (List[str]): 待删除的IP配置列表，格式为["IP地址 / 子网掩码", ...]
        """
        try:
            # 第一步：输入参数有效性验证
            if not adapter_name or not ip_configs:
                error_msg = "❌ 批量删除IP失败：缺少必要参数\n请确保已选择网卡并勾选要删除的IP配置"
                self.error_occurred.emit("参数错误", error_msg)
                return
            
            self._log_operation_start("批量删除额外IP", adapter_name=adapter_name, count=len(ip_configs))
            
            # 第二步：智能查找目标网卡信息
            target_adapter = self._find_target_adapter(adapter_name)
            if not target_adapter:
                error_msg = f"❌ 网卡查找失败：'{adapter_name}'\n可能原因：\n• 网卡已被禁用或断开连接\n• 网卡名称已更改\n• 系统网络配置发生变化"
                self.error_occurred.emit("网卡不存在", error_msg)
                return
            
            # 第三步：批量处理IP配置删除
            success_count = 0
            failed_configs = []
            
            for ip_config in ip_configs:
                try:
                    # 解析IP配置格式
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
            
            # 第四步：生成操作结果报告并发射相应信号
            total_count = len(ip_configs)
            
            if success_count == total_count:
                # 全部删除成功
                success_msg = f"✅ 批量删除IP配置成功！\n\n📊 操作统计：\n• 成功删除：{success_count} 个IP配置\n• 目标网卡：{adapter_name}\n\n💡 提示：IP配置已从网卡中移除"
                self._log_operation_success("批量删除额外IP", f"成功删除{success_count}个IP")
                self.extra_ips_removed.emit(success_msg)
                
            elif success_count > 0:
                # 部分删除成功
                warning_msg = f"⚠️ 批量删除IP配置部分成功\n\n📊 操作统计：\n• 成功删除：{success_count} 个\n• 删除失败：{len(failed_configs)} 个\n• 目标网卡：{adapter_name}"
                if failed_configs:
                    warning_msg += f"\n\n❌ 失败的IP配置：\n" + "\n".join([f"• {config}" for config in failed_configs[:5]])
                self.extra_ips_removed.emit(warning_msg)
                
            else:
                # 全部删除失败
                error_msg = f"❌ 批量删除IP配置失败\n\n📊 操作统计：\n• 尝试删除：{total_count} 个IP配置\n• 全部失败：{len(failed_configs)} 个\n• 目标网卡：{adapter_name}"
                if failed_configs:
                    error_msg += f"\n\n❌ 失败原因：\n" + "\n".join([f"• {config}" for config in failed_configs[:3]])
                error_msg += "\n\n💡 建议：\n• 检查IP配置是否确实存在于网卡上\n• 确认网卡状态是否正常\n• 验证是否有足够的系统权限"
                self.error_occurred.emit("批量删除失败", error_msg)
                
        except Exception as e:
            self._log_operation_error("批量删除额外IP", e)
            error_msg = f"💥 批量删除IP配置过程中发生系统异常\n\n🔍 异常详情：{str(e)}\n📡 目标网卡：{adapter_name}"
            self.error_occurred.emit("系统异常", error_msg)
    
    def set_adapters_cache(self, adapters: List[Dict[str, Any]]):
        """
        设置网卡信息缓存
        
        Args:
            adapters: 网卡信息列表，每个元素包含网卡的基本信息
        """
        self._adapters = adapters
        self.logger.info(f"更新网卡信息缓存，共 {len(adapters)} 个网卡")
    
    # endregion
    
    # region 私有实现方法
    
    def _find_target_adapter(self, adapter_name: str) -> Dict[str, Any]:
        """
        智能查找目标网卡信息
        
        Args:
            adapter_name: 网卡名称标识符
            
        Returns:
            Dict[str, Any]: 匹配的网卡信息，未找到返回None
        """
        self.logger.info(f"正在查找网卡: '{adapter_name}'")
        
        for adapter in self._adapters:
            # 处理AdapterInfo对象和字典两种格式
            if hasattr(adapter, 'friendly_name'):
                # AdapterInfo对象格式
                if (adapter.friendly_name == adapter_name or 
                    adapter.description == adapter_name or 
                    adapter.name == adapter_name):
                    self.logger.info(f"成功匹配网卡: '{adapter_name}' -> 友好名称: '{adapter.friendly_name}'")
                    return adapter
            else:
                # 字典格式（向后兼容）
                if (adapter.get('friendly_name') == adapter_name or 
                    adapter.get('description') == adapter_name or 
                    adapter.get('name') == adapter_name):
                    self.logger.info(f"成功匹配网卡: '{adapter_name}' -> 友好名称: '{adapter.get('friendly_name')}'")
                    return adapter
        
        return None
    
    def _add_extra_ip_to_adapter(self, adapter: Dict[str, Any], ip_address: str, subnet_mask: str) -> bool:
        """
        向指定网卡添加单个额外IP配置的底层实现方法
        
        Args:
            adapter: 目标网络适配器的信息
            ip_address: 要添加的IPv4地址
            subnet_mask: 对应的子网掩码
            
        Returns:
            bool: 操作结果，True表示成功，False表示失败
        """
        try:
            # 构建Windows netsh命令用于添加额外IP地址
            # 处理AdapterInfo对象和字典两种格式
            if hasattr(adapter, 'friendly_name'):
                adapter_friendly_name = adapter.friendly_name
            else:
                adapter_friendly_name = adapter.get('friendly_name', '')
                
            cmd = [
                'netsh', 'interface', 'ipv4', 'add', 'address',
                adapter_friendly_name, ip_address, subnet_mask
            ]
            
            # 执行命令并设置超时
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
                encoding='utf-8', errors='ignore'
            )
            
            # 检查命令执行结果
            if result.returncode == 0:
                self.logger.info(f"成功添加额外IP: {ip_address}/{subnet_mask} 到网卡 {adapter_friendly_name}")
                return True
            else:
                # 详细记录netsh命令执行信息
                cmd_str = ' '.join(cmd)
                error_output = result.stderr.strip() if result.stderr else "无错误输出"
                
                self.logger.error(f"添加额外IP失败:")
                self.logger.error(f"  命令: {cmd_str}")
                self.logger.error(f"  返回码: {result.returncode}")
                self.logger.error(f"  错误输出: {error_output}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"添加额外IP超时: {ip_address}/{subnet_mask}")
            return False
        except Exception as e:
            self.logger.error(f"添加额外IP异常: {ip_address}/{subnet_mask} - {str(e)}")
            return False

    def _remove_extra_ip_from_adapter(self, adapter: Dict[str, Any], ip_address: str, subnet_mask: str) -> bool:
        """
        从指定网卡删除单个额外IP配置的底层实现方法
        
        Args:
            adapter: 目标网络适配器的信息
            ip_address: 要删除的IPv4地址
            subnet_mask: 对应的子网掩码（用于日志记录）
            
        Returns:
            bool: 操作结果，True表示成功，False表示失败
        """
        try:
            # 构建Windows netsh命令用于从指定网络适配器删除额外IP地址
            # 处理AdapterInfo对象和字典两种格式
            if hasattr(adapter, 'friendly_name'):
                adapter_friendly_name = adapter.friendly_name
            else:
                adapter_friendly_name = adapter.get('friendly_name', '')
                
            cmd = [
                'netsh', 'interface', 'ipv4', 'delete', 'address',
                adapter_friendly_name, ip_address  # 删除时不需要子网掩码
            ]
            
            # 执行命令并设置超时
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
                encoding='utf-8', errors='ignore'
            )
            
            # 检查命令执行结果
            if result.returncode == 0:
                self.logger.info(f"成功删除额外IP: {ip_address}/{subnet_mask} 从网卡 {adapter_friendly_name}")
                return True
            else:
                # 详细记录netsh命令执行信息
                cmd_str = ' '.join(cmd)
                error_output = result.stderr.strip() if result.stderr else "无错误输出"
                
                self.logger.error(f"删除额外IP失败:")
                self.logger.error(f"  完整命令: {cmd_str}")
                self.logger.error(f"  返回码: {result.returncode}")
                self.logger.error(f"  错误输出: {error_output}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"删除额外IP超时: {ip_address}/{subnet_mask}")
            return False
        except Exception as e:
            self.logger.error(f"删除额外IP异常: {ip_address}/{subnet_mask} - {str(e)}")
            return False
    
    # endregion
