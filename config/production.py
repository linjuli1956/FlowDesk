"""
FlowDesk 生产环境配置文件

这个文件定义了生产环境下的配置，主要关注性能优化、稳定性、安全性和用户体验。
生产环境配置会覆盖基础配置中的相应项目，提供更稳定的运行参数和更好的用户体验。

生产环境特点：
- 优化性能和资源使用
- 提高系统稳定性和可靠性
- 加强安全性和数据保护
- 简化用户界面，隐藏调试信息
- 使用合理的超时和重试策略
"""

from .settings import Settings, AppSettings, NetworkSettings, HardwareSettings, RdpSettings, LoggingSettings


class ProductionAppSettings(AppSettings):
    """
    生产环境应用程序设置
    
    继承基础应用设置，并针对生产环境进行优化。主要包括性能优化、
    用户体验改进、稳定性增强等，确保应用程序在最终用户环境中稳定运行。
    """
    
    # 生产环境标识和优化
    ENVIRONMENT: str = "production"               # 环境标识，用于日志和错误报告
    ENABLE_DEBUG_MODE: bool = False               # 生产环境关闭调试模式
    SHOW_DEBUG_MENU: bool = False                 # 隐藏调试菜单，简化用户界面
    ENABLE_HOT_RELOAD: bool = False               # 关闭热重载，提高稳定性
    SHOW_PERFORMANCE_METRICS: bool = False        # 隐藏性能指标，避免干扰用户
    
    # 用户体验优化
    WINDOW_ALWAYS_ON_TOP: bool = False            # 不强制窗口置顶，让用户自由控制
    ENABLE_WINDOW_RESIZE_DEBUG: bool = False      # 关闭窗口调整调试信息
    SHOW_WIDGET_BORDERS: bool = False             # 隐藏组件边框，保持界面美观
    SHOW_ENVIRONMENT_INDICATOR: bool = False      # 不显示环境标识
    
    # 性能和稳定性优化
    ENABLE_ANIMATIONS: bool = True                # 保持动画效果，提升用户体验
    ANIMATION_DURATION: int = 150                 # 稍微缩短动画时间，提高响应速度
    
    # 错误处理和恢复
    ENABLE_CRASH_REPORTING: bool = True           # 启用崩溃报告，帮助改进软件
    AUTO_SAVE_SETTINGS: bool = True               # 自动保存用户设置
    BACKUP_SETTINGS_ON_START: bool = True         # 启动时备份设置文件


class ProductionNetworkSettings(NetworkSettings):
    """
    生产环境网络设置
    
    针对生产环境优化网络参数，主要关注稳定性和可靠性，使用更保守的
    超时时间和重试策略，确保网络操作在各种环境下都能稳定工作。
    """
    
    # 保守的超时设置，确保稳定性
    CONNECTION_TIMEOUT: int = 8                   # 较长的连接超时，适应不同网络环境
    PING_TIMEOUT: int = 4                         # 4秒Ping超时，确保准确性
    PING_COUNT: int = 4                           # 标准的4次Ping，获得可靠结果
    MAX_RETRY_COUNT: int = 3                      # 3次重试，平衡可靠性和响应速度
    
    # 生产环境网络目标
    DEFAULT_PING_TARGET: str = "www.baidu.com"   # 使用可靠的外部目标
    FALLBACK_PING_TARGET: str = "8.8.8.8"        # 备用Ping目标
    
    # 网络监控优化
    NETWORK_CHECK_INTERVAL: int = 60              # 1分钟检查一次，减少资源消耗
    ENABLE_NETWORK_SIMULATION: bool = False       # 关闭网络模拟功能
    LOG_ALL_NETWORK_OPERATIONS: bool = False      # 不记录所有操作，减少日志量
    
    # 严格的验证规则
    STRICT_IP_VALIDATION: bool = True             # 启用严格IP验证，提高安全性
    ALLOW_TEST_IP_RANGES: bool = False            # 不允许测试IP范围
    VALIDATE_DNS_SERVERS: bool = True             # 验证DNS服务器有效性
    
    # 网络安全设置
    ENABLE_NETWORK_SECURITY_CHECK: bool = True    # 启用网络安全检查
    BLOCK_PRIVATE_DNS: bool = False               # 允许私有DNS（企业环境常用）
    WARN_ON_INSECURE_CONNECTIONS: bool = True     # 警告不安全连接


