from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from ..extensions import db
from ..models.behavior_log import BehaviorLog
from ..models.product import Product
from ..models.user import User
from ..services.recommendation_service import RecommendationService
from ..services.simulation_service import SimulationService

bp = Blueprint("recommendation", __name__, url_prefix="/api/recommendations")
recommendation_service = RecommendationService()
simulation_service = SimulationService()


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
    logs = [item.to_dict() for item in BehaviorLog.query.order_by(BehaviorLog.timestamp.asc()).all()]
    payload = recommendation_service.recommend_for_customer(
        user_id=user_id,
        logs=logs,
        products=products,
    )
    return jsonify(payload)


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
