#!/usr/bin/env python3
"""Prepare a bounded current-native finite-corpus fit probe (no network)."""
import argparse
from collections import Counter
import json
from pathlib import Path
from tools.display_corpus import load_complete_corpus

ROOT = Path(__file__).resolve().parents[1]


def build_resource_plan(corpus):
    """Pure canonical resource plan; no SDK, private paths or business effects."""
    strings = corpus['strings']
    groups = Counter(tuple(None if i is None else strings[i] for i in row[3]) for row in corpus['launches'])
    rows = [[*fields, count] for fields, count in sorted(groups.items(), key=lambda x: json.dumps(x[0], ensure_ascii=False))]
    resources = {}
    names = []
    for offset in range(0, len(rows), 8):
        name = 'CurrentFinite' + str(len(names)); names.append(name)
        resources[name + '.json'] = json.dumps(rows[offset:offset+8], ensure_ascii=False, separators=(',', ':')).encode()
    resources['resources.xml'] = ('<resources>' + ''.join('<jsonData id="'+n+'" filename="'+n+'.json"/>' for n in names) + '</resources>').encode()
    return rows, names, resources


def probe_source(rows, names):
    code = '''import Toybox.Graphics;\nimport Toybox.Lang;\nimport Toybox.Test;\nimport Toybox.WatchUi;\n
(:test,:typecheck(false)) module CurrentFiniteProbe {
 function run(logger,refs,expected) as Boolean {
  var p=new LocalePresentation();var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();var count=0;
  for(var i=0;i<refs.size();i+=1){var rows=WatchUi.loadResource(refs[i]);
   for(var j=0;j<rows.size();j+=1){var row=rows[j];
    for(var k=0;k<4;k+=1){if(row[k]!=null && !row[k].equals("")){
     var font=(k==0||k==3)?p.label:p.latinSmall;var width=k==0?122:(k==1?238:(k==2?282:242));
     var result=p.fit(dc,row[k],font,width);Test.assert(!result.equals("")&&dc.getTextWidthInPixels(result,font)<=width);
     if(!result.equals(row[k])){Test.assert(result.substring(result.length()-1,result.length()).equals("…"));}
    }}count+=row[4];}rows=null;}
  logger.debug("CURRENT_FINITE records="+count+" expected="+expected);return count==expected;
 }
}
'''
    # Each selector owns an independent resource subset; the totals are literal
    # corpus-derived weights and collectively cover every enumerated launch.
    for index, start in enumerate(range(0, len(names), 16)):
        subset = names[start:start+16]
        expected = sum(row[4] for row in rows[start*8:(start+len(subset))*8])
        refs = ','.join('Rez.JsonData.' + name for name in subset)
        code += '(:test) function currentFinite%d(logger as Test.Logger) as Boolean {return CurrentFiniteProbe.run(logger,[%s],%d);}\n' % (index, refs, expected)
    code += """(:test,:typecheck(false)) class CurrentPaintRenderer extends SceneRenderer {
 var paints=[];
 function initialize(p){SceneRenderer.initialize(p);}
 function text(dc,x,y,font,value,color,width,contour){
  var result=SceneRenderer.text(dc,x,y,font,value,color,width,contour);paints.add([x,y,result]);return result;
 }
}
(:test,:typecheck(false)) module CurrentRendererProbe {
 function run(logger,refs,expected) as Boolean {
  var p=new LocalePresentation();var renderer=new CurrentPaintRenderer(p);var settings=new SceneSettings(null);
  renderer.prepare(new SceneContext({"id"=>"seed"}),settings);
  var fitness=new Fitness();var values={"steps"=>12345,"energy"=>0,"heart"=>null,"stress"=>47,"battery"=>82,"calories"=>0};
  var clock=new ClockSnapshot("08:08","T- 02:00:00");
  var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();var count=0;var compositions=0;var headerPaints=0;
  for(var i=0;i<refs.size();i+=1){var rows=WatchUi.loadResource(refs[i]);
   for(var j=0;j<rows.size();j+=1){var row=rows[j];
    for(var k=0;k<4;k+=1){if(row[k]!=null&&!row[k].equals("")){
     var font=(k==0||k==3)?p.label:p.latinSmall;var width=k==0?122:(k==1?238:(k==2?282:242));
     var result=p.fit(dc,row[k],font,width);Test.assert(!result.equals("")&&dc.getTextWidthInPixels(result,font)>0&&dc.getTextWidthInPixels(result,font)<=width);
     if(!result.equals(row[k])){Test.assert(result.substring(result.length()-1,result.length()).equals("…")&&row[k].find(result.substring(0,result.length()-1))==0);}
    }}
    var rocket=row[0]==null?"":row[0];var operator=row[1]==null?"":row[1];
    var context=new SceneContext({"id"=>"finite","rocket"=>rocket,"operator"=>operator,"purpose"=>row[2]==null?"":row[2],"site"=>row[3]==null?"":row[3]});
    Test.assert(context.rocket.equals(rocket)&&context.operator.equals(operator));
    renderer.fullContext=context;renderer.paints=[];renderer.active(dc,clock,settings,values,fitness,0.0);
    var expectedOperator=operator.equals("")?"—":operator;
    Test.assert(rocket.equals("")?renderer.layoutRocket.equals(""):!renderer.layoutRocket.equals("")&&renderer.layoutRocketWidth>0);
    Test.assert(!renderer.layoutOperator.equals("")&&renderer.layoutOperatorWidth>0);
    Test.assert(renderer.layoutRocketInput.equals(rocket)&&renderer.layoutOperatorInput.equals(operator));
    var outputs=[renderer.layoutRocket,renderer.layoutOperator];var sources=[rocket,expectedOperator];
    for(var q=0;q<2;q+=1){var shown=outputs[q];if(!shown.equals(sources[q])){Test.assert(!shown.equals("")&&shown.substring(shown.length()-1,shown.length()).equals("…")&&sources[q].find(shown.substring(0,shown.length()-1))==0);}}
    Test.assert(renderer.layoutRocketWidth+renderer.layoutOperatorWidth+renderer.layoutGap>0&&renderer.layoutRocketWidth+renderer.layoutOperatorWidth+renderer.layoutGap<=238);
    Test.assert(renderer.layoutGap==(rocket.equals("")?0:16));
    Test.assert(renderer.layoutLeft>=76&&renderer.layoutLeft+renderer.layoutRocketWidth+renderer.layoutOperatorWidth+renderer.layoutGap<=314);
    var titlePaint=false;var operatorPaint=false;
    for(var z=0;z<renderer.paints.size();z+=1){var paint=renderer.paints[z];if(paint[1]==43&&paint[2].equals(renderer.layoutRocket)){titlePaint=true;}if(paint[1]==47&&paint[2].equals(renderer.layoutOperator)){operatorPaint=true;}}
    Test.assert(titlePaint&&operatorPaint);headerPaints+=1;compositions+=1;count+=row[4];}rows=null;}
  logger.debug("CURRENT_JOINED records="+count+" expected="+expected+" compositions="+compositions+" header_paints="+headerPaints+" nonempty=true projection=true");return count==expected;
 }
}
"""
    for index, start in enumerate(range(0, len(names), 16)):
        subset = names[start:start+16]
        expected = sum(row[4] for row in rows[start*8:(start+len(subset))*8])
        refs = ','.join('Rez.JsonData.' + name for name in subset)
        code += '(:test) function currentRenderer%d(logger as Test.Logger) as Boolean {return CurrentRendererProbe.run(logger,[%s],%d);}\n' % (index, refs, expected)
    return code


def generate(output):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    corpus = load_complete_corpus(ROOT / 'corpus/real-schedule-basic-five-20261113/display-corpus.json')
    rows, names, payloads = build_resource_plan(corpus)
    resources = output / 'resources'; resources.mkdir(exist_ok=True)
    for name, raw in payloads.items(): (resources / name).write_bytes(raw)
    (output / 'CurrentFinite.mc').write_text(probe_source(rows, names))
    print(json.dumps({'records': len(corpus['launches']), 'compositions': len(rows), 'selectors': (len(names)+15)//16, 'resources': len(names)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    generate(parser.parse_args().output)
