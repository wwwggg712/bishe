## 目标

将“商品浏览量突增”异常检测从固定倍率阈值（ratio>=2）升级为动态阈值（z-score 简化版），使预警更符合统计意义、更像算法，同时保持接口结构稳定、演示可控。

## 范围

- 后端：PredictionService.build_anomalies
- 仅先覆盖：商品维度的“浏览量突增”检测逻辑

## 非目标

- 不引入机器学习训练流程
- 不引入外部依赖库
- 不改动前端页面逻辑（允许后端新增字段，前端忽略不影响）

## 现状

当前“商品浏览量突增”依赖固定倍率阈值：

- change_ratio = current_views / baseline_views
- 触发条件：current_views >= 3 且 change_ratio >= 2（并在某些类型里额外约束转化率）

该方式对不同基线规模不够自适应：基线小容易误报，基线大又可能漏报。

## 升级方案（Poisson 近似的简化 z-score）

把“浏览量”当作计数型数据，使用 Poisson 近似：方差≈均值，因此标准差可用 sqrt(baseline_views) 近似。

- baseline = baseline_views
- current = current_views
- z = (current - baseline) / sqrt(max(baseline, 1))

阈值：z >= 2.0

最小样本量：current_views >= 3（保留，避免噪声）

## 输出与兼容性

- 保留原有字段：
  - baseline、baseline_value、current_value、delta、change_ratio、severity、reason
- 新增字段：
  - z_score（float，建议 round 到 2 位）
- severity 继续沿用当前 ratio 的分档逻辑（不改变现有 high/medium/low 口径与筛选效果）

## 验收标准

- /api/prediction/anomalies 返回的“商品浏览量突增”类异常包含 z_score 字段
- 触发条件由 ratio>=2 替换为 z>=2.0（同时保留 current_views>=3）
- 现有 severity=high 过滤仍可用，且不破坏现有接口结构
- 后端与前端测试全绿

