# Defense Credibility Tail Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the last merchant-side credibility gaps by enforcing merchant-only analytics access, scoping anomaly alerts to the current merchant, fixing overview metric definitions, and aligning AI/brief inputs with the same merchant-scoped metrics.

**Architecture:** Keep the existing merchant dashboard page and API paths, but tighten semantics in the backend. `analytics.py` becomes explicitly merchant-only for merchant dashboard endpoints, `PredictionService.build_anomalies()` gains optional `merchant_id` scoping, and `AnalyticsService.build_overview()` returns both behavior volume and true view volume so the frontend can compute a real conversion rate. `MerchantDashboard.vue` then consumes the corrected fields and passes one consistent payload into both AI summary entry points.

**Tech Stack:** Flask, Flask-JWT-Extended, Pytest, Vue 3, Vitest

---

## File Structure

- Modify: `backend/app/routes/analytics.py`
  - Add strict merchant-role guard to merchant dashboard analytics endpoints
- Modify: `backend/app/routes/prediction.py`
  - Scope anomaly endpoint automatically for merchant callers
- Modify: `backend/app/services/analytics_service.py`
  - Return `behavior_count`, `view_count`, `purchase_count`, and a correct `purchase_rate`
- Modify: `backend/app/services/prediction_service.py`
  - Add optional merchant filtering for anomaly generation
- Modify: `backend/tests/test_analytics.py`
  - Add regression tests for merchant-only access and corrected overview totals
- Modify: `backend/tests/test_intelligence.py`
  - Add anomaly-scope regression tests if no dedicated anomaly test file exists
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
  - Update overview cards, conversion-rate consumption, and AI/brief payload building
- Modify: `frontend/src/tests/merchant-dashboard.test.js`
  - Lock the new dashboard metric labels and consistent anomaly/AI behavior

### Task 1: Lock merchant analytics endpoints behind merchant role checks

**Files:**
- Modify: `backend/tests/test_analytics.py`
- Modify: `backend/app/routes/analytics.py`
- Test: `backend/tests/test_analytics.py`

- [ ] **Step 1: Write failing tests for non-merchant access**

Append these tests to `backend/tests/test_analytics.py`:

```python
def test_customer_cannot_access_merchant_overview(client, customer_headers, seeded_demo_data):
    response = client.get("/api/analytics/overview", headers=customer_headers)

    assert response.status_code == 403
    assert response.get_json()["message"] == "仅商家可查看经营分析"


def test_customer_cannot_access_merchant_detail_analytics(
    client, customer_headers, seeded_demo_data
):
    paths = [
        "/api/analytics/funnel",
        "/api/analytics/regions",
        "/api/analytics/categories",
        "/api/analytics/products/hot",
        "/api/analytics/products/cold",
        "/api/analytics/users/rfm",
    ]

    for path in paths:
        response = client.get(path, headers=customer_headers)
        assert response.status_code == 403
        assert response.get_json()["message"] == "仅商家可查看经营分析"
```

- [ ] **Step 2: Run focused tests to verify they fail**

Run:

```bash
python -m pytest tests/test_analytics.py -k "customer_cannot_access_merchant" -q
```

Expected: FAIL because the routes currently allow any authenticated user through.

- [ ] **Step 3: Implement a reusable merchant-only guard in `analytics.py`**

Update `backend/app/routes/analytics.py` like this:

```python
def _ensure_merchant_analytics():
    if get_jwt().get("role") != "merchant":
        return jsonify({"message": "仅商家可查看经营分析"}), 403
    return None


def _current_merchant_scope():
    return int(get_jwt_identity())


@bp.get("/overview")
@jwt_required()
def overview():
    unauthorized = _ensure_merchant_analytics()
    if unauthorized is not None:
        return unauthorized

    payload = analytics_service.build_overview(
        simulation_memory_store.logs,
        merchant_id=_current_merchant_scope(),
    )
    return jsonify(payload)
```

