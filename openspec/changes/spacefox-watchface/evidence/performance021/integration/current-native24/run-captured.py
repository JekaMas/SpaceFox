import hashlib,json,os,pathlib,shutil,signal,subprocess,sys,time
sys.path.insert(0,os.getcwd())
from tools.run_native_tests import parse_output
from tools.native_b1_021_qualification import COMBINED,PEER_REPAIR
root=pathlib.Path.cwd(); out=pathlib.Path('/Users/jekamas/.codex/tmp/spacefox-performance024-captured-run');sdk=pathlib.Path('/Users/jekamas/Library/Application Support/Garmin/ConnectIQ/Sdks/connectiq-sdk-mac-9.3.0-2026-10-20-95888f262/bin');tmp=pathlib.Path(subprocess.check_output(['getconf','DARWIN_USER_TEMP_DIR'],text=True).strip());runtime=tmp/'com.garmin.connectiq';saved=tmp/'com.garmin.connectiq.performance024-original';guard=tmp/'spacefox-performance024-lease';ini=pathlib.Path.home()/'Library/Application Support/Garmin/ConnectIQ/simulator.ini';raw=subprocess.check_output(['ps','-axo','pid=,command='],text=True)
if any('ConnectIQ.app/Contents/MacOS/simulator' in x and 'python' not in x for x in raw.splitlines()) or saved.exists():raise SystemExit('simulator occupied')
out.mkdir(exist_ok=False)
COMBINED=['b1CapturedSuccessorTicksInFallback'];PEER_REPAIR=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest(); tree=lambda p:{str(x.relative_to(p)):sha(x) for x in p.rglob('*') if x.is_file()}; before=tree(runtime);ini_before=ini.read_bytes();guard.mkdir();pid=None;rows=[]
try:
 runtime.rename(saved);runtime.mkdir();(runtime/'GARMIN/APPS/MEDIA').mkdir(parents=True);app=sdk/'ConnectIQ.app';exe=str(app/'Contents/MacOS/simulator')
 launch=subprocess.run(['open','-n','--stdout',str(out/'sim.stdout'),'--stderr',str(out/'sim.stderr'),'-a',str(app)],capture_output=True,text=True,timeout=15);assert launch.returncode==0
 limit=time.monotonic()+30
 while time.monotonic()<limit:
  raw=subprocess.check_output(['ps','-axo','pid=,command='],text=True);matches=[int(x.strip().split(None,1)[0]) for x in raw.splitlines() if x.strip().split(None,1)[-1]==exe]
  if len(matches)==1:
   listener=subprocess.run(['lsof','-nP','-iTCP:1234','-sTCP:LISTEN','-t'],capture_output=True,text=True,timeout=5)
   if listener.stdout.strip()==str(matches[0]):pid=matches[0];break
  time.sleep(.25)
 if pid is None:raise RuntimeError('owned listener unavailable')
 print('OWNER',pid,flush=True)
 common=['/opt/homebrew/opt/openjdk@11/bin/java','-Dapple.awt.UIElement=true','-Dfile.encoding=UTF-8','-classpath',str(sdk/'monkeybrains.jar'),'com.garmin.monkeybrains.monkeydodeux.MonkeyDoDeux','-f','/Users/jekamas/.codex/tmp/spacefox-performance024-peer-compile/peer024.prg','-d','fr165','-s',str(sdk/'shell'),'-t']
 for name in dict.fromkeys(COMBINED+PEER_REPAIR):
  path=out/(name+'.log');start=time.monotonic()
  try:
   with path.open('w') as log:r=subprocess.run(common+[name],stdout=log,stderr=subprocess.STDOUT,timeout=120)
   result=parse_output(path.read_text(),r.returncode,(name,));result['seconds']=round(time.monotonic()-start,3)
  except subprocess.TimeoutExpired:result={'status':'timeout','seconds':round(time.monotonic()-start,3)}
  rows.append({'name':name,**result});print(name,result['status'],flush=True)
  (out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
finally:
 if pid is not None:
  try:os.kill(pid,signal.SIGTERM)
  except ProcessLookupError:pass
  deadline=time.monotonic()+10
  while time.monotonic()<deadline:
   try:os.kill(pid,0)
   except ProcessLookupError:break
   time.sleep(.1)
  else:os.kill(pid,signal.SIGKILL)
 if saved.exists():
  if runtime.exists():shutil.rmtree(runtime)
  saved.rename(runtime)
 ini.write_bytes(ini_before);(out/'restore.json').write_text(json.dumps({'files':len(before),'restored':before==tree(runtime),'ini':ini.read_bytes()==ini_before},indent=2)+'\n');guard.rmdir();print('RESTORED',before==tree(runtime),ini.read_bytes()==ini_before,flush=True)
