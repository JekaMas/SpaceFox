"""Build-time isolation of actual SceneRenderer drawing operations for masks.

This is a test-only source transform, never used by the watchface build. It
fails closed on changes to the enumerated primitive inventory. Each selected
operation still executes the product primitive and its real fonts/bitmaps;
non-selected operations are suppressed while layout/fit calculations run.
"""
import re

PRIMITIVES = {
    'clear': 2, 'drawText': 6, 'drawBitmap': 8, 'drawBitmap2': 1,
    'fillPolygon': 1, 'fillRectangle': 4, 'fillCircle': 4,
}


def isolate(source):
    found = {}
    for name in re.findall(r'\bdc\.(clear\w*|draw\w+|fill\w+|setClip)\s*\(', source):
        found[name] = found.get(name, 0) + 1
    if found != PRIMITIVES:
        raise ValueError('unsupported or changed scene primitive inventory: ' + repr(found))
    def one(old, new, count=1):
        nonlocal source
        if source.count(old) != count:
            raise ValueError('isolation source differs: ' + old[:90])
        source = source.replace(old, new)
    one('dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK); dc.clear();', 'MaskObserver.clear(dc);')
    one('dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();', 'MaskObserver.clear(dc);')
    one('var selectedMap=rich!=null && rich.mapBitmap!=null;', 'var selectedMap=rich!=null && rich.mapBitmap!=null;')
    one('if(selectedMap){dc.drawBitmap(0,0,rich.mapBitmap);}else if(map!=null){dc.drawBitmap2(0,0,map,mapScale);}', 'if(MaskObserver.visible("map")){if(selectedMap){dc.drawBitmap(0,0,rich.mapBitmap);}else if(map!=null){dc.drawBitmap2(0,0,map,mapScale);}}')
    one('if(downloaded!=null&&downloaded.bitmap!=null){downloaded.draw(dc,progress,ascent);}else{dc.drawBitmap(22,118-ascent,art as Graphics.BitmapType);}', 'if(MaskObserver.visible("art")){if(downloaded!=null&&downloaded.bitmap!=null){downloaded.draw(dc,progress,ascent);}else{dc.drawBitmap(22,118-ascent,art as Graphics.BitmapType);}}')
    one('if (progress > 0 && progress < 1) {\n                dc.setColor', 'if (MaskObserver.visible("flame") && progress > 0 && progress < 1) {\n                dc.setColor')
    one('if(flag!=null){dc.drawBitmap(footerLeft,325,flag as Graphics.BitmapType);}', 'if(flag!=null && MaskObserver.visible("flag")){dc.drawBitmap(footerLeft,325,flag as Graphics.BitmapType);}')
    one('if(context==null && art!=null){dc.drawBitmap(22,118,art as Graphics.BitmapType);}', 'if(context==null && art!=null && MaskObserver.visible("art")){dc.drawBitmap(22,118,art as Graphics.BitmapType);}')
    one('if(selectedMap){if(rich.scene!=null && rich.scene["position"]!=null){dc.drawBitmap(321,151,marker);}}\n        else if(pin){dc.drawBitmap(pinX-14,pinY-14,marker);}', 'if(MaskObserver.visible("point")){if(selectedMap){if(rich.scene!=null && rich.scene["position"]!=null){dc.drawBitmap(321,151,marker);}}\n        else if(pin){dc.drawBitmap(pinX-14,pinY-14,marker);}}')
    # Stable semantic IDs preserve all calls and resulting fit/layout values.
    calls = [
        ('text(dc,left+rocketWidth/2,43,', 'header_rocket'),
        ('text(dc,left+rocketWidth+8,47,', 'header_separator'),
        ('text(dc,left+rocketWidth+gap+operatorWidth/2,47,', 'header_operator'),
        ('text(dc,195,70,', 'purpose'), ('text(dc,footerLeft+flagWidth+footerWidth/2,319,', 'footer'),
        ('text(dc,195,95,', 'date'), ('text(dc,195,109,', 'clock'),
        ('text(dc,195,202,', 'countdown'), ('text(dc,left+width/2,y,', 'field_"+i'),
    ]
    for old, ident in calls:
        if ident == 'field_"+i':
            replacement = 'maskText("field_"+i,dc,left+width/2,y,'
        else:
            replacement = old.replace('text(dc,', 'maskText("'+ident+'",dc,', 1)
        one(old, replacement)
    one('icon(dc,left-(role.equals("battery")?31:25),rowTop+(role.equals("battery")?2:5),role);', 'if(MaskObserver.visible("icon_"+i)){icon(dc,left-(role.equals("battery")?31:25),rowTop+(role.equals("battery")?2:5),role);}')
    one('if ((current.stale || context != null && context.stale)) { underline', 'if (MaskObserver.visible("stale") && (current.stale || context != null && context.stale)) { underline')
    marker = '    (:typecheck(false)) function active('
    wrapper = '''    function maskText(id as String, dc as Graphics.Dc, x as Numeric, y as Numeric, font as Graphics.FontType, value as String, color as Number, width as Number, contour as Number) as String {
        if(MaskObserver.visible(id)){return text(dc,x,y,font,value,color,width,contour);}
        return fit(dc,value,font,width);
    }
'''
    one(marker, wrapper + marker)
    # LOW background cutouts belong to the map layer; foregrounds are isolated.
    one('if(map!=null){dc.drawBitmap(0,0,map);}', 'if(map!=null && MaskObserver.visible("map")){dc.drawBitmap(0,0,map);}')
    one('dc.fillRectangle(35,91,280,39);dc.fillRectangle(45,139,300,108);\n        dc.fillRectangle(40,247,310,39);dc.fillRectangle(125,296,140,43);', 'if(MaskObserver.visible("map")){dc.fillRectangle(35,91,280,39);dc.fillRectangle(45,139,300,108);\n        dc.fillRectangle(40,247,310,39);dc.fillRectangle(125,296,140,43);}')
    for operation, ident in [
        ('dc.drawText(195+p[0]+correction,121,font,current.localTime,Graphics.TEXT_JUSTIFY_CENTER);','clock'),
        ('dc.drawText(195+p[0],89+p[1],calendarFont,date,Graphics.TEXT_JUSTIFY_CENTER);','date'),
        ('dc.drawText(195+p[0],246+p[1],countFont,value,Graphics.TEXT_JUSTIFY_CENTER);','countdown'),
        ('dc.drawText(195+p[0],295+p[1],presentation.aodBatteryFont as Graphics.FontType,current.battery,Graphics.TEXT_JUSTIFY_CENTER);','battery'),
    ]:
        one(operation, 'if(MaskObserver.visible("'+ident+'")){'+operation+'}')
    one('if(current.stale){dc.setColor(color,Graphics.COLOR_TRANSPARENT);', 'if(current.stale && MaskObserver.visible("stale")){dc.setColor(color,Graphics.COLOR_TRANSPARENT);')
    one('if(map!=null && pin){var x=pinX;', 'if(map!=null && pin && MaskObserver.visible("point")){var x=pinX;')
    return source
