# 任务管理集中、日志清理与 DeepSeek AI 分析设计（A 版）

## 1. 目标

在不引入额外中间件的前提下，增强系统在答辩场景的“可解释性、可控性与可回滚性”：

1. 管理端将“日志生成、手动清理、任务触发”集中到任务管理页，日志预览页只负责查看
2. 行为日志支持手动清理：保留最新 N 条，避免无限增长
3. 用户端与商家端 AI 分析支持调用 DeepSeek（OpenAI 兼容接口），并在失败时给出明确错误原因（不再静默回退）
4. 推荐中心理由更可验证：优先使用可追溯的行为证据（类目偏好、热度分、用户交互）；DeepSeek 仅做解释与建议生成

## 2. 范围

### 2.1 本次要做

1. 管理端页面结构调整
2. 新增行为日志清理 API（保留最新 N 条）
3. DeepSeek 用户端与商家端 AI 分析接入与错误透传
4. 推荐理由升级为“证据型理由”（不改变推荐主逻辑，只增强解释字段）

### 2.2 本次不做

1. Kafka / ELK / ES 等日志中间件引入
2. 复杂日志检索（多条件筛选、全文搜索、导出）
3. 离线聚合体系重构（保留现有接口，不强制依赖定时任务）

## 3. 现状问题

1. 日志预览页承载了过多说明与操作入口，用户会误以为“必须在这里点任务才能生效”，且偏离“查看日志长什么样”的目的
2. LLM 调用失败会被吞掉并静默回退为 internal 文案，用户难以判断是否真正接入 DeepSeek
3. 行为日志持续生成后会快速增长，缺少清理机制影响演示与维护

## 4. 方案总览

### 4.1 页面职责重划分

1. 任务管理页（Admin Tasks）
   - 生成日志：立即生成一批 / 快速生成 2000 条
   - 日志清理：保留最新 N 条（手动）
   - 任务执行：仅保留“立即执行”入口（不强调定时）
2. 原始日志预览页（Admin Log Preview）
   - 只做“分页查看日志列表 + 基础统计（总量/最新时间）”
   - 保留“刷新”与分页控件
   - 不再放置生成/清理/任务控制入口
   - 不在该页面展示算法链路、生成说明与依赖关系内容

### 4.2 日志清理策略（保留最新 N 条）

新增管理员 API：

- `POST /api/admin/logs/cleanup`
- 入参：`keep_last`（int，1~500000，默认建议 20000）
- 行为：
  - 按 `timestamp desc, id desc` 排序保留最新 N 条
  - 删除其余记录
- 出参：
  - `deleted_count`
  - `kept_count`
  - `total_before`

### 4.3 DeepSeek 用户端与商家端 AI 分析（OpenAI 兼容）

后端继续使用 `/api/llm/report`，但增强为：

1. 显式识别 provider 配置是否完整
2. provider 调用失败时返回：
   - `mode=error`
   - `error_message`
   - `provider/model/base_url`（不包含密钥）
3. provider 调用成功时返回：
   - `mode=provider`
   - `summary`
   - `provider=model`

环境变量约定（由用户在 `backend/.env` 填写，不提交）：

- `LLM_PROVIDER=deepseek`
- `LLM_API_KEY=...`
- `LLM_BASE_URL=https://api.deepseek.com/v1/chat/completions`
- `LLM_MODEL=deepseek-chat`

调用约定：

1. 商家端调用：`scene=merchant`，输入为结构化经营分析结果（总览/漏斗/热销冷门/异常/分层等）
2. 用户端调用：`scene=customer`，输入为结构化画像与推荐结果（类目偏好/价格带/活跃时段/推荐候选等）

返回结构统一：

- `mode ∈ {provider, fallback, error}`
- `summary`：AI 输出（fallback/error 场景也给出可展示文本或错误信息）
- `provider/model`：便于前端显示“是否接入成功”

### 4.4 推荐理由升级（证据型）

推荐接口结构不变（`/api/recommendations/me`），但每条 item 的 reason 建议升级为“可追溯证据句”：

1. 类目偏好：该用户在 `customer_page` 的类目得分（按行为权重累计）
2. 热度分：该商品全局热度分（按行为权重累计）
3. 去重与安全：不展示其他用户隐私，仅展示聚合分值

AI（可选）：

- 若 `LLM_PROVIDER` 可用，可对证据句做“润色”输出一段更自然的中文解释，但不替代证据字段

## 5. 数据与接口

### 5.1 行为日志数据源

行为日志统一来自 MySQL：

- `behavior_logs`

所有分析、画像、推荐、异常等接口继续使用“读表→转换为 dict→计算”的方式，不要求先跑定时任务。

### 5.2 管理端接口

1. `GET /api/admin/logs/preview?page=&page_size=`
2. `POST /api/admin/logs/cleanup { keep_last }`

## 6. 错误处理与安全

1. 禁止在后端日志或响应中输出 `LLM_API_KEY`
2. `.env` 永远不进入 Git 仓库（通过 `.gitignore` 保证）
3. provider 失败时给出明确错误（HTTP 状态码与 message），前端提示用户检查 key/余额/网络

## 7. 验收标准

1. 管理端任务页可执行：生成 2000 条、保留最新 N 条清理
2. 原始日志预览页只展示：分页、统计、列表，不再出现“生成/清理”按钮
3. 配置 DeepSeek 后，商家 AI 建议展示 `mode=provider` 且不再显示 internal fallback
   - 用户端 AI 解释同样满足该要求
4. 未配置或配置错误时，前端能看到清晰错误提示，而不是默默回退
5. 后端 pytest、前端 vitest 全量通过
