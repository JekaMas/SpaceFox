"""Resumable LL2 metadata traversal, outside the served feed and watch cache.

Every HTTP attempt uses the existing publisher reservation authority. Complete
candidates are immutable facts/provenance, never an active catalog recipe update.
"""
from copy import deepcopy
from dataclasses import dataclass
import base64
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, build_opener, ProxyHandler

from .provider import (Response, _NoRedirect, retry_deadline,
                       validation_epoch)
from .publisher import (StateError, _canonical, _sha, _utc, _catalog_ref,
                        MAX_CATALOG_JOURNAL_BYTES, MAX_CATALOG_OBJECT_BYTES,
                        MAX_CATALOG_CORPUS_BYTES, MAX_CATALOG_OBJECTS)

MAX_PAGE_BYTES = 2097152
MAX_PAGES = 1024
MAX_ROWS = 20000
MAX_SOURCE_AGE_SECONDS = 86400
HTTP_DEADLINE_SECONDS = 20
COLLECTIONS = ('countries', 'organizations', 'models', 'sites')
# Exact LL2 2.3.0 paths/field names are verified against hash-matched primary
# archived responses. Unlike the old active/pending subset audit these tables
# are deliberately unfiltered; flags are facts, not retirement decisions.
PATHS = {'countries': '/2.3.0/config/countries/',
         'organizations': '/2.3.0/agencies/',
         'models': '/2.3.0/launcher_configurations/', 'sites': '/2.3.0/pads/'}
MODES = {'countries': None, 'organizations': 'normal', 'models': 'detailed', 'sites': 'detailed'}
_STORED_PAGE_SIZE = object()


class RefreshError(StateError):
    """Reject invalid source without replacing the previous complete candidate."""


class DuplicateSourceIdentity(RefreshError):
    """A response cannot be incorporated into this traversal."""


def require(condition, message):
    if not condition:
        raise RefreshError(message)


def _pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def strict_json(raw, limit=MAX_PAGE_BYTES):
    require(type(raw) is bytes and len(raw) <= limit, 'catalog JSON byte bound exceeded')
    try:
        source = raw.decode('utf-8')
        depth, quoted, escaped = 0, False, False
        for char in source:
            if quoted:
                if escaped:
                    escaped = False
                elif char == '\\':
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in '[{':
                depth += 1
                require(depth <= 32, 'catalog JSON nesting bound exceeded')
            elif char in ']}':
                depth -= 1
        value = json.loads(source, object_pairs_hook=_pairs,
                           parse_constant=lambda _: require(False, 'nonfinite catalog JSON'))
        todo, count = [value], 0
        while todo:
            item = todo.pop()
            count += 1
            require(count <= 1000000, 'catalog JSON cardinality bound exceeded')
            if type(item) is dict:
                todo.extend(item.values())
            elif type(item) is list:
                todo.extend(item)
            elif type(item) is float:
                require(math.isfinite(item), 'nonfinite catalog number')
        return value
    except (UnicodeError, ValueError, RecursionError) as error:
        raise RefreshError('malformed bounded catalog JSON') from error


def object_ref(raw):
    require(type(raw) is bytes and 1 <= len(raw) <= MAX_CATALOG_OBJECT_BYTES,
            'catalog object exceeds bound')
    return {'sha256': _sha(raw), 'bytes': len(raw)}


def object_path(ref):
    require(type(ref) is dict and set(ref) == {'sha256', 'bytes'}
            and type(ref['sha256']) is str and bool(re.fullmatch('[0-9a-f]{64}', ref['sha256']))
            and type(ref['bytes']) is int and 1 <= ref['bytes'] <= MAX_CATALOG_OBJECT_BYTES,
            'invalid catalog object reference')
    return 'catalog-refresh/objects/' + ref['sha256'] + '.json'


def number(value, optional=False):
    require(value is None and optional or type(value) is int and 1 <= value <= 2147483647,
            'source ID must be a positive integer or explicit unknown')
    return value


def text(value, optional=False, empty=False):
    require(value is None and optional or type(value) is str
            and (bool(value.strip()) or empty) and len(value.encode('utf-8')) <= 4096,
            'invalid source text')
    return value


def count(value):
    require(value is None or type(value) is int and 0 <= value <= 1000000000,
            'invalid source launch count')
    return value


def relation(value):
    require(value is None or type(value) is dict and 'id' in value, 'invalid source relation')
    return None if value is None else number(value['id'])


def relations(value):
    require(type(value) is list and len(value) <= 1000, 'invalid source relation list')
    ids = [relation(v) for v in value]
    require(None not in ids and len(ids) == len(set(ids)), 'duplicate/unknown list relation')
    return ids


def _boolean(row, key):
    require(key in row and type(row[key]) is bool, 'missing/invalid provider flag ' + key)
    return row[key]


