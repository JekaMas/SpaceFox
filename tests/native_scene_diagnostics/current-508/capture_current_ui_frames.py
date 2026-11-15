import subprocess,time,re,sys
from pathlib import Path
base=Path(sys.argv[1]).resolve()
container=sys.argv[2]
cmd=['docker','exec','-e','DISPLAY=:97',container,'sh','-c','env -u JAVA_TOOL_OPTIONS timeout 40 /task/garmin/Sdks/connectiq-sdk-lin-9.3.0-2026-10-20-95888f262/bin/monkeydo /task/output/ui-frames/UIF.prg fr165']
p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1);seen=set();rows=[]
for line in p.stdout:
 rows.append(line);print(line,end='',flush=True)
 key='en' if line.strip()=='UI_ACTIVE_EN' else 'ru' if line.strip()=='UI_ACTIVE_RU' else None
 match=re.search(r'UI_AOD phase=(\d+) ',line)
 if match:key='aod-'+match.group(1)
 if key and key not in seen:
  time.sleep(.4);subprocess.run(['docker','exec','-e','DISPLAY=:97',container,'python3','/task/capture_full.py','/task/output/ui-frames/'+key+'.ppm'],check=True);seen.add(key)
 if 'UI_AOD_COMPLETE phases=4' in line:break
(base/'runtime.log').write_text(''.join(rows));p.terminate();code=p.wait(timeout=5);(base/'launcher.txt').write_text('observer terminated after complete marker; host exit '+str(code)+'\n');print('CAPTURED',sorted(seen),flush=True)
