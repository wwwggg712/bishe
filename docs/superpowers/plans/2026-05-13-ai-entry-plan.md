# AI Entry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add visible AI entry points for merchant-side business analysis and customer-side recommendation explanation.

**Architecture:** Extend the existing `/api/llm/report` fallback so it understands `scene=merchant` and `scene=customer`, then add one button-triggered AI card to `MerchantDashboard.vue` and one to `CustomerHome.vue`. Reuse the current analytics and recommendation data already loaded on each page to assemble request payloads without introducing new data pipelines.

**Tech Stack:** Flask, Vue 3, Vitest, Pytest

---

### Task 1: Add failing tests for LLM scenes and page entry points

**Files:**
- Modify: `backend/tests/test_llm_report.py`
- Modify: `frontend/src/tests/merchant-dashboard.test.js`
- Modify: `frontend/src/tests/customer-home.test.js`

- [ ] **Step 1: Add failing backend tests**
- [ ] **Step 2: Add failing merchant and customer page assertions**
- [ ] **Step 3: Run focused tests and verify they fail**

### Task 2: Extend backend fallback responses by scene

**Files:**
- Modify: `backend/app/services/llm_service.py`
- Test: `backend/tests/test_llm_report.py`

- [ ] **Step 1: Implement merchant scene fallback**
- [ ] **Step 2: Implement customer scene fallback**
- [ ] **Step 3: Run backend tests and verify they pass**

### Task 3: Add merchant AI business analysis card

**Files:**
- Modify: `frontend/src/api/analytics.js`
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
- Test: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Add merchant AI API wrapper**
- [ ] **Step 2: Add button, loading state, and result card**
- [ ] **Step 3: Run merchant test and verify it passes**

### Task 4: Add customer AI explanation card

**Files:**
- Modify: `frontend/src/api/recommendation.js`
- Modify: `frontend/src/views/customer/CustomerHome.vue`
- Test: `frontend/src/tests/customer-home.test.js`

- [ ] **Step 1: Add customer AI API wrapper**
- [ ] **Step 2: Add button, loading state, and result card**
- [ ] **Step 3: Run customer test and verify it passes**

### Task 5: Verify regressions

**Files:**
- Test: `backend/tests/test_llm_report.py`
- Test: `frontend/src/tests/merchant-dashboard.test.js`
- Test: `frontend/src/tests/customer-home.test.js`

- [ ] **Step 1: Run focused tests**
- [ ] **Step 2: Run backend full suite**
- [ ] **Step 3: Run frontend full suite**
