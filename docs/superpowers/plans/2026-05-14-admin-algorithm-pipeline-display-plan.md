# Admin Algorithm Pipeline Display Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dynamic algorithm-processing pipeline to the admin log preview page so the system can visibly show how logs are transformed into analytics, recommendation, portrait, anomaly, segmentation, and AI explanation outputs.

**Architecture:** Keep the admin log preview page as the single evidence page. Add one new admin-only backend aggregation endpoint that summarizes existing live system state from `simulation_memory_store.logs`, analytics services, prediction services, recommendation semantics, and LLM mode metadata. Then render that payload as a pipeline card strip above the raw log preview without changing the existing preview contract or creating a new page.

**Tech Stack:** Flask, Flask-JWT-Extended, Pytest, Vue 3, Vitest

---

## File Structure

- Modify: `backend/app/routes/admin.py`
  - Add `GET /api/admin/algorithm-pipeline`
- Modify: `backend/tests/test_admin.py`
  - Add backend coverage for the new pipeline endpoint
- Modify: `frontend/src/api/admin.js`
  - Add `fetchAdminAlgorithmPipeline()`
- Modify: `frontend/src/views/admin/AdminLogPreviewPage.vue`
  - Load and render the dynamic algorithm pipeline module
- Modify: `frontend/src/tests/admin-pages.test.js`
  - Assert the new pipeline module renders node names and dynamic metrics

### Task 1: Add a failing backend test and implement the admin aggregation endpoint

**Files:**
- Modify: `backend/tests/test_admin.py`
- Modify: `backend/app/routes/admin.py`
- Test: `backend/tests/test_admin.py`

- [ ] **Step 1: Write the failing backend test for the admin pipeline endpoint**

Append this test to `backend/tests/test_admin.py`:

```python
def test_admin_algorithm_pipeline_returns_live_processing_summary(
    client, admin_headers, seeded_demo_data
):
    simulation_memory_store.logs = [
        {
            "log_id": "log-1",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 1,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 299.0,
            "action_type": "view",
            "region": "华东",
            "device_type": "mobile",
            "source_channel": "search",
            "session_id": "s-1",
            "stay_duration": 30,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:00:00",
        },
        {
            "log_id": "log-2",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 1,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 299.0,
            "action_type": "purchase",
            "region": "华东",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "s-2",
            "stay_duration": 45,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:05:00",
        },
    ]

    response = client.get("/api/admin/algorithm-pipeline", headers=admin_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert set(payload.keys()) == {
        "log_input",
        "aggregation",
        "scoring",
        "portrait_and_recommendation",
        "anomalies",
        "segmentation",
        "ai_meta",
    }
    assert payload["log_input"]["total_logs"] == 2
    assert payload["aggregation"]["behavior_count"] == 2
    assert payload["aggregation"]["view_count"] == 1
    assert payload["aggregation"]["purchase_count"] == 1
    assert payload["scoring"]["weight_rule"] == "view=1, click=2, favorite=3, cart=5, purchase=8"
    assert payload["portrait_and_recommendation"]["real_action_logs"] == 1
    assert payload["ai_meta"]["mode"] in {"provider", "fallback"}
```

- [ ] **Step 2: Run the focused backend test and verify it fails**

Run:

```bash
python -m pytest tests/test_admin.py -k "algorithm_pipeline" -q
```

Expected: FAIL because `/api/admin/algorithm-pipeline` does not exist yet.

- [ ] **Step 3: Implement the minimal aggregation endpoint in `admin.py`**

Add the required imports near the top of `backend/app/routes/admin.py`:

```python
import os
from collections import Counter

from ..services.analytics_service import analytics_service
from ..services.prediction_service import prediction_service
from ..services.recommendation_service import recommendation_service
```

Then append this route:

```python
@bp.get("/algorithm-pipeline")
@jwt_required()
def algorithm_pipeline():
    unauthorized = _ensure_admin()
    if unauthorized is not None:
        return unauthorized

    logs = simulation_memory_store.logs
    action_counter = Counter(log["action_type"] for log in logs)
    latest_timestamp = max((log["timestamp"] for log in logs), default="暂无数据")
    overview = analytics_service.build_overview(logs)
    hot_items = analytics_service.build_hot_products(logs)["items"]
    cold_items = analytics_service.build_cold_products(logs)["items"]
    anomalies = prediction_service.build_anomalies(logs)["items"]
    segmentation = analytics_service.build_user_rfm(logs)["items"]

    customer_logs = [
        log for log in logs if log.get("source_channel") == "customer_page"
    ]

    provider = os.getenv("LLM_PROVIDER", "").strip()
    api_key = os.getenv("LLM_API_KEY", "").strip()
    base_url = os.getenv("LLM_BASE_URL", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()
    has_provider = bool(provider and api_key and base_url and model)

    payload = {
        "log_input": {
            "total_logs": len(logs),
            "action_type_count": len(action_counter),
            "latest_timestamp": latest_timestamp,
        },
        "aggregation": {
            "behavior_count": overview["totals"]["behavior_count"],
            "view_count": overview["totals"]["view_count"],
            "purchase_count": overview["totals"]["purchase_count"],
            "region_count": len(overview["regions"]),
        },
        "scoring": {
            "weight_rule": "view=1, click=2, favorite=3, cart=5, purchase=8",
            "hot_product_count": len(hot_items),
            "cold_product_count": len(cold_items),
        },
        "portrait_and_recommendation": {
            "real_action_logs": len(customer_logs),
            "cold_start_state": "冷启动" if not customer_logs else "已进入个性化",
            "recommendation_mode": "fallback" if not customer_logs else "personalized",
        },
        "anomalies": {
            "high_risk_count": sum(1 for item in anomalies if item["severity"] == "high"),
            "medium_risk_count": sum(1 for item in anomalies if item["severity"] == "medium"),
            "window_rule": "最近2天 vs 前3天",
        },
        "segmentation": {
            "high_value_users": sum(1 for item in segmentation if item["label"] == "高价值用户"),
            "potential_users": sum(1 for item in segmentation if item["label"] == "潜力转化用户"),
            "inactive_users": sum(1 for item in segmentation if item["label"] == "待激活用户"),
        },
        "ai_meta": {
            "mode": "provider" if has_provider else "fallback",
            "provider": provider or "internal",
            "model": model or "rule-based-fallback",
        },
    }
    return jsonify(payload)
```

- [ ] **Step 4: Run the focused backend test and verify it passes**

Run:

```bash
python -m pytest tests/test_admin.py -k "algorithm_pipeline" -q
```

Expected: PASS

- [ ] **Step 5: Commit the admin aggregation endpoint**

```bash
git add backend/app/routes/admin.py backend/tests/test_admin.py
git commit -m "feat: add admin algorithm pipeline endpoint"
```

### Task 2: Add a failing frontend test and render the pipeline module on the admin log preview page

**Files:**
- Modify: `frontend/src/api/admin.js`
- Modify: `frontend/src/views/admin/AdminLogPreviewPage.vue`
- Modify: `frontend/src/tests/admin-pages.test.js`
- Test: `frontend/src/tests/admin-pages.test.js`

- [ ] **Step 1: Add the new admin API function**

In `frontend/src/api/admin.js`, add:

```javascript
export async function fetchAdminAlgorithmPipeline() {
  const response = await http.get('/api/admin/algorithm-pipeline')
  return response.data
}
```

- [ ] **Step 2: Write the failing frontend test for the algorithm pipeline module**

Update the admin API mock at the top of `frontend/src/tests/admin-pages.test.js`:

```javascript
vi.mock('../api/admin.js', () => ({
  fetchAdminUsers: vi.fn(),
  fetchJobs: vi.fn(),
  fetchAdminLogPreview: vi.fn(),
  fetchAdminAlgorithmPipeline: vi.fn(),
  fetchSimulationTasks: vi.fn(),
  runJob: vi.fn()
}))
```

Update the import:

```javascript
import {
  fetchAdminAlgorithmPipeline,
  fetchAdminLogPreview,
  fetchAdminUsers,
  fetchJobs,
  fetchSimulationTasks,
  runJob
} from '../api/admin.js'
```

Inside `beforeEach()`, add:

```javascript
fetchAdminAlgorithmPipeline.mockResolvedValue({
  log_input: {
    total_logs: 1280,
    action_type_count: 5,
    latest_timestamp: '2026-05-13T15:00:00'
  },
  aggregation: {
    behavior_count: 1280,
    view_count: 620,
    purchase_count: 96,
    region_count: 4
  },
  scoring: {
    weight_rule: 'view=1, click=2, favorite=3, cart=5, purchase=8',
    hot_product_count: 10,
    cold_product_count: 10
  },
  portrait_and_recommendation: {
    real_action_logs: 48,
    cold_start_state: '已进入个性化',
    recommendation_mode: 'personalized'
  },
  anomalies: {
    high_risk_count: 2,
    medium_risk_count: 3,
    window_rule: '最近2天 vs 前3天'
  },
  segmentation: {
    high_value_users: 6,
    potential_users: 18,
    inactive_users: 23
  },
  ai_meta: {
    mode: 'provider',
    provider: 'openai-compatible',
    model: 'deepseek-chat'
  }
})
```

Then expand the `renders admin log preview page with summary and raw logs` test with:

```javascript
expect(wrapper.text()).toContain('算法处理链路')
expect(wrapper.text()).toContain('日志输入')
expect(wrapper.text()).toContain('统计聚合')
expect(wrapper.text()).toContain('加权评分')
expect(wrapper.text()).toContain('用户画像与推荐')
expect(wrapper.text()).toContain('异常检测')
expect(wrapper.text()).toContain('用户分层')
expect(wrapper.text()).toContain('AI解释')
expect(wrapper.text()).toContain('1280')
expect(wrapper.text()).toContain('view=1, click=2, favorite=3, cart=5, purchase=8')
expect(wrapper.text()).toContain('最近2天 vs 前3天')
expect(fetchAdminAlgorithmPipeline).toHaveBeenCalled()
```

- [ ] **Step 3: Run the focused frontend test and verify it fails**

Run:

```bash
npm run test -- src/tests/admin-pages.test.js
```

Expected: FAIL because the page does not yet request or render the pipeline payload.

- [ ] **Step 4: Implement the pipeline module in `AdminLogPreviewPage.vue`**

Update imports:

```javascript
import { fetchAdminAlgorithmPipeline, fetchAdminLogPreview } from '../../api/admin.js'
```

Extend local state:

```javascript
const pipeline = ref({
  log_input: {
    total_logs: 0,
    action_type_count: 0,
    latest_timestamp: '暂无数据'
  },
  aggregation: {
    behavior_count: 0,
    view_count: 0,
    purchase_count: 0,
    region_count: 0
  },
  scoring: {
    weight_rule: '',
    hot_product_count: 0,
    cold_product_count: 0
  },
  portrait_and_recommendation: {
    real_action_logs: 0,
    cold_start_state: '冷启动',
    recommendation_mode: 'fallback'
  },
  anomalies: {
    high_risk_count: 0,
    medium_risk_count: 0,
    window_rule: ''
  },
  segmentation: {
    high_value_users: 0,
    potential_users: 0,
    inactive_users: 0
  },
  ai_meta: {
    mode: 'fallback',
    provider: 'internal',
    model: 'rule-based-fallback'
  }
})
```

Add a computed node list:

```javascript
const pipelineNodes = computed(() => [
  {
    key: 'log_input',
    title: '日志输入',
    metric: `${pipeline.value.log_input.total_logs} 条`,
    detail: `行为类型 ${pipeline.value.log_input.action_type_count} 种`,
    note: `最近时间：${pipeline.value.log_input.latest_timestamp}`
  },
  {
    key: 'aggregation',
    title: '统计聚合',
    metric: `行为 ${pipeline.value.aggregation.behavior_count}`,
    detail: `浏览 ${pipeline.value.aggregation.view_count} / 成交 ${pipeline.value.aggregation.purchase_count}`,
    note: `活跃地区 ${pipeline.value.aggregation.region_count} 个`
  },
  {
    key: 'scoring',
    title: '加权评分',
    metric: `热销 ${pipeline.value.scoring.hot_product_count} / 冷门 ${pipeline.value.scoring.cold_product_count}`,
    detail: pipeline.value.scoring.weight_rule,
    note: '按行为权重计算热度分'
  },
  {
    key: 'portrait',
    title: '用户画像与推荐',
    metric: `${pipeline.value.portrait_and_recommendation.real_action_logs} 条真实行为`,
    detail: pipeline.value.portrait_and_recommendation.cold_start_state,
    note: `推荐模式：${pipeline.value.portrait_and_recommendation.recommendation_mode}`
  },
  {
    key: 'anomalies',
    title: '异常检测',
    metric: `高风险 ${pipeline.value.anomalies.high_risk_count} / 中风险 ${pipeline.value.anomalies.medium_risk_count}`,
    detail: pipeline.value.anomalies.window_rule,
    note: '时间窗口对比识别异常'
  },
  {
    key: 'segmentation',
    title: '用户分层',
    metric: `高价值 ${pipeline.value.segmentation.high_value_users}`,
    detail: `潜力 ${pipeline.value.segmentation.potential_users} / 待激活 ${pipeline.value.segmentation.inactive_users}`,
    note: '基于频次、金额和最近行为分层'
  },
  {
    key: 'ai_meta',
    title: 'AI解释',
    metric: pipeline.value.ai_meta.mode === 'provider' ? '外部模型' : '内置回退',
    detail: `来源：${pipeline.value.ai_meta.provider}`,
    note: `模型：${pipeline.value.ai_meta.model}`
  }
])
```

