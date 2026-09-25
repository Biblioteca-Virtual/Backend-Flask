from flask import Flask

from app.config import Config
from app.errors.handlers import register_error_handlers


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    register_error_handlers(app)

    from app.routes.auth import auth_bp
    from app.routes.books import books_bp
    from app.routes.docs import docs_bp
    from app.routes.health import health_bp
    from app.routes.readings import readings_bp
    from app.routes.reviews import reviews_bp
    from app.routes.roulette import roulette_bp

    app.register_blueprint(docs_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(books_bp, url_prefix="/api/books")
    app.register_blueprint(readings_bp, url_prefix="/api/readings")
    app.register_blueprint(reviews_bp, url_prefix="/api/reviews")
    app.register_blueprint(roulette_bp, url_prefix="/api/roulette")

    return app