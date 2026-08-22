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
    def test_public_page_explains_free_regulation_preview_without_false_availability(self):
        html = (ROOT / "ia-integracion.html").read_text(encoding="utf-8")
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Buscador de normativa abierto y gratuito", html)
        self.assertIn("los demás contratos siguen siendo diseño remoto", html)
        self.assertIn("Normativa · API activa", html)
        self.assertIn("data/ai/discovery.json", html)
        self.assertIn("data/ai/readiness-report.json", html)
        self.assertIn("data/ai/tool-strategy.json", html)
        self.assertIn("data/ai/storage-policy.json", html)
        self.assertIn('href="ia-integracion.html"', home)
        self.assertNotIn("4097", html)
        self.assertNotRegex(html, r"sk-[A-Za-z0-9_-]{12,}")

    def test_discovery_separates_knowledge_and_diagram_services(self):
        discovery = load(ROOT / "data" / "ai" / "discovery.json")
        services = {item["id"]: item for item in discovery["service_families"]}
        self.assertEqual(discovery["status"], "public_free_preview_regulations_connectors_and_embedded_platforms")
        self.assertTrue(discovery["security"]["remote_execution_enabled"])
        self.assertEqual(
            discovery["security"]["remote_execution_scope"],
            [
                "supertecnico_search_regulations",
                "supertecnico_search_connectors",
                "supertecnico_get_connector",
                "supertecnico_resolve_connector_contact",
                "supertecnico_search_embedded_platforms",
                "supertecnico_get_embedded_platform",
                "supertecnico_recommend_embedded_platforms",
            ],
        )
        self.assertEqual(discovery["access_model"]["humans"]["site_access"], "free")
        self.assertEqual(discovery["access_model"]["machines"]["current_execution"], "enabled_for_regulation_connector_and_embedded_platform_lookup")
        self.assertEqual(discovery["access_model"]["machines"]["bulk_dataset_export"], "not_offered")
        self.assertIn("super-tecnico-knowledge", services)
        self.assertIn("electroia-diagram-engine", services)
        self.assertIn("replacor-embedded-platform-core", services)

    def test_tool_contract_uses_free_preflight_and_compact_paid_levels(self):
        manifest = load(ROOT / "data" / "ai" / "tool-manifest.json")
        tools = {item["name"]: item for item in manifest["tools"]}
        self.assertTrue(manifest["execution_enabled"])
        self.assertEqual(
            manifest["execution_scope"],
            [
                "supertecnico_search_regulations",
                "supertecnico_search_connectors",
                "supertecnico_get_connector",
                "supertecnico_resolve_connector_contact",
                "supertecnico_search_embedded_platforms",
                "supertecnico_get_embedded_platform",
                "supertecnico_recommend_embedded_platforms",
            ],
        )
        self.assertTrue(manifest["routing_policy"]["preflight_first"])
        self.assertFalse(manifest["routing_policy"]["bulk_export_allowed"])
        self.assertIn("status", manifest["default_output_schema"]["required"])
        self.assertIn("confidence", manifest["default_output_schema"]["required"])
        self.assertIn("source_ids", manifest["default_output_schema"]["required"])
        self.assertIn("usage", manifest["default_output_schema"]["properties"])
        self.assertEqual(tools["supertecnico_check_coverage"]["billing_tier"], "free")
        self.assertLessEqual(tools["supertecnico_check_coverage"]["target_output_tokens"], 250)
        self.assertEqual(tools["supertecnico_get_diagnostic"]["billing_tier"], "metered_diagnostic")
        self.assertEqual(tools["supertecnico_search_regulations"]["state"], "public_free_preview")
        self.assertEqual(tools["supertecnico_search_regulations"]["billing_tier"], "free_preview")
        self.assertEqual(tools["supertecnico_search_regulations"]["input_schema"]["properties"]["limit"]["maximum"], 20)
        self.assertEqual(tools["supertecnico_recommend_embedded_platforms"]["state"], "public_http_beta")
        self.assertIn("delegate", tools["supertecnico_render_diagram"])
        self.assertIn("supertecnico_get_compact_context", tools)
        self.assertIn("supertecnico_validate_measurements", tools)
        self.assertIn("supertecnico_get_next_measurement", tools)
        self.assertIn("supertecnico_validate_answer", tools)
        self.assertEqual(tools["supertecnico_validate_measurements"]["economic_class"], "micro")
        self.assertTrue(all(item["annotations"]["readOnlyHint"] for item in tools.values()))

    def test_openapi_is_explicitly_non_executable_and_protects_database(self):
        contract = load(ROOT / "data" / "ai" / "knowledge-api-contract.openapi.json")
        discovery = load(ROOT / "data" / "ai" / "discovery.json")
        self.assertEqual(contract["openapi"], "3.1.0")
        self.assertFalse(contract["x-execution-enabled"])
        self.assertTrue(contract["x-do-not-call-until-enabled"])
        self.assertIn("ApiKeyAuth", contract["components"]["securitySchemes"])
        self.assertIn("/knowledge/compact", contract["paths"])
        self.assertIn("/validate/measurements", contract["paths"])
        self.assertIn("/diagnostics/next-measurement", contract["paths"])
        self.assertIn("/validate/answer", contract["paths"])
        self.assertFalse(discovery["security"]["database_direct_access"])
        self.assertNotIn("4097", json.dumps(contract))

    def test_future_metering_schema_stores_hashes_not_raw_secrets(self):
        sql = (ROOT / "database" / "ai_gateway.schema.sql").read_text(encoding="utf-8")
        self.assertIn("st_ai_clients", sql)
        self.assertIn("st_ai_credentials", sql)
        self.assertIn("secret_hash", sql)
        self.assertIn("st_ai_usage_events", sql)
        self.assertIn("billable_units", sql)
        self.assertIn("input_tokens", sql)
        self.assertIn("estimated_searches_avoided", sql)
        self.assertIn("internal_compute_cost_microunits", sql)
        self.assertIn("estimated_without_tool_cost_microunits", sql)
        self.assertIn("st_ai_security_events", sql)
        self.assertIn("st_ai_benchmark_runs", sql)
        self.assertNotIn("4097", sql)
        self.assertNotRegex(sql, r"sk-[A-Za-z0-9_-]{12,}")

    def test_public_regulation_endpoint_is_limited_traceable_and_measured(self):
        endpoint = (ROOT / "api" / "regulations.php").read_text(encoding="utf-8")
        router = (ROOT / "api" / "index.php").read_text(encoding="utf-8")
        schema = (ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
        contract = load(ROOT / "data" / "regulations" / "tool-manifest.json")
        self.assertIn("regulation-search", router)
        self.assertIn("regulation-result-open", router)
        self.assertIn("source_content_sha256", endpoint)
        self.assertIn("official_page_url", endpoint)
        self.assertIn("free_preview", endpoint)
        self.assertIn("st_regulation_search_events", schema)
        self.assertIn("query_hash", schema)
        self.assertNotIn("ip_address", schema)
        self.assertEqual(contract["status"], "public_free_preview")
        self.assertEqual(contract["access"]["maximum_results"], 20)
        self.assertFalse(contract["access"]["bulk_dataset_export"])
        self.assertEqual(contract["measurement"]["retention_days"], 180)

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
        self.assertEqual(published["content_inventory"]["regulation_documents"], 18)
        self.assertEqual(published["content_inventory"]["strategy_tools_evaluated"], 16)
        self.assertEqual(published["content_inventory"]["strategy_phase_one_tools"], 5)
        self.assertGreater(published["content_inventory"]["source_documents"], 200)
        self.assertIn("economic_benchmark", {item["id"] for item in published["checkpoints"]})

    def test_strategy_evaluates_every_handoff_tool_without_building_everything(self):
        strategy = load(ROOT / "data" / "ai" / "tool-strategy.json")
        storage = load(ROOT / "data" / "ai" / "storage-policy.json")
        tools = strategy["tools"]
        self.assertEqual(strategy["status"], "adopted_as_product_roadmap")
        self.assertFalse(strategy["implementation_policy"]["build_all_at_once"])
        self.assertEqual(len(tools), 16)
        self.assertEqual(len({item["id"] for item in tools}), 16)
        self.assertTrue(all(item.get("decision") and item.get("next_step") for item in tools))
        self.assertEqual({item["id"] for item in tools if item["phase"] == 1}, set(strategy["priority_now"]))
        self.assertFalse(storage["public_response"]["bulk_dataset_export"])
        self.assertFalse(storage["public_response"]["internal_compute_cost_exposed"])

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
                "data/ai/tool-strategy.json",
                "data/ai/storage-policy.json",
                "data/regulations/tool-manifest.json",
                "assets/regulations-search.css",
            ):
                self.assertTrue((output / path).is_file(), path)
            self.assertFalse((output / "docs" / "SUPER_TECNICO_AI_PRODUCT.md").exists())
            self.assertFalse((output / "tools" / "audit_ai_readiness.py").exists())


if __name__ == "__main__":
    unittest.main()
