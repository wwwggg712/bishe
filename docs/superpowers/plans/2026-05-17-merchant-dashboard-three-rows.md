# Merchant Dashboard Three-Rows Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将商家端“经营总览 / 核心业务 / 辅助分析 / 详细分析”等模块从多列并排改为三行（单列堆叠），每行只展示一块内容，消除大块留白；AI 经营分析保持独占大块展示，不做折叠。

**Architecture:** 统一收敛到 CSS 层面的布局规则，避免在多个 Vue 组件中重复改结构；通过修改网格容器（summary、layer-grid、brief-matrix）为单列，实现“每行一块”。

**Tech Stack:** Vue 3, Vite, Vitest, 全局样式 `theme.css`

---

### Task 1: 将商家端网格布局改为单列堆叠

**Files:**
- Modify: [theme.css](file:///d:/MyProjects/bishe-finnal/frontend/src/styles/theme.css)

- [ ] **Step 1: 修改商家端 summary/layer-grid/brief-matrix 为单列**

目标改动点：
- `.merchant-dashboard__summary`：从 `repeat(4, ...)` 改为 `1fr`
- `.merchant-dashboard__layer-grid`：从 `repeat(auto-fit, ...)` 改为 `1fr`
- `.merchant-brief__matrix`：从 `repeat(3, ...)` 改为 `1fr`

- [ ] **Step 2: 本地跑前端测试确保无回归**

Run (PowerShell):
```bash
cd d:\MyProjects\bishe-finnal\frontend
npm test
```

Expected:
- Vitest 全量通过

- [ ] **Step 3: 手工验收页面（本地预览）**

重点检查：
- “辅助分析”中 `AI 经营分析 / 异常预警 / 类目热点 / 简化用户分层` 由并排多列变为纵向 4 行
- “详细分析”中 `热销商品 / 转化漏斗 / 冷门商品 / 策略建议` 由并排多列变为纵向多行
- “经营总览”中 `库存清单 / 建议下架 / 销量冠军品牌TOP / 已下架商品` 由并排多列变为纵向多行

