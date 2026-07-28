#!/usr/bin/env python3
"""Construye LG Referencia V1 para Super Técnico.

La proyección pública contiene resúmenes técnicos trazables a documentación
oficial de LG. No publica PDF, capturas, bases privadas ni material gráfico
de los manuales.
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
BRAND_DIR = ROOT / "data" / "brands" / "lg"
WEB_DIR = BRAND_DIR / "web"
BRAND_ID = 7


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


def split_items(value: str) -> list[str]:
    return [item.strip() for item in value.split("|") if item.strip()]


SOURCES: dict[str, dict[str, Any]] = {
    "SZ2015": {
        "title": "General Service Manual - Single Zone",
        "document_ref": "MFL41161610",
        "publication_date": "2015",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://legacy.lghvac.com/resource-service?filename=General_Service_Manual_MFL41161610_All_SZ.pdf",
        "notes": "Split y Single Zone: códigos CH, LED, Test Run, marcha forzada, Pump Down y diagnóstico eléctrico.",
    },
    "MULTIF": {
        "title": "Multi F / Multi F MAX Outdoor Unit Installation Manual",
        "document_ref": "IM_MultiF_ODU",
        "publication_date": "2024",
        "language": "en",
        "document_type": "installation_service_manual",
        "source_url": "https://lghvac.com/resource-service?filename=IM_MultiF_ODU.pdf",
        "notes": "Multisplit: cableado, DIP, refrigeración forzada, estados de parada, LGMV y códigos.",
    },
    "CASSETTE": {
        "title": "Multi F Ceiling Cassette Indoor Unit Installation Manual",
        "document_ref": "IM_Multi_F_CeilingCassette",
        "publication_date": "2024",
        "language": "en",
        "document_type": "installation_service_manual",
        "source_url": "https://lghvac.com/resource-service?filename=IM_Multi_F_CeilingCassette.pdf",
        "notes": "Cassette: bomba, boya, prueba de drenaje, LED, funcionamiento forzado y códigos con estado operativo.",
    },
    "MULTIV5": {
        "title": "MULTI V 5 Outdoor Unit Service Manual",
        "document_ref": "SM_MultiV_5_OutdoorUnits",
        "publication_date": "2024",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://lghvac.com/resource-service?filename=SM_MultiV_5_OutdoorUnits.pdf",
        "notes": "VRF: direccionamiento, niveles de respuesta, códigos con sufijo de bastidor, FDD, LGMV y respaldo.",
    },
    "PREMTB101": {
        "title": "Standard III Wired Remote Controller PREMTB101",
        "document_ref": "IM StandardIII Wired Remote PREMTB101",
        "publication_date": "2025",
        "language": "en",
        "document_type": "controller_manual",
        "source_url": "https://lghvac.com/resource-service?filename=IM+StandardIII+Wired+Remote+PREMTB101.pdf",
        "notes": "Mando actual de tres hilos: historial de 20 errores, instalación, grupo, Test Run y ajustes de instalador.",
    },
    "PREMTC00U": {
        "title": "Simple Wired Remote Controller PREMTC00U",
        "document_ref": "MFL62862020",
        "publication_date": "2019",
        "language": "en",
        "document_type": "controller_manual",
        "source_url": "https://lghvac.com/resource-service?filename=IM_SimpleRemoteController_PREMTC00U.pdf",
        "notes": "Mando sencillo: tres hilos, códigos de función, Test Run, ESP, sensores y maestro/esclavo.",
    },
    "LGMV": {
        "title": "LG Design and Service Tools - LG Monitoring View",
        "document_ref": "LG-HVAC-LGMV",
        "publication_date": "2026",
        "language": "en",
        "document_type": "official_web_resource",
        "source_url": "https://lghvac.com/lg-design-and-service-tools/",
        "notes": "Recurso oficial sobre LGMV y monitorización/gráficas de valores en tiempo real.",
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
    (1, "errors", "Errores y protecciones", "Códigos CH, patrones LED, subcódigos Multi V y efectos por familia."),
    (2, "diagnostic_access", "Obtención de códigos y subcódigos", "Lectura desde display, LED, mando cableado, placa exterior y LGMV."),
    (3, "history_reset", "Historial y borrado", "Historial del mando, rearme, tiempos de descarga y respuestas Multi V."),
    (4, "service_modes", "Modos de servicio", "Marcha forzada, refrigeración forzada, Pump Down, FDD y respaldo."),
    (5, "configuration", "Configuración y programación", "Códigos de instalador, DIP switch, ESP, sensores y límites."),
    (6, "controllers_buses", "Mandos y buses", "PREMTB101/PREMTC00U, tres hilos, 12 V, grupo y fallos del mando."),
    (7, "drainage_overflow", "Drenaje y desbordamiento", "Bomba, boya, CH04, prueba de desagüe y comportamiento de cassette."),
    (8, "commissioning", "Puesta en marcha", "Comprobaciones previas, Test Run, auto address e Integrated Test Run."),
    (9, "multisplit", "Multi F y Multi F MAX", "Cableado, unidades BD, conflicto de modo, DIP y continuidad de unidades."),
    (10, "multi_v_network", "MULTI V y red", "Bastidores master/slave, RS-485, auto addressing, HR y niveles de parada."),
    (11, "component_checks", "Comprobación de componentes", "Sondas, presiones, compresor, inverter, ventiladores, EEV, bomba y boya."),
    (12, "technical_values", "Valores técnicos", "Tensiones, umbrales, colores, cableado y puntos de medida documentados."),
    (13, "normal_states", "Comportamientos normales", "Retardos, desescarche, retorno de aceite, hot start y esperas."),
    (14, "service_tools_boards", "Herramientas y placas", "LGMV, SIMs, FDD y pasos tras sustituir una placa."),
    (15, "system_architecture", "Arquitectura de sistemas", "Pistas para distinguir Single Zone, Multi F, cassette y MULTI V."),
]

CATEGORY_BY_SLUG = {
    slug: {"id": ident, "slug": slug, "name": name, "description": description}
    for ident, slug, name, description in CATEGORIES
}


def operational_impact(behavior: str) -> dict[str, Any]:
    value = normalize(behavior)
    if "TODO EL SISTEMA" in value or "TODAS LAS UNIDADES" in value:
        level = "all_system"
    elif "SOLO" in value or "UNIDAD AFECTADA" in value:
        level = "affected_unit"
    elif "CONTINUA" in value or "REINTENTA" in value or "LIMITA" in value:
        level = "warning"
    else:
        level = "protected_stop"
    return {
        "stop_level": level,
        "summary": behavior,
        "affected_scope": "Alcance documentado para la familia indicada en esta interpretación.",
        "unaffected_scope": None,
        "restart_behavior": "Corregir la causa y aplicar el rearme descrito para la familia; no borrar antes de anotar el código.",
        "degraded_behavior": None,
        "notes": "No se generaliza el mismo alcance a otra familia LG.",
    }


def technical_dataset(dataset_id: int, spec: dict[str, str]) -> dict[str, Any]:
    return {
        "id": dataset_id,
        "name": f"{spec['code']} - referencia técnica documentada",
        "dataset_type": "technical_reference",
        "variable_name": "Comprobación",
        "variable_unit": None,
        "value_name": "Dato",
        "value_unit": None,
        "tolerance_text": "Aplicar únicamente a la familia y forma de indicación de esta interpretación.",
        "source_kind": "official",
        "calculation_method": None,
        "review_status": "reviewed",
        "notes": spec["value"],
        "visible": 1,
        "points": [{
            "variable_value": None,
            "value_min": None,
            "value_nominal": None,
            "value_max": None,
            "value_text": spec["value"],
            "sort_order": 1,
            "notes": None,
        }],
        "sources": [source(spec["ref"], spec["page"], spec["source_section"])],
    }


def error_spec(
    code: str,
    title: str,
    scope: str,
    ref: str,
    page: str,
    description: str,
    causes: str,
    checks: str,
    behavior: str,
    value: str,
    aliases: str = "",
    source_section: str = "Error codes",
) -> dict[str, str]:
    return {
        "code": code,
        "title": title,
        "scope": scope,
        "ref": ref,
        "page": page,
        "description": description,
        "causes": causes,
        "checks": checks,
        "behavior": behavior,
        "value": value,
        "aliases": aliases,
        "source_section": source_section,
    }


ERROR_SPECS: list[dict[str, str]] = []


INDOOR_ERRORS = [
    ("01", "Sonda de aire de retorno interior", "La entrada de la sonda de ambiente está abierta o en cortocircuito.", "Sonda NTC defectuosa|Cable o conector abierto|Entrada de placa interior", "Medir la sonda desconectada|Revisar continuidad y conector|Comparar lectura real con LGMV cuando esté disponible", "La unidad interior afectada queda OFF.", "LED de unidades: 1 parpadeo; Multi F indica estado OFF."),
    ("02", "Sonda de tubería de entrada interior", "La sonda de tubería de entrada está abierta o en cortocircuito.", "Sonda defectuosa|Contacto térmico deficiente|Cable o placa", "Medir NTC|Revisar fijación a tubería|Comprobar conector de placa", "La unidad interior afectada queda OFF.", "LED de unidades: 2 parpadeos; Multi F indica estado OFF."),
    ("03", "Comunicación entre mando cableado y unidad interior", "La placa interior no recibe la señal del mando cableado.", "Cable de mando abierto o cruzado|Rojo/amarillo/negro incorrectos|Mando o placa interior|Configuración maestro/esclavo", "Comprobar 12 V, señal y GND|Revisar longitud máxima de 50 m|Probar mando/cable conocido|Revisar maestro/esclavo", "La unidad asociada queda sin control desde ese mando y aparece OFF en Multi F.", "Mando LG de tres hilos: rojo 12 V, amarillo señal, negro GND."),
    ("04", "Bomba de drenaje, boya o desbordamiento", "La entrada de drenaje detecta bomba/float switch anormal o nivel alto.", "Bomba bloqueada|Boya atascada|Tubo obstruido o sin pendiente|Cable/conector|Placa interior", "Comprobar agua real y desagüe|Accionar prueba de bomba|Verificar continuidad de boya|Revisar salida de placa", "La cassette afectada queda OFF; la prueba debe repetirse tras corregir el drenaje.", "Cassette Multi F: código 4 y estado OFF; LED de unidades: 4 parpadeos."),
    ("05", "Comunicación entre unidad interior y exterior", "La interior no recibe señal válida de la placa exterior.", "Unidad exterior sin alimentación|Cableado de potencia/comunicación incorrecto|Polaridad o blindaje|PCB interior/exterior", "Comprobar alimentación de ambas unidades|Comparar bornes extremo a extremo|Revisar cable y tierra|Observar LED exterior", "La unidad afectada queda OFF; en Multi V la respuesta es de comunicación y se borra al restablecerse.", "Single Zone/Multi F: CH05; Multi V: ausencia de señal durante el tiempo de supervisión."),
    ("06", "Sonda de tubería de salida interior", "La sonda de tubería de salida está abierta o en cortocircuito.", "Sonda defectuosa|Conector o cable|Entrada de PCB", "Medir sonda y comparar con temperatura real|Revisar fijación|Comprobar placa", "La unidad interior afectada queda OFF.", "LED de unidades: 6 parpadeos; Multi F indica estado OFF."),
    ("07", "Conflicto de modo en sistema multisplit", "Las interiores solicitan modos incompatibles en una aplicación de bomba de calor.", "Una unidad pide frío y otra calor|Mando maestro fija el ciclo|Ajuste de override maestro/esclavo", "Identificar la primera unidad que fijó el modo|Unificar demandas|Revisar override master/slave", "La unidad con demanda incompatible queda OFF; las unidades compatibles pueden continuar.", "Multi F: código 07, different mode operation, estado OFF de la unidad incompatible."),
    ("09", "EEPROM de unidad interior", "La memoria de la placa interior no contiene datos válidos o no comunica.", "EEPROM ausente o mal insertada|Datos de modelo/capacidad corruptos|Placa sustituida sin configurar", "Cortar alimentación|Revisar inserción/orientación si es extraíble|Confirmar placa y capacidad correctas", "La unidad interior afectada queda OFF.", "Multi F: serial EEPROM 0 o FFFFFF; estado OFF."),
    ("10", "Motor BLDC de ventilador interior bloqueado", "No se detecta giro válido del ventilador interior.", "Aspa bloqueada|Conector desconectado|Motor defectuoso|Alimentación o placa interior", "Comprobar giro libre sin tensión|Revisar conector|Medir alimentaciones con procedimiento seguro|Descartar PCB", "La unidad interior afectada queda OFF.", "LED de decenas: 1 parpadeo; Multi F indica estado OFF."),
    ("12", "Sonda de tubería intermedia interior", "La entrada de la sonda intermedia se detecta fuera de rango.", "Sonda abierta/cortocircuitada|Cable o conector|PCB", "Medir resistencia|Contrastar temperatura|Revisar conector y placa", "La función dependiente de la sonda se detiene.", "Single Zone: LED unidades 2 y decenas 1."),
]

for code, title, description, causes, checks, behavior, value in INDOOR_ERRORS:
    ERROR_SPECS.append(error_spec(
        f"CH{code}", title, "indoor", "MULTIF" if code != "12" else "SZ2015",
        "92" if code != "12" else "26", description, causes, checks, behavior, value,
        aliases=f"{code}|{int(code)}|CH {code}",
    ))

# La cassette aporta una secuencia propia de drenaje que no debe diluirse en la interpretación genérica.
ERROR_SPECS.append(error_spec(
    "CH04", "Cassette: nivel alto, bomba y boya", "indoor", "CASSETTE", "59",
    "La cassette presenta el fallo de drenaje en sus LED, en el mando cableado o en LGMV.",
    "Bomba de drenaje sin caudal|Boya bloqueada mecánicamente|Desagüe obstruido|Unidad desnivelada",
    "Revisar horizontalidad|Ejecutar la prueba de bomba|Comprobar que la boya cambia de estado|Confirmar salida libre",
    "Solo la cassette afectada queda OFF en Multi F; anotar el código antes de cortar alimentación.",
    "Código 4; estado de operación interior OFF; LED y botón Forced Operation visibles en el receptor.",
    aliases="4|CH 4|DRAIN|FLOAT",
    source_section="Four-way ceiling cassette error codes",
))


SINGLE_ZONE_OUTDOOR = [
    ("21", "Pico DC / fallo IPM", "El inverter detecta sobrecorriente instantánea.", "Compresor bloqueado|U/V/W incorrectos|IPM o placa inverter|Tensión anormal", "Comprobar bobinados y aislamiento|Revisar U/V/W|Medir alimentación y bus DC|Seguir prueba de IPM", "El compresor se detiene por protección.", "LED decenas 2 y unidades 1."),
    ("22", "Sobrecorriente de entrada CT2", "La corriente AC medida supera el límite.", "Carga frigorífica anormal|Compresor|Sensor CT|Tensión de red", "Medir tensión/corriente|Revisar presiones|Comprobar CT y placa", "La exterior detiene el compresor.", "LED 2/2; Multi F estado OFF."),
    ("23", "Bus DC bajo o alto", "La tensión del DC link sale de rango.", "Red baja/alta|Rectificador, condensador o reactor|Conexión floja", "Medir red|Esperar descarga|Medir bus DC con procedimiento seguro|Revisar rectificación", "La exterior queda OFF.", "Multi F: <140 VDC o >420 VDC en la familia documentada."),
    ("25", "Tensión AC alta o baja", "La alimentación de entrada sale del rango permitido.", "Red fuera de rango|Bornes flojos|Protección o cable insuficiente", "Medir tensión durante arranque|Revisar bornes y caída de tensión|Comprobar fases cuando aplique", "La exterior queda OFF.", "Multi F: LED 2/5."),
    ("26", "Posición/arranque del compresor inverter", "El compresor no consigue iniciar correctamente.", "Compresor bloqueado|U/V/W incorrectos|Presiones no igualadas|Inverter", "Esperar igualación|Comprobar bobinados/aislamiento|Revisar U/V/W|Descartar módulo", "El intento de arranque se cancela.", "LED 2/6."),
    ("27", "Fallo PFC/PSC", "La etapa de corrección de factor de potencia detecta corriente anormal.", "Reactor|PFC/PSC|Red|Cortocircuito en bus", "Medir red y bus|Revisar reactor y conexiones|Seguir diagnóstico de PFC", "La exterior queda OFF.", "LED 2/7."),
    ("29", "Sobrecorriente de fase del compresor", "La corriente de una fase del compresor supera el límite.", "Compresor|Presión anormal|U/V/W|Módulo inverter", "Medir corriente|Comprobar presiones|Revisar cableado y compresor", "La exterior queda OFF.", "LED 2/9."),
    ("32", "Temperatura de descarga del inverter alta", "La tubería de descarga supera el límite de protección.", "Falta de refrigerante|EEV|Sonda de descarga|Compresor", "Buscar fugas|Comparar presión/temperatura|Comprobar EEV y sonda", "Reduce frecuencia y detiene si persiste.", "LED 3/2."),
    ("34", "Presión alta", "La señal de alta presión supera el límite.", "Ventilación insuficiente|Válvula cerrada|Sobrecarga|Sensor", "Limpiar baterías|Comprobar ventiladores y válvulas|Medir presión|Contrastar sensor", "El compresor se detiene.", "LED 3/4."),
    ("35", "Presión baja", "La presión de aspiración cae por debajo del límite.", "Fuga|Válvula cerrada|Restricción|Sensor", "Buscar fugas|Abrir válvulas|Medir presiones|Revisar expansión y sensor", "El compresor se detiene.", "LED 3/5."),
    ("36", "Detección de fuga de refrigerante", "La lógica detecta condición compatible con fuga.", "Falta de refrigerante|Fuga|Sensor incorrecto|Restricción", "No añadir gas sin localizar la causa|Buscar fugas|Comprobar sensores/presiones", "La exterior detiene la operación protegida.", "Puede aparecer como CH36 o CH38 según familia; LED 3/6 o 3/8."),
    ("37", "Relación de compresión fuera de límite", "La diferencia/relación de presiones no corresponde a una marcha normal.", "Falta de refrigerante|Compresor sin rendimiento|Válvula de cuatro vías|EEV", "Medir alta/baja|Comprobar válvulas y EEV|Evaluar compresor", "La exterior protege el compresor.", "LED 3/7."),
    ("39", "Comunicación entre MICOM PFC e inverter", "Los microcontroladores de la etapa PFC y del inverter no intercambian datos válidos.", "Alimentación de placa|Conector o pista interna|Etapa PFC|Placa inverter", "Comprobar alimentación y conectores de placa|Revisar signos de daño en PFC/inverter|Aplicar el diagnóstico de placa del manual", "La exterior queda OFF.", "Multi F: LED 3/9 y estado OFF."),
    ("40", "Sensor de corriente CT", "La señal del sensor de corriente es incoherente.", "CT desconectado|Cableado|Placa inverter", "Revisar conexión|Comparar lectura LGMV con pinza|Descartar placa", "La exterior queda OFF.", "LED decenas 4."),
    ("41", "Sonda de descarga", "La sonda de descarga está abierta o en cortocircuito.", "NTC|Conector|Placa", "Medir NTC|Contrastar con temperatura|Revisar entrada", "La protección de descarga impide la marcha.", "LED 4/1."),
    ("42", "Sensor de baja presión", "La señal del sensor de baja presión está fuera de rango.", "Sensor|Conector|5 V de referencia|Presión real", "Comparar manómetro con LGMV|Comprobar alimentación/señal|Revisar cable", "La exterior queda OFF o limitada.", "LED 4/2."),
    ("43", "Sensor de alta presión", "La señal del sensor de alta presión está fuera de rango.", "Sensor|Conector|5 V|Presión real", "Comparar manómetro con LGMV|Medir referencia/señal|Revisar placa", "La exterior queda OFF.", "LED 4/3."),
    ("44", "Sonda de aire exterior", "La sonda de ambiente exterior está abierta o en cortocircuito.", "NTC|Cable|PCB", "Medir resistencia|Contrastar temperatura|Revisar conector", "El control dependiente de ambiente se limita o detiene.", "LED 4/4."),
    ("45", "Sonda intermedia de condensador", "La sonda intermedia de batería exterior está fuera de rango.", "NTC|Contacto térmico|Cable/placa", "Medir sonda|Revisar fijación|Comprobar placa", "La exterior protege el ciclo.", "LED 4/5."),
    ("46", "Sonda de aspiración", "La sonda de tubería de aspiración está abierta o en corto.", "NTC|Conector|Placa", "Medir NTC|Contrastar temperatura|Revisar entrada", "La exterior protege el compresor.", "LED 4/6."),
    ("48", "Sonda de salida de condensador o tubería líquida", "La sonda de salida del condensador/tubería líquida está abierta o en cortocircuito.", "NTC|Conector|Contacto térmico|Entrada de placa exterior", "Medir la sonda|Revisar fijación a la tubería|Comprobar cable, conector y entrada de placa", "La exterior queda OFF.", "Multi F: LED 4/8 y estado OFF."),
    ("51", "Capacidad interior/exterior incompatible", "La suma de capacidades conectadas está fuera del rango admitido.", "Combinación no válida|Placa o capacidad incorrecta|Unidad no detectada", "Comparar capacidades|Revisar unidades detectadas y placa de repuesto|Corregir configuración", "La puesta en marcha queda bloqueada.", "Multi F: menos del 50 % o más del 130 % de la capacidad exterior."),
    ("53", "Comunicación exterior-interiores", "La exterior no mantiene comunicación con una o más interiores.", "Cableado|Unidad sin alimentación|Dirección/conexión|PCB", "Identificar qué unidad no responde|Comprobar alimentación|Revisar bus y blindaje", "La unidad sin comunicación queda OFF; el alcance del resto depende de Multi F o Multi V.", "LED 5/3."),
    ("54", "Secuencia de fases o cableado exterior", "La exterior detecta fases invertidas o cableado no válido.", "Fases invertidas|Fase ausente|Bornes flojos", "Cortar alimentación|Comprobar secuencia y tensión entre fases|Corregir bornes", "La exterior no arranca.", "Multi F trifásico: LED 5/4."),
    ("60", "Checksum EEPROM de placa exterior", "La memoria de la placa exterior no supera su comprobación.", "EEPROM|Placa incorrecta|Datos dañados", "Revisar EEPROM/orientación|Confirmar repuesto y capacidad|Reiniciar", "La exterior queda OFF.", "Multi F: LED decenas 6."),
    ("61", "Temperatura de condensador alta", "La batería exterior alcanza una temperatura excesiva.", "Batería sucia|Ventilador|Sobrecarga|Sensor", "Limpiar|Comprobar ventilador|Medir presión y temperatura|Contrastar sonda", "La exterior limita o detiene el compresor.", "LED 6/1."),
    ("62", "Temperatura de disipador inverter alta", "El disipador supera el límite.", "Ventilación|Suciedad|Montaje IPM|Sonda", "Comprobar ventilador y disipador|Revisar pasta/montaje|Contrastar sonda", "La exterior queda OFF.", "LED 6/2."),
    ("65", "Sonda de disipador inverter", "La sonda del disipador está abierta o en cortocircuito.", "Sonda|Conector|Placa", "Medir sensor|Comprobar referencia y señal|Revisar placa", "La exterior queda OFF.", "Multi F: LED 6/5."),
    ("67", "Ventilador BLDC exterior bloqueado", "No se detecta giro válido del ventilador exterior.", "Aspa bloqueada|Motor|Conector|Placa", "Comprobar giro libre|Revisar conector|Medir alimentaciones/señal con seguridad", "El compresor se detiene.", "LED 6/7."),
    ("72", "Fallo de transferencia de válvula de cuatro vías", "La temperatura/presión no confirma la inversión de ciclo.", "Bobina|Válvula atascada|Cableado|Carga", "Comprobar bobina y tensión|Medir temperaturas|Revisar circuito frigorífico", "La exterior cancela el cambio de ciclo.", "Single Zone: LED 7/2."),
    ("73", "Sobrecorriente PFC", "La etapa PFC detecta pico de corriente.", "PFC|Reactor|Bus DC|Cortocircuito", "Medir red/bus|Revisar reactor y placa|Seguir procedimiento de PFC", "La exterior queda OFF.", "Multi F: LED 7/3."),
]

for code, title, description, causes, checks, behavior, value in SINGLE_ZONE_OUTDOOR:
    ref = "MULTIF" if code in {"21", "22", "23", "25", "26", "27", "29", "32", "35", "39", "40", "41", "43", "44", "45", "46", "48", "51", "53", "54", "60", "61", "62", "65", "67", "73"} else "SZ2015"
    page = "93" if ref == "MULTIF" else "28"
    aliases = f"{code}|CH {code}"
    if code == "36":
        aliases += "|CH38|38"
    ERROR_SPECS.append(error_spec(
        f"CH{code}", title, "outdoor", ref, page, description, causes, checks, behavior, value,
        aliases=aliases,
    ))


MULTIV_ERRORS = [
    ("21", "Fallo IPM de compresor por bastidor", "El driver detecta sobrecorriente en una fase.", "Compresor|IPM|U/V/W|Tensión baja", "Comprobar compresor, U/V/W y placa inverter", "El bastidor afectado detiene el inverter; el sistema aplica su nivel de respuesta.", "211 master; 212 slave 1; 213 slave 2.", "128"),
    ("22", "Sobrecorriente AC del inverter por bastidor", "La corriente de entrada RMS del inverter es excesiva.", "Tensión baja|EEV restringida|Sobrecarga de refrigerante|Inverter", "Medir red/corriente|Revisar EEV y carga|Comprobar placa", "El bastidor afectado se protege.", "221/222/223 identifican master/slave.", "128"),
    ("23", "DC link anormal por bastidor", "El enlace DC cae por debajo o supera los límites del bastidor.", "Condensador|Bus desconectado|Rectificador|Red", "Empezar en la salida del filtro de ruido|Medir red y bus con seguridad|Esperar descarga", "El bastidor afectado se detiene.", "231/232/233; el manual documenta 50 V mínimo y límites por tensión nominal.", "128"),
    ("24", "Presostato de alta presión por bastidor", "El sistema se apaga por la entrada del presostato de alta.", "Alta presión real|Presostato|Conector|Caudal", "Medir presión|Comprobar señal del presostato|Revisar ventiladores y válvulas", "El sistema se detiene por alta presión.", "241/242/243 según master/slave.", "128"),
    ("25", "Tensión de entrada alta o baja por bastidor", "La alimentación del bastidor sale del rango admitido.", "Red|Bornes|Fase|Cable", "Medir tensión bajo carga|Revisar bornes/fases|Comparar con rango del equipo", "El bastidor no permite marcha.", "251/252/253; los límites dependen de 208-230 V o 460 V.", "128"),
    ("26", "Compresor inverter no arranca por bastidor", "El inverter no consigue iniciar el compresor.", "Compresor bloqueado|U/V/W|Presiones|Placa", "Comprobar bobinados/aislamiento|Revisar fases del motor|Esperar igualación", "El intento de arranque se cancela.", "261/262/263.", "128"),
    ("29", "Sobrecorriente de compresor por bastidor", "La corriente del compresor inverter es demasiado alta.", "Compresor|Restricción|Presión|Inverter", "Medir corriente y presiones|Revisar circuito y placa", "El bastidor afectado detiene el compresor.", "291/292/293.", "128"),
    ("32", "Descarga alta de compresor 1", "La temperatura de descarga del compresor 1 aumenta en exceso.", "Falta de refrigerante|EEV|Sonda|Válvula de inyección", "Buscar fugas|Comprobar EEV y sonda|Contrastar temperatura", "El bastidor afectado se protege.", "321/322/323; el manual cita >115 °C durante 10 s.", "129"),
    ("33", "Descarga alta de compresor 2", "La temperatura de descarga del compresor 2 aumenta en exceso.", "Falta de refrigerante|EEV|Sonda|Compresor", "Revisar carga, EEV y sonda|Comparar compresores", "El bastidor afectado se protege.", "331/332/333.", "129"),
    ("34", "Protección de alta presión Multi V", "La alta supera el límite de seguridad.", "Ventilación|Carga|EEV|Válvula|Sensor", "Medir presión|Revisar ventiladores, filtros, válvulas y EEV", "El sistema se detiene por alta presión.", "341/342/343; el manual cita >4.000 kPa durante 10 s.", "129"),
    ("35", "Protección de baja presión Multi V", "La baja cae por debajo del límite permitido.", "Fuga|Restricción|Válvula cerrada|Sensor", "Buscar fugas|Medir presión|Revisar EEV/válvulas/sensor", "El sistema se detiene por baja presión.", "351/352/353.", "129"),
    ("36", "Diferencia de presión insuficiente / cuatro vías", "No se consigue diferencia normal tras un cambio de válvula.", "Válvula de cuatro vías|Compresor|Carga|Sondas", "Medir alta/baja|Comprobar bobina y válvula|Evaluar compresor", "El sistema cancela el ciclo anormal.", "361/362/363; se evalúa tras el cambio de posición.", "129"),
    ("40", "Sensor CT del compresor por bastidor", "La entrada del transformador de corriente es anormal.", "CT|Cable|Placa inverter", "Comparar corriente real/LGMV|Revisar CT y conexión", "El bastidor restringe o detiene el inverter.", "401/402/403.", "130"),
    ("41", "Sonda de descarga compresor 1", "La sonda de descarga del compresor 1 está fuera de rango.", "Sonda|Conector|Placa", "Medir resistencia/señal|Contrastar temperatura", "El bastidor se protege.", "411/412/413.", "130"),
    ("42", "Sensor de baja presión Multi V", "La señal del sensor de baja no es válida.", "Sensor|5 V|Conector|Placa", "Comparar manómetro con LGMV|Medir referencia/señal", "El sistema limita o detiene el control de presión.", "421/422/423.", "130"),
    ("43", "Sensor de alta presión Multi V", "La señal del sensor de alta no es válida.", "Sensor|5 V|Cable|Placa", "Comparar manómetro/LGMV|Medir referencia y señal", "El sistema se protege.", "431/432/433.", "130"),
    ("44", "Sonda de ambiente exterior por bastidor", "La sonda exterior está abierta o en cortocircuito.", "Sonda|Conector|PCB", "Medir NTC|Contrastar temperatura|Revisar entrada", "El bastidor limita las funciones dependientes del ambiente.", "441/442/443.", "130"),
    ("45", "Sonda de batería exterior por bastidor", "La sonda de intercambiador exterior está fuera de rango.", "NTC|Fijación|Cable|PCB", "Medir NTC|Revisar fijación y conector", "El bastidor se protege.", "451/452/453.", "130"),
    ("46", "Sonda de aspiración por bastidor", "La sonda de aspiración está abierta o en corto.", "NTC|Conector|PCB", "Medir NTC|Contrastar temperatura", "El control de sobrecalentamiento se protege.", "461/462/463.", "130"),
    ("47", "Sonda de descarga compresor 2", "La sonda de descarga del compresor 2 está fuera de rango.", "Sonda|Cable|PCB", "Medir y comparar con compresor 1|Revisar conector", "El bastidor se protege.", "471/472/473.", "130"),
    ("49", "Sonda de temperatura IPM", "La lectura térmica del módulo de potencia no es válida.", "Sensor IPM|Placa|Montaje", "Comprobar señal y montaje del módulo|Revisar placa", "El inverter queda protegido.", "491/492/493.", "130"),
    ("50", "Pérdida de fase", "Falta una fase en la alimentación del bastidor.", "Fusible|Borne|Cable|Red", "Medir R-S-T|Revisar fusibles y bornes", "El bastidor no arranca.", "501/502/503.", "130"),
    ("51", "Relación de capacidad fuera de rango", "La suma nominal de interiores no entra en la ventana permitida.", "Combinación incorrecta|Unidad no direccionada|Datos de capacidad", "Comparar inventario/direcciones/capacidades|Repetir auto address", "La puesta en marcha queda bloqueada.", "511; Multi V documenta menos del 50 % o más del 130 %.", "131"),
    ("52", "Comunicación main-inverter por bastidor", "La placa principal y la de inverter no intercambian datos.", "Conector|Alimentación de placa|PCB", "Revisar conectores y fuentes|Resetear tras comprobar", "El bastidor afectado queda fuera de servicio.", "521/522/523.", "131"),
    ("53", "Comunicación exterior-interior/HR por bastidor", "La placa principal no mantiene comunicación con la red de interiores/HR.", "Bus A/B|Unidad sin alimentación|Dirección|PCB", "Comprobar bus, tierra y alimentación|Identificar nodo ausente con LGMV", "Las unidades sin comunicación se detienen; el resto depende de topología.", "531/532/533.", "131"),
    ("57", "Comunicación main PCB-inverter PCB", "La placa inverter no recibe señal de la principal.", "Conector|Fuente|PCB", "Revisar cableado entre placas|Comprobar alimentaciones", "El bastidor afectado detiene el inverter.", "571/572/573.", "131"),
    ("60", "EEPROM de placa inverter", "La memoria de la placa inverter no se lee correctamente.", "EEPROM mal insertada|Pines doblados|Repuesto incorrecto", "Cortar alimentación|Revisar orientación/pines|Confirmar placa", "El bastidor queda fuera de servicio.", "601/602/603.", "131"),
    ("62", "Disipador inverter a alta temperatura", "La temperatura del disipador supera el límite.", "Ventilación|Suciedad|Sensor|Montaje", "Revisar ventiladores/disipador|Contrastar sensor|Comprobar montaje", "El bastidor se detiene por temperatura.", "621/622/623.", "131"),
    ("65", "Sonda de disipador inverter", "La sonda del disipador está abierta o en corto.", "Sonda|Conector|12/5 V|PCB", "Comprobar 12 V y 5 V según manual|Medir señal a GND", "El bastidor se protege.", "651/652/653.", "131"),
    ("67", "Ventilador exterior bloqueado", "No hay caudal por bloqueo o ausencia de giro.", "Aspa|Motor|Conector|Placa fan", "Comprobar giro libre|Revisar alimentaciones y señal", "El bastidor afectado detiene el compresor.", "671/672/673.", "131"),
    ("71", "Sensor CT del inverter / restricción", "La lectura de corriente del inverter es anormal.", "CT|Restricción|Placa", "Comparar corriente real/LGMV|Revisar CT y circuito", "El bastidor se restringe.", "711/712/713.", "131"),
    ("75", "Sensor CT de ventilador", "La detección de corriente del ventilador está abierta o en corto.", "CT fan|Cable|Placa", "Revisar sensor y conector|Comparar corriente", "El ventilador/bastidor se protege.", "751/752/753.", "131"),
    ("77", "Sobrecorriente de ventilador exterior", "La corriente del ventilador supera el límite.", "Motor bloqueado|Aspa|Placa fan|Tensión", "Comprobar giro|Medir corriente|Revisar placa", "El bastidor detiene el ventilador y el compresor.", "771/772/773; >10 A en 208-230 V o >5 A en 460 V.", "132"),
    ("79", "Fallo de posición/giro del ventilador", "No se recibe posición inicial válida del ventilador.", "Motor|Sensor Hall|Conector|Placa", "Revisar giro/conector/señales|Descartar motor o placa", "El bastidor queda protegido.", "791/792/793.", "132"),
    ("86", "EEPROM de placa principal", "La EEPROM de la main PCB no se lee correctamente.", "EEPROM|Orientación|Pines|Placa", "Cortar alimentación|Revisar chip y datos|Confirmar repuesto", "El bastidor no inicia correctamente.", "861/862/863.", "132"),
    ("87", "EEPROM de placa de ventilador", "La placa de ventilador no comunica con su EEPROM.", "EEPROM|Placa fan|Conector", "Revisar inserción/orientación|Confirmar placa", "El ventilador/bastidor queda protegido.", "871/872/873.", "132"),
    ("104", "Comunicación entre exteriores master/slave", "Los bastidores exteriores no se reciben entre sí.", "Bus A/B|DIP master/slave|Alimentación|Tierra", "Revisar A/B, blindaje y tierra|Comprobar DIP y alimentación|Resetear", "El conjunto no puede operar como sistema combinado.", "1041 master; 1042 slave 1; 1043 slave 2.", "132"),
    ("105", "Comunicación placa fan-inverter", "La placa de ventilador no recibe señal de la placa inverter.", "Conector|Fuente|PCB fan/inverter", "Revisar conexiones y alimentaciones", "El bastidor afectado se detiene.", "1051/1052/1053.", "132"),
    ("106", "IPM del ventilador", "El IPM del ventilador detecta pico de sobrecorriente.", "Motor|IPM fan|Cableado|Tensión", "Comprobar motor y placa fan|Medir alimentación", "El ventilador y el bastidor se protegen.", "1061/1062/1063.", "132"),
    ("107", "DC link bajo de ventilador", "El enlace DC del ventilador cae por debajo del límite.", "Condensador|Bus|Filtro de ruido|Placa", "Empezar en el socket inverter del filtro|Medir bus con seguridad", "El ventilador/bastidor queda OFF.", "1071/1072/1073; <50 V durante 250 µs.", "132"),
    ("113", "Sonda de tubería líquida exterior", "La sonda líquida está abierta o en corto.", "NTC|Conector|12/5 V|PCB", "Medir sonda y señal|Revisar referencia", "El bastidor se protege.", "1131/1132/1133.", "133"),
    ("114", "Sonda de entrada de subenfriamiento", "La sonda de entrada del subcooler está fuera de rango.", "NTC|Conector|PCB", "Medir y contrastar con temperatura real", "El control de subenfriamiento se limita.", "1141/1142/1143.", "133"),
    ("115", "Sonda de salida de subenfriamiento", "La sonda de salida del subcooler está fuera de rango.", "NTC|Conector|PCB", "Medir y comparar entrada/salida", "El control de subenfriamiento se limita.", "1151/1152/1153.", "133"),
    ("116", "Nivel o sensor de aceite", "El bastidor detecta nivel bajo o señal de sensor anormal.", "Aceite insuficiente|Sensor|Cable|Retorno de aceite", "Revisar sensor y cable|Analizar retorno de aceite con LGMV", "El bastidor protege el compresor.", "1161/1162/1163.", "133"),
    ("145", "Comunicación main-external board", "La placa principal no comunica con la placa externa.", "Conector|Fuente|PCB", "Revisar conexiones y alimentaciones|Resetear", "El bastidor afectado queda fuera de servicio.", "1451/1452/1453.", "133"),
    ("150", "Sobrecalentamiento de descarga insuficiente", "Existe riesgo de retorno de líquido al compresor.", "Sobrecarga|EEV abierta|Sonda|Carga desequilibrada", "Comparar presiones/temperaturas|Revisar EEV y carga", "Tras tres repeticiones en una hora el sistema queda parado y exige reinicio manual.", "1501/1502/1503; <3 °C durante al menos 5 min en las condiciones descritas.", "133"),
    ("151", "Diferencia alta-baja insuficiente", "No se crea la diferencia de presión esperada.", "Válvula de cuatro vías|Compresor|Carga", "Medir alta/baja|Comprobar bobina/resistencia y válvula", "El sistema protege los compresores.", "1511/1512/1513; el manual cita bobina de cuatro vías 2.085 Ω ±10 %.", "133"),
    ("153", "Sonda superior de intercambiador", "La sonda superior de la batería exterior está fuera de rango.", "NTC|Conector|PCB", "Medir NTC/señal|Revisar fijación", "El bastidor se protege.", "1531/1532/1533.", "134"),
    ("154", "Sonda inferior de intercambiador", "La sonda inferior de la batería exterior está fuera de rango.", "NTC|Conector|PCB", "Medir NTC/señal|Revisar fijación", "El bastidor se protege.", "1541/1542/1543.", "134"),
    ("182", "Comunicación entre MICOM de placa externa", "Los MICOM principal y secundario de la placa externa no comunican.", "Placa externa|Fuente|Conexión interna", "Observar LED amarillo|Pulsar reset tras comprobar|Sustituir placa si persiste", "El bastidor afectado queda fuera de servicio.", "1821/1822/1823.", "134"),
    ("193", "Disipador de ventilador demasiado caliente", "La temperatura del disipador fan supera el límite.", "Ventilación|Suciedad|Sensor|Placa", "Revisar ventilador/disipador|Medir sensor y señal", "El bastidor se detiene.", "1931/1932/1933; >203 °F en la familia documentada.", "134"),
    ("194", "Sonda de disipador del ventilador", "La sonda térmica de la placa fan está fuera de rango.", "Sonda|12/5 V|Conector|Placa", "Medir referencia y señal|Contrastar temperatura", "El bastidor se protege.", "1941/1942/1943.", "134"),
    ("200", "Auto pipe search de Heat Recovery fallido", "La búsqueda automática de tuberías no finaliza correctamente.", "Válvulas/puertos HR|Direcciones|Cableado|Capacidad", "Revisar topología y direcciones|Corregir y repetir auto pipe search", "La puesta en marcha de Heat Recovery queda bloqueada.", "2001 identifica el fallo de auto pipe search.", "135"),
    ("201", "Sonda de líquido de unidad HR", "La sonda líquida del puerto HR está abierta o en corto.", "Sonda|Cable|PCB HR", "Medir NTC|Revisar conector y dirección HR", "El puerto/unidad HR afectado se protege.", "Código acompañado por número de HR.", "135"),
    ("202", "Sonda de entrada de subenfriamiento HR", "La sonda de entrada del subcooler HR está fuera de rango.", "Sonda|Cable|PCB HR", "Medir NTC y revisar conector", "El puerto HR afectado se protege.", "Código acompañado por número de HR.", "135"),
    ("203", "Sonda de salida de subenfriamiento HR", "La sonda de salida del subcooler HR está fuera de rango.", "Sonda|Cable|PCB HR", "Medir NTC y comparar entrada/salida", "El puerto HR afectado se protege.", "Código acompañado por número de HR.", "135"),
    ("204", "Comunicación exterior-unidad HR", "La exterior no recibe señal de la unidad Heat Recovery.", "Bus|Alimentación HR|Dirección|PCB", "Comprobar bus, alimentación y dirección|Aislar nodo", "La unidad/puerto HR afectado queda fuera de control.", "Código acompañado por número de HR.", "135"),
    ("205", "Comunicación HR-módem RS-485", "La unidad HR 2A no comunica con el módem 485.", "Módem|Bus|Conector|PCB HR", "Revisar módem y bus|Esperar recuperación de señal", "Se borra cuando vuelve la señal; aparece tras el tiempo documentado.", "Aplica a HR 2A a 9.600 bps; tres minutos sin señal.", "135"),
    ("206", "Dirección HR duplicada", "Dos unidades/puertos Heat Recovery comparten dirección.", "Dial HEX repetido|Configuración de puertos", "Comparar diales HEX|Asignar direcciones únicas|Repetir detección", "La configuración HR no se valida.", "Aplica a HR 2A con comunicación 485.", "135"),
    ("230", "Sensor de fuga de refrigerante", "El sensor detecta fuga o está mal configurado/defectuoso.", "Fuga real|Sensor defectuoso|Función activada sin sensor|Cable", "Ventilar y aplicar protocolo de seguridad|Comprobar sensor y configuración|No rearmar sin descartar fuga", "Se detiene la unidad, cierra la electroválvula interior y suena el zumbador; requiere reset de alimentación.", "Detección >6.000 ppm; normal por debajo del umbral de señal indicado por el manual.", "127"),
    ("237", "Comunicación interior-exterior - visualización local", "La interior no recibe a la exterior durante más de tres minutos.", "RS-485|Unidad exterior|Cable|PCB", "Comprobar bus y alimentación|Identificar nodo con LGMV", "Se muestra en interior y su mando; la unidad afectada queda parada.", "CH237; solo se muestra en la interior y mando indicados.", "127"),
    ("238", "Comunicación interior-exterior - placa exterior", "La interior no recibe datos válidos de la exterior.", "PCB exterior|RS-485|Cable|Alimentación", "Revisar placa exterior, bus y alimentación", "Se muestra en interior y mando; la unidad afectada queda parada.", "CH238.", "127"),
    ("242", "Red del controlador central", "El controlador central no recibe información de la exterior.", "Red central|Gateway|Dirección|Alimentación", "Comprobar topología, direcciones y alimentación|Aislar controlador", "El control central pierde visibilidad; el funcionamiento local depende del sistema.", "Error de red de controlador central.", "135"),
]

for code, title, description, causes, checks, behavior, value, page in MULTIV_ERRORS:
    aliases = [code, f"CH {code}"]
    numeric = int(code)
    if 21 <= numeric <= 194 and numeric not in {200, 201, 202, 203, 204, 205, 206, 230, 237, 238, 242}:
        aliases.extend([f"{code}1", f"{code}2", f"{code}3"])
    if code == "200":
        aliases.append("2001")
    ERROR_SPECS.append(error_spec(
        f"CH{code}", title, "system" if numeric in {51, 53, 104, 200, 204, 205, 206, 230, 237, 238, 242} else "outdoor",
        "MULTIV5", page, description, causes, checks, behavior, value,
        aliases="|".join(aliases),
        source_section="Multi V 5 error code tables",
    ))


def build_interpretation(interpretation_id: int, spec: dict[str, str]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    item_id = interpretation_id * 100

    def add(item_type: str, body: str, title: str | None = None) -> None:
        nonlocal item_id
        item_id += 1
        items.append({
            "id": item_id,
            "item_type": item_type,
            "title": title,
            "body": body,
            "sort_order": len(items) + 1,
            "review_status": "reviewed",
            "origin_ref": SOURCES[spec["ref"]]["document_ref"],
        })

    add("machine_behavior", spec["behavior"])
    add("related_element", spec["title"])
    for cause in split_items(spec["causes"]):
        add("cause", cause)
    for check in split_items(spec["checks"]):
        add("check", check)
    add(
        "observation",
        (
            f"Variante documentada en {SOURCES[spec['ref']]['document_ref']}. "
            "Confirme familia, forma de indicación y, en MULTI V, el sufijo de bastidor antes de intervenir."
        ),
    )

    return {
        "id": interpretation_id,
        "title": spec["title"],
        "description": spec["description"],
        "source_kind": "official",
        "confidence": "high",
        "review_status": "reviewed",
        "info_items": items,
        "operational_impacts": [operational_impact(spec["behavior"])],
        "datasets": [technical_dataset(interpretation_id * 10 + 1, spec)],
        "related_errors": [],
        "sources": [source(spec["ref"], spec["page"], spec["source_section"])],
    }


def code_sort(value: str) -> tuple[int, str]:
    match = re.search(r"(\d+)", value)
    return (int(match.group(1)) if match else 999999, value)


def build_errors() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for spec in ERROR_SPECS:
        grouped[normalize(spec["code"])].append(spec)

    indexes: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    interpretation_id = 0
    for error_id, code_key in enumerate(sorted(grouped, key=code_sort), start=1):
        specs = grouped[code_key]
        code_display = specs[0]["code"]
        interpretations = []
        alias_values = [code_display]
        for spec in specs:
            interpretation_id += 1
            interpretations.append(build_interpretation(interpretation_id, spec))
            alias_values.extend(split_items(spec["aliases"]))
        alias_values = list(dict.fromkeys(value for value in alias_values if value))
        aliases = [
            {"alias_display": value, "alias_normalized": normalize(value)}
            for value in alias_values
        ]
        short_label = (
            specs[0]["title"]
            if len(specs) == 1
            else f"{len(specs)} interpretaciones documentadas"
        )
        search_blob = " ".join(
            [code_display, short_label]
            + alias_values
            + [
                " ".join([
                    spec["title"], spec["description"], spec["causes"],
                    spec["checks"], spec["behavior"], spec["value"],
                ])
                for spec in specs
            ]
        )
        tags = sorted(set(normalize(search_blob).lower().split()))[:80]
        index = {
            "id": error_id,
            "code_display": code_display,
            "code_normalized": normalize(code_display),
            "indication_type": "display_led_controller_or_lgmv",
            "unit_scope": specs[0]["scope"],
            "short_label": short_label,
            "interpretation_count": len(interpretations),
            "search_text": normalize(search_blob),
        }
        detail = {
            **{key: value for key, value in index.items() if key not in {"interpretation_count", "search_text"}},
            "aliases": aliases,
            "tags": tags,
            "interpretations": interpretations,
            "media": [],
        }
        indexes.append(index)
        details.append(detail)
    return indexes, details


def section(section_type: str, title: str, body: str, open_by_default: bool = False) -> dict[str, Any]:
    return {
        "section_type": section_type,
        "title": title,
        "body": body,
        "collapsed_default": 0 if open_by_default else 1,
    }


def step(phase: str, number: int, instruction: str, expected: str | None = None, warning: str = "none") -> dict[str, Any]:
    return {
        "phase": phase,
        "step_no": number,
        "instruction": instruction,
        "expected_result": expected,
        "warning_level": warning,
    }


def controller_profile(
    family: str,
    startup: str,
    notes: str,
    maximum_scope: str = "Una unidad o grupo compatible.",
) -> dict[str, Any]:
    return {
        "interface_type": "mando cableado",
        "controller_family": family,
        "wire_count": "3",
        "polarity": "Sí: rojo 12 V, amarillo señal y negro GND.",
        "nominal_voltage": "12 VDC",
        "terminals": "DC 12 V / Signal / GND o conector CN-REMO según unidad.",
        "cable_colors": "Rojo / amarillo / negro",
        "cable_spec": "AWG 24, 3 conductores o superior; máximo 50 m según manual.",
        "startup_behavior": startup,
        "maximum_scope": maximum_scope,
        "notes": notes,
    }


TOPIC_DEFS = [
    (1, "diagnostic_access", "obtain-error-codes", "Cómo obtener códigos y subcódigos", "LED, display CH, mando, placa exterior y SSD Multi V."),
    (2, "history_reset", "history-and-reset", "Historial, rearme y borrado", "Historial de 20 registros, descarga de placas y niveles Multi V."),
    (3, "controllers_buses", "wired-controllers", "Mandos cableados LG", "PREMTB101, PREMTC00U, colores, tensión y grupos."),
    (4, "controllers_buses", "controller-communication", "Fallo de comunicación del mando", "CH03, cableado, maestro/esclavo y aislamiento."),
    (5, "service_modes", "forced-operation", "Marcha forzada y funcionamiento de respaldo", "Variantes Single Zone, Multi F y Multi V."),
    (6, "commissioning", "test-run", "Test Run y prueba de puesta en marcha", "Pruebas desde pulsador, mando, placa y LGMV."),
    (7, "service_modes", "pump-down", "Pump Down y recogida de refrigerante", "Recogida Single Zone y refrigeración forzada Multi F."),
    (8, "configuration", "installer-settings", "Programación desde mando", "Test, dirección, ESP, sensores, maestro/esclavo y estática."),
    (9, "configuration", "board-dip-settings", "DIP switch y opciones de placa", "Refrigeración forzada, consumo, bajo ruido y bloqueo de modo."),
    (10, "drainage_overflow", "cassette-drainage", "Cassette: bomba, boya y desbordamiento", "Proceso de detección, prueba y CH04."),
    (11, "multisplit", "multif-errors-modes", "Multi F: errores, modos y efecto operativo", "Estado OFF, prioridad de códigos y conflicto CH07."),
    (12, "multisplit", "multif-wiring", "Multi F: alimentación y comunicaciones", "Cuatro conductores, separación, blindaje y unidades BD."),
    (13, "multi_v_network", "multi-v-addressing", "MULTI V: auto addressing", "Requisitos, procedimiento, cantidad detectada y fallo CH200."),
    (14, "multi_v_network", "multi-v-functions", "MULTI V: funciones de servicio y red", "Opciones SW01, FDD, respaldo y Heat Recovery."),
    (15, "multi_v_network", "multi-v-response-levels", "MULTI V: niveles y alcance de paradas", "Niveles 1-4, reintentos, comunicaciones y reinicio."),
    (16, "service_tools_boards", "lgmv-sims-fdd", "LGMV, SIMs y FDD", "Datos en vivo, gráficas, informes y diagnóstico sin portátil."),
    (17, "component_checks", "sensors-pressure-drain", "Sondas, presión, bomba y boya", "NTC, sensores de presión y drenaje."),
    (18, "component_checks", "inverter-fans-compressor", "Inverter, compresor y ventiladores", "Bus DC, IPM, CT, BLDC y comprobaciones seguras."),
    (19, "technical_values", "quick-values", "Tensiones y valores rápidos", "12 V del mando, umbrales Multi F y referencias Multi V."),
    (20, "normal_states", "normal-behaviors", "Estados normales que parecen averías", "Retardos, hot start, desescarche, retorno de aceite y espera."),
    (21, "system_architecture", "family-recognition", "Cómo reconocer la familia técnica", "Single Zone, Multi F, cassette y MULTI V."),
    (22, "errors", "code-interpretation-rules", "Cómo interpretar CH y subcódigos", "No mezclar código base, LED, sufijo de bastidor y origen del display."),
    (23, "service_tools_boards", "after-board-replacement", "Después de sustituir una placa", "EEPROM, capacidad, DIP, direcciones y validación."),
]


def procedure(
    topic_id: int,
    title: str,
    recognition: str,
    system_type: str,
    unit_scope: str,
    purpose: str,
    summary: str,
    technical: str,
    scope_note: str,
    steps_text: list[str],
    ref: str,
    page: str,
    source_section: str,
    *,
    page_end: str | None = None,
    controller: dict[str, Any] | None = None,
) -> dict[str, Any]:
    phases = ["prepare", "procedure", "procedure", "verify", "exit"]
    steps = [
        step(
            phases[min(index, len(phases) - 1)],
            index + 1,
            instruction,
            warning="caution" if "tensión" in instruction.lower() or "presión" in instruction.lower() else "none",
        )
        for index, instruction in enumerate(steps_text)
    ]
    return {
        "id": 0,
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
        "sort_order": 0,
        "visible": 1,
        "sections": [
            section("recognition", "Cómo reconocer esta variante", recognition, True),
            section("technical", "Qué hace la máquina", technical, True),
            section("scope", "Alcance y límites", scope_note),
        ],
        "steps": steps,
        "parameters": [],
        "controller": controller,
        "monitoring_points": [],
        "media": [],
        "sources": [source(ref, page, source_section, page_end)],
    }


def build_topics() -> list[dict[str, Any]]:
    topics: dict[int, dict[str, Any]] = {}
    for topic_id, category_slug, slug, title, summary in TOPIC_DEFS:
        category = CATEGORY_BY_SLUG[category_slug]
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

    procedures: list[dict[str, Any]] = []

    def add(*args: Any, **kwargs: Any) -> None:
        procedures.append(procedure(*args, **kwargs))

    # 1. Obtención de códigos y subcódigos.
    add(1, "Split con dos LED: decenas y unidades", "Receptor interior con LED1 de unidades y LED2 de decenas.", "Single Zone / Multi F", "indoor",
        "Decodificar un código sin display numérico.", "Cada grupo de parpadeos forma las decenas y unidades del código CH.",
        "Ejemplo CH21: LED de decenas 2 veces y LED de unidades 1 vez; los intervalos separan cada repetición.",
        "La posición y el color de los LED varían; confirme el dibujo de la familia antes de contar.",
        ["Detenga la unidad y observe qué LED actúan.", "Cuente por separado decenas y unidades.", "Anote también el orden y la pausa.", "Busque CH más los dos dígitos."],
        "SZ2015", "26", "Indoor unit error display", page_end="30")
    add(1, "Unidad con display numérico: lectura CH directa", "Interior con display de segmentos o panel que muestra CH seguido de dos o tres cifras.", "Single Zone / Multi F", "indoor",
        "Leer el código sin convertir parpadeos.", "El display puede mostrar CH05, CH21 u otro código directo.",
        "Si hay varias averías, la familia muestra primero la de mayor prioridad; anote todos los ciclos.",
        "No sustituya una placa interior por un CH21-73 salvo las excepciones documentadas CH05/CH53.",
        ["Espere un ciclo completo del display.", "Anote CH y todos los dígitos.", "Compruebe si reaparece otro código.", "Consulte todas las interpretaciones."],
        "SZ2015", "25", "Error indicator and number display", page_end="30")
    add(1, "Cassette: LED del receptor y botón Forced Operation", "Receptor de cassette con LED visible y botón de operación forzada.", "Multi F cassette", "indoor",
        "Obtener el código cuando no hay display.", "El mismo código aparece por LED, mando cableado, placa exterior o LGMV.",
        "CH04, CH05 y CH10 dejan la cassette OFF; la indicación normal de filtro no es un error.",
        "Diferencie verde de marcha, amarillo-verde de filtro/programación y naranja de filtro en parada.",
        ["Identifique el LED y el estado previo.", "Cuente parpadeos sin pulsar Forced Operation.", "Anote código y estado de bomba/ventilador.", "Use el mando o LGMV para confirmar."],
        "CASSETTE", "59", "Ceiling cassette LED indications and error codes")
    add(1, "MULTI V: display SSD de placa exterior", "Placa principal exterior con display de siete segmentos.", "MULTI V 5", "outdoor",
        "Separar código y bastidor master/slave.", "El dígito derecho identifica 1=master, 2=slave 1 y 3=slave 2.",
        "211, 212 y 213 son CH21 en bastidores distintos; 1051 es CH105 en master.",
        "Los códigos de HR incorporan además el número de unidad o puerto; anote la cadena completa.",
        ["Espere a que el SSD repita la cadena.", "Anote todos los dígitos sin quitar el sufijo.", "Identifique master/slave por el último dígito.", "Busque el código completo y el CH base."],
        "MULTIV5", "126", "Error code display and nomenclature")
    add(1, "LGMV: código, unidad y evolución en tiempo real", "Sistema con conector de servicio y software/app LGMV.", "Multi F / MULTI V", "system",
        "Leer error y comprobar qué unidad lo genera.", "LGMV presenta códigos, sensores, velocidades y estados simultáneamente.",
        "La lectura es diagnóstica; no sustituye medir tensión, presión o continuidad cuando el manual lo pide.",
        "Guarde el registro antes de resetear para conservar el contexto de la avería.",
        ["Conecte el interfaz compatible con el equipo parado o según manual.", "Seleccione el sistema detectado.", "Anote código, unidad y hora.", "Guarde datos antes de reiniciar."],
        "MULTIF", "94", "LGMV diagnostic software", page_end="95")

    # 2. Historial y rearme.
    add(2, "PREMTB101: historial de hasta 20 errores", "Mando Standard III con menú, flechas y tecla OK.", "Single/Multi/MULTI V compatible", "controller",
        "Consultar memoria antes de borrar o cortar tensión.", "Service setting > Error history ordena hasta veinte eventos por fecha.",
        "El historial pertenece a la interior conectada y su alcance depende del grupo.",
        "No confunda historial con alarma activa; fotografíe la lista antes de cualquier reset.",
        ["Abra Menu y seleccione Settings.", "Entre en Service setting.", "Seleccione Error history.", "Anote los eventos por fecha."],
        "PREMTB101", "134", "Service setting - Error history",
        controller=controller_profile("PREMTB101 / Standard III", "Muestra la interfaz tras la inicialización de la interior.", "Historial de hasta 20 eventos."))
    add(2, "Rearme de Single Zone: descarga mínima de tres minutos", "Equipo split o Multi F con código CH en LED/display.", "Single Zone / Multi F", "system",
        "Rearmar después de corregir la causa.", "LG indica cortar alimentación y esperar la descarga completa de la placa.",
        "La desaparición del LED no demuestra que la causa esté resuelta; confirme arranque y medidas.",
        "No haga ciclos rápidos de alimentación: el manual indica tres minutos para descargar la PCB exterior.",
        ["Anote código y condiciones.", "Corrija la causa.", "Corte alimentación.", "Espere al menos tres minutos.", "Restablezca y verifique."],
        "SZ2015", "25", "Reset after CH error")
    add(2, "MULTI V: error activo, recuperación y reset", "Sistema VRF con SSD, mandos o LGMV.", "MULTI V 5", "system",
        "Decidir si esperar recuperación, corregir comunicación o reiniciar manualmente.", "Los niveles 1-4 no se borran de la misma forma.",
        "Nivel 2 desaparece al volver la comunicación; nivel 3 reintenta; nivel 1 exige corrección y reinicio manual.",
        "Conserve el registro LGMV y el sufijo de bastidor antes de pulsar reset.",
        ["Clasifique el código por tipo y nivel.", "Corrija comunicación o causa física.", "Observe si el nivel permite recuperación automática.", "Solo resetee cuando el manual lo requiera."],
        "MULTIV5", "125", "Error code general information")

    # 3. Mandos cableados.
    add(3, "PREMTB101: rojo, amarillo y negro", "Mando rectangular Standard III con menú gráfico.", "LG indoor units compatible", "controller",
        "Identificar alimentación, señal y masa.", "Rojo=12 VDC, amarillo=señal y negro=GND; extensión AWG24, tres conductores.",
        "Máximo 50 m según manual; un tendido incorrecto puede provocar CH03.",
        "No entierre el mando ni sitúe su sensor donde reciba sol o impulsión directa.",
        ["Corte alimentación.", "Compare colores en mando e interior.", "Compruebe continuidad y ausencia de cruces.", "Alimente y mida 12 VDC rojo-negro."],
        "PREMTB101", "69", "Installation of remote controller",
        controller=controller_profile("PREMTB101 / Standard III", "Arranca cuando la interior aporta 12 VDC y comunicación válida.", "El sensor interno puede participar en el control."))
    add(3, "PREMTC00U: mando simple de tres hilos", "Mando sencillo con botones físicos, sin menú gráfico Standard III.", "LG indoor units compatible", "controller",
        "Cablear y reconocer el mando antiguo/sencillo.", "Mantiene la misma asignación amarillo señal, rojo 12 V y negro GND.",
        "Para cambios de instalador se usan combinaciones de botones y códigos numéricos.",
        "No exceda 164 ft/50 m; después de maestro/esclavo mantenga la alimentación OFF un minuto.",
        ["Corte alimentación.", "Conecte amarillo-rojo-negro en el mismo orden.", "Compruebe continuidad.", "Restablezca y espere inicialización."],
        "PREMTC00U", "10", "Remote controller installation",
        controller=controller_profile("PREMTC00U Simple Wired Remote", "Enciende al recibir 12 VDC y señal de la interior.", "Código de instalador mediante botones físicos."))
    add(3, "Control de grupo: una interior master y hasta 16 unidades", "Varias interiores enlazadas a un mando mediante PZCWRCG3/PZCWRC1.", "Group control", "controller",
        "Evitar pérdidas de comunicación y alimentación duplicada.", "Solo la interior master entrega 12 V; las esclavas reciben señal y GND.",
        "Conectar 12 V a las esclavas puede causar pérdida de comunicación.",
        "DIP 3 OFF=master y ON=slave en cassette/conductos; cortar y reponer tras un minuto.",
        ["Identifique una sola master.", "Conecte rojo/amarillo/negro a master.", "A esclavas lleve solo amarillo y negro.", "Configure DIP 3 y reinicie tras un minuto."],
        "PREMTB101", "70", "Group control",
        controller=controller_profile("LG group control", "El grupo se reconoce tras reponer alimentación.", "Hasta 16 interiores; solo una master.", "Hasta 16 interiores."))

    # 4. Comunicación del mando.
    add(4, "CH03: la interior no recibe al mando", "Código CH03 en LED, display o LGMV.", "LG indoor unit", "controller",
        "Separar cable, mando, configuración y placa interior.", "La placa interior no recibe telegramas del mando cableado.",
        "Las causas más frecuentes son 12 V ausente, señal abierta, dos master o cable >50 m.",
        "No sustituya la placa sin probar continuidad, alimentación y un mando conocido.",
        ["Mida 12 V rojo-negro.", "Compruebe amarillo y continuidad.", "Revise maestro/esclavo.", "Pruebe cable/mando conocido.", "Solo entonces valore la placa."],
        "MULTIF", "92", "Indoor unit error CH03")
    add(4, "Grupo con fallo: aislar interior por interior", "Varias interiores bajo un solo PREMTB101 o PREMTC00U.", "LG group control", "controller",
        "Encontrar el nodo que tumba el mando.", "Una esclava con alimentación roja conectada o un corto de señal puede afectar al grupo.",
        "Aísle ramales con tensión cortada y mantenga siempre una única master.",
        "Después de cada cambio, espere el minuto de reinicio indicado.",
        ["Anote configuración actual.", "Corte alimentación.", "Desconecte esclavas por ramales.", "Compruebe señal/GND sin el rojo.", "Reconecte una a una."],
        "PREMTB101", "70", "Group control communication precautions")

    # 5. Marcha forzada y respaldo.
    add(5, "Single Zone: botón Forced Operation", "Pulsador manual en la unidad interior para usarla sin mando.", "Single Zone", "indoor",
        "Hacer funcionar el equipo cuando se pierde el mando.", "La placa aplica el modo y consignas de la lógica de operación forzada de esa familia.",
        "No asumir que anula protecciones; los códigos CH y retardos continúan activos.",
        "El mismo pulsador puede tener funciones distintas según tiempo de pulsación.",
        ["Identifique el pulsador exacto.", "Compruebe que no hay código activo.", "Pulse según el manual de la familia.", "Observe modo, ventilador y exterior.", "Detenga con el mismo control."],
        "SZ2015", "13", "Forced operation")
    add(5, "Multi F: refrigeración forzada mediante DIP 2", "Placa exterior con banco DIP-SW y TACT-SW1.", "Multi F / Multi F MAX", "outdoor",
        "Forzar frío para comprobación o servicio.", "DIP 2 ON inicia la secuencia documentada; debe volver a OFF al terminar.",
        "El sistema sigue vigilando errores y protecciones; no es una anulación de seguridad.",
        "Corte alimentación antes de mover DIP cuando el manual lo indique.",
        ["Compruebe válvulas, cableado y unidades.", "Coloque DIP 2 según la variante.", "Inicie y monitorice presiones/temperaturas.", "Detenga si aparece error.", "Devuelva DIP 2 a OFF."],
        "MULTIF", "88", "Forced cooling DIP switch", page_end="89")
    add(5, "MULTI V: respaldo automático o manual de compresor", "Exterior MULTI V 5 con uno de sus compresores inverter averiado.", "MULTI V 5", "outdoor",
        "Mantener servicio degradado de forma temporal.", "El sistema puede excluir el compresor defectuoso y trabajar con capacidad reducida.",
        "LG limita la operación manual de emergencia con compresor averiado a 48 horas.",
        "No usar como reparación permanente; confirme qué compresor está fallando.",
        ["Identifique bastidor y compresor por código/LGMV.", "Aplique respaldo solo según SW01 y menú documentados.", "Verifique presión, corriente y temperatura.", "Planifique reparación antes de 48 horas."],
        "MULTIV5", "56", "Automatic and manual emergency operation", page_end="57")

    # 6. Test Run.
    add(6, "Single Zone: Test Run previo y secuencia", "Split con unidad interior/exterior convencional.", "Single Zone", "system",
        "Verificar instalación antes de entregar.", "El flujo incluye cableado, válvulas, fuga, drenaje y operación.",
        "No iniciar con válvulas cerradas ni cableado dudoso.",
        "Pump Down es un procedimiento aparte y no sustituye la puesta en marcha.",
        ["Compruebe tubería, vacío y válvulas.", "Revise alimentación/tierra/comunicación.", "Ejecute Test Run.", "Observe temperaturas, ventiladores y códigos.", "Detenga y documente."],
        "SZ2015", "17", "Test run flow and details", page_end="19")
    add(6, "PREMTC00U: código de instalador 1", "Mando simple con acceso a códigos de instalador.", "LG indoor unit", "controller",
        "Iniciar prueba en frío o calor desde el mando.", "Código 1: 00 normal, 01 prueba de frío y 02 prueba de calor.",
        "Tocar ON/OFF, temperatura, ventilador o modo cancela el Test Run.",
        "La disponibilidad depende de la interior; confirme el manual de producto.",
        ["Entre en Installer setting.", "Seleccione código 1.", "Elija 01 frío o 02 calor.", "Observe la respuesta y códigos.", "Vuelva a 00 al terminar."],
        "PREMTC00U", "14", "Test run mode code 1",
        controller=controller_profile("PREMTC00U", "Muestra código y valor al entrar en instalador.", "El Test Run se cancela al cambiar controles básicos."))
    add(6, "MULTI V: Integrated Test Run con LGMV", "MULTI V 5 con LGMV conectado al master.", "MULTI V 5", "system",
        "Ejecutar una comprobación integral y guardar informe.", "ITR selecciona automáticamente frío o calor según ambiente y prueba componentes/funciones.",
        "Auto addressing debe estar correcto y todas las unidades deben estar preparadas.",
        "El informe HTML se guarda desde Diagnostics tras una prueba correcta.",
        ["Conecte LGMV al master.", "Compruebe auto address y ausencia de alarmas.", "Seleccione Fd7/Integrated Test Run.", "Siga resultados sin desconectar nodos.", "Guarde el informe."],
        "MULTIV5", "61", "Integrated Test Run", page_end="62")

    # 7. Pump down.
    add(7, "Single Zone: Pump Down desde el modo frío", "Split con válvulas de servicio en exterior.", "Single Zone", "outdoor",
        "Recoger refrigerante en la exterior sin liberarlo.", "Se hace funcionar en refrigeración, se cierra líquido y después gas en el momento indicado.",
        "El manual advierte no continuar fuera de presión segura ni operar con válvulas incorrectas.",
        "Debe realizarlo personal cualificado con manómetro y control del tiempo.",
        ["Conecte manómetro y confirme modo frío.", "Inicie refrigeración estable.", "Cierre la válvula de líquido.", "Vigile presión y cierre gas en el punto indicado.", "Detenga inmediatamente."],
        "SZ2015", "19", "Pump Down procedure")
    add(7, "Multi F: recogida apoyada en refrigeración forzada", "Exterior Multi F con DIP de servicio.", "Multi F / Multi F MAX", "outdoor",
        "Mantener demanda de frío durante la recogida.", "El DIP fuerza frío, pero las protecciones y códigos siguen activos.",
        "Las ramificaciones y unidades BD exigen confirmar qué circuito está siendo recogido.",
        "No cerrar válvulas ni puertos sin identificar la arquitectura.",
        ["Identifique exterior, ramales y BD.", "Active refrigeración forzada según DIP.", "Monitorice presión y temperatura.", "Realice la recogida según circuito.", "Restaure DIP y válvulas."],
        "MULTIF", "88", "Forced cooling for service", page_end="89")

    # 8. Programación desde mando.
    add(8, "PREMTC00U: mapa de códigos de instalador", "Mando simple con pantalla de código/valor.", "Single Zone / Multi F indoor", "controller",
        "Configurar funciones sin confundir código y valor.", "Incluye Test Run, dirección, ESP, sensor, altura, presión estática y maestro/esclavo.",
        "Un valor incorrecto puede provocar mal funcionamiento; anote el valor de fábrica antes de cambiar.",
        "Algunas funciones no existen en todas las interiores.",
        ["Entre con la combinación de instalador.", "Anote código y valor actual.", "Cambie una sola función.", "Guarde y salga.", "Reinicie si el manual lo exige."],
        "PREMTC00U", "11", "Installer setting code table", page_end="16",
        controller=controller_profile("PREMTC00U", "Muestra Function code y Value.", "Solo instalador cualificado."))
    add(8, "ESP y presión estática de conductos", "Interior de conductos con PREMTC00U/PREMTB101.", "Ducted indoor unit", "controller",
        "Adaptar el caudal a la red de conductos.", "El código 3 asigna ESP por velocidad; código 6/32 selecciona presión o escalón según producto.",
        "No copie valores entre modelos; use la tabla de la interior.",
        "Una presión incorrecta puede causar ruido, poco caudal, hielo o desbordamiento.",
        ["Mida o estime la presión externa.", "Consulte tabla específica de la interior.", "Ajuste velocidad/ESP.", "Verifique caudal en todas las bocas.", "Guarde valores."],
        "PREMTC00U", "14", "ESP and static pressure settings", page_end="16")
    add(8, "Selección del sensor de ambiente", "Mando con código 4 o menú de sensor.", "LG indoor unit", "controller",
        "Elegir sensor del mando, retorno interior o lógica 2TH.", "En 2TH la selección puede usar la temperatura más alta en frío y más baja en calor.",
        "Evite usar el sensor del mando si recibe sol, impulsión o está en pared exterior.",
        "La disponibilidad y criterio 2TH cambian por producto.",
        ["Compare ubicación de ambos sensores.", "Anote valor de fábrica.", "Seleccione mando/interior/2TH.", "Pruebe frío y calor.", "Compruebe estabilidad."],
        "PREMTC00U", "14", "Temperature sensor setting")

    # 9. DIP y placa.
    add(9, "Multi F: reducción de consumo", "Banco DIP de exterior con secuencia en dos pasos.", "Multi F / Multi F MAX", "outdoor",
        "Limitar potencia/corriente de la exterior.", "La combinación DIP selecciona el modo de ahorro documentado.",
        "Reduce capacidad disponible; no usar para ocultar una alimentación insuficiente.",
        "Cambie DIP solo siguiendo la secuencia y estado de alimentación del manual.",
        ["Anote posición original.", "Seleccione el nivel documentado.", "Aplique la secuencia DIP.", "Verifique corriente y capacidad.", "Restaure si no procede."],
        "MULTIF", "89", "Saving power consumption DIP settings", page_end="90")
    add(9, "Multi F: Night Quiet Mode", "Exterior Multi F con banco DIP 1-4.", "Multi F / Multi F MAX", "outdoor",
        "Reducir ruido nocturno.", "La opción limita ventilador/compresor y puede combinarse con bloqueo de modo.",
        "La capacidad puede disminuir; documente el horario y la necesidad real.",
        "No deje posiciones de servicio activas por error.",
        ["Anote DIP originales.", "Seleccione Night Quiet según tabla.", "Confirme la secuencia.", "Mida ruido/capacidad.", "Registre el ajuste."],
        "MULTIF", "90", "Night Quiet Mode DIP settings")
    add(9, "Multi F: bloqueo solo frío o solo calor", "Placa exterior con DIP de Mode Lock.", "Multi F / Multi F MAX", "outdoor",
        "Impedir demandas del modo contrario.", "Las combinaciones DIP bloquean frío o calor para todo el sistema.",
        "Una interior que pida el modo bloqueado puede parecer averiada o mostrar conflicto.",
        "Revise este ajuste antes de diagnosticar CH07.",
        ["Compruebe si existe CH07.", "Anote DIP.", "Verifique modo bloqueado.", "Corrija solo si la instalación lo requiere.", "Pruebe todas las interiores."],
        "MULTIF", "91", "Cooling/heating mode lock DIP settings")

    # 10. Drenaje.
    add(10, "Cassette: CH04 y estado OFF", "Cassette con bomba y boya integradas.", "Multi F cassette", "indoor",
        "Distinguir bomba, boya, tubo y nivelación.", "El código 4 deja la interior OFF; el LED normal de filtro no equivale a desbordamiento.",
        "La obstrucción puede hacer que una boya quede levantada incluso después de parar.",
        "Compruebe el comportamiento tanto en frío como con el equipo parado.",
        ["Observe agua en bandeja.", "Compruebe tubo y pendiente.", "Accione bomba.", "Verifique cambio de la boya.", "Rearme y pruebe."],
        "CASSETTE", "59", "Drain pump error CH04")
    add(10, "Prueba de bomba después de instalar", "Cassette recién instalada, antes de cerrar techo.", "Multi F cassette", "indoor",
        "Confirmar que el agua sale y no queda retenida.", "El manual permite operar la bomba para comprobar el drenaje después del cableado.",
        "No alimente componentes fuera del procedimiento ni deje funcionar en seco más de lo indicado.",
        "La unidad debe estar nivelada para que la boya represente el nivel real.",
        ["Nivele la cassette.", "Vierta agua de prueba en la bandeja.", "Active la prueba de bomba.", "Compruebe caudal y fugas.", "Detenga y seque."],
        "CASSETTE", "34", "Drain pump test", page_end="35")
    add(10, "Boya que queda pegada: diagnóstico mecánico", "CH04 intermitente, especialmente tras frío o deshumidificación.", "Cassette / duct with pump", "indoor",
        "Detectar un flotador que no baja cuando el agua ya salió.", "La lógica interpreta el contacto de la boya; una boya pegada puede mantener el fallo aunque la bomba funcione.",
        "En calor o ventilación puede no generarse condensado nuevo, pero el contacto anormal sigue siendo relevante.",
        "No puentee permanentemente la boya: se pierde la protección contra desbordamiento.",
        ["Corte alimentación.", "Mueva la boya y compruebe libertad.", "Mida continuidad arriba/abajo.", "Limpie bandeja y soporte.", "Repita prueba con agua."],
        "SZ2015", "50", "CH04 drain pump and float switch troubleshooting")

    # 11. Multi F.
    add(11, "Tabla Multi F: todos los códigos listados dejan la unidad OFF", "Sistema Multi F con tabla de errores interior/exterior.", "Multi F / Multi F MAX", "system",
        "Interpretar el efecto sin asumir parada total.", "La tabla marca OFF para la interior afectada y para la exterior cuando la protección es exterior.",
        "Un CH07 puede parar solo la interior incompatible; una protección exterior para el circuito común.",
        "Si hay varios códigos, se muestra primero el de mayor prioridad.",
        ["Anote código y origen del display.", "Determine si es interior o exterior.", "Consulte estado OFF y unidad afectada.", "Revise otras interiores antes de concluir parada total."],
        "MULTIF", "92", "Indoor and outdoor error code tables", page_end="93")
    add(11, "CH07: demanda de modo diferente", "Varias interiores de bomba de calor piden frío y calor a la vez.", "Multi F", "system",
        "Evitar diagnosticar una avería eléctrica inexistente.", "La interior cuya demanda no coincide con el modo dominante queda OFF.",
        "Las otras interiores compatibles pueden seguir funcionando.",
        "Compruebe también el bloqueo de modo por DIP y override maestro/esclavo.",
        ["Observe qué unidades funcionan.", "Anote el modo de cada mando.", "Revise DIP/override.", "Unifique el modo.", "Compruebe que CH07 desaparece."],
        "MULTIF", "92", "Different mode operation CH07")

    # 12. Cableado Multi F.
    add(12, "Multi F: alimentación y comunicación hasta 130 ft", "Exterior e interiores unidos por cable de cuatro conductores.", "Multi F", "system",
        "Verificar el cableado combinado sin confundir potencia y señal.", "Hasta 130 ft el manual admite el conjunto documentado; por encima separa potencia y comunicación/GND.",
        "La polaridad de comunicación debe mantenerse y el blindaje se conecta solo donde indica el manual.",
        "Nunca aplique tensión de línea al terminal de comunicación.",
        ["Corte alimentación.", "Compare cada borne extremo a extremo.", "Mida longitud y sección.", "Revise blindaje/tierra.", "Alimente y observe CH05/53."],
        "MULTIF", "66", "Power and communication wiring", page_end="72")
    add(12, "Multi F MAX: unidades de distribución BD", "Exterior de mayor capacidad con una o más branch distribution units.", "Multi F MAX", "system",
        "Seguir el flujo de potencia/comunicación a través de la BD.", "La BD añade conexiones, direcciones y posibles puntos de pérdida de comunicación.",
        "Una avería de BD puede afectar a las interiores de su ramal, no necesariamente a todas.",
        "Mantenga separación de potencia, señal y tierra según distancia.",
        ["Identifique exterior, BD y ramales.", "Compruebe alimentación de cada BD.", "Verifique entradas/salidas de comunicación.", "Aísle el ramal que no responde.", "Confirme con LGMV."],
        "MULTIF", "64", "BD unit power and communication", page_end="72")

    # 13. Auto addressing.
    add(13, "MULTI V: auto addressing desde SW01C", "Master exterior con display SSD y pulsador rojo SW01C.", "MULTI V 5", "system",
        "Asignar direcciones automáticamente a interiores.", "Mantener SW01C unos cinco segundos hasta 88; al final aparece durante unos 30 s el número detectado.",
        "Todas las interiores deben tener placa alimentada y mandos en OFF.",
        "Si se cambia una PCB interior, hay que repetir el auto addressing.",
        ["Alimente todas las interiores y deje mandos OFF.", "Verifique DIP master/slave.", "Mantenga SW01C hasta ver 88.", "Espere 3-7 minutos.", "Compare el número detectado con el instalado."],
        "MULTIV5", "51", "Indoor unit auto addressing")
    add(13, "Auto addressing fallido: 88 no desaparece o cuenta incorrecta", "SSD mantiene 88 más de siete minutos o muestra menos interiores.", "MULTI V 5", "system",
        "Localizar una pérdida de alimentación o comunicación.", "La rutina falla cuando no puede reconocer toda la red.",
        "No acepte una cuenta inferior: después aparecerán unidades ausentes y errores de comunicación.",
        "Corrija cableado/alimentación y repita desde el paso indicado.",
        ["Compare número instalado/detectado.", "Compruebe alimentación de cada interior.", "Revise bus y polaridad.", "Repare el nodo ausente.", "Repita auto address."],
        "MULTIV5", "53", "Troubleshooting failed auto addressing")

    # 14. Funciones MULTI V.
    add(14, "Acceso a funciones opcionales con SW01 nº 5", "Master exterior con DIP-SW01 y botones de selección.", "MULTI V 5", "outdoor",
        "Entrar en el menú de servicio sin alterar otras funciones.", "SW01 número 5 ON habilita selección; algunas opciones quedan en EEPROM y otras se pierden al cortar tensión.",
        "Todas las interiores deben estar OFF para guardar correctamente.",
        "Fotografíe DIP y display antes de cambiar una opción.",
        ["Apague todas las interiores.", "Anote DIP y opciones actuales.", "Ponga SW01 nº5 ON.", "Seleccione y confirme una función.", "Devuelva el sistema al estado normal."],
        "MULTIV5", "54", "Setting optional modes", page_end="55")
    add(14, "FDD Fd8/Fd9: todas las unidades a plena carga", "MULTI V 5 con menú FDD en placa.", "MULTI V 5", "system",
        "Forzar todo el sistema en frío o calor para commissioning.", "Fd8 fuerza todas las interiores en frío y Fd9 en calor; ignora ambiente y consigna.",
        "Las protecciones siguen activas y la prueba afecta a todo el sistema.",
        "Use para medir capacidad/estabilidad, no como modo normal.",
        ["Compruebe que todas las unidades están preparadas.", "Seleccione Fd8 o Fd9.", "Observe presiones, temperaturas y EEV.", "Detenga ante alarma.", "Devuelva SW01 a normal."],
        "MULTIV5", "63", "FDD all indoor cooling/heating modes")
    add(14, "Heat Recovery: auto pipe search y direcciones", "MULTI V Heat Recovery con unidades HR y puertos.", "MULTI V 5 HR", "system",
        "Relacionar interiores con puertos y validar la topología.", "CH200 indica que la búsqueda de tuberías no terminó; CH206 indica dirección HR duplicada.",
        "Una dirección o capacidad incorrecta puede bloquear solo un puerto, una HR o la puesta en marcha completa.",
        "Registre número de HR, puerto y dirección HEX.",
        ["Inventaríe HR y puertos.", "Compruebe diales/direcciones.", "Ejecute auto pipe search.", "Anote código completo con número HR.", "Corrija y repita."],
        "MULTIV5", "135", "Heat Recovery error codes")

    # 15. Niveles.
    add(15, "Nivel 4: avisa y continúa", "Código Multi V clasificado como respuesta Level 4.", "MULTI V 5", "system",
        "Distinguir una notificación de una parada.", "El sistema continúa indefinidamente y conserva el código hasta reset y 130 min sin repetición.",
        "Continuar no significa ignorar la causa; registre tendencia y repare.",
        "Confirme que el código concreto pertenece a este nivel.",
        ["Anote código y bastidor.", "Compruebe que el sistema sigue operando.", "Guarde datos LGMV.", "Corrija la causa.", "Verifique 130 min sin recurrencia."],
        "MULTIV5", "125", "Level 4 responses")
    add(15, "Nivel 3: nueve reintentos y parada al décimo", "Código Multi V no comunicacional con recuperación automática inicial.", "MULTI V 5", "system",
        "Comprender por qué la máquina arranca y vuelve a parar.", "Se detiene tres minutos y reinicia; a la décima repetición en una hora pasa a nivel 1.",
        "El décimo evento exige reinicio manual después de reparar.",
        "No haga resets repetidos que oculten el contador sin diagnosticar.",
        ["Registre horas de cada evento.", "Observe el retardo de tres minutos.", "Mida durante el reintento.", "Corrija antes del décimo.", "Rearme solo tras reparar."],
        "MULTIV5", "125", "Level 3 responses")
    add(15, "Nivel 2: comunicación y recuperación automática", "Código Multi V de pérdida de comunicación.", "MULTI V 5", "system",
        "Evitar un reset innecesario cuando vuelve el bus.", "Tras diez intentos aparece el código y desaparece cuando la comunicación se restablece.",
        "Los tiempos de detección varían: entre placas exterior sin demora, interior-exterior 3 min, HR 10 s, placas externas 10 s.",
        "Si el enlace cae otra vez dentro de un minuto, el código permanece.",
        ["Identifique el tramo de bus.", "Compruebe alimentación y conectores.", "Restablezca comunicación.", "Observe un minuto.", "No resetee si el código se limpia solo."],
        "MULTIV5", "125", "Level 2 communication responses")
    add(15, "Nivel 1: parada y reinicio manual", "Código Multi V que provoca shutdown inmediato o tras escalar desde nivel 3.", "MULTI V 5", "system",
        "Saber cuándo no habrá recuperación automática.", "El sistema queda parado y el código no se borra hasta corregir la causa.",
        "El código aparece en mandos, central, BMS, LGMV y SSD.",
        "No reinicie repetidamente una protección grave.",
        ["Registre todos los displays.", "Localice bastidor/unidad.", "Corrija la causa física.", "Compruebe seguridad.", "Aplique reinicio manual y verifique."],
        "MULTIV5", "125", "Level 1 responses")

    # 16. Herramientas.
    add(16, "LGMV: monitorización y gráficas", "PC o móvil con interfaz LGMV compatible.", "Multi F / MULTI V", "system",
        "Ver valores reales y objetivos durante la avería.", "Muestra frecuencias, ventiladores, sensores, EEV, presiones y códigos según equipo.",
        "Guarde CSV o informe antes de alterar la instalación.",
        "La disponibilidad de variables depende de familia y versión.",
        ["Conecte al puerto de servicio.", "Seleccione unidades.", "Compare actual/objetivo.", "Grafique el periodo del fallo.", "Guarde el archivo."],
        "MULTIF", "94", "LGMV display and graph", page_end="95")
    add(16, "FDD en placa: diagnóstico sin guardar datos", "MULTI V 5 con display SSD y funciones Fd.", "MULTI V 5", "outdoor",
        "Ejecutar algoritmos de diagnóstico sin ordenador.", "FDD aporta resultados de commissioning o avería desde la placa.",
        "Para guardar y analizar tendencias se necesita LGMV u otro registrador.",
        "El resultado FDD orienta; no sustituye comprobaciones físicas.",
        ["Seleccione la función Fd adecuada.", "Espere la secuencia completa.", "Anote todos los resultados.", "Contraste con LGMV o medidas.", "Salga y restaure DIP."],
        "MULTIV5", "63", "Fault Detection and Diagnosis")

    # 17. Sensores, presión y drenaje.
    add(17, "Sondas NTC: abierto, corto y coherencia térmica", "CH01/02/06/41/44/45/46 u otros códigos de sensor.", "Todas las familias LG", "component",
        "Comprobar una sonda sin asumir un valor universal.", "Los manuales distinguen sensor, conector, alimentación de placa y señal.",
        "La curva NTC cambia por función y familia; compare siempre con la tabla específica.",
        "Mida resistencia con la sonda desconectada y temperatura estabilizada.",
        ["Corte alimentación.", "Desconecte la sonda.", "Mida resistencia y temperatura.", "Revise continuidad/conector.", "Compare señal al alimentar si el manual lo permite."],
        "SZ2015", "47", "Sensor error troubleshooting")
    add(17, "Sensores de presión: manómetro frente a LGMV", "CH42/43 o protección de alta/baja.", "Multi F / MULTI V", "outdoor",
        "Distinguir presión real de sensor/entrada defectuosa.", "Se compara presión medida con lectura LGMV y tensión de referencia/señal.",
        "Trabaje con refrigerante y alta presión solo con instrumental y protección adecuados.",
        "No puentee un presostato de seguridad para dejar la máquina funcionando.",
        ["Conecte manómetros adecuados.", "Compare con LGMV.", "Mida referencia/señal según esquema.", "Revisar conector y placa.", "Corrija causa de presión real."],
        "MULTIV5", "128", "Pressure switch and sensor error checks")
    add(17, "Bomba y boya: prueba eléctrica y mecánica", "Cassette/ducto con CH04.", "Cassette / ducted indoor", "component",
        "Separar bomba sin caudal, boya pegada y salida de placa.", "La placa supervisa el nivel; una boya alta mantiene el fallo aunque la bomba suene.",
        "La unidad debe estar nivelada y el desagüe libre.",
        "No anule la boya permanentemente.",
        ["Compruebe nivelación y tubo.", "Verifique movimiento de boya.", "Mida continuidad.", "Active bomba según prueba.", "Valore salida de placa si no hay tensión."],
        "SZ2015", "50", "Drain pump and float switch troubleshooting")

    # 18. Inverter y ventiladores.
    add(18, "Compresor e IPM: CH21/26/29", "Exterior inverter con códigos de pico, posición o sobrecorriente.", "Single Zone / Multi F / MULTI V", "outdoor",
        "Evitar sustituir placa antes de comprobar compresor y circuito.", "La causa puede ser eléctrica, mecánica o frigorífica.",
        "Espere la descarga completa y confirme ausencia de tensión antes de medir bobinados/aislamiento.",
        "No meguee a través de la placa inverter conectada.",
        ["Corte y verifique descarga.", "Desconecte U/V/W.", "Mida bobinados y aislamiento.", "Compruebe presiones/igualación.", "Valore IPM y placa."],
        "SZ2015", "47", "CH21/CH26/CH29 inverter troubleshooting", page_end="73")
    add(18, "Ventilador BLDC: CH10/67/77/79", "Motor interior o exterior de continua con conector multipin.", "LG BLDC fan", "component",
        "Separar bloqueo, motor, alimentación, señal y placa.", "La lógica usa posición/velocidad/corriente; una aspa libre no descarta fallo electrónico.",
        "Hay tensiones peligrosas en motores exteriores e interiores de alta tensión.",
        "Compruebe giro con tensión cortada y mida solo con puntos/orden del manual.",
        ["Corte alimentación.", "Compruebe giro y obstrucciones.", "Revise conector.", "Mida alimentaciones/señal con seguridad.", "Compare motor conocido antes de placa."],
        "MULTIV5", "132", "Fan motor error codes")

    # 19. Valores rápidos.
    add(19, "Mando cableado: 12 VDC y colores", "PREMTB101/PREMTC00U de tres hilos.", "LG wired controller", "controller",
        "Comprobar rápidamente alimentación y orden de hilos.", "Rojo=12 VDC, amarillo=Signal y negro=GND.",
        "Máximo 50 m, AWG24/3 conductores o superior.",
        "Conecte solo señal y GND a esclavas en control de grupo.",
        ["Mida rojo-negro.", "Compruebe amarillo sin cortocircuito.", "Verifique orden en ambos extremos.", "Revise longitud/sección."],
        "PREMTB101", "69", "Remote controller cable values",
        controller=controller_profile("PREMTB101 / PREMTC00U", "Alimentación de 12 VDC desde la interior.", "Tres hilos polarizados."))
    add(19, "Multi F: umbrales documentados de bus y capacidad", "Exterior Multi F con CH23/CH51.", "Multi F / Multi F MAX", "outdoor",
        "Usar valores de la familia antes de interpretar el código.", "CH23 documenta bus <140 VDC o >420 VDC; CH51 combinación <50 % o >130 %.",
        "Estos umbrales no se trasladan a otra serie/tensión nominal.",
        "Mida DC link solo con procedimiento de alta tensión.",
        ["Confirme modelo/tensión.", "Mida red.", "Mida bus si procede.", "Calcule relación de capacidades.", "Compare con la tabla."],
        "MULTIF", "93", "Outdoor error thresholds")
    add(19, "MULTI V: sufijos y referencias de bastidor", "SSD con códigos de tres o cuatro cifras.", "MULTI V 5", "outdoor",
        "Interpretar correctamente 211, 1042 o 1503.", "El último dígito indica 1 master, 2 slave 1 y 3 slave 2.",
        "No quite el sufijo antes de localizar físicamente el bastidor.",
        "Los códigos de HR usan además número de unidad/puerto.",
        ["Anote la cadena completa.", "Separe código base y sufijo.", "Localice el bastidor.", "Compruebe sus LED/placas.", "Después consulte el CH base."],
        "MULTIV5", "126", "Error code nomenclature")

    # 20. Estados normales.
    add(20, "Hot Start y desescarche en cassette", "LED verde activo antes de que salga aire caliente.", "Cassette / heat pump", "indoor",
        "Evitar confundir espera de calefacción con avería.", "La cassette usa el mismo color verde para marcha y para hot start/defrost.",
        "El ventilador interior puede permanecer parado o limitado para no impulsar aire frío.",
        "Si aparece CH, deja de ser un estado normal.",
        ["Observe LED y modo.", "Espere la secuencia de hot start.", "Compruebe exterior y temperatura de tubería.", "Busque CH solo si la espera excede lo normal."],
        "CASSETTE", "59", "Normal LED indications")
    add(20, "Retardo de tres minutos", "Compresor no arranca inmediatamente tras parar o rearmar.", "Todas las familias inverter", "system",
        "Reconocer la protección antiarranque inmediato.", "La lógica espera para igualar presiones y proteger compresor/inverter.",
        "No fuerce ciclos repetidos ni corte/reponga antes de terminar la descarga.",
        "Si hay código, diagnostique el código y no atribuya todo al retardo.",
        ["Anote hora de la última parada.", "Mantenga demanda estable.", "Espere tres minutos.", "Observe intento de arranque.", "Compruebe código si no arranca."],
        "SZ2015", "25", "Restart delay and PCB discharge")
    add(20, "MULTI V: retorno de aceite y desescarche", "VRF que cambia temporalmente válvulas, frecuencia o ventiladores.", "MULTI V 5", "system",
        "Distinguir control normal de una pérdida de capacidad.", "El sistema ejecuta retorno de aceite y desescarche para proteger compresores y recuperar rendimiento.",
        "Durante estas secuencias algunas interiores pueden variar temporalmente su entrega.",
        "Use LGMV para confirmar el estado antes de intervenir.",
        ["Observe estado en LGMV/SSD.", "Anote presiones y temperaturas.", "Espere el fin de la secuencia.", "Compruebe retorno a control normal."],
        "MULTIV5", "45", "Oil return and defrost control", page_end="49")

    # 21. Reconocer familia.
    add(21, "Single Zone: una interior y una exterior", "Pareja directa, normalmente mural o comercial individual.", "Single Zone", "system",
        "Elegir códigos y procedimientos de una pareja directa.", "CH01-12 suelen ser interiores y CH21-73 exteriores; CH05/53 son comunicación.",
        "Puede usar display, uno/dos LED o mando según chasis.",
        "No aplique sufijos master/slave de Multi V.",
        ["Identifique número de interiores por exterior.", "Observe tipo de display.", "Anote refrigerante/tensión.", "Use la variante Single Zone."],
        "SZ2015", "25", "Single Zone error family")
    add(21, "Multi F / Multi F MAX", "Una exterior alimenta varias interiores; MAX puede incorporar unidades BD.", "Multi F / Multi F MAX", "system",
        "Interpretar CH07, relación de capacidad y efecto por ramal.", "Comparte circuito exterior y usa tabla de estados OFF.",
        "La exterior usa DIP y TACT-SW; los errores aparecen también en LGMV.",
        "Compruebe si existe BD antes de aislar comunicación.",
        ["Cuente interiores y BD.", "Identifique cableado.", "Observe DIP/LED exterior.", "Use las variantes Multi F."],
        "MULTIF", "92", "Multi F architecture")
    add(21, "Cassette con bomba y boya", "Unidad empotrada con receptor, LED, botón forzado, bomba y float switch.", "Cassette", "indoor",
        "Priorizar drenaje y control de grupo.", "CH04 y sus síntomas son propios de bomba/boya; filtro y hot start tienen indicaciones normales.",
        "Puede trabajar en Single Zone, Multi F o Multi V; identifique la exterior antes de interpretar el alcance.",
        "No confunda la familia de la interior con la arquitectura del sistema.",
        ["Identifique cassette y receptor.", "Compruebe bomba/boya.", "Siga la tubería/cable hasta exterior.", "Seleccione la arquitectura correcta."],
        "CASSETTE", "59", "Cassette controls and errors")
    add(21, "MULTI V: master/slave, HR y SSD", "Uno a tres bastidores exteriores, red de muchas interiores y posible Heat Recovery.", "MULTI V 5", "system",
        "Usar códigos completos, niveles y auto addressing.", "El SSD añade sufijo de bastidor; HR añade número de unidad/puerto.",
        "Una misma base CH puede tener alcance distinto por nivel y topología.",
        "Antes de actuar, identifique master, slaves, HR y control central.",
        ["Mapee bastidores.", "Anote DIP master/slave.", "Inventaríe HR/interiores.", "Registre código completo.", "Use la variante Multi V."],
        "MULTIV5", "126", "Multi V error architecture")

    # 22. Reglas de código.
    add(22, "Código CH base frente a sufijo MULTI V", "Un técnico ve CH21 en mando pero 212 en la placa exterior.", "Todas las familias LG", "system",
        "Unir ambas indicaciones sin perder información.", "CH21 es la familia de fallo; 212 identifica CH21 en slave 1.",
        "En Multi F, LED 2/1 también representa CH21, pero no existe el mismo sufijo de bastidor.",
        "La ficha muestra todas las interpretaciones; abra la que coincida con arquitectura y display.",
        ["Anote código de cada pantalla.", "Identifique la arquitectura.", "Conserve sufijo/bastidor.", "Compare las interpretaciones.", "Elija por reconocimiento."],
        "MULTIV5", "126", "Error code display examples")
    add(22, "Cuando hay varios errores: prioridad y cadena causal", "Display alterna o solo muestra uno de varios fallos.", "Single Zone / Multi F / MULTI V", "system",
        "Evitar reparar únicamente el último síntoma.", "Single/Multi F priorizan un código; Multi V muestra el menor código primero cuando coinciden.",
        "Una pérdida de alimentación puede generar después comunicación; repare primero la causa primaria.",
        "Use historial/LGMV para ordenar por hora.",
        ["Anote todos los ciclos.", "Consulte historial.", "Ordene por hora y alimentación.", "Repare causa primaria.", "Confirme que no reaparecen secundarios."],
        "MULTIV5", "126", "Simultaneous error display")

    # 23. Placas.
    add(23, "Placa interior: capacidad, EEPROM y grupo", "PCB interior sustituida en Single/Multi/MULTI V.", "LG indoor unit", "indoor",
        "Evitar CH09, capacidad incorrecta o pérdida de dirección.", "La nueva placa puede exigir EEPROM/datos, DIP master/slave y repetición de auto addressing.",
        "Fotografíe conectores, DIP y puentes antes de desmontar.",
        "En MULTI V, repita auto address después de cambiar una PCB interior.",
        ["Corte alimentación.", "Fotografíe y anote ajustes.", "Monte EEPROM/repuesto correcto.", "Restaure DIP/conectores.", "Repita auto address/Test Run."],
        "MULTIV5", "52", "PCB replacement and auto addressing")
    add(23, "Placa exterior: DIP, EEPROM y bastidor", "Main/inverter/fan PCB sustituida en Multi F o MULTI V.", "LG outdoor unit", "outdoor",
        "Recuperar identidad master/slave y opciones.", "CH60/86/87/104 pueden aparecer por memoria, orientación o configuración incorrectas.",
        "No copie un DIP de otra capacidad sin confirmar la tabla del equipo.",
        "Tras el cambio, verifique comunicaciones, ventilador, inverter, auto address e ITR.",
        ["Corte y espere descarga.", "Fotografíe DIP/EEPROM/conectores.", "Instale repuesto correcto.", "Restaure identidad y opciones.", "Ejecute auto address y Test Run."],
        "MULTIV5", "132", "EEPROM and PCB communication error codes", page_end="134")

    for variant_id, item in enumerate(procedures, start=1):
        item["id"] = variant_id
        item["sort_order"] = variant_id
        topics[item["topic_id"]]["variants"].append(item)
    return [topics[key] for key in sorted(topics)]


def build_search(
    topics: list[dict[str, Any]],
    error_indexes: list[dict[str, Any]],
    error_details: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    def synonyms(value: str) -> str:
        normalized = normalize(value)
        additions: list[str] = []
        if "BOYA" in normalized or "FLOAT" in normalized:
            additions.append("flotador desbordamiento overflow drain drenaje")
        if "RECOGIDA" in normalized or "PUMP DOWN" in normalized:
            additions.append("recuperacion refrigerante refrigeracion forzada")
        if "MANDO" in normalized:
            additions.append("remote controller control cableado tres hilos")
        if "AUTO ADDRESS" in normalized:
            additions.append("direccionamiento automatico SW01C 88")
        if "LGMV" in normalized:
            additions.append("monitorizacion graficas datos tiempo real service tool")
        if "FDD" in normalized:
            additions.append("Fd8 Fd9 full cooling full heating diagnosis")
        if "VENTILADOR" in normalized:
            additions.append("fan BLDC motor")
        if "COMUNICACION" in normalized:
            additions.append("bus datos señal cableado")
        return " ".join([value] + additions)

    for topic in topics:
        category = topic["category"]
        for item in topic["variants"]:
            parameter_text = " ".join(
                " ".join([
                    str(row.get("parameter_code") or ""),
                    str(row.get("name") or ""),
                    str(row.get("description") or ""),
                    " ".join(
                        " ".join([
                            str(option.get("option_value") or ""),
                            str(option.get("option_label") or ""),
                            str(option.get("effect") or ""),
                        ])
                        for option in row.get("options", [])
                    ),
                ])
                for row in item.get("parameters", [])
            )
            controller_text = " ".join(
                str(value or "") for value in (item.get("controller") or {}).values()
            )
            body = " ".join([
                item["title"],
                item.get("recognition") or "",
                item.get("purpose") or "",
                item.get("summary") or "",
                " ".join(row.get("body") or "" for row in item.get("sections", [])),
                " ".join(
                    " ".join([
                        row.get("instruction") or "",
                        row.get("expected_result") or "",
                    ])
                    for row in item.get("steps", [])
                ),
                parameter_text,
                controller_text,
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
        body = " ".join(
            [index["search_text"]]
            + [
                " ".join(
                    [row["title"], row["description"]]
                    + [info["body"] for info in row["info_items"]]
                    + [
                        " ".join([
                            dataset["name"],
                            dataset.get("notes") or "",
                            " ".join(
                                " ".join([
                                    str(point.get("variable_value") or ""),
                                    str(point.get("value_nominal") or ""),
                                    str(point.get("value_text") or ""),
                                ])
                                for point in dataset.get("points", [])
                            ),
                        ])
                        for dataset in row.get("datasets", [])
                    ]
                )
                for row in detail["interpretations"]
            ]
        )
        entries.append({
            "type": "error",
            "id": index["id"],
            "topic_id": None,
            "category_slug": "errors",
            "category": CATEGORY_BY_SLUG["errors"]["name"],
            "title": f"{index['code_display']} — {index['short_label']}",
            "summary": detail["interpretations"][0]["description"],
            "haystack": normalize(synonyms(body)),
        })
    return entries


def main() -> int:
    expected_root = (ROOT / "data" / "brands" / "lg").resolve()
    if BRAND_DIR.resolve() != expected_root:
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
        category_slug = topic["category"]["slug"]
        topics_by_category[category_slug].append({
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

    navigation_categories = []
    for sort_order, (category_id, slug, name, description) in enumerate(CATEGORIES, start=1):
        navigation_categories.append({
            "id": category_id,
            "slug": slug,
            "name": name,
            "description": description,
            "sort_order": sort_order * 10,
            "active": 1,
            "topics": topics_by_category.get(slug, []),
        })

    for detail in error_details:
        write_json(WEB_DIR / "errors" / "details" / f"{detail['id']}.json", detail)
    write_json(WEB_DIR / "errors" / "index.json", error_indexes)
    write_json(WEB_DIR / "search.json", search_entries)
    write_json(WEB_DIR / "variant_map.json", variant_map)

    source_rows = [
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
        for source_id, row in enumerate(SOURCES.values(), start=1)
    ]
    write_json(WEB_DIR / "sources.json", source_rows)

    coverage_notes = {
        "errors": "Single Zone, Multi F, cassette y MULTI V 5 con CH, LED y sufijos master/slave.",
        "diagnostic_access": "Display CH, conteo de LED, mando, placa exterior, SSD y LGMV.",
        "history_reset": "Historial de 20 eventos, descarga de tres minutos, rearme y niveles Multi V.",
        "service_modes": "Marcha forzada, refrigeración forzada, Pump Down, FDD y respaldo de compresor.",
        "configuration": "Programación PREMTC00U/PREMTB101, ESP, estática, sensores, DIP y límites.",
        "controllers_buses": "Mandos de tres hilos: rojo 12 V, amarillo señal, negro GND, grupos y CH03.",
        "drainage_overflow": "Cassette con CH04, bomba, boya, desbordamiento y prueba tras instalación.",
        "commissioning": "Test Run Single Zone/Multi F y auto addressing/ITR de MULTI V.",
        "multisplit": "Multi F y Multi F MAX: errores OFF, CH07, cableado y unidades BD.",
        "multi_v_network": "Master/slave, HR, RS-485, auto addressing, sufijos y niveles 1-4.",
        "component_checks": "NTC, presiones, bomba, boya, BLDC, compresor, IPM y placas inverter.",
        "technical_values": "12 V del mando, colores, umbrales CH23/CH51 y sufijos de bastidor.",
        "normal_states": "Retardo de tres minutos, hot start, desescarche y retorno de aceite.",
        "service_tools_boards": "LGMV, SIMs, FDD y pasos después de sustituir PCB.",
        "system_architecture": "Pistas para distinguir Single Zone, Multi F/MAX, cassette y MULTI V.",
    }
    coverage = [
        {
            "id": category_id,
            "brand_id": BRAND_ID,
            "area_slug": slug,
            "area_name": name,
            "equipment_scope": "LG — corpus Referencia V1",
            "coverage_status": "reference_v1",
            "source_count": len(SOURCES),
            "notes": coverage_notes[slug],
            "last_reviewed": now[:10],
        }
        for category_id, slug, name, _ in CATEGORIES
    ]
    write_json(WEB_DIR / "coverage.json", coverage)

    counts = {
        "categories": len(navigation_categories),
        "topics": len(topics),
        "variants": len(variant_map),
        "errors": len(error_indexes),
        "search_entries": len(search_entries),
    }
    navigation = {
        "metadata": {
            "schema_name": "Super Tecnico",
            "navigation_model": "brand_category_topic_variant",
            "schema_version": "2.2.0",
            "data_version": "1.0.0",
            "last_update_utc": now,
            "reference_brand": "LG",
            "verification_warning": (
                "Completa respecto al corpus LG Referencia V1. Confirme siempre "
                "familia, mando, forma de indicación y sufijo de bastidor."
            ),
        },
        "categories": navigation_categories,
    }
    write_json(WEB_DIR / "navigation.json", navigation)

    brand = {
        "slug": "lg",
        "name": "LG",
        "display_name": "LG",
        "enabled": True,
        "web_data": "web",
        "media": "media",
        "publish_media": False,
        "static_site": True,
        "schema_version": "2.2.0",
        "data_version": "1.0.0",
        "exported_at_utc": now,
        "counts": counts,
        "notes": (
            "LG Referencia V1: Single Zone, Multi F/Multi F MAX, cassette, "
            "MULTI V 5, PREMTB101/PREMTC00U y LGMV. Sin PDFs ni capturas."
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
