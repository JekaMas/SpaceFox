"""Captured MIN reschedule, withdrawal and new-ID native view projection."""
import json, sys, uuid
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0] = ['/task', '/task/source']
import linux_probe
from tools import native_full_visual_runtime as runtime
from tools import generate_native_current_tests as gen

out = Path('/task/output/reschedule-view')
out.mkdir(parents=True, exist_ok=True)
runtime.GROUPS['grammar'] = (uuid.uuid4().hex, 'CF6.prg')
source = gen.source(Path('/task/profile-a'))
for name in gen.EXPECTED:
    source = source.replace('(:test,:typecheck(false)) function ' + name,
                            '(:typecheck(false)) function ' + name)
fixture = json.loads(Path('/task/source/tests/fixtures/watch_refresh_cache/packets.json').read_text())
source += '''
class RescheduleClock extends WatchClock {function utcSeconds() as Number {return 1794551202;}}
(:test,:typecheck(false)) function rescheduleCurrentView(logger){
 var s=new CurrentStore();currentPut(s,CATALOG_A);currentPut(s,CATALOG_B);
 var c=new NativeCache("https://current-native.invalid/reschedule",s);var now=1794551202l;
 var v=new SpaceFoxView(new RescheduleClock(),new ScheduleState(null,"empty"));
 Test.assert(c.accept(INITIAL,now));v.setPacket(c.packet);var snap=v.snapshotAt(now);
 Test.assert(snap.countdown.equals("T- 16:18:18") && !snap.rescheduled);
 Test.assert(c.accept(MOVED,now));v.setPacket(c.packet);snap=v.snapshotAt(now);
 Test.assert(snap.countdown.equals("T- 16:38:18") && snap.rescheduled);
 Test.assert(c.accept(REFRESH,now));v.setPacket(c.packet);snap=v.snapshotAt(now);
 Test.assert(snap.countdown.equals("T- 16:38:18") && snap.rescheduled);
 Test.assert(c.accept(WITHDRAWN,now));v.setPacket(c.packet);snap=v.snapshotAt(now);
 Test.assert(snap.countdown.equals("--:--:--") && snap.rescheduled);
 Test.assert(c.accept(WITHDRAWN_REFRESH,now));v.setPacket(c.packet);snap=v.snapshotAt(now);
 Test.assert(snap.countdown.equals("--:--:--") && snap.rescheduled);
 Test.assert(c.accept(DIFFERENT,now));v.setPacket(c.packet);snap=v.snapshotAt(now);
 Test.assert(snap.countdown.equals("T- 16:18:18") && !snap.rescheduled);
 logger.debug("RESCHEDULE_VIEW minuteMoved=1 unchangedLatched=1 withdrawnUnknown=1 newIdClear=1");return true;
}
'''
replacements = {'CATALOG_A': fixture['catalogs']['initial']['catalog'],
                'CATALOG_B': fixture['catalogs']['different']['catalog']}
for name in ('initial','moved','refresh','withdrawn','withdrawn_refresh','different'):
    replacements[name.upper()] = fixture['packets'][name]
# Replace longer names first so WITHDRAWN_REFRESH remains a single token.
for name in sorted(replacements, key=len, reverse=True):
    source = source.replace(name, runtime.literal(replacements[name]))
with patch.object(runtime, 'discover', lambda: linux_probe.context), \
     patch.object(runtime.subprocess, 'check_output', linux_probe.git_info), \
     patch.object(runtime, 'validate_manifest', lambda r, l: ET.parse(r / 'watchface/manifest.xml')):
    result = runtime.build_probe(out, source, group='grammar', tests=True)
result.update({'sourceBinding': 'compare productionSources and productionResources to the checkout',
               'expectedTests': ['rescheduleCurrentView'], 'admission': 'diagnostic only'})
(out / 'build.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'exit': result['exitCode']}))
sys.exit(result['exitCode'])
