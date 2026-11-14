import Toybox.Lang;

(:extendedCode, :typecheck(false))
function nativeSame(a,b){
    if(a==null||b==null){return a==null&&b==null;}
    if(a instanceof String){return b instanceof String&&a.equals(b);}
    if(a instanceof Number||a instanceof Long){return (b instanceof Number||b instanceof Long)&&a==b;}
    if(a instanceof Boolean){return b instanceof Boolean&&a==b;}
    if(a instanceof Array){if(!(b instanceof Array)||a.size()!=b.size()){return false;}for(var i=0;i<a.size();i+=1){if(!nativeSame(a[i],b[i])){return false;}}return true;}
    if(a instanceof Dictionary){if(!(b instanceof Dictionary)||a.size()!=b.size()){return false;}var keys=a.keys();for(var j=0;j<keys.size();j+=1){if(!b.hasKey(keys[j])||!nativeSame(a[keys[j]],b[keys[j]])){return false;}}return true;}return false;
}

// The current schema3 SFR1M feed keeps exact raw/hash/order semantics. A bounded
// immutable catalog is admitted before the common launch/clock validator runs.
(:extendedCode, :typecheck(false))
class NativeBridgeFeed extends NativeFeed {
    var catalogStore;var catalogData=null;var catalogSiteId=null;var catalogSite=null;var catalogPin="";
    function initialize(text,now,adapter){catalogStore=adapter;NativeFeed.initialize(text,now);}
    function ref(r,prefix){shape(r,["path","sha256","decodedBytes"],[]);if(!hex(r["sha256"])||!integer(r["decodedBytes"])||r["decodedBytes"]<1||r["decodedBytes"]>4096||!same(r["path"],prefix+"/"+r["sha256"]+(prefix.equals("rasters")?".sfr":".json"))){fail();}return r;}
    function equal(a,b){return nativeSame(a,b);}
    function parse(value){
        catalogPin=nativeHeaderText(value,"catalogDigest");catalogSiteId=nativeHeaderText(value,"site_id");if(!hex(catalogPin)){fail();}
        var rawCatalog=catalogStore.read("sf.obj."+catalogPin);if(!(rawCatalog instanceof String)||rawCatalog.length()>4096){throw new Lang.InvalidValueException("Bridge catalog incomplete");}var hash=new NativeWireHash();hash.put(rawCatalog);if(!hash.digest().equals(catalogPin)||hash.count>4096){throw new Lang.InvalidValueException("Bridge catalog incomplete");}
        NativeMetrics.sample("bridge-catalog-before-parse");var parser=new NativeJson();parser.feedMode=true;parser.catalogMode=true;parser.rowOwner=self;catalogData=parser.parse(rawCatalog,4096);rawCatalog=null;parser=null;hash=null;NativeMetrics.sample("bridge-catalog-projected");NativeFeed.parse(value);
    }
    function dictionaryRow(key,row){
        var isSite=row instanceof Dictionary&&same(row["kind"],"site");shape(row,isSite?["kind","name","visual","sourcePosition","position","positionMode"]:["kind","name","visual"],[]);if(row["visual"]!=null){ref(row["visual"],"descriptors");}
        if(isSite){if(["fixed-source","mobile-reference-no-event"].indexOf(row["positionMode"])<0||!equal(row["position"],same(row["positionMode"],"fixed-source")?row["sourcePosition"]:null)){fail();}if(catalogSiteId!=null&&same(key,catalogSiteId)){catalogSite={"sourcePosition"=>row["sourcePosition"],"position"=>row["position"],"positionMode"=>row["positionMode"]};}row.remove("positionMode");row["position"]=null;}row["visual"]=null;return NativeFeed.dictionaryRow(key,row);
    }
    function header(d){
        NativeMetrics.sample("bridge-header-start");
        var version=d["schemaVersion"];if(!integer(version)||version!=3){fail();}
        var required=["schemaVersion","catalogRevision","catalogDigest","catalogPath","unresolvedCatalogIds","launch","timingState","refreshPolicy","pollIntervalSeconds","sourceContentRevision","selection","providerTraversal","publisher","visualSelection","catalogSourceDigest","dictionaryMode"];
        required.add("rendererProfile");required.add("nativeTransfer");shape(d,required,[]);
        if(!text(d["catalogRevision"],false)||d["catalogRevision"].length()==0||!hex(d["catalogDigest"])||!hex(d["sourceContentRevision"])||!hex(d["catalogSourceDigest"])||!same(d["dictionaryMode"],"immutable-catalog")||!same(d["catalogPath"],"wire3/catalogs/"+d["catalogDigest"]+".json")){fail();}
        if(d["visualSelection"]!=null){ref(d["visualSelection"],"descriptors");}if(!same(d["rendererProfile"],"SFR1M")){fail();}ref(d["nativeTransfer"],"descriptors");NativeMetrics.sample("bridge-header-refs");
        var catalog=catalogData;shape(catalog,["schemaVersion","catalogVersion","projection","entries","unresolved","visualSelection"],[]);
        if(!same(catalogPin,d["catalogDigest"])||!integer(catalog["schemaVersion"])||catalog["schemaVersion"]!=version||!same(catalog["catalogVersion"],d["catalogRevision"])||!same(catalog["projection"],"selected-display-motion-v3")||!equal(catalog["unresolved"],d["unresolvedCatalogIds"])||!equal(catalog["visualSelection"],d["visualSelection"])||!(catalog["entries"] instanceof Dictionary)){fail();}
        d["dictionaries"]=catalog["entries"];var l=d["launch"];if(l!=null&&!equal(catalogSiteId,l["site_id"])){fail();}
        bridge={"version"=>version,"catalogDigest"=>d["catalogDigest"],"selection"=>d["visualSelection"],"transfer"=>d["nativeTransfer"],"site"=>catalogSite,"ids"=>l==null?null:[l["launch_id"],l["configuration_id"],l["operator_id"],l["site_id"],l["country_id"]]};catalogData=null;
        NativeMetrics.sample("bridge-catalog-admitted");
    }
    function catalogHash(d){}
}

