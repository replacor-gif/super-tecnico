#!/usr/bin/env python3
"""Construye Gree Referencia V1 para Super Técnico.

La proyección pública contiene resúmenes técnicos, referencias y páginas
verificadas. No se publican PDF, capturas ni bases SQLite.
"""

from __future__ import annotations

import json
import re
import shutil
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BRAND_DIR = ROOT / "data" / "brands" / "gree"
WEB_DIR = BRAND_DIR / "web"
BRAND_ID = 5
BASE = "https://www.greecomfort.com/assets/"


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
    "ENVO": {
        "title": "Service Manual — Envo R32",
        "document_ref": "ENVO-R32-SM-A",
        "publication_date": "2024",
        "language": "en",
        "document_type": "service_manual",
        "source_url": BASE + "our-products/envo-r32/documents/envo-r32-service-manual-a.pdf",
        "notes": "Split R32 actual: estados operativos, códigos, comunicación, componentes y curvas NTC.",
    },
    "LIVO": {
        "title": "Service Manual — Livo GEN3 9–24K 230 V",
        "document_ref": "LIVO-GEN3-SM-230V-A",
        "publication_date": "2020",
        "language": "en",
        "document_type": "service_manual",
        "source_url": BASE + "our-products/livo-gen3/documents/livo-gen3-service-manual-9k-24k-230v-a.pdf",
        "notes": "Split de generación anterior para contrastar códigos y procedimientos.",
    },
    "VIREO": {
        "title": "Service Manual — Vireo GEN3",
        "document_ref": "VIREO-GEN3-SM-A",
        "publication_date": "2021",
        "language": "en",
        "document_type": "service_manual",
        "source_url": BASE + "our-products/vireo-gen3/documents/vireo-gen3-service-manual-a.pdf",
        "notes": "Split inverter: efecto operativo de protecciones y estados que no son avería.",
    },
    "SLIM": {
        "title": "Service Manual — Slim Duct",
        "document_ref": "SLIM-DUCT-SM-A",
        "publication_date": "2016",
        "language": "en",
        "document_type": "service_manual",
        "source_url": BASE + "our-products/slim-duct/documents/slim-duct-service-manual-a.pdf",
        "notes": "Conductos de generación anterior: E9, sensores, presión y consulta desde mando.",
    },
    "CASS9": {
        "title": "Service Manual — All Match 360 Cassette R32 9–24K",
        "document_ref": "ALL-MATCH-360-R32-9-24-SM-A",
        "publication_date": "2024",
        "language": "en",
        "document_type": "service_manual",
        "source_url": BASE + "our-products/all-match-360-cassette-r32/documents/all-match-360-cassette-r32-service-manual-9k-24k-a.pdf",
        "notes": "Cassette actual: boya, bomba, bus de mando, LED y lista de errores.",
    },
    "CASS30": {
        "title": "Service Manual — All Match 360 Cassette R32 30–36K",
        "document_ref": "ALL-MATCH-360-R32-30-36-SM-A",
        "publication_date": "2024",
        "language": "en",
        "document_type": "service_manual",
        "source_url": BASE + "our-products/all-match-360-cassette-r32/documents/all-match-360-cassette-r32-service-manual-30k-36k-a.pdf",
        "notes": "Cassette/comercial de mayor potencia: PCB, drenaje, errores y valores.",
    },
    "GMV5O": {
        "title": "Service Manual — GMV5 Mini DC Inverter Side Discharge VRF II",
        "document_ref": "GMV5-MINI-HP-SM",
        "publication_date": "2020",
        "language": "en",
        "document_type": "service_manual",
        "source_url": BASE + "our-products/multipro/documents/gmv5-mini-heat-pump-service-manual.pdf",
        "notes": "VRF lateral: CAN, Commissioning Tool, depuración, estados y errores.",
    },
    "GMV5I": {
        "title": "Service Manual — GMV5 Indoor Units",
        "document_ref": "GMV5-IDU-SM",
        "publication_date": "2021",
        "language": "en",
        "document_type": "service_manual",
        "source_url": BASE + "our-products/multipro/documents/gmv5-indoor-units-service-manual.pdf",
        "notes": "Interiores VRF: errores desarrollados, LED, drenaje y emergencia modular.",
    },
    "GMV6": {
        "title": "Service Manual — GMV6 Ultra Heat Mini 208/230 V",
        "document_ref": "GMV6-UH-MINI-SM",
        "publication_date": "2024",
        "language": "en",
        "document_type": "service_manual",
        "source_url": BASE + "our-products/multipro/documents/gmv6-ultra-heat-mini-heat-pump-208-230v-service-manual.pdf",
        "notes": "VRF actual: puesta en marcha, funciones de placa, historial, componentes y tablas.",
    },
    "XK19": {
        "title": "Technical Product Guide — Wired Controller XK19",
        "document_ref": "XK19-TPG",
        "publication_date": "2014",
        "language": "en",
        "document_type": "technical_guide",
        "source_url": BASE + "documents/controllers/xk19-wired-controller/xk19-technical-product-guide.pdf",
        "notes": "Mando antiguo con cable de comunicación premontado de 26 ft.",
    },
    "XK46": {
        "title": "Owner's Manual — Wired Controller XK46",
        "document_ref": "XK46-OM",
        "publication_date": "2016",
        "language": "en/es",
        "document_type": "controller_manual",
        "source_url": BASE + "documents/controllers/xk46-wired-controller/xk46-owner-s-manual.pdf",
        "notes": "Mando de dos hilos H1/H2: consulta C00/C01 y programación P00.",
    },
    "XK79": {
        "title": "Owner's Manual — Wired Controller XK62/XK79",
        "document_ref": "XK62-XK79-OM",
        "publication_date": "2018",
        "language": "en",
        "document_type": "controller_manual",
        "source_url": BASE + "documents/controllers/xk79-wired-controller/xk79-owner-s-manual.pdf",
        "notes": "Mando VRF actual: parámetros, tablas de errores, estados y control de acceso.",
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
    (1, "errors", "Errores y protecciones", "Códigos split, cassette, conductos y GMV con significados alternativos."),
    (2, "diagnostic_access", "Obtención de códigos y subcódigos", "Lectura desde mandos, displays, LED y placa exterior."),
    (3, "history_reset", "Historial y borrado", "Consulta n6, memoria de placa y salida segura."),
    (4, "service_modes", "Modos de servicio", "Pump down, vacío, desescarche forzado y emergencia."),
    (5, "configuration", "Configuración y programación", "Parámetros de mando, DIP, capacidad y funciones de placa."),
    (6, "controllers_buses", "Mandos y buses", "XK19, XK46, XK79, H1/H2, D1/D2 y comunicación split."),
    (7, "drainage_overflow", "Drenaje y desbordamiento", "Bomba, boya, detección E9/L3 y diferencias por familia."),
    (8, "commissioning", "Puesta en marcha", "Test, auto-debug, precalentamiento y validación de instalación."),
    (9, "multisplit", "Multisplit", "Compatibilidad, modo maestro, grupo y efectos sobre unidades."),
    (10, "gmv_network", "GMV, MultiPRO y red CAN", "Direcciones, proyecto, cantidad de interiores y red de transmisión."),
    (11, "component_checks", "Comprobación de componentes", "NTC, EEV, válvulas, compresor, IPM, ventilador y presión."),
    (12, "technical_values", "Valores técnicos", "Curvas 15/20/50 kΩ, tensión de sondas, bus y bobinas."),
    (13, "normal_states", "Comportamientos normales", "A0–A9, desescarche, retorno de aceite, esperas y limitaciones."),
    (14, "service_tools_boards", "Herramientas y placas", "Commissioning Tool, sustitución de PCB y recuperación de ajustes."),
    (15, "system_architecture", "Arquitectura de sistemas", "Pistas para reconocer split, cassette, conductos, MultiPRO y GMV."),
]
CAT = {slug: {"id": i, "slug": slug, "name": name, "description": desc}
       for i, slug, name, desc in CATEGORIES}


def operational_impact(text: str) -> dict[str, Any]:
    norm = normalize(text)
    if "TODO EL SISTEMA" in norm or "UNIDAD COMPLETA" in norm or "TODAS LAS CARGAS" in norm:
        level = "all_system"
    elif "UNIDAD AFECTADA" in norm or "MANDO AFECTADO" in norm:
        level = "affected_unit"
    elif "CONTINUA" in norm or "ESTADO" in norm or "REINTENTO" in norm:
        level = "warning"
    else:
        level = "protected_stop"
    return {
        "stop_level": level,
        "summary": text,
        "affected_scope": "Alcance documentado para esta familia Gree.",
        "unaffected_scope": None,
        "restart_behavior": "Corregir la causa y aplicar el rearme descrito para la familia.",
        "degraded_behavior": None,
        "notes": "No extrapolar este efecto a otra familia que use el mismo código.",
    }


NTC_15K = [(-20, 144.0, 0.311), (0, 49.02, 0.773), (10, 29.9, 1.102),
           (20, 18.75, 1.466), (25, 15.0, 1.65), (40, 7.967, 2.155),
           (60, 3.711, 2.646), (80, 1.871, 2.934), (100, 1.009, 3.092)]
NTC_20K = [(-20, 196.9, None), (0, 65.37, None), (10, 39.87, None),
           (20, 25.01, 1.466), (25, 20.0, 1.65), (40, 10.62, 2.155),
           (60, 4.948, 2.646), (80, 2.495, 2.934), (100, 1.346, None)]
NTC_50K = [(-20, 486.55, None), (0, 161.02, None), (10, 98.006, None),
           (20, 61.478, None), (25, 49.191, None), (40, 26.147, None),
           (60, 12.168, None), (80, 6.1288, None), (100, 3.3147, None)]


def curve_dataset(dataset_id: int, name: str, points: list[tuple[float, float, float | None]]) -> dict[str, Any]:
    return {
        "id": dataset_id,
        "name": name,
        "dataset_type": "sensor_curve",
        "variable_name": "Temperatura",
        "variable_unit": "°C",
        "value_name": "Resistencia",
        "value_unit": "kΩ",
        "tolerance_text": "Aplicar únicamente al tipo de NTC y familia indicados.",
        "source_kind": "official",
        "calculation_method": None,
        "review_status": "reviewed",
        "notes": "La tabla oficial incluye más puntos; se muestran referencias de trabajo.",
        "visible": 1,
        "points": [
            {
                "variable_value": temp,
                "value_min": None,
                "value_nominal": resistance,
                "value_max": None,
                "value_text": f"{voltage} VDC" if voltage is not None else None,
                "sort_order": order,
                "notes": "Tensión oficial cuando consta en el apéndice.",
            }
            for order, (temp, resistance, voltage) in enumerate(points)
        ],
        "sources": [source("GMV6", "97", "Temperature sensor resistance and voltage tables", "104")],
    }


