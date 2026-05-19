from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from ..extensions import db
from ..models.product import Product
from ..services.merchant_ops_service import MerchantOpsService


bp = Blueprint("merchant_ops", __name__, url_prefix="/api/merchant")
merchant_ops_service = MerchantOpsService()


def _ensure_merchant():
    if get_jwt().get("role") != "merchant":
        return jsonify({"message": "仅商家可查看经营总览"}), 403
    return None


@bp.get("/ops/overview")
@jwt_required()
def ops_overview():
    unauthorized = _ensure_merchant()
    if unauthorized is not None:
        return unauthorized

    merchant_id = int(get_jwt_identity())
    days = request.args.get("days", 30)
    low_sales_threshold = request.args.get("low_sales_threshold", 3)
    brand_top_n = request.args.get("brand_top_n", 5)
    return jsonify(
        merchant_ops_service.build_overview(
            merchant_id=merchant_id,
            days=days,
            low_sales_threshold=low_sales_threshold,
            brand_top_n=brand_top_n,
        )
    )


@bp.post("/products/<int:product_id>/deactivate")
@jwt_required()
def deactivate_product(product_id):
    unauthorized = _ensure_merchant()
    if unauthorized is not None:
        return unauthorized

    merchant_id = int(get_jwt_identity())
    product = Product.query.filter_by(id=product_id, merchant_id=merchant_id).first()
    if product is None:
        return jsonify({"message": "商品不存在或无权限操作"}), 404
    if not product.is_active:
        return jsonify({"message": "商品已下架", "product": {"id": product.id, "is_active": False}})

    product.is_active = False
    db.session.commit()
    return jsonify({"message": "下架成功", "product": {"id": product.id, "is_active": False}})

