"""
测试日志分级功能
验证标准模式和详细模式的输出差异
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flowdesk.utils.logger import setup_logging, get_logger

def test_logging_levels():
    """测试不同日志级别的输出效果"""
    
    print("=== 测试标准模式（控制台只显示INFO+） ===")
    setup_logging(verbose_mode=False)
    logger = get_logger(__name__)
    
    logger.debug("这是DEBUG信息 - 标准模式下控制台不应显示")
    logger.info("这是INFO信息 - 标准模式下控制台应该显示")
    logger.warning("这是WARNING信息 - 标准模式下控制台应该显示")
    logger.error("这是ERROR信息 - 标准模式下控制台应该显示")
    
    print("\n=== 测试详细模式（控制台显示DEBUG+） ===")
    # 重新初始化为详细模式
    import importlib
    import flowdesk.utils.logger
    importlib.reload(flowdesk.utils.logger)
    
    from flowdesk.utils.logger import setup_logging, get_logger
    setup_logging(verbose_mode=True)
    logger = get_logger(__name__)
    
    logger.debug("这是DEBUG信息 - 详细模式下控制台应该显示")
    logger.info("这是INFO信息 - 详细模式下控制台应该显示")
    logger.warning("这是WARNING信息 - 详细模式下控制台应该显示")
    logger.error("这是ERROR信息 - 详细模式下控制台应该显示")
    
    print("\n=== 测试完成 ===")
    print("请检查：")
    print("1. 标准模式下只看到INFO/WARNING/ERROR信息")
    print("2. 详细模式下可以看到所有级别信息包括DEBUG")
    print("3. 日志文件中应该记录所有级别的信息")

if __name__ == "__main__":
    test_logging_levels()
