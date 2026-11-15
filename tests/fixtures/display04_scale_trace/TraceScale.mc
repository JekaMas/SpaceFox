import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;

// Observe the actual SpaceFoxView buffer and transform path, not a substitute
// renderer. This unit uses test memory and says nothing about watch heap.
(:test,:typecheck(false)) class D04ScaleView extends SpaceFoxView {
 var actualWidth=0;var actualHeight=0;
 function initialize(){SpaceFoxView.initialize(new WatchClock(),new ScheduleState(null,"empty"));}
 function drawScene(dc){actualWidth=dc.getWidth();actualHeight=dc.getHeight();SpaceFoxView.drawScene(dc);}
}
(:test,:typecheck(false)) function display04Actual454ScaleTrace(logger){
 var outer=Graphics.createBufferedBitmap({:width=>454,:height=>454,:colorDepth=>16}).get();var dc=outer.getDc();var view=new D04ScaleView();view.onLayout(dc);
 Test.assert(view.sceneBuffer!=null&&view.sceneScaleOptions!=null);
 var logical=view.sceneBuffer;var transform=view.sceneScaleOptions[:transform];var end=transform.transformPoint([390.0,390.0]);
 view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);
 logger.debug("D04_SCALE|target="+dc.getWidth()+"x"+dc.getHeight()+"|buffer="+logical.getWidth()+"x"+logical.getHeight()+"|draw="+view.actualWidth+"x"+view.actualHeight+"|end="+end[0]+","+end[1]+"|filter="+view.sceneScaleOptions[:filterMode]);
 Test.assert(dc.getWidth()==454&&dc.getHeight()==454&&logical.getWidth()==390&&logical.getHeight()==390&&view.actualWidth==390&&view.actualHeight==390);
 Test.assert(end[0]>453.99&&end[0]<454.01&&end[1]>453.99&&end[1]<454.01&&view.sceneScaleOptions[:filterMode]==Graphics.FILTER_MODE_POINT);
 return true;
}
