import Toybox.Graphics;
import Toybox.Lang;
import Toybox.StringUtil;
import Toybox.Cryptography;
import Toybox.System;

// One bounded chunk and one previous scanline. No complete pixel array, geometry
// AST, network, storage or decoder work is owned by redraw.
// Hot pixel loops remain resident; only cold construction/chunk admission is
// paged. NativeCacheCore paging funds this within the same foreground cap.
(:typecheck(false))
class NativeSfrDecoder {
    var immutable;var descriptor;var bitmap;var dc;var hash;var row=[]b;var colors=[];var width;var height;var channels;var rgbRowBitmap=null;var rgbRowDc=null;var y=0;var shard=0;var data=null;var offset=0;var endRow=0;var done=false;
    (:extendedCode)
    function initialize(adapter,d){
        immutable=new NativeImmutable(adapter);descriptor=d;width=d["canvas"][0];height=d["canvas"][1];channels=d["channels"];hash=new Cryptography.Hash({:algorithm=>Cryptography.HASH_SHA256});
        bitmap=Graphics.createBufferedBitmap({:width=>width,:height=>height,:alphaBlending=>Graphics.ALPHA_BLENDING_FULL}).get();dc=bitmap.getDc();dc.setColor(Graphics.COLOR_TRANSPARENT,Graphics.COLOR_TRANSPARENT);dc.clear();if(channels==3){rgbRowBitmap=Graphics.createBufferedBitmap({:width=>width,:height=>1,:alphaBlending=>Graphics.ALPHA_BLENDING_FULL}).get();rgbRowDc=rgbRowBitmap.getDc();}
    }
    (:extendedCode)
    function fail(){throw new Lang.InvalidValueException("Invalid SFR1 raster");}
    (:extendedCode)
    function chunk(){
        row=[]b;colors=[];
        if(shard>=descriptor["shards"].size()){fail();}
        var item=descriptor["shards"][shard];
        if(!(item instanceof Array)||item.size()!=2||!(item[0] instanceof String)||!(item[1] instanceof Number||item[1] instanceof Long)){fail();}
        var raw=immutable.raw({"sha256"=>item[0],"decodedBytes"=>item[1]});
        if(!(raw instanceof String)||raw.length()<8||!raw.substring(0,5).equals("SFR1:")){fail();}
        NativeMetrics.sample("sfr-chunk-raw");
        // Inspect only the bounded ASCII header. Copying two almost-complete
        // tails retains three4KiB strings and can exhaust the ordinary heap.
        var tail=raw.substring(5,raw.length()<16?raw.length():16);
        var a=tail.find(":");if(a==null){fail();}
        var start=tail.substring(0,a);
        var rest=tail.substring(a+1,tail.length());
        var b=rest.find(":");if(b==null){fail();}
        var count=rest.substring(0,b);
        var encoded=raw.substring(5+a+b+2,raw.length());
        raw=null;tail=null;rest=null;
        if(!start.equals(y.toString())||count.length()<1||count.length()>3||count.substring(0,1).equals("0")){fail();}
        for(var i=0;i<count.length();i+=1){if("0123456789".find(count.substring(i,i+1))==null){fail();}}
        var rows=count.toNumber();if(rows==null||rows<1||y+rows>height){fail();}
        if(encoded.length()==0||encoded.length()%4!=0){fail();}var padding=encoded.find("=");if(padding!=null){if(padding<encoded.length()-2){fail();}for(var pad=padding;pad<encoded.length();pad+=1){if(!encoded.substring(pad,pad+1).equals("=")){fail();}}}
        // Decode once, then validate canonical128-character slices. Growing
        // a3072B ByteArray from32 tiny blocks transiently retained old/new
        // capacities alongside the4KiB input in the ordinary heap.
        data=StringUtil.convertEncodedString(encoded,{:fromRepresentation=>StringUtil.REPRESENTATION_STRING_BASE64,:toRepresentation=>StringUtil.REPRESENTATION_BYTE_ARRAY});if(data.size()>3072){fail();}
        for(var begin=0;begin<encoded.length();begin+=128){var end=begin+128;if(end>encoded.length()){end=encoded.length();}var last=(begin/4*3+96);if(last>data.size()){last=data.size();}var bytes=data.slice(begin/4*3,last);var canonical=StringUtil.convertEncodedString(bytes,{:fromRepresentation=>StringUtil.REPRESENTATION_BYTE_ARRAY,:toRepresentation=>StringUtil.REPRESENTATION_STRING_BASE64});if(!canonical.equals(encoded.substring(begin,end))){fail();}}
        encoded=null;offset=0;endRow=y+rows;for(var j=0;j<width*channels;j+=1){row.add(0);}if(channels==3){rgbRowDc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);rgbRowDc.clear();}else{for(var pixel=0;pixel<width;pixel+=1){colors.add(Graphics.COLOR_TRANSPARENT);}}shard+=1;
    }
    function color(at){var alpha=channels==3?255:data[at+3];return alpha==255?data[at]*65536+data[at+1]*256+data[at+2]:alpha==0?Graphics.COLOR_TRANSPARENT:Graphics.createColor(alpha,data[at],data[at+1],data[at+2]);}
    function span(x,length,value){if(value!=Graphics.COLOR_TRANSPARENT){if(channels==3){rgbRowDc.setColor(value,Graphics.COLOR_TRANSPARENT);rgbRowDc.fillRectangle(x,0,length,1);}else{dc.setColor(value,Graphics.COLOR_TRANSPARENT);dc.fillRectangle(x,y,length,1);}}}
    function paintCopy(x,length){
        var first=x;var current=colors[x];for(var n=1;n<length;n+=1){var next=colors[x+n];if(next!=current){span(first,x+n-first,current);first=x+n;current=next;}}span(first,x+length-first,current);
    }
    function oneRow(){
        if(data==null){chunk();}var x=0;
        while(x<width){if(offset>=data.size()){fail();}var token=data[offset];offset+=1;var count=(token&127)+1;if(x+count>width){fail();}if(token<128){if(offset+channels>data.size()){fail();}var value=color(offset);if(channels==3){for(var n=0;n<count;n+=1){var at=(x+n)*3;row[at]=data[offset];row[at+1]=data[offset+1];row[at+2]=data[offset+2];}}else{for(var n=0;n<count;n+=1){colors[x+n]=value;for(var c=0;c<channels;c+=1){row[(x+n)*channels+c]=data[offset+c];}}}offset+=channels;span(x,count,value);}else if(channels==4){paintCopy(x,count);}x+=count;}
        if(channels==3){dc.drawBitmap(0,y,rgbRowBitmap);}hash.update(row);y+=1;if(y==endRow){if(offset!=data.size()){fail();}data=null;row=[]b;colors=[];}if(y==height){if(shard!=descriptor["shards"].size()||data!=null){fail();}var digest=StringUtil.convertEncodedString(hash.digest(),{:fromRepresentation=>StringUtil.REPRESENTATION_BYTE_ARRAY,:toRepresentation=>StringUtil.REPRESENTATION_STRING_HEX}).toLower();if(!digest.equals(descriptor["pixelSha256"])){fail();}done=true;row=[]b;colors=[];descriptor=null;dc=null;hash=null;rgbRowDc=null;rgbRowBitmap=null;}
    }
    function step(){if(data==null&&!done){chunk();NativeMetrics.sample("sfr-chunk-ready");return false;}var start=System.getTimer();var rows=0;while(!done&&rows<16&&(rows==0||System.getTimer()-start<18)){oneRow();rows+=1;if(data==null){break;}}NativeMetrics.sample("sfr-decode-step");return done;}
}

