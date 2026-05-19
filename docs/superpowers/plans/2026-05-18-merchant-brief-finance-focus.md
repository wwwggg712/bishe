# 今日经营简报侧栏：经营盈亏（收入/成本/利润）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将商家端“今日经营简报”右侧信息块从“重点商品”改为“经营盈亏”，展示近{days}天收入/成本/利润（利润<0 显示亏损），并在底部保留重点商品名称提示。

**Architecture:** 复用 `MerchantDashboard` 已加载的 `opsOverview.summary` 数据（来自 `fetchMerchantOpsOverview(days=30)`），仅做 UI 组合与样式微调；通过少量 CSS 控制标题选择器与指标行排版。

**Tech Stack:** Vue 3 + Vite + Vitest + CSS（全局样式 `frontend/src/styles/theme.css`）

---

### Task 1: 组件改造（经营盈亏展示）

**Files:**
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`（overview 区域 `.merchant-brief__focus`）

- [ ] **Step 1: 增加金额格式化与利润标签计算**

在 `<script setup>` 中新增：

```js
function formatMoney(value) {
  const numberValue = Number(value || 0)
  return numberValue.toFixed(2)
}

const financeDays = computed(() => opsOverview.value?.summary?.days || 30)
const profitValue = computed(() => Number(opsOverview.value?.summary?.profit || 0))
const profitLabel = computed(() => (profitValue.value < 0 ? `近${financeDays.value}天亏损` : `近${financeDays.value}天利润`))
```

- [ ] **Step 2: 替换 `.merchant-brief__focus` 模板内容**

将：

```vue
<div class="merchant-brief__focus">
  <span>重点商品</span>
  <strong>{{ topProduct?.product_name || '待生成' }}</strong>
  <small>当前最高热度商品，适合作为今日运营重点</small>
</div>
```

替换为：

```vue
<div class="merchant-brief__focus">
  <span>经营盈亏</span>
  <div class="merchant-brief__finance">
    <div class="merchant-brief__finance-row">
      <span class="merchant-brief__finance-label">近{{ financeDays }}天收入</span>
      <strong class="merchant-brief__finance-value">{{ formatMoney(opsOverview?.summary?.revenue) }}</strong>
    </div>
    <div class="merchant-brief__finance-row">
      <span class="merchant-brief__finance-label">近{{ financeDays }}天成本</span>
      <strong class="merchant-brief__finance-value">{{ formatMoney(opsOverview?.summary?.cost) }}</strong>
    </div>
    <div class="merchant-brief__finance-row" :data-negative="profitValue < 0 ? 'true' : 'false'">
      <span class="merchant-brief__finance-label">{{ profitLabel }}</span>
      <strong class="merchant-brief__finance-value">{{ formatMoney(opsOverview?.summary?.profit) }}</strong>
    </div>
  </div>
  <small>
    口径：购买次数×售价/成本价 · 重点商品：{{ topProduct?.product_name || '待生成' }}
  </small>
</div>
```

### Task 2: 样式微调（标题选择器 + 指标行排版）

**Files:**
- Modify: `frontend/src/styles/theme.css`（`.merchant-brief__focus` 及新增子元素样式）

- [ ] **Step 1: 限定标题样式只作用于直系 span**

将：

```css
.merchant-brief__focus span { ... }
```

改为：

```css
.merchant-brief__focus > span { ... }
```

- [ ] **Step 2: 新增指标行样式**

追加：

```css
.merchant-brief__finance {
  display: grid;
  gap: 10px;
}

.merchant-brief__finance-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.merchant-brief__finance-label {
  font-size: 0.9rem;
  color: #475569;
}

.merchant-brief__finance-value {
  font-size: 1.15rem;
  font-weight: 900;
  color: #0f172a;
}

.merchant-brief__finance-row[data-negative='true'] .merchant-brief__finance-value {
  color: #b91c1c;
}
```

### Task 3: 验证

**Files:**
- Modify (if needed): `frontend/src/tests/merchant-dashboard.test.js`（仅当断言涉及“重点商品”文案）

- [ ] **Step 1: 运行前端测试**
  - Run: `npm test`
  - Expected: 42/42 通过
