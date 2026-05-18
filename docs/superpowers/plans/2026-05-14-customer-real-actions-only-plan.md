# Customer Real Actions Only Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make customer recommendation, portrait, and portrait evidence depend only on real front-end actions written with `source_channel="customer_page"`, while keeping trend products on global logs.

**Architecture:** Keep the current routes and page structure. Narrow the data source for `/api/recommendations/me` and `/api/users/portrait` inside the service layer instead of adding new APIs, so the frontend keeps the same contract but receives colder, more truthful data until the user performs real actions. Tests drive the change end-to-end: backend proves source filtering, frontend proves cold-start until real interaction.

**Tech Stack:** Flask, Pytest, Vue 3, Vitest

---

## File Structure

- Modify: `backend/app/services/recommendation_service.py`
  - Restrict personalized recommendation inputs to customer logs from `customer_page`
- Modify: `backend/app/services/prediction_service.py`
  - Restrict portrait, recent activity, and top actions to customer logs from `customer_page`
- Modify: `backend/tests/test_intelligence.py`
  - Add regression tests for mixed-source logs and update assumptions that currently rely on simulated history
- Modify: `frontend/src/tests/customer-home.test.js`
  - Make the customer homepage prove cold start when only simulated history exists
- Modify: `frontend/src/tests/profile-view.test.js`
  - Make the portrait page prove only real front-end actions show up in behavior preference and recent activity
- Test: `frontend/src/tests/customer-home.test.js`
- Test: `frontend/src/tests/profile-view.test.js`
- Test: `backend/tests/test_intelligence.py`

### Task 1: Lock recommendation behavior to real front-end actions only

**Files:**
- Modify: `backend/tests/test_intelligence.py`
- Modify: `backend/app/services/recommendation_service.py`
- Test: `backend/tests/test_intelligence.py`

- [ ] **Step 1: Write the failing backend test for “simulated history does not personalize recommendations”**

Add this test near the existing recommendation tests in `backend/tests/test_intelligence.py`:

```python
def test_customer_recommendations_ignore_simulated_history_and_stay_fallback(
    client, customer_headers, seeded_demo_data
):
    original_logs = list(simulation_memory_store.logs)
    simulation_memory_store.logs = [
        {
            "log_id": "sim-1",
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
            "source_channel": "homepage",
            "session_id": "sim-session-1",
            "stay_duration": 22,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:20:00",
        },
        {
            "log_id": "sim-2",
            "user_id": 2,
            "merchant_id": 2,
            "product_id": 2,
            "product_name": "透气训练T恤",
            "category": "运动服饰",
            "brand": "CloudStep",
            "price": 129.0,
            "action_type": "purchase",
            "region": "华东",
            "device_type": "desktop",
            "source_channel": "search",
            "session_id": "sim-session-2",
            "stay_duration": 17,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:25:00",
        },
    ]

    try:
        response = client.get("/api/recommendations/me", headers=customer_headers)

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["mode"] == "fallback"
        assert payload["items"]
        assert "冷启动推荐" in payload["items"][0]["reason"]
    finally:
        simulation_memory_store.logs = original_logs
```

- [ ] **Step 2: Write the failing backend test for “real customer_page logs can personalize recommendations”**

Add this test below the previous one:

```python
def test_customer_recommendations_use_customer_page_logs_for_personalization(
    client, customer_headers, seeded_demo_data
):
    original_logs = list(simulation_memory_store.logs)
    simulation_memory_store.logs = [
        {
            "log_id": "sim-1",
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
            "source_channel": "homepage",
            "session_id": "sim-session-3",
            "stay_duration": 22,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:20:00",
        },
        {
            "log_id": "real-1",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 2,
            "product_name": "透气训练T恤",
            "category": "运动服饰",
            "brand": "CloudStep",
            "price": 129.0,
            "action_type": "favorite",
            "region": "华南",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "real-session-1",
            "stay_duration": 18,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:30:00",
        },
    ]

    try:
        response = client.get("/api/recommendations/me", headers=customer_headers)

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["mode"] == "personalized"
        assert payload["items"]
        assert "运动服饰" in payload["items"][0]["reason"] or "运动服饰" in "".join(
            item["reason"] for item in payload["items"]
        )
    finally:
        simulation_memory_store.logs = original_logs
```

- [ ] **Step 3: Run the focused backend recommendation tests and verify they fail**

Run:

```bash
python -m pytest backend/tests/test_intelligence.py -k "ignore_simulated_history or use_customer_page_logs_for_personalization" -q
```

