## 目标

在不引入新依赖、不增加训练流程的前提下，将系统的商品热度分（hot_score）从“纯加权累计”升级为“带时间衰减的加权累计”，使热销/冷门榜更贴近“近期热度”，提升演示与业务解释性。

## 范围

- 影响范围：商家端热销/冷门商品榜（后端 AnalyticsService 计算 hot_score 的位置）
- 改动策略：直接替换原 hot_score（前端榜单立刻变化），不新增并行字段

## 非目标

- 不引入协同过滤、矩阵分解等训练型模型
- 不改变数据库表结构
- 不改变 API 返回字段结构（仍返回 hot_score 字段）

## 算法定义

### 行为权重

沿用现有权重：

- view=1
- click=2
- favorite=3
- cart=5
- purchase=8

### 时间衰减

以“当前日志集合的最新时间”为参考，对每条日志按距离最新时间的小时差进行指数衰减：

- delta_hours = (latest_ts - log_ts).total_seconds() / 3600
- decay = 0.5 ** (delta_hours / half_life_hours)
- contribution = action_weight * decay
- hot_score = Σ contribution

默认 half_life_hours = 24（含义：距离最新时间 24 小时的行为贡献减半）。

## 边界与降级

- 若日志为空：hot_score=0
- 若某条日志 timestamp 缺失/解析失败：该条日志 decay=1（不衰减）
- 若无法计算 latest_ts（全部 timestamp 解析失败）：退化为原始加权累计（相当于 decay 恒为 1）

## 实现点（后端）

- 文件：backend/app/services/analytics_service.py
- 修改点：
  - 在 _build_product_scores 内：
    - 预扫描 scoped_logs，计算 latest_ts（datetime.fromisoformat）
    - 累加 hot_score 时将 weight 替换为 weight * decay
    - hot_score 输出保留为数值，建议 round 到 2 位小数（或保持 float）

## 验收标准

- 热销榜/冷门榜仍能正常返回 items，且 hot_score 对“近期行为”更敏感
- 不改动前端即可看到榜单变化（同一数据集下，越新的商品热度更高）
- 原有测试通过；若存在与 hot_score 精确值强绑定的断言，需要调整为“结构/排序/范围”类断言

