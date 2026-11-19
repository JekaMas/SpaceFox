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
    const EMPTY=0;const VOLATILE=1;const DURABLE=2;
    var store;var base;var packet=null;var failure="";var ramState=0;var pendingVolatile=null;
    function initialize(url,adapter){var transfer=new NativeTransfer(url,adapter);base=transfer.base;store=transfer.store;}
    function comparePublisher(a,b,allowEqual){return nativePublisherNewer(a,b,allowEqual);}
    function newerPublisher(a,allowEqual){return packet==null||comparePublisher(a,packet.document["publisher"],allowEqual);}
    function queueVolatile(value){
        var publisher=value[1];if(!newerPublisher(publisher,false)){return false;}
        if(pendingVolatile!=null&&!comparePublisher(publisher,pendingVolatile[1],false)){return false;}
        pendingVolatile=value;return true;
    }
    // Bootstrap can admit a newer durable publisher while this delivery waits hidden.
    // Recheck before the foreground admission boundary can cancel current art.
    function takeVolatile(){var value=pendingVolatile;pendingVolatile=null;return value!=null&&newerPublisher(value[1],false)?value:null;}
    function newer(candidate,allowEqual){return newerPublisher(candidate.document["publisher"],allowEqual);}
    function acceptVolatile(candidate){if(!newer(candidate,false)){return false;}packet=candidate;ramState=VOLATILE;return true;}
    function acceptDurable(candidate){if(packet!=null&&!newer(candidate,true)){return false;}packet=candidate;ramState=DURABLE;return true;}

}
