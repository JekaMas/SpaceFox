import Toybox.Application;
import Toybox.ActivityMonitor;
import Toybox.Complications;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;

(:test, :typecheck(false))
class FieldExample {
    var value;var unit;var kind;var shortLabel;var longLabel;
    function initialize(t,v,u){kind=t;value=v;unit=u;shortLabel="Example";longLabel="Example";}
    function getType(){return kind;}
}
(:test, :typecheck(false))
class FieldCallback {
    function initialize(){}
    function changed(id){}
}
(:test, :typecheck(false))
class MissingFieldProvider {
    var target;var missing=false;var calls=0;
    function initialize(id){target=id;}
    function get(id){if(id.equals(target)){calls+=1;if(missing){throw new Complications.ComplicationNotFoundException();}}return Complications.getComplication(id);}
}
(:test, :typecheck(false))
function fields018Format(logger){
    // Expected strings are independent API-unit examples, not derived from
    // the production calculations. Signed temperature and altitude are real.
    Test.assert(FieldFormat.complication(new FieldExample(13,25500,null),"en").equals("07:05"));
    Test.assert(FieldFormat.complication(new FieldExample(14,86400,null),"en").equals("—"));
    Test.assert(FieldFormat.complication(new FieldExample(21,90,null),"en").equals("90 min"));
    Test.assert(FieldFormat.complication(new FieldExample(16,101300.0,null),"en").equals("1013.0 hPa"));
    Test.assert(FieldFormat.complication(new FieldExample(15,-20.0,null),"en").equals("-20.0 m"));
    Test.assert(FieldFormat.complication(new FieldExample(38,-3.0,null),"en").equals("-3.0°C"));
    Test.assert(FieldFormat.complication(new FieldExample(26,"Maintaining",null),"en").equals("Maintaining"));
    Test.assert(FieldFormat.complication(new FieldExample(42,87,null),"en").equals("87"));
    Test.assert(FieldFormat.complication(new FieldExample(0,1260.0,1),"en").equals("1.3 km"));
    Test.assert(FieldFormat.complication(new FieldExample(0,72,"bpm"),"en").equals("72 bpm"));
    Test.assert(FieldFormat.complication(new FieldExample(null,72,"bpm"),"en").equals("72 bpm"));
    Test.assert(FieldFormat.complication(new FieldExample(8,0,null),"en").equals("Clear"));
    Test.assert(FieldFormat.complication(new FieldExample(8,3,null),"ru").equals("Дождь"));
    Test.assert(FieldFormat.complication(new FieldExample(8,53,null),"en").equals("—"));
    Test.assert(FieldFormat.complication(new FieldExample(8,null,null),"en").equals("—"));
    Test.assert(FieldFormat.activity("distance",123400).equals("1.2 km"));
    Test.assert(FieldFormat.activity("pushDistance",123400).equals("1.2 km"));
    Test.assert(FieldFormat.system("system:batteryInDays",2.5,"en").equals("2.5 d"));
    Test.assert(FieldFormat.system("system:charging",false,"en").equals("Disconnected"));
    Test.assert(FieldFormat.system("system:solarIntensity",-1,"en").equals("Not charging"));
    Test.assert(FieldFormat.system("system:solarIntensity",0,"en").equals("0%"));
    Test.assert(FieldFormat.system("system:solarIntensity",null,"en").equals("—"));
    logger.debug("FORMAT time, duration, pressure, signed, strings, type42, units, weather, null");return true;
}
(:test, :typecheck(false))
function fields018Settings(logger){
    var s=new SceneSettings({"Field1"=>0,"Field2"=>5,"Field3"=>6,"Field4"=>3});
    Test.assert(s.slots[0].equals("steps")&&s.slots[1].equals("battery")&&s.slots[2].equals("custom3")&&s.slots[3].equals("stress"));
    var invalid=new SceneSettings({"Field1"=>-1,"Field2"=>7});
    Test.assert(invalid.slots[0].equals("steps")&&invalid.slots[1].equals("energy"));
    logger.debug("SETTINGS legacy identities, custom slot and invalid defaults");return true;
}
(:test, :typecheck(false))
function fields018NativeInventoryAndPersistence(logger){
    var items=[];var offset=0;var page=FieldCatalog.page("en",offset);
    while(true){Test.assert(page.entries.size()<=6);for(var n=0;n<page.entries.size();n+=1){items.add(page.entries[n][1]);}if(!page.more){break;}offset+=6;Test.assert(offset<600);page=FieldCatalog.page("en",offset);}
    var id=null;var actual=Complications.getComplications();var item=actual.next();var count=0;var expected=0;
    while(item!=null){Test.assert(item instanceof Complications.Complication);if(item.complicationId!=null){count+=1;if(id==null){id=item.complicationId;}expected+=1;var found=false;for(var n=0;n<items.size();n+=1){if(items[n] instanceof Complications.Id&&items[n].equals(item.complicationId)){found=true;break;}}Test.assert(found);}item=actual.next();}
    Test.assert(count>0&&id!=null&&items.size()>=expected);
    for(var slot=1;slot<=4;slot+=1){Application.Storage.setValue("sf.field"+slot,id);Test.assert(FieldCatalog.saved(slot).equals(id));}
    var f=new SelectedFields();var cb=new FieldCallback();f.start(["custom1","custom2","custom3","custom4"],cb.method(:changed));
    Test.assert(f.selected.size()==4&&f.subscribed.size()<=1&&f.includes(id));f.read("en");
    Test.assert(f.display("custom1").equals(f.display("custom2"))&&f.display("custom2").equals(f.display("custom3"))&&f.display("custom3").equals(f.display("custom4")));
    f.stop();Test.assert(!f.active()&&f.subscribed.size()==0&&!f.callbackRegistered);
    var provider=new MissingFieldProvider(id);provider.missing=true;f.provider=provider;
    Application.Properties.setValue("Field1",6);Application.Properties.setValue("Field1",0);Application.Properties.setValue("Field1",6);
    f.start(["custom1","energy","custom3","custom4"],cb.method(:changed));f.read("en");
    Test.assert(f.display("custom1").equals("—")&&FieldCatalog.saved(1).equals(id)&&provider.calls==1&&f.subscribed.size()<=2);
    f.stop();provider.missing=false;provider.calls=0;f.start(["custom1","energy","custom3","custom4"],cb.method(:changed));f.read("en");
    Test.assert(FieldCatalog.saved(1).equals(id)&&f.display("custom1").equals(f.display("custom3"))&&provider.calls==1);f.stop();
    for(var slot=1;slot<=4;slot+=1){Test.assert(FieldCatalog.saved(slot).equals(id));Application.Storage.deleteValue("sf.field"+slot);}
    logger.debug("INVENTORY actual="+count+" catalog="+items.size()+" duplicates=4 subscriptions<=1 storedId=yes stop=yes");return true;
}

