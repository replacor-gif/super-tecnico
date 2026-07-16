from __future__ import annotations

import json
import re
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from build_static import build  # noqa: E402
from audit_brand_quality import audit_brand  # noqa: E402


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalized(value: str) -> str:
    value = "".join(
        char for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    ).upper()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9]+", " ", value)).strip()


def contains_query(entries: list[dict], query: str) -> bool:
    tokens = normalized(query).split()
    return any(all(token in str(item.get("haystack", "")) for token in tokens) for item in entries)


class StaticSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.dist = Path(cls.temp.name) / "dist"
        cls.report = build(ROOT, cls.dist)
        cls.brand = cls.dist / "data" / "brands" / "fujitsu-general"
        cls.web = cls.brand / "web"
        cls.daikin = cls.dist / "data" / "brands" / "daikin"
        cls.daikin_web = cls.daikin / "web"

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_expected_counts(self):
        manifest = load(self.dist / "data" / "brands" / "index.json")
        brands = {item["slug"]: item for item in manifest["brands"]}
        self.assertEqual(set(brands), {"daikin", "fujitsu-general"})
        self.assertEqual(brands["fujitsu-general"]["counts"], {
            "categories": 18,
            "topics": 29,
            "variants": 46,
            "errors": 110,
            "search_entries": 156,
        })
        self.assertEqual(brands["daikin"]["counts"], {
            "categories": 7,
            "topics": 8,
            "variants": 14,
            "errors": 2,
            "search_entries": 16,
        })

    def test_search_examples_are_present(self):
        entries = load(self.web / "search.json")
        for query in ("pump down", "boya", "Peak Cut", "mando 2 hilos"):
            with self.subTest(query=query):
                self.assertTrue(contains_query(entries, query))

        errors = load(self.web / "errors" / "index.json")
        token = normalized("E12")
        self.assertTrue(any(token in item.get("search_text", "") for item in errors))

        daikin_entries = load(self.daikin_web / "search.json")
        for query in ("A3", "AF", "pump down", "flotador", "BRC1E", "VRV IV"):
            with self.subTest(brand="daikin", query=query):
                self.assertTrue(contains_query(daikin_entries, query))

        daikin_errors = load(self.daikin_web / "errors" / "index.json")
        self.assertEqual({item["code_display"] for item in daikin_errors}, {"A3", "AF"})

    def test_media_is_not_published_or_referenced(self):
        self.assertFalse((self.brand / "media").exists())
        self.assertFalse((self.daikin / "media").exists())
        self.assertEqual(self.report["checks"]["media_files"], 0)
        self.assertGreaterEqual(self.report["checks"]["media_references_removed"], 26)

        for path in list(self.web.rglob("*.json")) + list(self.daikin_web.rglob("*.json")):
            data = load(path)
            pending = [data]
            while pending:
                node = pending.pop()
                if isinstance(node, dict):
                    if "media" in node:
                        self.assertEqual(node["media"], [], path)
                    pending.extend(node.values())
                elif isinstance(node, list):
                    pending.extend(node)

    def test_forbidden_server_files_are_absent(self):
        forbidden_suffixes = {".db", ".sqlite", ".sqlite3", ".php", ".py", ".md"}
        for path in self.dist.rglob("*"):
            if path.is_file():
                self.assertNotIn(path.suffix.lower(), forbidden_suffixes, path)
                self.assertNotEqual(path.name.lower(), ".htaccess")

    def test_browser_uses_static_data_provider(self):
        html = (self.dist / "index.html").read_text(encoding="utf-8")
        script = (self.dist / "assets" / "app.js").read_text(encoding="utf-8")
        self.assertIn("assets/app.js", html)
        self.assertIn("data/brands/index.json", script)
        self.assertNotIn("api.php", html + script)
        self.assertNotIn("media.php", html + script)

    def test_error_finder_explains_current_coverage(self):
        script = (self.dist / "assets" / "app.js").read_text(encoding="utf-8")
        self.assertIn("Ver códigos disponibles", script)
        self.assertIn("todavía no está incluido en la base", script)
        self.assertIn("no puede mostrar una ficha que aún no se ha cargado", script)
        self.assertIn("limit:500", script)

    def test_daikin_projection_keeps_private_master_data_out(self):
        public_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in self.daikin.rglob("*.json")
        )
        self.assertNotIn("drive_id", public_text)
        self.assertNotIn("drive_title", public_text)
        self.assertNotIn("modelos_ocultos", public_text)
        self.assertNotIn("1uuiYPbdPX75iZNp2zBLjCQ8M8E3sxodh", public_text)
        self.assertFalse(any(self.daikin.rglob("*.sqlite")))
        self.assertFalse(any(self.daikin.rglob("*.db")))

        topics = [load(path) for path in (self.daikin_web / "topics").glob("*.json")]
        variants = [variant for topic in topics for variant in topic["variants"]]
        self.assertEqual(len(variants), 14)
        self.assertTrue(all(
            any(section["title"] == "Estado de verificación" for section in variant["sections"])
            for variant in variants
        ))

    def test_all_json_is_utf8_and_valid(self):
        paths = list(self.dist.rglob("*.json"))
        self.assertGreaterEqual(len(paths), 165)
        for path in paths:
            load(path)

    def test_fujitsu_quality_audit_is_current(self):
        brand = ROOT / "data" / "brands" / "fujitsu-general"
        expected = audit_brand(brand)
        actual = load(brand / "web" / "quality.json")
        self.assertEqual(actual, expected)
        self.assertEqual(actual["errors"]["entries"], 110)
        self.assertLessEqual(actual["errors"]["interpretations"], 121)
        self.assertGreater(actual["errors"]["status_counts"].get("reference_only", 0), 0)
        self.assertEqual(actual["technical_variants"]["entries"], 46)

    def test_fujitsu_confirmation_only_duplicates_are_consolidated(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"
        expected = {
            3: 2, 5: 1, 9: 1, 11: 1, 12: 1, 13: 1, 14: 2,
            16: 1, 17: 1, 18: 2, 19: 1, 20: 1, 21: 1, 22: 1,
            23: 1, 25: 1, 26: 1, 28: 1, 29: 1, 30: 1, 31: 1, 32: 1,
        }
        for error_id, interpretation_count in expected.items():
            with self.subTest(error_id=error_id):
                detail = load(web / "errors" / "details" / f"{error_id}.json")
                self.assertEqual(len(detail["interpretations"]), interpretation_count)
                index = load(web / "errors" / "index.json")
                row = next(item for item in index if item["id"] == error_id)
                self.assertEqual(row["interpretation_count"], interpretation_count)

    def test_fujitsu_vrii_service_diagnostics_are_developed(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"
        quality = load(web / "quality.json")
        self.assertGreaterEqual(quality["errors"]["status_counts"].get("complete", 0), 55)
        self.assertLessEqual(quality["errors"]["status_counts"].get("reference_only", 0), 54)

        for error_id in range(69, 111):
            with self.subTest(error_id=error_id):
                detail = load(web / "errors" / "details" / f"{error_id}.json")
                interpretation = detail["interpretations"][0]
                item_types = {item["item_type"] for item in interpretation["info_items"]}
                self.assertIn("cause", item_types)
                self.assertIn("check", item_types)
                self.assertIn("machine_behavior", item_types)
                self.assertTrue(any(
                    source.get("document_ref") == "AIRSTAGE_VRII_SERVICE"
                    for source in interpretation["sources"]
                ))

        discharge_pressure = load(web / "errors" / "details" / "90.json")["interpretations"][0]
        curve = discharge_pressure["datasets"][0]
        self.assertEqual(curve["points"][0]["value_nominal"], 0.50)
        self.assertEqual(curve["points"][-1]["value_nominal"], 4.50)

        eev = load(web / "errors" / "details" / "99.json")["interpretations"][0]
        winding = eev["datasets"][0]["points"][0]
        self.assertEqual((winding["value_min"], winding["value_nominal"], winding["value_max"]), (42.0, 46.0, 50.0))

        fan = load(web / "errors" / "details" / "96.json")["interpretations"][0]
        self.assertEqual(fan["operational_impacts"][0]["stop_level"], "permanent_stop")

        search = load(web / "search.json")
        self.assertTrue(contains_query(search, "CN118 5 V"))
        self.assertTrue(contains_query(search, "EEV1 46 ohm"))

    def test_fujitsu_vrii_communications_and_addressing_are_developed(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"
        quality = load(web / "quality.json")
        self.assertGreaterEqual(quality["errors"]["status_counts"].get("complete", 0), 66)
        self.assertLessEqual(quality["errors"]["status_counts"].get("reference_only", 0), 24)

        for error_id in (40, 54, 55, 58, 59, 61, 62, 63, 64, 65, 66):
            with self.subTest(error_id=error_id):
                detail = load(web / "errors" / "details" / f"{error_id}.json")
                interpretation = detail["interpretations"][0]
                item_types = {item["item_type"] for item in interpretation["info_items"]}
                self.assertIn("cause", item_types)
                self.assertIn("check", item_types)
                self.assertIn("machine_behavior", item_types)
                self.assertTrue(any(
                    source.get("document_ref") == "AIRSTAGE_VRII_SERVICE"
                    for source in interpretation["sources"]
                ))

        remote = load(web / "errors" / "details" / "54.json")["interpretations"][0]
        self.assertEqual(remote["datasets"][0]["points"][0]["value_nominal"], 12.0)

        missing_indoor = load(web / "errors" / "details" / "64.json")["interpretations"][0]
        self.assertEqual(missing_indoor["operational_impacts"][0]["stop_level"], "all_system")
        self.assertIn("no se detiene", missing_indoor["operational_impacts"][0]["degraded_behavior"])

        search = load(web / "search.json")
        self.assertTrue(contains_query(search, "SET4 1 180 segundos"))
        self.assertTrue(contains_query(search, "CNC01 12 V"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
