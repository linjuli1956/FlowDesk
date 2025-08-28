"""
样式表管理器

负责FlowDesk应用程序的QSS样式表加载和管理。
自动检测Windows版本，选择合适的样式表文件，并提供样式预处理功能。

主要功能：
- 自动检测Windows版本（Win10/11 vs Win7）
- 加载对应的QSS样式表文件
- 颜色变量预处理和替换
- 样式表缓存和热重载
- 开发环境和打包环境的资源路径处理

设计特点：
- 支持Win7降级样式处理
- 提供颜色方案变量替换
- 统一的样式表管理接口
- 错误处理和日志记录
"""

import os
import platform
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject

from ...utils.resource_path import resource_path
from ...utils.logger import get_logger
from .color_scheme import ColorScheme


class StylesheetManager(QObject):
    """
    样式表管理器类
    
    管理QSS样式表的加载、预处理和应用。
    根据系统环境自动选择合适的样式表文件。
    """
    
    def __init__(self):
        """初始化样式表管理器"""
        super().__init__()
        
        self.logger = get_logger(__name__)
        self.color_scheme = ColorScheme()
        self.current_stylesheet = ""
        self.is_win7 = self._detect_win7()
        
        self.logger.info(f"样式表管理器初始化完成，Windows 7模式: {self.is_win7}")
    
    def _detect_win7(self):
        """
        检测是否为Windows 7系统
        
        用于确定是否需要使用Win7兼容样式表。
        
        返回:
            bool: 如果是Windows 7返回True，否则返回False
        """
        try:
            # 获取Windows版本信息
            system = platform.system()
            release = platform.release()
            
            # 检查是否为Windows 7
            if system == "Windows" and release == "7":
                return True
            
            # 也可以通过版本号检查
            version = platform.version()
            if version.startswith("6.1"):  # Windows 7的版本号
                return True
                
            return False
            
        except Exception as e:
            self.logger.warning(f"检测Windows版本失败: {e}，默认使用现代样式")
            return False
    
    def get_stylesheet_path(self):
        """
        获取样式表文件路径
        
        根据Windows版本选择合适的样式表文件。
        
        返回:
            str: 样式表文件的绝对路径
        """
        if self.is_win7:
            # Windows 7兼容样式表
            stylesheet_name = "main_pyqt5_win7.qss"
        else:
            # Windows 10/11现代样式表
            stylesheet_name = "main_pyqt5.qss"
        
        return resource_path(f"src/flowdesk/ui/qss/{stylesheet_name}")
    
    def load_stylesheet(self):
        """
        加载QSS样式表文件
        
        从文件系统读取样式表内容，并进行预处理。
        
        返回:
            str: 处理后的样式表内容，如果加载失败返回空字符串
        """
        stylesheet_path = self.get_stylesheet_path()
        
        try:
            # 检查QSS文件是否存在
            if not os.path.exists(stylesheet_path):
                self.logger.warning(f"样式表文件不存在: {stylesheet_path}")
                return self._get_fallback_stylesheet()
            
            # 读取样式表文件
            with open(stylesheet_path, 'r', encoding='utf-8') as file:
                stylesheet_content = file.read()
            
            # 预处理样式表（替换颜色变量等）
            processed_stylesheet = self._preprocess_stylesheet(stylesheet_content)
            
            self.logger.info(f"样式表加载成功: {stylesheet_path}")
            return processed_stylesheet
            
        except Exception as e:
            self.logger.error(f"加载样式表失败: {e}")
            return self._get_fallback_stylesheet()
    
    def _preprocess_stylesheet(self, stylesheet_content):
        """
        预处理样式表内容
        
        替换颜色变量、处理条件编译等预处理操作。
        
        参数:
            stylesheet_content (str): 原始样式表内容
        
        返回:
            str: 预处理后的样式表内容
        """
        try:
            # 获取颜色方案
            colors = self.color_scheme.get_colors()
            
            # 替换颜色变量
            processed_content = stylesheet_content
            for color_name, color_value in colors.items():
                variable_name = f"--{color_name.replace('_', '-')}"
                processed_content = processed_content.replace(variable_name, color_value)
            
            # 处理Windows 7特定的条件编译
            if self.is_win7:
                processed_content = self._apply_win7_compatibility(processed_content)
            
            return processed_content
            
        except Exception as e:
            self.logger.error(f"样式表预处理失败: {e}")
            return stylesheet_content
    
    def _apply_win7_compatibility(self, stylesheet_content):
        """
        应用Windows 7兼容性处理
        
        移除或修改Windows 7不支持的CSS属性。
        
        参数:
            stylesheet_content (str): 样式表内容
        
        返回:
            str: Win7兼容的样式表内容
        """
        # 移除Windows 7不支持的属性
        win7_incompatible = [
            "border-radius",  # 部分情况下不支持
            "box-shadow",     # 不支持阴影效果
            "backdrop-filter", # 不支持背景滤镜
        ]
        
        processed_content = stylesheet_content
        
        # 这里可以添加更复杂的Win7兼容性处理逻辑
        # 例如替换不支持的属性或提供降级方案
        
        return processed_content
    
    def _get_fallback_stylesheet(self):
        """
        获取后备样式表
        
        当主样式表加载失败时使用的基础样式。
        
        返回:
            str: 基础样式表内容
        """
        return """
        /* FlowDesk 后备样式表 */
        QMainWindow {
            background-color: #f5f5f5;
        }
        
        QTabWidget::pane {
            border: 1px solid #c0c0c0;
            background-color: white;
        }
        
        QTabBar::tab {
            background-color: #e0e0e0;
            padding: 8px 16px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 2px solid #4A90E2;
        }
        
        QPushButton {
            background-color: #4A90E2;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        
        QPushButton:hover {
            background-color: #357ABD;
        }
        
        QPushButton:pressed {
            background-color: #2E6DA4;
        }
        """
    
    def apply_stylesheet(self, app):
        """
        应用样式表到应用程序
        
        加载并应用样式表到QApplication实例。
        
        参数:
            app (QApplication): Qt应用程序实例
        """
        try:
            # 加载样式表
            stylesheet = self.load_stylesheet()
            
            # 应用样式表
            app.setStyleSheet(stylesheet)
            
            # 缓存当前样式表
            self.current_stylesheet = stylesheet
            
            self.logger.info("样式表应用成功")
            
        except Exception as e:
            self.logger.error(f"应用样式表失败: {e}")
    
    def reload_stylesheet(self, app):
        """
        重新加载样式表
        
        用于开发环境的样式表热重载功能。
        
        参数:
            app (QApplication): Qt应用程序实例
        """
        self.logger.info("重新加载样式表")
        self.apply_stylesheet(app)
    
    def get_current_stylesheet(self):
        """
        获取当前应用的样式表内容
        
        返回:
            str: 当前样式表内容
        """
        return self.current_stylesheet
    
    def is_windows7_mode(self):
        """
        检查是否为Windows 7模式
        
        返回:
            bool: Windows 7模式返回True
        """
        return self.is_win7
