"""MIT. Real pack/identity boundary and source-bound browser size acceptance."""
import copy
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from tools.build_rocket_pack import PACK, manifest, validate_registry
from tools.rocket_pack_audit import accept, audit_pack, load_bound, png_alpha


def identity(inputs, catalog=None):
    code = "const fs=require('fs'),a=require('./prototype/rocket-models/core.js');const d=JSON.parse(fs.readFileSync(0,'utf8'));a.validate(d.catalog);process.stdout.write(JSON.stringify(d.inputs.map(x=>a.resolve(d.catalog,x))));"
    c = catalog or json.loads((PACK / 'catalog.json').read_text())
    r = subprocess.run(['node', '-e', code], input=json.dumps({'catalog': c, 'inputs': inputs}),
                       text=True, capture_output=True, check=True)
    return json.loads(r.stdout)


class RocketPackTest(unittest.TestCase):
    def test_pack_positive(self):
        c = audit_pack()
        self.assertEqual(len(c['models']), 6)
        self.assertEqual(len({m['svg']['sha256'] for m in c['models']}), 6)
        self.assertEqual(len({m['png']['sha256'] for m in c['models']}), 6)
        for mid, part, count in [('falcon-heavy', 'side-core', 2), ('ariane-62', 'booster', 2), ('ariane-64', 'booster', 4)]:
            entry = next(m for m in c['models'] if m['id'] == mid)
            root = ET.parse(PACK / entry['svg']['path']).getroot()
            self.assertEqual(len(root.findall(".//*[@data-part='" + part + "']")), count)

    def test_pack_negative(self):
        source = json.loads((PACK / 'registry.source.json').read_text())
        for fault in ('rights', 'reference', 'alias', 'origin', 'anchor'):
            data = copy.deepcopy(source)
            if fault == 'rights': data['models'][0]['license'] = 'unknown'
            elif fault == 'reference': data['models'][0]['file'] = '../outside.svg'
            elif fault == 'alias': data['models'][1]['aliases'].append('Falcon 9')
            elif fault == 'origin': data['models'][0]['originCode'] = 'XX'
            else: data['models'][0]['anchors']['company'][0] = 100
            with self.subTest(fault=fault), self.assertRaises(ValueError): validate_registry(data)
        raw = bytearray((PACK / 'png/falcon-9.png').read_bytes()); raw[-5] ^= 1
        with self.assertRaises(ValueError): png_alpha(raw)
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'pack'
            shutil.copytree(PACK, target)
            path = target / 'svg/falcon-9.svg'; path.write_text(path.read_text() + '\n')
            with self.assertRaises(ValueError): manifest(source, target)

    def test_identity_positive(self):
        fixtures = [
            ({'rocketName': 'Falcon 9 Block 5', 'operatorName': 'SpaceX', 'launchCountryCode': 'NZ'}, ('falcon-9', 'company-spacex', 'flag-us')),
            ({'rocketName': 'Falcon Heavy', 'operatorName': 'SpaceX'}, ('falcon-heavy', 'company-spacex', 'flag-us')),
            ({'rocketName': 'Electron', 'operatorName': 'Rocket Lab', 'launchCountryCode': 'US'}, ('electron', 'company-rocket-lab', 'flag-nz')),
            ({'rocketName': 'Electron', 'operatorName': 'Rocket Lab', 'originMode': 'operator'}, ('electron', 'company-rocket-lab', 'flag-us')),
            ({'rocketName': 'Ariane 64', 'operatorName': 'Arianespace'}, ('ariane-64', 'company-arianespace', 'flag-europe')),
            ({'rocketName': 'Ariane 62', 'operatorName': 'Arianespace', 'originMode': 'operator'}, ('ariane-62', 'company-arianespace', 'flag-fr'))]
        results = identity([f[0] for f in fixtures])
        self.assertEqual([(r['modelId'], r['companyId'], r['countryId']) for r in results], [f[1] for f in fixtures])
        c = audit_pack(); extra = copy.deepcopy(c['models'][0]); extra.update(id='new-explicit-model', aliases=['New Explicit Model']); c['models'].append(extra)
        self.assertEqual(identity([{'rocketName': 'New Explicit Model'}], c)[0]['modelId'], 'new-explicit-model')

    def test_identity_negative(self):
        fixtures = [
            ({'rocketName': 'Falcon 9 turbo', 'operatorName': ''}, ('generic', None, None)),
            ({'rocketName': 'Ariane 6', 'operatorName': ''}, ('generic', None, None)),
            ({'rocketName': 'Falcon 9', 'operatorName': 'Unknown'}, ('falcon-9', None, 'flag-us')),
            ({'rocketName': 'Falcon 9', 'operatorName': 'Unknown', 'originMode': 'operator'}, ('falcon-9', None, None)),
            ({'rocketName': 'Unknown', 'operatorName': 'SpaceX'}, ('generic', 'company-spacex', None))]
        results = identity([f[0] for f in fixtures])
        self.assertEqual([(r['modelId'], r['companyId'], r['countryId']) for r in results], [f[1] for f in fixtures])
        with self.assertRaises(subprocess.CalledProcessError): identity([{'originMode': 'launch-pad'}])

    def test_layout_positive(self):
        data = load_bound()
        for row in data['rows']:
            if row['variant'] != 'oversize':
                with self.subTest(size=row['variant'], scene=row['scene'], origin=row['originMode']): self.assertTrue(accept(row))

    def test_layout_negative(self):
        data = load_bound()
        for row in data['rows']:
            if row['variant'] == 'oversize':
                with self.subTest(scene=row['scene']), self.assertRaises(ValueError): accept(row)
        source = next(r for r in data['rows'] if r['variant'] == 'large' and r['rocket']['marks'])
        for fault in ('model', 'country', 'mark', 'position', 'body'):
            row = copy.deepcopy(source)
            if fault == 'model': row['rocket']['identity']['modelId'] = 'electron'
            elif fault == 'country': row['rocket']['identity']['countryId'] = 'flag-nz'
            elif fault == 'mark': row['rocket']['marks'].pop()
            elif fault == 'position': row['rocket']['marks'][0]['box']['x'] = 350
            else: row['rocket']['marks'][0]['box']['x'] = row['rocket']['box']['x'] + 1
            with self.subTest(fault=fault), self.assertRaises(ValueError): accept(row)
