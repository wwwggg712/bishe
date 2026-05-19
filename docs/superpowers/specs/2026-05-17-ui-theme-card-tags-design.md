# 全站主题统一与卡片“主题标签框”改造设计

## 背景与问题

当前界面存在以下体验问题：

- 强调色偏蓝，和“多彩潮玩/橙黄能量”审美目标不一致，且侧边栏选中态、按钮、图表/标签叠加后显得杂乱。
- 卡片缺少“主题标签框”的视觉锚点，用户需要先读标题/描述才能确认模块主题，浏览路径不清晰。
- “演示口径”说明文案占据显著位置，影响页面整洁；但答辩时又需要可随时展开解释口径。
- 商家页部分区域在固定两列网格下出现明显留白（同层级仅一张卡片时右侧空列常驻）。

目标：在不引入新字体文件与第三方 UI 库的前提下，统一全站卡片与强调色风格，使“先看主题→再看数据→再看解释/动作”的层级更清晰，适合答辩演示。

## 设计目标

- 全站统一强调色为“橙黄能量”体系，减少蓝色主导。
- 卡片头部增加明显的“主题标签框”（保留英文标签，不改成中文）。
- “演示口径”不以 badge 常驻展示，改为可折叠说明，默认收起。
- 修复商家页留白：单卡模块自动占满整行或网格自适应，避免右侧空一大片。
- 保持现有页面结构与数据流，尽量通过 CSS token 与少量模板调整实现，降低回归风险。

## 视觉规范（Tokens）

在 `:root` 中新增/替换：

- `--accent`：橙色主色（用于按钮/选中态/关键数字）
- `--accent-2`：黄色辅色（用于渐变与光晕）
- `--accent-gradient`：橙→黄渐变
- `--accent-shadow`：强调色阴影（较轻，避免“糊一坨”）
- `--card-bg`：卡片底（偏干净白底，叠加轻微橙黄光晕角落）
- `--card-border`：卡片描边（淡橙）
- `--card-radius`：统一圆角

约束：

- 不引入外部字体下载；仅调整 font-family fallback 与字重/字距。
- 避免高饱和大面积渐变填充正文区域；渐变仅用于 header/按钮/轻光晕。

## 组件与样式改造

### 1) 侧边栏与按钮（去蓝）

- `.app-shell__nav-link.router-link-active`：改用 `--accent-gradient`，阴影使用 `--accent-shadow`，移除蓝系强投影。
- `.primary-button`：跟随 `--accent`/`--accent-gradient`。
- `.ghost-button`：保持白底，但 hover/active 边框与文字使用 `--accent`。

### 2) 卡片“主题标签框”（不改英文）

将所有卡片 header 内的 `.section-kicker` 从纯文本样式升级为“标签框”：

- 白底/半透明底
- 细描边（`--card-border`）
- 左侧小圆点点缀（用伪元素实现）
- 更清晰的字重与 letter-spacing

适用范围：

- 客户端（Customer）所有模块 header
- 商家端（Merchant）所有模块 header
- 管理员端（Admin）所有模块 header

### 3) 列表卡片条理与标签（brand/category/status）

- 列表卡片统一 `--card-bg / --card-border / --card-radius`，hover 仅轻微上浮与阴影增强。
- 推荐卡片内的品牌/品类标签：
  - 改为“贴纸胶囊”：白底 + 描边（主色系与副色系区分）+ 文字同色
  - 不再使用大块纯色底，避免“糊”

### 4) “演示口径”说明收纳（不做 badge）

调整商家经营总览 `MerchantOpsOverview` 的标题区域：

- 标题 `经营总览` 保持
- 口径说明改为 `<details>` / `<summary>`：
  - 默认收起：只显示 `口径说明（点击展开）`
  - 展开后显示现有解释文案（purchase 次数估算等）

### 5) 商家页留白修复

对 `.merchant-dashboard__layer-grid` 做两类增强：

- 自适应列：使用 `auto-fit + minmax(...)`（或保持 2 列但当子元素数量为 1 时设置 `grid-column: 1 / -1`）
- 对已知“只有一块内容但包在 grid 中”的层级，给该卡片加 `--span-full` 类名，占满整行。

优先处理出现明显留白的 section（overview/analysis/core 内的 grid）。

## 兼容性与测试

- 前端：保持 Vitest 通过，主要涉及 CSS 与少量模板结构变化：
  - 更新或新增断言尽量避免依赖具体颜色值（只断言存在关键文案/结构）。
- 后端：不改动接口，pytest 保持通过。

## 交付物清单

- `frontend/src/styles/theme.css`：新增橙黄能量 token；侧边栏/按钮/卡片/标签框样式统一；网格留白修复样式。
- `frontend/src/views/merchant/MerchantOpsOverview.vue`：口径说明改为可折叠 `<details>`。
- 可能的局部页面 class 微调：仅在需要“单卡占满整行”时增加 class。
- 测试验证：`npm test`（frontend）、`python -m pytest -q`（backend）。

