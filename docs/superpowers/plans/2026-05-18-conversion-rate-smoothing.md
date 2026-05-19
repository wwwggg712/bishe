# Conversion Rate Smoothing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 对 purchase_rate / conversion_rate 应用 α=1、β=2 的平滑公式，并在 view_count=0 时保持为 0，提升小样本稳定性。

**Architecture:** 在 AnalyticsService 的两个计算点替换转化率公式；保持 API 字段结构不变；通过新增/调整测试用例保障行为变更正确且可回归。

**Tech Stack:** Python, Flask, pytest

---

### Task 1: 写测试（RED）

**Files:**
- Modify: `d:/MyProjects/bishe-finnal/backend/tests/test_analytics.py`

- [ ] **Step 1: 新增测试，断言总览 purchase_rate 为平滑值**

在 `test_overview_returns_core_metrics` 之外新增一个最小用例，构造 `view_count=1, purchase_count=1`，期望：

```python
assert payload["totals"]["purchase_rate"] == 0.6667
```

- [ ] **Step 2: 运行该测试并确认失败**

Run:

```bash
python -m pytest tests/test_analytics.py -q
```

Expected: FAIL（因为当前实现仍是 1/1=1.0）

---

### Task 2: 实现平滑（GREEN）

**Files:**
- Modify: `d:/MyProjects/bishe-finnal/backend/app/services/analytics_service.py`

- [ ] **Step 1: 修改 build_overview 的 purchase_rate 计算**

替换为：

```python
purchase_rate = (purchase_count + 1) / (view_count + 2) if view_count else 0
```

并保留现有 `round(purchase_rate, 4)`。

- [ ] **Step 2: 修改 build_daily_product_metrics 的 conversion_rate 计算**

替换为：

```python
payload["conversion_rate"] = (purchase_count + 1) / (view_count + 2) if view_count else 0.0
```

- [ ] **Step 3: 运行测试并确认新增测试通过**

Run:

```bash
python -m pytest tests/test_analytics.py -q
```

Expected: PASS

---

### Task 3: 回归验证

**Files:**
- Test: `d:/MyProjects/bishe-finnal/backend/tests/*`
- Test: `d:/MyProjects/bishe-finnal/frontend/src/tests/*`

- [ ] **Step 1: 运行后端全量测试**

Run:

```bash
python -m pytest -q
```

Expected: PASS

- [ ] **Step 2: 运行前端测试（字段未变，预期全绿）**

Run:

```bash
npm test
```

Expected: PASS

