"""Reconcile executed current SDK witnesses with their exact product inputs.

These tests parse retained simulator outputs, verify the compiled product and
relevant test/resource bytes, and keep physical/phone claims external. They do
not start a simulator or treat a planned graph entry as an execution result.
"""
import hashlib,json,re,unittest
from pathlib import Path
from tools.run_native_tests import parse_output
from tests.public_proof_inputs import recorded_input, original_source
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'openspec/changes/spacefox-watchface/evidence/watch-refresh-cache-whole/linux-runtime'
F=ROOT/'tests/fixtures/watch_refresh_cache'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def block(source,marker):
 i=source.find(marker)
 if i<0:raise AssertionError('missing native block '+marker)
 start=source.find('{',i);depth=0;quoted=False;escaped=False
 for pos in range(start,len(source)):
  ch=source[pos]
  if quoted:
   if escaped:escaped=False
   elif ch=='\\':escaped=True
   elif ch=='"':quoted=False
  elif ch=='"':quoted=True
  elif ch=='{':depth+=1
  elif ch=='}':
   depth-=1
   if depth==0:return source[i:pos+1]
 raise AssertionError('unterminated native block '+marker)

def method(source,name):return block(source,'function '+name+'(')

def resources():
 refresh=json.loads((F/'packets.json').read_bytes());final=json.loads((E.parent.parent/'final-native-timing-settings/packets.json').read_bytes())
 unresolved=json.loads((F/'unresolved.json').read_bytes());integrity=json.loads((F/'integrity.json').read_bytes());omission=json.loads((F/'omission.json').read_bytes())
 values={'RefreshCatalogInitial':refresh['catalogs']['initial'],'RefreshCatalogDifferent':refresh['catalogs']['different'],
         'FinalCatalog':{'catalog':final['catalog'],'catalogDigest':final['catalogDigest']},
         'OmissionInitial':omission['initial'],'OmissionOmitted':omission['omitted'],
         'IntegrityCatalog':{'catalog':integrity['badCatalog'],'catalogDigest':integrity['badCatalogDigest']},
         'IntegrityNanCatalog':{'catalog':integrity['nanCatalog'],'catalogDigest':integrity['nanCatalogDigest']}}
 for name,value in refresh['packets'].items():values['Refresh'+name.title().replace('_','')]={'raw':value}
 for name in ('exact','invalid'):values['Final'+name.title()]={'raw':final[name]}
 for name,value in unresolved.items():values['Unresolved'+name[0].upper()+name[1:]]={'raw':value}
 for name,value in integrity['packets'].items():values['Integrity'+name[0].upper()+name[1:]]={'raw':value}
 return {name+'.json':sha(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()) for name,value in values.items()}

