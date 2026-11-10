"""Reviewer-owned synthetic holdout. Do not inspect before candidate freeze."""
from pathlib import Path
import json
import hashlib
import unicodedata
import uuid

ROOT = Path(__file__).resolve().parent

# These are deliberate mathematical test locations, not asserted real pads.
points = [(160.0,82.0),(-130.0,60.0),(35.0,-2.0),(179.5,-52.0),(-179.5,24.0),(70.0,-78.0)]
sites = [
    ('Тест Полюс · Мыс Аврора','Test Polar · Aurora Cape'),
    ('Тест Восток · Плато Янтарь','Test East · Amber Plateau'),
    ('Тест Центр · Долина Маяк','Test Central · Beacon Vale'),
    ('Тест Юг · Остров Каскад','Test South · Cascade Isle'),
    ('Тест Запад · Порт Вега','Test West · Vega Harbour'),
    ('Тест Дата · Берег Орбита','Test Date · Orbit Shore'),
]

# Values are strings for typography/semantic testing. The combinations are
# fictional and are not a real launch manifest or a provider attribution claim.
payloads = [
    dict(rocket=('Falcon 9 Block 5','Falcon 9 Block 5'), operator=('SpaceX','SpaceX'), purpose=('Доставка научного аппарата','Science spacecraft delivery'), model='generic'),
    dict(rocket=('Electron','Electron'), operator=('Rocket Lab','Rocket Lab'), purpose=('Карта радиационного фона','Radiation environment mapping'), model='electron'),
    dict(rocket=('Atlas V 551','Atlas V 551'), operator=('United Launch Alliance','United Launch Alliance'), operatorDisplay=('ULA','ULA'), purpose=('Снабжение экипажа','Crew resupply'), model='generic'),
    dict(rocket=('Союз-2.1б/Фрегат','Soyuz-2.1b/Fregat'), operator=('Главкосмос','Glavkosmos'), purpose=('Передача данных с орбиты','Orbital data relay'), model='generic'),
    dict(rocket=('H3-22S','H3-22S'), operator=('Mitsubishi Heavy Industries','Mitsubishi Heavy Industries'), operatorDisplay=('MHI','MHI'), purpose=('Полярная климатическая съёмка','Polar climate survey'), model='generic'),
    dict(rocket=('Ariane 62','Ariane 62'), operator=('Arianespace','Arianespace'), purpose=('Навигационный резерв','Navigation backup'), model='ariane'),
    dict(rocket=('Neutron','Neutron'), operator=('Rocket Lab','Rocket Lab'), purpose=('Отработка возврата ступени','Stage return demonstration'), model='generic'),
    dict(rocket=('Vega-C','Vega-C'), operator=('Avio','Avio'), purpose=('Радиолокационная съёмка','Radar imaging mission'), model='generic'),
    dict(rocket=('New Shepard','New Shepard'), operator=('Blue Origin','Blue Origin'), purpose=('Короткий научный полёт','Suborbital science flight'), model='generic'),
    dict(rocket=('Minotaur IV','Minotaur IV'), operator=('Northrop Grumman','Northrop Grumman'), purpose=('Проверка связи спутников','Satellite link verification'), model='generic'),
    dict(rocket=('Falcon 9','Falcon 9'), operator=('SpaceX','SpaceX'), purpose=('Испытание орбитального буксира','Orbital tug test'), model='falcon'),
    dict(rocket=('Northstar Mk III','Northstar Mk III'), operator=('Northstar Launch Systems','Northstar Launch Systems'), purpose=('Проверка нового теплозащитника','Thermal shield qualification'), model='generic'),
]

states = [
    ('scheduled',False,False,True),('changed',True,False,True),
    ('stale',False,True,True),('both',True,True,True),
    ('tbd',True,False,False),('tbd',False,False,False),
    ('scheduled',False,False,True),('changed',True,False,True),
    ('stale',False,True,True),('both',True,True,True),
    ('both',True,True,True),('tbd',True,True,False),
]
clocks = ['00:00','23:59','08:08','10:10','11:11','20:02','22:22','06:50','15:45','19:07','09:30','16:16']
counts = [
    (38*86400+17*3600+42*60,'T−38д 17ч 42м','T−38d 17h 42m'),
    (2*86400+23*3600,'T−2д 23ч','T−2d 23h'),
    (11*3600+59*60,'T−11ч 59м','T−11h 59m'),
    (9*60+7,'T−9м 07с','T−9m 07s'),
    (None,'Время уточняется','Time pending'),
    (None,'Время уточняется','Time pending'),
    (41*86400+19*3600,'T−41д 19ч','T−41d 19h'),
    (19*3600+3*60,'T−19ч 03м','T−19h 03m'),
    (3*86400+12*3600,'T−3д 12ч','T−3d 12h'),
    (0,'T−00с','T−00s'),
    (86400,'T−1д 00ч','T−1d 00h'),
    (None,'Время уточняется','Time pending'),
]
fields = [
    [('steps',99999),('calories',88888),('heart',199),('battery',100)],
    [('energy',100),('heart',40),('stress',0),('battery',1)],
    [('calories',12345),('steps',54321),('energy',0),('stress',99)],
    [('heart',220),('battery',0),('steps',1),('calories',1)],
    [('stress',100),('energy',1),('battery',99),('heart',88)],
    [('calories',None),('steps',9999),('heart',72),('energy',66)],
    [('energy',99),('steps',10000),('calories',9999),('battery',100)],
    [('battery',9),('stress',87),('heart',155),('steps',25000)],
    [('calories',31415),('energy',42),('battery',42),('heart',99)],
    [('steps',88888),('battery',88),('stress',88),('calories',8888)],
    [('heart',200),('calories',22222),('steps',22222),('energy',100)],
    [('battery',100),('energy',100),('stress',100),('heart',100)],
]

