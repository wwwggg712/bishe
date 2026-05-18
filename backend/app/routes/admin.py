import os
from datetime import datetime, timedelta
from collections import Counter

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required
from sqlalchemy import func

from ..extensions import db
from ..models.behavior_log import BehaviorLog
from ..models.product import Product
from ..models.user import User
from ..services.analytics_service import AnalyticsService
from ..services.prediction_service import PredictionService
from ..tasks.jobs import execute_job, list_jobs

bp = Blueprint("admin", __name__, url_prefix="/api/admin")
analytics_service = AnalyticsService()
prediction_service = PredictionService()


def _ensure_admin():
    if get_jwt().get("role") != "admin":
        return jsonify({"message": "仅管理员可执行该操作"}), 403
    return None


@bp.get("/overview")
@jwt_required()
def overview():
    unauthorized = _ensure_admin()
    if unauthorized is not None:
        return unauthorized

    jobs = list_jobs()
    users = [user.to_dict() for user in User.query.order_by(User.id.asc()).limit(5).all()]
    logs = [
        {
            "id": job["name"],
            "level": "INFO" if job["status"] != "failed" else "ERROR",
            "timestamp": job["lastRunAt"],
            "message": f'{job["title"]} 当前状态：{job["status"]}',
        }
        for job in jobs
    ]

    return jsonify(
        {
            "metrics": {
                "logCount": BehaviorLog.query.count(),
                "userCount": User.query.count(),
                "productCount": Product.query.count(),
                "activeJobs": sum(1 for job in jobs if job["status"] == "running"),
            },
            "logs": logs,
            "users": users,
        }
    )


@bp.get("/jobs")
@jwt_required()
def jobs():
    unauthorized = _ensure_admin()
    if unauthorized is not None:
        return unauthorized

    return jsonify({"jobs": list_jobs()})


@bp.get("/users")
@jwt_required()
def users():
    unauthorized = _ensure_admin()
    if unauthorized is not None:
        return unauthorized

    users = [user.to_dict() for user in User.query.order_by(User.id.asc()).all()]
    return jsonify({"total": len(users), "users": users})


@bp.get("/logs/preview")
@jwt_required()
def logs_preview():
    unauthorized = _ensure_admin()
    if unauthorized is not None:
        return unauthorized

    try:
        page = int(request.args.get("page", 1))
    except (TypeError, ValueError):
        page = 1

    try:
        page_size = int(request.args.get("page_size", 20))
    except (TypeError, ValueError):
        page_size = 20

    page = max(page, 1)
    page_size = max(min(page_size, 200), 1)

    query = BehaviorLog.query.order_by(BehaviorLog.timestamp.desc())
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    recent_logs = [item.to_dict() for item in pagination.items]

    action_rows = (
        db.session.query(BehaviorLog.action_type, func.count(BehaviorLog.id))
        .group_by(BehaviorLog.action_type)
        .order_by(func.count(BehaviorLog.id).desc())
        .all()
    )
    action_counter = Counter({row[0]: row[1] for row in action_rows})
    latest_log = query.first()
    latest_timestamp = (
        latest_log.timestamp.isoformat(timespec="seconds") if latest_log else "暂无数据"
    )

    return jsonify(
        {
            "summary": {
                "total_logs": pagination.total,
                "latest_timestamp": latest_timestamp,
                "sample_generated_count": len(recent_logs),
                "action_type_count": len(action_counter),
                "page": page,
                "page_size": page_size,
            },
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": pagination.total,
                "pages": pagination.pages,
            },
            "action_breakdown": [
                {"action_type": action_type, "count": count}
                for action_type, count in action_counter.most_common()
            ],
            "generation_note": (
                "日志由系统模拟器按浏览、点击、收藏、加购、购买行为链路生成，"
                "用于热度、漏斗、RFM、趋势和异常分析。"
            ),
            "recent_logs": recent_logs,
        }
    )


@bp.get("/logs/metrics")
@jwt_required()
def logs_metrics():
    unauthorized = _ensure_admin()
    if unauthorized is not None:
        return unauthorized

    selected_category = request.args.get("category")
    total_logs = BehaviorLog.query.count()
    latest_log = BehaviorLog.query.order_by(BehaviorLog.created_at.desc()).first()
    latest_timestamp = (
        latest_log.created_at.isoformat(timespec="seconds") if latest_log else "暂无数据"
    )

    threshold = datetime.utcnow() - timedelta(minutes=1)
    last_minute_added = BehaviorLog.query.filter(BehaviorLog.created_at >= threshold).count()

    action_rows = (
        db.session.query(BehaviorLog.action_type, func.count(BehaviorLog.id))
        .group_by(BehaviorLog.action_type)
        .order_by(func.count(BehaviorLog.id).desc())
        .all()
    )

    category_rows = (
        db.session.query(func.coalesce(BehaviorLog.category, "未知品类"), func.count(BehaviorLog.id))
        .group_by(func.coalesce(BehaviorLog.category, "未知品类"))
        .order_by(func.count(BehaviorLog.id).desc())
        .limit(10)
        .all()
    )
    category_items = [{"category": category, "count": count} for category, count in category_rows]
    if not selected_category and category_items:
        selected_category = category_items[0]["category"]
    brand_rows = (
        db.session.query(func.coalesce(BehaviorLog.brand, "未知品牌"), func.count(BehaviorLog.id))
        .group_by(func.coalesce(BehaviorLog.brand, "未知品牌"))
        .filter(
            BehaviorLog.category == selected_category
            if selected_category and selected_category != "未知品类"
            else True
        )
        .order_by(func.count(BehaviorLog.id).desc())
        .limit(10)
        .all()
    )
    brand_display = AnalyticsService.BRAND_DISPLAY

    return jsonify(
        {
            "summary": {
                "total_logs": total_logs,
                "latest_timestamp": latest_timestamp,
                "last_minute_added": last_minute_added,
            },
            "action_breakdown": [
                {"action_type": action_type, "count": count}
                for action_type, count in action_rows
            ],
            "brand_breakdown": [
            "category_breakdown": category_items,
            "selected_category": selected_category or "",
                {"brand": brand_display.get(brand, brand), "count": count}
                for brand, count in brand_rows
            ],
        }
    )



