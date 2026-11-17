import json
from pathlib import Path
from tools.spacefox.watch_snapshot import snapshot
root=Path.cwd(); task=Path('/Users/jekamas/.codex/tmp/spacefox-physical-six-20261118');src=root/'tests/fixtures/fr165-runtime-20261116'; feed=json.loads((src/'feed.txt').read_text());cat=json.loads((src/'objects'/feed['catalogPath']).read_text());transfer=json.loads((src/'objects'/feed['nativeTransfer']['path']).read_text());payload=snapshot(feed,cat)
d=task/'sfr-res';d.mkdir(exist_ok=True);(d/'payload.json').write_text(json.dumps({'payload':payload},ensure_ascii=False));refs=[('Payload','payload.json')]; lines=[]
items=[(0,feed['nativeTransfer']['sha256'])]+[(row[0],row[1]) for row in transfer['objects']]
for i,(kind,digest) in enumerate(items):
 path=src/'objects'/('descriptors' if kind==0 else 'rasters')/(digest+('.json' if kind==0 else '.sfr'))
 raw=path.read_text();name='Object'+str(i);filename=name+'.json';(d/filename).write_text(json.dumps({'value':raw},ensure_ascii=False));refs.append((name,filename))
 lines.append('  value=WatchUi.loadResource(Rez.JsonData.%s);store.write("sf.obj.%s",value["value"]);value=null;'%(name,digest))
(d/'resources.xml').write_text('<resources>'+''.join('<jsonData id="%s" filename="%s"/>'%r for r in refs)+'</resources>')
code='''import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.WatchUi;
(:typecheck(false)) class SfrClock extends WatchClock {function utcSeconds() as Number {return 1795041600;}}
(:typecheck(false)) class SfrObserverView extends SpaceFoxView {
 var stagedPacket=null;var stagedSource=null;var switched=false;var entered=false;var complete=false;var failed=false;
 function initialize(){SpaceFoxView.initialize(new SfrClock(),new ScheduleState(null,"empty"));}
 function onUpdate(dc as Graphics.Dc) as Void {
  SpaceFoxView.onUpdate(dc);
  if(!switched&&renderer!=null&&renderer.art!=null){var s=System.getSystemStats();System.println("WATCHFACE_LARGEST total="+s.totalMemory+" used="+s.usedMemory+" free="+(s.totalMemory-s.usedMemory));switched=true;var p=stagedPacket;var a=stagedSource;stagedPacket=null;stagedSource=null;setPacket(p);setAssetCache(a);prepareVisual();}
 }
 function sfrStep() as Void {
  SpaceFoxView.sfrStep();
  if(!entered&&sfrBuild!=null){entered=true;var s=System.getSystemStats();System.println("WATCHFACE_SFR_STARTED total="+s.totalMemory+" used="+s.usedMemory+" free="+(s.totalMemory-s.usedMemory)+" reserve="+sfrReadReserve());}
  if(!complete&&downloaded!=null){complete=true;var s=System.getSystemStats();System.println("WATCHFACE_SFR_COMPLETE total="+s.totalMemory+" used="+s.usedMemory+" free="+(s.totalMemory-s.usedMemory)+" model="+context.modelId);}
  if(!failed&&sceneLifecycle.job!=null&&sceneLifecycle.job.state==sceneLifecycle.job.FAILED){failed=true;System.println("WATCHFACE_SFR_FAILED");}
 }
}
(:typecheck(false)) class SfrObserverApp extends Application.AppBase {
 function initialize(){AppBase.initialize();}
 function getInitialView(){
  var base="https://fixture.invalid";var store=new NativeStore();var value=null;
'''+ '\n'.join(lines)+'''
  value=WatchUi.loadResource(Rez.JsonData.Payload);var snap=new NativeTrustedStore(store,base);if(!snap.save(value["payload"])){throw new Lang.InvalidValueException("fixture snapshot");}value=null;var packet=new NativeTrustedPacket(snap.load());var bridge=packet.bridge;
  store.write("sf.batch.head",{"base"=>base,"pending"=>false,"catalogDigest"=>bridge["catalogDigest"],"transfer"=>bridge["transfer"],"serial"=>1});
  store.write("sf.batch.pending",{"base"=>base,"pending"=>false});var source=new NativeRenderSource(store,base,bridge);if(!source.ready){throw new Lang.InvalidValueException("fixture batch");}
  var view=new SfrObserverView();view.setContext(new SceneContext({"id"=>"ll2:launch:ffffffff-ffff-4fff-8fff-ffffffffffff","rocket"=>"Falcon Heavy","operator"=>"SpaceX","site"=>"Test location","modelId"=>"ll2:configuration:161","point"=>[-80.6,28.6],"target"=>1795042200,"precision"=>"exact"}));view.stagedPacket=packet;view.stagedSource=source;System.println("WATCHFACE_FIXTURE_READY objects='''+str(len(items))+'''");return [view];
 }
}
'''
(task/'sfr-src').mkdir(exist_ok=True);(task/'sfr-src/Observer.mc').write_text(code)
manifest=(root/'watchface/manifest.xml').read_text().replace('entry="SpaceFoxApp"','entry="SfrObserverApp"');(task/'sfr-manifest.xml').write_text(manifest)
(task/'sfr.jungle').write_text('project.manifest = /task/sfr-manifest.xml\nbase.sourcePath = /source/watchface/source;/task/sfr-src\nbase.resourcePath = /source/watchface/resources;/task/sfr-res\n')
print('bounded objects',len(items),'captured launch',payload[3][0])
