import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;

// System watch-face configuration, backed by the same properties as Connect.
(:extendedCode, :typecheck(false))
module SettingsMenu {
    function locale() {return new SceneSettings(null).load().language;}
    function keys() {return ["Language","Field1","Field2","Field3","Field4","ClockColor","CountdownColor","Field1Color","Field2Color","Field3Color","Field4Color","FeedBaseUrl","LaunchReminders"];}
    function titles() {return SettingsMenuText.values(locale(),0);}
    function ids() {return [:i0,:i1,:i2,:i3,:i4,:i5,:i6,:i7,:i8,:i9,:i10,:i11,:i12];}
    function root(app) as [WatchUi.Views, WatchUi.InputDelegates] {
        var menu=new WatchUi.Menu2({:title=>"SpaceFox "+NativeVersion.BUILD});var names=titles();var symbols=ids();
        for(var i=0;i<names.size();i+=1){menu.addItem(new WatchUi.MenuItem(names[i],i==12?SettingsMenuText.reminderHelp(locale()):null,symbols[i],null));}
        // Rejected input never becomes accepted data. Explain a useful recovery
        // path in settings without adding a persistent home-screen timestamp.
        if(app.feed!=null&&app.feed.failure.equals("update-rejected")){
            var help=SettingsMenuText.rejected(locale());
            menu.addItem(new WatchUi.MenuItem(help[0],help[1],:updateRejected,null));
        }
        return [menu,new SettingsRootDelegate(app,menu)];
    }
    function labels(index) {return index==12?SettingsMenuText.reminderChoices(locale()):SettingsMenuText.values(locale(),index==0?1:index<=4?2:3);}
    function refreshRejection(menu) {
        var index=menu.findItemById(:updateRejected);
        if(index>=0){var help=SettingsMenuText.rejected(locale());var item=menu.getItem(index);item.setLabel(help[0]);item.setSubLabel(help[1]);}
    }
    function apply(app,key,value){Application.Properties.setValue(key,value);app.onSettingsChanged();}
}
(:extendedCode, :typecheck(false))
class SettingsRootDelegate extends WatchUi.Menu2InputDelegate {
    var app;var rootMenu;
    function initialize(owner,menu){Menu2InputDelegate.initialize();app=owner;rootMenu=menu;}
    function onSelect(item){var index=SettingsMenu.ids().indexOf(item.getId());if(index<0){return;}var key=SettingsMenu.keys()[index];
        if(index==11){var current=Application.Properties.getValue(key);WatchUi.pushView(new WatchUi.TextPicker(current instanceof String?current:""),new SettingsUrlDelegate(app),WatchUi.SLIDE_UP);return;}
        var menu=new WatchUi.Menu2({:title=>SettingsMenu.titles()[index]});var names=SettingsMenu.labels(index);var ids=SettingsMenu.ids();var selected=Application.Properties.getValue(key);
        for(var i=0;i<names.size();i+=1){var value=index==0&&i==5?36:i;menu.addItem(new WatchUi.MenuItem(names[i],selected==value?"*":null,ids[i],null));}
        WatchUi.pushView(menu,new SettingsChoiceDelegate(app,index,rootMenu),WatchUi.SLIDE_UP);
    }
    function onBack(){WatchUi.popView(WatchUi.SLIDE_DOWN);}
}
(:extendedCode, :typecheck(false))
class SettingsChoiceDelegate extends WatchUi.Menu2InputDelegate {
    var app;var index;var rootMenu;
    function initialize(owner,which,menu){Menu2InputDelegate.initialize();app=owner;index=which;rootMenu=menu;}
    function onSelect(item){var i=SettingsMenu.ids().indexOf(item.getId());if(i<0||i>=6||(index==12&&i>=2)){return;}SettingsMenu.apply(app,SettingsMenu.keys()[index],index==0&&i==5?36:i);if(index==0){var labels=SettingsMenu.titles();for(var n=0;n<labels.size();n+=1){rootMenu.getItem(n).setLabel(labels[n]);if(n==12){rootMenu.getItem(n).setSubLabel(SettingsMenuText.reminderHelp(SettingsMenu.locale()));}}SettingsMenu.refreshRejection(rootMenu);}WatchUi.popView(WatchUi.SLIDE_DOWN);}
    function onBack(){WatchUi.popView(WatchUi.SLIDE_DOWN);}
}
(:extendedCode, :typecheck(false))
class SettingsUrlDelegate extends WatchUi.TextPickerDelegate {
    var app;
    function initialize(owner){TextPickerDelegate.initialize();app=owner;}
    function onTextEntered(value,changed){if(changed){SettingsMenu.apply(app,"FeedBaseUrl",value);}return true;}
    function onCancel(){return true;}
}
