import json
import unittest
from pathlib import Path

from campaign_qa import review


ROOT = Path(__file__).parents[1]


class CampaignQATests(unittest.TestCase):
    def setUp(self):
        self.campaign = json.loads((ROOT / "demo/campaign.json").read_text(encoding="utf-8"))
        self.policy = json.loads((ROOT / "demo/policy.json").read_text(encoding="utf-8"))

    def test_demo_requires_revision(self):
        result = review(self.campaign, self.policy)
        self.assertEqual(result["status"], "revise")
        self.assertGreaterEqual(result["finding_count"], 3)

    def test_approved_copy_reaches_review(self):
        self.campaign["text"] = "Learn more about a reporting workflow designed for marketing teams. Terms apply"
        self.assertEqual(review(self.campaign, self.policy)["status"], "ready_for_human_review")

    def test_invalid_channel_is_rejected(self):
        self.campaign["channel"] = "billboard"
        with self.assertRaises(ValueError):
            review(self.campaign, self.policy)


if __name__ == "__main__":
    unittest.main()

