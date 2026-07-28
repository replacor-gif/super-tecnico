#!/usr/bin/env python3
"""Construye Samsung Referencia V1 para Super Técnico.

Publica resúmenes técnicos trazables. No copia PDF, capturas ni bases privadas.
La capa de pilotos exteriores se mantiene separada por familia de placa.
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
BRAND_DIR = ROOT / "data" / "brands" / "samsung"
WEB_DIR = BRAND_DIR / "web"
BRAND_ID = 9


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
    "SMART": {
        "title": "Smart Whisper RAC Service Manual",
        "document_ref": "SAMSUNG-RAC-SMART-WHISPER-SM-2016",
        "source_url": "https://s3.amazonaws.com/samsung-files/Tech_Files/RAC/Smart_Whisper_AR_KSWSJWK/Service_Manual/Service_Manual_AR09_12_18_24KSWSJWKNCV_2%202016.pdf",
        "type": "service_manual",
        "year": "2016",
    },
    "MAX": {
        "title": "Max Heat RAC Service Manual",
        "document_ref": "SAMSUNG-RAC-MAX-HEAT-SM",
        "source_url": "https://s3.amazonaws.com/samsung-files/Tech_Files/RAC/MaxHeat_AR_KSWSPWK_AR_MSWSPWK/Service_Manual/SERVICE_MANUAL_AR18_24_NSWSPWKCV_MAX%20HEat%20RAC.pdf",
        "type": "service_manual",
        "year": "s. f.",
    },
    "FJM": {
        "title": "Free Joint Multi Service Manual",
        "document_ref": "SAMSUNG-FJM-SM-20180322B",
        "source_url": "https://s3.amazonaws.com/samsung-files/Tech_Files/FJM/Service%20Manual/FJM_Service_Manual_AA_03222018B.pdf",
        "type": "service_manual",
        "year": "2018",
    },
    "ECO": {
        "title": "DVM S Eco Heat Recovery Service Manual",
        "document_ref": "AC-00216E-1-180323",
        "source_url": "https://s3.amazonaws.com/samsung-files/Tech_Files/DVM/DVM%20S/Service%20Manuals/DVM%20S%20ECO%20HR_SERVICE%20MANUAL_AC-00216E_1_180323.pdf",
        "type": "service_manual",
        "year": "2018",
    },
    "IDU": {
        "title": "DVM S Indoor Unit Service Manual",
        "document_ref": "AC-00015E-9-161006",
        "source_url": "https://s3.amazonaws.com/samsung-files/Tech_Files/DVM/DVM%20S/Service%20Manuals/DVM%20S%20Indoor%20Unit%20Service%20Manual_AM054JNHDCH%20included_AC-00015E_9_161006.pdf",
        "type": "service_manual",
        "year": "2016",
    },
    "TRAIN1": {
        "title": "DVM S Advanced Service and Troubleshooting — Part I",
        "document_ref": "DVM-S-ADV-SERVICE-PT-I-REV-2.2",
        "source_url": "https://res.cloudinary.com/govimg/image/upload/v1556721192/5b294f9467c0d0489028b276/DVMS%20Adv%20Serv%20and%20%20Trble%20Pt%20I%20Rev%202.2%20%281%29.pdf",
        "type": "training_manual",
        "year": "2019",
    },
    "TRAIN2": {
        "title": "DVM S Advanced Service and Troubleshooting — Part II",
        "document_ref": "DVM-S-ADV-SERVICE-PT-II-REV-2",
        "source_url": "https://res.cloudinary.com/govimg/image/upload/v1556721190/5b294f9467c0d0489028b276/DVMS%20Adv%20Serv%20and%20%20Trble%20Pt%20II%20Rev%202%20handout.pdf",
        "type": "training_manual",
        "year": "2019",
    },
    "QUICK": {
        "title": "DVM S Heat Pump/Heat Recovery Quick Reference Guide",
        "document_ref": "DVM-S-HPHR-QUICK-REFERENCE-V1",
        "source_url": "https://res.cloudinary.com/govimg/image/upload/v1576528827/5b294f9467c0d0489028b276/DVMS%20HPHR%20QuickReferenceGuideFinalv1.pdf",
        "type": "quick_reference",
        "year": "2019",
    },
    "S2": {
        "title": "DVM S2 Technical Data Book",
        "document_ref": "SAMSUNG-DVM-S2-TDB",
        "source_url": "https://partnerhub.samsung.com/sfc/servlet.shepherd/document/download/0692y000007uZjWAAU",
        "type": "technical_data_book",
        "year": "2021",
    },
    "FAQ": {
        "title": "Samsung HVAC FAQs for Industry Professionals",
        "document_ref": "SAMSUNG-HVAC-FAQ",
        "source_url": "https://www.samsunghvac.com/faq",
        "type": "official_web",
        "year": "actualizado",
    },
    "SUPPORT": {
        "title": "Samsung Support — códigos de error de aire acondicionado",
        "document_ref": "SAMSUNG-SUPPORT-AC-ERROR-CODES",
        "source_url": "https://www.samsung.com/mx/support/home-appliances/error-codes-in-air-conditioning/",
        "type": "official_web",
        "year": "actualizado",
    },
    "VRFCODER": {
        "title": "Samsung HVAC VRF Coder Service Support Software",
        "document_ref": "SAMSUNG-HVAC-VRF-CODER",
        "source_url": "https://www.samsunghvac.com/Software-Downloads/VRF_Coder",
        "type": "official_web",
        "year": "actualizado",
    },
    "SOFTWARE": {
        "title": "Samsung HVAC Service Software",
        "document_ref": "SAMSUNG-HVAC-SOFTWARE",
        "source_url": "https://www.samsunghvac.com/Downloads/software",
        "type": "official_web",
        "year": "actualizado",
    },
}


def source(ref: str, page: str, section: str) -> dict[str, Any]:
    row = SOURCES[ref]
    return {
        "title": row["title"],
        "document_ref": row["document_ref"],
        "source_url": row["source_url"],
        "page_start": page,
        "page_end": page,
        "section": section,
    }


CATEGORIES = [
    (1, "errors", "Errores y protecciones", "Códigos E, U, estados y subcódigos, separados por punto de indicación."),
    (2, "outdoor_led_diagnostics", "Pilotos y display de la unidad exterior", "Tablas visuales de LED amarillo, verde, rojo/naranja y displays de placa."),
    (3, "diagnostic_access", "Obtención de códigos y subcódigos", "Lectura desde mando, receptor, display interior, placa exterior y software."),
    (4, "history_reset", "Historial y borrado", "Consulta de errores actuales, históricos y reinicio de controladores o placas."),
    (5, "service_modes", "Modos de servicio", "Test Run, Auto Trial, pump down, pump out, vacío, desescarche y retorno de aceite."),
    (6, "configuration", "Configuración y programación", "Option codes, DIP, selectores, funciones de mando y ajustes exteriores."),
    (7, "controllers_buses", "Mandos y buses", "Mandos de dos/cuatro terminales, F1-F2, F3-F4, R1-R2 y tensiones."),
    (8, "drainage_overflow", "Drenaje y desbordamiento", "Bomba, boya, detección E153 y comportamiento de cassette/conductos."),
    (9, "commissioning", "Puesta en marcha", "Tracking, direccionamiento, pipe check y Auto Trial Operation."),
    (10, "multisplit", "FJM y multisplit", "Cantidad de interiores, diales, puertos, pipe check y alcance de las averías."),
    (11, "dvm_network", "DVM/VRF y red", "Direcciones, MCU, PBA internas, comunicación y respuesta del sistema."),
    (12, "component_checks", "Comprobación de componentes", "Sondas, ventiladores, EEV, compresor, inverter, presiones y placas."),
    (13, "technical_values", "Valores técnicos", "Tensiones, resistencias, sensores, buses, motores y umbrales."),
    (14, "normal_states", "Comportamientos normales", "dF, CF, CI, UP, retardos y límites que no implican necesariamente avería."),
    (15, "service_tools_boards", "Herramientas y placas", "SNET Pro, VRF Coder, inverter checker y programación tras sustituir PBA."),
    (16, "system_architecture", "Arquitectura de sistemas", "Pistas para reconocer RAC, FJM, CAC, DVM S/S2, MCU e interiores."),
]

CATEGORY_BY_SLUG = {
    slug: {"id": ident, "slug": slug, "name": name, "description": description}
    for ident, slug, name, description in CATEGORIES
}


def leds(yellow: str, green: str, red: str, red_label: str = "Rojo") -> list[dict[str, str]]:
    return [
        {"label": "Amarillo", "color": "yellow", "state": yellow},
        {"label": "Verde", "color": "green", "state": green},
        {"label": red_label, "color": "orange" if red_label == "Naranja" else "red", "state": red},
    ]


def led_row(code: str, meaning: str, y: str, g: str, r: str, family: str) -> dict[str, Any]:
    return {
        "code_display": code,
        "indication_type": "outdoor_led",
        "display_location": "placa de la unidad exterior",
        "family_hint": family,
        "relationship": meaning,
        "led_indicators": leds(y, g, r),
        "counting_rule": "Compare los tres estados simultáneamente; no cuente destellos salvo que la placa use una secuencia numerada.",
        "cycle_note": "Observe al menos un ciclo completo y diferencie fijo, apagado y parpadeando.",
        "sequence": "Orden físico documentado: amarillo (YEL), verde (GRN), rojo (RED).",
    }


LED_9_12 = [
    led_row("Estado", "Sin alimentación o VDD anormal", "off", "off", "off", "RAC Smart Whisper 9K/12K"),
    led_row("Estado", "Reset al alimentar, aproximadamente 1 segundo", "on", "on", "on", "RAC Smart Whisper 9K/12K"),
    led_row("Estado", "Funcionamiento normal", "off", "blink", "on", "RAC Smart Whisper 9K/12K"),
    led_row("E101 / E102", "Comunicación interior-exterior anormal; el manual muestra dos patrones según el estado de enlace", "off", "off", "on", "RAC Smart Whisper 9K/12K"),
    led_row("E101 / E102", "Comunicación interior-exterior anormal; segunda condición documentada", "off", "on", "on", "RAC Smart Whisper 9K/12K"),
    led_row("E464", "Sobrecorriente IPM", "off", "off", "blink", "RAC Smart Whisper 9K/12K"),
    led_row("E461", "Fallo de arranque del compresor", "off", "blink", "off", "RAC Smart Whisper 9K/12K"),
    led_row("E470", "EEPROM sin datos", "off", "on", "off", "RAC Smart Whisper 9K/12K"),
    led_row("E466 / E483 / E484", "Bus DC bajo/alto, PFC sobrecargado o protección HW de sobretensión", "off", "on", "blink", "RAC Smart Whisper 9K/12K"),
    led_row("E221", "Sonda de ambiente exterior", "blink", "off", "blink", "RAC Smart Whisper 9K/12K"),
    led_row("E416", "Temperatura de descarga excesiva", "blink", "off", "on", "RAC Smart Whisper 9K/12K"),
    led_row("E251", "Sonda de descarga", "blink", "blink", "off", "RAC Smart Whisper 9K/12K"),
    led_row("E468 / E474 / E485", "Sensor de corriente, disipador o corriente de entrada", "blink", "blink", "on", "RAC Smart Whisper 9K/12K"),
    led_row("E465 / E500", "Límite V/I del compresor o sobretemperatura del disipador", "blink", "on", "off", "RAC Smart Whisper 9K/12K"),
    led_row("E231", "Sonda de condensación exterior", "blink", "on", "blink", "RAC Smart Whisper 9K/12K"),
    led_row("E203 / E205", "Tiempo agotado entre micom principal e inverter", "blink", "on", "on", "RAC Smart Whisper 9K/12K"),
    led_row("E458", "Ventilador exterior", "on", "off", "off", "RAC Smart Whisper 9K/12K"),
    led_row("E471", "EEPROM entre micom principal e inverter / OTP según generación", "on", "off", "blink", "RAC Smart Whisper 9K/12K"),
    led_row("E467", "Cable de compresor ausente o error de rotación", "on", "off", "on", "RAC Smart Whisper 9K/12K"),
    led_row("E440 / E441", "Operación inhibida por temperatura exterior", "on", "blink", "off", "RAC Smart Whisper 9K/12K"),
    led_row("E469 / E488", "Sensor de tensión DC-link o tensión de entrada AC", "on", "blink", "blink", "RAC Smart Whisper 9K/12K"),
    led_row("E462", "Límite de corriente de entrada / PFC", "on", "blink", "on", "RAC Smart Whisper 9K/12K"),
    led_row("E554 / E422", "Fuga de gas o EEV/válvula cerrada en autodiagnóstico", "on", "on", "off", "RAC Smart Whisper 9K/12K"),
    led_row("Test frío", "Funcionamiento de prueba en refrigeración", "off", "blink", "blink", "RAC Smart Whisper 9K/12K"),
    led_row("Test calor", "Funcionamiento de prueba en calefacción", "blink", "blink", "blink", "RAC Smart Whisper 9K/12K"),
]


LED_18_30 = [
    led_row("Estado", "Sin alimentación o VDD anormal", "off", "off", "off", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E464", "Sobrecorriente IPM", "off", "off", "blink", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E101 / E102", "Comunicación serie anormal entre display interior y exterior", "off", "off", "on", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E101 / E102", "Segunda condición de comunicación serie anormal", "off", "on", "on", "RAC Smart Whisper 18K/24K/30K"),
    led_row("Estado", "Funcionamiento normal", "off", "blink", "on", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E461", "Fallo de arranque del compresor", "off", "blink", "off", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E466 / E483 / E484", "Bus DC bajo/alto, sobrecarga PFC o protección HW", "off", "on", "blink", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E221", "Sonda de ambiente exterior", "blink", "off", "blink", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E416", "Temperatura de descarga excesiva", "blink", "off", "on", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E251", "Sonda de descarga", "blink", "blink", "off", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E468 / E474 / E485", "Sensor de corriente, disipador o corriente de entrada", "blink", "blink", "on", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E465 / E500", "Límite del compresor o sobretemperatura del disipador", "blink", "on", "off", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E231", "Sonda de batería/condensación exterior", "blink", "on", "blink", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E203 / E205", "Un minuto sin comunicación entre micom principal e inverter", "blink", "on", "on", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E470", "EEPROM", "off", "on", "off", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E458", "Ventilador exterior", "on", "off", "off", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E471", "OTP", "on", "off", "blink", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E467", "Rotación del compresor", "on", "off", "on", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E440 / E441", "Operación inhibida por condición exterior", "on", "blink", "off", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E469 / E488", "Sensor de tensión DC-link o tensión de entrada", "on", "blink", "blink", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E462", "I-trip o sobrecorriente PFC", "on", "blink", "on", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E554 / E422 / E407", "Fuga, EEV/válvula, autodiagnóstico o bloqueo de alta", "on", "on", "off", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E472", "Ausencia de señal de cruce por cero AC", "on", "on", "blink", "RAC Smart Whisper 18K/24K/30K"),
    led_row("Estado", "Reset al alimentar, aproximadamente 1 segundo", "on", "on", "on", "RAC Smart Whisper 18K/24K/30K"),
    led_row("E556", "Desajuste de capacidad", "blink", "off", "off", "RAC Smart Whisper 18K/24K/30K"),
    led_row("Test frío", "Funcionamiento de prueba en refrigeración", "off", "blink", "blink", "RAC Smart Whisper 18K/24K/30K"),
    led_row("Test calor", "Funcionamiento de prueba en calefacción", "blink", "blink", "blink", "RAC Smart Whisper 18K/24K/30K"),
]


def dvm_inverter_led() -> dict[str, Any]:
    return {
        "code_display": "E203",
        "indication_type": "outdoor_led",
        "display_location": "PBA inverter de la unidad exterior DVM S Eco",
        "family_hint": "Placa inverter con pilotos rojo, verde y naranja.",
        "relationship": "Rojo fijo + verde fijo + naranja parpadeando indica que la PBA inverter está comunicando; si el display principal queda en blanco, el manual dirige la sospecha a la PBA principal.",
        "led_indicators": [
            {"label": "Rojo", "color": "red", "state": "on"},
            {"label": "Verde", "color": "green", "state": "on"},
            {"label": "Naranja", "color": "orange", "state": "blink"},
        ],
        "counting_rule": "No se cuentan destellos: se observa el estado simultáneo de los tres pilotos.",
        "cycle_note": "Confirme además si el display de siete segmentos de la PBA principal muestra E203 o permanece apagado.",
        "sequence": "Diagnóstico cruzado PBA principal ↔ PBA inverter.",
    }


PROFILE_TEXT: dict[str, tuple[list[str], list[str], str]] = {
    "communication": (
        ["Cable de comunicación abierto, cruzado, empalmado o sin pantalla correcta", "Unidad o PBA sin alimentación", "Dirección repetida o tracking incompleto", "Circuito integrado de comunicación defectuoso"],
        ["Identificar si la lectura procede de interior, exterior, mando o PBA", "Comprobar alimentación de todas las unidades", "Revisar F1-F2/F3-F4 y continuidad sin empalmes", "Corregir direcciones y repetir tracking antes de sustituir placas"],
        "16/2 trenzado y apantallado; pantalla conectada a tierra solo en la exterior, cuando aplique a la red documentada.",
    ),
    "sensor": (
        ["Sonda abierta o en cortocircuito", "Conector o cable defectuoso", "Sonda descolocada del tubo", "Entrada analógica de placa defectuosa"],
        ["Medir la sonda desconectada y anotar la temperatura real", "Comparar con la curva correspondiente", "Verificar fijación y aislamiento térmico", "Comparar lectura de SNET/placa con medida real"],
        "Las sondas DVM documentadas incluyen 10 kΩ y descarga/top de 200 kΩ; confirme siempre la curva de esa posición.",
    ),
    "fan": (
        ["Hélice o turbina bloqueada", "Motor o realimentación de velocidad defectuosos", "Alimentación/driver de PBA anormal", "Intercambiador obstruido"],
        ["Girar mecánicamente con alimentación aislada", "Revisar conector y cable", "Medir alimentación y señal según la familia", "Probar solo con procedimiento de servicio documentado"],
        "No puentear el feedback ni conectar/desconectar un BLDC con tensión.",
    ),
    "drain": (
        ["Boya bloqueada arriba", "Desagüe obstruido o sifonado incorrecto", "Bomba defectuosa", "Cableado o entrada de flotador en corto"],
        ["Comprobar nivel real de agua", "Mover la boya y comprobar continuidad", "Verificar salida y funcionamiento de la bomba", "Limpiar drenaje y repetir una prueba con agua"],
        "E153 corresponde a la segunda detección de la boya en familias DVM; el alcance depende de la unidad interior.",
    ),
    "configuration": (
        ["Option code ausente o incorrecto", "DIP/selector no correspondiente", "PBA nueva sin identidad", "EEPROM o memoria defectuosa"],
        ["Fotografiar ajustes originales", "Comparar option code y diales con documentación", "Programar con el mando/herramienta correcta", "Reiniciar y repetir tracking"],
        "Todos los pilotos interiores parpadeando después de cambiar la PBA es una pista de option code no programado.",
    ),
    "inverter": (
        ["Compresor bloqueado o bobinados anormales", "Bus DC o red fuera de rango", "IPM/PFC/inverter defectuoso", "Disipación insuficiente"],
        ["Aislar alimentación y esperar al menos 15 minutos en el procedimiento DVM", "Comprobar descarga del bus antes de tocar", "Comparar U-V-W y aislamiento", "Usar inverter checker cuando la familia lo admite"],
        "Una o más luces del inverter checker que no parpadean indican salida de PBA anormal en el procedimiento DVM documentado.",
    ),
    "power": (
        ["Red alta, baja, invertida o con fase ausente", "Conexión floja", "PFC/rectificador/reactor defectuoso", "Sensor de tensión o corriente defectuoso"],
        ["Medir red en reposo y bajo carga", "Comprobar fases y aprietes", "Medir bus DC con procedimiento seguro", "Separar fallo de sensor de un fallo real de alimentación"],
        "Los sensores analógicos de placa deben permanecer normalmente dentro de 0,5–4,5 VDC cuando así lo especifica la fuente.",
    ),
    "pressure": (
        ["Carga incorrecta o fuga", "Válvula de servicio cerrada", "EEV o circuito restringido", "Ventilación/intercambio insuficiente", "Transductor o presostato defectuoso"],
        ["Medir presión real con instrumento adecuado", "Comparar con SNET y el valor del sensor", "Comprobar válvulas, EEV, ventiladores y baterías", "Reparar fugas y cargar por peso"],
        "No diagnosticar carga solo por sobrecalentamiento/subenfriamiento en un inverter; Samsung indica comprobar y cargar por peso.",
    ),
    "compressor": (
        ["Cable U-V-W suelto o invertido", "Bobinados desequilibrados o derivación", "Presiones no equilibradas", "Inverter defectuoso", "Compresor mecánicamente bloqueado"],
        ["Aislar y descargar el bus", "Comparar U-V-W; deben ser equivalentes", "Comprobar aislamiento a masa", "Separar compresor e inverter con el procedimiento documentado"],
        "En DVM el material de formación indica menos de 2 Ω entre fases para el ejemplo citado; no extrapolar a otro compresor sin confirmar.",
    ),
    "valve": (
        ["Bobina abierta o sin alimentación", "EEV/válvula bloqueada", "Conector equivocado", "Falta de refrigerante o presión insuficiente"],
        ["Comprobar bobina y orden", "Comparar temperaturas antes/después", "Activar la prueba específica si existe", "Confirmar carga y válvulas de servicio"],
        "El autodiagnóstico puede diferenciar EEV abierta/cerrada en primera y segunda detección.",
    ),
    "normal": (
        ["Condición ambiental o secuencia normal de protección/servicio"],
        ["Confirmar el texto exacto del estado", "Esperar el tiempo documentado", "No sustituir piezas si desaparece al cumplirse la condición"],
        "dF, CF, CI y UP no significan por sí solos una avería de componente.",
    ),
}


ERROR_SPECS: list[dict[str, Any]] = []


def add_error(
    code: str,
    title: str,
    profile: str,
    ref: str,
    page: str,
    scope: str = "system",
    behavior: str = "La unidad o el sistema entra en protección mientras persiste la condición.",
    technical: str = "",
    aliases: str = "",
    family: str = "DVM S Eco / DVM",
    section: str = "Error code table",
) -> None:
    ERROR_SPECS.append({
        "code": code,
        "title": title,
        "profile": profile,
        "ref": ref,
        "page": page,
        "scope": scope,
        "behavior": behavior,
        "technical": technical,
        "aliases": [x.strip() for x in aliases.split("|") if x.strip()],
        "family": family,
        "section": section,
    })


ERROR_ROWS = [
    ("E101","La interior no recibe datos de la exterior","communication","indoor"),
    ("E102","Comunicación interior-exterior indicada en la interior","communication","indoor"),
    ("E108","Dirección repetida en la red","configuration","system"),
    ("E109","Adquisición incompleta de dirección interior","configuration","indoor"),
    ("E121","Sonda de ambiente interior abierta o en corto","sensor","indoor"),
    ("E122","Sonda EVA IN interior abierta o en corto","sensor","indoor"),
    ("E123","Sonda EVA OUT interior abierta o en corto","sensor","indoor"),
    ("E128","Sonda EVA IN desprendida del tubo","sensor","indoor"),
    ("E129","Sonda EVA OUT desprendida del tubo","sensor","indoor"),
    ("E130","Sondas de entrada/salida de batería desprendidas","sensor","indoor"),
    ("E135","Realimentación del ventilador de limpieza / EEV según familia","fan","indoor"),
    ("E149","Configuración de sonda maestra AHU","configuration","indoor"),
    ("E151","EEV interior detectada abierta, segunda detección","valve","indoor"),
    ("E152","EEV interior detectada cerrada, segunda detección","valve","indoor"),
    ("E153","Segunda detección de boya de drenaje","drain","indoor"),
    ("E154","Realimentación RPM del ventilador interior","fan","indoor"),
    ("E161","Conflicto de modo frío/calor","configuration","system"),
    ("E162","EEPROM/micom de la unidad interior","configuration","indoor"),
    ("E163","Option code del mando incorrecto o ausente","configuration","indoor"),
    ("E180","Válvulas MCU de frío y calor abiertas simultáneamente, primera detección","valve","system"),
    ("E181","Válvulas MCU de frío y calor abiertas simultáneamente, segunda detección","valve","system"),
    ("E185","Cruce entre cable de comunicación y alimentación interior","communication","indoor"),
    ("E186","Conexión o problema de SPi","communication","indoor"),
    ("E190","Pipe check sin cambio esperado en EVA IN o dirección cruzada","sensor","system"),
    ("E191","Pipe check sin cambio esperado en EVA OUT o dirección cruzada","sensor","system"),
    ("E198","Fusible térmico interior desconectado","power","indoor"),
    ("E201","Cantidad/dirección/comunicación anormal durante tracking","communication","system"),
    ("E202","Comunicación perdida tras completar tracking","communication","system"),
    ("E203","Un minuto sin comunicación entre micom principal y secundario/exteriores","communication","outdoor"),
    ("E205","Comunicación entre PBA dentro de la caja exterior","communication","outdoor"),
    ("E211","Una interior usa dos puertos MCU no consecutivos","configuration","system"),
    ("E212","Dirección de interior repetida tres o más veces en MCU","configuration","system"),
    ("E213","Asignación MCU contiene una interior no instalada","configuration","system"),
    ("E214","Cantidad o direcciones MCU incorrectas","configuration","system"),
    ("E215","Dos MCU con la misma dirección","configuration","system"),
    ("E216","Puerto MCU activado sin interior conectada","configuration","system"),
    ("E217","Interior conectada a puerto MCU desactivado","configuration","system"),
    ("E218","Más interiores físicas que las asignadas a MCU","configuration","system"),
    ("E219","Sonda de entrada del intercooler MCU","sensor","system"),
    ("E220","Sonda de salida del intercooler MCU","sensor","system"),
    ("E221","Sonda de ambiente exterior","sensor","outdoor"),
    ("E231","Sonda de salida de condensador exterior","sensor","outdoor"),
    ("E241","Sonda COND OUT desprendida","sensor","outdoor"),
    ("E251","Sonda de descarga del compresor","sensor","outdoor"),
    ("E262","Sonda de descarga desprendida del tubo","sensor","outdoor"),
    ("E266","Sonda superior del compresor desprendida","sensor","outdoor"),
    ("E269","Sonda de aspiración desprendida","sensor","outdoor"),
    ("E276","Sonda superior del compresor abierta o en corto","sensor","outdoor"),
    ("E291","Fuga o señal anormal del sensor de alta","pressure","outdoor"),
    ("E296","Fuga o señal anormal del sensor de baja","pressure","outdoor"),
    ("E308","Sonda de aspiración abierta o en corto","sensor","outdoor"),
    ("E311","Sonda de doble tubo/líquido de subenfriador","sensor","outdoor"),
    ("E321","Sonda EVI/ESC IN","sensor","outdoor"),
    ("E322","Sonda EVI/ESC OUT","sensor","outdoor"),
    ("E323","Segunda sonda de aspiración","sensor","outdoor"),
    ("E403","Parada por protección antihielo","pressure","system"),
    ("E407","Parada del compresor por alta presión","pressure","system"),
    ("E410","Parada por baja presión o fuga","pressure","system"),
    ("E416","Parada por temperatura de descarga","pressure","outdoor"),
    ("E425","Fases invertidas/ausentes o entrada trifásica incorrecta","power","outdoor"),
    ("E428","Relación de compresión anormal","pressure","outdoor"),
    ("E438","Fuga en EEV EVI/ESC o intercooler/conector incorrecto","valve","outdoor"),
    ("E439","Detección de fuga de refrigerante","pressure","system"),
    ("E440","Calefacción inhibida por temperatura exterior alta","normal","system"),
    ("E441","Refrigeración inhibida por temperatura exterior baja","normal","system"),
    ("E442","Carga de refrigerante en calor inhibida sobre 15 °C","normal","system"),
    ("E443","Operación prohibida por baja presión","pressure","system"),
    ("E446","Fallo de funcionamiento del ventilador exterior 1","fan","outdoor"),
    ("E447","Cable del ventilador exterior 1 desconectado","fan","outdoor"),
    ("E458","Bloqueo del ventilador exterior 1","fan","outdoor"),
    ("E461","Fallo de arranque/operación del compresor inverter","compressor","outdoor"),
    ("E462","Parada por corriente total o corriente anormal","power","outdoor"),
    ("E463","Parada por temperatura OLP","pressure","outdoor"),
    ("E464","Sobrecorriente del compresor inverter/IPM","inverter","outdoor"),
    ("E465","Límite V/I del compresor inverter","inverter","outdoor"),
    ("E466","Tensión alta o baja en PBA inverter","power","outdoor"),
    ("E467","Cable U-V-W ausente o error de rotación","compressor","outdoor"),
    ("E468","Sensor de corriente de salida inverter","power","outdoor"),
    ("E469","Sensor de tensión DC-link","power","outdoor"),
    ("E470","EEPROM de la unidad exterior","configuration","outdoor"),
    ("E471","OTP/EEPROM entre micom principal e inverter","configuration","outdoor"),
    ("E472","Señal de cruce por cero AC ausente","power","outdoor"),
    ("E474","Disipador/IPM de PBA inverter","inverter","outdoor"),
    ("E475","Ventilador inverter 2","fan","outdoor"),
    ("E483","Protección hardware por sobretensión DC-link","power","outdoor"),
    ("E484","Sobrecarga PFC","power","outdoor"),
    ("E485","Sensor de corriente de entrada inverter","power","outdoor"),
    ("E488","Sensor de tensión de entrada AC","power","outdoor"),
    ("E489","Límite V del ventilador exterior","fan","outdoor"),
    ("E500","Sobretemperatura por contacto anormal del IPM","inverter","outdoor"),
    ("E503","Aviso de posible válvula de servicio cerrada","valve","system"),
    ("E504","Autodiagnóstico del compresor","compressor","outdoor"),
    ("E505","Autodiagnóstico del sensor de alta","pressure","outdoor"),
    ("E506","Autodiagnóstico del sensor de baja","pressure","outdoor"),
    ("E554","Fuga de gas detectada en RAC","pressure","system"),
    ("E556","Desajuste de capacidad interior-exterior","configuration","system"),
    ("E560","Option switch exterior incorrecto","configuration","outdoor"),
    ("E563","Módulo interior con versión antigua/incompatible","configuration","system"),
    ("E604","Comunicación entre mando cableado e interior","communication","controller"),
    ("E613","Comunicación DMS-PIM/SIM ausente durante 15 minutos","communication","controller"),
    ("E702","EEV interior detectada cerrada, primera detección","valve","indoor"),
    ("E703","EEV interior detectada abierta, primera detección","valve","indoor"),
]

for code, title, profile, scope in ERROR_ROWS:
    page = "35-37"
    ref = "ECO"
    if code in {"E472", "E554", "E556"}:
        ref, page = "SUPPORT", "tabla oficial"
    elif code in {"E604", "E613"}:
        ref, page = "TRAIN2", "30-31"
    add_error(code, title, profile, ref, page, scope=scope)

# Significados adicionales que cambian con la familia o capa de indicación.
add_error(
    "E163", "EEPROM de la unidad exterior en determinadas familias RAC", "configuration",
    "SUPPORT", "tabla oficial", scope="outdoor", family="RAC", section="Alternative family meaning",
)
add_error(
    "E201", "Cantidad de interiores distinta del dial de la exterior FJM", "communication",
    "FAQ", "pregunta E201 FJM", scope="system", family="FJM",
    technical="El dial debe coincidir con la cantidad de interiores conectadas; cualquier interior sin alimentación puede producir la discrepancia.",
)
add_error(
    "E203", "Diagnóstico cruzado entre PBA principal e inverter", "communication",
    "ECO", "40", scope="outdoor", family="DVM S Eco",
    technical="Rojo fijo + verde fijo + naranja parpadeando en la inverter indica inverter operativa; si el display principal está en blanco, comprobar la PBA principal.",
)
add_error(
    "E135", "Mal funcionamiento de apertura de EEV, según interior DVM", "valve",
    "IDU", "4-49", scope="indoor", family="DVM S Indoor",
)
add_error(
    "E199", "Pipe check pendiente en FJM", "normal", "FAQ", "pregunta E199 FJM",
    behavior="El sistema comunica y espera la comprobación de tuberías; no es por sí solo una avería de componente.",
    technical="Pulse K1 una vez; el display muestra K5. La FAQ indica 15–20 min en frío y hasta 60 min en calor.",
    family="FJM",
)
add_error(
    "UP", "Auto Trial Operation no completado", "normal", "ECO", "82",
    behavior="El funcionamiento normal del DVM queda prohibido hasta completar Auto Trial.",
    technical="Mantenga K1 durante 5 segundos; el display cambia a KK. La comprobación puede tardar de 30 a 50 minutos según la fuente de servicio.",
    family="DVM S",
)
add_error("dF", "Desescarche en curso", "normal", "SUPPORT", "estado dF", behavior="Estado normal temporal de calefacción; el compresor y ventiladores siguen la secuencia de desescarche.", family="RAC/DVM")
add_error("CF", "Recordatorio de limpieza de filtro", "normal", "SUPPORT", "estado CF", behavior="Aviso de mantenimiento, no fallo de componente.", family="RAC")
add_error("CI", "Auto Clean en curso", "normal", "SUPPORT", "estado CI", behavior="Secado/limpieza automática de la unidad interior.", family="RAC")
add_error("E361", "Fallo de arranque del segundo compresor DVM", "compressor", "TRAIN2", "32-35", scope="outdoor", family="DVM dual compressor")
add_error("E364", "Sobrecorriente IPM del segundo compresor DVM", "inverter", "TRAIN2", "32-35", scope="outdoor", family="DVM dual compressor")
add_error("E366", "Tensión alta/baja del segundo inverter DVM", "power", "TRAIN2", "36", scope="outdoor", family="DVM dual compressor")
add_error("E206-C001", "Comunicación de HUB PBA", "communication", "TRAIN2", "28", scope="outdoor", family="DVM S")
add_error("E206-C002", "Comunicación de Fan PBA", "communication", "TRAIN2", "28", scope="outdoor", family="DVM S")
add_error("E206-C003", "Comunicación de Inverter PBA 1", "communication", "TRAIN2", "28", scope="outdoor", family="DVM S")
add_error("E206-C004", "Comunicación de Inverter PBA 2", "communication", "TRAIN2", "28", scope="outdoor", family="DVM S")
add_error("E206-C005", "Comunicación de Water HUB PBA", "communication", "TRAIN2", "28", scope="outdoor", family="DVM S")
add_error("E108-A001", "Dirección interior duplicada", "configuration", "TRAIN2", "29", scope="system", family="DVM S")
add_error("E108-A200", "Duplicado en la capa de dirección DVM", "configuration", "TRAIN2", "29", scope="system", family="DVM S")
add_error("E108-C101", "Dirección MCU duplicada", "configuration", "TRAIN2", "29", scope="system", family="DVM S")
add_error("U200", "Comunicación interior-exterior en la capa de control DVM", "communication", "TRAIN2", "26", scope="system", family="DVM S")


LED_CODE_MAP = {
    "E101": LED_18_30[2], "E102": LED_18_30[2], "E203": dvm_inverter_led(),
    "E205": LED_18_30[13], "E221": LED_18_30[7], "E231": LED_18_30[12],
    "E251": LED_18_30[9], "E407": LED_18_30[21], "E416": LED_18_30[8],
    "E422": LED_18_30[21], "E440": LED_18_30[18], "E441": LED_18_30[18],
    "E458": LED_18_30[15], "E461": LED_18_30[5], "E462": LED_18_30[20],
    "E464": LED_18_30[1], "E465": LED_18_30[11], "E466": LED_18_30[6],
    "E467": LED_18_30[17], "E468": LED_18_30[10], "E469": LED_18_30[19],
    "E470": LED_18_30[14], "E471": LED_18_30[16], "E472": LED_18_30[22],
    "E474": LED_18_30[10], "E483": LED_18_30[6], "E484": LED_18_30[6],
    "E485": LED_18_30[10], "E488": LED_18_30[19], "E500": LED_18_30[11],
    "E554": LED_18_30[21], "E556": LED_18_30[24],
}


def error_source_ref(spec: dict[str, Any]) -> str:
    return SOURCES[spec["ref"]]["document_ref"]


def build_interpretation(ident: int, spec: dict[str, Any]) -> dict[str, Any]:
    causes, checks, profile_note = PROFILE_TEXT[spec["profile"]]
    technical = spec["technical"] or profile_note
    origin = error_source_ref(spec)
    info_items = [
        {"id": ident * 100 + 1, "item_type": "machine_behavior", "title": None, "body": spec["behavior"], "sort_order": 1, "review_status": "reviewed", "origin_ref": origin},
        {"id": ident * 100 + 2, "item_type": "related_element", "title": None, "body": spec["title"], "sort_order": 2, "review_status": "reviewed", "origin_ref": origin},
    ]
    order = 3
    for text in causes:
        info_items.append({"id": ident * 100 + order, "item_type": "cause", "title": None, "body": text, "sort_order": order, "review_status": "reviewed", "origin_ref": origin})
        order += 1
    for text in checks:
        info_items.append({"id": ident * 100 + order, "item_type": "check", "title": None, "body": text, "sort_order": order, "review_status": "reviewed", "origin_ref": origin})
        order += 1
    info_items.append({"id": ident * 100 + order, "item_type": "observation", "title": "Dato técnico", "body": technical, "sort_order": order, "review_status": "reviewed", "origin_ref": origin})

    contexts = [{
        "code_display": spec["code"],
        "code_normalized": normalize(spec["code"]),
        "indication_type": "controller" if spec["scope"] == "controller" else ("outdoor_display" if spec["scope"] == "outdoor" else "display"),
        "display_location": "mando/controlador" if spec["scope"] == "controller" else ("display o pilotos de la unidad exterior" if spec["scope"] == "outdoor" else "display/mando de la unidad o sistema"),
        "family_hint": spec["family"],
        "relationship": "Código documentado en esta familia y capa de indicación.",
        "source_ref": spec["ref"],
        "source_document_ref": origin,
        "related_error_id": None,
    }]
    led_context = LED_CODE_MAP.get(spec["code"])
    if led_context:
        contexts.append({**led_context, "code_normalized": normalize(led_context["code_display"]), "source_ref": "SMART" if spec["code"] != "E203" else "ECO", "source_document_ref": SOURCES["SMART" if spec["code"] != "E203" else "ECO"]["document_ref"], "related_error_id": None})

    if "no es" in spec["behavior"].lower() or spec["profile"] == "normal":
        stop_level = "warning"
    elif spec["scope"] in {"indoor", "controller"}:
        stop_level = "affected_unit"
    elif spec["scope"] == "outdoor":
        stop_level = "protected_stop"
    else:
        stop_level = "all_system" if "sistema" in spec["behavior"].lower() else "protected_stop"

    src = source(spec["ref"], spec["page"], f'{spec["section"]} — {spec["code"]}')
    return {
        "id": ident,
        "title": spec["title"],
        "description": f'{spec["code"]} en {spec["family"]}: {spec["title"]}.',
        "source_kind": "official",
        "confidence": "high",
        "review_status": "reviewed",
        "indication_contexts": contexts,
        "info_items": info_items,
        "operational_impacts": [{
            "stop_level": stop_level,
            "summary": spec["behavior"],
            "affected_scope": f'Alcance documentado para {spec["family"]}.',
            "unaffected_scope": None,
            "restart_behavior": "Corregir la causa y repetir la secuencia de inicialización o servicio indicada para la familia.",
            "degraded_behavior": None,
            "notes": "No extrapolar el mismo alcance a otra familia que utilice el mismo código.",
        }],
        "datasets": [{
            "id": ident * 10 + 1,
            "name": f'{spec["code"]} — referencia técnica',
            "dataset_type": "technical_reference",
            "variable_name": "Comprobación",
            "variable_unit": None,
            "value_name": "Dato",
            "value_unit": None,
            "tolerance_text": f'Aplicar solo a {spec["family"]}.',
            "source_kind": "official",
            "calculation_method": None,
            "review_status": "reviewed",
            "notes": technical,
            "visible": 1,
            "points": [{"variable_value": None, "value_min": None, "value_nominal": None, "value_max": None, "value_text": technical, "sort_order": 1, "notes": None}],
            "sources": [source(spec["ref"], spec["page"], f'Valor técnico — {spec["code"]}')],
        }],
        "sources": [src],
    }


def build_errors() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for spec in ERROR_SPECS:
        grouped[normalize(spec["code"])].append(spec)
    index_rows: list[dict[str, Any]] = []
    detail_rows: list[dict[str, Any]] = []
    interpretation_id = 1
    for error_id, key in enumerate(sorted(grouped), start=1):
        specs = grouped[key]
        primary = specs[0]
        aliases = [primary["code"], primary["code"].replace("-", " "), primary["code"].replace("-", "")]
        aliases.extend(alias for spec in specs for alias in spec["aliases"])
        aliases = list(dict.fromkeys(x for x in aliases if x))
        interpretations = []
        for spec in specs:
            interpretations.append(build_interpretation(interpretation_id, spec))
            interpretation_id += 1
        tags = sorted({
            token.lower()
            for spec in specs
            for token in normalize(f'{spec["title"]} {spec["family"]} {spec["profile"]}').split()
            if len(token) > 2
        })
        detail = {
            "id": error_id,
            "code_display": primary["code"],
            "code_normalized": key,
            "indication_type": "mixed" if len({x["scope"] for x in specs}) > 1 else ("outdoor_display" if primary["scope"] == "outdoor" else "display"),
            "unit_scope": primary["scope"],
            "short_label": primary["title"],
            "aliases": [{"alias_display": value, "alias_normalized": normalize(value)} for value in aliases],
            "tags": tags,
            "interpretations": interpretations,
            "media": [],
        }
        search_text = normalize(" ".join([primary["code"], *aliases, *tags, *(x["title"] for x in specs), *(x["family"] for x in specs)]))
        index_rows.append({
            "id": error_id,
            "code_display": primary["code"],
            "code_normalized": key,
            "indication_type": detail["indication_type"],
            "unit_scope": primary["scope"],
            "short_label": primary["title"],
            "aliases": aliases,
            "tags": tags,
            "search_text": search_text,
            "interpretation_count": len(interpretations),
        })
        detail_rows.append(detail)
    return index_rows, detail_rows


def section(title: str, body: str, kind: str = "technical", open_by_default: bool = False) -> dict[str, Any]:
    return {"section_type": kind, "title": title, "body": body, "collapsed_default": 0 if open_by_default else 1}


def step(no: int, instruction: str, expected: str = "", phase: str = "procedure", warning: str = "none") -> dict[str, Any]:
    return {"phase": phase, "step_no": no, "instruction": instruction, "expected_result": expected or None, "warning_level": warning}


def variant(
    title: str,
    recognition: str,
    ref: str,
    page: str,
    purpose: str,
    summary: str,
    *,
    system: str = "Samsung",
    scope: str = "system",
    steps: list[dict[str, Any]] | None = None,
    sections: list[dict[str, Any]] | None = None,
    parameters: list[dict[str, Any]] | None = None,
    controller: dict[str, Any] | None = None,
    monitoring: list[dict[str, Any]] | None = None,
    led_patterns: list[dict[str, Any]] | None = None,
    source_section: str = "Technical procedure",
) -> dict[str, Any]:
    return {
        "title": title,
        "recognition": recognition,
        "system_type": system,
        "unit_scope": scope,
        "refrigerant": None,
        "purpose": purpose,
        "summary": summary,
        "source_kind": "official",
        "review_status": "reviewed",
        "sections": sections or [
            section("Cómo reconocer esta variante", recognition, "recognition", True),
            section("Qué hace o tiene en cuenta la máquina", summary),
        ],
        "steps": steps or [
            step(1, "Identifique la familia, la placa y el punto exacto de indicación.", phase="prepare"),
            step(2, "Aplique solo el procedimiento documentado para esa variante."),
            step(3, "Anote el resultado antes de reiniciar.", phase="verify"),
        ],
        "parameters": parameters or [],
        "controller": controller,
        "monitoring_points": monitoring or [],
        "led_patterns": led_patterns or [],
        "media": [],
        "sources": [source(ref, page, source_section)],
    }


TOPICS: list[dict[str, Any]] = []


def add_topic(category: str, slug: str, title: str, summary: str, variants: list[dict[str, Any]]) -> None:
    TOPICS.append({"category": category, "slug": slug, "title": title, "summary": summary, "variants": variants})


add_topic("outdoor_led_diagnostics", "rac-outdoor-led-master", "Tabla maestra de pilotos exteriores RAC", "Dos tablas independientes para placas 9K/12K y 18K/24K/30K.", [
    variant("RAC 9K/12K — amarillo, verde y rojo", "Placa exterior con tres pilotos identificados YEL, GRN y RED.", "SMART", "3-3", "Interpretar la combinación completa.", "Una misma posición cambia de significado si el piloto está fijo, apagado o parpadeando.", system="RAC 9K/12K", scope="outdoor", led_patterns=LED_9_12, source_section="Outdoor LED Display Error and Check Method"),
    variant("RAC 18K/24K/30K — amarillo, verde y rojo", "Placa exterior de mayor potencia con tres pilotos YEL, GRN y RED.", "SMART", "3-4", "Interpretar la combinación completa.", "No mezcle esta tabla con la 9K/12K: algunas combinaciones y estados difieren.", system="RAC 18K/24K/30K", scope="outdoor", led_patterns=LED_18_30, source_section="Outdoor LED Display Error and Check Method"),
])
add_topic("outdoor_led_diagnostics", "dvm-inverter-led", "Pilotos de PBA inverter DVM", "Diagnóstico cruzado entre pilotos inverter y display principal.", [
    variant("E203: rojo fijo, verde fijo y naranja parpadeando", "PBA inverter DVM S Eco con LED rojo, verde y naranja.", "ECO", "40", "Separar PBA inverter de PBA principal.", "La combinación confirma actividad de la inverter; un display principal en blanco orienta a la PBA principal.", system="DVM S Eco", scope="outdoor", led_patterns=[dvm_inverter_led()], source_section="E203 main/sub micom diagnosis"),
    variant("No decidir por un solo piloto", "Cualquier exterior Samsung con más de un LED de estado.", "SMART", "3-3–3-4", "Evitar equivalencias falsas.", "Anote color, fijo/parpadeo/apagado, orden físico, tamaño de unidad y si existe 7 segmentos.", system="RAC/DVM", scope="outdoor"),
])
add_topic("outdoor_led_diagnostics", "indoor-led-layer", "Pilotos interiores y relación con el código E", "La indicación interior puede resumir una avería cuya placa exterior aporta más detalle.", [
    variant("Tres LED interiores + código de siete segmentos", "Unidad interior RAC con LED1/LED2/LED3 y display E…", "MAX", "10-2–10-32", "Relacionar código interior y patrón.", "Busque primero el E mostrado y después confirme el patrón exterior.", system="RAC", scope="indoor"),
    variant("Pilotos de cassette/ducto DVM", "Receptor interior con pilotos de operación, temporizador, filtro y desescarche.", "IDU", "4-1–4-54", "Distinguir estado interior de fallo exterior.", "Las secuencias incluyen sensores, ventilador, EEPROM, comunicación, térmico y flotador.", system="DVM S Indoor", scope="indoor"),
])

add_topic("diagnostic_access", "where-code-appears", "Dónde se muestra cada código", "Mando, interior, exterior, PBA y software pueden mostrar capas distintas.", [
    variant("Código E en mando o display interior", "Mando/receptor o display de unidad interior.", "ECO", "35-37", "Identificar la capa de usuario/técnico.", "El código E puede señalar una avería exterior sin describir su patrón de pilotos.", system="RAC/FJM/DVM"),
    variant("Display de siete segmentos exterior", "Placa exterior con display numérico/alfanumérico y teclas K1-K4.", "QUICK", "19-21", "Leer código, dirección y modos K.", "No confunda códigos E con confirmaciones K1/K2 o View Mode.", system="DVM S", scope="outdoor"),
    variant("SNET Pro y subcódigos", "Equipo conectado mediante herramienta de servicio.", "SOFTWARE", "página oficial", "Obtener contexto, datos y subcódigo.", "SNET permite observar la red y registrar variables que no aparecen en el mando.", system="DVM", scope="system"),
])
add_topic("diagnostic_access", "controller-error-access", "Obtención de errores desde mandos", "Acceso desde controladores cableados y capa DVM.", [
    variant("Mando cableado DVM: código actual", "MWR-WE10N o controlador compatible sobre F3-F4.", "TRAIN2", "25-31", "Leer código y unidad afectada.", "E604 pertenece al enlace mando-interior; otros E pueden proceder de la red DVM.", system="DVM", scope="controller"),
    variant("Autodiagnóstico desde mando inalámbrico RAC", "Control inalámbrico con acceso a service/check según generación.", "SMART", "3-5–3-12", "Consultar y programar sin abrir la placa.", "La combinación cambia entre mandos; identifique los botones y segmentos antes de seguirla.", system="RAC", scope="controller"),
])
add_topic("diagnostic_access", "outdoor-view-mode", "View Mode y lectura desde placa exterior", "Teclas K y display para estado, direcciones y pruebas.", [
    variant("DVM S: K1, K2, K3 y K4", "Placa principal exterior con cuatro pulsadores y display.", "QUICK", "19-21", "Entrar en funciones y salir sin alterar otra opción.", "K1/K2 recorren funciones; K3 inicializa/sale; una pulsación de más puede seleccionar otra función.", system="DVM S", scope="outdoor"),
    variant("FJM: display y dial de cantidad", "Exterior multisplit con display, K1/K2 y selector rotativo.", "FJM", "3-1–3-12", "Comprobar tracking y pipe check.", "E199, K5 y E201 deben interpretarse con la cantidad de interiores configurada.", system="FJM", scope="outdoor"),
])

add_topic("history_reset", "history-and-reset", "Historial, reset y conservación de datos", "Diferenciar borrado, reset y repetición de tracking.", [
    variant("Reset exterior DVM con K3", "Placa DVM S con K3 y display.", "ECO", "38-48", "Reiniciar tras corregir dirección/MCU.", "K3 repite tracking; no corrige por sí mismo una dirección duplicada.", system="DVM S", scope="outdoor"),
    variant("Reset de mando tras E604", "Mando cableado sin comunicación durante tracking.", "TRAIN2", "30-31", "Restablecer el tracking del mando.", "Desconecte y vuelva a conectar la alimentación del mando después de corregir el error raíz.", system="DVM", scope="controller"),
    variant("Registro con SNET Pro", "Sistema que no presenta código pero falla intermitentemente.", "FAQ", "pregunta sin código", "Conservar evidencia antes de reiniciar.", "Samsung indica registrar 60 minutos en Test Mode y 60 minutos en funcionamiento normal.", system="RAC/DVM"),
])

add_topic("service_modes", "rac-fjm-test", "Test Run en RAC y FJM", "Marcha forzada en frío/calor y comprobación de tuberías.", [
    variant("RAC: prueba desde mando", "Split con mando inalámbrico y modo Test.", "SMART", "3-1", "Forzar una prueba controlada.", "Las protecciones de potencia, descarga, ventiladores y comunicación siguen activas.", system="RAC"),
    variant("FJM: K2 calor/frío", "Exterior FJM con pulsador K2.", "FJM", "3-1", "Ejecutar Try Run.", "K2 una vez selecciona calor y tres veces frío en la variante documentada; confirme el display.", system="FJM", scope="outdoor"),
])
add_topic("service_modes", "dvm-key-functions", "Funciones DVM mediante K1/K2", "Tabla operativa de pruebas y servicios.", [
    variant("K1: carga, prueba, pump out y vacío", "PBA principal DVM S con K1-K4.", "QUICK", "19", "Seleccionar la función exacta.", "K1 recorre carga en calor, Test Heat, pump out por dirección y vacío por dirección/todas.", system="DVM S", scope="outdoor", parameters=[
        {"parameter_code":"K1","name":"Número de pulsaciones","description":"Funciones documentadas","factory_value":None,"dependencies":"Confirmar display antes de esperar o validar.","warnings":"No pulse una vez adicional: cambia la función.","options":[
            {"option_value":"1","option_label":"Carga de refrigerante en calor","effect":"Display K1"},
            {"option_value":"2","option_label":"Test Run calefacción","effect":"Display K2"},
            {"option_value":"3–6","option_label":"Pump out en calor por dirección exterior","effect":"K3 + dirección"},
            {"option_value":"7–10","option_label":"Vacío por dirección exterior","effect":"K4 + dirección"},
            {"option_value":"11","option_label":"Vacío de todas las exteriores","effect":"K4 A"},
            {"option_value":"12","option_label":"Fin","effect":"Sale del modo"},
        ]},
    ]),
    variant("K2: frío, pump down, defrost y pruebas", "PBA principal DVM S con K1-K4.", "QUICK", "20-21", "Seleccionar la prueba sin confundir la pulsación.", "K2 incluye carga/test en frío, pump down, check piping, refrigerant check, descarga del bus, defrost, oil return, inverter, ventiladores y heater.", system="DVM S", scope="outdoor", parameters=[
        {"parameter_code":"K2","name":"Número de pulsaciones","description":"Funciones documentadas","factory_value":None,"dependencies":"Confirmar cada indicación K en el display.","warnings":"Algunas funciones cambian entre Heat Pump y Heat Recovery.","options":[
            {"option_value":"1","option_label":"Carga en frío","effect":"K5"},
            {"option_value":"2","option_label":"Test Run frío","effect":"K6"},
            {"option_value":"3","option_label":"Pump down de todas las unidades","effect":"K7"},
            {"option_value":"4","option_label":"Check piping HR / auto mode HP","effect":"K8"},
            {"option_value":"5","option_label":"Comprobación de refrigerante","effect":"K9"},
            {"option_value":"6","option_label":"Descarga de tensión DC","effect":"KA"},
            {"option_value":"7","option_label":"Desescarche forzado","effect":"KB"},
            {"option_value":"8","option_label":"Retorno de aceite forzado","effect":"KC"},
            {"option_value":"9–10","option_label":"Prueba inverter 1/2","effect":"KD/KE"},
            {"option_value":"11–12","option_label":"Prueba ventilador 1/2","effect":"KF/KG"},
            {"option_value":"13","option_label":"Auto pipe pairing HR","effect":"KH"},
            {"option_value":"14","option_label":"Prueba resistencia de base","effect":"KI"},
            {"option_value":"15","option_label":"Fin","effect":"Sale del modo"},
        ]},
    ]),
])
add_topic("service_modes", "pump-vacuum", "Pump down, pump out y modo vacío", "Procedimientos distintos que no deben confundirse.", [
    variant("Pump down DVM S en frío", "DVM S con display K7.", "QUICK", "20", "Recoger refrigerante según procedimiento DVM.", "K2 tres veces selecciona pump down de todas las unidades; cierre de válvulas y finalización deben seguir el manual de esa instalación.", system="DVM S", scope="outdoor"),
    variant("Modo vacío tras reparación exterior", "DVM S con varias EEV/solenoides.", "TRAIN2", "23", "Abrir el circuito interno para evacuar.", "K1 permite vacío por dirección exterior o todas; esta función no sustituye el vacuómetro ni la prueba de estanqueidad.", system="DVM S", scope="outdoor"),
    variant("Triple evacuación de referencia Samsung HVAC", "Instalación con humedad o procedimiento de puesta en marcha indicado.", "FAQ", "triple evacuation", "Eliminar humedad de forma controlada.", "5000 micrones + N₂ 3 psi/10 min; 2000 + N₂ 3 psi/15 min; menos de 200 micrones y mantener 60 min.", system="RAC/FJM/DVM"),
])

add_topic("configuration", "indoor-option-code", "Option code y programación de PBA interior", "La placa nueva no viene programada.", [
    variant("Todos los pilotos parpadean después de cambiar la PBA", "Unidad interior recién reparada con todos los LED intermitentes.", "FAQ", "pregunta PBA interior", "Restaurar la identidad de producto.", "Introduzca el product/option code con el mando inalámbrico según el manual; no sustituya otra placa por este síntoma.", system="RAC/FJM/DVM", scope="indoor"),
    variant("Conductos sin receptor inalámbrico de fábrica", "Unidad de conductos sin receptor frontal.", "FAQ", "product code IDU", "Programar mediante receptor acoplado.", "Conecte el kit de receptor al conector de display de la PBA y repita la entrada del código hasta confirmar.", system="Ducted IDU", scope="indoor"),
])
add_topic("configuration", "fjm-addressing-settings", "DIP y dial de cantidad FJM", "Direccionamiento automático/manual y número de interiores.", [
    variant("Auto addressing FJM", "Exterior FJM con DIP y dial rotativo.", "FAQ", "FJM DIP/rotary", "Configurar el reconocimiento automático.", "DIP en posición por defecto ON y dial igual a la cantidad real de interiores.", system="FJM", scope="outdoor"),
    variant("Manual addressing FJM", "Exterior FJM donde se desea dirección manual.", "FAQ", "FJM DIP/rotary", "Evitar E201 por configuración.", "El primer DIP queda OFF para direccionamiento manual; confirme todas las interiores alimentadas.", system="FJM", scope="outdoor"),
])
add_topic("configuration", "dvm-outdoor-settings", "Programación de placa exterior DVM", "Opciones, guardado, restauración y direcciones.", [
    variant("Guardar, salir y restaurar ajustes", "PBA DVM con K1-K4.", "QUICK", "9-18", "Modificar sin perder el control de la opción.", "K1 largo recupera valores previos, K4 largo restaura fábrica, K2 largo guarda tras tracking y K3 sale.", system="DVM S", scope="outdoor"),
    variant("VRF Coder para ajustes exteriores", "Técnico con PC y familia DVM identificada.", "VRFCODER", "página oficial", "Consultar ajustes con ejemplos de display.", "Incluye option codes, direccionamiento, configuración exterior, conversor hexadecimal y base de errores.", system="DVM", scope="system"),
])

CONTROLLER_2 = {
    "interface_type":"bus de mando cableado","controller_family":"MWR-WE10N","wire_count":"2","polarity":"según terminales F3-F4","nominal_voltage":"12 VDC en el mando","terminals":"F3, F4","cable_colors":None,"cable_spec":"Confirmar el cable especificado por el manual del controlador","startup_behavior":"Puede permanecer sin alimentar hasta que termine el direccionamiento inicial del sistema DVM.","maximum_scope":"unidad/grupo según configuración","notes":"No confundir con MWR-WE10 de cuatro terminales.",
}
CONTROLLER_4 = {
    "interface_type":"mando cableado RAC/FJM","controller_family":"MWR-WE10","wire_count":"4","polarity":"respetar los cuatro terminales","nominal_voltage":"12 VDC en el mando","terminals":"cuatro terminales; familia RAC/FJM V1/V2","cable_colors":None,"cable_spec":"Según manual de instalación del mando","startup_behavior":"Realiza tracking con la unidad interior; un fallo puede aparecer como E604 en la capa DVM.","maximum_scope":"unidad/grupo compatible","notes":"Verifique el número de terminales antes de aplicar un esquema.",
}
add_topic("controllers_buses", "wired-controller-families", "Mandos MWR-WE10N y MWR-WE10", "Dos terminales y cuatro terminales no son intercambiables.", [
    variant("MWR-WE10N de dos hilos", "Mando con dos bornes F3-F4.", "FAQ", "wired controllers", "Comprobar alimentación y bus.", "Confirme aproximadamente 12 VDC y el final del tracking.", system="DVM", scope="controller", controller=CONTROLLER_2),
    variant("MWR-WE10 de cuatro terminales", "Mando con cuatro bornes, usado en RAC/FJM V1/V2.", "FAQ", "wired controllers", "No aplicar el esquema del WE10N.", "El propio número de terminales es la primera pista de identificación.", system="RAC/FJM", scope="controller", controller=CONTROLLER_4),
])
add_topic("controllers_buses", "communication-wiring", "Cableado de comunicación Samsung", "F1-F2, F3-F4 y apantallamiento.", [
    variant("F1-F2 entre interior y exterior", "Red DVM con terminales F1-F2.", "TRAIN2", "25-28", "Diagnosticar E201/E205.", "Samsung HVAC exige 16/2 trenzado apantallado, tierra de pantalla solo en la exterior y sin empalmes entre terminales.", system="DVM"),
    variant("F3-F4 del mando", "Mando MWR-WE10N sobre bus de dos hilos.", "FAQ", "wired controllers", "Diagnosticar E604.", "Primero confirme 12 VDC, después terminales y tracking; E108/E201 pueden impedir que el mando complete su adquisición.", system="DVM", scope="controller"),
    variant("R1-R2 y capa central", "PIM/SIM/DMS o control central DVM.", "TRAIN2", "30-31", "Separar E613 de E604.", "E613 aparece tras 15 minutos sin comunicación DMS-PIM/SIM; corrija primero la avería raíz de red.", system="DVM", scope="controller"),
])

add_topic("drainage_overflow", "float-switch-e153", "Boya, bomba y E153", "Segunda detección del flotador en unidades DVM.", [
    variant("Cassette DVM con bomba integrada", "Cassette con bomba, boya y elevación documentada.", "IDU", "4-52", "Seguir la lógica de detección.", "E153 es la segunda detección de la boya; compruebe agua real, flotador, bomba y desagüe antes de cambiar la PBA.", system="DVM cassette", scope="indoor"),
    variant("Conductos MA con bomba integrada", "Conducto MA-1/MA-2 equipado con drain pump.", "IDU", "2-41–2-45", "No asumir que todos los conductos carecen de bomba.", "Algunas variantes documentan bomba incorporada, 750 mm de elevación y 24 l/h; identifique la construcción.", system="DVM ducted", scope="indoor"),
    variant("Comportamiento en frío frente a calor/parada", "Unidad interior con flotador activo.", "IDU", "4-52", "Interpretar una boya trabada.", "La bomba puede seguir operando o arrancar por seguridad aunque no haya demanda de frío; una boya atascada reproduce el fallo.", system="DVM indoor", scope="indoor"),
])

add_topic("commissioning", "fjm-pipe-check", "FJM: tracking y comprobación de tuberías", "E199, K5, direcciones y tiempos.", [
    variant("E199 listo para pipe check", "FJM comunicado mostrando E199.", "FAQ", "E199 FJM", "Completar la puesta en marcha.", "Pulse K1 una vez; K5 confirma el inicio. La FAQ indica 15–20 minutos en frío y hasta 60 en calor.", system="FJM", scope="outdoor"),
    variant("E201 durante tracking FJM", "Cantidad detectada distinta del dial.", "FAQ", "E201 FJM", "Encontrar la interior ausente.", "Revise dial, alimentación y comunicación de cada interior; un empalme puede dejar una unidad fuera del conteo.", system="FJM", scope="outdoor"),
])
add_topic("commissioning", "dvm-auto-trial", "DVM Auto Trial Operation", "UP, KK, condiciones previas y resultado.", [
    variant("Inicio con K1 mantenido 5 segundos", "Exterior DVM mostrando UP.", "QUICK", "18", "Completar la comprobación automática.", "El display cambia a KK; al terminar correctamente, el sistema se detiene y desplaza las direcciones conectadas.", system="DVM S", scope="outdoor"),
    variant("Condiciones previas y alcance", "DVM recién instalado o reparado.", "ECO", "82-90", "Evitar resultados indeterminados.", "Alimente el calentador de cárter tres horas, abra válvulas, verifique carga, comunicación, drenaje y use SNET para el informe.", system="DVM S", scope="system"),
])

add_topic("multisplit", "fjm-errors-behavior", "FJM: alcance de errores y unidades", "El conteo de interiores y la comunicación condicionan todo el sistema.", [
    variant("Interior sin alimentación durante tracking", "Una o varias interiores FJM no aparecen.", "FAQ", "E201 FJM", "Localizar la rama ausente.", "La exterior puede mostrar E201 aunque el cable principal parezca correcto; compruebe cada interior.", system="FJM"),
    variant("Conflicto de modo E161", "Interiores solicitan frío y calor simultáneamente.", "ECO", "35", "Distinguir configuración de avería.", "En Heat Pump no puede satisfacerse una demanda contraria a la preparación de la exterior; la unidad afectada queda esperando o en error.", system="FJM/DVM HP"),
])

add_topic("dvm_network", "dvm-communication-stack", "DVM: pila de comunicación E108/E201/E604/E613", "Corregir primero la causa inferior.", [
    variant("E108 bloquea tracking de otras capas", "Dirección repetida con errores encadenados.", "TRAIN2", "29-31", "Evitar cambiar varias placas.", "E108 puede impedir tracking del mando y generar E604; también puede propagarse a control central.", system="DVM"),
    variant("E205/E206 dentro de la caja exterior", "DVM con Main, HUB, FAN e inverter PBA.", "TRAIN2", "28", "Localizar la placa interna.", "Los subcódigos C001-C005 separan HUB, Fan, inverter 1/2 y Water HUB.", system="DVM", scope="outdoor"),
])
add_topic("dvm_network", "mcu-addressing", "MCU: direcciones, puertos y solenoides", "E211–E220 y errores de asignación.", [
    variant("Puertos consecutivos y DIP de uso", "MCU Heat Recovery con varias salidas.", "ECO", "41-49", "Corregir asignación antes de reiniciar.", "Una interior que usa dos puertos debe emplear puertos consecutivos; cada puerto usado debe coincidir con su DIP.", system="DVM HR"),
    variant("Direcciones MCU duplicadas", "Dos MCU con el mismo selector rotativo.", "ECO", "41-49", "Eliminar E214/E215.", "Ajuste una dirección única, confirme cantidad de MCU en la exterior y pulse K3 para repetir tracking.", system="DVM HR"),
])
add_topic("dvm_network", "system-stop-scope", "Parada total, zona afectada y recuperación", "El alcance depende de la arquitectura.", [
    variant("Comunicación de sistema", "E201/E202 durante o después del tracking.", "ECO", "38-39", "Determinar alcance.", "Una pérdida global impide operar al sistema; una unidad no comunicada puede quedar fuera mientras se localiza la rama.", system="DVM"),
    variant("Detección de refrigerante RDS en DVM S2", "Sistema A2L con sensor en MCU/valve box o interior.", "FAQ", "RDS system response", "Distinguir parada de sistema y zona.", "Un RDS en MCU/valve box detiene el sistema; un RDS en una interior asociada detiene solo esa zona.", system="DVM S2"),
])

add_topic("component_checks", "compressor-inverter", "Compresor e inverter", "Separación de E461/E464 y segunda etapa E361/E364.", [
    variant("Inverter checker", "DVM con función de comprobación y herramienta Samsung.", "TRAIN2", "33", "Comprobar la salida U-V-W.", "Aísle la exterior, espere al menos 15 minutos, conecte U rojo/V blanco/W negro y ejecute la prueba; un LED que no parpadea apunta a salida de PBA.", system="DVM", scope="outdoor"),
    variant("Comprobar compresor con multímetro", "Compresor desconectado y bus descargado.", "TRAIN2", "34-35", "Separar bobinado, aislamiento e inverter.", "Compare U-V-W y aislamiento a chasis. El ejemplo formativo cita menos de 2 Ω entre fases, pero confirme el compresor concreto.", system="DVM", scope="outdoor"),
    variant("Doble compresor: cruzar diagnóstico", "Exterior DVM dual con inverter 1/2.", "TRAIN2", "34", "Ver si el fallo sigue la PBA o el compresor.", "El procedimiento cruza temporalmente las conexiones bajo condiciones controladas; solo personal cualificado y siguiendo el diagrama.", system="DVM dual", scope="outdoor"),
])
add_topic("component_checks", "sensors-pressure", "Sondas y transductores", "Curvas 10K/200K y señal 0,5–4,5 V.", [
    variant("Sondas DVM", "Arnés exterior/interior con sensor de tubería o ambiente.", "TRAIN1", "29", "Elegir la curva correcta.", "Descarga/top se documentan como 200K; ambiente, Cond Out, líquido, EVI y aspiración como 10K en el material formativo.", system="DVM"),
    variant("Transductores de presión", "Sensor analógico de alta/baja conectado a PBA.", "ECO", "50-51", "Separar presión real y señal.", "Compare SNET/manómetro y tensión; la ventana de entrada documentada para el diagnóstico es 0,5–4,95 V en esa familia.", system="DVM", scope="outdoor"),
])
add_topic("component_checks", "fans-eev", "Ventiladores y EEV", "Motores BLDC, feedback y válvulas paso a paso.", [
    variant("Ventilador exterior E446/E447/E458", "Exterior DVM con Fan1/Fan2.", "ECO", "60", "Separar bloqueo, cable y driver.", "Compruebe giro, conector, alimentación, control y feedback antes de condenar la PBA.", system="DVM", scope="outdoor"),
    variant("EEV abierta/cerrada", "Interior o exterior con E151/E152/E702/E703/E422.", "ECO", "35-37", "Usar etapa de detección correcta.", "Primera y segunda detección usan códigos distintos; compruebe bobina, conector, pulso y respuesta térmica.", system="RAC/DVM"),
])

add_topic("technical_values", "quick-electrical-values", "Valores eléctricos rápidos", "Bus, sensores, comunicación y motores.", [
    variant("Mando cableado", "MWR-WE10N/WE10 identificado.", "FAQ", "wired controllers", "Confirmar alimentación antes de diagnosticar.", "Valor de referencia oficial: 12 VDC en el mando.", system="RAC/FJM/DVM", scope="controller"),
    variant("Sensor analógico de PBA", "Entrada de presión u otro sensor analógico.", "FAQ", "outdoor PCB sensor", "Comprobar lectura de placa.", "Si la PBA no lee entre 0,5 y 4,5 VDC en el terminal del sensor según la prueba indicada, la PBA puede ser defectuosa.", system="Samsung HVAC", scope="outdoor"),
    variant("Comunicación DVM", "F1-F2 y cableado de red.", "FAQ", "communication wire", "Evitar fallos intermitentes.", "16/2 trenzado apantallado, tierra solo en exterior y sin empalmes.", system="DVM"),
])
add_topic("technical_values", "refrigeration-reference", "Carga, vacío y límites", "Métodos compatibles con inverter.", [
    variant("Carga por peso", "Sistema inverter con sospecha de carga incorrecta.", "FAQ", "charging", "Evitar conclusiones por presiones variables.", "Repare fugas, haga prueba de presión, evacúe por debajo de 500 micrones y pese la carga de placa/tubería.", system="RAC/FJM/DVM"),
    variant("Triple evacuación", "Sistema donde se requiere eliminar humedad.", "FAQ", "triple evacuation", "Aplicar la secuencia oficial.", "5000/2000/<200 micrones con nitrógeno y tiempos 10/15/60 minutos según la secuencia publicada.", system="RAC/FJM/DVM"),
])

add_topic("normal_states", "normal-display-states", "Estados normales del display", "No sustituir componentes por dF, CF, CI o UP sin interpretar.", [
    variant("dF — desescarche", "Display muestra dF durante calefacción.", "SUPPORT", "estado dF", "Reconocer la secuencia normal.", "Durante el desescarche cambian compresor, válvula y ventiladores; espere a que finalice.", system="RAC"),
    variant("CF — limpiar filtro", "Display muestra CF.", "SUPPORT", "estado CF", "Realizar mantenimiento.", "Es un recordatorio; limpie y restablezca según el mando.", system="RAC"),
    variant("CI — Auto Clean", "Display muestra CI tras la marcha.", "SUPPORT", "estado CI", "No confundir secado con avería.", "La interior seca/limpia el intercambiador según la función.", system="RAC"),
    variant("UP — no preparado", "Exterior DVM muestra UP.", "QUICK", "18", "Completar Auto Trial.", "El sistema no habilita la operación normal hasta completar la prueba.", system="DVM S", scope="outdoor"),
])

add_topic("service_tools_boards", "snet-and-vrf-coder", "SNET Pro y VRF Coder", "Herramientas oficiales de diagnóstico y programación.", [
    variant("SNET Pro 2", "Sistema NASA compatible y service tool.", "SOFTWARE", "página oficial", "Registrar la red y variables.", "Para una avería sin código, la FAQ prescribe 60 min en test y 60 min en operación normal.", system="DVM"),
    variant("VRF Coder", "PC de servicio con familia identificada.", "VRFCODER", "página oficial", "Consultar option codes y ajustes.", "Incluye errores, programación interior/exterior, direccionamiento, ejemplos de display, refrigerante y conversor hexadecimal.", system="DVM/RAC"),
])
add_topic("service_tools_boards", "board-replacement", "Después de cambiar una PBA", "Option code, conectores, EEPROM y tracking.", [
    variant("PBA interior nueva", "Todos los pilotos interiores parpadean.", "FAQ", "new indoor board", "Programar la identidad.", "Introduzca el option/product code antes de buscar otra avería.", system="RAC/FJM/DVM", scope="indoor"),
    variant("PBA exterior/inverter", "E203/E205/E470 o sustitución física.", "ECO", "40, 70-76", "Restaurar configuración y comprobar comunicación.", "Copie DIP/diales/opciones, revise jumpers y conectores, descargue el bus y repita tracking.", system="DVM", scope="outdoor"),
])

add_topic("system_architecture", "recognize-samsung-family", "Reconocer la familia antes de aplicar una tabla", "La misma combinación o código no es universal.", [
    variant("RAC 9K/12K frente a 18K/24K/30K", "Tres LED YEL/GRN/RED sin display alfanumérico principal.", "SMART", "3-3–3-4", "Elegir la tabla exterior correcta.", "La potencia/familia cambia algunos patrones, aunque los colores coincidan.", system="RAC", scope="outdoor"),
    variant("FJM multisplit", "Dial de cantidad, K1/K2 y varias interiores.", "FJM", "3-1–3-12", "Usar E199/E201 y pipe check.", "El conteo y la asociación de tuberías forman parte del diagnóstico.", system="FJM", scope="outdoor"),
    variant("DVM S/DVM S2", "Red F1-F2, MCU opcional, display K y herramientas SNET.", "S2", "1-102", "Usar la capa VRF.", "Direcciones, subcódigos y PBA internas exigen conservar la arquitectura de red.", system="DVM"),
])


def build_topics() -> list[dict[str, Any]]:
    result = []
    variant_id = 1
    for topic_id, spec in enumerate(TOPICS, start=1):
        cat = CATEGORY_BY_SLUG[spec["category"]]
        rows = []
        for sort_order, item in enumerate(spec["variants"], start=1):
            row = {**item, "id": variant_id, "topic_id": topic_id, "sort_order": sort_order, "visible": 1}
            rows.append(row)
            variant_id += 1
        result.append({
            "id": topic_id,
            "brand_id": BRAND_ID,
            "category_id": cat["id"],
            "slug": spec["slug"],
            "title": spec["title"],
            "summary": spec["summary"],
            "active": 1,
            "category": cat,
            "variants": rows,
        })
    return result


def build_search(
    error_index: list[dict[str, Any]],
    error_details: list[dict[str, Any]],
    topics: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    details_by_id = {row["id"]: row for row in error_details}
    entries = []
    for row in error_index:
        detail = details_by_id[row["id"]]
        text_parts = [row["code_display"], row["short_label"], *row["aliases"], *row["tags"]]
        for interpretation in detail["interpretations"]:
            text_parts.extend([interpretation["title"], interpretation["description"]])
            text_parts.extend(x["body"] for x in interpretation["info_items"])
            for context in interpretation["indication_contexts"]:
                text_parts.extend([
                    context.get("display_location", ""), context.get("family_hint", ""),
                    context.get("relationship", ""), context.get("counting_rule", ""),
                    context.get("cycle_note", ""), context.get("sequence", ""),
                ])
                for led in context.get("led_indicators", []):
                    text_parts.extend([led.get("label", ""), led.get("color", ""), led.get("state", "")])
        entries.append({
            "type": "error", "id": row["id"], "code": row["code_display"],
            "title": row["short_label"], "subtitle": f'{row["interpretation_count"]} interpretación(es)',
            "haystack": normalize(" ".join(text_parts)),
        })
    for topic in topics:
        for row in topic["variants"]:
            text_parts = [
                topic["title"], topic["summary"], row["title"], row["recognition"],
                row["purpose"], row["summary"], row["system_type"],
            ]
            text_parts.extend(x["body"] for x in row["sections"])
            text_parts.extend(x["instruction"] + " " + (x.get("expected_result") or "") for x in row["steps"])
            for pattern in row.get("led_patterns", []):
                text_parts.extend([pattern.get("code_display", ""), pattern.get("relationship", ""), pattern.get("family_hint", "")])
                for led in pattern.get("led_indicators", []):
                    state_es = {"on":"fijo encendido","off":"apagado","blink":"parpadea"}.get(led.get("state"), led.get("state", ""))
                    text_parts.extend([led.get("label", ""), led.get("color", ""), state_es])
            for parameter in row["parameters"]:
                text_parts.extend([parameter.get("parameter_code") or "", parameter["name"], parameter.get("description") or ""])
                for option in parameter.get("options", []):
                    text_parts.extend([option.get("option_value") or "", option.get("option_label") or "", option.get("effect") or ""])
            if row["controller"]:
                text_parts.extend(str(value or "") for value in row["controller"].values())
            entries.append({
                "type": "variant", "id": row["id"], "topic_id": topic["id"],
                "title": row["title"], "subtitle": topic["title"],
                "haystack": normalize(" ".join(text_parts)),
            })
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
    write_json(WEB_DIR / "variant_map.json", {
        str(row["id"]): topic["id"]
        for topic in topics
        for row in topic["variants"]
    })

    categories = []
    by_category: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for topic in topics:
        by_category[topic["category_id"]].append({
            "id": topic["id"], "slug": topic["slug"], "title": topic["title"],
            "summary": topic["summary"], "active": 1, "variant_count": len(topic["variants"]),
        })
    for ident, slug, name, description in CATEGORIES:
        categories.append({
            "id": ident, "slug": slug, "name": name, "description": description,
            "sort_order": ident * 10, "active": 1, "topics": by_category[ident],
        })
    write_json(WEB_DIR / "navigation.json", {
        "metadata": {
            "schema_name": "Super Tecnico",
            "navigation_model": "brand_category_topic_variant",
            "schema_version": "2.3.0",
            "data_version": "1.0.0",
            "last_update_utc": now,
            "reference_brand": "Samsung",
            "verification_warning": "Completa respecto al corpus Samsung Referencia V1. Confirme siempre familia, tamaño, PBA y lugar de lectura. Los patrones LED no son universales.",
        },
        "categories": categories,
    })
    write_json(WEB_DIR / "sources.json", [
        {
            "id": ident, "brand_id": BRAND_ID, "title": row["title"],
            "document_ref": row["document_ref"], "document_type": row["type"],
            "publication_date": row["year"], "language": "en/es",
            "source_url": row["source_url"], "status": "reviewed",
            "notes": "Fuente oficial Samsung/Samsung HVAC revisada para Referencia V1.",
        }
        for ident, row in enumerate(SOURCES.values(), start=1)
    ])
    write_json(WEB_DIR / "coverage.json", [
        {
            "id": ident, "brand_id": BRAND_ID, "area_slug": slug, "area_name": name,
            "equipment_scope": "Samsung — RAC, FJM, DVM S/S2 e interiores",
            "coverage_status": "reference_v1", "source_count": len(SOURCES),
            "notes": description, "last_reviewed": "2026-07-28",
        }
        for ident, slug, name, description in CATEGORIES
    ])
    counts = {
        "categories": len(CATEGORIES),
        "topics": len(topics),
        "variants": sum(len(x["variants"]) for x in topics),
        "errors": len(error_index),
        "search_entries": len(search_entries),
    }
    write_json(BRAND_DIR / "brand.json", {
        "slug": "samsung",
        "name": "Samsung",
        "display_name": "Samsung",
        "enabled": True,
        "web_data": "web",
        "media": "media",
        "publish_media": False,
        "static_site": True,
        "schema_version": "2.3.0",
        "data_version": "1.0.0",
        "exported_at_utc": now,
        "counts": counts,
        "notes": "Samsung Referencia V1: RAC, FJM, DVM S/S2, mandos, MCU, herramientas y tablas visuales de pilotos exteriores. Sin PDF ni capturas.",
    })
    return counts


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
