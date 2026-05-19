# 商家库存：颜色分布（A方案不改表）设计

**目标**
- 为商家端“库存清单/建议下架/已下架商品”增加固定 4-6 种颜色（红/蓝/黑/白/灰/绿）的库存分布展示，填充右侧留白区域。
- 不改数据库表结构（A方案），颜色库存为“演示/运营辅助视图”：由后端基于商品总库存生成稳定的拆分结果。
- 展示稳定：同一商品的颜色分布在刷新/重进页面时保持一致（基于 `product_id` 作为确定性种子）。

---

## 数据结构

### 后端输出字段
在 `inventory_items` / `delist_suggestions` / `inactive_items` 的每个商品项上新增：
```json
"color_breakdown": [
  { "color": "黑", "count": 40 },
  { "color": "白", "count": 30 },
  { "color": "红", "count": 20 }
]
```

约束：
- `count` 为非负整数
- `sum(count) == stock`（若 `stock==0`，返回空数组）
- 颜色集合固定为：`红、蓝、黑、白、灰、绿`（可根据 stock 自动裁剪到非零项）

---

## 生成规则（确定性拆分）

### 输入
- `product_id`（确定性种子）
- `stock`（商品总库存）

### 生成流程
- 使用 `random.Random(product_id)` 生成 6 个权重（0~1），归一化为比例
- 计算每色初始分配：`floor(weight/sum * stock)`
- 将剩余 `remainder` 逐个按权重从大到小分配 +1，直到补齐（保证总和等于 stock）
- 过滤 `count==0` 的颜色项，减少噪音

---

## 前端展示

### 展示位置
在库存清单每行的右侧新增颜色分布区域（用于填充现有右侧留白）：
- 展示为 2 行以内的彩色胶囊/小条形：`红 20`、`蓝 50`…
- 颜色用固定映射（不直接信任后端传入颜色值）：
  - 红 `#ff4d8d`
  - 蓝 `#8ec5ff`
  - 黑 `#111827`
  - 白 `#ffffff`（带边框）
  - 灰 `#94a3b8`
  - 绿 `#34d399`

### 交互
- 无需点击；仅展示数量
- 若 `color_breakdown` 为空则不渲染右侧区域（保持简洁）

---

## 影响范围

**后端**
- Modify: `backend/app/services/merchant_ops_service.py`（为列表项补 `color_breakdown`）
- Modify: `backend/tests/test_merchant_ops.py`（断言字段存在且满足 sum==stock）

**前端**
- Modify: `frontend/src/views/merchant/MerchantOpsOverview.vue`（渲染右侧颜色分布）
- Modify: `frontend/src/styles/theme.css`（颜色胶囊/布局样式）
- Modify: `frontend/src/tests/merchant-dashboard.test.js`（最小断言：渲染“颜色”区域或存在对应文案/数据-testid）

---

## 验收标准
- 库存清单每行右侧留白明显减少，出现颜色分布胶囊（红/蓝/黑/白/灰/绿）
- 任意一个商品：颜色数量求和等于该商品 `stock`
- 多次刷新页面，同一商品颜色分布不跳变（确定性）

