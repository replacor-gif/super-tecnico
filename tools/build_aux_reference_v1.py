#!/usr/bin/env python3
"""Construye AUX Referencia V1 para Super Técnico.

La proyección pública contiene resúmenes técnicos trazables, pero no publica
los PDF ni las capturas de los manuales. Los códigos se separan por familia y
por lugar de lectura: display interior, mando cableado, pilotos de la unidad
exterior, display de placa o sistema ARV/VRF.
"""

from __future__ import annotations

import json
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import build_hisense_reference_v1 as core


ROOT = Path(__file__).resolve().parents[1]
BRAND_DIR = ROOT / "data" / "brands" / "aux-air"
WEB_DIR = BRAND_DIR / "web"
BRAND_ID = 14

core.BRAND_DIR = BRAND_DIR
core.WEB_DIR = WEB_DIR
core.BRAND_ID = BRAND_ID

core.SOURCES = {
    "OFFICIAL": {
        "title": "AUX Global — Error Codes",
        "document_ref": "AUX-GLOBAL-ERROR-CODES",
        "source_url": "https://www.auxair.com/global/error-codes.html",
        "type": "official_web",
        "year": "actualizado",
    },
    "USA": {
        "title": "AUX USA — Error Codes FAQ",
        "document_ref": "AUX-USA-ERROR-CODES-FAQ",
        "source_url": "https://us.auxair.com/error-codes-faq",
        "type": "official_web",
        "year": "actualizado",
    },
    "SPLIT": {
        "title": "AUX F-Freedom Series — Service Manual",
        "document_ref": "AUX-F-FREEDOM-SERVICE-2023",
        "source_url": "https://aux-air.ru/erc/2023/08/30/f421f5ff2b69db2fa66744f839c042d87cae3bb6.pdf",
        "type": "service_manual",
        "year": "2023",
    },
    "MULTI": {
        "title": "AUX Multi — Technical Catalogue and Service Information",
        "document_ref": "AUX-MULTI-4.03-ENG",
        "source_url": "https://auxcool.com/wp-content/uploads/2024/10/AUX_MULTI_4.03_ENG_maly.pdf",
        "type": "service_manual",
        "year": "2025/2026",
    },
    "CAC": {
        "title": "AUX Light Commercial T1 R410A 50 Hz — Service Manual",
        "document_ref": "AUX-LIGHT-COMMERCIAL-T1-R410A",
        "source_url": "https://aux.az/wp-content/uploads/2017/ServiceManual--LightCommercialT1R410a50Hz.pdf",
        "type": "service_manual",
        "year": "2017",
    },
    "ARV": {
        "title": "AUX DC Inverter ARV Outdoor Unit Individual Series — Technical Manual",
        "document_ref": "AUX-ARV-INDIVIDUAL-2021",
        "source_url": "https://aux-air.co.il/wp-content/uploads/2021/06/VRF_individual.pdf",
        "type": "service_manual",
        "year": "2021",
    },
    "XK": {
        "title": "AUX Wired Controller XK — Installation and Operation Manual",
        "document_ref": "AUX-XK-CONTROLLER-2026",
        "source_url": "https://auxcool.com/wp-content/uploads/2026/02/Instrukcja-XK-2026-ENG.pdf",
        "type": "controller_manual",
        "year": "2026",
    },
    "DOWNLOADS": {
        "title": "AUX USA — Downloads",
        "document_ref": "AUX-USA-DOWNLOADS",
        "source_url": "https://us.auxair.com/downloads",
        "type": "official_web",
        "year": "actualizado",
    },
}

core.CATEGORIES = [
    (1, "errors", "Errores y protecciones", "Códigos separados por display, mando, placa, comercial, multisplit y ARV."),
    (2, "outdoor_diagnostics", "Pilotos y display de la unidad exterior", "Tablas D1/D2/D3, parpadeos comerciales y display de PCB ARV."),
    (3, "diagnostic_access", "Obtención de códigos y subcódigos", "Lectura desde mando, receptor, pilotos y placa exterior."),
    (4, "history_reset", "Historial y borrado", "Memoria, rearmado, recuperación automática y datos previos a la avería."),
    (5, "service_modes", "Modos de servicio", "Test Run, frío/calor forzado y comprobaciones frigoríficas."),
    (6, "configuration", "Configuración y programación", "DIP, direcciones, prioridad de modo, capacidad y funciones del mando."),
    (7, "controllers_buses", "Mandos y buses", "Mando XK, cableado, 12 V, bus ARV y fallos del propio mando."),
    (8, "drainage_overflow", "Drenaje y desbordamiento", "Boya, bomba, A5/E4/H1 y prueba de evacuación."),
    (9, "commissioning", "Puesta en marcha", "Prueba en frío/calor, válvulas, red, tubería y adquisición de unidades."),
    (10, "multisplit", "Multisplit y simultáneos", "Conflicto de modo, códigos por capa y efecto sobre las unidades."),
    (11, "vrf_network", "ARV/VRF y red", "Direcciones, comunicación, capacidad, prioridades, aceite y desescarche."),
    (12, "component_checks", "Comprobación de componentes", "Sondas, ventiladores, compresor, inverter, EEV, presión y comunicación."),
    (13, "technical_values", "Valores técnicos", "NTC, tensiones, tiempos, umbrales y límites documentados."),
    (14, "normal_states", "Comportamientos normales", "Retardos, desescarche, retorno de aceite, espera y conflicto de modo."),
    (15, "service_tools_boards", "Herramientas y placas", "Monitorización, memoria ARV y tareas después de cambiar una PCB."),
    (16, "system_architecture", "Reconocer el sistema", "Rasgos visibles para elegir la tabla correcta sin exigir el modelo."),
]
core.CATEGORY_BY_SLUG = {
    slug: {"id": ident, "slug": slug, "name": name, "description": description}
    for ident, slug, name, description in core.CATEGORIES
}
core.ERROR_SPECS.clear()
core.TOPICS.clear()


def err(
    code: str,
    title: str,
    profile: str,
    ref: str,
    page: str,
    *,
    family: str,
    scope: str = "system",
    behavior: str | None = None,
    technical: str = "",
    aliases: list[str] | None = None,
) -> None:
    core.add_error(
        code,
        title,
        profile,
        ref,
        page,
        family=family,
        scope=scope,
        behavior=behavior or "La protección detiene el funcionamiento afectado.",
        technical=technical,
        aliases=aliases,
    )


# Split/inverter. Se conserva el lugar de lectura para no mezclar estos códigos
# con las capas comercial, multisplit o ARV.
SPLIT_ERRORS = [
    ("E0", "Protección de sobrecorriente de la unidad interior", "power", "indoor"),
    ("E1", "Sonda de temperatura ambiente interior", "sensor", "indoor"),
    ("E2", "Sonda del condensador o batería exterior", "sensor", "outdoor"),
    ("E3", "Sonda del evaporador o batería interior", "sensor", "indoor"),
    ("E4", "Motor ventilador interior AC/PG/DC", "fan", "indoor"),
    ("E5", "Comunicación entre unidad interior y exterior", "communication", "system"),
    ("5E", "Comunicación entre unidad interior y exterior", "communication", "system"),
    ("E8", "Comunicación entre display y placa principal interior", "communication", "indoor"),
    ("Eb", "EEPROM o memoria de la unidad interior", "pcb", "indoor"),
    ("F0", "Motor ventilador exterior DC", "fan", "outdoor"),
    ("F1", "Protección del módulo inverter", "inverter", "outdoor"),
    ("F2", "Protección PFC", "inverter", "outdoor"),
    ("F3", "Fallo de arranque o pérdida de sincronismo del compresor", "compressor", "outdoor"),
    ("F4", "Sonda de temperatura de descarga", "sensor", "outdoor"),
    ("F5", "Sonda de la parte superior del compresor", "sensor", "outdoor"),
    ("F6", "Sonda de temperatura ambiente exterior", "sensor", "outdoor"),
    ("F7", "Protección por sobretensión o subtensión", "power", "outdoor"),
    ("F8", "Comunicación entre placa exterior principal y módulo driver", "communication", "outdoor"),
    ("F9", "EEPROM o memoria de la unidad exterior", "pcb", "outdoor"),
    ("FA", "Sonda de aspiración o anomalía del ciclo/válvula de cuatro vías", "sensor", "outdoor"),
    ("P2", "Protección de alta presión", "pressure", "system"),
    ("P3", "Falta de refrigerante", "pressure", "system"),
    ("P4", "Sobrecarga del condensador en refrigeración", "pressure", "system"),
    ("P5", "Protección por temperatura de descarga", "pressure", "system"),
    ("P6", "Sobrecarga del evaporador en calefacción", "pressure", "system"),
    ("P7", "Protección antihielo en refrigeración", "pressure", "indoor"),
    ("P8", "Protección de sobrecorriente exterior", "power", "outdoor"),
]
for code, title, profile, scope in SPLIT_ERRORS:
    technical = {
        "E1": "La familia revisada usa aproximadamente 15 kΩ a 25 °C para la sonda ambiente interior.",
        "E2": "La familia revisada usa aproximadamente 20 kΩ a 25 °C para la sonda de batería exterior.",
        "E3": "La familia revisada usa aproximadamente 20 kΩ a 25 °C; algunas generaciones anteriores citan 5 kΩ.",
        "E5": "El mismo fallo puede aparecer como 5E o como un patrón D1/D2/D3 en la placa exterior.",
        "E8": "Este E8 es de mural/display interior; no es el E8 de protección exterior multisplit ni la sonda de descarga comercial.",
    }.get(code, "")
    err(
        code,
        title,
        profile,
        "SPLIT",
        "62-96",
        family="AUX split inverter — display interior",
        scope=scope,
        technical=technical,
        aliases=[code.upper(), code.lower(), f"split {code}", f"mural {code}"],
    )


