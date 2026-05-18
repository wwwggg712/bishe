# 任务管理集中、日志清理与 DeepSeek AI 分析 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将日志生成/清理入口集中到任务管理页，日志预览页只用于查看；用户端与商家端接入 DeepSeek（OpenAI 兼容）做 AI 分析，并让失败原因可见。

**Architecture:** 后端继续基于 Flask + SQLAlchemy + MySQL 的 `behavior_logs` 作为统一日志源。管理端新增“保留最新 N 条”的清理接口。LLM 调用沿用 `/api/llm/report`，但从“静默回退”改为“成功/失败显式返回”。前端把生成/清理按钮挪到任务管理页，预览页仅保留分页查看。

**Tech Stack:** Flask, Flask-SQLAlchemy, MySQL, Vue 3, Axios, Vitest, Pytest

---

## File Structure

**Backend**
- Modify: `backend/app/services/llm_service.py`
- Modify: `backend/app/routes/admin.py`
- Create/Modify: `backend/tests/test_llm.py`（若不存在则创建）
- Modify: `backend/tests/test_admin.py`

**Frontend**
- Modify: `frontend/src/views/admin/AdminLogPreviewPage.vue`
- Modify: `frontend/src/views/admin/AdminTasksPage.vue`
- Modify: `frontend/src/api/admin.js`
- Modify: `frontend/src/tests/admin-pages.test.js`

---

### Task 1: 新增日志清理接口（保留最新 N 条）

**Files:**
- Modify: `backend/app/routes/admin.py`
- Modify: `backend/tests/test_admin.py`

- [ ] **Step 1: 写一个失败测试锁定“保留最新 N 条”行为**

在 `backend/tests/test_admin.py` 末尾追加：

```python
def test_admin_can_cleanup_logs_keep_last(client, admin_headers):
    from app.models.behavior_log import BehaviorLog

    client.post("/api/simulation/generate-bulk", headers=admin_headers)
    assert BehaviorLog.query.count() == 2000

    response = client.post(
        "/api/admin/logs/cleanup",
        headers=admin_headers,
        json={"keep_last": 500},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["kept_count"] == 500
    assert payload["deleted_count"] == 1500
    assert BehaviorLog.query.count() == 500
```

- [ ] **Step 2: 运行聚焦测试，确认先红灯**

Run:

```bash
cd backend
python -m pytest tests/test_admin.py -k "admin_can_cleanup_logs_keep_last" -q
```

Expected: FAIL，因接口不存在。

- [ ] **Step 3: 实现 `POST /api/admin/logs/cleanup`**

在 `backend/app/routes/admin.py` 中新增：

1. 仅管理员可访问（复用 `_ensure_admin()`）
2. 读取 `keep_last`（范围建议 `1..500000`）
3. 查询最新 N 条的 `id` 子查询（按 `timestamp desc, id desc`）
4. 删除其余 `BehaviorLog`（返回删除条数）

- [ ] **Step 4: 运行聚焦测试，确认转绿**

Run:

```bash
cd backend
python -m pytest tests/test_admin.py -k "admin_can_cleanup_logs_keep_last" -q
```

Expected: PASS

- [ ] **Step 5: 运行后端全量测试**

Run:

```bash
cd backend
python -m pytest -q
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/routes/admin.py backend/tests/test_admin.py
git commit -m "feat: add admin log cleanup keep-last endpoint"
```

---

### Task 2: LLM 调用失败显式返回（支持 DeepSeek OpenAI 兼容）

**Files:**
- Modify: `backend/app/services/llm_service.py`
- Create/Modify: `backend/tests/test_llm.py`

- [ ] **Step 1: 写一个失败测试，锁定“provider 配了但失败时返回 mode=error”**

创建或修改 `backend/tests/test_llm.py`：

```python
def test_llm_report_returns_error_mode_when_provider_fails(client, admin_headers, monkeypatch):
    from urllib import error as urllib_error
    from urllib import request as urllib_request

    def _raise(*args, **kwargs):
        raise urllib_error.URLError("boom")

    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.deepseek.com/v1/chat/completions")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setattr(urllib_request, "urlopen", _raise)

    response = client.post("/api/llm/report", headers=admin_headers, json={"scene": "merchant"})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["mode"] == "error"
    assert payload["provider"] == "deepseek"
    assert payload["model"] == "deepseek-chat"
    assert payload["base_url"]
    assert payload["error_message"]
```

- [ ] **Step 2: 运行聚焦测试，确认先红灯**

Run:

```bash
cd backend
python -m pytest tests/test_llm.py -q
```

