#!/usr/bin/env python3
"""Añade CHECK RUN multisplit y desarrolla el código Fujitsu E15."""

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
ORIGIN = "FUJITSU_V2_MULTISPLIT_CHECKRUN"
DOCUMENT_REF = "9374995530-05"
SOURCE_URL = "https://webstore.uk.fujitsu-general.com/product/attachment/AOYG45LBLA6/installation%20manual.pdf"
TOPIC_ID = 30
VARIANT_ID = 47


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def source(page_start: str, page_end: str, section: str) -> dict[str, Any]:
    return {
        "title": "Installation Manual — Fujitsu/General AOYG45LBLA6",
        "document_ref": DOCUMENT_REF,
        "source_url": SOURCE_URL,
        "page_start": page_start,
        "page_end": page_end,
        "section": section,
    }


def enrich_e15() -> None:
    path = DETAILS / "4.json"
    detail = load(path)
    interpretation = next(row for row in detail["interpretations"] if int(row["id"]) == 42)
    interpretation["description"] = (
        "En sistemas que incorporan CHECK RUN automático, la puesta en marcha no ha terminado, "
        "se ha interrumpido o sus resultados todavía no se han confirmado."
    )
    interpretation["info_items"] = [
        row for row in interpretation.get("info_items") or []
        if row.get("origin_ref") != ORIGIN
    ]
    content = [
        ("related_element", "CHECK RUN y memoria de corrección automática del cableado"),
        ("related_element", "Comunicación, tuberías y cableado entre exterior e interiores"),
        ("cause", "CHECK RUN no iniciado, interrumpido o no confirmado hasta el final."),
        ("cause", "Otro error aparece durante la comprobación y suspende el proceso."),
        ("cause", "El número de interiores detectado no coincide con el instalado o existen líneas de comunicación incorrectas."),
        ("cause", "La temperatura está fuera del margen de funcionamiento o no permite evaluar correctamente la instalación."),
        ("cause", "Se corta la alimentación durante la presentación de resultados antes de confirmar la corrección automática."),
        ("check", "Confirmar tuberías terminadas, cableado terminado, ausencia de fugas, carga correcta, magnetotérmico instalado, bornes firmes, válvulas de 3 vías abiertas y más de 12 horas de alimentación."),
        ("check", "Con las unidades paradas, mantener CHECK al menos 3 segundos y comparar el número de interiores mostrado con el realmente instalado."),
        ("check", "Si el recuento no coincide, cortar alimentación y revisar las líneas de comunicación interior-exterior."),
        ("check", "Mantener CHECK otros 3 segundos para iniciar; los LED A-F parpadean y cada LED se apaga al terminar la comprobación de su interior."),
        ("check", "Si aparece otro error, corregirlo y repetir CHECK RUN. Si falla por temperatura fuera de margen, usar la prueba en frío de la interior para comprobar la instalación."),
        ("check", "En los resultados, corregir manualmente con la alimentación desconectada o confirmar la corrección automática manteniendo CHECK más de 3 segundos."),
        ("check", "Después de completar la corrección automática, cortar alimentación, esperar 10 minutos, restablecerla y realizar TEST RUN."),
        ("machine_behavior", "Todas las interiores conectadas arrancan automáticamente; no pueden comprobarse por separado durante CHECK RUN."),
        ("machine_behavior", "El sistema elige frío o calor según las temperaturas. El proceso dura aproximadamente 30 minutos en frío o 1 hora en calor, aunque puede prolongarse."),
        ("observation", "Esta secuencia corresponde a la variante de placa con pulsador CHECK y LED A-F; no debe aplicarse a placas con MODE/SELECT/ENTER o display de siete segmentos."),
    ]
    for order, (item_type, body) in enumerate(content):
        interpretation["info_items"].append({
            "id": 40000 + order,
            "item_type": item_type,
            "title": None,
            "body": body,
            "sort_order": order,
            "review_status": "reviewed",
            "origin_ref": ORIGIN,
        })
    interpretation["sources"] = [
        row for row in interpretation.get("sources") or []
        if row.get("document_ref") != DOCUMENT_REF
    ] + [source("En-13", "En-16", "8. CHECK RUN")]
    write_json(path, detail)


