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
# Nginxレベルのレートリミット設定（ブルートフォース・DoS対策）
limit_req_zone $binary_remote_addr zone=sabanomisoni:10m rate=10r/s;

server {
    listen 80;
    server_name _;  # _ はすべてのホスト名を受け付けるという意味。独自ドメインがある場合は example.com のように変更

    # リクエストボディを1MBに制限する（大量データ送信対策）
    client_max_body_size 1m;

    location / {
        # Nginxレベルのレートリミットを適用する（バースト10リクエストまで許容）
        limit_req zone=sabanomisoni burst=10 nodelay;

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

### ステップ 10 — `.env` ファイルのパーミッション設定

`.env` ファイルには秘密鍵・DBパスワード等の機密情報が含まれています。適切なパーミッションを設定してください。

```bash
# パーミッションを600（オーナーのみ読み書き可能）に設定する
chmod 600 /home/ubuntu/sabanomisoni/.env

# オーナーをアプリ実行ユーザーに設定する（ubuntu の部分は実際のユーザー名に合わせてください）
chown ubuntu:ubuntu /home/ubuntu/sabanomisoni/.env
```

`.gitignore` に `.env` が含まれていることを確認します。

```bash
grep '\.env' /home/ubuntu/sabanomisoni/.gitignore
# .env と表示されれば設定済みです
```

---

### ステップ 11 — HTTPS 化（Let's Encrypt + Certbot）

> **注意**: 独自ドメインが必要です。EC2 のパブリック IP に対してドメインの A レコードを設定してから進めてください。

#### 11-1. Certbot のインストール

```bash
sudo apt install -y certbot python3-certbot-nginx
```

#### 11-2. SSL 証明書の取得

```bash
# example.com を実際のドメイン名に置き換えてください
sudo certbot --nginx -d example.com
```

対話形式で進めます。メールアドレスの入力・利用規約への同意を求められます。
成功すると Nginx の設定が自動的に更新され、HTTPS が有効になります。

#### 11-3. 証明書の自動更新設定

certbot をインストールすると `/etc/cron.d/certbot` が自動作成され、定期更新が設定されます。手動でテストするには以下を実行します。

```bash
sudo certbot renew --dry-run
```

`systemd timer` を使う場合は以下でも確認できます。

```bash
sudo systemctl status certbot.timer
```

#### 11-4. HTTPS 化後の環境変数設定

HTTPS 化が完了したら `.env` を以下のように更新してください。

```bash
nano /home/ubuntu/sabanomisoni/.env
```

以下の値を変更します。

```
# Nginxがリバースプロキシとして X-Forwarded-For を付与するため true に設定する
TRUST_PROXY_HEADERS=true

# HTTPS化済みのためセッションCookieにSecureフラグを付与する
HTTPS_ENABLED=true
```

変更後はアプリを再起動します。

```bash
sudo systemctl restart sabanomisoni
```

> **AWS EC2 + Nginx 構成で運用する場合は `TRUST_PROXY_HEADERS=true` に設定してください。**
> これにより Nginx が付与する `X-Forwarded-For` ヘッダーが信頼され、クライアント IP が正しく取得されます。
> プロキシを経由しない環境（直接インターネットに公開など）では `false` のままにしてください。

> **本番環境（HTTPS 化済み）では `HTTPS_ENABLED=true` に設定してください。**
> これによりセッション Cookie に `Secure` フラグが付与され、HTTPS 通信でのみ Cookie が送信されるようになります。

---

## オンプレミス環境でのデプロイ手順

> 自社サーバーに直接インストールして運用する方法です。OS は **Windows Server 2019** を前提にしています。

### 前提

- Windows Server 2019 がインストールされていること
- 管理者権限でログインできること
- インターネット接続が可能であること

---

### ステップ 1 — Python 3.12 のインストール

1. [Python 公式サイト](https://www.python.org/downloads/windows/) から **Python 3.12 の最新版 (Windows installer 64-bit)** をダウンロードします。
2. インストーラーを実行し、以下の点に注意してインストールします。
   - **「Add Python 3.12 to PATH」に必ずチェックを入れる**
   - 「Install Now」をクリック
3. インストール完了後、PowerShell（管理者権限）を開き、以下のコマンドで確認します。

```powershell
python --version
# Python 3.12.x と表示されれば成功
```

---

### ステップ 2 — MySQL のインストールとセットアップ

1. [MySQL Community Server](https://dev.mysql.com/downloads/mysql/) から **MySQL 8.x の Windows 版インストーラー** をダウンロードします（mysql-installer-community-x.x.x.msi）。
2. インストーラーを実行し、以下を選択します。
   - セットアップタイプ: **Server only**（サーバーのみ）または **Developer Default**
   - Config Type: **Development Computer**（開発用）または **Server Computer**
   - Authentication Method: **Use Strong Password Encryption**
   - Root パスワード: 強力なパスワードを設定（**必ずメモしてください**）
3. インストール完了後、スタートメニューから **「MySQL 8.x Command Line Client」** を起動します。
4. Root パスワードを入力してログインし、以下の SQL を実行します。

```sql
CREATE DATABASE saba_miso CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sabauser'@'localhost' IDENTIFIED BY 'あなたのパスワード';
GRANT ALL PRIVILEGES ON saba_miso.* TO 'sabauser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

### ステップ 3 — Git のインストール

1. [Git for Windows](https://git-scm.com/download/win) から **最新版の Git インストーラー** をダウンロードします。
2. インストーラーを実行し、デフォルト設定のままインストールします。

---

### ステップ 4 — アプリケーションの配置

PowerShell（管理者権限）を開き、以下のコマンドを順番に実行します。

```powershell
# 作業ディレクトリに移動（例: C:\inetpub）
cd C:\inetpub

# リポジトリをクローン
git clone https://github.com/<あなたのユーザー名>/sabanomisoni.git
cd sabanomisoni

# Python 仮想環境を作成
python -m venv .venv

# 仮想環境を有効化
.\.venv\Scripts\Activate.ps1

# 依存ライブラリをインストール
pip install -r requirements.txt
```

> **注意**: PowerShell の実行ポリシーでスクリプト実行がブロックされる場合、以下を実行してください。
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

---

### ステップ 5 — 環境変数の設定

```powershell
# .env ファイルを作成
Copy-Item .env.example .env

# メモ帳で編集
notepad .env
```

以下の内容を書き換えて保存します。

```
SECRET_KEY=（例: a1b2c3d4e5f6... のようなランダムな文字列）
DATABASE_URL=mysql+pymysql://sabauser:あなたのパスワード@localhost/saba_miso
ADMIN_USERNAME=admin
ADMIN_PASSWORD=強力なパスワード
```

> **ヒント**: `SECRET_KEY` にランダムな文字列を生成するには、PowerShell で以下を実行してください。
> ```powershell
> -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object {[char]$_})
> ```

---

### ステップ 6 — データベースの初期化

仮想環境が有効化されている状態で、以下を実行します。

```powershell
flask --app app.py init-db
```

「Created admin user: admin」と表示されれば成功です。

---

### ステップ 7 — IIS のインストールと設定

#### 7-1. IIS と必要な機能をインストール

1. **サーバーマネージャー** を開きます。
2. 「**役割と機能の追加**」をクリックします。
3. 「**役割ベースまたは機能ベースのインストール**」を選択し、次へ進みます。
4. 「**Web サーバー (IIS)**」にチェックを入れ、必要な機能を追加します。
5. 「**アプリケーション開発**」から以下にチェックを入れます。
   - CGI
   - WebSocket プロトコル
6. インストールを完了します。

#### 7-2. HttpPlatformHandler モジュールのインストール

1. [HttpPlatformHandler v1.2](https://www.iis.net/downloads/microsoft/httpplatformhandler) をダウンロードしてインストールします。
2. サーバーを再起動します。

---

### ステップ 8 — IIS サイトの作成と設定

1. **IIS マネージャー** を開きます（スタートメニューから「inetmgr」で検索）。
2. 左のツリーから「**サイト**」を右クリック → 「**Web サイトの追加**」を選択します。
3. 以下のように設定します。
   - サイト名: `sabanomisoni`
   - 物理パス: `C:\inetpub\sabanomisoni`
   - バインド: HTTP、ポート 80、ホスト名は空欄（すべて受け付ける）
4. 「OK」をクリックしてサイトを作成します。
5. 作成したサイトを選択し、「**ハンドラー マッピング**」を開きます。
6. 右側の「**モジュール マップの追加**」をクリックし、以下を設定します。
   - 要求パス: `*`
   - モジュール: `HttpPlatformHandler`
   - 実行可能ファイル: （空欄のまま）
   - 名前: `Python Application`
7. サイトのルートに `web.config` ファイルを作成します。

```powershell
notepad C:\inetpub\sabanomisoni\web.config
```

以下の内容を貼り付けて保存します。

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="httpPlatformHandler" path="*" verb="*" modules="httpPlatformHandler" resourceType="Unspecified" />
    </handlers>
    <httpPlatform processPath="C:\inetpub\sabanomisoni\.venv\Scripts\python.exe"
                  arguments="-m gunicorn --bind 127.0.0.1:%HTTP_PLATFORM_PORT% --workers 2 app:app"
                  stdoutLogEnabled="true"
                  stdoutLogFile="C:\inetpub\sabanomisoni\logs\stdout.log"
                  startupTimeLimit="60"
                  requestTimeout="00:04:00">
      <environmentVariables>
        <environmentVariable name="PYTHONPATH" value="C:\inetpub\sabanomisoni" />
      </environmentVariables>
    </httpPlatform>
  </system.webServer>
</configuration>
```

8. ログ出力用のフォルダを作成します。

```powershell
New-Item -ItemType Directory -Path C:\inetpub\sabanomisoni\logs -Force
```

9. IIS マネージャーでサイトを再起動します（右クリック → 停止 → 開始）。

---

### ステップ 9 — ファイアウォールの設定

PowerShell（管理者権限）で以下を実行し、HTTP (ポート 80) を外部に公開します。

```powershell
New-NetFirewallRule -DisplayName "Allow HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
```

---

### ステップ 10 — 動作確認

ブラウザで `http://<サーバーのIPアドレス>` または `http://localhost` にアクセスして掲示板が表示されれば完了です。

---

### トラブルシューティング

- **503 エラーが出る場合**: `C:\inetpub\sabanomisoni\logs\stdout.log` を確認してエラー内容を確認してください。
- **仮想環境のパスエラー**: `web.config` 内の Python.exe と gunicorn のパスが正しいか確認してください。
- **データベース接続エラー**: `.env` ファイルの `DATABASE_URL` が正しいか、MySQL サービスが起動しているか確認してください。

---

### 共通の注意事項

- **IP 記録と BAN 判定**を正しく動作させるため、IIS の設定で `X-Forwarded-For` ヘッダーを渡すよう設定しています（上記 `web.config` に含まれています）。
- 本番運用では HTTPS (SSL/TLS) の設定を強く推奨します。IIS では証明書をインポートし、バインドで HTTPS (ポート 443) を設定してください。
- `.env` ファイルには秘密情報が含まれています。Git にコミットしないよう注意してください（`.gitignore` に設定済み）。
- Windows Server では定期的な Windows Update の実行と、セキュリティパッチの適用を忘れずに行ってください。
