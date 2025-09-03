"""
MAC地址格式处理工具类

功能说明：
- 支持多种MAC地址输入格式的标准化处理
- 提供MAC地址格式验证和转换功能
- 遵循项目架构规范，提供纯工具函数

支持的输入格式：
1. 00:1A:2B:3C:4D:5E (冒号分隔)
2. 00-1A-2B-3C-4D-5E (连字符分隔)  
3. 001A-2B3C-4D5E (三组两段)
4. 001A2B3C4D5E (无分隔连续)

架构原则：
- 单一职责：专门处理MAC地址格式相关操作
- 无副作用：纯函数设计，不修改外部状态
- 异常安全：提供详细的错误信息和异常处理
"""

import re
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class MacValidationResult:
    """MAC地址验证结果数据类"""
    is_valid: bool
    normalized_mac: Optional[str] = None
    error_message: Optional[str] = None
    original_format: Optional[str] = None


class MacAddressUtils:
    """MAC地址格式处理工具类"""
    
    # MAC地址格式正则表达式模式
    MAC_PATTERNS = {
        'colon': r'^([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2})$',           # 00:1A:2B:3C:4D:5E
        'dash': r'^([0-9A-Fa-f]{2}[-]){5}([0-9A-Fa-f]{2})$',            # 00-1A-2B-3C-4D-5E
        'three_groups': r'^([0-9A-Fa-f]{4}[-]){2}([0-9A-Fa-f]{4})$',    # 001A-2B3C-4D5E
        'continuous': r'^[0-9A-Fa-f]{12}$'                               # 001A2B3C4D5E
    }
    
    @staticmethod
    def normalize_mac_address(mac_input: str) -> MacValidationResult:
        """
        标准化MAC地址格式
        
        Args:
            mac_input: 用户输入的MAC地址字符串
            
        Returns:
            MacValidationResult: 包含验证结果和标准化MAC地址
        """
        if not mac_input or not isinstance(mac_input, str):
            return MacValidationResult(
                is_valid=False,
                error_message="MAC地址不能为空"
            )
        
        # 去除首尾空格并转换为大写
        mac_clean = mac_input.strip().upper()
        
        # 检测输入格式并获取原始格式类型
        original_format = MacAddressUtils._detect_mac_format(mac_clean)
        if not original_format:
            return MacValidationResult(
                is_valid=False,
                error_message="不支持的MAC地址格式，请使用以下格式之一：\n"
                            "• 00:1A:2B:3C:4D:5E (冒号分隔)\n"
                            "• 00-1A-2B-3C-4D-5E (连字符分隔)\n"
                            "• 001A-2B3C-4D5E (三组两段)\n"
                            "• 001A2B3C4D5E (连续12位)",
                original_format=original_format
            )
        
        try:
            # 移除所有分隔符，获取纯净的12位十六进制字符串
            clean_mac = re.sub(r'[:-]', '', mac_clean)
            
            # 验证长度和字符有效性
            if len(clean_mac) != 12:
                return MacValidationResult(
                    is_valid=False,
                    error_message=f"MAC地址长度错误，应为12位十六进制字符，当前为{len(clean_mac)}位",
                    original_format=original_format
                )
            
            if not re.match(r'^[0-9A-F]{12}$', clean_mac):
                return MacValidationResult(
                    is_valid=False,
                    error_message="MAC地址包含无效字符，只能包含0-9和A-F",
                    original_format=original_format
                )
            
            # 检查是否为广播地址或多播地址
            if clean_mac == 'FFFFFFFFFFFF':
                return MacValidationResult(
                    is_valid=False,
                    error_message="不能使用广播MAC地址 (FF:FF:FF:FF:FF:FF)",
                    original_format=original_format
                )
            
            if clean_mac == '000000000000':
                return MacValidationResult(
                    is_valid=False,
                    error_message="不能使用全零MAC地址 (00:00:00:00:00:00)",
                    original_format=original_format
                )
            
            # 检查是否为多播地址（第一个字节的最低位为1）
            first_byte = int(clean_mac[:2], 16)
            if first_byte & 1:
                return MacValidationResult(
                    is_valid=False,
                    error_message="不能使用多播MAC地址（第一个字节必须为偶数）",
                    original_format=original_format
                )
            
            # 转换为标准格式（冒号分隔）
            normalized_mac = ':'.join([clean_mac[i:i+2] for i in range(0, 12, 2)])
            
            return MacValidationResult(
                is_valid=True,
                normalized_mac=normalized_mac,
                original_format=original_format
            )
            
        except Exception as e:
            return MacValidationResult(
                is_valid=False,
                error_message=f"MAC地址格式处理失败: {str(e)}",
                original_format=original_format
            )
    
    @staticmethod
    def _detect_mac_format(mac_address: str) -> Optional[str]:
        """
        检测MAC地址的输入格式类型
        
        Args:
            mac_address: 待检测的MAC地址字符串
            
        Returns:
            str: 格式类型名称，如果不匹配任何格式则返回None
        """
        for format_name, pattern in MacAddressUtils.MAC_PATTERNS.items():
            if re.match(pattern, mac_address):
                return format_name
        return None
    
    @staticmethod
    def format_mac_for_display(mac_address: str, format_type: str = 'colon') -> str:
        """
        将MAC地址格式化为指定显示格式
        
        Args:
            mac_address: 标准化的MAC地址（冒号分隔格式）
            format_type: 目标格式类型 ('colon', 'dash', 'three_groups', 'continuous')
            
        Returns:
            str: 格式化后的MAC地址字符串
        """
        if not mac_address:
            return ""
        
        # 移除分隔符获取纯净字符串
        clean_mac = re.sub(r'[:-]', '', mac_address.upper())
        
        if format_type == 'colon':
            return ':'.join([clean_mac[i:i+2] for i in range(0, 12, 2)])
        elif format_type == 'dash':
            return '-'.join([clean_mac[i:i+2] for i in range(0, 12, 2)])
        elif format_type == 'three_groups':
            return f"{clean_mac[:4]}-{clean_mac[4:8]}-{clean_mac[8:]}"
        elif format_type == 'continuous':
            return clean_mac
        else:
            # 默认返回冒号分隔格式
            return ':'.join([clean_mac[i:i+2] for i in range(0, 12, 2)])
    
    @staticmethod
    def is_valid_mac_format(mac_address: str) -> bool:
        """
        快速检查MAC地址格式是否有效
        
        Args:
            mac_address: 待检查的MAC地址字符串
            
        Returns:
            bool: 格式是否有效
        """
        result = MacAddressUtils.normalize_mac_address(mac_address)
        return result.is_valid
    
    @staticmethod
    def generate_random_mac() -> str:
        """
        生成随机的本地管理MAC地址
        
        Returns:
            str: 随机生成的MAC地址（冒号分隔格式）
        """
        import random
        
        # 生成本地管理的MAC地址（第一个字节的第二位设为1）
        # 这确保生成的MAC地址不会与厂商分配的地址冲突
        first_byte = random.randint(0, 255) | 0x02  # 设置本地管理位
        first_byte = first_byte & 0xFE  # 清除多播位，确保是单播地址
        
        # 生成其余5个字节
        mac_bytes = [first_byte] + [random.randint(0, 255) for _ in range(5)]
        
        # 转换为冒号分隔的十六进制格式
        return ':'.join([f'{byte:02X}' for byte in mac_bytes])