def normalize_row(collection, row, origin):
    """Reference-compatible facts only; raw exact body remains the provenance.

    Country kind, official lifecycle/origin, specific artwork and coordinate
    accuracy are not supplied by this import and are never inferred.
    """
    require(type(row) is dict, 'source row must be object')
    try:
        identity = number(row['id'])
        result = {'sourceId': identity, 'name': text(row['name'])}
        if collection == 'countries':
            for source, target, length in [('alpha_2_code', 'alpha2', 2), ('alpha_3_code', 'alpha3', 3)]:
                code = row[source]
                require(type(code) is str and (code == '?' * length or
                        bool(re.fullmatch('[A-Z]{' + str(length) + '}', code))), 'invalid source country code')
                result[target] = code
            result['currentPackFlagId'] = None
            return result
        source_url = row['url']
        require(type(source_url) is str and not any(ord(c) <= 32 or ord(c) == 127 for c in source_url),
                'invalid source row URL characters')
        u, base = urlsplit(source_url), urlsplit(origin)
        require(u.scheme == base.scheme and u.netloc == base.netloc
                and u.path == PATHS[collection] + str(identity) + '/'
                and not u.fragment and u.username is None
                and parse_qs(u.query, keep_blank_values=True) in ({}, {'format': ['json']}),
                'wrong-origin or mismatched source row URL')
        result['sourceUrl'] = source_url
        if collection == 'organizations':
            require(row.get('response_mode') == 'normal', 'normal agency mode required')
            kind = row.get('type')
            require(kind is None or type(kind) is dict, 'invalid agency type')
            if kind is not None:
                kind = {'id': number(kind['id']), 'name': text(kind['name'])}
            result.update(abbrev=text(row['abbrev'], empty=True), type=kind,
                          countryIds=relations(row['country']),
                          providerPendingLaunches=count(row.get('pending_launches')),
                          providerTotalLaunches=count(row.get('total_launch_count')),
                          referenceRoles=[], currentPackBadgeId=None)
        elif collection == 'models':
            require(row.get('response_mode') == 'detailed', 'detailed configuration mode required')
            manufacturer = row['manufacturer']
            result.update(fullName=text(row['full_name']), variant=text(row['variant'], empty=True),
                          providerActive=_boolean(row, 'active'),
                          providerPendingLaunches=count(row['pending_launches']),
                          placeholder=_boolean(row, 'is_placeholder'), familyIds=relations(row['families']),
                          manufacturerId=relation(manufacturer),
                          manufacturerCountryIds=[] if manufacturer is None else relations(manufacturer['country']),
                          currentPackAssetId='generic', currentPackSpecific=False)
        elif collection == 'sites':
            location = row['location']
            require(location is None or type(location) is dict, 'invalid pad location')
            location = location or {}
            body = location.get('celestial_body')
            lat, lon = row['latitude'], row['longitude']
            require(all(v is None or type(v) in (int, float) and math.isfinite(v) for v in (lat, lon)),
                    'invalid source coordinate type')
            finite = lat is not None and lon is not None and -90 <= lat <= 90 and -180 <= lon <= 180
            result.update(providerActive=_boolean(row, 'active'), locationId=relation(location or None),
                          locationName=text(location.get('name'), optional=True), countryId=relation(row['country']),
                          latitude=lat, longitude=lon,
                          coordinateStatus='finite-in-range-unverified' if finite else 'missing-or-invalid',
                          agencyIds=relations(row['agencies']), celestialBodyId=relation(body),
                          celestialBodyName=None if body is None else text(body['name']),
                          providerTotalLaunches=count(row.get('total_launch_count')),
                          providerOrbitalAttempts=count(row.get('orbital_launch_attempt_count')),
                          mapRenderQualification='not-performed')
        return result
    except (KeyError, TypeError, ValueError, UnicodeError) as error:
        if isinstance(error, RefreshError):
            raise
        raise RefreshError('unsupported source row schema') from error


class CatalogHTTPTransport:
    """One credential-free bounded HTTP attempt, no redirects/proxies/retries."""
    def get(self, url, etag=None):
        code = ('import base64,json,sys; from tools.spacefox.catalog_refresh import CatalogHTTPTransport; '
                'r=CatalogHTTPTransport()._direct(sys.argv[1],sys.argv[2] or None); '
                'print(json.dumps([r.status,r.headers,base64.b64encode(r.body).decode("ascii")]))')
        try:
            r = subprocess.run([sys.executable, '-B', '-c', code, url, etag or ''],
                               cwd=Path(__file__).resolve().parents[2], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, timeout=HTTP_DEADLINE_SECONDS, check=False)
            require(r.returncode == 0 and len(r.stdout) <= MAX_PAGE_BYTES * 2, 'bounded catalog HTTP worker failed')
            status, headers, body = json.loads(r.stdout)
            raw = base64.b64decode(body, validate=True)
            require(type(status) is int and type(headers) is dict and len(raw) <= MAX_PAGE_BYTES,
                    'invalid catalog HTTP worker response')
            return Response(status, headers, raw)
        except (subprocess.TimeoutExpired, OSError, ValueError, TypeError) as error:
            raise RefreshError('catalog HTTP deadline or worker failed') from error

    def _direct(self, url, etag=None):
        headers = {'Accept': 'application/json', 'Accept-Encoding': 'identity',
                   'Cache-Control': 'no-cache', 'User-Agent': 'SpaceFox/1 (cached metadata)'}
        if etag is not None:
            headers['If-None-Match'] = etag
        opener = build_opener(ProxyHandler({}), _NoRedirect())
        deadline = time.monotonic() + HTTP_DEADLINE_SECONDS
        try:
            try:
                response = opener.open(Request(url, headers=headers), timeout=10)
            except HTTPError as error:
                response = error
            with response:
                result_headers = {k.lower(): v for k, v in response.headers.items()
                                  if k.lower() in ('date', 'age', 'content-type', 'content-encoding',
                                                   'content-length', 'retry-after', 'etag')}
                require(all(len(response.headers.get_all(k, [])) == 1 and len(v) <= 1024
                            for k, v in result_headers.items()), 'duplicate/oversized catalog HTTP header')
                if response.status != 200:
                    return Response(response.status, result_headers, b'')
                require(result_headers.get('content-encoding', 'identity').lower() == 'identity', 'encoded catalog body')
                length = result_headers.get('content-length')
                require(length is None or length.isascii() and length.isdigit() and int(length) <= MAX_PAGE_BYTES,
                        'catalog Content-Length exceeds bound')
                parts, total = [], 0
                while response.fp is not None:
                    remaining = deadline - time.monotonic()
                    require(remaining > 0, 'catalog read deadline exceeded')
                    response.fp.raw._sock.settimeout(min(10, remaining))
                    chunk = response.read1(min(8192, MAX_PAGE_BYTES + 1 - total))
                    if not chunk:
                        break
                    parts.append(chunk)
                    total += len(chunk)
                    require(total <= MAX_PAGE_BYTES, 'streamed catalog body exceeds bound')
                require(time.monotonic() <= deadline, 'catalog deadline exceeded')
                return Response(200, result_headers, b''.join(parts))
        except (URLError, OSError, AttributeError) as error:
            raise RefreshError('catalog HTTP failed') from error


