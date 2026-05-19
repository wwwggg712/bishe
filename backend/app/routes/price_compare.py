from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required

from ..services.price_compare_service import PriceCompareService


bp = Blueprint("price_compare", __name__, url_prefix="/api")
service = PriceCompareService()


@bp.get("/price-compare")
@jwt_required()
def price_compare():
    if get_jwt().get("role") != "customer":
        return jsonify({"message": "仅普通用户可使用比价功能"}), 403

    product_id = request.args.get("product_id")
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return jsonify({"message": "product_id 非法"}), 400

    payload = service.build(product_id)
    if payload is None:
        return jsonify({"message": "商品不存在或已下架"}), 404
    return jsonify(payload)

