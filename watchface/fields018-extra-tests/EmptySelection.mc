import Toybox.Application;
import Toybox.Test;
(:test,:typecheck(false)) class EmptySelectionCallback { function changed(id){} }
(:test,:typecheck(false)) function fields018EmptyWatchSelection(logger){
    var previousId=Application.Storage.getValue("sf.field1");var previousProperty=Application.Properties.getValue("Field1");
    try{
        Application.Storage.deleteValue("sf.field1");Application.Properties.setValue("Field1",6);
        var settings=new SceneSettings({"Field1"=>Application.Properties.getValue("Field1"),"Field2"=>0,"Field3"=>5,"Field4"=>3});
        var selected=new SelectedFields();var callback=new EmptySelectionCallback();selected.start(settings.slots,callback.method(:changed));selected.read("en");
        Test.assert(FieldCatalog.saved(1)==null&&selected.display("custom1").equals("—")&&selected.subscribed.size()==0);
        Test.assert(Application.Properties.getValue("Field1")==6&&settings.slots[1].equals("steps")&&settings.slots[2].equals("battery")&&settings.slots[3].equals("stress"));
        selected.stop();logger.debug("EMPTY_WATCH_SELECTION dash=true phone6Preserved=true otherSlotsUntouched=true");return true;
    }finally{
        if(previousId==null){Application.Storage.deleteValue("sf.field1");}else{Application.Storage.setValue("sf.field1",previousId);}
        Application.Properties.setValue("Field1",previousProperty);
    }
}
