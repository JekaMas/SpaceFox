import hashlib,json,sys,uuid
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0]=['/task','/task/source']
import linux_probe
from tools import native_full_visual_runtime as runtime
from tools.native_current_runtime import selected_files
root=Path('/task');out=root/'output/callback-skew';out.mkdir(parents=True,exist_ok=True)
fa,a,_,pa=selected_files(root/'profile-a');fb,b,_,pb=selected_files(root/'profile-b')
missing=next(p for p in pb if p.startswith('rasters/') and p not in pa)
print('missing',missing,flush=True)
resources={};xml=['<resources>'];ids={}
for label,files,feed,paths in [('A',fa,a,pa),('B',fb,b,pb)]:
 names=[]
 for i,path in enumerate(paths):
  name='Obj%s%d'%(label,i);raw=files[path];digest=hashlib.sha256(raw).hexdigest();value={'ref':{'path':path,'sha256':digest,'decodedBytes':len(raw)},'raw':raw.decode()}
  resources[name+'.json']=json.dumps(value,ensure_ascii=False,separators=(',',':')).encode();xml.append('<jsonData id="'+name+'" filename="'+name+'.json"/>')
  if label=='B' and path==missing:missingId='Rez.JsonData.'+name
  else:names.append('Rez.JsonData.'+name)
 name='Feed'+label;resources[name+'.json']=json.dumps({'raw':files['feed.json'].decode()},ensure_ascii=False,separators=(',',':')).encode();xml.append('<jsonData id="'+name+'" filename="'+name+'.json"/>');ids[label]=names
