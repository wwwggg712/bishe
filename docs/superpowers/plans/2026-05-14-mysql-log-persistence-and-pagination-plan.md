# MySQL 日志持久化与分页预览 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让行为日志真正持久化到 MySQL，并让管理员日志预览页可以分页查看完整日志，而不是只显示最近 20 条样例。

**Architecture:** 后端新增 `BehaviorLog` 模型承接模拟日志和用户真实行为，运行环境通过 `DATABASE_URL` 切换到 MySQL，测试环境继续使用 SQLite。管理员日志预览接口保留原路径但升级为分页返回结构，前端只做必要的数据消费改造，不在本轮重排页面布局。

**Tech Stack:** Flask, Flask-SQLAlchemy, Flask-JWT-Extended, SQLAlchemy, PyMySQL, Pytest, Vue 3, Axios, Vitest

---

## File Structure

- Modify: `backend/requirements.txt`
  - 增加 MySQL 驱动依赖
- Modify: `backend/app/models/__init__.py`
  - 导出新日志模型
- Create: `backend/app/models/behavior_log.py`
  - 定义行为日志数据库模型
- Modify: `backend/app/services/simulation_service.py`
  - 模拟日志和真实行为改为入库
- Modify: `backend/app/routes/admin.py`
  - 日志预览改为分页查询，算法链路改为读数据库
- Modify: `backend/app/services/analytics_service.py`
  - 商家分析优先消费数据库日志对象转换结果
- Modify: `backend/app/services/prediction_service.py`
  - 画像、趋势、异常优先消费数据库日志对象转换结果
- Modify: `backend/app/services/recommendation_service.py`
  - 推荐读取数据库日志，继续只认 `customer_page`
- Modify: `backend/app/routes/recommendation.py`
  - 用户真实行为写入数据库日志
- Modify: `backend/tests/conftest.py`
  - 测试环境建表时纳入新日志模型
- Modify: `backend/tests/test_admin.py`
  - 增加日志分页与算法链路数据库来源测试
- Modify: `backend/tests/test_intelligence.py`
  - 增加模拟日志入库和真实行为入库测试
- Modify: `frontend/src/api/admin.js`
  - 日志预览请求支持分页参数
- Modify: `frontend/src/views/admin/AdminLogPreviewPage.vue`
  - 消费分页结构并展示页码、总条数
- Modify: `frontend/src/tests/admin-pages.test.js`
  - 更新日志预览页分页断言

### Task 1: 建立行为日志模型并接入 MySQL 配置

**Files:**
- Create: `backend/app/models/behavior_log.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/requirements.txt`
- Modify: `backend/tests/conftest.py`
- Test: `backend/tests/test_admin.py`

- [ ] **Step 1: 先写一个失败测试，锁定新模型会被建表**

在 `backend/tests/test_admin.py` 末尾追加：

```python
from app.extensions import db


def test_behavior_log_table_is_created(app):
    with app.app_context():
        inspector = db.inspect(db.engine)
        assert "behavior_logs" in inspector.get_table_names()
```

- [ ] **Step 2: 运行聚焦测试，确认先红灯**

Run:

```bash
cd backend
python -m pytest tests/test_admin.py -k "behavior_log_table_is_created" -q
```

Expected: FAIL，因为当前还没有 `BehaviorLog` 模型和对应表。

- [ ] **Step 3: 新建行为日志模型**

创建 `backend/app/models/behavior_log.py`：

```python
from datetime import datetime

from ..extensions import db


class BehaviorLog(db.Model):
    __tablename__ = "behavior_logs"

    id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    merchant_id = db.Column(db.Integer, nullable=False, index=True)
    product_id = db.Column(db.Integer, nullable=False, index=True)
    product_name = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(64), nullable=False, index=True)
    brand = db.Column(db.String(64), nullable=True)
    price = db.Column(db.Float, nullable=False)
    action_type = db.Column(db.String(32), nullable=False, index=True)
    region = db.Column(db.String(32), nullable=True, index=True)
    device_type = db.Column(db.String(32), nullable=True)
    source_channel = db.Column(db.String(32), nullable=False, index=True)
    session_id = db.Column(db.String(64), nullable=True)
    stay_duration = db.Column(db.Integer, nullable=True)
    is_new_user = db.Column(db.Boolean, default=False, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "log_id": self.log_id,
            "user_id": self.user_id,
            "merchant_id": self.merchant_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "category": self.category,
            "brand": self.brand,
            "price": float(self.price),
            "action_type": self.action_type,
            "region": self.region,
            "device_type": self.device_type,
            "source_channel": self.source_channel,
            "session_id": self.session_id,
            "stay_duration": self.stay_duration,
            "is_new_user": self.is_new_user,
            "timestamp": self.timestamp.isoformat(),
        }
```

