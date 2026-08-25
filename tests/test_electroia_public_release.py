import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ElectroIAPublicReleaseTests(unittest.TestCase):
    def test_release_candidate_passes_every_automated_gate(self):
        report = json.loads(
            (ROOT / "data" / "electroia" / "public-release-readiness.json").read_text(encoding="utf-8")
        )
        self.assertEqual(report["release_stage"], "private_release_candidate")
        self.assertTrue(report["summary"]["automated_gates_pass"])
        self.assertTrue(report["summary"]["public_information_surface_ready"])
        self.assertTrue(report["summary"]["private_human_preview_ready"])
        self.assertFalse(report["summary"]["public_execution_ready"])
        self.assertTrue(report["summary"]["field_validation_recorder_ready"])
        self.assertEqual(report["summary"]["field_validation_target"], 20)
        self.assertTrue(report["summary"]["document_profiles_separated"])
        self.assertTrue(report["summary"]["public_execution_policy_ready"])
        self.assertEqual(report["summary"]["reviewed_symbols"], 501)
        self.assertEqual(report["summary"]["professional_examples"], 5)
        self.assertEqual(report["summary"]["component_overlaps"], 0)
        self.assertEqual(report["summary"]["wire_component_conflicts"], 0)
        self.assertEqual(report["summary"]["dangerous_warnings"], 0)
        for group in report["automated_gates"].values():
            self.assertTrue(all(item["passed"] for item in group))
        for example in report["examples"]:
            self.assertEqual(example["errors"], 0, example["file"])
            self.assertEqual(example["component_overlaps"], 0, example["file"])
            self.assertEqual(example["wire_component_conflicts"], 0, example["file"])
            self.assertEqual(example["dangerous_warnings"], [], example["file"])

    def test_public_surface_is_read_only_and_private_execution_stays_protected(self):
        backend = (ROOT / "api" / "electroia.php").read_text(encoding="utf-8")
        router = (ROOT / "api" / "index.php").read_text(encoding="utf-8")
        openapi = json.loads(
            (ROOT / "data" / "electroia" / "discovery.openapi.json").read_text(encoding="utf-8")
        )
        serialized = json.dumps(openapi)
        self.assertIn("st_electroia_public_status", backend)
        self.assertIn("st_electroia_public_symbol_search", backend)
        self.assertIn("electroia-public-status", router)
        self.assertIn("electroia-symbol-search", router)
        self.assertIn("st_require_electroia_access();", router)
        self.assertNotIn("electroia_render_diagram", serialized)
        self.assertNotIn("electroia_generate_relay_driver", serialized)
        self.assertNotIn("electroia_generate_temperature_fan", serialized)
        policy = json.loads((ROOT / "data" / "electroia" / "public-execution-policy.json").read_text(encoding="utf-8"))
        self.assertFalse(policy["enabled"])
        self.assertTrue(policy["authentication"]["required"])
        self.assertFalse(policy["safety"]["anonymous_execution_allowed"])

    def test_manual_release_blockers_are_explicit(self):
        report = json.loads(
            (ROOT / "data" / "electroia" / "public-release-readiness.json").read_text(encoding="utf-8")
        )
        blocker_ids = {item["id"] for item in report["manual_release_blockers"]}
        self.assertEqual(
            blocker_ids,
            {
                "FIELD_VALIDATION_REQUIRED",
                "IEC_PROFILE_REMAINS_EXPERIMENTAL",
                "PUBLIC_EXECUTION_GUARDRAILS_REQUIRED",
            },
        )


if __name__ == "__main__":
    unittest.main()
