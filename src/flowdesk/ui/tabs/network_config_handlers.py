# -*- coding: utf-8 -*-
"""
网络配置事件处理器 - 负责所有业务逻辑处理方法

这个模块实现网络配置Tab页面的所有事件处理逻辑，包括：
- IP配置数据收集与验证
- 添加IP对话框处理
- 额外IP管理操作
- 网络配置确认和发射

设计原则：
1. 纯事件处理逻辑，不涉及UI组件创建
2. 所有方法供主容器调用
3. 保持原有的验证和处理逻辑
4. 严格遵循面向对象单一职责原则
"""

from PyQt5.QtWidgets import QMessageBox, QListWidgetItem
from PyQt5.QtCore import Qt

from ..dialogs import AddIPDialog


class NetworkConfigHandlers:
    """
    网络配置事件处理器类
    
    负责处理网络配置Tab页面的所有业务逻辑事件，包括IP配置验证、
    对话框管理、额外IP操作等功能。
    
    设计特点：
    - 纯事件处理功能，不涉及UI组件管理
    - 所有方法供主容器类调用
    - 保持原有处理逻辑和验证规则
    """
    
    def __init__(self):
        """初始化处理器"""
        pass
    
    def emit_ip_config(self, parent):
        """
        网络配置数据收集与验证的核心方法
        
        作用说明：
        这个方法是网络配置Tab页面的核心业务逻辑处理器，负责从五个输入框中
        收集用户输入的网络配置数据，进行全面的输入验证，并在用户确认后
        发射配置信号给服务层执行实际的网络配置操作。
        
        面向对象设计特点：
        - 单一职责原则：专门负责UI层的数据收集和初步验证
        - 封装性：将复杂的验证逻辑封装在独立方法中
        - 依赖倒置：通过信号槽机制与服务层解耦
        - 开闭原则：验证规则可以通过扩展方法来增加新规则
        
        数据流程：
        用户输入 → 数据收集 → 格式验证 → 逻辑验证 → 确认对话框 → 信号发射
        
        Args:
            parent: 父容器对象，用于访问UI组件和发射信号
        """
        # 第一步：从五个输入框收集完整的网络配置数据
        # 这些数据将用于后续的验证和配置操作
        ip_address = parent.ip_address_input.text().strip()
        subnet_mask = parent.subnet_mask_input.text().strip()
        gateway = parent.gateway_input.text().strip()
        primary_dns = parent.primary_dns_input.text().strip()
        secondary_dns = parent.secondary_dns_input.text().strip()
        adapter_name = parent.adapter_combo.currentText()
        
        # 第二步：执行全面的输入验证
        validation_result = self._validate_network_config(
            ip_address, subnet_mask, gateway, primary_dns, secondary_dns
        )
        
        if not validation_result['is_valid']:
            QMessageBox.warning(parent, "输入验证失败", validation_result['error_message'])
            return
        
        # 第三步：构建详细的确认消息，显示所有将要配置的网络参数
        confirm_message = self._build_confirmation_message(
            adapter_name, ip_address, subnet_mask, gateway, primary_dns, secondary_dns
        )
        
        # 第四步：显示确认对话框，确保用户明确了解即将进行的配置更改
        reply = QMessageBox.question(
            parent, 
            "确认IP配置修改", 
            confirm_message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # 默认选择"否"，确保用户主动确认
        )
        
        # 第五步：用户确认后，构建完整的配置数据并发射信号
        if reply == QMessageBox.Yes:
            config_data = {
                'ip_address': ip_address,
                'subnet_mask': subnet_mask,
                'gateway': gateway if gateway else '',
                'primary_dns': primary_dns if primary_dns else '',
                'secondary_dns': secondary_dns if secondary_dns else '',
                'adapter': adapter_name
            }
            # 通过信号槽机制将配置数据传递给服务层
            # 这体现了面向对象设计中的依赖倒置原则
            parent.apply_ip_config.emit(config_data)

    def _validate_network_config(self, ip_address, subnet_mask, gateway, primary_dns, secondary_dns):
        """
        网络配置参数验证方法 - 委托给Service层处理
        
        UI层只负责调用Service层的验证方法，不包含业务逻辑。
        
        Args:
            ip_address (str): IPv4地址字符串
            subnet_mask (str): 子网掩码字符串
            gateway (str): 网关地址字符串，可选
            primary_dns (str): 主DNS服务器地址，可选
            secondary_dns (str): 备用DNS服务器地址，可选
            
        Returns:
            dict: 验证结果字典，包含is_valid(bool)和error_message(str)字段
        """
        # 委托给Service层处理验证逻辑，UI层不包含业务逻辑
        return self.parent().network_service.validate_network_config(
            ip_address, subnet_mask, gateway, primary_dns, secondary_dns
        )
    
    def _build_confirmation_message(self, adapter_name, ip_address, subnet_mask, gateway, primary_dns, secondary_dns):
        """
        构建网络配置确认对话框的详细消息内容
        
        作用说明：
        这个方法负责生成用户确认对话框中显示的详细配置信息，包括所有将要设置的
        网络参数。通过清晰的格式化显示，让用户能够准确了解即将进行的配置更改。
        
        Args:
            adapter_name (str): 网络适配器名称
            ip_address (str): IP地址
            subnet_mask (str): 子网掩码
            gateway (str): 网关地址，可能为空
            primary_dns (str): 主DNS，可能为空
            secondary_dns (str): 备用DNS，可能为空
            
        Returns:
            str: 格式化的确认消息字符串
        """
        # 构建基础配置信息
        message = f"""确定要修改以下网卡的IP配置吗？

📡 网卡：{adapter_name}
🌐 IP地址：{ip_address}
🔒 子网掩码：{subnet_mask}"""
        
        # 添加可选配置项（只有在用户输入时才显示）
        if gateway:
            message += f"\n🚪 网关：{gateway}"
        if primary_dns:
            message += f"\n🔍 主DNS：{primary_dns}"
        if secondary_dns:
            message += f"\n🔍 备用DNS：{secondary_dns}"
        
        # 添加重要提示信息
        message += "\n\n⚠️ 重要提示："
        message += "\n• 修改IP配置可能会暂时中断网络连接"
        message += "\n• 请确认所有配置参数正确无误"
        message += "\n• 建议在修改前记录当前配置以便恢复"
        
        return message

    def show_add_ip_dialog(self, parent):
        """
        显示添加额外IP地址对话框
        
        作用说明：
        当用户点击"添加IP"按钮时，弹出专用的IP地址配置对话框。
        该对话框提供标准化的IP地址和子网掩码输入界面，集成了
        实时输入验证功能，确保用户只能输入有效的网络参数。
        
        设计特点：
        - 使用模态对话框，确保用户专注于IP配置输入
        - 集成QValidator实时验证，防止无效输入
        - 通过信号槽机制处理用户输入结果
        - 遵循面向对象设计，对话框逻辑完全封装
        
        交互流程：
        1. 创建AddIPDialog实例并显示
        2. 用户在对话框中输入IP地址和子网掩码
        3. 实时验证确保输入格式正确
        4. 用户点击确定后，对话框发射ip_added信号
        5. 处理信号，将新IP信息传递给服务层
        
        Args:
            parent: 父容器对象
        """
        # 创建添加IP对话框实例，设置当前窗口为父窗口确保正确的模态行为
        dialog = AddIPDialog(parent)
        
        # 连接对话框的ip_added信号到处理方法
        # 当用户成功添加IP时，对话框会发射此信号携带IP配置数据
        dialog.ip_added.connect(lambda ip, mask: self.handle_ip_added(parent, ip, mask))
        
        # 显示模态对话框
        # exec_()方法会阻塞程序执行，直到对话框被关闭
        # 返回值指示用户是点击了确定(QDialog.Accepted)还是取消(QDialog.Rejected)
        result = dialog.exec_()
        
        # 注意：这里不需要手动处理返回值，因为ip_added信号已经处理了确定的情况
        # 如果用户取消或关闭对话框，不会有任何操作，这是期望的行为

    def handle_ip_added(self, parent, ip_address: str, subnet_mask: str):
        """
        处理添加IP对话框的确认操作
        
        作用说明：
        当用户在添加IP对话框中输入有效的IP配置并点击确定时，此方法负责
        将新的IP配置直接添加到右侧的额外IP列表中。新添加的IP会显示在
        列表的第一位，确保用户能够立即看到刚刚添加的内容。
        
        参数说明：
            parent: 父容器对象
            ip_address (str): 用户输入的IP地址（如：192.168.1.100）
            subnet_mask (str): 用户输入的子网掩码（如：255.255.255.0或/24）
        """
        # 格式化IP配置为标准显示格式
        # 统一使用 "IP地址 / 子网掩码" 的格式显示
        ip_config_text = f"{ip_address} / {subnet_mask}"
        
        # 创建新的列表项用于显示额外IP
        # QListWidgetItem封装了列表项的数据和显示属性
        new_item = QListWidgetItem(ip_config_text)
        new_item.setFlags(new_item.flags() | Qt.ItemIsUserCheckable)  # 设置可勾选
        new_item.setCheckState(Qt.Unchecked)  # 默认未选中状态
        
        # 将新项目插入到列表的第一位（索引0）
        # 这确保了最新添加的IP配置总是显示在最顶部，用户可以立即看到
        parent.extra_ip_list.insertItem(0, new_item)
        
        # 自动滚动到列表顶部，确保新添加的项目在可视区域内
        parent.extra_ip_list.scrollToTop()
        
        # 获取当前选择的网卡名称，用于服务层处理
        current_adapter = parent.adapter_combo.currentText()
        
        # 同时发射信号给服务层进行实际的网络配置操作
        # 这保持了UI层与服务层的解耦，UI负责界面更新，服务层负责业务逻辑
        parent.add_extra_ip.emit(current_adapter, ip_config_text)

    def add_selected_ips_to_adapter(self, parent):
        """
        将选中的额外IP添加到当前网卡的核心处理方法
        
        作用说明：
        这个方法负责处理"添加选中"按钮的点击事件，将用户在额外IP管理列表中
        勾选的IP地址配置应用到当前选择的网络适配器上。
        
        Args:
            parent: 父容器对象
        """
        # 第一步：获取当前选择的网络适配器名称
        current_adapter = parent.adapter_combo.currentText()
        
        # 第二步：遍历额外IP列表，收集所有勾选的IP配置项
        selected_ip_configs = []
        
        for index in range(parent.extra_ip_list.count()):
            item = parent.extra_ip_list.item(index)
            if item.checkState() == Qt.Checked:
                ip_config_text = item.text()
                selected_ip_configs.append(ip_config_text)
        
        # 第三步：验证用户选择的有效性
        if not selected_ip_configs:
            # 显示用户友好提示
            QMessageBox.information(parent, "提示", "请先勾选要添加的IP地址。")
            return
        
        # 第四步：发射信号给服务层执行实际的网络配置操作
        parent.add_selected_ips.emit(current_adapter, selected_ip_configs)

    def remove_selected_ips_from_adapter(self, parent):
        """
        从当前网卡删除选中的额外IP的核心处理方法
        
        作用说明：
        这个方法负责处理"删除选中"按钮的点击事件，将用户在额外IP管理列表中
        勾选的IP地址配置从当前选择的网络适配器上移除。
        
        Args:
            parent: 父容器对象
        """
        # 第一步：获取当前选择的网络适配器名称
        current_adapter = parent.adapter_combo.currentText()
        
        # 第二步：遍历额外IP列表，收集所有勾选的IP配置项
        selected_ip_configs = []
        
        for index in range(parent.extra_ip_list.count()):
            item = parent.extra_ip_list.item(index)
            if item.checkState() == Qt.Checked:
                ip_config_text = item.text()
                selected_ip_configs.append(ip_config_text)
        
        # 第三步：验证用户选择的有效性
        if not selected_ip_configs:
            # 显示用户友好提示
            QMessageBox.information(parent, "提示", "请先勾选要删除的IP地址。")
            return
        
        # 第四步：发射信号给服务层执行删除操作
        parent.remove_selected_ips.emit(current_adapter, selected_ip_configs)
