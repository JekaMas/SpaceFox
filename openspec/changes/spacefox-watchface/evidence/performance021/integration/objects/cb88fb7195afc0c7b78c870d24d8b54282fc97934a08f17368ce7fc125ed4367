#!/usr/bin/env python3
"""Finite, source-bound display corpus. No native or artwork acceptance is implied.

Fetch uses an explicit externally coordinated quota grant and durable reservations.
All reads resume the same URL chain; malformed or changed pagination fails closed.
The accepted receipt contains selected display inputs and raw-response SHA-256;
gzip pages retain full source bytes for independent reconstruction.
"""
# Exact JSON types intentionally reject booleans as integer counts/allowances.
# ruff: noqa: E721
from __future__ import annotations

import argparse
from datetime import datetime
import fcntl
import gzip
import hashlib
import json
import os
import re
from pathlib import Path
import sys
import time
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://ll.thespacedevs.com'
PATH = '/2.3.0/launches/'
START = '2021-11-13T00:00:00Z'
FIELDS = ('rocket', 'operator', 'purpose', 'site', 'country', 'location')
MAX_BYTES = 16 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pairs(items):
    out = {}
    for key, value in items:
        require(key not in out, 'duplicate JSON key')
        out[key] = value
    return out


def loads(raw):
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def atomic(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('wb') as out:
        out.write(raw)
        out.flush()
        os.fsync(out.fileno())
    os.replace(temporary, path)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def epoch(value):
    require(isinstance(value, str) and (value.endswith('Z') or '+' in value[10:]), 'UTC timestamp required')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.utcoffset() is not None, 'timestamp must include timezone')
    return int(parsed.timestamp())


def first_url():
    return ORIGIN + PATH + '?' + urlencode({'net__gte': START, 'limit': '100', 'mode': 'normal', 'ordering': 'net,id', 'format': 'json'})


def validate_url(url, offset):
    parsed = urlsplit(url)
    require(parsed.scheme == 'https' and parsed.netloc == 'll.thespacedevs.com'
            and parsed.path == PATH and not parsed.fragment, 'unsafe corpus URL')
    query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)
    expected = parse_qs(urlsplit(first_url()).query)
    if offset:
        expected['offset'] = [str(offset)]
    require(query == expected, 'changed corpus query/window/offset')


def text(value):
    if value is None or value == '':
        return None
    require(type(value) is str, 'display field must be source string/null')
    # Exactly the production provider._text whitespace normalization.
    return ' '.join(value.split()) or None


def obj(value):
    require(value is None or type(value) is dict, 'source object required')
    return value or {}


def project(row):
    import uuid
    try:
        from tools.spacefox.provider import _country_code
    except ModuleNotFoundError:
        from spacefox.provider import _country_code
    require(type(row) is dict and str(uuid.UUID(row['id'])) == row['id'], 'canonical launch UUID required')
    require(epoch(row['net']) >= epoch(START), 'launch outside five-year window')
    rocket = obj(obj(row.get('rocket')).get('configuration'))
    operator = obj(row.get('launch_service_provider'))
    pad = obj(row.get('pad'))
    country = obj(pad.get('country'))
    location = obj(pad.get('location'))
    mission = obj(row.get('mission'))
    values = [text(rocket.get('full_name') or rocket.get('name')), text(operator.get('name')),
              text(mission.get('type')), text(pad.get('name')), text(country.get('name')),
              text(location.get('name'))]
    # Use the actual producer's alpha2/alpha3/unknown precedence. FeedScene
    # receives the chosen code; it does not choose alpha3 from the raw source.
    code = _country_code(country)
    return {'id': row['id'], 'net': row['net'], 'sourceUpdated': row.get('last_updated'),
            'sourceIds': [rocket.get('id'), operator.get('id'), pad.get('id'), country.get('id')],
            'descriptionSha256': digest((mission.get('description') or '').encode('utf-8')),
            'descriptionCharacters': len(mission.get('description') or ''),
            'texts': values, 'countryCode': code}


