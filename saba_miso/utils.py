import os
from datetime import UTC, datetime
from functools import wraps

from flask import abort, flash, g, redirect, request, session, url_for

from .extensions import db
from .models import BannedIp, NgWord


def get_client_ip():
    """クライアントIPアドレスを返す。

    TRUST_PROXY_HEADERS=true の場合のみ X-Forwarded-For ヘッダーを信頼する。
    false（デフォルト）の場合は request.remote_addr を直接使用し、
    ヘッダー偽造によるBAN回避・レート制限回避を防ぐ。
    """
    trust_proxy = os.environ.get("TRUST_PROXY_HEADERS", "false").lower() == "true"
    if trust_proxy:
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "0.0.0.0"


def validate_post_fields(title=None, body="", edit_key=""):
    if title is not None and not title.strip():
        return "タイトルを入力してください。"
    if not body.strip():
        return "本文を入力してください。"
    if not edit_key.strip():
        return "編集キーを入力してください。"
    if contains_ng_word((title or "") + "\n" + body):
        return "NGワードを含む投稿はできません。"
    return None


def contains_ng_word(text):
    normalized = text.lower()
    if "ng_words" not in g:
        g.ng_words = db.session.execute(
            db.select(NgWord.word).order_by(NgWord.word.asc())
        ).scalars().all()

    for ng_word in g.ng_words:
        if ng_word.lower() in normalized:
            return True
    return False


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_user_id"):
            flash("管理者ログインが必要です。", "error")
            return redirect(url_for("admin.login"))
        # 最終アクセス時刻を更新する（セッション監査用）
        session["last_active"] = datetime.now(UTC).replace(tzinfo=None).isoformat()
        return view(*args, **kwargs)

    return wrapped_view


def block_banned_ip():
    if session.get("admin_user_id"):
        return

    if request.endpoint in {"admin.login", "admin.logout", "static"}:
        return

    client_ip = get_client_ip()
    if BannedIp.query.filter_by(ip_address=client_ip).first():
        abort(403)
