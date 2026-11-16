import Toybox.ActivityMonitor;
import Toybox.Application;
import Toybox.Complications;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;

// Runtime enumeration is intentionally limited to the picker. Active drawing
// retains only the four selected identifiers and formatted values.
(:extendedCode, :typecheck(false))
module FieldCatalog {
    function saved(slot) {try{return Application.Storage.getValue("sf.field"+slot);}catch(e){return null;}}
    // Re-enumerate when changing pages so no full provider inventory remains
    // resident beside the selected scene. Only six entries are materialized.
    function page(locale,offset) {
        var result=new FieldPage(offset);var types=[];var words=null;
        try {
            var iter=Complications.getComplications();var item=iter.next();
            while(item!=null){
                if(item.complicationId!=null){
                    var kind=item.getType();if((kind==4||kind==5||kind==21||kind==36||kind==37||kind==40)&&types.indexOf(kind)<0){types.add(kind);}
                    // Legacy choices use their original readers; expose the
                    // complication itself even when its label looks similar.
                    var label=item.longLabel;
                    if(!(label instanceof String)||label.equals("")){label=item.shortLabel;}
                    if(!(label instanceof String)||label.equals("")){label=kind instanceof Number&&kind>0?"Complication "+kind:"Complication";}
                    if(kind==18||kind==22){if(words==null){words=FieldText.menu(locale);}label+=" "+words["current"];}
                    result.add(label,item.complicationId);
                }
                if(result.more){return result;}
                item=iter.next();
            }
        } catch(e) {}
        try {var info=ActivityMonitor.getInfo();if(info!=null){
            var keys=activityKeys();if(words==null){words=FieldText.menu(locale);}var labels=words["activity"];
            for(var i=0;i<keys.size();i+=1){var key=keys[i];
                var duplicate=(key.equals("activeMinutesWeekTotal")&&types.indexOf(5)>=0)||(key.equals("floorsClimbed")&&types.indexOf(4)>=0)||(key.equals("pushes")&&types.indexOf(40)>=0)||(key.equals("timeToRecovery")&&types.indexOf(21)>=0)||(key.equals("respirationRate")&&types.indexOf(36)>=0);
                if(!duplicate&&supported(info,key)){result.add(labels[i],key);if(result.more){return result;}}}
        }}catch(e){}
        try{var stats=System.getSystemStats();if(stats!=null){var keys=systemKeys();if(words==null){words=FieldText.menu(locale);}var labels=words["system"];
            for(var i=0;i<keys.size();i+=1){if(systemSupported(stats,keys[i],types)){result.add(labels[i],keys[i]);if(result.more){return result;}}}
        }}catch(e){}
        return result;
    }
    function systemKeys(){return ["system:batteryInDays","system:charging","system:solarIntensity"];}
    function systemLabels(locale){return FieldText.menu(locale)["system"];}
    function systemSupported(stats,key,types){
        if(key.equals("system:batteryInDays")){return stats has :batteryInDays;}
        if(key.equals("system:charging")){return stats has :charging;}
        if(key.equals("system:solarIntensity")){return types.indexOf(37)<0&&stats has :solarIntensity&&stats.solarIntensity!=null;}
        return false;
    }
    function systemValue(stats,key){if(key.equals("system:batteryInDays")&&stats has :batteryInDays){return stats.batteryInDays;}
        if(key.equals("system:charging")&&stats has :charging){return stats.charging;}
        if(key.equals("system:solarIntensity")&&stats has :solarIntensity){return stats.solarIntensity;}return null;}
    function activityKeys(){return ["distance","stepGoal","floorsClimbedGoal","floorsDescended","metersClimbed","metersDescended","moveBarLevel","activeMinutesWeekGoal","activeMinutesDayTotal","activeMinutesDayModerate","activeMinutesDayVigorous","activeMinutesWeekTotal","activeMinutesWeekModerate","activeMinutesWeekVigorous","pushes","pushGoal","pushDistance","timeToRecovery","respirationRate","stressScore","floorsClimbed"];}
    function activityLabels(locale){return FieldText.menu(locale)["activity"];}
    function supported(info,key){
        if(key.equals("distance")){return info has :distance;} if(key.equals("stepGoal")){return info has :stepGoal;}
        if(key.equals("floorsClimbedGoal")){return info has :floorsClimbedGoal;} if(key.equals("floorsDescended")){return info has :floorsDescended;}
        if(key.equals("metersClimbed")){return info has :metersClimbed;} if(key.equals("metersDescended")){return info has :metersDescended;}
        if(key.equals("moveBarLevel")){return info has :moveBarLevel;} if(key.equals("activeMinutesWeekGoal")){return info has :activeMinutesWeekGoal;}
        if(key.find("activeMinutesDay")==0){return info has :activeMinutesDay;} if(key.find("activeMinutesWeek")==0){return info has :activeMinutesWeek;}
        if(key.equals("pushes")){return info has :pushes;} if(key.equals("pushGoal")){return info has :pushGoal;} if(key.equals("pushDistance")){return info has :pushDistance;}
        if(key.equals("floorsClimbed")){return info has :floorsClimbed;} if(key.equals("timeToRecovery")){return info has :timeToRecovery;} if(key.equals("respirationRate")){return info has :respirationRate;} if(key.equals("stressScore")){return info has :stressScore;}
        return false;
    }
    function activityValue(info,key){
        if(!supported(info,key)){return null;}
        if(key.equals("distance")){return info.distance;} if(key.equals("stepGoal")){return info.stepGoal;}
        if(key.equals("floorsClimbedGoal")){return info.floorsClimbedGoal;} if(key.equals("floorsDescended")){return info.floorsDescended;}
        if(key.equals("metersClimbed")){return info.metersClimbed;} if(key.equals("metersDescended")){return info.metersDescended;}
        if(key.equals("moveBarLevel")){return info.moveBarLevel;} if(key.equals("activeMinutesWeekGoal")){return info.activeMinutesWeekGoal;}
        if(key.equals("pushes")){return info.pushes;} if(key.equals("pushGoal")){return info.pushGoal;} if(key.equals("pushDistance")){return info.pushDistance;}
        if(key.equals("floorsClimbed")){return info.floorsClimbed;} if(key.equals("timeToRecovery")){return info.timeToRecovery;} if(key.equals("respirationRate")){return info.respirationRate;} if(key.equals("stressScore")){return info.stressScore;}
        var minutes=key.find("activeMinutesDay")==0?info.activeMinutesDay:info.activeMinutesWeek;
        if(minutes==null){return null;} if(key.find("Moderate")!=null){return minutes.moderate;} if(key.find("Vigorous")!=null){return minutes.vigorous;}return minutes.total;
    }
}

