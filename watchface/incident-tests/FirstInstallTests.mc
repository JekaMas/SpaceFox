import Toybox.Lang;
import Toybox.Test;

(:typecheck(false)) class FirstInstallStore {
    var data={};
    function read(key){return data.hasKey(key)?data[key]:null;}
    function write(key,value){data[key]=value;}
    function remove(key){data.remove(key);}
}

(:test, :typecheck(false)) function firstInstallDefaultsAndRetry(logger){
    Test.assert(feedUrlValue(null).equals("https://jekamas.github.io/SpaceFox"));
    Test.assert(feedUrlValue("").equals(""));
    Test.assert(feedUrlValue("https://example.org/space").equals("https://example.org/space"));
    var store=new FirstInstallStore();
    var transfer=new NativeTransfer("https://jekamas.github.io/SpaceFox",store);
    Test.assert(transfer.due(1000l));transfer.attempted(1000l);
    Test.assert(!transfer.due(1299l));Test.assert(transfer.due(1300l));
    Test.assert(transfer.nextWake(1200l)==1300l);
    store.write("sf.transfer.ready",{"base"=>transfer.base,"accepted"=>true});
    Test.assert(!transfer.due(1300l));Test.assert(transfer.nextWake(1300l)==4600l);
    var disabled=new NativeTransfer("",store);Test.assert(!disabled.due(1300l));
    logger.debug("FIRST_INSTALL default=true blankDisabled=true coldRetry=300 acceptedRetry=3600");return true;
}
