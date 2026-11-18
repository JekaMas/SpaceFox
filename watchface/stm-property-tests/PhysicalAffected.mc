import Toybox.Test;
import Toybox.Lang;

(:test,:typecheck(false)) class PbtFallbackFitnessView extends PbtView {
 function initialize(){PbtView.initialize();}
 function refreshFitnessWork() as Void {SpaceFoxView.refreshFitnessWork();}
}

// One clock timer owns both the visible one-second tick and the minute-gated
// health refresh during optional art work. It must not discard last values.
(:test,:typecheck(false)) function fallbackFitnessTimerOwnership(logger){
 var v=new PbtFallbackFitnessView();v.onShow();v.refreshFitness();
 Test.assert(v.fitnessTimer!=null);Test.assertEqual(v.lowSnapshots,1);
 v.startFallbackClock();Test.assert(v.fitnessTimer==null);Test.assert(v.fallbackClockTimer!=null);
 v.fallbackClockTick();Test.assertEqual(v.lowSnapshots,1);Test.assert(v.fitnessTimer==null);
 v.clock.now+=60;v.fallbackClockTick();Test.assertEqual(v.lowSnapshots,2);Test.assert(v.fitnessTimer==null);
 v.stopFallbackClock();Test.assert(v.fallbackClockTimer==null);Test.assert(v.fitnessTimer!=null);
 Test.assertEqual(v.lowSnapshots,2);v.onHide();pbtCheckViewReleased(v,0,0,[]);
 logger.debug("FALLBACK_FITNESS one_clock=true minute_refresh=true normal_timer_restored=true");return true;
}

// Model the observed fr165 three-active-timer budget, including a one-shot
// callback until it returns. This exercises the real view timer handover.
(:test,:typecheck(false)) class PbtTimerBudget {var active=0;var peak=0;var violations=0;var timers=[];}
(:test,:typecheck(false)) class PbtBudgetTimer extends Toybox.Timer.Timer {
 var budget;var callback=null;var repeating=false;var active=false;
 function initialize(b){budget=b;}
 function start(cb as Method,ms as Number,repeat as Boolean) as Void {
  if(active){stop();}callback=cb;repeating=repeat;active=true;budget.active+=1;
  if(budget.active>budget.peak){budget.peak=budget.active;}if(budget.active>3){budget.violations+=1;}
 }
 function stop() as Void {if(active){active=false;budget.active-=1;}callback=null;}
 function fire(){if(!active||callback==null){return false;}var cb=callback;if(!repeating){callback=null;}cb.invoke();if(!repeating&&active){active=false;budget.active-=1;}return true;}
}
(:test,:typecheck(false)) class PbtBudgetArtView extends PbtArtView {
 var budget;
 function initialize(b){budget=b;PbtArtView.initialize();}
 function newViewTimer() as Toybox.Timer.Timer {var timer=new PbtBudgetTimer(budget);budget.timers.add(timer);return timer;}
 function refreshFitnessWork() as Void {SpaceFoxView.refreshFitnessWork();}
}
(:test,:typecheck(false)) function foregroundArtTimerBudget(logger){
 var budget=new PbtTimerBudget();var v=new PbtBudgetArtView(budget);v.onShow();
 var payload=pbtSnapshot(85,1795042260l);payload[6]={"selection"=>{"sha256"=>"selection"},"transfer"=>{"sha256"=>"transfer"},"ids"=>[],"site"=>null};
 v.setPacket(new NativeTrustedPacket(payload));v.setAssetCache(new PbtArtSource(new PbtMemoryStore()));
 v.prepareVisual();v.sfrStep();v.startSfrTimer();
 Test.assert(v.sfrTimer!=null&&v.fallbackClockTimer!=null);Test.assertEqual(budget.violations,0);
 v.queueResumeAfterFrame();Test.assertEqual(budget.active,3);Test.assertEqual(budget.violations,0);
 // The one-shot remains budgeted while its callback starts health work.
 var resume=budget.timers[budget.timers.size()-1] as PbtBudgetTimer;Test.assert(resume.fire());
 Test.assertEqual(budget.violations,0);Test.assert(v.fitnessTimer==null);Test.assertEqual(v.lowSnapshots,1);
 var tick=v.fallbackClockTimer as PbtBudgetTimer;Test.assert(tick.fire());Test.assertEqual(v.lowSnapshots,1);
 v.clock.now+=60;Test.assert(tick.fire());Test.assertEqual(v.lowSnapshots,2);Test.assertEqual(budget.violations,0);
 v.cancelSfrBuild();v.stopFallbackClock();Test.assert(v.fitnessTimer!=null);Test.assertEqual(budget.violations,0);
 // Re-admitting the same source after cancellation hands the cadence back to
 // fallback and starts a fresh SFR job without exceeding the same budget.
 v.prepareVisual();v.sfrStep();v.startSfrTimer();
 Test.assert(v.sfrTimer!=null&&v.fallbackClockTimer!=null&&v.fitnessTimer==null);
 Test.assertEqual(v.lowSnapshots,2);Test.assertEqual(budget.violations,0);
 v.onHide();Test.assertEqual(budget.active,0);Test.assertEqual(budget.violations,0);Test.assert(budget.peak<=3);
 logger.debug("FOREGROUND_TIMER_BUDGET peak="+budget.peak+" violations="+budget.violations+" minute_reads="+v.lowSnapshots);return true;
}

