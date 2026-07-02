from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter


db = SQLAlchemy()


def _get_client_ip():
    """レート制限のキー関数。utils.pyのget_client_ip()を遅延インポートして循環参照を回避する。"""
    from .utils import get_client_ip
    return get_client_ip()


# レート制限インスタンス（application factoryパターンのため、init_app()で初期化する）
limiter = Limiter(
    key_func=_get_client_ip,
    storage_uri="memory://",
)
