@echo off
rem waitress-serve.exe を直接呼び出すことで Python Launcher (py.exe) を経由しない
rem %~dp0 はこの bat ファイルがあるディレクトリに展開される
%~dp0.venv\Scripts\waitress-serve.exe --port=%HTTP_PLATFORM_PORT% --host=127.0.0.1 app:app
