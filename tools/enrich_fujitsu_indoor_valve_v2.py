#!/usr/bin/env python3
"""Amplía Fujitsu V2 con agrupadores, mando de 2 hilos, damper y sondas de válvula.

La fuente principal es un manual de servicio del fabricante conservado por un
distribuidor técnico. La publicación web contiene únicamente resúmenes, valores
y referencias; no incorpora páginas ni imágenes del documento.
"""

from __future__ import annotations

import json
import re
import unicodedata
from copy import deepcopy
from pathlib import Path
from typing import Any

from audit_brand_quality import audit_brand, write as write_json


ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "data" / "brands" / "fujitsu-general"
WEB = BRAND / "web"
DETAILS = WEB / "errors" / "details"
VERSION = "2.12.0"

ORIGIN = "AOHG18_24KBTA3_SERVICE"
MANUAL_TITLE = "Service Manual — Fujitsu/General AOHG18/24KBTA3"
MANUAL_URL = (
    "https://server.bulclima.com/publicserver/FUJITSU%20GENERAL%20Air%20"
    "Conditioners%20and%20VRF/%D0%A1%D0%95%D0%A0%D0%92%D0%98%D0%97%D0%9D%D0%90%20"
    "%D0%94%D0%9E%D0%9A%D0%A3%D0%9C%D0%95%D0%9D%D0%A2%D0%90%D0%A6%D0%98%D0%AF/"
    "Service%20Manual%20R32/Service%20manual%20AOHG18-24KBTA3.pdf"
)
VRF_TITLE = "Installation Manual - AIRSTAGE VRF outdoor AJY/AJH072-162LALBH"
VRF_REF = "9378945593-02"
VRF_URL = (
    "https://webstore.uk.fujitsu-general.com/product/attachment/"
    "AJY108LALBH/installation%20manual.pdf"
)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(value: str) -> str:
    value = "".join(
        char for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    ).upper()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9]+", " ", value)).strip()


def service_source(page_start: str, page_end: str | None, section: str) -> dict[str, Any]:
    return {
        "title": MANUAL_TITLE,
        "document_ref": ORIGIN,
        "source_url": MANUAL_URL,
        "page_start": page_start,
        "page_end": page_end or page_start,
        "section": section,
    }


def vrf_source(page_start: str, page_end: str | None, section: str) -> dict[str, Any]:
    return {
        "title": VRF_TITLE,
        "document_ref": VRF_REF,
        "source_url": VRF_URL,
        "page_start": page_start,
        "page_end": page_end or page_start,
        "section": section,
    }


