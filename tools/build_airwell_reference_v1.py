#!/usr/bin/env python3
"""Construye Airwell histórica Referencia V1.

La selección es deliberadamente restrictiva. Se admiten familias documentadas
en el corpus industrial propio de Airwell, con edición original de 2005 y
revisión de 2008, y la familia HRW cuyo manual identifica expresamente a
AIRWELL Industrie France. No se publican manuales, capturas ni bases maestras.
"""

from __future__ import annotations

import json
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import build_hisense_reference_v1 as core
from audit_brand_quality import audit_brand, write as write_quality


ROOT = Path(__file__).resolve().parents[1]
BRAND_DIR = ROOT / "data" / "brands" / "airwell-historica"
WEB_DIR = BRAND_DIR / "web"
BRAND_ID = 16

core.BRAND_DIR = BRAND_DIR
core.WEB_DIR = WEB_DIR
core.BRAND_ID = BRAND_ID

core.SOURCES = {
    "BS": {
        "title": "Airwell BS DCI Series — Service Manual",
        "document_ref": "SM BS DCI 1-A.1 GB",
        "source_url": "https://lh.airwell-res.com/sites/default/files/imported/Airwell/c56/p121/SM_BS_DCI_1_A_1_GB.pdf",
        "type": "service_manual",
        "year": "edición original mayo de 2005; revisión octubre de 2008",
    },
    "DLS": {
        "title": "Airwell DLS Series — Service Manual",
        "document_ref": "SM DLSRPM 1-A.4 GB",
        "source_url": "https://lh.airwell-res.com/sites/default/files/imported/Airwell/c55/p118/SM_DLSRPM_1%20A%204%20GB.pdf",
        "type": "service_manual",
        "year": "edición original 24-02-2005; revisión diciembre de 2008",
    },
    "DUO": {
        "title": "Airwell Multi Split DUO 50 DCI — Service Manual",
        "document_ref": "SM DUODCI 1-A.1 GB",
        "source_url": "https://lh.airwell-res.com/sites/default/files/imported/Airwell/c61/p146/SM_DUODCI_1_A_1_GB.pdf",
        "type": "service_manual",
        "year": "edición original enero de 2005; revisión septiembre de 2008",
    },
    "TQ": {
        "title": "Airwell Multi Split Trio Quattro DCI — Service Manual",
        "document_ref": "SM TQDCI 1-A.1 GB",
        "source_url": "https://lh.airwell-res.com/sites/default/files/imported/Airwell/c61/p150/SM_TQDCI_1%20A%201%20GB.pdf",
        "type": "service_manual",
        "year": "edición original junio de 2005; revisión octubre de 2008",
    },
    "HRW": {
        "title": "Airwell HRW 07-12 — Manuel d'installation et de maintenance",
        "document_ref": "IOM HRW 02-N-7F / 3990404",
        "source_url": "https://www.manualslib.fr/manual/27590/Airwell-Hrw-07.html",
        "type": "installation_maintenance_manual",
        "year": "etapa Airwell Industrie France",
    },
    "HISTORY17": {
        "title": "Airwell — Catalogue Climatisation 2017",
        "document_ref": "AIRWELL-CATALOGUE-2017-GB",
        "source_url": "https://lh.airwell-res.com/sites/default/files/product_uploads/Catalogue%20Airwell%20Climatisation%202017-GB.pdf",
        "type": "official_corporate_catalogue",
        "year": "2017",
    },
    "HISTORY25": {
        "title": "Airwell — Dépliant gamme et repères historiques",
        "document_ref": "AIRWELL-DEPLIANT-GAMME-FR-0425-V11",
        "source_url": "https://lh.airwell-res.com/sites/default/files/product_uploads/DEPLIANT%20GAMME%20FR_0425_V11.pdf",
        "type": "official_corporate_history",
        "year": "2025",
    },
}

core.CATEGORIES = [
    (1, "errors", "Errores, protecciones y estados", "Todas las interpretaciones, separadas por familia y lugar de lectura."),
    (2, "outdoor_diagnostics", "Pilotos y display exterior", "Tablas de cinco bits, MSMP y display exterior de tres dígitos."),
    (3, "diagnostic_access", "Obtención de códigos", "Acceso con MODE/RESET, mando, display y placa."),
    (4, "history_reset", "Memoria, salida y rearme", "Qué se conserva, qué borra la consulta y cómo recuperar."),
    (5, "service_modes", "Test y modos de servicio", "Test fijo, Technician Test y autocomprobación de placa."),
    (6, "configuration", "DIP, jumpers y programación", "Model plug, modos del mando, Group ID y configuración del sistema."),
    (7, "controllers_buses", "Mandos, placas y buses", "Control remoto, HMI, MSMP, MegaTool y comunicación."),
    (8, "drainage_overflow", "Drenaje y desbordamiento", "Boya, bomba, bandeja y lógica distinta con la unidad ON/OFF."),
    (9, "commissioning", "Puesta en marcha", "Comprobaciones, configuración de puertos y pruebas de instalación."),
    (10, "multisplit", "DUO, TRIO y QUATTRO", "Puertos A-D, capacidad, continuidad y efecto por rama."),
    (11, "operational_effects", "Efecto sobre el funcionamiento", "Parada de compresor, aviso, protección temporal o estado normal."),
    (12, "component_checks", "Comprobación de componentes", "Sondas, ventiladores, compresor, EEV, RV, fuentes y comunicación."),
    (13, "technical_values", "Valores técnicos", "Tensiones, resistencias, tiempos y umbrales documentados."),
    (14, "normal_states", "Estados normales", "Desescarche, modelo, EEPROM y estados sin avería."),
    (15, "service_tools_boards", "Herramientas y placas", "MegaTool, HMI, MSMP y autoprueba DLS."),
    (16, "system_architecture", "Reconocer la familia", "Pistas observables para elegir la tabla sin exigir el modelo."),
    (17, "provenance", "Procedencia y autenticidad", "Qué se admite como fabricación Airwell y qué se excluye."),
]
core.CATEGORY_BY_SLUG = {
    slug: {"id": ident, "slug": slug, "name": name, "description": description}
    for ident, slug, name, description in core.CATEGORIES
}
core.ERROR_SPECS.clear()
core.TOPICS.clear()


def default_behavior(title: str, profile: str, family: str) -> str:
    lowered = title.lower()
    if profile == "normal" or "no fault" in lowered or "modelo" in lowered or "model " in lowered:
        return "Es una indicación de estado o identificación; no representa por sí sola una avería."
    if "configuration changed" in lowered or "configuración modificada" in lowered:
        return "El manual la define como aviso de cambio de configuración, sin avería."
    if "deicing" in lowered or "desescarche" in lowered:
        return "Corresponde a una secuencia de desescarche/protección temporal; la tabla no exige intervención."
    if "no communication a" in lowered or "no communication b" in lowered or "no communication c" in lowered or "no communication d" in lowered:
        return "Se pierde la comunicación de la línea indicada; el manual no afirma que se detenga todo el multisplit."
    if "compressor stopped" in lowered or "compresor detenido" in lowered:
        return "La protección detiene el compresor; el resto del alcance depende de las unidades conectadas."
    return (
        f"El manual identifica la condición en {family}; no se atribuye una parada total "
        "del conjunto cuando la tabla no la especifica."
    )


def err(
    code: str,
    title: str,
    profile: str,
    ref: str,
    page: str,
    *,
    family: str,
    scope: str,
    technical: str = "",
    behavior: str = "",
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
        behavior=behavior or default_behavior(title, profile, family),
        technical=technical or (
            "Confirme la familia, el punto de lectura y el patrón completo antes de aplicar la comprobación."
        ),
        aliases=aliases or [],
    )


