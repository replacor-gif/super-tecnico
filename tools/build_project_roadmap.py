#!/usr/bin/env python3
"""Build the public, measurable project roadmap from current reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "core" / "project-roadmap.json"


def read(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def build() -> dict:
    symbols = read("data/electroia/symbol-normalization-report.json")
    electroia_release = read("data/electroia/public-release-readiness.json")
    readiness = read("data/ai/readiness-report.json")
    regulations = read("data/regulations/tool-manifest.json")
    connectors = read("data/connectors/tool-manifest.json")
    embedded = read("data/embedded-platforms/tool-manifest.json")
    reviewed = int(symbols["catalog_status_counts"]["engine_reviewed"])
    draft = int(symbols["catalog_status_counts"]["auto_draft"])
    total = int(symbols["catalog_symbols"])
    remaining = [
        {"family": family, "pending_symbols": quality["auto_draft"]}
        for family, quality in symbols["category_quality"].items()
        if quality["auto_draft"]
    ]
    remaining.sort(key=lambda item: (-item["pending_symbols"], item["family"]))
    public_ai_tools = int(str(regulations.get("status", "")).startswith("public"))
    public_ai_tools += sum(str(item.get("state", "")).startswith("public") for item in connectors.get("tools", []))
    public_ai_tools += sum(str(item.get("state", "")).startswith("public") for item in embedded.get("tools", []))
    if electroia_release["summary"]["public_information_surface_ready"]:
        public_ai_tools += 2
    return {
        "schema_version": "1.0",
        "updated_at": "2026-08-24",
        "release_stage": "beta_publica_competente",
        "summary": {
            "electroia_catalog_symbols": total,
            "electroia_reviewed_symbols": reviewed,
            "electroia_pending_symbols": draft,
            "electroia_reviewed_percent": round(reviewed * 100 / total, 1),
            "electroia_complete_families": len(symbols["fully_reviewed_categories"]),
            "electroia_total_families": len(symbols["category_quality"]),
            "electroia_release_stage": electroia_release["release_stage"],
            "electroia_professional_examples": electroia_release["summary"]["professional_examples"],
            "electroia_component_overlaps": electroia_release["summary"]["component_overlaps"],
            "electroia_wire_component_conflicts": electroia_release["summary"]["wire_component_conflicts"],
            "electroia_public_execution_ready": electroia_release["summary"]["public_execution_ready"],
            "public_ai_tools": public_ai_tools,
            "ai_readiness_percent": readiness["readiness_score_percent"],
        },
        "remaining_electroia_families": remaining,
        "priorities": [
            {
                "id": "electroia-professional-hardening",
                "area": "ElectroIA",
                "title": "Ampliar pruebas y perfiles profesionales",
                "status": "in_progress",
                "progress": {"done": reviewed, "total": total, "unit": "símbolos"},
                "next_action": "Validar más esquemas reales y ampliar ICT, energía, documentación de cuadros y perfiles normativos sin degradar el catálogo ya revisado.",
            },
            {
                "id": "diagram-real-cases",
                "area": "ElectroIA",
                "title": "Validar diagramas completos de casos reales",
                "status": "field_validation",
                "progress": {"done": electroia_release["summary"]["professional_examples"], "total": 20, "unit": "casos reales"},
                "next_action": "Probar en móvil otros quince esquemas reales de cuadros, automatismos, electrónica HVAC y controladores embebidos y registrar cualquier corrección visual.",
            },
            {
                "id": "duct-field-validation",
                "area": "Conductos",
                "title": "Afinar el diseñador con casos de campo",
                "status": "field_validation",
                "next_action": "Añadir pérdida de carga, accesorios, presión disponible y ruido sin perder la edición táctil sencilla del plano.",
            },
            {
                "id": "frigorista-field-validation",
                "area": "Frigorista",
                "title": "Ampliar diagnóstico Mollier con evidencias reales",
                "status": "field_validation",
                "next_action": "Contrastar diagnósticos completos, tuberías y desagües con instalaciones y modelos aportados por técnicos.",
            },
            {
                "id": "regulation-reviewed-rules",
                "area": "Normativa",
                "title": "Convertir consultas frecuentes en reglas revisadas",
                "status": "in_progress",
                "next_action": "Priorizar las búsquedas reales y documentar ámbito, excepciones, versión y fuente exacta de cada regla de cálculo.",
            },
            {
                "id": "ai-remote-service",
                "area": "SINAPSYS / IA",
                "title": "Preparar el servicio remoto para IAs",
                "status": "planned",
                "next_action": "Medir utilidad y coste de las herramientas gratuitas antes de activar MCP remoto, autenticación, cuotas o cobro.",
            },
            {
                "id": "cross-domain-budgeting",
                "area": "Proyectos",
                "title": "Presupuesto técnico transversal",
                "status": "foundation_only",
                "next_action": "Conectar mediciones de climatización, electricidad, agua y refrigeración con bases de precios versionadas sin mezclar cálculo técnico y precio.",
            },
        ],
        "status_labels": {
            "in_progress": "En desarrollo",
            "field_validation": "Necesita casos de campo",
            "planned": "Planificado",
            "foundation_only": "Base preparada",
        },
        "notice": "El estado indica cobertura de la beta, no certificación normativa ni sustitución del criterio profesional.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = json.dumps(build(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != content:
            raise SystemExit("data/core/project-roadmap.json está desactualizado")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(content, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
