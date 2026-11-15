"""Source-bound DISPLAY04 locale admission over the immutable .13 chain.

The historical proof is reconstructed exactly, then current native/UI evidence
is validated against the changed source. This is software qualification only.
"""
import ast,base64,hashlib,json,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path

def sha(data):return hashlib.sha256(data).hexdigest()
HOST_MODULES=('tests.test_display04_aod_outline','tests.test_display04_native_mask_pixels',
              'tests.test_display04_ready_mask_pixels','tests.test_display04_conditional_pixels',
              'tests.test_display04_preclip_evidence')
# Every file in these immutable evidence directories was an input to the
# source-bound composed-mask, trace or direct-font checks. Fixing an input
# requires an actual renewed observation, not a rewritten historical receipt.
EVIDENCE_DIRS=(
 'mask-active-en390','mask-active-ru454','mask-active-ru454-target33','mask-low-ru454',
 'trace-pending-390','trace-pending-454','scale-view-454','font-trace-390-corrected',
 'bitmap-trace-390','bitmap-trace-454','subset-ru390','subset-en454',
 'low-en390','low-en390-map','low-ru390-date','low-en454-date','low-ru390-battery','low-en454-battery',
 'ready-mask-en390','ready-mask-en454','ready-trace-390','ready-trace-454',
 'ready-asset-trace-390','ready-asset-trace-454','ready-low-trace-fixed-390','ready-low-trace-fixed-454',
 'ready-low-en390','ready-low-en390-clockdate','ready-low-en454-all','ready-low-ru390-datebattery','ready-low-ru454-datebattery',
 'conditional-390','conditional-454','low-dimensions-390','low-dimensions-454',
 'retained-primary-date','battery-metrics-size51','preclip-fields/viewport-green','clock-cases-454','pending-point-current')
SUPPORT=(
 'tools/native_display04_requalification.py','tools/generate_native_display04_proof.py','tools/native_language_policy.py','tools/native_element_masks.py',
 'tools/native_element_isolation.py','tools/native_display04_mask_probe.py','tools/run_native_tests.py',
 'tests/test_display04_pending_pixels.py','tests/test_display04_operation_trace.py',
 'tests/test_display04_aod_outline.py','tests/test_display04_native_mask_pixels.py',
 'tests/test_display04_ready_mask_pixels.py','tests/test_display04_conditional_pixels.py',
 'tests/test_display04_preclip_evidence.py','prototype/fonts/RobotoCondensed-latin-600.woff2')

def support_inputs(root):
 root=Path(root);result={name:sha((root/name).read_bytes()) for name in SUPPORT}
 for directory in sorted((root/'tests/fixtures').glob('display04_*')):
  if directory.is_dir():
   for path in sorted(directory.rglob('*')):
    if path.is_file():result[path.relative_to(root).as_posix()]=sha(path.read_bytes())
 return result

def current_fields_inputs(root):
 root=Path(root);watch=root/'watchface';paths=list((watch/'source').rglob('*.mc'))
 paths += [p for p in (watch/'resources').rglob('*') if p.is_file()]
 paths += [p for d in root.glob('watchface/resources-*') for p in d.rglob('*') if p.is_file()]
 paths += [watch/'manifest.xml',watch/'toolchain-lock.json',watch/'current-fields-tests/FieldsTests.mc',root/'tests/fixtures/watch_refresh_cache/packets.json']
 return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in sorted(paths) if p.is_file()}

def evidence_inputs(root):
 base=Path(root)/'openspec/changes/spacefox-watchface/evidence/display04-whole-quality';result={}
 for name in EVIDENCE_DIRS:
  directory=base/name
  if not directory.is_dir():raise ValueError('DISPLAY04 evidence directory absent: '+name)
  for path in sorted(directory.rglob('*')):
   if path.is_file():result[path.relative_to(root).as_posix()]=sha(path.read_bytes())
 return result