def label(full,display=None):
    return {'full':unicodedata.normalize('NFC',full),'displayLabel':unicodedata.normalize('NFC',display if display is not None else full)}

def numeric_display(role,value,language):
    if value is None:return '—'
    if role=='battery':return str(value)+'%'
    if role in ('steps','calories') and value>=1000:
        return f'{value:,}'.replace(',','\u202f') if language=='ru' else f'{value:,}'
    return str(value)

def graphemes(text):
    assert text==unicodedata.normalize('NFC',text)
    assert not any(unicodedata.category(char).startswith('M') for char in text)
    assert '\u200d' not in text
    return len(text)

scenes=[];expectations=[]
for i,payload in enumerate(payloads):
    for lang_index,language in enumerate(('ru','en')):
        id='holdout-'+uuid.uuid4().hex[:16]
        status,rescheduled,stale,time_known=states[i]
        fixture={key:label(payload[key][lang_index],payload.get(key+'Display',payload[key])[lang_index]) for key in ('rocket','operator','purpose')}
        fixture['site']=label(sites[i//2][lang_index])
        fixture['point']=None if i==11 else list(points[i//2])
        fixture['model']=payload['model']
        field_rows=[{'role':role,'value':value,'displayLabel':numeric_display(role,value,language)} for role,value in fields[i]]
        scene={'id':id,'language':language,'status':status,'flags':{'rescheduled':rescheduled,'stale':stale,'timeKnown':time_known},'clock':clocks[i],'fixture':fixture,'countdown':{'seconds':counts[i][0],'displayLabel':counts[i][lang_index+1]},'fields':field_rows}
        scenes.append(scene)
        limits={'rocket':20,'operator':32,'purpose':32,'site':28}
        lengths={key:graphemes(fixture[key]['displayLabel']) for key in limits}
        assert all(lengths[key]<=limit for key,limit in limits.items())
        assert all(graphemes(fixture[key]['full'])<=limits[key] for key in ('rocket','operator','purpose'))
        expectations.append({'sceneId':id,'language':language,'requiredDisplay':{'time':scene['clock'],'rocket':fixture['rocket']['displayLabel'],'operator':fixture['operator']['displayLabel'],'purpose':fixture['purpose']['displayLabel'],'site':fixture['site']['displayLabel'],'countdown':scene['countdown']['displayLabel']},'slots':[{'slot':index,'role':f['role'],'value':f['value'],'displayLabel':f['displayLabel']} for index,f in enumerate(field_rows)],'indicators':{'exclamation':rescheduled,'cloudOff':stale,'uncertaintyLabel':not time_known},'pointExpected':fixture['point'] is not None,'sourcePoint':fixture['point'],'modelExpected':fixture['model'],'mustNotAssertLiftoff':True,'withinDeclaredReadableClass':True,'graphemeLengths':lengths})

assert len(scenes)==24 and len(set(s['id'] for s in scenes))==24
assert len({tuple(s['fixture']['point']) for s in scenes if s['fixture']['point'] is not None})>=6
assert {s['status'] for s in scenes}=={'scheduled','changed','stale','both','tbd'}
assert {f['role'] for s in scenes for f in s['fields']}=={'steps','energy','heart','stress','calories','battery'}
assert any(f['value'] is None for s in scenes for f in s['fields'])
assert any(s['fixture']['point'] is None for s in scenes)
assert all(len(s['fields'])==4 for s in scenes)
assert all(len(s['clock'])==5 and 0<=int(s['clock'][:2])<24 and 0<=int(s['clock'][3:])<60 for s in scenes)
assert all(s['countdown']['seconds'] is None if not s['flags']['timeKnown'] else s['countdown']['seconds']>=0 for s in scenes)

inputs={'schemaVersion':1,'synthetic':True,'scenes':scenes}
oracle={'schemaVersion':1,'synthetic':True,'claimBoundary':'Display labels are the exact producer-approved onscreen strings; this is a browser geometry/semantic holdout, not human or native-device validation.','expectedSceneCount':24,'expected':expectations}
for filename,value in [('inputs.json',inputs),('oracle.json',oracle)]:
    (ROOT/filename).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
seal={'schemaVersion':1,'status':'sealed-before-candidate-freeze','files':{}}
for filename in ['inputs.json','oracle.json','schema.md','protocol.md','build_holdout.py']:
    blob=(ROOT/filename).read_bytes();seal['files'][filename]={'sha256':hashlib.sha256(blob).hexdigest(),'bytes':len(blob)}
(ROOT/'SEAL.json').write_text(json.dumps(seal,indent=2)+'\n')
print('Prepared and internally validated sealed holdout; contents and hashes withheld.')
