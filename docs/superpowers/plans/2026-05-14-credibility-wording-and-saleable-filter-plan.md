# 可售商品过滤与口径收紧 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让用户推荐只返回可售商品，并把商家页与管理员页中强于真实实现的漏斗、分层、近期信号文案收紧到准确口径。

**Architecture:** 后端只在推荐路由层增加“可售商品”业务约束，不重写推荐排序服务，保持冷启动和个性化逻辑不变。前端不改布局结构，只更新商家页、管理员页和漏斗卡片中的标题、说明文案与测试断言，把“完整漏斗”“RFM”“变化”等容易被追问的表达改成事件级经营指标、简化用户分层和最近 24 小时信号。

**Tech Stack:** Flask, Flask-JWT-Extended, SQLAlchemy, Pytest, Vue 3, Vitest

---

## File Structure

- Modify: `backend/app/routes/recommendation.py`
  - 在推荐接口和行为记录接口收口可售商品过滤
- Modify: `backend/tests/test_intelligence.py`
  - 增加不可售商品不进入推荐、不可售商品不可记录行为的回归测试
- Modify: `frontend/src/views/merchant/FunnelView.vue`
  - 收紧漏斗卡片副标题和提示说明
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
  - 收紧“用户行为变化”和“RFM”相关标题与说明
- Modify: `frontend/src/views/admin/AdminLogPreviewPage.vue`
  - 收紧管理员页日志说明和算法链路说明
- Modify: `frontend/src/tests/merchant-dashboard.test.js`
  - 更新商家页文案断言
- Modify: `frontend/src/tests/admin-pages.test.js`
  - 更新管理员页文案断言

### Task 1: 用测试锁定“只推荐可售商品”

**Files:**
- Modify: `backend/tests/test_intelligence.py`
- Modify: `backend/app/routes/recommendation.py`
- Test: `backend/tests/test_intelligence.py`

- [ ] **Step 1: 写两个后端失败测试**

在 `backend/tests/test_intelligence.py` 末尾追加以下测试：

```python
def test_customer_recommendations_exclude_inactive_and_out_of_stock_products(
    client, customer_headers, seeded_demo_data
):
    original_logs = list(simulation_memory_store.logs)
    simulation_memory_store.logs = _seed_profile_logs()

    from app.models.product import Product
    from app.extensions import db

    inactive_product = db.session.get(Product, 1)
    inactive_product.is_active = False
    sold_out_product = db.session.get(Product, 2)
    sold_out_product.stock = 0
    db.session.commit()

    try:
        response = client.get("/api/recommendations/me", headers=customer_headers)

        assert response.status_code == 200
        payload = response.get_json()
        product_ids = {item["product_id"] for item in payload["items"]}
        assert 1 not in product_ids
        assert 2 not in product_ids
    finally:
        simulation_memory_store.logs = original_logs


def test_customer_cannot_record_action_for_unsaleable_product(
    client, customer_headers, seeded_demo_data
):
    from app.models.product import Product
    from app.extensions import db

    product = db.session.get(Product, 1)
    product.is_active = False
    product.stock = 0
    db.session.commit()

    response = client.post(
        "/api/recommendations/actions",
        json={"product_id": 1, "action_type": "purchase"},
        headers=customer_headers,
    )

    assert response.status_code == 400
    assert "不可售" in response.get_json()["message"]
```

- [ ] **Step 2: 运行聚焦后端测试，确认先红灯**

Run:

```bash
python -m pytest backend/tests/test_intelligence.py -k "exclude_inactive or unsaleable_product" -q
```

Expected: FAIL，因为当前推荐接口仍读取全部商品，行为记录接口也未拦截不可售商品。

- [ ] **Step 3: 在推荐路由中实现最小可售商品过滤**

将 `backend/app/routes/recommendation.py` 改成以下关键逻辑：

```python
@bp.get("/me")
@jwt_required()
def recommend_me():
    if get_jwt().get("role") != "customer":
        return jsonify({"message": "仅普通用户可查看个人推荐"}), 403

    user_id = int(get_jwt_identity())
    products = Product.query.filter(
        Product.is_active.is_(True),
        Product.stock > 0,
    ).all()
    payload = recommendation_service.recommend_for_customer(
        user_id=user_id,
        logs=simulation_memory_store.logs,
        products=products,
    )
    return jsonify(payload)
```

```python
@bp.post("/actions")
@jwt_required()
def record_action():
    if get_jwt().get("role") != "customer":
        return jsonify({"message": "仅普通用户可记录推荐行为"}), 403

    payload = request.get_json(silent=True) or {}
    product_id = payload.get("product_id")
    action_type = (payload.get("action_type") or "").strip().lower()

    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        product_id = None

    if product_id is None or action_type not in SimulationService.VALID_CUSTOMER_ACTION_TYPES:
        return jsonify({"message": "product_id 或 action_type 非法"}), 400

    user = db.session.get(User, int(get_jwt_identity()))
    product = db.session.get(Product, product_id)
    if user is None or product is None:
        return jsonify({"message": "用户或商品不存在"}), 404
    if not product.is_active or product.stock <= 0:
        return jsonify({"message": "商品当前不可售，无法记录用户行为"}), 400

    log = simulation_service.record_customer_action(
        user=user,
        product=product,
        action_type=action_type,
    )
    return jsonify({"message": "用户行为记录成功", "log": log})
```