L_ERRORS = [
    ("L0", "Tensión del bus DC demasiado alta o demasiado baja", "power"),
    ("L1", "Sobrecorriente de fase del compresor", "inverter"),
    ("L2", "Compresor fuera de paso o desincronizado", "compressor"),
    ("L3", "Pérdida de fase del compresor", "compressor"),
    ("L4", "Protección del módulo IPM", "inverter"),
    ("L5", "Protección PFC de hardware", "inverter"),
    ("L6", "Protección PFC de software", "inverter"),
    ("L7", "Lectura AD anormal de corriente del compresor", "inverter"),
    ("L8", "Desequilibrio del shunt o corriente de fase", "inverter"),
    ("L9", "Sonda de temperatura del módulo IPM", "sensor"),
    ("LA", "Fallo de arranque del compresor", "compressor"),
    ("LC", "Lectura AD anormal de corriente PFC", "inverter"),
    ("LD", "Pérdida de sincronismo del compresor", "compressor"),
    ("LE", "Protección de fase del compresor", "compressor"),
    ("LF", "Protección del bus o circuito de potencia", "inverter"),
    ("LH", "Protección térmica del módulo o driver", "inverter"),
]
for code, title, profile in L_ERRORS:
    err(
        code,
        title,
        profile,
        "MULTI" if code in {"LD", "LE", "LF", "LH"} else "SPLIT",
        "14-17" if code in {"LD", "LE", "LF", "LH"} else "94",
        family="AUX inverter/multisplit — placa o módulo exterior",
        scope="outdoor",
        technical="Es un código de la capa inverter; compruebe red, bus DC, U-V-W, motor y driver por separado.",
        aliases=[f"módulo {code}", f"driver {code}"],
    )


# Multisplit: se añaden interpretaciones incluso cuando el código ya existe en
# split. Así el técnico ve todas las posibilidades antes de abrir una ficha.
MULTI_ERRORS = [
    ("H1", "Fallo de drenaje o nivel de agua de la unidad interior", "drain", "indoor"),
    ("H2", "Comunicación entre mando cableado y unidad interior", "communication", "controller"),
    ("H3", "Sonda de entrada del evaporador interior", "sensor", "indoor"),
    ("H4", "Sonda de salida del evaporador interior", "sensor", "indoor"),
    ("H5", "Temperatura de descarga demasiado baja", "pressure", "system"),
    ("H6", "Presostato de baja presión", "pressure", "outdoor"),
    ("H7", "Protección de baja presión", "pressure", "system"),
    ("H8", "Anomalía de la válvula de cuatro vías", "valve", "outdoor"),
    ("H9", "Comunicación entre placas o unidades del sistema", "communication", "system"),
    ("C1", "Sonda de temperatura ambiente exterior", "sensor", "outdoor"),
    ("C2", "Sonda de desescarche o batería exterior", "sensor", "outdoor"),
    ("C3", "Sonda de temperatura de descarga", "sensor", "outdoor"),
    ("C6", "Sonda de aspiración", "sensor", "outdoor"),
    ("C8", "Sonda de la zona central del condensador", "sensor", "outdoor"),
    ("J3", "Comunicación entre driver y placa principal exterior", "communication", "outdoor"),
    ("J7", "EEPROM de la unidad exterior", "pcb", "outdoor"),
    ("E1", "Anomalía de la válvula de cuatro vías", "valve", "outdoor"),
    ("E3", "Protección por temperatura alta de descarga", "pressure", "outdoor"),
    ("E8", "Protección por temperatura exterior alta en refrigeración", "pressure", "outdoor"),
    ("F6", "Protección de baja presión", "pressure", "system"),
    ("FH", "Temperatura de descarga demasiado baja", "pressure", "system"),
    ("31", "Protección del módulo inverter", "inverter", "outdoor"),
    ("32", "EEPROM o hardware del módulo inverter", "pcb", "outdoor"),
    ("34", "Protección o desconexión del compresor", "compressor", "outdoor"),
    ("35", "Sobrecorriente del conjunto exterior", "power", "outdoor"),
    ("36", "Tensión del bus demasiado alta o baja", "power", "outdoor"),
    ("39", "Sonda o sobretemperatura del módulo IPM", "inverter", "outdoor"),
    ("3H", "Protección del ventilador exterior", "fan", "outdoor"),
    ("3C", "Ventilador exterior fuera de paso", "fan", "outdoor"),
    ("3J", "Lectura AD anormal de corriente del ventilador", "fan", "outdoor"),
    ("3E", "Protección PFC de software", "inverter", "outdoor"),
    ("3F", "Protección PFC de hardware", "inverter", "outdoor"),
    ("41", "Protección IPM del ventilador exterior", "fan", "outdoor"),
    ("AD", "Protección antihielo de la unidad interior", "pressure", "indoor"),
]
for code, title, profile, scope in MULTI_ERRORS:
    err(
        code,
        title,
        profile,
        "MULTI",
        "12-17",
        family="AUX Multi — tabla de unidad interior/exterior",
        scope=scope,
        behavior=(
            "Se detiene la unidad interior afectada; las demás pueden continuar si la exterior y el modo común lo permiten."
            if scope in {"indoor", "controller"}
            else "La protección afecta a la exterior o al ciclo común del multisplit."
        ),
        technical=(
            "No confundir con E8 de mural: aquí E8 es protección por temperatura exterior alta."
            if code == "E8"
            else "Anote si el código se leyó en la interior, el mando o la placa exterior."
        ),
        aliases=[f"multi {code}", f"multisplit {code}"],
    )


CASSETTE_ERRORS = [
    ("A1", "Sonda de temperatura ambiente interior", "sensor"),
    ("A2", "Sonda central del evaporador interior", "sensor"),
    ("A3", "Sonda de entrada del evaporador interior", "sensor"),
    ("A4", "Sonda de salida del evaporador interior", "sensor"),
    ("A5", "Bomba de condensados, boya o drenaje", "drain"),
    ("A6", "Motor ventilador interior", "fan"),
    ("A7", "Motor de oscilación o lama", "valve"),
    ("A8", "EEPROM de la unidad interior", "pcb"),
    ("A9", "Comunicación entre unidad interior y exterior", "communication"),
    ("AA", "Comunicación entre mando cableado/display y placa interior", "communication"),
]
for code, title, profile in CASSETTE_ERRORS:
    err(
        code,
        title,
        profile,
        "MULTI",
        "15-16",
        family="AUX cassette/techo-suelo/conductos slim — display o mando",
        scope="controller" if code == "AA" else "indoor",
        behavior="Se detiene la unidad interior afectada; el resto del multisplit puede seguir si el ciclo común lo permite.",
        technical=(
            "A5 obliga a revisar nivel real, boya, bomba, pendiente y placa; no significa automáticamente bomba averiada."
            if code == "A5"
            else "Use la tabla A únicamente cuando la interfaz y el tipo de unidad coincidan."
        ),
        aliases=[f"cassette {code}", f"conductos {code}"],
    )


# Comercial anterior. Conserva las diferencias entre 220-240 V y 380-415 V.
CAC_ERRORS = [
    ("E1", "Sonda de aire interior TA", "sensor", "indoor", "TIMER: 1 destello cada 8 s"),
    ("E2", "Sonda exterior de condensador TW", "sensor", "outdoor", "TIMER: 2 destellos cada 1 s; el manual indica que no detiene"),
    ("E3", "Sonda de batería interior TE", "sensor", "indoor", "TIMER: 2 destellos cada 8 s"),
    ("E4", "Desbordamiento, boya o bomba de condensados", "drain", "indoor", "TIMER: 4 destellos cada 8 s; detiene"),
    ("E5", "Comunicación entre unidad interior y exterior", "communication", "system", "Sin piloto en 220-240 V; detiene"),
    ("E6", "Secuencia de fases, fase ausente o tensión baja", "power", "system", "TIMER: 6 destellos cada 8 s; detiene"),
    ("E7", "Sonda exterior de condensador TL", "sensor", "outdoor", "Tabla de diagnosis adicional"),
    ("E8", "Sonda de temperatura de descarga TP", "sensor", "outdoor", "Tabla de diagnosis adicional"),
    ("E9", "Protección de alta o baja presión", "pressure", "system", "380-415 V: display 9 destellos; placa 1 o 3"),
    ("EA", "Protección por temperatura de descarga elevada", "pressure", "outdoor", "380-415 V: 10 destellos; detiene"),
    ("F1", "Comunicación interior–exterior en variante trifásica", "communication", "system", "Display y placa: 5 destellos y 2 s apagado"),
]
for code, title, profile, scope, indication in CAC_ERRORS:
    err(
        code,
        title,
        profile,
        "CAC",
        "125-126",
        family="AUX Light Commercial R410A — mando cableado y pilotos",
        scope=scope,
        behavior=(
            "El manual permite continuar el funcionamiento para esta detección."
            if code in {"E2", "E7", "E8"}
            else "La protección detiene la unidad comercial afectada."
        ),
        technical=(
            f"{indication}. El mismo código puede tener otro significado en mural o multisplit; confirme alimentación y tabla."
        ),
        aliases=[f"comercial {code}", f"conductos {code}", indication],
    )


