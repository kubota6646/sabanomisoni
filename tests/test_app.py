import unittest

from saba_miso import create_app
from saba_miso.extensions import db
from saba_miso.models import AdminUser, BannedIp, NgWord, Response, Thread


class BulletinBoardTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
                "SECRET_KEY": "test-secret",
            }
        )
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            db.session.add(AdminUser.create(username="admin", raw_secret="password"))
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_thread_response_edit_and_delete_flow(self):
        response = self.client.post(
            "/threads",
            data={
                "title": "最初のスレッド",
                "author_name": "テスター",
                "body": "こんにちは",
                "edit_key": "thread-key",
            },
            environ_base={"REMOTE_ADDR": "203.0.113.1"},
            follow_redirects=True,
        )
        self.assertIn("スレッドを作成しました。", response.get_data(as_text=True))

        with self.app.app_context():
            thread = Thread.query.one()

        response = self.client.post(
            f"/threads/{thread.id}/responses",
            data={
                "author_name": "",
                "body": "レス本文",
                "edit_key": "response-key",
            },
            environ_base={"REMOTE_ADDR": "203.0.113.2"},
            follow_redirects=True,
        )
        self.assertIn("レスを投稿しました。", response.get_data(as_text=True))

        with self.app.app_context():
            saved_response = Response.query.one()

        response = self.client.post(
            f"/responses/{saved_response.id}/edit",
            data={
                "author_name": "更新者",
                "body": "更新したレス",
                "edit_key": "response-key",
            },
            follow_redirects=True,
        )
        self.assertIn("レスを更新しました。", response.get_data(as_text=True))

        response = self.client.post(
            f"/threads/{thread.id}/delete",
            data={"edit_key": "thread-key"},
            follow_redirects=True,
        )
        self.assertIn("スレッドを削除しました。", response.get_data(as_text=True))

        with self.app.app_context():
            self.assertEqual(Thread.query.count(), 0)
            self.assertEqual(Response.query.count(), 0)

    def test_admin_ng_word_and_ban_controls(self):
        login_response = self.client.post(
            "/admin/login",
            data={"username": "admin", "password": "password"},
            follow_redirects=True,
        )
        self.assertIn("管理者としてログインしました。", login_response.get_data(as_text=True))

        response = self.client.post(
            "/admin/ng-words",
            data={"word": "禁止語"},
            follow_redirects=True,
        )
        self.assertIn("NGワードを登録しました。", response.get_data(as_text=True))

        blocked = self.client.post(
            "/threads",
            data={
                "title": "投稿",
                "author_name": "匿名",
                "body": "これは禁止語を含みます",
                "edit_key": "ng-key",
            },
            follow_redirects=True,
        )
        self.assertIn("NGワードを含む投稿はできません。", blocked.get_data(as_text=True))

        response = self.client.post(
            "/admin/bans",
            data={"ip_address": "198.51.100.4", "reason": "spam"},
            follow_redirects=True,
        )
        self.assertIn("IPアドレスをBANしました。", response.get_data(as_text=True))

        self.client.post("/admin/logout", follow_redirects=True)
        banned = self.client.get("/", environ_base={"REMOTE_ADDR": "198.51.100.4"})
        self.assertEqual(banned.status_code, 403)

        with self.app.app_context():
            self.assertEqual(NgWord.query.count(), 1)
            self.assertEqual(BannedIp.query.count(), 1)


if __name__ == "__main__":
    unittest.main()
