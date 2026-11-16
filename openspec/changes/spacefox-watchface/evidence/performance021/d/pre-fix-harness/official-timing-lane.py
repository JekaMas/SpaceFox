#!/usr/bin/env python3
"""Single owned simulator stock lane; UI must claim and release its bounded lease."""
import argparse, hashlib, json, os, pathlib, re, secrets, shutil, signal, subprocess, time
from PIL import Image
from tools.run_native_tests import parse_output

p=argparse.ArgumentParser()
p.add_argument('--out',type=pathlib.Path,required=True)
p.add_argument('--seed',type=pathlib.Path,required=True)
p.add_argument('--program',type=pathlib.Path,required=True)
p.add_argument('--program-sha',required=True)
p.add_argument('--fixture-validated-utc',type=int,required=True)
p.add_argument('--observe-seconds',type=int,default=120)
a=p.parse_args(); out=a.out.resolve(); out.mkdir(parents=True,exist_ok=False)
seed=a.seed.resolve(); program=a.program.resolve(); debug=pathlib.Path(str(program)+'.debug.xml')
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
if sha(program)!=a.program_sha:raise SystemExit('unexpected stock PRG')
token=secrets.token_hex(16);sdk=pathlib.Path.home()/'Library/Application Support/Garmin/ConnectIQ/Sdks/connectiq-sdk-mac-9.3.0-2026-10-20-95888f262/bin'
tmp=pathlib.Path(subprocess.check_output(['getconf','DARWIN_USER_TEMP_DIR'],text=True).strip());runtime=tmp/'com.garmin.connectiq';saved=tmp/'com.garmin.connectiq.performance021-original';guard=tmp/'spacefox-performance021-lease';ini=pathlib.Path.home()/'Library/Application Support/Garmin/ConnectIQ/simulator.ini'
raw=subprocess.check_output(['ps','-axo','pid=,command='],text=True)
if any('ConnectIQ.app/Contents/MacOS/simulator' in x and 'python' not in x for x in raw.splitlines()):raise SystemExit('Garmin simulator active; refusing lane')
if saved.exists():raise SystemExit('saved runtime exists; refusing lane')
guard.mkdir(); ini_data=ini.read_bytes(); h=lambda path:{str(x.relative_to(path)):sha(x) for x in path.rglob('*') if x.is_file()}; before=h(runtime);sim=child=None;log=None

class OwnedSimulator:
 def __init__(self,pid,executable):self.pid=pid;self.executable=executable;self.returncode=None
 def poll(self):
  run=subprocess.run(['ps','-p',str(self.pid),'-o','command='],capture_output=True,text=True,timeout=5)
  return None if run.returncode==0 and run.stdout.strip()==self.executable else self.returncode if self.returncode is not None else -1
 def terminate(self):
  if self.poll() is None:os.kill(self.pid,signal.SIGTERM)
 def kill(self):
  if self.poll() is None:os.kill(self.pid,signal.SIGKILL)
 def wait(self,timeout):
  deadline=time.monotonic()+timeout
  while time.monotonic()<deadline:
   if self.poll() is not None:self.returncode=-15;return self.returncode
   time.sleep(.1)
  raise subprocess.TimeoutExpired('owned simulator',timeout)

def status():
 if sim.poll() is not None:raise RuntimeError('owned simulator exited')
 if child and child.poll() is not None:raise RuntimeError('stock launcher exited')

def ack(name,limit):
 path=out/name
 while time.monotonic()<limit:
  status()
  if path.exists():
   row=json.loads(path.read_text())
   if row.get('token')!=token or row.get('simulatorPid')!=sim.pid:raise RuntimeError('invalid UI acknowledgement')
   return row
  time.sleep(.25)
 raise TimeoutError('UI lease expired waiting for '+name)