@dataclass(frozen=True)
class RefreshResult:
    status: str
    requests: int
    completed: dict | None


class CatalogRefresh:
    def __init__(self, publisher, *, origin='https://ll.thespacedevs.com', page_size=_STORED_PAGE_SIZE,
                 max_source_age_seconds=MAX_SOURCE_AGE_SECONDS, schedule_max_pages=2,
                 transport=None, local_http=False, migrate_page_size=False):
        parsed = urlsplit(origin)
        require(parsed.path in ('', '/') and not parsed.query and not parsed.fragment
                and parsed.username is None and parsed.password is None, 'invalid catalog origin')
        if local_http:
            require(parsed.scheme == 'http' and parsed.hostname == '127.0.0.1' and parsed.port is not None,
                    'test HTTP requires explicit IPv4 loopback')
        else:
            require(parsed.scheme == 'https' and parsed.hostname == 'll.thespacedevs.com'
                    and parsed.port in (None, 443), 'production official LL2 origin required')
        use_stored_size = page_size is _STORED_PAGE_SIZE
        if use_stored_size:
            page_size = 20
        require(type(page_size) is int and 1 <= page_size <= 100, 'page size must be1..100')
        require(type(migrate_page_size) is bool and (not migrate_page_size or page_size == 100),
                'qualified page-size migration requires desired100')
        require(type(max_source_age_seconds) is int and 60 <= max_source_age_seconds <= 604800,
                'catalog source age must be60..604800seconds')
        require(type(schedule_max_pages) is int and 1 <= schedule_max_pages <= 4, 'primary request bound must be1..4')
        self.publisher = publisher
        self.origin = origin.rstrip('/')
        self.page_size = page_size
        self.max_age = max_source_age_seconds
        self.migrate_page_size = migrate_page_size
        self.schedule_max_pages = schedule_max_pages
        self.transport = transport or CatalogHTTPTransport()
        self.objects = {}
        ref = publisher.ledger.get('catalog_refresh')
        if ref is None:
            self.journal = self._empty_journal()
        else:
            raw = publisher.store._blob(publisher.head, _catalog_ref(ref), MAX_CATALOG_JOURNAL_BYTES)
            self.journal = strict_json(raw, MAX_CATALOG_JOURNAL_BYTES)
            try:
                if use_stored_size:
                    self.page_size = self._size(self.journal['pageSize'])
                self._check_journal()
            except (KeyError, TypeError, ValueError, AttributeError) as error:
                if isinstance(error, StateError):
                    raise
                raise RefreshError('malformed catalog checkpoint/candidate') from error

    def _empty_journal(self):
        return dict(schemaVersion=2 if self.migrate_page_size else 1, origin=self.origin,
                    pageSize=self.page_size, maxSourceAgeSeconds=self.max_age,
                    staging=None, cache={}, current=None, previous=None)

    def _check_journal(self):
        j = self.journal
        require(type(j) is dict and set(j) == {'schemaVersion', 'origin', 'pageSize', 'maxSourceAgeSeconds',
                                             'staging', 'cache', 'current', 'previous'}
                and type(j['schemaVersion']) is int and j['schemaVersion'] in (1, 2),
                'unsupported catalog journal')
        self._size(j['pageSize'])
        require(type(j['maxSourceAgeSeconds']) is int
                and (j['origin'], j['maxSourceAgeSeconds']) == (self.origin, self.max_age)
                and (j['pageSize'] == self.page_size or self.migrate_page_size),
                'checkpoint query/policy changed; use original collector settings')
        require(type(j['cache']) is dict and len(j['cache']) <= MAX_PAGES, 'catalog cache index exceeds bound')
        for ref in (j['current'], j['previous']):
            if ref is not None:
                candidate = strict_json(self._read(ref), MAX_CATALOG_OBJECT_BYTES)
                require(candidate.get('complete') is True and type(candidate.get('schemaVersion')) is int
                        and candidate['schemaVersion'] in (1, 2),
                        'referenced catalog candidate is not complete')
                sizes = self._candidate_sizes(candidate)
                if j['schemaVersion'] == 1:
                    require(candidate['schemaVersion'] == 1 and all(v == j['pageSize'] for v in sizes.values()),
                            'legacy candidate query policy differs from journal')
                data, remaining, _, _, _ = self._assemble(candidate['coverage']['pages'], sizes)
                require(remaining is None, 'complete candidate has incomplete pages')
                for collection in COLLECTIONS:
                    data[collection].sort(key=lambda row: row['sourceId'])
                require(candidate['reference'] == data and candidate['coverage']['counts'] ==
                        {c: len(data[c]) for c in COLLECTIONS} and candidate['coverage']['distinctIds'] ==
                        {c: [r['sourceId'] for r in data[c]] for c in COLLECTIONS},
                        'complete candidate differs from raw source proof')
                require(candidate['coverage']['recordValidatedUtc'] == self._record_epochs(candidate['coverage']['pages']),
                        'complete candidate record ages differ from page proof')
                epochs = [page['validatedUtc'] for page in candidate['coverage']['pages']]
                source = candidate['source']
                require(source['observedFromUtc'] == min(epochs) and source['observedToUtc'] == max(epochs)
                        and all(source['completedUtc'] - self.max_age <= epoch <= source['completedUtc'] for epoch in epochs),
                        'complete candidate source-date age proof mismatch')
        # Replay the stored prefix through the actual page/typed normalizer. A
        # hash-consistent malformed journal cannot manufacture a complete prefix.
        if j['staging'] is not None:
            stage = j['staging']
            require(type(stage) is dict and set(stage) == ({'startedUtc', 'pages'} if j['schemaVersion'] == 1
                    else {'startedUtc', 'pages', 'pageSizes'}), 'invalid catalog staging')
            _utc(stage['startedUtc'])
            require(type(stage['pages']) is list and len(stage['pages']) <= MAX_PAGES, 'catalog page bound exceeded')
            self._assemble(stage['pages'], self._stage_sizes())
        for url, meta in j['cache'].items():
            require(type(meta) is dict and set(meta) == ({'body', 'etag'} if j['schemaVersion'] == 1
                    else {'body', 'etag', 'pageSize'}), 'invalid catalog cache entry')
            size = j['pageSize'] if j['schemaVersion'] == 1 else self._size(meta['pageSize'])
            self._etag(meta['etag'])
            self._read(meta['body'])
            require(any(self._valid_url(c, url, page_size=size) for c in COLLECTIONS), 'unsafe cache URL')
        if self.migrate_page_size and (j['schemaVersion'] == 1 or j['pageSize'] != self.page_size):
            old_size = j['pageSize']
            sizes = self._stage_sizes()
            stage = j['staging']
            if stage is not None:
                # Every already-started collection keeps its complete query
                # binding. No committed page/link is changed or redownloaded.
                started = {p['collection'] for p in stage['pages']}
                stage['pageSizes'] = {c: sizes[c] if c in started else self.page_size for c in COLLECTIONS}
            if j['schemaVersion'] == 1:
                for meta in j['cache'].values():
                    meta['pageSize'] = old_size
            j['schemaVersion'], j['pageSize'] = 2, self.page_size

    @staticmethod
    def _size(value):
        require(type(value) is int and 1 <= value <= 100, 'page size must be1..100')
        return value

    def _stage_sizes(self):
        stage = self.journal['staging']
        sizes = (stage['pageSizes'] if self.journal['schemaVersion'] == 2 and stage is not None
                 else {c: self.journal['pageSize'] for c in COLLECTIONS})
        require(type(sizes) is dict and set(sizes) == set(COLLECTIONS), 'invalid collection query policy')
        for size in sizes.values():
            self._size(size)
        return sizes

    def _candidate_sizes(self, candidate):
        queries = candidate['coverage']['queries']
        require(type(queries) is dict and set(queries) == set(COLLECTIONS), 'invalid candidate queries')
        sizes = {}
        for collection in COLLECTIONS:
            query = parse_qs(urlsplit(queries[collection]).query, strict_parsing=True)
            limit = query.get('limit', [])
            require(len(limit) == 1 and bool(re.fullmatch('[1-9][0-9]*', limit[0])), 'invalid candidate page size')
            sizes[collection] = self._size(int(limit[0]))
            require(self._valid_url(collection, queries[collection], 0, sizes[collection]), 'unsafe candidate query')
        source = candidate['source']
        require(source['baseUrl'] == self.origin + '/2.3.0/' and type(source['maxSourceAgeSeconds']) is int
                and source['maxSourceAgeSeconds'] == self.max_age, 'candidate source policy differs from journal')
        if candidate['schemaVersion'] == 2:
            policy = candidate['queryPolicy']
            require(type(policy) is dict and set(policy) == {'origin', 'pageSizes', 'maxSourceAgeSeconds'}
                    and type(policy['maxSourceAgeSeconds']) is int
                    and type(policy['pageSizes']) is dict and set(policy['pageSizes']) == set(COLLECTIONS),
                    'invalid candidate query policy')
            for size in policy['pageSizes'].values():
                self._size(size)
            require(policy == dict(origin=self.origin, pageSizes=sizes,
                    maxSourceAgeSeconds=self.max_age), 'candidate query policy mismatch')
        return sizes

    def _read(self, ref):
        path = object_path(ref)
        raw = self.objects.get(path)
        if raw is None:
            require(len(self.objects) < MAX_CATALOG_OBJECTS and
                    sum(map(len, self.objects.values())) + ref['bytes'] <= MAX_CATALOG_CORPUS_BYTES,
                    'catalog loaded corpus exceeds finite working-set bound')
            raw = self.publisher.store._blob(self.publisher.head, path, MAX_CATALOG_OBJECT_BYTES)
        require(len(raw) == ref['bytes'] and _sha(raw) == ref['sha256'], 'catalog object digest mismatch')
        self.objects[path] = raw
        return raw

    def _put(self, raw):
        ref = object_ref(raw)
        self.objects[object_path(ref)] = raw
        return ref

    def _url(self, collection, offset, page_size=None):
        query = {'format': 'json', 'limit': str(self.page_size if page_size is None else page_size)}
        if MODES[collection] is not None:
            query['mode'] = MODES[collection]
        if offset:
            query['offset'] = str(offset)
        return self.origin + PATHS[collection] + '?' + urlencode(query)

    def _valid_url(self, collection, url, offset=None, page_size=None):
        try:
            if type(url) is not str or any(ord(c) <= 32 or ord(c) == 127 for c in url):
                return False
            u, base = urlsplit(url), urlsplit(self.origin)
            if not (u.scheme == base.scheme and u.netloc == base.netloc and u.path == PATHS[collection]
                    and not u.fragment and u.username is None):
                return False
            query = parse_qs(u.query, strict_parsing=True, keep_blank_values=True)
            supplied = query.get('offset', ['0'])
            if len(supplied) != 1 or not re.fullmatch('0|[1-9][0-9]*', supplied[0]):
                return False
            value = int(supplied[0])
            if offset is not None and value != offset:
                return False
            expected = parse_qs(urlsplit(self._url(collection, value, page_size)).query)
            return query == expected
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _etag(value):
        require(value is None or type(value) is str and 1 <= len(value) <= 512
                and bool(re.fullmatch(r'(?:W/)?"[\x21\x23-\x7e]*"', value)), 'invalid ETag')
        return value

    def _page(self, collection, raw, offset, expected, page_size=None):
        page_size = self.page_size if page_size is None else page_size
        page = strict_json(raw)
        require(type(page) is dict and {'count', 'next', 'previous', 'results'} <= page.keys(), 'incomplete collection page')
        total = page['count']
        require(type(total) is int and 0 <= total <= MAX_ROWS and (expected is None or total == expected),
                'invalid/drifting collection count')
        rows = page['results']
        require(type(rows) is list and len(rows) <= page_size, 'invalid collection page cardinality')
        received = offset + len(rows)
        require(received <= total, 'collection exceeds declared count')
        following = page['next']
        require(following is None or type(following) is str and self._valid_url(collection, following, received, page_size)
                and len(rows) > 0, 'unsafe/nonadvancing pagination')
        require(following is not None or received == total, 'truncated collection')
        require(following is None or received < total, 'next page after declared count')
        prior = page['previous']
        require(prior is None if offset == 0 else type(prior) is str and
                self._valid_url(collection, prior, max(0, offset - page_size), page_size), 'invalid previous page link')
        normalized = [normalize_row(collection, row, self.origin) for row in rows]
        return total, following, normalized

    def _assemble(self, pages, page_sizes=None):
        sizes = self._stage_sizes() if page_sizes is None else page_sizes
        data = {c: [] for c in COLLECTIONS}
        seen = {c: set() for c in COLLECTIONS}
        expected = None
        index, offset, url = 0, 0, self._url(COLLECTIONS[0], 0, sizes[COLLECTIONS[0]])
        for page in pages:
            require(type(page) is dict and set(page) == {'collection', 'url', 'body', 'etag', 'validatedUtc',
                                                       'receivedUtc', 'status', 'count', 'rows', 'next'}, 'invalid page checkpoint')
            require(index < len(COLLECTIONS), 'page after collection completion')
            collection = COLLECTIONS[index]
            require(page['collection'] == collection and self._valid_url(collection, page['url'], offset, sizes[collection]),
                    'checkpoint page sequence mismatch')
            _utc(page['validatedUtc'])
            _utc(page['receivedUtc'])
            require(page['validatedUtc'] <= page['receivedUtc'] and page['status'] in (200, 304), 'invalid page source epoch/status')
            self._etag(page['etag'])
            total, following, rows = self._page(collection, self._read(page['body']), offset, expected, sizes[collection])
            require((total, len(rows), following) == (page['count'], page['rows'], page['next']), 'page checkpoint facts mismatch')
            ids = [row['sourceId'] for row in rows]
            require(len(set(ids)) == len(ids) and not seen[collection].intersection(ids), 'duplicate source identity')
            seen[collection].update(ids)
            data[collection].extend(rows)
            offset += len(rows)
            expected = total
            if following is None:
                index += 1
                offset, expected = 0, None
                url = None if index == len(COLLECTIONS) else self._url(COLLECTIONS[index], 0, sizes[COLLECTIONS[index]])
            else:
                url = following
        return data, (None if index == len(COLLECTIONS) else COLLECTIONS[index]), url, offset, expected

    def _save(self, now):
        try:
            raw = _canonical(self.journal)
            require(len(raw) <= MAX_CATALOG_JOURNAL_BYTES, 'catalog journal exceeds bound')
            ref = object_ref(raw)
            needed = {_catalog_ref(ref): raw}
            refs = [m['body'] for m in self.journal['cache'].values()]
            stage = self.journal['staging']
            refs.extend(p['body'] for p in ([] if stage is None else stage['pages']))
            for candidate_ref in (self.journal['current'], self.journal['previous']):
                if candidate_ref is not None:
                    candidate_raw = self._read(candidate_ref)
                    needed[object_path(candidate_ref)] = candidate_raw
                    candidate = strict_json(candidate_raw, MAX_CATALOG_OBJECT_BYTES)
                    refs.extend(p['body'] for p in candidate['coverage']['pages'])
            for item in refs:
                needed[object_path(item)] = self._read(item)
            require(len(needed) <= MAX_CATALOG_OBJECTS and sum(map(len, needed.values())) <= MAX_CATALOG_CORPUS_BYTES,
                    'catalog corpus exceeds finite working-set bound')
            self.publisher.checkpoint_catalog(self.publisher.head, now, ref, needed)
        except Exception:
            # Preflight bounds and CAS are one save boundary. Neither refusal
            # may expose an uncommitted complete flag or retain scratch objects.
            # Actual CAS conflicts still require a new reconciled owner.
            durable = self.publisher.ledger.get('catalog_refresh')
            if durable is None:
                self.journal = self._empty_journal()
            else:
                self.journal = strict_json(self.publisher.store._blob(
                    self.publisher.head, _catalog_ref(durable), MAX_CATALOG_JOURNAL_BYTES), MAX_CATALOG_JOURNAL_BYTES)
            self.objects = {}
            raise
        self.objects = {path: value for path, value in needed.items() if '/objects/' in path}

    def current(self):
        ref = self.journal['current']
        return None if ref is None else strict_json(self._read(ref), MAX_CATALOG_OBJECT_BYTES)

    def _record_epochs(self, pages):
        result = {collection: {} for collection in COLLECTIONS}
        for page in pages:
            for row in strict_json(self._read(page['body']))['results']:
                result[page['collection']][str(row['id'])] = page['validatedUtc']
        return result

    def _candidate(self, data, pages, now):
        require(pages and all(now - self.max_age <= p['validatedUtc'] <= now for p in pages),
                'catalog traversal exceeds source-date age bound; restart required')
        ids = {c: {r['sourceId'] for r in data[c]} for c in COLLECTIONS}
        edges = []
        def edge(owner, kind, value):
            if value is not None:
                require(value in ids[kind], 'dangling ' + kind + ' relation')
                edges.append([owner, kind, value])
        for row in data['organizations']:
            for value in row['countryIds']:
                edge('organization:' + str(row['sourceId']), 'countries', value)
        for row in data['models']:
            owner = 'configuration:' + str(row['sourceId'])
            edge(owner, 'organizations', row['manufacturerId'])
            for value in row['manufacturerCountryIds']:
                edge(owner, 'countries', value)
        for row in data['sites']:
            owner = 'site:' + str(row['sourceId'])
            edge(owner, 'countries', row['countryId'])
            for value in row['agencyIds']:
                edge(owner, 'organizations', value)
        upcoming = []
        required_models = {r['sourceId'] for r in data['models'] if r['providerActive'] or (r['providerPendingLaunches'] or 0) > 0}
        required_sites = {r['sourceId'] for r in data['sites'] if r['providerActive']}
        for entry in self.publisher.schedule.entries:
            record = entry.record
            item = {'launchId': list(record.launch_id.key), 'sourceValidatedUtc': record.source_validated_utc, 'references': {}}
            for field, kind in [('configuration_id', 'models'), ('operator_id', 'organizations'), ('site_id', 'sites'), ('country_id', 'countries')]:
                identity = getattr(record, field)
                if identity is not None and identity.namespace == 'll2':
                    require(identity.value.isascii() and identity.value.isdigit(), 'noninteger LL2 metadata reference')
                    value = int(identity.value)
                    edge('launch:' + record.launch_id.value, kind, value)
                    item['references'][kind] = value
                    if kind == 'models':
                        required_models.add(value)
                    elif kind == 'sites':
                        required_sites.add(value)
            upcoming.append(item)
        missing, retained = {}, {}
        record_epochs = self._record_epochs(pages)
        previous = self.current()
        for collection in COLLECTIONS:
            missing[collection], retained[collection] = [], []
            if previous is not None:
                old = {r['sourceId']: {'fact': r, 'lastObservedUtc': previous['coverage']['recordValidatedUtc'][collection][str(r['sourceId'])]}
                       for r in previous['reference'][collection]}
                old.update({r['fact']['sourceId']: r for r in previous['retainedMissing'][collection]})
                for identity, item in sorted(old.items()):
                    if identity not in ids[collection]:
                        missing[collection].append(identity)
                        retained[collection].append(deepcopy(item))
            data[collection].sort(key=lambda r: r['sourceId'])
        candidate = dict(schemaVersion=self.journal['schemaVersion'], complete=True,
                    source=dict(provider='The Space Devs Launch Library 2', apiVersion='2.3.0', baseUrl=self.origin + '/2.3.0/',
                                observedFromUtc=min(p['validatedUtc'] for p in pages), observedToUtc=max(p['validatedUtc'] for p in pages),
                                completedUtc=now, maxSourceAgeSeconds=self.max_age,
                                scope='Complete unfiltered typed provider-table pagination; multi-request nontransactional traversal, not worldwide official operational completeness.'),
                    reference=data, retainedMissing=retained, missingComparedToPrevious=missing,
                    coverage=dict(pages=deepcopy(pages), queries={c: self._url(c, 0, self._stage_sizes()[c]) for c in COLLECTIONS},
                                  counts={c: len(data[c]) for c in COLLECTIONS}, distinctIds={c: sorted(ids[c]) for c in COLLECTIONS},
                                  recordValidatedUtc=record_epochs,
                                  relations=sorted(edges), upcomingReferences=upcoming,
                                  acceptedScheduleSha256=_sha(_canonical(self.publisher.ledger['accepted'])),
                                  requiredModelIds=sorted(required_models), requiredSiteIds=sorted(required_sites),
                                  requiredNonPlaceholderModelIds=sorted(r['sourceId'] for r in data['models']
                                                                       if r['sourceId'] in required_models and not r['placeholder']),
                                  unknownJurisdictionIds=sorted(r['sourceId'] for r in data['countries'] if r['alpha2'] == '??' or r['alpha3'] == '???'),
                                  jurisdictionKinds={str(r['sourceId']): 'unknown' if r['alpha2'] == '??' or r['alpha3'] == '???'
                                                     else 'unclassified' for r in data['countries']},
                                  numericallyValidSitePositions=sum(r['coordinateStatus'] == 'finite-in-range-unverified' for r in data['sites']),
                                  specificVisualMappings=0, verifiedCountryMarks=0, verifiedOrganizationMarks=0,
                                  externalRelationIds=dict(families=sorted({v for r in data['models'] for v in r['familyIds']}),
                                                           locations=sorted({r['locationId'] for r in data['sites'] if r['locationId'] is not None}),
                                                           celestialBodies=sorted({r['celestialBodyId'] for r in data['sites'] if r['celestialBodyId'] is not None})),
                                  worldwideOfficialSupplementClosure=False, artworkQualification=False, coordinateAccuracyQualification=False),
                    previousComplete=self.journal['current'])
        if self.journal['schemaVersion'] == 2:
            candidate['queryPolicy'] = dict(origin=self.origin, pageSizes=deepcopy(self._stage_sizes()),
                                           maxSourceAgeSeconds=self.max_age)
        return candidate

    def _cache_entry(self, page, page_size):
        entry = {'body': page['body'], 'etag': page['etag']}
        if self.journal['schemaVersion'] == 2:
            entry['pageSize'] = page_size
        return entry

    def run(self, now, *, max_requests=1, clock=None, restart=False):
        require(type(max_requests) is int and 1 <= max_requests <= 4, 'bounded invocation requires1..4requests')
        _utc(now)
        def sample():
            value = now if clock is None else clock()
            _utc(value)
            require(value >= now, 'catalog runtime clock regressed')
            return value
        # Recheck source/base before any work, including cache-only completion.
        self.publisher._context(self.publisher.head)
        if self.publisher.ledger.get('catalog_refresh') is not None:
            durable = self.publisher.ledger['catalog_refresh']
            self.journal = strict_json(self.publisher.store._blob(
                self.publisher.head, _catalog_ref(durable), MAX_CATALOG_JOURNAL_BYTES), MAX_CATALOG_JOURNAL_BYTES)
            self._check_journal()
        if restart or self.journal['staging'] is None and self.journal['current'] is None:
            self.journal['staging'] = {'startedUtc': sample(), 'pages': []}
            if self.journal['schemaVersion'] == 2:
                self.journal['staging']['pageSizes'] = {c: self.page_size for c in COLLECTIONS}
            self._save(sample())
        if self.journal['staging'] is None:
            return RefreshResult('complete', 0, self.journal['current'])
        # A traversal cannot become complete with expired raw proofs. Restart
        # without changing any page's source date or accepted schedule age.
        stage = self.journal['staging']
        checked_at = sample()
        if any(p['validatedUtc'] < checked_at - self.max_age for p in stage['pages']):
            for page in stage['pages']:
                self.journal['cache'].pop(page['url'], None)
            self.journal['staging'] = {'startedUtc': checked_at, 'pages': []}
            if self.journal['schemaVersion'] == 2:
                self.journal['staging']['pageSizes'] = {c: self.page_size for c in COLLECTIONS}
            self._save(checked_at)
        attempts = 0
        for _ in range(max_requests):
            stage = self.journal['staging']
            data, collection, url, offset, expected = self._assemble(stage['pages'])
            if collection is None:
                break
            require(len(stage['pages']) < MAX_PAGES, 'catalog page budget exhausted')
            requested_at = sample()
            token = self.publisher.reserve_catalog(self.publisher.head, requested_at, schedule_max_pages=self.schedule_max_pages)
            if token is None:
                return RefreshResult('yielded', attempts, self.journal['current'])
            cache = self.journal['cache'].get(url)
            etag = None if cache is None else cache['etag']
            received_at = None
            response = None
            try:
                attempts += 1
                response = self.transport.get(url, etag)
                received_at = sample()
                require(response.status in (200, 304), 'catalog HTTP status ' + str(response.status))
                headers = {k.lower(): v for k, v in response.headers.items()}
                if response.status == 304:
                    require(cache is not None and etag is not None and not response.body, '304 without exact conditional cache')
                    require(headers.get('etag', etag) == etag, '304 changed ETag')
                    body = self._read(cache['body'])
                    headers.setdefault('content-type', 'application/json')
                else:
                    body = response.body
                epoch = validation_epoch(Response(200, headers, body), received_at)
                require(received_at - self.max_age <= epoch, 'catalog source Date/Age too old')
                size = self._stage_sizes()[collection]
                total, following, rows = self._page(collection, body, offset, expected, size)
                old_ids = {row['sourceId'] for row in data[collection]}
                new_ids = [row['sourceId'] for row in rows]
                if len(new_ids) != len(set(new_ids)) or old_ids.intersection(new_ids):
                    raise DuplicateSourceIdentity('duplicate source identity')
                page = dict(collection=collection, url=url, body=self._put(body), etag=self._etag(headers.get('etag', etag if response.status == 304 else None)),
                            validatedUtc=epoch, receivedUtc=received_at, status=response.status, count=total, rows=len(rows), next=following)
                # Validate tentative whole-prefix and resource limits before
                # committing it; failures retain the previous durable page.
                tentative = deepcopy(self.journal)
                tentative['staging']['pages'].append(page)
                tentative['cache'][url] = self._cache_entry(page, size)
                require(len(tentative['cache']) <= MAX_PAGES, 'catalog cache URL budget exhausted')
                require(len(_canonical(tentative)) <= MAX_CATALOG_JOURNAL_BYTES, 'catalog journal byte budget exhausted')
                self.publisher.finish_request(self.publisher.head, token, received_at, 'success')
                token = None
                self.journal = tentative
                self._save(received_at)
            except Exception as error:
                # A tentative prefix can fail before _save owns rollback. Its
                # raw body must not accumulate across valid failure retries.
                # Durable pages/candidates can be reloaded by content address.
                self.objects = {}
                if token is not None:
                    failed_at = sample() if received_at is None else received_at
                    throttled = response is not None and response.status == 429
                    self.publisher.finish_request(self.publisher.head, token, failed_at, 'throttled' if throttled else 'failed',
                                                  retry_after_utc=retry_deadline(response.headers, failed_at) if throttled else None)
                if isinstance(error, DuplicateSourceIdentity):
                    # A poisoned prefix can reproduce the overlap forever.
                    # Retain complete earlier tables and their exact ages; the
                    # current table restarts unconditionally on a later call.
                    # No invalid response is admitted and failed quota remains.
                    stage = self.journal['staging']
                    stage['pages'] = [p for p in stage['pages'] if p['collection'] != collection]
                    self.journal['cache'] = {key: value for key, value in self.journal['cache'].items()
                                             if not self._valid_url(collection, key, page_size=(
                                                 self.journal['pageSize'] if self.journal['schemaVersion'] == 1
                                                 else value['pageSize']))}
                    self._save(failed_at)
                raise
        data, collection, _, _, _ = self._assemble(self.journal['staging']['pages'])
        if collection is None:
            completed_at = sample()
            candidate = self._candidate(data, self.journal['staging']['pages'], completed_at)
            reference = self._put(_canonical(candidate))
            self.journal['previous'] = self.journal['current']
            self.journal['current'] = reference
            sizes = self._stage_sizes()
            self.journal['cache'] = {p['url']: self._cache_entry(p, sizes[p['collection']]) for p in self.journal['staging']['pages']}
            self.journal['staging'] = None
            self._save(completed_at)
            return RefreshResult('complete', attempts, reference)
        return RefreshResult('partial', attempts, self.journal['current'])


def reference_inventory(candidate):
    """Explicit data-only integration input; never writes the active recipe.

    This has the existing immutable reference inventory's four row collections
    and exact row field sets. All artwork fields remain unqualified defaults;
    reviewed mappings/curations must be reconciled by the later integration.
    """
    require(type(candidate) is dict and candidate.get('complete') is True, 'complete candidate required')
    source = candidate['source']
    from datetime import datetime, timezone
    iso = lambda value: datetime.fromtimestamp(value, timezone.utc).isoformat()
    return dict(schemaVersion=1, purpose='Complete provider metadata candidate only; reviewed recipe/artwork/official supplement integration pending.',
                source=dict(provider=source['provider'], apiVersion=source['apiVersion'], baseUrl=source['baseUrl'],
                            docsUrl='https://ll.thespacedevs.com/docs/', termsUrl='https://github.com/TheSpaceDevs/Tutorials/blob/main/faqs/faq_TSD.md',
                            observedFromUTC=iso(source['observedFromUtc']), observedToUTC=iso(source['observedToUtc']), scope=source['scope']),
                queries=deepcopy(candidate['coverage']['queries']), **deepcopy(candidate['reference']), mapBaseline={})
