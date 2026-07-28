#!/usr/bin/env python3
"""Construye Haier Referencia V1 para Super Técnico.

La salida pública contiene resúmenes técnicos trazables a manuales oficiales.
No copia PDF, capturas, bases privadas ni ilustraciones de los manuales.
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
BRAND_DIR = ROOT / "data" / "brands" / "haier"
WEB_DIR = BRAND_DIR / "web"
BRAND_ID = 8


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
    "ADVPLUS": {
        "title": "Advanced Plus Series Service Manual",
        "document_ref": "HAIER-ADVANCED-PLUS-SM",
        "publication_date": "s. f.",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://www.haierappliances.com/content/downloads/ductless/Advanced-Plus-Series/Haier-Advanced_Plus_Service_Manual.pdf",
        "notes": "Single Zone: códigos E/F, LED exterior, comunicación, inverter, ventiladores, EEV y valores eléctricos.",
    },
    "ARCTIC": {
        "title": "Arctic Multi Series Service Guide",
        "document_ref": "HAIER-ARCTIC-MULTI-SG-20210508",
        "publication_date": "2021",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://www.haierappliances.com/content/downloads/ductless/Arctic-Multi-Series/Arctic-Multi-Service-Guide-REVISION-20210508.pdf",
        "notes": "Multisplit, cassette y conductos: drenaje, sensores 10K/23K/50K, comunicación, DIP y funciones de servicio.",
    },
    "FLEXMULTI": {
        "title": "FlexFit Multi Series Service Manual",
        "document_ref": "HAIER-GE-MULTI-SM-20220411",
        "publication_date": "2022",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://www.haierappliances.com/content/downloads/ductless/FlexFit-Multi-Series/Haier_GE_Multi_Service_Manual_4.11.22.pdf",
        "notes": "Multisplit: autocomprobación, códigos numéricos exteriores, puertos, comunicación, EEV y valores de motores.",
    },
    "FLEXPRO": {
        "title": "FlexFit Pro Series Service Manual",
        "document_ref": "HAIER-FLEXFIT-PRO-SM-20210508",
        "publication_date": "2021",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://www.haierappliances.com/content/downloads/ductless/Flexfit-Pro-Series/Haier-Flexfit-Pro-Service-Manual-20210508.pdf",
        "notes": "Comercial, cassette y conductos: códigos interior/exterior, boya, bomba, presión estática, DIP y mandos.",
    },
    "MRVODU": {
        "title": "MRV-S Outdoor Unit Service Manual",
        "document_ref": "HAIER-MRV-S-ODU-SM",
        "publication_date": "s. f.",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://www.haierappliances.com/content/downloads/ductless/MRV-S-Series/Haier-MRV-S-Outdoor-Service-Manual.pdf",
        "notes": "VRF MRV-S: red, direccionamiento, Trial Operation, monitor, estados, subcódigos y respuesta de la máquina.",
    },
    "MRVCAS": {
        "title": "MRV-S Compact Cassette Service Manual",
        "document_ref": "HAIER-MRV-S-COMPACT-CASSETTE-SM",
        "publication_date": "s. f.",
        "language": "en",
        "document_type": "service_manual",
        "source_url": "https://www.haierappliances.com/content/downloads/ductless/MRV-S-Series/Haier-Compact-Cassette-Service-Manual.pdf",
        "notes": "Cassette MRV-S: códigos interiores, bomba, boya, mando A/B/C, direccionamiento y prueba LL/HH.",
    },
    "YRE17": {
        "title": "YR-E17 Wired Controller Manual",
        "document_ref": "HAIER-YR-E17-CONTROLLER",
        "publication_date": "s. f.",
        "language": "en",
        "document_type": "controller_manual",
        "source_url": "https://www.haierappliances.com/content/downloads/ductless/Controller/Haier-Controller-YR-E17-Manual.pdf",
        "notes": "Mando cableado de tres hilos: errores en hexadecimal, historial, parámetros, direcciones, presión estática y LL/HH.",
    },
    "YRE16B": {
        "title": "YR-E16B Wired Controller Manual",
        "document_ref": "49-5000680-REV0",
        "publication_date": "2022",
        "language": "en",
        "document_type": "controller_manual",
        "source_url": "https://www.haierappliances.com/content/downloads/ductless/Controller/Haier_YRE-16B_Manual_5.18.22.pdf",
        "notes": "Mando cableado con menú: código actual, hasta 35 históricos por unidad, ajustes de servicio y red de tres hilos.",
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
    (1, "errors", "Errores y protecciones", "Códigos de unidades, mandos y placas, con equivalencias entre puntos de indicación."),
    (2, "diagnostic_access", "Obtención de códigos y subcódigos", "Métodos desde display, LED, YR-E17, YR-E16B y placa MRV."),
    (3, "history_reset", "Historial y borrado", "Consulta, conservación y borrado de registros por unidad o grupo."),
    (4, "service_modes", "Modos de servicio", "Marcha forzada, LL/HH, autocomprobación, desescarche y emergencia."),
    (5, "configuration", "Configuración y programación", "DIP, presión estática, direcciones, prioridad, ruido y ajustes de placa."),
    (6, "controllers_buses", "Mandos y buses", "YR-E17/YR-E16B, tres hilos polarizados, grupos y comunicación."),
    (7, "drainage_overflow", "Drenaje y desbordamiento", "Secuencias completas de bomba y boya en frío, calor y espera."),
    (8, "commissioning", "Puesta en marcha", "Autocomprobación, Trial Operation y comprobaciones previas."),
    (9, "multisplit", "Multisplit y FlexFit", "Puertos, conflicto frío/calor, comunicación y alcance de las averías."),
    (10, "mrv_network", "MRV/VRF y red", "Direcciones, conteo de interiores, buses, códigos decimales/hex y respuesta del sistema."),
    (11, "component_checks", "Comprobación de componentes", "Sondas, ventiladores, EEV, inverter, compresor, presiones, bomba y boya."),
    (12, "technical_values", "Valores técnicos", "Curvas NTC, tensiones, umbrales, conectores y puntos de monitorización."),
    (13, "normal_states", "Comportamientos normales", "Retardos, desescarche, retorno de aceite, precalentamiento y limitaciones."),
    (14, "service_tools_boards", "Herramientas y placas", "Diagnóstico desde PCB, monitor integrado y pasos tras sustituir placas."),
    (15, "system_architecture", "Arquitectura de sistemas", "Pistas para reconocer Single Zone, Multi, cassette, conductos y MRV."),
]

CATEGORY_BY_SLUG = {
    slug: {"id": ident, "slug": slug, "name": name, "description": description}
    for ident, slug, name, description in CATEGORIES
}


SOURCE_INDICATION_CONTEXTS = {
    "ADVPLUS": {
        "indication_type": "display",
        "display_location": "display de la unidad interior",
        "family_hint": "Advanced Plus Single Zone; los números vinculados corresponden a LED1 de la exterior.",
    },
    "FLEXMULTI": {
        "indication_type": "outdoor_display",
        "display_location": "display/LED de la placa exterior FlexFit Multi",
        "family_hint": "FlexFit Multi; el código visto en una interior o mando puede ser diferente.",
    },
    "FLEXPRO": {
        "indication_type": "mixed",
        "display_location": "display o receptor de la unidad FlexFit Pro",
        "family_hint": "FlexFit Pro comercial; confirme si lo muestra interior, mando o exterior.",
    },
    "MRVODU": {
        "indication_type": "outdoor_display",
        "display_location": "display y LED de la placa exterior MRV-S",
        "family_hint": "MRV-S; el display exterior usa decimal/subcódigo y el mando puede mostrar hexadecimal.",
    },
    "MRVCAS": {
        "indication_type": "controller",
        "display_location": "mando/receptor de cassette MRV-S",
        "family_hint": "Cassette compacta MRV-S; código interior de dos caracteres.",
    },
    "ARCTIC": {
        "indication_type": "mixed",
        "display_location": "display, mando o LED de la familia Arctic Multi",
        "family_hint": "Arctic Multi; el propio manual advierte que interior y exterior pueden mostrar códigos distintos.",
    },
}


def indication(
    code: str,
    indication_type: str,
    location: str,
    family: str,
    relationship: str,
    source_ref: str,
) -> dict[str, Any]:
    return {
        "code_display": code,
        "indication_type": indication_type,
        "display_location": location,
        "family_hint": family,
        "relationship": relationship,
        "source_ref": source_ref,
    }


def err(
    code: str,
    title: str,
    ref: str,
    page: str,
    scope: str,
    description: str,
    behavior: str,
    technical: str,
    *,
    aliases: str = "",
    restart: str = "Corregir la causa, restablecer la alimentación cuando el manual lo requiera y comprobar que el código no reaparece.",
    linked: list[dict[str, Any]] | None = None,
    section: str = "Error codes",
    profile: str = "",
) -> dict[str, Any]:
    return {
        "code": code,
        "title": title,
        "ref": ref,
        "page": page,
        "scope": scope,
        "description": description,
        "behavior": behavior,
        "technical": technical,
        "aliases": aliases,
        "restart": restart,
        "linked_indications": linked or [],
        "source_section": section,
        "profile": profile,
    }


ERROR_SPECS: list[dict[str, Any]] = []


def add_common_single_zone_errors() -> None:
    rows = [
        ("E1", "Sonda de ambiente interior", "Entrada de la sonda de aire interior fuera de rango.", "La unidad interior se protege.", "Comparar resistencia con temperatura real.", "sensor", None),
        ("E2", "Sonda de batería interior", "Entrada de la sonda de batería interior fuera de rango.", "La unidad interior se protege.", "Comprobar sonda, fijación térmica y conector.", "sensor", None),
        ("E4", "EEPROM de la unidad interior", "La placa interior no puede leer correctamente su memoria.", "La unidad interior se detiene o no inicializa correctamente.", "Reiniciar; si persiste, comprobar placa y configuración.", "configuration", None),
        ("E7", "Comunicación entre unidad interior y exterior", "La interior no recibe intercambio válido con la exterior.", "El sistema Single Zone se detiene por pérdida de comunicación.", "Terminales 1 y 2 alimentan la interior; el terminal 3 transporta datos y no debe llevar empalmes.", "communication", "15"),
        ("E14", "Ventilador interior", "La placa no detecta la velocidad interior esperada.", "La unidad interior detiene el funcionamiento protegido.", "Comprobar giro, alimentación, orden, realimentación y conector.", "fan", None),
        ("F12", "EEPROM de la unidad exterior", "La placa exterior no puede leer correctamente su memoria.", "La exterior se detiene.", "Confirmar placa/configuración antes de sustituir.", "configuration", "1"),
        ("F1", "Protección del módulo IPM", "El módulo inverter ha actuado.", "El compresor se detiene por protección.", "Comprobar alimentación, bus, compresor, disipación e IPM.", "inverter", "2"),
        ("F22", "Sobrecorriente de alimentación AC", "La corriente de entrada supera la protección.", "Compresor y exterior se protegen.", "Medir red bajo carga y revisar rectificador/PFC/carga.", "power", "3"),
        ("F3", "Comunicación entre IPM y placa exterior", "La placa principal no intercambia datos con el módulo de potencia.", "El compresor no puede funcionar.", "Conector de módulo: aproximadamente 5 V entre 1-2 y 15 V entre 2-3.", "communication", "4"),
        ("F19", "Tensión de red alta o baja", "La tensión queda fuera de la ventana permitida.", "La exterior bloquea o limita el compresor.", "Medir red y bus durante el intento de arranque.", "power", "6"),
        ("F27", "Rotor bloqueado o parada instantánea del compresor", "El inverter no consigue mantener el giro.", "El compresor se detiene.", "Comprobar equilibrio U/V/W, carga mecánica e IPM.", "compressor", "7"),
        ("F4", "Temperatura de descarga excesiva", "La sonda de descarga alcanza la protección.", "El compresor se detiene; puede reintentar al enfriar.", "Umbral documentado: 110 °C durante 20 s.", "temperature", "8"),
        ("F8", "Ventilador exterior DC", "La placa no detecta velocidad exterior correcta.", "La exterior protege el circuito frigorífico.", "Aproximadamente 310 V, 15 V y señales 0-6/0-5 V según pines del motor documentado.", "fan", "9"),
        ("F21", "Sonda de desescarche", "La entrada de la sonda de batería exterior está fuera de rango.", "La exterior pierde la regulación normal y se protege.", "Comparar curva NTC y temperatura real.", "sensor", "10"),
        ("F7", "Sonda de aspiración", "La entrada de temperatura de aspiración está fuera de rango.", "La exterior se protege.", "Comprobar sonda, fijación y cable.", "sensor", "11"),
        ("F6", "Sonda de ambiente exterior", "La entrada de ambiente exterior está fuera de rango.", "La exterior se protege o pierde límites de funcionamiento.", "Comparar NTC y temperatura real.", "sensor", "12"),
        ("F25", "Sonda de descarga", "La entrada de la sonda de descarga está abierta, en corto o fuera de rango.", "La exterior se protege.", "Confirmar que la sonda corresponde a la curva de descarga.", "sensor", "13"),
        ("F11", "Pérdida de sincronismo del compresor", "El control detecta desviación o pérdida de giro.", "El compresor se detiene.", "Comprobar U/V/W, resistencias, carga e inverter.", "compressor", "18"),
        ("F28", "Circuito de detección de posición", "El inverter no determina correctamente la posición del rotor.", "El compresor no arranca o se detiene.", "Comprobar compresor, cableado y placa inverter.", "compressor", "19"),
        ("F2", "Sobrecorriente del compresor", "La corriente del compresor supera la protección.", "El compresor se detiene.", "Medir corriente, equilibrio de bobinados, presión y bus.", "compressor", "24"),
        ("F23", "Sobrecorriente de fase del compresor", "Una fase del compresor supera el límite.", "El compresor se detiene.", "Comparar las tres fases y descartar bloqueo o IPM.", "compressor", "25"),
        ("F36", "Sonda de batería exterior", "La sonda de condensación exterior está fuera de rango.", "La exterior se protege.", "Comparar NTC, fijación y lectura real.", "sensor", "39"),
    ]
    for code, title, description, behavior, technical, profile, linked_code in rows:
        linked = []
        if linked_code:
            linked.append(indication(
                linked_code,
                "outdoor_led",
                "LED1/display de la placa exterior",
                "Advanced Plus / FlexFit: referencia numérica exterior",
                f"La avería {code} de la capa interior se relaciona con la indicación exterior {linked_code}; confirme familia.",
                "ADVPLUS",
            ))
        ERROR_SPECS.append(err(
            code, title, "ADVPLUS", "30", "system", description, behavior, technical,
            linked=linked, profile=profile,
        ))


def add_multisplit_numeric_errors() -> None:
    rows = [
        ("1", "EEPROM de la exterior", "Memoria exterior anormal.", "La exterior se protege.", "Confirmar ajuste y placa.", "configuration"),
        ("2", "Protección IPM", "Actuación del módulo de potencia.", "El compresor se detiene.", "Revisar compresor, bus, IPM y disipador.", "inverter"),
        ("4", "Comunicación IPM-placa exterior", "Pérdida de intercambio entre placas.", "El compresor se detiene.", "Comprobar alimentación y cable de módulo.", "communication"),
        ("5", "Sobrecarga del compresor", "La protección térmica/carga del compresor actúa.", "El compresor se detiene.", "Comprobar corriente, presiones y refrigeración.", "compressor"),
        ("6", "Alimentación no fiable", "Tensión demasiado baja o alta bajo carga.", "La exterior impide o detiene el compresor.", "No menos de 187 VAC al arranque, 197 VAC en marcha ni más de 253 VAC.", "power"),
        ("8", "Temperatura de descarga alta", "La descarga supera el límite.", "El compresor se detiene; tras tres veces en una hora queda bloqueado.", "Umbral 115 °C; recupera al bajar dentro de la lógica documentada.", "temperature"),
        ("9", "Ventilador exterior", "No se alcanza la velocidad de ventilador.", "La exterior se protege.", "310-334 V rojo-negro; 15 V blanco-negro; orden y feedback según manual.", "fan"),
        ("10", "Sonda de desescarche", "Sonda exterior de desescarche fuera de rango.", "La exterior se protege.", "Comparar curva NTC.", "sensor"),
        ("11", "Sonda de aspiración", "Sonda de aspiración fuera de rango.", "La exterior se protege.", "Comparar curva NTC.", "sensor"),
        ("12", "Sonda de ambiente exterior", "Sonda de ambiente fuera de rango.", "La exterior se protege.", "Comparar curva NTC.", "sensor"),
        ("13", "Sonda de descarga", "Sonda de descarga fuera de rango.", "La exterior se protege.", "Aplicar la curva de alta temperatura correspondiente.", "sensor"),
        ("15", "Comunicación interior-exterior", "Uno o más puertos no intercambian datos con su interior.", "La unidad/puerto afectado no funciona; el alcance depende de la arquitectura y del puerto.", "Bornes 3/C y 1; el LED verde continuo identifica comunicación normal del puerto.", "communication"),
        ("16", "Falta de refrigerante", "Rendimiento/condiciones compatibles con carga insuficiente.", "La exterior se protege o limita.", "Confirmar con presiones, temperaturas y búsqueda de fugas; no cargar solo por el código.", "refrigerant"),
        ("17", "Válvula de cuatro vías", "No se detecta la inversión esperada.", "La demanda de calor/frío no se completa.", "Comprobar bobina, alimentación y diferencia térmica.", "valve"),
        ("18", "Pérdida de sincronismo del compresor", "El rotor se desvía del control.", "El compresor se detiene.", "Comprobar compresor, U/V/W e inverter.", "compressor"),
        ("20", "Sobrecarga térmica interior", "La batería interior alcanza protección.", "La interior afectada limita o detiene la demanda.", "Comprobar caudal, filtros, ventilador y temperatura de batería.", "temperature"),
        ("21", "Batería interior congelada", "La temperatura interior cae al límite antihielo.", "La interior/compresor se detiene temporalmente.", "Comprobar caudal, filtros, ventilador y carga.", "temperature"),
        ("23", "Temperatura del IPM alta", "El disipador del módulo supera el límite.", "El compresor se detiene.", "Comprobar ventilación, fijación y pasta térmica.", "inverter"),
        ("24", "Fallo de arranque del compresor", "El inverter no consigue arrancar.", "El compresor se detiene.", "Comprobar presión equilibrada, bobinados e IPM.", "compressor"),
        ("25", "Corriente IPM", "El módulo detecta corriente anormal.", "El compresor se detiene.", "Comprobar carga, compresor y módulo.", "inverter"),
        ("26", "Reinicio de la placa", "La placa exterior se reinicia de forma anormal.", "El sistema interrumpe la marcha.", "Revisar alimentación, fuentes y placa.", "power"),
        ("27", "Detección de corriente", "La lectura de corriente no es coherente.", "La exterior se protege.", "Comprobar CT/sensor, cable y placa.", "power"),
        ("28", "Sonda de líquido A", "Sonda de líquido del puerto A fuera de rango.", "Se afecta la regulación del puerto A.", "Comparar curva y conector del puerto.", "sensor"),
        ("29", "Sonda de líquido B", "Sonda de líquido del puerto B fuera de rango.", "Se afecta la regulación del puerto B.", "Comparar curva y conector del puerto.", "sensor"),
        ("30", "Sonda de líquido C", "Sonda de líquido del puerto C fuera de rango.", "Se afecta la regulación del puerto C.", "Comparar curva y conector del puerto.", "sensor"),
        ("31", "Sonda de líquido D", "Sonda de líquido del puerto D fuera de rango.", "Se afecta la regulación del puerto D.", "Comparar curva y conector del puerto.", "sensor"),
        ("32", "Sonda de gas A", "Sonda de gas del puerto A fuera de rango.", "Se afecta la regulación del puerto A.", "Comparar curva y conector del puerto.", "sensor"),
        ("33", "Sonda de gas B", "Sonda de gas del puerto B fuera de rango.", "Se afecta la regulación del puerto B.", "Comparar curva y conector del puerto.", "sensor"),
        ("34", "Sonda de gas C", "Sonda de gas del puerto C fuera de rango.", "Se afecta la regulación del puerto C.", "Comparar curva y conector del puerto.", "sensor"),
        ("35", "Sonda de gas D", "Sonda de gas del puerto D fuera de rango.", "Se afecta la regulación del puerto D.", "Comparar curva y conector del puerto.", "sensor"),
        ("36", "Sonda de gas E", "Sonda de gas del puerto E fuera de rango.", "Se afecta la regulación del puerto E.", "Comparar curva y conector del puerto.", "sensor"),
        ("38", "Temperatura IPM o corte momentáneo", "El módulo registra sobretemperatura o una interrupción de potencia.", "El compresor se detiene.", "Comprobar red, bus y disipación.", "inverter"),
        ("39", "Sonda de condensación", "Sonda de condensación fuera de rango.", "La exterior se protege.", "Comparar NTC y fijación.", "sensor"),
        ("40", "Sonda de líquido E", "Sonda de líquido del puerto E fuera de rango.", "Se afecta la regulación del puerto E.", "Comparar curva y conector.", "sensor"),
        ("41", "Sonda Toci", "La entrada Toci está fuera de rango.", "La exterior se protege.", "Identificar sonda y comparar curva.", "sensor"),
        ("42", "Presostato de alta abierto", "El contacto HPS indica alta presión.", "El compresor se detiene.", "Medir presión real y revisar caudal/ventilación/válvulas.", "pressure"),
        ("43", "Presostato de baja abierto", "El contacto LPS indica baja presión.", "El compresor se detiene.", "Medir presión real, carga y restricciones.", "pressure"),
        ("44", "Protección de alta presión", "La presión de descarga supera el límite.", "El compresor se detiene.", "Comprobar condensación, ventiladores, válvulas y carga.", "pressure"),
        ("45", "Protección de baja presión", "La presión de aspiración cae al límite.", "El compresor se detiene.", "Comprobar carga, fugas, EEV y restricciones.", "pressure"),
        ("Lo", "Temperatura ambiente exterior demasiado baja", "La máquina está fuera del límite de ambiente para la operación solicitada.", "La demanda queda inhibida; es una condición de límite, no un componente averiado.", "Confirmar temperatura exterior y rango de funcionamiento.", "normal"),
    ]
    reverse_links = {
        "1": "F12", "2": "F1", "4": "F3", "6": "F19", "8": "F4", "9": "F8",
        "10": "F21", "11": "F7", "12": "F6", "13": "F25", "15": "E7",
        "18": "F11", "24": "F2", "25": "F23", "39": "F36",
    }
    for code, title, description, behavior, technical, profile in rows:
        linked = []
        if code in reverse_links:
            linked.append(indication(
                reverse_links[code],
                "display",
                "display de la unidad interior",
                "Advanced Plus Single Zone",
                f"Código interior relacionado; no usar la equivalencia sin confirmar la familia y el lugar de lectura.",
                "ADVPLUS",
            ))
        ERROR_SPECS.append(err(
            code, title, "FLEXMULTI", "22", "outdoor", description, behavior, technical,
            linked=linked, profile=profile,
        ))


add_common_single_zone_errors()
add_multisplit_numeric_errors()


def add_mrv_outdoor_errors() -> None:
    rows = [
        ("20", "Sonda Te1 de la exterior MRV", "Entrada Te1 anormal.", "Avería rearmable; la exterior se protege mientras persiste.", "Comparar sonda y temperatura real.", "sensor"),
        ("21", "Sonda de ambiente Ta de la exterior MRV", "Entrada Ta anormal.", "Avería rearmable.", "Comparar sonda y temperatura real.", "sensor"),
        ("22", "Sonda de aspiración Ts de la exterior MRV", "Entrada Ts anormal.", "Avería rearmable.", "Comparar sonda y temperatura real.", "sensor"),
        ("23", "Sonda de descarga Td de la exterior MRV", "Entrada Td anormal.", "Avería rearmable.", "Comparar sonda de alta temperatura y cable.", "sensor"),
        ("26-0", "Sin comunicación con unidades interiores", "La exterior no encuentra ninguna interior en la red.", "El sistema MRV no puede funcionar.", "Comprobar alimentación de todas las interiores, polaridad/topología y bus.", "communication"),
        ("26-1", "Menos interiores detectadas que configuradas", "El conteo online es inferior al ajuste.", "Las unidades ausentes no funcionan y la puesta en marcha queda incompleta.", "Comparar conteo, direcciones y alimentación.", "address"),
        ("26-2", "Más interiores detectadas que configuradas", "El conteo online supera el ajuste.", "La red queda en condición de configuración anormal.", "Buscar direcciones/ramas adicionales o ajuste de cantidad incorrecto.", "address"),
        ("28", "Sensor de alta presión", "La señal del transductor de alta es anormal.", "Avería rearmable; se detiene la regulación normal.", "Comparar presión de monitor con manómetro y alimentación del sensor.", "pressure"),
        ("29", "Sensor de baja presión", "La señal del transductor de baja es anormal.", "Avería rearmable.", "En el mando cableado este fallo puede aparecer como 1D; comparar monitor con manómetro.", "pressure"),
        ("30", "Presostato de alta HPS", "El contacto de alta actúa.", "Reintenta; tres actuaciones en una hora confirman el bloqueo.", "Medir presión real y revisar condensación, ventiladores, válvulas y carga.", "pressure"),
        ("33", "EEPROM de la exterior MRV", "Lectura/escritura de memoria anormal.", "La exterior no puede mantener una configuración fiable.", "Comprobar placa, selectores y datos de configuración.", "configuration"),
        ("34", "Descarga excesiva MRV", "Td alcanza 115 °C.", "Reinicia tras el tiempo de protección; tres veces en una hora confirman la avería.", "Umbral 115 °C; revisar refrigerante, EEV, sensores y compresor.", "temperature"),
        ("35", "Inversión de válvula de cuatro vías", "Tras 3 min energizada no se alcanza Pd-Ps ≥ 0,6 MPa durante 10 s.", "El sistema se detiene por inversión no confirmada.", "Comprobar bobina, corredera, presiones y orden.", "valve"),
        ("39-0", "Baja presión MRV", "Ps queda por debajo del límite.", "Reintenta tras 2 min 50 s; tres veces en una hora confirman la avería.", "Frío: <0,05 MPa; calor/retorno de aceite: <0,03 MPa durante 5 min.", "pressure"),
        ("39-1", "Relación de compresión demasiado alta", "Pd/Ps supera 8 durante 5 min.", "Reintenta tras 2 min 50 s; tres veces en una hora confirman la avería.", "Comprobar presiones, caudal, EEV y restricciones.", "pressure"),
        ("39-2", "Relación de compresión demasiado baja", "Pd/Ps queda por debajo de 1,8 durante 5 min.", "Reintenta; tres veces en una hora confirman la avería.", "Comprobar compresor, válvula de cuatro vías y presiones.", "pressure"),
        ("40", "Alta presión MRV", "Pd alcanza 4,15 MPa durante 50 ms.", "Reintenta tras 2 min 50 s; tres veces en una hora confirman la avería.", "Revisar intercambio, ventiladores, válvulas y carga.", "pressure"),
        ("43", "Temperatura de descarga demasiado baja", "Td queda por debajo de CT + 10 °C durante 5 min.", "Reintenta tras 2 min 50 s; tres veces en una hora confirman la avería.", "Comprobar sonda, retorno de líquido, EEV y compresor.", "temperature"),
        ("46", "Comunicación de placa inverter", "La placa principal pierde intercambio con el inverter.", "Avería rearmable; el compresor no funciona mientras persiste.", "Comprobar fuentes, conectores y placas.", "communication"),
        ("53", "Corriente CT baja o sensor CT", "La lectura de corriente es insuficiente/anormal.", "Reintenta tras 3 min; tres veces en una hora confirman la avería.", "Comprobar CT, cableado, compresor y corriente real.", "power"),
        ("54", "Comunicación con placa de válvulas", "La placa de válvulas no responde.", "La regulación de válvulas queda interrumpida.", "Comprobar alimentación, bus y placa.", "communication"),
        ("57", "Comunicación placa de válvulas-host", "Pérdida de datos entre placa de válvulas y control principal.", "La regulación asociada se detiene.", "Comprobar cable y fuentes.", "communication"),
        ("58", "Sonda Tc1 de placa de válvulas", "Entrada Tc1 anormal.", "La regulación asociada se protege.", "Comparar NTC y conector.", "sensor"),
        ("59", "Sonda Tc2 de placa de válvulas", "Entrada Tc2 anormal.", "La regulación asociada se protege.", "Comparar NTC y conector.", "sensor"),
        ("60", "Reserva de módulo de válvulas 60", "Código reservado por el módulo.", "No sustituir componentes solo por el número; confirmar revisión de placa.", "Consultar la tabla exacta de la variante.", "configuration"),
        ("61", "Reserva de módulo de válvulas 61", "Código reservado por el módulo.", "No sustituir componentes solo por el número; confirmar revisión de placa.", "Consultar la tabla exacta de la variante.", "configuration"),
        ("62", "Reserva de módulo de válvulas 62", "Código reservado por el módulo.", "No sustituir componentes solo por el número; confirmar revisión de placa.", "Consultar la tabla exacta de la variante.", "configuration"),
        ("63", "Selector de la placa de válvulas", "La posición del dial/selector no es válida.", "La placa no se identifica correctamente.", "Comparar posición con diseño de sistema y placa sustituida.", "configuration"),
        ("64", "Corriente CT alta", "La lectura de corriente supera el límite.", "El compresor se detiene.", "Medir corriente real y revisar CT, compresor e inverter.", "power"),
        ("71-0", "Ventilador exterior superior bloqueado", "Velocidad <20 rpm durante 30 s o <70 % del objetivo durante 2 min.", "Reintenta tras 2 min 50 s; tres veces en una hora confirman la avería.", "Comprobar bloqueo, motor, alimentación, orden y feedback.", "fan"),
        ("71-1", "Ventilador exterior inferior bloqueado", "Velocidad <20 rpm durante 30 s o <70 % del objetivo durante 2 min.", "Reintenta tras 2 min 50 s; tres veces en una hora confirman la avería.", "Comprobar bloqueo, motor, alimentación, orden y feedback.", "fan"),
        ("75-0", "Sin caída de presión al arrancar", "Pd-Ps no supera 0,1 MPa durante el primer minuto.", "Reintenta después de 180 s; tres veces en una hora confirman la avería.", "Comprobar compresor, válvula de cuatro vías y sensores.", "pressure"),
        ("75-4", "Caída de presión insuficiente", "Pd-Ps permanece ≤0,2 MPa durante 5 min.", "Reintenta tras 3 min; tres veces en una hora confirman la avería.", "Comprobar compresor, válvulas y presiones reales.", "pressure"),
        ("78", "Falta de refrigerante MRV", "El control detecta condición compatible con carga insuficiente.", "Genera alarma pero el manual indica expresamente que no detiene el sistema.", "Confirmar con presiones, temperaturas, estanqueidad y carga pesada; no añadir refrigerante por el código aislado.", "refrigerant"),
        ("81", "Temperatura IPM alta", "El disipador alcanza 85 °C.", "El compresor se detiene para proteger el módulo.", "Revisar ventilación, fijación, suciedad y módulo.", "inverter"),
        ("82", "Corriente del compresor", "La corriente supera la condición permitida.", "El compresor se detiene.", "Comprobar bobinados, carga, presiones e inverter.", "compressor"),
        ("83", "Modelo o cantidad de ventiladores incorrectos", "La configuración no coincide con el equipo.", "Avería no rearmable hasta corregir la configuración.", "Revisar selectores, placa y cantidad de ventiladores.", "configuration"),
        ("108", "Sobrecorriente software del rectificador IPM", "El control detecta exceso de corriente en rectificación.", "El compresor se detiene.", "Comprobar red, rectificador, bus e inverter.", "inverter"),
        ("109", "Detección de corriente inverter", "La lectura interna de corriente es anormal.", "El compresor se detiene.", "Comprobar sensor/circuito de corriente e inverter.", "inverter"),
        ("110", "Protección IPM F0", "El módulo informa protección F0.", "El compresor se detiene.", "Comprobar compresor, módulo, disipación y bus.", "inverter"),
        ("111", "Compresor fuera de control o rotor no detectado", "El inverter pierde control del rotor.", "El compresor se detiene.", "Comprobar U/V/W, equilibrio y módulo.", "compressor"),
        ("112", "Disipador inverter demasiado caliente", "La temperatura del radiador supera el límite.", "El compresor se detiene.", "Comprobar ventilación, sensor y contacto térmico.", "inverter"),
        ("113", "Sobrecarga inverter", "El módulo supera la carga permitida.", "El compresor se detiene.", "Comprobar corriente, presión y compresor.", "inverter"),
        ("114", "Bus DC bajo", "La tensión del bus de continua es insuficiente.", "El compresor se detiene.", "Medir red, rectificador, PFC y condensadores.", "power"),
        ("115", "Bus DC alto", "La tensión del bus de continua es excesiva.", "El compresor se detiene.", "Medir red, PFC y regeneración.", "power"),
        ("116", "Comunicación inverter-control", "La placa inverter pierde comunicación con el control.", "Avería rearmable; el compresor se detiene.", "Comprobar cable, fuentes y placas.", "communication"),
        ("117", "Sobrecorriente software inverter", "El cálculo de corriente supera el límite.", "El compresor se detiene.", "Comprobar carga, compresor y módulo.", "inverter"),
        ("118", "Arranque del compresor inverter", "El rotor no inicia correctamente.", "El compresor se detiene.", "Comprobar presión equilibrada, bobinados e IPM.", "compressor"),
        ("119", "Circuito de detección de corriente", "La etapa de medida de corriente es anormal.", "El compresor se detiene.", "Comprobar CT, circuito y placa.", "inverter"),
        ("120", "Fallo instantáneo de potencia inverter", "Se detecta una interrupción/caída instantánea.", "El compresor se detiene.", "Comprobar red, contactores y bus.", "power"),
        ("121", "Alimentación de la placa inverter", "Una fuente de la placa está fuera de rango.", "El compresor no funciona.", "Comprobar entrada y fuentes internas.", "power"),
        ("122", "Sonda del radiador inverter", "La entrada de temperatura del disipador es anormal.", "El compresor se protege.", "Comparar sensor, fijación y conector.", "sensor"),
        ("123", "Sobrecorriente hardware del rectificador", "La protección física del rectificador actúa.", "El compresor se detiene.", "Comprobar red, rectificador, bus e inverter.", "inverter"),
        ("555.0", "Capacidad interior fuera del intervalo", "La suma conectada queda por debajo del 50 % o por encima del 130 %.", "El sistema permanece en espera por combinación no válida.", "Comparar suma de capacidades con límites del conjunto.", "configuration"),
        ("555.1", "Ambiente demasiado alto para calefacción", "Ta supera 27 °C (80,6 °F).", "La calefacción queda en espera; no es un componente averiado.", "Confirmar Ta y rango de trabajo.", "normal"),
        ("555.3", "Ambiente fuera de rango para refrigeración", "Ta supera 54 °C (129,2 °F) o baja de -10 °C (14 °F).", "La refrigeración queda en espera.", "Confirmar Ta y rango de trabajo.", "normal"),
    ]
    for code, title, description, behavior, technical, profile in rows:
        linked = []
        aliases = ""
        if code == "29":
            aliases = "1D"
            linked = [indication(
                "1D", "controller", "mando cableado MRV",
                "MRV-S: representación hexadecimal del código decimal 29",
                "El mismo fallo de sensor de baja presión se muestra como 29 en la exterior y 1D en el mando.",
                "MRVODU",
            )]
        ERROR_SPECS.append(err(
            code, title, "MRVODU", "63-66", "outdoor", description, behavior, technical,
            aliases=aliases, linked=linked, profile=profile,
            restart=(
                "No requiere rearme por componente: volverá a operar cuando la condición ambiental o de combinación sea válida."
                if profile == "normal"
                else "Aplicar la respuesta y el número de reintentos indicados; no borrar sin registrar el código y su subcódigo."
            ),
            section="Failure code table and control response",
        ))


def add_mrv_cassette_errors() -> None:
    rows = [
        ("01", "Sonda de ambiente TA de cassette MRV", "Entrada TA anormal.", "La cassette afectada se protege.", "Comparar NTC y temperatura real.", "sensor"),
        ("02", "Sonda TC1 de cassette MRV", "Entrada TC1 anormal.", "La cassette afectada se protege.", "Comparar NTC y fijación.", "sensor"),
        ("03", "Sonda TC2 de cassette MRV", "Entrada TC2 anormal.", "La cassette afectada se protege.", "Comparar NTC y fijación.", "sensor"),
        ("04", "Sonda de fuente dual de calor", "Entrada de la sonda auxiliar anormal.", "La función asociada se protege.", "Comprobar sonda, cable y configuración.", "sensor"),
        ("05", "EEPROM de cassette MRV", "Memoria interior anormal.", "La cassette puede quedar detenida.", "Revisar DIP/dirección y placa.", "configuration"),
        ("06", "Comunicación interior-exterior MRV", "La cassette pierde la red exterior.", "La cassette afectada queda sin operación normal; otras unidades pueden seguir si la red lo permite.", "Comprobar alimentación y bus.", "communication"),
        ("07", "Comunicación cassette-mando cableado", "No hay intercambio válido con el mando.", "La unidad queda sin control desde ese mando.", "Comprobar tres hilos A/B/C, polaridad, principal/secundario y conectores.", "communication"),
        ("08", "Drenaje de cassette MRV", "La boya permanece en condición de nivel alto o la bomba no evacua.", "La cassette afectada detiene su operación y mantiene la lógica de bombeo; las demás unidades no tienen por qué pararse.", "CN13 es la boya; CN4 entrega 220 VAC a la bomba en esta variante.", "drain"),
        ("09", "Dirección interior duplicada", "Dos unidades comparten dirección.", "La red no identifica correctamente las interiores.", "Revisar DIP/dirección y repetir adquisición.", "address"),
        ("0A", "Código reservado de cassette MRV", "Función reservada en la tabla de esta familia.", "No sustituir piezas sin una tabla específica de la revisión instalada.", "Confirmar revisión de placa/manual.", "configuration"),
        ("0C", "Detección de cruce por cero", "La placa interior no detecta correctamente el cruce de la red AC.", "La cassette se protege.", "Comprobar alimentación, señal de cruce y placa.", "power"),
        ("0E", "Ventilador DC interior de cassette", "No se detecta la velocidad esperada.", "La cassette afectada se detiene.", "Comprobar motor, alimentación, orden y realimentación.", "fan"),
        ("20", "Fallo exterior comunicado a cassette MRV", "La interior informa que existe un código en la exterior.", "El alcance depende del código exterior; consultar inmediatamente el display MRV.", "Anotar también código principal y subcódigo de la placa exterior.", "communication"),
    ]
    for code, title, description, behavior, technical, profile in rows:
        ERROR_SPECS.append(err(
            code, title, "MRVCAS", "33", "indoor", description, behavior, technical,
            profile=profile, section="Indoor failure code table",
        ))

    ERROR_SPECS.append(err(
        "0C", "Desbordamiento/boya en FlexFit Pro", "FLEXPRO", "73-75", "indoor",
        "La entrada de boya permanece abierta o la bomba no consigue bajar el nivel.",
        "En frío/seco se detiene la demanda afectada y continúa la bomba; en calor/ventilación/espera la apertura también arranca la bomba.",
        "Boya normalmente cerrada: abre al subir el agua. Si no cierra, mantiene bomba y genera el código de drenaje.",
        profile="drain", section="Drain control and failure diagnosis",
    ))


add_mrv_outdoor_errors()
add_mrv_cassette_errors()

ERROR_SPECS.append(err(
    "1D", "Sensor de baja presión MRV mostrado en el mando", "MRVODU", "63-66", "outdoor",
    "Representación hexadecimal que usa el mando cableado para el código decimal 29 de la exterior.",
    "Avería rearmable del sensor de baja presión; el técnico debe consultar también el display exterior.",
    "Comparar presión mostrada, señal del transductor y manómetro; no confundir 1D con una familia que use códigos alfanuméricos propios.",
    aliases="29",
    linked=[indication(
        "29", "outdoor_display", "display de la placa exterior MRV-S",
        "MRV-S: código decimal correspondiente",
        "1D en el mando y 29 en la exterior describen el mismo fallo en esta familia.",
        "MRVODU",
    )],
    profile="pressure", section="Decimal outdoor code to hexadecimal controller code",
))


DIAGNOSTIC_PROFILES: dict[str, tuple[list[str], list[str]]] = {
    "sensor": (
        ["Sonda abierta o en cortocircuito", "Cable, conector o contacto térmico incorrecto", "Entrada analógica de la placa defectuosa"],
        ["Medir la sonda desconectada y anotar la temperatura real", "Comparar con la curva correcta de 10K, 23K o 50K", "Revisar continuidad, conector y lectura de placa antes de sustituir"],
    ),
    "communication": (
        ["Unidad sin alimentación", "Cable abierto, cruzado, empalmado o con mala conexión", "Dirección/configuración incorrecta", "Placa emisora o receptora defectuosa"],
        ["Anotar dónde se leyó cada código", "Comprobar alimentación de ambos extremos", "Revisar continuidad, polaridad y topología del bus", "Aislar por ramas antes de condenar una placa"],
    ),
    "configuration": (
        ["DIP, dial, dirección o capacidad incorrectos", "Placa sustituida sin reproducir ajustes", "EEPROM o placa defectuosa"],
        ["Fotografiar y registrar ajustes antes de cambiarlos", "Comparar con placa de características y arquitectura", "Reiniciar y repetir adquisición/prueba"],
    ),
    "address": (
        ["Dirección duplicada o fuera de rango", "Cantidad configurada diferente de la instalada", "Unidad sin alimentación o fuera de la red"],
        ["Contar unidades realmente alimentadas", "Comparar direcciones y ajuste de cantidad", "Corregir y repetir direccionamiento/Trial Operation"],
    ),
    "fan": (
        ["Ventilador bloqueado o turbina rozando", "Alimentación u orden de velocidad ausente", "Realimentación, cable o motor defectuosos", "Driver de placa defectuoso"],
        ["Cortar tensión y comprobar giro libre", "Identificar conector/pines antes de medir", "Comprobar potencia, alimentación de control, orden y feedback", "Sustituir el motor solo si las señales son correctas"],
    ),
    "drain": (
        ["Boya atascada abierta", "Bomba de condensados bloqueada o sin alimentación", "Tubo obstruido, sin pendiente o con entrada de aire", "Cable/conector o placa interior"],
        ["Comprobar primero si hay agua real en la bandeja", "Verificar que la boya normalmente cerrada cambia de estado", "Comprobar salida de bomba y caudal", "Repetir la secuencia completa en frío y en espera/calor"],
    ),
    "inverter": (
        ["Compresor o motor anormal", "Red o bus DC fuera de rango", "IPM/rectificador/driver defectuoso", "Disipación insuficiente"],
        ["Descargar y verificar el bus antes de manipular", "Medir red y bus bajo la condición de fallo", "Comparar bobinados/fases y aislamiento según manual", "Revisar disipador y conectores antes de sustituir placa"],
    ),
    "compressor": (
        ["Compresor bloqueado o bobinado desequilibrado", "Presiones no equilibradas o carga frigorífica anormal", "Cable U/V/W o inverter defectuoso"],
        ["Esperar descarga segura del bus", "Comparar resistencias U/V/W y aislamiento según manual", "Medir corriente y presiones durante un intento controlado", "Separar fallo mecánico de fallo del inverter"],
    ),
    "power": (
        ["Alimentación alta, baja o inestable", "Conexión floja o fase ausente", "Rectificador, PFC, condensadores o sensor de corriente defectuosos"],
        ["Medir tensión en reposo y bajo arranque", "Comprobar conexiones, caída y equilibrio", "Medir bus DC con procedimiento seguro", "Aislar cargas antes de sustituir placa"],
    ),
    "pressure": (
        ["Caudal de aire o agua insuficiente", "Carga, EEV o válvula anormal", "Transductor/presostato o cable defectuoso", "Compresor o restricción frigorífica"],
        ["Medir presión real con instrumento adecuado", "Comparar con el valor calculado por la placa", "Revisar ventiladores, filtros, baterías y válvulas", "No puentear protecciones como solución"],
    ),
    "temperature": (
        ["Caudal insuficiente", "Carga o EEV anormal", "Sonda desplazada o fuera de curva", "Intercambiador sucio o ventilador defectuoso"],
        ["Comparar temperatura real y lectura de placa", "Comprobar caudal y limpieza", "Medir presiones y sobrecalentamiento/subenfriamiento", "Dejar recuperar y verificar el tiempo de rearme"],
    ),
    "refrigerant": (
        ["Fuga de refrigerante", "Carga incorrecta", "Restricción o EEV anormal", "Sonda/presión que induce una detección falsa"],
        ["Buscar fugas y reparar antes de cargar", "Pesar la carga según placa y tubería", "Comparar presiones, temperaturas y válvulas", "No añadir refrigerante únicamente por el código"],
    ),
    "valve": (
        ["Bobina sin alimentación o abierta", "Corredera bloqueada", "Presión insuficiente para invertir", "Cable o salida de placa"],
        ["Comprobar orden y tensión de la bobina", "Comparar temperaturas y presiones antes/después", "Verificar que no existe restricción o falta de carga"],
    ),
    "normal": (
        ["Condición ambiental o de demanda fuera del rango permitido"],
        ["Confirmar temperatura/estado real", "Esperar la condición de recuperación documentada", "No sustituir componentes si el sistema vuelve a operar al entrar en rango"],
    ),
}


def diagnostic_profile(spec: dict[str, Any]) -> tuple[list[str], list[str]]:
    profile = spec.get("profile") or ""
    if profile in DIAGNOSTIC_PROFILES:
        return DIAGNOSTIC_PROFILES[profile]
    return (
        ["Condición indicada por el código", "Cableado, conector o ajuste incorrecto", "Placa de control defectuosa"],
        ["Confirmar familia y punto de indicación", "Comprobar el elemento relacionado y su cableado", "Corregir la causa y repetir una prueba controlada"],
    )


def operational_impact(spec: dict[str, Any]) -> dict[str, Any]:
    value = normalize(spec["behavior"])
    if "NO DETIENE" in value or "NO ES UN COMPONENTE" in value or "QUEDA EN ESPERA" in value:
        level = "warning"
    elif "TODO EL SISTEMA" in value or "EL SISTEMA MRV NO" in value:
        level = "all_system"
    elif "AFECTADA" in value or "PUERTO" in value:
        level = "affected_unit"
    else:
        level = "protected_stop"
    return {
        "stop_level": level,
        "summary": spec["behavior"],
        "affected_scope": "Alcance documentado para esta familia Haier y este punto de indicación.",
        "unaffected_scope": (
            "El código 78 de MRV-S solo genera alarma según la fuente."
            if spec["code"] == "78" and spec["ref"] == "MRVODU"
            else None
        ),
        "restart_behavior": spec["restart"],
        "degraded_behavior": None,
        "notes": "No extrapolar la misma respuesta a otra familia que use el mismo código.",
    }


def dataset_for(spec: dict[str, Any], interpretation_id: int) -> dict[str, Any]:
    return {
        "id": interpretation_id * 10 + 1,
        "name": f"{spec['code']} — referencia técnica de la variante",
        "dataset_type": "technical_reference",
        "variable_name": "Comprobación",
        "variable_unit": None,
        "value_name": "Dato",
        "value_unit": None,
        "tolerance_text": "Aplicar solo a la familia y punto de indicación descritos.",
        "source_kind": "official",
        "calculation_method": None,
        "review_status": "reviewed",
        "notes": spec["technical"],
        "visible": 1,
        "points": [{
            "variable_value": None,
            "value_min": None,
            "value_nominal": None,
            "value_max": None,
            "value_text": spec["technical"],
            "sort_order": 1,
            "notes": None,
        }],
        "sources": [source(spec["ref"], spec["page"], f"Valor técnico — {spec['code']}")],
    }


def build_indication_contexts(spec: dict[str, Any]) -> list[dict[str, Any]]:
    base = SOURCE_INDICATION_CONTEXTS[spec["ref"]]
    rows = [{
        "code_display": spec["code"],
        "code_normalized": normalize(spec["code"]).replace(" ", ""),
        "indication_type": base["indication_type"],
        "display_location": base["display_location"],
        "family_hint": base["family_hint"],
        "relationship": "Código documentado en esta capa de indicación.",
        "source_ref": spec["ref"],
        "source_document_ref": SOURCES[spec["ref"]]["document_ref"],
        "related_error_id": None,
    }]
    for linked in spec["linked_indications"]:
        row = dict(linked)
        row["code_normalized"] = normalize(row["code_display"]).replace(" ", "")
        row["source_document_ref"] = SOURCES[row["source_ref"]]["document_ref"]
        row["related_error_id"] = None
        rows.append(row)
    return rows


def build_interpretation(interpretation_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    causes, checks = diagnostic_profile(spec)
    contexts = build_indication_contexts(spec)
    info: list[dict[str, Any]] = []
    item_id = interpretation_id * 100

    def add(item_type: str, body: str) -> None:
        nonlocal item_id
        item_id += 1
        info.append({
            "id": item_id,
            "item_type": item_type,
            "title": None,
            "body": body,
            "sort_order": len(info) + 1,
            "review_status": "reviewed",
            "origin_ref": SOURCES[spec["ref"]]["document_ref"],
        })

    add("machine_behavior", spec["behavior"])
    add("related_element", spec["title"])
    for item in causes:
        add("cause", item)
    for item in checks:
        add("check", item)
    if spec["profile"] in {"power", "inverter", "fan", "compressor"}:
        add("safety", "Puede existir tensión peligrosa y carga almacenada en el bus DC; solo personal cualificado debe medir con el procedimiento adecuado.")
    add("observation", f"Rearme: {spec['restart']}")
    add("observation", "Anote siempre el lugar exacto donde se visualiza el código; Haier puede traducirlo entre unidad, mando y placa exterior.")
    return {
        "id": interpretation_id,
        "title": spec["title"],
        "description": (
            f"Interpretación documentada de {spec['code']} en "
            f"{contexts[0]['display_location'].lower()}: {spec['description']}"
        ),
        "source_kind": "official",
        "confidence": "high",
        "review_status": "reviewed",
        "indication_contexts": contexts,
        "info_items": info,
        "operational_impacts": [operational_impact(spec)],
        "datasets": [dataset_for(spec, interpretation_id)],
        "sources": [source(spec["ref"], spec["page"], f"{spec['source_section']} — {spec['code']}")],
        "_aliases": split_items(spec["aliases"]),
        "_scope": spec["scope"],
    }


def build_errors() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for interpretation_id, original in enumerate(ERROR_SPECS, start=1):
        by_code[original["code"]].append(build_interpretation(interpretation_id, dict(original)))

    indexes: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    for error_id, code in enumerate(sorted(by_code, key=normalize), start=1):
        interpretations = by_code[code]
        scopes = {item.pop("_scope") for item in interpretations}
        scope = next(iter(scopes)) if len(scopes) == 1 else "system"
        alias_values = {code}
        for item in interpretations:
            alias_values.update(item.pop("_aliases"))
        aliases = [
            {"alias_display": alias, "alias_normalized": normalize(alias).replace(" ", "")}
            for alias in sorted(alias_values, key=normalize)
        ]
        indication_types = {
            row["indication_type"]
            for item in interpretations
            for row in item["indication_contexts"]
        }
        indication_type = next(iter(indication_types)) if len(indication_types) == 1 else "mixed"
        short_label = interpretations[0]["title"] if len(interpretations) == 1 else f"{len(interpretations)} interpretaciones documentadas"
        search_blob = " ".join(
            [code, short_label]
            + [row["alias_display"] for row in aliases]
            + [
                " ".join(
                    [item["title"], item["description"]]
                    + [row["body"] for row in item["info_items"]]
                    + [
                        " ".join([
                            row["code_display"], row["display_location"],
                            row["family_hint"], row["relationship"],
                        ])
                        for row in item["indication_contexts"]
                    ]
                )
                for item in interpretations
            ]
        )
        index = {
            "id": error_id,
            "code_display": code,
            "code_normalized": normalize(code).replace(" ", ""),
            "indication_type": indication_type,
            "unit_scope": scope,
            "short_label": short_label,
            "interpretation_count": len(interpretations),
            "search_text": normalize(search_blob),
        }
        indexes.append(index)
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

    ids = {row["code_normalized"]: row["id"] for row in indexes}
    for detail in details:
        for interpretation in detail["interpretations"]:
            for row in interpretation["indication_contexts"]:
                if row["code_normalized"] != detail["code_normalized"]:
                    row["related_error_id"] = ids.get(row["code_normalized"])
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


def option(value: str, label: str, effect: str, factory: bool = False) -> dict[str, Any]:
    return {
        "option_value": value,
        "option_label": label,
        "effect": effect,
        "is_factory": 1 if factory else 0,
    }


def parameter(code: str, name: str, description: str, options: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "parameter_code": code,
        "name": name,
        "description": description,
        "factory_value": next((row["option_value"] for row in options if row["is_factory"]), None),
        "options": options,
    }


TOPIC_DEFS = [
    (1, "diagnostic_access", "code-layer", "Dónde se muestra cada código", "Relación entre interior, mando, LED y placa exterior."),
    (2, "diagnostic_access", "controller-code-access", "Obtener códigos desde mandos", "YR-E17, YR-E16B y selección de unidad."),
    (3, "diagnostic_access", "outdoor-code-access", "Obtener códigos desde la placa exterior", "Display, LED, código principal y subcódigo MRV."),
    (4, "history_reset", "error-history", "Historial y borrado", "Registros actuales e históricos por unidad o grupo."),
    (5, "controllers_buses", "yr-e17", "Mando YR-E17", "Reconocimiento, cableado, errores, parámetros y funciones."),
    (6, "controllers_buses", "yr-e16b", "Mando YR-E16B", "Menú, historial, servicio, direcciones y cableado."),
    (7, "controllers_buses", "controller-communication", "Comunicación del mando", "Tres hilos A/B/C, principal/secundario y fallos 07."),
    (8, "service_modes", "forced-operation", "Marcha forzada LL/HH y emergencia", "Variantes desde mando y pulsador interior."),
    (9, "service_modes", "forced-defrost", "Desescarche forzado y AUTO restart", "Combinaciones del mando inalámbrico."),
    (10, "commissioning", "flexfit-check", "Autocomprobación FlexFit Multi", "CC, n2/n3, PS, reinicio y bypass."),
    (11, "commissioning", "mrv-trial", "Trial Operation MRV", "Condiciones previas y prueba desde la exterior."),
    (12, "configuration", "static-pressure", "Presión estática de conductos", "YR-E17, mando inalámbrico y grados."),
    (13, "configuration", "dip-settings", "DIP, ruido y ajustes de placa", "Defrost, Quiet, direcciones y opciones reconocibles."),
    (14, "drainage_overflow", "drain-sequence", "Bomba, boya y desbordamiento", "Secuencias separadas para frío/seco y calor/espera."),
    (15, "multisplit", "multi-behavior", "Multisplit: modo, puertos y alcance", "Primera demanda, cableado por puerto y continuidad."),
    (16, "mrv_network", "mrv-addressing", "MRV: direcciones y conteo", "Unidades interiores online, cantidad configurada y duplicados."),
    (17, "mrv_network", "mrv-error-response", "MRV: reintentos y alcance", "Rearmable, confirmada, advertencia sin parada y espera."),
    (18, "mrv_network", "mrv-monitor", "MRV: monitor y estado de placa", "Parámetros, códigos decimales/hex y LED."),
    (19, "component_checks", "sensors", "Sondas 10K, 23K y 50K", "Identificación de curva y comprobación."),
    (20, "component_checks", "fans-eev", "Ventiladores y válvulas EEV", "Tensiones, feedback, bobinas y bloqueo."),
    (21, "component_checks", "inverter-compressor", "Inverter, compresor y presiones", "Bus, IPM, U/V/W, CT y respuesta frigorífica."),
    (22, "technical_values", "quick-values", "Valores técnicos rápidos", "Tensiones, bomba, presiones, temperatura y cableado."),
    (23, "normal_states", "normal-behavior", "Estados normales y esperas", "Límites ambientales, retardos y secuencias."),
    (24, "service_tools_boards", "boards-and-architecture", "Placas, diagnóstico integrado y arquitectura", "Sustitución, conservación de ajustes y reconocimiento de familias."),
]


def vs(
    topic: int,
    title: str,
    recognition: str,
    system_type: str,
    unit_scope: str,
    purpose: str,
    summary: str,
    details: str,
    procedure: str,
    ref: str,
    page: str,
    source_section: str,
    *,
    warning: str = "",
    parameters: list[dict[str, Any]] | None = None,
    monitoring: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "topic": topic,
        "title": title,
        "recognition": recognition,
        "system_type": system_type,
        "unit_scope": unit_scope,
        "purpose": purpose,
        "summary": summary,
        "details": details,
        "procedure": procedure,
        "ref": ref,
        "page": page,
        "source_section": source_section,
        "warning": warning,
        "parameters": parameters or [],
        "monitoring": monitoring or [],
    }


SENSOR_CURVE = [
    {"code": "0 °C", "name": "10K / 23K / 50K", "unit": "kΩ", "notes": "30,30 / 82,691 / 1887,00"},
    {"code": "10 °C", "name": "10K / 23K / 50K", "unit": "kΩ", "notes": "19,06 / 48,314 / 1094,32"},
    {"code": "20 °C", "name": "10K / 23K / 50K", "unit": "kΩ", "notes": "12,32 / 29,21 / 654,16"},
    {"code": "25 °C", "name": "10K / 23K / 50K", "unit": "kΩ", "notes": "10,00 / 23,00 / 511,08"},
    {"code": "30 °C", "name": "10K / 23K / 50K", "unit": "kΩ", "notes": "8,16 / 18,252 / 402,24"},
    {"code": "40 °C", "name": "10K / 23K / 50K", "unit": "kΩ", "notes": "5,53 / 11,736 / 253,73"},
    {"code": "50 °C", "name": "10K / 23K / 50K", "unit": "kΩ", "notes": "3,83 / 7,728 / 163,80"},
]

MRV_RESPONSE_PARAMETERS = [
    parameter("resumable", "Avería rearmable", "Puede recuperar cuando desaparece la condición.", [
        option("1", "Rearmable", "No implica sustituir placa ni borrar memoria por sí sola.", True),
    ]),
    parameter("3/hour", "Confirmación por repetición", "Algunas protecciones se confirman tras tres actuaciones en una hora.", [
        option("3", "Tres veces en una hora", "Queda confirmada y exige corregir la causa."),
    ]),
    parameter("alarm-only", "Alarma sin parada", "El código 78 se documenta como alarma sin detener.", [
        option("78", "Falta de refrigerante", "El sistema sigue funcionando mientras muestra la alarma."),
    ]),
]


VARIANT_SPECS = [
    vs(1, "Interior E/F y LED numérico exterior",
       "Single Zone con display interior y LED1 de diagnóstico en la placa exterior.", "Single Zone", "system",
       "Relacionar dos indicaciones de la misma avería.",
       "E7 puede corresponder al 15 exterior; F1 al 2; F3 al 4; la ficha enlaza ambas capas.",
       "No todas las familias conservan la misma equivalencia. Anote el lugar de lectura antes del código.",
       "Anote código interior|Abra la exterior solo con procedimiento seguro|Anote número de LED/display exterior|Compare la equivalencia de la ficha",
       "ADVPLUS", "30", "Indoor code and outdoor LED mapping"),
    vs(1, "FlexFit: código interior distinto del exterior",
       "Multisplit/comercial con display interior o mando y display/LED en la exterior.", "FlexFit Multi/Pro", "system",
       "Evitar buscar un único código como si fuese universal.",
       "Los manuales advierten que la interior puede mostrar un código diferente del código numérico de la exterior.",
       "La ficha debe abrirse por cada punto de indicación y enlazar la avería relacionada.",
       "Fotografíe ambos códigos|Identifique quién muestra cada uno|Busque primero el código local|Siga el enlace a la placa exterior",
       "ARCTIC", "128-131", "Different indoor and outdoor codes"),
    vs(1, "MRV: decimal 29 en exterior y hexadecimal 1D en mando",
       "Sistema MRV-S con display exterior y mando cableado.", "MRV-S", "system",
       "Reconocer la traducción decimal/hexadecimal.",
       "El fallo del sensor de baja presión es 29 en la exterior y 1D en el mando.",
       "La aplicación ofrece ambas entradas para que la lista desplegable funcione desde cualquiera de las dos lecturas.",
       "Anote 1D en el mando|Compruebe el display exterior|Confirme 29|Abra cualquiera de las dos fichas enlazadas",
       "MRVODU", "63-66", "Decimal and hexadecimal error mapping"),
    vs(1, "Drenaje 08, 0C y significados repetidos",
       "Cassette MRV o FlexFit Pro con boya/bomba.", "Cassette/duct", "indoor",
       "Separar código y familia antes de diagnosticar.",
       "Cassette MRV usa 08 para drenaje; FlexFit Pro puede usar 0C, mientras otra cassette MRV usa 0C para cruce por cero.",
       "La lista muestra todas las interpretaciones cerradas para que el técnico elija la familia correcta.",
       "Anote familia y punto de indicación|Busque 08 u 0C|Revise todas las interpretaciones|Confirme boya/bomba antes de decidir",
       "MRVCAS", "33", "Repeated drain code meanings"),

    vs(2, "YR-E17: error actual e histórico de todo el grupo",
       "Mando con teclas táctiles/funciones Set, Time y pantalla con dos colon.", "YR-E17", "controller",
       "Consultar sin borrar la memoria.",
       "Mantener la tecla de avería 10 s muestra unidad decimal, error actual y error histórico en hexadecimal.",
       "«--» significa que no existe error en ese campo; b y d se representan en minúscula para no confundir con 8.",
       "Con pantalla activa mantenga la tecla de avería 10 s|Seleccione la unidad|Anote actual e histórico|Pulse la misma tecla para salir",
       "YRE17", "35", "Malfunction display"),
    vs(2, "YR-E16B: menú Error Code",
       "Mando con menú, flechas y tecla ENTER.", "YR-E16B", "controller",
       "Consultar el código actual y el historial por unidad.",
       "El menú muestra un error actual y hasta 35 errores pasados por cada unidad.",
       "Las flechas arriba/abajo eligen unidad y izquierda/derecha cambian de página.",
       "Abra Menu y seleccione Error Code|Pulse ENTER|Elija unidad con arriba/abajo|Recorra páginas con izquierda/derecha|Anote antes de borrar",
       "YRE16B", "18", "Error Code menu"),
    vs(2, "YR-E17: parámetros A-b-C-d-E-F",
       "Mando YR-E17 y grupo de interiores.", "YR-E17", "controller",
       "Consultar temperaturas, EEV y direcciones.",
       "A=Tai, b=Tc1, C=Tc2, d=apertura PMV/2, E=dirección interior hex y F=dirección central hex.",
       "La entrada exige 5 s; en cassette de cuatro vías, 10 s.",
       "Mantenga la tecla de parámetros 5 s o 10 s en cassette|Seleccione unidad|Recorra A-b-C-d-E-F|Anote valor y unidad|Salga o espere 10 s",
       "YRE17", "37-38", "Parameter inquiry"),

    vs(3, "MRV: código principal y sufijo alternados",
       "Placa exterior con display digital y LED rojo/verde.", "MRV-S", "outdoor",
       "Leer el código completo, incluido el subcódigo.",
       "El display alterna principal y sufijo durante 1 s, separados por 2 s; no debe anotarse solo la primera parte.",
       "Los LED representan decenas con rojo LED1 y unidades con verde LED3 a 2 Hz.",
       "Espere varios ciclos|Anote código principal|Anote sufijo tras el intervalo|Compare con parpadeos LED si el display no es legible",
       "MRVODU", "63-66", "Failure display method"),
    vs(3, "FlexFit Multi: display numérico de la placa",
       "Exterior multisplit con display de placa y LEDs verdes por puerto.", "FlexFit Multi", "outdoor",
       "Localizar el puerto afectado.",
       "Los códigos 1-45/Lo se leen en la exterior; un LED verde estable identifica comunicación normal de su puerto.",
       "La ausencia de LED de un puerto orienta a cable/interior antes de condenar la placa común.",
       "Anote el número del display|Observe LED de cada puerto|Compare cableado 3/C y 1|Aísle el puerto sospechoso",
       "FLEXMULTI", "22-24", "Outdoor display and port LEDs"),

    vs(4, "YR-E17: borrar actual e histórico de todas las unidades",
       "YR-E17 dentro de la pantalla de averías.", "YR-E17", "controller",
       "Borrar solo después de registrar.",
       "Tras entrar manteniendo 10 s, mantener de nuevo la tecla 5 s borra actual e histórico de todas las unidades.",
       "No existe selección de una sola unidad para ese borrado en este procedimiento.",
       "Fotografíe todos los códigos|Entre manteniendo 10 s|Mantenga de nuevo 5 s|Compruebe «--»|Repita prueba de funcionamiento",
       "YRE17", "35", "Malfunction record clearance", warning="caution"),
    vs(4, "YR-E16B: borrar una unidad o todas",
       "YR-E16B dentro de Error Code.", "YR-E16B", "controller",
       "Elegir el alcance correcto del borrado.",
       "Izquierda+derecha 5 s borra el historial de la unidad actual; arriba+abajo 5 s borra todas las unidades online.",
       "Las combinaciones solo son válidas dentro de la pantalla de errores.",
       "Guarde el historial|Seleccione la unidad si procede|Use izquierda+derecha para una unidad o arriba+abajo para todas|Verifique el resultado",
       "YRE16B", "18", "Clear error history", warning="caution"),

    vs(5, "YR-E17: red polarizada de tres hilos A/B/C",
       "Bornes A, B y C y conector CON1 en el mando.", "YR-E17", "controller",
       "Cablear sin perder polaridad ni blindaje.",
       "Usa tres conductores polarizados y admite un mando para hasta 16 interiores o dos mandos principal/secundario.",
       "El blindaje se pone a tierra solo por un extremo.",
       "Corte alimentación|Identifique A/B/C en ambos extremos|Conecte CON1|Ponga a tierra un solo extremo del blindaje|Revise principal/secundario",
       "YRE17", "47-49", "Wired controller wiring", warning="danger"),
    vs(5, "YR-E17: sección de cable según longitud",
       "Instalación de mando de 3 hilos entre 0 y 500 m.", "YR-E17", "controller",
       "Elegir sección sin generalizar.",
       "La tabla aumenta de 0,3 mm²/22 AWG por debajo de 100 m hasta 2 mm²/14 AWG entre 400 y 500 m.",
       "Es cable de tres conductores apantallado; no aplicar a otro bus Haier sin confirmar.",
       "Mida la longitud total|Seleccione la fila de la tabla|Use tres conductores apantallados|Conecte blindaje a tierra en un extremo",
       "YRE17", "48", "Communication wire size",
       parameters=[
           parameter("length", "Longitud y sección", "Sección mínima indicada para el mando YR-E17.", [
               option("<100 m", "0,3 mm² / 22 AWG", "Tres conductores apantallados.", True),
               option("100-200 m", "0,5 mm² / 20 AWG", "Tres conductores apantallados."),
               option("200-300 m", "0,75 mm² / 18 AWG", "Tres conductores apantallados."),
               option("300-400 m", "1,25 mm² / 16 AWG", "Tres conductores apantallados."),
               option("400-500 m", "2 mm² / 14 AWG", "Tres conductores apantallados."),
           ]),
       ]),
    vs(5, "YR-E17: una unidad, grupo o dos mandos",
       "Esquema A/B/C con varias interiores o mando secundario.", "YR-E17", "controller",
       "Escoger topología válida.",
       "Tres métodos: un mando para hasta 16 interiores, un mando para una interior o dos mandos para una interior.",
       "En dos mandos, uno es principal y el otro secundario; ambos conservan A/B/C.",
       "Identifique la topología|Conecte el mando a la unidad principal|Encadene las interiores según esquema|Configure principal/secundario|Compruebe comunicación",
       "YRE17", "47-48", "Controller topology"),

    vs(6, "YR-E16B: historial de 35 códigos por unidad",
       "Mando gráfico con Menu/ENTER.", "YR-E16B", "controller",
       "Aprovechar la memoria antes de intervenir.",
       "Conserva un código actual y hasta 35 pasados para cada unidad conectada.",
       "El número de unidad y las páginas permiten reconstruir si el problema migra por la red.",
       "Abra Error Code|Recorra todas las unidades|Anote actual y pasados|Ordene por unidad antes de borrar",
       "YRE16B", "18", "Error history per unit"),
    vs(6, "YR-E16B: Service Help y dirección",
       "Menú de servicio protegido.", "YR-E16B", "controller",
       "Acceder a ajustes solo cuando sea necesario.",
       "La contraseña predeterminada documentada es 841226; el menú permite dirección central y comunicación interior-exterior.",
       "Cambiar una dirección sin registrar la anterior puede dejar unidades fuera de red.",
       "Registre todas las direcciones|Entre en Service Help|Introduzca la contraseña|Modifique solo el parámetro documentado|Reinicie y compruebe unidades online",
       "YRE16B", "19, 27", "Service Help and address setting", warning="caution"),
    vs(6, "YR-E16B: cableado por CON4",
       "Mando YR-E16B con conector CON4 y red A/B/C.", "YR-E16B", "controller",
       "Distinguirlo del CON1 del YR-E17.",
       "Se conecta a CON4 mediante tres conductores; admite una interior, grupo o principal/secundario.",
       "Cassette y conductos pueden requerir instrucciones específicas de su unidad o kit.",
       "Corte alimentación|Pase el cable|Conecte A/B/C en CON4|Configure topología|Compruebe cantidad online",
       "YRE16B", "37-39", "Wired controller installation", warning="danger"),

    vs(7, "Código 07: comunicación cassette-mando",
       "Cassette MRV con mando A/B/C.", "MRV-S cassette", "indoor",
       "Separar mando, cable y placa.",
       "07 identifica la pérdida de comunicación con el mando; no equivale al 06 interior-exterior.",
       "Compruebe principal/secundario, polaridad y continuidad antes de sustituir.",
       "Verifique alimentación de la interior|Compare A/B/C extremo a extremo|Desconecte mandos secundarios|Pruebe cable/mando conocido|Valide que desaparece 07",
       "MRVCAS", "33", "Controller communication code 07"),
    vs(7, "YR-E17: comunicación perdida durante 4 minutos",
       "Mando YR-E17 sin respuesta de la unidad.", "YR-E17", "controller",
       "Entender el proceso de supervisión.",
       "El mando declara fallo de comunicación cuando no recibe intercambio durante cuatro minutos.",
       "Al consultar la avería puede mostrar 07; el problema puede ser alimentación de la interior, cable o dirección.",
       "Compruebe si la interior está alimentada|Espere el tiempo de supervisión|Revise A/B/C|Compruebe dirección y principal/secundario",
       "YRE17", "11, 35", "Controller communication supervision"),

    vs(8, "YR-E17: refrigeración forzada LL",
       "YR-E17 apagado con último modo frío.", "YR-E17", "controller",
       "Forzar una prueba sin demanda normal de termostato.",
       "Mantener ON/OFF 10 s entra en refrigeración forzada; LL parpadea y el icono de frío queda visible.",
       "ON/OFF detiene y sale; continúan las protecciones propias de la máquina.",
       "Seleccione frío y apague|Mantenga ON/OFF 10 s|Confirme LL e icono frío|Observe funcionamiento|Pulse ON/OFF para salir",
       "YRE17", "46", "Forced cooling", warning="caution"),
    vs(8, "YR-E17: calefacción forzada HH",
       "YR-E17 apagado con último modo calor.", "YR-E17", "controller",
       "Forzar prueba de calefacción.",
       "Mantener ON/OFF 10 s entra en calefacción forzada y muestra HH parpadeando.",
       "La máquina sigue considerando sus protecciones; HH no garantiza arranque si existe una seguridad activa.",
       "Seleccione calor y apague|Mantenga ON/OFF 10 s|Confirme HH|Observe presiones y temperaturas|Pulse ON/OFF para salir",
       "YRE17", "46", "Forced heating", warning="caution"),
    vs(8, "Cassette MRV: LL/HH desde ON/OFF",
       "Cassette compacta con mando cableado compatible.", "MRV-S cassette", "indoor",
       "Ejecutar prueba forzada de la unidad.",
       "Con frío o calor seleccionado, mantener ON/OFF 5 s muestra LL o HH; durante la prueba solo responden ON/OFF y temperatura.",
       "La indicación y el icono de modo parpadean.",
       "Seleccione frío o calor|Mantenga ON/OFF 5 s|Confirme LL/HH|Observe la unidad|Pulse ON/OFF para terminar",
       "MRVCAS", "30-31", "Compulsory cooling and heating", warning="caution"),
    vs(8, "Pulsador de emergencia AUTO 75 °F",
       "Unidad interior Single Zone con botón Emergency/Manual.", "Advanced Plus", "indoor",
       "Probar cuando el mando no está disponible.",
       "El pulsador inicia AUTO con consigna de 75 °F en la familia documentada.",
       "Es una marcha básica; no sustituye la lectura de códigos ni anula protecciones.",
       "Localice el pulsador de emergencia|Pulse una vez|Compruebe AUTO 75 °F|Vuelva a pulsar o use el mando para detener",
       "ADVPLUS", "9-10", "Emergency operation"),

    vs(9, "Mando inalámbrico: desescarche forzado",
       "Familia Arctic Multi con mando inalámbrico compatible.", "Arctic Multi", "controller",
       "Iniciar desescarche para comprobación.",
       "En calor, 30 °C y ventilador alto, pulse Sleep seis veces en cinco segundos; tres pitidos confirman.",
       "Solo funciona en familias compatibles y no debe repetirse sin comprobar condiciones frigoríficas.",
       "Seleccione calor 30 °C y ventilador alto|Pulse Sleep 6 veces en 5 s|Confirme 3 pitidos|Observe ciclo y finalización",
       "ARCTIC", "116-118", "Forced defrost", warning="caution"),
    vs(9, "Mando inalámbrico: AUTO restart",
       "Familia Arctic Multi con mando compatible.", "Arctic Multi", "controller",
       "Activar o desactivar el rearranque automático.",
       "Sleep diez veces en cinco segundos; cuatro pitidos habilitan y dos deshabilitan.",
       "Registre el estado porque modifica qué ocurre tras un corte de red.",
       "Ponga el mando en la condición indicada|Pulse Sleep 10 veces en 5 s|Cuente 4 o 2 pitidos|Pruebe solo si es seguro cortar alimentación",
       "ARCTIC", "116-118", "Auto restart setting", warning="caution"),

    vs(10, "FlexFit Multi: autocomprobación automática CC",
       "Exterior recién alimentada o autocomprobación reiniciada.", "FlexFit Multi", "outdoor",
       "Validar instalación y modos disponibles.",
       "Muestra CC durante 5 s; según temperatura exterior ejecuta frío y calor o solo uno, muestra n2/n3 y termina en PS si supera.",
       "Los intervalos documentados son -20 a -10 °C, -10 a 24 °C y 24 a 46 °C.",
       "Alimente todas las interiores|Observe CC|Espere la secuencia n2/n3 según ambiente|No interrumpa|Confirme PS",
       "FLEXMULTI", "6", "Start-up system check"),
    vs(10, "FlexFit Multi: reiniciar la autocomprobación",
       "Mando inalámbrico compatible, autocomprobación ya terminada.", "FlexFit Multi", "controller",
       "Repetir la prueba tras corregir una instalación.",
       "Frío, ventilador alto, 16 °C y Sleep cuatro veces en cinco segundos; cinco pitidos y CC confirman.",
       "Debe hacerse con todas las unidades correctamente alimentadas y cableadas.",
       "Seleccione frío, High y 16 °C|Pulse Sleep 4 veces en 5 s|Confirme 5 pitidos|Compruebe CC y secuencia completa",
       "FLEXMULTI", "6", "Manual restart of system check"),
    vs(10, "FlexFit Multi: bypass BP",
       "Durante los primeros cinco segundos de CC.", "FlexFit Multi", "controller",
       "Omitir la autocomprobación solo de forma consciente.",
       "Seleccione Dry a 20 °C dentro de los cinco segundos; BP confirma el bypass.",
       "El bypass no demuestra que puertos, modos y sensores estén correctos.",
       "Alimente y espere CC|Dentro de 5 s seleccione Dry 20 °C|Confirme BP|Registre que la instalación no ha sido autoverificada",
       "FLEXMULTI", "6", "System check bypass", warning="caution"),

    vs(11, "MRV: condiciones previas al Trial Operation",
       "Exterior MRV-S tras instalación o intervención.", "MRV-S", "system",
       "Evitar daños y falsos fallos durante la puesta en marcha.",
       "Aislamiento >1 MΩ, exterior alimentada al menos 12 h, calentador de cárter al menos 6 h, válvulas abiertas y todas las interiores alimentadas.",
       "El manual advierte que interiores sin alimentación pueden provocar problemas de drenaje/fuga de agua.",
       "Mida aislamiento >1 MΩ|Abra válvulas|Alimente exterior 12 h y calentador 6 h|Alimente todas las interiores|Revise direcciones y cantidad",
       "MRVODU", "49", "Trial operation prerequisites", warning="danger"),
    vs(11, "MRV: Trial Operation desde la placa exterior",
       "Sistema cuya temperatura ambiente impide una demanda normal.", "MRV-S", "outdoor",
       "Forzar prueba del circuito frigorífico.",
       "La prueba se inicia desde la exterior y permite comprobar el conjunto aunque la consigna normal no lo active.",
       "Debe vigilar códigos, presiones, temperaturas, ventiladores y retorno de condensados.",
       "Cumpla todos los requisitos previos|Seleccione Trial Operation según la placa|Observe interiores online|Registre parámetros y códigos|Salga según el procedimiento",
       "MRVODU", "49-52", "Trial operation", warning="danger"),

    vs(12, "YR-E17: Fan + Set durante 5 s",
       "Conductos compatibles con YR-E17 y grados visibles.", "YR-E17", "controller",
       "Consultar o cambiar presión estática.",
       "Fan+Set 5 s abre el ajuste; Time cambia unidad y Set confirma.",
       "El mando secundario no puede cambiar el grado; algunas familias usan 01-04 y otras más grados.",
       "Con la unidad ON mantenga Fan+Set 5 s|Seleccione unidad con Time|Cambie el grado|Pulse Set para guardar|Compruebe caudal",
       "YRE17", "39-41", "Static pressure grade"),
    vs(12, "Conductos: grados 1-10 desde mando",
       "FlexFit Pro/duct compatible con diez grados.", "FlexFit Pro duct", "controller",
       "Ajustar caudal a la red real.",
       "La familia documentada permite elegir grados 1-10; no equivalen a un único Pa universal.",
       "Antes de cambiar, mida presión externa y registre el grado de fábrica.",
       "Registre grado actual|Mida presión/caudal|Entre en ajuste|Cambie un grado|Vuelva a medir y confirme",
       "FLEXPRO", "58-61", "Static pressure setting", warning="caution"),
    vs(12, "Mando inalámbrico: selección por número de pulsaciones",
       "Conductos con método de mando inalámbrico y confirmación acústica.", "Arctic Multi duct", "controller",
       "Elegir presión estática sin mando cableado.",
       "El número de pulsaciones dentro de 12 s selecciona el grado y la unidad responde con N+1 pitidos.",
       "Anote la secuencia exacta de la familia; no improvise el número.",
       "Confirme compatibilidad|Entre en el modo de grado|Pulse N veces dentro de 12 s|Cuente N+1 pitidos|Compruebe caudal",
       "ARCTIC", "88-96", "Wireless static pressure selection"),

    vs(13, "Advanced Plus: BM2 y opciones de desescarche",
       "Placa exterior con bloque DIP BM2.", "Advanced Plus", "outdoor",
       "Conservar el ajuste de desescarche.",
       "BM2 modifica la estrategia de desescarche en la familia documentada.",
       "No copie una posición a otra placa/familia sin comparar el manual y la posición original.",
       "Corte alimentación|Fotografíe BM2|Compare tabla de la familia|Cambie solo si procede|Reinicie y observe un ciclo",
       "ADVPLUS", "26-28", "Defrost DIP settings", warning="caution"),
    vs(13, "FlexFit Multi: Quiet con SW5-8",
       "Exterior FlexFit Multi con banco SW5-8.", "FlexFit Multi", "outdoor",
       "Activar reducción de ruido.",
       "El manual documenta SW5-8 en ON para Quiet en esta variante.",
       "El modo puede reducir capacidad; no confundirlo con falta de rendimiento.",
       "Corte alimentación|Registre posiciones|Ponga SW5-8 en ON si corresponde|Reinicie|Compruebe ruido y capacidad",
       "FLEXMULTI", "7-8", "Quiet operation DIP", warning="caution"),
    vs(13, "Cassette MRV: DIP de dirección y opciones",
       "Placa interior con DIP/diales de dirección.", "MRV-S cassette", "indoor",
       "Evitar 09 y pérdida de red.",
       "La dirección interior debe ser única; los ajustes se leen al alimentar.",
       "Después de cambiar placa deben reproducirse antes de la adquisición.",
       "Corte alimentación|Anote DIP/diales|Compare con las demás interiores|Corrija duplicados|Alimente y repita adquisición",
       "MRVCAS", "27-32", "Indoor address and DIP", warning="caution"),

    vs(14, "Frío/seco con compresor en marcha",
       "Cassette o conductos con bomba interna y boya normalmente cerrada.", "Arctic Multi/FlexFit Pro", "indoor",
       "Entender por qué se para el compresor y la bomba sigue.",
       "La bomba funciona con el compresor y continúa 5 min después. Si la boya abre 5 min, se detiene el compresor, la bomba continúa y aparece el error si no cierra.",
       "Si la boya cierra, la bomba aún funciona 5 min adicionales.",
       "Compruebe agua real|Observe bomba con compresor ON|Simule solo con método seguro|Cronometre 5 min|Verifique que la bomba prolonga otros 5 min al cerrar",
       "ARCTIC", "95-96", "Drain sequence in COOL/DRY"),
    vs(14, "Calor, ventilación o espera",
       "Misma cassette/conductos fuera de frío activo.", "Arctic Multi/FlexFit Pro", "indoor",
       "Diagnosticar una boya pegada aunque la máquina esté en calor.",
       "Si la boya abre durante 2 s en espera de frío/seco o en calor/ventilación, la bomba arranca.",
       "Si cierra, la bomba continúa 5 min; si no cierra, mantiene bomba y muestra error.",
       "Ponga la unidad en calor/ventilación o espera|Compruebe estado normalmente cerrado|Observe apertura 2 s|Verifique arranque y prolongación de 5 min",
       "ARCTIC", "95-96", "Drain sequence in HEAT/FAN/standby"),
    vs(14, "Cassette MRV: CN13 y CN4",
       "Cassette compacta MRV con placa accesible.", "MRV-S cassette", "indoor",
       "Separar boya, bomba y placa.",
       "CN13 recibe la boya; CN4 entrega 220 VAC a la bomba en la variante documentada.",
       "Si la salida existe y la bomba no mueve agua, valore bomba/atasco; sin salida, compruebe boya y placa.",
       "Corte y compruebe CN13|Verifique boya normalmente cerrada|Alimente con seguridad y mida CN4|Compruebe caudal y tubería|Repita hasta que no reaparezca 08",
       "MRVCAS", "34-36", "Drain pump and float diagnosis", warning="danger"),

    vs(15, "La primera unidad decide frío o calor",
       "FlexFit Multi con varias interiores y demandas incompatibles.", "FlexFit Multi", "system",
       "Explicar por qué una unidad no arranca sin tener avería.",
       "Si la primera demanda es calor, el sistema trabaja en calor; si es frío, trabaja en frío.",
       "Las demandas incompatibles pueden quedar esperando; no cambie placas por ese comportamiento.",
       "Anote qué unidad arrancó primero|Compare modos de todas|Ponga todas en el mismo modo|Reinicie la demanda|Compruebe operación",
       "FLEXMULTI", "5-7", "Mode priority"),
    vs(15, "Puertos de comunicación deben corresponder",
       "Exterior multisplit con salidas A-E y LEDs por puerto.", "FlexFit Multi", "system",
       "Evitar códigos por cruce de tubería/cable.",
       "El cableado de cada interior debe coincidir con su puerto; no se requiere direccionamiento en esta familia.",
       "Un cruce puede simular comunicación o sonda de puerto anormal.",
       "Etiquete tubería y cable por puerto|Compare A-E|Observe LEDs verdes|Corrija cruces|Repita autocomprobación CC",
       "FLEXMULTI", "6, 22-24", "Port matching"),
    vs(15, "Avería de un puerto frente a placa común",
       "Solo una interior no comunica y las demás sí.", "FlexFit Multi", "system",
       "Aislar el alcance antes de sustituir.",
       "Si los demás LEDs de puerto quedan verdes y funcionan, el fallo puede limitarse a cable/interior/puerto.",
       "Una caída de alimentación o placa común afecta a varios puertos.",
       "Compare todos los LEDs|Intercambie solo pruebas permitidas|Revise interior y cable del puerto|Condene placa común solo con evidencia",
       "FLEXMULTI", "22-24", "Port-level communication"),

    vs(16, "MRV: 26-0, 26-1 y 26-2",
       "Exterior MRV durante adquisición o puesta en marcha.", "MRV-S", "network",
       "Interpretar el conteo de interiores.",
       "26-0: ninguna interior; 26-1: menos que la cantidad ajustada; 26-2: más.",
       "La diferencia suele orientar a alimentación, dirección, bus o cantidad configurada.",
       "Cuente interiores instaladas|Compruebe que todas tienen tensión|Compare cantidad ajustada y online|Revise direcciones|Repita adquisición",
       "MRVODU", "63-66", "Indoor quantity errors"),
    vs(16, "Cassette MRV: 09 dirección duplicada",
       "Dos interiores con la misma dirección.", "MRV-S cassette", "network",
       "Restablecer identidad única.",
       "09 identifica dirección interior duplicada.",
       "No cambie direcciones al azar: registre la red completa y el rango válido.",
       "Liste direcciones|Localice duplicado|Corte alimentación|Corrija DIP/dial|Alimente y confirme desaparición",
       "MRVCAS", "33", "Duplicated indoor address"),

    vs(17, "Protección MRV con tres reintentos por hora",
       "Códigos 30, 34, 39-x, 40, 43, 71-x o 75-x.", "MRV-S", "system",
       "Distinguir protección temporal de bloqueo confirmado.",
       "Varias protecciones reintentan tras 2-3 min y se confirman después de tres actuaciones en una hora.",
       "Anote cada repetición y el tiempo; cortar alimentación oculta la secuencia.",
       "Registre código y sufijo|Cronometre el rearme|Observe tres ciclos como máximo seguro|Corrija la causa antes de borrar",
       "MRVODU", "63-66", "Retry and confirmed failure", parameters=MRV_RESPONSE_PARAMETERS),
    vs(17, "Código 78: alarma sin parada",
       "MRV-S funcionando con 78.", "MRV-S", "system",
       "No interpretar toda alarma como parada.",
       "El manual especifica que 78 avisa de falta de refrigerante pero no detiene.",
       "El funcionamiento no confirma que la carga sea correcta; debe investigarse sin añadir gas por intuición.",
       "Registre presiones y temperaturas|Busque fugas|Compruebe EEV y sensores|Pese/corrija carga según procedimiento",
       "MRVODU", "65", "Refrigerant shortage alarm without stop"),
    vs(17, "Códigos 555.x: espera, no avería de placa",
       "Exterior MRV muestra 555.0, 555.1 o 555.3.", "MRV-S", "system",
       "Reconocer una condición de standby.",
       "555.0 es combinación de capacidad 50-130 %; 555.1/555.3 son límites ambientales de calor/frío.",
       "La máquina volverá cuando la combinación o ambiente sean válidos.",
       "Anote subcódigo|Compruebe suma de capacidades o Ta|Espere condición válida|No sustituya componentes por 555 aislado",
       "MRVODU", "66", "Standby codes"),

    vs(18, "MRV: LED rojo decenas y verde unidades",
       "Display ilegible pero LED1 rojo y LED3 verde visibles.", "MRV-S", "outdoor",
       "Recuperar el código por parpadeos.",
       "Rojo LED1 indica decenas y verde LED3 unidades; parpadean a 2 Hz y separan códigos por 2 s.",
       "Para subcódigos use el display digital si está disponible.",
       "Cuente rojo|Cuente verde|Espere intervalo|Repita tres veces|Compare con display",
       "MRVODU", "63-66", "LED failure indication"),
    vs(18, "MRV: monitor de presiones, temperaturas y estado",
       "Placa exterior con menú de consulta.", "MRV-S", "outdoor",
       "Comparar lo que calcula la placa con instrumentos.",
       "El monitor permite revisar sensores, presiones, compresor, EEV, ventiladores y cantidad de interiores.",
       "Un valor plausible no demuestra que el sensor sea exacto; compare tendencia y medida física.",
       "Registre estado antes de cambiar nada|Recorra parámetros|Compare presión con manómetro|Compare temperatura con termómetro|Guarde resultados",
       "MRVODU", "52-62", "Outdoor parameter monitor",
       monitoring=[
           {"code": "Ta/Ts/Td/Te", "name": "Temperaturas exteriores", "unit": "°C", "notes": "Comparar con medida física."},
           {"code": "Pd/Ps", "name": "Alta y baja presión", "unit": "MPa", "notes": "Comparar con manómetro."},
           {"code": "Fan/EEV/Hz", "name": "Actuadores y compresor", "unit": "estado", "notes": "Relacionar orden y respuesta."},
           {"code": "IDU qty", "name": "Interiores online/configuradas", "unit": "unidades", "notes": "Base de 26-0/1/2."},
       ]),

    vs(19, "Elegir la curva correcta: 10K, 23K o 50K",
       "Haier Arctic Multi con sondas de varias familias.", "Arctic Multi", "system",
       "Evitar condenar una sonda sana por usar la tabla incorrecta.",
       "El manual reúne curvas nominales 10K, 23K y 50K; a 25 °C son 10,00 kΩ, 23,00 kΩ y 511,08 kΩ respectivamente.",
       "La sonda de descarga de alta temperatura no se comporta como una NTC 50K a 25 °C convencional; use la tabla oficial mostrada.",
       "Desconecte la sonda con tensión cortada|Mida temperatura real|Mida resistencia|Compare las tres curvas|Confirme por ubicación y manual",
       "ARCTIC", "119-122", "Thermistor resistance charts", monitoring=SENSOR_CURVE),
    vs(19, "Tabla rápida NTC por temperatura",
       "Sonda fuera de la máquina o accesible en conector.", "Arctic Multi", "system",
       "Comparar varios puntos, no solo 25 °C.",
       "La ficha incorpora valores a 0, 10, 20, 25, 30, 40 y 50 °C para las tres curvas documentadas.",
       "Una sonda puede coincidir en un punto y desviarse en otros; caliéntela/enfríela lentamente.",
       "Mida a temperatura estable|Compare al menos dos puntos|Observe cambio continuo|Sustituya solo si curva o aislamiento son anormales",
       "ARCTIC", "119-122", "Thermistor resistance charts", monitoring=SENSOR_CURVE),

    vs(20, "Ventilador exterior FlexFit: potencia, orden y feedback",
       "Motor exterior con colores rojo, negro, blanco, amarillo y azul.", "FlexFit Multi", "outdoor",
       "Separar motor y placa.",
       "310-334 V rojo-negro, 15 V blanco-negro, 4 V amarillo-negro de orden; azul-negro aproximadamente 8 V en marcha y 14 V parado.",
       "Es una variante concreta y existe tensión peligrosa incluso sin giro.",
       "Corte y compruebe giro|Identifique colores|Alimente con protección|Mida potencia y 15 V|Compare orden amarillo y feedback azul",
       "FLEXMULTI", "19", "Outdoor DC fan diagnosis", warning="danger"),
    vs(20, "Ventilador exterior Advanced Plus: señales",
       "Motor de seis hilos/pines de la familia Advanced Plus.", "Advanced Plus", "outdoor",
       "Comprobar el circuito de ventilador.",
       "La guía documenta aproximadamente 310 V en potencia, 15 V de control y señales variables 0-6/0-5 V según pines.",
       "Confirme pinout exacto antes de medir; no lo mezcle con el código de colores FlexFit.",
       "Desenergice y localice pinout|Compruebe giro|Mida potencia y 15 V|Mida orden/feedback|Compare con estado de marcha",
       "ADVPLUS", "32", "Outdoor fan motor diagnosis", warning="danger"),
    vs(20, "EEV de 46 Ω o 92 Ω",
       "Válvula electrónica FlexFit con bobina desmontable.", "FlexFit Multi", "outdoor",
       "Escoger la tabla de bobina correcta.",
       "El manual contiene variantes de 46 Ω y 92 Ω según válvula/conexión.",
       "No use un único valor para todas las EEV; compare fases y la tabla de la válvula instalada.",
       "Corte alimentación|Identifique conector y válvula|Mida bobinados por pares|Compare equilibrio y tabla 46/92 Ω|Revise correspondencia de puerto",
       "FLEXMULTI", "21", "EEV coil resistance"),

    vs(21, "IPM-placa: fuentes 5 V y 15 V",
       "Advanced Plus con módulo separado y conector de control.", "Advanced Plus", "outdoor",
       "Comprobar alimentación antes de cambiar el módulo.",
       "Aproximadamente 5 V entre pines 1-2 y 15 V entre 2-3 en el conector documentado.",
       "La ausencia puede proceder de la placa principal o de un corto en el módulo/cable.",
       "Descargue el bus|Desconecte/revise cable|Alimente con seguridad|Mida 5 V y 15 V|Aísle módulo si el procedimiento lo permite",
       "ADVPLUS", "34", "IPM-main board communication", warning="danger"),
    vs(21, "Compresor U/V/W y pérdida de sincronismo",
       "Códigos F11/F27/F28 o 18/24.", "Single Zone/FlexFit", "outdoor",
       "Separar compresor bloqueado de inverter.",
       "Compare resistencias U-V, V-W y W-U, aislamiento y presión antes del arranque.",
       "No meguee a través del inverter y no manipule hasta descargar el bus.",
       "Corte y descargue|Desconecte U/V/W|Compare resistencias|Compruebe aislamiento según manual|Mida presiones y un intento controlado",
       "ADVPLUS", "36-43", "Compressor and inverter diagnosis", warning="danger"),
    vs(21, "MRV: presión y relación de compresión",
       "Códigos 39-x, 40, 43 o 75-x.", "MRV-S", "outdoor",
       "Usar umbrales y tiempos de detección.",
       "Baja: 0,05 MPa en frío o 0,03 MPa en calor/aceite; alta: 4,15 MPa; relación alta >8 y baja <1,8.",
       "Los códigos 75-x comprueban que Pd-Ps aumente al arrancar.",
       "Mida Pd y Ps reales|Compare con monitor|Cronometre 5 min cuando aplique|Revise EEV, válvulas, carga y compresor",
       "MRVODU", "63-66", "Pressure protection thresholds", warning="danger"),

    vs(22, "Single Zone: alimentación y comunicación 1-2-3",
       "Bornero interior/exterior con 1, 2, 3 y tierra.", "Advanced Plus", "system",
       "Distinguir potencia y datos.",
       "1 y 2 suministran alimentación a la interior; 3 es comunicación. El manual documenta 240 VAC entre 1(N) y 2(L).",
       "Un empalme o corte en 3 provoca E7 aunque la interior tenga alimentación.",
       "Compare numeración extremo a extremo|Mida 1-2 con seguridad|Revise continuidad de 3 sin tensión|Elimine empalmes y compruebe E7",
       "ADVPLUS", "15-18", "Power and communication terminals", warning="danger"),
    vs(22, "Cassette MRV: bomba a 220 VAC",
       "Bomba conectada a CN4 y boya a CN13.", "MRV-S cassette", "indoor",
       "Medir el circuito de drenaje.",
       "CN4 entrega AC 220 V en esta variante; CN13 recibe el contacto de boya.",
       "No aplicar este valor a bombas de baja tensión de otras marcas o familias.",
       "Identifique CN4/CN13|Compruebe boya sin tensión|Alimente y mida CN4 con protección|Compruebe caudal",
       "MRVCAS", "34-36", "Drain electrical values", warning="danger"),
    vs(22, "MRV: requisitos eléctricos de Trial Operation",
       "Puesta en marcha tras instalación.", "MRV-S", "system",
       "Recordar mínimos antes de arrancar.",
       "Aislamiento >1 MΩ, exterior alimentada 12 h y calentador de cárter al menos 6 h.",
       "No intentar compresor sin precalentamiento suficiente.",
       "Mida aislamiento|Compruebe tiempo de alimentación|Verifique calentador|Abra válvulas|Autorice Trial Operation",
       "MRVODU", "49", "Electrical prerequisites", warning="danger"),

    vs(23, "Lo: límite de temperatura exterior",
       "FlexFit Multi muestra Lo.", "FlexFit Multi", "outdoor",
       "Distinguir límite de ambiente de avería.",
       "Lo indica detección de ambiente bajo para la operación solicitada.",
       "La unidad debe recuperar cuando vuelva al rango; confirme que Ta es coherente.",
       "Mida temperatura exterior|Compare lectura Ta|Espere rango permitido|Investigue la sonda si la lectura no coincide",
       "FLEXMULTI", "22", "Low ambient status"),
    vs(23, "555.1/555.3: espera por ambiente MRV",
       "MRV-S con código 555.x.", "MRV-S", "system",
       "Evitar cambiar componentes por standby.",
       "555.1 limita calor por Ta >27 °C; 555.3 limita frío por Ta >54 °C o <-10 °C.",
       "Son estados de espera mientras la condición persiste.",
       "Anote subcódigo|Compruebe Ta real y del monitor|Espere rango válido|Verifique recuperación",
       "MRVODU", "66", "Ambient standby"),
    vs(23, "Bomba sigue cinco minutos",
       "Cassette/duct tras parar compresor o cerrar boya.", "Arctic Multi/FlexFit Pro", "indoor",
       "Reconocer funcionamiento normal de drenaje.",
       "La bomba continúa cinco minutos tras Thermal OFF y cinco minutos después de cerrar la boya.",
       "No es un relé pegado si se cumple el tiempo y se detiene.",
       "Cronometre desde Thermal OFF|Escuche/observe bomba|Espere 5 min|Investigue solo si supera la secuencia",
       "ARCTIC", "95-96", "Normal pump overrun"),
    vs(23, "Retardo y protecciones siguen activas en marcha forzada",
       "LL/HH o prueba exterior.", "Haier service modes", "system",
       "No confundir forzado con anulación de seguridades.",
       "La marcha forzada elimina la demanda normal de termostato, pero las protecciones de presión, temperatura, corriente y comunicación pueden impedir o detener.",
       "Un compresor que no arranca en LL/HH aún puede estar protegido.",
       "Anote LL/HH|Espere retardos|Observe códigos|No puentee protecciones|Salga y diagnostique la causa",
       "YRE17", "46", "Protection behavior during forced operation"),

    vs(24, "Después de sustituir una placa: copiar ajustes",
       "Placa interior/exterior con DIP, diales, capacidad o direcciones.", "Haier", "system",
       "Evitar EEPROM, modelo, dirección o cantidad incorrectos.",
       "Fotografíe DIP/diales/direcciones antes de retirar; repóngalos en la placa compatible y repita adquisición/prueba.",
       "Una placa nueva sin configurar puede crear códigos distintos a la avería original.",
       "Registre referencias y ajustes|Corte y descargue|Monte placa compatible|Reproduzca ajustes|Alimente y repita CC/Trial Operation",
       "MRVODU", "33-49", "Board replacement and commissioning", warning="danger"),
    vs(24, "Diagnóstico integrado de la placa MRV",
       "Exterior MRV-S con display y botones.", "MRV-S", "outdoor",
       "Usar historial, monitor y Trial antes de cambiar piezas.",
       "La placa permite leer código/sufijo, parámetros, unidades online y ejecutar prueba.",
       "El orden recomendado es registrar, medir, aislar y solo después modificar.",
       "Registre códigos completos|Consulte monitor|Compare instrumentos|Revise red/cantidad|Ejecute Trial solo si es seguro",
       "MRVODU", "49-66", "Integrated board diagnostics"),
    vs(24, "Cómo reconocer la familia antes de abrir una ficha",
       "Técnico sin modelo exacto pero con la máquina delante.", "Haier", "system",
       "Reducir interpretaciones sin pedir datos tediosos.",
       "Single Zone suele mostrar E/F interior y LED exterior; FlexFit Multi usa puertos A-E y códigos numéricos; MRV usa display con sufijos y red de interiores.",
       "Cassette/conductos añaden bomba, boya y mando cableado A/B/C.",
       "Identifique tipo de equipo|Anote dónde aparece el código|Observe placa/puertos/mando|Elija la interpretación con rasgos coincidentes",
       "FLEXMULTI", "5-24", "System family recognition"),
]


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

    for variant_id, spec in enumerate(VARIANT_SPECS, start=1):
        instructions = split_items(spec["procedure"])
        steps = []
        for index, instruction in enumerate(instructions, start=1):
            phase = "prepare" if index == 1 else "procedure"
            if index == len(instructions):
                phase = "verify"
            steps.append(step(
                phase,
                index,
                instruction,
                warning="danger" if spec["warning"] == "danger" else "none",
            ))
        sections = [
            section("recognition", "Cómo reconocer esta variante", spec["recognition"], True),
            section("technical", "Qué hace o tiene en cuenta la máquina", spec["details"]),
        ]
        if spec["warning"]:
            sections.append(section(
                "warning",
                "Advertencia",
                (
                    "Procedimiento con riesgo eléctrico, mecánico o frigorífico; debe realizarlo personal cualificado."
                    if spec["warning"] == "danger"
                    else "Registre el estado inicial y no cambie ajustes sin comprender su efecto."
                ),
            ))
        topics[spec["topic"]]["variants"].append({
            "id": variant_id,
            "topic_id": spec["topic"],
            "title": spec["title"],
            "recognition": spec["recognition"],
            "system_type": spec["system_type"],
            "unit_scope": spec["unit_scope"],
            "refrigerant": None,
            "purpose": spec["purpose"],
            "summary": spec["summary"],
            "source_kind": "official",
            "review_status": "reviewed",
            "sort_order": variant_id,
            "visible": 1,
            "sections": sections,
            "steps": steps,
            "parameters": spec["parameters"],
            "controller": None,
            "monitoring_points": spec["monitoring"],
            "media": [],
            "sources": [source(spec["ref"], spec["page"], spec["source_section"])],
        })
    return list(topics.values())


def synonyms(value: str) -> str:
    replacements = {
        "DRENAJE": "BOYA FLOTADOR BOMBA CONDENSADOS WATER LEVEL OVERFLOW",
        "BOYA": "FLOTADOR FLOAT SWITCH NIVEL AGUA DRENAJE",
        "MANDO": "CONTROL REMOTO WIRED CONTROLLER",
        "MARCHA FORZADA": "FORCED COOLING FORCED HEATING LL HH TEST RUN",
        "AUTOCOMPROBACION": "SYSTEM CHECK COMMISSIONING CC PS",
        "PRESION ESTATICA": "ESP CONDUCTOS CAUDAL STATIC PRESSURE",
        "COMUNICACION": "BUS DATOS TRANSMISION",
        "HISTORIAL": "HISTORY ERROR RECORD",
        "DESESCARCHE": "DEFROST",
        "FALTA DE REFRIGERANTE": "LEAK REFRIGERANT SHORTAGE FUGA",
        "MRV": "VRF AIRSTAGE SISTEMA CENTRALIZADO",
        "VALVULA ELECTRONICA": "EEV PMV EXPANSION VALVE",
        "RUIDO": "QUIET LOW NOISE",
        "PLACA": "PCB BOARD",
        "PUESTA EN MARCHA": "COMMISSIONING TRIAL OPERATION STARTUP",
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
                    str(row.get("parameter_code") or ""),
                    str(row.get("name") or ""),
                    str(row.get("description") or ""),
                    " ".join(
                        " ".join([
                            str(opt.get("option_value") or ""),
                            str(opt.get("option_label") or ""),
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
                item["title"],
                item["recognition"],
                item["purpose"],
                item["summary"],
                " ".join(row["body"] for row in item["sections"]),
                " ".join(row["instruction"] for row in item["steps"]),
                parameter_text,
                monitoring_text,
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
        titles = [row["title"] for row in detail["interpretations"]]
        body = " ".join(
            [index["search_text"]]
            + [
                " ".join(
                    [row["title"], row["description"]]
                    + [item["body"] for item in row["info_items"]]
                    + [
                        " ".join([
                            dataset["name"],
                            dataset.get("notes") or "",
                            " ".join(str(point.get("value_text") or "") for point in dataset["points"]),
                        ])
                        for dataset in row["datasets"]
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
            "summary": (
                "Incluye: " + "; ".join(titles)
                if len(titles) > 1
                else detail["interpretations"][0]["description"]
            ),
            "haystack": normalize(synonyms(body)),
        })
    return entries


def main() -> int:
    expected = (ROOT / "data" / "brands" / "haier").resolve()
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
        for source_id, row in enumerate(SOURCES.values(), start=1)
    ])

    coverage_notes = {
        "errors": "Single Zone, FlexFit Multi/Pro, cassette y MRV-S con códigos repetidos separados por capa de indicación.",
        "diagnostic_access": "YR-E17, YR-E16B, display/LED exterior, subcódigos MRV y equivalencia decimal/hexadecimal.",
        "history_reset": "Error actual, histórico YR-E17 y hasta 35 registros por unidad YR-E16B.",
        "service_modes": "LL/HH, emergencia, desescarche forzado, AUTO restart y System Check.",
        "configuration": "Presión estática, DIP de desescarche/Quiet, direcciones y ajustes tras sustituir placas.",
        "controllers_buses": "Tres hilos polarizados A/B/C, CON1/CON4, grupos de hasta 16 interiores y principal/secundario.",
        "drainage_overflow": "Secuencia de 5 min en frío, detección de 2 s en calor/espera, CN13 y CN4 220 VAC.",
        "commissioning": "FlexFit CC/n2/n3/PS/BP y MRV Trial Operation con precalentamiento.",
        "multisplit": "Prioridad por primera demanda, puertos A-E, LEDs de comunicación y alcance por unidad.",
        "mrv_network": "Conteo 26-x, dirección duplicada, reintentos, código 78 sin parada y estados 555.x.",
        "component_checks": "Sondas, ventiladores, EEV, IPM, compresor, CT y presiones.",
        "technical_values": "Curvas 10K/23K/50K, motores, fuentes IPM, comunicación 1-2-3 y umbrales MRV.",
        "normal_states": "Lo, 555.x, prolongación de bomba y protecciones durante LL/HH.",
        "service_tools_boards": "Monitor integrado MRV, conservación de DIP/diales/direcciones y reconocimiento de arquitectura.",
        "system_architecture": "Reconocimiento por punto de indicación, placa, puertos, mando y sistema.",
    }
    write_json(WEB_DIR / "coverage.json", [
        {
            "id": category_id,
            "brand_id": BRAND_ID,
            "area_slug": slug,
            "area_name": name,
            "equipment_scope": "Haier — corpus Referencia V1",
            "coverage_status": "reference_v1",
            "source_count": len(SOURCES),
            "notes": coverage_notes[slug],
            "last_reviewed": now[:10],
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
            "reference_brand": "Haier",
            "verification_warning": (
                "Completa respecto al corpus Haier Referencia V1. Confirme siempre familia, "
                "unidad o mando que muestra el código y forma de indicación."
            ),
        },
        "categories": navigation_categories,
    })
    brand = {
        "slug": "haier",
        "name": "Haier",
        "display_name": "Haier",
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
            "Haier Referencia V1: Advanced Plus, Arctic Multi, FlexFit Multi/Pro, "
            "MRV-S, cassette y mandos YR-E17/YR-E16B. Distingue códigos de unidad, "
            "mando y placa. Sin PDF ni capturas de manuales."
        ),
    }
    write_json(BRAND_DIR / "brand.json", brand)

    from audit_brand_quality import audit_brand

    quality = audit_brand(BRAND_DIR)
    write_json(WEB_DIR / "quality.json", quality)
    print(json.dumps({
        "brand": "haier",
        "counts": counts,
        "interpretations": quality["errors"]["interpretations"],
        "error_quality": quality["errors"]["status_counts"],
        "variant_quality": quality["technical_variants"]["status_counts"],
        "sources": len(SOURCES),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
