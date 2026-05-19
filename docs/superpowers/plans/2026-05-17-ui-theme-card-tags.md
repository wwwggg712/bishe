# UI Theme & Card Tag Boxes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将全站强调色切换为“橙黄能量”，为所有卡片增加明显的“主题标签框”，收纳“演示口径”说明，并提升商家页布局条理与 AI 分析可读性。

**Architecture:** 以 `theme.css` 的设计 token 为核心统一主题；少量调整 Vue 模板以收纳口径说明；后端调整 LLM system prompt 与参数以生成更长、更结构化的输出。

**Tech Stack:** Vue 3 + Vite + Pinia + Vitest；Flask + SQLAlchemy；OpenAI-compatible LLM provider（DeepSeek）。

---

## File Map

**Frontend**
- Modify: [theme.css](file:///d:/MyProjects/bishe-finnal/frontend/src/styles/theme.css)
- Modify: [MerchantOpsOverview.vue](file:///d:/MyProjects/bishe-finnal/frontend/src/views/merchant/MerchantOpsOverview.vue)

**Backend**
- Modify: [llm_service.py](file:///d:/MyProjects/bishe-finnal/backend/app/services/llm_service.py)

**Docs**
- Reference spec: [2026-05-17-ui-theme-card-tags-design.md](file:///d:/MyProjects/bishe-finnal/docs/superpowers/specs/2026-05-17-ui-theme-card-tags-design.md)

---

### Task 1: Orange-Yellow Accent Tokens & Remove Blue Dominance

**Files:**
- Modify: `frontend/src/styles/theme.css`

- [ ] **Step 1: Define global accent tokens**
  - Add tokens in `:root`:
    - `--accent`, `--accent-2`, `--accent-gradient`, `--accent-shadow`
    - `--card-bg`, `--card-border`, `--card-radius`
  - Replace previous “toy card” variables usage with new tokens to avoid blue/purple border defaults.

- [ ] **Step 2: Update sidebar active state & primary buttons**
  - Update `.app-shell__nav-link.router-link-exact-active/.router-link-active` to use `--accent-gradient` and `--accent-shadow`.
  - Update `.primary-button` to use `--accent-gradient`.
  - Update `.ghost-button:hover` to use `--accent` border/text (keep white base).

- [ ] **Step 3: Run frontend tests**
  - Run: `npm test`
  - Expected: `Test Files ... passed`

---

### Task 2: Card “Theme Tag Box” & Sticker Tags (Order & Clarity)

**Files:**
- Modify: `frontend/src/styles/theme.css`

- [ ] **Step 1: Turn `.section-kicker` into a visible tag-box**
  - Style `.section-kicker` as:
    - inline-block / pill-like framed label
    - white/transparent background
    - thin border `--card-border`
    - a small dot decoration using `::before`
  - Keep English text (do not translate).

- [ ] **Step 2: Normalize card headers for scanability**
  - Ensure `.dashboard-panel__header` aligns:
    - tag-box + title/desc area + right-side badge/button
  - Make `.dashboard-panel__meta-list` display as a vertical list (avoid “一行挤在一起”).

- [ ] **Step 3: Update product tags into “sticker” style**
  - Update `.recommend-product__tag` to:
    - white background
    - colored border and text (use `--accent` and a secondary tone)
    - remove large solid background blocks

- [ ] **Step 4: Keep list cards consistent and calm**
  - Apply `--card-bg/border/shadow` to:
    - `.recommend-list__item`, `.trend-list__item`, `.profile-grid__item`
    - `.admin-log-list__item`, `.admin-job-list__item`
    - `.strategy-list__item`, `.compare-offer-list__item`
  - Hover: small translateY + shadow only (no neon borders).

- [ ] **Step 5: Run frontend tests**
  - Run: `npm test`
  - Expected: PASS

---

### Task 3: Merchant “演示口径” Copy Collapsed by Default

**Files:**
- Modify: `frontend/src/views/merchant/MerchantOpsOverview.vue`

- [ ] **Step 1: Update title & move explanation into `<details>`**
  - Change heading from `经营总览（演示口径）` → `经营总览`
  - Add a `<details>` block under the header:
    - `<summary>口径说明（点击展开）</summary>`
    - Content: keep existing explanation about profit/inventory/delist/focus brands and “purchase 次数估算”

- [ ] **Step 2: Add minimal CSS for `<details>`**
  - Add styles in `theme.css` for details/summary in dashboard headers so it looks like a subtle link/button.

- [ ] **Step 3: Run frontend tests**
  - Run: `npm test`
  - Expected: PASS

---

### Task 4: Fix Merchant Grid Empty White Space

**Files:**
- Modify: `frontend/src/styles/theme.css`

- [ ] **Step 1: Make layer grid responsive**
  - Update `.merchant-dashboard__layer-grid` to `repeat(auto-fit, minmax(320px, 1fr))` (or comparable).

- [ ] **Step 2: Ensure single-card rows fill the row**
  - Add selector:
    - `.merchant-dashboard__layer-grid > :only-child { grid-column: 1 / -1; }`
  - This prevents right-side empty column when only one card exists.

- [ ] **Step 3: Run frontend tests**
  - Run: `npm test`
  - Expected: PASS

---

### Task 5: Make DeepSeek / Provider Output Longer & More Structured (No Markdown Asterisks)

**Files:**
- Modify: `backend/app/services/llm_service.py`
- Test: `backend/tests/test_llm_report.py` (only if needed)

- [ ] **Step 1: Update system prompt for provider mode**
  - Replace current system content with a stricter instruction:
    - Output plain Chinese text
    - Do NOT use Markdown (no `**`, no lists with `-` if it prints oddly; prefer `1)` style)
    - Provide sections: 核心结论 / 机会点 / 风险预警 / 行动清单(P0/P1)
    - Minimum bullets: opportunities ≥ 3, risks ≥ 3, actions ≥ 5

- [ ] **Step 2: Increase provider generation length**
  - Add `max_tokens` to request body (e.g., 700~1000)
  - Slightly raise temperature (e.g., 0.6) if needed to avoid overly short responses.

- [ ] **Step 3: Run backend tests**
  - Run: `python -m pytest -q`
  - Expected: `77 passed`

---

### Task 6: Verification (End-to-End)

- [ ] **Step 1: Frontend**
  - Run: `npm test` in `frontend`
  - Expected: PASS

- [ ] **Step 2: Backend**
  - Run: `python -m pytest -q` in `backend`
  - Expected: PASS

