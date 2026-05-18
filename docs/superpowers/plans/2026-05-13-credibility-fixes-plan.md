# Credibility Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the highest-priority credibility issues so simulated user logs only represent customers, merchant linkage really means “recent”, linkage summaries are fully Chinese, and customer spending preference uses high-intent behavior instead of all actions.

**Architecture:** Keep the existing product surface unchanged and tighten the semantics underneath it. The backend remains the main area of change: simulation only generates customer actions, merchant linkage aggregates over a recent 24-hour window with Chinese labels, and portrait pricing uses purchase-first intent rules. The frontend only needs light assertion updates for the new wording.

**Tech Stack:** Flask, Flask-JWT-Extended, Vue 3, Pytest, Vitest

---

### Task 1: Add failing tests for simulation user role filtering

**Files:**
- Modify: `backend/tests/test_simulation.py`

- [ ] **Step 1: Add a failing test that generated users are all customers**

```python
def test_generate_once_from_db_only_creates_customer_behavior_logs(client, admin_headers, seeded_demo_data):
    from app.models.user import User
    from app.services.simulation_service import simulation_service

    logs = simulation_service.generate_once_from_db(batch_size=20)
    customer_ids = {user.id for user in User.query.filter_by(role="customer").all()}

    assert logs
    assert all(log["user_id"] in customer_ids for log in logs)
```

- [ ] **Step 2: Run the focused simulation test and verify it fails**

Run: `python -m pytest tests/test_simulation.py -k "only_creates_customer_behavior_logs" -q`

Expected: FAIL because the current generator still includes merchant users in the sampled pool.

### Task 2: Implement customer-only simulation logs

**Files:**
- Modify: `backend/app/services/simulation_service.py`
- Test: `backend/tests/test_simulation.py`

- [ ] **Step 1: Change the user query to only include customers**

```python
users = User.query.filter_by(role="customer").all()
```

- [ ] **Step 2: Run the focused simulation test and verify it passes**

Run: `python -m pytest tests/test_simulation.py -k "only_creates_customer_behavior_logs" -q`

Expected: PASS

### Task 3: Add failing tests for merchant linkage recent window and Chinese summaries

**Files:**
- Modify: `backend/tests/test_analytics.py`

- [ ] **Step 1: Add a failing test for the recent 24-hour window**

```python
def test_merchant_user_behavior_only_counts_recent_24_hour_intent_logs(
    client, merchant_headers, seeded_demo_data
):
    from app.services.simulation_service import simulation_memory_store

    original_logs = list(simulation_memory_store.logs)
    simulation_memory_store.logs = [
        {
            "log_id": "recent-1",
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
            "session_id": "s-1",
            "stay_duration": 12,
            "is_new_user": False,
            "timestamp": "2026-05-13T12:00:00",
        },
        {
            "log_id": "old-1",
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
            "session_id": "s-2",
            "stay_duration": 20,
            "is_new_user": False,
            "timestamp": "2026-05-11T09:00:00",
        },
    ]

    try:
        response = client.get("/api/analytics/merchant/user-behavior", headers=merchant_headers)
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["preference_changes"]
        assert payload["preference_changes"][0]["category"] == "运动鞋"
        assert all(item["product_name"] != "透气训练T恤" for item in payload["intent_products"])
    finally:
        simulation_memory_store.logs = original_logs
```

- [ ] **Step 2: Add a failing test for Chinese summary wording**

```python
def test_merchant_user_behavior_summaries_use_chinese_action_labels(
    client, merchant_headers, seeded_demo_data
):
    from app.services.simulation_service import simulation_memory_store

    original_logs = list(simulation_memory_store.logs)
    simulation_memory_store.logs = [
        {
            "log_id": "cn-1",
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
            "session_id": "s-3",
            "stay_duration": 16,
            "is_new_user": False,
            "timestamp": "2026-05-13T12:10:00",
        }
    ]

    try:
        response = client.get("/api/analytics/merchant/user-behavior", headers=merchant_headers)
        payload = response.get_json()
        assert "收藏" in payload["preference_changes"][0]["summary"]
        assert "favorite" not in payload["preference_changes"][0]["summary"]
    finally:
        simulation_memory_store.logs = original_logs
```

- [ ] **Step 3: Run the focused analytics tests and verify they fail**

Run: `python -m pytest tests/test_analytics.py -k "recent_24_hour or chinese_action_labels" -q`

Expected: FAIL because the current analytics logic scans all history and builds English action summaries.

### Task 4: Implement recent-window merchant linkage with Chinese summaries

