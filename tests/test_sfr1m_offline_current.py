"""Offline SFR1M captured-record qualification. No SDK or physical-device claim."""
from copy import deepcopy
import tempfile
import base64
import gzip
import hashlib
import json
import re
import unittest

from tests.test_global_catalog import temporary_catalog
from tests.test_current_motion_publisher import ROOT, NOW, FIXTURE, FIXTURE_SHA, captured_starship
from tools.spacefox.catalog import build_catalog, canonical_bytes
from tools.spacefox.native_motion import build_artifact, validate_artifact, with_text_transport
from tools.spacefox.native_profile import decode_raster
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import ScheduleState, merge_schedule

PINS = {
    'map': ('b166d43ce4b6b0bb659656eb3b98bf62683c7fbb5443c3bfaba1f543c2537ccd', '248b4469c8cb3c0633ce03204090b46af0c450b2ea64c4e7ab8c3d5e1d46c30f'),
    'rocket': ('15395365f81866ada8f35c360baa648fb7621b9a0e15052c2dfe5562ae8eacba', '214d70b59c4e703e8ad0cdc3321c41eebdf3e3c584a0554a235fd672a615332e'),
    'siteCountry': ('c8b74ae2cd882dfb43d120675b2c3cca57e8d69584f9ab902ba1b6d1c63f1fa9', 'a0e87cf2d85204c842bff2f12a6f3026d4976d299471093c72b24e3227ba884c'),
}

def digest(data): return hashlib.sha256(data).hexdigest()

def literal_decode(chunks, width, height, channels):
    """Literal SFR1 wire grammar; independent of both production codec functions."""
    rows=[]
    for chunk in chunks:
        if not 1 <= len(chunk) <= 4096: raise ValueError('shard size')
        m=re.fullmatch(rb'SFR1:(0|[1-9][0-9]*):([1-9][0-9]*):([A-Za-z0-9+/]*={0,2})',chunk)
        if not m or int(m[1])!=len(rows) or len(rows)+int(m[2])>height: raise ValueError('row header')
        data=base64.b64decode(m[3],validate=True)
        if base64.b64encode(data)!=m[3]: raise ValueError('base64')
        cursor=0; prior=[bytes(channels)]*width
        for _ in range(int(m[2])):
            line=[]
            while len(line)<width:
                if cursor>=len(data): raise ValueError('truncated token')
                token=data[cursor];cursor+=1; run=(token & 127)+1
                if len(line)+run>width: raise ValueError('row overflow')
                if token & 128: line.extend(prior[len(line):len(line)+run])
                else:
                    color=data[cursor:cursor+channels];cursor+=channels
                    if len(color)!=channels: raise ValueError('truncated color')
                    line.extend([color]*run)
            prior=line;rows.append(line)
        if cursor!=len(data): raise ValueError('trailing bytes')
    if len(rows)!=height: raise ValueError('incomplete rows')
    return b''.join(pixel for row in rows for pixel in row)

def build(row,catalog):
    launch=normalize_launch(row,NOW)
    state=merge_schedule(ScheduleState(),(launch,),NOW)
    return build_artifact(state,catalog,NOW,publisher=dict(instance='a'*64,generation=1,selectionValidatedUtc=NOW),root=ROOT)[0]

def documents(files):
    feed=json.loads(files['feed.json']);scene=json.loads(files[feed['visualSelection']['path']]);transfer=json.loads(files[feed['nativeTransfer']['path']]);return feed,scene,transfer

def cache_rows(files):
    feed,_,index=documents(files)
    # NativeImmutable pins selected catalog, transfer descriptor, then index rows.
    paths=[feed['catalogPath'],feed['nativeTransfer']['path']]
    paths += [('rasters/' if kind else 'descriptors/')+sha+('.sfr' if kind else '.json') for kind,sha,_ in index['objects']]
    return {digest(files[path]):len(files[path]) for path in paths}