- [ ] **Step 4: 导出模型并补充 MySQL 依赖**

在 `backend/app/models/__init__.py` 中确保导出：

```python
from .behavior_log import BehaviorLog
from .daily_metric import DailyMetric
from .merchant_action import MerchantAction
from .product import Product
from .task import Task
from .user import User
```

在 `backend/requirements.txt` 追加：

```text
PyMySQL==1.1.1
```

- [ ] **Step 5: 确保测试建表包含新模型**

`backend/tests/conftest.py` 不需要改 fixture 结构，但需要在文件顶部显式导入新模型：

```python
from app.models.behavior_log import BehaviorLog  # noqa: F401
from app.models.user import User
```

这样 `db.create_all()` 能包含新表。

- [ ] **Step 6: 运行聚焦测试，确认转绿**

Run:

```bash
cd backend
python -m pytest tests/test_admin.py -k "behavior_log_table_is_created" -q
```

Expected: PASS

- [ ] **Step 7: 做一次 Python 语法检查**

Run:

```bash
cd backend
python -m py_compile app/models/behavior_log.py app/models/__init__.py tests/conftest.py
```

Expected: PASS，无输出。

- [ ] **Step 8: 提交模型和依赖改动**

```bash
git add backend/app/models/behavior_log.py backend/app/models/__init__.py backend/requirements.txt backend/tests/conftest.py backend/tests/test_admin.py
git commit -m "feat: add persistent behavior log model"
```

### Task 2: 让模拟日志和真实行为真正入库

**Files:**
- Modify: `backend/app/services/simulation_service.py`
- Modify: `backend/app/routes/recommendation.py`
- Modify: `backend/tests/test_intelligence.py`
- Test: `backend/tests/test_intelligence.py`

- [ ] **Step 1: 先写两个后端失败测试，锁住“模拟日志入库”和“真实行为入库”**

在 `backend/tests/test_intelligence.py` 末尾追加：

```python
from app.models.behavior_log import BehaviorLog


def test_generate_bulk_logs_persist_to_behavior_log_table(client, admin_headers, seeded_demo_data):
    response = client.post("/api/simulation/generate/bulk", headers=admin_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["generated_count"] == 2000
    assert BehaviorLog.query.count() >= 2000


def test_customer_recommendation_action_persists_to_behavior_log_table(
    client, customer_headers, seeded_demo_data
):
    response = client.post(
        "/api/recommendations/actions",
        json={"product_id": 1, "action_type": "favorite"},
        headers=customer_headers,
    )

    assert response.status_code == 200
    log = BehaviorLog.query.filter_by(
        user_id=3,
        product_id=1,
        action_type="favorite",
        source_channel="customer_page",
    ).order_by(BehaviorLog.id.desc()).first()
    assert log is not None
```

- [ ] **Step 2: 运行聚焦测试，确认先红灯**

Run:

```bash
cd backend
python -m pytest tests/test_intelligence.py -k "persist_to_behavior_log_table" -q
```

Expected: FAIL，因为当前日志仍主要写入内存。

- [ ] **Step 3: 给模拟服务增加数据库日志写入能力**

在 `backend/app/services/simulation_service.py` 中引入模型并增加两个辅助方法：

```python
from ..models.behavior_log import BehaviorLog
```

```python
    def _to_behavior_log_model(self, log):
        return BehaviorLog(
            log_id=log["log_id"],
            user_id=log["user_id"],
            merchant_id=log["merchant_id"],
            product_id=log["product_id"],
            product_name=log["product_name"],
            category=log["category"],
            brand=log["brand"],
            price=log["price"],
            action_type=log["action_type"],
            region=log["region"],
            device_type=log["device_type"],
            source_channel=log["source_channel"],
            session_id=log["session_id"],
            stay_duration=log["stay_duration"],
            is_new_user=log["is_new_user"],
            timestamp=datetime.fromisoformat(log["timestamp"]),
        )

    def _save_logs(self, logs):
        simulation_memory_store.save(logs)
        db.session.add_all([self._to_behavior_log_model(log) for log in logs])
        db.session.commit()
```