Apply the same `unauthorized` gate to:

- `funnel()`
- `regions()`
- `categories()`
- `hot_products()`
- `cold_products()`
- `user_rfm()`

Leave `/api/analytics/merchant/user-behavior` as-is, because it already has its own merchant guard.

- [ ] **Step 4: Run focused tests to verify they pass**

Run:

```bash
python -m pytest tests/test_analytics.py -k "customer_cannot_access_merchant" -q
```

Expected: PASS

- [ ] **Step 5: Commit the merchant-role access fix**

```bash
git add backend/app/routes/analytics.py backend/tests/test_analytics.py
git commit -m "fix: restrict merchant analytics endpoints to merchants"
```

### Task 2: Scope merchant anomaly alerts and fix overview metric definitions

**Files:**
- Modify: `backend/tests/test_analytics.py`
- Modify: `backend/tests/test_intelligence.py`
- Modify: `backend/app/services/analytics_service.py`
- Modify: `backend/app/routes/prediction.py`
- Modify: `backend/app/services/prediction_service.py`
- Test: `backend/tests/test_analytics.py`
- Test: `backend/tests/test_intelligence.py`

- [ ] **Step 1: Write a failing overview-metric test with correct behavior and view counts**

Replace the assertions in `test_overview_returns_core_metrics()` inside `backend/tests/test_analytics.py` with:

```python
assert payload["totals"] == {
    "behavior_count": 4,
    "view_count": 1,
    "uv": 2,
    "purchase_count": 1,
    "purchase_rate": 1.0,
}
```

Keep the rest of the test intact.

- [ ] **Step 2: Write failing anomaly-scope tests**

Append this test to `backend/tests/test_intelligence.py`:

```python
def test_merchant_anomalies_only_include_current_merchant_logs(
    client, merchant_headers, seeded_demo_data
):
    original_logs = list(simulation_memory_store.logs)
    simulation_memory_store.logs = [
        {
            "log_id": "m2-view-1",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 101,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 299.0,
            "action_type": "view",
            "region": "华东",
            "device_type": "mobile",
            "source_channel": "homepage",
            "session_id": "m2-s1",
            "stay_duration": 20,
            "is_new_user": False,
            "timestamp": "2026-05-12T10:00:00",
        },
        {
            "log_id": "m2-view-2",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 101,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 299.0,
            "action_type": "view",
            "region": "华东",
            "device_type": "mobile",
            "source_channel": "homepage",
            "session_id": "m2-s2",
            "stay_duration": 20,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:00:00",
        },
        {
            "log_id": "m2-view-3",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 101,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 299.0,
            "action_type": "view",
            "region": "华东",
            "device_type": "mobile",
            "source_channel": "homepage",
            "session_id": "m2-s3",
            "stay_duration": 20,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:05:00",
        },
        {
            "log_id": "m4-view-1",
            "user_id": 8,
            "merchant_id": 4,
            "product_id": 404,
            "product_name": "户外冲锋衣",
            "category": "户外装备",
            "brand": "TrailX",
            "price": 599.0,
            "action_type": "view",
            "region": "华南",
            "device_type": "desktop",
            "source_channel": "homepage",
            "session_id": "m4-s1",
            "stay_duration": 30,
            "is_new_user": False,
            "timestamp": "2026-05-12T10:00:00",
        },
        {
            "log_id": "m4-view-2",
            "user_id": 8,
            "merchant_id": 4,
            "product_id": 404,
            "product_name": "户外冲锋衣",
            "category": "户外装备",
            "brand": "TrailX",
            "price": 599.0,
            "action_type": "view",
            "region": "华南",
            "device_type": "desktop",
            "source_channel": "homepage",
            "session_id": "m4-s2",
            "stay_duration": 30,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:00:00",
        },
        {
            "log_id": "m4-view-3",
            "user_id": 8,
            "merchant_id": 4,
            "product_id": 404,
            "product_name": "户外冲锋衣",
            "category": "户外装备",
            "brand": "TrailX",
            "price": 599.0,
            "action_type": "view",
            "region": "华南",
            "device_type": "desktop",
            "source_channel": "homepage",
            "session_id": "m4-s3",
            "stay_duration": 30,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:05:00",
        },
    ]

    try:
        response = client.get("/api/prediction/anomalies?severity=high", headers=merchant_headers)

        assert response.status_code == 200
        items = response.get_json()["items"]
        assert items
        assert all(item["target"] != "户外冲锋衣" for item in items)
    finally:
        simulation_memory_store.logs = original_logs
```