BS_INDOOR = [
    ("1", "RT-1 desconectada", "sensor"), ("2", "RT-1 en cortocircuito", "sensor"),
    ("3", "RT-2 desconectada", "sensor"), ("4", "RT-2 en cortocircuito", "sensor"),
    ("7", "Versiones de comunicación incompatibles", "communication"),
    ("8", "Sin comunicación interior-exterior", "communication"),
    ("9", "Sin señal de encoder del ventilador interior", "fan"),
    ("11", "Avería comunicada por la unidad exterior", "pcb"),
    ("17", "Protección de defrost", "normal"), ("18", "Protección de deicing", "normal"),
    ("19", "Protección de la unidad exterior", "pressure"),
    ("20", "Protección de alta presión en batería interior", "pressure"),
    ("24", "EEPROM no actualizada; usa parámetros ROM", "pcb"),
    ("25", "EEPROM defectuosa", "pcb"), ("26", "Comunicación de baja fiabilidad", "communication"),
    ("27", "Funcionamiento con datos EEPROM", "normal"),
    ("28", "Identificación Model A", "normal"), ("29", "Identificación Model B", "normal"),
    ("30", "Identificación Model C", "normal"), ("31", "Identificación Model D", "normal"),
]
for code, title, profile in BS_INDOOR:
    err(
        code, title, profile, "BS", "12-3 a 12-5 (PDF 38-40)",
        family="BS DCI — diagnóstico interior", scope="indoor",
        aliases=[f"BS interior {code}", f"COOL HEAT {code}"],
    )

BS_OUTDOOR = [
    ("1", "OCT desconectada", "sensor"), ("2", "OCT en cortocircuito", "sensor"),
    ("3", "CTT desconectada", "sensor"), ("4", "CTT en cortocircuito", "sensor"),
    ("5", "HST desconectada cuando está habilitada", "sensor"),
    ("6", "HST en cortocircuito", "sensor"), ("7", "OAT desconectada", "sensor"),
    ("8", "OAT en cortocircuito", "sensor"), ("9", "TSUC desconectada", "sensor"),
    ("10", "TSUC en cortocircuito", "sensor"), ("11", "Fallo IPM", "inverter"),
    ("12", "EEPROM exterior defectuosa", "pcb"), ("13", "Subtensión del bus DC", "power"),
    ("14", "Sobretensión del bus DC", "power"), ("15", "Subtensión de red AC", "power"),
    ("16", "Versiones interior-exterior incompatibles", "communication"),
    ("17", "Sin comunicación interior-exterior", "communication"),
    ("20", "Sobretemperatura del disipador", "inverter"), ("21", "Deicing", "normal"),
    ("22", "Sobretemperatura del compresor", "compressor"),
    ("23", "Sobrecorriente del compresor", "compressor"),
    ("27", "Comunicación de baja fiabilidad", "communication"),
]
for code, title, profile in BS_OUTDOOR:
    err(
        code, title, profile, "BS", "12-4 a 12-5 (PDF 39-40)",
        family="BS DCI — diagnóstico exterior", scope="outdoor",
        technical=(
            "La tabla recomienda revisar alimentación para 13-15, cableado y tierra para 16/17/27, "
            "y conexiones/control de potencia para IPM y disipador."
        ),
        aliases=[f"BS exterior {code}", f"Filter Timer {code}"],
    )

DLS_ERRORS = [
    ("1", "RT1 desconectada", "sensor"), ("2", "RT1 en cortocircuito", "sensor"),
    ("3", "Fallo de válvula de cuatro vías", "valve"),
    ("4", "RT2 desconectada", "sensor"), ("5", "RT2 en cortocircuito", "sensor"),
    ("7", "La lectura de RT2 no cambia", "sensor"), ("8", "RT3 desconectada", "sensor"),
    ("9", "RT3 en cortocircuito", "sensor"), ("11", "La lectura de RT3 no cambia", "sensor"),
    ("12", "Las lecturas de RT2 y RT3 no cambian", "sensor"),
]
for code, title, profile in DLS_ERRORS:
    err(
        code, title, profile, "DLS", "13-30 (PDF 100)",
        family="DLS/RPM — diagnóstico COOL/HEAT", scope="indoor",
        technical="Si coinciden varias sondas, el manual muestra solo una según prioridad RT3, RT2 y RT1; el caso 12 es conjunto.",
        aliases=[f"DLS {code}", f"HEAT COOL {code}"],
    )

DUO_OUTDOOR = [
    ("1", "OCT desconectada", "sensor"), ("2", "OCT en cortocircuito", "sensor"),
    ("3", "CTT desconectada", "sensor"), ("4", "CTT en cortocircuito", "sensor"),
    ("5", "HST desconectada cuando está habilitada", "sensor"),
    ("6", "HST en cortocircuito", "sensor"), ("7", "OAT desconectada", "sensor"),
    ("8", "OAT en cortocircuito", "sensor"), ("9", "TSUC desconectada", "sensor"),
    ("10", "TSUC en cortocircuito", "sensor"), ("11", "Fallo IPM", "inverter"),
    ("12", "EEPROM exterior defectuosa", "pcb"), ("13", "Subtensión del bus DC", "power"),
    ("14", "Sobretensión del bus DC", "power"), ("15", "Subtensión de red AC", "power"),
    ("16", "Versiones interior-exterior incompatibles", "communication"),
    ("17", "Sin comunicación", "communication"), ("18", "Modelo exterior no válido", "configuration"),
    ("19", "EEPROM MSMP defectuosa", "pcb"), ("20", "Sobretemperatura del disipador", "inverter"),
    ("21", "Deicing", "normal"), ("22", "Sobretemperatura del compresor", "compressor"),
    ("23", "Sobrecorriente del compresor", "compressor"),
    ("27", "Comunicación de baja fiabilidad", "communication"),
    ("29", "Sin avería en calefacción", "normal"), ("30", "Sin avería en frío, dry o fan", "normal"),
    ("31", "Sin avería en standby", "normal"),
]
for code, title, profile in DUO_OUTDOOR:
    err(
        code, title, profile, "DUO", "12-2 a 12-3 (PDF 55-56)",
        family="DUO 50 DCI — MSMP exterior", scope="outdoor",
        aliases=[f"DUO MSMP exterior {code}", f"MSMP ODU {code}"],
    )

DUO_INDOOR = [
    ("1", "RT1 desconectada", "sensor"), ("2", "RT1 en cortocircuito", "sensor"),
    ("3", "RT2 desconectada", "sensor"), ("4", "RT2 en cortocircuito", "sensor"),
    ("5", "RGT desconectada", "sensor"), ("7", "Versiones de comunicación incompatibles", "communication"),
    ("8", "Sin comunicación", "communication"), ("9", "Sin encoder del ventilador interior", "fan"),
    ("11", "Avería de unidad exterior", "pcb"), ("17", "Protección de defrost", "normal"),
    ("18", "Protección de deicing", "normal"), ("19", "Protección de unidad exterior", "pressure"),
    ("20", "Protección de alta presión en batería interior", "pressure"),
    ("21", "Protección por desbordamiento", "drain"),
    ("24", "EEPROM no actualizada; usa parámetros ROM", "pcb"),
    ("25", "EEPROM defectuosa", "pcb"), ("26", "Comunicación de baja fiabilidad", "communication"),
    ("27", "Funcionamiento con datos EEPROM", "normal"),
    ("29", "Sin avería en calefacción", "normal"), ("30", "Sin avería en frío, dry o fan", "normal"),
    ("31", "Sin avería en standby", "normal"),
]
for code, title, profile in DUO_INDOOR:
    err(
        code, title, profile, "DUO", "12-4 a 12-5 (PDF 57-58)",
        family="DUO 50 DCI — MSMP interior", scope="indoor",
        aliases=[f"DUO MSMP interior {code}", f"MSMP IDU {code}"],
    )

