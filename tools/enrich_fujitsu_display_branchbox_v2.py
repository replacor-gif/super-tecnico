#!/usr/bin/env python3
"""Completa E6A y ED2/J2 con un manual de servicio Hybrid Flex.

La web pública conserva solo resúmenes, valores y referencias. No se incluyen
páginas ni imágenes del manual.
"""

from __future__ import annotations

import json
from typing import Any

from audit_brand_quality import audit_brand, write as write_json
from enrich_fujitsu_indoor_valve_v2 import (
    BRAND,
    DETAILS,
    WEB,
    load,
    normalize,
    refresh_catalogs,
)


VERSION = "2.16.0"
ORIGIN = "AOU48RLXFZ1_HYBRID_FLEX_SERVICE"
MANUAL_TITLE = "Service Instruction — Fujitsu Hybrid Flex AOU48RLXFZ1"
MANUAL_URL = "https://www.master.ca/media/akeneo_connector/asset_files/F/u/Fujitsu_AOU48RLXFZ1_service_instruction_en_CA_5282.pdf"


def source(page_start: str, page_end: str | None, section: str) -> dict[str, Any]:
    return {
        "title": MANUAL_TITLE,
        "document_ref": ORIGIN,
        "source_url": MANUAL_URL,
        "page_start": page_start,
        "page_end": page_end or page_start,
        "section": section,
    }


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


