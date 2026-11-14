"""One finite source-bound SFR codec contact-sheet audit; no SDK/device claim."""
import hashlib
import io
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from tools.audit_site_flag_batch import audit, ROOT
from tools.spacefox.catalog import build_catalog, loads_json
from tools.spacefox.native_profile import _map_visuals, rasterize, encode_raster, decode_raster
from tools.spacefox.graphics import export_svg
from tools.spacefox import bridge_map
from tools.spacefox.graphics import PACK_BASE
from tools.spacefox.bridge_map import build_map

OUT = ROOT / 'openspec/changes/spacefox-watchface/evidence/site-flag-visual-batch'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pixels_from_asset(row, width, height):
    raw = (ROOT / row['content']['path']).read_bytes()
    if sha(raw) != row['content']['sha256']:
        raise ValueError('source asset digest mismatch')
    visual = export_svg(raw, row['facts'].get('exportSize'), row['facts'].get('visualAnimation'))
    rgba, _, _ = rasterize([visual], width, height)
    encoded = encode_raster(rgba, width, height, 4)
    if decode_raster(encoded, width, height, 4) != rgba:
        raise ValueError('codec round trip mismatch')
    return Image.frombytes('RGBA', (width, height), rgba), sha(rgba)


def sheet(rows, cols, cell, name):
    width, height = cell
    canvas = Image.new('RGB', (cols * width, math.ceil(len(rows)/cols) * height), '#132032')
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    for i, (label, image) in enumerate(rows):
        x, y = (i % cols) * width, (i // cols) * height
        if image is not None:
            image.thumbnail((width - 10, height - 38), Image.Resampling.LANCZOS)
            if image.mode == 'RGBA': canvas.paste(image, (x + (width-image.width)//2, y+3), image)
            else: canvas.paste(image, (x + (width-image.width)//2, y+3))
        draw.text((x+4, y+height-32), label[:24], fill='white', font=font)
    target = OUT / name
    canvas.save(target)
    return {'path':str(target.relative_to(ROOT)), 'sha256':sha(target.read_bytes()), 'count':len(rows)}


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    inventory = audit(); catalog = build_catalog(ROOT); assets = catalog['dictionaries']['assets']
    models=[]; model_rows=[]
    for row in inventory['modelsCurrentOrEventReferenced']:
        asset_id = row['asset']
        if asset_id is None:
            models.append((row['id'], None)); model_rows.append({'id':row['id'],'status':'missing'}); continue
        image, digest=pixels_from_asset(assets[asset_id],54,124)
        models.append((row['id']+(' GAP' if not row['specific'] else ''),image))
        model_rows.append({'id':row['id'],'asset':asset_id,'specific':row['specific'],
                           'sourceSha256':assets[asset_id]['content']['sha256'],'pixelSha256':digest})
    flags=[]; flag_rows=[]
    all_countries=sorted(set(inventory['identities']['country']) | {'ll2:country:26'})
    for identity in all_countries:
        country=catalog['dictionaries']['countries'].get(identity); aid=None if country is None else country['references']['mark']
        if aid is None or aid.startswith('spacefox:asset:country-code-'):
            flags.append((identity+' GAP',None)); flag_rows.append({'id':identity,'status':'missing-or-badge'}); continue
        image,digest=pixels_from_asset(assets[aid],20,12)
        flags.append((identity,image.resize((100,60),Image.Resampling.NEAREST)))
        flag_rows.append({'id':identity,'asset':aid,'sourceSha256':assets[aid]['content']['sha256'],'pixelSha256':digest})
    maps=[]; map_rows=[]
    marker=Image.open(ROOT/'watchface/resources/drawables/LaunchMarker.png').convert('RGBA')
    if marker.size!=(28,28):raise ValueError('marker resource dimensions')
    for row in inventory['eventAndAnnouncedSites']:
        identity=row['id']; files={}; dropped=[]
        original=bridge_map.canonical_visual
        def observed(value):
            try: return original(value)
            except ValueError as error:
                if str(error) in ('zero-area wire polygon','duplicate polygon vertex','unsupported self-intersecting fill/polygon') and len(value[6])==1:
                    pool=value[5]; points=[(pool[i]%PACK_BASE,pool[i]//PACK_BASE) for i in value[6][0][2]]
                    xs=[x for x,y in points];ys=[y for x,y in points]
                    dropped.append({'reason':str(error),'boundsQ32':[min(xs),min(ys),max(xs),max(ys)],
                                    'pointsQ32':points})
                raise
        bridge_map.canonical_visual=observed
        try: ref=build_map(ROOT,catalog,identity,files)
        except Exception as error: raise RuntimeError('map cohort failed for '+identity) from error
        finally: bridge_map.canonical_visual=original
        desc=loads_json(files[ref['path']])
        if desc['position'] is None:
            maps.append((identity+' NO POINT',None)); map_rows.append({'id':identity,'position':None,'reason':desc['contextLimits']});continue
        visuals=_map_visuals(files,desc);rgba,_,_=rasterize(visuals,390,390,opaque=True)
        data=bytes(v for i,v in enumerate(rgba) if i%4!=3);encoded=encode_raster(data,390,390,3)
        if decode_raster(encoded,390,390,3)!=data or desc['marker']['anchor']!=[335,165]:raise ValueError('map codec or marker')
        image=Image.frombytes('RGB',(390,390),data).convert('RGBA');image.alpha_composite(marker,(321,151))
        maps.append((identity,image));map_rows.append({'id':identity,'position':desc['position'],'mapPixelSha256':sha(data),'markerAnchor':desc['marker']['anchor'],'shards':len(encoded),'droppedQuantizedCoastStrips':dropped,
                         'droppedBoxAreaUpperBoundPixels':sum((x['boundsQ32'][2]-x['boundsQ32'][0])*(x['boundsQ32'][3]-x['boundsQ32'][1])*(390/(256*32))**2 for x in dropped)})
    sheets={'models':sheet(models,8,(120,165),'models-contact.png'),
            'flags':sheet(flags,4,(160,110),'flags-contact.png'),
            'sites':sheet(maps,6,(130,165),'sites-contact.png')}
    result={'scope':'source-bound raster/codec contact sheets; not native SDK display or worldwide completion',
            'catalogVersion':catalog['catalogVersion'],'inventory':inventory,'models':model_rows,'flags':flag_rows,'maps':map_rows,'sheets':sheets}
    (OUT/'source-pixel-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result


if __name__=='__main__':
    result=run(); print(json.dumps({k:v['count'] for k,v in result['sheets'].items()},sort_keys=True))
