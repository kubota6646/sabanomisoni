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

- MySQL 向けスキーマ: `database/schema.sql`
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

## AWS EC2 + RDS デプロイ手順

> PC 初心者の方でも手順通りに進めれば公開できます。各ステップをひとつずつ実行してください。

### 前提

- AWS アカウントをお持ちであること
- ターミナル（Windows なら「コマンドプロンプト」または「PowerShell」、Mac なら「ターミナル」）を使えること

---

### ステップ 1 — RDS (MySQL データベース) の作成

1. [AWS マネジメントコンソール](https://console.aws.amazon.com/) にログインします。
2. 上部の検索バーで **「RDS」** と入力し、RDS ページを開きます。
3. 「**データベースの作成**」ボタンをクリックします。
4. 以下の通り設定します。
   - エンジンのタイプ: **MySQL**
   - テンプレート: **無料利用枠**（12 か月間無料）
   - DB インスタンス識別子: 任意（例: `saba-miso-db`）
   - マスターユーザー名: 任意（例: `dbadmin`）※**必ずメモしてください**（アプリの管理者ユーザーとは別物です）
   - マスターパスワード: 英数字記号を含む強力なパスワード ※**必ずメモしてください**
   - パブリックアクセス: **「なし」**（EC2 経由でのみ接続するため）
   - 最初のデータベース名（追加設定の中）: `saba_miso`
5. 「**データベースの作成**」をクリックし、数分待ちます。
6. 作成後、RDS の詳細ページから **「エンドポイント」**（例: `saba-miso-db.xxxxxx.ap-northeast-1.rds.amazonaws.com`）をメモします。
7. RDS のセキュリティグループの「インバウンドルール」に、後で作成する EC2 からのポート **3306** (MySQL/Aurora) 接続を許可するルールを追加します。

---

### ステップ 2 — EC2 インスタンスの作成

1. AWS コンソールで **「EC2」** を開きます。
2. 「**インスタンスを起動**」をクリックします。
3. 以下の通り設定します。
   - 名前: 任意（例: `sabanomisoni-server`）
   - AMI: **Ubuntu Server 24.04 LTS**（無料利用枠対象）
   - インスタンスタイプ: **t2.micro**（無料利用枠対象、リージョンによっては t3.micro の場合もあります）
   - キーペア: 「**新しいキーペアの作成**」→ 名前を入力 → **「キーペアのダウンロード」** (.pem ファイル) ※**絶対に紛失しないように保管してください**
   - ネットワーク設定: 「**セキュリティグループを作成**」を選び、以下を許可
     - SSH (ポート 22) — 自分の IP からのみ
     - HTTP (ポート 80) — どこからでも
4. 「**インスタンスを起動**」をクリックします。
5. EC2 の詳細ページから **「パブリック IPv4 アドレス」** をメモします。
6. EC2 のセキュリティグループを RDS のインバウンドルールに追加します（ステップ 1 の 7 を実施）。

---

### ステップ 3 — EC2 への SSH 接続

Windows の場合は PowerShell、Mac/Linux の場合はターミナルを開き、以下を実行します。

```bash
# .pem ファイルのあるフォルダに移動してから実行 (Mac/Linux)
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@<EC2のパブリックIPアドレス>
```

Windows (PowerShell) の場合:

```powershell
ssh -i C:\Users\あなたのユーザー名\Downloads\your-key.pem ubuntu@<EC2のパブリックIPアドレス>
```

「Are you sure you want to continue connecting?」と聞かれたら **`yes`** と入力して Enter を押します。

---

### ステップ 4 — サーバーのセットアップ

EC2 に接続したら、以下のコマンドを順番に実行します。

```bash
# システムを最新化
sudo apt update && sudo apt upgrade -y

# Python 3.12、pip、仮想環境、Nginx、Git をインストール
sudo apt install -y python3.12 python3.12-venv python3-pip nginx git
```

---

### ステップ 5 — アプリケーションの配置

```bash
# ホームディレクトリに移動
cd /home/ubuntu

# リポジトリをクローン（またはファイルをアップロード）
git clone https://github.com/<あなたのユーザー名>/sabanomisoni.git
cd sabanomisoni

# Python 仮想環境を作成・有効化
python3.12 -m venv .venv
source .venv/bin/activate

# 依存ライブラリをインストール
pip install -r requirements.txt
```

---

### ステップ 6 — 環境変数の設定

```bash
cp .env.example .env
nano .env   # テキストエディタで開く
```

以下の内容を書き換えます（`nano` では Ctrl+O で保存、Ctrl+X で終了）。

```
SECRET_KEY=（例: a1b2c3d4e5f6... のようなランダムな文字列）
DATABASE_URL=mysql+pymysql://dbadmin:RDSパスワード@RDSエンドポイント/saba_miso
ADMIN_USERNAME=admin（任意のログイン名）
ADMIN_PASSWORD=強力なパスワード
```

> **ヒント**: `SECRET_KEY` にランダムな文字列を生成するには、別のターミナルで `openssl rand -hex 32` を実行し、その出力をそのまま貼り付けてください。

---

### ステップ 7 — データベースの初期化

```bash
flask --app app.py init-db
```

「Created admin user: admin」と表示されれば成功です。

---

### ステップ 8 — Gunicorn を自動起動サービスとして登録

```bash
sudo nano /etc/systemd/system/sabanomisoni.service
```

以下の内容を貼り付けます。

```ini
[Unit]
Description=Sabanomisoni Gunicorn Service
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/sabanomisoni
EnvironmentFile=/home/ubuntu/sabanomisoni/.env
ExecStart=/home/ubuntu/sabanomisoni/.venv/bin/gunicorn \
    --workers 2 \
    --bind unix:/run/sabanomisoni.sock \
    app:app

[Install]
WantedBy=multi-user.target
```

保存（Ctrl+O → Enter → Ctrl+X）したら有効化します。

```bash
sudo systemctl daemon-reload
sudo systemctl enable sabanomisoni
sudo systemctl start sabanomisoni
# 起動状態を確認
sudo systemctl status sabanomisoni
```

---

### ステップ 9 — Nginx のリバースプロキシ設定

```bash
sudo nano /etc/nginx/sites-available/sabanomisoni
```

以下の内容を貼り付けます。

```nginx
server {
    listen 80;
    server_name _;  # _ はすべてのホスト名を受け付けるという意味。独自ドメインがある場合は example.com のように変更

    location / {
        proxy_pass http://unix:/run/sabanomisoni.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

設定を有効化します。

```bash
sudo ln -s /etc/nginx/sites-available/sabanomisoni /etc/nginx/sites-enabled/
sudo nginx -t        # 設定ファイルの文法チェック
sudo systemctl reload nginx
```

ブラウザで `http://<EC2のパブリックIPアドレス>` にアクセスして掲示板が表示されれば完了です。

---

## オンプレミス環境でのデプロイ手順

> 自分のパソコンや自社サーバーに直接インストールして運用する方法です。OS は **Ubuntu 24.04 LTS** を前提にしています。

### ステップ 1 — 必要なソフトウェアのインストール

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.12 python3.12-venv python3-pip nginx git mysql-server
```

---

### ステップ 2 — MySQL のセットアップ

```bash
# MySQL を起動・自動起動を有効化
sudo systemctl enable --now mysql

# MySQL の初期設定（ルートパスワードなどを対話形式で設定）
sudo mysql_secure_installation

# MySQL にログイン
sudo mysql -u root -p
```

MySQL のプロンプト内で以下を実行します。

```sql
CREATE DATABASE saba_miso CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sabauser'@'localhost' IDENTIFIED BY 'あなたのパスワード';
GRANT ALL PRIVILEGES ON saba_miso.* TO 'sabauser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

### ステップ 3 — アプリケーションの配置

```bash
cd /home/あなたのユーザー名
git clone https://github.com/<あなたのユーザー名>/sabanomisoni.git
cd sabanomisoni

python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### ステップ 4 — 環境変数の設定

```bash
cp .env.example .env
nano .env
```

以下の内容を書き換えます。

```
SECRET_KEY=ランダムな長い文字列
DATABASE_URL=mysql+pymysql://sabauser:あなたのパスワード@localhost/saba_miso
ADMIN_USERNAME=admin
ADMIN_PASSWORD=強力なパスワード
```

---

### ステップ 5 — データベースの初期化

```bash
flask --app app.py init-db
```

---

### ステップ 6 — Gunicorn を自動起動サービスとして登録

```bash
sudo nano /etc/systemd/system/sabanomisoni.service
```

```ini
[Unit]
Description=Sabanomisoni Gunicorn Service
After=network.target

[Service]
User=あなたのユーザー名
Group=あなたのユーザー名
WorkingDirectory=/home/あなたのユーザー名/sabanomisoni
EnvironmentFile=/home/あなたのユーザー名/sabanomisoni/.env
ExecStart=/home/あなたのユーザー名/sabanomisoni/.venv/bin/gunicorn \
    --workers 2 \
    --bind unix:/run/sabanomisoni.sock \
    app:app

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable sabanomisoni
sudo systemctl start sabanomisoni
sudo systemctl status sabanomisoni
```

---

### ステップ 7 — Nginx のリバースプロキシ設定

```bash
sudo nano /etc/nginx/sites-available/sabanomisoni
```

```nginx
server {
    listen 80;
    server_name _;  # _ はすべてのホスト名を受け付けるという意味。独自ドメインがある場合は example.com のように変更

    location / {
        proxy_pass http://unix:/run/sabanomisoni.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/sabanomisoni /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

### ステップ 8 — ファイアウォールの設定

```bash
# HTTP のみ外部公開、SSH は管理用に残す
sudo ufw allow 'Nginx HTTP'
sudo ufw allow OpenSSH
sudo ufw enable
```

ブラウザで `http://<サーバーのIPアドレス>` にアクセスして掲示板が表示されれば完了です。

---

### 共通の注意事項

- **IP 記録と BAN 判定**を正しく動作させるため、Nginx の設定で `X-Forwarded-For` ヘッダーを渡すよう設定しています（上記設定に含まれています）。
- 本番運用では HTTPS (SSL/TLS) の設定を強く推奨します。[Let's Encrypt](https://letsencrypt.org/) を使えば無料で証明書を取得できます（`sudo apt install certbot python3-certbot-nginx` → `sudo certbot --nginx`）。
- `.env` ファイルには秘密情報が含まれています。Git にコミットしないよう注意してください（`.gitignore` に設定済み）。