Also append:

```python
def test_customer_cannot_access_merchant_scoped_anomaly_insights(
    client, customer_headers, seeded_demo_data
):
    response = client.get("/api/prediction/anomalies?severity=high", headers=customer_headers)

    assert response.status_code == 403
    assert response.get_json()["message"] == "仅商家可查看异常预警"
```

- [ ] **Step 3: Run focused tests and verify they fail**

Run:

```bash
python -m pytest tests/test_analytics.py -k "overview_returns_core_metrics" -q
python -m pytest tests/test_intelligence.py -k "merchant_anomalies_only_include_current_merchant_logs or customer_cannot_access_merchant_scoped_anomaly_insights" -q
```

Expected: FAIL because overview still returns `pv`, and anomalies are still global and role-open.

- [ ] **Step 4: Implement corrected overview totals in `AnalyticsService`**

Update `build_overview()` in `backend/app/services/analytics_service.py`:

```python
def build_overview(self, logs, merchant_id=None):
    scoped_logs = self._merchant_logs(logs, merchant_id)
    action_counter = self._action_counter(scoped_logs)
    unique_users = {log["user_id"] for log in scoped_logs}
    product_counter = Counter(
        (log["product_id"], log["product_name"]) for log in scoped_logs
    )
    region_counter = Counter(log["region"] for log in scoped_logs)
    view_count = action_counter.get("view", 0)
    purchase_count = action_counter.get("purchase", 0)
    purchase_rate = purchase_count / view_count if view_count else 0

    return {
        "totals": {
            "behavior_count": len(scoped_logs),
            "view_count": view_count,
            "uv": len(unique_users),
            "purchase_count": purchase_count,
            "purchase_rate": round(purchase_rate, 4),
        },
        "funnel": {step: action_counter.get(step, 0) for step in FUNNEL_STEPS},
        "top_products": [
            {
                "product_id": product_id,
                "product_name": product_name,
                "count": count,
            }
            for (product_id, product_name), count in product_counter.most_common(5)
        ],
        "regions": [
            {"region": region, "count": count}
            for region, count in region_counter.most_common(5)
        ],
    }
```

- [ ] **Step 5: Implement merchant-scoped anomalies**

Update `backend/app/services/prediction_service.py`:

```python
def build_anomalies(self, logs, merchant_id=None):
    if merchant_id is not None:
        logs = [log for log in logs if log.get("merchant_id") == merchant_id]
    if not logs:
        return {"items": []}
    ...
```

Update `backend/app/routes/prediction.py`:

```python
def _ensure_merchant_anomalies():
    if get_jwt().get("role") != "merchant":
        return jsonify({"message": "仅商家可查看异常预警"}), 403
    return None


@bp.get("/anomalies")
@jwt_required()
def anomalies():
    unauthorized = _ensure_merchant_anomalies()
    if unauthorized is not None:
        return unauthorized

    payload = prediction_service.build_anomalies(
        simulation_memory_store.logs,
        merchant_id=int(get_jwt_identity()),
    )
    severity = (request.args.get("severity") or "").strip().lower()
    if severity:
        payload["items"] = [item for item in payload["items"] if item["severity"] == severity]
    return jsonify(payload)
```

