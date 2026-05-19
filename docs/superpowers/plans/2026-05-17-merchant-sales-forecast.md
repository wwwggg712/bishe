# 商家爆火商品销量预测（30天）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在商家端新增“爆火商品未来30天销量预测”，自动选Top1商品，返回未来30天折线与总销量区间，并在前端经营总览展示且具备兜底输出。

**Architecture:** 后端新增商家预测接口（店铺口径）与服务层：按天聚合 purchase → 自动选品 → 轻量可解释预测（趋势+衰减+波动区间）→ 返回结构化结果；前端新增 API 与预测卡片，复用现有 ECharts 折线组件展示“历史 vs 预测”。

**Tech Stack:** Flask + SQLAlchemy, Vue 3 + Vite, ECharts, Pytest, Vitest

---

## File Structure

**Backend**
- Create: `backend/app/routes/merchant_prediction.py`
- Create: `backend/app/services/merchant_prediction_service.py`
- Modify: `backend/app/__init__.py`（注册 blueprint）
- Test: `backend/tests/test_merchant_prediction_sales_forecast.py`

**Frontend**
- Create: `frontend/src/api/merchantPrediction.js`
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`（经营总览插入预测卡）
- Modify: `frontend/src/tests/merchant-dashboard.test.js`（mock 新接口并断言渲染）
- Modify: `frontend/src/styles/theme.css`（预测卡与折线图容器样式，仅补必要样式）

---

### Task 1: 后端—写失败测试（无数据兜底）

**Files:**
- Create: `backend/tests/test_merchant_prediction_sales_forecast.py`

- [ ] **Step 1: 新增测试文件，先写“无 purchase 数据时返回兜底结构”的 failing test**

```python
from datetime import datetime

from app.extensions import db
from app.models.behavior_log import BehaviorLog


def _persist_log(merchant_id, product_id, product_name, category, brand, action_type, created_at):
    entity = BehaviorLog(
        log_id=f"forecast-{merchant_id}-{product_id}-{action_type}-{created_at.timestamp()}",
        user_id=123,
        merchant_id=merchant_id,
        product_id=product_id,
        product_name=product_name,
        category=category,
        brand=brand,
        price=99.0,
        action_type=action_type,
        region="华东",
        device_type="ios",
        source_channel="customer_page",
        session_id="sess",
        stay_duration=10,
        is_new_user=False,
        timestamp=created_at,
        created_at=created_at,
    )
    db.session.add(entity)
    db.session.commit()


def test_sales_forecast_returns_fallback_when_no_purchase_data(client, merchant_headers, seeded_demo_data):
    response = client.get("/api/merchant/prediction/sales-forecast?days=30", headers=merchant_headers)
    assert response.status_code == 200
    payload = response.get_json()

    assert payload["product"] is None
    assert payload["history"] == []
    assert payload["forecast"] == []
    assert payload["forecast_total"] == {"value": 0, "lower": 0, "upper": 0}
    assert payload["confidence"] == "low"
    assert payload["explain"]
```

- [ ] **Step 2: 运行测试确认失败（因为接口不存在）**

Run:
```bash
cd d:\MyProjects\bishe-finnal\backend
$env:PYTHONPATH='.'; pytest -q tests/test_merchant_prediction_sales_forecast.py::test_sales_forecast_returns_fallback_when_no_purchase_data
```

Expected:
- FAIL，HTTP 404 或导入错误（接口未实现）

---

### Task 2: 后端—实现预测接口与服务（最小可用）

**Files:**
- Create: `backend/app/routes/merchant_prediction.py`
- Create: `backend/app/services/merchant_prediction_service.py`
- Modify: `backend/app/__init__.py`

- [ ] **Step 1: 新建服务层骨架 `MerchantPredictionService`（只实现兜底返回）**

Create `backend/app/services/merchant_prediction_service.py`:
```python
from datetime import date


class MerchantPredictionService:
    def build_sales_forecast(self, merchant_id: int, days: int = 30):
        return {
            "product": None,
            "history": [],
            "forecast": [],
            "forecast_total": {"value": 0, "lower": 0, "upper": 0},
            "confidence": "low",
            "explain": ["暂无可预测商品：近7/30天购买数据不足"],
        }
