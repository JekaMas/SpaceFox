from pathlib import Path
import json
import sys
from unittest.mock import patch
from xml.etree import ElementTree as ET
from tools.native_full_visual_runtime import ROOT, GROUPS, IMPORTS, build_probe
from tools.spacefox.catalog import canonical_bytes
base=ROOT/'openspec/changes/spacefox-watchface/evidence/final-native-timing-settings'
d=json.loads((base/'packets.json').read_text())
raw=json.loads(d['exact']); f={'launch_id':raw['launch']['launch_id'],'target_utc':1794583543,'end_utc':1794585343,'source_url':'https://example.invalid/mission/?missionId=technical','reviewed_utc':1794576344};raw['launch']['ascent_end']=f;raw['publisher']['generation']+=1;d['ascentGood']=canonical_bytes(raw).decode()
for label,change in [('ascentBadId',{'launch_id':'ll2:launch:wrong'}),('ascentBadTarget',{'target_utc':1794583544}),('ascentBadEnd',{'end_utc':1794583542}),('ascentBadUrl',{'source_url':'https://example.invalid:abc/'}),('ascentBadFuture',{'reviewed_utc':1794576346})]:
 j=json.loads(d['ascentGood']);j['launch']['ascent_end'].update(change);d[label]=canonical_bytes(j).decode()
source=(ROOT/'tests/fixtures/sourced_ascent_end/Assertions.mc').read_text()
strict='--strict' in sys.argv
out=base/('ascent-fix/native-strict' if strict else 'ascent-fix/native');GROUPS['ascent-fix']=('9af62b7a43d84afcb21e8d935670c109','SpaceFoxAscentFix20261113.prg')
resources={'packets.json':json.dumps(d).encode(),'packets.xml':b'<resources><jsonData id="FinalPackets" filename="packets.json"/></resources>'}
if strict:
 r=build_probe(out,source,group='ascent-fix',tests=True,probe_resources=resources)
else:
 with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
  r=build_probe(out,source,group='ascent-fix',tests=True,probe_resources=resources)
r['expectedTests']=['ascentAdmissionPositive','ascentAdmissionNegative'];r['admissionValidation']='strict-current-proof' if strict else 'pending-delta-diagnostic-build';(out/'build.json').write_text(json.dumps(r,indent=2)+'\n');print('compile exit',r['exitCode'])
