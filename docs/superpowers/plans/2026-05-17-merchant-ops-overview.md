# 商家经营总览增强（演示口径）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在商家端新增“经营总览（演示口径）”，展示近30天收入/成本/利润、库存清单、低销量建议下架清单（手动确认下架）、销量冠军品牌 TOP（按购买次数）。

**Architecture:** 后端新增商家经营接口聚合 `BehaviorLog(purchase)` + `Product(price/stock/is_active/cost_price)` 生成一份 ops 视图；前端在商家仪表盘 overview 面板增加一个“经营总览”模块展示并支持下架操作。

**Tech Stack:** Flask + Flask-JWT-Extended + SQLAlchemy，Vue3 + Vite + Vitest

---

## File Structure / Touch Points

**Backend**
- Modify: `backend/app/models/product.py`（新增 `cost_price`）
- Modify: `backend/app/utils/seed_data.py`（写入 demo 商品成本价）
- Create: `backend/app/services/merchant_ops_service.py`（经营聚合逻辑）
- Create: `backend/app/routes/merchant_ops.py`（经营总览 & 下架接口）
- Modify: `backend/app/__init__.py`（注册蓝图）
- Create: `backend/tests/test_merchant_ops.py`（接口单测）

**Frontend**
- Create: `frontend/src/api/merchantOps.js`（API 封装）
- Create: `frontend/src/views/merchant/MerchantOpsOverview.vue`（经营总览模块）
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`（接入模块、加载数据、下架动作）
- Modify: `frontend/src/tests/merchant-dashboard.test.js`（mock 新 API 并断言渲染/下架）

---

### Task 1: Add product cost field (backend model + seed)

**Files:**
- Modify: `backend/app/models/product.py`
- Modify: `backend/app/utils/seed_data.py`

- [ ] **Step 1: Write failing backend test for `cost_price` existence**

Create `backend/tests/test_merchant_ops.py` (initial skeleton):

```python
from decimal import Decimal

from app.extensions import db
from app.models.product import Product


def test_product_has_cost_price_column(seeded_demo_data):
    product = Product.query.first()
    assert hasattr(product, "cost_price")
    assert product.cost_price is not None
    assert Decimal(str(product.cost_price)) > 0
```

- [ ] **Step 2: Run the test to verify it fails**

Run (PowerShell, from `backend/`):

```powershell
$env:PYTHONPATH='.'; pytest -q backend/tests/test_merchant_ops.py::test_product_has_cost_price_column
```

Expected: FAIL (attribute missing).

- [ ] **Step 3: Add `cost_price` to Product model**

Update `backend/app/models/product.py`:

```python
from datetime import datetime
from decimal import Decimal

from ..extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False, default="未分类")
    brand = db.Column(db.String(50), nullable=False, default="自有品牌")
    price = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    cost_price = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    stock = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    merchant = db.relationship("User", back_populates="products")
```

- [ ] **Step 4: Seed demo data with default `cost_price = price * 0.6`**

Update `backend/app/utils/seed_data.py` when creating `Product(...)` (keep existing fields, add one line):

```python
cost_price=(payload["price"] * Decimal("0.60")).quantize(Decimal("0.01")),
```

- [ ] **Step 5: Run the test to verify it passes**

```powershell
$env:PYTHONPATH='.'; pytest -q backend/tests/test_merchant_ops.py::test_product_has_cost_price_column
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/product.py backend/app/utils/seed_data.py backend/tests/test_merchant_ops.py
git commit -m "feat(merchant): add product cost_price for ops overview"
```

---

### Task 2: Implement merchant ops overview API (backend)

**Files:**
- Create: `backend/app/services/merchant_ops_service.py`
- Create: `backend/app/routes/merchant_ops.py`
- Modify: `backend/app/__init__.py`
- Test: `backend/tests/test_merchant_ops.py`

- [ ] **Step 1: Write failing test for ops overview endpoint**

Append to `backend/tests/test_merchant_ops.py`:

```python
from datetime import datetime, timedelta

from app.extensions import db
from app.models.behavior_log import BehaviorLog
from app.models.product import Product


