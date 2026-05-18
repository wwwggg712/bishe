# Merchant Dashboard Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize the merchant dashboard into a cleaner “经营驾驶舱” so the page keeps all core features while improving visual hierarchy, grouping, and scanability.

**Architecture:** This is a frontend-only restructuring of the existing merchant homepage. Keep all current capabilities and data sources, but reorder panels into four visual layers, standardize the 2-column card rhythm for the middle sections, shorten descriptive copy, and update tests so the new grouping remains stable.

**Tech Stack:** Vue 3, Vitest, CSS

---

### Task 1: Add failing merchant dashboard tests for the new section hierarchy

**Files:**
- Modify: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Add a failing test that asserts the new top-level structure is present**

```javascript
it('renders the cleaned merchant cockpit hierarchy', async () => {
  const wrapper = mount(MerchantDashboard, {
    global: {
      stubs: {
        RouterLink: true
      }
    }
  })

  await flushPromises()

  const text = wrapper.text()
  expect(text).toContain('经营总览')
  expect(text).toContain('今日经营简报')
  expect(text).toContain('用户行为变化')
  expect(text).toContain('今日已执行运营动作')
  expect(text).toContain('热销机会')
  expect(text).toContain('滞销风险')
  expect(text).toContain('AI 经营分析')
  expect(text).toContain('异常预警')
  expect(text).toContain('类目热点')
  expect(text).toContain('用户价值分层')
  expect(text).toContain('转化漏斗')
  expect(text).toContain('冷门商品')
})
```

- [ ] **Step 2: Add a failing test for the new section labels and compressed copy**

```javascript
it('renders grouped section labels for business, analysis, and detail layers', async () => {
  const wrapper = mount(MerchantDashboard, {
    global: {
      stubs: {
        RouterLink: true
      }
    }
  })

  await flushPromises()

  expect(wrapper.text()).toContain('核心业务')
  expect(wrapper.text()).toContain('辅助分析')
  expect(wrapper.text()).toContain('详细分析')
  expect(wrapper.text()).toContain('把最近24小时高意向行为变化')
})
```

- [ ] **Step 3: Run the focused merchant dashboard tests to verify they fail**

Run: `npm run test -- src/tests/merchant-dashboard.test.js`

Expected: FAIL because the current merchant page does not yet render the new group headers or cleaned hierarchy labels.

### Task 2: Rebuild the merchant dashboard template into four visual layers

**Files:**
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
- Test: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Add section helper arrays for grouped rendering**

```javascript
const secondaryAnalysisItems = computed(() => [
  {
    key: 'ai-analysis',
    title: 'AI 经营分析'
  },
  {
    key: 'anomalies',
    title: '异常预警'
  },
  {
    key: 'categories',
    title: '类目热点'
  },
  {
    key: 'user-rfm',
    title: '用户价值分层'
  }
])
```

This step is only a small setup step; keep the actual rendering explicit in the template rather than abstracting the whole page.

- [ ] **Step 2: Insert grouped section headers into the template**

```vue
<section class="merchant-dashboard__layer">
  <div class="merchant-dashboard__layer-head">
    <h3>核心业务</h3>
    <p>优先展示经营联动、动作闭环、机会和风险。</p>
  </div>
  <!-- 2列核心业务卡片 -->
</section>
```

```vue
<section class="merchant-dashboard__layer">
  <div class="merchant-dashboard__layer-head">
    <h3>辅助分析</h3>
    <p>补充解释经营判断，保留分析深度但降低视觉权重。</p>
  </div>
  <!-- 2列辅助分析卡片 -->
</section>
```

```vue
<section class="merchant-dashboard__layer">
  <div class="merchant-dashboard__layer-head">
    <h3>详细分析</h3>
    <p>用于答辩追问时补充说明证据，不再占据首页第一优先级。</p>
  </div>
  <!-- 详细分析卡片 -->
</section>
```

- [ ] **Step 3: Move the four highest-value cards into the “核心业务” grid**

The `核心业务` grid must contain these four cards, in this order:

```vue
<!-- 用户行为变化 -->
<!-- 今日已执行运营动作 -->
<!-- 热销机会 -->
<!-- 滞销风险 -->
```

Keep the existing card bodies and buttons, but place them under the new grouped section so the page reads like:

```vue
<section class="merchant-dashboard__layer">
  <div class="merchant-dashboard__layer-head">
    <h3>核心业务</h3>
    <p>优先展示经营联动、动作闭环、机会和风险。</p>
  </div>
  <div class="merchant-dashboard__layer-grid">
    <!-- 用户行为变化 -->
    <!-- 今日已执行运营动作 -->
    <!-- 热销机会 -->
    <!-- 滞销风险 -->
  </div>
</section>
```

- [ ] **Step 4: Move AI, anomalies, categories, and RFM into the “辅助分析” grid**

Keep the current existing content but reorder it into:

```vue
<div class="merchant-dashboard__layer-grid merchant-dashboard__layer-grid--secondary">
  <!-- AI 经营分析 -->
  <!-- 异常预警 -->
  <!-- 类目热点 -->
  <!-- 用户价值分层 -->
</div>
```

- [ ] **Step 5: Move funnel and cold-product details into the “详细分析” layer**

```vue
<div class="merchant-dashboard__layer-grid merchant-dashboard__layer-grid--detail">
  <!-- 转化漏斗 -->
  <!-- 冷门商品 -->
</div>
```

If there is no standalone region panel yet, do not invent one. Keep this task limited to the panels that already exist in the current page.

- [ ] **Step 6: Run the focused merchant dashboard tests and verify they still fail only on styling/copy gaps**

Run: `npm run test -- src/tests/merchant-dashboard.test.js`

Expected: FAIL or partially fail because the new layout classes and shortened copy are not fully aligned yet.

### Task 3: Standardize copy and reduce visual noise

**Files:**
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
- Test: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Shorten card descriptions to one sentence each**

Update the card header descriptions so they stay within one short sentence, for example:

```vue
<p>把最近24小时高意向行为变化映射成商家可理解的经营信号。</p>
```

```vue
<p>把分析结果转成可见动作，直接展示今天执行了哪些运营决策。</p>
```

```vue
<p>优先关注热度高、可继续放大的商品。</p>
```

```vue
<p>优先处理高浏览低转化商品，降低流量浪费。</p>
```

- [ ] **Step 2: Reduce repeated explanatory text in lower-priority cards**

For `AI 经营分析` / `异常预警` / `类目热点` / `用户价值分层` / `转化漏斗` / `冷门商品`, trim the descriptions to compact one-line text. Keep the meaning, but avoid long multi-clause explanations.

- [ ] **Step 3: Run the focused merchant dashboard tests and verify copy-related assertions pass**

Run: `npm run test -- src/tests/merchant-dashboard.test.js`

Expected: PASS for the new group labels and compact copy assertions.

### Task 4: Add layout classes and consistent grid styling

**Files:**
- Modify: `frontend/src/styles/theme.css`
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
- Test: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Add layer container styles**

```css
.merchant-dashboard__layer {
  display: grid;
  gap: 16px;
}

.merchant-dashboard__layer-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
}

.merchant-dashboard__layer-head h3 {
  margin: 0;
  font-size: 1.2rem;
}

.merchant-dashboard__layer-head p {
  margin: 0;
  color: #64748b;
}
```

- [ ] **Step 2: Add unified 2-column grid styles for the middle layers**

```css
.merchant-dashboard__layer-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}
```

```css
.merchant-dashboard__layer-grid--detail {
  align-items: start;
}
```

- [ ] **Step 3: Reduce over-expansion from old full-width panels where needed**

If a panel currently spans the entire row only because of old layout assumptions, remove the full-width class unless it is still needed for the new grouped design. Keep the top hero summary full-width; keep the rest inside the new grid rhythm.

- [ ] **Step 4: Ensure mobile layout still collapses cleanly**

Update the existing responsive block so the new classes also switch to one column:

```css
.merchant-dashboard__layer-grid,
.merchant-dashboard__layer-head {
  grid-template-columns: 1fr;
}
```

Only apply the correct property to each selector in the real CSS; this snippet is a reminder that both need responsive treatment.

- [ ] **Step 5: Run the focused merchant dashboard tests to verify the page still renders**

Run: `npm run test -- src/tests/merchant-dashboard.test.js`

Expected: PASS

### Task 5: Run regression verification

**Files:**
- Test: `frontend/src/tests/merchant-dashboard.test.js`
- Test: `frontend/src/tests`

- [ ] **Step 1: Run focused merchant dashboard tests**

Run: `npm run test -- src/tests/merchant-dashboard.test.js`

Expected: PASS

- [ ] **Step 2: Run frontend full suite**

Run: `npm run test`

Expected: PASS