resources['objects.xml']=(''.join(xml)+'</resources>').encode();identity=uuid.uuid4().hex;runtime.GROUPS['negative-settings']=(identity,'CB1.prg')
app='''// NativeMetrics probe-only adapter inclusion
import Toybox.Application;import Toybox.Lang;import Toybox.System;import Toybox.WatchUi;
(:typecheck(false)) class NegativeView extends WatchUi.WatchFace {var app;function initialize(a){WatchFace.initialize();app=a;}function onUpdate(dc){app.step();}}
(:typecheck(false)) class SfrRuntimeApp extends Application.AppBase {
 var store;var cache;var immutable;var stage=0;var pos=0;var objects=@@OBJA@@;var build;var prior;var missing;
 function initialize(){AppBase.initialize();}
 function ensure(ok,msg){if(!ok){System.println("NEG_FAIL "+msg);throw new Lang.InvalidValueException(msg);}}
 function getInitialView(){store=new NativeStore();cache=new NativeCache("https://negative.invalid",store);immutable=new NativeImmutable(store);ensure(store.read("sf.commit")==null,"fresh");return [new NegativeView(self)];}
 function again(){WatchUi.requestUpdate();}
 function step(){
 if(stage==0||stage==2){if(pos<objects.size()){var item=WatchUi.loadResource(objects[pos]);ensure(immutable.put(item["ref"],item["raw"]),"seed "+pos);pos+=1;again();return;}if(stage==0){ensure(cache.accept(WatchUi.loadResource(Rez.JsonData.FeedA)["raw"],1794551192l),"accept A");build=new NativeSfrBuild(store,"https://negative.invalid",cache.packet);stage=1;}else{missing=WatchUi.loadResource(@@MISSING@@);ensure(!immutable.put(missing["ref"],missing["raw"]+"x"),"reject corrupted bytes");ensure(immutable.raw(missing["ref"])==null,"missing remains absent");ensure(cache.accept(WatchUi.loadResource(Rez.JsonData.FeedB)["raw"],1794551192l),"accept fresh B schedule");var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));view.setSettings(new SceneSettings({"Field1"=>5,"Field2"=>4,"Field3"=>2,"Field4"=>0}));ensure(nativeSame(view.settings.slots,["battery","calories","heart","steps"]),"settings before");var old=new NativeSfrRenderer();old.selectionHash="@@SEL_A@@";view.downloaded=old;view.setPacket(cache.packet);ensure(nativeSame(view.settings.slots,["battery","calories","heart","steps"]),"settings preserved");ensure(view.downloaded==null&&view.context.launchId.equals("ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b"),"no old bitmap under B");build=new NativeSfrBuild(store,"https://negative.invalid",cache.packet);stage=3;}again();return;}
 if(stage==1){if(!build.step()){again();return;}prior=store.read("sf.raster.active")["selectionHash"];ensure(prior.equals("@@SEL_A@@"),"A active");build=null;objects=@@OBJB@@;pos=0;stage=2;again();return;}
 if(stage==3){var refused=false;try{build.step();}catch(ex){refused=true;System.println("NEG_EXPECTED missingObject="+ex.getErrorMessage());}if(!refused){again();return;}ensure(store.read("sf.raster.active")["selectionHash"].equals(prior),"partial activated");ensure(cache.packet.document["publisher"]["generation"]==2&&cache.packet.validation==1794551192l,"B source facts");ensure(immutable.put(missing["ref"],missing["raw"]),"retry missing object");build=new NativeSfrBuild(store,"https://negative.invalid",cache.packet);stage=4;again();return;}
 if(stage==4){if(!build.step()){again();return;}ensure(build.result.selectionHash.equals("@@SEL_B@@")&&store.read("sf.raster.active")["selectionHash"].equals("@@SEL_B@@"),"retry B active");ensure(store.read("sf.raster.recovery")["selectionHash"].equals(prior),"A recovery");System.println("NEG_COMPLETE corruptRejected=true missingRefused=true priorPointerPreserved=true freshBContext=true noOldBitmap=true retryB=true recoveryA=true fourSettingsPreserved=true");stage=99;System.exit();}
 }
}'''
for k,v in {'@@OBJA@@':'['+','.join(ids['A'])+']','@@OBJB@@':'['+','.join(ids['B'])+']','@@MISSING@@':missingId,'@@SEL_A@@':a['visualSelection']['sha256'],'@@SEL_B@@':b['visualSelection']['sha256']}.items():app=app.replace(k,v)
app=app.replace('store=new NativeStore();cache=new NativeCache', 'store=new NativeStore();var service=new FeedService();service.transfer=new NativeTransfer("https://first.invalid/site",store);ensure(service.requestUrl("feed.json").equals("https://first.invalid/site/feed.json.txt"),"first host");service.transfer=new NativeTransfer("https://second.invalid/site",store);ensure(service.requestUrl("feed.json").equals("https://second.invalid/site/feed.json.txt"),"second host");cache=new NativeCache')
oldA=next(p for p in pa if p.startswith('rasters/') and p not in pb)
oldId='Rez.JsonData.ObjA'+str(pa.index(oldA))
app=app.replace('ensure(!immutable.put(missing["ref"],missing["raw"]+"x"),"reject corrupted bytes");', 'ensure(!immutable.put(missing["ref"],missing["raw"]+"x"),"reject corrupted bytes");ensure(!immutable.put(missing["ref"],WatchUi.loadResource('+oldId+')["raw"]),"reject old CDN bytes for new digest");')
app=app.replace('fourSettingsPreserved=true', 'fourSettingsPreserved=true twoHosts=true oldBytesRefused=true')
app=app.replace('(:typecheck(false)) class NegativeView', '(:typecheck(false)) class ControlledCallback extends FeedService {var finishes=0;var optionals=0;var status="";function finish() as Void{finishes+=1;}function optional() as Void{optionals+=1;}function diagnosticCode(stage,code) as Void{status=stage;}}\n(:typecheck(false)) class NegativeView')
old='ensure(!immutable.put(missing["ref"],WatchUi.loadResource('+oldId+')["raw"]),"reject old CDN bytes for new digest");'
new='var callback=new ControlledCallback();callback.transfer=new NativeTransfer("https://negative.invalid",store);callback.batch=new NativeBatch(store,callback.transfer.base);callback.assetRequest=missing["ref"];callback.receiveBatch(200,WatchUi.loadResource('+oldId+')["raw"]);ensure(callback.finishes==1&&callback.optionals==0&&immutable.raw(missing["ref"])==null,"200 stale response refusal");'
assert old in app;app=app.replace(old,new).replace('oldBytesRefused=true', 'oldBytesRefused=true http200CallbackRefused=true')
with patch.object(runtime,'discover' ,lambda:linux_probe.context),patch.object(runtime.subprocess,'check_output',linux_probe.git_info),patch.object(runtime,'validate_manifest',lambda r,l:ET.parse(r/'watchface/manifest.xml')):
 result=runtime.build_probe(out,app,group='negative-settings',tests=False,probe_resources=resources)
result.update({'actualBase':'854a5a30a5bb021d2bac3e2f799b4f6401f269af','missing':missing,'admission':'diagnostic only'});(out/'build.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'exit':result['exitCode'],'uuid':identity}));sys.exit(result['exitCode'])
