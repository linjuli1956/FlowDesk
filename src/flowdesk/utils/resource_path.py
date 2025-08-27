"""
资源路径管理工具

提供FlowDesk应用程序的资源文件路径解析功能。
支持开发环境和打包环境的资源定位，确保图标、DLL等资源文件能够正确访问。

主要功能：
- 自动检测运行环境（开发环境 vs 打包环境）
- 提供统一的资源路径解析接口
- 支持相对路径和绝对路径转换
- 处理PyInstaller打包后的资源访问
- 提供资源文件存在性检查

使用示例：
    icon_path = resource_path("assets/icons/flowdesk.ico")
    dll_path = get_asset_path("LibreHardwareMonitor/LibreHardwareMonitorLib.dll")
"""

import os
import sys
from pathlib import Path


def get_base_path():
    """
    获取应用程序基础路径
    
    根据运行环境返回正确的基础路径：
    - 开发环境：返回项目根目录
    - 打包环境：返回PyInstaller临时目录
    
    返回:
        str: 应用程序基础路径
    """
    if getattr(sys, 'frozen', False):
        # 打包环境 - PyInstaller创建的临时目录
        base_path = sys._MEIPASS
    else:
        # 开发环境 - 项目根目录
        # 从当前文件位置向上查找项目根目录
        current_file = Path(__file__).resolve()
        # 当前文件路径: src/flowdesk/utils/resource_path.py
        # 项目根目录: 向上3级目录
        base_path = current_file.parent.parent.parent.parent
    
    return str(base_path)


def resource_path(relative_path):
    """
    获取资源文件的绝对路径
    
    将相对路径转换为绝对路径，支持开发环境和打包环境。
    自动处理路径分隔符的跨平台兼容性。
    
    参数:
        relative_path (str): 相对于项目根目录的资源路径
                           例如: "assets/icons/flowdesk.ico"
    
    返回:
        str: 资源文件的绝对路径
    
    示例:
        >>> resource_path("assets/icons/flowdesk.ico")
        "C:/Projects/FlowDesk/assets/icons/flowdesk.ico"
    """
    # 获取基础路径
    base_path = get_base_path()
    
    # 组合完整路径
    full_path = os.path.join(base_path, relative_path)
    
    # 规范化路径（处理路径分隔符）
    return os.path.normpath(full_path)


def get_asset_path(asset_relative_path):
    """
    获取assets目录下资源文件的绝对路径
    
    专门用于访问assets目录下的资源文件，
    是resource_path的便捷封装。
    
    参数:
        asset_relative_path (str): 相对于assets目录的路径
                                 例如: "icons/flowdesk.ico"
    
    返回:
        str: 资源文件的绝对路径
    
    示例:
        >>> get_asset_path("icons/flowdesk.ico")
        "C:/Projects/FlowDesk/assets/icons/flowdesk.ico"
    """
    return resource_path(f"assets/{asset_relative_path}")


def check_resource_exists(relative_path):
    """
    检查资源文件是否存在
    
    验证指定的资源文件是否存在于文件系统中。
    用于在使用资源前进行存在性检查。
    
    参数:
        relative_path (str): 相对于项目根目录的资源路径
    
    返回:
        bool: 如果文件存在返回True，否则返回False
    
    示例:
        >>> check_resource_exists("assets/icons/flowdesk.ico")
        True
    """
    full_path = resource_path(relative_path)
    return os.path.exists(full_path)


def get_config_path(config_filename):
    """
    获取配置文件的绝对路径
    
    专门用于访问config目录下的配置文件。
    
    参数:
        config_filename (str): 配置文件名
                             例如: "settings.json"
    
    返回:
        str: 配置文件的绝对路径
    """
    return resource_path(f"config/{config_filename}")