Expected: FAIL because recommendation logic still uses all logs for the current user without filtering by `source_channel`.

- [ ] **Step 4: Implement the minimal log-source filter in `RecommendationService`**

Update `backend/app/services/recommendation_service.py`:

```python
from collections import Counter, defaultdict

from .prediction_service import ACTION_SCORES


class RecommendationService:
    CUSTOMER_SOURCE_CHANNEL = "customer_page"

    def _customer_personal_logs(self, user_id, logs):
        return [
            log
            for log in logs
            if log.get("user_id") == user_id
            and log.get("source_channel") == self.CUSTOMER_SOURCE_CHANNEL
        ]

    def _build_fallback_items(self, products, hot_scores, limit=5):
        ranked_products = sorted(
            products,
            key=lambda product: (hot_scores.get(product.id, 0), product.stock),
            reverse=True,
        )

        items = []
        for product in ranked_products[:limit]:
            items.append(
                {
                    "product_id": product.id,
                    "product_name": product.name,
                    "category": product.category,
                    "reason": "该商品近期热度较高，适合作为当前阶段的冷启动推荐",
                }
            )
        return items

    def recommend_for_customer(self, user_id, logs, products):
        if not products:
            return {"mode": "fallback", "items": []}

        interacted_product_ids = set()
        category_counter = Counter()
        hot_scores = defaultdict(int)

        for log in logs:
            score = ACTION_SCORES.get(log["action_type"], 0)
            hot_scores[log["product_id"]] += score

        for log in self._customer_personal_logs(user_id, logs):
            score = ACTION_SCORES.get(log["action_type"], 0)
            category_counter[log["category"]] += score
            interacted_product_ids.add(log["product_id"])

        favorite_category = category_counter.most_common(1)[0][0] if category_counter else None
        if not favorite_category and not interacted_product_ids:
            return {
                "mode": "fallback",
                "items": self._build_fallback_items(products, hot_scores),
            }

        ranked_products = sorted(
            products,
            key=lambda product: (
                1 if product.category == favorite_category else 0,
                hot_scores.get(product.id, 0),
                product.stock,
            ),
            reverse=True,
        )

        items = []
        for product in ranked_products:
            if product.id in interacted_product_ids:
                continue

            if favorite_category and product.category == favorite_category:
                reason = f"该商品属于你偏好的 {favorite_category} 类目，且近期热度表现较好"
            elif favorite_category:
                reason = f"该商品近期热度较高，可作为你常看 {favorite_category} 类目的扩展选择"
            else:
                reason = "该商品近期热度较高，适合作为你的入门推荐"

            items.append(
                {
                    "product_id": product.id,
                    "product_name": product.name,
                    "category": product.category,
                    "reason": reason,
                }
            )

        if not items:
            return {
                "mode": "fallback",
                "items": self._build_fallback_items(products, hot_scores),
            }

        return {"mode": "personalized", "items": items[:5]}
```

- [ ] **Step 5: Run the focused backend recommendation tests and verify they pass**

Run:

```bash
python -m pytest backend/tests/test_intelligence.py -k "ignore_simulated_history or use_customer_page_logs_for_personalization" -q
```

Expected: PASS

- [ ] **Step 6: Commit the recommendation-source change**

```bash
git add backend/app/services/recommendation_service.py backend/tests/test_intelligence.py
git commit -m "fix: restrict customer recommendations to real actions"
```

### Task 2: Lock portrait and recent activity to real front-end actions only

**Files:**
- Modify: `backend/tests/test_intelligence.py`
- Modify: `backend/app/services/prediction_service.py`
- Test: `backend/tests/test_intelligence.py`

- [ ] **Step 1: Write the failing backend test for “portrait ignores simulated history”**

Add this test near the portrait tests in `backend/tests/test_intelligence.py`:

```python
def test_users_portrait_ignores_simulated_history_for_top_actions_and_recent_activity(
    client, customer_headers, seeded_demo_data
):
    original_logs = list(simulation_memory_store.logs)
    simulation_memory_store.logs = [
        {
            "log_id": "sim-portrait-1",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 11,
            "product_name": "旗舰跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 399.0,
            "action_type": "click",
            "region": "华东",
            "device_type": "mobile",
            "source_channel": "recommendation",
            "session_id": "sim-portrait-session-1",
            "stay_duration": 35,
            "is_new_user": False,
            "timestamp": "2026-05-13T09:00:00",
        }
    ]

    try:
        response = client.get("/api/users/portrait", headers=customer_headers)

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["is_cold_start"] is True
        assert payload["top_actions"] == []
        assert payload["recent_activity"] == []
    finally:
        simulation_memory_store.logs = original_logs
```

