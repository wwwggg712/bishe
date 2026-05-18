# Defense Polish Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve defense readiness by adding merchant anchor navigation, surfacing the 2000-log bulk action in admin tasks, expanding demo products/categories, and upgrading AI reports to provider-or-fallback mode with explicit UI status.

**Architecture:** Keep the existing routes and page structure, but polish the surface and data depth. The frontend gets a merchant in-page directory and clearer admin/AI status display; the backend keeps `/api/llm/report` stable while adding provider mode and richer seed data; all risky AI calls fall back to the current internal summary path.

**Tech Stack:** Flask, Flask-JWT-Extended, Vue 3, Vitest, Pytest

---

### Task 1: Add failing frontend tests for merchant sidebar anchor navigation

**Files:**
- Create: `frontend/src/tests/app-layout.test.js`
- Test: `frontend/src/layouts/AppLayout.vue`

- [ ] **Step 1: Write the failing merchant navigation test**

```javascript
import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import AppLayout from '../layouts/AppLayout.vue'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push
  })
}))

vi.mock('../stores/auth', () => ({
  useAuthStore: () => ({
    role: 'merchant',
    user: { nickname: 'Merchant Demo', username: 'merchant_demo' },
    clearSession: vi.fn()
  })
}))

describe('AppLayout', () => {
  it('renders merchant in-page anchor navigation items', () => {
    const wrapper = mount(AppLayout, {
      global: {
        stubs: {
          RouterView: true,
          RouterLink: {
            props: ['to'],
            template: '<a :href="typeof to === `string` ? to : `${to.path}${to.hash || ``}`"><slot /></a>'
          }
        }
      }
    })

    const text = wrapper.text()
    expect(text).toContain('经营总览')
    expect(text).toContain('核心业务')
    expect(text).toContain('辅助分析')
    expect(text).toContain('详细分析')
    expect(text).not.toContain('前后端分离的演示工作台壳子')
  })
})
```

- [ ] **Step 2: Run the layout test to verify it fails**

Run: `npm run test -- src/tests/app-layout.test.js`

Expected: FAIL because merchant navigation still only renders `商家看板` and the sidebar subtitle has not been polished.

### Task 2: Implement merchant sidebar anchor navigation

**Files:**
- Modify: `frontend/src/layouts/AppLayout.vue`
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
- Test: `frontend/src/tests/app-layout.test.js`

- [ ] **Step 1: Replace the merchant sidebar nav items with anchor targets**

```javascript
if (role === 'merchant') {
  return [
    { label: '经营总览', to: { path: '/merchant/dashboard', hash: '#merchant-overview' } },
    { label: '核心业务', to: { path: '/merchant/dashboard', hash: '#merchant-core' } },
    { label: '辅助分析', to: { path: '/merchant/dashboard', hash: '#merchant-analysis' } },
    { label: '详细分析', to: { path: '/merchant/dashboard', hash: '#merchant-detail' } }
  ]
}
```

- [ ] **Step 2: Polish the sidebar subtitle so it sounds like a product, not a shell**

```vue
<p class="app-shell__subtitle">多角色联动的电商经营分析与决策工作台</p>
```

- [ ] **Step 3: Add matching section ids to the merchant dashboard**

```vue
<section id="merchant-overview" class="merchant-dashboard__hero">
```

```vue
<section id="merchant-core" class="merchant-dashboard__layer">
```

```vue
<section id="merchant-analysis" class="merchant-dashboard__layer">
```

```vue
<section id="merchant-detail" class="merchant-dashboard__layer">
```

- [ ] **Step 4: Run the layout test and verify it passes**

Run: `npm run test -- src/tests/app-layout.test.js`

Expected: PASS

### Task 3: Add failing frontend tests for the admin 2000-log shortcut

**Files:**
- Modify: `frontend/src/tests/admin-pages.test.js`

- [ ] **Step 1: Extend the simulation mock to assert bulk generation is used from the tasks page**

```javascript
vi.mock('../api/simulation.js', () => ({
  startSimulationTask: vi.fn(),
  stopSimulationTask: vi.fn(),
  generateSimulationBulk: vi.fn()
}))
```

- [ ] **Step 2: Add a failing test for the admin shortcut button**

```javascript
it('renders and triggers the 2000-log shortcut from the admin task page', async () => {
  generateSimulationBulk.mockResolvedValue({ generated_count: 2000 })

  const wrapper = mount(AdminTasksPage)
  await flushPromises()

  expect(wrapper.text()).toContain('快速生成 2000 条')

  await wrapper.find('button[data-testid="admin-generate-bulk"]').trigger('click')
  await flushPromises()

  expect(generateSimulationBulk).toHaveBeenCalled()
})
```

