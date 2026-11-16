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
    var admissionPending as Boolean=false;
    var upcoming as Array = [];
    var passedSelections as Array = [];
    var downloaded as NativeVisualRenderer or Null=null;
    var assetCache as NativeRenderSource or Null=null;
    var sfrBuild as NativeSfrBuild or Null=null;var sfrTimer as Timer.Timer or Null=null;
    var sceneLifecycle as SceneLifecycle;var sfrGeneration as Number=0;
    var pendingLoader as Method or Null=null;
    var renderer as SceneRenderer or Null;
    var fitness as Fitness;
    var selectedFields as SelectedFields;
    var values as Dictionary<String, Number or Null>;
    var animationProgress as Float = 0.0;
    var animationRunning as Boolean = false;
    var metricsMinute as Long or Null = null;
    var aodMinute as Long or Null = null;
    var fitnessTimer as Timer.Timer or Null=null;
    var restMask as Graphics.BitmapType or Null=null;
    var sceneBuffer as Graphics.BufferedBitmap or Null=null;
    var sceneScaleOptions as Dictionary or Null=null;
    var sceneWidth as Number=0;var sceneHeight as Number=0;var sceneX as Number=0;var sceneY as Number=0;
    function initialize(clock as WatchClock, schedule as ScheduleState) {
        WatchFace.initialize();_clock=clock;_schedule=schedule;
        presentation=new LocalePresentation();settings=new SceneSettings(null);context=null;renderer=null;fitness=new Fitness();selectedFields=new SelectedFields();fitness.selectedFields=selectedFields;values={};sceneLifecycle=new SceneLifecycle();
    }
    function syncDisplayMode(mode as System.DisplayMode) as Void {
        if(mode==System.DISPLAY_MODE_OFF){stopForDisplayOff();return;}
        transitionMode(_awake && mode == System.DISPLAY_MODE_HIGH_POWER ? NOT_LOW : LOW);
    }
    function stopForDisplayOff() as Void {
        _mode=LOW;_resumePending=false;aodMinute=null;metricsMinute=null;restMask=null;if(renderer!=null){(renderer as SceneRenderer).releaseAod();}
        stopResume();stopAnimation();stopFitness();
        if(sceneLifecycle.job!=null||sfrBuild!=null||sfrTimer!=null){cancelSfrBuild();}
    }
    function displayMode() as Number {return _mode;}
    function transitionMode(next as Number) as Void {
        if (_mode == next) { return; }
        _mode=next;aodMinute=null;metricsMinute=null;System.println("SF_VIEW mode="+(_mode==LOW?"LOW":"HIGH")+" pending="+admissionPending);
        if (_mode == LOW) { _resumePending=false;stopResume();stopAnimation();cancelSfrBuild();stopFitness();if(renderer!=null){(renderer as SceneRenderer).prepareAod();} }
        else { restMask=null;if(renderer!=null){(renderer as SceneRenderer).releaseAod();}_resumePending=true; }
        WatchUi.requestUpdate();
    }
    function onShow() as Void {
        NativeForegroundApp.traceWake("show");_shown=true;refreshLocale();syncDisplayMode(System.getDisplayMode());
        if(_mode == NOT_LOW){_resumePending=true;WatchUi.requestUpdate();}
    }
    function resumeAfterAdmission() as Void {_resumePending=true;WatchUi.requestUpdate();}
    function stopResume() as Void {if(_resumeTimer!=null){_resumeTimer.stop();_resumeTimer=null;}}
    function resumeAfterFrame() as Void {
        _resumeTimer=null;if(!_shown||_mode!=NOT_LOW||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}
        refreshLocale();if(pendingLoader!=null){pendingLoader.invoke();}if(admissionPending){return;}refreshFitness();prepareVisual();
        if(context!=null){var duration=downloaded==null?2.5:((downloaded as NativeVisualRenderer).duration() as Float);animationRunning=true;WatchUi.animate(self,:animationProgress,WatchUi.ANIM_TYPE_LINEAR,0.0,1.0,duration,method(:animationDone));}
    }
    function queueResumeAfterFrame() as Void {
        if(_shown && _resumePending && _resumeTimer==null){_resumePending=false;_resumeTimer=new Timer.Timer();_resumeTimer.start(method(:resumeAfterFrame),50,false);}
    }
    (:extendedCode)
    function refreshFitness() as Void {
        if(admissionPending||!_shown||!(_mode == NOT_LOW)||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}
        var now=_clock.utcSeconds();var minute=utcMinute(now);var changed=false;
        if(metricsMinute==null||metricsMinute!=minute){
            fitness.selectedRoles=settings.slots;
            if(!selectedFields.active()){selectedFields.start(settings.slots,method(:fieldsChanged));}
            selectedFields.read(settings.language);
            fitness.currentBodyBattery=selectedFields.energy;
            values=fitness.sample(now);metricsMinute=minute;changed=true;
        }
        if(fitnessTimer==null){fitnessTimer=new Timer.Timer();fitnessTimer.start(method(:refreshFitness),60000,true);}
        if(changed){WatchUi.requestUpdate();}
    }
    function fieldsChanged(id as Complications.Id) as Void {
        if(admissionPending||!_shown||_mode!=NOT_LOW||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER||!selectedFields.includes(id)){return;}
        selectedFields.read(settings.language);fitness.currentBodyBattery=selectedFields.energy;
        values["energy"]=fitness.currentBodyBattery;WatchUi.requestUpdate();
    }
    function stopFitness() as Void {if(fitnessTimer!=null){fitnessTimer.stop();fitnessTimer=null;}selectedFields.stop();fitness.currentBodyBattery=null;values["energy"]=null;metricsMinute=null;}
    function snapshotAt(now as Number or Long) as ClockSnapshot {
        advanceSelection(now);
        if(context!=null){context.advanceFreshness(now);}
        var remaining=_schedule.remainingSeconds(now);
        var current=new ClockSnapshot(_clock.localTimeText(),CountdownFormat.format(remaining));
        current.lowCountdown=CountdownFormat.minutes(remaining);
        current.date=context==null?null:context.date;current.localCalendar=_clock.localCalendar();current.battery=fitness.display(values,"battery");
        if(context!=null){current.stale=context.stale;current.rescheduled=context.rescheduled;current.sourceHold=context.sourceHold;}
        return current;
    }
    // Selection transitions happen on a permitted frame, never by polling or
    // storage work on every countdown tick. A successor can replace this
    // waiting state only through a validated, source-bound admission.
    (:extendedCode) function resetRollover() as Void {passedSelections=[];}
    (:typecheck(false)) function selectionPassed(scene) {
        if(scene==null||scene.retentionDeadline==null||scene.retentionTarget==null){return false;}
        for(var i=0;i<passedSelections.size();i+=1){var row=passedSelections[i];if(row[0].equals(scene.launchId)&&row[1]==scene.retentionTarget&&row[2]==scene.retentionDeadline){return true;}}
        return false;
    }
    (:typecheck(false)) function advanceSelection(now as Number or Long) as Void {
        if(context==null||context.retentionDeadline==null){return;}
        if(now.toLong()<context.retentionDeadline&&!selectionPassed(context)){return;}
        resolveSelection(now);
    }
    (:extendedCode,:typecheck(false)) function resolveSelection(now as Number or Long) as Void {
        var next=context;var changed=false;
        while(next!=null&&next.retentionDeadline!=null&&(selectionPassed(next)||now.toLong()>=next.retentionDeadline)){
            if(!selectionPassed(next)){passedSelections.add([next.launchId,next.retentionTarget,next.retentionDeadline]);if(passedSelections.size()>3){passedSelections=passedSelections.slice(passedSelections.size()-3,passedSelections.size());}}
            changed=true;next=null;if(upcoming.size()>0){next=upcoming[0];upcoming=upcoming.slice(1,upcoming.size());}
        }
        if(!changed){return;}
        // The packet's bitmap/transfer belong to the old identity. A successor
        // starts with its own bundled fallback until its source update arrives.
        packet=null;assetCache=null;setContext(next);
    }
    (:extendedCode,:typecheck(false)) function queueSnapshots(){var rows=[];if(context!=null){rows.add(context);}for(var i=0;i<upcoming.size();i+=1){rows.add(upcoming[i]);}return rows;}
    (:extendedCode,:typecheck(false)) function earlier(a,b){if(a.orderingUtc==null){return b.orderingUtc==null&&a.launchId.compareTo(b.launchId)<0;}if(b.orderingUtc==null){return true;}return a.orderingUtc==b.orderingUtc?a.launchId.compareTo(b.launchId)<0:a.orderingUtc<b.orderingUtc;}
    (:extendedCode,:typecheck(false)) function mergeSaved(saved,now,terminal) as Void {
        var rows=queueSnapshots();
        for(var i=0;i<saved.size();i+=1){var candidate=saved[i];var removed=false;for(var t=0;t<terminal.size();t+=1){if(terminal[t]["launch_id"].equals(candidate.launchId)&&terminal[t]["source_validated_utc"]>candidate.sourceValidated){removed=true;break;}}if(removed){continue;}var index=-1;for(var j=0;j<rows.size();j+=1){if(rows[j].launchId.equals(candidate.launchId)){index=j;break;}}
            if(index<0){rows.add(candidate);}else if(candidate.sourceValidated>rows[index].sourceValidated){rows[index]=candidate;}}
        var ordered=[];for(var k=0;k<rows.size();k+=1){var row=rows[k];if(selectionPassed(row)||row.retentionDeadline!=null&&now>=row.retentionDeadline){continue;}var inserted=false;var list=[];for(var n=0;n<ordered.size();n+=1){if(!inserted&&earlier(row,ordered[n])){list.add(row);inserted=true;}list.add(ordered[n]);}if(!inserted){list.add(row);}ordered=list;}
        var selected=ordered.size()==0?null:ordered[0];upcoming=[];for(var q=1;q<ordered.size()&&q<3;q+=1){upcoming.add(ordered[q]);}
        if(selected!=context){packet=null;assetCache=null;setContext(selected);}
    }
    function snapshot() as ClockSnapshot {return snapshotAt(_clock.utcSeconds());}
    (:extendedCode)
    function setSettings(next as SceneSettings) as Void { stopFitness();var rolesChanged=!nativeSame(settings.slots,next.slots);settings=next;if(rolesChanged){metricsMinute=null;}aodMinute=null;if(!admissionPending){presentation.prepare(settings.language);}stopAnimation();if(renderer!=null){renderer.prepare(context,settings);(renderer as SceneRenderer).downloaded=downloaded;} if(!admissionPending&&canForegroundWork()){refreshFitness();} }
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
        upcoming=next!=null && next.upcomingScenes instanceof Array?next.upcomingScenes.slice(0,next.upcomingScenes.size()):[];
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
            upcoming=next.upcomingScenes instanceof Array?next.upcomingScenes.slice(0,next.upcomingScenes.size()):[];
            downloaded=retained;if(renderer!=null){renderer.prepare(context,settings);renderer.downloaded=downloaded;}
            packet.compact();advanceSelection(_clock.utcSeconds());return;
        }
        packet=next;downloaded=null;assetCache=null;
        setContext(feedScene(packet,_clock.utcSeconds()));upcoming=packet!=null && packet.upcomingScenes instanceof Array?packet.upcomingScenes.slice(0,packet.upcomingScenes.size()):[];visualKey=key;downloaded=retained;
        if(retained!=null){sceneLifecycle.bindReady();}
        if(renderer!=null){renderer.downloaded=downloaded;}
        if(packet!=null){packet.compact();}advanceSelection(_clock.utcSeconds());
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
        if (!_shown || renderer == null || assetCache == null || !assetCache.ready || packet == null || packet.bridge == null) { return; }
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
        stopAnimation();stopSfrTimer();if(sfrBuild!=null){sfrBuild.dispose();}sfrBuild=null;sceneLifecycle.replace();visualKey=null;downloaded=null;aodMinute=null;
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
    function prepareRenderer() as Void {if(sfrBuild!=null){return;}presentation.resume(settings.language);renderer=new SceneRenderer(presentation);renderer.prepare(context,settings);(renderer as SceneRenderer).downloaded=downloaded;if(_mode==LOW){(renderer as SceneRenderer).prepareAod();}}
    function releaseRenderer() as Void {stopAnimation();renderer=null;}
    function onLayout(dc as Graphics.Dc) as Void {
        if(admissionPending){return;}
        prepareRenderer();
        // Render the complete 390px design into one canvas before scaling:
        // map, points, dynamic raster, foreground, fonts and maintenance stay
        // in the same coordinate system on larger supported round screens.
        if(dc.getWidth()!=390||dc.getHeight()!=390){if(sceneBuffer==null){sceneBuffer=Graphics.createBufferedBitmap({:width=>390,:height=>390,:colorDepth=>16}).get() as Graphics.BufferedBitmap;sceneWidth=0;sceneHeight=0;}if(sceneWidth!=dc.getWidth()||sceneHeight!=dc.getHeight()){sceneWidth=dc.getWidth();sceneHeight=dc.getHeight();var side=sceneWidth<sceneHeight?sceneWidth:sceneHeight;sceneX=(sceneWidth-side)/2;sceneY=(sceneHeight-side)/2;var scale=new Graphics.AffineTransform();scale.scale(side.toFloat()/390.0,side.toFloat()/390.0);sceneScaleOptions={:transform=>scale,:filterMode=>Graphics.FILTER_MODE_POINT};}}else{sceneBuffer=null;sceneScaleOptions=null;sceneWidth=0;sceneHeight=0;}
    }
    function utcMinute(now as Number or Long) as Long {
        var seconds=now.toLong();var minute=seconds/60;
        if(seconds<0 && seconds%60!=0){minute-=1;}
        return minute;
    }
    function onUpdate(dc as Graphics.Dc) as Void {updateForDisplayMode(dc,System.getDisplayMode());}
    // LOW can interrupt a long foreground admission. Keep the accepted
    // context and draw the normal AOD using only temporary LOW resources;
    // they are released again before the parser resumes in HIGH.
    (:extendedCode, :typecheck(false)) function drawPendingLow(dc) {
        var now=_clock.utcSeconds();var minute=utcMinute(now);if(aodMinute!=null&&aodMinute==minute){return;}
        try{values["battery"]=fitness.number(System.getSystemStats().battery,100);}catch(e){values["battery"]=null;}
        var current=snapshotAt(now);current.countdown=current.lowCountdown;
        var index=0;var pin=false;var pinX=335;var pinY=165;
        if(context!=null&&context.point!=null){var point=context.point;for(var i=0;i<NativeAssets.mapCount;i+=1){var map=NativeAssets.mapAt(i);var lon=point[0]-map.longitude;var lat=point[1]-map.latitude;if(lon>=-0.25&&lon<=0.25&&lat>=-0.25&&lat<=0.25){index=i;pin=true;var projected=SceneAod.project(point,map.longitude,map.latitude);pinX=projected[0];pinY=projected[1];break;}}
            if(!pin){var coords=NativeAssets.aodCoordinates;for(var j=0;j<coords.size()/8;j+=1){var longitude=SceneAod.coordinate(coords,j*8);var latitude=SceneAod.coordinate(coords,j*8+4);var lon=point[0]-longitude;var lat=point[1]-latitude;if(lon>=-0.25&&lon<=0.25&&lat>=-0.25&&lat<=0.25){index=54+j;pin=true;var projected=SceneAod.project(point,longitude,latitude);pinX=projected[0];pinY=projected[1];break;}}}
        }
        var map=WatchUi.loadResource(NativeAssets.aodResource(index)) as Graphics.BitmapType;var font=WatchUi.loadResource(Rez.Fonts.Aod40) as Graphics.FontType;
        var oldContext=presentation.aodContextFont;var oldBattery=presentation.aodBatteryFont;
        try{if(oldContext==null){try{presentation.aodContextFont=Graphics.getVectorFont({:face=>["RobotoRegular","RobotoCondensedRegular"],:size=>47});}catch(ignore){}}if(oldBattery==null){try{presentation.aodBatteryFont=Graphics.getVectorFont({:face=>["RobotoRegular","RobotoCondensedRegular"],:size=>51});}catch(ignore){}}if(presentation.aodContextFont==null){presentation.aodContextFont=Graphics.FONT_SMALL;}if(presentation.aodBatteryFont==null){presentation.aodBatteryFont=Graphics.FONT_SMALL;}
            var canvas=null;var target=dc;var side=dc.getWidth()<dc.getHeight()?dc.getWidth():dc.getHeight();
            if(dc.getWidth()!=390||dc.getHeight()!=390){canvas=Graphics.createBufferedBitmap({:width=>390,:height=>390,:colorDepth=>16}).get();target=canvas.getDc();}
            SceneAod.draw(target,current,minute,presentation,font,settings,map,pin,pinX,pinY);
            var mask=WatchUi.loadResource(Rez.Drawables.AodRestMask) as Graphics.BitmapType;var phase=((minute%4+4)%4).toNumber();target.drawBitmap(-(phase%2),-(phase/2),mask);
            if(canvas!=null){var transform=new Graphics.AffineTransform();transform.scale(side.toFloat()/390.0,side.toFloat()/390.0);dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();dc.drawBitmap2((dc.getWidth()-side)/2,(dc.getHeight()-side)/2,canvas,{:transform=>transform,:filterMode=>Graphics.FILTER_MODE_POINT});}aodMinute=minute;
        }finally{presentation.aodContextFont=oldContext;presentation.aodBatteryFont=oldBattery;}
    }
    (:typecheck(false)) function updateForDisplayMode(dc as Graphics.Dc, displayMode as System.DisplayMode) as Void {
        // OFF is not a third layout. Stop any owned work without scheduling a
        // redraw or loading resources; a later HIGH observation resumes after
        // its first frame, and LOW never starts active sampling or decoding.
        if(displayMode==System.DISPLAY_MODE_OFF){
            stopForDisplayOff();return;
        }
        // Garmin may deliver a draw before the corresponding sleep callback.
        syncDisplayMode(displayMode);
        // Admission releases reconstructible artwork while validating. Do not
        // recreate it between slices; keep the current clock/countdown visible.
        if(admissionPending&&_mode==LOW){drawPendingLow(dc);return;}
        if(admissionPending){var current=snapshotAt(_clock.utcSeconds());dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();dc.setColor(Graphics.COLOR_WHITE,Graphics.COLOR_TRANSPARENT);var w=dc.getWidth();var h=dc.getHeight();if(current.localCalendar!=null){dc.drawText(w/2,h/2-75,Graphics.FONT_SMALL,presentation.calendar(current.localCalendar),Graphics.TEXT_JUSTIFY_CENTER);}dc.drawText(w/2,h/2-40,Graphics.FONT_LARGE,current.localTime,Graphics.TEXT_JUSTIFY_CENTER);dc.drawText(w/2,h/2+15,Graphics.FONT_MEDIUM,_mode==NOT_LOW?current.countdown:current.lowCountdown,Graphics.TEXT_JUSTIFY_CENTER);if(context!=null){dc.drawText(w/2,h/2+55,Graphics.FONT_SMALL,context.rocket+" · "+context.purpose,Graphics.TEXT_JUSTIFY_CENTER);dc.drawText(w/2,h/2+78,Graphics.FONT_SMALL,context.site,Graphics.TEXT_JUSTIFY_CENTER);if(context.pointText!=null){dc.drawText(w/2,h/2+100,Graphics.FONT_SMALL,context.pointText[1]+", "+context.pointText[0],Graphics.TEXT_JUSTIFY_CENTER);}}if(_mode==NOT_LOW){queueResumeAfterFrame();}return;}
        if(renderer==null && sfrBuild==null){onLayout(dc);}
        // Skip the entire LOW update, including mask and scaled-buffer blit.
        if(!(_mode == NOT_LOW) && aodMinute!=null && aodMinute==utcMinute(_clock.utcSeconds())){return;}
        if(sceneBuffer!=null){var bitmap=sceneBuffer as Graphics.BufferedBitmap;var target=bitmap.getDc();drawScene(target);applyPixelRest(target);if(sceneX!=0||sceneY!=0){dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();}dc.drawBitmap2(sceneX,sceneY,bitmap,sceneScaleOptions);if(_mode==NOT_LOW&&renderer!=null){queueResumeAfterFrame();}return;}
        drawScene(dc);applyPixelRest(dc);
        if(_mode==NOT_LOW&&renderer!=null){queueResumeAfterFrame();}
    }
    function applyPixelRest(dc as Graphics.Dc) as Void {
        if(_mode == NOT_LOW){return;}
        if(restMask==null){restMask=WatchUi.loadResource(Rez.Drawables.AodRestMask) as Graphics.BitmapType;}
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
    function onHide() as Void {_shown=false;_resumePending=false;stopResume();stopAnimation();cancelSfrBuild();stopFitness();releaseVisualForSettings();}
    // Settings must not retain the decoded scene while its picker is open.
    // The accepted packet and source remain; onLayout/onShow rebuild the view.
    function releaseVisualForSettings() as Void {downloaded=null;renderer=null;restMask=null;sceneBuffer=null;sceneScaleOptions=null;sceneLifecycle.replace();}
    function releaseForSettings() as Void {onHide();}
    (:typecheck(false))
    // Fixed SDK-minimum cadence; repeated preparation cannot postpone a pending
    // slice. Each decoder slice still has its existing18ms/16row work budget.
    function startSfrTimer() as Void {if(!_shown||!(_mode == NOT_LOW)||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}if(sfrTimer==null){sfrTimer=new Timer.Timer();sfrTimer.start(method(:sfrStep),50,true);}}
    (:typecheck(false))
    function stopSfrTimer() as Void {if(sfrTimer!=null){sfrTimer.stop();sfrTimer=null;}}
    (:typecheck(false))
    function cancelSfrBuild() as Void {
        stopSfrTimer();if(sfrBuild!=null){sfrBuild.dispose();}sfrBuild=null;sceneLifecycle.cancel();
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
                // Keep the active renderer for every clock/countdown tick while
                // the decoder owns its working buffers. LOW-only resources can
                // be rebuilt after the build or on a transition to LOW.
                var bundled=renderer!=null&&renderer.aodPin&&renderer.aodResource!=null;
                if(renderer!=null){(renderer as SceneRenderer).releaseAod();}
                sfrBuild=new NativeSfrBuild(assetCache.store,assetCache.base,packet);sfrBuild.preferBundled=bundled;
                return;
            }
            if (sfrBuild.step()) {
                var result=sfrBuild.result;stopSfrTimer();sfrBuild=null;
                if (sceneLifecycle.complete(sfrGeneration)) {
                    downloaded=result;if(renderer==null){prepareRenderer();}else{(renderer as SceneRenderer).downloaded=downloaded;}
                    WatchUi.requestUpdate();
                }
            }
        } catch(e) {

            if(sfrBuild!=null){sfrBuild.dispose();}sfrBuild=null;stopSfrTimer();sceneLifecycle.fail(sfrGeneration);WatchUi.requestUpdate();
        }
    }

}
