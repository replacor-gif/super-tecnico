#!/usr/bin/env python3
"""Añade seguridad interior y diagnóstico sin código a Fujitsu V2.

La fuente es el manual de servicio AOHG18/24KBTA3 ya registrado. La salida
pública contiene únicamente resúmenes técnicos y referencias, nunca páginas
ni imágenes del manual.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from audit_brand_quality import audit_brand, write as write_json
from enrich_fujitsu_indoor_valve_v2 import (
    BRAND,
    DETAILS,
    MANUAL_TITLE,
    MANUAL_URL,
    ORIGIN,
    WEB,
    info_items,
    load,
    normalize,
    refresh_catalogs,
    service_source,
)


VERSION = "2.13.0"


def impact(
    impact_id: int,
    stop_level: str,
    summary: str,
    affected_scope: str,
    restart_behavior: str | None = None,
    degraded_behavior: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    return {
        "id": impact_id,
        "stop_level": stop_level,
        "summary": summary,
        "affected_scope": affected_scope,
        "unaffected_scope": None,
        "restart_behavior": restart_behavior,
        "degraded_behavior": degraded_behavior,
        "notes": notes,
        "review_status": "reviewed",
    }


def aliases(code: str, operation_flashes: int, timer_flashes: int) -> list[dict[str, str]]:
    compact = code.replace(" ", "")
    blink = f"{operation_flashes} parpadeos operación + {timer_flashes} parpadeos temporizador"
    return [
        {"alias_display": code, "alias_normalized": compact},
        {"alias_display": f"E{compact}", "alias_normalized": f"E{compact}"},
        {"alias_display": blink, "alias_normalized": normalize(blink)},
    ]


def add_error_details() -> None:
    e45 = {
        "id": 114,
        "code_display": "E: 45",
        "code_normalized": "E45",
        "indication_type": "remote_controller",
        "unit_scope": "indoor",
        "short_label": "Fallo o deterioro del sensor de fuga de refrigerante",
        "aliases": aliases("45", 4, 5),
        "tags": ["sensor de fuga", "seguridad", "unidad interior"],
        "interpretations": [
            {
                "id": 149,
                "title": "Fallo eléctrico del sensor de fuga de refrigerante",
                "description": (
                    "El sensor está abierto, en cortocircuito o la PCB detecta una tensión anormal "
                    "en su circuito de excitación. Esta variante detiene el sistema."
                ),
                "source_kind": "official",
                "confidence": "high",
                "review_status": "reviewed",
                "info_items": info_items(
                    149,
                    ["Sensor de fuga de refrigerante", "Conector y mazo del sensor", "Circuito de lectura interior"],
                    [
                        "Conector flojo, retirado o conectado de forma incorrecta.",
                        "Cable del sensor abierto.",
                        "Sensor de fuga deteriorado o averiado.",
                    ],
                    [
                        "Cortar la alimentación antes de manipular el conector del sensor.",
                        "Revisar que el conector esté firme y correctamente colocado.",
                        "Comprobar continuidad del mazo y descartar circuito abierto.",
                        "Restablecer alimentación después de corregir conexión o cableado.",
                        "Si el cableado es correcto y la anomalía continúa, sustituir el sensor.",
                    ],
                    ["No confundir esta avería eléctrica E45 con EA8, que indica refrigerante detectado por el sensor."],
                ),
                "operational_impacts": [impact(
                    14901,
                    "all_system",
                    "El manual indica que el sistema queda detenido.",
                    "Frío y calor del sistema asociado",
                    "Corregir conexión/cableado o sustituir el sensor y volver a alimentar.",
                )],
                "datasets": [],
                "sources": [service_source("03-32", None, "2-16. Refrigerant leakage sensor error")],
            },
            {
                "id": 150,
                "title": "Sensor de fuga deteriorado o al final de su vida útil",
                "description": (
                    "El mismo E45 también puede avisar del deterioro o vencimiento del sensor. "
                    "El manual permite funcionamiento durante un periodo limitado."
                ),
                "source_kind": "official",
                "confidence": "high",
                "review_status": "reviewed",
                "info_items": info_items(
                    150,
                    ["Sensor de fuga de refrigerante", "Control de vida útil del sensor"],
                    ["Envejecimiento, deterioro o vencimiento de la vida de servicio del sensor."],
                    [
                        "Identificar que se trata del aviso de deterioro y no de una fuga EA8.",
                        "Sustituir el sensor de fuga de refrigerante.",
                        "Mantener la periodicidad de sustitución indicada para el sensor de la familia concreta.",
                    ],
                    ["El manual no publica en esta sección una duración universal del periodo de funcionamiento restante."],
                ),
                "operational_impacts": [impact(
                    15001,
                    "degraded",
                    "Se permite funcionamiento durante un periodo limitado antes de sustituir el sensor.",
                    "Supervisión de seguridad del sistema",
                    degraded_behavior="El equipo puede seguir funcionando temporalmente; no debe interpretarse como permiso para aplazar indefinidamente la sustitución.",
                )],
                "datasets": [],
                "sources": [service_source("03-33", None, "2-17. Refrigerant leakage sensor deterioration")],
            },
        ],
        "media": [],
    }

    e58 = {
        "id": 115,
        "code_display": "E: 58",
        "code_normalized": "E58",
        "indication_type": "remote_controller",
        "unit_scope": "indoor",
        "short_label": "Fallo de rejilla de aspiración o su microinterruptor",
        "aliases": aliases("58", 5, 8),
        "tags": ["rejilla", "microinterruptor", "CN11"],
        "interpretations": [{
            "id": 151,
            "title": "Microinterruptor de rejilla abierto durante el funcionamiento del compresor",
            "description": (
                "La PCB interior detecta abierto el microinterruptor de seguridad de la rejilla "
                "mientras el compresor está funcionando."
            ),
            "source_kind": "official",
            "confidence": "high",
            "review_status": "reviewed",
            "info_items": info_items(
                151,
                ["Rejilla de aspiración", "Microinterruptor de seguridad", "Conector CN11", "PCB principal interior"],
                [
                    "Microinterruptor averiado o bloqueado por polvo.",
                    "Cable o conector CN11 flojo, pellizcado o en cortocircuito.",
                    "Fallo de la PCB principal interior.",
                ],
                [
                    "Cortar alimentación antes de desmontar la rejilla o desconectar CN11.",
                    "Comprobar que la rejilla acciona correctamente el microinterruptor y que no hay suciedad bloqueándolo.",
                    "Desmontar el microinterruptor y comprobar con un multímetro que conmuta entre ON y OFF.",
                    "Revisar contacto de CN11 y buscar cable pellizcado o cortocircuitado.",
                    "Si interruptor, conector y cable son correctos, comprobar/sustituir la PCB principal.",
                ],
            ),
            "operational_impacts": [],
            "datasets": [],
            "sources": [service_source("03-38", None, "2-22. Intake grille error")],
        }],
        "media": [],
    }

    ea8 = {
        "id": 116,
        "code_display": "E: A8",
        "code_normalized": "EA8",
        "indication_type": "remote_controller",
        "unit_scope": "indoor",
        "short_label": "Fuga de refrigerante detectada por el sensor interior",
        "aliases": aliases("A8", 10, 8),
        "tags": ["fuga de refrigerante", "seguridad", "ventilación forzada"],
        "interpretations": [{
            "id": 152,
            "title": "Concentración de refrigerante detectada",
            "description": (
                "El sensor interior ha detectado refrigerante. Se bloquean frío y calor, "
                "pero la ventilación de mezcla de seguridad permanece activa y no puede detenerse."
            ),
            "source_kind": "official",
            "confidence": "high",
            "review_status": "reviewed",
            "info_items": info_items(
                152,
                ["Sensor de fuga de refrigerante", "Circuito frigorífico", "Ventilador interior de seguridad"],
                ["Fuga de refrigerante detectada en el ambiente de la unidad interior."],
                [
                    "No anular ni detener la ventilación de mezcla de seguridad.",
                    "Localizar la fuga y realizar la corrección técnica antes de intentar recuperar el servicio.",
                    "Una vez corregida la fuga y comprobada la seguridad, cortar y restablecer la alimentación para liberar el error.",
                    "Si vuelve a detectarse refrigerante después del rearme, el error se genera de nuevo.",
                    "Sustituir el sensor si ha estado expuesto a una concentración alta o a exposiciones repetidas y no recupera su funcionamiento.",
                ],
                [
                    "Aunque la concentración baje, el error no se borra sin volver a alimentar.",
                    "EA8 confirma detección de refrigerante; E45 identifica fallo eléctrico o deterioro del propio sensor.",
                ],
            ),
            "operational_impacts": [impact(
                15201,
                "all_system",
                "Frío y calor quedan detenidos; el ventilador mantiene una operación de mezcla por seguridad.",
                "Compresor y climatización del sistema asociado",
                "Solo se libera al volver a alimentar después de corregir la fuga; si se detecta de nuevo, reaparece.",
                "La ventilación interior de seguridad continúa y no puede detenerse.",
                "No debe puentearse el sensor ni anularse la ventilación de seguridad.",
            )],
            "datasets": [],
            "sources": [service_source("03-62", None, "2-42. Refrigerant leakage sensor error")],
        }],
        "media": [],
    }

    for detail in (e45, e58, ea8):
        write_json(DETAILS / f"{detail['id']}.json", detail)


def enrich_e39_source() -> None:
    path = DETAILS / "10.json"
    detail = load(path)
    interpretation = detail["interpretations"][0]
    interpretation["info_items"] = [
        row for row in interpretation.get("info_items") or []
        if row.get("origin_ref") != f"{ORIGIN}_E39"
    ]
    interpretation["info_items"].extend([
        {
            "id": 55101,
            "item_type": "observation",
            "title": None,
            "body": "La detección se activa ante un corte momentáneo o cuando el motor ventilador interior no inicia el giro.",
            "sort_order": 20,
            "review_status": "reviewed",
            "origin_ref": f"{ORIGIN}_E39",
        },
        {
            "id": 55102,
            "item_type": "check",
            "title": None,
            "body": "Después de corregir un conector retirado o una conexión errónea, restablecer la alimentación y volver a comprobar.",
            "sort_order": 21,
            "review_status": "reviewed",
            "origin_ref": f"{ORIGIN}_E39",
        },
    ])
    interpretation["sources"] = [
        row for row in interpretation.get("sources") or []
        if not (row.get("document_ref") == ORIGIN and row.get("page_start") == "03-28")
    ] + [service_source("03-28", None, "2-12. Indoor unit power supply error for fan motor")]
    write_json(path, detail)


def variant(
    variant_id: int,
    topic_id: int,
    title: str,
    recognition: str,
    purpose: str,
    summary: str,
    sections: list[dict[str, Any]],
    steps: list[dict[str, Any]],
    page_start: str,
    page_end: str | None,
    section: str,
    sort_order: int,
) -> dict[str, Any]:
    return {
        "id": variant_id,
        "topic_id": topic_id,
        "title": title,
        "recognition": recognition,
        "system_type": "split / comercial",
        "unit_scope": "system",
        "refrigerant": "R32",
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
        "sources": [service_source(page_start, page_end, section)],
    }


def step(no: int, instruction: str, expected: str | None = None, level: str = "warning") -> dict[str, Any]:
    return {
        "phase": "check" if no > 1 else "safety",
        "step_no": no,
        "instruction": instruction,
        "expected_result": expected,
        "warning_level": level,
    }


def symptom_topic() -> dict[str, Any]:
    variants = [
        variant(
            51, 33, "Unidad interior sin alimentación",
            "La unidad interior no muestra indicadores ni responde y no existe un código activo.",
            "Separar alimentación ausente, caída/ruido eléctrico, fusible, varistor y cableado.",
            "La familia documentada se alimenta desde la exterior y pide verificar 198–264 V CA en L–N antes de intervenir en la PCB de filtro.",
            [
                {"section_type": "electrical", "title": "Tensión documentada", "body": "Comprobar 198–264 V CA en L–N de la unidad exterior. Este punto pertenece a la arquitectura del manual y no debe extrapolarse sin revisar el esquema del equipo.", "collapsed_default": 0},
                {"section_type": "interpretation", "title": "Fusible y varistor", "body": "Fusible abierto: revisar primero el cableado entre bornera y PCB de filtro. Varistor dañado: sospechar alimentación anormal, corregirla y sustituir el varistor.", "collapsed_default": 1},
            ],
            [
                step(1, "Aplicar procedimientos de seguridad eléctrica antes de abrir cajas o tocar la PCB.", level="danger"),
                step(2, "Revisar magnetotérmico, conexiones flojas y cable retirado.", "Alimentación y cableado firmes."),
                step(3, "Buscar grandes cargas, contactos defectuosos, fugas, armónicos y puesta a tierra deficiente.", "Sin caída instantánea, microcorte ni fuente de ruido."),
                step(4, "Medir L–N en la unidad exterior con el equipo energizado y protección adecuada.", "198–264 V CA.", "danger"),
                step(5, "Cortar alimentación y revisar fusible, cableado y varistor de la PCB de filtro.", "Componentes y conexiones sin daño.", "danger"),
            ],
            "03-63", None, "3-1. Indoor unit—No power", 10,
        ),
        variant(
            52, 33, "Unidad exterior sin alimentación",
            "La unidad exterior no muestra actividad y no existe un código disponible.",
            "Distinguir red eléctrica, fusible, módulo de filtro activo/IPM y PCB principal.",
            "El procedimiento oficial empieza por 198–264 V CA en L–N y avanza desde fusible y potencia hasta la PCB principal.",
            [
                {"section_type": "electrical", "title": "Tensión documentada", "body": "La familia del manual requiere 198–264 V CA en L–N. Confirmar siempre la alimentación nominal de la placa concreta.", "collapsed_default": 0},
                {"section_type": "warning", "title": "Etapa de potencia", "body": "El filtro activo y el IPM trabajan con tensiones peligrosas y pueden conservar carga. Su comprobación exige competencia y equipos adecuados.", "collapsed_default": 0},
            ],
            [
                step(1, "Aplicar descarga y seguridad de la etapa de potencia antes de manipular la exterior.", level="danger"),
                step(2, "Revisar magnetotérmico, bornes y cable de alimentación.", "Conexiones correctas."),
                step(3, "Descartar caída instantánea, microcorte, armónicos y puesta a tierra deficiente."),
                step(4, "Medir L–N con protección adecuada.", "198–264 V CA.", "danger"),
                step(5, "Cortar alimentación y comprobar fusible de la PCB principal y su cableado.", "Fusible y conductores correctos.", "danger"),
                step(6, "Comprobar módulo de filtro activo e IPM según el procedimiento específico de la placa.", "Sin cortocircuitos ni anomalías.", "danger"),
                step(7, "Si todo lo anterior es correcto, continuar con la PCB principal.", level="caution"),
            ],
            "03-64", None, "3-2. Outdoor unit—No power", 20,
        ),
        variant(
            53, 33, "Hay alimentación, pero la máquina no funciona",
            "Unidades o mando alimentados, sin arranque y sin un código que explique el bloqueo.",
            "Comprobar compatibilidad, cableado, ruido y alimentación del mando antes de sustituir placas.",
            "La tensión del mando permite separar fallo del mando y fallo de la placa: 12 V o 13 V CC según interfaz; 0 V dirige a la alimentación/comunicación de la PCB.",
            [
                {"section_type": "wiring", "title": "Puntos de medida por interfaz", "body": "Compacta/cassette/conductos/suelo/techo: CN14 1–3, 12 V CC. Mural con CN300: 1–2, 12 V CC. Mural con CNC01: 1–3, 13 V CC. Miniconductos con CN300: 1–3 o 1–2 según mando de 3 o 2 hilos, 12 V CC.", "collapsed_default": 0},
                {"section_type": "interpretation", "title": "Interpretación del manual", "body": "Tensión nominal presente: la PCB suministra alimentación y se sospecha del mando/cable. 0 V: volver a comprobar el mando y continuar con la PCB de control/comunicación.", "collapsed_default": 0},
            ],
            [
                step(1, "Cortar alimentación antes de revisar compatibilidad, cableado entre mando/interior y comunicación interior–exterior.", level="danger"),
                step(2, "Verificar que interior, exterior y mando pertenecen a una combinación admitida."),
                step(3, "Descartar caídas, microcortes, armónicos y problemas de tierra."),
                step(4, "Identificar primero la interfaz y medir en CN14, CN300 o CNC01 según corresponda.", "12 V o 13 V CC según la variante; nunca aplicar un punto de otra placa.", "danger"),
                step(5, "Con tensión correcta, probar/sustituir el mando; con 0 V, volver a revisar el bus y continuar con la PCB."),
                step(6, "Si el síntoma persiste tras las comprobaciones, continuar con la PCB principal."),
            ],
            "03-65", "03-66", "3-3. No operation (Power is on)", 30,
        ),
        variant(
            54, 33, "No enfría o no calienta",
            "El equipo funciona parcial o aparentemente, pero no entrega la capacidad esperada.",
            "Ordenar la revisión desde flujo de aire e instalación hasta ciclo frigorífico, EEV y compresor.",
            "Evita comenzar por el refrigerante sin comprobar ventiladores, filtros, baterías, válvulas, tuberías y condiciones del local.",
            [
                {"section_type": "diagnostic", "title": "Colador/strainer", "body": "Normalmente no presenta diferencia de temperatura entre entrada y salida. Una diferencia clara puede indicar obstrucción interna y el manual dirige a sustituirlo.", "collapsed_default": 1},
                {"section_type": "warning", "title": "Carga de refrigerante", "body": "Si se corrige una fuga y se recarga, el manual exige vacío y la cantidad especificada, no una carga aproximada.", "collapsed_default": 0},
            ],
            [
                step(1, "Comprobar ventilador interior en alta, filtro, batería interior y funciones de ahorro."),
                step(2, "Comprobar funcionamiento exterior, obstáculos, batería exterior y válvulas de servicio abiertas."),
                step(3, "Valorar dimensionado, ventanas abiertas y radiación solar."),
                step(4, "Revisar diámetro/longitud de tuberías y línea de comunicación."),
                step(5, "Comprobar presiones y fugas, strainer, apertura de EEV/capilar y compresor.", level="danger"),
            ],
            "03-67", "03-68", "3-4. No cooling/No heating", 40,
        ),
        variant(
            55, 33, "Ruido anormal",
            "Ruido mecánico, vibración o contacto de tuberías sin código activo.",
            "Separar rápidamente ruido interior, exterior, ventilador, instalación o compresor.",
            "El flujo oficial comienza localizando de qué unidad procede el ruido antes de desmontar componentes.",
            [
                {"section_type": "indoor", "title": "Si procede de la interior", "body": "Revisar estabilidad, rejilla/panel, ventilador deformado, tornillos y objetos que impidan el giro.", "collapsed_default": 0},
                {"section_type": "outdoor", "title": "Si procede de la exterior", "body": "Revisar estabilidad, protector, ventilador, tornillos, obstáculos, pernos flojos, contacto de tuberías y posible compresor bloqueado.", "collapsed_default": 0},
            ],
            [
                step(1, "Localizar si el ruido procede de la unidad interior o exterior."),
                step(2, "Comprobar instalación estable, paneles/protecciones y puntos de contacto."),
                step(3, "Con alimentación cortada, revisar deformación, tornillos y obstáculos del ventilador.", level="danger"),
                step(4, "En la exterior, revisar vibración de pernos y contacto de tuberías."),
                step(5, "Si se sospecha bloqueo del compresor, aplicar su procedimiento eléctrico específico.", level="danger"),
            ],
            "03-69", None, "3-5. Abnormal noise", 50,
        ),
        variant(
            56, 33, "Fuga de agua o gotas expulsadas por el aire",
            "Agua bajo la unidad o gotas lanzadas por la impulsión, sin limitarse al error de boya de una cassette.",
            "Diferenciar instalación/desagüe de filtro, ventilador y problema frigorífico.",
            "El manual separa agua que fuga por el equipo de agua que sale impulsada con el aire.",
            [
                {"section_type": "drain", "title": "Si el agua fuga por la unidad", "body": "Revisar estabilidad/deformación, unión del desagüe, sifón o contrapendiente, obstrucción de la manguera y giro del ventilador.", "collapsed_default": 0},
                {"section_type": "airflow", "title": "Si expulsa gotas", "body": "Revisar filtro obstruido y comprobar presión/carga; una fuga de refrigerante también puede provocar este síntoma.", "collapsed_default": 0},
            ],
            [
                step(1, "Determinar si el agua cae por la carcasa o sale en forma de gotas por la impulsión."),
                step(2, "Para fuga: revisar nivelación, deformación, unión, sifón/contrapendiente y obstrucción del desagüe."),
                step(3, "Comprobar que el ventilador gira correctamente."),
                step(4, "Para gotas impulsadas: revisar filtro y flujo de aire."),
                step(5, "Comprobar presiones y posibles fugas de refrigerante con el procedimiento adecuado.", level="danger"),
            ],
            "03-70", None, "3-6. Water leaking", 60,
        ),
    ]
    return {
        "id": 33,
        "brand_id": 2,
        "category_id": 17,
        "slug": "troubleshooting-without-error-code",
        "title": "Diagnóstico oficial cuando no hay código",
        "summary": "Flujos de comprobación para falta de alimentación, ausencia de funcionamiento, rendimiento, ruido y agua.",
        "active": 1,
        "category": {"id": 17, "slug": "symptom_diagnosis", "name": "Diagnóstico sin código"},
        "variants": variants,
    }


def safety_components_topic() -> dict[str, Any]:
    return {
        "id": 34,
        "brand_id": 2,
        "category_id": 9,
        "slug": "leak-sensor-intake-grille-checks",
        "title": "Sensor de fuga y seguridad de rejilla",
        "summary": "Diferenciar fallo del sensor, fuga real y apertura del microinterruptor de la rejilla.",
        "active": 1,
        "category": {"id": 9, "slug": "component_checks", "name": "Comprobación de componentes"},
        "variants": [
            variant(
                57, 34, "Distinguir E45 de EA8 en el sensor de fuga",
                "Unidad interior equipada con sensor de fuga: E45 o EA8, con ventilación de seguridad posible.",
                "Evitar confundir sensor averiado/deteriorado con refrigerante realmente detectado.",
                "E45 corresponde al circuito o vida útil del sensor; EA8 confirma detección y mantiene la ventilación de mezcla.",
                [
                    {"section_type": "comparison", "title": "E45", "body": "Abierto, cortocircuito, tensión anormal o deterioro del sensor. La variante de deterioro puede permitir funcionamiento temporal.", "collapsed_default": 0},
                    {"section_type": "comparison", "title": "EA8", "body": "Refrigerante detectado: frío/calor parados y ventilación de seguridad activa. No puentear el sensor ni parar esa ventilación.", "collapsed_default": 0},
                ],
                [
                    step(1, "Leer el código exacto antes de tocar el sensor: E45 y EA8 requieren respuestas distintas."),
                    step(2, "Con E45, cortar alimentación y revisar conector, mazo y circuito abierto; sustituir el sensor si continúa.", level="danger"),
                    step(3, "Con aviso de deterioro E45, programar la sustitución; el periodo temporal no es indefinido."),
                    step(4, "Con EA8, mantener la ventilación de seguridad, localizar la fuga y corregirla antes del rearme.", level="danger"),
                    step(5, "Después de corregir la fuga, volver a alimentar; si detecta gas de nuevo, el código reaparece.", level="danger"),
                    step(6, "Sustituir el sensor si una exposición alta o repetida impide su recuperación."),
                ],
                "03-32", "03-33 / 03-62", "E45 sensor error/deterioration and EA8 refrigerant detection", 10,
            ),
            variant(
                58, 34, "Comprobar microinterruptor de rejilla de aspiración",
                "Unidad interior con rejilla protegida por microinterruptor y conector CN11; código E58.",
                "Separar rejilla mal cerrada, interruptor, suciedad, cableado y PCB.",
                "E58 se detecta cuando el microinterruptor aparece abierto con el compresor funcionando.",
                [
                    {"section_type": "wiring", "title": "Conexión documentada", "body": "La familia del manual identifica CN11. Confirmar la serigrafía antes de aplicar este punto a otra placa.", "collapsed_default": 0},
                    {"section_type": "recognition", "title": "Condición de detección", "body": "Microinterruptor abierto mientras funciona el compresor.", "collapsed_default": 0},
                ],
                [
                    step(1, "Cortar alimentación antes de desmontar la rejilla o desconectar CN11.", level="danger"),
                    step(2, "Comprobar cierre mecánico, accionamiento y ausencia de polvo/obstáculos."),
                    step(3, "Medir que el microinterruptor cambia entre ON y OFF."),
                    step(4, "Revisar CN11, falsos contactos, cable pellizcado y cortocircuito."),
                    step(5, "Si interruptor y cableado son correctos, continuar con la PCB principal."),
                ],
                "03-38", None, "2-22. Intake grille error", 20,
            ),
        ],
    }


def refresh_search() -> tuple[int, int]:
    error_count, _ = refresh_catalogs()
    search = [row for row in load(WEB / "search.json") if int(row.get("topic_id") or 0) not in (33, 34)]
    for topic_id in (33, 34):
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
        "latest_phase": "Fujitsu V2 — seguridad interior y diagnóstico sin código",
        "last_processed_manual": ORIGIN,
        "technical_library_review": "E45/E58/EA8 desarrollados y seis flujos oficiales sin código añadidos.",
        "last_update_utc": "2026-07-16T16:30:00Z",
    })

    topic33 = load(WEB / "topics" / "33.json")
    topic34 = load(WEB / "topics" / "34.json")
    for category_id, topic in ((17, topic33), (9, topic34)):
        category = next(row for row in navigation["categories"] if int(row["id"]) == category_id)
        category["topics"] = [row for row in category.get("topics") or [] if int(row["id"]) != int(topic["id"])]
        category["topics"].append({
            "id": topic["id"],
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
    variant_map.update({str(item): 33 for item in range(51, 57)})
    variant_map.update({"57": 34, "58": 34})
    write_json(variant_map_path, variant_map)

    sources_path = WEB / "sources.json"
    sources = load(sources_path)
    source = next(row for row in sources if row.get("document_ref") == ORIGIN)
    source["notes"] = (
        "Documento técnico del fabricante conservado por un distribuidor. Se resumen diagnósticos "
        "03-23 a 03-70, curva 03-98 y esquema 02-111; no se publican páginas ni imágenes."
    )
    write_json(sources_path, sources)

    coverage_path = WEB / "coverage.json"
    coverage = load(coverage_path)
    for row in coverage:
        row["source_count"] = len(sources)
        if row.get("area_slug") == "errors":
            row["notes"] = "Incluye ahora seguridad interior E45/EA8, rejilla E58, agrupadores y subcódigos desarrollados; la auditoría mantiene visibles los huecos restantes."
        elif row.get("area_slug") == "component_checks":
            row["notes"] = "Incluye compuertas, sondas de válvula, sensor de fuga y microinterruptor de rejilla, además de los componentes ya documentados en otras familias."
        elif row.get("area_slug") == "symptom_diagnosis":
            row["notes"] = "Incluye mando sin pantalla y los seis flujos oficiales: interior/exterior sin alimentación, no funciona, no enfría/calienta, ruido y agua."
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
    config["notes"] = "Fujitsu V2.13: E45/E58/EA8 y diagnóstico oficial sin código con seguridad y valores eléctricos."
    write_json(config_path, config)


def main() -> int:
    enrich_e39_source()
    add_error_details()
    write_json(WEB / "topics" / "33.json", symptom_topic())
    write_json(WEB / "topics" / "34.json", safety_components_topic())
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
