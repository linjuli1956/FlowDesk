#!/usr/bin/env python3
"""
FlowDesk 应用程序启动脚本
简化启动流程，自动处理路径问题
"""

import sys
import os

# 添加 src 目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# 导入并启动应用程序
try:
    from flowdesk.app import main
    main()
except Exception as e:
    print(f"启动失败: {e}")
    sys.exit(1)
