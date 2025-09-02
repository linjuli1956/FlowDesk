# -*- coding: utf-8 -*-
"""
IP配置确认数据模型：定义IP修改确认弹窗所需的数据结构
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class IPConfigConfirmation:
    """
    IP配置确认信息的不可变数据类
    
    用于在确认弹窗中展示即将应用的IP配置信息，
    让用户在确认修改前查看完整的配置详情。
    
    Attributes:
        adapter_name: 目标网卡名称
        current_ip: 当前IP地址
        new_ip: 新IP地址
        current_subnet_mask: 当前子网掩码
        new_subnet_mask: 新子网掩码
        current_gateway: 当前网关
        new_gateway: 新网关（可选）
        current_dns_primary: 当前主DNS
        new_dns_primary: 新主DNS（可选）
        current_dns_secondary: 当前备用DNS
        new_dns_secondary: 新备用DNS（可选）
        dhcp_enabled: 是否启用DHCP
    """
    adapter_name: str
    current_ip: Optional[str]
    new_ip: str
    current_subnet_mask: Optional[str]
    new_subnet_mask: str
    current_gateway: Optional[str]
    new_gateway: Optional[str]  # 允许为空
    current_dns_primary: Optional[str]
    new_dns_primary: Optional[str]  # 允许为空
    current_dns_secondary: Optional[str]
    new_dns_secondary: Optional[str]  # 允许为空
    dhcp_enabled: bool
    
    def _get_smart_subnet_mask_display(self, original_mask: str, user_input: str) -> str:
        """
        生成智能子网掩码三段式转换显示
        
        Args:
            original_mask: 原始子网掩码
            user_input: 用户输入的子网掩码
            
        Returns:
            str: 三段式转换显示文本
        """
        from ..utils.ip_validation_utils import (
            subnet_mask_to_cidr, 
            cidr_to_subnet_mask,
            normalize_subnet_mask_for_netsh
        )
        
        try:
            # 获取原始掩码的CIDR值
            original_cidr = ""
            if original_mask and original_mask != "未设置":
                cidr_val = subnet_mask_to_cidr(original_mask)
                if cidr_val != -1:
                    original_cidr = f"/{cidr_val}"
            
            # 判断用户输入的格式类型
            user_input_clean = user_input.strip()
            
            if user_input_clean.isdigit():
                # 用户输入纯数字格式 (如: 16)
                cidr_val = int(user_input_clean)
                converted_mask = cidr_to_subnet_mask(cidr_val)
                return f"{original_mask} → <span style='color: #e67e22; font-weight: bold;'>{user_input_clean}</span> → <span style='color: #10b981; font-weight: bold;'>{converted_mask}</span>"
                
            elif user_input_clean.startswith('/'):
                # 用户输入CIDR格式 (如: /16)
                cidr_val = int(user_input_clean[1:])
                converted_mask = cidr_to_subnet_mask(cidr_val)
                return f"{original_mask} → <span style='color: #e67e22; font-weight: bold;'>{user_input_clean}</span> → <span style='color: #10b981; font-weight: bold;'>{converted_mask}</span>"
                
            else:
                # 用户输入点分十进制格式 (如: 255.255.0.0)
                cidr_val = subnet_mask_to_cidr(user_input_clean)
                if cidr_val != -1:
                    return f"{original_mask} → <span style='color: #e67e22; font-weight: bold;'>{user_input_clean}</span> → <span style='color: #10b981; font-weight: bold;'>/{cidr_val}</span>"
                else:
                    return f"{original_mask} → <span style='color: #10b981; font-weight: bold;'>{user_input_clean}</span>"
                    
        except (ValueError, TypeError):
            # 转换失败，使用简单显示
            return f"{original_mask} → <span style='color: #10b981; font-weight: bold;'>{user_input}</span>"

    def get_changes_summary(self) -> str:
        """
        生成配置变更摘要文本 - 显示所有配置项对比，带HTML格式和颜色
        
        Returns:
            str: 格式化的变更摘要（HTML格式）
        """
        changes = []
        
        # 生成配置变更摘要，使用内联样式（QTextEdit不支持CSS类选择器）
        ip_changed = self.current_ip != self.new_ip
        current_ip_display = self.current_ip or "未设置"
        changes.append(f'<span style="color: #2c3e50; font-size: 13px;">IP地址: {current_ip_display} </span><span style="color: #3b82f6; font-size: 15px; font-weight: bold;">→ {self.new_ip}</span>')
        
        # 智能子网掩码显示 - 三段式转换
        subnet_changed = self.current_subnet_mask != self.new_subnet_mask
        current_subnet_display = self.current_subnet_mask or "未设置"
        smart_subnet_display = self._get_smart_subnet_mask_display(current_subnet_display, self.new_subnet_mask)
        changes.append(f'<span style="color: #2c3e50; font-size: 13px;">子网掩码: {smart_subnet_display}</span>')
        
        current_gw = self.current_gateway or "未设置"
        new_gw = self.new_gateway or "未设置"
        gw_changed = self.current_gateway != self.new_gateway
        changes.append(f'<span style="color: #2c3e50; font-size: 13px;">默认网关: {current_gw} </span><span style="color: #8b5cf6; font-size: 15px; font-weight: bold;">→ {new_gw}</span>')
        
        current_dns1 = self.current_dns_primary or "未设置"
        new_dns1 = self.new_dns_primary or "未设置"
        dns1_changed = self.current_dns_primary != self.new_dns_primary
        changes.append(f'<span style="color: #2c3e50; font-size: 13px;">主DNS: {current_dns1} </span><span style="color: #f59e0b; font-size: 15px; font-weight: bold;">→ {new_dns1}</span>')
        
        current_dns2 = self.current_dns_secondary or "未设置"
        new_dns2 = self.new_dns_secondary or "未设置"
        dns2_changed = self.current_dns_secondary != self.new_dns_secondary
        changes.append(f'<span style="color: #2c3e50; font-size: 13px;">备用DNS: {current_dns2} </span><span style="color: #ec4899; font-size: 15px; font-weight: bold;">→ {new_dns2}</span>')
        
        return "<br>".join(changes)
    
    def has_changes(self) -> bool:
        """
        检查是否有配置变更
        
        Returns:
            bool: 有变更返回True，无变更返回False
        """
        # 处理可选字段的空值比较
        current_gw = self.current_gateway or ""
        new_gw = self.new_gateway or ""
        current_dns1 = self.current_dns_primary or ""
        new_dns1 = self.new_dns_primary or ""
        current_dns2 = self.current_dns_secondary or ""
        new_dns2 = self.new_dns_secondary or ""
        
        return (
            self.current_ip != self.new_ip or
            self.current_subnet_mask != self.new_subnet_mask or
            current_gw != new_gw or
            current_dns1 != new_dns1 or
            current_dns2 != new_dns2
        )