- [ ] **Step 2: Write the failing backend test for “portrait only shows customer_page actions in ranked sections”**

Add this test below it:

```python
def test_users_portrait_only_uses_customer_page_logs_in_ranked_sections(
    client, customer_headers, seeded_demo_data
):
    original_logs = list(simulation_memory_store.logs)
    simulation_memory_store.logs = [
        {
            "log_id": "sim-portrait-2",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 11,
            "product_name": "旗舰跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 399.0,
            "action_type": "click",
            "region": "华东",
            "device_type": "mobile",
            "source_channel": "recommendation",
            "session_id": "sim-portrait-session-2",
            "stay_duration": 35,
            "is_new_user": False,
            "timestamp": "2026-05-13T09:00:00",
        },
        {
            "log_id": "real-portrait-1",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 12,
            "product_name": "轻盈卫衣",
            "category": "运动服饰",
            "brand": "CloudStep",
            "price": 129.0,
            "action_type": "favorite",
            "region": "华东",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "real-portrait-session-1",
            "stay_duration": 18,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:00:00",
        },
        {
            "log_id": "real-portrait-2",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 13,
            "product_name": "智能手表",
            "category": "智能设备",
            "brand": "CloudStep",
            "price": 599.0,
            "action_type": "purchase",
            "region": "华东",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "real-portrait-session-2",
            "stay_duration": 42,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:05:00",
        },
    ]

    try:
        response = client.get("/api/users/portrait", headers=customer_headers)

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["is_cold_start"] is False
        assert {item["action_type"] for item in payload["top_actions"]} <= {"favorite", "purchase"}
        assert {item["log_id"] for item in payload["recent_activity"]} == {
            "real-portrait-1",
            "real-portrait-2",
        }
    finally:
        simulation_memory_store.logs = original_logs
```

- [ ] **Step 3: Run the focused backend portrait tests and verify they fail**

Run:

```bash
python -m pytest backend/tests/test_intelligence.py -k "ignores_simulated_history_for_top_actions_and_recent_activity or only_uses_customer_page_logs_in_ranked_sections" -q
```

Expected: FAIL because portrait logic still includes all logs for the user.

- [ ] **Step 4: Implement the minimal portrait-source filter in `PredictionService`**

Update `backend/app/services/prediction_service.py`:

```python
class PredictionService:
    CUSTOMER_SOURCE_CHANNEL = "customer_page"

    def _parse_logs(self, logs):
        parsed_logs = []
        latest_timestamp = None
        ...

    def _customer_personal_logs(self, user_id, parsed_logs):
        return [
            (log, timestamp)
            for log, timestamp in parsed_logs
            if log["user_id"] == user_id
            and log.get("source_channel") == self.CUSTOMER_SOURCE_CHANNEL
        ]

    def build_user_portrait(self, user_id, logs, top_categories=3, top_actions=5, recent_activity=5):
        if not logs:
            return self._build_empty_portrait()

        parsed_logs, _ = self._parse_logs(logs)
        user_logs = self._customer_personal_logs(user_id, parsed_logs)

        if not user_logs:
            return self._build_empty_portrait()

        category_stats = defaultdict(lambda: {"category": "", "count": 0, "score": 0})
        action_stats = defaultdict(lambda: {"action_type": "", "count": 0, "score": 0})
        recent_items = []
        active_hours = defaultdict(int)
        total_score = 0

        for log, timestamp in user_logs:
            score = ACTION_SCORES.get(log["action_type"], 0)
            total_score += score
            active_hours[timestamp.hour] += 1
            ...
```

Leave price preference logic unchanged, because it already consumes `user_logs`; once `user_logs` is filtered, the price calculation naturally becomes real-action-only too.

- [ ] **Step 5: Run the focused backend portrait tests and verify they pass**

Run:

```bash
python -m pytest backend/tests/test_intelligence.py -k "ignores_simulated_history_for_top_actions_and_recent_activity or only_uses_customer_page_logs_in_ranked_sections" -q
```

Expected: PASS

- [ ] **Step 6: Commit the portrait-source change**

```bash
git add backend/app/services/prediction_service.py backend/tests/test_intelligence.py
git commit -m "fix: restrict customer portrait to real actions"
```

