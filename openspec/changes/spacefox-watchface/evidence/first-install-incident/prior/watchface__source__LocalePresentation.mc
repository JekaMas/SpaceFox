import Toybox.Graphics;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.System;

// One foreground owner survives renderer release, so active/AOD/maintenance
// share the same dictionary and fonts. All resources are prepared off redraw.
(:extendedCode, :typecheck(false))
class LocalePresentation {
    var qualificationMode as Boolean=false;
    var locale as String="";
    var dictionary=null;
    var small as Graphics.FontType or Null=null;
    var label as Graphics.FontType or Null=null;
    var latinSmall as Graphics.FontType or Null=null;
    var count as Graphics.FontType or Null=null;
    var loads=0;
    function initialize(){
        // Proper names use a shared Latin face, independent of UI language.
        // SDK font files stay external; retain only these two common handles.
        try{label=Graphics.getVectorFont({:face=>"RobotoRegular",:size=>26});latinSmall=Graphics.getVectorFont({:face=>"RobotoRegular",:size=>22});}catch(e){}
        if(label==null){label=Graphics.FONT_TINY;}if(latinSmall==null){latinSmall=Graphics.FONT_XTINY;}
        LocaleGraphemes.load();prepare("en");
    }
    function prepare(requested) {
        var index=SceneStrings.index(requested);
        if(!qualificationMode&&!SceneStrings.available(index)){index=0;}
        var next=SceneStrings.locale(index);
        if(next.equals(locale)){return;}
        dictionary=null;small=null;count=null;locale="";
        try {
            dictionary=WatchUi.loadResource(SceneStrings.resource(index));loads+=1;
            var face=dictionary["face"];
            small=face.equals("RobotoRegular")?latinSmall:Graphics.getVectorFont({:face=>[face,"RobotoRegular"],:size=>22});
            count=Graphics.getVectorFont({:face=>[face,"RobotoRegular"],:size=>36});
            if(small==null||label==null||count==null){throw new Lang.InvalidValueException("locale font unavailable");}
            locale=next;
        } catch(e) {
            dictionary=null;small=null;count=null;
            if(!next.equals("en")){prepare("en");return;}
            // Built-in English survives unavailable scalable-font resources.
            locale="en";small=latinSmall;count=Graphics.FONT_SMALL;
        }
    }
    function word(key) as String {
        if(dictionary!=null&&dictionary.hasKey(key)){return dictionary[key];}
        if(key.equals("noSchedule")){return "No schedule";}
        if(key.equals("dateOnly")){return "Date only";}
        if(key.equals("window")){return "Launch window";}
        if(key.equals("awaitUpdate")){return "Awaiting update";}
        if(key.equals("day")){return "d";}if(key.equals("hour")){return "h";}if(key.equals("minute")){return "m";}if(key.equals("second")){return "s";}
        return "Time unknown";
    }
    function mission(value as String) as String {
        // The provider category remains retained verbatim; only this known
        // semantic category has an existing locale resource mapping.
        if(value.equals("Communications")&&dictionary!=null&&dictionary.hasKey("communications")){return dictionary["communications"];}
        return value;
    }
    function countdown(current, active) as String {
        return CountdownFormat.format(current.remaining);
    }
    function number(raw) as String {
        if(raw.equals("—")){return raw;}
        var separator=dictionary==null?",":dictionary["group"];var result="";
        while(raw.length()>3){result=separator+raw.substring(raw.length()-3,raw.length())+result;raw=raw.substring(0,raw.length()-3);}
        return raw+result;
    }
    function metric(fitness,values,role) as String {var raw=fitness.display(values,role);return role.equals("steps")||role.equals("calories")?number(raw):raw;}
    function date(iso) as String {
        // Provider date is a UTC civil date, never a fabricated midnight moment.
        // Garmin exposes no date-order preference: explicit locale rule.
        if(iso.length()!=10){return word("dateOnly");}
        var y=iso.substring(0,4);var m=iso.substring(5,7);var d=iso.substring(8,10);
        var order=dictionary==null?"mdy":dictionary["dateOrder"];
        if(order.equals("ymd")){return y+"/"+m+"/"+d;}
        return order.equals("mdy")?m+"/"+d+"/"+y:d+"/"+m+"/"+y;
    }
    function fit(dc,value,font,width) as String {
        if(dc.getTextWidthInPixels(value,font)<=width){return value;}
        if(dc.getTextWidthInPixels("…",font)>width){return "";}
        // Walk each visible boundary once. Re-scanning every growing prefix
        // multiplied Unicode property decoding inside a single redraw.
        var best="…";var end=1;var ri=0;
        var chars=[value.substring(0,1).toCharArray()[0]];
        while(end<=value.length()){
            var boundary=end==value.length();
            if(!boundary){
                chars.add(value.substring(end,end+1).toCharArray()[0]);
                var prior=chars[end-1].toNumber();
                if(prior>=0x1f1e6&&prior<=0x1f1ff){ri+=1;}else{ri=0;}
                boundary=clusterBoundary(chars,end,ri);
            }
            if(boundary){
                var candidate=value.substring(0,end)+"…";
                if(dc.getTextWidthInPixels(candidate,font)>width){break;}
                best=candidate;
            }
            end+=1;
        }
        return best;
    }
    function previousCluster(value,end) as Number {
        return previousPoints(value.toCharArray(),end);
    }
    function previousPoints(chars,end) as Number {
        var boundary=0;var ri=0;
        for(var i=1;i<end;i+=1){
            var a=chars[i-1].toNumber();
            if(a>=0x1f1e6&&a<=0x1f1ff){ri+=1;}else{ri=0;}
            if(clusterBoundary(chars,i,ri)){boundary=i;}
        }
        return boundary;
    }
    function clusterBoundary(chars,i,ri) as Boolean {
        var a=chars[i-1].toNumber();var b=chars[i].toNumber();
        // Printable ASCII pairs cannot be joined by any UAX29 rule. Controls
        // and every boundary touching a non-ASCII code point use the full rules.
        if(a>=32&&a<=126&&b>=32&&b<=126){return true;}
        var join=false;
        if(a==13&&b==10){join=true;}
        else if(!LocaleGraphemes.control(a)&&!LocaleGraphemes.control(b)){
            join=LocaleGraphemes.extend(b)||b==0x200d||LocaleGraphemes.spacing(b)||LocaleGraphemes.prepend(a)||(a>=0x1f1e6&&a<=0x1f1ff&&b>=0x1f1e6&&b<=0x1f1ff&&ri%2==1)||LocaleGraphemes.hangul(a,b);
            if(!join&&a==0x200d&&LocaleGraphemes.pictographic(b)){
                var j=i-2;while(j>=0&&LocaleGraphemes.extend(chars[j].toNumber())){j-=1;}
                join=j>=0&&LocaleGraphemes.pictographic(chars[j].toNumber());
            }
            if(!join&&LocaleGraphemes.incbConsonant(b)){
                var j=i-1;var linker=false;
                while(j>=0&&(LocaleGraphemes.incbExtend(chars[j].toNumber())||LocaleGraphemes.incbLinker(chars[j].toNumber()))){if(LocaleGraphemes.incbLinker(chars[j].toNumber())){linker=true;}j-=1;}
                join=linker&&j>=0&&LocaleGraphemes.incbConsonant(chars[j].toNumber());
            }
        }
        return !join;
    }
}
