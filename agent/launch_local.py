"""Launch isolated official target and agent together; never modifies target source."""
import os, subprocess, time, urllib.request, sys, secrets
from pathlib import Path
root=Path(__file__).resolve().parents[1]
procs=[]
def start(cmd,cwd,env=None):
 f=open(Path(__file__).parent/(str(len(procs))+'-service.log'),'w')
 p=subprocess.Popen(cmd,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT);procs.append(p)
def wait(url):
 for _ in range(80):
  try:
   with urllib.request.urlopen(url,timeout=1) as r:
    if r.status==200:return
  except Exception:time.sleep(.5)
 raise RuntimeError('Service not ready: '+url)
try:
 start(['node','local-runtime/db.mjs'],root/'agent')
 time.sleep(4)
 env=dict(os.environ,DATABASE_URL='postgresql://postgres:postgres@127.0.0.1:5432/postgres?sslmode=disable',SESSION_SECRET=secrets.token_urlsafe(32))
 start([sys.executable,'local_backend.py'],root/'agent',env)
 start(['npm','run','dev','--','--host','localhost'],root/'test-website/frontend')
 wait('http://localhost:8000/health');wait('http://localhost:5173')
 subprocess.run([sys.executable,'run.py','--allow-demo-target',*sys.argv[1:]],cwd=root/'agent',check=True)
finally:
 for p in reversed(procs):p.terminate()
