from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from .extensions import db, limiter
from .models import AdminLoginLog, AdminUser, BannedIp, NgWord, Response, Thread
from .utils import admin_required, get_client_ip

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", exempt_when=lambda: request.method != "POST")
@limiter.limit("20 per hour", exempt_when=lambda: request.method != "POST")
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        user = AdminUser.query.filter_by(username=username).first()
        if user and user.matches_password(request.form.get("password", "")):
            # ログイン成功を記録する
            db.session.add(AdminLoginLog(
                username=username,
                ip_address=get_client_ip(),
                success=True,
            ))
            db.session.commit()
            session["admin_user_id"] = user.id
            # セッションに有効期限を設定する（PERMANENT_SESSION_LIFETIMEで制御）
            session.permanent = True
            flash("管理者としてログインしました。", "success")
            return redirect(url_for("admin.dashboard"))
        # ログイン失敗を記録する（ブルートフォース攻撃の検知に使用）
        db.session.add(AdminLoginLog(
            username=username,
            ip_address=get_client_ip(),
            success=False,
        ))
        db.session.commit()
        flash("ユーザー名またはパスワードが正しくありません。", "error")
    return render_template("admin_login.html")


@bp.post("/logout")
def logout():
    session.pop("admin_user_id", None)
    flash("ログアウトしました。", "success")
    return redirect(url_for("board.index"))


@bp.get("")
@admin_required
def dashboard():
    login_logs = AdminLoginLog.query.order_by(AdminLoginLog.created_at.desc()).limit(20).all()
    return render_template(
        "admin_dashboard.html",
        threads=Thread.query.order_by(Thread.created_at.desc()).all(),
        responses=Response.query.order_by(Response.created_at.desc()).all(),
        ng_words=NgWord.query.order_by(NgWord.word.asc()).all(),
        banned_ips=BannedIp.query.order_by(BannedIp.created_at.desc()).all(),
        login_logs=login_logs,
    )


@bp.post("/threads/delete-all")
@admin_required
def delete_all_threads():
    Thread.query.delete()
    db.session.commit()
    flash("全スレッドを削除しました。", "success")
    return redirect(url_for("admin.dashboard"))


@bp.post("/threads/<int:thread_id>/delete")
@admin_required
def delete_thread(thread_id):
    thread = db.get_or_404(Thread, thread_id)
    db.session.delete(thread)
    db.session.commit()
    flash("スレッドを削除しました。", "success")
    return redirect(url_for("admin.dashboard"))


@bp.post("/responses/delete-all")
@admin_required
def delete_all_responses():
    Response.query.delete()
    db.session.commit()
    flash("全レスを削除しました。", "success")
    return redirect(url_for("admin.dashboard"))


@bp.post("/responses/<int:response_id>/delete")
@admin_required
def delete_response(response_id):
    response = db.get_or_404(Response, response_id)
    db.session.delete(response)
    db.session.commit()
    flash("レスを削除しました。", "success")
    return redirect(url_for("admin.dashboard"))


@bp.post("/ng-words")
@admin_required
def add_ng_word():
    word = request.form.get("word", "").strip()
    if not word:
        flash("NGワードを入力してください。", "error")
    elif NgWord.query.filter_by(word=word).first():
        flash("そのNGワードはすでに登録されています。", "error")
    else:
        db.session.add(NgWord(word=word))
        db.session.commit()
        flash("NGワードを登録しました。", "success")
    return redirect(url_for("admin.dashboard"))


@bp.post("/ng-words/<int:ng_word_id>/delete")
@admin_required
def delete_ng_word(ng_word_id):
    ng_word = db.get_or_404(NgWord, ng_word_id)
    db.session.delete(ng_word)
    db.session.commit()
    flash("NGワードを削除しました。", "success")
    return redirect(url_for("admin.dashboard"))


@bp.post("/bans")
@admin_required
def add_ban():
    ip_address = request.form.get("ip_address", "").strip()
    reason = request.form.get("reason", "").strip()
    if not ip_address or not reason:
        flash("IPアドレスと理由を入力してください。", "error")
    elif BannedIp.query.filter_by(ip_address=ip_address).first():
        flash("そのIPアドレスはすでにBANされています。", "error")
    else:
        db.session.add(BannedIp(ip_address=ip_address, reason=reason))
        db.session.commit()
        flash("IPアドレスをBANしました。", "success")
    return redirect(url_for("admin.dashboard"))


@bp.post("/bans/<int:ban_id>/delete")
@admin_required
def delete_ban(ban_id):
    ban = db.get_or_404(BannedIp, ban_id)
    db.session.delete(ban)
    db.session.commit()
    flash("BANを解除しました。", "success")
    return redirect(url_for("admin.dashboard"))
