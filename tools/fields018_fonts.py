#!/usr/bin/env python3
"""Check actual fields018 UI literals against installed SDK fonts and HarfBuzz.

This checks only new user-visible text, not a synthetic Unicode corpus. Native
rendering, Settings UI, physical watch and speaker review remain separate.
"""
import argparse, hashlib, json, os, re, subprocess, sys, unicodedata
from pathlib import Path
from xml.etree import ElementTree as ET
from fontTools.ttLib import TTFont
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.native_finite_display import FONT_FILES

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def arrays(region):
    return [json.loads(match) for match in re.findall(r'\[(?:\s*"(?:[^"\\]|\\.)*"\s*,?)+\]',region)]
def function(source,start,end): return source.split(start,1)[1].split(end,1)[0]
def texts(root):
    result={};folders={'en':'resources','ru':'resources-rus','de':'resources-deu','fr':'resources-fre','es':'resources-spa'}
    for index,locale in enumerate(['en','ru','de','fr','es']):
        menu=json.loads((root/f'watchface/resources/json/FieldMenu{index}.json').read_text())
        weather=json.loads((root/f'watchface/resources/json/FieldWeather{index}.json').read_text())
        status=json.loads((root/f'watchface/resources/json/FieldStatus{index}.json').read_text())
        values=menu['activity']+menu['system']+menu['navigation']+[menu['recent'],menu['current']]+weather['labels']+status['labels']
        rootxml=ET.parse(root/'watchface'/folders[locale]/'strings/strings.xml').getroot()
        values.append(next(e.text for e in rootxml if e.get('id')=='WatchSelected'));result[locale]=values
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);parser.add_argument('--fonts',type=Path,default=Path.home()/'Library/Application Support/Garmin/ConnectIQ/Fonts');args=parser.parse_args()
    targets=texts(ROOT);rows=[];font_hashes={};base=args.fonts/FONT_FILES['RobotoRegular'];base_cmap=set(TTFont(base).getBestCmap())
    for index,locale in enumerate(['en','ru','de','fr','es']):
        obj=json.loads((ROOT/f'watchface/resources/json/Locale{index}.json').read_text());face=obj['face'];font=args.fonts/FONT_FILES[face];face_cmap=set(TTFont(font).getBestCmap());cmap=face_cmap|base_cmap
        font_hashes[face]=sha(font);font_hashes['RobotoRegular']=sha(base);values=targets[locale]
        missing=sorted({ord(c) for text in values for c in text if unicodedata.category(c)!='Cf'}-cmap);shapes=[]
        for value in values:
            chosen=font if set(map(ord,value))<=face_cmap else base
            process=subprocess.run(['hb-shape',str(chosen),value,'--output-format=json'],capture_output=True,text=True,check=True,env={**os.environ,'LC_ALL':'en_US.UTF-8'});glyphs=json.loads(process.stdout)
            if any(g.get('g') in (0,'.notdef') for g in glyphs):raise ValueError('missing shaped glyph: '+locale+' '+value)
            shapes.append({'text':value,'font':chosen.name,'glyphs':glyphs})
        rows.append({'locale':locale,'count':len(values),'missingCodepoints':[f'U+{v:04X}' for v in missing],'shapes':shapes})
    inputs=['tools/fields018_fonts.py','watchface/source/FieldText.mc','watchface/resources/json/fields018.xml']+[f'watchface/resources/json/Field{kind}{i}.json' for kind in ('Menu','Weather','Status') for i in range(5)]+[f'watchface/resources/json/Locale{i}.json' for i in range(5)]+[f'watchface/{folder}/strings/strings.xml' for folder in ('resources','resources-rus','resources-deu','resources-fre','resources-spa')]
    result={'status':'passed' if all(not x['missingCodepoints'] for x in rows) else 'failed','inputs':{name:sha(ROOT/name) for name in inputs},'fonts':font_hashes,'rows':rows,'boundary':'Installed SDK cmap and host HarfBuzz for literal new UI text; native settings, physical and language review remain separate.'}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    if result['status']!='passed':raise SystemExit(1)
    print('PASS fields018 primary literal font coverage',sum(x['count'] for x in rows))
if __name__=='__main__':main()