- [ ] **Step 3: Run the admin pages test to verify it fails**

Run: `npm run test -- src/tests/admin-pages.test.js`

Expected: FAIL because the task page does not yet render or wire the bulk shortcut button.

### Task 4: Implement the admin 2000-log shortcut

**Files:**
- Modify: `frontend/src/views/admin/AdminTasksPage.vue`
- Modify: `frontend/src/tests/admin-pages.test.js`
- Test: `frontend/src/tests/admin-pages.test.js`

- [ ] **Step 1: Import the bulk simulation action**

```javascript
import { generateSimulationBulk, startSimulationTask, stopSimulationTask } from '../../api/simulation.js'
```

- [ ] **Step 2: Add local status feedback for bulk generation**

```javascript
const actionMessage = ref('')
```

```javascript
async function handleGenerateBulk() {
  simulationAction.value = 'bulk'
  errorMessage.value = ''
  actionMessage.value = ''
  try {
    const response = await generateSimulationBulk()
    actionMessage.value = `已快速生成 ${response.generated_count || 0} 条日志。`
    await Promise.all([loadJobs(), loadSimulationTasks()])
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '批量日志生成失败，请稍后重试。'
  } finally {
    simulationAction.value = ''
  }
}
```

- [ ] **Step 3: Render the shortcut button in the simulation control area**

```vue
<button
  class="primary-button"
  type="button"
  data-testid="admin-generate-bulk"
  :disabled="simulationAction === 'bulk'"
  @click="handleGenerateBulk"
>
  {{ simulationAction === 'bulk' ? '生成中...' : '快速生成 2000 条' }}
</button>
```

- [ ] **Step 4: Render the success message below the task header**

```vue
<p v-else-if="actionMessage" class="admin-action-message">{{ actionMessage }}</p>
```

- [ ] **Step 5: Run the admin pages test and verify it passes**

Run: `npm run test -- src/tests/admin-pages.test.js`

Expected: PASS

### Task 5: Add failing backend tests for expanded demo catalog

**Files:**
- Modify: `backend/tests/test_simulation.py`

- [ ] **Step 1: Add a failing seed-data richness test**

```python
def test_seed_demo_data_creates_richer_catalog(app):
    from app.models.product import Product
    from app.utils.seed_data import seed_demo_data

    with app.app_context():
      seed_demo_data()
      products = Product.query.all()
      categories = {product.category for product in products}

      assert len(products) >= 24
      assert len(categories) >= 8
```

- [ ] **Step 2: Run the focused simulation test and verify it fails**

Run: `python -m pytest tests/test_simulation.py -k "richer_catalog" -q`

Expected: FAIL because the seed catalog still only contains 4 products and 4 categories.

### Task 6: Expand demo products and categories

**Files:**
- Modify: `backend/app/utils/seed_data.py`
- Test: `backend/tests/test_simulation.py`

- [ ] **Step 1: Expand the demo catalog to at least 24 products across 8 categories**

Update `DEMO_PRODUCTS` so it includes at least these categories:

```python
"运动鞋"
"运动服饰"
"智能设备"
"健身器材"
"户外装备"
"营养补给"
"居家运动"
"配件周边"
```

Each category should contain around 3 products with varied names, prices, brands, and stock.

- [ ] **Step 2: Keep the single-merchant ownership model**

Do not create more merchants. Continue assigning all seeded products to `merchant_demo` so the current merchant demo account still sees the full catalog.

- [ ] **Step 3: Run the focused catalog test and verify it passes**

Run: `python -m pytest tests/test_simulation.py -k "richer_catalog" -q`

Expected: PASS

### Task 7: Add failing backend tests for provider/fallback LLM modes

**Files:**
- Modify: `backend/tests/test_llm_report.py`

- [ ] **Step 1: Add a failing provider-mode test**

```python
def test_llm_report_returns_provider_mode_when_external_model_is_available(
    client, merchant_headers, monkeypatch
):
    from app.routes.llm import llm_service

    monkeypatch.setattr(llm_service, "_provider_config", lambda: {
        "provider": "openai-compatible",
        "model": "deepseek-chat",
        "api_key": "demo-key",
        "base_url": "https://example.com/v1/chat/completions",
    })
    monkeypatch.setattr(
        llm_service,
        "_call_provider",
        lambda payload, config: {
            "summary": "这是外部模型返回的经营分析。",
            "mode": "provider",
            "provider": config["provider"],
            "model": config["model"],
        },
    )

    response = client.post(
        "/api/llm/report",
        headers=merchant_headers,
        json={"scene": "merchant", "product_name": "轻量跑鞋"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["mode"] == "provider"
    assert payload["provider"] == "openai-compatible"
    assert payload["model"] == "deepseek-chat"
```