### Task 3: Update frontend tests to prove cold start until real interaction

**Files:**
- Modify: `frontend/src/tests/customer-home.test.js`
- Modify: `frontend/src/tests/profile-view.test.js`
- Test: `frontend/src/tests/customer-home.test.js`
- Test: `frontend/src/tests/profile-view.test.js`

- [ ] **Step 1: Add a homepage test for “simulated-only history still renders cold start”**

Add this test in `frontend/src/tests/customer-home.test.js`:

```javascript
it('stays in cold start when only simulated history exists for the user', async () => {
  fetchMyRecommendations.mockResolvedValue({
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
  fetchPreferenceProfile.mockResolvedValue({
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

  const wrapper = mount(CustomerHome)
  await flushPromises()

  expect(wrapper.text()).toContain('冷启动推荐')
  expect(wrapper.text()).toContain('冷启动用户')
  expect(wrapper.text()).toContain('最近 5 条画像依据')
  expect(wrapper.text()).toContain('当前暂无历史个人行为记录。')
})
```

- [ ] **Step 2: Tighten the homepage interaction test so it proves “real action exits cold start”**

In the existing `records customer actions and refreshes recommendation data` test, keep the current first payload cold and second payload active, and add these assertions after `await flushPromises()`:

```javascript
expect(wrapper.text()).toContain('冷启动推荐')
expect(wrapper.text()).toContain('冷启动用户')
...
expect(wrapper.text()).not.toContain('冷启动推荐')
expect(wrapper.text()).not.toContain('冷启动用户')
expect(wrapper.text()).toContain('最近 5 条画像依据')
```

- [ ] **Step 3: Add a portrait-page test for “only real actions appear in portrait sections”**

Append this test to `frontend/src/tests/profile-view.test.js`:

```javascript
it('renders only real customer actions in portrait sections', async () => {
  fetchPreferenceProfile.mockResolvedValue({
    user: {
      nickname: '小林',
      region: '华东'
    },
    top_categories: [{ category: '智能设备', count: 1, score: 8 }],
    top_actions: [{ action_type: 'purchase', count: 1, score: 8 }],
    recent_activity: [
      {
        log_id: 'real-portrait-2',
        product_id: 13,
        product_name: '智能手表',
        category: '智能设备',
        action_type: 'purchase',
        timestamp: '2026-05-13T10:05:00'
      }
    ],
    engagement_score: 8,
    top_active_hours: [{ hour: 10, count: 1 }],
    price_preference: {
      average_price: 599,
      price_band: '高消费偏好'
    },
    profile_tags: ['智能设备偏好', '高消费偏好']
  })

  const wrapper = mount(ProfileView)
  await flushPromises()

  expect(wrapper.text()).toContain('购买')
  expect(wrapper.text()).toContain('智能手表 / 智能设备')
  expect(wrapper.text()).not.toContain('点击')
})
```

- [ ] **Step 4: Run the focused frontend tests and verify they pass**

Run:

```bash
npm run test -- src/tests/customer-home.test.js src/tests/profile-view.test.js
```

Expected: PASS

- [ ] **Step 5: Commit the frontend expectation update**

```bash
git add frontend/src/tests/customer-home.test.js frontend/src/tests/profile-view.test.js
git commit -m "test: cover real-action-only customer semantics"
```

### Task 4: Run end-to-end regression verification for the narrowed semantics

**Files:**
- Test: `backend/tests/test_intelligence.py`
- Test: `frontend/src/tests/customer-home.test.js`
- Test: `frontend/src/tests/profile-view.test.js`
- Test: `frontend/src/tests`
- Test: `backend/tests`

- [ ] **Step 1: Run the full backend intelligence suite**

Run:

```bash
python -m pytest backend/tests/test_intelligence.py -q
```

Expected: PASS

- [ ] **Step 2: Run the focused frontend customer suite**

Run:

```bash
npm run test -- src/tests/customer-home.test.js src/tests/profile-view.test.js
```

Expected: PASS

- [ ] **Step 3: Run backend full suite**

Run:

```bash
python -m pytest -q
```

Expected: PASS

- [ ] **Step 4: Run frontend full suite**

Run:

```bash
npm run test
```

Expected: PASS

- [ ] **Step 5: Commit the final regression-verified state**

```bash
git add backend/tests/test_intelligence.py frontend/src/tests/customer-home.test.js frontend/src/tests/profile-view.test.js
git commit -m "fix: make customer intelligence depend on real actions"
```
