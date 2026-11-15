"""Current renderer preserves source context and draws explicit absence."""
import json, sys, uuid
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0] = ['/task', '/task/source']
import linux_probe
from tools import native_full_visual_runtime as runtime
from tools import generate_native_current_tests as gen

out = Path('/task/output/context-header')
out.mkdir(parents=True, exist_ok=True)
runtime.GROUPS['grammar'] = (uuid.uuid4().hex, 'CF7.prg')
source = 'import Toybox.Graphics;\n' + gen.source(Path('/task/profile-a'))
for name in gen.EXPECTED:
    source = source.replace('(:test,:typecheck(false)) function ' + name,
                            '(:typecheck(false)) function ' + name)
source += '''
(:typecheck(false)) class HeaderRecorder extends SceneRenderer {
 var rows={};
 function initialize(){SceneRenderer.initialize(null);}
 function text(dc as Graphics.Dc,x as Numeric,y as Numeric,font as Graphics.FontType,value as String,color as Number,width as Number,contour as Number) as String {
  var shown=SceneRenderer.text(dc,x,y,font,value,color,width,contour);rows[y]=shown;return shown;
 }
}
(:test,:typecheck(false)) function currentSourceHeader(logger){
 var s=new CurrentStore();var p=currentPacket(s);var ctx=feedScene(p,1794551192l);
 Test.assert(ctx.rocket.equals("Starship V3") && ctx.operator.equals("SpaceX") && ctx.purpose.equals("Communications"));
 var settings=new SceneSettings(null);var recorder=new HeaderRecorder();var bitmap=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();
 recorder.prepare(ctx,settings);recorder.active(bitmap.getDc(),new ClockSnapshot("08:08","--:--:--"),settings,{},new Fitness(),0.0);
 Test.assert(recorder.rows[70].equals("Communications"));
 // Controlled mapping seam: actual packet parsed first; these explicit nulls
 // do not claim that modified packet bytes passed wire admission.
 var l=p.document["launch"];l["configuration_id"]=null;l["configuration_name"]=null;
 l["operator_id"]=null;l["operator_name"]=null;l["operator_abbrev"]=null;l["mission_purpose"]=null;
 p.catalogOperatorShort=null;ctx=feedScene(p,1794551192l);
 Test.assert(ctx.rocket.equals("") && ctx.operator.equals("") && ctx.purpose.equals(""));
 recorder=new HeaderRecorder();recorder.prepare(ctx,settings);recorder.active(bitmap.getDc(),new ClockSnapshot("08:08","--:--:--"),settings,{},new Fitness(),0.0);
 Test.assert(recorder.rows[47].equals("—") && recorder.rows[70].equals("—"));
 logger.debug("SOURCE_HEADER capturedContext=1 missingOperatorPurposeMarkers=1 noPriorBorrow=1");return true;
}
'''
with patch.object(runtime, 'discover', lambda: linux_probe.context), \
     patch.object(runtime.subprocess, 'check_output', linux_probe.git_info), \
     patch.object(runtime, 'validate_manifest', lambda r, l: ET.parse(r / 'watchface/manifest.xml')):
    result = runtime.build_probe(out, source, group='grammar', tests=True)
result.update({'sourceBinding': 'compare productionSources and productionResources to the checkout',
               'expectedTests': ['currentSourceHeader'], 'admission': 'diagnostic only'})
(out / 'build.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'exit': result['exitCode']}))
sys.exit(result['exitCode'])