- [ ] **Step 6: Run focused tests to verify they pass**

Run:

```bash
python -m pytest tests/test_analytics.py -k "overview_returns_core_metrics" -q
python -m pytest tests/test_intelligence.py -k "merchant_anomalies_only_include_current_merchant_logs or customer_cannot_access_merchant_scoped_anomaly_insights" -q
```

Expected: PASS

- [ ] **Step 7: Commit overview/anomaly fixes**

```bash
git add backend/app/services/analytics_service.py backend/app/services/prediction_service.py backend/app/routes/prediction.py backend/tests/test_analytics.py backend/tests/test_intelligence.py
git commit -m "fix: align merchant metrics and anomaly scope"
```

### Task 3: Align merchant dashboard cards and AI/brief payloads to one metric definition

**Files:**
- Modify: `frontend/src/tests/merchant-dashboard.test.js`
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
- Test: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Update the merchant dashboard test data to the new totals contract**

In `frontend/src/tests/merchant-dashboard.test.js`, change the mocked `fetchOverview` payload to:

```javascript
fetchOverview.mockResolvedValue({
  totals: {
    behavior_count: 1280,
    view_count: 860,
    uv: 420,
    purchase_count: 64,
    purchase_rate: 0.0744
  },
  top_products: [
    { product_id: 1, product_name: '轻量跑鞋', count: 186, hot_score: 640 },
    { product_id: 2, product_name: '城市双肩包', count: 132, hot_score: 438 }
  ],
  regions: [{ region: '华东', count: 460 }]
})
```

- [ ] **Step 2: Add failing assertions for the corrected merchant overview semantics**

In `renders redesigned merchant cockpit sections and loaded analytics data`, add:

```javascript
expect(wrapper.text()).toContain('行为总量')
expect(wrapper.text()).toContain('浏览量')
expect(wrapper.text()).toContain('成交笔数')
expect(wrapper.text()).toContain('成交转化率')
expect(wrapper.text()).toContain('860')
expect(wrapper.text()).toContain('7.4%')
```

In `renders merchant ai analysis entry and result`, add:

```javascript
await wrapper.find('button[data-testid="merchant-ai-generate"]').trigger('click')
await flushPromises()

expect(fetchMerchantAiAnalysis).toHaveBeenCalledWith(
  expect.objectContaining({
    product_name: '轻量跑鞋',
    hot_score: 640,
    purchase_rate: 0.0744,
    anomaly_count: 1,
    category_name: '运动鞋'
  })
)
```

Also add a new test:

```javascript
it('uses the same merchant-scoped metrics for brief and ai summaries', async () => {
  mount(MerchantDashboard, {
    global: {
      stubs: {
        RouterLink: true
      }
    }
  })

  await flushPromises()

  expect(fetchMerchantBrief).toHaveBeenCalledWith(
    expect.objectContaining({
      product_name: '轻量跑鞋',
      hot_score: 640,
      purchase_rate: 0.0744
    })
  )
})
```

- [ ] **Step 3: Run focused frontend tests and verify they fail**

Run:

```bash
npm run test -- src/tests/merchant-dashboard.test.js
```

Expected: FAIL because the dashboard still reads `totals.pv`, still passes inconsistent rates, and still uses `count` in one summary path.

- [ ] **Step 4: Implement the corrected dashboard metric consumption**

Update `frontend/src/views/merchant/MerchantDashboard.vue`:

```javascript
const overview = ref({
  totals: {
    behavior_count: 0,
    view_count: 0,
    uv: 0,
    purchase_count: 0,
    purchase_rate: 0
  },
  funnel: {
    view: 0,
    click: 0,
    favorite: 0,
    cart: 0,
    purchase: 0
  },
  top_products: [],
  regions: []
})

const overviewCards = computed(() => {
  const totals = overview.value.totals
  const purchaseRate = `${(((totals.purchase_rate || 0) * 100)).toFixed(1)}%`

  return [
    {
      label: '行为总量',
      value: totals.behavior_count,
      hint: '全链路行为次数'
    },
    {
      label: '浏览量',
      value: totals.view_count,
      hint: 'view 行为次数'
    },
    {
      label: '成交笔数',
      value: totals.purchase_count,
      hint: 'purchase 行为次数'
    },
    {
      label: '成交转化率',
      value: purchaseRate,
      hint: '购买行为 / 浏览行为'
    }
  ]
})
```

Add a helper above `handleGenerateAiAnalysis()`:

```javascript
function buildMerchantInsightPayload() {
  const bestProduct = hotProducts.value[0]
  return {
    product_name: bestProduct?.product_name || '暂无重点商品',
    hot_score: bestProduct?.hot_score ?? bestProduct?.count ?? 0,
    purchase_rate: overview.value.totals.purchase_rate || 0,
    anomaly_count: criticalAnomalies.value.length,
    cold_product_count: coldProducts.value.length,
    category_name: categoryItems.value[0]?.category || '综合类目'
  }
}
```

Then update both summary calls:

```javascript
async function handleGenerateAiAnalysis() {
  ...
  try {
    const payload = await fetchMerchantAiAnalysis(buildMerchantInsightPayload())
    ...
  }
}
```

And in `loadDashboard()`:

```javascript
if (hotProducts.value.length) {
  const briefPayload = await fetchMerchantBrief({
    scene: 'merchant',
    ...buildMerchantInsightPayload(),
    trend_label: anomalyItems.value.length ? 'warning' : 'up'
  })
  briefSummary.value = briefPayload.summary || '今日经营简报生成成功。'
}
```

- [ ] **Step 5: Run focused frontend tests and verify they pass**

Run:

```bash
npm run test -- src/tests/merchant-dashboard.test.js
```

Expected: PASS

- [ ] **Step 6: Commit the frontend credibility fixes**

```bash
git add frontend/src/views/merchant/MerchantDashboard.vue frontend/src/tests/merchant-dashboard.test.js
git commit -m "fix: align merchant dashboard metrics and ai inputs"
```

### Task 4: Run final regression and perform one more credibility review

**Files:**
- Test: `backend/tests/test_analytics.py`
- Test: `backend/tests/test_intelligence.py`
- Test: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Run backend analytics regression**

Run:

```bash
python -m pytest tests/test_analytics.py -q
```

Expected: PASS

- [ ] **Step 2: Run backend intelligence regression**

Run:

```bash
python -m pytest tests/test_intelligence.py -q
```

Expected: PASS

- [ ] **Step 3: Run frontend merchant regression**

Run:

```bash
npm run test -- src/tests/merchant-dashboard.test.js
```

Expected: PASS

- [ ] **Step 4: Run backend full suite**

Run:

```bash
python -m pytest -q
```

Expected: PASS

- [ ] **Step 5: Run frontend full suite**

Run:

```bash
npm run test
```

Expected: PASS

- [ ] **Step 6: Perform final credibility check**

Review these points against the running code:

```text
1. Customer users receive 403 on merchant analytics endpoints.
2. Merchant anomaly alerts are scoped to the current merchant.
3. Dashboard labels match the actual metric definitions.
4. AI analysis and daily brief receive the same hot_score and purchase_rate.
5. Merchant page no longer mixes global anomalies with merchant-scoped modules.
```

Record the result in the handoff summary.

- [ ] **Step 7: Commit the regression-verified final state**

```bash
git add backend/app/routes/analytics.py backend/app/routes/prediction.py backend/app/services/analytics_service.py backend/app/services/prediction_service.py backend/tests/test_analytics.py backend/tests/test_intelligence.py frontend/src/views/merchant/MerchantDashboard.vue frontend/src/tests/merchant-dashboard.test.js
git commit -m "fix: close merchant dashboard credibility gaps"
```
