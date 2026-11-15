import Toybox.Lang;
class NativeModel {
    var resource as ResourceId;
    function initialize(r as ResourceId){resource=r;}
}
class NativeMap {
    var longitude as Numeric;var latitude as Numeric;var resource as ResourceId;
    function initialize(x as Numeric,y as Numeric,r as ResourceId){longitude=x;latitude=y;resource=r;}
}
