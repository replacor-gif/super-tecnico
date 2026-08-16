import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "regulations" / "catalog.json"
INDEX_DIR = ROOT / "data" / "regulations" / "index"


class RegulationStructureTests(unittest.TestCase):
    def test_every_regulation_index_exposes_structured_records(self):
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        self.assertEqual(catalog["schema_version"], "1.2.0")
        self.assertGreaterEqual(len(catalog["documents"]), 18)
        for document in catalog["documents"]:
            payload = json.loads((INDEX_DIR / f"{document['id']}.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "1.2.0", document["id"])
            self.assertTrue(payload["records"], document["id"])
            for record in payload["records"]:
                self.assertIn(record.get("record_type"), {"body", "table", "heading", "index"}, record["id"])
                self.assertIn("breadcrumb", record, record["id"])
                self.assertIn("search_context", record, record["id"])
                self.assertIsInstance(record.get("locators"), list, record["id"])
                self.assertNotIn("BOLETÍN OFICIAL DEL ESTADO", record["text"], record["id"])
                self.assertNotRegex(record["text"], r"LEGISLACIÓN CONSOLIDADA\s+Página\s+\d+$", record["id"])

    def test_rebt_keeps_itc_section_and_table_hierarchy(self):
        payload = json.loads((INDEX_DIR / "rebt.json").read_text(encoding="utf-8"))
        voltage = next(record for record in payload["records"] if record["page"] == 128 and "2.2.2 Sección de los conductores" in record["text"])
        self.assertEqual(voltage["instruction_id"], "ITC-BT-19")
        self.assertEqual(voltage["section_id"], "2.2.2")
        self.assertIn("ITC-BT-19", voltage["breadcrumb"])

        lighting = next(record for record in payload["records"] if record["page"] == 169 and "C1 Iluminación" in record["text"])
        self.assertEqual(lighting["instruction_id"], "ITC-BT-25")
        self.assertEqual(lighting["record_type"], "table")
        self.assertIn("Tabla 1", lighting["breadcrumb"])

    def test_contents_are_labeled_and_cannot_masquerade_as_body_text(self):
        payload = json.loads((INDEX_DIR / "rebt.json").read_text(encoding="utf-8"))
        contents = [record for record in payload["records"] if record["page"] == 3]
        self.assertTrue(contents)
        self.assertTrue(all(record["record_type"] == "index" for record in contents))
        self.assertTrue(all(not record["instruction_id"] for record in contents))


if __name__ == "__main__":
    unittest.main()
