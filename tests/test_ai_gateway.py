import json
import tempfile
import unittest
from pathlib import Path

from tools.audit_ai_readiness import audit
from tools.build_static import build


ROOT = Path(__file__).resolve().parents[1]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class AIGatewayFoundationTests(unittest.TestCase):
    def test_public_page_explains_private_preview_without_false_availability(self):
        html = (ROOT / "ia-integracion.html").read_text(encoding="utf-8")
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Vista previa privada", html)
        self.assertIn("conexión remota todavía desactivada", html)
        self.assertIn("data/ai/discovery.json", html)
        self.assertIn("data/ai/readiness-report.json", html)
        self.assertIn('href="ia-integracion.html"', home)
        self.assertNotIn("4097", html)
        self.assertNotRegex(html, r"sk-[A-Za-z0-9_-]{12,}")

    def test_discovery_separates_knowledge_and_diagram_services(self):
        discovery = load(ROOT / "data" / "ai" / "discovery.json")
        services = {item["id"]: item for item in discovery["service_families"]}
        self.assertEqual(discovery["status"], "design_ready_private_preview")
        self.assertFalse(discovery["security"]["remote_execution_enabled"])
        self.assertEqual(discovery["access_model"]["humans"]["site_access"], "free")
        self.assertEqual(discovery["access_model"]["machines"]["coverage_preflight"], "planned_free")
        self.assertEqual(discovery["access_model"]["machines"]["bulk_dataset_export"], "not_offered")
        self.assertIn("super-tecnico-knowledge", services)
        self.assertIn("electroia-diagram-engine", services)

    def test_tool_contract_uses_free_preflight_and_compact_paid_levels(self):
        manifest = load(ROOT / "data" / "ai" / "tool-manifest.json")
        tools = {item["name"]: item for item in manifest["tools"]}
        self.assertFalse(manifest["execution_enabled"])
        self.assertTrue(manifest["routing_policy"]["preflight_first"])
        self.assertFalse(manifest["routing_policy"]["bulk_export_allowed"])
        self.assertIn("status", manifest["default_output_schema"]["required"])
        self.assertIn("usage", manifest["default_output_schema"]["properties"])
        self.assertEqual(tools["supertecnico_check_coverage"]["billing_tier"], "free")
        self.assertLessEqual(tools["supertecnico_check_coverage"]["target_output_tokens"], 250)
        self.assertEqual(tools["supertecnico_get_diagnostic"]["billing_tier"], "metered_diagnostic")
        self.assertIn("delegate", tools["supertecnico_render_diagram"])
        self.assertTrue(all(item["annotations"]["readOnlyHint"] for item in tools.values()))

    def test_openapi_is_explicitly_non_executable_and_protects_database(self):
        contract = load(ROOT / "data" / "ai" / "knowledge-api-contract.openapi.json")
        discovery = load(ROOT / "data" / "ai" / "discovery.json")
        self.assertEqual(contract["openapi"], "3.1.0")
        self.assertFalse(contract["x-execution-enabled"])
        self.assertTrue(contract["x-do-not-call-until-enabled"])
        self.assertIn("ApiKeyAuth", contract["components"]["securitySchemes"])
        self.assertFalse(discovery["security"]["database_direct_access"])
        self.assertNotIn("4097", json.dumps(contract))

    def test_future_metering_schema_stores_hashes_not_raw_secrets(self):
        sql = (ROOT / "database" / "ai_gateway.schema.sql").read_text(encoding="utf-8")
        self.assertIn("st_ai_clients", sql)
        self.assertIn("st_ai_credentials", sql)
        self.assertIn("secret_hash", sql)
        self.assertIn("st_ai_usage_events", sql)
        self.assertIn("billable_units", sql)
        self.assertIn("st_ai_security_events", sql)
        self.assertIn("st_ai_benchmark_runs", sql)
        self.assertNotIn("4097", sql)
        self.assertNotRegex(sql, r"sk-[A-Za-z0-9_-]{12,}")

    def test_knowledge_schema_requires_evidence_confidence_and_version(self):
        schema = load(ROOT / "data" / "ai" / "knowledge-record.schema.json")
        required = set(schema["required"])
        self.assertTrue({"record_id", "record_version", "evidence", "confidence", "updated_at"}.issubset(required))
        evidence_kinds = schema["properties"]["evidence"]["items"]["properties"]["kind"]["enum"]
        self.assertIn("OFFICIAL_FABRICANTE", evidence_kinds)
        self.assertIn("CASO_CONFIRMADO", evidence_kinds)
        self.assertIn("PENDIENTE_VALIDACION", evidence_kinds)

    def test_readiness_audit_matches_current_content_inventory(self):
        current = audit(ROOT)
        published = load(ROOT / "data" / "ai" / "readiness-report.json")
        self.assertEqual(current["content_inventory"], published["content_inventory"])
        self.assertEqual(published["content_inventory"]["brands"], 30)
        self.assertEqual(published["content_inventory"]["components"], 38618)
        self.assertEqual(published["content_inventory"]["electroia_symbols"], 460)
        self.assertGreater(published["content_inventory"]["source_documents"], 200)
        self.assertIn("economic_benchmark", {item["id"] for item in published["checkpoints"]})

    def test_static_build_publishes_discovery_but_not_internal_docs_or_audit_script(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dist"
            build(ROOT, output)
            for path in (
                "ia-integracion.html",
                "robots.txt",
                "sitemap.xml",
                "data/ai/discovery.json",
                "data/ai/tool-manifest.json",
                "data/ai/knowledge-record.schema.json",
                "data/ai/knowledge-api-contract.openapi.json",
                "data/ai/readiness-report.json",
                "data/ai/benchmark-plan.json",
            ):
                self.assertTrue((output / path).is_file(), path)
            self.assertFalse((output / "docs" / "SUPER_TECNICO_AI_PRODUCT.md").exists())
            self.assertFalse((output / "tools" / "audit_ai_readiness.py").exists())


if __name__ == "__main__":
    unittest.main()