**Files:**
- Modify: `backend/app/services/analytics_service.py`
- Test: `backend/tests/test_analytics.py`

- [ ] **Step 1: Add shared Chinese action labels**

```python
MERCHANT_BEHAVIOR_LABELS = {
    "favorite": "收藏",
    "cart": "加购",
    "purchase": "购买",
}
```

- [ ] **Step 2: Add a helper that filters logs to the latest 24-hour window**

```python
def _recent_window_logs(self, logs, hours=24):
    if not logs:
        return []

    latest_timestamp = max(datetime.fromisoformat(log["timestamp"]) for log in logs)
    threshold = latest_timestamp - timedelta(hours=hours)
    return [
        log
        for log in logs
        if datetime.fromisoformat(log["timestamp"]) >= threshold
    ]
```

- [ ] **Step 3: Use the filtered logs inside merchant linkage**

```python
def build_merchant_user_behavior(self, merchant_id, logs):
    recent_logs = self._recent_window_logs(logs, hours=24)
    category_stats = defaultdict(
        lambda: {"category": "", "scores": defaultdict(int)}
    )
    product_stats = defaultdict(
        lambda: {"product_id": None, "product_name": "", "scores": defaultdict(int)}
    )

    for log in recent_logs:
        if log.get("merchant_id") != merchant_id:
            continue
```

- [ ] **Step 4: Build Chinese summaries instead of raw action codes**

```python
action_label = MERCHANT_BEHAVIOR_LABELS.get(top_action, top_action)
preference_changes.append(
    {
        "category": item["category"],
        "top_action": top_action,
        "action_count": action_count,
        "summary": f"{item['category']}最近{action_label}行为更活跃",
    }
)
```

```python
action_label = MERCHANT_BEHAVIOR_LABELS.get(top_action, top_action)
intent_products.append(
    {
        "product_id": item["product_id"],
        "product_name": item["product_name"],
        "top_action": top_action,
        "action_count": action_count,
        "summary": f"{item['product_name']}最近{action_label}较多，值得重点关注",
    }
)
```

- [ ] **Step 5: Run the focused analytics tests and verify they pass**

Run: `python -m pytest tests/test_analytics.py -k "recent_24_hour or chinese_action_labels" -q`

Expected: PASS

### Task 5: Add failing tests for portrait spending preference intent rules

**Files:**
- Modify: `backend/tests/test_intelligence.py`

- [ ] **Step 1: Add a failing test that purchase price takes priority**

```python
def test_customer_portrait_price_preference_prioritizes_purchase_logs(client, customer_headers, seeded_demo_data):
    from app.services.simulation_service import simulation_memory_store

    original_logs = list(simulation_memory_store.logs)
    simulation_memory_store.logs = [
        {
            "log_id": "pp-1",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 1,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 999.0,
            "action_type": "view",
            "region": "华南",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "s-1",
            "stay_duration": 10,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:00:00",
        },
        {
            "log_id": "pp-2",
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
            "session_id": "s-2",
            "stay_duration": 30,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:05:00",
        },
    ]

    try:
        response = client.get("/api/users/portrait", headers=customer_headers)
        payload = response.get_json()
        assert payload["price_preference"]["average_price"] == 129.0
    finally:
        simulation_memory_store.logs = original_logs
```

- [ ] **Step 2: Add a failing fallback test for cart and favorite**

```python
def test_customer_portrait_price_preference_falls_back_to_cart_and_favorite(client, customer_headers, seeded_demo_data):
    from app.services.simulation_service import simulation_memory_store

    original_logs = list(simulation_memory_store.logs)
    simulation_memory_store.logs = [
        {
            "log_id": "pf-1",
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
            "session_id": "s-3",
            "stay_duration": 10,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:10:00",
        },
        {
            "log_id": "pf-2",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 2,
            "product_name": "透气训练T恤",
            "category": "运动服饰",
            "brand": "CloudStep",
            "price": 129.0,
            "action_type": "cart",
            "region": "华南",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "s-4",
            "stay_duration": 18,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:12:00",
        },
        {
            "log_id": "pf-3",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 3,
            "product_name": "智能运动手环",
            "category": "智能设备",
            "brand": "CloudStep",
            "price": 999.0,
            "action_type": "view",
            "region": "华南",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "s-5",
            "stay_duration": 40,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:15:00",
        },
    ]

    try:
        response = client.get("/api/users/portrait", headers=customer_headers)
        payload = response.get_json()
        assert payload["price_preference"]["average_price"] == 214.0
        assert payload["price_preference"]["price_band"] == "中高消费偏好"
    finally:
        simulation_memory_store.logs = original_logs
```

