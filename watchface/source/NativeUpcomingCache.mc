import Toybox.Lang;
// Preserve a bounded accepted future queue across a partial update. The source
// namespace and publisher identity are stored directly, without re-hashing it.
(:extendedCode,:typecheck(false))
class NativeUpcomingCache {
    var store;var base;var instance;var key;
    function initialize(adapter,url,owner){store=adapter;base=url;instance=owner;key="sf.queue:"+url;}
    function save(scenes){
        var rows=[];for(var i=0;i<scenes.size()&&rows.size()<3;i+=1){var scene=scenes[i];if(scene!=null&&scene.sourceValidated!=null){rows.add(scene.cacheRow());}}
        store.write(key,{"instance"=>instance,"rows"=>rows});
    }
    function load(){
        var value=store.read(key);if(!(value instanceof Dictionary)||!(value["instance"] instanceof String)||!value["instance"].equals(instance)||!(value["rows"] instanceof Array)||value["rows"].size()>3){return [];}
        var result=[];for(var i=0;i<value["rows"].size();i+=1){var row=value["rows"][i];if(!(row instanceof Dictionary)){return [];}var point=row["pointText"];row["point"]=point==null?null:[point[0].toFloat(),point[1].toFloat()];result.add(new SceneContext(row));}return result;
    }
}
