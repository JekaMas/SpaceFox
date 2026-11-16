import os,subprocess,time,socket,hashlib
from pathlib import Path
sdk='/task/garmin/Sdks/connectiq-sdk-lin-9.3.0-2026-10-20-95888f262/bin/';env=dict(os.environ,DISPLAY=':91');env.pop('JAVA_TOOL_OPTIONS',None)
log=open('/task/pair-simulator.log','w');sim=subprocess.Popen([sdk+'simulator'],env=env,stdout=log,stderr=subprocess.STDOUT)
try:
 for i in range(100):
  if sim.poll() is not None:raise RuntimeError('owned simulator exited')
  try:
   with socket.create_connection(('127.0.0.1',1234),timeout=.1):break
  except OSError:time.sleep(.1)
 else:raise RuntimeError('simulator unavailable')
 data=Path('/tmp/com.garmin.connectiq/GARMIN/APPS/DATA');print('DATA_BEFORE_SEED',sorted(p.name for p in data.glob('SINGLE.*')),flush=True)
 program=Path('/task/single.prg');before=hashlib.sha256(program.read_bytes()).hexdigest(); print('PROGRAM_SHA256',before,flush=True)
 seed=subprocess.run([sdk+'monkeydo','/task/single.prg','fr165m','-t','seedCapturedPair'],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=120);Path('/task/pair-seed.log').write_text(seed.stdout)
 if 'PASSED (passed=1, failed=0, errors=0)' not in seed.stdout:raise RuntimeError('seed failed')
 data=Path('/tmp/com.garmin.connectiq/GARMIN/APPS/DATA');print('DATA_AFTER_SEED',sorted(p.name for p in data.glob('SINGLE.*')),flush=True)
 if hashlib.sha256(program.read_bytes()).hexdigest()!=before:raise RuntimeError('program changed between phases')
 with open('/task/pair-app.log','w') as output:
  app=subprocess.Popen([sdk+'monkeydo','/task/single.prg','fr165m'],env=env,stdout=output,stderr=subprocess.STDOUT)
  try:
   completedAt=None
   for i in range(210):
    time.sleep(1);data=Path('/task/pair-app.log').read_text()
    if 'REAL_REPLACEMENT visual_complete=true' in data and completedAt is None:completedAt=i;print('PAIR_COMPLETE_OBSERVED',flush=True)
    if completedAt is not None and i-completedAt>=30:print('PAIR_COMPLETE_STABLE_30S',flush=True);break
    if app.poll() is not None:print('APP_EXIT',app.returncode,flush=True);break
   else:print('PAIR_TIMEOUT',flush=True)
  finally:
   if app.poll() is None:app.terminate();app.wait(timeout=5)
finally:
 sim.terminate()
 try:sim.wait(timeout=5)
 except subprocess.TimeoutExpired:sim.kill();sim.wait()
 log.close()