def validate_page(page, state):
    require(type(page) is dict and {'count', 'next', 'previous', 'results'} <= page.keys(), 'incomplete page')
    count, rows = page['count'], page['results']
    require(type(count) is int and count >= 0 and type(rows) is list and len(rows) <= 100, 'invalid page cardinality')
    require(state['count'] is None or count == state['count'], 'source count changed; retain checkpoint and investigate')
    projected = [project(row) for row in rows]
    ids = [row['id'] for row in projected]
    prior = {r['id'] for p in state['pages'] for r in p['records']}
    require(len(set(ids)) == len(ids) and not prior.intersection(ids), 'duplicate launch identity')
    ordered = [(epoch(row['net']), row['id']) for row in projected]
    previous = [(epoch(r['net']), r['id']) for p in state['pages'] for r in p['records']]
    require(ordered == sorted(ordered) and (not previous or not ordered or previous[-1] <= ordered[0]), 'unstable source ordering')
    received = len(prior) + len(rows)
    require(received <= count, 'received more than source count')
    next_url = page['next']
    require(next_url is None or type(next_url) is str, 'invalid next URL')
    if next_url is not None:
        require(rows and received < count, 'nonterminal empty/excess page')
        validate_url(next_url, received)
    else:
        require(received == count, 'terminal page omits source records')
    return projected


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def http_get(url):
    opener = build_opener(ProxyHandler({}), NoRedirect())
    request = Request(url, headers={'Accept': 'application/json', 'Accept-Encoding': 'identity',
                      'User-Agent': 'SpaceFox/1 finite-display-corpus (https://github.com/JekaMas/SpaceFox)'})
    try:
        response = opener.open(request, timeout=60)
    except HTTPError as error:
        response = error
    with response:
        headers = {k.lower(): v for k, v in response.headers.items()
                   if k.lower() in ('date', 'age', 'retry-after', 'content-type', 'content-encoding')}
        raw = response.read(MAX_BYTES + 1)
        require(len(raw) <= MAX_BYTES, 'source response exceeds bound')
        require(headers.get('content-encoding', 'identity') == 'identity', 'unexpected content encoding')
        return response.status, headers, raw


