# 全站楷书：字体更清晰更大（方案A）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改变全站楷书字体栈的前提下，提升整体字号与弱文本可读性（更清晰、更“实”），减少“发浅/偏小”的观感。

**Architecture:** 仅修改 `frontend/src/styles/theme.css` 的全局基础字号、默认字重，以及入口弱文本（eyebrow/label）的字号与颜色；不改组件结构与交互逻辑。

**Tech Stack:** Vue 3 + Vite + Vitest + CSS（全局样式 `frontend/src/styles/theme.css`）

---

### Task 1: 全局基础字号与默认字重

**Files:**
- Modify: `frontend/src/styles/theme.css`（`html`、`body`）

- [ ] **Step 1: 在 `html` 增加基础字号**

将以下样式加入到 `html, body` 规则之前（或紧邻其后也可，但需确保覆盖默认值）：

```css
html {
  font-size: 17px;
}
```

- [ ] **Step 2: 在 `body` 增加默认字重**

在现有 `body { ... }` 中加入：

```css
font-weight: 500;
```

### Task 2: 入口弱文本（eyebrow/label）更清晰

**Files:**
- Modify: `frontend/src/styles/theme.css`（`.login-panel__eyebrow/.workspace-view__eyebrow/.app-shell__eyebrow/.app-shell__header-label`）

- [ ] **Step 1: 调整弱文本颜色与字号**

将现有规则：

```css
.login-panel__eyebrow,
.workspace-view__eyebrow,
.app-shell__eyebrow,
.app-shell__header-label {
  color: #475569;
  font-size: 0.875rem;
}
```

调整为：

```css
.login-panel__eyebrow,
.workspace-view__eyebrow,
.app-shell__eyebrow,
.app-shell__header-label {
  color: #334155;
  font-size: 0.92rem;
}
```

### Task 3: 验证

**Files:**
- No new files

- [ ] **Step 1: 运行前端测试**
  - Run: `npm test`
  - Expected: 全部通过

- [ ] **Step 2: 本地人工检查关键页面**
  - 登录页：标题区与说明文字清晰、字号更舒适
  - 侧边栏：E-commerce/当前登录等小字不再发灰
  - 商家仪表盘：说明/标签更清晰，布局无明显挤压或溢出
