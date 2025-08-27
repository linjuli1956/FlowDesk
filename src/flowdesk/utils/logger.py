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


def setup_logging(log_level=logging.INFO, enable_file_logging=True, enable_console_logging=True):
    """
    设置应用程序的日志系统
    
    配置日志记录器的基本参数，包括日志级别、输出目标、格式等。
    应该在应用程序启动时调用一次。
    
    参数:
        log_level (int): 日志级别，默认为INFO
        enable_file_logging (bool): 是否启用文件日志，默认True
        enable_console_logging (bool): 是否启用控制台日志，默认True
    """
    global _logger_initialized
    
    if _logger_initialized:
        return
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除现有的处理器
    root_logger.handlers.clear()
    
    # 创建日志格式器
    formatter = create_log_formatter()
    
    # 设置控制台日志处理器
    if enable_console_logging:
        console_handler = create_console_handler(formatter)
        root_logger.addHandler(console_handler)
    
    # 设置文件日志处理器
    if enable_file_logging:
        file_handler = create_file_handler(formatter)
        if file_handler:
            root_logger.addHandler(file_handler)
    
    # 设置第三方库的日志级别
    configure_third_party_loggers()
    
    _logger_initialized = True
    
    # 记录日志系统初始化完成
    logger = get_logger(__name__)
    logger.info("日志系统初始化完成")


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


def create_console_handler(formatter):
    """
    创建控制台日志处理器
    
    配置输出到控制台（stdout）的日志处理器。
    
    参数:
        formatter (logging.Formatter): 日志格式器
    
    返回:
        logging.StreamHandler: 控制台日志处理器
    """
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    return console_handler


def create_file_handler(formatter):
    """
    创建文件日志处理器
    
    配置输出到文件的日志处理器，支持日志文件轮转。
    
    参数:
        formatter (logging.Formatter): 日志格式器
    
    返回:
        logging.Handler: 文件日志处理器，如果创建失败返回None
    """
    try:
        # 获取日志文件路径
        log_file_path = get_log_path("flowdesk.log")
        
        # 创建轮转文件处理器
        # 最大文件大小10MB，保留5个备份文件
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)  # 文件日志记录更详细的信息
        
        return file_handler
        
    except Exception as e:
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
