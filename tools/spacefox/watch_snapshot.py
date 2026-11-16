"""Project validated current feed facts once for a compact watch snapshot.

The upstream publisher owns source acquisition and schema validation; the
consumer receives this fixed positional projection. No digest is used here.
"""
from datetime import date
import json

# Order is shared with the native decoder. New values are appended only when
# the publisher and watch are released together.
FIELDS=('id','rocket','operator','operatorShort','purpose','site','modelId',
        'operatorId','siteId','point','target','precision','date',
        'retentionDeadline','orderingUtc','sourceValidated','freshnessPolicy',
        'rescheduled','stale','sourceHold','displayTarget','reminderEligible')

def _row(launch, catalog, policy, selected):
    if launch is None:
        return None
    entries=catalog['entries'];timing=launch['timing']
    def name(key, fallback):
        value=launch.get(key)
        return value if value is not None or not selected else entries.get(launch.get(fallback),{}).get('name')
    rocket=name('configuration_name','configuration_id')
    operator=name('operator_name','operator_id')
    site=launch.get('site_location_name') or launch.get('site_name')
    if site is None and selected: site=entries.get(launch.get('site_id'),{}).get('name')
    if site:
        site=site.split(',',1)[0]
        prefix=(launch.get('operator_name') or '')+' '
        if prefix!=' ' and site.startswith(prefix):site=site[len(prefix):]
    country=launch.get('country_code') or launch.get('country_name')
    if country:site=country+' · '+site if site else country
    short=launch.get('operator_abbrev')
    if selected and short is None:short=entries.get(launch.get('operator_id'),{}).get('abbrev')
    site_data=entries.get(launch.get('site_id'),{}) if selected else None
    pos=(site_data.get('position') if site_data.get('positionMode')=='fixed-source' else None) if selected else launch.get('sitePosition')
    point=None if pos is None else [pos['longitude'],pos['latitude']]
    precision=timing['precision'];target=timing['exact_utc'];display=timing['nominal_utc'] if target is None else None
    if precision=='source-coarse' and timing['source_precision_id']==1 and timing['nominal_utc'] is not None:
        precision='minute';target=timing['nominal_utc']
    elif precision=='source-coarse' and (timing['window_start_utc'] is not None or timing['window_end_utc'] is not None):precision='window'
    ordering=timing['exact_utc']
    if ordering is None:
        ordering=timing['window_start_utc']
        if timing['date_utc'] is not None:
            day=(date.fromisoformat(timing['date_utc'])-date(1970,1,1)).days*86400
            if ordering is None or day>ordering:ordering=day
        if ordering is None:ordering=timing['window_end_utc'] if timing['window_end_utc'] is not None else timing['nominal_utc']
    deadline=None
    if precision in ('exact','minute') and target is not None:
        deadline=target+900;ascent=launch.get('ascent_end')
        if ascent is not None:deadline=max(deadline,ascent['end_utc'])
    reminder=(launch['status']=='pending' and deadline is not None and
              (timing['window_start_utc'] is None or target>=timing['window_start_utc']) and
              (timing['window_end_utc'] is None or target<=timing['window_end_utc']))
    values=(launch['launch_id'],rocket,operator,short,launch['mission_purpose'],site,
            launch['configuration_id'],launch['operator_id'],launch['site_id'],point,target,
            precision,timing['date_utc'],deadline,ordering,launch['source_validated_utc'],policy,
            launch['rescheduled'],launch['stale'],launch.get('source_status_id')==5,display,reminder)
    return list(values)

def snapshot(feed,catalog):
    policy={k:(None if v is None else min(v,315537897600)) for k,v in feed['refreshPolicy'].items()};launch=feed['launch'];upcoming=feed.get('upcoming',[])
    rows=[_row(r,catalog,policy,False) for r in upcoming if 'terminal' not in r]
    terminal=[r for r in upcoming if 'terminal' in r]
    site=catalog['entries'].get(launch['site_id']) if launch and launch['site_id'] else None
    bridge={'version':3,'catalogDigest':feed['catalogDigest'],'selection':feed['visualSelection'],
            'transfer':feed['nativeTransfer'],'site':None if site is None else {'sourcePosition':site['sourcePosition'],'position':site['position'],'positionMode':site['positionMode']},
            'ids':None if launch is None else [launch.get(x) for x in ('launch_id','configuration_id','operator_id','site_id','country_id')]}
    return [1,feed['publisher'],policy,_row(launch,catalog,policy,True),rows,terminal,bridge]

def encode_snapshot(feed,catalog):
    encoded=json.dumps({'data':snapshot(feed,catalog)},ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
    if len(encoded)>8192:raise ValueError('watch snapshot exceeds 8192 bytes')
    return encoded