- [ ] **Step 2: Add a failing fallback test for missing config**

```python
def test_llm_report_returns_fallback_mode_when_provider_config_is_missing(
    client, merchant_headers, monkeypatch
):
    from app.routes.llm import llm_service

    monkeypatch.setattr(llm_service, "_provider_config", lambda: None)

    response = client.post(
        "/api/llm/report",
        headers=merchant_headers,
        json={"scene": "merchant", "product_name": "轻量跑鞋"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["mode"] == "fallback"
    assert payload["provider"] == "internal"
    assert payload["model"] == "rule-based-fallback"
```

- [ ] **Step 3: Add a failing fallback test for provider failure**

```python
def test_llm_report_falls_back_when_provider_call_raises(
    client, merchant_headers, monkeypatch
):
    from app.routes.llm import llm_service

    monkeypatch.setattr(llm_service, "_provider_config", lambda: {
        "provider": "openai-compatible",
        "model": "deepseek-chat",
        "api_key": "demo-key",
        "base_url": "https://example.com/v1/chat/completions",
    })

    def raise_error(payload, config):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(llm_service, "_call_provider", raise_error)

    response = client.post(
        "/api/llm/report",
        headers=merchant_headers,
        json={"scene": "merchant", "product_name": "轻量跑鞋"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["mode"] == "fallback"
    assert payload["provider"] == "internal"
```

- [ ] **Step 4: Run the focused LLM tests and verify they fail**

Run: `python -m pytest tests/test_llm_report.py -k "provider_mode or provider_config_is_missing or provider_call_raises" -q`

Expected: FAIL because the current service always returns fallback and has no provider metadata.

### Task 8: Implement provider-or-fallback LLM service

**Files:**
- Modify: `backend/app/services/llm_service.py`
- Test: `backend/tests/test_llm_report.py`

- [ ] **Step 1: Add provider config discovery**

```python
import os
```

```python
def _provider_config(self):
    provider = os.getenv("LLM_PROVIDER", "").strip()
    api_key = os.getenv("LLM_API_KEY", "").strip()
    base_url = os.getenv("LLM_BASE_URL", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()

    if not provider or not api_key or not base_url or not model:
        return None

    return {
        "provider": provider,
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
    }
```

- [ ] **Step 2: Add a minimal external provider call helper**

Use Python stdlib to avoid adding a new dependency:

```python
import json
from urllib import request as urllib_request
```

```python
def _call_provider(self, payload, config):
    prompt = self._build_prompt(payload)
    request_body = json.dumps(
        {
            "model": config["model"],
            "messages": [
                {"role": "system", "content": "你是电商经营分析助手，请结合结构化结果给出简洁专业的中文总结。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        }
    ).encode("utf-8")

    req = urllib_request.Request(
        config["base_url"],
        data=request_body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}",
        },
        method="POST",
    )

    with urllib_request.urlopen(req, timeout=20) as response:
        payload_json = json.loads(response.read().decode("utf-8"))

    summary = payload_json["choices"][0]["message"]["content"].strip()
    return {
        "summary": summary,
        "mode": "provider",
        "provider": config["provider"],
        "model": config["model"],
    }
```

- [ ] **Step 3: Update `build_report()` to prefer provider and fall back on failure**

```python
def build_report(self, payload):
    config = self._provider_config()
    if config is not None:
        try:
            return self._call_provider(payload, config)
        except Exception:
            pass

    return {
        "summary": self._build_fallback_summary(payload),
        "mode": "fallback",
        "provider": "internal",
        "model": "rule-based-fallback",
    }
```

- [ ] **Step 4: Add a prompt builder shared by both merchant and customer scenes**

```python
def _build_prompt(self, payload):
    scene = payload.get("scene", "general")
    return json.dumps({"scene": scene, "payload": payload}, ensure_ascii=False)
```

This prompt builder can stay simple; do not over-engineer templating in this task.

- [ ] **Step 5: Run the focused LLM tests and verify they pass**

Run: `python -m pytest tests/test_llm_report.py -k "provider_mode or provider_config_is_missing or provider_call_raises" -q`

Expected: PASS

### Task 9: Add failing frontend tests for explicit AI mode metadata

**Files:**
- Modify: `frontend/src/tests/merchant-dashboard.test.js`
- Modify: `frontend/src/tests/customer-home.test.js`

- [ ] **Step 1: Update the merchant AI mock payload to include provider metadata**

