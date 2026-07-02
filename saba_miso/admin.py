from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from .extensions import db
from .models import AdminUser, BannedIp, NgWord, Response, Thread
from .utils import admin_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = AdminUser.query.filter_by(username=request.form.get("username", "")).first()
        if user and user.matches_password(request.form.get("password", "")):
            session["admin_user_id"] = user.id
            flash("管理者としてログインしました。", "success")
            return redirect(url_for("admin.dashboard"))
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
    return render_template(
        "admin_dashboard.html",
        threads=Thread.query.order_by(Thread.created_at.desc()).all(),
        responses=Response.query.order_by(Response.created_at.desc()).all(),
        ng_words=NgWord.query.order_by(NgWord.word.asc()).all(),
        banned_ips=BannedIp.query.order_by(BannedIp.created_at.desc()).all(),
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
