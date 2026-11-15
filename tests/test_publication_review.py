"""Release review declaration boundaries; no signing or Store access."""
import unittest

from tools import release
from tools.build_watchface import BuildBlocked


class PublicationReviewTest(unittest.TestCase):
    def record(self):
        return {"publisher": "adult_owner_own_account", "account_age_condition": "confirmed",
                "audience_review": "pending", "audience_review_reference": "",
                "store_status": "not_submitted", "claimed_exemption": "none"}

    def test_adult_owner_publishes_the_app_positive(self):
        result = release.review_publication(self.record())
        self.assertFalse(result["implementation_blocked_by_unknown_viewer_age"])
        self.assertFalse(result["store_approved"])
        self.assertFalse(result["publication_ready"])

    def test_adult_owner_publishes_the_app_negative(self):
        for status in ("approved", "beta", "tagged"):
            with self.subTest(status=status), self.assertRaisesRegex(BuildBlocked, "approval"):
                release.review_publication(dict(self.record(), store_status=status))
        with self.assertRaisesRegex(BuildBlocked, "private/unknown"):
            release.review_publication(dict(self.record(), viewer_age=12))

    def test_audience_review_identifies_an_applicable_restriction_positive(self):
        result = release.review_publication(dict(self.record(), audience_review="resolved",
                                                audience_review_reference="review-record"))
        self.assertEqual(result["audience_review"], "resolved")
        self.assertFalse(result["store_approved"])

    def test_audience_review_identifies_an_applicable_restriction_negative(self):
        for exemption in ("adult_publisher", "private_sideload"):
            with self.subTest(exemption=exemption), self.assertRaisesRegex(BuildBlocked, "not an audience exemption"):
                release.review_publication(dict(self.record(), claimed_exemption=exemption))
        with self.assertRaisesRegex(BuildBlocked, "needs a reference"):
            release.review_publication(dict(self.record(), audience_review="resolved"))


