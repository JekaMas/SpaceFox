#!/usr/bin/env python3
"""Reconcile actual finite SDK phases and write software-only admission proof."""
import argparse,hashlib,json,re,shutil,sys
from pathlib import Path
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.build_native_localization import scene_strings
from tools.native_language_policy import input_paths
ROOT=Path(__file__).resolve().parents[1]
# Independent finite-script oracles for the actual timeUnknown UI strings, using
# the pinned SDK Arabic/Hebrew font glyph names in left-to-right paint order.
RTL_UNKNOWN = {
 'ar': ('الوقت غير معروف', ['uni0641','uni0648','uni0631.fina','uni0639.medi','uni0645.init','space','uni0631.fina','uni064A.medi','uni063A.init','space','uni062A.fina','uni0642.init','uni0648.fina','uni0644.init','uni0627']),
 'he': ('הזמן לא ידוע', ['ayin','vav','dalet','yod','space','alef','lamed','space','finalnun','mem','zayin','he']),
}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def require(ok,message):
 if not ok:raise ValueError(message)
def fields(line):return dict(re.findall(r'(\w+)=([^\s]+)',line))
def observe(ui,common,fonts,corpus,root=ROOT):
 root=Path(root);catalog=json.loads((root/'locales/catalog.json').read_text());primary=catalog['supportPolicy']['primaryLocales'];data=json.loads(corpus.read_text());font=json.loads(fonts.read_text());receipts={}
 require(font['status']=='passed' and font['corpusSha256']==sha(corpus),'finite font corpus mismatch/failure');require(font['commonRoleMissingCodepoints']==[] and {r['locale'] for r in font['ui']}==set(primary) and all(not r['missingCodepoints'] for r in font['ui']),'finite glyph coverage missing')
 for label,path,marker in [('ui',ui,'FINITE_UI COMPLETE locales='+str(len(primary))),('common',common,'FINITE_CORPUS COMPLETE records='+str(data['coverage']['sourceCount']))]:
  build=json.loads((path/'build.json').read_text());binding=path/'finite-binding.json'
  if binding.exists():build.update(json.loads(binding.read_text()))
  raw=(path/('ui.log' if label=='ui' else 'corpus.log')).read_text();require(build['exitCode']==0 and build['tests'] is False,'ordinary compiled source required');require(build['productionSourceScope']=='all-native','whole native production scope required');owner=build['ownerTag'];owned='\n'.join(line for line in raw.splitlines() if 'owner='+owner in line);require(marker in owned,'missing owned finite completion '+label)
  for fatal in ('Error:','Unhandled Exception','Out Of Memory','Stack Overflow','FINITE_UI FAILED','FINITE_CORPUS FAILED'):require(fatal not in raw,'finite native failure '+fatal)
  expected={str(p.relative_to(root)) for p in (root/'watchface/source').rglob('*.mc')};require(set(build['productionSources'])==expected,'native production closure changed')
  for name,digest in build['productionSources'].items():
   if name=='watchface/source/generated/SceneStrings.mc':
    # Diagnostic UI runs bypass pending admission only. Availability metadata
    # later changes this expression; the complete static mapping stays identical.
    pending=scene_strings(catalog["locales"],[]).encode();require(hashlib.sha256(pending).hexdigest()==digest,'observed static locale mapping differs')
   else:require(sha(root/name)==digest,'observed native owner changed: '+name)
  for name,digest in build['productionResources'].items():require(sha(root/name)==digest,'observed native resource changed: '+name)
  receipts[label]={'build':build,'owned':owned,'raw':raw}
 ready=[fields(line) for line in receipts['ui']['owned'].splitlines() if 'FINITE_UI READY locale=' in line];require(len(ready)==len(primary) and {r['locale'] for r in ready}==set(primary),'exact primary SDK rows required');require(all(r['words']=='0' and r['renderedStates']=='10' and r['sameBitmap']=='true' for r in ready),'finite UI states incomplete')
 done=[fields(line) for line in receipts['common']['owned'].splitlines() if 'FINITE_CORPUS COMPLETE ' in line];require(len(done)==1 and int(done[0]['records'])==data['coverage']['sourceCount']==1822,'complete finite corpus native record coverage');require(int(done[0]['compositions'])==receipts['common']['build']['uniqueCompositions'],'native composition coverage');require(done[0]['ordinaryBytes']=='126784' and done[0]['sameBitmap']=='true','ordinary corpus/bitmap boundary')
 require(receipts['common']['build']['corpusSha256']==sha(corpus),'observed corpus changed');require(data['coverage']['pageCount']==19 and data['coverage']['terminalNext'] is None and data['coverage']['uniqueLaunchIds']==1822,'complete actual source denominator')
 return {'status':'passed','qualifiedLocales':primary,'corpusSha256':sha(corpus),'productionSources':{name:sha(root/name) for name in input_paths(catalog)},'observedUiOrder':[r['locale'] for r in ready],'nativeUiWords':0,'renderedStatesPerPrimary':10,'nativeCommonRecords':1822,'nativeCommonCompositions':int(done[0]['compositions']),'sampledUiHighBytes':max(int(r['sampledHigh']) for r in ready),'sampledCommonHighBytes':int(done[0]['sampledHigh']),'ordinaryForegroundBytes':126784,'physicalDeviceObserved':False,'nativeSpeakerReviewed':False,'phoneSettingsRendered':False,'nativeHistoricalArtworkQualified':False,'proofBoundary':'Actual ordinary FR165 SDK finite UI/common-role fitting plus exact installed font cmap/host shaping. Source-bound software availability only; sampled memory is not peak. The failed HTTP loopback attempt and raw launcher termination codes are separate retained observations.'}
