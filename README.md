# サバの味噌煮

匿名で利用できるシンプルな総合掲示板 Web アプリケーションです。  
Flask + SQLAlchemy を使ったサーバーサイドレンダリング構成で、MySQL での運用を前提にしています。

## 主な機能

- スレッド一覧 / スレッド作成
- スレッド詳細 / レス投稿
- 編集キーによる本人のみの編集・削除
- 管理者ログイン
- 全スレッド / 全レスの管理者削除
- NG ワード管理
- IP アドレス記録と BAN
- PC / スマートフォン向けのシンプルなレスポンシブ UI

## 技術スタック

- Python 3.12
- Flask
- Flask-SQLAlchemy
- MySQL（本番想定）

## セットアップ

1. Python 3.12 と MySQL を用意します。
2. 依存関係をインストールします。

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. 環境変数を設定します。

   ```bash
   cp .env.example .env
   ```

4. MySQL にデータベースを作成し、`.env` の `DATABASE_URL` を更新します。
5. テーブルを作成します。

   ```bash
   flask --app app.py init-db
   ```

   `ADMIN_USERNAME` と `ADMIN_PASSWORD` を設定しておくと、初回実行時に管理者ユーザーも作成されます。

6. 開発サーバーを起動します。

   ```bash
   flask --app app.py run --debug
   ```

## テスト

標準ライブラリの `unittest` を使っています。

```bash
python -m unittest discover -s tests
```

## データベーススキーマ

- MySQL 向けスキーマ: `/home/runner/work/sabanomisoni/sabanomisoni/database/schema.sql`
- アプリケーションは `DATABASE_URL` で指定した DB に対して SQLAlchemy を利用します

## 画面 / ルート

- `/` : スレッド一覧 / 新規作成
- `/threads/<id>` : スレッド詳細 / レス一覧 / レス投稿
- `/threads/<id>/edit` : スレッド編集
- `/responses/<id>/edit` : レス編集
- `/admin/login` : 管理者ログイン
- `/admin` : 管理者ダッシュボード

## セキュリティ上の考慮

- 編集キーはハッシュ化して保存
- 管理者パスワードはハッシュ化して保存
- ORM により SQL インジェクションを回避
- Jinja2 自動エスケープと `white-space: pre-wrap` で XSS を抑制
- NG ワード投稿を拒否
- 投稿 IP を保存し、管理者が BAN 可能

## AWS EC2 デプロイ手順

1. EC2 に Python 3.12、MySQL クライアントライブラリ、Nginx をインストールします。
2. アプリケーションコードを配置し、仮想環境を作成して `pip install -r requirements.txt` を実行します。
3. `.env` を配置し、`DATABASE_URL` を EC2 から接続できる MySQL に設定します。
4. `flask --app app.py init-db` を実行してテーブルと管理者を初期化します。
5. `gunicorn app:app` で起動し、Nginx からリバースプロキシします。
6. ALB や Nginx を使う場合でも、`X-Forwarded-For` をそのまま渡す設定にして IP 記録と BAN 判定を正しく動作させてください。
