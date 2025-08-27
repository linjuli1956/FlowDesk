"""
FlowDesk 应用程序基础配置文件

这个文件定义了FlowDesk应用程序的核心配置项，包括窗口设置、UI主题、
网络配置、硬件监控等各个模块的默认参数。所有配置都有合理的默认值，
确保应用程序在不同环境下都能稳定运行。

配置分类：
- 应用程序基础设置（窗口、主题、语言等）
- UI界面配置（尺寸、布局、动画等）
- 网络模块配置（超时、重试、默认值等）
- 硬件监控配置（刷新频率、阈值、显示项等）
- 远程桌面配置（连接参数、历史记录等）
- 系统托盘配置（图标、菜单、行为等）
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class AppSettings:
    """
    应用程序基础设置类
    
    定义FlowDesk应用程序的核心运行参数，包括窗口属性、主题设置、
    语言配置等。这些设置影响整个应用程序的基础行为和外观。
    """
    
    # 应用程序基本信息
    APP_NAME: str = "FlowDesk"                    # 应用程序名称，用于窗口标题和系统识别
    APP_VERSION: str = "1.0.0"                   # 版本号，用于更新检查和兼容性判断
    APP_AUTHOR: str = "FlowDesk Team"             # 开发团队名称
    
    # 窗口设置 - 定义主窗口的尺寸和行为
    WINDOW_WIDTH: int = 660                       # 主窗口宽度（像素），基于UI设计规范
    WINDOW_HEIGHT: int = 645                      # 主窗口高度（像素），确保所有内容完整显示
    WINDOW_MIN_WIDTH: int = 600                   # 窗口最小宽度，防止界面元素重叠
    WINDOW_MIN_HEIGHT: int = 580                  # 窗口最小高度，保证基本功能可用
    WINDOW_RESIZABLE: bool = True                 # 是否允许调整窗口大小
    WINDOW_CENTER_ON_START: bool = True           # 启动时是否居中显示窗口
    
    # UI主题和样式设置
    THEME_NAME: str = "claymorphism"              # 主题名称，对应QSS样式文件
    THEME_PATH: str = "src/flowdesk/ui/qss"       # QSS样式文件存放路径
    ICON_PATH: str = "assets/icons"               # 图标文件存放路径
    ENABLE_ANIMATIONS: bool = True                # 是否启用UI动画效果
    ANIMATION_DURATION: int = 200                 # 动画持续时间（毫秒）
    
    # 语言和本地化设置
    LANGUAGE: str = "zh_CN"                       # 界面语言，支持中文简体
    ENCODING: str = "utf-8"                       # 文本编码格式
    
    # 系统托盘设置
    ENABLE_SYSTEM_TRAY: bool = True               # 是否启用系统托盘功能
    MINIMIZE_TO_TRAY: bool = True                 # 最小化时是否隐藏到系统托盘
    CLOSE_TO_TRAY: bool = True                    # 关闭窗口时是否最小化到托盘
    TRAY_ICON_NAME: str = "flowdesk.ico"          # 系统托盘图标文件名


@dataclass
class NetworkSettings:
    """
    网络模块配置类
    
    定义网络配置和网络工具模块的各项参数，包括连接超时、重试次数、
    默认值等。这些设置影响网络操作的行为和用户体验。
    """
    
    # 网络连接基础参数
    CONNECTION_TIMEOUT: int = 5                   # 网络连接超时时间（秒）
    PING_TIMEOUT: int = 3                         # Ping操作超时时间（秒）
    PING_COUNT: int = 4                           # 默认Ping次数
    MAX_RETRY_COUNT: int = 3                      # 网络操作最大重试次数
    
    # 默认网络配置值
    DEFAULT_DNS_PRIMARY: str = "8.8.8.8"         # 主DNS服务器地址（Google DNS）
    DEFAULT_DNS_SECONDARY: str = "8.8.4.4"       # 备用DNS服务器地址
    DEFAULT_SUBNET_MASK: str = "255.255.255.0"   # 默认子网掩码（C类网络）
    DEFAULT_PING_TARGET: str = "www.baidu.com"   # 默认Ping测试目标
    
    # 网络诊断设置
    ENABLE_NETWORK_MONITORING: bool = True        # 是否启用网络状态监控
    NETWORK_CHECK_INTERVAL: int = 30              # 网络状态检查间隔（秒）
    SHOW_NETWORK_SPEED: bool = True               # 是否显示网络速度
    
    # IP地址验证规则
    ALLOW_PRIVATE_IP: bool = True                 # 是否允许私有IP地址
    ALLOW_LOOPBACK_IP: bool = True                # 是否允许回环地址
    STRICT_IP_VALIDATION: bool = False            # 是否启用严格IP验证


@dataclass
class HardwareSettings:
    """
    硬件监控模块配置类
    
    定义硬件信息监控的各项参数，包括刷新频率、温度阈值、显示项目等。
    这些设置控制硬件监控的精度和性能平衡。
    """
    
    # 监控刷新设置
    REFRESH_INTERVAL: int = 2                     # 硬件信息刷新间隔（秒）
    AUTO_REFRESH: bool = True                     # 是否自动刷新硬件信息
    ENABLE_REAL_TIME_MONITORING: bool = True      # 是否启用实时监控
    
    # 温度阈值设置（摄氏度）
    CPU_TEMP_WARNING: int = 70                    # CPU温度警告阈值
    CPU_TEMP_CRITICAL: int = 85                   # CPU温度危险阈值
    GPU_TEMP_WARNING: int = 75                    # GPU温度警告阈值
    GPU_TEMP_CRITICAL: int = 90                   # GPU温度危险阈值
    
    # 使用率阈值设置（百分比）
    CPU_USAGE_WARNING: int = 80                   # CPU使用率警告阈值
    CPU_USAGE_CRITICAL: int = 95                  # CPU使用率危险阈值
    MEMORY_USAGE_WARNING: int = 85                # 内存使用率警告阈值
    MEMORY_USAGE_CRITICAL: int = 95               # 内存使用率危险阈值
    
    # 悬浮窗设置
    ENABLE_OVERLAY_WINDOW: bool = False           # 是否默认启用悬浮窗
    OVERLAY_TRANSPARENCY: float = 0.8             # 悬浮窗透明度（0-1）
    OVERLAY_UPDATE_INTERVAL: int = 1              # 悬浮窗更新间隔（秒）
    
    # 显示项目配置
    SHOW_CPU_INFO: bool = True                    # 是否显示CPU信息
    SHOW_GPU_INFO: bool = True                    # 是否显示GPU信息
    SHOW_MEMORY_INFO: bool = True                 # 是否显示内存信息
    SHOW_DISK_INFO: bool = True                   # 是否显示硬盘信息
    SHOW_NETWORK_INFO: bool = True                # 是否显示网络信息


@dataclass
class RdpSettings:
    """
    远程桌面模块配置类
    
    定义远程桌面连接的各项参数，包括默认连接设置、历史记录管理、
    安全配置等。这些设置影响RDP连接的便利性和安全性。
    """
    
    # 默认连接参数
    DEFAULT_PORT: int = 3389                      # 默认RDP端口号
    DEFAULT_USERNAME: str = "Administrator"       # 默认用户名
    CONNECTION_TIMEOUT: int = 10                  # 连接超时时间（秒）
    
    # 历史记录设置
    MAX_HISTORY_COUNT: int = 100                  # 最大历史记录数量
    HISTORY_FILE_NAME: str = "rdp_history.json"  # 历史记录文件名
    ENCRYPT_HISTORY: bool = True                  # 是否加密历史记录
    AUTO_SAVE_HISTORY: bool = True                # 是否自动保存历史记录
    
    # 连接行为设置
    AUTO_CONNECT_ON_SAVE: bool = False            # 保存配置后是否自动连接
    REMEMBER_CREDENTIALS: bool = True             # 是否记住登录凭据
    SHOW_PASSWORD: bool = False                   # 是否默认显示密码
    
    # 分组管理设置
    DEFAULT_GROUP_NAME: str = "默认分组"          # 默认分组名称
    ENABLE_GROUP_MANAGEMENT: bool = True          # 是否启用分组管理
    MAX_GROUP_COUNT: int = 20                     # 最大分组数量


@dataclass
class LoggingSettings:
    """
    日志系统配置类
    
    定义日志记录的各项参数，包括日志级别、文件路径、轮转策略等。
    这些设置控制日志系统的详细程度和存储管理。
    """
    
    # 日志级别设置
    LOG_LEVEL: str = "INFO"                       # 默认日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）
    CONSOLE_LOG_LEVEL: str = "INFO"               # 控制台日志级别
    FILE_LOG_LEVEL: str = "DEBUG"                 # 文件日志级别
    
    # 日志文件设置
    LOG_DIR: str = "logs"                         # 日志文件存放目录
    LOG_FILE_NAME: str = "flowdesk.log"           # 主日志文件名
    ERROR_LOG_FILE_NAME: str = "error.log"        # 错误日志文件名
    
    # 日志轮转设置
    MAX_LOG_FILE_SIZE: int = 10 * 1024 * 1024     # 单个日志文件最大大小（10MB）
    MAX_LOG_FILE_COUNT: int = 5                   # 保留的日志文件数量
    LOG_ROTATION_ENABLED: bool = True             # 是否启用日志轮转
    
    # 日志格式设置
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # 日志格式
    DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"        # 时间格式
    
    # 调试设置
    ENABLE_DEBUG_MODE: bool = False               # 是否启用调试模式
    LOG_NETWORK_REQUESTS: bool = True             # 是否记录网络请求日志
    LOG_UI_EVENTS: bool = False                   # 是否记录UI事件日志


class Settings:
    """
    配置管理主类
    
    这个类负责管理FlowDesk应用程序的所有配置项，提供统一的配置访问接口。
    它整合了各个模块的配置类，并提供配置加载、保存、验证等功能。
    
    使用方法：
        settings = Settings()
        window_width = settings.app.WINDOW_WIDTH
        ping_timeout = settings.network.PING_TIMEOUT
    """
    
    def __init__(self):
        """
        初始化配置管理器
        
        创建各个模块的配置实例，并设置配置文件路径。
        这里使用了组合模式，将不同模块的配置组织在一起。
        """
        # 初始化各模块配置
        self.app = AppSettings()                  # 应用程序基础配置
        self.network = NetworkSettings()          # 网络模块配置
        self.hardware = HardwareSettings()        # 硬件监控配置
        self.rdp = RdpSettings()                  # 远程桌面配置
        self.logging = LoggingSettings()          # 日志系统配置
        
        # 设置项目根目录路径
        self.project_root = Path(__file__).parent.parent
        
        # 初始化路径配置
        self._init_paths()
    
    def _init_paths(self):
        """
        初始化各种路径配置
        
        根据项目结构设置各种资源文件的完整路径，确保应用程序
        能够正确找到所需的文件和目录。
        """
        # 设置完整的资源路径
        self.app.THEME_PATH = str(self.project_root / self.app.THEME_PATH)
        self.app.ICON_PATH = str(self.project_root / self.app.ICON_PATH)
        
        # 设置日志目录路径
        self.logging.LOG_DIR = str(self.project_root / self.logging.LOG_DIR)
        
        # 设置RDP历史记录文件路径
        rdp_history_path = self.project_root / "data" / self.rdp.HISTORY_FILE_NAME
        self.rdp.HISTORY_FILE_NAME = str(rdp_history_path)
    
    def get_theme_file_path(self) -> str:
        """
        获取当前主题的QSS文件完整路径
        
        Returns:
            str: QSS样式文件的完整路径
        """
        theme_file = f"{self.app.THEME_NAME}_pyqt5.qss"
        return str(Path(self.app.THEME_PATH) / theme_file)
    
    def get_icon_path(self, icon_name: str) -> str:
        """
        获取指定图标文件的完整路径
        
        Args:
            icon_name (str): 图标文件名
            
        Returns:
            str: 图标文件的完整路径
        """
        return str(Path(self.app.ICON_PATH) / icon_name)
    
    def validate_settings(self) -> bool:
        """
        验证配置项的有效性
        
        检查关键配置项是否合理，如窗口尺寸、超时时间、阈值等。
        这个方法在应用程序启动时调用，确保配置的正确性。
        
        Returns:
            bool: 配置是否有效
        """
        # 验证窗口尺寸
        if self.app.WINDOW_WIDTH < self.app.WINDOW_MIN_WIDTH:
            return False
        if self.app.WINDOW_HEIGHT < self.app.WINDOW_MIN_HEIGHT:
            return False
        
        # 验证超时设置
        if self.network.CONNECTION_TIMEOUT <= 0:
            return False
        if self.network.PING_TIMEOUT <= 0:
            return False
        
        # 验证温度阈值
        if self.hardware.CPU_TEMP_WARNING >= self.hardware.CPU_TEMP_CRITICAL:
            return False
        if self.hardware.GPU_TEMP_WARNING >= self.hardware.GPU_TEMP_CRITICAL:
            return False
        
        return True


# 全局配置实例
# 这个实例在整个应用程序中共享，提供统一的配置访问点
_settings_instance = None

def get_settings() -> Settings:
    """
    获取全局配置实例（单例模式）
    
    这个函数确保整个应用程序使用同一个配置实例，避免配置不一致的问题。
    第一次调用时创建配置实例，后续调用直接返回已创建的实例。
    
    Returns:
        Settings: 全局配置实例
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


# 导出主要的配置类和函数
__all__ = [
    'Settings',
    'AppSettings', 
    'NetworkSettings',
    'HardwareSettings',
    'RdpSettings',
    'LoggingSettings',
    'get_settings'
]