```

- [ ] **Step 2: 新增商家预测路由（校验 merchant 角色）**

Create `backend/app/routes/merchant_prediction.py`:
```python
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from ..services.merchant_prediction_service import MerchantPredictionService


bp = Blueprint("merchant_prediction", __name__, url_prefix="/api/merchant/prediction")
service = MerchantPredictionService()


def _ensure_merchant():
    if get_jwt().get("role") != "merchant":
        return jsonify({"message": "仅商家可查看销量预测"}), 403
    return None


@bp.get("/sales-forecast")
@jwt_required()
def sales_forecast():
    unauthorized = _ensure_merchant()
    if unauthorized is not None:
        return unauthorized

    merchant_id = int(get_jwt_identity())
    days = int(request.args.get("days", 30))
    payload = service.build_sales_forecast(merchant_id=merchant_id, days=days)
    return jsonify(payload)
```

- [ ] **Step 3: 注册 blueprint**

Modify `backend/app/__init__.py`：
```python
from .routes.merchant_prediction import bp as merchant_prediction_bp
...
app.register_blueprint(merchant_prediction_bp)
```

- [ ] **Step 4: 运行单测，确认 Task 1 通过**

Run:
```bash
cd d:\MyProjects\bishe-finnal\backend
$env:PYTHONPATH='.'; pytest -q tests/test_merchant_prediction_sales_forecast.py::test_sales_forecast_returns_fallback_when_no_purchase_data
```

Expected:
- PASS

---

### Task 3: 后端—写有 purchase 数据的失败测试（自动选Top1 + 30天历史与预测）

**Files:**
- Modify: `backend/tests/test_merchant_prediction_sales_forecast.py`

- [ ] **Step 1: 增加“有 purchase 数据”测试用例**

Append:
```python
from datetime import datetime, timedelta


def test_sales_forecast_selects_top_product_and_returns_series(client, merchant_headers, seeded_demo_data):
    merchant_id = 2
    base = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)

    for idx in range(7):
        day = base - timedelta(days=idx)
        for _ in range(3):
            _persist_log(merchant_id, 101, "爆火商品A", "户外装备", "CloudStep", "purchase", day)
        for _ in range(1):
            _persist_log(merchant_id, 102, "普通商品B", "户外装备", "CloudStep", "purchase", day)

    response = client.get("/api/merchant/prediction/sales-forecast?days=30", headers=merchant_headers)
    assert response.status_code == 200
    payload = response.get_json()

    assert payload["product"]["product_id"] == 101
    assert len(payload["history"]) == 30
    assert len(payload["forecast"]) == 30
    assert payload["forecast_total"]["value"] >= 0
    assert payload["forecast_total"]["lower"] <= payload["forecast_total"]["value"] <= payload["forecast_total"]["upper"]
    assert payload["explain"]
```

- [ ] **Step 2: 运行测试确认失败（服务还未实现真实逻辑）**

Run:
```bash
cd d:\MyProjects\bishe-finnal\backend
$env:PYTHONPATH='.'; pytest -q tests/test_merchant_prediction_sales_forecast.py::test_sales_forecast_selects_top_product_and_returns_series
```

Expected:
- FAIL（product 为 null 或 history/forecast 为空）

---

### Task 4: 后端—实现自动选Top1 + 聚合 purchase + 轻量预测

**Files:**
- Modify: `backend/app/services/merchant_prediction_service.py`

- [ ] **Step 1: 实现按天 purchase 聚合（SQL group by date）**

Replace `MerchantPredictionService` with:
```python
from datetime import date, datetime, timedelta
from statistics import pstdev

from sqlalchemy import func

from ..extensions import db
from ..models.behavior_log import BehaviorLog
from ..models.product import Product