def _expected_probes(root,catalog,data,ui_build,common_build,ui_probe,common_probe):
 from tools.native_finite_display import UI_WORDS,ui_source,common_source
 primary=catalog['supportPolicy']['primaryLocales'];indices=[];ui_resources={};xml=[]
 for index,row in enumerate(catalog['locales']):
  if row['id'] not in primary:continue
  name='FiniteLocale'+str(len(indices));indices.append(index);native=json.loads((root/'watchface/resources/json'/('Locale'+str(index)+'.json')).read_text());raw=json.dumps({'locale':row['id'],'words':{key:native[key] for key in UI_WORDS}},ensure_ascii=False,separators=(',',':')).encode();ui_resources[name+'.json']=raw;xml.append('<jsonData id="'+name+'" filename="'+name+'.json"/>')
 ui_resources['finite.xml']=('<resources>'+''.join(xml)+'</resources>').encode()
 groups={}
 for row in data['launches']:
  values=tuple(None if ref is None else data['strings'][ref] for ref in row[3]);groups[values]=groups.get(values,0)+1
 rows=[[*fields,count] for fields,count in sorted(groups.items(),key=lambda item:json.dumps(item[0],ensure_ascii=False))];common_resources={};xml=[];names=[]
 for offset in range(0,len(rows),4):
  name='FiniteCommon'+str(len(names));names.append(name);common_resources[name+'.json']=json.dumps(rows[offset:offset+4],ensure_ascii=False,separators=(',',':')).encode();xml.append('<jsonData id="'+name+'" filename="'+name+'.json"/>')
 common_resources['finite-common.xml']=('<resources>'+''.join(xml)+'</resources>').encode()
 marker='<resources><strings><string id="SfrProbeName">SFR-finite</string></strings></resources>'.encode()
 ui_resources['probe.xml']=marker;common_resources['probe.xml']=marker
 match=re.search(r'phase\+=1;stage=0;expected=null;observer.start\(method\(:tick\),(\d+),false\);',ui_probe);require(match is not None,'native UI probe schedule missing')
 for build,raw,expected,resources in [(ui_build,ui_probe,ui_source(indices,int(match.group(1)),ui_build.get("baseUrl","https://current-native.invalid")),ui_resources),(common_build,common_probe,common_source(names,len(data['launches']),common_build.get('baseUrl','https://current-native.invalid')),common_resources)]:
  expected=expected.replace('SpaceFoxApp.initialize();','SpaceFoxApp.initialize();NativeMetrics.ownerTag='+json.dumps(build['ownerTag'])+';System.println("SFR_PROBE owner="+NativeMetrics.ownerTag);',1)
  require(raw==expected and hashlib.sha256(raw.encode()).hexdigest()==build['probeSha256'],'native finite probe does not match actual assertion program')
  require({name:hashlib.sha256(value).hexdigest() for name,value in resources.items()}==build['probeResources'],'compiled finite resource plan differs from complete source/native UI')
 return len(rows)


