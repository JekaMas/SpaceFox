import os,subprocess,time
from pathlib import Path
p=Path('/task/output/life-observe/inflight.log');env=dict(os.environ,DISPLAY=':97')
end=time.monotonic()+35
while time.monotonic()<end:
 if p.exists() and 'buildTimer=true build=true' in p.read_text(errors='replace'):
  subprocess.run(['python3','/task/xclick.py','72','12'],env=env,check=True)
  subprocess.run(['python3','/task/xmove.py','295','964'],env=env,check=True)
  time.sleep(.65)
  subprocess.run(['python3','/task/xclick.py','375','988'],env=env,check=True)
  print('UI_ACTUAL_LOW after build observed',flush=True);break
 time.sleep(.05)
else: print('UI_FAILED no in-flight marker',flush=True)
