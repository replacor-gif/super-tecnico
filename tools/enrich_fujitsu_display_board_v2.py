#!/usr/bin/env python3
"""Completa la lectura de estados VRF y el reconocimiento de la PCB S130-S134."""

from __future__ import annotations

import json
from typing import Any

from audit_brand_quality import audit_brand, write as write_json
from enrich_fujitsu_indoor_valve_v2 import BRAND, WEB, load, normalize


VERSION = "2.18.0"


def section(section_type: str, title: str, body: str, collapsed: int = 0) -> dict[str, Any]:
    return {
        "section_type": section_type,
        "title": title,
        "body": body,
        "collapsed_default": collapsed,
    }


def step(
    phase: str,
    number: int,
    instruction: str,
    expected: str | None = None,
    warning: str = "none",
) -> dict[str, Any]:
    return {
        "phase": phase,
        "step_no": number,
        "instruction": instruction,
        "expected_result": expected,
        "warning_level": warning,
    }


def enrich_board_buttons() -> None:
    path = WEB / "topics" / "5.json"
    topic = load(path)
    variant = next(row for row in topic["variants"] if int(row["id"]) == 6)
    variant["summary"] = (
        "Guía para reconocer S134 MODE, S133 SELECT, S132 ENTER, S131 EXIT y S130 PUMP DOWN, "
        "interpretar sus LED y abandonar una consulta sin iniciar por error una operación de servicio."
    )
    variant["sections"] = [
        section(
            "safety",
            "Antes de tocar la placa",
            "Para cambiar ajustes, detener antes el equipo. Descargar la electricidad estática del cuerpo y no tocar terminales ni pistas de la PCB. El pulsador PUMP DOWN inicia una operación frigorífica: no usarlo para navegar ni para salir.",
        ),
        section(
            "recognition",
            "Indicadores que identifican esta variante",
            "POWER/MODE es verde; ERROR es rojo. PUMP DOWN (L1), LOW NOISE (L2-L3) y PEAK CUT (L4-L6) son naranjas. POWER/MODE queda encendido con alimentación y parpadea durante ajustes locales o visualización de códigos.",
        ),
        section(
            "controls",
            "Función de los cinco pulsadores",
            "MODE cambia entre ajuste local y visualización de error; SELECT recorre las opciones; ENTER entra o confirma; EXIT regresa a la indicación de funcionamiento; PUMP DOWN inicia la recogida de refrigerante.",
        ),
        section(
            "recovery",
            "Si se pierde la posición del menú",
            "Pulsar EXIT una vez para volver a la indicación de funcionamiento normal. Para una programación, empezar de nuevo desde el principio y comprobar la secuencia LED del procedimiento concreto.",
            1,
        ),
    ]
    variant["steps"] = [
        step(
            "recognition",
            1,
            "Identificar los cinco pulsadores en línea y leer sus referencias impresas: S134, S133, S132, S131 y S130.",
            "Deben corresponder, en ese orden, a MODE, SELECT, ENTER, EXIT y PUMP DOWN.",
        ),
        step(
            "recognition",
            2,
            "Comprobar la fila de indicadores antes de pulsar nada.",
            "POWER/MODE verde indica alimentación; ERROR rojo parpadea durante una condición de error; L1-L6 identifican pump down, bajo ruido y Peak Cut.",
        ),
        step(
            "navigation",
            1,
            "Usar MODE para elegir entre ajuste local y visualización de errores; usar SELECT para recorrer la opción disponible.",
            "La indicación POWER/MODE y los LED de función cambian según el modo seleccionado.",
        ),
        step(
            "navigation",
            2,
            "Pulsar ENTER solo cuando la indicación corresponda a la consulta o ajuste deseado.",
            "Se entra en la opción o se confirma el valor mostrado.",
            "caution",
        ),
        step(
            "exit",
            1,
            "Pulsar EXIT para regresar a la indicación de funcionamiento normal.",
            "La placa abandona el recorrido de consulta o ajuste.",
        ),
        step(
            "warning",
            1,
            "No pulsar PUMP DOWN salvo que se vaya a ejecutar el procedimiento completo de recogida de refrigerante.",
            "Ese botón no es una tecla de retroceso: inicia una operación de servicio separada.",
            "danger",
        ),
    ]
    variant["sources"][0].update({
        "page_start": "05-6",
        "page_end": "05-8",
        "section": "2-1 Control PCB and switch buttons location / 2-2 Local setting procedure",
    })
    write_json(path, topic)


