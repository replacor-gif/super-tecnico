#!/usr/bin/env python3
"""Construye Roca / Clima Roca York Referencia V1.

La selección es histórica y deliberadamente restrictiva: solo se incorporan
familias cuya documentación pertenece a la etapa industrial de Clima Roca York
y cuya procedencia puede acreditarse. No se publican PDF ni capturas.
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
BRAND_DIR = ROOT / "data" / "brands" / "roca-clima"
WEB_DIR = BRAND_DIR / "web"
BRAND_ID = 15

core.BRAND_DIR = BRAND_DIR
core.WEB_DIR = WEB_DIR
core.BRAND_ID = BRAND_ID

core.SOURCES = {
    "AVO03": {
        "title": "AVO-72/172 B-BG, BLI-72/152, BCI-72/172 y BVI-102/152 — Información técnica",
        "document_ref": "N-27134-1003",
        "source_url": "https://es.scribd.com/document/490126454/AVO-72-172-B-BG-BLI-72-152-BCI-72-172-BVI-102-152",
        "type": "technical_manual",
        "year": "2003",
    },
    "AVO04": {
        "title": "AVO-74/174 BG — Información técnica y control electrónico",
        "document_ref": "INF-27426",
        "source_url": "https://es.scribd.com/document/725907196/inf27426",
        "type": "technical_manual",
        "year": "2004",
    },
    "DPC1": {
        "title": "Clima Roca York DPC-1 — Termostato programable",
        "document_ref": "DPC-1-INSTALLATION-OPERATION",
        "source_url": "https://www.manualslib.de/manual/559785/Clima-Roca-York-Dpc-1.html?page=7",
        "type": "controller_manual",
        "year": "etapa Clima Roca York",
    },
    "YLCC": {
        "title": "YLCC/YLCC-H 42 a 152 — Información técnica",
        "document_ref": "N-27344-1204M",
        "source_url": "https://www.manualslib.es/manual/140787/York-Ylcc-42.html?page=35",
        "type": "technical_manual",
        "year": "2004",
    },
    "YCSA50": {
        "title": "YCSA/YCSA-H 50 y 60 T/TP — Instalación",
        "document_ref": "Y-R61063-1104",
        "source_url": "https://usermanual.wiki/York/YcsaUsersManual.1957807651.pdf",
        "type": "installation_manual",
        "year": "2004",
    },
    "YCSA120": {
        "title": "YCSA/YCSA-H 120 a 180 — Información técnica",
        "document_ref": "YCSA-120-180-TECHNICAL",
        "source_url": "https://www.manualslib.es/manual/140788/York-Ycsa-120.html?page=46",
        "type": "technical_manual",
        "year": "etapa Clima Roca York",
    },
    "ROCA_HISTORY": {
        "title": "Roca — Historia corporativa",
        "document_ref": "ROCA-HISTORY-2005-HVAC-SALE",
        "source_url": "https://publications.apac.roca.com/drive/11748/449458/index-5.html",
        "type": "official_corporate_history",
        "year": "2005",
    },
    "BOE": {
        "title": "BORME — cambio de denominación de Clima Roca York",
        "document_ref": "BORME-C-2007-16073",
        "source_url": "https://boe.es/diario_borme/txt.php?id=BORME-C-2007-16073",
        "type": "official_register",
        "year": "2007",
    },
}

core.CATEGORIES = [
    (1, "errors", "Errores, alarmas e incidencias", "Códigos separados por interfaz, familia y gravedad."),
    (2, "outdoor_diagnostics", "Pilotos y control exterior", "Pilotos verde/rojo y secuencias de placa de equipos históricos."),
    (3, "diagnostic_access", "Obtención de códigos", "Lectura en termostato DPC-1, control chiller y placa."),
    (4, "history_reset", "Rearme y memoria", "Reset por termostato, TEST, alimentación y control local."),
    (5, "service_modes", "Modos de servicio", "TEST, acortamiento de tiempos, búsqueda de accesorios y desescarche."),
    (6, "configuration", "DIP y programación", "Desescarche, tipo de equipo, válvula de cuatro vías y termostato."),
    (7, "controllers_buses", "Mandos, señales y buses", "DPC-1, 24 V CA, señales G/Y/W/O-B y comunicación."),
    (8, "chillers", "Enfriadoras y bombas de calor", "YLCC y YCSA: alarmas, entradas, bombas, caudal y parada."),
    (9, "commissioning", "Puesta en marcha", "Comprobaciones previas, caudal, fases, presiones y control remoto."),
    (10, "operational_effects", "Efecto sobre el funcionamiento", "Diferencia entre aviso, parada de circuito y parada general."),
    (11, "component_checks", "Comprobación de componentes", "Sondas, presostatos, ventiladores, compresores y bombas."),
    (12, "technical_values", "Valores y umbrales", "Temperaturas, tiempos, contactos, tensiones y límites documentados."),
    (13, "normal_states", "Estados normales", "Desescarche, retardos y sucesos que no bloquean el equipo."),
    (14, "service_tools_boards", "Placas y entradas de servicio", "Entradas ID/B, relés, TEST y trabajo después de intervenir."),
    (15, "system_architecture", "Reconocer la familia", "Cómo elegir la tabla correcta sin exigir el modelo."),
    (16, "provenance", "Procedencia y autenticidad", "Qué se admite como fabricación Roca y qué se excluye."),
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
    behavior: str,
    technical: str,
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
        behavior=behavior,
        technical=technical,
        aliases=aliases,
    )


# AVO/BLI/BCI/BVI 2003: el verde informa incidencias sin parada; el rojo,
# averías que paran y se rearman. Se conservan ambas capas por separado.
AVO_INCIDENTS = [
    ("1-1", "Sonda de descarga abierta o descarga superior a 150 °C", "sensor"),
    ("1-2", "Sonda de líquido abierta o cortocircuitada", "sensor"),
    ("1-3", "Sonda exterior abierta o cortocircuitada", "sensor"),
    ("1-4", "Sonda interior abierta o cortocircuitada", "sensor"),
    ("1-5", "Temperatura exterior demasiado baja para calefacción", "pressure"),
    ("2-1", "Orden Y1/Y2 recibida sin señal G", "configuration"),
    ("2-2", "Orden W recibida sin señal B", "configuration"),
    ("2-3", "Orden W recibida sin señal G", "configuration"),
    ("2-4", "Orden Y2 recibida sin Y1", "configuration"),
    ("3-1", "Protección térmica de calefacción auxiliar AUX1", "power"),
    ("3-2", "Protección térmica de calefacción auxiliar AUX2", "power"),
    ("3-3", "Protección térmica de calefacción de emergencia EM1", "power"),
    ("3-4", "Protección térmica de calefacción de emergencia EM2", "power"),
    ("4-1", "Desescarches repetidos", "normal"),
    ("4-2", "La temperatura de descarga no recupera", "pressure"),
    ("4-4", "La temperatura de calefacción no recupera", "pressure"),
]
for code, title, profile in AVO_INCIDENTS:
    err(
        code,
        title,
        profile,
        "AVO03",
        "22-25",
        family="AVO/BLI/BCI/BVI — piloto verde de incidencias",
        scope="outdoor",
        behavior="La incidencia se señaliza con el piloto verde y no detiene el equipo.",
        technical="Lea primero la secuencia completa; el grupo anterior y posterior a la pausa forman un único código.",
        aliases=[f"piloto verde {code}", f"incidencia {code}"],
    )

AVO_RED_FAULTS = [
    ("1", "Temperatura de descarga excedida o sonda de descarga en corto", "pressure"),
    ("2", "Protección de alta presión", "pressure"),
    ("3", "Protección de baja presión", "pressure"),
    ("4", "Protección térmica del ventilador interior", "fan"),
    ("5", "Arranques repetidos en frío o aspiración inferior a -25 °C", "pressure"),
    ("6", "Temperatura de líquido inferior a -30 °C", "pressure"),
]
for code, title, profile in AVO_RED_FAULTS:
    err(
        code,
        title,
        profile,
        "AVO03",
        "24-25",
        family="AVO/BLI/BCI/BVI — piloto rojo de avería",
        scope="outdoor",
        behavior="La avería enciende o hace parpadear el piloto rojo y detiene la función protegida.",
        technical="Rearme documentado mediante termostato en OFF cuando hay comunicación, pulsador TEST, corte de alimentación o bus de comunicación.",
        aliases=[f"piloto rojo {code}", f"avería AVO {code}"],
    )

# Generación AVO posterior: la numeración se reutiliza con otra organización.
AVO04_EVENTS = [
    ("1-1", "Temperatura de descarga superior a 130 °C", "pressure", "fault"),
    ("1-2", "Protección de alta presión", "pressure", "fault"),
    ("1-3", "Protección de baja presión opcional", "pressure", "fault"),
    ("1-5", "Arranques repetidos o aspiración inferior a -25 °C", "pressure", "fault"),
    ("1-6", "Temperatura de líquido inferior a -30 °C", "pressure", "fault"),
    ("2-1", "Desescarches repetidos", "normal", "incident"),
    ("2-2", "La temperatura de descarga no recupera", "pressure", "incident"),
    ("2-3", "Temperatura exterior demasiado baja", "pressure", "incident"),
    ("2-4", "Proceso de desescarche activo", "normal", "incident"),
    ("2-5", "Entrada HP2 activada", "pressure", "incident"),
    ("3-1", "Sonda de aspiración abierta o cortocircuitada", "sensor", "incident"),
    ("3-2", "Sonda de líquido abierta o cortocircuitada", "sensor", "incident"),
    ("3-3", "Sonda de descarga abierta o cortocircuitada", "sensor", "incident"),
    ("3-4", "Sonda exterior abierta o cortocircuitada", "sensor", "incident"),
    ("4-1", "Sin comunicación con el termostato", "communication", "incident"),
]
for code, title, profile, event_type in AVO04_EVENTS:
    err(
        code,
        title,
        profile,
        "AVO04",
        "sección Control electrónico y tabla de LED",
        family="AVO 74/174 BG — secuencia de LED de segunda generación",
        scope="outdoor",
        behavior=(
            "La avería detiene la función protegida y requiere corregir la causa y rearmar."
            if event_type == "fault"
            else "La placa registra o indica la incidencia; consulte si el funcionamiento continúa o queda limitado."
        ),
        technical="No mezclar esta secuencia con la tabla AVO de 2003: la misma combinación puede tener otro significado.",
        aliases=[f"AVO segunda generación {code}", f"LED {code}"],
    )

# DPC-1: códigos mostrados por el termostato. Los 11/21/31, etc. indican
# circuitos o etapas equivalentes y se mantienen como códigos independientes.
DPC_MACHINE = [
    ("11", "Temperatura de descarga excedida — circuito o etapa 1", "pressure"),
    ("21", "Temperatura de descarga excedida — circuito o etapa 2", "pressure"),
    ("31", "Temperatura de descarga excedida — circuito o etapa 3", "pressure"),
    ("12", "Alta presión, térmico de ventilador exterior o módulo de compresor — etapa 1", "pressure"),
    ("22", "Alta presión, térmico de ventilador exterior o módulo de compresor — etapa 2", "pressure"),
    ("32", "Alta presión, térmico de ventilador exterior o módulo de compresor — etapa 3", "pressure"),
    ("13", "Baja presión — circuito 1", "pressure"),
    ("23", "Baja presión — circuito 2", "pressure"),
    ("33", "Baja presión — circuito 3", "pressure"),
    ("14", "Protección térmica del ventilador interior", "fan"),
    ("15", "Arranques repetidos o aspiración inferior a -25 °C — circuito 1", "pressure"),
    ("25", "Arranques repetidos o aspiración inferior a -25 °C — circuito 2", "pressure"),
    ("35", "Arranques repetidos o aspiración inferior a -25 °C — circuito 3", "pressure"),
    ("16", "Temperatura de líquido inferior a -30 °C — circuito 1", "pressure"),
    ("26", "Temperatura de líquido inferior a -30 °C — circuito 2", "pressure"),
    ("36", "Temperatura de líquido inferior a -30 °C — circuito 3", "pressure"),
    ("41", "Térmico de gas 1 o calefacción eléctrica 1", "power"),
    ("42", "Térmico de gas 2 o calefacción eléctrica 2", "power"),
    ("43", "Protección de la tercera etapa de calefacción", "power"),
    ("44", "Protección de la cuarta etapa de calefacción", "power"),
    ("45", "Economizador o batería de agua caliente: sonda exterior/retorno", "sensor"),
    ("46", "Detector de humo o protección por temperatura alta", "power"),
]
for code, title, profile in DPC_MACHINE:
    err(
        code,
        title,
        profile,
        "DPC1",
        "7-8",
        family="Termostato cableado DPC-1 — error recibido de la máquina",
        scope="controller",
        behavior="El termostato muestra la llave parpadeando para errores de máquina; el alcance depende de la etapa o circuito indicado.",
        technical="Los códigos 0 a 90 proceden de la máquina. Confirme el equipo conectado antes de aplicar el significado.",
        aliases=[f"DPC {code}", f"termostato {code}"],
    )

DPC_CONTROLLER = [
    ("91", "Sonda ambiente del termostato abierta, en corto o fuente seleccionada no válida", "sensor"),
    ("92", "Sonda interna del termostato sin calibrar", "sensor"),
    ("93", "Fallo de comunicación del termostato", "communication"),
    ("94", "Alarma aplicada al terminal AL", "power"),
    ("95", "Sonda o entrada S5 ausente", "sensor"),
    ("96", "Sonda o entrada S6 ausente", "sensor"),
    ("97", "Sonda o entrada S7 ausente", "sensor"),
    ("98", "Sonda o entrada S8 ausente", "sensor"),
    ("99", "Sonda digital exterior ausente", "sensor"),
]
for code, title, profile in DPC_CONTROLLER:
    err(
        code,
        title,
        profile,
        "DPC1",
        "7-8",
        family="Termostato cableado DPC-1 — diagnóstico propio",
        scope="controller",
        behavior="La llave queda fija para alarmas propias o de sondas; 93 identifica la pérdida de comunicación.",
        technical="Separe estos códigos 91-99 de los códigos de máquina 0-90.",
        aliases=[f"DPC-1 {code}", f"alarma mando {code}"],
    )

# YLCC: tabla alfanumérica completa, con tipo de rearme conservado.
YLCC_ERRORS = [
    ("E1", "Sonda B1", "sensor", "automático"),
    ("E2", "Sonda B2", "sensor", "automático"),
    ("E3", "Sonda B3", "sensor", "automático"),
    ("E4", "Sonda B4", "sensor", "automático"),
    ("E5", "Sonda B5", "sensor", "automático"),
    ("EE", "Memoria EEPROM del control", "pcb", "automático"),
    ("FL", "Control de caudal de agua", "pressure", "automático"),
    ("H1", "Alta presión del circuito 1", "pressure", "manual"),
    ("L1", "Baja presión del circuito 1", "pressure", "manual"),
    ("C1", "Térmico de compresor 1 o ventilador 1 según versión YLCC", "compressor", "manual"),
    ("F1", "Térmico de ventilador 1 en versión YLCC-H", "fan", "manual"),
    ("A1", "Protección antihielo del circuito 1", "pressure", "manual"),
    ("d1", "Desescarche del circuito 1", "normal", "automático"),
    ("r1", "Fallo de desescarche del circuito 1", "pressure", "automático"),
    ("n1", "Aviso de mantenimiento del compresor 1", "normal", "manual"),
    ("H2", "Alta presión del circuito 2", "pressure", "manual"),
    ("L2", "Baja presión del circuito 2", "pressure", "manual"),
    ("C2", "Térmico de compresor 2 o ventilador 2 según versión YLCC", "compressor", "manual"),
    ("F2", "Térmico de ventilador 2 en versión YLCC-H", "fan", "manual"),
    ("A2", "Protección antihielo del circuito 2", "pressure", "manual"),
    ("d2", "Desescarche del circuito 2", "normal", "automático"),
    ("r2", "Fallo de desescarche del circuito 2", "pressure", "automático"),
    ("n2", "Aviso de mantenimiento del compresor 2", "normal", "manual"),
    ("Cn", "Error de comunicación del control", "communication", "automático"),
]
for code, title, profile, reset in YLCC_ERRORS:
    err(
        code,
        title,
        profile,
        "YLCC",
        "35",
        family="Enfriadora/bomba de calor YLCC-H 42 a 152 — display local",
        scope="system",
        behavior=(
            "Estado o aviso con recuperación automática cuando desaparece la condición."
            if reset == "automático"
            else "La alarma requiere rearme manual después de corregir la causa."
        ),
        technical=f"La tabla del fabricante clasifica el rearme como {reset}. Las entradas asociadas se consultan en la misma tabla.",
        aliases=[f"YLCC {code}", f"chiller {code}"],
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
    system: str = "Roca / Clima Roca York",
    scope: str = "system",
    steps: list[dict[str, Any]] | None = None,
    led_patterns: list[dict[str, Any]] | None = None,
    controller_data: dict[str, Any] | None = None,
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
        led_patterns=led_patterns,
        controller_data=controller_data,
    )


def add_topic(category: str, slug: str, title: str, summary: str, variants: list[dict[str, Any]]) -> None:
    core.add_topic(category, slug, title, summary, variants)


def led_pattern(code: str, relationship: str, color: str, sequence: str) -> dict[str, Any]:
    return {
        "code_display": code,
        "indication_type": "outdoor_led_sequence",
        "display_location": "placa de control exterior",
        "family_hint": "AVO/BLI/BCI/BVI de la etapa Clima Roca York",
        "relationship": relationship,
        "led_indicators": [{
            "label": f"Piloto {color}",
            "color": "red" if color == "rojo" else "green",
            "state": "blink",
            "detail": sequence,
        }],
        "counting_rule": "Cuente el primer grupo, espere la pausa y cuente el segundo. Observe al menos dos ciclos.",
        "cycle_note": "El guion separa los dos grupos de destellos; no es un número decimal.",
        "sequence": sequence,
    }


AVO_GREEN_PATTERNS = [
    led_pattern(code, title, "verde", f"{code.split('-')[0]} destello(s), pausa, {code.split('-')[1]} destello(s)")
    for code, title, _ in AVO_INCIDENTS
]
AVO04_PATTERNS = [
    led_pattern(code, title, "rojo" if kind == "fault" else "verde", f"{code.split('-')[0]} destello(s), pausa, {code.split('-')[1]} destello(s)")
    for code, title, _, kind in AVO04_EVENTS
]


add_topic("errors", "three-error-layers", "Tres capas de error que no deben mezclarse", "La misma cifra cambia entre piloto exterior, termostato y chiller.", [
    v("Piloto exterior AVO", "Uno o dos grupos de destellos en la placa exterior.", "AVO03", "22-25", "Leer la secuencia correcta.", "El color separa incidencia sin parada y avería con parada.", system="AVO/BLI/BCI/BVI", scope="outdoor"),
    v("Termostato DPC-1", "LCD con símbolo de llave y código 0-99.", "DPC1", "7-8", "Separar máquina y mando.", "0-90 llegan de la máquina; 91-99 diagnostican el termostato o sus entradas.", system="DPC-1", scope="controller"),
    v("Control local YLCC", "Display alfanumérico de una enfriadora.", "YLCC", "30-36", "Aplicar la tabla de chiller.", "E, H, L, C, F, A, d, r, n y Cn tienen significado y rearme propios.", system="YLCC/YLCC-H"),
])

add_topic("outdoor_diagnostics", "avo-green-incidents", "AVO: tabla completa del piloto verde", "Son incidencias registradas que no detienen el equipo en la familia documentada.", [
    v("Secuencias 1-1 a 4-4", "Placa con piloto verde y códigos por dos grupos.", "AVO03", "22-25", "Identificar sensores, señales y desescarche.", "El primer grupo identifica la familia; el segundo concreta la entrada o la condición.", system="AVO/BLI/BCI/BVI 2003", scope="outdoor", led_patterns=AVO_GREEN_PATTERNS),
    v("No confundir incidencia con avería", "El equipo sigue funcionando y solo el verde señala.", "AVO03", "24-25", "Evitar un reset innecesario.", "Anote el evento y compruebe la causa, pero no suponga una parada de seguridad.", system="AVO/BLI/BCI/BVI 2003", scope="outdoor"),
])

add_topic("outdoor_diagnostics", "avo-red-faults", "AVO: piloto rojo y averías con parada", "La generación debe confirmarse antes de contar.", [
    v("AVO 2003: códigos simples 1 a 6", "Piloto rojo con un único número de destellos.", "AVO03", "24-25", "Traducir la avería bloqueante.", "Incluye descarga, alta/baja, térmico interior, arranques repetidos y líquido muy frío.", system="AVO/BLI/BCI/BVI 2003", scope="outdoor", led_patterns=[
        led_pattern(code, title, "rojo", f"{code} destello(s), pausa y repetición")
        for code, title, _ in AVO_RED_FAULTS
    ]),
    v("AVO segunda generación: dos grupos", "Placa posterior con secuencias 1-1 a 4-1.", "AVO04", "tabla de LED", "Aplicar la tabla posterior.", "No traslade los significados de 2003: la organización del código cambió.", system="AVO 74/174 BG", scope="outdoor", led_patterns=AVO04_PATTERNS),
])

add_topic("diagnostic_access", "dpc-read-errors", "DPC-1: obtener y clasificar el código", "El símbolo de llave indica el origen y el estado.", [
    v("Código de máquina 0-90", "Llave parpadeando y número hasta 90.", "DPC1", "7-8", "Leer el fallo recibido.", "Consulte después la familia de la máquina; el DPC-1 solo transmite su número.", system="DPC-1", scope="controller", steps=[
        step(1, "Anote el número y si la llave parpadea o permanece fija.", phase="prepare"),
        step(2, "Si está entre 0 y 90 y la llave parpadea, trátelo como error recibido de la máquina."),
        step(3, "Identifique la familia conectada antes de abrir la interpretación.", phase="verify"),
    ]),
    v("Código propio 91-99", "Llave fija y número de 91 a 99.", "DPC1", "7-8", "Diagnosticar mando, comunicación o sonda.", "91-99 pertenecen al termostato y a las entradas S5-S8/sensor exterior.", system="DPC-1", scope="controller"),
])

add_topic("diagnostic_access", "ylcc-read-display", "YLCC: leer display, LED y zumbador", "La letra forma parte del código.", [
    v("Código alfanumérico", "Terminal local con display y LED amarillo.", "YLCC", "30-36", "Conservar mayúscula/minúscula.", "d1 es desescarche; r1 fallo de desescarche; n1 mantenimiento. No normalice las tres como el número 1.", system="YLCC/YLCC-H"),
    v("Gravedad y aviso acústico", "LED amarillo rápido o normal y posible zumbador/relé.", "YLCC", "35-36", "Distinguir alarma seria y estado recuperable.", "La tabla separa alarmas con rearme manual de estados automáticos y comunicación.", system="YLCC/YLCC-H"),
])

add_topic("history_reset", "avo-reset-methods", "AVO: cuatro formas documentadas de rearme", "Antes de borrar, registre color, secuencia y demanda.", [
    v("Termostato en OFF", "Hay comunicación implementada con la placa.", "AVO03", "24-25", "Rearmar desde zona ocupada.", "El manual limita este método a tres rearmes diarios.", system="AVO/BLI/BCI/BVI", scope="controller"),
    v("Pulsador TEST", "Placa accesible por técnico cualificado.", "AVO03", "24-25", "Borrar el bloqueo local.", "Pulse únicamente después de corregir la causa y anotar la secuencia.", system="AVO/BLI/BCI/BVI", scope="outdoor"),
    v("Corte de alimentación o bus", "El equipo no responde a los métodos anteriores.", "AVO03", "24-25", "Reiniciar el control.", "Restablezca la tensión solo después de las comprobaciones de seguridad; el corte borra evidencia temporal.", system="AVO/BLI/BCI/BVI"),
])

add_topic("history_reset", "ylcc-reset-types", "YLCC: rearme automático y manual", "La ficha de cada código conserva su tipo de recuperación.", [
    v("Automático", "E1-E5, EE, FL, d/r y Cn según la tabla.", "YLCC", "35", "Esperar recuperación solo si está autorizada.", "El control recupera cuando la condición válida vuelve; investigue repeticiones.", system="YLCC/YLCC-H"),
    v("Manual", "H/L/C/F/A/n según circuito.", "YLCC", "35", "No rearmar sin comprobar.", "Alta, baja, térmicos, antihielo y mantenimiento exigen intervención o confirmación.", system="YLCC/YLCC-H"),
])

add_topic("service_modes", "avo-test-button", "AVO: funciones del pulsador TEST", "Pulsación corta y larga hacen cosas distintas.", [
    v("Pulsación corta", "Placa energizada y temporizadores activos.", "AVO04", "control electrónico", "Acortar tiempos de espera.", "La pulsación corta reduce temporizadores para la comprobación; no anula protecciones.", system="AVO 74/174 BG", scope="outdoor"),
    v("Pulsación larga superior a 2 s", "Se necesita reconocer accesorios o restaurar averías.", "AVO03", "22-25", "Iniciar búsqueda de accesorios/rearme.", "Mantener TEST más de dos segundos inicia la búsqueda documentada y puede rearmar fallos.", system="AVO/BLI/BCI/BVI", scope="outdoor"),
])

add_topic("service_modes", "forced-defrost", "Desescarche: prueba e interpretación", "El control mantiene límites aunque se acorten temporizadores.", [
    v("Desescarche programado por DIP", "Placa AVO con SW1/SW2.", "AVO03", "22-24", "Elegir intervalo documentado.", "Las combinaciones permiten 30, 60 o 90 minutos; la segunda generación añade 0 según configuración.", system="AVO/BLI/BCI/BVI", scope="outdoor"),
    v("Incidencia 2-4", "Segunda generación indica 2-4 durante el proceso.", "AVO04", "tabla de LED", "Reconocer un estado normal.", "2-4 informa desescarche activo; no es por sí solo una avería.", system="AVO 74/174 BG", scope="outdoor"),
])

add_topic("configuration", "avo-dip-switches", "AVO: programación mediante DIP", "Corte tensión antes de cambiar y haga que la placa relea la configuración.", [
    v("Intervalo de desescarche", "DIP 1 y 2 en placa exterior.", "AVO03", "22-24", "Ajustar 30/60/90 min.", "Use la tabla de la generación exacta; la posterior incluye una combinación 0.", system="AVO/BLI/BCI/BVI", scope="outdoor"),
    v("Ventilador y calefacción auxiliar", "DIP 3 cambia de función entre generaciones.", "AVO03", "22-24", "Evitar copiar posiciones.", "En una familia controla ventilador durante desescarche; en otra declara calefacción eléctrica auxiliar.", system="AVO/AVO-BG", scope="outdoor"),
    v("Tipo de equipo y válvula", "DIP 5, 6 y 7.", "AVO04", "control electrónico", "Definir frío/bomba de calor y lógica O/B.", "DIP 5 selecciona frío o bomba de calor; 6 la activación de cuatro vías; 7 interpreta B/O.", system="AVO 74/174 BG", scope="outdoor"),
])

add_topic("configuration", "dpc-dip-switches", "DPC-1: tabla completa SW1", "Los seis interruptores cambian mando y máquina.", [
    v("SW1-1 a SW1-3", "Banco de seis DIP en la parte posterior.", "DPC1", "7", "Bloqueo, AUTO PROG y O/B.", "1 bloquea teclado; 2 habilita AUTO PROG; 3 define si 24 V en O/B corresponde a calor o frío.", system="DPC-1", scope="controller"),
    v("SW1-4 a SW1-6", "Mismo banco, configuración de fábrica OFF.", "DPC1", "7", "Retardo, etapas y ventilador.", "4 selecciona 2 o 4 minutos; 5 mono/multietapa; 6 ventilador de tres o una velocidad.", system="DPC-1", scope="controller"),
])

add_topic("controllers_buses", "dpc-signals", "DPC-1: señales y proceso de diagnóstico", "El mando trabaja con señales de 24 V CA y entradas propias.", [
    v("Demanda G/Y/W/O-B", "Termostato conectado a unidad compatible.", "DPC1", "7-10", "Comprobar órdenes coherentes.", "La placa AVO puede registrar Y sin G, W sin B/G o Y2 sin Y1; compruebe demanda y cable.", system="DPC-1 + AVO", scope="controller"),
    v("Entrada AL y sondas S5-S8", "DPC muestra 94-98.", "DPC1", "7-8", "Separar alarma externa y sensor ausente.", "94 corresponde al terminal AL; 95-98 indican la entrada S concreta que falta.", system="DPC-1", scope="controller"),
    v("Comunicación 93", "DPC alimentado pero sin intercambio válido.", "DPC1", "7-8", "Aislar mando, cable y placa.", "Compruebe alimentación de control, continuidad, terminales y electrónica en ambos extremos.", system="DPC-1", scope="controller"),
])

add_topic("chillers", "ylcc-alarm-table", "YLCC: tabla de alarmas por circuito", "El sufijo 1/2 identifica el circuito frigorífico.", [
    v("Circuito 1", "Códigos H1, L1, C1, F1, A1, d1, r1 y n1.", "YLCC", "35", "Localizar el primer circuito.", "La letra distingue presión, térmico, antihielo, desescarche o mantenimiento.", system="YLCC/YLCC-H"),
    v("Circuito 2", "Códigos H2, L2, C2, F2, A2, d2, r2 y n2.", "YLCC", "35", "Localizar el segundo circuito.", "No confunda el sufijo con el número de destellos; es el circuito.", system="YLCC/YLCC-H"),
])

add_topic("chillers", "ycsa120-alarm-effects", "YCSA 120-180: qué para cada alarma", "La tabla OFF especifica circuito, ventilador, bomba y sistema.", [
    v("Alarma seria ID1", "Entrada FC/PG en la tabla de alarmas.", "YCSA120", "46", "Reconocer parada total.", "Detiene circuitos 1 y 2, ventiladores, bomba y sistema; rearme manual.", system="YCSA/YCSA-H 120-180"),
    v("Antihielo B6", "Protección de agua activa.", "YCSA120", "46", "Mantener circulación cuando corresponde.", "Detiene circuitos, ventiladores y sistema; la tabla no ordena parar la bomba.", system="YCSA/YCSA-H 120-180"),
    v("Térmico de bomba ID4/ID18", "Una de dos bombas se protege.", "YCSA120", "46", "Determinar continuidad.", "Si existe segunda bomba, arranca la disponible; sin reserva se detiene todo el sistema.", system="YCSA/YCSA-H 120-180"),
    v("Control de caudal ID2", "Entrada PDW/FS sin caudal válido.", "YCSA120", "46", "Proteger intercambiador.", "Detiene ambos circuitos, ventiladores, bomba y sistema; el retardo cambia entre arranque y marcha.", system="YCSA/YCSA-H 120-180"),
])

add_topic("chillers", "ycsa120-circuit-effects", "YCSA 120-180: parada parcial por circuito", "Térmicos, presostatos y ventiladores no siempre paran toda la máquina.", [
    v("Térmico de ventiladores ID9/ID14", "Falla un grupo de ventilación exterior.", "YCSA120", "46", "Aislar el circuito afectado.", "Detiene el circuito y ventiladores correspondientes; primer evento en 60 min puede recuperar, el segundo exige rearme.", system="YCSA/YCSA-H 120-180", scope="outdoor"),
    v("Térmico de compresor ID7/ID8/ID12/ID13", "Entrada asociada a un compresor.", "YCSA120", "46", "Mantener el resto si está autorizado.", "Detiene el compresor afectado; la repetición dentro de 60 min cambia el tipo de rearme.", system="YCSA/YCSA-H 120-180", scope="outdoor"),
    v("Presostatos HP/LP", "Entradas ID5/ID6 e ID10/ID11.", "YCSA120", "46", "Detener solo el circuito protegido.", "Alta o baja presión detienen el circuito y su ventilación; confirme el presostato y la presión real.", system="YCSA/YCSA-H 120-180", scope="outdoor"),
])

add_topic("commissioning", "ycsa50-wiring", "YCSA 50/60: control local y conexiones", "El esquema identifica seguridad y señales remotas.", [
    v("Entradas de seguridad", "Placa chiller µ y bornero de baja tensión.", "YCSA50", "9-11", "Verificar antes del arranque.", "Compruebe presostatos alta/baja, control de caudal, térmicos, sondas, termostatos y contactores.", system="YCSA/YCSA-H 50/60"),
    v("Mando remoto", "Bornero con ON/OFF remoto y selección frío/calor.", "YCSA50", "9-11", "Probar órdenes externas.", "Confirme contactos y común sin introducir tensión donde el esquema espera una entrada de control.", system="YCSA/YCSA-H 50/60"),
    v("Salida de alarma", "Contacto libre de tensión para alarma general.", "YCSA50", "9-11", "Integrar señal externa.", "El manual especifica contacto libre de tensión, máximo 10 A resistivos a 250 V CA.", system="YCSA/YCSA-H 50/60"),
])

add_topic("commissioning", "chiller-prestart", "Enfriadora: comprobaciones antes de arrancar", "El control no sustituye las comprobaciones hidráulicas y eléctricas.", [
    v("Agua y caudal", "YLCC/YCSA recién instalada o vaciada.", "YLCC", "27-35", "Evitar FL/antihielo.", "Confirme llenado, purga, bomba, filtro, válvulas y sentido/ajuste del detector de caudal.", system="YLCC/YCSA"),
    v("Red y protecciones", "Unidad trifásica antes de habilitar compresores.", "YCSA50", "6-11", "Evitar daños eléctricos.", "Compruebe tensión, fases, protecciones, aprietes y puesta a tierra antes de activar el control.", system="YCSA/YCSA-H"),
    v("Presiones y válvulas", "Circuitos listos para Test.", "YLCC", "27-35", "Evitar H/L falsos.", "Compruebe válvulas de servicio, carga, manómetros, ventiladores e intercambiadores.", system="YLCC/YLCC-H"),
])

add_topic("operational_effects", "incident-fault-stop", "Incidencia, avería y alarma seria", "El color o la tabla define el alcance; no basta el número.", [
    v("Incidencia verde AVO", "Piloto verde con secuencia.", "AVO03", "24-25", "Reconocer funcionamiento conservado.", "El manual indica que estas incidencias no detienen el equipo.", system="AVO/BLI/BCI/BVI"),
    v("Avería roja AVO", "Piloto rojo con código.", "AVO03", "24-25", "Reconocer parada protegida.", "Requiere corregir y rearmar; anote antes de borrar.", system="AVO/BLI/BCI/BVI"),
    v("Parada parcial/total YCSA", "Tabla OFF con columnas de circuito, ventilador, bomba y sistema.", "YCSA120", "46", "Saber qué puede seguir.", "Una alarma de bomba sin reserva o caudal para todo; un térmico de compresor puede dejar otros compresores disponibles.", system="YCSA/YCSA-H 120-180"),
])

add_topic("component_checks", "avo-sensors", "AVO: sondas y límites de plausibilidad", "La placa diferencia circuito abierto, corto y temperatura fuera de rango.", [
    v("Rango válido de sondas", "Incidencias 1-1 a 1-4 o 3-1 a 3-4.", "AVO03", "22-25", "Separar sensor y entrada.", "La familia revisada considera una banda general de -40 a 100 °C para varias sondas; la descarga tiene protección propia.", system="AVO/BLI/BCI/BVI", scope="outdoor"),
    v("Descarga a 130/150 °C", "Avería de descarga según generación.", "AVO03", "22-25", "Aplicar el umbral correcto.", "Una documentación cita parada a 130 °C y otra incidencia/sonda por encima de 150 °C; no mezcle generaciones.", system="AVO/AVO-BG", scope="outdoor"),
])

add_topic("component_checks", "chiller-inputs", "Chiller: entradas B e ID", "El identificador es un punto de placa, no siempre un código visible.", [
    v("Sondas B1-B5 en YLCC", "Display E1-E5 y bornero GND.", "YLCC", "35", "Comprobar cada canal.", "Aísle la sonda correspondiente y compare con su curva; no intercambie B1-B5.", system="YLCC/YLCC-H"),
    v("Entradas ID en YCSA", "Tabla de alarmas con ID1, ID2, ID4, ID5, etc.", "YCSA120", "46", "Relacionar protección y efecto.", "Use el identificador para localizar borne y función; no lo introduzca como si fuera un código de display.", system="YCSA/YCSA-H 120-180"),
])

add_topic("component_checks", "motors-pumps", "Ventiladores, compresores y bombas", "El alcance ayuda a decidir qué medir primero.", [
    v("Térmico de ventilador", "Código 4 AVO, C/F YLCC o ID9/ID14 YCSA.", "AVO03", "24-25", "Separar motor y protección.", "Compruebe giro, contactor, térmico, caudal de aire y alimentación.", system="Roca histórico"),
    v("Térmico de compresor", "C1/C2 YLCC o ID7/ID8/ID12/ID13 YCSA.", "YCSA120", "46", "Aislar el compresor afectado.", "Compruebe intensidad, tensión, equilibrio, contactor, presiones y estado térmico.", system="YLCC/YCSA"),
    v("Bombas redundantes", "YCSA con dos bombas.", "YCSA120", "46", "Verificar conmutación.", "La protección de una bomba debe arrancar la reserva; confirme señal, contactor, caudal y alarma.", system="YCSA/YCSA-H 120-180"),
])

add_topic("technical_values", "avo-thresholds", "AVO: umbrales y temporizadores", "Valores de control que explican la protección.", [
    v("Temperatura exterior mínima", "Calefacción con ambiente muy frío.", "AVO03", "22-25", "Interpretar 1-5/2-3.", "Por debajo de -20 °C la placa detiene el compresor en calefacción.", system="AVO/BLI/BCI/BVI"),
    v("Recuperación de descarga", "Compresor lleva cinco minutos.", "AVO03", "22-25", "Detectar falta de respuesta.", "Tras cinco minutos debe superar 50 °C en frío o 35 °C en calor según la lógica documentada.", system="AVO/BLI/BCI/BVI"),
    v("Repetición de baja", "Aspiración anormal repetida.", "AVO03", "22-25", "Distinguir evento y bloqueo.", "Tres detecciones dentro de 35 minutos elevan la condición a avería.", system="AVO/BLI/BCI/BVI"),
])

add_topic("technical_values", "dpc-values", "DPC-1: ajustes y tensiones", "Cada posición se presenta con su efecto.", [
    v("Alimentación y señales", "Termostato compatible con control de baja tensión.", "DPC1", "7-10", "Medir sin aplicar red.", "El sistema de mando trabaja con 24 V CA; no aplicar 230 V a entradas de control.", system="DPC-1", scope="controller"),
    v("Retardo de compresor", "SW1-4.", "DPC1", "7", "Elegir tiempo anti-ciclo.", "OFF selecciona 2 minutos y ON 4 minutos.", system="DPC-1", scope="controller"),
])

add_topic("technical_values", "ycsa-values", "YCSA: contactos y tiempos de protección", "Valores ligados a la familia exacta.", [
    v("Alarma general", "Salida de relé YCSA 50/60.", "YCSA50", "9-11", "Dimensionar el receptor.", "Contacto libre de tensión, máximo 10 A resistivos a 250 V CA.", system="YCSA/YCSA-H 50/60"),
    v("Ventana de repetición", "Térmico o presostato YCSA 120-180.", "YCSA120", "46", "Entender auto/manual.", "El primer evento puede recuperar; un segundo dentro de 60 minutos requiere rearme manual en las funciones indicadas.", system="YCSA/YCSA-H 120-180"),
])

add_topic("normal_states", "defrost-delays", "Desescarche y retardos que parecen avería", "Antes de intervenir, identifique la indicación exacta.", [
    v("d1/d2 YLCC", "Display muestra d minúscula.", "YLCC", "35", "Reconocer desescarche normal.", "d1/d2 indican proceso de desescarche; r1/r2 indican fallo de ese proceso.", system="YLCC/YLCC-H"),
    v("2-4 AVO", "Piloto de segunda generación marca 2-4.", "AVO04", "tabla de LED", "Reconocer desescarche activo.", "La indicación puede coexistir con cambios de ventilador y válvula.", system="AVO 74/174 BG"),
    v("Retardo 2/4 minutos DPC", "Hay demanda pero el compresor espera.", "DPC1", "7", "Evitar diagnóstico prematuro.", "SW1-4 programa el tiempo anti-ciclo; espere el intervalo antes de declarar fallo.", system="DPC-1 + máquina"),
])

add_topic("service_tools_boards", "test-and-inputs", "Placa: TEST, entradas y registro previo", "Procedimientos de baja tensión no autorizan trabajar sin seguridad.", [
    v("Antes de pulsar TEST", "Existe un código visible o una parada.", "AVO03", "24-25", "Conservar evidencia.", "Anote color, secuencia, demanda, temperaturas y presiones; TEST puede borrar el bloqueo.", system="AVO/BLI/BCI/BVI", scope="outdoor"),
    v("Entradas YCSA", "Tabla identifica B, ID, HP, LP y FS.", "YCSA120", "43-46", "Seguir la cadena real.", "Compruebe estado físico y eléctrico de la protección antes de puentear; no deje anulada una seguridad.", system="YCSA/YCSA-H", scope="outdoor"),
])

add_topic("system_architecture", "recognize-roca-family", "Reconocer qué sistema Roca histórico tiene delante", "La interfaz visible decide la tabla.", [
    v("AVO/BLI/BCI/BVI", "Unidad autónoma/rooftop con placa, TEST y pilotos verde/rojo.", "AVO03", "1, 22-25", "Usar secuencias AVO.", "Confirme si la secuencia es simple o de dos grupos y la generación del manual.", system="AVO/BLI/BCI/BVI"),
    v("DPC-1", "Termostato programable con LCD y llave de alarma.", "DPC1", "7-10", "Separar mando y máquina.", "0-90 llegan de la máquina; 91-99 son propios.", system="DPC-1"),
    v("YLCC", "Enfriadora compacta con display alfanumérico local.", "YLCC", "30-36", "Usar códigos E/H/L/C/F/A/d/r/n.", "El sufijo 1/2 es el circuito.", system="YLCC/YLCC-H"),
    v("YCSA", "Enfriadora aire-agua con control chiller µ y entradas B/ID.", "YCSA50", "6-11", "Usar tabla de entradas y alcance.", "Las referencias ID/B son puntos técnicos y no deben presentarse como códigos visibles.", system="YCSA/YCSA-H"),
])

add_topic("system_architecture", "search-strategy", "Cómo buscar códigos antiguos sin perder el contexto", "La lista muestra todas las interpretaciones cerradas.", [
    v("Busque el código completo", "Ejemplo: 1-1, H1, d1 o 93.", "AVO03", "22-25", "Evitar normalizaciones erróneas.", "Conserve guion, letra, mayúscula/minúscula y lugar de lectura.", system="Super Técnico"),
    v("Busque por interfaz", "No conoce el código exacto.", "DPC1", "7-10", "Llegar por rasgos observables.", "Pruebe 'piloto rojo AVO', 'llave DPC', 'display YLCC' o 'entrada ID YCSA'.", system="Super Técnico"),
])

add_topic("provenance", "manufacturer-policy", "Regla de inclusión: fabricación Roca acreditada", "El nombre comercial por sí solo no basta.", [
    v("Fabricante explícito", "El documento YCSA declara FABRICANTE: CLIMA ROCA YORK, S.L.", "YCSA50", "55", "Acreditar procedencia industrial.", "La familia YCSA 50/60 queda aceptada por declaración expresa de fabricante en el propio manual.", system="Control de procedencia"),
    v("Etapa industrial histórica", "Manual técnico Clima Roca York fechado antes de la venta de climatización.", "ROCA_HISTORY", "historia corporativa", "Aceptar familias históricas documentadas.", "AVO, DPC-1, YLCC y YCSA revisados pertenecen al corpus técnico de esa etapa y conservan referencia documental.", system="Control de procedencia"),
    v("Origen dudoso o posterior", "Catálogo posterior, marca usada bajo otra sociedad o fabricante no indicado.", "BOE", "BORME-C-2007-16073", "Excluir sin contaminar la base.", "No se incorpora hasta disponer de prueba independiente de fabricación por Roca/Clima Roca York.", system="Control de procedencia"),
])

add_topic("provenance", "excluded-families", "Familias excluidas por ahora", "La ausencia en la aplicación es deliberada, no un olvido.", [
    v("Equipos posteriores a la venta", "Documentación posterior a 2005 sin declaración de fabricante Roca.", "ROCA_HISTORY", "historia corporativa", "Evitar marcas blancas.", "El uso posterior de Roca/York en un catálogo no demuestra fabricación por Roca.", system="Control de procedencia"),
    v("Manual sin fabricante verificable", "Solo aparece un logotipo o un distribuidor.", "BOE", "BORME-C-2007-16073", "Mantener cuarentena documental.", "Se registra como candidato privado, pero no entra en la base pública hasta acreditar origen.", system="Control de procedencia"),
])


PROVENANCE = {
    "policy_version": "1.0",
    "brand_slug": "roca-clima",
    "rule": "Solo se publica una familia cuando la fabricación por Roca/Clima Roca York o su pertenencia inequívoca a esa etapa industrial está acreditada.",
    "accepted": [
        {
            "family": "YCSA/YCSA-H 50/60 T/TP",
            "status": "accepted_explicit_manufacturer",
            "evidence": "El propio manual identifica a CLIMA ROCA YORK, S.L. como fabricante.",
            "source_ref": "YCSA50",
            "page": "55",
        },
        {
            "family": "AVO/BLI/BCI/BVI, DPC-1, YLCC/YLCC-H y YCSA/YCSA-H 120-180",
            "status": "accepted_historic_industrial_corpus",
            "evidence": "Documentación técnica emitida por Clima Roca York y perteneciente a la etapa anterior a la venta de climatización de 2005.",
            "source_ref": "ROCA_HISTORY",
            "page": "historia corporativa",
        },
    ],
    "excluded": [
        {
            "scope": "equipos modernos o de marca comercial posterior",
            "reason": "El nombre Roca/York o su presencia en catálogo no acredita que fueran fabricados por Roca.",
            "reconsider_when": "Aparezca una declaración de fabricante, placa técnica o documento corporativo verificable.",
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
            "reference_brand": "Roca / Clima Roca York",
            "verification_warning": (
                "Referencia histórica restringida a familias con procedencia industrial acreditada. "
                "No aplique estos códigos a equipos modernos que solo compartan la marca comercial."
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
        "notes": (
            "Fuente revisada para Roca Referencia V1. La aceptación de la familia "
            "se rige además por web/provenance.json."
        ),
    } for ident, row in enumerate(core.SOURCES.values(), start=1)])
    write_json(WEB_DIR / "coverage.json", [{
        "id": ident,
        "brand_id": BRAND_ID,
        "area_slug": slug,
        "area_name": name,
        "equipment_scope": "Roca / Clima Roca York — corpus histórico acreditado",
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
        "slug": "roca-clima",
        "name": "Roca / Clima Roca York",
        "display_name": "Roca (histórica)",
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
            "Roca Referencia V1 histórica: AVO/BLI/BCI/BVI, DPC-1, YLCC y YCSA. "
            "Solo incluye familias de fabricación/procedencia industrial acreditada; "
            "equipos modernos o de origen dudoso quedan excluidos."
        ),
    })
    write_quality(WEB_DIR / "quality.json", audit_brand(BRAND_DIR))
    return counts


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
