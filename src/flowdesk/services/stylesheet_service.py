"""
FlowDesk样式表管理服务

专业的QSS样式表管理器，支持模块化样式文件的加载、合并和应用。
解决样式文件臃肿和加载冲突问题，提供可扩展的架构支持。

主要功能：
- 按顺序读取并合并多个QSS文件
- 模块化加载：主样式 + 特定页面样式
- 统一应用：合并后的样式字符串一次性设置
- 避免样式冲突和重复定义

设计原则：
🚫 禁止样式重复 - 通过统一管理器避免重复定义
🔄 严格自适应布局 - 保持样式的响应式特性
📏 最小宽度保护 - 维护所有尺寸保护机制
⚙️ 智能组件缩放 - 支持模块化的组件样式管理
"""

import os
import logging
from typing import List, Optional


class StylesheetService:
    """
    样式表管理服务
    
    负责管理FlowDesk应用程序的所有QSS样式文件，
    提供模块化的样式加载和统一的样式应用功能。
    
    核心职责：
    - 按预定义顺序加载多个QSS文件
    - 合并样式内容，确保优先级正确
    - 统一应用样式，避免多次setStyleSheet调用
    - 提供开发时的热重载支持
    """
    
    def __init__(self, use_win7_compatibility=False):
        """
        初始化样式表管理服务
        
        设置QSS文件目录路径，定义样式文件加载顺序。
        加载顺序决定样式优先级，后加载的文件会覆盖前面的相同选择器。
        
        Args:
            use_win7_compatibility (bool): 是否使用Windows 7兼容模式
        """
        self.logger = logging.getLogger(__name__)
        self.qss_dir = os.path.join(os.path.dirname(__file__), "..", "ui", "qss")
        self.current_stylesheet = ""
        self.use_win7_compatibility = use_win7_compatibility
        
        # 根据系统版本选择主样式文件
        main_style_file = "main_win7.qss" if use_win7_compatibility else "main_pyqt5.qss"
        
        # 定义样式文件加载顺序（重要：顺序决定样式优先级）
        # 后加载的文件会覆盖前面文件中的相同选择器
        self.stylesheet_files = [
            main_style_file,            # 主样式文件：全局变量、通用组件样式
            "network_config_tab.qss",   # 网络配置Tab专用样式
            "network_tools_tab.qss",    # 网络工具Tab专用样式
            "rdp_tab.qss",              # 远程桌面Tab专用样式
            "hardware_tab.qss",         # 硬件信息Tab专用样式
            "system_tray_menu.qss",     # 系统托盘右键菜单样式
            "tray_exit_dialog.qss",     # 托盘退出对话框样式
            "add_ip_dialog.qss",        # 添加IP对话框专用样式
            "ip_config_confirm_dialog.qss",  # IP配置确认弹窗专用样式
            "main_window.qss",          # 主窗口特定样式
        ]
        
        self.logger.debug(f"样式表管理服务初始化完成 - {'Win7兼容模式' if use_win7_compatibility else '标准模式'}")
    
    def load_stylesheets(self) -> str:
        """
        按顺序加载并合并所有QSS样式文件
        
        核心方法：读取预定义的样式文件列表，按顺序合并内容，
        确保样式优先级正确，避免冲突。每个文件的内容会添加
        分隔注释，便于调试时定位样式来源。
        
        Returns:
            str: 合并后的完整样式字符串
            
        Raises:
            FileNotFoundError: 当关键样式文件（main_pyqt5.qss）缺失时抛出异常
            Exception: 当主样式文件读取失败时抛出异常
        """
        combined_styles = ""
        loaded_files = []
        
        for filename in self.stylesheet_files:
            file_path = os.path.join(self.qss_dir, filename)
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                if filename == "main_pyqt5.qss":
                    # 主样式文件是必需的，缺失时抛出异常
                    raise FileNotFoundError(f"关键样式文件缺失: {filename}")
                else:
                    # 其他文件可选，记录警告但继续加载
                    self.logger.warning(f"样式文件不存在，跳过: {filename}")
                    continue
            
            try:
                # 读取样式文件内容，使用UTF-8编码确保中文注释正确显示
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 添加文件分隔注释，便于调试时识别样式来源
                combined_styles += f"\n/* ===== 样式文件: {filename} ===== */\n"
                combined_styles += content + "\n"
                
                
                loaded_files.append(filename)
                self.logger.debug(f"样式文件加载成功: {filename}")
                
            except Exception as e:
                self.logger.error(f"加载样式文件失败 {filename}: {e}")
                if filename == "main_pyqt5.qss":
                    # 主样式文件加载失败是致命错误，必须抛出异常
                    raise
        
        self.logger.debug(f"样式表合并完成，已加载文件: {', '.join(loaded_files)}")
        
        
        return combined_styles
    
    def apply_stylesheets(self, app) -> None:
        """
        将合并后的样式表应用到应用程序
        
        统一应用方法：加载所有样式文件，合并后一次性设置给应用程序，
        避免多次setStyleSheet调用导致的性能问题和样式冲突。
        这是整个样式系统的入口点。
        
        Args:
            app: Qt应用程序实例（移除PyQt类型依赖）
        """
        try:
            # 加载并合并所有样式文件
            combined_styles = self.load_stylesheets()
            
            # 一次性应用所有样式到应用程序
            # 这会替换之前所有的样式设置
            app.setStyleSheet(combined_styles)
            
            # 缓存当前样式，便于后续操作（如热重载、调试等）
            self.current_stylesheet = combined_styles
            
            self.logger.debug("样式表应用成功")
            
        except Exception as e:
            self.logger.error(f"应用样式表失败: {e}")
            # 应用失败时使用空样式，确保程序能正常运行
            # 这样即使样式有问题，UI功能仍然可用
            app.setStyleSheet("")
    
    def reload_stylesheets(self, app) -> None:
        """
        重新加载样式表（用于开发调试）
        
        开发辅助方法：在开发过程中可以调用此方法重新加载样式，
        无需重启应用程序即可看到样式修改效果。特别适用于
        样式调试和实时预览场景。
        
        Args:
            app: Qt应用程序实例（移除PyQt类型依赖）
        """
        self.logger.debug("重新加载样式表...")
        self.apply_stylesheets(app)
    
    def add_stylesheet_file(self, filename: str, position: Optional[int] = None) -> None:
        """
        动态添加样式文件到加载列表
        
        扩展方法：支持在运行时动态添加新的样式文件，
        适用于插件系统或动态功能模块。添加的文件会在
        下次调用apply_stylesheets时生效。
        
        Args:
            filename (str): 要添加的样式文件名（不包含路径）
            position (Optional[int]): 插入位置，None表示添加到末尾
                                    位置越靠后，样式优先级越高
        """
        if position is None:
            self.stylesheet_files.append(filename)
        else:
            self.stylesheet_files.insert(position, filename)
        
        self.logger.debug(f"样式文件已添加到加载列表: {filename}")
    
    def remove_stylesheet_file(self, filename: str) -> bool:
        """
        从加载列表中移除样式文件
        
        管理方法：支持动态移除不需要的样式文件，
        提供灵活的样式管理能力。移除后需要重新
        应用样式才能生效。
        
        Args:
            filename (str): 要移除的样式文件名
            
        Returns:
            bool: 移除成功返回True，文件不存在返回False
        """
        try:
            self.stylesheet_files.remove(filename)
            self.logger.debug(f"样式文件已从加载列表移除: {filename}")
            return True
        except ValueError:
            self.logger.warning(f"要移除的样式文件不在列表中: {filename}")
            return False
    
    def get_loaded_files(self) -> List[str]:
        """
        获取当前加载列表中的所有样式文件
        
        查询方法：返回当前配置的样式文件列表，
        便于调试和状态检查。返回的是列表副本，
        修改不会影响原始配置。
        
        Returns:
            List[str]: 样式文件名列表的副本
        """
        return self.stylesheet_files.copy()
    
    def get_current_stylesheet(self) -> str:
        """
        获取当前应用的完整样式字符串
        
        调试方法：返回最后一次成功应用的样式内容，
        便于样式调试和问题排查。可以用于导出
        当前样式或进行样式分析。
        
        Returns:
            str: 当前的完整样式字符串
        """
        return self.current_stylesheet
    
    def validate_qss_files(self) -> List[str]:
        """
        验证所有QSS文件的存在性和可读性
        
        诊断方法：检查配置列表中的所有QSS文件是否存在
        且可读，返回有问题的文件列表。用于部署前的
        完整性检查或故障排除。
        
        Returns:
            List[str]: 有问题的文件名列表，空列表表示所有文件正常
        """
        problematic_files = []
        
        for filename in self.stylesheet_files:
            file_path = os.path.join(self.qss_dir, filename)
            
            if not os.path.exists(file_path):
                problematic_files.append(f"{filename} (文件不存在)")
            elif not os.access(file_path, os.R_OK):
                problematic_files.append(f"{filename} (文件不可读)")
        
        if problematic_files:
            self.logger.warning(f"发现问题文件: {', '.join(problematic_files)}")
        else:
            self.logger.debug("所有QSS文件验证通过")
            
        return problematic_files
