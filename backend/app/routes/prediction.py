from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from ..models.behavior_log import BehaviorLog
from ..services.prediction_service import PredictionService

bp = Blueprint("prediction", __name__, url_prefix="/api/prediction")
prediction_service = PredictionService()


def _ensure_merchant_anomalies():
    if get_jwt().get("role") != "merchant":
        return jsonify({"message": "仅商家可查看异常预警"}), 403
    return None


@bp.get("/trends")
@jwt_required()
def trends():
    logs = [item.to_dict() for item in BehaviorLog.query.order_by(BehaviorLog.timestamp.asc()).all()]
    return jsonify(prediction_service.build_trends(logs))


@bp.get("/profile")
@jwt_required()
def profile():
    if get_jwt().get("role") != "customer":
        return jsonify({"message": "仅普通用户可查看个人画像"}), 403

    user_id = int(get_jwt_identity())
    logs = [item.to_dict() for item in BehaviorLog.query.order_by(BehaviorLog.timestamp.asc()).all()]
    return jsonify(prediction_service.build_profile(user_id, logs))


@bp.get("/anomalies")
@jwt_required()
def anomalies():
    unauthorized = _ensure_merchant_anomalies()
    if unauthorized is not None:
        return unauthorized

    logs = [item.to_dict() for item in BehaviorLog.query.order_by(BehaviorLog.timestamp.asc()).all()]
    payload = prediction_service.build_anomalies(
        logs,
        merchant_id=int(get_jwt_identity()),
    )
    severity = (request.args.get("severity") or "").strip().lower()
    if severity:
        payload["items"] = [item for item in payload["items"] if item["severity"] == severity]
    return jsonify(payload)
