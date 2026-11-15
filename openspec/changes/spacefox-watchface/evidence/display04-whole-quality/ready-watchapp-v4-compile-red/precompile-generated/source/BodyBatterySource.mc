import Toybox.Lang;
(:typecheck(false)) class BodyBatterySource { var value=null; var observed=false; var subscribed=false; function start(callback){return false;} function read(){return null;} function stop(){value=null;observed=false;subscribed=false;} }
