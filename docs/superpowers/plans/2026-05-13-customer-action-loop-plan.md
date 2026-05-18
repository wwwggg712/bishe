# Customer Action Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add customer-side action logging so clicking browse, favorite, cart, and purchase on recommendation cards immediately updates portrait and recommendation results.

**Architecture:** Reuse the existing in-memory simulation log store instead of creating new persistence. Add one customer-only action endpoint under the recommendation blueprint, reuse the existing recommendation/portrait refresh requests on the frontend, and keep all behavior changes inside the current customer home page.

**Tech Stack:** Flask, Flask-JWT-Extended, Vue 3, Vitest, Pytest

---

### Task 1: Add failing backend tests for customer action logging

**Files:**
- Modify: `backend/tests/test_intelligence.py`

- [ ] **Step 1: Write the failing customer action success test**

```python
def test_customer_can_record_recommendation_action(client, customer_headers, seeded_demo_data):
    from app.services.simulation_service import simulation_memory_store

    original_logs = list(simulation_memory_store.logs)
    simulation_memory_store.logs = []

    try:
        response = client.post(
            "/api/recommendations/actions",
            headers=customer_headers,
            json={"product_id": 1, "action_type": "favorite"},
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["message"] == "用户行为记录成功"
        assert payload["log"]["product_id"] == 1
        assert payload["log"]["action_type"] == "favorite"
        assert len(simulation_memory_store.logs) == 1
    finally:
        simulation_memory_store.logs = original_logs
```

- [ ] **Step 2: Write the failing non-customer forbidden test**

```python
def test_non_customer_cannot_record_recommendation_action(client, merchant_headers, seeded_demo_data):
    response = client.post(
        "/api/recommendations/actions",
        headers=merchant_headers,
        json={"product_id": 1, "action_type": "view"},
    )

    assert response.status_code == 403
```

- [ ] **Step 3: Write the failing cold-start transition test**

```python
def test_customer_action_turns_cold_start_portrait_into_active_portrait(client, customer_headers, seeded_demo_data):
    from app.services.simulation_service import simulation_memory_store

    original_logs = list(simulation_memory_store.logs)
    simulation_memory_store.logs = []

    try:
        before_response = client.get("/api/users/portrait", headers=customer_headers)
        assert before_response.status_code == 200
        assert before_response.get_json()["is_cold_start"] is True

        action_response = client.post(
            "/api/recommendations/actions",
            headers=customer_headers,
            json={"product_id": 1, "action_type": "purchase"},
        )
        assert action_response.status_code == 200

        after_response = client.get("/api/users/portrait", headers=customer_headers)
        assert after_response.status_code == 200
        payload = after_response.get_json()
        assert payload["is_cold_start"] is False
        assert payload["engagement_score"] > 0
    finally:
        simulation_memory_store.logs = original_logs
```

- [ ] **Step 4: Run backend tests to verify they fail**

Run: `python -m pytest tests/test_intelligence.py -k "recommendation_action or cold_start_portrait_into_active_portrait" -q`

Expected: FAIL because `/api/recommendations/actions` does not exist yet.

### Task 2: Implement backend customer action logging

**Files:**
- Modify: `backend/app/services/simulation_service.py`
- Modify: `backend/app/routes/recommendation.py`
- Test: `backend/tests/test_intelligence.py`

- [ ] **Step 1: Add a service helper that records one customer action log**

```python
def record_customer_action(self, user, product, action_type):
    log = {
        "log_id": str(uuid4()),
        "user_id": user.id,
        "merchant_id": product.merchant_id,
        "product_id": product.id,
        "product_name": product.name,
        "category": product.category,
        "brand": product.brand,
        "price": float(product.price),
        "action_type": action_type,
        "region": user.region,
        "device_type": random.choice(DEVICE_TYPES),
        "source_channel": "customer_page",
        "session_id": str(uuid4()),
        "stay_duration": random.randint(5, 180),
        "is_new_user": user.created_at >= datetime.utcnow() - timedelta(days=30),
        "timestamp": datetime.utcnow().isoformat(),
    }
    simulation_memory_store.save([log])
    return log
```

