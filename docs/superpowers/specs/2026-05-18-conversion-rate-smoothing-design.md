## 目标

对系统中的“成交转化率”做最轻量的贝叶斯/拉普拉斯平滑，降低小样本下转化率极端波动，使看板与异常判断更稳定、更像工程化算法。

## 范围

- 商家总览：overview.totals.purchase_rate
- 每日聚合：DailyProductMetric.conversion_rate（由 AnalyticsService.build_daily_product_metrics 计算）

## 非目标

- 不引入训练流程与模型
- 不改变 API 字段结构（仍返回 purchase_rate / conversion_rate）
- 不改变数据库结构

## 平滑公式

### 原始转化率

- purchase_rate = purchase_count / view_count

### 平滑后转化率（方案 A）

- purchase_rate = (purchase_count + α) / (view_count + β)
- 取值：α=1，β=2
- 当 view_count=0：purchase_rate 固定为 0（避免无曝光却产生 0.5 的不合理值）

解释：等价于一个很弱的先验（“2 次曝光、1 次成交”的先验），可抑制小样本的 0/1 极端。

## 边界与一致性

- 保持现有小数处理：
  - overview.totals.purchase_rate 继续 round 到 4 位小数
  - daily_metric.conversion_rate 保持 float（必要时可 round 到 4 位小数，本文以现状为准）

## 实现点

- backend/app/services/analytics_service.py
  - build_overview：替换 purchase_rate 计算
  - build_daily_product_metrics：替换 conversion_rate 计算

## 测试与验收

- 新增/调整后端测试用例，覆盖：
  - view_count=1, purchase_count=1 的平滑后结果应为 0.6667
  - view_count=0 时 purchase_rate=0
- 后端全量测试通过，前端测试不受影响（字段未变）

