"""Enumerate the current feed commit's reached store operations and fault each."""
import copy, hashlib, json, sys, uuid
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0] = ['/task', '/task/source']
import linux_probe
from tools import native_full_visual_runtime as runtime
from tools import generate_native_current_tests as gen
from tools.native_current_runtime import selected_files
from tools.spacefox.catalog import canonical_bytes

out = Path('/task/output/core-fault-roles')
out.mkdir(parents=True, exist_ok=True)
identity = uuid.uuid4().hex
runtime.GROUPS['grammar'] = (identity, 'CF4.prg')
source = gen.source(Path('/task/profile-a'))
_, feed, _, _ = selected_files(Path('/task/profile-a'))
wide = copy.deepcopy(feed)
wide['launch']['mission_name'] = ''
missing = 8192 - len(canonical_bytes(wide))
name = feed['launch']['mission_name'] or feed['launch']['configuration_name']
wide['launch']['mission_name'] = (name * (missing // len(name) + 1))[:missing]
changed = copy.deepcopy(wide)
changed['publisher']['generation'] += 2
changed['publisher']['selectionValidatedUtc'] += 3600
changed['launch']['source_validated_utc'] += 3600
changed['launch']['mission_name'] = feed['launch']['mission_name']
old_expected = hashlib.sha256(canonical_bytes(wide)).hexdigest()
new_expected = hashlib.sha256(canonical_bytes(changed)).hexdigest()
for name in gen.EXPECTED:
    source = source.replace('(:test,:typecheck(false)) function ' + name,
                            '(:typecheck(false)) function ' + name)
source += '''
(:typecheck(false)) class RoleFaultStore {
 var values={};var operations=0;var failAt=0;var fired=false;var roles=[];
 function initialize(seed){if(seed!=null){values=copy(seed);}}
 function copy(v){if(v instanceof Dictionary){var o={};var ks=v.keys();for(var i=0;i<ks.size();i+=1){o[ks[i]]=copy(v[ks[i]]);}return o;}if(v instanceof Array){var a=[];for(var j=0;j<v.size();j+=1){a.add(copy(v[j]));}return a;}return v;}
 function touch(role,key){operations+=1;roles.add(role+":"+key);if(failAt>0 && operations==failAt){fired=true;throw new Lang.InvalidValueException("controlled current operation failure");}}
 function read(k){touch("read",k);return values.hasKey(k)?copy(values[k]):null;}
 function write(k,v){touch("write",k);values[k]=copy(v);}
 function remove(k){touch("remove",k);values.remove(k);}
 function arm(n){operations=0;roles=[];failAt=n;fired=false;}
}
(:test,:typecheck(false)) function currentCoreFaultRoles(logger){
 var now=1794551192l;var seed=new RoleFaultStore(null);var a=currentCache(seed);
 Test.assert(a.accept(CurrentFixture.wide(),now));var snapshot=seed.copy(seed.values);
 var baseline=new RoleFaultStore(snapshot);var good=new NativeCache(a.base,baseline);
 Test.assert(good.load(now)!=null);var oldHash=good.packet.wireHash;var oldAge=good.packet.validation;
 baseline.arm(0);Test.assert(good.accept(CurrentFixture.changed(),now+3600l));
 var newHash=good.packet.wireHash;var newAge=good.packet.validation;
 Test.assert(oldHash.equals("OLD_EXPECTED") && oldAge==1794551192l);
 Test.assert(newHash.equals("NEW_EXPECTED") && newAge==1794554792l);var roles=baseline.roles;var count=baseline.operations;
 Test.assert(count>0);logger.debug("CURRENT_CORE_OPERATIONS count="+count+" roles="+roles);
 for(var i=1;i<=count;i+=1){
  var store=new RoleFaultStore(snapshot);var c=new NativeCache(a.base,store);Test.assert(c.load(now)!=null);
  store.arm(i);c.accept(CurrentFixture.changed(),now+3600l);
  Test.assertMessage(store.fired,"operation not reached "+i);Test.assert(store.roles[i-1].equals(roles[i-1]));store.failAt=0;
  var reopened=new NativeCache(a.base,store);Test.assert(reopened.load(now+3600l)!=null);
  var h=reopened.packet.wireHash;var age=reopened.packet.validation;
  Test.assertMessage(h.equals(oldHash) && age==oldAge || h.equals(newHash) && age==newAge,"mixed accepted state at "+roles[i-1]);
 }
 logger.debug("CURRENT_CORE_FAULTS reached="+count+" exactOldOrNew=true");return true;
}
'''.replace('OLD_EXPECTED', old_expected).replace('NEW_EXPECTED', new_expected)
with patch.object(runtime, 'discover', lambda: linux_probe.context), \
     patch.object(runtime.subprocess, 'check_output', linux_probe.git_info), \
     patch.object(runtime, 'validate_manifest', lambda r, l: ET.parse(r / 'watchface/manifest.xml')):
    result = runtime.build_probe(out, source, group='grammar', tests=True)
result.update({'sourceBinding': 'compare productionSources and productionResources to the checkout',
               'expectedTests': ['currentCoreFaultRoles'], 'admission': 'diagnostic only'})
(out / 'build.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'exit': result['exitCode'], 'uuid': identity}))
sys.exit(result['exitCode'])
