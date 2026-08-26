from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from build_editable_content_catalog import PRIVATE_PAGES, build, fnv1a  # noqa: E402


def js_fnv1a(value: str) -> str:
    """Reference for JavaScript's charCodeAt + Math.imul implementation."""
    current = 2166136261
    encoded = value.encode("utf-16-le")
    for index in range(0, len(encoded), 2):
        current ^= encoded[index] | (encoded[index + 1] << 8)
        current = (current * 16777619) & 0xFFFFFFFF
    return f"{current:08x}"


class ContentEditorV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(
            (ROOT / "data" / "content" / "editable-catalog.json").read_text(encoding="utf-8")
        )

    def test_catalog_is_current_complete_and_stable(self):
        self.assertEqual(self.catalog, build(ROOT))
        self.assertEqual(self.catalog["summary"]["pages"], 23)
        self.assertGreaterEqual(self.catalog["summary"]["editable_fields"], 1200)
        entries = self.catalog["entries"]
        keys = [entry["key"] for entry in entries]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertTrue(all(key.startswith("page.") for key in keys))
        self.assertFalse({entry["page"] for entry in entries} & PRIVATE_PAGES)
        self.assertTrue(all(entry["default"].strip() for entry in entries))

    def test_catalog_hash_matches_javascript_utf16(self):
        for value in ("text|Super Técnico", "placeholder|Buscar…", "text|Aviso ⚡ técnico"):
            self.assertEqual(fnv1a(value), js_fnv1a(value))

    def test_editor_loads_pages_lazily_and_public_runtime_applies_them(self):
        editor = (ROOT / "assets" / "content-editor.js").read_text(encoding="utf-8")
        runtime = (ROOT / "assets" / "page-counter.js").read_text(encoding="utf-8")
        html = (ROOT / "editor-contenidos.html").read_text(encoding="utf-8")
        build_script = (ROOT / "tools" / "build_static.py").read_text(encoding="utf-8")
        self.assertIn("data/content/editable-catalog.json", editor)
        self.assertIn("function populateGroup", editor)
        self.assertIn("details.contentKeys = keys", editor)
        self.assertNotIn("keys.forEach(key => fields.append(fieldCard(key)))", editor)
        self.assertIn("applyHardcodedContentOverrides", runtime)
        self.assertIn("window.ST_CONTENT_OVERRIDES_REQUEST", runtime)
        self.assertIn("content-editor-v2.css", html)
        self.assertIn("build_editable_content_catalog", build_script)


if __name__ == "__main__":
    unittest.main()
