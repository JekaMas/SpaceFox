import Toybox.Lang;

(:extendedCode, :typecheck(false))
class NativeFeed {
    var bridge=null;var presentation=null;var upcomingScenes=null;var terminalUpdates=[];var document;var validation;var stale=false;var rescheduled=false;
    function fail(){throw new Lang.InvalidValueException("Invalid visual descriptor");}
    function shape(value,required,optional){if(!(value instanceof Dictionary)){fail();}var keys=value.keys();for(var i=0;i<required.size();i+=1){if(!value.hasKey(required[i])){fail();}}for(var j=0;j<keys.size();j+=1){if(required.indexOf(keys[j])<0 && optional.indexOf(keys[j])<0){fail();}}}
    function integer(value){return value instanceof Number || value instanceof Long;}
    function same(value,expected){return value instanceof String && value.equals(expected);}
    function hex(value){return nativeHex(value);}
    function id(value,kind,optional){
        if(value==null){return optional;}if(!(value instanceof String)){return false;}var a=value.find(":");if(a==null||a==0){return false;}var rest=value.substring(a+1,value.length());var b=rest.find(":");return b!=null && rest.substring(0,b).equals(kind) && b<rest.length()-1&&nativeNormalizedEdges(value.substring(0,a))&&nativeNormalizedEdges(rest.substring(b+1,rest.length()));
    }
    function advance(now){}
    function refreshTarget(){return null;}
    function compact(){}
}
