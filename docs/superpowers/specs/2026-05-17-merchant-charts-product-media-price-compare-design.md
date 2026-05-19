# 商家图表 + 商品图片/价格 + 用户端比价（演示版）设计

## 背景

现有系统商家端以列表/数字卡片为主，直观性不足；用户端商品展示偏“文本化”，缺少图片与价格；同时希望增加“对比其他平台价格”的拓展功能，用于答辩展示系统扩展性与智能决策能力。

本设计遵循两个原则：

- 演示稳定：不依赖真实平台抓取（合规与稳定性风险），比价走“演示报价”。
- 口径一致：所有趋势与占比统计优先使用 `BehaviorLog.created_at` 做时间窗口，避免依赖定时聚合是否执行。

## 目标

1) 商家端新增更直观的图表：
- 漏斗：view→click→favorite→cart→purchase（沿用现有漏斗组件）
- 品类/品牌占比：Top5 + 其它（饼图）
- 近7天趋势：view/purchase 折线图

2) 商品展示更真实：
- 用户端推荐/列表卡片展示商品图片 + 价格 + 品牌/品类

3) 用户端比价功能（演示版）：
- 对比平台：抖音、京东、拼多多、得物
- 返回各平台报价、最低价平台、省钱金额、省钱建议

## 非目标

- 不实现真实抓取/爬虫获取京东/抖音/拼多多/得物实时价格
- 不实现完整订单口径（比价只围绕“商品标价”对比）
- 不实现复杂商品图册/多图/规格 SKU

## 数据与模型改动

### Product 新增字段

- `Product.image_url`：商品主图 URL（String）
  - 演示数据默认值：使用稳定的文本生成图片接口 URL（对每个商品生成固定 prompt）

### 推荐/列表返回字段补全

当前用户端推荐主要来自推荐服务，返回 `product_id/product_name/category/reason`。为支持图片与价格展示，需要补充：

- `price`
- `brand`
- `image_url`

补全方式：在推荐服务输出时按 `product_id` 查询 `Product` 表合并字段，避免在 `BehaviorLog` 里扩字段。

## 商家端图表设计

### 图表类型

- 漏斗图：沿用现有 `FunnelChart.vue`
- 品类/品牌占比：新增 ECharts 饼图（Pie）
- 近7天趋势：新增 ECharts 折线图（Line）

### 组件设计

- 新增通用 `EChartView` 组件：
  - 输入：`option`（ECharts option 对象）、`height`、`theme`（可选）
  - 生命周期：mounted init、unmounted dispose、window resize 触发 resize
- 视图层组件：
  - `SharePieChart`：品类/品牌占比饼图（复用 `EChartView`）
  - `TrendLineChart`：近7天趋势折线图（复用 `EChartView`）

### 后端接口

新增商家图表数据接口（JWT role=merchant）：

1) `GET /api/merchant/charts/share?top_n=5`
- 返回：
  - `category_share`: `[{ name, value }]`（name=品类，value=行为量或 purchase 量）
  - `brand_share`: `[{ name, value }]`（name=品牌中文展示，value=purchase 次数）
- 口径：
  - 品类占比：按窗口内 `BehaviorLog.category` 聚合（可用行为总量或 purchase，总量更“热度”，purchase 更“销量”，本设计默认用行为总量）
  - 品牌占比：按窗口内 purchase 聚合（更符合“品牌销量”）

2) `GET /api/merchant/charts/trend?days=7`
- 返回：
  - `days`: `["2026-05-11", ...]`
  - `series`: `[{ name: "浏览", data: [...] }, { name: "购买", data: [...] }]`
- 口径：按 `created_at` 分组到自然日（UTC 或本地统一一套），分别统计 view 次数与 purchase 次数。

## 用户端商品卡片增强

### 页面

- `CustomerHome.vue` 推荐列表
- `RecommendationView.vue` 推荐中心列表

### 展示元素

- 商品图片（image）
- 商品名（name）
- 品类/品牌 tag
- 价格（price）

### 数据来源

推荐接口返回补齐 `price/brand/image_url` 后直接渲染。

## 用户端比价功能（演示版）

### 页面与入口

新增页面 `PriceCompareView.vue`：

- 可从用户端首页的“推荐商品”列表新增按钮进入：
  - “比价”按钮：跳转到 `/customer/price-compare?product_id=...`

### 后端接口

新增接口：

- `GET /api/price-compare?product_id=<id>`

返回（示意）：

- `product`: `{ product_id, name, price, brand, category, image_url }`
- `offers`: `[{ platform, price, delivery_hint, coupon_hint }]`
  - platform ∈ { 抖音, 京东, 拼多多, 得物 }
- `best`: `{ platform, price, saving }`
- `advice`: 一段可读建议（例如“拼多多当前更便宜，预计可省 12.5 元；若追求正品保障可选得物”）

### 演示报价生成规则

为保证“每次演示一致”：

- 基于 `product_id` 做确定性扰动（非随机）：
  - 对每个平台设定一个固定系数区间（如 0.88~1.15），并用 `product_id` 映射到区间内的一个值
  - 得到 `external_price = base_price * factor`，并四舍五入到 0.01
- 可附加“平台侧优势文案”：
  - 京东：次日达/自营
  - 拼多多：百亿补贴
  - 抖音：直播券
  - 得物：鉴别保障

## 权限与安全

- 商家图表接口：仅 merchant 角色可访问
- 比价接口：customer 角色可访问（或允许匿名也可，本设计默认 customer）
- 不在日志/接口响应中回显敏感 key

## 测试策略

后端：
- 新增 `test_merchant_charts.py`：验证 share/trend 返回结构、长度、top_n 生效
- 新增 `test_price_compare.py`：验证 offers 平台齐全、best 计算正确、同 product_id 输出稳定一致
- 更新 `seed_demo_data`：确保 `image_url` 不为空

前端：
- 更新 CustomerHome/RecommendationView 测试：断言图片与价格出现
- 新增 price compare view 测试：mock API 返回并断言对比列表渲染、最低价提示与建议渲染

## 验收标准

- 商家端能在同一页看到：漏斗图 + 品类/品牌占比饼图 + 近7天趋势折线图
- 用户端推荐商品卡片展示：图片 + 价格 + 品类/品牌
- 用户端比价页可以对同一商品展示：抖音/京东/拼多多/得物报价、最低价平台、省钱金额与建议

