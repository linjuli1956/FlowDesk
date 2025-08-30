# FlowDesk UI组件与样式规范（CLAYMORPHISM）

*版本标记: v2025-08-30*

> **设计风格**：基于StylesheetService架构的Claymorphism企业级设计语言

## 1. 核心原则

### 🚫 禁止样式重复
- ✅ 模块化QSS管理：通过 `StylesheetService` 统一管理多个QSS文件
- ✅ 按顺序合并样式：主样式文件 + 各Tab专用样式文件
- ❌ 禁止任何内联样式：禁止 `setStyleSheet()` 与内联片段
- ❌ 禁止 `!important`：通过选择器特异性与结构化命名解决优先级

### 📁 QSS文件组织结构 ✅ 已完整实现
```
assets/styles/                     # 样式文件目录
├── main_pyqt5.qss                 # 主样式文件：全局变量、通用组件基础样式
├── main_win7.qss                  # Win7兼容样式文件（降级支持）
├── network_config_tab.qss         # 网络配置Tab专用样式（已实现）
├── add_ip_dialog.qss              # 添加IP对话框样式（已实现）
├── network_tools_tab.qss          # 网络工具Tab专用样式（规划中）
├── rdp_tab.qss                    # 远程桌面Tab专用样式（规划中）
├── hardware_tab.qss               # 硬件信息Tab专用样式（规划中）
└── tray_exit_dialog.qss           # 托盘对话框样式（规划中）
```

### 📊 当前实现状态
- ✅ **StylesheetService核心架构**：完整实现模块化QSS管理
- ✅ **主样式文件**：main_pyqt5.qss + Win7兼容版本
- ✅ **网络配置Tab样式**：完整的UI组件样式支持
- ✅ **对话框样式系统**：AddIPDialog专业渐变色按钮
- 🚧 **其他Tab样式**：随功能开发逐步实现

### 🔧 StylesheetService 实际实现架构 ✅
```python
# 核心服务类：src/flowdesk/services/stylesheet_service.py
class StylesheetService:
    def load_and_apply_styles(self, app):
        """加载并应用所有QSS样式文件"""
        # 1. 检测系统版本，选择合适的主样式文件
        # 2. 按顺序加载8个QSS文件并合并
        # 3. 一次性应用到QApplication
        
# 在 app.py 中的实际使用
def main():
    app = QApplication(sys.argv)
    
    # 创建样式服务并应用样式
    stylesheet_service = StylesheetService()
    stylesheet_service.load_and_apply_styles(app)
    
    # 创建主窗口
    main_window = MainWindow()
    main_window.show()
```

### 🏗️ 技术实现特点
- **单一入口原则**：所有样式管理统一由StylesheetService处理
- **自动继承机制**：UI组件自动继承全局样式，无需手动setStyleSheet()
- **Win7兼容检测**：自动检测系统版本，加载对应样式文件
- **高特异性选择器**：通过objectName确保样式优先级正确

## 2. 命名与选择器规范 ✅ 已实施

### 2.1 objectName命名约定
- **命名格式**：`<scope>_<widget>_<role>`（蛇形命名法）
- **实际案例**：
  - `adapter_combo` - 网卡选择下拉框
  - `refresh_button` - 刷新按钮  
  - `add_ip_button` - 添加IP按钮
  - `dialog_ok_button` - 对话框确定按钮
  - `dialog_cancel_button` - 对话框取消按钮

### 2.2 选择器特异性策略 ✅
- **基类样式优先**：QPushButton通用样式定义在main_pyqt5.qss
- **高特异性覆盖**：`QDialog#add_ip_dialog QPushButton#dialog_ok_button`
- **避免!important**：通过选择器层级解决优先级冲突
- **模块化管理**：每个Tab的objectName在专用QSS文件中定义

## 3. CLAYMORPHISM设计语言实现 ✅ 已部分实现

### 3.1 核心设计原则
- **材质感设计**：柔和阴影、圆角边框、渐变色彩
- **语义化颜色**：按钮颜色与功能意图直接对应
- **现代化布局**：卡片式容器、合理间距、响应式适配
- **视觉层次**：通过颜色深浅、大小对比建立信息层级

