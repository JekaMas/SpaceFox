import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Test;
import Toybox.WatchUi;

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
(:test) function currentFinite0(logger as Test.Logger) as Boolean {return CurrentFiniteProbe.run(logger,[Rez.JsonData.CurrentFinite0,Rez.JsonData.CurrentFinite1,Rez.JsonData.CurrentFinite2,Rez.JsonData.CurrentFinite3,Rez.JsonData.CurrentFinite4,Rez.JsonData.CurrentFinite5,Rez.JsonData.CurrentFinite6,Rez.JsonData.CurrentFinite7,Rez.JsonData.CurrentFinite8,Rez.JsonData.CurrentFinite9,Rez.JsonData.CurrentFinite10,Rez.JsonData.CurrentFinite11,Rez.JsonData.CurrentFinite12,Rez.JsonData.CurrentFinite13,Rez.JsonData.CurrentFinite14,Rez.JsonData.CurrentFinite15],1035);}
(:test) function currentFinite1(logger as Test.Logger) as Boolean {return CurrentFiniteProbe.run(logger,[Rez.JsonData.CurrentFinite16,Rez.JsonData.CurrentFinite17,Rez.JsonData.CurrentFinite18,Rez.JsonData.CurrentFinite19,Rez.JsonData.CurrentFinite20,Rez.JsonData.CurrentFinite21,Rez.JsonData.CurrentFinite22,Rez.JsonData.CurrentFinite23,Rez.JsonData.CurrentFinite24,Rez.JsonData.CurrentFinite25,Rez.JsonData.CurrentFinite26,Rez.JsonData.CurrentFinite27,Rez.JsonData.CurrentFinite28,Rez.JsonData.CurrentFinite29,Rez.JsonData.CurrentFinite30,Rez.JsonData.CurrentFinite31],377);}
(:test) function currentFinite2(logger as Test.Logger) as Boolean {return CurrentFiniteProbe.run(logger,[Rez.JsonData.CurrentFinite32,Rez.JsonData.CurrentFinite33,Rez.JsonData.CurrentFinite34,Rez.JsonData.CurrentFinite35,Rez.JsonData.CurrentFinite36,Rez.JsonData.CurrentFinite37,Rez.JsonData.CurrentFinite38,Rez.JsonData.CurrentFinite39,Rez.JsonData.CurrentFinite40,Rez.JsonData.CurrentFinite41,Rez.JsonData.CurrentFinite42,Rez.JsonData.CurrentFinite43,Rez.JsonData.CurrentFinite44,Rez.JsonData.CurrentFinite45,Rez.JsonData.CurrentFinite46,Rez.JsonData.CurrentFinite47],298);}
(:test) function currentFinite3(logger as Test.Logger) as Boolean {return CurrentFiniteProbe.run(logger,[Rez.JsonData.CurrentFinite48,Rez.JsonData.CurrentFinite49,Rez.JsonData.CurrentFinite50,Rez.JsonData.CurrentFinite51],112);}
(:test,:typecheck(false)) class CurrentPaintRenderer extends SceneRenderer {
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
(:test) function currentRenderer0(logger as Test.Logger) as Boolean {return CurrentRendererProbe.run(logger,[Rez.JsonData.CurrentFinite0,Rez.JsonData.CurrentFinite1,Rez.JsonData.CurrentFinite2,Rez.JsonData.CurrentFinite3,Rez.JsonData.CurrentFinite4,Rez.JsonData.CurrentFinite5,Rez.JsonData.CurrentFinite6,Rez.JsonData.CurrentFinite7,Rez.JsonData.CurrentFinite8,Rez.JsonData.CurrentFinite9,Rez.JsonData.CurrentFinite10,Rez.JsonData.CurrentFinite11,Rez.JsonData.CurrentFinite12,Rez.JsonData.CurrentFinite13,Rez.JsonData.CurrentFinite14,Rez.JsonData.CurrentFinite15],1035);}
(:test) function currentRenderer1(logger as Test.Logger) as Boolean {return CurrentRendererProbe.run(logger,[Rez.JsonData.CurrentFinite16,Rez.JsonData.CurrentFinite17,Rez.JsonData.CurrentFinite18,Rez.JsonData.CurrentFinite19,Rez.JsonData.CurrentFinite20,Rez.JsonData.CurrentFinite21,Rez.JsonData.CurrentFinite22,Rez.JsonData.CurrentFinite23,Rez.JsonData.CurrentFinite24,Rez.JsonData.CurrentFinite25,Rez.JsonData.CurrentFinite26,Rez.JsonData.CurrentFinite27,Rez.JsonData.CurrentFinite28,Rez.JsonData.CurrentFinite29,Rez.JsonData.CurrentFinite30,Rez.JsonData.CurrentFinite31],377);}
(:test) function currentRenderer2(logger as Test.Logger) as Boolean {return CurrentRendererProbe.run(logger,[Rez.JsonData.CurrentFinite32,Rez.JsonData.CurrentFinite33,Rez.JsonData.CurrentFinite34,Rez.JsonData.CurrentFinite35,Rez.JsonData.CurrentFinite36,Rez.JsonData.CurrentFinite37,Rez.JsonData.CurrentFinite38,Rez.JsonData.CurrentFinite39,Rez.JsonData.CurrentFinite40,Rez.JsonData.CurrentFinite41,Rez.JsonData.CurrentFinite42,Rez.JsonData.CurrentFinite43,Rez.JsonData.CurrentFinite44,Rez.JsonData.CurrentFinite45,Rez.JsonData.CurrentFinite46,Rez.JsonData.CurrentFinite47],298);}
(:test) function currentRenderer3(logger as Test.Logger) as Boolean {return CurrentRendererProbe.run(logger,[Rez.JsonData.CurrentFinite48,Rez.JsonData.CurrentFinite49,Rez.JsonData.CurrentFinite50,Rez.JsonData.CurrentFinite51],112);}
