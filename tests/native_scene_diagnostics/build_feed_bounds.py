import json,sys,uuid
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0]=['/task','/task/source']
import linux_probe
from tools import native_full_visual_runtime as runtime
from tools import generate_native_current_tests as gen
out=Path('/task/output/p3');out.mkdir(parents=True,exist_ok=True);identity=uuid.uuid4().hex;runtime.GROUPS['grammar']=(identity,'P3.prg');source=gen.source(Path('/task/profile-a'))
for name in gen.EXPECTED:source=source.replace('(:test,:typecheck(false)) function '+name,'(:typecheck(false)) function '+name)
source+='''
(:typecheck(false)) class BoundsService extends FeedService {var finished=0;function initialize(){FeedService.initialize();}function finish() as Void {finished+=1;}function optional() as Void {finish();}}
(:test,:typecheck(false)) function p3ProvisionalForeground(logger){
 Application.Properties.setValue("FeedBaseUrl","https://current-native.invalid");var s=new CurrentStore();var c=currentCache(s);var now=1794554792l;Test.assert(c.accept(CurrentFixture.feed(),now));var seal=c.commit["seal"];var age=c.packet.validation;var pub=c.packet.document["publisher"]["generation"];
 var service=new BoundsService();service.transfer=new NativeTransfer(c.base,s);service.batch=new NativeBatch(s,c.base);service.receive(200,CurrentFixture.fresh());Test.assert(service.finished==1);Test.assert(c.commit["seal"].equals(seal)&&c.packet.validation==age&&c.packet.document["publisher"]["generation"]==pub);Test.assert(s.read("sf.incoming.feed") instanceof Dictionary);
 var app=new SpaceFoxApp();app.view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));app.feed=c;app.onBackgroundData({"provisional"=>true});Test.assert(c.packet!=null&&c.packet.document["publisher"]["generation"]==pub+1&&c.packet.validation==1794554792l);Test.assert(!c.commit["seal"].equals(seal));logger.debug("P3_FOREGROUND serviceCallback=true provisionalOnly=true callbackAdmission=true sourceAge=1794554792 heap="+System.getSystemStats().totalMemory);return true;
}
(:test,:typecheck(false)) function p3BoundsRetain(logger){
 var s=new CurrentStore();var c=currentCache(s);var now=1794554792l;Test.assert(c.accept(CurrentFixture.feed(),now));var seal=c.commit["seal"];var age=c.packet.validation;var t=new NativeTransfer(c.base,s);var writes=s.writes;
 Test.assert(!t.stage("feed",CurrentFixture.wide()+"x",null));Test.assert(s.writes==writes&&c.commit["seal"].equals(seal));
 var parser=new NativeJson();Test.assert(parser.parse("[[[[[[[[0]]]]]]]]",8192) instanceof Array);var depthFailed=false;try{parser.parse("[[[[[[[[[0]]]]]]]]]",8192);}catch(e){depthFailed=true;}Test.assert(depthFailed);
 var malformed=CurrentFixture.feed().substring(0,CurrentFixture.feed().length()-1)+",\\"zzzLateRoot\\":[[[[[[[[[0]]]]]]]]]}";Test.assert(!c.accept(malformed,now));Test.assert(c.commit["seal"].equals(seal)&&c.packet.validation==age);
 s.failAt=s.writes+1;var failed=false;try{t.stage("feed",CurrentFixture.fresh(),null);}catch(e){failed=true;}s.failAt=-1;Test.assert(failed);var reopened=new NativeCache(c.base,s);Test.assert(reopened.load(now)!=null&&reopened.commit["seal"].equals(seal)&&reopened.packet.validation==age);logger.debug("P3_REFUSAL oversizeNoWrite=true depth8=true depth9Refused=true failedStageReopens=true");return true;
}
'''
with patch.object(runtime,'discover',lambda:linux_probe.context),patch.object(runtime.subprocess,'check_output',linux_probe.git_info),patch.object(runtime,'validate_manifest',lambda r,l:ET.parse(r/'watchface/manifest.xml')):result=runtime.build_probe(out,source,group='grammar',tests=True)
result.update({'sourceBinding':'compare hashes against checkout','expectedTests':['p3ProvisionalForeground','p3BoundsRetain'],'admission':'diagnostic only'});(out/'build.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'exit':result['exitCode'],'uuid':identity}));sys.exit(result['exitCode'])
