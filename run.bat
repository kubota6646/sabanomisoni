@echo off
rem waitress-serve.exe を直接呼び出すことで Python Launcher (py.exe) を経由しない
C:\inetpub\sabanomisoni\.venv\Scripts\waitress-serve.exe --port=%HTTP_PLATFORM_PORT% --host=127.0.0.1 app:app
