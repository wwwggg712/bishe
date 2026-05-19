from flask import Flask
import os

from . import models  # noqa: F401
from .config import Config
from .extensions import cors, db, jwt, scheduler
from .routes.admin import bp as admin_bp
from .routes.analytics import bp as analytics_bp
from .routes.auth import bp as auth_bp
from .routes.llm import bp as llm_bp
from .routes.merchant_charts import bp as merchant_charts_bp
from .routes.merchant_ops import bp as merchant_ops_bp
from .routes.merchant_prediction import bp as merchant_prediction_bp
from .routes.price_compare import bp as price_compare_bp
from .routes.prediction import bp as prediction_bp
from .routes.recommendation import bp as recommendation_bp
from .routes.simulation import bp as simulation_bp
from .routes.strategy import bp as strategy_bp
from .routes.users import bp as users_bp
from .tasks.jobs import ensure_job_tasks, register_jobs
from .utils.seed_data import seed_demo_data


def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=False,
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(llm_bp)
    app.register_blueprint(merchant_charts_bp)
    app.register_blueprint(merchant_ops_bp)
    app.register_blueprint(merchant_prediction_bp)
    app.register_blueprint(price_compare_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(simulation_bp)
    app.register_blueprint(strategy_bp)
    app.register_blueprint(users_bp)

    with app.app_context():
        db.create_all()
        if app.config.get("AUTO_SEED_DEMO_DATA", True):
            seed_demo_data()
        ensure_job_tasks()
        register_jobs()

    if not app.config.get("TESTING"):
        try:
            if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
                return app
            if not getattr(scheduler, "running", False):
                scheduler.start()
        except Exception:
            pass

    return app
