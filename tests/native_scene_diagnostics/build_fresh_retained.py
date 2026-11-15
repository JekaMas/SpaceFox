"""Directed source-only freshness and retained bitmap probe; diagnostic build."""
import copy, json, sys, uuid
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

sys.path[:0] = ['/task', '/task/source']
import linux_probe
from tools import native_full_visual_runtime as runtime
from tools import generate_native_current_tests as gen
from tools.native_current_runtime import selected_files
from tools.spacefox.catalog import canonical_bytes

out = Path('/task/output/fresh-retained')
out.mkdir(parents=True, exist_ok=True)
identity = uuid.uuid4().hex
runtime.GROUPS['grammar'] = (identity, 'CF2.prg')
source = gen.source(Path('/task/profile-a'))
_, feed, _, _ = selected_files(Path('/task/profile-a'))
fresh = copy.deepcopy(feed)
fresh['publisher']['generation'] += 1
fresh['publisher']['selectionValidatedUtc'] += 3600
fresh['launch']['source_validated_utc'] += 3600
fresh_literal = runtime.literal(canonical_bytes(fresh).decode())
for name in gen.EXPECTED:
    source = source.replace('(:test,:typecheck(false)) function ' + name,
                            '(:typecheck(false)) function ' + name)
source += '''
class DataClock extends WatchClock {
 var at as Number = 1794551192;
 function utcSeconds() as Number {return at;}
}
(:test,:typecheck(false)) function freshRetainedScene(logger){
 var s=new NativeStore();var c=currentCache(s);var start=1794551192l;
 Test.assert(c.accept(CurrentFixture.feed(),start));
 var oldRaw=c.commit["rawHash"];var oldValidation=c.packet.validation;
 var clock=new DataClock();var v=new SpaceFoxView(clock,new ScheduleState(null,"empty"));
 v.setPacket(c.packet);var art=new NativeSfrRenderer();
 art.selectionHash=c.packet.bridge["selection"]["sha256"];v.downloaded=art;
 c.packet.advance(start+10800l);Test.assert(c.packet.stale);
 Test.assert(c.accept(FRESH_INPUT,start+10800l));
 Test.assert(c.packet.validation==start+3600l && c.packet.validation>oldValidation);
 Test.assertMessage(!c.packet.stale,"newer validation must clear stale");
 Test.assertMessage(c.commit["rawHash"].equals(oldRaw),"source-only raw must be reused");
 clock.at=1794561992;v.setPacket(c.packet);
 Test.assertMessage(v.downloaded==art,"same selected bitmap must survive");
 Test.assertMessage(!v.context.stale,"view must expose renewed source age");
 var reopened=new NativeCache(c.base,s);Test.assert(reopened.load(start+10800l)!=null);
 Test.assert(reopened.packet.validation==start+3600l && !reopened.packet.stale);
 logger.debug("FRESH_RETAINED newerValidation=1 sameRaw=1 staleCleared=1 bitmapRetained=1 reopen=1");return true;
}
'''.replace('FRESH_INPUT', fresh_literal)
with patch.object(runtime, 'discover', lambda: linux_probe.context), \
     patch.object(runtime.subprocess, 'check_output', linux_probe.git_info), \
     patch.object(runtime, 'validate_manifest', lambda r, l: ET.parse(r / 'watchface/manifest.xml')):
    result = runtime.build_probe(out, source, group='grammar', tests=True)
result.update({'sourceBinding': 'compare productionSources and productionResources to the checkout',
               'expectedTests': ['freshRetainedScene'], 'admission': 'diagnostic only'})
(out / 'build.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'exit': result['exitCode'], 'uuid': identity}))
sys.exit(result['exitCode'])
