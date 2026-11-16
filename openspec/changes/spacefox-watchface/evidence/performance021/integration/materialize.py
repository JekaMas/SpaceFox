import json,os,subprocess,sys,tempfile
from pathlib import Path
from tools.release import source_state
root=Path.cwd();state=source_state(root)
with tempfile.TemporaryDirectory(prefix='spacefox-022-export-') as td:
 out=Path(td)
 for name in state['inputs']:
  dst=out/name;dst.parent.mkdir(parents=True,exist_ok=True);os.link(root/name,dst)
 code='import json;from pathlib import Path;from tools.native_language_policy import software_locales;print(json.dumps(software_locales(Path.cwd())))'
 p=subprocess.run([sys.executable,'-B','-c',code],cwd=out,env={**os.environ,'PYTHONPATH':str(out)},capture_output=True,text=True,timeout=600)
 if p.returncode: print(p.stderr);raise SystemExit(p.returncode)
 print(json.dumps({'revision':state['revision'],'tracked_release_inputs':len(state['inputs']),'materialized_locale_admission':json.loads(p.stdout)}))
