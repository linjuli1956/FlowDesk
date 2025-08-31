# -*- coding: utf-8 -*-
"""
服务层单元测试模块

包含FlowDesk应用程序所有服务类的单元测试。
每个服务类都有对应的测试文件，测试其核心功能和异常处理。

测试原则：
- 使用Mock对象隔离外部依赖
- 测试正常流程和异常情况
- 验证信号发射和状态变化
- 确保服务间协作正确

网络服务测试模块：
- test_network_service: NetworkService门面测试
- test_network_ui_coordinator_service: UI协调服务测试
- test_adapter_discovery_service: 网卡发现服务测试
- test_adapter_info_service: 网卡信息服务测试
- test_adapter_status_service: 网卡状态服务测试
- test_adapter_performance_service: 网卡性能服务测试
- test_ip_configuration_service: IP配置服务测试
- test_extra_ip_management_service: 额外IP管理服务测试
- test_rdp_service.py: 远程桌面服务测试
- test_hardware_monitor_service.py: 硬件监控服务测试
- test_settings_service.py: 配置管理服务测试
- test_system_tray_service.py: 系统托盘服务测试
"""