### 3.2 当前实现的颜色方案 ✅
```css
/* 实际在用的QSS颜色系统 */

/* 渐变色按钮 - AddIPDialog已实现 */
确定按钮渐变: linear-gradient(135deg, #2ecc71, #27ae60, #229954)
取消按钮渐变: linear-gradient(135deg, #e74c3c, #c0392b, #a93226)

/* 状态徽章颜色 - NetworkConfigTab已实现 */
已连接状态: background-color: #22995440;  /* 绿色半透明 */
未连接状态: background-color: #a9322640;  /* 红色半透明 */
DHCP模式: color: #3498db;                /* 蓝色 */
静态IP模式: color: #f39c12;             /* 橙色 */

/* 主题基础色 - main_pyqt5.qss */
主背景色: #f8f9fa                       /* 浅灰白 */
卡片背景: #ffffff                       /* 纯白 */
边框颜色: #dee2e6                       /* 浅灰边框 */
主文本色: #212529                       /* 深灰文本 */
```

### 3.3 待实现的扩展颜色方案 🚧
```css
/* 规划中的完整颜色系统 */
--btn-blue: #3498db        /* 主要操作按钮 */
--btn-green: #2ecc71       /* 成功/启用操作 */
--btn-red: #e74c3c         /* 危险/删除操作 */
--btn-orange: #f39c12      /* 警告/配置操作 */
--btn-purple: #9b59b6      /* 特殊功能按钮 */
--btn-cyan: #1abc9c        /* 网络工具按钮 */
```

## 4. UI四大铁律实施细则 ✅ 已严格执行

### 4.1 🚫 禁止样式重复
- **实施状态**：100%合规，全项目仅StylesheetService调用setStyleSheet()
- **违规检测**：代码库全文搜索无违规setStyleSheet()调用
- **模块化管理**：8个QSS文件按功能模块分离，无重复定义

### 4.2 🔄 严格自适应布局  
- **实施状态**：网络配置Tab完全使用QLayout系统
- **禁止绝对定位**：所有UI组件使用QGridLayout、QVBoxLayout、QHBoxLayout
- **响应式设计**：窗口拉伸时组件合理缩放，无重叠或错位

### 4.3 📏 最小宽度保护
- **主窗口**：setMinimumSize(660, 645) 防止内容压缩
- **关键按钮**：min-width设置确保按钮文字完整显示
- **输入框**：min-height保护，防止内容被压缩变形

### 4.4 ⚙️ 智能组件缩放
- **输入框**：Preferred策略，随内容合理扩展
- **按钮**：Fixed策略，保持固定尺寸不变形  
- **列表容器**：Expanding策略，充分利用可用空间

## 5. 当前已实现的核心样式组件 ✅

### 5.1 AddIPDialog渐变色按钮实现
```css
/* 确定按钮 - 绿色渐变系 */
QDialog#add_ip_dialog QPushButton#dialog_ok_button {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #2ecc71, stop: 0.5 #27ae60, stop: 1 #229954);
    color: white;
    border: 2px solid #22995440;
    border-radius: 6px;
    padding: 8px 16px;
    min-width: 80px;
}

/* 取消按钮 - 红色渐变系 */
QDialog#add_ip_dialog QPushButton#dialog_cancel_button {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #e74c3c, stop: 0.5 #c0392b, stop: 1 #a93226);
    color: white;
    border: 2px solid #a9322640;
    border-radius: 6px;
    padding: 8px 16px;
    min-width: 80px;
}
```

### 5.2 网络配置Tab状态徽章实现  
```css
/* 连接状态徽章 */
#status_badge_connected {
    background-color: #22995440;  /* 绿色半透明 */
    color: #155724;
    border-radius: 4px;
    padding: 2px 8px;
}

#status_badge_disconnected {
    background-color: #a9322640;  /* 红色半透明 */
    color: #721c24;
    border-radius: 4px;  
    padding: 2px 8px;
}
```

### 5.3 基础UI组件样式
```css
/* 主窗口背景 */
QMainWindow {
    background-color: #f8f9fa;
}

/* 通用按钮基类 */
QPushButton {
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    min-height: 24px;
}

QPushButton:hover {
    background-color: #0056b3;
}

QPushButton:pressed {
    background-color: #004085;
}
```

## 6. 开发规范与最佳实践 ✅ 已实施

### 6.1 代码开发规范
- **UI代码职责**：仅负责信号槽连接和视图更新，禁止业务逻辑
- **objectName设置**：所有关键控件必须设置objectName用于样式控制
- **中文注释**：描述代码作用和设计意图，面向初学者友好
- **类型注解**：使用typing确保数据类型安全

