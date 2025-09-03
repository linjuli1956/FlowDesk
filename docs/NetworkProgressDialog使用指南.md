# NetworkProgressDialog 使用指南

## 概述
NetworkProgressDialog是FlowDesk项目的通用网络操作进度提示组件，提供统一的用户体验和专业的Claymorphism设计风格。

## 核心特性

### 🎯 设计原则
- **模态对话框**：防止用户误操作，确保操作完整性
- **可取消操作**：支持用户主动取消耗时操作
- **实时反馈**：显示操作进度、状态和耗时
- **线程安全**：后台执行操作，避免UI阻塞

### 🎨 视觉特点
- **Claymorphism风格**：柔和渐变、圆角边框、毛玻璃效果
- **状态色彩语义**：红色取消、绿色完成、蓝色进度
- **响应式布局**：固定尺寸400×200，居中显示
- **动画效果**：平滑的进度条动画和按钮状态切换

## 使用方法

### 方法一：便捷函数（推荐）

```python
from flowdesk.ui.dialogs import show_network_progress

# 示例：修改MAC地址
def modify_mac_address(adapter_name: str, new_mac: str) -> bool:
    """修改MAC地址的业务逻辑函数"""
    # 实际的MAC修改逻辑
    time.sleep(3)  # 模拟耗时操作
    return True

# 调用进度对话框
success = show_network_progress(
    operation_name="修改MAC地址",
    operation_func=modify_mac_address,
    adapter_name="以太网 2",
    parent=self,
    new_mac="AA:BB:CC:DD:EE:FF"
)

if success:
    print("MAC地址修改成功")
else:
    print("MAC地址修改失败或被取消")
```

### 方法二：手动控制

```python
from flowdesk.ui.dialogs import NetworkProgressDialog, NetworkOperationWorker

# 创建进度对话框
dialog = NetworkProgressDialog("启用网卡", "以太网 2", parent=self)

# 创建工作线程
worker = NetworkOperationWorker(enable_network_adapter, "以太网 2")

# 连接信号
worker.progress_updated.connect(dialog.update_progress)
worker.operation_completed.connect(dialog.complete_operation)
dialog.operation_cancelled.connect(worker.cancel_operation)

# 启动操作
worker.start()
result = dialog.exec_()
```

### 方法三：自定义进度控制

```python
from flowdesk.ui.dialogs import NetworkProgressDialog

# 创建对话框
dialog = NetworkProgressDialog("配置IP地址", "以太网 2", parent=self)
dialog.show()

# 手动更新进度
dialog.update_progress(25, "正在验证IP地址...")
time.sleep(1)

dialog.update_progress(50, "正在应用网络配置...")
time.sleep(2)

dialog.update_progress(75, "正在重启网络适配器...")
time.sleep(2)

# 完成操作
dialog.complete_operation(True, "IP地址配置成功")
```

## 集成到现有功能

### 1. MAC地址修改集成

```python
# 在 network_event_handler.py 中
def _on_modify_mac_clicked(self):
    """处理修改MAC地址按钮点击"""
    # 获取当前选中的网卡和新MAC地址
    adapter_name = self.get_current_adapter_name()
    new_mac = self.get_new_mac_address()
    
    # 使用进度对话框执行操作
    success = show_network_progress(
        operation_name="修改MAC地址",
        operation_func=self.mac_service.modify_mac_address,
        adapter_name=adapter_name,
        parent=self.main_window,
        new_mac=new_mac
    )
    
    if success:
        self.show_success_message("MAC地址修改成功")
        self.refresh_adapter_info()
    else:
        self.show_error_message("MAC地址修改失败")
```

### 2. IP配置修改集成

```python
def _on_apply_ip_config(self):
    """应用IP配置"""
    ip_config = self.get_ip_config_data()
    adapter_name = self.get_current_adapter_name()
    
    success = show_network_progress(
        operation_name="修改IP配置",
        operation_func=self.network_service.apply_ip_config,
        adapter_name=adapter_name,
        parent=self.main_window,
        config=ip_config
    )
    
    if success:
        self.update_ui_after_config_change()
```

### 3. 网卡启用/禁用集成

```python
def _on_enable_adapter(self):
    """启用网卡"""
    adapter_name = self.get_current_adapter_name()
    
    success = show_network_progress(
        operation_name="启用网卡",
        operation_func=self.adapter_service.enable_adapter,
        adapter_name=adapter_name,
        parent=self.main_window
    )
    
    if success:
        self.refresh_adapter_status()

def _on_disable_adapter(self):
    """禁用网卡"""
    adapter_name = self.get_current_adapter_name()
    
    success = show_network_progress(
        operation_name="禁用网卡", 
        operation_func=self.adapter_service.disable_adapter,
        adapter_name=adapter_name,
        parent=self.main_window
    )
    
    if success:
        self.refresh_adapter_status()
```

