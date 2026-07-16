#!/usr/bin/env python3
"""Consolida duplicados E84/E95 y separa las dos lógicas reales de E95."""

from __future__ import annotations

import json
from copy import deepcopy
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


VERSION = "2.17.0"


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


def append_info(
    interpretation: dict[str, Any],
    item_type: str,
    body: str,
    item_id: int,
    origin_ref: str,
) -> None:
    rows = interpretation.setdefault("info_items", [])
    if any(row.get("item_type") == item_type and row.get("body") == body for row in rows):
        return
    rows.append({
        "id": item_id,
        "item_type": item_type,
        "title": None,
        "body": body,
        "sort_order": max((int(row.get("sort_order") or 0) for row in rows), default=0) + 1,
        "review_status": "reviewed",
        "origin_ref": origin_ref,
    })


def consolidate_e84() -> None:
    path = DETAILS / "24.json"
    detail = load(path)
    legacy, developed = detail["interpretations"]
    developed["title"] = "Sensor de corriente integrado en la PCB principal exterior"
    developed["description"] = (
        "La entrada de corriente lee 0 A cuando el compresor inverter funciona por encima de 56 rps, "
        "ha transcurrido un minuto desde el arranque y no está activo el desescarche."
    )
    developed["operational_impacts"] = deepcopy(legacy.get("operational_impacts") or [])
    if developed["operational_impacts"]:
        developed["operational_impacts"][0]["restart_behavior"] = (
            "Corregir conexión, alimentación/ruido o PCB y restablecer la alimentación; "
            "el subcódigo 84.1 se clasifica como parada permanente."
        )
    developed["sources"] = unique_sources(
        (developed.get("sources") or []) + (legacy.get("sources") or [])
    )
    append_info(
        developed,
        "observation",
        "La tabla antigua y el subcódigo moderno 84.1 describen el mismo fallo; se consolidan para no mostrar dos causas idénticas.",
        82401,
        "AOEH09KMCG",
    )
    detail["interpretations"] = [developed]
    detail["short_label"] = "Sensor de corriente exterior — lectura 0 A"
    detail["tags"] = ["sensor corriente", "0 A", "56 rps", "84.1", "parada permanente"]
    write_json(path, detail)


def consolidate_e95() -> None:
    path = DETAILS / "27.json"
    detail = load(path)
    legacy_rotor, startup_overcurrent, rotor = detail["interpretations"]

    startup_overcurrent["title"] = "Sobrecorriente repetida durante el arranque del compresor"
    startup_overcurrent["description"] = (
        "En esta generación, E95 aparece cuando el ciclo de parada por sobrecorriente durante el arranque "
        "y rearranque del compresor se genera 10 veces consecutivas en 3 grupos: 30 intentos en total."
    )
    append_info(
        startup_overcurrent,
        "machine_behavior",
        "La protección de sobrecorriente al arrancar y rearrancar se repite 10 veces consecutivas por grupo y 3 grupos, 30 veces en total.",
        82701,
        "AOEG22KATA",
    )
    append_info(
        startup_overcurrent,
        "observation",
        "Esta interpretación pertenece a una generación cuyo manual define E95 por sobrecorriente de arranque; no debe mezclarse con la lógica 95.1 de desfase del rotor.",
        82702,
        "AOEG22KATA",
    )

    rotor["title"] = "Desfase superior a 90° en la posición detectada del rotor"
    rotor["description"] = (
        "Durante el funcionamiento, la posición detectada del rotor difiere más de 90° de la real. "
        "Si reaparece dentro de 40 segundos tras el rearranque y el ciclo se repite cinco veces, "
        "el compresor queda detenido permanentemente."
    )
    rotor["sources"] = unique_sources(
        (rotor.get("sources") or []) + (legacy_rotor.get("sources") or [])
    )
    append_info(
        rotor,
        "machine_behavior",
        "Un desfase de rotor superior a 90° detiene el compresor; si reaparece dentro de 40 segundos tras el rearranque y ocurre cinco veces, se produce parada permanente.",
        83901,
        "AOEH09KMCG",
    )
    append_info(
        rotor,
        "observation",
        "La interpretación antigua de posición del rotor y el subcódigo 95.1 moderno son el mismo mecanismo y se presentan como una sola ficha.",
        83902,
        "AOEH09KMCG",
    )
    detail["interpretations"] = [startup_overcurrent, rotor]
    detail["short_label"] = "Control del compresor: arranque o posición del rotor"
    detail["tags"] = ["compresor inverter", "sobrecorriente arranque", "rotor 90 grados", "40 segundos", "95.1"]
    write_json(path, detail)


