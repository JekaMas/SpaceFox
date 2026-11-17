import Toybox.Lang;
import Toybox.Test;
(:test,:typecheck(false)) class RequestFirstRed extends FeedService {
 function initialize(){FeedService.initialize();}
 function sendRequest(path,callback) {}
 function rearm() as Void {}
 function leave() as Void {}
 function done(code,data) {}
}
(:test,:typecheck(false)) function requestDuplicateRejected(logger) {
 var service=new RequestFirstRed();service.startDeadline();service.request("test",service.method(:done));
 Test.assertMessage(service.callbackAllowed(),"first response must be admitted");
 Test.assertMessage(!service.callbackAllowed(),"duplicate response must not be admitted");
 return true;
}