并把原来的：

```python
simulation_memory_store.save(logs)
return logs
```

替换为：

```python
self._save_logs(logs)
return logs
```

同理把 `record_customer_action()` 末尾的：

```python
simulation_memory_store.save([log])
return log
```

替换为：

```python
self._save_logs([log])
return log
```

- [ ] **Step 4: 运行聚焦测试，确认转绿**

Run:

```bash
cd backend
python -m pytest tests/test_intelligence.py -k "persist_to_behavior_log_table" -q
```

Expected: PASS

- [ ] **Step 5: 跑推荐与模拟链路回归**

Run:

```bash
cd backend
python -m pytest tests/test_intelligence.py -k "recommendation or simulation" -q
```

Expected: PASS，保证现有推荐与模拟任务未被破坏。

- [ ] **Step 6: 提交日志入库改动**

```bash
git add backend/app/services/simulation_service.py backend/app/routes/recommendation.py backend/tests/test_intelligence.py
git commit -m "feat: persist simulation and customer logs to database"
```

### Task 3: 管理员日志预览改为数据库分页接口

**Files:**
- Modify: `backend/app/routes/admin.py`
- Modify: `backend/tests/test_admin.py`
- Modify: `frontend/src/api/admin.js`
- Modify: `frontend/src/views/admin/AdminLogPreviewPage.vue`
- Modify: `frontend/src/tests/admin-pages.test.js`
- Test: `backend/tests/test_admin.py`
- Test: `frontend/src/tests/admin-pages.test.js`

- [ ] **Step 1: 先写后端失败测试，锁住分页结构**

在 `backend/tests/test_admin.py` 新增：

```python
from app.extensions import db
from app.models.behavior_log import BehaviorLog
from datetime import datetime, timedelta


def test_admin_log_preview_returns_paginated_database_logs(client, admin_headers, seeded_demo_data):
    now = datetime.utcnow()
    db.session.add_all(
        [
            BehaviorLog(
                log_id=f"log-{index}",
                user_id=3,
                merchant_id=2,
                product_id=1,
                product_name="轻量跑鞋",
                category="运动鞋",
                brand="Trace",
                price=299,
                action_type="view",
                region="华东",
                device_type="mobile",
                source_channel="search",
                session_id=f"s-{index}",
                stay_duration=30,
                is_new_user=False,
                timestamp=now - timedelta(minutes=index),
            )
            for index in range(35)
        ]
    )
    db.session.commit()

    response = client.get("/api/admin/logs/preview?page=2&page_size=10", headers=admin_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["summary"]["total_logs"] == 35
    assert payload["pagination"]["page"] == 2
    assert payload["pagination"]["page_size"] == 10
    assert payload["pagination"]["total_pages"] == 4
    assert len(payload["logs"]) == 10
```

- [ ] **Step 2: 运行聚焦后端测试，确认先红灯**

Run:

```bash
cd backend
python -m pytest tests/test_admin.py -k "paginated_database_logs" -q
```

Expected: FAIL，因为当前接口仍返回 `recent_logs` 且不支持分页。

- [ ] **Step 3: 实现后端分页接口**

在 `backend/app/routes/admin.py` 中引入：

```python
from ..models.behavior_log import BehaviorLog
```

把 `logs_preview()` 改成如下关键结构：

```python
@bp.get("/logs/preview")
@jwt_required()
def logs_preview():
    unauthorized = _ensure_admin()
    if unauthorized is not None:
        return unauthorized

    page = max(request.args.get("page", default=1, type=int), 1)
    page_size = min(max(request.args.get("page_size", default=20, type=int), 1), 100)

    query = BehaviorLog.query.order_by(BehaviorLog.timestamp.desc(), BehaviorLog.id.desc())
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    items = [item.to_dict() for item in pagination.items]

    action_counter = Counter(
        row.action_type
        for row in db.session.query(BehaviorLog.action_type).all()
    )
    latest_log = BehaviorLog.query.order_by(BehaviorLog.timestamp.desc(), BehaviorLog.id.desc()).first()

    return jsonify(
        {
            "summary": {
                "total_logs": pagination.total,
                "latest_timestamp": latest_log.timestamp.isoformat() if latest_log else "暂无数据",
                "sample_generated_count": len(items),
                "action_type_count": len(action_counter),
            },
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_pages": pagination.pages,
                "total_items": pagination.total,
            },
            "action_breakdown": [
                {"action_type": action_type, "count": count}
                for action_type, count in action_counter.most_common()
            ],
            "generation_note": (
                "日志由系统模拟器与用户真实操作写入数据库，用于热度、事件级经营指标、"
                "简化用户分层和异常分析。"
            ),
            "logs": items,
        }
    )
```

