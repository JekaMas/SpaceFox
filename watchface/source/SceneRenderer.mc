import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Math;
import Toybox.WatchUi;

class SceneRenderer {
    var presentation as LocalePresentation;
    var fonts as Dictionary<String, Graphics.FontType>;
    var model as NativeModel or Null;
    var icons as Dictionary<String,Graphics.BitmapType>;
    var marker as Graphics.BitmapType;
    var art as Graphics.BitmapType or Null;
    var map as Graphics.BitmapType or Null;
    var aodMap as Graphics.BitmapType or Null=null;
    var aodResource as ResourceId or Null=null;
    var aodPin as Boolean=false;var aodPinX as Number=335;var aodPinY as Number=165;
    var mapScale as Dictionary;
    var pin as Boolean = false;
    var pinX as Number = 335; var pinY as Number = 165;
    var fullContext as SceneContext or Null;
    var downloaded as NativeVisualRenderer or Null=null;
    var resourceLoads as Number = 0;
    var prepared as Boolean = false;
    (:extendedCode)
    function initialize(owner as LocalePresentation or Null) {
        presentation=owner==null?new LocalePresentation():owner;
        fonts = {};icons={};var transform=new Graphics.AffineTransform();transform.scale(2.0,2.0);mapScale={:transform=>transform,:filterMode=>Graphics.FILTER_MODE_BILINEAR};
        marker=load(Rez.Drawables.LaunchMarker) as Graphics.BitmapType;
        fonts["time"] = load(Rez.Fonts.Time80) as Graphics.FontType;
        fonts["metric"] = load(Rez.Fonts.Metric32) as Graphics.FontType;
        fonts["label"] = presentation.label as Graphics.FontType;
        fonts["nameSmall"] = presentation.latinSmall as Graphics.FontType;
        fonts["small"] = presentation.small as Graphics.FontType;
        fonts["count"] = presentation.count as Graphics.FontType;
        model = null; art = null; map = null;
    }
    (:extendedCode)
    function load(id as ResourceId) as WatchUi.Resource { resourceLoads += 1; return WatchUi.loadResource(id); }
    (:extendedCode)
    function prepare(context as SceneContext or Null, settings as SceneSettings) as Void {
        presentation.prepare(settings.language);fonts["label"]=presentation.label as Graphics.FontType;fonts["small"]=presentation.small as Graphics.FontType;fonts["count"]=presentation.count as Graphics.FontType;
        var selected={} as Dictionary<String,Graphics.BitmapType>;
        for(var i=0;i<settings.slots.size();i+=1){var role=settings.slots[i];if(NativeAssets.icons.hasKey(role)&&!selected.hasKey(role)){selected[role]=icons.hasKey(role)?(icons[role] as Graphics.BitmapType):load(NativeAssets.icons[role] as ResourceId) as Graphics.BitmapType;}}
        icons=selected;
        // Unchanged model and qualified point retain the same bitmaps even if
        // metadata/settings were refreshed or the accepted scene woke again.
        var same=prepared && ((context==null && fullContext==null) ||
            (context!=null && fullContext!=null && context.modelId.equals(fullContext.modelId) && samePoint(context.point,fullContext.point)));
        fullContext=context;
        if(same){return;}
        prepared=true;
        // The bundled view is geographical backdrop only: no location marker is
        // shown unless the selected launch supplies a qualified matching point.
        model = null; art = null; map = null; aodMap=null; aodResource=null; pin = false;aodPin=false;
        var mapResource=Rez.Drawables.MapView0;
        if (context == null) { aodResource=NativeAssets.aodResource(0); map=load(mapResource) as Graphics.BitmapType; art = load(Rez.Drawables.Art_unknown) as Graphics.BitmapType; return; }
        var id = NativeAssets.models.hasKey(context.modelId) ? context.modelId : "generic";
        model = NativeAssets.models[id] as NativeModel; art = load(id.equals("generic") ? Rez.Drawables.Art_unknown : (model as NativeModel).resource) as Graphics.BitmapType;
        if (context.point != null) {
            for (var i = 0; i < NativeAssets.mapCount; i += 1) {
                var view = NativeAssets.mapAt(i) as NativeMap;
                var point=context.point as Array<Numeric>;
                // These bitmaps use D3's rotated equirectangular projection.
                // Admit only points within a quarter degree of the bitmap's
                // actual center, where its site remains legible beside time.
                var lonDelta=point[0]-view.longitude;var latDelta=point[1]-view.latitude;
                if (lonDelta>=-0.25 && lonDelta<=0.25 && latDelta>=-0.25 && latDelta<=0.25) {
                    var projected=projectSite(point,view.longitude,view.latitude);
                    pinX=projected[0];pinY=projected[1];aodPinX=pinX;aodPinY=pinY;
                    mapResource=view.resource;aodResource=NativeAssets.aodResource(i);pin = true;aodPin=true;break;
                }
            }
            if(aodResource==null){
                var point=context.point as Array<Numeric>;
                var coordinates=NativeAssets.aodCoordinates;
                for(var i=0;i<coordinates.size()/8;i+=1){var longitude=aodCoordinate(coordinates,i*8);var latitude=aodCoordinate(coordinates,i*8+4);var lon=point[0]-longitude;var lat=point[1]-latitude;
                    if(lon>=-0.25&&lon<=0.25&&lat>=-0.25&&lat<=0.25){var projected=projectSite(point,longitude,latitude);aodPinX=projected[0];aodPinY=projected[1];pinX=aodPinX;pinY=aodPinY;pin=true;mapResource=NativeAssets.extraMapResource(i);aodPin=true;aodResource=NativeAssets.aodResource(54+i);break;}}
            }
        }
        if(aodResource==null){aodResource=NativeAssets.aodResource(0);}
        map=load(mapResource) as Graphics.BitmapType;
    }
    function samePoint(a as Array<Numeric> or Null,b as Array<Numeric> or Null) as Boolean {
        if(a==null||b==null){return a==null&&b==null;}
        return a.size()==2&&b.size()==2&&a[0]==b[0]&&a[1]==b[1];
    }
    function aodCoordinate(data as ByteArray,offset as Number) as Float {return ((data[offset]<<24)|(data[offset+1]<<16)|(data[offset+2]<<8)|data[offset+3])/1000000.0;}
    function projectSite(point as Array<Numeric>,longitude as Numeric,latitude as Numeric) as Array<Number> {
        var rad=0.017453292519943295;var lambda=(point[0]-longitude)*rad;var phi=point[1]*rad;var delta=-latitude*rad;
        var x=Math.cos(lambda)*Math.cos(phi);var y=Math.sin(lambda)*Math.cos(phi);var z=Math.sin(phi);
        return [(335+145*Math.atan2(y,x*Math.cos(delta)-z*Math.sin(delta))+0.5).toNumber(),(165-145*Math.asin(z*Math.cos(delta)+x*Math.sin(delta))+0.5).toNumber()];
    }
    (:extendedCode) function fit(dc as Graphics.Dc, text as String, font as Graphics.FontType, width as Number) as String {
        return presentation.fit(dc,text,font,width);
    }
    (:extendedCode) function text(dc as Graphics.Dc, x as Numeric, y as Numeric, font as Graphics.FontType, value as String, color as Number, width as Number, contour as Number) as String {
        var content = fit(dc, value, font, width);
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_TRANSPARENT);
        if (contour > 0) {
            for (var dx = -contour; dx <= contour; dx += 1) {
                for (var dy = -contour; dy <= contour; dy += 1) {
                    if (dx != 0 || dy != 0) { dc.drawText(x+dx, y+dy, font, content, Graphics.TEXT_JUSTIFY_CENTER); }
                }
            }
        }
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.drawText(x, y, font, content, Graphics.TEXT_JUSTIFY_CENTER);
        return content;
    }
    (:extendedCode, :typecheck(false)) function active(dc as Graphics.Dc, current as ClockSnapshot, settings as SceneSettings, values as Dictionary<String, Number or Null>, fitness as Fitness, progress as Float) as Void {
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK); dc.clear();
        var rich=downloaded instanceof NativeSfrRenderer?downloaded:null;
        // A complete selected scene owns its validated map; the bundled map
        // remains the fallback while that scene is absent or incomplete.
        var selectedMap=rich!=null && rich.mapBitmap!=null;
        if(selectedMap){dc.drawBitmap(0,0,rich.mapBitmap);}else if(map!=null){dc.drawBitmap2(0,0,map,mapScale);}
        var context = fullContext;
        if (context != null) {
            // Match the existing unavailable health marker without changing the
            // accepted context: absent company/mission stay empty in storage.
            var operatorText=context.operator.equals("")?(context.operatorShort.equals("")?"—":context.operatorShort):context.operator;
            var purposeText=context.purpose.equals("")?"—":presentation.mission(context.purpose);
            var naturalOperator=dc.getTextWidthInPixels(operatorText,fonts["nameSmall"] as Graphics.FontType);
            if(!context.operatorShort.equals("")&&!context.operator.equals("")&&naturalOperator>(context.rocket.equals("")?238:100)){
                operatorText=context.operatorShort;naturalOperator=dc.getTextWidthInPixels(operatorText,fonts["nameSmall"] as Graphics.FontType);
            }
            var operatorBudget=context.rocket.equals("")?238:(naturalOperator<100?naturalOperator:100);
            var rocketBudget=238-operatorBudget-(context.rocket.equals("")?0:16);
            var rocketTitle=fit(dc,context.rocket,fonts["label"] as Graphics.FontType,rocketBudget);
            var operatorTitle=fit(dc,operatorText,fonts["nameSmall"] as Graphics.FontType,operatorBudget);
            var rocketWidth=dc.getTextWidthInPixels(rocketTitle,fonts["label"] as Graphics.FontType);
            var operatorWidth=dc.getTextWidthInPixels(operatorTitle,fonts["nameSmall"] as Graphics.FontType);
            var gap=rocketTitle.equals("")||operatorTitle.equals("")?0:16;
            var left=195-(rocketWidth+operatorWidth+gap)/2;
            text(dc,left+rocketWidth/2,43,fonts["label"] as Graphics.FontType,rocketTitle,0xD8E2ED,238,1);
            if(gap>0){text(dc,left+rocketWidth+8,47,fonts["nameSmall"] as Graphics.FontType,"·",0x96B8C9,16,1);}
            text(dc,left+rocketWidth+gap+operatorWidth/2,47,fonts["nameSmall"] as Graphics.FontType,operatorTitle,0xD4DFEB,238,1);
            text(dc,195,70,(fonts["small"] as Graphics.FontType),purposeText,0xD4DFEB,282,1);
            var ascent = progress > 0 && progress < 1 ? (progress * 9).toNumber() : 0;
            if(downloaded!=null&&downloaded.bitmap!=null){downloaded.draw(dc,progress,ascent);}else{dc.drawBitmap(22,118-ascent,art as Graphics.BitmapType);}
            // Flags and operator marks are never attached to the rocket.
            if (progress > 0 && progress < 1) {
                dc.setColor(0xF7AE4F,Graphics.COLOR_TRANSPARENT); dc.fillPolygon([[45,239-ascent],[53,239-ascent],[49,248-ascent]]);
            }
            var flag=rich==null?null:rich.siteCountryBitmap;
            var footerBudget=flag==null?242:216;
            var footerFont=dc.getTextWidthInPixels(context.site,fonts["label"] as Graphics.FontType)>footerBudget?fonts["nameSmall"] as Graphics.FontType:fonts["label"] as Graphics.FontType;
            var footer=fit(dc,context.site,footerFont,footerBudget);
            var footerWidth=dc.getTextWidthInPixels(footer,footerFont);
            var flagWidth=flag==null?0:26;
            var footerLeft=195-(footerWidth+flagWidth)/2;
            if(flag!=null){dc.drawBitmap(footerLeft,325,flag as Graphics.BitmapType);}
            text(dc,footerLeft+flagWidth+footerWidth/2,319,footerFont,footer,0xD4DFEB,footerBudget,1);
        }
        if(context==null && art!=null){dc.drawBitmap(22,118,art as Graphics.BitmapType);}
        if(current.localCalendar!=null){text(dc,195,95,presentation.calendarFont as Graphics.FontType,presentation.calendar(current.localCalendar as Array<Number>),0xD4DFEB,200,1);}
        text(dc,195,109,(fonts["time"] as Graphics.FontType),current.localTime,settings.clockColor,250,1);
        current.rescheduled=current.rescheduled||context!=null&&context.rescheduled;
        current.sourceHold=current.sourceHold||context!=null&&context.sourceHold;
        var color = SceneAod.countdownColor(current,settings);
        var countdownLabel=current.countdown;
        var countFont = dc.getTextWidthInPixels(countdownLabel,fonts["count"] as Graphics.FontType) > 275 ? (fonts["small"] as Graphics.FontType) : (fonts["count"] as Graphics.FontType);
        var shown = text(dc,195,202,countFont,countdownLabel,color,275,1);
        if ((current.stale || context != null && context.stale)) { underline(dc,195,241,dc.getTextWidthInPixels(shown,countFont),color); }
        for (var i = 0; i < 4; i += 1) {
            var role = settings.slots[i];
            var label=metricText(fitness,values,role,settings);
            var rowTop=i<2?244:282;
            if(role.find("custom")==0){
                var small=fonts["small"] as Graphics.FontType;var metric=fonts["metric"] as Graphics.FontType;
                var customLeft=i%2==0?55:207;var name=fit(dc,fitness.fieldLabel(role),small,35);
                var customIcon=fitness.fieldIcon(role);if(customIcon!=null){try{dc.drawBitmap2(customLeft-25,rowTop+5,customIcon[0],customIcon[1]);}catch(e){}}
                text(dc,customLeft+17,rowTop+6,small,name,settings.fieldColors[i],35,1);
                var valueFont=metricGlyphs(label)?metric:small;
                text(dc,customLeft+80,rowTop+(valueFont==metric?-4:6),valueFont,label,settings.fieldColors[i],90,1);
            }else{
                label=fit(dc,label,fonts["metric"] as Graphics.FontType,128);
                var width=dc.getTextWidthInPixels(label,fonts["metric"] as Graphics.FontType);
                var left=i%2==0?55:335-width;if(i==2&&role.equals("battery")){left+=18;}var y=rowTop-4;
                icon(dc,left-(role.equals("battery")?31:25),rowTop+(role.equals("battery")?2:5),role);
                text(dc,left+width/2,y,fonts["metric"] as Graphics.FontType,label,settings.fieldColors[i],128,1);
            }
        }
        if(selectedMap){if(rich.scene!=null && rich.scene["position"]!=null){dc.drawBitmap(321,151,marker);}}
        else if(pin){dc.drawBitmap(pinX-14,pinY-14,marker);}
    }
    // Metric32 contains digits, percent and punctuation only. Provider strings
    // and units use the locale-capable font instead of missing bitmap glyphs.
    (:extendedCode) function metricGlyphs(value as String) as Boolean {
        for(var i=0;i<value.length();i+=1){if("0123456789.,% —…".find(value.substring(i,i+1) as String)==null){return false;}}
        return true;
    }
    (:extendedCode) function metricText(fitness as Fitness,values as Dictionary<String,Number or Null>,role as String,settings as SceneSettings) as String {
        return presentation.metric(fitness,values,role);
    }
    (:extendedCode) function underline(dc as Graphics.Dc,x as Numeric,y as Numeric,width as Number,color as Number) as Void {
        dc.setColor(color,Graphics.COLOR_TRANSPARENT);
        for (var i = x-width/2; i <= x+width/2; i += 5) { dc.fillCircle(i,y,1); }
    }
    (:extendedCode) function icon(dc as Graphics.Dc,x as Numeric,y as Numeric,role as String) as Void {
        if(icons.hasKey(role)){dc.drawBitmap(x,y,icons[role] as Graphics.BitmapType);}
    }
    (:extendedCode) function prepareAod() as Void {if(!fonts.hasKey("aod")){fonts["aod"]=load(Rez.Fonts.Aod40) as Graphics.FontType;}if(aodMap==null && aodResource!=null){aodMap=load(aodResource as ResourceId) as Graphics.BitmapType;}}
    (:extendedCode) function releaseAod() as Void {aodMap=null;fonts.remove("aod");}
    (:extendedCode, :typecheck(false)) function aod(dc as Graphics.Dc,current as ClockSnapshot,minute as Number or Long,settings as SceneSettings) as Void {
        current.rescheduled=current.rescheduled||fullContext!=null&&fullContext.rescheduled;
        current.sourceHold=current.sourceHold||fullContext!=null&&fullContext.sourceHold;
        current.stale=current.stale||fullContext!=null&&fullContext.stale;
        var rich=downloaded instanceof NativeSfrRenderer?downloaded:null;
        var selected=rich!=null && (rich.mapOutline!=null||(rich.bundledOutline&&aodPin&&aodResource!=null)) && rich.scene!=null && rich.scene["position"]!=null;
        // The current finite fixed-site catalog has full outlines at matching
        // centers. Prefer that shape even when the selected scene is READY;
        // unmatched future locations retain their own decoded raster outline.
        var bundled=aodMap!=null && (aodPin||!selected);
        SceneAod.draw(dc,current,minute,presentation,fonts["aod"] as Graphics.FontType,settings,bundled?aodMap:(selected?rich.mapOutline:null),bundled?aodPin:selected,bundled?aodPinX:335,bundled?aodPinY:165);
    }
}

