import Toybox.Application;
import Toybox.System;
import Toybox.Lang;
(:background,:typecheck(false)) class MetricsIpcStore extends NativeStore {
 function initialize(){NativeStore.initialize();}
 function write(key,value){if(key.find("sf.snapshot.")==0){throw new Lang.InvalidValueException("injected snapshot storage failure");}NativeStore.write(key,value);}
}
(:background,:typecheck(false)) class MetricsIpcService extends FeedService {
 function initialize(){FeedService.initialize();}
 function createTransfer(){return new NativeTransfer(configuredFeedUrl(),new MetricsIpcStore());}
}
(:background,:typecheck(false)) class MetricsIpcProbe extends SpaceFoxApp {
 function initialize(){SpaceFoxApp.initialize();}
 function getServiceDelegate(){return [new MetricsIpcService()];}
 function onBackgroundData(data){SpaceFoxApp.onBackgroundData(data);if(view!=null&&view.context!=null){System.println("SF_IPC accepted="+view.context.launchId+" point="+view.context.point+" target="+view.context.displayTarget);}else{System.println("SF_IPC no_visible_facts");}}
}
(:background,:typecheck(false)) class MetricsIpcProbeRu extends MetricsIpcProbe {
 function initialize(){MetricsIpcProbe.initialize();}
 function initialSettings(){return new SceneSettings({"Language"=>"ru"});}
}
