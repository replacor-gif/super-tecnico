import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ElectroIAAIBridgeTests(unittest.TestCase):
    def test_private_lab_exposes_one_provider_neutral_input(self):
        html = (ROOT / "archivo-tecnico-47097e44267b9cb111636b84823f1d47" / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "archivo-tecnico-47097e44267b9cb111636b84823f1d47" / "app.js").read_text(encoding="utf-8")
        self.assertIn('data-workspace="bridge"', html)
        self.assertIn('id="aiDocumentInput"', html)
        self.assertIn('id="renderAiDocument"', html)
        self.assertIn("structuredContent?.document", script)
        self.assertIn("ElectroDiagramCore.validate(documentData)", script)
        self.assertIn("publicDesignFromDiagramDocument(documentData)", script)
        self.assertIn("new Blob([input]).size > 262144", script)

    def test_bridge_and_discovery_share_the_same_contract(self):
        bridge = json.loads((ROOT / "data" / "electroia" / "ai-bridge.json").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / "data" / "electroia" / "tool-manifest.json").read_text(encoding="utf-8"))
        discovery = json.loads((ROOT / "data" / "electroia" / "discovery.json").read_text(encoding="utf-8"))
        diagram_spec = json.loads((ROOT / "data" / "electroia" / "diagram-spec.schema.json").read_text(encoding="utf-8"))
        self.assertTrue(bridge["provider_neutral"])
        self.assertEqual(bridge["architecture"]["single_contract"], "diagram-document.schema.json")
        self.assertEqual(manifest["capabilities"]["ai_design_bridge"], "ai-bridge.json")
        self.assertEqual(manifest["capabilities"]["diagram_spec_schema"], "diagram-spec.schema.json")
        self.assertTrue(manifest["core_policy"]["compiles_ai_friendly_specifications"])
        self.assertIn("electroia_compile_diagram", {tool["name"] for tool in manifest["tools"]})
        self.assertEqual(discovery["contracts"]["ai_design_bridge"], "ai-bridge.json")
        self.assertEqual(discovery["contracts"]["diagram_spec_schema"], "diagram-spec.schema.json")
        self.assertIn("electroia_compile_diagram", discovery["recommended_ai_workflow"])
        self.assertEqual(diagram_spec["required"], ["title", "components", "nets"])
        self.assertEqual(diagram_spec["properties"]["components"]["maxItems"], 200)
        self.assertEqual(diagram_spec["properties"]["nets"]["maxItems"], 400)
        self.assertFalse(bridge["launch_boundary"]["public_anonymous_render"])

    def test_api_usage_attribution_is_explicit_and_visible(self):
        bootstrap = (ROOT / "api" / "bootstrap.php").read_text(encoding="utf-8")
        electroia = (ROOT / "api" / "electroia.php").read_text(encoding="utf-8")
        analytics = (ROOT / "assets" / "analytics.js").read_text(encoding="utf-8")
        dashboard = (ROOT / "analitica-privada.html").read_text(encoding="utf-8")
        self.assertIn("HTTP_X_ST_CLIENT_TYPE", bootstrap)
        self.assertIn("'electroia-public-status', 'electroia-symbol-search'", bootstrap)
        self.assertIn("st_electroia_usage_events", electroia)
        self.assertIn("declared_ai_calls", electroia)
        self.assertIn("renderElectroiaUsage(data)", analytics)
        self.assertIn('id="electroiaUsageMetrics"', dashboard)


if __name__ == "__main__":
    unittest.main()
