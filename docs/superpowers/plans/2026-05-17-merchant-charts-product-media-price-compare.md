# 商家图表 + 商品图片/价格 + 用户端比价（演示版）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在商家端增加更直观的图表（漏斗+占比饼图+近7天趋势折线图），在用户端商品卡片展示图片与价格，并新增“比价（演示版：抖音/京东/拼多多/得物）”页面与接口。

**Architecture:** 后端新增三类能力：Product 增加 `image_url` 并在 demo 数据中填充；新增商家图表接口（share/trend）基于 `BehaviorLog.created_at` 做聚合；新增比价接口返回确定性“外部平台报价”。前端新增 ECharts 容器组件与两类图表组件，商家仪表盘接入；用户端推荐卡片增强并新增比价页。

**Tech Stack:** Flask + Flask-JWT-Extended + SQLAlchemy，Vue3 + Vite + Vitest，ECharts 5（已在依赖中）

---

## File Structure / Touch Points

**Backend**
- Modify: `backend/app/models/product.py`（新增 `image_url`）
- Modify: `backend/app/utils/seed_data.py`（demo 商品填充 `image_url`）
- Modify: `backend/app/services/recommendation_service.py`（推荐返回补齐 price/brand/image_url）
- Modify: `backend/app/routes/recommendation.py`（必要时优化 products 查询字段）
- Create: `backend/app/routes/merchant_charts.py`（商家图表接口：share/trend）
- Modify: `backend/app/__init__.py`（注册 merchant_charts blueprint）
- Create: `backend/app/routes/price_compare.py`（比价接口）
- Create: `backend/app/services/price_compare_service.py`（演示报价生成与 best/advice）
- Modify: `backend/app/__init__.py`（注册 price_compare blueprint）
- Create: `backend/tests/test_merchant_charts.py`
- Create: `backend/tests/test_price_compare.py`
- Update: `backend/tests/test_intelligence.py` 或相关推荐测试（若断言字段变更）

**Frontend**
- Create: `frontend/src/components/charts/EChartView.vue`（ECharts 容器）
- Create: `frontend/src/components/charts/SharePieChart.vue`（饼图）
- Create: `frontend/src/components/charts/TrendLineChart.vue`（折线图）
- Create: `frontend/src/api/merchantCharts.js`
- Create: `frontend/src/api/priceCompare.js`
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`（接入饼图/折线图数据与渲染）
- Modify: `frontend/src/views/customer/CustomerHome.vue`（推荐卡片展示图/价 & 比价入口）
- Modify: `frontend/src/views/customer/RecommendationView.vue`（推荐卡片展示图/价 & 比价入口）
- Create: `frontend/src/views/customer/PriceCompareView.vue`
- Modify: `frontend/src/router/index.js`（新增路由）
- Modify: `frontend/src/tests/customer-home.test.js`
- Modify: `frontend/src/tests/router.test.js`
- Create: `frontend/src/tests/price-compare.test.js`

---

### Task 1: Add Product.image_url + seed demo images (backend)

**Files:**
- Modify: `backend/app/models/product.py`
- Modify: `backend/app/utils/seed_data.py`
- Test: `backend/tests/test_app_boot.py`（启动覆盖）

- [ ] **Step 1: Write failing test for `image_url` column**

Create `backend/tests/test_product_media.py`:

```python
from app.models.product import Product


def test_product_has_image_url(seeded_demo_data):
    product = Product.query.first()
    assert hasattr(product, "image_url")
    assert product.image_url
```

- [ ] **Step 2: Run the test to verify it fails**

```powershell
$env:PYTHONPATH='.'; pytest -q tests/test_product_media.py::test_product_has_image_url
```

Expected: FAIL (attribute missing).

- [ ] **Step 3: Add `image_url` to Product model**

Modify `backend/app/models/product.py`:

```python
image_url = db.Column(db.String(512), nullable=False, default="")
```

Keep existing fields unchanged.

- [ ] **Step 4: Seed demo data with stable image URLs**

Update `backend/app/utils/seed_data.py` Product creation to include `image_url` using the allowed generator endpoint:

```python
from urllib.parse import quote

