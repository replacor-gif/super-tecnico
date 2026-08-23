import json
import unittest
from pathlib import Path

from tools.audit_app_quality import build_report


ROOT = Path(__file__).resolve().parents[1]


class AppQualityAuditTests(unittest.TestCase):
    def test_current_application_passes_all_quality_gates(self):
        report, errors = build_report()
        self.assertEqual(errors, [])
        self.assertEqual(report["status"], "pass")
        self.assertTrue(all(report["quality_gates"].values()))
        self.assertGreaterEqual(report["summary"]["root_pages"], 25)
        self.assertGreaterEqual(report["summary"]["local_references_checked"], 350)

    def test_published_report_matches_the_current_application(self):
        expected, _ = build_report()
        published = json.loads((ROOT / "data" / "core" / "app-quality-audit.json").read_text(encoding="utf-8"))
        self.assertEqual(published, expected)


if __name__ == "__main__":
    unittest.main()
