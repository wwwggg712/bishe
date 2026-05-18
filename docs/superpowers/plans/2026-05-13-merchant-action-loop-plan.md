# Merchant Action Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add merchant-side action recording so analytics results can be turned into visible operational actions on the dashboard.

**Architecture:** Create a small `MerchantAction` persistence model and expose merchant-only strategy endpoints for recording and summarizing actions. Wire dashboard buttons for hot, cold, and risk items to these endpoints, then render inline action status plus a summary panel for today’s executed actions.

**Tech Stack:** Flask, Flask-SQLAlchemy, Vue 3, Vitest, Pytest

---

### Task 1: Add failing tests for merchant actions

**Files:**
- Create: `backend/tests/test_merchant_actions.py`
- Modify: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Write failing backend tests**
- [ ] **Step 2: Write failing frontend interaction assertions**
- [ ] **Step 3: Run focused tests and verify they fail**

### Task 2: Add backend model and strategy action endpoints

**Files:**
- Create: `backend/app/models/merchant_action.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/app/services/merchant_action_service.py`
- Modify: `backend/app/routes/strategy.py`
- Test: `backend/tests/test_merchant_actions.py`

- [ ] **Step 1: Add persistence model**
- [ ] **Step 2: Add action recording service**
- [ ] **Step 3: Add POST and GET strategy action endpoints**
- [ ] **Step 4: Run backend tests and verify they pass**

### Task 3: Add frontend merchant action API wrappers

**Files:**
- Modify: `frontend/src/api/analytics.js`
- Test: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Add record and summary API methods**
- [ ] **Step 2: Run merchant test and verify it still fails on missing UI**

### Task 4: Wire merchant dashboard action loop

**Files:**
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
- Modify: `frontend/src/styles/theme.css`
- Test: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Add action summary card**
- [ ] **Step 2: Add action buttons to hot, cold, and risk sections**
- [ ] **Step 3: Add inline executed-state tags**
- [ ] **Step 4: Run merchant test and verify it passes**

### Task 5: Verify regressions

**Files:**
- Test: `backend/tests/test_merchant_actions.py`
- Test: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Run focused backend and frontend tests**
- [ ] **Step 2: Run backend full suite**
- [ ] **Step 3: Run frontend full suite**