def _demo_image_url(product_name, category):
    prompt = quote(f"ecommerce product photo, {product_name}, category {category}, studio lighting, white background, high detail")
    return f"https://coreva-normal.trae.ai/api/ide/v1/text_to_image?prompt={prompt}&image_size=square"
```

Then add:

```python
image_url=_demo_image_url(payload["name"], payload["category"]),
```

- [ ] **Step 5: Run test again**

```powershell
$env:PYTHONPATH='.'; pytest -q tests/test_product_media.py::test_product_has_image_url
```

Expected: PASS.

- [ ] **Step 6: Run full backend tests**

```powershell
$env:PYTHONPATH='.'; pytest -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/product.py backend/app/utils/seed_data.py backend/tests/test_product_media.py
git commit -m "feat(product): add image_url and seed demo images"
```

---

### Task 2: Enrich recommendations with price/brand/image_url (backend + frontend assertions)

**Files:**
- Modify: `backend/app/services/recommendation_service.py`
- Modify: `backend/app/routes/recommendation.py` (if needed)
- Test: `backend/tests/test_intelligence.py` (or create new test)

- [ ] **Step 1: Write failing test asserting recommendation items include `price` and `image_url`**

Create `backend/tests/test_recommendation_enriched.py`:

```python
def test_recommendations_include_price_and_image_url(client, customer_headers, seeded_demo_data):
    response = client.get("/api/recommendations/me", headers=customer_headers)
    assert response.status_code == 200
    payload = response.get_json()
    if not payload["items"]:
        return
    item = payload["items"][0]
    assert "price" in item
    assert "brand" in item
    assert "image_url" in item
```

- [ ] **Step 2: Run it to verify it fails**

```powershell
$env:PYTHONPATH='.'; pytest -q tests/test_recommendation_enriched.py::test_recommendations_include_price_and_image_url
```

Expected: FAIL (missing keys).

- [ ] **Step 3: Implement enrichment**

In `backend/app/services/recommendation_service.py`, after building each item, add product fields.

Minimal approach:
- Build `product_by_id = {p.id: p for p in products}`
- When emitting item, merge:

```python
product = product_by_id.get(product.id)  # or by product_id
item.update(
    {
        "price": float(product.price or 0),
        "brand": AnalyticsService._brand_display(product.brand),
        "image_url": product.image_url or "",
    }
)
```

Note: Import `AnalyticsService` from `app.services.analytics_service`.

- [ ] **Step 4: Run test again**

```powershell
$env:PYTHONPATH='.'; pytest -q tests/test_recommendation_enriched.py::test_recommendations_include_price_and_image_url
```

Expected: PASS.

- [ ] **Step 5: Run full backend tests**

```powershell
$env:PYTHONPATH='.'; pytest -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/recommendation_service.py backend/tests/test_recommendation_enriched.py
git commit -m "feat(recommendation): include price brand image_url in items"
```

---

### Task 3: Merchant chart APIs (share + trend) (backend)

**Files:**
- Create: `backend/app/routes/merchant_charts.py`
- Modify: `backend/app/__init__.py`
- Create: `backend/tests/test_merchant_charts.py`

- [ ] **Step 1: Write failing tests for endpoints**

Create `backend/tests/test_merchant_charts.py`:

```python
from datetime import datetime

from app.extensions import db
from app.models.behavior_log import BehaviorLog


def _persist_log(merchant_id, product_id, product_name, category, brand, action_type):
    now = datetime.utcnow()
    entity = BehaviorLog(
        log_id=f"chart-{merchant_id}-{product_id}-{action_type}-{now.timestamp()}",
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
        timestamp=now,
        created_at=now,
    )
    db.session.add(entity)
    db.session.commit()


def test_merchant_charts_share(client, merchant_headers, seeded_demo_data):
    _persist_log(2, 1, "轻量跑鞋", "运动鞋", "CloudStep", "view")
    _persist_log(2, 1, "轻量跑鞋", "运动鞋", "CloudStep", "purchase")
    response = client.get("/api/merchant/charts/share?top_n=5", headers=merchant_headers)
    assert response.status_code == 200
    payload = response.get_json()
    assert "category_share" in payload
    assert "brand_share" in payload
    assert payload["category_share"]
    assert payload["brand_share"]


