#!/usr/bin/env python3
"""Technical mutations of the captured current producer packet, no new text."""
import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from tools.spacefox.catalog import canonical_bytes
from tools.spacefox.wire import validate_current_feed
out=Path(__file__).resolve().parent
bundle=json.loads((out/'packets.json').read_bytes());base=json.loads(bundle['packets']['initial']);cat=json.loads(bundle['catalogs']['initial']['catalog'])
rows={}
def add(name,value):rows[name]=canonical_bytes(value).decode()
x=copy.deepcopy(base);x['sourceContentRevision']='b'*64;x['publisher']['generation']=2;x['launch']['source_status_id']=9223372036854775808;x['refreshPolicy']['normal_interval_seconds']=9223372036854775808;x['refreshPolicy']['stale_cycles']=9223372036854775808;x['pollIntervalSeconds']=9223372036854775808;add('wide',x)
x=copy.deepcopy(base);x['schemaVersion']=4;add('badSchema',x)
x=copy.deepcopy(base);del x['launch']['launch_id'];add('missingId',x)
x=copy.deepcopy(base);x['launch']['source_updated_iso']='2026-11-10T00:00:00Z';add('badIso',x)
x=copy.deepcopy(base);x['refreshPolicy']['normal_interval_seconds']=900;x['refreshPolicy']['near_interval_seconds']=3600;x['pollIntervalSeconds']=900;add('badPolicy',x)
x=copy.deepcopy(base);x['launch']['source_status_id']=-1;add('negativeId',x)
x=copy.deepcopy(base);x['refreshPolicy']['normal_interval_seconds']=True;add('boolPolicy',x)
x=copy.deepcopy(base);x['refreshPolicy']['normal_interval_seconds']=-1;add('negativePolicy',x)
x=copy.deepcopy(base);x['publisher']['instance']='c'*64;x['publisher']['generation']=2;add('changedInstance',x)
x=copy.deepcopy(base);x['publisher']['selectionValidatedUtc']=None;x['publisher']['generation']=2;add('nullSelection',x)
x=copy.deepcopy(base);x['publisher']['selectionValidatedUtc']=1794551191;x['publisher']['generation']=2;add('regressedOrigin',x)
x=copy.deepcopy(base);x['launch']['source_status_id']=None;add('nullId',x)
x=copy.deepcopy(base);x['launch']['source_status_id']=True;add('boolId',x)
x=copy.deepcopy(base);x['launch']['source_status_id']='8';add('quotedId',x)
x=copy.deepcopy(base);x['launch']['source_validated_utc']=253402300800;add('badUtc',x)
x=copy.deepcopy(base);x['launch']['timing']['source_precision_id']=9223372036854775808;add('widePrecision',x)
final=json.loads((ROOT/'openspec/changes/spacefox-watchface/evidence/final-native-timing-settings/packets.json').read_bytes())
x=json.loads(final['exact']);x['publisher']['generation']+=1;x['publisher']['selectionValidatedUtc']=1794585344;x['launch']['source_validated_utc']=1794585344;add('finalRefresh',x)
x=json.loads(final['exact']);x['publisher']['generation']+=1;x['launch']['ascent_end']={'launch_id':x['launch']['launch_id'],'target_utc':1794583543,'end_utc':1794585343,'source_url':'https://example.invalid/mission/?missionId=technical','reviewed_utc':1794576344};add('ascentGood',x)
for label,change in [('ascentBadId',{'launch_id':'ll2:launch:wrong'}),('ascentBadTarget',{'target_utc':1794583544}),('ascentBadEnd',{'end_utc':1794583542}),('ascentBadUrl',{'source_url':'https://example.invalid:abc/'}),('ascentBadFuture',{'reviewed_utc':1794576346})]:
 y=copy.deepcopy(x);y['launch']['ascent_end'].update(change);add(label,y)

# Existing fixed-position limit: same typed real site, only latitude changes.
c=copy.deepcopy(cat);site=c['entries']['ll2:site:235'];site['position']['latitude']='-91';site['sourcePosition']['latitude']='-91'
rawcat=canonical_bytes(c);h=hashlib.sha256(rawcat).hexdigest();x=copy.deepcopy(base);x['catalogDigest']=h;x['catalogPath']='wire3/catalogs/'+h+'.json';add('badGeometry',x)
for n in ('wide','nullId','widePrecision','finalRefresh','changedInstance','ascentGood'):validate_current_feed(rows[n].encode(),now=1794585344 if n=='finalRefresh' else 1794576345 if n=='ascentGood' else 1794551202)
for n in ('badSchema','missingId','badIso','badPolicy','negativeId','boolId','quotedId','badUtc','boolPolicy','negativePolicy'):
 try:validate_current_feed(rows[n].encode(),now=1794551202)
 except (ValueError, KeyError):continue
 raise ValueError('invalid fixture unexpectedly accepted by producer validator: '+n)
nancat=copy.deepcopy(cat);site=nancat['entries']['ll2:site:235'];site['position']['latitude']='NaN';site['sourcePosition']['latitude']='NaN'
nanraw=canonical_bytes(nancat);nanhash=hashlib.sha256(nanraw).hexdigest();x=copy.deepcopy(base);x['catalogDigest']=nanhash;x['catalogPath']='wire3/catalogs/'+nanhash+'.json';add('nanGeometry',x)
raw=canonical_bytes({'packets':rows,'badCatalog':rawcat.decode(),'badCatalogDigest':h,'nanCatalog':nanraw.decode(),'nanCatalogDigest':nanhash});(out/'integrity.json').write_bytes(raw)
result={'bundleSha256':hashlib.sha256(raw).hexdigest(),'packetSha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in rows.items()},'badCatalogSha256':h,'mutationBoundary':'current producer packet, technical validity fields only; captured display strings unchanged'}
(out/'integrity-oracle.json').write_bytes(canonical_bytes(result));print(json.dumps(result,sort_keys=True))