def infer_diagnostics(title: str) -> tuple[list[str], list[str]]:
    norm = normalize(title)
    if "SENSOR" in norm or "SONDA" in norm or "TEMPERATURA" in norm:
        return (
            ["Sonda abierta, en cortocircuito o fuera de curva", "Conector, cableado o contacto térmico defectuoso", "Circuito de lectura de la PCB"],
            ["Medir la sonda desconectada y compararla con su curva", "Revisar continuidad, conector y fijación", "Comparar el valor real con la lectura de monitor antes de condenar la placa"],
        )
    if "COMUNIC" in norm or "NETWORK" in norm or "ADDRESS" in norm or "DIRECCION" in norm:
        return (
            ["Unidad sin alimentación o dirección repetida/incorrecta", "Bus abierto, cruzado, en corto o con interferencias", "PCB o interfaz de comunicación defectuosa"],
            ["Confirmar alimentación en cada nodo", "Revisar continuidad, bornes, tipo de bus y direcciones", "Aislar tramos o equipos y repetir la inicialización"],
        )
    if "PRESION" in norm or "PRESSURE" in norm:
        return (
            ["Presión real fuera de rango por caudal, carga, válvula o obstrucción", "Transductor/presostato o cableado defectuoso", "Entrada de PCB incorrecta"],
            ["Medir con manómetro y comparar con la lectura del sistema", "Revisar ventiladores, intercambiadores, válvulas y carga", "Comprobar señal del transductor con la tabla oficial"],
        )
    if "FAN" in norm or "VENTILADOR" in norm or "MOTOR" in norm:
        return (
            ["Motor o rodete bloqueado", "Alimentación, conector o realimentación anormales", "Driver o placa defectuosos"],
            ["Comprobar giro libre con alimentación cortada", "Medir bobinados/alimentaciones según la familia", "Separar motor y driver antes de sustituir la placa"],
        )
    if "COMPRESOR" in norm or "INVERTER" in norm or "IPM" in norm or "DRIVE" in norm:
        return (
            ["Compresor, módulo de potencia o cable U/V/W defectuosos", "Alimentación/bus DC fuera de rango", "Carga frigorífica o presiones anormales"],
            ["Comprobar resistencias iguales y aislamiento a tierra", "Medir red y bus DC con procedimiento seguro", "Revisar presiones, ventilación e IPM/driver"],
        )
    if "BOYA" in norm or "AGUA" in norm or "DRENA" in norm or "WATER" in norm:
        return (
            ["Boya activada o bloqueada", "Bomba o desagüe obstruidos/defectuosos", "Cableado o PCB interior"],
            ["Comprobar agua real, pendiente y obstrucciones", "Verificar actuación de boya y bomba", "Rearmar solo después de eliminar la causa"],
        )
    if "MANDO" in norm or "CONTROLLER" in norm:
        return (
            ["Cable H1/H2 o alimentación del mando", "Dirección Main/Sub o número de mandos incorrectos", "PCB del mando o interior"],
            ["Revisar dos hilos, bornes y separación de potencia", "Comprobar parámetros P13/P14 o equivalentes", "Probar con un mando conocido compatible"],
        )
    return (
        ["Componente o condición indicada por el código", "Cableado, conector o ajuste incorrecto", "PCB de control defectuosa"],
        ["Confirmar familia, modo y forma de indicación", "Inspeccionar el elemento y su cableado", "Corregir la causa y verificar mediante Test Run"],
    )


def behavior_for(scope: str, title: str) -> str:
    norm = normalize(title)
    if "ESTADO" in norm or "DEBUG" in norm or "DEFROST" in norm or "OIL RETURN" in norm:
        return "Es un estado o función; la máquina continúa la secuencia correspondiente y no debe tratarse como avería."
    if scope == "controller":
        return "El mando afectado pierde total o parcialmente el control; confirme si las demás unidades siguen operativas."
    if scope == "indoor":
        return "La unidad interior afectada se protege; el resto del sistema depende de la topología y del código exterior asociado."
    if scope == "outdoor":
        return "La unidad exterior limita o detiene el compresor/actuador afectado hasta recuperar una condición válida."
    return "La puesta en marcha o el funcionamiento del sistema se limita o bloquea mientras persiste la condición."


def spec(code: str, title: str, scope: str, ref: str, page: str,
         description: str = "", behavior: str = "", aliases: str = "",
         causes: list[str] | None = None, checks: list[str] | None = None) -> dict[str, Any]:
    inferred_causes, inferred_checks = infer_diagnostics(title)
    return {
        "code": code, "title": title, "scope": scope, "ref": ref, "page": page,
        "description": description or f"Interpretación documentada de {code} para {title.lower()}.",
        "behavior": behavior or behavior_for(scope, title),
        "aliases": [x.strip() for x in aliases.split("|") if x.strip()],
        "causes": causes or inferred_causes,
        "checks": checks or inferred_checks,
    }


SPLIT_ROWS = [
    ("C5", "Jumper de capacidad ausente o incorrecto", "indoor", "60"),
    ("E6", "Comunicación entre interior y exterior", "system", "60"),
    ("H5", "Protección IPM", "outdoor", "60"),
    ("L3", "Ventilador exterior 1 / motor DC", "outdoor", "60"),
    ("LA", "Ventilador exterior 2 / motor DC", "outdoor", "60"),
    ("H3", "Sobrecarga del compresor", "outdoor", "60"),
    ("F0", "Refrigerante insuficiente o circuito cortado", "system", "60"),
    ("F1", "Sonda de ambiente interior", "indoor", "60"),
    ("F2", "Sonda de evaporador interior", "indoor", "60"),
    ("H6", "Sin realimentación del ventilador interior", "indoor", "60"),
    ("LP", "Capacidad interior/exterior incompatible", "system", "60"),
    ("C4", "Jumper de capacidad exterior ausente", "outdoor", "60"),
    ("b7", "Sonda de válvula de gas", "outdoor", "60"),
    ("b5", "Sonda de válvula de líquido", "outdoor", "61"),
    ("E1", "Protección de alta presión", "system", "61"),
    ("E3", "Protección de baja presión", "system", "61"),
    ("E4", "Temperatura de descarga alta", "outdoor", "61"),
    ("E5", "Sobrecorriente AC", "outdoor", "61"),
    ("E7", "Conflicto de modo en multisplit", "system", "61"),
    ("E8", "Prevención por temperatura elevada", "system", "61"),
    ("EE", "EEPROM exterior", "outdoor", "61"),
    ("Fo", "Modo de recuperación de refrigerante", "system", "61"),
    ("F3", "Sonda de ambiente exterior", "outdoor", "61"),
    ("F4", "Sonda del condensador exterior", "outdoor", "62"),
    ("F5", "Sonda de descarga exterior", "outdoor", "62"),
    ("FC", "Microinterruptor o puerta deslizante", "indoor", "62"),
    ("H4", "Sistema frigorífico anormal", "system", "62"),
    ("H7", "Desincronización del compresor", "outdoor", "62"),
    ("HC", "Protección PFC", "outdoor", "62"),
    ("HE", "Desmagnetización del compresor", "outdoor", "62"),
    ("JF", "Comunicación interior–placa de inspección", "controller", "62"),
    ("L1", "Sonda de humedad / placa de inspección", "indoor", "62"),
    ("L9", "Protección de potencia elevada", "outdoor", "62"),
    ("Lc", "Fallo de arranque del compresor", "outdoor", "62"),
    ("Ld", "Pérdida de fase del compresor", "outdoor", "62"),
    ("P5", "Sobrecorriente de fase del compresor", "outdoor", "62"),
    ("oE", "Error exterior no definido", "outdoor", "63"),
    ("P6", "Comunicación entre placa principal y driver", "outdoor", "63"),
    ("P7", "Circuito de sonda de temperatura del módulo", "outdoor", "63"),
    ("P8", "Sobretemperatura del módulo", "outdoor", "63"),
    ("Pf", "Sonda ambiente de la placa driver", "outdoor", "63"),
    ("PH", "Bus DC demasiado alto", "outdoor", "63"),
    ("PL", "Bus DC demasiado bajo", "outdoor", "63"),
    ("PU", "Fallo de carga del condensador", "outdoor", "63"),
    ("rF", "Módulo RF", "controller", "63"),
    ("U1", "Circuito de detección de corriente de fase", "outdoor", "63"),
    ("U2", "Pérdida de fase del compresor", "outdoor", "63"),
    ("U3", "Caída de tensión del bus DC", "outdoor", "64"),
    ("U5", "Detección de corriente de la unidad", "outdoor", "64"),
    ("U7", "Válvula de cuatro vías anormal", "outdoor", "64"),
    ("U8", "Cruce por cero de la unidad interior", "indoor", "64"),
    ("U9", "Cruce por cero de la unidad exterior", "outdoor", "64"),
    ("E2", "Antihielo del evaporador — estado", "indoor", "64"),
    ("E9", "Prevención de aire frío — estado", "indoor", "64"),
    ("EA", "Alarma de fuga de refrigerante", "system", "64"),
]