def test_merchant_charts_trend(client, merchant_headers, seeded_demo_data):
    _persist_log(2, 1, "轻量跑鞋", "运动鞋", "CloudStep", "view")
    response = client.get("/api/merchant/charts/trend?days=7", headers=merchant_headers)
    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload["days"]) == 7
    assert len(payload["series"]) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

```powershell
$env:PYTHONPATH='.'; pytest -q tests/test_merchant_charts.py -q
```

Expected: 404.

- [ ] **Step 3: Implement `merchant_charts` routes**

Create `backend/app/routes/merchant_charts.py`:

```python
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from sqlalchemy import func

from ..extensions import db
from ..models.behavior_log import BehaviorLog
from ..services.analytics_service import AnalyticsService


bp = Blueprint("merchant_charts", __name__, url_prefix="/api/merchant/charts")


def _ensure_merchant():
    if get_jwt().get("role") != "merchant":
        return jsonify({"message": "仅商家可查看图表"}), 403
    return None


@bp.get("/share")
@jwt_required()
def share():
    unauthorized = _ensure_merchant()
    if unauthorized is not None:
        return unauthorized
    merchant_id = int(get_jwt_identity())
    top_n = int(request.args.get("top_n", 5))

    category_rows = (
        db.session.query(func.coalesce(BehaviorLog.category, "未知品类"), func.count(BehaviorLog.id))
        .filter(BehaviorLog.merchant_id == merchant_id)
        .group_by(func.coalesce(BehaviorLog.category, "未知品类"))
        .order_by(func.count(BehaviorLog.id).desc())
        .all()
    )

    total = sum(count for _, count in category_rows) or 1
    top = category_rows[:top_n]
    rest = sum(count for _, count in category_rows[top_n:])
    category_share = [{"name": name, "value": int(count)} for name, count in top]
    if rest:
        category_share.append({"name": "其它", "value": int(rest)})

    brand_rows = (
        db.session.query(func.coalesce(BehaviorLog.brand, "未知品牌"), func.count(BehaviorLog.id))
        .filter(BehaviorLog.merchant_id == merchant_id, BehaviorLog.action_type == "purchase")
        .group_by(func.coalesce(BehaviorLog.brand, "未知品牌"))
        .order_by(func.count(BehaviorLog.id).desc())
        .all()
    )
    brand_share = [{"name": AnalyticsService._brand_display(name), "value": int(count)} for name, count in brand_rows[:top_n]]
    rest_brand = sum(count for _, count in brand_rows[top_n:])
    if rest_brand:
        brand_share.append({"name": "其它", "value": int(rest_brand)})

    return jsonify({"category_share": category_share, "brand_share": brand_share})


@bp.get("/trend")
@jwt_required()
def trend():
    unauthorized = _ensure_merchant()
    if unauthorized is not None:
        return unauthorized
    merchant_id = int(get_jwt_identity())
    days = int(request.args.get("days", 7))
    end = datetime.utcnow().date()
    start = end - timedelta(days=days - 1)

    # SQLite/MySQL compatibility: use DATE(created_at)
    date_expr = func.date(BehaviorLog.created_at)
    rows = (
        db.session.query(date_expr, BehaviorLog.action_type, func.count(BehaviorLog.id))
        .filter(BehaviorLog.merchant_id == merchant_id, BehaviorLog.created_at >= datetime.combine(start, datetime.min.time()))
        .group_by(date_expr, BehaviorLog.action_type)
        .all()
    )
    view_map = {}
    purchase_map = {}
    for day_str, action_type, count in rows:
        key = str(day_str)
        if action_type == "view":
            view_map[key] = int(count)
        if action_type == "purchase":
            purchase_map[key] = int(count)

    day_list = [(start + timedelta(days=i)).isoformat() for i in range(days)]
    return jsonify(
        {
            "days": day_list,
            "series": [
                {"name": "浏览", "data": [view_map.get(day, 0) for day in day_list]},
                {"name": "购买", "data": [purchase_map.get(day, 0) for day in day_list]},
            ],
        }
    )
```

