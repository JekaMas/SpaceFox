#!/usr/bin/env python3
"""Check bounded geometry and AOD pixels in captured FR165M frames."""
import json
from pathlib import Path
from tools.spacefox.native_profile import png_pixels

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'openspec/changes/spacefox-watchface/evidence/display03-active-tick-wake/author-runtime'
REGIONS={'left1':(50,246,105,285),'left2':(50,285,105,323),
         'right1':(284,246,340,285),'right2':(284,285,340,323)}

def verify(root=ROOT):
    evidence=Path(root)/'openspec/changes/spacefox-watchface/evidence/display03-active-tick-wake/author-runtime'
    observations={}
    for language in ('en','ru'):
        aw,ah,active=png_pixels((evidence/f'final-active-{language}.png').read_bytes())
        lw,lh,low=png_pixels((evidence/f'final-low-{language}.png').read_bytes())
        assert (aw,ah,lw,lh)==(390,390,390,390)
        def pixel(data,x,y):
            at=(y*390+x)*4
            return data[at:at+3]
        fields={}
        for name,(x0,y0,x1,y1) in REGIONS.items():
            points=[(x,y) for y in range(y0,y1) for x in range(x0,x1)
                    if min(pixel(active,x,y))>=190]
            assert len(points)>100
            bounds=(min(x for x,y in points),min(y for x,y in points),
                    max(x for x,y in points),max(y for x,y in points))
            assert 30<=bounds[3]-bounds[1]+1<=36
            fields[name]={'bounds':bounds,'brightPixels':len(points)}
        assert abs(fields['left1']['bounds'][1]-fields['right1']['bounds'][1])<=1
        assert abs(fields['left2']['bounds'][1]-fields['right2']['bounds'][1])<=1
        for x0,x1 in ((50,105),(284,340)):
            assert not any(max(pixel(low,x,y)) for x in range(x0,x1) for y in range(287,323))
        lit=sum(1 for at in range(0,len(low),4) if max(low[at:at+3])>0)
        assert 0<lit<11945
        marker=sum(1 for y in range(65,85) for x in range(290,310)
                   if (lambda p:p[0]>150 and p[1]<180)(pixel(low,x,y)))
        assert marker>=8
        outline=sum(1 for y in range(20,100) for x in range(245,320)
                    if (lambda p:p[2]>p[0] and p[2]>8)(pixel(low,x,y)))
        assert outline>30
        yellow=sum(1 for y in range(152,178) for x in range(323,348)
                   if (lambda p:p[0]>180 and p[1]>120 and p[2]<150)(pixel(active,x,y)))
        assert yellow>20
        coral=sum(1 for y in range(207,244) for x in range(90,300)
                  if (lambda p:p[0]>130 and p[0]>p[1]*1.3)(pixel(active,x,y)))
        assert coral>100
        low_coral=sum(1 for y in range(250,290) for x in range(95,290)
                      if (lambda p:p[0]>100 and p[0]>p[1]*1.3)(pixel(low,x,y)))
        assert low_coral>50
        observations[language]={'fields':fields,'lowLitPixels':lit,
                                'lowPointPixels':marker,'lowOutlinePixels':outline,
                                'activePointPixels':yellow,'activeCoralPixels':coral,'lowCoralPixels':low_coral}
    return observations

if __name__=='__main__':print(json.dumps(verify(),indent=2))
