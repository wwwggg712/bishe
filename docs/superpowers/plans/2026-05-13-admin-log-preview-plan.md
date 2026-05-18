# Admin Log Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an admin-only raw log preview page that proves where analysis data comes from and lets the user inspect recent simulated behavior logs.

**Architecture:** Add one backend admin endpoint that summarizes the in-memory simulated logs and returns recent raw records. Add one frontend admin page, route, navigation item, and API wrapper that render the proof-oriented preview using existing admin panel styles.

**Tech Stack:** Flask, Flask-JWT-Extended, Vue 3, Vue Router, Vitest, Pytest

---

### Task 1: Add failing backend test for admin log preview

**Files:**
- Modify: `backend/tests/test_admin.py`
- Read: `backend/app/routes/admin.py`

- [ ] **Step 1: Write the failing test**

```python
def test_admin_log_preview_returns_recent_logs_and_summary(client, admin_headers, seeded_logs):
    response = client.get("/api/admin/logs/preview", headers=admin_headers)
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["summary"]["total_logs"] >= 1
    assert "recent_logs" in payload
    assert payload["recent_logs"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_admin.py -q`
Expected: FAIL with `404 NOT FOUND`

- [ ] **Step 3: Write minimal implementation**

```python
@bp.get("/logs/preview")
@jwt_required()
def logs_preview():
    unauthorized = _ensure_admin()
    if unauthorized is not None:
        return unauthorized

    return jsonify({"summary": {}, "recent_logs": []})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_admin.py -q`
Expected: PASS

---

### Task 2: Add failing frontend tests for route and page rendering

**Files:**
- Modify: `frontend/src/tests/router.test.js`
- Modify: `frontend/src/tests/admin-pages.test.js`
- Read: `frontend/src/router/index.js`

- [ ] **Step 1: Write the failing route test**

```javascript
it('registers the admin log preview page under the admin route', () => {
  const appRoute = routes.find((route) => route.path === '/')
  const logRoute = appRoute.children.find((route) => route.name === 'admin-log-preview')

  expect(logRoute.path).toBe('admin/logs')
  expect(logRoute.meta.roles).toEqual(['admin'])
})
```

- [ ] **Step 2: Write the failing page test**

```javascript
it('renders admin log preview page with summary and raw logs', async () => {
  const wrapper = mount(AdminLogPreviewPage)
  await flushPromises()

  expect(wrapper.text()).toContain('原始日志预览')
  expect(wrapper.text()).toContain('当前日志总量')
  expect(wrapper.text()).toContain('最近生成日志')
})
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `npm run test -- src/tests/router.test.js src/tests/admin-pages.test.js`
Expected: FAIL because route, API wrapper, and page do not exist

- [ ] **Step 4: Write minimal implementation**

```javascript
export async function fetchAdminLogPreview() {
  const response = await http.get('/api/admin/logs/preview')
  return response.data
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `npm run test -- src/tests/router.test.js src/tests/admin-pages.test.js`
Expected: PASS

---

### Task 3: Complete backend preview payload

**Files:**
- Modify: `backend/app/routes/admin.py`
- Modify: `backend/app/services/simulation_service.py`
- Test: `backend/tests/test_admin.py`

- [ ] **Step 1: Expand summary fields in the test**

```python
assert payload["summary"]["action_type_count"] >= 1
assert payload["summary"]["latest_timestamp"]
assert "sample_generated_count" in payload["summary"]
assert "generation_note" in payload
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_admin.py -q`
Expected: FAIL because fields are missing

- [ ] **Step 3: Implement minimal summary builder**

```python
summary = {
    "total_logs": len(logs),
    "latest_timestamp": logs[-1]["timestamp"] if logs else "暂无数据",
    "sample_generated_count": min(20, len(logs)),
    "action_type_count": len({log["action_type"] for log in logs}),
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_admin.py -q`
Expected: PASS

---

### Task 4: Complete frontend admin log preview page

**Files:**
- Create: `frontend/src/views/admin/AdminLogPreviewPage.vue`
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/layouts/AppLayout.vue`
- Modify: `frontend/src/api/admin.js`
- Modify: `frontend/src/tests/admin-pages.test.js`
- Modify: `frontend/src/tests/router.test.js`

- [ ] **Step 1: Expand page test with expected proof-oriented sections**

```javascript
expect(wrapper.text()).toContain('日志生成规则说明')
expect(wrapper.text()).toContain('分析结果依赖关系')
expect(wrapper.text()).toContain('立即生成一批')
expect(wrapper.text()).toContain('刷新日志')
expect(wrapper.text()).toContain('浏览')
expect(wrapper.text()).toContain('轻量跑鞋')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm run test -- src/tests/router.test.js src/tests/admin-pages.test.js`
Expected: FAIL because the page is incomplete

- [ ] **Step 3: Implement the page**

```vue
<template>
  <section class="admin-page">
    <header class="admin-page__header">
      <div>
        <p class="section-kicker">RAW LOG PREVIEW</p>
        <h2>原始日志预览</h2>
      </div>
      <div class="admin-page__actions">
        <button class="ghost-button" type="button">刷新日志</button>
        <button class="primary-button" type="button">立即生成一批</button>
      </div>
    </header>
  </section>
</template>
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm run test -- src/tests/router.test.js src/tests/admin-pages.test.js`
Expected: PASS

---

### Task 5: Verify feature and regressions

**Files:**
- Test: `backend/tests/test_admin.py`
- Test: `frontend/src/tests/router.test.js`
- Test: `frontend/src/tests/admin-pages.test.js`

- [ ] **Step 1: Run backend focused tests**

Run: `python -m pytest backend/tests/test_admin.py -q`
Expected: PASS

- [ ] **Step 2: Run frontend focused tests**

Run: `npm run test -- src/tests/router.test.js src/tests/admin-pages.test.js`
Expected: PASS

- [ ] **Step 3: Run broader verification**

Run:

```bash
cd backend && python -m pytest -q
cd frontend && npm run test
```

Expected:

- Backend suite passes
- Frontend suite passes
