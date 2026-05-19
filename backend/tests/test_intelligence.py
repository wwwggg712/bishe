from datetime import datetime, timedelta


def _make_log(
    *,
    log_id,
    user_id,
    merchant_id,
    product_id,
    product_name,
    category,
    action_type,
    days_ago=0,
    hours_ago=0,
    region="华东",
    price=199.0,
    source_channel="recommendation",
):
    return {
        "log_id": log_id,
        "user_id": user_id,
        "merchant_id": merchant_id,
        "product_id": product_id,
        "product_name": product_name,
        "category": category,
        "brand": "Demo Brand",
        "price": price,
        "action_type": action_type,
        "region": region,
        "device_type": "mobile",
        "source_channel": source_channel,
        "session_id": f"session-{user_id}",
        "stay_duration": 45,
        "is_new_user": False,
        "timestamp": (datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago)).isoformat(),
    }


def _seed_intelligence_logs():
    return [
        _make_log(
            log_id="p1-old-view-1",
            user_id=3,
            merchant_id=2,
            product_id=1,
            product_name="轻量跑鞋",
            category="运动鞋",
            action_type="view",
            days_ago=5,
        ),
        _make_log(
            log_id="p1-old-view-2",
            user_id=3,
            merchant_id=2,
            product_id=1,
            product_name="轻量跑鞋",
            category="运动鞋",
            action_type="view",
            days_ago=4,
        ),
        _make_log(
            log_id="p1-old-click",
            user_id=3,
            merchant_id=2,
            product_id=1,
            product_name="轻量跑鞋",
            category="运动鞋",
            action_type="click",
            days_ago=4,
        ),
        _make_log(
            log_id="p1-new-view-1",
            user_id=3,
            merchant_id=2,
            product_id=1,
            product_name="轻量跑鞋",
            category="运动鞋",
            action_type="view",
            days_ago=1,
        ),
        _make_log(
            log_id="p1-new-view-2",
            user_id=3,
            merchant_id=2,
            product_id=1,
            product_name="轻量跑鞋",
            category="运动鞋",
            action_type="view",
            days_ago=1,
        ),
        _make_log(
            log_id="p1-new-click",
            user_id=3,
            merchant_id=2,
            product_id=1,
            product_name="轻量跑鞋",
            category="运动鞋",
            action_type="click",
            days_ago=1,
        ),
        _make_log(
            log_id="p1-new-cart",
            user_id=3,
            merchant_id=2,
            product_id=1,
            product_name="轻量跑鞋",
            category="运动鞋",
            action_type="cart",
            days_ago=0,
        ),
        _make_log(
            log_id="p1-new-purchase",
            user_id=3,
            merchant_id=2,
            product_id=1,
            product_name="轻量跑鞋",
            category="运动鞋",
            action_type="purchase",
            days_ago=0,
        ),
        _make_log(
            log_id="p2-old-view-1",
            user_id=3,
            merchant_id=2,
            product_id=2,
            product_name="透气训练T恤",
            category="运动服饰",
            action_type="view",
            days_ago=5,
        ),
        _make_log(
            log_id="p2-old-click-1",
            user_id=3,
            merchant_id=2,
            product_id=2,
            product_name="透气训练T恤",
            category="运动服饰",
            action_type="click",
            days_ago=5,
        ),
        _make_log(
            log_id="p2-old-click-2",
            user_id=3,
            merchant_id=2,
            product_id=2,
            product_name="透气训练T恤",
            category="运动服饰",
            action_type="click",
            days_ago=4,
        ),
        _make_log(
            log_id="p2-old-cart",
            user_id=3,
            merchant_id=2,
            product_id=2,
            product_name="透气训练T恤",
            category="运动服饰",
            action_type="cart",
            days_ago=4,
        ),
        _make_log(
            log_id="p2-new-view",
            user_id=3,
            merchant_id=2,
            product_id=2,
            product_name="透气训练T恤",
            category="运动服饰",
            action_type="view",
            days_ago=1,
        ),
        _make_log(
            log_id="p3-reco-view-1",
            user_id=3,
            merchant_id=2,
            product_id=3,
            product_name="智能运动手环",
            category="智能设备",
            action_type="view",
            days_ago=0,
        ),
        _make_log(
            log_id="p3-reco-view-2",
            user_id=3,
            merchant_id=2,
            product_id=3,
            product_name="智能运动手环",
            category="智能设备",
            action_type="view",
            days_ago=0,
        ),
        _make_log(
            log_id="p3-reco-click",
            user_id=3,
            merchant_id=2,
            product_id=3,
            product_name="智能运动手环",
            category="智能设备",
            action_type="click",
            days_ago=0,
        ),
        _make_log(
            log_id="p3-reco-purchase",
            user_id=3,
            merchant_id=2,
            product_id=3,
            product_name="智能运动手环",
            category="智能设备",
            action_type="purchase",
            days_ago=0,
        ),
    ]


