# 经营盈亏并入经营总览小卡片 + 简报标题框化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将“经营盈亏（收入/成本/利润-亏损）”移动到经营总览小卡片首行展示；将“今日经营简报”改为单列并把标题框起来；全链路强制去除 `P0/P1` 等优先级字母。

**Architecture:** 前端在 `MerchantDashboard` 生成盈亏卡片并在总览卡片区三列展示；`MerchantOpsOverview` 增加开关以避免重复显示；简报改为单列结构并强化标题样式；前后端同时禁止/清洗 `P0/P1`。

**Tech Stack:** Vue 3 + Vite + Vitest + Flask + pytest

---

### Task 1: 经营盈亏加入总览小卡片并避免重复

**Files:**
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
- Modify: `frontend/src/views/merchant/MerchantOpsOverview.vue`
- Test: `frontend/src/tests/merchant-dashboard.test.js`（如断言受影响）

- [ ] **Step 1: 在 `MerchantOpsOverview` 新增开关 prop**

新增 props：

```js
showSummaryCards: {
  type: Boolean,
  default: true
}
```

并用 `v-if="showSummaryCards"` 包裹原来的盈亏卡片 section。

- [ ] **Step 2: 在 `MerchantDashboard` 的 overviewCards 前追加盈亏三卡**

使用 `opsOverview.summary.days/revenue/cost/profit` 生成：
- 近{days}天收入
- 近{days}天成本
- 近{days}天利润/亏损（profit<0 改为“亏损”）

并让总览卡片区使用 `merchant-dashboard__summary--triple`。

- [ ] **Step 3: 在 `MerchantDashboard` 调用 `MerchantOpsOverview` 时传入 `:show-summary-cards="false"`**

### Task 2: 今日经营简报单列 + 标题框化

**Files:**
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
- Modify: `frontend/src/styles/theme.css`

- [ ] **Step 1: 移除简报卡片右侧区域**
将 `.merchant-brief__hero-card` 改为单列结构，仅保留简报标题与分点内容。

- [ ] **Step 2: 给“今日经营简报”标题增加框化样式**
为标题增加专属 class，并在 `theme.css` 中设置 padding/border/background，使标题有明显“框/胶囊”视觉锚点。

### Task 3: 强制去除 P0/P1（后端禁止 + 前端清洗兜底）

**Files:**
- Modify: `backend/app/services/llm_service.py`
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
- Test: `backend/tests/test_llm_report.py`（如触发断言变化）

- [ ] **Step 1: 后端 system prompt 明确禁止 P0/P1/P2**
行动清单要求只允许 `1）2）3）`。

- [ ] **Step 2: 前端解析层扩展清洗规则**
确保能剥离：
- `P0-`、`P1-3）`、`P2)` 等变体

### Task 4: 验证

**Files:**
- No new files

- [ ] **Step 1: 前端测试**
Run: `npm test`（cwd: `frontend`）
Expected: 42/42 通过

- [ ] **Step 2: 后端测试**
Run: `python -m pytest -q`（cwd: `backend`）
Expected: 全量通过
