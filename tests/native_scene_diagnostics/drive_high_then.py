import os,subprocess,time,sys
from pathlib import Path
p=Path('/task/output/life-observe/inflight.log');env=dict(os.environ,DISPLAY=':97');offset=p.stat().st_size

def click(x,y):subprocess.run(['python3','/task/xclick.py',str(x),str(y)],env=env,check=True)
def move(x,y):subprocess.run(['python3','/task/xmove.py',str(x),str(y)],env=env,check=True)
def mode(y):
 click(72,12);move(295,964);time.sleep(.65);click(375,y)
mode(963)
end=time.monotonic()+15
while time.monotonic()<end:
 if 'buildTimer=true build=true' in p.read_text(errors='replace')[offset:]:
  if sys.argv[1]=='off':mode(1013)
  else:click(72,12);click(110,1013)
  print('UI_ACTUAL_'+sys.argv[1].upper()+' after build observed',flush=True);break
 time.sleep(.05)
else:print('UI_FAILED no restarted build marker',flush=True)