def _seed_profile_logs():
    return [
        _make_log(
            log_id="profile-1",
            user_id=3,
            merchant_id=2,
            product_id=11,
            product_name="旗舰跑鞋",
            category="运动鞋",
            action_type="view",
            days_ago=3,
            hours_ago=6,
            source_channel="customer_page",
        ),
        _make_log(
            log_id="profile-2",
            user_id=3,
            merchant_id=2,
            product_id=12,
            product_name="轻盈卫衣",
            category="运动服饰",
            action_type="favorite",
            days_ago=2,
            hours_ago=18,
            source_channel="customer_page",
        ),
        _make_log(
            log_id="profile-3",
            user_id=3,
            merchant_id=2,
            product_id=13,
            product_name="智能耳机",
            category="智能设备",
            action_type="purchase",
            days_ago=1,
            hours_ago=20,
            price=399.0,
            source_channel="customer_page",
        ),
        _make_log(
            log_id="profile-4",
            user_id=3,
            merchant_id=2,
            product_id=13,
            product_name="智能耳机",
            category="智能设备",
            action_type="click",
            days_ago=1,
            hours_ago=10,
            price=399.0,
            source_channel="customer_page",
        ),
        _make_log(
            log_id="profile-5",
            user_id=3,
            merchant_id=2,
            product_id=14,
            product_name="露营灯",
            category="户外装备",
            action_type="cart",
            days_ago=1,
            hours_ago=6,
            price=159.0,
            source_channel="customer_page",
        ),
        _make_log(
            log_id="profile-6",
            user_id=3,
            merchant_id=2,
            product_id=15,
            product_name="智能手表",
            category="智能设备",
            action_type="purchase",
            hours_ago=5,
            price=599.0,
            source_channel="customer_page",
        ),
        _make_log(
            log_id="profile-7",
            user_id=3,
            merchant_id=2,
            product_id=15,
            product_name="智能手表",
            category="智能设备",
            action_type="click",
            hours_ago=4,
            price=599.0,
            source_channel="customer_page",
        ),
        _make_log(
            log_id="profile-8",
            user_id=3,
            merchant_id=2,
            product_id=16,
            product_name="跑步腰包",
            category="运动鞋",
            action_type="view",
            hours_ago=3,
            price=99.0,
            source_channel="customer_page",
        ),
        _make_log(
            log_id="profile-9",
            user_id=3,
            merchant_id=2,
            product_id=17,
            product_name="训练短裤",
            category="运动服饰",
            action_type="favorite",
            hours_ago=2,
            price=129.0,
            source_channel="customer_page",
        ),
        _make_log(
            log_id="profile-10",
            user_id=3,
            merchant_id=2,
            product_id=18,
            product_name="登山水壶",
            category="户外装备",
            action_type="cart",
            hours_ago=1,
            price=89.0,
            source_channel="customer_page",
        ),
        _make_log(
            log_id="profile-11",
            user_id=9,
            merchant_id=4,
            product_id=22,
            product_name="无关商品",
            category="家居",
            action_type="purchase",
            hours_ago=1,
            region="华南",
        ),
    ]


