import Toybox.Lang;
import Toybox.Test;

(:test, :typecheck(false)) class SequenceStore {
    var data={};var failWrite=null;var failRemove=false;
    function read(key){return data.hasKey(key)?data[key]:null;}
    function write(key,value){if(key.equals(failWrite)){throw new Lang.InvalidValueException("injected write failure");}data[key]=value;}
    function remove(key){if(failRemove){throw new Lang.InvalidValueException("injected cleanup failure");}data.remove(key);}
}

(:test, :typecheck(false)) function dInterruptedFragmentRecovery(logger) {
    var store=new SequenceStore();var base="https://fragment-sequence.fixture.invalid";var transfer=new NativeTransfer(base,store);var incoming=new NativeIncoming(store,base);var old="";
    for(var i=0;i<1100;i+=1){old+="a";}store.write("sf.commit",{"seal"=>"accepted"});Test.assert(transfer.stage("feed",old,null));
    store.failWrite="sf.incoming.feed";var failed=false;try{transfer.stage("feed","short",null);}catch(e){failed=true;}
    Test.assert(failed&&incoming.read("feed",true)[1].equals(old)&&store.read("sf.commit")["seal"].equals("accepted"));
    store.failWrite=null;store.failRemove=true;Test.assert(transfer.stage("feed","short",null));Test.assert(incoming.read("feed",true)[1].equals("short"));
    var marker=store.read("sf.incoming.feed");var garbage=0;for(var i=0;i<16;i+=1){for(var bank=0;bank<2;bank+=1){if(!(i==0&&bank==marker["parts"][0])&&store.read("sf.incoming.feed."+bank+"."+i)!=null){garbage+=1;}}}Test.assert(garbage>0);
    store.failRemove=false;Test.assert(transfer.stage("feed","short",null));for(var i=0;i<16;i+=1){for(var bank=0;bank<2;bank+=1){if(!(i==0&&bank==marker["parts"][0])){Test.assert(store.read("sf.incoming.feed."+bank+"."+i)==null);}}}
    Test.assert(incoming.read("feed",true)[1].equals("short")&&store.read("sf.commit")["seal"].equals("accepted"));logger.debug("FRAGMENT_SEQUENCE failedMarkerPreservesOld=true failedCleanupPreservesNew=true retryReclaimsTail=true acceptedUnchanged=true");return true;
}

(:test, :typecheck(false)) function dInactiveFeedTailRecovery(logger) {
    var store=new SequenceStore();var cache=new NativeCache("https://tail-sequence.fixture.invalid",store);store.write("sf.commit",{"slot"=>0,"seal"=>"accepted"});store.write("sf.recovery",{"slot"=>1,"seal"=>"recovery"});
    store.write("sf.feed.0.4","active");store.write("sf.feed.1.4","recovery");store.write("sf.feed.2.4","orphan");store.write("future.fact",{"value"=>"kept"});
    cache.cleanupFeedTail(0,1);cache.cleanupFeedTail(1,1);Test.assert(store.read("sf.feed.0.4").equals("active")&&store.read("sf.feed.1.4").equals("recovery"));
    store.failRemove=true;cache.cleanupFeedTail(2,1);Test.assert(store.read("sf.feed.2.4").equals("orphan"));store.failRemove=false;cache.cleanupFeedTail(2,1);
    Test.assert(store.read("sf.feed.2.4")==null&&store.read("sf.feed.0.4").equals("active")&&store.read("sf.feed.1.4").equals("recovery")&&store.read("future.fact")["value"].equals("kept")&&store.read("sf.commit")["seal"].equals("accepted"));
    logger.debug("FEED_TAIL_SEQUENCE activeRecoveryProtected=true interruptedCleanupRetry=true acceptedFutureUnchanged=true");return true;
}
