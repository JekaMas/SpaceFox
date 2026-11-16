"""Literal projection vectors and source-bound site-view primitives."""
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.spacefox.catalog import build_catalog, canonical_bytes, loads_json, validate_catalog
from tools.spacefox.global_map import (GeographyError, build_site_view,
                                      load_world, project)
from tools.spacefox.graphics import build_pack, loads_shard

ROOT=Path(__file__).resolve().parents[1]


class GlobalMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=build_catalog(ROOT)

    def test_projection_positive(self):
        self.assertEqual(project(0,0),(128,128))
        self.assertEqual(project(90,-180),(1,1))
        self.assertEqual(project(-90,180),(1,255))
        view=build_site_view(ROOT,self.catalog,'ll2:site:13')
        self.assertIsNone(view['manifest']['marker'])
        self.assertEqual(canonical_bytes(view['manifest']['site']['sourcePosition']),canonical_bytes(self.catalog['dictionaries']['sites']['ll2:site:13']['position']))
        row=self.catalog['dictionaries']['sites']['ll2:site:13']
        self.assertEqual(view['manifest']['site']['sourceUrl'],row['facts']['sourceUrl'])
        self.assertEqual(view['manifest']['site']['definitionSha256'],hashlib.sha256(canonical_bytes(row)).hexdigest())
        # An explicit, sourced event position is separate from the reference.
        event={'latitude':Decimal('0.0000'),'longitude':Decimal('-154.1234567890123456789'),'sources':['https://example.org/official-event-position']}
        moving=build_site_view(ROOT,self.catalog,'ll2:site:13',event_position=event)
        self.assertIsNotNone(moving['manifest']['marker'])
        self.assertEqual(moving['manifest']['site']['eventPosition'],event)
        self.assertIsNone(build_site_view(ROOT,self.catalog,'ll2:site:101')['manifest']['marker'])

    def test_projection_negative(self):
        for a,b in [(Decimal('NaN'),0),(0,Decimal('Infinity')),(True,0),(0,False),(91,0),(0,-181),(0.0,0)]:
            with self.assertRaises(GeographyError):project(a,b)
        with self.assertRaises(GeographyError):project(0,0,kind='mercator-guessed')
        with self.assertRaises(GeographyError):build_site_view(ROOT,self.catalog,'ll2:site:999999')
        for event in [{'latitude':0,'longitude':0}, {'latitude':0,'longitude':0,'sources':[]}, {'latitude':91,'longitude':0,'sources':['https://example.org/a']}]:
            with self.assertRaises(GeographyError):build_site_view(ROOT,self.catalog,'ll2:site:13',event_position=event)
        bad=copy.deepcopy(self.catalog);bad['source']['geography']['sha256']='0'*64
        with self.assertRaises(GeographyError):load_world(ROOT,bad)

    def test_selection_positive(self):
        catalog=self.catalog;site='ll2:site:65'
        view=build_site_view(ROOT,catalog,site)
        visuals=build_pack(ROOT,catalog,roots=['ll2:configuration:164','ll2:site:65'])
        c=copy.deepcopy(catalog)
        # An unrelated curated site with a real typed country is valid growth.
        row=copy.deepcopy(c['dictionaries']['sites']['spacefox:site:esrange-sounding-area'])
        row['facts']['sourceId']='unrelated-new-global-site';row['facts']['name']='Unrelated source addition';row['references']={'country':'ll2:country:15','agencies':['ll2:organization:151']}
        c['dictionaries']['sites']['spacefox:site:unrelated-new-global-site']=row
        validate_catalog(c)
        after=build_site_view(ROOT,c,site)
        self.assertEqual(canonical_bytes(after['manifest']),canonical_bytes(view['manifest']))
        self.assertEqual(after['objects'],view['objects'])
        grown=build_pack(ROOT,c,roots=['ll2:configuration:164','ll2:site:65'])
        self.assertEqual(len(canonical_bytes(visuals['manifest'])),len(canonical_bytes(grown['manifest'])))
        self.assertEqual(visuals['objects'],grown['objects'])
        self.assertLessEqual(len(canonical_bytes(view['manifest'])),8192)
        self.assertTrue(all(len(b)<=4096 and loads_shard(b) for b in view['objects'].values()))
        mobile=build_site_view(ROOT,catalog,'ll2:site:13')
        unknown=build_site_view(ROOT,catalog,'ll2:site:101')
        event={'latitude':Decimal('0.0000'),'longitude':Decimal('-179.9999999999999999'),
               'sources':['https://example.org/literal-event-point']}
        moving=build_site_view(ROOT,catalog,'ll2:site:13',event_position=event)
        self.assertIsNone(mobile['manifest']['marker']);self.assertIsNone(unknown['manifest']['marker'])
        self.assertEqual(moving['manifest']['marker'],[32,4096])
