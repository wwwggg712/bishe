# Customer Activity Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dual activity panel on the customer home page so the UI shows both the actions performed in the current session and the latest personal behavior records used by the portrait system.

**Architecture:** Keep the backend unchanged and build the feature entirely on the frontend. Reuse `profile.recent_activity` for the historical panel, and maintain a small in-memory `sessionActions` list in `CustomerHome.vue` so freshly clicked actions appear immediately without adding a new API.

**Tech Stack:** Vue 3, Vitest

---

### Task 1: Add failing frontend tests for the dual activity panel

**Files:**
- Modify: `frontend/src/tests/customer-home.test.js`

- [ ] **Step 1: Add a failing test for rendering both activity panels**

```javascript
it('renders session activity panel and recent personal activity panel', async () => {
  fetchPreferenceProfile.mockResolvedValue({
    user: { nickname: '小林', region: '华东' },
    is_cold_start: false,
    top_categories: [{ category: '运动服饰', count: 2, score: 6 }],
    top_actions: [{ action_type: 'favorite', count: 1, score: 3 }],
    recent_activity: [
      {
        log_id: 'r-1',
        product_id: 2,
        product_name: '透气训练T恤',
        category: '运动服饰',
        action_type: 'favorite',
        timestamp: '2026-05-13T10:20:00'
      }
    ],
    engagement_score: 3,
    top_active_hours: [{ hour: 20, count: 1 }],
    price_preference: { average_price: 129, price_band: '大众消费偏好' },
    profile_tags: ['运动服饰偏好']
  })

  const wrapper = mount(CustomerHome)
  await flushPromises()

  expect(wrapper.text()).toContain('本次会话刚刚操作')
  expect(wrapper.text()).toContain('最近 5 条个人行为')
  expect(wrapper.text()).toContain('透气训练T恤')
  expect(wrapper.text()).toContain('favorite')
})
```

- [ ] **Step 2: Add a failing test for current-session actions appearing immediately**

```javascript
it('shows freshly recorded actions in the session activity panel', async () => {
  fetchMyRecommendations
    .mockResolvedValueOnce({
      mode: 'fallback',
      items: [
        {
          product_id: 1,
          product_name: '轻量跑鞋',
          category: '运动鞋',
          reason: '该商品近期热度较高，适合作为当前阶段的冷启动推荐'
        }
      ]
    })
    .mockResolvedValueOnce({
      mode: 'personalized',
      items: [
        {
          product_id: 2,
          product_name: '透气训练T恤',
          category: '运动服饰',
          reason: '该商品属于你偏好的 运动服饰 类目，且近期热度表现较好'
        }
      ]
    })

  fetchPreferenceProfile
    .mockResolvedValueOnce({
      user: { nickname: '小林', region: '华东' },
      is_cold_start: true,
      top_categories: [],
      top_actions: [],
      recent_activity: [],
      engagement_score: 0,
      top_active_hours: [],
      price_preference: { average_price: 0, price_band: '暂无数据' },
      profile_tags: []
    })
    .mockResolvedValueOnce({
      user: { nickname: '小林', region: '华东' },
      is_cold_start: false,
      top_categories: [{ category: '运动鞋', count: 1, score: 3 }],
      top_actions: [{ action_type: 'favorite', count: 1, score: 3 }],
      recent_activity: [
        {
          log_id: 'r-2',
          product_id: 1,
          product_name: '轻量跑鞋',
          category: '运动鞋',
          action_type: 'favorite',
          timestamp: '2026-05-13T10:30:00'
        }
      ],
      engagement_score: 3,
      top_active_hours: [{ hour: 20, count: 1 }],
      price_preference: { average_price: 299, price_band: '中高消费偏好' },
      profile_tags: ['运动鞋偏好']
    })

  const wrapper = mount(CustomerHome)
  await flushPromises()

  expect(wrapper.text()).toContain('你还没有进行操作')

  await wrapper.find('button[data-testid="customer-action-favorite-1"]').trigger('click')
  await flushPromises()

  expect(wrapper.text()).toContain('轻量跑鞋')
  expect(wrapper.text()).toContain('刚刚')
  expect(wrapper.text()).toContain('收藏')
  expect(wrapper.text()).toContain('最近 5 条个人行为')
})
```

- [ ] **Step 3: Run the focused customer page tests and verify they fail**

Run: `npm run test -- src/tests/customer-home.test.js`

Expected: FAIL because the customer page does not yet render `本次会话刚刚操作` or `最近 5 条个人行为`.

### Task 2: Implement session activity state and helper formatting

**Files:**
- Modify: `frontend/src/views/customer/CustomerHome.vue`
- Test: `frontend/src/tests/customer-home.test.js`

- [ ] **Step 1: Add local session activity state**

```javascript
const sessionActions = ref([])
```

- [ ] **Step 2: Add helper labels for action names**

