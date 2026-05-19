def _make_log(
    user_id,
    product_id,
    product_name,
    action_type,
    region,
    *,
    merchant_id=1,
    category="运动鞋",
    price=299.0,
):
    return {
        "log_id": f"log-{merchant_id}-{user_id}-{product_id}-{action_type}-{region}",
        "user_id": user_id,
        "merchant_id": merchant_id,
        "product_id": product_id,
        "product_name": product_name,
        "category": category,
        "brand": "CloudStep",
        "price": price,
        "action_type": action_type,
        "region": region,
        "device_type": "mobile",
        "source_channel": "homepage",
        "session_id": f"session-{merchant_id}-{user_id}",
        "stay_duration": 30,
        "is_new_user": False,
        "timestamp": "2026-05-12T10:00:00",
    }


def test_overview_returns_core_metrics(
    client, merchant_headers, seeded_demo_data, persist_behavior_logs
):
    persist_behavior_logs(
        [
        _make_log(1, 101, "轻量跑鞋", "view", "华东", merchant_id=2),
        _make_log(1, 101, "轻量跑鞋", "click", "华东", merchant_id=2),
        _make_log(1, 101, "轻量跑鞋", "purchase", "华东", merchant_id=2),
        _make_log(3, 101, "轻量跑鞋", "favorite", "华北", merchant_id=2),
        _make_log(2, 202, "智能运动手环", "view", "华南", merchant_id=4),
        _make_log(2, 202, "智能运动手环", "cart", "华南", merchant_id=4),
        ]
    )

    response = client.get("/api/analytics/overview", headers=merchant_headers)

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["totals"] == {
        "behavior_count": 4,
        "view_count": 1,
        "uv": 2,
        "purchase_count": 1,
        "purchase_rate": 0.6667,
    }
    assert payload["funnel"] == {
        "view": 1,
        "click": 1,
        "favorite": 1,
        "cart": 0,
        "purchase": 1,
    }
    assert payload["top_products"] == [
        {"product_id": 101, "product_name": "轻量跑鞋", "count": 4}
    ]
    assert payload["regions"] == [
        {"region": "华东", "count": 3},
        {"region": "华北", "count": 1},
    ]


