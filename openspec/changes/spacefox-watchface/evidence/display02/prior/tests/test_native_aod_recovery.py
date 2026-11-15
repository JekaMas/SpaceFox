"""Current source-bound SDK recovery observations, with independent corruptions.

Receipt checking is not another Simulator execution. Original pre-fix failures,
partial harness failures and no-VM runs remain in the packet.
"""
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest

from tools.run_native_tests import parse_output
from tools.spacefox.native_profile import png_pixels

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT/'openspec/changes/spacefox-watchface/evidence/native-combined/independent-r1'


def load(mode, label='native'):
    path = PACKET/'raw'/mode
    return {'build': json.loads((path/'build.json').read_text()),
            'execution': json.loads((path/(label+'-execution.json')).read_text()),
            'raw': (path/(label+'.log')).read_text(),
            'probe': (path/'Probe.mc').read_bytes()}


def validate(row, tests=()):
    b, e, raw = row['build'], row['execution'], row['raw']
    if b['exitCode'] != 0 or b['tests'] != bool(tests):
        raise ValueError('compile/profile mismatch')
    if hashlib.sha256(row['probe']).hexdigest() != b['probeSha256']:
        raise ValueError('probe differs')
    # Resources are unchanged from the frozen joined observation. Preserve its
    # original pins instead of manufacturing post-hoc compiler resource pins.
    old = json.loads((PACKET.parent/'apply/raw/lossless/paged-final-fullstore-callbacks/build.json').read_text())
    for relative, digest in old['resourceSha256'].items():
        if hashlib.sha256((ROOT/relative).read_bytes()).hexdigest() != digest:
            raise ValueError('retained resource differs: '+relative)
    identity = json.loads((PACKET/'identity.json').read_text())
    if b['applicationUuid'] != identity['uuid'] or b['packageName'] != identity['basename']:
        raise ValueError('unowned application')
    if b['sourceSetSha256'] != hashlib.sha256(json.dumps(b['productionSources'], sort_keys=True).encode()).hexdigest():
        raise ValueError('source set differs')
    for relative, digest in b['productionSources'].items():
        saved = PACKET/'sources'/b['sourceSetSha256']/(relative+'.txt')
        if hashlib.sha256(saved.read_bytes()).hexdigest() != digest or hashlib.sha256((ROOT/relative).read_bytes()).hexdigest() != digest:
            raise ValueError('current source differs: '+relative)
    if ('--unit-test' in b['command']) != bool(tests) or ('-t' in e['command']) != bool(tests):
        raise ValueError('test profile differs')
    if tests:
        if parse_output(raw, e['exitCode'], tests)['status'] != 'passed':
            raise ValueError('native test did not pass')
    else:
        if 'owner='+b['ownerTag'] not in raw or e['exitCode'] not in (0, 143):
            raise ValueError('missing owner/runtime completion')
        if any(x in raw for x in ('Error:', 'Out Of Memory', 'Stack Overflow', 'Unhandled Exception')):
            raise ValueError('native runtime failure')
    return raw


def recovery(row, stale=False):
    raw = validate(row)
    kind = 'stagedStaleSource' if stale else 'stagedMalformed'
    if 'REVIEW_BG '+kind+'=true preserved=true total=61248' not in raw or 'REVIEW_BG_CALLBACK mode=1' not in raw:
        raise ValueError('missing actual low background callback')
    ready = re.search(r'REVIEW_READY seal=(\w+) age=(\d+)', raw)
    refused = re.search(r'REVIEW_RESTORE pending=true maintenance=true aodMinute=null acceptedSeal=(\w+)', raw)
    draw = re.search(r'REVIEW_DRAW mode=1 pending=true maintenance=true renderer=false firstMinute=(\d+) secondMinute=(\d+) bitmap=false total=126784', raw)
    if not ready or not refused or ready[1] != refused[1] or ready[2] != '1794438000':
        raise ValueError('accepted source/seal was not retained')
    if not draw or draw[1] != draw[2]:
        raise ValueError('low maintenance minute guard absent')
    if 'phase=foreground-restore-total count=0' not in raw or 'phase=foreground-restore-complete' not in raw:
        raise ValueError('accepted reopen missing')
    if 'REVIEW_MODE mode=0 pending=true' not in raw or raw.rfind('phase=sfr-full-scene-active') < refused.start():
        raise ValueError('High did not restore complete scene')
    if not stale:
        off = raw.index('REVIEW_MODE mode=2 pending=true')
        high = raw.index('REVIEW_MODE mode=0 pending=true', off)
        if 'phase=sfr-step-enter' in raw[off:high] or 'phase=foreground-restore-complete' in raw[off:high]:
            raise ValueError('decode/restore work while Off')
    return raw


