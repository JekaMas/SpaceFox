import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Test;
import Toybox.System;
import Toybox.WatchUi;

(:test,:typecheck(false)) class PhysicalRocketTrace {
 var positions=[];var clips=[];
 function setClip(x,y,w,h){clips.add([x,y,w,h]);}
 function clearClip(){}
 function drawBitmap(x,y,bitmap){positions.add([x,y,bitmap]);}
}
(:test,:typecheck(false)) function physicalRocketNeverMoves(logger){
 var renderer=new NativeVisualRenderer();renderer.bitmap="the-same-bitmap";var trace=new PhysicalRocketTrace();
 renderer.draw(trace,0.0,0);renderer.draw(trace,0.5,9);renderer.draw(trace,1.0,0);
 Test.assert(trace.positions.size()==3&&trace.clips.size()==3);
 for(var i=0;i<3;i+=1){Test.assert(trace.positions[i][0]==22&&trace.positions[i][1]==118&&trace.positions[i][2].equals("the-same-bitmap"));Test.assert(trace.clips[i][0]==22&&trace.clips[i][1]==118&&trace.clips[i][2]==54&&trace.clips[i][3]==124);}
 logger.debug("downloaded rocket uses one fixed frame regardless of timeline");return true;
}

(:test,:typecheck(false)) class PhysicalFrameTrace {
 var questions=0;var unknown=0;var polygons=0;var bitmapMarkers=0;var circles=0;var expectedMarker=null;var art=null;var artPositions=[];
 function setColor(a,b){} function clear(){} function fillRectangle(x,y,w,h){}
 function drawBitmap(x,y,b){if(expectedMarker!=null&&b==expectedMarker){bitmapMarkers+=1;}if(art!=null&&b==art){artPositions.add([x,y]);}}
 function drawBitmap2(x,y,b,opt){} function fillCircle(x,y,r){if(r==4||r==7){circles+=1;}}
 function fillPolygon(p){polygons+=1;} function drawCircle(x,y,r){} function drawLine(x1,y1,x2,y2){}
 function getTextWidthInPixels(value,font){return value.length()*8;}
 function drawText(x,y,font,value,flags){if(value.equals("?")){questions+=1;}if(value.equals("Unknown")){unknown+=1;}}
}
(:test,:typecheck(false)) function physicalTaiyuanActiveLowTrace(logger){
 var scene=new SceneContext({"id"=>"ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60","rocket"=>"Long March 2D","operator"=>"CASC","purpose"=>"Unknown","site"=>"CN · Taiyuan","modelId"=>"ll2:configuration:17","point"=>[111.589567,38.863128],"pointText"=>["111.589567","38.863128"],"target"=>1795042200,"precision"=>"exact"});
 var settings=new SceneSettings(null);var renderer=new SceneRenderer(null);renderer.prepare(scene,settings);renderer.prepareAod();
 Test.assert(renderer.artResource==NativeModels.resource("ll2:configuration:17")&&renderer.artResource!=Rez.Drawables.Art_unknown);
 var clock=new ClockSnapshot("08:25","T- 00:10:00");clock.localCalendar=[3,17,11];var values={"steps"=>null,"heart"=>null,"energy"=>null,"stress"=>null,"battery"=>null,"calories"=>null};
 var active=new PhysicalFrameTrace();active.expectedMarker=renderer.marker;active.art=renderer.art;
 renderer.active(active,clock,settings,values,new Fitness(),0.0f);renderer.active(active,clock,settings,values,new Fitness(),0.5f);renderer.active(active,clock,settings,values,new Fitness(),1.0f);
 Test.assert(active.bitmapMarkers==3&&active.questions==0&&active.unknown==0&&active.polygons==0&&active.artPositions.size()==3);
 for(var i=0;i<3;i+=1){Test.assert(active.artPositions[i][0]==42&&active.artPositions[i][1]==120);}
 var low=new PhysicalFrameTrace();renderer.aod(low,clock,0l,settings);Test.assert(low.circles>=2&&low.questions==0&&low.unknown==0);
 logger.debug("Taiyuan active/LOW marker; static LM2D bitmap, no Unknown, question or flame");return true;
}

(:test,:typecheck(false)) function physicalLargestModelResourceHeap(logger){
 var beforeStats=System.getSystemStats();var before=beforeStats.totalMemory-beforeStats.usedMemory;
 // Representative Falcon Heavy resource: source canvas is 54x124; its
 // lossless cropped bounds are 22x120 and retain their generated anchor.
 var image=WatchUi.loadResource(NativeModels.resource("ll2:configuration:161"));
 Test.assert(image!=null&&image.getWidth()==22&&image.getHeight()==120);
 var afterStats=System.getSystemStats();var after=afterStats.totalMemory-afterStats.usedMemory;
 Test.assert(after>=0&&afterStats.totalMemory==beforeStats.totalMemory);
 logger.debug("MODEL_HEAP free_before="+before+" free_after="+after+" source_canvas=54x124 cropped=22x120; instantaneous samples, not peak");return true;
}

(:test,:typecheck(false)) function anchoredModelFrame(logger){
 physicalTaiyuanActiveLowTrace(logger);physicalLargestModelResourceHeap(logger);
 logger.debug("ANCHORED_MODEL exact_lm2d_origin=42,120 falcon_heavy_crop=22x120");return true;
}