// LOW rendering uses the same clock snapshot as the active scene. The caller
// owns the once-per-minute guard; fonts/dictionary are prepared outside redraw.
module SceneAod {
    (:extendedCode) function project(point,longitude,latitude) {var rad=0.017453292519943295;var lambda=(point[0]-longitude)*rad;var phi=point[1]*rad;var delta=-latitude*rad;var x=Math.cos(lambda)*Math.cos(phi);var y=Math.sin(lambda)*Math.cos(phi);var z=Math.sin(phi);return [(335+145*Math.atan2(y,x*Math.cos(delta)-z*Math.sin(delta))+0.5).toNumber(),(165-145*Math.asin(z*Math.cos(delta)+x*Math.sin(delta))+0.5).toNumber()];}
    (:extendedCode) function coordinate(data as ByteArray,offset as Number) as Float {return ((data[offset]<<24)|(data[offset+1]<<16)|(data[offset+2]<<8)|data[offset+3])/1000000.0;}
    (:extendedCode) function countdownColor(current as ClockSnapshot, settings as SceneSettings) as Number {return current.rescheduled || current.sourceHold ? 0xFF6B6B : settings.countdownColor;}
    (:extendedCode) function draw(dc as Graphics.Dc,current as ClockSnapshot,minute as Number or Long,presentation as LocalePresentation,font as Graphics.FontType,settings as SceneSettings,map as Graphics.BitmapType or Null,pin as Boolean,pinX as Number,pinY as Number) as Void {
        dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();
        var positions=[[-1,-1],[1,-1],[-1,1],[1,1]];var phase=((minute%4+4)%4).toNumber();var p=positions[phase];
        if(map!=null){dc.drawBitmap(0,0,map);}
        // Keep the ACTIVE-coordinate coastlines outside the foreground bands.
        // Clearing under the hollow clock also bounds lit pixels on dense maps.
        dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);
        dc.fillRectangle(35,91,280,39);dc.fillRectangle(45,139,300,108);
        dc.fillRectangle(40,247,310,39);dc.fillRectangle(125,296,140,43);
        dc.setColor(settings.clockColor,Graphics.COLOR_TRANSPARENT);
        // Monospaced advance boxes do not imply symmetric digit ink. The
        // bundled AOD atlas has 53px advances; these are the fully lit left
        // and exclusive right edges of each digit. Center actual time ink,
        // The glyph baseline stays fixed vertically: native 454px scaling adds a
        // device-font offset that otherwise shifts the lower phases beyond
        // the two-pixel center bound. Horizontal movement and the independent
        // four-phase pixel-rest mask retain the minute-based burn-in pattern.
        var leftEdges=[5,9,4,4,4,5,5,4,5,5];
        var rightEdges=[48,37,49,48,50,48,49,49,48,48];
        var first="0123456789".find(current.localTime.substring(0,1) as String);
        var last="0123456789".find(current.localTime.substring(4,5) as String);
        var correction=first==null||last==null?0:(54-leftEdges[first as Number]-rightEdges[last as Number])/2;
        dc.setColor(settings.clockColor,Graphics.COLOR_TRANSPARENT);dc.drawText(195+p[0]+correction,121,font,current.localTime,Graphics.TEXT_JUSTIFY_CENTER);
        var calendarFont=presentation.aodContextFont as Graphics.FontType;
        if(current.localCalendar!=null){var date=presentation.calendar(current.localCalendar as Array<Number>);dc.setColor(0xD4DFEB,Graphics.COLOR_TRANSPARENT);dc.drawText(195+p[0],89+p[1],calendarFont,date,Graphics.TEXT_JUSTIFY_CENTER);}
        var color=countdownColor(current,settings);
        var countFont=presentation.aodContextFont as Graphics.FontType;
        var value=presentation.fit(dc,current.countdown,countFont,300);
        dc.setColor(color,Graphics.COLOR_TRANSPARENT);dc.drawText(195+p[0],246+p[1],countFont,value,Graphics.TEXT_JUSTIFY_CENTER);
        dc.setColor(0xD4DFEB,Graphics.COLOR_TRANSPARENT);dc.drawText(195+p[0],295+p[1],presentation.aodBatteryFont as Graphics.FontType,current.battery,Graphics.TEXT_JUSTIFY_CENTER);
        if(current.stale){dc.setColor(color,Graphics.COLOR_TRANSPARENT);var width=dc.getTextWidthInPixels(value,countFont);for(var x=195+p[0]-width/2;x<=195+p[0]+width/2;x+=5){dc.fillCircle(x,286+p[1],1);}}
        if(map!=null && pin){var x=pinX;var y=pinY;dc.setColor(0xFFFFFF,Graphics.COLOR_TRANSPARENT);dc.fillCircle(x,y,7);dc.setColor(0xFF6B6B,Graphics.COLOR_TRANSPARENT);dc.fillCircle(x,y,4);}
    }
}
