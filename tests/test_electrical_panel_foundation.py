import json
import unittest
from pathlib import Path

from tools.validate_panel_project import validate_project


ROOT = Path(__file__).resolve().parents[1]
PANEL_DATA = ROOT / "data" / "electrical-panels"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class ElectricalPanelFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_json(PANEL_DATA / "tool-manifest.json")
        cls.standards = load_json(PANEL_DATA / "standards-registry.json")
        cls.schema = load_json(PANEL_DATA / "panel-project.schema.json")
        cls.controllers = load_json(ROOT / "data" / "electroia" / "controller-ecosystems.json")
        cls.example = load_json(PANEL_DATA / "examples" / "motor-pump-dol-auto-manual.json")

    def test_tool_is_one_coordinated_project_graph(self):
        self.assertEqual(self.manifest["schema_version"], "0.1.0")
        self.assertEqual(self.manifest["project_schema"], "panel-project.schema.json")
        self.assertIn("single_line_diagram", self.manifest["minimum_outputs"])
        self.assertIn("terminal_plan", self.manifest["minimum_outputs"])
        self.assertIn("panel_layout_2d", self.manifest["minimum_outputs"])
        self.assertIn("automation_source_and_backup_manifest", self.manifest["minimum_outputs"])
        self.assertTrue(self.manifest["provider_neutral"])
        self.assertFalse(self.manifest["embedded_ai_model"])

    def test_normative_profiles_reference_known_primary_sources(self):
        reference_ids = {item["id"] for item in self.standards["references"]}
        profiles = {item["id"]: item for item in self.standards["profiles"]}
        self.assertEqual(set(profiles), {"ES_DBO", "ES_PSC", "ES_MACHINE", "ES_HVAC_AUTOMATION", "ES_EMBEDDED_IOT"})
        for profile in profiles.values():
            self.assertTrue(profile["primary_references"])
            self.assertTrue(set(profile["primary_references"]).issubset(reference_ids))
            self.assertTrue(set(profile["conditional_references"]).issubset(reference_ids))
        self.assertIn("ES_REBT", profiles["ES_DBO"]["primary_references"])
        self.assertIn("IEC_61439_2", profiles["ES_PSC"]["primary_references"])
        self.assertIn("IEC_60204_1", profiles["ES_MACHINE"]["primary_references"])
        self.assertFalse(self.standards["licensing"]["automatic_compliance_claim"])

    def test_controller_registry_covers_plc_arduino_and_raspberry_pi(self):
        ecosystems = {item["id"]: item for item in self.controllers["ecosystems"]}
        expected = {
            "generic_iec_industrial_plc",
            "safety_plc",
            "codesys_target",
            "arduino_generic_5v",
            "arduino_generic_3v3",
            "arduino_opta",
            "arduino_portenta_machine_control",
            "raspberry_pi_compute_or_sbc",
            "custom_embedded_controller",
        }
        self.assertTrue(expected.issubset(ecosystems))
        for ecosystem_id in ("arduino_generic_5v", "arduino_generic_3v3", "arduino_opta", "arduino_portenta_machine_control", "raspberry_pi_compute_or_sbc"):
            self.assertNotIn("safety_control", ecosystems[ecosystem_id]["allowed_safety_roles"])
        self.assertIn("safety_control", ecosystems["safety_plc"]["allowed_safety_roles"])
        self.assertFalse(self.controllers["core_safety_policy"]["generic_arduino_or_raspberry_pi_may_execute_safety_functions"])

    def test_project_contract_links_loads_io_evidence_and_lifecycle(self):
        required = set(self.schema["required"])
        self.assertTrue({"loads", "control_system", "safety", "evidence", "lifecycle"}.issubset(required))
        controller_properties = self.schema["$defs"]["controller"]["properties"]
        io_properties = self.schema["$defs"]["io_point"]["properties"]
        self.assertIn("ecosystem_id", controller_properties)
        self.assertIn("firmware", controller_properties)
        self.assertIn("safety_role", controller_properties)
        self.assertIn("terminal_id", io_properties)
        self.assertIn("fail_state", io_properties)
        self.assertIn("safety_related", io_properties)

    def test_reference_project_uses_non_safety_plc_and_exposes_blocking_checks(self):
        self.assertEqual(self.example["project_kind"], "machine_electrical_equipment")
        controller = self.example["control_system"]["controllers"][0]
        self.assertEqual(controller["ecosystem_id"], "generic_iec_industrial_plc")
        self.assertEqual(controller["safety_role"], "non_safety_control")
        self.assertTrue(self.example["safety"]["safety_functions"])
        self.assertTrue(any(check["blocks_manufacture"] for check in self.example["lifecycle"]["open_checks"]))
        self.assertEqual(self.example["lifecycle"]["state"], "draft")

    def test_reference_project_passes_semantic_relationship_checks(self):
        report = validate_project(self.example, self.controllers)
        self.assertTrue(report["valid"], report["issues"])
        self.assertEqual(report["summary"]["errors"], 0)
        self.assertGreater(report["summary"]["blocking_checks"], 0)

    def test_generic_arduino_is_rejected_as_safety_controller(self):
        project = json.loads(json.dumps(self.example))
        controller = project["control_system"]["controllers"][0]
        controller["ecosystem_id"] = "arduino_generic_5v"
        controller["safety_role"] = "safety_control"
        report = validate_project(project, self.controllers)
        self.assertFalse(report["valid"])
        self.assertIn("UNSUPPORTED_SAFETY_ROLE", {issue["code"] for issue in report["issues"]})

    def test_schema_is_valid_when_jsonschema_is_available(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest("jsonschema is not installed")
        Draft202012Validator.check_schema(self.schema)
        Draft202012Validator(self.schema).validate(self.example)


if __name__ == "__main__":
    unittest.main()