- [ ] **Step 4: 让前端 API 支持分页参数**

把 `frontend/src/api/admin.js` 中的：

```javascript
export async function fetchAdminLogPreview() {
  const response = await http.get('/api/admin/logs/preview')
  return response.data
}
```

改成：

```javascript
export async function fetchAdminLogPreview(params = {}) {
  const response = await http.get('/api/admin/logs/preview', { params })
  return response.data
}
```

- [ ] **Step 5: 让管理员页消费分页结构**

在 `frontend/src/views/admin/AdminLogPreviewPage.vue` 中：

1. 把默认 payload 增加：

```javascript
pagination: {
  page: 1,
  page_size: 20,
  total_pages: 0,
  total_items: 0
},
logs: []
```

2. 把 `recent_logs` 改为 `logs`

3. 在 `loadPreview()` 中改为：

```javascript
async function loadPreview(page = payload.value.pagination.page || 1) {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const [previewPayload, pipelinePayload] = await Promise.all([
      fetchAdminLogPreview({ page, page_size: 20 }),
      fetchAdminAlgorithmPipeline()
    ])
    payload.value = normalizePayload(previewPayload)
    pipeline.value = normalizePipeline(pipelinePayload)
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '日志预览加载失败，请稍后重试。'
  } finally {
    isLoading.value = false
  }
}
```

4. 在表格徽标和表体中把：

```vue
{{ payload.recent_logs.length }} 条预览
```

改为：

```vue
第 {{ payload.pagination.page }} 页 / 共 {{ payload.pagination.total_pages || 1 }} 页
```

表格循环改为：

```vue
<tr v-for="item in payload.logs" :key="item.log_id">
```

5. 在表格下方新增两个分页按钮：

```vue
<div class="admin-log-preview__pager">
  <button
    class="ghost-button"
    type="button"
    :disabled="isLoading || payload.pagination.page <= 1"
    @click="loadPreview(payload.pagination.page - 1)"
  >
    上一页
  </button>
  <span>共 {{ payload.pagination.total_items }} 条日志</span>
  <button
    class="ghost-button"
    type="button"
    :disabled="isLoading || payload.pagination.page >= payload.pagination.total_pages"
    @click="loadPreview(payload.pagination.page + 1)"
  >
    下一页
  </button>
</div>
```

- [ ] **Step 6: 更新前端测试夹具与断言**

把 `frontend/src/tests/admin-pages.test.js` 里的日志 mock 改成：

```javascript
fetchAdminLogPreview.mockResolvedValue({
  summary: {
    total_logs: 1280,
    latest_timestamp: '2026-05-13T15:00:00',
    sample_generated_count: 20,
    action_type_count: 5
  },
  pagination: {
    page: 1,
    page_size: 20,
    total_pages: 64,
    total_items: 1280
  },
  action_breakdown: [
    { action_type: '浏览', count: 620 },
    { action_type: '点击', count: 280 }
  ],
  generation_note: '日志由系统模拟器与用户真实操作写入数据库，用于热度、事件级经营指标、简化用户分层和异常分析。',
  logs: [
    {
      log_id: 'log-1',
      timestamp: '2026-05-13T15:00:00',
      user_id: 3,
      product_name: '轻量跑鞋',
      category: '运动鞋',
      action_type: 'view',
      region: '华东',
      price: 299,
      source_channel: 'search'
    }
  ]
})
```

并新增断言：

```javascript
expect(wrapper.text()).toContain('共 1280 条日志')
expect(wrapper.text()).toContain('第 1 页 / 共 64 页')
expect(wrapper.text()).not.toContain('20 条预览')
```

- [ ] **Step 7: 运行后端与前端聚焦测试，确认转绿**

Run:

```bash
cd backend
python -m pytest tests/test_admin.py -k "paginated_database_logs or behavior_log_table_is_created" -q
```

```bash
cd ..\\frontend
npm run test -- src/tests/admin-pages.test.js
```

Expected: PASS

