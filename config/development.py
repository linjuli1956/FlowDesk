"""
FlowDesk 开发环境配置文件

这个文件定义了开发环境下的特殊配置，主要用于调试、测试和开发过程中的便利功能。
开发环境配置会覆盖基础配置中的相应项目，提供更详细的日志、调试信息和开发工具集成。

开发环境特点：
- 启用详细的调试日志和错误信息
- 缩短各种超时时间以加快开发测试
- 启用开发工具和调试功能
- 使用测试数据和模拟环境
- 放宽某些验证规则以便于测试
"""

from .settings import Settings, AppSettings, NetworkSettings, HardwareSettings, RdpSettings, LoggingSettings


class DevelopmentAppSettings(AppSettings):
    """
    开发环境应用程序设置
    
    继承基础应用设置，并针对开发环境进行调整。主要包括调试功能的启用、
    窗口行为的调整等，让开发者能够更方便地进行调试和测试。
    """
    
    # 调试和开发功能
    ENABLE_DEBUG_MODE: bool = True                # 启用调试模式，显示更多调试信息
    SHOW_DEBUG_MENU: bool = True                  # 显示调试菜单，提供开发工具访问
    ENABLE_HOT_RELOAD: bool = True                # 启用热重载，QSS样式修改后自动刷新
    SHOW_PERFORMANCE_METRICS: bool = True        # 显示性能指标，监控应用程序性能
    
    # 窗口调试设置
    WINDOW_ALWAYS_ON_TOP: bool = False            # 开发时不强制窗口置顶，便于切换工具
    ENABLE_WINDOW_RESIZE_DEBUG: bool = True       # 启用窗口调整调试信息
    SHOW_WIDGET_BORDERS: bool = False             # 是否显示组件边框（调试布局用）
    
    # 开发环境标识
    ENVIRONMENT: str = "development"              # 环境标识，用于日志和错误报告
    SHOW_ENVIRONMENT_INDICATOR: bool = True       # 在界面上显示环境标识


class DevelopmentNetworkSettings(NetworkSettings):
    """
    开发环境网络设置
    
    针对开发环境调整网络相关参数，主要是缩短超时时间、启用详细日志、
    使用测试目标等，让开发者能够快速验证网络功能。
    """
    
    # 缩短超时时间以加快开发测试
    CONNECTION_TIMEOUT: int = 3                   # 连接超时3秒（比生产环境短）
    PING_TIMEOUT: int = 2                         # Ping超时2秒，快速得到结果
    PING_COUNT: int = 2                           # 减少Ping次数，加快测试速度
    MAX_RETRY_COUNT: int = 2                      # 减少重试次数，快速失败
    
    # 开发测试用的网络目标
    DEFAULT_PING_TARGET: str = "127.0.0.1"       # 使用本地回环地址进行快速测试
    TEST_EXTERNAL_TARGET: str = "8.8.8.8"        # 外部连通性测试目标
    
    # 开发环境网络监控
    NETWORK_CHECK_INTERVAL: int = 10              # 更频繁的网络状态检查（10秒）
    ENABLE_NETWORK_SIMULATION: bool = True        # 启用网络状况模拟（测试用）
    LOG_ALL_NETWORK_OPERATIONS: bool = True       # 记录所有网络操作的详细日志
    
    # 宽松的验证规则
    STRICT_IP_VALIDATION: bool = False            # 关闭严格验证，便于测试各种IP
    ALLOW_TEST_IP_RANGES: bool = True             # 允许测试IP范围（如192.0.2.x）


