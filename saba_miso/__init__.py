import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

from .extensions import db, limiter


# CSRF保護インスタンス（application factoryパターンのため、init_app()で初期化する）
csrf = CSRFProtect()

_SQLITE_FALLBACK_URI = "sqlite:///saba_miso.db"


def _resolve_database_uri():
    """DATABASE_URL 環境変数からデータベース URI を決定する。

    MySQL URL が設定されていても接続できない場合は SQLite にフォールバックする。
    DATABASE_URL が未設定の場合も SQLite を使用する。
    """
    database_url = os.environ.get("DATABASE_URL", "").strip()

    if not database_url:
        return _SQLITE_FALLBACK_URI

    if database_url.startswith("mysql"):
        try:
            import pymysql
            from urllib.parse import urlparse

            # mysql+pymysql:// スキームを urllib で解析できる形式に変換する
            parsed = urlparse(database_url.split("+", 1)[-1])  # pymysql://... 部分
            connect_kwargs = {
                "host": parsed.hostname or "localhost",
                "port": parsed.port or 3306,
                "user": parsed.username or "",
                "passwd": parsed.password or "",
                "database": (parsed.path or "").lstrip("/"),
                "connect_timeout": 3,
            }
            pymysql.connect(**connect_kwargs).close()
        except Exception:
            print(
                "警告: MySQL に接続できません。SQLite にフォールバックします。"
                f" (DATABASE_URL={database_url!r})"
            )
            return _SQLITE_FALLBACK_URI

    return database_url


def create_app(test_config=None):
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)

    # 環境変数でプロキシ信頼・HTTPS有効化・セッション時間を制御する
    trust_proxy = os.environ.get("TRUST_PROXY_HEADERS", "false").lower() == "true"
    https_enabled = os.environ.get("HTTPS_ENABLED", "false").lower() == "true"
    admin_session_hours = int(os.environ.get("ADMIN_SESSION_HOURS", "2"))

    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key"),
        SQLALCHEMY_DATABASE_URI=_resolve_database_uri(),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        # HTTPS環境ではCookieをSecureフラグ付きで送信する（HTTPS_ENABLED=trueで有効）
        SESSION_COOKIE_SECURE=https_enabled,
        # CSRFトークン保護を有効化する
        WTF_CSRF_ENABLED=True,
        WTF_CSRF_SECRET_KEY=os.environ.get(
            "WTF_CSRF_SECRET_KEY", os.environ.get("SECRET_KEY", "dev-secret-key")
        ),
        # 管理者セッションタイムアウト（デフォルト2時間）
        PERMANENT_SESSION_LIFETIME=timedelta(hours=admin_session_hours),
        # リクエストボディの最大サイズを1MBに制限する（大量データ送信攻撃対策）
        MAX_CONTENT_LENGTH=1 * 1024 * 1024,
    )

    if test_config:
        app.config.update(test_config)

    # テスト時はCSRFトークン検証とレート制限を無効化する
    if app.config.get("TESTING"):
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["RATELIMIT_ENABLED"] = False

    # X-Forwarded-Forを信頼できる場合のみProxyFixを適用する（TRUST_PROXY_HEADERS=trueで有効）
    # Nginx等のリバースプロキシ経由の場合に使用する
    if trust_proxy:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # セキュリティヘッダーを設定する（クリックジャッキング・MIMEスニッフィング等の対策）
    csp = {
        "default-src": "'self'",
        "style-src": ["'self'", "'unsafe-inline'"],  # 既存インラインCSSを許可
        "script-src": "'self'",
        "img-src": "'self' data:",
    }
    Talisman(
        app,
        force_https=False,           # HTTPS強制はNginx側で行う
        strict_transport_security=False,
        content_security_policy=csp,
        x_content_type_options=True,
        frame_options="DENY",
        referrer_policy="strict-origin-when-cross-origin",
        # Flask側でセッションCookieのセキュリティ設定を管理する
        session_cookie_secure=False,
    )

    from . import admin, views

    app.register_blueprint(views.bp)
    app.register_blueprint(admin.bp)

    # リクエストボディが1MBを超えた場合のエラーハンドラ
    @app.errorhandler(413)
    def request_too_large(e):
        return "送信データが大きすぎます（上限1MB）。", 413

    # レート制限超過時のエラーハンドラ
    @app.errorhandler(429)
    def ratelimit_exceeded(e):
        return "投稿が多すぎます。しばらくしてからお試しください。", 429

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
