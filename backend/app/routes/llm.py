from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..services.llm_service import LLMService

bp = Blueprint("llm", __name__, url_prefix="/api/llm")
llm_service = LLMService()


@bp.post("/report")
@jwt_required()
def report():
    payload = request.get_json() or {}
    return jsonify(llm_service.build_report(payload))
