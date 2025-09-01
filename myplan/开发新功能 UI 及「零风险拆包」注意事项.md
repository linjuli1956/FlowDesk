# 开发新功能 UI 及「零风险拆包」注意事项
> FlowDesk 全景式开发守则——新功能、拆包、弹窗、方法实现，一律照此执行

---

## 🏛️ 总则：四层架构铁律

### 架构分层原则
| 层级 | 绝对禁止 | 必须做到 |
|---|---|---|
| **UI** | 任何业务逻辑、直接 import Service/Model/Utils、内联样式、Lambda 处理器 | 只收 PyQt 信号，调用 Service 方法；样式 100% 走 StylesheetService |
| **Service** | 出现 PyQt 类、承担多个职责、出现裸 dict | 单职责、@dataclass(frozen=True) 输入输出、依赖注入 |
| **Model** | 出现业务逻辑、可变属性 | 全部 @dataclass(frozen=True)，只读数据契约 |
| **Utils** | 保存状态、依赖 Service/Model | 纯函数、无状态、可复用 |

### 面向对象五大原则 (SOLID)
1. **单一职责原则 (SRP)**: 一个类只负责一项功能，避免类过于庞大或复杂
2. **开闭原则 (OCP)**: 对扩展开放，对修改封闭，通过添加新代码来扩展功能
3. **里氏替换原则 (LSP)**: 子类必须能够替换父类而不破坏程序正确性
4. **接口分离原则 (ISP)**: 不要强迫客户依赖于它们不使用的方法
5. **依赖倒置原则 (DIP)**: 依赖于抽象，而不是具体实现，减少类之间的直接依赖

### 通信机制规范
- **UI → Service**: 方法调用
- **Service → UI**: PyQt信号
- **数据传递**: 统一使用模型类，禁止原始字典
- **异常处理**: Service层捕获并转换为信号，UI层只负责展示

---

## 📝 标准文件模板

### Model 层模板
```python
# -*- coding: utf-8 -*-
"""
数据模型｜一句话用途说明
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass(frozen=True)
class XxxInfo:
    """XXX信息数据模型
    
    用途: 封装XXX相关的所有数据字段
    特点: 不可变数据契约，确保数据一致性
    """
    id: str
    name: str
    status: str
    created_at: datetime
    # 所有字段必须有类型注解
```

### Service 层模板
```python
# -*- coding: utf-8 -*-
"""
XXX业务服务｜专门负责XXX相关的业务逻辑处理
"""
from PyQt5.QtCore import QObject, pyqtSignal
from typing import Optional, List
from dataclasses import dataclass
import logging

from flowdesk.models import XxxInfo
from flowdesk.utils import xxx_utils

class XxxService(QObject):
    """XXX业务服务
    
    职责: 处理XXX相关的所有业务逻辑
    原则: 单一职责，无UI依赖，通过信号通信
    """
    
    # 信号定义
    xxx_updated = pyqtSignal(XxxInfo)  # XXX更新信号
    error_occurred = pyqtSignal(str)   # 错误信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def process_xxx(self, data: XxxInfo) -> Optional[XxxInfo]:
        """处理XXX业务逻辑"""
        try:
            # 业务逻辑实现
            result = self._do_process(data)
            self.xxx_updated.emit(result)
            return result
        except Exception as e:
            self.logger.error(f"处理XXX失败: {e}")
            self.error_occurred.emit(str(e))
            return None
```

### UI 层模板
```python
# -*- coding: utf-8 -*-
"""
XXX界面组件｜负责XXX功能的用户界面展示
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

from flowdesk.services import XxxService
from flowdesk.models import XxxInfo

class XxxWidget(QWidget):
    """XXX界面组件
    
    职责: 纯UI展示，无业务逻辑
    原则: 只接收信号，只调用Service方法
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_services()
        self._connect_signals()
    
    def _setup_ui(self):
        """初始化UI组件"""
        self.layout = QVBoxLayout(self)
        # UI组件初始化
    
    def _setup_services(self):
        """初始化服务依赖"""
        self.xxx_service = XxxService(self)
    
    def _connect_signals(self):
        """连接信号槽"""
        self.xxx_service.xxx_updated.connect(self._on_xxx_updated)
        self.xxx_service.error_occurred.connect(self._on_error)
    
    @pyqtSlot(XxxInfo)
    def _on_xxx_updated(self, info: XxxInfo):
        """处理XXX更新信号"""
        # 更新UI显示
        pass
    
    @pyqtSlot(str)
    def _on_error(self, error_msg: str):
        """处理错误信号"""
        # 显示错误信息
        pass
```

### Utils 层模板
```python
# -*- coding: utf-8 -*-
"""
XXX工具函数｜提供XXX相关的纯函数工具
"""
from typing import Optional, List, Dict, Any
import re

def validate_xxx(value: str) -> bool:
    """验证XXX格式
    
    Args:
        value: 待验证的值
        
    Returns:
        bool: 验证结果
    """
    # 纯函数实现
    pass

def format_xxx(data: Dict[str, Any]) -> str:
    """格式化XXX数据
    
    Args:
        data: 原始数据字典
        
    Returns:
        str: 格式化后的字符串
    """
    # 纯函数实现
    pass
```

