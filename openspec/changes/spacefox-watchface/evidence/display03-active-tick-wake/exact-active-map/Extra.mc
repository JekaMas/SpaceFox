import Toybox.Graphics;import Toybox.Lang;import Toybox.System;import Toybox.Test;import Toybox.WatchUi;
(:test,:typecheck(false)) class ExtraRecorder extends SceneRenderer {
 var chosen=null;function initialize(){SceneRenderer.initialize(null);}
 function load(id){if(id==Rez.Drawables.MapExtra0||id==Rez.Drawables.MapExtra17){chosen=id;}return SceneRenderer.load(id);}
}
(:test,:typecheck(false)) function exactExtraIdentity(logger){
 var r=new ExtraRecorder();var settings=new SceneSettings(null);
 var ctx=new SceneContext({"id"=>"extra104","point"=>[144.797222,13.483889]});r.prepare(ctx,settings);
 Test.assert(r.pin&&r.aodPin&&r.pinX==r.aodPinX&&r.pinY==r.aodPinY&&r.chosen==Rez.Drawables.MapExtra0&&r.aodResource==Rez.Drawables.AodExtra0);logger.debug("EXTRA first active="+r.pinX+","+r.pinY+" low="+r.aodPinX+","+r.aodPinY);
 ctx=new SceneContext({"id"=>"extra59","point"=>[167.733333,8.716667]});r.prepare(ctx,settings);
 Test.assert(r.pin&&r.aodPin&&r.pinX==r.aodPinX&&r.pinY==r.aodPinY&&r.chosen==Rez.Drawables.MapExtra17&&r.aodResource==Rez.Drawables.AodExtra17);logger.debug("EXTRA last active="+r.pinX+","+r.pinY+" low="+r.aodPinX+","+r.aodPinY);return true;
}