// Draw the actual selected provider text through the production renderer. The
// input label/value comes from the profile's iterator, not made-up display text.
(:test, :typecheck(false))
class Fields018Drawing extends SceneRenderer {
    var captured=[];var valueFonts=[];var inBounds=true;
    function initialize(p){SceneRenderer.initialize(p);}
    function text(dc,x,y,font,value,color,width,contour){
        var shown=fit(dc,value,font,width);var w=dc.getTextWidthInPixels(shown,font);var h=dc.getFontHeight(font);
        if(y==250||y==288||y==240||y==278){captured.add(shown);if(y==240||y==278){valueFonts.add(font);}var left=x-w/2.0-1;var right=x+w/2.0+1;var top=y-1;var bottom=y+h+1;
            var dx1=left-195;var dx2=right-195;var dy1=top-195;var dy2=bottom-195;
            inBounds=inBounds&&dx1*dx1+dy1*dy1<=195*195&&dx1*dx1+dy2*dy2<=195*195&&dx2*dx2+dy1*dy1<=195*195&&dx2*dx2+dy2*dy2<=195*195;}
        return SceneRenderer.text(dc,x,y,font,value,color,width,contour);
    }
}
(:test, :typecheck(false))
function fields018RenderRealSource(logger){
    var it=Complications.getComplications();var item=it.next();var id=null;
    while(item!=null){var kind=item.getType();if(item.complicationId!=null&&kind!=1&&kind!=2&&kind!=3&&kind!=23&&item.shortLabel!=null&&item.shortLabel.length()>0){id=item.complicationId;break;}item=it.next();}
    Test.assert(id!=null);
    for(var slot=1;slot<=4;slot+=1){Application.Storage.setValue("sf.field"+slot,id);}
    var source=new SelectedFields();var cb=new FieldCallback();source.start(["custom1","custom2","custom3","custom4"],cb.method(:changed));
    for(var language=0;language<2;language+=1){
        var locale=language==0?"en":"ru";source.read(locale);var fitness=new Fitness();fitness.selectedFields=source;
        var settings=new SceneSettings({"Language"=>language,"Field1"=>6,"Field2"=>6,"Field3"=>6,"Field4"=>6});
        var presentation=new LocalePresentation();var draw=new Fields018Drawing(presentation);
        draw.prepare(new SceneContext({"id"=>"ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b","rocket"=>"Starship V3","operator"=>"SpaceX","purpose"=>"Communications","site"=>"US · SpaceX Starbase, TX, USA"}),settings);
        var bitmap=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();draw.active(bitmap.getDc(),new ClockSnapshot("08:08","T- 49:02:03"),settings,{},fitness,0.0);
        var visibleValue=source.display("custom1");var selectedFont=draw.metricGlyphs(visibleValue)?draw.fonts["metric"]:draw.fonts["small"];
        Test.assert(draw.captured.size()==8&&draw.inBounds&&!visibleValue.equals("")&&draw.captured[1].equals(draw.fit(bitmap.getDc(),visibleValue,selectedFont,90)));
        Test.assert(draw.metricGlyphs("0")&&!draw.metricGlyphs("Cloudy")&&draw.metricGlyphs("0%"));
        if(draw.metricGlyphs(visibleValue)){Test.assert(draw.valueFonts.size()==4&&draw.valueFonts[0]==draw.fonts["metric"]);}
        logger.debug("RENDER locale="+locale+" provider="+source.label("custom1")+" value="+draw.captured[1]+" fields=4 bounds=true numericMetric=true");
    }
    source.stop();for(var slot=1;slot<=4;slot+=1){Application.Storage.deleteValue("sf.field"+slot);}return true;
}
(:test, :typecheck(false))
function fields018PrimaryLabels(logger){
    var keys=FieldCatalog.activityKeys();var locales=["en","ru","de","fr","es"];
    for(var i=0;i<locales.size();i+=1){var labels=FieldCatalog.activityLabels(locales[i]);Test.assert(labels.size()==keys.size());for(var j=0;j<labels.size();j+=1){Test.assert(labels[j] instanceof String&&labels[j].length()>0);}Test.assert(FieldCatalog.systemLabels(locales[i]).size()==FieldCatalog.systemKeys().size());}
    logger.debug("PRIMARY labels locales=5 activity="+keys.size());return true;
}

