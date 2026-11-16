import Toybox.Lang;

(:extendedCode, :typecheck(false))
function nativeSame(a,b){
    if(a==null||b==null){return a==null&&b==null;}
    if(a instanceof String){return b instanceof String&&a.equals(b);}
    if(a instanceof Number||a instanceof Long){return (b instanceof Number||b instanceof Long)&&a==b;}
    if(a instanceof Boolean){return b instanceof Boolean&&a==b;}
    if(a instanceof Array){if(!(b instanceof Array)||a.size()!=b.size()){return false;}for(var i=0;i<a.size();i+=1){if(!nativeSame(a[i],b[i])){return false;}}return true;}
    if(a instanceof Dictionary){if(!(b instanceof Dictionary)||a.size()!=b.size()){return false;}var keys=a.keys();for(var j=0;j<keys.size();j+=1){if(!b.hasKey(keys[j])||!nativeSame(a[keys[j]],b[keys[j]])){return false;}}return true;}return false;
}

(:extendedCode, :typecheck(false))
class NativeFeedHashJob {
    var text;var spans;var wire;var cursor=0;var limit;var spanIndex=0;var result=null;var byteCount=0;
    function initialize(value,ignored){text=value;spans=ignored;limit=value.length();wire=new NativeWireHash();}
    function setRange(start,end){cursor=start;limit=end;}
    function step(){
        var work=0;
        while(work<4){work+=1;var target=spanIndex<spans.size()?spans[spanIndex][0]:limit;
            if(cursor<target){var end=cursor+128;if(end>target){end=target;}wire.put(text.substring(cursor,end));cursor=end;continue;}
            if(spanIndex<spans.size()){wire.put(spans[spanIndex].size()>2?spans[spanIndex][2]:"null");cursor=spans[spanIndex][1];spanIndex+=1;continue;}
            result=wire.digest();byteCount=wire.count;text=null;wire=null;return true;
        }return false;
    }
}
