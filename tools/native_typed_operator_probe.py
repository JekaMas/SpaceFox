"""Compile captured typed-operator and public marker integration assertions."""
import json
from pathlib import Path
from tools.native_full_visual_runtime import GROUPS, build_probe
from tools.spacefox.visual_bridge import canonical_bytes, sha

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/typed_operator'


def pair(mode):
    feed = json.loads((FIXTURE / 'feed.json').read_text())
    catalog = json.loads((FIXTURE / 'catalog.json').read_text())
    operator = feed['launch']['operator_id']
    if mode in ('provider', 'absent'):
        catalog['entries'][operator].pop('abbrev')
    if mode == 'provider':
        feed['launch']['operator_abbrev'] = 'United Launch Alliance'
    if mode == 'wrong':
        value = catalog['entries'][operator].pop('abbrev')
        catalog['entries'][feed['launch']['configuration_id']]['abbrev'] = value
    raw = canonical_bytes(catalog)
    digest = sha(raw)
    feed['catalogDigest'] = digest
    feed['catalogPath'] = 'wire3/catalogs/' + digest + '.json'
    return canonical_bytes(feed).decode(), raw.decode(), digest


def source():
    rows = [pair(x) for x in ('catalog', 'provider', 'absent', 'wrong')]
    cases = []
    for i, (feed, catalog, digest) in enumerate(rows):
        create = 'store.write("sf.obj.'+digest+'",'+json.dumps(catalog,ensure_ascii=False)+');'
        expr = 'new NativeBridgeFeed('+json.dumps(feed,ensure_ascii=False)+',1794631193,store)'
        if i < 3:
            cases.append(create+'var p'+str(i)+'='+expr+';var c'+str(i)+'=feedScene(p'+str(i)+',1794631193);')
        else:
            cases.append(create+'var refused=false;try{'+expr+';}catch(e){refused=true;}')
    return '''import Toybox.Application;import Toybox.Lang;import Toybox.Test;import Toybox.Graphics;
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {function initialize(){SpaceFoxApp.initialize();}}
(:typecheck(false)) class CaptureOperatorRenderer extends SceneRenderer {
 var observed;
 function initialize(){SceneRenderer.initialize(null);observed=[];}
 function text(dc as Graphics.Dc,x as Numeric,y as Numeric,font as Graphics.FontType,value as String,color as Number,width as Number,contour as Number) as String {observed.add(value);return SceneRenderer.text(dc,x,y,font,value,color,width,contour);}
}
(:test,:typecheck(false)) function typedOperatorCombined(logger as Test.Logger) as Boolean {var store=new NativeStore();'''+''.join(cases)+'''
 Test.assert(c0.operatorShort.equals("ULA"));Test.assert(c1.operatorShort.equals("United Launch Alliance"));Test.assert(c2.operatorShort.equals(""));Test.assert(refused);
 Test.assert(c0.point!=null);var settings=new SceneSettings(null);var renderer=new CaptureOperatorRenderer();renderer.prepare(c0,settings);Test.assert(renderer.pin);
 var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390,:colorDepth=>16}).get().getDc();
 Test.assert(dc.getTextWidthInPixels(c0.operator,renderer.fonts["nameSmall"])>100);
 renderer.active(dc,new ClockSnapshot("08:08","T- 00:00:59"),settings,{},new Fitness(),0.0);
 Test.assert(renderer.observed.indexOf("ULA")>=0);logger.debug("typed identity/absence/refusal long-caption=ULA fixed-site-marker=true");return true;}
'''


def build(output):
    GROUPS['typed-combined'] = ('bcac05fab0a84a1ba1985af2dabba69b', 'SpaceFoxTypedCombined.prg')
    result = build_probe(output, source(), group='typed-combined', tests=True)
    result['expectedTests'] = ['typedOperatorCombined']
    (output / 'build.json').write_text(json.dumps(result, indent=2) + '\n')
    return result

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(build(args.output)['exitCode'])