def enrich_normal_status() -> None:
    path = WEB / "topics" / "24.json"
    topic = load(path)
    variant = next(row for row in topic["variants"] if int(row["id"]) == 37)
    variant["summary"] = (
        "CL y Ht indican frío o calor; or y dF son recuperación de aceite o desescarche; "
        "PC, Ln y Sn señalan Peak Cut, bajo ruido o modo nieve. Son estados del sistema, no errores por sí solos."
    )
    variant["sections"] = [
        section(
            "classification",
            "Cómo distinguir estado y avería",
            "La tabla oficial separa los códigos normales de los códigos de error. CL, Ht, or, dF, PC, Ln y Sn describen el estado actual. Los fallos aparecen en la tabla de errores con prefijo E y subcódigo.",
        ),
        section(
            "machine_behavior",
            "Estados transitorios del circuito",
            "or significa que el sistema está ejecutando recuperación de aceite y dF que está en desescarche. Durante esos procesos el comportamiento puede diferir de una demanda normal, pero el código por sí solo no acredita una avería.",
        ),
        section(
            "limitations",
            "Limitaciones o funciones activas",
            "PC indica Peak Cut; Ln, funcionamiento de bajo ruido; Sn, configuración de modo nieve. Si la capacidad o el ventilador parecen limitados, comprobar primero si una de estas funciones está activada antes de buscar un fallo.",
        ),
        section(
            "scope",
            "Límite de esta tabla",
            "La indicación confirma el estado mostrado, pero no demuestra por sí sola por qué se activó una función ni sustituye la lectura de un código E cuando también exista una avería.",
            1,
        ),
    ]
    variant["steps"] = [
        step(
            "read",
            1,
            "Leer los dos caracteres del indicador exterior de siete segmentos sin interpretar todavía el comportamiento de la máquina.",
            "Registrar exactamente mayúsculas y minúsculas: CL, Ht, or, dF, PC, Ln o Sn.",
        ),
        step(
            "classify",
            2,
            "Comparar la indicación con la tabla de estados normales.",
            "CL: frío; Ht: calor; or: recuperación de aceite; dF: desescarche; PC: Peak Cut; Ln: bajo ruido; Sn: modo nieve.",
        ),
        step(
            "classify",
            3,
            "Si el display empieza por E o presenta un subcódigo de error, abandonar esta tabla y consultar la ficha de errores.",
            "No mezclar un estado normal con un código de avería.",
            "caution",
        ),
        step(
            "interpret",
            4,
            "Si aparece or o dF, esperar a que termine el proceso y comprobar después si el sistema recupera el funcionamiento solicitado.",
            "La indicación debe cambiar cuando finalice la recuperación de aceite o el desescarche.",
        ),
        step(
            "interpret",
            5,
            "Si aparece PC, Ln o Sn y el rendimiento parece limitado, revisar la programación o entrada externa correspondiente.",
            "La limitación puede ser coherente con una función activa y no con una protección de avería.",
        ),
    ]
    variant["media"] = []
    write_json(path, topic)


def update_search() -> int:
    search = load(WEB / "search.json")
    topics = {5: load(WEB / "topics" / "5.json"), 24: load(WEB / "topics" / "24.json")}
    for row in search:
        topic_id = int(row.get("topic_id") or 0)
        if topic_id not in topics or int(row.get("id") or 0) not in {6, 37}:
            continue
        topic = topics[topic_id]
        variant = next(item for item in topic["variants"] if int(item["id"]) == int(row["id"]))
        parts = [
            topic["title"], topic["summary"], variant["title"], variant["recognition"],
            variant["purpose"], variant["summary"],
        ]
        parts.extend(item.get("title") or "" for item in variant["sections"])
        parts.extend(item.get("body") or "" for item in variant["sections"])
        parts.extend(item.get("instruction") or "" for item in variant["steps"])
        parts.extend(item.get("expected_result") or "" for item in variant["steps"])
        for parameter in variant.get("parameters") or []:
            parts.extend([parameter.get("parameter_code") or "", parameter.get("name") or "", parameter.get("description") or ""])
        row["summary"] = variant["summary"]
        row["haystack"] = normalize(" ".join(parts))
    write_json(WEB / "search.json", search)
    return len(search)


def update_metadata(search_count: int) -> None:
    navigation_path = WEB / "navigation.json"
    navigation = load(navigation_path)
    navigation["metadata"].update({
        "data_version": VERSION,
        "latest_phase": "Fujitsu V2 — display de estados y pulsadores exteriores",
        "last_processed_manual": "9378945593-02 / AOEG22KATA",
        "technical_library_review": "No quedan variantes técnicas parciales: se completan los estados normales VRF y la placa S130-S134.",
        "last_update_utc": "2026-07-16T15:30:00Z",
    })
    write_json(navigation_path, navigation)

    coverage_path = WEB / "coverage.json"
    coverage = load(coverage_path)
    for row in coverage:
        if row.get("area_slug") == "normal_states":
            row["notes"] = "Tabla y procedimiento para distinguir CL, Ht, or, dF, PC, Ln y Sn de los códigos E de avería."
        elif row.get("area_slug") == "configuration":
            row["notes"] = "Incluye reconocimiento seguro, indicadores, navegación y salida de la PCB S130-S134, además de ajustes locales y VRF."
    write_json(coverage_path, coverage)

    config_path = BRAND / "brand.json"
    config = load(config_path)
    config["data_version"] = VERSION
    config["counts"]["search_entries"] = search_count
    config["notes"] = "Fujitsu V2.18: completados los códigos normales VRF y el uso seguro de la placa exterior S130-S134."
    write_json(config_path, config)


def main() -> int:
    enrich_board_buttons()
    enrich_normal_status()
    search_count = update_search()
    update_metadata(search_count)
    report = audit_brand(BRAND)
    write_json(WEB / "quality.json", report)
    print(json.dumps({
        "version": VERSION,
        "search_entries": search_count,
        "error_statuses": report["errors"]["status_counts"],
        "variant_statuses": report["technical_variants"]["status_counts"],
        "remaining_partial_variants": [
            item["id"] for item in report["technical_variants"]["backlog"]
            if item["status"] in {"partial", "reference_only", "unverified"}
        ],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
