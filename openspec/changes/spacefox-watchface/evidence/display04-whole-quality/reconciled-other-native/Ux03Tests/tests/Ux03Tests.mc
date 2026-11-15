import Toybox.Test;
import Toybox.Graphics;
(:test,:typecheck(false)) function ux03MatchingFallback(logger){
 var r=new SceneRenderer(null);var s=new SceneSettings(null);
 var cape=new SceneContext({"id"=>"ll2:launch:known","point"=>[-80.58303644,28.58341025]});
 r.prepare(cape,s);Test.assert(r.pin&&r.pinX==335&&r.pinY==165);
 // Exact prepared Māhia center from the maintained site fixture.
 var nz=new SceneContext({"id"=>"ll2:launch:known","point"=>[177.864469,-39.262833]});
 r.prepare(nz,s);Test.assert(r.pin&&r.pinX==335&&r.pinY==165);
 // An unmatched bundled view does not reject this coordinate as source data;
 // it simply must not label a different prepared map with its pin.
 var former=new SceneContext({"id"=>"ll2:launch:known","point"=>[166.463,-39.261]});r.prepare(former,s);Test.assert(former.point!=null&&!r.pin);
 var unknown=new SceneContext({"id"=>"ll2:launch:known","point"=>null});r.prepare(unknown,s);Test.assert(!r.pin);
 var unmatched=new SceneContext({"id"=>"ll2:launch:known","point"=>[-80.0,28.0]});r.prepare(unmatched,s);Test.assert(!r.pin);
 var mobile=new SceneContext({"id"=>"ll2:launch:known","moving"=>true,"point"=>[-80.58303644,28.58341025]});r.prepare(mobile,s);Test.assert(!r.pin);
 logger.debug("matching fixed Cape and NZ point; unmatched, absent and moving omit point");return true;
}
