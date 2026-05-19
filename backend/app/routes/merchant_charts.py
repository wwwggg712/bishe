from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from sqlalchemy import func

from ..extensions import db
from ..models.behavior_log import BehaviorLog
from ..services.analytics_service import AnalyticsService


bp = Blueprint("merchant_charts", __name__, url_prefix="/api/merchant/charts")


def _ensure_merchant():
    if get_jwt().get("role") != "merchant":
        return jsonify({"message": "仅商家可查看图表"}), 403
    return None


@bp.get("/share")
@jwt_required()
def share():
    unauthorized = _ensure_merchant()
    if unauthorized is not None:
        return unauthorized

    merchant_id = int(get_jwt_identity())
    top_n = int(request.args.get("top_n", 5))

    category_rows = (
        db.session.query(func.coalesce(BehaviorLog.category, "未知品类"), func.count(BehaviorLog.id))
        .filter(BehaviorLog.merchant_id == merchant_id)
        .group_by(func.coalesce(BehaviorLog.category, "未知品类"))
        .order_by(func.count(BehaviorLog.id).desc())
        .all()
    )
    top = category_rows[:top_n]
    rest = sum(count for _, count in category_rows[top_n:])
    category_share = [{"name": name, "value": int(count)} for name, count in top]
    if rest:
        category_share.append({"name": "其它", "value": int(rest)})

    brand_rows = (
        db.session.query(func.coalesce(BehaviorLog.brand, "未知品牌"), func.count(BehaviorLog.id))
        .filter(BehaviorLog.merchant_id == merchant_id, BehaviorLog.action_type == "purchase")
        .group_by(func.coalesce(BehaviorLog.brand, "未知品牌"))
        .order_by(func.count(BehaviorLog.id).desc())
        .all()
    )
    brand_top = brand_rows[:top_n]
    brand_rest = sum(count for _, count in brand_rows[top_n:])
    brand_share = [
        {"name": AnalyticsService._brand_display(name), "value": int(count)}
        for name, count in brand_top
    ]
    if brand_rest:
        brand_share.append({"name": "其它", "value": int(brand_rest)})

    return jsonify({"category_share": category_share, "brand_share": brand_share})


@bp.get("/trend")
@jwt_required()
def trend():
    unauthorized = _ensure_merchant()
    if unauthorized is not None:
        return unauthorized

    merchant_id = int(get_jwt_identity())
    days = int(request.args.get("days", 7))
    end = datetime.utcnow().date()
    start = end - timedelta(days=days - 1)

    date_expr = func.date(BehaviorLog.created_at)
    rows = (
        db.session.query(date_expr, BehaviorLog.action_type, func.count(BehaviorLog.id))
        .filter(
            BehaviorLog.merchant_id == merchant_id,
            BehaviorLog.created_at
            >= datetime.combine(start, datetime.min.time()),
        )
        .group_by(date_expr, BehaviorLog.action_type)
        .all()
    )

    view_map = {}
    purchase_map = {}
    for day_str, action_type, count in rows:
        key = str(day_str)
        if action_type == "view":
            view_map[key] = int(count)
        if action_type == "purchase":
            purchase_map[key] = int(count)

    day_list = [(start + timedelta(days=i)).isoformat() for i in range(days)]
    return jsonify(
        {
            "days": day_list,
            "series": [
                {"name": "浏览", "data": [view_map.get(day, 0) for day in day_list]},
                {"name": "购买", "data": [purchase_map.get(day, 0) for day in day_list]},
            ],
        }
    )

