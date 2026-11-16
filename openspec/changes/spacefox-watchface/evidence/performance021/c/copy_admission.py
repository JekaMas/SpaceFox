import collections,hashlib,json,os,shutil,sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path.cwd()))
from tools.release import source_state,validate_snapshot_inputs,ReleaseBlocked
from tools.native_language_policy import software_locales
root=Path.cwd();before=source_state(root);report={'revision':before['revision'],'selected':len(before['inputs']),'inputs':before['inputs'],'nativeUnchanged':True}
with tempfile.TemporaryDirectory(prefix='spacefox-c-release-copy-') as temp:
 copied=Path(temp)
 for name,expected in before['inputs'].items():
  dst=copied/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,dst)
  assert hashlib.sha256(dst.read_bytes()).hexdigest()==expected
 report['qualified']=software_locales(copied,json.loads((copied/'locales/catalog.json').read_text()))
 # Generated selectors are real copied current manifest/jungle bytes, not a new
 # compile claim. Exercise unchanged full inventories twice, then changed bytes.
 generated={copied/'manifest.xml':(copied/'watchface/manifest.xml').read_bytes(),copied/'monkey.jungle':(copied/'watchface/monkey.jungle').read_bytes()}
 for p,data in generated.items():p.write_bytes(data)
 hashes={p:hashlib.sha256(data).hexdigest() for p,data in generated.items()}
 reader=Path.read_bytes;counts=collections.Counter();total=[0]
 def count(p):
  data=reader(p);counts[p]+=1;total[0]+=len(data);return data
 start=time.monotonic()
 with patch.object(Path,'read_bytes',count):
  validate_snapshot_inputs(copied,before['inputs'],hashes)
  validate_snapshot_inputs(copied,before['inputs'],hashes)
 report['twoFreshSnapshotFences']={'reads':sum(counts.values()),'bytes':total[0],'uniqueFiles':len(counts),'allReadTwice':set(counts.values())=={2},'seconds':time.monotonic()-start}
 assert report['twoFreshSnapshotFences']['allReadTwice']
 p=copied/'watchface/source/SpaceFoxView.mc';data=p.read_bytes();old=p.stat();p.write_bytes(bytes([data[0]^1])+data[1:]);os.utime(p,ns=(old.st_atime_ns,old.st_mtime_ns))
 try:validate_snapshot_inputs(copied,before['inputs'],hashes)
 except ReleaseBlocked as exc:report['sameSizeMtimeMutationRefused']=str(exc)
 else:raise AssertionError('full copied snapshot mutation admitted')
 assert source_state(root)==before
print(json.dumps(report,indent=2))
