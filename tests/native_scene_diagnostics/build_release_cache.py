import json,sys,uuid
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0]=['/task','/task/source']
import linux_probe
from tools import native_full_visual_runtime as runtime
from tools import generate_native_current_tests as gen
out=Path('/task/output/release-cache');out.mkdir(parents=True,exist_ok=True)
runtime.GROUPS['grammar']=(uuid.uuid4().hex,'RC1.prg')
source=gen.source(Path('/task/profile-a'))
for name in gen.EXPECTED:
 source=source.replace('(:test,:typecheck(false)) function '+name,'(:typecheck(false)) function '+name)
fixture=json.loads(Path('/task/source/tests/fixtures/watch_refresh_cache/packets.json').read_text())
initial=fixture['packets']['initial'];bad=json.loads(initial);bad['schemaVersion']=4
bad_renderer=json.loads(initial);bad_renderer['rendererProfile']='SFR-unsupported'
source += '''
(:typecheck(false)) class ReleaseTestOwner { var feed; function initialize(cache){feed=cache;} function onSettingsChanged(){} }
(:test,:typecheck(false)) function releaseCurrentHostSchema(log){
 var s=new CurrentStore();currentPut(s,CATALOG_A);currentPut(s,CATALOG_B);
 var a=new NativeCache("https://current-native.invalid/first",s);var now=1794551202l;
 Test.assert(a.accept(INITIAL,now));Test.assert(a.accept(MOVED,now));
 Test.assert(a.packet.rescheduled);Test.assert(a.packet.validation==1794551193l);
 var b=new NativeCache("https://current-native.invalid/second",s);
 Test.assert(b.load(now)==null);Test.assert(b.accept(INITIAL,now));
 Test.assert(!b.packet.rescheduled);Test.assert(b.packet.validation==1794551192l);
 var owner=new ReleaseTestOwner(b);var before=SettingsMenu.root(owner)[0];Test.assert(before.findItemById(:updateRejected)==-1);
 var wire=b.packet.wireHash;var transfer=new NativeTransfer(b.base,s);var incoming=new NativeIncoming(s,b.base);
 Test.assert(transfer.stage("feed",BADSCHEMA,null));Test.assert(!incoming.admitFeedForView(b,now,null));
 Test.assert(b.failure.equals("update-rejected"));
 Test.assert(transfer.stage("feed",BADRENDERER,null));Test.assert(!incoming.admitFeedForView(b,now,null));
 Test.assert(b.failure.equals("update-rejected"));
 var menu=SettingsMenu.root(owner)[0];
 var item=menu.getItem(12);Test.assertEqual(item.getId(),:updateRejected);
 Test.assertEqual(item.getLabel(),"Feed rejected");Test.assertEqual(item.getSubLabel(),"Check URL or update SpaceFox");
 Test.assert(SettingsMenuText.rejected("ru")[0].equals("Данные отклонены"));
 Test.assert(SettingsMenuText.rejected("de")[0].equals("Daten abgelehnt"));
 Test.assert(SettingsMenuText.rejected("fr")[0].equals("Données refusées"));
 Test.assert(SettingsMenuText.rejected("es")[0].equals("Datos rechazados"));
 Test.assert(transfer.stage("feed",INITIAL,null));Test.assert(incoming.admitFeedForView(b,now,null));var recovered=SettingsMenu.root(owner)[0];
 Test.assert(recovered.findItemById(:updateRejected)==-1);
 var reopened=new NativeCache("https://current-native.invalid/second",s);
 Test.assert(reopened.load(now)!=null);Test.assertEqual(reopened.packet.wireHash,wire);
 Test.assert(!reopened.packet.rescheduled);Test.assert(reopened.packet.validation==1794551192l);
 var original=new NativeCache("https://current-native.invalid/first",s);
 Test.assert(original.load(now)==null);Test.assert(!original.accept(INITIAL,now));
 Test.assert(original.accept(MOVED,now));Test.assert(original.packet.validation==1794551193l);
 log.debug("RELEASE_CURRENT incomingPath=1 schemaRefused=1 rendererRefused=1 actionableMenu=1 fiveLocales=1 clearsOnSuccess=1 oldWireRetained=1 separateHostAge=1 separateReschedule=1 hostFloor=1");return true;
}
'''
items={'CATALOG_A':fixture['catalogs']['initial']['catalog'],'CATALOG_B':fixture['catalogs']['different']['catalog'],'INITIAL':initial,'MOVED':fixture['packets']['moved'],'BADSCHEMA':json.dumps(bad,separators=(',',':')),'BADRENDERER':json.dumps(bad_renderer,separators=(',',':'))}
for name in sorted(items,key=len,reverse=True):source=source.replace(name,runtime.literal(items[name]))
with patch.object(runtime,'discover',lambda:linux_probe.context),patch.object(runtime.subprocess,'check_output',linux_probe.git_info),patch.object(runtime,'validate_manifest',lambda r,l:ET.parse(r/'watchface/manifest.xml')):
 result=runtime.build_probe(out,source,group='grammar',tests=True)
result.update({'sourceBinding':'compare productionSources and productionResources to checkout','expectedTests':['releaseCurrentHostSchema'],'admission':'diagnostic only'})
(out/'build.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'exit':result['exitCode']}));sys.exit(result['exitCode'])
