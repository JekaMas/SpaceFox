"""Bounded EN/RU HTTP-text regression observer; no physical claim or provider call."""
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import argparse,json
from tools.native_full_visual_runtime import IMPORTS,GROUPS,build_probe
UUID='f015b626c9a740ca9a6235b326b476b1'
GROUP='phone-015'
BASE='https://phone-015.invalid'

def source():
 return IMPORTS+'''import Toybox.Timer;
import Toybox.Graphics;
(:typecheck(false)) class PhoneClock extends WatchClock {var now=1794540000l;function utcSeconds(){return now;}function localTimeText(){return "08:08";}}
(:typecheck(false)) class PhoneDrawing extends SceneRenderer {
 var app;var recording=false;function initialize(a,p){SceneRenderer.initialize(p);app=a;}
 function text(dc as Graphics.Dc,x as Numeric,y as Numeric,font as Graphics.FontType,value as String,color as Number,width as Number,contour as Number) as String {
  var shown=SceneRenderer.text(dc,x,y,font,value,color,width,contour);
  if(recording){var kind=font==fonts["time"]?"time":font==fonts["metric"]?"metric":font==fonts["battery"]?"battery":"vector";System.println("PHONE_TEXT|"+app.frame+"|"+kind+"|"+x+"|"+y+"|"+dc.getTextWidthInPixels(shown,font)+"|"+dc.getFontHeight(font)+"|"+color+"|"+shown);if(kind.equals("metric")||kind.equals("battery")){app.ensure(shown.equals(value),"numeric truncation "+value);}}
  return shown;
 }
}
(:typecheck(false)) class PhoneProxy extends WatchUi.WatchFace {var app;function initialize(a){WatchFace.initialize();app=a;}function onLayout(dc){app.view.onLayout(dc);}function onShow(){app.view.onShow();}function onHide(){app.view.onHide();}function onUpdate(dc){app.view.onUpdate(dc);app.drawn(dc);}}
(:background,:typecheck(false)) class PhoneService extends FeedService {
 function requestUrl(path as String) as String {var logical=FeedService.requestUrl(path);var actual="http://127.0.0.1:18795"+logical.substring("https://phone-015.invalid".length(),logical.length());System.println("PHONE_HTTP logical="+path+" actual="+actual);return actual;}
}
(:background,:extendedCode,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 var observer=null;var clock=null;var rich=null;var sourceContext=null;var frame=-1;var recorded=false;var checks=0;
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled=true;}
 function ensure(ok,message){if(!ok){throw new Lang.InvalidValueException("PHONE_015 "+message);}}
 function getServiceDelegate(){return [new PhoneService()];}
 (:typecheck(disableBackgroundCheck)) function getInitialView(){Application.Properties.setValue("FeedBaseUrl","https://phone-015.invalid");clock=new PhoneClock();view=new SpaceFoxView(clock,new ScheduleState(null,"unknown"));view.setSettings(new SceneSettings(null).load());feed=new NativeCache(configuredFeedUrl(),null);feed.load(Time.now().value().toLong());NativeForegroundApp.display(self,feed);view.pendingLoader=method(:begin);view.syncDisplayMode(System.getDisplayMode());var transfer=new NativeTransfer(configuredFeedUrl(),null);transfer.load();armFeed(transfer,Time.now().value().toLong());return [new PhoneProxy(self)];}
 (:typecheck(disableBackgroundCheck)) function begin(){SpaceFoxApp.reloadFeed();checks=0;if(observer==null){observer=new Timer.Timer();}observer.start(method(:ready),100,false);}
 (:typecheck(disableBackgroundCheck)) function onBackgroundData(data as Application.PersistableType) as Void {SpaceFoxApp.onBackgroundData(data);checks=0;if(observer==null){observer=new Timer.Timer();}observer.start(method(:ready),100,false);}
 (:typecheck(disableBackgroundCheck)) function ready(){checks+=1;if(view.downloaded==null||view.sfrBuild!=null||view.sfrRequested){if(checks<500){observer.start(method(:ready),100,false);}return;}Background.deleteTemporalEvent();ensure(System.getSystemStats().totalMemory==126784,"ordinary heap");rich=view.downloaded;sourceContext=view.context;ensure(rich.mapBitmap!=null&&rich.bitmap!=null,"complete actual HTTP visual");System.println("PHONE_HTTP_COMPLETE packet=true map=true rocket=true ordinaryBytes=126784");frame=0;applyFrame();}
 (:typecheck(disableBackgroundCheck)) function onDisplayModeChanged(){var high=System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER;SpaceFoxApp.onDisplayModeChanged();if(high&&rich!=null&&frame>=0&&frame<8){frame+=1;applyFrame();}}
 (:typecheck(disableBackgroundCheck)) function applyFrame(){
  var phase=frame%4;var russian=frame>=4;Application.Properties.setValue("Language",russian?1:0);Application.Properties.setValue("CountdownColor",phase==0?0:3);var sets=[[0,1,2,3],[4,5,0,1]];var roles=sets[phase%2];for(var i=0;i<4;i+=1){Application.Properties.setValue("Field"+(i+1),roles[i]);}view.setSettings(new SceneSettings(null).load());Background.deleteTemporalEvent();
  sourceContext.schedule=new ScheduleState(phase==1||phase==2?null:clock.now+176523l,phase==1||phase==2?"unknown":"minute");sourceContext.rescheduled=frame==8;sourceContext.stale=false;view.setContext(sourceContext);view.downloaded=rich;view.packet=null;view.renderer=new PhoneDrawing(self,view.presentation);view.renderer.prepare(sourceContext,view.settings);view.renderer.downloaded=rich;
  view.values={"steps"=>12345,"energy"=>68,"heart"=>72,"stress"=>47,"calories"=>2345,"battery"=>82};view.animationProgress=0.0;view.stopAnimation();view.visualMaintenance=phase==2;
  if(phase==2){view.maintenanceTimeFont=view.renderer.fonts["time"];view.maintenanceMetricFont=view.renderer.fonts["metric"];view.maintenanceIcons=view.renderer.icons;}
  if(phase==3){view.setContext(null);view.renderer.prepare(null,view.settings);view.renderer.syncStatus="feedFailed";view.renderer.syncDetail="-400";view.syncStatus="feedFailed";view.syncDetail="-400";}
  recorded=false;WatchUi.requestUpdate();
 }
 function drawn(dc){if(frame<0||recorded||view.renderer==null){return;}var drawing=view.renderer;drawing.recording=true;view.onUpdate(dc);drawing.recording=false;recorded=true;var expected=frame%4==0?0x7fe7c6:0xcdb7ff;ensure(view.settings.countdownColor==expected,"persisted countdown color");System.println("PHONE_FRAME_READY frame="+frame+" language="+view.presentation.locale+" phase="+(frame%4)+" configured="+view.settings.countdownColor+" countdown="+view.snapshot().countdown+" maintenance="+view.visualMaintenance+" ordinary="+System.getSystemStats().totalMemory);}
}
'''

def build(out,mode):
 GROUPS[GROUP]=(UUID,'SpaceFoxPhone015.prg')
 program=source()
 if mode=='unit':
  GROUPS[GROUP]=('a015b626c9a740ca9a6235b326b476b1','SpaceFoxPhone015Unit.prg')
  program=IMPORTS+'(:background) class SfrRuntimeApp extends SpaceFoxApp {function initialize(){SpaceFoxApp.initialize();}}\n'+(Path(__file__).resolve().parents[1]/'watchface/incident-tests/FirstInstallTests.mc').read_text()
 with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
  result=build_probe(out,program,group=GROUP,tests=mode=='unit')
 result['admissionValidation']='pending-phone-delta-diagnostic-build'
 if mode=='unit':result['expectedTests']=['firstInstallDefaultsAndRetry','phoneTextTransportAndColors']
 (out/'build.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['observer','unit']);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(build(a.output,a.mode)['exitCode'])