WITNESS={
 'refreshCacheSequence':('coherent',['RefreshCatalogInitial','RefreshCatalogDifferent','RefreshInitial','RefreshMoved','RefreshRefresh','RefreshWithdrawn','RefreshWithdrawnRefresh','RefreshDifferent']),
 'refreshCacheRefusals':('coherent',['RefreshCatalogInitial','RefreshInitial','RefreshMoved','RefreshUnchanged']),
 'refreshSourceAge':('coherent',['RefreshCatalogInitial','RefreshInitial','RefreshUnchanged']),
 'refreshNamespaces':('coherent',['RefreshCatalogInitial','RefreshInitial','RefreshMoved']),
 'refreshFeedCacheFaults':('coherent',['RefreshCatalogInitial','RefreshInitial','RefreshMoved']),
 'refreshSdkStorage':('coherent',['RefreshCatalogInitial','RefreshInitial','RefreshMoved']),
 'refreshTransferBoundaries':('coherent',[]),
 'refreshNotModifiedCallback':('coherent',['RefreshCatalogInitial','RefreshInitial']),
 'refreshOfflineView':('coherent',['RefreshCatalogInitial','RefreshInitial']),
 'refreshJsonRefusals':('coherent',['RefreshInitial']),
 'refreshUnresolvedSequence':('coherent',['UnresolvedEmpty1','UnresolvedReal2','UnresolvedEmpty3','UnresolvedReal4','UnresolvedEmptyCatalog','UnresolvedRealCatalog','UnresolvedTechnicalCatalog','UnresolvedRealScene','UnresolvedTechnicalScene']),
 'refreshUnresolvedScene':('coherent',['UnresolvedReal2','UnresolvedTechnical1','UnresolvedEmptyCatalog','UnresolvedRealCatalog','UnresolvedTechnicalCatalog','UnresolvedRealScene','UnresolvedTechnicalScene']),
 'moreServiceAcceptAndReplay':('integrity-r2',['RefreshCatalogInitial','RefreshInitial','RefreshMoved']),
 'moreCurrentIntegrity':('integrity-r5',['RefreshCatalogInitial','RefreshInitial','IntegrityCatalog','IntegrityBadSchema','IntegrityMissingId','IntegrityBadIso','IntegrityBadPolicy','IntegrityNegativeId','IntegrityBadGeometry','IntegrityBoolPolicy','IntegrityNegativePolicy']),
 'moreWidePolicy':('integrity-r6',['RefreshCatalogInitial','IntegrityWide']),
 'moreTypedMetadata':('integrity-r5',['RefreshCatalogInitial','RefreshInitial','IntegrityNullId','IntegrityWidePrecision','IntegrityBoolId','IntegrityQuotedId','IntegrityBadUtc']),
 'moreNearLatchReopen':('integrity-r5',['FinalCatalog','FinalExact','IntegrityFinalRefresh']),
 'moreCanonicalCurrent':('integrity-r5',['UnresolvedReal2','IntegrityWide']),
 'moreCorruptRecovery':('integrity-r2',['RefreshCatalogInitial','RefreshInitial','RefreshMoved']),
 'morePublisherFloor':('integrity-r5',['RefreshCatalogInitial','RefreshInitial','IntegrityChangedInstance','IntegrityNullSelection','IntegrityRegressedOrigin']),
 'moreSourceIdentity':('integrity-r5',['RefreshCatalogInitial','RefreshInitial','RefreshMoved']),
 'moreRescheduledStale':('integrity-r5',['RefreshCatalogInitial','RefreshInitial','RefreshMoved']),
 'moreSdkThreeSlots':('integrity-r5',['RefreshCatalogInitial','RefreshCatalogDifferent','RefreshInitial','RefreshMoved','RefreshWithdrawn']),
 'moreOmissionPreservesAge':('integrity-r3',['OmissionInitial','OmissionOmitted']),
 'moreOfflineEmpty':('integrity-r3',[]),
 'moreCurrentIsoLiterals':('integrity-r4',[]),
 'moreSourcedAscent':('integrity-r6',['FinalCatalog','FinalExact','IntegrityAscentGood','IntegrityAscentBadId','IntegrityAscentBadTarget','IntegrityAscentBadEnd','IntegrityAscentBadUrl','IntegrityAscentBadFuture']),
 'moreSourceOnlyReuse':('integrity-r7',['RefreshCatalogInitial','RefreshInitial','RefreshMoved','RefreshRefresh']),
 'moreNonfinitePosition':('integrity-r8',['RefreshCatalogInitial','RefreshInitial','IntegrityNanCatalog','IntegrityNanGeometry']),
 'moreStorageFull':('integrity-r8',['RefreshCatalogInitial','RefreshInitial','RefreshMoved']),
 'moreGenericRenderer':('integrity-r7',['UnresolvedReal2','UnresolvedTechnical1','UnresolvedEmptyCatalog','UnresolvedRealCatalog','UnresolvedTechnicalCatalog','UnresolvedRealScene','UnresolvedTechnicalScene']),
}

# These current builds exercise changed cache/refresh paths. Three parser-only
# assertions retain their original immutable execution because none calls a
# changed owner; see the independent reached-dependency review.
WITNESS['moreMinuteRefresh']=('../independent-minute-r1/native-r10',[])
WITNESS['refreshNearAndClock']=('../independent-minute-r1/native-r10',['FinalCatalog','FinalExact'])
RETAINED_PURE={'refreshJsonRefusals','moreCurrentIsoLiterals','moreCanonicalCurrent'}
for witness,(folder,needed) in tuple(WITNESS.items()):
 if witness not in RETAINED_PURE:WITNESS[witness]=('../independent-minute-r1/native-r10',needed)
CHANGED_NATIVE={'watchface/source/NativeCache.mc','watchface/source/NativeFeed.mc',
                'watchface/source/NativeForegroundApp.mc','watchface/source/NativeForegroundCache.mc'}
BASE='9a5de861940773528ac88e34bd66e5b3ab4e1a82'
INDEPENDENT=E.parent/'independent-minute-r1'

