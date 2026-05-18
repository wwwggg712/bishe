from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from ..models.behavior_log import BehaviorLog
from ..services.auth_service import AuthService
from ..services.prediction_service import PredictionService

bp = Blueprint("users", __name__, url_prefix="/api/users")
prediction_service = PredictionService()
auth_service = AuthService()


@bp.get("/portrait")
@jwt_required()
def portrait():
    if get_jwt().get("role") != "customer":
        return jsonify({"message": "仅普通用户可查看个人画像"}), 403

    user = auth_service.get_user(get_jwt_identity())
    if user is None:
        return jsonify({"message": "用户不存在"}), 404

    logs = [item.to_dict() for item in BehaviorLog.query.order_by(BehaviorLog.timestamp.asc()).all()]
    portrait_payload = prediction_service.build_user_portrait(int(user.id), logs)
    return jsonify(
        {
            "user": user.to_dict(),
            **portrait_payload,
        }
    )
