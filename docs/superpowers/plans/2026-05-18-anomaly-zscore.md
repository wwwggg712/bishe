# Anomaly Z-Score (Product View Spike) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将“商品浏览量突增”异常触发条件从固定倍率阈值改为 z-score（Poisson 近似）阈值 z>=2.0，并在输出中增加 z_score 字段。

**Architecture:** 在 PredictionService.build_anomalies 内计算 baseline/current 的 z_score，并用 z_score 替换 ratio>=2 的触发条件；severity 保持现有 ratio 分档以兼容筛选；通过新增测试验证字段与阈值生效。

**Tech Stack:** Python, Flask, pytest

---

### Task 1: 写失败测试（RED）

**Files:**
- Modify: `d:/MyProjects/bishe-finnal/backend/tests/test_intelligence.py`

- [ ] **Step 1: 更新现有异常测试，要求返回 z_score 且 z_score>=2.0**

在 `test_prediction_anomalies_grade_severity_against_baseline` 中增加断言：

```python
assert "z_score" in anomaly
assert anomaly["z_score"] >= 2.0
```

- [ ] **Step 2: 运行该测试并确认失败**

Run:

```bash
python -m pytest tests/test_intelligence.py::test_prediction_anomalies_grade_severity_against_baseline -q
```

Expected: FAIL（z_score 字段尚未实现）

---

### Task 2: 实现 z-score 并替换触发条件（GREEN）

**Files:**
- Modify: `d:/MyProjects/bishe-finnal/backend/app/services/prediction_service.py`

- [ ] **Step 1: 添加 z-score 计算**

实现 Poisson 近似 z-score：

```python
z = (current_views - baseline_views) / sqrt(max(baseline_views, 1))
```

并在异常 item 中加入：

```python
"z_score": round(z, 2)
```

- [ ] **Step 2: 替换触发条件**

把“商品浏览量突增”触发条件从：

```python
traffic_ratio >= 2
```

替换为：

```python
z >= 2.0
```

并保留：

```python
current_views >= 3
```

- [ ] **Step 3: 运行单测并确认通过**

Run:

```bash
python -m pytest tests/test_intelligence.py::test_prediction_anomalies_grade_severity_against_baseline -q
```

Expected: PASS

---

### Task 3: 全量回归

**Files:**
- Test: `d:/MyProjects/bishe-finnal/backend/tests/*`
- Test: `d:/MyProjects/bishe-finnal/frontend/src/tests/*`

- [ ] **Step 1: 后端全量测试**

Run:

```bash
python -m pytest -q
```

Expected: PASS

- [ ] **Step 2: 前端测试**

Run:

```bash
npm test
```

Expected: PASS