def _create_purchase_log(merchant_id, product):
    return BehaviorLog(
        log_id=f"purchase-{merchant_id}-{product.id}-{datetime.utcnow().timestamp()}",
        user_id=999,
        merchant_id=merchant_id,
        product_id=product.id,
        product_name=product.name,
        category=product.category,
        brand=product.brand,
        price=float(product.price),
        action_type="purchase",
        region="华东",
        device_type="ios",
        source_channel="customer_page",
        session_id="sess",
        stay_duration=10,
        is_new_user=False,
        timestamp=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )


def test_merchant_ops_overview_returns_profit_and_lists(client, merchant_headers, seeded_demo_data):
    merchant_id = 2
    product = Product.query.filter_by(merchant_id=merchant_id).first()
    assert product is not None

    db.session.add_all([_create_purchase_log(merchant_id, product), _create_purchase_log(merchant_id, product)])
    db.session.commit()

    response = client.get("/api/merchant/ops/overview?days=30&low_sales_threshold=3&brand_top_n=5", headers=merchant_headers)
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["summary"]["days"] == 30
    assert payload["summary"]["revenue"] > 0
    assert payload["summary"]["cost"] > 0
    assert "profit" in payload["summary"]
    assert "inventory_items" in payload
    assert "delist_suggestions" in payload
    assert "inactive_items" in payload
    assert "focus_brands" in payload
    assert payload["focus_brands"][0]["purchase_count_30d"] >= 2
```

- [ ] **Step 2: Run the test to verify it fails**

```powershell
$env:PYTHONPATH='.'; pytest -q backend/tests/test_merchant_ops.py::test_merchant_ops_overview_returns_profit_and_lists
```

Expected: 404 or FAIL.

- [ ] **Step 3: Implement service aggregation**

Create `backend/app/services/merchant_ops_service.py`:

```python
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func

from ..extensions import db
from ..models.behavior_log import BehaviorLog
from ..models.product import Product
from .analytics_service import AnalyticsService


class MerchantOpsService:
    def __init__(self):
        self._brand_display = AnalyticsService.BRAND_DISPLAY

    def build_overview(self, merchant_id, days=30, low_sales_threshold=3, brand_top_n=5):
        days = int(days)
        low_sales_threshold = int(low_sales_threshold)
        brand_top_n = int(brand_top_n)

        threshold = datetime.utcnow() - timedelta(days=days)

        products = Product.query.filter_by(merchant_id=merchant_id).all()
        product_by_id = {item.id: item for item in products}

        purchase_rows = (
            db.session.query(BehaviorLog.product_id, func.count(BehaviorLog.id))
            .filter(
                BehaviorLog.merchant_id == merchant_id,
                BehaviorLog.action_type == "purchase",
                BehaviorLog.created_at >= threshold,
            )
            .group_by(BehaviorLog.product_id)
            .all()
        )
        purchase_by_product = {product_id: count for product_id, count in purchase_rows}

        revenue = Decimal("0.00")
        cost = Decimal("0.00")
        for product_id, count in purchase_by_product.items():
            product = product_by_id.get(product_id)
            if product is None:
                continue
            price = Decimal(str(product.price or 0))
            cost_price = Decimal(str(product.cost_price or 0))
            if cost_price <= 0:
                cost_price = (price * Decimal("0.60")).quantize(Decimal("0.01"))
            revenue += (price * Decimal(count)).quantize(Decimal("0.01"))
            cost += (cost_price * Decimal(count)).quantize(Decimal("0.01"))

        inventory_items = []
        inactive_items = []
        for product in products:
            item = {
                "product_id": product.id,
                "name": product.name,
                "category": product.category,
                "brand": self._brand_display.get(product.brand, product.brand),
                "stock": int(product.stock or 0),
                "price": float(product.price or 0),
                "cost_price": float(product.cost_price or 0) if product.cost_price else float((Decimal(str(product.price or 0)) * Decimal("0.60")).quantize(Decimal("0.01"))),
                "is_active": bool(product.is_active),
            }
            if not product.is_active:
                inactive_items.append(item)
                continue
            if int(product.stock or 0) > 0:
                inventory_items.append(item)

        delist_suggestions = []
        for product in products:
            if not product.is_active:
                continue
            purchase_count = int(purchase_by_product.get(product.id, 0))
            if purchase_count < low_sales_threshold:
                delist_suggestions.append(
                    {
                        "product_id": product.id,
                        "name": product.name,
                        "category": product.category,
                        "brand": self._brand_display.get(product.brand, product.brand),
                        "purchase_count_30d": purchase_count,
                        "stock": int(product.stock or 0),
                        "price": float(product.price or 0),
                    }
                )

        brand_counter = {}
        for product in products:
            count = int(purchase_by_product.get(product.id, 0))
            if count <= 0:
                continue
            brand = self._brand_display.get(product.brand, product.brand)
            brand_counter[brand] = brand_counter.get(brand, 0) + count
        focus_brands = [
            {"brand": brand, "purchase_count_30d": count}
            for brand, count in sorted(brand_counter.items(), key=lambda item: item[1], reverse=True)[:brand_top_n]
        ]

        return {
            "summary": {
                "days": days,
                "revenue": float(revenue),
                "cost": float(cost),
                "profit": float((revenue - cost).quantize(Decimal("0.01"))),
            },
            "inventory_items": inventory_items,
            "delist_suggestions": delist_suggestions,
            "inactive_items": inactive_items,
            "focus_brands": focus_brands,
        }
