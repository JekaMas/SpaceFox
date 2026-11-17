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
    function comparePublisher(a,b,allowEqual){
        var at=a["selectionValidatedUtc"];var bt=b["selectionValidatedUtc"];
        if(!(at instanceof Number||at instanceof Long)||!(bt instanceof Number||bt instanceof Long)){return false;}
        if(at!=bt){return at>bt;}
        if(!(a["instance"] instanceof String)||!(b["instance"] instanceof String)||!a["instance"].equals(b["instance"])){return false;}
        return allowEqual?a["generation"]>=b["generation"]:a["generation"]>b["generation"];
    }
    function newerPublisher(a,allowEqual){return packet==null||comparePublisher(a,packet.document["publisher"],allowEqual);}
    function queueVolatile(value){
        var publisher=value[1];if(!newerPublisher(publisher,false)){return false;}
        if(pendingVolatile!=null&&!comparePublisher(publisher,pendingVolatile[1],false)){return false;}
        pendingVolatile=value;return true;
    }
    function takeVolatile(){var value=pendingVolatile;pendingVolatile=null;return value;}
    function newer(candidate,allowEqual){return newerPublisher(candidate.document["publisher"],allowEqual);}
    function acceptVolatile(candidate){if(!newer(candidate,false)){return false;}packet=candidate;ramState=VOLATILE;return true;}
    function acceptDurable(candidate){if(ramState==VOLATILE&&!newer(candidate,true)){return false;}packet=candidate;ramState=DURABLE;return true;}

}
