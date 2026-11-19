import os, sqlite3, uuid, subprocess, sys, shutil, threading, secrets, base64
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

ROOT=Path(__file__).resolve().parent
DATA=Path(os.getenv('WORSHIP_DATA', ROOT/'data')).resolve()
DATA.mkdir(parents=True,exist_ok=True)
DB=DATA/'app.sqlite3'
MAX_BYTES=100*1024*1024
ALLOWED={'.mp3','.wav','.flac','.m4a','.ogg'}
app=FastAPI(title='Worship Stem Player MVP')

@app.middleware('http')
async def protect(request: Request, call_next):
    username=os.getenv('APP_USERNAME','')
    password=os.getenv('APP_PASSWORD','')
    if not username or not password:
        return Response('APP_USERNAME and APP_PASSWORD must be configured',status_code=503)
    header=request.headers.get('authorization','')
    try:
        scheme, token=header.split(' ',1)
        decoded=base64.b64decode(token,validate=True).decode('utf-8')
        supplied_user,supplied_password=decoded.split(':',1)
    except (ValueError,UnicodeError):
        supplied_user=supplied_password=''
        scheme=''
    if not (scheme.lower()=='basic' and secrets.compare_digest(supplied_user,username) and secrets.compare_digest(supplied_password,password)):
        return Response('Authentication required',status_code=401,headers={'WWW-Authenticate':'Basic realm="Worship Stem Player"'})
    return await call_next(request)


def conn():
 c=sqlite3.connect(DB,timeout=30); c.row_factory=sqlite3.Row; return c
with conn() as c:
 c.execute('CREATE TABLE IF NOT EXISTS songs (id TEXT PRIMARY KEY,title TEXT NOT NULL,original TEXT NOT NULL,status TEXT NOT NULL,error TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
 c.execute('CREATE TABLE IF NOT EXISTS stems (id TEXT PRIMARY KEY,song_id TEXT NOT NULL,label TEXT NOT NULL,path TEXT NOT NULL,FOREIGN KEY(song_id) REFERENCES songs(id))')

def song_payload(c, row):
 d=dict(row); d['stems']=[{'id':s['id'],'label':s['label'],'url':f"/api/stems/{s['id']}/audio"} for s in c.execute('SELECT * FROM stems WHERE song_id=? ORDER BY label',(d['id'],))];return d

@app.get('/api/songs')
def songs():
 with conn() as c: return [song_payload(c,r) for r in c.execute('SELECT * FROM songs ORDER BY created_at DESC')]

@app.post('/api/songs',status_code=201)
async def upload(file:UploadFile=File(...)):
 name=Path(file.filename or '').name
 ext=Path(name).suffix.lower()
 if ext not in ALLOWED: raise HTTPException(400,'지원하지 않는 파일 확장자입니다.')
 sid=uuid.uuid4().hex; folder=DATA/'uploads'/sid;folder.mkdir(parents=True)
 target=folder/('source'+ext); total=0
 try:
  with target.open('wb') as out:
   while chunk:=await file.read(1024*1024):
    total+=len(chunk)
    if total>MAX_BYTES: raise HTTPException(413,'파일 크기는 100MB 이하여야 합니다.')
    out.write(chunk)
 except Exception:
  target.unlink(missing_ok=True);shutil.rmtree(folder,ignore_errors=True);raise
 finally: await file.close()
 with conn() as c: c.execute('INSERT INTO songs(id,title,original,status) VALUES(?,?,?,?)',(sid,Path(name).stem,str(target),'uploaded'))
 return {'id':sid,'status':'uploaded'}

def separate(sid):
 with conn() as c:
  row=c.execute('SELECT * FROM songs WHERE id=?',(sid,)).fetchone()
 if not row:return
 try:
  output=DATA/'separated'/sid;output.mkdir(parents=True,exist_ok=True)
  # Requires separately installed torch and demucs. No fake AI results.
  result=subprocess.run([sys.executable,'-m','demucs','-n','htdemucs_6s','--out',str(output),row['original']],capture_output=True,text=True,timeout=3600)
  if result.returncode:raise RuntimeError((result.stderr or result.stdout)[-1200:])
  files=list(output.glob('**/*.wav'))
  if not files:raise RuntimeError('AI 분리 결과 WAV 파일이 없습니다.')
  with conn() as c:
   c.execute('DELETE FROM stems WHERE song_id=?',(sid,))
   for f in files:c.execute('INSERT INTO stems(id,song_id,label,path) VALUES(?,?,?,?)',(uuid.uuid4().hex,sid,f.stem,str(f.resolve())))
   c.execute('UPDATE songs SET status=?,error=NULL WHERE id=?',('ready',sid))
 except Exception as e:
  with conn() as c:c.execute('UPDATE songs SET status=?,error=? WHERE id=?',('failed',str(e)[:1200],sid))

@app.post('/api/songs/{sid}/separate')
def start_separation(sid:str):
 if os.getenv('ENABLE_AI','false').lower()!='true':raise HTTPException(503,'AI 분리 서버가 아직 활성화되지 않았습니다. GPU 처리 서버 연결 후 사용할 수 있습니다.')
 with conn() as c:
  row=c.execute('SELECT * FROM songs WHERE id=?',(sid,)).fetchone()
  if not row:raise HTTPException(404,'곡을 찾을 수 없습니다.')
  if row['status']=='processing':raise HTTPException(409,'이미 처리 중입니다.')
  c.execute('UPDATE songs SET status=?,error=NULL WHERE id=?',('processing',sid))
 threading.Thread(target=separate,args=(sid,),daemon=True).start()
 return {'status':'processing'}

@app.get('/api/stems/{stem_id}/audio')
def audio(stem_id:str):
 with conn() as c: row=c.execute('SELECT path FROM stems WHERE id=?',(stem_id,)).fetchone()
 if not row:raise HTTPException(404,'트랙을 찾을 수 없습니다.')
 p=Path(row['path'])
 if not p.is_file():raise HTTPException(404,'음원 파일이 없습니다.')
 return FileResponse(p,media_type='audio/wav',filename=p.name,content_disposition_type='inline')

@app.get('/')
def home():return FileResponse(ROOT/'static'/'index.html')
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
