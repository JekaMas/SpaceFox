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
    var context as SceneContext or Null;
    var packet as NativeFeed or Null=null;
    var downloaded as NativeVisualRenderer or Null=null;
    var assetCache as NativeRenderSource or Null=null;var assetTried as Boolean=false;
    var sfrBuild as NativeSfrBuild or Null=null;var sfrTimer as Timer.Timer or Null=null;
    var sfrRequested as Boolean=false;var visualMaintenance as Boolean=false;var fallbackPainted as Boolean=false;
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
    var maintenanceSecond as Long or Null=null;
    var restoreStatus as Boolean=false;var restoreStale as Boolean=false;var restoreRescheduled as Boolean=false;
    var maintenanceIcons as Dictionary<String,Graphics.BitmapType> or Null=null;
    var maintenanceTimeFont as Graphics.FontType or Null=null;
    var maintenanceCountFont as Graphics.FontType or Null=null;
    var maintenanceMetricFont as Graphics.FontType or Null=null;
    var maintenanceAodFont as Graphics.FontType or Null=null;
    var restMask as Graphics.BitmapType or Null=null;
    var sceneBuffer as Graphics.BufferedBitmap or Null=null;
    var sceneScaleOptions as Dictionary or Null=null;
    function initialize(clock as WatchClock, schedule as ScheduleState) {
        WatchFace.initialize();_clock=clock;_schedule=schedule;
        presentation=new LocalePresentation();settings=new SceneSettings(null);context=null;renderer=null;fitness=new Fitness();values={};
    }
    function syncDisplayMode(mode as System.DisplayMode) as Void { _active=mode==System.DISPLAY_MODE_HIGH_POWER;aodMinute=null;metricsMinute=null;if(!_active){stopAnimation();cancelSfrBuild();stopFitness();}else{refreshFitness();}if(NativeMetrics.enabled){System.println("NATIVE_DISPLAY mode="+mode+" active="+_active+" bitmap="+(downloaded!=null)+" decoding="+(sfrBuild!=null)+" ms="+System.getTimer()+" owner="+NativeMetrics.ownerTag);}WatchUi.requestUpdate(); }
    function onShow() as Void {_shown=true;refreshLocale();if(pendingLoader!=null){pendingLoader.invoke();}if(_active){refreshFitness();}}
    (:extendedCode)
    function refreshFitness() as Void {if(!_active){return;}var now=_clock.utcSeconds();var minute=utcMinute(now);if(metricsMinute==null||metricsMinute!=minute){values=fitness.sample(now);metricsMinute=minute;}if(_shown&&fitnessTimer==null){fitnessTimer=new Timer.Timer();fitnessTimer.start(method(:refreshFitness),60000,true);}WatchUi.requestUpdate();}
    function stopFitness() as Void {if(fitnessTimer!=null){fitnessTimer.stop();fitnessTimer=null;}}
    function snapshot() as ClockSnapshot {var now=_clock.utcSeconds();var current=new ClockSnapshot(_clock.localTimeText(),_schedule.display(now,_active));current.remaining=_schedule.remainingSeconds(now);current.date=context==null?null:context.date;current.localCalendar=_clock.localCalendar();current.battery=fitness.display(values,"battery");return current;}
    (:extendedCode)
    function setSettings(next as SceneSettings) as Void { settings=next;aodMinute=null;presentation.prepare(settings.language);stopAnimation();if(renderer!=null){renderer.prepare(context,settings);(renderer as SceneRenderer).downloaded=downloaded;} }
    function refreshLocale() as Void {var previous=settings.language;settings.refreshLanguage();if(!previous.equals(settings.language)){setSettings(settings);}}
    (:extendedCode, :typecheck(false))
    function setPacket(next) as Void {restoreStatus=false;var retained=downloaded instanceof NativeSfrRenderer&&next!=null&&next.bridge!=null&&next.bridge["version"]==3&&next.bridge["selection"]!=null&&downloaded.selectionHash.equals(next.bridge["selection"]["sha256"])?downloaded:null;packet=next;downloaded=null;assetCache=null;assetTried=false;setContext(feedScene(packet,_clock.utcSeconds()));downloaded=retained;if(renderer!=null){renderer.downloaded=downloaded;}if(packet!=null){packet.compact();}}
    function setAssetCache(cache as NativeRenderSource) as Void {assetCache=cache;assetTried=false;}
    (:extendedCode, :typecheck(false))
    function prepareVisual() as Void {
        if(!_shown){return;}
        if(sfrBuild!=null||sfrRequested){startSfrTimer();return;}
        if(assetTried||assetCache==null||packet==null){return;}assetTried=true;NativeMetrics.sample("visual-activation-start");
        if(packet.bridge!=null&&packet.bridge["selection"]!=null&&!(downloaded instanceof NativeSfrRenderer&&downloaded.selectionHash.equals(packet.bridge["selection"]["sha256"]))){sfrRequested=true;startSfrTimer();}
    }
    (:extendedCode)
    function setContext(next as SceneContext or Null) as Void {
        // Same object owns every metadata/time/point/visual field. No cross-ID merge.
        stopAnimation();stopSfrTimer();sfrBuild=null;sfrRequested=false;visualMaintenance=false;fallbackPainted=false;downloaded=null;aodMinute=null;
        if(next!=null && next.launchId.equals("")){next=null;}
        context=next;_schedule=next==null?new ScheduleState(null,"empty"):next.schedule;
        if(renderer!=null){renderer.prepare(context,settings);(renderer as SceneRenderer).downloaded=downloaded;}
    }
    function canForegroundWork() as Boolean {return _shown&&_active;}
    (:typecheck(false))
    function clearForRestore() as Void {var schedule=_schedule;var accepted=context;var stale=packet!=null?packet.stale:(context!=null&&context.stale);var rescheduled=packet!=null?packet.rescheduled:(context!=null&&context.rescheduled);setPacket(null);context=accepted;_schedule=schedule;restoreStatus=true;restoreStale=stale;restoreRescheduled=rescheduled;visualMaintenance=true;releaseRenderer();}
    function setSyncStatus(value as String,detail as String) as Void {syncStatus=value;syncDetail=detail;if(renderer!=null){renderer.syncStatus=value;renderer.syncDetail=detail;}}
    function prepareRenderer() as Void { maintenanceIcons=null;maintenanceTimeFont=null;maintenanceCountFont=null;maintenanceMetricFont=null;renderer=new SceneRenderer(presentation);renderer.prepare(context,settings);maintenanceAodFont=(renderer as SceneRenderer).fonts["aod"];(renderer as SceneRenderer).downloaded=downloaded;(renderer as SceneRenderer).syncStatus=syncStatus;(renderer as SceneRenderer).syncDetail=syncDetail; }
    function releaseRenderer() as Void {stopAnimation();if(renderer!=null){maintenanceIcons=renderer.icons;}renderer=null;}
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
        if(visualMaintenance||renderer==null){maintenance(dc);if(!_active){aodMinute=minute;}return;}
        if(packet!=null){(packet as NativeFeed).advance(now);if(context!=null){(context as SceneContext).stale=(packet as NativeFeed).stale as Boolean;}}
        var current=new ClockSnapshot(_clock.localTimeText(),_schedule.display(now,_active));current.remaining=_schedule.remainingSeconds(now);current.date=context==null?null:context.date;current.localCalendar=_clock.localCalendar();current.battery=fitness.display(values,"battery");
        if(packet!=null){current.stale=(packet as NativeFeed).stale as Boolean;current.rescheduled=(packet as NativeFeed).rescheduled as Boolean;}else if(restoreStatus){current.stale=restoreStale;current.rescheduled=restoreRescheduled;}
        var drawing=renderer as SceneRenderer;
        if(_active){drawing.active(dc,current,settings,values,fitness,animationProgress);fallbackPainted=true;}
        else{drawing.aod(dc,current,minute,settings);aodMinute=minute;}
    }
    // Resident built-in fonts keep the clock/countdown and four cached fields
    // live while the reconstructible full renderer is released for admission.
    // No network, storage, health sampling, parser or resource construction here.
    function maintenance(dc as Graphics.Dc) as Void {
        var now=_clock.utcSeconds();var current=context;var selected=packet;var stale=restoreStatus?restoreStale:current!=null&&current.stale;var rescheduled=restoreStatus?restoreRescheduled:current!=null&&current.rescheduled;if(selected!=null){selected.advance(now);stale=selected.stale;rescheduled=selected.rescheduled;}var remaining=_schedule.remainingSeconds(now);var snapshot=new ClockSnapshot(_clock.localTimeText(),_schedule.display(now,_active));snapshot.remaining=remaining;snapshot.date=context==null?null:context.date;snapshot.localCalendar=_clock.localCalendar();snapshot.battery=fitness.display(values,"battery");snapshot.stale=stale as Boolean;snapshot.rescheduled=rescheduled as Boolean;
        // Failed admission may wait here until HIGH. Keep the same sparse AOD
        // geometry/font/phase and minute guard as the complete-renderer path.
        if(!_active){SceneAod.draw(dc,snapshot,utcMinute(now),presentation,maintenanceAodFont==null?Graphics.FONT_XTINY:maintenanceAodFont,settings);return;}
        var count=presentation.countdown(snapshot,true);
        dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();dc.setColor(settings.clockColor,Graphics.COLOR_TRANSPARENT);
        if(snapshot.localCalendar!=null){dc.setColor(0xD4DFEB,Graphics.COLOR_TRANSPARENT);dc.drawText(195,95,presentation.calendarFont as Graphics.FontType,presentation.calendar(snapshot.localCalendar as Array<Number>),Graphics.TEXT_JUSTIFY_CENTER);}
        dc.setColor(settings.clockColor,Graphics.COLOR_TRANSPARENT);dc.drawText(195,109,maintenanceTimeFont==null?Graphics.FONT_NUMBER_MILD:maintenanceTimeFont,_clock.localTimeText(),Graphics.TEXT_JUSTIFY_CENTER);
        var countFont=(dc.getTextWidthInPixels(count,presentation.count as Graphics.FontType)>275?presentation.small:presentation.count) as Graphics.FontType;count=presentation.fit(dc,count,countFont,275);dc.setColor(rescheduled?0xF3C37A:settings.countdownColor,Graphics.COLOR_TRANSPARENT);dc.drawText(195,202,countFont,count,Graphics.TEXT_JUSTIFY_CENTER);if(stale){var width=dc.getTextWidthInPixels(count,countFont);if(width>275){width=275;}for(var dot=195-width/2;dot<195+width/2;dot+=5){dc.fillCircle(dot,237,1);}}
        if(context!=null){dc.setColor(0xd4dfeb,Graphics.COLOR_TRANSPARENT);dc.setClip(42,48,306,54);dc.drawText(195,50,presentation.small as Graphics.FontType,presentation.fit(dc,context.rocket,presentation.small,306),Graphics.TEXT_JUSTIFY_CENTER);dc.clearClip();}
        if(_active){for(var i=0;i<4;i+=1){var role=settings.slots[i];var font=maintenanceMetricFont==null?Graphics.FONT_LARGE:maintenanceMetricFont;var label=presentation.fit(dc,presentation.metric(fitness,values,role),font,128);var width=dc.getTextWidthInPixels(label,font);var left=i%2==0?55:335-width;if(i==2&&role.equals("battery")){left+=18;}var rowTop=i<2?244:282;if(maintenanceIcons!=null&&maintenanceIcons.hasKey(role)){dc.drawBitmap(left-(role.equals("battery")?31:25),rowTop+(role.equals("battery")?2:5),maintenanceIcons[role] as Graphics.BitmapType);}dc.setColor(settings.fieldColors[i],Graphics.COLOR_TRANSPARENT);dc.drawText(left+width/2,rowTop-4,font,label,Graphics.TEXT_JUSTIFY_CENTER);}for(var stage=0;stage<4;stage+=1){dc.setColor(sfrBuild!=null&&stage<sfrBuild.role?0x7fe7c6:0x334e5c,Graphics.COLOR_TRANSPARENT);dc.fillRectangle(148+stage*25,355,18,3);}}
    }
    function stopAnimation() as Void{
        if(animationRunning){WatchUi.cancelAllAnimations();}
        animationRunning=false;animationProgress=0.0;
    }
    function animationDone() as Void{animationRunning=false;animationProgress=0.0;WatchUi.requestUpdate();}
    function onEnterSleep() as Void {if(NativeMetrics.enabled){System.println("NATIVE_LIFECYCLE sleep bitmap="+(downloaded!=null)+" decoding="+(sfrBuild!=null)+" ms="+System.getTimer()+" owner="+NativeMetrics.ownerTag);}_active=false;stopAnimation();cancelSfrBuild();stopFitness();aodMinute=null;WatchUi.requestUpdate();}
    function onExitSleep() as Void {
        refreshLocale();
        if(downloaded==null&&statusLoader!=null){statusLoader.invoke();}
        if(NativeMetrics.enabled){System.println("NATIVE_LIFECYCLE wake bitmap="+(downloaded!=null)+" decoding="+(sfrBuild!=null)+" ms="+System.getTimer()+" owner="+NativeMetrics.ownerTag);}_active=true;aodMinute=null;metricsMinute=null;refreshFitness();prepareVisual();
        if(_shown&&context!=null){var duration=downloaded==null?2.5:((downloaded as NativeVisualRenderer).duration() as Float);animationRunning=true;WatchUi.animate(self,:animationProgress,WatchUi.ANIM_TYPE_LINEAR,0.0,1.0,duration,method(:animationDone));}
        WatchUi.requestUpdate();
    }
    function onHide() as Void {_shown=false;stopAnimation();cancelSfrBuild();stopFitness();}
    (:typecheck(false))
    // Fixed SDK-minimum cadence; repeated preparation cannot postpone a pending
    // slice. Each decoder slice still has its existing18ms/16row work budget.
    function startSfrTimer() as Void {if(!_shown||!_active||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}if(sfrTimer==null){sfrTimer=new Timer.Timer();sfrTimer.start(method(:sfrStep),50,true);}}
    (:typecheck(false))
    function stopSfrTimer() as Void {if(sfrTimer!=null){sfrTimer.stop();sfrTimer=null;}}
    (:typecheck(false))
    function cancelSfrBuild() as Void {stopSfrTimer();sfrBuild=null;sfrRequested=false;assetTried=false;if(visualMaintenance){visualMaintenance=false;prepareRenderer();}}
    (:typecheck(false))
    function sfrStep() as Void {
        NativeMetrics.sample("sfr-step-enter");
        if(System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){cancelSfrBuild();return;}
        if(!_shown||!_active||packet==null||packet.bridge==null||(!sfrRequested&&sfrBuild==null)){stopSfrTimer();return;}
        try{
            if(sfrBuild==null){if(!fallbackPainted){startSfrTimer();return;}visualMaintenance=true;if(renderer!=null){maintenanceTimeFont=renderer.fonts["time"];maintenanceCountFont=renderer.fonts["count"];maintenanceMetricFont=renderer.fonts["metric"];}releaseRenderer();NativeMetrics.sample("sfr-renderer-released");sfrBuild=new NativeSfrBuild(assetCache.store,assetCache.base,packet);startSfrTimer();return;}
            if(sfrBuild.step()){stopSfrTimer();downloaded=sfrBuild.result;sfrBuild=null;sfrRequested=false;visualMaintenance=false;prepareRenderer();NativeMetrics.sample("sfr-full-scene-active");WatchUi.requestUpdate();}else{var second=_clock.utcSeconds().toLong();if(maintenanceSecond==null||maintenanceSecond!=second){maintenanceSecond=second;WatchUi.requestUpdate();}startSfrTimer();}
        }catch(e){NativeMetrics.failure(e.getErrorMessage());if(NativeMetrics.enabled){e.printStackTrace();}sfrBuild=null;sfrRequested=false;stopSfrTimer();if(visualMaintenance){visualMaintenance=false;prepareRenderer();}WatchUi.requestUpdate();}
    }
}
