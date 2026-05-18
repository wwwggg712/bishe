from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from ..models.behavior_log import BehaviorLog
from ..services.merchant_action_service import MerchantActionService
from ..services.strategy_service import StrategyService

bp = Blueprint("strategy", __name__, url_prefix="/api/strategy")
strategy_service = StrategyService()
merchant_action_service = MerchantActionService()


def _ensure_merchant():
    if get_jwt().get("role") != "merchant":
        return jsonify({"message": "仅商家可执行运营动作"}), 403
    return None


@bp.get("/merchant")
@jwt_required()
def merchant_strategy():
    unauthorized = _ensure_merchant()
    if unauthorized is not None:
        return unauthorized

    merchant_id = int(get_jwt_identity())
    logs = [item.to_dict() for item in BehaviorLog.query.order_by(BehaviorLog.timestamp.asc()).all()]
    payload = strategy_service.build_for_merchant(
        merchant_id=merchant_id,
        logs=logs,
    )
    return jsonify(payload)


@bp.post("/actions")
@jwt_required()
def record_merchant_action():
    unauthorized = _ensure_merchant()
    if unauthorized is not None:
        return unauthorized

    payload = request.get_json(silent=True) or {}
    product_id = payload.get("product_id")
    action_type = (payload.get("action_type") or "").strip()

    if not product_id or not action_type:
        return jsonify({"message": "product_id 和 action_type 不能为空"}), 400

    try:
        result = merchant_action_service.record_action(
            merchant_id=int(get_jwt_identity()),
            product_id=int(product_id),
            action_type=action_type,
        )
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    except LookupError as error:
        return jsonify({"message": str(error)}), 404

    return jsonify(result)


@bp.get("/actions/summary")
@jwt_required()
def merchant_action_summary():
    unauthorized = _ensure_merchant()
    if unauthorized is not None:
        return unauthorized

    return jsonify(merchant_action_service.build_summary(int(get_jwt_identity())))
