import Toybox.Lang;
class NativeCompany {
    var resource as ResourceId; var origin as String;
    function initialize(r as ResourceId,o as String){resource=r;origin=o;}
}
class NativeModel extends NativeCompany {
    var country as Array<Number>;var company as Array<Number>;
    function initialize(r as ResourceId,o as String,c as Array<Number>,m as Array<Number>){NativeCompany.initialize(r,o);country=c;company=m;}
}
class NativeMap {
    var longitude as Numeric;var latitude as Numeric;var resource as ResourceId;
    function initialize(x as Numeric,y as Numeric,r as ResourceId){longitude=x;latitude=y;resource=r;}
}