GMV_ROWS = [
    ("A0", "Esperando depuración/commissioning", "system", "37"),
    ("A2", "Pump down / recuperación de refrigerante", "system", "37"),
    ("A3", "Desescarche", "system", "37"),
    ("A4", "Retorno de aceite", "system", "37"),
    ("A6", "Ajuste bomba de calor", "system", "37"),
    ("A7", "Modo silencioso exterior", "system", "37"),
    ("A8", "Modo de vacío de mantenimiento", "system", "37"),
    ("A9", "Funcionamiento Setback", "system", "37"),
    ("Ab", "Parada de emergencia local", "system", "37"),
    ("AC", "Estado de refrigeración", "system", "37"),
    ("AE", "Carga manual de refrigerante en depuración", "system", "37"),
    ("AF", "Estado ventilación", "system", "37"),
    ("AH", "Estado calefacción", "system", "37"),
    ("AJ", "Recordatorio de limpieza de filtro", "indoor", "37"),
    ("AP", "Confirmación de depuración", "system", "37"),
    ("AU", "Parada de emergencia remota", "system", "37"),
    ("Ay", "Limitación remota desde BMS/central", "system", "37"),
    ("b1", "Sonda ambiente exterior RT7 — 15 kΩ", "outdoor", "38"),
    ("b2", "Sonda de desescarche RT3 — 20 kΩ", "outdoor", "38"),
    ("b4", "Sonda salida líquido subenfriador RT5 — 20 kΩ", "outdoor", "38"),
    ("b5", "Sonda salida gas subenfriador RT4 — 20 kΩ", "outdoor", "38"),
    ("b6", "Sonda entrada acumulador RT1 — 20 kΩ", "outdoor", "38"),
    ("b7", "Sonda salida acumulador RT2 — 20 kΩ", "outdoor", "38"),
    ("bd", "Sonda entrada gas subenfriador RT6 — 20 kΩ", "outdoor", "38"),
    ("bH", "Reloj del sistema", "outdoor", "38"),
    ("bJ", "Transductores de alta y baja invertidos", "outdoor", "38"),
    ("C0", "Comunicación IDU–ODU–mando", "system", "38"),
    ("C1", "Comunicación control principal–convertidor DC/DC", "outdoor", "38"),
    ("C2", "Comunicación control principal–driver compresor", "outdoor", "38"),
    ("C3", "Comunicación control principal–driver ventilador", "outdoor", "38"),
    ("C4", "Faltan unidades interiores", "system", "39"),
    ("C5", "Número de proyecto/dirección interior duplicado", "network", "39"),
    ("CH", "Capacidad interior conectada superior al 135 %", "system", "39"),
    ("CL", "Capacidad interior conectada inferior al 50 %", "system", "39"),
    ("CP", "Varios mandos configurados como maestro", "controller", "39"),
    ("d1", "PCB de unidad interior", "indoor", "39"),
    ("d3", "Sonda de ambiente interior — 15 kΩ", "indoor", "39"),
    ("d4", "Sonda de entrada de tubería — 20 kΩ", "indoor", "39"),
    ("d5", "Sonda intermedia de tubería — 20 kΩ", "indoor", "39"),
    ("d6", "Sonda de salida de tubería — 20 kΩ", "indoor", "39"),
    ("d7", "Sonda de humedad interior", "indoor", "39"),
    ("d9", "Jumper de capacidad interior", "indoor", "39"),
    ("db", "Estado de depuración de campo", "system", "39"),
    ("dC", "DIP de capacidad interior incorrecto", "indoor", "39"),
    ("dH", "PCB del mando cableado", "controller", "39"),
    ("dL", "Sonda de impulsión — 15 kΩ", "indoor", "39"),
    ("dn", "Conjunto de lamas bloqueado", "indoor", "40"),
    ("E0", "Código acompañante de fallo exterior", "outdoor", "40"),
    ("E1", "Alta presión — 609 psi", "outdoor", "40"),
    ("E2", "Descarga a baja temperatura", "outdoor", "40"),
    ("E3", "Baja presión", "outdoor", "40"),
    ("E4", "Descarga del compresor superior a 244 °F", "outdoor", "40"),
    ("Ed", "Temperatura interna IPM inferior al ambiente", "outdoor", "40"),
    ("F0", "Placa principal exterior / memoria", "outdoor", "40"),
    ("F1", "Transductor de alta presión CN425", "outdoor", "40"),
    ("F3", "Transductor de baja presión CN426", "outdoor", "40"),
    ("F5", "Sonda de descarga RT8 — 50 kΩ", "outdoor", "40"),
    ("FP", "Motor DC exterior", "outdoor", "40"),
    ("H0", "Placa driver de ventilador", "outdoor", "40"),
    ("H1", "Funcionamiento anormal del driver de ventilador", "outdoor", "40"),
    ("H2", "Alimentación del driver de ventilador", "outdoor", "40"),
    ("H3", "Reset del módulo driver de ventilador", "outdoor", "40"),
    ("H4", "PFC del ventilador", "outdoor", "40"),
    ("H5", "Sobrecorriente del ventilador inverter", "outdoor", "40"),
    ("H6", "Protección IPM del ventilador", "outdoor", "40"),
    ("H7", "Sonda de temperatura del driver de ventilador", "outdoor", "40"),
    ("H8", "Sobretemperatura IPM de ventilador", "outdoor", "40"),
    ("H9", "Desincronización del ventilador inverter", "outdoor", "40"),
    ("HA", "Memoria del driver de ventilador", "outdoor", "40"),
    ("HC", "Detección de corriente del driver de ventilador", "outdoor", "41"),
    ("HE", "Pérdida de fase del ventilador inverter", "outdoor", "41"),
    ("HF", "Circuito de carga del driver de ventilador", "outdoor", "41"),
    ("HH", "Sobretensión del bus DC del ventilador", "outdoor", "41"),
    ("HJ", "Fallo de arranque del ventilador inverter", "outdoor", "41"),
    ("HL", "Baja tensión del bus DC del ventilador", "outdoor", "41"),
    ("HP", "Protección de corriente AC del ventilador", "outdoor", "41"),
    ("HU", "Tensión de entrada AC del ventilador", "outdoor", "41"),
    ("J1", "Sobrecorriente del compresor 1", "outdoor", "41"),
    ("J7", "Mezcla de gas / válvula de cuatro vías", "outdoor", "41"),
    ("J8", "Relación de presión alta", "outdoor", "41"),
    ("J9", "Relación de presión baja", "outdoor", "41"),
    ("JA", "Presión anormal", "outdoor", "41"),
    ("JL", "Alta presión demasiado baja", "outdoor", "41"),
    ("L0", "Fallo general de unidad interior", "indoor", "41"),
    ("L1", "Protección del ventilador interior", "indoor", "41"),
    ("L3", "Boya abierta / bandeja llena", "indoor", "41"),
    ("L4", "Alimentación anormal del mando", "controller", "41"),
    ("L5", "Protección antihielo", "indoor", "41"),
    ("L6", "Conflicto de modo", "system", "41"),
    ("L7", "No existe unidad interior maestra", "system", "41"),
    ("L8", "Alimentación insuficiente de la interior", "indoor", "42"),
    ("L9", "Cantidad de interiores de grupo incorrecta", "controller", "42"),
    ("LA", "Series incompatibles en control de grupo", "controller", "42"),
    ("Lb", "Interiores incompatibles en deshumidificación con recalentamiento", "system", "42"),
    ("LC", "Unidad interior incompatible con la exterior", "system", "42"),
    ("LH", "Aviso de mala calidad de aire", "indoor", "42"),
    ("LJ", "DIP de función interior incorrecto", "indoor", "42"),
    ("LL", "Interruptor de caudal de agua", "indoor", "42"),
    ("LP", "Cruce por cero del motor PG", "indoor", "42"),
    ("LU", "Incompatibilidad de rama/grupo", "system", "42"),
]


XK79_EXTRA = [
    ("FL", "Sensor de corriente del compresor 3", "outdoor"),
    ("Fn", "Sonda de entrada del intercambiador de modo", "outdoor"),
    ("FU", "Temperatura de carcasa del compresor 2", "outdoor"),
    ("J2", "Sobrecorriente del compresor 2", "outdoor"),
    ("J3", "Sobrecorriente del compresor 3", "outdoor"),
    ("J4", "Sobrecorriente del compresor 4", "outdoor"),
    ("J5", "Sobrecorriente del compresor 5", "outdoor"),
    ("J6", "Sobrecorriente del compresor 6", "outdoor"),
    ("J9", "Relación de presión insuficiente", "outdoor"),
    ("JC", "Protección de interruptor de caudal", "system"),
    ("JE", "Tubería de retorno de aceite obstruida", "outdoor"),
    ("JF", "Fuga en tubería de retorno de aceite", "outdoor"),
    ("P0", "Fallo general de placa driver de compresor", "outdoor"),
    ("P1", "Funcionamiento anormal del driver de compresor", "outdoor"),
    ("P2", "Alimentación del driver de compresor", "outdoor"),
    ("P3", "Reset del módulo driver de compresor", "outdoor"),
    ("bA", "Sonda de retorno de aceite", "outdoor"),
    ("bC", "Sonda de carcasa del compresor 1 desprendida", "outdoor"),
    ("bE", "Sonda de entrada del condensador", "outdoor"),
    ("bF", "Sonda de salida del condensador", "outdoor"),
    ("LF", "Ajuste de válvula de derivación", "indoor"),
    ("LJ", "DIP de función interior incorrecto", "indoor"),
    ("LP", "Cruce por cero de motor PG", "indoor"),
    ("dE", "Sensor de CO₂ interior", "indoor"),
    ("y7", "Sonda de aire fresco de entrada", "indoor"),
    ("y8", "Sonda de caja de aire interior", "indoor"),
    ("y9", "Sonda de caja de aire exterior", "indoor"),
]

VIREO_EXTRA = [
    ("EU", "Limitación de frecuencia por temperatura elevada del módulo", "outdoor", "49"),
    ("F6", "Limitación de frecuencia por sobrecarga", "outdoor", "50"),
    ("F8", "Reducción de frecuencia por sobrecorriente", "outdoor", "50"),
    ("F9", "Reducción de frecuencia por temperatura de descarga", "outdoor", "50"),
    ("FH", "Limitación de frecuencia por antihielo", "indoor", "50"),
    ("P0", "Frecuencia mínima del compresor en modo de prueba", "outdoor", "51"),
    ("P1", "Frecuencia nominal del compresor en modo de prueba", "outdoor", "51"),
    ("P2", "Frecuencia máxima del compresor en modo de prueba", "outdoor", "51"),
    ("P3", "Frecuencia intermedia del compresor en modo de prueba", "outdoor", "51"),
]


