#!/usr/bin/env python3
"""Construye Toshiba Referencia V1 para Super Técnico.

La salida pública contiene resúmenes técnicos trazables, no PDF, capturas ni
bases privadas. Los códigos se separan por familia y punto de lectura.
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
BRAND_DIR = ROOT / "data" / "brands" / "toshiba"
WEB_DIR = BRAND_DIR / "web"
BRAND_ID = 10


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def normalize(value: str) -> str:
    value = "".join(
        char for char in unicodedata.normalize("NFD", str(value or ""))
        if unicodedata.category(char) != "Mn"
    ).upper()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9]+", " ", value)).strip()


SOURCES: dict[str, dict[str, str]] = {
    "SEIYA": {
        "title": "SEIYA S4 R32 Service Manual",
        "document_ref": "SVM-24006-02",
        "source_url": "https://www.toshiba-aircon.co.uk/content/dam/public-toshiba/gb/documents/products/r32-split-systems/residential/wall-mounted/ras-seiya-s4-high-wall/20250610_SM_SVM-24006_02_R32_RAS_SEIYA_S4_EN.pdf",
        "type": "service_manual", "year": "2025",
    },
    "MULTI": {
        "title": "RAS-5M34G3AVG-E R32 Multi Split Service Manual",
        "document_ref": "SVM-23012",
        "source_url": "https://www.toshiba-aircon.co.uk/content/dam/public-toshiba/gb/documents/products/r32-split-systems/residential/multi-split/ras-outdoor-2-5-rooms-g3/20233005_SM_SVM-23012_R32_RAS-5M34G3AVG-E_EN.pdf",
        "type": "service_manual", "year": "2023",
    },
    "RAV": {
        "title": "RAV-GM224/2801AT8-E Digital Inverter Service Manual",
        "document_ref": "A10-1901-1",
        "source_url": "https://www.toshiba-aircon.co.uk/content/dam/public-toshiba/gb/documents/products/r32-split-systems/light-commercial/rav-digital-inverter-outdoor/20190926_SM_A10-1901-1_RAV-GM224_2801AT8-E_EN.pdf",
        "type": "service_manual", "year": "2019",
    },
    "CASSETTE": {
        "title": "RAV-RM Compact 4-Way Cassette Service Manual",
        "document_ref": "A10-1811",
        "source_url": "https://www.toshiba-aircon.co.uk/content/dam/public-toshiba/gb/products/archive/light-commercial/r32-rav-digital-inverter-compact-4-way-cassette/20180314_SM_A10-1811_Compact_Cassette_RAV-RM_1MUT-E_EN.pdf/_jcr_content/renditions/original.media_file.download_attachment.file/20180314_SM_A10-1811_Compact_Cassette_RAV-RM_1MUT-E_EN.pdf",
        "type": "service_manual", "year": "2018",
    },
    "SMMSE": {
        "title": "SMMSe 2-Pipe VRF Service Manual",
        "document_ref": "SVM-15067-11",
        "source_url": "https://www.toshiba-aircon.co.uk/content/dam/public-toshiba/gb/products/archive/vrf--air-to-water/smmse-2-pipe-heat-pump-outdoor/20181108_SVM-15067-11_MMY-MAP_6HT8P-E.pdf/_jcr_content/renditions/original.media_file.download_attachment.file/20181108_SVM-15067-11_MMY-MAP_6HT8P-E.pdf",
        "type": "service_manual", "year": "2018",
    },
    "SMMSU": {
        "title": "SMMS-u VRF Outdoor Service Manual",
        "document_ref": "SVM-20113-9",
        "source_url": "https://www.toshiba-aircon.co.uk/content/dam/public-toshiba/gb/documents/products/r410a-split-systems/smmsu-mmy-mup-18ht8p-e/20220801_SM_SVM-20113-9_MMY-MUP_1HT8P-E_8-24HP_EN.pdf",
        "type": "service_manual", "year": "2022",
    },
    "RBCI": {
        "title": "RBC-AMTU31-E Installation Manual",
        "document_ref": "DEB9509102",
        "source_url": "https://www.toshiba-aircon.co.uk/content/dam/public-toshiba/gb/documents/products/controls/standard/rbc-amtu31-e/20210419_IM_DEB9509102_RBC-AMTU31-E_RC_EN.pdf",
        "type": "installation_manual", "year": "2021",
    },
    "RBCO": {
        "title": "RBC-AMTU31-E Owner's Manual",
        "document_ref": "DEB9509002-01",
        "source_url": "https://www.toshiba-aircon.co.uk/content/dam/public-toshiba/gb/documents/products/controls/standard/rbc-amtu31-e/20240318_OM_DEB9509002_01_RBC-AMTU31-E_EN.pdf",
        "type": "owner_manual", "year": "2024",
    },
    "TOOLS": {
        "title": "Toshiba Air Conditioning — Technical Support Tools",
        "document_ref": "TOSHIBA-UK-TECHNICAL-SUPPORT-TOOLS",
        "source_url": "https://www.toshiba-aircon.co.uk/en/support/technical-support-tools.html",
        "type": "official_web", "year": "actualizado",
    },
}


def source(ref: str, page: str, section_name: str) -> dict[str, Any]:
    row = SOURCES[ref]
    return {
        "title": row["title"], "document_ref": row["document_ref"],
        "source_url": row["source_url"], "page_start": page, "page_end": page,
        "section": section_name,
    }


CATEGORIES = [
    (1, "errors", "Errores y protecciones", "Códigos de mando, unidad interior, exterior, RAV y VRF con alcance documentado."),
    (2, "outdoor_led_diagnostics", "Pilotos y display de la unidad exterior", "Tablas D800–D805 y displays de siete segmentos separadas por placa."),
    (3, "diagnostic_access", "Obtención de códigos y subcódigos", "Lectura inalámbrica, mando cableado, pilotos, siete segmentos y monitor."),
    (4, "history_reset", "Historial y borrado", "Memorias de averías, notice codes y formas de borrado."),
    (5, "service_modes", "Modos de servicio", "Test Run, marcha forzada, recogida, comprobación de ventiladores y válvulas."),
    (6, "configuration", "Configuración y programación", "DN, O.DN, DIP, selectores y ajustes de placa o mando."),
    (7, "controllers_buses", "Mandos y buses", "RBC, A/B, U1/U2, red, alimentación, grupos y arranque."),
    (8, "drainage_overflow", "Drenaje y desbordamiento", "Bomba, boya, P10 y secuencias distintas en frío, calor y parada."),
    (9, "commissioning", "Puesta en marcha", "Direccionamiento, terminadores, test, comprobación de tuberías y válvulas."),
    (10, "multisplit", "Multisplit", "Cinco puertos, pilotos por unidad, PMV, tuberías y funcionamiento de respaldo."),
    (11, "vrf_network", "VRF y red", "SMMS-e/SMMS-u, cabeceras, seguidoras, comunicación y alcance de parada."),
    (12, "component_checks", "Comprobación de componentes", "Sondas, ventiladores, compresor, inverter, PMV, presiones y válvulas."),
    (13, "technical_values", "Valores técnicos", "Tensiones, resistencias, tiempos, temperaturas y umbrales documentados."),
    (14, "normal_states", "Comportamientos normales", "Retardos, desescarche, recuperación de aceite, Peak Cut y bajo ruido."),
    (15, "service_tools_boards", "Herramientas y placas", "Herramientas oficiales, Wave Tool, NFC y tareas después de cambiar una PCB."),
    (16, "system_architecture", "Reconocer el sistema", "Pistas para no aplicar una tabla RAC, RAV, multisplit o VRF a otra familia."),
]
CATEGORY_BY_SLUG = {
    slug: {"id": ident, "slug": slug, "name": name, "description": description}
    for ident, slug, name, description in CATEGORIES
}


PROFILE_TEXT = {
    "communication": (
        ["Cable abierto, cruzado o en corto", "Alimentación ausente en uno de los equipos", "Dirección, terminador o configuración incorrectos", "Circuito de transmisión defectuoso"],
        ["Confirmar dónde se leyó el código", "Medir alimentación y bus con la referencia de esa familia", "Revisar continuidad, polaridad si procede y terminadores", "Aislar por tramos antes de sustituir una placa"],
        "No extrapolar una tensión de RAC al bus A/B, U1/U2 o al enlace VRF.",
    ),
    "sensor": (
        ["Sensor abierto o en corto", "Conector suelto o cable dañado", "Sensor desprendido del tubo", "Entrada analógica de la placa defectuosa"],
        ["Medir resistencia con el sensor aislado", "Comparar con temperatura real y curva correcta", "Comprobar montaje térmico y cable", "Comparar la lectura de monitor con un instrumento"],
        "La misma denominación puede usar una curva distinta según el punto y la generación.",
    ),
    "fan": (
        ["Turbina o hélice bloqueada", "Motor o realimentación defectuosos", "Conector/cableado anormal", "Driver o alimentación de placa defectuosos"],
        ["Comprobar giro con la alimentación aislada", "Revisar conectores y devanados", "Medir alimentación y salida con el procedimiento documentado", "Observar si el error sigue al motor o a la placa"],
        "No conectar ni desconectar motores inverter o BLDC con tensión.",
    ),
    "drain": (
        ["Boya atascada arriba", "Desagüe obstruido o mal sifonado", "Bomba defectuosa", "Conector o entrada de flotador abiertos"],
        ["Verificar el nivel real de agua", "Comprobar continuidad y movimiento de la boya", "Confirmar que la bomba evacua y que el tubo no retorna agua", "Repetir la prueba con agua antes de rearmar"],
        "En cassette Toshiba la temporización cambia según la bomba ya estuviera funcionando o estuviera parada.",
    ),
    "configuration": (
        ["Dirección duplicada o sin asignar", "Capacidad/DN/DIP incorrectos", "PCB nueva sin configurar", "EEPROM o memoria defectuosa"],
        ["Anotar todos los selectores antes de tocar", "Comparar DN/O.DN y cabecera/seguidora", "Repetir direccionamiento con todas las unidades alimentadas", "Verificar el número reconocido tras el reinicio"],
        "Un ajuste incorrecto puede detener una unidad, una línea o todo el sistema.",
    ),
    "inverter": (
        ["Compresor bloqueado o bobinado anormal", "IPM/inverter defectuoso", "Bus DC o red fuera de rango", "Disipador o ventilación anormales"],
        ["Aislar y comprobar descarga del bus", "Comparar U-V-W y aislamiento", "Medir red y salida con el procedimiento de servicio", "Separar fallo de compresor, cable e inverter"],
        "Las mediciones de potencia requieren personal cualificado y el manual exacto.",
    ),
    "power": (
        ["Fase ausente, secuencia incorrecta o tensión fuera de rango", "Conexión floja", "Rectificador/PFC/fusible defectuoso", "Sensor de tensión o corriente defectuoso"],
        ["Medir entrada en reposo y bajo carga", "Comprobar las tres fases y aprietes", "Revisar fusibles y bus con seguridad", "Distinguir una lectura falsa de un problema real de red"],
        "P05 en VRF admite subcódigos de detección de potencia, fase abierta y cableado.",
    ),
    "pressure": (
        ["Válvula de servicio cerrada", "Carga incorrecta o fuga", "Intercambiador/flujo de aire insuficiente", "PMV, presostato o transductor defectuoso"],
        ["Confirmar válvulas totalmente abiertas", "Comparar presión real y lectura de sensor", "Revisar ventiladores, filtros y baterías", "Comprobar PMV y cantidad de refrigerante"],
        "El alcance y los umbrales cambian entre RAV, multisplit y VRF.",
    ),
    "compressor": (
        ["Cable U-V-W o devanados anormales", "Presiones sin equilibrar", "Inverter defectuoso", "Compresor mecánicamente bloqueado"],
        ["Aislar alimentación y descargar el bus", "Comparar resistencias entre fases y aislamiento a chasis", "Comprobar salida del inverter sin extrapolar valores", "Revisar el historial de protecciones previas"],
        "En SMMS-u se documentan subcódigos para compresor 1 y 2.",
    ),
    "valve": (
        ["Bobina o cable abierto", "PMV/EEV bloqueada", "Conector intercambiado", "Válvula de cuatro vías sin invertir"],
        ["Comprobar bobina y conector", "Usar el modo de servicio de PMV si existe", "Comparar temperaturas y presiones", "Verificar la inversión antes de condenar la placa"],
        "Una respuesta térmica incorrecta también puede deberse a carga o tubería.",
    ),
    "pcb": (
        ["PCB sin alimentación", "EEPROM o MCU defectuosos", "Conector interno suelto", "Configuración no restaurada tras sustitución"],
        ["Comprobar fuentes y fusibles", "Revisar conectores internos", "Copiar ajustes y direcciones", "Repetir inicialización y comprobar el código"],
        "No sustituir una PCB solo por un código de comunicación sin aislar antes el cableado.",
    ),
    "normal": (
        ["Secuencia normal, aviso de mantenimiento o condición temporal"],
        ["Identificar el texto exacto", "Esperar la secuencia documentada", "Consultar historial si no recupera", "No cambiar componentes por un estado normal"],
        "CL, Ht, or, dF, PC, Ln y Sn son estados, no diagnósticos de componente.",
    ),
}


def six_leds(states: list[str]) -> list[dict[str, str]]:
    return [
        {"label": f"D80{i}", "color": "green" if i == 5 else "yellow", "state": state}
        for i, state in enumerate(states)
    ]


def led_pattern(code: str, meaning: str, bits: str, family: str, *, latest: bool = False, multi: bool = False) -> dict[str, Any]:
    states = []
    for char in bits:
        states.append("fast_blink" if char == "1" and not multi else ("blink" if char == "1" else "off"))
    states.append("slow_blink" if latest else "on")
    return {
        "code_display": code, "indication_type": "outdoor_led",
        "display_location": "placa de la unidad exterior",
        "family_hint": family, "relationship": meaning,
        "led_indicators": six_leds(states),
        "counting_rule": (
            "D800–D804: 3 s encendido / 0,5 s apagado cuando el bit está activo; D805 verde fijo."
            if multi else
            "D800–D804: parpadeo rápido de 5 veces/s cuando el bit está activo; D805 distingue actual e histórico."
        ),
        "cycle_note": (
            "Si hay varias averías, la placa recorre los patrones. Observe todos los ciclos."
            if multi else
            "D805 verde fijo indica avería actual; parpadeo lento de 1 vez/s indica la última avería guardada."
        ),
        "sequence": "Orden físico: D800, D801, D802, D803, D804 y D805.",
    }


RAV_LED_BASE = [
    ("Estado", "Funcionamiento normal", "00000"),
    ("F04", "Sonda de descarga TD", "10000"), ("F06", "Sonda de batería TE", "01000"),
    ("F07", "Sonda TL", "11000"), ("F08", "Sonda exterior TO", "00100"),
    ("F12", "Sonda de aspiración TS", "10100"), ("F13", "Sonda de disipador TH", "01100"),
    ("F15", "TE/TS intercambiadas", "11100"), ("F23", "Sensor de baja Ps", "00010"),
    ("F31", "EEPROM exterior", "01010"), ("H01", "Avería del compresor", "11010"),
    ("H02", "Bloqueo del compresor", "00110"), ("H03", "Detección de corriente", "10110"),
    ("H04", "Termostato de carcasa", "01110"), ("H06", "Protección de baja presión", "11110"),
    ("L10", "Tipo/capacidad exterior sin ajustar", "00001"), ("L29", "Comunicación entre MCU", "10001"),
    ("P03", "Temperatura de descarga", "01001"), ("P04", "Alta presión/termostato", "11001"),
    ("P05", "Alimentación", "00101"), ("P07", "Disipador sobrecalentado", "01101"),
    ("P15", "Fuga de gas", "11101"), ("P19", "Inversión de cuatro vías", "00011"),
    ("P20", "Protección de alta presión", "10011"), ("P22", "Ventilador exterior", "01011"),
    ("P26", "Cortocircuito/overcurrent de accionamiento", "11011"),
    ("P29", "Detección de posición", "00111"),
]
RAV_LED_CURRENT = [led_pattern(*row, "RAV Digital Inverter GM224/280") for row in RAV_LED_BASE]
RAV_LED_LATEST = [led_pattern(*row, "RAV Digital Inverter GM224/280", latest=True) for row in RAV_LED_BASE]

MULTI_LED_BASE = [
    ("Estado", "Funcionamiento normal", "00000"),
    ("1C", "Termostato de carcasa del compresor", "10000"), ("21", "Presostato de alta", "01000"),
    ("1C", "Sistema de compresor", "11000"), ("1D", "Compresor bloqueado", "00100"),
    ("1F", "Avería del compresor", "10100"), ("14", "Elemento de accionamiento en corto", "01100"),
    ("16", "Detección de posición", "11100"), ("17", "Detección de corriente", "00010"),
    ("1C", "Comunicación MCU", "10010"), ("1A", "Ventilador exterior", "01010"),
    ("1E", "Temperatura de descarga", "11010"), ("19", "Sonda TD", "00110"),
    ("1B", "Sonda exterior TO; puede continuar en respaldo", "10110"), ("18", "Sonda TS", "01110"),
    ("18", "Sonda TE", "11110"), ("1C", "Sonda TGa, puerto A", "00001"),
    ("1C", "Sonda TGb, puerto B", "10001"), ("1C", "Sonda TGc, puerto C", "01001"),
    ("1C", "Sonda TGd, puerto D", "11001"), ("1C", "Sonda TGe, puerto E", "00101"),
    ("Sin código interior", "PMV: sobrecalentamiento igual o superior a 20", "10101"),
    ("Sin código interior", "PMV: sobrecalentamiento igual o inferior a -8", "01101"),
    ("20", "Fuga de PMV, unidad A", "00011"), ("20", "Fuga de PMV, unidad B", "10011"),
    ("20", "Fuga de PMV, unidad C", "01011"), ("20", "Fuga de PMV, unidad D", "11011"),
    ("20", "Fuga de PMV, unidad E", "00111"),
    ("Sin código interior", "Cableado o tubería cruzados", "10111"),
    ("1C", "Comunicación MCU, patrón adicional", "01111"),
    ("1C", "Comunicación MCU, todos los bits", "11111"),
]
MULTI_LED = [led_pattern(*row, "RAS-5M34G3AVG-E, placa WP-524", multi=True) for row in MULTI_LED_BASE]


ERROR_SPECS: list[dict[str, Any]] = []


def add_error(
    code: str, title: str, profile: str, ref: str, page: str, *,
    scope: str = "system", family: str, behavior: str,
    technical: str = "", aliases: str = "", led_patterns: list[dict[str, Any]] | None = None,
) -> None:
    ERROR_SPECS.append({
        "code": code, "title": title, "profile": profile, "ref": ref, "page": page,
        "scope": scope, "family": family, "behavior": behavior, "technical": technical,
        "aliases": [x.strip() for x in aliases.split("|") if x.strip()],
        "led_patterns": led_patterns or [],
    })


RAC_ERRORS = [
    ("02", "Sonda de ambiente interior TA", "sensor", "indoor"),
    ("04", "Comunicación serie interior–exterior", "communication", "system"),
    ("07", "Se interrumpe el retorno serie después del arranque", "communication", "system"),
    ("0E", "Sensor de gas/refrigerante", "sensor", "indoor"),
    ("11", "Ventilador interior", "fan", "indoor"), ("12", "PCB interior", "pcb", "indoor"),
    ("14", "Sobrecorriente o cortocircuito del inverter", "inverter", "outdoor"),
    ("16", "Detección de posición del compresor", "compressor", "outdoor"),
    ("17", "Detección de corriente del compresor", "power", "outdoor"),
    ("18", "Sondas de batería TE/TS", "sensor", "outdoor"), ("19", "Sonda de descarga TD", "sensor", "outdoor"),
    ("1A", "Ventilador exterior", "fan", "outdoor"), ("1B", "Sonda exterior TO", "sensor", "outdoor"),
    ("1C", "Sistema/accionamiento del compresor", "compressor", "outdoor"),
    ("1D", "Compresor no gira o devanado/fase anormal", "compressor", "outdoor"),
    ("1E", "Temperatura de descarga superior al límite", "pressure", "outdoor"),
    ("1F", "Corriente alta o avería del compresor", "compressor", "outdoor"),
    ("21", "Retorno serie/protector, alta temperatura o presión", "pressure", "system"),
    ("26", "Vida útil o detección del sensor de gas", "sensor", "indoor"),
    ("27", "Ionizador", "pcb", "indoor"),
    ("7F", "Orden de borrado de memoria desde el mando inalámbrico", "normal", "controller"),
]
for code, title, profile, scope in RAC_ERRORS:
    behavior = (
        "La unidad registra la condición; la sonda TO puede permitir funcionamiento de respaldo sin hacer parpadear la interior."
        if code == "1B" else
        "La unidad afectada se protege o detiene según el bloque de autodiagnóstico."
    )
    technical = (
        "Entre terminales interiores 2 y 3 (L2/S), la señal documentada varía aproximadamente entre 15 y 60 V durante el envío."
        if code == "04" else
        "El mando inalámbrico recorre 52 códigos; el código coincidente produce pitido continuo durante 10 s y parpadeo de indicadores a 5 Hz."
    )
    related = [row for row in MULTI_LED if row["code_display"] == code]
    add_error(code, title, profile, "SEIYA", "99-104", scope=scope, family="SEIYA S4 / RAC",
              behavior=behavior, technical=technical, led_patterns=related)

# El mando agrupa varias condiciones exteriores bajo el mismo código. Se
# conservan como interpretaciones independientes para que ninguna quede oculta.
for title in (
    "Termostato de carcasa del compresor",
    "Protección del sistema de compresor",
    "Comunicación entre MCU de la exterior",
    "Sonda de puerto TGa/TGb/TGc/TGd/TGe",
):
    add_error("1C", title, "communication" if "Comunicación" in title else ("sensor" if "Sonda" in title else "compressor"),
              "MULTI", "120", scope="outdoor", family="RAS-5M34G3 multisplit",
              behavior="La exterior se protege; el patrón D800–D804 separa la causa y, en sondas, el puerto A–E.",
              technical="No decidir por 1C únicamente: lea los seis pilotos y espere todos los ciclos.",
              led_patterns=[row for row in MULTI_LED if row["code_display"] == "1C"])
add_error("18", "Sonda de aspiración TS", "sensor", "MULTI", "120", scope="outdoor",
          family="RAS-5M34G3 multisplit", behavior="La exterior se protege por la lectura de TS.",
          technical="El patrón D800–D804 01110 identifica TS.", led_patterns=[MULTI_LED[14]])
add_error("18", "Sonda de batería exterior TE", "sensor", "MULTI", "120", scope="outdoor",
          family="RAS-5M34G3 multisplit", behavior="La exterior se protege por la lectura de TE.",
          technical="El patrón D800–D804 11110 identifica TE.", led_patterns=[MULTI_LED[15]])
add_error("20", "Fuga o cierre incorrecto de PMV en un puerto A–E", "valve", "MULTI", "120",
          scope="outdoor", family="RAS-5M34G3 multisplit",
          behavior="La exterior identifica la rama afectada mediante D800–D804.",
          technical="D800=A, D801=B, D802=C, D803=D y D804=E.",
          led_patterns=[row for row in MULTI_LED if row["code_display"] == "20"])


RAV_ERRORS = [
    ("E01", "No hay mando cabecera o no recibe señal de la interior", "communication", "controller"),
    ("E02", "El mando no puede enviar a la unidad interior", "communication", "controller"),
    ("E03", "La interior no recibe al mando/adaptador", "communication", "indoor"),
    ("E04", "Comunicación serie interior–exterior", "communication", "system"),
    ("E08", "Direcciones interiores duplicadas", "configuration", "system"),
    ("E09", "Dos mandos configurados como cabecera", "configuration", "controller"),
    ("E10", "Comunicación entre MCU de la unidad interior", "communication", "indoor"),
    ("E18", "Comunicación entre interior cabecera y seguidora", "communication", "indoor"),
    ("F01", "Sonda de batería interior TCJ", "sensor", "indoor"), ("F02", "Sonda de batería interior TC", "sensor", "indoor"),
    ("F04", "Sonda de descarga TD", "sensor", "outdoor"), ("F06", "Sonda exterior TE", "sensor", "outdoor"),
    ("F07", "Sonda exterior TL", "sensor", "outdoor"), ("F08", "Sonda de ambiente exterior TO", "sensor", "outdoor"),
    ("F10", "Sonda de ambiente interior TA", "sensor", "indoor"), ("F12", "Sonda de aspiración TS", "sensor", "outdoor"),
    ("F13", "Sonda del disipador TH", "sensor", "outdoor"), ("F15", "TE y TS mal conectadas", "sensor", "outdoor"),
    ("F23", "Sensor de baja presión Ps", "pressure", "outdoor"), ("F29", "EEPROM/PCB interior", "pcb", "indoor"),
    ("F31", "EEPROM exterior", "pcb", "outdoor"), ("H01", "Avería del compresor", "compressor", "outdoor"),
    ("H02", "Compresor bloqueado", "compressor", "outdoor"), ("H03", "Detección de corriente", "power", "outdoor"),
    ("H04", "Termostato de carcasa del compresor", "pressure", "outdoor"), ("H06", "Protección de baja presión", "pressure", "outdoor"),
    ("L03", "Varias interiores cabecera en el grupo", "configuration", "indoor"),
    ("L07", "Cable de grupo conectado a una interior individual", "configuration", "indoor"),
    ("L08", "Dirección de grupo interior sin ajustar", "configuration", "indoor"),
    ("L09", "Capacidad interior sin ajustar", "configuration", "indoor"),
    ("L10", "Tipo/capacidad exterior sin ajustar", "configuration", "outdoor"),
    ("L20", "Dirección de control central duplicada", "configuration", "system"),
    ("L29", "Comunicación entre MCU de la exterior", "communication", "outdoor"),
    ("L30", "Entrada externa de interbloqueo", "configuration", "indoor"),
    ("L31", "Circuito IC ampliado de la PCB exterior", "pcb", "outdoor"),
    ("P01", "Ventilador interior AC", "fan", "indoor"), ("P03", "Temperatura de descarga TD", "pressure", "outdoor"),
    ("P04", "Alta presión, termostato o tensión de red", "pressure", "outdoor"),
    ("P05", "Alimentación exterior", "power", "outdoor"), ("P07", "Sobretemperatura del disipador", "inverter", "outdoor"),
    ("P10", "Desbordamiento: actúa la boya", "drain", "indoor"), ("P12", "Ventilador interior DC", "fan", "indoor"),
    ("P15", "Detección de fuga de gas", "pressure", "system"), ("P19", "La válvula de cuatro vías no invierte", "valve", "system"),
    ("P20", "Protección de alta presión", "pressure", "system"), ("P22", "Ventilador exterior", "fan", "outdoor"),
    ("P26", "Cortocircuito/sobrecorriente de accionamiento", "inverter", "outdoor"),
    ("P29", "Detección de posición del compresor", "compressor", "outdoor"),
    ("P31", "Otra interior del grupo está averiada", "communication", "indoor"),
]
rav_map = defaultdict(list)
for row in RAV_LED_CURRENT:
    rav_map[row["code_display"]].append(row)
for code, title, profile, scope in RAV_ERRORS:
    behavior = (
        "La interior cabecera avisa y se detiene; la seguidora puede continuar."
        if code == "E09" else
        "La sonda TO admite continuación de funcionamiento en esta familia."
        if code == "F08" else
        "Se detiene la unidad afectada; el resto del grupo depende de la arquitectura y del código asociado."
        if scope in {"indoor", "controller"} else
        "La exterior entra en protección; confirme si la indicación es actual o la última avería guardada."
    )
    tech = (
        "Si la boya actúa con la bomba parada, la bomba arranca; si permanece activa aproximadamente 4 minutos se genera P10."
        if code == "P10" else
        "D805 verde fijo indica avería actual; a 1 Hz indica la última avería. D800–D804 forman el patrón binario."
    )
    add_error(code, title, profile, "RAV", "56-59, 85", scope=scope,
              family="RAV Digital Inverter / cassette", behavior=behavior,
              technical=tech, led_patterns=rav_map[code])


VRF_ERRORS = [
    ("C05", "El control central no puede transmitir", "communication", "controller", "Continúa funcionando."),
    ("C06", "El control central no puede recibir", "communication", "controller", "Continúa funcionando."),
    ("C12", "Aviso de dispositivo de propósito general", "configuration", "controller", "Continúa funcionando."),
    ("E01", "Comunicación mando–interior detectada por el mando", "communication", "controller", "Se detiene la interior afectada."),
    ("E02", "El mando no puede transmitir a las interiores", "communication", "controller", "Se detiene la interior afectada."),
    ("E03", "La interior no recibe al mando", "communication", "indoor", "Se detiene la interior afectada; puede no mostrarse en el propio mando."),
    ("E04", "Comunicación interior–exterior detectada por la interior", "communication", "system", "Se detiene la unidad afectada; según la condición puede detenerse la línea."),
    ("E06", "Disminuye el número de interiores que comunican", "communication", "system", "Puede detener toda la línea o las interiores especificadas."),
    ("E07", "Comunicación interior–exterior detectada por la exterior", "communication", "system", "Se detiene todo el sistema de esa línea."),
    ("E08", "Direcciones interiores duplicadas", "configuration", "system", "Se detiene todo el sistema de esa línea."),
    ("E09", "Mandos cabecera duplicados", "configuration", "controller", "Se detiene la interior cabecera; las seguidoras continúan."),
    ("E10", "Comunicación entre MCU interiores", "communication", "indoor", "Se detiene la interior afectada."),
    ("E11", "Comunicación con Application Control Kit", "communication", "indoor", "Se detiene la unidad afectada."),
    ("E12", "Arranque simultáneo/incompatible de direccionamiento automático", "configuration", "system", "Se detiene el direccionamiento de la línea."),
    ("E15", "No se localizan interiores durante direccionamiento", "configuration", "system", "Se detiene todo el sistema."),
    ("E16", "Exceso de interiores o capacidad conectada", "configuration", "system", "Se detiene todo el sistema."),
    ("E18", "Comunicación cabecera–seguidora interior", "communication", "indoor", "Se detiene la unidad afectada."),
    ("E19", "No hay cabecera exterior o hay varias", "configuration", "system", "Se detiene todo el sistema."),
    ("E20", "Se detecta conexión desde otra línea durante direccionamiento", "configuration", "system", "Se detiene todo el sistema."),
    ("E23", "Transmisión entre unidades exteriores", "communication", "outdoor", "Se detiene todo el sistema."),
    ("E25", "Dirección exterior seguidora duplicada", "configuration", "outdoor", "Se detiene todo el sistema."),
    ("E26", "Desaparece una unidad exterior", "communication", "outdoor", "Se detiene todo el sistema."),
    ("E28", "Avería en una exterior seguidora", "communication", "outdoor", "Se detiene todo el sistema; el subcódigo identifica la exterior."),
    ("E31", "Comunicación interna entre PCB exteriores", "communication", "outdoor", "Se detiene todo el sistema."),
    ("F03", "Sonda de batería interior TC1", "sensor", "indoor", "Se detiene la interior afectada."),
    ("F05", "Sonda de descarga TD2", "sensor", "outdoor", "Se detiene todo el sistema."),
    ("F09", "Sondas TG1/TG2/TG3", "sensor", "outdoor", "Se detiene todo el sistema."),
    ("F11", "Sonda TF", "sensor", "outdoor", "Se detiene todo el sistema."),
    ("F16", "Sensores de presión Pd/Ps intercambiados", "pressure", "outdoor", "Se detiene todo el sistema."),
    ("F24", "Sensor de alta presión Pd", "pressure", "outdoor", "Se detiene todo el sistema."),
    ("H05", "Sonda TD1 mal conectada", "sensor", "outdoor", "Se detiene todo el sistema."),
    ("H07", "Protección de bajo nivel/retorno de aceite", "pressure", "outdoor", "Se detiene todo el sistema."),
    ("H08", "Circuito/sensor de nivel de aceite", "sensor", "outdoor", "Se detiene todo el sistema."),
    ("H15", "Sonda TD2 mal insertada", "sensor", "outdoor", "Se detiene todo el sistema."),
    ("H16", "Circuito de nivel de aceite", "pressure", "outdoor", "Se detiene todo el sistema."),
    ("H17", "Pérdida de sincronismo del compresor", "compressor", "outdoor", "Se detiene todo el sistema."),
    ("L02", "Modelo/capacidad exterior incompatible", "configuration", "outdoor", "Se detiene la unidad afectada."),
    ("L04", "Dirección de línea frigorífica duplicada", "configuration", "system", "Se detiene todo el sistema."),
    ("L05", "Varias interiores configuradas como prioridad", "configuration", "system", "Se detiene todo el sistema."),
    ("L06", "Error de prioridad interior", "configuration", "system", "Se detiene todo el sistema."),
    ("L17", "Combinación de exteriores incompatible", "configuration", "outdoor", "Se detiene todo el sistema."),
    ("L23", "Ajuste de switches/DN incompatible", "configuration", "outdoor", "Se detiene todo el sistema."),
    ("L28", "Más de cinco exteriores conectadas", "configuration", "outdoor", "Se detiene todo el sistema."),
    ("P11", "Escarcha anormal persistente en batería exterior", "pressure", "outdoor", "Se detiene todo el sistema tras repeticiones."),
    ("P13", "Retorno de líquido hacia una exterior parada", "pressure", "outdoor", "Se detiene todo el sistema."),
    ("P14", "Válvula de servicio cerrada durante Test Run", "valve", "outdoor", "Se detiene todo el sistema."),
    ("P17", "Temperatura de descarga TD2 superior al límite", "pressure", "outdoor", "Se detiene todo el sistema."),
    ("P30", "Avería en seguidora de grupo informada al control central", "communication", "controller", "El alcance depende del error real de la seguidora."),
    ("S01", "El control central no recibe señal", "communication", "controller", "Continúa funcionando."),
    ("80", "Comunicación MCU/sub-MCU exterior", "communication", "outdoor", "Se detiene todo el sistema."),
]
for code, title, profile, scope, behavior in VRF_ERRORS:
    tech = (
        "En A/B deben medirse aproximadamente 18 V CC; compruebe cabecera/seguidora y cable no polarizado."
        if code in {"E01", "E02", "E03", "E09"} else
        "El manual SMMS-u distingue expresamente parada total, unidad afectada y continuación."
    )
    add_error(code, title, profile, "SMMSU", "199-208", scope=scope, family="SMMS-u VRF",
              behavior=behavior, technical=tech)

VRF_SHARED = [
    ("F01", "Sonda interior TCJ", "sensor", "indoor", "Se detiene la interior afectada."),
    ("F02", "Sonda interior TC2", "sensor", "indoor", "Se detiene la interior afectada."),
    ("F04", "Sonda de descarga TD1", "sensor", "outdoor", "Se detiene todo el sistema."),
    ("F06", "Sondas exteriores TE1/TE2/TE3", "sensor", "outdoor", "Se detiene todo el sistema."),
    ("F07", "Sondas exteriores TL1/TL2/TL3", "sensor", "outdoor", "Se detiene todo el sistema."),
    ("F08", "Sonda exterior TO", "sensor", "outdoor", "Se detiene todo el sistema en esta familia VRF."),
    ("F10", "Sonda de ambiente interior TA", "sensor", "indoor", "Se detiene la interior afectada."),
    ("F12", "Sondas de aspiración TS1/TS3", "sensor", "outdoor", "Se detiene todo el sistema."),
    ("F13", "Sonda del IPM/disipador TH", "sensor", "outdoor", "Se detiene todo el sistema."),
    ("F15", "Conexión incorrecta de sensores TE/TL", "sensor", "outdoor", "Se detiene todo el sistema."),
    ("F23", "Sensor de baja presión Ps", "pressure", "outdoor", "Se detiene todo el sistema."),
    ("F29", "PCB/EEPROM interior", "pcb", "indoor", "Se detiene la interior afectada."),
    ("F31", "EEPROM de la PCB exterior", "pcb", "outdoor", "Si ocurre en la cabecera se detiene el sistema; una seguidora puede continuar."),
    ("H01", "Avería del compresor", "compressor", "outdoor", "Se detiene todo el sistema."),
    ("H02", "Bloqueo del compresor", "compressor", "outdoor", "Se detiene todo el sistema."),
    ("H03", "Circuito de detección de corriente", "power", "outdoor", "Se detiene todo el sistema."),
    ("H06", "Protección de baja presión", "pressure", "outdoor", "Se detiene todo el sistema."),
    ("L03", "Cabeceras interiores duplicadas", "configuration", "indoor", "Se detiene la unidad o grupo afectado."),
    ("L07", "Cable de grupo en una interior individual", "configuration", "indoor", "Se detiene la interior afectada."),
    ("L08", "Dirección de grupo interior sin ajustar", "configuration", "indoor", "Se detiene la interior afectada."),
    ("L09", "Capacidad interior sin ajustar", "configuration", "indoor", "Se detiene la interior afectada."),
    ("L10", "Capacidad de la exterior sin ajustar", "configuration", "outdoor", "Se detiene todo el sistema."),
    ("L20", "Dirección de control central duplicada", "configuration", "controller", "El sistema puede continuar funcionando."),
    ("L29", "Cantidad/modelo de PCB exteriores no coincide", "communication", "outdoor", "Se detiene todo el sistema."),
    ("L30", "Entrada externa anormal/interbloqueo interior", "configuration", "indoor", "Se detiene la interior afectada."),
    ("L31", "Avería parcial del IC ampliado de la PCB exterior", "pcb", "outdoor", "Continúa funcionando con el aviso registrado."),
    ("P01", "Ventilador interior AC", "fan", "indoor", "Se detiene la interior afectada."),
    ("P03", "Temperatura de descarga TD1 superior al límite", "pressure", "outdoor", "Se detiene todo el sistema."),
    ("P04", "Actúa el presostato de alta", "pressure", "outdoor", "Se detiene todo el sistema."),
    ("P05", "Detección de potencia, fase abierta o cableado de red", "power", "outdoor", "Se detiene todo el sistema."),
    ("P07", "Sobretemperatura o condensación en el disipador", "inverter", "outdoor", "Se detiene todo el sistema."),
    ("P10", "Desbordamiento interior por boya abierta/activa", "drain", "indoor", "El manual VRF indica parada del sistema para la condición detectada."),
    ("P12", "Ventilador interior DC", "fan", "indoor", "Se detiene la interior afectada."),
    ("P15", "Fuga detectada por condición TS o TD", "pressure", "outdoor", "Se detiene todo el sistema."),
    ("P19", "La válvula de cuatro vías no invierte", "valve", "outdoor", "Se detiene todo el sistema."),
    ("P20", "Protección de alta presión por Pd", "pressure", "outdoor", "Se detiene todo el sistema."),
    ("P22", "PCB inverter del ventilador exterior", "fan", "outdoor", "Se detiene todo el sistema."),
    ("P26", "Cortocircuito/sobrecorriente IPM del compresor", "inverter", "outdoor", "Se detiene todo el sistema."),
    ("P29", "Circuito de detección de posición del compresor", "compressor", "outdoor", "Se detiene todo el sistema."),
    ("P31", "Otra interior del grupo tiene E07/L07/L03/L08", "communication", "indoor", "Se detiene la interior correspondiente."),
]
for code, title, profile, scope, behavior in VRF_SHARED:
    add_error(code, title, profile, "SMMSU", "199-208", scope=scope, family="SMMS-u VRF",
              behavior=behavior,
              technical="Interpretación y alcance específicos de SMMS-u; no sustituye la interpretación RAV del mismo código.")

add_error("001", "Aviso: tiempo de mantenimiento del compresor superado", "normal", "SMMSU", "107-108",
          family="SMMS-u TC2U-Link", behavior="El sistema puede funcionar normalmente; aparece el símbolo de llave.",
          technical="O.DN 007 define el umbral en miles de horas; valor 20 equivale a 20.000 horas.")
add_error("022", "Aviso: comunicación o cableado de la etiqueta NFC", "communication", "SMMSU", "107-108",
          family="SMMS-u TC2U-Link", behavior="El sistema puede funcionar normalmente y el aviso cesa al recuperarse la comunicación.",
          technical="Con equipo conectado a CN800 puede aparecer 022 sin avería; diagnosticar NFC con CN800 libre.")
for code, title in [
    ("CL", "Refrigeración"), ("Ht", "Calefacción"), ("or", "Recuperación de aceite"),
    ("dF", "Desescarche"), ("PC", "Peak Cut"), ("Ln", "Bajo ruido"), ("Sn", "Modo nieve"),
]:
    add_error(code, title, "normal", "SMMSE", "display de estado", family="SMMSe/SMMS-u VRF",
              behavior="Estado operativo; no implica por sí solo una avería.", technical="Confirmar el estado y esperar la secuencia normal.")


def build_interpretation(ident: int, spec: dict[str, Any]) -> dict[str, Any]:
    causes, checks, profile_note = PROFILE_TEXT[spec["profile"]]
    technical = spec["technical"] or profile_note
    origin = SOURCES[spec["ref"]]["document_ref"]
    info_items = [
        {"id": ident * 100 + 1, "item_type": "machine_behavior", "title": None, "body": spec["behavior"], "sort_order": 1, "review_status": "reviewed", "origin_ref": origin},
        {"id": ident * 100 + 2, "item_type": "related_element", "title": None, "body": spec["title"], "sort_order": 2, "review_status": "reviewed", "origin_ref": origin},
    ]
    order = 3
    for item_type, values in (("cause", causes), ("check", checks)):
        for text in values:
            info_items.append({"id": ident * 100 + order, "item_type": item_type, "title": None, "body": text, "sort_order": order, "review_status": "reviewed", "origin_ref": origin})
            order += 1
    info_items.append({"id": ident * 100 + order, "item_type": "observation", "title": "Dato técnico", "body": technical, "sort_order": order, "review_status": "reviewed", "origin_ref": origin})
    contexts = [{
        "code_display": spec["code"], "code_normalized": normalize(spec["code"]),
        "indication_type": "controller" if spec["scope"] == "controller" else ("outdoor_display" if spec["scope"] == "outdoor" else "display"),
        "display_location": "mando/controlador" if spec["scope"] == "controller" else ("unidad exterior" if spec["scope"] == "outdoor" else "unidad o sistema"),
        "family_hint": spec["family"], "relationship": "Código documentado en esta familia y punto de indicación.",
        "source_ref": spec["ref"], "source_document_ref": origin, "related_error_id": None,
    }]
    contexts.extend({
        **pattern, "code_normalized": normalize(pattern["code_display"]),
        "source_ref": "MULTI" if spec["family"].startswith("SEIYA") else "RAV",
        "source_document_ref": SOURCES["MULTI" if spec["family"].startswith("SEIYA") else "RAV"]["document_ref"],
        "related_error_id": None,
    } for pattern in spec["led_patterns"])
    lower = spec["behavior"].lower()
    stop_level = (
        "warning" if "continúa" in lower or "estado operativo" in lower or "puede funcionar" in lower
        else "affected_unit" if "afectada" in lower or "cabecera" in lower
        else "all_system" if "todo el sistema" in lower or "toda la línea" in lower
        else "protected_stop"
    )
    return {
        "id": ident, "title": spec["title"],
        "description": f'{spec["code"]} en {spec["family"]}: {spec["title"]}.',
        "source_kind": "official", "confidence": "high", "review_status": "reviewed",
        "indication_contexts": contexts, "info_items": info_items,
        "operational_impacts": [{
            "stop_level": stop_level, "summary": spec["behavior"],
            "affected_scope": f'Alcance documentado para {spec["family"]}.',
            "unaffected_scope": "Consulte el texto: algunas familias permiten continuidad o solo paran la unidad afectada.",
            "restart_behavior": "Corregir la causa, borrar o reiniciar únicamente con el procedimiento de esa familia.",
            "degraded_behavior": None, "notes": "No extrapolar el alcance a otra familia que muestre el mismo código.",
        }],
        "datasets": [{
            "id": ident * 10 + 1, "name": f'{spec["code"]} — referencia técnica',
            "dataset_type": "technical_reference", "variable_name": "Comprobación", "variable_unit": None,
            "value_name": "Dato", "value_unit": None, "tolerance_text": f'Aplicar solo a {spec["family"]}.',
            "source_kind": "official", "calculation_method": None, "review_status": "reviewed",
            "notes": technical, "visible": 1,
            "points": [{"variable_value": None, "value_min": None, "value_nominal": None, "value_max": None, "value_text": technical, "sort_order": 1, "notes": None}],
            "sources": [source(spec["ref"], spec["page"], f'Valor técnico — {spec["code"]}')],
        }],
        "sources": [source(spec["ref"], spec["page"], f'Tabla de códigos — {spec["code"]}')],
    }


def build_errors() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for spec in ERROR_SPECS:
        grouped[normalize(spec["code"])].append(spec)
    index_rows, detail_rows = [], []
    interpretation_id = 1
    for error_id, key in enumerate(sorted(grouped), start=1):
        specs = grouped[key]
        primary = specs[0]
        aliases = list(dict.fromkeys([
            primary["code"], primary["code"].replace("-", " "), primary["code"].replace("-", ""),
            *(alias for spec in specs for alias in spec["aliases"]),
        ]))
        interpretations = []
        for spec in specs:
            interpretations.append(build_interpretation(interpretation_id, spec))
            interpretation_id += 1
        tags = sorted({
            token.lower() for spec in specs
            for token in normalize(f'{spec["title"]} {spec["family"]} {spec["profile"]}').split()
            if len(token) > 2
        })
        detail = {
            "id": error_id, "code_display": primary["code"], "code_normalized": key,
            "indication_type": "mixed" if len({x["scope"] for x in specs}) > 1 else ("outdoor_display" if primary["scope"] == "outdoor" else "display"),
            "unit_scope": primary["scope"], "short_label": primary["title"],
            "aliases": [{"alias_display": value, "alias_normalized": normalize(value)} for value in aliases],
            "tags": tags, "interpretations": interpretations, "media": [],
        }
        index_rows.append({
            "id": error_id, "code_display": primary["code"], "code_normalized": key,
            "indication_type": detail["indication_type"], "unit_scope": primary["scope"],
            "short_label": primary["title"], "aliases": aliases, "tags": tags,
            "search_text": normalize(" ".join([primary["code"], *aliases, *tags, *(x["title"] for x in specs), *(x["family"] for x in specs)])),
            "interpretation_count": len(interpretations),
        })
        detail_rows.append(detail)
    return index_rows, detail_rows


def section(title: str, body: str, kind: str = "technical", open_by_default: bool = False) -> dict[str, Any]:
    return {"section_type": kind, "title": title, "body": body, "collapsed_default": 0 if open_by_default else 1}


def step(no: int, instruction: str, expected: str = "", phase: str = "procedure", warning: str = "none") -> dict[str, Any]:
    return {"phase": phase, "step_no": no, "instruction": instruction, "expected_result": expected or None, "warning_level": warning}


def variant(
    title: str, recognition: str, ref: str, page: str, purpose: str, summary: str, *,
    system: str = "Toshiba", scope: str = "system", steps: list[dict[str, Any]] | None = None,
    parameters: list[dict[str, Any]] | None = None, controller: dict[str, Any] | None = None,
    monitoring: list[dict[str, Any]] | None = None, led_patterns: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "title": title, "recognition": recognition, "system_type": system, "unit_scope": scope,
        "refrigerant": None, "purpose": purpose, "summary": summary,
        "source_kind": "official", "review_status": "reviewed",
        "sections": [
            section("Cómo reconocer esta variante", recognition, "recognition", True),
            section("Qué hace o tiene en cuenta la máquina", summary),
        ],
        "steps": steps or [
            step(1, "Identifique la familia, la placa y el lugar exacto donde aparece la indicación.", phase="prepare"),
            step(2, "Aplique solamente la secuencia documentada para esa variante."),
            step(3, "Anote código, subcódigo, unidad y resultado antes de borrar o cortar tensión.", phase="verify"),
        ],
        "parameters": parameters or [], "controller": controller,
        "monitoring_points": monitoring or [], "led_patterns": led_patterns or [],
        "media": [], "sources": [source(ref, page, title)],
    }


TOPICS: list[dict[str, Any]] = []


def add_topic(category: str, slug: str, title: str, summary: str, variants: list[dict[str, Any]]) -> None:
    TOPICS.append({"category": category, "slug": slug, "title": title, "summary": summary, "variants": variants})


add_topic("outdoor_led_diagnostics", "toshiba-six-led-master", "Tabla maestra Toshiba D800–D805", "Patrones visuales de RAV y multisplit sin convertirlos en un código universal.", [
    variant("RAV — avería actual", "Placa exterior con seis LED D800–D805; D805 verde fijo.", "RAV", "85", "Traducir el patrón actual.", "D800–D804 parpadean rápido a 5 Hz según la avería; D805 permanece fijo.", system="RAV GM224/280", scope="outdoor", led_patterns=RAV_LED_CURRENT),
    variant("RAV — última avería guardada", "Misma placa, pero D805 verde parpadea lentamente a 1 Hz.", "RAV", "85", "Distinguir historial de avería activa.", "Los cinco bits conservan el significado; cambia D805 para indicar memoria.", system="RAV GM224/280", scope="outdoor", led_patterns=RAV_LED_LATEST),
    variant("Multisplit de cinco puertos — WP-524", "Exterior RAS-5M34G3 con D800–D805 y pulsadores SW81/SW82.", "MULTI", "120", "Relacionar cada bit con unidad A–E o protección.", "D800–D804 usan ciclos de 3 s encendido y 0,5 s apagado; varios fallos se muestran sucesivamente.", system="RAS multi 5 rooms", scope="outdoor", led_patterns=MULTI_LED),
])
add_topic("errors", "same-code-different-layer", "El mismo código cambia según familia y punto de lectura", "La ficha mantiene todas las interpretaciones visibles y cerradas.", [
    variant("E01/E04/E09 en RAV y VRF", "Código alfanumérico en mando, interior o red VRF.", "SMMSU", "199-213", "Evitar aplicar una definición única.", "E01 puede detectarse en el mando; E03 en la interior; E04 pertenece al enlace interior–exterior. E09 tiene un alcance específico de cabecera/seguidora.", system="RAV/VRF"),
    variant("1C en RAC/multisplit", "Mando inalámbrico muestra 1C y la placa tiene seis pilotos.", "MULTI", "99, 120", "Abrir todas las posibilidades.", "1C agrupa compresor, termostato, MCU y sondas de puertos; el patrón D800–D804 decide la rama correcta.", system="RAS multi"),
])
add_topic("diagnostic_access", "wireless-service-check", "Mando inalámbrico: Service Check y 52 códigos", "Lectura y borrado sin desmontar la exterior.", [
    variant("Entrar y recorrer códigos", "Mando con orificio CHECK accesible con punta fina.", "SEIYA", "96-99", "Encontrar el código memorizado.", "Pulse CHECK; use ON TIMER/OFF TIMER para recorrer 52 códigos. Un pitido simple descarta; pitido continuo 10 s y pilotos a 5 Hz confirma coincidencia.", system="SEIYA/RAC", scope="controller"),
    variant("Borrar con 7F", "Ya está dentro de Service Check.", "SEIYA", "98-99", "Limpiar la memoria después de reparar.", "La tecla CLR transmite 7F. Cortar y reponer alimentación reinicia el control, pero no borra la memoria.", system="SEIYA/RAC", scope="controller"),
])
add_topic("diagnostic_access", "wired-controller-codes", "Mando cableado RBC: error, subcódigo y unidad", "Lectura desde mando sin exigir el modelo al técnico.", [
    variant("RBC-AMTU31: información y monitor", "Mando rectangular con bus A/B y menús de información.", "RBCO", "15-20", "Ver código y seleccionar unidad.", "La pantalla permite consultar información, datos I.DN/O.DN y monitor de servicio según la unidad conectada.", system="RAV/VRF", scope="controller"),
    variant("Código no visible por caída del propio mando", "La interior o el control central muestra E03, pero el mando no comunica.", "SMMSU", "210", "No concluir que no hay avería.", "E03 puede no aparecer en el mando porque precisamente el enlace A/B está caído; comprobar en control central o exterior.", system="SMMS-u", scope="controller"),
])
add_topic("diagnostic_access", "outdoor-display-access", "Display exterior y subcódigos VRF", "Lectura directa en la PCB exterior.", [
    variant("Código y subcódigo de siete segmentos", "Exterior SMMS-u con SW01–SW05 y display.", "SMMSU", "199-208", "Localizar exterior, compresor o PCB.", "El código principal se completa con subcódigos: número de unidad, compresor 1/2, placa o condición.", system="SMMS-u", scope="outdoor"),
    variant("Forzar identificación de exterior seguidora", "E28 con varias exteriores enlazadas.", "SMMSU", "199-204", "Encontrar la seguidora averiada.", "La función de servicio usa los switches de placa y el ventilador para identificar físicamente la unidad indicada.", system="SMMS-u", scope="outdoor"),
])
add_topic("history_reset", "error-history", "Historial de errores y borrado", "Conservar evidencias antes de rearmar.", [
    variant("RBC: hasta cuatro eventos", "Mando cableado compatible con historial.", "RBCO", "18-20", "Revisar las últimas averías.", "Consulte código, unidad y orden de aparición; anótelos antes de ejecutar el borrado.", system="RAV/VRF", scope="controller"),
    variant("RAV: avería actual frente a última", "D805 fijo o parpadeo lento.", "RAV", "85", "No confundir memoria con fallo presente.", "El mismo patrón D800–D804 se interpreta como actual o histórico según D805.", system="RAV", scope="outdoor"),
])
add_topic("history_reset", "notice-code-history", "SMMS-u: avisos actuales, historial y borrado", "Notice codes no detienen normalmente el equipo.", [
    variant("Avisos actuales", "Display exterior con SW01=1, SW02=1, SW03=14.", "SMMSU", "107-108", "Ver hasta cinco avisos.", "Pulse SW04 un segundo para recorrer n.1 a n.5.", system="SMMS-u", scope="outdoor"),
    variant("Historial de diez avisos", "SW01=1, SW02=2, SW03=14.", "SMMSU", "107-108", "Consultar avisos anteriores.", "SW04 recorre h.1 a h.A, hasta diez registros.", system="SMMS-u", scope="outdoor"),
    variant("Borrar historial", "SW01=2, SW02=15, SW03=8; display n.c.", "SMMSU", "108", "Borrar después de documentar.", "Mantenga SW04 cinco segundos; el display confirma n.c CL.", system="SMMS-u", scope="outdoor"),
])
add_topic("service_modes", "rav-service-switches", "RAV: funciones SW01/SW02", "Pruebas exteriores sin demanda convencional.", [
    variant("Marcha forzada en frío, calor o ventilación", "PCB RAV con SW01 y SW02.", "RAV", "79-84", "Probar el circuito.", "Seleccione la función indicada, vigile protecciones y restaure el modo normal manteniendo SW01+SW02 durante 5 s.", system="RAV", scope="outdoor"),
    variant("Monitor de sensores, corriente, frecuencia y PMV", "Misma PCB y display/pilotos de servicio.", "RAV", "79-84", "Observar variables antes de sustituir componentes.", "La selección de servicio permite recorrer sensores, corriente, frecuencia del compresor y apertura PMV.", system="RAV", scope="outdoor"),
])
add_topic("service_modes", "multi-service-switches", "Multisplit: SW81/SW82", "Pruebas específicas de cinco puertos.", [
    variant("Recogida de refrigerante", "Exterior WP-524 con SW81/SW82.", "MULTI", "89-91", "Ejecutar refrigerant collection.", "Siga la secuencia de botones, válvulas y tiempos; la protección permanece activa.", system="RAS multi", scope="outdoor"),
    variant("Comprobar cableado/tubería", "Varias interiores conectadas a puertos A–E.", "MULTI", "89-91", "Detectar cruces.", "La placa compara la respuesta térmica de cada puerto y puede mostrar un patrón sin código interior.", system="RAS multi", scope="outdoor"),
    variant("Prueba de ventilador y PMV", "Necesidad de mover un componente de forma controlada.", "MULTI", "89-91", "Separar motor, válvula y placa.", "Use solo la posición documentada de SW81/SW82 y vuelva al modo normal al terminar.", system="RAS multi", scope="outdoor"),
])
add_topic("service_modes", "vrf-test-run", "VRF: Test Run y funciones forzadas", "Pruebas por línea con protecciones activas.", [
    variant("Test Run desde la exterior", "SMMS-e/u con dirección y comunicación finalizadas.", "SMMSE", "119-145", "Validar la instalación.", "Abra válvulas, alimente calentadores, confirme direcciones y ejecute frío/calor desde la cabecera.", system="SMMSe/SMMS-u", scope="outdoor"),
    variant("Abrir PMV, solenoides y ventiladores", "Modo de servicio exterior con selectores.", "SMMSE", "150-169", "Comprobar actuadores.", "La función fuerza componentes concretos; anote el estado y restaure los selectores.", system="SMMSe", scope="outdoor"),
    variant("Recuperación/pump down", "Sistema y tubería preparados para servicio.", "SMMSE", "170-180", "Gestionar refrigerante sin confundirlo con Test Run.", "La secuencia depende de la arquitectura VRF y de las válvulas; no aplicar el método de un split.", system="SMMSe", scope="outdoor"),
])
add_topic("configuration", "dn-programming", "Programación DN desde mando", "Ajustes interiores y exteriores con trazabilidad.", [
    variant("I.DN interior", "RBC-AMTU31 conectado al grupo.", "RBCO", "15-20", "Leer o modificar funciones interiores.", "Seleccione unidad, código DN y valor; registre el valor original y reinicie solo si el manual lo pide.", system="RAV/VRF", scope="controller"),
    variant("O.DN exterior", "Mando/control de servicio compatible con SMMS-u.", "SMMSU", "107-110", "Configurar funciones exteriores.", "O.DN 007 fija el aviso de mantenimiento del compresor; el valor se multiplica por 1.000 horas.", system="SMMS-u", scope="outdoor"),
])
add_topic("configuration", "vrf-addressing-switches", "Direcciones, cabecera, seguidoras y terminadores", "La red debe estar definida antes de operar.", [
    variant("Dirección de línea frigorífica", "Varias líneas U1/U2 y exteriores enlazadas.", "SMMSE", "62-95", "Evitar E04/E07/E08/L04.", "Asigne direcciones únicas, seleccione cabecera/seguidoras y compruebe el número reconocido.", system="SMMSe/SMMS-u"),
    variant("Terminador de comunicación", "Inicio y final de una red TU2C/TCC-Link.", "SMMSU", "210-212", "Evitar bus abierto o múltiples terminadores.", "Compruebe la posición de terminación y confirme con el monitor cuando la familia lo permita.", system="SMMS-u"),
])
add_topic("controllers_buses", "rbc-amtu31-bus", "RBC-AMTU31: bus A/B de dos hilos", "Cableado no polarizado y alimentación por bus.", [
    variant("Cable y terminales A/B", "Mando cableado con dos bornes de comunicación.", "RBCI", "4-7", "Conectar sin crear fallos intermitentes.", "Bus no polarizado, conductores de 0,5 a 2 mm²; mantenga separación respecto a potencia.", system="RAV/VRF", scope="controller", controller={"controller_type": "wired", "bus_type": "A/B", "wire_count": "2", "polarity": "no polarizado", "nominal_voltage": "aprox. 18 V CC en diagnóstico SMMS-u"}),
    variant("Hasta 8 o 16 interiores según enlace", "Control de grupo desde un único mando.", "RBCI", "5-8", "No superar la capacidad de red.", "Admite hasta 8 unidades TCC-Link o hasta 16 TU2C-Link en la configuración documentada.", system="RAV/VRF", scope="controller"),
    variant("Dos mandos: cabecera y seguidor", "Dos RBC en el mismo grupo.", "RBCI", "8-10", "Evitar E09.", "Configure uno como cabecera y el otro como seguidor mediante el ajuste indicado.", system="RAV/VRF", scope="controller"),
])
add_topic("controllers_buses", "controller-power-up", "Qué hace el mando al alimentar", "No confundir inicialización con avería.", [
    variant("Primer arranque: SETTING", "RBC-AMTU31 recién conectado o sistema inicializado.", "RBCI", "11-12", "Esperar la adquisición de datos.", "El primer SETTING puede durar aproximadamente 10 minutos; arranques posteriores, alrededor de 3 minutos.", system="RAV/VRF", scope="controller"),
    variant("Comprobar A/B en E01", "Mando sin pantalla normal o E01/E03.", "SMMSU", "210", "Separar mando, bus e interior.", "La referencia de diagnóstico es aproximadamente 18 V CC entre A y B.", system="SMMS-u", scope="controller"),
])
add_topic("controllers_buses", "rac-serial-bus", "RAC: comunicación interior–exterior", "Señal distinta del bus de mando.", [
    variant("Terminales 2–3 / L2–S", "SEIYA con código 04.", "SEIYA", "101-104", "Comprobar si la interior transmite.", "La medida con diodo varía aproximadamente entre 15 y 60 V durante el envío.", system="SEIYA/RAC"),
    variant("Temporización de reintento", "No llega retorno de la exterior.", "SEIYA", "101-104", "Interpretar cuándo aparece 04.", "Tras el retardo de 3 minutos, transmite durante 1 minuto; para 3 minutos y reintenta. Si sigue sin retorno, indica el fallo.", system="SEIYA/RAC"),
])
add_topic("drainage_overflow", "cassette-p10-sequence", "Cassette: secuencia completa P10", "La respuesta depende de si la bomba ya funcionaba.", [
    variant("Frío o Dry con bomba en marcha", "Cassette produciendo condensado.", "CASSETTE", "38-39", "Interpretar la boya atascada.", "La bomba funciona normalmente. Si actúa la boya, se detiene el compresor, la bomba continúa y se emite P10.", system="RAV cassette", scope="indoor"),
    variant("Calor, ventilación o parada con bomba parada", "No hay orden normal de drenaje.", "CASSETTE", "38-39", "Detectar agua o boya pegada.", "Si actúa la boya, se detiene el compresor y arranca la bomba; si permanece activa unos 4 minutos, se emite P10.", system="RAV cassette", scope="indoor"),
    variant("Postfuncionamiento de bomba", "Se detiene frío o Dry.", "CASSETTE", "38-39", "No confundir bomba activa con fallo.", "La bomba sigue funcionando 5 minutos para vaciar la bandeja.", system="RAV cassette", scope="indoor"),
])
add_topic("drainage_overflow", "cassette-drain-checks", "Comprobación de boya, bomba y placa", "Orden práctico antes de sustituir componentes.", [
    variant("Diagnóstico P10", "Bandeja con agua o código P10.", "CASSETTE", "60", "Localizar bloqueo mecánico o eléctrico.", "Compruebe boya, bomba, tubería, conectores y PCB; una boya bloqueada puede dar el mismo síntoma en frío y calor.", system="RAV cassette", scope="indoor"),
    variant("CN71 Operation Check", "PCB interior con conector CHK/CN71.", "CASSETTE", "45-46", "Probar interior sin comunicación normal.", "La función activa ventilador alto, lamas y bomba de drenaje; úsela solo como indica el manual.", system="RAV cassette", scope="indoor"),
])
add_topic("commissioning", "vrf-address-setup", "VRF: direccionamiento y reconocimiento", "Evitar errores encadenados al arrancar.", [
    variant("Orden de alimentación", "Instalación nueva con E04/E12/E15.", "SMMSU", "210-213", "Permitir direccionamiento correcto.", "Siga el orden interior–exterior indicado, con todas las interiores alimentadas y una única red por línea.", system="SMMS-u"),
    variant("Repetir dirección automática", "Dirección duplicada, unidad ausente o cantidad incorrecta.", "SMMSE", "62-95", "Reconstruir el mapa.", "Corrija cable/energía/terminación, borre la condición y repita la adquisición completa.", system="SMMSe/SMMS-u"),
])
add_topic("commissioning", "pre-test-checks", "Antes de Test Run", "Condiciones que la máquina sigue vigilando.", [
    variant("Válvulas y refrigerante", "Sistema instalado o reparado.", "SMMSU", "205-208", "Evitar P14/P15/P20.", "Abra totalmente válvulas, confirme estanqueidad/carga y flujo de aire; Test Run no anula las protecciones.", system="RAV/VRF"),
    variant("Calentador de cárter y comunicaciones", "VRF parado mucho tiempo o recién alimentado.", "SMMSE", "119-145", "Evitar arranques dañinos.", "Respete el tiempo previo de alimentación y confirme que todas las unidades están reconocidas.", system="SMMSe/SMMS-u"),
])
add_topic("multisplit", "five-port-identification", "Multisplit de cinco puertos A–E", "Cada LED amarillo puede representar una unidad.", [
    variant("D800=A, D801=B, D802=C, D803=D, D804=E", "Patrones de sonda TGa–TGe o fuga PMV.", "MULTI", "120", "Localizar físicamente la rama.", "Los bits individuales permiten saber qué puerto provoca el patrón.", system="RAS multi", scope="outdoor"),
    variant("Varios fallos se alternan", "El patrón cambia mientras se observa.", "MULTI", "120", "No quedarse con el primer código.", "Espere varios ciclos y anote todos los patrones antes de reiniciar.", system="RAS multi", scope="outdoor"),
])
add_topic("multisplit", "multi-backup-operation", "Funcionamiento de respaldo y fallos sin código interior", "No toda avería exterior se ve igual en la interior.", [
    variant("Sonda TO 1B", "Patrón 10110 y posible ausencia de parpadeo interior.", "MULTI", "120", "Reconocer operación degradada.", "La exterior registra la sonda TO y puede continuar mediante respaldo.", system="RAS multi", scope="outdoor"),
    variant("PMV y tuberías cruzadas sin código interior", "Patrón exterior, pero la interior no muestra código.", "MULTI", "120", "Consultar siempre la placa.", "Sobrecalentamiento anormal y miswiring/mispiping pueden existir sin código en la interior.", system="RAS multi", scope="outdoor"),
])
add_topic("vrf_network", "vrf-stop-scope", "VRF: parada total, unidad afectada o continuidad", "El alcance se muestra dentro de cada interpretación.", [
    variant("Parada total de línea", "E07/E08/E19/E23/E25/E26, protecciones exteriores.", "SMMSU", "199-208", "Saber por qué paran todas.", "Comunicación exterior, direcciones de línea y protecciones de ciclo detienen el sistema completo.", system="SMMS-u"),
    variant("Solo unidad afectada", "E01/E03/E10/E18, sensores interiores.", "SMMSU", "199-208", "Mantener operativas otras unidades cuando está permitido.", "El manual identifica la dirección detectada y detiene la interior correspondiente.", system="SMMS-u"),
    variant("Continúa funcionando", "C05/C06/C12, S01 y notice codes.", "SMMSU", "199-208", "Separar aviso de parada.", "La red o el control pueden seguir operando mientras se registra el aviso.", system="SMMS-u"),
])
add_topic("vrf_network", "cooperative-defrost", "Desescarche cooperativo entre sistemas", "Evita que todos desescarchen a la vez.", [
    variant("Dos o tres sistemas coordinados", "Cabeceras enlazadas por Uh (U3/U4).", "SMMSU", "109-110", "Reducir caída de temperatura del local.", "Un sistema retrasa su desescarche hasta que termina el otro; una seguidora puede desescarchar mientras su cabecera continúa calentando.", system="SMMS-u"),
    variant("O.DN 01D/01E/01F", "Configuración específica de cooperación.", "SMMSU", "109-110", "Programar maestro, subordinados y cantidad.", "01F define maestro/subordinado, 01E habilita la función y 01D indica dos o tres sistemas.", system="SMMS-u", scope="outdoor"),
])
add_topic("component_checks", "compressor-inverter-checks", "Compresor e inverter VRF", "Valores útiles sin convertirlos en universales.", [
    variant("Resistencia y aislamiento", "Compresor desconectado de la PCB.", "SMMSU", "209", "Separar bobinado y derivación.", "La referencia de esa familia es 0,1–0,4 Ω entre fases y al menos 10 MΩ a chasis.", system="SMMS-u", scope="outdoor"),
    variant("Salida U-V-W", "Compresor aislado y exterior en prueba.", "SMMSU", "209", "Comprobar simetría del inverter.", "La tabla cita 240–400 V entre cada par U-V, V-W y W-U; aplique el método seguro del manual.", system="SMMS-u", scope="outdoor"),
])
add_topic("component_checks", "outdoor-fan-check", "Ventilador exterior inverter", "Bloqueo, devanado y salida de placa.", [
    variant("Devanados del motor", "Motor desconectado y giro libre.", "SMMSU", "209", "Comprobar motor antes de PCB.", "La referencia SMMS-u es 9,3–11,5 Ω entre fases.", system="SMMS-u", scope="outdoor"),
    variant("P22 y familia RAV", "Patrón D800–D805 01011.", "RAV", "85", "Confirmar que P22 es actual.", "D805 debe estar fijo; si parpadea lento se trata de la última avería guardada.", system="RAV", scope="outdoor"),
])
add_topic("component_checks", "sensors-and-pressure", "Sondas y sensores de presión", "Comparar lectura, valor físico y montaje.", [
    variant("TD/TE/TL/TS/TO", "Código F04/F06/F07/F08/F12.", "RAV", "56-59", "Elegir sensor correcto.", "Compruebe circuito abierto/corto, resistencia y si está sujeto al tubo; F15 avisa de TE/TS intercambiadas.", system="RAV"),
    variant("Pd/Ps en VRF", "F16/F23/F24 o protecciones P04/P20.", "SMMSU", "199-208", "Separar sensor y presión real.", "Compare manómetro, lectura de servicio y señal; revise también válvulas, PMV y flujo de aire.", system="SMMS-u"),
])
add_topic("component_checks", "pmv-four-way", "PMV y válvula de cuatro vías", "Pruebas térmicas y modos de servicio.", [
    variant("PMV de puertos A–E", "Multisplit con patrones 20 o sin código interior.", "MULTI", "89-91, 120", "Localizar fuga o bloqueo.", "Use el puerto indicado por el bit D800–D804 y compare respuesta térmica.", system="RAS multi"),
    variant("P19: inversión de cuatro vías", "RAV/VRF sin cambio esperado entre frío y calor.", "SMMSU", "207", "Distinguir bobina, cuerpo y sensores.", "Compruebe bobina/conector, cuerpo de válvula y coherencia de TS/TE/Pd/Ps.", system="RAV/VRF"),
])
add_topic("technical_values", "quick-electrical-values", "Valores eléctricos rápidos", "Referencias concretas con familia visible.", [
    variant("RAC serie 2–3", "SEIYA con código 04.", "SEIYA", "101-104", "Ver transmisión interior.", "15–60 V variables durante el envío, medidos con el método indicado.", system="SEIYA/RAC"),
    variant("Mando A/B", "SMMS-u con E01.", "SMMSU", "210", "Ver alimentación del mando.", "Aproximadamente 18 V CC entre A y B.", system="SMMS-u", scope="controller"),
    variant("Entrada/salida externa", "PCB interior de cassette.", "CASSETTE", "45-46", "Identificar referencia de control.", "La documentación muestra circuitos de control a 12 V CC; confirmar conector antes de medir.", system="RAV cassette", scope="indoor"),
])
add_topic("technical_values", "protection-thresholds", "Umbrales de protección documentados", "Datos útiles para interpretar la causa.", [
    variant("P20 alta presión", "SMMS-u en frío o calor.", "SMMSU", "208", "Comparar con el sensor Pd.", "Se documentan 3,85 MPa en refrigeración y 3,6 MPa en calefacción.", system="SMMS-u", scope="outdoor"),
    variant("P15 fuga por TS/TD", "Protección repetida cuatro veces.", "SMMSU", "207", "Distinguir falta de refrigerante y flujo.", "TS: 60 °C en frío o 40 °C en calor durante al menos 10 min; TD: 108 °C durante al menos 10 min.", system="SMMS-u", scope="outdoor"),
    variant("P03/P17 descarga", "TD1 o TD2.", "SMMSU", "205, 207", "Confirmar protección real.", "La tabla de códigos indica 115 °C para la condición de temperatura de descarga.", system="SMMS-u", scope="outdoor"),
])
add_topic("normal_states", "vrf-normal-display", "Estados normales del display VRF", "No sustituir piezas por una abreviatura operativa.", [
    variant("CL / Ht", "Display exterior indica modo.", "SMMSE", "display de estado", "Reconocer frío o calor.", "CL es refrigeración y Ht calefacción.", system="SMMSe/SMMS-u", scope="outdoor"),
    variant("or / dF", "El sistema cambia temporalmente actuadores.", "SMMSE", "display de estado", "Reconocer recuperación de aceite o desescarche.", "or es recuperación de aceite y dF desescarche; otras unidades pueden seguir una secuencia coordinada.", system="SMMSe/SMMS-u", scope="outdoor"),
    variant("PC / Ln / Sn", "Limitación o modo especial activo.", "SMMSE", "display de estado", "Evitar confundir baja capacidad con avería.", "PC es Peak Cut, Ln bajo ruido y Sn modo nieve.", system="SMMSe/SMMS-u", scope="outdoor"),
])
add_topic("normal_states", "normal-delays", "Retardos y postfuncionamientos normales", "Tiempos que parecen avería.", [
    variant("Retardo de tres minutos", "Compresor acaba de parar o vuelve la alimentación.", "SEIYA", "65-70", "Esperar protección de rearranque.", "El control bloquea el rearranque inmediato del compresor.", system="RAC/RAV"),
    variant("Bomba de cassette cinco minutos", "Se detuvo frío/Dry.", "CASSETTE", "38-39", "No cortar una evacuación normal.", "La bomba continúa cinco minutos después de parar la operación.", system="RAV cassette", scope="indoor"),
])
add_topic("service_tools_boards", "official-tools", "Herramientas oficiales de servicio", "Diagnóstico, selección y documentación.", [
    variant("Technical Support Tools", "Acceso profesional Toshiba Air Conditioning UK.", "TOOLS", "página oficial", "Localizar software y utilidades compatibles.", "La página oficial reúne herramientas técnicas; la compatibilidad depende de familia y generación.", system="Toshiba"),
    variant("Wave Tool / NFC", "Exterior SMMSe/SMMS-u con etiqueta NFC.", "SMMSE", "180-190", "Leer datos sin confundir un aviso 022.", "La herramienta accede a información de servicio; 022 puede aparecer temporalmente si CN800 está ocupado.", system="SMMSe/SMMS-u", scope="outdoor"),
])
add_topic("service_tools_boards", "board-replacement", "Después de cambiar una PCB", "Direcciones, capacidad y switches deben conservarse.", [
    variant("PCB interior", "L08/L09/F29 o placa nueva.", "RAV", "56-60", "Restaurar capacidad y grupo.", "Copie DN, dirección y condición cabecera/seguidora; repita adquisición.", system="RAV/VRF", scope="indoor"),
    variant("PCB exterior VRF", "F31/E31/L10/L29 después de sustitución.", "SMMSU", "199-208", "Restaurar identidad de la exterior.", "Copie switches, O.DN, dirección de línea y rol cabecera/seguidora antes de Test Run.", system="SMMS-u", scope="outdoor"),
])
add_topic("system_architecture", "recognize-toshiba-family", "Reconocer la familia antes de buscar", "La interfaz muestra rasgos observables, no obliga a introducir el modelo.", [
    variant("SEIYA/RAC", "Mando inalámbrico, bloque de dos dígitos y enlace serie 2–3.", "SEIYA", "96-104", "Usar códigos 02–27.", "La memoria se consulta recorriendo 52 códigos; no hay tabla D800–D805 en esta familia.", system="RAC"),
    variant("RAV comercial/cassette", "Mando RBC, códigos E/F/H/L/P y placa exterior de seis LED.", "RAV", "53-85", "Combinar mando y placa.", "El código de mando y los pilotos aportan capas complementarias; D805 distingue actual e histórico.", system="RAV"),
    variant("Multisplit cinco puertos", "Exterior WP-524, SW81/SW82 y D800–D805 asociados a A–E.", "MULTI", "89-91, 120", "Usar la tabla específica.", "Los patrones de PMV, sonda y tubería no son los mismos que en RAV.", system="RAS multi"),
    variant("SMMSe/SMMS-u VRF", "Varias exteriores, U1/U2/U3/U4, siete segmentos y O.DN.", "SMMSU", "199-208", "Usar subcódigos y alcance de sistema.", "La ficha indica si continúan otras unidades o se detiene toda la línea.", system="VRF"),
])


def build_topics() -> list[dict[str, Any]]:
    result, variant_id = [], 1
    for topic_id, spec in enumerate(TOPICS, start=1):
        cat = CATEGORY_BY_SLUG[spec["category"]]
        rows = []
        for sort_order, item in enumerate(spec["variants"], start=1):
            rows.append({**item, "id": variant_id, "topic_id": topic_id, "sort_order": sort_order, "visible": 1})
            variant_id += 1
        result.append({
            "id": topic_id, "brand_id": BRAND_ID, "category_id": cat["id"],
            "slug": spec["slug"], "title": spec["title"], "summary": spec["summary"],
            "active": 1, "category": cat, "variants": rows,
        })
    return result


def build_search(error_index: list[dict[str, Any]], error_details: list[dict[str, Any]], topics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    details_by_id = {row["id"]: row for row in error_details}
    entries = []
    for row in error_index:
        detail = details_by_id[row["id"]]
        parts = [row["code_display"], row["short_label"], *row["aliases"], *row["tags"]]
        for interpretation in detail["interpretations"]:
            parts.extend([interpretation["title"], interpretation["description"]])
            parts.extend(x["body"] for x in interpretation["info_items"])
            for context in interpretation["indication_contexts"]:
                parts.extend([str(context.get(key, "")) for key in ("display_location", "family_hint", "relationship", "counting_rule", "cycle_note", "sequence")])
                for led in context.get("led_indicators", []):
                    parts.extend([led.get("label", ""), led.get("color", ""), led.get("state", "")])
        entries.append({"type": "error", "id": row["id"], "code": row["code_display"], "title": row["short_label"], "subtitle": f'{row["interpretation_count"]} interpretación(es)', "haystack": normalize(" ".join(parts))})
    for topic in topics:
        for row in topic["variants"]:
            parts = [topic["title"], topic["summary"], row["title"], row["recognition"], row["purpose"], row["summary"], row["system_type"]]
            parts.extend(x["body"] for x in row["sections"])
            parts.extend(x["instruction"] + " " + (x.get("expected_result") or "") for x in row["steps"])
            for pattern in row.get("led_patterns", []):
                parts.extend([pattern.get("code_display", ""), pattern.get("relationship", ""), pattern.get("family_hint", "")])
                for led in pattern.get("led_indicators", []):
                    parts.extend([led.get("label", ""), led.get("color", ""), led.get("state", "")])
            if row["controller"]:
                parts.extend(str(value or "") for value in row["controller"].values())
            entries.append({"type": "variant", "id": row["id"], "topic_id": topic["id"], "title": row["title"], "subtitle": topic["title"], "haystack": normalize(" ".join(parts))})
    return entries


def build() -> dict[str, int]:
    if BRAND_DIR.exists():
        shutil.rmtree(BRAND_DIR)
    WEB_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    error_index, error_details = build_errors()
    topics = build_topics()
    search_entries = build_search(error_index, error_details, topics)
    write_json(WEB_DIR / "errors" / "index.json", error_index)
    for row in error_details:
        write_json(WEB_DIR / "errors" / "details" / f'{row["id"]}.json', row)
    for topic in topics:
        write_json(WEB_DIR / "topics" / f'{topic["id"]}.json', topic)
    write_json(WEB_DIR / "search.json", search_entries)
    write_json(WEB_DIR / "variant_map.json", {str(row["id"]): topic["id"] for topic in topics for row in topic["variants"]})
    by_category: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for topic in topics:
        by_category[topic["category_id"]].append({
            "id": topic["id"], "slug": topic["slug"], "title": topic["title"],
            "summary": topic["summary"], "active": 1, "variant_count": len(topic["variants"]),
        })
    categories = [{
        "id": ident, "slug": slug, "name": name, "description": description,
        "sort_order": ident * 10, "active": 1, "topics": by_category[ident],
    } for ident, slug, name, description in CATEGORIES]
    write_json(WEB_DIR / "navigation.json", {
        "metadata": {
            "schema_name": "Super Tecnico", "navigation_model": "brand_category_topic_variant",
            "schema_version": "2.3.0", "data_version": "1.0.0", "last_update_utc": now,
            "reference_brand": "Toshiba",
            "verification_warning": "Completa respecto al corpus Toshiba Referencia V1. Confirme familia, placa y lugar de lectura: los códigos y D800–D805 no son universales.",
        },
        "categories": categories,
    })
    write_json(WEB_DIR / "sources.json", [{
        "id": ident, "brand_id": BRAND_ID, "title": row["title"], "document_ref": row["document_ref"],
        "document_type": row["type"], "publication_date": row["year"], "language": "en",
        "source_url": row["source_url"], "status": "reviewed",
        "notes": "Fuente oficial Toshiba revisada para Referencia V1.",
    } for ident, row in enumerate(SOURCES.values(), start=1)])
    write_json(WEB_DIR / "coverage.json", [{
        "id": ident, "brand_id": BRAND_ID, "area_slug": slug, "area_name": name,
        "equipment_scope": "Toshiba — RAC, multisplit, RAV, cassette, SMMSe y SMMS-u",
        "coverage_status": "reference_v1", "source_count": len(SOURCES),
        "notes": description, "last_reviewed": "2026-07-29",
    } for ident, slug, name, description in CATEGORIES])
    counts = {
        "categories": len(CATEGORIES), "topics": len(topics),
        "variants": sum(len(x["variants"]) for x in topics),
        "errors": len(error_index), "search_entries": len(search_entries),
    }
    write_json(BRAND_DIR / "brand.json", {
        "slug": "toshiba", "name": "Toshiba", "display_name": "Toshiba", "enabled": True,
        "web_data": "web", "media": "media", "publish_media": False, "static_site": True,
        "schema_version": "2.3.0", "data_version": "1.0.0", "exported_at_utc": now,
        "counts": counts,
        "notes": "Toshiba Referencia V1: RAC, multisplit, RAV, cassette y VRF, con mandos, drenaje, modos de servicio, alcance operativo y tablas visuales D800–D805. Sin PDF ni capturas.",
    })
    return counts


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