(:extendedCode, :typecheck(false))
class FieldPage {
    var entries=[];var offset=0;var count=0;var more=false;
    function initialize(start){offset=start;}
    function add(label,source){if(count>=offset&&entries.size()<6){entries.add([label,source]);}else if(count>=offset+6){more=true;}count+=1;}
}

(:extendedCode, :typecheck(false))
module FieldFormat {
    function decimal(value){return value.format("%.1f");}
    function clock(seconds){var n=seconds.toNumber();return (n/3600).format("%02d")+":"+((n/60)%60).format("%02d");}
    function duration(seconds){var n=seconds.toNumber();return (n/3600)>0?(n/3600).toString()+":"+((n/60)%60).format("%02d")+":"+(n%60).format("%02d"):(n/60).toString()+":"+(n%60).format("%02d");}
    function weather(n,locale){
        // These categories preserve the official condition family, including
        // forecasts expressed as a chance; unknown codes remain unavailable.
        var category=0;
        if([0,22,23,40].indexOf(n)>=0){category=1;}
        else if([1,2,20,52].indexOf(n)>=0){category=2;}
        else if([3,11,14,15,24,25,26,31].indexOf(n)>=0){category=3;}
        else if([4,16,17,48].indexOf(n)>=0){category=4;}
        else if([6,12].indexOf(n)>=0){category=5;}
        else if([5,36].indexOf(n)>=0){category=6;}
        else if(n==10){category=7;}
        else if([7,18,19,21,34,49,50,51].indexOf(n)>=0){category=8;}
        else if([8,29].indexOf(n)>=0){category=9;}
        else if([9,39].indexOf(n)>=0){category=10;}
        else if([30,35,37].indexOf(n)>=0){category=11;}
        else if(n==33){category=12;}else if(n==38){category=13;}
        else if(n==32){category=14;}else if([41,42].indexOf(n)>=0){category=15;}
        else if([27,45].indexOf(n)>=0){category=16;}
        else if([43,46].indexOf(n)>=0){category=17;}
        else if([44,47].indexOf(n)>=0){category=18;}
        else if(n==28){category=19;}else if(n==13){category=20;}
        var labels=FieldText.weather(locale);
        return labels[category];
    }
    function complication(item,locale){
        var v=item.value;if(v==null){return "—";}if(v instanceof String){return v;}
        if(!(v instanceof Number||v instanceof Long||v instanceof Float||v instanceof Double)){return "—";}
        var t=item.getType();if(!(t instanceof Number)){t=0;}var u=item.unit;
        if(t>=8&&t<=11){return weather(v,locale);} if(t==13||t==14){return v>=0&&v<86400?clock(v):"—";}
        if(t>=27&&t<=30){return v>=0?duration(v):"—";}
        if(t==21){return v.toString()+" min";} if(t==16){return decimal(v/100.0)+" hPa";}
        if(t==1||t==35||t==37){return v.toString()+"%";} if(t==38){return decimal(v)+"°C";}
        if(t==15){return decimal(v)+" m";} if(t==19||t==20){return decimal(v/1000.0)+" km";}
        if(t>=31&&t<=34){return decimal(v*3.6)+" km/h";}
        if(u==1){return decimal(v/1000.0)+" km";} if(u==2||u==3){return decimal(v)+" m";}
        if(u==4){return decimal(v*3.6)+" km/h";} if(u==5){return decimal(v)+"°C";} if(u==6){return decimal(v/1000.0)+" kg";}
        return v.toString()+(u instanceof String&&!u.equals("")?" "+u:"");
    }
    function system(key,v,locale){
        if(v==null){return "—";}
        if(key.equals("system:batteryInDays")){return v>=0?decimal(v)+" d":"—";}
        if(key.equals("system:charging")){if(!(v instanceof Boolean)){return "—";}var labels=FieldText.status(locale);return labels[v?0:1];}
        if(key.equals("system:solarIntensity")){if(v<0){return FieldText.status(locale)[2];}return v<=100?v.toString()+"%":"—";}
        return "—";
    }
    function activity(key,v){
        if(v==null){return "—";} if(key.equals("distance")||key.equals("pushDistance")){return decimal(v/100000.0)+" km";}
        if(key.equals("metersClimbed")||key.equals("metersDescended")){return decimal(v)+" m";}
        if(key.find("activeMinutes")==0){return v.toString()+" min";} if(key.equals("timeToRecovery")){return v.toString()+" h";}return v.toString();
    }
}

