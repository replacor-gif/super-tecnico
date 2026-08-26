import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class ElectroIAPublicShowcaseTests(unittest.TestCase):
    def test_public_page_is_discoverable_and_read_only(self):
        page = (ROOT / "electroia.html").read_text(encoding="utf-8")
        script = (ROOT / "assets" / "electroia-public.js").read_text(encoding="utf-8")
        portal = (ROOT / "index.html").read_text(encoding="utf-8")
        shell = (ROOT / "assets" / "app-shell.js").read_text(encoding="utf-8")
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")

        self.assertNotIn("noindex", page)
        self.assertIn('id="eiaSymbolResults"', page)
        self.assertIn('id="eiaGallery"', page)
        self.assertIn("api/index.php?action=electroia-public-status", script)
        self.assertIn("api/index.php?action=electroia-symbol-search", script)
        self.assertNotIn("diagram-core.js", script)
        self.assertNotIn("electroia-render", script)
        self.assertNotIn("archivo-tecnico-47097e44267b9cb111636b84823f1d47", page)
        self.assertIn('href="electroia.html"', portal)
        self.assertIn("ElectroIA", shell)
        self.assertIn("/electroia.html", sitemap)

    def test_gallery_contains_only_reviewed_single_canvas_examples(self):
        gallery = load("data/electroia/public-gallery.json")
        self.assertEqual(gallery["count"], 5)
        self.assertEqual(len(gallery["items"]), 5)
        self.assertEqual(len({item["id"] for item in gallery["items"]}), 5)
        for item in gallery["items"]:
            self.assertTrue(item["single_canvas"], item["id"])
            self.assertEqual(item["pages"], 1, item["id"])
            self.assertTrue(all(value == 0 for value in item["validation"].values()), item["id"])
            image = ROOT / item["image"]
            source = ROOT / item["source"]
            self.assertTrue(image.is_file(), image)
            self.assertTrue(source.is_file(), source)
            svg = image.read_text(encoding="utf-8")
            self.assertIn('xmlns="http://www.w3.org/2000/svg"', svg)
            self.assertIn('data-pages="1"', svg)
            self.assertIn('class="electrical-diagram electroia-core-diagram"', svg)

    def test_release_and_discovery_publish_the_same_safe_surface(self):
        release = load("data/electroia/public-release-readiness.json")
        discovery = load("data/electroia/discovery.json")
        manifest = load("data/electroia/tool-manifest.json")
        roadmap = load("data/core/project-roadmap.json")
        service_worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")

        self.assertTrue(release["summary"]["public_showcase_ready"])
        self.assertFalse(release["summary"]["public_execution_ready"])
        self.assertEqual(discovery["public_showcase"], "../../electroia.html")
        self.assertEqual(discovery["contracts"]["public_gallery"], "public-gallery.json")
        self.assertEqual(manifest["discovery"]["public_showcase_path"], "electroia.html")
        self.assertTrue(roadmap["summary"]["electroia_public_showcase_ready"])
        self.assertFalse(roadmap["summary"]["electroia_public_execution_ready"])
        for expected in ("./electroia.html", "./assets/electroia-public.js", "./data/electroia/public-gallery.json"):
            self.assertIn(expected, service_worker)


if __name__ == "__main__":
    unittest.main()
