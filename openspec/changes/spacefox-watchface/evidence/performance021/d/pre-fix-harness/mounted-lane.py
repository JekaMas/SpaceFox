import hashlib,json,pathlib,shutil,subprocess,time
from tools.run_native_tests import parse_output
root=pathlib.Path.cwd();out=pathlib.Path('/Users/jekamas/.codex/tmp/spacefox-performance021-d-mounted');tmp=pathlib.Path(subprocess.check_output(['getconf','DARWIN_USER_TEMP_DIR'],text=True).strip());runtime=tmp/'com.garmin.connectiq';saved=tmp/'com.garmin.connectiq.performance021-original';guard=tmp/'spacefox-performance021-lease';ini=pathlib.Path.home()/'Library/Application Support/Garmin/ConnectIQ/simulator.ini';sdk=pathlib.Path.home()/'Library/Application Support/Garmin/ConnectIQ/Sdks/connectiq-sdk-mac-9.3.0-2026-10-20-95888f262/bin';raw=subprocess.check_output(['ps','-axo','pid=,command='],text=True)
if any('ConnectIQ.app/Contents/MacOS/simulator' in x and 'python' not in x for x in raw.splitlines()):raise SystemExit('Garmin simulator already active; lane refused')
if saved.exists():raise SystemExit('saved runtime already exists; lane refused')
guard.mkdir();ini_data=ini.read_bytes();h=lambda p:{str(x.relative_to(p)):hashlib.sha256(x.read_bytes()).hexdigest() for x in p.rglob('*') if x.is_file()};before=h(runtime);sim=child=None
try:
 runtime.rename(saved);runtime.mkdir();(runtime/'GARMIN/APPS/MEDIA').mkdir(parents=True);sim=subprocess.Popen([str(sdk/'ConnectIQ.app/Contents/MacOS/simulator')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(5)
 common=['/opt/homebrew/opt/openjdk@11/bin/java','-Dfile.encoding=UTF-8','-classpath',str(sdk/'monkeybrains.jar'),'com.garmin.monkeybrains.monkeydodeux.MonkeyDoDeux'];base=pathlib.Path('/Users/jekamas/.codex/tmp/spacefox-performance021-baseline');seed=common+['-f',str(base/'seed/SpaceFoxRolloverStock.prg'),'-d','venux1','-s',str(sdk/'shell'),'-t'];p=subprocess.run(seed,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=120);(out/'seed.log').write_text(p.stdout);result=parse_output(p.stdout,p.returncode,('motionSeed',));print('SEED',json.dumps(result),flush=True)
 if result['status']!='passed':raise RuntimeError('seed failed; stock not started')
 files=['GARMIN/APPS/SETTINGS/SPACEFOXROLLOVERSTOCK.SET','GARMIN/APPS/DATA/SPACEFOXROLLOVERSTOCK.DAT','GARMIN/APPS/DATA/SPACEFOXROLLOVERSTOCK.IDX'];gate={x:hashlib.sha256((runtime/x).read_bytes()).hexdigest() for x in files};(out/'seed-gate.json').write_text(json.dumps(gate,indent=2)+'\n')
 snapshot=out/'seed-runtime';shutil.copytree(runtime,snapshot);fixture=snapshot/'GARMIN/APPS';log=(out/'identity.log').open('w');cmd=common+['-f','/Users/jekamas/.codex/tmp/spacefox-performance021-d-stock-identity/SpaceFoxRolloverStock.prg','-d','venux1','-s',str(sdk/'shell')]
 for rel in ['DATA/SPACEFOXROLLOVERSTOCK.DAT','DATA/SPACEFOXROLLOVERSTOCK.IDX','SETTINGS/SPACEFOXROLLOVERSTOCK.SET']:
  cmd+=['-a',str(fixture/rel)+':GARMIN/APPS/'+rel]
 child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);print('DIAGNOSTIC_ACTIVE simulator_pid',sim.pid,'launcher_pid',child.pid,flush=True)
 try:code=child.wait(timeout=90);print('DIAGNOSTIC_EXIT',code,flush=True)
 except subprocess.TimeoutExpired:print('DIAGNOSTIC_TIMEOUT',flush=True)

except KeyboardInterrupt:print('LANE_STOP',flush=True)
finally:
 for p in (child,sim):
  if p and p.poll() is None:
   p.terminate()
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:p.kill();p.wait()
 if saved.exists():
  if runtime.exists():shutil.rmtree(runtime)
  saved.rename(runtime)
 ini.write_bytes(ini_data);after=h(runtime);(out/'restore.json').write_text(json.dumps({'files':len(before),'restored':before==after,'ini':ini.read_bytes()==ini_data,'ownedExit':sim.returncode if sim else None},indent=2)+'\n');guard.rmdir();print('RESTORED',before==after,ini.read_bytes()==ini_data,flush=True)