---

## ✅ 新功能开发检查清单

### 代码质量标准
| 检查点 | 通过标准 | 检查命令 |
|---|---|---|
| 📏 **文件行数** | ≤400行有效代码 | `wc -l filename.py` |
| 📦 **模块导出** | 立即更新 `__init__.py` 的 `__all__` | 手动检查 |
| 🎨 **样式管理** | 零 `setStyleSheet`，全部通过 `StylesheetService` | `grep -r "setStyleSheet" src/` |
| 📁 **资源路径** | 统一使用 `resource_path()` | `grep -r "assets/" src/` |
| 🔧 **版本兼容** | Win7自动降级并提示 | 手动测试 |
| 🧪 **单元测试** | Service公共方法100%覆盖 | `pytest --cov=src tests/` |
| 📝 **日志规范** | 支持 `-v`/`--verbose` 调试模式 | `python app.py -v` |

### Claymorphism 设计风格要求
| 元素 | 设计标准 |
|---|---|
| 🎨 **按钮** | 使用渐变色，支持悬停效果 |
| 🖼️ **面板** | 柔和阴影，圆角边框 |
| 🎯 **对话框** | 毛玻璃效果，居中显示 |
| 📱 **自适应** | 最小宽度保护，智能缩放 |

### UI四大铁律
| 铁律 | 具体要求 |
|---|---|
| 🚫 **禁止样式重复** | 模块化QSS管理，禁止内联样式和 `!important` |
| 🔄 **严格自适应布局** | 使用QLayout，支持窗口缩放 |
| 📏 **最小宽度保护** | 设置 `setMinimumWidth()` 防止组件挤压 |
| ⚙️ **智能组件缩放** | 关键组件设置合理的 `sizePolicy` |

---

## 🔧 「零风险拆包」详细流程

### 拆包前准备
```bash
# 1. 备份当前状态
git add .
git stash push -m "拆包前备份: $(date)"

# 2. 确认测试通过
python -m pytest tests/ -v

# 3. 统计目标文件行数
wc -l target_file.py
```

### 四步拆包流程

#### 步骤① 新建目录/文件
| 动作 | 检查项 | 示例 |
|---|---|---|
| 按职责创建新文件 | 每个文件 ≤400行 | `adapter_info_retriever.py` |
| 使用标准模板 | 包含中文用途说明 | 见上方模板 |
| 创建对应测试文件 | `test_*.py` | `test_adapter_info_retriever.py` |

#### 步骤② 零业务逻辑迁移
| 动作 | 检查项 | 禁止操作 |
|---|---|---|
| 纯代码搬运 | 不改变任何行为 | 修改方法签名 |
| 保持导入关系 | UI层无Service/Model/Utils导入 | 添加新的业务逻辑 |
| 维护注释完整性 | 所有注释原样保留 | 删除或修改现有注释 |

#### 步骤③ 信号槽零改动
| 动作 | 检查项 | 必须保留 |
|---|---|---|
| 保留所有信号定义 | 信号名称不变 | `pyqtSignal` 定义 |
| 保留所有槽连接 | 连接关系不变 | `connect()` 调用 |
| 保留资源路径 | 路径引用不变 | `resource_path()` 调用 |

#### 步骤④ 更新导出和依赖
| 动作 | 检查项 | 检查命令 |
|---|---|---|
| 更新 `__init__.py` | 添加到 `__all__` | 手动检查导出 |
| 检查循环依赖 | 无相互导入 | `python -c "import new_module"` |
| 验证功能完整性 | 所有功能正常 | 手动功能测试 |

### 拆包后验证
```bash
# 1. 运行完整测试套件
python -m pytest tests/ -x --tb=short

# 2. 检查代码质量
flake8 src/ --max-line-length=120

# 3. 验证应用启动
python src/flowdesk/app.py --help

# 4. 如果失败，立即回滚
if [ $? -ne 0 ]; then
    git stash pop
    echo "❌ 拆包失败，已回滚"
else
    echo "✅ 拆包成功"
fi
```

### 拆包成功标准
- ✅ 所有测试通过 (`pytest` 0失败)
- ✅ 应用正常启动
- ✅ 原有功能完全保留
- ✅ 无新增警告或错误
- ✅ 代码行数符合要求 (≤400行/文件)

---

## 🪟 弹窗/对话框专用守则

### 文件组织规范
| 组件 | 位置 | 命名规范 | 示例 |
|---|---|---|---|
| 对话框类 | `ui/dialogs/` | `xxx_dialog.py` | `add_ip_dialog.py` |
| 样式文件 | `ui/qss/` | `xxx_dialog.qss` | `add_ip_dialog.qss` |
| 测试文件 | `tests/ui/dialogs/` | `test_xxx_dialog.py` | `test_add_ip_dialog.py` |

### 对话框设计原则

#### 1. 样式隔离
```css
/* 所有对话框样式必须用ID选择器包裹 */
#AddIPDialog {
    background: qlineargradient(...);
    border-radius: 12px;
}

#AddIPDialog QPushButton {
    /* 按钮样式 */
}
```

