from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.errors.handlers import register_error_handlers


def _init_cors(app):
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        allow_headers=["Authorization", "Content-Type"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        supports_credentials=False,
        max_age=600,
    )


def _register_blueprints(app):
    from app.routes.auth import auth_bp
    from app.routes.books import books_bp
    from app.routes.docs import docs_bp
    from app.routes.health import health_bp
    from app.routes.reviews import reviews_bp
    from app.routes.roulette import roulette_bp
    from app.routes.storage import storage_bp

    app.register_blueprint(docs_bp)
    app.register_blueprint(health_bp)

    api_routes = [
        (auth_bp, "/api/auth"),
        (books_bp, "/api/books"),
        (reviews_bp, "/api/reviews"),
        (roulette_bp, "/api/roulette"),
        (storage_bp, "/api/storage"),
    ]
    for bp, prefix in api_routes:
        app.register_blueprint(bp, url_prefix=prefix)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    _init_cors(app)
    register_error_handlers(app)
    _register_blueprints(app)
    return app
