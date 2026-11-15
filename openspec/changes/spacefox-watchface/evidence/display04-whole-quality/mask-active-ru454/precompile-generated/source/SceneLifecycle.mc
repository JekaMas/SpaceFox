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
    var generation as Number = 0;
    var job as SceneJob or Null = null;
    function replace() as Void {generation+=1;job=null;}
    function bindReady() as Void {job=null;}
    function pending() as Boolean {return job!=null && job.state!=job.FAILED;}
    function request(serial as Number or Long) as Boolean {
        if(job!=null){
            // An immutable job already queued/building is never replaced by a
            // duplicate publication. A failed read gets one attempt only when
            // a strictly newer completed batch is admitted; advancing the token
            // prevents an old callback from publishing into the retry.
            if(job.state!=job.FAILED || serial<=job.batchSerial){return false;}
            generation+=1;
        }
        job=new SceneJob(generation,serial);return true;
    }
    function begin() as Number or Null {
        if(job==null || job.state!=job.QUEUED){return null;}
        job.state=job.BUILDING;return job.token;
    }
    function complete(token as Number) as Boolean {
        if(job==null || job.state!=job.BUILDING || token!=job.token || token!=generation){return false;}
        job=null;return true;
    }
    function fail(token as Number) as Void {
        if(job!=null && job.state==job.BUILDING && token==job.token && token==generation){job.state=job.FAILED;}
    }
    function cancel() as Void {generation+=1;job=null;}
}
