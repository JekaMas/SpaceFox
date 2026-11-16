import Toybox.Graphics;
import Toybox.Test;
(:test,:typecheck(false)) function peer024WorldAndDownloadedOwnership(logger){
 var scene=new SceneContext({"id"=>"ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b","rocket"=>"Starship V3","site"=>"Starbase","point"=>[-97.15799f,-80.0f],"precision"=>"minute","target"=>1794609900l});
 var settings=new SceneSettings(null);var r=new SceneRenderer(null);r.prepare(scene,settings);Test.assert(r.worldFallback&&r.map==null&&r.mapResource==null);var loads=r.resourceLoads;r.prepare(scene,settings);Test.assert(r.worldFallback&&r.map==null&&r.mapResource==null&&r.resourceLoads==loads);r.useDownloaded(null);Test.assert(r.worldFallback&&r.map==null&&r.mapResource==null);
 var bitmap=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();var rich=new NativeSfrRenderer();rich.mapBitmap=bitmap;rich.scene={"position"=>scene.point};r.useDownloaded(rich);Test.assert(r.map==null);r.useDownloaded(null);Test.assert(r.worldFallback&&r.map==null&&r.mapResource==null);r.prepareAod();Test.assert(r.aodWorldPoint(false,false)!=null);logger.debug("PEER024 unmatchedFallback retainedThroughReuse and downloaded transitions");return true;
}