```

- [ ] **Step 4: Implement routes + register blueprint**

Create `backend/app/routes/merchant_ops.py`:

```python
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from ..extensions import db
from ..models.product import Product
from ..services.merchant_ops_service import MerchantOpsService


bp = Blueprint("merchant_ops", __name__, url_prefix="/api/merchant")
merchant_ops_service = MerchantOpsService()


def _ensure_merchant():
    if get_jwt().get("role") != "merchant":
        return jsonify({"message": "仅商家可查看经营总览"}), 403
    return None


@bp.get("/ops/overview")
@jwt_required()
def ops_overview():
    unauthorized = _ensure_merchant()
    if unauthorized is not None:
        return unauthorized

    merchant_id = int(get_jwt_identity())
    days = request.args.get("days", 30)
    low_sales_threshold = request.args.get("low_sales_threshold", 3)
    brand_top_n = request.args.get("brand_top_n", 5)
    return jsonify(
        merchant_ops_service.build_overview(
            merchant_id=merchant_id,
            days=days,
            low_sales_threshold=low_sales_threshold,
            brand_top_n=brand_top_n,
        )
    )


@bp.post("/products/<int:product_id>/deactivate")
@jwt_required()
def deactivate_product(product_id):
    unauthorized = _ensure_merchant()
    if unauthorized is not None:
        return unauthorized

    merchant_id = int(get_jwt_identity())
    product = Product.query.filter_by(id=product_id, merchant_id=merchant_id).first()
    if product is None:
        return jsonify({"message": "商品不存在或无权限操作"}), 404
    if not product.is_active:
        return jsonify({"message": "商品已下架", "product": {"id": product.id, "is_active": False}})

    product.is_active = False
    db.session.commit()
    return jsonify({"message": "下架成功", "product": {"id": product.id, "is_active": False}})
```

Modify `backend/app/__init__.py` to register:

```python
from .routes.merchant_ops import bp as merchant_ops_bp
...
app.register_blueprint(merchant_ops_bp)
```

- [ ] **Step 5: Run test to verify it passes**

```powershell
$env:PYTHONPATH='.'; pytest -q backend/tests/test_merchant_ops.py::test_merchant_ops_overview_returns_profit_and_lists
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/merchant_ops_service.py backend/app/routes/merchant_ops.py backend/app/__init__.py backend/tests/test_merchant_ops.py
git commit -m "feat(merchant): add ops overview api"
```

---

### Task 3: Implement manual deactivate flow test (backend)

**Files:**
- Test: `backend/tests/test_merchant_ops.py`
- Modify: `backend/app/routes/merchant_ops.py` (if needed)

- [ ] **Step 1: Write failing test for deactivate endpoint**

Append to `backend/tests/test_merchant_ops.py`:

```python
def test_merchant_can_deactivate_low_sales_product(client, merchant_headers, seeded_demo_data):
    merchant_id = 2
    product = Product.query.filter_by(merchant_id=merchant_id, is_active=True).first()
    assert product is not None

    response = client.post(f"/api/merchant/products/{product.id}/deactivate", headers=merchant_headers)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["product"]["id"] == product.id
    assert payload["product"]["is_active"] is False

    updated = Product.query.get(product.id)
    assert updated.is_active is False
