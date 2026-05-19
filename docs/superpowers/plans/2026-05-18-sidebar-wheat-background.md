# 侧边栏麦色浅底（方案2）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将应用侧边栏从深色渐变替换为麦色/奶油色系浅底轻渐变，并同步调整侧边栏文字与未选中导航项底色，保证可读性与整体一致性。

**Architecture:** 仅修改全局样式 `theme.css` 中侧边栏相关选择器，不改动组件结构与路由逻辑；保持现有选中态高亮样式不变，降低风险。

**Tech Stack:** Vue 3 + Vite + Vitest + CSS（全局样式 `frontend/src/styles/theme.css`）

---

### Task 1: 调整侧边栏背景与文字颜色

**Files:**
- Modify: `frontend/src/styles/theme.css`（`.app-shell__sidebar`、`.app-shell__title`、`.app-shell__subtitle`、`.app-shell__eyebrow`、`.app-shell__header-label`）

- [ ] **Step 1: 为侧边栏选择一组“麦色轻渐变”颜色值**
  - 目标：背景偏暖白/麦色，不叠加光斑；不刺眼；能承载粉蓝选中态按钮。
  - 建议候选：
    - 顶部：`#fff7e6`（奶油白）
    - 底部：`#f2e1c5`（淡麦色）
    - 分隔线：`rgba(148, 163, 184, 0.28)`

- [ ] **Step 2: 修改 `.app-shell__sidebar` 的背景、文字色与分隔线**
  - 将 `background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);` 替换为浅底轻渐变
  - 将 `color` 改为深色（例如 `#111827` / `#0f172a`）
  - 增加 `border-right: 1px solid rgba(148, 163, 184, 0.28);`

- [ ] **Step 3: 修改侧边栏标题与副标题颜色（适配浅底）**
  - `.app-shell__title`：深色（例如 `#111827`）
  - `.app-shell__subtitle`：中灰（例如 `#475569`）
  - `.app-shell__eyebrow`：中灰（例如 `#64748b`），保留大写与字距

### Task 2: 调整未选中导航项底色（更贴合麦色浅底）

**Files:**
- Modify: `frontend/src/styles/theme.css`（`.app-shell__nav-link`）

- [ ] **Step 1: 修改 `.app-shell__nav-link` 未选中态背景**
  - 将 `background: rgba(148, 163, 184, 0.12);` 替换为浅色半透明（例如 `rgba(255, 255, 255, 0.62)`）
  - 若边界不够清晰，补充：`border: 1px solid rgba(148, 163, 184, 0.22);`

- [ ] **Step 2: 确认选中态样式不变**
  - `.app-shell__nav-link.router-link-exact-active` / `.router-link-active` 保持 `var(--accent-gradient)` 与 `var(--accent-shadow)`

### Task 3: 验证

**Files:**
- No new files

- [ ] **Step 1: 运行前端测试**
  - Run: `npm test`
  - Expected: 全部通过

- [ ] **Step 2: 本地人工检查（3 个角色）**
  - merchant/customer/admin 登录后观察侧边栏：
    - 背景为麦色浅底渐变
    - 文字清晰可读
    - 未选中导航项是奶白底
    - 选中态仍为粉蓝渐变高亮
