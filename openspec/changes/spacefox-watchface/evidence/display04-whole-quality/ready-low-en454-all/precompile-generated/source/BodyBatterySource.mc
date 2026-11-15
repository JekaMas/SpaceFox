import Toybox.Lang;
(:typecheck(false)) class BodyBatterySource { var value as Number or Null=null; var observed as Boolean=false; var subscribed as Boolean=false; function start(callback as Method) as Boolean {return false;} function read() as Number or Null {return null;} function stop() as Void {value=null;observed=false;subscribed=false;} }
