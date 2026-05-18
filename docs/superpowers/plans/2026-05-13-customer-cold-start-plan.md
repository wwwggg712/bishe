# Customer Cold Start Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add cold-start portrait detection and fallback recommendations so the customer page stays credible when the user has no personal behavior or no remaining personalized candidates.

**Architecture:** Keep the existing endpoints and enrich their payloads with explicit state. The backend adds `is_cold_start` and recommendation `mode`, while the frontend renders different copy for personalized versus cold-start states without introducing a new page or new route.

**Tech Stack:** Flask, Flask-JWT-Extended, Vue 3, Vitest, Pytest

---

### Task 1: Add failing backend tests for cold-start portrait and fallback recommendations

**Files:**
- Modify: `backend/tests/test_intelligence.py`
- Modify: `backend/tests/conftest.py`

- [ ] **Step 1: Write the failing portrait cold-start test**

```python
def test_customer_portrait_returns_cold_start_when_no_personal_logs(client, customer_headers, seeded_demo_data):
    from app.services.simulation_service import simulation_memory_store

    simulation_memory_store.logs = [
        {
            "log_id": "m-1",
            "user_id": 2,
            "merchant_id": 2,
            "product_id": 1,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 299.0,
            "action_type": "view",
            "region": "华东",
            "device_type": "mobile",
            "source_channel": "homepage",
            "session_id": "s-1",
            "stay_duration": 18,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:00:00",
        }
    ]

    response = client.get("/api/users/portrait", headers=customer_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["is_cold_start"] is True
    assert payload["top_categories"] == []
    assert payload["price_preference"]["price_band"] == "暂无数据"
```

- [ ] **Step 2: Write the failing fallback recommendation test**

```python
def test_customer_recommendations_fall_back_when_no_personal_candidates(client, customer_headers, seeded_demo_data):
    from app.services.simulation_service import simulation_memory_store

    simulation_memory_store.logs = [
        {
            "log_id": "c-1",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 1,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 299.0,
            "action_type": "purchase",
            "region": "华南",
            "device_type": "mobile",
            "source_channel": "homepage",
            "session_id": "s-2",
            "stay_duration": 26,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:10:00",
        },
        {
            "log_id": "c-2",
            "user_id": 2,
            "merchant_id": 2,
            "product_id": 1,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 299.0,
            "action_type": "purchase",
            "region": "华东",
            "device_type": "desktop",
            "source_channel": "search",
            "session_id": "s-3",
            "stay_duration": 15,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:15:00",
        },
    ]

    response = client.get("/api/recommendations/me", headers=customer_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["mode"] == "fallback"
    assert payload["items"]
    assert "冷启动推荐" in payload["items"][0]["reason"]
```

- [ ] **Step 3: Write the failing personalized recommendation mode test**

```python
def test_customer_recommendations_return_personalized_mode_when_candidates_exist(client, customer_headers, seeded_demo_data):
    from app.services.simulation_service import simulation_memory_store

    simulation_memory_store.logs = [
        {
            "log_id": "p-1",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 1,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 299.0,
            "action_type": "favorite",
            "region": "华南",
            "device_type": "mobile",
            "source_channel": "homepage",
            "session_id": "s-4",
            "stay_duration": 22,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:20:00",
        },
        {
            "log_id": "p-2",
            "user_id": 2,
            "merchant_id": 2,
            "product_id": 2,
            "product_name": "透气训练T恤",
            "category": "运动服饰",
            "brand": "CloudStep",
            "price": 129.0,
            "action_type": "purchase",
            "region": "华东",
            "device_type": "desktop",
            "source_channel": "search",
            "session_id": "s-5",
            "stay_duration": 17,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:25:00",
        },
    ]

    response = client.get("/api/recommendations/me", headers=customer_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["mode"] == "personalized"
    assert payload["items"]
```

- [ ] **Step 4: Run backend tests to verify they fail**

Run: `python -m pytest tests/test_intelligence.py -k "cold_start or recommendations_return or recommendations_fall_back" -q`

Expected: FAIL because `is_cold_start` and `mode` are not returned yet, or fallback reason text does not match.

### Task 2: Implement backend cold-start portrait state

**Files:**
- Modify: `backend/app/services/prediction_service.py`
- Modify: `backend/app/routes/users.py`
- Test: `backend/tests/test_intelligence.py`

- [ ] **Step 1: Extend the empty portrait payload to include cold-start state**

