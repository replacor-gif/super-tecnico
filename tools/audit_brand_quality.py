#!/usr/bin/env python3
"""Audita la profundidad técnica de una marca web de Super Técnico."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def present(values: Any) -> list[Any]:
    return [value for value in (values or []) if value is not None]


def has_page(sources: list[dict[str, Any]]) -> bool:
    return any(str(source.get("page_start") or "").strip() for source in sources)


def interpretation_quality(item: dict[str, Any]) -> dict[str, Any]:
    info = present(item.get("info_items"))
    sources = present(item.get("sources"))
    causes = [row for row in info if row.get("item_type") == "cause"]
    checks = [row for row in info if row.get("item_type") == "check"]
    behavior = present(item.get("operational_impacts")) or [
        row for row in info if row.get("item_type") == "machine_behavior"
    ]
    datasets = present(item.get("datasets"))
    page = has_page(sources)
    reviewed = item.get("review_status") == "reviewed"
    meaning = bool(str(item.get("title") or item.get("description") or "").strip())
    grouping_reference = (
        item.get("entry_role") == "grouping_reference"
        and bool(present(item.get("related_errors")))
    )

    score = sum((
        10 if meaning else 0,
        10 if sources else 0,
        15 if page else 0,
        20 if causes else 0,
        20 if checks else 0,
        10 if behavior else 0,
        10 if datasets else 0,
        5 if reviewed else 0,
    ))
    missing = []
    if not causes:
        missing.append("causas")
    if not checks:
        missing.append("comprobaciones")
    if not behavior:
        missing.append("efecto_funcionamiento")
    if not datasets:
        missing.append("valores_tecnicos")
    if not page:
        missing.append("pagina_exacta")
    if not sources:
        missing.append("fuente")

    if grouping_reference and sources and page:
        status = "grouping_reference"
        score = max(score, 95)
        missing = []
    elif causes and checks and page and (behavior or datasets) and score >= 75:
        status = "complete"
    elif causes and checks and sources and score >= 55:
        status = "developed"
    elif causes or checks or behavior or datasets:
        status = "partial"
    elif sources:
        status = "reference_only"
    else:
        status = "unverified"

    return {
        "status": status,
        "score": score,
        "missing": missing,
        "counts": {
            "causes": len(causes),
            "checks": len(checks),
            "operational_impacts": len(present(item.get("operational_impacts"))),
            "datasets": len(datasets),
            "sources": len(sources),
        },
    }


def variant_quality(item: dict[str, Any]) -> dict[str, Any]:
    sources = present(item.get("sources"))
    steps = present(item.get("steps"))
    sections = present(item.get("sections"))
    parameters = present(item.get("parameters"))
    monitoring = present(item.get("monitoring_points"))
    controller = item.get("controller")
    page = has_page(sources)
    score = sum((
        15 if str(item.get("title") or "").strip() else 0,
        10 if sources else 0,
        15 if page else 0,
        25 if steps else 0,
        15 if sections else 0,
        10 if parameters else 0,
        5 if monitoring else 0,
        5 if controller else 0,
    ))
    missing = []
    if not steps:
        missing.append("pasos")
    if not sections:
        missing.append("explicacion")
    if not page:
        missing.append("pagina_exacta")
    if not sources:
        missing.append("fuente")

    if score >= 75 and sources and page and (steps or parameters):
        status = "complete"
    elif score >= 55 and sources and (steps or sections or parameters):
        status = "developed"
    elif sources and (steps or sections or parameters or monitoring or controller):
        status = "partial"
    elif sources:
        status = "reference_only"
    else:
        status = "unverified"
    return {"status": status, "score": score, "missing": missing}


def percentage(count: int, total: int) -> float:
    return round((100 * count / total), 1) if total else 0.0


def audit_brand(brand_dir: Path) -> dict[str, Any]:
    config = load(brand_dir / "brand.json")
    web = brand_dir / str(config.get("web_data") or "web")
    error_rows = []
    interpretation_statuses: Counter[str] = Counter()
    component_counts: Counter[str] = Counter()
    interpretation_total = 0

    for path in sorted((web / "errors" / "details").glob("*.json"), key=lambda p: int(p.stem)):
        error = load(path)
        assessments = []
        for interpretation in present(error.get("interpretations")):
            quality = interpretation_quality(interpretation)
            assessments.append(quality)
            interpretation_total += 1
            interpretation_statuses[quality["status"]] += 1
            if quality["status"] == "grouping_reference":
                continue
            counts = quality["counts"]
            for key in ("causes", "checks", "operational_impacts", "datasets"):
                if counts[key]:
                    component_counts[key] += 1
            if "pagina_exacta" not in quality["missing"]:
                component_counts["exact_page"] += 1

        weakest = min((row["score"] for row in assessments), default=0)
        combined_missing = sorted({name for row in assessments for name in row["missing"]})
        error_rows.append({
            "id": error.get("id"),
            "code": error.get("code_display"),
            "title": error.get("short_label"),
            "interpretations": len(assessments),
            "lowest_score": weakest,
            "statuses": dict(Counter(row["status"] for row in assessments)),
            "missing": combined_missing,
        })

    grouping_total = interpretation_statuses["grouping_reference"]
    technical_total = interpretation_total - grouping_total

    variants = []
    variant_statuses: Counter[str] = Counter()
    for path in sorted((web / "topics").glob("*.json"), key=lambda p: int(p.stem)):
        topic = load(path)
        for variant in present(topic.get("variants")):
            quality = variant_quality(variant)
            variant_statuses[quality["status"]] += 1
            variants.append({
                "id": variant.get("id"),
                "topic_id": topic.get("id"),
                "category": (topic.get("category") or {}).get("name"),
                "title": variant.get("title"),
                **quality,
            })

    error_rows.sort(key=lambda row: (row["lowest_score"], str(row["code"])))
    variants.sort(key=lambda row: (row["score"], str(row["title"])))
    return {
        "schema_version": "1.0",
        "brand": config.get("display_name") or config.get("name"),
        "brand_slug": config.get("slug"),
        "data_version": config.get("data_version"),
        "quality_standard": {
            "complete": "Causas y comprobaciones, página exacta y al menos efecto operativo o valores técnicos.",
            "developed": "Causas, comprobaciones y fuente; todavía falta algún bloque de profundidad.",
            "partial": "Tiene desarrollo técnico, pero faltan causas, comprobaciones o trazabilidad suficiente.",
            "grouping_reference": "Código paraguas con fuente y enlaces directos a las variantes técnicas desarrolladas; no duplica sus comprobaciones.",
            "reference_only": "Solo significado y fuente. No debe presentarse como ficha técnica completa.",
            "unverified": "No tiene fuente documental utilizable.",
        },
        "errors": {
            "entries": len(error_rows),
            "interpretations": interpretation_total,
            "technical_interpretations": technical_total,
            "grouping_references": grouping_total,
            "status_counts": dict(interpretation_statuses),
            "component_coverage": {
                key: {"count": component_counts[key], "percent": percentage(component_counts[key], technical_total)}
                for key in ("causes", "checks", "operational_impacts", "datasets", "exact_page")
            },
            "backlog": error_rows,
        },
        "technical_variants": {
            "entries": len(variants),
            "status_counts": dict(variant_statuses),
            "backlog": variants,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("brand", help="Slug de la marca")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    brand_dir = args.root / "data" / "brands" / args.brand
    report = audit_brand(brand_dir)
    output = args.output or brand_dir / str(load(brand_dir / "brand.json").get("web_data") or "web") / "quality.json"
    write(output, report)
    print(json.dumps({
        "output": str(output),
        "errors": report["errors"]["entries"],
        "interpretations": report["errors"]["interpretations"],
        "error_statuses": report["errors"]["status_counts"],
        "variant_statuses": report["technical_variants"]["status_counts"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
