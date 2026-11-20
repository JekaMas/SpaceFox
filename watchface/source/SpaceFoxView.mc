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
    var remainingUtc as Number or Long or Null = null;
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
    // Lifecycle state is changed only by WatchFace/OS display events.
    private var lifecycle as NativeDisplayLifecycle;
    private var _resumePending as Boolean = false;
    private var _resumeTimer as Timer.Timer or Null = null;
    var bootstrapPending as Boolean=false;var lowNeedsLoader as Boolean=false;
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
    var sceneLifecycle as SceneLifecycle;var mapDecision as MapPresentation;var sfrGeneration as Number=0;
    var pendingLoader as Method or Null=null;
    var renderer as SceneRenderer or Null;
    var fitness as Fitness;
    var selectedFields as SelectedFields;
    var values as Dictionary<String, Number or Null>;
    var restMask as Graphics.BitmapType or Null=null;
    var sceneBuffer as Graphics.BufferedBitmap or Null=null;
    var sceneScaleOptions as Dictionary or Null=null;
    var sceneWidth as Number=0;var sceneHeight as Number=0;var sceneX as Number=0;var sceneY as Number=0;
    var layoutReady as Boolean=false;
    function initialize(clock as WatchClock, schedule as ScheduleState) {
        WatchFace.initialize();lifecycle=new NativeDisplayLifecycle();_clock=clock;_schedule=schedule;
        presentation=createPresentation();settings=new SceneSettings(null);context=null;renderer=null;fitness=new Fitness();selectedFields=new SelectedFields();selectedFields.bindClock(clock);fitness.selectedFields=selectedFields;values={};sceneLifecycle=new SceneLifecycle();mapDecision=new MapPresentation();
    }
    // External effects are overridable at the actual view boundary for logical
    // event tests; the default implementations are the unchanged Garmin APIs.
    function createPresentation() as LocalePresentation {return new LocalePresentation();}
    function deviceMode() as System.DisplayMode {return System.getDisplayMode();}
    function requestFrame() as Void {WatchUi.requestUpdate();}
    function logMode() as Void {System.println("SF_VIEW mode="+(lifecycle.mode()==LOW?"LOW":"HIGH")+" pending="+admissionPending);}
    function newViewTimer() as Timer.Timer {return new Timer.Timer();}
    function syncDisplayMode(mode as System.DisplayMode) as Void {
        if(mode==System.DISPLAY_MODE_OFF){stopForDisplayOff();return;}
        transitionMode(lifecycle.awake() && mode == System.DISPLAY_MODE_HIGH_POWER ? NOT_LOW : LOW);
    }
    function stopForDisplayOff() as Void {
        lifecycle.setMode(LOW);_resumePending=false;lifecycle.invalidateFrame();lifecycle.resetFitness();restMask=null;if(renderer!=null){(renderer as SceneRenderer).releaseAod();}
        stopResume();stopFitness();
        // Preserve the resumable SFR job across OFF; no timer runs there.
        stopSfrTimer();
    }
    function displayMode() as Number {return lifecycle.mode();}
    function visible() as Boolean {return lifecycle.shown();}
    function lastLowFrameMinute() as Long or Null {return lifecycle.frameMinute;}
    function markLowFramePainted(minute as Long) as Void {lifecycle.framePainted(minute);}
    function transitionMode(next as Number) as Void {
        if (!lifecycle.shown() || lifecycle.mode() == next) { return; }
        lifecycle.setMode(next);lifecycle.invalidateFrame();lifecycle.resetFitness();logMode();
        if (lifecycle.mode() == LOW) { _resumePending=false;stopResume();stopSfrTimer();stopFitness();prepareOptionalAod(); }
        else { restMask=null;if(renderer!=null){(renderer as SceneRenderer).releaseAod();}_resumePending=true; }
        requestFrame();
    }
    function onShow() as Void {
        if(!lifecycle.show()){return;}try{refreshLocale();}catch(e){}syncDisplayMode(deviceMode());
        // A hidden background delivery can update durable storage without a
        // volatile payload. Check once after the first LOW frame on every show.
        if(lifecycle.mode() == NOT_LOW){_resumePending=true;requestFrame();}else{lowNeedsLoader=true;}
    }
    function resumeAfterAdmission() as Void {_resumePending=true;requestFrame();}
    function stopResume() as Void {if(_resumeTimer!=null){_resumeTimer.stop();_resumeTimer=null;}}
    function resumeAfterFrame() as Void {
        _resumeTimer=null;if(!lifecycle.shown()||lifecycle.mode()!=NOT_LOW||deviceMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}
        try{refreshLocale();}catch(e){}
        // First frame precedes optional work. Acquire the independently selected
        // health values before a new snapshot can suspend provider resources.
        if(!admissionPending){try{refreshFitness();}catch(e){}}
        if(pendingLoader!=null){try{pendingLoader.invoke();}catch(e){}}
        if(bootstrapPending){bootstrapPending=false;if(!admissionPending){try{if(renderer==null){prepareRenderer();}}catch(e){renderer=null;}_resumePending=true;requestFrame();}}
        if(admissionPending){return;}
        try{refreshFitness();}catch(e){}prepareVisual();
    }
    function queueResumeAfterFrame() as Void {
        if(lifecycle.shown() && _resumePending && _resumeTimer==null){_resumePending=false;_resumeTimer=newViewTimer();_resumeTimer.start(method(:resumeAfterFrame),50,false);}
    }
    (:extendedCode)
    function refreshFitness() as Void {refreshFitnessIfDue(false);}
    function refreshFitnessIfDue(drawing as Boolean) as Void {
        if(!lifecycle.shown()||lifecycle.mode()!=NOT_LOW||admissionPending||deviceMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}
        if(!lifecycle.takeFitness(_clock.utcSeconds().toLong())){return;}
        try{refreshFitnessWork();if(!drawing){requestFrame();}}catch(e){}
    }
    (:extendedCode)
    function refreshFitnessWork() as Void {readFitnessSnapshot(_clock.utcSeconds());}
    function readFitnessSnapshot(now as Number or Long) as Void {
        fitness.selectedRoles=settings.slots;
        if(!selectedFields.active()){selectedFields.start(settings.slots,method(:fieldsChanged));}
        selectedFields.read(settings.language);values=fitness.sample(now);
    }
    function fieldsChanged(id as Complications.Id) as Void {
        if(!lifecycle.shown()||lifecycle.mode()!=NOT_LOW||admissionPending||deviceMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}
        try{if(!selectedFields.includes(id)){return;}selectedFields.readChanged(settings.language,id);
        if(id.getType()==2&&settings.slots.indexOf("steps")>=0){values["steps"]=fitness.sampleSteps();}
        var roles=["energy","heart","stress"];var kinds=[23,18,22];for(var i=0;i<roles.size();i+=1){var role=roles[i];if(id.getType()==kinds[i]&&settings.slots.indexOf(role)>=0){values[role]=selectedFields.healthValue(role);fitness.status[role]=selectedFields.healthState(role);fitness.reason[role]=selectedFields.healthReason(role);}}requestFrame();}catch(e){}
    }
    function stopFitness() as Void {try{selectedFields.stop();}catch(e){}lifecycle.resetFitness();}
    (:typecheck(false)) function snapshotAt(now as Number or Long) as ClockSnapshot {
        if(selectedFields.expireHistory(now.toLong())){var health=["energy","stress"];for(var i=0;i<health.size();i+=1){var role=health[i];values[role]=selectedFields.healthValue(role);fitness.status[role]=selectedFields.healthState(role);fitness.reason[role]=selectedFields.healthReason(role);}}
        advanceSelection(now);
        if(context!=null){context.advanceFreshness(now);if(packet!=null&&packet.presentation==context){packet.stale=context.stale;}}
        var remaining=_schedule.remainingSeconds(now);
        if(context!=null&&context.displayTarget!=null){remaining=(context.displayTarget as Long)-now.toLong();}
        var current=new ClockSnapshot(_clock.localTimeText(),CountdownFormat.format(remaining));current.remainingUtc=remaining;
        current.lowCountdown=CountdownFormat.minutes(remaining);
        current.date=context==null?null:context.date;current.localCalendar=_clock.localCalendar();current.battery=fitness.display(values,"battery");
        if(context!=null){current.stale=context.stale;current.rescheduled=context.rescheduled;current.sourceHold=context.sourceHold;}
        return current;
    }
    // Selection transitions happen on a permitted frame, never by polling or
    // storage work on every countdown tick. A successor can replace this
    // waiting state only through a validated, source-bound admission.
    (:extendedCode) function resetRollover() as Void {passedSelections=[];}
    (:typecheck(false)) function selectionTarget(scene) {return scene.retentionTarget==null?scene.displayTarget:scene.retentionTarget;}
    (:typecheck(false)) function selectionPassed(scene) {
        if(scene==null||scene.retentionDeadline==null){return false;}
        var target=selectionTarget(scene);if(target==null){return false;}
        for(var i=0;i<passedSelections.size();i+=1){var row=passedSelections[i];if(row[0].equals(scene.launchId)&&row[1]==target&&row[2]==scene.retentionDeadline){return true;}}
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
            if(!selectionPassed(next)){passedSelections.add([next.launchId,selectionTarget(next),next.retentionDeadline]);if(passedSelections.size()>3){passedSelections=passedSelections.slice(passedSelections.size()-3,passedSelections.size());}}
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
    function setSettings(next as SceneSettings) as Void { stopFitness();selectedFields.invalidateSnapshot();lifecycle.rearmInitialFitness();var rolesChanged=!nativeSame(settings.slots,next.slots);settings=next;if(rolesChanged){lifecycle.resetFitness();values={};}lifecycle.invalidateFrame();if(lifecycle.shown()&&!admissionPending&&!sfrFallbackPrepared&&sfrBuild==null){presentation.restore(settings.language);}if(renderer!=null){renderer.prepare(context,settings);(renderer as SceneRenderer).useDownloaded(downloaded);} if(canForegroundWork()){refreshFitness();} }
    function refreshLocale() as Void {var previous=settings.language;settings.refreshLanguage();if(!previous.equals(settings.language)){setSettings(settings);}}
    (:extendedCode, :typecheck(false))
    // The scene digest binds selected art/map identity; bridge IDs and exact
    // qualified site data prevent reusing a visual for changed model or place.
    function packetVisualKey(next) {
        if(next==null||next.bridge==null||next.bridge["selection"]==null){return null;}
        return [next.bridge["selection"]["sha256"],next.bridge["ids"],next.bridge["site"],next.bridge["artRevision"]];
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
            context=refreshed;mapDecision.bind(refreshed);_schedule=refreshed==null?new ScheduleState(null,"empty"):refreshed.schedule;
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
        if (!lifecycle.shown() || admissionPending || assetCache == null || !assetCache.ready || packet == null || packet.bridge == null) { return; }
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
        stopSfrTimer();if(sfrBuild!=null){sfrBuild.dispose();}sfrBuild=null;sfrFallbackPrepared=false;sceneLifecycle.replace();visualKey=null;downloaded=null;lifecycle.invalidateFrame();
        if(next!=null && next.launchId.equals("")){next=null;}
        context=next;mapDecision.bind(next);_schedule=next==null?new ScheduleState(null,"empty"):next.schedule;
        if(renderer!=null){try{renderer.prepare(context,settings);(renderer as SceneRenderer).useDownloaded(downloaded);}catch(e){renderer=null;layoutReady=false;}if(lifecycle.mode()==LOW){prepareOptionalAod();}}
    }
    function canForegroundWork() as Boolean {return lifecycle.shown()&&(lifecycle.mode() == NOT_LOW)&&!_resumePending&&_resumeTimer==null&&deviceMode()==System.DISPLAY_MODE_HIGH_POWER;}
    function canAcceptBackground() as Boolean {return lifecycle.shown()&&deviceMode()!=System.DISPLAY_MODE_OFF&&(lifecycle.mode()==LOW||canForegroundWork());}
    // Release only rebuildable graphics while the strict candidate is resident;
    // retain the compact selected context, UTC schedule and successor facts.
    function beginAdmission() as Void {cancelSfrBuild();stopFitness();presentation.suspend();LocaleGraphemes.data=null;if(packet!=null&&context!=null){context.stale=packet.stale as Boolean;context.rescheduled=packet.rescheduled as Boolean;}packet=null;downloaded=null;assetCache=null;renderer=null;restMask=null;sceneBuffer=null;sceneScaleOptions=null;layoutReady=false;admissionPending=true;requestFrame();}
    function endAdmission() as Void {admissionPending=false;_resumePending=true;requestFrame();}
    (:typecheck(false))
    // Keep the last accepted scene while its durable packet is revalidated.
    // The packet is detached for the parser, but its presentation and qualified
    // visual remain the only visible scene until a replacement is admitted.
    function clearForRestore() as Void {
        if(packet!=null && context!=null){context.stale=packet.stale;context.rescheduled=packet.rescheduled;}
        packet=null;
    }
    function createSceneRenderer() as SceneRenderer {return new SceneRenderer(presentation);}
    function prepareRenderer() as Void {presentation.restore(settings.language);LocaleGraphemes.load();renderer=createSceneRenderer();renderer.mapDecision=mapDecision;renderer.prepare(context,settings);(renderer as SceneRenderer).useDownloaded(downloaded);mapDecision.restored();if(lifecycle.mode()==LOW){(renderer as SceneRenderer).prepareAod();}}
    function prepareOptionalAod() as Void {if(renderer!=null&&sfrBuild==null&&!sfrFallbackPrepared){try{(renderer as SceneRenderer).prepareAod();}catch(e){renderer=null;layoutReady=false;}}}
    function releaseRenderer() as Void {renderer=null;layoutReady=false;}
    function onLayout(dc as Graphics.Dc) as Void {
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
    function onUpdate(dc as Graphics.Dc) as Void {updateForDisplayMode(dc,deviceMode());}
    // LOW can interrupt a long foreground admission. Keep the accepted
    // context and draw the normal AOD using only temporary LOW resources;
    // they are released again before the parser resumes in HIGH.
    (:extendedCode, :typecheck(false)) function drawPendingLow(dc) {
        var now=_clock.utcSeconds();var minute=utcMinute(now);if(!lifecycle.frameDue(minute)){return;}
        try{values["battery"]=fitness.number(System.getSystemStats().battery,100);}catch(e){values["battery"]=null;}
        var current=snapshotAt(now);current.countdown=current.lowCountdown;
        var pin=mapDecision.pointVisible(true)&&mapDecision.matched;var pinX=mapDecision.x;var pinY=mapDecision.y;
        var worldPoint=mapDecision.worldPoint(true);
        var map=worldPoint==null?(WatchUi.loadResource(mapDecision.lowResource()) as Graphics.BitmapType):null;var font=WatchUi.loadResource(Rez.Fonts.Aod40) as Graphics.FontType;
        var oldContext=presentation.aodContextFont;var oldBattery=presentation.aodBatteryFont;var oldLocale=presentation.locale;presentation.locale=settings.language;
        try{if(oldContext==null){try{presentation.aodContextFont=Graphics.getVectorFont({:face=>["RobotoRegular","RobotoCondensedRegular"],:size=>47});}catch(ignore){}}if(oldBattery==null){try{presentation.aodBatteryFont=Graphics.getVectorFont({:face=>["RobotoRegular","RobotoCondensedRegular"],:size=>51});}catch(ignore){}}if(presentation.aodContextFont==null){presentation.aodContextFont=Graphics.FONT_SMALL;}if(presentation.aodBatteryFont==null){presentation.aodBatteryFont=Graphics.FONT_SMALL;}
            var canvas=null;var target=dc;var side=dc.getWidth()<dc.getHeight()?dc.getWidth():dc.getHeight();
            if(dc.getWidth()!=390||dc.getHeight()!=390){canvas=Graphics.createBufferedBitmap({:width=>390,:height=>390,:colorDepth=>16}).get();target=canvas.getDc();}
            SceneAod.draw(target,current,minute,presentation,font,settings,map,pin,pinX,pinY,worldPoint);
            var mask=WatchUi.loadResource(Rez.Drawables.AodRestMask) as Graphics.BitmapType;var phase=((minute%4+4)%4).toNumber();target.drawBitmap(-(phase%2),-(phase/2),mask);
            if(canvas!=null){var transform=new Graphics.AffineTransform();transform.scale(side.toFloat()/390.0,side.toFloat()/390.0);dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();dc.drawBitmap2((dc.getWidth()-side)/2,(dc.getHeight()-side)/2,canvas,{:transform=>transform,:filterMode=>Graphics.FILTER_MODE_POINT});}lifecycle.framePainted(minute);
        }finally{presentation.aodContextFont=oldContext;presentation.aodBatteryFont=oldBattery;presentation.locale=oldLocale;}
    }
    function afterLowFrame() as Void {
        if(admissionPending){return;}
        // Cold LOW must not depend on a preceding ACTIVE callback. Consume one
        // startup/settings lease after the first clock frame, then stop sources;
        // later LOW frames retain the result without provider polling/timers.
        if(lifecycle.takeInitialLowFitness()){
            try{readFitnessSnapshot(_clock.utcSeconds());}catch(e){}finally{stopFitness();}
            lifecycle.invalidateFrame();requestFrame();
        }
        if(bootstrapPending||lowNeedsLoader){bootstrapPending=false;lowNeedsLoader=false;if(pendingLoader!=null){try{pendingLoader.invoke();}catch(e){}}}
    }
    (:typecheck(false)) function updateForDisplayMode(dc as Graphics.Dc, displayMode as System.DisplayMode) as Void {
        // An OS draw queued before hide must not recreate LOW resources or
        // load facts after that lifecycle owner has revoked visible work.
        if(!lifecycle.shown()){return;}
        // OFF is not a third layout. Stop any owned work without scheduling a
        // redraw or loading resources; a later HIGH observation resumes after
        // its first frame, and LOW never starts active sampling or decoding.
        if(displayMode==System.DISPLAY_MODE_OFF){
            stopForDisplayOff();return;
        }
        // Garmin may deliver a draw before the corresponding sleep callback.
        syncDisplayMode(displayMode);
        if(lifecycle.mode()==NOT_LOW&&canForegroundWork()){refreshFitnessIfDue(true);}

        if(!(lifecycle.mode() == NOT_LOW) && !lifecycle.frameDue(utcMinute(_clock.utcSeconds()))){return;}
        if(lifecycle.mode()==LOW&&(bootstrapPending||admissionPending||sfrFallbackPrepared||renderer==null)){
            try{drawPendingLow(dc);}catch(e){mapDecision.failure();drawClockFallback(dc);}
            // The first LOW frame must not leave cached facts waiting for an
            // ACTIVE frame, which may never arrive while the watch is worn.
            afterLowFrame();
            return;
        }
        if((renderer==null||!layoutReady) && lifecycle.mode()==NOT_LOW){onLayout(dc);}
        if((bootstrapPending||admissionPending)&&lifecycle.mode()==NOT_LOW&&renderer==null){queueResumeAfterFrame();return;}
        if(lifecycle.mode()==LOW&&(renderer==null||!layoutReady)&&sfrBuild==null&&!sfrFallbackPrepared){onLayout(dc);}
        if(lifecycle.mode()==LOW&&renderer!=null&&!(renderer as SceneRenderer).fonts.hasKey("aod")){prepareOptionalAod();}
        if(renderer==null){drawClockFallback(dc);if(lifecycle.mode()==NOT_LOW){queueResumeAfterFrame();}return;}
        // Skip the entire LOW update, including mask and scaled-buffer blit.
        if(sceneBuffer!=null){var bitmap=sceneBuffer as Graphics.BufferedBitmap;var target=bitmap.getDc();drawScene(target);applyPixelRest(target);if(sceneX!=0||sceneY!=0){dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();}dc.drawBitmap2(sceneX,sceneY,bitmap,sceneScaleOptions);if(lifecycle.mode()==LOW){afterLowFrame();}if(lifecycle.mode()==NOT_LOW&&(renderer!=null||sfrFallbackPrepared||sfrBuild!=null)){queueResumeAfterFrame();}return;}
        drawScene(dc);applyPixelRest(dc);
        if(lifecycle.mode()==LOW){afterLowFrame();}
        if(lifecycle.mode()==NOT_LOW&&(renderer!=null||sfrFallbackPrepared||sfrBuild!=null)){queueResumeAfterFrame();}
    }
    // Built-in fonts and local system clock do not depend on feed, assets or
    // health providers. This is temporary while the full scene is unavailable.
    function joinDetail(base as String,detail as String) as String {return base.equals("")?detail:(detail.equals("")?base:base+" · "+detail);}
    (:typecheck(false)) function drawClockFallback(dc as Graphics.Dc) as Void {
        var x=dc.getWidth()/2;var y=dc.getHeight()/2;var active=lifecycle.mode()==NOT_LOW;var parts=_clock.localCalendar();
        if(lifecycle.mode()==LOW){var minute=utcMinute(_clock.utcSeconds());var phase=((minute%4+4)%4).toNumber();x+=(phase%2==0?-1:1);y+=(phase/2==0?-1:1);lifecycle.framePainted(minute);}
        dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();
        dc.setColor(settings.clockColor,Graphics.COLOR_TRANSPARENT);
        dc.drawText(x,active?y-77:y-15,active?Graphics.FONT_NUMBER_MEDIUM:Graphics.FONT_MEDIUM,_clock.localTimeText(),Graphics.TEXT_JUSTIFY_CENTER);
        if(parts.size()==3){dc.drawText(x,active?y-107:y-45,Graphics.FONT_TINY,parts[1].format("%02d")+"."+parts[2].format("%02d"),Graphics.TEXT_JUSTIFY_CENTER);}
        // Keep admitted facts independent of the optional graphics as well.
        // Their own failure cannot prevent the already drawn clock/date.
        try{if(context!=null){var now=_clock.utcSeconds();advanceSelection(now);var selected=context as SceneContext or Null;if(selected!=null){var snap=snapshotAt(now);var value=lifecycle.mode()==LOW?snap.lowCountdown:snap.countdown;dc.setColor(SceneAod.countdownColor(snap,settings),Graphics.COLOR_TRANSPARENT);dc.drawText(x,active?y+7:y+25,Graphics.FONT_TINY,value,Graphics.TEXT_JUSTIFY_CENTER);if(snap.rescheduled){SceneAod.rescheduleMark(dc,x+dc.getTextWidthInPixels(value,Graphics.FONT_TINY)/2+8,active?y+11:y+29);}if(snap.sourceHold){SceneAod.holdMark(dc,x+dc.getTextWidthInPixels(value,Graphics.FONT_TINY)/2+(snap.rescheduled?20:8),active?y+11:y+29);}dc.setColor(0xD4DFEB,Graphics.COLOR_TRANSPARENT);dc.drawText(x,active?y+124:y+55,Graphics.FONT_XTINY,active?presentation.fit(dc,selected.site,Graphics.FONT_XTINY,242):selected.site,Graphics.TEXT_JUSTIFY_CENTER);dc.drawText(x,active?y-159:y+80,Graphics.FONT_XTINY,active?presentation.fit(dc,selected.rocket,Graphics.FONT_XTINY,238):joinDetail(selected.rocket,selected.purpose),Graphics.TEXT_JUSTIFY_CENTER);if(active){var company=selected.operatorShort.equals("")?selected.operator:selected.operatorShort;dc.drawText(x,y-133,Graphics.FONT_XTINY,presentation.fit(dc,joinDetail(company,selected.purpose),Graphics.FONT_XTINY,282),Graphics.TEXT_JUSTIFY_CENTER);}}}}catch(e){}
        LocaleGraphemes.data=null;
        // Mandatory-resource recovery has no metric composition. The clear
        // above removes partial fields before clock/date and accepted facts
        // are redrawn. A healthy next frame rebuilds the canonical renderer.
        // Bounded direct-draw map after clock and facts: an optional failure
        // must never erase or prevent the clock. Its source point is separate
        // from downloaded artwork and is absent for an unknown event location.
        try{var left=(dc.getWidth()-195)/2;FallbackWorld.draw(dc,left,15);if(mapDecision.pointVisible(true)){FallbackMap.point(dc,mapDecision.point,left,15);}}catch(e){}
    }
    function applyPixelRest(dc as Graphics.Dc) as Void {
        if(lifecycle.mode() == NOT_LOW){return;}
        if(restMask==null){try{restMask=WatchUi.loadResource(Rez.Drawables.AodRestMask) as Graphics.BitmapType;}catch(e){return;}}
        var minute=utcMinute(_clock.utcSeconds());var phase=((minute%4+4)%4).toNumber();
        dc.drawBitmap(-(phase%2),-(phase/2),restMask as Graphics.BitmapType);
    }
    function drawScene(dc as Graphics.Dc) as Void {
        var now=_clock.utcSeconds();var minute=utcMinute(now);
        if(!(lifecycle.mode() == NOT_LOW) && !lifecycle.frameDue(minute)){return;}
        // One inexpensive system battery read per permitted LOW snapshot.
        // Do not start the active health sampler or any timer in LOW.
        if(!(lifecycle.mode() == NOT_LOW)){try{values["battery"]=fitness.number(System.getSystemStats().battery,100);}catch(e){values["battery"]=null;}}
        // Renderer release is synchronous; retain the last frame if an OS draw
        // arrives before its rebind rather than rendering a separate mode.
        if(renderer==null){return;}
        var current=snapshotAt(now);
        var drawing=renderer as SceneRenderer;
        try{if((lifecycle.mode() == NOT_LOW)){drawing.active(dc,current,settings,values,fitness,0.0);}
        else{current.countdown=current.lowCountdown;drawing.aod(dc,current,minute,settings);lifecycle.framePainted(minute);}}
        catch(e){mapDecision.failure();renderer=null;layoutReady=false;drawClockFallback(dc);}
        finally{if(sfrFallbackPrepared||sfrBuild!=null){LocaleGraphemes.data=null;}}

    }
    function onEnterSleep() as Void {if(!lifecycle.sleep()){return;}var display=deviceMode();syncDisplayMode(display);if(display!=System.DISPLAY_MODE_OFF){prepareOptionalAod();} }
    function onExitSleep() as Void {
        // A view can first be shown in LOW without having received onEnterSleep.
        // The first wake must still reconcile the actual OS display mode.
        var woke=lifecycle.wake();var before=lifecycle.mode();var display=deviceMode();syncDisplayMode(display);
        if(woke&&lifecycle.shown()&&display!=System.DISPLAY_MODE_OFF&&before==lifecycle.mode()){requestFrame();}
    }
    function onHide() as Void {if(!lifecycle.hide()){return;}_resumePending=false;lowNeedsLoader=false;stopResume();cancelSfrBuild();stopFitness();if(cancelAdmission!=null){cancelAdmission.invoke();}releaseVisualForSettings();}
    // Settings must not retain the decoded scene while its picker is open.
    // The accepted packet and source remain; onLayout/onShow rebuild the view.
    function releaseVisualForSettings() as Void {downloaded=null;renderer=null;restMask=null;sceneBuffer=null;sceneScaleOptions=null;layoutReady=false;sceneLifecycle.replace();presentation.suspend();}
    function releaseForSettings() as Void {onHide();}
    (:typecheck(false))
    // Fixed SDK-minimum cadence; repeated preparation cannot postpone a pending
    // slice. Each decoder slice still has its existing18ms/16row work budget.
    function startSfrTimer() as Void {if(!lifecycle.shown()||(!layoutReady&&sfrBuild==null&&!sfrFallbackPrepared)||!(lifecycle.mode() == NOT_LOW)||deviceMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}if(sfrTimer==null){sfrTimer=newViewTimer();sfrTimer.start(method(:sfrStep),50,true);}}
    (:typecheck(false))
    function stopSfrTimer() as Void {if(sfrTimer!=null){sfrTimer.stop();sfrTimer=null;}sfrDeferred=false;}
    (:typecheck(false))
    function cancelSfrBuild() as Void {
        stopSfrTimer();if(sfrBuild!=null){sfrBuild.dispose();}sfrBuild=null;sfrFallbackPrepared=false;sceneLifecycle.cancel();
    }
    // Native Storage can need more than one copy of a verified shard: the
    // observed 4,028-byte read failed with 8,184 bytes free. Reserve two shard
    // copies plus bounded decode blocks and clock work, and a possible RGB
    // scanline growth copy only before the row has been allocated.
    (:typecheck(false)) function optionalHeapFree(){try{var stats=System.getSystemStats();return stats.totalMemory-stats.usedMemory;}catch(e){return 0;}}
    (:typecheck(false)) function sfrReadReserve(){
        // A root or role descriptor reader already owns the input; its bounded
        // hash and parser continuations perform no further storage read.
        // Decoder allocation remains a later step with the full reserve.
        if(sfrBuild!=null&&!sfrBuild.closureChecked&&sfrBuild.pendingRead!=null){return 8192;}
        if(sfrBuild!=null&&sfrBuild.decoder!=null){var decoder=sfrBuild.decoder;if(decoder.data!=null){return 128*3+512;}var shard=decoder.descriptor["shards"][decoder.shard];var row=decoder.row.size()==0?2*decoder.width*decoder.channels:0;return 2*shard[2]+row+128*3+512;}
        if(sfrBuild!=null&&sfrBuild.closureChecked&&sfrBuild.closureAt<sfrBuild.expected.size()){var largest=0;for(var i=sfrBuild.closureAt;i<sfrBuild.expected.size()&&i<sfrBuild.closureAt+4;i+=1){if(sfrBuild.expected[i][2]>largest){largest=sfrBuild.expected[i][2];}}return 2*largest+128*3+512;}
        return 2*4096+2*390*3+128*3+512;
    }
    (:typecheck(false)) function deferSfr(){stopSfrTimer();sfrDeferred=true;sfrTimer=newViewTimer();sfrTimer.start(method(:sfrStep),5000,true);requestFrame();}
    (:typecheck(false)) function resumeSfrCadence(){if(sfrDeferred){stopSfrTimer();sfrTimer=newViewTimer();sfrTimer.start(method(:sfrStep),50,true);}}
    (:typecheck(false))
    function sfrStep() as Void {

        if (deviceMode()!=System.DISPLAY_MODE_HIGH_POWER) { stopSfrTimer(); return; }
        if (!lifecycle.shown() || !(lifecycle.mode() == NOT_LOW) || packet==null || packet.bridge==null || !sceneLifecycle.pending()) { stopSfrTimer(); return; }
        try {
            if (sfrBuild==null) {
                // Release rebuildable resources before testing available heap;
                // a refused optional decode retries slowly with clock intact.
                if(!sfrFallbackPrepared){sfrBundled=renderer!=null&&renderer.aodPin&&renderer.aodResource!=null;if(renderer!=null){(renderer as SceneRenderer).releaseAod();}restMask=null;LocaleGraphemes.data=null;sfrFallbackPrepared=true;}
                if(optionalHeapFree()<sfrReadReserve()){if(!sfrDeferred){deferSfr();}return;}
                resumeSfrCadence();var token=sceneLifecycle.begin();if(token==null){return;}sfrGeneration=token;
                sfrBuild=createSfrBuild(assetCache.store,assetCache.base,packet);sfrBuild.preferBundled=sfrBundled;return;
            }
            if(optionalHeapFree()<sfrReadReserve()){if(!sfrDeferred){deferSfr();}return;}
            resumeSfrCadence();
            if (sfrBuild.step()) {
                var result=sfrBuild.result;stopSfrTimer();sfrBuild=null;sfrFallbackPrepared=false;
                if (sceneLifecycle.complete(sfrGeneration)) {
                    downloaded=result;if(renderer==null){prepareRenderer();}else{(renderer as SceneRenderer).useDownloaded(downloaded);prepareOptionalAod();}_resumePending=true;
                    requestFrame();
                }
            }
        } catch(e) {

            if(sfrBuild!=null){sfrBuild.dispose();}sfrBuild=null;stopSfrTimer();sfrFallbackPrepared=false;sceneLifecycle.fail(sfrGeneration);_resumePending=true;requestFrame();
        }
    }

    (:typecheck(false)) function createSfrBuild(store,base,packet) {return new NativeSfrBuild(store,base,packet);}

}
