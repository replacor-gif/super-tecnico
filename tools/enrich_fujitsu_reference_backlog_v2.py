#!/usr/bin/env python3
"""Reduce el backlog Fujitsu V2 con EEPROM, E82 y ventilador exterior 2."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from audit_brand_quality import audit_brand, write as write_json
from enrich_fujitsu_indoor_valve_v2 import (
    BRAND,
    DETAILS,
    ORIGIN,
    WEB,
    info_items,
    load,
    normalize,
    refresh_catalogs,
    related_error,
    service_source,
)


VERSION = "2.14.0"

FAN_REF = "ARYG30_54_AOYG30_54_SERVICE"
FAN_TITLE = "Service Instruction — Fujitsu/General ARYG30-54LHTBP / AOYG30-54LBTA"
FAN_URL = (
    "https://www.fujitsuklima.hu/vmfiles/attachments/sm/"
    "FJ_SI_ARYG30-36-45-54LHTBP_AOYG30-36-45-54LBTA.pdf"
)

JII_REF = "AIRSTAGE_JII_SERVICE"
JII_TITLE = "Service Manual — Fujitsu AIRSTAGE J-II Series"
JII_URL = (
    "https://bulclima.com/uploads/fileattachment/files/originals/"
    "Airstage%20J-II%20series%20service%20manual.pdf"
)


def source(
    title: str,
    document_ref: str,
    url: str,
    page_start: str,
    page_end: str | None,
    section: str,
) -> dict[str, Any]:
    return {
        "title": title,
        "document_ref": document_ref,
        "source_url": url,
        "page_start": page_start,
        "page_end": page_end or page_start,
        "section": section,
    }


def fan_source(page_start: str, page_end: str | None, section: str) -> dict[str, Any]:
    return source(FAN_TITLE, FAN_REF, FAN_URL, page_start, page_end, section)


def jii_source(page_start: str, page_end: str | None, section: str) -> dict[str, Any]:
    return source(JII_TITLE, JII_REF, JII_URL, page_start, page_end, section)


def unique_sources(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        key = (
            str(row.get("document_ref") or ""),
            str(row.get("page_start") or ""),
            str(row.get("section") or ""),
        )
        if key not in seen:
            seen.add(key)
            result.append(row)
    return result


def retag_items(rows: list[dict[str, Any]], origin_ref: str) -> list[dict[str, Any]]:
    for row in rows:
        row["origin_ref"] = origin_ref
    return rows


def consolidate_e32() -> None:
    path = DETAILS / "7.json"
    detail = load(path)
    sources = [row for item in detail["interpretations"] for row in item.get("sources") or []]
    interpretation = {
        "id": 7,
        "title": "Información de modelo o acceso EEPROM de la PCB interior",
        "description": (
            "Al alimentar, la PCB interior detecta información de modelo incorrecta "
            "o no puede acceder a su memoria EEPROM."
        ),
        "source_kind": "official",
        "confidence": "high",
        "review_status": "reviewed",
        "info_items": info_items(
            7,
            ["PCB principal interior", "Memoria EEPROM", "Conectores de componentes interiores"],
            [
                "Información de modelo almacenada incorrecta.",
                "Fallo de acceso a la EEPROM.",
                "Ruido eléctrico, armónicos o puesta a tierra deficiente.",
                "Conector flojo o cableado incorrecto.",
                "Cortocircuito, corrosión o fallo de la PCB principal.",
            ],
            [
                "Restablecer alimentación y comprobar si reaparece E32.",
                "Si no reaparece, revisar puesta a tierra y equipos cercanos que generen armónicos.",
                "Si reaparece, cortar alimentación y revisar todos los conectores y el cableado de la unidad interior.",
                "Inspeccionar la PCB en busca de cortocircuitos o corrosión.",
                "Si las comprobaciones no corrigen el síntoma, sustituir la PCB principal interior.",
            ],
            [
                "La EEPROM conserva la información sin alimentación y tiene un número limitado de reescrituras.",
                "La antigua ficha separada de 'información de modelo' era el mismo mecanismo y se ha consolidado para no duplicar resultados.",
            ],
        ),
        "operational_impacts": [],
        "datasets": [],
        "sources": unique_sources(sources + [service_source("03-25", None, "2-9. Indoor unit main PCB error")]),
    }
    detail["short_label"] = "Información de modelo o EEPROM de la PCB interior"
    detail["interpretations"] = [interpretation]
    write_json(path, detail)


def consolidate_e62() -> None:
    path = DETAILS / "15.json"
    detail = load(path)
    sources = [row for item in detail["interpretations"] for row in item.get("sources") or []]
    interpretation = {
        "id": 15,
        "title": "Información de modelo o acceso EEPROM de la PCB exterior",
        "description": (
            "Al alimentar, la PCB exterior detecta información de modelo incorrecta "
            "o no puede acceder a su memoria EEPROM."
        ),
        "source_kind": "official",
        "confidence": "high",
        "review_status": "reviewed",
        "info_items": info_items(
            15,
            ["PCB principal exterior", "Memoria EEPROM", "Conectores del control exterior"],
            [
                "Información de modelo almacenada incorrecta.",
                "Fallo de acceso a la EEPROM.",
                "Ruido eléctrico, armónicos o puesta a tierra deficiente.",
                "Conector flojo o conexión incorrecta.",
                "Cortocircuito, corrosión o fallo de la PCB principal exterior.",
            ],
            [
                "Restablecer alimentación y comprobar si reaparece E62.",
                "Si no reaparece, revisar tierra y fuentes próximas de armónicos.",
                "Si reaparece, cortar alimentación y revisar conectores y cableado de la unidad exterior.",
                "Inspeccionar la PCB en busca de cortocircuitos o corrosión.",
                "Si las comprobaciones no corrigen el síntoma, sustituir la PCB principal exterior y restaurar los ajustes que exija esa familia.",
            ],
            [
                "Una tabla antigua denomina E62 de forma genérica como modelo o comunicación. Si el display aporta decimal, consultar E62.3, E62.6 o E62.8 antes de aplicar este flujo.",
                "La página 03-40 contiene un encabezado interno incoherente, pero identifica como actuador la PCB principal exterior; no se asigna un conector concreto sin esquema.",
            ],
        ),
        "operational_impacts": [],
        "datasets": [],
        "related_errors": [related_error(error_id) for error_id in (70, 71, 72)],
        "routing_note": "Solo use los subcódigos VRF relacionados cuando el display muestre el decimal; el E62 simple conserva su propio flujo de modelo/EEPROM.",
        "sources": unique_sources(sources + [service_source("03-40", None, "2-24. Outdoor unit model information error")]),
    }
    detail["short_label"] = "Información de modelo o EEPROM de la PCB exterior"
    detail["interpretations"] = [interpretation]
    write_json(path, detail)


THERMISTOR_B = [
    (-10, 27.8), (-5, 21.0), (0, 16.1), (5, 12.4), (10, 9.6),
    (15, 7.6), (20, 6.0), (25, 4.8), (30, 3.8), (40, 2.5),
    (50, 1.7), (60, 1.2),
]


def thermistor_b_dataset() -> dict[str, Any]:
    return {
        "id": 3070,
        "name": "Termistor B J-II — sonda de entrada de gas del subenfriador",
        "dataset_type": "sensor_curve",
        "variable_name": "Temperatura",
        "variable_unit": "°C",
        "value_name": "Resistencia",
        "value_unit": "kΩ",
        "tolerance_text": None,
        "source_kind": "official",
        "calculation_method": None,
        "review_status": "reviewed",
        "notes": "La tabla identifica TH8 de entrada de gas del subenfriador como Termistor B en esta familia J-II.",
        "visible": 1,
        "points": [
            {
                "variable_value": temperature,
                "value_min": None,
                "value_nominal": resistance,
                "value_max": None,
                "value_text": None,
                "sort_order": order,
                "notes": None,
            }
            for order, (temperature, resistance) in enumerate(THERMISTOR_B)
        ],
        "sources": [jii_source("04-105", None, "Service Parts Information 16 — Thermistor")],
        "origin_ref": JII_REF,
    }


def add_e821_and_group_e82() -> None:
    detail = {
        "id": 117,
        "code_display": "E: 82.1",
        "code_normalized": "E821",
        "indication_type": "display",
        "unit_scope": "outdoor",
        "short_label": "Sonda de entrada de gas del subenfriador",
        "aliases": [
            {"alias_display": "82.1", "alias_normalized": "821"},
            {"alias_display": "E82.1", "alias_normalized": "E821"},
            {"alias_display": "TH8", "alias_normalized": "TH8"},
        ],
        "tags": ["subenfriador", "TH8", "CN142"],
        "interpretations": [{
            "id": 153,
            "title": "Sonda de entrada de gas del subenfriador abierta o en corto",
            "description": "La PCB detecta circuito abierto o cortocircuito en la sonda TH8 de entrada de gas del subenfriador.",
            "source_kind": "official",
            "confidence": "high",
            "review_status": "reviewed",
            "info_items": retag_items(info_items(
                153,
                ["Sonda TH8", "Conector CN142 pines 5–6", "PCB principal exterior"],
                [
                    "Conector suelto o cable abierto.",
                    "Sonda abierta, en cortocircuito o fuera de curva.",
                    "Circuito de lectura de la PCB principal defectuoso.",
                ],
                [
                    "Cortar alimentación y revisar conexión/continuidad en CN142 pines 5–6.",
                    "Desconectar la sonda y comparar su resistencia con la curva Termistor B.",
                    "Con las precauciones eléctricas necesarias y la sonda desconectada, comprobar 5,0 V CC en CN142 pines 5–6.",
                    "Si no aparece la referencia de 5 V, continuar con la PCB principal y restaurar sus ajustes si se sustituye.",
                ],
                ["Los pines y la curva pertenecen a la familia J-II documentada; confirmar serigrafía antes de aplicarlos a otra placa."],
            ), JII_REF),
            "operational_impacts": [],
            "datasets": [thermistor_b_dataset()],
            "sources": [
                jii_source("04-37", None, "Trouble shooting 27 — E82.1"),
                jii_source("04-105", None, "Service Parts Information 16 — Thermistor"),
            ],
        }],
        "media": [],
    }
    write_json(DETAILS / "117.json", detail)

    path = DETAILS / "46.json"
    grouped = load(path)
    interpretation = grouped["interpretations"][0]
    interpretation["entry_role"] = "grouping_reference"
    interpretation["routing_note"] = (
        "E82 no permite saber qué sonda del subenfriador ha fallado. Abra E82.1 para entrada de gas "
        "o E82.2 para salida de gas según el subcódigo mostrado."
    )
    interpretation["related_errors"] = [related_error(117), related_error(86)]
    interpretation["sources"] = unique_sources(
        interpretation.get("sources") or []
        + [jii_source("04-37", "04-38", "Trouble shooting 27-28 — E82.1/E82.2")]
    )
    write_json(path, grouped)


def fan_voltage_dataset() -> dict[str, Any]:
    return {
        "id": 3080,
        "name": "Salida de la PCB al ventilador exterior 2 — CN802",
        "dataset_type": "technical_values",
        "variable_name": "Conductores",
        "variable_unit": None,
        "value_name": "Tensión CC",
        "value_unit": "V CC",
        "tolerance_text": "Valores documentados para la familia 45/54 con ventilador inferior.",
        "source_kind": "official",
        "calculation_method": None,
        "review_status": "reviewed",
        "notes": "Medir en el lado de la PCB y confirmar CN802, colores y arquitectura antes de aplicar el dato.",
        "visible": 1,
        "points": [
            {"variable_value": "Rojo–Negro", "value_min": 280.0, "value_nominal": None, "value_max": 373.0, "value_text": None, "sort_order": 0, "notes": "Bus de potencia del motor."},
            {"variable_value": "Blanco–Negro", "value_min": 13.5, "value_nominal": 15.0, "value_max": 16.5, "value_text": None, "sort_order": 1, "notes": "15 ± 1,5 V CC."},
        ],
        "sources": [fan_source("02-33", None, "Trouble shooting 31 — Outdoor fan motor 2")],
        "origin_ref": FAN_REF,
    }


def enrich_e98() -> None:
    path = DETAILS / "48.json"
    detail = load(path)
    interpretation = detail["interpretations"][0]
    interpretation.update({
        "title": "Fallo del segundo ventilador exterior",
        "description": (
            "En la familia de gran potencia con dos ventiladores, el ventilador inferior no alcanza 100 rpm "
            "después de los intentos de arranque."
        ),
        "source_kind": "official",
        "confidence": "high",
        "review_status": "reviewed",
        "info_items": retag_items(info_items(
            75,
            ["Ventilador exterior 2 (inferior)", "Motor DC", "Conector CN802", "PCB principal exterior"],
            [
                "Ventilador atrapado, desprendido o rodamiento/motor bloqueado.",
                "Protección del motor por temperatura ambiente elevada.",
                "Motor del ventilador exterior 2 defectuoso.",
                "Salida o circuito de detección de la PCB principal defectuoso.",
            ],
            [
                "Con la alimentación cortada, girar el ventilador a mano y comprobar bloqueo, roce o rodamiento.",
                "Comprobar si existe una fuente de calor excesiva alrededor del motor; dejar enfriar y repetir la prueba.",
                "Aplicar la comprobación específica del motor exterior; el manual de esta familia dirige a sustituir motor y PCB si el motor es anormal.",
                "Con las protecciones eléctricas necesarias, medir en el lado de la PCB: CN802 rojo–negro 280–373 V CC y blanco–negro 15 ± 1,5 V CC.",
                "Si las tensiones no son correctas, continuar con la PCB principal.",
            ],
            [
                "La detección detiene el motor si no llega a 100 rpm en 20 s; tras reinicios, tres repeticiones en 60 s paran compresor y ventilador y cinco conducen a parada permanente.",
                "CN802, colores y valores corresponden a la familia 45/54 con ventilador 2 inferior; no extrapolar a una exterior de un solo ventilador.",
            ],
        ), FAN_REF),
        "operational_impacts": [{
            "id": 7501,
            "stop_level": "permanent_stop",
            "summary": "Cinco repeticiones de la secuencia de fallo conducen a parada permanente de compresor y ventilador.",
            "affected_scope": "Unidad exterior y sistema asociado",
            "unaffected_scope": None,
            "restart_behavior": "Antes del bloqueo permanente existen reintentos; corregir la causa y restablecer según el procedimiento de la familia.",
            "degraded_behavior": "A las tres repeticiones consecutivas dentro de 60 s se detienen compresor y ventilador como protección.",
            "notes": None,
            "review_status": "reviewed",
        }],
        "datasets": [fan_voltage_dataset()],
        "sources": unique_sources(
            interpretation.get("sources") or []
            + [fan_source("02-33", None, "Trouble shooting 31 — Outdoor fan motor 2")]
        ),
    })
    detail["short_label"] = "Fallo del segundo ventilador exterior"
    write_json(path, detail)


def component_topic() -> dict[str, Any]:
    return {
        "id": 35,
        "brand_id": 2,
        "category_id": 9,
        "slug": "subcooler-sensors-second-outdoor-fan",
        "title": "Subenfriador y segundo ventilador exterior",
        "summary": "Comprobaciones directas de las sondas E82 y del ventilador inferior E98.",
        "active": 1,
        "category": {"id": 9, "slug": "component_checks", "name": "Comprobación de componentes"},
        "variants": [
            {
                "id": 59,
                "topic_id": 35,
                "title": "Comprobar el segundo ventilador exterior",
                "recognition": "Exterior de gran potencia con dos ventiladores; el segundo es el inferior y usa CN802 en la familia documentada.",
                "system_type": "conductos / alta potencia",
                "unit_scope": "outdoor",
                "refrigerant": "R410A",
                "purpose": "Separar bloqueo mecánico, temperatura, motor y PCB en E98.",
                "summary": "Incluye secuencia de reintentos, parada permanente y tensiones de salida de CN802.",
                "source_kind": "official",
                "review_status": "reviewed",
                "sort_order": 10,
                "visible": 1,
                "sections": [
                    {"section_type": "electrical", "title": "Valores de CN802", "body": "Rojo–negro: 280–373 V CC. Blanco–negro: 15 ± 1,5 V CC. Confirmar placa y colores antes de medir.", "collapsed_default": 0},
                    {"section_type": "behavior", "title": "Cómo llega al bloqueo", "body": "No alcanzar 100 rpm en 20 s provoca parada y reintento. Tres repeticiones en 60 s paran compresor/ventilador; cinco provocan parada permanente.", "collapsed_default": 0},
                ],
                "steps": [
                    {"phase": "safety", "step_no": 1, "instruction": "Cortar alimentación y descargar la etapa de potencia antes de manipular motor o CN802.", "expected_result": None, "warning_level": "danger"},
                    {"phase": "check", "step_no": 2, "instruction": "Girar el ventilador a mano y revisar roce, bloqueo, rodamiento y fijación.", "expected_result": "Giro libre y uniforme.", "warning_level": "warning"},
                    {"phase": "check", "step_no": 3, "instruction": "Descartar calor excesivo alrededor del motor y dejar enfriar antes de repetir.", "expected_result": "Temperatura ambiente dentro del rango de la unidad.", "warning_level": "warning"},
                    {"phase": "check", "step_no": 4, "instruction": "Comprobar el motor según su procedimiento específico.", "expected_result": "Motor y cableado correctos.", "warning_level": "danger"},
                    {"phase": "check", "step_no": 5, "instruction": "Medir las salidas documentadas en CN802 del lado de la PCB.", "expected_result": "280–373 V CC y 15 ± 1,5 V CC.", "warning_level": "danger"},
                ],
                "parameters": [], "controller": None, "monitoring_points": [], "media": [],
                "sources": [fan_source("02-33", None, "Trouble shooting 31 — Outdoor fan motor 2")],
            },
            {
                "id": 60,
                "topic_id": 35,
                "title": "Comprobar sondas de entrada y salida del subenfriador",
                "recognition": "Exterior VRF con subcódigos E82.1/E82.2 y conector CN142.",
                "system_type": "VRF",
                "unit_scope": "outdoor",
                "refrigerant": "R410A",
                "purpose": "Identificar la NTC exacta y separar sonda, cable y PCB.",
                "summary": "E82.1 usa entrada de gas TH8; E82.2 usa salida de gas TH9. Ambas se comprueban por resistencia y referencia de 5 V.",
                "source_kind": "official",
                "review_status": "reviewed",
                "sort_order": 20,
                "visible": 1,
                "sections": [
                    {"section_type": "comparison", "title": "E82.1 — entrada", "body": "TH8, CN142 pines 5–6, aproximadamente 5,0 V CC con la sonda desconectada.", "collapsed_default": 0},
                    {"section_type": "comparison", "title": "E82.2 — salida", "body": "TH9. La ficha específica contiene sus pines y curva de la familia correspondiente.", "collapsed_default": 0},
                    {"section_type": "curve", "title": "Punto útil de TH8", "body": "Curva Termistor B J-II: 4,8 kΩ a 25 °C. La ficha E82.1 contiene la tabla completa de -10 a 60 °C.", "collapsed_default": 1},
                ],
                "steps": [
                    {"phase": "safety", "step_no": 1, "instruction": "Cortar alimentación antes de desconectar CN142.", "expected_result": None, "warning_level": "danger"},
                    {"phase": "check", "step_no": 2, "instruction": "Leer el decimal del código para decidir entrada E82.1 o salida E82.2.", "expected_result": "Sonda identificada sin intercambiarlas.", "warning_level": "warning"},
                    {"phase": "check", "step_no": 3, "instruction": "Revisar conector y continuidad del cable de la sonda seleccionada.", "expected_result": "Sin circuito abierto ni falso contacto.", "warning_level": "warning"},
                    {"phase": "check", "step_no": 4, "instruction": "Medir la NTC desconectada y compararla con su curva oficial.", "expected_result": "Resistencia coherente con la temperatura real.", "warning_level": "warning"},
                    {"phase": "check", "step_no": 5, "instruction": "Comprobar la referencia de 5,0 V en los pines documentados de la placa correspondiente.", "expected_result": "Aproximadamente 5,0 V CC.", "warning_level": "danger"},
                ],
                "parameters": [], "controller": None, "monitoring_points": [], "media": [],
                "sources": [
                    jii_source("04-37", "04-38", "Trouble shooting 27-28 — E82.1/E82.2"),
                    jii_source("04-105", None, "Service Parts Information 16 — Thermistor"),
                ],
            },
        ],
    }


def refresh_search() -> tuple[int, int]:
    error_count, _ = refresh_catalogs()
    search = [row for row in load(WEB / "search.json") if int(row.get("topic_id") or 0) != 35]
    topic = load(WEB / "topics" / "35.json")
    for item in topic["variants"]:
        parts = [topic["title"], topic["summary"], item["title"], item["recognition"], item["purpose"], item["summary"]]
        parts.extend(section.get("title") or "" for section in item.get("sections") or [])
        parts.extend(section.get("body") or "" for section in item.get("sections") or [])
        parts.extend(row.get("instruction") or "" for row in item.get("steps") or [])
        parts.extend(row.get("expected_result") or "" for row in item.get("steps") or [])
        search.append({
            "type": "technical",
            "id": int(item["id"]),
            "topic_id": 35,
            "category_slug": "component_checks",
            "category": "Comprobación de componentes",
            "title": item["title"],
            "summary": item["summary"],
            "haystack": normalize(" ".join(parts)),
        })
    write_json(WEB / "search.json", search)
    return error_count, len(search)


def update_metadata(error_count: int, search_count: int) -> None:
    navigation_path = WEB / "navigation.json"
    navigation = load(navigation_path)
    navigation["metadata"].update({
        "data_version": VERSION,
        "latest_phase": "Fujitsu V2 — EEPROM, subenfriador y ventilador exterior 2",
        "last_processed_manual": FAN_REF,
        "technical_library_review": "E32/E62 consolidados; E82 enlaza E82.1/E82.2; E98 desarrollado con CN802 y bloqueo.",
        "last_update_utc": "2026-07-16T18:00:00Z",
    })
    topic = load(WEB / "topics" / "35.json")
    category = next(row for row in navigation["categories"] if int(row["id"]) == 9)
    category["topics"] = [row for row in category.get("topics") or [] if int(row["id"]) != 35]
    category["topics"].append({
        "id": 35, "slug": topic["slug"], "title": topic["title"], "summary": topic["summary"],
        "active": 1, "variant_count": len(topic["variants"]),
    })
    category["topics"].sort(key=lambda row: int(row["id"]))
    write_json(navigation_path, navigation)

    variant_map_path = WEB / "variant_map.json"
    variant_map = load(variant_map_path)
    variant_map.update({"59": 35, "60": 35})
    write_json(variant_map_path, variant_map)

    sources_path = WEB / "sources.json"
    sources = [row for row in load(sources_path) if row.get("document_ref") not in (FAN_REF, JII_REF)]
    sources.extend([
        {
            "id": 19,
            "title": FAN_TITLE,
            "document_ref": FAN_REF,
            "publication_date": "2015-11-25",
            "language": "en",
            "document_type": "service_manual",
            "source_url": FAN_URL,
            "status": "reviewed",
            "notes": "Manual de servicio del fabricante para conductos 30–54. Se resume E98 en 02-33; no se publican páginas ni imágenes.",
        },
        {
            "id": 20,
            "title": JII_TITLE,
            "document_ref": JII_REF,
            "publication_date": "2011-11-07",
            "language": "en",
            "document_type": "service_manual",
            "source_url": JII_URL,
            "status": "reviewed",
            "notes": "Manual de servicio del fabricante. Se resumen E82.1/E82.2 y la curva TH8/TH9; no se publican páginas ni imágenes.",
        },
    ])
    write_json(sources_path, sources)

    coverage_path = WEB / "coverage.json"
    coverage = load(coverage_path)
    for row in coverage:
        row["source_count"] = len(sources)
        if row.get("area_slug") == "errors":
            row["notes"] = "E32/E62 se consolidan sin duplicados; E82 conduce a sus dos sondas y E98 incluye secuencia, tensiones y efecto operativo. Los huecos restantes siguen visibles."
        elif row.get("area_slug") == "component_checks":
            row["notes"] = "Incluye ahora segundo ventilador exterior y sondas del subenfriador, además de compuertas, válvulas, sensor de fuga y rejilla."
    write_json(coverage_path, coverage)

    config_path = BRAND / "brand.json"
    config = load(config_path)
    config["data_version"] = VERSION
    config["counts"] = {
        "categories": len(navigation["categories"]),
        "topics": len(list((WEB / "topics").glob("*.json"))),
        "variants": sum(len(load(path).get("variants") or []) for path in (WEB / "topics").glob("*.json")),
        "errors": error_count,
        "search_entries": search_count,
    }
    config["notes"] = "Fujitsu V2.14: E32/E62 consolidados, E82.1/E82.2 y E98 con valores y bloqueo documentados."
    write_json(config_path, config)


def main() -> int:
    consolidate_e32()
    consolidate_e62()
    add_e821_and_group_e82()
    enrich_e98()
    write_json(WEB / "topics" / "35.json", component_topic())
    error_count, search_count = refresh_search()
    update_metadata(error_count, search_count)
    report = audit_brand(BRAND)
    write_json(WEB / "quality.json", report)
    print(json.dumps({
        "version": VERSION,
        "errors": error_count,
        "search_entries": search_count,
        "interpretations": report["errors"]["interpretations"],
        "technical_interpretations": report["errors"]["technical_interpretations"],
        "statuses": report["errors"]["status_counts"],
        "topics": load(BRAND / "brand.json")["counts"]["topics"],
        "variants": load(BRAND / "brand.json")["counts"]["variants"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
