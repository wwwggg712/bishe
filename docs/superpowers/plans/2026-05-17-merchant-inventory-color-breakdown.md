# Merchant Inventory Color Breakdown Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在商家端库存相关列表（库存清单/建议下架/已下架）为每个商品生成固定颜色（红蓝黑白灰绿）的库存分布，并在库存行右侧展示以填充留白。

**Architecture:** 后端在 `merchant_ops_service.build_overview()` 生成 `color_breakdown`（确定性随机，sum==stock），前端在 `MerchantOpsOverview.vue` 渲染右侧颜色胶囊并用固定颜色映射上色；补齐 pytest/vitest 覆盖字段与 sum 校验。

**Tech Stack:** Flask + SQLAlchemy, Vue 3, Vitest, Pytest

---

## File Structure

**Backend**
- Modify: `backend/app/services/merchant_ops_service.py`
- Test: `backend/tests/test_merchant_ops.py`

**Frontend**
- Modify: `frontend/src/views/merchant/MerchantOpsOverview.vue`
- Modify: `frontend/src/styles/theme.css`
- Modify: `frontend/src/tests/merchant-dashboard.test.js`

---

### Task 1: 后端—先写 failing 测试（color_breakdown 字段与 sum==stock）

**Files:**
- Modify: `backend/tests/test_merchant_ops.py`

- [ ] **Step 1: 为 ops overview 的 inventory_items/delist_suggestions/inactive_items 增加断言**

在 `test_merchant_ops_overview_returns_profit_and_lists` 末尾追加：
```python
def _sum_color_breakdown(item):
    items = item.get("color_breakdown") or []
    return sum(int(part.get("count") or 0) for part in items)


def _assert_color_breakdown(item):
    assert "color_breakdown" in item
    if int(item.get("stock") or 0) <= 0:
        assert item["color_breakdown"] == []
        return
    assert item["color_breakdown"]
    assert _sum_color_breakdown(item) == int(item.get("stock") or 0)
```

并对 `inventory_items[0]`、若存在则对 `delist_suggestions[0]` 与 `inactive_items[0]` 调用 `_assert_color_breakdown(...)`。

- [ ] **Step 2: 运行后端测试确认失败**

Run:
```bash
cd d:\MyProjects\bishe-finnal\backend
$env:PYTHONPATH='.'; pytest -q tests/test_merchant_ops.py::test_merchant_ops_overview_returns_profit_and_lists
```

Expected:
- FAIL（缺少 color_breakdown 字段）

---

### Task 2: 后端—实现确定性颜色拆分并注入到 payload

**Files:**
- Modify: `backend/app/services/merchant_ops_service.py`

- [ ] **Step 1: 新增颜色拆分函数（确定性、sum==stock）**

在 `MerchantOpsService` 中新增方法：
```python
import math
import random


def _build_color_breakdown(self, product_id: int, stock: int):
    stock = int(stock or 0)
    if stock <= 0:
        return []

    palette = ["红", "蓝", "黑", "白", "灰", "绿"]
    rng = random.Random(int(product_id))
    weights = [rng.random() + 0.05 for _ in palette]
    total_weight = sum(weights) or 1.0

    raw = [(w / total_weight) * stock for w in weights]
    base = [int(math.floor(x)) for x in raw]
    remainder = stock - sum(base)

    order = sorted(range(len(palette)), key=lambda idx: raw[idx] - base[idx], reverse=True)
    for idx in order[: max(remainder, 0)]:
        base[idx] += 1

    items = []
    for color, count in zip(palette, base):
        if count > 0:
            items.append({"color": color, "count": int(count)})
    return items
```

- [ ] **Step 2: 在 overview 列表项上挂载 color_breakdown**

在生成 `inventory_items/inactive_items` 的 `item` dict 中加入：
```python
"color_breakdown": self._build_color_breakdown(product.id, item["stock"])
```

在生成 `delist_suggestions` 的 dict 中加入：
```python
"color_breakdown": self._build_color_breakdown(product.id, int(product.stock or 0))
```

- [ ] **Step 3: 运行 Task 1 测试确认通过**

Run:
```bash
cd d:\MyProjects\bishe-finnal\backend
$env:PYTHONPATH='.'; pytest -q tests/test_merchant_ops.py::test_merchant_ops_overview_returns_profit_and_lists
```

Expected:
- PASS

---

### Task 3: 前端—库存行右侧渲染颜色胶囊（先写 failing 测试）

**Files:**
- Modify: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: 在 mock 的 ops overview payload 中给 inventory_items[0] 增加 color_breakdown**

在 `fetchMerchantOpsOverview.mockResolvedValue({...})` 里把任意一个 `inventory_items` 项加入：
```js
color_breakdown: [
  { color: '红', count: 20 },
  { color: '蓝', count: 50 },
  { color: '黑', count: 50 }
]
```

- [ ] **Step 2: 增加最小断言（预期先失败）**

在 `defaults to overview panel...` 用例中追加：
```js
expect(wrapper.text()).toContain('红 20')
```

- [ ] **Step 3: 运行前端测试确认失败**

Run:
```bash
cd d:\MyProjects\bishe-finnal\frontend
npm test
```

Expected:
- FAIL（页面尚未渲染颜色胶囊）

---

### Task 4: 前端—实现颜色胶囊与样式，并跑全量测试

**Files:**
- Modify: `frontend/src/views/merchant/MerchantOpsOverview.vue`
- Modify: `frontend/src/styles/theme.css`

- [ ] **Step 1: 在库存清单/建议下架/已下架商品行中渲染 color_breakdown**

在 `merchant-product-row` 内，增加一个右侧区域：
```vue
<div v-if="item.color_breakdown?.length" class="merchant-color-breakdown">
  <span
    v-for="part in item.color_breakdown"
    :key="`${item.product_id}-${part.color}`"
    class="merchant-color-pill"
    :data-color="part.color"
  >
    {{ part.color }} {{ part.count }}
  </span>
</div>
```

对 `inventory_items`、`delist_suggestions`、`inactive_items` 三处均加上（复用同一渲染结构）。

- [ ] **Step 2: 补齐样式（固定颜色映射）**

在 `theme.css` 增加：
```css
.merchant-color-breakdown {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.merchant-color-pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 0.86rem;
  font-weight: 800;
  border: 1px solid rgba(15, 23, 42, 0.12);
  background: rgba(255, 255, 255, 0.86);
  color: #0f172a;
}

.merchant-color-pill[data-color="红"] { background: rgba(255, 77, 141, 0.16); color: #9f1239; }
.merchant-color-pill[data-color="蓝"] { background: rgba(142, 197, 255, 0.22); color: #1d4ed8; }
.merchant-color-pill[data-color="黑"] { background: rgba(17, 24, 39, 0.14); color: #111827; }
.merchant-color-pill[data-color="白"] { background: rgba(255, 255, 255, 0.92); color: #0f172a; }
.merchant-color-pill[data-color="灰"] { background: rgba(148, 163, 184, 0.22); color: #334155; }
.merchant-color-pill[data-color="绿"] { background: rgba(52, 211, 153, 0.18); color: #047857; }
```

- [ ] **Step 3: 运行前端全量测试**

Run:
```bash
cd d:\MyProjects\bishe-finnal\frontend
npm test
```

Expected:
- PASS

---

### Task 5: 全量验证

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