```python
def _build_empty_portrait(self):
    return {
        "is_cold_start": True,
        "top_categories": [],
        "top_actions": [],
        "recent_activity": [],
        "engagement_score": 0,
        "top_active_hours": [],
        "price_preference": {
            "average_price": 0,
            "price_band": "暂无数据",
        },
        "profile_tags": [],
    }
```

- [ ] **Step 2: Mark non-empty portraits as non-cold-start**

```python
return {
    "is_cold_start": False,
    "top_categories": top_categories,
    "top_actions": top_actions,
    "recent_activity": recent_items[:recent_activity],
    "engagement_score": total_score,
    "top_active_hours": hour_items,
    "price_preference": {
        "average_price": average_price,
        "price_band": self._build_price_band(average_price),
    },
    "profile_tags": profile_tags,
}
```

- [ ] **Step 3: Keep the portrait route response shape stable while returning the new field**

```python
portrait_payload = prediction_service.build_user_portrait(int(user.id), simulation_memory_store.logs)
return jsonify(
    {
        "user": user.to_dict(),
        **portrait_payload,
    }
)
```

- [ ] **Step 4: Run the portrait cold-start test and verify it passes**

Run: `python -m pytest tests/test_intelligence.py::test_customer_portrait_returns_cold_start_when_no_personal_logs -q`

Expected: PASS

### Task 3: Implement backend fallback recommendation mode

**Files:**
- Modify: `backend/app/services/recommendation_service.py`
- Modify: `backend/app/routes/recommendation.py`
- Test: `backend/tests/test_intelligence.py`

- [ ] **Step 1: Add a helper that builds fallback recommendations**

```python
def _build_fallback_items(self, products, hot_scores, limit=5):
    ranked_products = sorted(
        products,
        key=lambda product: (hot_scores.get(product.id, 0), product.stock),
        reverse=True,
    )

    items = []
    for product in ranked_products[:limit]:
        items.append(
            {
                "product_id": product.id,
                "product_name": product.name,
                "category": product.category,
                "reason": "该商品近期热度较高，适合作为当前阶段的冷启动推荐",
            }
        )
    return items
```

- [ ] **Step 2: Return fallback mode when the user has no personal logs**

```python
favorite_category = category_counter.most_common(1)[0][0] if category_counter else None
if not favorite_category and not interacted_product_ids:
    return {
        "mode": "fallback",
        "items": self._build_fallback_items(products, hot_scores),
    }
```

- [ ] **Step 3: Return fallback mode when personalized candidates are filtered out**

```python
if not items:
    return {
        "mode": "fallback",
        "items": self._build_fallback_items(products, hot_scores),
    }

return {"mode": "personalized", "items": items[:5]}
```

- [ ] **Step 4: Keep the route unchanged and let the service own the mode decision**

```python
payload = recommendation_service.recommend_for_customer(
    user_id=user_id,
    logs=simulation_memory_store.logs,
    products=products,
)
return jsonify(payload)
```

- [ ] **Step 5: Run the recommendation mode tests and verify they pass**

Run: `python -m pytest tests/test_intelligence.py -k "recommendations_fall_back or recommendations_return_personalized_mode" -q`

Expected: PASS

### Task 4: Add failing frontend tests for cold-start and fallback rendering

**Files:**
- Modify: `frontend/src/tests/customer-home.test.js`

- [ ] **Step 1: Add a failing cold-start UI test**

```javascript
it('renders cold-start portrait copy when the user has no personal behavior', async () => {
  fetchMyRecommendations.mockResolvedValue({
    mode: 'fallback',
    items: [
      {
        product_id: 1,
        product_name: '轻量跑鞋',
        category: '运动鞋',
        reason: '该商品近期热度较高，适合作为当前阶段的冷启动推荐'
      }
    ]
  })
  fetchPreferenceProfile.mockResolvedValue({
    user: { nickname: '小林', region: '华东' },
    is_cold_start: true,
    top_categories: [],
    top_actions: [],
    recent_activity: [],
    engagement_score: 0,
    top_active_hours: [],
    price_preference: { average_price: 0, price_band: '暂无数据' },
    profile_tags: []
  })

  const wrapper = mount(CustomerHome)
  await flushPromises()

  expect(wrapper.text()).toContain('冷启动用户')
  expect(wrapper.text()).toContain('冷启动推荐')
  expect(wrapper.text()).toContain('暂无个人行为')
})
```

