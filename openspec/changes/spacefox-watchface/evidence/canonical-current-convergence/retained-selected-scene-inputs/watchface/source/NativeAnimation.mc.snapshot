import Toybox.Lang;
(:extendedCode,:typecheck(false))
class NativeAnimation {
    function initialize(){}
    function fail(){throw new Lang.InvalidValueException("Invalid native animation");}
    function integer(v){return v instanceof Number||v instanceof Long;}
    function bounded(v,lo,hi){return integer(v)&&v>=lo&&v<=hi;}
    function array(v,size){return v instanceof Array&&v.size()==size;}
    function validate(a){
        if(!array(a,2)||!integer(a[0])||!(a[1] instanceof Array)){fail();}if(a[0]==0){if(a[1].size()!=0){fail();}return;}
        if(!bounded(a[0],2000,3000)||a[1].size()<2||a[1].size()>16){fail();}var last=-1;
        for(var i=0;i<a[1].size();i+=1){var f=a[1][i];if(!array(f,4)||!bounded(f[0],0,a[0])||f[0]<=last||!bounded(f[1],-2048,2048)||!bounded(f[2],-2048,2048)||!bounded(f[3],128,512)){fail();}if(i==0&&(f[0]!=0||f[1]!=0||f[2]!=0||f[3]!=256)){fail();}last=f[0];}if(last!=a[0]){fail();}
    }
}
