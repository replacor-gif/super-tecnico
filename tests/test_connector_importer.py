from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "connector_importer", ROOT / "tools" / "import_connector_documents.py"
)
assert SPEC and SPEC.loader
IMPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPORTER)


class ConnectorImporterTests(unittest.TestCase):
    def test_csv_becomes_review_staging_without_touching_catalog(self) -> None:
        catalog_path = ROOT / "data" / "connectors" / "catalog.json"
        before = catalog_path.read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "contacts.csv"
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["connector_id", "contact", "signal"])
                writer.writeheader()
                writer.writerow({"connector_id": "test-01", "contact": "1", "signal": "GND"})
            staging = IMPORTER.build_staging(source)

        self.assertEqual(staging["import_status"], "extracted")
        self.assertEqual(staging["extraction"]["rows"], 1)
        self.assertEqual(staging["candidates"][0]["contacts"][0]["signal"], "GND")
        self.assertEqual(catalog_path.read_bytes(), before)

    def test_json_and_image_are_truthfully_classified(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            json_path = base / "connector.json"
            json_path.write_text(json.dumps({"records": [{"id": "demo", "contacts": []}]}), encoding="utf-8")
            image_path = base / "photo.png"
            image_path.write_bytes(b"not-a-real-image")

            parsed = IMPORTER.build_staging(json_path)
            pending = IMPORTER.build_staging(image_path)

        self.assertEqual(parsed["import_status"], "extracted")
        self.assertEqual(parsed["extraction"]["source_records"], 1)
        self.assertEqual(pending["import_status"], "needs_extractor")
        self.assertIn("imagen", pending["warning"].lower())


if __name__ == "__main__":
    unittest.main()