def topic() -> dict[str, Any]:
    sections = [
        {
            "section_type": "recognition",
            "title": "Cómo reconocer esta variante",
            "body": "PCB exterior multisplit con pulsador CHECK (SW2), LED POWER/MODE y seis indicadores A-F. No usa MODE/SELECT/ENTER ni display alfanumérico.",
            "collapsed_default": 0,
        },
        {
            "section_type": "prerequisites",
            "title": "Antes de empezar",
            "body": "Tuberías y cableado terminados; sin fugas; carga correcta; protección eléctrica instalada; bornes firmes; válvulas de gas y líquido abiertas; alimentación conectada durante más de 12 horas; interiores y exterior paradas.",
            "collapsed_default": 0,
        },
        {
            "section_type": "machine_behavior",
            "title": "Qué hace la máquina",
            "body": "Arrancan automáticamente todas las interiores. El sistema selecciona frío o calor según las temperaturas y no permite comprobar cada interior por separado. Duración orientativa: unos 30 minutos en frío o 1 hora en calor.",
            "collapsed_default": 0,
        },
        {
            "section_type": "results",
            "title": "Interpretación de resultados",
            "body": "Los LED muestran el orden de correspondencia entre tuberías y cableado. Una secuencia intercambiada señala cruces. Puede corregirse físicamente con la alimentación desconectada o mediante la función automática de la placa.",
            "collapsed_default": 1,
        },
        {
            "section_type": "limitations",
            "title": "Cuándo no puede completarse",
            "body": "La prueba se detiene si aparece otro error, si la temperatura está fuera de margen o si no coincide el número de conexiones de tubería y cableado. Corregir la causa y repetir.",
            "collapsed_default": 1,
        },
        {
            "section_type": "safety",
            "title": "Precauciones",
            "body": "No cerrar todas las ventanas durante la prueba. Para corregir cableado manualmente, cortar la alimentación. Tras la corrección automática, cortar alimentación, esperar 10 minutos y volver a alimentar antes de TEST RUN.",
            "collapsed_default": 1,
        },
    ]
    steps = [
        {"phase": "start", "step_no": 1, "instruction": "Comprobar las ocho condiciones previas y que todas las unidades estén paradas.", "expected_result": None, "warning_level": "none"},
        {"phase": "start", "step_no": 2, "instruction": "Mantener pulsado CHECK durante 3 segundos o más.", "expected_result": "La placa muestra cuántas interiores detecta y sus posiciones A-F.", "warning_level": "none"},
        {"phase": "start", "step_no": 3, "instruction": "Comparar el recuento con la instalación. Si no coincide, cortar alimentación y revisar las líneas de comunicación.", "expected_result": "El número mostrado coincide con el instalado.", "warning_level": "warning"},
        {"phase": "start", "step_no": 4, "instruction": "Mantener CHECK otros 3 segundos o más.", "expected_result": "Todos los LED A-F parpadean en la fase preliminar y se apagan al completar cada interior.", "warning_level": "none"},
        {"phase": "check", "step_no": 1, "instruction": "Esperar al resultado y anotar el orden en que se iluminan los LED, a intervalos de aproximadamente 7 segundos.", "expected_result": "La secuencia permite comparar correspondencia de tubería y cableado.", "warning_level": "none"},
        {"phase": "correct", "step_no": 1, "instruction": "Si hay cruces, corregir el cableado manualmente con tensión cortada o mantener CHECK más de 3 segundos durante la pantalla de resultados para aplicar la corrección automática.", "expected_result": "Los LED A-F se encienden en secuencia y después todos juntos al finalizar la corrección automática.", "warning_level": "warning"},
        {"phase": "finish", "step_no": 1, "instruction": "Cortar alimentación, esperar 10 minutos, volver a alimentar y realizar TEST RUN.", "expected_result": "El sistema vuelve al funcionamiento normal con la correspondencia guardada.", "warning_level": "warning"},
        {"phase": "stop", "step_no": 1, "instruction": "Para interrumpir CHECK RUN, pulsar CHECK.", "expected_result": "La comprobación se detiene; deberá repetirse para obtener un resultado válido.", "warning_level": "note"},
    ]
    return {
        "id": TOPIC_ID,
        "brand_id": 2,
        "category_id": 4,
        "slug": "multisplit-check-run-wiring-correction",
        "title": "CHECK RUN multisplit y corrección automática de cableado",
        "summary": "Comprobación automática de correspondencia entre tuberías y cableado desde una PCB con botón CHECK y LED A-F.",
        "active": 1,
        "category": {"id": 4, "slug": "commissioning", "name": "Puesta en marcha"},
        "variants": [{
            "id": VARIANT_ID,
            "topic_id": TOPIC_ID,
            "title": "PCB multisplit con pulsador CHECK y LED A-F",
            "recognition": "Pulsador CHECK (SW2), POWER/MODE y seis LED A-F para las interiores conectadas.",
            "system_type": "multisplit",
            "unit_scope": "system",
            "refrigerant": "R410A",
            "purpose": "Detectar cruces entre tuberías y cableado y, si se desea, corregir la correspondencia automáticamente.",
            "summary": "Muestra el número de interiores, prueba todas las unidades, presenta el orden de correspondencia y permite guardar una corrección automática.",
            "source_kind": "official",
            "review_status": "reviewed",
            "sort_order": 0,
            "visible": 1,
            "sections": sections,
            "steps": steps,
            "parameters": [],
            "controller": None,
            "monitoring_points": [],
            "media": [],
            "sources": [source("En-13", "En-16", "8. CHECK RUN")],
        }],
    }


