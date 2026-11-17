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
    var bootstrapPending as Boolean=false;
    var admissionPending as Boolean=false;var cancelAdmission as Method or Null=null;
    var presentation as LocalePresentation;
    var settings as SceneSettings;
    var context as SceneContext or Null;var visualKey as Array or Null=null;
    var packet as NativeFeed or Null=null;
    var upcoming as Array = [];
    var passedSelections as Array = [];
    var downloaded as NativeVisualRenderer or Null=null;
    var assetCache as NativeRenderSource or Null=null;
    var sfrBuild as NativeSfrBuild or Null=null;var sfrTimer as Timer.Timer or Null=null;
    var sfrDeferred as Boolean=false;var sfrFallbackPrepared as Boolean=false;var sfrBundled as Boolean=false;
    var decodingText as Array or Null=null;var decodingMetricInput as Array or Null=null;var decodingMetricText as Array or Null=null;
    var fallbackClockTimer as Timer.Timer or Null=null;
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
    var layoutReady as Boolean=false;
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
        stopResume();stopAnimation();stopFitness();stopFallbackClock();
        // Preserve the resumable SFR job across OFF; no timer runs there.
        stopSfrTimer();
    }
    function displayMode() as Number {return _mode;}
    function transitionMode(next as Number) as Void {
        if (_mode == next) { return; }
        _mode=next;aodMinute=null;metricsMinute=null;System.println("SF_VIEW mode="+(_mode==LOW?"LOW":"HIGH")+" pending="+admissionPending);
        if (_mode == LOW) { _resumePending=false;stopResume();stopAnimation();stopSfrTimer();stopFitness();stopFallbackClock();prepareOptionalAod(); }
        else { restMask=null;if(renderer!=null){(renderer as SceneRenderer).releaseAod();}_resumePending=true; }
        WatchUi.requestUpdate();
    }
    function onShow() as Void {
        _shown=true;try{refreshLocale();}catch(e){}syncDisplayMode(System.getDisplayMode());
        if(_mode == NOT_LOW){_resumePending=true;WatchUi.requestUpdate();}
    }
    function resumeAfterAdmission() as Void {_resumePending=true;WatchUi.requestUpdate();}
    function stopResume() as Void {if(_resumeTimer!=null){_resumeTimer.stop();_resumeTimer=null;}}
    function resumeAfterFrame() as Void {
        _resumeTimer=null;if(!_shown||_mode!=NOT_LOW||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}
        try{refreshLocale();}catch(e){}
        // First frame precedes cache work; failure never takes away the clock.
        if(pendingLoader!=null){try{pendingLoader.invoke();}catch(e){}}
        if(bootstrapPending){bootstrapPending=false;if(!admissionPending){try{if(renderer==null){prepareRenderer();}}catch(e){renderer=null;}_resumePending=true;WatchUi.requestUpdate();}}
        if(admissionPending){return;}
        try{refreshFitness();}catch(e){}prepareVisual();
        if(context!=null&&!sfrFallbackPrepared&&sfrBuild==null){var duration=downloaded==null?2.5:((downloaded as NativeVisualRenderer).duration() as Float);animationRunning=true;WatchUi.animate(self,:animationProgress,WatchUi.ANIM_TYPE_LINEAR,0.0,1.0,duration,method(:animationDone));}
    }
    function queueResumeAfterFrame() as Void {
        if(_shown && _resumePending && _resumeTimer==null){_resumePending=false;_resumeTimer=new Timer.Timer();_resumeTimer.start(method(:resumeAfterFrame),50,false);}
    }
    (:extendedCode)
    function refreshFitness() as Void {
        if(!_shown||!(_mode == NOT_LOW)||admissionPending||sfrFallbackPrepared||sfrBuild!=null||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}
        try{refreshFitnessWork();}catch(e){}
    }
    (:extendedCode)
    function refreshFitnessWork() as Void {
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
        if(!_shown||_mode!=NOT_LOW||admissionPending||sfrFallbackPrepared||sfrBuild!=null||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}
        try{if(!selectedFields.includes(id)){return;}selectedFields.readChanged(settings.language,id);fitness.currentBodyBattery=selectedFields.energy;
        values["energy"]=fitness.currentBodyBattery;WatchUi.requestUpdate();}catch(e){}
    }
    function stopFitness() as Void {if(fitnessTimer!=null){fitnessTimer.stop();fitnessTimer=null;}try{selectedFields.stop();}catch(e){}fitness.currentBodyBattery=null;values["energy"]=null;metricsMinute=null;}
    function snapshotAt(now as Number or Long) as ClockSnapshot {
        advanceSelection(now);
        if(context!=null){context.advanceFreshness(now);}
        var remaining=_schedule.remainingSeconds(now);
        if(context!=null&&context.displayTarget!=null){remaining=(context.displayTarget as Long)-now.toLong();}
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
        // Successors are checkpointed while the parser owns the heap. At a
        // rollover, cancel that candidate so the accepted queue can be
        // restored instead of losing the next selection or keeping it stale.
        if(admissionPending){if(cancelAdmission!=null){cancelAdmission.invoke();resumeAfterAdmission();}return;}
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
    function setSettings(next as SceneSettings) as Void { clearDecodingText();stopFitness();var rolesChanged=!nativeSame(settings.slots,next.slots);settings=next;if(rolesChanged){metricsMinute=null;}aodMinute=null;if(!admissionPending&&!sfrFallbackPrepared&&sfrBuild==null){presentation.restore(settings.language);}stopAnimation();if(renderer!=null){renderer.prepare(context,settings);(renderer as SceneRenderer).useDownloaded(downloaded);} if(canForegroundWork()){refreshFitness();} }
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
        clearDecodingText();var key=packetVisualKey(next);
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
            downloaded=retained;if(renderer!=null){renderer.prepare(context,settings);renderer.useDownloaded(downloaded);}
            packet.compact();advanceSelection(_clock.utcSeconds());return;
        }
        packet=next;downloaded=null;assetCache=null;
        setContext(feedScene(packet,_clock.utcSeconds()));upcoming=packet!=null && packet.upcomingScenes instanceof Array?packet.upcomingScenes.slice(0,packet.upcomingScenes.size()):[];visualKey=key;downloaded=retained;
        if(retained!=null){sceneLifecycle.bindReady();}
        if(renderer!=null){renderer.useDownloaded(downloaded);}
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
        if (!_shown || admissionPending || assetCache == null || !assetCache.ready || packet == null || packet.bridge == null) { return; }
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
        stopAnimation();stopSfrTimer();if(sfrBuild!=null){sfrBuild.dispose();}sfrBuild=null;sfrFallbackPrepared=false;sceneLifecycle.replace();visualKey=null;downloaded=null;aodMinute=null;
        if(next!=null && next.launchId.equals("")){next=null;}
        context=next;_schedule=next==null?new ScheduleState(null,"empty"):next.schedule;
        if(renderer!=null){try{renderer.prepare(context,settings);(renderer as SceneRenderer).useDownloaded(downloaded);}catch(e){renderer=null;layoutReady=false;}if(_mode==LOW){prepareOptionalAod();}}
    }
    function canForegroundWork() as Boolean {return _shown&&(_mode == NOT_LOW)&&!_resumePending&&_resumeTimer==null&&System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER;}
    function canAcceptBackground() as Boolean {return _shown&&!bootstrapPending&&System.getDisplayMode()!=System.DISPLAY_MODE_OFF&&(!_awake||canForegroundWork());}
    // Release only rebuildable graphics while the strict candidate is resident;
    // retain the compact selected context, UTC schedule and successor facts.
    function beginAdmission() as Void {cancelSfrBuild();stopAnimation();stopFitness();presentation.suspend();LocaleGraphemes.data=null;if(packet!=null&&context!=null){context.stale=packet.stale as Boolean;context.rescheduled=packet.rescheduled as Boolean;}packet=null;downloaded=null;assetCache=null;renderer=null;restMask=null;sceneBuffer=null;sceneScaleOptions=null;layoutReady=false;admissionPending=true;startFallbackClock();WatchUi.requestUpdate();}
    function endAdmission() as Void {admissionPending=false;_resumePending=true;WatchUi.requestUpdate();}
    (:typecheck(false))
    // Keep the last accepted scene while its durable packet is revalidated.
    // The packet is detached for the parser, but its presentation and qualified
    // visual remain the only visible scene until a replacement is admitted.
    function clearForRestore() as Void {
        if(packet!=null && context!=null){context.stale=packet.stale;context.rescheduled=packet.rescheduled;}
        packet=null;
    }
    function prepareRenderer() as Void {if(sfrBuild!=null||sfrFallbackPrepared){return;}presentation.restore(settings.language);LocaleGraphemes.load();renderer=new SceneRenderer(presentation);renderer.prepare(context,settings);(renderer as SceneRenderer).useDownloaded(downloaded);if(_mode==LOW){(renderer as SceneRenderer).prepareAod();}}
    function prepareOptionalAod() as Void {if(renderer!=null&&sfrBuild==null&&!sfrFallbackPrepared){try{(renderer as SceneRenderer).prepareAod();}catch(e){renderer=null;layoutReady=false;}}}
    function releaseRenderer() as Void {stopAnimation();renderer=null;layoutReady=false;}
    function onLayout(dc as Graphics.Dc) as Void {
        if(bootstrapPending||admissionPending){return;}
        try{if(renderer==null){prepareRenderer();}}catch(e){renderer=null;return;}
        // Render the complete 390px design into one canvas before scaling:
        // map, points, dynamic raster, foreground, fonts and maintenance stay
        // in the same coordinate system on larger supported round screens.
        try{if(dc.getWidth()!=390||dc.getHeight()!=390){if(sceneBuffer==null){sceneBuffer=Graphics.createBufferedBitmap({:width=>390,:height=>390,:colorDepth=>16}).get() as Graphics.BufferedBitmap;sceneWidth=0;sceneHeight=0;}if(sceneWidth!=dc.getWidth()||sceneHeight!=dc.getHeight()){sceneWidth=dc.getWidth();sceneHeight=dc.getHeight();var side=sceneWidth<sceneHeight?sceneWidth:sceneHeight;sceneX=(sceneWidth-side)/2;sceneY=(sceneHeight-side)/2;var scale=new Graphics.AffineTransform();scale.scale(side.toFloat()/390.0,side.toFloat()/390.0);sceneScaleOptions={:transform=>scale,:filterMode=>Graphics.FILTER_MODE_POINT};}}else{sceneBuffer=null;sceneScaleOptions=null;sceneWidth=0;sceneHeight=0;}layoutReady=true;}catch(e){renderer=null;sceneBuffer=null;sceneScaleOptions=null;layoutReady=false;}
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
        if(context!=null&&context.point!=null){var point=context.point;var mapCoordinates=NativeAssets.mapCoordinates();for(var i=0;i<mapCoordinates.size()/8;i+=1){var longitude=mapCoordinates.decodeNumber(Lang.NUMBER_FORMAT_FLOAT,{:offset=>i*8,:endianness=>Lang.ENDIAN_BIG});var latitude=mapCoordinates.decodeNumber(Lang.NUMBER_FORMAT_FLOAT,{:offset=>i*8+4,:endianness=>Lang.ENDIAN_BIG});var lon=point[0]-longitude;var lat=point[1]-latitude;if(lon>=-0.25&&lon<=0.25&&lat>=-0.25&&lat<=0.25){index=i;pin=true;var projected=SceneAod.project(point,longitude,latitude);pinX=projected[0];pinY=projected[1];break;}}
            if(!pin){var coords=NativeAssets.aodCoordinates;for(var j=0;j<coords.size()/8;j+=1){var longitude=SceneAod.coordinate(coords,j*8);var latitude=SceneAod.coordinate(coords,j*8+4);var lon=point[0]-longitude;var lat=point[1]-latitude;if(lon>=-0.25&&lon<=0.25&&lat>=-0.25&&lat<=0.25){index=54+j;pin=true;var projected=SceneAod.project(point,longitude,latitude);pinX=projected[0];pinY=projected[1];break;}}}
        }
        var worldPoint=context!=null&&context.point!=null&&!pin?context.point:null;
        var map=worldPoint==null?(WatchUi.loadResource(NativeAssets.aodResource(index)) as Graphics.BitmapType):null;var font=WatchUi.loadResource(Rez.Fonts.Aod40) as Graphics.FontType;
        var oldContext=presentation.aodContextFont;var oldBattery=presentation.aodBatteryFont;var oldLocale=presentation.locale;presentation.locale=settings.language;
        try{if(oldContext==null){try{presentation.aodContextFont=Graphics.getVectorFont({:face=>["RobotoRegular","RobotoCondensedRegular"],:size=>47});}catch(ignore){}}if(oldBattery==null){try{presentation.aodBatteryFont=Graphics.getVectorFont({:face=>["RobotoRegular","RobotoCondensedRegular"],:size=>51});}catch(ignore){}}if(presentation.aodContextFont==null){presentation.aodContextFont=Graphics.FONT_SMALL;}if(presentation.aodBatteryFont==null){presentation.aodBatteryFont=Graphics.FONT_SMALL;}
            var canvas=null;var target=dc;var side=dc.getWidth()<dc.getHeight()?dc.getWidth():dc.getHeight();
            if(dc.getWidth()!=390||dc.getHeight()!=390){canvas=Graphics.createBufferedBitmap({:width=>390,:height=>390,:colorDepth=>16}).get();target=canvas.getDc();}
            SceneAod.draw(target,current,minute,presentation,font,settings,map,pin,pinX,pinY,worldPoint);
            if(context!=null&&context.point==null){FallbackMap.unknown(target,365,20);}else if(pin){FallbackMap.uncertain(target,pinX,pinY);}
            var mask=WatchUi.loadResource(Rez.Drawables.AodRestMask) as Graphics.BitmapType;var phase=((minute%4+4)%4).toNumber();target.drawBitmap(-(phase%2),-(phase/2),mask);
            if(canvas!=null){var transform=new Graphics.AffineTransform();transform.scale(side.toFloat()/390.0,side.toFloat()/390.0);dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();dc.drawBitmap2((dc.getWidth()-side)/2,(dc.getHeight()-side)/2,canvas,{:transform=>transform,:filterMode=>Graphics.FILTER_MODE_POINT});}aodMinute=minute;
        }finally{presentation.aodContextFont=oldContext;presentation.aodBatteryFont=oldBattery;presentation.locale=oldLocale;}
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

        if(!(_mode == NOT_LOW) && aodMinute!=null && aodMinute==utcMinute(_clock.utcSeconds())){return;}
        if(_mode==LOW&&(bootstrapPending||admissionPending||sfrFallbackPrepared||renderer==null)){
            try{drawPendingLow(dc);}catch(e){drawClockFallback(dc);}return;
        }
        if(bootstrapPending||admissionPending){drawClockFallback(dc);if(_mode==NOT_LOW){queueResumeAfterFrame();}return;}
        if((renderer==null||!layoutReady) && sfrBuild==null&&!sfrFallbackPrepared){onLayout(dc);}
        if(_mode==LOW&&renderer!=null&&!(renderer as SceneRenderer).fonts.hasKey("aod")){prepareOptionalAod();}
        if(_mode==NOT_LOW&&(sfrFallbackPrepared||sfrBuild!=null)){
            try{if(sceneBuffer!=null){var canvas=sceneBuffer as Graphics.BufferedBitmap;drawDecodingFrame(canvas.getDc());if(sceneX!=0||sceneY!=0){dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();}dc.drawBitmap2(sceneX,sceneY,canvas,sceneScaleOptions);}else{drawDecodingFrame(dc);}}catch(e){drawClockFallback(dc);}queueResumeAfterFrame();return;
        }
        if(renderer==null){drawClockFallback(dc);if(_mode==NOT_LOW){queueResumeAfterFrame();}return;}
        if(!sfrFallbackPrepared&&sfrBuild==null){stopFallbackClock();}
        // Skip the entire LOW update, including mask and scaled-buffer blit.
        if(sceneBuffer!=null){var bitmap=sceneBuffer as Graphics.BufferedBitmap;var target=bitmap.getDc();drawScene(target);applyPixelRest(target);if(sceneX!=0||sceneY!=0){dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();}dc.drawBitmap2(sceneX,sceneY,bitmap,sceneScaleOptions);if(_mode==NOT_LOW&&(renderer!=null||sfrFallbackPrepared||sfrBuild!=null)){queueResumeAfterFrame();}return;}
        drawScene(dc);applyPixelRest(dc);
        if(_mode==NOT_LOW&&(renderer!=null||sfrFallbackPrepared||sfrBuild!=null)){queueResumeAfterFrame();}
    }
    // Keep only already fitted short strings while optional SFR work owns the
    // heap. Scene/settings changes clear this cache before admission begins.
    (:typecheck(false)) function clearDecodingText(){decodingText=null;decodingMetricInput=null;decodingMetricText=null;}
    // Frame-local resources keep accepted facts visible while the optional
    // decoder owns heap. No renderer, provider or icon cache survives a frame.
    (:extendedCode, :typecheck(false)) function drawDecodingFrame(dc){
        presentation.prepareLight(settings.language);
        try{
            var current=snapshotAt(_clock.utcSeconds());var selected=context;
            if(decodingText==null){var title="";var details="";var siteText="";if(selected!=null){var operator=selected.operatorShort.equals("")?selected.operator:selected.operatorShort;var combined=operator.equals("")?presentation.mission(selected.purpose):operator+" · "+presentation.mission(selected.purpose);title=presentation.fit(dc,selected.rocket,Graphics.FONT_XTINY,238);details=presentation.fit(dc,combined,Graphics.FONT_XTINY,282);siteText=presentation.fit(dc,selected.site,Graphics.FONT_XTINY,242);}decodingText=[title,details,siteText];decodingMetricInput=[null,null,null,null];decodingMetricText=[null,null,null,null];}
            for(var m=0;m<4;m+=1){var rawMetric=presentation.metric(fitness,values,settings.slots[m]);if(decodingMetricInput[m]==null||!decodingMetricInput[m].equals(rawMetric)){decodingMetricInput[m]=rawMetric;decodingMetricText[m]=presentation.fit(dc,rawMetric,Graphics.FONT_TINY,105);}}
            // Fitting may load the full grapheme table. Only fitted strings are
            // needed below; release the table before map/art and SFR buffers.
            LocaleGraphemes.data=null;
            var resource=NativeAssets.mapResource(0);var pin=false;var x=335;var y=165;
            if(selected!=null&&selected.point!=null){var point=selected.point;var mapCoordinates=NativeAssets.mapCoordinates();for(var i=0;i<mapCoordinates.size()/8;i+=1){var longitude=mapCoordinates.decodeNumber(Lang.NUMBER_FORMAT_FLOAT,{:offset=>i*8,:endianness=>Lang.ENDIAN_BIG});var latitude=mapCoordinates.decodeNumber(Lang.NUMBER_FORMAT_FLOAT,{:offset=>i*8+4,:endianness=>Lang.ENDIAN_BIG});var dx=point[0]-longitude;var dy=point[1]-latitude;if(dx>=-0.25&&dx<=0.25&&dy>=-0.25&&dy<=0.25){resource=NativeAssets.mapResource(i);pin=true;var projected=SceneAod.project(point,longitude,latitude);x=projected[0];y=projected[1];break;}}
                if(!pin){var coordinates=NativeAssets.aodCoordinates;for(var i=0;i<coordinates.size()/8;i+=1){var longitude=SceneAod.coordinate(coordinates,i*8);var latitude=SceneAod.coordinate(coordinates,i*8+4);var dx=point[0]-longitude;var dy=point[1]-latitude;if(dx>=-0.25&&dx<=0.25&&dy>=-0.25&&dy<=0.25){resource=NativeAssets.extraMapResource(i);pin=true;var projected=SceneAod.project(point,longitude,latitude);x=projected[0];y=projected[1];break;}}}}
            var worldPoint=selected!=null&&selected.point!=null&&!pin?selected.point:null;
            dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();
            if(worldPoint!=null){FallbackWorld.draw(dc,97,15);}else{var map=WatchUi.loadResource(resource);var transform=new Graphics.AffineTransform();transform.scale(2.0,2.0);dc.drawBitmap2(0,0,map,{:transform=>transform,:filterMode=>Graphics.FILTER_MODE_BILINEAR});map=null;transform=null;}
            dc.setColor(0xD4DFEB,Graphics.COLOR_TRANSPARENT);
            if(selected!=null){dc.drawText(195,36,Graphics.FONT_XTINY,decodingText[0],Graphics.TEXT_JUSTIFY_CENTER);dc.drawText(195,62,Graphics.FONT_XTINY,decodingText[1],Graphics.TEXT_JUSTIFY_CENTER);dc.drawText(195,319,Graphics.FONT_XTINY,decodingText[2],Graphics.TEXT_JUSTIFY_CENTER);var model=NativeAssets.models.hasKey(selected.modelId)?selected.modelId:"generic";var asset=model.equals("generic")?Rez.Drawables.Art_unknown:NativeAssets.models[model];dc.drawBitmap(22,118,WatchUi.loadResource(asset));}
            if(current.localCalendar!=null){dc.drawText(195,88,Graphics.FONT_XTINY,presentation.calendar(current.localCalendar),Graphics.TEXT_JUSTIFY_CENTER);}
            dc.setColor(settings.clockColor,Graphics.COLOR_TRANSPARENT);dc.drawText(195,118,Graphics.FONT_NUMBER_MEDIUM,current.localTime,Graphics.TEXT_JUSTIFY_CENTER);
            dc.setColor(SceneAod.countdownColor(current,settings),Graphics.COLOR_TRANSPARENT);dc.drawText(195,202,Graphics.FONT_MEDIUM,current.countdown,Graphics.TEXT_JUSTIFY_CENTER);
            for(var i=0;i<4;i+=1){dc.setColor(settings.fieldColors[i],Graphics.COLOR_TRANSPARENT);dc.drawText(i%2==0?95:295,i<2?244:282,Graphics.FONT_TINY,decodingMetricText[i],Graphics.TEXT_JUSTIFY_CENTER);}
            if(pin){dc.setColor(0xFFFFFF,Graphics.COLOR_TRANSPARENT);dc.fillCircle(x,y,8);dc.setColor(0xF7AE4F,Graphics.COLOR_TRANSPARENT);dc.fillCircle(x,y,5);FallbackMap.uncertain(dc,x,y);}else if(worldPoint!=null){FallbackMap.point(dc,worldPoint,97,15);}else if(selected!=null){FallbackMap.unknown(dc,365,20);}
        }finally{presentation.suspend();}
    }
    // Built-in fonts and local system clock do not depend on feed, assets or
    // health providers. This is temporary while the full scene is unavailable.
    (:typecheck(false)) function drawClockFallback(dc as Graphics.Dc) as Void {
        startFallbackClock();
        var x=dc.getWidth()/2;var y=dc.getHeight()/2;var parts=_clock.localCalendar();
        if(_mode==LOW){var minute=utcMinute(_clock.utcSeconds());var phase=((minute%4+4)%4).toNumber();x+=(phase%2==0?-1:1);y+=(phase/2==0?-1:1);aodMinute=minute;}
        dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();
        dc.setColor(settings.clockColor,Graphics.COLOR_TRANSPARENT);
        dc.drawText(x,y-15,Graphics.FONT_MEDIUM,_clock.localTimeText(),Graphics.TEXT_JUSTIFY_CENTER);
        if(parts.size()==3){dc.drawText(x,y-45,Graphics.FONT_TINY,parts[1].format("%02d")+"."+parts[2].format("%02d"),Graphics.TEXT_JUSTIFY_CENTER);}
        // Keep admitted facts independent of the optional graphics as well.
        // Their own failure cannot prevent the already drawn clock/date.
        try{if(context!=null){var now=_clock.utcSeconds();advanceSelection(now);var selected=context as SceneContext or Null;if(selected!=null){var snap=snapshotAt(now);var value=_mode==LOW?snap.lowCountdown:snap.countdown;dc.setColor(selected.rescheduled||selected.sourceHold?0xFF6B6B:settings.countdownColor,Graphics.COLOR_TRANSPARENT);dc.drawText(x,y+25,Graphics.FONT_TINY,value,Graphics.TEXT_JUSTIFY_CENTER);dc.setColor(0xD4DFEB,Graphics.COLOR_TRANSPARENT);dc.drawText(x,y+55,Graphics.FONT_XTINY,selected.site,Graphics.TEXT_JUSTIFY_CENTER);dc.drawText(x,y+80,Graphics.FONT_XTINY,selected.rocket+" · "+selected.purpose,Graphics.TEXT_JUSTIFY_CENTER);}}}catch(e){}
        // Bounded direct-draw map after clock and facts: an optional failure
        // must never erase or prevent the clock. Its source point is separate
        // from downloaded artwork and is absent for an unknown event location.
        try{if(context!=null){var left=(dc.getWidth()-195)/2;FallbackWorld.draw(dc,left,15);if(context.point!=null){FallbackMap.point(dc,context.point,left,15);}else{FallbackMap.unknown(dc,left+190,20);}}}catch(e){}
    }
    function applyPixelRest(dc as Graphics.Dc) as Void {
        if(_mode == NOT_LOW){return;}
        if(restMask==null){try{restMask=WatchUi.loadResource(Rez.Drawables.AodRestMask) as Graphics.BitmapType;}catch(e){return;}}
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
        try{if((_mode == NOT_LOW)){drawing.active(dc,current,settings,values,fitness,animationProgress);}
        else{current.countdown=current.lowCountdown;drawing.aod(dc,current,minute,settings);aodMinute=minute;}}
        catch(e){renderer=null;layoutReady=false;drawClockFallback(dc);}
        finally{if(sfrFallbackPrepared||sfrBuild!=null){renderer=null;presentation.suspend();}}
    }
    function startFallbackClock() as Void {if(_shown&&_mode==NOT_LOW&&System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER&&fallbackClockTimer==null){fallbackClockTimer=new Timer.Timer();fallbackClockTimer.start(method(:fallbackClockTick),1000,true);}}
    function stopFallbackClock() as Void {if(fallbackClockTimer!=null){fallbackClockTimer.stop();fallbackClockTimer=null;}}
    function fallbackClockTick() as Void {if(!_shown||_mode!=NOT_LOW||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){stopFallbackClock();return;}WatchUi.requestUpdate();}
    function stopAnimation() as Void{
        if(animationRunning){WatchUi.cancelAllAnimations();}
        animationRunning=false;animationProgress=0.0;
    }
    function animationDone() as Void{animationRunning=false;animationProgress=0.0;WatchUi.requestUpdate();}
    function onEnterSleep() as Void { _awake=false;var display=System.getDisplayMode();syncDisplayMode(display);if(display!=System.DISPLAY_MODE_OFF){prepareOptionalAod();} }
    function onExitSleep() as Void { _awake=true;var display=System.getDisplayMode();syncDisplayMode(display);if(display!=System.DISPLAY_MODE_OFF){WatchUi.requestUpdate();} }
    function onHide() as Void {_shown=false;_resumePending=false;stopResume();stopAnimation();cancelSfrBuild();stopFitness();stopFallbackClock();if(cancelAdmission!=null){cancelAdmission.invoke();}releaseVisualForSettings();}
    // Settings must not retain the decoded scene while its picker is open.
    // The accepted packet and source remain; onLayout/onShow rebuild the view.
    function releaseVisualForSettings() as Void {clearDecodingText();downloaded=null;renderer=null;restMask=null;sceneBuffer=null;sceneScaleOptions=null;layoutReady=false;sceneLifecycle.replace();}
    function releaseForSettings() as Void {onHide();}
    (:typecheck(false))
    // Fixed SDK-minimum cadence; repeated preparation cannot postpone a pending
    // slice. Each decoder slice still has its existing18ms/16row work budget.
    function startSfrTimer() as Void {if(!_shown||(!layoutReady&&sfrBuild==null&&!sfrFallbackPrepared)||!(_mode == NOT_LOW)||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}if(sfrTimer==null){sfrTimer=new Timer.Timer();sfrTimer.start(method(:sfrStep),50,true);}}
    (:typecheck(false))
    function stopSfrTimer() as Void {if(sfrTimer!=null){sfrTimer.stop();sfrTimer=null;}sfrDeferred=false;}
    (:typecheck(false))
    function cancelSfrBuild() as Void {
        clearDecodingText();stopSfrTimer();if(sfrBuild!=null){sfrBuild.dispose();}sfrBuild=null;sfrFallbackPrepared=false;sceneLifecycle.cancel();
    }
    // Native Storage can need more than one copy of a verified shard: the
    // observed 4,028-byte read failed with 8,184 bytes free. Reserve two shard
    // copies plus bounded decode blocks and clock work, and a possible RGB
    // scanline growth copy only before the row has been allocated.
    (:typecheck(false)) function optionalHeapFree(){try{var stats=System.getSystemStats();return stats.totalMemory-stats.usedMemory;}catch(e){return 0;}}
    (:typecheck(false)) function sfrReadReserve(){
        // A root or role descriptor is already read and owned in phase 1. Its bounded
        // parser continuation does not read another shard or create a decoder.
        // Decoder allocation remains a later step with the full reserve.
        if(sfrBuild!=null&&!sfrBuild.closureChecked&&sfrBuild.pendingRead!=null&&sfrBuild.pendingRead.phase==1){return 8192;}
        if(sfrBuild!=null&&sfrBuild.decoder!=null){var decoder=sfrBuild.decoder;if(decoder.data!=null){return 128*3+512;}var shard=decoder.descriptor["shards"][decoder.shard];var row=decoder.row.size()==0?2*decoder.width*decoder.channels:0;return 2*shard[1]+row+128*3+512;}
        if(sfrBuild!=null&&sfrBuild.closureChecked&&sfrBuild.closureAt<sfrBuild.expected.size()){var largest=0;for(var i=sfrBuild.closureAt;i<sfrBuild.expected.size()&&i<sfrBuild.closureAt+4;i+=1){if(sfrBuild.expected[i][2]>largest){largest=sfrBuild.expected[i][2];}}return 2*largest+128*3+512;}
        return 2*4096+2*390*3+128*3+512;
    }
    (:typecheck(false)) function deferSfr(){stopSfrTimer();sfrDeferred=true;sfrTimer=new Timer.Timer();sfrTimer.start(method(:sfrStep),5000,true);if(renderer==null){startFallbackClock();}WatchUi.requestUpdate();}
    (:typecheck(false)) function resumeSfrCadence(){if(sfrDeferred){stopSfrTimer();sfrTimer=new Timer.Timer();sfrTimer.start(method(:sfrStep),50,true);}}
    (:typecheck(false))
    function sfrStep() as Void {

        if (System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER) { stopSfrTimer(); return; }
        if (!_shown || !(_mode == NOT_LOW) || packet==null || packet.bridge==null || !sceneLifecycle.pending()) { stopSfrTimer(); return; }
        try {
            if (sfrBuild==null) {
                // Release rebuildable resources before testing available heap;
                // a refused optional decode retries slowly with clock intact.
                if(!sfrFallbackPrepared){sfrBundled=renderer!=null&&renderer.aodPin&&renderer.aodResource!=null;stopAnimation();if(renderer!=null){(renderer as SceneRenderer).releaseAod();}restMask=null;renderer=null;presentation.suspend();sfrFallbackPrepared=true;if(renderer==null){startFallbackClock();}WatchUi.requestUpdate();}
                if(optionalHeapFree()<sfrReadReserve()){if(!sfrDeferred){deferSfr();}return;}
                resumeSfrCadence();var token=sceneLifecycle.begin();if(token==null){return;}sfrGeneration=token;
                sfrBuild=new NativeSfrBuild(assetCache.store,assetCache.base,packet);sfrBuild.preferBundled=sfrBundled;return;
            }
            if(optionalHeapFree()<sfrReadReserve()){if(!sfrDeferred){deferSfr();}return;}
            resumeSfrCadence();
            if (sfrBuild.step()) {
                var result=sfrBuild.result;stopSfrTimer();sfrBuild=null;sfrFallbackPrepared=false;
                if (sceneLifecycle.complete(sfrGeneration)) {
                    downloaded=result;clearDecodingText();if(renderer==null){prepareRenderer();}else{(renderer as SceneRenderer).useDownloaded(downloaded);prepareOptionalAod();}_resumePending=true;
                    WatchUi.requestUpdate();
                }
            }
        } catch(e) {

            if(sfrBuild!=null){sfrBuild.dispose();}sfrBuild=null;stopSfrTimer();clearDecodingText();sfrFallbackPrepared=false;sceneLifecycle.fail(sfrGeneration);_resumePending=true;WatchUi.requestUpdate();
        }
    }

}