class DevelopmentHardwareSettings(HardwareSettings):
    """
    开发环境硬件监控设置
    
    调整硬件监控参数以适应开发环境，主要是更频繁的更新、详细的日志、
    模拟数据等，便于开发和测试硬件监控功能。
    """
    
    # 更频繁的刷新以便观察变化
    REFRESH_INTERVAL: int = 1                     # 1秒刷新一次，便于观察实时变化
    OVERLAY_UPDATE_INTERVAL: int = 1              # 悬浮窗也1秒更新一次
    
    # 降低阈值以便触发警告（测试用）
    CPU_TEMP_WARNING: int = 50                    # 降低CPU温度警告阈值便于测试
    CPU_TEMP_CRITICAL: int = 70                   # 降低危险阈值
    GPU_TEMP_WARNING: int = 55                    # 降低GPU温度阈值
    GPU_TEMP_CRITICAL: int = 75                   # 降低GPU危险阈值
    
    CPU_USAGE_WARNING: int = 60                   # 降低CPU使用率警告阈值
    CPU_USAGE_CRITICAL: int = 80                  # 降低危险阈值
    MEMORY_USAGE_WARNING: int = 70                # 降低内存使用率阈值
    MEMORY_USAGE_CRITICAL: int = 85               # 降低内存危险阈值
    
    # 开发调试功能
    ENABLE_HARDWARE_SIMULATION: bool = True       # 启用硬件数据模拟（无硬件时测试用）
    LOG_HARDWARE_DATA: bool = True                # 记录硬件数据到日志文件
    SHOW_RAW_SENSOR_DATA: bool = True             # 显示原始传感器数据（调试用）
    ENABLE_PERFORMANCE_PROFILING: bool = True     # 启用性能分析


class DevelopmentRdpSettings(RdpSettings):
    """
    开发环境远程桌面设置
    
    调整RDP相关参数以适应开发测试，包括测试连接参数、简化的历史记录、
    调试功能等。
    """
    
    # 开发测试用的默认值
    DEFAULT_PORT: int = 3389                      # 保持标准端口
    DEFAULT_USERNAME: str = "testuser"            # 使用测试用户名
    CONNECTION_TIMEOUT: int = 5                   # 较短的连接超时
    
    # 简化的历史记录管理
    MAX_HISTORY_COUNT: int = 20                   # 减少历史记录数量
    HISTORY_FILE_NAME: str = "rdp_history_dev.json"  # 使用开发环境专用历史文件
    ENCRYPT_HISTORY: bool = False                 # 开发环境不加密，便于调试
    
    # 开发便利功能
    AUTO_FILL_LOCAL_IP: bool = True               # 自动填充本机IP地址
    SHOW_CONNECTION_DEBUG_INFO: bool = True       # 显示连接调试信息
    ENABLE_CONNECTION_LOGGING: bool = True        # 启用连接日志记录
    ALLOW_INSECURE_CONNECTIONS: bool = True       # 允许不安全连接（测试用）


class DevelopmentLoggingSettings(LoggingSettings):
    """
    开发环境日志设置
    
    配置详细的日志记录以便于开发调试，包括更低的日志级别、更详细的格式、
    更多的日志类型等。
    """
    
    # 详细的日志级别
    LOG_LEVEL: str = "DEBUG"                      # 开发环境使用DEBUG级别
    CONSOLE_LOG_LEVEL: str = "DEBUG"              # 控制台也显示DEBUG信息
    FILE_LOG_LEVEL: str = "DEBUG"                 # 文件记录所有DEBUG信息
    
    # 开发环境专用日志文件
    LOG_FILE_NAME: str = "flowdesk_dev.log"       # 开发环境专用日志文件
    ERROR_LOG_FILE_NAME: str = "error_dev.log"    # 开发环境错误日志
    
    # 更小的文件大小以便于查看
    MAX_LOG_FILE_SIZE: int = 5 * 1024 * 1024      # 5MB文件大小限制
    MAX_LOG_FILE_COUNT: int = 3                   # 保留3个日志文件
    
    # 详细的日志格式（包含更多调试信息）
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s"
    
    # 开发调试功能
    ENABLE_DEBUG_MODE: bool = True                # 启用调试模式
    LOG_NETWORK_REQUESTS: bool = True             # 记录所有网络请求
    LOG_UI_EVENTS: bool = True                    # 记录UI事件（开发环境启用）
    LOG_PERFORMANCE_METRICS: bool = True          # 记录性能指标
    LOG_MEMORY_USAGE: bool = True                 # 记录内存使用情况
    
    # 实时日志查看
    ENABLE_LOG_VIEWER: bool = True                # 启用内置日志查看器
    AUTO_SCROLL_LOGS: bool = True                 # 日志自动滚动到最新


