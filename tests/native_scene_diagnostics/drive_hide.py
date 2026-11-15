import os,subprocess,time
from pathlib import Path
p=Path('/task/output/ru-draw-hide/run.log');env=dict(os.environ,DISPLAY=':97');end=time.monotonic()+40
while time.monotonic()<end:
 if p.exists() and 'buildTimer=true build=true' in p.read_text(errors='replace'):
  subprocess.run(['python3','/task/xclick.py','72','12'],env=env,check=True);subprocess.run(['python3','/task/xclick.py','110','1013'],env=env,check=True);print('UI_FORCE_ONHIDE after in-flight build',flush=True);break
 time.sleep(.05)
else:print('UI_FAILED no build',flush=True)
