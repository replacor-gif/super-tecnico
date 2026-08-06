#!/usr/bin/env python3
"""Import the expanded Replacor database as safe reference-only records."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


GENERATION = "component-reference-database-v5"
RETRIEVED_DATE = "2026-07-31"
SOURCE_MANUFACTURERS = {
    "FUJI_HS": "Fuji Electric", "FUJI_MOD": "Fuji Electric",
    "INF_MODULE": "Infineon", "INF_MOS": "Infineon",
    "LITT_VAR": "Littelfuse", "MITSU_MOD": "Mitsubishi Electric",
    "OMRON_RELAY": "Omron", "PAN_RELAY": "Panasonic",
    "SEMIKRON_MOD": "Semikron Danfoss",
    "ST_BLDC": "STMicroelectronics", "ST_BRIDGE": "STMicroelectronics",
    "ST_DIODE": "STMicroelectronics", "ST_MCU": "STMicroelectronics",
    "ST_STEPPER": "STMicroelectronics", "ST_THY": "STMicroelectronics",
    "TDK_NTC": "TDK", "TI_CURRENT": "Texas Instruments",
    "TI_GATE": "Texas Instruments", "TI_MOTOR": "Texas Instruments",
    "TI_REG": "Texas Instruments",
}


def normalize(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def https_url(value: Any) -> str | None:
    text = str(value or "").strip()
    return text if text.startswith("https://") else None


def mapped_category(category: str, subcategory: str) -> str:
    text = f"{category} {subcategory}".casefold()
    rules = (
        (("módulos ipm",), "Módulo de potencia IPM"),
        (("módulos igbt", "módulos potencia", "módulos de potencia"), "Módulo de potencia"),
        (("optoacopladores", "optotriacs", "aisladores digitales"), "Optoacoplador"),
        (("mosfet", "jfet", " sic ", " gan "), "MOSFET"),
        (("igbt discret",), "IGBT"),
        (("diodos", "zener", "schottky", "rectificadores", "tvs", "esd"), "Diodo"),
        (("triac", " scr ", "diac", "tiristor"), "Tiristor / TRIAC"),
        (("transistores bjt", "darlington", "transistores digitales"), "Transistor BJT"),
        (("operacionales", "comparadores", "instrumentación"), "Amplificador / comparador"),
        (("reguladores", "ldo", "referencias"), "Regulador / referencia"),
        (("controladores smps", "buck", "boost", "dc-dc", "llc", "resonantes", "pfc"), "Controlador de fuente"),
        (("drivers", "control de potencia", "motores", "puentes h"), "Driver de potencia"),
        (("sensores", "temperatura", "termostatos", "hall", "presión", "corriente"), "Sensor"),
        (("relés", "actuadores", "photomos"), "Relé / actuador"),
        (("varistores", "protección", "efuse", "hot-swap", "bms", "supervisores", "watchdog"), "Protección"),
        (("ntc", "ptc", "cristales", "resonadores", "osciladores", "fusibles", "shunts"), "Componente pasivo"),
    )
    for needles, result in rules:
        if any(needle in text for needle in needles):
            return result
    return {
        "Integrados": "Circuito integrado", "Sensores": "Sensor",
        "Relés y actuadores": "Relé / actuador", "Pasivos": "Componente pasivo",
        "Protecciones": "Protección", "Módulos potencia": "Módulo de potencia",
    }.get(category, "No clasificado")


def quality(source_id: str) -> tuple[str, float, int, str]:
    if source_id == "BASE":
        return "índice_referencia", 0.30, 1, "base histórica de referencias"
    if source_id.startswith("KICAD"):
        return "índice_referencia", 0.42, 3, "biblioteca oficial de símbolos"
    return "índice_fabricante", 0.55, 4, "catálogo general del fabricante"


def choose(rows: list[dict[str, Any]], sources: dict[str, dict[str, Any]]) -> dict[str, Any]:
    def score(row: dict[str, Any]) -> tuple[int, int, int, int]:
        sid = str(row.get("source_id") or "")
        source = sources.get(sid, {})
        return (
            int(row.get("category") != "Climatización"),
            int(sid not in {"BASE", "KICAD"}),
            int(bool(https_url(source.get("url")))),
            int(bool(str(row.get("notes") or "").strip())),
        )
    return max(rows, key=score)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def build(database: Path, catalogue_path: Path, supplements_path: Path, report_path: Path) -> dict[str, Any]:
    catalogue = load_json(catalogue_path)
    supplements = load_json(supplements_path)
    old_ids = {int(item["id"]) for item in supplements if item.get("generation") == GENERATION}
    base_supplements = [item for item in supplements if item.get("generation") != GENERATION]
    existing_items = [item for item in catalogue.get("components", []) if int(item.get("id") or 0) not in old_ids]
    existing = {normalize(item.get("part_number")) for item in existing_items if normalize(item.get("part_number"))}

    connection = sqlite3.connect(f"file:{database.resolve().as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"SQLite integrity_check: {integrity}")
        sources = {str(row["source_id"]): dict(row) for row in connection.execute("SELECT * FROM sources")}
        rows = [dict(row) for row in connection.execute("SELECT * FROM components")]
    finally:
        connection.close()

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = normalize(row.get("reference"))
        if key:
            groups[key].append(row)

    max_id = max((int(item.get("id") or 0) for item in existing_items + base_supplements), default=0)
    imported: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    skipped = 0
    for key in sorted(groups):
        if key in existing:
            skipped += 1
            continue
        rows_for_reference = groups[key]
        selected = choose(rows_for_reference, sources)
        source_id = str(selected.get("source_id") or "")
        source = sources.get(source_id, {})
        quality_name, confidence, authority, source_type = quality(source_id)
        manufacturer = SOURCE_MANUFACTURERS.get(source_id)
        part_number = str(selected.get("reference") or "").strip()
        raw_variants = sorted({str(row.get("reference") or "").strip() for row in rows_for_reference}, key=str.casefold)
        category = mapped_category(str(selected.get("category") or ""), str(selected.get("subcategory") or ""))
        applications = sorted({f"Climatización: {row['subcategory']}" for row in rows_for_reference if row.get("category") == "Climatización" and row.get("subcategory")})
        notes = " ".join(value for value in (
            str(selected.get("notes") or "").strip(), str(source.get("notes") or "").strip(),
            "Ficha de índice para identificación. Verifica datasheet exacto, sufijo, encapsulado, patillaje y límites antes de comprobar o sustituir.",
        ) if value)
        max_id += 1
        imported.append({
            "id": max_id, "part_number": part_number, "manufacturer": manufacturer,
            "category": category, "subtype": str(selected.get("subcategory") or "").strip() or None,
            "description": f"Referencia de índice para identificación, clasificada como {selected.get('subcategory') or selected.get('category') or 'componente electrónico'}.",
            "packages": [], "markings": [],
            "aliases": [value for value in raw_variants if value.casefold() != part_number.casefold()],
            "quality": quality_name, "quality_rank": 1, "confidence": confidence,
            "official": False, "generic": bool(re.search(r"(?i)xxx", part_number)) or not any(ch.isdigit() for ch in part_number),
            "record_level": "indice", "voltage_max_v": None, "current_max_a": None,
            "power_max_w": None, "rds_on_max_ohm": None, "frequency_hz": None,
            "lifecycle_status": "Referencia pendiente de contrastar con la ficha exacta",
            "notes": notes, "datasheet_url": None, "specifications": [],
            "package_details": [], "marking_details": [], "pinouts": [],
            "applications": applications, "equivalents": [],
            "verification": [{"priority": 3, "reason_es": "Referencia de índice sin parámetros eléctricos ni patillaje verificados.", "status": "pendiente"}],
            "source": {"title": source.get("source_name") or "Base de referencias Replacor", "publisher": manufacturer,
                       "url": https_url(source.get("url")), "type": source_type, "authority": authority,
                       "retrieved_date": source.get("consulted_on") or RETRIEVED_DATE, "source_id": source_id},
            "generation": GENERATION,
        })
        existing.add(key)
        category_counts[category] += 1
        source_counts[source_id or "SIN_FUENTE"] += 1

    merged = base_supplements + imported
    write_json(supplements_path, merged)
    report = {
        "generation": GENERATION, "input_rows": len(rows),
        "input_normalized_references": len(groups), "overlap_skipped": skipped,
        "previous_generated_replaced": len(old_ids), "references_imported": len(imported),
        "supplement_total": len(merged),
        "first_generated_id": imported[0]["id"] if imported else None,
        "last_generated_id": imported[-1]["id"] if imported else None,
        "categories": dict(category_counts.most_common()), "sources": dict(source_counts.most_common()),
        "safety": {"record_level": "indice", "automatic_comparison_eligible": False,
                   "reason": "No hay parámetros eléctricos, encapsulado ni patillaje suficientes."},
    }
    write_json(report_path, report)
    return report


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("--catalogue", type=Path, default=root / "data/components/catalog.json")
    parser.add_argument("--supplements", type=Path, default=root / "data/component_additions.json")
    parser.add_argument("--report", type=Path, default=root / "data/component_reference_import_v5_report.json")
    args = parser.parse_args()
    print(json.dumps(build(args.database, args.catalogue, args.supplements, args.report), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
