"""Current FeedService 304 callback preserves accepted source age and raw feed."""
import hashlib, json, sys, uuid
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0] = ['/task', '/task/source']
import linux_probe
from tools import native_full_visual_runtime as runtime
from tools import generate_native_current_tests as gen
from tools.native_current_runtime import selected_files

out = Path('/task/output/callback-304')
out.mkdir(parents=True, exist_ok=True)
runtime.GROUPS['grammar'] = (uuid.uuid4().hex, 'CF9.prg')
source = gen.source(Path('/task/profile-a'))
files, _, route, _ = selected_files(Path('/task/profile-a'))
expected = hashlib.sha256(files[route]).hexdigest()
for name in gen.EXPECTED:
    source = source.replace('(:test,:typecheck(false)) function ' + name,
                            '(:typecheck(false)) function ' + name)
source += '''
(:typecheck(false)) class Callback304Service extends FeedService {
 var finishes=0;function finish() as Void {finishes+=1;}
}
(:test,:typecheck(false)) function current304PreservesSource(logger){
 var s=new NativeStore();var c=currentCache(s);var now=1794551192l;
 Test.assert(c.accept(CurrentFixture.feed(),now));var seal=c.commit["seal"];var before=s.writes;
 Test.assert(c.packet.validation==now && c.packet.wireHash.equals("EXPECTED_SHA"));
 var service=new Callback304Service();service.transfer=new NativeTransfer(c.base,s);
 service.receive(304,null);Test.assert(service.finishes==1 && s.writes==before);
 var reopened=new NativeCache(c.base,s);Test.assert(reopened.load(now+10800l)!=null);
 Test.assert(reopened.packet.validation==now && reopened.packet.stale);
 Test.assert(reopened.packet.wireHash.equals("EXPECTED_SHA") && reopened.commit["seal"].equals(seal));
 Test.assert(s.writes==before);
 logger.debug("CURRENT_304 finish=1 unchangedWire=1 unchangedSourceAge=1 staleFromSource=1 noCallbackWrites=1");return true;
}
'''.replace('EXPECTED_SHA', expected)
with patch.object(runtime, 'discover', lambda: linux_probe.context), \
     patch.object(runtime.subprocess, 'check_output', linux_probe.git_info), \
     patch.object(runtime, 'validate_manifest', lambda r, l: ET.parse(r / 'watchface/manifest.xml')):
    result = runtime.build_probe(out, source, group='grammar', tests=True)
result.update({'sourceBinding': 'compare productionSources and productionResources to the checkout',
               'expectedTests': ['current304PreservesSource'], 'admission': 'diagnostic only'})
(out / 'build.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'exit': result['exitCode']}))
sys.exit(result['exitCode'])
