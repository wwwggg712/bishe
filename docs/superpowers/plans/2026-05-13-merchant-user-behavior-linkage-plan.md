# Merchant User Behavior Linkage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a merchant-side “用户行为变化” card so recent customer behavior changes become visible as preference shifts and high-intent product signals on the merchant dashboard.

**Architecture:** Reuse the existing in-memory log pipeline and extend the analytics layer with one merchant-only aggregation endpoint. Keep the frontend change localized to `MerchantDashboard.vue` and the existing analytics API wrapper, so user-side actions can be reflected on the merchant page after a normal refresh.

**Tech Stack:** Flask, Flask-JWT-Extended, Vue 3, Vitest, Pytest

---

### Task 1: Add failing backend tests for merchant user behavior linkage

**Files:**
- Modify: `backend/tests/test_analytics.py`

- [ ] **Step 1: Write the failing merchant access test**

```python
def test_merchant_user_behavior_endpoint_requires_merchant_role(client, customer_headers, seeded_demo_data):
    response = client.get("/api/analytics/merchant/user-behavior", headers=customer_headers)

    assert response.status_code == 403
```

- [ ] **Step 2: Write the failing aggregation shape test**

```python
def test_merchant_user_behavior_endpoint_returns_preference_and_intent_sections(
    client, merchant_headers, seeded_demo_data
):
    from app.services.simulation_service import simulation_memory_store

    original_logs = list(simulation_memory_store.logs)
    simulation_memory_store.logs = [
        {
            "log_id": "b-1",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 1,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 299.0,
            "action_type": "favorite",
            "region": "华南",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "s-1",
            "stay_duration": 12,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:00:00",
        },
        {
            "log_id": "b-2",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 1,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 299.0,
            "action_type": "cart",
            "region": "华南",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "s-2",
            "stay_duration": 18,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:05:00",
        },
        {
            "log_id": "b-3",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 2,
            "product_name": "透气训练T恤",
            "category": "运动服饰",
            "brand": "CloudStep",
            "price": 129.0,
            "action_type": "purchase",
            "region": "华南",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "s-3",
            "stay_duration": 20,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:10:00",
        },
    ]

    try:
        response = client.get("/api/analytics/merchant/user-behavior", headers=merchant_headers)

        assert response.status_code == 200
        payload = response.get_json()
        assert "preference_changes" in payload
        assert "intent_products" in payload
        assert payload["preference_changes"]
        assert payload["intent_products"]
    finally:
        simulation_memory_store.logs = original_logs
```

- [ ] **Step 3: Run backend analytics tests to verify they fail**

Run: `python -m pytest tests/test_analytics.py -k "user_behavior_endpoint" -q`

Expected: FAIL because `/api/analytics/merchant/user-behavior` does not exist yet.

### Task 2: Implement backend aggregation for user behavior linkage

**Files:**
- Modify: `backend/app/services/analytics_service.py`
- Modify: `backend/app/routes/analytics.py`
- Test: `backend/tests/test_analytics.py`

- [ ] **Step 1: Add shared weights for high-intent merchant linkage**

```python
MERCHANT_BEHAVIOR_WEIGHTS = {
    "favorite": 3,
    "cart": 5,
    "purchase": 8,
}
```

- [ ] **Step 2: Add the analytics service method**

```python
def build_merchant_user_behavior(self, merchant_id, logs):
    category_stats = defaultdict(lambda: {"category": "", "scores": defaultdict(int)})
    product_stats = defaultdict(
        lambda: {"product_id": None, "product_name": "", "scores": defaultdict(int)}
    )

    for log in logs:
        if log["merchant_id"] != merchant_id:
            continue
        if log["action_type"] not in MERCHANT_BEHAVIOR_WEIGHTS:
            continue

        category_item = category_stats[log["category"]]
        category_item["category"] = log["category"]
        category_item["scores"][log["action_type"]] += 1

        product_item = product_stats[log["product_id"]]
        product_item["product_id"] = log["product_id"]
        product_item["product_name"] = log["product_name"]
        product_item["scores"][log["action_type"]] += 1
```

- [ ] **Step 3: Finish the service method by building `preference_changes` and `intent_products`**

