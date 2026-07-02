import sys
import os
import traceback

try:
    # 使用しているPythonのパスを出力
    print(f'Python executable: {sys.executable}', flush=True)
    print(f'Python version: {sys.version}', flush=True)
    print(f'Working directory: {os.getcwd()}', flush=True)

    # カレントディレクトリを設定
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # .envファイルを読み込む
    from dotenv import load_dotenv
    load_dotenv()

    from waitress import serve
    from app import app

    port = int(os.environ.get('HTTP_PLATFORM_PORT', '8000'))
    threads = int(os.environ.get('WAITRESS_THREADS', '4'))
    print(f'Starting Waitress on port {port}', flush=True)
    sys.stdout.flush()

    serve(app, host='127.0.0.1', port=port, threads=threads)

except Exception as e:
    print(f'Error starting application: {e}', file=sys.stderr, flush=True)
    print(traceback.format_exc(), file=sys.stderr, flush=True)
    sys.stderr.flush()
    raise