```javascript
fetchMerchantAiAnalysis.mockResolvedValue({
  summary: '这是外部模型返回的经营分析。',
  mode: 'provider',
  provider: 'openai-compatible',
  model: 'deepseek-chat'
})
```

- [ ] **Step 2: Add a failing merchant metadata assertion**

```javascript
expect(wrapper.text()).toContain('当前模式：外部模型')
expect(wrapper.text()).toContain('模型来源：openai-compatible')
expect(wrapper.text()).toContain('模型名称：deepseek-chat')
```

- [ ] **Step 3: Update the customer AI mock payload to include fallback metadata and add assertions**

```javascript
fetchCustomerAiExplanation.mockResolvedValue({
  summary: '这是回退模式生成的推荐解释。',
  mode: 'fallback',
  provider: 'internal',
  model: 'rule-based-fallback'
})
```

```javascript
expect(wrapper.text()).toContain('当前模式：内置回退')
expect(wrapper.text()).toContain('模型来源：internal')
```

- [ ] **Step 4: Run focused frontend AI tests and verify they fail**

Run: `npm run test -- src/tests/merchant-dashboard.test.js src/tests/customer-home.test.js`

Expected: FAIL because the current pages do not render mode/provider/model metadata.

### Task 10: Render AI mode metadata in merchant and customer pages

**Files:**
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
- Modify: `frontend/src/views/customer/CustomerHome.vue`
- Test: `frontend/src/tests/merchant-dashboard.test.js`
- Test: `frontend/src/tests/customer-home.test.js`

- [ ] **Step 1: Add local AI meta state to the merchant page**

```javascript
const merchantAiMeta = ref({
  mode: '',
  provider: '',
  model: ''
})
```

```javascript
merchantAiMeta.value = {
  mode: payload.mode || 'fallback',
  provider: payload.provider || 'internal',
  model: payload.model || 'rule-based-fallback'
}
```

- [ ] **Step 2: Render merchant AI status lines**

```vue
<div v-if="merchantAiMeta.mode" class="dashboard-panel__meta-list">
  <span>当前模式：{{ merchantAiMeta.mode === 'provider' ? '外部模型' : '内置回退' }}</span>
  <span>模型来源：{{ merchantAiMeta.provider }}</span>
  <span>模型名称：{{ merchantAiMeta.model }}</span>
</div>
```

- [ ] **Step 3: Add local AI meta state to the customer page**

```javascript
const customerAiMeta = ref({
  mode: '',
  provider: '',
  model: ''
})
```

```javascript
customerAiMeta.value = {
  mode: payload.mode || 'fallback',
  provider: payload.provider || 'internal',
  model: payload.model || 'rule-based-fallback'
}
```

- [ ] **Step 4: Render customer AI status lines**

```vue
<div v-if="customerAiMeta.mode" class="dashboard-panel__meta-list">
  <span>当前模式：{{ customerAiMeta.mode === 'provider' ? '外部模型' : '内置回退' }}</span>
  <span>模型来源：{{ customerAiMeta.provider }}</span>
  <span>模型名称：{{ customerAiMeta.model }}</span>
</div>
```

- [ ] **Step 5: Run the focused merchant and customer tests and verify they pass**

Run: `npm run test -- src/tests/merchant-dashboard.test.js src/tests/customer-home.test.js`

Expected: PASS

### Task 11: Run regression verification

**Files:**
- Test: `frontend/src/tests/app-layout.test.js`
- Test: `frontend/src/tests/admin-pages.test.js`
- Test: `frontend/src/tests/merchant-dashboard.test.js`
- Test: `frontend/src/tests/customer-home.test.js`
- Test: `backend/tests/test_simulation.py`
- Test: `backend/tests/test_llm_report.py`
- Test: `backend/tests`
- Test: `frontend/src/tests`

- [ ] **Step 1: Run focused frontend layout/admin tests**

Run: `npm run test -- src/tests/app-layout.test.js src/tests/admin-pages.test.js`

Expected: PASS

- [ ] **Step 2: Run focused frontend AI/dashboard tests**

Run: `npm run test -- src/tests/merchant-dashboard.test.js src/tests/customer-home.test.js`

Expected: PASS

- [ ] **Step 3: Run focused backend simulation and LLM tests**

Run: `python -m pytest tests/test_simulation.py tests/test_llm_report.py -q`

Expected: PASS

- [ ] **Step 4: Run backend full suite**

Run: `python -m pytest -q`

Expected: PASS

- [ ] **Step 5: Run frontend full suite**

Run: `npm run test`

Expected: PASS
