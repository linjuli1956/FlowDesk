# FlowDesk UI组件与样式规范

> **设计风格更新**：  Claymorphism 设计风格

## 1. 核心原则
- ✅ 唯一外置 QSS：所有样式集中于 `src/flowdesk/ui/qss/main_pyqt5.qss`。
- ❌ 禁止任何内联样式：禁止 `setStyleSheet()` 与内联片段。
- ❌ 禁止 `!important`：通过选择器特异性与结构化命名解决优先级。

## 2. 命名与选择器规范
- objectName 命名：`<scope>_<widget>_<role>`（蛇形命名），示例：`home_tab_connect_btn`。
- 作用域层级：窗口/Tab 为前缀，如 `ip_config_...`，避免样式串扰。
- 基类样式 + 定制：
  - 仅定义一次通用组件基类样式（如 `QPushButton`）。
  - 专用样式通过 `#objectName` 扩展，避免重复定义。

## 3. 卡片式彩色按钮设计系统
### 3.1 颜色方案（基于UI截图分析）
- 运行态 Qt5 采用预处理/构建脚本替换方案；颜色变量命名：
```
--background-primary: #f5f5f5        # 主背景色（浅灰）
--background-secondary: #ffffff      # 卡片背景色（白色）
--text-primary: #333333              # 主文本色（深灰）
--text-secondary: #666666            # 次要文本色（中灰）
--border-color: #e0e0e0              # 边框颜色（浅灰）

# 功能按钮彩色方案
--btn-blue: #4A90E2                  # 蓝色按钮（主要操作）
--btn-green: #7ED321                 # 绿色按钮（成功/启用）
--btn-red: #D0021B                   # 红色按钮（危险/禁用）
--btn-orange: #F5A623                # 橙色按钮（警告/工具）
--btn-purple: #9013FE                # 紫色按钮（特殊功能）
--btn-cyan: #50E3C2                  # 青色按钮（网络相关）

# 状态徽章颜色
--badge-connected: #7ED321           # 已连接（绿色）
--badge-disconnected: #D0021B        # 未连接（红色）
--badge-dhcp: #4A90E2                # DHCP模式（蓝色）
--badge-static: #F5A623              # 静态IP（橙色）
```

### 3.2 视觉设计原则
- **卡片容器**：白色背景，圆角8-12px，淡灰色边框1px
- **功能按钮**：圆角6-8px，纯色背景，白色文字，hover时加深10%
- **输入框**：圆角4-6px，白色背景，灰色边框，聚焦时蓝色边框
- **状态徽章**：圆角12px，小尺寸，对应状态颜色背景
- **布局间距**：卡片间距12px，内容边距8-16px

### 3.3 QSS 实现方案（卡片式风格）
```css
/* 主窗口背景 */
QMainWindow {
  background-color: #f5f5f5;
}

/* 基类按钮 - 蓝色主题 */
QPushButton {
  color: white;
  background-color: #4A90E2;
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  font-weight: bold;
  min-height: 24px;
}
QPushButton:hover {
  background-color: #357ABD;
}
QPushButton:pressed {
  background-color: #2E6DA4;
}
QPushButton:disabled {
  background-color: #cccccc;
  color: #999999;
}

/* 彩色按钮变体 */
#green_btn { background-color: #7ED321; }
#green_btn:hover { background-color: #6BB91C; }
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