- [ ] **Step 4: Register blueprint**

Modify `backend/app/__init__.py`:

```python
from .routes.merchant_charts import bp as merchant_charts_bp
...
app.register_blueprint(merchant_charts_bp)
```

- [ ] **Step 5: Run tests again**

```powershell
$env:PYTHONPATH='.'; pytest -q tests/test_merchant_charts.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routes/merchant_charts.py backend/app/__init__.py backend/tests/test_merchant_charts.py
git commit -m "feat(merchant): add charts share and trend apis"
```

---

### Task 4: Price compare API (backend, demo offers)

**Files:**
- Create: `backend/app/services/price_compare_service.py`
- Create: `backend/app/routes/price_compare.py`
- Modify: `backend/app/__init__.py`
- Create: `backend/tests/test_price_compare.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_price_compare.py`:

```python
def test_price_compare_returns_platform_offers(client, customer_headers, seeded_demo_data):
    response = client.get("/api/price-compare?product_id=1", headers=customer_headers)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["product"]["product_id"] == 1
    platforms = [item["platform"] for item in payload["offers"]]
    assert platforms == ["抖音", "京东", "拼多多", "得物"]
    assert payload["best"]["platform"]
    assert payload["best"]["saving"] >= 0


def test_price_compare_is_deterministic(client, customer_headers, seeded_demo_data):
    response1 = client.get("/api/price-compare?product_id=1", headers=customer_headers)
    response2 = client.get("/api/price-compare?product_id=1", headers=customer_headers)
    assert response1.get_json()["offers"] == response2.get_json()["offers"]
```

- [ ] **Step 2: Run tests to verify they fail**

```powershell
$env:PYTHONPATH='.'; pytest -q tests/test_price_compare.py
```

Expected: 404.

- [ ] **Step 3: Implement service**

Create `backend/app/services/price_compare_service.py`:

```python
from decimal import Decimal

from ..models.product import Product
from ..services.analytics_service import AnalyticsService


class PriceCompareService:
    PLATFORMS = ("抖音", "京东", "拼多多", "得物")
    PLATFORM_HINTS = {
        "京东": ("次日达/自营", "可叠加满减券"),
        "拼多多": ("百亿补贴", "大促券可能更低"),
        "抖音": ("直播券", "关注直播间福利"),
        "得物": ("鉴别保障", "正品安心"),
    }
    FACTOR_RANGES = {
        "抖音": (Decimal("0.92"), Decimal("1.08")),
        "京东": (Decimal("0.95"), Decimal("1.12")),
        "拼多多": (Decimal("0.88"), Decimal("1.05")),
        "得物": (Decimal("0.97"), Decimal("1.15")),
    }

    def _factor(self, product_id, platform):
        low, high = self.FACTOR_RANGES[platform]
        span = high - low
        # deterministic: map product_id to 0..99
        bucket = Decimal(str((product_id * 37 + len(platform) * 11) % 100)) / Decimal("100")
        return (low + span * bucket).quantize(Decimal("0.0001"))

    def build(self, product_id):
        product = Product.query.filter_by(id=product_id, is_active=True).first()
        if product is None:
            return None
        base_price = Decimal(str(product.price or 0)).quantize(Decimal("0.01"))

        offers = []
        for platform in self.PLATFORMS:
            factor = self._factor(product_id, platform)
            price = (base_price * factor).quantize(Decimal("0.01"))
            delivery_hint, coupon_hint = self.PLATFORM_HINTS.get(platform, ("", ""))
            offers.append(
                {
                    "platform": platform,
                    "price": float(price),
                    "delivery_hint": delivery_hint,
                    "coupon_hint": coupon_hint,
                }
            )

        best_offer = min(offers, key=lambda item: item["price"])
        saving = (base_price - Decimal(str(best_offer["price"]))).quantize(Decimal("0.01"))
        saving_value = float(max(saving, Decimal("0.00")))

        advice = (
            f"{best_offer['platform']} 当前更便宜，预计可省 {saving_value:.2f} 元；"
            f"若更看重保障与体验，可优先考虑 京东/得物。"
        )

        return {
            "product": {
                "product_id": product.id,
                "name": product.name,
                "price": float(base_price),
                "brand": AnalyticsService._brand_display(product.brand),
                "category": product.category,
                "image_url": product.image_url or "",
            },
            "offers": offers,
            "best": {
                "platform": best_offer["platform"],
                "price": best_offer["price"],
                "saving": saving_value,
            },
            "advice": advice,
        }
```

