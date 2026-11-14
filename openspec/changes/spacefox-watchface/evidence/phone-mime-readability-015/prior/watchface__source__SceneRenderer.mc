import Toybox.Graphics;
import Toybox.Lang;
import Toybox.WatchUi;

class SceneRenderer {
    var presentation as LocalePresentation;
    var fonts as Dictionary<String, Graphics.FontType>;
    var model as NativeModel or Null;
    var icons as Dictionary<String,Graphics.BitmapType>;
    var marker as Graphics.BitmapType;
    var art as Graphics.BitmapType or Null;
    var map as Graphics.BitmapType or Null;
    var pin as Boolean = false;
    var fullContext as SceneContext or Null;
    var downloaded as NativeVisualRenderer or Null=null;
    var syncStatus as String="waiting";
    var syncDetail as String="";
    var resourceLoads as Number = 0;
    (:extendedCode)
    function initialize(owner as LocalePresentation or Null) {
        presentation=owner==null?new LocalePresentation():owner;
        fonts = {};icons={};
        var roles=["steps","energy","heart","stress","calories","battery"];
        for(var i=0;i<roles.size();i+=1){icons[roles[i]]=load(NativeAssets.icons[roles[i]] as ResourceId) as Graphics.BitmapType;}
        marker=load(Rez.Drawables.LaunchMarker) as Graphics.BitmapType;
        fonts["battery"] = load(Rez.Fonts.Battery13) as Graphics.FontType;
        fonts["aod"] = load(Rez.Fonts.Aod40) as Graphics.FontType;
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
        // The bundled view is geographical backdrop only: no location marker is
        // shown unless the selected launch supplies a qualified matching point.
        fullContext = context; model = null; art = null; map = null; pin = false;
        var mapResource=Rez.Drawables.MapView0;
        if (context == null) { map=load(mapResource) as Graphics.BitmapType; art = load(Rez.Drawables.Art_unknown) as Graphics.BitmapType; return; }
        var id = NativeAssets.models.hasKey(context.modelId) ? context.modelId : "generic";
        model = NativeAssets.models[id] as NativeModel; art = load(id.equals("generic") ? Rez.Drawables.Art_unknown : (model as NativeModel).resource) as Graphics.BitmapType;
        if (context.point != null) {
            for (var i = 0; i < NativeAssets.maps.size(); i += 1) {
                var view = NativeAssets.maps[i];
                if ((context.point as Array<Numeric>)[0] == view.longitude && (context.point as Array<Numeric>)[1] == view.latitude) {
                    mapResource=view.resource; pin = true; break;
                }
            }
        }
        map=load(mapResource) as Graphics.BitmapType;
    }
    function fit(dc as Graphics.Dc, text as String, font as Graphics.FontType, width as Number) as String {
        return presentation.fit(dc,text,font,width);
    }
    function text(dc as Graphics.Dc, x as Numeric, y as Numeric, font as Graphics.FontType, value as String, color as Number, width as Number, contour as Number) as String {
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
    function active(dc as Graphics.Dc, current as ClockSnapshot, settings as SceneSettings, values as Dictionary<String, Number or Null>, fitness as Fitness, progress as Float) as Void {
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK); dc.clear();
        var rich=downloaded instanceof NativeSfrRenderer?downloaded:null;
        if(rich!=null){rich.drawBackground(dc,settings,marker);}else if (map != null) { dc.drawBitmap(0,0,map); }
        if (rich==null&&pin) {
            // Accepted ring24 SVG: opaque backplate, white halo, yellow core.
            // 28px resource center14 preserves the source-projected335/165 point.
            dc.drawBitmap(321,151,marker);
        }
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
            // Optional art can fail after schedule admission. Expose the bounded
            // reason until the matching visual is ready, without changing the
            // selected mission or the independent countdown status colors.
            if(downloaded==null&&(syncStatus.equals("assetFailed")||syncStatus.equals("incomplete")&&syncDetail.equals("Assets"))){text(dc,195,95,(fonts["small"] as Graphics.FontType),presentation.assetStatus(syncStatus,syncDetail),0xD4DFEB,282,1);}
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
        if(context==null){
            text(dc,195,50,fonts["small"] as Graphics.FontType,presentation.syncStatus(syncStatus),0xD4DFEB,282,1);
            if(!syncDetail.equals("")){text(dc,195,75,fonts["small"] as Graphics.FontType,syncDetail,0xAFC3CE,282,1);}
            if(art!=null){dc.drawBitmap(22,118,art as Graphics.BitmapType);}
        }
        dc.setColor(0xB2C3CE,Graphics.COLOR_TRANSPARENT); dc.drawRectangle(173,27,13,8); dc.drawLine(187,29,187,33);
        text(dc,207,24,(fonts["battery"] as Graphics.FontType),fitness.display(values,"battery"),0xB2C3CE,65,1);
        text(dc,195,120,(fonts["time"] as Graphics.FontType),current.localTime,settings.clockColor,250,1);
        var color = (current.rescheduled || context != null && context.rescheduled) ? 0xF3C37A : settings.countdownColor;
        var countdownLabel=displayCountdown(current,settings);
        var countFont = dc.getTextWidthInPixels(countdownLabel,fonts["count"] as Graphics.FontType) > 275 ? (fonts["small"] as Graphics.FontType) : (fonts["count"] as Graphics.FontType);
        var shown = text(dc,195,202,countFont,countdownLabel,color,275,1);
        if ((current.stale || context != null && context.stale)) { underline(dc,195,237,dc.getTextWidthInPixels(shown,countFont),color); }
        for (var i = 0; i < 4; i += 1) {
            var role = settings.slots[i];
            var label=metricText(fitness,values,role,settings);
            label=fit(dc,label,fonts["metric"] as Graphics.FontType,112);
            var width=dc.getTextWidthInPixels(label,fonts["metric"] as Graphics.FontType);
            var left=i%2==0?80:335-width;var rowTop=i<2?244:282;var y=rowTop-4;
            icon(dc,left-25,rowTop+5,role);
            text(dc,left+width/2,y,fonts["metric"] as Graphics.FontType,label,settings.fieldColors[i],112,1);
        }
    }
    function displayCountdown(current as ClockSnapshot,settings as SceneSettings) as String {
        return presentation.countdown(current,true);
    }
    function metricText(fitness as Fitness,values as Dictionary<String,Number or Null>,role as String,settings as SceneSettings) as String {
        return presentation.metric(fitness,values,role);
    }
    function underline(dc as Graphics.Dc,x as Numeric,y as Numeric,width as Number,color as Number) as Void {
        dc.setColor(color,Graphics.COLOR_TRANSPARENT);
        for (var i = x-width/2; i <= x+width/2; i += 5) { dc.fillCircle(i,y,1); }
    }
    function icon(dc as Graphics.Dc,x as Numeric,y as Numeric,role as String) as Void {
        if(icons.hasKey(role)){dc.drawBitmap(x,y,icons[role] as Graphics.BitmapType);}
    }
    function aod(dc as Graphics.Dc,current as ClockSnapshot,minute as Number or Long) as Void {
        current.rescheduled=current.rescheduled||fullContext!=null&&fullContext.rescheduled;
        current.stale=current.stale||fullContext!=null&&fullContext.stale;
        SceneAod.draw(dc,current,minute,presentation,fonts["aod"] as Graphics.FontType);
    }
}

