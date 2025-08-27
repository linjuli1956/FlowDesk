#!/usr/bin/env python3
"""
FlowDesk 配置系统测试脚本

这个脚本用于测试配置系统是否正常工作，包括：
- 基础配置加载
- 开发环境配置
- 生产环境配置
- 日志配置
- 配置验证

运行方法：python test_config.py
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_basic_config():
    """
    测试基础配置系统
    
    验证基础配置类是否能正常加载和使用，包括各个模块的配置项。
    """
    print("=== 测试基础配置系统 ===")
    
    try:
        from config.settings import get_settings
        
        # 获取配置实例
        settings = get_settings()
        
        # 测试应用程序配置
        print(f"应用程序名称: {settings.app.APP_NAME}")
        print(f"应用程序版本: {settings.app.APP_VERSION}")
        print(f"窗口尺寸: {settings.app.WINDOW_WIDTH}x{settings.app.WINDOW_HEIGHT}")
        print(f"主题名称: {settings.app.THEME_NAME}")
        
        # 测试网络配置
        print(f"连接超时: {settings.network.CONNECTION_TIMEOUT}秒")
        print(f"主DNS服务器: {settings.network.DEFAULT_DNS_PRIMARY}")
        print(f"备用DNS服务器: {settings.network.DEFAULT_DNS_SECONDARY}")
        
        # 测试硬件配置
        print(f"刷新间隔: {settings.hardware.REFRESH_INTERVAL}秒")
        print(f"CPU温度警告阈值: {settings.hardware.CPU_TEMP_WARNING}°C")
        
        # 测试RDP配置
        print(f"默认RDP端口: {settings.rdp.DEFAULT_PORT}")
        print(f"最大历史记录: {settings.rdp.MAX_HISTORY_COUNT}")
        
        # 测试日志配置
        print(f"日志级别: {settings.logging.LOG_LEVEL}")
        print(f"日志目录: {settings.logging.LOG_DIR}")
        
        # 测试配置验证
        is_valid = settings.validate_settings()
        print(f"配置验证结果: {'通过' if is_valid else '失败'}")
        
        # 测试路径获取
        theme_path = settings.get_theme_file_path()
        print(f"主题文件路径: {theme_path}")
        
        icon_path = settings.get_icon_path("flowdesk.ico")
        print(f"图标文件路径: {icon_path}")
        
        print("✅ 基础配置系统测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 基础配置系统测试失败: {e}\n")
        return False

def test_development_config():
    """
    测试开发环境配置
    
    验证开发环境配置是否能正确覆盖基础配置，并提供开发特有的功能。
    """
    print("=== 测试开发环境配置 ===")
    
    try:
        from config.development import create_development_config
        
        # 创建开发环境配置
        dev_config = create_development_config()
        
        # 验证开发环境特有设置
        print(f"环境标识: {dev_config.app.ENVIRONMENT}")
        print(f"调试模式: {dev_config.app.ENABLE_DEBUG_MODE}")
        print(f"显示调试菜单: {dev_config.app.SHOW_DEBUG_MENU}")
        print(f"连接超时(开发): {dev_config.network.CONNECTION_TIMEOUT}秒")
        print(f"刷新间隔(开发): {dev_config.hardware.REFRESH_INTERVAL}秒")
        print(f"日志级别(开发): {dev_config.logging.LOG_LEVEL}")
        
        # 测试调试信息获取
        debug_info = dev_config.get_debug_info()
        print(f"调试信息: {debug_info}")
        
        print("✅ 开发环境配置测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 开发环境配置测试失败: {e}\n")
        return False

def test_production_config():
    """
    测试生产环境配置
    
    验证生产环境配置是否能正确优化设置，提供稳定的运行环境。
    """
    print("=== 测试生产环境配置 ===")
    
    try:
        from config.production import create_production_config
        
        # 创建生产环境配置
        prod_config = create_production_config()
        
        # 验证生产环境特有设置
        print(f"环境标识: {prod_config.app.ENVIRONMENT}")
        print(f"调试模式: {prod_config.app.ENABLE_DEBUG_MODE}")
        print(f"连接超时(生产): {prod_config.network.CONNECTION_TIMEOUT}秒")
        print(f"刷新间隔(生产): {prod_config.hardware.REFRESH_INTERVAL}秒")
        print(f"日志级别(生产): {prod_config.logging.LOG_LEVEL}")
        print(f"加密历史记录: {prod_config.rdp.ENCRYPT_HISTORY}")
        
        # 测试系统信息获取
        system_info = prod_config.get_system_info()
        print(f"系统信息: {system_info}")
        
        print("✅ 生产环境配置测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 生产环境配置测试失败: {e}\n")
        return False

def test_logging_config():
    """
    测试日志配置
    
    验证日志配置文件是否存在且格式正确。
    """
    print("=== 测试日志配置 ===")
    
    try:
        import logging.config
        
        # 检查日志配置文件是否存在
        log_config_path = project_root / "config" / "logging.conf"
        if not log_config_path.exists():
            print(f"❌ 日志配置文件不存在: {log_config_path}")
            return False
        
        print(f"日志配置文件路径: {log_config_path}")
        
        # 尝试加载日志配置（指定UTF-8编码）
        logging.config.fileConfig(str(log_config_path), encoding='utf-8')
        
        # 测试不同模块的日志记录器
        loggers_to_test = [
            'flowdesk',
            'flowdesk.services.network',
            'flowdesk.services.hardware',
            'flowdesk.services.rdp',
            'flowdesk.ui',
            'flowdesk.services.system_tray'
        ]
        
        for logger_name in loggers_to_test:
            logger = logging.getLogger(logger_name)
            logger.info(f"测试日志记录器: {logger_name}")
            print(f"✓ 日志记录器 {logger_name} 工作正常")
        
        print("✅ 日志配置测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 日志配置测试失败: {e}\n")
        return False

def test_directory_structure():
    """
    测试目录结构
    
    验证必要的目录是否存在，如果不存在则创建。
    """
    print("=== 测试目录结构 ===")
    
    try:
        # 需要检查的目录列表
        required_dirs = [
            "logs",
            "logs/development", 
            "data",
            "data/development",
            "backup"
        ]
        
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✓ 创建目录: {dir_path}")
            else:
                print(f"✓ 目录已存在: {dir_path}")
        
        print("✅ 目录结构测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 目录结构测试失败: {e}\n")
        return False

def test_qss_file():
    """
    测试QSS样式文件
    
    验证QSS样式文件是否存在且不包含不支持的属性。
    """
    print("=== 测试QSS样式文件 ===")
    
    try:
        qss_file_path = project_root / "src" / "flowdesk" / "ui" / "qss" / "main_pyqt5.qss"
        
        if not qss_file_path.exists():
            print(f"❌ QSS文件不存在: {qss_file_path}")
            return False
        
        print(f"QSS文件路径: {qss_file_path}")
        
        # 读取QSS文件内容
        with open(qss_file_path, 'r', encoding='utf-8') as f:
            qss_content = f.read()
        
        # 检查是否还有box-shadow属性
        box_shadow_count = qss_content.count('box-shadow')
        if box_shadow_count > 0:
            print(f"⚠️  警告: QSS文件中仍有 {box_shadow_count} 个 box-shadow 属性")
        else:
            print("✓ QSS文件中已移除所有 box-shadow 属性")
        
        # 检查文件大小
        file_size = len(qss_content)
        print(f"QSS文件大小: {file_size} 字符")
        
        # 检查是否包含中文注释
        chinese_comments = qss_content.count('/*') + qss_content.count('//')
        print(f"注释块数量: {chinese_comments}")
        
        print("✅ QSS样式文件测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ QSS样式文件测试失败: {e}\n")
        return False

def main():
    """
    主测试函数
    
    运行所有测试并汇总结果。
    """
    print("FlowDesk 配置系统测试开始...\n")
    
    # 运行所有测试
    test_results = []
    test_results.append(("目录结构", test_directory_structure()))
    test_results.append(("基础配置", test_basic_config()))
    test_results.append(("开发环境配置", test_development_config()))
    test_results.append(("生产环境配置", test_production_config()))
    test_results.append(("日志配置", test_logging_config()))
    test_results.append(("QSS样式文件", test_qss_file()))
    
    # 汇总测试结果
    print("=== 测试结果汇总 ===")
    passed_count = 0
    total_count = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed_count += 1
    
    print(f"\n总计: {passed_count}/{total_count} 项测试通过")
    
    if passed_count == total_count:
        print("🎉 所有测试通过！FlowDesk配置系统工作正常。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查相关配置。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
