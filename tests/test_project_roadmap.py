import json
import tempfile
import unittest
from pathlib import Path

from tools.build_project_roadmap import build as build_roadmap
from tools.build_static import build as build_static


ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "data" / "core" / "project-roadmap.json"


class ProjectRoadmapTests(unittest.TestCase):
    def test_roadmap_matches_generated_reports(self):
        published = json.loads(ROADMAP.read_text(encoding="utf-8"))
        self.assertEqual(published, build_roadmap())
        summary = published["summary"]
        self.assertEqual(summary["electroia_reviewed_symbols"], 439)
        self.assertEqual(summary["electroia_pending_symbols"], 21)
        self.assertEqual(summary["electroia_complete_families"], 13)
        self.assertEqual([item["pending_symbols"] for item in published["remaining_electroia_families"]], [8, 8, 5])

    def test_public_page_renders_measurable_priorities(self):
        html = (ROOT / "actualizaciones.html").read_text(encoding="utf-8")
        script = (ROOT / "assets" / "updates.js").read_text(encoding="utf-8")
        self.assertIn("roadmapSummary", html)
        self.assertIn("data/core/project-roadmap.json", script)
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dist"
            build_static(ROOT, output)
            self.assertTrue((output / "data" / "core" / "project-roadmap.json").is_file())


if __name__ == "__main__":
    unittest.main()
