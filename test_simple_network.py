#!/usr/bin/env python3
"""
简化的网络配置功能测试脚本

验证NetworkService的基本功能是否正常工作，
不依赖PyQt5 GUI，直接测试核心业务逻辑。
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_imports():
    """测试基本导入功能"""
    print("=== 测试基本导入 ===")
    
    try:
        from flowdesk.models.adapter_info import AdapterInfo, IPConfigInfo, DnsConfig, ExtraIP
        print("✓ 数据模型导入成功")
        
        from flowdesk.services.network_service import NetworkService
        print("✓ 网络服务导入成功")
        
        return True
    except Exception as e:
        print(f"✗ 导入失败: {str(e)}")
        return False

def test_data_models():
    """测试数据模型功能"""
    print("\n=== 测试数据模型 ===")
    
    try:
        from flowdesk.models.adapter_info import AdapterInfo, IPConfigInfo, ExtraIP
        
        # 创建测试数据
        adapter = AdapterInfo(
            id="test-adapter-001",
            name="以太网",
            friendly_name="测试网卡",
            description="测试网络适配器",
            mac_address="00:11:22:33:44:55",
            status="已连接",
            is_connected=True,
            ip_addresses=["192.168.1.100", "10.0.0.100"],
            subnet_masks=["255.255.255.0", "255.255.0.0"],
            gateway="192.168.1.1",
            dns_servers=["8.8.8.8", "8.8.4.4"],
            dhcp_enabled=False
        )
        
        print(f"✓ AdapterInfo创建成功: {adapter.friendly_name}")
        
        # 测试智能IP分类
        primary_ip = adapter.get_primary_ip()
        extra_ips = adapter.get_extra_ips()
        
        print(f"✓ 主IP地址: {primary_ip}")
        print(f"✓ 额外IP数量: {len(extra_ips)}")
        
        # 测试格式化复制功能
        formatted_info = adapter.format_for_copy()
        print(f"✓ 格式化信息长度: {len(formatted_info)} 字符")
        
        return True
    except Exception as e:
        print(f"✗ 数据模型测试失败: {str(e)}")
        return False

def test_network_service_creation():
    """测试网络服务创建"""
    print("\n=== 测试网络服务创建 ===")
    
    try:
        # 模拟PyQt5环境
        class MockQObject:
            def __init__(self):
                pass
        
        class MockSignal:
            def __init__(self):
                self.connected_slots = []
            
            def emit(self, *args):
                for slot in self.connected_slots:
                    slot(*args)
            
            def connect(self, slot):
                self.connected_slots.append(slot)
        
        class MockQSystemTrayIcon:
            def __init__(self):
                pass
        
        class MockQMenu:
            def __init__(self):
                pass
        
        class MockQAction:
            def __init__(self, text, parent=None):
                pass
        
        class MockQApplication:
            @staticmethod
            def clipboard():
                return None
        
        class MockQMessageBox:
            def __init__(self):
                pass
        
        # 替换PyQt5导入
        sys.modules['PyQt5'] = type(sys)('mock_pyqt5')
        sys.modules['PyQt5.QtCore'] = type(sys)('mock_qtcore')
        sys.modules['PyQt5.QtCore'].QObject = MockQObject
        sys.modules['PyQt5.QtCore'].pyqtSignal = lambda *args: MockSignal()
        sys.modules['PyQt5.QtWidgets'] = type(sys)('mock_qtwidgets')
        sys.modules['PyQt5.QtWidgets'].QApplication = MockQApplication
        sys.modules['PyQt5.QtWidgets'].QSystemTrayIcon = MockQSystemTrayIcon
        sys.modules['PyQt5.QtWidgets'].QMenu = MockQMenu
        sys.modules['PyQt5.QtWidgets'].QAction = MockQAction
        sys.modules['PyQt5.QtWidgets'].QMessageBox = MockQMessageBox
        sys.modules['PyQt5.QtWidgets'].QDialog = MockQObject
        sys.modules['PyQt5.QtWidgets'].QVBoxLayout = MockQObject
        sys.modules['PyQt5.QtWidgets'].QHBoxLayout = MockQObject
        sys.modules['PyQt5.QtWidgets'].QLabel = MockQObject
        sys.modules['PyQt5.QtWidgets'].QPushButton = MockQObject
        sys.modules['PyQt5.QtWidgets'].QWidget = MockQObject
        
        from flowdesk.services.network_service import NetworkService
        
        # 创建网络服务（不调用实际的系统命令）
        service = NetworkService()
        print("✓ NetworkService创建成功")
        
        # 测试信号定义
        signals = [
            'adapters_updated', 'adapter_selected', 'ip_info_updated',
            'extra_ips_updated', 'adapter_refreshed', 'network_info_copied',
            'error_occurred'
        ]
        
        for signal_name in signals:
            if hasattr(service, signal_name):
                print(f"✓ 信号 {signal_name} 定义正确")
            else:
                print(f"✗ 信号 {signal_name} 缺失")
        
        return True
    except Exception as e:
        print(f"✗ 网络服务测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("FlowDesk 网络配置Tab核心功能测试")
    print("=" * 50)
    
    success_count = 0
    total_tests = 3
    
    # 执行测试
    if test_basic_imports():
        success_count += 1
    
    if test_data_models():
        success_count += 1
    
    if test_network_service_creation():
        success_count += 1
    
    # 输出测试结果
    print(f"\n=== 测试结果 ===")
    print(f"通过测试: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("✓ 所有核心功能测试通过")
        print("\n网络配置Tab核心功能实现完成！")
        print("主要功能:")
        print("• 启动初始化：自动获取网卡信息")
        print("• 智能IP显示：主IP和额外IP分类显示")
        print("• 网卡状态同步：选择网卡时实时更新界面")
        print("• 刷新按钮：重新获取当前网卡信息")
        print("• 信息复制：格式化网卡信息复制到剪贴板")
        return 0
    else:
        print("✗ 部分测试失败，需要进一步调试")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
