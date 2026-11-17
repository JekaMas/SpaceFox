"""Due schedule must outrank a content-only selection transition."""
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from tools.cloud_feed import _prepare_content
from tools.spacefox.schedule import DEFAULT_POLICY, ScheduleState


class PublisherPriorityTest(TestCase):
    def test_empty_future_due_reaches_request_before_content(self):
        previous = {'launch': {'launch_id': 'll2:launch:expired'}, 'upcoming': [],
                    'catalogSourceDigest': 'current', 'providerTraversal': None}
        store = SimpleNamespace(_blob=lambda *args: b'fixture')
        pub = SimpleNamespace(ledger={'pending': None, 'accepted': {'entries': [], 'evaluated_at_utc': None}, 'last_poll_utc': None, 'requests': [], 'active': {'generation': 7,
            'files': {'feed.json': 1, 'feed.json.txt': 1, 'watch.json': 1}}},
            store=store, head='head', schedule=ScheduleState(), policy=DEFAULT_POLICY,
            publisher_envelope=lambda now: {}, prepare=lambda *a, **k: SimpleNamespace())
        owner = SimpleNamespace(build=lambda *a, **k: ({}, 'digest'), review={},
                                source_digest=lambda: 'current')
        with patch('tools.cloud_feed.validate_feed', return_value=previous), \
             patch('tools.cloud_feed.update', return_value={'result': 'requested', 'requests': 1}) as request:
            result = _prepare_content(pub, object(), 1800000000, None, root='.', clock=None, owner=owner)
        self.assertEqual(result['result'], 'requested')
        self.assertEqual(request.call_count, 1)
