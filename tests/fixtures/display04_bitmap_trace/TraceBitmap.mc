import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Test;
import Toybox.WatchUi;

(:test,:typecheck(false)) class D04BitmapStore {
 var data={};function read(k){return data.hasKey(k)?data[k]:null;}function write(k,v){data[k]=v;}function remove(k){data.remove(k);}
}
(:test,:typecheck(false)) class D04BitmapDrawing extends SceneRenderer {
 var ids;var refs;
 function initialize(){ids=[];refs=[];SceneRenderer.initialize(null);}
 function load(id){var value=SceneRenderer.load(id);ids.add(id);refs.add(value);return value;}
 function identity(value){for(var i=0;i<refs.size();i+=1){if(refs[i]==value){return ids[i];}}return null;}
}
(:test,:typecheck(false)) function display04PendingBitmapTrace(logger){
 var store=new D04BitmapStore();var catalog=WatchUi.loadResource(Rez.JsonData.D04Catalog);store.write("sf.obj."+catalog["catalogDigest"],catalog["catalog"]);
 var cache=new NativeCache("https://fixture.invalid/display04-point",store);var raw=WatchUi.loadResource(Rez.JsonData.D04Feed)["raw"];
 Test.assert(cache.accept(raw,1794551202));var context=feedScene(cache.packet,1794551202);Test.assert(context!=null&&context.point!=null);
 var previous=null;
 for(var language=0;language<2;language+=1){
  var settings=new SceneSettings({"Language"=>language});var draw=new D04BitmapDrawing();draw.prepare(context,settings);
  Test.assert(draw.map!=null&&draw.art!=null&&draw.pin&&draw.downloaded==null&&!context.stale);
  var idMap=draw.identity(draw.map);var idArt=draw.identity(draw.art);var idPoint=draw.identity(draw.marker);
  Test.assert(idMap!=null&&idArt!=null&&idPoint==Rez.Drawables.LaunchMarker);
  var actual=[idMap,idArt,idPoint,draw.map.getWidth(),draw.map.getHeight(),draw.art.getWidth(),draw.art.getHeight(),draw.marker.getWidth(),draw.marker.getHeight(),draw.pinX,draw.pinY,draw.mapScale[:filterMode]];
  logger.debug("D04_BITMAP|"+language+"|map="+idMap+","+draw.map.getWidth()+"x"+draw.map.getHeight()+"|art="+idArt+","+draw.art.getWidth()+"x"+draw.art.getHeight()+"|marker="+idPoint+","+draw.marker.getWidth()+"x"+draw.marker.getHeight()+"|pin="+draw.pinX+","+draw.pinY+"|filter="+draw.mapScale[:filterMode]+"|phase=0|downloaded=false|stale=false");
  if(previous!=null){for(var i=0;i<actual.size();i+=1){Test.assert(actual[i]==previous[i]);}}
  previous=actual;
 }
 return true;
}