class DevelopmentConfig(Settings):
    """
    开发环境配置管理类
    
    这个类整合了所有开发环境的配置设置，覆盖基础配置中的相应项目。
    开发环境配置主要用于提供更好的开发体验和调试功能。
    
    使用方法：
        config = DevelopmentConfig()
        # 配置会自动应用开发环境的所有设置
    """
    
    def __init__(self):
        """
        初始化开发环境配置
        
        使用开发环境专用的配置类替换基础配置，确保所有模块都使用
        适合开发环境的参数设置。
        """
        # 不调用父类初始化，直接使用开发环境配置
        self.app = DevelopmentAppSettings()          # 开发环境应用设置
        self.network = DevelopmentNetworkSettings()  # 开发环境网络设置
        self.hardware = DevelopmentHardwareSettings()  # 开发环境硬件设置
        self.rdp = DevelopmentRdpSettings()          # 开发环境RDP设置
        self.logging = DevelopmentLoggingSettings()  # 开发环境日志设置
        
        # 设置项目根目录路径
        from pathlib import Path
        self.project_root = Path(__file__).parent.parent
        
        # 初始化开发环境专用路径
        self._init_development_paths()
    
    def _init_development_paths(self):
        """
        初始化开发环境专用路径
        
        设置开发环境下的特殊路径，如开发日志目录、测试数据目录等。
        这些路径与生产环境分离，避免开发数据污染生产环境。
        """
        # 开发环境专用日志目录
        dev_log_dir = self.project_root / "logs" / "development"
        self.logging.LOG_DIR = str(dev_log_dir)
        
        # 开发环境专用数据目录
        dev_data_dir = self.project_root / "data" / "development"
        rdp_history_path = dev_data_dir / self.rdp.HISTORY_FILE_NAME
        self.rdp.HISTORY_FILE_NAME = str(rdp_history_path)
        
        # 确保开发环境目录存在
        dev_log_dir.mkdir(parents=True, exist_ok=True)
        dev_data_dir.mkdir(parents=True, exist_ok=True)
    
    def enable_debug_features(self):
        """
        启用所有调试功能
        
        这个方法会启用所有可用的调试和开发功能，包括详细日志、
        性能监控、调试菜单等。通常在开发阶段调用。
        """
        self.app.ENABLE_DEBUG_MODE = True
        self.app.SHOW_DEBUG_MENU = True
        self.app.SHOW_PERFORMANCE_METRICS = True
        self.logging.LOG_UI_EVENTS = True
        self.logging.LOG_PERFORMANCE_METRICS = True
        self.hardware.ENABLE_PERFORMANCE_PROFILING = True
        self.rdp.SHOW_CONNECTION_DEBUG_INFO = True
    
    def get_debug_info(self) -> dict:
        """
        获取调试信息
        
        返回当前配置的调试相关信息，用于开发工具显示或日志记录。
        
        Returns:
            dict: 包含调试信息的字典
        """
        return {
            "environment": self.app.ENVIRONMENT,
            "debug_mode": self.app.ENABLE_DEBUG_MODE,
            "log_level": self.logging.LOG_LEVEL,
            "refresh_interval": self.hardware.REFRESH_INTERVAL,
            "connection_timeout": self.network.CONNECTION_TIMEOUT,
            "log_directory": self.logging.LOG_DIR,
            "data_directory": str(self.project_root / "data" / "development")
        }


# 创建开发环境配置实例的便捷函数
def create_development_config() -> DevelopmentConfig:
    """
    创建开发环境配置实例
    
    这个函数提供了创建开发环境配置的便捷方式，并自动启用
    所有适合开发环境的功能。
    
    Returns:
        DevelopmentConfig: 配置好的开发环境配置实例
    """
    config = DevelopmentConfig()
    config.enable_debug_features()  # 自动启用调试功能
    return config


# 导出开发环境配置相关的类和函数
__all__ = [
    'DevelopmentConfig',
    'DevelopmentAppSettings',
    'DevelopmentNetworkSettings', 
    'DevelopmentHardwareSettings',
    'DevelopmentRdpSettings',
    'DevelopmentLoggingSettings',
    'create_development_config'
]
