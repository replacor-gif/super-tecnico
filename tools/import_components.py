#!/usr/bin/env python3
"""Create the public, read-only component catalogue from the private SQLite master."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


CHUNK_COUNT = 64
SUPPLEMENTS_PATH = Path(__file__).resolve().parents[1] / "data" / "component_additions.json"
QUALITY_ORDER = {
    "oficial": 7,
    "oficial_serie": 6,
    "oficial_importado": 5,
    "oficial_familia": 4,
    "curado": 3,
    "curado_serie": 2,
    "histórico_extraído": 1,
}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def public_url(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    parsed = urlparse(text)
    return text if parsed.scheme == "https" and parsed.netloc else None


def public_label(value: Any) -> str | None:
    text = str(value or "").strip()
    if text.casefold() in {"", "-", "—", "n/a", "na", "unknown", "desconocido"}:
        return None
    return text


def rows_by_component(connection: sqlite3.Connection, query: str) -> dict[int, list[dict[str, Any]]]:
    result: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in connection.execute(query):
        item = dict(row)
        component_id = int(item.pop("component_id"))
        result[component_id].append(item)
    return result


def build(database: Path, output: Path) -> dict[str, Any]:
    database = database.resolve()
    if not database.is_file():
        raise FileNotFoundError(database)

    connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"SQLite integrity_check: {integrity}")

        summaries = [
            dict(row)
            for row in connection.execute(
                """
                SELECT
                    v.*,
                    cs.voltage_max_v,
                    cs.current_max_a,
                    cs.power_max_w,
                    cs.rds_on_max_ohm,
                    cs.frequency_hz
                FROM v_component_summary v
                LEFT JOIN v_common_specs cs ON cs.component_id=v.component_id
                ORDER BY
                    v.part_number COLLATE NOCASE,
                    v.official_verified DESC,
                    v.confidence_score DESC,
                    v.component_id
                """
            )
        ]

        aliases = rows_by_component(
            connection,
            """
            SELECT component_id, alias, alias_type, notes
            FROM aliases
            ORDER BY component_id, alias COLLATE NOCASE
            """,
        )
        specifications = rows_by_component(
            connection,
            """
            SELECT
                specification_id, component_id, spec_key, name_es,
                minimum_value, typical_value, maximum_value, text_value,
                unit, conditions, confidence_score, notes
            FROM specifications
            ORDER BY component_id, specification_id
            """,
        )
        packages = rows_by_component(
            connection,
            """
            SELECT
                cp.component_id, p.canonical_name AS name, p.family,
                COALESCE(cp.pin_count,p.pin_count) AS pin_count,
                p.mount_type, cp.pinout_variant, cp.primary_package, cp.notes
            FROM component_packages cp
            JOIN packages p ON p.package_id=cp.package_id
            ORDER BY cp.component_id, cp.primary_package DESC, p.canonical_name
            """,
        )
        markings = rows_by_component(
            connection,
            """
            SELECT
                mk.component_id, mk.marking, p.canonical_name AS package,
                mk.pattern_kind, mk.confidence_score, mk.notes
            FROM markings mk
            LEFT JOIN packages p ON p.package_id=mk.package_id
            ORDER BY mk.component_id, mk.marking COLLATE NOCASE
            """,
        )
        pinouts = rows_by_component(
            connection,
            """
            SELECT
                po.component_id, p.canonical_name AS package, po.pin_number,
                po.pin_symbol, po.function_es, po.confidence_score, po.notes
            FROM pinouts po
            LEFT JOIN packages p ON p.package_id=po.package_id
            ORDER BY po.component_id, p.canonical_name, po.pin_number
            """,
        )
        applications = rows_by_component(
            connection,
            """
            SELECT component_id, application_es
            FROM applications
            ORDER BY component_id, application_es
            """,
        )
        queue = rows_by_component(
            connection,
            """
            SELECT component_id, priority, reason_es, status
            FROM verification_queue
            ORDER BY component_id, priority, verification_id
            """,
        )
        equivalents = rows_by_component(
            connection,
            """
            SELECT
                e.original_component_id AS component_id,
                c.component_id AS related_id,
                c.part_number,
                m.canonical_name AS manufacturer,
                e.compatibility_level,
                e.pinout_match,
                e.package_match,
                e.notes_es
            FROM equivalents e
            JOIN components c ON c.component_id=e.equivalent_component_id
            LEFT JOIN manufacturers m ON m.manufacturer_id=c.manufacturer_id
            ORDER BY e.original_component_id, c.part_number COLLATE NOCASE
            """,
        )

        source_rows = {
            int(row["component_id"]): dict(row)
            for row in connection.execute(
                """
                SELECT
                    c.component_id, s.title, s.publisher, s.url,
                    s.source_type, s.authority_level, s.retrieved_date
                FROM components c
                LEFT JOIN sources s ON s.source_id=c.primary_source_id
                """
            )
        }

        categories = sorted(
            {str(row["category"]) for row in summaries if row.get("category")},
            key=str.casefold,
        )
        manufacturers = sorted(
            {
                public_label(row.get("manufacturer"))
                for row in summaries
                if public_label(row.get("manufacturer"))
            },
            key=str.casefold,
        )
        package_names = sorted(
            {
                public_label(package["name"])
                for component_packages in packages.values()
                for package in component_packages
                if public_label(package.get("name"))
            },
            key=str.casefold,
        )

        catalogue: list[dict[str, Any]] = []
        chunks: dict[int, dict[str, Any]] = {index: {} for index in range(CHUNK_COUNT)}
        quality_counts: dict[str, int] = defaultdict(int)
        reviewed = 0
        historical = 0

        for row in summaries:
            component_id = int(row["component_id"])
            quality = str(row.get("data_quality") or "histórico_extraído")
            quality_counts[quality] += 1
            is_historical = quality == "histórico_extraído"
            historical += int(is_historical)
            reviewed += int(not is_historical)
            component_aliases = [item["alias"] for item in aliases.get(component_id, [])]
            component_packages = [
                {**item, "name": public_label(item.get("name"))}
                for item in packages.get(component_id, [])
            ]
            component_markings = [
                {**item, "package": public_label(item.get("package"))}
                for item in markings.get(component_id, [])
            ]

            index_item = {
                "id": component_id,
                "part_number": row["part_number"],
                "manufacturer": public_label(row.get("manufacturer")),
                "category": row.get("category"),
                "subtype": row.get("subtype_es"),
                "description": row.get("description_es"),
                "packages": [item["name"] for item in component_packages if item.get("name")],
                "markings": [item["marking"] for item in component_markings if item.get("marking")],
                "aliases": component_aliases,
                "quality": quality,
                "quality_rank": QUALITY_ORDER.get(quality, 0),
                "confidence": row.get("confidence_score"),
                "official": bool(row.get("official_verified")),
                "generic": bool(row.get("generic_reference")),
                "voltage_max_v": row.get("voltage_max_v"),
                "current_max_a": row.get("current_max_a"),
                "power_max_w": row.get("power_max_w"),
                "rds_on_max_ohm": row.get("rds_on_max_ohm"),
                "frequency_hz": row.get("frequency_hz"),
            }
            catalogue.append(index_item)

            source = source_rows.get(component_id) or {}
            source_url = public_url(source.get("url"))
            datasheet_url = public_url(row.get("datasheet_url"))
            detail = {
                **index_item,
                "lifecycle_status": (
                    "Pendiente de verificar" if is_historical else row.get("lifecycle_status")
                ),
                "notes": row.get("notes_es"),
                "datasheet_url": datasheet_url,
                "specifications": specifications.get(component_id, []),
                "package_details": component_packages,
                "marking_details": component_markings,
                "pinouts": pinouts.get(component_id, []),
                "applications": [
                    item["application_es"]
                    for item in applications.get(component_id, [])
                    if item.get("application_es")
                ],
                "equivalents": equivalents.get(component_id, []),
                "verification": queue.get(component_id, []),
                "source": {
                    "title": source.get("title"),
                    "publisher": source.get("publisher"),
                    "url": source_url,
                    "type": source.get("source_type"),
                    "authority": source.get("authority_level"),
                    "retrieved_date": source.get("retrieved_date"),
                },
            }
            chunks[component_id % CHUNK_COUNT][str(component_id)] = detail

        supplements_sha256 = None
        supplement_specifications = 0
        supplement_markings = 0
        if SUPPLEMENTS_PATH.is_file():
            supplements_sha256 = hashlib.sha256(SUPPLEMENTS_PATH.read_bytes()).hexdigest()
            supplements = json.loads(SUPPLEMENTS_PATH.read_text(encoding="utf-8"))
            existing_ids = {int(item["id"]) for item in catalogue}
            for detail in supplements:
                component_id = int(detail["id"])
                if component_id in existing_ids:
                    raise RuntimeError(f"ID suplementario duplicado: {component_id}")
                if component_id % CHUNK_COUNT not in chunks:
                    raise RuntimeError(f"ID suplementario no válido: {component_id}")
                for key in ("datasheet_url",):
                    if detail.get(key) and not public_url(detail[key]):
                        raise RuntimeError(f"URL suplementaria no segura: {component_id}")
                source_url = (detail.get("source") or {}).get("url")
                if source_url and not public_url(source_url):
                    raise RuntimeError(f"Fuente suplementaria no segura: {component_id}")

                index_item = {
                    key: detail.get(key)
                    for key in (
                        "id", "part_number", "manufacturer", "category", "subtype",
                        "description", "packages", "markings", "aliases", "quality",
                        "quality_rank", "confidence", "official", "generic",
                        "voltage_max_v", "current_max_a", "power_max_w",
                        "rds_on_max_ohm", "frequency_hz",
                    )
                }
                catalogue.append(index_item)
                chunks[component_id % CHUNK_COUNT][str(component_id)] = detail
                existing_ids.add(component_id)
                quality_counts[str(detail.get("quality") or "curado")] += 1
                reviewed += 1
                supplement_specifications += len(detail.get("specifications") or [])
                supplement_markings += len(detail.get("marking_details") or [])
                if detail.get("manufacturer"):
                    manufacturers.append(str(detail["manufacturer"]))
                package_names.extend(
                    str(value) for value in (detail.get("packages") or []) if public_label(value)
                )

        manufacturers = sorted(set(manufacturers), key=str.casefold)
        package_names = sorted(set(package_names), key=str.casefold)
        catalogue.sort(
            key=lambda item: (
                str(item.get("part_number") or "").casefold(),
                -int(bool(item.get("official"))),
                -float(item.get("confidence") or 0),
                int(item["id"]),
            )
        )

        metadata = {
            str(row["key"]): str(row["value"])
            for row in connection.execute("SELECT key,value FROM metadata")
        }
        generated_at = datetime.now(timezone.utc).isoformat()
        database_sha256 = hashlib.sha256(database.read_bytes()).hexdigest()
        public_meta = {
            "schema_version": "1.0",
            "source_schema_version": connection.execute("PRAGMA user_version").fetchone()[0],
            "data_version": metadata.get("version", "1.0"),
            "generated_at_utc": generated_at,
            "source_sha256": database_sha256,
            "supplements_sha256": supplements_sha256,
            "counts": {
                "components": len(catalogue),
                "specifications": (
                    sum(len(items) for items in specifications.values())
                    + supplement_specifications
                ),
                "markings": (
                    sum(len(items) for items in markings.values())
                    + supplement_markings
                ),
                "manufacturers": len(manufacturers),
                "packages": len(package_names),
                "reviewed": reviewed,
                "historical": historical,
            },
            "quality_counts": dict(sorted(quality_counts.items())),
            "chunk_count": CHUNK_COUNT,
            "warning": (
                "Los registros históricos son candidatos pendientes de verificar. "
                "Nunca deben utilizarse como único criterio de identificación o sustitución."
            ),
        }

        write_json(
            output / "catalog.json",
            {
                "meta": public_meta,
                "filters": {
                    "categories": categories,
                    "manufacturers": manufacturers,
                    "packages": package_names,
                },
                "components": catalogue,
            },
        )
        details_dir = output / "details"
        for chunk_id, items in chunks.items():
            write_json(details_dir / f"{chunk_id}.json", items)
        return public_meta
    finally:
        connection.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "components",
    )
    args = parser.parse_args()
    report = build(args.database, args.output)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
