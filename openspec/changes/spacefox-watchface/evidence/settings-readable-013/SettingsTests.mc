import Toybox.Application;import Toybox.Lang;import Toybox.Test;import Toybox.WatchUi;
(:test,:typecheck(false)) class PeerSettingsOwner {var feed;function initialize(){feed=new NativeCache("https://jekamas.github.io/SpaceFox",null);feed.failure="update-rejected";}function onSettingsChanged(){}}
(:test,:typecheck(false)) function peerSettingsFiveLocales(logger){
 var names=["Feed rejected","Ошибка данных","Daten abgelehnt","Données refusées","Datos rechazados"];var helps=["Check URL / update","URL / обновить","URL / App-Update","URL / mise à jour","URL / actualizar"];
 for(var i=0;i<5;i+=1){Application.Properties.setValue("Language",i);var owner=new PeerSettingsOwner();var menu=SettingsMenu.root(owner)[0];var item=menu.getItem(12);Test.assertEqual(item.getId(),:updateRejected);Test.assertEqual(item.getLabel(),names[i]);Test.assertEqual(item.getSubLabel(),helps[i]);logger.debug("WARNING locale="+i+" title="+item.getLabel()+" recovery="+item.getSubLabel());}
 Application.Properties.setValue("Language",0);return true;
}
