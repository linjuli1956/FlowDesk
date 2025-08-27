"""
颜色方案定义

定义FlowDesk应用程序的统一颜色方案和语义化颜色常量。
基于UI截图分析的卡片式彩色按钮设计，提供一致的视觉体验。

颜色语义：
- 蓝色：主要操作（连接、修改、复制）
- 绿色：成功/启用操作（启用网卡、添加IP）
- 红色：危险/禁用操作（禁用网卡、删除）
- 橙色：警告/工具操作（静态IP、DHCP）
- 紫色：特殊功能（Win11自动登录、计算机名）
- 青色：网络相关工具

设计特点：
- 基于Material Design颜色规范
- 支持悬停和按下状态的颜色变化
- 提供浅色和深色主题支持
- 语义化命名便于维护
"""

from typing import Dict


class ColorScheme:
    """
    颜色方案管理类
    
    提供统一的颜色定义和访问接口。
    支持不同主题和状态的颜色管理。
    """
    
    def __init__(self, theme="light"):
        """
        初始化颜色方案
        
        参数:
            theme (str): 主题名称，支持 "light" 和 "dark"
        """
        self.theme = theme
        self._colors = self._define_colors()
    
    def _define_colors(self) -> Dict[str, str]:
        """
        定义颜色常量
        
        基于UI截图分析定义的颜色方案。
        
        返回:
            Dict[str, str]: 颜色名称到十六进制颜色值的映射
        """
        if self.theme == "light":
            return {
                # 基础背景色
                "background_primary": "#f5f5f5",      # 主背景色（浅灰）
                "background_secondary": "#ffffff",    # 卡片背景色（白色）
                "background_tertiary": "#fafafa",     # 次要背景色
                
                # 文本颜色
                "text_primary": "#333333",            # 主文本色（深灰）
                "text_secondary": "#666666",          # 次要文本色（中灰）
                "text_tertiary": "#999999",           # 辅助文本色（浅灰）
                "text_inverse": "#ffffff",            # 反色文本（白色）
                
                # 边框颜色
                "border_color": "#e0e0e0",            # 主边框色（浅灰）
                "border_focus": "#4A90E2",            # 焦点边框色（蓝色）
                "border_error": "#D0021B",            # 错误边框色（红色）
                
                # Claymorphism按钮颜色 - 更淡的柔和渐变色系统（降低饱和度）
                # 蓝色按钮 - 主要操作（连接、修改、复制）- 更淡的蓝色渐变
                '--btn-blue': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F0F7FF, stop:1 #E1EFFF)',
                '--btn-blue-hover': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #E1EFFF, stop:1 #D1E7FF)',
                '--btn-blue-pressed': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #D1E7FF, stop:1 #C1DFFF)',
                '--btn-blue-border': '#D1E7FF',
                '--btn-blue-text': '#4A7BA7',
                
                # 绿色按钮 - 成功/启用操作（启用网卡、添加IP）- 更淡的绿色渐变
                '--btn-green': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F0F9F0, stop:1 #E1F5E1)',
                '--btn-green-hover': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #E1F5E1, stop:1 #D1F1D1)',
                '--btn-green-pressed': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #D1F1D1, stop:1 #C1EDC1)',
                '--btn-green-border': '#D1F1D1',
                '--btn-green-text': '#4A7C59',
                
                # 红色按钮 - 危险/禁用操作（禁用网卡、删除）- 更淡的红色渐变
                '--btn-red': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFF5F5, stop:1 #FFE9E9)',
                '--btn-red-hover': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFE9E9, stop:1 #FFDDDD)',
                '--btn-red-pressed': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFDDDD, stop:1 #FFD1D1)',
                '--btn-red-border': '#FFDDDD',
                '--btn-red-text': '#B85450',
                
                # 橙色按钮 - 警告/工具操作（静态IP、DHCP）- 更淡的橙色渐变
                '--btn-orange': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFAF0, stop:1 #FFF2E1)',
                '--btn-orange-hover': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFF2E1, stop:1 #FFEAD1)',
                '--btn-orange-pressed': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFEAD1, stop:1 #FFE2C1)',
                '--btn-orange-border': '#FFEAD1',
                '--btn-orange-text': '#CC8800',
                
                # 紫色按钮 - 特殊功能（Win11自动登录、计算机名）- 更淡的紫色渐变
                '--btn-purple': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FAF5FF, stop:1 #F0E6FF)',
                '--btn-purple-hover': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F0E6FF, stop:1 #E6D7FF)',
                '--btn-purple-pressed': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #E6D7FF, stop:1 #DCC8FF)',
                '--btn-purple-border': '#E6D7FF',
                '--btn-purple-text': '#8E4EC6',
                
                # 青色按钮 - 网络相关工具 - 更淡的青色渐变
                '--btn-cyan': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F0FFFE, stop:1 #E1FFF8)',
                '--btn-cyan-hover': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #E1FFF8, stop:1 #D1FFF2)',
                '--btn-cyan-pressed': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #D1FFF2, stop:1 #C1FFEC)',
                '--btn-cyan-border': '#D1FFF2',
                '--btn-cyan-text': '#4A9B8E',
                
                # 状态徽章颜色
                "badge_connected": "#7ED321",         # 已连接状态（绿色）
                "badge_disconnected": "#D0021B",      # 未连接状态（红色）
                "badge_dhcp": "#4A90E2",              # DHCP模式（蓝色）
                "badge_static": "#F5A623",            # 静态IP模式（橙色）
                "badge_warning": "#FF9500",           # 警告状态（橙色）
                "badge_info": "#5AC8FA",              # 信息状态（浅蓝）
                
                # 输入框颜色
                "input_background": "#ffffff",        # 输入框背景
                "input_border": "#d1d1d1",           # 输入框边框
                "input_border_focus": "#4A90E2",     # 输入框焦点边框
                "input_placeholder": "#999999",      # 占位符文本
                
                # 卡片颜色
                "card_background": "#ffffff",         # 卡片背景
                "card_border": "#e0e0e0",            # 卡片边框
                "card_shadow": "rgba(0, 0, 0, 0.1)", # 卡片阴影
                
                # Tab页面颜色
                "tab_background": "#f5f5f5",         # Tab背景
                "tab_active": "#ffffff",             # 活动Tab
                "tab_inactive": "#e0e0e0",           # 非活动Tab
                "tab_border": "#4A90E2",             # Tab边框
                
                # 系统托盘和对话框颜色
                "dialog_background": "#ffffff",       # 对话框背景
                "dialog_border": "#d1d1d1",          # 对话框边框
                "menu_background": "#ffffff",         # 菜单背景
                "menu_hover": "#f0f0f0",             # 菜单悬停
                "menu_separator": "#e0e0e0",         # 菜单分隔线
            }
        else:
            # 深色主题（预留）
            return self._define_dark_colors()
    
    def _define_dark_colors(self) -> Dict[str, str]:
        """
        定义深色主题颜色
        
        为未来的深色主题支持预留接口。
        
        返回:
            Dict[str, str]: 深色主题颜色映射
        """
        return {
            # 深色主题颜色定义
            "background_primary": "#2b2b2b",
            "background_secondary": "#3c3c3c",
            "text_primary": "#ffffff",
            "text_secondary": "#cccccc",
            # ... 其他深色主题颜色
        }
    
    def get_colors(self) -> Dict[str, str]:
        """
        获取当前主题的所有颜色
        
        返回:
            Dict[str, str]: 颜色名称到颜色值的映射
        """
        return self._colors.copy()
    
    def get_color(self, color_name: str, default: str = "#000000") -> str:
        """
        获取指定名称的颜色值
        
        参数:
            color_name (str): 颜色名称
            default (str): 默认颜色值
        
        返回:
            str: 颜色的十六进制值
        """
        return self._colors.get(color_name, default)
    
    def get_button_colors(self, button_type: str) -> Dict[str, str]:
        """
        获取按钮的所有状态颜色
        
        参数:
            button_type (str): 按钮类型（blue, green, red, orange, purple, cyan）
        
        返回:
            Dict[str, str]: 包含normal, hover, pressed状态的颜色映射
        """
        base_key = f"btn_{button_type}"
        return {
            "normal": self.get_color(base_key),
            "hover": self.get_color(f"{base_key}_hover"),
            "pressed": self.get_color(f"{base_key}_pressed"),
        }
    
    def get_semantic_colors(self) -> Dict[str, str]:
        """
        获取语义化颜色映射
        
        返回常用的语义化颜色，便于在代码中使用。
        
        返回:
            Dict[str, str]: 语义化颜色映射
        """
        return {
            "primary": self.get_color("btn_blue"),
            "success": self.get_color("btn_green"),
            "danger": self.get_color("btn_red"),
            "warning": self.get_color("btn_orange"),
            "info": self.get_color("btn_cyan"),
            "secondary": self.get_color("text_secondary"),
        }
    
    def set_theme(self, theme: str):
        """
        切换颜色主题
        
        参数:
            theme (str): 主题名称（light 或 dark）
        """
        if theme != self.theme:
            self.theme = theme
            self._colors = self._define_colors()
    
    def get_theme(self) -> str:
        """
        获取当前主题名称
        
        返回:
            str: 当前主题名称
        """
        return self.theme
    
    def export_css_variables(self) -> str:
        """
        导出CSS变量格式的颜色定义
        
        用于在QSS文件中使用颜色变量。
        
        返回:
            str: CSS变量格式的颜色定义
        """
        css_vars = []
        for color_name, color_value in self._colors.items():
            css_var_name = f"--{color_name.replace('_', '-')}"
            css_vars.append(f"{css_var_name}: {color_value};")
        
        return "\n".join(css_vars)
