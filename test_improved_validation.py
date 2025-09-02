#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
改进后的验证器行为测试脚本

作用说明：
测试修改后的SubnetMaskValidator行为，验证用户现在可以自由输入
中间状态的内容（如255.255.251.），而错误提示只在最终验证时触发。
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLineEdit, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QValidator

from flowdesk.ui.widgets.validators import SubnetMaskValidator


class ImprovedValidationTestWindow(QMainWindow):
    """改进后的验证器行为测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔧 改进后的子网掩码验证器测试")
        self.setGeometry(100, 100, 600, 300)
        
        # 创建中央窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 添加说明标签
        info_label = QLabel("测试改进后的子网掩码验证器行为：")
        info_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px;")
        layout.addWidget(info_label)
        
        # 说明文本
        desc_label = QLabel("""
✅ 现在可以自由输入中间状态内容（如：255.255.251.）
✅ 实时验证不会阻止用户继续输入
✅ 错误提示只在最终验证时触发（点击测试按钮）
        """)
        desc_label.setStyleSheet("color: #27ae60; margin: 10px;")
        layout.addWidget(desc_label)
        
        # 子网掩码测试输入框
        mask_label = QLabel("子网掩码输入测试（尝试输入：255.255.251.）：")
        layout.addWidget(mask_label)
        
        self.mask_input = QLineEdit()
        self.mask_input.setPlaceholderText("现在可以自由输入：255.255.251. 不会被阻止")
        self.mask_validator = SubnetMaskValidator()
        self.mask_input.setValidator(self.mask_validator)
        layout.addWidget(self.mask_input)
        
        # 验证状态显示
        self.status_label = QLabel("验证状态：等待输入...")
        self.status_label.setStyleSheet("padding: 10px; background: #f8f9fa; border: 1px solid #dee2e6;")
        layout.addWidget(self.status_label)
        
        # 实时验证状态监控
        self.mask_input.textChanged.connect(self.check_validation_status)
        
        # 最终验证测试按钮
        final_test_btn = QPushButton("🎯 最终验证测试（模拟点击确定按钮）")
        final_test_btn.clicked.connect(self.test_final_validation)
        layout.addWidget(final_test_btn)
        
        # 测试结果显示
        self.result_label = QLabel("")
        self.result_label.setStyleSheet("padding: 10px; margin-top: 10px;")
        layout.addWidget(self.result_label)
    
    def check_validation_status(self):
        """检查当前输入的验证状态"""
        current_text = self.mask_input.text()
        if not current_text:
            self.status_label.setText("验证状态：等待输入...")
            self.status_label.setStyleSheet("padding: 10px; background: #f8f9fa; border: 1px solid #dee2e6;")
            return
        
        # 调用验证器检查状态
        state, _, _ = self.mask_validator.validate(current_text, 0)
        
        if state == QValidator.Acceptable:
            status_text = f"✅ 可接受：'{current_text}' - 有效的子网掩码格式"
            style = "padding: 10px; background: #d4edda; border: 1px solid #c3e6cb; color: #155724;"
        elif state == QValidator.Intermediate:
            status_text = f"🔄 中间状态：'{current_text}' - 可以继续输入"
            style = "padding: 10px; background: #fff3cd; border: 1px solid #ffeaa7; color: #856404;"
        else:
            status_text = f"❌ 无效：'{current_text}' - 输入被阻止"
            style = "padding: 10px; background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24;"
        
        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(style)
    
    def test_final_validation(self):
        """测试最终验证（模拟用户点击确定按钮）"""
        current_text = self.mask_input.text().strip()
        
        if not current_text:
            self.result_label.setText("⚠️ 请先输入子网掩码进行测试")
            self.result_label.setStyleSheet("padding: 10px; background: #fff3cd; border: 1px solid #ffeaa7; color: #856404;")
            return
        
        # 模拟AddIPDialog中的最终验证逻辑
        state, _, _ = self.mask_validator.validate(current_text, 0)
        
        if state == QValidator.Acceptable:
            result_text = f"🎉 最终验证通过：'{current_text}' 是有效的子网掩码"
            style = "padding: 10px; background: #d4edda; border: 1px solid #c3e6cb; color: #155724;"
        else:
            result_text = f"🚨 最终验证失败：'{current_text}' 不是有效的子网掩码\n💡 此时会触发错误提示弹窗（在实际应用中）"
            style = "padding: 10px; background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24;"
        
        self.result_label.setText(result_text)
        self.result_label.setStyleSheet(style)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序基本信息
    app.setApplicationName("Improved Validation Test")
    app.setApplicationVersion("1.0")
    
    # 创建测试窗口
    window = ImprovedValidationTestWindow()
    window.show()
    
    print("🔧 改进后的子网掩码验证器测试启动")
    print("📋 测试重点：")
    print("   1. 输入 '255.255.251.' 应该显示为中间状态，可以继续输入")
    print("   2. 实时验证不会阻止用户输入")
    print("   3. 只有在最终验证时才会触发错误提示")
    print()
    print("🎯 推荐测试序列：")
    print("   1. 输入：255")
    print("   2. 输入：255.255")
    print("   3. 输入：255.255.251")
    print("   4. 输入：255.255.251.")
    print("   5. 输入：255.255.251.0")
    print("   6. 点击'最终验证测试'按钮")
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
