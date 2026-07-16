#!/usr/bin/env python3
"""Desarrolla los fallos internos del mando cableado Fujitsu de 2 hilos.

La publicación contiene resúmenes y referencias. No incorpora páginas ni
imágenes del manual del fabricante.
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


VERSION = "2.15.0"
ORIGIN = "UTY_RCRYZ1_IM_9373328483"
MANUAL_TITLE = "Installation Manual — Wired Remote Controller UTY-RCRYZ1"
MANUAL_URL = "https://www.fujitsu-general.com/datafiles/W9373328483-0201_IM_En_UTY-RCRYZ1.pdf"


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
    observations: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    order = 1
    for item_type, bodies in (
        ("related_element", related),
        ("cause", causes),
        ("check", checks),
        ("observation", observations),
    ):
        for body in bodies:
            rows.append({
                "id": 70000 + interpretation_id * 100 + order,
                "item_type": item_type,
                "title": None,
                "body": body,
                "sort_order": order,
                "review_status": "reviewed",
                "origin_ref": ORIGIN,
            })
            order += 1
    return rows


def enrich_error(
    error_id: int,
    *,
    title: str,
    description: str,
    related: list[str],
    causes: list[str],
    checks: list[str],
    observations: list[str],
    pages: list[dict[str, Any]],
) -> None:
    path = DETAILS / f"{error_id}.json"
    detail = load(path)
    interpretation = detail["interpretations"][0]
    interpretation.update({
        "title": title,
        "description": description,
        "source_kind": "official",
        "confidence": "high",
        "review_status": "reviewed",
        "info_items": info_items(
            int(interpretation["id"]), related, causes, checks, observations
        ),
        "operational_impacts": [],
        "datasets": [],
        "sources": unique_sources((interpretation.get("sources") or []) + pages),
    })
    detail["short_label"] = title
    detail["tags"] = sorted(set((detail.get("tags") or []) + ["mando 2 hilos", "12 V", "bus no polar"]))
    write_json(path, detail)


def enrich_controller_errors() -> None:
    common_limitation = (
        "El manual define el código y documenta instalación, arranque y ajustes, "
        "pero no publica un árbol de reparación electrónica a nivel de componentes. "
        "Las comprobaciones siguientes descartan primero las condiciones documentadas."
    )

    enrich_error(
        53,
        title="Fallo de la PCB de transmisión del mando",
        description=(
            "El propio mando de 2 hilos informa C2.1 para identificar un fallo de su PCB "
            "de transmisión. No es un código frigorífico de la unidad interior."
        ),
        related=[
            "PCB de transmisión del mando",
            "Alimentación/bus de 2 hilos no polar",
            "Conexión entre PCB delantera y trasera del mando",
        ],
        causes=[
            "Fallo interno de la PCB de transmisión indicado por el propio código C2.1.",
            "Conector interno del mando mal asentado o dañado; el manual advierte que una conexión incorrecta provoca problemas.",
            "Alimentación o cableado del bus incorrectos que deben descartarse antes de sustituir el mando.",
        ],
        checks=[
            "Entrar en F2, función 02 (Error Details) y confirmar que la dirección mostrada corresponde a 'This product', no a una unidad interior.",
            "Comprobar que el bus es de dos conductores trenzados, no polar, y que la placa interior está configurada como 2WIRE.",
            "Comprobar una alimentación aproximada de 12 V CC en el mando y revisar continuidad/terminales del cable.",
            "Con la alimentación cortada, revisar el conector entre la PCB delantera y la trasera del mando.",
            "Si alimentación, cableado, selección 2WIRE y conexión interna son correctos y C2.1 permanece, continuar con sustitución o servicio del conjunto del mando.",
        ],
        observations=[common_limitation],
        pages=[
            source("En-5", "En-6", "5.3–5.4 Wiring and front case connection"),
            source("En-10", "En-12", "8.2.2 Error Details and error codes"),
        ],
    )

    enrich_error(
        56,
        title="Fallo durante el arranque del mando cableado",
        description=(
            "El mando de 2 hilos no completa correctamente su inicialización. En un arranque "
            "normal aparecen primero todos los segmentos y después entra en Monitor Mode."
        ),
        related=[
            "Mando cableado de 2 hilos",
            "Alimentación de 12 V CC",
            "Bus no polar y selector 2WIRE de la placa interior",
            "Direcciones del mando y de las unidades interiores",
        ],
        causes=[
            "Cableado incorrecto, terminal flojo o falta de alimentación durante la inicialización.",
            "Placa interior no configurada como 2WIRE para este tipo de mando.",
            "Conector entre las dos partes del mando mal insertado.",
            "Dirección o datos de instalación no adquiridos correctamente después de un cambio o traslado.",
            "Fallo interno del mando si todas las condiciones anteriores son correctas.",
        ],
        checks=[
            "Cortar alimentación y volver a comprobar cableado, terminales, conexión interna y posición 2WIRE antes de reenergizar.",
            "Comprobar aproximadamente 12 V CC en la entrada del mando.",
            "Observar el arranque: deben encenderse los segmentos de pantalla y, si es normal, aparecer Monitor Mode.",
            "Revisar direcciones con F2 n.º 10 y localizar físicamente la unidad con F2 n.º 11 cuando sea necesario.",
            "Después de una reubicación o sustitución, usar F2 n.º 16 (Initialization) solo cuando proceda; el mando se reinicia automáticamente.",
        ],
        observations=[
            "No confundir 12.4 con 26.4/26.5: estos últimos identifican direcciones duplicadas o mal configuradas.",
            common_limitation,
        ],
        pages=[
            source("En-5", "En-6", "5.3–6 Wiring, power on and initialization"),
            source("En-10", "En-12", "8.2 Service checks, initialization and error codes"),
        ],
    )

    enrich_error(
        57,
        title="Fallo de adquisición de datos de la unidad interior",
        description=(
            "El mando no consigue adquirir correctamente los datos de la unidad interior. "
            "La documentación Fujitsu también lo denomina 'Indoor unit data acquisition error'."
        ),
        related=[
            "Mando cableado de 2 hilos",
            "Unidad interior y su dirección",
            "Bus no polar de 12 V CC",
        ],
        causes=[
            "Comunicación o alimentación del bus interrumpida durante la adquisición.",
            "Dirección de unidad interior o de mando incorrecta/duplicada.",
            "La unidad interior seleccionada no responde o no entrega sus datos al mando.",
            "Fallo del propio mando si la unidad, el bus y el direccionamiento son correctos.",
        ],
        checks=[
            "Abrir F2 n.º 02 (Error Details) y anotar la dirección de la unidad afectada.",
            "Usar F2 n.º 10 para verificar direcciones y F2 n.º 11 para identificar por soplado/LED la unidad seleccionada.",
            "Comprobar bus no polar, terminales, continuidad, selección 2WIRE y aproximadamente 12 V CC.",
            "Verificar que las direcciones manuales de interior 1–15 y de mando 1–32 no están duplicadas; el valor 0 corresponde a asignación automática.",
            "Si el fallo queda ligado a una unidad concreta con bus y direcciones correctos, continuar en esa unidad interior; si afecta al propio producto, continuar con el mando.",
        ],
        observations=[
            "Los cambios manuales de dirección se reflejan después de cortar y restablecer alimentación.",
            common_limitation,
        ],
        pages=[
            source("En-8", "En-11", "8.1.7 addresses and 8.2.2–8.2.4 service checks"),
            source("En-12", None, "9 Error Codes"),
        ],
    )

    enrich_error(
        60,
        title="Configuración maestro/esclavo incorrecta del mando",
        description=(
            "En un grupo de mandos de 2 hilos, la configuración Master/Slave no cumple la regla "
            "documentada: solo un mando debe quedar como Master."
        ),
        related=[
            "Función F1 n.º 06 Master/Slave",
            "Mandos de 2 hilos conectados al mismo grupo",
            "Direcciones del sistema de mando",
        ],
        causes=[
            "Más de un mando configurado como Master dentro del mismo grupo.",
            "Ningún mando queda correctamente establecido como Master tras una instalación o sustitución.",
            "Configuración no aplicada o direcciones del grupo incorrectas.",
        ],
        checks=[
            "Entrar en F1 n.º 06 en cada mando del grupo y comprobar su ajuste Master o Slave.",
            "Dejar exactamente un mando como Master; configurar los demás como Slave.",
            "Consultar en la misma pantalla el número de mandos Master detectados y confirmar que es uno.",
            "Revisar direcciones con F2 n.º 10 y corregir duplicados antes de repetir la configuración.",
            "Cortar y restablecer alimentación cuando el procedimiento lo requiera y confirmar que 27.1 desaparece.",
        ],
        observations=[
            "No confundir 'Remote controller Master/Slave' F1 n.º 06 con 'Master indoor unit' F1 n.º 12; son ajustes distintos.",
            common_limitation,
        ],
        pages=[
            source("En-7", "En-8", "8.1.2 Remote controller master/slave setting"),
            source("En-10", "En-12", "8.2 Address checks and 9 Error Codes"),
        ],
    )


def step(
    number: int,
    instruction: str,
    expected: str | None = None,
    level: str = "warning",
) -> dict[str, Any]:
    return {
        "phase": "check" if number > 1 else "safety",
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
        "topic_id": 36,
        "title": title,
        "recognition": recognition,
        "system_type": "split / multisplit / VRF",
        "unit_scope": "general",
        "refrigerant": None,
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


def controller_topic() -> dict[str, Any]:
    common_recognition = (
        "Mando compacto de dos hilos, bus no polar, menús F1/F2 y código con punto mostrado en su pantalla."
    )
    return {
        "id": 36,
        "brand_id": 2,
        "category_id": 12,
        "slug": "two-wire-controller-internal-errors",
        "title": "Diagnóstico de fallos internos del mando de 2 hilos",
        "summary": "Flujos separados para C2.1, 12.4, 15.4 y 27.1 sin confundirlos con averías frigoríficas.",
        "active": 1,
        "category": {"id": 12, "slug": "controllers_buses", "name": "Mandos, cableado y buses"},
        "variants": [
            variant(
                61,
                "C2.1 — PCB de transmisión del propio mando",
                common_recognition,
                "Confirmar que el error pertenece al mando y descartar instalación antes de sustituirlo.",
                "F2 n.º 02 permite distinguir 'This product' de una unidad interior; después se revisan 12 V, bus, 2WIRE y conector interno.",
                [
                    {"section_type": "recognition", "title": "A quién pertenece el error", "body": "En Error Details, 'This product' identifica el propio mando. Una dirección interior dirige el diagnóstico a esa unidad.", "collapsed_default": 0},
                    {"section_type": "limits", "title": "Límite de la fuente", "body": "El manual no publica una reparación electrónica interna de la PCB; primero se descartan las condiciones de instalación documentadas.", "collapsed_default": 1},
                ],
                [
                    step(1, "Cortar alimentación antes de abrir el mando o revisar su conector interno.", level="danger"),
                    step(2, "Abrir F2 n.º 02 y confirmar que C2.1 corresponde a 'This product'."),
                    step(3, "Comprobar bus de dos hilos no polar, continuidad y aproximadamente 12 V CC.", "12 V CC aproximadamente."),
                    step(4, "Confirmar selector 2WIRE en la placa interior y revisar el conector entre PCB delantera y trasera."),
                    step(5, "Si instalación y alimentación son correctas y C2.1 permanece, continuar con servicio o sustitución del mando."),
                ],
                [source("En-5", "En-6", "5.3–5.4 Wiring and front case connection"), source("En-10", "En-12", "8.2.2 Error Details and 9 Error Codes")],
                10,
            ),
            variant(
                62,
                "12.4 — El mando no completa el arranque",
                common_recognition,
                "Comprobar por qué la inicialización no llega al Monitor Mode.",
                "La secuencia normal enciende segmentos y finaliza en Monitor Mode; cableado, 12 V, 2WIRE, conexión interna y direcciones se comprueban en ese orden.",
                [
                    {"section_type": "behavior", "title": "Arranque normal documentado", "body": "Tras alimentar se muestran los segmentos de inicio. Si la inicialización termina correctamente, el mando entra en Monitor Mode.", "collapsed_default": 0},
                    {"section_type": "reset", "title": "Inicialización F2 n.º 16", "body": "Se reserva para reubicación/sustitución cuando proceda; el mando se reinicia automáticamente.", "collapsed_default": 1},
                ],
                [
                    step(1, "Cortar alimentación antes de corregir cableado o conectores.", level="danger"),
                    step(2, "Revisar bus no polar, terminales, selector 2WIRE y conector de la carcasa frontal."),
                    step(3, "Comprobar aproximadamente 12 V CC en el mando.", "12 V CC aproximadamente."),
                    step(4, "Restablecer alimentación y observar si la pantalla completa la secuencia hasta Monitor Mode."),
                    step(5, "Comprobar direcciones con F2 n.º 10; usar F2 n.º 16 solo si la instalación requiere reinicialización."),
                ],
                [source("En-5", "En-6", "5.3–6 Wiring and initialization"), source("En-10", "En-12", "8.2 Service checks and 9 Error Codes")],
                20,
            ),
            variant(
                63,
                "15.4 — No se adquieren datos de una unidad interior",
                common_recognition,
                "Localizar la dirección afectada y separar bus, direccionamiento, unidad interior y mando.",
                "Error Details identifica la dirección; Address Verification y Position Check permiten verificar qué unidad no entrega datos.",
                [
                    {"section_type": "addressing", "title": "Rangos documentados", "body": "Dirección interior manual 1–15; dirección de mando 1–32; 0 conserva la asignación automática. No se permiten duplicados.", "collapsed_default": 0},
                    {"section_type": "identification", "title": "Identificación física", "body": "F2 n.º 11 puede provocar soplado o indicación LED para reconocer la unidad seleccionada.", "collapsed_default": 1},
                ],
                [
                    step(1, "No modificar direcciones con la instalación en marcha; aplicar el procedimiento de alimentación del manual.", level="danger"),
                    step(2, "Abrir F2 n.º 02 y anotar la dirección asociada a 15.4."),
                    step(3, "Comprobar direcciones con F2 n.º 10 y localizar la unidad mediante F2 n.º 11."),
                    step(4, "Revisar bus no polar, 12 V, continuidad, terminales y selector 2WIRE."),
                    step(5, "Con bus y direcciones correctos, continuar el diagnóstico en la unidad interior identificada o en el mando si Error Details señala 'This product'."),
                ],
                [source("En-8", "En-11", "8.1.7 addresses and 8.2.2–8.2.4 service checks"), source("En-12", None, "9 Error Codes")],
                30,
            ),
            variant(
                64,
                "27.1 — Maestro/esclavo incorrecto",
                common_recognition,
                "Dejar exactamente un mando Master dentro del grupo de control.",
                "F1 n.º 06 muestra el ajuste Master/Slave y el número de maestros detectados.",
                [
                    {"section_type": "rule", "title": "Regla del grupo", "body": "Solo un mando debe configurarse como Master. Los demás quedan como Slave y tienen funciones restringidas.", "collapsed_default": 0},
                    {"section_type": "warning", "title": "No confundir dos ajustes", "body": "F1 n.º 06 configura el mando Master/Slave; F1 n.º 12 configura la unidad interior maestra.", "collapsed_default": 0},
                ],
                [
                    step(1, "Anotar los ajustes actuales antes de modificar el grupo."),
                    step(2, "Entrar en F1 n.º 06 en cada mando y comprobar Master/Slave."),
                    step(3, "Dejar un solo Master y configurar todos los demás como Slave.", "Número de Master mostrado: 1."),
                    step(4, "Verificar direcciones con F2 n.º 10 y eliminar duplicados."),
                    step(5, "Reiniciar cuando lo exija el procedimiento y confirmar que 27.1 desaparece."),
                ],
                [source("En-7", "En-8", "8.1.2 Remote controller master/slave setting"), source("En-10", "En-12", "8.2 Address checks and 9 Error Codes")],
                40,
            ),
        ],
    }


def refresh_search() -> tuple[int, int]:
    error_count, _ = refresh_catalogs()
    search = [row for row in load(WEB / "search.json") if int(row.get("topic_id") or 0) != 36]
    topic = load(WEB / "topics" / "36.json")
    for item in topic["variants"]:
        parts = [topic["title"], topic["summary"], item["title"], item["recognition"], item["purpose"], item["summary"]]
        parts.extend(section.get("title") or "" for section in item.get("sections") or [])
        parts.extend(section.get("body") or "" for section in item.get("sections") or [])
        parts.extend(row.get("instruction") or "" for row in item.get("steps") or [])
        parts.extend(row.get("expected_result") or "" for row in item.get("steps") or [])
        search.append({
            "type": "technical",
            "id": int(item["id"]),
            "topic_id": 36,
            "category_slug": "controllers_buses",
            "category": "Mandos, cableado y buses",
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
        "latest_phase": "Fujitsu V2 — diagnóstico interno del mando de 2 hilos",
        "last_processed_manual": ORIGIN,
        "technical_library_review": "C2.1, 12.4, 15.4 y 27.1 desarrollados con arranque, bus, direcciones y maestro/esclavo.",
        "last_update_utc": "2026-07-16T20:00:00Z",
    })
    topic = load(WEB / "topics" / "36.json")
    category = next(row for row in navigation["categories"] if int(row["id"]) == 12)
    category["topics"] = [row for row in category.get("topics") or [] if int(row["id"]) != 36]
    category["topics"].append({
        "id": 36,
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
    variant_map.update({str(item): 36 for item in range(61, 65)})
    write_json(variant_map_path, variant_map)

    sources_path = WEB / "sources.json"
    sources = [row for row in load(sources_path) if row.get("document_ref") != ORIGIN]
    sources.append({
        "id": 21,
        "title": MANUAL_TITLE,
        "document_ref": ORIGIN,
        "publication_date": "2020-01-17",
        "language": "en",
        "document_type": "installation_manual",
        "source_url": MANUAL_URL,
        "status": "reviewed",
        "notes": "Fuente oficial. Se resumen cableado, 12 V, arranque, F1/F2, direcciones y códigos; no se publican páginas ni imágenes.",
    })
    sources.sort(key=lambda row: int(row["id"]))
    write_json(sources_path, sources)

    coverage_path = WEB / "coverage.json"
    coverage = load(coverage_path)
    for row in coverage:
        row["source_count"] = len(sources)
        if row.get("area_slug") == "controllers_buses":
            row["notes"] = "Incluye 2 hilos no polar, 3 hilos, tensiones, arranque, diagnóstico E12 y los flujos internos C2.1/12.4/15.4/27.1."
        elif row.get("area_slug") == "errors":
            row["notes"] = "Los cuatro códigos propios del mando de 2 hilos ya tienen causas a descartar, comprobaciones y limitación documental explícita."
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
    config["notes"] = "Fujitsu V2.15: diagnóstico del mando de 2 hilos para C2.1, 12.4, 15.4 y 27.1."
    write_json(config_path, config)


def main() -> int:
    enrich_controller_errors()
    write_json(WEB / "topics" / "36.json", controller_topic())
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
