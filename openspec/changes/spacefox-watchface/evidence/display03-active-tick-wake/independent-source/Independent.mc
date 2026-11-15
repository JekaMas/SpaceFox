import Toybox.Graphics;
import Toybox.System;
import Toybox.Test;
(:test,:typecheck(false)) function independentWakeAndIdentity(logger) {
 var c=new Display03Clock();var v=new SpaceFoxView(c,new ScheduleState(1794762690,"exact"));var d=new Display03ModeRenderer();v.renderer=d;
 var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();v.onEnterSleep();v.updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);v.onExitSleep();v.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);v.updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);
 Test.assert(d.lowCalls==2&&d.activeCalls==1);logger.debug("PEER same_minute_low_high_low low=2 active=1");
 var a=new NativeRenderSource(null,"https://one.invalid",null);a.ready=true;a.serial=1;a.transferHash="t";a.selectionHash="s";v.setAssetCache(a);Test.assert(v.sceneLifecycle.request(1));
 var b=new NativeRenderSource(null,"https://one.invalid",null);b.ready=true;b.serial=2;b.transferHash="t";b.selectionHash="s";var gen=v.sceneLifecycle.generation;v.setAssetCache(b);Test.assert(v.sceneLifecycle.pending()&&v.sceneLifecycle.generation==gen);
 var e=new NativeRenderSource(null,"https://one.invalid",null);e.ready=true;e.serial=3;e.transferHash="t";e.selectionHash="different";v.setAssetCache(e);Test.assert(!v.sceneLifecycle.pending());
 Test.assert(v.sceneLifecycle.request(3));var f=new NativeRenderSource(null,"https://two.invalid",null);f.ready=true;f.serial=4;f.transferHash="t";f.selectionHash="different";v.setAssetCache(f);Test.assert(!v.sceneLifecycle.pending());logger.debug("PEER same_identity_preserved selection_and_namespace_changes_cancelled");return true;
}