def validate_bound_observation(root,catalog):
 """Public admission requires actual complete corpus and exact SDK cohort proof."""
 root=Path(root).resolve();proof=catalog['supportPolicy']['softwareQualificationProof'];receipt_path=root/proof['receiptPath'];receipt=json.loads(receipt_path.read_text());require(type(receipt.get('evidenceSchemaVersion')) is int and receipt['evidenceSchemaVersion']==1,'actual finite observation schema required');observations=receipt.get('observations');require(isinstance(observations,dict) and observations,'actual SDK observations required')
 for name,digest in observations.items():
  require(isinstance(name,str) and not Path(name).is_absolute() and '..' not in Path(name).parts,'unsafe finite observation path');path=(root/name).resolve();require(path.is_relative_to(root) and path.is_file() and sha(path)==digest,'finite observation bytes changed: '+name)
 base=receipt_path.parent;required=['ui/build.json','ui/ui.log','ui/compile.log','ui/Probe.mc.txt','common/build.json','common/corpus.log','common/compile.log','common/Probe.mc.txt','fonts.json']
 for name in required:require(str((base/name).relative_to(root)) in observations,'missing actual finite observation: '+name)
 from tools.native_finite_display import load_complete_corpus,UI_WORDS
 corpus=root/proof['corpusPath'];data=load_complete_corpus(corpus,root);ui=base/'ui';common=base/'common';fonts=base/'fonts.json';observed=observe(ui,common,fonts,corpus,root)
 for key in ('qualifiedLocales','nativeCommonRecords','nativeCommonCompositions','nativeUiWords','renderedStatesPerPrimary','ordinaryForegroundBytes','sampledUiHighBytes','sampledCommonHighBytes','productionSources','corpusSha256'):require(receipt.get(key)==observed[key],'finite observed result differs: '+key)
 ui_build=json.loads((ui/'build.json').read_text());common_build=json.loads((common/'build.json').read_text());supplement=common/'finite-binding.json'
 if supplement.exists():
  require(str(supplement.relative_to(root)) in observations,'unbound finite binding supplement');common_build.update(json.loads(supplement.read_text()))
 compositions=_expected_probes(root,catalog,data,ui_build,common_build,(ui/'Probe.mc.txt').read_text(),(common/'Probe.mc.txt').read_text());require(compositions==observed['nativeCommonCompositions'],'finite actual composition count differs')
 lock_path=root/'watchface/toolchain-lock.json';lock=json.loads(lock_path.read_text());sdk=receipt.get('sdkBinding',{});require(sdk.get('toolchainLockSha256')==sha(lock_path) and sdk.get('product')==lock['product']=='fr165' and sdk.get('profileApi')==lock['profile_api'] and sdk.get('sdkVersion')==lock['sdk_version'] and sdk.get('compilerSha256')==lock['compiler_sha256'],'finite SDK lock binding differs')
 for path,build in [(ui,ui_build),(common,common_build)]:
  command=build['command'];require(command[command.index('-d')+1]=='fr165','finite target differs');jar=Path(command[command.index('-jar')+1]);require(jar.name=='monkeybrains.jar' and jar.parent.parent.name==lock['sdk_directory'],'finite compiler version path differs');compile_log=(path/'compile.log').read_text();require('BUILD SUCCESSFUL' in compile_log and 'ERROR:' not in compile_log,'finite compile observation incomplete')
 font=json.loads(fonts.read_text());require(set(font['fonts'])=={'RobotoRegular','NotoNaskhArabicRegular','NotoSansHebrewRegular','NotoSansSCMedium','KosugiRegular','NanumGothicBold','PridiRegular'},'finite font set differs')
 for row in font['ui']:
  require(len(row.get('shaping',[]))==len(UI_WORDS) and {item['key'] for item in row['shaping']}==set(UI_WORDS),'finite host shaping incomplete')
  for item in row['shaping']:require(isinstance(item.get('glyphs'),list) and item['glyphs'] and all(glyph.get('g') not in (None,0,'.notdef') for glyph in item['glyphs']),'finite host glyph missing')
 require(receipt.get('physicalDeviceObserved') is False and receipt.get('nativeSpeakerReviewed') is False and receipt.get('phoneSettingsRendered') is False,'finite proof exceeds software boundary')
 return observed