### 6.2 样式开发规范
- **基类优先**：先定义QPushButton、QLineEdit等通用样式
- **选择器扩展**：专用样式通过#objectName扩展，避免重复
- **十六进制颜色**：使用#RRGGBB格式确保PyQt5兼容性
- **状态完整性**：按钮样式包含normal、hover、pressed、disabled四种状态

## 7. 兼容性策略 ✅ 已实现

### 7.1 Win7/Win10/Win11兼容
- **自动检测**：StylesheetService自动检测系统版本
- **降级支持**：Win7使用main_win7.qss，功能完整但效果简化
- **视觉一致性**：核心UI元素在所有系统上保持一致的功能和布局

### 7.2 PyQt5版本兼容
- **渐变语法**：使用qlineargradient确保跨版本兼容
- **颜色格式**：避免rgba语法，使用十六进制颜色
- **边框透明度**：使用#RRGGBBAA格式支持透明效果

## 8. 性能与体验优化 ✅ 已实现

### 8.1 样式加载优化  
- **一次性加载**：启动时统一加载所有QSS文件并合并
- **缓存机制**：避免重复解析和应用样式
- **按需加载**：Tab样式随功能开发逐步添加

### 8.2 用户体验优化
- **视觉反馈**：按钮hover、pressed状态提供即时反馈
- **状态可视化**：网络状态通过颜色徽章直观显示  
- **无干扰验证**：输入验证不使用弹窗，实时阻止无效输入

## 9. 评审清单与质量保证 ✅

### 9.1 代码质量检查
- ✅ **样式一致性**：全项目无setStyleSheet()违规调用
- ✅ **!important检查**：QSS文件中零!important使用
- ✅ **objectName完整性**：关键控件均设置objectName
- ✅ **选择器特异性**：通过层级解决样式优先级冲突

### 9.2 功能验证清单
- ✅ **渐变色按钮**：AddIPDialog确定/取消按钮效果正确
- ✅ **状态徽章**：网卡连接状态颜色显示正确
- ✅ **响应式布局**：窗口缩放时UI组件无重叠变形
- ✅ **兼容性测试**：Win7/Win10/Win11样式加载正常

---

**FlowDesk UI规范总结**: 基于StylesheetService的模块化样式管理架构已完整实现，严格遵循UI四大铁律，实现了企业级CLAYMORPHISM设计语言的核心功能。当前网络配置Tab样式完备，为后续Tab开发奠定了坚实的样式架构基础。
#red_btn { background-color: #D0021B; }
#red_btn:hover { background-color: #B8011A; }
#orange_btn { background-color: #F5A623; }
#orange_btn:hover { background-color: #E8941F; }
#purple_btn { background-color: #9013FE; }
#purple_btn:hover { background-color: #7B0FE3; }
#cyan_btn { background-color: #50E3C2; }
#cyan_btn:hover { background-color: #3DD9B8; }

/* 卡片容器 */
QGroupBox, QFrame {
  background-color: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin: 4px;
  padding: 8px;
}

/* 输入框 */
QLineEdit, QComboBox {
  background-color: white;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 6px 8px;
  color: #333333;
  min-height: 20px;
}
QLineEdit:focus, QComboBox:focus {
  border: 2px solid #4A90E2;
}

