from functools import lru_cache
import os
from pathlib import Path

from tools.native_all_site_qualification import qualify
from tools.spacefox.catalog import build_catalog, loads_json

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def evidence_data():
    evidence = Path(os.environ.get('SPACEFOX_NATIVE_ALL_SITE_EVIDENCE', ROOT/'openspec/changes/spacefox-watchface/evidence/native-all-site-maps'))
    catalog = build_catalog(ROOT)
    rows = loads_json((evidence/'producer-rows.json').read_bytes())
    results = qualify(ROOT, evidence)
    return evidence, catalog, rows, results
