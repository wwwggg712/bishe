# Merchant Single Panel Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the merchant dashboard from a long scroll page with anchor links into a fixed left directory with one active content panel shown at a time.

**Architecture:** Keep `/merchant/dashboard` as a single route and keep existing data loading unchanged. Replace hash-based merchant navigation with explicit section state, pass the active section from `AppLayout.vue` into `MerchantDashboard.vue` through route query or props-friendly state, and conditionally render only one merchant dashboard section at a time. Use CSS `sticky` for the left directory and focused Vitest coverage to lock default section, active highlight, and panel switching.

**Tech Stack:** Vue 3, Vue Router, Vitest, Vue Test Utils, CSS

---

## File Structure

- Modify: `frontend/src/layouts/AppLayout.vue`
  - Replace merchant hash links with explicit section-aware navigation targets
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
  - Add `activeSection` handling and render only one section at a time
- Modify: `frontend/src/styles/theme.css`
  - Make merchant sidebar sticky and support selected navigation styling
- Modify: `frontend/src/tests/app-layout.test.js`
  - Verify merchant navigation no longer depends on hash anchors
- Modify: `frontend/src/tests/merchant-dashboard.test.js`
  - Verify default section, switching behavior, and single-panel rendering

### Task 1: Replace merchant hash navigation with section-aware route state

**Files:**
- Modify: `frontend/src/tests/app-layout.test.js`
- Modify: `frontend/src/layouts/AppLayout.vue`
- Test: `frontend/src/tests/app-layout.test.js`

- [ ] **Step 1: Write failing layout tests for merchant navigation without hash anchors**

Replace the first two merchant assertions in `frontend/src/tests/app-layout.test.js` with these tests:

```javascript
it('renders merchant section navigation items without hash anchors', () => {
  const wrapper = mount(AppLayout, {
    global: {
      stubs: {
        RouterView: true,
        RouterLink: {
          props: ['to'],
          template: '<a :href="typeof to === `string` ? to : `${to.path}${to.query ? `?section=${to.query.section}` : ``}`"><slot /></a>'
        }
      }
    }
  })

  const links = wrapper.findAll('a')
  const hrefs = links.map((link) => link.attributes('href'))

  expect(hrefs).toContain('/merchant/dashboard?section=overview')
  expect(hrefs).toContain('/merchant/dashboard?section=core')
  expect(hrefs).toContain('/merchant/dashboard?section=analysis')
  expect(hrefs).toContain('/merchant/dashboard?section=detail')
  expect(hrefs.every((href) => !href.includes('#merchant-'))).toBe(true)
})

it('marks merchant navigation as a fixed dashboard directory', () => {
  const wrapper = mount(AppLayout, {
    global: {
      stubs: {
        RouterView: true,
        RouterLink: {
          props: ['to'],
          template: '<a :href="typeof to === `string` ? to : `${to.path}${to.query ? `?section=${to.query.section}` : ``}`"><slot /></a>'
        }
      }
    }
  })

  expect(wrapper.find('aside.app-shell__sidebar--merchant').exists()).toBe(true)
  expect(wrapper.find('nav.app-shell__nav--merchant').exists()).toBe(true)
})
```

- [ ] **Step 2: Run the focused layout tests and verify they fail**

Run:

```bash
npm run test -- src/tests/app-layout.test.js
```

Expected: FAIL because merchant links still use `hash` anchors and the merchant sidebar has no dedicated fixed/sticky class.

- [ ] **Step 3: Implement section-aware merchant links in `AppLayout.vue`**

Update the merchant branch in `frontend/src/layouts/AppLayout.vue`:

```javascript
if (role === 'merchant') {
  return [
    { label: '经营总览', to: { path: '/merchant/dashboard', query: { section: 'overview' } } },
    { label: '核心业务', to: { path: '/merchant/dashboard', query: { section: 'core' } } },
    { label: '辅助分析', to: { path: '/merchant/dashboard', query: { section: 'analysis' } } },
    { label: '详细分析', to: { path: '/merchant/dashboard', query: { section: 'detail' } } }
  ]
}
```

Add a sidebar class helper:

```javascript
const sidebarClassName = computed(() => ({
  'app-shell__sidebar--merchant': authStore.role === 'merchant'
}))
```

Then update the template:

```vue
<aside class="app-shell__sidebar" :class="sidebarClassName">
```

Keep the existing `navClassName` support.

- [ ] **Step 4: Run the focused layout tests and verify they pass**

Run:

```bash
npm run test -- src/tests/app-layout.test.js
```

Expected: PASS

- [ ] **Step 5: Commit the merchant layout navigation change**

```bash
git add frontend/src/layouts/AppLayout.vue frontend/src/tests/app-layout.test.js
git commit -m "feat: switch merchant nav to section-based links"
```

