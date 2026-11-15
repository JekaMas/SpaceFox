"""Derive finite bundled map centers from the current authored site catalog."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.spacefox.catalog import build_catalog

def points():
    catalog=build_catalog(ROOT);centers=[];rows=[]
    for identity,entry in sorted(catalog['dictionaries']['sites'].items()):
        point=entry.get('position');mode=entry['facts'].get('positionMode','fixed-source')
        if point is None or mode!='fixed-source':continue
        lon=float(point['longitude']);lat=float(point['latitude'])
        index=next((i for i,(x,y) in enumerate(centers) if abs(lon-x)<=.25 and abs(lat-y)<=.25),None)
        if index is None:index=len(centers);centers.append([lon,lat])
        rows.append({'id':identity,'point':[lon,lat],'view':index})
    return {'schema':1,'boundary':'Fixed-source positions from current authored catalog; no mobile-reference points. Later catalog additions require resource refresh.','catalogVersion':catalog['catalogVersion'],'points':centers,'siteBindings':rows}
if __name__=='__main__':
    (ROOT/'watchface/resource-inputs/map-views.json').write_text(json.dumps(points(),indent=2)+'\n')