(:test, :typecheck(false))
function fields018SameSlotReplacement(logger){
    var it=Complications.getComplications();var item=it.next();var first=null;var second=null;
    while(item!=null){var kind=item.getType();if(item.complicationId!=null&&kind!=1&&kind!=2&&kind!=3&&kind!=23){if(first==null){first=item.complicationId;}else if(!first.equals(item.complicationId)){second=item.complicationId;break;}}item=it.next();}
    Test.assert(first!=null&&second!=null&&System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER);
    Application.Storage.setValue("sf.field1",first);Application.Properties.setValue("Field1",6);
    var settings=new SceneSettings({"Field1"=>6,"Field2"=>0,"Field3"=>5,"Field4"=>3});
    var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));view.setSettings(settings);view.onShow();view.onExitSleep();view.queueResumeAfterFrame();view.stopResume();view.resumeAfterFrame();
    Test.assert(view.canForegroundWork()&&view.selectedFields.includes(first));
    Application.Storage.setValue("sf.field1",second);view.setSettings(new SceneSettings({"Field1"=>6,"Field2"=>0,"Field3"=>5,"Field4"=>3}));
    Test.assert(view.settings.slots[0].equals("custom1")&&view.selectedFields.includes(second)&&!view.selectedFields.includes(first));
    var expected=FieldFormat.complication(Complications.getComplication(second),"en");Test.assert(view.fitness.display(view.values,"custom1").equals(expected));
    view.stopFitness();view.admissionPending=true;view.values["energy"]=1234;view.refreshFitness();view.fieldsChanged(second);Test.assert(!view.selectedFields.active()&&view.fitnessTimer==null&&view.values["energy"]==1234);view.admissionPending=false;view.refreshFitness();Test.assert(view.selectedFields.active());
    view.onEnterSleep();Test.assert(!view.selectedFields.active());view.onHide();Application.Storage.deleteValue("sf.field1");
    logger.debug("SAME_SLOT property=6 unchanged=true source=A->B immediate=true pendingNoRead=true resume=true lowStopped=true");return true;
}

