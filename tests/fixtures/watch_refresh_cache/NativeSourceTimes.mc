import Toybox.Lang;

(:typecheck(false))
function nativeDigits(value,start,end){
    if(start<0||end>value.length()||start>=end){throw new Lang.InvalidValueException("Invalid ISO digits");}
    var text=value.substring(start,end);var chars=text.toCharArray();for(var i=0;i<chars.size();i+=1){var n=chars[i].toNumber();if(n<48||n>57){throw new Lang.InvalidValueException("Invalid ISO digits");}}return text.toNumber();
}
(:typecheck(false))
function nativeCivilDay(y,m,d){
    var leap=y%4==0&&(y%100!=0||y%400==0);var days=[31,leap?29:28,31,30,31,30,31,31,30,31,30,31];if(y<1||m<1||m>12||d<1||d>days[m-1]){throw new Lang.InvalidValueException("Invalid UTC date");}
    y-=m<=2?1:0;var era=y/400;var year=y-era*400;var month=m+(m>2?-3:9);var ordinal=(153*month+2)/5+d-1;return (era*146097+year*365+year/4-year/100+ordinal-719468).toLong();
}
(:typecheck(false))
function nativeUtcDay(value){
    if(!(value instanceof String)||value.length()!=10||!value.substring(4,5).equals("-")||!value.substring(7,8).equals("-")){throw new Lang.InvalidValueException("Invalid UTC date");}
    var year=nativeDigits(value,0,4);if(year>9999){throw new Lang.InvalidValueException("Invalid UTC year");}return nativeCivilDay(year,nativeDigits(value,5,7),nativeDigits(value,8,10));
}
(:typecheck(false)) function nativeIsoChar(value,index){return index<value.length()?value.substring(index,index+1):"";}
(:typecheck(false)) function nativeIsoDigit(value,index){var c=nativeIsoChar(value,index);return !c.equals("")&&"0123456789".find(c)!=null;}
(:typecheck(false)) function nativeWeekStart(year){var jan4=nativeCivilDay(year,1,4);var weekday=(jan4+3)%7;if(weekday<0){weekday+=7;}return jan4-weekday;}
// Python3.12 datetime.fromisoformat date forms: extended/basic calendar and ISO
// week, optional week day (Monday otherwise). UTC's supported year stays1..9999.
(:typecheck(false))
function nativeIsoDate(value){
    var y=nativeDigits(value,0,4);if(y<1){throw new Lang.InvalidValueException("Invalid ISO year");}var dashed=nativeIsoChar(value,4).equals("-");var index=dashed?5:4;
    if(nativeIsoChar(value,index).equals("W")){var week=nativeDigits(value,index+1,index+3);index+=3;var day=1;if(dashed&&nativeIsoChar(value,index).equals("-")&&!nativeIsoDigit(value,index+2)){day=nativeDigits(value,index+1,index+2);index+=2;}else if(!dashed&&nativeIsoDigit(value,index)){var stop=index+1;while(nativeIsoDigit(value,stop)){stop+=1;}if(stop==index+1||(stop-index)%2==0){day=nativeDigits(value,index,index+1);index+=1;}}var start=nativeWeekStart(y);var next=nativeWeekStart(y+1);var actual=start+(week-1)*7+day-1;if(week<1||week>53||day<1||day>7||actual>=next||actual< -719162l||actual>2932896l){throw new Lang.InvalidValueException("Invalid ISO week");}return [actual,index];}
    var m=nativeDigits(value,index,index+2);index+=2;if(dashed){if(!nativeIsoChar(value,index).equals("-")){throw new Lang.InvalidValueException("Invalid ISO date");}index+=1;}var d=nativeDigits(value,index,index+2);return [nativeCivilDay(y,m,d),index+2];
}
// The producer uses Python3.12's actual lexical behavior, including one
// ignored local-time trailing character before the timezone. Offset parsing
// does not have that allowance. Fractions truncate at six digits.
(:typecheck(false))
function nativeIsoTime(value,index,end,offset){
    var units=[0,0,0];var micros=0;var colon=false;var pairs=0;
    for(var part=0;part<3;part+=1){
        if(part>0){var remaining=end-index;if(remaining<=1){if(offset&&remaining>0){throw new Lang.InvalidValueException("Invalid offset tail");}index=end;break;}if([".",","].indexOf(nativeIsoChar(value,index))>=0){break;}if(part==1){colon=nativeIsoChar(value,index).equals(":");}if(colon){if(!nativeIsoChar(value,index).equals(":")){throw new Lang.InvalidValueException("Invalid time separator");}index+=1;}}
        if(index+2>end){throw new Lang.InvalidValueException("Invalid time digits");}units[part]=nativeDigits(value,index,index+2);index+=2;pairs+=1;
    }
    if(!offset&&end-index==1){index=end;}
    if(index<end){var unmarked=pairs==3&&!colon&&end-index>1&&nativeIsoDigit(value,index);if(!unmarked){if([".",","].indexOf(nativeIsoChar(value,index))<0){throw new Lang.InvalidValueException("Invalid fraction separator");}index+=1;}var count=0;while(count<6&&index<end){micros=micros*10+nativeDigits(value,index,index+1);count+=1;index+=1;}if(count==0){throw new Lang.InvalidValueException("Invalid ISO fraction");}while(count<6){micros*=10;count+=1;}if(offset){while(index<end){nativeDigits(value,index,index+1);index+=1;}}else{index=end;}}
    var seconds=units[0]*3600+units[1]*60+units[2];if(offset?seconds>=86400:units[0]>23||units[1]>59||units[2]>59){throw new Lang.InvalidValueException("Invalid ISO time");}return [seconds,micros,index];
}
(:typecheck(false))
function nativeIsoExpanded(value){
    // The producer replaces EVERY Z before finding the date/time boundary.
    // A Z separator can therefore become '+' plus part of the local time.
    // At most two replacements can parse: one date separator and one zone;
    // any third introduces another sign inside the sole offset production.
    var first=value.find("Z");if(first==null){return value;}var second=null;
    for(var i=first+1;i<value.length();i+=1){if(nativeIsoChar(value,i).equals("Z")){if(second!=null){throw new Lang.InvalidValueException("Multiple ISO zones");}second=i;}}
    return value.substring(0,first)+"+00:00"+(second==null?value.substring(first+1,value.length()):value.substring(first+1,second)+"+00:00"+value.substring(second+1,value.length()));
}
(:typecheck(false))
function nativeSourceIso(value,seconds,subsecond){
    if(value==null){return true;}if(!(value instanceof String)||seconds==null){return false;}
    try{
        value=nativeIsoExpanded(value);var date=nativeIsoDate(value);var index=date[1];if(index>=value.length()){return false;}var start=index+1;index=start;while(index<value.length()&&["+","-"].indexOf(nativeIsoChar(value,index))<0){index+=1;}if(index==value.length()){return false;}var time=nativeIsoTime(value,start,index,false);var sign=nativeIsoChar(value,index);var offsetSeconds=0;var offsetMicros=0;
        var offset=nativeIsoTime(value,index+1,value.length(),true);if(offset[2]!=value.length()){return false;}var direction=sign.equals("-")?-1:1;offsetSeconds=offset[0]*direction;offsetMicros=offset[0]==0?0:offset[1]*direction;
        var utc=date[0]*86400+time[0]-offsetSeconds;var micro=time[1]-offsetMicros;if(micro<0){utc-=1;}else if(micro>=1000000){utc+=1;}
        return utc>= -62135596800l&&utc<=253402300799l&&utc==seconds&&(subsecond==null||time[1]==subsecond);
    }catch(e){return false;}
}
