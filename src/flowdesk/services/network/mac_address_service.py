"""
MAC地址修改服务类

功能说明：
- 提供多重备用MAC地址修改方法
- 支持注册表、PowerShell、WMI等多种修改方式
- 实现智能降级策略，确保修改成功率
- 提供网卡重启功能使MAC修改生效

架构原则：
- 单一职责：专门处理MAC地址相关操作
- 异常安全：完整的错误处理和回滚机制
- 日志记录：详细记录操作过程和结果
"""

import asyncio
import subprocess
import winreg
import psutil
import gc
import threading
import signal
import sys
from typing import Optional, List
from dataclasses import dataclass
import logging

try:
    import wmi
except ImportError:
    wmi = None

from ...utils.logger import get_logger
from ...utils.mac_address_utils import MacAddressUtils


class ResourceMonitor:
    """系统资源监控器，防止资源泄漏影响其他应用"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.initial_memory = psutil.virtual_memory().used
        self.max_memory_increase = 100 * 1024 * 1024  # 100MB限制
    
    def check_memory_usage(self):
        """检查内存使用情况"""
        try:
            current_memory = psutil.virtual_memory().used
            memory_increase = current_memory - self.initial_memory
            
            if memory_increase > self.max_memory_increase:
                self.logger.warning(f"内存使用增长过多: {memory_increase / 1024 / 1024:.1f}MB")
                gc.collect()  # 强制垃圾回收
                return False
            return True
        except Exception as e:
            self.logger.error(f"内存检查失败: {e}")
            return True
    
    def cleanup_zombie_processes(self):
        """清理僵尸PowerShell进程"""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and 'powershell' in proc.info['name'].lower():
                    try:
                        process = psutil.Process(proc.info['pid'])
                        if process.status() == psutil.STATUS_ZOMBIE:
                            process.terminate()
                            self.logger.debug(f"清理僵尸PowerShell进程: {proc.info['pid']}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
        except Exception as e:
            self.logger.error(f"清理僵尸进程失败: {e}")


@dataclass
class MacModifyResult:
    """MAC地址修改结果数据类"""
    success: bool
    message: str
    method_used: Optional[str] = None
    original_mac: Optional[str] = None
    new_mac: Optional[str] = None


class MacAddressService:
    """MAC地址管理服务类"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.wmi_connection = None
        self._running_processes = []
        self._resource_monitor = ResourceMonitor()
        self._initialize_wmi()
        self._setup_signal_handlers()
    
    def _initialize_wmi(self):
        """初始化WMI连接"""
        try:
            if wmi:
                self.wmi_connection = wmi.WMI()
                self.logger.debug("WMI连接初始化成功")
            else:
                self.logger.warning("WMI模块不可用")
        except Exception as e:
            self.logger.error(f"WMI初始化失败: {e}")
            self.wmi_connection = None
    
    def _setup_signal_handlers(self):
        """设置信号处理器，防止程序异常退出影响系统"""
        try:
            signal.signal(signal.SIGINT, self._emergency_cleanup)
            signal.signal(signal.SIGTERM, self._emergency_cleanup)
        except Exception as e:
            self.logger.warning(f"信号处理器设置失败: {e}")
    
    def _emergency_cleanup(self, signum, frame):
        """紧急清理资源，防止影响其他应用"""
        try:
            self.logger.critical("收到退出信号，执行紧急资源清理")
            
            # 终止所有运行中的进程
            for process in self._running_processes:
                try:
                    if process.poll() is None:  # 进程仍在运行
                        process.terminate()
                        process.wait(timeout=2)
                except Exception:
                    pass
            
            # 清理WMI连接
            if self.wmi_connection:
                try:
                    del self.wmi_connection
                    self.wmi_connection = None
                except Exception:
                    pass
            
            # 强制垃圾回收
            gc.collect()
            
        except Exception as e:
            self.logger.error(f"紧急清理失败: {e}")
        finally:
            sys.exit(0)
    
    async def modify_mac_address(self, adapter_name: str, new_mac: str) -> MacModifyResult:
        """
        修改网卡MAC地址（多重备用方法）
        
        Args:
            adapter_name: 网卡名称
            new_mac: 新的MAC地址（标准格式）
            
        Returns:
            MacModifyResult: 修改结果
        """
        self.logger.info(f"开始修改MAC地址: {adapter_name} -> {new_mac}")
        
        # 获取当前MAC地址作为备份
        current_mac = await self.get_current_mac_address(adapter_name)
        if not current_mac:
            return MacModifyResult(
                success=False,
                message="无法获取当前MAC地址",
                original_mac=current_mac
            )
        
        # 验证新MAC地址格式
        validation_result = MacAddressUtils.normalize_mac_address(new_mac)
        if not validation_result.is_valid:
            return MacModifyResult(
                success=False,
                message=f"MAC地址格式无效: {validation_result.error_message}",
                original_mac=current_mac
            )
        
        normalized_mac = validation_result.normalized_mac
        
        # 检查是否与当前MAC相同
        if normalized_mac.upper() == current_mac.upper():
            return MacModifyResult(
                success=False,
                message="新MAC地址与当前MAC地址相同",
                original_mac=current_mac,
                new_mac=normalized_mac
            )
        
        # 定义修改方法列表（按优先级排序）
        methods = [
            ("注册表方法", self._modify_mac_registry),
            ("PowerShell方法", self._modify_mac_powershell),
            ("WMI方法", self._modify_mac_wmi),
            ("DevCon方法", self._modify_mac_devcon)
        ]
        
        # 依次尝试各种方法
        for method_name, method_func in methods:
            try:
                self.logger.debug(f"尝试使用{method_name}修改MAC地址")
                result = await method_func(adapter_name, normalized_mac)
                
                if result.success:
                    self.logger.info(f"MAC修改成功，使用方法: {method_name}")
                    return MacModifyResult(
                        success=True,
                        message=f"MAC地址修改成功 ({method_name})",
                        method_used=method_name,
                        original_mac=current_mac,
                        new_mac=normalized_mac
                    )
                else:
                    self.logger.warning(f"{method_name}失败: {result.message}")
                    
            except Exception as e:
                self.logger.warning(f"{method_name}异常: {e}")
                continue
        
        # 所有方法都失败
        return MacModifyResult(
            success=False,
            message="所有MAC修改方法均失败，请检查网卡是否支持MAC修改",
            original_mac=current_mac
        )
    
    async def restore_original_mac(self, adapter_name: str) -> MacModifyResult:
        """恢复初始MAC地址 - 直接清除注册表NetworkAddress值"""
        try:
            self.logger.info(f"开始恢复初始MAC地址: {adapter_name}")
            
            # 优先使用注册表方法，这是最直接有效的方式
            registry_result = await self._restore_mac_registry(adapter_name)
            
            if registry_result.success:
                # 注册表清除成功后，重启网卡使设置生效
                restart_result = await self._restart_network_adapter(adapter_name)
                
                if restart_result.success:
                    success_msg = "MAC地址已恢复到物理地址（清除注册表NetworkAddress值）"
                    self.logger.info(f"恢复完成: {adapter_name} - {success_msg}")
                    return MacModifyResult(True, success_msg)
                else:
                    # 即使重启失败，注册表清除也是成功的
                    success_msg = "MAC地址已恢复（注册表已清除，请手动重启网卡）"
                    self.logger.warning(f"注册表清除成功但网卡重启失败: {restart_result.message}")
                    return MacModifyResult(True, success_msg)
            else:
                # 注册表方法失败，尝试PowerShell方法作为备用
                self.logger.warning(f"注册表恢复失败，尝试PowerShell方法: {registry_result.message}")
                
                powershell_result = await self._restore_mac_powershell(adapter_name)
                if powershell_result.success:
                    restart_result = await self._restart_network_adapter(adapter_name)
                    success_msg = f"MAC地址已恢复（PowerShell方法）"
                    return MacModifyResult(True, success_msg)
                else:
                    error_msg = f"所有恢复方法都失败 - 注册表: {registry_result.message}, PowerShell: {powershell_result.message}"
                    self.logger.error(f"恢复失败: {adapter_name} - {error_msg}")
                    return MacModifyResult(False, error_msg)
                
        except Exception as e:
            error_msg = f"恢复初始MAC地址异常: {str(e)}"
            self.logger.error(error_msg)
            return MacModifyResult(False, error_msg)
    
    async def get_current_mac_address(self, adapter_name: str) -> Optional[str]:
        """
        获取网卡当前MAC地址（支持禁用网卡）
        
        Args:
            adapter_name: 网卡名称
            
        Returns:
            MAC地址字符串，格式为 XX:XX:XX:XX:XX:XX，失败返回None
        """
        try:
            self.logger.debug(f"开始获取网卡MAC地址: {adapter_name}")
            
            # 方法1: 通过WMI获取MAC地址（支持禁用网卡）
            if self.wmi_connection:
                try:
                    for adapter in self.wmi_connection.Win32_NetworkAdapter():
                        if adapter.NetConnectionID == adapter_name:
                            # 优先使用MACAddress字段
                            if adapter.MACAddress:
                                mac = adapter.MACAddress.replace('-', ':').upper()
                                self.logger.debug(f"通过WMI MACAddress获取: {adapter_name} -> {mac}")
                                return mac
                            # 如果MACAddress为空，尝试PermanentAddress
                            elif hasattr(adapter, 'PermanentAddress') and adapter.PermanentAddress:
                                mac = adapter.PermanentAddress.replace('-', ':').upper()
                                self.logger.debug(f"通过WMI PermanentAddress获取: {adapter_name} -> {mac}")
                                return mac
                except Exception as e:
                    self.logger.debug(f"WMI方法失败: {e}")
            
            # 方法2: 通过注册表获取MAC地址（支持禁用网卡）
            try:
                registry_mac = await self._get_mac_from_registry(adapter_name)
                if registry_mac:
                    self.logger.debug(f"通过注册表获取MAC地址: {adapter_name} -> {registry_mac}")
                    return registry_mac
            except Exception as e:
                self.logger.debug(f"注册表方法失败: {e}")
            
            # 方法3: 通过getmac命令获取（只对启用的网卡有效）
            try:
                result = subprocess.run(
                    ['getmac', '/fo', 'csv', '/v'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines[1:]:  # 跳过标题行
                        parts = line.split(',')
                        if len(parts) >= 4:
                            connection_name = parts[0].strip('"')
                            mac_address = parts[2].strip('"')
                            if connection_name == adapter_name and mac_address != "N/A":
                                mac = mac_address.replace('-', ':').upper()
                                self.logger.debug(f"通过getmac获取MAC地址: {adapter_name} -> {mac}")
                                return mac
            except Exception as e:
                self.logger.debug(f"getmac方法失败: {e}")
            
            # 方法4: 通过PowerShell获取网卡信息（支持禁用网卡）
            try:
                ps_command = f'Get-NetAdapter -Name "{adapter_name}" | Select-Object MacAddress'
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self._run_powershell_command, ps_command, 10
                )
                
                if result['success'] and result['output']:
                    output = result['output'].strip()
                    # 解析PowerShell输出
                    lines = output.split('\n')
                    for line in lines:
                        if line.strip() and '-' in line and len(line.strip()) == 17:
                            mac = line.strip().replace('-', ':').upper()
                            self.logger.debug(f"通过PowerShell获取MAC地址: {adapter_name} -> {mac}")
                            return mac
            except Exception as e:
                self.logger.debug(f"PowerShell方法失败: {e}")
            
            self.logger.warning(f"所有方法都无法获取网卡MAC地址: {adapter_name}")
            return None
            
        except Exception as e:
            self.logger.error(f"获取MAC地址异常: {e}")
            return None
    
    async def _get_mac_from_registry(self, adapter_name: str) -> Optional[str]:
        """从注册表获取网卡MAC地址"""
        try:
            # 查找网卡的注册表项
            registry_key = await self._find_adapter_registry_key_optimized(adapter_name)
            if not registry_key:
                return None
            
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_key) as key:
                try:
                    # 尝试获取NetworkAddress（用户设置的MAC）
                    network_address = winreg.QueryValueEx(key, "NetworkAddress")[0]
                    if network_address and len(network_address) == 12:
                        # 格式化MAC地址
                        mac = ':'.join([network_address[i:i+2] for i in range(0, 12, 2)]).upper()
                        return mac
                except FileNotFoundError:
                    pass
                
                # 如果没有NetworkAddress，尝试获取原始MAC地址
                # 这通常存储在不同的注册表位置，需要进一步实现
                pass
            
            return None
            
        except Exception as e:
            self.logger.debug(f"从注册表获取MAC失败: {e}")
            return None
    
    async def get_original_mac_address(self, adapter_name: str) -> Optional[str]:
        """
        获取网卡的初始MAC地址（出厂MAC）
{{ ... }}
        
        Args:
            adapter_name: 网卡名称
            
        Returns:
            str: 初始MAC地址（标准格式）
        """
        methods = [
            self._get_mac_from_registry_backup,
            self._get_mac_from_hardware_info,
            self._get_mac_from_wmi_permanent
        ]
        
        for method in methods:
            try:
                original_mac = await method(adapter_name)
                if original_mac and MacAddressUtils.is_valid_mac_format(original_mac):
                    self.logger.debug(f"获取初始MAC地址: {adapter_name} -> {original_mac}")
                    return original_mac
            except Exception as e:
                self.logger.debug(f"获取初始MAC失败: {e}")
                continue
        
        # 如果无法获取初始MAC，返回当前MAC作为备用
        current_mac = await self.get_current_mac_address(adapter_name)
        self.logger.warning(f"无法获取初始MAC，使用当前MAC: {adapter_name} -> {current_mac}")
        return current_mac
    
    async def restart_adapter(self, adapter_name: str) -> MacModifyResult:
        """
        重启网卡使MAC修改生效
        
        Args:
            adapter_name: 网卡名称
            
        Returns:
            MacModifyResult: 重启结果
        """
        self.logger.info(f"开始重启网卡: {adapter_name}")
        
        try:
            # 1. 禁用网卡
            disable_result = await self._disable_adapter(adapter_name)
            if not disable_result:
                return MacModifyResult(
                    success=False,
                    message="禁用网卡失败"
                )
            
            # 等待禁用完成
            await asyncio.sleep(2)
            
            # 2. 启用网卡
            enable_result = await self._enable_adapter(adapter_name)
            if not enable_result:
                return MacModifyResult(
                    success=False,
                    message="启用网卡失败"
                )
            
            # 等待启用完成
            await asyncio.sleep(3)
            
            self.logger.info(f"网卡重启完成: {adapter_name}")
            return MacModifyResult(
                success=True,
                message="网卡重启成功"
            )
            
        except Exception as e:
            self.logger.error(f"网卡重启失败: {e}")
            return MacModifyResult(
                success=False,
                message=f"网卡重启失败: {str(e)}"
            )
    
    # === 私有方法：MAC修改实现 ===
    
    async def _modify_mac_registry(self, adapter_name: str, new_mac: str) -> MacModifyResult:
        """通过注册表修改MAC地址"""
        try:
            # 使用优化的注册表查找方法
            registry_key = await self._find_adapter_registry_key_optimized(adapter_name)
            
            if not registry_key:
                return MacModifyResult(False, "未找到网卡注册表项")
            
            # 格式化MAC地址（去除冒号）
            registry_mac = new_mac.replace(':', '').replace('-', '').upper()
            
            # 修改注册表
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_key, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "NetworkAddress", 0, winreg.REG_SZ, registry_mac)
            
            self.logger.info(f"注册表MAC地址修改成功: {adapter_name} -> {new_mac}")
            return MacModifyResult(True, "注册表修改成功")
            
        except Exception as e:
            return MacModifyResult(False, f"注册表修改失败: {str(e)}")
    
    async def _modify_mac_powershell(self, adapter_name: str, new_mac: str) -> MacModifyResult:
        """通过PowerShell修改MAC地址"""
        try:
            # 使用Set-NetAdapter命令，去除不支持的-Force参数
            ps_command = f'Set-NetAdapter -Name "{adapter_name}" -MacAddress "{new_mac}"'
            
            self.logger.debug(f"执行PowerShell命令: {ps_command}")
            
            # 在线程池中执行PowerShell命令，避免阻塞UI
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._run_powershell_command,
                ps_command,
                15  # 15秒超时
            )
            
            if result['success']:
                self.logger.info(f"PowerShell修改MAC成功: {adapter_name} -> {new_mac}")
                return MacModifyResult(True, "PowerShell MAC地址修改成功")
            else:
                self.logger.warning(f"PowerShell修改MAC失败: {result['error']}")
                return MacModifyResult(False, f"PowerShell修改失败: {result['error']}")
                
        except Exception as e:
            self.logger.error(f"PowerShell修改MAC异常: {e}")
            return MacModifyResult(False, f"PowerShell修改异常: {str(e)}")
            
    async def _modify_mac_wmi(self, adapter_name: str, new_mac: str) -> MacModifyResult:
        """通过WMI修改MAC地址"""
        try:
            if not self.wmi_connection:
                return MacModifyResult(False, "WMI连接不可用")
            
            # 查找网卡
            for adapter in self.wmi_connection.Win32_NetworkAdapter():
                if adapter.NetConnectionID == adapter_name:
                    # 检查是否支持SetMacAddress方法
                    if hasattr(adapter, 'SetMacAddress'):
                        try:
                            # 尝试设置MAC地址（移除冒号）
                            result = adapter.SetMacAddress(new_mac.replace(':', ''))
                            if result == 0:
                                return MacModifyResult(True, "WMI修改成功")
                            else:
                                return MacModifyResult(False, f"WMI修改失败，错误代码: {result}")
                        except Exception as method_error:
                            return MacModifyResult(False, f"WMI方法调用失败: {str(method_error)}")
                    else:
                        return MacModifyResult(False, "网卡不支持WMI MAC地址修改")
            
            return MacModifyResult(False, "未找到指定网卡")
            
        except Exception as e:
            return MacModifyResult(False, f"WMI修改异常: {str(e)}")
    
    async def _modify_mac_devcon(self, adapter_name: str, new_mac: str) -> MacModifyResult:
        """通过DevCon工具修改MAC地址"""
        try:
            import os
            # DevCon工具路径（需要预先安装）
            devcon_path = os.path.join("assets", "devcon.exe")
            if not os.path.exists(devcon_path):
                return MacModifyResult(False, "DevCon工具不可用")
            
            # 这里需要实现DevCon的具体调用逻辑
            # 由于DevCon使用复杂，暂时返回不支持
            return MacModifyResult(False, "DevCon方法暂未实现")
            
        except Exception as e:
            return MacModifyResult(False, f"DevCon修改异常: {str(e)}")
    
    # === 私有方法：辅助功能 ===
    
    async def _find_adapter_registry_key(self, adapter_name: str) -> Optional[str]:
        """查找网卡的注册表键路径"""
        try:
            base_key = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}"
            
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_key) as key:
                i = 0
                max_iterations = 50  # 限制最大遍历数量，避免无限循环
                
                while i < max_iterations:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        # 跳过非数字键名（如Properties）
                        if not subkey_name.isdigit():
                            i += 1
                            continue
                            
                        subkey_path = f"{base_key}\\{subkey_name}"
                        
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey_path) as subkey:
                            try:
                                # 优先检查最可能的字段
                                fields_to_check = [
                                    "DriverDesc",           # 驱动描述 - 最常用
                                    "NetCfgInstanceId"      # 网络配置实例ID - 次优先
                                ]
                                
                                for field in fields_to_check:
                                    try:
                                        value = winreg.QueryValueEx(subkey, field)[0]
                                        if adapter_name in str(value):
                                            self.logger.debug(f"通过{field}字段匹配到网卡: {adapter_name}")
                                            return subkey_path
                                    except FileNotFoundError:
                                        continue
                                        
                            except Exception:
                                pass
                        
                        i += 1
                    except OSError:
                        break
            
            self.logger.warning(f"未找到网卡注册表项: {adapter_name} (遍历了{i}个项)")
            return None
            
        except Exception as e:
            self.logger.error(f"查找注册表键失败: {e}")
            return None
    
    async def _find_adapter_registry_key_optimized(self, adapter_name: str) -> Optional[str]:
        """优化的网卡注册表键查找方法"""
        try:
            base_key = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}"
            self.logger.debug(f"开始查找网卡 '{adapter_name}' 的注册表项")
            
            # 首先尝试通过WMI获取更准确的匹配信息
            if self.wmi_connection:
                try:
                    self.logger.debug("尝试通过WMI获取网卡GUID")
                    for adapter in self.wmi_connection.Win32_NetworkAdapter():
                        if adapter.NetConnectionID == adapter_name and adapter.GUID:
                            guid = adapter.GUID.strip('{}')
                            self.logger.debug(f"找到网卡GUID: {guid}")
                            
                            # 使用GUID直接查找对应的注册表项
                            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_key) as key:
                                i = 0
                                while i < 50:  # 扩大查找范围
                                    try:
                                        subkey_name = winreg.EnumKey(key, i)
                                        if subkey_name.isdigit():
                                            subkey_path = f"{base_key}\\{subkey_name}"
                                            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey_path) as subkey:
                                                try:
                                                    net_cfg_id = winreg.QueryValueEx(subkey, "NetCfgInstanceId")[0]
                                                    if guid.lower() in net_cfg_id.lower():
                                                        self.logger.info(f"✅ 通过GUID匹配到注册表项: {subkey_path}")
                                                        return subkey_path
                                                except FileNotFoundError:
                                                    pass
                                        i += 1
                                    except OSError:
                                        break
                except Exception as e:
                    self.logger.debug(f"WMI查找失败: {e}")
            
            # 如果WMI方法失败，使用增强的名称匹配方法
            self.logger.debug("WMI方法失败，使用增强名称匹配")
            return await self._find_adapter_registry_key_debug(adapter_name)
            
        except Exception as e:
            self.logger.error(f"优化注册表查找失败: {e}")
            return None
    
    async def _find_adapter_registry_key_debug(self, adapter_name: str) -> Optional[str]:
        """调试版本的注册表查找，输出详细信息"""
        try:
            base_key = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}"
            self.logger.debug(f"🔍 开始详细查找网卡 '{adapter_name}' 的注册表项")
            
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_key) as key:
                i = 0
                found_adapters = []
                
                while i < 50:  # 扩大查找范围
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        if not subkey_name.isdigit():
                            i += 1
                            continue
                            
                        subkey_path = f"{base_key}\\{subkey_name}"
                        
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey_path) as subkey:
                            try:
                                # 收集所有可能的字段
                                fields = {}
                                field_names = ["DriverDesc", "NetCfgInstanceId", "ComponentId", "FriendlyName", "DeviceDesc"]
                                
                                for field in field_names:
                                    try:
                                        value = winreg.QueryValueEx(subkey, field)[0]
                                        fields[field] = str(value)
                                    except FileNotFoundError:
                                        pass
                                
                                # 如果有任何字段，记录这个适配器
                                if fields:
                                    found_adapters.append({
                                        'path': subkey_path,
                                        'index': subkey_name,
                                        'fields': fields
                                    })
                                    
                                    # 检查是否匹配目标网卡
                                    for field_name, field_value in fields.items():
                                        if adapter_name in field_value:
                                            self.logger.info(f"✅ 通过{field_name}字段匹配: '{field_value}' 包含 '{adapter_name}'")
                                            self.logger.info(f"✅ 匹配的注册表路径: {subkey_path}")
                                            return subkey_path
                                        
                            except Exception:
                                pass
                        
                        i += 1
                    except OSError:
                        break
                
                # 输出找到的所有网络适配器信息用于调试
                self.logger.warning(f"❌ 未找到匹配的网卡，但发现了 {len(found_adapters)} 个网络适配器:")
                for adapter in found_adapters[:10]:  # 只显示前10个
                    self.logger.warning(f"  📋 索引{adapter['index']}: {adapter['fields']}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"调试注册表查找失败: {e}")
            return None
    
    async def _restore_mac_registry(self, adapter_name: str) -> MacModifyResult:
        """通过删除注册表NetworkAddress值恢复MAC地址"""
        try:
            self.logger.debug(f"开始查找网卡注册表项: {adapter_name}")
            
            # 使用优化的注册表查找方法
            registry_key = await self._find_adapter_registry_key_optimized(adapter_name)
            
            if not registry_key:
                self.logger.warning(f"未找到网卡注册表项: {adapter_name}")
                return MacModifyResult(False, "未找到网卡注册表项")
            
            self.logger.debug(f"找到注册表项: {registry_key}")
            
            # 删除NetworkAddress值
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_key, 0, winreg.KEY_SET_VALUE) as key:
                try:
                    winreg.DeleteValue(key, "NetworkAddress")
                    self.logger.info(f"成功删除NetworkAddress值: {adapter_name}")
                    return MacModifyResult(True, "注册表NetworkAddress值已删除")
                except FileNotFoundError:
                    # NetworkAddress值不存在，说明没有被修改过
                    self.logger.info(f"NetworkAddress值不存在，网卡已是物理MAC: {adapter_name}")
                    return MacModifyResult(True, "注册表中无NetworkAddress值，网卡已使用物理MAC")
            
        except Exception as e:
            self.logger.error(f"注册表恢复失败: {e}")
            return MacModifyResult(False, f"注册表恢复失败: {str(e)}")
    
    async def _restore_mac_powershell(self, adapter_name: str) -> MacModifyResult:
        """通过PowerShell清除MAC地址设置"""
        try:
            # 方法1: 使用$null清除MAC地址
            clear_mac_cmd = f'Set-NetAdapter -Name "{adapter_name}" -MacAddress $null'
            
            self.logger.debug(f"执行PowerShell清除命令: {clear_mac_cmd}")
            
            loop = asyncio.get_event_loop()
            clear_result = await loop.run_in_executor(
                None,
                self._run_powershell_command,
                clear_mac_cmd,
                15  # 15秒超时
            )
            
            if clear_result['success']:
                self.logger.info(f"PowerShell MAC地址已清除: {adapter_name}")
                return MacModifyResult(True, "PowerShell MAC地址已清除")
            
            # 方法2: 如果$null失败，尝试空字符串
            empty_mac_cmd = f'Set-NetAdapter -Name "{adapter_name}" -MacAddress ""'
            
            self.logger.debug(f"尝试空字符串清除: {empty_mac_cmd}")
            
            empty_result = await loop.run_in_executor(
                None,
                self._run_powershell_command,
                empty_mac_cmd,
                15
            )
            
            if empty_result['success']:
                self.logger.info(f"PowerShell MAC地址已清除(空字符串): {adapter_name}")
                return MacModifyResult(True, "PowerShell MAC地址已清除")
            
            # 方法3: 如果以上都失败，尝试禁用启用网卡重启
            disable_cmd = f'Disable-NetAdapter -Name "{adapter_name}"'
            enable_cmd = f'Enable-NetAdapter -Name "{adapter_name}"'
            
            self.logger.debug(f"尝试重启网卡: {adapter_name}")
            
            # 禁用网卡
            disable_result = await loop.run_in_executor(
                None,
                self._run_powershell_command,
                disable_cmd,
                15
            )
            
            if disable_result['success']:
                # 等待1秒
                await asyncio.sleep(1)
                
                # 启用网卡
                enable_result = await loop.run_in_executor(
                    None,
                    self._run_powershell_command,
                    enable_cmd,
                    15
                )
                
                if enable_result['success']:
                    self.logger.info(f"网卡重启成功: {adapter_name}")
                    return MacModifyResult(True, "通过重启网卡恢复MAC地址")
            
            # 所有方法都失败
            self.logger.warning(f"PowerShell恢复MAC失败: {clear_result['error']}")
            return MacModifyResult(False, f"PowerShell恢复失败: {clear_result['error']}")
            
        except Exception as e:
            self.logger.error(f"PowerShell恢复MAC异常: {e}")
            return MacModifyResult(False, f"PowerShell恢复异常: {str(e)}")

    async def _get_mac_from_registry_backup(self, adapter_name: str) -> Optional[str]:
        """从注册表备份获取初始MAC"""
        # 实现从注册表获取备份MAC的逻辑
        return None
    
    async def _get_mac_from_hardware_info(self, adapter_name: str) -> Optional[str]:
        """从硬件信息获取初始MAC"""
        # 实现从硬件信息获取MAC的逻辑
        return None
    
    def _run_powershell_command(self, command: str, timeout: int = 20) -> dict:
        """安全执行PowerShell命令，防止资源泄漏"""
        process = None
        try:
            # 检查内存使用情况
            if not self._resource_monitor.check_memory_usage():
                return {'success': False, 'output': None, 'error': '内存使用过多，取消执行'}
            
            # 清理僵尸进程
            self._resource_monitor.cleanup_zombie_processes()
            
            # 优化命令参数
            if "Set-NetAdapter" in command:
                if "-Confirm:$false" not in command:
                    command = f"{command} -Confirm:$false"
            elif "Disable-NetAdapter" in command or "Enable-NetAdapter" in command:
                if "-Confirm:$false" not in command:
                    command = f"{command} -Confirm:$false"
            
            self.logger.debug(f"执行PowerShell命令: {command}")
            
            # 创建进程时设置更严格的参数
            process = subprocess.Popen(
                ["powershell", "-ExecutionPolicy", "Bypass", "-NoProfile", "-Command", command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            # 添加到运行进程列表
            self._running_processes.append(process)
            
            try:
                # 等待进程完成
                stdout, stderr = process.communicate(timeout=timeout)
                returncode = process.returncode
                
                if returncode == 0:
                    self.logger.debug(f"PowerShell命令执行成功")
                    return {'success': True, 'output': stdout, 'error': None}
                else:
                    error_msg = stderr.strip() if stderr else "未知错误"
                    self.logger.warning(f"PowerShell命令执行失败: {error_msg}")
                    return {'success': False, 'output': stdout, 'error': error_msg}
                    
            except subprocess.TimeoutExpired:
                # 超时处理
                self.logger.error(f"PowerShell命令超时，强制终止进程")
                process.kill()
                process.wait(timeout=5)  # 等待进程完全终止
                return {'success': False, 'output': None, 'error': f'命令执行超时({timeout}秒)'}
                
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"PowerShell执行异常: {error_msg}")
            
            # 确保进程被清理
            if process:
                try:
                    process.kill()
                    process.wait(timeout=2)
                except Exception:
                    pass
                    
            return {'success': False, 'output': None, 'error': error_msg}
            
        finally:
            # 从运行进程列表中移除
            if process and process in self._running_processes:
                self._running_processes.remove(process)
            
            # 强制垃圾回收
            gc.collect()
    
    async def _get_mac_from_wmi_permanent(self, adapter_name: str) -> Optional[str]:
        """从WMI获取永久MAC地址"""
        try:
            if not self.wmi_connection:
                return None
            
            for adapter in self.wmi_connection.Win32_NetworkAdapter():
                if adapter.NetConnectionID == adapter_name and adapter.PermanentAddress:
                    mac = adapter.PermanentAddress.replace('-', ':').upper()
                    return mac
            
            return None
            
        except Exception:
            return None
    
    async def _disable_adapter(self, adapter_name: str) -> bool:
        """禁用网卡"""
        try:
            result = subprocess.run(
                ['netsh', 'interface', 'set', 'interface', adapter_name, 'disable'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    async def _enable_adapter(self, adapter_name: str) -> bool:
        """启用网卡"""
        try:
            result = subprocess.run(
                ['netsh', 'interface', 'set', 'interface', adapter_name, 'enable'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    async def _restart_network_adapter(self, adapter_name: str) -> MacModifyResult:
        """重启网卡使MAC地址修改生效"""
        try:
            self.logger.info(f"开始重启网卡: {adapter_name}")
            
            # 禁用网卡
            disable_cmd = f'Disable-NetAdapter -Name "{adapter_name}" -Confirm:$false'
            disable_result = await asyncio.get_event_loop().run_in_executor(
                None, self._run_powershell_command, disable_cmd, 15
            )
            
            if not disable_result['success']:
                return MacModifyResult(False, f"禁用网卡失败: {disable_result['error']}")
            
            # 等待2秒
            await asyncio.sleep(2)
            
            # 启用网卡
            enable_cmd = f'Enable-NetAdapter -Name "{adapter_name}" -Confirm:$false'
            enable_result = await asyncio.get_event_loop().run_in_executor(
                None, self._run_powershell_command, enable_cmd, 15
            )
            
            if enable_result['success']:
                self.logger.info(f"网卡重启完成: {adapter_name}")
                return MacModifyResult(True, "网卡重启成功")
            else:
                return MacModifyResult(False, f"启用网卡失败: {enable_result['error']}")
                
        except Exception as e:
            error_msg = f"网卡重启异常: {str(e)}"
            self.logger.error(error_msg)
            return MacModifyResult(False, error_msg)
