# SPDX-License-Identifier: MIT
"""One-packet builder. Do not rerun a finalized sealed packet: IDs are minted once."""
import json,unicodedata,uuid
from pathlib import Path
ROOT=Path(__file__).parent
source=json.loads((ROOT/'source.json').read_text())
limits={'rocket':20,'operator':32,'purpose':32,'site':28}
roles={'steps','energy','heart','stress','calories','battery'}
def label(text):
    text=unicodedata.normalize('NFC',text)
    return {'full':text,'displayLabel':text}
def length(text):
    assert text==unicodedata.normalize('NFC',text)
    assert not any(unicodedata.category(c).startswith('M') for c in text)
    assert '\u200d' not in text
    return len(text)
def numeric(role,value,lang):
    if value is None:return '—'
    if role=='battery':return str(value)+'%'
    if role in ('steps','calories') and value>=1000:
        return f'{value:,}'.replace(',','\u202f') if lang=='ru' else f'{value:,}'
    return str(value)
def countdown(seconds,lang):
    if seconds is None:return 'Время уточняется' if lang=='ru' else 'Time pending'
    d,rest=divmod(seconds,86400);h,rest=divmod(rest,3600);m,s=divmod(rest,60)
    u=('д','ч','м','с') if lang=='ru' else ('d','h','m','s')
    if d:return f'T−{d}{u[0]} {h:02}{u[1]} {m:02}{u[2]}'
    if h:return f'T−{h}{u[1]} {m:02}{u[2]}'
    if m:return f'T−{m}{u[2]} {s:02}{u[3]}'
    return f'T−{s:02}{u[3]}'
scenes=[];expected=[]
for i,payload in enumerate(source['payloads']):
    country=source['countries'][i//2]
    for langindex,language in enumerate(('ru','en')):
        scene_id='scene-'+uuid.uuid4().hex[:20]
        fixture={k:label(payload[j][langindex]) for j,k in enumerate(('rocket','operator','purpose'))}
        site=f'{country[langindex+1]} · '+('Тест ' if language=='ru' else 'Test ')+country[4][langindex]
        fixture['site']=label(site)
        fixture['site']['full']=f'{country[langindex+1]} · '+('синтетическая площадка ' if language=='ru' else 'synthetic test location ')+country[4][langindex]
        fixture['point']=None if i in source['nullPoints'] else country[3][i%2]
        fixture['model']=payload[3]
        rescheduled,stale,time_known=map(bool,source['flags'][i])
        seconds=source['seconds'][i]
        status='tbd' if not time_known else 'both' if rescheduled and stale else 'changed' if rescheduled else 'stale' if stale else 'scheduled'
        field_rows=[{'role':r,'value':v,'displayLabel':numeric(r,v,language)} for r,v in source['fields'][i]]
        scene={'id':scene_id,'language':language,'status':status,'flags':{'rescheduled':rescheduled,'stale':stale,'timeKnown':time_known},'clock':source['clocks'][i],'fixture':fixture,'countdown':{'seconds':seconds,'displayLabel':countdown(seconds,language)},'fields':field_rows}
        for k,limit in limits.items():assert length(fixture[k]['displayLabel'])<=limit,f'label length at private payload {i}: {k}'
        assert length(scene['countdown']['displayLabel'])<=16,f'countdown length at private payload {i}'
        assert time_known==(seconds is not None)
        assert len(field_rows)==4 and len({f['role'] for f in field_rows})==4
        for f in field_rows:
            assert f['role'] in roles and length(f['displayLabel'])<=7
            maximum=99999 if f['role'] in ('steps','calories') else 240 if f['role']=='heart' else 100
            assert f['value'] is None or isinstance(f['value'],int) and 0<=f['value']<=maximum
        hh,mm=scene['clock'].split(':');assert len(hh)==len(mm)==2 and 0<=int(hh)<24 and 0<=int(mm)<60
        scenes.append(scene)
        expected.append({'sceneId':scene_id,'language':language,'requiredDisplay':{'time':scene['clock'],**{k:fixture[k]['displayLabel'] for k in ('rocket','operator','purpose','site')},'countdown':scene['countdown']['displayLabel']},'slots':[{'slot':j,**f} for j,f in enumerate(field_rows)],'indicators':{'exclamation':rescheduled,'cloudOff':stale,'uncertaintyLabel':not time_known},'pointExpected':fixture['point'] is not None,'sourcePoint':fixture['point'],'sourceCountryIso':country[0],'modelExpected':fixture['model'],'mustNotAssertLiftoff':True,'withinDeclaredReadableClass':True,'graphemeLengths':{k:length(fixture[k]['displayLabel']) for k in limits}})
assert len(scenes)==24 and len({s['id'] for s in scenes})==24
assert {s['status'] for s in scenes}=={'scheduled','changed','stale','both','tbd'}
assert len({tuple(s['flags'].values()) for s in scenes})==8
assert {f['role'] for s in scenes for f in s['fields']}==roles
assert any(s['flags']['rescheduled'] and s['flags']['stale'] and (s['countdown']['seconds'] or 0)>86400 for s in scenes)
assert any(s['fixture']['point'] is None for s in scenes)
assert any(f['value'] is None for s in scenes for f in s['fields'])
assert len({tuple(s['fixture']['point']) for s in scenes if s['fixture']['point'] is not None})>=6
for filename,value in [('inputs.json',{'schemaVersion':1,'synthetic':True,'scenes':scenes}),('oracle.json',{'schemaVersion':1,'synthetic':True,'expectedSceneCount':24,'claimBoundary':'Finite synthetic browser semantic/geometry benchmark, not human/native evidence','expected':expected})]:
    (ROOT/filename).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
print('Packet built and class-validated; scene values and IDs withheld.')
