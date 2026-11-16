import Toybox.Application;
import Toybox.Lang;

(:background, :typecheck(false))
class NativeStore {
    var reads=0;var writes=0;var dataWrites=0;
    function initialize(){}
    function read(key){reads+=1;return Application.Storage.getValue(key);}
    function write(key,value){writes+=1;if(key.find("sf.feed.")==0){dataWrites+=1;}Application.Storage.setValue(key,value);}
    function remove(key){writes+=1;Application.Storage.deleteValue(key);}
}

(:extendedCode, :typecheck(false))
class NativeCache {
    var store;var base;var packet=null;var failure="";
    function initialize(url,adapter){var transfer=new NativeTransfer(url,adapter);base=transfer.base;store=transfer.store;}
}