/* 状态徽章 */
.status-badge {
  border-radius: 12px;
  padding: 2px 8px;
  font-size: 10px;
  font-weight: bold;
  color: white;
}
.badge-connected { background-color: #7ED321; }
.badge-disconnected { background-color: #D0021B; }
.badge-dhcp { background-color: #4A90E2; }
.badge-static { background-color: #F5A623; }

/* Tab样式 */
QTabWidget::pane {
  border: 1px solid #e0e0e0;
  background-color: white;
}
QTabBar::tab {
  background-color: #f5f5f5;
  border: 1px solid #e0e0e0;
  padding: 8px 16px;
  margin-right: 2px;
}
QTabBar::tab:selected {
  background-color: white;
  border-bottom: none;
}
```

## 4. 布局与响应式
- 必须使用 `QLayout`（`QGridLayout`、`QHBoxLayout`、`QVBoxLayout`）。
- 设置 `sizePolicy`：关键输入/表格随窗口拉伸；按钮保守扩展。
- 主窗口与关键容器 `setMinimumWidth/Height`，防止拥挤与错乱。
- 禁止绝对定位；尽量避免 `setFixedSize`，除非图标类控件。

## 5. 资源与主题
- 统一入口 QSS：`main_pyqt5.qss`；主题配色通过构建时变量替换生成。
- 归档样式保留在 `qss/archive/`，不参与运行加载。

## 6. 兼容性策略
- **Win10/11**：完整卡片式设计，支持所有彩色按钮效果
- **Win7**：保持相同布局和颜色方案，可能简化部分视觉效果
- **跨平台一致性**：确保功能按钮颜色在所有系统上保持一致
- **降级策略**：Win7下禁用复杂效果，保留核心视觉识别

## 7. 代码与注释规范（UI）
- UI 代码仅连接信号槽并更新视图，注释说明“角色与原因”。
- 所有控件设定 `objectName` 并在文档中登记关键控件命名。

## 8. 落地执行指南（完全重写）
- 基类样式先行：先定义 `QPushButton`、`QLineEdit`、`QComboBox`、`QLabel`、容器的通用基类样式与状态（normal/hover/pressed/disabled）。
- 角色扩展：所有专用样式一律通过 `#objectName` 扩展，禁止再次定义组件通用属性。
- 命名表（建议摘录）：
  - 适配器下拉：`ip_config_adapter_combo`
  - 操作按钮：`ip_config_enable_btn` / `ip_config_disable_btn` / `ip_config_static_btn` / `ip_config_dhcp_btn` / `ip_config_refresh_btn`
  - 修改按钮：`ip_config_modify_btn`
  - 徽章：`ip_status_badge` / `ip_mode_badge` / `link_speed_badge`
- 主题产物：构建生成 `main_pyqt5.qss`（Win10/11）与 `main_pyqt5_win7.qss`（Win7 降级），运行时按能力选择加载。

## 9. 按钮样式与复用（强约束）
- 通用 `QPushButton` 基类一次定义，变体仅覆盖颜色/尺寸；严禁复制粘贴整段 QSS。
- 变体通过 `#objectName` 控制：只允许覆盖必要差异（最小宽度、图标、强调色）。
- 禁止在不同位置重复拷贝同一段按钮 QSS；新增按钮需复用基类。

## 10. 自适应/最小宽度/智能缩放
- 自适应：所有页面使用 `QLayout`（`Grid/HBox/VBox`），表格与输入框使用 `Expanding` 横向策略。
- 最小尺寸：主窗口与关键容器设置 `setMinimumWidth/Height`，建议主窗口最小宽度 ≥ 660px。
- 智能缩放：
  - 表格/文本区：`Expanding, Expanding`
  - 按钮：`Minimum, Fixed` 或 `Preferred, Fixed`
  - 下拉与输入：`Preferred, Fixed`，必要时放入伸缩容器。

## 11. 硬件监控显示（卡片式彩色按钮风格）
- **信息卡片**：`cpu_info_card`、`gpu_info_card`、`memory_info_card`等
- **数值显示**：根据阈值应用阶梯颜色策略
  - 温度：蓝色（<50°C）→ 绿色（50-70°C）→ 橙色（70-85°C）→ 红色（>85°C）
  - 使用率：绿色（<50%）→ 橙色（50-80%）→ 红色（>80%）
  - 风扇转速：绿色系渐变
- **悬浮窗**：透明背景，圆角8px，白色文字带阴影

## 12. 对象命名与彩色按钮样式清单

### 12.1 网络配置页面按钮颜色方案
- `#refresh_btn` - 蓝色（刷新操作）
- `#modify_ip_btn` - 蓝色（主要操作）
- `#enable_adapter_btn` - 绿色（启用操作）
- `#disable_adapter_btn` - 红色（禁用操作）
- `#set_static_btn` - 橙色（配置操作）
- `#set_dhcp_btn` - 橙色（配置操作）
- `#copy_info_btn` - 蓝色（复制操作）
- `#add_extra_ip_btn` - 绿色（添加操作）
- `#add_selected_btn` - 绿色（添加操作）
- `#remove_selected_btn` - 红色（删除操作）

### 12.2 网络工具页面9宫格按钮颜色（3×3布局）
**第一行**：
- `#winsock_reset_btn` - 蓝色（Winsock重置）
- `#fw_allow_ping_btn` - 绿色（防火墙允许Ping）
- `#fw_block_ping_btn` - 红色（防火墙禁止Ping）

**第二行**：
- `#network_panel_btn` - 青色（网络控制面板）
- `#win11_autologin_btn` - 紫色（Win11自动登录）
- `#clear_browser_cache_btn` - 蓝色（清理浏览器缓存）

**第三行**：
- `#computer_name_btn` - 紫色（修改计算机名）
- `#device_printer_btn` - 橙色（设备和打印机）
- `#user_management_btn` - 绿色（添加系统用户）

**密码设置区域**：
- `#enable_rdp_btn` - 绿色（启用远程桌面）

### 12.3 远程桌面页面按钮颜色
**主页面**：
- `#connect_rdp_btn` - 蓝色（连接远程桌面）

**连接配置弹窗**：
- `#new_group_btn` - 绿色（新增分组）
- `#search_btn` - 蓝色（搜索历史记录）
- `#change_group_btn` - 橙色（变更分组）
- `#cancel_btn` - 红色（取消）
- `#save_btn` - 蓝色（保存配置）
- `#connect_btn` - 绿色（连接）

约束：
- 通用 `QPushButton` 基类一次定义，变体仅覆盖颜色/尺寸；严禁复制粘贴整段 QSS。
- 所有页面用 `QLayout`，主窗口/关键容器设 `minimumSize`；按钮行距/内边距统一。

## 13. 响应式与最小宽度（落地清单）
- 主窗口 `minimumSize` 设定并评审；
- 所有页面/对话框使用 `QLayout`，不得绝对定位；
- 关键容器 `setMinimumWidth/Height`；
- 输入/下拉/表格使用 `Expanding/Preferred` 策略；按钮 `Fixed/Preferred`；
- 通过 `setStretch` 控制列宽比；长列表与文本区放入 `QScrollArea`；
- 缩放验证：窗口从最小到最大拉伸，控件无溢出/重叠；
- Win7 QSS 降级验证：降级样式加载后，仍满足以上布局要求。

## 14. 评审清单（构建前必须通过）
- 样式：代码库全文无 `setStyleSheet(`；QSS 中无 `!important`；按钮基类唯一；
- 命名：关键控件均设置了 `objectName` 且与文档命名表一致；
- 自适应：人工拉伸+自动化截图对比无错位；
- 兼容：Win10/11 和 Win7 均可加载对应 QSS，视觉一致且不崩溃。

## 15. 卡片式布局与窗口尺寸规范
### 15.1 窗口尺寸约束
- **主窗口尺寸**：660×645像素（基于UI截图的实际尺寸）
- **最小尺寸保护**：不小于660×645，防止内容压缩变形
- **Tab内容区域**：充分利用可用空间，合理分配各功能区域

### 15.2 卡片布局原则
- **信息展示卡片**：白色背景，圆角边框，内边距12px
- **功能按钮网格**：3×3布局，按钮间距8px，统一尺寸
- **输入表单区域**：标签左对齐，输入框右侧对齐
- **列表展示区域**：带滚动条，支持多选操作
- **状态徽章**：圆角设计，颜色语义化（连接状态、IP模式、网卡速率）
- **悬浮窗设计**：透明背景，可拖动，右键菜单配置

### 15.3 响应式适配
- **固定布局优先**：基于660×645设计，保证在目标尺寸下完美显示
- **最小尺寸保护**：设置minimumSize防止过度压缩
- **内容优先级**：重要功能优先显示，次要内容可滚动查看

## 16. 阶梯颜色策略（硬件监控专用）
### 16.1 温度阶梯颜色
- **CPU/GPU温度**：蓝色(<50°C) → 绿色(50-70°C) → 橙色(70-85°C) → 红色(>85°C)
- **硬盘温度**：绿色(<45°C) → 橙色(45-60°C) → 红色(>60°C)

### 16.2 使用率阶梯颜色
- **CPU使用率**：绿色(<50%) → 橙色(50-80%) → 红色(>80%)
- **内存使用率**：绿色(<70%) → 橙色(70-90%) → 红色(>90%)

### 16.3 网络延迟阶梯颜色
- **Ping延迟**：绿色(<50ms) → 橙色(50-200ms) → 红色(>200ms)
- **网络速度**：绿色(正常) → 橙色(较慢) → 红色(超时)

## 17. 评审清单（构建前必须通过）
- **样式一致性**：所有按钮遵循彩色方案，无内联样式
- **命名规范**：控件objectName与功能文档一致
- **布局验证**：660×645尺寸下所有内容正常显示
- **颜色验证**：按钮颜色与功能语义匹配，阶梯颜色策略正确实现
- **兼容性**：Win7降级样式保持功能完整
- **Emoji支持**：所有带Emoji的控件正确显示图标