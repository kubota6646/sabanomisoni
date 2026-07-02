from functools import wraps

from flask import abort, flash, redirect, request, session, url_for

from .models import BannedIp, NgWord


def get_client_ip():
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
    for ng_word in NgWord.query.order_by(NgWord.word.asc()).all():
        if ng_word.word.lower() in normalized:
            return True
    return False


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_user_id"):
            flash("管理者ログインが必要です。", "error")
            return redirect(url_for("admin.login"))
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
