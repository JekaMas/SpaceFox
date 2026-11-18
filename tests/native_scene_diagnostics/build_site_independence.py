"""Directed scene mapping of unknown model/operator versus qualified site."""
import json, sys, uuid
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0] = ['/task', '/task/source']
import linux_probe
from tools import native_full_visual_runtime as runtime
from tools import generate_native_current_tests as gen

out = Path('/task/output/site-independence')
out.mkdir(parents=True, exist_ok=True)
runtime.GROUPS['grammar'] = (uuid.uuid4().hex, 'CF5.prg')
source = gen.source(Path('/task/profile-a'))
for name in gen.EXPECTED:
    source = source.replace('(:test,:typecheck(false)) function ' + name,
                            '(:typecheck(false)) function ' + name)
source += '''
(:test,:typecheck(false)) function siteIndependentOfModel(logger){
 var s=new CurrentStore();var p=currentPacket(s);var l=p.document["launch"];
 // Controlled mapping seam: the valid captured site is parsed first; unknown
 // model/operator fields below are test-only mutations, not parser evidence.
 l["configuration_id"]=null;l["configuration_name"]=null;
 l["operator_id"]=null;l["operator_name"]=null;l["operator_abbrev"]=null;
 var ctx=feedScene(p,1794551192l);Test.assert(ctx.point!=null);
 Test.assert(ctx.point[0]==-97.15799f && ctx.point[1]==25.99677f);
 var renderer=new SceneRenderer(null);renderer.prepare(ctx,new SceneSettings(null));
 Test.assert(renderer.pin && renderer.model==Rez.Drawables.Art_unknown);
 p.bridge["site"]["position"]=null;ctx=feedScene(p,1794551192l);
 renderer.prepare(ctx,new SceneSettings(null));Test.assert(ctx.point==null && !renderer.pin);
 p.bridge["site"]["position"]={"longitude"=>"-97.15799","latitude"=>"26.99677"};
 ctx=feedScene(p,1794551192l);renderer.prepare(ctx,new SceneSettings(null));
 Test.assert(ctx.point!=null && !renderer.pin);
 logger.debug("SITE_INDEPENDENCE unknownModelOperator=1 qualifiedOwnPoint=1 matchingMarker=1 missingNoPoint=1 unmatchedNoMarker=1");return true;
}
'''
with patch.object(runtime, 'discover', lambda: linux_probe.context), \
     patch.object(runtime.subprocess, 'check_output', linux_probe.git_info), \
     patch.object(runtime, 'validate_manifest', lambda r, l: ET.parse(r / 'watchface/manifest.xml')):
    result = runtime.build_probe(out, source, group='grammar', tests=True)
result.update({'sourceBinding': 'compare productionSources and productionResources to the checkout',
               'expectedTests': ['siteIndependentOfModel'], 'admission': 'diagnostic only'})
(out / 'build.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'exit': result['exitCode']}))
sys.exit(result['exitCode'])