Update `loadPreview()`:

```javascript
const [previewPayload, pipelinePayload] = await Promise.all([
  fetchAdminLogPreview(),
  fetchAdminAlgorithmPipeline()
])
payload.value = normalizePayload(previewPayload)
pipeline.value = pipelinePayload || pipeline.value
```

Render the pipeline above the existing `admin-log-preview__grid`:

```vue
<section class="dashboard-panel admin-log-preview__pipeline" :aria-busy="isLoading">
  <div class="dashboard-panel__header">
    <div>
      <p class="section-kicker">ALGORITHM PIPELINE</p>
      <h3>算法处理链路</h3>
      <p>展示系统如何把原始日志转成聚合指标、评分结果、画像、异常、分层与 AI 解释。</p>
    </div>
    <span class="dashboard-panel__badge">动态展示</span>
  </div>

  <div class="admin-log-preview__pipeline-grid">
    <article v-for="node in pipelineNodes" :key="node.key" class="admin-log-preview__pipeline-node">
      <p class="section-kicker">{{ node.title }}</p>
      <strong>{{ node.metric }}</strong>
      <p>{{ node.detail }}</p>
      <span>{{ node.note }}</span>
    </article>
  </div>
</section>
```

- [ ] **Step 5: Run the focused frontend test and verify it passes**

Run:

```bash
npm run test -- src/tests/admin-pages.test.js
```

Expected: PASS

- [ ] **Step 6: Commit the admin pipeline UI**

```bash
git add frontend/src/api/admin.js frontend/src/views/admin/AdminLogPreviewPage.vue frontend/src/tests/admin-pages.test.js
git commit -m "feat: add admin algorithm pipeline display"
```

### Task 3: Run regression for admin pages and final verification

**Files:**
- Test: `backend/tests/test_admin.py`
- Test: `frontend/src/tests/admin-pages.test.js`

- [ ] **Step 1: Run the backend admin suite**

Run:

```bash
python -m pytest tests/test_admin.py -q
```

Expected: PASS

- [ ] **Step 2: Run the frontend admin pages suite**

Run:

```bash
npm run test -- src/tests/admin-pages.test.js
```

Expected: PASS

- [ ] **Step 3: Run frontend full suite**

Run:

```bash
npm run test
```

Expected: PASS

- [ ] **Step 4: Perform final display review**

Verify these points against the rendered code and tests:

```text
1. Admin log preview page still shows raw logs and generation controls.
2. The algorithm pipeline appears above the raw log table.
3. Each node shows both an algorithm/rule label and a live metric.
4. The pipeline values come from the new backend endpoint, not hard-coded numbers.
5. The page now visually supports the defense narrative: log input -> processing -> result.
```

Record the result in the handoff summary.

- [ ] **Step 5: Commit the regression-verified final state**

```bash
git add backend/app/routes/admin.py backend/tests/test_admin.py frontend/src/api/admin.js frontend/src/views/admin/AdminLogPreviewPage.vue frontend/src/tests/admin-pages.test.js
git commit -m "feat: visualize admin algorithm processing pipeline"
```