- [ ] **Step 3: Add a failing no-intent fallback test**

```python
def test_customer_portrait_price_preference_returns_no_data_without_intent_actions(client, customer_headers, seeded_demo_data):
    from app.services.simulation_service import simulation_memory_store

    original_logs = list(simulation_memory_store.logs)
    simulation_memory_store.logs = [
        {
            "log_id": "pn-1",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 1,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 299.0,
            "action_type": "view",
            "region": "华南",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "s-6",
            "stay_duration": 15,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:20:00",
        }
    ]

    try:
        response = client.get("/api/users/portrait", headers=customer_headers)
        payload = response.get_json()
        assert payload["price_preference"]["average_price"] == 0
        assert payload["price_preference"]["price_band"] == "暂无数据"
    finally:
        simulation_memory_store.logs = original_logs
```

- [ ] **Step 4: Run the focused portrait tests and verify they fail**

Run: `python -m pytest tests/test_intelligence.py -k "price_preference" -q`

Expected: FAIL because average price is currently based on all user logs.

### Task 6: Implement high-intent spending preference rules

**Files:**
- Modify: `backend/app/services/prediction_service.py`
- Test: `backend/tests/test_intelligence.py`

- [ ] **Step 1: Add a helper that selects price samples by intent priority**

```python
def _select_price_logs(self, user_logs):
    purchase_logs = [log for log, _ in user_logs if log["action_type"] == "purchase"]
    if purchase_logs:
        return purchase_logs

    intent_logs = [
        log
        for log, _ in user_logs
        if log["action_type"] in {"cart", "favorite"}
    ]
    if intent_logs:
        return intent_logs

    return []
```

- [ ] **Step 2: Use the selected price logs instead of all user logs**

```python
price_logs = self._select_price_logs(user_logs)
total_price = sum(float(log.get("price", 0) or 0) for log in price_logs)
average_price = round(total_price / len(price_logs), 2) if price_logs else 0
```

- [ ] **Step 3: Run the focused portrait tests and verify they pass**

Run: `python -m pytest tests/test_intelligence.py -k "price_preference" -q`

Expected: PASS

### Task 7: Add a frontend assertion for Chinese merchant linkage wording

**Files:**
- Modify: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Add a focused assertion for the Chinese linkage summary**

```javascript
expect(wrapper.text()).toContain('运动鞋最近加购行为更活跃')
expect(wrapper.text()).not.toContain('cart行为')
```

- [ ] **Step 2: Run the focused merchant dashboard test and verify it fails**

Run: `npm run test -- src/tests/merchant-dashboard.test.js`

Expected: FAIL because the current mock/real wording is not yet aligned with the backend semantics.

### Task 8: Align the merchant frontend copy with the new “recent 24h” semantics

**Files:**
- Modify: `frontend/src/tests/merchant-dashboard.test.js`
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
- Test: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Update the merchant test mock to use Chinese summaries**

```javascript
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
```

- [ ] **Step 2: Add a line in the merchant card description to make the recent window explicit**

```vue
<p>把最近 24 小时用户侧的高意向行为变化，直接映射成商家可理解的经营信号。</p>
```

- [ ] **Step 3: Run the focused merchant dashboard test and verify it passes**

Run: `npm run test -- src/tests/merchant-dashboard.test.js`

Expected: PASS

### Task 9: Run regression verification

**Files:**
- Test: `backend/tests/test_simulation.py`
- Test: `backend/tests/test_analytics.py`
- Test: `backend/tests/test_intelligence.py`
- Test: `frontend/src/tests/merchant-dashboard.test.js`
- Test: `backend/tests`
- Test: `frontend/src/tests`

- [ ] **Step 1: Run focused backend simulation tests**

Run: `python -m pytest tests/test_simulation.py -q`

Expected: PASS

- [ ] **Step 2: Run focused backend analytics tests**

Run: `python -m pytest tests/test_analytics.py -q`

Expected: PASS

- [ ] **Step 3: Run focused backend intelligence tests**

Run: `python -m pytest tests/test_intelligence.py -q`

Expected: PASS

- [ ] **Step 4: Run focused merchant frontend tests**

Run: `npm run test -- src/tests/merchant-dashboard.test.js`

Expected: PASS

- [ ] **Step 5: Run backend full suite**

Run: `python -m pytest -q`

Expected: PASS

- [ ] **Step 6: Run frontend full suite**

Run: `npm run test`

Expected: PASS
