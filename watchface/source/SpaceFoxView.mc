import Toybox.Complications;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.System;
import Toybox.Timer;

class ClockSnapshot {
    var localTime as String;
    var countdown as String;
    var lowCountdown as String = "--:--";
    var stale as Boolean=false;var rescheduled as Boolean=false;var sourceHold as Boolean=false;
    var date as String or Null=null;
    var localCalendar as Array<Number> or Null=null;
    var battery as String="—";
    function initialize(local as String, launch as String) { localTime=local;countdown=launch; }
}

class SpaceFoxView extends WatchUi.WatchFace {
    private var _clock as WatchClock;
    private var _schedule as ScheduleState;
    const LOW = 0;
    const NOT_LOW = 1;
    private var _mode as Number = LOW;
    // The WatchFace callback controls update cadence; display mode separately
    // permits or forbids the full-power layout.
    private var _awake as Boolean = true;
    private var _shown as Boolean = false;
    private var _resumePending as Boolean = false;
    private var _resumeTimer as Timer.Timer or Null = null;
    var presentation as LocalePresentation;
    var settings as SceneSettings;
    var context as SceneContext or Null;var visualKey as Array or Null=null;
    var packet as NativeFeed or Null=null;
    var downloaded as NativeVisualRenderer or Null=null;
    var assetCache as NativeRenderSource or Null=null;
    var sfrBuild as NativeSfrBuild or Null=null;var sfrTimer as Timer.Timer or Null=null;
    var sceneLifecycle as SceneLifecycle;var sfrGeneration as Number=0;
    var pendingLoader as Method or Null=null;
    var renderer as SceneRenderer or Null;
    var fitness as Fitness;
    var bodyBattery as BodyBatterySource;
    var values as Dictionary<String, Number or Null>;
    var animationProgress as Float = 0.0;
    var animationRunning as Boolean = false;
    var metricsMinute as Long or Null = null;
    var aodMinute as Long or Null = null;
    var fitnessTimer as Timer.Timer or Null=null;
    var restMask as Graphics.BitmapType or Null=null;
    var sceneBuffer as Graphics.BufferedBitmap or Null=null;
    var sceneScaleOptions as Dictionary or Null=null;
    function initialize(clock as WatchClock, schedule as ScheduleState) {
        WatchFace.initialize();_clock=clock;_schedule=schedule;
        presentation=new LocalePresentation();settings=new SceneSettings(null);context=null;renderer=null;fitness=new Fitness();bodyBattery=new BodyBatterySource();values={};sceneLifecycle=new SceneLifecycle();
    }
    function syncDisplayMode(mode as System.DisplayMode) as Void {
        if(mode==System.DISPLAY_MODE_OFF){stopForDisplayOff();return;}
        transitionMode(_awake && mode == System.DISPLAY_MODE_HIGH_POWER ? NOT_LOW : LOW);
    }
    function stopForDisplayOff() as Void {
        _mode=LOW;_resumePending=false;aodMinute=null;metricsMinute=null;
        stopResume();stopAnimation();stopFitness();
        if(sceneLifecycle.job!=null||sfrBuild!=null||sfrTimer!=null){cancelSfrBuild();}
    }
    function displayMode() as Number {return _mode;}
    function transitionMode(next as Number) as Void {
        if (_mode == next) { return; }
        _mode=next;aodMinute=null;metricsMinute=null;
        if (_mode == LOW) { _resumePending=false;stopResume();stopAnimation();cancelSfrBuild();stopFitness(); }
        else { _resumePending=true; }
        WatchUi.requestUpdate();
    }
    function onShow() as Void {
        _shown=true;refreshLocale();syncDisplayMode(System.getDisplayMode());
        if(_mode == NOT_LOW){_resumePending=true;WatchUi.requestUpdate();}
    }
    function stopResume() as Void {if(_resumeTimer!=null){_resumeTimer.stop();_resumeTimer=null;}}
    function resumeAfterFrame() as Void {
        _resumeTimer=null;if(!_shown||_mode!=NOT_LOW||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}
        refreshLocale();if(renderer!=null){(renderer as SceneRenderer).prepareAod();}if(pendingLoader!=null){pendingLoader.invoke();}refreshFitness();prepareVisual();
        if(context!=null){var duration=downloaded==null?2.5:((downloaded as NativeVisualRenderer).duration() as Float);animationRunning=true;WatchUi.animate(self,:animationProgress,WatchUi.ANIM_TYPE_LINEAR,0.0,1.0,duration,method(:animationDone));}
    }
    function queueResumeAfterFrame() as Void {
        if(_shown && _resumePending && _resumeTimer==null){_resumePending=false;_resumeTimer=new Timer.Timer();_resumeTimer.start(method(:resumeAfterFrame),50,false);}
    }
    (:extendedCode)
    function refreshFitness() as Void {
        if(!_shown||!(_mode == NOT_LOW)||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}
        var now=_clock.utcSeconds();var minute=utcMinute(now);var changed=false;
        if(metricsMinute==null||metricsMinute!=minute){
            fitness.selectedRoles=settings.slots;
            if(settings.slots.indexOf("energy")>=0){
                if(!bodyBattery.subscribed){bodyBattery.start(method(:bodyBatteryChanged));}
                if(!bodyBattery.observed||!bodyBattery.subscribed||bodyBattery.value==null){bodyBattery.read();}
                fitness.currentBodyBattery=bodyBattery.value;
            }else{bodyBattery.stop();fitness.currentBodyBattery=null;}
            values=fitness.sample(now);metricsMinute=minute;changed=true;
        }
        if(fitnessTimer==null){fitnessTimer=new Timer.Timer();fitnessTimer.start(method(:refreshFitness),60000,true);}
        if(changed){WatchUi.requestUpdate();}
    }
    function bodyBatteryChanged(id as Complications.Id) as Void {
        if(!_shown||_mode!=NOT_LOW||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER||!bodyBattery.subscribed||settings.slots.indexOf("energy")<0||id.getType()!=Complications.COMPLICATION_TYPE_BODY_BATTERY){return;}
        var previous=values["energy"];var current=bodyBattery.read();fitness.currentBodyBattery=current;values["energy"]=current;
        if(previous!=current){WatchUi.requestUpdate();}
    }
    function stopFitness() as Void {if(fitnessTimer!=null){fitnessTimer.stop();fitnessTimer=null;}bodyBattery.stop();fitness.currentBodyBattery=null;values["energy"]=null;}
    function snapshotAt(now as Number or Long) as ClockSnapshot {
        var remaining=_schedule.remainingSeconds(now);
        var current=new ClockSnapshot(_clock.localTimeText(),CountdownFormat.format(remaining));
        current.lowCountdown=CountdownFormat.minutes(remaining);
        current.date=context==null?null:context.date;current.localCalendar=_clock.localCalendar();current.battery=fitness.display(values,"battery");
        if(context!=null){current.stale=context.stale;current.rescheduled=context.rescheduled;current.sourceHold=context.sourceHold;}
        return current;
    }
    function snapshot() as ClockSnapshot {return snapshotAt(_clock.utcSeconds());}
    (:extendedCode)
    function setSettings(next as SceneSettings) as Void { var rolesChanged=!nativeSame(settings.slots,next.slots);settings=next;if(rolesChanged){metricsMinute=null;}aodMinute=null;presentation.prepare(settings.language);stopAnimation();if(renderer!=null){renderer.prepare(context,settings);(renderer as SceneRenderer).downloaded=downloaded;} if(rolesChanged&&canForegroundWork()){refreshFitness();} }
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
        var sameVisual=key!=null && nativeSame(visualKey,key);
        var retained=downloaded instanceof NativeSfrRenderer&&sameVisual&&downloaded.selectionHash.equals(key[0])?downloaded:null;
        // An accepted same-identity refresh can update schedule metadata while
        // an immutable build is in flight. Retain it only when the transfer and
        // selected source identity both agree and its cache remains admitted.
        var sameTransfer=sameVisual && assetCache!=null && assetCache.ready && assetCache.transferHash!=null &&
            next!=null && next.bridge!=null && next.bridge["transfer"] instanceof Dictionary &&
            next.bridge["transfer"]["sha256"] instanceof String && assetCache.transferHash.equals(next.bridge["transfer"]["sha256"]);
        if(sameTransfer){
            packet=next;var refreshed=feedScene(packet,_clock.utcSeconds());
            if(refreshed!=null && refreshed.launchId.equals("")){refreshed=null;}
            context=refreshed;_schedule=refreshed==null?new ScheduleState(null,"empty"):refreshed.schedule;
            downloaded=retained;if(renderer!=null){renderer.prepare(context,settings);renderer.downloaded=downloaded;}
            packet.compact();return;
        }
        packet=next;downloaded=null;assetCache=null;
        setContext(feedScene(packet,_clock.utcSeconds()));visualKey=key;downloaded=retained;
        if(retained!=null){sceneLifecycle.bindReady();}
        if(renderer!=null){renderer.downloaded=downloaded;}
        if(packet!=null){packet.compact();}
    }
    (:typecheck(false)) function setAssetCache(cache as NativeRenderSource) as Void {
        var newlyReady=cache.ready && (assetCache==null || !assetCache.ready || assetCache.serial!=cache.serial);
        // A newly admitted batch serial can point to the same immutable scene.
        // Keep the one existing job only when namespace, transfer and selection
        // digests all match. Packet/schedule admission remains independent.
        var same=assetCache!=null && assetCache.ready && cache.ready && assetCache.base.equals(cache.base) &&
            assetCache.transferHash!=null && cache.transferHash!=null && assetCache.transferHash.equals(cache.transferHash) &&
            assetCache.selectionHash!=null && cache.selectionHash!=null && assetCache.selectionHash.equals(cache.selectionHash);
        if(newlyReady && assetCache!=null && !same){cancelSfrBuild();}
        assetCache=cache;
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
        if (sceneLifecycle.request(assetCache.serial)) { startSfrTimer(); }
    }
    (:extendedCode)
    function setContext(next as SceneContext or Null) as Void {
        // Same object owns every metadata/time/point/visual field. No cross-ID merge.
        stopAnimation();stopSfrTimer();sfrBuild=null;sceneLifecycle.replace();visualKey=null;downloaded=null;aodMinute=null;
        if(next!=null && next.launchId.equals("")){next=null;}
        context=next;_schedule=next==null?new ScheduleState(null,"empty"):next.schedule;
        if(renderer!=null){renderer.prepare(context,settings);(renderer as SceneRenderer).downloaded=downloaded;if(_mode==LOW){(renderer as SceneRenderer).prepareAod();}}
    }
    function canForegroundWork() as Boolean {return _shown&&(_mode == NOT_LOW)&&!_resumePending&&_resumeTimer==null&&System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER;}
    function canAcceptBackground() as Boolean {return _shown&&System.getDisplayMode()!=System.DISPLAY_MODE_OFF&&(!_awake||canForegroundWork());}
    (:typecheck(false))
    // Keep the last accepted scene while its durable packet is revalidated.
    // The packet is detached for the parser, but its presentation and qualified
    // visual remain the only visible scene until a replacement is admitted.
    function clearForRestore() as Void {
        if(packet!=null && context!=null){context.stale=packet.stale;context.rescheduled=packet.rescheduled;}
        packet=null;
    }
    function prepareRenderer() as Void {renderer=new SceneRenderer(presentation);renderer.prepare(context,settings);(renderer as SceneRenderer).downloaded=downloaded;if(_mode==LOW){(renderer as SceneRenderer).prepareAod();}}
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
    function onUpdate(dc as Graphics.Dc) as Void {updateForDisplayMode(dc,System.getDisplayMode());}
    (:typecheck(false)) function updateForDisplayMode(dc as Graphics.Dc, displayMode as System.DisplayMode) as Void {
        // OFF is not a third layout. Stop any owned work without scheduling a
        // redraw or loading resources; a later HIGH observation resumes after
        // its first frame, and LOW never starts active sampling or decoding.
        if(displayMode==System.DISPLAY_MODE_OFF){
            stopForDisplayOff();return;
        }
        // Garmin may deliver a draw before the corresponding sleep callback.
        syncDisplayMode(displayMode);
        // Skip the entire LOW update, including mask and scaled-buffer blit.
        if(!(_mode == NOT_LOW) && aodMinute!=null && aodMinute==utcMinute(_clock.utcSeconds())){return;}
        if(sceneBuffer!=null){var bitmap=sceneBuffer as Graphics.BufferedBitmap;var target=bitmap.getDc();drawScene(target);applyPixelRest(target);dc.drawBitmap2(0,0,bitmap,sceneScaleOptions);if(_mode==NOT_LOW&&renderer!=null){queueResumeAfterFrame();}return;}
        drawScene(dc);applyPixelRest(dc);
        if(_mode==NOT_LOW&&renderer!=null){queueResumeAfterFrame();}
    }
    function applyPixelRest(dc as Graphics.Dc) as Void {
        if((_mode == NOT_LOW)||restMask==null){return;}
        var minute=utcMinute(_clock.utcSeconds());var phase=((minute%4+4)%4).toNumber();
        dc.drawBitmap(-(phase%2),-(phase/2),restMask as Graphics.BitmapType);
    }
    function drawScene(dc as Graphics.Dc) as Void {
        var now=_clock.utcSeconds();var minute=utcMinute(now);
        if(!(_mode == NOT_LOW) && aodMinute!=null && aodMinute==minute){return;}
        // One inexpensive system battery read per permitted LOW snapshot.
        // Do not start the active health sampler or any timer in LOW.
        if(!(_mode == NOT_LOW)){try{values["battery"]=fitness.number(System.getSystemStats().battery,100);}catch(e){values["battery"]=null;}}
        // Renderer release is synchronous; retain the last frame if an OS draw
        // arrives before its rebind rather than rendering a separate mode.
        if(renderer==null){return;}
        if(packet!=null){(packet as NativeFeed).advance(now);if(context!=null){(context as SceneContext).stale=(packet as NativeFeed).stale as Boolean;}}
        var current=snapshotAt(now);
        var drawing=renderer as SceneRenderer;
        if((_mode == NOT_LOW)){drawing.active(dc,current,settings,values,fitness,animationProgress);}
        else{current.countdown=current.lowCountdown;drawing.aod(dc,current,minute,settings);aodMinute=minute;}
    }
    function stopAnimation() as Void{
        if(animationRunning){WatchUi.cancelAllAnimations();}
        animationRunning=false;animationProgress=0.0;
    }
    function animationDone() as Void{animationRunning=false;animationProgress=0.0;WatchUi.requestUpdate();}
    function onEnterSleep() as Void { _awake=false;var display=System.getDisplayMode();syncDisplayMode(display);if(display!=System.DISPLAY_MODE_OFF&&renderer!=null){(renderer as SceneRenderer).prepareAod();} }
    function onExitSleep() as Void { _awake=true;var display=System.getDisplayMode();syncDisplayMode(display);if(display!=System.DISPLAY_MODE_OFF){WatchUi.requestUpdate();} }
    function onHide() as Void {_shown=false;_resumePending=false;stopResume();stopAnimation();cancelSfrBuild();stopFitness();}
    (:typecheck(false))
    // Fixed SDK-minimum cadence; repeated preparation cannot postpone a pending
    // slice. Each decoder slice still has its existing18ms/16row work budget.
    function startSfrTimer() as Void {if(!_shown||!(_mode == NOT_LOW)||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}if(sfrTimer==null){sfrTimer=new Timer.Timer();sfrTimer.start(method(:sfrStep),50,true);}}
    (:typecheck(false))
    function stopSfrTimer() as Void {if(sfrTimer!=null){sfrTimer.stop();sfrTimer=null;}}
    (:typecheck(false))
    function cancelSfrBuild() as Void {
        stopSfrTimer();sfrBuild=null;sceneLifecycle.cancel();
    }
    (:typecheck(false))
    function sfrStep() as Void {

        if (System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER) { cancelSfrBuild(); return; }
        if (!_shown || !(_mode == NOT_LOW) || packet==null || packet.bridge==null || !sceneLifecycle.pending()) { stopSfrTimer(); return; }
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
                    WatchUi.requestUpdate();
                }
            }
        } catch(e) {

            sfrBuild=null;stopSfrTimer();sceneLifecycle.fail(sfrGeneration);WatchUi.requestUpdate();
        }
    }

}
