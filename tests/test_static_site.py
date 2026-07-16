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
            "topics": 38,
            "variants": 68,
            "errors": 117,
            "search_entries": 185,
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
        self.assertIn("renderRelatedErrors", script)

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
        self.assertEqual(actual["errors"]["entries"], 117)
        self.assertEqual(actual["errors"]["interpretations"], 129)
        self.assertEqual(actual["errors"]["status_counts"].get("reference_only", 0), 0)
        self.assertEqual(actual["technical_variants"]["entries"], 68)

    def test_fujitsu_confirmation_only_duplicates_are_consolidated(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"
        expected = {
            3: 2, 5: 1, 7: 1, 9: 1, 11: 1, 12: 1, 13: 1, 14: 2, 15: 1,
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

    def test_fujitsu_multisplit_check_run_is_complete(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"
        quality = load(web / "quality.json")
        self.assertGreaterEqual(quality["errors"]["status_counts"].get("complete", 0), 67)
        self.assertLessEqual(quality["errors"]["status_counts"].get("reference_only", 0), 23)

        e15 = load(web / "errors" / "details" / "4.json")
        interpretation = next(item for item in e15["interpretations"] if item["id"] == 42)
        item_types = {item["item_type"] for item in interpretation["info_items"]}
        self.assertIn("cause", item_types)
        self.assertIn("check", item_types)
        self.assertIn("machine_behavior", item_types)
        self.assertTrue(any(
            source.get("document_ref") == "9374995530-05"
            for source in interpretation["sources"]
        ))

        topic = load(web / "topics" / "30.json")
        variant = topic["variants"][0]
        self.assertEqual(variant["id"], 47)
        self.assertGreaterEqual(len(variant["steps"]), 8)
        self.assertTrue(any("10 minutos" in step.get("instruction", "") for step in variant["steps"]))

        search = load(web / "search.json")
        self.assertTrue(contains_query(search, "CHECK RUN LED A F"))
        self.assertTrue(contains_query(search, "correccion automatica cableado"))

    def test_fujitsu_legacy_simultaneous_addressing_is_complete(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"
        quality = load(web / "quality.json")
        self.assertGreaterEqual(quality["errors"]["status_counts"].get("complete", 0), 70)
        self.assertLessEqual(quality["errors"]["status_counts"].get("reference_only", 0), 20)

        for error_id, interpretation_id in ((37, 43), (38, 45), (39, 46)):
            with self.subTest(error_id=error_id):
                detail = load(web / "errors" / "details" / f"{error_id}.json")
                interpretation = next(item for item in detail["interpretations"] if item["id"] == interpretation_id)
                item_types = {item["item_type"] for item in interpretation["info_items"]}
                self.assertIn("cause", item_types)
                self.assertIn("check", item_types)
                self.assertIn("machine_behavior", item_types)
                self.assertTrue(interpretation["datasets"])
                self.assertTrue(any(
                    source.get("document_ref") == "9374318445-06"
                    for source in interpretation["sources"]
                ))

        topic = load(web / "topics" / "31.json")
        variant = topic["variants"][0]
        self.assertEqual(variant["id"], 48)
        self.assertEqual({parameter["parameter_code"] for parameter in variant["parameters"]}, {"DIP R.C.", "02", "51", "DIP SW1-2"})
        rc = next(parameter for parameter in variant["parameters"] if parameter["parameter_code"] == "DIP R.C.")
        self.assertEqual(len(rc["options"]), 16)

        search = load(web / "search.json")
        self.assertTrue(contains_query(search, "funcion 02 circuito frigorifico"))
        self.assertTrue(contains_query(search, "funcion 51 principal secundaria"))

    def test_fujitsu_grouping_codes_route_to_complete_subcodes(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"
        quality = load(web / "quality.json")
        self.assertEqual(quality["errors"]["grouping_references"], 9)
        self.assertEqual(quality["errors"]["technical_interpretations"], 120)
        self.assertEqual(quality["errors"]["status_counts"].get("grouping_reference"), 9)
        self.assertLessEqual(quality["errors"]["status_counts"].get("reference_only", 0), 6)
        for component in quality["errors"]["component_coverage"].values():
            self.assertLessEqual(component["percent"], 100.0)

        expected = {
            44: {84},
            47: {87, 88},
            49: {99, 100, 101},
            50: {105, 106},
        }
        for error_id, target_ids in expected.items():
            with self.subTest(error_id=error_id):
                detail = load(web / "errors" / "details" / f"{error_id}.json")
                interpretation = detail["interpretations"][0]
                self.assertEqual(interpretation["entry_role"], "grouping_reference")
                self.assertEqual({item["id"] for item in interpretation["related_errors"]}, target_ids)
                self.assertTrue(interpretation["routing_note"])
                for target_id in target_ids:
                    self.assertTrue((web / "errors" / "details" / f"{target_id}.json").exists())

        search = load(web / "search.json")
        self.assertTrue(contains_query(search, "E75 E75 1 sonda aspiracion"))
        self.assertTrue(contains_query(search, "E9A E9A 3 bobina expansion"))

    def test_fujitsu_indoor_damper_power_and_valve_diagnostics(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"

        for error_id in (111, 112, 113):
            with self.subTest(error_id=error_id):
                interpretation = load(web / "errors" / "details" / f"{error_id}.json")["interpretations"][0]
                kinds = {item["item_type"] for item in interpretation["info_items"]}
                self.assertIn("cause", kinds)
                self.assertIn("check", kinds)
                self.assertTrue(any(source.get("document_ref") == "AOHG18_24KBTA3_SERVICE" for source in interpretation["sources"]))

        e57 = load(web / "errors" / "details" / "41.json")
        self.assertEqual(len(e57["interpretations"]), 2)
        self.assertTrue(all(
            {"cause", "check"}.issubset({item["item_type"] for item in interpretation["info_items"]})
            for interpretation in e57["interpretations"]
        ))

        e76 = load(web / "errors" / "details" / "45.json")
        self.assertEqual(len(e76["interpretations"]), 2)
        for interpretation in e76["interpretations"]:
            self.assertEqual(len(interpretation["datasets"]), 2)
            resistance = interpretation["datasets"][0]
            voltage = interpretation["datasets"][1]
            self.assertEqual(next(point["value_nominal"] for point in resistance["points"] if point["variable_value"] == 25), 10.0)
            self.assertEqual(next(point["value_nominal"] for point in voltage["points"] if point["variable_value"] == 25), 3.97)
            self.assertTrue(any("5,0 V" in item["body"] for item in interpretation["info_items"]))

        e612 = load(web / "errors" / "details" / "68.json")["interpretations"][0]
        values = [point["value_nominal"] for point in e612["datasets"][0]["points"]]
        self.assertEqual(values, [342, 400, 456])

        topic = load(web / "topics" / "32.json")
        self.assertEqual({variant["id"] for variant in topic["variants"]}, {49, 50})
        self.assertTrue(all(not variant["media"] for variant in topic["variants"]))

        search = load(web / "search.json")
        for query in ("E26 direccion duplicada", "CN18 compuerta", "E76 sonda valvula 5 V", "E61 2 342 V"):
            with self.subTest(query=query):
                self.assertTrue(contains_query(search, query))

    def test_fujitsu_indoor_safety_and_symptom_diagnostics(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"

        e45 = load(web / "errors" / "details" / "114.json")
        self.assertEqual(len(e45["interpretations"]), 2)
        self.assertEqual(
            {item["operational_impacts"][0]["stop_level"] for item in e45["interpretations"]},
            {"all_system", "degraded"},
        )
        self.assertTrue(all(
            any(source.get("document_ref") == "AOHG18_24KBTA3_SERVICE" for source in item["sources"])
            for item in e45["interpretations"]
        ))

        e58 = load(web / "errors" / "details" / "115.json")["interpretations"][0]
        self.assertTrue(any("CN11" in item["body"] for item in e58["info_items"]))
        self.assertTrue({"cause", "check"}.issubset({item["item_type"] for item in e58["info_items"]}))

        ea8 = load(web / "errors" / "details" / "116.json")["interpretations"][0]
        self.assertEqual(ea8["operational_impacts"][0]["stop_level"], "all_system")
        self.assertIn("ventilación", ea8["operational_impacts"][0]["degraded_behavior"])
        self.assertIn("no puede detenerse", ea8["description"])

        symptom = load(web / "topics" / "33.json")
        self.assertEqual({item["id"] for item in symptom["variants"]}, set(range(51, 57)))
        no_operation = next(item for item in symptom["variants"] if item["id"] == 53)
        self.assertTrue(any("CN14" in section["body"] and "CNC01" in section["body"] for section in no_operation["sections"]))
        self.assertTrue(any("13 V" in (step.get("expected_result") or "") for step in no_operation["steps"]))

        components = load(web / "topics" / "34.json")
        self.assertEqual({item["id"] for item in components["variants"]}, {57, 58})
        self.assertTrue(all(not item["media"] for item in components["variants"]))

        search = load(web / "search.json")
        for query in (
            "E45 sensor deteriorado",
            "EA8 ventilacion seguridad",
            "E58 CN11 microinterruptor",
            "198 264 V sin alimentacion",
            "no enfria strainer",
            "fuga agua desague",
        ):
            with self.subTest(query=query):
                self.assertTrue(contains_query(search, query))

    def test_fujitsu_eeprom_subcooler_and_second_fan_are_developed(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"

        for error_id, page in ((7, "03-25"), (15, "03-40")):
            with self.subTest(error_id=error_id):
                detail = load(web / "errors" / "details" / f"{error_id}.json")
                self.assertEqual(len(detail["interpretations"]), 1)
                interpretation = detail["interpretations"][0]
                kinds = {item["item_type"] for item in interpretation["info_items"]}
                self.assertTrue({"cause", "check"}.issubset(kinds))
                self.assertTrue(any(
                    source.get("document_ref") == "AOHG18_24KBTA3_SERVICE" and source.get("page_start") == page
                    for source in interpretation["sources"]
                ))

        e62 = load(web / "errors" / "details" / "15.json")["interpretations"][0]
        self.assertEqual({item["id"] for item in e62["related_errors"]}, {70, 71, 72})

        e82 = load(web / "errors" / "details" / "46.json")["interpretations"][0]
        self.assertEqual(e82["entry_role"], "grouping_reference")
        self.assertEqual({item["id"] for item in e82["related_errors"]}, {86, 117})

        e821 = load(web / "errors" / "details" / "117.json")["interpretations"][0]
        self.assertTrue(any("CN142" in item["body"] and "5–6" in item["body"] for item in e821["info_items"]))
        curve = e821["datasets"][0]
        self.assertEqual(next(point["value_nominal"] for point in curve["points"] if point["variable_value"] == 25), 4.8)
        self.assertTrue(any(source.get("document_ref") == "AIRSTAGE_JII_SERVICE" for source in e821["sources"]))

        e98 = load(web / "errors" / "details" / "48.json")["interpretations"][0]
        self.assertEqual(e98["operational_impacts"][0]["stop_level"], "permanent_stop")
        power, control = e98["datasets"][0]["points"]
        self.assertEqual((power["value_min"], power["value_max"]), (280.0, 373.0))
        self.assertEqual((control["value_min"], control["value_nominal"], control["value_max"]), (13.5, 15.0, 16.5))

        topic = load(web / "topics" / "35.json")
        self.assertEqual({item["id"] for item in topic["variants"]}, {59, 60})
        self.assertTrue(all(not item["media"] for item in topic["variants"]))

        search = load(web / "search.json")
        for query in (
            "E32 EEPROM corrosion",
            "E62 6 comunicacion inverter",
            "E82 1 CN142 5 6",
            "E98 CN802 280 373",
            "segundo ventilador parada permanente",
        ):
            with self.subTest(query=query):
                self.assertTrue(contains_query(search, query))

    def test_fujitsu_two_wire_controller_internal_errors_are_developed(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"

        for error_id in (53, 56, 57, 60):
            with self.subTest(error_id=error_id):
                interpretation = load(web / "errors" / "details" / f"{error_id}.json")["interpretations"][0]
                kinds = {item["item_type"] for item in interpretation["info_items"]}
                self.assertTrue({"cause", "check"}.issubset(kinds))
                self.assertTrue(any(
                    source.get("document_ref") == "UTY_RCRYZ1_IM_9373328483"
                    for source in interpretation["sources"]
                ))
                self.assertTrue(any("12 V" in item["body"] or "F1" in item["body"] for item in interpretation["info_items"]))

        data_error = load(web / "errors" / "details" / "57.json")["interpretations"][0]
        self.assertIn("unidad interior", data_error["description"])
        master_error = load(web / "errors" / "details" / "60.json")["interpretations"][0]
        self.assertTrue(any("exactamente un mando" in item["body"] for item in master_error["info_items"]))

        topic = load(web / "topics" / "36.json")
        self.assertEqual({item["id"] for item in topic["variants"]}, {61, 62, 63, 64})
        self.assertTrue(all(item["steps"] and item["sections"] for item in topic["variants"]))
        self.assertTrue(all(not item["media"] for item in topic["variants"]))

        quality = load(web / "quality.json")
        self.assertLessEqual(quality["errors"]["status_counts"].get("reference_only", 0), 2)

        search = load(web / "search.json")
        for query in (
            "C2 1 PCB transmision this product",
            "12 4 arranque Monitor Mode",
            "15 4 adquisicion datos direccion",
            "27 1 maestro esclavo F1 06",
        ):
            with self.subTest(query=query):
                self.assertTrue(contains_query(search, query))

    def test_fujitsu_display_io_and_branch_box_errors_are_complete(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"

        e6a = load(web / "errors" / "details" / "43.json")
        self.assertIn("E6A.1", {item["alias_display"] for item in e6a["aliases"]})
        e6a_interpretation = e6a["interpretations"][0]
        self.assertTrue({"cause", "check", "machine_behavior"}.issubset(
            {item["item_type"] for item in e6a_interpretation["info_items"]}
        ))
        self.assertEqual(e6a_interpretation["datasets"][0]["points"][0]["value_nominal"], 10)
        self.assertTrue(any(
            source.get("document_ref") == "AOU48RLXFZ1_HYBRID_FLEX_SERVICE"
            and source.get("page_start") == "02-64"
            for source in e6a_interpretation["sources"]
        ))

        ed2 = load(web / "errors" / "details" / "51.json")
        self.assertTrue({"J2", "E.J2.U"}.issubset({item["alias_display"] for item in ed2["aliases"]}))
        ed2_interpretation = ed2["interpretations"][0]
        led_map = ed2_interpretation["datasets"][0]["points"]
        self.assertEqual(len(led_map), 10)
        self.assertTrue(any(point["variable_value"] == "LED402: 8 + LED403/404/405" and "EEV" in point["value_text"] for point in led_map))
        self.assertTrue(any("no afirma" in item["body"] for item in ed2_interpretation["info_items"]))

        e6a_topic = load(web / "topics" / "37.json")
        branch_topic = load(web / "topics" / "38.json")
        self.assertEqual({item["id"] for item in e6a_topic["variants"]}, {65})
        self.assertEqual({item["id"] for item in branch_topic["variants"]}, {66, 67, 68})
        self.assertTrue(all(not item["media"] for item in e6a_topic["variants"] + branch_topic["variants"]))

        quality = load(web / "quality.json")
        self.assertEqual(quality["errors"]["status_counts"].get("reference_only", 0), 0)
        self.assertEqual(quality["errors"]["status_counts"].get("complete"), 80)

        search = load(web / "search.json")
        for query in (
            "E6A 1 PCB I O 10 segundos",
            "J2 LED401 LED402 caja primaria",
            "LED402 8 EEV puerto A B C",
            "ED2 cantidad cajas CHECK RUN",
        ):
            with self.subTest(query=query):
                self.assertTrue(contains_query(search, query))


if __name__ == "__main__":
    unittest.main(verbosity=2)