```javascript
const ACTION_LABELS = {
  view: '浏览',
  favorite: '收藏',
  cart: '加购',
  purchase: '购买'
}
```

- [ ] **Step 3: Add a helper that inserts one fresh session action at the top**

```javascript
function pushSessionAction(product, actionType) {
  sessionActions.value = [
    {
      product_id: product.product_id,
      product_name: product.product_name,
      action_type: actionType,
      action_label: ACTION_LABELS[actionType] || actionType,
      time_label: '刚刚'
    },
    ...sessionActions.value.filter(
      (item) => !(item.product_id === product.product_id && item.action_type === actionType)
    )
  ].slice(0, 5)
}
```

- [ ] **Step 4: Call the helper after a successful customer action**

```javascript
async function handleCustomerAction(productId, actionType) {
  actionInFlightKey.value = buildActionKey(productId, actionType)
  actionMessage.value = ''
  errorMessage.value = ''

  try {
    await recordCustomerAction({
      product_id: productId,
      action_type: actionType
    })
    const product = recommendations.value.find((item) => item.product_id === productId)
    if (product) {
      pushSessionAction(product, actionType)
    }
    actionMessage.value = `已记录${ACTION_LABELS[actionType]}行为`
    await loadCustomerHome()
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '用户行为记录失败，请稍后重试。'
  } finally {
    actionInFlightKey.value = ''
  }
}
```

- [ ] **Step 5: Run the focused tests and verify the new state helpers are not enough yet**

Run: `npm run test -- src/tests/customer-home.test.js`

Expected: FAIL because the panels are still not rendered in the template.

### Task 3: Render the dual activity panels in the customer page

**Files:**
- Modify: `frontend/src/views/customer/CustomerHome.vue`
- Modify: `frontend/src/styles/theme.css`
- Test: `frontend/src/tests/customer-home.test.js`

- [ ] **Step 1: Add a small formatter for recent activity rows**

```javascript
function formatRecentActivityTime(timestamp) {
  if (!timestamp) {
    return '未知时间'
  }
  return timestamp.replace('T', ' ').slice(0, 16)
}
```

- [ ] **Step 2: Render the session activity panel near the recommendation card**

```vue
<article class="dashboard-panel">
  <div class="dashboard-panel__header">
    <div>
      <h3>本次会话刚刚操作</h3>
      <p>用于展示你在本轮演示里刚刚触发的用户行为。</p>
    </div>
    <span class="dashboard-panel__badge">{{ sessionActions.length }} 条</span>
  </div>

  <ul v-if="sessionActions.length" class="recommend-list">
    <li v-for="item in sessionActions" :key="`${item.product_id}-${item.action_type}`" class="recommend-list__item">
      <strong>{{ item.product_name }}</strong>
      <span>{{ item.action_label }}</span>
      <p>{{ item.time_label }}</p>
    </li>
  </ul>
  <p v-else class="empty-state">你还没有进行操作，可先点击浏览、收藏、加购或购买。</p>
</article>
```

- [ ] **Step 3: Render the recent personal activity panel near the portrait card**

```vue
<article class="dashboard-panel">
  <div class="dashboard-panel__header">
    <div>
      <h3>最近 5 条个人行为</h3>
      <p>用于展示系统最近依据了哪些个人行为来生成画像。</p>
    </div>
    <span class="dashboard-panel__badge">{{ profile.recent_activity?.length || 0 }} 条</span>
  </div>

  <ul v-if="profile.recent_activity?.length" class="recommend-list">
    <li
      v-for="item in profile.recent_activity"
      :key="item.log_id"
      class="recommend-list__item"
    >
      <strong>{{ item.product_name }}</strong>
      <span>{{ ACTION_LABELS[item.action_type] || item.action_type }}</span>
      <p>{{ formatRecentActivityTime(item.timestamp) }}</p>
    </li>
  </ul>
  <p v-else class="empty-state">当前暂无历史个人行为记录。</p>
</article>
```

- [ ] **Step 4: Add minimal layout styles for the new panels**

```css
.customer-activity-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}
```

```css
.customer-action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
```

- [ ] **Step 5: Place the two new panels in a dedicated section**

```vue
<section class="customer-activity-grid">
  <!-- 本次会话刚刚操作 -->
  <!-- 最近 5 条个人行为 -->
</section>
```

- [ ] **Step 6: Run the focused customer page tests and verify they pass**

Run: `npm run test -- src/tests/customer-home.test.js`

Expected: PASS

### Task 4: Run regression verification

**Files:**
- Test: `frontend/src/tests/customer-home.test.js`
- Test: `frontend/src/tests`

- [ ] **Step 1: Run focused customer tests**

Run: `npm run test -- src/tests/customer-home.test.js`

Expected: PASS

- [ ] **Step 2: Run frontend full suite**

Run: `npm run test`

Expected: PASS
