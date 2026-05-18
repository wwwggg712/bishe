# Merchant Scope Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make merchant dashboard analytics endpoints return only the current merchant's data while keeping existing API paths and frontend calls unchanged.

**Architecture:** Add a single merchant-scope filter in `AnalyticsService` and thread `merchant_id` from the analytics routes when the caller is a merchant. Keep the current response shapes so `MerchantDashboard.vue` and `frontend/src/api/analytics.js` do not need structural changes. Drive the work with backend tests over mixed multi-merchant logs, then run existing frontend merchant tests as regression protection.

**Tech Stack:** Flask, Flask-JWT-Extended, Pytest, Vue 3, Vitest

---

## File Structure

- Modify: `backend/app/services/analytics_service.py`
  - Add merchant log scoping helper and optional `merchant_id` support in analytics builders
- Modify: `backend/app/routes/analytics.py`
  - Pass the current merchant identity into merchant-facing analytics calls without changing paths
- Modify: `backend/tests/test_analytics.py`
  - Add failing tests for mixed-merchant overview, product lists, category stats, and RFM scope
- Test: `frontend/src/tests/merchant-dashboard.test.js`
  - Existing regression coverage only; no new UI features required

### Task 1: Add failing backend tests for merchant-scoped analytics endpoints

**Files:**
- Modify: `backend/tests/test_analytics.py`
- Test: `backend/tests/test_analytics.py`

- [ ] **Step 1: Add a helper that can seed logs for two different merchants**

Near the top of `backend/tests/test_analytics.py`, replace `_make_log()` with this richer helper:

```python
def _make_log(
    user_id,
    product_id,
    product_name,
    action_type,
    region,
    *,
    merchant_id=1,
    category="运动鞋",
    price=299.0,
):
    return {
        "log_id": f"log-{merchant_id}-{user_id}-{product_id}-{action_type}-{region}",
        "user_id": user_id,
        "merchant_id": merchant_id,
        "product_id": product_id,
        "product_name": product_name,
        "category": category,
        "brand": "CloudStep",
        "price": price,
        "action_type": action_type,
        "region": region,
        "device_type": "mobile",
        "source_channel": "homepage",
        "session_id": f"session-{merchant_id}-{user_id}",
        "stay_duration": 30,
        "is_new_user": False,
        "timestamp": "2026-05-12T10:00:00",
    }
```

- [ ] **Step 2: Add a failing test that merchant overview ignores other merchants**

Append this test after `test_overview_returns_core_metrics`:

```python
def test_merchant_overview_only_counts_current_merchant_logs(
    client, merchant_headers, seeded_demo_data
):
    original_logs = list(simulation_memory_store.logs)
    simulation_memory_store.logs = [
        _make_log(3, 101, "轻量跑鞋", "view", "华东", merchant_id=2, category="运动鞋"),
        _make_log(3, 101, "轻量跑鞋", "purchase", "华东", merchant_id=2, category="运动鞋"),
        _make_log(4, 201, "户外冲锋衣", "view", "华南", merchant_id=4, category="户外装备"),
        _make_log(4, 201, "户外冲锋衣", "purchase", "华南", merchant_id=4, category="户外装备"),
    ]

    try:
        response = client.get("/api/analytics/overview", headers=merchant_headers)

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["totals"] == {
            "pv": 2,
            "uv": 1,
            "purchase_count": 1,
        }
        assert payload["top_products"] == [
            {"product_id": 101, "product_name": "轻量跑鞋", "count": 2}
        ]
        assert payload["regions"] == [{"region": "华东", "count": 2}]
    finally:
        simulation_memory_store.logs = original_logs
```

- [ ] **Step 3: Add a failing test that merchant detail endpoints ignore other merchants**

Append this test below it:

