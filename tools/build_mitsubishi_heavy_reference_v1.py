#!/usr/bin/env python3
"""Construye Mitsubishi Heavy Industries Referencia V1 para Super Técnico.

La marca se mantiene separada de Mitsubishi Electric. La proyección pública
contiene resúmenes técnicos trazables, pero no los PDF ni las capturas de los
manuales. Los códigos se separan por familia y por lugar de lectura: pilotos
RUN/TIMER, mando PAC, PCB exterior o display de siete segmentos KX/KXZ.
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
BRAND_DIR = ROOT / "data" / "brands" / "mitsubishi-heavy-industries"
WEB_DIR = BRAND_DIR / "web"
BRAND_ID = 13

core.BRAND_DIR = BRAND_DIR
core.WEB_DIR = WEB_DIR
core.BRAND_ID = BRAND_ID

core.SOURCES = {
    "RACZT": {
        "title": "Mitsubishi Heavy SRK/SRC ZT Series — Service Manual",
        "document_ref": "MHI-RAC-ZT-SERVICE-2025",
        "source_url": "https://bvtpartners.com/wp-content/uploads/2025/05/Mitsubishi_SRK20_50ZT-WF-WFB-WFT_SRC20_50ZT-W-WB_Service_Manual.pdf",
        "type": "service_manual", "year": "2025",
    },
    "RACOLD": {
        "title": "Mitsubishi Heavy SRK/SRC ZG Series — Service Manual",
        "document_ref": "MHI-RAC-ZG-SERVICE",
        "source_url": "https://www.mitsubishi-climate.ru/pdf_mh/service_manual_zg_en.pdf",
        "type": "service_manual", "year": "anterior a 2015",
    },
    "PAC": {
        "title": "Mitsubishi Heavy PAC Inverter — Service Manual",
        "document_ref": "PAC-SM-383",
        "source_url": "https://bvtpartners.com/wp-content/uploads/2025/11/Mitsubishi_PAC_service_manual.pdf",
        "type": "service_manual", "year": "2021",
    },
    "SCM": {
        "title": "Mitsubishi Heavy RAC Multi SCM — Technical Manual",
        "document_ref": "SCM-T-186",
        "source_url": "https://bvtpartners.com/wp-content/uploads/2025/05/SCM_RAC_MULTI_15-SCM-T-186.pdf",
        "type": "service_manual", "year": "2015",
    },
    "RCEX3": {
        "title": "eco touch RC-EX3 — Installation Manual",
        "document_ref": "PJZ012D114",
        "source_url": "https://www.mhi-mth.co.jp/en/products/pdf/pjz012d114_english.pdf",
        "type": "controller_manual", "year": "2016",
    },
    "RCEX3D": {
        "title": "Remote Control RC-EX3D — User Manual",
        "document_ref": "PJZ012A231",
        "source_url": "https://www.mhi-mth.co.jp/en/products/pdf/pjz012a231_english.pdf",
        "type": "controller_manual", "year": "2026",
    },
    "KXZ": {
        "title": "Mitsubishi Heavy KXZ Series — Service Manual",
        "document_ref": "KX-SM-318",
        "source_url": "https://www.manualslib.com/manual/1938494/Mitsubishi-Heavy-Industries-Kxz-Series.html",
        "type": "service_manual", "year": "2019",
    },
    "MANUALS": {
        "title": "MHI Thermal Systems — Air-conditioner User's Manuals",
        "document_ref": "MHI-OFFICIAL-MANUAL-PORTAL",
        "source_url": "https://www.mhi-mth.co.jp/en/products/detail/air-conditioner_users_manual.html",
        "type": "official_web", "year": "actualizado",
    },
    "ERRORWEB": {
        "title": "MHI Thermal Systems — Error Code Support",
        "document_ref": "MHI-OFFICIAL-ERROR-CODE-SUPPORT",
        "source_url": "https://www.mhi-mth.co.jp/support/errorcode/",
        "type": "official_web", "year": "actualizado",
    },
}

core.CATEGORIES = [
    (1, "errors", "Errores y protecciones", "Códigos residenciales, PAC, multisplit y KX/KXZ separados por punto de lectura."),
    (2, "outdoor_diagnostics", "Pilotos y display de la unidad exterior", "RUN/TIMER, LED rojo/verde/amarillo y siete segmentos."),
    (3, "diagnostic_access", "Obtención de códigos y subcódigos", "Service Mode, RC-EX3 y consulta desde PCB exterior."),
    (4, "history_reset", "Historial y borrado", "Memoria RAC, historial RC-EX3 y datos congelados KX."),
    (5, "service_modes", "Modos de servicio", "Test Run, frío/calor forzado y Pump Down."),
    (6, "configuration", "Configuración y programación", "DIP, funciones de mando, direcciones, demanda y bajo ruido."),
    (7, "controllers_buses", "Mandos y buses", "RC-EX3, mando cableado antiguo, cableado, arranque y comunicación."),
    (8, "drainage_overflow", "Drenaje y desbordamiento", "Boya, bomba, temporizaciones, E9 y prueba de drenaje."),
    (9, "commissioning", "Puesta en marcha", "Comprobaciones previas, Test Run y direccionamiento automático."),
    (10, "multisplit", "Multisplit y simultáneos", "SCM, ramas, errores compartidos y alcance operativo."),
    (11, "vrf_network", "VRF KX/KXZ y Superlink", "Direcciones, terminación, exteriores combinadas y funcionamiento del ciclo."),
    (12, "component_checks", "Comprobación de componentes", "Sondas, ventiladores, compresor, inverter, EEV y comunicaciones."),
    (13, "technical_values", "Valores técnicos", "Umbrales, tiempos, presiones y datos eléctricos documentados."),
    (14, "normal_states", "Comportamientos normales", "Retardos, desescarche, retorno de aceite, Silent y controles preventivos."),
    (15, "service_tools_boards", "Herramientas y placas", "Mente PC, datos congelados y sustitución de PCB."),
    (16, "system_architecture", "Reconocer el sistema", "Pistas visibles para elegir la tabla correcta sin exigir el modelo."),
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
    behavior: str | None = None,
    technical: str = "",
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
        behavior=behavior or "La protección detiene el funcionamiento afectado.",
        technical=technical,
        aliases=aliases,
    )


# RAC actual: la cifra se obtiene con RUN (decenas) y TIMER (unidades).
RAC_CURRENT = [
    ("0", "Funcionamiento normal", "normal", "system"),
    ("01", "Error de cableado o comunicación del mando cableado", "communication", "controller"),
    ("05", "Comunicación entre unidad interior y exterior", "communication", "system"),
    ("35", "Control de alta presión en refrigeración", "pressure", "system"),
    ("36", "Sobretemperatura del compresor a 110 °C", "compressor", "outdoor"),
    ("37", "Sonda del intercambiador exterior", "sensor", "outdoor"),
    ("38", "Sonda de aire exterior", "sensor", "outdoor"),
    ("39", "Sonda de descarga exterior", "sensor", "outdoor"),
    ("40", "Válvula de servicio de gas cerrada en calefacción", "pressure", "outdoor"),
    ("42", "Corte de corriente o sobrecorriente del compresor", "inverter", "outdoor"),
    ("47", "Tensión del filtro activo anormal", "power", "outdoor"),
    ("48", "Motor ventilador exterior anormal", "fan", "outdoor"),
    ("51", "Cortocircuito del transistor de potencia o circuito de corte", "inverter", "outdoor"),
    ("57", "Protección del circuito frigorífico", "pressure", "system"),
    ("58", "Current safe: limitación/protección de corriente", "power", "outdoor"),
    ("59", "Cableado del compresor abierto, caída de tensión o baja velocidad", "compressor", "outdoor"),
    ("60", "Bloqueo de rotor del compresor", "compressor", "outdoor"),
    ("61", "Interconexión interior–exterior incorrecta", "communication", "system"),
    ("62", "Error de transmisión serie durante el funcionamiento", "communication", "system"),
    ("80", "Motor ventilador interior anormal", "fan", "indoor"),
    ("82", "Sonda del intercambiador interior", "sensor", "indoor"),
    ("84", "Control anticondensación activo", "normal", "indoor"),
    ("85", "Control antihielo activo", "normal", "indoor"),
    ("86", "Control de alta presión en calefacción", "pressure", "system"),
]
for code, title, profile, scope in RAC_CURRENT:
    detail = {
        "01": "El manual cita hilo Y abierto, X/Y invertidos, ruido, mando o PCB interior.",
        "05": "Se declara tras 35 s sin recibir correctamente la comunicación; no confundir con 61/62.",
        "35": "La tabla asocia cinco destellos TIMER y registra hasta cinco recuperaciones antes de fijar la indicación.",
        "42": "En Service Mode: RUN cuatro destellos y TIMER dos; no se cuenta el pulso inicial de 1,5 s.",
        "48": "Se evalúa si el ventilador permanece a 75 min⁻¹ o menos durante 30 s.",
        "61": "Se evalúa a los 10 s desde la alimentación si no se detecta correctamente la trama.",
        "62": "Se evalúa tras 7 min 35 s sin comunicación correcta durante funcionamiento.",
        "84": "Es un control recuperable por humedad elevada, no una condena automática de componente.",
    }.get(code, "")
    aliases = [f"stop code {code}", f"código de parada {code}"]
    if code.isdigit():
        value = int(code)
        aliases.append(f"RUN {value // 10} TIMER {value % 10}")
    err(
        code,
        title,
        profile,
        "RACZT",
        "30-31",
        family="RAC SRK/SRC ZT — pilotos RUN/TIMER",
        scope=scope,
        behavior=(
            "Es un estado o control temporal; la unidad puede recuperar automáticamente."
            if profile == "normal"
            else "La unidad afectada se detiene; la tabla indica si existe recuperación automática."
        ),
        technical=detail,
        aliases=aliases,
    )


# RAC anterior: más granularidad de protecciones y corriente.
RAC_LEGACY = [
    ("11", "Corte de corriente durante arranque de software", "inverter"),
    ("12", "Corte de corriente por debajo de 20 rps", "inverter"),
    ("13", "Corte de corriente a 20 rps o más", "inverter"),
    ("14", "Sobretensión del bus DC, aproximadamente 350 V", "power"),
    ("15", "Cortocircuito del transistor de potencia, lado alto", "inverter"),
    ("16", "Fallo del circuito de corte de corriente", "inverter"),
    ("21", "Cálculo PWM anormal", "inverter"),
    ("22", "Entrada anormalmente baja con PWM alto", "power"),
    ("23", "Tres paradas anormales en veinte minutos", "compressor"),
    ("27", "Motor ventilador exterior", "fan"),
    ("29", "Caída de tensión", "power"),
    ("31", "Current safe I en refrigeración", "power"),
    ("32", "Current safe I en calefacción", "power"),
    ("33", "Current safe II en refrigeración", "power"),
    ("34", "Current safe II en calefacción", "power"),
    ("41", "Sobrecarga 1 en refrigeración", "pressure"),
    ("43", "Sobrecarga 3 en refrigeración", "pressure"),
    ("44", "Sobrecarga 1 en calefacción", "pressure"),
    ("45", "Sobrecarga 2 en calefacción", "pressure"),
    ("46", "Sobrecarga 3 en calefacción", "pressure"),
    ("50", "Protección por sobretemperatura de descarga", "compressor"),
    ("71", "Bloqueo de rotor por debajo de 16 rps", "compressor"),
    ("72", "Bloqueo de rotor a 16 rps o más", "compressor"),
    ("73", "Conmutación de fase U anormal", "compressor"),
    ("74", "Conmutación de fase V anormal", "compressor"),
    ("75", "Conmutación de fase W o fase no identificable", "compressor"),
    ("76", "Fallo de arranque de software del compresor", "compressor"),
    ("81", "Sonda de descarga: señal de cable abierto", "sensor"),
    ("83", "Sonda del intercambiador exterior en protección", "sensor"),
    ("87", "Protección de sobretemperatura del compresor", "compressor"),
    ("88", "Protección del circuito frigorífico", "pressure"),
]
for code, title, profile in RAC_LEGACY:
    err(
        code,
        title,
        profile,
        "RACOLD",
        "37-38",
        family="RAC SRK/SRC generación anterior — Service Mode",
        scope="outdoor",
        behavior="Es un dato de parada; las paradas transitorias pueden recuperar automáticamente.",
        technical="El manual conserva hasta diez datos de parada y avisa que tres repeticiones o más requieren investigación.",
        aliases=[f"RUN {int(code) // 10} TIMER {int(code) % 10}", f"stop data {code}"],
    )


# PAC: códigos del mando y equivalencias de pilotos interiores/exteriores.
PAC_ERRORS = [
    ("E1", "Comunicación entre mando cableado y unidad interior", "communication", "controller"),
    ("E5", "Comunicación entre unidad interior y exterior", "communication", "system"),
    ("E6", "Sonda del intercambiador interior", "sensor", "indoor"),
    ("E7", "Sonda de retorno de aire interior", "sensor", "indoor"),
    ("E8", "Sobrecarga en calefacción o sonda interior en cortocircuito", "pressure", "indoor"),
    ("E9", "Desagüe anormal: boya, bomba o circuito de entrada", "drain", "indoor"),
    ("E10", "Demasiadas unidades interiores en un mismo mando", "configuration", "controller"),
    ("E11", "Error de direccionamiento interior", "configuration", "indoor"),
    ("E14", "Sin principal asignada o comunicación principal–secundaria", "configuration", "indoor"),
    ("E16", "Motor ventilador interior", "fan", "indoor"),
    ("E18", "Direccionamiento principal–secundaria incorrecto", "configuration", "indoor"),
    ("E19", "Modo de comprobación de operación o bomba configurado incorrectamente", "configuration", "indoor"),
    ("E20", "Velocidad anormal del motor ventilador interior", "fan", "indoor"),
    ("E28", "Sonda de temperatura del mando cableado", "sensor", "controller"),
    ("E35", "Sobrecarga en refrigeración o temperatura alta del intercambiador exterior", "pressure", "outdoor"),
    ("E36", "Temperatura de descarga elevada", "compressor", "outdoor"),
    ("E37", "Sonda del intercambiador exterior", "sensor", "outdoor"),
    ("E38", "Sonda de aire exterior", "sensor", "outdoor"),
    ("E39", "Sonda de descarga exterior", "sensor", "outdoor"),
    ("E40", "Alta presión, 63H1 o válvula de servicio cerrada", "pressure", "outdoor"),
    ("E41", "Sobretemperatura del transistor de potencia", "inverter", "outdoor"),
    ("E42", "Corte de corriente o sobrecorriente del compresor", "inverter", "outdoor"),
    ("E44", "Retorno de líquido o sobrecalentamiento insuficiente bajo cárter", "pressure", "outdoor"),
    ("E45", "Comunicación entre PCB inverter y PCB de control exterior", "communication", "outdoor"),
    ("E48", "Motor ventilador exterior", "fan", "outdoor"),
    ("E49", "Baja presión o sonda de baja presión", "pressure", "outdoor"),
    ("E51", "Inverter o transistor de potencia", "inverter", "outdoor"),
    ("E53", "Sonda de aspiración", "sensor", "outdoor"),
    ("E54", "Sonda de baja presión", "sensor", "outdoor"),
    ("E55", "Sonda de temperatura bajo cárter del compresor", "sensor", "outdoor"),
    ("E57", "Falta de refrigerante o válvula de servicio cerrada", "pressure", "system"),
    ("E59", "Fallo de arranque del compresor", "compressor", "outdoor"),
    ("E75", "Comunicación con control opcional", "communication", "controller"),
]
for code, title, profile, scope in PAC_ERRORS:
    technical = {
        "E1": "Compruebe el hilo de señal blanco, ruido, continuidad, mando y circuito de comunicación interior.",
        "E8": "En la familia PAC revisada también se activa con Thi-R a 63 °C; cinco detecciones en 60 min o seis minutos continuos fijan E8.",
        "E9": "Boya abierta 3 s activa la detección; cerrada 10 s la libera. La bomba sigue 5 min en varias transiciones.",
        "E16": "La tabla separa motor, placa de potencia interior y placa de control.",
        "E19": "Puede aparecer si SW7-1 está en posición de comprobación al alimentar o si la selección de prueba no corresponde.",
        "E36": "No asumir carga: también aparecen sonda de descarga o entrada analógica de PCB.",
        "E41": "La placa inverter muestra además LED amarillo ocho destellos en la familia documentada.",
        "E42": "La placa inverter muestra además LED amarillo nueve destellos en la familia documentada.",
        "E48": "Si se detectan 100 min⁻¹ o menos durante 30 s y se repite cinco veces en 60 min, queda E48.",
        "E59": "Cinco fallos de arranque producen E59; vuelve a permitirse un intento tres minutos después de parar.",
    }.get(code, "")
    err(
        code,
        title,
        profile,
        "PAC",
        "42-43, 63-64",
        family="PAC FDT/FDTC/FDU/FDUM/FDE y SRK comercial",
        scope=scope,
        behavior=(
            "La interior se detiene y la bomba permanece activa mientras persiste el nivel."
            if code == "E9"
            else "La protección detiene la unidad o el ciclo afectado; algunas condiciones reintentan antes del bloqueo."
        ),
        technical=technical,
        aliases=[code.replace("E", "E "), f"mando {code}"],
    )


# KXZ: subcódigo exterior en siete segmentos. El mando puede mostrar solo la cabecera.
KXZ_ERRORS = [
    ("E3", "No se establece comunicación interior–exterior", "communication"),
    ("E5", "Comunicación perdida durante el funcionamiento", "communication"),
    ("E6", "Sonda del intercambiador interior Thi-R", "sensor"),
    ("E7", "Sonda de retorno interior Thi-A", "sensor"),
    ("E9", "Desagüe interior anormal", "drain"),
    ("E10", "Más de 17 interiores bajo un mando", "configuration"),
    ("E11", "Métodos de direccionamiento mezclados", "configuration"),
    ("E14", "Comunicación principal–secundaria interior", "communication"),
    ("E16", "Motor ventilador interior", "fan"),
    ("E19", "Comprobación de operación/bomba de drenaje", "configuration"),
    ("E28", "Sonda del mando Thc", "sensor"),
    ("E30", "Conexión interior–exterior no coincidente", "configuration"),
    ("E31", "Dirección exterior duplicada", "configuration"),
    ("E32", "Fase L3 abierta en la alimentación exterior", "power"),
    ("E36-1", "Temperatura de descarga anormal Tho-D1", "compressor"),
    ("E36-3", "Temperatura de descarga anormal en circuito/compresor adicional", "compressor"),
    ("E37-1", "Sonda de intercambiador exterior Tho-R1", "sensor"),
    ("E37-5", "Sonda de subenfriamiento Tho-SC", "sensor"),
    ("E37-6", "Sonda exterior Tho-H", "sensor"),
    ("E38", "Sonda de aire exterior Tho-A", "sensor"),
    ("E39-1", "Sonda de descarga Tho-D1", "sensor"),
    ("E40", "Alta presión, presostato 63H1-1", "pressure"),
    ("E41-1", "Sobretemperatura del transistor de potencia del inverter 1", "inverter"),
    ("E42", "Corte de corriente del inverter", "inverter"),
    ("E43-1", "Exceso de unidades interiores conectadas", "configuration"),
    ("E43-2", "Exceso de capacidad interior conectada", "configuration"),
    ("E45", "Comunicación inverter–PCB exterior", "communication"),
    ("E46", "Métodos de direccionamiento mezclados en la red", "configuration"),
    ("E48", "Motor ventilador DC exterior", "fan"),
    ("E49", "Baja presión", "pressure"),
    ("E51-1", "Anomalía del inverter o transistor de potencia 1", "inverter"),
    ("E53", "Sonda de aspiración Tho-S", "sensor"),
    ("E54-1", "Sonda de baja presión PSL", "sensor"),
    ("E54-2", "Sonda de alta presión PSH", "sensor"),
    ("E56-1", "Sonda de temperatura del transistor Tho-P1", "sensor"),
    ("E58-1", "Pérdida de sincronismo del compresor", "compressor"),
    ("E59", "Fallo de arranque del compresor", "compressor"),
    ("E63", "Parada de emergencia", "configuration"),
]
for code, title, profile in KXZ_ERRORS:
    err(
        code,
        title,
        profile,
        "KXZ",
        "62, 81-116",
        family="KXZ VRF — display exterior de siete segmentos",
        scope="outdoor",
        behavior=(
            "Se detiene la unidad interior afectada; otras unidades pueden continuar."
            if code in {"E6", "E7", "E9", "E10", "E14", "E16", "E19", "E28"}
            else "Se detiene la exterior o el ciclo frigorífico afectado."
        ),
        technical=(
            "El subcódigo tras el guion identifica sensor, compresor o variante; no debe ocultarse al técnico."
            if "-" in code
            else "Conecte Mente PC y guarde los datos antes de borrar o sustituir una placa."
        ),
        aliases=[code.replace("-", " "), code.replace("-", ""), f"siete segmentos {code}"],
    )

for code, title, technical in [
    ("WAIT", "Espera de comunicación o adquisición al alimentar", "Si permanece más de dos minutos, revise alimentación, fusibles, bus y direccionamiento."),
    ("INSPECT I/U", "El mando solicita inspeccionar la unidad interior", "Puede acompañar un fallo de interconexión o una configuración principal–secundaria incorrecta."),
]:
    err(
        code,
        title,
        "communication",
        "PAC",
        "42-43, 74-80",
        family="PAC/KX — mensajes de mando",
        scope="controller",
        behavior="Es un mensaje de diagnóstico; el alcance depende del código asociado.",
        technical=technical,
    )


def rac_pattern(code: str, meaning: str) -> dict[str, Any]:
    value = int(code)
    tens, ones = value // 10, value % 10
    return {
        "code_display": code,
        "indication_type": "indoor_led_pair",
        "display_location": "pilotos RUN y TIMER de la unidad interior",
        "family_hint": "MHI RAC SRK/SRC con Service Mode",
        "relationship": meaning,
        "led_indicators": [
            {
                "label": "RUN",
                "color": "green",
                "state": "pulse" if tens else "off",
                "detail": f"{tens} destellos" if tens else "sin destellos",
            },
            {
                "label": "TIMER",
                "color": "yellow",
                "state": "pulse" if ones else "off",
                "detail": f"{ones} destellos" if ones else "sin destellos",
            },
        ],
        "counting_rule": "No cuente la señal inicial de 1,5 s. RUN forma las decenas y TIMER las unidades; cada destello dura aproximadamente 0,5 s.",
        "cycle_note": "No se cuenta el pulso inicial de 1,5 s; el ciclo se repite cada 11 s.",
        "sequence": f"{tens} × 10 + {ones} = {code}.",
    }


RAC_LED_PATTERNS = [
    rac_pattern(code, title)
    for code, title, _profile, _scope in RAC_CURRENT
    if code.isdigit() and int(code) > 0
]


def pac_pattern(code: str, meaning: str, red: str, green: str = "parpadeo continuo", yellow: str = "apagado") -> dict[str, Any]:
    def indicator(label: str, color: str, value: str) -> dict[str, str]:
        normalized = value.lower()
        if "destello" in normalized:
            state = "pulse"
        elif "parpadeo" in normalized:
            state = "blink"
        elif "encendido" in normalized:
            state = "on"
        else:
            state = "off"
        return {"label": label, "color": color, "state": state, "detail": value}

    return {
        "code_display": code,
        "indication_type": "outdoor_led",
        "display_location": "PCB de control/inverter de la unidad exterior PAC",
        "family_hint": "MHI PAC FDC VSA-W; confirmar placa antes de aplicar",
        "relationship": meaning,
        "led_indicators": [
            indicator("LED rojo control", "red", red),
            indicator("LED verde control", "green", green),
            indicator("LED amarillo inverter", "yellow", yellow),
        ],
        "counting_rule": "El piloto rojo de control y el amarillo del inverter aportan capas distintas.",
        "cycle_note": "Compruebe el código del mando y varios ciclos del piloto.",
        "sequence": "No trasladar esta tabla a un split RAC ni a KXZ.",
    }


PAC_LED_PATTERNS = [
    pac_pattern("E35", "Sobrecarga en refrigeración", "1 destello"),
    pac_pattern("E36", "Temperatura de descarga elevada", "1 destello"),
    pac_pattern("E37", "Sonda del intercambiador exterior", "1 destello"),
    pac_pattern("E38", "Sonda de aire exterior", "1 destello"),
    pac_pattern("E39", "Sonda de descarga", "1 destello"),
    pac_pattern("E40", "Alta presión o 63H1", "1 destello"),
    pac_pattern("E41", "Sobretemperatura del transistor", "1 destello", yellow="8 destellos"),
    pac_pattern("E42", "Corte de corriente", "1 destello", yellow="9 destellos"),
    pac_pattern("E44", "Retorno de líquido", "1 destello"),
    pac_pattern("E45", "Comunicación control–inverter", "1 destello"),
    pac_pattern("E48", "Motor ventilador exterior", "1 destello", yellow="encendido continuo"),
    pac_pattern("E49", "Baja presión", "1 destello"),
    pac_pattern("E51", "Inverter/transistor", "1 destello", yellow="8 destellos"),
    pac_pattern("E53", "Sonda de aspiración", "1 destello"),
    pac_pattern("E54", "Sonda de baja presión", "1 destello"),
    pac_pattern("E55", "Sonda bajo cárter", "1 destello"),
    pac_pattern("E57", "Falta de refrigerante/válvula cerrada", "1 destello"),
    pac_pattern("E59", "Fallo de arranque del compresor", "5 destellos", yellow="4 destellos"),
]


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
    system: str = "Mitsubishi Heavy Industries",
    scope: str = "system",
    steps: list[dict[str, Any]] | None = None,
    parameters: list[dict[str, Any]] | None = None,
    controller_data: dict[str, Any] | None = None,
    monitoring: list[dict[str, Any]] | None = None,
    led_patterns: list[dict[str, Any]] | None = None,
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
        parameters=parameters,
        controller_data=controller_data,
        monitoring=monitoring,
        led_patterns=led_patterns,
    )


def add_topic(category: str, slug: str, title: str, summary: str, variants: list[dict[str, Any]]) -> None:
    core.add_topic(category, slug, title, summary, variants)


add_topic("errors", "same-code-different-families", "El mismo código cambia entre RAC, PAC y KXZ", "La ficha muestra todas las posibilidades cerradas para que el técnico elija.", [
    v("35/36/37/38/39 en pilotos RAC", "Interior mural con pilotos RUN y TIMER, sin código E en pantalla.", "RACZT", "30-31", "Aplicar la tabla numérica.", "35 es alta presión en frío; 36 sobretemperatura del compresor; 37/38/39 son sondas exteriores.", system="RAC SRK/SRC"),
    v("E35–E39 en mando PAC", "Mando cableado o display comercial muestra prefijo E.", "PAC", "42-43", "Aplicar la tabla PAC.", "El prefijo E y los pilotos de PCB distinguen sobrecarga y sondas; no son los stop codes numéricos del RAC.", system="PAC"),
    v("E36-1, E37-5 y E54-2 en KXZ", "Exterior VRF con tres dígitos y subcódigo tras guion.", "KXZ", "97-113", "Conservar el subcódigo.", "El mando puede enseñar la cabecera; el display exterior identifica sensor, circuito o compresor.", system="KXZ VRF"),
])
add_topic("outdoor_diagnostics", "rac-run-timer-table", "RAC: tabla completa RUN/TIMER", "RUN son las decenas; TIMER son las unidades.", [
    v("Tabla de códigos actuales", "Split SRK/SRC con dos pilotos en la unidad interior.", "RACZT", "30-31", "Traducir el patrón sin desmontar la exterior.", "El pulso inicial de 1,5 s es una señal de comienzo y no cuenta. Después se cuentan destellos de 0,5 s; el ciclo dura 11 s.", system="RAC SRK/SRC", scope="indoor", led_patterns=RAC_LED_PATTERNS),
    v("Ejemplo 42", "RUN parpadea cuatro veces y TIMER dos.", "RACZT", "31", "Comprobar la regla.", "4 × 10 + 2 = 42: corte de corriente. Cuente al menos dos ciclos completos.", system="RAC SRK/SRC", scope="indoor"),
    v("Datos de parada de generaciones anteriores", "Service Mode ofrece códigos 11–88 más granulares.", "RACOLD", "37-38", "Distinguir protección transitoria y error fijo.", "Los códigos 31–46 separan current safe y sobrecarga por modo; 71–76 detallan bloqueo/fases del compresor.", system="RAC anterior", scope="indoor"),
])
add_topic("outdoor_diagnostics", "pac-led-table", "PAC: tabla de pilotos de placa exterior", "El código del mando y los LED aportan información complementaria.", [
    v("LED rojo/verde de control y amarillo inverter", "FDC comercial con PCB de control y placa inverter.", "PAC", "43-43-1", "Cruzar mando y placa.", "E41/E42/E51 añaden 8/9 destellos amarillos; E48 puede mostrar amarillo fijo; E59 combina cinco rojos y cuatro amarillos.", system="PAC FDC", scope="outdoor", led_patterns=PAC_LED_PATTERNS),
    v("No indication / WAIT / INSPECT I/U", "El mando no presenta todavía un código E estable.", "PAC", "42-43, 74-80", "Diagnosticar alimentación o comunicación.", "La ausencia de display, WAIT persistente e INSPECT I/U tienen tablas propias de alimentación, fusibles, comunicación y principal/secundaria.", system="PAC", scope="controller"),
])
add_topic("outdoor_diagnostics", "kxz-seven-segment", "KXZ: display exterior de siete segmentos", "La cabecera E del mando puede tener un subcódigo más preciso en exterior.", [
    v("E37-1 / E37-5 / E37-6", "Display exterior muestra E37 seguido de guion y cifra.", "KXZ", "99", "Identificar la sonda exacta.", "1 corresponde a Tho-R1; 5 a Tho-SC; 6 a Tho-H. No sustituya una sonda por el E37 genérico.", system="KXZ", scope="outdoor"),
    v("E54-1 / E54-2", "Mando muestra E54 o la placa muestra subcódigo.", "KXZ", "112", "Separar baja y alta presión.", "E54-1 es PSL; E54-2 es PSH. Compare tensión del sensor con manómetros.", system="KXZ", scope="outdoor"),
    v("Códigos C00–Cxx", "Display exterior en modo monitor, sin E delante.", "KXZ", "42-47", "Leer variables y actuadores.", "La serie C muestra sensores, frecuencia, demanda, ventiladores, EEV, contadores y estado; no es una lista de averías.", system="KXZ", scope="outdoor"),
])
add_topic("diagnostic_access", "rac-service-mode-entry", "RAC: entrar en Service Mode y obtener códigos", "Procedimiento para equipos con mando inalámbrico y botón ON/OFF en la interior.", [
    v("Entrada completa", "Split parado; botón físico ON/OFF accesible en la interior.", "RACOLD", "35-36", "Mostrar memoria sin herramienta.", "La entrada debe iniciarse tras cortar alimentación al menos un minuto. En Service Mode el mando cableado opcional no responde: use el inalámbrico.", system="RAC SRK/SRC", scope="indoor", steps=[
        step(1, "Corte la alimentación y espere un minuto o más.", phase="prepare"),
        step(2, "Mantenga pulsado el botón ON/OFF de la unidad interior mientras restablece la alimentación."),
        step(3, "Ajuste en el mando inalámbrico: refrigeración, ventilador MED y 21 °C."),
        step(4, "Envíe la orden y escuche el aviso acústico de confirmación."),
        step(5, "No cuente el encendido inicial de 1,5 s; cuente RUN y TIMER después.", phase="verify"),
        step(6, "Para salir, corte alimentación y espere al menos un minuto antes de volver a conectar.", phase="finish"),
    ]),
    v("Si no hay aviso acústico", "La secuencia no entra tras varios intentos.", "RACOLD", "35", "No interpretar luces normales como código.", "Repita desde el corte de alimentación; si nunca confirma, el pulsador ON/OFF o la variante de control pueden no corresponder.", system="RAC SRK/SRC", scope="indoor"),
])
add_topic("diagnostic_access", "rcex3-error-access", "RC-EX3/RC-EX3D: obtener error y datos de la unidad", "El mando muestra código, dirección interior y exterior.", [
    v("Error activo desde el mensaje de protección", "Pantalla táctil con mensaje Unit protection stop.", "RCEX3D", "Error display", "Leer sin borrar.", "Abra Menu y toque el contenido del error. Anote Code, IU y OU antes de reiniciar.", system="RC-EX3D", scope="controller"),
    v("Menú de servicio → Error display", "RC-EX3 con contraseña de servicio.", "RCEX3", "29-30", "Abrir historial y datos congelados.", "Error display contiene Error history, Display anomaly data, Erase anomaly data y Reset periodical check.", system="RC-EX3", scope="controller"),
    v("Seleccionar unidad en un grupo", "Varias interiores comparten mando.", "RCEX3", "24-30", "Relacionar código y dirección.", "La pantalla identifica IU y OU; no trate un error de otra interior como propio de la unidad que está mirando.", system="RC-EX3", scope="controller"),
])
add_topic("history_reset", "rac-memory", "RAC: cinco errores y diez paradas", "La memoria no se borra al cortar la alimentación.", [
    v("Cinco self-diagnosis data", "Service Mode activo y mando ajustable.", "RACOLD", "35-37", "Reconstruir fallos anómalos.", "Se guardan cinco errores con temperaturas de ambiente, batería interior/exterior, descarga y datos de modo/ventilador.", system="RAC SRK/SRC", scope="indoor"),
    v("Diez stop data", "La máquina recuperó y no queda alarma visible.", "RACOLD", "35-38", "Encontrar protecciones transitorias.", "Se guardan diez causas de parada. Una protección aislada puede ser normal; tres o más repeticiones merecen investigación.", system="RAC SRK/SRC", scope="indoor"),
])
add_topic("history_reset", "rcex3-history-anomaly", "RC-EX3: historial y datos justo antes del error", "No borre antes de capturar la evidencia.", [
    v("Error history", "Menú Error display del RC-EX3.", "RCEX3", "30", "Ver orden y dirección.", "Muestra fecha/hora, dirección IU y código. Delete elimina el historial completo mostrado.", system="RC-EX3", scope="controller"),
    v("Display anomaly data", "Existe un último error con datos congelados.", "RCEX3", "30-31", "Ver qué hacía la máquina.", "Conserva modo, consigna, temperaturas, velocidad interior, frecuencia requerida/real, EEV, presiones, descarga, corriente y protecciones.", system="RC-EX3", scope="controller"),
    v("Antes de Delete/Erase", "El técnico quiere rearmar.", "RCEX3", "30-31", "Conservar evidencia.", "Fotografíe historial, código, IU/OU y todas las páginas de anomaly data; después borre solo si el procedimiento lo requiere.", system="RC-EX3", scope="controller"),
])
add_topic("history_reset", "kxz-data-retention", "KXZ: datos de operación guardados continuamente", "La avería congela los datos anteriores al evento.", [
    v("Memoria de operación", "Sistema KXZ con Mente PC o conector RS-232C.", "KXZ", "50-58", "Analizar una parada intermitente.", "La escritura es continua; cuando ocurre un problema se detiene y conserva los datos inmediatamente anteriores.", system="KXZ", scope="outdoor"),
    v("Error counters y estados", "Display C70+ o archivo de Mente PC.", "KXZ", "47, 54-57", "Distinguir evento aislado y repetido.", "Incluye contadores de sonda, alta/baja presión, estados de protección, retorno de aceite, desescarche y registro de interiores.", system="KXZ", scope="outdoor"),
])
add_topic("service_modes", "pac-test-run", "PAC: Test Run desde la placa exterior", "Frío/calor se seleccionan con SW3-3 y SW3-4.", [
    v("Refrigeración de prueba", "PCB exterior con DIP SW3-3/SW3-4.", "PAC", "40", "Forzar frío sin consigna normal.", "SW3-3 ON y SW3-4 OFF inicia frío. El mando muestra consigna de 5 °C.", system="PAC", scope="outdoor"),
    v("Calefacción de prueba", "Misma placa y máquina preparada.", "PAC", "40", "Forzar calor.", "SW3-3 ON y SW3-4 ON inicia calor. El mando muestra preparación/consigna de 30 °C.", system="PAC", scope="outdoor"),
    v("Protecciones activas", "Test Run en curso.", "PAC", "40", "Interpretar una parada.", "La frecuencia objetivo se fija por modelo, pero todas las protecciones y detecciones de error siguen activas. Devuelva SW3-3 a OFF al terminar.", system="PAC", scope="outdoor"),
])
add_topic("service_modes", "pac-pump-down", "PAC: Pump Down documentado con SW1", "La secuencia explica por qué aparece E5 durante la recogida.", [
    v("Iniciar recogida", "Unidad parada o en parada anómala; SW4-1 OFF y placa con SW1.", "PAC", "40", "Recoger refrigerante en la exterior.", "Cierre líquido, deje gas abierto y mantenga SW1 de Pump Down durante dos segundos. El compresor trabaja en frío a 55 rps, EEV abierta y ventilador normal.", system="PAC", scope="outdoor", steps=[
        step(1, "Confirme que la interior no está funcionando y cierre la válvula de líquido.", phase="prepare", warning="warning"),
        step(2, "Mantenga SW1 Pump Down durante dos segundos."),
        step(3, "Observe LED rojo y verde parpadeando y vigile la baja presión."),
        step(4, "Al parar el compresor, cierre la válvula de gas.", phase="finish", warning="warning"),
    ]),
    v("Qué protecciones siguen activas", "Pump Down en curso.", "PAC", "40", "Entender el control.", "Siguen activas todas salvo baja presión, antihielo y anticondensación. La EEV queda totalmente abierta.", system="PAC", scope="outdoor"),
    v("Condiciones de fin", "La presión baja o transcurren cinco minutos.", "PAC", "40", "Finalizar con seguridad.", "Finaliza a 0,087 MPa o menos durante 5 s, por otra protección o al acumular 5 min. Un error de protección puede exigir reset de alimentación.", system="PAC", scope="outdoor"),
    v("E5 durante Pump Down", "La interior y el mando muestran Transmission error E5.", "PAC", "40", "No diagnosticar una avería inexistente.", "SW1 cancela la comunicación con la interior; E5 durante esta secuencia está documentado como normal.", system="PAC", scope="system"),
])
add_topic("service_modes", "scm-manual-pump-down", "SCM/multisplit: recogida por frío forzado", "Variante sin botón específico de Pump Down.", [
    v("Procedimiento con manómetro", "Exterior SCM y acceso a válvulas de líquido/gas.", "SCM", "109-110", "Recoger refrigerante.", "Conecte el manómetro, cierre líquido, deje gas abierto y haga frío. Al llegar aproximadamente a 0,01 MPa, pare y cierre gas.", system="SCM/RAC Multi", scope="outdoor"),
    v("Frío forzado con ambiente interior bajo", "La demanda normal no permite frío.", "SCM", "109", "Mantener el compresor durante la recogida.", "Use el procedimiento de refrigeración forzada de esa unidad interior; no invente una combinación universal.", system="SCM/RAC Multi", scope="system"),
])
add_topic("configuration", "pac-switches-functions", "PAC: DIP y funciones de placa/mando", "Registrar la posición original evita errores E18/E19.", [
    v("SW3-3 / SW3-4", "PCB exterior con tabla Test Run.", "PAC", "40", "Seleccionar prueba.", "SW3-3 activa/desactiva; SW3-4 elige frío/calor. SW3-3 debe quedar OFF al finalizar.", system="PAC", scope="outdoor"),
    v("SW7-1 interior", "PCB interior con prueba de operación/bomba.", "PAC", "17-18", "Elegir prueba al alimentar.", "La posición se lee al aplicar tensión; cambiarla después es ineficaz. Con mando comunicado entra Operation Check; sin comunicación, Drain Pump Test.", system="PAC", scope="indoor"),
    v("Funciones de drenaje desde RC-EX3", "Mando de servicio y unidad con bomba.", "PAC", "17", "Elegir en qué modos trabaja la bomba.", "Se documentan: solo frío; frío+calor; frío+calor+fan; frío+fan. El valor depende de la unidad.", system="PAC", scope="controller"),
])
add_topic("configuration", "kxz-p-settings", "KXZ: programación P y entradas exteriores", "La pantalla de siete segmentos muestra y modifica funciones.", [
    v("P31 — direccionamiento automático", "Red Superlink preparada y todas las unidades alimentadas.", "KXZ", "49", "Iniciar adquisición de interiores.", "P31 pasa de espera a inicio de automatic address setting. Confirme el número registrado antes del Test Run.", system="KXZ", scope="outdoor"),
    v("P07/P08/P09/P10 — entradas", "PCB con CnS1, CnS2, CnG1 o CnG2.", "KXZ", "31-40", "Asignar demanda, permiso o modo forzado.", "La función elegida determina si la entrada actúa por nivel o impulso; documente el ajuste antes de puentear.", system="KXZ", scope="outdoor"),
    v("P02 — protección nieve", "Exterior en zona fría con ventilador parado.", "KXZ", "34", "Activar la lógica documentada.", "Con P02 válido y temperatura exterior inferior a 3 °C durante diez minutos, el control puede hacer girar ventiladores para evitar nieve.", system="KXZ", scope="outdoor"),
])
add_topic("controllers_buses", "rcex3-cabling-startup", "RC-EX3: cableado, bus y arranque", "El mando usa dos hilos no polarizados.", [
    v("Dos conductores no polarizados", "Mando táctil eco touch RC-EX3.", "RCEX3", "6-7", "Cablear sin invertir un bus polarizado inexistente.", "El cable de mando es no polarizado. Sepárelo de potencia y no aplique tensión externa.", system="RC-EX3", scope="controller", controller_data=core.controller("mando cableado táctil", "bus de mando MHI", "2 hilos", "no polarizado", "alimentado por la unidad interior", "X/Y según unidad")),
    v("USB de servicio/configuración", "Lateral del RC-EX3 con puerto USB.", "RCEX3", "7", "Reconocer la interfaz.", "El puerto forma parte del mando; no debe confundirse con el bus de dos hilos ni usarse como alimentación de la instalación.", system="RC-EX3", scope="controller"),
    v("Main/Sub R/C", "Dos mandos o control de grupo.", "RCEX3", "12-24", "Evitar conflicto de rol.", "El menú de instalación permite Main/Sub R/C; una configuración incorrecta puede dar WAIT, E1 o impedir el control del grupo.", system="RC-EX3", scope="controller"),
])
add_topic("controllers_buses", "controller-communication", "Fallo de comunicación del propio mando", "Separar mando, hilo y placa interior antes de sustituir.", [
    v("RAC 01", "Pilotos forman 01 y hay mando cableado opcional.", "RACZT", "30", "Diagnosticar el enlace del mando.", "Compruebe hilo Y abierto, X/Y invertidos, ruido, continuidad, alimentación interior y circuito de mando.", system="RAC", scope="controller"),
    v("PAC E1", "RC-EX3 o mando cableado muestra E1.", "PAC", "42, 74", "Separar ruido, cable y electrónica.", "La tabla destaca el hilo de señal blanco, conexiones, ruido, mando y PCB interior.", system="PAC", scope="controller"),
    v("WAIT persistente al alimentar", "Mando permanece WAIT más de dos minutos.", "KXZ", "74-80", "Comprobar adquisición inicial.", "Revise alimentación interior/exterior, fusibles, terminación Superlink, direcciones y número de unidades antes de cambiar el mando.", system="PAC/KXZ", scope="controller"),
])
add_topic("drainage_overflow", "pac-drain-sequence", "PAC/cassette: proceso completo de boya y bomba", "E9 no significa siempre bomba averiada.", [
    v("Funcionamiento normal de la bomba", "Cassette/conductos con bomba integrada.", "PAC", "17", "Interpretar post-marcha.", "Trabaja en frío, auto-frío y deshumidificación con frecuencia distinta de cero; después continúa cinco minutos, incluso tras parada anómala.", system="PAC cassette/conductos", scope="indoor"),
    v("Boya abierta tres segundos", "Nivel alto real, boya atascada o cable abierto.", "PAC", "17", "Confirmar detección.", "Tres segundos de float OPEN activan la detección. La bomba se fuerza; en Control A la unidad para con E9 y mantiene la bomba.", system="PAC cassette/conductos", scope="indoor"),
    v("Boya cerrada diez segundos", "El agua ha bajado y el contacto recupera.", "PAC", "17", "Confirmar salida del estado.", "Diez segundos de float CLOSE liberan la detección. En Control B se prueba la bomba cinco minutos y se vuelve a comprobar diez segundos después de pararla.", system="PAC cassette/conductos", scope="indoor"),
    v("Calefacción, ventilación y parada", "No hay frío activo, pero sube el nivel.", "PAC", "17", "No descartar la boya por el modo.", "La detección funciona también en calor, fan, stop y termostato de frío OFF; la configuración del mando define en qué modos funciona preventivamente la bomba.", system="PAC cassette/conductos", scope="indoor"),
])
add_topic("drainage_overflow", "drain-pump-test", "Prueba de bomba sin arrancar el sistema frigorífico", "Hay variantes desde RC-EX3 y desde SW7-1.", [
    v("Desde RC-EX3", "Menú de instalación con Drain pump test run.", "RCEX3", "24", "Comprobar evacuación.", "Active la prueba, vierta agua y compruebe caudal, ruido, retorno y cierre de boya; salga desde el mando.", system="RC-EX3", scope="controller"),
    v("Desde SW7-1 sin comunicación de mando", "PCB interior accesible y alimentación desconectada.", "PAC", "17-18", "Hacer funcionar solo la bomba.", "Ponga SW7-1 antes de alimentar y desconecte CnB para impedir comunicación. En este modo opera solo la bomba y las protecciones del micro interior quedan inactivas.", system="PAC", scope="indoor", steps=[
        step(1, "Corte alimentación y coloque SW7-1 según el manual.", phase="prepare", warning="warning"),
        step(2, "Desconecte CnB solo si necesita la variante Drain Pump Test."),
        step(3, "Alimente y compruebe evacuación sin abandonar la unidad."),
        step(4, "Corte tensión, restaure SW7-1 y CnB.", phase="finish", warning="warning"),
    ]),
])
add_topic("commissioning", "pac-startup-checks", "PAC: puesta en marcha sin falsos códigos", "Válvulas, comunicación, drenaje y DIP deben validarse antes del Test Run.", [
    v("Comprobaciones previas", "Instalación nueva o placa sustituida.", "PAC", "17-18, 40-43", "Evitar E5/E9/E18/E19/E40/E57.", "Confirme vávulas abiertas, alimentación, interconexión, principal/secundaria, SW7-1 normal y drenaje antes de forzar.", system="PAC"),
    v("Protecciones durante Test Run", "SW3-3 activo.", "PAC", "40", "No ocultar una avería real.", "Test Run mantiene todos los controles de protección y detección; una parada debe diagnosticarse.", system="PAC", scope="outdoor"),
])
add_topic("commissioning", "kxz-autoaddress-test", "KXZ: direccionamiento, registro y Test Run", "No inicie la prueba hasta que la red esté estable.", [
    v("P31 automatic address setting", "Exterior maestra y Superlink terminado.", "KXZ", "49, 59", "Registrar interiores.", "Inicie P31 y espere a que finalice; compare el número registrado con la instalación y resuelva duplicados/ausencias.", system="KXZ", scope="outdoor"),
    v("SW5-1 / SW5-2", "PCB exterior con switches de Test Run.", "KXZ", "59", "Forzar prueba de sistema.", "SW5-1 gobierna Test Run y SW5-2 selecciona frío/calor. Las protecciones continúan activas.", system="KXZ", scope="outdoor"),
    v("Guardar datos antes de intervenir", "Aparece un error durante commissioning.", "KXZ", "50-60", "No perder el contexto.", "Conecte Mente PC, guarde al menos los datos previos a la parada y solo después corrija dirección, cable o placa.", system="KXZ", scope="outdoor"),
])
add_topic("multisplit", "scm-code-layers", "SCM: código interior y piloto de la exterior", "La misma avería puede señalarse en la unidad afectada y en la exterior común.", [
    v("Código de la interior", "Una sola unidad interior muestra luces o mando en error.", "SCM", "260-287", "Localizar la rama.", "Anote qué interior falla y si las demás continúan; E9, sondas y ventilador pueden ser locales.", system="SCM/RAC Multi", scope="indoor"),
    v("LED E exterior", "PCB exterior SCM con piloto de autodiagnóstico.", "SCM", "42-96, 287-289", "Cruzar la causa común.", "Cuente el patrón del LED E y compárelo con comunicación, sensores exteriores, corriente, ventilador e inverter.", system="SCM/RAC Multi", scope="outdoor"),
    v("Fallo común de exterior", "Varias interiores pierden capacidad a la vez.", "SCM", "260-289", "Distinguir rama y generador.", "Comunicación exterior, compresor, alimentación, presión y ventilador exterior afectan al conjunto; el alcance exacto depende de la protección.", system="SCM/RAC Multi"),
])
add_topic("multisplit", "simultaneous-control", "Control simultáneo y principal/secundaria", "Los errores de mando y dirección no son averías frigoríficas.", [
    v("E10/E14/E18", "Varias interiores bajo uno o dos mandos.", "PAC", "42-43", "Corregir grupo.", "E10 indica exceso de unidades; E14 falta principal o comunicación; E18 dirección principal/secundaria incorrecta.", system="PAC simultáneo", scope="controller"),
    v("Qué unidades siguen funcionando", "Una interior tiene sonda, ventilador o drenaje.", "PAC", "42-43", "Estimar alcance.", "Un fallo local detiene normalmente la interior afectada; una pérdida de exterior, presión o compresor bloquea el ciclo común.", system="PAC/SCM"),
])
add_topic("vrf_network", "kxz-superlink-network", "KXZ y New Superlink: red, dirección y terminación", "WAIT, E3/E5/E11/E31/E46 pertenecen a capas distintas.", [
    v("Dirección exterior", "PCB con selectores de decenas y unidades.", "KXZ", "59", "Evitar E31.", "Configure una dirección única y conserve una fotografía antes de sustituir la placa.", system="KXZ", scope="outdoor"),
    v("New Superlink", "Parámetro de comunicación y direccionamiento P31.", "KXZ", "49", "Preparar adquisición.", "Seleccione la red correcta, terminación y alimentación de todas las unidades antes del auto-addressing.", system="KXZ"),
    v("E3 frente a E5", "El mando indica comunicación.", "KXZ", "83-84", "Saber cuándo se perdió.", "E3 aparece cuando nunca se estableció la comunicación; E5 cuando se pierde durante el funcionamiento.", system="KXZ"),
])
add_topic("vrf_network", "kxz-system-effects", "KXZ: alcance de la parada", "El técnico debe saber si falla una interior o el ciclo.", [
    v("Fallo interior local", "E6/E7/E9/E16/E19/E28 con dirección IU.", "KXZ", "85-93", "Mantener el resto del sistema.", "Se detiene la interior afectada; otras interiores pueden continuar si no dependen de la misma causa.", system="KXZ", scope="indoor"),
    v("Fallo exterior común", "E32/E36/E40–E59 en la exterior.", "KXZ", "96-115", "Reconocer parada de ciclo.", "Fase, presión, inverter, compresor, ventilador y PCB detienen la exterior o el circuito común.", system="KXZ", scope="outdoor"),
    v("Control preventivo sin alarma fija", "Display C/estado limita frecuencia.", "KXZ", "42-58", "No sustituir componentes por una limitación.", "Demanda, alta/baja presión, descarga, retorno de aceite y desescarche pueden reducir capacidad antes de un E.", system="KXZ", scope="outdoor"),
])
add_topic("vrf_network", "kxz-forced-operation", "KXZ: frío/calor forzado y Pump Down", "La placa dispone de switches separados.", [
    v("SW3-7 — frío/calor forzado", "Entrada asignada y PCB exterior maestra.", "KXZ", "40, 59", "Forzar modo del sistema.", "La orden usa SW3-7 junto con la función de entrada seleccionada; confirme CnG/CnS y P correspondiente.", system="KXZ", scope="outdoor"),
    v("SW5-3 — Pump Down", "Procedimiento de retirada o alarma externa de fuga.", "KXZ", "36-37, 59", "Recuperar refrigerante.", "El manual diferencia recogida para retirar unidad y recogida por entrada externa de alarma. Siga la variante exacta.", system="KXZ", scope="outdoor"),
])
add_topic("component_checks", "communication-paths", "Diagnóstico de comunicación por capas", "No sustituya una PCB sin comprobar alimentación y cable.", [
    v("Mando–interior: 01/E1", "El mando está apagado, en WAIT o muestra E1.", "PAC", "42, 74", "Aislar el primer tramo.", "Compruebe alimentación interior, continuidad del par, hilo blanco en PAC antiguo, ruido y configuración Main/Sub.", system="RAC/PAC", scope="controller"),
    v("Interior–exterior: 05/61/62/E5", "Mando o pilotos indican pérdida entre unidades.", "RACZT", "30", "Distinguir arranque y pérdida.", "05: 35 s; 61: 10 s desde alimentación; 62: 7 min 35 s durante funcionamiento en la familia RAC revisada.", system="RAC"),
    v("Control exterior–inverter: E45", "PAC/KXZ con dos placas.", "PAC", "43, 109", "Separar enlace interno.", "Compruebe alimentación de 15 V, conectores y cable interno antes de condenar inverter o control.", system="PAC/KXZ", scope="outdoor"),
])
add_topic("component_checks", "sensors-pressure", "Sondas y transductores", "Código, punto de lectura y subcódigo evitan cambiar la sonda equivocada.", [
    v("RAC 37/38/39 y 82", "Pilotos RUN/TIMER.", "RACZT", "30", "Identificar la sonda.", "37 batería exterior, 38 aire exterior, 39 descarga, 82 batería interior.", system="RAC"),
    v("PAC E6/E7/E37/E38/E39/E53/E55", "Mando con prefijo E.", "PAC", "42-43", "Aplicar la tabla comercial.", "Confirme conector, montaje, resistencia y lectura antes de sustituir la PCB.", system="PAC"),
    v("KXZ con subcódigo", "E37-x, E39-1, E54-x o E56-1.", "KXZ", "97-113", "Elegir sensor/circuito exacto.", "Conserve el sufijo y compare presión real o temperatura con el monitor.", system="KXZ"),
])
add_topic("component_checks", "compressor-inverter-fan", "Compresor, inverter y ventilador exterior", "Las fichas separan carga, motor, driver y placa.", [
    v("RAC 42/51/59/60", "RUN/TIMER produce un código numérico.", "RACZT", "30", "Aislar potencia.", "Compruebe red, bus, U-V-W, aislamiento, bloqueo y válvulas antes de cambiar la PCB.", system="RAC", scope="outdoor"),
    v("PAC E41/E42/E48/E51/E59", "Mando E y LED amarillo inverter.", "PAC", "43-43-1", "Usar las dos capas.", "El amarillo 8/9/4 destellos ayuda a distinguir transistor, current cut y arranque.", system="PAC", scope="outdoor"),
    v("KXZ E41-1/E51-1/E56-1/E58-1", "Siete segmentos con sufijo -1.", "KXZ", "103-115", "Identificar inverter/compresor 1.", "Guarde datos Mente PC y espere al menos tres minutos tras cortar tensión antes de comprobar potencia.", system="KXZ", scope="outdoor"),
])
add_topic("technical_values", "quick-thresholds", "Umbrales y tiempos rápidos", "Cada valor queda unido a la familia que lo documenta.", [
    v("RAC Service Mode", "Pilotos RUN/TIMER.", "RACZT", "31", "Contar correctamente.", "Inicio 1,5 s no contado; destello 0,5 s; ciclo 11 s. 42 = RUN 4 + TIMER 2.", system="RAC", scope="indoor"),
    v("PAC drenaje", "E9 o bomba en post-marcha.", "PAC", "17", "Validar boya y tiempo.", "Float OPEN 3 s activa; CLOSE 10 s libera; post-marcha de bomba 5 min.", system="PAC", scope="indoor"),
    v("PAC Pump Down", "SW1 activo.", "PAC", "40", "Vigilar final.", "55 rps; baja ≤0,087 MPa durante 5 s o máximo acumulado 5 min.", system="PAC", scope="outdoor"),
    v("PAC ventilador exterior", "E48.", "PAC", "39, 43", "Confirmar repetición.", "100 min⁻¹ o menos durante 30 s; cinco detecciones en 60 min fijan E48.", system="PAC", scope="outdoor"),
    v("KXZ alimentación de control", "Diagnóstico E41/E42/E45/E48.", "KXZ", "61", "Comprobar PCB.", "El procedimiento de la placa usa la fuente de 15 V y exige esperar tres minutos tras cortar alimentación.", system="KXZ", scope="outdoor"),
])
add_topic("normal_states", "normal-delays", "Retardos y recuperaciones normales", "No toda parada breve es una avería.", [
    v("Retardo de tres minutos", "Compresor acaba de parar.", "PAC", "16, 39-40", "Evitar arranques repetidos.", "El rearranque queda inhibido tres minutos tras termostato, orden o condición anómala.", system="PAC/RAC"),
    v("E5 durante Pump Down", "Recogida PAC con SW1.", "PAC", "40", "Reconocer estado esperado.", "La comunicación con la interior se cancela y aparece E5; es normal exclusivamente durante esa secuencia.", system="PAC"),
    v("Current safe y sobrecarga", "Stop codes 31–46 recuperan.", "RACOLD", "37-38", "Distinguir protección y fallo.", "Una parada aislada puede recuperar; tres o más repeticiones justifican revisar carga, caudal, red y compresor.", system="RAC anterior"),
])
add_topic("normal_states", "defrost-oil-silent", "Desescarche, retorno de aceite y Silent", "Cambian frecuencia, ventiladores y válvulas sin ser una avería.", [
    v("Desescarche", "Calefacción, batería exterior fría y estado en monitor.", "KXZ", "54-55", "No confundir parada de ventiladores.", "El estado se guarda junto con datos de protección; la interior puede retener el ventilador para evitar aire frío.", system="KXZ/PAC"),
    v("Retorno de aceite", "VRF modifica frecuencia y EEV.", "KXZ", "54", "No interrumpir la secuencia.", "El monitor registra Oil return ON. La capacidad y las temperaturas pueden cambiar temporalmente.", system="KXZ"),
    v("Silent mode", "Orden de mando o entrada exterior.", "PAC", "40", "Explicar capacidad reducida.", "Reduce velocidad del ventilador exterior y frecuencia del compresor; no indica por sí mismo falta de gas.", system="PAC", scope="outdoor"),
])
add_topic("service_tools_boards", "mente-pc-monitoring", "Mente PC: herramienta de diagnóstico KXZ", "La documentación la considera el primer paso de servicio.", [
    v("Conectar antes de trabajar", "Sistema KXZ con interfaz de servicio.", "KXZ", "60", "Guardar evidencia.", "El procedimiento básico indica conectar Mente PC al llegar para comprobar, analizar y guardar datos.", system="KXZ"),
    v("Datos de funcionamiento", "Avería actual o intermitente.", "KXZ", "42-58", "Ver la película completa.", "Registra frecuencia, demanda, ventiladores, EEV, presiones, temperaturas, contadores, protecciones e interiores registrados.", system="KXZ"),
    v("30 minutos antes de la parada", "Diagnóstico de errores exteriores con Mente PC.", "KXZ", "94-116", "Conservar contexto.", "Las hojas de diagnóstico piden guardar con Mente PC los datos de operación, incluida la ventana de 30 minutos anterior a la parada, antes de cambiar componentes.", system="KXZ"),
])
add_topic("service_tools_boards", "board-replacement", "Después de sustituir una placa", "Direcciones y DIP deben copiarse antes del Test Run.", [
    v("PCB exterior KXZ", "E31/E43/E45/E46 tras una sustitución.", "KXZ", "59, 117-118", "Restaurar identidad.", "Copie dirección, New Superlink, funciones P, entradas y switches; espere tres minutos tras cortar tensión.", system="KXZ", scope="outdoor"),
    v("PCB interior PAC", "E1/E11/E14/E18/E19 después del cambio.", "PAC", "42-43", "Restaurar grupo y funciones.", "Confirme principal/secundaria, SW7-1, bomba, dirección y comunicación del mando.", system="PAC", scope="indoor"),
    v("Placa inverter", "E41/E42/E45/E51 tras sustituir.", "KXZ", "61, 117-118", "No omitir ventiladores y 15 V.", "Compruebe ambos ventiladores, la fuente de 15 V, conectores internos y referencia correcta antes de energizar.", system="KXZ", scope="outdoor"),
])
add_topic("system_architecture", "recognize-mhi-family", "Reconocer Mitsubishi Heavy antes de buscar", "La aplicación usa rasgos visibles, no obliga a saber el modelo.", [
    v("RAC split", "Mural con pilotos RUN verde y TIMER amarillo; mando inalámbrico.", "RACZT", "30-31", "Usar códigos numéricos.", "RUN forma decenas y TIMER unidades; no añada prefijo E.", system="RAC SRK/SRC"),
    v("PAC comercial", "Cassette/conductos/suelo-techo con mando cableado y código E.", "PAC", "42-43", "Usar tabla PAC.", "Cruce el E del mando con LED rojo/verde y, si existe, amarillo inverter.", system="PAC"),
    v("SCM multisplit", "Varias interiores comparten exterior y PCB con LED E.", "SCM", "260-289", "Localizar rama y fallo común.", "Anote qué interior informa y después lea la exterior.", system="SCM"),
    v("KX/KXZ VRF", "Muchas interiores, Superlink y exterior con siete segmentos/switches.", "KXZ", "42-62", "Usar cabecera y subcódigo.", "Conserve E37-5, E54-2, número de unidad y datos Mente PC.", system="KXZ"),
])
add_topic("system_architecture", "mhi-not-mitsubishi-electric", "Mitsubishi Heavy no es Mitsubishi Electric", "Evita aplicar tablas incompatibles.", [
    v("Identificación de fabricante", "Placa de características o documentación de la unidad.", "MANUALS", "portal", "Elegir la marca correcta.", "Mitsubishi Heavy Industries Thermal Systems usa familias SRK/SRC, SCM, FDT/FDU/FDC y KX/KXZ. Mitsubishi Electric usa otras familias y códigos.", system="Super Técnico"),
    v("Códigos cerrados por interpretación", "Un mismo E tiene varias fichas.", "ERRORWEB", "error code support", "No perder posibilidades.", "Ninguna interpretación se abre automáticamente: el técnico ve primero todas las variantes y elige la pantalla/familia correcta.", system="Super Técnico"),
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
            "reference_brand": "Mitsubishi Heavy Industries",
            "verification_warning": (
                "Completa respecto al corpus Mitsubishi Heavy Referencia V1. "
                "Confirme fabricante, familia y punto de lectura: RUN/TIMER RAC, "
                "mando PAC, LED exterior, SCM o siete segmentos KX/KXZ."
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
        "notes": "Fuente revisada para Mitsubishi Heavy Industries Referencia V1.",
    } for ident, row in enumerate(core.SOURCES.values(), start=1)])
    write_json(WEB_DIR / "coverage.json", [{
        "id": ident,
        "brand_id": BRAND_ID,
        "area_slug": slug,
        "area_name": name,
        "equipment_scope": "MHI — RAC, PAC, cassette, conductos, SCM multisplit, RC-EX3 y KX/KXZ VRF",
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
        "slug": "mitsubishi-heavy-industries",
        "name": "Mitsubishi Heavy Industries",
        "display_name": "Mitsubishi Heavy Industries",
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
            "Mitsubishi Heavy Industries Referencia V1: RAC actual y antiguo, "
            "PAC, cassette/conductos, SCM multisplit, RC-EX3 y KX/KXZ VRF; "
            "incluye pilotos RUN/TIMER, tabla exterior PAC, subcódigos de siete "
            "segmentos, procedimientos, drenaje, programación y alcance operativo."
        ),
    })
    return counts


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
