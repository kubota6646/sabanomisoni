from datetime import UTC, datetime

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def current_utc_time():
    return datetime.now(UTC).replace(tzinfo=None)


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=current_utc_time, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=current_utc_time,
        onupdate=current_utc_time,
        nullable=False,
    )


class Thread(TimestampMixin, db.Model):
    __tablename__ = "threads"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author_name = db.Column(db.String(100), nullable=False, default="名無しさん")
    edit_key = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    responses = db.relationship(
        "Response",
        back_populates="thread",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Response.id",
        lazy="selectin",
    )

    @classmethod
    def create(cls, title, body, author_name, edit_key, ip_address):
        return cls(
            title=title,
            body=body,
            author_name=author_name or "名無しさん",
            edit_key=generate_password_hash(edit_key),
            ip_address=ip_address,
        )

    def matches_edit_key(self, edit_key):
        return check_password_hash(self.edit_key, edit_key)


class Response(TimestampMixin, db.Model):
    __tablename__ = "responses"

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(
        db.Integer, db.ForeignKey("threads.id", ondelete="CASCADE"), nullable=False
    )
    body = db.Column(db.Text, nullable=False)
    author_name = db.Column(db.String(100), nullable=False, default="名無しさん")
    edit_key = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    thread = db.relationship("Thread", back_populates="responses")

    @classmethod
    def create(cls, thread, body, author_name, edit_key, ip_address):
        return cls(
            thread=thread,
            body=body,
            author_name=author_name or "名無しさん",
            edit_key=generate_password_hash(edit_key),
            ip_address=ip_address,
        )

    def matches_edit_key(self, edit_key):
        return check_password_hash(self.edit_key, edit_key)


class AdminUser(TimestampMixin, db.Model):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)

    @classmethod
    def create(cls, username, raw_secret):
        values = {
            "username": username,
            "password": generate_password_hash(raw_secret),
        }
        return cls(**values)

    def matches_password(self, raw_secret):
        return check_password_hash(self.password, raw_secret)


class NgWord(db.Model):
    __tablename__ = "ng_words"

    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(255), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=current_utc_time, nullable=False)


class BannedIp(db.Model):
    __tablename__ = "banned_ips"

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, unique=True)
    reason = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=current_utc_time, nullable=False)