@bp.get("/algorithm-pipeline")
@jwt_required()
def algorithm_pipeline():
    unauthorized = _ensure_admin()
    if unauthorized is not None:
        return unauthorized

    logs = [item.to_dict() for item in BehaviorLog.query.order_by(BehaviorLog.timestamp.asc()).all()]
    action_counter = Counter(log["action_type"] for log in logs)
    latest_log = BehaviorLog.query.order_by(BehaviorLog.timestamp.desc()).first()
    latest_timestamp = (
        latest_log.timestamp.isoformat(timespec="seconds") if latest_log else "暂无数据"
    )
    overview = analytics_service.build_overview(logs)
    hot_items = analytics_service.build_hot_products(logs)["items"]
    cold_items = analytics_service.build_cold_products(logs)["items"]
    anomalies = prediction_service.build_anomalies(logs)["items"]
    segmentation = analytics_service.build_user_rfm(logs)["items"]
    customer_logs = [
        log for log in logs if log.get("source_channel") == "customer_page"
    ]

    provider = os.getenv("LLM_PROVIDER", "").strip()
    api_key = os.getenv("LLM_API_KEY", "").strip()
    base_url = os.getenv("LLM_BASE_URL", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()
    has_provider = bool(provider and api_key and base_url and model)

    return jsonify(
        {
            "log_input": {
                "total_logs": len(logs),
                "action_type_count": len(action_counter),
                "latest_timestamp": latest_timestamp,
            },
            "aggregation": {
                "behavior_count": overview["totals"]["behavior_count"],
                "view_count": overview["totals"]["view_count"],
                "purchase_count": overview["totals"]["purchase_count"],
                "region_count": len(overview["regions"]),
            },
            "scoring": {
                "weight_rule": "view=1, click=2, favorite=3, cart=5, purchase=8",
                "hot_product_count": len(hot_items),
                "cold_product_count": len(cold_items),
            },
            "portrait_and_recommendation": {
                "real_action_logs": len(customer_logs),
                "cold_start_state": "冷启动" if not customer_logs else "已进入个性化",
                "recommendation_mode": "fallback"
                if not customer_logs
                else "personalized",
            },
            "anomalies": {
                "high_risk_count": sum(
                    1 for item in anomalies if item.get("severity") == "high"
                ),
                "medium_risk_count": sum(
                    1 for item in anomalies if item.get("severity") == "medium"
                ),
                "window_rule": "最近2天 vs 前3天",
            },
            "segmentation": {
                "high_value_users": sum(
                    1 for item in segmentation if item.get("rfm_label") == "高价值用户"
                ),
                "potential_users": sum(
                    1 for item in segmentation if item.get("rfm_label") == "潜力转化用户"
                ),
                "inactive_users": sum(
                    1 for item in segmentation if item.get("rfm_label") == "待激活用户"
                ),
            },
            "ai_meta": {
                "mode": "provider" if has_provider else "fallback",
                "provider": provider or "internal",
                "model": model or "rule-based-fallback",
            },
        }
    )


@bp.post("/logs/cleanup")
@jwt_required()
def logs_cleanup():
    unauthorized = _ensure_admin()
    if unauthorized is not None:
        return unauthorized

    payload = request.get_json(silent=True) or {}
    keep_last = payload.get("keep_last")
    try:
        keep_last = int(keep_last)
    except (TypeError, ValueError):
        keep_last = None

    if keep_last is None:
        return jsonify({"message": "keep_last 非法"}), 400

    keep_last = max(min(keep_last, 500000), 1)
    total_before = BehaviorLog.query.count()
    if total_before <= keep_last:
        return jsonify(
            {
                "total_before": total_before,
                "kept_count": total_before,
                "deleted_count": 0,
            }
        )

    keep_ids_subquery = (
        db.session.query(BehaviorLog.id)
        .order_by(BehaviorLog.timestamp.desc(), BehaviorLog.id.desc())
        .limit(keep_last)
        .subquery()
    )
    deleted_count = (
        BehaviorLog.query.filter(~BehaviorLog.id.in_(db.session.query(keep_ids_subquery.c.id)))
        .delete(synchronize_session=False)
    )
    db.session.commit()
    kept_count = BehaviorLog.query.count()

    return jsonify(
        {
            "total_before": total_before,
            "kept_count": kept_count,
            "deleted_count": deleted_count,
        }
    )


@bp.post("/jobs/run")
@jwt_required()
def run_job():
    unauthorized = _ensure_admin()
    if unauthorized is not None:
        return unauthorized

    data = request.get_json(silent=True) or {}
    job_name = (data.get("job_name") or "").strip()
    if not job_name:
        return jsonify({"message": "缺少 job_name"}), 400

    try:
        result = execute_job(job_name)
    except KeyError:
        return jsonify({"message": "任务不存在"}), 404

    return jsonify({"message": f"任务 {job_name} 已执行", "result": result})