- [ ] **Step 8: 提交分页预览改动**

```bash
git add backend/app/routes/admin.py backend/tests/test_admin.py frontend/src/api/admin.js frontend/src/views/admin/AdminLogPreviewPage.vue frontend/src/tests/admin-pages.test.js
git commit -m "feat: paginate admin log preview from database"
```

### Task 4: 让推荐、画像、商家分析和算法链路读数据库日志并做回归

**Files:**
- Modify: `backend/app/services/recommendation_service.py`
- Modify: `backend/app/services/prediction_service.py`
- Modify: `backend/app/services/analytics_service.py`
- Modify: `backend/app/routes/admin.py`
- Modify: `backend/tests/test_intelligence.py`
- Modify: `backend/tests/test_admin.py`
- Test: `backend/tests/test_intelligence.py`
- Test: `backend/tests/test_admin.py`

- [ ] **Step 1: 先写失败测试，锁住“算法链路读数据库”和“推荐只认数据库真实行为”**

在 `backend/tests/test_admin.py` 新增：

```python
def test_admin_algorithm_pipeline_reads_database_logs(client, admin_headers, seeded_demo_data):
    from app.models.behavior_log import BehaviorLog
    from datetime import datetime

    db.session.add(
        BehaviorLog(
            log_id="pipeline-log-1",
            user_id=3,
            merchant_id=2,
            product_id=1,
            product_name="轻量跑鞋",
            category="运动鞋",
            brand="Trace",
            price=299,
            action_type="purchase",
            region="华东",
            device_type="mobile",
            source_channel="customer_page",
            session_id="pipeline-session",
            stay_duration=40,
            is_new_user=False,
            timestamp=datetime.utcnow(),
        )
    )
    db.session.commit()

    response = client.get("/api/admin/algorithm-pipeline", headers=admin_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["log_input"]["total_logs"] >= 1
    assert payload["portrait_and_recommendation"]["real_action_logs"] >= 1
```

在 `backend/tests/test_intelligence.py` 新增：

```python
def test_customer_recommendations_read_database_customer_page_logs(
    client, customer_headers, seeded_demo_data
):
    from datetime import datetime
    from app.models.behavior_log import BehaviorLog

    db.session.add(
        BehaviorLog(
            log_id="db-rec-log-1",
            user_id=3,
            merchant_id=2,
            product_id=1,
            product_name="轻量跑鞋",
            category="运动鞋",
            brand="Trace",
            price=299,
            action_type="favorite",
            region="华东",
            device_type="mobile",
            source_channel="customer_page",
            session_id="db-rec-session",
            stay_duration=25,
            is_new_user=False,
            timestamp=datetime.utcnow(),
        )
    )
    db.session.commit()

    response = client.get("/api/recommendations/me", headers=customer_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["mode"] in {"personalized", "fallback"}
```

- [ ] **Step 2: 运行聚焦测试，确认先红灯**

Run:

```bash
cd backend
python -m pytest tests/test_admin.py tests/test_intelligence.py -k "reads_database" -q
```

Expected: FAIL，因为当前分析链路还主要吃内存日志。

- [ ] **Step 3: 为服务层增加数据库日志转换入口**

在三个服务文件中统一增加辅助方法模式，例如在 `backend/app/services/analytics_service.py`：

```python
    def _normalize_logs(self, logs):
        normalized = []
        for log in logs:
            if hasattr(log, "to_dict"):
                normalized.append(log.to_dict())
            else:
                normalized.append(log)
        return normalized
```

并在公共入口先做：

```python
logs = self._normalize_logs(logs)
```

同样思路加到：

- `backend/app/services/prediction_service.py`
- `backend/app/services/recommendation_service.py`

这样服务层既能吃旧 dict，也能吃 `BehaviorLog` 模型对象。

- [ ] **Step 4: 让推荐和算法链路优先读数据库**

在 `backend/app/routes/admin.py` 中把：

```python
logs = simulation_memory_store.logs
```

替换为：

```python
logs = BehaviorLog.query.order_by(BehaviorLog.timestamp.asc(), BehaviorLog.id.asc()).all()
```

在 `backend/app/routes/recommendation.py` 中把：

```python
payload = recommendation_service.recommend_for_customer(
    user_id=user_id,
    logs=simulation_memory_store.logs,
    products=products,
)
```

替换为：