// Independent list of official Info symbols; null values do not remove a
// supported symbol. The expected key mapping is deliberately separate from
// FieldCatalog.supported and its choice-generation code.
(:test, :typecheck(false)) module FieldsCapabilityOracle {
 function activity(info,key){
  if(key.equals("distance")){return info has :distance;}if(key.equals("stepGoal")){return info has :stepGoal;}
  if(key.equals("floorsClimbedGoal")){return info has :floorsClimbedGoal;}if(key.equals("floorsDescended")){return info has :floorsDescended;}
  if(key.equals("metersClimbed")){return info has :metersClimbed;}if(key.equals("metersDescended")){return info has :metersDescended;}
  if(key.equals("moveBarLevel")){return info has :moveBarLevel;}if(key.equals("activeMinutesWeekGoal")){return info has :activeMinutesWeekGoal;}
  if(key.equals("activeMinutesDayTotal")||key.equals("activeMinutesDayModerate")||key.equals("activeMinutesDayVigorous")){return info has :activeMinutesDay;}
  if(key.equals("activeMinutesWeekTotal")||key.equals("activeMinutesWeekModerate")||key.equals("activeMinutesWeekVigorous")){return info has :activeMinutesWeek;}
  if(key.equals("pushes")){return info has :pushes;}if(key.equals("pushGoal")){return info has :pushGoal;}if(key.equals("pushDistance")){return info has :pushDistance;}
  if(key.equals("timeToRecovery")){return info has :timeToRecovery;}if(key.equals("respirationRate")){return info has :respirationRate;}
  if(key.equals("stressScore")){return info has :stressScore;}if(key.equals("floorsClimbed")){return info has :floorsClimbed;}return false;
 }
 function system(stats,key,types){if(key.equals("system:batteryInDays")){return stats has :batteryInDays;}if(key.equals("system:charging")){return stats has :charging;}if(key.equals("system:solarIntensity")){return types.indexOf(37)<0&&stats has :solarIntensity&&stats.solarIntensity!=null;}return false;}
}
(:test, :typecheck(false)) class FieldsEmptyInfo {var stepGoal=null;}
(:test, :typecheck(false)) class FieldsDeviceStats {var batteryInDays=2.5;var charging=false;var solarIntensity=null;}
(:test, :typecheck(false))
function fields018CapabilityInventory(logger){
    var visible=[];var offset=0;var page=FieldCatalog.page("en",0);
    while(true){for(var i=0;i<page.entries.size();i+=1){visible.add(page.entries[i][1]);}if(!page.more){break;}offset+=6;page=FieldCatalog.page("en",offset);}
    var it=Complications.getComplications();var item=it.next();var types=[];var nativeCount=0;var paged=0;var late=false;
    while(item!=null){var id=item.complicationId;var kind=item.getType();if(id!=null){nativeCount+=1;types.add(kind);
        var found=false;for(var i=0;i<visible.size();i+=1){if(visible[i] instanceof Complications.Id&&id.equals(visible[i])){found=true;break;}}Test.assert(found);paged+=1;if(kind==42){late=true;}
    }item=it.next();}
    Test.assert(nativeCount==paged);
    var info=ActivityMonitor.getInfo();var keys=FieldCatalog.activityKeys();var activityCount=0;var activityNames=[];
    if(info!=null){for(var i=0;i<keys.size();i+=1){var key=keys[i];var duplicate=(key.equals("activeMinutesWeekTotal")&&types.indexOf(5)>=0)||(key.equals("floorsClimbed")&&types.indexOf(4)>=0)||(key.equals("pushes")&&types.indexOf(40)>=0)||(key.equals("timeToRecovery")&&types.indexOf(21)>=0)||(key.equals("respirationRate")&&types.indexOf(36)>=0);var expected=FieldsCapabilityOracle.activity(info,key)&&!duplicate;Test.assert((visible.indexOf(key)>=0)==expected);if(expected){activityCount+=1;activityNames.add(key);}}}
    var stats=System.getSystemStats();var systemKeys=FieldCatalog.systemKeys();var systemCount=0;var systemNames=[];
    for(var i=0;i<systemKeys.size();i+=1){var expected=FieldsCapabilityOracle.system(stats,systemKeys[i],types);Test.assert((visible.indexOf(systemKeys[i])>=0)==expected);if(expected){systemCount+=1;systemNames.add(systemKeys[i]);}}
    var empty=new FieldsEmptyInfo();Test.assert(FieldCatalog.supported(empty,"stepGoal")&&FieldCatalog.activityValue(empty,"stepGoal")==null);
    var fake=new FieldsDeviceStats();Test.assert(FieldCatalog.systemSupported(fake,"system:batteryInDays",[])&&FieldCatalog.systemSupported(fake,"system:charging",[])&&!FieldCatalog.systemSupported(fake,"system:solarIntensity",[]));
    fake.solarIntensity=-1;Test.assert(FieldCatalog.systemSupported(fake,"system:solarIntensity",[])&&!FieldCatalog.systemSupported(fake,"system:solarIntensity",[37]));
    logger.debug("ACTIVITY_KEYS "+activityNames);logger.debug("SYSTEM_KEYS "+systemNames);logger.debug("CAPABILITY native="+nativeCount+" paged="+paged+" activity="+activityCount+" system="+systemCount+" availableNullSelectable=true solarNullUnsupported=true solarNegativeSupported=true type42="+late);return true;
}
