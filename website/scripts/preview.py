"""Build, serve, and rebuild after source edits; Ctrl+C to stop."""
from pathlib import Path
import subprocess,shutil,threading,time,sys
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
ROOT=Path(__file__).resolve().parents[1]
node=shutil.which('node') or str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
def build():return subprocess.run([node,str(ROOT/'scripts/build.mjs')]).returncode==0
def snapshot():
 return {str(p):p.stat().st_mtime_ns for d in ['lessons','templates','assets','data','scripts'] for p in (ROOT/d).rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.name!='theory-blocks.json'}
def watch():
 previous=snapshot()
 while True:
  time.sleep(1);current=snapshot()
  if current!=previous:
   build();previous=snapshot();print('Обновите страницу в браузере.',flush=True)
if not build():sys.exit(1)
threading.Thread(target=watch,daemon=True).start()
server=ThreadingHTTPServer(('127.0.0.1',4173),partial(SimpleHTTPRequestHandler,directory=str(ROOT/'dist')))
print('Предпросмотр: http://127.0.0.1:4173/topics/problem-solving-practice/index.html',flush=True)
try:server.serve_forever()
except KeyboardInterrupt:server.server_close()