class MerchantPredictionService:
    def _date_range(self, end_date: date, days: int):
        start = end_date - timedelta(days=days - 1)
        items = []
        cursor = start
        while cursor <= end_date:
            items.append(cursor)
            cursor += timedelta(days=1)
        return items

    def _daily_purchase_map(self, merchant_id: int, product_id: int, days: int):
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days - 1)
        date_expr = func.date(BehaviorLog.created_at)
        rows = (
            db.session.query(date_expr, func.count(BehaviorLog.id))
            .filter(
                BehaviorLog.merchant_id == merchant_id,
                BehaviorLog.product_id == product_id,
                BehaviorLog.action_type == "purchase",
                BehaviorLog.created_at >= start_date,
            )
            .group_by(date_expr)
            .all()
        )
        mapping = {str(day): int(count) for day, count in rows}
        days_list = self._date_range(end_date, days)
        return [{"date": d.isoformat(), "value": int(mapping.get(d.isoformat(), 0))} for d in days_list]

    def _select_top_product_id(self, merchant_id: int):
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=6)
        date_expr = func.date(BehaviorLog.created_at)
        rows = (
            db.session.query(BehaviorLog.product_id, func.count(BehaviorLog.id))
            .filter(
                BehaviorLog.merchant_id == merchant_id,
                BehaviorLog.action_type == "purchase",
                BehaviorLog.created_at >= start_date,
            )
            .group_by(BehaviorLog.product_id)
            .order_by(func.count(BehaviorLog.id).desc())
            .all()
        )
        if rows:
            return int(rows[0][0])
        start_date = end_date - timedelta(days=29)
        rows = (
            db.session.query(BehaviorLog.product_id, func.count(BehaviorLog.id))
            .filter(
                BehaviorLog.merchant_id == merchant_id,
                BehaviorLog.action_type == "purchase",
                BehaviorLog.created_at >= start_date,
            )
            .group_by(BehaviorLog.product_id)
            .order_by(func.count(BehaviorLog.id).desc())
            .all()
        )
        if rows:
            return int(rows[0][0])
        return 0

    def _build_forecast(self, history_values, days: int):
        if not history_values:
            return ([0] * days, {"value": 0, "lower": 0, "upper": 0}, "low", ["历史购买数据不足，预测结果为0"])

        last7 = history_values[-7:] if len(history_values) >= 7 else history_values
        avg7 = sum(last7) / max(len(last7), 1)
        avg30 = sum(history_values) / max(len(history_values), 1)
        trend_ratio = 1.0
        if avg30 > 0:
            trend_ratio = avg7 / avg30
        trend_ratio = max(0.7, min(trend_ratio, 1.4))

        base = max(avg7, avg30) * trend_ratio
        base = max(base, 0.0)

        sigma = float(pstdev(history_values)) if len(history_values) >= 2 else 0.0
        forecast = []
        lower = []
        upper = []
        for idx in range(days):
            decay = 1.0 - (min(idx, days - 1) / max(days - 1, 1)) * 0.35
            value = max(base * decay, 0.0)
            value_int = int(round(value))
            forecast.append(value_int)
            lower.append(max(int(round(value - sigma)), 0))
            upper.append(max(int(round(value + sigma)), 0))

        total = sum(forecast)
        total_lower = sum(lower)
        total_upper = sum(upper)

        confidence = "low" if sum(history_values) < 10 else "medium"
        explain = [
            f"近7天日均销量 {avg7:.1f}",
            f"近30天对比趋势系数 {trend_ratio:.2f}",
            "加入爆火回落衰减，避免预测过于乐观",
        ]
        return (forecast, {"value": total, "lower": total_lower, "upper": total_upper}, confidence, explain)

    def build_sales_forecast(self, merchant_id: int, days: int = 30):
        days = int(days)
        days = max(7, min(days, 60))

        top_product_id = self._select_top_product_id(merchant_id=merchant_id)
        if not top_product_id:
            return {
                "product": None,
                "history": [],
                "forecast": [],
                "forecast_total": {"value": 0, "lower": 0, "upper": 0},
                "confidence": "low",
                "explain": ["暂无可预测商品：近7/30天购买数据不足"],
            }

        product = Product.query.filter_by(id=top_product_id, merchant_id=merchant_id).first()
        if product is None:
            return {
                "product": None,
                "history": [],
                "forecast": [],
                "forecast_total": {"value": 0, "lower": 0, "upper": 0},
                "confidence": "low",
                "explain": ["暂无可预测商品：商品不存在或无权限"],
            }

        history = self._daily_purchase_map(merchant_id=merchant_id, product_id=top_product_id, days=30)
        history_values = [item["value"] for item in history]
        forecast_values, total_info, confidence, explain = self._build_forecast(history_values, days=days)

        start_date = datetime.utcnow().date() + timedelta(days=1)
        forecast_days = self._date_range(start_date + timedelta(days=days - 1), days)
        forecast = [{"date": d.isoformat(), "value": int(forecast_values[idx])} for idx, d in enumerate(forecast_days)]

        return {
            "product": {
                "product_id": product.id,
                "name": product.name,
                "brand": product.brand,
                "category": product.category,
                "price": float(product.price or 0),
                "image_url": product.image_url,
            },
            "history": history,
            "forecast": forecast,
            "forecast_total": total_info,
            "confidence": confidence,
            "explain": explain,
        }