TQ_OUTDOOR = [
    ("1", "Sonda OCT defectuosa", "sensor"), ("2", "Sonda CTT defectuosa", "sensor"),
    ("3", "Sonda HST defectuosa", "sensor"), ("4", "Sonda OAT defectuosa", "sensor"),
    ("5", "Sonda OMT defectuosa", "sensor"), ("6", "Sonda RGT defectuosa", "sensor"),
    ("7", "Pérdida de feedback del ventilador exterior o compresor", "fan"),
    ("8", "Fallo IPM del ventilador exterior", "inverter"), ("9", "Ventilador exterior bloqueado", "fan"),
    ("10", "Velocidad excesiva del ventilador exterior", "fan"),
    ("11", "Fallo IPM del compresor", "inverter"), ("12", "Compresor bloqueado", "compressor"),
    ("13", "Velocidad excesiva del compresor", "compressor"),
    ("14", "Foldback por alta presión o corriente", "pressure"),
    ("15", "Subtensión del bus DC", "power"), ("16", "Sobretensión del bus DC", "power"),
    ("17", "Subtensión de red AC", "power"), ("18", "Sin comunicación en línea A", "communication"),
    ("19", "Sin comunicación en línea B", "communication"), ("20", "Sin comunicación en línea C", "communication"),
    ("21", "Sin comunicación en línea D", "communication"), ("22", "Velocidad ilegal del compresor", "compressor"),
    ("23", "Configuración del sistema modificada", "normal"),
    ("24", "Configuración de puertos o capacidad no válida", "configuration"),
    ("25", "Compresor detenido por sobretemperatura del disipador", "inverter"),
    ("26", "Protección de desescarche", "normal"),
    ("27", "Compresor detenido por sobretemperatura", "compressor"),
    ("28", "Compresor detenido por sobrepotencia del sistema", "power"),
    ("29", "EEPROM exterior defectuosa", "pcb"), ("30", "Control exterior sin configurar", "configuration"),
]
for code, title, profile in TQ_OUTDOOR:
    technical = "Lea el número en el display HMI exterior de tres dígitos y aplique la tabla TQ, no la tabla de cinco LED."
    if code == "16":
        technical += " La tabla pide comprobar si la entrada supera 270 V CA."
    elif code == "17":
        technical += " La tabla pide comprobar si la entrada cae por debajo de 170 V CA."
    elif code in {"18", "19", "20", "21"}:
        technical += f" El número identifica la línea/puerto {'ABCD'[int(code) - 18]}."
    err(
        code, title, profile, "TQ", "12-2 a 12-3 (PDF 84-85)",
        family="TRIO/QUATTRO DCI — display HMI exterior", scope="outdoor",
        technical=technical,
        aliases=[f"TQ exterior {code}", f"TRIO QUATTRO {code}"],
    )

TQ_INDOOR = [
    ("1", "RT-1 desconectada", "sensor"), ("2", "RT-1 en cortocircuito", "sensor"),
    ("3", "RT-2 desconectada", "sensor"), ("4", "RT-2 en cortocircuito", "sensor"),
    ("7", "Versiones de comunicación incompatibles", "communication"),
    ("8", "Sin comunicación interior-exterior", "communication"),
    ("9", "Sin encoder del ventilador interior", "fan"), ("11", "Avería de unidad exterior", "pcb"),
    ("17", "Protección de defrost", "normal"), ("18", "Protección de deicing", "normal"),
    ("19", "Protección de unidad exterior", "pressure"),
    ("20", "Protección de alta presión en batería interior", "pressure"),
    ("21", "Protección por desbordamiento", "drain"),
    ("24", "EEPROM no actualizada; usa parámetros ROM", "pcb"),
    ("25", "EEPROM defectuosa", "pcb"), ("26", "Comunicación de baja fiabilidad", "communication"),
    ("27", "Funcionamiento con datos EEPROM", "normal"),
    ("28", "Identificación de interior DCI-25", "normal"), ("29", "Identificación de interior DCI-35", "normal"),
    ("30", "Identificación de interior DCI-50", "normal"), ("31", "Identificación de interior DCI-60", "normal"),
]
for code, title, profile in TQ_INDOOR:
    err(
        code, title, profile, "TQ", "12-4 a 12-5 (PDF 86-87)",
        family="TRIO/QUATTRO DCI — diagnóstico interior COOL/HEAT", scope="indoor",
        aliases=[f"TQ interior {code}", f"COOL HEAT {code}"],
    )

HRW_COOL = [
    ("100000000", "Alta presión en modo frío", "pressure"),
    ("110000000", "Baja presión en modo frío", "pressure"),
    ("111000000", "Protección térmica del ventilador en frío", "fan"),
    ("111110000", "Temperatura de agua en límite bajo en frío", "pressure"),
    ("111111000", "Temperatura de agua en límite alto en frío", "pressure"),
    ("111111100", "Protección antihielo en frío", "pressure"),
    ("111111110", "Protección por desbordamiento de condensados en frío", "drain"),
    ("111111111", "Otras alarmas en modo frío", "pcb"),
]
HRW_HEAT = [
    ("100000000", "Alta presión en modo calor", "pressure"),
    ("110000000", "Baja presión en modo calor", "pressure"),
    ("111000000", "Protección térmica del ventilador en calor", "fan"),
    ("111100000", "Protección antihielo del intercambiador de placas", "pressure"),
    ("111110000", "Temperatura de agua en límite bajo en calor", "pressure"),
    ("111111000", "Temperatura de agua en límite alto en calor", "pressure"),
    ("111111110", "Protección por desbordamiento de condensados en calor", "drain"),
    ("111111111", "Otras alarmas en modo calor", "pcb"),
]
for rows, mode, page in ((HRW_COOL, "frío", "32 y 34"), (HRW_HEAT, "calor", "33 y 34")):
    for code, title, profile in rows:
        behavior = (
            "La alarma se anula automáticamente tras corregir la causa cuando así lo indica la fila; "
            "tres eventos en una hora provocan parada y exigen cortar cinco segundos."
        )
        err(
            code, title, profile, "HRW", page,
            family=f"HRW 07-12 — LED RCL/adaptador en modo {mode}", scope="system",
            behavior=behavior,
            technical=(
                "El patrón tiene nueve posiciones: 1 es destello verde y 0 ausencia de destello. "
                "La misma secuencia puede cambiar de causas y umbrales entre frío y calor."
            ),
            aliases=[f"HRW {mode} {code}", f"{code.count('1')} flashes HRW"],
        )


def step(no: int, instruction: str, expected: str = "", phase: str = "procedure", warning: str = "none") -> dict[str, Any]:
    return core.step(no, instruction, expected, phase, warning)