def build_errors() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    specs: list[dict[str, Any]] = []
    split_behaviors = {
        "E6": "En frío se detiene el compresor y sigue el ventilador interior; en calor se detienen todas las cargas.",
        "E3": "En frío se detienen compresor y ambos ventiladores; en calor el ventilador interior para 1 min después y la válvula de cuatro vías 2 min después.",
        "E4": "En frío/deshumidificación paran compresor y exterior y sigue el ventilador interior; en calor se detienen todas las cargas.",
        "E7": "Solo se detienen las cargas de la unidad interior en conflicto de modo.",
        "F4": "En frío paran compresor y exterior y sigue la interior; en calor la parada total se produce tras 3 minutos.",
        "Fo": "Durante la recuperación paran compresor y ventilador exterior mientras el ventilador interior continúa.",
        "E2": "Estado de protección antihielo en refrigeración; no es avería.",
        "E9": "Estado de prevención de aire frío; no es avería en esta familia split.",
    }
    for code, title, scope, page in SPLIT_ROWS:
        specs.append(spec(code, title, scope, "ENVO", page, behavior=split_behaviors.get(code, "")))

    specs.append(spec(
        "E9", "Cassette: protección de bandeja llena", "indoor", "CASS9", "61",
        "La placa confirma E9 si detecta abierto el interruptor de nivel durante 8 segundos continuos después de alimentar.",
        "La unidad entra en protección de agua; el manual indica cortar y restablecer la alimentación después de eliminar la causa.",
        causes=["Boya abierta por nivel alto", "Boya atascada o montaje sin nivel", "Bomba, desagüe o PCB defectuosos"],
        checks=["Comprobar agua real y nivelación en cuatro direcciones", "Verificar bomba, tubería y actuación de la boya", "No rearmar hasta corregir la causa de desbordamiento"],
    ))

    state_codes = {"A0", "A2", "A3", "A4", "A6", "A7", "A8", "A9", "AC", "AE", "AF", "AH", "AJ", "AP", "AU", "Ay", "db"}
    for code, title, scope, page in GMV_ROWS:
        behavior = ""
        if code in state_codes:
            behavior = "Es un estado o función GMV; la máquina ejecuta o espera la secuencia indicada y no debe interpretarse automáticamente como avería."
        specs.append(spec(code, title, scope, "GMV6", page, behavior=behavior))

    for code, title, scope in XK79_EXTRA:
        specs.append(spec(code, title, scope, "XK79", "71" if scope == "outdoor" else "73"))

    for code, title, scope, page in VIREO_EXTRA:
        if code in {"P0", "P1", "P2", "P3"}:
            behavior = "Es un estado de Test Run; el compresor trabaja a la frecuencia de prueba indicada y no representa una avería."
        else:
            behavior = "La unidad continúa operando, pero reduce o limita la frecuencia del compresor para proteger el sistema."
        specs.append(spec(code, title, scope, "VIREO", page, behavior=behavior))

    by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    interpretation_id = 0
    for row in specs:
        interpretation_id += 1
        item_id = interpretation_id * 100
        info: list[dict[str, Any]] = []

        def add(kind: str, body: str) -> None:
            nonlocal item_id
            item_id += 1
            info.append({
                "id": item_id, "item_type": kind, "title": None, "body": body,
                "sort_order": len(info) + 1, "review_status": "reviewed",
                "origin_ref": SOURCES[row["ref"]]["document_ref"],
            })

        add("machine_behavior", row["behavior"])
        add("related_element", row["title"])
        for value in row["causes"]:
            add("cause", value)
        for value in row["checks"]:
            add("check", value)
        add("observation", f"Confirme familia y forma de indicación. Fuente: {SOURCES[row['ref']]['document_ref']}.")

        datasets: list[dict[str, Any]] = []
        title_norm = normalize(row["title"])
        if "15 K" in title_norm:
            datasets.append(curve_dataset(interpretation_id * 10 + 1, "NTC 15 kΩ", NTC_15K))
        elif "20 K" in title_norm:
            datasets.append(curve_dataset(interpretation_id * 10 + 1, "NTC 20 kΩ", NTC_20K))
        elif "50 K" in title_norm:
            datasets.append(curve_dataset(interpretation_id * 10 + 1, "NTC 50 kΩ", NTC_50K))

        by_code[row["code"]].append({
            "id": interpretation_id,
            "title": row["title"],
            "description": row["description"],
            "source_kind": "official",
            "confidence": "high",
            "review_status": "reviewed",
            "info_items": info,
            "operational_impacts": [operational_impact(row["behavior"])],
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
        alias_rows = [{"alias_display": alias, "alias_normalized": normalize(alias).replace(" ", "")}
                      for alias in sorted(aliases, key=normalize)]
        label = interpretations[0]["title"] if len(interpretations) == 1 else f"{len(interpretations)} interpretaciones documentadas"
        blob = " ".join(
            [code, label] + [a["alias_display"] for a in alias_rows] +
            [" ".join([item["title"], item["description"]] + [r["body"] for r in item["info_items"]])
             for item in interpretations]
        )
        index = {
            "id": error_id,
            "code_display": code,
            "code_normalized": normalize(code).replace(" ", ""),
            "indication_type": "display_led_or_controller",
            "unit_scope": next(iter(scopes)) if len(scopes) == 1 else "system",
            "short_label": label,
            "interpretation_count": len(interpretations),
            "search_text": normalize(blob),
        }
        detail = {
            **{k: v for k, v in index.items() if k not in {"interpretation_count", "search_text"}},
            "aliases": alias_rows,
            "tags": sorted({token.lower() for token in normalize(blob).split() if len(token) > 4})[:20],
            "interpretations": interpretations,
            "media": [],
        }
        indexes.append(index)
        details.append(detail)
    return indexes, details


def section(kind: str, title: str, body: str, opened: bool = False) -> dict[str, Any]:
    return {"section_type": kind, "title": title, "body": body, "collapsed_default": 0 if opened else 1}


def step(phase: str, number: int, instruction: str, expected: str | None = None,
         warning: str = "none") -> dict[str, Any]:
    return {"phase": phase, "step_no": number, "instruction": instruction,
            "expected_result": expected, "warning_level": warning}


def controller(family: str, wires: str, polarity: str, voltage: str | None,
               terminals: str, startup: str, notes: str, cable_spec: str) -> dict[str, Any]:
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
        "maximum_scope": "Hasta 16 interiores compatibles cuando el manual de la familia lo permite.",
        "notes": notes,
    }


def option(value: str, label: str, effect: str, factory: bool = False) -> dict[str, Any]:
    return {"option_value": value, "option_label": label, "effect": effect, "is_factory": factory}


def parameter(code: str, name: str, description: str, options: list[dict[str, Any]],
              factory: str | None = None, dependencies: str | None = None,
              warnings: str | None = None) -> dict[str, Any]:
    return {
        "parameter_code": code, "name": name, "description": description,
        "factory_value": factory, "dependencies": dependencies,
        "warnings": warnings, "options": options,
    }


TOPIC_DEFS = [
    (1, "diagnostic_access", "read-errors", "Cómo obtener códigos y subcódigos", "Mando, LED interior y display exterior."),
    (2, "history_reset", "history-n6", "Historial, consulta y borrado", "Memoria n6 y salida segura."),
    (3, "controllers_buses", "wired-controllers", "Mandos XK19, XK46 y XK79", "Cómo reconocerlos, cablearlos y configurarlos."),
    (4, "controllers_buses", "communications", "Diagnóstico de buses y comunicación", "COM/N, H1/H2, D1/D2 y CAN."),
    (5, "service_modes", "pump-down", "Pump down y recuperación", "Variantes split y GMV A2."),
    (6, "service_modes", "vacuum-defrost-emergency", "Vacío, desescarche y emergencia", "A8, n3 y C9."),
    (7, "configuration", "controller-parameters", "Programación desde mando", "C00/P00, maestro/esclavo y presión estática."),
    (8, "configuration", "outdoor-board-functions", "Programación de placa exterior", "A6, A7, n0, n4 y restauración."),
    (9, "drainage_overflow", "drainage", "Bomba, boya y desbordamiento", "E9 cassette y L3 GMV."),
    (10, "commissioning", "test-debug", "Test Run y depuración automática", "Split, cassette y GMV."),
    (11, "multisplit", "group-control", "Multisplit y control de grupo", "Conflicto de modo, cantidades y maestra."),
    (12, "gmv_network", "gmv-addressing", "Red GMV, direcciones y cantidad de unidades", "Proyecto, n8, n9 y topología."),
    (13, "gmv_network", "gmv-operational-impact", "Alcance de parada y emergencia modular", "Qué puede continuar funcionando."),
    (14, "component_checks", "temperature-sensors", "Sondas 15/20/50 kΩ", "Resistencia y tensión por temperatura."),
    (15, "component_checks", "valves-compressor", "EEV, solenoides y compresor", "Bobinas, pulsos y aislamiento."),
    (16, "component_checks", "drives-pressure", "IPM, ventiladores y presión", "Diodos y comparación con manómetro."),
    (17, "technical_values", "quick-values", "Valores eléctricos rápidos", "Bus, bobinas, compresor y sondas."),
    (18, "normal_states", "normal-status", "Estados normales y esperas", "A0–A9, db y retardos."),
    (19, "service_tools_boards", "commissioning-tool", "Gree Commissioning Tool", "Conexión, datos y depuración."),
    (20, "service_tools_boards", "board-replacement", "Después de sustituir una placa", "Jumper, DIP, direcciones y depuración."),
    (21, "system_architecture", "recognize-family", "Cómo reconocer la familia técnica", "Split, cassette, conductos y GMV."),
    (22, "errors", "using-repeated-codes", "Cómo usar códigos repetidos", "No mezclar split, cassette y GMV."),
]


def variant(variant_id: int, topic_id: int, title: str, recognition: str,
            purpose: str, summary: str, bullets: list[str], steps: list[dict[str, Any]],
            ref: str, page: str, page_end: str | None = None, *,
            system_type: str = "Gree", unit_scope: str = "system",
            controller_profile: dict[str, Any] | None = None,
            parameters: list[dict[str, Any]] | None = None,
            monitoring: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "id": variant_id,
        "topic_id": topic_id,
        "title": title,
        "recognition": recognition,
        "system_type": system_type,
        "unit_scope": unit_scope,
        "refrigerant": None,
        "purpose": purpose,
        "summary": summary,
        "source_kind": "official",
        "review_status": "reviewed",
        "sort_order": variant_id,
        "visible": 1,
        "sections": [
            section("recognition", "Cómo reconocer esta variante", recognition, True),
            section("technical", "Qué debe tener en cuenta la máquina", " ".join(bullets)),
        ],
        "steps": steps,
        "parameters": parameters or [],
        "controller": controller_profile,
        "monitoring_points": monitoring or [],
        "media": [],
        "sources": [source(ref, page, title, page_end)],
    }


def build_topics() -> list[dict[str, Any]]:
    topics: dict[int, dict[str, Any]] = {}
    for topic_id, category_slug, slug, title, summary in TOPIC_DEFS:
        category = CAT[category_slug]
        topics[topic_id] = {
            "id": topic_id, "brand_id": BRAND_ID, "category_id": category["id"],
            "slug": slug, "title": title, "summary": summary, "active": 1,
            "category": category, "variants": [],
        }

    vid = 0

    def add(topic_id: int, title: str, recognition: str, purpose: str, summary: str,
            bullets: list[str], steps_: list[dict[str, Any]], ref: str, page: str,
            page_end: str | None = None, **kwargs: Any) -> None:
        nonlocal vid
        vid += 1
        topics[topic_id]["variants"].append(
            variant(vid, topic_id, title, recognition, purpose, summary, bullets,
                    steps_, ref, page, page_end, **kwargs)
        )

    add(1, "XK46 — localizar interior y leer errores con C01",
        "Mando con botones FUNCTION, MODE y ENTER/CANCEL; bornes H1/H2.",
        "Leer códigos y número de proyecto sin desmontar la máquina.",
        "C01 recorre las interiores; si hay varias averías las muestra cada 3 segundos.",
        ["FUNCTION 5 s abre C00/CHECK.", "MODE en C01 entra en la lista.", "La pantalla de temperatura muestra error y la zona de temporizador el proyecto."],
        [step("prepare", 1, "Con la unidad encendida o apagada, mantenga FUNCTION 5 s.", "Aparece C00 y CHECK."),
         step("procedure", 1, "Seleccione C01 y pulse MODE."),
         step("procedure", 2, "Use las flechas para recorrer números de proyecto y anote los códigos."),
         step("exit", 1, "Salga manualmente con ENTER/CANCEL; C01 no sale solo.")],
        "XK46", "16", "17")

    add(1, "XK79 — lectura automática de varios errores",
        "Mando XK62/XK79 con zona de temperatura y botón SWING/ENTER.",
        "Identificar errores exterior, interior, depuración y estados.",
        "Cuando coinciden varias averías, la pantalla repite los códigos.",
        ["E/F/J/P/H/b corresponden normalmente a exterior.", "L/d/y corresponden a interior.", "A y algunos n/db pueden ser estados o funciones."],
        [step("prepare", 1, "Observe la zona de temperatura sin entrar en programación."),
         step("procedure", 1, "Anote todos los códigos que aparecen en ciclo."),
         step("verify", 1, "Clasifique cada código con las tablas exterior, interior, depuración o estado.")],
        "XK79", "70", "75")

    add(1, "Cassette de dos vías — lectura por tres LED",
        "Panel sin display numérico; dispone de POWER, OPERATION y TIMER.",
        "Convertir el patrón de los tres pilotos en un código.",
        "El manual ofrece combinaciones para C0, A0, A3/A4, L0, L1, L3, L5, d1, d3, d4, d6, d7, E0 y db.",
        ["No confundir encendido, apagado y parpadeo.", "A3/A4 comparten patrón y se distinguen por el estado operativo."],
        [step("prepare", 1, "Anote para cada LED si está encendido, apagado o parpadeando."),
         step("procedure", 1, "Compare la combinación completa con la tabla, no un LED aislado."),
         step("verify", 1, "Confirme el resultado en el mando o display exterior cuando exista.")],
        "GMV5I", "158", system_type="GMV cassette", unit_scope="indoor")

    add(1, "GMV exterior — código y dirección del módulo",
        "Placa exterior con display LED1 y botones SW1–SW4.",
        "Distinguir el código de avería de la dirección del módulo.",
        "El display alterna código, valor o dirección según el menú; nE indica valor negativo.",
        ["Anote la alternancia completa y el intervalo.", "E0 puede acompañar a la avería exterior real.", "00 puede significar sin registro dentro de n6."],
        [step("prepare", 1, "Espere a que el display complete al menos dos ciclos."),
         step("procedure", 1, "Anote código, dirección y cualquier valor alternado."),
         step("verify", 1, "Consulte n6 si necesita confirmar una avería anterior.")],
        "GMV6", "28", "31", system_type="GMV6", unit_scope="outdoor")

    add(2, "GMV6 — consultar las cinco últimas averías con n6",
        "Placa maestra con SW1 arriba, SW2 abajo, SW3 confirmar y SW4 volver.",
        "Recuperar la secuencia histórica antes de cortar o sustituir componentes.",
        "n6 conserva hasta cinco fallos con la dirección del módulo y los muestra en orden temporal.",
        ["SW2 más de 5 s abre consulta.", "SW1/SW2 seleccionan n6.", "SW3 confirma; 00 indica que no quedan más registros."],
        [step("prepare", 1, "En la unidad maestra mantenga SW2 más de 5 s."),
         step("procedure", 1, "Seleccione n6 con SW1/SW2 y confirme con SW3."),
         step("procedure", 2, "Anote cada pareja avería/dirección hasta 00."),
         step("exit", 1, "Pulse SW4 para volver o espere 5 min sin actuar.")],
        "GMV6", "28", "29")

    add(2, "GMV6 — borrar el historial n6",
        "Solo después de registrar y reparar la causa.",
        "Vaciar las cinco memorias históricas de la exterior.",
        "En n6, SW3 durante más de 5 segundos borra todas las averías históricas.",
        ["El borrado elimina evidencia útil.", "No corrige una avería activa."],
        [step("prepare", 1, "Fotografíe o anote los cinco registros."),
         step("procedure", 1, "Dentro de n6 mantenga SW3 más de 5 s."),
         step("verify", 1, "Repita n6 y confirme 00.")],
        "GMV6", "29")

    add(3, "XK19 — cable premontado de dos conectores",
        "Mando compacto con cable de comunicación suministrado de 26 ft.",
        "Evitar averías creadas por empalmar o recortar el cable propietario.",
        "El manual ordena usar el cable suministrado y no cortarlo ni empalmarlo.",
        ["Los conectores se enchufan a interior y mando.", "No asignar colores/tensiones si el manual del equipo no los confirma."],
        [step("prepare", 1, "Corte alimentación antes de conectar."),
         step("procedure", 1, "Tienda el cable completo evitando potencia y bordes."),
         step("verify", 1, "Compruebe que ambos conectores quedan insertados y sin empalmes.")],
        "XK19", "8", "10",
        controller_profile=controller("XK19", "cable premontado", "según conectores", None,
                                      "conectores específicos", "Inicialización al alimentar la interior.",
                                      "No cortar ni empalmar.", "Cable Gree de 26 ft suministrado."))

    add(3, "XK46 — H1/H2 de dos hilos",
        "Mando rectangular con FUNCTION, MODE y ENTER/CANCEL.",
        "Cablear uno o dos mandos y hasta 16 interiores compatibles.",
        "Emplea par trenzado de dos hilos en H1/H2; dos mandos deben usar direcciones 01 y 02.",
        ["Solo un mando maestro 01 y uno esclavo 02.", "Las interiores del grupo deben pertenecer a la misma serie.", "El mando se instala sin tensión."],
        [step("prepare", 1, "Corte alimentación de la interior."),
         step("procedure", 1, "Conecte el par trenzado a H1 y H2."),
         step("procedure", 2, "Si hay dos mandos, configure P13 como 01 y 02."),
         step("verify", 1, "Compruebe C09 y C11.")],
        "XK46", "12", "15",
        controller_profile=controller("XK46", "2", "H1/H2 según esquema", None, "H1-H2",
                                      "El mando arranca desde la interior y adquiere la red.",
                                      "Máximo dos mandos y 16 interiores compatibles.",
                                      "Par trenzado de dos hilos, separado de potencia."))

    add(3, "XK79 — H1/H2 y entrada de tarjeta",
        "Mando XK62/XK79; puede incorporar gate-control.",
        "Separar el bus de mando de las entradas de control de acceso.",
        "H1/H2 usa par trenzado de dos hilos; gate-control admite 100–240 VAC o 5–24 VDC, nunca ambas entradas.",
        ["S1 activa/desactiva gate-control.", "P69 debe corresponder al tipo de señal.", "Elegir solo N/L o VCC/GND."],
        [step("prepare", 1, "Corte alimentación."),
         step("procedure", 1, "Conecte el par H1/H2 y verifique longitud pelada ≤6 mm."),
         step("procedure", 2, "Si existe tarjeta, seleccione una única alimentación y ajuste S1/P69."),
         step("verify", 1, "Compruebe que el mando controla sin icono de bloqueo.")],
        "XK79", "23", "25",
        controller_profile=controller("XK62/XK79", "2", "H1/H2 según esquema", None, "H1-H2",
                                      "Adquiere la red y muestra estados/errores.",
                                      "Gate-control es una entrada separada.",
                                      "Par trenzado de dos hilos."))

    add(4, "Split inverter — diagnóstico COM–N (~56 VDC)",
        "Interconexión con borne COM y neutro N en placa exterior.",
        "Decidir si el fallo E6 está en cable/interior o en la comunicación exterior.",
        "Con la comunicación interior–exterior desconectada, el manual indica medir alrededor de 56 VDC entre COM y N de la exterior.",
        ["Es una prueba energizada: aplicar procedimiento eléctrico seguro.", "Primero revisar continuidad y orden de bornes.", "El valor corresponde a esta familia, no a H1/H2 ni D1/D2."],
        [step("prepare", 1, "Corte tensión, identifique COM y N y separe la comunicación."),
         step("procedure", 1, "Energice con protección y mida en escala DC entre COM y N.", warning="danger"),
         step("verify", 1, "Alrededor de 56 VDC orienta a revisar cable/interior; ausencia orienta a circuito exterior."),
         step("exit", 1, "Corte tensión antes de reconectar.")],
        "ENVO", "63", system_type="Split inverter", unit_scope="system")

    add(4, "GMV — D1/D2 frente a H1/H2 y G1/G2",
        "Red CAN de interiores/exterior y buses separados de mando/centralización.",
        "Evitar cruces de buses que generan C0.",
        "El manual de GMV6 exige no mezclar D1/D2 con H1/H2 ni G1/G2.",
        ["Compruebe alimentación 208/230 VAC en IDU y ODU.", "Siga el mismo par extremo a extremo.", "La red CAN admite cable ordinario según la guía GMV5, pero debe respetarse la instalación."],
        [step("prepare", 1, "Con tensión cortada, identifique cada par por etiqueta."),
         step("procedure", 1, "Compruebe continuidad y ausencia de cruces."),
         step("verify", 1, "Alimente y confirme que desaparece C0 antes de sustituir placas.")],
        "GMV6", "36", system_type="GMV6", unit_scope="network")

    add(5, "GMV6 — A2 recuperación desde tuberías interiores",
        "Placa exterior maestra con display y SW1–SW4.",
        "Recuperar refrigerante en la exterior durante mantenimiento.",
        "Seleccione A2→01; el display muestra baja presión y SW3 confirma la parada final.",
        ["La cantidad máxima recuperable depende de la capacidad.", "Tras confirmar, todo el sistema se detiene y no puede arrancar durante 10 min.", "SW4 permite volver."],
        [step("prepare", 1, "Entre en funciones y seleccione A2."),
         step("procedure", 1, "Seleccione 01 con SW1/SW2 y confirme con SW3."),
         step("procedure", 2, "Vigile la baja presión mostrada; nE precede a un valor negativo."),
         step("procedure", 3, "Cuando el sistema solicite la maniobra manual, pulse SW3."),
         step("exit", 1, "Espere 10 min; después use SW4 para volver a espera.")],
        "GMV6", "19", "21", system_type="GMV6", unit_scope="system")

    add(5, "Split — modo Fo de recuperación",
        "Equipo split que muestra Fo en la tabla de mantenimiento.",
        "Reconocer el estado de recuperación sin confundirlo con una avería.",
        "En Fo paran compresor y ventilador exterior mientras el ventilador interior continúa.",
        ["Solo debe activarlo personal de mantenimiento.", "No aplicar el procedimiento GMV A2 a un split."],
        [step("prepare", 1, "Confirme que el equipo y manual incluyen Fo."),
         step("procedure", 1, "Ejecute únicamente el método de servicio de esa familia."),
         step("verify", 1, "Compruebe que el comportamiento coincide con Fo.")],
        "ENVO", "58", system_type="Split inverter")

    add(6, "GMV6 — A8 vacío de mantenimiento",
        "Función A8 en la placa maestra.",
        "Abrir EEV y solenoides para evitar zonas muertas durante vacío/recuperación.",
        "Al confirmar A8 todas las válvulas de interiores y exteriores abren y el sistema no puede arrancar.",
        ["Salir con SW4 más de 5 s.", "La salida automática se produce a las 24 h.", "Es mantenimiento, no puesta en marcha normal."],
        [step("prepare", 1, "Seleccione A8 y compruebe 00 parpadeando."),
         step("procedure", 1, "Pulse SW3; confirme A8 fijo en todos los módulos."),
         step("exit", 1, "Mantenga SW4 más de 5 s para salir.")],
        "GMV6", "24")

    add(6, "GMV6 — n3 desescarche forzado",
        "Función n3 disponible en la placa exterior.",
        "Forzar un desescarche solo cuando se cumplen sus condiciones.",
        "n3 es función de servicio; A3 es el estado normal de desescarche.",
        ["No confundir el código de selección n3 con el estado A3.", "Las protecciones del sistema permanecen activas."],
        [step("prepare", 1, "Entre en funciones de placa y seleccione n3."),
         step("procedure", 1, "Confirme con SW3."),
         step("verify", 1, "Compruebe A3 y la evolución de presiones/temperaturas."),
         step("exit", 1, "Use SW4 para volver.")],
        "GMV6", "19", "26")

    add(6, "GMV6 — C9 emergencia de un ventilador",
        "Exterior de doble ventilador; uno de ellos presenta fallo.",
        "Mantener servicio temporal bloqueando un único ventilador averiado.",
        "C9 permite 01=anular fan 1 o 02=anular fan 2; el ajuste queda memorizado.",
        ["Solo para modelos de dos ventiladores.", "Solo puede anularse uno.", "Máximo 120 h; después se detiene todo el sistema."],
        [step("prepare", 1, "Identifique con certeza qué ventilador falla."),
         step("procedure", 1, "Seleccione C9 y elija 01 o 02."),
         step("procedure", 2, "Confirme con SW3."),
         step("verify", 1, "Planifique reparación antes de 120 h."),
         step("exit", 1, "Tras reparar, devuelva C9 a 00.")],
        "GMV6", "27", system_type="GMV6", unit_scope="outdoor")

    params_xk46 = [
        parameter("P10", "Unidad interior maestra", "Asigna la interior correspondiente como maestra.",
                  [option("00", "No cambiar", "Mantiene el estado", True), option("01", "Maestra", "Asigna MASTER")], "00"),
        parameter("P13", "Dirección del mando", "Diferencia los dos mandos del mismo grupo.",
                  [option("01", "Maestro", "Mando principal", True), option("02", "Esclavo", "Mando secundario")], "01"),
        parameter("P14", "Cantidad de interiores", "Número de interiores bajo control de grupo.",
                  [option("00", "Desactivado", "Sin grupo"), option("01–16", "Cantidad", "Debe coincidir con la instalación")], "01"),
        parameter("P30", "Presión estática", "Nivel de presión del ventilador de conductos.",
                  [option("01–09", "Nivel", "La interior adapta a 5 o 9 niveles")], "05"),
    ]
    add(7, "XK46 — entrar en C00 y P00",
        "Mando con FUNCTION/MODE/ENTER-CANCEL.",
        "Consultar parámetros o modificar únicamente los autorizados.",
        "FUNCTION 5 s abre C00; otros 5 s abren P00. MODE entra, flechas cambian y ENTER/CANCEL confirma.",
        ["C00 es consulta y P00 programación.", "El mando esclavo no puede cambiar la mayoría de parámetros.", "Registre valores antes de modificarlos."],
        [step("prepare", 1, "Mantenga FUNCTION 5 s para C00."),
         step("procedure", 1, "Para programar, mantenga FUNCTION otros 5 s hasta P00."),
         step("procedure", 2, "Seleccione código, pulse MODE, ajuste y confirme."),
         step("exit", 1, "Retroceda con ENTER/CANCEL.")],
        "XK46", "16", "23", parameters=params_xk46)

    add(7, "XK46 — consultas C07, C09, C11, C12 y C18",
        "Dentro de C00/CHECK.",
        "Leer temperaturas, dirección, cantidad de grupo y número de proyecto.",
        "C07=ambiente interior; C09=dirección del mando; C11=cantidad; C12=ambiente exterior; C18=proyecto.",
        ["C18 muestra proyectos cada 3 s si controla varias interiores.", "C18 no está disponible en mando esclavo."],
        [step("prepare", 1, "Entre en C00."),
         step("procedure", 1, "Seleccione el código C correspondiente."),
         step("procedure", 2, "Pulse MODE cuando el parámetro requiera elegir interior."),
         step("exit", 1, "Salga manualmente; algunos menús no caducan.")],
        "XK46", "17", "21")

    add(8, "GMV6 — A6 selección frío/calor global",
        "Función A6 en placa exterior.",
        "Restringir los modos admitidos por todo el sistema.",
        "nA=frío/calor; nC=solo frío; nH=solo calor; nF=solo ventilación. El ajuste se memoriza.",
        ["nA es valor de fábrica.", "Una selección incorrecta puede parecer conflicto de modo."],
        [step("prepare", 1, "Entre en A6 y anote el valor actual."),
         step("procedure", 1, "Seleccione nA, nC, nH o nF con SW1/SW2."),
         step("procedure", 2, "Confirme con SW3."),
         step("verify", 1, "Pruebe los modos permitidos y documente el cambio.")],
        "GMV6", "21", "22")

    add(8, "GMV6 — A7 bajo ruido",
        "Función A7 en placa exterior.",
        "Elegir reducción de ruido conociendo la pérdida de capacidad.",
        "00=sin silencio; 01–09=perfiles inteligentes; 10–13=forzados.",
        ["La capacidad disminuye.", "El ajuste debe equilibrar ruido y rendimiento."],
        [step("prepare", 1, "Entre en A7 y anote el valor actual."),
         step("procedure", 1, "Seleccione 00–13 y confirme con SW3."),
         step("verify", 1, "Compruebe ruido, capacidad y horario.")],
        "GMV6", "22", "24")

    add(8, "GMV6 — restauraciones 0C con tres alcances",
        "Combinaciones SW1/SW2/SW3 con SW4 durante más de 10 s.",
        "Restaurar solo el alcance necesario sin perder commissioning por error.",
        "SW1+SW4 borra todo; SW2+SW4 conserva commissioning; SW3+SW4 borra solo funciones exteriores.",
        ["0C parpadea 3, 5 o 7 s según el alcance.", "Documente direcciones, cantidades y ajustes antes."],
        [step("prepare", 1, "Exporte o anote todas las configuraciones."),
         step("procedure", 1, "Elija una única combinación acorde al alcance."),
         step("verify", 1, "Compruebe la duración 0C y vuelva a validar la red.")],
        "GMV6", "33")

    add(9, "Cassette R32 — E9 tras 8 s de boya abierta",
        "Cassette con interruptor de nivel y bomba integrados.",
        "Distinguir agua real, boya atascada, bomba y placa.",
        "Tras alimentar, 8 s continuos con la boya abierta confirman E9.",
        ["La unidad debe quedar nivelada en cuatro direcciones.", "El rearme indicado es cortar y restablecer tras corregir.", "No puentee la boya para dejar el equipo funcionando."],
        [step("prepare", 1, "Corte tensión y revise bandeja, nivel y desagüe."),
         step("procedure", 1, "Compruebe continuidad de la boya arriba/abajo."),
         step("procedure", 2, "Compruebe bomba y evacuación."),
         step("verify", 1, "Restablezca alimentación y confirme que la boya cierra antes de 8 s.")],
        "CASS9", "58", system_type="Cassette R32", unit_scope="indoor")

    add(9, "GMV — L3 por flotador/bomba",
        "Interior GMV con mando o panel que muestra L3.",
        "Localizar la causa de bandeja llena sin sustituir la placa por descarte.",
        "L3 se genera cuando el interruptor de flotador se activa por nivel alto.",
        ["Causas oficiales: instalación, bomba, flotador o placa.", "El panel de cassette de dos vías también tiene patrón LED para L3."],
        [step("prepare", 1, "Observe agua real y estado de la boya."),
         step("procedure", 1, "Revise instalación, pendiente y bomba."),
         step("procedure", 2, "Compruebe el flotador y su entrada en placa."),
         step("verify", 1, "Ejecute una prueba de drenaje antes de cerrar.")],
        "GMV5I", "167", system_type="GMV indoor", unit_scope="indoor")

    add(10, "Split/cassette — Test Operation básico",
        "Equipo individual con mando inalámbrico o cableado.",
        "Confirmar frío, calor, ventilación y drenaje después de instalar.",
        "El manual exige verificar válvulas, fugas, tensión, drenaje y ausencia de obstrucciones antes del test.",
        ["Por debajo de 16 °C ambiente la familia Envo puede no iniciar refrigeración normal.", "No use un test para saltarse protecciones."],
        [step("prepare", 1, "Complete la lista de instalación, abra válvulas y verifique tensión."),
         step("procedure", 1, "Arranque desde el mando y seleccione los modos disponibles."),
         step("verify", 1, "Compruebe temperaturas, ruidos, drenaje y ausencia de códigos.")],
        "ENVO", "56", system_type="Split/cassette")

    add(10, "GMV5 — depuración obligatoria tras instalación o PCB",
        "Exterior GMV5 con display y acceso a commissioning.",
        "Reconocer unidades, validar red y autorizar el funcionamiento.",
        "La depuración es obligatoria tras la instalación inicial o sustituir la placa principal.",
        ["Compresor precalentado más de 8 h.", "Válvulas completamente abiertas.", "Cableado/control y carga adicional revisados."],
        [step("prepare", 1, "Compruebe red, válvulas, carga y precalentamiento >8 h."),
         step("procedure", 1, "Inicie la depuración desde la placa o herramienta."),
         step("procedure", 2, "Siga cada etapa y corrija las que no terminan OK."),
         step("verify", 1, "Confirme fin de commissioning y Test Run.")],
        "GMV5O", "86", "93", system_type="GMV5", unit_scope="system")

    add(10, "GMV6 — preparación y secuencia de commissioning",
        "Exterior GMV6 Ultra Heat Mini.",
        "Completar la puesta en marcha con datos en tiempo real.",
        "El manual exige conexión de software de depuración y compresor precalentado más de 8 h.",
        ["La cantidad de interiores y su comunicación deben coincidir.", "La carga manual aparece en la etapa AE/AP.", "Una depuración incompleta deja A0/db."],
        [step("prepare", 1, "Verifique instalación, tensión, válvulas y precalentamiento."),
         step("procedure", 1, "Conecte la herramienta y mantenga SW3 5 s para iniciar."),
         step("procedure", 2, "Siga las etapas y añada refrigerante solo cuando se solicite."),
         step("verify", 1, "Confirme finalización, cantidades, presiones y temperaturas.")],
        "GMV6", "6", "14", system_type="GMV6")

    add(11, "XK46 — un mando controla hasta 16 interiores",
        "Grupo de interiores de la misma serie conectado a un XK46.",
        "Evitar L9/LA por cantidad o series incorrectas.",
        "P14 debe coincidir con la cantidad real; el grupo admite hasta 16 interiores compatibles.",
        ["Solo una interior maestra.", "Dos mandos deben ser 01 y 02.", "Todas las interiores del grupo deben compartir red/serie."],
        [step("prepare", 1, "Cuente interiores y confirme que pertenecen a la misma serie."),
         step("procedure", 1, "Ajuste P14 al número real."),
         step("procedure", 2, "Revise P13 si hay dos mandos."),
         step("verify", 1, "Compruebe C11 y ausencia de L9/LA.")],
        "XK46", "12", "23")

    add(11, "Multisplit — E7 conflicto de modo",
        "Dos interiores del mismo exterior solicitan frío y calor incompatibles.",
        "Reconocer un conflicto de demanda, no una avería frigorífica.",
        "La tabla split indica que se detienen las cargas de la interior en conflicto.",
        ["La unidad maestra o prioridad del sistema determina el modo.", "Revisar consignas antes de medir componentes."],
        [step("prepare", 1, "Anote modo de todas las interiores conectadas."),
         step("procedure", 1, "Ponga todas en un modo compatible."),
         step("verify", 1, "Compruebe que E7 desaparece y la interior recupera servicio.")],
        "ENVO", "58", system_type="Multisplit")

    add(12, "GMV6 — n8 mostrar número de proyecto en todas las interiores",
        "Placa exterior maestra y red GMV operativa.",
        "Identificar físicamente cada interior sin conocer su modelo.",
        "n8 fuerza a mandos/paneles a mostrar el número de proyecto sin cambiar el estado operativo.",
        ["SW4 vuelve de nivel pero mantiene la indicación.", "SW4 >5 s la cancela en todas.", "Salida automática a los 30 min."],
        [step("prepare", 1, "Entre en consultas con SW2 >5 s."),
         step("procedure", 1, "Seleccione n8 y confirme con SW3."),
         step("verify", 1, "Recorra la instalación y registre cada número."),
         step("exit", 1, "Mantenga SW4 >5 s para cancelar en todas.")],
        "GMV6", "31", "32", system_type="GMV6", unit_scope="network")

    add(12, "GMV6 — n9 cantidad de interiores en línea",
        "Display exterior en menú n9.",
        "Comparar cantidad reconocida con cantidad instalada.",
        "n9 muestra código y cantidad alternados; solo consulta una red de sistema.",
        ["Una diferencia orienta a alimentación, D1/D2, dirección o incompatibilidad.", "No sustituya placas antes de aislar el nodo ausente."],
        [step("prepare", 1, "Cuente las interiores instaladas y alimentadas."),
         step("procedure", 1, "Seleccione n9 en consulta."),
         step("verify", 1, "Compare la cantidad mostrada con la real.")],
        "GMV6", "32", system_type="GMV6", unit_scope="network")

    add(13, "Sistema modular — aislar un módulo exterior averiado",
        "Varias exteriores conectadas en paralelo con válvulas de gas, líquido y equilibrado de aceite.",
        "Mantener capacidad parcial sin dañar los módulos sanos.",
        "El procedimiento oficial obliga a parar todo antes de aislar físicamente y reconfigurar.",
        ["Cerrar gas, líquido y equilibrado de aceite del módulo averiado.", "Cortar su magnetotérmico y retirar su comunicación.", "Reajustar dirección y cantidad de módulos restantes."],
        [step("prepare", 1, "Ponga todas las interiores en OFF y corte alimentación total."),
         step("procedure", 1, "Cierre las tres válvulas del módulo averiado."),
         step("procedure", 2, "Aísle su alimentación y comunicación."),
         step("procedure", 3, "Reconfigure dirección y cantidad de módulos restantes."),
         step("verify", 1, "Alimente y compruebe funcionamiento degradado de los módulos sanos.")],
        "GMV5I", "172", system_type="GMV modular", unit_scope="outdoor")

    add(13, "GMV6 — parada de emergencia local y remota",
        "Códigos Ab o AU en el sistema.",
        "Distinguir una orden externa de una avería de máquina.",
        "Ab indica entrada local abierta; AU indica deshabilitación remota desde BMS o control central.",
        ["Revisar la cadena de seguridad y el origen de la orden.", "No puentear sin autorización."],
        [step("prepare", 1, "Determine si aparece Ab o AU."),
         step("procedure", 1, "Revise entrada local o sistema BMS correspondiente."),
         step("verify", 1, "Restablezca la orden y confirme la salida del estado.")],
        "GMV6", "35", "36", system_type="GMV6")

    add(14, "NTC de ambiente — 15 kΩ a 25 °C",
        "Sondas de ambiente exterior/interior y algunas de impulsión GMV.",
        "Comparar resistencia y, cuando consta, tensión de placa.",
        "Referencia: 15 kΩ y aproximadamente 1,65 VDC a 25 °C en la tabla GMV6.",
        ["Medir resistencia con la sonda desconectada.", "No aplicar a sondas de 20 o 50 kΩ."],
        [step("prepare", 1, "Mida temperatura real del punto."),
         step("procedure", 1, "Desconecte la sonda y mida resistencia."),
         step("verify", 1, "Compare con tabla 15 kΩ y tolerancia de la familia.")],
        "GMV6", "60", "97")

    add(14, "NTC de tubería — 20 kΩ a 25 °C",
        "Sondas RT1–RT6 y de tubería GMV.",
        "Distinguir una sonda de 20 kΩ de una de ambiente o descarga.",
        "Referencia: 20 kΩ a 25 °C; 65,37 kΩ a 0 °C y 10,62 kΩ a 40 °C.",
        ["La curva es decreciente.", "Conector y contacto térmico pueden simular fallo."],
        [step("prepare", 1, "Identifique el conector y mida la temperatura de la tubería."),
         step("procedure", 1, "Desconecte y mida resistencia."),
         step("verify", 1, "Compare con la curva 20 kΩ.")],
        "GMV6", "61", "99")

    add(14, "NTC de descarga — 50 kΩ a 25 °C",
        "Sonda RT8 en descarga de compresor.",
        "Comprobar F5 sin confundirla con sondas de 20 kΩ.",
        "Referencia: 49,191 kΩ a 25 °C; 161,02 kΩ a 0 °C y 26,147 kΩ a 40 °C.",
        ["La temperatura de descarga exige buen contacto.", "Un valor eléctrico correcto con lectura incoherente orienta a PCB."],
        [step("prepare", 1, "Espere una condición térmica segura y mida temperatura."),
         step("procedure", 1, "Desconecte RT8 y mida resistencia."),
         step("verify", 1, "Compare con la curva 50 kΩ.")],
        "GMV6", "62", "104")

    add(15, "GMV6 — bobinas de válvulas",
        "Bobina de cuatro vías y solenoides de subenfriamiento/retorno.",
        "Separar bobina abierta de válvula mecánicamente atascada.",
        "Valores oficiales: 4 vías 1880 Ω ±10 %; solenoides 1830 Ω ±10 %.",
        ["Medir sin tensión.", "Una bobina correcta no confirma que el cuerpo cambie."],
        [step("prepare", 1, "Corte alimentación y descargue."),
         step("procedure", 1, "Desconecte la bobina y mida resistencia."),
         step("verify", 1, "Compare con 1880 o 1830 Ω según el componente.")],
        "GMV6", "63", "65", unit_scope="outdoor")

    add(15, "GMV6 — EEV de 5 hilos",
        "Válvula electrónica exterior con conector de cinco hilos.",
        "Comprobar bobina antes de condenar la placa.",
        "El manual indica 480 pulsos y aproximadamente 46 Ω ±3,7 Ω.",
        ["Compruebe todas las fases de bobina.", "Un valor correcto no descarta atasco mecánico."],
        [step("prepare", 1, "Corte alimentación y desconecte la EEV."),
         step("procedure", 1, "Mida las combinaciones indicadas por el esquema."),
         step("verify", 1, "Compare con 46 Ω ±3,7 Ω y verifique inicialización.")],
        "GMV6", "66", "68", unit_scope="outdoor")

    add(15, "GMV6 — compresor U/V/W",
        "Compresor inverter con tres salidas U, V y W.",
        "Distinguir bobinado, aislamiento y driver.",
        "Referencia de la familia: 0,197 Ω ±7 % entre fases y aislamiento superior a 10 MΩ.",
        ["Las tres resistencias deben ser equivalentes.", "Desconecte del driver y espere descarga."],
        [step("prepare", 1, "Corte tensión, espere y desconecte U/V/W."),
         step("procedure", 1, "Mida U-V, V-W y W-U con equipo apropiado."),
         step("procedure", 2, "Mida aislamiento a tierra."),
         step("verify", 1, "Compare equilibrio, 0,197 Ω ±7 % y >10 MΩ.")],
        "GMV6", "73", "76", unit_scope="outdoor")

    add(16, "GMV6 — prueba de diodos del IPM",
        "Placa driver de compresor desconectada de U/V/W.",
        "Separar módulo en corto de compresor defectuoso.",
        "Las doce lecturas de diodo deben estar entre 0,3 y 0,7 V; cualquier lectura 0 indica módulo dañado.",
        ["Espere al menos 2 min sin tensión.", "Siga polaridades P/N–U/V/W del manual."],
        [step("prepare", 1, "Corte tensión, espere 2 min y desconecte U/V/W y alimentación."),
         step("procedure", 1, "Use modo diodo y realice las doce combinaciones."),
         step("verify", 1, "Todas entre 0,3–0,7 V; 0 V en cualquiera indica daño.")],
        "GMV6", "78", "79", unit_scope="outdoor")

    add(16, "GMV6 — driver del ventilador",
        "Ventiladores inverter U1/V1/W1.",
        "Comprobar el módulo antes de sustituir motor o placa.",
        "Las seis lecturas por ventilador deben quedar entre 0,3 y 0,7 V; 0 indica módulo dañado.",
        ["Espere 2 min sin tensión.", "Compruebe también bobinados iguales y aislamiento."],
        [step("prepare", 1, "Corte tensión y desconecte U1/V1/W1."),
         step("procedure", 1, "Realice las seis mediciones P/N con modo diodo."),
         step("verify", 1, "Todas deben estar entre 0,3 y 0,7 V.")],
        "GMV6", "80", "81", unit_scope="outdoor")

    add(16, "GMV6 — comprobar transductores con manómetro",
        "Sistema con lectura de alta/baja disponible en mando o monitor.",
        "Diferenciar presión real de sensor desviado.",
        "En frío compare baja; en calor compare alta. La lectura del sistema debe quedar dentro de ±10 % del manómetro.",
        ["LP=CN426 azul; HP=CN425 rojo.", "bJ puede indicar conectores invertidos."],
        [step("prepare", 1, "Conecte manómetro y confirme válvulas abiertas."),
         step("procedure", 1, "Estabilice en frío para baja o en calor para alta."),
         step("verify", 1, "Compare monitor y manómetro; tolerancia ±10 %.")],
        "GMV6", "82", "83", unit_scope="outdoor")

    quick_rows = [
        ("COM–N split", "~56 VDC", "ENVO", "63"),
        ("NTC ambiente", "15 kΩ a 25 °C", "GMV6", "60"),
        ("NTC tubería", "20 kΩ a 25 °C", "GMV6", "61"),
        ("NTC descarga", "49,191 kΩ a 25 °C", "GMV6", "62"),
        ("Bobina cuatro vías", "1880 Ω ±10 %", "GMV6", "63"),
        ("Bobinas solenoides", "1830 Ω ±10 %", "GMV6", "63"),
        ("EEV exterior", "46 Ω ±3,7 Ω; 480 pulsos", "GMV6", "66"),
        ("Compresor", "0,197 Ω ±7 %; aislamiento >10 MΩ", "GMV6", "73"),
    ]
    for name, value, ref, page in quick_rows:
        add(17, f"Referencia rápida — {name}", f"Valor exclusivo de la familia {SOURCES[ref]['document_ref']}.",
            "Localizar un valor sin recorrer el procedimiento completo.",
            value, ["Confirme componente, familia y condiciones de medida.", "Corte tensión cuando corresponda."],
            [step("prepare", 1, "Identifique la familia y el componente."),
             step("procedure", 1, f"Mida según procedimiento; referencia: {value}."),
             step("verify", 1, "Si no coincide, descarte cableado y condiciones antes de sustituir.")],
            ref, page)

    status_rows = [
        ("A0", "Esperando commissioning; el sistema aún no está autorizado para servicio."),
        ("A3", "Desescarche normal; no necesita acción."),
        ("A4", "Retorno de aceite normal; no necesita acción."),
        ("db", "Depuración de campo; las interiores no pueden operarse durante el proceso."),
        ("A9", "Setback activo; puede arrancar automáticamente por límites de temperatura."),
        ("AJ", "Recordatorio de filtro generado por horas configuradas."),
    ]
    for code, text in status_rows:
        add(18, f"{code} — estado normal o función", f"Display GMV o mando muestra {code}.",
            "Evitar sustituir componentes por un estado previsto.",
            text, ["Compruebe si el estado termina por sí mismo.", "Busque avería acompañante solo si existe."],
            [step("prepare", 1, f"Confirme el código {code}."),
             step("procedure", 1, "Observe modo, tiempo y otros códigos."),
             step("verify", 1, "Intervenga solo si la secuencia no finaliza o aparece una avería real.")],
            "GMV6", "35" if code != "db" else "39")

    add(19, "GMV5 — Commissioning Tool Kit por USB",
        "PC, convertidor USB Gree y conexión al sistema GMV.",
        "Ver datos en tiempo real y seguir la depuración por etapas.",
        "La herramienta integra monitorización, control y commissioning; muestra etapas OK o con incidencia.",
        ["Use el convertidor Gree MC40-00/B o el indicado.", "No confunda el bus de aire acondicionado con USB directo."],
        [step("prepare", 1, "Instale software/controlador y conecte el convertidor."),
         step("procedure", 1, "Abra Debug y pulse Start."),
         step("procedure", 2, "Revise cada etapa y los datos en tiempo real."),
         step("verify", 1, "Guarde el resultado de commissioning.")],
        "GMV5O", "24", "29", system_type="GMV5")

    add(19, "GMV6 — consulta n7 sin ordenador",
        "Placa exterior maestra con display.",
        "Leer frecuencia, presiones, temperaturas, corriente y EEV.",
        "n7 permite consultar 33 parámetros; nE indica un valor negativo.",
        ["Frecuencias, alta/baja, descarga, corriente y posición de EEV.", "Algunos valores no están disponibles desde mando."],
        [step("prepare", 1, "Entre en consulta con SW2 >5 s y seleccione n7."),
         step("procedure", 1, "Elija módulo y parámetro con SW1/SW2."),
         step("verify", 1, "Registre valor, modo y carga para interpretarlo.")],
        "GMV6", "29", "31", system_type="GMV6",
        monitoring=[
            {"point_code": "01", "name": "Temperatura exterior", "unit": "°C", "notes": None},
            {"point_code": "02", "name": "Frecuencia compresor 1", "unit": "Hz", "notes": None},
            {"point_code": "05", "name": "Alta del módulo", "unit": "temperatura equivalente", "notes": None},
            {"point_code": "06", "name": "Baja del módulo", "unit": "temperatura equivalente", "notes": None},
            {"point_code": "25", "name": "EEV calefacción 1", "unit": "pulsos/10", "notes": None},
        ])

    add(20, "Interior GMV — recuperar jumper y DIP de capacidad",
        "PCB interior de recambio sin configuración de la máquina original.",
        "Evitar d9, dC, LJ, LC y fallos de comunicación después del cambio.",
        "El jumper no viene necesariamente con el repuesto y los DIP deben copiarse de la placa original.",
        ["Fotografíe antes de desmontar.", "Copie solo ajustes documentados.", "Ejecute commissioning cuando aplique."],
        [step("prepare", 1, "Corte tensión y fotografíe jumper, DIP, conectores y direcciones."),
         step("procedure", 1, "Transfiera jumper y posiciones a la placa compatible."),
         step("verify", 1, "Alimente, compruebe códigos y complete depuración.")],
        "GMV6", "37", "40", unit_scope="indoor")

    add(20, "Exterior GMV — depuración obligatoria tras PCB",
        "Placa principal exterior sustituida.",
        "Recuperar capacidad, direcciones y autorización de marcha.",
        "GMV5 indica que después de sustituir la placa principal debe ejecutarse depuración.",
        ["SA1 de capacidad solo se modifica para reemplazo.", "Compruebe dirección centralizada y número de unidades."],
        [step("prepare", 1, "Copie SA1/SA2 y ajustes antes de retirar la placa."),
         step("procedure", 1, "Instale, verifique cableado y configure capacidad/dirección."),
         step("procedure", 2, "Ejecute commissioning completo."),
         step("verify", 1, "Confirme n9, n8, códigos y parámetros.")],
        "GMV5O", "86", "93", unit_scope="outdoor")

    family_rows = [
        ("Split residencial", "Una interior mural y una exterior; códigos C5/E6/H5/F1… y comunicación COM/N.", "ENVO", "57"),
        ("Cassette All Match", "Panel de techo, bomba y boya; E9 puede significar bandeja llena.", "CASS9", "58"),
        ("Conductos Slim Duct", "Unidad oculta con mando cableado, presión estática y E9 de agua.", "SLIM", "1"),
        ("GMV/MultiPRO", "Varias interiores, D1/D2, display exterior, códigos L/d/E/F/J/P/H/b/A.", "GMV6", "35"),
    ]
    for name, text, ref, page in family_rows:
        add(21, f"Familia — {name}", text,
            "Elegir el procedimiento correcto sin introducir un modelo exacto.",
            text, ["Observe tipo de unidad, mando, bornes y display.", "No use un código aislado para decidir la familia."],
            [step("prepare", 1, "Identifique físicamente equipo, mando, bornes y display."),
             step("procedure", 1, "Seleccione la familia que coincide con esas pistas."),
             step("verify", 1, "Confirme que la fuente contiene el mismo tipo de indicación.")],
            ref, page)

    add(22, "E9 puede ser aire frío o agua llena",
        "E9 aparece en split y cassette con significados opuestos.",
        "Evitar diagnosticar la boya de un split o ignorar agua en un cassette.",
        "En Envo E9 es prevención de aire frío; en cassette E9 es bandeja llena tras 8 s de boya abierta.",
        ["Identifique tipo de unidad y forma de indicación.", "Revise efecto operativo y fuente de cada interpretación."],
        [step("prepare", 1, "Determine si es split o cassette."),
         step("procedure", 1, "Abra todas las interpretaciones de E9."),
         step("verify", 1, "Elija solo la que coincide con la arquitectura y comportamiento.")],
        "CASS9", "58")

    add(22, "C5, L3, F0 y H5 cambian entre familias",
        "Código corto mostrado sin contexto.",
        "Usar todas las interpretaciones sin convertir una en universal.",
        "C5 puede ser jumper o dirección; L3 ventilador exterior o agua; F0 refrigerante o PCB; H5 IPM o ventilador.",
        ["La aplicación conserva cada interpretación con su fuente.", "El técnico decide por tipo de equipo y efecto."],
        [step("prepare", 1, "Anote equipo, unidad que muestra el código y modo."),
         step("procedure", 1, "Compare títulos, efectos y comprobaciones de todas las variantes."),
         step("verify", 1, "Confirme la familia antes de medir.")],
        "GMV6", "36", "41")

    add(21, "Familia — Livo GEN3 de generación 2020",
        "Split mural con tabla de códigos E/F/H/P y estados de frecuencia.",
        "Reconocer una generación anterior y conservar sus diferencias operativas.",
        "La tabla Livo distingue protecciones que paran la demanda de estados que solo reducen frecuencia.",
        ["EU, F6, F8, F9 y FH limitan frecuencia.", "P0–P3 son estados de prueba, no fallos.", "Fo es recuperación de refrigerante."],
        [step("prepare", 1, "Identifique el display dual-8 y la familia split."),
         step("procedure", 1, "Compare el código con la tabla de generación 2020."),
         step("verify", 1, "Compruebe si la máquina para o solo reduce frecuencia.")],
        "LIVO", "54", "56", system_type="Split Livo GEN3")

    add(21, "Familia — Vireo GEN3 R410A",
        "Split mural Vireo con mando YAP1F7F y display dual-8.",
        "Elegir la interpretación Vireo cuando un código coincide con otras familias.",
        "Vireo documenta el efecto exacto por modo y separa protección, limitación y Test Run.",
        ["E1–E8 detienen cargas según frío/calor.", "EU/F6/F8/F9/FH reducen frecuencia.", "P0–P3 identifican frecuencia de prueba."],
        [step("prepare", 1, "Confirme familia, tensión y mando."),
         step("procedure", 1, "Abra todas las interpretaciones del código."),
         step("verify", 1, "Use la variante Vireo solo si coincide el comportamiento.")],
        "VIREO", "49", "52", system_type="Split Vireo GEN3")

    add(9, "Cassette 30/36K — identificar bomba AC/DC y entrada de nivel",
        "Cassette comercial de mayor potencia con PCB que separa bomba y sensor de nivel.",
        "Reconocer la variante antes de medir o sustituir.",
        "La documentación muestra una entrada dedicada de nivel, salida de bomba y variantes AC/DC según placa.",
        ["No aplicar automáticamente el pinout del cassette 9–24K.", "Compruebe el esquema impreso de la placa instalada."],
        [step("prepare", 1, "Corte tensión e identifique la placa por sus conectores."),
         step("procedure", 1, "Localice entrada de nivel y salida de bomba del esquema correcto."),
         step("verify", 1, "Pruebe boya, bomba y drenaje antes de rearmar.")],
        "CASS30", "17", "18", system_type="Cassette 30/36K", unit_scope="indoor")

    return [topics[i] for i in sorted(topics)]


def build_search(topics: list[dict[str, Any]], error_indexes: list[dict[str, Any]],
                 error_details: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    def synonyms(value: str) -> str:
        norm = normalize(value)
        extra = []
        if "BOYA" in norm or "AGUA" in norm:
            extra.append("flotador float switch water overflow desbordamiento")
        if "RECUPER" in norm or "PUMP DOWN" in norm:
            extra.append("recogida refrigerante A2 Fo")
        if "MANDO" in norm:
            extra.append("wired controller control remoto XK19 XK46 XK79")
        if "COMUNIC" in norm or "BUS" in norm:
            extra.append("datos CAN COM N D1 D2 H1 H2")
        if "DEPUR" in norm:
            extra.append("debug debugging commissioning puesta marcha")
        return " ".join([value] + extra)

    for topic in topics:
        category = topic["category"]
        for item in topic["variants"]:
            body = " ".join([
                item["title"], item["recognition"], item["purpose"], item["summary"],
                " ".join(x["body"] for x in item["sections"]),
                " ".join((x["instruction"] or "") + " " + (x["expected_result"] or "") for x in item["steps"]),
                " ".join(str(v or "") for v in (item.get("controller") or {}).values()),
                " ".join(
                    " ".join([p["parameter_code"], p["name"], p["description"]] +
                             [o["option_value"] + " " + o["option_label"] + " " + o["effect"] for o in p["options"]])
                    for p in item.get("parameters", [])
                ),
                category["name"], topic["title"],
            ])
            entries.append({
                "type": "variant", "id": item["id"], "topic_id": topic["id"],
                "category_slug": category["slug"], "category": category["name"],
                "title": item["title"], "summary": item["summary"],
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
                        " ".join(str(value) for value in (
                            point.get("variable_value"),
                            point.get("value_nominal"),
                            point.get("value_text"),
                        ) if value is not None)
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
            "type": "error", "id": index["id"], "topic_id": None,
            "category_slug": "errors", "category": CAT["errors"]["name"],
            "title": f"{index['code_display']} — {index['short_label']}",
            "summary": detail["interpretations"][0]["description"],
            "haystack": normalize(synonyms(body)),
        })
    return entries


def main() -> int:
    expected = (ROOT / "data" / "brands" / "gree").resolve()
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
            "id": topic["id"], "slug": topic["slug"], "title": topic["title"],
            "summary": topic["summary"], "active": 1,
            "variant_count": len(topic["variants"]),
        })
        for item in topic["variants"]:
            variant_map[str(item["id"])] = topic["id"]
        write_json(WEB_DIR / "topics" / f"{topic['id']}.json", topic)

    navigation_categories = [
        {
            "id": category_id, "slug": slug, "name": name, "description": desc,
            "sort_order": order * 10, "active": 1,
            "topics": topics_by_category.get(slug, []),
        }
        for order, (category_id, slug, name, desc) in enumerate(CATEGORIES, 1)
    ]

    for detail in error_details:
        write_json(WEB_DIR / "errors" / "details" / f"{detail['id']}.json", detail)
    write_json(WEB_DIR / "errors" / "index.json", error_indexes)
    write_json(WEB_DIR / "search.json", search_entries)
    write_json(WEB_DIR / "variant_map.json", variant_map)

    write_json(WEB_DIR / "sources.json", [
        {
            "id": source_id, "title": row["title"], "document_ref": row["document_ref"],
            "publication_date": row["publication_date"], "language": row["language"],
            "document_type": row["document_type"], "source_url": row["source_url"],
            "status": "reviewed", "notes": row["notes"],
        }
        for source_id, row in enumerate(SOURCES.values(), 1)
    ])

    coverage_notes = {
        "errors": "Split, cassette, conductos, GMV5/GMV6 y mandos con interpretaciones separadas.",
        "diagnostic_access": "XK46 C01, XK79, LED de cassette, display exterior y dirección.",
        "history_reset": "n6, cinco fallos, dirección, borrado y salida.",
        "service_modes": "A2, Fo, A8, n3 y C9 con límites y salida.",
        "configuration": "C00/P00, P10/P13/P14/P30, A6/A7 y restauraciones 0C.",
        "controllers_buses": "XK19/XK46/XK79, H1/H2, D1/D2 y prueba COM–N.",
        "drainage_overflow": "E9 tras 8 s, L3 GMV, nivelación, bomba y boya.",
        "commissioning": "Test individual y depuración obligatoria GMV5/GMV6.",
        "multisplit": "Conflicto de modo y control de grupo hasta 16 interiores.",
        "gmv_network": "n8, n9, proyecto, capacidad y emergencia modular.",
        "component_checks": "NTC, bobinas, EEV, compresor, IPM, fan y presión.",
        "technical_values": "Valores exactos con familia y página.",
        "normal_states": "A0/A3/A4/A9/AJ/db y distinción de avería.",
        "service_tools_boards": "Commissioning Tool, n7 y ajustes tras sustituir PCB.",
        "system_architecture": "Pistas para split, cassette, conductos y GMV.",
    }
    write_json(WEB_DIR / "coverage.json", [
        {
            "id": category_id, "brand_id": BRAND_ID, "area_slug": slug,
            "area_name": name, "equipment_scope": "Gree — corpus Referencia V1",
            "coverage_status": "reference_v1", "source_count": len(SOURCES),
            "notes": coverage_notes[slug], "last_reviewed": now[:10],
        }
        for category_id, slug, name, _ in CATEGORIES
    ])

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
            "data_version": "1.0.0",
            "last_update_utc": now,
            "reference_brand": "Gree",
            "verification_warning": (
                "Completa respecto al corpus Gree Referencia V1. "
                "Confirme siempre familia, unidad que muestra el código y forma de indicación."
            ),
        },
        "categories": navigation_categories,
    })

    brand = {
        "slug": "gree", "name": "Gree", "display_name": "Gree", "enabled": True,
        "web_data": "web", "media": "media", "publish_media": False,
        "static_site": True, "schema_version": "2.2.0", "data_version": "1.0.0",
        "exported_at_utc": now, "counts": counts,
        "notes": (
            "Gree Referencia V1: split actual y antiguo, cassette, conductos, "
            "GMV5/GMV6, XK19/XK46/XK79, drenaje, buses y modos de servicio."
        ),
    }
    write_json(BRAND_DIR / "brand.json", brand)

    from audit_brand_quality import audit_brand

    quality = audit_brand(BRAND_DIR)
    write_json(WEB_DIR / "quality.json", quality)
    print(json.dumps({
        "brand": brand["slug"], "counts": counts,
        "interpretations": quality["errors"]["interpretations"],
        "error_quality": quality["errors"]["status_counts"],
        "variant_quality": quality["technical_variants"]["status_counts"],
        "sources": len(SOURCES),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
