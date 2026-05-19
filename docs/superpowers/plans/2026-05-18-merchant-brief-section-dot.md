# 今日经营简报小标题黑点 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为“今日经营简报”的小节标题（核心结论/机会点/风险预警/行动清单）增加小黑点前缀，使其更像小标题、更易识别。

**Architecture:** 仅修改 `theme.css`，在 `.merchant-brief__summary-title` 上使用 `::before` 伪元素绘制 6px 圆点；不改组件结构与数据逻辑。

**Tech Stack:** Vue 3 + Vite + Vitest + CSS

---

### Task 1: 样式实现

**Files:**
- Modify: `frontend/src/styles/theme.css`（`.merchant-brief__summary-title`）

- [ ] **Step 1: 给标题增加布局与圆点伪元素**

将 `.merchant-brief__summary-title` 调整为 `inline-flex`，并增加：

```css
.merchant-brief__summary-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.merchant-brief__summary-title::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: #0f172a;
}
```

### Task 2: 验证

- [ ] **Step 1: 运行前端测试**
  - Run: `npm test`（cwd: `frontend`）
  - Expected: 全量通过