# Current applicability is per named historical witness, not whole-tree equivalence.
# Each route requires its listed unchanged owner methods and a separately observed
# current seam. Original SDK executions remain on their original inputs.
FEED_ROUTE = ('feed', 'test_current_refusals_preserve_state')
CACHE_ROUTE = ('cache', 'test_current_refusals_preserve_state')
FRESH_ROUTE = ('feed', 'test_current_freshness_batch_and_context')
SITE_ROUTE = ('feed', 'test_current_parser_and_site')
WITNESS_ROUTES = {
 'refreshCacheSequence': CACHE_ROUTE, 'refreshCacheRefusals': CACHE_ROUTE,
 'refreshSourceAge': FRESH_ROUTE, 'refreshNamespaces': CACHE_ROUTE,
 'refreshFeedCacheFaults': CACHE_ROUTE, 'refreshSdkStorage': CACHE_ROUTE,
 'refreshTransferBoundaries': ('transfer', 'test_current_304_preserves_source'),
 'refreshOfflineView': SITE_ROUTE, 'refreshJsonRefusals': FEED_ROUTE,
 'refreshUnresolvedSequence': SITE_ROUTE, 'refreshUnresolvedScene': SITE_ROUTE,
 'moreServiceAcceptAndReplay': CACHE_ROUTE, 'moreCurrentIntegrity': FEED_ROUTE,
 'moreWidePolicy': FEED_ROUTE, 'moreTypedMetadata': FEED_ROUTE,
 'moreNearLatchReopen': FRESH_ROUTE, 'moreCanonicalCurrent': FEED_ROUTE,
 'moreCorruptRecovery': CACHE_ROUTE, 'morePublisherFloor': CACHE_ROUTE,
 'moreRescheduledStale': FRESH_ROUTE, 'moreSdkThreeSlots': CACHE_ROUTE,
 'moreOmissionPreservesAge': FRESH_ROUTE, 'moreOfflineEmpty': SITE_ROUTE,
 'moreCurrentIsoLiterals': FEED_ROUTE, 'moreSourcedAscent': FEED_ROUTE,
 'moreSourceOnlyReuse': FRESH_ROUTE, 'moreNonfinitePosition': FEED_ROUTE,
 'moreStorageFull': CACHE_ROUTE, 'moreGenericRenderer': SITE_ROUTE,
 'moreMinuteRefresh': ('transfer', 'test_current_freshness_batch_and_context'),
 'refreshNearAndClock': ('transfer', 'test_current_freshness_batch_and_context'),
}
ROUTE_METHODS = {
 'feed': (('watchface/source/NativeFeed.mc','validate'), ('watchface/source/NativeFeed.mc','metadata'),
          ('watchface/source/NativeFeed.mc','interval'), ('watchface/source/NativeFeed.mc','advance')),
 'cache': (('watchface/source/NativeCache.mc','checkPublisher'), ('watchface/source/NativeCache.mc','rememberPublisher'),
           ('watchface/source/NativeCache.mc','freeSlot')),
 'transfer': (('watchface/source/NativeTransfer.mc','due'), ('watchface/source/NativeTransfer.mc','nextWake')),
}

