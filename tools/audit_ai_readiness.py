from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def checkpoint(check_id: str, title: str, status: str, evidence: str) -> dict[str, str]:
    return {"id": check_id, "title": title, "status": status, "evidence": evidence}


def audit(root: Path) -> dict[str, Any]:
    brands: list[dict[str, Any]] = []
    source_documents = 0
    brands_with_sources = 0
    brands_with_quality = 0
    brands_with_provenance_policy = 0
    total_errors = 0
    total_topics = 0
    total_variants = 0

    for directory in sorted((root / "data" / "brands").iterdir()):
        config_path = directory / "brand.json"
        if not config_path.is_file():
            continue
        config = read_json(config_path)
        if config.get("enabled") is not True:
            continue
        web = directory / str(config.get("web_data") or "web")
        sources_path = web / "sources.json"
        quality_path = web / "quality.json"
        provenance_path = web / "provenance.json"
        sources = read_json(sources_path) if sources_path.is_file() else []
        source_count = len(sources) if isinstance(sources, list) else 0
        source_documents += source_count
        brands_with_sources += int(source_count > 0)
        brands_with_quality += int(quality_path.is_file())
        brands_with_provenance_policy += int(provenance_path.is_file())
        counts = config.get("counts") or {}
        total_errors += int(counts.get("errors") or 0)
        total_topics += int(counts.get("topics") or 0)
        total_variants += int(counts.get("variants") or 0)
        brands.append({
            "slug": config.get("slug") or directory.name,
            "data_version": config.get("data_version"),
            "errors": int(counts.get("errors") or 0),
            "topics": int(counts.get("topics") or 0),
            "variants": int(counts.get("variants") or 0),
            "source_documents": source_count,
            "quality_report": quality_path.is_file(),
            "provenance_policy": provenance_path.is_file(),
        })

    components = read_json(root / "data" / "components" / "catalog.json")
    component_meta = components.get("meta") or {}
    component_counts = component_meta.get("counts") or {}
    symbols = read_json(root / "data" / "electroia" / "symbol-library.json")
    symbol_report = read_json(root / "data" / "electroia" / "symbol-normalization-report.json")
    training = read_json(root / "data" / "training" / "collection.json")
    electronics = read_json(root / "data" / "electronics" / "collection.json")

    checks = [
        checkpoint("public_discovery", "Descubrimiento público para máquinas", "pass", "llms.txt y data/ai/discovery.json"),
        checkpoint("stable_contracts", "Contratos estables y versionados", "pass", "Manifiesto, JSON Schema y contrato OpenAPI de diseño"),
        checkpoint("focused_tools", "Herramientas centradas en objetivos", "pass", "Preflight, resolución, diagnóstico, componentes, casos y diagramas"),
        checkpoint("quality_labels", "Calidad y confianza explícitas", "pass", f"{brands_with_quality}/{len(brands)} marcas con informe y componentes con confidence"),
        checkpoint("source_traceability", "Fuentes aplicables por respuesta", "partial", f"{brands_with_sources}/{len(brands)} marcas con fuentes; {brands_with_provenance_policy} políticas históricas específicas"),
        checkpoint("remote_mcp", "Servidor MCP remoto", "planned", "ElectroIA dispone de stdio local; el transporte remoto sigue desactivado"),
        checkpoint("machine_auth", "Autenticación de clientes máquina", "planned", "Contrato API key/OAuth definido; sin emisión de credenciales"),
        checkpoint("metering", "Medición y facturación por uso", "planned", "Niveles de consumo definidos; sin contabilidad activa"),
        checkpoint("economic_benchmark", "Ahorro económico demostrado", "planned", "Plan y umbrales definidos; baseline pendiente"),
        checkpoint("anti_extraction", "Protección contra extracción masiva", "partial", "Política sin exportación masiva definida; falta aplicación en gateway remoto"),
    ]
    weights = {"pass": 2, "partial": 1, "planned": 0}
    readiness_score = round(100 * sum(weights[item["status"]] for item in checks) / (2 * len(checks)))

    return {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "private_preview_foundation",
        "readiness_score_percent": readiness_score,
        "score_meaning": "Preparación contractual y de datos; no disponibilidad comercial.",
        "content_inventory": {
            "brands": len(brands),
            "brands_with_sources": brands_with_sources,
            "brands_with_quality_report": brands_with_quality,
            "brands_with_specific_provenance_policy": brands_with_provenance_policy,
            "source_documents": source_documents,
            "hvac_errors": total_errors,
            "hvac_topics": total_topics,
            "hvac_variants": total_variants,
            "components": int(component_counts.get("components") or 0),
            "component_specifications": int(component_counts.get("specifications") or 0),
            "components_reviewed": int(component_counts.get("reviewed") or 0),
            "components_historical": int(component_counts.get("historical") or 0),
            "electroia_symbols": int(symbols.get("catalog_symbol_count") or 0),
            "electroia_symbols_reviewed": int((symbol_report.get("catalog_status_counts") or {}).get("engine_reviewed") or 0),
            "hvac_training_chapters": int((training.get("stats") or {}).get("chapters") or 0),
            "electronics_chapters": int((electronics.get("stats") or {}).get("chapters") or 0),
        },
        "checkpoints": checks,
        "release_blockers": [
            "Implementar el gateway remoto MCP/HTTPS con autenticación y cuotas.",
            "Crear proyecciones de respuesta que nunca expongan registros maestros completos.",
            "Registrar uso, coste, latencia, cache y resultado por herramienta.",
            "Completar el benchmark ciego antes de publicar promesas de ahorro.",
            "Definir condiciones comerciales, privacidad, soporte y proceso de alta.",
            "Validar seguridad y revisión de la plataforma antes de publicar en directorios."
        ],
        "brands": brands,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output or (root / "data" / "ai" / "readiness-report.json")
    result = audit(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "readiness_score_percent": result["readiness_score_percent"], "inventory": result["content_inventory"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
