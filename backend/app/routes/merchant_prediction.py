from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from ..services.merchant_prediction_service import MerchantPredictionService


bp = Blueprint("merchant_prediction", __name__, url_prefix="/api/merchant/prediction")
merchant_prediction_service = MerchantPredictionService()


def _ensure_merchant():
    if get_jwt().get("role") != "merchant":
        return jsonify({"message": "仅商家可查看销量预测"}), 403
    return None


@bp.get("/sales-forecast")
@jwt_required()
def sales_forecast():
    unauthorized = _ensure_merchant()
    if unauthorized is not None:
        return unauthorized

    merchant_id = int(get_jwt_identity())
    days = request.args.get("days", 30)
    payload = merchant_prediction_service.build_sales_forecast(merchant_id=merchant_id, days=days)
    return jsonify(payload)