def timing(row):
    raw = validate(row)
    begin = re.findall(r'SFR_TIMING requested=(\d+) metrics=false trace=false observerMs=50 owner=([^\n]+)', raw)
    end = re.findall(r'SFR_TIMING fullObserved=(\d+) requestToFullUpperMs=(\d+) observedBuildToFullMs=(\d+) decodedMapObserved=(\d+) complete=true generation=1 storeWriteDelta=(\d+) owner=([^\n]+)', raw)
    if len(begin) != 1 or len(end) != 1:
        raise ValueError('missing unique completed timing')
    start, owner = begin[0]
    full, elapsed, built, first, writes, final_owner = end[0]
    if owner != row['build']['ownerTag'] or owner != final_owner or not 0 < int(built) <= int(elapsed) <= 8000 or int(full)-int(start) != int(elapsed) or int(first) >= int(full):
        raise ValueError('strict timing/owner violated')
    return int(elapsed), int(writes)


def pixel_sets(paths):
    result = []
    for path in paths:
        width, height, pixels = png_pixels(path.read_bytes())
        if (width, height) != (390, 390):
            raise ValueError('unexpected capture size')
        lit = {i for i in range(width*height) if any(pixels[i*4:i*4+3])}
        if not 0 < len(lit) < 11945:  # conservative integer bound below 10% circle
            raise ValueError('AOD lit pixel bound')
        result.append(lit)
    if len(result) != 4 or set.intersection(*result):
        raise ValueError('AOD four-minute pixel rest absent')
    return result


class NativeAodRecoveryTest(unittest.TestCase):
    def test_current_low_rejection_reopen_and_sparse_pixels(self):
        recovery(load('green-ordinary3'))
        recovery(load('stale-ordinary2'), stale=True)
        raw = validate(load('recovery-units2'), ('recoverySparseMinuteGuard',))
        self.assertIn('4 same-minute calls suppressed', raw)
        self.assertIn('High2 draws; hidden timers stopped', raw)
        gallery = validate(load('gallery'))
        self.assertEqual(re.findall(r'REVIEW_GALLERY_PHASE phase=(\d+) sourceClockControlled=true', gallery), ['0', '1', '2', '3'])
        paths = [PACKET/('review-aod-phase'+str(i)+'.png') for i in range(4)]
        self.assertEqual([len(s) for s in pixel_sets(paths)], [1311, 1351, 1474, 1484])
        self.assertEqual(timing(load('timing-map', 'recovered')), (3918, 0))
        self.assertEqual(timing(load('timing-globe', 'fullstore')), (4522, 0))
        fill = validate(load('fill'))
        self.assertIn('COMPLETE full=true logicalBytes=10285952 keys=329 setupBlank=true', fill)
        self.assertIn('tier=1 successful=0 keys=329', fill)
        clean = validate(load('clean'))
        self.assertIn('CLEAN removed=329 ownFillerOnly=true', clean)
        seals = re.findall(r'SNAPSHOT label=\S+ generation=1 validation=1794438000 seal=(\w+)', clean)
        self.assertEqual(len(seals), 2)
        self.assertEqual(seals[0], seals[1])
        cleanup = validate(load('cleanup'))
        self.assertRegex(cleanup, r'newTemporal=null blank=true acceptedBefore=(\w+) acceptedAfter=\1 preserved=true')

    def test_missing_guard_changed_seal_and_false_pixels_refuse(self):
        for kind in ('guard', 'seal', 'callback', 'restore'):
            row = copy.deepcopy(load('green-ordinary3'))
            if kind == 'guard':
                row['raw'] = re.sub(r'firstMinute=\d+', 'firstMinute=null', row['raw'])
            elif kind == 'seal':
                row['raw'] = re.sub(r'acceptedSeal=\w+', 'acceptedSeal=wrong', row['raw'])
            elif kind == 'callback':
                row['raw'] = row['raw'].replace('REVIEW_BG_CALLBACK mode=1', 'REVIEW_BG_CALLBACK mode=0')
            else:
                row['raw'] = row['raw'].replace('phase=foreground-restore-complete', 'phase=missing-restore')
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                recovery(row)
        row = copy.deepcopy(load('timing-globe', 'fullstore'))
        row['raw'] = re.sub(r'requestToFullUpperMs=\d+', 'requestToFullUpperMs=8001', row['raw'])
        with self.assertRaises(ValueError):
            timing(row)
        with self.assertRaises(ValueError):
            pixel_sets([PACKET/'review-aod-phase0.png']*4)
        row = copy.deepcopy(load('recovery-units2'))
        row['build']['tests'] = False
        with self.assertRaises(ValueError):
            validate(row, ('recoverySparseMinuteGuard',))