```

- [ ] **Step 2: Run it to verify it fails (before endpoint exists / wrong behavior)**

```powershell
$env:PYTHONPATH='.'; pytest -q backend/tests/test_merchant_ops.py::test_merchant_can_deactivate_low_sales_product
```

Expected: FAIL until endpoint is correct.

- [ ] **Step 3: Implement minimal fixes if needed**

If response shape differs, adjust route to match test expectations:

- Returns `200` and sets `is_active=False`
- Returns `404` when product not found or not owned by merchant

- [ ] **Step 4: Re-run the test**

```powershell
$env:PYTHONPATH='.'; pytest -q backend/tests/test_merchant_ops.py::test_merchant_can_deactivate_low_sales_product
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routes/merchant_ops.py backend/tests/test_merchant_ops.py
git commit -m "feat(merchant): support manual product deactivation"
```

---

### Task 4: Add frontend API client + ops overview component

**Files:**
- Create: `frontend/src/api/merchantOps.js`
- Create: `frontend/src/views/merchant/MerchantOpsOverview.vue`

- [ ] **Step 1: Add API wrappers**

Create `frontend/src/api/merchantOps.js`:

```js
import http from './http'

export async function fetchMerchantOpsOverview(params = {}) {
  const response = await http.get('/api/merchant/ops/overview', { params })
  return response.data
}

export async function deactivateMerchantProduct(productId) {
  const response = await http.post(`/api/merchant/products/${productId}/deactivate`)
  return response.data
}
```

- [ ] **Step 2: Create `MerchantOpsOverview` component**

Create `frontend/src/views/merchant/MerchantOpsOverview.vue`:

```vue
<script setup>
import { computed } from 'vue'

import TrendBarChart from '../../components/charts/TrendBarChart.vue'

const props = defineProps({
  payload: {
    type: Object,
    required: true
  },
  onDeactivate: {
    type: Function,
    required: true
  },
  isDeactivatingId: {
    type: Number,
    default: 0
  }
})

function formatMoney(value) {
  const numberValue = Number(value || 0)
  return numberValue.toFixed(2)
}

const cards = computed(() => [
  { label: `近${props.payload?.summary?.days || 30}天收入`, value: formatMoney(props.payload?.summary?.revenue), hint: '估算：购买次数×商品售价' },
  { label: `近${props.payload?.summary?.days || 30}天成本`, value: formatMoney(props.payload?.summary?.cost), hint: '估算：购买次数×商品成本价' },
  { label: `近${props.payload?.summary?.days || 30}天利润`, value: formatMoney(props.payload?.summary?.profit), hint: '利润=收入-成本' }
])
</script>