class ProductionHardwareSettings(HardwareSettings):
    """
    生产环境硬件监控设置
    
    优化硬件监控参数以平衡功能性和性能，使用合理的刷新频率和阈值，
    确保监控功能不会对系统性能造成明显影响。
    """
    
    # 平衡的刷新频率
    REFRESH_INTERVAL: int = 3                     # 3秒刷新，平衡实时性和性能
    OVERLAY_UPDATE_INTERVAL: int = 2              # 悬浮窗2秒更新，减少资源消耗
    
    # 合理的温度阈值（基于实际硬件规格）
    CPU_TEMP_WARNING: int = 75                    # CPU温度警告阈值
    CPU_TEMP_CRITICAL: int = 90                   # CPU危险温度阈值
    GPU_TEMP_WARNING: int = 80                    # GPU温度警告阈值
    GPU_TEMP_CRITICAL: int = 95                   # GPU危险温度阈值
    
    # 合理的使用率阈值
    CPU_USAGE_WARNING: int = 85                   # CPU使用率警告阈值
    CPU_USAGE_CRITICAL: int = 95                  # CPU危险使用率
    MEMORY_USAGE_WARNING: int = 90                # 内存使用率警告阈值
    MEMORY_USAGE_CRITICAL: int = 98               # 内存危险使用率
    
    # 生产环境优化
    ENABLE_HARDWARE_SIMULATION: bool = False      # 关闭硬件模拟，使用真实数据
    LOG_HARDWARE_DATA: bool = False               # 不记录详细硬件数据，减少日志
    SHOW_RAW_SENSOR_DATA: bool = False            # 隐藏原始传感器数据
    ENABLE_PERFORMANCE_PROFILING: bool = False    # 关闭性能分析，减少开销
    
    # 用户体验优化
    ENABLE_SMART_NOTIFICATIONS: bool = True       # 启用智能通知（避免频繁提醒）
    NOTIFICATION_COOLDOWN: int = 300              # 通知冷却时间（5分钟）
    AUTO_HIDE_NORMAL_VALUES: bool = True          # 自动隐藏正常值，突出异常
    
    # 悬浮窗优化
    OVERLAY_TRANSPARENCY: float = 0.85            # 稍高透明度，减少干扰
    OVERLAY_AUTO_HIDE: bool = True                # 无活动时自动隐藏悬浮窗
    OVERLAY_HIDE_DELAY: int = 30                  # 30秒后自动隐藏


class ProductionRdpSettings(RdpSettings):
    """
    生产环境远程桌面设置
    
    优化RDP功能以提供更好的安全性和用户体验，包括加强的安全措施、
    更好的连接管理和用户友好的默认设置。
    """
    
    # 标准的连接参数
    DEFAULT_PORT: int = 3389                      # 标准RDP端口
    DEFAULT_USERNAME: str = "Administrator"       # 标准管理员用户名
    CONNECTION_TIMEOUT: int = 15                  # 较长超时，适应不同网络环境
    
    # 增强的历史记录管理
    MAX_HISTORY_COUNT: int = 200                  # 更多历史记录，方便用户使用
    HISTORY_FILE_NAME: str = "rdp_history.json"  # 标准历史文件名
    ENCRYPT_HISTORY: bool = True                  # 加密历史记录，保护敏感信息
    AUTO_SAVE_HISTORY: bool = True                # 自动保存，防止数据丢失
    
    # 安全性增强
    ALLOW_INSECURE_CONNECTIONS: bool = False      # 不允许不安全连接
    REQUIRE_CERTIFICATE_VALIDATION: bool = True   # 要求证书验证
    ENABLE_CONNECTION_ENCRYPTION: bool = True     # 启用连接加密
    WARN_ON_WEAK_PASSWORDS: bool = True           # 警告弱密码
    
    # 用户体验优化
    AUTO_FILL_LOCAL_IP: bool = True               # 自动填充本机IP，提高便利性
    REMEMBER_WINDOW_SIZE: bool = True             # 记住窗口大小
    ENABLE_CONNECTION_PROFILES: bool = True       # 启用连接配置文件
    SHOW_CONNECTION_STATUS: bool = True           # 显示连接状态
    
    # 连接优化
    ENABLE_CONNECTION_POOLING: bool = True        # 启用连接池，提高性能
    MAX_CONCURRENT_CONNECTIONS: int = 5           # 最大并发连接数
    CONNECTION_KEEP_ALIVE: bool = True            # 保持连接活跃
    AUTO_RECONNECT_ON_FAILURE: bool = True        # 连接失败时自动重连


