#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Rebuild public native resources; no private workflow/SDK required.
Python3.14, Pillow13.0.0, fonttools4.68.0, brotli1.2.1 and Node are pinned.
Only existing licensed woff2/PNG/Natural Earth sources are inputs. No live data.
Prepared map views are bundled fallbacks, never downloaded-asset qualification.
"""
from pathlib import Path
import hashlib,io,json,math,shutil,subprocess,tempfile
import PIL,fontTools,brotli
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from fontTools.ttLib import TTFont
ROOT=Path(__file__).resolve().parents[1];RES=ROOT/'watchface/resources';GEN=ROOT/'watchface/source/generated'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rid(s):return ''.join(c if c.isalnum() else '_' for c in s)
def font(name,size,files,characters):
 loaded=[]
 for f in files:
  tt=TTFont(ROOT/'prototype/fonts'/f);tt.flavor=None;b=io.BytesIO();tt.save(b);b.seek(0);loaded.append((ImageFont.truetype(b,size),tt.getBestCmap()))
 width=512;x=y=row=0;glyphs=[];im=Image.new('RGBA',(width,2048));draw=ImageDraw.Draw(im);base=round(size*.9)
 for ch in sorted(set(characters)):
  source=next(((f,cmap)for f,cmap in loaded if ord(ch)in cmap),None)
  if source is None:raise ValueError(f'missing real font glyph {ch!r} U+{ord(ch):04X}')
  f,_=source;features=['tnum'] if name in ['Time80','Metric32','Count31','Aod40'] else [];l,t,r,b=f.getbbox(ch,anchor='ls',features=features);w=max(1,r-l);h=max(1,b-t)
  if x+w+2>width:x=0;y+=row+2;row=0
  draw.text((x-l,y-t),ch,font=f,fill='white',anchor='ls',features=features);glyphs.append((ord(ch),x,y,w,h,l,base+t,round(f.getlength(ch,features=features))-(1 if name=='Time80' else 0)));x+=w+2;row=max(row,h)
 im=im.crop((0,0,width,2**math.ceil(math.log2(max(1,y+row+2)))));directory=RES/'fonts';directory.mkdir(parents=True,exist_ok=True);
 if name == 'Aod40':
  alpha=im.getchannel('A');from PIL import ImageChops
  edge=ImageChops.subtract(alpha,alpha.filter(ImageFilter.MinFilter(3)));im.putalpha(edge)
 coverage=im.getchannel('A')
 im=Image.merge('RGB',(coverage,coverage,coverage))
 im.save(directory/(name+'.png'))
 lines=[f'info face="{name}" size={round(size)} bold=0 italic=0 charset="" unicode=1 stretchH=100 smooth=1 aa=1 padding=0,0,0,0 spacing=0,0',f'common lineHeight={round(size*1.12)} base={base} scaleW={width} scaleH={im.height} pages=1 packed=0',f'page id=0 file="{name}.png"',f'chars count={len(glyphs)}']
 for n,x,y,w,h,l,t,a in glyphs:lines.append(f'char id={n} x={x} y={y} width={w} height={h} xoffset={l} yoffset={t} xadvance={a} page=0 chnl=15')
 (directory/(name+'.fnt')).write_text('\n'.join(lines)+'\n')
 return {'name':name,'em_pixels':size,'glyphs':[g[0]for g in glyphs],'atlas_size':im.size}

def main():
 observed={'Pillow':PIL.__version__,'fonttools':fontTools.__version__,'brotli':brotli.__version__}
 expected={'Pillow':'13.0.0','fonttools':'4.68.0','brotli':'1.2.1'}
 if observed!=expected:raise RuntimeError('Resource builder dependency drift: '+repr(observed)+'; install tools/native-resources-requirements.txt in an isolated venv')
 expected_fonts=json.loads((ROOT/'prototype/fonts/manifest.json').read_text())['fonts']
 for entry in expected_fonts:
  if sha(ROOT/'prototype/fonts'/entry['file'])!=entry['sha256']:raise ValueError('Licensed source font digest drift: '+entry['file'])
 RES.mkdir(exist_ok=True);GEN.mkdir(exist_ok=True);catalog=json.loads((ROOT/'assets/rocket-pack/catalog.json').read_text());drawables=['<drawables>','<bitmap id="LauncherIcon" filename="launcher.png"/>'];models=[]
 for a in catalog['models']:
  p=ROOT/'assets/rocket-pack'/a['png']['path'];assert sha(p)==a['png']['sha256'];dest=RES/'drawables'/('art_'+a['id']+'.png');shutil.copyfile(p,dest);identity='Art_'+rid(a['id']);drawables.append(f'<bitmap id="{identity}" filename="{dest.name}"/>')
  models.append(f'"{a["id"]}" => new NativeModel(Rez.Drawables.{identity})')
 # Neutral fallback has no vehicle or country mark and asserts no launch identity.
 renderer=shutil.which('rsvg-convert')
 if not renderer:raise RuntimeError('Public dependency rsvg-convert2.57.0 is required; no automatic installation')
 unknown=ROOT/'watchface/resource-inputs/art-unknown.svg'
 (RES/'drawables/art_unknown.png').write_bytes(subprocess.check_output([renderer,'-w','54','-h','124',str(unknown)]))
 drawables.append('<bitmap id="Art_unknown" filename="art_unknown.png"/>')
 chars=''.join(chr(i)for i in range(32,127))+''.join(chr(i)for i in range(0x410,0x450))+'Ёё—…·–'
 fonts=[font('Aod40',40,['RobotoCondensed-latin-600.woff2'],'0123456789:'),font('Time80',83.3737,['BarlowSemiCondensed-latin-600.woff2'],'0123456789:'),font('Metric32',38,['RobotoCondensed-latin-600.woff2','NotoSans-latin-500.woff2'], '0123456789 ,—%.…'),font('Label21',21,['NotoSans-latin-500.woff2','NotoSans-cyrillic-500.woff2'],chars),font('Label17',17.2,['NotoSans-latin-500.woff2','NotoSans-cyrillic-500.woff2'],chars),font('Battery13',15,['NotoSans-latin-500.woff2'],'0123456789%—'),font('Count31',31,['RobotoCondensed-latin-600.woff2','NotoSans-cyrillic-500.woff2','NotoSans-latin-500.woff2'],chars+'−')]
 (RES/'fonts/fonts.xml').write_text('<fonts>\n'+''.join(f'<font id="{f["name"]}" filename="{f["name"]}.fnt" antialias="true"/>\n'for f in fonts)+'</fonts>\n')
 points=json.loads((ROOT/'watchface/resource-inputs/map-views.json').read_text())['points']
 with tempfile.NamedTemporaryFile('w',suffix='.json')as temp:
  json.dump(points,temp);temp.flush();maps=json.loads(subprocess.check_output(['node',str(ROOT/'tools/native_map_paths.js'),temp.name]))
 entries=[]
 for i,m in enumerate(maps):
  scale=4
  im=Image.new('RGBA',(390*scale,390*scale),(16,44,67,255));draw=ImageDraw.Draw(im)
  for polygon in m['polygons']:
   if len(polygon)>=3:draw.polygon([(round(x*scale),round(y*scale))for x,y in polygon],fill=(57,127,154,255),outline=(132,186,208,255),width=round(.65*scale))
  grid=Image.new('RGBA',im.size);gd=ImageDraw.Draw(grid)
  for line in m['grid']:
   if len(line)>=2:gd.line([(round(x*scale),round(y*scale))for x,y in line],fill=(85,132,154,round(.18*255)),width=round(.65*scale))
  im=Image.alpha_composite(im,grid).resize((390,390),Image.Resampling.LANCZOS).convert('RGB')
  px=im.load()
  def interp(z,stops):
   for (a,v),(b,w)in zip(stops,stops[1:]):
    if z<=b:return v+(w-v)*(z-a)/(b-a)
   return stops[-1][1]
  for y in range(390):
   for x in range(390):
    fade=.85*interp(x/389,[(0,.06),(.25,.22),(.60,.68),(1,1)])*interp(y/389,[(0,.06),(.18,.55),(.40,1),(.65,.9),(1,.04)])
    px[x,y]=tuple(round(a*fade)for a in px[x,y])
  name=f'MapView{i}';im.quantize(colors=256,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).save(RES/'drawables'/(name+'.png'));drawables.append(f'<bitmap id="{name}" filename="{name}.png"/>');entries.append(f'new NativeMap({m["point"][0]},{m["point"][1]},Rez.Drawables.{name})')
 renderer=shutil.which('rsvg-convert')
 if not renderer:raise RuntimeError('Public dependency rsvg-convert2.57.0 is required for accepted SVG icon paths; no automatic installation')
 version=subprocess.check_output([renderer,'--version'],text=True).strip()
 if version!='rsvg-convert version 2.57.0':raise RuntimeError('SVG renderer dependency drift: '+version)
 marker_svg=subprocess.check_output(['node',str(ROOT/'tools/native_marker_svg.js')])
 marker_png=subprocess.check_output([renderer],input=marker_svg)
 (RES/'drawables/LaunchMarker.png').write_bytes(marker_png)
 drawables.append('<bitmap id="LaunchMarker" filename="LaunchMarker.png"/>')
 import re
 icon_source=(ROOT/'prototype/qualification/renderer.js').read_text()
 icon_block=icon_source.split('const icons={',1)[1].split('};',1)[0]
 icon_entries=[]
 for role,body in re.findall(r"(\w+):'([^']*)'",icon_block):
  svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="18" height="22" viewBox="0 0 24 24"><g fill="none" stroke="#d4dfeb" stroke-width="1.8">{body}</g></svg>'
  image=Image.open(io.BytesIO(subprocess.check_output([renderer],input=svg.encode()))).convert('RGBA')
  alpha=image.getchannel('A');shadow=Image.new('RGBA',image.size);shadow.putalpha(alpha.filter(ImageFilter.GaussianBlur(.5)));image=Image.alpha_composite(shadow,image)
  identity='Metric_'+role;name=identity+'.png';image.save(RES/'drawables'/name);drawables.append(f'<bitmap id="{identity}" filename="{name}"/>');icon_entries.append(f'"{role}"=>Rez.Drawables.{identity}')
 (RES/'drawables/drawables.xml').write_text('\n'.join(drawables+['</drawables>'])+'\n')
 (GEN/'NativeAssets.mc').write_text('// Generated by public tools/build_native_resources.py; catalog-driven, MIT.\nimport Toybox.Lang;\nmodule NativeAssets {\n var models as Dictionary<String, NativeModel> = {'+','.join(models)+'};\n var maps as Array<NativeMap> =['+','.join(entries)+'];\n var icons as Dictionary<String,ResourceId> = {'+','.join(icon_entries)+'};\n}\n')
 try:
  from tools.build_native_localization import generate
 except ImportError:
  from build_native_localization import generate
 generate(ROOT)
 manifest={'schema':1,'builder':'tools/build_native_resources.py','dependencies':{'Pillow':'13.0.0','fonttools':'4.68.0','brotli':'1.2.1'},'svg_renderer':version,'marker_source_sha256':sha(ROOT/'prototype/marker/renderer.js'),'marker_exporter_sha256':sha(ROOT/'tools/native_marker_svg.js'),'metric_icon_source_sha256':sha(ROOT/'prototype/qualification/renderer.js'),'unknown_art_source_sha256':sha(unknown),'unknown_art_png_sha256':sha(RES/'drawables/art_unknown.png'),'fonts':fonts,'font_sources':{str(p.relative_to(ROOT)):sha(p)for p in sorted((ROOT/'prototype/fonts').glob('*.woff2'))},'map_views_sha256':sha(ROOT/'watchface/resource-inputs/map-views.json'),'catalog_sha256':sha(ROOT/'assets/rocket-pack/catalog.json'),'bundled_prepared_map_points':points,'proof_boundary':'Bundled prepared fallback views only; no native arbitrary geography, remote download, transport or full36locale qualification.'}
 (RES/'resource-build.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':main()