(:typecheck(false))
class NativeSfrRenderer extends NativeVisualRenderer {
    var siteCountryBitmap=null;var mapBitmap=null;var scene=null;var selectionHash="";
    function initialize(){NativeVisualRenderer.initialize();}
    function drawBackground(dc,settings,marker){if(mapBitmap!=null){dc.drawBitmap(0,0,mapBitmap);if(scene["position"]!=null){dc.drawBitmap(321,151,marker);}}}

}

(:extendedCode, :typecheck(false))
class NativeSfrBuild {
    var store;var base;var packet;var immutable;var scene;var descriptors={};var expected=[];var role=0;var decoder=null;var result;var complete=false;var closureChecked=false;var closureAt=0;var selection;var rasterBytes=0;var rasterObjects=0;var readKind=0;var names;
    function initialize(adapter,url,p){NativeMetrics.sample("sfr-build-start");store=adapter;base=url;packet=p;immutable=new NativeImmutable(store);selection=p.bridge["selection"];names=["map","rocket","siteCountry"];result=new NativeSfrRenderer();NativeMetrics.sample("sfr-build-reader");begin();}
    function fail(){throw new Lang.InvalidValueException("Invalid native SFR1M scene");}
    function same(a,b){return nativeSame(a,b);}
    function ref(r,prefix){packet.ref(r,prefix);return r;}
    function read(r){var raw=immutable.raw(r);if(raw==null){fail();}var parser=new NativeJson();parser.feedMode=true;parser.nodeOwner=self;return parser.parse(raw,4096);}
    function add(r){addTuple(0,r["sha256"],r["decodedBytes"]);}
    function addTuple(kind,digest,bytes){for(var i=0;i<expected.size();i+=1){if(expected[i][1].equals(digest)){if(expected[i][0]!=kind||expected[i][2]!=bytes){fail();}return false;}}expected.add([kind,digest,bytes]);return true;}
    function objectField(path,key,value){
        if(path.equals("/mapSource")){if(key.equals("corresponding")||key.equals("notices")){sourceRef(value);}else if(key.equals("recipeSha256")||key.equals("worldSha256")){if(!packet.hex(value)){fail();}}else{fail();}return null;}
        if(path.find("/roles/")==0&&key.equals("descriptor")){ref(value,"descriptors");return [value["sha256"],value["decodedBytes"]];}
        if((path.equals("/origins/model")||path.equals("/origins/operator"))&&key.equals("sourceRecord")){if(value!=null){sourceRef(value);}return value==null?null:true;}
        if(path.equals("")&&key.equals("siteCountrySource")){sourceRef(value);return true;}
        if(path.equals("")&&key.equals("motionSource")){sourceRef(value);return true;}
        if(path.equals("")&&key.equals("sourceDescriptor")){ref(value,"descriptors");return null;}
        if(path.equals("")&&key.equals("scene")&&value!=null){ref(value,"descriptors");return [value["sha256"],value["decodedBytes"]];}
        return value;
    }
    function arrayElement(path,index,value,depth){
        if(readKind==0&&!path.equals("/marker/anchor")&&!path.equals("/marker/colors")){fail();}
        if(readKind==1&&!path.equals("/canvas")&&!path.equals("/sourceCanvas")&&!path.equals("/animation")&&!path.equals("/shards")){fail();}
        if(readKind==2&&!path.equals("/objects")){fail();}
        if(path.equals("/shards")&&depth==1){if(index>=32){fail();}ref(value,"rasters");return [value["sha256"],value["decodedBytes"]];}
        if(path.equals("/shards")&&depth>1){fail();}
        if(path.equals("/objects")&&depth==1){if(index>=40||!(value instanceof Array)||value.size()!=3||!packet.integer(value[0])||(value[0]!=0&&value[0]!=1)||!packet.hex(value[1])||!packet.integer(value[2])||value[2]<1||value[2]>4096){fail();}}
        if(path.equals("/objects")&&(depth>2||depth==2&&index>=3)){fail();}
        if(path.equals("/animation")&&(depth>3||depth==1&&index>=2||depth==2&&index>=16||depth==3&&index>=4)){fail();}
        if(((path.equals("/canvas")||path.equals("/sourceCanvas"))&&index>=2)||(path.equals("/marker/anchor")&&index>=2)||(path.equals("/marker/colors")&&index>=3)){fail();}
        return value;
    }
    function knownField(path,key){
        var allowed=null;
        if(path.equals("")){allowed=readKind==0?["type","schemaVersion","rendererProfile","layoutRevision","sourceSelection","launchId","modelId","operatorId","siteId","countryId","sourcePosition","position","positionMode","mapDefinitionSha256","mapSource","marker","roles"]:readKind==1?["type","schemaVersion","rendererProfile","canvas","channels","pixelSha256","sourceDescriptor","sourceSemanticSha256","animation","shards"]:["type","schemaVersion","rendererProfile","scene","objects"];}
        else if(path.equals("/roles")){allowed=names;}
        else if(path.equals("/origins")){allowed=["model","operator"];}
        else if(path.equals("/origins/model")||path.equals("/origins/operator")){allowed=["ownerId","countryId","sourceRecord"];}
        else if(path.equals("/mapSource")){allowed=["recipeSha256","worldSha256","corresponding","notices"];}
        else if(path.equals("/marker")){allowed=["anchor","diameter","colors"];}
        else if(path.equals("/position")||path.equals("/sourcePosition")){allowed=["encoding","latitude","longitude","units","qualification"];}
        else if(path.equals("/roles/map")||path.equals("/roles/rocket")||path.equals("/roles/siteCountry")){allowed=["entityId","descriptor"];}
        else{allowed=["path","sha256","decodedBytes"];}
        if(path.equals("")){if(readKind==0){allowed=sceneKeys();}else if(readKind==1){allowed=allowed.slice(0,allowed.size());allowed.add("sourceCanvas");allowed.add("motionSource");}}
        if(allowed.indexOf(key)<0){fail();}
    }
    function sourceRef(r){packet.shape(r,["path","sha256","decodedBytes"],[]);if(!packet.hex(r["sha256"])||!packet.integer(r["decodedBytes"])||r["decodedBytes"]<1||r["decodedBytes"]>1048576||!packet.same(r["path"],"sources/"+r["sha256"]+".json")){fail();}}
    function sceneField(key,value){
        if(key.equals("sourcePosition")||key.equals("position")){var site=packet.bridge["site"];if(!same(value,site==null?null:site[key])){fail();}return key.equals("position")&&value!=null?true:null;}
        if(key.equals("sourceSelection")){ref(value,"descriptors");return null;}
        if(key.equals("mapDefinitionSha256")){if(value!=null&&!packet.hex(value)){fail();}return value==null?null:true;}
        if(key.equals("marker")){if(value!=null&&!same(value,{"anchor"=>[335,165],"diameter"=>28,"colors"=>[0,0xf7f9fc,0xffd166]})){fail();}return value==null?null:true;}
        if(key.equals("mapSource")){if(value!=null){packet.shape(value,["recipeSha256","worldSha256","corresponding","notices"],[]);}return value==null?null:true;}
        return value;
    }
    function sceneKeys(){var keys=["type","schemaVersion","rendererProfile","layoutRevision","sourceSelection","launchId","modelId","operatorId","siteId","countryId","sourcePosition","position","positionMode","mapDefinitionSha256","mapSource","marker","roles"];keys.add("origins");keys.add("siteCountrySource");return keys;}
    function admitOrigins(){
        var origins=scene["origins"];packet.shape(origins,["model","operator"],[]);var modes=["model","operator"];for(var i=0;i<2;i+=1){var origin=origins[modes[i]];packet.shape(origin,["ownerId","countryId","sourceRecord"],[]);var owner=scene[i==0?"modelId":"operatorId"];if(!same(origin["ownerId"],owner)||!packet.id(origin["countryId"],"country",true)||owner==null&&origin["countryId"]!=null||origin["sourceRecord"]!=true){fail();}origin.remove("sourceRecord");}
    }
    function begin(){
        if(packet.bridge==null||packet.bridge["version"]!=3||selection==null){fail();}ref(selection,"descriptors");var rawScene=immutable.raw(selection);if(rawScene==null){fail();}NativeMetrics.sample("sfr-build-root-raw");var parser=new NativeJson();parser.feedMode=true;parser.rootOwner=self;parser.nodeOwner=self;scene=parser.parse(rawScene,4096);rawScene=null;parser=null;NativeMetrics.sample("sfr-build-root-parsed");packet.shape(scene,sceneKeys(),[]);
        if(!packet.same(scene["type"],"native-scene")||!packet.integer(scene["schemaVersion"])||scene["schemaVersion"]!=3||!packet.same(scene["rendererProfile"],"SFR1M")||!packet.same(scene["layoutRevision"],"native-04-motion-v1")){fail();}var keys=["launchId","modelId","operatorId","siteId","countryId"];for(var i=0;i<keys.size();i+=1){if(!same(scene[keys[i]],packet.bridge["ids"][i])){fail();}}
        var site=packet.bridge["site"];if(!same(scene["positionMode"],site==null?null:site["positionMode"])){fail();}
        if(scene["position"]!=null){if(scene["mapDefinitionSha256"]!=true||scene["marker"]!=true||scene["mapSource"]!=true){fail();}}
        admitOrigins();if(scene["siteCountrySource"]!=true){fail();}scene.remove("siteCountrySource");packet.shape(scene["roles"],names,[]);if(scene["position"]==null&&(scene["roles"]["map"]!=null||scene["marker"]!=null)){fail();}add(selection);
        // Provenance is digest-bound by the raw root. Only current scene facts
        // and selected role references need to remain resident after admission.
        scene.remove("mapSource");scene.remove("sourceSelection");scene.remove("sourcePosition");scene.remove("mapDefinitionSha256");scene.remove("marker");result.scene=scene;result.selectionHash=selection["sha256"];
    }
    function prepareRole(name){
        var binding=scene["roles"][name];if(binding==null){return null;}packet.shape(binding,["entityId","descriptor"],[]);var identity=name.equals("map")?scene["siteId"]:name.equals("rocket")?scene["modelId"]:scene["countryId"];if(identity==null||!packet.same(binding["entityId"],identity)){fail();}var tuple=binding["descriptor"];var r={"sha256"=>tuple[0],"decodedBytes"=>tuple[1]};add(r);readKind=1;var d=read(r);var moving=name.equals("rocket");packet.shape(d,["type","schemaVersion","rendererProfile","canvas","channels","pixelSha256","sourceDescriptor","sourceSemanticSha256","animation","shards"],moving?["sourceCanvas","motionSource"]:[]);if(moving&&(!d.hasKey("sourceCanvas")||!d.hasKey("motionSource"))){fail();}
        var size=name.equals("map")?[390,390]:name.equals("rocket")?[54,124]:[20,12];
        if(!packet.same(d["type"],"raster")||!packet.integer(d["schemaVersion"])||d["schemaVersion"]!=(moving?2:1)||!packet.same(d["rendererProfile"],moving?"SFR1M":"SFR1")||!same(d["canvas"],size)||!packet.integer(d["channels"])||d["channels"]!=(name.equals("map")?3:4)||!packet.hex(d["pixelSha256"])||!name.equals("map")&&!packet.hex(d["sourceSemanticSha256"])||name.equals("map")&&d["sourceSemanticSha256"]!=null||!(d["shards"] instanceof Array)||d["shards"].size()<1||d["shards"].size()>32){fail();}var total=0;for(var i=0;i<d["shards"].size();i+=1){var shard=d["shards"][i];if(addTuple(1,shard[0],shard[1])){total+=shard[1];rasterObjects+=1;}}rasterBytes+=total;if(rasterBytes>98304||rasterObjects>32){fail();}
        if(!moving&&!same(d["animation"],[0,[]])){fail();}if(moving){var canvas=d["sourceCanvas"];if(!(canvas instanceof Array)||canvas.size()!=2||!packet.integer(canvas[0])||!packet.integer(canvas[1])||canvas[0]<1||canvas[0]>256||canvas[1]<1||canvas[1]>256||d["motionSource"]!=true){fail();}}
        new NativeAnimation().validate(d["animation"]);if(name.equals("rocket")){result.manifest={"canvas"=>moving?d["sourceCanvas"]:size,"animation"=>d["animation"]};result.animations=d["animation"];result.prepareCanvas(result.manifest["canvas"]);}
        d.remove("sourceDescriptor");d.remove("sourceSemanticSha256");return d;
    }
    function checkIndex(){
        readKind=2;var index=read(ref(packet.bridge["transfer"],"descriptors"));packet.shape(index,["type","schemaVersion","rendererProfile","scene","objects"],[]);if(!packet.same(index["type"],"native-transfer")||!packet.integer(index["schemaVersion"])||index["schemaVersion"]!=1||!packet.same(index["rendererProfile"],"SFR1M")||!same(index["scene"],[selection["sha256"],selection["decodedBytes"]])||!(index["objects"] instanceof Array)||index["objects"].size()!=expected.size()||expected.size()>40){fail();}var total=0;for(var i=0;i<expected.size();i+=1){var r=expected[i];if(!same(index["objects"][i],r)){fail();}total+=r[2];}if(total>114688){fail();}
    }
    function checkRaw(r){if(immutable.raw({"sha256"=>r[1],"decodedBytes"=>r[2]})==null){fail();}}
    function closure(){
        // Commit only the complete decoded/pixel-verified current selection.
        var beforeWrites=store.writes;var prior=store.read("sf.raster.active");if(prior instanceof Dictionary&&!(prior["base"] instanceof String&&prior["base"].equals(base)&&prior["selectionHash"] instanceof String&&prior["selectionHash"].equals(selection["sha256"]))){store.write("sf.raster.recovery",prior);}if(!(prior instanceof Dictionary&&prior["base"] instanceof String&&prior["base"].equals(base)&&prior["selectionHash"] instanceof String&&prior["selectionHash"].equals(selection["sha256"]))){var refs=expected.slice(0,expected.size());refs.add([0,packet.bridge["transfer"]["sha256"],packet.bridge["transfer"]["decodedBytes"]]);store.write("sf.raster.active",{"base"=>base,"catalogDigest"=>packet.bridge["catalogDigest"],"selectionHash"=>selection["sha256"],"refs"=>refs});}result.scene=displayScene();complete=true;packet=null;NativeMetrics.writes("raster-activation",store.writes-beforeWrites);
    }
    function displayScene(){return {"position"=>scene["position"]};}
    function step(){
        if(role>=names.size()){if(!closureChecked){checkIndex();closureChecked=true;scene=displayScene();result.scene=scene;return false;}if(closureAt<expected.size()){var start=System.getTimer();var checked=0;while(closureAt<expected.size()&&checked<4&&(checked==0||System.getTimer()-start<18)){checkRaw(expected[closureAt]);closureAt+=1;checked+=1;}return false;}closure();return true;}var name=names[role];if(decoder==null){var d=prepareRole(name);if(d==null){role+=1;return false;}decoder=new NativeSfrDecoder(store,d);}
        if(decoder.step()){if(name.equals("map")){result.mapBitmap=decoder.bitmap;NativeMetrics.sample("sfr-first-map-verified");}else if(name.equals("rocket")){result.bitmap=decoder.bitmap;}else if(name.equals("siteCountry")){result.siteCountryBitmap=decoder.bitmap;}decoder=null;role+=1;}return false;
    }
}