<template>
  <section class="merchant-dashboard__layer">
    <div class="merchant-dashboard__layer-head">
      <h3>经营总览（演示口径）</h3>
      <p>用于答辩展示“利润、库存、下架、重点品牌”的经营视角（基于 purchase 行为次数估算）。</p>
    </div>

    <section class="merchant-dashboard__summary">
      <article v-for="card in cards" :key="card.label" class="metric-card">
        <p class="metric-card__label">{{ card.label }}</p>
        <strong class="metric-card__value">{{ card.value }}</strong>
        <span class="metric-card__hint">{{ card.hint }}</span>
      </article>
    </section>

    <div class="merchant-dashboard__layer-grid">
      <article class="dashboard-panel">
        <div class="dashboard-panel__header">
          <div>
            <p class="section-kicker">INVENTORY</p>
            <h3>库存清单</h3>
            <p>展示当前有库存的商品（stock>0）。</p>
          </div>
          <span class="dashboard-panel__badge">{{ payload.inventory_items?.length || 0 }} 个SKU</span>
        </div>

        <ul v-if="payload.inventory_items?.length" class="strategy-list">
          <li v-for="item in payload.inventory_items" :key="item.product_id" class="strategy-list__item">
            <div class="strategy-list__meta">
              <strong>{{ item.name }}</strong>
              <span>{{ item.category }} / {{ item.brand }}</span>
            </div>
            <p>库存 {{ item.stock }} · 售价 {{ Number(item.price || 0).toFixed(2) }} · 成本 {{ Number(item.cost_price || 0).toFixed(2) }}</p>
          </li>
        </ul>
        <p v-else class="empty-state">暂无库存商品。</p>
      </article>

      <article class="dashboard-panel">
        <div class="dashboard-panel__header">
          <div>
            <p class="section-kicker">DELIST SUGGESTIONS</p>
            <h3>建议下架（近30天购买&lt;3）</h3>
            <p>只给建议，点击按钮才会真正下架。</p>
          </div>
          <span class="dashboard-panel__badge">{{ payload.delist_suggestions?.length || 0 }} 个</span>
        </div>

        <ul v-if="payload.delist_suggestions?.length" class="strategy-list">
          <li v-for="item in payload.delist_suggestions" :key="item.product_id" class="strategy-list__item">
            <div class="strategy-list__meta">
              <strong>{{ item.name }}</strong>
              <span>近30天购买 {{ item.purchase_count_30d }} 次</span>
            </div>
            <p>{{ item.category }} / {{ item.brand }} · 库存 {{ item.stock }}</p>
            <div class="merchant-action-buttons">
              <button
                class="ghost-button"
                type="button"
                :disabled="isDeactivatingId === item.product_id"
                @click="onDeactivate(item.product_id)"
              >
                {{ isDeactivatingId === item.product_id ? '下架中...' : '下架' }}
              </button>
            </div>
          </li>
        </ul>
        <p v-else class="empty-state">暂无需要下架的低销量商品。</p>
      </article>

      <article class="dashboard-panel">
        <div class="dashboard-panel__header">
          <div>
            <p class="section-kicker">FOCUS BRANDS</p>
            <h3>销量冠军品牌TOP</h3>
            <p>按近30天购买次数统计，帮助确定重点品牌资源倾斜。</p>
          </div>
          <span class="dashboard-panel__badge">{{ payload.focus_brands?.length || 0 }} 个品牌</span>
        </div>

        <TrendBarChart
          v-if="payload.focus_brands?.length"
          :items="payload.focus_brands"
          label-key="brand"
          value-key="purchase_count_30d"
        />
        <p v-else class="empty-state">暂无品牌成交数据。</p>
      </article>

      <article class="dashboard-panel">
        <div class="dashboard-panel__header">
          <div>
            <p class="section-kicker">INACTIVE</p>
            <h3>已下架商品</h3>
            <p>展示已下架但仍有库存的商品。</p>
          </div>
          <span class="dashboard-panel__badge">{{ payload.inactive_items?.length || 0 }} 个</span>
        </div>

        <ul v-if="payload.inactive_items?.length" class="strategy-list">
          <li v-for="item in payload.inactive_items" :key="item.product_id" class="strategy-list__item">
            <div class="strategy-list__meta">
              <strong>{{ item.name }}</strong>
              <span>{{ item.category }} / {{ item.brand }}</span>
            </div>
            <p>库存 {{ item.stock }}</p>
          </li>
        </ul>
        <p v-else class="empty-state">暂无已下架商品。</p>
      </article>
    </div>
  </section>