- [ ] **Step 4: 运行聚焦后端测试，确认转绿**

Run:

```bash
python -m pytest backend/tests/test_intelligence.py -k "exclude_inactive or unsaleable_product" -q
```

Expected: PASS

- [ ] **Step 5: 扩一轮推荐链路回归**

Run:

```bash
python -m pytest backend/tests/test_intelligence.py -k "recommendations or record_recommendation_action" -q
```

Expected: PASS，现有冷启动、真实行为闭环和个性化推荐测试继续通过。

- [ ] **Step 6: 提交后端过滤改动**

```bash
git add backend/app/routes/recommendation.py backend/tests/test_intelligence.py
git commit -m "fix: filter unsaleable products from recommendations"
```

### Task 2: 收紧商家页与管理员页文案口径

**Files:**
- Modify: `frontend/src/views/merchant/FunnelView.vue`
- Modify: `frontend/src/views/merchant/MerchantDashboard.vue`
- Modify: `frontend/src/views/admin/AdminLogPreviewPage.vue`
- Modify: `frontend/src/tests/merchant-dashboard.test.js`
- Modify: `frontend/src/tests/admin-pages.test.js`
- Test: `frontend/src/tests/merchant-dashboard.test.js`
- Test: `frontend/src/tests/admin-pages.test.js`

- [ ] **Step 1: 先写前端失败断言，锁住新文案**

在 `frontend/src/tests/merchant-dashboard.test.js` 的 `section=core` 和 `section=analysis` 用例中，把断言替换为：

```javascript
expect(wrapper.text()).toContain('最近24小时用户活跃信号')
expect(wrapper.text()).toContain('最近24小时高意向商品信号')
expect(wrapper.text()).toContain('简化用户分层')
expect(wrapper.text()).not.toContain('用户行为变化')
expect(wrapper.text()).not.toContain('通过 RFM 识别高价值与潜力用户')
```

在同文件新增一个 `section=detail` 用例断言漏斗文案：

```javascript
it('renders event-level funnel wording in detail section', async () => {
  mockRoute.query = { section: 'detail' }

  const wrapper = mount(MerchantDashboard, {
    global: {
      stubs: {
        RouterLink: true
      }
    }
  })

  await flushPromises()

  expect(wrapper.text()).toContain('转化漏斗')
  expect(wrapper.text()).toContain('事件级经营转化指标')
  expect(wrapper.text()).toContain('购买行为 / 浏览行为')
  expect(wrapper.text()).not.toContain('浏览到购买')
})
```

在 `frontend/src/tests/admin-pages.test.js` 的日志预览页用例中，把相关断言替换为：

```javascript
expect(wrapper.text()).toContain('基于五类行为事件统计经营转化指标')
expect(wrapper.text()).toContain('基于最近活跃、购买频次和金额的分层统计')
expect(wrapper.text()).toContain('事件级转化统计')
expect(wrapper.text()).not.toContain('完整漏斗')
expect(wrapper.text()).not.toContain('浏览到购买的行为路径')
expect(wrapper.text()).not.toContain('RFM 和异常分析')
```

- [ ] **Step 2: 运行聚焦前端测试，确认先红灯**

Run:

```bash
npm run test -- src/tests/merchant-dashboard.test.js src/tests/admin-pages.test.js
```

Expected: FAIL，因为页面仍保留旧文案。

- [ ] **Step 3: 实现商家页漏斗和信号文案收紧**

把 `frontend/src/views/merchant/FunnelView.vue` 改成：

```vue
<template>
  <article class="dashboard-panel">
    <div class="dashboard-panel__header">
      <div>
        <p class="section-kicker">FUNNEL</p>
        <h3>转化漏斗</h3>
        <p>基于五类行为事件统计经营转化指标，不代表单用户真实路径漏斗。</p>
      </div>
      <span class="dashboard-panel__badge">事件级经营指标</span>
    </div>

    <FunnelChart :steps="steps" />

    <div class="funnel-insight">
      <strong>整体成交转化率</strong>
      <p>{{ conversionRate }}</p>
      <span>购买行为 / 浏览行为</span>
    </div>
  </article>
</template>
```

把 `frontend/src/views/merchant/MerchantDashboard.vue` 中“用户行为变化”和“用户价值分层”相关文案改成：