# Process-local reuse only after hashing all bytes the isolated historical
# validators can read. Any file addition, deletion, or byte mutation changes
# the key; no success is cached across roots or processes.
_PRIOR_VALIDATED=set()
def prior_cache_key(root,record,read):
 root=Path(root);digest=hashlib.sha256();digest.update(str(root).encode()+b'\0')
 for name,item in sorted(record['priorSnapshots'].items()):
  digest.update(name.encode()+b'\0'+hashlib.sha256(read(item)).digest())
 digest.update(hashlib.sha256(read(record['priorCatalog'])).digest())
 excluded=Path('openspec/changes/spacefox-watchface/evidence/display04-whole-quality')
 for folder in ('watchface','locales','tools','tests','corpus','assets','catalog','schemas','openspec'):
  base=root/folder
  for path in sorted(base.rglob('*')):
   if not path.is_file() or '__pycache__' in path.parts or path.suffix=='.pyc':continue
   relative=path.relative_to(root)
   if relative==excluded or excluded in relative.parents:continue
   digest.update(relative.as_posix().encode()+b'\0'+hashlib.sha256(path.read_bytes()).digest())
 return digest.hexdigest()

def validate(root,catalog):
 from tools.generate_native_version import validate as validate_version
 from tools.native_display03_probe import inputs as native_inputs, NAMES as display_names
 from tools.run_native_tests import parse_output
 root=Path(root).resolve();proof=catalog['supportPolicy']['softwareQualificationProof']
 def read(item):
  name=Path(item['path'])
  if name.is_absolute() or '..' in name.parts:raise ValueError('invalid DISPLAY04 evidence path')
  raw=(root/name).read_bytes()
  if sha(raw)!=item['sha256']:raise ValueError('DISPLAY04 evidence changed: '+str(name))
  return base64.b64decode(raw,validate=True) if item.get('encoding')=='base64' else raw
 record=json.loads(read(proof['display04DeltaProof']))
 if record['scope']!='display04-current-primary-software':raise ValueError('unexpected DISPLAY04 qualification scope')
 prior=json.loads(read(record['priorCatalog']));priorproof=prior['supportPolicy']['softwareQualificationProof']
 if {k:v for k,v in proof.items() if k!='display04DeltaProof'}!=priorproof:raise ValueError('historical admission proof changed')
 comparable=json.loads(json.dumps(catalog));comparable['supportPolicy']['softwareQualificationProof']=priorproof
 if comparable!=prior:raise ValueError('catalog changed beyond current qualification proof')
 # Historical UI evidence remains a live part of the accepted prior proof.
 # Check it in this process too, so caller-side corruption hooks cannot be
 # bypassed by the isolated legacy subprocess.
 supplement=json.loads(read(priorproof['currentNativeUiDeltaProof']))
 for item in supplement['evidence'].values():read(item)
 if record['nativeInputs']!=native_inputs(root):raise ValueError('DISPLAY04 current native closure changed')
 if record['supportInputs']!=support_inputs(root):raise ValueError('DISPLAY04 support input or inventory changed')
 validate_version(root)
 # Current changed owners are covered by the original 24-case framework run,
 # exact reconstructed old input bytes, and the separate current guard case.
 evidence=record['nativeEvidence'];expected_full=tuple(display_names[:-1])
 for key,expected in (('display03',expected_full),('rocketGuard',(display_names[-1],)),('currentFields',tuple(record['fieldsTests']))):
  row=evidence[key];rec=json.loads(read(row['receipt']));raw=read(row['log']).decode();prg=read(row['program'])
  if sha(prg)!=rec['packageSha256']:raise ValueError('DISPLAY04 program differs: '+key)
  if parse_output(raw,rec['rawExit'],expected)['status']!='passed':raise ValueError('DISPLAY04 native framework failure: '+key)
  if key!='display03':
   pre=json.loads(read(row['precompile']))
   if pre['inputHashes']!=rec['inputHashes'] or pre['buildCommand']!=rec['buildCommand']:raise ValueError('DISPLAY04 precompile input mismatch: '+key)
   base=Path(row['receipt']['path']).parent
   for name,h in pre['generatedInputs'].items():
    if sha((root/base/name).read_bytes())!=h:raise ValueError('DISPLAY04 generated compile input differs: '+name)
  if key=='rocketGuard' and rec['inputHashes']!=record['nativeInputs']:raise ValueError('DISPLAY04 current guard closure incomplete')
  if key=='currentFields' and (rec['inputHashes']!=current_fields_inputs(root) or pre['probeSha256']!=sha((root/'tests/native_scene_diagnostics/current-508/current_fields_probe.py').read_bytes())):raise ValueError('DISPLAY04 fields closure incomplete')
  if key=='display03':
   old=rec['inputHashes'];now=record['nativeInputs'];delta={n for n in set(old)|set(now) if old.get(n)!=now.get(n)}
   expected_delta={'watchface/source/SceneRenderer.mc','watchface/source/NativeVisualRenderer.mc','watchface/source/generated/NativeVersion.mc','tools/native_display03_probe.py','watchface/display03-tests/InvisibleRocketTests.mc'}
   if delta!=expected_delta:raise ValueError('DISPLAY04 historical native delta differs')
   snapshots=record['display03HistoricalInputs']
   if set(snapshots)!=expected_delta-{'watchface/display03-tests/InvisibleRocketTests.mc'}:raise ValueError('DISPLAY04 old input inventory differs')
   for name,item in snapshots.items():
    if sha(read(item))!=old[name]:raise ValueError('DISPLAY04 old input does not match original receipt: '+name)
   # Only the center correction changed in SceneRenderer; all older lifecycle
   # assertions remain valid, while current ink is proved by the pixel batch.
   old_renderer=read(snapshots['watchface/source/SceneRenderer.mc']).decode();current=(root/'watchface/source/SceneRenderer.mc').read_text()
   old_comment='// then apply at most one pixel of minute-based burn-in movement.'
   new_comment=('// The glyph baseline stays fixed vertically: native 454px scaling adds a\n'
                '        // device-font offset that otherwise shifts the lower phases beyond\n'
                '        // the two-pixel center bound. Horizontal movement and the independent\n'
                '        // four-phase pixel-rest mask retain the minute-based burn-in pattern.')
   old_draw='dc.drawText(195+p[0]+correction,122+p[1],font,current.localTime,Graphics.TEXT_JUSTIFY_CENTER);'
   new_draw='dc.drawText(195+p[0]+correction,121,font,current.localTime,Graphics.TEXT_JUSTIFY_CENTER);'
   if old_renderer.count(old_comment)!=1 or old_renderer.count(old_draw)!=1 or old_renderer.replace(old_comment,new_comment).replace(old_draw,new_draw)!=current:raise ValueError('DISPLAY04 old renderer delta differs')
   old_visual=read(snapshots['watchface/source/NativeVisualRenderer.mc']).decode();visual=(root/'watchface/source/NativeVisualRenderer.mc').read_text()
   before='''        transform.setToTranslation((27-27*frameScale).toFloat(),(62-62*frameScale).toFloat());transform.scale(frameScale.toFloat(),frameScale.toFloat());
    }
    function draw(dc,progress,ascent){
        if(bitmap==null){return;}prepareFrame(progress,ascent);
        dc.setClip(22,118-ascent,54,124);dc.drawBitmap2(frameX,frameY,bitmap,drawOptions);dc.clearClip();
    }'''
   after='''    }
    // The source transform scales about the 54x124 frame center. Use the
    // union of translation-before/after-scale bounds and a pixel of rounding
    // margin: only frames that cannot intersect the intended clip are skipped.
    function frameIntersects(ascent){
        var tx=27.0-27.0*frameScale;var ty=62.0-62.0*frameScale;
        var sx=tx*frameScale;var sy=ty*frameScale;
        var left=frameX+(tx<sx?tx:sx)-1;var right=frameX+(tx>sx?tx:sx)+bitmap.getWidth()*frameScale+1;
        var top=frameY+(ty<sy?ty:sy)-1;var bottom=frameY+(ty>sy?ty:sy)+bitmap.getHeight()*frameScale+1;
        return right>22 && left<76 && bottom>118-ascent && top<242-ascent;
    }
    function draw(dc,progress,ascent){
        if(bitmap==null){return;}prepareFrame(progress,ascent);if(!frameIntersects(ascent)){return;}
        transform.setToTranslation((27-27*frameScale).toFloat(),(62-62*frameScale).toFloat());transform.scale(frameScale.toFloat(),frameScale.toFloat());
        dc.setClip(22,118-ascent,54,124);dc.drawBitmap2(frameX,frameY,bitmap,drawOptions);dc.clearClip();
    }'''
   if old_visual.count(before)!=1 or old_visual.replace(before,after)!=visual:raise ValueError('DISPLAY04 old rocket source delta differs')
   old_runner=read(snapshots['tools/native_display03_probe.py']).decode();current_runner=(root/'tools/native_display03_probe.py').read_text()
   old_build_call=";build=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(out/'compile.log').write_text(build.stdout)"
   new_build_call='''
 generated={str(q.relative_to(out)):sha(q) for q in [out/'manifest.xml',out/'probe.jungle',*sorted(out.glob('*.mc')),*sorted(res.glob('*'))]}
 (out/'precompile.json').write_text(json.dumps({'inputHashes':before,'generatedInputs':generated,'buildCommand':cmd},indent=2)+'\\n')
 build=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(out/'compile.log').write_text(build.stdout)
 if any(sha(out/n)!=digest for n,digest in generated.items()):raise RuntimeError('generated native inputs changed during compile')'''
   if old_runner.count(old_build_call)!=1:raise ValueError('DISPLAY04 old runner differs')
   old_runner=old_runner.replace(old_build_call,new_build_call).replace(",'display03ActualComplicationApi')",",'display03ActualComplicationApi','display03SkipInvisibleRocket')")
   if old_runner!=current_runner:raise ValueError('DISPLAY04 old runner delta differs')
   old_build=re.search(rb'const BUILD = "([0-9.]+)";',read(snapshots['watchface/source/generated/NativeVersion.mc']))
   new_build=re.search(rb'const BUILD = "([0-9.]+)";',(root/'watchface/source/generated/NativeVersion.mc').read_bytes())
   if not old_build or not new_build or old_build.group(1)!=new_build.group(1):raise ValueError('DISPLAY04 old build version differs')
 # The current field inventory must remain executable, not a stored count.
 import ast
 tree=ast.parse((root/'tests/native_scene_diagnostics/current-508/current_fields_probe.py').read_text())
 actual=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='NAMES' for t in n.targets))
 if list(actual)!=record['fieldsTests']:raise ValueError('DISPLAY04 field inventory differs')
 host=record['hostEvidence'];raw=read(host['log']).decode()
 if host['modules']!=list(HOST_MODULES):raise ValueError('DISPLAY04 host inventory differs')
 if record['evidenceInputs']!=evidence_inputs(root):raise ValueError('DISPLAY04 visual evidence changed')
 expected_host=[]
 for module in HOST_MODULES:
  file=root/Path(*module.split('.')).with_suffix('.py');tree=ast.parse(file.read_text())
  for cls in (n for n in tree.body if isinstance(n,ast.ClassDef)):
   for method in (n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')):
    expected_host.append(method.name+' ('+module+'.'+cls.name+'.'+method.name+') ... ok')
 observed=[line.strip() for line in raw.splitlines() if re.fullmatch(r'test_\w+ \([\w.]+\) \.\.\. ok',line.strip())]
 if len(expected_host)!=len(set(expected_host)) or sorted(expected_host)!=sorted(observed):raise ValueError('DISPLAY04 host assertions omitted or failed')
 if not raw.rstrip().endswith('OK') or not re.search(r'Ran '+str(len(expected_host))+r' tests? in ',raw):raise ValueError('DISPLAY04 host result incomplete')
 # Reconstruct the old .13 tree rather than editing/repinning old receipts.
 cache_key=prior_cache_key(root,record,read)
 if cache_key not in _PRIOR_VALIDATED:
  with tempfile.TemporaryDirectory(prefix='spacefox-display04-prior-') as temp:
   target=Path(temp)
   for folder in ('watchface','locales','tools','tests'):
    shutil.copytree(root/folder,target/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
   for folder in ('openspec','corpus','assets','catalog','schemas'):(target/folder).symlink_to(root/folder,target_is_directory=True)
   for name,item in record['priorSnapshots'].items():
    path=Path(name)
    if path.is_absolute() or '..' in path.parts:raise ValueError('invalid prior snapshot path')
    destination=target/path;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(read(item))
   for name in record['priorAbsent']:
    path=Path(name)
    if path.is_absolute() or '..' in path.parts:raise ValueError('invalid prior absent path')
    (target/path).unlink(missing_ok=True)
   (target/'locales/catalog.json').write_bytes(read(record['priorCatalog']))
   code=('import json;from pathlib import Path;from tools.native_integration13_requalification import validate;'
         'p=Path.cwd();c=json.loads((p/"locales/catalog.json").read_text());'
         'assert validate(p,c)==c["supportPolicy"]["softwareQualifiedLocales"]')
   env=dict(os.environ,PYTHONPATH=str(target),PYTHONDONTWRITEBYTECODE='1')
   result=subprocess.run([sys.executable,'-B','-c',code],cwd=target,env=env,capture_output=True,text=True,timeout=180)
   if result.returncode:raise ValueError('prior .13 reconstruction failed: '+result.stderr[-3000:])
  _PRIOR_VALIDATED.add(cache_key)
 return catalog['supportPolicy']['softwareQualifiedLocales']
