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

    def test_static_build_includes_the_hidden_lab(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dist"
            build(ROOT, output)
            for filename in ("index.html", "styles.css", "engine.js", "app.js"):
                self.assertTrue((output / ROUTE / filename).is_file(), filename)


if __name__ == "__main__":
    unittest.main()
