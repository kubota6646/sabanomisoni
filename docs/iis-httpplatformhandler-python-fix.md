# IIS + HttpPlatformHandler で正しい Python が起動されない問題の修正

## 問題の概要

`web.config` で仮想環境の `python.exe` を `processPath` に指定しているにもかかわらず、
IIS（HttpPlatformHandler）が別の Python（`C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe`）を参照して起動に失敗する。

### 発生しているエラー（イベントログ）

```
Process 'XXXX' failed to start. Port = XXXXX, Error Code = '-2147023829'
```

```
did not find executable at 'C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe': Access is denied.
```

### 環境

| 項目 | 内容 |
|------|------|
| OS | Windows Server |
| Web サーバー | IIS + HttpPlatformHandler |
| アプリサーバー | waitress |
| Python（仮想環境） | `C:\inetpub\sabanomisoni\.venv\Scripts\python.exe` |
| 誤って参照される Python | `C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe` |
| アプリプールユーザー | Administrator（SpecificUser に変更済み） |

### 原因

1. `C:\Windows\py.exe`（Python Launcher）が `PATH` の解決に介在している
2. ユーザー環境変数 `PATH` に Python313 が登録されており、HttpPlatformHandler がそちらを優先する
3. HttpPlatformHandler の旧バージョンに、`processPath` を直接呼び出さず `PATH` から Python を探すバグがある可能性がある

### 試みた対処（すべて効果なし）

- `web.config` の `environmentVariables` に `PATH` を明示的に上書き
- ユーザー環境変数から Python313 を削除
- アプリプールユーザーを Administrator に変更
- `processPath` を `cmd.exe` 経由・バッチファイル経由に変更
- Python313 フォルダに IIS アプリプールの拒否 ACL を追加

---

## 依頼内容

以下のいずれかの方法で問題を解決し、IIS 経由でアプリが正常に起動するようにしてください。

### 優先して試みてほしい解決策

#### 方針 A：HttpPlatformHandler を最新バージョンに更新する

現在インストールされている HttpPlatformHandler のバージョンを確認し、
旧バージョン（v1.2 以前）であれば最新版（v2.0 以降、または Microsoft が提供する最新版）に更新する。

確認コマンド：
```powershell
Get-Item "C:\Windows\System32\inetsrv\HttpPlatformHandler*.dll" | Select-Object Name, VersionInfo
Get-Item "C:\Windows\SysWOW64\inetsrv\HttpPlatformHandler*.dll" | Select-Object Name, VersionInfo
```

ダウンロード先：
- https://www.iis.net/downloads/microsoft/httpplatformhandler
- または Windows Server 向け最新版を Microsoft 公式から取得

#### 方針 B：Python Launcher（py.exe）を無効化または迂回する

`C:\Windows\py.exe` が仲介しないよう、以下のいずれかを実施する：

1. Python Launcher のデフォルトバージョン設定ファイル（`py.ini`）を作成して仮想環境の Python を指定する
2. または `C:\Windows\py.exe` 自体を IIS アプリプールから参照できないよう ACL で制限する

#### 方針 C：waitress ではなく gunicorn を使用する

`web.config` で直接 `gunicorn` を呼び出す構成に変更する。
`gunicorn` は仮想環境の `Scripts` フォルダに存在するため、Python Launcher を経由しない。

```xml
<httpPlatform processPath="C:\inetpub\sabanomisoni\.venv\Scripts\gunicorn.exe"
              arguments="--bind 127.0.0.1:%HTTP_PLATFORM_PORT% --workers 2 app:app"
              ...>
```

`gunicorn` が未インストールの場合は以下でインストール：
```powershell
C:\inetpub\sabanomisoni\.venv\Scripts\pip.exe install gunicorn
```

> **注意**: gunicorn は Windows 環境では公式サポート外ですが、waitress の代替として動作する場合があります。
> 動作しない場合は waitress のラッパースクリプトを gunicorn 相当の形で作成することも検討してください。

---

## 期待する結果

- IIS 経由でブラウザからサイトにアクセスしたとき、掲示板のトップページが表示されること
- `C:\inetpub\sabanomisoni\logs\stdout.log_*` に waitress（または代替サーバー）の起動ログが出力されること
- Python313 への参照エラーが発生しないこと

## 現在の web.config（参考）

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="httpPlatformHandler" path="*" verb="*" modules="httpPlatformHandler" resourceType="Unspecified" />
    </handlers>
    <httpPlatform processPath="C:\Windows\System32\cmd.exe"
                  arguments="/c C:\inetpub\sabanomisoni\run.bat"
                  stdoutLogEnabled="true"
                  stdoutLogFile="C:\inetpub\sabanomisoni\logs\stdout.log"
                  startupTimeLimit="60"
                  requestTimeout="00:04:00">
      <environmentVariables>
        <environmentVariable name="HTTP_PLATFORM_PORT" value="%HTTP_PLATFORM_PORT%" />
        <environmentVariable name="PYTHONPATH" value="C:\inetpub\sabanomisoni" />
        <environmentVariable name="FLASK_APP" value="app.py" />
        <environmentVariable name="SECRET_KEY" value="（設定済み）" />
        <environmentVariable name="ADMIN_USERNAME" value="（設定済み）" />
        <environmentVariable name="ADMIN_PASSWORD" value="（設定済み）" />
        <environmentVariable name="WTF_CSRF_SECRET_KEY" value="（設定済み）" />
        <environmentVariable name="TRUST_PROXY_HEADERS" value="false" />
        <environmentVariable name="HTTPS_ENABLED" value="false" />
        <environmentVariable name="ADMIN_SESSION_HOURS" value="2" />
      </environmentVariables>
    </httpPlatform>
  </system.webServer>
</configuration>
```

## 現在の run.bat（参考）

```bat
@echo off
C:\inetpub\sabanomisoni\.venv\Scripts\python.exe -m waitress --port=%HTTP_PLATFORM_PORT% --host=127.0.0.1 app:app
```

## ディレクトリ構成（参考）

```
C:\inetpub\sabanomisoni\
├── .venv\
│   └── Scripts\
│       ├── python.exe         ← 使いたい Python
│       ├── waitress-serve.exe
│       └── pip.exe
├── saba_miso\
│   ├── static\
│   ├── templates\
│   ├── __init__.py
│   ├── admin.py
│   ├── extensions.py
│   ├── models.py
│   ├── utils.py
│   └── views.py
├── app.py
├── run.bat
├── web.config
├── logs\
└── requirements.txt
```