- [ ] **Step 4: Implement route + register**

Create `backend/app/routes/price_compare.py`:

```python
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required

from ..services.price_compare_service import PriceCompareService


bp = Blueprint("price_compare", __name__, url_prefix="/api")
service = PriceCompareService()


@bp.get("/price-compare")
@jwt_required()
def price_compare():
    if get_jwt().get("role") != "customer":
        return jsonify({"message": "仅普通用户可使用比价功能"}), 403

    product_id = request.args.get("product_id")
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return jsonify({"message": "product_id 非法"}), 400

    payload = service.build(product_id)
    if payload is None:
        return jsonify({"message": "商品不存在或已下架"}), 404
    return jsonify(payload)
```

Register in `backend/app/__init__.py`:

```python
from .routes.price_compare import bp as price_compare_bp
...
app.register_blueprint(price_compare_bp)
```

- [ ] **Step 5: Run tests again**

```powershell
$env:PYTHONPATH='.'; pytest -q tests/test_price_compare.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/price_compare_service.py backend/app/routes/price_compare.py backend/app/__init__.py backend/tests/test_price_compare.py
git commit -m "feat(customer): add demo price compare api"
```

---

### Task 5: Frontend ECharts base + merchant chart UI

**Files:**
- Create: `frontend/src/components/charts/EChartView.vue`
- Create: `frontend/src/components/charts/SharePieChart.vue`
- Create: `frontend/src/components/charts/TrendLineChart.vue`
- Create: `frontend/src/api/merchantCharts.js`
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
- Modify: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Add EChartView component**

Create `frontend/src/components/charts/EChartView.vue`:

```vue
<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: {
    type: Object,
    required: true
  },
  height: {
    type: [String, Number],
    default: 260
  }
})

const rootRef = ref(null)
let chart = null

function resize() {
  chart?.resize()
}

onMounted(() => {
  chart = echarts.init(rootRef.value)
  chart.setOption(props.option || {}, true)
  window.addEventListener('resize', resize)
})

watch(
  () => props.option,
  (nextOption) => {
    chart?.setOption(nextOption || {}, true)
  },
  { deep: true }
)

onUnmounted(() => {
  window.removeEventListener('resize', resize)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div ref="rootRef" :style="{ width: '100%', height: typeof height === 'number' ? `${height}px` : height }"></div>
</template>
```

- [ ] **Step 2: Add SharePieChart + TrendLineChart wrappers**

Create `frontend/src/components/charts/SharePieChart.vue`:

```vue
<script setup>
import { computed } from 'vue'

import EChartView from './EChartView.vue'

const props = defineProps({
  title: { type: String, default: '' },
  items: { type: Array, default: () => [] }
})

const option = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { top: 0, left: 'center' },
  series: [
    {
      type: 'pie',
      radius: ['35%', '70%'],
      avoidLabelOverlap: true,
      label: { show: false },
      emphasis: { label: { show: true, fontWeight: 'bold' } },
      data: props.items
    }
  ]
}))
</script>

<template>
  <EChartView :option="option" :height="280" />
</template>
```

Create `frontend/src/components/charts/TrendLineChart.vue`:

```vue
<script setup>
import { computed } from 'vue'

import EChartView from './EChartView.vue'

const props = defineProps({
  days: { type: Array, default: () => [] },
  series: { type: Array, default: () => [] }
})

const option = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { top: 0 },
  grid: { left: 32, right: 18, top: 36, bottom: 24 },
  xAxis: { type: 'category', data: props.days },
  yAxis: { type: 'value' },
  series: props.series.map((item) => ({
    name: item.name,
    type: 'line',
    smooth: true,
    data: item.data
  }))
}))
</script>

<template>
  <EChartView :option="option" :height="280" />
</template>
```