class ProductionLoggingSettings(LoggingSettings):
    """
    生产环境日志设置
    
    配置适合生产环境的日志记录，平衡信息详细程度和性能影响，
    确保能够记录重要信息同时不影响应用程序性能。
    """
    
    # 适中的日志级别
    LOG_LEVEL: str = "INFO"                       # INFO级别，记录重要信息
    CONSOLE_LOG_LEVEL: str = "WARNING"            # 控制台只显示警告和错误
    FILE_LOG_LEVEL: str = "INFO"                  # 文件记录INFO及以上级别
    
    # 生产环境日志文件
    LOG_FILE_NAME: str = "flowdesk.log"           # 标准日志文件名
    ERROR_LOG_FILE_NAME: str = "error.log"        # 错误日志文件
    AUDIT_LOG_FILE_NAME: str = "audit.log"        # 审计日志文件（新增）
    
    # 合理的文件大小和保留策略
    MAX_LOG_FILE_SIZE: int = 20 * 1024 * 1024     # 20MB文件大小限制
    MAX_LOG_FILE_COUNT: int = 10                  # 保留10个历史文件
    LOG_ROTATION_ENABLED: bool = True             # 启用日志轮转
    
    # 简洁的日志格式
    LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    ERROR_LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(message)s"
    
    # 生产环境日志策略
    ENABLE_DEBUG_MODE: bool = False               # 关闭调试模式
    LOG_NETWORK_REQUESTS: bool = False            # 不记录所有网络请求
    LOG_UI_EVENTS: bool = False                   # 不记录UI事件
    LOG_PERFORMANCE_METRICS: bool = False         # 不记录性能指标
    LOG_MEMORY_USAGE: bool = False                # 不记录内存使用
    
    # 错误和审计日志
    ENABLE_ERROR_REPORTING: bool = True           # 启用错误报告
    ENABLE_AUDIT_LOGGING: bool = True             # 启用审计日志
    LOG_USER_ACTIONS: bool = True                 # 记录用户重要操作
    LOG_SYSTEM_CHANGES: bool = True               # 记录系统配置更改
    
    # 日志安全和隐私
    MASK_SENSITIVE_DATA: bool = True              # 掩码敏感数据（IP、密码等）
    ENABLE_LOG_ENCRYPTION: bool = False           # 可选的日志加密
    LOG_RETENTION_DAYS: int = 30                  # 日志保留30天


