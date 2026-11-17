#!/usr/bin/env python3
"""Supplement the current packet probe with bounded integrity/callback cases."""
import hashlib,json
from pathlib import Path
from unittest.mock import patch
from tools import watch_refresh_cache_probe as core
ROOT=core.ROOT
FIXTURE=ROOT/'tests/fixtures/watch_refresh_cache'
NAMES=('moreServiceAcceptAndReplay','moreCurrentIntegrity','moreWidePolicy','moreCorruptRecovery','moreTypedMetadata','moreNearLatchReopen','moreOmissionPreservesAge','moreOfflineEmpty','moreCurrentIsoLiterals','moreCanonicalCurrent','morePublisherFloor','moreSourceIdentity','moreRescheduledStale','moreSdkThreeSlots','moreSourcedAscent','moreSourceOnlyReuse','moreGenericRenderer','moreNonfinitePosition','moreStorageFull','moreMinuteRefresh')

def build(output,*,diagnostic_unqualified=False):
 data=json.loads((FIXTURE/'integrity.json').read_bytes());omission=json.loads((FIXTURE/'omission.json').read_bytes())
 original=core.build_probe
 def add_source(out,source,**kwargs):
  resources=kwargs['probe_resources'];xml=['<resources>']
  values={'IntegrityCatalog':{'catalog':data['badCatalog'],'catalogDigest':data['badCatalogDigest']},'OmissionInitial':omission['initial'],'OmissionOmitted':omission['omitted'],'IntegrityNanCatalog':{'catalog':data['nanCatalog'],'catalogDigest':data['nanCatalogDigest']}}
  values.update({'Integrity'+k[0].upper()+k[1:]:{'raw':v} for k,v in data['packets'].items()})
  # Technical timestamp mutation of the captured MIN record; retain its exact
  # identity/target and catalog while exercising a near-window source epoch.
  captured=json.loads(json.loads((FIXTURE/'packets.json').read_text())['packets']['initial'])
  captured['launch']['source_validated_utc']=1794602700
  captured['publisher']['selectionValidatedUtc']=1794602700
  values['IntegrityMinuteNear']={'raw':json.dumps(captured,ensure_ascii=False,sort_keys=True,separators=(',',':'))}
  context=json.loads(json.loads((FIXTURE/'packets.json').read_text())['packets']['initial'])
  context['launch']['timing']['window_end_utc']=1794614460
  context['launch']['source_validated_utc']=1794551193
  context['launch']['source_updated_utc']=1794348407;context['launch']['source_updated_iso']='2026-11-10T22:06:47Z'
  context['publisher']['selectionValidatedUtc']=1794551193;context['publisher']['generation']=2
  values['IntegrityMinuteContext']={'raw':json.dumps(context,ensure_ascii=False,sort_keys=True,separators=(',',':'))}

  refreshed=json.loads(json.dumps(captured));refreshed['launch']['source_validated_utc']=1794611701
  refreshed['publisher']['selectionValidatedUtc']=1794611701;refreshed['publisher']['generation']=2
  values['IntegrityMinuteNewer']={'raw':json.dumps(refreshed,ensure_ascii=False,sort_keys=True,separators=(',',':'))}
  for name,precision in (('Date','date'),('Window','window')):
   other=json.loads(json.dumps(captured));timing=other['launch']['timing'];timing['precision']=precision
   if precision=='date':
    timing.update(date_utc='2026-11-13',nominal_utc=None,source_net=None,window_start_utc=None,window_end_utc=None)
   other['timingState']='uncertain'
   values['IntegrityMinute'+name]={'raw':json.dumps(other,ensure_ascii=False,sort_keys=True,separators=(',',':'))}


  for name,value in values.items():
   raw=json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()
   if len(raw)>8192:raise ValueError('integrity resource too large '+name)
   resources[name+'.json']=raw;xml.append('<jsonData id="'+name+'" filename="'+name+'.json"/>')
  resources['integrity.xml']=(''.join(xml)+'</resources>').encode()
  return original(out,source+'\n'+(FIXTURE/'NativeSourceTimes.mc').read_text()+'\n'+(FIXTURE/'AdditionalAssertions.mc').read_text(),**kwargs)
 with patch.object(core,'build_probe',add_source),patch.object(core,'NAMES',NAMES):
  result=core.build(output,diagnostic_unqualified)
 result['additionalInputs']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (FIXTURE/'AdditionalAssertions.mc',FIXTURE/'NativeSourceTimes.mc',FIXTURE/'integrity.json',FIXTURE/'integrity-oracle.json',FIXTURE/'build_integrity.py',FIXTURE/'omission.json',FIXTURE/'build_omission.py',Path(__file__).resolve())}
 (output/'build.json').write_text(json.dumps(result,indent=2)+'\n');return result
