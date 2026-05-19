# 商家经营总览：简报容错 + 三卡并列 + 品牌解释 + 列表密度设计

**目标**
- “今日经营简报”失败不再导致整页失败：基础数据与简报生成解耦，页面始终可用可演示。
- “热销机会 / 滞销风险 / 异常预警”在桌面端并列一行三块，降低页面纵向长度。
- “销量冠军品牌TOP”补充每个品牌对应的 Top1 商品名，并上移到“库存清单”上方、放在经营总览区域下方更靠前位置。
- 库存/下架/已下架商品列表减少右侧留白：提升信息密度与横向填充，保留呼吸感但不空。

---

## 现状与问题

### 1) 今日经营简报与整页加载耦合
- 当前 `MerchantDashboard` 的 `loadDashboard()` 使用 `Promise.all` 同时请求多个接口；任意接口失败会触发 `catch`，导致页面显示“仪表页数据加载失败”，同时简报也显示失败。
- 今日经营简报通过 `fetchMerchantBrief` 调用 `/api/llm/report` 生成；该请求失败时也会触发整页失败路径（因为与基础加载在一个 try/catch 中）。

### 2) 三卡纵向过长
- “热销机会/滞销风险/异常预警”属于小指标卡，适合并列展示以减少滚动。

### 3) 品牌榜缺乏商品解释 + 位置偏后
- “销量冠军品牌TOP”展示品牌购买次数，但用户无法直观知道该品牌主要靠哪个商品贡献。
- 该模块在经营总览中位置偏后，希望上移到库存清单上方，靠近经营总览指标区，便于答辩口径讲述。

### 4) 商品列表留白过大
- 商品列表行中，内容布局倾向“左右两端对齐”，在宽屏下会产生明显右侧空白，信息密度不足。

---

## 方案总览

### A. 简报容错：解耦基础加载与简报生成
- 将 `loadDashboard()` 拆为两段逻辑：
  1) **基础数据加载段**：获取 overview / funnel / region / category / brand / ops / charts / hot&cold / userRfm / strategy / anomalies / actions / userBehavior
  2) **简报生成段**：在基础数据成功后，单独触发 `fetchMerchantBrief`；失败仅更新 `briefSummary` 的失败提示，不影响整页 `errorMessage`
- 文案约定：
  - 基础失败：`errorMessage = '仪表页数据加载失败，请稍后重试。'`
  - 简报失败：`briefSummary = '今日经营简报生成失败（不影响其它数据），请稍后重试。'`，不设置 `errorMessage`

### B. 三卡并列：桌面端 3 列，小屏回落 1 列
- 引入专用容器类（示例：`merchant-brief__highlights`）承载 “热销机会 / 滞销风险 / 异常预警”
- CSS：
  - 桌面端：`grid-template-columns: repeat(3, minmax(0, 1fr))`
  - 小屏断点：回落 `1fr`

### C. 品牌榜增强：补充 Top1 商品名 + 位置上移
- 数据侧：在 `/api/merchant/ops/overview` 的 `focus_brands` 每个元素增加 `top_product_name` 字段
  - 计算口径：近 `days` 天购买次数聚合，按品牌分组；并取品牌下购买次数最高的商品名作为 Top1
- UI 侧：
  - 标题保持“销量冠军品牌TOP”
  - 描述文案增加：`每个品牌展示一个近30天购买贡献最高的代表商品。`
  - 条形榜单每行显示：品牌名（label）+ 购买次数（value）+ Top1 商品名（次要信息）
- 位置调整：将该面板上移到库存清单上方（同一 `merchant-dashboard__layer-grid` 的顺序调整）

### D. 商品列表密度：减少右侧留白、适当拉开行距
- 将商品行内容采用“左图 + 右侧信息块”形式（已存在缩略图结构），并对文本区域使用更合理的宽度占用与换行策略：
  - 让 meta 行（商品名/类目品牌/购买次数等）在宽屏下也能占满宽度，避免右侧空白
  - 适当增加列表项 `gap` 与行内 `line-height`，提升“拉开间距但不留空”的观感

---

## 影响范围（文件与模块）

**前端**
- `frontend/src/views/merchant/MerchantDashboard.vue`
  - 调整 `loadDashboard()` 错误处理与简报生成调用
  - 调整“热销机会/滞销风险/异常预警”渲染结构为并列容器
- `frontend/src/views/merchant/MerchantOpsOverview.vue`
  - 调整面板顺序：品牌榜（增强）上移到库存清单上方
  - 使用 `top_product_name` 展示品牌对应的代表商品
- `frontend/src/components/charts/TrendBarChart.vue`
  - 支持可选的“副标题/次要信息”显示（用于 Top1 商品名）
- `frontend/src/styles/theme.css`
  - 新增 `merchant-brief__highlights` 三列布局
  - 优化商品行/列表项的横向填充与间距

**后端**
- `backend/app/services/merchant_ops_service.py`
  - `focus_brands` 增加 `top_product_name`
- `backend/tests/test_merchant_ops.py`
  - 增加对 `top_product_name` 的断言

---

## 验收标准
- 今日经营简报接口失败时：
  - 页面不出现“仪表页数据加载失败”，除简报外其它模块正常显示
  - 简报区域出现失败提示文案
- 经营总览页中：
  - “热销机会 / 滞销风险 / 异常预警”桌面端同排并列三块
  - “销量冠军品牌TOP”出现在库存清单之上
  - 品牌榜每一行能看到“品牌 + 次数 + Top1 商品名”
  - 库存/下架/已下架列表的右侧留白明显减少，整体更紧凑但不拥挤