try:
 runtime.rename(saved);runtime.mkdir();(runtime/'GARMIN/APPS/MEDIA').mkdir(parents=True)
 app=sdk/'ConnectIQ.app';executable=str(app/'Contents/MacOS/simulator')
 subprocess.run(['open','-a',str(app)],check=True,timeout=15)
 launch_limit=time.monotonic()+20
 while time.monotonic()<launch_limit:
  listing=subprocess.run(['ps','-axo','pid=,command='],capture_output=True,text=True,timeout=5,check=True).stdout
  matches=[int(line.strip().split(None,1)[0]) for line in listing.splitlines() if line.strip().split(None,1)[-1]==executable]
  if len(matches)==1:
   sim=OwnedSimulator(matches[0],executable)
   listener=subprocess.run(['lsof','-nP','-iTCP:1234','-sTCP:LISTEN','-t'],capture_output=True,text=True,timeout=5)
   if listener.returncode==0 and listener.stdout.strip()==str(sim.pid):break
  elif len(matches)>1:raise RuntimeError('ambiguous simulator processes')
  time.sleep(.25)
 else:raise TimeoutError('owned simulator listener not established')
 print('OFFICIAL_APP_OWNER',sim.pid,'tcp=1234',flush=True)
 common=['/opt/homebrew/opt/openjdk@11/bin/java','-Dfile.encoding=UTF-8','-classpath',str(sdk/'monkeybrains.jar'),'com.garmin.monkeybrains.monkeydodeux.MonkeyDoDeux']
 with (out/'seed.log').open('w') as f:
  result=subprocess.run(common+['-f',str(seed),'-d','venux1','-s',str(sdk/'shell'),'-t'],stdout=f,stderr=subprocess.STDOUT,timeout=120)
 seed_text=(out/'seed.log').read_text();receipt=parse_output(seed_text,result.returncode,('motionSeed',));print('SEED',json.dumps(receipt),flush=True)
 if receipt['status']!='passed':raise RuntimeError('seed failed')
 match=re.search(r'FUTURE_SEED now=(\d+) deadline=(\d+)',seed_text)
 if not match or 'objects=19' not in seed_text or 'SELECTED_ACTUAL_TYPES 4,5,6,8' not in seed_text:raise RuntimeError('fixture seed witness missing')
 seed_now=int(match.group(1));age=seed_now-a.fixture_validated_utc
 if age<0 or age+a.observe_seconds+240>=10800:raise RuntimeError('fixture freshness margin insufficient')
 rels=['DATA/SPACEFOXROLLOVERSTOCK.DAT','DATA/SPACEFOXROLLOVERSTOCK.IDX','SETTINGS/SPACEFOXROLLOVERSTOCK.SET'];snapshot=out/'seed-runtime';shutil.copytree(runtime,snapshot);fixture=snapshot/'GARMIN/APPS';seed_hashes={r:sha(fixture/r) for r in rels}
 cmd=common+['-f',str(program),'-d','venux1','-s',str(sdk/'shell')]
 for r in rels:cmd+=['-a',str(fixture/r)+':GARMIN/APPS/'+r]
 log=(out/'stock.log').open('w');start=time.monotonic();child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);media=runtime/'GARMIN/APPS/MEDIA/SPACEFOXROLLOVERSTOCK.PRG';loaded_debug=runtime/'GARMIN/Debug/SPACEFOXROLLOVERSTOCK.PRG.DEBUG.XML';install_deadline=start+180
 while time.monotonic()<install_deadline:
  status()
  if media.is_file() and media.stat().st_size==program.stat().st_size and loaded_debug.is_file() and sha(loaded_debug)==sha(debug):break
  time.sleep(.25)
 else:raise TimeoutError('stock binary gate timed out')
 gate=time.monotonic(); window=subprocess.run([str(pathlib.Path('/Users/jekamas/.codex/tmp/spacefox-performance021-timing-stock/window-id')),str(sim.pid)],capture_output=True,text=True,timeout=10,check=True).stdout.strip()
 if not window.isdigit():raise RuntimeError('owned window not found')
 lease=time.monotonic()+240; deadline_epoch=time.time()+240
 ready={'token':token,'simulatorPid':sim.pid,'launcherPid':child.pid,'windowId':window,'leaseDeadlineUnix':deadline_epoch,'seedSha256':sha(seed),'stockSha256':sha(program),'debugSha256':sha(debug),'gateAfterLaunchSeconds':gate-start,'fixtureValidatedUtc':a.fixture_validated_utc,'seedNow':seed_now,'seedAgeSeconds':age,'seedFilesSha256':seed_hashes}
 (out/'UI_READY.json').write_text(json.dumps(ready,indent=2)+'\n');print('UI_READY',json.dumps(ready),flush=True)
 claim=ack('UI_CLAIMED.json',lease);(out/'UI_GRANTED.json').write_text(json.dumps(ready,indent=2)+'\n');print('UI_GRANTED',flush=True)
 complete=ack('UI_COMPLETE.json',lease)
 if not complete.get('foregroundWitness'):raise RuntimeError('foreground witness missing')
 observation=time.monotonic();samples=[];deadline=observation+a.observe_seconds
 while time.monotonic()<deadline:
  status();index=len(samples);path=out/('frame-%03d.png'%index);b=time.monotonic();capture=subprocess.run(['screencapture','-l',window,'-x',str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10);end=time.monotonic()
  if capture.returncode:raise RuntimeError('capture failed')
  with Image.open(path) as image:image.verify()
  samples.append({'index':index,'fromLaunch':[b-start,end-start],'fromObservation':[b-observation,end-observation],'path':path.name,'sha256':sha(path)})
  (out/'samples.json').write_text(json.dumps(samples,indent=2)+'\n');time.sleep(2)
 print('OBSERVATION_DONE',len(samples),flush=True)

finally:
 for proc in (child,sim):
  if proc and proc.poll() is None:
   proc.terminate()
   try:proc.wait(timeout=10)
   except subprocess.TimeoutExpired:proc.kill();proc.wait()
 if log:log.close()
 if saved.exists():
  if runtime.exists():shutil.rmtree(runtime)
  saved.rename(runtime)
 ini.write_bytes(ini_data);after=h(runtime);(out/'restore.json').write_text(json.dumps({'files':len(before),'restored':before==after,'ini':ini.read_bytes()==ini_data,'ownedExit':sim.returncode if sim else None},indent=2)+'\n');guard.rmdir();print('RESTORED',before==after,ini.read_bytes()==ini_data,flush=True)