def test_merchant_overview_only_counts_current_merchant_logs(
    client, merchant_headers, seeded_demo_data, persist_behavior_logs
):
    persist_behavior_logs(
        [
        _make_log(3, 101, "轻量跑鞋", "view", "华东", merchant_id=2, category="运动鞋"),
        _make_log(3, 101, "轻量跑鞋", "purchase", "华东", merchant_id=2, category="运动鞋"),
        _make_log(4, 201, "户外冲锋衣", "view", "华南", merchant_id=4, category="户外装备"),
        _make_log(4, 201, "户外冲锋衣", "purchase", "华南", merchant_id=4, category="户外装备"),
        ]
    )

    response = client.get("/api/analytics/overview", headers=merchant_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["totals"] == {
        "behavior_count": 2,
        "view_count": 1,
        "uv": 1,
        "purchase_count": 1,
        "purchase_rate": 0.6667,
    }
    assert payload["top_products"] == [
        {"product_id": 101, "product_name": "轻量跑鞋", "count": 2}
    ]
    assert payload["regions"] == [{"region": "华东", "count": 2}]


def test_merchant_detail_endpoints_only_return_current_merchant_scope(
    client, merchant_headers, seeded_demo_data, persist_behavior_logs
):
    persist_behavior_logs(
        [
        _make_log(3, 101, "轻量跑鞋", "view", "华东", merchant_id=2, category="运动鞋"),
        _make_log(3, 101, "轻量跑鞋", "favorite", "华东", merchant_id=2, category="运动鞋"),
        _make_log(
            3,
            102,
            "透气训练T恤",
            "purchase",
            "华东",
            merchant_id=2,
            category="运动服饰",
            price=129.0,
        ),
        _make_log(5, 201, "户外冲锋衣", "view", "华南", merchant_id=4, category="户外装备"),
        _make_log(5, 201, "户外冲锋衣", "cart", "华南", merchant_id=4, category="户外装备"),
        ]
    )

    funnel_response = client.get("/api/analytics/funnel", headers=merchant_headers)
    categories_response = client.get("/api/analytics/categories", headers=merchant_headers)
    hot_response = client.get("/api/analytics/products/hot", headers=merchant_headers)
    cold_response = client.get("/api/analytics/products/cold", headers=merchant_headers)
    rfm_response = client.get("/api/analytics/users/rfm", headers=merchant_headers)

    assert funnel_response.status_code == 200
    funnel_items = funnel_response.get_json()["items"]
    assert {item["key"]: item["value"] for item in funnel_items} == {
        "view": 1,
        "click": 0,
        "favorite": 1,
        "cart": 0,
        "purchase": 1,
    }

    assert categories_response.status_code == 200
    categories = categories_response.get_json()["items"]
    assert {item["category"] for item in categories} == {"运动鞋", "运动服饰"}

    assert hot_response.status_code == 200
    hot_products = hot_response.get_json()["items"]
    assert all(item["product_name"] != "户外冲锋衣" for item in hot_products)

    assert cold_response.status_code == 200
    cold_products = cold_response.get_json()["items"]
    assert all(item["product_name"] != "户外冲锋衣" for item in cold_products)

    assert rfm_response.status_code == 200
    rfm_items = rfm_response.get_json()["items"]
    assert {item["user_id"] for item in rfm_items} == {3}


def test_brands_returns_brand_breakdown_for_current_merchant(
    client, merchant_headers, seeded_demo_data, persist_behavior_logs
):
    persist_behavior_logs(
        [
            _make_log(3, 101, "轻量跑鞋", "view", "华东", merchant_id=2),
            _make_log(3, 101, "轻量跑鞋", "purchase", "华东", merchant_id=2),
            {
                **_make_log(4, 102, "透气训练T恤", "favorite", "华南", merchant_id=2),
                "brand": "ActiveWear",
            },
            _make_log(5, 201, "户外冲锋衣", "view", "华南", merchant_id=4),
        ]
    )

    response = client.get("/api/analytics/brands", headers=merchant_headers)

    assert response.status_code == 200
    items = response.get_json()["items"]
    assert {item["brand"] for item in items} == {"云步", "活力穿"}
    assert {item["brand"]: item["count"] for item in items}["云步"] == 2
    assert {item["brand"]: item["count"] for item in items}["活力穿"] == 1


def test_hot_products_prioritizes_recent_activity_with_time_decay(
    client, merchant_headers, seeded_demo_data, persist_behavior_logs
):
    old_timestamp = "2026-05-10T10:00:00"
    latest_timestamp = "2026-05-12T10:00:00"

    logs = []
    for idx in range(1, 21):
        logs.append(
            {
                **_make_log(
                    idx,
                    101,
                    "历史浏览很多的商品",
                    "view",
                    "华东",
                    merchant_id=2,
                ),
                "timestamp": old_timestamp,
            }
        )

    for idx in range(21, 23):
        logs.append(
            {
                **_make_log(
                    idx,
                    202,
                    "近期加购更强的商品",
                    "cart",
                    "华东",
                    merchant_id=2,
                ),
                "timestamp": latest_timestamp,
            }
        )

    persist_behavior_logs(logs)

    response = client.get("/api/analytics/products/hot", headers=merchant_headers)

    assert response.status_code == 200
    items = response.get_json()["items"]
    assert items[0]["product_name"] == "近期加购更强的商品"


def test_customer_cannot_access_merchant_overview(
    client, customer_headers, seeded_demo_data
):
    response = client.get("/api/analytics/overview", headers=customer_headers)

    assert response.status_code == 403
    assert response.get_json()["message"] == "仅商家可查看经营分析"


def test_customer_cannot_access_merchant_detail_analytics(
    client, customer_headers, seeded_demo_data
):
    paths = [
        "/api/analytics/funnel",
        "/api/analytics/regions",
        "/api/analytics/categories",
        "/api/analytics/brands",
        "/api/analytics/products/hot",
        "/api/analytics/products/cold",
        "/api/analytics/users/rfm",
    ]

    for path in paths:
        response = client.get(path, headers=customer_headers)
        assert response.status_code == 403
        assert response.get_json()["message"] == "仅商家可查看经营分析"


def test_analytics_detail_endpoints_return_expected_shapes(
    client, merchant_headers, seeded_demo_data, persist_behavior_logs
):
    persist_behavior_logs(
        [
        _make_log(1, 101, "轻量跑鞋", "view", "华东", merchant_id=2),
        _make_log(1, 101, "轻量跑鞋", "click", "华东", merchant_id=2),
        _make_log(1, 101, "轻量跑鞋", "purchase", "华东", merchant_id=2),
        _make_log(2, 202, "智能运动手环", "view", "华南", merchant_id=2, category="智能设备"),
        _make_log(2, 202, "智能运动手环", "cart", "华南", merchant_id=2, category="智能设备"),
        _make_log(3, 101, "轻量跑鞋", "favorite", "华北", merchant_id=2),
        _make_log(3, 303, "瑜伽垫", "view", "华北", merchant_id=2, category="健身器材"),
        _make_log(9, 404, "户外冲锋衣", "view", "华南", merchant_id=4, category="户外装备"),
        ]
    )

    funnel_response = client.get("/api/analytics/funnel", headers=merchant_headers)
    regions_response = client.get("/api/analytics/regions", headers=merchant_headers)
    categories_response = client.get("/api/analytics/categories", headers=merchant_headers)
    hot_response = client.get("/api/analytics/products/hot", headers=merchant_headers)
    cold_response = client.get("/api/analytics/products/cold", headers=merchant_headers)
    rfm_response = client.get("/api/analytics/users/rfm", headers=merchant_headers)

    assert funnel_response.status_code == 200
    assert funnel_response.get_json()["items"][0]["key"] == "view"

    assert regions_response.status_code == 200
    assert regions_response.get_json()["items"][0]["region"] in {"华东", "华北", "华南"}

    assert categories_response.status_code == 200
    assert categories_response.get_json()["items"][0]["category"] == "运动鞋"

    assert hot_response.status_code == 200
    assert hot_response.get_json()["items"][0]["product_name"] == "轻量跑鞋"
    assert all(
        item["product_name"] != "户外冲锋衣"
        for item in hot_response.get_json()["items"]
    )

    assert cold_response.status_code == 200
    assert cold_response.get_json()["items"][-1]["product_name"] == "轻量跑鞋"
    assert all(
        item["product_name"] != "户外冲锋衣"
        for item in cold_response.get_json()["items"]
    )

    assert rfm_response.status_code == 200
    rfm_items = rfm_response.get_json()["items"]
    assert any(item["user_id"] == 1 for item in rfm_items)
    assert all(item["user_id"] in {1, 2, 3} for item in rfm_items)
    assert all("rfm_label" in item for item in rfm_items)


def test_merchant_user_behavior_endpoint_requires_merchant_role(
    client, customer_headers, seeded_demo_data
):
    response = client.get(
        "/api/analytics/merchant/user-behavior", headers=customer_headers
    )

    assert response.status_code == 403


def test_merchant_user_behavior_endpoint_returns_preference_and_intent_sections(
    client, merchant_headers, seeded_demo_data, persist_behavior_logs
):
    persist_behavior_logs(
        [
        {
            "log_id": "b-1",
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
            "source_channel": "customer_page",
            "session_id": "s-1",
            "stay_duration": 12,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:00:00",
        },
        {
            "log_id": "b-2",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 1,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 299.0,
            "action_type": "cart",
            "region": "华南",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "s-2",
            "stay_duration": 18,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:05:00",
        },
        {
            "log_id": "b-3",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 2,
            "product_name": "透气训练T恤",
            "category": "运动服饰",
            "brand": "CloudStep",
            "price": 129.0,
            "action_type": "purchase",
            "region": "华南",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "s-3",
            "stay_duration": 20,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:10:00",
        },
        ]
    )

    response = client.get(
        "/api/analytics/merchant/user-behavior", headers=merchant_headers
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["preference_changes"] == [
        {
            "category": "运动服饰",
            "top_action": "purchase",
            "action_count": 1,
            "summary": "运动服饰最近购买行为更活跃",
        },
        {
            "category": "运动鞋",
            "top_action": "cart",
            "action_count": 1,
            "summary": "运动鞋最近加购行为更活跃",
        },
    ]
    assert payload["intent_products"] == [
        {
            "product_id": 2,
            "product_name": "透气训练T恤",
            "top_action": "purchase",
            "action_count": 1,
            "summary": "透气训练T恤最近购买较多，值得重点关注",
        },
        {
            "product_id": 1,
            "product_name": "轻量跑鞋",
            "top_action": "cart",
            "action_count": 1,
            "summary": "轻量跑鞋最近加购较多，值得重点关注",
        },
    ]


def test_merchant_user_behavior_only_counts_recent_24_hour_intent_logs(
    client, merchant_headers, seeded_demo_data, persist_behavior_logs
):
    persist_behavior_logs(
        [
        {
            "log_id": "recent-1",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 1,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 299.0,
            "action_type": "cart",
            "region": "华南",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "s-1",
            "stay_duration": 12,
            "is_new_user": False,
            "timestamp": "2026-05-13T12:00:00",
        },
        {
            "log_id": "old-1",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 2,
            "product_name": "透气训练T恤",
            "category": "运动服饰",
            "brand": "CloudStep",
            "price": 129.0,
            "action_type": "purchase",
            "region": "华南",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "s-2",
            "stay_duration": 20,
            "is_new_user": False,
            "timestamp": "2026-05-11T09:00:00",
        },
        ]
    )

    response = client.get("/api/analytics/merchant/user-behavior", headers=merchant_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["preference_changes"]
    assert payload["preference_changes"][0]["category"] == "运动鞋"
    assert all(item["product_name"] != "透气训练T恤" for item in payload["intent_products"])


def test_merchant_user_behavior_summaries_use_chinese_action_labels(
    client, merchant_headers, seeded_demo_data, persist_behavior_logs
):
    persist_behavior_logs(
        [
        {
            "log_id": "cn-1",
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
            "source_channel": "customer_page",
            "session_id": "s-3",
            "stay_duration": 16,
            "is_new_user": False,
            "timestamp": "2026-05-13T12:10:00",
        }
        ]
    )

    response = client.get("/api/analytics/merchant/user-behavior", headers=merchant_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert "收藏" in payload["preference_changes"][0]["summary"]
    assert "favorite" not in payload["preference_changes"][0]["summary"]