def v(
    title: str,
    recognition: str,
    ref: str,
    page: str,
    purpose: str,
    summary: str,
    *,
    system: str = "Airwell histórica",
    scope: str = "system",
    steps: list[dict[str, Any]] | None = None,
    led_patterns: list[dict[str, Any]] | None = None,
    controller_data: dict[str, Any] | None = None,
    parameters: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return core.variant(
        title, recognition, ref, page, purpose, summary,
        system=system, scope=scope, steps=steps, led_patterns=led_patterns,
        controller_data=controller_data, parameters=parameters,
    )


def add_topic(category: str, slug: str, title: str, summary: str, variants: list[dict[str, Any]]) -> None:
    core.add_topic(category, slug, title, summary, variants)


def five_bit_pattern(code: str, meaning: str, family: str, location: str) -> dict[str, Any]:
    bits = format(int(code), "05b")
    states = [f"{label}:{'ON' if bit == '1' else 'OFF'}" for label, bit in zip(("5", "4", "3", "2", "1"), bits)]
    return {
        "code_display": code,
        "indication_type": "five_bit_led_pattern",
        "display_location": location,
        "family_hint": family,
        "relationship": meaning,
        "led_indicators": [{"label": label, "color": "green", "state": state} for label, state in (
            (item.split(":")[0], item.split(":")[1]) for item in states
        )],
        "counting_rule": "Observe cinco ventanas de un segundo durante los cinco segundos activos.",
        "cycle_note": "Después hay cinco segundos de pausa y el ciclo se repite.",
        "sequence": " · ".join(states),
    }


BS_IN_PATTERNS = [five_bit_pattern(code, title, "BS DCI interior", "LED FILTER y TIMER") for code, title, _ in BS_INDOOR]
BS_OUT_PATTERNS = [five_bit_pattern(code, title, "BS DCI exterior", "LED FILTER y TIMER") for code, title, _ in BS_OUTDOOR]
DUO_IN_PATTERNS = [five_bit_pattern(code, title, "DUO 50 DCI interior", "MSMP: LED de unidad + cinco LED de estado") for code, title, _ in DUO_INDOOR]
DUO_OUT_PATTERNS = [five_bit_pattern(code, title, "DUO 50 DCI exterior", "MSMP: LED exterior + cinco LED de estado") for code, title, _ in DUO_OUTDOOR]
TQ_IN_PATTERNS = [five_bit_pattern(code, title, "TRIO/QUATTRO interior", "LED HEAT y COOL") for code, title, _ in TQ_INDOOR]

DLS_PATTERN_BITS = {
    "1": "ON OFF OFF OFF OFF", "2": "ON OFF OFF OFF ON", "3": "ON OFF OFF ON OFF",
    "4": "OFF ON OFF OFF OFF", "5": "OFF ON OFF OFF ON", "7": "OFF ON OFF ON ON",
    "8": "OFF OFF ON OFF OFF", "9": "OFF OFF ON OFF ON",
    "11": "OFF OFF ON ON ON", "12": "OFF ON ON ON ON",
}


def dls_pattern(code: str, meaning: str) -> dict[str, Any]:
    states = DLS_PATTERN_BITS[code].split()
    return {
        "code_display": code,
        "indication_type": "five_window_led_pattern",
        "display_location": "LED COOL durante el ciclo del LED HEAT",
        "family_hint": "DLS/RPM",
        "relationship": meaning,
        "led_indicators": [{"label": str(index), "color": "green", "state": state.lower()} for index, state in enumerate(states, 1)],
        "counting_rule": "HEAT marca el ciclo; anote el estado de COOL en las cinco posiciones.",
        "cycle_note": "Cinco segundos activos y cinco de pausa.",
        "sequence": " ".join(f"{index}:{state}" for index, state in enumerate(states, 1)),
    }


DLS_PATTERNS = [dls_pattern(code, title) for code, title, _ in DLS_ERRORS]


def hrw_pattern(code: str, meaning: str, mode: str) -> dict[str, Any]:
    return {
        "code_display": code,
        "indication_type": "nine_position_green_led",
        "display_location": "LED verde de RCL o placa adaptadora",
        "family_hint": f"HRW 07-12 en modo {mode}",
        "relationship": meaning,
        "led_indicators": [{"label": str(index), "color": "green", "state": "blink" if bit == "1" else "off"} for index, bit in enumerate(code, 1)],
        "counting_rule": "1 significa destello verde; 0 significa ausencia de destello.",
        "cycle_note": "Tras las nueve posiciones hay una pausa de varios segundos y el patrón se repite.",
        "sequence": " ".join(code),
    }


HRW_COOL_PATTERNS = [hrw_pattern(code, title, "frío") for code, title, _ in HRW_COOL]
HRW_HEAT_PATTERNS = [hrw_pattern(code, title, "calor") for code, title, _ in HRW_HEAT]


add_topic("errors", "same-number-many-families", "Una cifra Airwell puede tener muchas interpretaciones", "La aplicación no abre ninguna por defecto: primero muestra toda la lista.", [
    v("Código 3", "Puede aparecer en BS, DLS, DUO, TRIO/QUATTRO o MSMP.", "DLS", "13-30", "No aplicar una definición universal.", "Puede ser sonda RT-2, CTT, válvula de cuatro vías o HST según familia y punto de lectura."),
    v("Códigos 11 y 21", "Se leen en interior, exterior, MSMP o HMI.", "TQ", "12-2 a 12-5", "Separar protección y componente.", "11 puede ser aviso de exterior o IPM; 21 puede ser desescarche exterior o desbordamiento interior."),
    v("29, 30 y 31", "Aparecen al recorrer diagnósticos aunque la máquina no esté averiada.", "DUO", "12-2 a 12-5", "Reconocer estado/modelo.", "En MSMP son estados sin fallo; en otros interiores pueden identificar el modelo."),
])

add_topic("outdoor_diagnostics", "bs-five-bit-tables", "BS DCI: tablas completas interior y exterior", "FILTER/TIMER representan cinco bits; los tres LED distinguen interior de exterior.", [
    v("Tabla interior BS", "STBY/Operate, Filter y Timer permanecen encendidos.", "BS", "12-3 (PDF 38)", "Traducir el patrón interior.", "Solo se muestra un código; la prioridad va del número menor al mayor.", system="BS DCI", scope="indoor", led_patterns=BS_IN_PATTERNS),
    v("Tabla exterior BS", "Los tres LED interiores parpadean y FILTER/TIMER transportan el código.", "BS", "12-3 a 12-4 (PDF 38-39)", "Traducir el patrón exterior.", "No confunda el mismo número con la tabla interior.", system="BS DCI", scope="outdoor", led_patterns=BS_OUT_PATTERNS),
])

add_topic("outdoor_diagnostics", "duo-msmp-table", "DUO 50: tabla completa del controlador MSMP", "Un LED selecciona la unidad y cinco LED muestran el estado.", [
    v("Exterior MSMP", "LED de unidad exterior activo; código estable durante diez segundos si hay fallo.", "DUO", "12-2 a 12-3 (PDF 55-56)", "Leer la unidad exterior.", "El controlador dispone de un LED STBY, cinco LED de unidad y cinco LED de estado/fallo.", system="DUO 50 DCI", scope="outdoor", led_patterns=DUO_OUT_PATTERNS),
    v("Interiores MSMP", "LED de la interior correspondiente activo.", "DUO", "12-4 a 12-5 (PDF 57-58)", "Leer la unidad afectada.", "Una unidad normal se muestra cinco segundos; una unidad con fallo, diez.", system="DUO 50 DCI", scope="indoor", led_patterns=DUO_IN_PATTERNS),
])

add_topic("outdoor_diagnostics", "trio-quattro-hmi", "TRIO/QUATTRO: display HMI exterior de tres dígitos", "Los códigos 1-30 son números del display, no cinco destellos.", [
    v("Tabla exterior 1-30", "Placa exterior con HMI de tres displays de siete segmentos.", "TQ", "12-2 a 12-3 (PDF 84-85)", "Aplicar la tabla exterior correcta.", "Incluye sondas, fan/IPM, compresor, red, puertos A-D, configuración y protecciones.", system="TRIO/QUATTRO DCI", scope="outdoor"),
    v("Puertos A-D", "Aparecen 18, 19, 20 o 21 en el HMI.", "TQ", "12-3 (PDF 85)", "Localizar la rama sin comunicación.", "18=A, 19=B, 20=C y 21=D; revise esa línea antes de condenar todo el sistema.", system="TRIO/QUATTRO DCI", scope="outdoor"),
])

add_topic("outdoor_diagnostics", "hrw-led-codes", "HRW 07-12: patrones de alarma por modo", "La misma secuencia tiene causas distintas en frío y calor.", [
    v("Tabla modo frío", "LED verde de RCL o adaptador y unidad en refrigeración.", "HRW", "32 y 34", "Traducir nueve posiciones.", "La tabla incluye alta/baja, térmico, límites de agua, antihielo, desbordamiento y otras alarmas.", system="HRW 07-12", led_patterns=HRW_COOL_PATTERNS),
    v("Tabla modo calor", "Mismo LED y unidad en calefacción.", "HRW", "33 y 34", "Usar umbrales de calor.", "Añade protección antihielo del intercambiador y cambia límites/causas respecto a frío.", system="HRW 07-12", led_patterns=HRW_HEAT_PATTERNS),
])

add_topic("diagnostic_access", "bs-diagnostics-entry", "BS DCI: entrar, distinguir interior/exterior y salir", "MODE/RESET durante cinco segundos.", [
    v("Entrada común", "Display interior con MODE/RESET y tres LED.", "BS", "12-3 (PDF 38)", "Activar diagnósticos.", "Tres pitidos cortos y el estado de los tres LED confirman la entrada.", system="BS DCI", steps=[
        step(1, "Mantenga MODE/RESET cinco segundos en cualquier modo.", phase="prepare"),
        step(2, "Espere tres pitidos cortos y observe STBY/Operate, Filter y Timer."),
        step(3, "Tres LED parpadeando = exterior; tres LED fijos = interior.", phase="verify"),
    ]),
    v("Prioridad y código persistente", "Hay más de una avería o la máquina ya recuperó.", "BS", "12-3 (PDF 38)", "Entender lo mostrado.", "Solo aparece un código y el último permanece visible aunque la avería haya recuperado.", system="BS DCI"),
])

add_topic("diagnostic_access", "dls-diagnostics-entry", "DLS/RPM: lectura COOL/HEAT", "MODE entre cinco y diez segundos; COOL contiene el patrón.", [
    v("Activar diagnóstico", "Panel con LED COOL y HEAT.", "DLS", "13-30 (PDF 100)", "Leer códigos 1-12.", "Tres pitidos y ambos LED confirman la entrada; HEAT delimita el ciclo.", system="DLS/RPM", scope="indoor", steps=[
        step(1, "Mantenga MODE entre cinco y diez segundos."),
        step(2, "Confirme tres pitidos y encendido de COOL y HEAT."),
        step(3, "Anote las cinco posiciones de COOL mientras HEAT marca el ciclo.", phase="verify"),
    ], led_patterns=DLS_PATTERNS),
    v("Salir sin borrar el contexto", "Diagnóstico activo y mando disponible.", "DLS", "13-30 (PDF 100)", "Volver a funcionamiento.", "Cualquier orden del mando sale de diagnóstico; si contiene Group ID, pasa a ser el nuevo identificador.", system="DLS/RPM", scope="controller"),
])

add_topic("diagnostic_access", "tq-indoor-entry", "TRIO/QUATTRO: diagnóstico interior con MODE", "HEAT marca cinco ventanas y COOL forma el código.", [
    v("Entrada desde el display", "Mando/display CD o similar con MODE.", "TQ", "12-4 (PDF 86)", "Leer el código interior.", "Una pulsación larga activa diagnóstico, confirma con tres pitidos y enciende COOL/HEAT.", system="TRIO/QUATTRO DCI", scope="indoor", led_patterns=TQ_IN_PATTERNS),
    v("Solo consulta desde standby", "Se entra con el sistema en SB.", "TQ", "12-4 (PDF 86)", "Evitar una maniobra involuntaria.", "Desde standby el diagnóstico permite ver estado/fallo; no cambia el modo de funcionamiento.", system="TRIO/QUATTRO DCI", scope="controller"),
])

add_topic("history_reset", "memory-and-exit", "Qué ocurre con el último código al salir", "No todas las familias conservan el historial igual.", [
    v("BS: el último código se borra al salir", "Diagnóstico BS activo.", "BS", "12-3 (PDF 38)", "Conservar evidencia.", "El manual indica que el último fallo se elimina de EEPROM después de salir del modo diagnóstico.", system="BS DCI", steps=[
        step(1, "Fotografíe o anote código, tabla interior/exterior y modo.", phase="prepare", warning="important"),
        step(2, "Complete las comprobaciones antes de salir."),
        step(3, "Salga sabiendo que el registro indicado será eliminado.", phase="verify"),
    ]),
    v("DLS: una orden sale y puede reprogramar Group ID", "Diagnóstico DLS activo.", "DLS", "13-30 (PDF 100)", "Evitar cambiar dirección por accidente.", "Si la orden del mando contiene Group ID, ese valor se convierte en el nuevo ID de la unidad.", system="DLS/RPM", scope="controller"),
    v("HRW: autoanulación y bloqueo por repetición", "LED verde de alarma RCL/adaptador.", "HRW", "32-34", "Distinguir recuperación y reset.", "Varias filas se anulan tras corregir; tres fallos en una hora paran la unidad y requieren cortar alimentación cinco segundos.", system="HRW 07-12"),
])

add_topic("service_modes", "bs-duo-test", "BS y DUO: Test con consignas fijas", "Frío 16 °C o calor 30 °C, ventilador alto.", [
    v("BS DCI", "Una interior BS con mando compatible.", "BS", "11-15 y 12-2", "Comprobar rendimiento con ajustes fijos.", "Seleccione Cool 16 °C/High o Heat 30 °C/High y entre en diagnóstico para activar Test.", system="BS DCI", steps=[
        step(1, "Seleccione frío 16 °C y ventilador alto, o calor 30 °C y ventilador alto.", phase="prepare"),
        step(2, "Entre en diagnóstico con MODE/RESET."),
        step(3, "Mida solo bajo las condiciones y curvas del manual.", phase="verify", warning="important"),
    ]),
    v("DUO 50 DCI", "Dos interiores conectadas a la misma exterior.", "DUO", "12-2 (PDF 55)", "Probar el multisplit.", "Ambas interiores deben quedar en el mismo modo y velocidad alta antes de entrar.", system="DUO 50 DCI", steps=[
        step(1, "Ajuste las dos interiores al mismo modo.", phase="prepare"),
        step(2, "Use Cool 16 °C/High o Heat 30 °C/High en ambas."),
        step(3, "Entre en diagnóstico y confirme que las dos aceptan la prueba.", phase="verify"),
    ]),
    v("Advertencia de protección", "Test activo en BS o DUO.", "BS", "11-15", "No usar como funcionamiento normal.", "El manual declara deshabilitadas las protecciones durante Test salvo la condición de parada del compresor.", system="BS/DUO", steps=[
        step(1, "Limite la prueba al tiempo imprescindible.", phase="prepare", warning="danger"),
        step(2, "Vigile presiones, temperaturas e intensidad con instrumentos externos.", warning="danger"),
        step(3, "Salga inmediatamente si aparece una condición anormal.", phase="verify", warning="danger"),
    ]),
])

add_topic("service_modes", "dls-self-test", "DLS: autoprueba completa desde mando", "Secuencia oculta que recorre modelo, relés, sensores y EEPROM.", [
    v("Entrada por mando", "Unidad funcionando y mando IR.", "DLS", "13-27 a 13-29 (PDF 97-99)", "Iniciar autoprueba.", "La secuencia de autoprueba por mando usa Heat/High a 16 grados Celsius con IR visible/oculto y después Cool/Low.", system="DLS/RPM", scope="controller", steps=[
        step(1, "Con la unidad en marcha, envíe HEAT, ventilador HIGH y 16 °C.", phase="prepare"),
        step(2, "Tape el transmisor IR para que la segunda orden no llegue."),
        step(3, "Seleccione COOL y ventilador LOW con el IR tapado."),
        step(4, "Destape el IR y cambie la temperatura; la unidad debe iniciar la autoprueba.", phase="verify"),
    ]),
    v("Recorrido de salidas", "Autoprueba ya iniciada.", "DLS", "13-27 a 13-29 (PDF 97-99)", "Comprobar actuadores.", "Recorre configuración, step motor, LED, compresor, fan exterior, RV, heaters, bomba, swing, fan interior, comunicación, termistores y EEPROM.", system="DLS/RPM"),
    v("Salida y resultado EEPROM", "La prueba ha terminado o debe cancelarse.", "DLS", "13-29 (PDF 99)", "Cerrar correctamente.", "STBY indica EEPROM correcta y FILTER fallo; cambie Cool/Low a Cool/Med o espere 60 segundos para salir.", system="DLS/RPM"),
])

add_topic("service_modes", "tq-technician-test", "TRIO/QUATTRO: Technician Test", "Modo fijo desde los menús técnicos del HMI.", [
    v("Entrada y señalización", "HMI exterior con menús Technician.", "TQ", "11-15 a 11-21", "Probar con condiciones fijas.", "El menú de prueba en frío o calor parpadea continuamente mientras está seleccionado.", system="TRIO/QUATTRO DCI", scope="outdoor"),
    v("Salida automática", "Technician Test activo.", "TQ", "11-19", "No dejar el equipo indefinidamente.", "La prueba técnica termina automáticamente a los 60 minutos.", system="TRIO/QUATTRO DCI", scope="outdoor"),
])

add_topic("configuration", "dls-model-plug-dips", "DLS: Model Plug y DIP del mando", "La placa distingue ST, RC, SH y RH; el mando limita funciones.", [
    v("J6/J2 del Model Plug", "PCB DLS con puentes J6 y J2.", "DLS", "11-1 a 11-2 (PDF 71-72)", "Identificar el tipo de control.", "ST/RC: J6 y J2 abiertos; SH: J6 cerrado/J2 abierto; RH: ambos cerrados.", system="DLS/RPM", scope="indoor"),
    v("SW1/SW2 del mando", "Banco DIP del mando RC3/RC4.", "DLS", "11-1 a 11-2 (PDF 71-72)", "Limitar modos accesibles.", "00 todos los modos; 01 frío/fan/dry; 10 calor/frío/fan/dry; 11 auto fan.", system="DLS/RPM", scope="controller"),
    v("Reset tras cambiar DIP", "DIP ya ajustados.", "DLS", "11-1 a 11-2 (PDF 71-72)", "Aplicar configuración.", "Mantenga CLEAR + SET + HR+ + HR- durante cinco segundos.", system="DLS/RPM", scope="controller"),
])

add_topic("configuration", "tq-system-configuration", "TRIO/QUATTRO: puertos, capacidad y configuración", "La exterior compara líneas A-D y capacidad total.", [
    v("Aviso 23", "Se han cambiado líneas respecto al último funcionamiento.", "TQ", "12-3 (PDF 85)", "Reconocer anuncio.", "El manual indica expresamente que no es un problema; informa del cambio.", system="TRIO/QUATTRO DCI", scope="outdoor"),
    v("Fallo 24", "Interiores conectadas a puerto incorrecto o capacidad total excesiva.", "TQ", "12-3 (PDF 85)", "Corregir combinación.", "Compruebe puertos A-D y códigos de capacidad antes de sustituir una placa.", system="TRIO/QUATTRO DCI", scope="outdoor"),
    v("Reset de parámetros de fábrica", "HMI en menú RST.", "TQ", "11-19", "Restaurar solo parámetros.", "SELECT + ESCAPE durante más de cinco segundos restaura parámetros de fábrica; RST parpadea tres segundos.", system="TRIO/QUATTRO DCI", scope="outdoor"),
])

add_topic("controllers_buses", "airwell-control-interfaces", "Cómo reconocer mandos y placas Airwell históricas", "Cinco interfaces con lecturas distintas.", [
    v("Display BS/CD", "Tres LED y tecla MODE/RESET.", "BS", "12-3", "Acceder a interior/exterior.", "Los tres LED fijos o parpadeando seleccionan la tabla.", system="BS DCI", scope="controller"),
    v("Control DLS RC3/RC4", "Mando IR con SLEEP, CLEAR, SET y HR.", "DLS", "11-1 a 13-30", "Configurar y autoprobar.", "Los DIP del mando cambian modos, reloj, swing o iluminación.", system="DLS/RPM", scope="controller"),
    v("MSMP", "Placa con un STBY, cinco LED de unidad y cinco de estado.", "DUO", "12-2", "Localizar interior/exterior.", "Recorre unidades y prolonga diez segundos la que presenta fallo.", system="DUO 50 DCI", scope="outdoor"),
    v("HMI 3x7 segmentos", "Display exterior de tres dígitos y menús técnicos.", "TQ", "1-2 y 11-15", "Diagnóstico y ajustes.", "Muestra diagnóstico exterior y funciones de configuración.", system="TRIO/QUATTRO DCI", scope="outdoor"),
    v("RCL / placa adaptadora", "LED verde con patrón de nueve posiciones.", "HRW", "20-26, 32-34", "Leer alarmas y configuración.", "El mismo patrón debe cruzarse con el modo frío/calor.", system="HRW 07-12", scope="controller"),
])

add_topic("controllers_buses", "communication-and-monitoring", "Comunicación: incompatibilidad, ausencia y baja calidad", "Airwell separa tres fallos que suelen confundirse.", [
    v("Mismatch", "Código 7 interior o 16 exterior.", "BS", "12-3 a 12-5", "Comparar versiones.", "La tabla atribuye el mismatch a controladores interior y exterior con versiones distintas.", system="BS/DUO"),
    v("No communication", "Código 8 interior, 17 exterior o 18-21 TQ.", "TQ", "12-3 a 12-5", "Buscar línea abierta.", "Revise señal, cable, tierra y alimentación; en TQ cada número identifica un puerto.", system="BS/DUO/TQ"),
    v("Bad communication", "Código 26 interior o 27 exterior.", "BS", "12-4 a 12-5", "Evaluar fiabilidad.", "Hay intercambio, pero la proporción de mensajes correctos/incorrectos es insuficiente.", system="BS/DUO/TQ"),
])

add_topic("drainage_overflow", "dls-condensate-logic", "DLS DNC: lógica de bomba y desbordamiento", "El comportamiento cambia si la unidad estaba ON u OFF.", [
    v("Desbordamiento con unidad ON", "DNC en Cool, Dry o Auto; contacto de nivel abre.", "DLS", "13-25 (PDF 95)", "Proteger la bandeja.", "COMP/WVL queda forzado OFF, OPER parpadea y la bomba sigue activa mientras se evacua.", system="DLS DNC", scope="indoor"),
    v("Desbordamiento con unidad OFF", "Unidad en standby y contacto de nivel abre.", "DLS", "13-25 (PDF 95)", "Evacuar sin demanda de frío.", "El propio desbordamiento puede arrancar la bomba aun con la unidad parada.", system="DLS DNC", scope="indoor"),
    v("Temporizaciones documentadas", "La boya vuelve a normal.", "DLS", "13-25 (PDF 95)", "No cortar antes de tiempo.", "El diagrama contiene prolongaciones de ocho minutos y una ventana de un minuto; siga la secuencia gráfica de esta familia.", system="DLS DNC", scope="indoor"),
])

add_topic("drainage_overflow", "overflow-across-families", "Desbordamiento en multisplit y HRW", "El código puede proceder de boya, cable, evacuación o placa.", [
    v("Código interior 21", "MSMP o diagnóstico interior TQ.", "DUO", "12-4 a 12-5", "Localizar la interior afectada.", "La protección se registra en la unidad interior; no debe confundirse con el 21 exterior de deicing.", system="DUO/TQ", scope="indoor"),
    v("HRW 111111110", "RCL/adaptador en frío o calor.", "HRW", "32-34", "Revisar flotador y bandeja.", "El manual cita evacuación obstruida, flotador bloqueado/mal conectado, cable roto y pérdidas de carga/filtros según modo.", system="HRW 07-12"),
])

add_topic("commissioning", "prestart-checks", "Comprobaciones antes de arrancar", "La tabla de errores no sustituye la instalación.", [
    v("Red y tierra", "BS/DUO/TQ antes de Test.", "TQ", "12-5 a 12-8", "Evitar diagnósticos falsos.", "Confirme 198-264 V CA en la familia documentada, tierra, fusible, terminales y ausencia de daños.", system="BS/DUO/TQ"),
    v("Puertos y capacidades", "TRIO/QUATTRO con varias interiores.", "TQ", "11-15 a 12-3", "Evitar 23/24.", "Compruebe cada línea A-D, interior reconocida y capacidad total antes del Technician Test.", system="TRIO/QUATTRO DCI"),
    v("HRW hidráulica", "Bomba de calor sobre bucle de agua.", "HRW", "28-29", "Proteger el intercambiador.", "Abra válvulas, confirme circulación y temperatura de bucle antes de pedir frío o calor.", system="HRW 07-12"),
])

add_topic("multisplit", "ports-and-continuity", "Qué puede seguir funcionando en un multisplit", "La documentación permite aislar una rama, pero no autoriza a suponer una parada total.", [
    v("DUO: selección por LED de unidad", "MSMP recorre interiores y exterior.", "DUO", "12-2 a 12-5", "Saber dónde está el fallo.", "Anote qué LED de unidad estaba activo; el mismo número cambia entre interior y exterior.", system="DUO 50 DCI"),
    v("TRIO/QUATTRO: líneas A-D", "Códigos exteriores 18-21.", "TQ", "12-3 (PDF 85)", "Aislar el puerto.", "El código identifica la línea sin señal; la tabla no declara parada general para cada evento.", system="TRIO/QUATTRO DCI"),
    v("Alarma por contacto seco", "Salida de alarma exterior disponible.", "TQ", "1-2 y diagramas de control", "Integrar aviso remoto.", "El contacto se activa ante fallo/protección exterior y vuelve al desaparecer la condición.", system="TRIO/QUATTRO DCI", scope="outdoor"),
])

add_topic("operational_effects", "protection-versus-announcement", "Protección, aviso y estado normal", "El número no siempre implica una avería.", [
    v("23 TQ: solo anuncio", "HMI exterior muestra 23.", "TQ", "12-3 (PDF 85)", "Evitar sustituir componentes.", "Indica que las líneas de comunicación cambiaron respecto al último uso.", system="TRIO/QUATTRO DCI"),
    v("26 TQ: deicing", "HMI muestra 26 durante desescarche.", "TQ", "12-3 (PDF 85)", "Reconocer proceso normal.", "La acción correctiva es 'no action required'.", system="TRIO/QUATTRO DCI"),
    v("25, 27 y 28 TQ", "HMI exterior y compresor parado.", "TQ", "12-3 (PDF 85)", "Identificar protección real.", "Disipador, sobretemperatura o sobrepotencia detienen el compresor; investigue antes de rearmar.", system="TRIO/QUATTRO DCI"),
    v("29-31 MSMP", "MSMP recorre una unidad sin fallo.", "DUO", "12-2 a 12-5", "Leer el modo normal.", "29=calor, 30=frío/dry/fan y 31=standby sin avería.", system="DUO 50 DCI"),
])

add_topic("component_checks", "tq-motors-compressor", "TRIO/QUATTRO: ventilador y compresor", "Valores de devanado y corriente documentados.", [
    v("Ventilador exterior BLDC", "Códigos 7-10.", "TQ", "12-5 a 12-6 (PDF 87-88)", "Separar bloqueo, bobina y driver.", "Giro libre, corriente por fase inferior a 1 A y resistencias de bobina similares entre 10 y 20 Ω.", system="TRIO/QUATTRO DCI", scope="outdoor"),
    v("Compresor inverter", "Códigos 7, 11-14, 22, 27 o 28.", "TQ", "12-6 (PDF 88)", "Separar compresor y control.", "Corriente por fase no superior a 15 A; resistencias entre polos similares, entre 0,8 y 1,5 Ω.", system="TRIO/QUATTRO DCI", scope="outdoor"),
])

add_topic("component_checks", "tq-valves-thermistors", "TRIO/QUATTRO: RV, EEV y sondas", "Pruebas específicas de salida y respuesta.", [
    v("Válvula de cuatro vías", "Frío funciona pero calor no, o al contrario.", "TQ", "12-6 (PDF 88)", "Separar bobina y válvula.", "En calefacción la bobina debe recibir 230 V CA; si actúa con alimentación directa pero no desde placa, revise el control.", system="TRIO/QUATTRO DCI", scope="outdoor"),
    v("Válvula de expansión electrónica", "Al alimentar no hay clic/vibración.", "TQ", "12-6 (PDF 88)", "Comprobar drive y válvula.", "El motor EEV trabaja a 12 V CC; confirme prueba de instalación y conectores antes de sustituir.", system="TRIO/QUATTRO DCI", scope="outdoor"),
    v("Termistores TQ", "Códigos 1-6 exterior.", "TQ", "12-6 (PDF 88)", "Comprobar plausibilidad.", "Entre 0 y 40 °C el manual da una banda general aproximada de 35 kΩ a 5 kΩ.", system="TRIO/QUATTRO DCI", scope="outdoor"),
])

add_topic("component_checks", "communication-check", "Comprobar comunicación y tierra", "La continuidad documentada debe ser inferior a 2 Ω.", [
    v("Línea interior-exterior", "Código 8, 17, 18-21, 26 o 27.", "TQ", "12-6 (PDF 88)", "Separar cable y placa.", "Con equipo seguro, revise conexiones y continuidad de comunicación/tierra; el manual fija menos de 2,0 Ω.", system="BS/DUO/TQ"),
    v("Reinicio de contraste", "Fallo de comunicación activo.", "TQ", "12-6 (PDF 88)", "Confirmar persistencia.", "Pase a standby o corte/restablezca alimentación; si persiste, aísle la interior que no responde o la exterior.", system="TRIO/QUATTRO DCI"),
])

add_topic("technical_values", "dls-sensor-voltage", "DLS: temperatura frente a tensión de sonda", "Tabla completa de -20 a 67 °C, con puntos de contraste.", [
    v("-20, 0 y 25 °C", "Entrada analógica DLS con tabla de 5 V.", "DLS", "13-29 (PDF 99)", "Contrastar la lectura.", "Valores documentados: -20 °C = 4,554 V; 0 °C = 3,839 V; 25 °C = 2,500 V.", system="DLS/RPM"),
    v("44 y 67 °C", "Temperatura alta en la misma curva.", "DLS", "13-29 (PDF 99)", "Comprobar continuidad de curva.", "44 °C = 1,569 V y 67 °C = 0,831 V. No aplicar esta tabla a otra familia sin confirmación.", system="DLS/RPM"),
])

add_topic("technical_values", "power-thresholds", "Red, bus y umbrales eléctricos", "Valores diferentes según familia.", [
    v("BS/DUO/TQ: 198-264 V CA", "Alimentación monofásica de la familia revisada.", "TQ", "12-5 (PDF 87)", "Descartar red anormal.", "Fuera de la banda el manual espera funcionamiento anómalo.", system="BS/DUO/TQ"),
    v("TQ: 270/170 V CA", "Códigos 16 o 17 en HMI exterior.", "TQ", "12-3 (PDF 85)", "Distinguir red y placa.", "La tabla manda comprobar sobretensión por encima de 270 V CA y subtensión por debajo de 170 V CA.", system="TRIO/QUATTRO DCI"),
    v("HRW: 230 V ±10 %", "Bomba de calor sobre bucle de agua.", "HRW", "9", "Comprobar alimentación.", "El manual indica 207 V mínimo y 253 V máximo.", system="HRW 07-12"),
])

add_topic("technical_values", "drain-times", "Temporizaciones de drenaje y bloqueo", "No confundir continuidad de bomba con avería.", [
    v("DLS DNC", "Bomba activa después de compresor o desbordamiento.", "DLS", "13-25 (PDF 95)", "Esperar la secuencia.", "El gráfico usa prolongación de ocho minutos y una ventana de un minuto según estado ON/OFF.", system="DLS DNC"),
    v("HRW: repetición", "Alarma se repite tres veces en una hora.", "HRW", "32-33", "Reconocer bloqueo.", "Tras el tercer evento la unidad se detiene; el manual pide cortar cinco segundos y reconectar.", system="HRW 07-12"),
])

add_topic("normal_states", "not-a-fault", "Indicaciones que no son avería", "Aparecen en las mismas tablas de diagnóstico.", [
    v("MSMP 29-31", "Unidad normal durante el barrido.", "DUO", "12-2 a 12-5", "Reconocer el modo.", "Calor, frío/dry/fan y standby se codifican aunque no exista fallo.", system="DUO 50 DCI"),
    v("TQ 23 y 26", "HMI exterior muestra configuración modificada o deicing.", "TQ", "12-3", "Evitar intervenciones innecesarias.", "23 es anuncio; 26 es protección durante desescarche sin acción requerida.", system="TRIO/QUATTRO DCI"),
    v("BS/TQ 27-31", "Interior muestra datos EEPROM o modelo.", "TQ", "12-4 a 12-5", "Distinguir identificación.", "27 confirma datos EEPROM y 28-31 pueden identificar capacidad/modelo.", system="BS/TQ"),
])

add_topic("service_tools_boards", "megatool-and-hmi", "Herramientas de monitorización Airwell histórica", "La herramienta ayuda a observar; no sustituye la tabla de la familia.", [
    v("MegaTool", "PC con puerto RS232, cable especial y software Airwell.", "BS", "12-6 y 13-1", "Monitorizar control interior/exterior.", "Se conecta al controlador correspondiente para observar el sistema; use el cable y software específicos.", system="BS/DUO", scope="controller"),
    v("HMI exterior", "Tres displays de siete segmentos en TRIO/QUATTRO.", "TQ", "1-2 y 11-15", "Diagnóstico y ajustes locales.", "Muestra códigos exteriores y permite los menús de técnico/configuración.", system="TRIO/QUATTRO DCI", scope="outdoor"),
    v("MSMP", "Módulo de once LED.", "DUO", "12-2", "Barrido de unidades.", "Selecciona la unidad y conserva más tiempo los códigos de fallo para facilitar la lectura.", system="DUO 50 DCI", scope="outdoor"),
])

add_topic("service_tools_boards", "after-pcb-work", "Después de intervenir en una placa", "Antes de dar por terminada la reparación, restaure configuración y compruebe comunicación.", [
    v("EEPROM y parámetros", "Códigos 12, 19, 24, 25, 27, 29 o 30.", "TQ", "12-3 a 12-5", "No confundir placa nueva y fallo.", "Compruebe parámetros ROM/EEPROM, configuración, modelo y datos copiados antes de sustituir de nuevo.", system="BS/DUO/TQ"),
    v("Puentes y tipo de motor", "Fallo IPM/velocidad después de cambiar controlador.", "TQ", "12-2 a 12-3", "Restaurar compatibilidad.", "La tabla pide comprobar que el tipo de motor coincide con los jumpers del controlador.", system="TRIO/QUATTRO DCI", scope="outdoor"),
])

add_topic("system_architecture", "recognize-airwell-family", "Reconocer qué Airwell histórica tiene delante", "El aspecto del control decide la tabla.", [
    v("BS DCI", "Conductos BS 12 DCI, tres LED y MODE/RESET.", "BS", "portada y 12-3", "Usar tablas BS.", "Interior/exterior se distinguen por tres LED fijos o parpadeando.", system="BS DCI"),
    v("DLS/RPM", "Conductos DLS 18-44 con mando RC3/RC4.", "DLS", "portada, 11-1 y 13-30", "Usar tabla COOL/HEAT.", "Incluye Model Plug, autoprueba y DNC con bomba.", system="DLS/RPM"),
    v("DUO 50 DCI", "Exterior para dos interiores y placa MSMP.", "DUO", "portada y 12-2", "Usar selección de unidad.", "El LED de unidad es tan importante como el número.", system="DUO 50 DCI"),
    v("TRIO/QUATTRO DCI", "Exterior con puertos A-D y HMI 3x7 segmentos.", "TQ", "portada, 1-2 y 12-2", "Usar HMI exterior y COOL/HEAT interior.", "Los códigos 18-21 localizan cada línea.", system="TRIO/QUATTRO DCI"),
    v("HRW 07-12", "Bomba de calor sobre bucle de agua con RCL/µBMS.", "HRW", "1, 20-34", "Usar patrones de nueve posiciones.", "Cruce siempre el patrón con frío o calor.", system="HRW 07-12"),
])

add_topic("system_architecture", "search-strategy", "Cómo buscar sin mezclar generaciones", "Busque código, interfaz y lugar de lectura.", [
    v("Número + punto de lectura", "Ejemplo: 11 exterior, 21 interior o 111111110 HRW.", "TQ", "12-2 a 12-5", "Reducir posibilidades.", "La aplicación mantiene cerradas todas las interpretaciones hasta que el técnico elige.", system="Super Técnico"),
    v("Rasgos visibles", "No conoce el modelo.", "DUO", "12-2", "Llegar por aspecto.", "Pruebe 'MSMP once LED', 'HMI tres dígitos', 'COOL HEAT', 'MODE RESET' o 'RCL nueve posiciones'.", system="Super Técnico"),
])

add_topic("provenance", "manufacturer-policy", "Regla de inclusión: fabricación Airwell acreditada", "Un logotipo o un manual moderno no bastan.", [
    v("Corpus industrial 2005/2008", "Documento Airwell con edición original 2005 y revisión límite de 2008.", "HISTORY25", "repères historiques", "Aceptar familias de la etapa industrial propia.", "BS, DLS, DUO y TRIO/QUATTRO se aceptan como corpus técnico de esa etapa; cada dato conserva documento y página.", system="Control de procedencia"),
    v("Fabricante explícito HRW", "El propio manual imprime AIRWELL Industrie France, Tillières-sur-Avre.", "HRW", "40", "Acreditar fabricación.", "HRW 07-12 queda aceptada por declaración expresa de fabricante en el documento.", system="Control de procedencia"),
    v("Corte de 2008", "La historia oficial indica 'désengagement industriel et restructuration'.", "HISTORY25", "repères historiques", "Evitar rebrands posteriores.", "Después de 2008 se excluye toda familia salvo prueba explícita de fabricación Airwell.", system="Control de procedencia"),
])

add_topic("provenance", "excluded-families", "Familias excluidas por ahora", "La ausencia es intencionada.", [
    v("Equipos posteriores a 2008", "Solo aparece marca Airwell, importador o catálogo y el origen no está acreditado.", "HISTORY25", "repères historiques", "Mantener fuera la marca blanca.", "No se incorporan códigos actuales o de terceros con origen no acreditado, sin declaración de fábrica o fabricante verificable.", system="Control de procedencia"),
    v("Servicio de códigos actual", "La web actual contiene códigos, pero no acredita quién fabricó cada unidad.", "HISTORY17", "historia de la marca", "No contaminar la base histórica.", "Los códigos modernos se mantienen fuera de Airwell histórica hasta documentar origen industrial.", system="Control de procedencia"),
])


PROVENANCE = {
    "policy_version": "1.0",
    "brand_slug": "airwell-historica",
    "rule": (
        "Solo se publica una familia cuando pertenece al corpus industrial propio anterior/al límite de 2008 "
        "o el documento identifica expresamente a Airwell como fabricante."
    ),
    "accepted": [
        {
            "family": "BS DCI, DLS/RPM, DUO 50 DCI y TRIO/QUATTRO DCI",
            "status": "accepted_historic_own_manufacturing_era",
            "evidence": (
                "Manuales Airwell con edición original de 2005 y revisiones de 2008; "
                "la historia corporativa sitúa el desenganche industrial en 2008."
            ),
            "source_ref": "HISTORY25",
            "page": "repères historiques",
        },
        {
            "family": "HRW 07-12",
            "status": "accepted_explicit_manufacturer",
            "evidence": "El manual identifica AIRWELL Industrie France y la fábrica de Tillières-sur-Avre.",
            "source_ref": "HRW",
            "page": "40",
        },
    ],
    "excluded": [
        {
            "scope": "familias posteriores a 2008 o de origen industrial no demostrado",
            "reason": "La marca comercial Airwell no prueba que el equipo fuera fabricado por Airwell.",
            "reconsider_when": "Exista placa, declaración de fabricante o documento industrial verificable para la familia concreta.",
        }
    ],
}


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
    write_json(WEB_DIR / "provenance.json", PROVENANCE)

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
            "reference_brand": "Airwell histórica",
            "verification_warning": (
                "Referencia restringida a familias de fabricación propia acreditada. "
                "No aplique estas tablas a equipos Airwell posteriores o reetiquetados sin confirmar origen."
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
        "language": "en/fr/es",
        "source_url": row["source_url"],
        "status": "reviewed",
        "notes": (
            "Fuente revisada para Airwell histórica Referencia V1. "
            "La aceptación de cada familia se rige por web/provenance.json."
        ),
    } for ident, row in enumerate(core.SOURCES.values(), start=1)])
    write_json(WEB_DIR / "coverage.json", [{
        "id": ident,
        "brand_id": BRAND_ID,
        "area_slug": slug,
        "area_name": name,
        "equipment_scope": "Airwell histórica — fabricación propia acreditada",
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
        "slug": "airwell-historica",
        "name": "Airwell histórica",
        "display_name": "Airwell (histórica)",
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
            "Airwell histórica Referencia V1: BS DCI, DLS/RPM, DUO 50 DCI, "
            "TRIO/QUATTRO DCI y HRW 07-12. Excluye equipos posteriores o de origen no acreditado."
        ),
    })
    write_quality(WEB_DIR / "quality.json", audit_brand(BRAND_DIR))
    return counts


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
