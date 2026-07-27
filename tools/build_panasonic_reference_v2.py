#!/usr/bin/env python3
"""Construye Panasonic Referencia V2 para Super Técnico.

La publicación contiene resúmenes técnicos trazables a documentación oficial.
No publica PDF, capturas, bases SQLite ni material gráfico de los manuales.
"""

from __future__ import annotations

import json
import math
import re
import shutil
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BRAND_DIR = ROOT / "data" / "brands" / "panasonic"
WEB_DIR = BRAND_DIR / "web"
BRAND_ID = 6


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def normalize(value: str) -> str:
    value = "".join(
        char
        for char in unicodedata.normalize("NFD", str(value or ""))
        if unicodedata.category(char) != "Mn"
    ).upper()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9]+", " ", value)).strip()


SOURCES: dict[str, dict[str, Any]] = {
    "RAC_PKE": {
        "title": "Service Manual — CS-E/RE/UE/XE PKEW",
        "document_ref": "PAPAMY1212045CE",
        "publication_date": "2012",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://www.panasonicproclub.com/uploads/CZ/catalogues/rac/service-manual/CS-ExxPKEW_service%20manual_PAPAMY1212045CE.pdf",
        "notes": "Split mural: autodiagnóstico inalámbrico, borrado, marcha forzada y códigos H/F.",
    },
    "RAC_JKE": {
        "title": "Service Manual — CS-E7/9/12/15/18/21JKE",
        "document_ref": "PHAAM0810051C2",
        "publication_date": "2008",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://www.panasonicproclub.com/uploads/CZ/catalogues/rac/service-manual/CS-E7JKEW_SM_PHAAM0810051C2.pdf0on.pdf",
        "notes": "Split de generación anterior para contrastar códigos, AUTO OFF/ON y temporizaciones.",
    },
    "MULTI_5E": {
        "title": "Service Manual — CU-5E34NBE",
        "document_ref": "SM700885-00",
        "publication_date": "2012",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://www.panasonicproclub.com/uploads/CZ/catalogues/rac/service-manual/CU-5E34NBE_service%20manual_SM700885-00_11.pdf",
        "notes": "Multisplit cinco conexiones: EEV, ventilador DC, tuberías, cableado y secuencias normales.",
    },
    "MULTI_4E": {
        "title": "Service Manual — CU-4E24RBU-5",
        "document_ref": "PAPAMY1505100CE",
        "publication_date": "2015",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://iaq.na.panasonic.com/hubfs/PCI%20-%20Panasonic%20North%20America%20Canada/Resources/Service%20Manual%20-%20CU-4E24RBU-5%20%28English%29%20%28PDF%29.pdf?hsLang=en",
        "notes": "Multisplit cuatro conexiones: detección de sensores, capacidad, comunicación y efecto operativo.",
    },
    "CASSETTE": {
        "title": "Service Manual — CS-E12RB4UW cassette",
        "document_ref": "PAPAMY1503095CE",
        "publication_date": "2015",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://iaq.na.panasonic.com/hubfs/PCI%20-%20Panasonic%20North%20America%20Canada/Resources/Service%20Manual%20-%20CS-E12RB4UW%20%28English%29.pdf?hsLang=en",
        "notes": "Cassette: esquema de boya y bomba, NTC de 15/20 kΩ y circuito de 5 V.",
    },
    "PACI_PE4": {
        "title": "Service Manual — PACi NX S-60…160PE4R",
        "document_ref": "PAPAMY2509044CE",
        "publication_date": "2025",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://www.panasonic.com/content/dam/pim/au/en/PA/PAC-S-/PAC-S-R32-INV-NX-SD-SPP/S-60_160PE4R_Service%20Manual.pdf",
        "notes": "Conductos PACi actuales: CZ-RTC5B/6, EEPROM, Test Run, drenaje y valores de motor.",
    },
    "PACI_HIGH": {
        "title": "Service Manual — PACi NX S-160…224PE4R",
        "document_ref": "PAPAMY2308067CE",
        "publication_date": "2023",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://www.panasonic.com/content/dam/pim/au/en/PA/PAC-S-/PAC-S-R32-INV-NX-SD-SPP/S-160_224PE4R_Service%20Manual.pdf",
        "notes": "Conductos de alta potencia: P10/P11/P12, drenaje y programación de servicio.",
    },
    "ECOI_CODES": {
        "title": "ECOi/VRF — guía técnica de códigos",
        "document_ref": "ECOI-VRF-CODE-GUIDE",
        "publication_date": "2010",
        "language": "nl",
        "document_type": "technical_guide",
        "source_url": "https://www.panasonicproclub.com/uploads/NL/catalogues/Storing-code%20ECOi-%20VRF.pdf",
        "notes": "Tablas desarrolladas de comunicación, sensores, compresores, ajustes y protecciones.",
    },
    "ECOI_2PIPE": {
        "title": "Service Manual — ECOi 2-Pipe ME1",
        "document_ref": "SM830186-00",
        "publication_date": "2010",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://www.panasonicproclub.com/uploads/CZ/catalogues/ecoi/service-manual/Ecoi_service%20manual_ME1%28SM830186-00%29.pdf",
        "notes": "ECOi 2 tubos: CZ-RTC2, monitor de sensores, alarmas, direccionamiento y servicio.",
    },
    "ECOI_W2": {
        "title": "Service Manual — W-2WAY ECOi",
        "document_ref": "W-2WAY-ECOI-SM",
        "publication_date": "2012",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://tda.panasonic-europe-service.com/GetDoc.aspx?ticket=1z68f8150cz1z35ed0z656ez706466zbc97825f14e0b62da22c08752d4906cc49498a66",
        "notes": "VRF de potencia: alcance de alarmas, mantenimiento de exterior y funcionamiento de respaldo.",
    },
    "VRF_MS3": {
        "title": "Installation Instructions — U-8…24MS3H7",
        "document_ref": "U-8_24MS3H7-II-EN",
        "publication_date": "2025",
        "language": "en",
        "document_type": "installation_manual",
        "source_url": "https://www.panasonic.com/content/dam/pim/id/id/VR/VRF-U-/VRF-U-MS3-SPP/U-8_24MS3H7_Installation%20Instructions_EN.pdf",
        "notes": "ECOi actual: S-LINK, terminadores, direccionamiento, LED exterior, pump down y alarmas.",
    },
    "RTC5": {
        "title": "Operating Instructions — CZ-RTC5A",
        "document_ref": "CZ-RTC5A-OM",
        "publication_date": "2016",
        "language": "en",
        "document_type": "controller_manual",
        "source_url": "https://iaq.na.panasonic.com/hubfs/PCI%20IAQ%20-%20North%20America%20US/Resources/CZ-RTC5a%20Operation%20Manual%20%28PDF%29.pdf?hsLang=en",
        "notes": "Mando cableado: 16 VDC, asignación, alarmas y comportamiento ante códigos transitorios.",
    },
    "RTC6_INSTALL": {
        "title": "Installation Instructions — CZ-RTC6/CZ-RTC6W",
        "document_ref": "WEB-ACXF60-38393-EN",
        "publication_date": "2023",
        "language": "en",
        "document_type": "controller_manual",
        "source_url": "https://www.panasonic.com/content/dam/pim/my/en/CZ/CZ-RTC/CZ-RTC6-SPP/CZ-RTC6%28W%29_Installation%20Instructions_EN.pdf",
        "notes": "Dos hilos R1/R2 sin polaridad, puesta en marcha, Main/Sub y Test Run.",
    },
    "RTC6_OPER": {
        "title": "Operating Instructions — CZ-RTC6/CZ-RTC6W",
        "document_ref": "CZ-RTC6-OM-EN",
        "publication_date": "2023",
        "language": "en",
        "document_type": "controller_manual",
        "source_url": "https://www.panasonic.com/content/dam/pim/my/en/CZ/CZ-RTC/CZ-RTC6-SPP/CZ-RTC6%28W%29_Operating%20Instructions_EN.pdf",
        "notes": "Menús de servicio, información de sensores, cuatro alarmas recientes y borrado.",
    },
    "CONEX": {
        "title": "CZ-RTC6 CONEX — H&C Control / H&C Diagnosis",
        "document_ref": "EU-4P-CZ-RTC6-CONEX-20",
        "publication_date": "2020",
        "language": "en",
        "document_type": "technical_guide",
        "source_url": "https://www.panasonicproclub.com/uploads/SI/catalogues/EU%204P%20CZ-RTC6%20CONEX%2020%20v2%20LR.pdf",
        "notes": "Aplicaciones de instalación, mantenimiento, monitorización, gráficas y registro.",
    },
    "CLOUD": {
        "title": "Panasonic AC Smart Cloud / Service Cloud",
        "document_ref": "EU-LFLTSMARTMULTI-SITE0622-02",
        "publication_date": "2022",
        "language": "en",
        "document_type": "technical_guide",
        "source_url": "https://www.panasonicproclub.com/uploads/GB/catalogues/EU-LFLTSMARTMULTI-SITE0622-02%20LR.pdf",
        "notes": "Servicio remoto: topología, alarmas, valores en vivo, tablas y gráficas.",
    },
    "OLD_PACI": {
        "title": "Service Manual — PACi R410A",
        "document_ref": "SM830194-00",
        "publication_date": "2010",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://www.panasonicproclub.com/uploads/HU/catalogues/service-manuals/SM830194-00.pdf",
        "notes": "Curvas oficiales de termistores de aire/intercambiador y descarga.",
    },
    "ECOI_3WAY": {
        "title": "Service Manual — ECOi 3-Way MF1",
        "document_ref": "SM830188-00",
        "publication_date": "2010",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://www.panasonicproclub.com/uploads/CZ/catalogues/ecoi/service-manual/Ecoi_service%20manual_MF1%28SM830188-00%29.pdf",
        "notes": "Tres tubos de 8–16 HP: respaldo, recuperación, mando de mantenimiento, alarmas y programación EEPROM.",
    },
    "RTC2_OPER": {
        "title": "Operating Instructions — CZ-RTC2",
        "document_ref": "CZ-RTC2-OM-9L",
        "publication_date": "2010",
        "language": "en",
        "document_type": "controller_manual",
        "source_url": "https://www.panasonicproclub.com/uploads/CZ/catalogues/ecoi/operating-instruction/CZ-RTC2_instruction%20manual_9L.pdf",
        "notes": "Mando cableado clásico ECOi/PACi: reconocimiento, botones, control diario y avisos.",
    },
    "PACI_WALL": {
        "title": "Service Manual — PACi NX mural S-25…100PK4R",
        "document_ref": "PAPAMY2509043CE",
        "publication_date": "2025",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://www.panasonic.com/content/dam/pim/au/en/PA/PAC-S-/PAC-S-R32-INV-WM-1-SPP/S-25_100PK4R_Service%20Manual.pdf",
        "notes": "PACi mural actual: placa interior, catálogo PAC, diagnóstico y reparación.",
    },
    "VRF_GEN_2026": {
        "title": "VRF General Catalogue 2026 — ECOi R32/R410A",
        "document_ref": "VRF-GEN-26-LR",
        "publication_date": "2026",
        "language": "en",
        "document_type": "technical_catalogue",
        "source_url": "https://www.panasonicproclub.com/uploads/LT/catalogues/VRF_GEN_26_LR.pdf",
        "notes": "Topologías actuales, capacidades, válvulas de seguridad R32 y efecto operativo por zona.",
    },
}


def source(ref: str, page: str, section_name: str, page_end: str | None = None) -> dict[str, Any]:
    row = SOURCES[ref]
    return {
        "title": row["title"],
        "document_ref": row["document_ref"],
        "source_url": row["source_url"],
        "page_start": page,
        "page_end": page_end or page,
        "section": section_name,
    }


CATEGORIES = [
    (1, "errors", "Errores y protecciones", "Códigos RAC, multisplit, PACi y ECOi/VRF con significados separados."),
    (2, "diagnostic_access", "Obtención de códigos y subcódigos", "Lectura inalámbrica, mandos cableados, LED y placa exterior."),
    (3, "history_reset", "Historial y borrado", "Memorias de mando, consulta de alarmas y rearme correcto."),
    (4, "service_modes", "Modos de servicio", "Test Run, marcha forzada, pump down, desescarche y recuperación."),
    (5, "configuration", "Configuración y programación", "Ajustes simple/detailed, EEPROM, sensores y placa exterior."),
    (6, "controllers_buses", "Mandos y buses", "CZ-RTC2/5/6, dos hilos R1/R2, S-LINK y comunicación RAC."),
    (7, "drainage_overflow", "Drenaje y desbordamiento", "Bomba, boya, P10/P11/P12 y secuencias por modo."),
    (8, "commissioning", "Puesta en marcha", "Test, auto-address, validación de red y comprobaciones previas."),
    (9, "multisplit", "Multisplit", "Capacidad, tuberías/cableado, conflictos y continuidad de otras interiores."),
    (10, "vrf_network", "ECOi/VRF y red S-LINK", "Direcciones, terminadores, unidades exteriores y alcance de parada."),
    (11, "component_checks", "Comprobación de componentes", "NTC, EEV, ventiladores, bombas, presiones, CT e inverter."),
    (12, "technical_values", "Valores técnicos", "Curvas, tensiones, resistencias, umbrales y temporizaciones."),
    (13, "normal_states", "Comportamientos normales", "Esperas, desescarche, retorno de aceite y protección temporal."),
    (14, "service_tools_boards", "Herramientas y placas", "CONEX, Service Cloud, sustitución de PCB y conservación de ajustes."),
    (15, "system_architecture", "Arquitectura y seguridad", "Cómo reconocer la familia y límites de intervención R32/VRF."),
]
CAT = {
    slug: {"id": category_id, "slug": slug, "name": name, "description": description}
    for category_id, slug, name, description in CATEGORIES
}


def operational_impact(text: str, scope: str) -> dict[str, Any]:
    norm = normalize(text)
    if "TODAS" in norm or "TODO EL SISTEMA" in norm:
        stop_level = "all_system"
    elif "CONTINUA" in norm or "NO ES AVERIA" in norm or "REINTENTO" in norm:
        stop_level = "warning"
    elif scope in {"indoor", "controller"}:
        stop_level = "affected_unit"
    else:
        stop_level = "protected_stop"
    return {
        "stop_level": stop_level,
        "summary": text,
        "affected_scope": "Alcance documentado para la familia Panasonic indicada.",
        "unaffected_scope": "No extrapolar a otra familia que reutilice el mismo código.",
        "restart_behavior": "Corregir la causa y aplicar el rearme o salida de servicio de la fuente citada.",
        "degraded_behavior": None,
        "notes": "En ECOi/VRF el efecto sobre otras interiores depende de la topología y de la categoría de alarma.",
    }


def ntc_beta_points(r25_kohm: float, beta: float) -> list[tuple[float, float]]:
    points = []
    for temp in (-20, -10, 0, 10, 20, 25, 30, 40, 50, 60, 80, 100):
        kelvin = temp + 273.15
        resistance = r25_kohm * math.exp(beta * ((1 / kelvin) - (1 / 298.15)))
        points.append((float(temp), round(resistance, 3)))
    return points


NTC_15K_B3950 = ntc_beta_points(15.0, 3950.0)
NTC_20K_B3950 = ntc_beta_points(20.0, 3950.0)
OLD_PACI_COIL = [
    (-10, 23.7), (-5, 18.8), (0, 15.0), (5, 12.1), (10, 9.7),
    (20, 6.5), (30, 4.4), (40, 3.1), (45, 2.6), (50, 2.1),
]
OLD_PACI_DISCHARGE = [
    (60, 12.4), (70, 8.7), (75, 7.4), (80, 6.3), (85, 5.3),
    (90, 4.6), (100, 3.4), (110, 2.5), (120, 1.9), (130, 1.5),
]


def curve_dataset(
    dataset_id: int,
    name: str,
    points: list[tuple[float, float]],
    ref: str,
    page: str,
    *,
    source_kind: str = "official",
    method: str | None = None,
    tolerance: str = "Utilizar únicamente con la familia y el tipo de sonda indicados.",
) -> dict[str, Any]:
    return {
        "id": dataset_id,
        "name": name,
        "dataset_type": "sensor_curve",
        "variable_name": "Temperatura",
        "variable_unit": "°C",
        "value_name": "Resistencia",
        "value_unit": "kΩ",
        "tolerance_text": tolerance,
        "source_kind": source_kind,
        "calculation_method": method,
        "review_status": "reviewed",
        "notes": "Valores calculados se identifican expresamente y no se presentan como tabla literal del fabricante.",
        "visible": 1,
        "points": [
            {
                "variable_value": temp,
                "value_min": None,
                "value_nominal": resistance,
                "value_max": None,
                "value_text": None,
                "sort_order": order,
                "notes": None,
            }
            for order, (temp, resistance) in enumerate(points)
        ],
        "sources": [source(ref, page, name)],
    }


def diagnostic_profile(title: str, code: str) -> tuple[list[str], list[str]]:
    norm = normalize(f"{code} {title}")
    if any(word in norm for word in ("COMUNIC", "TRANSMISION", "RECEPCION", "ADDRESS", "DIRECCION")):
        return (
            [
                "Cable de comunicación abierto, cruzado, derivado o con ruido",
                "Dirección duplicada, Main/Sub incorrecto o autoasignación incompleta",
                "Falta de alimentación o avería en la placa que debe transmitir",
            ],
            [
                "Identificar qué unidad muestra el código y cuál dejó de responder",
                "Con la alimentación cortada, revisar continuidad, topología y terminadores aplicables",
                "Confirmar direcciones y reiniciar la asignación solo después de corregir la red",
            ],
        )
    if any(word in norm for word in ("SONDA", "SENSOR", "THERMISTOR", "TEMPERATURA")):
        return (
            [
                "Sonda abierta, cortocircuitada, desprendida o fuera de curva",
                "Conector, cableado o contacto térmico defectuoso",
                "Circuito de lectura de la placa o asignación de sensor incorrecta",
            ],
            [
                "Medir la sonda desconectada y compararla con la tabla de su familia",
                "Comparar temperatura real con Sensor info/Service Tool antes de sustituir",
                "Revisar fijación, conector y continuidad hasta la placa",
            ],
        )
    if any(word in norm for word in ("FLOTADOR", "BOYA", "DRENAJE", "BOMBA", "AGUA")):
        return (
            [
                "Nivel de agua alto, desagüe obstruido o pendiente incorrecta",
                "Boya bloqueada, contacto/cableado defectuoso o conector suelto",
                "Bomba de drenaje o salida de la placa interior defectuosa",
            ],
            [
                "Comprobar primero si existe agua real en la bandeja",
                "Accionar la boya y verificar continuidad sin confundirla con una boya atascada",
                "Forzar la bomba desde servicio y comprobar caudal, tensión y parada retardada",
            ],
        )
    if any(word in norm for word in ("PRESION", "REFRIGER", "CICLO", "VALVULA", "DESCARGA")):
        return (
            [
                "Carga de refrigerante incorrecta, restricción o válvula que no actúa",
                "Intercambiador sucio, caudal de aire insuficiente o ventilador defectuoso",
                "Sensor/presostato, cableado o placa de control defectuosos",
            ],
            [
                "Registrar presiones y temperaturas reales antes de rearmar",
                "Comprobar caudal, filtros, ventiladores, EEV y válvula de cuatro vías",
                "Comparar la medida con el valor leído por la electrónica y el umbral documentado",
            ],
        )
    if any(word in norm for word in ("COMPRESOR", "CORRIENTE", "INVERTER", "PAM", "HIC", "IPM", "FAN", "VENTILADOR")):
        return (
            [
                "Motor/compresor bloqueado, bobinado o aislamiento defectuoso",
                "Alimentación, fase, tensión DC o conexión de potencia anormal",
                "Driver, CT, Hall, HIC/IPM o placa principal defectuosos",
            ],
            [
                "Cortar tensión y comprobar giro, bobinados, aislamiento y conectores",
                "Medir alimentación y corriente respetando los tiempos de detección del código",
                "Separar fallo del motor de fallo del driver con el procedimiento del manual",
            ],
        )
    if any(word in norm for word in ("EEPROM", "PCB", "PLACA", "MEMORIA")):
        return (
            [
                "Datos de capacidad/dirección no transferidos o ajuste de EEPROM incorrecto",
                "Conector, alimentación o comunicación interna de la placa",
                "PCB o memoria no volátil defectuosa",
            ],
            [
                "Anotar ajustes y direcciones antes de sustituir la placa",
                "Confirmar alimentación, conectores y referencia de la PCB",
                "Restaurar parámetros, direccionar y ejecutar la puesta en marcha indicada",
            ],
        )
    return (
        [
            "Condición o componente indicado por el código",
            "Cableado, conector, alimentación o configuración incorrectos",
            "Placa de control defectuosa tras descartar la instalación y el componente",
        ],
        [
            "Confirmar familia, unidad y forma exacta de indicación",
            "Aplicar las comprobaciones de la página citada en el orden indicado",
            "Corregir la causa y verificar con Test Run sin puentear protecciones",
        ],
    )


