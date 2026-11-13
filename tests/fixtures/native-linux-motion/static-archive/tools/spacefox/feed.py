"""Lossless, bounded schedule serialization for the static-feed publisher.

This is the publisher byte-admission boundary, not provider/schema validation or
native RAM/storage qualification. The updater must validate schedule semantics
before calling it and publish the returned bytes unchanged. It adds no fields,
defaults, timestamps or filters, and performs no I/O or compression.
"""
import json
import math


MAX_DECODED_UTF8_BYTES = 8192


class FeedEncodingError(ValueError):
    """The supplied snapshot cannot be represented as a publishable JSON feed."""


class FeedTooLargeError(FeedEncodingError):
    """The complete decoded JSON exceeds the publisher's byte allowance."""

    def __init__(self, decoded_bytes: int):
        self.decoded_bytes = decoded_bytes
        self.limit = MAX_DECODED_UTF8_BYTES
        super().__init__(f'feed is {decoded_bytes} decoded UTF-8 bytes; limit is {self.limit}')


def _validate_json(value, active_containers: set[int]) -> None:
    """Reject Python coercions that would silently change the JSON value tree."""
    kind = type(value)
    if value is None or kind in (str, int, bool):
        return
    if kind is float:
        if not math.isfinite(value):
            raise FeedEncodingError('feed numbers must be finite')
        return
    if kind not in (dict, list):
        raise FeedEncodingError('feed values must be plain JSON types')
    identity = id(value)
    if identity in active_containers:
        raise FeedEncodingError('feed must not contain circular references')
    active_containers.add(identity)
    try:
        if kind is dict:
            for key, item in value.items():
                if type(key) is not str:
                    raise FeedEncodingError('feed object keys must be strings')
                _validate_json(item, active_containers)
        else:
            for item in value:
                _validate_json(item, active_containers)
    finally:
        active_containers.remove(identity)


def encode_feed(snapshot: dict) -> bytes:
    """Return the entire snapshot as deterministic JSON, at most 8192 UTF-8 bytes.

    Accept a plain dict containing only plain JSON types: dict with string keys,
    list, str, int, finite float, bool and None. Preserve list order, all fields,
    numeric values, nulls and Unicode text; sort object keys and omit whitespace.
    Unsupported types, cycles, nonfinite numbers, invalid Unicode and values the
    JSON encoder cannot represent raise FeedEncodingError. An oversize result
    raises FeedTooLargeError; compression never changes this allowance. Inputs
    are not mutated, and no candidate bytes are returned on failure.

    Consumers must still validate schema, identities, coordinates, time units,
    revisions and source freshness. This function does not establish those facts
    or the separate qualified native container/persistence budgets.
    """
    if type(snapshot) is not dict:
        raise FeedEncodingError('feed snapshot must be a plain JSON object')
    try:
        _validate_json(snapshot, set())
        encoded = json.dumps(snapshot, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':'), allow_nan=False).encode('utf-8')
    except FeedEncodingError:
        raise
    except (ValueError, TypeError, OverflowError, RecursionError) as error:
        raise FeedEncodingError('feed cannot be encoded as UTF-8 JSON') from error
    if len(encoded) > MAX_DECODED_UTF8_BYTES:
        raise FeedTooLargeError(len(encoded))
    return encoded