```python
def test_merchant_detail_endpoints_only_return_current_merchant_scope(
    client, merchant_headers, seeded_demo_data
):
    original_logs = list(simulation_memory_store.logs)
    simulation_memory_store.logs = [
        _make_log(3, 101, "轻量跑鞋", "view", "华东", merchant_id=2, category="运动鞋"),
        _make_log(3, 101, "轻量跑鞋", "favorite", "华东", merchant_id=2, category="运动鞋"),
        _make_log(3, 102, "透气训练T恤", "purchase", "华东", merchant_id=2, category="运动服饰", price=129.0),
        _make_log(5, 201, "户外冲锋衣", "view", "华南", merchant_id=4, category="户外装备"),
        _make_log(5, 201, "户外冲锋衣", "cart", "华南", merchant_id=4, category="户外装备"),
    ]

    try:
        funnel_response = client.get("/api/analytics/funnel", headers=merchant_headers)
        categories_response = client.get("/api/analytics/categories", headers=merchant_headers)
        hot_response = client.get("/api/analytics/products/hot", headers=merchant_headers)
        cold_response = client.get("/api/analytics/products/cold", headers=merchant_headers)
        rfm_response = client.get("/api/analytics/users/rfm", headers=merchant_headers)

        assert funnel_response.status_code == 200
        funnel_items = funnel_response.get_json()["items"]
        assert {item["key"]: item["value"] for item in funnel_items} == {
            "view": 1,
            "click": 0,
            "favorite": 1,
            "cart": 0,
            "purchase": 1,
        }

        assert categories_response.status_code == 200
        categories = categories_response.get_json()["items"]
        assert {item["category"] for item in categories} == {"运动鞋", "运动服饰"}

        assert hot_response.status_code == 200
        hot_products = hot_response.get_json()["items"]
        assert all(item["product_name"] != "户外冲锋衣" for item in hot_products)

        assert cold_response.status_code == 200
        cold_products = cold_response.get_json()["items"]
        assert all(item["product_name"] != "户外冲锋衣" for item in cold_products)

        assert rfm_response.status_code == 200
        rfm_items = rfm_response.get_json()["items"]
        assert {item["user_id"] for item in rfm_items} == {3}
    finally:
        simulation_memory_store.logs = original_logs
```

- [ ] **Step 4: Run the focused analytics tests and verify they fail**

Run:

```bash
python -m pytest backend/tests/test_analytics.py -k "merchant_overview_only_counts_current_merchant_logs or merchant_detail_endpoints_only_return_current_merchant_scope" -q
```

Expected: FAIL because the current routes still feed all logs into the service layer.

- [ ] **Step 5: Commit the red tests**

```bash
git add backend/tests/test_analytics.py
git commit -m "test: add merchant-scoped analytics regressions"
```

### Task 2: Add merchant scoping to analytics service and routes

**Files:**
- Modify: `backend/app/services/analytics_service.py`
- Modify: `backend/app/routes/analytics.py`
- Test: `backend/tests/test_analytics.py`

- [ ] **Step 1: Add a reusable merchant log filter in `AnalyticsService`**

At the top of `AnalyticsService`, add:

```python
class AnalyticsService:
    def _merchant_logs(self, logs, merchant_id=None):
        if merchant_id is None:
            return logs

        return [log for log in logs if log.get("merchant_id") == merchant_id]

    def _action_counter(self, logs):
        return Counter(log["action_type"] for log in logs)
```

- [ ] **Step 2: Thread `merchant_id` through the analytics builders**

Update these method signatures and first lines in `backend/app/services/analytics_service.py`:

```python
def build_overview(self, logs, merchant_id=None):
    scoped_logs = self._merchant_logs(logs, merchant_id)
    action_counter = self._action_counter(scoped_logs)
    unique_users = {log["user_id"] for log in scoped_logs}
    product_counter = Counter(
        (log["product_id"], log["product_name"]) for log in scoped_logs
    )
    region_counter = Counter(log["region"] for log in scoped_logs)
    return {
        "totals": {
            "pv": len(scoped_logs),
            "uv": len(unique_users),
            "purchase_count": action_counter.get("purchase", 0),
        },
        ...
    }

def build_funnel(self, logs, merchant_id=None):
    scoped_logs = self._merchant_logs(logs, merchant_id)
    action_counter = self._action_counter(scoped_logs)
    return {
        "items": [
            {"key": step, "label": step, "value": action_counter.get(step, 0)}
            for step in FUNNEL_STEPS
        ]
    }

def build_regions(self, logs, merchant_id=None):
    scoped_logs = self._merchant_logs(logs, merchant_id)
    region_counter = Counter(log["region"] for log in scoped_logs)
    ...

def build_categories(self, logs, merchant_id=None):
    scoped_logs = self._merchant_logs(logs, merchant_id)
    category_counter = Counter(log["category"] for log in scoped_logs)
    ...

def _build_product_scores(self, logs, merchant_id=None):
    scoped_logs = self._merchant_logs(logs, merchant_id)
    product_scores = defaultdict(
        lambda: {"product_id": None, "product_name": "", "hot_score": 0, "count": 0}
    )
    for log in scoped_logs:
        ...
    return list(product_scores.values())

def build_hot_products(self, logs, merchant_id=None):
    items = sorted(
        self._build_product_scores(logs, merchant_id=merchant_id),
        key=lambda item: (item["hot_score"], item["count"]),
        reverse=True,
    )
    return {"items": items[:10]}

def build_cold_products(self, logs, merchant_id=None):
    items = sorted(
        self._build_product_scores(logs, merchant_id=merchant_id),
        key=lambda item: (item["hot_score"], item["count"], item["product_name"]),
    )
    return {"items": items[:10]}

def build_user_rfm(self, logs, merchant_id=None):
    scoped_logs = self._merchant_logs(logs, merchant_id)
    if not scoped_logs:
        return {"items": []}

    parsed_logs = []
    latest_timestamp = None
    for log in scoped_logs:
        timestamp = datetime.fromisoformat(log["timestamp"])
        parsed_logs.append((log, timestamp))
        ...
```

