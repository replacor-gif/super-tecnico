import json
import unittest
from pathlib import Path

from tools.audit_electroia_engine import build_report


ROOT = Path(__file__).resolve().parents[1]


class ElectroIAAuditTests(unittest.TestCase):
    def test_published_audit_matches_the_current_engine(self):
        published = json.loads(
            (ROOT / "data" / "electroia" / "engine-audit-report.json").read_text(encoding="utf-8")
        )
        current, failures = build_report()
        self.assertEqual(failures, [])
        self.assertEqual(published, current)
        self.assertEqual(published["status"], "pass")
        self.assertEqual(published["summary"]["public_symbols"], 501)
        self.assertEqual(published["summary"]["professional_symbols"], 41)
        self.assertEqual(published["summary"]["fatal_failures"], 0)

    def test_professional_domains_and_structural_gates_are_complete(self):
        report, _ = build_report()
        self.assertTrue(all(report["structural_gates"].values()))
        for coverage in report["professional_domain_coverage"].values():
            self.assertEqual(coverage["available"], coverage["required"])
            self.assertEqual(coverage["missing"], [])
        limitation_ids = {item["id"] for item in report["known_limitations"]}
        self.assertEqual(
            limitation_ids,
            {"FUNCTIONAL_GROUPS_REQUIRE_MODEL", "IEC_PROFILE_EXPERIMENTAL", "SINGLE_CANVAS_ONLY"},
        )


if __name__ == "__main__":
    unittest.main()
