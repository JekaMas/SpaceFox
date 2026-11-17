import Toybox.Lang;

// Optional asset work is a single cancellable job for the selected scene. It is
// independent of the two display modes and never selects a different layout.
class SceneJob {
    const QUEUED = 0;
    const BUILDING = 1;
    const FAILED = 2;
    var token as Number;
    var state as Number = QUEUED;
    var batchSerial as Number or Long;
    function initialize(generation as Number, serial as Number or Long) {token=generation;batchSerial=serial;}
}
class SceneLifecycle {
    // Facts remain usable in all states; only the optional art job changes.
    const FACTS=0;const ART_PENDING=1;const ART_READY=2;
    var presentationState as Number=FACTS;
    var generation as Number = 0;
    var job as SceneJob or Null = null;
    function replace() as Void {generation+=1;job=null;presentationState=FACTS;}
    function bindReady() as Void {job=null;presentationState=ART_READY;}
    function pending() as Boolean {return presentationState==ART_PENDING && job!=null;}
    function request(serial as Number or Long) as Boolean {
        if(job!=null){
            // An immutable job already queued/building is never replaced by a
            // duplicate publication. A failed read gets one attempt only when
            // a strictly newer completed batch is admitted; advancing the token
            // prevents an old callback from publishing into the retry.
            if(job.state!=job.FAILED || serial<=job.batchSerial){return false;}
        }
        // Every accepted job gets a fresh identity, including a job started
        // after a previous successful completion or a retained ready scene.
        // A late completion from that earlier job must not publish this one.
        generation+=1;
        job=new SceneJob(generation,serial);presentationState=ART_PENDING;return true;
    }
    function begin() as Number or Null {
        if(job==null || job.state!=job.QUEUED){return null;}
        job.state=job.BUILDING;return job.token;
    }
    function complete(token as Number) as Boolean {
        if(job==null || job.state!=job.BUILDING || token!=job.token || token!=generation){return false;}
        job=null;presentationState=ART_READY;return true;
    }
    function fail(token as Number) as Void {
        if(job!=null && job.state==job.BUILDING && token==job.token && token==generation){job.state=job.FAILED;presentationState=FACTS;}
    }
    function cancel() as Void {generation+=1;job=null;presentationState=FACTS;}
}

// One bounded map decision for every presentation path. The projection and
// resource index change only when the accepted launch identity/point changes;
// no bitmap or world geometry is retained by this owner.
(:extendedCode, :typecheck(false))
class MapPresentation {
    const NONE=0;const SIMPLIFIED=1;const FULL=2;
    var identity=null;var longitude=null;var latitude=null;
    var point=null;var mapIndex=0;var matched=false;var x=335;var y=165;var renderFailed=false;
    function bind(context) {
        var id=context==null?null:context.launchId;
        var p=context==null?null:context.point;
        var lon=p==null?null:p[0];var lat=p==null?null:p[1];
        if((identity==null?id==null:id!=null&&identity.equals(id))&&longitude==lon&&latitude==lat){return;}
        identity=id;longitude=lon;latitude=lat;point=p;mapIndex=0;matched=false;x=335;y=165;renderFailed=false;
        if(p==null){return;}
        var coordinates=NativeAssets.mapCoordinates();
        for(var i=0;i<coordinates.size()/8;i+=1){
            var a=coordinates.decodeNumber(Lang.NUMBER_FORMAT_FLOAT,{:offset=>i*8,:endianness=>Lang.ENDIAN_BIG});
            var b=coordinates.decodeNumber(Lang.NUMBER_FORMAT_FLOAT,{:offset=>i*8+4,:endianness=>Lang.ENDIAN_BIG});
            if(lon-a>=-0.25&&lon-a<=0.25&&lat-b>=-0.25&&lat-b<=0.25){mapIndex=i;matched=true;var xy=SceneAod.project(p,a,b);x=xy[0];y=xy[1];return;}
        }
        var extra=NativeAssets.aodCoordinates;
        for(var i=0;i<extra.size()/8;i+=1){
            var a=SceneAod.coordinate(extra,i*8);var b=SceneAod.coordinate(extra,i*8+4);
            if(lon-a>=-0.25&&lon-a<=0.25&&lat-b>=-0.25&&lat-b<=0.25){mapIndex=54+i;matched=true;var xy=SceneAod.project(p,a,b);x=xy[0];y=xy[1];return;}
        }
    }
    function mode(shown,artReady){if(!shown){return NONE;}return artReady&&!renderFailed&&point!=null?FULL:SIMPLIFIED;}
    function failure(){renderFailed=true;}
    function restored(){renderFailed=false;}
    function reason(shown,artReady){
        if(!shown){return "hidden";}if(identity==null){return "empty";}
        if(point==null){return "unqualified-point";}if(renderFailed){return "render-error";}
        return artReady?"art-ready":"art-unavailable";
    }
    function useDownloaded(shown,available){return mode(shown,available)==FULL;}
    function useBundled(shown,available){return shown&&available&&(point==null||matched);}
    function pointVisible(shown){return shown&&point!=null;}
    function worldPoint(shown){return pointVisible(shown)&&!matched?point:null;}
    function activeResource(){return mapIndex<54?NativeAssets.mapResource(mapIndex):NativeAssets.extraMapResource(mapIndex-54);}
    function lowResource(){return NativeAssets.aodResource(mapIndex);}
}
