from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COSTING = ROOT / "data" / "internal-costing"


def load(name: str):
    return json.loads((COSTING / name).read_text(encoding="utf-8"))


class CostingFoundationTests(unittest.TestCase):
    def test_private_cross_domain_contract_is_complete(self):
        project = load("estimate-project.schema.json")
        rate = load("unit-rate.schema.json")
        policy = load("source-policy.json")
        disciplines = set(project["properties"]["discipline"]["enum"])
        self.assertTrue({"water", "electricity", "hvac", "refrigeration", "multidiscipline"}.issubset(disciplines))
        self.assertEqual(rate["properties"]["publication_policy"]["enum"], ["private_only", "aggregate_only", "public_allowed"])
        self.assertFalse(policy["public_price_data"])
        self.assertIn("base_date", policy["required_dimensions"])
        self.assertIn("geography", policy["required_dimensions"])
        self.assertIn("confidence", policy["required_dimensions"])

    def test_example_is_measurement_only_and_contains_no_money(self):
        example = load("example-measurement-only.json")
        self.assertEqual(example["pricing_status"], "private_rates_required")
        self.assertIsNone(example["estimate_summary"])
        self.assertTrue(example["measurements"])
        for item in example["measurements"]:
            self.assertEqual(item["pricing_status"], "unpriced")
            self.assertIsNone(item["unit_rate_id"])
            self.assertNotIn("unit_price", item)
            self.assertNotIn("amount", item)


if __name__ == "__main__":
    unittest.main()
