# サバの味噌煮 🐟

匿名で利用できるシンプルな総合掲示板 Web アプリケーションです。  
Flask + SQLAlchemy を使ったサーバーサイドレンダリング構成で、MySQL / SQLite の両方に対応しています。

---

## 目次

- [主な機能](#主な機能)
- [技術スタック](#技術スタック)
- [ローカル開発環境のセットアップ](#ローカル開発環境のセットアップ)
- [テスト](#テスト)
- [データベース](#データベース)
- [画面 / ルート](#画面--ルート)
- [セキュリティ上の考慮](#セキュリティ上の考慮)
- [AWS EC2 + RDS デプロイ手順](#aws-ec2--rds-デプロイ手順)
- [オンプレミス環境でのデプロイ手順（Windows Server + IIS）](#オンプレミス環境でのデプロイ手順windows-server--iis)

---

## 主な機能

| 機能 | 説明 |
|------|------|
| スレッド管理 | スレッドの一覧表示・作成・編集・削除 |
| レス投稿 | スレッドへの返信投稿・編集・削除 |
| 編集キー | 投稿者本人のみが編集・削除できる編集キー機能 |
| 管理者機能 | 管理者ログイン・全スレッド/レスの削除・NG ワード管理 |
| BAN 機能 | 投稿 IP の記録と管理者による BAN |
| レスポンシブ UI | PC / スマートフォン向けのシンプルなデザイン |

---

## 技術スタック

| 項目 | 内容 |
|------|------|
| 言語 | Python 3.12 |
| Web フレームワーク | Flask 3.1 |
| ORM | Flask-SQLAlchemy 3.1 |
| データベース | SQLite（デフォルト）/ MySQL 8.x（本番推奨）|
| WSGI サーバー（Linux） | Gunicorn 23 |
| WSGI サーバー（Windows） | Waitress 3.0 |
| フォームバリデーション | Flask-WTF 1.3 |
| レート制限 | Flask-Limiter 4.1 |
| セキュリティヘッダー | Flask-Talisman 1.1 |

---

## ローカル開発環境のセットアップ

```bash
# 1. リポジトリをクローン
git clone https://github.com/<あなたのユーザー名>/sabanomisoni.git
cd sabanomisoni

# 2. Python 仮想環境を作成・有効化
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\Activate.ps1

# 3. 依存ライブラリをインストール
pip install -r requirements.txt

# 4. 環境変数を設定
cp .env.example .env
# .env をエディタで開き、SECRET_KEY・ADMIN_USERNAME・ADMIN_PASSWORD を設定してください

# 5. テーブルを作成（初回のみ）
flask --app app.py init-db

# 6. 開発サーバーを起動
flask --app app.py run --debug
```

> **MySQL を使う場合**: `.env` の `DATABASE_URL` のコメントを外して接続情報を設定してください。  
> 未設定または接続できない場合は自動的に SQLite（`instance/saba_miso.db`）を使用します。

---

## テスト

```bash
python -m unittest discover -s tests
```

---

## データベース

| 状況 | 使用する DB |
|------|------------|
| `DATABASE_URL` が未設定 | SQLite（`instance/saba_miso.db`）|
| `DATABASE_URL` に MySQL URL を設定したが接続不可 | SQLite（自動フォールバック）|
| `DATABASE_URL` に MySQL URL を設定し接続可 | MySQL |

- MySQL 向けスキーマ: `database/schema.sql`

---

## 画面 / ルート

| パス | 内容 |
|------|------|
| `/` | スレッド一覧 / 新規作成 |
| `/threads/<id>` | スレッド詳細 / レス一覧 / レス投稿 |
| `/threads/<id>/edit` | スレッド編集 |
| `/responses/<id>/edit` | レス編集 |
| `/admin/login` | 管理者ログイン |
| `/admin` | 管理者ダッシュボード |

---

## セキュリティ上の考慮

- 編集キー・管理者パスワードはハッシュ化して保存
- ORM により SQL インジェクションを回避
- Jinja2 自動エスケープと `white-space: pre-wrap` で XSS を抑制
- CSRF トークン保護（Flask-WTF）
- エンドポイントごとのレート制限（Flask-Limiter）
- セキュリティヘッダーの自動付与（Flask-Talisman）
- NG ワード投稿を拒否
- 投稿 IP を保存し、管理者が BAN 可能

---

## AWS EC2 + RDS デプロイ手順

> PC 初心者の方でも手順通りに進めれば公開できます。各ステップをひとつずつ実行してください。

### 前提

- AWS アカウントをお持ちであること
- ターミナル（Windows なら PowerShell、Mac/Linux なら Terminal）を使えること

---

### ステップ 1 — RDS (MySQL) の作成

1. [AWS マネジメントコンソール](https://console.aws.amazon.com/) にログインします。
2. **RDS** を開き、「**データベースの作成**」をクリックします。
3. 以下の通り設定します。

   | 項目 | 設定値 |
   |------|--------|
   | エンジン | MySQL |
   | テンプレート | 無料利用枠 |
   | DB インスタンス識別子 | 任意（例: `saba-miso-db`）|
   | マスターユーザー名 | 任意（例: `dbadmin`）※メモ必須 |
   | マスターパスワード | 強力なパスワード ※メモ必須 |
   | パブリックアクセス | なし |
   | 最初のデータベース名 | `saba_miso` |

4. 「**データベースの作成**」をクリックし、数分待ちます。
5. 作成後、RDS の詳細ページから **エンドポイント**（例: `saba-miso-db.xxxxxx.ap-northeast-1.rds.amazonaws.com`）をメモします。
6. RDS のセキュリティグループの「インバウンドルール」に、EC2 からのポート **3306** 接続を許可するルールを追加します。

---

### ステップ 2 — EC2 インスタンスの作成

1. AWS コンソールで **EC2** を開き、「**インスタンスを起動**」をクリックします。
2. 以下の通り設定します。

   | 項目 | 設定値 |
   |------|--------|
   | AMI | Ubuntu Server 24.04 LTS（無料利用枠対象）|
   | インスタンスタイプ | t2.micro または t3.micro（無料利用枠対象）|
   | キーペア | 新しいキーペアを作成 → .pem ファイルをダウンロード（紛失厳禁）|
   | セキュリティグループ | SSH(22) を自分の IP から、HTTP(80) をどこからでも許可 |

3. 「**インスタンスを起動**」をクリックし、**パブリック IPv4 アドレス**をメモします。

---

### ステップ 3 — EC2 への SSH 接続

```bash
# Mac/Linux
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@<EC2のパブリックIPアドレス>
```

```powershell
# Windows (PowerShell)
ssh -i C:\Users\あなたのユーザー名\Downloads\your-key.pem ubuntu@<EC2のパブリックIPアドレス>
```

「Are you sure you want to continue connecting?」と聞かれたら **`yes`** を入力して Enter を押します。

---

### ステップ 4 — サーバーのセットアップ

```bash
# システムを最新化
sudo apt update && sudo apt upgrade -y

# Python 3.12・Nginx・Git をインストール
sudo apt install -y python3.12 python3.12-venv python3-pip nginx git
```

---

### ステップ 5 — アプリケーションの配置

```bash
cd /home/ubuntu

# リポジトリをクローン（main ブランチを指定）
git clone -b main https://github.com/<あなたのユーザー名>/sabanomisoni.git
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
nano .env   # Ctrl+O で保存、Ctrl+X で終了
```

以下を書き換えます。

```
SECRET_KEY=<openssl rand -hex 32 の出力>
DATABASE_URL=mysql+pymysql://dbadmin:RDSパスワード@RDSエンドポイント/saba_miso
ADMIN_USERNAME=admin
ADMIN_PASSWORD=強力なパスワード
```

> **ヒント**: `SECRET_KEY` の生成は `openssl rand -hex 32` を実行してください。

セキュリティのため、`.env` のパーミッションを設定します。

```bash
chmod 600 /home/ubuntu/sabanomisoni/.env
```

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
sudo systemctl status sabanomisoni   # 起動状態を確認
```

---

### ステップ 9 — Nginx のリバースプロキシ設定

```bash
sudo nano /etc/nginx/sites-available/sabanomisoni
```

以下の内容を貼り付けます。

```nginx
# Nginx レベルのレートリミット設定（DoS 対策）
limit_req_zone $binary_remote_addr zone=sabanomisoni:10m rate=10r/s;

server {
    listen 80;
    server_name _;  # 独自ドメインがある場合は example.com のように変更

    client_max_body_size 1m;

    location / {
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
sudo nginx -t
sudo systemctl reload nginx
```

ブラウザで `http://<EC2のパブリックIPアドレス>` にアクセスして掲示板が表示されれば完了です。

---

### ステップ 10 — HTTPS 化（Let's Encrypt + Certbot）

> **注意**: 独自ドメインが必要です。EC2 のパブリック IP にドメインの A レコードを設定してから進めてください。

```bash
# Certbot のインストール
sudo apt install -y certbot python3-certbot-nginx

# SSL 証明書の取得（example.com を実際のドメインに置き換えてください）
sudo certbot --nginx -d example.com
```

成功すると Nginx の設定が自動的に更新され、HTTPS が有効になります。証明書は自動更新されます（確認: `sudo certbot renew --dry-run`）。

HTTPS 化が完了したら `.env` を更新します。

```bash
nano /home/ubuntu/sabanomisoni/.env
```

```
# Nginx がリバースプロキシとして X-Forwarded-For を付与するため true に設定する
TRUST_PROXY_HEADERS=true

# HTTPS 化済みのためセッション Cookie に Secure フラグを付与する
HTTPS_ENABLED=true
```

変更後はアプリを再起動します。

```bash
sudo systemctl restart sabanomisoni
```

> **`TRUST_PROXY_HEADERS=true`**: Nginx 経由の場合のみ設定してください。直接公開している環境では `false` のままにしてください。  
> **`HTTPS_ENABLED=true`**: HTTPS 化済みの場合に設定してください。

---

### アプリのアップデート（EC2）

コードに更新があった場合は、以下の手順でアプリを最新バージョンに更新してください。

```bash
cd /home/ubuntu/sabanomisoni

# リモートの最新情報を取得
git fetch origin

# アップデートしたいブランチを指定して切り替え・更新
# （通常は main ブランチを使用します）
git checkout main
git pull origin main

# 依存ライブラリを更新（新しいライブラリが追加されている場合に対応）
source .venv/bin/activate
pip install -r requirements.txt

# アプリを再起動
sudo systemctl restart sabanomisoni

# 再起動後の状態確認
sudo systemctl status sabanomisoni
```

> **特定のバージョン（タグ）に切り替える場合**:
> ```bash
> git fetch origin --tags
> git checkout tags/v1.2.0   # バージョン番号は適宜変更してください
> pip install -r requirements.txt
> sudo systemctl restart sabanomisoni
> ```

> **更新後にデータベーススキーマが変わった場合** は、`flask --app app.py init-db` を再実行してください。

---

## オンプレミス環境でのデプロイ手順（Windows Server + IIS）

> 自社サーバーに直接インストールして運用する方法です。OS は **Windows Server 2019** を前提にしています。

### 前提

- Windows Server 2019 がインストールされていること
- 管理者権限でログインできること
- インターネット接続が可能であること

---

### ステップ 1 — Python 3.12 のインストール

1. [Python 公式サイト](https://www.python.org/downloads/windows/) から **Python 3.12 の最新版 (Windows installer 64-bit)** をダウンロードします。
2. インストーラーを実行し、**「Add Python 3.12 to PATH」に必ずチェックを入れて**インストールします。
3. インストール後、PowerShell（管理者権限）で確認します。

```powershell
python --version
# Python 3.12.x と表示されれば成功
```

---

### ステップ 2 — MySQL のインストールとセットアップ

1. [MySQL Community Server](https://dev.mysql.com/downloads/mysql/) から **MySQL 8.x の Windows 版インストーラー** をダウンロードします。
2. インストーラーを実行し、Root パスワードを設定します（**必ずメモしてください**）。
3. スタートメニューから **「MySQL 8.x Command Line Client」** を起動し、以下の SQL を実行します。

```sql
CREATE DATABASE saba_miso CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sabauser'@'localhost' IDENTIFIED BY 'あなたのパスワード';
GRANT ALL PRIVILEGES ON saba_miso.* TO 'sabauser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

### ステップ 3 — Git のインストール

1. [Git for Windows](https://git-scm.com/download/win) から最新版をダウンロードし、デフォルト設定でインストールします。

---

### ステップ 4 — アプリケーションの配置

PowerShell（管理者権限）を開き、以下を順番に実行します。

```powershell
# 作業ディレクトリに移動
cd C:\inetpub

# main ブランチを指定してリポジトリをクローン
git clone -b main https://github.com/<あなたのユーザー名>/sabanomisoni.git
cd sabanomisoni

# Python 仮想環境を作成
python -m venv .venv

# 仮想環境を有効化
.\.venv\Scripts\Activate.ps1

# 依存ライブラリをインストール
pip install -r requirements.txt
```

> **注意**: PowerShell の実行ポリシーでスクリプト実行がブロックされる場合は以下を実行してください。
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

---

### ステップ 5 — 環境変数の設定

```powershell
Copy-Item .env.example .env
notepad .env
```

以下の内容を書き換えて保存します。

```
SECRET_KEY=<ランダムな文字列>
DATABASE_URL=mysql+pymysql://sabauser:あなたのパスワード@localhost/saba_miso
ADMIN_USERNAME=admin
ADMIN_PASSWORD=強力なパスワード
```

> **ヒント**: `SECRET_KEY` の生成は PowerShell で以下を実行してください。
> ```powershell
> -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object {[char]$_})
> ```

---

### ステップ 6 — データベースの初期化

仮想環境が有効化されている状態で実行します。

```powershell
flask --app app.py init-db
```

「Created admin user: admin」と表示されれば成功です。

---

### ステップ 7 — IIS のインストールと HttpPlatformHandler の設定

#### 7-1. IIS と必要な機能をインストール

1. **サーバーマネージャー** を開き、「**役割と機能の追加**」をクリックします。
2. 「**Web サーバー (IIS)**」を選択し、「**アプリケーション開発**」から以下にチェックを入れます。
   - CGI
   - WebSocket プロトコル
3. インストールを完了します。

#### 7-2. HttpPlatformHandler モジュールのインストール

1. [HttpPlatformHandler](https://www.iis.net/downloads/microsoft/httpplatformhandler) のページから **最新版** をダウンロードしてインストールします。

   > **注意**: 旧バージョン（v1.2 以前）には `processPath` に指定した実行ファイルを直接起動せず `PATH` を経由して Python を探すバグがある場合があります。最新版の使用を強く推奨します。

2. サーバーを再起動します。

---

### ステップ 8 — IIS サイトの作成と設定

1. **IIS マネージャー**（`inetmgr`）を開きます。
2. 「**サイト**」を右クリック → 「**Web サイトの追加**」を選択し、以下を設定します。

   | 項目 | 設定値 |
   |------|--------|
   | サイト名 | `sabanomisoni` |
   | 物理パス | `C:\inetpub\sabanomisoni` |
   | バインド | HTTP、ポート 80、ホスト名は空欄 |

3. 作成したサイトの「**ハンドラー マッピング**」→「**モジュール マップの追加**」で以下を設定します。

   | 項目 | 設定値 |
   |------|--------|
   | 要求パス | `*` |
   | モジュール | `HttpPlatformHandler` |
   | 実行可能ファイル | （空欄のまま）|
   | 名前 | `Python Application` |

4. リポジトリに `web.config` が含まれているため、Git クローン済みであればそのまま使用できます。手動で作成・上書きする場合は以下を実行してください。

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
    <!--
      processPath に waitress-serve.exe を直接指定することで、Python Launcher (py.exe) や
      PATH 解決を完全に回避し、仮想環境の Python だけを使って waitress を起動します。
      %APPL_PHYSICAL_PATH% は IIS がアプリケーションの物理パスに展開します。
    -->
    <httpPlatform processPath="%APPL_PHYSICAL_PATH%\.venv\Scripts\waitress-serve.exe"
                  arguments="--port=%HTTP_PLATFORM_PORT% --host=127.0.0.1 app:app"
                  stdoutLogEnabled="true"
                  stdoutLogFile="%APPL_PHYSICAL_PATH%\logs\stdout.log"
                  startupTimeLimit="60"
                  requestTimeout="00:04:00">
      <environmentVariables>
        <environmentVariable name="PYTHONPATH" value="%APPL_PHYSICAL_PATH%" />
      </environmentVariables>
    </httpPlatform>
  </system.webServer>
</configuration>
```

> **ポイント**: `processPath` に `waitress-serve.exe` を直接指定することで、Python Launcher（`py.exe`）や `PATH` 経由で別の Python が起動されてしまう問題を回避しています。アプリの環境変数（`SECRET_KEY`・`DATABASE_URL` など）はアプリケーションディレクトリの `.env` ファイルから読み込まれます（ステップ 5 で作成済み）。IIS を起動する前に `.env` ファイルが存在することを確認してください。

5. ログ出力用フォルダを作成します。

```powershell
New-Item -ItemType Directory -Path C:\inetpub\sabanomisoni\logs -Force
```

6. IIS マネージャーでサイトを再起動します（右クリック → 停止 → 開始）。

---

### ステップ 9 — ファイアウォールの設定

```powershell
New-NetFirewallRule -DisplayName "Allow HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
```

---

### ステップ 10 — 動作確認

ブラウザで `http://<サーバーのIPアドレス>` または `http://localhost` にアクセスして掲示板が表示されれば完了です。

---

### アプリのアップデート（Windows / IIS）

コードに更新があった場合は、以下の手順でアプリを最新バージョンに更新してください。

PowerShell（管理者権限）を開き、以下を実行します。

```powershell
cd C:\inetpub\sabanomisoni

# リモートの最新情報を取得
git fetch origin

# アップデートしたいブランチを指定して切り替え・更新
# （通常は main ブランチを使用します）
git checkout main
git pull origin main

# 依存ライブラリを更新
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

更新後、IIS マネージャーでサイトを再起動します（右クリック → 停止 → 開始）。または PowerShell から実行します。

```powershell
# IIS サイトを再起動
Stop-Website -Name "sabanomisoni"
Start-Website -Name "sabanomisoni"
```

> **特定のバージョン（タグ）に切り替える場合**:
> ```powershell
> git fetch origin --tags
> git checkout tags/v1.2.0   # バージョン番号は適宜変更してください
> pip install -r requirements.txt
> Stop-Website -Name "sabanomisoni"; Start-Website -Name "sabanomisoni"
> ```

> **更新後にデータベーススキーマが変わった場合** は、仮想環境を有効化した状態で `flask --app app.py init-db` を再実行してください。

---

### トラブルシューティング（IIS）

| 症状 | 確認・対処方法 |
|------|--------------|
| 503 エラーが出る | `C:\inetpub\sabanomisoni\logs\stdout.log` を確認してください |
| `waitress-serve.exe` が見つからない | 仮想環境を有効化した状態で `pip install waitress` を実行してください |
| `%APPL_PHYSICAL_PATH%` が展開されない | IIS マネージャーでサイトの「基本設定」→「物理パス」を確認してください |
| 起動時に別の Python が使われる | HttpPlatformHandler を最新版に更新してください |
| データベース接続エラー | `.env` の `DATABASE_URL` と MySQL サービスの起動状態を確認してください |

---

### 共通の注意事項

- 本番運用では HTTPS (SSL/TLS) の設定を強く推奨します。IIS では証明書をインポートし、バインドで HTTPS (ポート 443) を設定してください。
- `.env` ファイルには秘密情報が含まれています。Git にコミットしないよう注意してください（`.gitignore` に設定済み）。
- Windows Server では定期的な Windows Update の実行とセキュリティパッチの適用を行ってください。

