#!/usr/bin/env python3
"""Construye Midea Referencia V1 para Super Técnico.

Solo publica resúmenes técnicos trazables. Los PDF, capturas y bases maestras
no forman parte de la proyección web.
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
BRAND_DIR = ROOT / "data" / "brands" / "midea"
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
    "ATOMX": {
        "title": "Service Manual — AtomX VRF R454B 60 Hz",
        "document_ref": "SM-MIDEA-R454B-ATOMX-V2",
        "publication_date": "2024",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://hvac.midea.com/products/vrf_r454b_outdoor/651632815689797.shtml",
        "notes": "Exterior VRF R454B: menús, prueba, recuperación, monitorización, fugas y diagnóstico.",
    },
    "IDU454": {
        "title": "Service Manual — Midea VRF Indoor Units R454B",
        "document_ref": "MIDEA-VRF-IDU-R454B-V5",
        "publication_date": "2026",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://hvac.midea.com/resource/literature_RM12F1/",
        "notes": "Interiores VRF: errores, funcionamiento degradado, drenaje, sensores y fuga R454B.",
    },
    "WDC120": {
        "title": "Installation & Owner's Manual — WDC-120T2",
        "document_ref": "WDC-120T2-V1",
        "publication_date": "2026",
        "language": "en",
        "document_type": "controller_manual",
        "source_url": "https://hvac.midea.com/products/vrf_r454b_controller/651643942101061.shtml",
        "notes": "Mando cableado actual: historial, monitor de parámetros, ajustes y red.",
    },
    "INFINI": {
        "title": "Service Manual — Infini wall mounted R410A",
        "document_ref": "SM-AG11-R410A-3D-INV-220628",
        "publication_date": "2022",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://www.mideacomfort.us/downloads/SINGLE-ZONE%20U-match/2%20TON%20AND%20BELOW/Service%20Manual/WALL%20MOUNTED/INFINI%20Series%20%28SEER%2021%29/SM_AG11%28GA%29_R410A_3D%20INV_US_NA_H_220628_99-ok.pdf",
        "notes": "Split mural: códigos actuales, modo ingeniero, marcha forzada y valores.",
    },
    "HYPER": {
        "title": "Service Manual — Infini Hyper Heat wall mounted",
        "document_ref": "SM-DLFSHCH",
        "publication_date": "2021",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://www.mideacomfort.us/downloads/SINGLE-ZONE%20U-match/2%20TON%20AND%20BELOW/Service%20Manual/WALL%20MOUNTED/INFINI%20Hyper%20Heat%20Series%20%28SEER%2025%EF%BC%8CEnergy%20Star%29/DLFSHCH/Service%20Manual-DLFSHCH.pdf",
        "notes": "Split mural Hyper Heat: lógica, protecciones y diagnóstico eléctrico.",
    },
    "ONEWAY": {
        "title": "Service Manual — One-way cassette",
        "document_ref": "SM-DLFSOAH",
        "publication_date": "2022",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://www.mideacomfort.us/downloads/SINGLE-ZONE%20U-match/2%20TON%20AND%20BELOW/Service%20Manual/INCASSETTE/Service%20Manual-DLFSOAH.pdf",
        "notes": "Cassette de una vía: secuencia de bomba y boya diferenciada en frío y calor.",
    },
    "MULTI": {
        "title": "Service Manual — Multizone outdoor units",
        "document_ref": "SM-DLCMRHB",
        "publication_date": "2021",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://www.mideacomfort.us/downloads/MULTI-ZONE/Service%20Manual/ODU/Service%20Manual-DLCMRHB.pdf",
        "notes": "Multisplit: códigos, comunicación, presiones, bus DC y lógica de varias interiores.",
    },
    "HIGHE": {
        "title": "Installation Instructions — High ESP duct",
        "document_ref": "II-DLFSDAH-DLFLDAH",
        "publication_date": "2021",
        "language": "en",
        "document_type": "installation_manual",
        "source_url": "https://www.mideacomfort.us/downloads/SINGLE-ZONE%20U-match/3%20TON%20AND%20ABOVE/Installation%20Instructions/HIGH%20ESP%20DUCT/IDU/Installation%20Instructions-DLFSDAH%26%20DLFLDAH.pdf",
        "notes": "Conductos de alta presión: cableado, control, prueba y drenaje.",
    },
    "V6": {
        "title": "Installation Manual — V6 I-Series VRF 8–32 HP",
        "document_ref": "MIDEA-V6-I-SERIES-IM",
        "publication_date": "2018",
        "language": "en",
        "document_type": "installation_manual",
        "source_url": "https://mbt.midea.com/content/dam/midea-aem/mbt/hvac-goods/midea-products-category/vrfs/vrf-odu/8hp-32hp-v6-i-series-vrf-50-60hz/pdf1.pdf",
        "notes": "VRF de generación anterior: P/Q/E, direccionamiento, menús, commissioning y códigos.",
    },
    "LARGE": {
        "title": "Service Manual — R410A T3 top-discharge split",
        "document_ref": "MCAC-UTSM-201501",
        "publication_date": "2015",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://www.midea.com/content/dam/midea-aem/mx/hvac/ac-dividido/unidades-tipo-us/mta-chrn1.pdf",
        "notes": "Equipo comercial de gran potencia y generación anterior.",
    },
    "Q4": {
        "title": "Installation Manual — VRF four-way cassette",
        "document_ref": "MIDEA-VRF-Q4-CASSETTE-IM",
        "publication_date": "2016",
        "language": "en",
        "document_type": "installation_manual",
        "source_url": "https://mbt.midea.com/content/dam/midea-aem/mbt/hvac-goods/midea-products-category/vrfs/vrf-idu/four-way-cassette/pdf1.pdf",
        "notes": "Cassette VRF: P/Q/E, X1/X2, resistencia final y prueba de desagüe.",
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
    (1, "errors", "Errores y protecciones", "Códigos, estados e interpretaciones separadas por familia."),
    (2, "diagnostic_access", "Obtención de códigos y subcódigos", "Lectura desde mando, receptor, display y placa."),
    (3, "history_reset", "Historial y borrado", "Memoria del mando y de la placa exterior."),
    (4, "service_modes", "Marchas y modos de servicio", "Forzado, Test Run, desescarche y recuperación."),
    (5, "configuration", "Configuración y programación", "Menús, DIP, selectores, capacidad y prioridades."),
    (6, "controllers_buses", "Mandos y buses", "Cableado, tensiones, comunicación y puesta en marcha del mando."),
    (7, "drainage_overflow", "Drenaje y desbordamiento", "Bomba, boya y secuencias distintas en frío y calor."),
    (8, "commissioning", "Puesta en marcha", "Pruebas previas, direccionamiento y System Test."),
    (9, "multisplit", "Multisplit", "Combinaciones, conflictos y alcance de averías."),
    (10, "vrf_network", "VRF y red", "P/Q/E, HyperLink, terminación, direcciones y arquitectura."),
    (11, "refrigerant_safety", "Fugas y seguridad de refrigerante", "Detección R454B, aislamiento y recuperación."),
    (12, "component_checks", "Comprobación de componentes", "Sondas, ventiladores, EEV, presión, inverter y alimentación."),
    (13, "technical_values", "Valores técnicos y monitorización", "Tensiones, temperaturas, presión, frecuencia y curvas."),
    (14, "normal_states", "Comportamientos normales", "Desescarche, aceite, precalentamiento y esperas."),
    (15, "service_tools_boards", "Herramientas y placas", "Spot Check, modo ingeniero y trabajo tras cambiar PCB."),
]
CATEGORY_BY_SLUG = {
    slug: {"id": ident, "slug": slug, "name": name, "description": description}
    for ident, slug, name, description in CATEGORIES
}


def error_spec(
    code: str,
    title: str,
    scope: str,
    ref: str,
    page: str,
    *,
    behavior: str | None = None,
    aliases: str = "",
    restart: str = "Según la condición y la familia.",
) -> dict[str, str]:
    return {
        "code": code, "title": title, "scope": scope, "ref": ref, "page": page,
        "behavior": behavior or "La unidad afectada entra en protección mientras persista la condición.",
        "aliases": aliases, "restart": restart,
    }


def rows_from_table(
    ref: str,
    page: str,
    scope: str,
    rows: list[tuple[str, str]],
    *,
    behavior: str | None = None,
) -> list[dict[str, str]]:
    return [
        error_spec(code, title, scope, ref, page, behavior=behavior)
        for code, title in rows
    ]


ATOMX_MAIN = rows_from_table("ATOMX", "64–67", "outdoor", [
    ("A01", "Parada de emergencia"), ("A11", "Fuga R454B detectada en una interior"),
    ("A15", "Recuperar refrigerante después de fuga y parada"), ("Ad1", "Dispositivo de corte de refrigerante"),
    ("C21", "Comunicación interior–exterior"), ("C26", "Disminuyó el número de interiores detectadas"),
    ("C28", "Aumentó el número de interiores detectadas"), ("C2A", "Comunicación exterior–dispositivo de corte"),
    ("1C41", "Comunicación entre control principal y driver inverter"),
    ("E41", "Sonda de ambiente exterior T4 abierta o en corto"),
    ("EC1", "Sensor de fuga de refrigerante"), ("F41", "Sonda de batería exterior T3"),
    ("F42", "Sobretemperatura de batería exterior T3"), ("F43", "Sonda intermedia T3B"),
    ("F62", "Temperatura alta del módulo inverter"), ("F6A", "F62 repetido"),
    ("F71", "Sonda de descarga T7C1"), ("F72", "Protección de temperatura de descarga"),
    ("F75", "Sobrecalentamiento de descarga insuficiente"), ("F7A", "F72 repetido"),
    ("F81", "Sonda de aspiración Tg"), ("F91", "Sonda de tubería líquida T5"),
    ("FC1", "Sonda de salida del intercambiador TL"), ("FL1", "Sonda ambiente adicional T10"),
    ("1L--", "Código agrupador del driver de compresor"), ("1L01", "Protección repetida del compresor"),
    ("1J--", "Código agrupador del driver de ventilador"), ("1J01", "Protección repetida del ventilador"),
    ("1b01", "Bobina EEV A/D"), ("4b01", "EEV durante carga automática"),
    ("P11", "Sensor de alta presión"), ("P12", "Protección de alta presión de descarga"),
    ("P13", "Presostato de alta"), ("P14", "P12 repetido"),
    ("P21", "Sensor de baja presión"), ("P22", "Protección de baja presión de aspiración"),
    ("P23", "Presostato de baja"), ("P24", "Ascenso anormal de presión de aspiración"),
    ("P25", "P22 repetido"), ("1P32", "Corriente alta del bus DC del compresor"),
    ("1P33", "1P32 repetido"), ("P51", "Tensión AC alta"), ("P52", "Tensión AC baja"),
    ("P54", "Bus DC bajo"), ("1P56", "Bus DC bajo en módulo inverter"),
    ("1P57", "Bus DC alto en módulo inverter"), ("1P58", "Bus DC gravemente alto"),
    ("1P59", "Caída de tensión del bus"), ("P71", "EEPROM"),
    ("P91", "Realimentación PFC"), ("Pb1", "Sobrecorriente HyperLink"),
    ("pd1", "Protección anticondensación"), ("pd2", "pd1 repetido"),
])

ATOMX_INSTALL = rows_from_table("ATOMX", "65", "system", [
    ("U02", "Barrera técnica de instalación"), ("U11", "Modelo no configurado"),
    ("U12", "Capacidad no configurada"), ("U13", "Tipo de interior no válido"),
    ("U21", "Interior de plataforma anterior"), ("U31", "System Test no ejecutado"),
    ("U32", "Temperatura exterior fuera de rango para prueba"), ("U33", "Temperatura interior fuera de rango"),
    ("U34", "Temperaturas interior y exterior incompatibles"), ("U35", "Válvula de líquido cerrada"),
    ("U36", "Presión anormal durante prueba"), ("U37", "Válvula de gas cerrada"),
    ("U38", "Dirección no detectada"), ("U3A", "Señal eléctrica y circuito frigorífico no coinciden"),
    ("U3b", "Entorno anormal para la prueba"), ("U3C", "Modo automático activo"),
    ("U41", "Relación o número de interiores excedido"),
])

DRIVER_CODES = rows_from_table("ATOMX", "65–66", "outdoor", [
    ("1L1E", "Sobrecorriente hardware del compresor"), ("1L11", "Sobrecorriente software"),
    ("1L12", "Sobrecorriente en los últimos 30 s"), ("1L2E", "Temperatura alta del módulo"),
    ("1L3E", "Bus DC bajo"), ("1L31", "Bus DC alto"), ("1L32", "Bus DC gravemente alto"),
    ("1L43", "Muestreo de corriente anormal"), ("1L45", "Código de motor no coincide"),
    ("1L46", "Protección IPM"), ("1L47", "Tipo de módulo no coincide"),
    ("1L5E", "Fallo de arranque del compresor"), ("1L51", "Compresor bloqueado"),
    ("1L52", "Protección sin carga"), ("1L6E", "Pérdida de fase del motor"),
    ("1LbE", "Actuación del presostato de alta"), ("1Lb7", "Excepción de diagnóstico 908"),
    ("1J1E", "Sobrecorriente hardware del ventilador"), ("1J11", "Sobrecorriente software del ventilador"),
    ("1J12", "Sobrecorriente del ventilador en 30 s"), ("1J2E", "Temperatura alta del módulo de ventilador"),
    ("1J3E", "Bus DC bajo del ventilador"), ("1J31", "Bus DC alto del ventilador"),
    ("1J32", "Bus DC gravemente alto del ventilador"), ("1J43", "Muestreo de corriente del ventilador"),
    ("1J5E", "Fallo de arranque del ventilador"), ("1J51", "Ventilador bloqueado"),
    ("1J52", "Ventilador sin carga"), ("1J6E", "Pérdida de fase del ventilador"),
])

IDU_CODES = rows_from_table("IDU454", "34–35", "indoor", [
    ("C21", "Comunicación interior–exterior — indicación en la interior"),
    ("A51", "Avería recibida de la exterior"), ("A74", "Subunidad AHU Kit"),
    ("A81", "Autocomprobación de MS Box"), ("A82", "MS Box"),
    ("A91", "Conflicto de modo"), ("b11", "Bobina EEV 1"), ("b13", "Bobina EEV 2"),
    ("b36", "Alarma del interruptor de nivel"), ("C11", "Dirección interior duplicada"),
    ("C41", "Comunicación placa interior–driver de ventilador"),
    ("C51", "Comunicación interior–mando cableado"),
    ("C61", "Comunicación placa interior–display"), ("C71", "Comunicación AHU master–slave"),
    ("C72", "Número de AHU Kits distinto del configurado"), ("C76", "Comunicación mando principal–secundario"),
    ("C77", "Comunicación con placa de expansión 1"), ("C78", "Comunicación con placa de expansión 2"),
    ("C79", "Comunicación con módulo de conmutación"), ("d16", "Aire de entrada demasiado frío en calor"),
    ("d17", "Aire de entrada demasiado caliente en frío"), ("d43", "Vida útil del sensor de fuga"),
    ("d50", "Señal de estado de ventilador AHU"), ("E21", "Sonda de aire fresco T0"),
    ("E24", "Sonda de retorno T1"), ("E81", "Sonda de impulsión TA"),
    ("EA2", "Sensor de humedad de retorno"), ("F01", "Sonda líquida T2A"),
    ("F11", "Sonda media T2"), ("F21", "Sonda de gas T2B"),
    ("P52", "Tensión de alimentación interior demasiado baja"),
    ("P71", "EEPROM de placa principal interior"), ("P72", "EEPROM de placa de display"),
    ("P31/P34", "Sobrecorriente AC del driver de ventilador"),
    ("J01", "Motor de ventilador falló repetidamente"), ("J1E", "IPM del ventilador"),
    ("J11", "Sobrecorriente instantánea de fase"), ("J3E", "Bus DC bajo del ventilador interior"),
    ("J31", "Bus DC alto del ventilador interior"), ("J43", "Desviación de muestreo de corriente"),
    ("J45", "Motor e interior incompatibles"), ("J47", "IPM e interior incompatibles"),
    ("J5E", "Fallo de arranque del motor"), ("J52", "Motor bloqueado"),
    ("J55", "Modo de control de velocidad incorrecto"), ("J6E", "Pérdida de fase del motor"),
])

RESIDENTIAL_CODES = rows_from_table("INFINI", "141–142", "system", [
    ("EH00", "Parámetro EEPROM interior"), ("EH0A", "Parámetro EEPROM interior"),
    ("EL01", "Comunicación interior–exterior"), ("EH02", "Detección de paso por cero"),
    ("EH03", "Velocidad del ventilador interior fuera de rango"), ("EC51", "EEPROM exterior"),
    ("EC52", "Sonda de batería exterior T3"), ("EC53", "Sonda ambiente exterior T4"),
    ("EC54", "Sonda de descarga TP"), ("EC56", "Sonda de salida de evaporador T2B"),
    ("EH60", "Sonda de ambiente interior T1"), ("EH61", "Sonda media de evaporador T2"),
    ("EC07", "Velocidad del ventilador exterior fuera de rango"), ("EH0F", "Comunicación placa interior–display"),
    ("EL0C", "Detección de falta o fuga de refrigerante"), ("PC00", "IPM o sobrecorriente IGBT"),
    ("PC01", "Sobretensión o subtensión"), ("PC02", "Temperatura alta de descarga, IPM o presión"),
    ("PC03", "Protección de alta o baja presión"), ("PC04", "Driver inverter del compresor"),
    ("PC08", "Sobrecarga de corriente"), ("PC40", "Comunicación control exterior–driver"),
    ("PC0L", "Límite de funcionamiento por temperatura exterior baja"),
    ("FH0P", "Modo AP sin módulo Wi-Fi"),
])

CASSETTE_CODES = [
    error_spec("EH0E", "Alarma de nivel de agua", "indoor", "ONEWAY", "23",
               behavior="En frío se detienen ventilador y EEV tras 3 min con boya abierta; en calor la bomba intenta evacuar antes de confirmar.",
               restart="Corregir drenaje, comprobar boya/bomba y restablecer alimentación."),
]

V6_CODES = rows_from_table("V6", "25", "system", [
    ("E0", "Comunicación entre exteriores"), ("E1", "Secuencia de fases"),
    ("E2", "Comunicación interior–exterior maestra"), ("E4", "Sondas T3/T4"),
    ("E5", "Tensión de alimentación"), ("E7", "Sonda de descarga"),
    ("E8", "Dirección de exterior"), ("xE9", "EEPROM/compresor no coinciden"),
    ("xF1", "Bus DC"), ("F3", "Sonda T6B"), ("F5", "Sonda T6A"), ("F6", "EEV"),
    ("xH0", "Comunicación placa principal–driver"), ("H2", "Disminuyó el número de exteriores"),
    ("H3", "Aumentó el número de exteriores"), ("xH4", "Protección del inverter"),
    ("H5", "P2 repetido"), ("H6", "P4 repetido"), ("H7", "Número de interiores no coincide"),
    ("H8", "Sensor de alta presión"), ("H9", "P9 repetido"), ("yHd", "Avería en exterior esclava"),
    ("C7", "PL repetido"), ("P1", "Alta presión o presostato de descarga"),
    ("P2", "Baja presión"), ("xP3", "Corriente del compresor"),
    ("P4", "Temperatura de descarga"), ("P5", "Temperatura del condensador"),
    ("xP9", "Módulo de ventilador"), ("xPL", "Temperatura del módulo"),
    ("PP", "Sobrecalentamiento de descarga insuficiente"), ("xL0", "Protección del módulo inverter"),
    ("xL1", "Bus DC bajo"), ("xL2", "Bus DC alto"), ("xL4", "Error MCE"),
    ("xL5", "Fallo a velocidad cero"), ("xL7", "Secuencia de fases del compresor"),
    ("xL8", "Variación de frecuencia"), ("xL9", "Frecuencia real distinta de la objetivo"),
])

STATUS_CODES = [
    error_spec("d0x", "Retorno de aceite en curso", "system", "ATOMX", "67",
               behavior="Estado normal; x identifica el paso de la secuencia de retorno.", restart="No requiere rearme."),
    error_spec("dfx", "Desescarche en curso", "system", "ATOMX", "67",
               behavior="Estado normal; x identifica el paso de desescarche.", restart="No requiere rearme."),
    error_spec("d31", "Evaluación de carga sin resultado", "system", "ATOMX", "67",
               behavior="Estado de evaluación, no avería.", restart="No requiere rearme."),
    error_spec("d32", "Carga de refrigerante muy excesiva", "system", "ATOMX", "67"),
    error_spec("d33", "Carga de refrigerante ligeramente excesiva", "system", "ATOMX", "67"),
    error_spec("d34", "Carga de refrigerante normal", "system", "ATOMX", "67",
               behavior="Resultado normal de la evaluación.", restart="No requiere rearme."),
    error_spec("d35", "Carga de refrigerante ligeramente insuficiente", "system", "ATOMX", "67"),
    error_spec("d36", "Carga de refrigerante muy insuficiente", "system", "ATOMX", "67"),
    error_spec("d41", "Interior sin alimentación controlada por HyperLink", "system", "ATOMX", "67",
               behavior="HyperLink mantiene control de la válvula de la interior sin alimentación.", restart="Restablecer la alimentación de la interior."),
    error_spec("d0", "Retorno de aceite o precalentamiento interior", "indoor", "IDU454", "35",
               behavior="El ventilador puede parar; retorno de aceite 4–6 min y precalentamiento 10–15 min, hasta 30 min bajo −20 °C.", restart="No requiere rearme."),
    error_spec("dC", "Autolimpieza", "indoor", "IDU454", "35",
               behavior="Secuencia frío/calor/ventilación/parada durante 1–1,5 h.", restart="Finaliza sola o por cambio de modo/apagado."),
    error_spec("dd", "Conflicto de modo", "indoor", "IDU454", "35",
               behavior="La interior no atiende la demanda incompatible con la prioridad exterior.", restart="Seleccionar un modo compatible."),
    error_spec("dF", "Desescarche", "indoor", "IDU454", "35",
               behavior="Ventilador interior parado; 4–6 min, hasta unos 12 min por debajo de −20 °C.", restart="No requiere rearme."),
    error_spec("d51", "Detección inicial de presión estática", "indoor", "IDU454", "35",
               behavior="Ventilador al máximo durante 3–7 min para determinar la resistencia del conducto.", restart="No requiere rearme."),
    error_spec("d72", "Funcionamiento de respaldo exterior", "system", "IDU454", "35",
               behavior="La exterior estima virtualmente un sensor averiado durante 1–7 días; valor predeterminado 7 días.", restart="Reparar el sensor antes de que expire el respaldo."),
]

ERROR_SPECS = (
    ATOMX_MAIN + ATOMX_INSTALL + DRIVER_CODES + IDU_CODES
    + RESIDENTIAL_CODES + CASSETTE_CODES + V6_CODES + STATUS_CODES
)


def diagnostic_profile(title: str, code: str) -> tuple[list[str], list[str]]:
    text = normalize(f"{code} {title}")
    if code == "A11":
        return (
            ["Fuga real de R454B en la zona de la interior", "Detector contaminado por vapor, aceite u otra sustancia", "Detector de fugas dañado o agotado", "Entrada del detector o placa principal interior defectuosa"],
            ["Asegurar y ventilar la zona antes de tocar la máquina", "Confirmar la atmósfera con detector adecuado y localizar la interior que alarma", "Recuperar el refrigerante residual por los puntos descritos", "Reparar y comprobar estanqueidad; limpiar/validar o sustituir el detector antes de recargar"],
        )
    if code == "C21":
        return (
            ["Una o varias interiores sin alimentación", "P/Q/E o HyperLink abierto, cortocircuitado, con ruido o longitud excesiva", "Direcciones/cantidad o resistencia final incorrectas", "Placa de comunicación interior o exterior defectuosa"],
            ["Comprobar alimentación de todas las interiores", "Revisar continuidad, pantalla, topología y terminador con tensión cortada", "Comparar interiores configuradas y online mediante Spot Check", "Aislar la red por tramos antes de sustituir placas"],
        )
    if code in {"b36", "EH0E"}:
        return (
            ["Agua real por tubería obstruida, mala pendiente o exceso de altura", "Boya bloqueada o con contacto incorrecto", "Bomba de condensados bloqueada o sin alimentación", "Conector CN5/cableado o placa interior defectuosos"],
            ["Comprobar visualmente bandeja y desagüe antes de medir", "Accionar la boya y verificar su cambio de estado", "Confirmar que la bomba arranca y evacua durante la ventana de 3 o 5 minutos de la familia", "Limpiar la tubería y repetir la secuencia completa antes de rearmar"],
        )
    if code in {"C51", "C76"}:
        return (
            ["Mando o interior sin alimentación", "X1/X2 abierto, en corto o con pantalla/topología incorrecta", "Dos mandos configurados ambos como principal o ambos como secundario", "Mando, CN6 o placa interior defectuosos"],
            ["Observar si el mando completa su arranque y adquisición de 3 min 30 s", "Comprobar X1/X2, CN6 y longitud total de 200 m", "Revisar principal/secundario y topología uno-a-uno/uno-a-varios", "Probar con cable y mando conocidos antes de sustituir la placa"],
        )
    if code == "EL01":
        return (
            ["Bornes N/L2–S cruzados, flojos o abiertos", "Interior o exterior sin alimentación", "Reactor o conexión entre placas exteriores defectuosos", "Placa interior o exterior defectuosa"],
            ["Cortar alimentación dos minutos y revisar los bornes extremo a extremo", "Medir la señal DC N/L2–S con polaridad y escala correctas", "Distinguir señal alternante normal, valor fijo cercano a cero y valor siempre positivo", "Comprobar el reactor cerca de 0 Ω antes de condenar una PCB"],
        )
    if code == "PC03":
        return (
            ["Alta presión real por ventilación deficiente, suciedad, válvula cerrada o sobrecarga", "Baja presión real por falta de refrigerante, restricción, válvula cerrada o caudal interior bajo", "Presostato o cableado defectuoso", "Placa exterior defectuosa"],
            ["Medir presión real y no puentear la protección para mantener la marcha", "Con el sistema desenergizado, comprobar que el protector normal mide aproximadamente 0 Ω", "Aplicar los umbrales de 4,4 MPa y 0,13 MPa solo a esta familia", "Comprobar ventiladores, intercambiadores, válvulas y carga"],
        )
    if any(word in text for word in ("SONDA", "SENSOR", "TEMPERATURA T", "HUMEDAD")):
        return (
            ["Sensor abierto, en cortocircuito o fuera de su curva", "Conector, cableado o contacto térmico defectuoso", "Entrada analógica de la placa defectuosa"],
            ["Comparar la lectura de monitor con la temperatura o presión real", "Medir el sensor desconectado y contrastarlo con su curva", "Revisar conector, continuidad y entrada de placa"],
        )
    if any(word in text for word in ("COMUNICACION", "HYPERLINK", "DIRECCION", "NUMERO DE INTERIORES", "NUMERO DE EXTERIORES")):
        return (
            ["Unidad o dispositivo sin alimentación", "Bus abierto, cruzado, en corto o con ruido", "Dirección, cantidad o resistencia de terminación incorrectas", "Placa de comunicación defectuosa"],
            ["Anotar qué unidad muestra el código y todas las direcciones", "Comprobar alimentación y continuidad con el sistema desenergizado", "Verificar topología, direccionamiento y terminador antes de sustituir placas"],
        )
    if any(word in text for word in ("PRESION", "PRESOSTATO", "SOBRECALENTAMIENTO", "REFRIGERANTE", "FUGA", "VALVULA")):
        return (
            ["Carga o circulación de refrigerante anormal", "Válvula cerrada, restricción o EEV incorrecta", "Caudal de aire o intercambio térmico insuficiente", "Sensor/presostato o cableado defectuoso"],
            ["Confirmar que las válvulas de servicio están abiertas", "Medir presiones y temperaturas, no decidir solo por el código", "Revisar fugas, carga, ventiladores, intercambiadores y sensores"],
        )
    if any(word in text for word in ("VENTILADOR", "MOTOR", "BLOQUEADO", "PERDIDA DE FASE")):
        return (
            ["Rotor o compresor bloqueado", "Bobinado, conector U/V/W o cableado defectuoso", "Driver, IPM o placa de potencia defectuosos", "Tensión de alimentación fuera de rango"],
            ["Desconectar alimentación y comprobar giro/bobinados/aislamiento", "Comparar fases y conectores; no medir el inverter como una salida AC convencional", "Comprobar tensiones de control y driver siguiendo el diagrama de la familia"],
        )
    if any(word in text for word in ("TENSION", "BUS DC", "SOBRECORRIENTE", "IPM", "INVERTER", "PFC", "CORRIENTE", "MODULO")):
        return (
            ["Red fuera de rango o conexión floja", "Carga, motor o compresor anormales", "Rectificador, PFC, condensadores o módulo IPM defectuosos", "Refrigeración del módulo insuficiente"],
            ["Medir primero la alimentación AC y después el bus DC con procedimiento seguro", "Descargar condensadores antes de desconectar componentes", "Comprobar carga, motor/compresor, disipador y placa antes de sustituir el IPM"],
        )
    if any(word in text for word in ("EEPROM", "MODELO", "CAPACIDAD", "INCOMPATIBLE", "CONFIGUR", "CODIGO DE MOTOR")):
        return (
            ["Ajuste de modelo/capacidad incorrecto", "Placa sustituida sin reproducir selectores o parámetros", "EEPROM o PCB defectuosa"],
            ["Anotar todos los ajustes antes de cambiar la placa", "Comparar ENC/DIP y capacidad con la documentación de la unidad", "Reiniciar y repetir la comprobación; sustituir la placa solo si persiste"],
        )
    if any(word in text for word in ("NIVEL", "AGUA", "DRENAJE", "BOMBA")):
        return (
            ["Boya abierta o bloqueada", "Bomba de condensados defectuosa", "Tubo obstruido, con mala pendiente o entrada de aire", "Conector o placa interior defectuosos"],
            ["Comprobar primero si existe agua real en la bandeja", "Verificar cambio de estado de la boya y funcionamiento de la bomba", "Limpiar desagüe y repetir la secuencia completa de tres minutos"],
        )
    return (
        ["Condición indicada por el código", "Cableado, conector o ajuste incorrecto", "Placa de control defectuosa"],
        ["Confirmar familia, unidad que indica el código y momento de aparición", "Inspeccionar el elemento relacionado y su cableado", "Corregir la causa y verificar con una prueba controlada"],
    )


def operational_impact(spec: dict[str, str]) -> dict[str, Any]:
    behavior = spec["behavior"]
    value = normalize(behavior)
    if any(word in value for word in ("ESTADO NORMAL", "NO AVERIA", "NO REQUIERE REARME", "SECUENCIA")):
        level = "warning"
    elif "TODO EL SISTEMA" in value or "TODAS LAS UNIDADES" in value:
        level = "all_system"
    elif "INTERIOR AFECTADA" in value or "UNIDAD AFECTADA" in value:
        level = "affected_unit"
    else:
        level = "protected_stop"
    return {
        "stop_level": level,
        "summary": behavior,
        "affected_scope": "Alcance documentado para esta familia Midea.",
        "unaffected_scope": None,
        "restart_behavior": spec["restart"],
        "degraded_behavior": None,
        "notes": "No extrapolar este efecto a otra familia que utilice el mismo código.",
    }


def datasets_for(spec: dict[str, str], interpretation_id: int) -> list[dict[str, Any]]:
    title = normalize(spec["title"])
    points: list[dict[str, Any]] = []
    dataset_name = ""
    variable_name = "Condición"
    variable_unit = ""
    value_name = "Valor"
    value_unit = ""
    notes = ""
    if any(word in title for word in ("SONDA", "SENSOR")) and spec["ref"] in {"INFINI", "ONEWAY", "HYPER"}:
        dataset_name = "Umbrales de diagnóstico de la entrada de temperatura"
        variable_name, variable_unit = "Estado", ""
        value_name, value_unit = "Tensión de muestreo", "V"
        points = [
            {"sort_order": 1, "variable_value": "cortocircuito", "value_nominal": 0.06, "value_min": None, "value_max": 0.06, "notes": "Por debajo del umbral se detecta fallo."},
            {"sort_order": 2, "variable_value": "circuito abierto", "value_nominal": 4.94, "value_min": 4.94, "value_max": None, "notes": "Por encima del umbral se detecta fallo."},
        ]
        notes = "Umbrales de la entrada; no sustituyen la curva resistencia–temperatura de la sonda."
    elif spec["code"] == "PC03":
        dataset_name = "Umbrales de los presostatos"
        variable_name, variable_unit = "Protección", ""
        value_name, value_unit = "Presión", "MPa"
        points = [
            {"sort_order": 1, "variable_value": "alta", "value_nominal": 4.4, "value_min": 4.4, "value_max": None, "notes": "Actuación de alta en la familia cassette."},
            {"sort_order": 2, "variable_value": "baja", "value_nominal": 0.13, "value_min": None, "value_max": 0.13, "notes": "Actuación de baja en la familia cassette."},
        ]
        notes = "Aplicar solo a la familia documentada."
    elif spec["code"] in {"P51", "P52"} and spec["ref"] == "ATOMX":
        dataset_name = "Rango de alimentación AtomX"
        variable_name, variable_unit = "Red", ""
        value_name, value_unit = "Tensión", "VAC"
        points = [
            {"sort_order": 1, "variable_value": "mínimo", "value_nominal": 187, "value_min": 187, "value_max": None, "notes": "Límite inferior documentado."},
            {"sort_order": 2, "variable_value": "máximo", "value_nominal": 264, "value_min": None, "value_max": 264, "notes": "Límite superior documentado."},
        ]
        notes = "Medición L1–L2 con la unidad alimentada."
    if not points:
        return []
    return [{
        "id": interpretation_id * 10 + 1,
        "name": dataset_name,
        "dataset_type": "thresholds",
        "variable_name": variable_name,
        "variable_unit": variable_unit,
        "value_name": value_name,
        "value_unit": value_unit,
        "tolerance_text": "No aplicar a otra familia sin confirmación.",
        "source_kind": "official",
        "calculation_method": None,
        "review_status": "reviewed",
        "notes": notes,
        "visible": 1,
        "points": points,
        "sources": [source(spec["ref"], spec["page"], f"Valores — {spec['code']}")],
    }]


def behavior_override(spec: dict[str, str]) -> None:
    code, ref = spec["code"], spec["ref"]
    if code == "A01":
        spec["behavior"] = "La exterior y todas las interiores del sistema se detienen por orden de emergencia."
        spec["restart"] = "Resolver la causa y liberar la parada desde el menú [9-5]; la interior recupera tras recibir la liberación."
    elif code == "A11":
        spec["behavior"] = "La interior que detecta fuga mantiene el ventilador a máxima velocidad, cierra la EEV y activa los zumbadores; el sistema entra en seguridad."
        spec["restart"] = "Cortar y restablecer alimentación no borra el fallo; reparar la fuga y sustituir/validar el sensor según el procedimiento R454B."
    elif code in {"C21", "C26", "C28"} and ref == "ATOMX":
        spec["behavior"] = "Todas las unidades del sistema se detienen; el código se muestra en la exterior."
    elif code in {"1b01", "4b01"}:
        spec["behavior"] = "Todas las unidades se detienen si la señal de la bobina no se detecta durante dos minutos."
    elif code == "b36":
        spec["behavior"] = "La interior afectada ejecuta la lógica de bomba y, si el nivel no baja en cinco minutos, se detiene y genera la alarma."
    elif code == "EL0C":
        spec["behavior"] = "Tras tres detecciones de rendimiento frigorífico insuficiente, la unidad se apaga."
    elif code == "PC0L":
        spec["behavior"] = "En calefacción, limita la operación tras una hora por debajo de −25 °C; puede recuperar al cumplirse las condiciones de temperatura y tiempo."


def build_interpretation(interpretation_id: int, spec: dict[str, str]) -> dict[str, Any]:
    behavior_override(spec)
    causes, checks = diagnostic_profile(spec["title"], spec["code"])
    info: list[dict[str, Any]] = []
    item_id = interpretation_id * 100

    def add(item_type: str, body: str) -> None:
        nonlocal item_id
        item_id += 1
        info.append({
            "id": item_id, "item_type": item_type, "title": None, "body": body,
            "sort_order": len(info) + 1, "review_status": "reviewed",
            "origin_ref": SOURCES[spec["ref"]]["document_ref"],
        })

    add("machine_behavior", spec["behavior"])
    add("related_element", spec["title"])
    for row in causes:
        add("cause", row)
    for row in checks:
        add("check", row)
    add("observation", f"Rearme: {spec['restart']}")
    add("observation", f"Variante documentada en {SOURCES[spec['ref']]['document_ref']}; confirme familia y forma de indicación.")
    return {
        "id": interpretation_id,
        "title": spec["title"],
        "description": f"Interpretación documentada de {spec['code']} para {spec['title'].lower()}.",
        "source_kind": "official",
        "confidence": "high",
        "review_status": "reviewed",
        "info_items": info,
        "operational_impacts": [operational_impact(spec)],
        "datasets": datasets_for(spec, interpretation_id),
        "sources": [source(spec["ref"], spec["page"], f"Diagnóstico — {spec['code']}: {spec['title']}")],
        "_aliases": split_items(spec.get("aliases", "")),
        "_scope": spec["scope"],
    }


def build_errors() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for interpretation_id, original in enumerate(ERROR_SPECS, start=1):
        spec = dict(original)
        by_code[spec["code"]].append(build_interpretation(interpretation_id, spec))

    indexes: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    for error_id, code in enumerate(sorted(by_code, key=normalize), start=1):
        interpretations = by_code[code]
        scopes = {item.pop("_scope") for item in interpretations}
        scope = next(iter(scopes)) if len(scopes) == 1 else "system"
        alias_values = {code}
        for interpretation in interpretations:
            alias_values.update(interpretation.pop("_aliases"))
        aliases = [
            {"alias_display": alias, "alias_normalized": normalize(alias).replace(" ", "")}
            for alias in sorted(alias_values, key=normalize)
        ]
        short_label = interpretations[0]["title"] if len(interpretations) == 1 else f"{len(interpretations)} interpretaciones documentadas"
        search_blob = " ".join(
            [code, short_label]
            + [row["alias_display"] for row in aliases]
            + [
                " ".join([item["title"], item["description"]] + [row["body"] for row in item["info_items"]])
                for item in interpretations
            ]
        )
        index = {
            "id": error_id, "code_display": code,
            "code_normalized": normalize(code).replace(" ", ""),
            "indication_type": "display_led_or_controller", "unit_scope": scope,
            "short_label": short_label, "interpretation_count": len(interpretations),
            "search_text": normalize(search_blob),
        }
        details.append({
            **{key: value for key, value in index.items() if key not in {"interpretation_count", "search_text"}},
            "aliases": aliases,
            "tags": sorted({
                token.lower()
                for item in interpretations
                for token in normalize(item["title"] + " " + item["description"]).split()
                if len(token) >= 4
            })[:20],
            "interpretations": interpretations,
            "media": [],
        })
        indexes.append(index)
    return indexes, details


def section(section_type: str, title: str, body: str, open_by_default: bool = False) -> dict[str, Any]:
    return {
        "section_type": section_type, "title": title, "body": body,
        "collapsed_default": 0 if open_by_default else 1,
    }


def step(phase: str, number: int, instruction: str, expected: str | None = None, warning: str = "none") -> dict[str, Any]:
    return {
        "phase": phase, "step_no": number, "instruction": instruction,
        "expected_result": expected, "warning_level": warning,
    }


def option(value: str, label: str, effect: str, factory: bool = False) -> dict[str, Any]:
    return {"option_value": value, "option_label": label, "effect": effect, "is_factory": 1 if factory else 0}


def parameter(code: str, name: str, description: str, options: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "parameter_code": code, "name": name, "description": description,
        "factory_value": next((row["option_value"] for row in options if row["is_factory"]), None),
        "options": options,
    }


TOPIC_DEFS = [
    (1, "diagnostic_access", "read-codes", "Cómo obtener códigos y subcódigos", "Mando, display, LED y placa exterior."),
    (2, "history_reset", "history-reset", "Historial y borrado", "Memoria de fallos actual y de generaciones anteriores."),
    (3, "controllers_buses", "wired-controllers", "Mandos cableados Midea", "WDC-120T2, X1/X2, D1/D2 y principal/secundario."),
    (4, "controllers_buses", "controller-communication", "Comunicación del mando", "Arranque, pérdida de comunicación y aislamiento del bus."),
    (5, "service_modes", "forced-operation", "Marcha forzada y emergencia", "Variantes de split, conductos y VRF."),
    (6, "service_modes", "refrigerant-recovery", "Recuperación y equilibrio de refrigerante", "Modos de servicio de la exterior AtomX."),
    (7, "commissioning", "system-test", "System Test y Test Run", "Prueba en frío/calor y controles previos."),
    (8, "configuration", "outdoor-menu", "Menú de placa exterior", "SW, ENC y funciones configurables."),
    (9, "configuration", "priority-energy", "Prioridad, silencio y energía", "Conflictos frío/calor, Peak/Power Limit y auxiliares."),
    (10, "configuration", "indoor-settings", "Programación interior y conductos", "Presión estática, interfaz 24 V y ajustes de mando."),
    (11, "drainage_overflow", "drainage-sequences", "Bomba, boya y desbordamiento", "Frío, calor, cassette y conductos."),
    (12, "multisplit", "multizone-behavior", "Multisplit: conflictos y alcance", "Modo, comunicación, bus y efectos sobre unidades."),
    (13, "vrf_network", "vrf-buses", "VRF: P/Q/E, HyperLink y direcciones", "Topologías de dos generaciones."),
    (14, "vrf_network", "vrf-system-structure", "VRF: maestro, esclavas y cantidad de interiores", "Selectores y comprobaciones de red."),
    (15, "refrigerant_safety", "r454b-leak", "Fuga R454B y dispositivo de corte", "Detección, comportamiento y recuperación."),
    (16, "component_checks", "sensors-pressure", "Sondas y sensores de presión", "Umbrales, monitor y comparación con medida real."),
    (17, "component_checks", "fans-motors", "Ventiladores, motores y EEV", "Tensiones, señales, bobinados y bloqueo."),
    (18, "component_checks", "inverter-power", "Inverter, IPM y alimentación", "Bus DC, fuentes auxiliares y descarga segura."),
    (19, "technical_values", "monitoring", "Monitorización y valores técnicos", "Spot Check, modo ingeniero y parámetros de sistema."),
    (20, "normal_states", "normal-operation", "Estados normales que parecen avería", "Aceite, desescarche, autolimpieza y límites."),
    (21, "service_tools_boards", "after-board", "Después de sustituir una placa", "Modelo, capacidad, selectores, EEPROM y prueba."),
    (22, "errors", "error-use-rules", "Cómo interpretar códigos repetidos", "Reglas para no mezclar split, multisplit y VRF."),
    (23, "commissioning", "addressing", "Direccionamiento y reconocimiento", "Automático, manual y borrado de direcciones."),
    (24, "service_tools_boards", "field-diagnostics", "Diagnóstico de campo sin herramienta propietaria", "Displays, botones y registros disponibles en la propia máquina."),
]


def vs(
    topic: int, title: str, recognition: str, system_type: str, unit_scope: str,
    purpose: str, summary: str, details: str, procedure: str,
    ref: str, page: str, source_section: str,
    *, warning: str = "", parameters: list[dict[str, Any]] | None = None,
    monitoring: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "topic": topic, "title": title, "recognition": recognition,
        "system_type": system_type, "unit_scope": unit_scope, "purpose": purpose,
        "summary": summary, "details": details, "procedure": procedure,
        "ref": ref, "page": page, "source_section": source_section,
        "warning": warning, "parameters": parameters or [], "monitoring": monitoring or [],
    }


PRIORITY_PARAMETERS = [
    parameter("n2-0", "Prioridad de modo", "Selecciona cómo resuelve la exterior demandas incompatibles.", [
        option("0", "Automática por ambiente", "T4 decide prioridad.", True),
        option("1", "Prioridad frío", "Demandas de calor quedan Thermo-OFF."),
        option("2", "VIP/votación", "La unidad VIP o la mayoría decide."),
        option("3", "Solo calor", "No acepta demanda de frío."),
        option("4", "Solo frío", "No acepta demanda de calor."),
        option("5", "Prioridad calor", "Demandas de frío quedan Thermo-OFF."),
        option("9", "Prioridad por demanda", "Decide la demanda de capacidad."),
    ]),
    parameter("n2-1", "Modo silencioso", "Cinco niveles además de funcionamiento normal.", [
        option("0", "Normal", "Sin reducción por silencio.", True),
        option("1–5", "Silencio 1–5", "Reduce ruido/capacidad según el nivel."),
    ]),
]

V6_ADDRESS_PARAMETERS = [
    parameter("ENC1", "Dirección de exterior", "0 identifica maestra y 1/2 las esclavas.", [
        option("0", "Maestra", "Única exterior con menú completo.", True),
        option("1", "Esclava 1", "Menú limitado."),
        option("2", "Esclava 2", "Menú limitado."),
    ]),
    parameter("ENC4", "Dirección de red exterior", "Dirección de 0 a 7.", [
        option("0–7", "Dirección de red", "Cada exterior debe tener la que corresponda.", True),
    ]),
]

ATOMX_MONITOR = [
    {"code": "0/3", "name": "Dirección exterior / cantidad de interiores", "unit": "", "notes": "En espera, DSP1/DSP2 muestran ambos datos."},
    {"code": "7", "name": "Frecuencia real del compresor", "unit": "rps", "notes": "Comprobar con el sistema estabilizado."},
    {"code": "10/11", "name": "Velocidad ventiladores 1/2", "unit": "rpm", "notes": "Valor real."},
    {"code": "34", "name": "Posición EEVD", "unit": "pulsos", "notes": "Valor mostrado ×4."},
    {"code": "35/36", "name": "Alta / baja presión", "unit": "MPa", "notes": "Valor mostrado ÷100."},
    {"code": "37/38", "name": "Interiores online / en marcha", "unit": "", "notes": "Permite detectar pérdidas de red."},
    {"code": "45/46", "name": "Tensión DC / AC", "unit": "V", "notes": "Lectura de la propia placa."},
]

VARIANT_SPECS = [
    vs(1, "WDC-120T2 — código activo desde Information",
       "Mando rectangular con pantalla grande y botón Information.", "VRF R454B", "controller",
       "Leer una avería sin entrar en programación.",
       "Information abre el código activo y la dirección del dispositivo.",
       "El mando registra código, dirección y hora; anote los tres datos antes de intervenir.",
       "Con la alarma visible, pulse Information|Anote código y dirección completos|Abra la ficha de la familia R454B",
       "WDC120", "46", "Active error information"),
    vs(1, "WDC-120T2 — monitor de los dos errores más recientes",
       "Mando WDC-120T2 en menú de parámetros de servicio.", "VRF R454B", "controller",
       "Recuperar errores reciente y anterior.",
       "El monitor incluye Historical error code (recent) y (sub-recent).",
       "No equivale al registro de diez fallos con fecha/hora; son dos puntos dentro del monitor técnico.",
       "Entre en el menú técnico autorizado|Recorra los puntos hasta recent y sub-recent|Anote ambos antes de borrar",
       "WDC120", "69–74", "Parameter check and historical errors"),
    vs(1, "Split mural — modo ingeniero del mando inalámbrico",
       "Mando con botones ON/OFF, velocidad y flechas; unidad con display numérico.", "Split inverter", "controller",
       "Leer error y 20 parámetros sin desmontar.",
       "ON/OFF + velocidad durante 7 s abre códigos 0–30; el código 0 consulta el error.",
       "Los códigos 1–20 incluyen T1, T2, T3, T4, TP, frecuencias, corriente, tensión, ventiladores y EEV.",
       "Con mando desbloqueado y unidad encendida o en espera, mantenga ON/OFF + velocidad 7 s|Seleccione 0 para el error o 1–20 para parámetros|Para salir mantenga ON/OFF + velocidad 2 s",
       "INFINI", "145", "Information Inquiry & Setting"),
    vs(1, "Split/cassette — LED y display de la interior",
       "Receptor con lámparas OPERATION/TIMER y display de dos dígitos.", "Split y cassette", "indoor",
       "Distinguir estado normal, código y patrón de parpadeos.",
       "La misma avería puede aparecer como parpadeos, código alfanumérico o ambos.",
       "F, SC, CL, FP, FC, AP y CP son estados/funciones; no deben tratarse automáticamente como avería.",
       "Observe dos ciclos completos|Anote código, número de parpadeos y estado de TIMER|Compruebe primero si es un estado normal",
       "INFINI", "141–142", "Indoor error display"),
    vs(1, "AtomX — historial desde la placa exterior",
       "Placa con DSP1/DSP2 y botones MENU, UP, DOWN y OK.", "AtomX VRF", "outdoor",
       "Consultar hasta diez errores anteriores.",
       "El menú n0-0-0 consulta los diez últimos códigos y n0-0-1 limpia el historial.",
       "No limpie el historial antes de anotar código, secuencia y unidad implicada.",
       "Mantenga MENU para entrar|Seleccione n0, después 0 y finalmente 0|Recorra y anote los registros|Salga sin ejecutar n0-0-1 salvo decisión consciente",
       "ATOMX", "40–41", "History error menu"),
    vs(1, "V6 — códigos e historial en maestra y esclavas",
       "Exterior V6 con DSP1/DSP2 y botones SW3–SW6.", "V6 VRF", "outdoor",
       "Leer avería actual e historial sin confundir el menú de la esclava.",
       "La maestra tiene menú completo; las esclavas solo consulta de errores y limpieza.",
       "El prefijo x/y puede identificar compresor, ventilador o exterior esclava.",
       "Anote primero qué exterior muestra el código|Mantenga SW5 MENU 5 s|Seleccione el menú de History codes|No borre hasta registrar prefijo y dirección",
       "V6", "20–23", "Digital display and history codes"),

    vs(2, "WDC-120T2 — registro de diez fallos",
       "Mando WDC-120T2 con reloj configurado.", "VRF R454B", "controller",
       "Relacionar avería con hora y dispositivo.",
       "Conserva hasta diez entradas (10 fallos) con dirección, código y momento de aparición.",
       "Una hora incorrecta en el mando reduce la utilidad del registro; ajuste reloj y zona antes de la puesta en marcha.",
       "Abra Fault record|Recorra las diez posiciones|Copie dirección, código y hora|Borre solo después de documentar y reparar",
       "WDC120", "45–46", "Fault record"),
    vs(2, "AtomX — borrar historial n0-0-1",
       "Placa AtomX con menú de tres niveles.", "AtomX VRF", "outdoor",
       "Limpiar memoria tras la reparación.",
       "n0-0-1 elimina el historial; no libera por sí solo una parada de emergencia ni una fuga R454B.",
       "A01 se libera por [9-5]. A11 exige su procedimiento de fuga; repotenciar no la elimina.",
       "Registre los diez errores|Corrija y verifique la causa|Ejecute n0-0-1|Repita consulta para confirmar",
       "ATOMX", "41, 68–69", "Clear history versus safety reset", warning="important"),
    vs(2, "V6 — History codes y Cleaning history error",
       "Exterior V6 con SW5 MENU y SW6 OK.", "V6 VRF", "outdoor",
       "Separar consulta y borrado.",
       "Los dos menús son acciones distintas; la limpieza no repara ni libera protecciones activas.",
       "Las esclavas tienen disponible la función de consulta/limpieza aunque no el menú completo.",
       "Consulte y documente History codes|Repare la causa|Ejecute Cleaning history error|Compruebe el display normal",
       "V6", "21–23", "History and cleaning"),

    vs(3, "WDC-120T2 — X1/X2 no polarizado",
       "Mando conectado a CN6/X1/X2 de la interior.", "VRF R454B", "controller",
       "Cablear un mando a una interior.",
       "X1 y X2 pueden invertirse; la longitud total permitida es 200 m.",
       "En uno-a-uno o dos-a-uno se usa cable apantallado con pantalla a tierra; dos mandos requieren principal/secundario.",
       "Desconecte alimentación|Conecte X1/X2 con cable apantallado|Configure principal/secundario si hay dos|Alimente y espere la adquisición",
       "WDC120", "51–52", "One/two controllers to one IDU"),
    vs(3, "WDC-120T2 — uno-a-varios y dos-a-varios",
       "Mando X1/X2 y red de interiores D1/D2.", "VRF R454B", "controller",
       "Controlar hasta 16 interiores desde uno o dos mandos.",
       "La comunicación debe mantenerse 3 min 30 s antes de que el control sea operativo.",
       "En la red D1/D2 mostrada para uno-a-varios la pantalla del blindaje no se conecta a tierra; siga el esquema exacto de la variante.",
       "Confirme topología uno-a-varios o dos-a-varios|Conecte X1/X2 y D1/D2 según el esquema|Configure principal/secundario|Espere 3 min 30 s antes de diagnosticar",
       "WDC120", "52–53", "One-to-more and two-to-more"),
    vs(3, "Interfaz 24 V en conductos — limitaciones",
       "Conducto High ESP con interfaz KSAIC de termostato 24 V.", "Conductos", "indoor",
       "Entender qué mandos quedan deshabilitados.",
       "Con la interfaz 24 V, el mando inalámbrico, los KSACN y Wi-Fi quedan deshabilitados.",
       "Para programar presión estática hay que puentear temporalmente la interfaz siguiendo el procedimiento por capacidad.",
       "Corte alimentación|Identifique 9–24K o 36–58K|Aísle CN11/CN12 y derive S o S1/S2 según capacidad|Configure con KSACN|Restaure exactamente la interfaz",
       "HIGHE", "56–57", "24 V interface bypass for static pressure", warning="important"),
    vs(4, "C51 — interior no comunica con el mando",
       "Interior VRF R454B con mando cableado X1/X2.", "VRF R454B", "controller",
       "Aislar mando, cable o placa.",
       "El fallo se refiere a la comunicación interior–mando, no a la comunicación P/Q/E con la exterior.",
       "Compruebe alimentación de interior, continuidad de X1/X2, longitud y configuración principal/secundario.",
       "Anote si el mando arranca|Aísle otros mandos/accesorios|Compruebe X1/X2 y CN6|Pruebe un mando/cable conocido antes de sustituir PCB",
       "IDU454", "34", "C51 controller communication"),
    vs(4, "C76 — comunicación entre mando principal y secundario",
       "Dos WDC-120T2 gobiernan una o varias interiores.", "VRF R454B", "controller",
       "Distinguir un problema entre mandos de un C51.",
       "C76 identifica el enlace/ajuste principal–secundario.",
       "Dos mandos configurados con el mismo papel o una topología incorrecta impiden completar la adquisición.",
       "Compruebe que uno es principal y otro secundario|Revise X1/X2 y D1/D2 según topología|Reinicie ambos a la vez|Espere 3 min 30 s",
       "IDU454", "34", "C76 main-secondary controller"),
    vs(4, "EL01 — comunicación serie split por N/L2–S",
       "Split o cassette con bornes N/L2 y S.", "Split/cassette inverter", "system",
       "Orientar si falla interior, exterior o cable.",
       "La tensión DC alterna entre valores positivos y negativos cuando comunica normalmente.",
       "Valor fijo cercano a cero orienta a interior; valor siempre positivo orienta a exterior, después de descartar cableado y reactor.",
       "Corte y espere dos minutos|Revise bornes extremo a extremo|Mida DC entre N/L2 y S con la polaridad indicada|Interprete alternante/fijo/positivo y confirme placas",
       "ONEWAY", "16–17", "EL01 communication waveform", warning="danger"),
    vs(4, "Arranque del WDC-120T2 en redes múltiples",
       "Uno o dos mandos con varias interiores.", "VRF R454B", "controller",
       "Evitar diagnosticar como avería el tiempo de adquisición.",
       "La implementación del control comienza tras 3 min 30 s de comunicación estable.",
       "Durante ese intervalo, confirme alimentación y espere antes de concluir que el mando no reconoce las interiores.",
       "Alimente todas las interiores y mandos en el orden previsto|No opere durante 3 min 30 s|Compruebe cantidad de unidades adquiridas|Si no completa, revise principal/secundario y bus",
       "WDC120", "53", "Controller acquisition time"),

    vs(5, "Split mural — botón AUTO/COOL",
       "Botón manual AUTO/COOL bajo la tapa de la interior.", "Split inverter", "indoor",
       "Arrancar sin mando para prueba básica.",
       "Las pulsaciones recorren automático forzado, frío forzado y parada; la consigna forzada es 24 °C.",
       "El modo forzado no anula las protecciones de corriente, temperatura, presión ni comunicación.",
       "Abra la tapa y localice AUTO/COOL|Pulse una vez para automático forzado|Pulse de nuevo para frío forzado|Pulse otra vez para salir",
       "INFINI", "79–80", "Forced operation"),
    vs(5, "Split mural — desescarche forzado",
       "Unidad ya funcionando en frío forzado.", "Split inverter heat pump", "system",
       "Ordenar un desescarche de servicio.",
       "Mantener AUTO/COOL 5 s durante frío forzado inicia el modo; el ventilador interior para.",
       "Sale al terminar el desescarche normal o al apagar desde el mando.",
       "Entre primero en frío forzado|Mantenga AUTO/COOL 5 s|Confirme lámpara de desescarche y ventilador parado|Espere salida normal o apague",
       "INFINI", "80", "Forced defrost"),
    vs(5, "Conductos High ESP — prueba con MANUAL",
       "Interior de conductos con opción/botón MANUAL.", "Conductos", "indoor",
       "Hacer una prueba sin depender del mando.",
       "Usa consigna de fábrica 24 °C, ventilador AUTO y dirección de aire propia del modo.",
       "Al terminar hay que devolver MANUAL a OFF pulsando dos veces; no debe quedar como modo normal.",
       "Abra el acceso de la interior|Active MANUAL según la secuencia del panel|Compruebe frío/calor y desagüe|Pulse dos veces para dejar MANUAL en OFF",
       "HIGHE", "55–56", "Manual test run"),
    vs(5, "AtomX — forzar desescarche o retorno de aceite",
       "Exterior AtomX en menú n9-4.", "AtomX VRF", "outdoor",
       "Ejecutar funciones especiales de servicio.",
       "n9-4-0 fuerza desescarche y n9-4-1 fuerza retorno de aceite.",
       "La máquina conserva sus protecciones; no usar estas funciones para ocultar un error activo.",
       "Estabilice el sistema y anote parámetros|Entre en n9-4|Seleccione 0 o 1|Observe estado, presiones y salida automática",
       "ATOMX", "44", "Force defrost and oil return", warning="important"),

    vs(6, "AtomX — recuperar refrigerante hacia la exterior",
       "Exterior AtomX con menú n1-2.", "AtomX VRF R454B", "system",
       "Recoger refrigerante hacia la unidad exterior.",
       "n1-2-0 es una variante específica de recuperación hacia la exterior.",
       "No confundir con pump down de un split; el técnico debe seguir válvulas, tiempos y seguridad R454B del procedimiento completo.",
       "Confirme que la variante corresponde al sistema|Conecte equipo de recuperación adecuado|Seleccione n1-2-0|Controle presiones y termine según el manual",
       "ATOMX", "41", "Recover refrigerant to outdoor", warning="danger"),
    vs(6, "AtomX — recuperar hacia interiores o equilibrar",
       "Exterior AtomX con n1-2-1 y n1-2-2.", "AtomX VRF R454B", "system",
       "Mover o equilibrar la carga para una intervención.",
       "1 recupera hacia interiores; 2 equilibra el refrigerante del sistema.",
       "Son funciones distintas y no sustituyen la recuperación exigida después de A11.",
       "Identifique el objetivo técnico|Seleccione 1 o 2, nunca por ensayo|Vigile presión, estado de válvulas y códigos|Finalice y verifique carga",
       "ATOMX", "41", "Indoor recovery and balance", warning="danger"),
    vs(6, "A11 — recuperación residual tras una fuga R454B",
       "Sistema bloqueado en A11 con dispositivo de corte.", "AtomX VRF R454B", "system",
       "Dejar la zona segura antes de reparar.",
       "El manual ordena recuperar desde la válvula de comprobación exterior y la válvula de servicio del dispositivo de corte.",
       "Después se usa modo de vacío, se repara, se comprueba estanqueidad, se valida/cambia sensor y se recarga.",
       "Ventile y elimine fuentes de ignición|Recupere el residual por los puntos indicados|Entre en modo de vacío|Repare y pruebe estanqueidad|Evacúe, cargue y valide detector",
       "ATOMX", "69–70", "A11 residual recovery", warning="danger"),

    vs(7, "AtomX — Cooling System Test",
       "Exterior con menú n1-1-0.", "AtomX VRF", "system",
       "Probar todas las interiores en frío.",
       "Todas las interiores trabajan a 62,6 °F y ventilador alto; sale por error, a los 240 minutos o manteniendo OK 5 s.",
       "Comprueba temperaturas, válvulas, presiones y correspondencia de tubería/señal; puede generar U32–U3A.",
       "Abra todas las válvulas y confirme direcciones|Seleccione n1-1-0|Observe U32–U3A y parámetros|Mantenga OK 5 s para salir si no finaliza sola",
       "ATOMX", "47–48", "Cooling system test"),
    vs(7, "AtomX — Heating System Test",
       "Exterior con menú n1-1-1.", "AtomX VRF heat pump", "system",
       "Probar todas las interiores en calor.",
       "Todas las interiores trabajan a 86 °F y ventilador alto; conserva las protecciones.",
       "Sale por error, límite de 240 min o pulsación larga de OK.",
       "Confirme válvulas y condiciones ambientales|Seleccione n1-1-1|Compruebe respuesta de todas las interiores|Salga con OK 5 s",
       "ATOMX", "47–48", "Heating system test"),
    vs(7, "V6 — prueba del sistema completo",
       "Exterior maestra V6 con todas las interiores instaladas.", "V6 VRF", "system",
       "Detectar cableado, válvulas y longitud de tubería.",
       "La prueba arranca exteriores e interiores y comprueba error de comunicación, válvulas y estimación de tubería.",
       "Alimente 12 h antes para el calentador de cárter y abra todas las válvulas; trabajar con válvulas cerradas puede dañar el compresor.",
       "Alimente 12 h antes|Revise alimentación, direcciones, tuberías y válvulas|Inicie Test Run desde la maestra|Registre códigos y resultados",
       "V6", "23–24", "Commissioning and test run", warning="danger"),
    vs(7, "Cassette VRF — prueba real de drenaje",
       "Cassette de cuatro vías con tapón de prueba y bomba.", "VRF cassette", "indoor",
       "Comprobar desagüe antes de entregar.",
       "Se añade agua, se trabaja en frío, se para tres minutos y se fuerza el nivel hasta activar la alarma.",
       "Si el agua no baja en tres minutos la unidad se apaga; hay que cortar alimentación y vaciar antes de volver a encender.",
       "Añada agua por el punto de prueba|Arranque en frío y confirme bomba/salida|Pare y espere 3 min|Añada hasta alarma y confirme evacuación|Corte y vacíe antes de cerrar",
       "Q4", "20–21", "Drainage test", warning="important"),
    vs(7, "Equipo comercial antiguo — Trial Run sin forzar protecciones",
       "R410A T3 top-discharge con mando o controlador cableado.", "Commercial split", "system",
       "Probar un equipo de potencia anterior.",
       "El manual exige 12 h de alimentación, válvulas abiertas y prueba desde el mando.",
       "Prohíbe la operación compulsiva porque puede dejar inactiva una protección.",
       "Alimente más de 12 h|Abra todas las válvulas y revise seguridad|Ordene frío desde mando|Compruebe vibración, agua, aislamiento y fugas",
       "LARGE", "97–98", "Trial run", warning="danger"),

    vs(8, "AtomX — navegación por MENU/UP/DOWN/OK",
       "DSP1/DSP2 con botones de cuatro funciones.", "AtomX VRF", "outdoor",
       "Acceder sin cambiar por error un ajuste.",
       "n0 consulta, n1 instalación, n2 modos, n3 parámetros, n6 temperaturas y n9 funciones de servicio.",
       "Anote el valor inicial y salga con MENU; OK confirma y puede ejecutar inmediatamente una función.",
       "Mantenga MENU para entrar|Use UP/DOWN para primer nivel|Pulse OK y seleccione segundo/tercer nivel|Anote valor original antes de confirmar",
       "ATOMX", "40–44", "Menu navigation"),
    vs(8, "AtomX — ENC1 de modelo",
       "Selector rotativo ENC1 en la placa exterior.", "AtomX VRF", "outdoor",
       "Configurar la capacidad que la placa debe controlar.",
       "Las posiciones 0–5 corresponden a 18, 24, 30, 36, 48 y 60; el valor predeterminado es 0.",
       "Después de cambiar una PCB copie la posición de la placa original y confirme el modelo físico.",
       "Corte alimentación|Fotografíe el ENC1 original|Ajuste 0–5 según capacidad|Alimente y descarte U11/U12",
       "ATOMX", "45", "ENC1 model setting"),
    vs(8, "V6 — ENC1, ENC3/S12 y ENC4",
       "Exterior V6 con selectores rotativos y DIP S12.", "V6 VRF", "outdoor",
       "Definir maestra/esclavas, red y número de interiores.",
       "ENC1 0/1/2 asigna maestra/esclavas; ENC4 usa 0–7; ENC3+S12 cubren 0–63 interiores.",
       "Una cantidad o dirección incorrecta puede producir H2/H3/H7/E8 y bloquear commissioning.",
       "Corte alimentación|Asigne una sola maestra ENC1=0|Configure esclavas 1/2 y ENC4|Ajuste ENC3/S12 al número real|Reinicie y compruebe",
       "V6", "20", "ENC selectors", parameters=V6_ADDRESS_PARAMETERS),
    vs(8, "V6 — menú de placa y funciones reservadas",
       "SW3 UP, SW4 DOWN, SW5 MENU y SW6 OK.", "V6 VRF", "outdoor",
       "Acceder a debug, respaldo, historial y limitación.",
       "MENU 5 s abre n1/n2/n3/n4/nb; la maestra dispone del menú completo.",
       "No ejecute Restore factory settings ni Backup run por ensayo; registre primero todos los valores.",
       "Mantenga SW5 5 s|Seleccione nivel con SW3/SW4|Confirme con SW6|Salga con SW5 sin alterar funciones desconocidas",
       "V6", "21–23", "Menu mode"),
    vs(9, "AtomX — prioridad de frío/calor",
       "Sistema bomba de calor con demandas simultáneas incompatibles.", "AtomX VRF", "system",
       "Explicar por qué algunas interiores quedan Thermo-OFF.",
       "La prioridad puede decidirla T4, frío, calor, unidad VIP, votación o demanda.",
       "Una interior en modo contrario puede mostrar not priority sin que exista avería.",
       "Consulte n2-0|Identifique el modo solicitado por cada interior|Compare con la prioridad activa|Cambie solo si responde al diseño de la instalación",
       "ATOMX", "42, 45–46", "Mode priority", parameters=PRIORITY_PARAMETERS),
    vs(9, "AtomX — temperaturas objetivo de evaporación/condensación",
       "Menú n6 de la exterior.", "AtomX VRF", "outdoor",
       "Ajustar capacidad, consumo y comportamiento de presión.",
       "n6-0 dispone de Ke0 −3 a 11 °C; n6-2 ajusta Kc0 por niveles.",
       "Modificar objetivos altera presiones y capacidad; no usar para compensar suciedad, carga o sensores incorrectos.",
       "Registre Ke0/Kc0 actuales|Compruebe primero el estado frigorífico|Cambie un solo nivel|Vigile presiones, temperaturas y capacidad",
       "ATOMX", "43", "Evaporation and condensation targets"),
    vs(9, "AtomX — silencio y limitación",
       "Menús n2 y n9 de la exterior.", "AtomX VRF", "outdoor",
       "Distinguir una limitación programada de falta de rendimiento.",
       "Cinco niveles de silencio y las funciones de limitación reducen frecuencia, ventilador o capacidad.",
       "Antes de diagnosticar poca potencia, compruebe PC, silent/low noise, entrada seca y limitación eléctrica.",
       "Consulte modo silencioso y limitaciones|Revise entradas secas/contador|Desactive temporalmente solo con autorización|Compare frecuencia objetivo y real",
       "ATOMX", "42–44", "Silent and power limitation"),
    vs(9, "V6 — prioridad y restricciones de modo",
       "VRF V6 con demanda de varias interiores.", "V6 VRF", "system",
       "Configurar frío, calor, VIP o votación.",
       "Las opciones incluyen prioridad calor, frío, VIP/votación, solo calor, solo frío y auto.",
       "Una prioridad incorrecta se manifiesta como interiores que no arrancan aunque no exista código activo.",
       "Registre la prioridad actual|Compare con el uso del edificio|Ajuste desde la exterior maestra|Pruebe demandas opuestas",
       "V6", "20–23", "Mode priority settings"),

    vs(10, "Conductos — detección automática de presión estática",
       "Interior VRF de caudal constante o conducto High ESP.", "VRF/duct", "indoor",
       "Adaptar el ventilador a la red de conductos.",
       "d51 trabaja a máxima velocidad 3–7 min para estimar resistencia y fijar la velocidad de diseño.",
       "No interrumpa la secuencia ni la interprete como ventilador descontrolado.",
       "Abra rejillas y compuertas de diseño|Inicie/permita la detección|Espere 3–7 min|Compruebe caudal final y ausencia de d51",
       "IDU454", "35", "Initial static pressure detection"),
    vs(10, "High ESP — ajuste desde KSACN",
       "Conducto con mando cableado KSACN y parámetro de flujo.", "Conductos", "indoor",
       "Ajustar presión estática manual.",
       "Con la unidad apagada, COPY durante unos 4 s abre el ajuste; antes se equilibran las salidas en FAN ONLY.",
       "Si existe interfaz 24 V hay que derivarla temporalmente y restaurarla al terminar.",
       "Equilibre rejillas en FAN ONLY|Apague el mando|Mantenga COPY unos 4 s|Seleccione el valor de flujo/presión|Restaure interfaz y compruebe caudal",
       "HIGHE", "55–57", "Static pressure setting"),
    vs(10, "AtomX — contacto seco de control",
       "Entradas secas configurables en menú nc.", "AtomX VRF", "outdoor",
       "Entender órdenes externas que modifican la operación.",
       "El menú asigna funciones como solo frío forzado u otras órdenes de instalación.",
       "Una entrada activa puede dominar al mando; comprobarla antes de buscar averías de control.",
       "Consulte nc y su valor|Mida el estado real del contacto|Desconecte solo para prueba autorizada|Restaure cableado y función",
       "ATOMX", "44", "Dry contact functions"),

    vs(11, "Cassette de una vía — secuencia en calefacción",
       "Cassette con bomba y level switch normalmente cerrado sin agua.", "Cassette", "indoor",
       "Diagnosticar una boya que se queda abierta en calor.",
       "La bomba no funciona sin condensado; si la boya abre, arranca en unos 4 s.",
       "Si cierra antes de 3 min la bomba sigue 1 min; si sigue abierta, paran ventilador y EEV, la bomba se apaga y aparece EE.",
       "Ordene calor y observe el switch|Si abre, confirme bomba en unos 4 s|Espere hasta 3 min|Compruebe cierre, minuto adicional y código",
       "ONEWAY", "11–12", "Drain pump — heating"),
    vs(11, "Cassette de una vía — secuencia en refrigeración",
       "Cassette con bomba activa cuando arranca el compresor.", "Cassette/multizone", "indoor",
       "Distinguir comportamiento normal y desbordamiento en frío.",
       "La bomba trabaja hasta que para la exterior o la interior queda Thermo-OFF.",
       "Si la boya abre y no cierra en 3 min, paran ventilador y EEV y se detiene la bomba; se genera EE.",
       "Ordene frío y confirme bomba al arrancar compresor|Eleve la boya/controladamente|Compruebe que sigue bombeando|Si no cierra en 3 min, confirme parada y EE",
       "ONEWAY", "12", "Drain pump — cooling"),
    vs(11, "VRF R454B — alarma b36",
       "Interior con CN5 water level switch y bomba.", "VRF R454B", "indoor",
       "Seguir la detección de nivel de la generación actual.",
       "Al desconectarse/abrirse el switch, la bomba arranca; si el nivel no baja en 5 min, interior y bomba paran y aparece alarma.",
       "Si vuelve a estado normal dentro de 5 min, recupera el modo previo.",
       "Compruebe agua real y CN5|Observe arranque de bomba|Espere la ventana de 5 min|Verifique recuperación o confirmación b36",
       "IDU454", "27–28", "Water level switch control"),
    vs(11, "Cassette VRF — prueba de alarma EE",
       "Cassette de cuatro vías con tapón de prueba.", "VRF cassette", "indoor",
       "Validar boya, bomba, tubería y bloqueo.",
       "Al añadir agua hasta alarma, la bomba debe drenar inmediatamente.",
       "Si el nivel no baja en 3 min, la unidad se apaga; exige cortar alimentación y vaciar el agua antes de reiniciar.",
       "Añada agua con alimentación controlada|Confirme arranque inmediato de bomba|Espere 3 min|Corte alimentación y vacíe si no baja|Repare pendiente/obstrucción/bomba",
       "Q4", "20–21", "Overflow alarm test", warning="important"),
    vs(11, "Conductos — bomba de elevación y mantenimiento",
       "High ESP con bomba hasta 750 mm y switch de nivel.", "Conductos", "indoor",
       "Comprobar instalación y desmontaje de la bomba.",
       "Una mala pendiente o sifón puede causar daño por agua aunque la bomba funcione.",
       "Para mantenimiento se cortan todas las alimentaciones, se desconectan bomba y switch y se retiran cuatro tornillos.",
       "Pruebe cada unión con agua|Compruebe pendiente y altura|Corte todas las alimentaciones|Desconecte bomba y boya|Desmonte y limpie",
       "HIGHE", "15, 24", "Condensate lift pump"),

    vs(12, "Conflicto de modo en multisplit",
       "Varias interiores sobre una exterior bomba de calor.", "Multisplit", "system",
       "Explicar por qué una interior no trabaja.",
       "Una interior que pide modo opuesto a la exterior queda en conflicto sin que esté averiada.",
       "El código/indicador de conflicto puede aparecer sin detener las interiores cuyo modo coincide.",
       "Anote el modo de todas las interiores|Apague demandas opuestas|Seleccione un modo común|Compruebe que la unidad recupera",
       "INFINI", "142", "Indoor mode conflict"),
    vs(12, "EL01 en multisplit — localizar el tramo",
       "Exterior multizona con varias salidas/interiores.", "Multisplit", "system",
       "Determinar si la pérdida es general o de una rama.",
       "Primero se compara qué interiores comunican; una avería general orienta a exterior/alimentación y una sola a su línea o PCB.",
       "No mezcle el borne de potencia/comunicación de split con P/Q/E de VRF.",
       "Liste interiores online|Revise alimentación de cada rama|Compare señal N/L2–S|Intercambie solo pruebas autorizadas entre puertos",
       "MULTI", "31–36", "Multizone communication"),
    vs(12, "Bus DC de exteriores multizona",
       "Exterior 2–5 zonas con módulo inverter.", "Multisplit", "outdoor",
       "Comprobar la alimentación del inverter.",
       "El rango esperado depende de capacidad: 277–356 VDC en algunas 18/27K y hasta 277–410 VDC en 36/48K.",
       "Medición de alta energía; descargue condensadores y use la tabla de la capacidad exacta.",
       "Confirme capacidad y esquema|Mida AC de entrada|Mida P–N con protección adecuada|Compare con el rango de esa familia|Descargue antes de desconectar",
       "MULTI", "49–57", "DC bus diagnosis", warning="danger"),

    vs(13, "V6 — bus P/Q/E",
       "Bornero de comunicación P, Q y E en exteriores e interiores.", "V6 VRF", "network",
       "Cablear la red principal.",
       "Usa cable apantallado de tres conductores, sección mínima 0,75 mm² y hasta 1200 m.",
       "P/Q llevan comunicación y E es pantalla/tierra funcional según el esquema; no aplicar tensión de red al bornero.",
       "Corte alimentación|Tienda P/Q/E separado de potencia|Mantenga continuidad y pantalla|Compruebe longitud y sección|Alimente y verifique cantidad de interiores",
       "V6", "17–18", "P/Q/E communication network", warning="important"),
    vs(13, "AtomX — HyperLink y continuidad con una interior sin tensión",
       "Sistema R454B con comunicación HyperLink.", "AtomX VRF", "network",
       "Entender d41 y la alimentación de emergencia de la válvula.",
       "d41 indica una interior sin alimentación mientras HyperLink controla su válvula.",
       "Pb1 es sobrecorriente del enlace; bus, interiores o conexión defectuosa deben aislarse por tramos.",
       "Localice la interior sin tensión|Restablezca su alimentación|Compruebe si desaparece d41|Si aparece Pb1, aísle tramos y dispositivos",
       "ATOMX", "65, 67", "HyperLink status and overcurrent"),
    vs(13, "Cassette VRF — X1/X2, D1/D2 y P/Q/E",
       "Interior VRF con varios bornes de control.", "VRF cassette", "network",
       "No cruzar bus de mando, agrupación y red exterior.",
       "X1/X2 se usa para mando, D1/D2 para ciertos grupos y P/Q/E para comunicación de sistema.",
       "La resistencia de terminación se coloca solo donde indique el esquema, normalmente en el último nodo.",
       "Identifique cada bornero por serigrafía|Siga un solo esquema de topología|No puentee buses distintos|Compruebe terminación en el último nodo",
       "Q4", "21–23", "Controller and VRF buses"),
    vs(13, "WDC-120T2 — pantalla del cable según topología",
       "Cable apantallado entre mando e interiores.", "VRF R454B", "network",
       "Aplicar la conexión de blindaje correcta.",
       "Los esquemas uno-a-uno/dos-a-uno y uno-a-varios no muestran la misma conexión de pantalla.",
       "No use una regla universal: seleccione la figura exacta para la topología instalada.",
       "Clasifique la topología|Abra la figura correspondiente|Conecte o aísle la pantalla como indica|Compruebe comunicación tras 3 min 30 s",
       "WDC120", "51–53", "Shield connection by topology"),
    vs(14, "V6 — maestra y hasta dos esclavas",
       "Conjunto modular V6 de varias exteriores.", "V6 VRF", "outdoor",
       "Configurar jerarquía y evitar duplicidades.",
       "ENC1=0 maestra; ENC1=1 y 2 identifican esclavas.",
       "Solo la maestra ofrece menú completo; una jerarquía incorrecta produce errores de comunicación/cantidad.",
       "Desenergice todas las exteriores|Configure una sola maestra|Asigne esclavas únicas|Alimente conjuntamente y confirme cantidad",
       "V6", "20", "Master and slave outdoor units", parameters=V6_ADDRESS_PARAMETERS),
    vs(14, "V6 — cantidad de interiores 0–63",
       "ENC3 combinado con S12.", "V6 VRF", "outdoor",
       "Declarar la cantidad esperada.",
       "Las combinaciones de S12 seleccionan bloques y ENC3 completa 0–63.",
       "El valor debe coincidir con unidades realmente alimentadas y direccionadas; de lo contrario aparece H7/H2/H3.",
       "Cuente interiores instaladas y alimentadas|Ajuste S12 al bloque|Ajuste ENC3 al valor|Reinicie y compare el conteo del display",
       "V6", "20", "Indoor unit quantity"),
    vs(14, "AtomX — conteo online mediante Spot Check",
       "Exterior AtomX con UP/DOWN fuera de menú.", "AtomX VRF", "outdoor",
       "Comparar interiores configuradas, online y activas.",
       "Los puntos 3, 37 y 38 muestran cantidad configurada, online y en marcha.",
       "Una diferencia ayuda a localizar C26/C28/U41 antes de cambiar placas.",
       "Deje estabilizar más de una hora|Lea 3, 37 y 38|Compare con la instalación|Localice direcciones ausentes o adicionales",
       "ATOMX", "49–50", "System parameter check", monitoring=ATOMX_MONITOR),

    vs(15, "A11 — comportamiento automático por fuga",
       "Interior R454B con sensor de fuga y zumbador.", "VRF R454B", "system",
       "Entender qué hace la máquina antes de intervenir.",
       "La interior afectada pone ventilador a máximo, cierra EEV y mantiene alarma acústica; repotenciar no libera.",
       "Puede ser fuga real, sensor contaminado/dañado o placa; primero debe asegurarse la zona.",
       "Evacúe/ventile y elimine ignición|Localice la interior que alarma|No corte el ventilador como primera acción|Siga recuperación, reparación y validación del sensor",
       "ATOMX", "69–70", "A11 leak behavior", warning="danger"),
    vs(15, "EC1/d43 — sensor de fuga y vida útil",
       "Interior R454B sin indicios de fuga pero con código del detector.", "VRF R454B", "indoor",
       "Separar fuga, sensor defectuoso y recordatorio de vida.",
       "EC1 identifica fallo del detector; d43 es recordatorio de vida útil.",
       "Vapores, aceite u otros contaminantes pueden afectar el detector; si no recupera tras eliminar contaminación se sustituye.",
       "Compruebe primero atmósfera con equipo adecuado|Inspeccione contaminación y conexión|Respete vida útil|Sustituya y ejecute la validación prevista",
       "IDU454", "34, 38–40", "Leak sensor diagnosis", warning="danger"),
    vs(15, "Ad1/C2A — dispositivo de corte",
       "Instalación R454B con válvula/dispositivo externo de aislamiento.", "AtomX VRF R454B", "system",
       "Diagnosticar el elemento que aísla refrigerante.",
       "Ad1 es fallo del dispositivo; C2A es pérdida de comunicación con la exterior.",
       "Revise alimentación, supercondensador, válvula de bola, bus y placa antes de sustituir el conjunto.",
       "Identifique si aparece Ad1 o C2A|Compruebe alimentación y comunicación|Pruebe válvula y reserva de energía|Repita la prueba de seguridad",
       "ATOMX", "64, 137–140", "Refrigerant shut-off device"),

    vs(16, "Entradas de temperatura — 0,06 a 4,94 V",
       "Split/cassette con entrada analógica de 5 V.", "Split/cassette inverter", "system",
       "Distinguir abierto, corto y lectura plausible.",
       "Por debajo de 0,06 V o por encima de 4,94 V se confirma la avería de sensor.",
       "Una tensión dentro de rango no demuestra que la curva sea correcta; compare resistencia y temperatura real.",
       "Desconecte la sonda con tensión cortada|Mida resistencia y temperatura|Alimente y mida señal si el procedimiento lo permite|Compare con umbrales y curva",
       "ONEWAY", "21", "Temperature sensor diagnosis"),
    vs(16, "PC03 — presostatos de cassette",
       "Familia con código PC03 y presostatos cableados.", "Cassette/split inverter", "outdoor",
       "Distinguir alta y baja presión.",
       "La alta actúa sobre 4,4 MPa y la baja por debajo de 0,13 MPa en esta variante.",
       "Desconectado, un protector normal mide aproximadamente 0 Ω; confirme la presión real antes de puentear o sustituir.",
       "Revise conexión del presostato|Mida continuidad desenergizado|Mida presión real|Compruebe ventiladores, válvulas, carga y restricciones",
       "ONEWAY", "27", "High/low pressure protection", warning="danger"),
    vs(16, "AtomX — sensores Pc y Pe mediante monitor",
       "Exterior con puntos 35/36 y transductores de presión.", "AtomX VRF", "outdoor",
       "Comparar presión calculada por la placa con manómetro.",
       "El display muestra el valor dividido por 100 en MPa.",
       "Una diferencia estable entre manómetro y monitor orienta a sensor, alimentación o entrada; una diferencia real de proceso orienta al circuito.",
       "Estabilice más de una hora|Lea puntos 35/36|Conecte manómetros adecuados|Compare tendencias, no una lectura aislada",
       "ATOMX", "49–50", "Pressure monitoring", monitoring=ATOMX_MONITOR),
    vs(17, "Ventilador DC interior — seis hilos",
       "Motor con rojo, negro, blanco, amarillo y azul.", "Split/cassette/duct", "indoor",
       "Separar placa, señal y motor.",
       "Vs/Vm es 192–380 VDC; Vcc y FG 13,5–16,5 V; Vsp 0–6,5 V.",
       "Hay alta tensión incluso en espera; medir solo con puntas y protección adecuadas.",
       "Con tensión cortada compruebe giro y conector|Alimente y mida Vs/Vm y Vcc|Compruebe Vsp y FG|Si alimentaciones/orden son correctas y no gira, valore motor",
       "ONEWAY", "19–20", "Indoor DC fan signals", warning="danger"),
    vs(17, "Ventilador exterior U/V/W",
       "Motor trifásico DC con control en placa exterior.", "Split/cassette", "outdoor",
       "Comprobar el motor sin excitar el inverter.",
       "Con U/V/W desconectados, las resistencias U–V, U–W y V–W deben ser equilibradas.",
       "No meguee a través de la placa; si bobinados son equilibrados y no existe bloqueo, continúe con el driver.",
       "Descargue el bus|Desconecte U/V/W|Mida las tres resistencias y aislamiento según manual|Compare fases|Reconecte respetando orden",
       "ONEWAY", "20", "Outdoor DC fan motor"),
    vs(17, "EEV — bobina y correspondencia",
       "Códigos b11/b13/1b01/4b01.", "VRF R454B", "system",
       "Distinguir bobina, cable y salida de placa.",
       "AtomX confirma fallo si no detecta señal durante dos minutos; la variante 4b01 aparece durante carga automática.",
       "No intercambie conectores entre EEV A/D o EEV 1/2; un cruce produce código aunque ambas bobinas sean sanas.",
       "Corte alimentación|Compruebe conector y correspondencia|Mida bobinados según esquema|Accione desde prueba/monitor si está permitido|Confirme desaparición",
       "ATOMX", "70", "EEV coil diagnosis"),
    vs(18, "Split — señal de comunicación N/L2–S",
       "Borne S comparte señal pulsante y el sistema usa red de alta tensión.", "Split inverter", "system",
       "Medir sin confundir señal con alimentación.",
       "El manual documenta pulso de 24 VDC en la comunicación y 208–230 VAC en el circuito asociado de bornes.",
       "Use exactamente los puntos y polaridad del diagrama; una medición incorrecta puede destruir el multímetro o la placa.",
       "Identifique bornes y esquema|Seleccione DC para la señal indicada|Observe alternancia|Seleccione AC solo para los puntos de alimentación|Compare con la guía",
       "INFINI", "41, 141–142", "Communication and line voltage", warning="danger"),
    vs(18, "AtomX — fuentes auxiliares de placa",
       "Placa exterior con puntos +24V, +12V, +5V ISO y +3,3V.", "AtomX VRF", "outdoor",
       "Comprobar fuentes antes de condenar lógica o sensores.",
       "Rangos: 22–26 V, 10–14 V, 4,5–5,5 V y 3–3,6 V.",
       "Una fuente caída puede deberse a una carga externa en corto; desconecte por ramas siguiendo el diagrama.",
       "Mida AC L1–L2 187–264 V|Mida bus P+–N|Compruebe 24/12/5/3,3 V|Aísle cargas si una fuente está baja",
       "ATOMX", "137–138", "Main board voltage checks", warning="danger"),
    vs(18, "Split — descarga segura del bus",
       "Placa inverter con condensadores y puntos P/N.", "Split inverter", "outdoor",
       "Verificar que el bus está descargado antes de manipular.",
       "El manual considera descargado al medir menos de 36 V entre P y N; si no se puede medir, espera al menos 5 min.",
       "La espera no sustituye la medición cuando el diseño permite medir; use resistencias/descarga previstas por el fabricante.",
       "Corte y bloquee alimentación|Espere el tiempo mínimo|Mida P–N en DC|No desconecte hasta estar por debajo de 36 V",
       "INFINI", "140", "Capacitor discharge", warning="danger"),
    vs(18, "Multizone — rango de bus según capacidad",
       "Exterior 18–48K con bus P/N.", "Multisplit", "outdoor",
       "Evitar aplicar un único valor a todas las máquinas.",
       "Las tablas separan 277–356 VDC y 277–410 VDC según combinación/capacidad.",
       "Confirme modelo de la placa aunque la aplicación no lo muestre como filtro; el rango es una pista de variante.",
       "Identifique capacidad y número de zonas|Busque la variante de rango|Mida red y después P/N|Compare bajo la misma condición de marcha",
       "MULTI", "49–57", "DC bus ranges", warning="danger"),

    vs(19, "AtomX — System Parameter Check",
       "UP/DOWN fuera del menú, después de una hora de funcionamiento estable.", "AtomX VRF", "outdoor",
       "Leer estado completo sin herramienta externa.",
       "Incluye frecuencias, T2/T2B/T3/T4, ventiladores, EEV, presiones, tensiones y cantidades de interiores.",
       "Las presiones se dividen por 100 y la posición EEV se multiplica por 4.",
       "Deje trabajar más de una hora|Pulse UP/DOWN fuera de menú|Registre código de punto y valor|Convierta unidades antes de comparar",
       "ATOMX", "49–50", "System parameter check", monitoring=ATOMX_MONITOR),
    vs(19, "Split mural — 20 puntos desde el mando",
       "Mando inalámbrico con modo ingeniero.", "Split inverter", "controller",
       "Consultar temperaturas y actuadores.",
       "Puntos 1–20: T1, T2, T3, T4, TP, frecuencia objetivo/real, corriente, AC, estado de capacidad, ventilador, EEV, humedad y consigna compensada.",
       "Ventilador y EEV se muestran como valor ×8.",
       "Entre con ON/OFF + velocidad 7 s|Recorra 1–20|Anote código, valor y estado de marcha|Salga con combinación 2 s",
       "INFINI", "144–145", "Engineer parameter query"),
    vs(19, "WDC-120T2 — monitor del sistema",
       "Mando actual con menú de monitorización.", "VRF R454B", "controller",
       "Leer parámetros de interior y exterior desde la sala.",
       "Incluye temperaturas, sobrecalentamiento objetivo, EEV, software y dos errores históricos.",
       "Un guion indica dato no disponible, no necesariamente avería.",
       "Abra Monitor/Check|Seleccione unidad/dirección|Recorra parámetros|Anote unidades y guiones|Compare con Spot Check exterior",
       "WDC120", "69–74", "Monitor parameters"),
    vs(19, "V6 — UP/DOWN después de estabilizar",
       "Exterior V6 fuera de menú.", "V6 VRF", "outdoor",
       "Consultar 45 parámetros del sistema.",
       "El manual pide más de una hora de funcionamiento estable antes de usar la lista.",
       "Incluye temperaturas T3/T6A/T6B, EEV, frecuencia, capacidad, corriente, tensión y versiones.",
       "Estabilice más de una hora|Pulse SW3/SW4 fuera de menú|Registre índice y valor|Compare unidades y estado de marcha",
       "V6", "22", "UP/DOWN system check"),
    vs(20, "d0 — retorno de aceite o precalentamiento",
       "Interior R454B mostrando d0.", "VRF R454B", "indoor",
       "Evitar diagnosticar ventilador parado como avería.",
       "Retorno de aceite dura 4–6 min; precalentamiento 10–15 min y hasta 30 min por debajo de −20 °C.",
       "Durante retorno en calor puede cambiar a frío con ventilador parado o al mínimo.",
       "Observe código y temperatura exterior|Espere el tiempo documentado|Compruebe que vuelve al modo anterior|Investigue solo si supera el tiempo",
       "IDU454", "35", "Oil return and preheating"),
    vs(20, "dF — desescarche",
       "Interior en calor con dF y ventilador parado.", "VRF R454B", "indoor",
       "Distinguir desescarche normal.",
       "Suele durar 4–6 min y puede acercarse a 12 min por debajo de −20 °C.",
       "Después puede mantenerse prevención de aire frío antes de arrancar ventilador.",
       "Confirme dF y modo calor|Observe exterior y drenaje|Espere hasta 12 min en frío extremo|Verifique retorno a calor",
       "IDU454", "35", "Defrost status"),
    vs(20, "dC — autolimpieza de 1 a 1,5 h",
       "Interior mostrando dC.", "VRF R454B", "indoor",
       "Explicar cambios de modo y falta de respuesta.",
       "Secuencia frío, calor, ventilación y parada; no permite ajustar ventilador ni temporizadores.",
       "Finaliza sola o se cancela con cambio de modo/apagado y recupera el modo previo.",
       "Confirme que el usuario inició autolimpieza|No interrumpa salvo necesidad|Espere 1–1,5 h|Compruebe recuperación del modo previo",
       "IDU454", "35", "Self-cleaning status"),
    vs(20, "PC0L — límite por frío exterior",
       "Cassette/split Hyper Heat en calefacción extrema.", "Split/cassette", "system",
       "Distinguir límite de aplicación de avería frigorífica.",
       "Aparece tras una hora por debajo de −25 °C.",
       "Recupera con combinaciones temporizadas: más de −22 °C durante 10 min con compresor parado una hora, o más de −5 °C durante 10 min.",
       "Registre T4 y tiempo|No cambie componentes por el código aislado|Espere condición de recuperación|Compruebe que el código desaparece",
       "ONEWAY", "14", "Low ambient operating limit"),
    vs(20, "Retardo de tres minutos y prevención de aire frío",
       "Equipo comercial que no arranca inmediatamente.", "Commercial split", "system",
       "Evitar confundir protección normal con fallo.",
       "El compresor puede esperar tres minutos; en calefacción el ventilador interior espera a que la batería se caliente.",
       "Run y Defrost/Preheat encendidos pueden indicar una espera normal.",
       "Observe indicadores|Espere al menos 3 min|Compruebe temperaturas de batería|Investigue solo si no sale de la espera",
       "LARGE", "101–103", "Normal delay and preheat"),
    vs(21, "AtomX — reproducir ENC1 y ajustes",
       "Sustitución de placa exterior.", "AtomX VRF", "outdoor",
       "Evitar U11/U12 y combinaciones incorrectas.",
       "La placa nueva debe recibir modelo/capacidad y ajustes de campo de la original.",
       "No copie una posición si la placa anterior era de otra capacidad; contraste con placa de características.",
       "Fotografíe ENC y menús antes de retirar|Monte placa compatible|Reproduzca modelo/capacidad|Revise fuentes|Ejecute System Test",
       "ATOMX", "40–45, 64–67", "Board replacement settings"),
    vs(21, "Split — EEPROM interior/exterior",
       "EH00/EH0A o EC51 después de reiniciar.", "Split/cassette", "system",
       "Decidir entre reinicio y PCB.",
       "El chip principal no recibe respuesta válida de EEPROM.",
       "Algunas exteriores no permiten cambiar solo la PCB y exigen el cuadro eléctrico completo.",
       "Corte alimentación 2 min|Revise conectores y versión de placa|Reinicie|Si reaparece, sustituya la unidad de placa permitida por el fabricante",
       "ONEWAY", "15", "EEPROM diagnosis"),
    vs(21, "V6 — restaurar selectores y jerarquía",
       "Cambio de placa en un conjunto de exteriores.", "V6 VRF", "outdoor",
       "Recuperar dirección y cantidad.",
       "ENC1, ENC3/S12 y ENC4 deben volver a su valor; una sola exterior debe quedar maestra.",
       "Restore factory settings no reconstruye automáticamente el diseño de red.",
       "Registre selectores de todas las exteriores|Cambie la placa|Reponga ENC/S12|Alimente conjuntamente|Repita direccionamiento y commissioning",
       "V6", "20–24", "Board replacement and commissioning"),
    vs(22, "Un mismo código cambia entre familias",
       "Búsqueda por P5, E0, E1, E4, P1 o códigos con prefijo x.", "Midea", "system",
       "Usar correctamente las interpretaciones múltiples.",
       "P5 puede ser temperatura de condensador en V6; en otra familia P5/EE puede relacionarse con drenaje.",
       "Confirme quién muestra el código, refrigerante, arquitectura y forma exacta antes de abrir una interpretación.",
       "Anote código respetando letras/prefijos|Identifique interior/exterior/mando|Elija split, multizona, V6 o AtomX|Compare descripción y comportamiento",
       "V6", "25", "Repeated code rules"),
    vs(22, "Prefijos x/y y mayúsculas",
       "Código xH4, xP3, xL0 o yHd en VRF.", "V6 VRF", "outdoor",
       "No perder la identidad del compresor o exterior.",
       "x/y son marcadores de posición de módulo/unidad, no una letra opcional.",
       "PC40 no equivale a P40; EC1 no equivale a C1; registre exactamente lo mostrado.",
       "Fotografíe el display|Anote alternancia y prefijo|Busque código completo|Use el alias corto solo como apoyo",
       "V6", "25", "Code prefixes"),
    vs(23, "V6 — direccionamiento automático, manual y borrado",
       "DIP S8 en exterior V6.", "V6 VRF", "network",
       "Elegir el método de direcciones interiores.",
       "El selector contempla automático (predeterminado), manual y limpieza de direcciones.",
       "Después de borrar, todas las interiores deben estar alimentadas y comunicando antes de repetir adquisición.",
       "Registre direcciones existentes|Seleccione automático, manual o borrar según el diseño|Alimente todos los nodos|Compruebe H7/E8 y cantidad",
       "V6", "20", "Indoor addressing"),
    vs(23, "AtomX — dirección VIP y conteo de interiores",
       "Menú n1-6 y Spot Check.", "AtomX VRF", "network",
       "Configurar la interior que decide prioridad.",
       "n1-6 fija la dirección VIP; el valor predeterminado es 63.",
       "Una VIP inexistente cambia la lógica de prioridad; compare dirección con la lista online.",
       "Consulte direcciones online|Seleccione n1-6|Introduzca la VIP real|Pruebe demandas de frío/calor",
       "ATOMX", "41, 45–46", "VIP IDU address"),
    vs(24, "Diagnóstico integrado AtomX",
       "Exterior con dos displays y cuatro botones.", "AtomX VRF", "outdoor",
       "Aprovechar historial, monitor y pruebas sin portátil.",
       "La placa reúne últimos diez errores, 50+ parámetros, pruebas frío/calor, recuperación y ajustes.",
       "Use el orden: registrar historial, leer estado, comprobar instalación y solo después ejecutar funciones.",
       "Consulte n0-0-0|Registre Spot Check|Compare cantidades y presiones|Ejecute System Test si es seguro|Guarde resultados",
       "ATOMX", "40–50", "Integrated field diagnostics", monitoring=ATOMX_MONITOR),
    vs(24, "Diagnóstico integrado del mando split",
       "Mando inalámbrico con combinación de modo ingeniero.", "Split inverter", "controller",
       "Obtener datos sin abrir la exterior.",
       "Permite ver error, cinco temperaturas, frecuencia objetivo/real, corriente, AC, ventiladores y EEV.",
       "Los datos son los que calcula la placa; contraste valores críticos con instrumentos.",
       "Entre en modo ingeniero|Registre puntos 0–20 bajo la misma condición|Compare objetivo/real|Confirme con mediciones físicas",
       "INFINI", "144–145", "Remote engineer diagnostics"),
]


def build_topics() -> list[dict[str, Any]]:
    topics: dict[int, dict[str, Any]] = {}
    for topic_id, category_slug, slug, title, summary in TOPIC_DEFS:
        category = CATEGORY_BY_SLUG[category_slug]
        topics[topic_id] = {
            "id": topic_id, "brand_id": BRAND_ID, "category_id": category["id"],
            "slug": slug, "title": title, "summary": summary, "active": 1,
            "category": category, "variants": [],
        }

    for variant_id, spec in enumerate(VARIANT_SPECS, start=1):
        steps = []
        for index, instruction in enumerate(split_items(spec["procedure"]), start=1):
            phase = "prepare" if index == 1 else "procedure"
            if index == len(split_items(spec["procedure"])):
                phase = "verify"
            steps.append(step(phase, index, instruction, warning="danger" if spec["warning"] == "danger" else "none"))
        sections = [
            section("recognition", "Cómo reconocer esta variante", spec["recognition"], True),
            section("technical", "Qué hace o tiene en cuenta la máquina", spec["details"]),
        ]
        if spec["warning"]:
            sections.append(section("warning", "Advertencia", (
                "Procedimiento con riesgo eléctrico, mecánico o frigorífico; debe realizarlo personal cualificado."
                if spec["warning"] == "danger"
                else "Registre el estado inicial y no cambie ajustes sin comprender su efecto."
            )))
        topics[spec["topic"]]["variants"].append({
            "id": variant_id, "topic_id": spec["topic"], "title": spec["title"],
            "recognition": spec["recognition"], "system_type": spec["system_type"],
            "unit_scope": spec["unit_scope"], "refrigerant": "R454B" if "R454B" in spec["system_type"] else None,
            "purpose": spec["purpose"], "summary": spec["summary"],
            "source_kind": "official", "review_status": "reviewed",
            "sort_order": variant_id, "visible": 1, "sections": sections, "steps": steps,
            "parameters": spec["parameters"], "controller": None,
            "monitoring_points": spec["monitoring"], "media": [],
            "sources": [source(spec["ref"], spec["page"], spec["source_section"])],
        })
    return list(topics.values())


def synonyms(value: str) -> str:
    replacements = {
        "WATER LEVEL": "BOYA FLOTADOR NIVEL AGUA DRENAJE",
        "INTERRUPTOR DE NIVEL": "BOYA FLOTADOR WATER LEVEL",
        "RECUPERAR REFRIGERANTE": "PUMP DOWN RECOGIDA REFRIGERANTE",
        "RECUPERACION": "PUMP DOWN RECOGIDA",
        "MANDO CABLEADO": "WIRED CONTROLLER CONTROL REMOTO",
        "PRESION ESTATICA": "ESP CONDUCTOS CAUDAL",
        "COMUNICACION": "BUS DATOS TRANSMISION",
        "RETORNO DE ACEITE": "OIL RETURN",
        "DESESCARCHE": "DEFROST",
        "FUGA": "LEAK REFRIGERANT LEAKAGE",
        "PRUEBA": "TEST RUN SYSTEM TEST COMMISSIONING",
        "MARCHA FORZADA": "FORCED COOLING MANUAL AUTO",
        "HISTORIAL": "HISTORY ERROR RECORD",
        "SILENCIO": "SILENT LOW NOISE",
        "LIMITACION": "PEAK CUT POWER LIMIT",
    }
    upper = normalize(value)
    additions = [replacement for term, replacement in replacements.items() if term in upper]
    return f"{value} {' '.join(additions)}"


def build_search(
    topics: list[dict[str, Any]],
    error_indexes: list[dict[str, Any]],
    error_details: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for topic in topics:
        category = topic["category"]
        for item in topic["variants"]:
            parameter_text = " ".join(
                " ".join([
                    str(row.get("parameter_code") or ""), str(row.get("name") or ""),
                    str(row.get("description") or ""),
                    " ".join(
                        " ".join([
                            str(opt.get("option_value") or ""), str(opt.get("option_label") or ""),
                            str(opt.get("effect") or ""),
                        ])
                        for opt in row.get("options", [])
                    ),
                ])
                for row in item.get("parameters", [])
            )
            monitoring_text = " ".join(
                " ".join(str(value or "") for value in row.values())
                for row in item.get("monitoring_points", [])
            )
            body = " ".join([
                item["title"], item.get("recognition") or "", item.get("purpose") or "",
                item.get("summary") or "",
                " ".join(row.get("body") or "" for row in item.get("sections", [])),
                " ".join(
                    " ".join([row.get("instruction") or "", row.get("expected_result") or ""])
                    for row in item.get("steps", [])
                ),
                parameter_text, monitoring_text, category["name"], topic["title"],
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
        body = " ".join(
            [index["search_text"]]
            + [
                " ".join(
                    [row["title"], row["description"]]
                    + [info["body"] for info in row["info_items"]]
                    + [
                        " ".join([
                            dataset["name"], dataset.get("notes") or "",
                            " ".join(
                                f"{point.get('variable_value')} {point.get('value_nominal')}"
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
            "type": "error", "id": index["id"], "topic_id": None,
            "category_slug": "errors", "category": CATEGORY_BY_SLUG["errors"]["name"],
            "title": f"{index['code_display']} — {index['short_label']}",
            "summary": detail["interpretations"][0]["description"],
            "haystack": normalize(synonyms(body)),
        })
    return entries


def main() -> int:
    expected_root = (ROOT / "data" / "brands" / "midea").resolve()
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
            "id": topic["id"], "slug": topic["slug"], "title": topic["title"],
            "summary": topic["summary"], "active": 1,
            "variant_count": len(topic["variants"]),
        })
        for item in topic["variants"]:
            variant_map[str(item["id"])] = topic["id"]
        write_json(WEB_DIR / "topics" / f"{topic['id']}.json", topic)

    navigation_categories = []
    for sort_order, (category_id, slug, name, description) in enumerate(CATEGORIES, start=1):
        navigation_categories.append({
            "id": category_id, "slug": slug, "name": name, "description": description,
            "sort_order": sort_order * 10, "active": 1,
            "topics": topics_by_category.get(slug, []),
        })

    for detail in error_details:
        write_json(WEB_DIR / "errors" / "details" / f"{detail['id']}.json", detail)
    write_json(WEB_DIR / "errors" / "index.json", error_indexes)
    write_json(WEB_DIR / "search.json", search_entries)
    write_json(WEB_DIR / "variant_map.json", variant_map)

    source_rows = [
        {
            "id": source_id, "title": row["title"], "document_ref": row["document_ref"],
            "publication_date": row["publication_date"], "language": row["language"],
            "document_type": row["document_type"], "source_url": row["source_url"],
            "status": "reviewed", "notes": row["notes"],
        }
        for source_id, row in enumerate(SOURCES.values(), start=1)
    ]
    write_json(WEB_DIR / "sources.json", source_rows)

    coverage_notes = {
        "errors": "AtomX R454B, interiores R454B, V6, split, cassette y multisplit con interpretaciones separadas.",
        "diagnostic_access": "WDC-120T2, modo ingeniero inalámbrico, LED/display y placas AtomX/V6.",
        "history_reset": "Diez fallos con fecha/hora, dos históricos de monitor y memorias de placa.",
        "service_modes": "AUTO/COOL, desescarche, System Test y recuperación/equilibrado AtomX.",
        "configuration": "Prioridades, silencio, temperaturas objetivo, contactos, ENC y presión estática.",
        "controllers_buses": "X1/X2, D1/D2, 24 V, adquisición 3 min 30 s y comunicaciones C51/C76/EL01.",
        "drainage_overflow": "Secuencias diferenciadas frío/calor, b36 a 5 min y cassette EE a 3 min.",
        "commissioning": "AtomX frío/calor, V6, cassette, conductos y comercial antiguo.",
        "multisplit": "Conflicto de modo, comunicación por ramas y bus DC por capacidad.",
        "vrf_network": "P/Q/E, HyperLink, maestro/esclavas, cantidad 0–63 y dirección VIP.",
        "refrigerant_safety": "A11, EC1/d43, Ad1/C2A, recuperación y rearme no eliminable por repotenciación.",
        "component_checks": "Sondas, presión, ventiladores, EEV, inverter y fuentes auxiliares.",
        "technical_values": "Spot Check AtomX, 45 puntos V6, 20 puntos de mando y monitor WDC.",
        "normal_states": "Aceite, precalentamiento, dF, dC, d51, d72, PC0L y retardo de tres minutos.",
        "service_tools_boards": "Diagnóstico integrado y restauración de ENC/DIP/EEPROM tras sustituir placas.",
    }
    coverage = [
        {
            "id": category_id, "brand_id": BRAND_ID, "area_slug": slug,
            "area_name": name, "equipment_scope": "Midea — corpus Referencia V1",
            "coverage_status": "reference_v1", "source_count": len(SOURCES),
            "notes": coverage_notes[slug], "last_reviewed": now[:10],
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
    write_json(WEB_DIR / "navigation.json", {
        "metadata": {
            "schema_name": "Super Tecnico",
            "navigation_model": "brand_category_topic_variant",
            "schema_version": "2.2.0", "data_version": "1.0.0",
            "last_update_utc": now, "reference_brand": "Midea",
            "verification_warning": (
                "Completa respecto al corpus Midea Referencia V1. Confirme siempre "
                "familia, refrigerante, unidad que muestra el código y forma de indicación."
            ),
        },
        "categories": navigation_categories,
    })

    brand = {
        "slug": "midea", "name": "Midea", "display_name": "Midea",
        "enabled": True, "web_data": "web", "media": "media",
        "publish_media": False, "static_site": True,
        "schema_version": "2.2.0", "data_version": "1.0.0",
        "exported_at_utc": now, "counts": counts,
        "notes": (
            "Midea Referencia V1: AtomX R454B, interiores VRF R454B, WDC-120T2, "
            "V6, split, cassette, conductos, multisplit y comercial anterior. Sin PDFs ni capturas."
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