class CurrentFormatAcceptanceTest(unittest.TestCase):
 _historical_cache = set()
 _route_cache = set()
 _current_ready = False
 @classmethod
 def current_route(cls, name):
  if name == 'refreshNotModifiedCallback':
   route, probe = 'transfer', 'test_current_304_preserves_source'
  else:
   if name not in WITNESS_ROUTES:raise AssertionError('unclassified historical witness: '+name)
   route,probe=WITNESS_ROUTES[name]
  from tests.test_current_data_convergence import CurrentDataConvergenceTest as Current
  if cls._current_ready:
   for path,stamp in Current.input_stamps.items():
    info=Path(path).stat()
    if (info.st_mtime_ns,info.st_size,info.st_ino)!=stamp:
     cls._current_ready=False;cls._route_cache.clear();break
  if not cls._current_ready:
   Current.setUpClass();cls._current_ready=True
  if route not in cls._route_cache:
   comparison=json.loads((ROOT/'openspec/changes/spacefox-watchface/evidence/current-native-data-applicability/method-comparison.json').read_text())
   for path,owner in ROUTE_METHODS[route]:
    row=next(x for x in comparison['rows'] if x['file']==path and x['method']==owner)
    if not row['byte_identical']:raise AssertionError('changed route owner '+path+':'+owner)
    prior=original_source(row['prior']+':'+path,text=True)
    current=(ROOT/path).read_text()
    if sha(method(prior,owner).encode()) != row['old_sha256'] or sha(method(current,owner).encode()) != row['current_sha256']:
     raise AssertionError('route owner differs '+path+':'+owner)
   if route=='feed':
    # These changed owners differ only by removed instrumentation. The exact
    # current source is also checked by Current.setUpClass and current probes.
    for path,owners in (('watchface/source/NativeBridgeFeed.mc',('parse','header')),('watchface/source/NativeJson.mc',('parse',))):
     prior=original_source('b9dbfd26:'+path,text=True);current=(ROOT/path).read_text()
     for owner in owners:
      a=re.sub(r'NativeMetrics\.sample\("[^"]+"\);','',method(prior,owner));b=method(current,owner)
      if re.sub(r'\s+','',a)!=re.sub(r'\s+','',b):raise AssertionError('changed admission method '+path+':'+owner)
   cls._route_cache.add(route)
  key=('probe',probe)
  if key not in cls._route_cache:
   getattr(Current(probe),probe)();cls._route_cache.add(key)
 def source_matches(self,source,digest,*,retained=False,source_head=BASE):
  key=(source,digest)
  if key in self._historical_cache:return
  path=ROOT/source
  if path.is_file() and sha(path.read_bytes())==digest:
   self._historical_cache.add(key);return
  # Original sourceHead is dirty in r10 only for four named files; b9dbfd26
  # contains those exact recorded bytes. The old hash is never rewritten.
  if source in ('tests/fixtures/watch_refresh_cache/Assertions.mc','tests/fixtures/watch_refresh_cache/AdditionalAssertions.mc'):
   saved=ROOT/'openspec/changes/spacefox-watchface/evidence/canonical-current-convergence/historical'/(Path(source).name+'.txt')
   if saved.is_file() and sha(saved.read_bytes())==digest:self._historical_cache.add(key);return
  recorded_input(source,digest)
  self._historical_cache.add(key)
 def observe(self,*names):
  expected_resources=resources()
  for name in names:
   self.current_route(name)
   if name=='refreshNotModifiedCallback':continue
   folder,needed=WITNESS[name];path=E/folder;build=json.loads((path/'build.json').read_text());probe=(path/'Probe.mc').read_text()
   self.assertEqual(sha(probe.encode()),build['probeSha256'],name)
   for source,digest in {**build['productionSources'],**build['productionResources']}.items():self.source_matches(source,digest,retained=name in RETAINED_PURE,source_head=build['sourceHead'])
   fixture=ROOT/'openspec/changes/spacefox-watchface/evidence/canonical-current-convergence/historical'/('AdditionalAssertions.mc.txt' if name.startswith('more') else 'Assertions.mc.txt')
   self.assertEqual(method(probe,name),method(recorded_input(str(fixture.relative_to(ROOT)), {'Assertions.mc.txt': 'ea384b8a5e3aa19196f79e8e13ad4a94a177dc95e3ffd77a2108cf5eb9e2957f', 'AdditionalAssertions.mc.txt': 'dbef385eee10b0181e21a17cb8ef3ea59bbaceddba37cc5d1f43df8278cdfd2f'}[fixture.name]).decode(),name),name)
   if name.startswith('more'):
    self.assertIn(recorded_input('openspec/changes/spacefox-watchface/evidence/canonical-current-convergence/historical/Assertions.mc.txt','ea384b8a5e3aa19196f79e8e13ad4a94a177dc95e3ffd77a2108cf5eb9e2957f').decode(),probe)
    text=recorded_input(str(fixture.relative_to(ROOT)), {'Assertions.mc.txt': 'ea384b8a5e3aa19196f79e8e13ad4a94a177dc95e3ffd77a2108cf5eb9e2957f', 'AdditionalAssertions.mc.txt': 'dbef385eee10b0181e21a17cb8ef3ea59bbaceddba37cc5d1f43df8278cdfd2f'}[fixture.name]).decode();body=method(text,name)
    for helper in ('integrityPacket','ascentPacket'):
     if helper+'(' in body:self.assertEqual(method(probe,helper),method(text,helper),name+':'+helper)
    for helper in ('MoreService','MoreCountingStore','MoreFullStore'):
     if 'new '+helper+'(' in body:self.assertEqual(block(probe,'class '+helper+' '),block(text,'class '+helper+' '),name+':'+helper)

   if 'RefreshCatalogInitial' in needed and 'RefreshCatalogDifferent' not in needed:needed=needed+['RefreshCatalogDifferent']
   for resource in needed:self.assertEqual(build['probeResources'][resource+'.json'],expected_resources[resource+'.json'],name+':'+resource)
   out=(path/(name+'.stdout')).read_text();err=(path/(name+'.stderr')).read_text();code=int((path/(name+'.exit')).read_text())
   self.assertFalse(err,name);self.assertEqual(parse_output(out,code,(name,))['status'],'passed',name)
 def current_ui(self):
  from tests.public_proof_inputs import verify_current_closure
  verify_current_closure(ROOT)  # Live owners are mutable; never cache their identity.
  # DISPLAY03 replaced the old whole-UI source epoch. Do not rerun the old
  # verify_current_ui_batch against changed current owners or repin its hashes.
  # Its original lifecycle observation is read below; current mode/recovery
  # composition has its own source-qualified positive and tamper controls.
  # Retained receipts and their source snapshots are mutable checkout files.
  # Authenticate the composition on every call, including an already-warmed route.
  from tests.test_display03_receipt_binding import Display03ReceiptBindingTest, WF09CurrentCompositionTest
  from tests.retained_native_binding import verify_current
  verify_current()
  Display03ReceiptBindingTest.setUpClass()
  Display03ReceiptBindingTest('test_modes_positive').test_modes_positive()
  Display03ReceiptBindingTest('test_modes_negative').test_modes_negative()
  WF09CurrentCompositionTest('test_recovery_positive').test_recovery_positive()
 def lifecycle(self,*names):
  self.current_ui()
  path=E/'lifecycle';build=json.loads((path/'build.json').read_text());fixture=ROOT/'tests/fixtures/final_design/LifecycleProbe.mc'
  self.assertEqual(build['assertionSha256'],sha(fixture.read_bytes()))
  for source,digest in {**build['productionSources'],**build['productionResources']}.items():self.source_matches(source,digest,retained=True,source_head=build['sourceHead'])
  for name in names:
   self.assertEqual(parse_output((path/(name+'.stdout')).read_text(),int((path/(name+'.exit')).read_text()),(name,))['status'],'passed');self.assertFalse((path/(name+'.stderr')).read_text())
 def near(self):
  self.observe('refreshNearAndClock')
 def minute(self):
  self.observe('moreMinuteRefresh')
  build=json.loads((INDEPENDENT/'native-r10/build.json').read_text())
  for path,digest in build['additionalInputs'].items():self.source_matches(path,digest,source_head=build['sourceHead'])
  from tests.test_minute_refresh import MinuteRefreshTest
  if 'minute-host' not in self._route_cache:
   MinuteRefreshTest('test_captured_minute_cadence_and_slept_through_stale').test_captured_minute_cadence_and_slept_through_stale();self._route_cache.add('minute-host')
  captured=json.loads(json.loads((F/'packets.json').read_text())['packets']['initial'])
  def encoded(doc):return sha(json.dumps({'raw':json.dumps(doc,ensure_ascii=False,sort_keys=True,separators=(',',':'))},ensure_ascii=False,separators=(',',':')).encode())
  captured['launch']['source_validated_utc']=1794602700;captured['publisher']['selectionValidatedUtc']=1794602700
  expected={'IntegrityMinuteNear':captured}
  newer=json.loads(json.dumps(captured));newer['launch']['source_validated_utc']=1794611701;newer['publisher']['selectionValidatedUtc']=1794611701;newer['publisher']['generation']=2;expected['IntegrityMinuteNewer']=newer
  for name,precision in (('Date','date'),('Window','window')):
   other=json.loads(json.dumps(captured));timing=other['launch']['timing'];timing['precision']=precision
   if precision=='date':timing.update(date_utc='2026-11-13',nominal_utc=None,source_net=None,window_start_utc=None,window_end_utc=None)
   other['timingState']='uncertain';expected['IntegrityMinute'+name]=other
  context=json.loads(json.loads((F/'packets.json').read_text())['packets']['initial']);context['launch']['timing']['window_end_utc']=1794614460;context['launch']['source_validated_utc']=1794551193;context['launch']['source_updated_utc']=1794348407;context['launch']['source_updated_iso']='2026-11-10T22:06:47Z';context['publisher']['selectionValidatedUtc']=1794551193;context['publisher']['generation']=2;expected['IntegrityMinuteContext']=context
  for name,doc in expected.items():self.assertEqual(build['probeResources'][name+'.json'],encoded(doc),name)
 def timing(self,*names):
  self.current_ui()
  NATIVE=('clockExactPositive','clockExactNegative','uncertaintyPositive','uncertaintyNegative','offlineWakePositive','offlineWakeNegative','precisionTransitions','emptyStartup','clockAdapterSmoke','formatLocalSettings','finalTimingPositive','finalTimingNegative','finalParserUpdatePositive','finalParserUpdateNegative','finalSettingsPositive','finalSettingsNegative')
  path=INDEPENDENT/'timing';build=json.loads((path/'build.json').read_text())
  for source,digest in {**build['productionSources'],**build['productionResources'],**build['assertionInputs']}.items():self.source_matches(source,digest,source_head=build['sourceHead'])
  self.current_route('moreTypedMetadata')
  from tests.test_current_timing_convergence import CurrentTimingConvergenceTest
  if 'current-paired-timing' not in self._route_cache:
   CurrentTimingConvergenceTest('test_retained_native_countdown_pair_positive').test_retained_native_countdown_pair_positive();self._route_cache.add('current-paired-timing')
  probe=(path/'Probe.mc').read_bytes();self.assertEqual(sha(probe),build['probeSha256'])
  raw=(path/'timing-run.stdout').read_text();self.assertFalse((path/'timing-run.stderr').read_text())
  result=parse_output(raw,int((path/'timing-run.exit').read_text()),NATIVE);self.assertEqual(result['status'],'passed')
  for name in names:self.assertEqual(result['observed_tests'].get(name),'PASS')
 def reschedule(self,name):
  path=INDEPENDENT/'reschedule';row=json.loads((path/'reschedule-observation.json').read_text());build=row['build']
  for source,digest in build['source_sha256'].items():self.source_matches(source,digest,source_head=BASE)
  self.current_route('moreTypedMetadata')
  from tests.test_current_data_convergence import CurrentDataConvergenceTest
  CurrentDataConvergenceTest('test_actual_parser_cache_and_view_reschedule').test_actual_parser_cache_and_view_reschedule()
  self.assertEqual(sha((path/'ReschedulePackets.mc').read_bytes()),build['packets_sha256'])
  result=parse_output((path/'native-tests.log').read_text(),row['raw_exit_code'],('rescheduleMove','rescheduleRefresh','rescheduleWithdraw','rescheduleDifferent'))
  self.assertEqual(result['status'],'passed');self.assertEqual(result['observed_tests'][name],'PASS')
  self.assertEqual((path/'reschedule.exit').read_text().strip(),'0');self.assertIn('Ran 4 tests',(path/'reschedule.stderr').read_text());self.assertIn('\nOK\n',(path/'reschedule.stderr').read_text())
 def producer(self):
  # The retained local 200/304/429 witness has a captured MIN target at
  # 1794609900 and polls no later than NOW+7201, still before T-7200. It
  # never re-admits changed timing content. Only the named near/stale and
  # same-target merge branches changed; all other schedule AST is identical.
  import ast
  testpath='tests/test_schedule_producer_whole.py';oldtest=ast.parse(original_source('e01977de:'+testpath,text=True));newtest=ast.parse((ROOT/testpath).read_text())
  def method_ast(tree,name):return ast.dump(next(x for x in ast.walk(tree) if isinstance(x,ast.FunctionDef) and x.name==name),include_attributes=False)
  self.assertEqual(method_ast(oldtest,'test_local_http_due_origin_304_and_429'),method_ast(newtest,'test_local_http_due_origin_304_and_429'))
  path='tools/spacefox/schedule.py';old=ast.parse(original_source('e01977de:'+path,text=True));new=ast.parse((ROOT/path).read_text())
  def filtered(tree):
   tree.body=[x for x in tree.body if not isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) or x.name not in ('cadence_seconds','_stale','merge_schedule')]
   return ast.dump(tree,include_attributes=False)
  self.assertEqual(filtered(old),filtered(new))
  # The current wire tightened source/selection epochs and catalog projection
  # became selected-only. Compare the exact update owner and its wire delta;
  # current selected-projection and publisher controls are separately executed.
  path='tools/update_feed.py';prior=ast.parse(original_source('e01977de:'+path,text=True));current=ast.parse((ROOT/path).read_text())
  self.assertEqual(method_ast(prior,'update'),method_ast(current,'update'))
  path='tools/spacefox/wire.py';prior=original_source('e01977de:'+path,text=True);current=(ROOT/path).read_text()
  added="        selection_epoch = doc['publisher']['selectionValidatedUtc']\n        if selection_epoch is None or selection_epoch < normalized.source_validated_utc:\n            raise ValueError('selection validation precedes selected source')\n"
  self.assertEqual(current.replace(added,''),prior)
  self.current_route('refreshNotModifiedCallback')
  from tests.test_current_motion_publisher import NOW,captured_starship
  from tools.spacefox.provider import normalize_launch
  target=normalize_launch(captured_starship(),NOW).timing.countdown_utc
  self.assertEqual(target,1794609900);self.assertLess(NOW+7201,target-7200)
  text=(E.parent/'transport/http-304-429.log').read_text();self.assertIn('test_local_http_due_origin_304_and_429',text);self.assertIn('\nOK\n',text)
  current=(INDEPENDENT/'producer-final.log').read_text();self.assertIn('test_captured_minute_cadence_and_slept_through_stale',current);self.assertIn('\nOK\n',current)
 def redraw_sources(self):
  paths=list((ROOT/'watchface/source').rglob('*.mc'));calls=[str(p.relative_to(ROOT)) for p in paths if 'Communications.makeWebRequest' in p.read_text()]
  self.assertEqual(calls,['watchface/source/FeedService.mc'])
  for name in ('SpaceFoxView.mc','SceneRenderer.mc','Fitness.mc','LocalePresentation.mc','FeedScene.mc','ScheduleState.mc','NativeVisualRenderer.mc','NativeSfr.mc'):
   self.assertNotIn('makeWebRequest',(ROOT/'watchface/source'/name).read_text())

 def test_ls02_p1_s02_positive_current(self):
  self.producer();self.observe('refreshNotModifiedCallback','moreServiceAcceptAndReplay')

 def test_ls02_p1_s02_negative_current(self):
  self.producer();self.observe('refreshOfflineView');self.redraw_sources()

 def test_ls02_p1_s03_positive_current(self):
  self.observe('refreshTransferBoundaries');self.near()

 def test_ls02_p1_s03_negative_current(self):
  self.observe('refreshTransferBoundaries');self.near()

 def test_ls02_p3_s01_positive_current(self):
  self.observe('refreshTransferBoundaries','moreNearLatchReopen','refreshCacheSequence');self.near();self.minute()

 def test_ls02_p3_s01_negative_current(self):
  self.observe('refreshTransferBoundaries','moreNearLatchReopen','refreshCacheRefusals');self.near();self.minute()

 def test_ls02_p4_s01_positive_current(self):
  self.observe('refreshOfflineView');self.lifecycle('finalAnimationLifecycle','finalAodMinuteGuard');self.redraw_sources()

 def test_ls02_p4_s01_negative_current(self):
  self.observe('refreshOfflineView');self.lifecycle('finalAnimationLifecycle','finalAodMinuteGuard');self.redraw_sources()

 def test_ls05_p2_s01_positive(self):
  from tests.test_current_data_convergence import CurrentDataConvergenceTest
  CurrentDataConvergenceTest.setUpClass()
  CurrentDataConvergenceTest('test_current_parser_and_site').test_current_parser_and_site()

 def test_ls05_p2_s01_negative(self):
  from tests.test_current_data_convergence import CurrentDataConvergenceTest
  CurrentDataConvergenceTest.setUpClass()
  CurrentDataConvergenceTest('test_current_refusals_preserve_state').test_current_refusals_preserve_state()

 def test_ls05_p5_s01_positive(self):
  self.observe('moreWidePolicy','moreTypedMetadata','moreCanonicalCurrent','moreCurrentIsoLiterals')

 def test_ls05_p5_s01_negative(self):
  self.observe('moreCurrentIntegrity','moreTypedMetadata','moreCurrentIsoLiterals')

 def test_ls05_p5_s02_positive_current(self):
  self.observe('moreTypedMetadata','moreWidePolicy','moreCanonicalCurrent','moreSourceOnlyReuse')

 def test_ls05_p5_s02_negative_current(self):
  self.observe('moreTypedMetadata','moreCurrentIntegrity')

 def test_ls05_p5_s03_positive_current(self):
  self.observe('moreWidePolicy','moreCurrentIsoLiterals','moreSourceOnlyReuse')

 def test_ls05_p5_s03_negative_current(self):
  self.observe('moreCurrentIntegrity','moreCurrentIsoLiterals')

 def test_ls05_p6_s01_positive_current(self):
  self.observe('refreshNamespaces','refreshCacheSequence','moreSourceOnlyReuse')

 def test_ls05_p6_s01_negative_current(self):
  self.observe('refreshCacheRefusals','morePublisherFloor','refreshNamespaces')

 def test_ls05_p7_s01_positive_current(self):
  self.observe('refreshUnresolvedSequence','refreshUnresolvedScene','moreGenericRenderer')

 def test_ls05_p7_s01_negative_current(self):
  self.observe('refreshUnresolvedSequence','refreshUnresolvedScene','moreGenericRenderer')

 def test_ls05_p8_s01_positive_current(self):
  self.observe('moreCanonicalCurrent','moreWidePolicy','refreshSdkStorage')

 def test_ls05_p8_s01_negative_current(self):
  self.observe('refreshJsonRefusals','moreCurrentIntegrity','moreTypedMetadata')

 def test_ls11_p1_s01_positive(self):
  self.observe('refreshSourceAge','moreRescheduledStale')

 def test_ls11_p1_s01_negative(self):
  self.observe('refreshSourceAge','moreRescheduledStale')

 def test_ls11_p1_s02_positive(self):
  self.observe('moreOfflineEmpty')

 def test_ls11_p1_s02_negative(self):
  self.observe('moreOfflineEmpty','refreshUnresolvedSequence')

 def test_ls11_p1_s03_positive(self):
  self.observe('refreshSourceAge','refreshNotModifiedCallback')

 def test_ls11_p1_s03_negative(self):
  self.observe('refreshSourceAge','refreshNotModifiedCallback','moreServiceAcceptAndReplay')

 def test_ls11_p1_s04_positive_current(self):
  self.observe('moreOmissionPreservesAge')

 def test_ls11_p1_s04_negative_current(self):
  self.observe('moreOmissionPreservesAge')

 def test_ls11_p1_s05_positive(self):
  self.observe('moreNearLatchReopen');self.near();self.minute()

 def test_ls11_p1_s05_negative(self):
  self.observe('moreNearLatchReopen');self.near();self.minute()

 def test_ls11_p4_s01_positive_current(self):
  self.observe('refreshFeedCacheFaults','moreCorruptRecovery','moreSdkThreeSlots','moreStorageFull')

 def test_ls11_p4_s01_negative_current(self):
  self.observe('refreshFeedCacheFaults','moreCorruptRecovery','moreCurrentIntegrity','moreStorageFull')

 def test_ls11_p5_s01_positive_current(self):
  self.observe('moreSdkThreeSlots','moreSourceOnlyReuse','refreshNamespaces')

 def test_ls11_p5_s01_negative_current(self):
  self.observe('moreSdkThreeSlots','moreCorruptRecovery','refreshOfflineView')

 def test_ls09_p1_s1_positive(self):
  self.timing('finalTimingPositive','clockExactPositive')

 def test_ls09_p1_s1_negative(self):
  self.timing('finalTimingNegative','clockExactNegative')

 def test_ls09_p1_s2_positive(self):
  self.timing('uncertaintyPositive')

 def test_ls09_p1_s2_negative(self):
  self.timing('uncertaintyNegative','finalTimingNegative')

 def test_ls09_p1_s3_positive(self):
  self.timing('offlineWakePositive','clockAdapterSmoke')

 def test_ls09_p1_s3_negative(self):
  self.timing('offlineWakeNegative','emptyStartup')

 def test_ls09_p1_s4_positive(self):
  self.timing('finalParserUpdatePositive','finalTimingPositive')

 def test_ls09_p1_s4_negative(self):
  self.timing('finalParserUpdateNegative','finalTimingNegative')

 def test_ls10_p1_s01_positive_current(self):
  self.reschedule('rescheduleMove')

 def test_ls10_p1_s01_negative_current(self):
  self.reschedule('rescheduleRefresh')

 def test_ls10_p1_s02_positive_current(self):
  self.reschedule('rescheduleWithdraw')

 def test_ls10_p1_s02_negative_current(self):
  self.reschedule('rescheduleDifferent')