def behavior_for(scope: str, title: str) -> str:
    norm = normalize(title)
    if "SIN AVERIA" in norm or "NORMAL" in norm:
        return "Es una indicación normal; la máquina mantiene la secuencia correspondiente y no debe tratarse como avería."
    if scope == "controller":
        return "El mando afectado pierde total o parcialmente el control; las demás unidades dependen del esquema de grupo."
    if scope == "indoor":
        return "La unidad interior afectada entra en protección; otras interiores pueden continuar si la arquitectura lo permite."
    if scope == "outdoor":
        return "La unidad exterior limita o detiene compresor/actuador hasta recuperar una condición válida."
    return "La puesta en marcha o el circuito frigorífico queda limitado o detenido mientras persiste la condición."


def spec(
    code: str,
    title: str,
    scope: str,
    ref: str,
    page: str,
    *,
    description: str = "",
    behavior: str = "",
    aliases: tuple[str, ...] = (),
    causes: list[str] | None = None,
    checks: list[str] | None = None,
    dataset: str | None = None,
) -> dict[str, Any]:
    inferred_causes, inferred_checks = diagnostic_profile(title, code)
    return {
        "code": code,
        "title": title,
        "scope": scope,
        "ref": ref,
        "page": page,
        "description": description or f"Interpretación documentada de {code}: {title.lower()}.",
        "behavior": behavior or behavior_for(scope, title),
        "aliases": list(aliases),
        "causes": causes or inferred_causes,
        "checks": checks or inferred_checks,
        "dataset": dataset,
    }


RAC_ROWS = [
    ("H00", "Sin anomalía memorizada", "system"),
    ("H11", "Fallo de comunicación interior–exterior", "system"),
    ("H12", "Capacidad interior/exterior incompatible", "system"),
    ("H14", "Sonda de aire interior", "indoor"),
    ("H15", "Sonda de temperatura del compresor exterior", "outdoor"),
    ("H16", "Transformador de corriente exterior anormal", "outdoor"),
    ("H19", "Motor del ventilador interior bloqueado", "indoor"),
    ("H21", "Interruptor de flotador interior activado", "indoor"),
    ("H23", "Sonda del intercambiador interior n.º 1", "indoor"),
    ("H27", "Sonda de aire exterior", "outdoor"),
    ("H28", "Sonda del intercambiador exterior n.º 1", "outdoor"),
    ("H30", "Sonda de descarga exterior", "outdoor"),
    ("H32", "Sonda del intercambiador exterior n.º 2", "outdoor"),
    ("H33", "Tensión interior/exterior incompatible", "system"),
    ("H34", "Sonda del disipador exterior", "outdoor"),
    ("H36", "Sonda de tubería de gas exterior", "outdoor"),
    ("H37", "Sonda de tubería de líquido exterior", "outdoor"),
    ("H38", "Incompatibilidad entre unidades interior y exterior", "system"),
    ("H39", "Unidad interior anormal o en espera", "indoor"),
    ("H41", "Cableado o tuberías cruzados", "system"),
    ("H50", "Motor de ventilación anormal", "indoor"),
    ("H51", "Motor de ventilación bloqueado", "indoor"),
    ("H52", "Final de carrera anormal", "indoor"),
    ("H59", "Sensor Eco Patrol anormal", "indoor"),
    ("H64", "Sensor de alta presión exterior", "outdoor"),
    ("H67", "Generador nanoe anormal", "indoor"),
    ("H70", "Sensor de luz anormal", "indoor"),
    ("H97", "Motor del ventilador exterior bloqueado", "outdoor"),
    ("H98", "Protección por alta presión interior", "indoor"),
    ("H99", "Protección antihielo del intercambiador interior", "indoor"),
    ("F11", "Conmutación de la válvula de cuatro vías", "outdoor"),
    ("F16", "Protección de corriente total", "outdoor"),
    ("F17", "Protección antihielo de interior en espera", "indoor"),
    ("F18", "Bloqueo de circuito seco", "indoor"),
    ("F90", "Circuito PFC o alimentación de potencia", "outdoor"),
    ("F91", "Ciclo frigorífico anormal", "system"),
    ("F93", "Rotación anormal del compresor", "outdoor"),
    ("F94", "Protección por presión de descarga", "outdoor"),
    ("F95", "Protección de alta presión en refrigeración", "outdoor"),
    ("F96", "Sobretemperatura del módulo de potencia", "outdoor"),
    ("F97", "Sobretemperatura del compresor", "outdoor"),
    ("F98", "Protección por corriente total", "outdoor"),
    ("F99", "Detección de pico de corriente DC", "outdoor"),
]


ECOI_ROWS = [
    ("E01", "El mando no recibe respuesta de la unidad interior", "controller", "1"),
    ("E02", "Fallo de transmisión desde el mando", "controller", "1"),
    ("E03", "La unidad interior no recibe señal del mando o control central", "indoor", "1"),
    ("E04", "La unidad interior no recibe señal de la exterior", "system", "1"),
    ("E06", "La unidad exterior no recibe señal de las interiores", "system", "1"),
    ("E08", "Dirección de unidad interior duplicada", "network", "1"),
    ("E09", "Dirección de mando duplicada / dos mandos Main", "controller", "1"),
    ("E12", "Auto-address iniciado simultáneamente en otra exterior", "network", "1"),
    ("E15", "Auto-address impedido o dirección no asignada", "network", "1"),
    ("E16", "Número configurado de interiores mayor que el detectado", "network", "1"),
    ("E18", "Exterior principal sin señal de una exterior secundaria", "network", "1"),
    ("E20", "Interiores sin respuesta durante auto-address", "network", "1"),
    ("E24", "Una exterior no recibe comunicación de las interiores", "network", "1"),
    ("E25", "Dirección de exterior duplicada o comunicación perdida tras asignar", "network", "1"),
    ("E26", "Número de unidades exteriores no coincide con la configuración", "network", "1"),
    ("E29", "Exterior Main sin comunicación con otra exterior", "network", "1"),
    ("E30", "Comunicación serie de unidad exterior", "outdoor", "1"),
    ("E31", "Comunicación entre microprocesadores o placas exteriores", "outdoor", "1"),
    ("F01", "Sonda de intercambiador interior E1", "indoor", "1"),
    ("F02", "Sonda de intercambiador interior E2", "indoor", "1"),
    ("F03", "Sonda de intercambiador interior E3", "indoor", "2"),
    ("F04", "Sonda de descarga del compresor 1", "outdoor", "2"),
    ("F05", "Sonda de descarga del compresor 2", "outdoor", "2"),
    ("F06", "Sonda de gas del intercambiador exterior 1", "outdoor", "2"),
    ("F07", "Sonda de líquido del intercambiador exterior 1", "outdoor", "2"),
    ("F08", "Sonda de aire exterior", "outdoor", "2"),
    ("F10", "Sonda de aire de retorno interior", "indoor", "2"),
    ("F11", "Sonda de aire de impulsión interior", "indoor", "2"),
    ("F12", "Sonda de aspiración del compresor", "outdoor", "2"),
    ("F16", "Sensor o presostato de alta presión", "outdoor", "2"),
    ("F17", "Sensor de baja presión abierto o cortocircuitado", "outdoor", "2"),
    ("F22", "Sonda de descarga del compresor 3", "outdoor", "2"),
    ("F23", "Sonda de gas del intercambiador exterior 3", "outdoor", "3"),
    ("F24", "Sonda de líquido del intercambiador exterior 2", "outdoor", "3"),
    ("F25", "Sonda de gas del intercambiador exterior 3 — sistema 3 tubos", "outdoor", "3"),
    ("F26", "Sonda de líquido del intercambiador exterior 3 — sistema 3 tubos", "outdoor", "3"),
    ("F29", "EEPROM de la unidad interior", "indoor", "3"),
    ("F31", "EEPROM de la unidad exterior", "outdoor", "3"),
    ("H01", "Protección de corriente del compresor 1", "outdoor", "3"),
    ("H02", "Protección PAM del compresor 1", "outdoor", "3"),
    ("H03", "Sensor CT del compresor 1 abierto o cortocircuitado", "outdoor", "3"),
    ("H04", "Dirección de unidad exterior duplicada", "network", "3"),
    ("H05", "Sonda de descarga del compresor 1 sin variación válida", "outdoor", "3"),
    ("H06", "Baja presión inferior a 0,05 MPa durante más de 2 minutos", "outdoor", "3"),
    ("H07", "Nivel de aceite insuficiente — sistema 3 tubos", "outdoor", "3"),
    ("H08", "Sensor de aceite del compresor 1", "outdoor", "3"),
    ("H10", "Capacidad de unidad exterior sin ajustar o incorrecta", "outdoor", "3"),
    ("H11", "Compresor 2: corriente superior a 12 A durante 30 segundos", "outdoor", "3"),
    ("H12", "Compresor 2 bloqueado: corriente superior a 14 A durante 4 segundos", "outdoor", "4"),
    ("H13", "Sensor CT del compresor 2", "outdoor", "4"),
    ("H15", "Sonda de descarga del compresor 2 sin variación válida", "outdoor", "4"),
    ("H21", "Compresor 3: corriente superior a 12 A durante 30 segundos", "outdoor", "4"),
    ("H22", "Compresor 3 bloqueado: corriente superior a 14 A durante 4 segundos", "outdoor", "4"),
    ("H23", "Sensor CT del compresor 3", "outdoor", "4"),
    ("H25", "Sonda de descarga del compresor 3 sin variación válida", "outdoor", "4"),
    ("H27", "Sensor de aceite del compresor 2", "outdoor", "4"),
    ("H28", "Sensor de aceite del compresor 3", "outdoor", "4"),
    ("H31", "Alarma HIC / circuito inverter", "outdoor", "4"),
    ("L02", "Interior Main de grupo no conectada a la exterior", "network", "4"),
    ("L03", "Dirección Main duplicada en el grupo", "network", "4"),
    ("L04", "Dirección interior ausente o incorrecta", "network", "4"),
    ("L05", "Más de dos mandos con prioridad en un circuito", "controller", "4"),
    ("L06", "Más de dos mandos sin prioridad definida", "controller", "4"),
    ("L07", "Cableado de control de grupo conectado a control individual", "controller", "5"),
    ("L08", "Dirección de unidad interior no configurada", "network", "5"),
    ("L09", "Código de capacidad interior no configurado", "indoor", "5"),
    ("L10", "Capacidad de unidad exterior no configurada o a cero", "outdoor", "5"),
    ("L11", "Cableado incorrecto del grupo — sistema 3 tubos", "network", "5"),
    ("L17", "Modelos de unidades exteriores incompatibles", "system", "5"),
    ("L18", "Funcionamiento anormal de la válvula de cuatro vías", "outdoor", "5"),
    ("P01", "Protección térmica del ventilador interior", "indoor", "5"),
    ("P02", "Tensión de alimentación fuera de 160–260 V o corriente no detectada", "outdoor", "5"),
    ("P03", "Temperatura de descarga del compresor 1 superior a 106 °C", "outdoor", "5"),
    ("P04", "Alta presión: activa sobre 3,3 MPa y libera bajo 2,6 MPa", "outdoor", "5"),
    ("P05", "Fase ausente o secuencia de fases incorrecta", "outdoor", "5"),
    ("P09", "Cableado incorrecto del panel de techo", "indoor", "5"),
    ("P10", "Interruptor de flotador activado", "indoor", "5"),
    ("P12", "Protección inverter del motor del ventilador interior", "indoor", "5"),
    ("P13", "Válvulas de gas y líquido cerradas o circuito frigorífico bloqueado", "system", "5"),
    ("P14", "Entrada EXCT / sensor O₂ activado", "indoor", "5"),
    ("P16", "Sobrecorriente del compresor inverter 1", "outdoor", "5"),
    ("P17", "Temperatura de descarga del compresor 2 superior a 106 °C", "outdoor", "5"),
    ("P18", "Temperatura de descarga del compresor 3 superior a 106 °C", "outdoor", "6"),
    ("P20", "Alarma de carga elevada — sistema 2 tubos", "system", "6"),
    ("P22", "Motor de ventilador exterior o señal Hall", "outdoor", "6"),
    ("P26", "Sobrecorriente a alta frecuencia del compresor inverter", "outdoor", "6"),
    ("P29", "Fase de compresor perdida o rotor bloqueado", "outdoor", "6"),
    ("C05", "Configuración de transmisión con control de sistema", "controller", "6"),
    ("C06", "Comunicación serie con control central", "controller", "6"),
    ("P30", "Protección en una subunidad del grupo", "indoor", "6"),
]

ECOI_3WAY_ROWS = [
    ("E06", "ECOi 3 tubos — exterior sin comunicación serie de las interiores", "system", "5-9"),
    ("E12", "ECOi 3 tubos — inicio de auto-address prohibido", "network", "5-9"),
    ("E15", "ECOi 3 tubos — auto-address detecta menos interiores de las configuradas", "network", "5-9"),
    ("E16", "ECOi 3 tubos — auto-address detecta más interiores de las configuradas", "network", "5-10"),
    ("E20", "ECOi 3 tubos — ninguna interior reconocida durante auto-address", "network", "5-10"),
    ("E24", "ECOi 3 tubos — exterior inverter sin comunicación de otra exterior", "network", "5-11"),
    ("E25", "ECOi 3 tubos — dirección de exterior duplicada", "network", "5-11"),
    ("E26", "ECOi 3 tubos — cantidad de exteriores no coincide con la configuración", "network", "5-11"),
    ("E29", "ECOi 3 tubos — secundaria sin comunicación de la exterior Main durante 3 min", "network", "5-11"),
    ("F04", "ECOi 3 tubos — sonda de descarga del compresor inverter 1", "outdoor", "5-12"),
    ("F05", "ECOi 3 tubos — sonda de descarga del compresor 2", "outdoor", "5-12"),
    ("F22", "ECOi 3 tubos — sonda de descarga del compresor 3", "outdoor", "5-12"),
    ("F06", "ECOi 3 tubos — sonda de gas del intercambiador exterior 1", "outdoor", "5-13"),
    ("F23", "ECOi 3 tubos — sonda de gas del intercambiador exterior 2", "outdoor", "5-13"),
    ("F25", "ECOi 3 tubos — sonda de gas del intercambiador exterior 3", "outdoor", "5-13"),
    ("F07", "ECOi 3 tubos — sonda de líquido del intercambiador exterior 1", "outdoor", "5-13"),
    ("F24", "ECOi 3 tubos — sonda de líquido del intercambiador exterior 2", "outdoor", "5-13"),
    ("F26", "ECOi 3 tubos — sonda de líquido del intercambiador exterior 3", "outdoor", "5-13"),
    ("F08", "ECOi 3 tubos — sonda de aire exterior", "outdoor", "5-14"),
    ("F12", "ECOi 3 tubos — sonda de aspiración del compresor", "outdoor", "5-14"),
    ("F16", "ECOi 3 tubos — incoherencia entre sensor y presostato de alta", "outdoor", "5-15"),
    ("F17", "ECOi 3 tubos — sensor de baja abierto o cortocircuitado", "outdoor", "5-16"),
    ("H11", "ECOi 3 tubos — sobrecorriente del compresor 2", "outdoor", "5-17"),
    ("H12", "ECOi 3 tubos — corriente de bloqueo del compresor 2", "outdoor", "5-17"),
    ("H21", "ECOi 3 tubos — sobrecorriente del compresor 3", "outdoor", "5-17"),
    ("H22", "ECOi 3 tubos — corriente de bloqueo del compresor 3", "outdoor", "5-17"),
    ("H05", "ECOi 3 tubos — sonda de descarga del compresor 1 desprendida", "outdoor", "5-18"),
    ("H15", "ECOi 3 tubos — sonda de descarga del compresor 2 desprendida", "outdoor", "5-18"),
    ("H25", "ECOi 3 tubos — sonda de descarga del compresor 3 desprendida", "outdoor", "5-18"),
    ("H06", "ECOi 3 tubos — presostato de baja activado", "outdoor", "5-19"),
    ("H07", "ECOi 3 tubos — no se detecta retorno de aceite", "outdoor", "5-20"),
    ("L04", "ECOi 3 tubos — dirección de sistema exterior duplicada", "network", "5-21"),
    ("L11", "ECOi 3 tubos — kit de solenoides común o grupo de mandos mal cableado", "network", "5-22"),
    ("L10", "ECOi 3 tubos — capacidad exterior EEPROM sin configurar", "outdoor", "5-22"),
    ("L17", "ECOi 3 tubos — exterior incompatible o tipo de refrigerante EEPROM incorrecto", "system", "5-23"),
    ("P03", "ECOi 3 tubos — descarga alta del compresor inverter 1", "outdoor", "5-24"),
    ("P17", "ECOi 3 tubos — descarga alta del compresor 2", "outdoor", "5-24"),
    ("P18", "ECOi 3 tubos — descarga alta del compresor 3", "outdoor", "5-24"),
    ("P04", "ECOi 3 tubos — presostato de alta activado a 3,3 MPa", "outdoor", "5-25"),
    ("P22", "ECOi 3 tubos — fallo de arranque o señal Hall del ventilador exterior", "outdoor", "5-26"),
    ("CHECK", "ECOi 3 tubos — inspección parpadeante por funcionamiento de respaldo", "system", "5-27"),
]


