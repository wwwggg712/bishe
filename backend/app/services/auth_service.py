from flask_jwt_extended import create_access_token

from ..extensions import db
from ..models.user import User


class AuthService:
    def authenticate(self, username, password):
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            return None
        return user

    def build_login_payload(self, user):
        token = create_access_token(
            identity=str(user.id),
            additional_claims={"role": user.role},
        )
        return {"token": token, "user": user.to_dict()}

    def get_user(self, user_id):
        return db.session.get(User, int(user_id))
