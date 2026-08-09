import json
import tempfile
import unittest
from pathlib import Path

from tools.build_static import build


ROOT = Path(__file__).resolve().parents[1]
ROUTE = "archivo-tecnico-47097e44267b9cb111636b84823f1d47"


class HiddenElectroIATests(unittest.TestCase):
    def test_page_is_not_linked_from_public_html(self):
        for path in ROOT.glob("*.html"):
            self.assertNotIn(ROUTE, path.read_text(encoding="utf-8"), path.name)

    def test_page_requests_no_indexing(self):
        html = (ROOT / ROUTE / "index.html").read_text(encoding="utf-8")
        self.assertIn("noindex,nofollow,noarchive,nosnippet,noimageindex", html)
        self.assertIn('<script src="engine.js"></script>', html)
        self.assertIn('<script src="diagram-symbol-library.js"></script>', html)
        self.assertIn('<script src="diagram-core.js"></script>', html)
        self.assertIn('<script src="diagram.js"></script>', html)

    def test_omega_access_is_added_below_the_page_counter(self):
        counter = (ROOT / "assets" / "page-counter.js").read_text(encoding="utf-8")
        styles = (ROOT / "assets" / "common.css").read_text(encoding="utf-8")
        self.assertIn(f"const ELECTROIA_PATH = '{ROUTE}/';", counter)
        self.assertIn("access.textContent = 'Ω'", counter)
        self.assertIn("tools.prepend(counter)", counter)
        self.assertIn(".st-electro-access", styles)

    def test_lab_uses_public_component_and_symbol_databases(self):
        app = (ROOT / ROUTE / "app.js").read_text(encoding="utf-8")
        engine = (ROOT / ROUTE / "engine.js").read_text(encoding="utf-8")
        self.assertIn('../data/components/catalog.json', app)
        self.assertIn('../data/symbols/catalog.json', app)
        self.assertIn('circuit_model', engine)
        self.assertIn('SYM-0080', engine)

    def test_result_shows_outcomes_without_internal_calculations(self):
        html = (ROOT / ROUTE / "index.html").read_text(encoding="utf-8")
        app = (ROOT / ROUTE / "app.js").read_text(encoding="utf-8")
        diagram = (ROOT / ROUTE / "diagram.js").read_text(encoding="utf-8")
        self.assertNotIn("Por qué funciona", html)
        self.assertNotIn("Bases utilizadas", html)
        self.assertNotIn("Modelo eléctrico interno", html)
        self.assertIn("renderPublicResult(data.design)", app)
        self.assertIn("ElectroDiagram.render(design)", app)
        public_renderer = app.split("function renderPublicResult", 1)[1].split("function escapeHtml", 1)[0]
        self.assertNotIn("item.calculation", public_renderer)
        self.assertNotIn("design.decisions", public_renderer)
        self.assertNotIn("function renderDesign", app)
        self.assertNotIn("decisions", engine := (ROOT / ROUTE / "engine.js").read_text(encoding="utf-8"))
        self.assertIn("design.circuit_model", diagram)
        self.assertIn('data-symbol-id="SYM-0119"', diagram)

    def test_isolation_has_two_real_separate_domains(self):
        engine = (ROOT / ROUTE / "engine.js").read_text(encoding="utf-8")
        diagram = (ROOT / ROUTE / "diagram.js").read_text(encoding="utf-8")
        self.assertIn('resources.componentsByPart.get("PC817")', engine)
        self.assertIn('{ id: "GND_CONTROL"', engine)
        self.assertIn('{ id: "GND_RELAY"', engine)
        self.assertIn('pins: { A: "CTRL_LED", K: "GND_CONTROL", C: "VRELAY_PLUS", E: "ISO_OUT" }', engine)
        self.assertIn('ref: "R3"', engine)
        self.assertNotIn('status: "incomplete"', engine)
        self.assertIn("function renderIsolatedRelayDriver", diagram)
        self.assertIn("NO UNIR LAS DOS MASAS", diagram)

    def test_model_is_ready_for_future_photo_or_sketch_input(self):
        engine = (ROOT / ROUTE / "engine.js").read_text(encoding="utf-8")
        diagram = (ROOT / ROUTE / "diagram.js").read_text(encoding="utf-8")
        self.assertIn('future: ["image", "hand_drawn_sketch"]', engine)
        self.assertIn('{ ref: "LOAD1"', engine)
        self.assertIn('schema_version: "0.4"', engine)
        self.assertNotIn("requestText", diagram)

    def test_private_pin_is_verified_only_on_the_server(self):
        html = (ROOT / ROUTE / "index.html").read_text(encoding="utf-8")
        app = (ROOT / ROUTE / "app.js").read_text(encoding="utf-8")
        backend = (ROOT / "api" / "electroia.php").read_text(encoding="utf-8")
        api = (ROOT / "api" / "index.php").read_text(encoding="utf-8")
        runtime = (ROOT / ".deploy-now" / "api" / "config.runtime.php.template").read_text(encoding="utf-8")
        self.assertIn('id="pinGate"', html)
        self.assertIn("electroia-access", app)
        self.assertIn("electroia-unlock", api)
        self.assertIn("password_verify", backend)
        self.assertIn("ST_ELECTROIA_PIN_HASH", runtime)
        for content in (html, app, backend, api, runtime):
            self.assertNotIn("4097", content)

    def test_provider_neutral_tool_has_no_embedded_ai_or_billing(self):
        app = (ROOT / ROUTE / "app.js").read_text(encoding="utf-8")
        engine = (ROOT / ROUTE / "engine.js").read_text(encoding="utf-8")
        backend = (ROOT / "api" / "electroia.php").read_text(encoding="utf-8")
        api = (ROOT / "api" / "index.php").read_text(encoding="utf-8")
        manifest = (ROOT / "data" / "electroia" / "tool-manifest.json").read_text(encoding="utf-8")
        server = (ROOT / "electroia-tool-server" / "src" / "index.mjs").read_text(encoding="utf-8")
        self.assertIn('new URL("../api/index.php", document.baseURI)', app)
        self.assertIn('ElectroEngine.callTool("electroia_analyze_request"', app)
        self.assertIn('ElectroEngine.callTool("electroia_generate_relay_driver"', app)
        self.assertIn('ElectroEngine.callTool("electroia_generate_temperature_fan"', app)
        self.assertIn("function callTool", engine)
        self.assertIn("electroia-status", api)
        self.assertIn("electroia-tools", api)
        self.assertIn("provider_neutral", backend)
        self.assertIn("st_electroia_access_cookie_is_valid", backend)
        self.assertIn("hash_hmac('sha256'", backend)
        self.assertIn('"provider_neutral": true', manifest)
        self.assertIn('"embedded_ai_model": false', manifest)
        self.assertIn('"billing_required_by_electroia": false', manifest)
        self.assertIn('"electroia_generate_relay_driver"', manifest)
        self.assertIn('"electroia_generate_temperature_fan"', manifest)
        self.assertIn('"electroia_get_diagram_contract"', manifest)
        self.assertIn('"electroia_render_diagram"', manifest)
        self.assertIn('"diagram_engine_version": "1.3.0-alpha.1"', manifest)
        self.assertIn('"normalized_symbol_count": 460', manifest)
        self.assertIn('"calculates_values"', manifest)
        self.assertIn('server.registerTool(', server)
        self.assertIn('serveStdio(createServer)', server)
        for content in (app, backend, api, manifest, server):
            self.assertNotIn("api.openai.com", content)
            self.assertNotIn("OPENAI_API_KEY", content)
        self.assertNotRegex(app, r"sk-[A-Za-z0-9_-]{12,}")

    def test_static_build_includes_the_hidden_lab(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dist"
            build(ROOT, output)
            for filename in ("index.html", "styles.css", "engine.js", "diagram-symbol-library.js", "diagram-core.js", "diagram.js", "app.js"):
                self.assertTrue((output / ROUTE / filename).is_file(), filename)
            self.assertTrue((output / "data" / "symbols" / "catalog.json").is_file())
            self.assertTrue((output / "data" / "electroia" / "tool-manifest.json").is_file())
            self.assertTrue((output / "data" / "electroia" / "diagram-document.schema.json").is_file())
            self.assertTrue((output / "data" / "electroia" / "symbol-library.json").is_file())
            self.assertTrue((output / "data" / "electroia" / "symbol-normalization-report.json").is_file())
            self.assertTrue((output / "data" / "electroia" / "examples" / "motor-starter-direct.json").is_file())
            self.assertTrue((output / "data" / "electroia" / "examples" / "distribution-board-single-line.json").is_file())
            self.assertTrue(
                (output / "assets" / "symbols" / "SYM-0080_mosfet-n-con-diodo-de-cuerpo.svg").is_file()
            )

    def test_complete_symbol_library_is_normalized_and_quality_labeled(self):
        library = json.loads((ROOT / "data" / "electroia" / "symbol-library.json").read_text(encoding="utf-8"))
        report = json.loads((ROOT / "data" / "electroia" / "symbol-normalization-report.json").read_text(encoding="utf-8"))
        catalog_symbols = [item for item in library["symbols"] if item["catalog_id"]]
        self.assertEqual(len(catalog_symbols), 460)
        self.assertEqual(library["engine_symbol_count"], 463)
        self.assertTrue(all(item["ports"] for item in library["symbols"]))
        self.assertEqual(report["catalog_status_counts"], {"auto_draft": 413, "engine_reviewed": 47})
        self.assertEqual(report["coverage_percent"], 100)


if __name__ == "__main__":
    unittest.main()