def info_items(
    interpretation_id: int,
    related: list[str],
    causes: list[str],
    checks: list[str],
    observations: list[str] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    order = 1
    for item_type, bodies in (
        ("related_element", related),
        ("cause", causes),
        ("check", checks),
        ("observation", observations or []),
    ):
        for body in bodies:
            rows.append({
                "id": 50000 + interpretation_id * 100 + order,
                "item_type": item_type,
                "title": None,
                "body": body,
                "sort_order": order,
                "review_status": "reviewed",
                "origin_ref": ORIGIN,
            })
            order += 1
    return rows


OUTDOOR_TEMP_CURVE = [
    (-30, 224.3, 0.73), (-25, 159.7, 0.97), (-20, 115.2, 1.25),
    (-15, 84.2, 1.56), (-10, 62.3, 1.90), (-5, 46.6, 2.26),
    (0, 35.2, 2.61), (5, 26.9, 2.94), (10, 20.7, 3.25),
    (15, 16.1, 3.52), (20, 12.6, 3.76), (25, 10.0, 3.97),
    (30, 8.0, 4.14), (35, 6.4, 4.28), (40, 5.2, 4.41),
    (45, 4.2, 4.51), (50, 3.5, 4.59), (55, 2.8, 4.65),
]


def sensor_dataset(dataset_id: int, title: str, value_index: int) -> dict[str, Any]:
    value_name, value_unit = (
        ("Resistencia", "kΩ") if value_index == 1 else ("Tensión", "V CC")
    )
    return {
        "id": dataset_id,
        "name": f"{title} — {value_name}",
        "dataset_type": "sensor_curve",
        "variable_name": "Temperatura",
        "variable_unit": "°C",
        "value_name": value_name,
        "value_unit": value_unit,
        "tolerance_text": None,
        "source_kind": "official",
        "calculation_method": None,
        "review_status": "reviewed",
        "notes": (
            "El procedimiento de E76 remite a esta curva oficial para la sonda de válvula. "
            "Debe usarse solo en la variante física descrita por este manual."
        ),
        "visible": 1,
        "points": [
            {
                "variable_value": temperature,
                "value_min": None,
                "value_nominal": values[value_index],
                "value_max": None,
                "value_text": None,
                "sort_order": order,
                "notes": None,
            }
            for order, values in enumerate(OUTDOOR_TEMP_CURVE)
            for temperature in [values[0]]
        ],
        "sources": [service_source("03-98", None, "6-2. Outdoor unit thermistor resistance values")],
        "origin_ref": ORIGIN,
    }


def power_dataset() -> dict[str, Any]:
    return {
        "id": 6050,
        "name": "Alimentación exterior VRF — rango documentado",
        "dataset_type": "technical_values",
        "variable_name": "Referencia",
        "variable_unit": None,
        "value_name": "Tensión entre fases",
        "value_unit": "V CA",
        "tolerance_text": "El manual exige 342–456 V para una alimentación nominal de 400 V trifásica.",
        "source_kind": "official",
        "calculation_method": None,
        "review_status": "reviewed",
        "notes": "La sección de cableado limita además la caída de tensión de la línea al 2 %.",
        "visible": 1,
        "points": [
            {"variable_value": "Mínimo", "value_min": None, "value_nominal": 342, "value_max": None, "value_text": None, "sort_order": 0, "notes": None},
            {"variable_value": "Nominal", "value_min": None, "value_nominal": 400, "value_max": None, "value_text": None, "sort_order": 1, "notes": None},
            {"variable_value": "Máximo", "value_min": None, "value_nominal": 456, "value_max": None, "value_text": None, "sort_order": 2, "notes": None},
        ],
        "sources": [vrf_source("En-12", "En-13", "6. Electrical wiring")],
        "origin_ref": ORIGIN,
    }


def related_error(error_id: int) -> dict[str, Any]:
    detail = load(DETAILS / f"{error_id}.json")
    return {
        "id": error_id,
        "code_display": detail["code_display"],
        "label": detail["short_label"],
    }


def set_grouping(error_id: int, targets: list[int], note: str) -> None:
    path = DETAILS / f"{error_id}.json"
    detail = load(path)
    interpretation = detail["interpretations"][0]
    interpretation["entry_role"] = "grouping_reference"
    interpretation["routing_note"] = note
    interpretation["related_errors"] = [related_error(target) for target in targets]
    write_json(path, detail)


def enrich_e57() -> None:
    path = DETAILS / "41.json"
    detail = load(path)
    old_sources = [
        row for row in detail["interpretations"][0].get("sources") or []
        if row.get("document_ref") != ORIGIN
    ]
    common_related = ["Compuerta de distribución de aire", "Final de carrera", "PCB principal interior"]

    first = {
        "id": 54,
        "title": "Fallo de detección de apertura o cierre de la compuerta",
        "description": (
            "La orden de abrir o cerrar no produce la confirmación esperada del final de carrera. "
            "Puede ocurrir en la posición de aire superior o en la de aire superior e inferior."
        ),
        "source_kind": "official",
        "confidence": "high",
        "review_status": "reviewed",
        "info_items": info_items(
            54,
            common_related + ["Conector CN18"],
            [
                "Final de carrera averiado o bloqueado por polvo.",
                "Contacto flojo en CN18 o cable pellizcado/cortocircuitado.",
                "Compuerta obstruida o mecanismo defectuoso.",
                "Fallo de la PCB principal interior.",
            ],
            [
                "Comprobar que el final de carrera cambia realmente entre ON y OFF; retirarlo y medir su conmutación con multímetro.",
                "Revisar CN18, contacto flojo, cable pellizcado y cortocircuito.",
                "Comprobar que la compuerta se mueve sin obstáculos y llega a sus posiciones finales.",
                "Sustituir el final de carrera o el conjunto de compuerta cuando la prueba correspondiente sea anormal.",
                "Si las comprobaciones mecánicas y de cableado son correctas, comprobar/sustituir la PCB principal.",
            ],
        ),
        "operational_impacts": [],
        "datasets": [],
        "sources": old_sources + [service_source("03-36", None, "2-20. Damper Open/Close detection limit switch error")],
    }
    second = {
        "id": 144,
        "title": "Detección simultánea de apertura y cierre de la compuerta",
        "description": "La entrada de la PCB recibe simultáneamente las confirmaciones de compuerta abierta y cerrada.",
        "source_kind": "official",
        "confidence": "high",
        "review_status": "reviewed",
        "info_items": info_items(
            144,
            common_related + ["Conector CN18"],
            [
                "Final de carrera averiado.",
                "Contacto flojo en CN18 o cable pellizcado/cortocircuitado.",
                "Fallo de la PCB principal interior.",
            ],
            [
                "Comprobar la conmutación ON/OFF del final de carrera con multímetro y descartar bloqueo por suciedad.",
                "Revisar CN18 y el cable en busca de contacto flojo, pellizco o cortocircuito.",
                "Sustituir el final de carrera si su conmutación o cableado son anormales.",
                "Si la entrada sigue indicando ambas posiciones, comprobar/sustituir la PCB principal.",
            ],
        ),
        "operational_impacts": [],
        "datasets": [],
        "sources": [service_source("03-37", None, "2-21. Damper simultaneous detection limit switch error")],
    }
    detail["short_label"] = "Error de compuerta y finales de carrera"
    detail["interpretations"] = [first, second]
    write_json(path, detail)


def valve_interpretation(
    interpretation_id: int,
    valve: str,
    page: str,
    dataset_base: int,
    old_sources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    title = f"Sonda de temperatura de válvula de {valve}"
    return {
        "id": interpretation_id,
        "title": title,
        "description": (
            f"La PCB detecta la sonda de la válvula de {valve} abierta o en cortocircuito "
            "al alimentar o mientras funciona el compresor."
        ),
        "source_kind": "official",
        "confidence": "high",
        "review_status": "reviewed",
        "info_items": info_items(
            interpretation_id,
            [title, "Cableado y conector de sonda", "PCB principal exterior"],
            [
                "Conector suelto, retirado o conectado de forma incorrecta.",
                "Cable de la sonda abierto.",
                "Sonda NTC abierta o en cortocircuito.",
                "Fallo de la entrada de medida de la PCB principal.",
            ],
            [
                "Revisar el conector, la colocación correcta y la continuidad del cable; volver a alimentar después de corregir una desconexión.",
                "Desconectar la sonda y comparar su resistencia con la curva oficial a la temperatura real.",
                "Si la sonda está abierta o cortocircuitada, sustituirla y reiniciar la alimentación.",
                "Comprobar en el terminal de la sonda que la PCB proporciona aproximadamente 5,0 V CC.",
                "Si no aparece la tensión de referencia después de descartar cableado y sonda, comprobar/sustituir la PCB principal.",
            ],
            [
                "En el esquema de esta familia las sondas de válvula se agrupan en los conectores P6/P7; no extrapolar esa identificación a otras placas.",
                "El propio procedimiento remite a la curva denominada 'Outdoor temperature thermistor' para verificar esta sonda.",
            ],
        ),
        "operational_impacts": [],
        "datasets": [
            sensor_dataset(dataset_base, title, 1),
            sensor_dataset(dataset_base + 1, title, 2),
        ],
        "sources": (old_sources or []) + [
            service_source(page, None, f"E76. {valve} valve thermistor error"),
            service_source("02-111", None, "7-6. Outdoor unit wiring diagram"),
            service_source("03-98", None, "6-2. Outdoor unit thermistor resistance values"),
        ],
    }


def enrich_e76() -> None:
    path = DETAILS / "45.json"
    detail = load(path)
    old_sources = [
        row for row in detail["interpretations"][0].get("sources") or []
        if row.get("document_ref") != ORIGIN
    ]
    detail["short_label"] = "Error de sonda de válvula de 2 o 3 vías"
    detail["interpretations"] = [
        valve_interpretation(66, "2 vías", "03-47", 6040, old_sources),
        valve_interpretation(145, "3 vías", "03-48", 6042),
    ]
    write_json(path, detail)


def enrich_e612() -> None:
    path = DETAILS / "68.json"
    detail = load(path)
    interpretation = detail["interpretations"][0]
    interpretation["description"] = (
        "La unidad exterior VRF detecta una tensión de alimentación inferior a la admitida. "
        "En esta familia la alimentación nominal es 400 V trifásica y el rango documentado es 342–456 V."
    )
    interpretation["info_items"] = info_items(
        int(interpretation["id"]),
        ["Alimentación trifásica exterior", "Cable y terminales de potencia", "Protección y cuadro eléctrico"],
        [
            "Tensión de red inferior al rango admitido o caída durante el arranque.",
            "Sección insuficiente o longitud excesiva del cable, con caída de tensión superior al 2 %.",
            "Terminal, anillo o conexión de potencia flojos.",
            "Capacidad insuficiente de la red o protección eléctrica inadecuada.",
        ],
        [
            "Medir la tensión entre fases en la entrada de la exterior, primero en reposo y después durante el intento de arranque; debe permanecer entre 342 y 456 V CA.",
            "Confirmar que la alimentación corresponde a 400 V, trifásica, 4 hilos y 50 Hz.",
            "Revisar terminales, anillos, apriete, calentamiento y estado del cable de potencia.",
            "Comprobar sección y longitud del cable; el manual exige diseñar la línea para una caída inferior al 2 %.",
            "Verificar que cada exterior dispone de su propio interruptor/protección y que la capacidad corresponde a la instalación.",
            "Si la tensión permanece dentro del rango y el error continúa, este manual de instalación no aporta diagnóstico interno de placa; debe continuarse con el manual de servicio de esa familia.",
        ],
        ["No confundir con E61.5, que corresponde a inversión, ausencia de fase o error de cableado."],
    )
    interpretation["datasets"] = [power_dataset()]
    interpretation["sources"] = [
        row for row in interpretation.get("sources") or []
        if not (row.get("document_ref") == VRF_REF and row.get("section") == "6. Electrical wiring")
    ] + [vrf_source("En-12", "En-13", "6. Electrical wiring")]
    write_json(path, detail)


def new_error(
    error_id: int,
    interpretation_id: int,
    code: str,
    label: str,
    description: str,
    blink_operation: int,
    blink_timer: int,
    related: list[str],
    causes: list[str],
    checks: list[str],
    page: str,
    section: str,
) -> dict[str, Any]:
    compact = code.replace(" ", "")
    return {
        "id": error_id,
        "code_display": f"E: {code}",
        "code_normalized": f"E{compact}",
        "indication_type": "remote_controller",
        "unit_scope": "indoor",
        "short_label": label,
        "aliases": [
            {"alias_display": code, "alias_normalized": compact},
            {"alias_display": f"E{compact}", "alias_normalized": f"E{compact}"},
            {
                "alias_display": f"{blink_operation} parpadeos operación + {blink_timer} parpadeos temporizador",
                "alias_normalized": normalize(f"{blink_operation} parpadeos operación {blink_timer} parpadeos temporizador"),
            },
        ],
        "tags": [],
        "interpretations": [{
            "id": interpretation_id,
            "title": label,
            "description": description,
            "source_kind": "official",
            "confidence": "high",
            "review_status": "reviewed",
            "info_items": info_items(interpretation_id, related, causes, checks),
            "operational_impacts": [],
            "datasets": [],
            "sources": [service_source(page, None, section)],
        }],
        "media": [],
    }


def add_new_errors() -> None:
    errors = [
        new_error(
            111, 146, "26", "Error de dirección del mando cableado",
            "En un grupo de mando de 2 hilos se han mezclado direcciones automáticas y manuales, o existe una dirección duplicada.",
            2, 6,
            ["Grupo de mando cableado de 2 hilos", "Direcciones de unidad interior", "PCB principal interior"],
            [
                "Cableado incorrecto del grupo de mando.",
                "Mezcla de dirección automática 00 con direcciones manuales distintas de 00.",
                "Dirección duplicada dentro del mismo grupo.",
                "Fallo del mando o de la PCB principal interior.",
            ],
            [
                "Revisar el cableado completo del grupo según el manual de instalación.",
                "Comprobar que un mismo grupo no mezcla dirección automática 00 y direcciones manuales.",
                "Comprobar que no existe ninguna dirección repetida.",
                "Corregir las direcciones y volver a inicializar el grupo.",
                "Si el ajuste y el cableado son correctos, inspeccionar la PCB y repetir la configuración después de sustituirla.",
            ],
            "03-23", "2-7. Address setting error in wired remote controller",
        ),
        new_error(
            112, 147, "29", "Exceso de unidades conectadas al grupo de mando",
            "El número de unidades interiores conectadas al mando de 2 hilos supera el límite admitido por esa configuración.",
            2, 9,
            ["Grupo de mando cableado de 2 hilos", "Unidades interiores y mandos", "PCB principal interior"],
            [
                "Número o agrupación incorrectos de unidades interiores/mandos.",
                "Cableado del grupo conectado de forma incorrecta.",
                "Fallo de la PCB principal interior.",
            ],
            [
                "Contar las unidades interiores y mandos conectados al grupo y compararlo con el límite del manual de esa interfaz.",
                "Revisar la topología y el cableado del grupo; separar o corregir conexiones si excede el límite.",
                "Después de corregir la agrupación, reinicializar y comprobar el código.",
                "Si el número y el cableado son correctos, inspeccionar/comprobar la PCB principal interior.",
            ],
            "03-24", "2-8. Connected unit number error",
        ),
        new_error(
            113, 148, "3A", "Comunicación interna entre PCB principal y PCB de mando",
            "El sistema de mando de 2 hilos detecta un fallo de comunicación entre el microprocesador de la PCB principal interior y la PCB de comunicación.",
            3, 10,
            ["PCB de comunicación de 2 hilos", "PCB principal interior", "Conexión entre ambas placas"],
            ["Conexión entre placas floja o incorrecta.", "PCB de comunicación defectuosa.", "PCB principal interior defectuosa."],
            [
                "Cortar la alimentación antes de manipular las placas.",
                "Revisar y corregir la conexión entre la PCB de comunicación y la PCB principal interior.",
                "Si la conexión es correcta, sustituir la PCB de comunicación y volver a probar.",
                "Si el fallo continúa, comprobar/sustituir la PCB principal interior.",
            ],
            "03-29", "2-13. Indoor unit communication circuit error",
        ),
    ]
    for error in errors:
        write_json(DETAILS / f"{error['id']}.json", error)


def add_grouping_routes() -> None:
    set_grouping(
        36, [1, 2],
        "Este código antiguo no distingue el sentido de la comunicación. Abra las dos variantes documentadas y compruebe cuál coincide con la detección de su equipo.",
    )
    set_grouping(
        35, [1, 2, 3, 34, 5, 6, 111, 112, 7, 8, 9, 113, 11, 12, 13],
        "E5U no identifica un componente: obliga a consultar el código interior asociado. Las opciones mostradas son las que el manual de servicio enumera expresamente.",
    )
    e5u_path = DETAILS / "35.json"
    e5u = load(e5u_path)
    e5u_source = service_source("03-39", None, "2-23. Indoor unit error")
    if not any(row.get("document_ref") == ORIGIN for row in e5u["interpretations"][0].get("sources") or []):
        e5u["interpretations"][0]["sources"].append(e5u_source)
    write_json(e5u_path, e5u)
    set_grouping(
        42, [35],
        "En esta generación, E5F solo informa de que existe un error interior. Abra E5U para acceder a las variantes interiores documentadas; no trate E5F como un componente averiado.",
    )
    set_grouping(
        67, [35],
        "El display exterior VRF está remitiendo a una avería de unidad interior. Abra el agrupador E5U y obtenga después el código concreto en la unidad o su mando.",
    )


def component_topic() -> dict[str, Any]:
    return {
        "id": 32,
        "brand_id": 2,
        "category_id": 9,
        "slug": "damper-valve-sensor-checks",
        "title": "Compuertas y sondas de válvula",
        "summary": "Pruebas directas de finales de carrera, mecanismos de compuerta y sondas NTC instaladas en válvulas.",
        "active": 1,
        "category": {"id": 9, "slug": "component_checks", "name": "Comprobación de componentes"},
        "variants": [
            {
                "id": 49,
                "topic_id": 32,
                "title": "Comprobar compuerta y finales de carrera",
                "recognition": "Unidad interior con compuerta superior/inferior, final de carrera y conector CN18; normalmente asociada a E57.",
                "system_type": "indoor_unit",
                "unit_scope": "indoor",
                "refrigerant": None,
                "purpose": "Distinguir bloqueo mecánico, final de carrera, cableado y PCB.",
                "summary": "El mismo E57 puede significar que no se alcanza una posición o que se detectan apertura y cierre simultáneamente.",
                "source_kind": "official",
                "review_status": "reviewed",
                "sort_order": 10,
                "visible": 1,
                "sections": [
                    {"section_type": "recognition", "title": "Dos formas de detección", "body": "Variante 1: la compuerta no confirma la posición ordenada. Variante 2: la PCB recibe a la vez las señales de abierta y cerrada.", "collapsed_default": 0},
                    {"section_type": "wiring", "title": "Conexión documentada", "body": "El manual identifica CN18 para el final de carrera en esta familia. Debe comprobarse la serigrafía antes de usar ese conector en otra placa.", "collapsed_default": 1},
                ],
                "steps": [
                    {"phase": "safety", "step_no": 1, "instruction": "Cortar alimentación antes de desconectar el final de carrera o manipular CN18.", "expected_result": None, "warning_level": "danger"},
                    {"phase": "check", "step_no": 2, "instruction": "Comprobar que la compuerta se mueve libremente y no está bloqueada por polvo u objetos.", "expected_result": "Recorrido completo sin atascos.", "warning_level": "warning"},
                    {"phase": "check", "step_no": 3, "instruction": "Retirar el final de carrera y medir que conmuta entre ON y OFF.", "expected_result": "Cambio claro de continuidad al accionarlo.", "warning_level": "warning"},
                    {"phase": "check", "step_no": 4, "instruction": "Revisar CN18 y el cableado por contacto flojo, pellizco o cortocircuito.", "expected_result": "Conexión firme y conductores aislados.", "warning_level": "warning"},
                    {"phase": "interpretation", "step_no": 5, "instruction": "Si mecanismo, final y cableado son correctos, continuar con la PCB principal.", "expected_result": None, "warning_level": "caution"},
                ],
                "parameters": [], "controller": None, "monitoring_points": [], "media": [],
                "sources": [service_source("03-36", "03-37", "E57. Damper limit switch errors")],
            },
            {
                "id": 50,
                "topic_id": 32,
                "title": "Comprobar sondas de válvula de 2 y 3 vías",
                "recognition": "Multisplit exterior con sondas NTC sujetas a válvulas y código E76.",
                "system_type": "multisplit",
                "unit_scope": "outdoor",
                "refrigerant": "R32",
                "purpose": "Separar sonda, cableado y circuito de lectura de la PCB.",
                "summary": "La detección se produce por sonda abierta o cortocircuitada al alimentar o durante el funcionamiento del compresor.",
                "source_kind": "official",
                "review_status": "reviewed",
                "sort_order": 20,
                "visible": 1,
                "sections": [
                    {"section_type": "electrical", "title": "Referencia de la PCB", "body": "El manual indica aproximadamente 5,0 V CC en el terminal de la sonda. Si falta después de descartar cableado y NTC, dirige a la PCB principal.", "collapsed_default": 0},
                    {"section_type": "curve", "title": "Punto de referencia útil", "body": "En esta curva: 10,0 kΩ y 3,97 V a 25 °C. La ficha E76 contiene la tabla completa de -30 a 55 °C.", "collapsed_default": 0},
                    {"section_type": "wiring", "title": "Pista de reconocimiento", "body": "El esquema de esta familia agrupa las sondas de válvula en P6/P7. Verifique siempre serigrafía y esquema antes de medir otra placa.", "collapsed_default": 1},
                ],
                "steps": [
                    {"phase": "safety", "step_no": 1, "instruction": "Cortar alimentación antes de desconectar la sonda.", "expected_result": None, "warning_level": "danger"},
                    {"phase": "check", "step_no": 2, "instruction": "Revisar conector, posición correcta y continuidad del cable.", "expected_result": "Sin falsos contactos ni circuito abierto.", "warning_level": "warning"},
                    {"phase": "check", "step_no": 3, "instruction": "Desconectar la NTC y medir su resistencia a la temperatura real.", "expected_result": "Valor coherente con la curva E76.", "warning_level": "warning"},
                    {"phase": "check", "step_no": 4, "instruction": "Con las precauciones eléctricas necesarias, comprobar la referencia de la PCB en el terminal de sonda.", "expected_result": "Aproximadamente 5,0 V CC.", "warning_level": "danger"},
                    {"phase": "interpretation", "step_no": 5, "instruction": "Sonda abierta/cortocircuitada: sustituir y reiniciar. Referencia ausente con cableado correcto: continuar con la PCB.", "expected_result": None, "warning_level": "caution"},
                ],
                "parameters": [], "controller": None, "monitoring_points": [], "media": [],
                "sources": [
                    service_source("03-47", "03-48", "E76. Valve thermistor errors"),
                    service_source("02-111", None, "Outdoor unit wiring diagram"),
                    service_source("03-98", None, "Outdoor thermistor resistance values"),
                ],
            },
        ],
    }


def refresh_catalogs() -> tuple[int, int]:
    detail_rows = [load(path) for path in sorted(DETAILS.glob("*.json"), key=lambda path: int(path.stem))]
    old_index = {int(row["id"]): row for row in load(WEB / "errors" / "index.json")}
    index: list[dict[str, Any]] = []
    error_search: list[dict[str, Any]] = []

    for detail in detail_rows:
        error_id = int(detail["id"])
        text: list[str] = [
            str(detail.get("code_display") or ""), str(detail.get("code_normalized") or ""),
            str(detail.get("short_label") or ""),
        ]
        for alias in detail.get("aliases") or []:
            text.extend([str(alias.get("alias_display") or ""), str(alias.get("alias_normalized") or "")])
        for interpretation in detail.get("interpretations") or []:
            text.extend([str(interpretation.get("title") or ""), str(interpretation.get("description") or ""), str(interpretation.get("routing_note") or "")])
            for related in interpretation.get("related_errors") or []:
                text.extend([str(related.get("code_display") or ""), str(related.get("label") or "")])
            text.extend(str(item.get("body") or "") for item in interpretation.get("info_items") or [])
            for dataset in interpretation.get("datasets") or []:
                text.extend([str(dataset.get("name") or ""), str(dataset.get("notes") or "")])
        haystack = normalize(" ".join(text))
        row = deepcopy(old_index.get(error_id) or {})
        row.update({
            "id": error_id,
            "code_display": detail["code_display"],
            "code_normalized": detail["code_normalized"],
            "indication_type": detail["indication_type"],
            "unit_scope": detail["unit_scope"],
            "short_label": detail["short_label"],
            "interpretation_count": len(detail.get("interpretations") or []),
            "search_text": haystack,
        })
        index.append(row)
        first = (detail.get("interpretations") or [{}])[0]
        error_search.append({
            "type": "error", "id": error_id, "topic_id": None,
            "category_slug": "errors", "category": "Errores y protecciones",
            "title": detail["short_label"],
            "summary": first.get("description") or detail["short_label"],
            "haystack": haystack,
        })

    index.sort(key=lambda row: (str(row["code_normalized"]), int(row["id"])))
    technical_search = [row for row in load(WEB / "search.json") if row.get("type") != "error"]
    topic = load(WEB / "topics" / "32.json")
    technical_search = [row for row in technical_search if int(row.get("topic_id") or 0) != 32]
    for variant in topic["variants"]:
        parts = [topic["title"], topic["summary"], variant["title"], variant["recognition"], variant["purpose"], variant["summary"]]
        parts.extend(section.get("body") or "" for section in variant.get("sections") or [])
        parts.extend(step.get("instruction") or "" for step in variant.get("steps") or [])
        technical_search.append({
            "type": "technical", "id": int(variant["id"]), "topic_id": 32,
            "category_slug": "component_checks", "category": "Comprobación de componentes",
            "title": variant["title"], "summary": variant["summary"],
            "haystack": normalize(" ".join(parts)),
        })
    search = error_search + technical_search
    write_json(WEB / "errors" / "index.json", index)
    write_json(WEB / "search.json", search)
    return len(index), len(search)


def update_metadata(error_count: int, search_count: int) -> None:
    topic = component_topic()
    write_json(WEB / "topics" / "32.json", topic)

    navigation_path = WEB / "navigation.json"
    navigation = load(navigation_path)
    navigation["metadata"].update({
        "data_version": VERSION,
        "latest_phase": "Fujitsu V2 — agrupadores, damper, alimentación y sondas de válvula",
        "last_processed_manual": ORIGIN,
        "technical_library_review": "E26/E29/E3A, E57, E61.2 y E76 desarrollados; E11/E5F/E5U enlazados a variantes exactas.",
        "last_update_utc": "2026-07-16T14:30:00Z",
    })
    category = next(row for row in navigation["categories"] if int(row["id"]) == 9)
    category["topics"] = [row for row in category.get("topics") or [] if int(row["id"]) != 32]
    category["topics"].append({
        "id": 32, "slug": topic["slug"], "title": topic["title"],
        "summary": topic["summary"], "active": 1, "variant_count": len(topic["variants"]),
    })
    write_json(navigation_path, navigation)

    variant_map_path = WEB / "variant_map.json"
    variant_map = load(variant_map_path)
    variant_map.update({"49": 32, "50": 32})
    write_json(variant_map_path, variant_map)

    sources_path = WEB / "sources.json"
    sources = [row for row in load(sources_path) if row.get("document_ref") != ORIGIN]
    sources.append({
        "id": 18,
        "title": MANUAL_TITLE,
        "document_ref": ORIGIN,
        "publication_date": "2022-08-08",
        "language": "en",
        "document_type": "service_manual",
        "source_url": MANUAL_URL,
        "status": "reviewed",
        "notes": (
            "Documento técnico del fabricante conservado por un distribuidor. Se resumen diagnósticos 03-23 a 03-48, "
            "curva 03-98 y esquema 02-111; no se publican páginas ni imágenes."
        ),
    })
    write_json(sources_path, sources)

    coverage_path = WEB / "coverage.json"
    coverage = load(coverage_path)
    for row in coverage:
        row["source_count"] = len(sources)
        if row.get("area_slug") == "errors":
            row["notes"] = "Fujitsu V2 incluye agrupadores navegables, subcódigos VR-II y nuevos diagnósticos de mando, compuerta, baja tensión y sondas de válvula. Permanecen huecos documentales explícitos en la auditoría."
        elif row.get("area_slug") == "component_checks":
            row["coverage_status"] = "partial"
            row["notes"] = "Incluye ahora comprobación directa de compuertas/finales de carrera y sondas de válvula, además de curvas, presiones, EEV, ventiladores e inverter de otras familias."
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
    config["notes"] = "Fujitsu V2.12: agrupadores navegables y diagnósticos completos de E26, E29, E3A, E57, E61.2 y E76."
    write_json(config_path, config)


def main() -> int:
    add_new_errors()
    add_grouping_routes()
    enrich_e57()
    enrich_e76()
    enrich_e612()
    write_json(WEB / "topics" / "32.json", component_topic())
    error_count, search_count = refresh_catalogs()
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