// Reuse the two existing production-bound sequence generators at their short
// selected scope after the wake and metric-source contracts changed.
(:test,:typecheck(false)) function physicalAffectedStateSequences(logger){
 Test.assert(generatedViewLifecycle(logger));
 Test.assert(generatedFitnessOwners(logger));
 Test.assert(coldLowAcquiresOneFieldSnapshot(logger));
 logger.debug("PHYSICAL_AFFECTED view_and_fitness_generators plus cold_low=true");return true;
}

// The captured pre-revision snapshot is admitted, but its rocket must not
// replace a specific bundled model. Unknown/generic IDs may use remote art.
// A revision-only change is an actual view event and invalidates the old job.
(:test,:typecheck(false)) function rocketArtworkRevisionContext(logger){
 var source=pbtSnapshot(85,1795042260l);source[6]={"selection"=>null};
 var owner=new NativeSfrBuild(null,"https://pbt.invalid",new NativeTrustedPacket(source));
 Test.assert(owner.useBundledRocket("ll2:configuration:17",null));
 Test.assert(!owner.useBundledRocket("ll2:configuration:17",1));
 Test.assert(!owner.useBundledRocket("ll2:configuration:17",2));
 Test.assert(!owner.useBundledRocket("ll2:configuration:511",null));
 Test.assert(!owner.useBundledRocket("ll2:configuration:999999999",null));
 var view=new PbtArtView();view.onShow();var first=pbtSnapshot(85,1795042260l);
 first[6]={"selection"=>{"sha256"=>"selection"},"transfer"=>{"sha256"=>"transfer"},"ids"=>[],"site"=>null};
 view.setPacket(new NativeTrustedPacket(first));view.setAssetCache(new PbtArtSource(new PbtMemoryStore()));view.prepareVisual();view.sfrStep();
 var oldToken=view.sfrGeneration;Test.assert(view.sfrBuild!=null);
 var next=pbtSnapshot(86,1795042260l);next[6]={"selection"=>{"sha256"=>"selection"},"transfer"=>{"sha256"=>"transfer"},"ids"=>[],"site"=>null,"artRevision"=>1};
 view.setPacket(new NativeTrustedPacket(next));Test.assert(view.sfrBuild==null);Test.assert(!view.sceneLifecycle.complete(oldToken));
 Test.assert(view.context.modelId.equals("ll2:configuration:17"));Test.assert(view.context.point!=null);
 // setPacket detaches the old source. A fresh admitted asset source is an
 // independent event and is required before the next immutable job starts.
 view.setAssetCache(new PbtArtSource(new PbtMemoryStore()));view.prepareVisual();view.sfrStep();var nextToken=view.sfrGeneration;Test.assert(view.sfrBuild!=null);
 var later=pbtSnapshot(87,1795042260l);later[6]={"selection"=>{"sha256"=>"selection2"},"transfer"=>{"sha256"=>"transfer2"},"ids"=>[],"site"=>null,"artRevision"=>2};
 view.setPacket(new NativeTrustedPacket(later));Test.assert(view.sfrBuild==null);Test.assert(!view.sceneLifecycle.complete(nextToken));
 Test.assert(view.context.modelId.equals("ll2:configuration:17"));Test.assert(view.context.point!=null);
 logger.debug("ART_REVISION old_specific=local old_generic=remote successive_new=eligible stale_jobs=refused facts=retained");return true;
}
