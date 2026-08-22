import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONNECTORS = ROOT / "data" / "connectors"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ConnectorCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load(CONNECTORS / "catalog.json")
        cls.sources = load(CONNECTORS / "sources.json")
        cls.manifest = load(CONNECTORS / "tool-manifest.json")

    def test_catalog_counts_and_identifiers_are_consistent(self):
        records = self.catalog["records"]
        contacts = sum(len(record["contacts"]) for record in records)
        statuses = {status: sum(record["review"]["status"] == status for record in records) for status in ("reviewed", "source_identified", "pending_review")}
        self.assertEqual(len(records), 17)
        self.assertEqual(contacts, 185)
        self.assertEqual(len({record["id"] for record in records}), len(records))
        self.assertEqual(self.catalog["counts"], {"records": 17, "reviewed": statuses["reviewed"], "source_identified": statuses["source_identified"], "pending_review": statuses["pending_review"], "contacts": 185})

    def test_every_record_preserves_view_review_and_sources(self):
        source_ids = {source["id"] for source in self.sources["sources"]}
        for record in self.catalog["records"]:
            with self.subTest(record=record["id"]):
                self.assertIn(record["view"]["perspective"], {"mating_face", "wiring_side", "device_front", "logical_only"})
                self.assertGreater(len(record["view"]["orientation_note"]), 20)
                self.assertIn(record["review"]["status"], {"reviewed", "source_identified", "pending_review"})
                self.assertTrue(set(record["source_ids"]).issubset(source_ids))
                contact_ids = [contact["id"] for contact in record["contacts"]]
                self.assertEqual(len(contact_ids), len(set(contact_ids)))
                self.assertTrue(all(contact["signal"] and contact["description"] for contact in record["contacts"]))

    def test_machine_contract_requires_identification_before_pinout(self):
        tools = {tool["name"]: tool for tool in self.manifest["tools"]}
        self.assertIn("supertecnico_search_connectors", tools)
        self.assertIn("supertecnico_get_connector", tools)
        self.assertIn("supertecnico_resolve_connector_contact", tools)
        self.assertTrue(self.manifest["remote_execution"])
        self.assertEqual(tools["supertecnico_search_connectors"]["state"], "public_http_beta")
        get_schema = tools["supertecnico_get_connector"]["input_schema"]
        self.assertEqual(get_schema["required"], ["connector_id"])
        self.assertIn("view", self.manifest["instructions"])
        self.assertIn("review.status", self.manifest["instructions"])

    def test_browser_and_both_manuals_are_present(self):
        html = (ROOT / "conectores.html").read_text(encoding="utf-8")
        js = (ROOT / "assets" / "connectors.js").read_text(encoding="utf-8")
        self.assertIn("data/connectors/catalog.json", js)
        self.assertIn("view.orientation_note", js)
        self.assertIn("catalogo-normalizado-conectores-replacor-edicion-9.pdf", html)
        self.assertTrue((ROOT / "recursos" / "catalogo-normalizado-conectores-replacor-edicion-9.pdf").is_file())
        self.assertTrue((ROOT / "recursos" / "enciclopedia-conectores-pinouts-edicion-8-origen.pdf").is_file())

    def test_private_review_and_import_workflow_is_server_side(self):
        moderation = (ROOT / "moderacion.html").read_text(encoding="utf-8")
        app = (ROOT / "assets" / "moderation.js").read_text(encoding="utf-8")
        backend = (ROOT / "api" / "connectors.php").read_text(encoding="utf-8")
        router = (ROOT / "api" / "index.php").read_text(encoding="utf-8")
        schema = (ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
        self.assertIn("SINAPSYS · control humano", moderation)
        self.assertIn("admin-connector-review", app)
        self.assertIn("admin-connector-import", app)
        self.assertIn("review_evidence_incomplete", backend)
        self.assertIn("connector-search", router)
        self.assertIn("st_connector_reviews", schema)
        self.assertIn("st_connector_import_batches", schema)
        self.assertTrue((ROOT / "data" / "connectors" / "discovery.openapi.json").is_file())


if __name__ == "__main__":
    unittest.main()
