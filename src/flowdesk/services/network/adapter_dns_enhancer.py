# -*- coding: utf-8 -*-
"""
网卡DNS配置增强器｜专门负责DNS配置的增强获取和处理
"""
import subprocess
import re
import logging
from typing import Optional, List


class AdapterDnsEnhancer:
    """
    网卡DNS配置增强器
    
    专门负责通过netsh命令获取更准确的DNS服务器配置信息。
    作为ipconfig命令的补充，提供更可靠的DNS信息获取能力。
    
    主要功能：
    - 使用netsh命令查询DNS服务器配置
    - 提供DNS配置的增强获取和合并策略
    - 实现DNS服务器列表的去重和排序
    """
    
    def __init__(self):
        """初始化DNS增强器"""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_enhanced_dns_config(self, adapter_name: str) -> Optional[List[str]]:
        """
        使用netsh命令增强获取DNS配置信息
        
        这个方法专门用于通过netsh命令获取更准确的DNS服务器配置信息。
        作为ipconfig命令的补充，提供更可靠的DNS信息获取能力。
        
        Args:
            adapter_name (str): 网卡连接名称
            
        Returns:
            Optional[List[str]]: DNS服务器地址列表，失败时返回None
        """
        try:
            # 使用netsh命令查询DNS服务器配置
            result = subprocess.run(
                ['netsh', 'interface', 'ipv4', 'show', 'dns', f'name={adapter_name}'],
                capture_output=True, text=True, timeout=10, encoding='gbk', errors='ignore'
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # 解析DNS服务器地址
                dns_pattern = r'(\d+\.\d+\.\d+\.\d+)'
                dns_servers = re.findall(dns_pattern, output)
                
                if dns_servers:
                    self.logger.debug(f"netsh获取到网卡 {adapter_name} 的DNS服务器: {dns_servers}")
                    return dns_servers
                else:
                    self.logger.debug(f"netsh未找到网卡 {adapter_name} 的DNS配置")
                    return None
            else:
                self.logger.warning(f"netsh DNS查询失败，返回码: {result.returncode}")
                return None
                
        except Exception as e:
            self.logger.error(f"增强DNS配置获取失败: {str(e)}")
            return None
    
    def enhance_dns_config(self, adapter_name: str, existing_dns: List[str]) -> List[str]:
        """
        增强DNS配置的公共入口方法
        
        结合现有DNS配置和netsh获取的DNS信息，提供完整的DNS服务器列表。
        
        Args:
            adapter_name (str): 网卡连接名称
            existing_dns (List[str]): 现有的DNS服务器列表
            
        Returns:
            List[str]: 增强后的DNS服务器列表
        """
        # 获取netsh增强的DNS配置
        enhanced_dns = self.get_enhanced_dns_config(adapter_name)
        
        if enhanced_dns:
            # 如果netsh获取到了DNS信息，优先使用或合并到现有DNS列表中
            # 合并DNS服务器列表，去重并保持顺序
            combined_dns = enhanced_dns.copy()
            for dns in existing_dns:
                if dns not in combined_dns:
                    combined_dns.append(dns)
            
            self.logger.debug(f"网卡 {adapter_name} DNS配置已增强: {combined_dns}")
            return combined_dns
        else:
            # 如果netsh获取失败，返回原有DNS配置
            return existing_dns
