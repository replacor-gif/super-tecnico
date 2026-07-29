#!/usr/bin/env python3
"""Construye Hisense Referencia V1 para Super Técnico.

La proyección pública contiene resúmenes técnicos trazables. Los manuales,
capturas y la base maestra no se publican. Cada código conserva la familia,
el punto de lectura y el alcance documentado.
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
BRAND_DIR = ROOT / "data" / "brands" / "hisense"
WEB_DIR = BRAND_DIR / "web"
BRAND_ID = 11


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
    "HIFLEXI": {
        "title": "Hi-FLEXi S Series Heat Recovery — Technical, Installation and Service Handbook",
        "document_ref": "TCY12020008C",
        "source_url": "https://drive.google.com/file/d/1b81kkbP2rfOAzkaY1YFkCthZ7-eIU2IW/view?usp=share_link",
        "type": "service_manual", "year": "2023",
    },
    "CTRL": {
        "title": "Control Switch Technical and Service Handbook",
        "document_ref": "TC2201702B",
        "source_url": "https://deltaterm.net/media/smartweb/pdf/T_Hisense-Uputstvo%20za%20kontrolere%202017%20%5BENG%5D.pdf",
        "type": "service_manual", "year": "2017",
    },
    "FLOOR": {
        "title": "Floor Standing Air Conditioner Technical & Service Manual V3.2",
        "document_ref": "HISENSE-FLOOR-STANDING-V3.2",
        "source_url": "https://manualzz.com/doc/81168802/hisense-auf-48htr4fem--auf-60htr6fpm-technical-and-service-...",
        "type": "service_manual", "year": "s. f.",
    },
    "UNITARY": {
        "title": "DC Inverter Air Conditioner Service Manual V3.0",
        "document_ref": "HISENSE-UNITARY-SM-V3.0",
        "source_url": "https://manualzz.com/doc/6285293/service-manual-v-3.0",
        "type": "service_manual", "year": "s. f.",
    },
    "MULTI": {
        "title": "Multi-Split Type Air Conditioner Service Manual V3.0",
        "document_ref": "HISENSE-MULTI-SM-V3.0",
        "source_url": "https://manualzz.com/doc/6300650/service-manual-v--3.0",
        "type": "service_manual", "year": "s. f.",
    },
    "CASSETTE": {
        "title": "Cassette Inverter — Instrucciones de uso e instalación",
        "document_ref": "HISENSE-MX-CASSETTE-INVERTER",
        "source_url": "https://hisense.com.mx/storage/downloads/Cassette-Inverter/Mexico-Inverter-Cassette%20-comprimido.pdf",
        "type": "installation_manual", "year": "2025",
    },
    "SPLIT36": {
        "title": "AU36VQ2 — Instrucciones de uso e instalación",
        "document_ref": "HISENSE-MX-AU36VQ2",
        "source_url": "https://hisense.com.mx/storage/downloads/Inverter-Solo-Frio/Manual%20del%20usuario%20AU36VQ2-comprimido.pdf",
        "type": "installation_manual", "year": "2026",
    },
    "CAT24": {
        "title": "Catálogo Hisense HVAC España 2024",
        "document_ref": "HISENSE-HVAC-ES-2024",
        "source_url": "https://www.hisense.es/wp-content/uploads/2024/09/Hisense-Catalogo2024_ES-2.pdf",
        "type": "technical_catalog", "year": "2024",
    },
    "PORTAL": {
        "title": "Hisense HVAC — Technical Resources",
        "document_ref": "HISENSE-HVAC-TECHNICAL-RESOURCES",
        "source_url": "https://support.hisensehvac.com/TechnicalResources/index.aspx?nodeid=6279",
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
    (1, "errors", "Errores y protecciones", "Códigos de mando, display interior, placa exterior, multisplit y VRF."),
    (2, "outdoor_diagnostics", "Pilotos y display de la unidad exterior", "Conteo de pilotos, tubo digital y siete segmentos separados por familia."),
    (3, "diagnostic_access", "Obtención de códigos y subcódigos", "Métodos desde mando inalámbrico, cableado, central y placa."),
    (4, "history_reset", "Historial y borrado", "Memoria de alarmas, orden de eventos y borrado seguro."),
    (5, "service_modes", "Modos de servicio", "Test Run, marcha forzada, emergencia y comprobaciones de placa."),
    (6, "configuration", "Configuración y programación", "DIP, selectores, direcciones, funciones de mando y control central."),
    (7, "controllers_buses", "Mandos y buses", "Mandos HYXE/HYRE, H-NET, cableado, alimentación, grupos y arranque."),
    (8, "drainage_overflow", "Drenaje y desbordamiento", "Boya, bomba, bandeja, código 01/51 y comportamiento del sistema."),
    (9, "commissioning", "Puesta en marcha", "Auto-addressing, válvulas, fases, terminación y Test Run."),
    (10, "multisplit", "Multisplit y simultáneos", "Puertos, códigos exteriores, combinación y continuidad de unidades."),
    (11, "vrf_network", "VRF, recuperación de calor y red", "Hi-FLEXi, H-NET, exteriores combinadas y cajas selectoras."),
    (12, "component_checks", "Comprobación de componentes", "Sondas, motores, compresor, inverter, presiones, EEV y comunicación."),
    (13, "technical_values", "Valores técnicos", "Tensiones, resistencias, tiempos y umbrales documentados."),
    (14, "normal_states", "Comportamientos normales", "Retardos, desescarche, recuperación de aceite y precalentamiento."),
    (15, "service_tools_boards", "Herramientas y placas", "Hi-Checker, monitorización y tareas tras sustituir una PCB."),
    (16, "system_architecture", "Reconocer el sistema", "Pistas observables para elegir la tabla correcta sin pedir el modelo."),
]
CATEGORY_BY_SLUG = {
    slug: {"id": ident, "slug": slug, "name": name, "description": description}
    for ident, slug, name, description in CATEGORIES
}


PROFILE_TEXT = {
    "communication": (
        ["Cable abierto, cruzado, en corto o con terminal flojo", "Una unidad o placa sin alimentación", "Dirección, cantidad o terminación incorrecta", "Circuito de transmisión o fusible defectuoso"],
        ["Confirmar en qué equipo y pantalla se leyó", "Medir alimentaciones antes de condenar el bus", "Revisar continuidad, blindaje, rutas y terminales", "Aislar por tramos y repetir adquisición de unidades"],
        "El mismo número puede tener otra función en un display residencial o en H-NET.",
    ),
    "sensor": (
        ["Sensor o cable abierto/cortocircuitado", "Conector flojo o sensor intercambiado", "Sensor desprendido del punto de medida", "Entrada analógica de la PCB defectuosa"],
        ["Aislar el sensor y medir resistencia", "Comparar con temperatura real y tabla de esa familia", "Comprobar montaje térmico, conector y cable", "Comparar lectura del monitor con instrumento externo"],
        "No extrapolar una curva NTC de otro punto o generación.",
    ),
    "fan": (
        ["Rodete o hélice bloqueados", "Motor o realimentación defectuosos", "Conector, cable o alimentación anormales", "Driver o PCB de control defectuosos"],
        ["Aislar tensión y comprobar giro libre", "Revisar cableado y devanados", "Medir alimentación/realimentación con el método del manual", "Separar fallo de motor y de placa antes de sustituir"],
        "No conectar ni desconectar motores DC/BLDC con tensión.",
    ),
    "drain": (
        ["Boya atascada arriba o nivel realmente alto", "Tubo obstruido, mal nivelado o con retorno", "Bomba defectuosa", "Cableado, flotador o entrada de placa anormales"],
        ["Comprobar nivel real y movimiento de la boya", "Verificar continuidad del flotador", "Probar evacuación con agua y revisar altura del tubo", "Confirmar salida de bomba antes de sustituir PCB"],
        "La máquina activa la protección por nivel; el origen puede ser hidráulico o eléctrico.",
    ),
    "configuration": (
        ["Dirección duplicada o fuera de rango", "DIP/selector o capacidad mal configurados", "PCB nueva sin restaurar ajustes", "Número de unidades o combinación no válida"],
        ["Fotografiar y anotar posiciones originales", "Comparar unidad principal, subordinadas y ciclo frigorífico", "Comprobar número reconocido tras auto-addressing", "Reiniciar y repetir Test Run tras corregir"],
        "Una configuración incorrecta puede bloquear una unidad, una rama o todo el sistema.",
    ),
    "inverter": (
        ["Compresor bloqueado o bobinado anormal", "IPM/inverter o driver defectuoso", "Bus DC o red fuera de rango", "Disipador, ventilación o sensor anormales"],
        ["Aislar alimentación y esperar descarga del bus", "Comprobar U-V-W y aislamiento a tierra", "Medir red, bus y salida con el procedimiento documentado", "Separar compresor, cableado, driver y PCB principal"],
        "Las mediciones de potencia deben realizarlas técnicos cualificados.",
    ),
    "power": (
        ["Fase ausente, invertida o desequilibrada", "Tensión fuera de rango o capacidad insuficiente", "Conexión floja, contactor o fusible anormal", "Circuito de medida de corriente/tensión defectuoso"],
        ["Medir entrada en reposo y bajo carga", "Comprobar las tres fases y su secuencia", "Revisar aprietes, contactor y fusibles", "Comparar la medida real con el valor leído por la placa"],
        "No confundir protección de red con avería del compresor.",
    ),
    "pressure": (
        ["Válvula de servicio cerrada", "Carga incorrecta, fuga o gas no condensable", "Intercambiador, filtro o caudal de aire insuficientes", "EEV, presostato o transductor defectuosos"],
        ["Confirmar válvulas totalmente abiertas", "Comparar manómetros y lectura del sensor", "Revisar ventiladores, filtros e intercambiadores", "Comprobar EEV y cantidad de refrigerante"],
        "Los umbrales y el alcance cambian entre unitario, multisplit y VRF.",
    ),
    "compressor": (
        ["Cable U-V-W o devanados anormales", "Presiones sin equilibrar", "Inverter o contactor defectuoso", "Compresor mecánicamente bloqueado"],
        ["Aislar y descargar el bus", "Comparar resistencia entre fases y aislamiento", "Comprobar salida del inverter o contactor", "Revisar alarmas repetidas antes del bloqueo"],
        "EE en VRF se registra tras repetirse determinadas protecciones tres veces en seis horas.",
    ),
    "valve": (
        ["Bobina o cable abierto", "EEV o válvula de cuatro vías bloqueada", "Conector intercambiado", "Carga o presión impiden la respuesta prevista"],
        ["Comprobar bobina y conector", "Usar el modo de servicio si existe", "Comparar temperaturas antes y después", "Revisar presión y refrigerante antes de condenar la válvula"],
        "Una respuesta térmica anormal no demuestra por sí sola una válvula defectuosa.",
    ),
    "pcb": (
        ["PCB sin alimentación o fusible abierto", "EEPROM, MCU o driver defectuosos", "Conector interno suelto", "Configuración no restaurada tras sustitución"],
        ["Comprobar fuentes y fusibles", "Revisar conectores internos", "Copiar ajustes, direcciones y capacidad", "Inicializar, repetir adquisición y comprobar historial"],
        "No sustituir una placa por un fallo de comunicación sin aislar antes cable y alimentación.",
    ),
    "normal": (
        ["Secuencia normal, espera o protección temporal"],
        ["Identificar el indicador exacto", "Esperar el tiempo documentado", "Consultar historial si no recupera", "No sustituir componentes por un estado normal"],
        "El precalentamiento, el retardo de tres minutos y ciertos modos VRF no son averías.",
    ),
}


ERROR_SPECS: list[dict[str, Any]] = []


def add_error(
    code: str, title: str, profile: str, ref: str, page: str, *,
    family: str, scope: str = "system", behavior: str = "La protección detiene el funcionamiento afectado.",
    technical: str = "", aliases: list[str] | None = None,
) -> None:
    ERROR_SPECS.append({
        "code": code, "title": title, "profile": profile, "ref": ref, "page": page,
        "family": family, "scope": scope, "behavior": behavior,
        "technical": technical or PROFILE_TEXT[profile][2], "aliases": aliases or [],
    })


# Hi-FLEXi S: tabla oficial de alarmas, incluida la capa de mando y display exterior.
VRF_ERRORS = [
    ("01", "Protección interior por boya o nivel alto", "drain", "indoor"),
    ("02", "Corte por alta presión PSH", "pressure", "system"),
    ("03", "Comunicación entre unidad interior y exterior", "communication", "system"),
    ("04", "Comunicación entre PCB inverter y PCB exterior", "communication", "outdoor"),
    ("04", "Comunicación entre controlador de ventilador y PCB exterior", "communication", "outdoor"),
    ("05", "Secuencia de fases incorrecta o fase abierta", "power", "system"),
    ("06", "Tensión anormal del inverter", "power", "outdoor"),
    ("06", "Tensión anormal del controlador de ventilador", "power", "outdoor"),
    ("07", "Sobrecalentamiento de descarga demasiado bajo", "pressure", "system"),
    ("08", "Temperatura de descarga demasiado alta", "pressure", "system"),
    ("0A", "Comunicación entre unidades exteriores", "communication", "system"),
    ("0b", "Dirección exterior duplicada", "configuration", "system"),
    ("0C", "Más de una exterior configurada como principal", "configuration", "system"),
    ("11", "Sonda de aire de entrada o agua de entrada", "sensor", "indoor"),
    ("12", "Sonda de aire de salida o agua de salida", "sensor", "indoor"),
    ("13", "Sonda de protección antihielo", "sensor", "indoor"),
    ("14", "Sonda de tubería de gas interior", "sensor", "indoor"),
    ("15", "Sonda de aire de recuperador total", "sensor", "indoor"),
    ("16", "Sonda del mando", "sensor", "controller"),
    ("17", "Sonda integrada en mando cableado", "sensor", "controller"),
    ("19", "Protección del ventilador interior", "fan", "indoor"),
    ("21", "Sensor de alta presión", "sensor", "outdoor"),
    ("22", "Sonda de aire exterior", "sensor", "outdoor"),
    ("23", "Sonda de descarga del compresor", "sensor", "outdoor"),
    ("24", "Sonda de líquido del intercambiador exterior", "sensor", "outdoor"),
    ("25", "Sonda de gas del intercambiador exterior", "sensor", "outdoor"),
    ("29", "Sensor de baja presión", "sensor", "outdoor"),
    ("31", "Capacidad exterior/interior incorrecta", "configuration", "system"),
    ("35", "Dirección interior duplicada", "configuration", "system"),
    ("36", "Combinación interior no compatible", "configuration", "system"),
    ("37", "Número de módulos de agua incorrecto", "configuration", "system"),
    ("38", "Circuito exterior de detección de protecciones", "pcb", "outdoor"),
    ("39", "Corriente anormal del compresor de velocidad fija", "compressor", "outdoor"),
    ("3A", "Capacidad exterior superior al límite", "configuration", "system"),
    ("3b", "Combinación o tensión de exteriores incorrecta", "configuration", "system"),
    ("3d", "Comunicación entre exterior principal y subordinadas", "communication", "system"),
    ("43", "Relación de compresión demasiado baja", "pressure", "system"),
    ("44", "Aumento anormal de baja presión", "pressure", "system"),
    ("45", "Aumento anormal de alta presión", "pressure", "system"),
    ("46", "Descenso anormal de alta presión", "pressure", "system"),
    ("47", "Descenso anormal de baja presión o vacío", "pressure", "system"),
    ("48", "Sobrecorriente del inverter", "inverter", "outdoor"),
    ("51", "Sensor de corriente del inverter", "sensor", "outdoor"),
    ("53", "Señal de error del inverter", "inverter", "outdoor"),
    ("54", "Temperatura anormal del disipador inverter", "inverter", "outdoor"),
    ("55", "Fallo de PCB inverter", "inverter", "outdoor"),
    ("57", "Protección del controlador de ventilador", "fan", "outdoor"),
    ("5A", "Temperatura anormal del disipador de ventilador", "fan", "outdoor"),
    ("5b", "Sobrecorriente del motor de ventilador", "fan", "outdoor"),
    ("5C", "Sensor del controlador de ventilador", "sensor", "outdoor"),
    ("EE", "Bloqueo por protección repetida del compresor", "compressor", "system"),
    ("A6", "Temperatura anormal del módulo de refrigeración", "pressure", "outdoor"),
    ("b1", "Dirección de unidad o ciclo superior al límite", "configuration", "system"),
    ("b5", "Demasiadas interiores no H-NET II", "configuration", "system"),
    ("7A", "Anomalía del módulo de agua", "pressure", "system"),
    ("C1", "Dos cajas selectoras conectadas en serie", "configuration", "system"),
    ("C2", "Demasiadas interiores conectadas a la caja selectora", "configuration", "system"),
    ("C3", "Interior de otro ciclo conectada a la caja selectora", "configuration", "system"),
    ("C4", "Puerto de caja selectora mal declarado", "configuration", "system"),
]
for code, title, profile, scope in VRF_ERRORS:
    behavior = (
        "Se detiene la unidad interior afectada; el resto puede continuar si el sistema lo permite."
        if scope in {"indoor", "controller"} else
        "La protección detiene la exterior o el ciclo frigorífico afectado."
    )
    technical = {
        "01": "La entrada de boya permanece activa por nivel alto, drenaje, bandeja o flotador.",
        "03": "Si la transmisión era normal y se pierde, se evalúa durante 3 minutos; desde el arranque se indica tras 30 segundos.",
        "19": "El manual detecta menos de 70 rpm durante 5 segundos, tres veces en 30 minutos.",
        "21": "La entrada del sensor fuera de 0,1–4,9 V se considera anormal.",
        "EE": "No se rearma desde el mando: aparece si 02, 07, 08, 43–45 o 47 ocurre tres veces en 6 horas.",
    }.get(code, "")
    add_error(code, title, profile, "HIFLEXI", "124-185", family="Hi-FLEXi S Heat Recovery", scope=scope, behavior=behavior, technical=technical)


# Módulo de agua y caja selectora: significados adicionales de números ya usados.
for code, title, profile in [
    ("16", "Sonda del depósito de agua", "sensor"), ("17", "Sonda de salida del intercambiador de placas", "sensor"),
    ("70", "Caudal o presión de agua insuficientes", "pressure"), ("71", "Protección del calentador del depósito", "power"),
    ("72", "Protección del calentador del módulo de agua", "power"), ("73", "Interruptor de caudal activo con bomba parada", "pressure"),
    ("76", "Protección antihielo del módulo de agua", "pressure"), ("80", "Comunicación mando–módulo de agua", "communication"),
    ("7C", "Comunicación módulo de agua–unidad exterior", "communication"),
]:
    add_error(code, title, profile, "HIFLEXI", "125", family="Hi-FLEXi S — módulo de agua", scope="system",
              behavior="Se detiene el módulo de agua afectado; comprobar si el resto del sistema permanece operativo.")


# Equipos comerciales/unitarios antiguos. El lugar de lectura es decisivo.
LEGACY_OUTDOOR = [
    ("1", "Sonda de temperatura ambiente exterior", "sensor"),
    ("2", "Sonda de batería exterior", "sensor"),
    ("3", "Parada por sobrecorriente de la unidad", "power"),
    ("4", "Error de datos EEPROM exterior", "pcb"),
    ("5", "Antihielo en frío o sobrecarga interior en calor", "pressure"),
    ("6", "Protección por bloqueo de motor en unidad ON/OFF", "fan"),
    ("7", "Comunicación entre unidad interior y exterior", "communication"),
    ("8", "Desequilibrio de corriente entre fases", "power"),
    ("9", "Corriente anormal en fase U del compresor", "power"),
    ("10", "Corriente anormal en fase V del compresor", "power"),
    ("11", "Secuencia de fases o cableado trifásico incorrectos", "power"),
    ("12", "Fase ausente en alimentación trifásica", "power"),
    ("13", "Protección térmica del compresor", "compressor"),
    ("14", "Protección de alta presión", "pressure"),
    ("15", "Protección de baja presión", "pressure"),
    ("16", "Sobrecarga del sistema en refrigeración", "pressure"),
    ("17", "Sonda de temperatura de descarga", "sensor"),
    ("18", "Tensión de alimentación anormal", "power"),
    ("19", "Sonda de aspiración", "sensor"),
    ("20", "Sonda de entrada del condensador", "sensor"),
    ("21", "Sonda de salida del condensador", "sensor"),
    ("22", "Sonda de desescarche", "sensor"),
    ("23", "Sonda de tubo fino del puerto A", "sensor"),
    ("24", "Sonda de tubo fino del puerto B", "sensor"),
    ("25", "Sonda de tubo fino del puerto C", "sensor"),
    ("26", "Sonda de tubo fino del puerto D", "sensor"),
    ("28", "Sonda de tubo grueso del puerto A", "sensor"),
    ("29", "Sonda de tubo grueso del puerto B", "sensor"),
    ("30", "Sonda de tubo grueso del puerto C", "sensor"),
    ("31", "Sonda de tubo grueso del puerto D", "sensor"),
    ("44", "Sensor de baja presión", "sensor"),
    ("45", "Fallo IPM; consultar el código del driver", "inverter"),
    ("48", "Ventilador exterior DC superior", "fan"),
    ("49", "Ventilador exterior DC inferior", "fan"),
    ("50", "Sonda de EEV de caja selectora", "sensor"),
    ("63", "Sensor de corriente exterior", "sensor"),
]
for code, title, profile in LEGACY_OUTDOOR:
    add_error(code, title, profile, "FLOOR", "68-77", family="Comercial unitario/multisplit — display o piloto exterior",
              scope="outdoor", behavior="Se detiene la unidad exterior o la función afectada.",
              technical="En modelos ON/OFF el piloto exterior repite el número; en inverter se lee directamente en el tubo digital.")


LEGACY_INDOOR = [
    ("31", "Teclas o entrada AD del panel frontal", "pcb"),
    ("32", "Panel frontal fuera de posición", "configuration"),
    ("33", "Sonda de temperatura ambiente interior", "sensor"),
    ("34", "Sonda de batería interior", "sensor"),
    ("36", "Comunicación interior–exterior", "communication"),
    ("51", "Protección de drenaje o nivel alto", "drain"),
    ("52", "Protección de rejilla", "configuration"),
    ("53", "Panel superior fuera de posición", "configuration"),
    ("54", "Panel inferior fuera de posición", "configuration"),
    ("64", "Comunicación interior–exterior en comercial/VRF antiguo", "communication"),
    ("65", "La interior no recibe al mando cableado", "communication"),
    ("72", "Fallo del ventilador interior", "fan"),
    ("73", "EEPROM interior", "pcb"),
    ("80", "Fallo de teclas del panel", "pcb"),
    ("81", "Sonda ambiente interior", "sensor"),
    ("83", "Sonda de batería interior", "sensor"),
    ("EA", "Comunicación entre display y PCB interior", "communication"),
    ("ER", "Comunicación del panel/display con la PCB interior", "communication"),
    ("FE", "El mando cableado no recibe a la unidad interior", "communication"),
]
for code, title, profile in LEGACY_INDOOR:
    add_error(code, title, profile, "FLOOR", "61-85", family="Comercial antiguo — mando, display o PCB interior",
              scope="indoor", behavior="Se detiene la unidad interior afectada; otras unidades pueden continuar.")


# Residencial: códigos de display que no deben mezclarse con los números VRF.
for code, title, profile in [
    ("E4", "Ventilador interior no mantiene la velocidad", "fan"),
    ("E8", "Protección de sobrecorriente en esta familia residencial", "power"),
    ("E9", "Protección de corriente máxima", "power"),
    ("E11", "EEPROM exterior", "pcb"),
    ("E13", "Temperatura de descarga elevada", "pressure"),
    ("E14", "Sonda de ambiente exterior", "sensor"),
    ("E15", "Protección de temperatura de carcasa del compresor", "compressor"),
    ("E16", "Antihielo interior en frío o sobrecarga en calor", "pressure"),
    ("E21", "Protección de batería exterior en refrigeración", "pressure"),
    ("E33", "Sonda ambiente interior", "sensor"),
    ("E34", "Sonda de batería interior", "sensor"),
    ("E36", "Comunicación interior–exterior", "communication"),
]:
    add_error(code, title, profile, "UNITARY", "49-65", family="Split DC inverter — display interior",
              scope="indoor", behavior="El compresor se detiene; el display interior conserva el código para diagnóstico.")


# Multisplit: tabla exterior por número y acceso desde mando/emergencia.
for code, title, profile in [
    ("5", "Comunicación entre PCB principal e IPM", "communication"),
    ("6", "Sonda de aspiración", "sensor"), ("7", "Sonda de descarga", "sensor"),
    ("8", "Sonda superior/carcasa del compresor", "sensor"), ("9", "Sonda de batería exterior", "sensor"),
    ("10", "Sonda de desescarche", "sensor"), ("11", "Sonda de aire exterior", "sensor"),
    ("12", "Sonda de líquido del puerto A", "sensor"), ("13", "Sonda de líquido del puerto B", "sensor"),
    ("14", "Sonda de líquido del puerto C", "sensor"), ("15", "Sonda de líquido del puerto D", "sensor"),
    ("16", "Sonda de gas del puerto A", "sensor"), ("17", "Sonda de gas del puerto B", "sensor"),
    ("18", "Sonda de gas del puerto C", "sensor"), ("19", "Sonda de gas del puerto D", "sensor"),
]:
    add_error(code, title, profile, "MULTI", "149-153", family="Multisplit AMW — display exterior",
              scope="outdoor", behavior="La exterior registra la rama o componente; las interiores no afectadas pueden seguir según la protección.")


# Códigos de control: limitan antes de declarar una avería.
for code, title, profile, technical in [
    ("P01", "Control por relación de presiones", "pressure", "El control reduce o reintenta para evitar una relación de compresión anormal."),
    ("P02", "Control por aumento de alta presión", "pressure", "Actúa por incremento de la presión de descarga."),
    ("P03", "Control por corriente del inverter", "inverter", "Limita la frecuencia por corriente del compresor."),
    ("P04", "Control por temperatura del disipador inverter", "inverter", "Reduce capacidad para proteger el módulo de potencia."),
    ("P05", "Control por temperatura de descarga", "pressure", "Reduce capacidad antes del corte por temperatura."),
    ("P06", "Control por descenso de baja presión", "pressure", "Condición documentada: Ps ≤ 0,2 MPa."),
    ("P09", "Control por descenso de alta presión", "pressure", "Condición documentada: Pd ≤ 1,5 MPa."),
    ("P0A", "Limitación por demanda de corriente", "power", "La corriente del compresor alcanza el límite de demanda configurado."),
    ("P0d", "Control por aumento de baja presión", "pressure", "Condición documentada: Ps ≥ 1,5 MPa."),
]:
    add_error(code, title, profile, "HIFLEXI", "193-195", family="Hi-FLEXi S — display de protección",
              scope="outdoor", behavior="El sistema limita o reintenta; no es por sí solo una alarma permanente.",
              technical=technical)


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
            info_items.append({
                "id": ident * 100 + order, "item_type": item_type, "title": None,
                "body": text, "sort_order": order, "review_status": "reviewed", "origin_ref": origin,
            })
            order += 1
    info_items.append({
        "id": ident * 100 + order, "item_type": "observation", "title": "Dato técnico",
        "body": technical, "sort_order": order, "review_status": "reviewed", "origin_ref": origin,
    })
    location = {
        "controller": "mando o controlador", "outdoor": "placa/display de unidad exterior",
        "indoor": "display, panel o PCB de unidad interior", "system": "mando, exterior o sistema",
    }[spec["scope"]]
    indication_type = {
        "controller": "controller", "outdoor": "outdoor_display",
        "indoor": "indoor_display", "system": "display",
    }[spec["scope"]]
    lower = spec["behavior"].lower()
    stop_level = (
        "warning" if "limita" in lower or "reintenta" in lower or "puede seguir" in lower
        else "affected_unit" if "afectada" in lower or "módulo" in lower
        else "all_system" if "ciclo frigorífico" in lower or "sistema" in lower
        else "protected_stop"
    )
    source_kind = "official" if spec["ref"] in {"HIFLEXI", "CASSETTE", "SPLIT36", "CAT24", "PORTAL"} else "manufacturer_manual"
    return {
        "id": ident, "title": spec["title"],
        "description": f'{spec["code"]} en {spec["family"]}: {spec["title"]}.',
        "source_kind": source_kind, "confidence": "high", "review_status": "reviewed",
        "indication_contexts": [{
            "code_display": spec["code"], "code_normalized": normalize(spec["code"]),
            "indication_type": indication_type, "display_location": location,
            "family_hint": spec["family"],
            "relationship": "Significado válido únicamente para esta familia y este punto de lectura.",
            "source_ref": spec["ref"], "source_document_ref": origin, "related_error_id": None,
        }],
        "info_items": info_items,
        "operational_impacts": [{
            "stop_level": stop_level, "summary": spec["behavior"],
            "affected_scope": f'Alcance documentado para {spec["family"]}.',
            "unaffected_scope": "Compruebe la ficha: una misma cifra puede detener solo la unidad, una rama o todo el ciclo.",
            "restart_behavior": "Corregir la causa y rearmar únicamente con el procedimiento de esta familia.",
            "degraded_behavior": None,
            "notes": "No extrapolar este alcance a otro mando, display o generación.",
        }],
        "datasets": [{
            "id": ident * 10 + 1, "name": f'{spec["code"]} — referencia técnica',
            "dataset_type": "technical_reference", "variable_name": "Comprobación", "variable_unit": None,
            "value_name": "Dato", "value_unit": None, "tolerance_text": f'Aplicar solo a {spec["family"]}.',
            "source_kind": source_kind, "calculation_method": None, "review_status": "reviewed",
            "notes": technical, "visible": 1,
            "points": [{
                "variable_value": None, "value_min": None, "value_nominal": None,
                "value_max": None, "value_text": technical, "sort_order": 1, "notes": None,
            }],
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
            primary["code"], primary["code"].replace("-", " "),
            primary["code"].replace("-", ""), *(alias for spec in specs for alias in spec["aliases"]),
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
        scopes = {item["scope"] for item in specs}
        detail = {
            "id": error_id, "code_display": primary["code"], "code_normalized": key,
            "indication_type": "mixed" if len(scopes) > 1 else (
                "outdoor_display" if primary["scope"] == "outdoor"
                else "controller" if primary["scope"] == "controller"
                else "indoor_display" if primary["scope"] == "indoor" else "display"
            ),
            "unit_scope": "mixed" if len(scopes) > 1 else primary["scope"],
            "short_label": primary["title"],
            "aliases": [{"alias_display": value, "alias_normalized": normalize(value)} for value in aliases],
            "tags": tags, "interpretations": interpretations, "media": [],
        }
        index_rows.append({
            "id": error_id, "code_display": primary["code"], "code_normalized": key,
            "indication_type": detail["indication_type"], "unit_scope": detail["unit_scope"],
            "short_label": primary["title"], "aliases": aliases, "tags": tags,
            "search_text": normalize(" ".join([
                primary["code"], *aliases, *tags, *(item["title"] for item in specs),
                *(item["family"] for item in specs),
            ])),
            "interpretation_count": len(interpretations),
        })
        detail_rows.append(detail)
    return index_rows, detail_rows


def section(title: str, body: str, kind: str = "technical", open_by_default: bool = False) -> dict[str, Any]:
    return {
        "section_type": kind, "title": title, "body": body,
        "collapsed_default": 0 if open_by_default else 1,
    }


def step(no: int, instruction: str, expected: str = "", phase: str = "procedure", warning: str = "none") -> dict[str, Any]:
    return {
        "phase": phase, "step_no": no, "instruction": instruction,
        "expected_result": expected or None, "warning_level": warning,
    }


def controller(
    kind: str, bus: str, wires: str, polarity: str, voltage: str, terminals: str = "",
) -> dict[str, Any]:
    return {
        "controller_type": kind, "bus_type": bus, "wire_count": wires,
        "polarity": polarity, "nominal_voltage": voltage, "terminals": terminals,
    }


def variant(
    title: str, recognition: str, ref: str, page: str, purpose: str, summary: str, *,
    system: str = "Hisense", scope: str = "system", steps: list[dict[str, Any]] | None = None,
    parameters: list[dict[str, Any]] | None = None, controller_data: dict[str, Any] | None = None,
    monitoring: list[dict[str, Any]] | None = None, led_patterns: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    source_kind = "official" if ref in {"HIFLEXI", "CASSETTE", "SPLIT36", "CAT24", "PORTAL"} else "manufacturer_manual"
    return {
        "title": title, "recognition": recognition, "system_type": system, "unit_scope": scope,
        "refrigerant": None, "purpose": purpose, "summary": summary,
        "source_kind": source_kind, "review_status": "reviewed",
        "sections": [
            section("Cómo reconocer esta variante", recognition, "recognition", True),
            section("Qué hace o tiene en cuenta la máquina", summary),
        ],
        "steps": steps or [
            step(1, "Identifique familia, placa y lugar exacto de la indicación.", phase="prepare"),
            step(2, "Aplique solo el procedimiento documentado para esta variante."),
            step(3, "Anote código, dirección, unidad y resultado antes de borrar o cortar tensión.", phase="verify"),
        ],
        "parameters": parameters or [], "controller": controller_data,
        "monitoring_points": monitoring or [], "led_patterns": led_patterns or [],
        "media": [], "sources": [source(ref, page, title)],
    }


def lamp_pattern(code: str, meaning: str) -> dict[str, Any]:
    return {
        "code_display": code, "indication_type": "outdoor_led",
        "display_location": "piloto LED2 de placa exterior",
        "family_hint": "Hisense comercial ON/OFF con caja de control exterior",
        "relationship": meaning,
        "led_indicators": [{"label": "LED2", "color": "red", "state": "blink"}],
        "counting_rule": f"El piloto parpadea {code} vez/veces: 300 ms encendido y 300 ms apagado.",
        "cycle_note": "Tras el grupo de destellos hay una pausa de 900 ms y se repite.",
        "sequence": "Cuente varios ciclos completos antes de interpretar.",
    }


LEGACY_LED_PATTERNS = [
    lamp_pattern(code, title) for code, title, _ in LEGACY_OUTDOOR
    if code.isdigit() and 1 <= int(code) <= 18
]


TOPICS: list[dict[str, Any]] = []


def add_topic(category: str, slug: str, title: str, summary: str, variants: list[dict[str, Any]]) -> None:
    TOPICS.append({
        "category": category, "slug": slug, "title": title,
        "summary": summary, "variants": variants,
    })


add_topic("outdoor_diagnostics", "legacy-outdoor-led-table", "Tabla de pilotos exteriores Hisense ON/OFF", "Los destellos representan el número de fallo; no son los LED de un inverter.", [
    variant("LED2 exterior — tabla 1 a 18", "Caja de control exterior con un LED2 de avería, sin tubo digital.", "FLOOR", "65-71", "Traducir el conteo de destellos.", "Cada destello dura 300 ms, hay 300 ms entre destellos y 900 ms antes de repetir. La tabla conserva los 18 significados.", system="Comercial ON/OFF", scope="outdoor", led_patterns=LEGACY_LED_PATTERNS),
    variant("Cómo contar sin equivocarse", "El piloto repite grupos y puede parecer un parpadeo continuo.", "FLOOR", "65-71", "Distinguir código y ruido de arranque.", "Cuente al menos tres ciclos, confirme la pausa de 900 ms y anote si la unidad estaba arrancando, funcionando o parada.", system="Comercial ON/OFF", scope="outdoor"),
])
add_topic("outdoor_diagnostics", "digital-tube-layers", "Tubo digital exterior: unitario, multisplit y VRF", "La cifra se lee de forma distinta según la arquitectura.", [
    variant("Inverter unitario y multisplit", "PCB exterior con uno o dos displays de siete segmentos.", "FLOOR", "66-77", "Leer el código exterior directamente.", "La exterior muestra sus fallos en el tubo digital. En multisplit, una sonda de puerto A–D identifica la rama.", system="Unitario/multisplit", scope="outdoor"),
    variant("VRF Hi-FLEXi", "Exterior principal con SEG1/SEG2 y pulsadores PSW.", "HIFLEXI", "107-110, 193-195", "Separar unidad, alarma y código de reintento.", "SEG1/SEG2 muestran dirección/unidad, alarma AC, reintento d1, reinicio c1 o protección P. El historial completa exterior, compresor y controlador de ventilador.", system="Hi-FLEXi S", scope="outdoor"),
])
add_topic("errors", "same-code-different-layer", "El mismo código cambia con el lugar de lectura", "Ninguna interpretación se abre por defecto: el técnico elige la que encaja.", [
    variant("03, 16 y 17", "Código numérico en mando VRF, display comercial o placa exterior.", "HIFLEXI", "124-125", "Evitar una definición universal.", "03 es comunicación H-NET en VRF; 16/17 pueden ser sondas de mando, sondas de agua o protecciones de familias antiguas.", system="Hisense varias familias"),
    variant("31, 36, 51, 64 y 72", "Cifras repetidas entre interior, exterior y sistema.", "FLOOR", "68-85", "Abrir todas las posibilidades.", "31 puede ser capacidad VRF, sonda de puerto o teclas; 51 puede ser sensor inverter o drenaje; 72 puede ser calentador de agua o ventilador interior.", system="Hisense varias familias"),
    variant("E8 no es universal", "Display residencial alfanumérico.", "UNITARY", "49-65", "No trasladar códigos de Midea u otra marca.", "En la familia Hisense residencial documentada E8 es sobrecorriente; confirme siempre marca, display y familia antes de aplicar la ficha.", system="Split DC inverter"),
])
add_topic("diagnostic_access", "wireless-code-retrieval", "Mando inalámbrico: cuatro métodos de obtención", "El número de pulsaciones cambia con mando y familia.", [
    variant("SLEEP cuatro veces", "Split de pared con mando clásico y display interior.", "UNITARY", "86-87", "Mostrar el último código.", "Con la unidad en marcha, pulse SLEEP cuatro veces; si no hay avería aparece 00.", system="Split de pared", scope="controller", steps=[
        step(1, "Ponga la unidad en funcionamiento con el mando.", phase="prepare"),
        step(2, "Pulse SLEEP cuatro veces seguidas."),
        step(3, "Lea el código que parpadea en el display interior; 00 indica ausencia de código.", phase="verify"),
    ]),
    variant("SLEEP diez veces", "Mando nuevo donde SLEEP cambia entre cuatro combinaciones.", "UNITARY", "49-50", "Entrar en consulta sin cambiar el ajuste Sleep.", "En esta variante la consulta responde a diez pulsaciones en diez segundos.", system="Split de pared", scope="controller"),
    variant("HIGH POWER cinco veces", "Multisplit con tecla HIGH POWER o H.P.", "MULTI", "149", "Mostrar error interior o exterior en el área de temperatura.", "Pulse HIGH POWER cinco veces; el código se muestra en el área de temperatura de la unidad interior.", system="Multisplit AMW", scope="controller"),
    variant("Interruptor de emergencia cinco segundos", "No hay mando disponible, pero la interior tiene pulsador de emergencia.", "MULTI", "149", "Consultar sin mando.", "Mantenga el interruptor de emergencia más de cinco segundos; el display interior muestra el error.", system="Multisplit AMW", scope="indoor"),
])
add_topic("diagnostic_access", "floor-cassette-code-retrieval", "Suelo, conductos y cassette: mando, panel y PCB", "Métodos antiguos que siguen apareciendo en instalaciones.", [
    variant("CLOCK ocho veces", "Equipo de suelo con panel no bloqueado.", "FLOOR", "61-67", "Mostrar el código durante diez segundos.", "Pulse CLOCK ocho veces; el código se muestra diez segundos y desaparece automáticamente.", system="Suelo comercial", scope="controller"),
    variant("SLEEP ocho veces", "Equipo de suelo con mando inalámbrico compatible.", "FLOOR", "61-67", "Consultar desde el mando.", "Pulse SLEEP ocho veces; el código se muestra durante diez segundos.", system="Suelo comercial", scope="controller"),
    variant("RUN y DEFROST forman decenas y unidades", "Cassette o techo-suelo con dos pilotos.", "UNITARY", "87-89", "Traducir el parpadeo interior.", "RUN y DEFROST parpadean juntos para las decenas; DEFROST continúa para las unidades. Para 36: tres conjuntos y tres destellos adicionales.", system="Cassette/techo-suelo", scope="indoor"),
    variant("LED2 y LED5 en conductos VRF", "PCB interior sin display, LED2 y LED5 visibles.", "UNITARY", "89", "Leer la cifra en placa.", "LED2 indica decenas y LED5 unidades. Cuente varios ciclos antes de cortar tensión.", system="Conductos VRF", scope="indoor"),
])
add_topic("diagnostic_access", "wired-controller-check-modes", "Mandos cableados HYXE: alarma, Check y Test", "La aplicación los distingue por aspecto y funciones, no obliga a escribir el modelo.", [
    variant("HYXE-G01H — alarma directa", "Mando cableado con dirección interior, dirección de sistema y código en LCD.", "CTRL", "34-45", "Leer la unidad exacta.", "Ante anomalía parpadea la luz de funcionamiento y la LCD muestra dirección interior, sistema y alarma.", system="HYXE-G01H", scope="controller", controller_data=controller("wired", "remote control switch", "1 par / 2 conductores", "sin polaridad indicada en esta ficha", "alimentado por la unidad interior", "REMOCON")),
    variant("HYXE-F01H — Check 1 y Check 2", "Mando cableado básico con tecla CHECK.", "CTRL", "17-34", "Consultar estado y diagnóstico.", "El manual separa Check Mode 1 y 2, autocomprobación de PCB y Test Run. Anote la pantalla antes de salir.", system="HYXE-F01H", scope="controller"),
    variant("HYXE-J01H/M01H — servicio y ajustes", "Mando con menús de servicio y selección de unidad.", "CTRL", "35-71", "Acceder a la unidad del grupo.", "Permite elegir dirección, revisar alarma, ejecutar Test Run y modificar ajustes de servicio documentados.", system="HYXE-J01H/M01H", scope="controller"),
])
add_topic("history_reset", "vrf-outdoor-history", "Exterior VRF: 15 alarmas, reintentos y control", "El historial conserva más que el código principal.", [
    variant("Recorrer no01 a no15", "PCB exterior en Check Mode con PSW2/PSW4.", "HIFLEXI", "108-110", "Ver la alarma más reciente y las anteriores.", "no01 es el evento más reciente y no15 el más antiguo. El registro puede incluir exterior, compresor, fan controller y tiempo acumulado.", system="Hi-FLEXi S", scope="outdoor"),
    variant("Distinguir AC, d1 y c1", "Historial muestra prefijo junto al código.", "HIFLEXI", "108-110", "No tratar un reintento como alarma permanente.", "AC es alarma; d1 un paro de reintento; c1 un reinicio de microcontrolador. El significado cambia aunque la cifra coincida.", system="Hi-FLEXi S", scope="outdoor"),
    variant("Borrar con PSW1 + PSW3", "Historial ya visible en la placa.", "HIFLEXI", "110", "Limpiar solo después de documentar.", "Mantenga PSW1 y PSW3 durante cinco segundos para borrar todos los registros.", system="Hi-FLEXi S", scope="outdoor"),
])
add_topic("history_reset", "controller-central-history", "Mando y control central: historial y borrado", "La unidad, la hora y el orden ayudan a encontrar fallos intermitentes.", [
    variant("Control central táctil", "Pantalla de Service Menu con Alarm History.", "CTRL", "174-186", "Ver hora, unidad y código.", "El historial registra alarmas de climatización y del controlador; Delete History borra todos tras confirmación.", system="HYJM-S01H", scope="controller"),
    variant("Antes de borrar", "Cualquier mando o central con varios eventos.", "CTRL", "174-186", "Conservar evidencia.", "Anote ciclo frigorífico, dirección interior, código y momento. Compruebe si hay varias unidades con la misma causa.", system="Control central", scope="controller"),
])
add_topic("service_modes", "vrf-test-run", "Hi-FLEXi: Test Run completo", "El modo de prueba no anula las protecciones.", [
    variant("Desde mando: MODE + CHECK", "Direcciones, alimentación y válvulas ya verificadas.", "HIFLEXI", "102-104", "Probar interiores una a una.", "Mantenga MODE y CHECK al menos tres segundos. La regulación de temperatura queda anulada, pero las protecciones siguen activas.", system="Hi-FLEXi S", scope="controller", steps=[
        step(1, "Abra completamente las válvulas y confirme fases, direcciones y comunicación.", phase="prepare", warning="warning"),
        step(2, "Mantenga MODE y CHECK durante al menos tres segundos."),
        step(3, "Ejecute las interiores secuencialmente y verifique tubería/ciclo correspondiente."),
        step(4, "Finalice con RUN/STOP o espere el límite documentado de dos horas.", phase="verify"),
    ]),
    variant("Desde la placa exterior", "PCB principal con PSW y siete segmentos.", "HIFLEXI", "301-306", "Probar sin una demanda normal.", "Seleccione el modo de prueba exterior, vigile el display y restaure la selección al terminar.", system="Hi-FLEXi S", scope="outdoor"),
    variant("Qué sigue vigilando", "Test Run activo y consigna de habitación ignorada.", "HIFLEXI", "103-104", "Interpretar una parada durante la prueba.", "Siguen activas alta/baja presión, corriente, descarga, inverter, ventiladores, comunicaciones y sensores.", system="Hi-FLEXi S"),
])
add_topic("service_modes", "vrf-emergency-operation", "VRF: funcionamiento de emergencia por compresor", "Permite servicio temporal, no una reparación permanente.", [
    variant("Desde mando", "Alarma compatible y todos los mandos/interiores H-NET.", "HIFLEXI", "111-116", "Excluir el compresor fallado.", "El sistema puede continuar con capacidad reducida; el manual limita el uso a ocho horas y no lo permite para PCB inverter o fan controller.", system="Hi-FLEXi S", scope="controller"),
    variant("Desde PCB exterior", "Compresor identificado mediante historial y selectores.", "HIFLEXI", "111-116", "Excluir físicamente la unidad fallada.", "Configure solo la combinación indicada y restaure los switches después del servicio.", system="Hi-FLEXi S", scope="outdoor"),
    variant("Limitaciones durante emergencia", "El equipo funciona con un compresor excluido.", "HIFLEXI", "111-116", "No confundir nuevos códigos con otra avería.", "La frecuencia no se controla normalmente; pueden aparecer 07, 43, 44, 45 o 47 y la capacidad será menor.", system="Hi-FLEXi S"),
])
add_topic("service_modes", "wireless-test-run", "Test Run desde mando inalámbrico", "Método útil en interiores con receptor.", [
    variant("SET + OFF TIMER", "Mando inalámbrico/receptor HYRE compatible.", "CTRL", "92-103", "Entrar en modo de prueba.", "Con la instalación preparada, use SET y OFF TIMER; el receptor enciende RUN rojo y TIMER verde parpadea.", system="HYRE-T/V/X", scope="controller"),
    variant("Finalizar prueba", "Test Run inalámbrico activo.", "CTRL", "92-103", "Volver a operación normal.", "Pulse RUN/STOP o espere dos horas; al finalizar deben apagarse RUN y TIMER.", system="HYRE-T/V/X", scope="controller"),
])
add_topic("configuration", "vrf-dip-addressing", "DIP, selectores y direccionamiento H-NET", "La posición correcta depende del rol y del ciclo frigorífico.", [
    variant("Exterior principal y subordinadas", "Dos o más exteriores combinadas.", "HIFLEXI", "97-101, 105-107", "Definir rol y número de unidad.", "Configure dirección exterior, número de ciclo y una sola principal; 0b, 0C, 3b y 3d indican errores de esta capa.", system="Hi-FLEXi S", scope="outdoor"),
    variant("Resistencia terminal", "Extremo de una red H-NET.", "HIFLEXI", "97-101", "Evitar red abierta o múltiples terminadores.", "La resistencia terminal se define por DIP; no copie la posición de otra exterior sin entender su lugar en la red.", system="Hi-FLEXi S"),
    variant("Direcciones interiores únicas", "Hasta 64 direcciones en el ciclo.", "HIFLEXI", "105-107", "Evitar 35 y b1.", "Compruebe que no se repitan dirección interior ni ciclo frigorífico y que ninguna supere el rango.", system="Hi-FLEXi S"),
])
add_topic("configuration", "controller-central-programming", "Programación desde mando y control central", "Funciones, grupos, restricciones y calendario.", [
    variant("HYXE: selección de unidad y ajuste de servicio", "Mando cableado conectado a un grupo.", "CTRL", "17-71", "Modificar solo la unidad elegida.", "Seleccione dirección, función y valor; registre el ajuste original y confirme si requiere cortar alimentación.", system="HYXE", scope="controller"),
    variant("Central HYJE/HYJM", "Control de 16 grupos o más con menú de servicio.", "CTRL", "119-186", "Crear grupos y permisos.", "Permite registrar grupos, maestro, prohibiciones, horario y salidas externas. Una dirección duplicada altera toda la supervisión.", system="Central control", scope="controller"),
    variant("SW3 en receptor inalámbrico", "Receptor con DIP interno.", "CTRL", "92-103", "Activar opciones compatibles.", "Desconecte alimentación antes de cambiar SW3 y documente la posición original.", system="HYRE receiver", scope="indoor"),
])
add_topic("controllers_buses", "controller-family-map", "Mapa de mandos Hisense y cómo reconocerlos", "Cableado, capacidad y menús cambian entre generaciones.", [
    variant("HYXE-F/G/J/M — cableados", "Mando fijo con LCD y cable de control.", "CTRL", "1-8, 19-20", "Elegir el procedimiento correcto.", "Los modelos ofrecen Check, Test Run, alarma y hasta 16 interiores según versión. Usan un par de 0,3–0,75 mm²; si se superan 30 m se exige par trenzado apantallado y se admiten hasta 500 m.", system="HYXE", scope="controller", controller_data=controller("wired", "remote control switch", "1 par / 2 conductores", "consultar variante", "alimentado por unidad interior", "REMOCON")),
    variant("HYRE-T/V/X — inalámbricos con receptor", "Mando portátil y receptor en interior.", "CTRL", "1-8, 92-103", "Usar self-check y Test Run.", "El enlace radio es de unos 5 m; el receptor se integra en la red de control de la interior.", system="HYRE", scope="controller", controller_data=controller("wireless", "IR + receiver", "receptor cableado", "según receptor", "alimentación desde interior")),
    variant("HYJE/HYJM/Hi-Dom — centrales", "Panel mural o servidor que muestra varias unidades.", "CTRL", "119-224", "Localizar dirección y ciclo.", "La central puede manejar grupos, historial, restricciones y servicios; la red total documentada llega a 1.000 m en ciertas centrales.", system="Central control", scope="controller"),
])
add_topic("controllers_buses", "hnet-transmission", "H-NET: cable, topología y alimentación", "Separar siempre transmisión de potencia.", [
    variant("TB2 terminales 1–2", "Exterior VRF con bornero de transmisión.", "HIFLEXI", "89-96", "Conectar ciclo y red correctos.", "Use par trenzado apantallado de dos conductores; no emplee tres o más y no conecte tensión de red a TB2.", system="Hi-FLEXi S"),
    variant("Separación respecto a potencia", "Transmisión y alimentación recorren la instalación.", "HIFLEXI", "89-96", "Evitar perturbaciones.", "Mantenga al menos 50 mm respecto a potencia y, cuando procede, 5 m respecto al cableado de otros equipos.", system="Hi-FLEXi S"),
    variant("Fallo de mando frente a H-NET", "FE/65 en comercial o 03 en VRF.", "FLOOR", "61-85", "Aislar qué bus ha caído.", "FE/65 describen enlace mando–interior; 03 describe interior–exterior. No son la misma línea ni se miden igual.", system="Hisense varias familias", scope="controller"),
])
add_topic("controllers_buses", "controller-power-up", "Qué hace el mando al alimentar", "Una inicialización breve no es necesariamente avería.", [
    variant("Mando cableado y adquisición", "Se repone tensión a una red H-NET.", "CTRL", "19-20", "Esperar antes de diagnosticar.", "Una parte de la LCD puede encenderse inmediatamente y no es avería. El auto-addressing tarda unos tres minutos y puede necesitar cinco; si aparece 00 durante Test Run, la adquisición aún puede estar en curso.", system="HYXE", scope="controller"),
    variant("Control central", "Se alimenta después de probar los aires acondicionados.", "CTRL", "119-186", "Evitar mapas incompletos.", "El manual pide completar cableado y Test Run del sistema antes de encender/programar la central.", system="Central control", scope="controller"),
])
add_topic("drainage_overflow", "float-drain-protection", "Cassette/VRF: boya, bomba y códigos 01/51", "El mismo síntoma puede aparecer como 01 VRF o 51 comercial antiguo.", [
    variant("01 — boya en Hi-FLEXi", "Mando VRF muestra 01 y dirección interior.", "HIFLEXI", "124-126", "Localizar la interior afectada.", "Nivel alto, tubería, bandeja o flotador activan la protección. La unidad interior afectada se detiene.", system="Hi-FLEXi S", scope="indoor"),
    variant("51 — protección de drenaje comercial", "Display/panel antiguo muestra 51.", "FLOOR", "79", "Distinguir agua, bomba y señal.", "Compruebe obstrucción, altura de tubo, bomba, interruptor de nivel, cable y placa.", system="Cassette/conductos antiguo", scope="indoor"),
    variant("Prueba de drenaje en instalación", "Cassette recién montado sin código.", "CASSETTE", "16-18", "Comprobar antes de cerrar techo.", "Añada agua de prueba, verifique evacuación, pendiente y aislamiento; no dé por válido solo porque la bomba suena.", system="Cassette inverter", scope="indoor"),
])
add_topic("drainage_overflow", "drain-behavior-cooling-heating", "Qué ocurre en frío, calor y parada", "La boya atascada puede generar síntomas diferentes según el modo.", [
    variant("Frío o deshumidificación", "Hay producción de condensados y bomba prevista.", "FLOOR", "79-85", "Interpretar una parada con bomba activa.", "El control detiene la operación protegida por nivel alto mientras intenta evacuar; si la boya no baja, mantiene el fallo.", system="Cassette/conductos", scope="indoor"),
    variant("Calefacción o parada", "No debería generarse condensado interior, pero la boya está arriba.", "FLOOR", "79-85", "Detectar flotador trabado.", "Una boya mecánicamente bloqueada sigue informando nivel alto aunque el modo no produzca agua; compruebe el flotador antes de cambiar la placa.", system="Cassette/conductos", scope="indoor"),
])
add_topic("commissioning", "vrf-auto-addressing", "VRF: auto-addressing y reconocimiento de unidades", "La placa exterior muestra fallos antes de que el sistema pueda operar.", [
    variant("Comprobación simple en siete segmentos", "Instalación nueva en fase de adquisición.", "HIFLEXI", "105-107", "Detectar unidades sin alimentación o direcciones repetidas.", "Durante auto-addressing la exterior puede mostrar 03 por transmisión o 35 por dirección interior duplicada.", system="Hi-FLEXi S", scope="outdoor"),
    variant("Número de interiores incorrecto", "El display no coincide con la instalación.", "HIFLEXI", "105-107", "Evitar Test Run con mapa incompleto.", "Revise alimentación de todas las interiores, cable de transmisión, ciclo correcto y direcciones antes de repetir la adquisición.", system="Hi-FLEXi S"),
    variant("Dos mandos principal/subordinado", "Una interior tiene dos mandos.", "HIFLEXI", "102-104", "Ejecutar la prueba desde el correcto.", "El manual indica realizar primero el Test Run desde el mando principal.", system="Hi-FLEXi S", scope="controller"),
])
add_topic("commissioning", "pre-start-checks", "Antes del primer arranque", "Válvulas, fases y precalentamiento siguen siendo obligatorios.", [
    variant("Válvulas de servicio totalmente abiertas", "Sistema recién instalado o reparado.", "HIFLEXI", "102-104", "Evitar daños y alarmas de presión.", "El manual advierte que un Test Run con válvulas cerradas puede dañar el equipo.", system="Hi-FLEXi S", scope="outdoor"),
    variant("Fases y alimentación", "Exterior trifásica antes de Test Run.", "HIFLEXI", "102-104", "Evitar 05/06.", "Compruebe secuencia, ausencia de fase y tensión. Con fase incorrecta la unidad no funciona y el mando muestra 05.", system="Hi-FLEXi S", scope="outdoor"),
    variant("Precalentar aceite", "Sistema sin tensión durante un periodo prolongado.", "CTRL", "precauciones iniciales", "Proteger el compresor.", "Alimente el sistema al menos 12 horas antes del arranque tras una parada prolongada.", system="VRF/comercial", scope="outdoor"),
])
add_topic("multisplit", "multi-code-location", "Multisplit: interior, mando y display exterior", "No todos los fallos exteriores llegan con el mismo número a la interior.", [
    variant("HIGH POWER o emergencia", "Interior con display de temperatura.", "MULTI", "149", "Llevar el código exterior a una pantalla accesible.", "La consulta muestra errores interior/exterior en el área de temperatura; anote también qué interior realizó la consulta.", system="Multisplit AMW", scope="indoor"),
    variant("Tubo digital de exterior", "PCB exterior accesible y alimentada.", "MULTI", "149-153", "Identificar sonda o puerto.", "Los códigos 12–19 separan líquido/gas de puertos A–D. No sustituya una sonda sin verificar qué puerto representa.", system="Multisplit AMW", scope="outdoor"),
])
add_topic("multisplit", "multi-operation-scope", "Alcance de averías en multisplit", "Una rama puede fallar sin que todas las interiores se comporten igual.", [
    variant("Fallo de sonda de un puerto", "Código 12–19 en exterior.", "MULTI", "149-153", "Localizar la conexión afectada.", "La exterior identifica el puerto; compruebe si las demás ramas continúan y anote el modo de cada interior.", system="Multisplit AMW", scope="outdoor"),
    variant("Fallo común de IPM o alimentación", "Código 5, protección de corriente o exterior parada.", "MULTI", "149-153", "Reconocer causa común.", "Al afectar al generador común, todas las interiores asociadas pierden capacidad aunque algunas conserven display o ventilación.", system="Multisplit AMW", scope="system"),
    variant("Sistemas simultáneos comerciales", "Dos, tres o cuatro interiores comparten una exterior.", "CAT24", "210-214", "Evitar demandas incompatibles.", "Las interiores simultáneas deben ser del mismo tipo y operar con el mismo modo, temperatura y velocidad de ventilación.", system="Twin/Triple/Quad", scope="system"),
])
add_topic("vrf_network", "heat-recovery-switch-box", "Recuperación de calor y cajas selectoras", "Los códigos C1–C4 describen la arquitectura, no un sensor.", [
    variant("C1: cajas en serie", "Una interior queda detrás de dos switch boxes.", "HIFLEXI", "124-125", "Corregir topología.", "El manual no permite dos cajas selectoras entre exterior e interior.", system="Hi-FLEXi S Heat Recovery"),
    variant("C2: demasiadas interiores", "El puerto o la caja supera su límite.", "HIFLEXI", "124-125", "Repartir conexiones.", "Compare la cantidad real con el límite de la caja y su configuración.", system="Hi-FLEXi S Heat Recovery"),
    variant("C3/C4: ciclo o puerto incorrectos", "Interior de otro ciclo o puerto declarado sin uso.", "HIFLEXI", "124-125", "Corregir tubería, transmisión y DIP.", "La tubería y la transmisión deben pertenecer al mismo ciclo; cada puerto debe declararse usado/no usado correctamente.", system="Hi-FLEXi S Heat Recovery"),
])
add_topic("vrf_network", "vrf-stop-scope", "VRF: parada de unidad, exterior o ciclo", "Cada interpretación indica el alcance; no se deduce solo del código.", [
    variant("Fallo interior o mando", "01, 11–19 con dirección interior.", "HIFLEXI", "124-185", "Mantener operativas otras zonas cuando procede.", "Normalmente se detiene la interior afectada; la exterior y otras interiores pueden continuar si la protección común lo permite.", system="Hi-FLEXi S"),
    variant("Fallo de ciclo o exterior", "02–08, 43–57, EE.", "HIFLEXI", "124-185", "Reconocer una parada común.", "Protecciones de presión, compresor, inverter o comunicación exterior detienen el ciclo frigorífico afectado.", system="Hi-FLEXi S"),
    variant("Emergencia degradada", "Compresor excluido mediante procedimiento autorizado.", "HIFLEXI", "111-116", "Mantener servicio temporal.", "Puede seguir con capacidad limitada durante un máximo de ocho horas, solo con las condiciones del manual.", system="Hi-FLEXi S"),
])
add_topic("vrf_network", "vrf-protection-controls", "Códigos P: control preventivo, no alarma final", "El display explica por qué baja frecuencia o reintenta.", [
    variant("P01/P02/P06/P09/P0d — presiones", "Display exterior muestra P seguido de dos caracteres.", "HIFLEXI", "193-195", "Interpretar limitación hidráulica.", "El control protege relación, alta o baja presión antes del disparo de una alarma.", system="Hi-FLEXi S", scope="outdoor"),
    variant("P03/P04/P05 — inverter y descarga", "Capacidad reducida con display P.", "HIFLEXI", "193-195", "Separar protección de avería permanente.", "Compruebe corriente, disipador y descarga; si desaparece al normalizarse, era control preventivo.", system="Hi-FLEXi S", scope="outdoor"),
    variant("Pc1–Pc5", "El display usa c en lugar de 0 en determinadas degradaciones.", "HIFLEXI", "193-195", "Reconocer operación degradada.", "Pc1 a Pc5 sustituyen P01 a P05 cuando está activa la lógica de degeneración.", system="Hi-FLEXi S", scope="outdoor"),
])
add_topic("component_checks", "sensor-inputs", "Sondas y entradas analógicas", "La ficha combina código, ubicación, umbral y método.", [
    variant("Sondas VRF interior/exterior", "Códigos 11–17 y 22–25.", "HIFLEXI", "124-185", "Separar circuito abierto/corto y montaje.", "En varias sondas el manual usa menos de 0,24 kΩ o más de 840 kΩ como condición de fallo; confirme la página exacta del punto.", system="Hi-FLEXi S"),
    variant("Sensores de presión", "21/29 o 44 en familia antigua.", "HIFLEXI", "124-185", "Comparar presión real y tensión.", "En Hi-FLEXi el sensor se considera anormal por señal ≤0,1 V o ≥4,9 V; compare con manómetros.", system="Hi-FLEXi S", scope="outdoor"),
    variant("Sondas por puerto multisplit", "Códigos 12–19 en display exterior.", "MULTI", "149-153", "No intercambiar A, B, C o D.", "Identifique físicamente puerto, tubo líquido/gas y conector antes de medir.", system="Multisplit AMW", scope="outdoor"),
])
add_topic("component_checks", "fan-motor-checks", "Ventiladores interiores y exteriores", "Los códigos 19, 48/49, 57/5b y E4 corresponden a capas distintas.", [
    variant("Interior VRF — 19", "Mando VRF con dirección interior.", "HIFLEXI", "153-155", "Verificar velocidad real.", "La lógica registra menos de 70 rpm durante 5 s, tres veces en 30 min; revise bloqueo, motor, señal y PCB.", system="Hi-FLEXi S", scope="indoor"),
    variant("Interior residencial — E4", "Display alfanumérico de split.", "UNITARY", "49-65", "Distinguir motor y placa.", "Revise conexión, bloqueo, motor y PCB interior. No sustituya el motor sin comprobar alimentación/realimentación.", system="Split DC inverter", scope="indoor"),
    variant("Exterior VRF — 57/5A/5b/5C", "Display de la exterior principal.", "HIFLEXI", "124-185", "Separar motor, driver y disipador.", "El controlador de ventilador tiene protecciones y sensores propios; consulte el historial para el número de fan controller.", system="Hi-FLEXi S", scope="outdoor"),
])
add_topic("component_checks", "compressor-inverter", "Compresor, inverter y bloqueo EE", "El historial permite saber qué compresor o placa provocó la parada.", [
    variant("48/51/53/54/55", "Alarma exterior con número de compresor/inverter en historial.", "HIFLEXI", "124-185", "Separar potencia, driver y compresor.", "Compruebe red, bus DC, disipador, U-V-W, aislamiento y cableado antes de sustituir PCB.", system="Hi-FLEXi S", scope="outdoor"),
    variant("EE tras tres alarmas", "El mando muestra EE y no permite reset normal.", "HIFLEXI", "125", "Buscar la causa repetida.", "Revise historial: 02, 07, 08, 43–45 o 47 se repitió tres veces en seis horas.", system="Hi-FLEXi S", scope="system"),
    variant("45 en comercial antiguo", "Display exterior numérico muestra 45.", "FLOOR", "73-75", "Consultar el driver secundario.", "45 es una cabecera IPM; el código o LED de la placa driver aporta la causa concreta.", system="Comercial inverter", scope="outdoor"),
])
add_topic("component_checks", "valves-pressure-cycle", "EEV, válvula de cuatro vías y circuito frigorífico", "Las presiones y temperaturas deben confirmar el componente.", [
    variant("EEV abierta o cerrada", "07/08, 43–47 o sondas de puerto.", "HIFLEXI", "124-185", "Distinguir bloqueo y carga.", "Compare apertura, sobrecalentamiento, presiones y respuesta térmica; un conector suelto puede simular bloqueo.", system="Hi-FLEXi S"),
    variant("Cuatro vías", "No cambia correctamente entre frío y calor.", "FLOOR", "76-85", "Separar bobina y cuerpo.", "Compruebe alimentación de bobina, movimiento térmico, carga y presiones antes de sustituir la válvula.", system="Comercial/VRF"),
    variant("Alta y baja presión", "02, 43–47 o 14/15 antiguo.", "HIFLEXI", "124-185", "Aplicar el código de la familia.", "Válvulas cerradas, carga, intercambiadores, ventiladores y EEV pueden producir la misma protección.", system="Hisense varias familias"),
])
add_topic("technical_values", "quick-electrical-values", "Valores eléctricos y de bus", "Solo se muestran con familia y punto de medida.", [
    variant("H-NET transmisión", "TB2 1–2 en exterior VRF.", "HIFLEXI", "89-96", "Comprobar continuidad y topología.", "Par trenzado apantallado de dos conductores; nunca aplicar tensión de red a TB2.", system="Hi-FLEXi S"),
    variant("Mando cableado", "HYXE conectado a la unidad interior.", "CTRL", "1-8, 17-71", "Reconocer cable y alcance.", "El manual documenta hasta 500 m de cable total en varios mandos HYXE y hasta 16 interiores según versión.", system="HYXE", scope="controller"),
    variant("Control central", "HYJE/HYJM/Hi-Dom en H-NET.", "CTRL", "119-224", "Dimensionar red.", "Algunos controladores centrales documentan hasta 1.000 m; verifique la versión antes de aplicar.", system="Central control", scope="controller"),
])
add_topic("technical_values", "protection-thresholds", "Umbrales y tiempos de detección", "Ayudan a saber por qué aparece el código.", [
    variant("Comunicación 03", "Interior–exterior VRF.", "HIFLEXI", "126-132", "Distinguir pérdida y fallo desde arranque.", "Tras comunicación normal, la pérdida se evalúa durante tres minutos; desde el primer arranque se indica después de 30 segundos.", system="Hi-FLEXi S"),
    variant("Ventilador interior 19", "Motor gira por debajo de la velocidad mínima.", "HIFLEXI", "153-155", "Confirmar que no es un bloqueo momentáneo.", "Menos de 70 rpm durante cinco segundos, tres veces dentro de 30 minutos.", system="Hi-FLEXi S"),
    variant("Sensores de presión", "21 o 29.", "HIFLEXI", "156-170", "Validar señal eléctrica.", "Señal ≤0,1 V o ≥4,9 V se considera anormal.", system="Hi-FLEXi S"),
    variant("Protecciones P06/P09/P0d", "Display de control preventivo.", "HIFLEXI", "193-195", "Comparar presión.", "P06: Ps ≤0,2 MPa; P09: Pd ≤1,5 MPa; P0d: Ps ≥1,5 MPa.", system="Hi-FLEXi S"),
])
add_topic("normal_states", "normal-delays-preheat", "Retardos y precalentamiento normales", "Evitan arranques repetidos o retorno de líquido.", [
    variant("Retardo de tres minutos", "Compresor acaba de parar o vuelve la tensión.", "FLOOR", "60", "Esperar antes de diagnosticar.", "El compresor no puede reiniciar durante tres minutos mientras se equilibran presiones.", system="Comercial"),
    variant("Precalentamiento del compresor", "Frío exterior o parada prolongada.", "UNITARY", "protecciones exteriores", "No confundir pilotos con avería.", "El piloto exterior puede indicar precalentamiento como modo normal en tiempo frío.", system="Split DC inverter", scope="outdoor"),
    variant("Doce horas antes del arranque", "VRF o comercial sin tensión durante mucho tiempo.", "CTRL", "precauciones iniciales", "Proteger aceite y compresor.", "Mantenga alimentación previa durante 12 horas.", system="VRF/comercial", scope="outdoor"),
])
add_topic("normal_states", "defrost-oil-return", "Desescarche y recuperación de aceite", "Pueden detener ventiladores o modificar válvulas sin generar avería.", [
    variant("Desescarche en calefacción", "Batería exterior con escarcha y display de estado.", "HIFLEXI", "54, 266-288", "Reconocer la secuencia.", "El ventilador exterior se detiene durante el desescarche; la interior puede mostrar DEFROST y evita aire frío.", system="Hi-FLEXi S"),
    variant("Recuperación de aceite VRF", "Cambio temporal de frecuencia y válvulas.", "HIFLEXI", "266-288", "No interrumpir una secuencia normal.", "La recuperación distribuye aceite por el circuito y puede alterar temporalmente el confort.", system="Hi-FLEXi S"),
    variant("P01–P0d como protección temporal", "Display exterior muestra P y luego recupera.", "HIFLEXI", "193-195", "No borrar una alarma inexistente.", "Son controles de protección/reintento; investigue si se repiten o evolucionan a una alarma AC.", system="Hi-FLEXi S", scope="outdoor"),
])
add_topic("service_tools_boards", "hi-checker", "Hi-Checker: herramienta oficial de servicio", "Monitoriza variables y ayuda a registrar la puesta en marcha.", [
    variant("Conexión directa al ordenador", "Adaptador Hi-Checker disponible y sistema compatible.", "CAT24", "24-25", "Leer datos en tiempo real.", "Conexión plug and play para que el técnico acceda a información de funcionamiento.", system="Hisense HVAC"),
    variant("Hotspot o tarjeta SD", "No es posible dejar un ordenador junto a la unidad.", "CAT24", "24-25", "Registrar a distancia.", "Puede trabajar mediante hotspot temporal del móvil o guardar datos en tarjeta SD, según versión.", system="Hisense HVAC"),
    variant("Datos antes y después de reparar", "Avería intermitente o puesta en marcha.", "CAT24", "24-25", "Comparar condiciones.", "Guarde presiones, temperaturas, corriente, frecuencia y estados antes de borrar el historial.", system="Hisense HVAC"),
])
add_topic("service_tools_boards", "board-replacement", "Después de sustituir una PCB", "Una placa nueva puede necesitar identidad, dirección y DIP.", [
    variant("PCB exterior VRF", "0b/0C/31/3b/3d tras cambiar placa.", "HIFLEXI", "97-110", "Restaurar configuración.", "Copie dirección exterior, ciclo, rol principal/subordinada, capacidad y terminación antes del Test Run.", system="Hi-FLEXi S", scope="outdoor"),
    variant("PCB interior o display", "EA/ER/FE/65 después de sustitución.", "FLOOR", "61-85", "No confundir placa y cable.", "Compruebe alimentación, conector, mando, dirección y comunicación antes de declarar otra PCB defectuosa.", system="Comercial", scope="indoor"),
    variant("EEPROM 4/E11/55", "Código de memoria o placa.", "UNITARY", "49-65", "Separar componente y configuración.", "Reasiente la memoria si es extraíble, confirme referencia/capacidad y restaure ajustes.", system="Hisense varias familias"),
])
add_topic("system_architecture", "recognize-hisense-family", "Reconocer la familia antes de buscar", "La aplicación usa pistas visibles en vez de exigir un modelo.", [
    variant("Split residencial", "Mando inalámbrico, display interior alfanumérico E y una exterior.", "UNITARY", "49-65", "Usar E4/E8/E36 y consulta SLEEP.", "No aplique los números 01–EE de H-NET.", system="Split DC inverter"),
    variant("Comercial antiguo", "Cassette, conductos, suelo o techo-suelo; mando, RUN/DEFROST o LED2 exterior.", "FLOOR", "61-85", "Elegir conteo o cifra directa.", "La misma máquina puede mostrar un número en mando, panel interior y exterior.", system="Unitario comercial"),
    variant("Multisplit", "Varias interiores y puertos A–D, display exterior numérico.", "MULTI", "149-153", "Localizar la rama.", "Use HIGH POWER/emergencia para consulta y confirme la cifra en la PCB exterior.", system="Multisplit AMW"),
    variant("Hi-FLEXi VRF", "Varias exteriores, H-NET, PSW, SEG1/SEG2 y posibles switch boxes.", "HIFLEXI", "97-195", "Usar dirección, historial y alcance.", "Los códigos incluyen unidad, ciclo, compresor/fan controller, reintentos d1 y controles P.", system="Hi-FLEXi S"),
])
add_topic("system_architecture", "public-information-rule", "Cómo está organizada la información", "Toda la profundidad queda disponible sin saturar la pantalla.", [
    variant("Marca → categoría → tema → variante", "Menú principal de Super Técnico.", "PORTAL", "recursos técnicos", "Llegar rápido al procedimiento.", "Los códigos están en lista desplegable; las interpretaciones permanecen cerradas hasta que el técnico elige.", system="Super Técnico"),
    variant("Fuente, página y familia", "Bloque Fuentes dentro de cada ficha.", "PORTAL", "recursos técnicos", "Comprobar trazabilidad.", "Cada dato técnico conserva documento y página. Los modelos se usan internamente, pero la búsqueda muestra rasgos observables.", system="Super Técnico"),
])


def build_topics() -> list[dict[str, Any]]:
    result, variant_id = [], 1
    for topic_id, spec in enumerate(TOPICS, start=1):
        cat = CATEGORY_BY_SLUG[spec["category"]]
        rows = []
        for sort_order, item in enumerate(spec["variants"], start=1):
            rows.append({
                **item, "id": variant_id, "topic_id": topic_id,
                "sort_order": sort_order, "visible": 1,
            })
            variant_id += 1
        result.append({
            "id": topic_id, "brand_id": BRAND_ID, "category_id": cat["id"],
            "slug": spec["slug"], "title": spec["title"], "summary": spec["summary"],
            "active": 1, "category": cat, "variants": rows,
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
        parts = [row["code_display"], row["short_label"], *row["aliases"], *row["tags"]]
        for interpretation in detail["interpretations"]:
            parts.extend([interpretation["title"], interpretation["description"]])
            parts.extend(item["body"] for item in interpretation["info_items"])
            for context in interpretation["indication_contexts"]:
                parts.extend(str(context.get(key, "")) for key in (
                    "display_location", "family_hint", "relationship",
                ))
        entries.append({
            "type": "error", "id": row["id"], "code": row["code_display"],
            "title": row["short_label"], "subtitle": f'{row["interpretation_count"]} interpretación(es)',
            "haystack": normalize(" ".join(parts)),
        })
    for topic in topics:
        for row in topic["variants"]:
            parts = [
                topic["title"], topic["summary"], row["title"], row["recognition"],
                row["purpose"], row["summary"], row["system_type"],
            ]
            parts.extend(item["body"] for item in row["sections"])
            parts.extend(
                item["instruction"] + " " + (item.get("expected_result") or "")
                for item in row["steps"]
            )
            for pattern in row.get("led_patterns", []):
                parts.extend([
                    pattern.get("code_display", ""), pattern.get("relationship", ""),
                    pattern.get("family_hint", ""), pattern.get("counting_rule", ""),
                    pattern.get("cycle_note", ""),
                ])
                for led in pattern.get("led_indicators", []):
                    parts.extend([led.get("label", ""), led.get("color", ""), led.get("state", "")])
            if row["controller"]:
                parts.extend(str(value or "") for value in row["controller"].values())
            entries.append({
                "type": "variant", "id": row["id"], "topic_id": topic["id"],
                "title": row["title"], "subtitle": topic["title"],
                "haystack": normalize(" ".join(parts)),
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
    write_json(
        WEB_DIR / "variant_map.json",
        {str(row["id"]): topic["id"] for topic in topics for row in topic["variants"]},
    )
    by_category: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for topic in topics:
        by_category[topic["category_id"]].append({
            "id": topic["id"], "slug": topic["slug"], "title": topic["title"],
            "summary": topic["summary"], "active": 1,
            "variant_count": len(topic["variants"]),
        })
    categories = [{
        "id": ident, "slug": slug, "name": name, "description": description,
        "sort_order": ident * 10, "active": 1, "topics": by_category[ident],
    } for ident, slug, name, description in CATEGORIES]
    write_json(WEB_DIR / "navigation.json", {
        "metadata": {
            "schema_name": "Super Tecnico",
            "navigation_model": "brand_category_topic_variant",
            "schema_version": "2.3.0", "data_version": "1.0.0",
            "last_update_utc": now, "reference_brand": "Hisense",
            "verification_warning": (
                "Completa respecto al corpus Hisense Referencia V1. Confirme familia, "
                "punto de lectura y arquitectura: el mismo número puede cambiar entre "
                "mando, display interior, placa exterior, multisplit y H-NET."
            ),
        },
        "categories": categories,
    })
    write_json(WEB_DIR / "sources.json", [{
        "id": ident, "brand_id": BRAND_ID, "title": row["title"],
        "document_ref": row["document_ref"], "document_type": row["type"],
        "publication_date": row["year"], "language": "es/en",
        "source_url": row["source_url"], "status": "reviewed",
        "notes": "Fuente revisada para Hisense Referencia V1.",
    } for ident, row in enumerate(SOURCES.values(), start=1)])
    write_json(WEB_DIR / "coverage.json", [{
        "id": ident, "brand_id": BRAND_ID, "area_slug": slug, "area_name": name,
        "equipment_scope": "Hisense — split, comercial, cassette, multisplit, simultáneo y Hi-FLEXi VRF",
        "coverage_status": "reference_v1", "source_count": len(SOURCES),
        "notes": description, "last_reviewed": "2026-07-29",
    } for ident, slug, name, description in CATEGORIES])
    counts = {
        "categories": len(CATEGORIES), "topics": len(topics),
        "variants": sum(len(topic["variants"]) for topic in topics),
        "errors": len(error_index), "search_entries": len(search_entries),
    }
    write_json(BRAND_DIR / "brand.json", {
        "slug": "hisense", "name": "Hisense", "display_name": "Hisense",
        "enabled": True, "web_data": "web", "media": "media",
        "publish_media": False, "static_site": True,
        "schema_version": "2.3.0", "data_version": "1.0.0",
        "exported_at_utc": now, "counts": counts,
        "notes": (
            "Hisense Referencia V1: split, comercial, cassette, multisplit, "
            "mandos HYXE/HYRE y Hi-FLEXi VRF; códigos separados por pantalla, "
            "procedimientos, buses, drenaje, alcance operativo y tabla exterior de pilotos."
        ),
    })
    return counts


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
