import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTE = ROOT / "archivo-tecnico-47097e44267b9cb111636b84823f1d47"


class ElectroIAFieldValidationTests(unittest.TestCase):
    def test_private_field_validation_is_persistent_and_traceable(self):
        service = (ROOT / "api" / "electroia-validation.php").read_text(encoding="utf-8")
        router = (ROOT / "api" / "index.php").read_text(encoding="utf-8")
        schema = (ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
        self.assertIn("st_electroia_field_validations", service)
        self.assertIn("UNIQUE KEY uq_electroia_validation_case (case_key)", service)
        self.assertIn("electroia-validation-summary", router)
        self.assertIn("electroia-validation", router)
        self.assertIn("st_require_electroia_access();", router)
        self.assertIn("st_electroia_field_validations", schema)
        self.assertNotIn("DELETE FROM st_electroia_field_validations", service)

    def test_mobile_lab_records_fingerprint_outcome_and_domain(self):
        html = (ROUTE / "index.html").read_text(encoding="utf-8")
        app = (ROUTE / "app.js").read_text(encoding="utf-8")
        styles = (ROUTE / "styles.css").read_text(encoding="utf-8")
        for expected in (
            'id="fieldValidationForm"',
            'id="validationDomain"',
            'value="approved"',
            'value="needs_changes"',
            'id="downloadSvg"',
            'id="downloadJson"',
        ):
            self.assertIn(expected, html)
        self.assertIn('window.crypto.subtle.digest("SHA-256"', app)
        self.assertIn('privateApi("electroia-validation"', app)
        self.assertIn("detectedDevice()", app)
        self.assertIn("state.currentValidation.errors", app)
        self.assertIn("@media (max-width: 520px)", styles)
        self.assertIn(".field-validation-form { grid-template-columns: 1fr; }", styles)

    def test_engine_enforces_machine_readable_hard_limits(self):
        policy = json.loads((ROOT / "data" / "electroia" / "public-execution-policy.json").read_text(encoding="utf-8"))
        profiles = json.loads((ROOT / "data" / "electroia" / "document-profiles.json").read_text(encoding="utf-8"))
        schema = json.loads((ROOT / "data" / "electroia" / "diagram-document.schema.json").read_text(encoding="utf-8"))
        core = (ROUTE / "diagram-core.js").read_text(encoding="utf-8")
        self.assertFalse(policy["enabled"])
        self.assertTrue(policy["default_deny"])
        self.assertTrue(policy["emergency_stop_default"])
        self.assertEqual(policy["limits"]["components_per_document"], 200)
        self.assertEqual(policy["limits"]["nets_per_document"], 400)
        self.assertEqual(schema["properties"]["components"]["maxItems"], 200)
        self.assertEqual(schema["properties"]["nets"]["maxItems"], 400)
        self.assertEqual(len(profiles["document_profiles"]), 3)
        self.assertTrue(all(not item["verified"] for item in profiles["document_profiles"]))
        for diagnostic in ("DOCUMENT_TOO_LARGE", "COMPONENT_LIMIT", "NET_LIMIT", "CONNECTION_LIMIT", "TOTAL_CONNECTION_LIMIT"):
            self.assertIn(diagnostic, core)

    def test_pin_session_uses_the_same_key_when_written_and_read(self):
        backend = (ROOT / "api" / "electroia.php").read_text(encoding="utf-8")
        self.assertGreaterEqual(backend.count("$_SESSION['electroia_unlocked']"), 2)
        self.assertNotIn("$_SESSION['st_electroia_unlocked']", backend)


if __name__ == "__main__":
    unittest.main()
