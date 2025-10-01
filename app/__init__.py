import os
from flask import Flask
from dotenv import load_dotenv

from .config import Config
from .extensions import db, migrate, jwt, mail, cors
from .cli import seed_admin


def create_app() -> Flask:
    load_dotenv()

    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config())

    cors.init_app(app, supports_credentials=True)
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    jwt.init_app(app)

    # Register blueprints (added incrementally)
    from .routes.auth import bp as auth_bp
    from .routes.health import bp as health_bp
    from .routes.students import bp as students_bp
    from .routes.dashboard import bp as dashboard_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(students_bp, url_prefix="/api/students")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")

    # CLI commands
    app.cli.add_command(seed_admin)

    return app