Expected: FAIL（当前代码会静默回退为 fallback）。

- [ ] **Step 3: 实现错误透传**

修改 `backend/app/services/llm_service.py`：

1. `build_report()`：若 provider 配置齐全但调用失败，返回：
   - `mode="error"`
   - `error_message=str(error)`
   - `provider/model/base_url`（不要包含 key）
2. 保持未配置 provider 时仍为 fallback（internal）

- [ ] **Step 4: 运行聚焦测试，确认转绿**

Run:

```bash
cd backend
python -m pytest tests/test_llm.py -q
```

Expected: PASS

- [ ] **Step 5: 运行后端全量测试**

Run:

```bash
cd backend
python -m pytest -q
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/llm_service.py backend/tests/test_llm.py
git commit -m "feat: surface deepseek llm errors instead of silent fallback"
```

---

### Task 3: 前端把“生成/清理”迁移到任务管理页，日志预览页只看

**Files:**
- Modify: `frontend/src/views/admin/AdminLogPreviewPage.vue`
- Modify: `frontend/src/views/admin/AdminTasksPage.vue`
- Modify: `frontend/src/api/admin.js`
- Modify: `frontend/src/tests/admin-pages.test.js`

- [ ] **Step 1: 更新前端测试（先红灯）**

在 `frontend/src/tests/admin-pages.test.js`：

1. `AdminLogPreviewPage` 用例：断言不再包含“立即生成一批/快速生成 2000 条”
2. `AdminTasksPage` 用例：断言包含“保留最新 N 条”输入与按钮

Run:

```bash
cd frontend
npm run test --silent
```

Expected: FAIL

- [ ] **Step 2: 修改 AdminLogPreviewPage.vue**

1. 移除日志生成按钮与相关状态文案
2. 保留：刷新、分页查看、每页条数选择

- [ ] **Step 3: 修改 AdminTasksPage.vue**

1. 保留已有“生成 2000/立即生成”入口
2. 新增“保留最新 N 条”输入与执行按钮
3. 调用 `POST /api/admin/logs/cleanup`
4. 成功后显示 `deleted_count/kept_count`

- [ ] **Step 4: 修改 admin.js API**

新增：

```js
export async function cleanupAdminLogs(keepLast) {
  const response = await http.post('/api/admin/logs/cleanup', { keep_last: keepLast })
  return response.data
}
```

- [ ] **Step 5: 运行前端测试，确认转绿**

Run:

```bash
cd frontend
npm run test --silent
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/admin/AdminLogPreviewPage.vue frontend/src/views/admin/AdminTasksPage.vue frontend/src/api/admin.js frontend/src/tests/admin-pages.test.js
git commit -m "feat: move log generate/cleanup into admin tasks page"
```

---

### Task 4: 推荐理由升级为证据型（不改推荐主逻辑）

**Files:**
- Modify: `backend/app/services/recommendation_service.py`
- Test: `backend/tests/test_intelligence.py`

- [ ] **Step 1: 写一个失败测试锁定“理由包含证据字段”**

在 `backend/tests/test_intelligence.py` 中找到 `test_customer_recommendations_use_customer_page_logs_for_personalization`，在断言理由包含类目名基础上增加：

```python
assert "热度" in payload["items"][0]["reason"]
```

- [ ] **Step 2: 运行聚焦测试，确认先红灯**

Run:

```bash
cd backend
python -m pytest tests/test_intelligence.py -k "customer_recommendations_use_customer_page_logs_for_personalization" -q
```

Expected: FAIL

- [ ] **Step 3: 实现证据型 reason**

修改 `backend/app/services/recommendation_service.py`：

1. fallback reason 增加该商品热度分（hot score）
2. personalized reason 增加：
   - 用户偏好类目得分（category score）
   - 候选商品热度分（hot score）
3. 保持原返回结构字段不变

- [ ] **Step 4: 运行聚焦测试与全量测试**

Run:

```bash
cd backend
python -m pytest tests/test_intelligence.py -k "customer_recommendations_use_customer_page_logs_for_personalization" -q
python -m pytest -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/recommendation_service.py backend/tests/test_intelligence.py
git commit -m "feat: enrich recommendation reasons with evidence scores"
```

---

## Final Verification

- [ ] 后端：`cd backend && python -m pytest -q`
- [ ] 前端：`cd frontend && npm run test --silent`
- [ ] 手动验证：管理端任务页生成 2000 条 → 日志预览分页可查看 → 任务页“保留最新 N 条”后预览总数下降