```python
    preference_changes = []
    for item in category_stats.values():
        top_action, action_count = max(
            item["scores"].items(),
            key=lambda pair: (MERCHANT_BEHAVIOR_WEIGHTS.get(pair[0], 0), pair[1]),
        )
        preference_changes.append(
            {
                "category": item["category"],
                "top_action": top_action,
                "action_count": action_count,
                "summary": f"{item['category']}最近{top_action}行为更活跃",
            }
        )

    intent_products = []
    for item in product_stats.values():
        top_action, action_count = max(
            item["scores"].items(),
            key=lambda pair: (MERCHANT_BEHAVIOR_WEIGHTS.get(pair[0], 0), pair[1]),
        )
        intent_products.append(
            {
                "product_id": item["product_id"],
                "product_name": item["product_name"],
                "top_action": top_action,
                "action_count": action_count,
                "summary": f"{item['product_name']}最近{top_action}较多，值得重点关注",
            }
        )

    preference_changes.sort(
        key=lambda item: (MERCHANT_BEHAVIOR_WEIGHTS.get(item["top_action"], 0), item["action_count"]),
        reverse=True,
    )
    intent_products.sort(
        key=lambda item: (MERCHANT_BEHAVIOR_WEIGHTS.get(item["top_action"], 0), item["action_count"]),
        reverse=True,
    )
    return {
        "preference_changes": preference_changes[:5],
        "intent_products": intent_products[:5],
    }
```

- [ ] **Step 4: Add the merchant-only analytics route**

```python
@bp.get("/merchant/user-behavior")
@jwt_required()
def merchant_user_behavior():
    if get_jwt().get("role") != "merchant":
        return jsonify({"message": "仅商家可查看用户行为变化"}), 403

    merchant_id = int(get_jwt_identity())
    payload = analytics_service.build_merchant_user_behavior(merchant_id, simulation_memory_store.logs)
    return jsonify(payload)
```

- [ ] **Step 5: Run backend analytics tests and verify they pass**

Run: `python -m pytest tests/test_analytics.py -k "user_behavior_endpoint" -q`

Expected: PASS

### Task 3: Add failing frontend tests for the merchant linkage card

**Files:**
- Modify: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Extend the analytics mock with the new API**

```javascript
vi.mock('../api/analytics.js', () => ({
  fetchOverview: vi.fn(),
  fetchFunnel: vi.fn(),
  fetchRegions: vi.fn(),
  fetchCategories: vi.fn(),
  fetchHotProducts: vi.fn(),
  fetchColdProducts: vi.fn(),
  fetchUserRfm: vi.fn(),
  fetchMerchantUserBehavior: vi.fn(),
  fetchMerchantActionSummary: vi.fn(),
  fetchMerchantAiAnalysis: vi.fn(),
  recordMerchantAction: vi.fn(),
  fetchMerchantStrategy: vi.fn(),
  fetchPredictionAnomalies: vi.fn(),
  fetchMerchantBrief: vi.fn()
}))
```

- [ ] **Step 2: Add a failing merchant card rendering test**

```javascript
it('renders merchant user behavior linkage sections', async () => {
  fetchMerchantUserBehavior.mockResolvedValue({
    preference_changes: [
      {
        category: '运动鞋',
        top_action: 'cart',
        action_count: 2,
        summary: '运动鞋最近加购行为更活跃'
      }
    ],
    intent_products: [
      {
        product_id: 1,
        product_name: '轻量跑鞋',
        top_action: 'purchase',
        action_count: 1,
        summary: '轻量跑鞋最近购买较多，值得重点关注'
      }
    ]
  })

  const wrapper = mount(MerchantDashboard, {
    global: {
      stubs: {
        RouterLink: true
      }
    }
  })

  await flushPromises()

  expect(wrapper.text()).toContain('用户行为变化')
  expect(wrapper.text()).toContain('最近用户偏好变化')
  expect(wrapper.text()).toContain('最近高意向商品变化')
  expect(wrapper.text()).toContain('运动鞋')
  expect(wrapper.text()).toContain('轻量跑鞋')
})
```

- [ ] **Step 3: Run the focused merchant dashboard tests and verify they fail**

Run: `npm run test -- src/tests/merchant-dashboard.test.js`

Expected: FAIL because the analytics API wrapper and merchant card do not exist yet.

### Task 4: Implement the merchant linkage card

**Files:**
- Modify: `frontend/src/api/analytics.js`
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
- Modify: `frontend/src/styles/theme.css`
- Test: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Add the analytics API wrapper**