```

- [ ] **Step 2: 运行 Task 3 测试，确认通过**

Run:
```bash
cd d:\MyProjects\bishe-finnal\backend
$env:PYTHONPATH='.'; pytest -q tests/test_merchant_prediction_sales_forecast.py
```

Expected:
- PASS

---

### Task 5: 前端—新增 API 并写失败测试（预测卡渲染）

**Files:**
- Create: `frontend/src/api/merchantPrediction.js`
- Modify: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: 新增前端 API**

Create `frontend/src/api/merchantPrediction.js`:
```js
import http from './http'

export async function fetchMerchantSalesForecast(params = {}) {
  const response = await http.get('/api/merchant/prediction/sales-forecast', { params })
  return response.data
}
```

- [ ] **Step 2: 在 merchant-dashboard 测试中 mock 新 API（先写 failing 断言）**

Modify `frontend/src/tests/merchant-dashboard.test.js`：
1) 增加 mock：
```js
vi.mock('../api/merchantPrediction.js', () => ({
  fetchMerchantSalesForecast: vi.fn()
}))
```
2) 在 imports 增加：
```js
import { fetchMerchantSalesForecast } from '../api/merchantPrediction.js'
```
3) 在 `beforeEach` 中设置默认返回：
```js
fetchMerchantSalesForecast.mockResolvedValue({
  product: { product_id: 1, name: '爆火商品A', brand: '云步', category: '户外装备', price: 99, image_url: '' },
  history: Array.from({ length: 30 }, (_, idx) => ({ date: `2026-04-${String(idx + 1).padStart(2, '0')}`, value: 1 })),
  forecast: Array.from({ length: 30 }, (_, idx) => ({ date: `2026-05-${String(idx + 1).padStart(2, '0')}`, value: 2 })),
  forecast_total: { value: 60, lower: 40, upper: 80 },
  confidence: 'medium',
  explain: ['近7天日均销量 1.0']
})
```
4) 增加断言（预期先失败，因为页面还没渲染预测卡）：
```js
expect(wrapper.text()).toContain('爆火商品销量预测')
expect(fetchMerchantSalesForecast).toHaveBeenCalled()
```

- [ ] **Step 3: 运行前端测试确认失败**

Run:
```bash
cd d:\MyProjects\bishe-finnal\frontend
npm test
```

Expected:
- FAIL（页面未展示预测卡或未调用 API）

---

### Task 6: 前端—经营总览插入预测卡（复用 TrendLineChart）

**Files:**
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
- Modify: `frontend/src/styles/theme.css`

- [ ] **Step 1: 在 MerchantDashboard 引入预测 API 与 TrendLineChart**

在 `MerchantDashboard.vue` 顶部 imports 增加：
```js
import { fetchMerchantSalesForecast } from '../../api/merchantPrediction.js'
import TrendLineChart from '../../components/charts/TrendLineChart.vue'
```

- [ ] **Step 2: 增加状态与加载逻辑（overview 页面 onMounted 触发）**

新增 refs：
```js
const salesForecast = ref(null)
const isLoadingForecast = ref(false)
```

在 `loadDashboard()` 成功段落后追加（不阻塞主加载）：
```js
isLoadingForecast.value = true
try {
  salesForecast.value = await fetchMerchantSalesForecast({ days: 30 })
} catch (error) {
  salesForecast.value = {
    product: null,
    history: [],
    forecast: [],
    forecast_total: { value: 0, lower: 0, upper: 0 },
    confidence: 'low',
    explain: ['销量预测生成失败，请稍后重试']
  }
} finally {
  isLoadingForecast.value = false
}
```

- [ ] **Step 3: 组装“历史+预测”折线数据（60天横轴 + null 断开）**

新增 computed：
```js
const forecastChart = computed(() => {
  const payload = salesForecast.value
  if (!payload || !payload.history || !payload.forecast) {
    return { days: [], series: [] }
  }

  const historyDays = payload.history.map((item) => item.date)
  const forecastDays = payload.forecast.map((item) => item.date)
  const days = [...historyDays, ...forecastDays]

  const historyData = payload.history.map((item) => item.value).concat(Array.from({ length: payload.forecast.length }, () => null))
  const forecastData = Array.from({ length: payload.history.length }, () => null).concat(payload.forecast.map((item) => item.value))

  return {
    days,
    series: [
      { name: '历史销量', data: historyData },
      { name: '预测销量', data: forecastData }
    ]
  }
})
```

- [ ] **Step 4: 在 overview 模块插入预测卡片 UI**

在 overview 模板中（建议放在 `.merchant-dashboard__summary` 后、图表区域前）插入一个 `dashboard-panel`：
```vue
<section class="merchant-dashboard__layer" :aria-busy="isLoading">
  <div class="merchant-dashboard__layer-grid">
    <article class="dashboard-panel merchant-forecast-panel">
      <div class="dashboard-panel__header">
        <div>
          <p class="section-kicker">SALES FORECAST</p>
          <h3>爆火商品销量预测（30天）</h3>
          <p>自动选取近7天购买最多的商品，输出未来30天折线与总销量区间。</p>
        </div>
        <span v-if="salesForecast?.forecast_total" class="dashboard-panel__badge">
          预测总销量 {{ salesForecast.forecast_total.value }}
        </span>
      </div>

      <div v-if="salesForecast?.product" class="merchant-forecast-panel__product">
        <div class="merchant-product-thumb">
          <img
            v-if="salesForecast.product.image_url"
            class="merchant-product-thumb__image"
            :src="salesForecast.product.image_url"
            :alt="salesForecast.product.name"
            loading="lazy"
          />
          <div v-else class="merchant-product-thumb__placeholder">
            {{ String(salesForecast.product.name || '').trim().slice(0, 1) }}
          </div>
        </div>
        <div class="merchant-forecast-panel__product-meta">
          <strong>{{ salesForecast.product.name }}</strong>
          <span>{{ salesForecast.product.category }} / {{ salesForecast.product.brand }}</span>
          <span>区间 {{ salesForecast.forecast_total.lower }} - {{ salesForecast.forecast_total.upper }}</span>
        </div>
      </div>

      <p v-if="isLoadingForecast" class="empty-state">预测生成中...</p>
      <template v-else>
        <TrendLineChart v-if="forecastChart.days.length" :days="forecastChart.days" :series="forecastChart.series" />
        <ul v-if="salesForecast?.explain?.length" class="strategy-list">
          <li v-for="item in salesForecast.explain" :key="item" class="strategy-list__item">
            <p>{{ item }}</p>
          </li>
        </ul>
        <p v-else class="empty-state">暂无可用预测说明。</p>
      </template>
    </article>
  </div>