def fetch(directory, grant_path, budget=1, *, get=http_get, clock=time.time):
    """One lock across checkpoint/grant reservations and HTTP. Never automatic retry."""
    require(type(budget) is int and 1 <= budget <= 15, 'call budget must be1..15')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / 'collector.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        path = directory / 'collection.json'
        state = loads(path.read_bytes()) if path.exists() else {
            'schema': 1, 'windowStart': START, 'firstUrl': first_url(), 'next': first_url(),
            'count': None, 'complete': False, 'pages': [], 'attempts': [], 'backoffUntil': 0}
        require(state['firstUrl'] == first_url() and state['windowStart'] == START, 'checkpoint window changed')
        grant_raw = Path(grant_path).read_bytes()
        grant = loads(grant_raw)
        require(grant.get('schema') == 1 and grant.get('coordination') and grant.get('id'), 'explicit coordinated quota grant required')
        require(type(grant['maxRequests']) is int and 0 < grant['maxRequests'] <= 15, 'grant must allow1..15 requests')
        grant_hash = digest(grant_raw)
        seed = grant['quotaSeed']
        require(seed.get('providerLimitPerRollingHour') == 15 and seed.get('noActiveRunsObserved') is True
                and seed.get('workflowState') == 'disabled_manually', 'quiesced shared quota seed required')
        if 'foreignRequests' not in state:
            state['foreignRequests'] = seed['foreignRequests']
            state['quotaSeed'] = seed
            state['backoffUntil'] = max(state['backoffUntil'], seed['backoffUntilUtc'])
        require(state['quotaSeed'] == seed, 'shared quota seed cannot change or reset')
        for _ in range(budget):
            if state['complete']:
                break
            now = int(clock())
            require(epoch(grant['notBefore']) <= now < epoch(grant['expires']), 'quota grant outside validity window')
            require(now >= state['backoffUntil'], 'durable Retry-After/backoff active')
            used = sum(a['grantId'] == grant['id'] for a in state['attempts'])
            require(used < grant['maxRequests'], 'coordinated grant exhausted')
            recent = [a for a in state['attempts'] if now < a['reservedAt'] + 3600]
            foreign = [a for a in state['foreignRequests'] if now < a['at_utc'] + 3600]
            require(len(recent) + len(foreign) < 15, 'shared rolling15/hour limit')
            offset = sum(len(p['records']) for p in state['pages'])
            validate_url(state['next'], offset)
            attempt = {'url': state['next'], 'reservedAt': now, 'grantId': grant['id'],
                       'grantSha256': grant_hash, 'outcome': 'reserved'}
            state['attempts'].append(attempt)
            atomic(path, encoded(state))  # Durable allowance BEFORE any network.
            try:
                status, headers, raw = get(attempt['url'])
                attempt.update(status=status, headers=headers, responseSha256=digest(raw), receivedAt=int(clock()))
                raw_path = directory / 'raw' / (digest(raw) + '.json.gz')
                atomic(raw_path, gzip.compress(raw, mtime=0))
                attempt['raw'] = str(raw_path.relative_to(directory))
                if status == 429:
                    try:
                        from tools.spacefox.provider import retry_deadline
                    except ImportError:
                        from spacefox.provider import retry_deadline
                    state['backoffUntil'] = retry_deadline(headers, attempt['receivedAt'])
                    raise ValueError('provider429: retained durable Retry-After')
                require(status == 200, f'provider HTTP{status}; no automatic retry')
                require(headers.get('content-type', '').split(';')[0] == 'application/json', 'JSON source required')
                page = loads(raw)
                records = validate_page(page, state)
                state['pages'].append({'url': attempt['url'], 'raw': attempt['raw'],
                    'responseSha256': digest(raw), 'headers': headers, 'receivedAt': attempt['receivedAt'],
                    'count': page['count'], 'next': page['next'], 'records': records})
                state.update(count=page['count'], next=page['next'], complete=page['next'] is None)
                attempt['outcome'] = 'accepted'
            except Exception as error:
                attempt.update(outcome='failed', error=str(error))
                atomic(path, encoded(state))
                raise
            atomic(path, encoded(state))
        return state




def status(directory, grant_path, *, now=None):
    """Read-only live budget calculation from the preserved shared ledger."""
    now = int(time.time()) if now is None else now
    state = loads((Path(directory) / 'collection.json').read_bytes())
    grant = loads(Path(grant_path).read_bytes())
    reservations = [a['reservedAt'] for a in state['attempts']] + [a['at_utc'] for a in state['foreignRequests']]
    active = sorted(at for at in reservations if now < at + 3600)
    used = sum(a['grantId'] == grant['id'] for a in state['attempts'])
    next_allowed = max(now, state['backoffUntil'], epoch(grant['notBefore']),
                       active[0] + 3600 if len(active) >= 15 else now)
    return {'complete': state['complete'], 'count': state['count'], 'pages': len(state['pages']),
            'capturedRows': sum(len(p['records']) for p in state['pages']), 'next': state['next'],
            'observedAt': now, 'activeSharedReservations': len(active),
            'availableSharedSlots': max(0, 15 - len(active)),
            'grantRequestsRemaining': max(0, grant['maxRequests'] - used),
            'grantExpiresAt': epoch(grant['expires']), 'nextAllowedAt': next_allowed,
            'canFetchNow': (not state['complete'] and now >= next_allowed
                            and now < epoch(grant['expires']) and used < grant['maxRequests'])}


UI_WORDS = ()  # Numeric countdown has no localized face words.


def ui_file_hashes(root=ROOT):
    """Historical exact build inputs; kept outside the qualification-bound corpus."""
    root = Path(root)
    owners = [root / 'locales/catalog.json', root / 'watchface/manifest.xml',
              root / 'watchface/source/LocalePresentation.mc',
              root / 'watchface/source/generated/SceneStrings.mc']
    owners += sorted((root / 'locales').glob('*.json'))
    owners += sorted((root / 'watchface/resources/json').glob('Locale*.json'))
    owners += sorted((root / 'watchface/resources/settings').glob('*.xml'))
    owners += sorted((root / 'watchface').glob('resources*/strings/strings.xml'))
    return {str(path.relative_to(root)): digest(path.read_bytes()) for path in owners}


