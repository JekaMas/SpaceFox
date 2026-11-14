import Toybox.Graphics;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.System;
import Toybox.Timer;

class ClockSnapshot {
    var localTime as String;
    var countdown as String;
    var stale as Boolean=false;var rescheduled as Boolean=false;
    var date as String or Null=null;
    var localCalendar as Array<Number> or Null=null;
    var battery as String="—";
    var remaining as Number or Long or Null=null;
    function initialize(local as String, launch as String) { localTime=local;countdown=launch; }
}

class SpaceFoxView extends WatchUi.WatchFace {
    private var _clock as WatchClock;
    private var _schedule as ScheduleState;
    private var _active as Boolean = false;
    private var _shown as Boolean = false;
    var presentation as LocalePresentation;
    var settings as SceneSettings;
    var context as SceneContext or Null;var visualKey as Array or Null=null;
    var packet as NativeFeed or Null=null;
    var downloaded as NativeVisualRenderer or Null=null;
    var assetCache as NativeRenderSource or Null=null;
    var sfrBuild as NativeSfrBuild or Null=null;var sfrTimer as Timer.Timer or Null=null;
    var sceneLifecycle as SceneLifecycle;var sfrGeneration as Number=0;
    var pendingLoader as Method or Null=null;
    var statusLoader as Method or Null=null;
    var renderer as SceneRenderer or Null;
    var syncStatus as String="waiting";
    var syncDetail as String="";
    var fitness as Fitness;
    var values as Dictionary<String, Number or Null>;
    var animationProgress as Float = 0.0;
    var animationRunning as Boolean = false;
    var metricsMinute as Long or Null = null;
    var aodMinute as Long or Null = null;
    var fitnessTimer as Timer.Timer or Null=null;
    var restoreStatus as Boolean=false;var restoreStale as Boolean=false;var restoreRescheduled as Boolean=false;
    var restMask as Graphics.BitmapType or Null=null;
    var sceneBuffer as Graphics.BufferedBitmap or Null=null;
    var sceneScaleOptions as Dictionary or Null=null;
    function initialize(clock as WatchClock, schedule as ScheduleState) {
        WatchFace.initialize();_clock=clock;_schedule=schedule;
        presentation=new LocalePresentation();settings=new SceneSettings(null);context=null;renderer=null;fitness=new Fitness();values={};sceneLifecycle=new SceneLifecycle();
    }
    function syncDisplayMode(mode as System.DisplayMode) as Void {
        if (mode==System.DISPLAY_MODE_HIGH_POWER) { setActive(true); }
        else if (mode==System.DISPLAY_MODE_LOW_POWER || mode==System.DISPLAY_MODE_OFF) { setActive(false); }
    }
    function setActive(active as Boolean) as Void {
        if (_active==active) { return; }
        _active=active;aodMinute=null;metricsMinute=null;
        if (!active) { stopAnimation();cancelSfrBuild();stopFitness(); }
        else {
            refreshLocale();
            if(downloaded==null&&statusLoader!=null){statusLoader.invoke();}
            refreshFitness();prepareVisual();
            if(_shown&&context!=null){var duration=downloaded==null?2.5:((downloaded as NativeVisualRenderer).duration() as Float);animationRunning=true;WatchUi.animate(self,:animationProgress,WatchUi.ANIM_TYPE_LINEAR,0.0,1.0,duration,method(:animationDone));}
        }
        if(NativeMetrics.enabled){System.println("NATIVE_DISPLAY active="+_active+" bitmap="+(downloaded!=null)+" decoding="+(sfrBuild!=null)+" ms="+System.getTimer()+" owner="+NativeMetrics.ownerTag);}
        WatchUi.requestUpdate();
    }
    function onShow() as Void {_shown=true;refreshLocale();if(pendingLoader!=null){pendingLoader.invoke();}if(_active){refreshFitness();}}
    (:extendedCode)
    function refreshFitness() as Void {if(!_active){return;}var now=_clock.utcSeconds();var minute=utcMinute(now);if(metricsMinute==null||metricsMinute!=minute){values=fitness.sample(now);metricsMinute=minute;}if(_shown&&fitnessTimer==null){fitnessTimer=new Timer.Timer();fitnessTimer.start(method(:refreshFitness),60000,true);}WatchUi.requestUpdate();}
    function stopFitness() as Void {if(fitnessTimer!=null){fitnessTimer.stop();fitnessTimer=null;}}
    function snapshot() as ClockSnapshot {var now=_clock.utcSeconds();var current=new ClockSnapshot(_clock.localTimeText(),_schedule.display(now,_active));current.remaining=_schedule.remainingSeconds(now);current.date=context==null?null:context.date;current.localCalendar=_clock.localCalendar();current.battery=fitness.display(values,"battery");return current;}
    (:extendedCode)
    function setSettings(next as SceneSettings) as Void { settings=next;aodMinute=null;presentation.prepare(settings.language);stopAnimation();if(renderer!=null){renderer.prepare(context,settings);(renderer as SceneRenderer).downloaded=downloaded;} }
    function refreshLocale() as Void {var previous=settings.language;settings.refreshLanguage();if(!previous.equals(settings.language)){setSettings(settings);}}
    (:extendedCode, :typecheck(false))
    // The scene digest binds selected art/map identity; bridge IDs and exact
    // qualified site data prevent reusing a visual for changed model or place.
    function packetVisualKey(next) {
        if(next==null||next.bridge==null||next.bridge["selection"]==null){return null;}
        return [next.bridge["selection"]["sha256"],next.bridge["ids"],next.bridge["site"]];
    }
    (:extendedCode, :typecheck(false))
    function setPacket(next) as Void {
        var key=packetVisualKey(next);
        var retained=downloaded instanceof NativeSfrRenderer&&key!=null&&nativeSame(visualKey,key)&&downloaded.selectionHash.equals(key[0])?downloaded:null;
        restoreStatus=false;packet=next;downloaded=null;assetCache=null;
        setContext(feedScene(packet,_clock.utcSeconds()));visualKey=key;downloaded=retained;
        if(retained!=null){sceneLifecycle.bindReady();}
        if(renderer!=null){renderer.downloaded=downloaded;}
        if(packet!=null){packet.compact();}
    }
    function setAssetCache(cache as NativeRenderSource) as Void {
        var newlyReady=cache.ready && (assetCache==null || !assetCache.ready || assetCache.serial!=cache.serial);
        assetCache=cache;if(newlyReady){sceneLifecycle.allowRetry();}
    }
    (:extendedCode, :typecheck(false))
    function prepareVisual() as Void {
        if (!_shown || assetCache == null || !assetCache.ready || packet == null || packet.bridge == null) { return; }
        if (sceneLifecycle.pending()) { startSfrTimer(); return; }
        var selection=packet.bridge["selection"];
        if (selection == null) { return; }
        if (downloaded instanceof NativeSfrRenderer && downloaded.selectionHash.equals(selection["sha256"])) {
            sceneLifecycle.bindReady(); return;
        }
        if (sceneLifecycle.request()) { startSfrTimer(); }
    }
    (:extendedCode)
    function setContext(next as SceneContext or Null) as Void {
        // Same object owns every metadata/time/point/visual field. No cross-ID merge.
        stopAnimation();stopSfrTimer();sfrBuild=null;sceneLifecycle.replace(next!=null);visualKey=null;downloaded=null;aodMinute=null;
        if(next!=null && next.launchId.equals("")){next=null;}
        context=next;_schedule=next==null?new ScheduleState(null,"empty"):next.schedule;
        if(renderer!=null){renderer.prepare(context,settings);(renderer as SceneRenderer).downloaded=downloaded;}
    }
    function canForegroundWork() as Boolean {return _shown&&_active;}
    (:typecheck(false))
    // Keep the last accepted scene while its durable packet is revalidated.
    // The packet is detached for the parser, but its presentation and qualified
    // visual remain the only visible scene until a replacement is admitted.
    function clearForRestore() as Void {restoreStale=packet!=null?packet.stale:(context!=null&&context.stale);restoreRescheduled=packet!=null?packet.rescheduled:(context!=null&&context.rescheduled);packet=null;restoreStatus=true;}
    function setSyncStatus(value as String,detail as String) as Void {syncStatus=value;syncDetail=detail;if(renderer!=null){renderer.syncStatus=value;renderer.syncDetail=detail;}}
    function prepareRenderer() as Void {renderer=new SceneRenderer(presentation);renderer.prepare(context,settings);(renderer as SceneRenderer).downloaded=downloaded;(renderer as SceneRenderer).syncStatus=syncStatus;(renderer as SceneRenderer).syncDetail=syncDetail;}
    function releaseRenderer() as Void {stopAnimation();renderer=null;}
    function onLayout(dc as Graphics.Dc) as Void {
        prepareRenderer();
        if(restMask==null){restMask=WatchUi.loadResource(Rez.Drawables.AodRestMask) as Graphics.BitmapType;}
        // Render the complete 390px design into one canvas before scaling:
        // map, points, dynamic raster, foreground, fonts and maintenance stay
        // in the same coordinate system on larger supported round screens.
        if((dc.getWidth()!=390||dc.getHeight()!=390)&&sceneBuffer==null){sceneBuffer=Graphics.createBufferedBitmap({:width=>390,:height=>390,:colorDepth=>16}).get() as Graphics.BufferedBitmap;var scale=new Graphics.AffineTransform();scale.scale(dc.getWidth().toFloat()/390.0,dc.getHeight().toFloat()/390.0);sceneScaleOptions={:transform=>scale,:filterMode=>Graphics.FILTER_MODE_POINT};}
    }
    function utcMinute(now as Number or Long) as Long {
        var seconds=now.toLong();var minute=seconds/60;
        if(seconds<0 && seconds%60!=0){minute-=1;}
        return minute;
    }
    (:typecheck(false)) function onUpdate(dc as Graphics.Dc) as Void {
        // Skip the entire LOW update, including mask and scaled-buffer blit.
        if(!_active && aodMinute!=null && aodMinute==utcMinute(_clock.utcSeconds())){return;}
        if(sceneBuffer!=null){var bitmap=sceneBuffer as Graphics.BufferedBitmap;var target=bitmap.getDc();drawScene(target);applyPixelRest(target);dc.drawBitmap2(0,0,bitmap,sceneScaleOptions);return;}
        drawScene(dc);applyPixelRest(dc);
    }
    function applyPixelRest(dc as Graphics.Dc) as Void {
        if(_active||restMask==null){return;}
        var minute=utcMinute(_clock.utcSeconds());var phase=((minute%4+4)%4).toNumber();
        dc.drawBitmap(-(phase%2),-(phase/2),restMask as Graphics.BitmapType);
    }
    function drawScene(dc as Graphics.Dc) as Void {
        var now=_clock.utcSeconds();var minute=utcMinute(now);
        if(!_active && aodMinute!=null && aodMinute==minute){return;}
        // One inexpensive system battery read per permitted LOW snapshot.
        // Do not start the active health sampler or any timer in LOW.
        if(!_active){try{values["battery"]=fitness.number(System.getSystemStats().battery,100);}catch(e){values["battery"]=null;}}
        // Renderer release is synchronous; retain the last frame if an OS draw
        // arrives before its rebind rather than rendering a separate mode.
        if(renderer==null){return;}
        if(packet!=null){(packet as NativeFeed).advance(now);if(context!=null){(context as SceneContext).stale=(packet as NativeFeed).stale as Boolean;}}
        var current=new ClockSnapshot(_clock.localTimeText(),_schedule.display(now,_active));current.remaining=_schedule.remainingSeconds(now);current.date=context==null?null:context.date;current.localCalendar=_clock.localCalendar();current.battery=fitness.display(values,"battery");
        if(packet!=null){current.stale=(packet as NativeFeed).stale as Boolean;current.rescheduled=(packet as NativeFeed).rescheduled as Boolean;}else if(restoreStatus){current.stale=restoreStale;current.rescheduled=restoreRescheduled;}
        var drawing=renderer as SceneRenderer;
        if(_active){drawing.active(dc,current,settings,values,fitness,animationProgress);sceneLifecycle.painted();}
        else{drawing.aod(dc,current,minute,settings);aodMinute=minute;}
    }
    function stopAnimation() as Void{
        if(animationRunning){WatchUi.cancelAllAnimations();}
        animationRunning=false;animationProgress=0.0;
    }
    function animationDone() as Void{animationRunning=false;animationProgress=0.0;WatchUi.requestUpdate();}
    function onEnterSleep() as Void { setActive(false); }
    function onExitSleep() as Void { setActive(true); }
    function onHide() as Void {_shown=false;stopAnimation();cancelSfrBuild();stopFitness();}
    (:typecheck(false))
    // Fixed SDK-minimum cadence; repeated preparation cannot postpone a pending
    // slice. Each decoder slice still has its existing18ms/16row work budget.
    function startSfrTimer() as Void {if(!_shown||!_active||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}if(sfrTimer==null){sfrTimer=new Timer.Timer();sfrTimer.start(method(:sfrStep),50,true);}}
    (:typecheck(false))
    function stopSfrTimer() as Void {if(sfrTimer!=null){sfrTimer.stop();sfrTimer=null;}}
    (:typecheck(false))
    function cancelSfrBuild() as Void {
        stopSfrTimer();sfrBuild=null;sceneLifecycle.cancel();
    }
    (:typecheck(false))
    function sfrStep() as Void {
        NativeMetrics.sample("sfr-step-enter");
        if (System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER) { cancelSfrBuild(); return; }
        if (!_shown || !_active || packet==null || packet.bridge==null || !sceneLifecycle.pending()) { stopSfrTimer(); return; }
        try {
            if (sfrBuild==null) {
                var token=sceneLifecycle.begin();
                if (token==null) { return; }
                sfrGeneration=token;
                sfrBuild=new NativeSfrBuild(assetCache.store,assetCache.base,packet);
                return;
            }
            if (sfrBuild.step()) {
                var result=sfrBuild.result;stopSfrTimer();sfrBuild=null;
                if (sceneLifecycle.complete(sfrGeneration)) {
                    downloaded=result;if(renderer!=null){renderer.downloaded=downloaded;}
                    NativeMetrics.sample("sfr-full-scene-active");WatchUi.requestUpdate();
                }
            }
        } catch(e) {
            NativeMetrics.failure(e.getErrorMessage());if(NativeMetrics.enabled){e.printStackTrace();}
            sfrBuild=null;stopSfrTimer();sceneLifecycle.fail(sfrGeneration);WatchUi.requestUpdate();
        }
    }

}