### 4. 额外IP管理集成

```python
def _on_add_selected_ips(self):
    """添加选中的IP地址"""
    selected_ips = self.get_selected_extra_ips()
    adapter_name = self.get_current_adapter_name()
    
    success = show_network_progress(
        operation_name="添加IP地址",
        operation_func=self.ip_service.add_multiple_ips,
        adapter_name=adapter_name,
        parent=self.main_window,
        ip_list=selected_ips
    )
    
    if success:
        self.refresh_ip_list()

def _on_remove_selected_ips(self):
    """删除选中的IP地址"""
    selected_ips = self.get_selected_extra_ips()
    adapter_name = self.get_current_adapter_name()
    
    success = show_network_progress(
        operation_name="删除IP地址",
        operation_func=self.ip_service.remove_multiple_ips,
        adapter_name=adapter_name,
        parent=self.main_window,
        ip_list=selected_ips
    )
    
    if success:
        self.refresh_ip_list()
```

### 5. DHCP切换集成

```python
def _on_switch_to_dhcp(self):
    """切换到DHCP模式"""
    adapter_name = self.get_current_adapter_name()
    
    success = show_network_progress(
        operation_name="切换到DHCP",
        operation_func=self.network_service.enable_dhcp,
        adapter_name=adapter_name,
        parent=self.main_window
    )
    
    if success:
        self.update_ip_config_ui()
```

## API参考

### NetworkProgressDialog

#### 构造函数
```python
NetworkProgressDialog(operation_name: str, adapter_name: str = "", parent=None)
```

#### 主要方法
- `update_progress(progress: int, status_text: str = "")` - 更新进度
- `set_indeterminate_progress(status_text: str = "")` - 设置不确定进度
- `complete_operation(success: bool, message: str = "")` - 完成操作

#### 信号
- `operation_cancelled` - 操作取消信号
- `dialog_closed` - 对话框关闭信号

### show_network_progress 函数

```python
show_network_progress(
    operation_name: str,        # 操作名称
    operation_func: Callable,   # 操作函数
    adapter_name: str = "",     # 网卡名称（可选）
    parent=None,               # 父窗口
    *args, **kwargs           # 传递给操作函数的参数
) -> bool                     # 返回操作是否成功
```

## 样式定制

### QSS选择器
```css
/* 对话框容器 */
QDialog#network_progress_dialog { }

/* 标题标签 */
QLabel#operation_title_label { }

/* 状态标签 */
QLabel#operation_status_label { }

/* 进度条 */
QProgressBar#network_progress_bar { }

/* 取消按钮 */
QPushButton#dialog_cancel_button { }

/* 完成按钮 */
QPushButton#dialog_ok_button { }
```

### 自定义样式
如需修改样式，请编辑 `src/flowdesk/ui/qss/network_progress_dialog.qss` 文件。

## 最佳实践

### 1. 操作函数设计
```python
def network_operation_template(adapter_name: str, param1: str) -> bool:
    """网络操作模板
    
    Returns:
        bool: 操作是否成功
    """
    try:
        # 执行具体操作
        result = do_network_operation(adapter_name, param1)
        return result
    except Exception as e:
        logger.error(f"网络操作失败: {e}")
        return False
```

### 2. 错误处理
```python
# 在Service层捕获异常，返回bool结果
def modify_mac_with_progress(self, adapter_name: str, new_mac: str):
    success = show_network_progress(
        operation_name="修改MAC地址",
        operation_func=self.mac_service.modify_mac_address,
        adapter_name=adapter_name,
        parent=self.main_window,
        new_mac=new_mac
    )
    
    if not success:
        # 显示详细错误信息
        QMessageBox.warning(
            self.main_window,
            "操作失败",
            f"修改MAC地址失败，请检查网卡状态和权限设置"
        )
```

### 3. 用户体验优化
- **合理的操作名称**：使用用户友好的操作描述
- **及时的状态更新**：在关键步骤更新进度和状态
- **优雅的错误处理**：提供清晰的错误信息和解决建议
- **一致的交互模式**：所有网络操作使用相同的进度提示

## 注意事项

### 1. 线程安全
- 操作函数在后台线程执行，避免阻塞UI
- 不要在操作函数中直接操作UI组件
- 使用信号槽机制进行线程间通信

### 2. 资源管理
- 对话框会自动管理计时器和线程资源
- 操作取消时会正确清理资源
- 避免在操作函数中创建长期持有的资源

### 3. 兼容性
- 遵循FlowDesk的四层架构原则
- 与StylesheetService统一样式管理兼容
- 支持Windows 7兼容模式

---

*文档版本: 1.0*  
*创建日期: 2025-09-03*  
*适用项目: FlowDesk*