def _seed_anomaly_logs():
    return [
        _make_log(
            log_id="baseline-view-1",
            user_id=3,
            merchant_id=2,
            product_id=31,
            product_name="爆款跑鞋",
            category="运动鞋",
            action_type="view",
            days_ago=4,
            region="华东",
        ),
        _make_log(
            log_id="baseline-view-2",
            user_id=3,
            merchant_id=2,
            product_id=31,
            product_name="爆款跑鞋",
            category="运动鞋",
            action_type="view",
            days_ago=4,
            hours_ago=1,
            region="华东",
        ),
        _make_log(
            log_id="baseline-purchase",
            user_id=3,
            merchant_id=2,
            product_id=31,
            product_name="爆款跑鞋",
            category="运动鞋",
            action_type="purchase",
            days_ago=4,
            hours_ago=2,
            region="华东",
        ),
        _make_log(
            log_id="recent-view-1",
            user_id=3,
            merchant_id=2,
            product_id=31,
            product_name="爆款跑鞋",
            category="运动鞋",
            action_type="view",
            hours_ago=12,
            region="华东",
        ),
        _make_log(
            log_id="recent-view-2",
            user_id=4,
            merchant_id=2,
            product_id=31,
            product_name="爆款跑鞋",
            category="运动鞋",
            action_type="view",
            hours_ago=11,
            region="华东",
        ),
        _make_log(
            log_id="recent-view-3",
            user_id=5,
            merchant_id=2,
            product_id=31,
            product_name="爆款跑鞋",
            category="运动鞋",
            action_type="view",
            hours_ago=10,
            region="华东",
        ),
        _make_log(
            log_id="recent-view-4",
            user_id=6,
            merchant_id=2,
            product_id=31,
            product_name="爆款跑鞋",
            category="运动鞋",
            action_type="view",
            hours_ago=9,
            region="华东",
        ),
        _make_log(
            log_id="recent-view-5",
            user_id=7,
            merchant_id=2,
            product_id=31,
            product_name="爆款跑鞋",
            category="运动鞋",
            action_type="view",
            hours_ago=8,
            region="华东",
        ),
        _make_log(
            log_id="recent-view-6",
            user_id=8,
            merchant_id=2,
            product_id=31,
            product_name="爆款跑鞋",
            category="运动鞋",
            action_type="view",
            hours_ago=7,
            region="华东",
        ),
    ]


def test_prediction_returns_trend_labels(client, auth_headers, persist_behavior_logs):
    persist_behavior_logs(_seed_intelligence_logs())

    response = client.get("/api/prediction/trends", headers=auth_headers)
    assert response.status_code == 200

    payload = response.get_json()
    assert "items" in payload
    assert payload["items"][0]["trend_label"] in {"up", "down", "flat"}


def test_customer_recommendations_include_reason(
    client, customer_headers, persist_behavior_logs
):
    persist_behavior_logs(_seed_intelligence_logs())

    response = client.get("/api/recommendations/me", headers=customer_headers)
    assert response.status_code == 200

    item = response.get_json()["items"][0]
    assert "reason" in item
    assert item["reason"]


