# -*- coding: utf-8 -*-
"""
状态栏信息数据模型

这个模块定义了主窗口状态栏显示所需的数据结构。
通过不可变数据类确保状态信息的类型安全和数据一致性，
为状态栏UI组件提供标准化的数据契约。
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class StatusBarInfo:
    """
    状态栏信息数据模型
    
    封装主窗口底部状态栏需要显示的所有信息，包括应用运行状态、
    用户当前操作状态、版本信息和构建日期。使用frozen=True确保
    数据不可变性，避免意外的状态修改。
    
    属性说明：
    - app_status: 应用程序当前运行状态，带Emoji标识
    - user_action: 用户当前执行的操作描述，带Emoji标识
    - version: 应用程序版本号
    - build_date: 构建日期或开发环境的当前日期
    """
    
    app_status: str                    # 应用状态，如 "🟢 就绪"
    user_action: str                   # 用户操作，如 "📡 获取网卡信息"
    version: str                       # 版本号，如 "v1.0.0"
    build_date: str                    # 构建日期，如 "2025-09-01"
    
    @classmethod
    def create_default(cls, version: str = "v1.0.0", build_date: str = "") -> 'StatusBarInfo':
        """
        创建默认状态栏信息
        
        提供便捷的工厂方法创建初始状态的StatusBarInfo实例，
        用于应用程序启动时的默认状态显示。
        
        Args:
            version: 应用版本号
            build_date: 构建日期
            
        Returns:
            StatusBarInfo: 默认状态的数据实例
        """
        return cls(
            app_status="🟢 就绪",
            user_action="⏳ 初始化中...",
            version=version,
            build_date=build_date
        )
    
    def with_app_status(self, new_status: str) -> 'StatusBarInfo':
        """
        创建新的StatusBarInfo实例，更新应用状态
        
        由于数据类是不可变的，任何状态更新都需要创建新实例。
        这个方法提供便捷的应用状态更新功能。
        
        Args:
            new_status: 新的应用状态
            
        Returns:
            StatusBarInfo: 更新应用状态后的新实例
        """
        return StatusBarInfo(
            app_status=new_status,
            user_action=self.user_action,
            version=self.version,
            build_date=self.build_date
        )
    
    def with_user_action(self, new_action: str) -> 'StatusBarInfo':
        """
        创建新的StatusBarInfo实例，更新用户操作状态
        
        Args:
            new_action: 新的用户操作描述
            
        Returns:
            StatusBarInfo: 更新用户操作后的新实例
        """
        return StatusBarInfo(
            app_status=self.app_status,
            user_action=new_action,
            version=self.version,
            build_date=self.build_date
        )


@dataclass(frozen=True)
class StatusBarTheme:
    """
    状态栏主题配置数据模型
    
    定义状态栏的视觉样式配置，包括颜色、字体等主题相关设置。
    通过数据模型管理主题配置，便于后续扩展主题切换功能。
    """
    
    status_color: str = "#333333"      # 状态文字颜色
    version_color: str = "#5dade2"     # 版本信息颜色(淡蓝色)
    background_color: str = "#f8f9fa"  # 背景颜色
    border_color: str = "#e0e0e0"      # 边框颜色
    font_weight: str = "bold"          # 状态文字字重
    font_size: str = "12px"            # 版本文字大小
