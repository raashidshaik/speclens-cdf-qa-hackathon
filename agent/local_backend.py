"""Local PGlite compatibility: serialize pool access; target business logic unchanged."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'test-website/backend'))
import demobank.repository as repo
OriginalPool=repo.AsyncConnectionPool
def single_connection_pool(*args,**kwargs):
 kwargs['min_size']=1;kwargs['max_size']=1
 return OriginalPool(*args,**kwargs)
repo.AsyncConnectionPool=single_connection_pool
from demobank.main import app
import uvicorn
uvicorn.run(app,host='127.0.0.1',port=8000)