def test_customer_portrait_returns_cold_start_when_no_personal_logs(
    client, customer_headers, seeded_demo_data, persist_behavior_logs
):
    persist_behavior_logs(
        [
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
    )

    response = client.get("/api/users/portrait", headers=customer_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["is_cold_start"] is True
    assert payload["top_categories"] == []
    assert payload["price_preference"]["price_band"] == "暂无数据"


def test_users_portrait_ignores_simulated_history_for_top_actions_and_recent_activity(
    client, customer_headers, seeded_demo_data, persist_behavior_logs
):
    persist_behavior_logs(
        [
        {
            "log_id": "sim-portrait-1",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 11,
            "product_name": "旗舰跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 399.0,
            "action_type": "click",
            "region": "华东",
            "device_type": "mobile",
            "source_channel": "recommendation",
            "session_id": "sim-portrait-session-1",
            "stay_duration": 35,
            "is_new_user": False,
            "timestamp": "2026-05-13T09:00:00",
        }
        ]
    )

    response = client.get("/api/users/portrait", headers=customer_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["is_cold_start"] is True
    assert payload["top_actions"] == []
    assert payload["recent_activity"] == []


def test_users_portrait_only_uses_customer_page_logs_in_ranked_sections(
    client, customer_headers, seeded_demo_data, persist_behavior_logs
):
    persist_behavior_logs(
        [
        {
            "log_id": "sim-portrait-2",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 11,
            "product_name": "旗舰跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 399.0,
            "action_type": "click",
            "region": "华东",
            "device_type": "mobile",
            "source_channel": "recommendation",
            "session_id": "sim-portrait-session-2",
            "stay_duration": 35,
            "is_new_user": False,
            "timestamp": "2026-05-13T09:00:00",
        },
        {
            "log_id": "real-portrait-1",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 12,
            "product_name": "轻盈卫衣",
            "category": "运动服饰",
            "brand": "CloudStep",
            "price": 129.0,
            "action_type": "favorite",
            "region": "华东",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "real-portrait-session-1",
            "stay_duration": 18,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:00:00",
        },
        {
            "log_id": "real-portrait-2",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 13,
            "product_name": "智能手表",
            "category": "智能设备",
            "brand": "CloudStep",
            "price": 599.0,
            "action_type": "purchase",
            "region": "华东",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "real-portrait-session-2",
            "stay_duration": 42,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:05:00",
        },
        ]
    )

    response = client.get("/api/users/portrait", headers=customer_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["is_cold_start"] is False
    assert {item["action_type"] for item in payload["top_actions"]} <= {
        "favorite",
        "purchase",
    }
    assert {item["log_id"] for item in payload["recent_activity"]} == {
        "real-portrait-1",
        "real-portrait-2",
    }


def test_customer_recommendations_fall_back_when_no_personal_candidates(
    client, customer_headers, seeded_demo_data, persist_behavior_logs
):
    from app.models.product import Product

    with client.application.app_context():
        products = Product.query.order_by(Product.id.asc()).all()

    persist_behavior_logs(
        [
        {
            "log_id": f"c-{index}",
            "user_id": 3,
            "merchant_id": product.merchant_id,
            "product_id": product.id,
            "product_name": product.name,
            "category": product.category,
            "brand": product.brand,
            "price": float(product.price),
            "action_type": "purchase" if index == 1 else "favorite",
            "region": "华南",
            "device_type": "mobile",
            "source_channel": "detail",
            "session_id": f"s-{index}",
            "stay_duration": 15 + index,
            "is_new_user": False,
            "timestamp": f"2026-05-13T10:{index:02d}:00",
        }
        for index, product in enumerate(products, start=1)
        ]
    )

    response = client.get("/api/recommendations/me", headers=customer_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["mode"] == "fallback"
    assert payload["items"]
    assert "冷启动推荐" in payload["items"][0]["reason"]


def test_customer_recommendations_ignore_simulated_history_and_stay_fallback(
    client, customer_headers, seeded_demo_data, persist_behavior_logs
):
    persist_behavior_logs(
        [
        {
            "log_id": "sim-1",
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
            "session_id": "sim-session-1",
            "stay_duration": 22,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:20:00",
        },
        {
            "log_id": "sim-2",
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
            "session_id": "sim-session-2",
            "stay_duration": 17,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:25:00",
        },
        ]
    )

    response = client.get("/api/recommendations/me", headers=customer_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["mode"] == "fallback"
    assert payload["items"]
    assert "冷启动推荐" in payload["items"][0]["reason"]


def test_customer_recommendations_use_customer_page_logs_for_personalization(
    client, customer_headers, seeded_demo_data, persist_behavior_logs
):
    persist_behavior_logs(
        [
            {
                "log_id": "sim-1",
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
                "session_id": "sim-session-3",
                "stay_duration": 22,
                "is_new_user": False,
                "timestamp": "2026-05-13T10:20:00",
            },
            {
                "log_id": "real-1",
                "user_id": 3,
                "merchant_id": 2,
                "product_id": 2,
                "product_name": "透气训练T恤",
                "category": "运动服饰",
                "brand": "CloudStep",
                "price": 129.0,
                "action_type": "favorite",
                "region": "华南",
                "device_type": "mobile",
                "source_channel": "customer_page",
                "session_id": "real-session-1",
                "stay_duration": 18,
                "is_new_user": False,
                "timestamp": "2026-05-13T10:30:00",
            },
        ]
    )

    response = client.get("/api/recommendations/me", headers=customer_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["mode"] == "personalized"
    assert payload["items"]
    assert "运动服饰" in payload["items"][0]["reason"] or "运动服饰" in "".join(
        item["reason"] for item in payload["items"]
    )
    assert "热度" in payload["items"][0]["reason"] or "热度" in "".join(
        item["reason"] for item in payload["items"]
    )


def test_customer_recommendations_return_personalized_mode_when_candidates_exist(
    client, customer_headers, seeded_demo_data, persist_behavior_logs
):
    persist_behavior_logs(
        [
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
            "source_channel": "customer_page",
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
    )

    response = client.get("/api/recommendations/me", headers=customer_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["mode"] == "personalized"
    assert payload["items"]


def test_customer_can_record_recommendation_action(client, customer_headers, seeded_demo_data):
    from app.models.behavior_log import BehaviorLog

    response = client.post(
        "/api/recommendations/actions",
        headers=customer_headers,
        json={"product_id": 1, "action_type": "favorite"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["message"] == "用户行为记录成功"
    assert payload["log"]["product_id"] == 1
    assert payload["log"]["action_type"] == "favorite"
    assert BehaviorLog.query.count() == 1


def test_non_customer_cannot_record_recommendation_action(client, merchant_headers, seeded_demo_data):
    response = client.post(
        "/api/recommendations/actions",
        headers=merchant_headers,
        json={"product_id": 1, "action_type": "view"},
    )

    assert response.status_code == 403


def test_customer_action_turns_cold_start_portrait_into_active_portrait(
    client, customer_headers, seeded_demo_data
):
    before_response = client.get("/api/users/portrait", headers=customer_headers)
    assert before_response.status_code == 200
    assert before_response.get_json()["is_cold_start"] is True

    action_response = client.post(
        "/api/recommendations/actions",
        headers=customer_headers,
        json={"product_id": 1, "action_type": "purchase"},
    )
    assert action_response.status_code == 200

    after_response = client.get("/api/users/portrait", headers=customer_headers)
    assert after_response.status_code == 200
    payload = after_response.get_json()
    assert payload["is_cold_start"] is False
    assert payload["engagement_score"] > 0


def test_merchant_strategy_returns_actions(client, merchant_headers, persist_behavior_logs):
    persist_behavior_logs(_seed_intelligence_logs())

    response = client.get("/api/strategy/merchant", headers=merchant_headers)
    assert response.status_code == 200

    payload = response.get_json()
    assert len(payload["items"]) > 0
    assert "action" in payload["items"][0]


def test_prediction_profile_limits_ranked_sections(
    client, customer_headers, persist_behavior_logs
):
    persist_behavior_logs(_seed_profile_logs())

    response = client.get("/api/prediction/profile", headers=customer_headers)
    assert response.status_code == 200

    payload = response.get_json()
    profile = payload["profile"]
    assert len(profile["top_categories"]) == 3
    assert len(profile["top_actions"]) == 5
    assert len(profile["recent_activity"]) == 5
    assert profile["top_categories"][0]["category"] == "智能设备"
    assert profile["recent_activity"][0]["log_id"] == "profile-10"
    assert profile["recent_activity"][-1]["log_id"] == "profile-6"


def test_users_portrait_returns_analysis_style_payload(
    client, customer_headers, persist_behavior_logs
):
    persist_behavior_logs(_seed_profile_logs())

    response = client.get("/api/users/portrait", headers=customer_headers)
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["user"]["username"] == "customer_demo"
    assert len(payload["top_categories"]) == 3
    assert len(payload["top_actions"]) == 5
    assert len(payload["recent_activity"]) == 5
    assert payload["top_categories"][0]["category"] == "智能设备"
    assert payload["engagement_score"] > 0
    assert payload["price_preference"]["average_price"] > 0
    assert payload["price_preference"]["price_band"]
    assert len(payload["top_active_hours"]) > 0
    assert len(payload["profile_tags"]) >= 2


def test_prediction_anomalies_grade_severity_against_baseline(
    client, merchant_headers, persist_behavior_logs
):
    persist_behavior_logs(_seed_anomaly_logs())

    response = client.get("/api/prediction/anomalies", headers=merchant_headers)
    assert response.status_code == 200

    payload = response.get_json()
    assert len(payload["items"]) > 0
    anomaly = payload["items"][0]
    assert anomaly["severity"] == "high"
    assert anomaly["current_value"] > anomaly["baseline_value"]
    assert anomaly["change_ratio"] > 2
    assert "z_score" in anomaly
    assert anomaly["z_score"] >= 2.0
    assert anomaly["baseline"] == anomaly["baseline_value"]
    assert anomaly["delta"] == anomaly["current_value"] - anomaly["baseline"]
    assert anomaly["reason"]


def test_prediction_anomalies_supports_severity_filter(
    client, merchant_headers, persist_behavior_logs
):
    persist_behavior_logs(_seed_anomaly_logs())

    response = client.get(
        "/api/prediction/anomalies?severity=high", headers=merchant_headers
    )
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["items"]
    assert all(item["severity"] == "high" for item in payload["items"])


def test_merchant_anomalies_only_include_current_merchant_logs(
    client, merchant_headers, seeded_demo_data, persist_behavior_logs
):
    persist_behavior_logs(
        [
        {
            "log_id": "m2-view-1",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 101,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 299.0,
            "action_type": "view",
            "region": "华东",
            "device_type": "mobile",
            "source_channel": "homepage",
            "session_id": "m2-s1",
            "stay_duration": 20,
            "is_new_user": False,
            "timestamp": "2026-05-12T10:00:00",
        },
        {
            "log_id": "m2-view-2",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 101,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 299.0,
            "action_type": "view",
            "region": "华东",
            "device_type": "mobile",
            "source_channel": "homepage",
            "session_id": "m2-s2",
            "stay_duration": 20,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:00:00",
        },
        {
            "log_id": "m2-view-3",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 101,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 299.0,
            "action_type": "view",
            "region": "华东",
            "device_type": "mobile",
            "source_channel": "homepage",
            "session_id": "m2-s3",
            "stay_duration": 20,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:05:00",
        },
        {
            "log_id": "m4-view-1",
            "user_id": 8,
            "merchant_id": 4,
            "product_id": 404,
            "product_name": "户外冲锋衣",
            "category": "户外装备",
            "brand": "TrailX",
            "price": 599.0,
            "action_type": "view",
            "region": "华南",
            "device_type": "desktop",
            "source_channel": "homepage",
            "session_id": "m4-s1",
            "stay_duration": 30,
            "is_new_user": False,
            "timestamp": "2026-05-12T10:00:00",
        },
        {
            "log_id": "m4-view-2",
            "user_id": 8,
            "merchant_id": 4,
            "product_id": 404,
            "product_name": "户外冲锋衣",
            "category": "户外装备",
            "brand": "TrailX",
            "price": 599.0,
            "action_type": "view",
            "region": "华南",
            "device_type": "desktop",
            "source_channel": "homepage",
            "session_id": "m4-s2",
            "stay_duration": 30,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:00:00",
        },
        {
            "log_id": "m4-view-3",
            "user_id": 8,
            "merchant_id": 4,
            "product_id": 404,
            "product_name": "户外冲锋衣",
            "category": "户外装备",
            "brand": "TrailX",
            "price": 599.0,
            "action_type": "view",
            "region": "华南",
            "device_type": "desktop",
            "source_channel": "homepage",
            "session_id": "m4-s3",
            "stay_duration": 30,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:05:00",
        },
        ]
    )

    response = client.get(
        "/api/prediction/anomalies?severity=high", headers=merchant_headers
    )

    assert response.status_code == 200
    items = response.get_json()["items"]
    assert items
    assert all(item["target"] != "户外冲锋衣" for item in items)


def test_customer_cannot_access_merchant_scoped_anomaly_insights(
    client, customer_headers, seeded_demo_data
):
    response = client.get(
        "/api/prediction/anomalies?severity=high", headers=customer_headers
    )

    assert response.status_code == 403
    assert response.get_json()["message"] == "仅商家可查看异常预警"


def test_customer_portrait_price_preference_prioritizes_purchase_logs(
    client, customer_headers, seeded_demo_data, persist_behavior_logs
):
    persist_behavior_logs(
        [
        {
            "log_id": "pp-1",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 1,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 999.0,
            "action_type": "view",
            "region": "华南",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "s-1",
            "stay_duration": 10,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:00:00",
        },
        {
            "log_id": "pp-2",
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
            "stay_duration": 30,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:05:00",
        },
        ]
    )

    response = client.get("/api/users/portrait", headers=customer_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["price_preference"]["average_price"] == 129.0


def test_customer_portrait_price_preference_falls_back_to_cart_and_favorite(
    client, customer_headers, seeded_demo_data, persist_behavior_logs
):
    persist_behavior_logs(
        [
        {
            "log_id": "pf-1",
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
            "stay_duration": 10,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:10:00",
        },
        {
            "log_id": "pf-2",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 2,
            "product_name": "透气训练T恤",
            "category": "运动服饰",
            "brand": "CloudStep",
            "price": 129.0,
            "action_type": "cart",
            "region": "华南",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "s-4",
            "stay_duration": 18,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:12:00",
        },
        {
            "log_id": "pf-3",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 3,
            "product_name": "智能运动手环",
            "category": "智能设备",
            "brand": "CloudStep",
            "price": 999.0,
            "action_type": "view",
            "region": "华南",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "s-5",
            "stay_duration": 40,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:15:00",
        },
        ]
    )

    response = client.get("/api/users/portrait", headers=customer_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["price_preference"]["average_price"] == 214.0
    assert payload["price_preference"]["price_band"] == "中高消费偏好"


def test_customer_portrait_price_preference_returns_no_data_without_intent_actions(
    client, customer_headers, seeded_demo_data, persist_behavior_logs
):
    persist_behavior_logs(
        [
        {
            "log_id": "pn-1",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 1,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 299.0,
            "action_type": "view",
            "region": "华南",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "s-6",
            "stay_duration": 15,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:20:00",
        }
        ]
    )

    response = client.get("/api/users/portrait", headers=customer_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["price_preference"]["average_price"] == 0
    assert payload["price_preference"]["price_band"] == "暂无数据"


def test_customer_recommendations_exclude_inactive_and_out_of_stock_products(
    client, customer_headers, seeded_demo_data, persist_behavior_logs
):
    from app.extensions import db
    from app.models.product import Product

    persist_behavior_logs(
        [
        _make_log(
            log_id=f"sold-out-hot-{index}",
            user_id=9,
            merchant_id=2,
            product_id=2,
            product_name="透气训练T恤",
            category="运动服饰",
            action_type="purchase",
            hours_ago=index,
        )
        for index in range(6)
        ]
    )

    products = Product.query.order_by(Product.id.asc()).all()
    for product in products:
        product.stock = 0
        product.is_active = True

    inactive_product = db.session.get(Product, 1)
    inactive_product.stock = 500
    inactive_product.is_active = False

    sold_out_product = db.session.get(Product, 2)
    sold_out_product.stock = 0

    for product_id in (3, 4, 5, 6):
        candidate = db.session.get(Product, product_id)
        candidate.stock = 10

    db.session.commit()

    response = client.get("/api/recommendations/me", headers=customer_headers)

    assert response.status_code == 200
    payload = response.get_json()
    product_ids = {item["product_id"] for item in payload["items"]}
    assert 1 not in product_ids
    assert 2 not in product_ids
    assert product_ids == {3, 4, 5, 6}


def test_customer_cannot_record_action_for_unsaleable_product(
    client, customer_headers, seeded_demo_data
):
    from app.extensions import db
    from app.models.product import Product

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
