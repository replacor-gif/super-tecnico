#!/usr/bin/env python3
"""Convert the Daikin reference package into Super Técnico web projections."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CATEGORIES = [
    (1, "errors", "Errores y protecciones", "Códigos y tablas de errores, manteniendo separadas las familias documentales."),
    (2, "diagnostic_access", "Obtención de códigos y subcódigos", "Métodos documentados para consultar códigos desde mandos y sistemas compatibles."),
    (3, "service_modes", "Modos de servicio", "Funcionamiento de emergencia, Pump Down y pruebas iniciadas por el técnico."),
    (4, "configuration", "Configuración y programación", "Pulsadores, interruptores, placas y funciones configurables."),
    (5, "controllers_buses", "Mandos y control", "Variantes de mandos, historial, ajustes y configuración principal/secundario."),
    (6, "drainage_overflow", "Drenaje y desbordamiento", "Bomba, flotador y códigos relacionados con el sistema de evacuación."),
    (7, "system_architecture", "Arquitectura de sistemas", "Información de familias Multi-Split, Sky Air y VRV que ayuda a reconocer la variante."),
]

TOPIC_SPECS = [
    (1, "service_modes", "service-rzqs-b", "Modos de servicio de Sky Air serie B", "Funcionamiento de emergencia, recogida de refrigerante y descongelación forzada.", ["DAI-00001", "DAI-00002", "DAI-00003"]),
    (2, "configuration", "configuration-rzqs-b", "Configuración de placa en Sky Air serie B", "Elementos y funciones de la placa que no deben generalizarse a otras familias.", ["DAI-00004", "DAI-00005"]),
    (3, "drainage_overflow", "cassette-drainage", "Drenaje en cassette FCQ/FFQ", "Arquitectura documentada de bomba de drenaje y flotador.", ["DAI-00006"]),
    (4, "system_architecture", "multisplit-architecture", "Arquitectura Multi-Split 2MXL/3MXL", "Referencia de una familia Multi-Split que debe mantenerse separada de otras series.", ["DAI-00009"]),
    (5, "diagnostic_access", "wireless-error-query", "Consulta de códigos desde mando inalámbrico", "Método disponible para la familia residencial R32 documentada.", ["DAI-00010"]),
    (6, "configuration", "modern-skyair-board", "Identificación de placa A1P/HAP", "Criterios reconocibles de placa, pulsadores, DIP y puentes.", ["DAI-00011"]),
    (7, "errors", "vrviv-codes", "Tabla de códigos y subcódigos VRV IV", "Acceso a códigos principales y subcódigos sin seleccionar automáticamente una causa.", ["DAI-00012"]),
    (8, "controllers_buses", "brc-controllers", "Mandos BRC y configuración de control", "Variantes documentales de mandos, historial, ajustes y principal/secundario.", ["DAI-00013", "DAI-00014", "DAI-00015", "DAI-00016"]),
]

PUBLIC_SOURCE_TITLES = {
    "DAI-RZQS-ESIES06-07": "Manual de servicio — Sky Air RZQS serie B",
    "DAI-FCQ-ESIEN05-04": "Manual de servicio — Sky Air interior R-410A",
    "DAI-MXL-SIUS121602E": "Manual de servicio — Multi-Split 2/3MXL-Q",
    "DAI-CTXA-FTXA-OM": "Manual de operación — Residencial R32",
    "DAI-VRVIV-4P370475-1": "Guía de referencia — VRV IV",
    "DAI-SKYAIR-WIR-4D109863A": "Esquema de cableado — Sky Air moderno",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def normalize(value: str) -> str:
    value = "".join(
        char for char in unicodedata.normalize("NFD", str(value or ""))
        if unicodedata.category(char) != "Mn"
    ).upper()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9]+", " ", value)).strip()


def numeric_id(record_id: str) -> int:
    match = re.search(r"(\d+)$", record_id)
    if not match:
        raise ValueError(f"Identificador Daikin no válido: {record_id}")
    return int(match.group(1))


def public_source(record: dict[str, Any], manuals: dict[str, dict[str, Any]]) -> dict[str, Any]:
    manual_id = record.get("manual_id")
    if not manual_id:
        return {
            "title": "Fuente documental del mando pendiente de vincular",
            "document_ref": record["id"],
            "source_url": None,
            "page_start": None,
            "page_end": None,
            "section": "Pendiente de manual y página",
        }
    manual = manuals[manual_id]
    page = record.get("pagina")
    return {
        "title": PUBLIC_SOURCE_TITLES.get(manual_id, manual["titulo"]),
        "document_ref": manual.get("codigo_manual") or manual_id,
        "source_url": None,
        "page_start": page,
        "page_end": page,
        "section": "Referencia Daikin",
    }


def verification_text(record: dict[str, Any]) -> str:
    if record.get("verificacion") == "consolidado":
        return f"Información consolidada en la fuente indicada. Página: {record.get('pagina') or 'documentada'}."
    return (
        "La información procede del paquete Daikin Referencia V1, pero la página exacta del manual "
        "está pendiente de verificación. Debe confirmarse en el manual correspondiente antes de una intervención."
    )


def unit_scope(record: dict[str, Any]) -> str:
    family = record.get("familia_id")
    if family in {"daikin-rzqs-b", "daikin-skyair-moderno", "daikin-vrviv"}:
        return "outdoor"
    if family in {"daikin-fcq-ffq", "daikin-ctxa-ftxa"}:
        return "indoor"
    return "general"


def build_variant(record: dict[str, Any], topic_id: int, manuals: dict[str, dict[str, Any]], families: dict[str, dict[str, Any]]) -> dict[str, Any]:
    family = families.get(record.get("familia_id"))
    recognition = "Referencia o aspecto del mando indicado en el título."
    system_type = "mando / control"
    if family:
        clues = family.get("reconocimiento") or []
        recognition = f"{family['familia']}: " + ", ".join(clues)
        system_type = family["familia"]
    return {
        "id": numeric_id(record["id"]),
        "topic_id": topic_id,
        "title": record["titulo"],
        "recognition": recognition,
        "system_type": system_type,
        "unit_scope": unit_scope(record),
        "refrigerant": None,
        "purpose": "Consultar la variante documental sin convertirla en un diagnóstico automático.",
        "summary": record["contenido"],
        "source_kind": "official",
        "review_status": "reviewed" if record.get("verificacion") == "consolidado" else "pending_review",
        "sort_order": numeric_id(record["id"]),
        "visible": 1,
        "sections": [
            {
                "section_type": "notes",
                "title": "Estado de verificación",
                "body": verification_text(record),
                "collapsed_default": 0,
            },
            {
                "section_type": "scope",
                "title": "Aplicabilidad",
                "body": "No generalizar esta información a otras familias Daikin. " + recognition,
                "collapsed_default": 1,
            },
        ],
        "steps": [],
        "parameters": [],
        "controller": None,
        "monitoring_points": [],
        "media": [],
        "sources": [public_source(record, manuals)],
    }


def build_error(record: dict[str, Any], error_id: int, interpretation_id: int, manuals: dict[str, dict[str, Any]], families: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    code = record["titulo"].strip().upper()
    label = "Fallo del sistema de drenaje en cassette" if code == "A3" else "Condición del sistema de drenaje en cassette"
    family = families.get(record.get("familia_id"), {})
    search_text = normalize(" ".join([code, label, record["contenido"], family.get("familia", ""), "bomba flotador drenaje cassette"]))
    index = {
        "id": error_id,
        "code_display": code,
        "code_normalized": normalize(code).replace(" ", ""),
        "indication_type": "display",
        "unit_scope": "indoor",
        "short_label": label,
        "interpretation_count": 1,
        "search_text": search_text,
    }
    detail = {
        "id": error_id,
        "code_display": code,
        "code_normalized": normalize(code).replace(" ", ""),
        "indication_type": "display",
        "unit_scope": "indoor",
        "short_label": label,
        "aliases": [{"alias_display": code, "alias_normalized": normalize(code).replace(" ", "")}],
        "tags": ["cassette", "drenaje", "bomba", "flotador"],
        "interpretations": [{
            "id": interpretation_id,
            "title": label,
            "description": record["contenido"],
            "source_kind": "official",
            "confidence": "medium",
            "review_status": "pending_review",
            "info_items": [
                {
                    "item_type": "related_element",
                    "title": "Elementos relacionados",
                    "body": "Bomba de drenaje, flotador y sistema de evacuación de la unidad cassette.",
                },
                {
                    "item_type": "observation",
                    "title": "Verificación documental pendiente",
                    "body": verification_text(record),
                },
            ],
            "operational_impacts": [],
            "datasets": [],
            "sources": [public_source(record, manuals)],
        }],
        "media": [],
    }
    return index, detail


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json", type=Path)
    parser.add_argument("output_brand", type=Path)
    args = parser.parse_args()

    package = read_json(args.input_json)
    if package.get("package_id") != "Super_Tecnico_Daikin_Referencia_V1":
        raise ValueError("El paquete no es Super_Tecnico_Daikin_Referencia_V1")

    records = {item["id"]: item for item in package["registros"]}
    manuals = {item["id"]: item for item in package["manuales"]}
    families = {item["id"]: item for item in package["familias"]}
    code_ids = {"DAI-00007", "DAI-00008"}
    expected_ids = {f"DAI-{number:05d}" for number in range(1, 17)}
    if set(records) != expected_ids:
        raise ValueError("El paquete no contiene exactamente los 16 registros esperados")

    output = args.output_brand.resolve()
    if output.exists():
        raise FileExistsError(f"El destino ya existe: {output}")
    web = output / "web"

    category_map = {slug: {"id": cid, "slug": slug, "name": name, "description": description} for cid, slug, name, description in CATEGORIES}
    topic_files: list[dict[str, Any]] = []
    variant_map: dict[str, int] = {}
    navigation_topics: dict[str, list[dict[str, Any]]] = {slug: [] for _, slug, _, _ in CATEGORIES}

    for topic_id, category_slug, slug, title, summary, record_ids in TOPIC_SPECS:
        variants = [build_variant(records[record_id], topic_id, manuals, families) for record_id in record_ids]
        if any(record_id in code_ids for record_id in record_ids):
            raise ValueError("Un código no puede duplicarse como variante")
        topic = {
            "id": topic_id,
            "brand_id": 3,
            "category_id": category_map[category_slug]["id"],
            "slug": slug,
            "title": title,
            "summary": summary,
            "active": 1,
            "category": category_map[category_slug],
            "variants": variants,
        }
        topic_files.append(topic)
        for variant in variants:
            variant_map[str(variant["id"])] = topic_id
        navigation_topics[category_slug].append({
            "id": topic_id,
            "slug": slug,
            "title": title,
            "summary": summary,
            "active": 1,
            "variant_count": len(variants),
        })

    navigation_categories = []
    for sort_order, (category_id, slug, name, description) in enumerate(CATEGORIES, start=1):
        navigation_categories.append({
            "id": category_id,
            "slug": slug,
            "name": name,
            "description": description,
            "sort_order": sort_order * 10,
            "active": 1,
            "topics": navigation_topics[slug],
        })

    error_indexes: list[dict[str, Any]] = []
    error_details: list[dict[str, Any]] = []
    for error_id, record_id in enumerate(sorted(code_ids), start=1):
        index, detail = build_error(records[record_id], error_id, error_id, manuals, families)
        error_indexes.append(index)
        error_details.append(detail)

    search_entries = []
    category_names = {slug: name for _, slug, name, _ in CATEGORIES}
    for topic in topic_files:
        category_slug = topic["category"]["slug"]
        for variant in topic["variants"]:
            search_entries.append({
                "type": "variant",
                "id": variant["id"],
                "topic_id": topic["id"],
                "category_slug": category_slug,
                "category": category_names[category_slug],
                "title": variant["title"],
                "summary": variant["summary"],
                "haystack": normalize(" ".join([
                    variant["title"], variant["summary"], variant["recognition"],
                    category_names[category_slug], " ".join(section["body"] for section in variant["sections"]),
                ])),
            })
    for item, detail in zip(error_indexes, error_details):
        search_entries.append({
            "type": "error",
            "id": item["id"],
            "topic_id": None,
            "category_slug": "errors",
            "category": category_names["errors"],
            "title": f"{item['code_display']} — {item['short_label']}",
            "summary": detail["interpretations"][0]["description"],
            "haystack": item["search_text"],
        })

    source_records = []
    for source_id, manual in enumerate(package["manuales"], start=1):
        source_records.append({
            "id": source_id,
            "title": PUBLIC_SOURCE_TITLES.get(manual["id"], manual["titulo"]),
            "document_ref": manual.get("codigo_manual") or manual["id"],
            "publication_date": None,
            "language": manual.get("idioma"),
            "document_type": "service_manual" if "Manual" in manual["titulo"] else "technical_manual",
            "source_url": None,
            "status": "pending_page_verification",
            "notes": "Referencia oficial incluida en el paquete Daikin. El enlace privado de origen no se publica.",
        })

    coverage_notes = {
        "errors": "A3 y AF de cassette, más referencia general a códigos y subcódigos VRV IV.",
        "diagnostic_access": "Método de consulta desde mando inalámbrico; faltan pasos detallados y páginas verificadas.",
        "service_modes": "Emergencia, Pump Down y descongelación forzada identificados; procedimientos detallados pendientes.",
        "configuration": "Elementos JX5/DS1/BS1, funcionamiento silencioso y placa A1P/HAP.",
        "controllers_buses": "BRC1D, BRC1E, BRC7E830 y principal/secundario; manual y página pendientes en varias variantes.",
        "drainage_overflow": "Arquitectura FCQ/FFQ y códigos A3/AF; secuencia operativa aún pendiente.",
        "system_architecture": "Referencias Multi-Split, Sky Air y VRV separadas por familia.",
    }
    coverage = [{
        "id": index,
        "brand_id": 3,
        "area_slug": slug,
        "area_name": name,
        "equipment_scope": "Daikin — familias documentadas en Referencia V1",
        "coverage_status": "partial",
        "source_count": len(package["manuales"]),
        "notes": coverage_notes[slug],
        "last_reviewed": package["created_at"],
    } for index, (_, slug, name, _) in enumerate(CATEGORIES, start=1)]

    counts = {
        "categories": len(navigation_categories),
        "topics": len(topic_files),
        "variants": len(variant_map),
        "errors": len(error_indexes),
        "search_entries": len(search_entries),
    }
    now = datetime.now(timezone.utc).isoformat()
    brand = {
        "slug": "daikin",
        "name": "Daikin",
        "display_name": "Daikin",
        "enabled": True,
        "web_data": "web",
        "media": "media",
        "publish_media": False,
        "static_site": True,
        "schema_version": "2.2.0",
        "data_version": "1.0.0",
        "exported_at_utc": now,
        "counts": counts,
        "notes": "Referencia V1 de prueba. Quince de dieciséis registros siguen pendientes de verificar página o manual.",
    }
    navigation = {
        "metadata": {
            "schema_name": "Super Tecnico",
            "navigation_model": "brand_category_topic_variant",
            "schema_version": "2.2.0",
            "data_version": "1.0.0",
            "last_update_utc": now,
            "reference_brand": "Daikin",
            "verification_warning": "15 de 16 registros pendientes de página o manual",
        },
        "categories": navigation_categories,
    }

    write_json(output / "brand.json", brand)
    write_json(web / "navigation.json", navigation)
    write_json(web / "variant_map.json", variant_map)
    write_json(web / "search.json", search_entries)
    write_json(web / "coverage.json", coverage)
    write_json(web / "sources.json", source_records)
    write_json(web / "errors" / "index.json", error_indexes)
    for detail in error_details:
        write_json(web / "errors" / "details" / f"{detail['id']}.json", detail)
    for topic in topic_files:
        write_json(web / "topics" / f"{topic['id']}.json", topic)

    print(json.dumps({"brand": "daikin", "counts": counts, "output": str(output)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