# ARV/VRF individual. La columna Recovery del manual se conserva en el
# comportamiento para ayudar a distinguir reintento y bloqueo.
ARV_ERRORS = [
    ("A1", "Sonda de ambiente interior", "sensor", "indoor", True),
    ("A2", "Sonda central del evaporador interior", "sensor", "indoor", True),
    ("A3", "Sonda de entrada de tubería interior", "sensor", "indoor", True),
    ("A4", "Sonda de salida de tubería interior", "sensor", "indoor", True),
    ("A5", "Bomba de agua, boya o drenaje interior", "drain", "indoor", True),
    ("A6", "Motor ventilador PG interior", "fan", "indoor", False),
    ("A7", "Motor de oscilación", "valve", "indoor", False),
    ("A8", "EEPROM de la unidad interior", "pcb", "indoor", False),
    ("A9", "Comunicación entre unidad interior y exterior", "communication", "system", False),
    ("AA", "Comunicación entre unidad interior y mando cableado", "communication", "controller", False),
    ("AE", "Conflicto de modo de funcionamiento", "configuration", "indoor", True),
    ("AH", "Dirección interior duplicada", "configuration", "system", True),
    ("AJ", "Capacidad interior total fuera de límites", "configuration", "system", True),
    ("AF", "La válvula de expansión no puede cerrar", "valve", "indoor", True),
    ("A0", "La válvula de expansión no puede abrir", "valve", "indoor", False),
    ("C1", "Sonda de temperatura ambiente exterior", "sensor", "outdoor", True),
    ("C2", "Sonda de desescarche exterior", "sensor", "outdoor", True),
    ("C3", "Sonda de descarga del inverter", "sensor", "outdoor", True),
    ("C6", "Sonda de aspiración", "sensor", "outdoor", True),
    ("37", "Sonda de temperatura del módulo inverter", "sensor", "outdoor", False),
    ("F1", "Sensor de alta presión", "sensor", "outdoor", True),
    ("F4", "Sensor de baja presión", "sensor", "outdoor", True),
    ("H1", "Presostato de alta presión", "pressure", "system", False),
    ("H4", "Presostato de baja presión", "pressure", "system", True),
    ("E3", "Protección por temperatura alta de descarga", "pressure", "system", False),
    ("F3", "Protección de alta presión", "pressure", "system", True),
    ("F6", "Protección de baja presión", "pressure", "system", False),
    ("F8", "Relación de compresión demasiado alta", "pressure", "system", False),
    ("F9", "Relación de compresión demasiado baja", "pressure", "system", False),
    ("FA", "Sin diferencia suficiente entre alta y baja presión", "pressure", "system", True),
    ("H5", "Falta de refrigerante", "pressure", "system", False),
    ("JJ", "Capacidad interior fuera del 50–130 % de la exterior", "configuration", "system", True),
    ("HJ", "Fallo de alimentación principal o secuencia de fases", "power", "system", False),
    ("J2", "Comunicación entre exterior e interiores", "communication", "system", True),
    ("J3", "Comunicación entre placa exterior y driver inverter", "communication", "outdoor", True),
    ("J7", "EEPROM de la placa exterior", "pcb", "outdoor", False),
    ("31", "Protección del módulo inverter", "inverter", "outdoor", True),
    ("32", "Fallo de hardware del módulo inverter", "inverter", "outdoor", False),
    ("33", "Protección de software del módulo inverter", "inverter", "outdoor", True),
    ("34", "Compresor desconectado o fase abierta", "compressor", "outdoor", True),
    ("35", "Sobrecorriente de fase del compresor", "compressor", "outdoor", True),
    ("36", "Tensión del bus DC demasiado alta o baja", "power", "outdoor", True),
    ("39", "Parada por temperatura del módulo inverter", "inverter", "outdoor", True),
    ("47", "Pérdida de una unidad interior registrada", "communication", "system", True),
]
for code, title, profile, scope, recovery in ARV_ERRORS:
    technical = (
        "El manual marca Recovery: Yes; investigue la causa aunque el sistema vuelva a funcionar."
        if recovery
        else "El manual marca Recovery: No; normalmente requiere corregir la causa y rearmar."
    )
    if code == "36":
        technical += " La tabla revisada cita bus inferior a 420 V o superior a 642 V."
    if code == "39":
        technical += " La protección térmica del módulo se registra por encima de 94 °C."
    if code in {"AJ", "JJ"}:
        technical += " La capacidad total debe quedar entre el 50 % y el 130 % de la exterior."
    err(
        code,
        title,
        profile,
        "ARV",
        "126-132",
        family="AUX ARV individual — mando, receptor o display exterior",
        scope=scope,
        behavior=(
            "La unidad puede recuperar automáticamente cuando desaparece la condición."
            if recovery
            else "La protección no está marcada como recuperable; detiene la unidad o el ciclo afectado."
        ),
        technical=technical,
        aliases=[f"ARV {code}", f"VRF {code}", "recovery yes" if recovery else "recovery no"],
    )


def step(
    no: int,
    instruction: str,
    expected: str = "",
    phase: str = "procedure",
    warning: str = "none",
) -> dict[str, Any]:
    return core.step(no, instruction, expected, phase, warning)