```python
logs = BehaviorLog.query.order_by(BehaviorLog.timestamp.asc(), BehaviorLog.id.asc()).all()
payload = recommendation_service.recommend_for_customer(
    user_id=user_id,
    logs=logs,
    products=products,
)
```

同时把画像、异常、趋势相关入口按同样思路逐步替换为数据库查询结果。

- [ ] **Step 5: 运行聚焦测试，确认转绿**

Run:

```bash
cd backend
python -m pytest tests/test_admin.py tests/test_intelligence.py -k "reads_database" -q
```

Expected: PASS

- [ ] **Step 6: 做一轮后端全量关键回归**

Run:

```bash
cd backend
python -m pytest tests/test_admin.py tests/test_intelligence.py -q
```

Expected: PASS

- [ ] **Step 7: 提交数据库日志主读链改动**

```bash
git add backend/app/services/recommendation_service.py backend/app/services/prediction_service.py backend/app/services/analytics_service.py backend/app/routes/admin.py backend/tests/test_admin.py backend/tests/test_intelligence.py
git commit -m "refactor: read analytics and recommendation logs from database"
```

### Task 5: 做最终回归和环境说明更新

**Files:**
- Modify: `README.md`
- Test: `backend/tests/test_admin.py`
- Test: `backend/tests/test_intelligence.py`
- Test: `frontend/src/tests/admin-pages.test.js`
- Review: `backend/app/models/behavior_log.py`
- Review: `backend/app/services/simulation_service.py`
- Review: `backend/app/routes/admin.py`
- Review: `frontend/src/views/admin/AdminLogPreviewPage.vue`

- [ ] **Step 1: 更新 README 的数据库说明**

在 `README.md` 环境变量部分把：

```md
| `DATABASE_URL` | `sqlite:///local.db` | 数据库连接；默认在 `backend/instance/local.db` 生成本地库 |
```

改成：

```md
| `DATABASE_URL` | `sqlite:///local.db` | 数据库连接；本地演示推荐显式配置为 MySQL，如 `mysql+pymysql://root:password@127.0.0.1:3306/ecommerce_analysis` |
```

并在说明中补一段：

```md
- 当前系统支持使用 MySQL 持久化用户、商品、任务与行为日志。
- 自动化测试默认仍使用 SQLite，以保证本地回归快速稳定。
```

- [ ] **Step 2: 跑后端关键回归**

Run:

```bash
cd backend
python -m pytest tests/test_admin.py tests/test_intelligence.py -q
```

Expected: PASS

- [ ] **Step 3: 跑管理员页前端回归**

Run:

```bash
cd ..\\frontend
npm run test -- src/tests/admin-pages.test.js
```

Expected: PASS

- [ ] **Step 4: 跑前端全量测试**

Run:

```bash
cd ..\\frontend
npm run test
```

Expected: PASS

- [ ] **Step 5: 检查最近改动文件诊断**

Use diagnostics on:

```text
d:\MyProjects\bishe-finnal\backend\app\models\behavior_log.py
d:\MyProjects\bishe-finnal\backend\app\services\simulation_service.py
d:\MyProjects\bishe-finnal\backend\app\routes\admin.py
d:\MyProjects\bishe-finnal\frontend\src\views\admin\AdminLogPreviewPage.vue
```

Expected: 无新增语法或类型错误。

- [ ] **Step 6: 做人工复查**

核对以下结果：

```text
1. 应用运行时可通过 DATABASE_URL 切到 MySQL。
2. 快速生成 2000 条后，日志能真实入库。
3. 管理员日志预览页默认每页 20 条，但可翻页查看完整日志。
4. 推荐、画像、商家分析和管理员算法链路不再只依赖内存日志。
5. 测试环境仍可使用 SQLite 跑回归。
```

- [ ] **Step 7: 提交最终状态**

```bash
git add backend/requirements.txt backend/app/models/behavior_log.py backend/app/models/__init__.py backend/app/services/simulation_service.py backend/app/routes/admin.py backend/app/services/analytics_service.py backend/app/services/prediction_service.py backend/app/services/recommendation_service.py backend/app/routes/recommendation.py backend/tests/conftest.py backend/tests/test_admin.py backend/tests/test_intelligence.py frontend/src/api/admin.js frontend/src/views/admin/AdminLogPreviewPage.vue frontend/src/tests/admin-pages.test.js README.md
git commit -m "feat: persist behavior logs in mysql with paginated admin preview"
```