- [ ] **Step 2: Add the recommendation action endpoint with customer-only permission**

```python
@bp.post("/actions")
@jwt_required()
def record_action():
    if get_jwt().get("role") != "customer":
        return jsonify({"message": "仅普通用户可记录推荐行为"}), 403

    payload = request.get_json(silent=True) or {}
    product_id = payload.get("product_id")
    action_type = (payload.get("action_type") or "").strip().lower()

    if not product_id or action_type not in {"view", "favorite", "cart", "purchase"}:
        return jsonify({"message": "product_id 或 action_type 非法"}), 400
```

- [ ] **Step 3: Complete the endpoint by finding the user and product, then writing the log**

```python
    user = User.query.get(int(get_jwt_identity()))
    product = Product.query.get(int(product_id))
    if user is None or product is None:
        return jsonify({"message": "用户或商品不存在"}), 404

    log = simulation_service.record_customer_action(user=user, product=product, action_type=action_type)
    return jsonify({"message": "用户行为记录成功", "log": log})
```

- [ ] **Step 4: Run backend focused tests to verify they pass**

Run: `python -m pytest tests/test_intelligence.py -k "recommendation_action or cold_start_portrait_into_active_portrait" -q`

Expected: PASS

### Task 3: Add failing frontend tests for customer action buttons and refresh

**Files:**
- Modify: `frontend/src/tests/customer-home.test.js`

- [ ] **Step 1: Add mocks for the new action API**

```javascript
vi.mock('../api/recommendation.js', () => ({
  fetchMyRecommendations: vi.fn(),
  fetchTrendProducts: vi.fn(),
  fetchPreferenceProfile: vi.fn(),
  fetchCustomerAiExplanation: vi.fn(),
  recordCustomerAction: vi.fn()
}))
```

- [ ] **Step 2: Add a failing action loop test**

```javascript
it('records customer actions and refreshes recommendation data', async () => {
  recordCustomerAction.mockResolvedValue({
    message: '用户行为记录成功',
    log: { product_id: 1, action_type: 'favorite' }
  })

  fetchMyRecommendations
    .mockResolvedValueOnce({
      mode: 'fallback',
      items: [{ product_id: 1, product_name: '轻量跑鞋', category: '运动鞋', reason: '该商品近期热度较高，适合作为当前阶段的冷启动推荐' }]
    })
    .mockResolvedValueOnce({
      mode: 'personalized',
      items: [{ product_id: 2, product_name: '透气训练T恤', category: '运动服饰', reason: '该商品属于你偏好的 运动服饰 类目，且近期热度表现较好' }]
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
      top_categories: [{ category: '运动服饰', count: 1, score: 3 }],
      top_actions: [{ action_type: 'favorite', count: 1, score: 3 }],
      recent_activity: [],
      engagement_score: 3,
      top_active_hours: [{ hour: 20, count: 1 }],
      price_preference: { average_price: 129, price_band: '大众消费偏好' },
      profile_tags: ['运动服饰偏好']
    })

  const wrapper = mount(CustomerHome)
  await flushPromises()

  expect(wrapper.text()).toContain('冷启动用户')
  await wrapper.find('button[data-testid="customer-action-favorite-1"]').trigger('click')
  await flushPromises()

  expect(recordCustomerAction).toHaveBeenCalledWith({ product_id: 1, action_type: 'favorite' })
  expect(wrapper.text()).toContain('已记录收藏行为')
  expect(wrapper.text()).not.toContain('冷启动用户')
  expect(wrapper.text()).toContain('透气训练T恤')
})
```

- [ ] **Step 3: Run frontend tests to verify they fail**

Run: `npm run test -- src/tests/customer-home.test.js`

Expected: FAIL because the action buttons and `recordCustomerAction()` do not exist yet.

### Task 4: Implement frontend customer action loop

