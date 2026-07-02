import os

from dotenv import load_dotenv
from flask import Flask

from .extensions import db


def create_app(test_config=None):
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", "sqlite:///saba_miso.db"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from . import admin, views

    app.register_blueprint(views.bp)
    app.register_blueprint(admin.bp)

    @app.cli.command("init-db")
    def init_db_command():
        """Create database tables and seed the initial admin user if configured."""

        from .models import AdminUser

        with app.app_context():
            db.create_all()

            username = os.environ.get("ADMIN_USERNAME")
            admin_secret = os.environ.get("ADMIN_PASSWORD")
            admin_exists = AdminUser.query.filter_by(username=username).first() if username else None
            if username and admin_secret and not admin_exists:
                db.session.add(
                    AdminUser.create(username=username, raw_secret=admin_secret)
                )
                db.session.commit()
                print(f"Created admin user: {username}")
            else:
                print("Database initialized.")

    return app
