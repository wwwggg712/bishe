from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from ..models.behavior_log import BehaviorLog
from ..services.analytics_service import AnalyticsService

bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")
analytics_service = AnalyticsService()


def _ensure_merchant():
    if get_jwt().get("role") != "merchant":
        return jsonify({"message": "仅商家可查看用户行为变化"}), 403
    return None


def _ensure_merchant_analytics():
    if get_jwt().get("role") != "merchant":
        return jsonify({"message": "仅商家可查看经营分析"}), 403
    return None


def _current_merchant_scope():
    return int(get_jwt_identity())


@bp.get("/overview")
@jwt_required()
def overview():
    unauthorized = _ensure_merchant_analytics()
    if unauthorized is not None:
        return unauthorized

    logs = [item.to_dict() for item in BehaviorLog.query.order_by(BehaviorLog.timestamp.asc()).all()]
    payload = analytics_service.build_overview(
        logs,
        merchant_id=_current_merchant_scope(),
    )
    return jsonify(payload)


@bp.get("/funnel")
@jwt_required()
def funnel():
    unauthorized = _ensure_merchant_analytics()
    if unauthorized is not None:
        return unauthorized

    logs = [item.to_dict() for item in BehaviorLog.query.order_by(BehaviorLog.timestamp.asc()).all()]
    return jsonify(
        analytics_service.build_funnel(
            logs,
            merchant_id=_current_merchant_scope(),
        )
    )


@bp.get("/regions")
@jwt_required()
def regions():
    unauthorized = _ensure_merchant_analytics()
    if unauthorized is not None:
        return unauthorized

    logs = [item.to_dict() for item in BehaviorLog.query.order_by(BehaviorLog.timestamp.asc()).all()]
    return jsonify(
        analytics_service.build_regions(
            logs,
            merchant_id=_current_merchant_scope(),
        )
    )


@bp.get("/categories")
@jwt_required()
def categories():
    unauthorized = _ensure_merchant_analytics()
    if unauthorized is not None:
        return unauthorized

    logs = [item.to_dict() for item in BehaviorLog.query.order_by(BehaviorLog.timestamp.asc()).all()]
    return jsonify(
        analytics_service.build_categories(
            logs,
            merchant_id=_current_merchant_scope(),
        )
    )


@bp.get("/brands")
@jwt_required()
def brands():
    unauthorized = _ensure_merchant_analytics()
    if unauthorized is not None:
        return unauthorized

    category = request.args.get("category")
    logs = [item.to_dict() for item in BehaviorLog.query.order_by(BehaviorLog.timestamp.asc()).all()]
    return jsonify(
        analytics_service.build_brands(
            logs,
            merchant_id=_current_merchant_scope(),
            category=category,
        )
    )


@bp.get("/products/hot")
@jwt_required()
def hot_products():
    unauthorized = _ensure_merchant_analytics()
    if unauthorized is not None:
        return unauthorized

    logs = [item.to_dict() for item in BehaviorLog.query.order_by(BehaviorLog.timestamp.asc()).all()]
    return jsonify(
        analytics_service.build_hot_products(
            logs,
            merchant_id=_current_merchant_scope(),
        )
    )


@bp.get("/products/cold")
@jwt_required()
def cold_products():
    unauthorized = _ensure_merchant_analytics()
    if unauthorized is not None:
        return unauthorized

    logs = [item.to_dict() for item in BehaviorLog.query.order_by(BehaviorLog.timestamp.asc()).all()]
    return jsonify(
        analytics_service.build_cold_products(
            logs,
            merchant_id=_current_merchant_scope(),
        )
    )


@bp.get("/users/rfm")
@jwt_required()
def user_rfm():
    unauthorized = _ensure_merchant_analytics()
    if unauthorized is not None:
        return unauthorized

    logs = [item.to_dict() for item in BehaviorLog.query.order_by(BehaviorLog.timestamp.asc()).all()]
    return jsonify(
        analytics_service.build_user_rfm(
            logs,
            merchant_id=_current_merchant_scope(),
        )
    )


@bp.get("/merchant/user-behavior")
@jwt_required()
def merchant_user_behavior():
    unauthorized = _ensure_merchant()
    if unauthorized is not None:
        return unauthorized

    logs = [item.to_dict() for item in BehaviorLog.query.order_by(BehaviorLog.timestamp.asc()).all()]
    payload = analytics_service.build_merchant_user_behavior(
        int(get_jwt_identity()),
        logs,
    )
    return jsonify(payload)