- [ ] **Step 3: Add merchantCharts API**

Create `frontend/src/api/merchantCharts.js`:

```js
import http from './http'

export async function fetchMerchantChartShare(params = {}) {
  const response = await http.get('/api/merchant/charts/share', { params })
  return response.data
}

export async function fetchMerchantChartTrend(params = {}) {
  const response = await http.get('/api/merchant/charts/trend', { params })
  return response.data
}
```

- [ ] **Step 4: Wire into MerchantDashboard**

In `MerchantDashboard.vue`, add new state:

```js
const chartShare = ref({ category_share: [], brand_share: [] })
const chartTrend = ref({ days: [], series: [] })
```

Fetch in `loadDashboard()` and `refreshOverviewSnapshot()` with Promise.all:

```js
fetchMerchantChartShare({ top_n: 5 })
fetchMerchantChartTrend({ days: 7 })
```

Then in overview panel template, render 2 panels:
- 品类占比饼图（items=chartShare.category_share）
- 品牌销量占比饼图（items=chartShare.brand_share）
- 近7天趋势折线图（days=chartTrend.days, series=chartTrend.series）

Use existing `dashboard-panel` layout.

- [ ] **Step 5: Update merchant-dashboard tests**

Mock `../api/merchantCharts.js` and assert that:
- “品类占比”“品牌占比”“近7天趋势”文案出现
- `fetchMerchantChartShare/fetchMerchantChartTrend` 被调用

- [ ] **Step 6: Run frontend tests**

```bash
npm test
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/charts/EChartView.vue frontend/src/components/charts/SharePieChart.vue frontend/src/components/charts/TrendLineChart.vue frontend/src/api/merchantCharts.js frontend/src/views/merchant/MerchantDashboard.vue frontend/src/tests/merchant-dashboard.test.js
git commit -m "feat(merchant): add charts pie and trend line"
```

---

### Task 6: Customer product cards show image + price + compare entry (frontend)

**Files:**
- Modify: `frontend/src/views/customer/CustomerHome.vue`
- Modify: `frontend/src/views/customer/RecommendationView.vue`
- Modify: `frontend/src/tests/customer-home.test.js`

- [ ] **Step 1: Enhance templates**

In both lists, render:
- `<img :src="item.image_url" ... />`
- price: `￥{{ Number(item.price || 0).toFixed(2) }}`
- tags: `{{ item.brand }} · {{ item.category }}`

Add a “比价” button in `CustomerHome` recommendation list to route to price compare page:

```vue
<RouterLink class="ghost-button" :to="`/customer/price-compare?product_id=${item.product_id}`">比价</RouterLink>
```

In `RecommendationView`, include same link.

- [ ] **Step 2: Update tests**

Update mocks in `customer-home.test.js` so recommendation items include `price/image_url/brand`.
Assert rendered price and that an `<img>` exists.

- [ ] **Step 3: Run tests**

```bash
npm test
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/customer/CustomerHome.vue frontend/src/views/customer/RecommendationView.vue frontend/src/tests/customer-home.test.js
git commit -m "feat(customer): show product image price and compare entry"
```

---

### Task 7: Price compare page + routing (frontend)

**Files:**
- Create: `frontend/src/api/priceCompare.js`
- Create: `frontend/src/views/customer/PriceCompareView.vue`
- Modify: `frontend/src/router/index.js`
- Create: `frontend/src/tests/price-compare.test.js`
- Modify: `frontend/src/tests/router.test.js`

- [ ] **Step 1: Add API**

Create `frontend/src/api/priceCompare.js`:

```js
import http from './http'

export async function fetchPriceCompare(params = {}) {
  const response = await http.get('/api/price-compare', { params })
  return response.data
}
```

- [ ] **Step 2: Build view**

Create `frontend/src/views/customer/PriceCompareView.vue`:

```vue
<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { fetchPriceCompare } from '../../api/priceCompare.js'

const route = useRoute()
const isLoading = ref(true)
const errorMessage = ref('')
const payload = ref(null)

const productId = computed(() => Number(route.query.product_id || 0))

async function load() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const result = await fetchPriceCompare({ product_id: productId.value })
    payload.value = result
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '比价数据加载失败，请稍后重试。'
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  load()
})
</script>

<template>
  <section class="customer-page">
    <header class="customer-page__header">
      <div>
        <p class="section-kicker">PRICE COMPARE</p>
        <h2>平台比价</h2>
        <p>对比抖音、京东、拼多多、得物的演示报价，辅助做购买决策。</p>
      </div>
      <button class="ghost-button" type="button" @click="load">刷新比价</button>
    </header>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

    <div v-if="payload" class="dashboard-panel" :aria-busy="isLoading">
      <div style="display: grid; grid-template-columns: 84px 1fr; gap: 14px; align-items: center;">
        <img
          :src="payload.product.image_url"
          alt="商品图片"
          style="width: 84px; height: 84px; object-fit: cover; border-radius: 16px; border: 1px solid rgba(148, 163, 184, 0.25);"
        />
        <div>
          <strong style="display: block; font-size: 1.05rem;">{{ payload.product.name }}</strong>
          <p style="margin: 6px 0 0; color: #475569;">
            本平台价 ￥{{ Number(payload.product.price || 0).toFixed(2) }} · {{ payload.product.brand }} · {{ payload.product.category }}
          </p>
        </div>
      </div>

      <div style="margin-top: 16px;">
        <p v-if="payload.best" class="admin-log-preview__note">
          最低价平台：{{ payload.best.platform }}，预计可省 ￥{{ Number(payload.best.saving || 0).toFixed(2) }}
        </p>
        <p v-if="payload.advice" class="admin-log-preview__note">{{ payload.advice }}</p>
      </div>

      <ul v-if="payload.offers?.length" class="strategy-list" style="margin-top: 16px;">
        <li v-for="offer in payload.offers" :key="offer.platform" class="strategy-list__item">
          <div class="strategy-list__meta">
            <strong>{{ offer.platform }}</strong>
            <span>￥{{ Number(offer.price || 0).toFixed(2) }}</span>
          </div>
          <p>{{ offer.delivery_hint }} · {{ offer.coupon_hint }}</p>
        </li>
      </ul>
    </div>
  </section>
</template>
```

- [ ] **Step 3: Add route**

In `frontend/src/router/index.js`, add customer child route (follow existing patterns):
- name: `customer-price-compare`
- path: `customer/price-compare`
- component: `PriceCompareView`
- meta.roles: `['customer']`

- [ ] **Step 4: Add tests**

Create `frontend/src/tests/price-compare.test.js` mocking `fetchPriceCompare`, assert:
- 标题“平台比价”
- 渲染 4 个平台
- 渲染最低价提示/省钱金额

Update `router.test.js` to assert route registration.

- [ ] **Step 5: Run tests**

```bash
npm test
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api/priceCompare.js frontend/src/views/customer/PriceCompareView.vue frontend/src/router/index.js frontend/src/tests/price-compare.test.js frontend/src/tests/router.test.js
git commit -m "feat(customer): add demo price compare page"
```

---

### Task 8: Final verification (full test suites)

- [ ] **Step 1: Run backend tests**

```powershell
cd backend
$env:PYTHONPATH='.'; pytest -q
```

Expected: PASS.

- [ ] **Step 2: Run frontend tests**

```bash
cd frontend
npm test
```

Expected: PASS.

- [ ] **Step 3: Commit (if any leftover)**

```bash
git status
```

Ensure working tree clean.

---

## Self-Review Checklist

- Spec coverage:
  - 商家：漏斗（既有）+ 占比饼图 + 近7天趋势折线图 ✅
  - 用户端：商品卡片图片+价格 ✅
  - 比价：4平台、最低价、省钱、建议、确定性报价 ✅
- No placeholders: 每个任务包含精确路径、代码块、命令与预期结果 ✅
- Naming consistency:
  - `Product.image_url`
  - `/api/merchant/charts/share` `/api/merchant/charts/trend`
  - `/api/price-compare`

