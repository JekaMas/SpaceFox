import copy,hashlib,json,sys,uuid
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0]=['/task','/task/source']
import linux_probe
import current_runtime as runtime
from tools.native_current_runtime import selected_files
root=Path('/task');out=root/'output/batch-source-age';out.mkdir(parents=True,exist_ok=True);files,feed,_,paths=selected_files(root/'profile-a');resources={};xml=['<resources>'];names=[]
for i,path in enumerate(paths):
 name='Obj%d'%i;raw=files[path];digest=hashlib.sha256(raw).hexdigest();item={'path':path,'sha256':digest,'raw':raw.decode()};resources[name+'.json']=json.dumps(item,ensure_ascii=False,separators=(',',':')).encode();xml.append('<jsonData id="'+name+'" filename="'+name+'.json"/>');names.append('Rez.JsonData.'+name)
resources['Feed.json']=json.dumps({'raw':files['feed.json'].decode()},ensure_ascii=False,separators=(',',':')).encode();xml.append('<jsonData id="Feed" filename="Feed.json"/>');fresh=copy.deepcopy(feed);fresh['publisher']['generation']+=1;resources['Fresh.json']=json.dumps({'raw':json.dumps(fresh,sort_keys=True,ensure_ascii=False,separators=(',',':'))},ensure_ascii=False,separators=(',',':')).encode();xml.append('<jsonData id="Fresh" filename="Fresh.json"/>');resources['objects.xml']=(''.join(xml)+'</resources>').encode();identity=uuid.uuid4().hex;runtime.GROUPS['batch']=(identity,'CT2.prg')
rows=','.join('[0,"'+format(i,'064x')+'",1]' for i in range(1,42));bad=json.dumps('{"objects":['+rows+']}')
app='''import Toybox.Application;import Toybox.Lang;import Toybox.System;import Toybox.WatchUi;
(:typecheck(false)) class CountingService extends FeedService {var got=0;var finishes=0;function request(path as String,callback as Method) as Void {got+=1;}function finish() as Void {finishes+=1;}function diagnosticCode(stage,code) as Void {}}
(:typecheck(false)) class BatchView extends WatchUi.WatchFace {var app;function initialize(a){WatchFace.initialize();app=a;}function onUpdate(dc){app.step();}}
(:typecheck(false)) class SfrRuntimeApp extends Application.AppBase {
 var store;var batch;var objects=@@OBJECTS@@;var count=0;var seen={};var finished=false;var cache;var phase=0;var originalAge;
 function initialize(){AppBase.initialize();}
 function ensure(ok,msg){if(!ok){System.println("BATCH_FAIL "+msg);throw new Lang.InvalidValueException(msg);}}
 function getInitialView(){store=new NativeStore();batch=new NativeBatch(store,"https://selected.invalid");ensure(batch.begin(WatchUi.loadResource(Rez.JsonData.Feed)["raw"]),"begin");var refused=false;try{batch.parseIndex(@@BAD@@);}catch(ex){refused=true;}ensure(refused,"unbounded index accepted");return [new BatchView(self)];}
 function step(){if(finished){return;}if(phase==1){cache=new NativeCache("https://selected.invalid",store);ensure(cache.accept(WatchUi.loadResource(Rez.JsonData.Feed)["raw"],1794551192l),"accepted A");originalAge=cache.packet.validation;phase=2;WatchUi.requestUpdate();return;}if(phase==2){var incoming=new NativeIncoming(store,cache.base);ensure(incoming.admitFeed(cache,1794554792l),"admit source-only B");ensure(cache.packet.validation==originalAge&&cache.packet.document["publisher"]["generation"]==2,"true source age");System.println("SOURCE_AGE_COMPLETE generation=2 sourceValidation="+cache.packet.validation+" unchanged=true");finished=true;System.exit();return;}var ref=batch.next();if(ref==null){ensure(count==@@COUNT@@,"request count");var service=new CountingService();service.transfer=new NativeTransfer("https://selected.invalid",store);service.batch=batch;service.receive(200,WatchUi.loadResource(Rez.JsonData.Fresh)["raw"]);ensure(service.got==0&&service.finishes==1,"source-only optional GET");System.println("SOURCE_ONLY_CALLBACK generation=2 optionalGets=0 callbackFinish=1");System.println("BATCH_COMPLETE fetched="+count+" expected=@@COUNT@@ exactSelectedOnly=true noGlobalManifest=true unboundedIndexRefused=true");phase=1;WatchUi.requestUpdate();return;}ensure(!seen.hasKey(ref["path"]),"duplicate request");seen[ref["path"]]=true;var found=null;for(var i=0;i<objects.size();i+=1){var value=WatchUi.loadResource(objects[i]);if(value["path"].equals(ref["path"])){found=value;break;}}ensure(found!=null&&found["sha256"].equals(ref["sha256"]),"nonselected path");ensure(batch.immutable.put(ref,found["raw"]),"integrity");count+=1;WatchUi.requestUpdate();}
}'''
for k,v in {'@@OBJECTS@@':'['+','.join(names)+']','@@BAD@@':bad,'@@COUNT@@':str(len(paths))}.items():app=app.replace(k,v)
with patch.object(runtime,'discover',lambda:linux_probe.context),patch.object(runtime.subprocess,'check_output',linux_probe.git_info),patch.object(runtime,'validate_manifest',lambda r,l:ET.parse(r/'watchface/manifest.xml')):
 result=runtime.build_probe(out,app,group='batch',tests=False,probe_resources=resources)
result.update({'actualBase':'508679499bb34926207d695ced00b7890be7530d','selectedPaths':paths,'admission':'diagnostic only'});(out/'build.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'exit':result['exitCode'],'uuid':identity,'count':len(paths)}));sys.exit(result['exitCode'])
