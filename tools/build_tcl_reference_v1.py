#!/usr/bin/env python3
"""Construye TCL Referencia V1 para Super Técnico.

La proyección pública contiene resúmenes técnicos trazables. Los PDF, las
capturas y la base maestra no se publican. Los códigos se separan por familia
y, sobre todo, por el lugar donde se leen: display interior, mando, cassette
o piloto de la placa exterior.
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
BRAND_DIR = ROOT / "data" / "brands" / "tcl"
WEB_DIR = BRAND_DIR / "web"
BRAND_ID = 12

core.BRAND_DIR = BRAND_DIR
core.WEB_DIR = WEB_DIR
core.BRAND_ID = BRAND_ID

core.SOURCES = {
    "XA81": {
        "title": "TCL Elite XA81 Inverter — Service Manual",
        "document_ref": "TCL-XA81-SERVICE",
        "source_url": "https://aws-obg-image-lb-4.tcl.com/content/dam/brandsite/region/maylaysia/download/air-conditioners/xa81i/ac-new-elite-series-inverter.pdf",
        "type": "service_manual", "year": "2022",
    },
    "TPRO": {
        "title": "TCL T‑Pro Inverter — Service Manual",
        "document_ref": "TCL-TPRO-INVERTER-SM",
        "source_url": "https://tcl-aircon.ua/wp-content/uploads/2025/06/t-pro-inveter-service-manual.pdf",
        "type": "service_manual", "year": "2025",
    },
    "COMM": {
        "title": "TCL Commercial, Duct and Cassette — Service Manual",
        "document_ref": "TCL-COMMERCIAL-CASSETTE-SM",
        "source_url": "https://tcl-aircon.ua/wp-content/uploads/2023/09/12b0f4a5e7caa929a48a50f215d04d01.pdf",
        "type": "service_manual", "year": "2018",
    },
    "FREE": {
        "title": "TCL Free Match R32 — Service Manual",
        "document_ref": "TCL-FREE-MATCH-R32-SM",
        "source_url": "https://tcl-aircon.ua/wp-content/uploads/2023/09/054509d08e4f6a06983e41c691824c6e.pdf",
        "type": "service_manual", "year": "2020",
    },
    "WIRE": {
        "title": "TCL WIREDCASCTRL — Wired Controller Manual",
        "document_ref": "TCL-WIREDCASCTRL",
        "source_url": "https://manualsfile.com/product/pb5q749elo.html",
        "type": "controller_manual", "year": "2021",
    },
    "TMV6": {
        "title": "TCL TMV6+ Super VRF — Technical Catalogue",
        "document_ref": "TCL-TMV6PLUS-SUPER-VRF",
        "source_url": "https://www.tcl.com/content/dam/brandsite/global/cac/download/r410a-tmv6plus-super-vrf.pdf",
        "type": "technical_catalog", "year": "2025",
    },
    "PORT": {
        "title": "TCL Portable Air Conditioner — Display Codes",
        "document_ref": "TCL-SUPPORT-PORTABLE-CODES",
        "source_url": "https://support.tcl.com/en_US/portable-ac-codes",
        "type": "official_web", "year": "actualizado",
    },
    "VRFWEB": {
        "title": "TCL TMV6+ Super VRF — Product Information",
        "document_ref": "TCL-TMV6PLUS-WEB",
        "source_url": "https://www.tcl.com/global/en/commercial-air-conditioner/vrf/tmv6-plus-super",
        "type": "official_web", "year": "actualizado",
    },
}

core.CATEGORIES = [
    (1, "errors", "Errores y protecciones", "Códigos de display, mando, cassette, multisplit, exterior y portátil."),
    (2, "outdoor_diagnostics", "Pilotos y display de la unidad exterior", "Conteo de destellos y equivalencias con el código interior."),
    (3, "diagnostic_access", "Obtención de códigos y subcódigos", "Consulta desde mando inalámbrico, cableado, display y PCB."),
    (4, "history_reset", "Historial y borrado", "Errores actuales, cinco históricos y recuperación de códigos."),
    (5, "service_modes", "Modos de servicio", "Emergencia, Test Run, desescarche forzado y generador."),
    (6, "configuration", "Configuración y programación", "Parámetros de mando, direcciones, memoria y límites."),
    (7, "controllers_buses", "Mandos y buses", "Mando cableado, arranque, comunicación, CAN y RS485."),
    (8, "drainage_overflow", "Drenaje y desbordamiento", "Boya, bomba, temporizaciones y D3."),
    (9, "commissioning", "Puesta en marcha", "Pruebas, auto-addressing y comprobación de comunicación."),
    (10, "multisplit", "Multisplit y Free Match", "Ramas, equivalencias interior/exterior y alcance común."),
    (11, "vrf_network", "VRF TMV6+ y red", "CAN, respaldo, mantenimiento y control central."),
    (12, "component_checks", "Comprobación de componentes", "Sondas, ventiladores, IPM, refrigerante y comunicación."),
    (13, "technical_values", "Valores técnicos", "Tensiones, presiones, tiempos y límites documentados."),
    (14, "normal_states", "Comportamientos normales", "Desescarche, limitaciones de frecuencia y retardos."),
    (15, "service_tools_boards", "Herramientas y placas", "Software de commissioning, PCB y sustitución."),
    (16, "system_architecture", "Reconocer el sistema", "Pistas visibles para elegir la tabla correcta."),
]
core.CATEGORY_BY_SLUG = {
    slug: {"id": ident, "slug": slug, "name": name, "description": description}
    for ident, slug, name, description in core.CATEGORIES
}
core.ERROR_SPECS.clear()
core.TOPICS.clear()


def err(code: str, title: str, profile: str, ref: str, page: str, *,
        family: str, scope: str = "system", behavior: str | None = None,
        technical: str = "", aliases: list[str] | None = None) -> None:
    core.add_error(
        code, title, profile, ref, page, family=family, scope=scope,
        behavior=behavior or "La protección detiene el funcionamiento afectado.",
        technical=technical, aliases=aliases,
    )


# Split inverter actual y comercial. Los significados repetidos se conservan.
SPLIT_ERRORS = [
    ("E0", "Fallo de comunicación entre interior y exterior", "communication", "system", "7 destellos exterior"),
    ("E1", "Sonda de temperatura ambiente interior", "sensor", "indoor", "25 destellos exterior"),
    ("E2", "Sonda de batería interior", "sensor", "indoor", "26 destellos exterior"),
    ("E3", "Sonda de batería exterior", "sensor", "outdoor", "10 destellos exterior"),
    ("E4", "Sistema frigorífico anormal o circulación de gas insuficiente", "pressure", "system", ""),
    ("E5", "Configuración o correspondencia interior–exterior incorrecta", "configuration", "system", "29 destellos exterior"),
    ("E6", "Motor ventilador interior PG/DC anormal", "fan", "indoor", "21 destellos exterior"),
    ("E7", "Sonda de temperatura ambiente exterior", "sensor", "outdoor", "9 destellos exterior"),
    ("E8", "Sonda de descarga exterior", "sensor", "outdoor", "11 destellos exterior"),
    ("E9", "Control de compresor, IPM o módulo inverter anormal", "inverter", "outdoor", "30 destellos exterior"),
    ("EA", "Circuito de medida de corriente exterior", "power", "outdoor", "13 destellos exterior"),
    ("Eb", "Comunicación entre PCB principal y placa display interior", "communication", "indoor", ""),
    ("EE", "EEPROM de la unidad exterior", "pcb", "outdoor", "19 destellos exterior"),
    ("EF", "Motor ventilador DC exterior sin realimentación", "fan", "outdoor", "16 destellos exterior"),
    ("EU", "Circuito de medida de tensión exterior", "power", "outdoor", "12 destellos exterior"),
    ("EC", "Comunicación exterior entre placa de potencia y control", "communication", "outdoor", "15 destellos exterior"),
    ("EP", "Interruptor térmico superior del compresor", "compressor", "outdoor", "8 destellos exterior"),
    ("Ey", "Sondas de salida A/B de la batería interior", "sensor", "indoor", "47 o 48 destellos exterior"),
    ("En", "Sondas de entrada A/B de la batería interior", "sensor", "indoor", "51 o 52 destellos exterior"),
]
for code, title, profile, scope, alias in SPLIT_ERRORS:
    detail = {
        "E0": "Compruebe alimentación y comunicación por separado; en la familia XA81 el LED5 exterior ayuda a distinguir placa sin comunicación.",
        "E4": "El manual manda revisar fuga, válvulas de servicio y bloqueo. Una presión baja en frío o calor orienta, pero no sustituye la prueba de estanqueidad.",
        "E9": "Tras seis paradas P0 puede quedar bloqueado como E9; requiere corregir la causa y rearmar con ON/OFF.",
    }.get(code, "")
    err(code, title, profile, "XA81", "33-34", family="Split inverter XA81/T‑Pro",
        scope=scope, technical=detail, aliases=[alias] if alias else [])

err("EE", "EEPROM de la unidad interior", "pcb", "COMM", "13",
    family="Comercial, conductos y cassette", scope="indoor",
    aliases=["27 destellos exterior"])
err("E4", "Sobrecorriente IPM", "inverter", "COMM", "13",
    family="Comercial, conductos y cassette", scope="outdoor",
    aliases=["40 destellos exterior"])
err("E4", "Funcionamiento con fase de compresor ausente", "compressor", "COMM", "13",
    family="Comercial, conductos y cassette", scope="outdoor",
    aliases=["34 destellos exterior"])
err("D3", "Protección por bandeja llena o boya de condensados", "drain", "COMM", "11-13",
    family="Cassette y conductos", scope="indoor",
    behavior="La unidad se detiene y la bomba trabaja para evacuar el agua.",
    technical="Boya abierta 8 s: entra D3. Boya cerrada 180 s: sale de la protección. La bomba se mantiene 10 min tras desaparecer el nivel.")

PROTECTIONS = [
    ("P0", "Protección hardware del módulo IPM", "inverter", "1 destello exterior"),
    ("P1", "Protección de tensión alta o baja", "power", "2 destellos exterior"),
    ("P2", "Protección de sobrecorriente", "power", "3 destellos exterior"),
    ("P3", "Protección de sobretensión", "power", "24 destellos exterior"),
    ("P4", "Temperatura de descarga demasiado alta", "pressure", "4 destellos exterior"),
    ("P5", "Batería interior demasiado fría en refrigeración", "pressure", "32 destellos exterior"),
    ("P6", "Batería exterior demasiado caliente en refrigeración", "pressure", "5 destellos exterior"),
    ("P7", "Batería interior demasiado caliente en calefacción", "pressure", "33 destellos exterior"),
    ("P8", "Temperatura exterior fuera del límite de protección", "sensor", "31 destellos exterior"),
    ("P9", "Protección software del accionamiento del compresor", "inverter", "6 destellos exterior"),
    ("PA", "Diferencia de modelo o conflicto de modo", "configuration", ""),
]
for code, title, profile, alias in PROTECTIONS:
    technical = {
        "P5": "En frío/deshumidificación se evalúa después de 6 min de compresor; temperatura de evaporador baja durante 3 min provoca la parada.",
        "P6": "La familia documentada protege cuando la batería exterior alcanza aproximadamente 62 °C en frío.",
        "P7": "La familia documentada protege cuando la batería interior alcanza aproximadamente 62 °C en calor.",
    }.get(code, "Es una protección; investigue por qué aparece antes de condenar una placa.")
    err(code, title, profile, "COMM", "13", family="Split/comercial TCL",
        scope="outdoor", behavior="El control para o limita el compresor y puede reintentar.",
        technical=technical, aliases=[alias] if alias else [])

# Códigos especiales visibles solo mediante consulta ECO.
SPECIAL = [
    ("F0", "Sensor infrarrojo de presencia o percepción del usuario", "sensor"),
    ("F1", "Módulo de medida de potencia interior", "power"),
    ("F2", "Protección asociada a la sonda de descarga", "sensor"),
    ("F3", "Protección asociada a la sonda de batería exterior", "sensor"),
    ("F4", "Protección por circulación de refrigerante anormal", "pressure"),
    ("F5", "Protección PFC", "power"),
    ("F6", "Falta o inversión de fase del compresor", "compressor"),
    ("F7", "Temperatura del módulo IPM", "inverter"),
    ("F8", "Conmutación anormal de válvula de cuatro vías", "valve"),
    ("F9", "Circuito de medida de temperatura del módulo", "inverter"),
    ("FA", "Circuito de medida de corriente de fase del compresor", "power"),
    ("Fb", "Limitación de frecuencia por sobrecarga", "normal"),
    ("FC", "Limitación por consumo de potencia", "normal"),
    ("FE", "Limitación por corriente de fase del módulo", "normal"),
    ("FF", "Limitación por temperatura del módulo", "normal"),
    ("FH", "Limitación por protección del accionamiento", "normal"),
    ("FP", "Limitación anticondensación", "normal"),
    ("FU", "Limitación antihielo", "normal"),
    ("Fj", "Limitación por temperatura de descarga", "normal"),
    ("Fn", "Limitación por corriente AC exterior", "normal"),
    ("Fy", "Protección por fuga de refrigerante", "pressure"),
    ("bf", "Sonda TVOC opcional", "sensor"),
    ("bc", "Sonda PM2.5 opcional", "sensor"),
    ("bj", "Sonda de humedad interior", "sensor"),
]
for code, title, profile in SPECIAL:
    err(code, title, profile, "XA81", "34", family="Consulta especial del mando inalámbrico",
        scope="controller", behavior="Código de consulta: puede describir limitación sin parada total.",
        technical="Se consulta con la unidad funcionando: ECO 8 veces en 8 s; dos avisos acústicos confirman la entrada.")

# Mando cableado: códigos adicionales y capa de red/configuración.
WIRED = [
    ("EH", "Sonda de retorno T5", "sensor"), ("EL", "Protección por baja temperatura", "sensor"),
    ("Ed", "EEPROM interior", "pcb"), ("FE", "Comunicación del mando cableado", "communication"),
    ("b1", "Sonda ambiente del mando", "sensor"), ("b2", "Sonda de entrada de batería", "sensor"),
    ("b3", "Sonda intermedia de batería", "sensor"), ("b4", "Sonda de salida de batería", "sensor"),
    ("b5", "Sonda de humedad", "sensor"), ("b6", "Sonda de temperatura de agua", "sensor"),
    ("b7", "EEPROM interior", "pcb"), ("b8", "Motor de oscilación", "fan"),
    ("b9", "Dirección MAC", "configuration"), ("bA", "Selector de modelo/capacidad", "configuration"),
    ("H0", "Alarma general de unidad exterior", "communication"),
    ("C0", "Comunicación CAN", "communication"), ("C1", "Varias PCB principales declaradas", "configuration"),
    ("C2", "Número anormal de módulos exteriores", "configuration"),
    ("C3", "Comunicación PCB principal–driver de compresor", "communication"),
    ("C4", "Comunicación PCB principal–driver de ventilador", "communication"),
    ("C5", "Comunicación interior–mando cableado", "communication"),
    ("d1", "Protección del ventilador interior", "fan"), ("d2", "Protección del calefactor auxiliar", "power"),
    ("d3", "Bandeja llena o boya activada", "drain"), ("d4", "Protección antihielo interior", "pressure"),
    ("d5", "Conflicto de modo", "configuration"), ("d6", "Dirección IP anormal", "configuration"),
    ("d7", "Selector de capacidad interior", "configuration"), ("d8", "Número de ingeniería duplicado", "configuration"),
]
for code, title, profile in WIRED:
    err(code, title, profile, "WIRE", "12-14", family="Mando cableado WIREDCASCTRL",
        scope="controller", technical="Confirme que el código aparece en el área de temperatura del mando y no en la placa exterior.")

# Portátiles: se mantienen separados para evitar trasladar P1 o PF a un split.
for code, title, profile in [
    ("Lt", "Protección antihielo del evaporador", "normal"),
    ("PF", "Fallo de sonda en aire acondicionado portátil", "sensor"),
    ("Ft", "Depósito de condensados lleno", "drain"),
    ("AS", "Sonda de temperatura ambiente", "sensor"),
    ("ES", "Sonda de temperatura de tubería", "sensor"),
    ("P1", "Depósito lleno: drenar la unidad", "drain"),
    ("Dh", "Estado informativo de deshumidificación", "normal"),
]:
    err(code, title, profile, "PORT", "Display Codes", family="Aire acondicionado portátil TCL",
        scope="indoor", behavior="El portátil detiene o adapta el funcionamiento según el estado.",
        technical="No aplicar este significado a split, cassette, Free Match ni VRF.")

# Destellos de la PCB exterior, buscables como códigos independientes.
OUTDOOR_BLINKS = [
    (1, "Protección IPM"), (2, "Tensión alta o baja"), (3, "Sobrecorriente"),
    (4, "Temperatura de descarga alta"), (5, "Batería exterior demasiado caliente"),
    (6, "Fallo o protección del accionamiento"), (7, "Comunicación con la unidad interior"),
    (8, "Sobretemperatura o interruptor superior del compresor"),
    (9, "Sonda ambiente exterior abierta/cortocircuitada"),
    (10, "Sonda de batería exterior abierta/cortocircuitada"),
    (11, "Sonda de descarga abierta/cortocircuitada"), (12, "Circuito de medida de tensión"),
    (13, "Circuito de medida de corriente"), (14, "Fallo del IPM"),
    (15, "Comunicación entre placa de potencia e IPM"),
    (16, "Sin realimentación del ventilador DC exterior"), (17, "Estado de desescarche"),
]
for count, title in OUTDOOR_BLINKS:
    err(f"{count} destello exterior", title, "normal" if count == 17 else (
        "communication" if count in {7, 15} else "sensor" if count in {9, 10, 11}
        else "fan" if count == 16 else "inverter" if count in {1, 6, 14}
        else "power" if count in {2, 3, 12, 13} else "pressure"
    ), "COMM", "14", family="PCB de potencia exterior TCL", scope="outdoor",
        behavior="El piloto exterior repite el grupo de destellos.",
        technical="0,5 s encendido y 0,5 s apagado por destello; tras el grupo queda apagado 3 s.")


def src(ref: str, page: str, section_name: str) -> dict[str, Any]:
    return core.source(ref, page, section_name)


def step(no: int, instruction: str, expected: str = "", phase: str = "procedure",
         warning: str = "none") -> dict[str, Any]:
    return core.step(no, instruction, expected, phase, warning)


def controller(interface: str, family: str, wires: str, polarity: str,
               voltage: str, terminals: str = "", startup: str = "",
               notes: str = "") -> dict[str, Any]:
    return {
        "interface_type": interface, "controller_family": family,
        "wire_count": wires, "polarity": polarity, "nominal_voltage": voltage,
        "terminals": terminals, "cable_colors": "No documentados en la fuente revisada",
        "cable_spec": "Aplicar la sección de instalación de la familia",
        "startup_behavior": startup, "maximum_scope": None, "notes": notes,
    }


def param(code: str, name: str, description: str, options: list[tuple[str, str, str]],
          factory: str = "", warnings: str = "") -> dict[str, Any]:
    return {
        "parameter_code": code, "name": name, "description": description,
        "factory_value": factory or None, "dependencies": None,
        "warnings": warnings or None,
        "options": [
            {"option_value": value, "option_label": label, "effect": effect,
             "is_factory": bool(factory and value == factory)}
            for value, label, effect in options
        ],
    }


def v(title: str, recognition: str, ref: str, page: str, purpose: str, summary: str,
      *, system: str = "TCL", scope: str = "system", steps: list[dict[str, Any]] | None = None,
      parameters: list[dict[str, Any]] | None = None, controller_data: dict[str, Any] | None = None,
      monitoring: list[dict[str, Any]] | None = None,
      led_patterns: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return core.variant(
        title, recognition, ref, page, purpose, summary, system=system, scope=scope,
        steps=steps, parameters=parameters, controller_data=controller_data,
        monitoring=monitoring, led_patterns=led_patterns,
    )


def led_count(count: int, meaning: str) -> dict[str, Any]:
    return {
        "code_display": str(count), "indication_type": "outdoor_led",
        "display_location": "LED de la placa de potencia exterior",
        "family_hint": "TCL comercial, cassette, conductos y Free Match",
        "relationship": meaning,
        "led_indicators": [{"label": "LED exterior", "color": "red", "state": "pulse",
                            "detail": f"{count} destello(s)"}],
        "counting_rule": f"{count} destello(s), cada uno 0,5 s encendido y 0,5 s apagado.",
        "cycle_note": "Después del grupo permanece apagado 3 s y repite.",
        "sequence": "En espera: 1 s ON/1 s OFF. En marcha: encendido fijo. No confundir estos estados con un fallo.",
    }


OUTDOOR_PATTERNS = [led_count(count, title) for count, title in OUTDOOR_BLINKS]


def cassette_pattern(code: str, title: str, states: tuple[str, str, str, str]) -> dict[str, Any]:
    return {
        "code_display": code, "indication_type": "cassette_led",
        "display_location": "Panel de cuatro pilotos de cassette",
        "family_hint": "TCL cassette/comercial",
        "relationship": title,
        "led_indicators": [
            {"label": f"LED{idx}", "color": "green", "state": state}
            for idx, state in enumerate(states, start=1)
        ],
        "counting_rule": "Círculo vacío = encendido; círculo negro = apagado; doble círculo = parpadea.",
        "cycle_note": "Lea simultáneamente los cuatro pilotos.",
        "sequence": "Confirme después el código equivalente en display o el conteo de la exterior.",
    }


CASSETTE_PATTERNS = [
    cassette_pattern("E0", "Comunicación interior–exterior", ("off", "off", "off", "blink")),
    cassette_pattern("EC", "Comunicación exterior", ("blink", "blink", "off", "off")),
    cassette_pattern("E1", "Sonda ambiente interior", ("off", "off", "blink", "off")),
    cassette_pattern("E2", "Sonda de batería interior", ("off", "off", "blink", "blink")),
    cassette_pattern("E3", "Sonda de batería exterior", ("off", "blink", "off", "off")),
    cassette_pattern("E5", "Configuración incorrecta", ("off", "blink", "blink", "off")),
    cassette_pattern("E6", "Ventilador interior", ("off", "blink", "blink", "blink")),
    cassette_pattern("E7", "Sonda ambiente exterior", ("blink", "off", "off", "off")),
    cassette_pattern("E8", "Sonda de descarga", ("blink", "off", "off", "blink")),
    cassette_pattern("E9", "IPM/accionamiento", ("blink", "off", "blink", "off")),
    cassette_pattern("EF", "Ventilador DC exterior", ("blink", "blink", "blink", "blink")),
    cassette_pattern("D3", "Bandeja llena", ("off", "on", "on", "blink")),
]


def add_topic(category: str, slug: str, title: str, summary: str,
              variants: list[dict[str, Any]]) -> None:
    core.add_topic(category, slug, title, summary, variants)


add_topic("outdoor_diagnostics", "outdoor-blink-table",
          "Tabla completa de destellos de la placa exterior",
          "Estado normal y fallos 1–17 con ciclo de lectura documentado.", [
    v("LED exterior — 1 a 17 destellos", "Placa de potencia con un único piloto; sin display alfanumérico.",
      "COMM", "14", "Traducir el conteo exterior.",
      "La tabla conserva los 17 significados y la temporización exacta.",
      system="Comercial / cassette / Free Match", scope="outdoor", led_patterns=OUTDOOR_PATTERNS),
    v("Espera, marcha y avería", "El mismo LED puede estar fijo o parpadear.",
      "COMM", "14", "No confundir funcionamiento normal con código.",
      "Espera: 1 s encendido/1 s apagado. Compresor en marcha: fijo. Avería: pulsos de 0,5 s y pausa de 3 s.",
      system="Comercial / cassette / Free Match", scope="outdoor"),
])
add_topic("outdoor_diagnostics", "cassette-four-led-table",
          "Cassette: tabla de cuatro pilotos y equivalencias",
          "Cada fila combina LED1–LED4, código interior y destellos de exterior.", [
    v("Panel LED1–LED4", "Cassette sin código alfanumérico visible, con cuatro pilotos.",
      "COMM", "13", "Interpretar encendido, apagado y parpadeo.",
      "La simbología se ha verificado visualmente: vacío encendido, negro apagado, doble círculo parpadeo.",
      system="Cassette TCL", scope="indoor", led_patterns=CASSETTE_PATTERNS),
    v("Confirmación en la exterior", "Hay acceso a la placa de potencia exterior.",
      "COMM", "13-14", "Cruzar la lectura.", "Ejemplos: E0 equivale a 7 destellos; E6 a 21; E9 a 30; EF a 16.",
      system="Cassette TCL", scope="outdoor"),
])
add_topic("errors", "same-code-different-display",
          "El código cambia según dónde se lea",
          "La ficha muestra todas las interpretaciones cerradas para que el técnico elija.", [
    v("Display interior frente a piloto exterior", "Hay código E/P en el interior y conteo en la exterior.",
      "COMM", "13-14", "Relacionar ambas capas.",
      "E8 en el display es sonda de descarga y corresponde a 11 destellos exteriores. No busque necesariamente E8 en la placa.",
      system="TCL comercial", scope="system"),
    v("Mando cableado frente a placa", "ERR aparece en el mando WIREDCASCTRL.",
      "WIRE", "12-14", "Evitar aplicar una tabla exterior.", "C0–C5 y d1–d8 pertenecen a la capa de mando/sistema; confirme el lugar de lectura.",
      system="Mando cableado", scope="controller"),
    v("Portátil frente a split", "Equipo monobloque con depósito interno.",
      "PORT", "Display Codes", "Separar P1, PF y Ft.", "P1 en portátil indica depósito lleno; en split/comercial P1 es protección de tensión.",
      system="Portátil TCL", scope="indoor"),
])
add_topic("diagnostic_access", "eco-special-code-query",
          "Mando inalámbrico: obtener códigos especiales",
          "Fb–Fn, bj y otros estados no aparecen en la consulta normal.", [
    v("ECO ocho veces en ocho segundos", "Split inverter funcionando y mando con tecla ECO.",
      "XA81", "34", "Entrar en la consulta especial.",
      "Dos avisos acústicos confirman el acceso; después se muestran códigos como Fb–Fn y bj.",
      system="Split XA81/T‑Pro", scope="controller", steps=[
          step(1, "Mantenga la unidad funcionando.", phase="prepare"),
          step(2, "Pulse ECO ocho veces dentro de ocho segundos."),
          step(3, "Espere dos avisos acústicos y lea el código especial.", phase="verify"),
      ]),
    v("No confundir con reinicio automático", "El mando también admite otra secuencia repetida.",
      "XA81", "12, 34", "Evitar cambiar una función.",
      "La consulta usa ECO 8 veces. El auto‑restart de ciertas familias usa otra tecla/secuencia de 10 pulsaciones.",
      system="Split inverter", scope="controller"),
])
add_topic("diagnostic_access", "wired-controller-query",
          "Mando cableado: error actual, histórico y parámetros",
          "El área de temperatura sirve para código y para valores de consulta.", [
    v("Error actual", "Icono ERR activo en el mando cableado.",
      "WIRE", "12-14", "Leer la alarma sin cortar tensión.",
      "El código parpadea en el área de temperatura. Anote unidad, modo y código antes de salir.",
      system="WIREDCASCTRL", scope="controller"),
    v("Mode + Up durante 5 s", "Mando con teclas Mode, Up y Down.",
      "WIRE", "10-12", "Entrar en consulta de parámetros e historial.",
      "Seleccione 01–07 para valores actuales o E1–E5 para los cinco errores históricos.",
      system="WIREDCASCTRL", scope="controller", steps=[
          step(1, "Mantenga Mode + Up durante cinco segundos.", phase="prepare"),
          step(2, "Use Up/Down para elegir 01–07 o E1–E5."),
          step(3, "Anote el valor antes de modificar cualquier parámetro.", phase="verify"),
      ], monitoring=[
          {"device_id": "IDU", "sensor_id": "01", "item": "Temperatura ambiente", "unit_label": "°C", "remarks": "Lectura actual"},
          {"device_id": "IDU", "sensor_id": "02", "item": "Apertura EEV", "unit_label": "0–500", "remarks": "Pasos/posición lógica"},
          {"device_id": "IDU", "sensor_id": "03", "item": "Temperatura entrada evaporador", "unit_label": "°C", "remarks": ""},
          {"device_id": "IDU", "sensor_id": "04", "item": "Temperatura media evaporador", "unit_label": "°C", "remarks": ""},
          {"device_id": "IDU", "sensor_id": "05", "item": "Temperatura salida evaporador", "unit_label": "°C", "remarks": ""},
          {"device_id": "IDU", "sensor_id": "06", "item": "Número de ingeniería", "unit_label": "", "remarks": ""},
          {"device_id": "IDU", "sensor_id": "07", "item": "Dirección IP interior", "unit_label": "", "remarks": ""},
      ]),
])
add_topic("history_reset", "wired-history-five",
          "Historial del mando: cinco eventos",
          "E1 es el evento histórico más cercano y E5 el más antiguo de los cinco mostrados.", [
    v("Consultar E1–E5", "Mando en modo de consulta Mode + Up.",
      "WIRE", "10-12", "Reconstruir una avería intermitente.",
      "Recorra las cinco posiciones y anote repeticiones antes de rearmar.",
      system="WIREDCASCTRL", scope="controller"),
    v("Antes de borrar o cortar", "El error actual ya ha desaparecido.",
      "WIRE", "10-14", "Conservar evidencia.",
      "Registre código, unidad, estado, temperaturas y orden de los históricos. La pérdida de alimentación puede ocultar contexto.",
      system="WIREDCASCTRL", scope="controller"),
])
add_topic("service_modes", "emergency-operation",
          "Funcionamiento de emergencia desde la unidad interior",
          "Métodos antiguos y actuales cambian en el número de pulsaciones.", [
    v("Pulsador Emergency — frío, calor y parada", "Botón físico en el frontal interior.",
      "COMM", "12", "Probar sin mando.",
      "Un aviso corto selecciona frío; dos avisos cortos calor; un aviso largo apaga. No usar como operación normal.",
      system="Comercial TCL", scope="indoor"),
    v("T‑Pro: pulsaciones consecutivas", "Split actual con botón de emergencia.",
      "TPRO", "funciones de control", "Forzar una prueba básica.",
      "Primera pulsación frío; segunda dentro de 3 s calor; tercera apagado. Las protecciones permanecen activas.",
      system="T‑Pro", scope="indoor"),
])
add_topic("service_modes", "forced-defrost-generator",
          "Desescarche forzado y modo generador",
          "Funciones de servicio que no deben confundirse con fallos.", [
    v("Desescarche forzado desde mando cableado", "Calefacción activa a 16 °C.",
      "WIRE", "8-10", "Comprobar la secuencia de desescarche.",
      "Dentro de 5 s pulse Up, Down, Up, Down, Up, Down; un aviso largo confirma la orden.",
      system="WIREDCASCTRL", scope="controller"),
    v("C8 — desescarche forzado", "Display T‑Pro muestra un código de función, no una alarma.",
      "TPRO", "funciones especiales", "Reconocer el modo.", "C8 indica la orden de desescarche forzado.",
      system="T‑Pro", scope="indoor"),
    v("0A / 3A / 0F — generador", "Equipo T‑Pro con función Generator.",
      "TPRO", "funciones especiales", "Limitar consumo o desactivar la función.",
      "0A activa el modo; 3A muestra el nivel/límite de corriente; 0F lo desactiva.",
      system="T‑Pro", scope="indoor"),
])
add_topic("configuration", "wired-parameters",
          "Programación completa del mando cableado",
          "Mode + Down durante 5 s abre la configuración; registre el valor original.", [
    v("P1–P9, PF y PH", "Mando WIREDCASCTRL con teclas Mode/Up/Down.",
      "WIRE", "8-12", "Configurar mando, sensor y desescarche.",
      "P1/P2 gestionan principal/secundario; P3 dirección; P5 memoria; P6 unidades; P7 sensor; P8/P9 correcciones; PF anti‑estratificación; PH desescarche.",
      system="WIREDCASCTRL", scope="controller", steps=[
          step(1, "Mantenga Mode + Down durante cinco segundos.", phase="prepare"),
          step(2, "Seleccione el parámetro con Up/Down y anote su valor original."),
          step(3, "Cambie solo el valor respaldado por el manual y confirme."),
      ], parameters=[
          param("P1", "Principal/secundario", "Rol del mando", [("0", "Principal", "Control principal"), ("1", "Secundario", "Control subordinado")]),
          param("P3", "Dirección del mando", "Dirección en sistema de dos hilos/RS485", [("00–15", "Dirección", "Evita duplicados")]),
          param("P5", "Memoria tras corte", "Recuperación de estado", [("0", "Sin memoria", "No recupera"), ("1", "Con memoria", "Recupera estado")]),
          param("P6", "Unidades", "Escala de temperatura", [("0", "Celsius", "°C"), ("1", "Fahrenheit", "°F")]),
          param("P7", "Sonda de control", "Selección de sensor", [("0", "Unidad interior", "Usa sonda IDU"), ("1", "Mando", "Usa sonda del controlador")]),
          param("P8/P9", "Corrección de temperatura", "Offset", [("-15…15", "Corrección", "Ajuste en grados")], "0"),
          param("PF", "Prevención de estratificación", "Tiempo", [("00–60", "Minutos", "Ciclo antiagregación")], "00"),
          param("PH", "Duración máxima de desescarche", "Límite", [("00–20", "Minutos", "Duración máxima")], "15"),
      ]),
])
add_topic("controllers_buses", "wired-controller-startup",
          "Mando cableado: cableado, arranque y comunicación",
          "La fuente confirma dos hilos/RS485, pero no documenta colores ni tensión nominal.", [
    v("Autocomprobación al alimentar", "LCD del WIREDCASCTRL recién energizada.",
      "WIRE", "4-6", "Distinguir arranque normal de fallo.",
      "Todos los símbolos se encienden durante 3 s. Mantener ON/OFF 5 s ejecuta self‑check; un aviso y barrido izquierda‑derecha preceden al apagado.",
      system="WIREDCASCTRL", scope="controller",
      controller_data=controller("Cableado", "WIREDCASCTRL", "2 hilos / enlace RS485",
                                 "Consultar bornero de la unidad", "No documentada",
                                 "Bus de mando/RS485", "Todos los iconos 3 s al alimentar",
                                 "No inventar colores ni tensión: no constan en la fuente revisada.")),
    v("C5 / FE — comunicación de mando", "Mando encendido con ERR o sin controlar la interior.",
      "WIRE", "12-14", "Separar bus, dirección y alimentación.",
      "Revise continuidad, dirección P3, principal/secundario y alimentación de la unidad antes de sustituir el mando.",
      system="WIREDCASCTRL", scope="controller"),
])
add_topic("controllers_buses", "tmv6-can-bus",
          "TMV6+: bus CAN no polarizado",
          "La red VRF no debe confundirse con el mando RS485.", [
    v("CAN interior–exterior", "Sistema TMV6+ con múltiples interiores.",
      "TMV6", "14, 24", "Cablear y diagnosticar la red.",
      "CAN no polarizado, hasta unos 2.000 m y 100 kbps. El cable de comunicación debe separarse de potencia.",
      system="TMV6+ VRF", scope="system",
      controller_data=controller("Red VRF", "TMV6+ CAN", "2 conductores apantallados recomendados",
                                 "No polarizado", "Señal CAN; no aplicar tensión de red",
                                 "CAN bus", "Adquisición/auto-addressing",
                                 "Separación mínima recomendada respecto a potencia: más de 20 cm.")),
    v("C0–C4 en la capa VRF", "Mando/monitor muestra código C.",
      "WIRE", "12-14", "Localizar la comunicación afectada.",
      "C0 es CAN; C1/C2 configuración de exteriores; C3 driver de compresor; C4 driver de ventilador.",
      system="TMV6+ / controlador", scope="controller"),
])
add_topic("drainage_overflow", "cassette-drain-sequence",
          "Cassette y conductos: secuencia completa de bomba y boya",
          "Los tiempos explican por qué la bomba continúa después de parar.", [
    v("Frío y deshumidificación", "Cassette o conductos con bomba y boya.",
      "COMM", "12", "Interpretar D3 y la post‑marcha.",
      "La bomba trabaja en frío/dry y continúa 10 min tras parar el compresor o cambiar de modo.",
      system="Cassette/conductos", scope="indoor"),
    v("Boya abierta durante 8 s", "Nivel alto real o flotador bloqueado.",
      "COMM", "12", "Confirmar entrada a protección.",
      "La bomba arranca, la unidad se detiene y muestra D3. La protección entra tras 8 s continuos de contacto abierto.",
      system="Cassette/conductos", scope="indoor"),
    v("Boya cerrada durante 180 s", "El nivel ha bajado.",
      "COMM", "12", "Confirmar recuperación.",
      "Tras 180 s continuos en estado normal sale de protección; la bomba se detiene 10 min después.",
      system="Cassette/conductos", scope="indoor"),
])
add_topic("commissioning", "basic-startup",
          "Puesta en marcha de split, cassette y Free Match",
          "Antes de buscar una avería, valide alimentación, válvulas y correspondencia.", [
    v("Comprobaciones previas", "Instalación nueva o reparada.",
      "COMM", "11-14", "Evitar falsos E0, E4, E5 y P1.",
      "Confirme válvulas abiertas, tensión, interconexión, drenaje y correspondencia interior–exterior.",
      system="Split/comercial", scope="system"),
    v("La exterior conserva el fallo recuperado", "La causa ya se normalizó.",
      "COMM", "12", "No interpretar un código residual como fallo activo.",
      "Los fallos relacionados con la exterior pueden permanecer mostrados hasta 2 min después de recuperarse; las sondas recuperan automáticamente.",
      system="Comercial/Free Match", scope="outdoor"),
])
add_topic("commissioning", "vrf-one-touch-autoaddress",
          "TMV6+: commissioning y auto-addressing",
          "La prueba puede iniciarse desde exterior o software sin arrancar cada interior.", [
    v("One‑touch commissioning", "Exterior TMV6+ o software de monitorización.",
      "TMV6", "24", "Ejecutar prueba en frío/calor.",
      "Permite realizar la prueba desde la exterior o en remoto y comprobar la instalación completa.",
      system="TMV6+ VRF", scope="outdoor"),
    v("Auto-addressing", "Red CAN terminada y todas las unidades alimentadas.",
      "TMV6", "24", "Asignar direcciones interiores.",
      "La dirección se asigna automáticamente; no es necesario ajustar cada interior con DIP.",
      system="TMV6+ VRF", scope="system"),
])
add_topic("multisplit", "free-match-code-layers",
          "Free Match: código interior, cassette y piloto exterior",
          "Un mismo fallo puede leerse en tres formatos.", [
    v("Interior de pared, conductos o cassette", "Hasta cuatro interiores conectadas a una exterior Free Match.",
      "FREE", "12-14", "Elegir la pantalla accesible.",
      "Use código E/P en display, patrón LED1–LED4 en cassette o conteo exterior; las tres capas se cruzan en la tabla.",
      system="Free Match R32", scope="system"),
    v("Fallo común de exterior", "Varias interiores pierden capacidad simultáneamente.",
      "FREE", "12-14", "Reconocer causa compartida.",
      "IPM, alimentación, comunicación exterior y ventilador exterior afectan al generador común; una interior puede conservar display aunque no haya frío/calor.",
      system="Free Match R32", scope="system"),
])
add_topic("multisplit", "multi-branch-method",
          "Cómo localizar la rama afectada",
          "La base no obliga a escribir el modelo; use el puerto y el tipo de interior.", [
    v("Confirmar qué interior muestra el error", "Varias interiores comparten exterior.",
      "FREE", "12-14", "Separar fallo local y común.",
      "Anote cuál muestra E1/E2/E6/D3 y cuáles continúan; esas averías suelen pertenecer a la interior indicada.",
      system="Free Match R32", scope="indoor"),
    v("Confirmar el piloto exterior", "E0, E3, E7–E9, EF o P en interior.",
      "FREE", "12-14", "Cruzar la causa común.",
      "Cuente al menos tres ciclos completos del LED exterior y compare con la equivalencia del display.",
      system="Free Match R32", scope="outdoor"),
])
add_topic("vrf_network", "tmv6-capacity-backup",
          "TMV6+: alcance, respaldo y funcionamiento degradado",
          "Una avería no siempre obliga a parar todo el sistema.", [
    v("Un sistema, hasta 80 interiores", "Exterior modular TMV6+.",
      "TMV6", "23-24", "Entender el alcance.", "La red CAN admite hasta 80 interiores por sistema; la supervisión puede ver 4 exteriores y 80 interiores en paralelo.",
      system="TMV6+ VRF", scope="system"),
    v("Respaldo de compresor", "Módulo con dos compresores.",
      "TMV6", "19", "Mantener servicio degradado.", "Si un compresor falla, el otro puede continuar con capacidad reducida.",
      system="TMV6+ VRF", scope="outdoor"),
    v("Respaldo de módulo exterior", "Sistema con varias exteriores.",
      "TMV6", "19", "Evitar parada total cuando la lógica lo permite.",
      "Si una exterior falla, otros módulos pueden respaldar el sistema; confirme que el estado concreto admite emergencia.",
      system="TMV6+ VRF", scope="system"),
    v("Respaldo de ventilador", "Exterior con dos ventiladores.",
      "TMV6", "19", "Mantener servicio temporal.", "El ventilador restante puede continuar en emergencia si uno falla.",
      system="TMV6+ VRF", scope="outdoor"),
])
add_topic("vrf_network", "tmv6-maintenance-refrigerant",
          "TMV6+: mantenimiento sin parar todo y gestión de refrigerante",
          "La documentación distingue funciones disponibles de procedimientos que requieren manual específico.", [
    v("Apagado individual de interior", "Una interior necesita mantenimiento.",
      "TMV6", "24", "Mantener el resto en servicio.",
      "La interior puede aislarse eléctricamente para mantenimiento mientras otras continúan normalmente.",
      system="TMV6+ VRF", scope="indoor"),
    v("Juicio automático de refrigerante", "Sistema en commissioning/monitorización.",
      "TMV6", "23", "Detectar pérdida significativa.", "El sistema puede avisar cuando una fuga afecta al funcionamiento.",
      system="TMV6+ VRF", scope="system"),
    v("Modo de recogida de refrigerante", "PCB exterior con función de reciclaje.",
      "TMV6", "23", "Almacenar refrigerante en la exterior.",
      "El catálogo confirma activación mediante botones de PCB, pero no publica la secuencia; no se inventan pulsaciones.",
      system="TMV6+ VRF", scope="outdoor"),
])
add_topic("component_checks", "communication-e0",
          "Diagnóstico de comunicación E0",
          "Separe alimentación, cable y placa antes de sustituir componentes.", [
    v("Comprobar 220 V entre L y N", "Split XA81 con E0.",
      "XA81", "35-40", "Confirmar alimentación exterior.",
      "Mida alimentación antes de tocar la comunicación. Revise el terminal de señal, continuidad y conexiones.",
      system="Split XA81", scope="system"),
    v("LED5 exterior", "PCB exterior accesible con indicador LED5.",
      "XA81", "35-40", "Distinguir ausencia de trama.",
      "Si la línea de comunicación está anormal, LED5 puede permanecer fijo. Use el diagrama de esa placa y no aplique tensiones de otro bus.",
      system="Split XA81", scope="outdoor"),
])
add_topic("component_checks", "fan-motors",
          "Ventiladores PG, DC y BLDC",
          "La tensión cambia según motor; desconectarlo con tensión puede dañar la placa.", [
    v("Motor interior de cinco hilos con control integrado", "Conector de potencia/realimentación de cinco vías.",
      "XA81", "diagnóstico E6", "Comprobar alimentación y señal.",
      "Valores de referencia documentados: Vm alrededor de 310 V DC y Vcc alrededor de 15 V DC. Aplique solo a esta arquitectura.",
      system="Split inverter", scope="indoor"),
    v("Motor exterior trifásico U‑V‑W", "Motor DC/BLDC con tres fases.",
      "XA81", "diagnóstico EF", "Separar motor y driver.",
      "La salida puede variar aproximadamente entre 20 y 200 V DC según carga. No medir como una red AC convencional.",
      system="Split inverter", scope="outdoor"),
])
add_topic("component_checks", "refrigerant-e4-protections",
          "Circuito frigorífico E4, P5, P6 y P7",
          "Las protecciones describen una condición; no garantizan una causa única.", [
    v("E4 — caudal de refrigerante anormal", "Split inverter sin capacidad.",
      "XA81", "41-45", "Buscar fuga, válvula o bloqueo.",
      "Compruebe válvulas de servicio, fugas, restricción, ventiladores e intercambiadores antes de recargar.",
      system="Split XA81", scope="system"),
    v("P5/P6/P7 — temperaturas de batería", "La unidad para y luego puede recuperar.",
      "XA81", "protecciones", "Distinguir hielo y sobretemperatura.",
      "P5 protege evaporador frío; P6 batería exterior caliente en frío; P7 batería interior caliente en calor.",
      system="Split inverter", scope="system"),
])
add_topic("technical_values", "quick-values",
          "Valores rápidos de diagnóstico",
          "Cada valor conserva familia y punto de medida.", [
    v("Comunicación y red", "E0 o C0/C5.",
      "XA81", "35-40", "Elegir la medida correcta.",
      "Split: confirme 220 V L‑N y la línea de comunicación. TMV6+: CAN no polar, 100 kbps, unos 2.000 m y más de 20 cm respecto a potencia.",
      system="TCL varias familias"),
    v("Boya de condensados", "D3 en cassette/conductos.",
      "COMM", "12", "Validar tiempos.", "Entrada tras 8 s abierta; salida tras 180 s cerrada; post‑marcha de bomba 10 min.",
      system="Cassette/conductos", scope="indoor"),
    v("Ventiladores inverter", "E6 o EF.",
      "XA81", "diagnóstico E6/EF", "Comparar alimentación.",
      "Cinco hilos: Vm≈310 V DC, Vcc≈15 V DC. Exterior U‑V‑W: salida variable aprox. 20–200 V DC.",
      system="Split inverter"),
])
add_topic("normal_states", "frequency-limitations",
          "Fb–Fn: limitaciones, no siempre averías",
          "Explican por qué el compresor reduce frecuencia.", [
    v("Carga, potencia y corriente", "Consulta ECO muestra Fb, FC, FE o Fn.",
      "XA81", "34", "Interpretar pérdida de capacidad.",
      "El control reduce frecuencia por sobrecarga, consumo, corriente de fase o corriente AC exterior.",
      system="Split inverter", scope="outdoor"),
    v("Temperatura y protecciones", "Consulta ECO muestra FF, FH, FP, FU o Fj.",
      "XA81", "34", "Reconocer limitación preventiva.",
      "Puede limitar por módulo, accionamiento, anticondensación, antihielo o descarga antes de un código de parada.",
      system="Split inverter", scope="outdoor"),
])
add_topic("normal_states", "defrost-delays",
          "Desescarche, retardos y post‑marchas normales",
          "Evitan diagnósticos falsos durante una secuencia normal.", [
    v("17 destellos — desescarche", "LED exterior repite 17 pulsos.",
      "COMM", "14", "No sustituir una placa por un estado.", "La tabla exterior define 17 destellos como estado de desescarche.",
      system="Comercial/Free Match", scope="outdoor"),
    v("Reinicio del compresor", "El compresor acaba de parar.",
      "XA81", "control exterior", "Esperar el retardo.", "La comunicación recuperada no permite arranque inmediato: el compresor respeta aproximadamente 3 min de protección.",
      system="Split inverter", scope="outdoor"),
    v("Válvula de cuatro vías", "Se abandona calefacción.",
      "XA81", "control exterior", "Interpretar el retraso de conmutación.", "La bobina puede mantenerse unos 2 min después de salir de calor.",
      system="Split inverter", scope="outdoor"),
])
add_topic("service_tools_boards", "tmv6-commissioning-software",
          "Software de commissioning TMV6+",
          "Monitoriza, registra y fuerza carga para verificar la instalación.", [
    v("Monitorización paralela", "Ordenador/herramienta de servicio conectada a TMV6+.",
      "TMV6", "24", "Ver curvas y datos reales.",
      "Puede monitorizar 4 exteriores y 80 interiores, representar curvas y guardar datos originales.",
      system="TMV6+ VRF"),
    v("Control forzado de carga", "Prueba de mantenimiento autorizada.",
      "TMV6", "24", "Verificar comportamiento bajo carga.",
      "La herramienta permite control de carga para comprobación; mantenga activas las protecciones y siga el manual de servicio.",
      system="TMV6+ VRF"),
])
add_topic("service_tools_boards", "board-replacement",
          "Después de sustituir una placa",
          "Una placa nueva puede necesitar identidad, dirección y configuración.", [
    v("Split/comercial", "E5, Eb, EE, EA o EU después del cambio.",
      "XA81", "33-45", "Restaurar configuración.", "Compruebe referencia, conectores, EEPROM, selector de modelo y correspondencia interior–exterior.",
      system="Split/comercial"),
    v("TMV6+ modular", "C1, C2, C3 o C4 después del cambio.",
      "WIRE", "12-14", "Restaurar rol y red.", "Confirme una sola principal, cantidad de módulos, direcciones y comunicación con drivers antes del commissioning.",
      system="TMV6+ VRF", scope="outdoor"),
])
add_topic("system_architecture", "recognize-tcl-family",
          "Reconocer la familia TCL antes de buscar",
          "Use lo que ve en la máquina; el modelo exacto queda como trazabilidad interna.", [
    v("Split inverter", "Una interior mural, mando IR y display E/P/F.",
      "XA81", "33-34", "Usar tabla split y consulta ECO.", "No aplique C0–C5 ni tabla de cuatro pilotos.",
      system="Split inverter"),
    v("Cassette o conductos", "Panel con cuatro LED, bomba de drenaje o mando cableado.",
      "COMM", "11-14", "Usar D3, LED1–LED4 y equivalencias exteriores.", "Confirme boya, código interior y conteo exterior.",
      system="Comercial"),
    v("Free Match", "Dos a cuatro interiores comparten una exterior con un LED.",
      "FREE", "12-14", "Separar fallo local y común.", "Anote qué interior informa y cuente el piloto exterior.",
      system="Free Match R32"),
    v("TMV6+ VRF", "Exterior modular, muchas interiores y red CAN.",
      "TMV6", "14, 23-24", "Usar capa de red y commissioning.", "No extrapole los destellos 1–17 de una placa comercial.",
      system="TMV6+ VRF"),
    v("Portátil", "Monobloque con depósito o tubo de drenaje.",
      "PORT", "Display Codes", "Usar Lt/PF/Ft/AS/ES/P1/Dh.", "P1 significa depósito lleno, no tensión exterior.",
      system="Portátil TCL"),
])
add_topic("system_architecture", "information-organization",
          "Cómo consultar TCL sin perder información",
          "Marca → categoría → tema → variante; todo permanece plegado hasta elegir.", [
    v("Lista de códigos", "Acceso Errores y protecciones.",
      "VRFWEB", "producto", "Buscar por código o significado.", "Cuando un código tiene varios usos, ninguno se abre automáticamente.",
      system="Super Técnico"),
    v("Pilotos exteriores", "Acceso Pilotos y display exterior.",
      "COMM", "13-14", "Llegar directamente a la tabla visual.", "La tabla 1–17 y los cuatro pilotos cassette están separadas del buscador alfanumérico.",
      system="Super Técnico"),
    v("Fuentes y límites", "Bloque Fuentes de cada ficha.",
      "VRFWEB", "producto", "Comprobar trazabilidad.", "La base está completa respecto al corpus TCL Referencia V1; no pretende cubrir todas las generaciones.",
      system="Super Técnico"),
])


def write_json(path: Path, value: Any) -> None:
    core.write_json(path, value)


def build() -> dict[str, int]:
    if BRAND_DIR.exists():
        shutil.rmtree(BRAND_DIR)
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
            "id": topic["id"], "slug": topic["slug"], "title": topic["title"],
            "summary": topic["summary"], "active": 1,
            "variant_count": len(topic["variants"]),
        })
    categories = [{
        "id": ident, "slug": slug, "name": name, "description": description,
        "sort_order": ident * 10, "active": 1, "topics": by_category[ident],
    } for ident, slug, name, description in core.CATEGORIES]
    write_json(WEB_DIR / "navigation.json", {
        "metadata": {
            "schema_name": "Super Tecnico",
            "navigation_model": "brand_category_topic_variant",
            "schema_version": "2.3.0", "data_version": "1.0.0",
            "last_update_utc": now, "reference_brand": "TCL",
            "verification_warning": (
                "Completa respecto al corpus TCL Referencia V1. Confirme siempre "
                "familia y punto de lectura: display interior, mando, cuatro pilotos "
                "cassette, conteo exterior, Free Match, portátil o CAN TMV6+."
            ),
        },
        "categories": categories,
    })
    write_json(WEB_DIR / "sources.json", [{
        "id": ident, "brand_id": BRAND_ID, "title": row["title"],
        "document_ref": row["document_ref"], "document_type": row["type"],
        "publication_date": row["year"], "language": "es/en",
        "source_url": row["source_url"], "status": "reviewed",
        "notes": "Fuente revisada para TCL Referencia V1.",
    } for ident, row in enumerate(core.SOURCES.values(), start=1)])
    write_json(WEB_DIR / "coverage.json", [{
        "id": ident, "brand_id": BRAND_ID, "area_slug": slug, "area_name": name,
        "equipment_scope": "TCL — split, comercial, cassette, conductos, Free Match, portátil y TMV6+ VRF",
        "coverage_status": "reference_v1", "source_count": len(core.SOURCES),
        "notes": description, "last_reviewed": "2026-07-29",
    } for ident, slug, name, description in core.CATEGORIES])
    counts = {
        "categories": len(core.CATEGORIES), "topics": len(topics),
        "variants": sum(len(topic["variants"]) for topic in topics),
        "errors": len(error_index), "search_entries": len(search_entries),
    }
    write_json(BRAND_DIR / "brand.json", {
        "slug": "tcl", "name": "TCL", "display_name": "TCL",
        "enabled": True, "web_data": "web", "media": "media",
        "publish_media": False, "static_site": True,
        "schema_version": "2.3.0", "data_version": "1.0.0",
        "exported_at_utc": now, "counts": counts,
        "notes": (
            "TCL Referencia V1: split inverter actual y anterior, comercial, "
            "cassette, conductos, Free Match, mando cableado, portátil y TMV6+ VRF; "
            "incluye tabla exterior 1–17, cuatro pilotos cassette, procedimientos, "
            "valores, drenaje, programación y alcance operativo."
        ),
    })
    return counts


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
