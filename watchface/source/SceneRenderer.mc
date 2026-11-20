import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Math;
import Toybox.WatchUi;

class SceneRenderer {
    var presentation as LocalePresentation;
    var mapDecision as MapPresentation;
    var fonts as Dictionary<String, Graphics.FontType>;
    var model as ResourceId or Null;
    var icons as Dictionary<String,Graphics.BitmapType>;
    var marker as Graphics.BitmapType;
    var art as Graphics.BitmapType or Null;
    var map as Graphics.BitmapType or Null;
    var artResource as ResourceId or Null=null;var artX as Number=0;var artY as Number=0;
    var mapResource as ResourceId or Null=null;
    var aodMap as Graphics.BitmapType or Null=null;
    var aodResource as ResourceId or Null=null;
    var aodPin as Boolean=false;var aodPinX as Number=335;var aodPinY as Number=165;
    var mapScale as Dictionary;
    var pin as Boolean = false;
    var worldFallback as Boolean = false;
    var pinX as Number = 335; var pinY as Number = 165;
    var fullContext as SceneContext or Null;
    var downloaded as NativeVisualRenderer or Null=null;
    var resourceLoads as Number = 0;
    var prepared as Boolean = false;
    var layoutRocketInput as String or Null=null;var layoutOperatorInput as String or Null=null;var layoutShortInput as String or Null=null;
    var layoutLabelFont as Graphics.FontType or Null=null;var layoutNameFont as Graphics.FontType or Null=null;var layoutRocket as String="";var layoutOperator as String="";
    var layoutRocketWidth as Number=0;var layoutOperatorWidth as Number=0;var layoutGap as Number=0;var layoutLeft as Number=0;
    var siteInput as String or Null=null;var siteFont as Graphics.FontType or Null=null;var siteBudget as Number=0;var siteText as String="";var siteWidth as Number=0;
    var metricLayouts as Array=[null,null,null,null,null,null,null,null];
    (:extendedCode)
    function initialize(owner as LocalePresentation or Null) {
        presentation=owner==null?new LocalePresentation():owner;mapDecision=new MapPresentation();
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
    (:extendedCode, :typecheck(false))
    function prepare(context as SceneContext or Null, settings as SceneSettings) as Void {
        presentation.prepare(settings.language);fonts["label"]=presentation.label as Graphics.FontType;fonts["small"]=presentation.small as Graphics.FontType;fonts["count"]=presentation.count as Graphics.FontType;
        var selected={} as Dictionary<String,Graphics.BitmapType>;
        for(var i=0;i<settings.slots.size();i+=1){var role=settings.slots[i];if(NativeAssets.icons.hasKey(role)&&!selected.hasKey(role)){selected[role]=icons.hasKey(role)?(icons[role] as Graphics.BitmapType):load(NativeAssets.icons[role] as ResourceId) as Graphics.BitmapType;}}
        icons=selected;
        mapDecision.bind(context);
        // Unchanged model and qualified point retain the same bitmaps even if
        // metadata/settings were refreshed or the accepted scene woke again.
        var same=prepared && ((context==null && fullContext==null) ||
            (context!=null && fullContext!=null && context.modelId.equals(fullContext.modelId) && samePoint(context.point,fullContext.point)));
        fullContext=context;
        if(same){
            var rich=downloaded instanceof NativeSfrRenderer?downloaded:null;
            if(art==null && artResource!=null && (downloaded==null||downloaded.bitmap==null)){art=load(artResource as ResourceId) as Graphics.BitmapType;}
            if(map==null && mapResource!=null && (rich==null||rich.mapBitmap==null)){map=load(mapResource as ResourceId) as Graphics.BitmapType;}
            return;
        }
        prepared=true;
        // The bundled view is geographical backdrop only: no location marker is
        // shown unless the selected launch supplies a qualified matching point.
        model = null; art = null; artX=0;artY=0; map = null; aodMap=null; aodResource=null; pin = false;aodPin=false;worldFallback=false;
        var resource=mapDecision.activeResource();
        if (context == null) { self.mapResource=resource;artResource=Rez.Drawables.Art_unknown;aodResource=mapDecision.lowResource();map=load(resource) as Graphics.BitmapType; art=load(artResource as ResourceId) as Graphics.BitmapType; return; }
        model=NativeModels.resource(context.modelId);artResource=model;var anchor=NativeModels.anchor(model as ResourceId);artX=anchor[0];artY=anchor[1];art=load(artResource as ResourceId) as Graphics.BitmapType;
        pin=mapDecision.matched;aodPin=pin;pinX=mapDecision.x;pinY=mapDecision.y;aodPinX=pinX;aodPinY=pinY;
        worldFallback=mapDecision.worldPoint(true)!=null;
        aodResource=worldFallback?null:mapDecision.lowResource();
        if(worldFallback){self.mapResource=null;map=null;}else{self.mapResource=resource;map=load(resource) as Graphics.BitmapType;}
    }
    // Only restore a bundled bitmap if this point has a matching bundled map;
    // unmatched points continue to use the bounded source-world fallback.
    (:typecheck(false)) function useDownloaded(value as NativeVisualRenderer or Null) as Void {
        downloaded=value;var rich=value instanceof NativeSfrRenderer?value:null;
        if(value!=null && value.bitmap!=null){art=null;}
        else if(art==null && artResource!=null){art=load(artResource as ResourceId) as Graphics.BitmapType;}
        if(rich!=null && rich.mapBitmap!=null){map=null;}
        else if(map==null && mapResource!=null){map=load(mapResource as ResourceId) as Graphics.BitmapType;}
    }
    function samePoint(a as Array<Numeric> or Null,b as Array<Numeric> or Null) as Boolean {
        if(a==null||b==null){return a==null&&b==null;}
        return a.size()==2&&b.size()==2&&a[0]==b[0]&&a[1]==b[1];
    }
    function aodCoordinate(data as ByteArray,offset as Number) as Float {return SceneAod.coordinate(data,offset);}
    (:extendedCode, :typecheck(false)) function fit(dc as Graphics.Dc, text as String, font as Graphics.FontType, width as Number) as String {
        if(layoutRocketInput!=null && font==layoutLabelFont && text.equals(layoutRocket) && layoutRocketWidth<=width){return text;}
        if(layoutOperatorInput!=null && font==layoutNameFont && text.equals(layoutOperator) && layoutOperatorWidth<=width){return text;}
        if(siteInput!=null&&font==siteFont&&text.equals(siteText)&&siteWidth<=width){return text;}
        for(var i=0;i<metricLayouts.size();i+=1){var entry=metricLayouts[i];if(entry!=null && entry[1]==font && text.equals(entry[3]) && entry[4]<=width){return text;}}
        return presentation.fit(dc,text,font,width);
    }
    (:extendedCode, :typecheck(false)) function metricFit(slot,dc,value,font,width) {
        var entry=metricLayouts[slot];if(entry!=null&&entry[1]==font&&entry[2]==width&&entry[0].equals(value)){return entry[3];}
        var fitted=presentation.fit(dc,value,font,width);metricLayouts[slot]=[value,font,width,fitted,dc.getTextWidthInPixels(fitted,font)];return fitted;
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
        var selectedMap=mapDecision.useDownloaded(true,rich!=null && rich.mapBitmap!=null && rich.scene!=null && rich.scene["position"]!=null);
        var useWorld=worldFallback;
        try{if(selectedMap){dc.drawBitmap(0,0,rich.mapBitmap);}else if(useWorld){FallbackWorld.draw(dc,97,15);}else if(map!=null){dc.drawBitmap2(0,0,map,mapScale);}}
        catch(e){selectedMap=false;useWorld=true;dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();try{FallbackWorld.draw(dc,97,15);}catch(ignored){}}
        var context = fullContext;
        if (context != null) {
            // Match the existing unavailable health marker without changing the
            // accepted context: absent company/mission stay empty in storage.
            var purposeText=presentation.mission(context.purpose);
            var labelFont=fonts["label"] as Graphics.FontType;var nameFont=fonts["nameSmall"] as Graphics.FontType;
            if(layoutRocketInput==null||!layoutRocketInput.equals(context.rocket)||!layoutOperatorInput.equals(context.operator)||!layoutShortInput.equals(context.operatorShort)||layoutLabelFont!=labelFont||layoutNameFont!=nameFont){
                // Invalidate by the actual text and fonts, including an empty
                // long operator whose short fallback may change independently.
                layoutRocketInput=null;layoutOperatorInput=null;
                var operatorText=context.operator.equals("")?(context.operatorShort.equals("")?"—":context.operatorShort):context.operator;
                var naturalOperator=dc.getTextWidthInPixels(operatorText,nameFont);
                if(!context.operatorShort.equals("")&&!context.operator.equals("")&&naturalOperator>(context.rocket.equals("")?238:100)){operatorText=context.operatorShort;naturalOperator=dc.getTextWidthInPixels(operatorText,nameFont);}
                var operatorBudget=context.rocket.equals("")?238:(naturalOperator<100?naturalOperator:100);
                var rocketBudget=238-operatorBudget-(context.rocket.equals("")?0:16);
                layoutRocket=presentation.fit(dc,context.rocket,labelFont,rocketBudget);layoutOperator=presentation.fit(dc,operatorText,nameFont,operatorBudget);
                layoutRocketWidth=dc.getTextWidthInPixels(layoutRocket,labelFont);layoutOperatorWidth=dc.getTextWidthInPixels(layoutOperator,nameFont);
                layoutGap=layoutRocket.equals("")||layoutOperator.equals("")?0:16;layoutLeft=195-(layoutRocketWidth+layoutOperatorWidth+layoutGap)/2;
                layoutRocketInput=context.rocket;layoutOperatorInput=context.operator;layoutShortInput=context.operatorShort;layoutLabelFont=labelFont;layoutNameFont=nameFont;
            }
            var rocketTitle=layoutRocket;var operatorTitle=layoutOperator;var rocketWidth=layoutRocketWidth;var operatorWidth=layoutOperatorWidth;var gap=layoutGap;var left=layoutLeft;
            text(dc,left+rocketWidth/2,43,fonts["label"] as Graphics.FontType,rocketTitle,0xD8E2ED,238,1);
            if(gap>0){text(dc,left+rocketWidth+8,47,fonts["nameSmall"] as Graphics.FontType,"·",0x96B8C9,16,1);}
            text(dc,left+rocketWidth+gap+operatorWidth/2,47,fonts["nameSmall"] as Graphics.FontType,operatorTitle,0xD4DFEB,238,1);
            text(dc,195,70,(fonts["small"] as Graphics.FontType),purposeText,0xD4DFEB,282,1);
            try{if(downloaded!=null&&downloaded.bitmap!=null){downloaded.draw(dc,0.0,0);}else if(art!=null){dc.drawBitmap(22+artX,118+artY,art as Graphics.BitmapType);}}
            catch(e){dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.fillRectangle(22,118,54,124);try{if(art==null&&artResource!=null){art=load(artResource as ResourceId) as Graphics.BitmapType;}if(art!=null){dc.drawBitmap(22+artX,118+artY,art as Graphics.BitmapType);}}catch(ignored){}}
            var flag=rich==null?null:rich.siteCountryBitmap;
            var footerBudget=flag==null?242:216;
            var footerFont=dc.getTextWidthInPixels(context.site,fonts["label"] as Graphics.FontType)>footerBudget?fonts["nameSmall"] as Graphics.FontType:fonts["label"] as Graphics.FontType;
            if(siteInput==null||!siteInput.equals(context.site)||siteFont!=footerFont||siteBudget!=footerBudget){
                siteInput=context.site;siteFont=footerFont;siteBudget=footerBudget;siteText=presentation.fit(dc,context.site,footerFont,footerBudget);siteWidth=dc.getTextWidthInPixels(siteText,footerFont);
            }
            var footer=siteText;var footerWidth=siteWidth;
            var flagWidth=flag==null?0:26;
            var footerLeft=195-(footerWidth+flagWidth)/2;
            if(flag!=null){dc.drawBitmap(footerLeft,325,flag as Graphics.BitmapType);}
            text(dc,footerLeft+flagWidth+footerWidth/2,319,footerFont,footer,0xD4DFEB,footerBudget,1);
        }
        if(context==null && art!=null){dc.drawBitmap(22+artX,118+artY,art as Graphics.BitmapType);}
        if(current.localCalendar!=null){text(dc,195,95,presentation.calendarFont as Graphics.FontType,presentation.calendar(current.localCalendar as Array<Number>),0xD4DFEB,200,1);}
        text(dc,195,109,(fonts["time"] as Graphics.FontType),current.localTime,settings.clockColor,250,1);
        current.rescheduled=current.rescheduled||context!=null&&context.rescheduled;
        current.sourceHold=current.sourceHold||context!=null&&context.sourceHold;
        var color = SceneAod.countdownColor(current,settings);
        var countdownLabel=current.countdown;
        var countFont = dc.getTextWidthInPixels(countdownLabel,fonts["count"] as Graphics.FontType) > 275 ? (fonts["small"] as Graphics.FontType) : (fonts["count"] as Graphics.FontType);
        var shown = text(dc,195,202,countFont,countdownLabel,color,275,1);
        var countWidth=dc.getTextWidthInPixels(shown,countFont);if(current.rescheduled){SceneAod.rescheduleMark(dc,195+countWidth/2+8,209);}if(current.sourceHold){SceneAod.holdMark(dc,195+countWidth/2+(current.rescheduled?20:8),209);}
        if ((current.stale || context != null && context.stale)) { underline(dc,195,241,countWidth,color); }
        for (var i = 0; i < 4; i += 1) {
            var role = settings.slots[i];
            var label=metricText(fitness,values,role,settings);
            var rowTop=i<2?244:282;
            if(role.find("custom")==0){
                var small=fonts["small"] as Graphics.FontType;var metric=fonts["metric"] as Graphics.FontType;
                var customLeft=i%2==0?55:207;var name=metricFit(i,dc,fitness.fieldLabel(role),small,35);
                drawProviderIcon(dc,fitness.fieldIcon(role),customLeft,rowTop,settings.fieldColors[i]);
                text(dc,customLeft+17,rowTop+6,small,name,settings.fieldColors[i],35,1);
                var selected=fitness.selectedFields;var numeric=selected!=null && (selected as SelectedFields).fitted(role)?(selected as SelectedFields).numeric(role):metricGlyphs(label);
                var valueFont=numeric?metric:small;
                var fittedValue=metricFit(i+4,dc,label,valueFont,90);
                var shownValue=text(dc,customLeft+80,rowTop+(valueFont==metric?-4:6),valueFont,fittedValue,settings.fieldColors[i],90,1);
                if(selected!=null){(selected as SelectedFields).keepFitted(role,name,shownValue,numeric);}
                // Do not retain a long provider string as a cache key after
                // the selected-field owner has kept its exact fitted output.
                if(selected!=null){metricLayouts[i][0]=name;metricLayouts[i+4][0]=shownValue;}
            }else{
                label=metricFit(i,dc,label,fonts["metric"] as Graphics.FontType,128);
                var width=metricLayouts[i][4] as Number;
                var left=i%2==0?55:335-width;if(i==2&&role.equals("battery")){left+=18;}var y=rowTop-4;
                icon(dc,left-(role.equals("battery")?31:25),rowTop+(role.equals("battery")?2:5),role);
                text(dc,left+width/2,y,fonts["metric"] as Graphics.FontType,label,settings.fieldColors[i],128,1);
            }
        }
        try{if(selectedMap){if(rich.scene!=null && rich.scene["position"]!=null){dc.drawBitmap(321,151,marker);}}
        else if(useWorld&&context!=null){FallbackMap.point(dc,context.point,97,15);}
        else if(pin){dc.drawBitmap(pinX-14,pinY-14,marker);}}catch(ignored){}
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
        SceneAod.staleMark(dc,x,y,width,color);
    }
    (:extendedCode) function icon(dc as Graphics.Dc,x as Numeric,y as Numeric,role as String) as Void {
        if(icons.hasKey(role)){dc.drawBitmap(x,y,icons[role] as Graphics.BitmapType);}
    }
    (:typecheck(false)) function drawProviderIcon(dc,icon,left,top,color) as Void {
        if(icon==null){return;}
        if(icon!=false){try{dc.drawBitmap2(left-25,top+5,icon[0],icon[1]);return;}catch(e){}}
        dc.setColor(color,Graphics.COLOR_TRANSPARENT);dc.drawCircle(left-16,top+14,4);
    }
    (:extendedCode) function prepareAod() as Void {presentation.prepareAodFonts();if(!fonts.hasKey("aod")){fonts["aod"]=load(Rez.Fonts.Aod40) as Graphics.FontType;}if(aodMap==null && aodResource!=null){aodMap=load(aodResource as ResourceId) as Graphics.BitmapType;}}
    (:extendedCode) function releaseAod() as Void {aodMap=null;fonts.remove("aod");presentation.aodContextFont=null;presentation.aodBatteryFont=null;}
    (:extendedCode, :typecheck(false)) function aodWorldPoint(bundled,selected) {return worldFallback&&!bundled&&!selected&&fullContext!=null?fullContext.point:null;}
    (:extendedCode, :typecheck(false)) function aod(dc as Graphics.Dc,current as ClockSnapshot,minute as Number or Long,settings as SceneSettings) as Void {
        current.rescheduled=current.rescheduled||fullContext!=null&&fullContext.rescheduled;
        current.sourceHold=current.sourceHold||fullContext!=null&&fullContext.sourceHold;
        current.stale=current.stale||fullContext!=null&&fullContext.stale;
        var rich=downloaded instanceof NativeSfrRenderer?downloaded:null;
        var selected=mapDecision.useDownloaded(true,rich!=null && (rich.mapOutline!=null||(rich.bundledOutline&&aodPin&&aodResource!=null)) && rich.scene!=null && rich.scene["position"]!=null);
        // The current finite fixed-site catalog has full outlines at matching
        // centers. Prefer that shape even when the selected scene is READY;
        // unmatched future locations retain their own decoded raster outline.
        var bundled=mapDecision.useBundled(true,aodMap!=null);
        var qualifiedPin=mapDecision.pointVisible(true)&&((bundled&&aodPin)||selected);
        SceneAod.draw(dc,current,minute,presentation,fonts["aod"] as Graphics.FontType,settings,bundled?aodMap:(selected?rich.mapOutline:null),qualifiedPin,bundled?aodPinX:335,bundled?aodPinY:165,aodWorldPoint(bundled,selected));
    }
}

// A compact, fixed equirectangular source map avoids associating an unmatched
// point with a different site's pre-rendered geography. Coordinates have been
// validated before reaching this renderer; no point is drawn for an unavailable position.
module FallbackMap {
    (:extendedCode, :typecheck(false)) function point(dc,position,x,y) as Void {
        if(position==null){return;}
        var px=x+((position[0]+180)*194/360+0.5).toNumber();
        var py=y+((90-position[1])*97/180+0.5).toNumber();
        dc.setColor(0xFFD066,Graphics.COLOR_TRANSPARENT);dc.fillCircle(px,py,3);
    }

}

// LOW rendering uses the same clock snapshot as the active scene. The caller
// owns the once-per-minute guard; fonts/dictionary are prepared outside redraw.
module SceneAod {
    (:extendedCode) function project(point as Array<Numeric>,longitude as Numeric,latitude as Numeric) as Array<Number> {var rad=0.017453292519943295;var lambda=(point[0]-longitude)*rad;var phi=point[1]*rad;var delta=-latitude*rad;var x=Math.cos(lambda)*Math.cos(phi);var y=Math.sin(lambda)*Math.cos(phi);var z=Math.sin(phi);return [(335+145*Math.atan2(y,x*Math.cos(delta)-z*Math.sin(delta))+0.5).toNumber(),(165-145*Math.asin(z*Math.cos(delta)+x*Math.sin(delta))+0.5).toNumber()];}
    (:extendedCode) function coordinate(data as ByteArray,offset as Number) as Float {return ((data[offset]<<24)|(data[offset+1]<<16)|(data[offset+2]<<8)|data[offset+3])/1000000.0;}
    (:extendedCode) function countdownColor(current as ClockSnapshot, settings as SceneSettings) as Number {var remaining=current.remainingUtc;if(remaining==null){return 0xA3ADB8;}return remaining>=86400?0xA3ADB8:settings.countdownColor;}
    (:extendedCode) function staleMark(dc as Graphics.Dc,x as Numeric,y as Numeric,width as Number,color as Number) as Void {dc.setColor(color,Graphics.COLOR_TRANSPARENT);for(var i=x-width/2;i<=x+width/2;i+=5){dc.fillCircle(i,y,1);}}
    (:extendedCode) function rescheduleMark(dc as Graphics.Dc,x as Number,y as Number) as Void {dc.drawLine(x-4,y-3,x+2,y-3);dc.drawLine(x+2,y-3,x+4,y-1);dc.drawLine(x+4,y-1,x+2,y+1);dc.drawLine(x+4,y+3,x-2,y+3);dc.drawLine(x-2,y+3,x-4,y+1);dc.drawLine(x-4,y+1,x-2,y-1);}
    (:extendedCode) function holdMark(dc as Graphics.Dc,x as Number,y as Number) as Void {dc.drawLine(x-2,y-4,x-2,y+4);dc.drawLine(x+2,y-4,x+2,y+4);}
    (:extendedCode) function draw(dc as Graphics.Dc,current as ClockSnapshot,minute as Number or Long,presentation as LocalePresentation,font as Graphics.FontType,settings as SceneSettings,map as Graphics.BitmapType or Null,pin as Boolean,pinX as Number,pinY as Number,worldPoint as Array<Numeric> or Null) as Void {
        dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();
        var positions=[[-1,-1],[1,-1],[-1,1],[1,1]];var phase=((minute%4+4)%4).toNumber();var p=positions[phase];
        if(map!=null){dc.drawBitmap(0,0,map);}
        if(worldPoint!=null){FallbackWorld.draw(dc,97,15);}
        // Keep the ACTIVE-coordinate coastlines outside the foreground bands.
        // Clearing under the hollow clock also bounds lit pixels on dense maps.
        dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);
        dc.fillRectangle(35,91,280,39);dc.fillRectangle(45,139,300,108);
        dc.fillRectangle(40,247,310,39);dc.fillRectangle(125,296,140,43);
        // Draw the qualified point after the foreground masks so a southern
        // coordinate is not erased by the calendar/clock clearing band.
        if(worldPoint!=null){FallbackMap.point(dc,worldPoint,97,15);}
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
        dc.setColor(color,Graphics.COLOR_TRANSPARENT);dc.drawText(195+p[0],246+p[1],countFont,value,Graphics.TEXT_JUSTIFY_CENTER);if(current.rescheduled){rescheduleMark(dc,195+p[0]+dc.getTextWidthInPixels(value,countFont)/2+8,253+p[1]);}if(current.sourceHold){holdMark(dc,195+p[0]+dc.getTextWidthInPixels(value,countFont)/2+(current.rescheduled?20:8),253+p[1]);}
        dc.setColor(0xD4DFEB,Graphics.COLOR_TRANSPARENT);dc.drawText(195+p[0],295+p[1],presentation.aodBatteryFont as Graphics.FontType,current.battery,Graphics.TEXT_JUSTIFY_CENTER);
        if(current.stale){staleMark(dc,195+p[0],286+p[1],dc.getTextWidthInPixels(value,countFont),color);}
        if(map!=null && pin){var x=pinX;var y=pinY;dc.setColor(0xFFFFFF,Graphics.COLOR_TRANSPARENT);dc.fillCircle(x,y,7);dc.setColor(0xFF6B6B,Graphics.COLOR_TRANSPARENT);dc.fillCircle(x,y,4);}
    }
}
