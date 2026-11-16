"""Generate authenticated combined-source proof only after staged source freeze."""
import hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root))
from tools.native_performance021_qualification import REQUIRED_CURRENT
from tools.native_b1_021_qualification import OWNERS,COMBINED,PEER_REPAIR
from tools.native_integration022_qualification import watch_inputs
base=Path('openspec/changes/spacefox-watchface/evidence/performance021/integration');obj=base/'objects';obj.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
def git(*a):return subprocess.check_output(['git',*a])
def tree(rev):
 out={}
 for row in git('ls-tree','-r','-z',rev).split(b'\0'):
  if not row:continue
  meta,path=row.split(b'\t',1);mode,kind,oid=meta.split();
  if kind==b'blob':out[path.decode()]=(mode.decode(),oid.decode())
 return out
candidate=tree(':') if False else None
# Index is the concrete merged source. Snapshot only differing parent blobs;
# paths added on this branch are removed in the isolated historical tree.
rows=git('ls-files','--stage','-z').split(b'\0');index={}
for row in rows:
 if not row:continue
 meta,path=row.split(b'\t',1);mode,oid,stage=meta.split();assert stage==b'0';index[path.decode()]=(mode.decode(),oid.decode())
roots=('tools/','watchface/','locales/','openspec/','tests/','assets/','corpus/','catalog/','schemas/','docs/','release/','prototype/','.github/','licenses/')
parents={'performance':'f955c6022ddabeb0153b71006ae1fa4bba4ad179','runtime':'c410eb4e5d86bbbe28d100996abf6bf5beb0607d'}
recipes={}; needed={}
for side,rev in parents.items():
 old=tree(rev); paths={n for n in set(index)|set(old) if (n.startswith(roots) or '/' not in n) and not n.startswith(str(base)+'/')};changed=[n for n in paths if index.get(n)!=old.get(n)]
 restore={};remove=[]
 for name in sorted(changed):
  if name not in old:remove.append(name);continue
  mode,oid=old[name]
  if mode not in ('100644','100755'):raise ValueError('unsupported historical path '+name)
  needed[oid]=None;restore[name]=oid
 recipes[side]={'revision':rev,'restore':restore,'remove':remove}
proc=subprocess.Popen(['git','cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
for oid in needed:
 proc.stdin.write((oid+'\n').encode());proc.stdin.flush();hdr=proc.stdout.readline().decode().split();assert hdr[0]==oid and hdr[1]=='blob';size=int(hdr[2]);data=proc.stdout.read(size);assert len(data)==size and proc.stdout.read(1)==b'\n';digest=sha(data);path=obj/digest
 if not path.exists():path.write_bytes(data)
 needed[oid]={'path':path.as_posix(),'sha256':digest}
proc.stdin.close();assert proc.wait()==0
for recipe in recipes.values():recipe['restore']={n:needed[o] for n,o in recipe['restore'].items()}
manifest=Path('release/native-admission-inputs.json');inputs=set(json.loads(manifest.read_text()));inputs.update(v['path'] for v in needed.values());inputs.update(str(p) for p in (base/'b1-native').glob('*.log'));evidence_files={'b1Results':'b1-native/results.json','b1Restore':'b1-native/restore.json','batchLinear':'batch-integrationBatchLinearAndTerminal.log','batchCorruption':'batch-final-integrationBatchCorruptPrefixBeforeCompletion.log','batchRestore':'batch-restore.json','scene':'suites-scene.log','fields':'suites-fields.log','incidentFirst':'incident-first-red.log','incidentRepairPrefix':'incident-repair-deliveryBatchPrefixLifetime.log','incidentRepairFragments':'incident-repair-deliveryProvisionalFragmentCleanup.log','display':'display-native.log','b1Build':'b1-native/build-inputs.json','b1RepairBuild':'b1-native/repair-build-inputs.json','b1StopBuild':'b1-native/stop-build-inputs.json','b1Program':'b1-native/combined.prg.gz','b1RepairProgram':'b1-native/repaired.prg.gz','b1StopProgram':'b1-native/stop.prg.gz','batchSource':'IntegrationBatchTests.mc','batchBuild':'batch-build.json','batchProgram':'batch-program.prg.gz','batchFinalBuild':'batch-final-build.json','batchFinalProgram':'batch-final-program.prg.gz','b1StopRestore':'b1-native/stop-restore.json','incidentFinalProjection':'incident-final-deliveryRawProjectionIntegrity.log','incidentFinalStop':'incident-stop-final-deliveryOwnerStopReleasesCycle.log'}
inputs.update(str(base/name) for name in evidence_files.values());inputs.add(str(base/'integration-proof.json'));
def replace(path,data):
 fd,n=tempfile.mkstemp(dir=path.parent,prefix='.'+path.name+'.');os.write(fd,data);os.close(fd);os.replace(n,path)
replace(manifest,(json.dumps(sorted(inputs),indent=2)+'\n').encode())
owners=set(REQUIRED_CURRENT)|set(OWNERS)|{'tools/native_integration022_qualification.py','tools/native_language_policy.py','tools/build_native_resources.py','tools/native_display03_probe.py','tools/fields018_native_probe.py','tools/native_other_batch.py'}
ownerhash={n:sha(Path(n).read_bytes()) for n in sorted(owners)}
rows=json.loads((base/'b1-native/results.json').read_text());byname={x['name']:x for x in rows};assert set(byname)==set(COMBINED+PEER_REPAIR+['b1TailCleanupRechecksOwnership','b1OwnerStopReleasesPendingWork']) and all(x['status']=='passed' for x in rows)
native={}
for name,r in byname.items():
 path=base/'b1-native'/(name+'.log');native[name]={'path':path.as_posix(),'sha256':sha(path.read_bytes()),'rawExit':r['raw_exit_code']}
catalog=json.loads(Path('locales/catalog.json').read_text());catalog['supportPolicy']['softwareQualificationProof'].pop('integration022Proof',None);catalog_hash=sha(json.dumps(catalog,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
record={'scope':'performance021-b1-current-source-022','version':'0.1.22','catalogWithoutIntegrationSha256':catalog_hash,'watchInputs':watch_inputs(root),'owners':ownerhash,'historical':recipes,'b1Native':native,'evidence':{k:{'path':str(base/v),'sha256':sha((base/v).read_bytes())} for k,v in evidence_files.items()}}
proof=base/'integration-proof.json';replace(proof,(json.dumps(record,indent=2,ensure_ascii=False,sort_keys=True)+'\n').encode());data=json.loads(Path('locales/catalog.json').read_text());data['supportPolicy']['softwareQualificationProof']['integration022Proof']={'path':proof.as_posix(),'sha256':sha(proof.read_bytes())};replace(Path('locales/catalog.json'),(json.dumps(data,indent=2,ensure_ascii=False)+'\n').encode());print('snapshot blobs',len(needed),'recipes',[(k,len(v['restore']),len(v['remove'])) for k,v in recipes.items()],'owners',len(owners),'watch',len(record['watchInputs']))
