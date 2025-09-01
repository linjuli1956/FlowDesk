# -*- coding: utf-8 -*-
"""
版本信息工具函数

提供应用程序版本号和构建日期的获取功能。
在开发环境中使用当前系统日期作为构建日期，
在生产环境中可以从配置文件或构建信息中获取。
"""

import os
import datetime
from typing import Tuple


def get_app_version() -> str:
    """
    获取应用程序版本号
    
    从多个数据源获取版本信息，优先级如下：
    1. 环境变量 FLOWDESK_VERSION
    2. 版本配置文件
    3. 默认版本号
    
    Returns:
        str: 版本号字符串，格式为 "v1.0.0"
    """
    # 优先从环境变量获取版本号
    version = os.environ.get('FLOWDESK_VERSION')
    if version:
        return f"v{version}" if not version.startswith('v') else version
    
    # 尝试从版本文件读取
    try:
        version_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'VERSION'
        )
        if os.path.exists(version_file):
            with open(version_file, 'r', encoding='utf-8') as f:
                version = f.read().strip()
                return f"v{version}" if not version.startswith('v') else version
    except Exception:
        # 版本文件读取失败，使用默认版本
        pass
    
    # 默认版本号
    return "v1.0.0"


def get_build_date() -> str:
    """
    获取构建日期
    
    在开发环境中返回当前系统日期，
    在生产环境中可以从构建信息中获取实际构建日期。
    
    Returns:
        str: 构建日期字符串，格式为 "YYYY-MM-DD"
    """
    # 优先从环境变量获取构建日期
    build_date = os.environ.get('FLOWDESK_BUILD_DATE')
    if build_date:
        return build_date
    
    # 尝试从构建信息文件读取
    try:
        build_info_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'BUILD_INFO'
        )
        if os.path.exists(build_info_file):
            with open(build_info_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except Exception:
        # 构建信息文件读取失败，使用当前日期
        pass
    
    # 开发环境使用当前日期
    return datetime.datetime.now().strftime("%Y-%m-%d")


def get_version_info() -> Tuple[str, str]:
    """
    获取完整的版本信息
    
    便捷函数，同时获取版本号和构建日期。
    
    Returns:
        Tuple[str, str]: (版本号, 构建日期)
    """
    return get_app_version(), get_build_date()


def format_version_display(version: str, build_date: str) -> str:
    """
    格式化版本显示文本
    
    将版本号和构建日期格式化为适合状态栏显示的文本。
    
    Args:
        version: 版本号
        build_date: 构建日期
        
    Returns:
        str: 格式化后的版本显示文本
    """
    return f"{version} ({build_date})"