```vue
<p class="section-kicker">USER BEHAVIOR SIGNALS</p>
<h3>最近24小时用户活跃信号</h3>
<p>展示最近24小时窗口内的收藏、加购、购买信号，不代表与历史基线比较后的变化结果。</p>
```

```vue
<h4>最近24小时高意向商品信号</h4>
```

```vue
<p class="section-kicker">USER SEGMENT</p>
<h3>简化用户分层</h3>
<p>基于最近活跃、购买频次和金额的分层统计，用于识别高价值、潜力和待激活用户。</p>
```

- [ ] **Step 4: 实现管理员页说明文案收紧**

把 `frontend/src/views/admin/AdminLogPreviewPage.vue` 中下列文案改成：

```vue
<p>展示系统如何把原始日志转成聚合指标、评分结果、画像、异常、分层与 AI 解释，其中转化相关内容为事件级统计。</p>
```

```vue
<p>基础主数据来自初始化的用户、商品、地区和类目，行为日志由模拟器按规则生成。</p>
```

```vue
<p>浏览、点击、收藏、加购、购买五类事件共同构成经营指标输入，而不是单用户完整路径漏斗。</p>
```

```vue
<p>依据商品行为次数和行为权重计算热度分，得到热销商品与冷门商品。</p>
```

```vue
<p>基于五类行为事件统计经营转化指标，并比较时间窗口识别异常变化。</p>
```

```vue
<p>基于最近活跃、购买频次和金额的分层统计，生成用户价值分层和偏好画像。</p>
```

并把 `generation_note` mock 相关断言从：

```javascript
'日志由系统模拟器生成，用于热度、漏斗、RFM 和异常分析。'
```

对应收紧为：

```javascript
'日志由系统模拟器生成，用于热度、事件级经营指标、简化用户分层和异常分析。'
```

- [ ] **Step 5: 运行聚焦前端测试，确认转绿**

Run:

```bash
npm run test -- src/tests/merchant-dashboard.test.js src/tests/admin-pages.test.js
```

Expected: PASS

- [ ] **Step 6: 提交前端文案收紧改动**

```bash
git add frontend/src/views/merchant/FunnelView.vue frontend/src/views/merchant/MerchantDashboard.vue frontend/src/views/admin/AdminLogPreviewPage.vue frontend/src/tests/merchant-dashboard.test.js frontend/src/tests/admin-pages.test.js
git commit -m "fix: align dashboard wording with actual analytics semantics"
```

### Task 3: 做最终回归并检查诊断

**Files:**
- Test: `backend/tests/test_intelligence.py`
- Test: `frontend/src/tests/merchant-dashboard.test.js`
- Test: `frontend/src/tests/admin-pages.test.js`
- Review: `backend/app/routes/recommendation.py`
- Review: `frontend/src/views/merchant/FunnelView.vue`
- Review: `frontend/src/views/merchant/MerchantDashboard.vue`
- Review: `frontend/src/views/admin/AdminLogPreviewPage.vue`

- [ ] **Step 1: 跑完整后端 intelligence 回归**

Run:

```bash
python -m pytest backend/tests/test_intelligence.py -q
```

Expected: PASS

- [ ] **Step 2: 跑商家与管理员前端回归**

Run:

```bash
npm run test -- src/tests/merchant-dashboard.test.js src/tests/admin-pages.test.js
```

Expected: PASS

- [ ] **Step 3: 跑前端全量测试**

Run:

```bash
npm run test
```

Expected: PASS

- [ ] **Step 4: 检查最近改动文件诊断**

Use diagnostics on:

```text
d:\MyProjects\bishe-finnal\backend\app\routes\recommendation.py
d:\MyProjects\bishe-finnal\frontend\src\views\merchant\FunnelView.vue
d:\MyProjects\bishe-finnal\frontend\src\views\merchant\MerchantDashboard.vue
d:\MyProjects\bishe-finnal\frontend\src\views\admin\AdminLogPreviewPage.vue
```

Expected: 无新增语法或类型错误。

- [ ] **Step 5: 做人工复查**

核对以下结果：

```text
1. 推荐列表不再返回下架或无库存商品。
2. 用户对不可售商品操作时会收到明确业务错误。
3. 商家页漏斗仍保留模块结构，但不会再暗示真实路径漏斗。
4. 商家页“最近24小时”模块不再把窗口内信号说成历史变化。
5. 商家页“简化用户分层”不再冒充完整 RFM。
6. 管理员页说明区不再把事件统计写成完整漏斗。
```

- [ ] **Step 6: 提交回归验证后的最终状态**

```bash
git add backend/app/routes/recommendation.py backend/tests/test_intelligence.py frontend/src/views/merchant/FunnelView.vue frontend/src/views/merchant/MerchantDashboard.vue frontend/src/views/admin/AdminLogPreviewPage.vue frontend/src/tests/merchant-dashboard.test.js frontend/src/tests/admin-pages.test.js
git commit -m "fix: tighten recommendation and analytics wording credibility"
```