def qualify(ui,common,fonts,corpus,output):
 ui,common,fonts,corpus,output=(p.resolve() for p in (ui,common,fonts,corpus,output))
 record=observe(ui,common,fonts,corpus);output.mkdir(parents=True,exist_ok=True);observations={}
 for label,path,names in [('ui',ui,['build.json','ui.log','ui-execution.json','compile.log']),('common',common,['build.json','finite-binding.json','corpus.log','corpus-execution.json','compile.log'])]:
  for name in names:
   source=path/name
   if not source.exists():continue
   target=output/label/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);observations[str(target.relative_to(ROOT))]=sha(target)
  # Exact compiled diagnostic source is retained without compiling the snapshot.
  target=output/label/'Probe.mc.txt';shutil.copyfile(path/'Probe.mc',target);observations[str(target.relative_to(ROOT))]=sha(target)
 target=output/'fonts.json';shutil.copyfile(fonts,target);observations[str(target.relative_to(ROOT))]=sha(target)
 lock_path=ROOT/'watchface/toolchain-lock.json';lock=json.loads(lock_path.read_text());record['evidenceSchemaVersion']=1;record['sdkBinding']={'toolchainLockSha256':sha(lock_path),'product':lock['product'],'profileApi':lock['profile_api'],'sdkVersion':lock['sdk_version'],'compilerSha256':lock['compiler_sha256']}
 record['observations']=observations;record['qualifierSha256']=sha(Path(__file__));record['probeReconstructorSha256']=sha(ROOT/'tools/native_finite_display.py');record['bindingReconciliation']='Python proof validation was strengthened after observation. Native font/layout/data owners and every compiled diagnostic input remain exact; only generated software availability expression changed from pending to observed primary IDs and is separately checked by actual no-bypass activation. UI/common probe byte reconstruction is checked, not rerun or assigned a new SDK fingerprint.';path=output/'software-qualification.json';path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
 catalog_path=ROOT/'locales/catalog.json';catalog=json.loads(catalog_path.read_text());policy=catalog['supportPolicy'];policy['softwareQualifiedLocales']=record['qualifiedLocales'];policy['softwareQualificationProof']={'schemaVersion':1,'corpusPath':str(corpus.relative_to(ROOT)),'corpusSha256':record['corpusSha256'],'receiptPath':str(path.relative_to(ROOT)),'receiptSha256':sha(path),'productionSources':record['productionSources'],'scope':'finite-primary-software','physicalDeviceObserved':False,'nativeSpeakerReviewed':False};catalog_path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n');return record
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--ui',type=Path,required=True);p.add_argument('--common',type=Path,required=True);p.add_argument('--fonts',type=Path,required=True);p.add_argument('--corpus',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=qualify(a.ui,a.common,a.fonts,a.corpus,a.output);print(json.dumps({key:r[key] for key in ('status','qualifiedLocales','nativeCommonRecords','nativeCommonCompositions')}))