def update_library() -> None:
    topic_data = topic()
    write_json(WEB / "topics" / f"{TOPIC_ID}.json", topic_data)

    navigation_path = WEB / "navigation.json"
    navigation = load(navigation_path)
    metadata = navigation.setdefault("metadata", {})
    metadata["data_version"] = "2.9.0"
    metadata["latest_phase"] = "Fujitsu V2 — CHECK RUN multisplit"
    metadata["last_processed_manual"] = DOCUMENT_REF
    metadata["technical_library_review"] = "Puesta en marcha multisplit, detección de cruces y corrección automática de cableado."
    category = next(row for row in navigation["categories"] if row.get("slug") == "commissioning")
    category["topics"] = [row for row in category.get("topics") or [] if int(row.get("id") or 0) != TOPIC_ID]
    category["topics"].append({
        "id": TOPIC_ID,
        "slug": topic_data["slug"],
        "title": topic_data["title"],
        "summary": topic_data["summary"],
        "active": 1,
        "variant_count": 1,
    })
    write_json(navigation_path, navigation)

    map_path = WEB / "variant_map.json"
    variant_map = load(map_path)
    variant_map[str(VARIANT_ID)] = TOPIC_ID
    write_json(map_path, variant_map)

    sources_path = WEB / "sources.json"
    sources = [row for row in load(sources_path) if row.get("document_ref") != DOCUMENT_REF]
    sources.append({
        "id": 16,
        "title": "Installation Manual — Fujitsu/General AOYG45LBLA6",
        "document_ref": DOCUMENT_REF,
        "publication_date": "2020",
        "language": "en",
        "document_type": "installation_manual",
        "source_url": SOURCE_URL,
        "extraction_status": "reviewed",
        "review_status": "reviewed",
        "notes": "CHECK RUN multisplit, resultados, corrección automática y reinicio de memoria.",
    })
    write_json(sources_path, sources)

    search_path = WEB / "search.json"
    search = [row for row in load(search_path) if not (row.get("type") == "variant" and int(row.get("id") or 0) == VARIANT_ID)]
    variant = topic_data["variants"][0]
    text = [variant["title"], variant["recognition"], variant["purpose"], variant["summary"]]
    text.extend(row.get("body") or "" for row in variant["sections"])
    text.extend(row.get("instruction") or "" for row in variant["steps"])
    text.extend(row.get("expected_result") or "" for row in variant["steps"])
    search.append({
        "type": "variant",
        "id": VARIANT_ID,
        "topic_id": TOPIC_ID,
        "category_slug": "commissioning",
        "category": "Puesta en marcha",
        "title": variant["title"],
        "summary": variant["summary"],
        "haystack": normalize(" ".join(text)),
    })
    write_json(search_path, search)


def main() -> int:
    enrich_e15()
    update_library()

    config_path = BRAND / "brand.json"
    config = load(config_path)
    config["data_version"] = "2.9.0"
    config["counts"] = {
        "categories": 18,
        "topics": 30,
        "variants": 47,
        "errors": 110,
        "search_entries": 157,
    }
    config["notes"] = "Fujitsu V2: CHECK RUN multisplit y código E15 desarrollados con procedimiento oficial de serie 45."
    write_json(config_path, config)

    coverage_path = WEB / "coverage.json"
    coverage = load(coverage_path)
    commissioning = next(row for row in coverage if row.get("area_slug") == "commissioning")
    commissioning["equipment_scope"] = "multisplit y VRF"
    commissioning["source_count"] = max(int(commissioning.get("source_count") or 0), 16)
    commissioning["notes"] = "Incluye CHECK RUN multisplit con detección/corrección de cruces y Test Run, autoaddress y red VRF."
    write_json(coverage_path, coverage)

    refresh_search()
    report = audit_brand(BRAND)
    write_json(WEB / "quality.json", report)
    print(json.dumps({
        "e15_developed": True,
        "topics": len(list((WEB / "topics").glob("*.json"))),
        "variants": report["technical_variants"]["entries"],
        "interpretations": report["errors"]["interpretations"],
        "statuses": report["errors"]["status_counts"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
