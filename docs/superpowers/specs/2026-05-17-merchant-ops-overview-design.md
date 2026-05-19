# 商家经营总览增强（演示口径）设计

## 背景

当前系统的“经营分析”主要基于 `BehaviorLog`（用户行为日志）进行 PV/UV、漏斗、热度等统计；缺少商家后台常见的“利润/库存/下架/重点品牌”视角。由于项目没有订单表，本次以“演示口径”实现：用 `purchase` 行为次数近似成交笔数，并以商品的 `price` 与新增的 `cost_price` 估算利润。

## 目标

- 商家端经营总览展示近30天：
  - 收入（估算）、成本（估算）、利润（可为负）
  - 库存清单（存了哪些货、库存占用）
  - 低销量商品建议下架清单（仅建议，手动确认后下架）
  - 销量冠军品牌 TOP（按购买次数）

## 非目标

- 不实现完整订单/支付/退款体系（不引入 `Order/OrderItem` 等表）。
- 不做自动下架（只做建议列表与手动下架）。
- 不做复杂库存流水、多仓、SKU 规格拆分。

## 数据与口径

### 新增字段

- `Product.cost_price`（商品成本价，Numeric）
  - 默认值：`price * 0.6`（用于演示，可后续再支持后台调整）

### 统计窗口

- 默认 `days=30`（可通过 query 参数修改）
- 仅统计当前商家的商品范围（按 `merchant_id` 过滤）

### 购买次数

- `purchase_count(product)` = 统计窗口内 `BehaviorLog.action_type == "purchase"` 的次数
- `brand_purchase_count(brand)` = 品牌下所有商品的 purchase 次数求和

### 收入/成本/利润（估算）

- `revenue` = Σ( purchase_count(product) * product.price )
- `cost` = Σ( purchase_count(product) * product.cost_price )
- `profit` = revenue - cost

### 低销量下架建议

- 规则：近30天购买次数 `< 3` 的在售商品（`is_active == True`）进入“建议下架”
- 展示字段：商品名、品类、品牌、近30天购买次数、库存、价格
- 操作：点击“下架”将该商品 `is_active` 置为 `False`

## API 设计

新增蓝图（或复用现有 analytics 蓝图也可，但建议独立避免混淆）：

### 获取商家经营总览

- `GET /api/merchant/ops/overview?days=30&low_sales_threshold=3&brand_top_n=5`
- 权限：JWT 且 role=merchant
- 返回（示意）：
  - `summary`: `{ days, revenue, cost, profit }`
  - `inventory_items`: `[{ product_id, name, category, brand, stock, price, cost_price, is_active }]`
  - `delist_suggestions`: `[{ product_id, name, category, brand, purchase_count_30d, stock, price }]`
  - `inactive_items`: `[{ product_id, name, category, brand, stock, price, deactivated_at? }]`
  - `focus_brands`: `[{ brand, purchase_count_30d }]`（按购买次数降序取 TOP N）

### 手动下架商品

- `POST /api/merchant/products/<product_id>/deactivate`
- 权限：JWT 且 role=merchant，且商品属于当前商家
- 行为：设置 `Product.is_active = False`
- 返回：`{ message, product: {...} }`

## 前端设计（商家端）

在 `MerchantDashboard` 增加“经营总览”区域（不替换现有 PV/UV/漏斗等统计，作为新增模块）：

- 卡片（3个）：
  - 近30天收入（估算）
  - 近30天成本（估算）
  - 近30天利润（估算，可为负）
- 面板（3块）：
  - 库存清单：按库存（stock）降序或按库存占用（stock * cost_price）降序
  - 建议下架：purchase<3 的在售商品列表（每行一个“下架”按钮）
  - 销量冠军品牌TOP：柱状图（brand vs purchase_count_30d）

交互与刷新：

- 沿用现有“自动刷新”模式，默认 60s 刷新一次；支持手动刷新。

## 约束与边界

- 没有 purchase 日志时：收入/成本/利润均为 0，列表为空，页面显示“暂无成交数据”。
- 成本字段缺失：由迁移/默认值保证存在；若为 null，当作 `price * 0.6` 兜底。
- 下架操作幂等：已下架重复点击提示“已下架”。

## 测试策略

- 后端：
  - 新增接口单测：overview 返回字段完整、利润计算正确、阈值筛选正确
  - 下架接口单测：权限校验、只能下架自己的商品、状态变更生效
- 前端：
  - dashboard 测试：渲染收入/利润卡片、渲染建议下架列表、点击下架按钮触发 API 并刷新

## 验收标准

- 商家端可以看到：收入/成本/利润（估算）、库存清单、建议下架清单、销量冠军品牌 TOP
- 点“下架”后该商品进入“已下架”列表，并且推荐/可售逻辑不再包含该商品（`is_active=false` 生效）