// Shared by complete rendering and deferred-admission maintenance. The caller
// owns the once-per-minute guard; fonts/dictionary are prepared outside redraw.
module SceneAod {
    function draw(dc as Graphics.Dc,current as ClockSnapshot,minute as Number or Long,presentation as LocalePresentation,font as Graphics.FontType) as Void {
        dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();
        var positions = [[-42,-36],[42,-36],[-42,36],[42,36]];var phase=((minute%4+4)%4).toNumber();var p=positions[phase];
        dc.setColor(0x777777,Graphics.COLOR_TRANSPARENT);
        dc.drawText(195+p[0],142+p[1],font,current.localTime,Graphics.TEXT_JUSTIFY_CENTER);
        var color=current.rescheduled?0xA8752D:0x558A78;
        var countFont=presentation.small as Graphics.FontType;
        var value=presentation.fit(dc,presentation.countdown(current,false),countFont,220);
        dc.setColor(color,Graphics.COLOR_TRANSPARENT);
        dc.drawText(195+p[0],190+p[1],countFont,value,Graphics.TEXT_JUSTIFY_CENTER);
        if(current.stale){var width=dc.getTextWidthInPixels(value,countFont);for(var x=195+p[0]-width/2;x<=195+p[0]+width/2;x+=5){dc.fillCircle(x,214+p[1],1);}}
    }
}