def v(
    title: str,
    recognition: str,
    ref: str,
    page: str,
    purpose: str,
    summary: str,
    *,
    system: str = "AUX",
    scope: str = "system",
    steps: list[dict[str, Any]] | None = None,
    parameters: list[dict[str, Any]] | None = None,
    controller_data: dict[str, Any] | None = None,
    monitoring: list[dict[str, Any]] | None = None,
    led_patterns: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return core.variant(
        title,
        recognition,
        ref,
        page,
        purpose,
        summary,
        system=system,
        scope=scope,
        steps=steps,
        parameters=parameters,
        controller_data=controller_data,
        monitoring=monitoring,
        led_patterns=led_patterns,
    )


def add_topic(
    category: str,
    slug: str,
    title: str,
    summary: str,
    variants: list[dict[str, Any]],
) -> None:
    core.add_topic(category, slug, title, summary, variants)


def aux_led_pattern(
    number: int,
    meaning: str,
    d1: str,
    d2: str,
    d3: str,
) -> dict[str, Any]:
    state_map = {"apagado": "off", "encendido": "on", "parpadeo": "blink"}

    def indicator(label: str, value: str) -> dict[str, str]:
        return {
            "label": label,
            "color": "neutral",
            "state": state_map[value],
            "detail": value,
        }

    return {
        "code_display": f"Patrón {number:02d}",
        "indication_type": "outdoor_three_led",
        "display_location": "PCB exterior con pilotos D1, D2 y D3",
        "family_hint": "AUX split inverter F-Freedom; confirmar serigrafía D1/D2/D3",
        "relationship": meaning,
        "led_indicators": [
            indicator("D1", d1),
            indicator("D2", d2),
            indicator("D3", d3),
        ],
        "counting_rule": "○ apagado, ● encendido fijo, ★ parpadeo. Observe varios ciclos antes de identificar el patrón.",
        "cycle_note": "Los tres estados se leen simultáneamente; no es un conteo de destellos.",
        "sequence": f"D1 {d1}; D2 {d2}; D3 {d3}.",
    }


AUX_THREE_LED_PATTERNS = [
    aux_led_pattern(1, "Normal en espera", "apagado", "apagado", "apagado"),
    aux_led_pattern(2, "Normal con compresor funcionando", "parpadeo", "parpadeo", "parpadeo"),
    aux_led_pattern(3, "Modo de servicio o prueba forzada", "encendido", "encendido", "encendido"),
    aux_led_pattern(4, "Protección del módulo inverter", "parpadeo", "parpadeo", "encendido"),
    aux_led_pattern(5, "Protección PFC", "parpadeo", "parpadeo", "apagado"),
    aux_led_pattern(6, "Compresor fuera de paso", "parpadeo", "encendido", "parpadeo"),
    aux_led_pattern(7, "Sonda de descarga", "parpadeo", "apagado", "parpadeo"),
    aux_led_pattern(8, "Sonda de batería exterior", "encendido", "parpadeo", "parpadeo"),
    aux_led_pattern(9, "Sonda de ambiente exterior", "apagado", "parpadeo", "parpadeo"),
    aux_led_pattern(10, "Comunicación interior–exterior", "parpadeo", "encendido", "encendido"),
    aux_led_pattern(11, "Comunicación entre placa exterior y módulo", "parpadeo", "encendido", "apagado"),
    aux_led_pattern(12, "EEPROM exterior", "parpadeo", "apagado", "encendido"),
    aux_led_pattern(13, "Motor ventilador exterior DC", "parpadeo", "apagado", "apagado"),
    aux_led_pattern(14, "Sonda de ambiente interior", "encendido", "parpadeo", "encendido"),
    aux_led_pattern(15, "Sonda de batería interior", "encendido", "parpadeo", "apagado"),
    aux_led_pattern(16, "Motor ventilador interior", "apagado", "parpadeo", "encendido"),
    aux_led_pattern(17, "Consultar el display/herramienta de servicio", "apagado", "parpadeo", "apagado"),
    aux_led_pattern(18, "Sonda superior o carcasa del compresor", "encendido", "encendido", "parpadeo"),
    aux_led_pattern(19, "Anomalía de recirculación o válvula de cuatro vías", "encendido", "apagado", "parpadeo"),
    aux_led_pattern(20, "Sobrecarga o potencia excesiva del compresor", "apagado", "encendido", "parpadeo"),
    aux_led_pattern(21, "Protección de sobrecorriente", "apagado", "apagado", "parpadeo"),
    aux_led_pattern(22, "Protección por temperatura de descarga", "encendido", "encendido", "apagado"),
    aux_led_pattern(23, "Sobrecarga en refrigeración", "encendido", "apagado", "encendido"),
    aux_led_pattern(24, "Temperatura interior alta en calefacción", "apagado", "encendido", "encendido"),
    aux_led_pattern(25, "Protección antihielo en refrigeración", "encendido", "apagado", "apagado"),
    aux_led_pattern(26, "Temperatura de carcasa del compresor", "apagado", "encendido", "apagado"),
    aux_led_pattern(27, "Protección por sobretensión o subtensión", "apagado", "apagado", "encendido"),
]


def cac_pattern(
    code: str,
    meaning: str,
    display: str,
    control: str = "no indicado",
    *,
    family: str,
) -> dict[str, Any]:
    def indicator(label: str, value: str) -> dict[str, str]:
        lower = value.lower()
        if "destello" in lower:
            state = "pulse"
        elif "parpadeo" in lower:
            state = "blink"
        elif "encendido" in lower:
            state = "on"
        else:
            state = "off"
        return {"label": label, "color": "neutral", "state": state, "detail": value}

    return {
        "code_display": code,
        "indication_type": "commercial_led",
        "display_location": "pilotos de unidad interior/placa de control comercial",
        "family_hint": family,
        "relationship": meaning,
        "led_indicators": [
            indicator("Piloto display/TIMER", display),
            indicator("Piloto placa CONTROL", control),
        ],
        "counting_rule": "Cuente los destellos y mida la pausa; la cadencia cambia entre alimentación monofásica y trifásica.",
        "cycle_note": "Repita la observación durante al menos dos ciclos completos.",
        "sequence": f"Display: {display}. Control: {control}.",
    }


CAC_230_PATTERNS = [
    cac_pattern("E5", "Comunicación interior–exterior", "sin indicación", family="AUX Light Commercial 220–240 V"),
    cac_pattern("E4", "Drenaje o boya", "4 destellos cada 8 s", family="AUX Light Commercial 220–240 V"),
    cac_pattern("E6", "Fase, secuencia o tensión baja", "6 destellos cada 8 s", family="AUX Light Commercial 220–240 V"),
    cac_pattern("E1", "Sonda de aire interior TA", "1 destello cada 8 s", family="AUX Light Commercial 220–240 V"),
    cac_pattern("E3", "Sonda de batería interior TE", "2 destellos cada 8 s", family="AUX Light Commercial 220–240 V"),
    cac_pattern("E2", "Sonda exterior TW; no detiene", "2 destellos cada 1 s", family="AUX Light Commercial 220–240 V"),
    cac_pattern("DEFROST", "Desescarche normal", "piloto OPERATION parpadea", family="AUX Light Commercial 220–240 V"),
]

CAC_400_PATTERNS = [
    cac_pattern("F1", "Comunicación interior–exterior", "5 destellos y 2 s apagado", "2 destellos y 2 s apagado", family="AUX Light Commercial 380–415 V"),
    cac_pattern("E4", "Drenaje o boya", "4 destellos y 2 s apagado", family="AUX Light Commercial 380–415 V"),
    cac_pattern("E6", "Secuencia de fases o fase ausente", "6 destellos y 2 s apagado", family="AUX Light Commercial 380–415 V"),
    cac_pattern("EA", "Temperatura de descarga elevada", "10 destellos y 2 s apagado", "10 destellos y 2 s apagado", family="AUX Light Commercial 380–415 V"),
    cac_pattern("E9 alta", "Protección de alta presión", "9 destellos y 2 s apagado", "1 destello y 2 s apagado", family="AUX Light Commercial 380–415 V"),
    cac_pattern("E9 baja", "Protección de baja presión", "9 destellos y 2 s apagado", "3 destellos y 2 s apagado", family="AUX Light Commercial 380–415 V"),
]


def arv_prefix_pattern(prefix: str, power: str, timing: str) -> dict[str, Any]:
    state_map = {"apagado": "off", "encendido": "on", "parpadeo": "blink"}
    return {
        "code_display": f"{prefix}1–{prefix}F",
        "indication_type": "indoor_three_indicator_hex",
        "display_location": "panel receptor interior ARV",
        "family_hint": "AUX ARV con pilotos POWER, TIMING y RUNNING",
        "relationship": f"Primer carácter {prefix}; RUNNING aporta el segundo carácter hexadecimal.",
        "led_indicators": [
            {"label": "POWER", "color": "green", "state": state_map[power], "detail": power},
            {"label": "TIMING", "color": "yellow", "state": state_map[timing], "detail": timing},
            {"label": "RUNNING", "color": "green", "state": "pulse", "detail": "1–15 destellos = 1–F"},
        ],
        "counting_rule": "POWER y TIMING forman el primer carácter; RUNNING parpadea de 1 a 15 veces para 1…9, A…F.",
        "cycle_note": "Anote estados fijos/parpadeantes y cuente RUNNING durante varios ciclos.",
        "sequence": f"POWER {power}; TIMING {timing}; RUNNING 1–15 = {prefix}1–{prefix}F.",
    }


ARV_INDICATOR_PATTERNS = [
    arv_prefix_pattern("A", "apagado", "apagado"),
    arv_prefix_pattern("C", "apagado", "encendido"),
    arv_prefix_pattern("E", "apagado", "parpadeo"),
    arv_prefix_pattern("H", "encendido", "apagado"),
    arv_prefix_pattern("F", "encendido", "encendido"),
    arv_prefix_pattern("J", "encendido", "parpadeo"),
    arv_prefix_pattern("3", "parpadeo", "apagado"),
    arv_prefix_pattern("4", "parpadeo", "encendido"),
    arv_prefix_pattern("5", "parpadeo", "parpadeo"),
]


add_topic("errors", "same-code-different-layers", "El mismo código cambia según dónde se lea", "AUX reutiliza códigos entre mural, comercial, multisplit y ARV.", [
    v("E8 — mural/display interior", "Mural con display frontal o placa de display separada.", "OFFICIAL", "tabla E8", "Aplicar la interpretación residencial.", "E8 es comunicación entre display y placa principal interior.", system="AUX split", scope="indoor"),
    v("E8 — multisplit/exterior", "Tabla de exterior multi o unidad compacta.", "MULTI", "14-17", "Aplicar la protección exterior.", "E8 es protección por temperatura exterior alta en refrigeración.", system="AUX Multi", scope="outdoor"),
    v("E8 — comercial anterior", "Conductos/cassette Light Commercial con mando cableado.", "CAC", "126", "Aplicar la tabla antigua.", "E8 identifica la sonda de descarga TP.", system="AUX Light Commercial", scope="outdoor"),
    v("H1/H4/F1 también cambian", "Código procedente de una interfaz distinta.", "USA", "familias de producto", "No abrir automáticamente una ficha.", "H1 puede ser drenaje o alta presión; H4 sonda de tubería o baja presión; F1 módulo, sensor de alta o comunicación comercial.", system="AUX"),
])

add_topic("outdoor_diagnostics", "split-d1-d2-d3-master", "Split: tabla completa de pilotos D1/D2/D3", "Veintisiete patrones visuales de la placa exterior.", [
    v("Tabla D1/D2/D3", "PCB exterior con tres pilotos serigrafiados D1, D2 y D3.", "SPLIT", "95-96", "Identificar la protección sin trasladar códigos de otra familia.", "Lea los tres estados a la vez. La tabla incluye espera, compresor activo, servicio forzado, sensores, comunicación, inverter, ventiladores y protecciones frigoríficas.", system="AUX split F-Freedom", scope="outdoor", led_patterns=AUX_THREE_LED_PATTERNS),
    v("Patrón 03 — servicio/prueba", "D1, D2 y D3 encendidos fijos.", "SPLIT", "95", "Reconocer un estado de servicio.", "Los tres pilotos encendidos indican modo forzado o de prueba; no es una avería por sí solo.", system="AUX split F-Freedom", scope="outdoor"),
    v("Patrón 10 — comunicación", "D1 parpadea; D2 y D3 fijos.", "SPLIT", "95", "Separar bus y potencia.", "Corresponde a comunicación interior–exterior. Compruebe alimentación de ambas unidades, cableado y polaridad según esquema.", system="AUX split F-Freedom", scope="system"),
])

add_topic("outdoor_diagnostics", "commercial-led-master", "Comercial: destellos, pausas y código del mando", "Las tablas monofásica y trifásica no son intercambiables.", [
    v("220–240 V", "Unidad comercial monofásica con piloto TIMER/OPERATION.", "CAC", "125", "Traducir el conteo.", "La cadencia de E2 es de un segundo; E1/E3/E4/E6 usan ventanas de ocho segundos. La comunicación puede no encender piloto.", system="AUX Light Commercial 220–240 V", led_patterns=CAC_230_PATTERNS),
    v("380–415 V", "Unidad comercial trifásica con piloto de display y piloto CONTROL BOARD.", "CAC", "125", "Cruzar dos indicadores.", "E9 muestra nueve destellos en display; uno en placa para alta presión y tres para baja.", system="AUX Light Commercial 380–415 V", led_patterns=CAC_400_PATTERNS),
])

add_topic("outdoor_diagnostics", "arv-indicator-code", "ARV: código hexadecimal con POWER, TIMING y RUNNING", "Los dos primeros pilotos forman el prefijo; RUNNING aporta 1–F.", [
    v("Tabla completa de prefijos", "Panel receptor con tres indicadores POWER, TIMING y RUNNING.", "ARV", "123 (PDF 126)", "Reconstruir el código sin display.", "POWER/TIMING forman A, C, E, H, F, J, 3, 4 o 5; RUNNING parpadea de 1 a 15 veces para el segundo carácter.", system="AUX ARV", scope="indoor", led_patterns=ARV_INDICATOR_PATTERNS),
    v("Display de placa exterior", "PCB exterior con display digital.", "ARV", "125 (PDF 128)", "Confirmar la capa exterior.", "La unidad exterior muestra directamente el código en su placa. Conserve el código completo y la dirección de la unidad.", system="AUX ARV", scope="outdoor"),
])

add_topic("diagnostic_access", "arv-check-button", "ARV: obtener el código desde el mando cableado", "El mando no siempre avisa automáticamente.", [
    v("Botón CHECK", "Mando ARV con botón CHECK y display de dos caracteres.", "ARV", "123 (PDF 126)", "Mostrar la avería activa.", "Pulse CHECK para solicitar el código; el primer carácter identifica la familia y el segundo el fallo concreto.", system="AUX ARV", scope="controller", steps=[
        step(1, "Anote el estado y las unidades que están paradas.", phase="prepare"),
        step(2, "Pulse CHECK en el mando cableado."),
        step(3, "Anote los dos caracteres sin invertirlos.", phase="verify"),
        step(4, "Compare con el display exterior y la dirección de unidad.", phase="verify"),
        step(5, "Salga sin borrar hasta haber guardado la evidencia.", phase="finish"),
    ]),
    v("Panel receptor sin display", "Cassette o unidad con pilotos POWER/TIMING/RUNNING.", "ARV", "123 (PDF 126)", "Leer el mismo código por luces.", "Use la combinación de POWER/TIMING para el primer carácter y el conteo RUNNING para el segundo.", system="AUX ARV", scope="indoor"),
])

add_topic("diagnostic_access", "split-code-crosscheck", "Split: cruzar display interior y pilotos exteriores", "No se debe elegir una sola capa.", [
    v("Display E/F/P/L", "Mural muestra un código alfanumérico.", "SPLIT", "62-94", "Localizar la familia de fallo.", "Anote el código exacto, incluida mayúscula, minúscula o prefijo; después lea D1/D2/D3.", system="AUX split"),
    v("Pilotos D1/D2/D3", "La exterior está alimentada y la placa es accesible con seguridad.", "SPLIT", "95-96", "Confirmar sensor, comunicación o potencia.", "Observe los tres estados simultáneamente y compare con la ficha del código interior.", system="AUX split", scope="outdoor"),
])

add_topic("history_reset", "arv-black-box", "ARV: memoria de funcionamiento antes de la avería", "La placa conserva una ventana técnica de 30 minutos.", [
    v("Black box", "Sistema ARV con software o herramienta de servicio compatible.", "ARV", "7", "Analizar fallos intermitentes.", "El manual describe memoria de los treinta minutos previos al fallo. Guarde temperaturas, presiones, frecuencia, EEV y estados antes de rearmar.", system="AUX ARV", scope="outdoor"),
    v("Antes de cortar tensión", "El sistema ha quedado bloqueado.", "ARV", "7, 126-132", "No perder evidencia.", "Fotografíe mando, receptores y display exterior; anote direcciones y Recovery Yes/No antes de resetear.", system="AUX ARV"),
])

add_topic("history_reset", "recovery-versus-reset", "Recuperación automática frente a rearmado", "El manual ARV marca qué errores pueden recuperar.", [
    v("Recovery: Yes", "La tabla marca recuperación.", "ARV", "126-132", "No dar por reparado al recuperar.", "La unidad puede volver cuando desaparece la condición, pero el origen debe revisarse si se repite.", system="AUX ARV"),
    v("Recovery: No", "La tabla no admite recuperación.", "ARV", "126-132", "Rearmar solo después de reparar.", "Corrija cable, componente, configuración o circuito frigorífico y después aplique el reset previsto.", system="AUX ARV"),
    v("Comunicación comercial", "E5/F1 aparece por pérdida de señal.", "CAC", "126", "Distinguir fallo activo y recuperado.", "El manual declara error tras dos minutos consecutivos sin señal correcta y desaparición cuando la comunicación se restablece.", system="AUX Light Commercial"),
])

add_topic("service_modes", "split-forced-service", "Split: modo de servicio o prueba forzada", "El patrón D1/D2/D3 confirma la entrada.", [
    v("Confirmación exterior", "D1, D2 y D3 quedan encendidos.", "SPLIT", "95", "Saber si la orden fue aceptada.", "El patrón 03 identifica modo forzado/de servicio. Las protecciones de potencia y refrigeración continúan siendo relevantes.", system="AUX split", scope="outdoor"),
    v("Salir de la prueba", "La comprobación ha terminado.", "SPLIT", "95-96", "Evitar dejar la máquina forzada.", "Cancele desde el control correspondiente y confirme que la placa vuelve a espera o funcionamiento normal.", system="AUX split"),
])

add_topic("service_modes", "multi-test-run", "Multisplit: prueba de funcionamiento", "La comprobación se hace con válvulas abiertas y tiempo suficiente.", [
    v("Prueba en refrigeración", "Instalación multi terminada y todas las válvulas abiertas.", "MULTI", "44", "Validar conexiones y rendimiento.", "Arranque en frío durante al menos treinta minutos. Compruebe que la diferencia entre salida y entrada supera aproximadamente 10 °C.", system="AUX Multi", steps=[
        step(1, "Confirme válvulas completamente abiertas y conexiones correctas.", phase="prepare", warning="warning"),
        step(2, "Ponga las interiores en refrigeración."),
        step(3, "Mantenga la prueba al menos treinta minutos."),
        step(4, "Mida temperaturas de entrada y salida; compruebe una diferencia superior a 10 °C.", phase="verify"),
        step(5, "Revise códigos y pare de forma normal.", phase="finish"),
    ]),
    v("Conflicto de modo durante prueba", "Una interior pide calor y otra frío.", "MULTI", "11", "No confundir rechazo con avería.", "La primera interior determina el modo de la exterior; una orden incompatible puede producir tres pitidos y apagarse automáticamente.", system="AUX Multi"),
])

add_topic("configuration", "arv-priority-address", "ARV: prioridad, dirección y combinación", "El sistema permite distintas prioridades de modo.", [
    v("Prioridad de calefacción", "Ajuste de sistema por defecto documentado.", "ARV", "5-6, 126", "Interpretar AE.", "Una interior que solicita frío puede quedar en espera y mostrar conflicto de modo cuando domina calefacción.", system="AUX ARV"),
    v("Otras prioridades", "Configuración de frío, primera unidad o mayoría.", "ARV", "5-6", "Adaptar el sistema a la instalación.", "El manual contempla prioridad de calefacción, refrigeración, primera orden y mayoría; registre el ajuste antes de modificarlo.", system="AUX ARV"),
    v("Capacidad 50–130 %", "AJ/JJ durante puesta en marcha.", "ARV", "126, 128", "Corregir combinación.", "La suma de interiores debe quedar entre el 50 % y el 130 % de la capacidad exterior en la familia revisada.", system="AUX ARV"),
])

add_topic("configuration", "arv-dip-settings", "ARV: DIP de capacidad, tipo y cantidad de unidades", "Copie los ajustes antes de sustituir la placa.", [
    v("Capacidad de la exterior", "PCB exterior con banco DIP de capacidad.", "ARV", "120 (PDF 123)", "Identificar la máquina para el control.", "La combinación de interruptores declara capacidad; una posición errónea altera límites y puede generar fallos de combinación.", system="AUX ARV", scope="outdoor"),
    v("Tipo y cantidad de unidades", "Instalación individual o combinada.", "ARV", "120 (PDF 123)", "Restaurar configuración.", "El manual muestra selectores de tipo, cantidad interior/exterior y bloqueo. Fotografíe la placa original.", system="AUX ARV", scope="outdoor"),
])

add_topic("configuration", "xk-controller-functions", "Mando XK: funciones útiles y restablecimientos", "Las combinaciones son del mando documentado, no universales.", [
    v("Bloqueo infantil", "Mando XK con teclas ▲ y ▼.", "XK", "14", "Bloquear o liberar teclas.", "Mantenga ▲ y ▼ más de cinco segundos. Un ciclo de alimentación también elimina el bloqueo.", system="AUX XK", scope="controller"),
    v("Borrar aviso CL de filtro", "CL parpadea cinco veces al apagar.", "XK", "17", "Reiniciar el recordatorio.", "Mantenga TIMER durante cinco segundos después de limpiar el filtro.", system="AUX XK", scope="controller"),
    v("Emparejamiento Wi‑Fi", "Unidad compatible con control inalámbrico.", "XK", "20", "Entrar en configuración.", "Pulse HEALTH ocho veces; dos pitidos confirman la orden.", system="AUX XK", scope="controller"),
    v("Borrar aviso de fuga en VRF", "El sistema ha sido revisado y el mando XK conserva el aviso.", "XK", "16", "Rearmar la indicación documentada.", "Mantenga SWING y FUNCTION durante cinco segundos (5 s). Como alternativa, el manual admite diez órdenes ON/OFF consecutivas con intervalos máximos de dos segundos; dos pitidos confirman el borrado.", system="AUX XK/VRF", scope="controller", steps=[
        step(1, "Repare y compruebe primero la causa de la indicación de fuga.", phase="prepare", warning="warning"),
        step(2, "Mantenga SWING + FUNCTION durante cinco segundos."),
        step(3, "Confirme los dos pitidos y verifique que el aviso desaparece.", phase="verify"),
        step(4, "Si usa la alternativa, envíe diez órdenes ON/OFF con intervalos no superiores a dos segundos.", phase="procedure"),
    ]),
    v("Prioridad de visualización de errores", "El mando alterna temperatura, iconos y código.", "XK", "17", "Reconocer una avería activa.", "El error tiene la prioridad de visualización más alta y aparece como XXE parpadeando en la zona de temperatura. Anote XX antes de reiniciar.", system="AUX XK", scope="controller"),
])

add_topic("controllers_buses", "xk-wiring", "Mando XK: dos variantes de cableado", "La bornera identifica si es control estándar o ARV.", [
    v("Mando estándar de dos terminales", "Base con dos bornes de comunicación/alimentación.", "XK", "25", "Cablear la variante correcta.", "Use el cable apantallado indicado, mantenga separación de potencia y coloque el núcleo de ferrita cerca del mando.", system="AUX XK", scope="controller", controller_data=core.controller("mando cableado XK", "bus AUX de unidad interior", "2 hilos", "según bornes del equipo", "12 V CC", "dos terminales")),
    v("Variante ARV de cuatro terminales", "Bornera marcada 12V, GND, A y B.", "XK", "25", "Separar alimentación y datos.", "12V/GND alimentan el mando; A/B forman el enlace de comunicación. No intercambie la variante con el mando de dos bornes.", system="AUX XK/ARV", scope="controller", controller_data=core.controller("mando cableado XK ARV", "bus AUX ARV", "4 hilos", "12V/GND polarizados y A/B de datos", "12 V CC", "12V, GND, A, B")),
    v("Longitud y ferrita", "Instalación del cable del mando.", "XK", "5, 23", "Evitar errores de comunicación.", "La guía cita longitud máxima de 30 m y cinco vueltas sobre el núcleo de ferrita cerca del controlador.", system="AUX XK", scope="controller"),
])

add_topic("controllers_buses", "controller-startup-errors", "Arranque y fallos del propio mando", "H2/AA pertenecen al tramo mando–interior.", [
    v("Al alimentar", "Pantalla del XK apagada o recién energizada.", "XK", "5, 17", "Distinguir arranque y avería.", "El mando trabaja a 12 V CC. El primer toque con retroiluminación apagada puede limitarse a despertar la pantalla antes de ejecutar la orden.", system="AUX XK", scope="controller"),
    v("H2 — comunicación de mando", "Tabla Multi de mural/control cableado.", "MULTI", "14", "Aislar el enlace local.", "Revise 12 V, bornes, continuidad, polaridad de la variante, apantallado y placa interior.", system="AUX Multi", scope="controller"),
    v("AA — comunicación mando/interior", "Cassette, techo-suelo o conductos con código A.", "ARV", "126", "Aplicar la tabla ARV/compacta.", "No confundir AA con A9: AA es mando–interior; A9 es interior–exterior.", system="AUX ARV", scope="controller"),
])

add_topic("controllers_buses", "arv-transmission-bus", "ARV: red de comunicación", "El bus interior–exterior es distinto de la alimentación del mando.", [
    v("Par apantallado de dos conductores", "Red entre exteriores e interiores ARV.", "ARV", "6", "Evitar J2/A9.", "La documentación revisada indica par apantallado de dos hilos y no polarizado para la transmisión del sistema.", system="AUX ARV"),
    v("Mando 12V/GND/A/B", "Control XK ARV conectado a una interior.", "XK", "25", "No mezclar redes.", "El mando usa alimentación 12V/GND y datos A/B; no es el mismo tramo que el bus principal de dos hilos.", system="AUX ARV", scope="controller"),
])

add_topic("drainage_overflow", "drain-code-map", "Drenaje: A5, E4 y H1 según la familia", "Los tres pueden apuntar a boya, bomba o tubería.", [
    v("A5 — cassette/ARV", "Código A5 en mando o receptor.", "ARV", "126", "Diagnosticar el nivel.", "Compruebe alimentación de bomba, interruptor/ boya, bomba, atasco o contrapendiente y placa interior.", system="AUX ARV/cassette", scope="indoor"),
    v("E4 — comercial anterior", "Mando comercial muestra E4 o TIMER parpadea cuatro veces.", "CAC", "125", "Aplicar la tabla comercial.", "La protección detiene la unidad; compruebe nivel, flotador, drenaje y salida de bomba.", system="AUX Light Commercial", scope="indoor"),
    v("H1 — multisplit compacto", "Tabla Multi de cassette/conductos.", "MULTI", "14", "No confundir con alta presión.", "H1 puede ser drenaje en esta familia. En otra tabla AUX, H1 identifica alta presión.", system="AUX Multi", scope="indoor"),
])

add_topic("drainage_overflow", "cassette-drain-test", "Cassette: prueba de drenaje y montaje", "La prueba se hace incluso en instalaciones solo calefacción.", [
    v("Prueba con agua", "Cassette recién instalada antes de cerrar techo.", "CAC", "29", "Confirmar evacuación real.", "Vierta agua de prueba, compruebe bomba y salida sin fugas. El manual exige la prueba aunque la instalación vaya a usarse solo en calefacción.", system="AUX cassette", scope="indoor"),
    v("Altura y pendiente", "Bomba trabaja pero el agua retorna.", "CAC", "29", "Corregir hidráulica.", "La familia revisada permite elevación hasta 1200 mm y requiere pendiente aproximada entre 1:50 y 1:100; el drenaje común debe quedar por debajo de las salidas.", system="AUX cassette", scope="indoor"),
    v("Boya atascada en frío o calor", "El error aparece fuera de refrigeración.", "ARV", "126", "No descartar el flotador por el modo.", "A5 se genera por la lógica de nivel/bomba; una boya mecánicamente trabada puede mantener la alarma aunque no haya condensación nueva.", system="AUX cassette/ARV", scope="indoor"),
])

add_topic("commissioning", "arv-commissioning", "ARV: puesta en marcha completa", "La secuencia evita diagnósticos falsos por red, carga o válvulas.", [
    v("Antes de alimentar", "Instalación ARV nueva.", "ARV", "116 (PDF 119)", "Preparar la prueba.", "Confirme que tubería y red pertenecen al mismo ciclo, tensión dentro de ±10 %, secuencia de fases, prueba de nitrógeno 24 h, vacío, carga y válvulas abiertas.", system="AUX ARV"),
    v("Precalentamiento", "La exterior ha estado sin tensión.", "ARV", "116-117 (PDF 119-120)", "Proteger el compresor.", "Alimente la exterior ocho horas antes del arranque normal. En la prueba invernal tras corte, el manual no permite Trial hasta al menos 2,5 h energizada.", system="AUX ARV", scope="outdoor"),
    v("Prueba en refrigeración", "Todas las interiores disponibles.", "ARV", "118 (PDF 121)", "Validar capacidad y válvulas.", "Ponga todas en frío, alta velocidad y 16 °C; estabilice una hora, registre parámetros y apague interiores una a una para comprobar que cada EEV cierra en espera.", system="AUX ARV"),
    v("Prueba en calefacción", "Temperatura exterior inferior a 21 °C.", "ARV", "119 (PDF 122)", "Validar el ciclo en calor.", "Ponga todas en calor, alta velocidad y 30 °C; estabilice una hora y deje después una sola interior para observar el comportamiento y posibles fugas de válvula.", system="AUX ARV"),
])

add_topic("commissioning", "commercial-startup", "Comercial: puesta en marcha, comunicación y fases", "La alimentación cambia la tabla de diagnóstico.", [
    v("220–240 V", "Comercial monofásica.", "CAC", "125-126", "Aplicar pilotos correctos.", "Revise tensión, comunicación y sensores; E5 puede no producir piloto aunque sí pare la unidad.", system="AUX Light Commercial"),
    v("380–415 V", "Comercial trifásica.", "CAC", "125", "Evitar E6/HJ.", "Compruebe presencia y secuencia de las tres fases antes de investigar compresor o placa.", system="AUX Light Commercial"),
])

add_topic("multisplit", "multi-mode-conflict", "Multisplit: la primera unidad determina el modo", "Una petición incompatible puede apagarse sin avería de hardware.", [
    v("Primera unidad en frío", "Otra interior pide calor.", "MULTI", "11", "Interpretar los tres pitidos.", "La nueva orden incompatible recibe tres avisos acústicos y la unidad se apaga automáticamente.", system="AUX Multi"),
    v("Primera unidad en calor", "Otra interior pide frío o deshumidificación.", "MULTI", "11", "No buscar un compresor averiado.", "El sistema mantiene el modo común. Revise la unidad que inició primero y las consignas del resto.", system="AUX Multi"),
])

add_topic("multisplit", "multi-code-layers", "Multisplit: display interior, mando y placa exterior", "El código cambia de formato entre capas.", [
    v("Interior mural", "Display con E/F/H/L/P.", "MULTI", "12-14", "Identificar el elemento local.", "H2 es mando; H3/H4 sondas; H1 puede ser drenaje en compactas.", system="AUX Multi", scope="indoor"),
    v("Compacta A1–AA", "Cassette, conductos slim, techo-suelo.", "MULTI", "15-16", "Usar la tabla A.", "A5 drenaje, A6 ventilador, A9 comunicación interior–exterior y AA mando–interior.", system="AUX Multi", scope="indoor"),
    v("Exterior 31–41/J/C", "Display o placa de la unidad exterior.", "MULTI", "14-17", "Localizar la capa común.", "Los códigos numéricos separan inverter, compresor, tensión y ventilador; J/C cubren comunicación, memoria y sensores.", system="AUX Multi", scope="outdoor"),
])

add_topic("multisplit", "multi-operational-effect", "Multisplit: qué unidades se paran", "El alcance depende de si el fallo es local o común.", [
    v("Fallo local interior", "A1–A8/H2–H4 en una sola unidad.", "MULTI", "12-16", "Mantener el resto cuando sea posible.", "Se detiene o limita la unidad afectada; las demás pueden continuar si solicitan un modo compatible y la exterior está disponible.", system="AUX Multi", scope="indoor"),
    v("Fallo de exterior o ciclo", "P/F/L/31–41 en la unidad exterior.", "MULTI", "12-17", "Reconocer la parada común.", "Presión, compresor, inverter, alimentación o ventilador exterior afectan a todas las interiores conectadas al mismo ciclo.", system="AUX Multi", scope="outdoor"),
])

add_topic("vrf_network", "arv-address-network", "ARV: auto-addressing y red", "Las direcciones y la red deben cerrar antes del Test Run.", [
    v("Direccionamiento automático", "Todas las unidades alimentadas y bus terminado.", "ARV", "5-6, 116-120", "Registrar interiores.", "Ejecute la adquisición prevista y compare el número reconocido con la instalación antes de probar.", system="AUX ARV"),
    v("AH — dirección duplicada", "Dos interiores comparten dirección.", "ARV", "126", "Corregir identidad.", "Cambie la dirección repetida, reinicie adquisición y verifique que ambas unidades aparecen.", system="AUX ARV"),
    v("47 — unidad interior perdida", "La exterior deja de ver una interior registrada.", "ARV", "129 (PDF 132)", "Aislar alimentación o bus.", "Compruebe alimentación de la interior, fusible, cable, derivación, blindaje y dirección.", system="AUX ARV"),
])

add_topic("vrf_network", "arv-priority-protections", "ARV: prioridad de controles y alcance", "Protección, desescarche y retorno de aceite tienen un orden definido.", [
    v("Orden de prioridad", "Coinciden varias secuencias.", "ARV", "72-75", "Interpretar cambios de estado.", "Las protecciones tienen prioridad sobre desescarche y este sobre retorno de aceite.", system="AUX ARV"),
    v("Baja presión durante desescarche", "Sistema en desescarche.", "ARV", "72-75", "No interpretar una vigilancia anulada como sensor roto.", "La protección de baja presión queda inactiva durante la secuencia de desescarche documentada.", system="AUX ARV"),
    v("Parada del ciclo", "Error exterior no recuperable.", "ARV", "126-132", "Saber qué afecta.", "Una protección exterior común detiene el ciclo; un error local recuperable puede permitir que otras interiores continúen.", system="AUX ARV"),
])

add_topic("component_checks", "communication-layers", "Comunicación por tramos", "AA/H2, A9/E5/J2 y J3/F8 no son el mismo enlace.", [
    v("Mando–interior: H2/AA", "El mando no controla o muestra error.", "MULTI", "14-16", "Aislar el primer tramo.", "Compruebe 12 V, GND, A/B o los dos bornes de la variante, continuidad y placa interior.", system="AUX", scope="controller"),
    v("Interior–exterior: E5/5E/A9/J2", "La interior no recibe respuesta exterior.", "SPLIT", "62-94", "Aislar red y potencia.", "Verifique alimentación de ambas unidades, cableado, bornes, ruido y direcciones en ARV.", system="AUX"),
    v("Placa principal–driver: F8/J3", "La exterior está alimentada, pero el inverter no comunica.", "MULTI", "14-17", "Separar enlace interno.", "Compruebe fuentes, conectores y mazo interno antes de sustituir driver o placa principal.", system="AUX", scope="outdoor"),
])

add_topic("component_checks", "sensor-families", "Sondas: valor y función dependen de la familia", "No se aplica una única curva NTC a toda AUX.", [
    v("Split ambiente interior", "E1 en mural de la familia revisada.", "SPLIT", "65", "Comprobar NTC.", "Aproximadamente 15 kΩ a 25 °C; revise cable, conector, variación térmica y entrada de placa.", system="AUX split", scope="indoor"),
    v("Split batería interior/exterior", "E2 o E3 en mural.", "SPLIT", "66-68", "Comprobar NTC.", "Aproximadamente 20 kΩ a 25 °C en la familia revisada; algunas generaciones interiores antiguas citan 5 kΩ.", system="AUX split"),
    v("Comercial 5K3470", "TA/TE/TW de la familia Light Commercial.", "CAC", "155", "Aplicar la curva correcta.", "La tabla documenta NTC 5K3470: 5,000 kΩ a 25 °C.", system="AUX Light Commercial"),
    v("ARV descarga 50K3950", "Sonda del compresor ARV.", "ARV", "131 (PDF 134)", "Aplicar la curva de alta temperatura.", "R25 = 50 kΩ ±1 % y B = 3950 ±1 % para la sonda documentada.", system="AUX ARV", scope="outdoor"),
])

add_topic("component_checks", "fan-inverter-compressor", "Ventiladores, inverter y compresor", "Los códigos separan motor, driver y carga frigorífica.", [
    v("Ventilador interior E4/A6", "La turbina no gira o pierde realimentación.", "SPLIT", "69-70", "Separar bloqueo, motor y PCB.", "Corte tensión, compruebe giro libre, conectores, alimentación y señal de retorno; no conecte motores DC energizados.", system="AUX", scope="indoor"),
    v("Ventilador exterior F0/3H/3C/41", "La hélice exterior no arranca o se para.", "MULTI", "12-17", "Separar motor e IPM.", "Compruebe bloqueo, devanados, driver, IPM de ventilador y fuente antes de cambiar la placa.", system="AUX", scope="outdoor"),
    v("Compresor F3/L2/LA/34/35", "El inverter intenta arrancar y corta.", "ARV", "129 (PDF 132)", "Aislar potencia y mecánica.", "Compruebe tensión, bus, U‑V‑W, aislamiento, presiones equilibradas y bloqueo antes de condenar el compresor.", system="AUX", scope="outdoor"),
])

add_topic("component_checks", "pressure-refrigerant", "Presión, falta de gas y válvula de cuatro vías", "P3/H5/F6 y E3 no son equivalentes.", [
    v("Falta de refrigerante P3/H5", "La protección informa carga insuficiente.", "ARV", "128 (PDF 131)", "Confirmar fuga y carga.", "Busque fugas, confirme carga adicional, válvulas abiertas, caudal y temperatura antes de recargar.", system="AUX"),
    v("Alta presión P2/F3/H1", "La tabla correspondiente marca alta.", "ARV", "127-128 (PDF 130-131)", "Separar caudal y sensor.", "Compruebe intercambiadores, ventiladores, válvulas, carga y presostato/transductor.", system="AUX"),
    v("Sin diferencia FA", "Alta y baja no se separan.", "ARV", "128 (PDF 131)", "Comprobar inversión de ciclo.", "El manual relaciona FA con válvula de cuatro vías bloqueada o incapaz de conmutar.", system="AUX ARV", scope="outdoor"),
])

add_topic("technical_values", "quick-values", "Valores rápidos documentados", "Cada cifra queda unida a su fuente y familia.", [
    v("Mando XK", "Control cableado actual.", "XK", "5, 23, 25", "Comprobar alimentación e instalación.", "12 V CC, longitud máxima 30 m y cinco vueltas en la ferrita cerca del mando.", system="AUX XK", scope="controller"),
    v("Sondas split", "E1/E2/E3 mural.", "SPLIT", "65-68", "Comparar a 25 °C.", "Ambiente interior ~15 kΩ; batería exterior/interior ~20 kΩ en la familia revisada.", system="AUX split"),
    v("Sonda comercial", "TA/TE/TW Light Commercial.", "CAC", "155", "Comparar a 25 °C.", "Curva 5K3470: 5,000 kΩ a 25 °C.", system="AUX Light Commercial"),
    v("Sonda ARV de descarga", "Compresor ARV.", "ARV", "131 (PDF 134)", "Comparar curva.", "R25 = 50 kΩ ±1 %; B = 3950 ±1 %.", system="AUX ARV"),
    v("Bus DC ARV", "Código 36.", "ARV", "129 (PDF 132)", "Comprobar protección.", "La tabla cita protección con bus inferior a 420 V o superior a 642 V.", system="AUX ARV", scope="outdoor"),
])

add_topic("technical_values", "time-thresholds", "Tiempos y umbrales de diagnóstico", "Evita interpretar antes de que la máquina confirme la condición.", [
    v("Comunicación comercial", "E5/F1.", "CAC", "126", "Esperar el criterio real.", "La unidad declara el fallo tras dos minutos consecutivos sin comunicación correcta.", system="AUX Light Commercial"),
    v("Prueba Multi", "Comprobación de rendimiento.", "MULTI", "44", "Estabilizar el sistema.", "Mantenga refrigeración al menos treinta minutos y busque diferencia aire entrada/salida superior a 10 °C.", system="AUX Multi"),
    v("ARV módulo inverter", "Código 39.", "ARV", "129 (PDF 132)", "Confirmar protección térmica.", "La tabla documenta parada por temperatura del módulo superior a 94 °C.", system="AUX ARV"),
    v("Precalentamiento ARV", "Exterior recién alimentada.", "ARV", "116-117 (PDF 119-120)", "Proteger compresor.", "Ocho horas antes de arranque normal; al menos 2,5 h para Trial invernal tras corte según el procedimiento revisado.", system="AUX ARV"),
])

add_topic("normal_states", "defrost-oil-return", "Desescarche y retorno de aceite", "Son secuencias normales que cambian ventiladores, EEV y frecuencia.", [
    v("Desescarche", "Calefacción con exterior fría; icono DEFROST.", "XK", "17", "No confundir con avería.", "El mando XK usa el icono DEFROST también para indicar retorno de aceite; observe el sistema y el historial.", system="AUX"),
    v("Retorno de aceite", "ARV trabaja a baja frecuencia durante horas.", "ARV", "72-75", "No interrumpir la secuencia.", "El manual indica retorno cada 2–4 h de baja frecuencia y una duración aproximada de seis minutos.", system="AUX ARV"),
    v("Prioridad de control", "Coinciden protección, desescarche y aceite.", "ARV", "72-75", "Interpretar la lógica.", "Protecciones > desescarche > retorno de aceite.", system="AUX ARV"),
])

add_topic("normal_states", "normal-waits-conflict", "Esperas que parecen averías", "Conflicto de modo y post-marcha no condenan componentes.", [
    v("Conflicto de modo", "Multi/ARV con órdenes frío y calor simultáneas.", "MULTI", "11", "Explicar la parada de una interior.", "La unidad incompatible puede pitar tres veces, apagarse o mostrar AE mientras el modo común continúa.", system="AUX Multi/ARV"),
    v("Display CL", "Mando XK al apagar.", "XK", "17", "Reconocer recordatorio de filtro.", "CL parpadea cinco veces; no es un código frigorífico. Limpie y mantenga TIMER cinco segundos.", system="AUX XK", scope="controller"),
    v("Primer toque del mando", "Retroiluminación apagada.", "XK", "14", "No confundir con tecla inoperante.", "El primer toque puede limitarse a encender la pantalla; repita la orden cuando quede activa.", system="AUX XK", scope="controller"),
])

add_topic("service_tools_boards", "arv-monitoring", "ARV: monitorización y memoria técnica", "Los parámetros deben guardarse antes de borrar.", [
    v("Ventana Black Box", "Fallo exterior intermitente.", "ARV", "7", "Reconstruir la avería.", "Recupere los treinta minutos previos: presión, temperatura, frecuencia, corriente, EEV y estado de unidades.", system="AUX ARV"),
    v("Comprobación de interiores en espera", "Commissioning en frío.", "ARV", "118 (PDF 121)", "Detectar EEV que no cierra.", "Apague interiores una a una y compruebe desde monitorización que su EEV se cierra en standby.", system="AUX ARV"),
])

add_topic("service_tools_boards", "board-replacement", "Después de sustituir una placa", "Copiar configuración evita fallos falsos.", [
    v("PCB exterior ARV", "J7/32 o placa sustituida.", "ARV", "120, 126-132", "Restaurar identidad.", "Copie capacidad, tipo, cantidad de unidades, dirección y DIP antes de energizar; repita adquisición y Test Run.", system="AUX ARV", scope="outdoor"),
    v("PCB interior", "Eb/A8 tras sustitución.", "SPLIT", "62-94", "Restaurar configuración.", "Compruebe referencia, EEPROM, dirección, mando, sensores y comunicación antes de declarar otra avería.", system="AUX", scope="indoor"),
    v("Driver inverter", "F8/J3 tras sustituir.", "ARV", "129 (PDF 132)", "Validar enlace interno.", "Revise alimentación, conectores y compatibilidad de driver/placa; no cambie compresor por un error de comunicación interno.", system="AUX", scope="outdoor"),
])

add_topic("system_architecture", "recognize-aux-family", "Reconocer qué AUX tiene delante", "La pantalla y la placa valen más que memorizar el modelo.", [
    v("Split mural", "Display E/F/P/L y exterior con D1/D2/D3.", "SPLIT", "62-96", "Aplicar la tabla residencial.", "Cruce el código interior con los tres pilotos exteriores.", system="AUX split"),
    v("Light Commercial", "Cassette/conductos con mando cableado y pilotos TIMER/CONTROL.", "CAC", "125-126", "Aplicar tabla por alimentación.", "Distinga 220–240 V de 380–415 V antes de contar destellos.", system="AUX Light Commercial"),
    v("Multi", "Varias interiores comparten exterior; códigos H/A/J/3.", "MULTI", "11-17", "Separar unidad local y ciclo común.", "Anote qué interior muestra el error y lea después la exterior.", system="AUX Multi"),
    v("ARV/VRF", "Muchas interiores, red de dos hilos, CHECK, POWER/TIMING/RUNNING y display exterior.", "ARV", "5-8, 123-132", "Conservar código y dirección.", "Use CHECK o los tres indicadores y confirme el código en la PCB exterior.", system="AUX ARV"),
])

add_topic("system_architecture", "aux-search-strategy", "Cómo buscar sin perder interpretaciones", "La aplicación muestra primero todas las fichas cerradas.", [
    v("Buscar por código", "El técnico conoce E8, H1, F1 u otro.", "OFFICIAL", "tabla de códigos", "Ver todas las posibilidades.", "Seleccione AUX y el código; compare título, tipo de máquina y lugar de lectura antes de abrir.", system="Super Técnico"),
    v("Buscar por síntoma o interfaz", "No se conoce el código exacto.", "USA", "familias de producto", "Llegar por contexto.", "Busque 'D1 D2 D3', 'CHECK ARV', 'bomba cassette', 'mando 12V GND A B' o '9 destellos'.", system="Super Técnico"),
    v("Conservar la capa de lectura", "Hay código en mando y otro en exterior.", "MULTI", "12-17", "No sustituir uno por otro.", "Guarde ambos: pueden ser equivalentes, complementarios o pertenecer a fallos diferentes.", system="Super Técnico"),
])


def write_json(path: Path, value: Any) -> None:
    core.write_json(path, value)


def build() -> dict[str, int]:
    if BRAND_DIR.exists():
        try:
            shutil.rmtree(BRAND_DIR)
        except PermissionError:
            # OneDrive/antivirus can retain the now-empty directory briefly on
            # Windows. rmtree has already removed its contents in that case.
            pass
    WEB_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    error_index, error_details = core.build_errors()
    topics = core.build_topics()
    search_entries = core.build_search(error_index, error_details, topics)

    write_json(WEB_DIR / "errors" / "index.json", error_index)
    for row in error_details:
        write_json(WEB_DIR / "errors" / "details" / f'{row["id"]}.json', row)
    for topic in topics:
        write_json(WEB_DIR / "topics" / f'{topic["id"]}.json', topic)
    write_json(WEB_DIR / "search.json", search_entries)
    write_json(WEB_DIR / "variant_map.json", {
        str(row["id"]): topic["id"] for topic in topics for row in topic["variants"]
    })

    by_category: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for topic in topics:
        by_category[topic["category_id"]].append({
            "id": topic["id"],
            "slug": topic["slug"],
            "title": topic["title"],
            "summary": topic["summary"],
            "active": 1,
            "variant_count": len(topic["variants"]),
        })
    categories = [{
        "id": ident,
        "slug": slug,
        "name": name,
        "description": description,
        "sort_order": ident * 10,
        "active": 1,
        "topics": by_category[ident],
    } for ident, slug, name, description in core.CATEGORIES]
    write_json(WEB_DIR / "navigation.json", {
        "metadata": {
            "schema_name": "Super Tecnico",
            "navigation_model": "brand_category_topic_variant",
            "schema_version": "2.3.0",
            "data_version": "1.0.0",
            "last_update_utc": now,
            "reference_brand": "AUX",
            "verification_warning": (
                "Completa respecto al corpus AUX Referencia V1. Confirme siempre "
                "dónde se leyó el código: display interior, mando, pilotos "
                "D1/D2/D3, placa comercial, multisplit o ARV."
            ),
        },
        "categories": categories,
    })
    write_json(WEB_DIR / "sources.json", [{
        "id": ident,
        "brand_id": BRAND_ID,
        "title": row["title"],
        "document_ref": row["document_ref"],
        "document_type": row["type"],
        "publication_date": row["year"],
        "language": "es/en",
        "source_url": row["source_url"],
        "status": "reviewed",
        "notes": "Fuente revisada para AUX Referencia V1.",
    } for ident, row in enumerate(core.SOURCES.values(), start=1)])
    write_json(WEB_DIR / "coverage.json", [{
        "id": ident,
        "brand_id": BRAND_ID,
        "area_slug": slug,
        "area_name": name,
        "equipment_scope": "AUX — split, Light Commercial, cassette/conductos, multisplit, mando XK y ARV/VRF",
        "coverage_status": "reference_v1",
        "source_count": len(core.SOURCES),
        "notes": description,
        "last_reviewed": "2026-07-29",
    } for ident, slug, name, description in core.CATEGORIES])
    counts = {
        "categories": len(core.CATEGORIES),
        "topics": len(topics),
        "variants": sum(len(topic["variants"]) for topic in topics),
        "errors": len(error_index),
        "search_entries": len(search_entries),
    }
    write_json(BRAND_DIR / "brand.json", {
        "slug": "aux-air",
        "name": "AUX",
        "display_name": "AUX",
        "enabled": True,
        "web_data": "web",
        "media": "media",
        "publish_media": False,
        "static_site": True,
        "schema_version": "2.3.0",
        "data_version": "1.0.0",
        "exported_at_utc": now,
        "counts": counts,
        "notes": (
            "AUX Referencia V1: split, Light Commercial, cassette/conductos, "
            "multisplit, mando XK y ARV/VRF; incluye diferencias por pantalla, "
            "tabla completa D1/D2/D3, pilotos comerciales, código ARV por tres "
            "indicadores, procedimientos, drenaje, programación y valores."
        ),
    })
    return counts


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
