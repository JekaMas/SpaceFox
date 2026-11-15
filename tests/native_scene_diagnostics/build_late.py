import copy,json,sys,uuid
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0]=['/task','/task/source']
import linux_probe
from tools import native_full_visual_runtime as runtime
from tools import generate_native_current_tests as gen
from tools.native_current_runtime import selected_files
from tools.spacefox.catalog import canonical_bytes
root=Path('/task');_,feed,_,_=selected_files(root/'profile-a');bad=[]
a=copy.deepcopy(feed);a['providerTraversal']={'query':'qualification-only','complete':True,'reportedCount':1,'receivedUpcoming':1,'detailRequests':0,'worldwideCompleteness':True};bad.append(canonical_bytes(a).decode())
a=copy.deepcopy(feed);a['visualSelection']['path']='https://invalid.example/scene.json';bad.append(canonical_bytes(a).decode())
a=copy.deepcopy(feed);a['nativeTransfer']['path']='../descriptors/outside.json';bad.append(canonical_bytes(a).decode())
a=copy.deepcopy(feed);a['catalogPath']='https://invalid.example/catalog.json';bad.append(canonical_bytes(a).decode())
source=gen.source(root/'profile-a')
for name in gen.EXPECTED:source=source.replace('(:test,:typecheck(false)) function '+name,'(:typecheck(false)) function '+name)
source+='''\n(:test,:typecheck(false)) function currentLateProvenanceAndEndpoints(logger){var s=new CurrentStore();var c=currentCache(s);Test.assert(c.accept(CurrentFixture.feed(),1794551192l));var seal=c.commit["seal"];var floor=s.read(c.pinKey)["generation"];var age=c.packet.validation;var cases='''+runtime.literal(bad)+''';for(var j=0;j<cases.size();j+=1){var before=s.writes;Test.assertMessage(!c.accept(cases[j],1794554792l),"malformed late provenance or endpoint "+j);Test.assert(s.writes==before&&c.commit["seal"].equals(seal)&&s.read(c.pinKey)["generation"]==floor&&c.packet.validation==age);}var reopened=new NativeCache(c.base,s);Test.assert(reopened.load(1794554792l)!=null&&reopened.commit["seal"].equals(seal));logger.debug("CURRENT_LATE provenance=1 endpoints=3 oldSealFloorAge=true reopen=true");return true;}\n'''
id=uuid.uuid4().hex;runtime.GROUPS['late-current']=(id,'CL2.prg');out=root/'output/late-current';out.mkdir(parents=True,exist_ok=True)
with patch.object(runtime,'discover',lambda:linux_probe.context),patch.object(runtime.subprocess,'check_output',linux_probe.git_info),patch.object(runtime,'validate_manifest',lambda r,l:ET.parse(r/'watchface/manifest.xml')):
 r=runtime.build_probe(out,source,group='late-current',tests=True)
r.update({'actualBase':'854a5a30a5bb021d2bac3e2f799b4f6401f269af','admission':'diagnostic only','expectedTests':['currentLateProvenanceAndEndpoints']});(out/'build.json').write_text(json.dumps(r,indent=2)+'\n');print('exit',r['exitCode'],'uuid',id);sys.exit(r['exitCode'])
