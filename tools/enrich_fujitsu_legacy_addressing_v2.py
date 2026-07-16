#!/usr/bin/env python3
"""Desarrolla E21/E24/E27 y la programación simultánea Fujitsu."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from audit_brand_quality import audit_brand, write as write_json
from enrich_fujitsu_vrf_v2 import normalize, refresh_search


ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "data" / "brands" / "fujitsu-general"
WEB = BRAND / "web"
DETAILS = WEB / "errors" / "details"
ORIGIN = "FUJITSU_V2_LEGACY_ADDRESSING"
DOCUMENT_REF = "9374318445-06"
SOURCE_URL = "https://webstore.uk.fujitsu-general.com/product/attachment/ABYG14LVTA/installation%20manual.pdf"
TOPIC_ID = 31
VARIANT_ID = 48


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def source(page_start: str = "En-12", page_end: str = "En-12", section: str = "9.4 Group control") -> dict[str, Any]:
    return {
        "title": "Installation Manual — Fujitsu/General ABYG14LVTA",
        "document_ref": DOCUMENT_REF,
        "source_url": SOURCE_URL,
        "page_start": page_start,
        "page_end": page_end,
        "section": section,
    }


RC_DIP = [
    ("00", "OFF / OFF / OFF / OFF"),
    ("01", "ON / OFF / OFF / OFF"),
    ("02", "OFF / ON / OFF / OFF"),
    ("03", "ON / ON / OFF / OFF"),
    ("04", "OFF / OFF / ON / OFF"),
    ("05", "ON / OFF / ON / OFF"),
    ("06", "OFF / ON / ON / OFF"),
    ("07", "ON / ON / ON / OFF"),
    ("08", "OFF / OFF / OFF / ON"),
    ("09", "ON / OFF / OFF / ON"),
    ("10", "OFF / ON / OFF / ON"),
    ("11", "ON / ON / OFF / ON"),
    ("12", "OFF / OFF / ON / ON"),
    ("13", "ON / OFF / ON / ON"),
    ("14", "OFF / ON / ON / ON"),
    ("15", "ON / ON / ON / ON"),
]


def dataset(error_id: int, name: str, variable_name: str, value_name: str, points: list[dict[str, Any]], notes: str) -> dict[str, Any]:
    return {
        "id": 6000 + error_id,
        "name": name,
        "dataset_type": "technical_values",
        "variable_name": variable_name,
        "variable_unit": None,
        "value_name": value_name,
        "value_unit": None,
        "tolerance_text": None,
        "source_kind": "official",
        "calculation_method": None,
        "review_status": "reviewed",
        "notes": notes,
        "visible": 1,
        "points": points,
        "sources": [source()],
        "origin_ref": ORIGIN,
    }


ENRICHMENTS: dict[int, dict[str, Any]] = {
    37: {
        "interpretation_id": 43,
        "description": "En un sistema simultáneo, el número de unidad o la dirección del circuito frigorífico no coincide con la programación del grupo.",
        "related": ["Dirección R.C. 00-15 por DIP de la interior", "Función 02: dirección del circuito frigorífico", "Cableado de grupo simultáneo"],
        "causes": [
            "Direcciones R.C. repetidas, no consecutivas o no acordes con el cableado del grupo.",
            "Las interiores conectadas a una misma exterior no comparten el mismo valor de la función 02.",
            "La dirección del circuito frigorífico no coincide con la asignada al conjunto.",
            "La programación se realizó sin respetar el orden de alimentación o no se reiniciaron todas las interiores.",
        ],
        "checks": [
            "Comprobar que las direcciones R.C. están asignadas secuencialmente desde 00 y que no existen duplicados.",
            "Revisar los cuatro DIP de cada interior contra la tabla 00-15.",
            "Programar con función 02 el mismo número de circuito frigorífico en todas las interiores conectadas a la misma exterior.",
            "Al configurar un simultáneo, alimentar todas las interiores y energizar la de dirección R.C. 00 en último lugar, dentro de 1 minuto.",
            "Después de terminar, cortar alimentación de todas las interiores y volver a alimentarlas. Si reaparece E21, repetir la programación desde el inicio.",
        ],
        "behavior": ["El manual agrupa E21, E22, E24 y E27 como posibles errores de configuración y ordena repetir el ajuste desde el mando."],
        "dataset": dataset(37, "Dirección de circuito frigorífico", "Función", "Valores admitidos", [{"variable_value": "02", "value_min": None, "value_nominal": None, "value_max": None, "value_text": "00 a 15; mismo valor para todas las interiores de una exterior", "sort_order": 0, "notes": "Valor de fábrica 00"}], "Programación documentada para sistemas simultáneos."),
    },
    38: {
        "interpretation_id": 45,
        "description": "El número de unidades reconocido no coincide con las interiores secundarias o con la estructura de grupo programada.",
        "related": ["Cantidad de interiores conectadas", "Direcciones R.C. secuenciales", "Grupo simultáneo o flexible"],
        "causes": [
            "Falta una dirección R.C., existe una dirección repetida o la secuencia no empieza en 00.",
            "Una interior secundaria no está alimentada o no comunica durante el reconocimiento del grupo.",
            "La topología real y la programación de simultáneo no coinciden.",
            "Los valores de circuito frigorífico o principal/secundaria no son coherentes entre interiores.",
        ],
        "checks": [
            "Contar las interiores realmente conectadas y compararlas con las direcciones R.C. programadas.",
            "Verificar alimentación, cableado de bus y continuidad hacia cada secundaria.",
            "Confirmar direcciones R.C. consecutivas y sin duplicados mediante los cuatro DIP.",
            "Revisar que todas las interiores de una misma exterior usan el mismo valor de función 02.",
            "Comprobar función 51: una sola principal 00 y las demás secundarias 01; después reiniciar todas las interiores.",
        ],
        "behavior": ["El manual no publica el umbral interno de detección; indica repetir la configuración de mando cuando aparece E24."],
        "dataset": dataset(38, "Direcciones R.C. de interiores", "Dirección", "DIP 1 / 2 / 3 / 4", [{"variable_value": address, "value_min": None, "value_nominal": None, "value_max": None, "value_text": switches, "sort_order": index, "notes": None} for index, (address, switches) in enumerate(RC_DIP)], "Las direcciones deben asignarse secuencialmente."),
    },
    39: {
        "interpretation_id": 46,
        "description": "La selección de unidad principal y secundarias del simultáneo es inexistente, duplicada o no corresponde al cableado.",
        "related": ["Función 51 de las interiores", "Interior conectada por transmisión a la exterior", "Configuración principal/secundaria del mando"],
        "causes": [
            "Más de una interior está configurada como principal o ninguna lo está.",
            "La interior seleccionada como principal no es la conectada a la exterior mediante el cable de transmisión.",
            "Una secundaria mantiene el valor 00 de fábrica en lugar de 01.",
            "La configuración del mando principal/secundario se confunde con el rol principal/secundaria de las interiores.",
        ],
        "checks": [
            "Identificar la interior conectada a la exterior por el cable de transmisión y programarla como principal: función 51, valor 00.",
            "Programar todas las demás interiores del simultáneo como secundarias: función 51, valor 01.",
            "No confundir función 51 de las interiores con DIP SW1-2 de dos mandos: en los mandos, principal es OFF y secundario ON.",
            "Comprobar la estructura y las direcciones R.C. del grupo antes de guardar.",
            "Cortar alimentación de todas las interiores y volver a alimentarlas; si aparece E27, repetir la programación completa.",
        ],
        "behavior": ["El manual indica que E27 puede aparecer tras una configuración incorrecta y que debe repetirse el ajuste desde el mando."],
        "dataset": dataset(39, "Principal y secundarias de interior", "Función", "Valor", [{"variable_value": "51 — principal", "value_min": None, "value_nominal": None, "value_max": None, "value_text": "00", "sort_order": 0, "notes": "Interior conectada a la exterior por transmisión"}, {"variable_value": "51 — secundaria", "value_min": None, "value_nominal": None, "value_max": None, "value_text": "01", "sort_order": 1, "notes": "Resto de interiores del simultáneo"}], "No confundir con el DIP de principal/secundario de dos mandos."),
    },
}


def enrich_errors() -> None:
    for error_id, enrichment in ENRICHMENTS.items():
        path = DETAILS / f"{error_id}.json"
        detail = load(path)
        interpretation = next(row for row in detail["interpretations"] if int(row["id"]) == enrichment["interpretation_id"])
        interpretation["description"] = enrichment["description"]
        interpretation["info_items"] = [row for row in interpretation.get("info_items") or [] if row.get("origin_ref") != ORIGIN]
        order = 0
        for item_type, key in (("related_element", "related"), ("cause", "causes"), ("check", "checks"), ("machine_behavior", "behavior")):
            for body in enrichment[key]:
                interpretation["info_items"].append({
                    "id": 50000 + error_id * 100 + order,
                    "item_type": item_type,
                    "title": None,
                    "body": body,
                    "sort_order": order,
                    "review_status": "reviewed",
                    "origin_ref": ORIGIN,
                })
                order += 1
        interpretation["datasets"] = [row for row in interpretation.get("datasets") or [] if row.get("origin_ref") != ORIGIN] + [enrichment["dataset"]]
        interpretation["sources"] = [row for row in interpretation.get("sources") or [] if row.get("document_ref") != DOCUMENT_REF] + [source()]
        write_json(path, detail)


def parameter(parameter_id: int, code: str, name: str, description: str, factory: str | None, options: list[tuple[str, str, str | None]], warning: str | None = None) -> dict[str, Any]:
    return {
        "id": parameter_id,
        "variant_id": VARIANT_ID,
        "parameter_code": code,
        "name": name,
        "description": description,
        "factory_value": factory,
        "dependencies": None,
        "warnings": warning,
        "sort_order": parameter_id - 100,
        "visible": 1,
        "options": [
            {"option_value": value, "option_label": label, "effect": effect, "is_factory": int(factory == value)}
            for value, label, effect in options
        ],
    }


def topic() -> dict[str, Any]:
    rc_options = [(address, switches, "Dirección R.C. mediante DIP 1-4") for address, switches in RC_DIP]
    parameters = [
        parameter(101, "DIP R.C.", "Dirección de unidad interior", "Direcciones 00-15; deben ser secuenciales.", "00", rc_options),
        parameter(102, "02", "Dirección de circuito frigorífico", "Mismo valor para todas las interiores conectadas a una exterior.", "00", [(f"{value:02d}", f"Circuito {value:02d}", None) for value in range(16)]),
        parameter(103, "51", "Rol de la interior", "La conectada por transmisión a la exterior es principal.", "00", [("00", "Principal", "Una por grupo"), ("01", "Secundaria", "Resto de interiores del simultáneo")]),
        parameter(104, "DIP SW1-2", "Rol cuando hay dos mandos", "Ajuste del mando, distinto de la función 51 de las interiores.", "OFF", [("OFF", "Mando principal", None), ("ON", "Mando secundario", "Sin temporizador ni autodiagnóstico")], "No usar este DIP para sustituir la función 51 de las interiores."),
    ]
    sections = [
        {"section_type": "recognition", "title": "Cómo reconocer esta variante", "body": "Grupo con pares estándar y simultáneos twin/triple; interiores con cuatro DIP para dirección R.C. y programación de funciones 02 y 51 desde el mando.", "collapsed_default": 0},
        {"section_type": "purpose", "title": "Qué se configura", "body": "Se separan tres datos: dirección R.C. individual, dirección de circuito frigorífico común y rol principal/secundaria de cada interior.", "collapsed_default": 0},
        {"section_type": "important", "title": "Reglas que no deben mezclarse", "body": "Las direcciones R.C. deben ser secuenciales. La función 02 es común para las interiores de una exterior. La función 51 define interiores principal/secundarias. El DIP SW1-2 solo define principal/secundario cuando existen dos mandos.", "collapsed_default": 0},
        {"section_type": "errors", "title": "Errores relacionados", "body": "Si después de programar aparecen 21, 22, 24 o 27, el fabricante indica que puede existir un ajuste incorrecto y que debe repetirse la configuración desde el mando.", "collapsed_default": 1},
    ]
    steps = [
        {"phase": "prepare", "step_no": 1, "instruction": "Identificar cada interior, la exterior a la que pertenece y cuál está conectada a ella por el cable de transmisión.", "expected_result": "Esquema de grupo definido antes de programar.", "warning_level": "none"},
        {"phase": "address", "step_no": 1, "instruction": "Asignar con los cuatro DIP una dirección R.C. única y secuencial de 00 a 15 a cada interior.", "expected_result": "No existen saltos ni duplicados.", "warning_level": "none"},
        {"phase": "power", "step_no": 1, "instruction": "Al configurar un simultáneo, energizar todas las interiores y conectar la de dirección R.C. 00 en último lugar, dentro de 1 minuto.", "expected_result": "El grupo reconoce correctamente la unidad 00.", "warning_level": "note"},
        {"phase": "configure", "step_no": 1, "instruction": "Programar función 02 con el mismo valor 00-15 en todas las interiores conectadas a una misma exterior.", "expected_result": "Cada grupo comparte una única dirección frigorífica.", "warning_level": "none"},
        {"phase": "configure", "step_no": 2, "instruction": "Programar función 51: valor 00 en la interior conectada por transmisión a la exterior y valor 01 en las restantes.", "expected_result": "Existe una sola principal y las demás son secundarias.", "warning_level": "none"},
        {"phase": "restart", "step_no": 1, "instruction": "Tras guardar, cortar la alimentación de todas las interiores y volver a alimentarlas.", "expected_result": "La nueva configuración queda aplicada.", "warning_level": "warning"},
        {"phase": "verify", "step_no": 1, "instruction": "Si se muestra 21, 22, 24 o 27, revisar tabla, cableado y roles y repetir la programación completa.", "expected_result": "El grupo arranca sin errores de configuración.", "warning_level": "note"},
    ]
    return {
        "id": TOPIC_ID,
        "brand_id": 2,
        "category_id": 3,
        "slug": "simultaneous-multi-addressing",
        "title": "Direcciones y principal/secundarias en simultáneos",
        "summary": "Programación de dirección R.C., circuito frigorífico y roles de interior para grupos twin/triple.",
        "active": 1,
        "category": {"id": 3, "slug": "configuration", "name": "Configuración y programación"},
        "variants": [{
            "id": VARIANT_ID,
            "topic_id": TOPIC_ID,
            "title": "Grupo simultáneo con DIP R.C. y funciones 02/51",
            "recognition": "Interiores con cuatro DIP de dirección R.C. y mando que permite programar funciones 02 y 51.",
            "system_type": "simultáneo twin/triple y control de grupo",
            "unit_scope": "system",
            "refrigerant": None,
            "purpose": "Evitar errores de dirección, cantidad y rol principal/secundaria en grupos simultáneos.",
            "summary": "Direcciones R.C. consecutivas, circuito común por función 02 y una sola interior principal mediante función 51.",
            "source_kind": "official",
            "review_status": "reviewed",
            "sort_order": 0,
            "visible": 1,
            "sections": sections,
            "steps": steps,
            "parameters": parameters,
            "controller": None,
            "monitoring_points": [],
            "media": [],
            "sources": [source("En-11", "En-12", "9.4 Group control")],
        }],
    }


def update_library() -> None:
    topic_data = topic()
    write_json(WEB / "topics" / f"{TOPIC_ID}.json", topic_data)

    navigation_path = WEB / "navigation.json"
    navigation = load(navigation_path)
    metadata = navigation.setdefault("metadata", {})
    metadata["data_version"] = "2.10.0"
    metadata["latest_phase"] = "Fujitsu V2 — direccionamiento simultáneo"
    metadata["last_processed_manual"] = DOCUMENT_REF
    metadata["technical_library_review"] = "Programación de grupos simultáneos y diagnóstico E21/E24/E27."
    category = next(row for row in navigation["categories"] if row.get("slug") == "configuration")
    category["topics"] = [row for row in category.get("topics") or [] if int(row.get("id") or 0) != TOPIC_ID]
    category["topics"].append({"id": TOPIC_ID, "slug": topic_data["slug"], "title": topic_data["title"], "summary": topic_data["summary"], "active": 1, "variant_count": 1})
    write_json(navigation_path, navigation)

    map_path = WEB / "variant_map.json"
    variant_map = load(map_path)
    variant_map[str(VARIANT_ID)] = TOPIC_ID
    write_json(map_path, variant_map)

    sources_path = WEB / "sources.json"
    sources = [row for row in load(sources_path) if row.get("document_ref") != DOCUMENT_REF]
    sources.append({
        "id": 17,
        "title": "Installation Manual — Fujitsu/General ABYG14LVTA",
        "document_ref": DOCUMENT_REF,
        "publication_date": "2018",
        "language": "en",
        "document_type": "installation_manual",
        "source_url": SOURCE_URL,
        "extraction_status": "reviewed",
        "review_status": "reviewed",
        "notes": "Control de grupo, direcciones R.C., funciones 02/51 y errores 21/22/24/27.",
    })
    write_json(sources_path, sources)

    search_path = WEB / "search.json"
    search = [row for row in load(search_path) if not (row.get("type") == "variant" and int(row.get("id") or 0) == VARIANT_ID)]
    variant = topic_data["variants"][0]
    text = [variant["title"], variant["recognition"], variant["purpose"], variant["summary"]]
    text.extend(row.get("body") or "" for row in variant["sections"])
    text.extend(row.get("instruction") or "" for row in variant["steps"])
    for row in variant["parameters"]:
        text.extend([row["parameter_code"], row["name"], row["description"], row.get("warnings") or ""])
        text.extend(f"{option['option_value']} {option['option_label']}" for option in row["options"])
    search.append({"type": "variant", "id": VARIANT_ID, "topic_id": TOPIC_ID, "category_slug": "configuration", "category": "Configuración y programación", "title": variant["title"], "summary": variant["summary"], "haystack": normalize(" ".join(text))})
    write_json(search_path, search)


def main() -> int:
    enrich_errors()
    update_library()

    config_path = BRAND / "brand.json"
    config = load(config_path)
    config["data_version"] = "2.10.0"
    config["counts"] = {"categories": 18, "topics": 31, "variants": 48, "errors": 110, "search_entries": 158}
    config["notes"] = "Fujitsu V2: E21/E24/E27 y programación de grupos simultáneos desarrollados con documentación oficial."
    write_json(config_path, config)

    coverage_path = WEB / "coverage.json"
    coverage = load(coverage_path)
    configuration = next(row for row in coverage if row.get("area_slug") == "configuration")
    configuration["equipment_scope"] = "split, simultáneo, multisplit y VRF"
    configuration["source_count"] = max(int(configuration.get("source_count") or 0), 17)
    configuration["notes"] = "Incluye programación desde mando, PCB exterior, simultáneos con DIP/funciones 02/51 y ajustes VRF."
    write_json(coverage_path, coverage)

    refresh_search()
    report = audit_brand(BRAND)
    write_json(WEB / "quality.json", report)
    print(json.dumps({
        "legacy_addressing_enriched": len(ENRICHMENTS),
        "topics": len(list((WEB / "topics").glob("*.json"))),
        "variants": report["technical_variants"]["entries"],
        "interpretations": report["errors"]["interpretations"],
        "statuses": report["errors"]["status_counts"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
