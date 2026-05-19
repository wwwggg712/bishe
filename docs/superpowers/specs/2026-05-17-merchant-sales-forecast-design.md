# 商家爆火商品销量预测（30天）设计

**目标**
- 在商家端提供“爆火商品未来30天销量预测”，同时输出：
  - 未来30天每日销量折线预测
  - 未来30天总销量预测（含上下界区间）
- 口径：**店铺口径**（仅统计当前登录商家的销量），且**自动选 Top1 爆火商品**（无需手动选商品）。
- 演示稳定：即使预测计算/数据不足，也要给出明确兜底输出，避免空白或无限 loading。

---

## 数据与口径

### 输入数据源
- `BehaviorLog`：按天聚合 `action_type == "purchase"` 的计数，过滤 `merchant_id == 当前商家`，可选过滤 `product_id == 目标商品`。
- 时间窗口：
  - 历史：默认最近30天（用于展示“历史对比折线”与估计趋势）
  - 选品：默认最近7天（用于选出 Top1 爆火商品）

### “爆火商品”自动选择规则
- 优先规则：最近7天购买次数（purchase）最高的商品
- 兜底：若最近7天 purchase 全为0，则降级为最近30天 purchase 最高；再不行则返回“暂无可预测商品”的兜底结构

---

## 预测模型（无需额外 ML 依赖）

### 输出形式
- 未来30天每日预测值：`forecast[i].value`（非负整数）
- 未来30天总销量：`forecast_total.value`
- 区间：`forecast_total.lower` / `forecast_total.upper`

### 预测核心思路（可解释、可答辩）
- **基线**：近7天日均销量 `avg7`
- **趋势修正**：近30天与近7天均值比值、或最近两周均值差形成轻量趋势项 `trend`
- **衰减约束**：爆火商品常见回落，给未来天数增加衰减系数 `decay(day)`，防止预测离谱
- **波动区间**：用历史日销量的简单波动（如近30天标准差或 IQR 简化）给出上下界

### 兜底
- 若历史 purchase 数据不足（比如近30天全0）：
  - 直接返回“预测为0”的折线与总量，`confidence = "low"`
  - `explain` 说明“历史购买数据不足”

---

## API 设计

### 新增接口
- `GET /api/merchant/prediction/sales-forecast?days=30`
- 权限：仅商家角色可访问

### 返回结构（示例）
```json
{
  "product": {
    "product_id": 1,
    "name": "露营保温水壶",
    "brand": "云步",
    "category": "户外装备",
    "price": 119.0,
    "image_url": "https://..."
  },
  "history": [
    { "date": "2026-04-18", "value": 0 },
    { "date": "2026-04-19", "value": 2 }
  ],
  "forecast": [
    { "date": "2026-05-18", "value": 3 },
    { "date": "2026-05-19", "value": 3 }
  ],
  "forecast_total": {
    "value": 86,
    "lower": 62,
    "upper": 112
  },
  "confidence": "medium",
  "explain": [
    "近7天日均销量 3.4",
    "近30天趋势：近期均值高于长期均值，保持温和增长预期",
    "按爆火回落规律加入衰减，避免预测过于乐观"
  ]
}
```

### 失败/兜底返回
- 不返回 500 造成页面崩；返回 200 + 明确兜底字段：
  - `product: null`
  - `history/forecast: []`
  - `forecast_total: { value: 0, lower: 0, upper: 0 }`
  - `confidence: "low"`
  - `explain: ["暂无可预测商品：近7/30天购买数据不足"]`

---

## 前端展示（商家端）

### 展示位置（推荐）
- 商家“经营总览”增加一张模块卡：`爆火商品销量预测（30天）`
- 内容：
  - 顶部：商品缩略图 + 商品名 + 类目/品牌 + “预测总销量（区间）”
  - 中间：折线图（历史30天 + 未来30天两条线或同一图不同颜色）
  - 底部：`explain` 解释条目（3-5条）

### 交互与稳定性
- 页面加载时自动请求接口
- loading 最长 2-3 秒后仍无结果要展示兜底文案（与后端兜底配合，避免空白）

---

## 代码落点（预期）

**后端**
- `backend/app/routes/merchant_prediction.py`（新增 blueprint 路由，挂载 `/api/merchant/prediction`）
- `backend/app/services/merchant_prediction_service.py`（新增：选品 + 聚合 + 预测 + 解释）
- 复用模式：参考 `merchant_charts.py` 的 `func.date(created_at)` 聚合写法

**前端**
- `frontend/src/api/merchantPrediction.js`（新增：请求 forecast 接口）
- `frontend/src/views/merchant/MerchantDashboard.vue`（overview 区插入预测卡）
- `frontend/src/components/charts/`：
  - 复用现有折线图组件（若已有），否则新增一个轻量折线展示组件
- `frontend/src/styles/theme.css`：预测卡样式与现有 dashboard-panel 对齐

**测试**
- 后端：pytest 新增 `test_merchant_prediction_sales_forecast.py`
  - 有 purchase 数据时返回结构完整
  - 无 purchase 数据时走兜底结构
- 前端：vitest 新增/扩展 merchant-dashboard 测试
  - mock 预测接口并断言卡片渲染与兜底渲染

---

## 验收标准
- 商家端经营总览能看到“爆火商品销量预测（30天）”，无需手动选商品即可出结果
- 折线与总量同时存在，且解释项可用于答辩讲述“依据是什么”
- 外部服务不可用/数据不足时也有稳定兜底输出，页面不崩不空