- [ ] **Step 3: Pass the merchant identity from the routes only when the caller is a merchant**

Update `backend/app/routes/analytics.py` like this:

```python
def _current_merchant_scope():
    if get_jwt().get("role") == "merchant":
        return int(get_jwt_identity())
    return None


@bp.get("/overview")
@jwt_required()
def overview():
    payload = analytics_service.build_overview(
        simulation_memory_store.logs,
        merchant_id=_current_merchant_scope(),
    )
    return jsonify(payload)


@bp.get("/funnel")
@jwt_required()
def funnel():
    return jsonify(
        analytics_service.build_funnel(
            simulation_memory_store.logs,
            merchant_id=_current_merchant_scope(),
        )
    )


@bp.get("/regions")
@jwt_required()
def regions():
    return jsonify(
        analytics_service.build_regions(
            simulation_memory_store.logs,
            merchant_id=_current_merchant_scope(),
        )
    )


@bp.get("/categories")
@jwt_required()
def categories():
    return jsonify(
        analytics_service.build_categories(
            simulation_memory_store.logs,
            merchant_id=_current_merchant_scope(),
        )
    )


@bp.get("/products/hot")
@jwt_required()
def hot_products():
    return jsonify(
        analytics_service.build_hot_products(
            simulation_memory_store.logs,
            merchant_id=_current_merchant_scope(),
        )
    )


@bp.get("/products/cold")
@jwt_required()
def cold_products():
    return jsonify(
        analytics_service.build_cold_products(
            simulation_memory_store.logs,
            merchant_id=_current_merchant_scope(),
        )
    )


@bp.get("/users/rfm")
@jwt_required()
def user_rfm():
    return jsonify(
        analytics_service.build_user_rfm(
            simulation_memory_store.logs,
            merchant_id=_current_merchant_scope(),
        )
    )
```

- [ ] **Step 4: Run the focused analytics tests and verify they pass**

Run:

```bash
python -m pytest backend/tests/test_analytics.py -k "merchant_overview_only_counts_current_merchant_logs or merchant_detail_endpoints_only_return_current_merchant_scope" -q
```

Expected: PASS

- [ ] **Step 5: Commit the merchant-scope implementation**

```bash
git add backend/app/services/analytics_service.py backend/app/routes/analytics.py backend/tests/test_analytics.py
git commit -m "fix: scope merchant analytics to current merchant"
```

### Task 3: Verify that existing merchant behavior analytics still works

**Files:**
- Test: `backend/tests/test_analytics.py`

- [ ] **Step 1: Run the existing merchant user behavior endpoint tests**

Run:

```bash
python -m pytest backend/tests/test_analytics.py -k "merchant_user_behavior" -q
```

Expected: PASS, proving the already-scoped behavior endpoint still works.

- [ ] **Step 2: Run the full analytics backend test file**

Run:

```bash
python -m pytest backend/tests/test_analytics.py -q
```

Expected: PASS

- [ ] **Step 3: Commit after analytics file regression passes**

```bash
git add backend/tests/test_analytics.py
git commit -m "test: verify merchant analytics scope regressions"
```

### Task 4: Run merchant dashboard regression without changing frontend API usage

**Files:**
- Test: `frontend/src/tests/merchant-dashboard.test.js`
- Test: `frontend/src/tests`
- Test: `backend/tests`

- [ ] **Step 1: Run the focused merchant dashboard frontend test**

Run:

```bash
npm run test -- src/tests/merchant-dashboard.test.js
```

Expected: PASS

- [ ] **Step 2: Run the backend full suite**

Run:

```bash
python -m pytest -q
```

Expected: PASS

- [ ] **Step 3: Run the frontend full suite**

Run:

```bash
npm run test
```

Expected: PASS

- [ ] **Step 4: Commit the regression-verified final state**

```bash
git add backend/app/services/analytics_service.py backend/app/routes/analytics.py backend/tests/test_analytics.py
git commit -m "fix: align merchant dashboard with merchant scope"
```