class Sfr1mOfflineCurrent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        catalog=build_catalog(ROOT)
        assert catalog["catalogVersion"] == "2026-11-14.global.40.best-effort-r1"
        assert len(catalog["dictionaries"]["assets"]) == 683
        cls.current=build(captured_starship(),catalog)
        raw=gzip.decompress(FIXTURE.read_bytes())
        assert digest(raw)==FIXTURE_SHA
        row=next(x for x in json.loads(raw)['results'] if x['id']=='76617033-4dc0-4448-b50c-e5b0d5a18539')
        cls.recovery=build(row,catalog)

    def test_current_raw_pixels_identity_age_and_bounds(self):
        files=self.current;feed,scene,index=documents(files)
        self.assertEqual((feed['schemaVersion'],feed['rendererProfile']),(3,'SFR1M'))
        self.assertEqual(feed['launch']['launch_id'],'ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b')
        self.assertEqual((feed['launch']['source_validated_utc'],feed['publisher']['selectionValidatedUtc']),(NOW,NOW))
        self.assertEqual(feed['launch']['timing']['source_net'],'2026-11-13T22:45:00Z')
        self.assertEqual((scene['modelId'],scene['operatorId'],scene['siteId'],scene['countryId']),('ll2:configuration:522','ll2:organization:121','ll2:site:235','ll2:country:2'))
        self.assertEqual(scene['marker']['anchor'],[335,165])
        self.assertEqual((scene['origins']['model']['ownerId'],scene['origins']['model']['countryId']),('ll2:configuration:522','ll2:country:2'))
        self.assertEqual((scene['origins']['operator']['ownerId'],scene['origins']['operator']['countryId']),('ll2:organization:121','ll2:country:2'))
        self.assertIsNone(feed['launch']['timing']['exact_utc'])
        self.assertEqual(feed['launch']['timing']['nominal_utc'],1794609900)
        self.assertEqual((scene['position']['latitude'],scene['position']['longitude']),('25.99677','-97.15799'))
        for role,binding in scene['roles'].items():
            self.assertIsNotNone(binding)
            desc=json.loads(files[binding['descriptor']['path']]);compressed=(ROOT/'tests/fixtures/sfr1m-current'/f'{role}.rgba.gz').read_bytes();raw=gzip.decompress(compressed)
            self.assertEqual((digest(raw),digest(compressed)),PINS[role]);self.assertEqual(desc['pixelSha256'],PINS[role][0])
            chunks=[files[x['path']] for x in desc['shards']]
            for pin,chunk in zip(desc['shards'],chunks):self.assertEqual((digest(chunk),len(chunk)),(pin['sha256'],pin['decodedBytes']))
            self.assertEqual(literal_decode(chunks,*desc['canvas'],desc['channels']),raw)
            self.assertEqual(desc['animation'],[0,[]])
        rows=index['objects'];self.assertLessEqual(len(rows),40);self.assertLessEqual(sum(x[2] for x in rows),114688)
        self.assertLessEqual(sum(x[2] for x in rows if x[0]==1),98304)
        self.assertTrue(all(1<=x[2]<=4096 for x in rows))
        a,b=cache_rows(files),cache_rows(self.recovery);self.assertNotEqual(set(a),set(b))
        union=a|b;self.assertLessEqual(len(union),56);self.assertLessEqual(sum(union.values()),229376)
        self.assertEqual(validate_artifact(files),feed)
        print('SFR1M selected/current+recovery',len(rows),sum(x[2] for x in rows),len(a),len(b),len(union),sum(union.values()))

    def test_global_growth_retains_selected_closure_bound(self):
        # Extend the current real catalog with ten unreferenced copies as a
        # technical growth probe. Their identities are not display strings.
        catalog=build_catalog(ROOT)
        asset=catalog['dictionaries']['assets']['spacefox:asset:further-r2-starship-v3-2026']
        for i in range(10):
            extra=deepcopy(asset);extra['facts']['id']='technical-growth-%s'%i
            catalog['dictionaries']['assets']['spacefox:asset:technical-growth-%s'%i]=extra
        grown=build(captured_starship(),catalog)
        _,scene,index=documents(grown);_,prior,_=documents(self.current)
        self.assertEqual(scene['launchId'],prior['launchId'])
        for role in scene['roles']:
            current=json.loads(grown[scene['roles'][role]['descriptor']['path']])
            original=json.loads(self.current[prior['roles'][role]['descriptor']['path']])
            self.assertEqual(current['pixelSha256'],original['pixelSha256'])
        self.assertLessEqual(len(index['objects']),40)
        self.assertLessEqual(sum(row[2] for row in index['objects']),114688)
        union=cache_rows(grown)|cache_rows(self.current)
        self.assertLessEqual(len(union),56);self.assertLessEqual(sum(union.values()),229376)
        print('SFR1M global growth/current+recovery',len(union),sum(union.values()))

    def test_same_identity_real_asset_replacement_keeps_recovery_bounded(self):
        # Technical mutation of the captured launch's real source artwork, not
        # a claim that this color is a researched or admissible product update.
        with tempfile.TemporaryDirectory() as tmp:
            root=temporary_catalog(tmp);catalog=build_catalog(ROOT)
            asset=catalog['dictionaries']['assets']['spacefox:asset:further-r2-starship-v3-2026']
            path=root/asset['content']['path'];before=path.read_bytes()
            self.assertIn(b'fill="#d9e5eb"',before)
            after=before.replace(b'fill="#d9e5eb"',b'fill="#123456"',1);path.write_bytes(after)
            pin=digest(after);asset['content'].update(sha256=pin,bytes=len(after))
            asset['facts']['sourceSha256']=pin;catalog['inputDigests'][asset['content']['path']]=pin
            launch=normalize_launch(captured_starship(),NOW)
            state=merge_schedule(ScheduleState(),(launch,),NOW)
            replacement,_=build_artifact(state,catalog,NOW+3600,publisher=dict(instance='a'*64,generation=2,selectionValidatedUtc=NOW),root=root)
            feed,scene,_=documents(replacement);oldfeed,oldscene,_=documents(self.current)
            self.assertEqual(feed['launch']['source_validated_utc'],NOW)
            self.assertEqual(feed['publisher']['selectionValidatedUtc'],NOW)
            self.assertEqual(scene['modelId'],oldscene['modelId'])
            self.assertNotEqual(scene['roles']['rocket']['descriptor'],oldscene['roles']['rocket']['descriptor'])
            new=json.loads(replacement[scene['roles']['rocket']['descriptor']['path']])
            old=json.loads(self.current[oldscene['roles']['rocket']['descriptor']['path']])
            self.assertNotEqual(new['pixelSha256'],old['pixelSha256'])
            pixels=literal_decode([replacement[x['path']] for x in new['shards']],*new['canvas'],new['channels'])
            self.assertEqual(digest(pixels),new['pixelSha256'])
            union=cache_rows(replacement)|cache_rows(self.current)
            self.assertLessEqual(len(union),56);self.assertLessEqual(sum(union.values()),229376)
            self.assertEqual(validate_artifact(replacement),feed)
            print('SFR1M replaced-asset/current+recovery',len(union),sum(union.values()))

    def test_corrupt_digest_rejected(self):
        files=self.current;_,scene,_=documents(files);desc=json.loads(files[scene['roles']['rocket']['descriptor']['path']]);pin=desc['shards'][0];bad=dict(files);bad[pin['path']]=bad[pin['path']][:-1]+b'!'
        with self.assertRaises(ValueError):validate_artifact(bad)

    def test_repinned_identity_mismatch_rejected(self):
        files=self.current
        # Rebuild mutable root and transport so a content hash cannot mask the guard.
        feed=json.loads(files['feed.json']);feed['launch']['configuration_id']='ll2:configuration:164'
        semantic={k:v for k,v in files.items() if not k.endswith('.txt')}
        semantic['feed.json']=canonical_bytes(feed)
        with self.assertRaises(ValueError):validate_artifact(with_text_transport(semantic))

    def test_token_row_overflow_rejected(self):
        for chunk in (b'SFR1:1:1:AA==',b'SFR1:0:1:/w==',b'SFR1:0:1:AQAAAAA='):
            with self.subTest(chunk=chunk):
                with self.assertRaises(ValueError):literal_decode([chunk],1,1,4)
                with self.assertRaises(ValueError):decode_raster([chunk],1,1,4)

    def test_truncated_and_noncanonical_tokens_rejected(self):
        for chunk in (b'SFR1:0:1:AA==',b'SFR1:0:1:AA====='):
            with self.subTest(chunk=chunk):
                with self.assertRaises(ValueError):literal_decode([chunk],1,1,4)
                with self.assertRaises(ValueError):decode_raster([chunk],1,1,4)

if __name__=='__main__':unittest.main()
