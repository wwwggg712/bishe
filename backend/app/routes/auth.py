from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..services.auth_service import AuthService

bp = Blueprint("auth", __name__, url_prefix="/api/auth")
auth_service = AuthService()


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = auth_service.authenticate(username, password)
    if user is None:
        return jsonify({"message": "用户名或密码错误"}), 401

    return jsonify(auth_service.build_login_payload(user))


@bp.get("/me")
@jwt_required()
def me():
    user = auth_service.get_user(get_jwt_identity())
    if user is None:
        return jsonify({"message": "用户不存在"}), 404

    return jsonify({"user": user.to_dict()})
