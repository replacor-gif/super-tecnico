import json
import tempfile
import unittest
from pathlib import Path

from tools.build_static import build


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "embedded-platforms"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class EmbeddedPlatformCatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load(DATA / "catalog.json")

    def test_catalog_is_complete_traceable_and_conservative(self):
        records = self.catalog["records"]
        self.assertEqual(self.catalog["count"], 41)
        self.assertEqual(len(records), 41)
        self.assertEqual(len({item["id"] for item in records}), 41)
        self.assertEqual([item["source_locator"]["pdf_page"] for item in records], list(range(69, 110)))
        self.assertTrue(all(item["review"]["status"] == "source_identified" for item in records))
        self.assertTrue(all(item["review"]["requires_exact_revision_check"] for item in records))
        self.assertTrue(all(item["architecture"] and item["logic_and_power"] and item["interfaces"] and item["primary_risk"] for item in records))

    def test_known_platforms_preserve_critical_distinctions(self):
        by_id = {item["id"]: item for item in self.catalog["records"]}
        self.assertIn("Matter", by_id["emb-esp32-c6-devkitc-1"]["recommended_use"])
        self.assertIn("sin Wi-Fi", by_id["emb-esp32-h2-devkitm"]["interfaces"][-1])
        self.assertEqual(by_id["emb-portenta-machine-control"]["platform_class"], "industrial_controller")
        self.assertEqual(by_id["emb-raspberry-pi-compute-module-5"]["platform_class"], "system_on_module")

    def test_machine_contract_and_public_http_are_explicit(self):
        manifest = load(DATA / "tool-manifest.json")
        discovery = load(DATA / "discovery.json")
        tools = {item["name"]: item for item in manifest["tools"]}
        self.assertEqual(discovery["status"], "public_browser_and_http_beta")
        self.assertEqual(set(tools), {"supertecnico_search_embedded_platforms", "supertecnico_get_embedded_platform", "supertecnico_recommend_embedded_platforms"})
        self.assertTrue(all(item["state"] == "public_http_beta" for item in tools.values()))
        self.assertTrue(all(item["annotations"]["readOnlyHint"] for item in tools.values()))
        backend = (ROOT / "api" / "embedded-platforms.php").read_text(encoding="utf-8")
        routes = (ROOT / "api" / "index.php").read_text(encoding="utf-8")
        self.assertIn("st_embedded_recommend", backend)
        self.assertIn("st_embedded_terms", backend)
        self.assertIn("in_array('linux', $queryTerms, true)", backend)
        self.assertIn("embedded-recommend", routes)
        self.assertNotIn("api.openai.com", backend)

    def test_browser_and_static_build_include_the_module(self):
        html = (ROOT / "plataformas-embebidas.html").read_text(encoding="utf-8")
        js = (ROOT / "assets" / "embedded-platforms.js").read_text(encoding="utf-8")
        self.assertIn("data/embedded-platforms/catalog.json", js)
        self.assertIn("ficha básica", html)
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dist"
            build(ROOT, output)
            for relative in ("plataformas-embebidas.html", "assets/embedded-platforms.css", "assets/embedded-platforms.js", "data/embedded-platforms/catalog.json", "data/embedded-platforms/tool-manifest.json", "data/embedded-platforms/discovery.json"):
                self.assertTrue((output / relative).is_file(), relative)


if __name__ == "__main__":
    unittest.main()