def build_errors() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    specs: list[dict[str, Any]] = []

    rac_behaviors = {
        "H00": "No existe una anomalía memorizada; la unidad puede funcionar normalmente.",
        "H11": "Tras aproximadamente un minuto sin comunicación, la unidad entra en protección; en determinadas pruebas forzadas puede mantenerse solo el ventilador interior.",
        "H12": "La combinación queda bloqueada después de verificar la capacidad conectada; corrija la incompatibilidad antes de rearmar.",
        "H21": "La unidad interior afectada detiene la producción; compruebe bandeja, bomba y boya antes de restablecer.",
        "H39": "La interior indicada permanece en espera; en multisplit otras interiores con demanda compatible pueden continuar.",
        "H41": "La unidad detiene la puesta en marcha para evitar trabajar con tuberías o cableado asignados a otra conexión.",
        "H97": "La exterior reintenta; si el bloqueo del ventilador se repite dos veces dentro de 30 minutos memoriza la avería.",
        "H98": "El compresor reduce frecuencia o se detiene para limitar la presión interior; reintenta cuando baja la temperatura del intercambiador.",
        "H99": "El compresor reduce frecuencia o se detiene para evitar congelación; reintenta al recuperar temperatura.",
        "F17": "La interior en espera se protege frente a congelación; no implica necesariamente que todas las interiores se detengan.",
        "F91": "El sistema detiene o limita el compresor al no confirmar un ciclo frigorífico normal.",
        "F95": "El compresor se detiene por alta presión en frío y puede reintentar después del retardo de protección.",
        "F96": "La electrónica reduce frecuencia o detiene el compresor hasta enfriar el módulo.",
        "F97": "La unidad detiene el compresor y espera a que descienda la temperatura de descarga/carcasa.",
        "F99": "El inverter corta inmediatamente el compresor ante el pico DC y controla la repetición antes de bloquear.",
    }
    sensor_dataset = {
        "H14": "15k",
        "H23": "20k",
        "H27": "15k",
        "H28": "20k",
        "H30": "old_discharge",
        "H32": "20k",
        "H36": "20k",
        "H37": "20k",
    }
    for code, title, scope in RAC_ROWS:
        specs.append(spec(
            code,
            f"RAC/split — {title}",
            scope,
            "RAC_PKE",
            "108",
            description=f"Código {code} leído mediante CHECK en una familia RAC/split Panasonic.",
            behavior=rac_behaviors.get(code, ""),
            aliases=(f"{code} TIMER",),
            dataset=sensor_dataset.get(code),
        ))

    multi_overrides = [
        spec(
            "H11",
            "Multisplit — comunicación interior/exterior ausente durante 1 minuto",
            "system",
            "MULTI_4E",
            "76",
            behavior="La unidad interior afectada no obtiene funcionamiento frigorífico; el manual permite confirmar con marcha forzada y observar si queda solo el ventilador interior.",
        ),
        spec(
            "H12",
            "Multisplit — suma de capacidades incompatible",
            "system",
            "MULTI_4E",
            "78",
            behavior="El conjunto impide el arranque aproximadamente 90 segundos después de alimentar mientras la combinación sea inválida.",
        ),
        spec(
            "H64",
            "Multisplit — sensor de alta presión abierto durante parada",
            "outdoor",
            "MULTI_4E",
            "88",
            description="La placa comprueba la entrada del sensor de alta presión incluso con el sistema parado.",
            behavior="La exterior bloquea la puesta en marcha si la señal permanece abierta durante aproximadamente un minuto.",
        ),
        spec(
            "H97",
            "Multisplit — ventilador exterior bloqueado dos veces en 30 minutos",
            "outdoor",
            "MULTI_4E",
            "92",
            behavior="La exterior reintenta tras el primer bloqueo y memoriza H97 si se repite dos veces dentro de 30 minutos.",
        ),
    ]
    specs.extend(multi_overrides)

    for code, title, scope, page in ECOI_ROWS:
        behavior = ""
        if code in {"E12", "E15", "E16", "E20", "E24", "E25", "E26", "E29", "H04", "L02", "L03", "L04", "L08"}:
            behavior = "La puesta en marcha, autoasignación o comunicación del circuito queda bloqueada; no repetir auto-address hasta corregir topología y direcciones."
        elif code in {"P10", "P12", "P30"}:
            behavior = "Se protege la unidad interior implicada; otras interiores pueden continuar cuando la categoría de alarma y la arquitectura ECOi lo permiten."
        elif code in {"H11", "H12", "H21", "H22", "P03", "P04", "P16", "P17", "P18", "P26", "P29"}:
            behavior = "La unidad exterior detiene el compresor afectado; el funcionamiento de respaldo depende del número de módulos/compresores y de la alarma concreta."
        specs.append(spec(
            code,
            f"ECOi/VRF — {title}",
            scope,
            "ECOI_CODES",
            page,
            description=f"Interpretación ECOi/VRF del código {code}; no mezclar con el significado RAC del mismo código.",
            behavior=behavior,
        ))

    backup_codes = {"H11", "H12", "H21", "H22", "H31", "P16", "P22", "P26", "P29"}
    for code, title, scope, page in ECOI_3WAY_ROWS:
        behavior = ""
        causes = None
        checks = None
        if code in backup_codes:
            behavior = (
                "El sistema ECOi 3 tubos puede continuar en respaldo automático cuando la arquitectura "
                "dispone de compresores/módulos sanos. CHECK parpadea; repare la causa y restablezca "
                "la alimentación de todas las exteriores para cancelar el respaldo."
            )
        elif code == "CHECK":
            behavior = (
                "No es por sí solo un código de avería: indica que el sistema continúa en respaldo automático. "
                "Consulte el historial para localizar P16/P22/P26/P29/Hx1/Hx2/H31 u otra causa asociada."
            )
            causes = [
                "Compresor o ventilador exterior aislado por una alarma compatible con respaldo",
                "Contactor de compresor pegado detectado por la lógica de inspección",
                "Respaldo manual aún activo después de una reparación",
            ]
            checks = [
                "Consultar el historial de exterior con el mando de mantenimiento",
                "Identificar qué exterior/compresor está aislado antes de intervenir",
                "Tras reparar, restablecer la alimentación de todas las exteriores para cancelar el modo",
            ]
        elif code in {"E12", "E15", "E16", "E20", "E24", "E25", "E26", "E29", "L04", "L11"}:
            behavior = "La puesta en marcha o comunicación del circuito queda bloqueada hasta corregir cantidad, dirección o cableado."
        specs.append(spec(
            code,
            title,
            scope,
            "ECOI_3WAY",
            page,
            description=f"Interpretación específica del sistema ECOi 3 tubos para {code}.",
            behavior=behavior,
            aliases=(f"{code} 3 WAY", f"{code} MF1"),
            causes=causes,
            checks=checks,
        ))

    specs.extend([
        spec(
            "P10",
            "PACi cassette/conductos — fallo de drenaje o boya",
            "indoor",
            "PACI_HIGH",
            "142",
            description="Protección de agua asociada a bomba, desagüe, boya y su cableado.",
            behavior="La interior detiene la producción y mantiene la estrategia de drenaje; el rearme solo debe realizarse después de vaciar y corregir la causa.",
            aliases=("P10 DRAIN", "P10 FLOAT"),
        ),
        spec(
            "P11",
            "PACi vertical — nivel de agua elevado o bomba de drenaje",
            "indoor",
            "PACI_HIGH",
            "143",
            behavior="La unidad interior vertical se protege por nivel alto; las demás unidades dependen del esquema de grupo.",
            aliases=("P11 HIGH WATER",),
        ),
        spec(
            "P12",
            "PACi — bomba de drenaje bloqueada o protección de ventilador según familia",
            "indoor",
            "PACI_HIGH",
            "144",
            behavior="La unidad afectada detiene el actuador protegido; confirme la familia porque P12 no identifica el mismo componente en todas las interiores.",
            aliases=("P12 DRAIN PUMP", "P12 FAN"),
        ),
        spec(
            "J07",
            "R32 — fallo de válvula de corte de seguridad o su cableado",
            "system",
            "VRF_MS3",
            "84",
            behavior="El circuito permanece bloqueado por seguridad; no rearmar la válvula hasta ventilar la zona y eliminar la causa.",
        ),
        spec(
            "J08",
            "R32 — incoherencia en el circuito de válvula de corte",
            "system",
            "VRF_MS3",
            "84",
            behavior="El circuito permanece bloqueado por seguridad; no forzar la apertura ni puentear la detección.",
        ),
    ])

    by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    interpretation_id = 0
    for row in specs:
        interpretation_id += 1
        item_id = interpretation_id * 100
        info_items: list[dict[str, Any]] = []

        def add(kind: str, body: str) -> None:
            nonlocal item_id
            item_id += 1
            info_items.append({
                "id": item_id,
                "item_type": kind,
                "title": None,
                "body": body,
                "sort_order": len(info_items) + 1,
                "review_status": "reviewed",
                "origin_ref": SOURCES[row["ref"]]["document_ref"],
            })

        add("machine_behavior", row["behavior"])
        add("related_element", row["title"])
        for value in row["causes"]:
            add("cause", value)
        for value in row["checks"]:
            add("check", value)
        add(
            "observation",
            f"Confirme familia, unidad y método de lectura. Fuente: {SOURCES[row['ref']]['document_ref']}, página {row['page']}.",
        )

        datasets: list[dict[str, Any]] = []
        if row["dataset"] == "15k":
            datasets.append(curve_dataset(
                interpretation_id * 10 + 1,
                "NTC 15 kΩ a 25 °C, Beta 3950",
                NTC_15K_B3950,
                "CASSETTE",
                "21",
                source_kind="calculated",
                method="Ecuación Beta con R25=15 kΩ y B=3950 K, ambos datos oficiales.",
            ))
        elif row["dataset"] == "20k":
            datasets.append(curve_dataset(
                interpretation_id * 10 + 1,
                "NTC 20 kΩ a 25 °C, Beta 3950",
                NTC_20K_B3950,
                "CASSETTE",
                "21",
                source_kind="calculated",
                method="Ecuación Beta con R25=20 kΩ y B=3950 K, ambos datos oficiales.",
            ))
        elif row["dataset"] == "old_discharge":
            datasets.append(curve_dataset(
                interpretation_id * 10 + 1,
                "Sonda de descarga PACi antigua",
                OLD_PACI_DISCHARGE,
                "OLD_PACI",
                "91",
                tolerance="±7 % en la zona indicada por la tabla oficial.",
            ))

        by_code[row["code"]].append({
            "id": interpretation_id,
            "title": row["title"],
            "description": row["description"],
            "source_kind": "official",
            "confidence": "high",
            "review_status": "reviewed",
            "info_items": info_items,
            "operational_impacts": [operational_impact(row["behavior"], row["scope"])],
            "datasets": datasets,
            "sources": [source(row["ref"], row["page"], f"{row['code']} — {row['title']}")],
            "_scope": row["scope"],
            "_aliases": row["aliases"],
        })

    indexes: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    for error_id, code in enumerate(sorted(by_code, key=normalize), 1):
        interpretations = by_code[code]
        scopes = {item.pop("_scope") for item in interpretations}
        aliases = {code}
        for item in interpretations:
            aliases.update(item.pop("_aliases"))
        alias_rows = [
            {"alias_display": alias, "alias_normalized": normalize(alias).replace(" ", "")}
            for alias in sorted(aliases, key=normalize)
        ]
        label = (
            interpretations[0]["title"]
            if len(interpretations) == 1
            else f"{len(interpretations)} interpretaciones documentadas"
        )
        blob = " ".join(
            [code, label]
            + [alias["alias_display"] for alias in alias_rows]
            + [
                " ".join(
                    [interpretation["title"], interpretation["description"]]
                    + [item["body"] for item in interpretation["info_items"]]
                )
                for interpretation in interpretations
            ]
        )
        index = {
            "id": error_id,
            "code_display": code,
            "code_normalized": normalize(code).replace(" ", ""),
            "indication_type": "controller_display_led_or_wireless_check",
            "unit_scope": next(iter(scopes)) if len(scopes) == 1 else "system",
            "short_label": label,
            "interpretation_count": len(interpretations),
            "search_text": normalize(blob),
        }
        detail = {
            **{key: value for key, value in index.items() if key not in {"interpretation_count", "search_text"}},
            "aliases": alias_rows,
            "tags": sorted({token.lower() for token in normalize(blob).split() if len(token) > 4})[:24],
            "interpretations": interpretations,
            "media": [],
        }
        indexes.append(index)
        details.append(detail)
    return indexes, details