```javascript
export async function fetchMerchantUserBehavior() {
  const response = await http.get('/api/analytics/merchant/user-behavior')
  return response.data
}
```

- [ ] **Step 2: Add local state in the merchant dashboard**

```javascript
const merchantUserBehavior = ref({
  preference_changes: [],
  intent_products: []
})
```

- [ ] **Step 3: Load the new payload together with the existing dashboard requests**

```javascript
const [
  overviewPayload,
  funnelPayload,
  regionPayload,
  categoryPayload,
  hotProductPayload,
  coldProductPayload,
  userRfmPayload,
  strategyPayload,
  anomalyPayload,
  merchantActionPayload,
  merchantUserBehaviorPayload
] = await Promise.all([
  fetchOverview(),
  fetchFunnel(),
  fetchRegions(),
  fetchCategories(),
  fetchHotProducts(),
  fetchColdProducts(),
  fetchUserRfm(),
  fetchMerchantStrategy(),
  fetchPredictionAnomalies({ severity: 'high' }),
  fetchMerchantActionSummary(),
  fetchMerchantUserBehavior()
])

merchantUserBehavior.value = {
  preference_changes: merchantUserBehaviorPayload.preference_changes || [],
  intent_products: merchantUserBehaviorPayload.intent_products || []
}
```

- [ ] **Step 4: Render the new merchant card**

```vue
<article class="dashboard-panel">
  <div class="dashboard-panel__header">
    <div>
      <p class="section-kicker">USER BEHAVIOR LINKAGE</p>
      <h3>用户行为变化</h3>
      <p>把最近用户侧的高意向行为变化，直接映射成商家可理解的经营信号。</p>
    </div>
  </div>

  <div class="merchant-linkage-grid">
    <section class="merchant-linkage-section">
      <h4>最近用户偏好变化</h4>
    </section>
    <section class="merchant-linkage-section">
      <h4>最近高意向商品变化</h4>
    </section>
  </div>
</article>
```

- [ ] **Step 5: Fill the two sections with list content and empty states**

```vue
<ul v-if="merchantUserBehavior.preference_changes.length" class="strategy-list">
  <li
    v-for="item in merchantUserBehavior.preference_changes"
    :key="`${item.category}-${item.top_action}`"
    class="strategy-list__item"
  >
    <div class="strategy-list__meta">
      <strong>{{ item.category }}</strong>
      <span>{{ item.top_action }} {{ item.action_count }} 次</span>
    </div>
    <p>{{ item.summary }}</p>
  </li>
</ul>
<p v-else class="empty-state">当前暂无明显用户偏好变化。</p>
```

```vue
<ul v-if="merchantUserBehavior.intent_products.length" class="strategy-list">
  <li
    v-for="item in merchantUserBehavior.intent_products"
    :key="`${item.product_id}-${item.top_action}`"
    class="strategy-list__item"
  >
    <div class="strategy-list__meta">
      <strong>{{ item.product_name }}</strong>
      <span>{{ item.top_action }} {{ item.action_count }} 次</span>
    </div>
    <p>{{ item.summary }}</p>
  </li>
</ul>
<p v-else class="empty-state">当前暂无明显高意向商品变化。</p>
```

- [ ] **Step 6: Add minimal styles for the linkage card**

```css
.merchant-linkage-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.merchant-linkage-section {
  display: grid;
  gap: 12px;
}
```

- [ ] **Step 7: Run the focused merchant dashboard tests and verify they pass**

Run: `npm run test -- src/tests/merchant-dashboard.test.js`

Expected: PASS

### Task 5: Run regression verification

**Files:**
- Test: `backend/tests/test_analytics.py`
- Test: `frontend/src/tests/merchant-dashboard.test.js`
- Test: `backend/tests`
- Test: `frontend/src/tests`

- [ ] **Step 1: Run focused backend analytics tests**

Run: `python -m pytest tests/test_analytics.py -q`

Expected: PASS

- [ ] **Step 2: Run focused merchant frontend tests**

Run: `npm run test -- src/tests/merchant-dashboard.test.js`

Expected: PASS

- [ ] **Step 3: Run backend full suite**

Run: `python -m pytest -q`

Expected: PASS

- [ ] **Step 4: Run frontend full suite**

Run: `npm run test`

Expected: PASS