</section>
```

- [ ] **Step 5: 追加必要样式（不破坏全局风格）**

Modify `frontend/src/styles/theme.css`：
```css
.merchant-forecast-panel__product {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.merchant-forecast-panel__product-meta {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.merchant-forecast-panel__product-meta strong {
  font-size: 1.05rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.merchant-forecast-panel__product-meta span {
  color: #64748b;
  font-size: 0.92rem;
}
```

- [ ] **Step 6: 运行前端测试确认通过**

Run:
```bash
cd d:\MyProjects\bishe-finnal\frontend
npm test
```

Expected:
- PASS（42/42 或新增后更多测试通过）

---

### Task 7: 全量验证与回归

**Files:**
- (none)

- [ ] **Step 1: 跑后端全量测试**

Run:
```bash
cd d:\MyProjects\bishe-finnal\backend
$env:PYTHONPATH='.'; pytest -q
```

Expected:
- PASS

- [ ] **Step 2: 本地联调预览**

Run (frontend):
```bash
cd d:\MyProjects\bishe-finnal\frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

验收要点：
- 经营总览出现“爆火商品销量预测（30天）”卡片
- 有 purchase 数据时：折线有两条线（历史/预测），右上角有预测总销量，区间与解释项可见
- 无 purchase 数据时：展示兜底文案与 0 区间，不空白不报错