class ProductionConfig(Settings):
    """
    生产环境配置管理类
    
    这个类整合了所有生产环境的配置设置，覆盖基础配置中的相应项目。
    生产环境配置主要关注稳定性、性能、安全性和用户体验。
    
    使用方法：
        config = ProductionConfig()
        # 配置会自动应用生产环境的所有优化设置
    """
    
    def __init__(self):
        """
        初始化生产环境配置
        
        使用生产环境专用的配置类替换基础配置，确保所有模块都使用
        适合生产环境的优化参数。
        """
        # 使用生产环境专用配置
        self.app = ProductionAppSettings()          # 生产环境应用设置
        self.network = ProductionNetworkSettings()  # 生产环境网络设置
        self.hardware = ProductionHardwareSettings()  # 生产环境硬件设置
        self.rdp = ProductionRdpSettings()          # 生产环境RDP设置
        self.logging = ProductionLoggingSettings()  # 生产环境日志设置
        
        # 设置项目根目录路径
        from pathlib import Path
        self.project_root = Path(__file__).parent.parent
        
        # 初始化生产环境路径
        self._init_production_paths()
        
        # 应用生产环境优化
        self._apply_production_optimizations()
    
    def _init_production_paths(self):
        """
        初始化生产环境路径
        
        设置生产环境下的标准路径，确保数据文件、日志文件等存储在
        合适的位置，并具有适当的权限和安全性。
        """
        # 生产环境日志目录
        log_dir = self.project_root / "logs"
        self.logging.LOG_DIR = str(log_dir)
        
        # 生产环境数据目录
        data_dir = self.project_root / "data"
        rdp_history_path = data_dir / self.rdp.HISTORY_FILE_NAME
        self.rdp.HISTORY_FILE_NAME = str(rdp_history_path)
        
        # 确保目录存在
        log_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置备份目录
        backup_dir = self.project_root / "backup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        self.backup_directory = str(backup_dir)
    
    def _apply_production_optimizations(self):
        """
        应用生产环境优化设置
        
        这个方法会应用各种生产环境优化，包括性能调优、安全加固、
        用户体验改进等。
        """
        # 性能优化
        self.hardware.REFRESH_INTERVAL = max(self.hardware.REFRESH_INTERVAL, 2)  # 最少2秒刷新
        self.network.NETWORK_CHECK_INTERVAL = max(self.network.NETWORK_CHECK_INTERVAL, 30)  # 最少30秒检查
        
        # 安全加固
        self.rdp.ENCRYPT_HISTORY = True
        self.logging.MASK_SENSITIVE_DATA = True
        
        # 用户体验优化
        self.app.ENABLE_ANIMATIONS = True
        self.hardware.ENABLE_SMART_NOTIFICATIONS = True
    
    def create_backup(self) -> str:
        """
        创建配置备份
        
        在生产环境中定期备份重要配置和数据，防止数据丢失。
        
        Returns:
            str: 备份文件路径
        """
        import json
        import datetime
        from pathlib import Path
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = Path(self.backup_directory) / f"config_backup_{timestamp}.json"
        
        # 创建配置备份数据
        backup_data = {
            "timestamp": timestamp,
            "environment": "production",
            "app_settings": {
                "window_width": self.app.WINDOW_WIDTH,
                "window_height": self.app.WINDOW_HEIGHT,
                "theme_name": self.app.THEME_NAME
            },
            "network_settings": {
                "connection_timeout": self.network.CONNECTION_TIMEOUT,
                "default_dns_primary": self.network.DEFAULT_DNS_PRIMARY,
                "default_dns_secondary": self.network.DEFAULT_DNS_SECONDARY
            }
        }
        
        # 保存备份文件
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        return str(backup_file)
    
    def get_system_info(self) -> dict:
        """
        获取系统信息
        
        返回当前系统和配置的基本信息，用于故障诊断和支持。
        
        Returns:
            dict: 包含系统信息的字典
        """
        import platform
        import sys
        
        return {
            "environment": self.app.ENVIRONMENT,
            "app_version": self.app.APP_VERSION,
            "python_version": sys.version,
            "platform": platform.platform(),
            "log_level": self.logging.LOG_LEVEL,
            "theme": self.app.THEME_NAME,
            "window_size": f"{self.app.WINDOW_WIDTH}x{self.app.WINDOW_HEIGHT}",
            "config_valid": self.validate_settings()
        }


# 创建生产环境配置实例的便捷函数
def create_production_config() -> ProductionConfig:
    """
    创建生产环境配置实例
    
    这个函数提供了创建生产环境配置的便捷方式，并自动应用
    所有生产环境优化设置。
    
    Returns:
        ProductionConfig: 配置好的生产环境配置实例
    """
    config = ProductionConfig()
    return config


# 导出生产环境配置相关的类和函数
__all__ = [
    'ProductionConfig',
    'ProductionAppSettings',
    'ProductionNetworkSettings',
    'ProductionHardwareSettings', 
    'ProductionRdpSettings',
    'ProductionLoggingSettings',
    'create_production_config'
]
