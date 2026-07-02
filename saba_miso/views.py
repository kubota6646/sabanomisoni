from flask import Blueprint, flash, redirect, render_template, request, url_for

from .extensions import db
from .models import Response, Thread
from .utils import block_banned_ip, get_client_ip, validate_post_fields

bp = Blueprint("board", __name__)


@bp.before_app_request
def before_request():
    block_banned_ip()


@bp.get("/")
def index():
    threads = Thread.query.order_by(Thread.created_at.desc()).all()
    return render_template("index.html", threads=threads)


@bp.post("/threads")
def create_thread():
    error = validate_post_fields(
        title=request.form.get("title", ""),
        body=request.form.get("body", ""),
        edit_key=request.form.get("edit_key", ""),
    )
    if error:
        flash(error, "error")
        return redirect(url_for("board.index"))

    thread = Thread.create(
        title=request.form["title"].strip(),
        body=request.form["body"].strip(),
        author_name=request.form.get("author_name", "").strip(),
        edit_key=request.form["edit_key"],
        ip_address=get_client_ip(),
    )
    db.session.add(thread)
    db.session.commit()
    flash("スレッドを作成しました。", "success")
    return redirect(url_for("board.thread_detail", thread_id=thread.id))


@bp.get("/threads/<int:thread_id>")
def thread_detail(thread_id):
    thread = db.get_or_404(Thread, thread_id)
    return render_template("thread_detail.html", thread=thread)


@bp.post("/threads/<int:thread_id>/responses")
def create_response(thread_id):
    thread = db.get_or_404(Thread, thread_id)
    error = validate_post_fields(
        body=request.form.get("body", ""),
        edit_key=request.form.get("edit_key", ""),
    )
    if error:
        flash(error, "error")
        return redirect(url_for("board.thread_detail", thread_id=thread.id))

    response = Response.create(
        thread=thread,
        body=request.form["body"].strip(),
        author_name=request.form.get("author_name", "").strip(),
        edit_key=request.form["edit_key"],
        ip_address=get_client_ip(),
    )
    db.session.add(response)
    db.session.commit()
    flash("レスを投稿しました。", "success")
    return redirect(url_for("board.thread_detail", thread_id=thread.id))


@bp.get("/threads/<int:thread_id>/edit")
def edit_thread_form(thread_id):
    thread = db.get_or_404(Thread, thread_id)
    return render_template("edit_thread.html", thread=thread)


@bp.post("/threads/<int:thread_id>/edit")
def edit_thread(thread_id):
    thread = db.get_or_404(Thread, thread_id)
    error = validate_post_fields(
        title=request.form.get("title", ""),
        body=request.form.get("body", ""),
        edit_key=request.form.get("edit_key", ""),
    )
    if error:
        flash(error, "error")
        return redirect(url_for("board.edit_thread_form", thread_id=thread.id))
    if not thread.matches_edit_key(request.form["edit_key"]):
        flash("編集キーが正しくありません。", "error")
        return redirect(url_for("board.edit_thread_form", thread_id=thread.id))

    thread.title = request.form["title"].strip()
    thread.body = request.form["body"].strip()
    thread.author_name = request.form.get("author_name", "").strip() or "名無しさん"
    db.session.commit()
    flash("スレッドを更新しました。", "success")
    return redirect(url_for("board.thread_detail", thread_id=thread.id))


@bp.post("/threads/<int:thread_id>/delete")
def delete_thread(thread_id):
    thread = db.get_or_404(Thread, thread_id)
    if not thread.matches_edit_key(request.form.get("edit_key", "")):
        flash("編集キーが正しくありません。", "error")
        return redirect(url_for("board.thread_detail", thread_id=thread.id))

    db.session.delete(thread)
    db.session.commit()
    flash("スレッドを削除しました。", "success")
    return redirect(url_for("board.index"))


@bp.get("/responses/<int:response_id>/edit")
def edit_response_form(response_id):
    response = db.get_or_404(Response, response_id)
    return render_template("edit_response.html", response=response)


@bp.post("/responses/<int:response_id>/edit")
def edit_response(response_id):
    response = db.get_or_404(Response, response_id)
    error = validate_post_fields(
        body=request.form.get("body", ""),
        edit_key=request.form.get("edit_key", ""),
    )
    if error:
        flash(error, "error")
        return redirect(url_for("board.edit_response_form", response_id=response.id))
    if not response.matches_edit_key(request.form["edit_key"]):
        flash("編集キーが正しくありません。", "error")
        return redirect(url_for("board.edit_response_form", response_id=response.id))

    response.body = request.form["body"].strip()
    response.author_name = request.form.get("author_name", "").strip() or "名無しさん"
    db.session.commit()
    flash("レスを更新しました。", "success")
    return redirect(url_for("board.thread_detail", thread_id=response.thread_id))


@bp.post("/responses/<int:response_id>/delete")
def delete_response(response_id):
    response = db.get_or_404(Response, response_id)
    if not response.matches_edit_key(request.form.get("edit_key", "")):
        flash("編集キーが正しくありません。", "error")
        return redirect(url_for("board.thread_detail", thread_id=response.thread_id))

    thread_id = response.thread_id
    db.session.delete(response)
    db.session.commit()
    flash("レスを削除しました。", "success")
    return redirect(url_for("board.thread_detail", thread_id=thread_id))
