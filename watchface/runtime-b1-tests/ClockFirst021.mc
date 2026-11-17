import Toybox.Application;
import Toybox.Lang;
import Toybox.Graphics;
import Toybox.Complications;
import Toybox.System;
import Toybox.Test;
import Toybox.Time;
import Toybox.WatchUi;

(:test,:typecheck(false)) class B1Clock extends WatchClock {
    var reads=0;var dates=0;var now=1794818604;
    function utcSeconds(){return now;}
    function localTimeText(){reads+=1;return "08:38";}
    function localCalendar(){dates+=1;return [1,16,11];}
}
(:test,:typecheck(false)) class B1UnavailableRenderer extends SpaceFoxView {
    function initialize(clock){SpaceFoxView.initialize(clock,new ScheduleState(null,"empty"));}
    function prepareRenderer(){throw new Lang.InvalidValueException("optional renderer unavailable");}
}
(:test,:typecheck(false)) class B1Loader {var calls=0;function load(){calls+=1;}}
(:test,:typecheck(false)) class B1BadLoader extends SpaceFoxApp {
    function initialize(){SpaceFoxApp.initialize();}
    function performReload(){throw new Lang.InvalidValueException("optional feed unavailable");}
}
(:test,:typecheck(false)) class B1BadSettings extends SpaceFoxApp {
    function initialize(){SpaceFoxApp.initialize();}
    function initialSettings(){throw new Lang.InvalidValueException("settings unavailable");}
}
(:test,:typecheck(false)) class B1BrokenFitness extends Fitness {
    function sample(now){throw new Lang.InvalidValueException("health unavailable");}
}
(:test,:typecheck(false)) class B1BrokenFields extends SelectedFields {
    function includes(id){throw new Lang.InvalidValueException("complication unavailable");}
}
(:test,:typecheck(false)) function b1ClockWithUnavailableSettings(logger) {
    var app=new B1BadSettings();var view=app.getInitialView()[0];
    var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
    Test.assert(view!=null&&view.bootstrapPending);view.onShow();view.onLayout(dc);view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);
    Test.assert(app.feed==null);view.onHide();logger.debug("B1_CLOCK settings_failure_first_frame=true");return true;
}
(:test,:typecheck(false)) function b1ClockWithUnavailableHealth(logger) {
    var clock=new B1Clock();var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));view.fitness=new B1BrokenFitness();
    var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();view.onShow();view.onLayout(dc);
    view.refreshFitness();view.selectedFields=new B1BrokenFields();view.fieldsChanged(new Complications.Id(23));
    view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);Test.assert(clock.reads>0&&clock.dates>0);
    view.onHide();logger.debug("B1_CLOCK health_and_callback_failure=true");return true;
}
(:test,:typecheck(false)) class B1BrokenDrawing extends SceneRenderer {
    function initialize(){SceneRenderer.initialize(null);}
    function active(dc,current,settings,values,fitness,progress){throw new Lang.InvalidValueException("optional drawing unavailable");}
}
(:test,:typecheck(false)) function b1ActualColdViewDefersCache(logger) {
    var app=new SpaceFoxApp();var view=app.getInitialView()[0];
    var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
    Test.assert(app.feed==null);view.onShow();view.onLayout(dc);
    view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);
    Test.assert(app.feed==null&&view.bootstrapPending);
    view.stopResume();view.resumeAfterFrame();
    Test.assert(app.feed instanceof NativeCache&&!view.bootstrapPending&&view.admissionPending&&view.fitnessTimer==null);
    view.onHide();logger.debug("B1_ACTUAL_INITIAL cache_before_frame=false cache_after_frame=true");return true;
}
// Switching a configured source takes the same strict-restore path as a cold
// cache, but begins with an existing renderer and must release it until done.
(:test,:typecheck(false)) function peerSourceChangeDefersRenderer021(logger) {
    Application.Storage.clearValues();
    var clock=new B1Clock();var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));
    var app=new SpaceFoxApp();app.view=view;app.feed=new NativeCache("https://fixture.invalid/old-source",null);
    app.batchingForeground=true;view.cancelAdmission=app.method(:cancelWork);
    var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
    view.onShow();view.onLayout(dc);Test.assert(view.renderer!=null);
    NativeForegroundApp.reload(app);
    Test.assertMessage(app.restorePending&&view.admissionPending&&view.renderer==null,"source switch must not rebuild renderer during strict restore");
    var before=clock.reads;view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);
    Test.assert(clock.reads>before&&view.renderer==null);
    var steps=0;while(app.restorePending){NativeForegroundApp.restoreStep(app);steps+=1;Test.assert(steps<20);}
    Test.assert(!view.admissionPending);view.onLayout(dc);Test.assert(view.renderer!=null);
    view.onHide();logger.debug("PEER_SOURCE_CHANGE restore_pending=true renderer_deferred=true clock_visible=true rebind=true");return true;
}
(:test,:typecheck(false)) function b1ClockAfterDrawingFailure(logger) {
    var clock=new B1Clock();var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));
    view.renderer=new B1BrokenDrawing();var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
    view.onShow();view.onLayout(dc);view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);
    Test.assert(clock.reads>=2&&clock.dates>=2&&view.renderer==null);
    view.onHide();logger.debug("B1_CLOCK drawing_failure_fallback=true");return true;
}
(:test,:typecheck(false)) function b1ClockAfterLoaderFailure(logger) {
    var clock=new B1Clock();var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));
    var loader=new B1BadLoader();loader.view=view;view.bootstrapPending=true;view.pendingLoader=loader.method(:reloadFeed);
    var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
    view.onShow();view.onLayout(dc);view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);
    view.stopResume();view.resumeAfterFrame();view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);
    Test.assert(clock.reads>=2&&clock.dates>=2&&!view.bootstrapPending);
    view.onHide();logger.debug("B1_CLOCK loader_failure_time_date_continue=true");return true;
}
(:test,:typecheck(false)) function b1ClockBeforeLoader(logger) {
    var clock=new B1Clock();var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));
    var loader=new B1Loader();view.bootstrapPending=true;view.pendingLoader=loader.method(:load);
    var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
    view.onShow();view.onLayout(dc);view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);
    Test.assert(clock.reads>0&&clock.dates>0&&loader.calls==0&&view.renderer==null);
    view.stopResume();view.resumeAfterFrame();Test.assert(loader.calls==1&&!view.bootstrapPending);
    view.onHide();logger.debug("B1_FIRST_FRAME clock_date=true loader_before_frame=false loader_after_frame=true");return true;
}
(:test,:typecheck(false)) function b1LowBeforeLoader(logger) {
    var clock=new B1Clock();var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));
    var loader=new B1Loader();view.bootstrapPending=true;view.pendingLoader=loader.method(:load);
    var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
    view.onShow();view.onLayout(dc);view.updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);
    Test.assert(clock.reads>0&&clock.dates>0&&loader.calls==0&&view.bootstrapPending);
    var first=clock.reads;view.updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);Test.assert(clock.reads==first);
    clock.now+=60;view.updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);Test.assert(clock.reads==first+1);
    view.onHide();logger.debug("B1_LOW_FIRST_FRAME clock_date=true loader_deferred=true");return true;
}
(:test,:typecheck(false)) function b1ClockWithUnavailableRenderer(logger) {
    var clock=new B1Clock();var view=new B1UnavailableRenderer(clock);
    var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
    view.onShow();view.onLayout(dc);view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);
    Test.assertMessage(clock.reads>0&&clock.dates>0,"clock and date must render when optional renderer is unavailable");
    view.onHide();logger.debug("B1_CLOCK optional_renderer_failed time_and_date_read=true");return true;
}
(:test,:typecheck(false)) class B1RolloverCancel {var view;var calls=0;function initialize(v){view=v;}function cancel(){calls+=1;view.admissionPending=false;}}
(:test,:typecheck(false)) function b1CapturedSuccessorTicksInFallback(logger) {
    var store=new NativeStore();var ref={"path"=>"wire3/catalogs/83226c3bce7f6da4d3830ffbff16aefe5632054f2eb23675ed2cc6ec8dcc82d0.json","sha256"=>"83226c3bce7f6da4d3830ffbff16aefe5632054f2eb23675ed2cc6ec8dcc82d0","decodedBytes"=>1386};
    Test.assert(new NativeImmutable(store).put(ref,b1Response(ref["path"])));
    var clock=new B1Clock();var raw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];
    var packet=new TestNativeBridgeFeed(raw,clock.now,store);feedScene(packet,clock.now);
    Test.assert(packet.upcomingScenes.size()>0);var selected=packet.upcomingScenes[0];
    Test.assert(selected.launchId.equals("ll2:launch:76617033-4dc0-4448-b50c-e5b0d5a18539"));
    var view=new B1UnavailableRenderer(clock);view.setContext(selected);
    var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
    view.onShow();view.onLayout(dc);view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);
    Test.assertEqual(view.snapshotAt(clock.now).countdown,"T- 66:16:36");
    clock.now+=2;view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);
    Test.assertEqual(view.snapshotAt(clock.now).countdown,"T- 66:16:34");
    view.updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);
    Test.assertEqual(view.snapshotAt(clock.now).lowCountdown,"T- 66:17");
    var rollover=new B1RolloverCancel(view);view.cancelAdmission=rollover.method(:cancel);view.admissionPending=true;selected.retentionDeadline=clock.now;view.advanceSelection(clock.now);Test.assert(rollover.calls==1&&view.context==selected&&!view.admissionPending);
    view.cancelAdmission=null;view.onHide();logger.debug("B1_CAPTURED_MINUTE active_tick=2s low_minute=true fallback=true");return true;
}
(:test,:typecheck(false)) class B1AdmissionFields extends SelectedFields {
    var starts=0;var reads=0;var stops=0;var running=false;var lastSlots=null;
    function active(){return running;}
    function start(slots,callback){starts+=1;running=true;lastSlots=slots;}
    function read(locale){reads+=1;energy=68;}
    function stop(){if(running){stops+=1;}running=false;energy=null;}
    function includes(id){return running;}
}
(:test,:typecheck(false)) class B1AdmissionFitness extends Fitness {
    function sample(now){return {"energy"=>(selectedFields==null?null:selectedFields.energy),"steps"=>123,"heart"=>72,"battery"=>80};}
}
(:test,:typecheck(false)) function b1AdmissionFitnessLifecycle(logger) {
    var clock=new B1Clock();var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));
    var fields=new B1AdmissionFields();view.selectedFields=fields;view.fitness=new B1AdmissionFitness();view.fitness.selectedFields=fields;
    var settings=new SceneSettings({"Field1"=>1,"Field2"=>2,"Field3"=>3,"Field4"=>4});
    view.setSettings(settings);view.onShow();var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
    view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);view.stopResume();view.resumeAfterFrame();
    Test.assert(fields.starts==1&&fields.reads==1&&fields.lastSlots.size()==4);
    view.beginAdmission();view.beginAdmission();Test.assert(fields.stops==1&&!fields.active()&&view.fitnessTimer==null&&view.fallbackClockTimer!=null);
    view.setSettings(settings);view.refreshFitness();view.fieldsChanged(new Complications.Id(23));
    Test.assert(fields.starts==1&&fields.reads==1);
    view.endAdmission();view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);view.stopResume();view.resumeAfterFrame();
    Test.assert(fields.starts==2&&fields.reads==2&&nativeSame(fields.lastSlots,settings.slots));
    view.beginAdmission();view.syncDisplayMode(System.DISPLAY_MODE_LOW_POWER);view.onHide();
    Test.assert(fields.stops==2&&!fields.active()&&view.fitnessTimer==null&&view.fallbackClockTimer==null);
    logger.debug("B1_FIELDS admission_stop_once=true pending_no_restart=true four_slots_resume=true low_hide_idempotent=true");return true;
}

(:test,:typecheck(false)) function b1GraphemeReleaseAndRebind(logger){
    var clock=new B1Clock();var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));view.onShow();
    LocaleGraphemes.load();Test.assert(LocaleGraphemes.data!=null&&LocaleGraphemes.extend(0x301));
    view.beginAdmission();Test.assert(LocaleGraphemes.data==null&&view.presentation.label==null&&view.presentation.dictionary==null);view.endAdmission();
    var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);
    Test.assert(LocaleGraphemes.data!=null&&LocaleGraphemes.extend(0x301)&&view.presentation.label!=null);
    view.presentation.prepare("en");Test.assertEqual(view.presentation.calendar([1,16,11]),"Sun 16.11");
    view.presentation.prepare("ru");Test.assertEqual(view.presentation.calendar([1,16,11]),"Вс 16.11");
    view.onHide();logger.debug("B1_GRAPHEME optional_release=true active_rebind=true en_ru_calendar=true");return true;
}
