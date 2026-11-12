"""Production producer/Git/HTTP boundaries; literal independent identity/age oracles.

LL2/Pages are replaced only by local HTTP or a forbidden-call guard. No native,
physical device, authentic Pages or elapsed90day claim is made.
"""
import copy
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tools.catalog import amend_recipe
from tools.cloud_feed import prepare_content
from tools.spacefox.catalog import build_catalog, canonical_bytes
from tools.spacefox.cloud import CloudError, Site, delivery, delivery_files
from tools.spacefox.graphics import assemble_visual, canonical_visual
from tools.spacefox.publisher import GitState, Publisher, LiveRevision, StateError
from tools.spacefox.schedule import (AcceptedLaunch, LaunchRecord, LaunchStatus, ScheduleState,
                                    StableId, IdKind, Timing, TimePrecision)
from tools.spacefox.visual_bridge import (build_artifact, validate_artifact, validate_feed,
    FEED_PATH, put, read_ref, _validate_descriptor, validate_dictionary)
from tools.spacefox.wire import build_artifact as build_v1, validate_feed as validate_v1
from tests.test_cloud_delivery import World, git

ROOT=Path(__file__).resolve().parents[1]
NOW=1794441600


def sid(kind,value):return StableId(kind,'ll2',value)


def record(**kwargs):
    fields=dict(launch_id=sid(IdKind.LAUNCH,'bridge-literal'),
        timing=Timing(TimePrecision.EXACT,exact_utc=NOW+7200),status=LaunchStatus.PENDING,
        source_validated_utc=NOW-3600,configuration_id=sid(IdKind.CONFIGURATION,'164'),
        operator_id=sid(IdKind.ORGANIZATION,'121'),site_id=sid(IdKind.SITE,'80'),
        country_id=sid(IdKind.COUNTRY,'2'),configuration_name='Falcon 9',operator_name='SpaceX',
        mission_name='Луна 零',mission_purpose='Measure lunar radiation',country_code='USA',site_location_name='Florida')
    fields.update(kwargs)
    return LaunchRecord(**fields)


def state(r=None):return ScheduleState((AcceptedLaunch(r or record()),),NOW-3600)


def envelope(generation=1,instance='1'*64):
    return {'instance':instance,'generation':generation,'selectionValidatedUtc':NOW-3600}


class NoProvider:
    def __init__(self):self.calls=0
    def request(self,*args,**kwargs):
        self.calls+=1
        raise AssertionError('content-only path must not invoke provider')


class VisualBridgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=build_catalog(ROOT)
        cls.files,cls.digest=build_artifact(state(),cls.catalog,NOW,publisher=envelope(),root=ROOT)

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='spacefox-bridge-')
        self.root=Path(self.tmp.name)
        self.remote=self.root/'remote.git';source=self.root/'source';self.source=source;source.mkdir()
        subprocess.run(['git','init','--bare','-q',str(self.remote)],check=True)
        subprocess.run(['git','init','-q',str(source)],check=True)
        git(source,'config','user.name','Bridge test');git(source,'config','user.email','bridge@example.invalid')
        git(source,'commit','--allow-empty','-qm','source')
        self.code=git(source,'rev-parse','HEAD');git(source,'push','-q',str(self.remote),'HEAD:refs/heads/main')
        self.store=GitState(str(self.remote));self.store.bootstrap(self.code)
        self.pub=Publisher(self.store,self.code);self.pub.reconcile(None)

    def tearDown(self):
        self.store.close();self.tmp.cleanup()

    def seed(self,files=None):
        token=self.pub.reserve(self.pub.head,NOW-60,trigger='manual')
        self.pub.accept_source(self.pub.head,token,(record(),),NOW,selection_validated_utc=NOW-3600)
        publisher=self.pub.publisher_envelope(NOW)
        if files is None:
            files,digest=build_artifact(self.pub.schedule,self.catalog,NOW,publisher=publisher,root=ROOT)
        else:
            # Only the independently built v1 seed uses this optional route.
            files,digest=build_v1(self.pub.schedule,self.catalog,NOW,publisher=publisher)
        revision=self.pub.prepare(self.pub.head,NOW,files,digest,feed_publisher=publisher)
        self.pub.reconcile(revision)
        return files

    def promote(self):
        pending=self.pub.ledger['pending'];self.pub.reconcile(LiveRevision(pending['generation'],pending['artifact_revision']))

    def test_selected_identity_and_lossless_dual_feed(self):
        old=validate_v1(self.files['feed.json']);new=validate_feed(self.files[FEED_PATH])
        original,_=build_v1(state(),self.catalog,NOW,publisher=envelope())
        self.assertEqual(original,{p:self.files[p] for p in original})
        self.assertEqual(1,old['schemaVersion']);self.assertEqual(2,new['schemaVersion'])
        self.assertEqual(old['launch'],new['launch']);self.assertEqual('Луна 零',new['launch']['mission_name'])
        self.assertEqual({'ll2:configuration:164','ll2:organization:121','ll2:site:80','ll2:country:2'},set(validate_dictionary(new,self.files[new['catalogPath']])['entries']))
        selection=json.loads(read_ref(new['visualSelection'],self.files))
        self.assertEqual(('ll2:launch:bridge-literal','ll2:configuration:164','ll2:organization:121','ll2:site:80','model','ll2:country:2'),tuple(selection[k] for k in ('launchId','modelId','operatorId','siteId','originMode','originId')))
        self.assertEqual('28.56194122',validate_dictionary(new,self.files[new['catalogPath']])['entries']['ll2:site:80']['position']['latitude'])
        for role in ('rocket','operator','origin','siteCountry'):
            desc=json.loads(read_ref(selection['roles'][role]['descriptor'],self.files))
            for pin in desc['shards']:
                raw=self.files[pin['path']]
                self.assertEqual(hashlib.sha256(raw).hexdigest(),pin['sha256'])
                self.assertEqual(len(raw),pin['decodedBytes']);self.assertLessEqual(len(raw),4096)
            logical=assemble_visual([self.files[p['path']] for p in desc['shards']],desc['animation'])
            self.assertEqual(hashlib.sha256(canonical_visual(logical)).hexdigest(),desc['sha256'])
        # An otherwise valid near8KiB v1 must not overflow v2 because of
        # optional dictionaries. Every launch purpose byte remains supplied.
        available=8190-len(original['feed.json'])+len(record().mission_purpose.encode())
        purpose='Ж'*(available//2)+('x' if available%2 else '')
        large,_=build_artifact(state(record(mission_purpose=purpose)),self.catalog,NOW,publisher=envelope(),root=ROOT)
        self.assertEqual(8190,len(large['feed.json']))
        self.assertLess(len(large[FEED_PATH]),8190)
        self.assertEqual(purpose,validate_feed(large[FEED_PATH])['launch']['mission_purpose'])
        # ESA's23 worldwide country relations stay offwatch; only selected roles.
        r=record(operator_id=sid(IdKind.ORGANIZATION,'27'))
        files,_=build_artifact(state(r),self.catalog,NOW,publisher=envelope(),root=ROOT,origin_mode='operator')
        feed=validate_feed(files[FEED_PATH]);selection=json.loads(read_ref(feed['visualSelection'],files))
        self.assertEqual('spacefox:country:EUROPE',selection['originId']);self.assertLessEqual(len(validate_dictionary(feed,files[feed['catalogPath']])['entries']),5)
        # Full supplied uncertain timing and source epoch zero are preserved.
        r=record(timing=Timing(TimePrecision.UNKNOWN),source_validated_utc=0,site_id=None,operator_id=None,configuration_id=None,country_id=None)
        files,_=build_artifact(state(r),self.catalog,NOW,publisher=envelope(),root=ROOT)
        self.assertIsNone(validate_feed(files[FEED_PATH])['launch']['timing']['exact_utc'])
        self.assertEqual(0,validate_feed(files[FEED_PATH])['launch']['source_validated_utc'])

    def test_raw_semantic_replay_and_index_rejection(self):
        feed=validate_feed(self.files[FEED_PATH]);selection=json.loads(read_ref(feed['visualSelection'],self.files))
        ref=selection['roles']['rocket']['descriptor'];desc=json.loads(read_ref(ref,self.files))
        pin=desc['shards'][0];raw=self.files[pin['path']]
        formatted=b' '+raw+b'\n'
        # Semantic equivalence never waives declared raw SHA. The independent
        # correct new raw pin/path can retain the full logical semantic SHA.
        files=dict(self.files);files[pin['path']]=formatted
        with self.assertRaises(ValueError):_validate_descriptor(ref,files,set())
        changed=copy.deepcopy(desc);digest=hashlib.sha256(formatted).hexdigest()
        changed['shards'][0]={'path':f'objects/{digest}.json','sha256':digest,'decodedBytes':len(formatted)}
        files[changed['shards'][0]['path']]=formatted;newref=put(files,changed)
        accepted=_validate_descriptor(newref,files,set());self.assertEqual(desc['sha256'],accepted['sha256'])
        for mode in ('missing','corrupt','semantic','index','major','reorder','external','replay'):
            with self.subTest(mode=mode):
                files=dict(self.files);bad=copy.deepcopy(desc)
                if mode=='missing':del files[pin['path']]
                elif mode=='corrupt':files[pin['path']]=raw[:-1]+b'!'
                elif mode=='semantic':bad['sha256']='0'*64
                elif mode=='major':bad['rendererVersion']=99
                elif mode=='external':bad['shards'][0]['path']='https://example.invalid/stale.json'
                elif mode=='replay':bad['assetId']='spacefox:asset:prior-same-id';files[ref['path']]=canonical_bytes(bad)
                elif mode=='index':
                    v=json.loads(raw);v[6][0][2][0]=99999;data=json.dumps(v,separators=(',',':')).encode();digest=hashlib.sha256(data).hexdigest();p=f'objects/{digest}.json';files[p]=data;bad['shards'][0]={'path':p,'sha256':digest,'decodedBytes':len(data)}
                else:
                    bad['shards']=bad['shards']+bad['shards']
                target=ref if mode in ('missing','corrupt','replay') else put(files,bad)
                with self.assertRaises(ValueError):_validate_descriptor(target,files,set())
        for mode in ('feed-major','catalog','selection','extra'):
            files=dict(self.files)
            if mode=='extra':files['unexpected.json']=b'{}'
            elif mode=='catalog':files[feed['catalogPath']]=b'{}'
            elif mode=='selection':files[feed['visualSelection']['path']]=canonical_bytes(dict(selection,modelId='ll2:configuration:165'))
            else:files[FEED_PATH]=json.dumps(dict(feed,schemaVersion=3),sort_keys=True,separators=(',',':')).encode()
            with self.assertRaises(ValueError):validate_artifact(files)
        # The same invalid candidate cannot be persisted even via Publisher.
        self.pub.reserve(self.pub.head,NOW,trigger='manual')
        self.pub.accept_source(self.pub.head,self.pub.ledger['requests'][-1]['id'],(record(),),NOW,selection_validated_utc=NOW-3600)
        publisher=self.pub.publisher_envelope(NOW);files,digest=build_artifact(self.pub.schedule,self.catalog,NOW,publisher=publisher,root=ROOT)
        del files[next(p for p in files if p.startswith('objects/'))]
        before=self.pub.head
        with self.assertRaises(StateError):self.pub.prepare(before,NOW,files,digest,feed_publisher=publisher)
        self.assertEqual(before,self.pub.head);self.assertIsNone(self.pub.ledger['pending'])

    def test_catalog_art_only_generations_recovery(self):
        self.seed();epoch=self.pub.ledger['selection_validated_utc'];quota=copy.deepcopy(self.pub.ledger['requests'])
        origin=self.pub.schedule.entries[0].record.source_validated_utc
        workspace=self.root/'content';workspace.mkdir()
        for path in {'catalog/source.json',*self.catalog['inputDigests']}:
            target=workspace/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
        # Two real original SVG revisions admitted by the single production recipe.
        catalogs=[]
        for i,color in ((1,'#ffffff'),(2,'#ffd166')):
            svg=(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 32"><path d="M6 1L9 8V28L11 31H1L3 28V8Z" fill="{color}"/></svg>').encode()
            path=workspace/f'assets/bridge-test/r{i}.svg';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(svg)
            facts={'id':f'bridge-original-{i}','name':'Literal original two-stage schematic','file':f'r{i}.svg','exportSize':[12,32],
                   'creator':'SpaceFox test contributors','license':'MIT','kind':'specific','sourceSha256':hashlib.sha256(svg).hexdigest(),
                   'sources':['https://www.spacex.com/vehicles/falcon-9/'],
                   'coverage':{'type':'specific','configurationIds':['ll2:configuration:164'],'features':['Tall two-stage body; test image color revision'],
                               'limitations':'Test-only original, not actual product artwork acceptance.'}}
            update={'identity':'ll2:configuration:164','changes':{'currentPackAssetId':facts['id'],'currentPackSpecific':True},'sources':facts['sources']}
            point={'identity':'ll2:site:80','changes':{'latitude':Decimal('28.561941220') if i==1 else Decimal('28.561951220')},'sources':['https://ll.thespacedevs.com/2.3.0/pads/80/?format=json']}
            amendment={'schemaVersion':1,'id':f'bridge-art-{i}','reviewedAt':'2026-11-12','reason':'Literal admitted art and sourced point revision test',
                       'sources':facts['sources'],'assets':[{'collection':'models','facts':facts}],'updates':[update,point],'additions':[]}
            supplement=workspace/f'assets/bridge-test/revision{i}.json';supplement.write_bytes(canonical_bytes(amendment))
            catalogs.append(amend_recipe(workspace,workspace/'catalog/source.json',supplement,f'bridge.revision{i}'))
        client=NoProvider();hashes=[];maphashes=[];shared=[];snapshot=copy.deepcopy(self.pub.ledger['active'])
        for generation,catalog in ((2,catalogs[0]),(3,catalogs[1]),(4,catalogs[0])):
            # Rollback-as-new-generation uses the prior reviewed complete source.
            result=prepare_content(self.pub,client,NOW+generation,catalog,root=workspace)
            self.assertEqual(('content_pending',0),(result['result'],result['requests']))
            files=self.pub.pending_files();feed=validate_feed(files[FEED_PATH]);sel=json.loads(read_ref(feed['visualSelection'],files))
            hashes.append(json.loads(read_ref(sel['roles']['rocket']['descriptor'],files))['sha256'])
            maphashes.append(sel['roles']['geography']['descriptor']['sha256'])
            shared.append(sel['roles']['operator']['descriptor']['sha256'])
            self.assertEqual(generation,feed['publisher']['generation']);self.assertEqual(epoch,feed['publisher']['selectionValidatedUtc'])
            self.assertEqual(origin,feed['launch']['source_validated_utc']);self.assertEqual(quota,self.pub.ledger['requests'])
            pending=copy.deepcopy(self.pub.ledger['pending'])
            reopened=Publisher(self.store,self.code);self.assertEqual('retry_pending',reopened.reconcile(LiveRevision(snapshot['generation'],snapshot['artifact_revision'])))
            self.assertEqual(files,reopened.pending_files())
            self.assertEqual('recovered_pending',prepare_content(reopened,client,NOW+generation+1,self.catalog,root=ROOT)['result'])
            self.assertEqual(files,reopened.pending_files());self.pub=reopened;self.promote();snapshot=pending
        self.assertNotEqual(hashes[0],hashes[1]);self.assertEqual(hashes[0],hashes[2])
        self.assertNotEqual(maphashes[0],maphashes[1]);self.assertEqual(maphashes[0],maphashes[2]);self.assertEqual(1,len(set(shared)))
        # Source-only metadata has a distinct generation without renewing ages.
        metadata=copy.deepcopy(catalogs[0]);metadata['catalogVersion']='bridge.metadata-only'
        # A new catalog revision must bind its own immutable eligibility decision
        # record, even when only its version metadata changed.
        from tools.spacefox.current_catalog import load_registry
        eligibility = copy.deepcopy(load_registry(workspace, catalogs[0]))
        eligibility['catalogVersion'] = metadata['catalogVersion']
        eligibility_bytes = canonical_bytes(eligibility)
        eligibility_hash = hashlib.sha256(eligibility_bytes).hexdigest()
        eligibility_path = 'catalog/current-eligibility-' + eligibility_hash + '.json'
        (workspace / eligibility_path).write_bytes(eligibility_bytes)
        metadata['source']['eligibility'] = {'path': eligibility_path, 'sha256': eligibility_hash}
        metadata['inputDigests'][eligibility_path] = eligibility_hash
        self.assertEqual('content_pending',prepare_content(self.pub,client,NOW+10,metadata,root=workspace)['result'])
        feed=validate_feed(self.pub.pending_files()[FEED_PATH]);self.assertEqual(5,feed['publisher']['generation']);self.assertEqual(epoch,feed['publisher']['selectionValidatedUtc'])
        self.assertEqual(0,client.calls);self.assertEqual(quota,self.pub.ledger['requests'])
        self.promote()
        # Independent code adoption does not masquerade as an asset update.
        git(self.source,'commit','--allow-empty','-qm','independent code adoption')
        code=git(self.source,'rev-parse','HEAD');git(self.source,'push','-q',str(self.remote),'HEAD:refs/heads/main')
        self.pub=Publisher(self.store,code);self.pub.adopt_code(self.pub.head)
        active=self.pub.ledger['active'];self.pub.reconcile(LiveRevision(active['generation'],active['artifact_revision']))
        class ForbiddenTransport:
            def get(self,url):raise AssertionError('code adoption must not force transport')
        from tools.spacefox.provider import LL2Client
        provider=LL2Client(ForbiddenTransport())
        result=prepare_content(self.pub,provider,NOW+11,metadata,root=workspace)
        self.assertEqual(('not_due',0),(result['result'],result['requests']))
        self.assertEqual(0,provider.requests_started);self.assertEqual(5,self.pub.ledger['generation'])
        self.assertIsNone(self.pub.ledger['pending']);self.assertEqual(epoch,self.pub.ledger['selection_validated_utc'])
        self.assertEqual(quota,self.pub.ledger['requests'])

    def test_complete_current_prior_http_and_budget(self):
        first=self.seed();world=World(self.remote)
        try:
            world.live=first;site=Site(world.base+'/site',local_http=True)
            active=self.pub.ledger['active'];self.assertEqual(LiveRevision(1,active['artifact_revision']),site.observe(self.pub))
            metadata=copy.deepcopy(self.catalog);metadata['catalogVersion']='literal-next'
            client=NoProvider();prepare_content(self.pub,client,NOW+1,metadata,root=ROOT)
            second=self.pub.pending_files();manifest=delivery(self.pub);complete=delivery_files(self.pub,manifest)
            self.assertEqual({**{p:v for p,v in first.items() if p not in ('feed.json',FEED_PATH)},**second},complete)
            self.assertLessEqual(len(complete),256);self.assertLessEqual(sum(map(len,complete.values())),1048576)
            world.live=complete;pending=self.pub.ledger['pending'];expected=LiveRevision(2,pending['artifact_revision'])
            self.assertEqual(expected,site.observe(self.pub,manifest))
            for mode in ('missing','corrupt','old-v2-root'):
                world.live=dict(complete)
                if mode=='old-v2-root':world.live[FEED_PATH]=first[FEED_PATH]
                else:
                    target=next(p for p in second if p.startswith('objects/'))
                    if mode=='missing':del world.live[target]
                    else:world.live[target]=b'{}'
                with self.assertRaises(CloudError):site.observe(self.pub,manifest)
                self.assertEqual(2,self.pub.ledger['generation']);self.assertIsNotNone(self.pub.ledger['pending'])
            self.assertEqual(0,client.calls)
            # Direct production refusal before durable candidate on budget error.
            for extra in ({f'extra/{i}.json':b'{}' for i in range(256)}, {'huge.json':b'x'*1048576}):
                with self.assertRaises(ValueError):validate_artifact({**second,**extra})
        finally:world.close()

    def test_distinct_art_point_current_prior_fixture_sequence(self):
        prior=self.seed();index=json.loads((ROOT/'tests/fixtures/bridge-v2/index.json').read_bytes())
        age=self.pub.ledger['selection_validated_utc'];quota=copy.deepcopy(self.pub.ledger['requests'])
        from tools.spacefox.feed import encode_feed
        for generation,label in ((2,'b'),(3,'rollback')):
            files={p:(ROOT/'tests/fixtures/bridge-v2'/label/p).read_bytes() for p in index[label]['files']}
            publisher=self.pub.publisher_envelope(NOW+generation)
            for path in ('feed.json',FEED_PATH):
                feed=json.loads(files[path]);feed['publisher']=publisher;files[path]=encode_feed(feed)
            digest=json.loads(files['feed.json'])['catalogDigest']
            self.pub.prepare(self.pub.head,NOW+generation,files,digest,feed_publisher=publisher)
            complete=delivery_files(self.pub,delivery(self.pub))
            expected={**{p:raw for p,raw in prior.items() if p not in ('feed.json',FEED_PATH)},**files}
            self.assertEqual(expected,complete)
            self.assertLessEqual(len(complete),256);self.assertLessEqual(sum(map(len,complete.values())),1048576)
            self.assertEqual(generation,json.loads(complete[FEED_PATH])['publisher']['generation'])
            self.assertEqual(age,json.loads(complete[FEED_PATH])['publisher']['selectionValidatedUtc'])
            self.assertEqual(quota,self.pub.ledger['requests'])
            self.promote();prior=files

    def test_delivery_index_omission_rejection(self):
        self.seed()
        metadata=copy.deepcopy(self.catalog);metadata['catalogVersion']='index-next'
        prepare_content(self.pub,NoProvider(),NOW+1,metadata,root=ROOT)
        manifest=delivery(self.pub)
        required=[FEED_PATH,next(p for p in manifest if p.startswith('objects/')),
                  next(p for p,m in manifest.items() if m['role']=='previous')]
        before=self.pub.head
        for path in required:
            missing=dict(manifest);del missing[path]
            with self.subTest(path=path):
                with self.assertRaises(CloudError):delivery_files(self.pub,missing)
                self.assertEqual(before,self.pub.head)
        self.assertEqual(set(manifest),set(delivery_files(self.pub,manifest)))

    def test_sourced_full_camera_geometry(self):
        feed=validate_feed(self.files[FEED_PATH]);selection=json.loads(read_ref(feed['visualSelection'],self.files))
        mapref=selection['roles']['geography']['descriptor'];m=json.loads(read_ref(mapref,self.files))
        self.assertEqual(['28.56194122','-80.57735736'],m['center'])
        self.assertEqual(([335,165],28,False,'transparent'),(m['marker']['anchor'],m['marker']['diameter'],m['style']['markerFade'],m['style']['timeBackground']))
        self.assertEqual([390,390],m['style']['canvas']);self.assertEqual(145,m['style']['scale'])
        self.assertLess(((335-195)**2+(165-195)**2)**.5+14,195)
        # Decode actual exported fills; independent sample points see bright land,
        # ocean and a directed fade. Every layer remains strict SFV1.
        layers=[];coasts=[];fills=[]
        for page in m['layers']:
            for pin in json.loads(read_ref(page,self.files))['layers']:
                desc=json.loads(read_ref(pin,self.files));v=assemble_visual([self.files[p['path']] for p in desc['shards']],desc['animation'])
                layers.append(v)
                if ':fill-' in desc['assetId']:
                    for _,color,indices in v[6]:
                        pts=[((v[5][i]%16384)*390/8192,(v[5][i]//16384)*390/8192) for i in indices]
                        fills.append((v[4][color],min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)))
                if ':coast-' in desc['assetId']:
                    for _,_,indices in v[6]:
                        coasts.append([((v[5][i]%16384)*390/8192,(v[5][i]//16384)*390/8192) for i in indices])
        # Independent source-vertex + spherical-rotation oracle. These are
        # literal Natural Earth coastline vertices, not guessed pad landmarks.
        # Land/ocean bracket across the literal Hatteras-area source coast,
        # outside the28px marker. This catches a separately rotated/flipped fill.
        samples=[]
        for x,y in ((342,147),(348,147)):
            samples.append(next(c for c,a,b,d,e in fills if a<=x<d and b<=y<e))
        self.assertEqual([0x285870,0x082030],samples)
        topology=json.loads((ROOT/'catalog/geography/accepted04-topology-c3791187.json').read_bytes())
        witnesses=[(50,47,-75.72855728557285,35.55015739417394,345.0562804585555,147.11134470263048),
                   (50,67,-81.17181171811718,25.200804152641524,333.6364460875812,173.50273980968043),
                   (18,158,-65.11565115651156,48.07009646656465,362.69404681829286,113.8475923403092)]
        def segment_distance(p,a,b):
            dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
            t=0 if not den else max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den))
            return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)
        for arc,vertex,lon,lat,expected_x,expected_y in witnesses:
            x=sum(p[0] for p in topology['arcs'][arc][:vertex+1]);y=sum(p[1] for p in topology['arcs'][arc][:vertex+1])
            self.assertAlmostEqual(lon,x*topology['transform']['scale'][0]+topology['transform']['translate'][0],places=12)
            self.assertAlmostEqual(lat,y*topology['transform']['scale'][1]+topology['transform']['translate'][1],places=12)
            phi,delta,phi0=map(math.radians,(lat,lon+80.57735736,28.56194122))
            gx=math.cos(phi)*math.sin(delta);gy=math.cos(phi0)*math.sin(phi)-math.sin(phi0)*math.cos(phi)*math.cos(delta)
            gz=math.sin(phi0)*math.sin(phi)+math.cos(phi0)*math.cos(phi)*math.cos(delta)
            self.assertAlmostEqual(expected_x,335+145*math.atan2(gx,gz),places=9)
            self.assertAlmostEqual(expected_y,165-145*math.asin(gy),places=9)
            distance=min(segment_distance((expected_x,expected_y),a,b) for poly in coasts for a,b in zip(poly,poly[1:]+poly[:1]))
            self.assertLess(distance,2.5)
        self.assertGreater(len(layers),1)
        filled_area=0;colors=set()
        for v in layers:
            colors.update(v[4])
            for cmd in v[6]:
                pts=[(v[5][i]%16384,v[5][i]//16384) for i in cmd[2]]
                filled_area+=abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(pts,pts[1:]+pts[:1])))/2
        self.assertGreater(filled_area,(256*32)**2*.98)
        self.assertGreater(max((c>>8)&255 for c in colors),100)
        # Real source2 island context and date-line camera use the same recipe.
        from tools.spacefox.bridge_map import load_source
        source=load_source(ROOT,self.catalog['source']['visualBridge'])
        for center in ([90,0],[-90,179.999999],[0,-180],[0,180]):
            data={'center':center,**{k:source[k] for k in ('d3','topojson','topology')}}
            result=subprocess.run(['node',str(ROOT/'tools/spacefox/bridge_map_render.js')],input=json.dumps(data).encode(),capture_output=True,check=True)
            rendered=json.loads(result.stdout)
            self.assertAlmostEqual(335,rendered['anchor'][0],places=7);self.assertAlmostEqual(165,rendered['anchor'][1],places=7)
            self.assertGreater(rendered['rings'],0)
            self.assertTrue(all(0<=x0<x1<=390 and 0<=y0<y1<=390 for _,x0,y0,x1,y1 in rendered['rectangles']))
        for site in ('ll2:site:107','ll2:site:13','ll2:site:101'):
            files,_=build_artifact(state(record(site_id=sid(IdKind.SITE,site.split(':')[-1]))),self.catalog,NOW,publisher=envelope(),root=ROOT)
            f=validate_feed(files[FEED_PATH]);s=json.loads(read_ref(f['visualSelection'],files));m=json.loads(read_ref(s['roles']['geography']['descriptor'],files))
            if site=='ll2:site:107':self.assertEqual([335,165],m['marker']['anchor']);self.assertTrue(m['source'])
            else:self.assertIsNone(m['position']);self.assertIsNone(m['marker']);self.assertEqual([],m['layers'])

    def test_unknown_mobile_and_optional_fallback(self):
        r=record(configuration_id=sid(IdKind.CONFIGURATION,'unknown'),operator_id=sid(IdKind.ORGANIZATION,'unknown'),site_id=sid(IdKind.SITE,'unknown'))
        files,_=build_artifact(state(r),self.catalog,NOW,publisher=envelope(),root=ROOT)
        feed=validate_feed(files[FEED_PATH]);sel=json.loads(read_ref(feed['visualSelection'],files))
        self.assertEqual(['ll2:configuration:unknown','ll2:organization:unknown','ll2:site:unknown'],feed['unresolvedCatalogIds'])
        self.assertIsNone(sel['roles']['rocket']);self.assertIsNone(sel['roles']['geography'])
        # Valid schedule metadata admission does not fetch/assemble optional art.
        metadata_only=validate_feed(self.files[FEED_PATH]);self.assertEqual('ll2:launch:bridge-literal',metadata_only['launch']['launch_id'])
        incomplete=dict(self.files);del incomplete[metadata_only['visualSelection']['path']]
        self.assertEqual(metadata_only,validate_feed(incomplete[FEED_PATH]))
        with self.assertRaises(ValueError):validate_artifact(incomplete)
        # Closed v1 never accepts new nonnull visual fields or wire2 major.
        old=validate_v1(self.files['feed.json']);old['dictionaries']['ll2:configuration:164']['visual']=metadata_only['visualSelection']
        from tools.spacefox.feed import encode_feed
        with self.assertRaises(ValueError):validate_v1(encode_feed(old))
        with self.assertRaises(ValueError):validate_v1(self.files[FEED_PATH])
        self.assertEqual(7776000,metadata_only['compatibility']['retainPreviousThroughUtc']-metadata_only['compatibility']['announcedUtc'])
