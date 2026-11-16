import Toybox.Lang;
import Toybox.Test;
import Toybox.WatchUi;

(:test, :typecheck(false)) class IncomingSequenceStore {
 var data={};
 function read(key){return data.hasKey(key)?data[key]:null;}
 function write(key,value){data[key]=value;}
 function remove(key){data.remove(key);}
}
(:test, :typecheck(false)) function dForegroundCorruptThenRepair(logger) {
 var store=new IncomingSequenceStore();var base="https://incoming-sequence.fixture.invalid";var now=1794551193l;
 var initial=WatchUi.loadResource(Rez.JsonData.DisplayInitial);var moved=WatchUi.loadResource(Rez.JsonData.DisplayMoved);var catalog=WatchUi.loadResource(Rez.JsonData.DisplayCatalog);
 store.write("sf.obj."+catalog["catalogDigest"],catalog["catalog"]);var cache=new NativeCache(base,store);Test.assert(cache.accept(initial["raw"],now));var old=store.read("sf.commit");var oldSeal=old["seal"];var oldId=cache.packet.launchId();
 var transfer=new NativeTransfer(base,store);Test.assert(transfer.stage("feed",moved["raw"],null));var marker=store.read("sf.incoming.feed");var part="sf.incoming.feed."+marker["parts"][0]+".0";var good=store.read(part);store.data[part]=good+"x";
 var incoming=new NativeIncoming(store,base);Test.assert(!incoming.admitFeed(cache,now));Test.assert(store.read("sf.commit")["seal"].equals(oldSeal)&&cache.packet!=null&&cache.packet.launchId().equals(oldId));
 var staged=transfer.stage("feed",moved["raw"],null);logger.debug("REPAIR staged="+staged);Test.assert(staged);var admitted=new NativeIncoming(store,base).admitFeed(cache,now);logger.debug("REPAIR admitted="+admitted+" failure="+cache.failure);Test.assert(admitted);Test.assert(cache.packet!=null&&store.read("sf.commit")["seal"]!=null);
 logger.debug("FOREGROUND_CORRUPTION rejected=true durablePriorRestored=true repairedIncomingAdmitted=true");return true;
}