def ui_sources(root=ROOT):
    """Actual face words, needed phone-settings strings and semantic selection.

    Availability/qualification flags, generated gate code and unrelated manifest
    metadata cannot change these text inputs. Exact historical file hashes are
    emitted separately by build(), so activating software admission has no cycle.
    """
    import xml.etree.ElementTree as ET
    root = Path(root)
    catalog = loads((root / 'locales/catalog.json').read_bytes())
    require(len(catalog['locales']) == 36, 'retain36 locale resources')
    ui, menus = {}, {}
    identity = []
    for index, row in enumerate(catalog['locales']):
        loc = row['id']
        identity.append({key: row[key] for key in ('id', 'garmin', 'name')})
        native_path = root / 'watchface/resources/json' / ('Locale' + str(index) + '.json')
        native = loads(native_path.read_bytes())
        require(native['locale'] == loc, 'native locale resource binding changed')
        ui[loc] = {key: native[key] for key in UI_WORDS}
    settings = (root / 'watchface/resources/settings/settings.xml').read_text()
    properties = (root / 'watchface/resources/settings/properties.xml').read_bytes()
    manifest = (root / 'watchface/manifest.xml').read_text()
    needed_ids = sorted(set(re.findall(r'@Strings\.([A-Za-z0-9_]+)', settings + manifest)))
    selections = []
    for node in ET.fromstring(settings):
        config = node.find('settingConfig')
        selections.append({'setting': dict(sorted(node.attrib.items())),
            'config': dict(sorted(config.attrib.items())),
            'entries': [{'attributes': dict(sorted(entry.attrib.items())),
                         'text': entry.text or ''} for entry in config]})
    defaults = [{'attributes': dict(sorted(node.attrib.items())),
                 'text': node.text or ''} for node in ET.fromstring(properties)]
    for source in sorted((root / 'watchface').glob('resources*/strings/strings.xml')):
        actual = {node.attrib['id']: node.text or '' for node in ET.fromstring(source.read_bytes())}
        require(set(needed_ids) <= actual.keys(), 'referenced native menu string missing')
        menus[str(source.relative_to(root))] = {key: actual[key] for key in needed_ids}
    semantic = {'schemaVersion': 1, 'localeIdentity': identity,
        'primaryLocales': catalog['supportPolicy']['primaryLocales'],
        'runtimeWordKeys': list(UI_WORDS), 'neededStringIds': needed_ids,
        'settingsSelections': selections, 'propertyDefaults': defaults,
        'uiWordsSha256': digest(encoded(ui)), 'menuStringsSha256': digest(encoded(menus))}
    return ui, menus, semantic