#### 2. 组件复用
| 组件类型 | 复用来源 | 用途 |
|---|---|---|
| 渐变按钮 | `widgets/gradient_button.py` | 确认、取消按钮 |
| 输入验证 | `widgets/validated_line_edit.py` | 表单输入 |
| 状态提示 | `widgets/status_indicator.py` | 操作反馈 |

#### 3. 业务逻辑分离
```python
class AddIPDialog(QDialog):
    """添加IP对话框 - 纯UI展示"""
    
    # 信号定义
    ip_add_requested = pyqtSignal(str, str)  # IP, 描述
    
    def _on_confirm_clicked(self):
        """确认按钮点击 - 只发射信号"""
        ip = self.ip_input.text()
        desc = self.desc_input.text()
        self.ip_add_requested.emit(ip, desc)  # 业务逻辑交给Service
```

### 对话框生命周期

#### 创建流程
1. **样式加载优先**: 确保QSS文件已通过StylesheetService加载
2. **居中显示**: 使用 `move()` 方法居中到父窗口
3. **模态设置**: 根据需要设置 `setModal(True/False)`
4. **焦点管理**: 设置合理的Tab顺序和默认焦点

#### 关闭处理
```python
def closeEvent(self, event):
    """对话框关闭事件处理"""
    # 清理资源
    self._cleanup_resources()
    # 发射关闭信号
    self.dialog_closed.emit()
    super().closeEvent(event)
```

---

## 🧪 测试规范

### 测试覆盖率要求
| 层级 | 覆盖率要求 | 测试重点 |
|---|---|---|
| **Service** | 100% 公共方法 | 业务逻辑、异常处理 |
| **Model** | 100% 数据验证 | 数据完整性、类型安全 |
| **Utils** | 100% 函数覆盖 | 边界条件、异常情况 |
| **UI** | 主要交互流程 | 信号发射、状态更新 |

### 测试文件组织
```
tests/
├── unit/                    # 单元测试
│   ├── test_services/       # Service层测试
│   ├── test_models/         # Model层测试
│   └── test_utils/          # Utils层测试
├── integration/             # 集成测试
│   └── test_workflows/      # 业务流程测试
└── ui/                      # UI测试
    ├── test_dialogs/        # 对话框测试
    └── test_widgets/        # 组件测试
```

### 测试命令
```bash
# 运行所有测试
python -m pytest tests/ -v

# 生成覆盖率报告
python -m pytest --cov=src --cov-report=html tests/

# 只运行Service层测试
python -m pytest tests/unit/test_services/ -v

# 测试特定模块
python -m pytest tests/unit/test_services/test_network_service.py -v
```

---

## 📝 异常处理和日志规范

### 异常处理层级
| 层级 | 异常处理策略 | 示例 |
|---|---|---|
| **Utils** | 抛出具体异常 | `raise ValueError("无效的IP地址")` |
| **Service** | 捕获并转换为信号 | `self.error_occurred.emit(str(e))` |
| **UI** | 显示用户友好提示 | `QMessageBox.warning(self, "错误", msg)` |

### 日志级别使用
```python
# DEBUG: 详细的调试信息（仅在 -v 模式显示）
self.logger.debug(f"正在处理网卡: {adapter_name}")

# INFO: 重要操作和状态变化
self.logger.info(f"网卡配置更新成功: {adapter_name}")

# WARNING: 可恢复的问题
self.logger.warning(f"网卡状态获取失败，使用默认值: {adapter_name}")

# ERROR: 严重错误
self.logger.error(f"网络服务初始化失败: {str(e)}")
```

### 日志格式规范
- **操作日志**: `[操作类型] 操作对象: 结果描述`
- **错误日志**: `[错误类型] 错误位置: 错误详情`
- **状态日志**: `[组件名称] 状态变化: 从X到Y`

---

## 🎯 记忆口诀

### 开发铁律 (背诵版)
> **"四层分离、数据只读、服务单一、UI只收信号"**
> **"样式全局、测试先行、异常分层、日志分级"**

### 拆包口诀
> **"备份测试、纯搬代码、信号不动、验证回滚"**

### 质量标准
> **"四百行限、模板规范、覆盖率百、调试可见"**

---

## 🚀 快速检查命令

```bash
# 一键质量检查脚本
#!/bin/bash
echo "🔍 FlowDesk 代码质量检查"

# 检查文件行数
echo "📏 检查文件行数 (>400行的文件):"
find src/ -name "*.py" -exec wc -l {} + | awk '$1 > 400 {print $2 ": " $1 "行"}'

# 检查内联样式
echo "🎨 检查内联样式:"
grep -r "setStyleSheet" src/ || echo "✅ 无内联样式"

# 运行测试
echo "🧪 运行测试套件:"
python -m pytest tests/ -x --tb=short

# 检查覆盖率
echo "📊 生成覆盖率报告:"
python -m pytest --cov=src --cov-report=term-missing tests/

echo "✅ 质量检查完成"
```

将此脚本保存为 `scripts/quality_check.sh` 并设置执行权限：
```bash
chmod +x scripts/quality_check.sh
./scripts/quality_check.sh
```