// Test adapters implement the same methods; production uses Garmin directly.
(:extendedCode, :typecheck(false))
class FieldComplicationApi {
    function register(callback){Complications.registerComplicationChangeCallback(callback);}
    function subscribe(id){return Complications.subscribeToUpdates(id);}
    function unsubscribe(id){Complications.unsubscribeFromUpdates(id);}
    function get(id){return Complications.getComplication(id);}
}

// One callback owner and at most four distinct subscriptions. Identifiers stay
// persisted if a provider disappears; a failed subscription is polled on minute.
(:extendedCode, :typecheck(false))
class SelectedFields {
    var selected=[];var subscribed=[];var labels={};var text={};var icons={};var energy as Number or Null=null;var callbackRegistered=false;var provider=null;var api=null;var customMask=0;var fittedMask=0;var numericMask=0;
    function initialize(){}
    function start(slots,callback){
        stop();
        for(var i=0;i<4;i+=1){
            var custom=slots[i].equals("custom"+(i+1));if(custom){customMask|=(1<<i);}
            var source=slots[i].equals("energy")?new Complications.Id(23):(custom?FieldCatalog.saved(i+1):null);
            selected.add(source);
        }
        var hasComplication=false;for(var i=0;i<selected.size();i+=1){if(selected[i] instanceof Complications.Id){hasComplication=true;break;}}
        if(!hasComplication){return;}
        try{if(api==null){Complications.registerComplicationChangeCallback(callback);}else{api.register(callback);}callbackRegistered=true;}catch(e){}
        if(!callbackRegistered){return;}
        var attempted=[];
        for(var i=0;i<selected.size();i+=1){var id=selected[i];if(!(id instanceof Complications.Id)){continue;}var duplicate=false;
            for(var j=0;j<attempted.size();j+=1){if(id.equals(attempted[j])){duplicate=true;break;}}
            if(!duplicate){attempted.add(id);try{if(api==null?Complications.subscribeToUpdates(id):api.subscribe(id)){subscribed.add(id);}}catch(e){}}
        }
    }
    function stop(){for(var i=0;i<subscribed.size();i+=1){try{if(api==null){Complications.unsubscribeFromUpdates(subscribed[i]);}else{api.unsubscribe(subscribed[i]);}}catch(e){}}
        if(callbackRegistered){try{if(api==null){Complications.registerComplicationChangeCallback(null);}else{api.register(null);}}catch(e){}}
        subscribed=[];selected=[];labels={};text={};icons={};energy=null;callbackRegistered=false;customMask=0;fittedMask=0;numericMask=0;
    }
    function read(locale){readSelected(locale,null);}
    function readChanged(locale,id){readSelected(locale,id);}
    function readSelected(locale,onlyId){
        var info=null;var fetched=false;var stats=null;var statsFetched=false;var words=null;
        if(onlyId==null){labels={};text={};icons={};energy=null;fittedMask=0;numericMask=0;}
        else{for(var i=0;i<selected.size();i+=1){var prior=selected[i];if(prior instanceof Complications.Id&&prior.equals(onlyId)){var key="custom"+(i+1);labels.remove(key);text.remove(key);icons.remove(key);fittedMask&=~(1<<i);numericMask&=~(1<<i);if(prior.getType()==23){energy=null;}}}}
        for(var i=0;i<selected.size();i+=1){var key="custom"+(i+1);var source=selected[i];if(source==null){continue;}
            if(onlyId!=null&&(!(source instanceof Complications.Id)||!source.equals(onlyId))){continue;}
            try{if(source instanceof Complications.Id){
                var earlier=-1;for(var n=0;n<i;n+=1){if(selected[n] instanceof Complications.Id&&source.equals(selected[n])){earlier=n;break;}}
                if(earlier>=0){var previous="custom"+(earlier+1);if(labels.hasKey(previous)){labels[key]=labels[previous];}if(text.hasKey(previous)){text[key]=text[previous];}if(icons.hasKey(previous)){icons[key]=icons[previous];}continue;}
                var item=null;try{item=provider!=null?provider.get(source):(api==null?Complications.getComplication(source):api.get(source));}catch(missing){}
                if(item!=null){var kind=source.getType();var needText=(customMask&(1<<i))!=0;
                    if(kind==23){if(item.value instanceof Number&&item.value>=0&&item.value<=100){energy=item.value;}
                        if(!needText){for(var j=i+1;j<selected.size();j+=1){if((customMask&(1<<j))!=0&&selected[j] instanceof Complications.Id&&source.equals(selected[j])){needText=true;break;}}}
                    }
                    if(needText){var label=item.shortLabel;if(!(label instanceof String)||label.equals("")){label=item.longLabel;}labels[key]=label instanceof String?label:"";
                        text[key]=kind==23?(energy==null?"—":energy.toString()):FieldFormat.complication(item,locale);
                        if(kind==0){try{var icon=item.getIcon();if(icon!=null){icons[key]=safeProviderIcon(icon);}}catch(noIcon){icons[key]=false;}}
                    }
                }item=null;
            }else if(source instanceof String){if(source.find("system:")==0){if(!statsFetched){stats=System.getSystemStats();statsFetched=true;}if(stats!=null){text[key]=FieldFormat.system(source,FieldCatalog.systemValue(stats,source),locale);var keys=FieldCatalog.systemKeys();var at=keys.indexOf(source);if(at>=0){if(words==null){words=FieldText.menu(locale);}labels[key]=words["system"][at];}}}
                else{if(!fetched){info=ActivityMonitor.getInfo();fetched=true;}if(info!=null){text[key]=FieldFormat.activity(source,FieldCatalog.activityValue(info,source));var keys=FieldCatalog.activityKeys();var at=keys.indexOf(source);if(at>=0){if(words==null){words=FieldText.menu(locale);}labels[key]=words["activity"][at];}}}}}
            catch(e){}
        }
    }
    // Optional provider graphics are managed references with bounded dimensions.
    // False requests a neutral marker; null means no icon was supplied.
    (:typecheck(false)) function safeProviderIcon(icon){
        if(!(icon instanceof Graphics.BitmapReference)){return false;}
        try{var w=icon.getWidth();var h=icon.getHeight();if(w<1||h<1||w>96||h>96){return false;}var transform=new Graphics.AffineTransform();transform.scale(18.0/w,18.0/h);return [icon,{:transform=>transform}];}catch(e){return false;}
    }
    function icon(role){return icons.hasKey(role)?icons[role]:null;}
    function active() as Boolean {return selected.size()>0;}
    function display(role) as String {return text.hasKey(role)?text[role] as String:"—";}
    function label(role) as String {return labels.hasKey(role)?labels[role] as String:"";}
    function roleBit(role){if(role.equals("custom1")){return 1;}if(role.equals("custom2")){return 2;}if(role.equals("custom3")){return 4;}if(role.equals("custom4")){return 8;}return 0;}
    function fitted(role){return (fittedMask&roleBit(role))!=0;}
    function numeric(role){return (numericMask&roleBit(role))!=0;}
    // Retain exactly the strings already fitted by the real destination font
    // and width. Remember the original value's font choice, since truncation
    // can remove non-numeric characters. A source/locale refresh replaces them.
    function keepFitted(role,name,value,isNumeric){var bit=roleBit(role);if(bit==0||(customMask&bit)==0){return;}if(labels.hasKey(role)){labels[role]=name;}if(text.hasKey(role)){text[role]=value;}fittedMask|=bit;if(isNumeric){numericMask|=bit;}else{numericMask&=~bit;}}
    function includes(id) as Boolean {for(var i=0;i<selected.size();i+=1){if(selected[i] instanceof Complications.Id&&selected[i].equals(id)){return true;}}return false;}
}
