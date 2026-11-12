"""Bounded LL2 2.3 normal-mode adapter; all HTTP requires durable permission.

The transport has no automatic retries, redirects, credentials or cache renewal.
Use LL2Client through update_feed: one committed Publisher reservation per call.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import base64
from pathlib import Path
import subprocess
import sys
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import uuid

from .schedule import (IdKind, StableId, Timing, TimePrecision, LaunchStatus,
                       LaunchRecord)

MAX_RESPONSE_BYTES = 524288
MAX_DEPTH = 32
MAX_NODES = 30000
MAX_RECORDS = 80
TIMEOUT_SECONDS = 10
TOTAL_TIMEOUT_SECONDS = 20
PATH = '/2.3.0/launches/upcoming/'
DEFAULT_ORIGIN = 'https://ll.thespacedevs.com'


class ProviderError(ValueError):
    """No provider facts may be accepted from this response."""


class Throttled(ProviderError):
    def __init__(self, retry_at):
        self.retry_at = retry_at
        super().__init__('provider throttled; durable backoff required')


def _require(condition, message):
    if not condition:
        raise ProviderError(message)


def _pairs(items):
    value = {}
    for key, item in items:
        _require(key not in value, 'duplicate provider JSON key')
        value[key] = item
    return value


def _bad_constant(value):
    raise ProviderError('nonfinite provider JSON')


def bounded_json(raw):
    """Check UTF8/bytes/nesting before JSON allocation, then bound cardinality."""
    _require(type(raw) is bytes and len(raw) <= MAX_RESPONSE_BYTES, 'provider byte bound exceeded')
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
                _require(depth <= MAX_DEPTH, 'provider nesting bound exceeded')
            elif char in ']}':
                depth -= 1
        value = json.loads(source, object_pairs_hook=_pairs, parse_constant=_bad_constant)
        todo, count = [value], 0
        while todo:
            item = todo.pop()
            count += 1
            _require(count <= MAX_NODES, 'provider cardinality bound exceeded')
            if type(item) is dict:
                todo.extend(item.values())
            elif type(item) is list:
                todo.extend(item)
        return value
    except (UnicodeError, RecursionError, json.JSONDecodeError) as error:
        raise ProviderError('malformed strict UTF8 provider JSON') from error


def timestamp(value):
    """Only explicit-offset ISO timestamps; never local/naive/date-only UTC."""
    _require(type(value) is str and bool(re.fullmatch(
        r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?(?:Z|[+-]\d\d:\d\d)', value)),
        'timestamp needs explicit timezone and seconds')
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        _require(parsed.utcoffset() is not None, 'naive provider timestamp')
        utc = parsed.astimezone(timezone.utc)
        delta = utc - datetime(1970, 1, 1, tzinfo=timezone.utc)
        return delta.days * 86400 + delta.seconds
    except (ValueError, OverflowError) as error:
        raise ProviderError('invalid provider timestamp') from error


def _object(value, label, optional=False):
    if value is None and optional:
        return {}
    _require(type(value) is dict, f'{label} must be an object')
    return value


def _text(value, *, limit=4096):
    if value is None or value == '':
        return None
    _require(type(value) is str, 'provider text must be a string/null')
    value = value.strip()
    if not value:
        return None
    _require(len(value.encode('utf-8')) <= limit, 'provider text exceeds field bound')
    # Descriptions may contain line breaks; normalize their whitespace explicitly.
    return ' '.join(value.split())


def _id(obj, kind):
    if not obj or obj.get('id') is None:
        return None
    value = obj['id']
    _require(type(value) is int and value > 0, 'related LL2 identity must be positive integer')
    return StableId(kind, 'll2', str(value))


def _country_code(country):
    for field, length in (('alpha_2_code', 2), ('alpha_3_code', 3)):
        value = _text(country.get(field), limit=3)
        if value is None or value == '?' * length:
            continue  # LL2 explicitly uses ??/??? for unknown jurisdiction.
        _require(bool(re.fullmatch(r'[A-Z]{' + str(length) + '}', value)), 'invalid sourced country code')
        return value
    return None


def normalize_launch(row, validated_utc):
    row = _object(row, 'launch')
    _require(row.get('response_mode', 'normal') == 'normal', 'normal launch mode required')
    try:
        identity = row['id']
        _require(type(identity) is str and str(uuid.UUID(identity)) == identity, 'canonical LL2 launch UUID required')
        status = _object(row['status'], 'status')
        status_id = status['id']
        _require(type(status_id) is int and status_id >= 0, 'invalid status identity')
        phase = {1: LaunchStatus.PENDING, 2: LaunchStatus.PENDING, 5: LaunchStatus.PENDING,
                 8: LaunchStatus.PENDING, 3: LaunchStatus.COMPLETED, 4: LaunchStatus.COMPLETED,
                 7: LaunchStatus.COMPLETED, 6: LaunchStatus.STARTED, 9: LaunchStatus.STARTED}.get(status_id, LaunchStatus.UNKNOWN)
        precision = _object(row.get('net_precision'), 'NET precision', optional=True)
        precision_id = precision.get('id')
        _require(precision_id is None or type(precision_id) is int and precision_id >= 0, 'invalid NET precision identity')
        net = row.get('net')
        nominal = None if net is None else timestamp(net)
        start = None if row.get('window_start') is None else timestamp(row['window_start'])
        end = None if row.get('window_end') is None else timestamp(row['window_end'])
        name, abbrev = _text(precision.get('name'), limit=100), _text(precision.get('abbrev'), limit=40)
        # Only documented second precision creates a second-level target. Minute,
        # hour, local morning/day/month and future precision IDs remain coarse.
        exact = (nominal is not None and precision_id == 0 and name == 'Second' and abbrev == 'SEC'
                 and datetime.fromisoformat(net.replace('Z', '+00:00')).microsecond == 0)
        timing = Timing(TimePrecision.EXACT if exact else (TimePrecision.SOURCE_COARSE if nominal is not None
                         else (TimePrecision.WINDOW if start is not None or end is not None else TimePrecision.UNKNOWN)),
                        exact_utc=nominal if exact else None, window_start_utc=start, window_end_utc=end,
                        nominal_utc=nominal, source_net=net, source_precision_id=precision_id,
                        source_precision_name=name, source_precision_abbrev=abbrev,
                        source_precision_description=_text(precision.get('description'), limit=512))
        source_updated = timestamp(row['last_updated'])
        _require(source_updated <= validated_utc, 'source content modification exceeds origin validation time')
        rocket = _object(row.get('rocket'), 'rocket', optional=True)
        configuration = _object(rocket.get('configuration'), 'configuration', optional=True)
        operator = _object(row.get('launch_service_provider'), 'operator', optional=True)
        pad = _object(row.get('pad'), 'pad', optional=True)
        country = _object(pad.get('country'), 'pad country', optional=True)
        location = _object(pad.get('location'), 'pad location', optional=True)
        mission = _object(row.get('mission'), 'mission', optional=True)
        return LaunchRecord(StableId(IdKind.LAUNCH, 'll2', identity), timing, phase, validated_utc,
                            configuration_id=_id(configuration, IdKind.CONFIGURATION),
                            operator_id=_id(operator, IdKind.ORGANIZATION), site_id=_id(pad, IdKind.SITE),
                            country_id=_id(country, IdKind.COUNTRY),
                            configuration_name=_text(configuration.get('full_name') or configuration.get('name'), limit=256),
                            operator_name=_text(operator.get('name'), limit=256), mission_name=_text(mission.get('name'), limit=256),
                            mission_purpose=_text(mission.get('description')), source_updated_utc=source_updated,
                            source_updated_iso=row['last_updated'],
                            source_updated_subsecond=datetime.fromisoformat(row['last_updated'].replace('Z', '+00:00')).microsecond,
                            source_status_id=status_id, source_status_name=_text(status.get('name'), limit=100),
                            site_name=_text(pad.get('name'), limit=256), country_name=_text(country.get('name'), limit=256),
                            country_code=_country_code(country), site_location_name=_text(location.get('name'), limit=256))
    except (KeyError, ValueError, TypeError, UnicodeError) as error:
        if isinstance(error, ProviderError):
            raise
        raise ProviderError(f'invalid normalized launch: {error}') from error


@dataclass(frozen=True)
class Response:
    status: int
    headers: dict
    body: bytes


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class HTTPTransport:
    """Real bounded direct HTTP, with redirects and environment proxies disabled."""
    def __init__(self):
        from urllib.request import ProxyHandler
        self.opener = build_opener(ProxyHandler({}), _NoRedirect())

    def get(self, url):
        # A process deadline also bounds DNS/TLS and kills the underlying request;
        # an abandoned resolver thread must not send a delayed request later.
        code = ("import base64,json,sys; from tools.spacefox.provider import HTTPTransport; "
                "r=HTTPTransport()._get_direct(sys.argv[1]); "
                "print(json.dumps([r.status,r.headers,base64.b64encode(r.body).decode('ascii')]))")
        try:
            result = subprocess.run([sys.executable, '-B', '-c', code, url],
                                    cwd=Path(__file__).resolve().parents[2],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    timeout=TOTAL_TIMEOUT_SECONDS, check=False)
        except (subprocess.TimeoutExpired, OSError) as error:
            raise ProviderError('provider process deadline or execution failed') from error
        _require(result.returncode == 0 and len(result.stdout) <= MAX_RESPONSE_BYTES * 2,
                 'provider bounded worker failed')
        try:
            status, headers, body = json.loads(result.stdout)
            raw = base64.b64decode(body, validate=True)
            _require(type(status) is int and type(headers) is dict and len(raw) <= MAX_RESPONSE_BYTES,
                     'invalid bounded HTTP worker result')
            return Response(status, headers, raw)
        except (ValueError, TypeError) as error:
            raise ProviderError('invalid bounded HTTP worker result') from error

    def _get_direct(self, url):
        request = Request(url, headers={'Accept': 'application/json', 'Accept-Encoding': 'identity',
                          'Cache-Control': 'no-cache', 'User-Agent': 'SpaceFox/1 (personal cached feed)'})
        deadline = time.monotonic() + TOTAL_TIMEOUT_SECONDS
        try:
            try:
                response = self.opener.open(request, timeout=TIMEOUT_SECONDS)
            except HTTPError as error:
                response = error
            with response:
                headers = {k.lower(): v for k, v in response.headers.items()
                           if k.lower() in ('date', 'age', 'content-type', 'content-encoding', 'content-length', 'retry-after')}
                _require(all(len(response.headers.get_all(k, [])) <= 1 for k in headers), 'duplicate provider metadata header')
                _require(all(len(v) <= 1024 for v in headers.values()), 'provider header value exceeds bound')
                if response.status != 200:
                    return Response(response.status, headers, b'')
                _require(headers.get('content-encoding', 'identity').lower() == 'identity', 'compressed provider responses not accepted')
                length = headers.get('content-length')
                _require(length is None or length.isascii() and length.isdigit() and int(length) <= MAX_RESPONSE_BYTES,
                         'provider Content-Length exceeds bound')
                parts, total = [], 0
                while True:
                    remaining = deadline - time.monotonic()
                    _require(remaining > 0, 'provider total read deadline exceeded')
                    # Set each read deadline too; read1 returns available bytes so
                    # a slow body cannot multiply the per-read timeout indefinitely.
                    if response.fp is None:
                        break
                    response.fp.raw._sock.settimeout(min(TIMEOUT_SECONDS, remaining))
                    chunk = response.read1(min(8192, MAX_RESPONSE_BYTES + 1 - total))
                    if not chunk:
                        break
                    parts.append(chunk)
                    total += len(chunk)
                    _require(total <= MAX_RESPONSE_BYTES, 'provider streamed body exceeds bound')
                _require(time.monotonic() <= deadline, 'provider total deadline exceeded')
                return Response(200, headers, b''.join(parts))
        except (URLError, OSError, AttributeError) as error:
            raise ProviderError('provider HTTP failed or timed out') from error


def retry_deadline(headers, now):
    value = headers.get('retry-after', '')
    if re.fullmatch(r'[0-9]{1,9}', value):
        return max(now + 60, now + int(value))
    try:
        parsed = parsedate_to_datetime(value)
        _require(parsed.tzinfo is not None, 'Retry-After date lacks timezone')
        return max(now + 60, int(parsed.timestamp()))
    except (ValueError, TypeError, OverflowError, ProviderError):
        return now + 300


def validation_epoch(response, now):
    """Origin observation epoch, never build/receipt time or last_updated."""
    _require(response.status == 200, 'response has no per-record validation')
    headers = {k.lower(): v for k, v in response.headers.items()}
    _require(headers.get('content-type', '').split(';')[0].strip().lower() == 'application/json', 'provider Content-Type must be JSON')
    _require(headers.get('content-encoding', 'identity').lower() == 'identity', 'encoded provider body refused')
    try:
        parsed = parsedate_to_datetime(headers.get('date', ''))
        _require(parsed.tzinfo is not None, 'provider Date needs timezone')
        observed = int(parsed.timestamp())
        age = headers.get('age', '0')
        _require(type(age) is str and age.isascii() and age.isdigit() and len(age) <= 9, 'invalid provider Age')
        epoch = observed - int(age)
        _require(epoch <= now + 60, 'provider Date exceeds clock tolerance')
        # Future origin seconds cannot be silently promoted into local future age.
        _require(epoch <= now, 'provider validation is in the future')
        return epoch
    except (ValueError, TypeError, OverflowError) as error:
        if isinstance(error, ProviderError):
            raise
        raise ProviderError('provider lacks usable origin validation Date') from error


class LL2Client:
    def __init__(self, transport=None, *, origin=DEFAULT_ORIGIN, page_size=10, local_http=False):
        parsed = urlsplit(origin)
        _require(parsed.path in ('', '/') and not parsed.query and not parsed.fragment and parsed.username is None,
                 'provider origin must not contain path/query/credentials')
        if local_http:
            _require(parsed.scheme == 'http' and parsed.hostname == '127.0.0.1' and parsed.port is not None,
                     'local HTTP requires explicit IPv4 loopback and port')
        else:
            _require(parsed.scheme == 'https' and parsed.hostname in ('ll.thespacedevs.com', 'lldev.thespacedevs.com')
                     and parsed.port in (None, 443), 'only official LL2 HTTPS origins accepted')
        _require(type(page_size) is int and 1 <= page_size <= 20, 'page size must be1..20')
        self.origin = urlunsplit((parsed.scheme, parsed.netloc, '', '', ''))
        self.transport = transport or HTTPTransport()
        self.page_size = page_size
        self._requests_started = 0
        self.query = {'mode': 'normal', 'limit': str(page_size), 'ordering': 'net',
                      'include_suborbital': 'true', 'hide_recent_previous': 'false'}

    @property
    def requests_started(self):
        """Monotonic transport attempts after durable permission, including errors."""
        return self._requests_started

    @property
    def first_url(self):
        return self.origin + PATH + '?' + urlencode(self.query)

    def detail_url(self, identity):
        _require(identity.namespace == 'll2' and identity.kind is IdKind.LAUNCH, 'non LL2 launch detail identity')
        _require(str(uuid.UUID(identity.value)) == identity.value, 'noncanonical detail UUID')
        return self.origin + '/2.3.0/launches/' + identity.value + '/?mode=normal'

    def next_url(self, url, received):
        parsed, origin = urlsplit(url), urlsplit(self.origin)
        _require(parsed.scheme == origin.scheme and parsed.netloc == origin.netloc and parsed.path == PATH
                 and not parsed.fragment and parsed.username is None, 'unsafe pagination URL')
        query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)
        expected = {k: [v] for k, v in self.query.items()}
        expected['offset'] = [str(received)]
        _require(query == expected, 'pagination changed query or offset')
        return url

    def request(self, publisher, now, *, trigger='scheduled', url=None, clock=None):
        """Only public fetch entry: commit allowance before exactly one HTTP call."""
        if url is not None:
            parsed, origin = urlsplit(url), urlsplit(self.origin)
            _require(parsed.scheme == origin.scheme and parsed.netloc == origin.netloc and not parsed.fragment
                     and parsed.username is None, 'unsafe provider URL')
            if parsed.path != PATH:
                _require(bool(re.fullmatch(r'/2.3.0/launches/[0-9a-f-]{36}/', parsed.path))
                         and parsed.query == 'mode=normal', 'unsafe detail endpoint')
            else:
                query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)
                offset = query.get('offset')
                if offset is None:
                    _require(query == {k: [v] for k, v in self.query.items()}, 'unsafe upcoming query')
                else:
                    _require(len(offset) == 1 and offset[0].isascii() and offset[0].isdigit(), 'invalid offset')
                    self.next_url(url, int(offset[0]))
        token = publisher.reserve(publisher.head, now, trigger=trigger)
        if token is None:
            return None
        received_at = None
        try:
            # A rolling quota ledger can shrink when reserve prunes old slots.
            # Count the actual attempted transport call only after all permission
            # checks return; pre-HTTP quota/source rejection starts no request.
            self._requests_started += 1
            response = self.transport.get(url or self.first_url)
            received_at = now if clock is None else clock()
            if response.status == 429:
                raise Throttled(retry_deadline({k.lower(): v for k, v in response.headers.items()}, received_at))
            _require(response.status in (200, 304), f'provider HTTP status{response.status}')
            return token, response
        except Exception as error:
            # Response status and its backoff are one causal operation. Sampling
            # again could turn an exact60-second Retry-After into59seconds.
            failed_at = received_at if received_at is not None else now if clock is None else clock()
            publisher.finish_request(publisher.head, token, failed_at, 'throttled' if isinstance(error, Throttled) else 'failed',
                                     retry_after_utc=error.retry_at if isinstance(error, Throttled) else None)
            raise

    def page(self, response, now):
        epoch = validation_epoch(response, now)
        document = _object(bounded_json(response.body), 'page')
        _require({'count', 'next', 'previous', 'results'} <= document.keys(), 'incomplete LL2 page')
        _require(type(document['count']) is int and 0 <= document['count'] <= 1000000, 'invalid provider count')
        rows = document['results']
        _require(type(rows) is list and len(rows) <= self.page_size, 'page cardinality exceeds query')
        _require(document['next'] is None or type(document['next']) is str, 'invalid next URL')
        return document, tuple(normalize_launch(row, epoch) for row in rows)
