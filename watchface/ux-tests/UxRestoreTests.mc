import Toybox.Lang;
import Toybox.Test;
(:test,:typecheck(false)) function uxAcceptedSceneDuringRestore(logger){
 var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
 var accepted=new SceneContext({"id"=>"accepted-launch","rocket"=>"Vulcan VC6L","operator"=>"ULA","purpose"=>"Communications","site"=>"US · Cape Canaveral SFS","target"=>1794800000l,"precision"=>"minute"});
 view.setContext(accepted);view.clearForRestore();
 Test.assert(view.context!=null);
 Test.assert(view.context.launchId.equals("accepted-launch"));
 Test.assert(view.context.rocket.equals("Vulcan VC6L"));
 Test.assert(view.snapshot().remaining!=null);
 logger.debug("UX_RESTORE acceptedMetadata=true schedule=true errorDoesNotReplace=true");return true;
}

(:test,:typecheck(false)) function uxNewIdentityAfterRestore(logger){
 var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
 var old=new SceneContext({"id"=>"accepted-launch","rocket"=>"Vulcan VC6L","target"=>1794800000l,"precision"=>"minute"});
 view.setContext(old);view.downloaded=new NativeSfrRenderer();view.clearForRestore();
 Test.assert(view.context!=null&&view.context.launchId.equals("accepted-launch"));
 var next=new SceneContext({"id"=>"new-launch","rocket"=>"New vehicle","site"=>"New site","target"=>1794900000l,"precision"=>"minute"});
 next.modelId="unmapped-new-model";view.setContext(next);view.prepareRenderer();
 Test.assert(view.context.launchId.equals("new-launch"));Test.assert(view.context.rocket.equals("New vehicle"));
 Test.assert(view.context.site.equals("New site"));Test.assert(view.downloaded==null);
 Test.assert(view.renderer.model==NativeAssets.models["generic"]);Test.assert(!view.renderer.pin);
 logger.debug("UX_IDENTITY afterRejectedRestore=newLaunch generic=true oldBitmap=false oldPoint=false");return true;
}