def get_logs_dir() -> str:
    """
    获取日志文件目录路径
    
    作用说明：
    返回应用程序日志文件的存储目录路径。
    在开发环境中使用项目根目录下的logs文件夹，
    在打包环境中使用用户数据目录下的logs文件夹。
    
    目录创建逻辑：
    - 如果目录不存在，会自动创建
    - 确保应用程序有写入权限
    - 提供跨平台的路径处理
    
    返回值：
        str: 日志目录的绝对路径
        
    使用示例：
        log_dir = get_logs_dir()
        log_file = os.path.join(log_dir, "flowdesk.log")
        print(f"日志文件路径: {log_file}")
    """
    try:
        if getattr(sys, 'frozen', False):
            # 打包环境：使用用户数据目录
            if platform.system() == "Windows":
                base_dir = os.path.expandvars(r'%APPDATA%\FlowDesk')
            else:
                base_dir = os.path.expanduser('~/.flowdesk')
        else:
            # 开发环境：使用项目根目录
            base_dir = get_project_root()
        
        log_dir = os.path.join(base_dir, 'logs')
        
        # 确保目录存在
        os.makedirs(log_dir, exist_ok=True)
        
        logger.debug(f"日志目录: {log_dir}")
        return log_dir
        
    except Exception as e:
        logger.error(f"获取日志目录失败: {e}")
        # 返回临时目录作为备选
        fallback_dir = os.path.join(tempfile.gettempdir(), 'FlowDesk', 'logs')
        os.makedirs(fallback_dir, exist_ok=True)
        return fallback_dir


def get_app_data_dir() -> str:
    """
    获取应用程序数据目录路径
    
    作用说明：
    返回应用程序配置文件和用户数据的存储目录路径。
    用于存储用户配置、缓存文件、临时数据等。
    
    目录选择逻辑：
    - Windows: %APPDATA%\\FlowDesk
    - Linux/macOS: ~/.flowdesk
    - 开发环境: 项目根目录/data
    
    返回值：
        str: 应用数据目录的绝对路径
        
    使用示例：
        data_dir = get_app_data_dir()
        config_file = os.path.join(data_dir, "config.ini")
        print(f"配置文件路径: {config_file}")
    """
    try:
        if getattr(sys, 'frozen', False):
            # 打包环境：使用用户数据目录
            if platform.system() == "Windows":
                data_dir = os.path.expandvars(r'%APPDATA%\FlowDesk')
            else:
                data_dir = os.path.expanduser('~/.flowdesk')
        else:
            # 开发环境：使用项目根目录下的data文件夹
            data_dir = os.path.join(get_project_root(), 'data')
        
        # 确保目录存在
        os.makedirs(data_dir, exist_ok=True)
        
        logger.debug(f"应用数据目录: {data_dir}")
        return data_dir
        
    except Exception as e:
        logger.error(f"获取应用数据目录失败: {e}")
        # 返回临时目录作为备选
        fallback_dir = os.path.join(tempfile.gettempdir(), 'FlowDesk', 'data')
        os.makedirs(fallback_dir, exist_ok=True)
        return fallback_dir


def get_log_path(log_filename):
    """
    获取日志文件的绝对路径
    
    返回日志文件的存储路径，通常在用户数据目录或临时目录。
    
    参数:
        log_filename (str): 日志文件名
                          例如: "flowdesk.log"
    
    返回:
        str: 日志文件的绝对路径
    """
    log_dir = get_logs_dir()
    return os.path.join(log_dir, log_filename)


def list_assets(asset_subdir=""):
    """
    列出assets目录下的所有文件
    
    用于调试和资源管理，列出指定子目录下的所有资源文件。
    
    参数:
        asset_subdir (str): assets下的子目录，默认为空（列出所有）
    
    返回:
        list: 资源文件路径列表
    """
    assets_path = resource_path(f"assets/{asset_subdir}")
    
    if not os.path.exists(assets_path):
        return []
    
    files = []
    for root, dirs, filenames in os.walk(assets_path):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            # 返回相对于assets目录的路径
            rel_path = os.path.relpath(file_path, resource_path("assets"))
            files.append(rel_path)
    
    return sorted(files)
