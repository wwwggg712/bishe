# Bulk Log Generate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a one-click admin action that quickly generates 2000 simulated behavior logs for答辩演示.

**Architecture:** Keep the existing small-batch generation path unchanged and add one dedicated bulk-generation path with a fixed batch size of 2000. Expose it through the simulation API and wire a second button into the admin raw log preview page so admins can quickly raise the log volume before demos.

**Tech Stack:** Flask, Vue 3, Vitest, Pytest

---

### Task 1: Add failing tests for fixed bulk generation

**Files:**
- Modify: `backend/tests/test_simulation.py`
- Modify: `frontend/src/tests/admin-pages.test.js`

- [ ] **Step 1: Write the failing backend test**

```python
def test_generate_bulk_returns_2000_logs(client, admin_headers):
    response = client.post("/api/simulation/generate-bulk", headers=admin_headers)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["generated_count"] == 2000
```

- [ ] **Step 2: Write the failing frontend test**

```javascript
expect(wrapper.text()).toContain('快速生成 2000 条')
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
cd backend && python -m pytest tests/test_simulation.py -q
cd frontend && npm run test -- src/tests/admin-pages.test.js
```

Expected:

- Backend fails with `404 NOT FOUND`
- Frontend fails because button or API wrapper is missing

---

### Task 2: Implement backend bulk generation endpoint

**Files:**
- Modify: `backend/app/services/simulation_service.py`
- Modify: `backend/app/routes/simulation.py`
- Test: `backend/tests/test_simulation.py`

- [ ] **Step 1: Add minimal service method**

```python
def generate_bulk_from_db(self, batch_size=2000):
    return self.generate_once_from_db(batch_size=batch_size)
```

- [ ] **Step 2: Add route**

```python
@bp.post("/generate-bulk")
@jwt_required()
def generate_bulk():
    logs = simulation_service.generate_bulk_from_db(batch_size=2000)
    return jsonify({"generated_count": len(logs), "preview": logs[:5]})
```

- [ ] **Step 3: Run backend test to verify it passes**

Run: `python -m pytest tests/test_simulation.py -q`
Expected: PASS

---

### Task 3: Implement frontend bulk generation button

**Files:**
- Modify: `frontend/src/api/simulation.js`
- Modify: `frontend/src/views/admin/AdminLogPreviewPage.vue`
- Test: `frontend/src/tests/admin-pages.test.js`

- [ ] **Step 1: Add API wrapper**

```javascript
export async function generateSimulationBulk() {
  const response = await http.post('/api/simulation/generate-bulk')
  return response.data
}
```

- [ ] **Step 2: Add button and action handler**

```vue
<button class="primary-button" type="button">
  快速生成 2000 条
</button>
```

- [ ] **Step 3: Run frontend test to verify it passes**

Run: `npm run test -- src/tests/admin-pages.test.js`
Expected: PASS

---

### Task 4: Verify focused and full regressions

**Files:**
- Test: `backend/tests/test_simulation.py`
- Test: `frontend/src/tests/admin-pages.test.js`

- [ ] **Step 1: Run focused tests**

Run:

```bash
cd backend && python -m pytest tests/test_simulation.py -q
cd frontend && npm run test -- src/tests/admin-pages.test.js
```

Expected:

- Focused tests pass

- [ ] **Step 2: Run full suites**

Run:

```bash
cd backend && python -m pytest -q
cd frontend && npm run test
```

Expected:

- Backend suite passes
- Frontend suite passes