def build(directory, root=ROOT):
    directory, root = Path(directory), Path(root)
    state = loads((directory / 'collection.json').read_bytes())
    require(state.get('complete') is True and state.get('next') is None, 'complete next=null enumeration required')
    replay = {'count': None, 'pages': []}
    records = []
    for page in state['pages']:
        raw = gzip.decompress((directory / page['raw']).read_bytes())
        require(digest(raw) == page['responseSha256'], 'source response hash mismatch')
        validate_url(page['url'], len(records))
        actual = loads(raw)
        selected = validate_page(actual, replay)
        require(selected == page['records'] and actual['next'] == page['next'], 'projection/source mismatch')
        replay['count'] = actual['count']
        replay['pages'].append(page)
        records.extend(selected)
    require(len(records) == state['count'] == replay['count'], 'exact source count required')
    strings, indices = [], {}
    def intern(value):
        if value is None:
            return None
        if value not in indices:
            indices[value] = len(strings)
            strings.append(value)
        return indices[value]
    launches = []
    for row in records:
        fields = [intern(value) for value in row['texts'][:3]]
        code = intern(row['countryCode'])
        site = row['texts'][5] or row['texts'][3]
        country = row['countryCode'] or row['texts'][4]
        rendered_site = (country + ' · ' + site if country and site else country or site)
        fields.append(intern(rendered_site))
        header = ' · '.join(value for value in row['texts'][:2] if value) or None
        launches.append([row['id'], row['net'], row['sourceIds'], fields, code, fields[3], intern(header)])
    # Hash all36 sources but qualify only native face words/referenced menus.
    ui_inputs, menu_inputs, ui_semantics = ui_sources(root)
    ui = {loc: {key: intern(value) for key, value in values.items()} for loc, values in ui_inputs.items()}
    menus = {path: {key: intern(value) for key, value in values.items()} for path, values in menu_inputs.items()}
    corpus = {'schema': 1, 'windowStart': START, 'windowEnd': 'all published future at source enumeration',
        'source': 'The Space Devs Launch Library2.3 normal',
        'fields': ['rocket', 'operator', 'purpose', 'composedSite'],
        'sourceProjectionFields': list(FIELDS), 'strings': strings,
        'launchColumns': ['id', 'net', 'sourceIds', 'displayStringIndices', 'countryCodeIndex', 'composedSiteIndex', 'composedHeaderIndex'],
        'launches': launches, 'ui': ui, 'menus': menus,
        'neededDisplayIndices': list(range(len(strings))),
        'provenance': {'collectionSha256': digest((directory / 'collection.json').read_bytes()),
            'pages': [{k: page[k] for k in ('url', 'responseSha256', 'receivedAt', 'headers', 'count', 'next')} for page in state['pages']],
            'nativeUiInputs': ui_semantics},
        'coverage': {'launchCount': len(records), 'uniqueLaunchIds': len(set(r['id'] for r in records)),
            'pageCount': len(state['pages']), 'terminalNext': None, 'sourceCount': state['count'],
            'localeCount': len(ui), 'dictionaryCount': len(strings), 'nativeOrArtworkAcceptance': False,
            'earliestNet': records[0]['net'] if records else None, 'latestPublishedNet': records[-1]['net'] if records else None,
            'sourceFieldDistinctCounts': {key: len({r['texts'][i] for r in records if r['texts'][i] is not None}) for i, key in enumerate(FIELDS)},
            'sourceFieldMissingCounts': {key: sum(r['texts'][i] is None for r in records) for i, key in enumerate(FIELDS)},
            'deduplicatedUtf8Bytes': sum(len(t.encode('utf-8')) for t in strings)}}
    raw_corpus = encoded(corpus)
    atomic(directory / 'ui-build-source-receipt.json', encoded({'schemaVersion': 1,
        'sourceFiles': ui_file_hashes(root), 'displayCorpusSha256': digest(raw_corpus),
        'proofBoundary': 'Historical exact build provenance; admission flags are excluded from the semantic corpus digest.'}))
    atomic(directory / 'display-corpus.json', raw_corpus)
    atomic(directory / 'display-texts.json', encoded(strings))
    atomic(directory / 'corpus-manifest.json', encoded({
        'schema': 1, 'displayCorpusSha256': digest(raw_corpus),
        'displayTextsSha256': digest(encoded(strings)), 'coverage': corpus['coverage'],
        'missionPurposeSource': 'mission.type', 'descriptionDisplayIncluded': False,
        'artworkScope': 'Historical display text does not qualify historical rocket artwork; current2026+ artwork remains separate.',
        'qualification': 'Resource coverage only; no native-speaker, SDK, device, hosted or Store acceptance.'}))
    return corpus


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    collect = subs.add_parser('fetch')
    collect.add_argument('--directory', type=Path, required=True)
    collect.add_argument('--grant', type=Path, required=True)
    collect.add_argument('--max-calls', type=int, default=1)
    inspect = subs.add_parser('status')
    inspect.add_argument('--directory', type=Path, required=True)
    inspect.add_argument('--grant', type=Path, required=True)
    generate = subs.add_parser('build')
    generate.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'status':
        print(json.dumps(status(args.directory, args.grant)))
        return
    result = fetch(args.directory, args.grant, args.max_calls) if args.command == 'fetch' else build(args.directory)
    print(json.dumps({'complete': result.get('complete'), 'count': result.get('count'),
                      'coverage': result.get('coverage'), 'pages': len(result.get('pages', []))}))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