</template>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/merchantOps.js frontend/src/views/merchant/MerchantOpsOverview.vue
git commit -m "feat(frontend): add merchant ops overview module"
```

---

### Task 5: Wire ops overview into MerchantDashboard + tests (frontend)

**Files:**
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
- Modify: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Add state + fetch to dashboard**

In `MerchantDashboard.vue`:

1) Import:

```js
import { deactivateMerchantProduct, fetchMerchantOpsOverview } from '../../api/merchantOps.js'
import MerchantOpsOverview from './MerchantOpsOverview.vue'
```

2) Add state:

```js
const opsOverview = ref({
  summary: { days: 30, revenue: 0, cost: 0, profit: 0 },
  inventory_items: [],
  delist_suggestions: [],
  inactive_items: [],
  focus_brands: []
})
const deactivatingProductId = ref(0)
```

3) In `loadDashboard()` Promise.all, include:

```js
fetchMerchantOpsOverview({ days: 30, low_sales_threshold: 3, brand_top_n: 5 }),
```

And assign:

```js
opsOverview.value = merchantOpsPayload || opsOverview.value
```

4) Add deactivate handler:

```js
async function handleDeactivateProduct(productId) {
  deactivatingProductId.value = productId
  errorMessage.value = ''
  try {
    await deactivateMerchantProduct(productId)
    opsOverview.value = await fetchMerchantOpsOverview({ days: 30, low_sales_threshold: 3, brand_top_n: 5 })
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '下架失败，请稍后重试。'
  } finally {
    deactivatingProductId.value = 0
  }
}
```

5) In overview template section (activeSection === 'overview'), append component under BrandsView:

```vue
<MerchantOpsOverview
  :payload="opsOverview"
  :on-deactivate="handleDeactivateProduct"
  :is-deactivating-id="deactivatingProductId"
/>
```

- [ ] **Step 2: Update unit test mocks**

In `frontend/src/tests/merchant-dashboard.test.js`:

1) Add mock:

```js
vi.mock('../api/merchantOps.js', () => ({
  fetchMerchantOpsOverview: vi.fn(),
  deactivateMerchantProduct: vi.fn()
}))
```

2) In `beforeEach`, set:

```js
fetchMerchantOpsOverview.mockResolvedValue({
  summary: { days: 30, revenue: 12800, cost: 7680, profit: 5120 },
  inventory_items: [{ product_id: 1, name: '轻量跑鞋', category: '运动鞋', brand: '云步', stock: 120, price: 299, cost_price: 179.4, is_active: true }],
  delist_suggestions: [{ product_id: 9, name: '瑜伽弹力带', category: '居家运动', brand: 'FlexPro', purchase_count_30d: 0, stock: 12, price: 89 }],
  inactive_items: [],
  focus_brands: [{ brand: '云步', purchase_count_30d: 6 }]
})
deactivateMerchantProduct.mockResolvedValue({ message: '下架成功', product: { id: 9, is_active: false } })
```

3) Extend the existing “overview panel” assertion:

```js
expect(wrapper.text()).toContain('经营总览（演示口径）')
expect(wrapper.text()).toContain('近30天利润')
expect(wrapper.text()).toContain('5120.00')
expect(wrapper.text()).toContain('建议下架')
expect(wrapper.text()).toContain('销量冠军品牌TOP')
```

- [ ] **Step 3: Add deactivate click test**

Append test:

```js
import { deactivateMerchantProduct, fetchMerchantOpsOverview } from '../api/merchantOps.js'

it('allows merchant to deactivate suggested products', async () => {
  const wrapper = mount(MerchantDashboard, { global: { stubs: { RouterLink: true } } })
  await flushPromises()

  await wrapper.find('button').trigger('click')
  await flushPromises()

  expect(deactivateMerchantProduct).toHaveBeenCalled()
  expect(fetchMerchantOpsOverview).toHaveBeenCalled()
  wrapper.unmount()
})
```

- [ ] **Step 4: Run frontend tests**

From `frontend/`:

```bash
npm test
```

Expected: PASS.

- [ ] **Step 5: Run full backend tests**

From `backend/`:

```powershell
$env:PYTHONPATH='.'; pytest -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/merchant/MerchantDashboard.vue frontend/src/tests/merchant-dashboard.test.js
git commit -m "feat(merchant): show ops overview and support deactivation"
```

---

## Self-Review Checklist

- Spec coverage: 收入/成本/利润、库存清单、建议下架清单（手动下架）、销量冠军品牌TOP、已下架清单。
- No placeholders: 每个任务均给出具体文件路径、代码块与可执行命令。
- Naming consistency: `cost_price`、`fetchMerchantOpsOverview`、`deactivateMerchantProduct`、`/api/merchant/ops/overview`、`/api/merchant/products/<id>/deactivate`。