- [ ] **Step 2: Run the frontend cold-start test to verify it fails**

Run: `npm run test -- src/tests/customer-home.test.js`

Expected: FAIL because the current page still renders fixed titles and does not recognize `is_cold_start` or `mode`.

### Task 5: Implement frontend cold-start and fallback rendering

**Files:**
- Modify: `frontend/src/views/customer/CustomerHome.vue`
- Modify: `frontend/src/api/recommendation.js`
- Test: `frontend/src/tests/customer-home.test.js`

- [ ] **Step 1: Extend the local profile state with the cold-start flag**

```javascript
const profile = ref({
  user: {
    nickname: '',
    region: ''
  },
  is_cold_start: false,
  top_categories: [],
  top_actions: [],
  recent_activity: [],
  engagement_score: 0,
  top_active_hours: [],
  price_preference: {
    average_price: 0,
    price_band: ''
  },
  profile_tags: []
})
```

- [ ] **Step 2: Add computed labels for recommendation mode and portrait state**

```javascript
const recommendationMode = computed(() => recommendationPayloadMode.value === 'fallback' ? 'fallback' : 'personalized')
const recommendationTitle = computed(() => recommendationMode.value === 'fallback' ? '冷启动推荐' : '猜你喜欢')
const recommendationDescription = computed(() =>
  recommendationMode.value === 'fallback'
    ? '当前暂无足够个人行为，先为你展示热门趋势商品。'
    : '基于你的历史行为偏好生成。'
)
const portraitTitle = computed(() => profile.value.is_cold_start ? '冷启动用户' : '我的偏好画像')
const portraitDescription = computed(() =>
  profile.value.is_cold_start
    ? '暂无个人行为，当前仅展示基础账号信息。'
    : '基于真实行为日志统计你的偏好类目、消费倾向和活跃时段。'
)
```

- [ ] **Step 3: Store the recommendation mode when loading the page**

```javascript
const recommendationPayloadMode = ref('personalized')

async function loadCustomerHome() {
  // ...
  recommendationPayloadMode.value = recommendationPayload.mode || 'personalized'
  recommendations.value = recommendationPayload.items || []
  // ...
}
```

- [ ] **Step 4: Render the dynamic titles and descriptions**

```vue
<h3>{{ recommendationTitle }}</h3>
<p>{{ recommendationDescription }}</p>
```

```vue
<h3>{{ portraitTitle }}</h3>
<p>{{ portraitDescription }}</p>
```

- [ ] **Step 5: Replace the empty personalized message with fallback-aware messaging**

```vue
<p v-else class="empty-state">
  {{ recommendationMode === 'fallback' ? '当前暂无可展示的冷启动推荐。' : '暂无个性化推荐，请稍后刷新。' }}
</p>
```

- [ ] **Step 6: Keep the AI explanation button but make the payload cold-start safe**

```javascript
const payload = await fetchCustomerAiExplanation({
  product_name: recommendations.value[0]?.product_name || '热门趋势商品',
  trend_product_name: trendProducts.value[0]?.product_name || '趋势商品',
  preferred_category: profile.value.is_cold_start
    ? '暂无个人偏好'
    : profile.value.top_categories[0]?.category || '综合偏好',
  price_band: profile.value.price_preference.price_band || '暂无数据',
  active_hour: profile.value.is_cold_start
    ? '暂无个人活跃时段'
    : (profile.value.top_active_hours[0] ? `${profile.value.top_active_hours[0].hour}点` : '晚间')
})
```

- [ ] **Step 7: Run the customer page tests and verify they pass**

Run: `npm run test -- src/tests/customer-home.test.js`

Expected: PASS

### Task 6: Run regression verification

**Files:**
- Test: `backend/tests/test_intelligence.py`
- Test: `frontend/src/tests/customer-home.test.js`
- Test: `backend/tests`
- Test: `frontend/src/tests`

- [ ] **Step 1: Run focused backend tests**

Run: `python -m pytest tests/test_intelligence.py -q`

Expected: PASS

- [ ] **Step 2: Run focused frontend tests**

Run: `npm run test -- src/tests/customer-home.test.js`

Expected: PASS

- [ ] **Step 3: Run backend full suite**

Run: `python -m pytest -q`

Expected: PASS

- [ ] **Step 4: Run frontend full suite**

Run: `npm run test`

Expected: PASS