def source(document_ref: str, page_start: str, section: str) -> dict[str, Any]:
    sources = load(WEB / "sources.json")
    entry = next(row for row in sources if row.get("document_ref") == document_ref)
    return {
        "title": entry["title"],
        "document_ref": document_ref,
        "source_url": entry.get("source_url"),
        "page_start": page_start,
        "page_end": page_start,
        "section": section,
    }


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
    title: str,
    recognition: str,
    purpose: str,
    summary: str,
    sections: list[dict[str, Any]],
    steps: list[dict[str, Any]],
    pages: list[dict[str, Any]],
    sort_order: int,
) -> dict[str, Any]:
    return {
        "id": variant_id,
        "topic_id": 39,
        "title": title,
        "recognition": recognition,
        "system_type": "split / conductos / comercial",
        "unit_scope": "outdoor",
        "refrigerant": "R32 / R410A",
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


def current_compressor_topic() -> dict[str, Any]:
    return {
        "id": 39,
        "brand_id": 2,
        "category_id": 9,
        "slug": "current-sensor-compressor-control",
        "title": "Sensor de corriente y control del compresor inverter",
        "summary": "Compara E84 y las dos lógicas documentadas de E95 sin mezclar generaciones.",
        "active": 1,
        "category": {"id": 9, "slug": "component_checks", "name": "Comprobación de componentes"},
        "variants": [
            variant(
                69,
                "E84 / 84.1 — El sensor de corriente lee 0 A",
                "Compresor por encima de 56 rps, más de un minuto desde el arranque y fuera del desescarche.",
                "Separar conexión, perturbación eléctrica y PCB principal con sensor integrado.",
                "El sensor está integrado en la PCB principal de la familia documentada; no se propone sustituir un captador externo inexistente.",
                [
                    {"section_type": "detection", "title": "Condición exacta", "body": "Lectura 0 A con el compresor >56 rps, transcurrido 1 minuto y fuera del desescarche.", "collapsed_default": 0},
                    {"section_type": "effect", "title": "Subcódigo 84.1", "body": "La tabla de la aplicación lo clasifica como parada permanente.", "collapsed_default": 0},
                    {"section_type": "electrical", "title": "Causas externas", "body": "Caída instantánea, microcorte, fuga/contacto defectuoso, armónicos o tierra deficiente pueden provocar la detección.", "collapsed_default": 1},
                ],
                [
                    step(1, "Cortar alimentación antes de revisar conexiones; esperar el tiempo de descarga indicado.", level="danger"),
                    step(2, "Restablecer y comprobar si E84 reaparece."),
                    step(3, "Revisar terminales, conectores, cable abierto y conexión errónea de la exterior."),
                    step(4, "Comprobar caída de tensión, microcortes, grandes cargas, armónicos y puesta a tierra."),
                    step(5, "Si todo es correcto y E84 reaparece, continuar con la PCB principal exterior."),
                ],
                [source("AOEH09KMCG", "03-41", "2-19. E84 Current sensor error")],
                10,
            ),
            variant(
                70,
                "E95 — Sobrecorriente repetida al arrancar",
                "Familia cuyo manual describe E95 como 'overcurrent generation at inverter compressor starting' y no como desfase del rotor.",
                "Diagnosticar una secuencia de 10 rearranques por grupo y 3 grupos antes del bloqueo de protección.",
                "Treinta repeticiones totales; el flujo separa ruido/avería mecánica del compresor, conexiones, PCB y compresor.",
                [
                    {"section_type": "sequence", "title": "Secuencia documentada", "body": "10 repeticiones consecutivas × 3 grupos = 30 ciclos de parada/rearranque por sobrecorriente de arranque.", "collapsed_default": 0},
                    {"section_type": "generation", "title": "No extrapolar", "body": "Esta lógica pertenece a una generación concreta; otras familias usan E95/95.1 para posición del rotor.", "collapsed_default": 0},
                ],
                [
                    step(1, "Desconectar alimentación antes de comprobar terminales del compresor o la etapa inverter.", level="danger"),
                    step(2, "Escuchar el intento de arranque y comprobar ruido mecánico anormal."),
                    step(3, "Revisar terminales, conectores, conexiones erróneas y continuidad del cable del compresor."),
                    step(4, "Si cableado y compresor no muestran anomalía evidente, seguir el flujo de PCB principal."),
                    step(5, "Si el cambio de PCB no corrige el síntoma, continuar con el compresor según el manual."),
                ],
                [source("AOEG22KATA", "03-33", "2-27. E95 Compressor motor control error")],
                20,
            ),
            variant(
                71,
                "E95 / 95.1 — Posición del rotor desfasada",
                "Familia cuyo manual/app identifica 95.1 como rotor position detection error con parada permanente.",
                "Aplicar la secuencia >90°, reaparición en 40 s y cinco repeticiones.",
                "El compresor se detiene por desfase; conexiones, PCB y compresor se comprueban en ese orden.",
                [
                    {"section_type": "sequence", "title": "Secuencia documentada", "body": "Desfase >90°; si reaparece dentro de 40 s tras el rearranque y el ciclo ocurre 5 veces, parada permanente.", "collapsed_default": 0},
                    {"section_type": "generation", "title": "No confundir con la otra E95", "body": "Si el manual de la unidad habla de 10 × 3 sobrecorrientes de arranque, usar la variante anterior.", "collapsed_default": 0},
                ],
                [
                    step(1, "Desconectar alimentación antes de comprobar terminales del compresor o la etapa inverter.", level="danger"),
                    step(2, "Escuchar ruido anormal durante el intento de arranque."),
                    step(3, "Revisar terminales, conectores, conexiones erróneas y cable abierto entre PCB y compresor."),
                    step(4, "Si no mejora, continuar con la PCB principal según el flujo oficial."),
                    step(5, "Si persiste tras la comprobación/cambio de PCB, continuar con el compresor."),
                ],
                [source("AOEH09KMCG", "03-43", "2-21. E95 Compressor motor control error")],
                30,
            ),
        ],
    }


def refresh_search() -> tuple[int, int]:
    error_count, _ = refresh_catalogs()
    search = [row for row in load(WEB / "search.json") if int(row.get("topic_id") or 0) != 39]
    topic = load(WEB / "topics" / "39.json")
    for item in topic["variants"]:
        parts = [topic["title"], topic["summary"], item["title"], item["recognition"], item["purpose"], item["summary"]]
        parts.extend(section.get("title") or "" for section in item.get("sections") or [])
        parts.extend(section.get("body") or "" for section in item.get("sections") or [])
        parts.extend(row.get("instruction") or "" for row in item.get("steps") or [])
        parts.extend(row.get("expected_result") or "" for row in item.get("steps") or [])
        search.append({
            "type": "technical",
            "id": int(item["id"]),
            "topic_id": 39,
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
        "latest_phase": "Fujitsu V2 — consolidación E84 y E95",
        "last_processed_manual": "AOEG22KATA / AOEH09KMCG",
        "technical_library_review": "E84 sin duplicado; E95 separa sobrecorriente de arranque y posición del rotor. No quedan interpretaciones parciales.",
        "last_update_utc": "2026-07-16T23:00:00Z",
    })
    topic = load(WEB / "topics" / "39.json")
    category = next(row for row in navigation["categories"] if int(row["id"]) == 9)
    category["topics"] = [row for row in category.get("topics") or [] if int(row["id"]) != 39]
    category["topics"].append({
        "id": 39,
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
    variant_map.update({"69": 39, "70": 39, "71": 39})
    write_json(variant_map_path, variant_map)

    coverage_path = WEB / "coverage.json"
    coverage = load(coverage_path)
    source_count = len(load(WEB / "sources.json"))
    for row in coverage:
        row["source_count"] = source_count
        if row.get("area_slug") == "errors":
            row["notes"] = "No quedan fichas ni interpretaciones parciales: E84 se consolida y E95 conserva solo sus dos lógicas realmente diferentes."
        elif row.get("area_slug") == "component_checks":
            row["notes"] = "Incluye sensor de corriente E84 y comparación de las dos secuencias E95, además de PCB I/O, ventiladores, sondas, EEV y mecanismos."
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
    config["notes"] = "Fujitsu V2.17: E84 consolidado y E95 separado por sobrecorriente de arranque o desfase del rotor."
    write_json(config_path, config)


def main() -> int:
    consolidate_e84()
    consolidate_e95()
    write_json(WEB / "topics" / "39.json", current_compressor_topic())
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