def info_items(
    interpretation_id: int,
    related: list[str],
    causes: list[str],
    checks: list[str],
    behaviors: list[str],
    observations: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    order = 1
    for item_type, bodies in (
        ("related_element", related),
        ("cause", causes),
        ("check", checks),
        ("machine_behavior", behaviors),
        ("observation", observations),
    ):
        for body in bodies:
            rows.append({
                "id": 80000 + interpretation_id * 100 + order,
                "item_type": item_type,
                "title": None,
                "body": body,
                "sort_order": order,
                "review_status": "reviewed",
                "origin_ref": ORIGIN,
            })
            order += 1
    return rows


def e6a_timeout_dataset() -> dict[str, Any]:
    return {
        "id": 3090,
        "name": "Condición de detección E6A.1",
        "dataset_type": "technical_values",
        "variable_name": "Condición",
        "variable_unit": None,
        "value_name": "Tiempo sin recepción",
        "value_unit": "s",
        "tolerance_text": None,
        "source_kind": "official",
        "calculation_method": None,
        "review_status": "reviewed",
        "notes": "Valor de la familia Hybrid Flex documentada: la PCB principal no recibe comunicación de la PCB I/O.",
        "visible": 1,
        "points": [{
            "variable_value": "I/O → PCB principal exterior",
            "value_min": None,
            "value_nominal": 10,
            "value_max": None,
            "value_text": None,
            "sort_order": 0,
            "notes": None,
        }],
        "sources": [source("02-64", None, "Trouble shooting 46 — Display P.C.B. Communication Error")],
        "origin_ref": ORIGIN,
    }


def branch_led_dataset() -> dict[str, Any]:
    points = [
        ("LED401: 1 / 2 / 3 parpadeos", "Caja primaria / secundaria 1 / secundaria 2"),
        ("LED402: 1 parpadeo", "Fallo de acceso EEPROM"),
        ("LED402: 2 parpadeos", "Información de modelo incorrecta"),
        ("LED402: 3 parpadeos", "Comunicación exterior–caja de derivación"),
        ("LED402: 4 parpadeos", "Comunicación entre cajas de derivación"),
        ("LED402: 5 + LED403/404/405", "Comunicación entre caja e interior A/B/C"),
        ("LED402: 6 + LED403/404/405", "Sonda de líquido A/B/C"),
        ("LED402: 7 + LED403/404/405", "Sonda de gas A/B/C"),
        ("LED402: 8 + LED403/404/405", "Control EEV A/B/C"),
        ("LED402: 9 parpadeos", "Comunicación del mando"),
    ]
    return {
        "id": 3100,
        "name": "Lectura de LED de la caja de derivación",
        "dataset_type": "indicator_map",
        "variable_name": "Patrón",
        "variable_unit": None,
        "value_name": "Interpretación",
        "value_unit": None,
        "tolerance_text": "Aplicar solo cuando la caja dispone de LED401–LED405 con esta lógica.",
        "source_kind": "official",
        "calculation_method": None,
        "review_status": "reviewed",
        "notes": "LED403, LED404 y LED405 identifican respectivamente el circuito interior A, B o C cuando LED402 marca 5, 6, 7 u 8.",
        "visible": 1,
        "points": [
            {
                "variable_value": pattern,
                "value_min": None,
                "value_nominal": None,
                "value_max": None,
                "value_text": meaning,
                "sort_order": order,
                "notes": None,
            }
            for order, (pattern, meaning) in enumerate(points)
        ],
        "sources": [source("02-14", "02-15", "2-3-6 Error status for Branch Box Display")],
        "origin_ref": ORIGIN,
    }


def enrich_e6a() -> None:
    path = DETAILS / "43.json"
    detail = load(path)
    interpretation = detail["interpretations"][0]
    interpretation.update({
        "title": "Comunicación entre PCB principal y PCB de display/I/O exterior",
        "description": (
            "En la familia Hybrid Flex documentada, E6A.1 aparece cuando la PCB principal exterior "
            "no recibe comunicación de la PCB I/O durante 10 segundos o más."
        ),
        "source_kind": "official",
        "confidence": "high",
        "review_status": "reviewed",
        "info_items": info_items(
            int(interpretation["id"]),
            ["PCB principal exterior", "PCB de display/I/O exterior", "Cable y conectores entre ambas PCB"],
            [
                "Conector flojo, cable abierto o conexión incorrecta entre PCB principal y PCB I/O.",
                "PCB I/O defectuosa.",
                "PCB principal exterior defectuosa.",
            ],
            [
                "Cortar alimentación y revisar estado de conectores y continuidad del cable entre PCB I/O y PCB principal.",
                "Consultar la indicación de error de la propia PCB I/O.",
                "Si la PCB I/O no muestra error, el flujo oficial dirige a sustituir la PCB I/O.",
                "Si la PCB I/O muestra error, el flujo deja como posibles la PCB I/O o la PCB principal; comprobar ambas antes de sustituir.",
                "Caso específico: si la exterior muestra E6A.1 y las interiores muestran E11.1 o E11.2, el manual dirige a la PCB principal exterior.",
            ],
            ["La detección se produce tras 10 segundos o más sin recibir la comunicación de la PCB I/O."],
            [
                "El nombre histórico 'display PCB' puede corresponder físicamente a una PCB I/O exterior; identificarla por el esquema y la serigrafía de la placa antes de intervenir.",
                "No confundir E6A con un fallo del display o del mando de la unidad interior.",
            ],
        ),
        "operational_impacts": [],
        "datasets": [e6a_timeout_dataset()],
        "sources": unique_sources((interpretation.get("sources") or []) + [
            source("02-64", None, "Trouble shooting 46 — Display P.C.B. Communication Error"),
        ]),
    })
    detail["short_label"] = "Comunicación entre PCB principal y display/I/O exterior"
    detail["aliases"] = [
        {"alias_display": "E6A", "alias_normalized": "E6A"},
        {"alias_display": "E6A.1", "alias_normalized": "E6A1"},
        {"alias_display": "6 parpadeos OPERATION + 10 parpadeos TIMER", "alias_normalized": "6PARPADEOSOPERATION10PARPADEOSTIMER"},
    ]
    detail["tags"] = ["PCB I/O", "PCB principal exterior", "10 segundos"]
    write_json(path, detail)


def enrich_ed2() -> None:
    path = DETAILS / "51.json"
    detail = load(path)
    interpretation = detail["interpretations"][0]
    interpretation.update({
        "title": "Fallo interno o de comunicación de una caja de derivación",
        "description": (
            "ED2 en tablas antiguas y J2/EJ2U en Hybrid Flex identifican la familia de fallos de la caja de derivación. "
            "El diagnóstico preciso se obtiene leyendo LED401–LED405 de la propia caja."
        ),
        "source_kind": "official",
        "confidence": "high",
        "review_status": "reviewed",
        "info_items": info_items(
            int(interpretation["id"]),
            [
                "Caja de derivación primaria o secundaria",
                "PCB controladora de la caja",
                "LED401–LED405",
                "Comunicaciones con exterior, interiores, otras cajas y mando",
                "Sondas de tubería y válvulas de expansión de la caja",
            ],
            [
                "Caja sin alimentación o cantidad de cajas detectada distinta de la memorizada.",
                "Conexión suelta, cable abierto, cortocircuito o cableado cruzado.",
                "Fallo de comunicación con la exterior, una interior, otra caja o el mando.",
                "Acceso EEPROM o información de modelo incorrecta en la PCB de la caja.",
                "Sonda de líquido/gas o EEV del puerto A, B o C defectuosa.",
                "PCB controladora de la caja defectuosa.",
            ],
            [
                "Antes del CHECK RUN, comparar el número de cajas/interiores mostrado por la exterior con el instalado; no iniciar la prueba si no coincide.",
                "Comprobar que todas las cajas tienen alimentación y que los cables hacia las interiores están conectados.",
                "Leer LED401 para identificar caja primaria/secundaria y LED402 para obtener el tipo de fallo; con LED402 en 5–8, LED403/404/405 selecciona el puerto A/B/C.",
                "Para fallos de comunicación, cortar alimentación y revisar terminales, conectores, cable abierto, cortocircuito y cableado cruzado.",
                "Para EEPROM/modelo, resetear y revisar conectores, corrosión, tierra y fuentes de armónicos antes de sustituir la PCB.",
                "Para sondas o EEV, seguir el componente y el conector que indique el patrón de LED; no sustituir la caja completa sin aislar el subfallo.",
                "Después de corregir cableado o sustituir una PCB, restablecer alimentación y repetir CHECK RUN cuando corresponda.",
            ],
            [
                "El mismo J2 se muestra de forma genérica en la interior/exterior; los LED de la caja contienen el subdiagnóstico accionable.",
                "El manual permite diferenciar la caja primaria, secundaria 1 o secundaria 2 y, en ciertos fallos, el puerto interior A, B o C.",
            ],
            [
                "El manual no afirma que todos los J2 detengan siempre todo el sistema. El alcance depende del subfallo y de la caja/puerto identificados; no se deduce una parada global.",
                "La nomenclatura cambia entre generaciones: ED2, J2 y EJ2U deben consultarse como variantes de la misma familia, no como una única causa.",
            ],
        ),
        "operational_impacts": [],
        "datasets": [branch_led_dataset()],
        "sources": unique_sources((interpretation.get("sources") or []) + [
            source("02-14", "02-15", "2-3-6 Error status for Branch Box Display"),
            source("02-16", "02-24", "Trouble shooting 1 and 7 — serial communication / number of boxes"),
            source("02-57", "02-63", "Trouble shooting 40–45 — J2 branch box sub-errors"),
        ]),
    })
    detail["short_label"] = "Fallo de caja de derivación (ED2/J2)"
    detail["aliases"] = [
        {"alias_display": "ED2", "alias_normalized": "ED2"},
        {"alias_display": "J2", "alias_normalized": "J2"},
        {"alias_display": "E.J2.U", "alias_normalized": "EJ2U"},
        {"alias_display": "13 parpadeos OPERATION + 2 parpadeos TIMER", "alias_normalized": "13PARPADEOSOPERATION2PARPADEOSTIMER"},
    ]
    detail["tags"] = ["branch box", "caja derivación", "LED401 LED402 LED403 LED404 LED405", "Hybrid Flex"]
    write_json(path, detail)


def step(
    number: int,
    instruction: str,
    expected: str | None = None,
    level: str = "warning",
) -> dict[str, Any]:
    return {
        "phase": "safety" if number == 1 else "check",
        "step_no": number,
        "instruction": instruction,
        "expected_result": expected,
        "warning_level": level,
    }


def variant(
    variant_id: int,
    topic_id: int,
    title: str,
    recognition: str,
    system_type: str,
    purpose: str,
    summary: str,
    sections: list[dict[str, Any]],
    steps: list[dict[str, Any]],
    pages: list[dict[str, Any]],
    sort_order: int,
) -> dict[str, Any]:
    return {
        "id": variant_id,
        "topic_id": topic_id,
        "title": title,
        "recognition": recognition,
        "system_type": system_type,
        "unit_scope": "outdoor" if topic_id == 37 else "general",
        "refrigerant": "R410A",
        "purpose": purpose,
        "summary": summary,
        "source_kind": "official",
        "review_status": "reviewed",
        "sort_order": sort_order,
        "visible": 1,
        "sections": sections,
        "steps": steps,
        "parameters": [],
        "controller": None,
        "monitoring_points": [],
        "media": [],
        "sources": pages,
    }


def e6a_topic() -> dict[str, Any]:
    return {
        "id": 37,
        "brand_id": 2,
        "category_id": 9,
        "slug": "outdoor-display-io-pcb-communication",
        "title": "Comunicación entre PCB principal y display/I/O exterior",
        "summary": "Diagnóstico E6A.1: cable/conectores, PCB I/O y PCB principal sin confundirlo con el mando interior.",
        "active": 1,
        "category": {"id": 9, "slug": "component_checks", "name": "Comprobación de componentes"},
        "variants": [variant(
            65,
            37,
            "E6A.1 — Comprobar comunicación principal–I/O exterior",
            "Exterior con PCB principal y PCB I/O/display separadas; seis parpadeos OPERATION y diez TIMER o E6A.1 en la exterior.",
            "Hybrid Flex / multisplit",
            "Separar cableado, PCB I/O y PCB principal siguiendo el criterio de la indicación de la propia PCB I/O.",
            "La principal declara el fallo tras 10 s sin recibir la I/O. E11.1/E11.2 simultáneo en interiores cambia el diagnóstico hacia la principal.",
            [
                {"section_type": "detection", "title": "Condición", "body": "La PCB principal exterior no recibe comunicación de la PCB I/O durante 10 segundos o más.", "collapsed_default": 0},
                {"section_type": "routing", "title": "Criterio de separación", "body": "Sin error visible en la I/O: el flujo dirige a la I/O. Con error en la I/O: comprobar I/O y principal. Con E6A.1 exterior y E11.1/E11.2 interior: principal exterior.", "collapsed_default": 0},
                {"section_type": "warning", "title": "Nombre de la placa", "body": "La tabla histórica dice 'display PCB'; el diagrama de diagnóstico de esta familia la identifica como PCB I/O exterior.", "collapsed_default": 1},
            ],
            [
                step(1, "Cortar alimentación y esperar la descarga antes de tocar conectores o PCB.", level="danger"),
                step(2, "Revisar conectores, cable abierto y continuidad entre PCB I/O y principal."),
                step(3, "Comprobar si la propia PCB I/O presenta indicación de error."),
                step(4, "Si no hay error en I/O, continuar con la PCB I/O; si lo hay, comprobar I/O y principal."),
                step(5, "Si además las interiores muestran E11.1/E11.2, seguir el criterio específico de PCB principal exterior."),
            ],
            [source("02-64", None, "Trouble shooting 46 — Display P.C.B. Communication Error")],
            10,
        )],
    }


def branchbox_topic() -> dict[str, Any]:
    return {
        "id": 38,
        "brand_id": 2,
        "category_id": 14,
        "slug": "hybrid-flex-branch-box-j2",
        "title": "Diagnóstico de cajas de derivación ED2/J2",
        "summary": "Identificación de la caja, lectura LED401–LED405 y separación de comunicación, PCB, sondas, EEV y mando.",
        "active": 1,
        "category": {"id": 14, "slug": "vrf_network", "name": "Redes VRF y direccionamiento"},
        "variants": [
            variant(
                66,
                38,
                "Localizar la caja y descodificar LED401–LED405",
                "Sistema Flexible/Hybrid Flex con ED2, J2 o EJ2U y cajas con cinco LED numerados 401–405.",
                "Hybrid Flex / Flexible Multi",
                "Convertir el código genérico J2 en un subfallo accionable antes de desmontar componentes.",
                "LED401 identifica primaria/secundaria; LED402 identifica el tipo de error y LED403–405 el puerto A/B/C.",
                [
                    {"section_type": "identification", "title": "LED401 — qué caja", "body": "1 parpadeo: primaria. 2: secundaria 1. 3: secundaria 2.", "collapsed_default": 0},
                    {"section_type": "subcode", "title": "LED402 — qué familia de fallo", "body": "1 EEPROM; 2 modelo; 3 comunicación con exterior; 4 entre cajas; 5 comunicación con interior; 6 sonda líquido; 7 sonda gas; 8 EEV; 9 mando.", "collapsed_default": 0},
                    {"section_type": "port", "title": "LED403/404/405 — qué puerto", "body": "Cuando LED402 marca 5–8, los LED403, 404 y 405 seleccionan respectivamente A, B y C.", "collapsed_default": 0},
                ],
                [
                    step(1, "No desconectar ni corregir cableado con tensión; anotar primero todos los LED.", level="danger"),
                    step(2, "Contar LED401 para identificar caja primaria o secundaria."),
                    step(3, "Contar LED402 para identificar la familia del subfallo."),
                    step(4, "Si LED402 está entre 5 y 8, anotar cuál de LED403/404/405 queda encendido."),
                    step(5, "Abrir el procedimiento del componente o comunicación resultante; no tratar J2 como una causa única."),
                ],
                [source("02-14", "02-15", "2-3-6 Error status for Branch Box Display")],
                10,
            ),
            variant(
                67,
                38,
                "Comprobar cantidad, alimentación y comunicaciones de cajas",
                "La exterior detecta un número de cajas distinto al memorizado, una caja sin alimentación o LED402 marca 3, 4 o 5.",
                "Hybrid Flex / Flexible Multi",
                "Separar caja apagada, cantidad incorrecta, cableado y PCB de comunicaciones.",
                "CHECK RUN muestra cajas/interiores conectados; no debe iniciarse si la cantidad no coincide con la instalada.",
                [
                    {"section_type": "commissioning", "title": "Antes del CHECK RUN", "body": "Esperar a que desaparezca 8888 y comparar el número mostrado de cajas e interiores con el real.", "collapsed_default": 0},
                    {"section_type": "power", "title": "Rango documentado en CN105", "body": "En la familia del manual: 187–253 V CA en terminal 1–2 de CN105, tanto para la alimentación de la primaria desde exterior como para la secundaria desde la caja anterior.", "collapsed_default": 1},
                    {"section_type": "scope", "title": "Alcance", "body": "El manual no asigna una parada universal a todos los J2; debe identificarse la caja y la comunicación afectada.", "collapsed_default": 0},
                ],
                [
                    step(1, "Cortar alimentación antes de corregir terminales o cables.", level="danger"),
                    step(2, "Comprobar que todas las cajas están alimentadas y que todas las interiores están conectadas."),
                    step(3, "Comparar cantidad detectada e instalada; no iniciar CHECK RUN si no coincide."),
                    step(4, "Revisar conectores, continuidad, cortocircuitos, cruces y puesta a tierra del tramo indicado por LED402."),
                    step(5, "En la familia documentada, medir 187–253 V CA en CN105 1–2 con las precauciones reglamentarias.", "187–253 V CA.", level="danger"),
                    step(6, "Corregir, restablecer toda la alimentación y repetir CHECK RUN cuando corresponda."),
                ],
                [source("02-03", "02-04", "Check operation"), source("02-24", None, "Trouble shooting 7 — Number of Branch Boxes Error"), source("02-56", None, "Trouble shooting 39 — Power frequency error 2")],
                20,
            ),
            variant(
                68,
                38,
                "Seguir el subfallo de PCB, sonda, EEV o mando",
                "LED402 marca 1, 2, 6, 7, 8 o 9 después de identificar la caja con LED401.",
                "Hybrid Flex / Flexible Multi",
                "Evitar sustituir toda la caja cuando el patrón identifica una memoria, puerto, sonda, válvula o mando concretos.",
                "Los subflujos oficiales separan EEPROM/modelo, sondas A–C, EEV A–C y comunicación del mando.",
                [
                    {"section_type": "pcb", "title": "LED402 1 o 2", "body": "Resetear y revisar conectores, cortocircuito/corrosión, puesta a tierra y armónicos; sustituir PCB solo si no mejora.", "collapsed_default": 0},
                    {"section_type": "components", "title": "LED402 6, 7 u 8", "body": "LED403/404/405 identifica A/B/C. 6 corresponde a sonda de líquido; 7 a sonda de gas; 8 a la EEV.", "collapsed_default": 0},
                    {"section_type": "controller", "title": "LED402 9", "body": "Comunicación del mando: comprobar terminal, cable y la alimentación del controlador antes de decidir entre mando y PCB de caja.", "collapsed_default": 0},
                ],
                [
                    step(1, "Cortar alimentación antes de desconectar sondas, EEV o PCB.", level="danger"),
                    step(2, "Anotar LED401, LED402 y, cuando proceda, LED403–405."),
                    step(3, "Comprobar primero conector/cable del componente o puerto identificado."),
                    step(4, "En sondas, medir circuito abierto/corto y comparar curva; en EEV, comprobar bobinados y actuación según su subflujo."),
                    step(5, "En EEPROM/modelo, descartar ruido, tierra, conectores y corrosión antes de sustituir la PCB."),
                    step(6, "Restablecer alimentación y confirmar que el patrón no reaparece."),
                ],
                [source("02-57", "02-63", "Trouble shooting 40–45 — J2 branch box sub-errors")],
                30,
            ),
        ],
    }


def refresh_search() -> tuple[int, int]:
    error_count, _ = refresh_catalogs()
    search = [row for row in load(WEB / "search.json") if int(row.get("topic_id") or 0) not in (37, 38)]
    for topic_id in (37, 38):
        topic = load(WEB / "topics" / f"{topic_id}.json")
        for item in topic["variants"]:
            parts = [topic["title"], topic["summary"], item["title"], item["recognition"], item["purpose"], item["summary"]]
            parts.extend(section.get("title") or "" for section in item.get("sections") or [])
            parts.extend(section.get("body") or "" for section in item.get("sections") or [])
            parts.extend(row.get("instruction") or "" for row in item.get("steps") or [])
            parts.extend(row.get("expected_result") or "" for row in item.get("steps") or [])
            search.append({
                "type": "technical",
                "id": int(item["id"]),
                "topic_id": topic_id,
                "category_slug": topic["category"]["slug"],
                "category": topic["category"]["name"],
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
        "latest_phase": "Fujitsu V2 — PCB display/I/O y cajas de derivación",
        "last_processed_manual": ORIGIN,
        "technical_library_review": "E6A.1 y ED2/J2 desarrollados; no quedan fichas de error de solo referencia.",
        "last_update_utc": "2026-07-16T21:30:00Z",
    })
    for category_id, topic_id in ((9, 37), (14, 38)):
        topic = load(WEB / "topics" / f"{topic_id}.json")
        category = next(row for row in navigation["categories"] if int(row["id"]) == category_id)
        category["topics"] = [row for row in category.get("topics") or [] if int(row["id"]) != topic_id]
        category["topics"].append({
            "id": topic_id,
            "slug": topic["slug"],
            "title": topic["title"],
            "summary": topic["summary"],
            "active": 1,
            "variant_count": len(topic["variants"]),
        })
        category["topics"].sort(key=lambda row: int(row["id"]))
    write_json(navigation_path, navigation)

    variant_map_path = WEB / "variant_map.json"
    variant_map = load(variant_map_path)
    variant_map.update({"65": 37, "66": 38, "67": 38, "68": 38})
    write_json(variant_map_path, variant_map)

    sources_path = WEB / "sources.json"
    sources = [row for row in load(sources_path) if row.get("document_ref") != ORIGIN]
    sources.append({
        "id": 22,
        "title": MANUAL_TITLE,
        "document_ref": ORIGIN,
        "publication_date": "2015-04-29",
        "language": "en",
        "document_type": "service_manual",
        "source_url": MANUAL_URL,
        "status": "reviewed",
        "notes": "Documento técnico del fabricante alojado por un distribuidor. Se resumen E6A.1, J2, LED401–405 y CHECK RUN; no se publican páginas ni imágenes.",
    })
    sources.sort(key=lambda row: int(row["id"]))
    write_json(sources_path, sources)

    coverage_path = WEB / "coverage.json"
    coverage = load(coverage_path)
    for row in coverage:
        row["source_count"] = len(sources)
        if row.get("area_slug") == "errors":
            row["notes"] = "Las 117 fichas tienen ya desarrollo técnico o son códigos agrupadores con rutas; no quedan fichas de solo referencia."
        elif row.get("area_slug") == "component_checks":
            row["notes"] = "Incluye ahora comunicación principal–I/O exterior E6A.1 además de ventiladores, sondas, compuertas, válvulas y sensores."
        elif row.get("area_slug") == "vrf_network":
            row["notes"] = "Incluye direccionamiento VRF y diagnóstico Hybrid/Flexible Multi mediante ED2/J2 y LED401–LED405 de las cajas."
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
    config["notes"] = "Fujitsu V2.16: E6A.1 y ED2/J2 desarrollados con PCB I/O y lectura completa de LED de cajas."
    write_json(config_path, config)


def main() -> int:
    enrich_e6a()
    enrich_ed2()
    write_json(WEB / "topics" / "37.json", e6a_topic())
    write_json(WEB / "topics" / "38.json", branchbox_topic())
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