**Files:**
- Modify: `frontend/src/api/recommendation.js`
- Modify: `frontend/src/views/customer/CustomerHome.vue`
- Test: `frontend/src/tests/customer-home.test.js`

- [ ] **Step 1: Add the new recommendation action API wrapper**

```javascript
export async function recordCustomerAction(payload) {
  const response = await http.post('/api/recommendations/actions', payload)
  return response.data
}
```

- [ ] **Step 2: Import the action API and add local action feedback state**

```javascript
import {
  fetchCustomerAiExplanation,
  fetchMyRecommendations,
  fetchPreferenceProfile,
  fetchTrendProducts,
  recordCustomerAction
} from '../../api/recommendation.js'

const actionMessage = ref('')
const actionInFlightKey = ref('')
```

- [ ] **Step 3: Add a helper to record one action and reload the page data**

```javascript
function buildActionKey(productId, actionType) {
  return `${productId}:${actionType}`
}

const ACTION_LABELS = {
  view: '浏览',
  favorite: '收藏',
  cart: '加购',
  purchase: '购买'
}

async function handleCustomerAction(productId, actionType) {
  actionInFlightKey.value = buildActionKey(productId, actionType)
  actionMessage.value = ''
  errorMessage.value = ''

  try {
    await recordCustomerAction({ product_id: productId, action_type: actionType })
    actionMessage.value = `已记录${ACTION_LABELS[actionType]}行为`
    await loadCustomerHome()
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '用户行为记录失败，请稍后重试。'
  } finally {
    actionInFlightKey.value = ''
  }
}
```

- [ ] **Step 4: Render action buttons under each recommendation card**

```vue
<div class="customer-action-buttons">
  <button
    class="ghost-button"
    type="button"
    :data-testid="`customer-action-view-${item.product_id}`"
    :disabled="actionInFlightKey === buildActionKey(item.product_id, 'view')"
    @click="handleCustomerAction(item.product_id, 'view')"
  >
    浏览
  </button>
  <button
    class="ghost-button"
    type="button"
    :data-testid="`customer-action-favorite-${item.product_id}`"
    :disabled="actionInFlightKey === buildActionKey(item.product_id, 'favorite')"
    @click="handleCustomerAction(item.product_id, 'favorite')"
  >
    收藏
  </button>
  <button
    class="ghost-button"
    type="button"
    :data-testid="`customer-action-cart-${item.product_id}`"
    :disabled="actionInFlightKey === buildActionKey(item.product_id, 'cart')"
    @click="handleCustomerAction(item.product_id, 'cart')"
  >
    加购
  </button>
  <button
    class="ghost-button"
    type="button"
    :data-testid="`customer-action-purchase-${item.product_id}`"
    :disabled="actionInFlightKey === buildActionKey(item.product_id, 'purchase')"
    @click="handleCustomerAction(item.product_id, 'purchase')"
  >
    购买
  </button>
</div>
```

- [ ] **Step 5: Render visible success feedback near the recommendation panel**

```vue
<p v-if="actionMessage" class="admin-log-preview__note">{{ actionMessage }}</p>
```

- [ ] **Step 6: Run frontend focused tests to verify they pass**

Run: `npm run test -- src/tests/customer-home.test.js`

Expected: PASS

### Task 5: Run regression verification

**Files:**
- Test: `backend/tests/test_intelligence.py`
- Test: `frontend/src/tests/customer-home.test.js`
- Test: `backend/tests`
- Test: `frontend/src/tests`

- [ ] **Step 1: Run focused backend tests**

Run: `python -m pytest tests/test_intelligence.py -q`

Expected: PASS

- [ ] **Step 2: Run focused frontend tests**

Run: `npm run test -- src/tests/customer-home.test.js`

Expected: PASS

- [ ] **Step 3: Run backend full suite**

Run: `python -m pytest -q`

Expected: PASS

- [ ] **Step 4: Run frontend full suite**

Run: `npm run test`

Expected: PASS
