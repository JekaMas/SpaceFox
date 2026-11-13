#!/usr/bin/env python3
"""Generate allocation-free Unicode17 property predicates from normative UCD.
Data are test/build inputs; no SDK font binaries are distributed.
"""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'tests/fixtures/native_localization/unicode17'
def read(name):
 for line in (DATA/name).read_text().splitlines():
  raw=line.split('#')[0].strip()
  if not raw:continue
  parts=[s.strip() for s in raw.split(';')];span=parts[0].split('..');yield int(span[0],16),int(span[-1],16),parts[1:]
def predicate(name,ranges):
 # Binary code tree bounds evaluation cost and keeps heap allocations at zero.
 ranges=sorted(ranges)
 def tree(rs):
  if not rs:return 'return false;'
  a,b=rs[len(rs)//2];lo=rs[:len(rs)//2];hi=rs[len(rs)//2+1:]
  return 'if(c<'+hex(a)+'){'+tree(lo)+'}if(c<='+hex(b)+'){return true;}'+tree(hi)
 return ' function '+name+'(c) { '+tree(ranges)+' }\n'
def generate():
 groups={x:[] for x in ['extend','spacing','prepend','control','pictographic','incbConsonant','incbExtend','incbLinker']}
 props={'Extend':'extend','SpacingMark':'spacing','Prepend':'prepend','Control':'control','CR':'control','LF':'control'}
 for a,b,p in read('GraphemeBreakProperty.txt'):
  if p[0] in props:groups[props[p[0]]].append((a,b))
 for a,b,p in read('emoji-data.txt'):
  if p[0]=='Extended_Pictographic':groups['pictographic'].append((a,b))
 for a,b,p in read('DerivedCoreProperties.txt'):
  if p[0]=='InCB' and p[1] in ['Consonant','Extend','Linker']:groups['incb'+p[1]].append((a,b))
 hangul=' function hangul(a,b){var al=(a>=0x1100&&a<=0x115f)||(a>=0xa960&&a<=0xa97c);var bl=(b>=0x1100&&b<=0x115f)||(b>=0xa960&&b<=0xa97c);var av=(a>=0x1160&&a<=0x11a7)||(a>=0xd7b0&&a<=0xd7c6);var bv=(b>=0x1160&&b<=0x11a7)||(b>=0xd7b0&&b<=0xd7c6);var at=(a>=0x11a8&&a<=0x11ff)||(a>=0xd7cb&&a<=0xd7fb);var bt=(b>=0x11a8&&b<=0x11ff)||(b>=0xd7cb&&b<=0xd7fb);var asyl=a>=0xac00&&a<=0xd7a3;var bsyl=b>=0xac00&&b<=0xd7a3;return al&&(bl||bv||bsyl)||(av||asyl&&(a-0xac00)%28==0)&&(bv||bt)||(at||asyl&&(a-0xac00)%28!=0)&&bt;}'
 import base64,json
 def points(rs):return {c for a,b in rs for c in range(a,b+1)}
 assert points(groups['incbExtend'])==(points(groups['extend'])-{0x200c}-points(groups['incbLinker']))|{0x200d}
 del groups['incbExtend']
 data=bytearray();methods=[' function incbExtend(c){return c==0x200d||(extend(c)&&c!=0x200c&&!incbLinker(c));}'];counts={}
 for name,rs in groups.items():
  merged=[]
  for a,b in sorted(rs):
   if merged and a<=merged[-1][1]+1:merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
   else:merged.append((a,b))
  offset=len(data);counts[name]=len(merged)
  previous=0
  for a,b in merged:
   for n in [a-previous,b-a]:
    while n>=128:data.append((n&127)|128);n>>=7
    data.append(n)
   previous=a
  methods.append(' function '+name+'(c){return contains('+str(offset)+','+str(len(merged))+',c);}')
 out='// Generated Unicode17 UAX29 compact ranges; see pinned normative fixtures.\nimport Toybox.WatchUi;import Toybox.StringUtil;\n(:extendedCode, :typecheck(false)) module LocaleGraphemes {\n var data=null;\n function load(){if(data==null){var encoded=WatchUi.loadResource(Rez.JsonData.GraphemeProperties);data=StringUtil.convertEncodedString(encoded,{:fromRepresentation=>StringUtil.REPRESENTATION_STRING_BASE64,:toRepresentation=>StringUtil.REPRESENTATION_BYTE_ARRAY});}}\n function contains(offset,count,c){var p=offset;var start=0;for(var i=0;i<count;i+=1){var shift=0;var delta=0;var b=0;do{b=data[p];p+=1;delta|=(b&127)<<shift;shift+=7;}while(b>=128);start+=delta;if(start>c){return false;}shift=0;var length=0;do{b=data[p];p+=1;length|=(b&127)<<shift;shift+=7;}while(b>=128);if(c<=start+length){return true;}}return false;}\n'+'\n'.join(methods)+hangul+'\n}\n'
 (ROOT/'watchface/source/generated/LocaleGraphemes.mc').write_text(out)
 resource=ROOT/'watchface/resources/json'
 (resource/'GraphemeProperties.json').write_text(json.dumps(base64.b64encode(data).decode())+'\n')
 (resource/'graphemes.xml').write_text('<resources><jsonData id="GraphemeProperties" filename="GraphemeProperties.json"/></resources>\n')
 print('Compact Unicode bytes',len(data),counts)
if __name__=='__main__':generate()