### Task 2: Add single-panel section switching to the merchant dashboard

**Files:**
- Modify: `frontend/src/tests/merchant-dashboard.test.js`
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
- Test: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Write failing tests for default section and single-panel switching**

In `frontend/src/tests/merchant-dashboard.test.js`, add a router mock at the top:

```javascript
const mockRoute = {
  query: {}
}

vi.mock('vue-router', async () => {
  const actual = await vi.importActual('../router/index.js')
  return {
    useRoute: () => mockRoute
  }
})
```

Then append these tests:

```javascript
it('defaults to overview panel and hides other merchant panels', async () => {
  mockRoute.query = {}

  const wrapper = mount(MerchantDashboard, {
    global: {
      stubs: {
        RouterLink: true
      }
    }
  })

  await flushPromises()

  expect(wrapper.text()).toContain('经营总览')
  expect(wrapper.text()).toContain('今日经营简报')
  expect(wrapper.text()).toContain('行为总量')
  expect(wrapper.text()).not.toContain('用户行为变化')
  expect(wrapper.text()).not.toContain('AI 经营分析')
  expect(wrapper.text()).not.toContain('转化漏斗')
})

it('renders only the selected core panel when section=core', async () => {
  mockRoute.query = { section: 'core' }

  const wrapper = mount(MerchantDashboard, {
    global: {
      stubs: {
        RouterLink: true
      }
    }
  })

  await flushPromises()

  expect(wrapper.text()).toContain('核心业务')
  expect(wrapper.text()).toContain('用户行为变化')
  expect(wrapper.text()).toContain('今日已执行运营动作')
  expect(wrapper.text()).not.toContain('今日经营简报')
  expect(wrapper.text()).not.toContain('AI 经营分析')
  expect(wrapper.text()).not.toContain('转化漏斗')
})

it('renders only the selected analysis panel when section=analysis', async () => {
  mockRoute.query = { section: 'analysis' }

  const wrapper = mount(MerchantDashboard, {
    global: {
      stubs: {
        RouterLink: true
      }
    }
  })

  await flushPromises()

  expect(wrapper.text()).toContain('辅助分析')
  expect(wrapper.text()).toContain('AI 经营分析')
  expect(wrapper.text()).toContain('异常预警')
  expect(wrapper.text()).not.toContain('今日经营简报')
  expect(wrapper.text()).not.toContain('用户行为变化')
  expect(wrapper.text()).not.toContain('转化漏斗')
})

it('renders only the selected detail panel when section=detail', async () => {
  mockRoute.query = { section: 'detail' }

  const wrapper = mount(MerchantDashboard, {
    global: {
      stubs: {
        RouterLink: true
      }
    }
  })

  await flushPromises()

  expect(wrapper.text()).toContain('详细分析')
  expect(wrapper.text()).toContain('转化漏斗')
  expect(wrapper.text()).toContain('冷门商品')
  expect(wrapper.text()).not.toContain('今日经营简报')
  expect(wrapper.text()).not.toContain('用户行为变化')
  expect(wrapper.text()).not.toContain('AI 经营分析')
})
```

- [ ] **Step 2: Run focused merchant dashboard tests and verify they fail**

Run:

```bash
npm run test -- src/tests/merchant-dashboard.test.js
```

Expected: FAIL because the dashboard still renders all four sections together and does not read `route.query.section`.

- [ ] **Step 3: Implement `activeSection` in `MerchantDashboard.vue`**

Update the script setup imports:

```javascript
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
```

Add route-aware section state:

```javascript
const route = useRoute()

const SECTION_MAP = {
  overview: 'overview',
  core: 'core',
  analysis: 'analysis',
  detail: 'detail'
}

const activeSection = computed(() => {
  const section = route.query.section
  if (typeof section === 'string' && SECTION_MAP[section]) {
    return SECTION_MAP[section]
  }
  return 'overview'
})
```

Then replace the four always-rendered top-level blocks with conditional rendering:

```vue
<section v-if="activeSection === 'overview'" class="merchant-dashboard merchant-dashboard--panel">
  <header class="merchant-dashboard__hero">
    ...
  </header>
  <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
  <section class="merchant-brief" :aria-busy="isLoading">
    ...
  </section>
  <section class="merchant-dashboard__summary" :aria-busy="isLoading">
    ...
  </section>
</section>

<section v-else-if="activeSection === 'core'" class="merchant-dashboard merchant-dashboard--panel">
  <section class="merchant-dashboard__layer">
    <div class="merchant-dashboard__layer-head">
      <h3>核心业务</h3>
      <p>优先展示经营联动、动作闭环、机会和风险。</p>
    </div>
    <div class="merchant-dashboard__layer-grid">
      ...
    </div>
  </section>
</section>

<section v-else-if="activeSection === 'analysis'" class="merchant-dashboard merchant-dashboard--panel">
  <section class="merchant-dashboard__layer">
    <div class="merchant-dashboard__layer-head">
      <h3>辅助分析</h3>
      <p>补充解释经营判断，保留分析深度但降低视觉权重。</p>
    </div>
    <div class="merchant-dashboard__layer-grid merchant-dashboard__layer-grid--secondary">
      ...
    </div>
  </section>
</section>

<section v-else class="merchant-dashboard merchant-dashboard--panel">
  <section class="merchant-dashboard__layer">
    <div class="merchant-dashboard__layer-head">
      <h3>详细分析</h3>
      <p>用于答辩追问时补充说明证据，不再占据首页第一优先级。</p>
    </div>
    <div class="merchant-dashboard__layer-grid merchant-dashboard__layer-grid--detail">
      ...
    </div>
  </section>
</section>
```

Remove merchant-specific `id` anchor dependencies such as:

```vue
id="merchant-overview"
id="merchant-core"
id="merchant-analysis"
id="merchant-detail"
```

because they are no longer needed for hash scrolling.

- [ ] **Step 4: Run focused merchant dashboard tests and verify they pass**

Run:

```bash
npm run test -- src/tests/merchant-dashboard.test.js
```

Expected: PASS

- [ ] **Step 5: Commit the single-panel merchant dashboard behavior**

```bash
git add frontend/src/views/merchant/MerchantDashboard.vue frontend/src/tests/merchant-dashboard.test.js
git commit -m "feat: render merchant dashboard as single active panel"
```

### Task 3: Make the merchant left directory sticky and visibly active

**Files:**
- Modify: `frontend/src/styles/theme.css`
- Modify: `frontend/src/tests/merchant-dashboard.test.js`
- Test: `frontend/src/tests/merchant-dashboard.test.js`

- [ ] **Step 1: Add a failing test for active merchant section highlighting**

Append this test to `frontend/src/tests/merchant-dashboard.test.js`:

```javascript
it('marks the current merchant section as active via route query', async () => {
  mockRoute.query = { section: 'analysis' }

  const wrapper = mount(MerchantDashboard, {
    global: {
      stubs: {
        RouterLink: true
      }
    }
  })

  await flushPromises()

  expect(wrapper.classes()).toContain('merchant-dashboard--panel')
})
```

This test is intentionally minimal at the dashboard level; the stronger visual-state assertion lives in layout and CSS behavior.

- [ ] **Step 2: Implement sticky merchant sidebar styles**

Update `frontend/src/styles/theme.css`:

```css
.app-shell__sidebar--merchant {
  position: sticky;
  top: 0;
  align-self: start;
  min-height: 100vh;
}

.app-shell__nav-link.router-link-exact-active,
.app-shell__nav-link.router-link-active {
  background: rgba(59, 130, 246, 0.28);
  color: #ffffff;
  box-shadow: inset 0 0 0 1px rgba(147, 197, 253, 0.22);
}

.merchant-dashboard--panel {
  min-height: calc(100vh - 140px);
  align-content: start;
}
```

Do not remove the existing shared nav styles; only extend them for the merchant-fixed experience.

- [ ] **Step 3: Run focused tests and verify they pass**

Run:

```bash
npm run test -- src/tests/app-layout.test.js src/tests/merchant-dashboard.test.js
```

Expected: PASS

- [ ] **Step 4: Commit the sticky sidebar and active-state styling**

```bash
git add frontend/src/styles/theme.css frontend/src/tests/app-layout.test.js frontend/src/tests/merchant-dashboard.test.js
git commit -m "style: pin merchant directory and active panel layout"
```

### Task 4: Run regression for merchant interactions under the new single-panel model

**Files:**
- Test: `frontend/src/tests/app-layout.test.js`
- Test: `frontend/src/tests/merchant-dashboard.test.js`
- Test: `frontend/src/tests`

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

- [ ] **Step 3: Perform a final UI-behavior review**

Verify these points directly against the code and test outcomes:

```text
1. Merchant left navigation no longer uses hash anchors.
2. Merchant dashboard defaults to overview.
3. Each query section shows only one top-level content panel.
4. Existing data loading, AI analysis, merchant actions, and user linkage tests remain green.
5. Merchant sidebar uses sticky/fixed behavior classes.
```

Record the result in the execution handoff.

- [ ] **Step 4: Commit the regression-verified final state**

```bash
git add frontend/src/layouts/AppLayout.vue frontend/src/views/merchant/MerchantDashboard.vue frontend/src/styles/theme.css frontend/src/tests/app-layout.test.js frontend/src/tests/merchant-dashboard.test.js
git commit -m "feat: switch merchant dashboard to fixed single-panel navigation"
```
