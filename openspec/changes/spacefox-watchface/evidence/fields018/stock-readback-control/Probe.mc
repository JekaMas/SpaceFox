import Toybox.Application;
import Toybox.Complications;
import Toybox.Lang;
import Toybox.Test;
import Toybox.Time;
(:background) class SfrRuntimeApp extends SpaceFoxApp {function initialize(){SpaceFoxApp.initialize();}}
(:test,:typecheck(false)) function fields018SeedReadback(logger) {
 var store=new NativeStore();var base="https://rollover017.fixture.invalid";
 var incoming=new NativeIncoming(store,base);var row=incoming.read("feed",true);Test.assert(row!=null);
 var feed=new NativeBridgeFeed(row[1],Time.now().value().toLong(),store);var source=new NativeRenderSource(store,base,feed.bridge);
 Test.assert(source.ready&&source.selectionHash.equals("77d4b3173b019ee84b7eb751e81ccb7a47edfba560a54166bfb47f441e8b7b37"));
 var up=feed.document["upcoming"];Test.assert(up instanceof Array&&up.size()==2);
 Test.assert(up[0]["launch_id"].equals("ll2:launch:76617033-4dc0-4448-b50c-e5b0d5a18539")&&up[1]["launch_id"].equals("ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b"));
 var ids=[4,5,6,8];for(var i=1;i<=4;i+=1){var id=FieldCatalog.saved(i);Test.assert(id instanceof Complications.Id&&id.getType()==ids[i-1]&&Application.Properties.getValue("Field"+i)==6);}
 logger.debug("RELOAD incomingValidated=true ready=true selection=77d4b317 upcoming=2 fieldTypes=4,5,6,8");return true;
}
