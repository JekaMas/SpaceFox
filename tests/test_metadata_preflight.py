"""Independent metadata preflight control using captured records and local Git."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from tests import test_current_metadata_publisher as fixture
from tools.spacefox import catalog_refresh as refresh_module
from tools.spacefox.catalog_refresh import CatalogRefresh, RefreshError
from tools.spacefox.publisher import Publisher

NOW = fixture.NOW


class MetadataPreflightTest(unittest.TestCase):
    def test_preflight_refusal_preserves_prefix_and_permission(self):
        expected, files = fixture.captured()
        helper = fixture.CurrentMetadataPublisherTest()
        with helper.authority() as (pub, store, code):
            helper.primary(pub, NOW, accept=True)
            preserved = deepcopy(helper.preserved(pub))
            transport = fixture.CapturedTransport(pub, expected, files)
            transport.epoch = NOW
            collector = CatalogRefresh(pub, transport=transport)
            head = pub.head
            requests = deepcopy(pub.ledger["requests"])
            with patch.object(refresh_module, "MAX_CATALOG_OBJECTS", 0):
                with self.assertRaisesRegex(RefreshError, "catalog corpus exceeds"):
                    collector.run(NOW)
            self.assertEqual(head, store.load()[0])
            self.assertEqual(requests, pub.ledger["requests"])
            self.assertEqual([], transport.calls)
            self.assertEqual({}, collector.objects)
            self.assertEqual("partial", collector.run(NOW).status)
            prefix = deepcopy(collector.journal["staging"]["pages"])
            with patch.object(refresh_module, "MAX_CATALOG_OBJECTS", 2):
                with self.assertRaisesRegex(RefreshError, "catalog corpus exceeds"):
                    collector.run(NOW + 1)
            self.assertEqual({}, collector.objects)
            durable = CatalogRefresh(Publisher(store, code))
            self.assertEqual(prefix, durable.journal["staging"]["pages"])
            self.assertEqual(prefix, collector.journal["staging"]["pages"])
            self.assertEqual("success", pub.ledger["requests"][-1]["outcome"])
            self.assertEqual("partial", collector.run(NOW + 2).status)
            self.assertEqual(transport.calls[1]["url"], transport.calls[2]["url"])
            self.assertEqual(prefix, collector.journal["staging"]["pages"][:1])
            self.assertEqual(preserved, helper.preserved(pub))

