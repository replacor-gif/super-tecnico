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

    def test_private_ai_backend_has_a_safe_local_fallback(self):
        app = (ROOT / ROUTE / "app.js").read_text(encoding="utf-8")
        backend = (ROOT / "api" / "electroia.php").read_text(encoding="utf-8")
        api = (ROOT / "api" / "index.php").read_text(encoding="utf-8")
        self.assertIn('new URL("../api/index.php", document.baseURI)', app)
        self.assertIn('ElectroEngine.analyze(body.request)', app)
        self.assertIn("electroia-status", api)
        self.assertIn("electroia-analyze", api)
        self.assertIn("https://api.openai.com/v1/responses", backend)
        self.assertIn("'type' => 'json_schema'", backend)
        self.assertIn("'strict' => true", backend)
        self.assertIn("'store' => false", backend)
        self.assertNotRegex(app, r"sk-[A-Za-z0-9_-]{12,}")

    def test_static_build_includes_the_hidden_lab(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dist"
            build(ROOT, output)
            for filename in ("index.html", "styles.css", "engine.js", "app.js"):
                self.assertTrue((output / ROUTE / filename).is_file(), filename)
            self.assertTrue((output / "data" / "symbols" / "catalog.json").is_file())
            self.assertTrue(
                (output / "assets" / "symbols" / "SYM-0080_mosfet-n-con-diodo-de-cuerpo.svg").is_file()
            )


if __name__ == "__main__":
    unittest.main()
