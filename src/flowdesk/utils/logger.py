"""
日志管理工具

提供FlowDesk应用程序的统一日志记录功能。
支持结构化日志记录、多级别日志输出、文件日志存储等功能。

主要功能：
- 统一的日志记录接口
- 多级别日志支持（DEBUG、INFO、WARNING、ERROR、CRITICAL）
- 文件日志输出和控制台日志输出
- 日志格式化和时间戳记录
- 日志文件轮转和大小控制
- 开发环境和生产环境的日志配置

使用示例：
    from flowdesk.utils.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info("应用程序启动")
    logger.error("发生错误", exc_info=True)
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path

from .resource_path import get_log_path


# 全局日志配置
_logger_initialized = False
_loggers = {}


def setup_logging(log_level=logging.INFO, enable_file_logging=True, enable_console_logging=True, verbose_mode=False):
    """
    设置应用程序的分级日志系统
    
    这是FlowDesk日志系统的核心配置函数，实现了专业的分级日志输出策略：
    - 控制台输出：只显示INFO级别及以上的重要信息，保持输出简洁
    - 文件输出：记录DEBUG级别及以上的所有详细信息，便于问题排查
    - 动态模式：支持verbose模式一键切换到详细调试输出
    
    分级策略说明：
    - 正常模式：控制台显示关键操作和错误，详细调试信息写入日志文件
    - 详细模式：控制台也显示DEBUG信息，适合开发调试使用
    - 文件日志：始终记录完整的调试信息，不受控制台级别影响
    
    参数:
        log_level (int): 根日志记录器的最低级别，默认为INFO
        enable_file_logging (bool): 是否启用文件日志记录，生产环境建议开启
        enable_console_logging (bool): 是否启用控制台日志显示，调试时建议开启
        verbose_mode (bool): 是否启用详细模式，True时控制台也显示DEBUG信息
    """
    global _logger_initialized
    
    if _logger_initialized:
        return
    
    # 设置根日志记录器的最低级别为DEBUG，确保所有级别的日志都能被处理
    # 具体的过滤由各个handler的级别设置来控制
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # 根记录器设为最低级别，由handler控制过滤
    
    # 清除可能存在的旧处理器，确保配置的纯净性
    root_logger.handlers.clear()
    
    # 创建统一的日志消息格式器，包含时间戳、模块名、级别等关键信息
    formatter = create_log_formatter()
    
    # 配置控制台日志处理器：根据verbose模式动态调整显示级别
    if enable_console_logging:
        console_handler = create_console_handler(formatter, verbose_mode)
        root_logger.addHandler(console_handler)
    
    # 配置文件日志处理器：始终记录详细的DEBUG级别信息
    if enable_file_logging:
        file_handler = create_file_handler(formatter)
        if file_handler:
            root_logger.addHandler(file_handler)
    
    # 配置第三方库的日志级别，避免过多的第三方调试信息干扰
    configure_third_party_loggers()
    
    _logger_initialized = True
    
    # 记录日志系统初始化完成状态，使用INFO级别确保在控制台可见
    logger = get_logger(__name__)
    mode_desc = "详细模式" if verbose_mode else "标准模式"
    logger.info(f"日志系统初始化完成 - {mode_desc}")


def create_log_formatter():
    """
    创建日志格式器
    
    定义日志消息的输出格式，包括时间戳、日志级别、
    模块名称、行号和日志消息等信息。
    
    返回:
        logging.Formatter: 配置好的日志格式器
    """
    # 定义日志格式
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "%(filename)s:%(lineno)d - %(message)s"
    )
    
    # 定义时间格式
    date_format = "%Y-%m-%d %H:%M:%S"
    
    return logging.Formatter(log_format, date_format)


def create_console_handler(formatter, verbose_mode=False):
    """
    创建智能控制台日志处理器
    
    这个函数负责创建向终端输出日志的处理器，是用户与程序交互的主要信息窗口。
    处理器会根据运行模式智能调整显示的信息量：
    
    - 标准模式（verbose_mode=False）：
      只显示INFO、WARNING、ERROR级别的信息，保持控制台整洁
      适合日常使用，用户只看到关键操作结果和错误提示
      
    - 详细模式（verbose_mode=True）：
      显示DEBUG及以上所有级别的信息，包含详细的调试过程
      适合开发调试，帮助开发者理解程序执行流程和定位问题
    
    设计理念：
    控制台是用户的直接交互界面，信息过多会造成干扰，信息过少会缺乏反馈。
    通过动态级别控制，在便利性和清晰性之间找到最佳平衡点。
    
    参数:
        formatter (logging.Formatter): 日志格式器，定义消息的显示格式
        verbose_mode (bool): 详细模式开关，True时显示DEBUG信息
        
    返回:
        logging.StreamHandler: 配置完成的控制台处理器
    """
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 根据verbose模式动态设置控制台日志级别
    # 这是分级日志的核心：同样的日志记录，不同级别的显示策略
    if verbose_mode:
        console_handler.setLevel(logging.DEBUG)  # 详细模式：显示所有调试信息
    else:
        console_handler.setLevel(logging.INFO)   # 标准模式：只显示重要信息
    
    return console_handler


def create_file_handler(formatter):
    """
    创建持久化文件日志处理器
    
    这个处理器负责将程序运行的完整日志信息保存到文件中，是问题排查的重要工具。
    与控制台处理器不同，文件处理器始终记录DEBUG级别及以上的所有信息，确保：
    
    功能特点：
    - 完整记录：保存所有DEBUG级别的详细调试信息，不受控制台显示级别影响
    - 自动轮转：当日志文件超过5MB时自动创建新文件，保留最近3个备份
    - 持久存储：程序关闭后日志信息仍然保留，便于事后分析问题
    - UTF-8编码：确保中文日志信息正确保存，避免乱码问题
    
    使用场景：
    - 生产环境问题排查：用户反馈问题时，可通过日志文件详细了解程序行为
    - 开发调试：即使控制台不显示DEBUG信息，文件中仍有完整的执行轨迹
    - 性能分析：通过详细的时间戳和执行流程分析程序性能瓶颈
    
    文件轮转策略：
    - flowdesk.log（当前文件）
    - flowdesk.log.1（上一个备份）
    - flowdesk.log.2（更早的备份）
    - flowdesk.log.3（最早的备份，超过后会被删除）
    
    参数:
        formatter (logging.Formatter): 日志格式器，定义文件中日志的格式
        
    返回:
        RotatingFileHandler: 配置完成的文件处理器，创建失败时返回None
    """
    try:
        log_file_path = get_log_path("flowdesk.log")
        
        # 创建旋转文件处理器，实现智能的日志文件管理
        # maxBytes=5MB：单个文件最大5兆字节，避免日志文件过大影响性能
        # backupCount=3：保留3个历史备份，平衡存储空间和历史信息保留
        # encoding='utf-8'：支持中文字符，确保日志内容完整可读
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        
        file_handler.setFormatter(formatter)
        # 文件日志始终设置为DEBUG级别，记录最详细的信息
        # 这是分级日志策略的核心：控制台简洁，文件详尽
        file_handler.setLevel(logging.DEBUG)
        
        return file_handler
        
    except Exception as e:
        # 使用print而不是logger，避免在日志系统初始化时产生循环依赖
        print(f"创建文件日志处理器失败: {e}")
        return None


def configure_third_party_loggers():
    """
    配置第三方库的日志级别
    
    设置第三方库（如PyQt5、requests等）的日志级别，
    避免过多的调试信息干扰应用程序日志。
    """
    # 设置PyQt5相关日志级别
    logging.getLogger("PyQt5").setLevel(logging.WARNING)
    
    # 设置其他第三方库日志级别
    third_party_loggers = [
        "urllib3",
        "requests",
        "PIL",
    ]
    
    for logger_name in third_party_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name):
    """
    获取指定名称的日志记录器
    
    为指定模块创建或获取日志记录器实例。
    使用模块的__name__作为参数可以自动获得层次化的日志记录器名称。
    
    参数:
        name (str): 日志记录器名称，通常使用__name__
    
    返回:
        logging.Logger: 日志记录器实例
    
    示例:
        >>> logger = get_logger(__name__)
        >>> logger.info("这是一条信息日志")
    """
    global _loggers
    
    # 如果日志系统未初始化，先进行初始化
    if not _logger_initialized:
        setup_logging()
    
    # 检查是否已经创建过该日志记录器
    if name in _loggers:
        return _loggers[name]
    
    # 创建新的日志记录器
    logger = logging.getLogger(name)
    _loggers[name] = logger
    
    return logger


def log_function_call(func):
    """
    函数调用日志装饰器
    
    用于记录函数的调用和执行时间，便于调试和性能分析。
    
    参数:
        func: 被装饰的函数
    
    返回:
        function: 装饰后的函数
    
    使用示例:
        @log_function_call
        def my_function():
            pass
    """
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        # 记录函数调用开始
        start_time = time.time()
        logger.debug(f"调用函数: {func.__name__}")
        
        try:
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 记录函数调用成功
            end_time = time.time()
            execution_time = end_time - start_time
            logger.debug(f"函数 {func.__name__} 执行完成，耗时: {execution_time:.3f}秒")
            
            return result
            
        except Exception as e:
            # 记录函数调用异常
            end_time = time.time()
            execution_time = end_time - start_time
            logger.error(f"函数 {func.__name__} 执行失败，耗时: {execution_time:.3f}秒，错误: {e}")
            raise
    
    return wrapper


def log_exception(logger, message="发生未处理的异常"):
    """
    记录异常信息的便捷函数
    
    记录异常的详细信息，包括异常类型、消息和堆栈跟踪。
    
    参数:
        logger (logging.Logger): 日志记录器实例
        message (str): 异常描述信息
    
    使用示例:
        try:
            risky_operation()
        except Exception:
            log_exception(logger, "执行危险操作时发生异常")
    """
    logger.error(message, exc_info=True)


def get_log_file_path():
    """
    获取当前日志文件的路径
    
    返回:
        str: 日志文件的绝对路径
    """
    return get_log_path("flowdesk.log")


def clear_old_logs(days_to_keep=30):
    """
    清理旧的日志文件
    
    删除超过指定天数的日志文件，节省磁盘空间。
    
    参数:
        days_to_keep (int): 保留日志文件的天数，默认30天
    """
    try:
        log_dir = os.path.dirname(get_log_file_path())
        current_time = datetime.now()
        
        for filename in os.listdir(log_dir):
            if filename.startswith("flowdesk.log"):
                file_path = os.path.join(log_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                
                # 计算文件年龄
                age_days = (current_time - file_time).days
                
                if age_days > days_to_keep:
                    os.remove(file_path)
                    print(f"删除旧日志文件: {filename}")
                    
    except Exception as e:
        print(f"清理旧日志文件失败: {e}")


def set_log_level(level):
    """
    动态设置日志级别
    
    在运行时调整日志记录的详细程度。
    
    参数:
        level (int): 日志级别（logging.DEBUG, INFO, WARNING, ERROR, CRITICAL）
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    logger = get_logger(__name__)
    logger.info(f"日志级别已设置为: {logging.getLevelName(level)}")
