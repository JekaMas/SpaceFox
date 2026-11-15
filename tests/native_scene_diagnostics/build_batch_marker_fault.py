"""Directed pending-batch marker interruption probe against SDK Storage."""
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

out = Path('/task/output/batch-marker-fault')
out.mkdir(parents=True, exist_ok=True)
identity = uuid.uuid4().hex
runtime.GROUPS['grammar'] = (identity, 'CF3.prg')
source = gen.source(Path('/task/profile-a'))
_, feed, _, _ = selected_files(Path('/task/profile-a'))
# Technical empty index exercises paired completion writes without making any
# claim that this index is an admissible complete visual selection.
index_raw = b'{"objects":[]}'
digest = hashlib.sha256(index_raw).hexdigest()
head = copy.deepcopy(feed)
head['nativeTransfer'] = {'path': 'descriptors/' + digest + '.json',
                          'sha256': digest, 'decodedBytes': len(index_raw)}
head_literal = runtime.literal(canonical_bytes(head).decode())
index_literal = runtime.literal(index_raw.decode())
for name in gen.EXPECTED:
    source = source.replace('(:test,:typecheck(false)) function ' + name,
                            '(:typecheck(false)) function ' + name)
source += '''
(:typecheck(false)) class BatchFaultStore extends NativeStore {
 var failKey=null;var fired=false;
 function write(key,value){if(failKey!=null && key.equals(failKey)){fired=true;throw new Lang.InvalidValueException("controlled marker write failure");}NativeStore.write(key,value);}
}
(:test,:typecheck(false)) function batchMarkerFaults(logger){
 var s=new BatchFaultStore();var c=currentCache(s);var now=1794551192l;
 Test.assert(c.accept(CurrentFixture.feed(),now));var seal=c.commit["seal"];
 var batch=new NativeBatch(s,c.base);s.failKey="sf.batch.head";
 var caught=false;try{batch.begin(CurrentFixture.feed());}catch(e){caught=true;}
 Test.assert(caught && s.fired);s.failKey=null;s.fired=false;
 var recovered=new NativeCache(c.base,s);Test.assert(recovered.load(now)!=null && recovered.commit["seal"].equals(seal));
 batch=new NativeBatch(s,c.base);s.failKey="sf.batch.pending";caught=false;
 try{batch.begin(CurrentFixture.feed());}catch(e){caught=true;}
 Test.assert(caught && s.fired);s.failKey=null;s.fired=false;
 Test.assert(batchPending(c));
 batch=new NativeBatch(s,c.base);batch.select(c.packet.bridge);
 var marker=s.read("sf.batch.pending");Test.assert(marker instanceof Dictionary && marker["pending"]==true);
 recovered=new NativeCache(c.base,s);Test.assert(recovered.load(now)!=null && recovered.commit["seal"].equals(seal));
 var fixture=HEAD_LITERAL;var index=INDEX_LITERAL;
 for(var i=0;i<2;i+=1){
   s.remove("sf.batch.head");s.remove("sf.batch.pending");s.remove("sf.batch.refs");
   batch=new NativeBatch(s,c.base);Test.assert(batch.begin(fixture));
   var h=new NativeWireHash();h.put(index);var d=h.digest();
   var catalog=batch.head["catalogDigest"];
   Test.assert(batch.immutable.put({"sha256"=>d,"decodedBytes"=>h.count},index));
   s.failKey=i==0?"sf.batch.head":"sf.batch.pending";s.fired=false;caught=false;
   try{batch.next();}catch(e){caught=true;}
   Test.assert(caught && s.fired);s.failKey=null;s.fired=false;
   Test.assertMessage(batchPending(c),"one durable marker must retain pending work");
   recovered=new NativeCache(c.base,s);Test.assert(recovered.load(now)!=null && recovered.commit["seal"].equals(seal));
   batch=new NativeBatch(s,c.base);Test.assert(batch.next()==null);
   Test.assert(!batchPending(c));
   var finishedHead=s.read("sf.batch.head");var finishedPending=s.read("sf.batch.pending");
   Test.assert(finishedHead["pending"]==false && finishedHead["catalogDigest"].equals(catalog) && finishedHead["transfer"]["sha256"].equals(d));
   Test.assert(finishedPending["pending"]==false && finishedPending["base"].equals(c.base));
   recovered=new NativeCache(c.base,s);Test.assert(recovered.load(now)!=null && recovered.commit["seal"].equals(seal));
 }
 logger.debug("BATCH_MARKER beginHead=1 beginPending=1 completionHead=1 completionPending=1 retry=1 acceptedSealPreserved=1");return true;
}
'''.replace('HEAD_LITERAL', head_literal).replace('INDEX_LITERAL', index_literal)
with patch.object(runtime, 'discover', lambda: linux_probe.context), \
     patch.object(runtime.subprocess, 'check_output', linux_probe.git_info), \
     patch.object(runtime, 'validate_manifest', lambda r, l: ET.parse(r / 'watchface/manifest.xml')):
    result = runtime.build_probe(out, source, group='grammar', tests=True)
result.update({'sourceBinding': 'compare productionSources and productionResources to the checkout',
               'expectedTests': ['batchMarkerFaults'], 'admission': 'diagnostic only'})
(out / 'build.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'exit': result['exitCode'], 'uuid': identity}))
sys.exit(result['exitCode'])