def section(kind: str, title: str, body: str, opened: bool = False) -> dict[str, Any]:
    return {
        "section_type": kind,
        "title": title,
        "body": body,
        "collapsed_default": 0 if opened else 1,
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


def controller(
    family: str,
    wires: str,
    polarity: str,
    voltage: str | None,
    terminals: str,
    startup: str,
    notes: str,
    cable_spec: str,
) -> dict[str, Any]:
    return {
        "interface_type": "mando cableado",
        "controller_family": family,
        "wire_count": wires,
        "polarity": polarity,
        "nominal_voltage": voltage,
        "terminals": terminals,
        "cable_colors": None,
        "cable_spec": cable_spec,
        "startup_behavior": startup,
        "maximum_scope": "Hasta 8 interiores y 2 mandos cuando lo admite la interfaz CZ-RTC6.",
        "notes": notes,
    }


def option(value: str, label: str, effect: str, factory: bool = False) -> dict[str, Any]:
    return {
        "option_value": value,
        "option_label": label,
        "effect": effect,
        "is_factory": factory,
    }


def parameter(
    code: str,
    name: str,
    description: str,
    options: list[dict[str, Any]],
    factory: str | None = None,
    dependencies: str | None = None,
    warnings: str | None = None,
) -> dict[str, Any]:
    return {
        "parameter_code": code,
        "name": name,
        "description": description,
        "factory_value": factory,
        "dependencies": dependencies,
        "warnings": warnings,
        "options": options,
    }


TOPIC_DEFS = [
    (1, "diagnostic_access", "wireless-check", "Lectura inalámbrica y por indicadores", "CHECK, TIMER, pitidos y LED de panel."),
    (2, "diagnostic_access", "wired-service-check", "Lectura desde CZ-RTC2, CZ-RTC5 y CZ-RTC6", "Código, unidad, historial y subinformación."),
    (3, "diagnostic_access", "outdoor-display", "Display y LED de placa exterior", "Decodificación M/N, grupo de alarma y dirección."),
    (4, "history_reset", "history-clear", "Historial, borrado y rearme", "Qué se borra, qué se conserva y cuándo cortar tensión."),
    (5, "controllers_buses", "controller-wiring", "Mandos cableados y alimentación", "R1/R2, 16 VDC, Main/Sub y límites de cable."),
    (6, "controllers_buses", "communication-buses", "Diagnóstico de comunicación", "S-LINK, RAC, terminadores, resistencia y ruido."),
    (7, "controllers_buses", "controller-startup", "Arranque y fallos propios del mando", "Assigning, códigos C/E y adquisición de datos."),
    (8, "service_modes", "test-run", "Test Run desde mando y placa", "Frío/calor, 60 minutos y protecciones activas."),
    (9, "service_modes", "pump-down", "Pump down y recuperación de refrigerante", "Límites split, multisplit, PACi y VRF."),
    (10, "service_modes", "forced-special", "Marcha forzada y funciones especiales", "Frío/calor, desescarche y prueba exterior."),
    (11, "drainage_overflow", "drainage", "Bomba, boya y desbordamiento", "P10/P11/P12, frío/calor y marcha posterior."),
    (12, "configuration", "controller-settings", "Programación desde mando", "Simple/Detailed settings, sensor y presión estática."),
    (13, "configuration", "outdoor-settings", "Programación de placa exterior", "DIP, selectores, capacidad y opciones de campo."),
    (14, "commissioning", "addressing", "Direccionamiento y puesta en marcha", "Auto-address, circuito frigorífico y verificación."),
    (15, "multisplit", "multi-operation", "Multisplit: combinaciones y funcionamiento", "Capacidad, tuberías, cableado y unidades no afectadas."),
    (16, "vrf_network", "vrf-impact", "ECOi/VRF: alcance de parada y respaldo", "Unidad, grupo, circuito y sistema completo."),
    (17, "component_checks", "sensors", "Sondas, presión y lectura en vivo", "NTC, transductores, curvas y Sensor info."),
    (18, "component_checks", "actuators", "EEV, ventiladores, bombas y compresor", "Resistencia, tensión, secuencia y seguridad."),
    (19, "technical_values", "quick-values", "Valores y umbrales de trabajo", "Resistencias, tensiones, presiones y tiempos."),
    (20, "normal_states", "normal-behavior", "Estados normales que parecen avería", "Retardos, desescarche, retorno de aceite y postdrenaje."),
    (21, "service_tools_boards", "service-tools", "Herramientas de servicio", "CONEX, H&C, Service Cloud y mando de mantenimiento."),
    (22, "service_tools_boards", "board-replacement", "Después de sustituir una placa", "EEPROM, capacidad, direcciones y validación."),
    (23, "system_architecture", "r32-safety", "Seguridad R32 y límites de intervención", "Válvulas de corte, recuperación y ventilación."),
    (24, "system_architecture", "recognize-family", "Cómo reconocer la familia técnica", "RAC, multisplit, PACi y ECOi/VRF sin depender del modelo."),
    (25, "errors", "using-error-codes", "Consultar errores y significados repetidos", "Cómo elegir entre interpretaciones RAC, PACi y ECOi/VRF."),
]


def tv(
    topic_id: int,
    title: str,
    recognition: str,
    purpose: str,
    summary: str,
    facts: tuple[str, ...],
    procedures: tuple[str, ...],
    ref: str,
    page: str,
    page_end: str | None = None,
    *,
    system_type: str = "Panasonic",
    unit_scope: str = "system",
    controller_profile: dict[str, Any] | None = None,
    parameters: list[dict[str, Any]] | None = None,
    monitoring: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "topic_id": topic_id,
        "title": title,
        "recognition": recognition,
        "purpose": purpose,
        "summary": summary,
        "facts": list(facts),
        "procedures": list(procedures),
        "ref": ref,
        "page": page,
        "page_end": page_end,
        "system_type": system_type,
        "unit_scope": unit_scope,
        "controller_profile": controller_profile,
        "parameters": parameters or [],
        "monitoring": monitoring or [],
    }


RTC6_PROFILE = controller(
    "CZ-RTC6 / CZ-RTC6W",
    "2",
    "sin polaridad",
    "16 VDC aprox. suministrados por la unidad interior",
    "R1–R2 / 1–2",
    "Muestra Assigning mientras adquiere direcciones; si parpadea más de 10 min debe revisarse la asignación.",
    "Máximo dos mandos por grupo; si hay dos, uno Main y otro Sub.",
    "0,75–1,25 mm²; 500 m totales, con un máximo de 200 m entre interiores.",
)
RTC5_PROFILE = controller(
    "CZ-RTC5 / CZ-RTC5B",
    "2",
    "sin polaridad en el bus compatible",
    "16 VDC suministrados por la unidad interior",
    "RC / R1–R2 según interior",
    "Espera durante la asignación antes de permitir control normal.",
    "La pantalla de alarma identifica la interior afectada; no todos los códigos admiten reinicio inmediato.",
    "Cable de mando independiente de potencia, según el manual de la unidad interior.",
)
RTC2_PROFILE = controller(
    "CZ-RTC2 y mandos ECOi de generación anterior",
    "2",
    "según placa/interfaz de la familia",
    "alimentado por la unidad interior",
    "RCU / remote controller",
    "La adquisición de dirección debe completarse antes de consultar sensores o alarmas.",
    "No aplicar la secuencia de CZ-RTC5/6: los botones y menús son diferentes.",
    "Cable de mando apantallado o especificado por el manual ECOi.",
)


TECH_VARIANTS = [
    tv(
        1,
        "Mando inalámbrico RAC — localizar el código con CHECK",
        "Mando de split con orificio/botón CHECK y teclas TIMER ▲/▼; la unidad interior dispone de receptor acústico.",
        "Leer el último código memorizado sin desmontar la unidad.",
        "CHECK durante 5 s muestra “--”; TIMER recorre H00 en adelante y la unidad confirma el código coincidente con pitido continuo.",
        (
            "Coincidencia: LED de alimentación encendido unos 30 s y pitido continuo durante 4 s.",
            "No coincidencia: LED 0,5 s y sin pitido; salir con CHECK 5 s o esperar 30 s.",
        ),
        (
            "Apunte primero qué unidad interior presenta TIMER intermitente.",
            "Mantenga CHECK 5 s hasta que el mando muestre “--”.",
            "Pulse TIMER ▲/▼ y espere la respuesta acústica en cada código.",
            "Anote código y unidad; salga manteniendo CHECK 5 s.",
        ),
        "RAC_PKE",
        "108",
        "109",
        system_type="RAC/split",
        unit_scope="indoor",
    ),
    tv(
        1,
        "RAC — distinguir coincidencia y código no almacenado",
        "Receptor interior con POWER/TIMER y confirmación acústica.",
        "Evitar aceptar como avería cualquier código recorrido por el mando.",
        "Solo el pitido continuo de 4 s identifica el código almacenado; los pitidos breves/no respuesta no son confirmación.",
        (
            "El mando transmite códigos aunque no estén memorizados.",
            "H00 significa que no hay anomalía registrada en la familia compatible.",
        ),
        (
            "Recorra despacio los códigos y espere la respuesta completa.",
            "Repita desde H00 si pasó por alto el pitido continuo.",
            "Confirme el significado en la familia RAC, no en la tabla ECOi.",
        ),
        "RAC_PKE",
        "108",
        "109",
        system_type="RAC/split",
        unit_scope="indoor",
    ),
    tv(
        1,
        "Unidad interior RAC — TIMER parpadea y conserva el último fallo",
        "Split mural con LED TIMER; no necesita display alfanumérico.",
        "Saber por qué el piloto continúa parpadeando después de un reintento.",
        "El controlador conserva el último código para recuperarlo con CHECK aunque la condición haya desaparecido.",
        (
            "Un rearme de alimentación no sustituye la reparación de la causa.",
            "La memoria debe leerse antes de borrarla para no perder el diagnóstico.",
        ),
        (
            "No corte tensión hasta recuperar el código cuando sea seguro esperar.",
            "Lea el código con CHECK y anote condiciones de funcionamiento.",
            "Borre únicamente después de corregir y verificar.",
        ),
        "RAC_JKE",
        "93",
        "94",
        system_type="RAC/split antiguo",
        unit_scope="indoor",
    ),
    tv(
        2,
        "CZ-RTC2 — monitor de sensores y selección de unidad",
        "Mando ECOi antiguo con botón CHECK y teclas de temperatura/unidad.",
        "Consultar sensores por dirección y separar lectura de alarma.",
        "La combinación de servicio abre el monitor; las teclas de temperatura recorren la dirección de sensor y UNIT selecciona la interior.",
        (
            "La dirección mostrada pertenece al dato monitorizado, no al código de alarma.",
            "CHECK permite salir del modo de servicio.",
        ),
        (
            "Mantenga la combinación indicada en el manual durante al menos 4 s.",
            "Seleccione la unidad con UNIT.",
            "Recorra identificadores con las teclas de temperatura y registre valor/unidad.",
            "Pulse CHECK para volver al control normal.",
        ),
        "ECOI_2PIPE",
        "161",
        "163",
        system_type="ECOi 2 tubos",
        unit_scope="controller",
        controller_profile=RTC2_PROFILE,
    ),
    tv(
        2,
        "CZ-RTC5B — Service check e identificación de la interior",
        "Mando rectangular con cinco teclas inferiores y menú Maintenance func.",
        "Leer alarma actual, historial y número de la unidad afectada.",
        "Service check muestra el código y la dirección/interior implicada; algunas alarmas transitorias admiten reinicio después de un minuto.",
        (
            "E04, E06, P10, P20 y H06 pueden ser transitorios, pero deben investigarse si se repiten.",
            "Otros códigos requieren detener y aislar alimentación antes de intervenir.",
        ),
        (
            "Abra Maintenance func desde la pantalla parada.",
            "Seleccione Service check / alarm history.",
            "Anote código, número de unidad y orden temporal.",
            "Salga sin borrar hasta terminar las comprobaciones.",
        ),
        "RTC5",
        "44",
        "45",
        unit_scope="controller",
        controller_profile=RTC5_PROFILE,
    ),
    tv(
        2,
        "CZ-RTC6 — últimas cuatro alarmas y Sensor info",
        "Mando compacto con MENU, flechas ▲/▼, ENTER y START/STOP.",
        "Consultar alarmas recientes y valores vivos desde el mismo mando.",
        "Service check conserva las cuatro alarmas recientes; Sensor info permite comparar la lectura electrónica con la medida real.",
        (
            "La lista de cuatro no equivale a un historial ilimitado.",
            "Borrar la lista elimina contexto diagnóstico, no corrige la causa.",
        ),
        (
            "Con la unidad parada, abra el menú de servicio.",
            "Entre en Service check y anote las cuatro posiciones.",
            "Abra Sensor info para comparar el elemento sospechoso.",
            "Salga sin modificar settings si solo está diagnosticando.",
        ),
        "RTC6_OPER",
        "18",
        "22",
        unit_scope="controller",
        controller_profile=RTC6_PROFILE,
    ),
    tv(
        2,
        "CZ-RTC6 — selección de unidad en un grupo",
        "Un solo mando controla varias interiores; la pantalla muestra un número de unidad.",
        "Atribuir el código o valor al equipo correcto.",
        "En un grupo, la misma alarma puede aparecer junto a la unidad que la originó; no sustituya el componente de otra interior.",
        (
            "Hasta ocho interiores pueden compartir el grupo en la interfaz documentada.",
            "La dirección debe verificarse en Simple settings o Sensor info.",
        ),
        (
            "Anote la unidad mostrada con la alarma.",
            "Recorra las unidades del grupo y compare Sensor info.",
            "Identifique físicamente la interior antes de desmontar.",
        ),
        "RTC6_INSTALL",
        "9",
        "10",
        unit_scope="controller",
        controller_profile=RTC6_PROFILE,
    ),
    tv(
        3,
        "ECOi actual — decodificar LED1 M y LED2 N",
        "Placa exterior sin texto completo; dos indicadores muestran grupo M y número N mediante parpadeos.",
        "Convertir parpadeos de placa en códigos E/F/H/L/P.",
        "M define la letra: P=2, H=3, E=4, F=5 y L=6; N define el número. Dos parpadeos M y diecisiete N corresponden a P17.",
        (
            "Cuente ciclos completos y no mezcle el final de un grupo con el inicio del siguiente.",
            "Confirme después el código en el mando o herramienta de servicio.",
        ),
        (
            "Grabe o anote al menos dos ciclos completos de LED1 y LED2.",
            "Convierta M a la letra del grupo.",
            "Conserve N con dos cifras y forme el código.",
            "Verifique el resultado en la tabla de alarmas de esa exterior.",
        ),
        "VRF_MS3",
        "72",
        "75",
        system_type="ECOi 3 tubos actual",
        unit_scope="outdoor",
    ),
    tv(
        3,
        "ECOi — separar código, dirección y estado operativo",
        "Display de placa exterior con botones y lectura alternante.",
        "Evitar confundir una dirección o estado con una alarma.",
        "El monitor puede alternar dirección de circuito, número de unidad, dato de sensor y código de alarma.",
        (
            "Registre la secuencia completa y el modo de menú.",
            "Un valor sin letra de alarma puede ser un dato de monitorización.",
        ),
        (
            "No pulse botones hasta registrar la pantalla espontánea.",
            "Anote letra, número, posición de display y frecuencia de alternancia.",
            "Consulte el mapa del menú antes de cambiar de función.",
        ),
        "ECOI_W2",
        "312",
        "316",
        system_type="W-2WAY ECOi",
        unit_scope="outdoor",
    ),
    tv(
        3,
        "ECOi — alarma interior indicada en control de sistema",
        "Control central o mando de grupo muestra C05, C06 o P30.",
        "Localizar la subunidad protegida cuando el código se ve en el control de sistema.",
        "P30 indica protección en una subunidad; el manual recomienda conectar temporalmente un mando cableado para leer la alarma cuando solo hay inalámbrico.",
        (
            "C05/C06 corresponden a comunicación/configuración con el control central.",
            "El código del control de sistema no sustituye la alarma local de la interior.",
        ),
        (
            "Seleccione la dirección afectada en el control central.",
            "Conecte un mando cableado compatible si necesita la alarma local.",
            "Lea y anote ambos códigos antes de rearmar.",
        ),
        "ECOI_CODES",
        "6",
        system_type="ECOi/VRF",
        unit_scope="controller",
    ),
    tv(
        4,
        "RAC — borrar la memoria de avería sin confundirlo con reparación",
        "Split con botón AUTO OFF/ON interior y mando con CHECK.",
        "Eliminar el código almacenado después de corregir la causa.",
        "Con alimentación, AUTO OFF/ON durante unos 5 s inicia frío forzado; después se pulsa CHECK aproximadamente 1 s hasta oír confirmación.",
        (
            "El borrado no elimina un fallo activo: volverá a aparecer.",
            "Anote el código antes de borrar.",
        ),
        (
            "Repare y verifique la causa.",
            "Mantenga AUTO OFF/ON unos 5 s para frío forzado.",
            "Pulse CHECK cerca de 1 s con una punta no metálica adecuada.",
            "Confirme el pitido y vuelva a leer H00.",
        ),
        "RAC_PKE",
        "108",
        "109",
        system_type="RAC/split",
        unit_scope="indoor",
    ),
    tv(
        4,
        "CZ-RTC6 — borrar las cuatro alarmas recientes",
        "Menú Service check del CZ-RTC6.",
        "Limpiar el historial después de documentar y reparar.",
        "La función Delete borra la lista del mando; no debe utilizarse como prueba de que el sistema está reparado.",
        (
            "Una alarma activa puede reaparecer inmediatamente.",
            "Conserve foto o registro de código, unidad y fecha antes de borrar.",
        ),
        (
            "Abra Service check y copie las cuatro entradas.",
            "Corrija la causa y ejecute Test Run.",
            "Use Delete únicamente al terminar.",
            "Vuelva a consultar tras la prueba.",
        ),
        "RTC6_OPER",
        "20",
        "22",
        unit_scope="controller",
        controller_profile=RTC6_PROFILE,
    ),
    tv(
        4,
        "ECOi — cuándo el corte de alimentación no basta",
        "Alarmas de presión, descarga, inverter, red o EEPROM que reaparecen al arrancar.",
        "Distinguir un rearme temporal de una corrección real.",
        "El corte puede liberar el bloqueo memorizado, pero la protección vuelve si el umbral, dirección o componente sigue incorrecto.",
        (
            "Registre valores de presión, temperatura, corriente y dirección antes del rearme.",
            "No repita arranques sobre P03/P04/P16/P26 sin comprobar la causa.",
        ),
        (
            "Anote alarma, unidad y condiciones previas.",
            "Aísle alimentación el tiempo indicado por el manual.",
            "Compruebe la causa antes de volver a energizar.",
            "Controle el primer arranque con datos en vivo.",
        ),
        "ECOI_W2",
        "330",
        "335",
        system_type="ECOi/VRF",
    ),
    tv(
        5,
        "CZ-RTC6 — bus R1/R2 de dos hilos sin polaridad",
        "Bornes R1/R2 en la unidad interior y 1/2 en el mando.",
        "Cablear y comprobar el mando sin aplicar tensiones de potencia.",
        "Usa 0,75–1,25 mm², hasta 500 m totales, máximo 200 m entre interiores, dos mandos y ocho interiores.",
        (
            "R1/R2 no tiene polaridad en esta interfaz.",
            "No agrupar con potencia ni conectar a bornes de alimentación.",
        ),
        (
            "Corte el magnetotérmico antes de cablear.",
            "Conecte exclusivamente R1/R2–1/2 con el cable especificado.",
            "Separe el tendido de potencia y revise ausencia de cortos.",
            "Alimente y espere a que finalice Assigning.",
        ),
        "RTC6_INSTALL",
        "4",
        "5",
        unit_scope="controller",
        controller_profile=RTC6_PROFILE,
    ),
    tv(
        5,
        "CZ-RTC6 — dos mandos Main/Sub",
        "Dos CZ-RTC6 o combinación compatible controlan el mismo grupo.",
        "Evitar direcciones/roles duplicados y pérdida de control.",
        "Uno debe configurarse Main y el otro Sub; al combinar con CZ-RTC5B o versión Bluetooth, CZ-RTC6 se configura Sub según el manual.",
        (
            "El cableado prohibido del manual no debe reproducirse.",
            "Los mandos pueden conectarse a cualquier interior del grupo compatible.",
        ),
        (
            "Instale ambos mandos con alimentación cortada.",
            "Entre en RC setting mode.",
            "Configure uno Main y el otro Sub.",
            "Reinicie y compruebe control desde ambos.",
        ),
        "RTC6_INSTALL",
        "5",
        "10",
        unit_scope="controller",
        controller_profile=RTC6_PROFILE,
        parameters=[
            parameter(
                "Main/Sub",
                "Rol del mando",
                "Solo un mando principal por grupo.",
                [
                    option("Main", "Principal", "Gestiona los ajustes principales.", True),
                    option("Sub", "Secundario", "Comparte el grupo sin duplicar el rol principal."),
                ],
                factory="Main",
            )
        ],
    ),
    tv(
        5,
        "CZ-RTC5A — alimentación aproximada de 16 VDC",
        "Mando CZ-RTC5A conectado a una interior PACi/ECOi.",
        "Distinguir falta de alimentación del mando de un fallo de comunicación.",
        "La alimentación nominal indicada es DC16 V desde la unidad interior; la ausencia obliga a revisar placa, fusible, cable y bornes.",
        (
            "Medir con referencia y polaridad conforme al esquema de la interior.",
            "No inyectar tensión externa en el bus.",
        ),
        (
            "Corte tensión y revise continuidad del cable.",
            "Alimente y mida en bornes del mando con cuidado.",
            "Si hay tensión pero no inicia, revise dirección/placa del mando.",
        ),
        "RTC5",
        "44",
        unit_scope="controller",
        controller_profile=RTC5_PROFILE,
    ),
    tv(
        5,
        "CZ-RTC2 — no aplicar la secuencia ni el cableado de CZ-RTC6",
        "Mando antiguo con botones CHECK/SET y pantalla segmentada.",
        "Evitar procedimientos incompatibles entre generaciones.",
        "Los menús de servicio, combinación de botones y algunas interfaces cambian; identifique primero la familia del mando.",
        (
            "La forma física y nombres de teclas son pistas más útiles que el modelo de la máquina.",
            "Conserve la referencia interna del manual para trazabilidad.",
        ),
        (
            "Fotografíe el mando y anote nombres de botones.",
            "Elija la variante CZ-RTC2 antes de acceder al servicio.",
            "No cambie ajustes si solo necesita leer sensores.",
        ),
        "ECOI_2PIPE",
        "159",
        "163",
        unit_scope="controller",
        controller_profile=RTC2_PROFILE,
    ),
    tv(
        6,
        "S-LINK — resistencia de línea con alimentación cortada",
        "Red ECOi/VRF con línea S-LINK y unidades de uno o varios circuitos frigoríficos.",
        "Detectar corto, línea abierta y terminación incorrecta antes de auto-address.",
        "Con todo sin tensión, la resistencia medida debe quedar entre 30 y 120 Ω (ohmios) según la red documentada.",
        (
            "Fuera de rango puede indicar corto, circuito abierto, mala conexión o número incorrecto de terminadores.",
            "La medida se hace sin alimentación; no es una tensión de bus.",
        ),
        (
            "Corte alimentación de todas las unidades y confirme ausencia de tensión.",
            "Desconecte controles externos que alteren la medida si lo exige el esquema.",
            "Mida entre los dos conductores S-LINK.",
            "Corrija topología antes de ejecutar auto-address.",
        ),
        "VRF_MS3",
        "28",
        "31",
        system_type="ECOi/VRF",
    ),
    tv(
        6,
        "S-LINK — exactamente dos terminadores en redes con varios circuitos",
        "Dos o más circuitos frigoríficos comparten la línea de transmisión.",
        "Colocar terminación en los extremos reales y evitar una tercera resistencia.",
        "La documentación actual exige dos terminadores, en las unidades más cercana y más alejada de la línea; tres o más están prohibidos.",
        (
            "La posición física del equipo no siempre coincide con el extremo eléctrico.",
            "Un terminador extra puede permitir fallos intermitentes difíciles de reproducir.",
        ),
        (
            "Dibuje la topología real de la línea.",
            "Identifique los dos extremos eléctricos.",
            "Active terminación solo en esos extremos.",
            "Mida 30–120 Ω antes de alimentar.",
        ),
        "VRF_MS3",
        "29",
        "32",
        system_type="ECOi/VRF",
    ),
    tv(
        6,
        "RAC/multisplit — comprobar comunicación sin mezclarla con potencia",
        "Cable interunidad que transporta alimentación y señal según la familia RAC.",
        "Diagnosticar H11 mediante alimentación, continuidad y transmisión.",
        "H11 se confirma después del tiempo de espera; un ventilador interior funcionando no demuestra que exista comunicación válida.",
        (
            "Revise orden de bornes y apriete en ambos extremos.",
            "Una tensión presente no confirma integridad de la señal ni tubería correcta.",
        ),
        (
            "Corte tensión y compare borne a borne con el esquema.",
            "Revise continuidad, aislamiento y conexión de tierra.",
            "Alimente, espere el minuto de detección y observe H11.",
        ),
        "MULTI_4E",
        "76",
        "77",
        system_type="Multisplit RAC",
    ),
    tv(
        6,
        "S-LINK — ruido, derivaciones y orden de energización",
        "Red larga, con controles centrales o repetidores, que falla de forma intermitente.",
        "Separar un problema de topología de una placa averiada.",
        "La red debe respetar longitud, tipo de cable, separación de potencia, terminación y secuencia de puesta en marcha.",
        (
            "E04/E06/E24/E29 señalan quién dejó de recibir, no necesariamente quién está averiado.",
            "El auto-address no debe repetirse sobre una red físicamente incorrecta.",
        ),
        (
            "Registre qué unidades comunican y cuáles no.",
            "Revise topología, empalmes, pantalla y separación de potencia.",
            "Mida resistencia con todo apagado.",
            "Energice siguiendo el orden de la instalación y verifique direcciones.",
        ),
        "ECOI_W2",
        "320",
        "327",
        system_type="W-2WAY ECOi",
    ),
    tv(
        7,
        "CZ-RTC6 — Assigning al alimentar",
        "El mando muestra Assigning fijo o intermitente al energizar.",
        "Distinguir adquisición normal de un fallo de direccionamiento.",
        "Assigning es normal durante la adquisición; si continúa parpadeando más de 10 minutos deben revisarse direcciones y comunicación.",
        (
            "No intente programar mientras la asignación está incompleta.",
            "La causa puede estar en una interior del grupo, no en el propio mando.",
        ),
        (
            "Alimente el grupo y espere sin pulsar teclas.",
            "Si supera 10 min, anote si Assigning está fijo o parpadea.",
            "Revise alimentación, bus y direcciones de todas las interiores.",
        ),
        "RTC6_INSTALL",
        "8",
        "9",
        unit_scope="controller",
        controller_profile=RTC6_PROFILE,
    ),
    tv(
        7,
        "E01/E02/E03 — localizar el extremo que no transmite",
        "ECOi con mando y una o varias interiores.",
        "Evitar sustituir el mando cuando la interior no está alimentada.",
        "E01 es recepción en mando, E02 transmisión desde mando y E03 recepción en interior; juntos acotan la dirección del fallo.",
        (
            "Compruebe primero alimentación y bus.",
            "Main/Sub o direcciones duplicadas pueden producir síntomas equivalentes.",
        ),
        (
            "Anote qué dispositivo muestra E01/E02/E03.",
            "Verifique alimentación del mando y de la interior.",
            "Revise cable y roles Main/Sub.",
            "Pruebe con un mando compatible solo después de la red.",
        ),
        "ECOI_CODES",
        "1",
        system_type="ECOi/VRF",
        unit_scope="controller",
    ),
    tv(
        8,
        "CZ-RTC6 — Test Run desde Maintenance func",
        "Mando CZ-RTC6 con MENU, ▲, ▼ y ENTER.",
        "Forzar una prueba controlada en frío, calor o ventilación.",
        "MENU+▲+▼ durante al menos 4 s abre Maintenance func; Test run se pone ON y se inicia con START/STOP.",
        (
            "No permite ajustar la temperatura durante la prueba.",
            "Se cancela automáticamente a los 60 min y la exterior conserva el retardo de seguridad de 3 min.",
        ),
        (
            "Compruebe alimentación, válvulas abiertas, drenaje y ausencia de herramientas.",
            "Mantenga MENU+▲+▼ al menos 4 s y seleccione Test run > ON.",
            "Arranque y elija Heat, Cool o Fan.",
            "Vigile presiones, temperaturas, agua y códigos; salga poniendo Test run OFF.",
        ),
        "RTC6_INSTALL",
        "10",
        "11",
        unit_scope="controller",
        controller_profile=RTC6_PROFILE,
    ),
    tv(
        8,
        "CZ-RTC5B — Test Run desde el menú de mantenimiento",
        "Mando CZ-RTC5B con menú Maintenance func y entrada Test Run.",
        "Probar una interior PACi/ECOi sin modificar su programación permanente.",
        "La combinación de tres botones abre mantenimiento; el ítem Test Run permite Heat/Cool/Fan y se cancela a los 60 min.",
        (
            "La exterior puede tardar 3 min por protección.",
            "La prueba no anula alta presión, descarga, sobrecorriente, drenaje ni comunicación.",
        ),
        (
            "Revise condiciones previas y abra Maintenance func.",
            "Seleccione Test Run y active ON.",
            "Arranque en el modo requerido y registre valores.",
            "Desactive Test Run manualmente al terminar.",
        ),
        "PACI_PE4",
        "151",
        "153",
        system_type="PACi",
        unit_scope="controller",
        controller_profile=RTC5_PROFILE,
    ),
    tv(
        8,
        "PACi — qué continúa vigilando durante Test Run",
        "Prueba iniciada desde CZ-RTC5B/6 en una interior de conductos o cassette.",
        "Interpretar una parada durante la prueba como protección válida.",
        "Test Run fuerza demanda, pero mantiene protecciones eléctricas, frigoríficas, comunicación, ventilador y drenaje.",
        (
            "Una parada con P10/P12/P03/P04 no significa que Test Run haya fallado.",
            "El termostato ambiente deja de regular, pero no se puentean seguridades.",
        ),
        (
            "Inicie la prueba con instrumentos preparados.",
            "Observe código, modo y tiempo exacto de la parada.",
            "Consulte la ficha de la protección antes de rearmar.",
        ),
        "PACI_PE4",
        "151",
        "154",
        system_type="PACi",
    ),
    tv(
        8,
        "ECOi — Test Run por circuito frigorífico",
        "Sistema VRF con varias interiores y dirección de circuito configurada.",
        "Probar un circuito sin confundirlo con auto-address.",
        "La prueba se ejecuta sobre el circuito seleccionado; deben completarse direcciones y comunicación antes de arrancar.",
        (
            "Auto-address puede detener el sistema completo; Test Run no corrige una red incompleta.",
            "Registre qué interiores participan y cuáles quedan fuera.",
        ),
        (
            "Verifique dirección de circuito e interiores reconocidas.",
            "Seleccione el circuito y el modo de prueba.",
            "Compruebe que participan las unidades esperadas.",
            "Finalice la prueba y revise historial.",
        ),
        "VRF_MS3",
        "56",
        "64",
        system_type="ECOi/VRF",
    ),
    tv(
        9,
        "RAC — pump down con AUTO OFF/ON",
        "Split con válvulas de servicio exterior y botón AUTO OFF/ON interior.",
        "Recoger refrigerante en la exterior antes de desconectar tuberías.",
        "La marcha forzada en frío mantiene el compresor; se cierra primero líquido, se controla presión y después gas antes de detener.",
        (
            "Nunca deje que aspire aire ni trabaje en vacío.",
            "Detenga el compresor antes de retirar tuberías.",
        ),
        (
            "Conecte manómetro y verifique válvulas, ventilación y carga admisible.",
            "Active frío forzado con AUTO OFF/ON.",
            "Cierre la válvula de líquido y observe la presión.",
            "Cierre gas y detenga inmediatamente antes de desconectar.",
        ),
        "RAC_PKE",
        "103",
        "105",
        system_type="RAC/split",
        unit_scope="outdoor",
    ),
    tv(
        9,
        "Multisplit — pump down tras detectar tubería o cableado cruzado",
        "Exterior con varias conexiones A–E y error de correspondencia.",
        "Recoger refrigerante de forma controlada antes de corregir conexiones.",
        "El manual exige detener, cortar tensión y efectuar pump down si se debe abrir el circuito por una conexión incorrecta.",
        (
            "Etiquete cada cable y par de tuberías antes de corregir.",
            "No mezcle refrigerante recogido de conexiones diferentes sin seguir la secuencia.",
        ),
        (
            "Detenga la operación al confirmar el cruce.",
            "Identifique conexión A–E afectada.",
            "Efectúe pump down según la unidad y cierre válvulas.",
            "Corrija, haga vacío y repita la prueba de correspondencia.",
        ),
        "MULTI_5E",
        "60",
        "61",
        system_type="Multisplit 5 conexiones",
        unit_scope="outdoor",
    ),
    tv(
        9,
        "ECOi/VRF — límite de recuperación en la unidad exterior",
        "Sistema de gran volumen con carga adicional de tubería.",
        "Evitar intentar almacenar en la exterior más refrigerante del admisible.",
        "La exterior no puede recoger más que la cantidad indicada en su placa/capacidad interna; el exceso exige equipo de recuperación.",
        (
            "La carga total del sistema puede superar ampliamente la capacidad de almacenamiento del módulo.",
            "No cierre válvulas sin calcular previamente la cantidad.",
        ),
        (
            "Calcule carga de fábrica más carga adicional.",
            "Compare con la capacidad de recogida documentada.",
            "Si la supera, utilice recuperadora y botella homologada.",
            "Pese el refrigerante recuperado.",
        ),
        "VRF_MS3",
        "19",
        "21",
        system_type="ECOi/VRF",
        unit_scope="outdoor",
    ),
    tv(
        9,
        "Pump down — protección frente a aspiración de aire",
        "Cualquier Panasonic inverter con tuberías que van a desconectarse.",
        "Evitar sobrepresión, mezcla de aire y daño del compresor.",
        "El compresor debe detenerse antes de desmontar tuberías; si aspira aire, la presión y temperatura internas pueden elevarse peligrosamente.",
        (
            "No utilice pump down como sustituto de una recuperadora cuando la carga no cabe.",
            "No puentee baja presión ni sensores para prolongar la maniobra.",
        ),
        (
            "Prepare manómetro y acceso a parada antes de iniciar.",
            "Controle presión continuamente.",
            "Detenga ante comportamiento anormal o antes de entrar en vacío.",
        ),
        "PACI_PE4",
        "127",
        "128",
        system_type="RAC/PACi",
        unit_scope="outdoor",
    ),
    tv(
        10,
        "RAC — frío forzado con AUTO OFF/ON",
        "Botón interior AUTO OFF/ON accesible bajo la tapa o panel.",
        "Forzar refrigeración para diagnóstico o pump down.",
        "Mantener el botón unos 5 s inicia refrigeración forzada con confirmación acústica.",
        (
            "Se mantiene el retardo del compresor y las protecciones.",
            "No equivale a ordenar una frecuencia fija en todas las familias.",
        ),
        (
            "Abra válvulas y compruebe alimentación y drenaje.",
            "Mantenga AUTO OFF/ON unos 5 s hasta el pitido.",
            "Controle arranque, ventiladores y valores.",
            "Pulse de nuevo para detener.",
        ),
        "RAC_PKE",
        "108",
        system_type="RAC/split",
        unit_scope="indoor",
    ),
    tv(
        10,
        "RAC antiguo — calefacción forzada mediante secuencia del botón",
        "Split JKE con botón AUTO OFF/ON y confirmaciones acústicas por duración.",
        "Forzar calor cuando la familia lo documenta.",
        "La secuencia de pulsación distingue frío, prueba y calefacción; no debe extrapolarse a otro receptor.",
        (
            "Cuente pitidos y duración, no solo que el LED se encienda.",
            "La unidad conserva protecciones de descarga, presión, corriente y desescarche.",
        ),
        (
            "Identifique que la interior pertenece a la generación JKE compatible.",
            "Aplique la duración y secuencia del manual.",
            "Confirme que conmuta la válvula de cuatro vías.",
            "Detenga desde AUTO OFF/ON.",
        ),
        "RAC_JKE",
        "95",
        "97",
        system_type="RAC/split antiguo",
        unit_scope="indoor",
    ),
    tv(
        10,
        "Multisplit antiguo — desescarche forzado desde T-RUN/COM",
        "Placa exterior con terminales TEST/T-RUN y COM.",
        "Comprobar compresor, ventilador, cuatro vías y bypass de gas caliente.",
        "Con 220 VAC aplicada, el puente T-RUN–COM inicia la secuencia; el compresor trabaja a 70 Hz y el ventilador exterior se detiene durante desescarche.",
        (
            "El ventilador interior se detiene y la cuatro vías permanece ON.",
            "No insertar ni retirar conectores de placa con tensión.",
        ),
        (
            "Corte tensión y prepare el puente temporal según esquema.",
            "Alimente y cierre T-RUN–COM.",
            "Verifique LED rojo y secuencia de actuadores.",
            "Retire el puente con seguridad y restablezca el circuito.",
        ),
        "MULTI_5E",
        "28",
        "30",
        system_type="Multisplit antiguo",
        unit_scope="outdoor",
    ),
    tv(
        11,
        "Cassette — proceso P10 por boya activada",
        "Unidad interior con bomba, bandeja y contacto de flotador.",
        "Distinguir agua real, boya atascada, bomba y placa.",
        "P10 indica que la entrada de flotador permanece en condición de alarma; la interior se protege mientras la bomba intenta evacuar.",
        (
            "Una boya pegada puede simular desbordamiento sin agua.",
            "En calor/parada la bomba puede activarse por la boya aunque no exista condensación normal.",
        ),
        (
            "Inspeccione bandeja antes de mover la boya.",
            "Compruebe pendiente, sifón, obstrucción y salida.",
            "Accione la boya y fuerce la bomba desde servicio.",
            "Verifique que el contacto cambia y el nivel baja antes de rearmar.",
        ),
        "PACI_HIGH",
        "142",
        "143",
        system_type="PACi cassette/conductos",
        unit_scope="indoor",
    ),
    tv(
        12,
        "CZ-RTC6 — Simple settings para dirección y funciones básicas",
        "Maintenance func > Simple settings en un CZ-RTC6.",
        "Consultar o ajustar dirección y opciones de la interior seleccionada.",
        "La pantalla permite escoger número de unidad, código de función y dato; debe anotarse el valor original antes de cambiar.",
        (
            "No cambie varias funciones a la vez.",
            "La dirección mostrada debe corresponder con la unidad física.",
        ),
        (
            "Entre en mantenimiento y seleccione Simple settings.",
            "Seleccione la interior y copie todos los valores relevantes.",
            "Cambie solo el código documentado.",
            "Confirme, reinicie si se exige y verifique.",
        ),
        "PACI_PE4",
        "155",
        "160",
        system_type="PACi/ECOi",
        unit_scope="controller",
        controller_profile=RTC6_PROFILE,
    ),
    tv(
        12,
        "CZ-RTC6 — Detailed settings y EEPROM",
        "Menú Detailed settings con códigos y valores de cuatro cifras.",
        "Acceder a funciones avanzadas sin perder la configuración de fábrica.",
        "Los valores se almacenan en EEPROM; una selección incorrecta puede alterar drenaje, ventilador, sensores o entradas externas.",
        (
            "Fotografíe o exporte la configuración antes de modificar.",
            "No copie ajustes entre interiores de distinta capacidad o arquitectura.",
        ),
        (
            "Seleccione la unidad exacta y abra Detailed settings.",
            "Registre código, valor actual y valor de fábrica.",
            "Cambie un único parámetro y confirme.",
            "Reinicie y compruebe su efecto.",
        ),
        "PACI_PE4",
        "160",
        "171",
        system_type="PACi",
        unit_scope="controller",
        controller_profile=RTC6_PROFILE,
    ),
    tv(
        12,
        "Selección del sensor de temperatura — unidad o mando",
        "Instalación con CZ-RTC5/6 situado en una zona representativa.",
        "Elegir qué sensor regula sin confundirlo con una sonda averiada.",
        "La programación permite usar sensor de retorno de la interior, sensor del mando o lógica combinada según familia.",
        (
            "Una mala ubicación del mando produce regulación incorrecta aunque no haya código.",
            "Sensor info permite comparar ambas temperaturas.",
        ),
        (
            "Mida temperatura real en retorno y junto al mando.",
            "Consulte la selección actual.",
            "Elija la fuente adecuada y documente el cambio.",
            "Compruebe estabilidad de regulación.",
        ),
        "PACI_PE4",
        "164",
        "166",
        system_type="PACi/ECOi",
        unit_scope="controller",
        controller_profile=RTC6_PROFILE,
    ),
    tv(
        12,
        "Conductos — presión estática y curva de ventilador",
        "Unidad S-PE4R de conductos con ventilador DC y ajuste desde mando.",
        "Adaptar el caudal a la red sin interpretar ruido o bajo caudal como avería.",
        "La función de presión estática modifica la curva del ventilador; debe coincidir con conductos, filtros y rejillas reales.",
        (
            "Un ajuste alto puede aumentar ruido, consumo y arrastre de agua.",
            "Un ajuste bajo puede provocar mala transferencia y protecciones.",
        ),
        (
            "Mida presión estática y caudal antes de cambiar.",
            "Consulte el código/valor actual.",
            "Seleccione la curva documentada para la instalación.",
            "Repita medidas y compruebe drenaje.",
        ),
        "PACI_PE4",
        "166",
        "169",
        system_type="PACi conductos",
        unit_scope="indoor",
        controller_profile=RTC6_PROFILE,
    ),
    tv(
        12,
        "Entradas externas — demanda, parada y contacto remoto",
        "Interior PACi/ECOi con conector de entrada externa y función asignable.",
        "Distinguir una orden externa de una avería interna.",
        "La programación define si el contacto actúa como arranque/parada, prohibición, demanda u otra función.",
        (
            "Compruebe estado del contacto y lógica NO/NC antes de sustituir la placa.",
            "Una orden BMS puede mantener la unidad parada sin código.",
        ),
        (
            "Identifique conector y función programada.",
            "Mida el contacto sin inyectar tensión externa no autorizada.",
            "Desconecte temporalmente solo según el manual y observe respuesta.",
            "Restaure y documente.",
        ),
        "PACI_PE4",
        "169",
        "172",
        system_type="PACi/ECOi",
        unit_scope="indoor",
    ),
    tv(
        12,
        "Configuración Main/Sub del mando y del grupo",
        "Dos mandos o varias interiores conectadas a un grupo común.",
        "Evitar E09/L05/L06 y control incoherente.",
        "Main/Sub del mando, Main de interior y prioridad del circuito son ajustes distintos y deben documentarse por separado.",
        (
            "Un grupo solo admite el número y roles indicados por su familia.",
            "No use auto-address para corregir únicamente un rol de mando.",
        ),
        (
            "Dibuje interiores, mandos y controles centrales.",
            "Anote rol/dirección de cada elemento.",
            "Corrija duplicados uno a uno.",
            "Reinicie y pruebe desde ambos mandos.",
        ),
        "ECOI_2PIPE",
        "145",
        "151",
        system_type="ECOi",
        unit_scope="controller",
    ),
    tv(
        13,
        "Exterior ECOi — DIP y selectores de dirección frigorífica",
        "Placa exterior con DIP switches y selectores rotativos/teclas de dirección.",
        "Configurar circuito sin duplicar exteriores.",
        "La dirección de circuito y el rol de unidad exterior deben ajustarse antes de auto-address.",
        (
            "H04/E25 pueden aparecer por direcciones duplicadas.",
            "Corte alimentación cuando el manual lo exija para leer los selectores al arrancar.",
        ),
        (
            "Registre posición original de todos los DIP/selectores.",
            "Asigne una dirección única al circuito y roles de exteriores.",
            "Revise terminadores y número de módulos.",
            "Alimente y ejecute auto-address.",
        ),
        "VRF_MS3",
        "45",
        "55",
        system_type="ECOi/VRF",
        unit_scope="outdoor",
    ),
    tv(
        13,
        "Exterior ECOi — número de módulos y Main/Sub",
        "Sistema modular con dos o más unidades exteriores conectadas.",
        "Evitar E18/E26/E29 por cantidad o rol incorrectos.",
        "La Main debe conocer el número de módulos y comunicarse con cada secundaria; una discrepancia bloquea la puesta en marcha.",
        (
            "E18/E29 indican falta de comunicación entre exteriores.",
            "E26 indica cantidad detectada distinta de la configurada.",
        ),
        (
            "Identifique físicamente Main y secundarias.",
            "Compruebe cable de comunicación entre exteriores.",
            "Ajuste número de módulos y roles.",
            "Reinicie y verifique que todas responden.",
        ),
        "ECOI_CODES",
        "1",
        system_type="ECOi/VRF modular",
        unit_scope="outdoor",
    ),
    tv(
        13,
        "PACi — conservar ajustes antes de sustituir placa",
        "Placa interior o exterior que va a ser reemplazada.",
        "Evitar F29/F31, capacidad cero y comportamiento incorrecto tras la reparación.",
        "Antes de desmontar deben copiarse EEPROM/settings, capacidad, dirección, DIP, Main/Sub y accesorios activados.",
        (
            "Una placa nueva puede estar sana y aun así generar L09/L10 o F29/F31.",
            "No copie posiciones de otro modelo sin confirmar compatibilidad.",
        ),
        (
            "Fotografíe placa, conectores, DIP y etiquetas.",
            "Exporte o anote Simple/Detailed settings.",
            "Instale la placa y restaure solo los datos documentados.",
            "Direccione y ejecute Test Run.",
        ),
        "PACI_PE4",
        "173",
        "178",
        system_type="PACi",
    ),
    tv(
        14,
        "ECOi — auto-address y parada del sistema",
        "Red S-LINK ya terminada, con direcciones de exterior configuradas.",
        "Asignar interiores de forma automática sin provocar E12/E15/E20.",
        "Auto-address interroga todo el circuito y puede detener el sistema completo; no debe iniciarse simultáneamente desde dos exteriores.",
        (
            "E12 indica otra autoasignación en curso.",
            "E20 indica interiores que no respondieron.",
        ),
        (
            "Verifique 30–120 Ω, dos terminadores y alimentación de todas las interiores.",
            "Inicie auto-address desde una sola exterior Main.",
            "Espere a que finalice sin cortar tensión.",
            "Compare cantidad y direcciones con el plano.",
        ),
        "VRF_MS3",
        "56",
        "63",
        system_type="ECOi/VRF",
    ),
    tv(
        14,
        "ECOi — direccionamiento manual de interiores",
        "Instalación donde se requiere una dirección interior concreta.",
        "Mantener correspondencia con planos, control central y circuitos.",
        "La dirección interior y la dirección de circuito frigorífico son campos diferentes; ambas deben ser únicas dentro de su alcance.",
        (
            "E08/L03/L04/L08 señalan duplicados o ausencia de dirección.",
            "Anote dirección física en la unidad después de confirmar.",
        ),
        (
            "Defina tabla de direcciones antes de programar.",
            "Ajuste dirección interior y circuito en cada unidad.",
            "Compruebe que no hay duplicados.",
            "Verifique desde CZ-RTC5/6 o control central.",
        ),
        "ECOI_2PIPE",
        "139",
        "151",
        system_type="ECOi",
        unit_scope="indoor",
    ),
    tv(
        14,
        "ECOi — comprobar la cantidad de interiores reconocidas",
        "Exterior muestra E16/E20 o la lista no coincide con la instalación.",
        "Localizar una interior sin alimentación o fuera de la red.",
        "La exterior compara cantidad configurada y respuestas reales; una unidad apagada puede impedir completar la puesta en marcha.",
        (
            "E16 suele indicar más interiores configuradas que detectadas.",
            "E20 identifica falta de respuesta durante auto-address.",
        ),
        (
            "Cuente interiores instaladas y alimentadas.",
            "Compare con la cantidad programada.",
            "Aísle por tramos la unidad que no responde.",
            "Repita auto-address solo al corregir.",
        ),
        "ECOI_CODES",
        "1",
        system_type="ECOi/VRF",
    ),
    tv(
        14,
        "CZ-RTC6 — verificar dirección sin volver a direccionar",
        "Mando controla un grupo ya puesto en marcha.",
        "Confirmar unidad/dirección con riesgo mínimo.",
        "Simple settings y Sensor info permiten seleccionar y reconocer interiores sin lanzar auto-address.",
        (
            "Es preferible consultar antes que reprogramar.",
            "La respuesta de ventilador o temperatura ayuda a identificar físicamente la unidad.",
        ),
        (
            "Abra Simple settings en modo consulta.",
            "Recorra números de unidad sin modificar valores.",
            "Compare Sensor info y ubicación física.",
            "Salga sin confirmar cambios.",
        ),
        "RTC6_INSTALL",
        "9",
        "10",
        unit_scope="controller",
        controller_profile=RTC6_PROFILE,
    ),
    tv(
        15,
        "Multisplit — capacidad conectada y H12",
        "Exterior con dos a cinco conexiones y varias interiores de distinta potencia.",
        "Comprobar combinación antes de condenar placas.",
        "La suma y tipos de interiores deben quedar dentro de la combinación admitida; la placa puede declarar H12 tras unos 90 s.",
        (
            "Una interior sustituida por otra capacidad puede provocar el fallo.",
            "El error aparece aunque cableado y refrigerante sean correctos.",
        ),
        (
            "Anote capacidad de cada interior conectada.",
            "Sume y compare con la tabla de combinación.",
            "Compruebe conectores de capacidad y placa instalada.",
            "Alimente y espere el tiempo de validación.",
        ),
        "MULTI_4E",
        "78",
        "80",
        system_type="Multisplit",
    ),
    tv(
        15,
        "Multisplit — una interior satisfecha no obliga a parar la exterior",
        "Varias interiores comparten compresor y alguna mantiene demanda.",
        "Interpretar correctamente paradas y continuidades.",
        "La exterior puede seguir funcionando si otra interior solicita carga; el termostato satisfecho de una unidad no implica parada del conjunto.",
        (
            "El ventilador interior puede seguir con el compresor atendiendo otra zona.",
            "Compruebe demanda de todas las interiores antes de diagnosticar.",
        ),
        (
            "Registre modo y consigna de cada interior.",
            "Compruebe cuál mantiene demanda.",
            "Observe frecuencia de compresor y válvulas de cada conexión.",
        ),
        "MULTI_5E",
        "18",
        "20",
        system_type="Multisplit",
    ),
    tv(
        15,
        "Multisplit — tubería y cableado deben corresponder A–E",
        "Exterior con pares de válvulas y bornes identificados A, B, C, D y E.",
        "Detectar H41 o rendimiento anormal por conexiones cruzadas.",
        "Cada cable interunidad debe corresponder a su par de tuberías; las etiquetas en ambos extremos evitan cruces.",
        (
            "Corregir tuberías exige pump down y nuevo vacío.",
            "No basta intercambiar cables si las tuberías también están cruzadas.",
        ),
        (
            "Identifique cada interior y su conexión de gas/líquido.",
            "Compare con el cable interunidad etiquetado.",
            "Realice prueba de correspondencia.",
            "Si hay cruce de tubería, efectúe pump down antes de corregir.",
        ),
        "MULTI_5E",
        "59",
        "61",
        system_type="Multisplit 5 conexiones",
    ),
    tv(
        16,
        "ECOi — alarma de una interior frente a alarma de circuito",
        "Sistema con varias interiores y código mostrado en una de ellas o en la exterior.",
        "Saber si pueden continuar las demás unidades.",
        "Alarmas interiores como P10/P12 pueden aislar la unidad afectada; comunicación de red, alta presión o auto-address pueden afectar circuito o sistema completo.",
        (
            "La guía marca categorías cuyo efecto no se extiende a otras interiores.",
            "Cuando el manual no determina el alcance, la ficha no lo inventa.",
        ),
        (
            "Anote dónde se muestra el código.",
            "Clasifique interior, exterior, red o configuración.",
            "Observe qué unidades siguen operativas sin forzarlas.",
            "Consulte el alcance de la interpretación concreta.",
        ),
        "ECOI_W2",
        "330",
        "336",
        system_type="ECOi/VRF",
    ),
    tv(
        16,
        "ECOi modular — funcionamiento de respaldo",
        "Sistema con varios módulos exteriores o varios compresores.",
        "Distinguir parada total de degradación por pérdida de un módulo.",
        "Determinadas alarmas permiten respaldo con capacidad reducida; otras de presión, red o seguridad bloquean el circuito.",
        (
            "No asumir respaldo solo porque existe otra exterior.",
            "Compruebe que el manual de la alarma permite operación de emergencia.",
        ),
        (
            "Identifique módulo y compresor afectados.",
            "Consulte la tabla de backup/emergency operation.",
            "Aísle únicamente según procedimiento oficial.",
            "Informe de la reducción de capacidad.",
        ),
        "ECOI_W2",
        "337",
        "344",
        system_type="ECOi modular",
        unit_scope="outdoor",
    ),
    tv(
        16,
        "Auto-address — parada global prevista",
        "ECOi en commissioning con autoasignación activa.",
        "No confundir la parada de unidades con una nueva avería.",
        "Durante la autoasignación se detiene el control normal del sistema hasta completar direcciones.",
        (
            "No interrumpa alimentación salvo condición insegura.",
            "Si no termina, investigue E12/E15/E16/E20.",
        ),
        (
            "Avise a usuarios antes de iniciar.",
            "Confirme que todas las interiores están alimentadas.",
            "Espere a finalización y revise el recuento.",
        ),
        "PACI_PE4",
        "158",
        "160",
        system_type="ECOi/VRF",
    ),
    tv(
        16,
        "P30 — obtener la alarma real de la subunidad",
        "Control de grupo muestra P30 y no identifica el componente.",
        "Llegar desde el código paraguas a la protección local.",
        "P30 indica que una subunidad del grupo está protegida; se necesita leer la alarma de esa interior.",
        (
            "No sustituya placa por P30 sin el código subordinado.",
            "Con mando inalámbrico puede ser necesario conectar temporalmente uno cableado.",
        ),
        (
            "Seleccione la unidad protegida.",
            "Conecte mando cableado compatible si es necesario.",
            "Lea la alarma local y su historial.",
            "Diagnostique el código subordinado.",
        ),
        "ECOI_CODES",
        "6",
        system_type="ECOi/VRF",
        unit_scope="indoor",
    ),
    tv(
        17,
        "Cassette — NTC de aire 15 kΩ, Beta 3950",
        "Sonda de retorno indicada como 15K, B=3950 en el esquema.",
        "Comparar resistencia con temperatura sin depender del código.",
        "R25 y Beta son oficiales; la tabla de varios puntos se calcula con la ecuación Beta y se marca como calculada.",
        (
            "A 25 °C debe aproximarse a 15 kΩ, dentro de tolerancia del componente.",
            "No use esta curva para una sonda de 20 kΩ.",
        ),
        (
            "Desconecte la sonda de la placa.",
            "Mida temperatura y resistencia en equilibrio.",
            "Compare con la curva 15 kΩ/B3950.",
            "Caliente o enfríe y compruebe variación progresiva.",
        ),
        "CASSETTE",
        "21",
        system_type="Cassette",
        unit_scope="indoor",
        monitoring=[{"name": "NTC aire", "value": "15 kΩ a 25 °C", "unit": "kΩ", "notes": "B=3950 K"}],
    ),
    tv(
        17,
        "Cassette — NTC de tubería 20 kΩ, Beta 3950",
        "Sonda de tubería indicada como 20K, B=3950.",
        "Diagnosticar H23/H28/H32/H36/H37 en familias compatibles.",
        "R25=20 kΩ y Beta=3950 permiten calcular la curva; confirme siempre el esquema de la unidad.",
        (
            "A 25 °C debe aproximarse a 20 kΩ.",
            "Una sonda desprendida puede medir bien en banco y leer mal durante funcionamiento.",
        ),
        (
            "Compruebe fijación y pasta/contacto térmico.",
            "Desconecte y mida resistencia.",
            "Compare con la curva 20 kΩ/B3950.",
            "Verifique Sensor info durante Test Run.",
        ),
        "CASSETTE",
        "21",
        system_type="Cassette/RAC",
        unit_scope="indoor",
        monitoring=[{"name": "NTC tubería", "value": "20 kΩ a 25 °C", "unit": "kΩ", "notes": "B=3950 K"}],
    ),
    tv(
        17,
        "PACi antiguo — tabla oficial de sonda de aire/intercambiador",
        "Termistores TH1–TH4 de una generación PACi R410A.",
        "Usar puntos oficiales sin extrapolar a PACi NX moderno.",
        "La tabla da 15,0 kΩ a 0 °C, 6,5 kΩ a 20 °C, 4,4 kΩ a 30 °C y 2,1 kΩ a 50 °C.",
        (
            "Tolerancia indicada ±5 %.",
            "La curva disminuye de forma no lineal al aumentar temperatura.",
        ),
        (
            "Identifique TH1–TH4 en el esquema.",
            "Mida temperatura local y resistencia desconectada.",
            "Compare con los puntos oficiales y tolerancia.",
        ),
        "OLD_PACI",
        "90",
        "91",
        system_type="PACi antiguo",
        monitoring=[{"name": "TH1–TH4", "value": "6,5 kΩ a 20 °C", "unit": "kΩ", "notes": "±5 %"}],
    ),
    tv(
        17,
        "PACi antiguo — tabla oficial de sonda de descarga",
        "Termistor TH5 o sonda de descarga de alta temperatura.",
        "Comprobar P03/H05 sin usar la curva de una sonda ambiente.",
        "La tabla da 12,4 kΩ a 60 °C, 4,6 kΩ a 90 °C, 3,4 kΩ a 100 °C y 1,5 kΩ a 130 °C.",
        (
            "La tolerancia indicada en la zona de trabajo es ±7 %.",
            "Una fijación deficiente puede activar H05 por falta de cambio térmico.",
        ),
        (
            "Deje enfriar antes de manipular la descarga.",
            "Revise fijación y aislamiento del sensor.",
            "Mida y compare con la tabla de alta temperatura.",
        ),
        "OLD_PACI",
        "91",
        "92",
        system_type="PACi/ECOi antiguo",
        unit_scope="outdoor",
        monitoring=[{"name": "TH5 descarga", "value": "3,4 kΩ a 100 °C", "unit": "kΩ", "notes": "±7 %"}],
    ),
    tv(
        17,
        "Sensor info — comparar lectura electrónica con termómetro/manómetro",
        "CZ-RTC6 o herramienta CONEX con datos de sensores en vivo.",
        "Separar sonda, cableado y circuito de lectura.",
        "Una discrepancia entre temperatura/presión real y valor monitorizado orienta a sensor, conexión o placa.",
        (
            "Use instrumentos calibrados y deje estabilizar.",
            "No condene la placa solo por un valor puntual durante transición.",
        ),
        (
            "Abra Sensor info y seleccione la unidad.",
            "Mida el mismo punto con instrumento externo.",
            "Compare en régimen estable y durante cambio controlado.",
            "Revise cable/sonda si la discrepancia persiste.",
        ),
        "RTC6_OPER",
        "18",
        "22",
        system_type="PACi/ECOi",
        unit_scope="controller",
        controller_profile=RTC6_PROFILE,
    ),
    tv(
        18,
        "Multisplit — comprobar EEV: 46 ±4 Ω a 20 °C",
        "Válvula electrónica con hilo gris común y varios hilos de fase.",
        "Separar bobina, válvula mecánica y salida de placa.",
        "La resistencia entre gris y cada otro hilo debe ser 46 ±4 Ω (ohmios) a 20 °C; al alimentar se comprueba una secuencia aproximada de 12 V.",
        (
            "Corte tensión antes de desconectar.",
            "Después de moverla manualmente hay que realimentar para que la electrónica recupere posición.",
        ),
        (
            "Desconecte la bobina y mida gris–cada fase.",
            "Conecte, alimente y compruebe la secuencia de 12 V con el método seguro del manual.",
            "Si bobina y mando son correctos, compruebe apertura mecánica por temperatura.",
        ),
        "MULTI_5E",
        "30",
        "31",
        system_type="Multisplit",
        unit_scope="outdoor",
        monitoring=[{"name": "Bobina EEV", "value": "46 ±4 Ω a 20 °C", "unit": "Ω", "notes": "gris a cada fase"}],
    ),
    tv(
        18,
        "EEV — imán de servicio: cinco vueltas para abrir/cerrar",
        "Válvula compatible con imán de servicio Panasonic.",
        "Confirmar bloqueo mecánico sin forzar el motor paso a paso.",
        "Cinco vueltas horarias cierran; cinco antihorarias abren. Tras la prueba se repone alimentación para reinicializar posición.",
        (
            "No aplicar a válvulas sin este procedimiento documentado.",
            "La diferencia de temperatura entre entrada/salida ayuda a confirmar cierre.",
        ),
        (
            "Corte tensión y coloque el imán correcto.",
            "Gire cinco vueltas horarias y compruebe cierre por temperatura.",
            "Gire cinco antihorarias para abrir.",
            "Retire herramienta, reconecte y realimente para inicializar.",
        ),
        "MULTI_5E",
        "30",
        "31",
        system_type="Multisplit",
        unit_scope="outdoor",
    ),
    tv(
        18,
        "Ventilador DC multisplit — 280 V, 15 V y señal 1,8–5,7 V",
        "Motor exterior DC con conectores CN30/CN31 y electrónica interna.",
        "Distinguir motor de placa mediante tensiones.",
        "Valores de referencia: Vm–GND 280 VDC ±10 %, Vcc–GND 15 VDC ±10 % y Vsp–GND variable 1,8–5,7 VDC.",
        (
            "Hay tensión DC peligrosa; solo personal cualificado.",
            "La salida puede cortarse unos 10 s después del disparo y exigir nuevo Test Run.",
        ),
        (
            "Corte tensión para conectar puntas y preparar acceso.",
            "Inicie Test Run y mida Vm, Vcc y Vsp respecto a GND.",
            "Si las tres son normales y no gira, sospeche motor.",
            "Si falta alguna, diagnostique placa/alimentación.",
        ),
        "MULTI_5E",
        "32",
        "33",
        system_type="Multisplit",
        unit_scope="outdoor",
        monitoring=[
            {"name": "Vm", "value": "280 VDC ±10 %", "unit": "VDC", "notes": "CN30"},
            {"name": "Vcc", "value": "15 VDC ±10 %", "unit": "VDC", "notes": "CN31"},
            {"name": "Vsp", "value": "1,8–5,7 VDC", "unit": "VDC", "notes": "variable"},
        ],
    ),
    tv(
        18,
        "Ventilador PACi S-160PE4R — bobinado y bus DC",
        "Motor interior de conductos de 10 polos y 1080 rpm.",
        "Comprobar bobinado antes de sustituir driver o placa.",
        "El manual indica alimentación DC 200–373 V, 3,5 Ω a 20 °C y velocidad nominal 1080 rpm.",
        (
            "La tensión es peligrosa y permanece en condensadores.",
            "Compare todas las fases y aislamiento con el motor desconectado.",
        ),
        (
            "Aísle alimentación y espere descarga del bus.",
            "Mida bobinados a temperatura conocida.",
            "Compruebe aislamiento a tierra.",
            "Solo después mida bus y orden de giro durante prueba.",
        ),
        "PACI_PE4",
        "132",
        "134",
        system_type="PACi conductos",
        unit_scope="indoor",
        monitoring=[
            {"name": "Bobinado motor", "value": "3,5 Ω a 20 °C", "unit": "Ω", "notes": "10 polos"},
            {"name": "Bus motor", "value": "200–373 VDC", "unit": "VDC", "notes": "peligroso"},
        ],
    ),
    tv(
        18,
        "Bomba de drenaje — separar orden, tensión y caudal",
        "Interior con salida de bomba y contacto de nivel independientes.",
        "Evitar sustituir bomba por una boya atascada o placa sin salida.",
        "La prueba correcta verifica orden desde mando, tensión en salida, funcionamiento mecánico y descenso real del agua.",
        (
            "Una bomba que zumba puede estar bloqueada.",
            "Una salida con tensión correcta orienta a bomba/cable; sin tensión, a placa/condición de control.",
        ),
        (
            "Añada agua controlada y active el test de bomba.",
            "Compruebe tensión con el esquema de la familia.",
            "Observe caudal, ruido y descenso de la boya.",
            "Restaure programación normal.",
        ),
        "PACI_PE4",
        "118",
        "123",
        system_type="PACi/cassette",
        unit_scope="indoor",
    ),
    tv(
        19,
        "Umbrales ECOi — H11/H12/H21/H22",
        "VRF con compresores de velocidad fija 2 o 3.",
        "Distinguir sobrecorriente sostenida de rotor bloqueado.",
        "H11/H21: más de 12 A durante 30 s. H12/H22: más de 14 A durante 4 s.",
        (
            "Los pares corresponden a compresores 2 y 3.",
            "Compruebe CT, tensión, fases y presión diferencial además del compresor.",
        ),
        (
            "Registre corriente de cada fase desde el arranque.",
            "Compare duración y pico con el umbral del código.",
            "Revise tensión, CT y compresor antes de rearmar.",
        ),
        "ECOI_CODES",
        "3",
        "4",
        system_type="ECOi/VRF",
        unit_scope="outdoor",
    ),
    tv(
        19,
        "Umbrales ECOi — P02, P03, P04 y H06",
        "Exterior ECOi con alarmas eléctricas/frigoríficas.",
        "Consultar valores de disparo antes de interpretar.",
        "P02: fuera de 160–260 V o sin corriente tras 4 s; P03: descarga >106 °C; P04: alta >3,3 MPa y libera <2,6 MPa; H06: baja <0,05 MPa más de 2 min.",
        (
            "Use unidades correctas y compare sensor con instrumento.",
            "No puentee presostatos ni prolongue marcha sobre descarga alta.",
        ),
        (
            "Registre alarma y valor monitorizado.",
            "Mida con instrumento externo.",
            "Compare con umbral y temporización.",
            "Investigue causa física antes de sustituir sensor.",
        ),
        "ECOI_CODES",
        "3",
        "5",
        system_type="ECOi/VRF",
        unit_scope="outdoor",
    ),
    tv(
        19,
        "CZ-RTC6 — límites rápidos de cableado",
        "Bus de mando R1/R2.",
        "Tener una referencia rápida sin abrir toda la instalación.",
        "0,75–1,25 mm²; 500 m totales; 200 m entre interiores; máximo dos mandos y ocho interiores.",
        (
            "Sin polaridad en esta interfaz.",
            "Separar de potencia y no compartir tubo metálico si induce ruido.",
        ),
        (
            "Mida longitudes y sección real.",
            "Cuente mandos e interiores.",
            "Corrija antes de atribuir Assigning a la placa.",
        ),
        "RTC6_INSTALL",
        "4",
        "5",
        unit_scope="controller",
        controller_profile=RTC6_PROFILE,
    ),
    tv(
        19,
        "Tabla rápida de termistores Panasonic",
        "Consulta por tipo: 15 kΩ/B3950, 20 kΩ/B3950, TH1–TH4 PACi o descarga TH5.",
        "Elegir la curva correcta por familia y función.",
        "La aplicación mantiene curvas separadas y etiqueta las calculadas frente a las tablas oficiales.",
        (
            "No existe una única NTC Panasonic universal.",
            "La tensión de sonda solo se ofrece cuando el circuito está documentado.",
        ),
        (
            "Identifique referencia, función y R25 de la sonda.",
            "Abra la curva correspondiente.",
            "Compare varios puntos, no solo 25 °C.",
        ),
        "CASSETTE",
        "21",
        system_type="Panasonic",
    ),
    tv(
        20,
        "RAC/multisplit — retardo de 3 a 5 minutos del compresor",
        "Ventilador interior funciona pero la exterior tarda tras alimentar o cambiar demanda.",
        "Evitar diagnosticar una espera normal como H11 o placa.",
        "La electrónica espera para equilibrar presiones y proteger el compresor; algunas generaciones multisplit documentan 5 min.",
        (
            "Cronometre desde el evento correcto: alimentación, parada o nuevo termostato ON.",
            "Durante la espera no debe forzarse contactor ni inverter.",
        ),
        (
            "Registre hora de demanda y estado de LEDs.",
            "Espere el retardo completo sin cortar tensión.",
            "Solo diagnostique si termina el tiempo y aparece condición anormal.",
        ),
        "MULTI_5E",
        "18",
        system_type="RAC/multisplit",
    ),
    tv(
        20,
        "Desescarche — ventiladores parados y cuatro vías activa",
        "Calefacción con exterior escarchada, compresor en marcha y ventiladores detenidos.",
        "Reconocer la secuencia normal de desescarche.",
        "En la generación documentada, interiores y exterior paran ventiladores, el compresor trabaja a 70 Hz y la cuatro vías permanece ON.",
        (
            "La duración máxima documentada es 12 min.",
            "Al liberar, el ventilador interior espera para evitar aire frío.",
        ),
        (
            "Observe temperatura exterior/intercambiador y hora de inicio.",
            "Compruebe secuencia sin cortar alimentación.",
            "Si supera límites o no libera, investigue sondas y ciclo.",
        ),
        "MULTI_5E",
        "17",
        "18",
        system_type="Multisplit antiguo",
    ),
    tv(
        20,
        "ECOi — retorno/recuperación de aceite",
        "VRF reduce o modifica operación periódicamente sin código de avería.",
        "Distinguir retorno de aceite de fallo de capacidad.",
        "La lógica mueve refrigerante y aceite entre módulos; durante el proceso cambian frecuencia, EEV y participación de interiores.",
        (
            "La indicación de estado no debe borrarse como alarma.",
            "Una interrupción repetida puede prolongar la recuperación.",
        ),
        (
            "Consulte estado en placa o Service Tool.",
            "Espere a que finalice la secuencia.",
            "Si no termina, revise alarmas y datos de aceite asociados.",
        ),
        "ECOI_W2",
        "210",
        "216",
        system_type="ECOi/VRF",
    ),
    tv(
        20,
        "Calefacción — espera para evitar aire frío",
        "Interior detiene o reduce ventilador al arrancar calor o salir de desescarche.",
        "Evitar sustituir motor cuando la batería aún está fría.",
        "El ventilador interior espera a que el intercambiador alcance temperatura y después aumenta progresivamente.",
        (
            "Compruebe temperatura de batería y estado de compresor.",
            "Si la sonda lee frío permanentemente, la espera puede no terminar.",
        ),
        (
            "Observe lectura de sonda de batería.",
            "Espere la secuencia normal de calentamiento.",
            "Diagnostique sensor/ciclo solo si no alcanza el criterio.",
        ),
        "MULTI_5E",
        "17",
        system_type="RAC/multisplit",
        unit_scope="indoor",
    ),
    tv(
        21,
        "CZ-RTC6 CONEX — H&C Control para instalación y mantenimiento",
        "CZ-RTC6 compatible con Bluetooth/CONEX y aplicación H&C Control.",
        "Realizar ajustes, auto-address, Test Run y consulta de sensores con trazabilidad.",
        "H&C Control reúne detailed maintenance, historial, auto-address, prueba y datos de sensores.",
        (
            "La aplicación no sustituye la identificación de la unidad física.",
            "Registre cambios antes/después para poder revertirlos.",
        ),
        (
            "Empareje solo con el controlador compatible.",
            "Descargue la configuración antes de modificar.",
            "Ejecute la función necesaria y guarde el resultado.",
            "Desconecte la sesión al terminar.",
        ),
        "CONEX",
        "2",
        "3",
        system_type="PACi/ECOi",
        unit_scope="controller",
        controller_profile=RTC6_PROFILE,
    ),
    tv(
        21,
        "H&C Diagnosis — datos en vivo, ciclo y grabación",
        "Aplicación de diagnosis vinculada a CZ-RTC6 CONEX compatible.",
        "Registrar una avería intermitente sin depender de una lectura puntual.",
        "Muestra valores interiores/exteriores, diagrama del ciclo, gráficas, grabación, historial y tablas de códigos.",
        (
            "Compare sensores relacionados y momento del disparo.",
            "Conserve el archivo de registro junto al caso de reparación.",
        ),
        (
            "Seleccione circuito y variables relevantes.",
            "Inicie grabación antes de reproducir el fallo.",
            "Marque hora de síntoma/código.",
            "Exporte y compare la tendencia.",
        ),
        "CONEX",
        "3",
        "4",
        system_type="PACi/ECOi",
        unit_scope="controller",
    ),
    tv(
        21,
        "AC Service Cloud — topología, alarmas y monitor remoto",
        "Instalación conectada a Panasonic AC Smart/Service Cloud.",
        "Orientar diagnóstico remoto y decidir qué medir en campo.",
        "Permite ver topología, alarmas, estado, detalles de exterior, corriente, valores registrados, tablas y gráficas 2D.",
        (
            "Admite ECOi, ECO G, PACi/PACi NX y RAC mediante interfaces compatibles.",
            "Los datos remotos no autorizan a puentear seguridad ni sustituir medición local.",
        ),
        (
            "Seleccione sitio, circuito y unidad afectada.",
            "Revise cronología de alarmas y valores previos.",
            "Prepare una lista de comprobaciones de campo.",
            "Adjunte el registro al informe técnico.",
        ),
        "CLOUD",
        "2",
        "4",
        system_type="Panasonic conectado",
    ),
    tv(
        21,
        "Mando de mantenimiento exterior RCS-TM80BG",
        "Herramienta específica conectada mediante harness de service checker a una exterior ECOi compatible.",
        "Leer EEPROM, alarmas, sensores y estado de conexión desde exterior.",
        "No sustituye a un mando ordinario; se usa con el mazo de servicio indicado para mantenimiento.",
        (
            "Permite revisar datos aun cuando el control interior dificulta el acceso.",
            "Conectar únicamente en el puerto y con el harness correctos.",
        ),
        (
            "Corte o mantenga alimentación según el procedimiento de conexión.",
            "Conecte el service checker harness y el mando de mantenimiento.",
            "Seleccione unidad/dato y registre EEPROM, alarmas y sensores.",
            "Desconecte siguiendo la secuencia segura.",
        ),
        "ECOI_W2",
        "345",
        "350",
        system_type="W-2WAY ECOi",
        unit_scope="outdoor",
    ),
    tv(
        22,
        "Placa interior — restaurar capacidad, dirección y accesorios",
        "PCB interior nueva o reparada con EEPROM vacía/diferente.",
        "Evitar F29, L09 y comportamiento incorrecto tras sustituir.",
        "La nueva placa debe recibir capacidad, dirección, funciones de ventilador/drenaje, sensor y accesorios de la original.",
        (
            "Una placa con la referencia correcta puede seguir necesitando programación.",
            "No reutilice una EEPROM dañada sin procedimiento oficial.",
        ),
        (
            "Antes de retirar, exporte ajustes y fotografíe jumpers/DIP.",
            "Instale y cargue capacidad/dirección.",
            "Restaure funciones de campo.",
            "Ejecute Test Run y lea historial.",
        ),
        "PACI_PE4",
        "173",
        "178",
        system_type="PACi/ECOi",
        unit_scope="indoor",
    ),
    tv(
        22,
        "Placa exterior — EEPROM, dirección y número de módulos",
        "PCB exterior ECOi sustituida en un sistema modular.",
        "Evitar F31, H04, H10, E25 y E26 después del cambio.",
        "Deben restaurarse dirección exterior, rol Main/Sub, capacidad, cantidad de módulos, terminación y opciones de campo.",
        (
            "No energice con dos Main o direcciones repetidas.",
            "La terminación S-LINK forma parte de la puesta en marcha.",
        ),
        (
            "Copie selectores/DIP y ajustes de la placa antigua.",
            "Instale y configure dirección, rol, capacidad y terminador.",
            "Compruebe 30–120 Ω.",
            "Ejecute auto-address y Test Run.",
        ),
        "VRF_MS3",
        "45",
        "64",
        system_type="ECOi/VRF",
        unit_scope="outdoor",
    ),
    tv(
        22,
        "Después de cambiar PCB — validación mínima obligatoria",
        "Cualquier placa Panasonic sustituida.",
        "Cerrar la reparación con pruebas reproducibles.",
        "La validación incluye direcciones, comunicación, sensores, actuadores, drenaje, Test Run e historial limpio.",
        (
            "No declare reparado solo porque desaparece el código al alimentar.",
            "Compruebe al menos un ciclo completo en el modo relevante.",
        ),
        (
            "Compare ajustes antes/después.",
            "Verifique comunicación y Sensor info.",
            "Ejecute Test Run vigilando protecciones.",
            "Revise y documente el historial final.",
        ),
        "PACI_PE4",
        "173",
        "178",
        system_type="Panasonic",
    ),
    tv(
        23,
        "R32 — J07/J08 y válvula de corte de seguridad",
        "Sistema R32 con válvula de corte y detección asociada.",
        "Actuar con seguridad ante un bloqueo de contención.",
        "J07/J08 se relacionan con válvula/cableado o incoherencia del circuito de seguridad; no se debe rearmar hasta ventilar y corregir.",
        (
            "No puentee sensor, EXCT ni válvula de corte.",
            "Compruebe ventilación y ausencia de concentración peligrosa.",
        ),
        (
            "Evacue personas y ventile según el plan de seguridad.",
            "Aísle fuentes de ignición.",
            "Compruebe válvula, cableado y detección.",
            "Rearme solo con el área segura y causa eliminada.",
        ),
        "VRF_MS3",
        "82",
        "86",
        system_type="ECOi R32",
    ),
    tv(
        23,
        "R32 — recuperación, vacío y herramientas compatibles",
        "Equipo R32 que requiere abrir el circuito.",
        "Evitar liberación, mezcla de aire y uso de equipo no compatible.",
        "Se necesita recuperadora, bomba de vacío, botella, manómetros y detector aptos para R32; no purgar con refrigerante.",
        (
            "Calcule la carga y pese lo recuperado.",
            "No use pump down si la exterior no puede almacenar la carga.",
        ),
        (
            "Ventile y elimine fuentes de ignición.",
            "Recupere en botella homologada y pese.",
            "Repare, presurice con nitrógeno y haga vacío.",
            "Cargue por peso y compruebe estanqueidad.",
        ),
        "VRF_MS3",
        "4",
        "21",
        system_type="Panasonic R32",
    ),
    tv(
        23,
        "EXCT / sensor O₂ — P14 no es una sonda de temperatura",
        "ECOi con entrada externa de seguridad configurada.",
        "Evitar buscar una NTC cuando la entrada EXCT está activa.",
        "P14 aparece cuando la exterior recibe señal de O₂/EXCT; la lógica depende de la programación EEPROM de la interior.",
        (
            "Compruebe dispositivo externo, contacto y función programada.",
            "No cortocircuite la entrada para mantener servicio.",
        ),
        (
            "Identifique qué interior aporta la entrada.",
            "Revise valor de programación y estado del contacto.",
            "Compruebe el dispositivo de seguridad.",
            "Rearme solo al recuperar condición segura.",
        ),
        "ECOI_CODES",
        "5",
        system_type="ECOi/VRF",
    ),
    tv(
        24,
        "RAC/split — cómo reconocer la familia",
        "Una interior mural, mando inalámbrico con CHECK y códigos H/F.",
        "Elegir las interpretaciones RAC antes de abrir ECOi.",
        "Los códigos se recuperan por pitidos; AUTO OFF/ON permite marcha forzada y el bus interunidad no es S-LINK.",
        (
            "H11 suele ser comunicación interior–exterior.",
            "H12 suele ser combinación/capacidad, no rotor bloqueado.",
        ),
        (
            "Identifique tipo de mando y LED TIMER.",
            "Lea el código por CHECK.",
            "Seleccione la interpretación RAC/split.",
        ),
        "RAC_PKE",
        "108",
        system_type="RAC/split",
    ),
    tv(
        24,
        "Multisplit — cómo reconocer conexiones y lógica compartida",
        "Una exterior alimenta varias interiores mediante pares A–E o varias válvulas de servicio.",
        "Interpretar capacidad, conflictos y continuidad de otras unidades.",
        "Comparte compresor pero cada conexión puede tener EEV y sensores; cable y tubería deben corresponder.",
        (
            "Una interior satisfecha no detiene necesariamente la exterior.",
            "H41 puede indicar correspondencia incorrecta.",
        ),
        (
            "Cuente conexiones y etiquete interiores.",
            "Registre demanda de todas las unidades.",
            "Seleccione fichas multisplit.",
        ),
        "MULTI_5E",
        "59",
        "61",
        system_type="Multisplit",
    ),
    tv(
        24,
        "PACi — cómo reconocer cassette o conductos",
        "Mando CZ-RTC5/6, interior comercial, bomba/ventilador programables y códigos P.",
        "Llegar rápido a drenaje, presión estática, Test Run y settings.",
        "PACi usa menús Simple/Detailed, Sensor info y Test Run de 60 min; P10/P11/P12 cambian con la arquitectura.",
        (
            "Cassette incorpora boya/bomba; conductos añade presión estática.",
            "No aplique el pinout de un split mural.",
        ),
        (
            "Identifique forma física y mando.",
            "Abra categoría PACi correspondiente.",
            "Confirme el tipo antes de interpretar P10/P12.",
        ),
        "PACI_PE4",
        "112",
        "178",
        system_type="PACi",
    ),
    tv(
        24,
        "ECOi/VRF — cómo reconocer red y alcance",
        "Varias interiores, S-LINK, dirección de circuito, controles centrales y exterior modular.",
        "Seleccionar la interpretación VRF del código repetido.",
        "Los mismos H11/H12/H21 pueden referirse a compresores 2/3, no a comunicación/float de RAC.",
        (
            "Busque dirección, unidad que muestra el código y grupo de letra.",
            "Compruebe 30–120 Ω y terminadores antes de auto-address.",
        ),
        (
            "Identifique topología, circuito y módulo.",
            "Lea código por mando/placa y su dirección.",
            "Abra la interpretación ECOi/VRF y el alcance operativo.",
        ),
        "ECOI_CODES",
        "1",
        "6",
        system_type="ECOi/VRF",
    ),
    tv(
        25,
        "Códigos repetidos — H11, H12, H21, P10 y P12",
        "La búsqueda devuelve varias fichas para el mismo código.",
        "Elegir por arquitectura observable, no por modelo.",
        "H11 puede ser comunicación RAC o 12 A/30 s en compresor ECOi; H12 combinación RAC o 14 A/4 s; H21 float RAC o compresor 3; P10/P12 varían por interior.",
        (
            "La aplicación no decide automáticamente cuál es la máquina.",
            "Cada interpretación mantiene su fuente, comportamiento y comprobaciones.",
        ),
        (
            "Seleccione marca Panasonic y busque el código.",
            "Abra todas las interpretaciones.",
            "Compare tipo de equipo, unidad que lo muestra y comportamiento.",
            "Use solo la ficha que coincide con la arquitectura.",
        ),
        "ECOI_CODES",
        "1",
        "6",
        system_type="Panasonic",
    ),
    tv(
        7,
        "E09/L05/L06 — conflictos de mando y prioridad",
        "Grupo ECOi con dos o más mandos o controles centrales.",
        "Corregir principal/secundario y prioridad sin perder direcciones.",
        "E09 indica dirección o rol duplicado; L05/L06 indican demasiados mandos con o sin prioridad definida.",
        (
            "No puede haber dos mandos Main en el mismo grupo.",
            "La prioridad frío/calor del circuito es distinta del rol Main/Sub del mando.",
        ),
        (
            "Dibuje los mandos y controles conectados al grupo.",
            "Identifique roles y direcciones actuales.",
            "Deje un solo Main y configure los secundarios.",
            "Reinicie y confirme que desaparece el conflicto.",
        ),
        "ECOI_CODES",
        "1",
        "4",
        system_type="ECOi/VRF",
        unit_scope="controller",
    ),
    tv(
        11,
        "PACi — forzar bomba 1 minuto o funcionamiento continuo",
        "CZ-RTC6 en Detailed settings con parámetro de operación automática de bomba.",
        "Probar caudal y drenaje sin esperar a que arranque el compresor.",
        "0000 no fuerza; 0001 fuerza aproximadamente 1 min; 0060 mantiene la bomba en funcionamiento continuo para prueba.",
        (
            "Salir de 0060 al terminar para no dejar la bomba permanentemente activada.",
            "La prueba no confirma por sí sola el buen estado de la boya.",
        ),
        (
            "Prepare agua de prueba y acceso al desagüe.",
            "Entre en Detailed settings y seleccione el ajuste de bomba.",
            "Use 0001 para prueba breve o 0060 bajo supervisión.",
            "Compruebe caudal y restaure 0000.",
        ),
        "PACI_PE4",
        "118",
        "121",
        system_type="PACi",
        unit_scope="indoor",
        controller_profile=RTC6_PROFILE,
        parameters=[
            parameter(
                "Drain pump auto operation",
                "Forzado de bomba",
                "Prueba de la bomba desde servicio.",
                [
                    option("0000", "Sin forzado", "Control normal.", True),
                    option("0001", "Prueba 1 min", "Fuerza la bomba aproximadamente un minuto."),
                    option("0060", "Continuo", "Mantiene la bomba activa hasta restaurar el ajuste."),
                ],
                factory="0000",
                warnings="Restaurar 0000 al terminar.",
            )
        ],
    ),
    tv(
        11,
        "PACi — parada retardada de bomba de 0 a 60 minutos",
        "Conductos/cassette PACi con programación Detailed settings.",
        "Explicar por qué la bomba continúa después de parar el compresor.",
        "El tiempo posterior de bomba puede configurarse entre 0 y 60 min; un funcionamiento posterior puede ser normal.",
        (
            "Antes de diagnosticar relé pegado, consulte el ajuste.",
            "El retardo ayuda a evacuar agua residual.",
        ),
        (
            "Consulte el valor programado sin modificarlo.",
            "Cronometre desde la parada del compresor.",
            "Compare el tiempo real con el ajuste y el estado de la boya.",
        ),
        "PACI_PE4",
        "121",
        "123",
        system_type="PACi",
        unit_scope="indoor",
    ),
    tv(
        11,
        "P11/P12 — no asumir que siempre significan lo mismo",
        "Interior PACi vertical, conductos o cassette de potencia.",
        "Elegir la interpretación de nivel alto, bomba o ventilador según familia.",
        "P11 se usa para nivel alto o bomba en determinadas verticales; P12 puede ser bomba bloqueada o protección de ventilador según la interior.",
        (
            "Identifique tipo de interior y actuador que se detuvo.",
            "Abra todas las interpretaciones antes de sustituir bomba o motor.",
        ),
        (
            "Registre código y tipo físico de unidad.",
            "Observe si funciona bomba, ventilador o ambos.",
            "Compare con la ficha P11/P12 de esa arquitectura.",
        ),
        "PACI_HIGH",
        "143",
        "145",
        system_type="PACi",
        unit_scope="indoor",
    ),
    tv(
        11,
        "Cassette — circuito de boya, bomba y alimentación de 5 V",
        "Esquema con FLOAT SWITCH, DRAIN PUMP TEST y termistores en circuito de 5 V.",
        "Seguir el circuito correcto sin inyectar tensión.",
        "La placa separa la entrada de boya y la salida de bomba; los termistores se leen en un circuito de 5 V.",
        (
            "La tensión de 5 V del circuito de sensores no es alimentación directa de la bomba.",
            "La bomba y la boya deben comprobarse como elementos distintos.",
        ),
        (
            "Corte tensión y localice conectores por el esquema.",
            "Compruebe continuidad del flotador.",
            "Alimente y use el test de bomba documentado.",
            "No puentee permanentemente la entrada de seguridad.",
        ),
        "CASSETTE",
        "21",
        system_type="Cassette",
        unit_scope="indoor",
    ),
    tv(
        20,
        "Bomba continúa después de parar — postdrenaje normal",
        "Cassette o conductos con bomba activa tras detener compresor.",
        "Distinguir relé pegado de tiempo posterior programado.",
        "La bomba puede continuar por retardo de fábrica o ajuste 0–60 min y también por una boya todavía activa.",
        (
            "Cronometre y consulte el ajuste.",
            "Si no para tras el tiempo y la boya está baja, investigue salida o placa.",
        ),
        (
            "Anote instante de parada del compresor.",
            "Compruebe estado de boya y ajuste de postdrenaje.",
            "Espere el tiempo programado antes de diagnosticar.",
        ),
        "PACI_PE4",
        "121",
        "123",
        system_type="PACi/cassette",
        unit_scope="indoor",
    ),
]

TECH_VARIANTS += [
    tv(
        16,
        "ECOi 3 tubos — respaldo automático de compresor o ventilador",
        "Sistema MF1 de 8–16 HP con varios compresores; CHECK parpadea después de una alarma exterior.",
        "Saber si el sistema puede seguir y cómo se cancela el respaldo.",
        "P16, P22, P26, P29, Hx1/Hx2 y H31 pueden iniciar funcionamiento de respaldo; el técnico debe consultar el historial para identificar el elemento aislado.",
        (
            "Después de transmitir la alarma, el respaldo comienza al volver a pulsar ON/OFF y borrar la alarma.",
            "CHECK sigue parpadeando para avisar de funcionamiento degradado.",
            "Tras reparar, el respaldo no se cancela hasta restablecer la alimentación de todas las exteriores.",
        ),
        (
            "Consulte el historial exterior y anote código, dirección y compresor.",
            "Confirme que el sistema tiene un elemento sano capaz de asumir el servicio.",
            "Use el respaldo solo mientras se organiza la reparación.",
            "Después de reparar, restablezca simultáneamente la alimentación de todas las exteriores.",
        ),
        "ECOI_3WAY",
        "1-31",
        "2-8",
        system_type="ECOi 3 tubos",
        unit_scope="system",
    ),
    tv(
        13,
        "ECOi 3 tubos — respaldo manual con DIP S010",
        "Exterior MF1 con compresor inverter y hasta dos compresores de velocidad fija.",
        "Aislar únicamente el compresor averiado cuando el procedimiento oficial lo permite.",
        "S010 combina BACK UP con INV, AC1 y AC2; la posición depende de cuál de los tres compresores haya fallado.",
        (
            "Antes del cambio deben identificarse con certeza el compresor y el código que lo afecta.",
            "El ajuste puede combinar dos compresores aislados, pero reduce mucho la capacidad disponible.",
            "Las válvulas de servicio de la exterior averiada se gestionan según el procedimiento frigorífico.",
        ),
        (
            "Corte la alimentación de todas las exteriores.",
            "Registre la posición original de S010 y seleccione la combinación oficial.",
            "Compruebe carga y presiones durante la puesta en marcha de respaldo.",
            "Después de reparar, devuelva S010 a funcionamiento normal.",
        ),
        "ECOI_3WAY",
        "2-6",
        "2-8",
        system_type="ECOi 3 tubos",
        unit_scope="outdoor",
    ),
    tv(
        21,
        "ECOi 3 tubos — conectar CZ-RTC2 como mando de mantenimiento exterior",
        "Placa exterior con conector RC azul de 3 pines y mazo de servicio CV6231785082.",
        "Consultar EEPROM, sensores, unidades conectadas e historial exterior.",
        "El CZ-RTC2 se conecta mediante el mazo especial; no sustituye al mando ordinario de las interiores y no funciona aquí como mando de usuario.",
        (
            "El mazo enlaza RC 3P azul con un relé/conector blanco de dos pines.",
            "Un mando ordinario debe permanecer conectado para las funciones normales.",
            "Permite Test Run global, monitor de temperaturas, direcciones, horas, EEV e historial.",
        ),
        (
            "Corte tensión e identifique el conector RC de la placa exterior.",
            "Conecte el mazo CV6231785082 y el CZ-RTC2 sin alterar el bus normal.",
            "Alimente y seleccione la dirección exterior que desea monitorizar.",
            "Desconecte el conjunto de servicio con la alimentación cortada.",
        ),
        "ECOI_3WAY",
        "3-2",
        "3-8",
        system_type="ECOi 3 tubos",
        unit_scope="outdoor",
        controller_profile=RTC2_PROFILE,
    ),
    tv(
        21,
        "CZ-RTC2 de mantenimiento — datos que realmente puede leer",
        "CZ-RTC2 conectado a la exterior mediante el mazo de servicio.",
        "Usar datos vivos e históricos antes de sustituir componentes.",
        "El monitor incluye interiores conectadas, modo, temperaturas de entrada/salida, posición EEV, presiones, corriente, horas y ocho alarmas exteriores.",
        (
            "Las alarmas exteriores se guardan de la 1, más reciente, a la 8, más antigua.",
            "La lectura de historial muestra código y número de unidad alternativamente.",
            "Los fallos interiores se consultan por separado desde sus mandos.",
        ),
        (
            "Registre dirección del sistema y de la exterior seleccionada.",
            "Lea primero historial y horas antes de borrar o cortar tensión.",
            "Compare sensores relacionados y no un único valor aislado.",
            "Guarde la ficha de puesta en marcha con modo, carga y temperaturas.",
        ),
        "ECOI_3WAY",
        "3-6",
        "3-11",
        system_type="ECOi 3 tubos",
        unit_scope="outdoor",
        monitoring=(
            {"point_code": "Alarm 1–8", "name": "Historial exterior", "unit": "código/dirección", "notes": "1 es la más reciente"},
            {"point_code": "IDU count", "name": "Interiores conectadas", "unit": "cantidad", "notes": None},
            {"point_code": "EEV", "name": "Posición de válvula interior", "unit": "pasos", "notes": None},
            {"point_code": "Comp hours", "name": "Horas de compresor", "unit": "h", "notes": None},
        ),
    ),
    tv(
        4,
        "ECOi 3 tubos — consultar ocho alarmas exteriores",
        "Mando de mantenimiento exterior en modo normal o monitor.",
        "Recuperar la secuencia de fallos sin mezclarla con las alarmas interiores.",
        "CHECK y el botón indicado durante cuatro segundos abren el historial; la dirección exterior aparece en lugar del número de interior.",
        (
            "Solo contiene alarmas exteriores.",
            "El código y la unidad que lo originó se alternan.",
            "No borre ni restablezca alimentación antes de fotografiar los ocho registros.",
        ),
        (
            "Seleccione la exterior y anote su dirección.",
            "Mantenga CHECK y el botón de historial durante cuatro segundos.",
            "Recorra del registro 1 al 8 y anote código/dirección.",
            "Salga sin modificar EEPROM.",
        ),
        "ECOI_3WAY",
        "3-11",
        system_type="ECOi 3 tubos",
        unit_scope="outdoor",
        controller_profile=RTC2_PROFILE,
    ),
    tv(
        9,
        "ECOi 3 tubos — bombear refrigerante desde una exterior averiada",
        "Sistema modular con una exterior que va a repararse y otras exteriores operativas.",
        "Trasladar refrigerante a módulos sanos/interiores antes de reparar componentes distintos del compresor.",
        "El procedimiento usa CZ-RTC2 de mantenimiento, manómetros y recuperadora; el cierre de válvulas y la parada se coordinan por presión.",
        (
            "La recuperación se realiza con las válvulas de servicio y la exterior seleccionada.",
            "Si no hay mando de mantenimiento, el manual ofrece una variante mediante el conector SCT amarillo CN231.",
            "No es el pump down simple de un split.",
        ),
        (
            "Prepare manómetros, recuperadora y cilindro preevacuado; identifique todas las válvulas.",
            "Conecte CZ-RTC2 al RC azul y arranque Test Run global en frío.",
            "Siga la presión y cierre las válvulas en el orden y momento indicados.",
            "Detenga todas las unidades y confirme presión segura antes de abrir el circuito.",
        ),
        "ECOI_3WAY",
        "2-9",
        "2-22",
        system_type="ECOi 3 tubos",
        unit_scope="system",
        controller_profile=RTC2_PROFILE,
    ),
    tv(
        25,
        "ECOi 3 tubos — interpretar símbolos de alarma y alcance",
        "Tabla de alarmas con códigos entre dobles o simples signos de inspección.",
        "Saber si una alarma afecta a otras interiores o permite servicio parcial.",
        "La leyenda distingue alarmas que no afectan a las otras interiores de otras que, según el caso, sí pueden afectar al sistema.",
        (
            "No debe deducirse el alcance solo por la letra E/F/H/L/P.",
            "El respaldo automático se confirma por CHECK parpadeante y el historial asociado.",
            "La aplicación conserva cada interpretación 3 tubos separada de RAC, PACi y 2 tubos.",
        ),
        (
            "Confirme que la fuente es ECOi 3 tubos.",
            "Abra todas las interpretaciones del código y compare el efecto operativo.",
            "Compruebe si CHECK parpadea y qué módulo continúa funcionando.",
            "No reinicie hasta registrar historial y alcance real.",
        ),
        "ECOI_3WAY",
        "5-2",
        "5-3",
        system_type="ECOi 3 tubos",
        unit_scope="system",
    ),
    tv(
        14,
        "ECOi 3 tubos — auto-address con cantidad incorrecta",
        "Puesta en marcha MF1 con E15, E16 o E20.",
        "Corregir la causa sin repetir auto-address a ciegas.",
        "E15 indica menos interiores que las configuradas, E16 más interiores y E20 ninguna interior reconocida.",
        (
            "E15 puede deberse a cantidad configurada excesiva o interiores sin alimentación/comunicación.",
            "E16 indica recuento superior al previsto o una configuración demasiado baja.",
            "E20 obliga a revisar primero el bus desde la exterior y el conector serie.",
        ),
        (
            "Anote cantidad configurada y cantidad realmente alimentada.",
            "Compruebe continuidad, polaridad/topología y alimentación de todas las interiores.",
            "Corrija direcciones duplicadas y conectores antes de repetir auto-address.",
            "Verifique el recuento final desde el mando de mantenimiento.",
        ),
        "ECOI_3WAY",
        "5-9",
        "5-10",
        system_type="ECOi 3 tubos",
        unit_scope="network",
    ),
    tv(
        22,
        "ECOi 3 tubos — L10 y L17 después de cambiar una placa exterior",
        "Placa exterior de recambio con capacidad o tipo de refrigerante EEPROM sin restaurar.",
        "Evitar que una placa correcta quede bloqueada por datos de modelo.",
        "L10 aparece si la capacidad está a cero/no admitida; L17 puede aparecer si el tipo de refrigerante EEPROM no corresponde a R410A.",
        (
            "El mando de mantenimiento permite revisar item 81, capacidad, e item 80, refrigerante.",
            "No copie valores de otra potencia.",
            "Después de programar deben verificarse direcciones, cantidad y Test Run.",
        ),
        (
            "Antes del cambio registre EEPROM, dirección, capacidad y posición de interruptores.",
            "Conecte el mando de mantenimiento y revise item 80 e item 81.",
            "Introduzca solo los valores documentados para la unidad.",
            "Complete auto-address y Test Run antes de entregar.",
        ),
        "ECOI_3WAY",
        "5-22",
        "5-23",
        system_type="ECOi 3 tubos",
        unit_scope="outdoor",
        controller_profile=RTC2_PROFILE,
    ),
    tv(
        23,
        "ECOi R32 actual — fuga aislada por zona",
        "Sistema 2 tubos R32 con válvula de seguridad por área y detectores compatibles.",
        "Saber qué se para cuando se detecta refrigerante en una zona.",
        "La válvula de seguridad cierra el área afectada y detiene sus interiores; las áreas no afectadas pueden reanudar después de tres minutos en Thermo Off.",
        (
            "El cierre por zona evita parar necesariamente todo el sistema.",
            "Un detector puede asociarse a una interior o grupo según la topología.",
            "No debe abrirse la válvula ni rearmarse antes de ventilar y eliminar la fuga.",
        ),
        (
            "Identifique en plano qué interiores pertenecen a la válvula de la zona.",
            "Ventile, localice y repare la fuga con procedimiento R32.",
            "Compruebe detector, cableado, fuente y válvula de seguridad.",
            "Confirme que solo las áreas sanas reanudan y que la zona reparada queda segura.",
        ),
        "VRF_GEN_2026",
        "R32 safety",
        system_type="ECOi R32",
        unit_scope="zone",
    ),
    tv(
        5,
        "ECOi R32 — detector, mando y alimentación de seguridad",
        "Interior/grupo con detector de fugas y válvula de seguridad R32.",
        "Evitar una topología que invalide la detección o deje dispositivos sin alimentación.",
        "Con detector conectado se admite un único mando cableado en el grupo; el conjunto de dispositivos y su fuente deben respetar la topología del sistema de seguridad.",
        (
            "No se instala un mando Sub cuando la configuración de detector exige un único mando.",
            "La documentación contempla alimentación externa de 16 V con respaldo independiente conforme a EN 378.",
            "El límite de dispositivos incluye interiores, detector y válvula de seguridad.",
        ),
        (
            "Dibuje el grupo y cuente todos los dispositivos conectados.",
            "Compruebe fuente de 16 V, respaldo y continuidad del circuito de seguridad.",
            "Verifique que no existe un segundo mando incompatible.",
            "Ejecute la prueba de seguridad de la puesta en marcha.",
        ),
        "VRF_GEN_2026",
        "R32 safety",
        system_type="ECOi R32",
        unit_scope="group",
    ),
    tv(
        24,
        "Familia — PACi NX mural actual S-25…100PK4R",
        "Interior mural comercial R32 de la serie PK4R, no un RAC doméstico.",
        "Evitar usar el catálogo H/F de RAC cuando la unidad pertenece a PACi.",
        "El manual actual separa placa y controles interiores, catálogo PACi y procedimientos de desmontaje/reparación.",
        (
            "Los códigos PACi se consultan desde el mando compatible y no con el CHECK inalámbrico RAC.",
            "P01/P09/P10/P12 conservan significados de la familia PACi, no del split doméstico.",
            "La capacidad llega a 100 y comparte arquitectura de servicio con PACi NX.",
        ),
        (
            "Confirme que la unidad es PK4R/PACi por etiqueta y mando.",
            "Use el método de lectura CZ-RTC compatible.",
            "Abra la interpretación PACi del código y sus pruebas.",
            "No aplique un procedimiento RAC por coincidencia de letras.",
        ),
        "PACI_WALL",
        "59",
        system_type="PACi NX mural R32",
        unit_scope="indoor",
    ),
    tv(
        17,
        "ECOi 3 tubos — diferenciar sonda abierta de sonda desprendida",
        "Códigos F04/F05/F22 o H05/H15/H25 en una exterior MF1.",
        "No sustituir una sonda eléctricamente correcta que solo ha perdido contacto térmico.",
        "F04/F05/F22 se declaran por circuito abierto/corto o temperatura imposible; H05/H15/H25 detectan que la descarga no cambia como debería con el compresor.",
        (
            "La sonda puede medir correctamente en ohmios y estar fuera del tubo.",
            "El contacto térmico y el aislamiento influyen en la lectura.",
            "Compare evolución de los tres compresores desde el monitor.",
        ),
        (
            "Mida resistencia y continuidad con la alimentación cortada.",
            "Inspeccione inserción, fijación y aislamiento sobre la tubería.",
            "Compare tendencia de descarga con compresor en marcha y parado.",
            "Sustituya solo después de separar sonda, montaje y placa.",
        ),
        "ECOI_3WAY",
        "5-12",
        "5-18",
        system_type="ECOi 3 tubos",
        unit_scope="outdoor",
    ),
    tv(
        17,
        "ECOi 3 tubos — F16 compara sensor y presostato de alta",
        "Exterior muestra F16 aunque la presión medida no parezca extrema.",
        "Distinguir transductor desviado, presostato, cableado o presión real.",
        "F16 puede aparecer si actúa el presostato cuando el sensor indica 3,03 MPa o menos; el manual avisa de que no siempre es un sensor averiado.",
        (
            "Debe compararse manómetro, lectura electrónica y estado del presostato.",
            "Un cierre real del presostato con lectura baja puede indicar incoherencia de señal.",
            "Caudal y exceso de refrigerante también deben descartarse si la presión sí es alta.",
        ),
        (
            "Conecte manómetro y lea alta desde el mando de mantenimiento.",
            "Compruebe el estado eléctrico del presostato y el cableado.",
            "Compare las tres señales durante funcionamiento estable.",
            "Decida entre circuito frigorífico, sensor, presostato o PCB.",
        ),
        "ECOI_3WAY",
        "5-15",
        system_type="ECOi 3 tubos",
        unit_scope="outdoor",
    ),
]


def build_topics() -> list[dict[str, Any]]:
    topics: dict[int, dict[str, Any]] = {}
    for topic_id, category_slug, slug, title, summary in TOPIC_DEFS:
        category = CAT[category_slug]
        topics[topic_id] = {
            "id": topic_id,
            "brand_id": BRAND_ID,
            "category_id": category["id"],
            "slug": slug,
            "title": title,
            "summary": summary,
            "active": 1,
            "category": category,
            "variants": [],
        }

    for variant_id, row in enumerate(TECH_VARIANTS, 1):
        procedures = row["procedures"]
        steps: list[dict[str, Any]] = []
        procedure_no = 0
        for index, instruction in enumerate(procedures):
            if index == 0:
                phase = "prepare"
                number = 1
            elif index == len(procedures) - 1:
                phase = "verify"
                number = 1
            else:
                phase = "procedure"
                procedure_no += 1
                number = procedure_no
            warning = "danger" if any(
                token in normalize(instruction)
                for token in ("PELIGR", "ALTA TENSION", "FUENTE DE IGNICION", "RECUPERADORA")
            ) else "none"
            steps.append(step(phase, number, instruction, warning=warning))

        topic = topics[row["topic_id"]]
        topic["variants"].append({
            "id": variant_id,
            "topic_id": row["topic_id"],
            "title": row["title"],
            "recognition": row["recognition"],
            "system_type": row["system_type"],
            "unit_scope": row["unit_scope"],
            "refrigerant": "R32" if "R32" in row["system_type"] else None,
            "purpose": row["purpose"],
            "summary": row["summary"],
            "source_kind": "official",
            "review_status": "reviewed",
            "sort_order": variant_id,
            "visible": 1,
            "sections": [
                section("recognition", "Cómo reconocer esta variante", row["recognition"], True),
                section("technical", "Qué debe tener en cuenta la máquina", " ".join(row["facts"])),
            ],
            "steps": steps,
            "parameters": row["parameters"],
            "controller": row["controller_profile"],
            "monitoring_points": row["monitoring"],
            "media": [],
            "sources": [
                source(
                    row["ref"],
                    row["page"],
                    row["title"],
                    row["page_end"],
                )
            ],
        })

    missing = [topic["title"] for topic in topics.values() if not topic["variants"]]
    if missing:
        raise RuntimeError(f"Temas sin variantes: {missing}")
    return [topics[topic_id] for topic_id in sorted(topics)]


def build_search(
    topics: list[dict[str, Any]],
    error_indexes: list[dict[str, Any]],
    error_details: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    def synonyms(value: str) -> str:
        norm = normalize(value)
        extra: list[str] = []
        if any(word in norm for word in ("BOYA", "FLOTADOR", "AGUA", "DRENAJE")):
            extra.append("float switch water overflow desbordamiento drain pump bomba condensados")
        if "PUMP DOWN" in norm or "RECUPER" in norm:
            extra.append("recogida refrigerante recovery refrigerant")
        if "MANDO" in norm or "RTC" in norm:
            extra.append("wired controller remote control pared cableado")
        if "COMUNIC" in norm or "S LINK" in norm or "BUS" in norm:
            extra.append("datos transmission red network R1 R2 S-LINK")
        if "DIRECCION" in norm or "ADDRESS" in norm:
            extra.append("auto address autoasignacion commissioning puesta marcha")
        if "SONDA" in norm or "NTC" in norm:
            extra.append("thermistor temperatura resistencia sensor curve curva")
        if "PRUEBA" in norm or "TEST RUN" in norm:
            extra.append("marcha forzada service check maintenance")
        return " ".join([value] + extra)

    for topic in topics:
        category = topic["category"]
        for item in topic["variants"]:
            body = " ".join([
                item["title"],
                item["recognition"],
                item["purpose"],
                item["summary"],
                " ".join(section_item["body"] for section_item in item["sections"]),
                " ".join(
                    (step_item["instruction"] or "") + " " + (step_item["expected_result"] or "")
                    for step_item in item["steps"]
                ),
                " ".join(str(value or "") for value in (item.get("controller") or {}).values()),
                " ".join(
                    " ".join([
                        param["parameter_code"],
                        param["name"],
                        param["description"],
                        *[
                            " ".join([
                                option_item["option_value"],
                                option_item["option_label"],
                                option_item["effect"],
                            ])
                            for option_item in param["options"]
                        ],
                    ])
                    for param in item.get("parameters", [])
                ),
                " ".join(
                    " ".join(str(value or "") for value in point.values())
                    for point in item.get("monitoring_points", [])
                ),
                category["name"],
                topic["title"],
            ])
            entries.append({
                "type": "variant",
                "id": item["id"],
                "topic_id": topic["id"],
                "category_slug": category["slug"],
                "category": category["name"],
                "title": item["title"],
                "summary": item["summary"],
                "haystack": normalize(synonyms(body)),
            })

    details_by_id = {item["id"]: item for item in error_details}
    for index in error_indexes:
        detail = details_by_id[index["id"]]
        interpretation_texts = []
        for interpretation in detail["interpretations"]:
            dataset_text = " ".join(
                " ".join([
                    dataset["name"],
                    dataset["variable_name"],
                    dataset["variable_unit"],
                    dataset["value_name"],
                    dataset["value_unit"],
                    " ".join(
                        " ".join(
                            str(value)
                            for value in (
                                point.get("variable_value"),
                                point.get("value_nominal"),
                                point.get("value_text"),
                            )
                            if value is not None
                        )
                        for point in dataset.get("points", [])
                    ),
                ])
                for dataset in interpretation.get("datasets", [])
            )
            interpretation_texts.append(" ".join(
                [interpretation["title"], interpretation["description"]]
                + [item["body"] for item in interpretation["info_items"]]
                + [dataset_text]
            ))
        body = " ".join([index["search_text"]] + interpretation_texts)
        entries.append({
            "type": "error",
            "id": index["id"],
            "topic_id": None,
            "category_slug": "errors",
            "category": CAT["errors"]["name"],
            "title": f"{index['code_display']} — {index['short_label']}",
            "summary": detail["interpretations"][0]["description"],
            "haystack": normalize(synonyms(body)),
        })
    return entries


def main() -> int:
    expected = (ROOT / "data" / "brands" / "panasonic").resolve()
    if BRAND_DIR.resolve() != expected:
        raise RuntimeError(f"Destino inesperado: {BRAND_DIR}")

    error_indexes, error_details = build_errors()
    topics = build_topics()
    search_entries = build_search(topics, error_indexes, error_details)
    now = datetime.now(timezone.utc).isoformat()

    if WEB_DIR.exists():
        shutil.rmtree(WEB_DIR)
    WEB_DIR.mkdir(parents=True, exist_ok=True)

    topics_by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    variant_map: dict[str, int] = {}
    for topic in topics:
        slug = topic["category"]["slug"]
        topics_by_category[slug].append({
            "id": topic["id"],
            "slug": topic["slug"],
            "title": topic["title"],
            "summary": topic["summary"],
            "active": 1,
            "variant_count": len(topic["variants"]),
        })
        for item in topic["variants"]:
            variant_map[str(item["id"])] = topic["id"]
        write_json(WEB_DIR / "topics" / f"{topic['id']}.json", topic)

    navigation_categories = [
        {
            "id": category_id,
            "slug": slug,
            "name": name,
            "description": description,
            "sort_order": order * 10,
            "active": 1,
            "topics": topics_by_category.get(slug, []),
        }
        for order, (category_id, slug, name, description) in enumerate(CATEGORIES, 1)
    ]

    for detail in error_details:
        write_json(WEB_DIR / "errors" / "details" / f"{detail['id']}.json", detail)
    write_json(WEB_DIR / "errors" / "index.json", error_indexes)
    write_json(WEB_DIR / "search.json", search_entries)
    write_json(WEB_DIR / "variant_map.json", variant_map)

    write_json(WEB_DIR / "sources.json", [
        {
            "id": source_id,
            "title": row["title"],
            "document_ref": row["document_ref"],
            "publication_date": row["publication_date"],
            "language": row["language"],
            "document_type": row["document_type"],
            "source_url": row["source_url"],
            "status": "reviewed",
            "notes": row["notes"],
        }
        for source_id, row in enumerate(SOURCES.values(), 1)
    ])

    coverage_notes = {
        "errors": "RAC, multisplit, PACi, ECOi 2/3 tubos y VRF actual con interpretaciones repetidas separadas.",
        "diagnostic_access": "CHECK inalámbrico, CZ-RTC2/5/6, mando de mantenimiento, display exterior y LED M/N.",
        "history_reset": "Memoria RAC, CZ-RTC6 y ocho alarmas exteriores ECOi 3 tubos.",
        "service_modes": "Test Run, frío/calor forzado, pump down, recuperación modular, respaldo y desescarche.",
        "configuration": "Simple/Detailed settings, EEPROM, capacidad, refrigerante, sensores, presión estática y entradas.",
        "controllers_buses": "CZ-RTC2/5/6, R1/R2, Assigning, S-LINK y comunicación RAC.",
        "drainage_overflow": "P10/P11/P12, boya, bomba, 1/60 min y postdrenaje 0–60 min.",
        "commissioning": "Auto-address, direccionamiento manual, recuento y verificación sin reprogramar.",
        "multisplit": "Capacidad, correspondencia A–E, demanda compartida y H41.",
        "vrf_network": "S-LINK 30–120 Ω, dos terminadores, módulos, respaldo y aislamiento R32 por zona.",
        "component_checks": "NTC, EEV, ventiladores DC, bomba, presión y monitorización.",
        "technical_values": "Curvas oficiales/calculadas, tensiones, resistencias, umbrales y tiempos.",
        "normal_states": "Retardos, desescarche, retorno de aceite, aire frío y postdrenaje.",
        "service_tools_boards": "CONEX, H&C, Service Cloud, CZ-RTC2 de mantenimiento, EEPROM y sustitución de PCB.",
        "system_architecture": "RAC, multi, PACi mural/conductos, ECOi 2/3 tubos, R32 y códigos reutilizados.",
    }
    write_json(WEB_DIR / "coverage.json", [
        {
            "id": category_id,
            "brand_id": BRAND_ID,
            "area_slug": slug,
            "area_name": name,
            "equipment_scope": "Panasonic — corpus Referencia V2",
            "coverage_status": "reference_v2_strong",
            "source_count": len(SOURCES),
            "notes": coverage_notes[slug],
            "last_reviewed": now[:10],
        }
        for category_id, slug, name, _ in CATEGORIES
    ])
    write_json(WEB_DIR / "coverage_matrix.json", {
        "brand": "Panasonic",
        "release": "Referencia V2",
        "coverage_basis": "Información completa respecto a los manuales oficiales enumerados; no se declara cobertura de todos los modelos fabricados.",
        "families": [
            {"family": "RAC/split", "status": "strong", "sources": ["PHAAM0810051C2", "PAPAMY1212045CE"]},
            {"family": "Multisplit", "status": "strong", "sources": ["SM700885-00", "PAPAMY1505100CE"]},
            {"family": "Cassette y PACi", "status": "strong", "sources": ["PAPAMY1503095CE", "PAPAMY2509044CE", "PAPAMY2308067CE", "PAPAMY2509043CE"]},
            {"family": "ECOi 2 tubos", "status": "strong", "sources": ["SM830186-00", "W-2WAY-ECOI-SM"]},
            {"family": "ECOi 3 tubos", "status": "strong", "sources": ["SM830188-00"]},
            {"family": "VRF R32 actual", "status": "strong", "sources": ["U-8_24MS3H7-II-EN", "VRF-GEN-26-LR"]},
            {"family": "Mandos y herramientas", "status": "strong", "sources": ["CZ-RTC2-OM-9L", "CZ-RTC5A-OM", "WEB-ACXF60-38393-EN", "CZ-RTC6-OM-EN", "EU-4P-CZ-RTC6-CONEX-20"]},
        ],
        "known_gaps": [
            "No se extrapolan códigos a familias regionales o generaciones que no figuran en el corpus.",
            "ECO G y determinadas generaciones Mini ECOi pueden añadir procedimientos no documentados aquí.",
            "Los ajustes reservados a fábrica y documentos sin acceso público no se publican.",
        ],
        "counts": {"sources": len(SOURCES), "categories": len(CATEGORIES), "topics": len(topics), "variants": len(variant_map), "errors": len(error_indexes)},
        "last_reviewed": now[:10],
    })

    counts = {
        "categories": len(navigation_categories),
        "topics": len(topics),
        "variants": len(variant_map),
        "errors": len(error_indexes),
        "search_entries": len(search_entries),
    }
    write_json(WEB_DIR / "navigation.json", {
        "metadata": {
            "schema_name": "Super Tecnico",
            "navigation_model": "brand_category_topic_variant",
            "schema_version": "2.2.0",
            "data_version": "2.0.0",
            "last_update_utc": now,
            "reference_brand": "Panasonic",
            "verification_warning": (
                "Completa respecto al corpus oficial Panasonic Referencia V2; no equivale a todos los modelos de la marca. "
                "Confirme siempre arquitectura, unidad que muestra el código y forma de indicación."
            ),
        },
        "categories": navigation_categories,
    })

    brand = {
        "slug": "panasonic",
        "name": "Panasonic",
        "display_name": "Panasonic",
        "enabled": True,
        "web_data": "web",
        "media": "media",
        "publish_media": False,
        "static_site": True,
        "schema_version": "2.2.0",
        "data_version": "2.0.0",
        "exported_at_utc": now,
        "counts": counts,
        "notes": (
            "Panasonic Referencia V2: RAC, multisplit, cassette, PACi mural/conductos, "
            "ECOi 2/3 tubos, VRF R32, CZ-RTC2/5/6, respaldo, drenaje y servicio."
        ),
    }
    write_json(BRAND_DIR / "brand.json", brand)

    from audit_brand_quality import audit_brand

    quality = audit_brand(BRAND_DIR)
    write_json(WEB_DIR / "quality.json", quality)
    print(json.dumps({
        "brand": brand["slug"],
        "counts": counts,
        "interpretations": quality["errors"]["interpretations"],
        "error_quality": quality["errors"]["status_counts"],
        "variant_quality": quality["technical_variants"]["status_counts"],
        "sources": len(SOURCES),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
