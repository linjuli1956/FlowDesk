#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
验证错误提示对话框功能测试脚本

作用说明：
测试ValidationErrorDialog的各种错误提示功能，验证用户体验和显示效果。
包括子网掩码错误、IP地址错误等不同场景的测试。
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLineEdit, QLabel
from PyQt5.QtCore import Qt

from flowdesk.ui.dialogs.validation_error_dialog import ValidationErrorDialog
from flowdesk.ui.widgets.validators import IPAddressValidator, SubnetMaskValidator


class ValidationTestWindow(QMainWindow):
    """验证错误提示功能测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧪 验证错误提示功能测试")
        self.setGeometry(100, 100, 500, 400)
        
        # 创建中央窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 添加说明标签
        info_label = QLabel("测试各种输入验证错误提示场景：")
        info_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px;")
        layout.addWidget(info_label)
        
        # 子网掩码测试区域
        mask_label = QLabel("子网掩码测试（输入错误格式会触发提示）：")
        layout.addWidget(mask_label)
        
        self.mask_input = QLineEdit()
        self.mask_input.setPlaceholderText("尝试输入：255.255.250. 或其他错误格式")
        mask_validator = SubnetMaskValidator()
        self.mask_input.setValidator(mask_validator)
        mask_validator.validation_error.connect(self.show_mask_error)
        layout.addWidget(self.mask_input)
        
        # IP地址测试区域
        ip_label = QLabel("IP地址测试（输入错误格式会触发提示）：")
        layout.addWidget(ip_label)
        
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("尝试输入：192.168.1.256 或其他错误格式")
        ip_validator = IPAddressValidator()
        self.ip_input.setValidator(ip_validator)
        ip_validator.validation_error.connect(self.show_ip_error)
        layout.addWidget(self.ip_input)
        
        # 手动测试按钮
        manual_test_label = QLabel("手动测试按钮：")
        layout.addWidget(manual_test_label)
        
        # 子网掩码错误测试按钮
        mask_error_btn = QPushButton("🔍 测试子网掩码错误提示")
        mask_error_btn.clicked.connect(self.test_mask_error)
        layout.addWidget(mask_error_btn)
        
        # IP地址错误测试按钮
        ip_error_btn = QPushButton("🌐 测试IP地址错误提示")
        ip_error_btn.clicked.connect(self.test_ip_error)
        layout.addWidget(ip_error_btn)
        
        # 多种错误场景测试按钮
        scenarios_btn = QPushButton("🎯 测试多种错误场景")
        scenarios_btn.clicked.connect(self.test_error_scenarios)
        layout.addWidget(scenarios_btn)
        
        # 初始化错误对话框
        self.error_dialog = None
    
    def show_mask_error(self, invalid_input: str):
        """显示子网掩码验证错误"""
        print(f"🚨 子网掩码验证错误: {invalid_input}")
        
        if self.error_dialog:
            self.error_dialog.close()
        
        self.error_dialog = ValidationErrorDialog(self)
        self.error_dialog.show_subnet_mask_error(invalid_input, auto_close_seconds=8)
    
    def show_ip_error(self, invalid_input: str):
        """显示IP地址验证错误"""
        print(f"🚨 IP地址验证错误: {invalid_input}")
        
        if self.error_dialog:
            self.error_dialog.close()
        
        self.error_dialog = ValidationErrorDialog(self)
        self.error_dialog.show_ip_address_error(invalid_input, auto_close_seconds=8)
    
    def test_mask_error(self):
        """手动测试子网掩码错误提示"""
        test_cases = [
            "255.255.250.",  # 用户实际遇到的错误
            "255.255.256.0",  # 超出范围
            "255.255.255",   # 不完整
            "/33",           # CIDR超出范围
            "255.255.255.abc", # 包含字母
        ]
        
        import random
        test_input = random.choice(test_cases)
        self.show_mask_error(test_input)
    
    def test_ip_error(self):
        """手动测试IP地址错误提示"""
        test_cases = [
            "192.168.1.256",  # 超出范围
            "192.168.1.",     # 不完整
            "192.168.1.1.1",  # 过多段
            "192.168.abc.1",  # 包含字母
            "300.168.1.1",    # 第一段超出范围
        ]
        
        import random
        test_input = random.choice(test_cases)
        self.show_ip_error(test_input)
    
    def test_error_scenarios(self):
        """测试多种错误场景"""
        scenarios = [
            ("子网掩码", "255.255.250."),
            ("子网掩码", "/35"),
            ("子网掩码", "255.255.255.abc"),
            ("IP地址", "192.168.1.300"),
            ("IP地址", "192.168."),
            ("IP地址", "abc.def.ghi.jkl"),
        ]
        
        import random
        error_type, test_input = random.choice(scenarios)
        
        if error_type == "子网掩码":
            self.show_mask_error(test_input)
        else:
            self.show_ip_error(test_input)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序基本信息
    app.setApplicationName("ValidationErrorDialog Test")
    app.setApplicationVersion("1.0")
    
    # 创建测试窗口
    window = ValidationTestWindow()
    window.show()
    
    print("🧪 验证错误提示功能测试启动")
    print("📋 测试说明：")
    print("   1. 在输入框中输入错误格式会自动触发错误提示")
    print("   2. 点击手动测试按钮可以测试预定义的错误场景")
    print("   3. 错误提示对话框会自动关闭或手动关闭")
    print("   4. 观察提示内容是否清晰、友好、有帮助")
    print()
    print("🎯 推荐测试输入：")
    print("   子网掩码: 255.255.250. (用户实际遇到的错误)")
    print("   子网掩码: /33, 255.255.256.0, abc.def.ghi.jkl")
    print("   IP地址: 192.168.1.256, 300.168.1.1, 192.168.1.")
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
