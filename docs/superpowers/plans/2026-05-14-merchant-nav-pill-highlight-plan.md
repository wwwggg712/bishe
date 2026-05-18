# Merchant Nav Pill Highlight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the merchant left navigation to a brighter pill-style active state while keeping the fixed directory and single-panel switching behavior unchanged.

**Architecture:** Limit the change to merchant navigation presentation. Keep `AppLayout.vue` and `MerchantDashboard.vue` behavior intact, and make the active route link visually read as a bright blue capsule on the merchant sidebar. Lock the style through lightweight CSS assertions and the existing app-layout/merchant-dashboard regression tests.

**Tech Stack:** Vue 3, Vue Router, Vitest, CSS

---

## File Structure

- Modify: `frontend/src/styles/theme.css`
  - Strengthen the merchant active nav link into a brighter pill highlight
- Modify: `frontend/src/tests/merchant-dashboard.test.js`
  - Tighten style assertions around the new merchant active state
- Test: `frontend/src/tests/app-layout.test.js`
- Test: `frontend/src/tests/merchant-dashboard.test.js`

### Task 1: Lock the brighter pill active state with a failing test

**Files:**
- Modify: `frontend/src/tests/merchant-dashboard.test.js`
- Test: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Add failing style assertions for the brighter merchant pill state**

In `frontend/src/tests/merchant-dashboard.test.js`, replace the existing CSS assertions inside `defines sticky merchant sidebar and active panel styles in theme css` with:

```javascript
expect(themeCss).toContain('.app-shell__sidebar--merchant')
expect(themeCss).toContain('position: sticky;')
expect(themeCss).toContain('top: 0;')
expect(themeCss).toContain('.app-shell__nav-link.router-link-exact-active')
expect(themeCss).toContain('background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);')
expect(themeCss).toContain('color: #ffffff;')
expect(themeCss).toContain('box-shadow: 0 10px 24px rgba(37, 99, 235, 0.28);')
expect(themeCss).toContain('transform: translateX(4px);')
expect(themeCss).toContain('.merchant-dashboard--panel')
expect(themeCss).toContain('min-height: calc(100vh - 140px);')
```

- [ ] **Step 2: Run the focused merchant tests and verify they fail**

Run:

```bash
npm run test -- src/tests/merchant-dashboard.test.js
```

Expected: FAIL because the current active nav style still uses the softer semi-transparent blue background.

- [ ] **Step 3: Commit the red test**

```bash
git add frontend/src/tests/merchant-dashboard.test.js
git commit -m "test: lock brighter merchant nav pill highlight"
```

### Task 2: Implement the brighter merchant pill highlight

**Files:**
- Modify: `frontend/src/styles/theme.css`
- Test: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Update the merchant active nav style in `theme.css`**

In `frontend/src/styles/theme.css`, replace the current merchant active link block:

```css
.app-shell__nav-link.router-link-exact-active,
.app-shell__nav-link.router-link-active {
  background: rgba(59, 130, 246, 0.28);
  color: #ffffff;
  box-shadow: inset 0 0 0 1px rgba(147, 197, 253, 0.22);
}
```

with:

```css
.app-shell__nav-link.router-link-exact-active,
.app-shell__nav-link.router-link-active {
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
  color: #ffffff;
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.28);
  transform: translateX(4px);
}
```

Do not change sidebar layout, sticky behavior, or single-panel rendering logic.

- [ ] **Step 2: Run the focused merchant tests and verify they pass**

Run:

```bash
npm run test -- src/tests/merchant-dashboard.test.js
```

Expected: PASS

- [ ] **Step 3: Commit the brighter pill highlight**

```bash
git add frontend/src/styles/theme.css frontend/src/tests/merchant-dashboard.test.js
git commit -m "style: brighten merchant nav active pill"
```

### Task 3: Run regression for layout and merchant dashboard behavior

**Files:**
- Test: `frontend/src/tests/app-layout.test.js`
- Test: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Run focused layout and merchant dashboard tests**

Run:

```bash
npm run test -- src/tests/app-layout.test.js src/tests/merchant-dashboard.test.js
```

Expected: PASS

- [ ] **Step 2: Run frontend full suite**

Run:

```bash
npm run test
```

Expected: PASS

- [ ] **Step 3: Perform a final visual-semantics review**

Verify these points against code and tests:

```text
1. Merchant left directory stays sticky.
2. The active item uses a brighter blue pill highlight.
3. Non-active items remain visually weaker than the current item.
4. Single-panel switching behavior remains unchanged.
5. Existing merchant AI, actions, and linkage tests remain green.
```

Record the result in the handoff summary.

- [ ] **Step 4: Commit the regression-verified final state**

```bash
git add frontend/src/styles/theme.css frontend/src/tests/merchant-dashboard.test.js frontend/src/tests/app-layout.test.js
git commit -m "style: polish merchant nav pill highlight"
```
