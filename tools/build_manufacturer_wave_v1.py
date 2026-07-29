#!/usr/bin/env python3
"""Construye Hitachi, Sharp, Sanyo histórica y Chigo Referencia V1.

El generador publica únicamente resúmenes técnicos trazables. No copia PDF,
capturas ni bases privadas y conserva separadas las familias y puntos de
lectura cuando un mismo código cambia de significado.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from audit_brand_quality import audit_brand, write as write_quality


ROOT = Path(__file__).resolve().parents[1]


CATEGORIES = [
    ("errors", "Errores y protecciones", "Códigos, significados alternativos y alcance operativo documentado."),
    ("outdoor_diagnostics", "Pilotos y display exterior", "Pilotos, displays de placa y reglas de lectura propias de cada familia."),
    ("diagnostic_access", "Obtención de códigos y subcódigos", "Métodos desde mando, receptor, display, placa o herramienta."),
    ("history_reset", "Historial y borrado", "Consulta de memoria, reinicio y diferencias entre alarma actual e histórica."),
    ("service_modes", "Modos de servicio", "Test Run, marcha forzada, pump down y pruebas de actuadores."),
    ("configuration", "Configuración y programación", "Funciones, DIP, selectores, direcciones y parámetros de placa o mando."),
    ("controllers_buses", "Mandos y buses", "Cableado, comunicación, alimentación, grupos y fallos del propio controlador."),
    ("drainage_overflow", "Drenaje y desbordamiento", "Boya, bomba, tiempos de detección y comportamiento por modo."),
    ("commissioning", "Puesta en marcha", "Comprobaciones previas, direccionamiento, reconocimiento y prueba final."),
    ("multisplit", "Multisplit", "Puertos, conflictos de modo, cableado/tuberías y alcance por unidad."),
    ("vrf_network", "VRF y red", "Red, unidades principales/secundarias, cajas de distribución y funcionamiento degradado."),
    ("component_checks", "Comprobación de componentes", "Sondas, motores, compresor, inverter, válvulas y circuitos de control."),
    ("technical_values", "Valores técnicos", "Tensiones, resistencias, tiempos y umbrales que sí constan en las fuentes."),
    ("normal_states", "Comportamientos normales", "Retardos, desescarche, recuperación de aceite y estados que no son avería."),
    ("service_tools_boards", "Herramientas y placas", "Herramientas de servicio y tareas posteriores a sustituir una placa."),
    ("system_architecture", "Reconocer el sistema", "Pistas visibles para escoger la tabla correcta sin exigir el modelo."),
]


PROFILES = {
    "communication": {
        "causes": ["Cable abierto, cruzado o en cortocircuito", "Una unidad no está alimentada", "Dirección o terminación incorrecta", "Circuito de transmisión defectuoso"],
        "checks": ["Confirmar dónde se leyó el código", "Comprobar alimentación de todas las unidades", "Revisar continuidad, polaridad y terminadores según la familia", "Aislar la red por tramos antes de sustituir una placa"],
        "note": "No extrapolar la tensión ni la topología de un bus a otra familia.",
    },
    "sensor": {
        "causes": ["Sensor abierto o en cortocircuito", "Conector o cable dañados", "Sensor desprendido del punto de medida", "Entrada analógica de placa defectuosa"],
        "checks": ["Medir el sensor aislado", "Comparar con la temperatura real y la curva de esa familia", "Revisar montaje térmico y cableado", "Comparar la lectura de servicio con un instrumento"],
        "note": "La misma denominación de sonda puede usar otra curva en una generación distinta.",
    },
    "fan": {
        "causes": ["Ventilador bloqueado", "Motor o realimentación defectuosos", "Conector o cableado anormal", "Driver o alimentación de placa defectuosos"],
        "checks": ["Comprobar giro libre con alimentación aislada", "Revisar conector y devanados", "Aplicar la secuencia de medida del manual", "Separar fallo de motor y fallo de placa"],
        "note": "No conectar ni desconectar motores DC o inverter con tensión.",
    },
    "drain": {
        "causes": ["Boya atascada", "Desagüe obstruido o con retorno", "Bomba defectuosa", "Entrada de boya o cableado anormales"],
        "checks": ["Comprobar el nivel real de agua", "Verificar movimiento y contacto de la boya", "Confirmar que la bomba evacua", "Probar con agua antes de rearmar"],
        "note": "El comportamiento puede ser distinto en frío, calor, ventilación y parada.",
    },
    "configuration": {
        "causes": ["Dirección duplicada o sin asignar", "Capacidad o selector incorrectos", "Placa nueva sin configurar", "Memoria no inicializada"],
        "checks": ["Anotar todos los ajustes antes de tocar", "Comparar direcciones y funciones con la fuente", "Repetir el reconocimiento con todas las unidades alimentadas", "Verificar el número de unidades detectadas"],
        "note": "Una programación incorrecta puede detener una unidad, una rama o todo el sistema.",
    },
    "inverter": {
        "causes": ["Compresor o motor bloqueado", "Módulo inverter/IPM defectuoso", "Bus de continua o red fuera de rango", "Refrigeración del módulo insuficiente"],
        "checks": ["Aislar alimentación y esperar la descarga del bus", "Comprobar U-V-W y aislamiento", "Revisar red, rectificador y PFC", "Separar compresor, cable e inverter"],
        "note": "Estas mediciones requieren el método de seguridad de la familia concreta.",
    },
    "power": {
        "causes": ["Fase ausente o secuencia incorrecta", "Tensión fuera de rango", "Conexión o fusible defectuosos", "Circuito de detección anormal"],
        "checks": ["Medir entrada en reposo y bajo carga", "Comprobar fases, neutro y aprietes", "Revisar fusibles y bus con seguridad", "Distinguir red real y lectura falsa"],
        "note": "No rearmar repetidamente una protección de potencia sin eliminar su causa.",
    },
    "pressure": {
        "causes": ["Válvula de servicio cerrada", "Carga incorrecta o fuga", "Intercambiador o caudal de aire insuficiente", "Válvula, presostato o transductor defectuoso"],
        "checks": ["Confirmar válvulas abiertas", "Comparar presión real y lectura del control", "Revisar filtros, baterías y ventiladores", "Comprobar expansión y carga"],
        "note": "Los límites cambian con el refrigerante, el modo y la familia.",
    },
    "compressor": {
        "causes": ["Cableado U-V-W o devanados anormales", "Presiones sin equilibrar", "Inverter defectuoso", "Compresor bloqueado"],
        "checks": ["Aislar y descargar el bus", "Comparar resistencias entre fases y aislamiento", "Revisar salida del inverter con el procedimiento correcto", "Consultar protecciones anteriores"],
        "note": "No condenar el compresor solo por un código de arranque.",
    },
    "valve": {
        "causes": ["Bobina o cable abiertos", "EEV/PMV bloqueada", "Conector intercambiado", "Válvula de cuatro vías sin invertir"],
        "checks": ["Comprobar bobina y conector", "Usar el modo de servicio si existe", "Comparar temperaturas y presiones", "Verificar respuesta antes de sustituir la placa"],
        "note": "Una respuesta térmica incorrecta también puede deberse a carga o tubería.",
    },
    "pcb": {
        "causes": ["Placa sin alimentación", "EEPROM o microcontrolador defectuosos", "Conector interno suelto", "Configuración no restaurada"],
        "checks": ["Comprobar fuentes y fusibles", "Revisar conectores", "Copiar ajustes, direcciones y memoria permitida", "Inicializar y repetir la prueba"],
        "note": "Antes de cambiar una placa, descarte cableado, alimentación y configuración.",
    },
    "normal": {
        "causes": ["Estado operativo, aviso o protección temporal documentada"],
        "checks": ["Identificar el texto exacto", "Esperar la secuencia documentada", "Consultar historial si no recupera", "No sustituir componentes por un estado normal"],
        "note": "Un estado normal solo debe tratarse como avería si no finaliza como indica la fuente.",
    },
}


def normalize(value: str) -> str:
    value = "".join(
        char for char in unicodedata.normalize("NFD", str(value or ""))
        if unicodedata.category(char) != "Mn"
    ).upper()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9]+", " ", value)).strip()


def src(title: str, ref: str, url: str, kind: str, year: str, language: str = "en") -> dict[str, str]:
    return {"title": title, "document_ref": ref, "source_url": url, "type": kind, "year": year, "language": language}


def error(code: str, title: str, profile: str, source_ref: str, page: str, family: str, scope: str = "system",
          behavior: str = "La unidad o el sistema se protege según el alcance indicado para esta familia.",
          technical: str = "", aliases: tuple[str, ...] = (), indication: str = "display",
          contexts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "code": code, "title": title, "profile": profile, "source_ref": source_ref,
        "page": page, "family": family, "scope": scope, "behavior": behavior,
        "technical": technical or f"Condición documentada para {family}; confirme el punto de lectura.",
        "aliases": list(aliases), "indication": indication, "contexts": contexts or [],
    }


def led_context(code: str, location: str, family: str, relationship: str, indicators: list[tuple[str, str, str]],
                counting: str, cycle: str = "") -> dict[str, Any]:
    return {
        "code_display": code, "code_normalized": normalize(code), "indication_type": "outdoor_led",
        "display_location": location, "family_hint": family, "relationship": relationship,
        "led_indicators": [{"label": label, "color": color, "state": state} for label, color, state in indicators],
        "counting_rule": counting, "cycle_note": cycle or "Observe el ciclo completo antes de interpretar.",
        "sequence": "Respete el orden físico de los indicadores indicado en la placa.",
    }


def topic(category: str, slug: str, title: str, summary: str, variants: list[dict[str, Any]]) -> dict[str, Any]:
    return {"category": category, "slug": slug, "title": title, "summary": summary, "variants": variants}


def variant(title: str, recognition: str, source_ref: str, page: str, purpose: str, summary: str,
            system: str, scope: str = "system", steps: list[str] | None = None,
            technical: str = "", controller: dict[str, Any] | None = None,
            patterns: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    instructions = steps or [
        "Identifique la familia, el punto de lectura y los mandos visibles.",
        "Aplique solo la secuencia descrita para esta variante.",
        "Anote el resultado antes de borrar, reiniciar o cortar alimentación.",
    ]
    return {
        "title": title, "recognition": recognition, "system_type": system, "unit_scope": scope,
        "refrigerant": None, "purpose": purpose, "summary": summary,
        "source_kind": "official", "review_status": "reviewed",
        "sections": [
            {"section_type": "recognition", "title": "Cómo reconocer esta variante", "body": recognition, "collapsed_default": 0},
            {"section_type": "technical", "title": "Qué hace o tiene en cuenta la máquina", "body": technical or summary, "collapsed_default": 1},
        ],
        "steps": [
            {"phase": "prepare" if idx == 1 else ("verify" if idx == len(instructions) else "procedure"),
             "step_no": idx, "instruction": text, "expected_result": None, "warning_level": "none"}
            for idx, text in enumerate(instructions, start=1)
        ],
        "parameters": [], "controller": controller, "monitoring_points": [],
        "led_patterns": patterns or [], "media": [], "sources": [{"source_ref": source_ref, "page": page}],
    }


def common_topics(brand: str, main_ref: str, controller_ref: str, service_ref: str,
                  family_small: str, family_large: str) -> list[dict[str, Any]]:
    return [
        topic("history_reset", "alarm-history", "Historial de alarmas y borrado",
              "Separar la avería actual de la memoria evita diagnósticos falsos.", [
            variant("Consultar antes de borrar", "Mando o placa con función CHECK/HISTORY.", controller_ref, "diagnóstico e historial",
                    "Conservar la secuencia real.", "Lea unidad, código, subcódigo y orden temporal antes de rearmar.",
                    brand, steps=["Entre en diagnóstico con el equipo parado.", "Recorra todas las posiciones y anote cada código.", "Salga sin borrar hasta terminar las comprobaciones."]),
            variant("Borrado y reinicio", "La causa ya está corregida y el manual permite borrar.", controller_ref, "borrado de memoria",
                    "No ocultar una avería activa.", "El corte de alimentación y el borrado desde control no siempre tienen el mismo efecto.",
                    brand, steps=["Confirme que la causa está corregida.", "Ejecute el borrado específico de esa interfaz.", "Arranque y vuelva a consultar la memoria."]),
        ]),
        topic("component_checks", "sensor-checks", "Sondas y entradas analógicas",
              "Comprobar valor, cable, montaje y lectura de placa.", [
            variant("Sonda abierta o en corto", "Código asociado a temperatura ambiente, batería, tubería o descarga.", main_ref, "diagnóstico de termistores",
                    "Separar sensor y placa.", "Mida con el sensor aislado y compare solo con la curva de esa familia.", family_small),
            variant("Sensor correcto pero lectura incorrecta", "La resistencia coincide con la temperatura real.", main_ref, "diagnóstico de termistores",
                    "Comprobar el circuito de lectura.", "Revise conector, cable, masa de referencia y valor que muestra el monitor.", family_large),
        ]),
        topic("component_checks", "compressor-power-stage", "Compresor e inverter",
              "Orden seguro para separar red, placa, cable y compresor.", [
            variant("Comprobación eléctrica", "Protección de arranque, sobrecorriente o posición.", service_ref, "diagnóstico de inverter",
                    "Evitar sustituir por descarte.", "Descargue el bus, aísle el compresor y compare fases y aislamiento.", family_large, scope="outdoor"),
            variant("Comprobación frigorífica", "El accionamiento parece correcto pero la protección reaparece.", service_ref, "diagnóstico frigorífico",
                    "Separar bloqueo mecánico y condición de ciclo.", "Compruebe equilibrado, válvulas, carga, intercambio y temperaturas.", family_large, scope="outdoor"),
        ]),
        topic("normal_states", "normal-delays", "Retardos y secuencias normales",
              "Comportamientos que pueden parecer una avería.", [
            variant("Protección de rearranque", "El compresor acaba de detenerse o vuelve la red.", main_ref, "control de funcionamiento",
                    "Evitar rearmes innecesarios.", "Espere el retardo documentado antes de concluir que no arranca.", family_small),
            variant("Desescarche o prevención de aire frío", "Calefacción con ventilador interior detenido o caudal reducido.", main_ref, "control de calefacción",
                    "Reconocer una secuencia normal.", "La unidad modifica ventiladores y compresor mientras mantiene protecciones.", family_large),
        ]),
        topic("service_tools_boards", "board-replacement", "Después de sustituir una placa",
              "La placa nueva puede necesitar identidad, capacidad y direcciones.", [
            variant("Copiar ajustes", "Antes de retirar la placa original.", service_ref, "sustitución de PCB",
                    "Conservar la configuración.", "Fotografíe DIP, selectores, jumpers y conectores; anote direcciones y capacidad.", family_large),
            variant("Inicializar y verificar", "Placa nueva instalada.", service_ref, "sustitución de PCB",
                    "Evitar errores de modelo o comunicación.", "Restaure parámetros, reinicie según la fuente y repita reconocimiento y Test Run.", family_large),
        ]),
        topic("system_architecture", "recognize-family", f"Reconocer la plataforma {brand}",
              "El código solo es válido si coincide la generación y el punto de lectura.", [
            variant(f"{family_small}", "Equipo individual o residencial con mando/display propio.", main_ref, "identificación de familia",
                    "Elegir la tabla doméstica.", "No aplique automáticamente códigos de VRF o control central.", family_small),
            variant(f"{family_large}", "Sistema comercial, multisplit o VRF con red y direccionamiento.", service_ref, "identificación de familia",
                    "Elegir la tabla de sistema.", "Cruce el código con unidad, dirección, subcódigo y display exterior.", family_large),
        ]),
    ]


def hitachi_config() -> dict[str, Any]:
    sources = {
        "SETFREE": src("SET FREE Series Service Manual", "SM-SET-FREE-FSXN", "https://compressors.hitachi.teradisk.net/en/resources/vrf-systems/set-free-sigma", "service_manual", "2019"),
        "CENTRAL-OM": src("Central Station EX Operation Manual", "R0000026321", "https://documentation.hitachiaircon.com/fr/fr/controles/psc-a128ex/download/R0000026321_JCH", "operation_manual", "2026"),
        "CENTRAL-IM": src("Central Station EX Installation Manual", "R0000026391", "https://documentation.hitachiaircon.com/fr/fr/controles/psc-a128ex/download/R0000026391_JCH", "installation_manual", "2026"),
        "PAC": src("RPI L/M/H/U/T NE1NH Installation and Maintenance Manual", "R0000025265", "https://documentation.hitachiaircon.com/emea/en/pac/rpi-l-m-h-u-t-ne1nh/download/R0000025265_JCH", "installation_manual", "2025"),
        "ALARM": src("airCloud Alarm Code", "HITACHI-AIRCLOUD-ALARM", "https://aircloud-alarmcode.hitachiaircon.com/", "official_web", "current"),
        "HISTORY": src("Hitachi Cooling & Heating platform notice", "HITACHI-AIRCLOUD-PRO", "https://aircloudpro.hitachiaircon.com/", "official_web", "current"),
    }
    errors: list[dict[str, Any]] = []
    def add(code: str, title: str, profile: str, page: str, scope: str = "system", behavior: str = "", tech: str = "") -> None:
        errors.append(error(code, title, profile, "SETFREE", page, "SET FREE / H-LINK II", scope,
                            behavior or "La unidad indicada se protege; el alcance final depende de si la alarma pertenece a unidad, ciclo o red.",
                            tech))
    for row in [
        ("01", "Actuación del dispositivo de protección de la unidad interior", "drain", "296", "indoor"),
        ("02", "Actuación del dispositivo de protección de la unidad exterior", "pressure", "296", "outdoor"),
        ("03", "Transmisión anormal entre unidades interior y exterior", "communication", "296", "system"),
        ("04", "Transmisión anormal entre PCB inverter y PCB exterior", "communication", "296", "outdoor"),
        ("05", "Fase invertida o fase ausente en la alimentación", "power", "296", "outdoor"),
        ("06", "Tensión exterior anormalmente baja", "power", "296", "outdoor"),
        ("07", "Sobrecalentamiento de descarga insuficiente", "pressure", "296", "outdoor"),
        ("08", "Temperatura de descarga excesiva", "pressure", "296", "outdoor"),
        ("11", "Termistor de aire de entrada interior", "sensor", "296", "indoor"),
        ("12", "Termistor de aire de salida interior", "sensor", "296", "indoor"),
        ("13", "Termistor de protección antihielo", "sensor", "296", "indoor"),
        ("14", "Termistor de tubería de gas interior", "sensor", "296", "indoor"),
        ("19", "Dispositivo de protección del ventilador interior", "fan", "296", "indoor"),
        ("21", "Sensor de alta presión", "sensor", "297", "outdoor"),
        ("22", "Termistor de aire exterior", "sensor", "297", "outdoor"),
        ("23", "Termistor de gas de descarga", "sensor", "297", "outdoor"),
        ("24", "Termistor de evaporación exterior", "sensor", "297", "outdoor"),
        ("25", "Termistor de tubería de gas exterior", "sensor", "297", "outdoor"),
        ("26", "Termistor de gas de aspiración", "sensor", "297", "outdoor"),
        ("29", "Sensor de baja presión", "sensor", "297", "outdoor"),
        ("31", "Configuración incorrecta de unidades interior/exterior", "configuration", "298", "system"),
        ("32", "Transmisión anormal con otra unidad interior", "communication", "298", "system"),
        ("35", "Número de unidad interior incorrecto", "configuration", "298", "system"),
        ("36", "Combinación de unidades interiores incorrecta", "configuration", "298", "system"),
        ("38", "Anomalía del circuito de protección exterior", "pcb", "298", "outdoor"),
        ("39", "Anomalía de corriente de funcionamiento", "power", "298", "outdoor"),
        ("41", "Protección por sobrecarga en refrigeración", "pressure", "298", "system"),
        ("42", "Protección por sobrecarga en calefacción", "pressure", "298", "system"),
        ("43", "Protección por relación de presiones", "pressure", "298", "outdoor"),
        ("44", "Protección por aumento de baja presión", "pressure", "298", "outdoor"),
        ("45", "Protección por aumento de alta presión", "pressure", "298", "outdoor"),
        ("46", "Protección por descenso de alta presión", "pressure", "298", "outdoor"),
        ("47", "Protección por descenso de baja presión", "pressure", "298", "outdoor"),
        ("48", "Protección de sobrecorriente del inverter", "inverter", "298", "outdoor"),
        ("51", "Sensor de corriente del inverter", "inverter", "298", "outdoor"),
        ("52", "Protección de sobrecarga del inverter", "inverter", "298", "outdoor"),
        ("53", "Señal de fallo del módulo inverter", "inverter", "298", "outdoor"),
        ("54", "Temperatura de aletas del inverter", "inverter", "298", "outdoor"),
        ("55", "Fallo del inverter", "inverter", "298", "outdoor"),
        ("57", "Protección del motor de ventilador exterior", "fan", "298", "outdoor"),
        ("59", "Anomalía del circuito AC chopper/PFC", "power", "298", "outdoor"),
        ("70", "Protección de caja CH o distribución", "configuration", "299", "system"),
        ("71", "Combinación o conexión incorrecta de caja CH", "configuration", "299", "system"),
        ("72", "Número de interiores por rama de caja CH incorrecto", "configuration", "299", "system"),
        ("EE", "Protección acumulada del compresor", "compressor", "300", "outdoor"),
    ]:
        add(*row)
    for code, title, behavior in [
        ("60", "Comunicación entre estación central y unidad exterior", "La estación central pierde la red H-LINK mientras hay unidades interiores funcionando."),
        ("61", "Comunicación entre unidad interior y estación central", "La unidad indicada no puede intercambiar datos con la estación central."),
        ("63", "Combinación incompatible de estaciones centrales", "El control central bloquea la combinación incoherente de especificaciones H-LINK."),
        ("64", "Comunicación central–exterior sin interiores activas", "La estación registra la pérdida aun cuando ninguna interior está en marcha."),
        ("65", "Comunicación entre estación central y adaptador", "El control central no puede comunicar con el adaptador asociado."),
        ("FF", "Alarma de una instalación o equipo externo", "La estación señala una entrada de instalación; debe comprobarse el equipo externo asociado."),
    ]:
        errors.append(error(code, title, "communication", "CENTRAL-OM", "tabla de alarmas", "Central Station EX / H-LINK", "system", behavior))
    for code, title, profile in [
        ("S10", "Comunicación con PIO1", "communication"),
        ("S11", "Comunicación con PIO2", "communication"),
        ("S20", "Memoria interna insuficiente", "pcb"),
        ("S21", "Fallo de escritura en memoria o medio", "pcb"),
        ("S22", "Fallo de carga desde memoria o medio", "pcb"),
        ("S23", "Comunicación con adaptador de extensión", "communication"),
        ("S24", "Actualización del horario de verano", "configuration"),
        ("S41", "Acceso al archivo de cálculo", "pcb"),
        ("S42", "Datos de descarga no válidos", "configuration"),
        ("S43", "Lectura o escritura de datos de configuración", "pcb"),
    ]:
        errors.append(error(
            code, title, profile, "CENTRAL-OM", "58, tabla de alarmas",
            "Central Station EX", "controller",
            "La estación central conserva el control HVAC que siga disponible, pero la función propia indicada queda degradada.",
            "Código interno de Central Station EX; no corresponde a una protección frigorífica de la unidad.",
        ))
    topics = [
        topic("outdoor_diagnostics", "seven-segment-outdoor", "Display exterior de siete segmentos",
              "La placa muestra dirección de unidad, alarma y estados de servicio.", [
            variant("Alarma actual", "PCB exterior SET FREE con display de siete segmentos y pulsadores.", "SETFREE", "296-300",
                    "Leer código y unidad afectada.", "La placa alterna información de unidad/ciclo y código; anote toda la secuencia.", "SET FREE", "outdoor"),
            variant("Subcódigo y compresor afectado", "Sistemas combinados o con más de un compresor.", "SETFREE", "285-300",
                    "No perder el componente concreto.", "Cruce el código principal con el número de exterior, compresor o caja CH mostrado.", "SET FREE", "outdoor"),
        ]),
        topic("diagnostic_access", "wired-controller-alarm", "Obtener alarma desde mando cableado",
              "RUN rojo parpadea y la pantalla identifica sistema, unidad y código.", [
            variant("Pantalla de alarma", "Mando PC-ARF/PC-ARFG con LCD y símbolo ALARM.", "SETFREE", "285-290",
                    "Registrar código completo.", "Anote número de ciclo frigorífico, unidad interior, código y modelo antes de salir.", "PC-ARF / PC-ARFG", "controller"),
            variant("Caja CH", "Sistema de tres tubos con caja de cambio.", "SETFREE", "290",
                    "Distinguir alarma de distribución.", "La caja CH dispone de su propia tabla; no la sustituya por el significado de una interior.", "SET FREE 3 tubos"),
        ]),
        topic("diagnostic_access", "central-station-alarm", "Alarmas desde Central Station EX",
              "La estación separa alarma del equipo y fallos propios de H-LINK.", [
            variant("00–FE", "La estación muestra una alarma generada por aire acondicionado.", "CENTRAL-OM", "tabla de alarmas",
                    "Ir a la unidad que originó la alarma.", "La estación remite al procedimiento de la unidad y conserva dirección y código.", "Central Station EX"),
            variant("60, 61, 63, 64 y 65", "Código de comunicación propio de la estación.", "CENTRAL-OM", "tabla de alarmas",
                    "Diagnosticar H-LINK/control central.", "Estos códigos no deben interpretarse como una protección frigorífica.", "Central Station EX"),
        ]),
        topic("service_modes", "set-free-test-run", "Test Run y comprobación SET FREE",
              "La prueba mantiene activas las protecciones del sistema.", [
            variant("Test Run desde mando", "Sistema direccionado y sin alarmas activas.", "SETFREE", "puesta en marcha",
                    "Verificar todas las interiores.", "Seleccione frío o calor, confirme respuesta por dirección y revise alarmas.", "SET FREE"),
            variant("Prueba desde placa exterior", "PCB con pulsadores y display.", "SETFREE", "display de servicio",
                    "Arrancar el ciclo sin demanda normal.", "La placa gobierna el modo de prueba, pero no anula alta/baja presión, corriente ni descarga.", "SET FREE", "outdoor"),
        ]),
        topic("service_modes", "emergency-operation", "Funcionamiento de emergencia por compresor",
              "Algunas SET FREE permiten seguir con capacidad reducida.", [
            variant("Aislar compresor inverter averiado", "Alarma admitida por la tabla de emergencia y resto de compresores disponibles.", "SETFREE", "emergency operation",
                    "Mantener servicio provisional.", "La continuidad solo está permitida para alarmas y combinaciones expresamente indicadas.", "SET FREE", "outdoor"),
            variant("Cancelar emergencia", "La reparación ya se ha completado.", "SETFREE", "emergency operation",
                    "Recuperar control normal.", "Restaure cableado y ajustes, reinicie todas las exteriores y ejecute Test Run.", "SET FREE", "outdoor"),
        ]),
        topic("configuration", "hlink-addressing", "Direcciones H-LINK y circuito frigorífico",
              "Duplicados y unidades ausentes generan alarmas de configuración.", [
            variant("Dirección de circuito", "PCB con DSW/RSW de refrigerant system number.", "SETFREE", "configuración H-LINK II",
                    "Evitar duplicados.", "Cada ciclo debe tener una dirección única y coherente en exterior, interiores y adaptadores.", "H-LINK II"),
            variant("Direccionamiento automático", "Todas las unidades alimentadas y red terminada.", "SETFREE", "automatic addressing",
                    "Construir el mapa de unidades.", "Si el conteo no coincide, revise alimentación, cable y ajustes antes de repetir.", "SET FREE"),
        ]),
        topic("controllers_buses", "hlink-bus", "Bus H-LINK / H-LINK II",
              "Red común de unidades y controladores con terminación única.", [
            variant("Cable y topología", "Terminales H-LINK y red de dos hilos.", "CENTRAL-IM", "H-LINK wiring",
                    "Comprobar continuidad y derivaciones.", "No mezcle alimentación con transmisión; respete sección, longitud y topología del manual.", "H-LINK II"),
            variant("Compatibilidad de controladores", "Alarma 63 o ampliación de red.", "CENTRAL-OM", "alarma 63",
                    "Evitar controles incompatibles.", "Confirme que todos los controladores usan la misma especificación H-LINK.", "H-LINK"),
        ]),
        topic("drainage_overflow", "hitachi-float-switch", "Boya, bomba y alarma 01",
              "La protección interior 01 también puede proceder del drenaje.", [
            variant("Frío con agua en bandeja", "Cassette o conductos con bomba y boya.", "SETFREE", "alarma 01",
                    "Separar ventilador y drenaje.", "Compruebe evacuación, bomba, boya y PCB antes de atribuir 01 al motor.", "Interior comercial", "indoor"),
            variant("Boya atascada", "Alarma reaparece sin condensación suficiente.", "SETFREE", "alarma 01",
                    "Detectar contacto retenido.", "Accione la boya manualmente, mida su contacto y verifique que baja al vaciar.", "Interior comercial", "indoor"),
        ]),
        topic("commissioning", "hlink-commissioning", "Puesta en marcha H-LINK",
              "Alimentación, terminación, conteo y prueba por dirección.", [
            variant("Antes de direccionar", "Instalación nueva o ampliada.", "CENTRAL-IM", "installation and function selection",
                    "Evitar alarmas encadenadas.", "Compruebe alimentación, aislamiento del bus, terminación y direcciones preexistentes.", "H-LINK II"),
            variant("Comprobación final", "Mapa de unidades adquirido.", "SETFREE", "test run",
                    "Confirmar todas las unidades.", "Mande marcha/parada por dirección y compruebe que no aparece una unidad distinta.", "SET FREE"),
        ]),
        topic("multisplit", "hitachi-multisplit", "Multisplit y adaptadores RAC",
              "El adaptador integra RAC en H-LINK, pero no convierte sus códigos en SET FREE.", [
            variant("Adaptador RAC", "Split doméstico conectado a control central mediante adaptador.", "PAC", "H-LINK adaptor",
                    "Separar código RAC y red.", "Una alarma de red puede estar en el adaptador mientras la protección del equipo sigue su tabla RAC.", "RAC + H-LINK"),
            variant("Conflicto de modo", "Varias interiores comparten exterior.", "PAC", "control operation",
                    "Reconocer espera normal.", "Una interior puede quedar en espera cuando su modo contradice al ciclo activo.", "Multisplit"),
        ]),
        topic("vrf_network", "stop-scope", "VRF: alcance de parada y respaldo",
              "El código debe indicar si afecta a unidad, ciclo, caja o compresor.", [
            variant("Alarma de unidad interior", "Código 01/11/12/13/14/19 con dirección interior.", "SETFREE", "296-297",
                    "Mantener el resto si el sistema lo permite.", "La dirección identifica la interior afectada; confirme en el historial si otras siguen operando.", "SET FREE"),
            variant("Alarma exterior o de red", "Códigos 02–08, 31–59 o 03.", "SETFREE", "296-300",
                    "Determinar parada de ciclo.", "Las protecciones de ciclo y transmisión pueden detener todas las interiores asociadas.", "SET FREE"),
        ]),
        topic("technical_values", "hitachi-control-data", "Datos de control y secuencias",
              "Solo se muestran valores ligados a una familia.", [
            variant("Retardo de tres minutos", "PAC recién detenido o alimentado.", "PAC", "control system",
                    "Esperar protección normal.", "El compresor no rearranca inmediatamente tras una parada.", "PAC"),
            variant("Marcha mínima de cinco minutos", "PAC ya arrancado sin protección activa.", "PAC", "control system",
                    "No confundir continuidad con mando ignorado.", "La lógica puede mantener la marcha mínima antes de atender una parada normal.", "PAC"),
        ]),
        topic("service_tools_boards", "aircloud-alarm-tool", "airCloud Alarm Code",
              "Herramienta oficial para escoger producto y abrir diagnóstico.", [
            variant("Selección por producto", "Web o aplicación oficial airCloud Alarm Code.", "ALARM", "servicio oficial",
                    "Evitar usar una tabla genérica.", "Seleccione tipo, familia y tamaño antes del código; el diagnóstico se descarga para esa selección.", "Hitachi Cooling & Heating"),
            variant("Fuente complementaria", "La aplicación no reconoce una generación antigua.", "ALARM", "servicio oficial",
                    "Mantener trazabilidad.", "Use manual de servicio de la familia y registre su referencia; no fuerce una equivalencia.", "Hitachi Cooling & Heating"),
        ]),
    ]
    topics += common_topics("Hitachi", "PAC", "CENTRAL-OM", "SETFREE", "RAC/PAC individual", "SET FREE / H-LINK II")
    return {
        "slug": "hitachi", "name": "Hitachi", "display_name": "Hitachi",
        "brand_id": 17, "sources": sources, "errors": errors, "topics": topics,
        "scope": "Hitachi RAC/PAC, controles H-LINK y SET FREE",
        "warning": "Confirme familia y etapa de producto. No mezcle plataformas Hitachi históricas con productos actuales bajo licencia Bosch.",
        "notes": "Hitachi Referencia V1: RAC/PAC, H-LINK, controles centrales y SET FREE, con códigos, procedimientos, red y funcionamiento degradado.",
    }


def sharp_config() -> dict[str, Any]:
    sources = {
        "ERROR": src("Sharp Air Conditioner Error Code List", "SHARP-AIR-ERROR", "https://global.sharp/smartapp/air/support/airconerror/", "official_web", "current"),
        "OM": src("Sharp ZU/ZHU/BU Operation Manual", "OM-ZU-ZHU-BU", "https://global.sharp/smartapp/air/support/airconmanual/OM_ZU_ZHU_BU.pdf", "operation_manual", "2024"),
        "MULTI": src("Sharp AE-X3M24CU Installation Manual", "IM-3M24CU", "https://global.sharp/smartapp/air/support/airconmanual/IM_3M24CU.pdf", "installation_manual", "2026"),
        "CPU": src("Sharp CPU Series Installation Manual", "IM-CPU", "https://global.sharp/smartapp/air/support/airconmanual/IM_CPU.pdf", "installation_manual", "2024"),
        "AHA": src("AHA! Air History Analyzer", "SHARP-AHA", "https://global.sharp/products/hvac/app/aha_app/", "official_web", "current"),
    }
    rows = [
        ("1-0", "Termistor de batería exterior en cortocircuito", "sensor"), ("1-1", "Termistor de aire exterior en cortocircuito", "sensor"),
        ("1-2", "Termistor de aspiración en cortocircuito", "sensor"), ("1-3", "Termistor de válvula de dos vías en cortocircuito", "sensor"),
        ("1-4", "Termistor de disipador en cortocircuito", "sensor"), ("2-0", "Temperatura alta del compresor", "pressure"),
        ("2-1", "Sobrecalentamiento de descarga del compresor", "pressure"), ("2-2", "Sobretemperatura de batería exterior", "pressure"),
        ("2-3", "Sobretemperatura de batería interior", "pressure"), ("2-4", "Temperatura alta del IPM", "inverter"),
        ("2-5", "Temperatura alta del IPM, variante de detección", "inverter"), ("3-0", "Parada temporal durante deshumidificación", "normal"),
        ("5-0", "Termistor de batería exterior abierto", "sensor"), ("5-1", "Termistor de aire exterior abierto", "sensor"),
        ("5-2", "Termistor de aspiración abierto", "sensor"), ("5-3", "Termistor de válvula de dos vías abierto", "sensor"),
        ("5-4", "Termistor de descarga abierto", "sensor"), ("5-5", "Termistor de disipador abierto", "sensor"),
        ("6-0", "Sobrecorriente DC", "inverter"), ("6-1", "Señal de nivel del pin IPM", "inverter"),
        ("7-0", "Sobrecorriente AC", "power"), ("7-1", "Corriente AC detectada con el equipo parado", "power"),
        ("7-2", "Corriente AC máxima", "power"), ("7-3", "Corriente AC insuficiente", "power"),
        ("9-0", "Termistor mal instalado o válvula de cuatro vías", "valve"), ("9-3", "Control de par del compresor", "compressor"),
        ("9-4", "Válvula de cuatro vías o fuga de gas", "valve"), ("9-5", "Válvulas de dos y tres vías cerradas", "pressure"),
        ("9-6", "Válvula solenoide", "valve"), ("10-0", "Datos EEPROM exterior", "pcb"),
        ("10-1", "Datos EEPROM exterior, variante", "pcb"), ("10-2", "Datos RAM de CPU exterior", "pcb"),
        ("11-0", "Rotación del ventilador DC exterior", "fan"), ("11-1", "Driver IC del ventilador DC exterior", "fan"),
        ("11-2", "Ventilador DC exterior bloqueado", "fan"), ("11-3", "Giro inverso del ventilador antes del compresor", "fan"),
        ("11-4", "Detección de corriente del ventilador DC", "fan"), ("11-5", "Conector abierto del ventilador DC exterior", "fan"),
        ("12-0", "Fusible térmico de la bornera de alimentación", "power"), ("13-0", "Arranque del compresor", "compressor"),
        ("13-1", "Rotación del compresor con excitación de 120°", "compressor"), ("13-2", "Rotación del compresor con excitación de 180°", "compressor"),
        ("13-3", "Detección de corriente del inverter", "inverter"), ("14-0", "Sobretensión PAM", "power"),
        ("14-1", "Reloj PAM", "power"), ("14-2", "Subtensión PAM", "power"), ("14-4", "Módulo PFC", "power"),
        ("17-0", "Circuito serie abierto", "communication"), ("18-0", "Circuito serie en cortocircuito", "communication"),
        ("18-1", "Cableado serie incorrecto", "communication"), ("18-2", "Comunicación serie de alta velocidad", "communication"),
        ("19-0", "Ventilador interior", "fan"), ("19-1", "Ventilador interior a baja velocidad", "fan"),
        ("19-2", "Ventilador interior gira durante parada", "fan"), ("19-3", "Ventilador interior a velocidad excesiva", "fan"),
        ("20-0", "Datos EEPROM interior", "pcb"), ("20-1", "Lectura inicial de EEPROM externa", "pcb"),
        ("20-2", "Verificación de EEPROM externa", "pcb"), ("20-3", "Comunicación con EEPROM externa", "pcb"),
        ("21-0", "Cierre incompleto de tapa o palanca de lamas", "configuration"), ("22-0", "Conexión Plasmacluster", "pcb"),
        ("22-1", "Sensor Lock On", "sensor"), ("22-2", "Tiempo acumulado de Plasmacluster excedido", "normal"),
        ("23-0", "Conexión incorrecta a 200 V AC", "power"), ("23-1", "Tensión incorrecta durante funcionamiento", "power"),
        ("24-0", "Comunicación con módulo WLAN", "communication"), ("24-1", "Conexión con router WLAN", "communication"),
        ("24-2", "Conexión a Internet", "communication"), ("24-3", "Conexión con servidor", "communication"),
        ("25-1", "Reloj del aire acondicionado", "pcb"), ("26-1", "Termistor de ambiente interior", "sensor"),
        ("26-2", "Termistor de tubería interior", "sensor"), ("26-3", "Sensor de gas", "sensor"),
        ("26-4", "Sensor de polvo", "sensor"), ("28-0", "Inicio de limpieza automática de filtro", "configuration"),
        ("28-1", "Fallo durante limpieza de filtro", "configuration"), ("28-2", "Panel o filtro mal cerrado/instalado", "configuration"),
        ("28-3", "Filtro desprendido", "configuration"), ("29-0", "El panel no puede abrir", "configuration"),
        ("29-1", "El panel no puede cerrar", "configuration"), ("31-0", "Microcontrolador secundario", "pcb"),
        ("31-6", "Microcontrolador secundario, variante 6", "pcb"), ("31-7", "Microcontrolador secundario, variante 7", "pcb"),
    ]
    errors = [
        error(code, title, profile, "ERROR", "tabla web oficial", "Sharp Air App / series compatibles",
              "system", "El equipo detiene o limita la función asociada; 3-0 es una parada temporal documentada.")
        for code, title, profile in rows
    ]
    wire_ok = led_context("WIRE CHECK OK", "placa exterior multisplit", "AE-X3M24CU",
                          "Cableado y tuberías reconocidos",
                          [("LED1A", "yellow", "blink"), ("LED1B", "yellow", "blink"), ("LED1C", "yellow", "blink")],
                          "Los tres LED vuelven a parpadeo normal al terminar correctamente.")
    wire_fail = led_context("WIRE CHECK FAIL", "placa exterior multisplit", "AE-X3M24CU",
                            "Autocorrección no completada",
                            [("LED1A", "yellow", "triple_blink"), ("LED1B", "yellow", "triple_blink"), ("LED1C", "yellow", "triple_blink")],
                            "Los LED repiten ocho ciclos de triple parpadeo y la operación se detiene.")
    topics = [
        topic("outdoor_diagnostics", "sharp-wire-check-leds", "Tabla visual LED1A–LED1C del multisplit",
              "Los pilotos indican puertos y resultado de Wire Check.", [
            variant("Parpadeo normal", "Tres LED LED1A, LED1B y LED1C en la placa exterior.", "MULTI", "4",
                    "Confirmar conexiones reconocidas.", "Parpadeo simultáneo normal después de una prueba correcta.", "Sharp 3-zone", "outdoor", patterns=[wire_ok]),
            variant("Ocho ciclos de triple parpadeo", "La prueba se detiene sin autocorrección.", "MULTI", "4",
                    "Detectar tubería, válvula o cableado.", "Revise tuberías, válvulas y bornes antes de repetir.", "Sharp 3-zone", "outdoor", patterns=[wire_fail]),
        ]),
        topic("diagnostic_access", "sharp-remote-error-code", "Sacar código principal y subcódigo con el mando",
              "El mando recorre por separado las dos partes del código y la unidad confirma con pitidos.", [
            variant("Entrar en modo de códigos", "Mando inalámbrico ZU/ZHU/BU con el equipo parado.", "OM", "25",
                    "Obtener el código completo.", "Mantenga la tecla indicada más de cinco segundos hasta que aparezca el modo y suene el receptor.", "Sharp ZU/ZHU/BU", "controller",
                    ["Apague la unidad desde el mando.", "Mantenga la tecla de diagnóstico más de cinco segundos.", "Recorra el código principal hasta escuchar el pitido largo.", "Recorra el subcódigo y anote ambos.", "Pulse la tecla de salida."]),
            variant("Pitido corto frente a largo", "El mando cambia valores mientras apunta al receptor.", "OM", "25",
                    "No confundir un valor probado con el guardado.", "Cada paso genera pitido corto; el valor coincidente genera pitido largo.", "Sharp ZU/ZHU/BU", "controller"),
        ]),
        topic("service_modes", "sharp-wire-check", "Wire Check de cableado y tuberías",
              "La exterior puede comprobar y corregir asignaciones en multisplit.", [
            variant("Iniciar con SW2", "Exterior AE-X3M24 con pulsador WIRE CHECK.", "MULTI", "4",
                    "Comprobar correspondencia de puertos.", "Mantenga SW2 al menos cinco segundos; la prueba dura aproximadamente 5–10 minutos.", "Sharp 3-zone", "outdoor",
                    ["Abra todas las válvulas y confirme cableado.", "Alimente y compruebe los tres LED.", "Mantenga SW2 durante cinco segundos o más.", "Espere 5–10 minutos sin interrumpir.", "Interprete los LED al finalizar."]),
            variant("Límite por temperatura exterior", "Temperatura exterior inferior a 5 °C.", "MULTI", "4",
                    "Evitar un resultado inválido.", "El manual advierte que Wire Check puede no ejecutarse correctamente por debajo de 5 °C.", "Sharp 3-zone", "outdoor"),
        ]),
        topic("service_modes", "sharp-pump-down", "Pump Down desde la placa exterior",
              "Recogida controlada cuando la familia dispone de SW1.", [
            variant("Pulsador SW1 PUMP DOWN", "Exterior con SW1 rotulado PUMP DOWN y SW2 WIRE CHECK.", "MULTI", "4 y procedimiento de pump down",
                    "Recoger refrigerante.", "Siga presión, válvulas y tiempo del manual exacto; no use SW1 como marcha forzada genérica.", "Sharp 3-zone", "outdoor"),
            variant("Finalizar con seguridad", "La presión alcanza el criterio del procedimiento.", "MULTI", "pump down",
                    "Evitar vacío profundo o entrada de aire.", "Cierre la válvula indicada, detenga la unidad y corte alimentación antes de desconectar.", "Sharp multisplit", "outdoor"),
        ]),
        topic("configuration", "sharp-wlan-setup", "WLAN, router y servidor",
              "24-0 a 24-3 separan cuatro capas de comunicación.", [
            variant("Módulo local", "Código 24-0.", "ERROR", "tabla web oficial",
                    "Revisar unidad–módulo.", "Compruebe alimentación, conector y comunicación local antes de tocar el router.", "Sharp Air App"),
            variant("Router, Internet o servidor", "Código 24-1, 24-2 o 24-3.", "ERROR", "tabla web oficial",
                    "Aislar la capa afectada.", "24-1 es enlace al router; 24-2 salida a Internet; 24-3 servicio remoto.", "Sharp Air App"),
        ]),
        topic("controllers_buses", "sharp-serial-link", "Enlace serie interior–exterior",
              "Los códigos 17-0 y 18-x distinguen apertura, corto, cableado y alta velocidad.", [
            variant("17-0 circuito abierto", "La interior no recibe retorno serie.", "ERROR", "tabla web oficial",
                    "Localizar interrupción.", "Compruebe alimentación exterior, continuidad y conectores.", "Sharp split"),
            variant("18-0, 18-1 y 18-2", "Hay señal pero es inválida o la línea está en corto.", "ERROR", "tabla web oficial",
                    "Separar corto, error de bornes y enlace rápido.", "No sustituya PCB hasta descartar cable y correspondencia de terminales.", "Sharp split"),
        ]),
        topic("drainage_overflow", "sharp-drainage", "Drenaje y agua en interiores",
              "La documentación de instalación exige pendiente y prueba de fugas.", [
            variant("Prueba de drenaje", "Interior recién instalado o con goteo.", "CPU", "drainage",
                    "Confirmar evacuación.", "Vierta agua de prueba, compruebe pendiente, uniones y ausencia de retorno.", "Sharp split", "indoor"),
            variant("Equipo sigue funcionando tras apagar", "Modo COOL/DRY con AFTER CARE.", "OM", "22 y 27",
                    "No confundir secado con avería.", "AFTER CARE puede mantener ventilación o calor para secar el interior.", "Sharp ZU/ZHU/BU", "indoor"),
        ]),
        topic("commissioning", "sharp-multi-commissioning", "Puesta en marcha multisplit",
              "Bornes, válvulas y Wire Check forman una única secuencia.", [
            variant("Antes de Wire Check", "Tres puertos A/B/C cableados.", "MULTI", "4",
                    "Evitar dañar el control.", "Haga coincidir marcas de borneras, abra válvulas y confirme alimentación 208/230 V.", "Sharp 3-zone"),
            variant("Resultado por puerto", "LED1A, LED1B y LED1C.", "MULTI", "4",
                    "Localizar la rama incorrecta.", "Un LED fijo indica puerto no conectado o no coincidente; corrija antes de iniciar.", "Sharp 3-zone"),
        ]),
        topic("multisplit", "sharp-mode-conflict", "Conflicto de modo y comportamiento multisplit",
              "La interior puede quedar pendiente sin avería cuando otra unidad fija el modo.", [
            variant("Dos indicadores parpadean", "Interior en modo incompatible con otra interior activa.", "OM", "27",
                    "Reconocer conflicto de frío/calor.", "Alinee los modos o apague la unidad incompatible; no es un fallo de placa.", "Sharp multisplit", "indoor"),
            variant("Calor residual durante AFTER CARE", "Otra interior del mismo sistema está en calefacción.", "OM", "27",
                    "Interpretar transferencia de calor.", "Puede llegar calor por tuberías compartidas aun con la interior en AFTER CARE o parada.", "Sharp multisplit", "indoor"),
        ]),
        topic("technical_values", "sharp-electrical-values", "Valores eléctricos documentados",
              "Referencias ligadas a la exterior de tres zonas.", [
            variant("Alimentación", "AE-X3M24CU.", "MULTI", "4",
                    "Verificar red.", "208/230 V monofásica; rango operativo publicado 187–253 V.", "Sharp 3-zone", "outdoor"),
            variant("Protección y corriente", "AE-X3M24CU.", "MULTI", "4",
                    "Dimensionar circuito.", "Fusible máximo 25 A y ampacidad mínima de circuito 17 A para esta familia.", "Sharp 3-zone", "outdoor"),
        ]),
        topic("service_tools_boards", "sharp-aha", "AHA! Air History Analyzer",
              "Aplicación oficial de apoyo al mantenimiento.", [
            variant("Historial y diagnóstico", "Equipo Sharp compatible y acceso profesional.", "AHA", "página oficial",
                    "Leer eventos y contexto.", "La herramienta ayuda a identificar errores y funcionamiento histórico en equipos compatibles.", "Sharp HVAC"),
            variant("Compatibilidad", "El equipo no aparece en AHA.", "AHA", "página oficial",
                    "Evitar resultados de otra plataforma.", "Use la tabla del manual y el punto de lectura local; no fuerce una familia parecida.", "Sharp HVAC"),
        ]),
    ]
    topics += common_topics("Sharp", "OM", "OM", "ERROR", "RAC ZU/ZHU/BU", "Multisplit / plataforma inverter")
    return {
        "slug": "sharp", "name": "Sharp", "display_name": "Sharp",
        "brand_id": 18, "sources": sources, "errors": errors, "topics": topics,
        "scope": "Sharp RAC actual y multisplit documentado",
        "warning": "Confirme que el equipo pertenece a la plataforma Sharp indicada; un código de la Air App no es universal para generaciones anteriores.",
        "notes": "Sharp Referencia V1: tabla oficial principal/subcódigo, obtención por mando, Wire Check multisplit, buses, servicio y estados normales.",
    }


def sanyo_config() -> dict[str, Any]:
    sources = {
        "2WAY": src("SANYO 2WAY ECO-i Service Manual", "SM830186-00", "https://www.panasonicproclub.com/uploads/CZ/catalogues/ecoi/service-manual/Ecoi_service%20manual_ME1%28SM830186-00%29.pdf", "service_manual", "2010"),
        "3WAY": src("SANYO 3-WAY ECO-i Service Manual", "SM830188-00", "https://www.panasonicproclub.com/uploads/GB/catalogues/ECOi%203-Pipe%20Service%20Manual.pdf", "service_manual", "2010"),
        "W2WAY": src("SANYO W-2WAY ECO-i Service Manual", "SM830157", "https://www.panasonicproclub.com/uploads/CZ/catalogues/ecoi/service-manual/Ecoi_service%20manual_ME1%28SM830186-00%29.pdf", "service_manual", "2007"),
    }
    rows = [
        ("E01", "El mando no recibe comunicación de la unidad interior", "communication", "indoor"),
        ("E02", "El mando no transmite a la unidad interior", "communication", "controller"),
        ("E03", "La unidad interior no recibe comunicación del mando", "communication", "indoor"),
        ("E04", "La unidad interior no recibe comunicación exterior al inicio", "communication", "system"),
        ("E05", "La unidad interior no transmite comunicación a la exterior", "communication", "system"),
        ("E06", "La exterior no recibe comunicación de la interior tras inicialización", "communication", "system"),
        ("E07", "La exterior no transmite comunicación a la interior", "communication", "system"),
        ("E08", "Dirección de unidad interior duplicada", "configuration", "system"),
        ("E09", "Varios mandos configurados como principal", "configuration", "controller"),
        ("E10", "Comunicación entre PCB interiores", "communication", "indoor"),
        ("E11", "Mando principal duplicado en control de grupo", "configuration", "controller"),
        ("E12", "Inicio de direccionamiento automático prohibido", "configuration", "system"),
        ("E13", "La unidad interior no responde durante direccionamiento", "communication", "system"),
        ("E14", "Dirección de unidad principal duplicada", "configuration", "system"),
        ("E15", "Direccionamiento automático: menos interiores de las configuradas", "configuration", "system"),
        ("E16", "Direccionamiento automático: más interiores de las configuradas", "configuration", "system"),
        ("E18", "Comunicación de grupo con unidad principal", "communication", "system"),
        ("E20", "Sin señal de interiores durante direccionamiento automático", "communication", "system"),
        ("E24", "Comunicación entre exteriores", "communication", "outdoor"),
        ("E25", "Dirección de exterior duplicada", "configuration", "system"),
        ("E26", "Número de exteriores no coincide", "configuration", "system"),
        ("E29", "Exterior secundaria no recibe comunicación de la principal", "communication", "outdoor"),
        ("F01", "Termistor de batería interior E1", "sensor", "indoor"),
        ("F02", "Termistor de batería interior E3", "sensor", "indoor"),
        ("F04", "Termistor de descarga exterior 1", "sensor", "outdoor"),
        ("F05", "Termistor de descarga exterior 2", "sensor", "outdoor"),
        ("F06", "Termistor de batería exterior C1", "sensor", "outdoor"),
        ("F07", "Termistor de batería exterior C2", "sensor", "outdoor"),
        ("F08", "Termistor de aire exterior", "sensor", "outdoor"),
        ("F10", "Termistor de aire de retorno interior", "sensor", "indoor"),
        ("F11", "Termistor de aire de impulsión interior", "sensor", "indoor"),
        ("F12", "Termistor de aspiración exterior", "sensor", "outdoor"),
        ("F16", "Sensor de alta presión exterior", "sensor", "outdoor"),
        ("F17", "Sensor de baja presión exterior", "sensor", "outdoor"),
        ("F29", "EEPROM interior", "pcb", "indoor"),
        ("F31", "EEPROM exterior", "pcb", "outdoor"),
        ("H05", "Sensor de descarga del compresor 1 no insertado o anormal", "sensor", "outdoor"),
        ("H11", "Sobrecorriente del compresor de velocidad fija 2", "compressor", "outdoor"),
        ("H12", "Corriente de bloqueo del compresor de velocidad fija 2", "compressor", "outdoor"),
        ("H13", "Sensor CT del compresor 2 abierto o en corto", "sensor", "outdoor"),
        ("H15", "Sensor de descarga del compresor 2 no insertado o anormal", "sensor", "outdoor"),
        ("H21", "Sobrecorriente del compresor 3", "compressor", "outdoor"),
        ("H22", "Corriente de bloqueo del compresor 3", "compressor", "outdoor"),
        ("H23", "Sensor CT del compresor 3 abierto o en corto", "sensor", "outdoor"),
        ("H25", "Sensor de descarga del compresor 3 no insertado o anormal", "sensor", "outdoor"),
        ("H31", "Alarma del módulo HIC", "inverter", "outdoor"),
        ("L02", "Unidad interior principal duplicada en grupo", "configuration", "system"),
        ("L03", "Dirección de unidad principal duplicada", "configuration", "system"),
        ("L04", "Dirección de exterior duplicada", "configuration", "system"),
        ("L05", "Prioridad interior duplicada, unidad prioritaria", "configuration", "indoor"),
        ("L06", "Prioridad interior duplicada, resto de unidades", "configuration", "system"),
        ("L07", "Cable de grupo conectado a unidad individual", "configuration", "system"),
        ("L08", "Dirección interior sin configurar", "configuration", "indoor"),
        ("L09", "Código de capacidad interior sin configurar", "configuration", "indoor"),
        ("L10", "Capacidad exterior sin configurar", "configuration", "outdoor"),
        ("L17", "Modelo o refrigerante de exterior incompatible", "configuration", "outdoor"),
        ("P01", "Protección del ventilador interior", "fan", "indoor"),
        ("P03", "Temperatura de descarga del compresor 1", "pressure", "outdoor"),
        ("P04", "Presostato de alta activado", "pressure", "outdoor"),
        ("P05", "Fase invertida o ausente", "power", "outdoor"),
        ("P09", "Protección térmica del ventilador interior", "fan", "indoor"),
        ("P10", "Boya de nivel alto / drenaje", "drain", "indoor"),
        ("P16", "Sobrecorriente del compresor inverter 1", "inverter", "outdoor"),
        ("P17", "Temperatura de descarga del compresor 2", "pressure", "outdoor"),
        ("P18", "Temperatura de descarga del compresor 3", "pressure", "outdoor"),
        ("P22", "Motor de ventilador exterior", "fan", "outdoor"),
        ("P26", "Sobrecorriente de alta frecuencia del compresor inverter", "inverter", "outdoor"),
        ("P29", "Fase ausente o bloqueo del compresor inverter", "compressor", "outdoor"),
    ]
    errors = []
    for code, title, profile, scope in rows:
        ref = "3WAY" if code in {"E24", "E25", "E26", "E29", "H21", "H22", "H23", "H25", "P18"} else "2WAY"
        page = "6-3 a 6-20" if ref == "2WAY" else "5-3 a 5-27"
        behavior = "La unidad afectada se detiene; en 3-WAY ciertos fallos de compresor admiten respaldo automático limitado." if scope != "system" else "La red o el ciclo puede detenerse hasta corregir comunicación, dirección o conteo."
        errors.append(error(code, title, profile, ref, page, "SANYO ECO-i histórica", scope, behavior))
    blink_e06 = led_context("E06", "receptor inalámbrico / PCB exterior", "SANYO ECO-i",
                            "Exterior no recibe comunicación interior",
                            [("LED1", "red", "blink_4"), ("LED2", "red", "blink_6")],
                            "LED1 indica la familia: 4 parpadeos = E; LED2 indica el número: 6 parpadeos = 06.")
    blink_p29 = led_context("P29", "receptor inalámbrico / PCB exterior", "SANYO ECO-i",
                            "Compresor inverter sin fase o bloqueado",
                            [("LED1", "red", "blink_2"), ("LED2", "red", "blink_29")],
                            "LED1: 2 parpadeos = P; LED2: 29 parpadeos = número 29.")
    topics = [
        topic("outdoor_diagnostics", "sanyo-two-led-code", "Tabla de dos pilotos: letra y número",
              "Un piloto codifica la familia E/F/H/L/P y el otro el número.", [
            variant("Ejemplo E06", "Receptor o placa con LED1/LED2 y ciclos separados.", "W2WAY", "3-4",
                    "Convertir parpadeos en código.", "LED1 marca la letra y LED2 el número; espere el ciclo completo.", "SANYO ECO-i", patterns=[blink_e06]),
            variant("Ejemplo P29", "Misma regla visual con 29 destellos en el segundo bloque.", "W2WAY", "3-4",
                    "Evitar contar solo el primer grupo.", "P corresponde al grupo indicado por LED1 y 29 al conteo de LED2.", "SANYO ECO-i", patterns=[blink_p29]),
        ]),
        topic("diagnostic_access", "sanyo-wired-controller", "Obtener alarmas desde mando cableado",
              "La pantalla CHECK muestra código y dirección de unidad.", [
            variant("Alarma activa", "Mando cableado ECO-i con indicación CHECK.", "2WAY", "trouble diagnosis",
                    "Identificar la unidad.", "Anote código, dirección y si parpadean operación y espera.", "SANYO ECO-i", "controller"),
            variant("Modo de servicio del mando", "Mando con botones de inspección y temporizador.", "2WAY", "remote controller servicing functions",
                    "Consultar datos e historial.", "Entre solo con la combinación documentada y recorra unidades sin cambiar ajustes.", "SANYO ECO-i", "controller"),
        ]),
        topic("diagnostic_access", "sanyo-outdoor-pcb", "Lectura desde la PCB exterior",
              "La exterior puede mostrar alarmas que no llegan al mando.", [
            variant("E12 durante direccionamiento", "La dirección automática ya está activa en otra exterior.", "2WAY", "6-9",
                    "Reconocer código no visible en mando.", "El manual indica que E12 se comprueba por parpadeo de la PCB exterior.", "SANYO 2WAY", "outdoor"),
            variant("LED de alarma 1/2", "PCB con dos LED de diagnóstico.", "W2WAY", "3-4",
                    "Leer categoría y número.", "Cuente ambos bloques y repita para confirmar antes de resetear.", "SANYO W-2WAY", "outdoor"),
        ]),
        topic("service_modes", "sanyo-test-run", "Test Run y autodiagnóstico",
              "La puesta en marcha incluye dirección automática y comprobación por unidad.", [
            variant("Test Run desde mando", "Sistema direccionado, válvulas abiertas y sin alarma.", "2WAY", "test run",
                    "Comprobar frío/calor.", "Seleccione modo de prueba y confirme cada interior sin anular protecciones.", "SANYO ECO-i"),
            variant("RUN/STOP de placa", "PCB exterior con pines RUN y STOP.", "W2WAY", "PCB settings",
                    "Probar desde exterior.", "Use los pines solo según el manual y retire el puente al finalizar.", "SANYO W-2WAY", "outdoor"),
        ]),
        topic("configuration", "sanyo-auto-address", "Direccionamiento automático",
              "E12, E15, E16 y E20 describen fases distintas del proceso.", [
            variant("Cantidad esperada", "Selectores S004/S005 en PCB exterior.", "2WAY", "6-9",
                    "Evitar E15/E16.", "Ajuste la cantidad correcta de interiores antes de iniciar.", "SANYO 2WAY", "outdoor"),
            variant("Sin respuesta", "E20 dentro de 90 segundos.", "W2WAY", "5-2",
                    "Localizar pérdida total.", "Compruebe alimentación interior, cable de control y terminador.", "SANYO W-2WAY"),
        ]),
        topic("configuration", "sanyo-eeprom-settings", "Ajustes simples y detallados EEPROM",
              "Capacidad, refrigerante, prioridad y grupo se almacenan en memoria.", [
            variant("Item 04 prioridad", "L05/L06 en control de prioridad.", "W2WAY", "7-12",
                    "Corregir prioridad duplicada.", "Desde el mando de mantenimiento compruebe que solo una interior tenga el valor prioritario.", "SANYO W-2WAY"),
            variant("Items 80 y 81 exterior", "L17 o L10.", "W2WAY", "7-12",
                    "Restaurar refrigerante y capacidad.", "Use el mando de mantenimiento exterior y reinicie interior y exterior tras modificar.", "SANYO W-2WAY", "outdoor"),
        ]),
        topic("controllers_buses", "sanyo-interunit-control", "Bus inter-unit control",
              "La misma red transporta dirección, grupo y alarmas.", [
            variant("E04 frente a E06", "Fallo antes o después de completar la comunicación inicial.", "2WAY", "6-8",
                    "Usar el momento de detección.", "E04 apunta a inicialización no completada; E06 aparece tras haber comunicado correctamente.", "SANYO 2WAY"),
            variant("Mando principal/secundario", "Control de grupo con E09/E11.", "2WAY", "remote controller",
                    "Eliminar duplicados.", "Debe existir un único mando principal por grupo.", "SANYO ECO-i", "controller"),
        ]),
        topic("drainage_overflow", "sanyo-float-sequence", "P10: boya y bomba de drenaje",
              "El nivel alto detiene la interior afectada y conserva la alarma.", [
            variant("Frío y deshumidificación", "Cassette con producción de condensados.", "2WAY", "P10 trouble diagnosis",
                    "Comprobar evacuación bajo carga.", "Revise bomba, boya, tubo y retorno de agua mientras la unidad produce condensación.", "SANYO cassette", "indoor"),
            variant("Boya atascada en calor o parada", "P10 sin condensación esperable.", "2WAY", "P10 trouble diagnosis",
                    "Detectar contacto mecánico.", "Una boya retenida puede activar la protección aunque la bomba no tuviera demanda normal.", "SANYO cassette", "indoor"),
        ]),
        topic("commissioning", "sanyo-commissioning", "Secuencia de puesta en marcha ECO-i",
              "La red debe estar completa antes de direccionar.", [
            variant("Orden de alimentación", "Instalación nueva o ampliada.", "2WAY", "test run",
                    "Permitir reconocimiento.", "Alimente todas las interiores y exteriores y confirme el terminador antes de iniciar dirección automática.", "SANYO ECO-i"),
            variant("Comprobar cantidad", "Termina el direccionamiento.", "2WAY", "6-9",
                    "Detectar unidades ausentes.", "Compare cantidad configurada y detectada; no continúe con E15/E16/E20.", "SANYO ECO-i"),
        ]),
        topic("vrf_network", "sanyo-three-way-backup", "3-WAY: respaldo automático",
              "Algunos fallos de compresor permiten funcionamiento limitado.", [
            variant("Alarmas admitidas", "P16, P22, P26, P29, Hx1, Hx2 o H31.", "3WAY", "5-27",
                    "Mantener servicio provisional.", "El respaldo se activa por entrada del control y limita la operación; no se aplica a comunicación.", "SANYO 3-WAY"),
            variant("Cancelar respaldo", "Componente reparado.", "3WAY", "5-27",
                    "Volver a operación normal.", "El manual exige reiniciar la alimentación de todo el sistema exterior.", "SANYO 3-WAY"),
        ]),
        topic("vrf_network", "sanyo-main-sub", "Exteriores principal y secundarias",
              "Direcciones, terminal y comunicación entre exteriores.", [
            variant("S006/S007", "PCB exterior W-2WAY con selectores de número y rol.", "W2WAY", "PCB settings",
                    "Definir principal/secundaria.", "Copie los ajustes antes de cambiar una PCB y evite dos principales.", "SANYO W-2WAY", "outdoor"),
            variant("Terminal plug", "Varias exteriores enlazadas por S-Net.", "W2WAY", "PCB settings",
                    "Terminar correctamente la red.", "El terminal plug se coloca solo donde indica la topología.", "SANYO W-2WAY", "outdoor"),
        ]),
        topic("technical_values", "sanyo-protection-values", "Umbrales técnicos documentados",
              "Valores concretos del W-2WAY histórico.", [
            variant("P04 alta presión", "W-2WAY con presostato de alta.", "W2WAY", "7-14",
                    "Comparar presión y contacto.", "Actúa a 3,20 MPa y permanece hasta bajar aproximadamente a 2,48 MPa.", "SANYO W-2WAY", "outdoor"),
            variant("P16 sobrecorriente", "Compresor inverter por debajo de 80 Hz.", "W2WAY", "7-15",
                    "Separar DCCT y compresor.", "El manual cita juicio a 13,5 A o más y también falta de corriente por DCCT.", "SANYO W-2WAY", "outdoor"),
            variant("H05/H15/H25", "Sensor de descarga montado en tubo.", "W2WAY", "7-10",
                    "Comprobar montaje térmico.", "Con exterior ≥0 °C se espera cambio superior a 2 K en 10 min; bajo 0 °C, en 30 min.", "SANYO W-2WAY", "outdoor"),
        ]),
        topic("service_tools_boards", "sanyo-service-checker", "Service Checker y mando de mantenimiento",
              "Herramientas históricas para leer unidades y EEPROM.", [
            variant("Service Checker", "Sistema ECO-i con conector de servicio.", "W2WAY", "service checker",
                    "Ver datos por dirección.", "Seleccione la unidad y registre sensores, estados y alarmas sin modificar parámetros.", "SANYO ECO-i"),
            variant("Mando de mantenimiento exterior", "Necesario para items 80/81.", "W2WAY", "7-12",
                    "Restaurar placa exterior.", "Después de cambiar capacidad o refrigerante, reinicie ambos lados del sistema.", "SANYO W-2WAY", "outdoor"),
        ]),
        topic("system_architecture", "sanyo-provenance", "SANYO histórica frente a Panasonic ECOi",
              "La base conserva el origen SANYO del documento y evita mezclar generaciones.", [
            variant("Documento SM830xxx", "Portada y referencias SANYO ECO-i anteriores a la integración.", "2WAY", "portada",
                    "Aceptar la plataforma histórica.", "Los códigos se publican como SANYO histórica aunque el archivo se conserve en Panasonic Pro Club.", "SANYO ECO-i"),
            variant("Equipo Panasonic posterior", "Placa o manual ya identificado solo como Panasonic.", "3WAY", "portada",
                    "No atribuirlo automáticamente a SANYO.", "Use la marca Panasonic de la aplicación salvo que la referencia de plataforma demuestre continuidad.", "Control de procedencia"),
        ]),
    ]
    topics += common_topics("SANYO histórica", "2WAY", "2WAY", "3WAY", "Mini/W-2WAY ECO-i", "2WAY / 3-WAY ECO-i")
    return {
        "slug": "sanyo-historica", "name": "Sanyo", "display_name": "SANYO (histórica)",
        "brand_id": 19, "sources": sources, "errors": errors, "topics": topics,
        "scope": "SANYO ECO-i histórica: W-2WAY, 2WAY y 3-WAY",
        "warning": "Solo para plataformas documentadas como SANYO ECO-i. No aplique estas tablas a cualquier Panasonic posterior por parecido de código.",
        "notes": "SANYO histórica Referencia V1: ECO-i de dos y tres tubos, direccionamiento, mandos, pilotos, respaldo y servicio.",
        "provenance": {
            "policy_version": "1.0", "brand_slug": "sanyo-historica",
            "rule": "Solo se incluyen documentos que conservan identidad SANYO ECO-i verificable.",
            "accepted": [{"family": "W-2WAY, 2WAY y 3-WAY ECO-i", "status": "accepted_historic_sanyo", "source_ref": "2WAY"}],
            "excluded": [{"scope": "plataformas Panasonic posteriores sin evidencia SANYO", "reason": "La similitud de código no acredita el origen."}],
        },
    }


def chigo_config() -> dict[str, Any]:
    sources = {
        "DC25": src("CHIGO DC Inverter Split Service Manual CS25/35", "CHIGO-CS25-35", "https://chigo.bg/dokumenti/Service-manual-CS25-35.pdf", "service_manual", "2016"),
        "DC70": src("CHIGO DC Inverter Split Service Manual CS51/61/70", "CHIGO-CS51-61-70", "https://chigo.bg/dokumenti/Service-manual-CS51-61-70.pdf", "service_manual", "2026"),
        "SERVICE": src("CHIGO Service Documentation", "CHIGO-BG-SERVICE", "https://chigo.bg/en/service-documentation-for-chigo-products/", "official_web", "current"),
        "LEGACY": src("CHIGO Room Air Conditioner Service Manual", "CHIGO-38B-85", "https://chigo.bg/en/service-documentation-for-chigo-products/", "service_manual", "legacy"),
    }
    specs = [
        ("E0", "Tapa o panel no cerrado / configuración de display", "configuration", "Split pared/floor standing", "indoor"),
        ("E1", "Sonda de condensador o sonda exterior según plataforma", "sensor", "Split / exterior", "outdoor"),
        ("E2", "Sonda de ambiente interior o exterior según punto de lectura", "sensor", "Split / exterior", "system"),
        ("E3", "Sonda de batería interior o tubería exterior según plataforma", "sensor", "Split / exterior", "system"),
        ("E4", "Sonda de descarga o protección de temperatura", "sensor", "DC inverter", "outdoor"),
        ("E5", "Motor ventilador interior / protección de corriente según familia", "fan", "Split / inverter", "system"),
        ("E6", "EEPROM / placa electrónica", "pcb", "Split pared", "system"),
        ("E7", "Comunicación interior–exterior", "communication", "DC inverter", "system"),
        ("E8", "Sobretemperatura / protección de sobrecarga", "pressure", "Split pared", "system"),
        ("E9", "Bomba o desbordamiento", "drain", "Cassette / conductos", "indoor"),
        ("EA", "Sensor de corriente o protección exterior", "power", "DC inverter", "outdoor"),
        ("EC", "Fuga de refrigerante o condición de ciclo", "pressure", "DC inverter", "system"),
        ("EE", "Memoria EEPROM exterior", "pcb", "DC inverter", "outdoor"),
        ("EF", "Motor ventilador exterior", "fan", "DC inverter", "outdoor"),
        ("F0", "Protección del módulo inverter", "inverter", "DC inverter", "outdoor"),
        ("F1", "Sensor exterior", "sensor", "DC inverter", "outdoor"),
        ("F2", "Sensor de batería exterior", "sensor", "DC inverter", "outdoor"),
        ("F3", "Sensor de descarga", "sensor", "DC inverter", "outdoor"),
        ("F4", "Sensor de aspiración o tubería", "sensor", "DC inverter", "outdoor"),
        ("F5", "Protección del compresor", "compressor", "DC inverter", "outdoor"),
        ("F6", "Sobrecorriente del inverter", "inverter", "DC inverter", "outdoor"),
        ("F7", "Sobretensión o subtensión", "power", "DC inverter", "outdoor"),
        ("F8", "Temperatura alta del módulo", "inverter", "DC inverter", "outdoor"),
        ("F9", "Fallo de accionamiento/posición del compresor", "compressor", "DC inverter", "outdoor"),
        ("P0", "Protección IPM/inverter", "inverter", "DC inverter", "outdoor"),
        ("P1", "Protección de tensión", "power", "DC inverter", "outdoor"),
        ("P2", "Protección de corriente del compresor", "inverter", "DC inverter", "outdoor"),
        ("P3", "Temperatura exterior o descarga fuera de rango", "pressure", "DC inverter", "outdoor"),
        ("P4", "Protección de alta presión / sobrecarga", "pressure", "DC inverter", "outdoor"),
        ("P5", "Protección de baja presión / falta de refrigerante", "pressure", "DC inverter", "outdoor"),
        ("P6", "Comunicación del módulo inverter", "communication", "DC inverter", "outdoor"),
        ("P7", "Ventilador exterior o disipación", "fan", "DC inverter", "outdoor"),
        ("P8", "Temperatura del disipador", "inverter", "DC inverter", "outdoor"),
        ("P9", "Arranque o bloqueo del compresor", "compressor", "DC inverter", "outdoor"),
        ("PH", "Tensión del bus DC demasiado alta", "power", "DC inverter", "outdoor"),
        ("PL", "Tensión del bus DC demasiado baja", "power", "DC inverter", "outdoor"),
        ("FC", "El compresor no consiguió arrancar tras varios intentos", "compressor", "DC inverter", "outdoor"),
    ]
    errors = []
    for code, title, profile, family, scope in specs:
        ref = "DC25" if code not in {"E0", "E1", "E2", "E3", "E5", "E6", "E8", "E9"} else "SERVICE"
        page = "protecciones y códigos" if ref == "DC25" else "tabla de códigos"
        behavior = "La unidad o el sistema se detiene según la plataforma; confirme display interior, mando o placa exterior." if code != "E9" else "La interior afectada detiene refrigeración y mantiene la gestión de drenaje."
        errors.append(error(code, title, profile, ref, page, family, scope, behavior))
    # Explicitly split ambiguous codes by platform instead of hiding alternatives.
    errors += [
        error("E1", "Sonda de condensador exterior", "sensor", "SERVICE", "tabla de códigos trifásicos", "Chigo trifásica", "outdoor"),
        error("E2", "Sonda de aire exterior", "sensor", "SERVICE", "tabla de códigos trifásicos", "Chigo trifásica", "outdoor"),
        error("E3", "Sonda de tubería exterior", "sensor", "SERVICE", "tabla de códigos trifásicos", "Chigo trifásica", "outdoor"),
        error("E5", "Protección de corriente/compresor exterior", "inverter", "DC70", "protecciones", "Chigo DC inverter grande", "outdoor"),
        error("E8", "Protección de alta temperatura o sobrecarga exterior", "pressure", "DC70", "protecciones", "Chigo DC inverter grande", "outdoor"),
    ]
    e2_led = led_context("E2", "display interior RUN/TIMER", "Chigo split pared",
                         "Sonda de ambiente interior",
                         [("RUN", "green", "blink_1"), ("TIMER", "yellow", "on")],
                         "RUN parpadea una vez por ciclo; TIMER permanece encendido durante 8 s.")
    e9_led = led_context("E9", "display interior RUN/TIMER", "Chigo cassette",
                         "Bomba o desbordamiento",
                         [("RUN", "green", "blink_4"), ("TIMER", "yellow", "on")],
                         "RUN parpadea cuatro veces por ciclo; TIMER permanece encendido durante 8 s.")
    topics = [
        topic("outdoor_diagnostics", "chigo-run-timer-table", "Tabla RUN/TIMER y código de display",
              "El número de destellos y el código LCD son dos representaciones de la misma plataforma.", [
            variant("E2: un destello", "Interior con pilotos RUN y TIMER.", "SERVICE", "tabla de códigos",
                    "Reconocer sonda de ambiente.", "RUN parpadea una vez y el display muestra E2.", "Chigo split pared", "indoor", patterns=[e2_led]),
            variant("E9: cuatro destellos", "Cassette o interior con bomba de condensados.", "SERVICE", "tabla de códigos",
                    "Reconocer desbordamiento.", "RUN parpadea cuatro veces y el display muestra E9.", "Chigo cassette", "indoor", patterns=[e9_led]),
        ]),
        topic("diagnostic_access", "chigo-display-location", "Dónde leer el código Chigo",
              "Display, pilotos y placa exterior pueden usar tablas diferentes.", [
            variant("Display interior", "Split, conductos o cassette con display alfanumérico.", "SERVICE", "tabla de códigos",
                    "Buscar la tabla de interior.", "Anote código, tipo de unidad y estado de RUN/TIMER.", "Chigo"),
            variant("Placa exterior", "DC inverter con LED o display propio.", "DC25", "protecciones",
                    "Buscar la protección exterior.", "No convierta automáticamente P/F de la placa en E del display interior.", "Chigo DC inverter", "outdoor"),
        ]),
        topic("service_modes", "chigo-forced-operation", "Marcha forzada y autocomprobación",
              "La tecla de emergencia cambia de función si se mantiene al alimentar.", [
            variant("Marcha de emergencia", "Pulsador manual en el frontal interior.", "LEGACY", "failure display and emergency key",
                    "Arrancar sin mando.", "Una pulsación permite funcionamiento de emergencia con consignas predeterminadas.", "Chigo split pared", "indoor"),
            variant("Autocomprobación al alimentar", "Pulsador manual mantenido mientras se aplica tensión.", "LEGACY", "self-check program",
                    "Ejecutar secuencia de fábrica.", "El manual diferencia la autocomprobación de la marcha normal; salga cortando y restableciendo como indica.", "Chigo split pared", "indoor"),
        ]),
        topic("configuration", "chigo-controller-code", "Código de mando y receptor",
              "El receptor solo acepta tramas correctas en arranque o espera.", [
            variant("Recepción correcta", "Unidad en arranque o standby y mando compatible.", "DC70", "remote control code",
                    "Separar mando y placa.", "Compruebe pilas, emisor, receptor y código antes de atribuir el fallo a la PCB.", "Chigo split", "controller"),
            variant("Mando universal", "El equipo responde parcialmente o con funciones cambiadas.", "SERVICE", "operating instructions remote control",
                    "Evitar configuraciones erróneas.", "Use el código específico de Chigo y verifique frío, calor, ventilador y apagado.", "Chigo split", "controller"),
        ]),
        topic("controllers_buses", "chigo-communication", "Comunicación interior–exterior",
              "La protección se confirma por tiempo, no por una pérdida instantánea.", [
            variant("Tres minutos anormal", "Código de comunicación en DC inverter.", "DC25", "4.2",
                    "Confirmar fallo persistente.", "Si la comunicación es anormal durante 3 minutos, se detiene el compresor y aparece el código.", "Chigo DC inverter"),
            variant("Recuperación automática", "La señal vuelve a ser normal.", "DC25", "4.2",
                    "Comprobar estabilidad.", "Tras un minuto de comunicación normal, el código desaparece y el sistema puede arrancar automáticamente.", "Chigo DC inverter"),
        ]),
        topic("drainage_overflow", "chigo-e9-overflow", "E9: bomba, boya y desbordamiento",
              "La protección de cassette debe comprobarse también fuera de refrigeración.", [
            variant("Con condensación", "Cassette en frío o deshumidificación.", "SERVICE", "tabla E9",
                    "Comprobar caudal de drenaje.", "Revise bomba, boya, bandeja, elevación y retorno de agua.", "Chigo cassette", "indoor"),
            variant("Boya retenida", "E9 en calor, ventilación o poco después de parar.", "SERVICE", "tabla E9",
                    "Detectar atasco mecánico.", "Compruebe el contacto de la boya al vaciar la bandeja; no sustituya la placa sin probarlo.", "Chigo cassette", "indoor"),
        ]),
        topic("commissioning", "chigo-commissioning", "Puesta en marcha Chigo",
              "Bornes, válvulas, vacío, drenaje y prueba funcional.", [
            variant("Comprobación eléctrica", "Equipo recién instalado.", "DC25", "installation checks",
                    "Evitar E7 y protecciones de red.", "Confirme tensión, tierra, sección, apriete y correspondencia de bornes.", "Chigo"),
            variant("Comprobación frigorífica", "Antes de Test Run.", "DC25", "installation checks",
                    "Evitar E8/EC/P4/P5 falsos.", "Compruebe vacío, estanqueidad, válvulas abiertas y caudal de aire.", "Chigo"),
        ]),
        topic("multisplit", "chigo-multisplit-sensor-scope", "Multisplit: alcance de fallos de sonda",
              "El manual diferencia sensores que paran todo y sensores que aíslan una interior.", [
            variant("Ambiente interior o aire exterior", "Sensor abierto o en corto.", "DC25", "4.1",
                    "Conocer el alcance total.", "La documentación indica que estas averías pueden detener todas las unidades.", "Chigo DC multi"),
            variant("Entrada/salida de evaporador interior", "Fallo en una interior de multisplit.", "DC25", "4.1",
                    "Aislar solo la afectada.", "En multisplit DC, la interior afectada se detiene y muestra su código.", "Chigo DC multi", "indoor"),
        ]),
        topic("component_checks", "chigo-pg-fan", "Motor interior PG y realimentación",
              "La placa vigila pulsos del motor antes de declarar fallo.", [
            variant("Sin feedback durante 20 s", "Motor PG ordenado en marcha.", "DC25", "4.3",
                    "Confirmar falta de pulsos.", "Compruebe bloqueo, alimentación, sensor Hall/PG y cable durante el intervalo de detección.", "Chigo DC inverter", "indoor"),
            variant("Motor gira pero da E5", "Hay movimiento sin realimentación válida.", "DC25", "4.3",
                    "Separar potencia y feedback.", "Mida por separado salida de motor y retorno de velocidad.", "Chigo DC inverter", "indoor"),
        ]),
        topic("technical_values", "chigo-sensor-values", "Valores de sondas y tiempos",
              "Referencias concretas de los manuales Chigo.", [
            variant("Sonda interior 5 kΩ", "Plataforma 38B/85 de split pared.", "LEGACY", "30",
                    "Comprobar E2/E3.", "El manual cita aproximadamente 5 kΩ a 25 °C para ambiente y batería de esa familia.", "Chigo 38B/85", "indoor"),
            variant("Comunicación 3 min / recuperación 1 min", "DC inverter.", "DC25", "4.2",
                    "Distinguir corte breve y fallo.", "La parada se declara tras 3 min anormales; recupera después de 1 min normal.", "Chigo DC inverter"),
            variant("Feedback de ventilador 20 s", "Motor PG interior.", "DC25", "4.3",
                    "Interpretar E5.", "La ausencia continua de feedback durante 20 s activa la lógica de protección.", "Chigo DC inverter", "indoor"),
        ]),
        topic("service_tools_boards", "chigo-board-identification", "Identificar placa Chigo",
              "La referencia de placa y el punto de lectura ayudan a escoger tabla.", [
            variant("Prefijos ZKFR / ZGHT", "Serigrafía de PCB claramente visible.", "SERVICE", "documentación de producto",
                    "Relacionar placa con fabricante.", "Use el identificador OEM integrado y después confirme la familia por conectores y display.", "Chigo"),
            variant("Después de cambiar PCB", "Placa compatible pero comportamiento distinto.", "DC25", "PCB function",
                    "Restaurar configuración.", "Copie jumpers, capacidad y opciones; repita autocomprobación y prueba funcional.", "Chigo"),
        ]),
        topic("system_architecture", "chigo-platform-warning", "No existe una única tabla Chigo",
              "E1, E2, E3, E5 y E8 cambian según familia y punto de lectura.", [
            variant("Split convencional", "Display interior E0–E9 y pilotos RUN/TIMER.", "SERVICE", "tabla de códigos",
                    "Usar significados de interior.", "Abra todas las interpretaciones del código y elija por tipo de equipo y punto de lectura.", "Chigo split"),
            variant("DC inverter / trifásica", "Placa exterior con códigos F/P o tabla propia E.", "DC70", "protecciones",
                    "Usar significados de exterior.", "No oculte una variante solo porque el display interior muestra el mismo carácter.", "Chigo DC inverter", "outdoor"),
        ]),
    ]
    topics += common_topics("Chigo", "DC25", "SERVICE", "DC70", "Split pared / cassette", "DC inverter / multisplit")
    return {
        "slug": "chigo", "name": "Chigo", "display_name": "Chigo",
        "brand_id": 20, "sources": sources, "errors": errors, "topics": topics,
        "scope": "Chigo split, cassette, DC inverter y multisplit documentados",
        "warning": "Los códigos Chigo cambian entre split convencional, inverter, trifásica y punto de lectura. Revise todas las interpretaciones.",
        "notes": "Chigo Referencia V1: códigos alternativos por plataforma, pilotos, comunicación temporizada, drenaje, servicio y valores.",
    }


CONFIG_FACTORIES = {
    "hitachi": hitachi_config,
    "sharp": sharp_config,
    "sanyo-historica": sanyo_config,
    "chigo": chigo_config,
}


def source_record(config: dict[str, Any], ref: str, page: str, section_name: str) -> dict[str, Any]:
    row = config["sources"][ref]
    return {
        "title": row["title"], "document_ref": row["document_ref"], "source_url": row["source_url"],
        "page_start": page, "page_end": page, "section": section_name,
    }


def build_interpretation(config: dict[str, Any], ident: int, spec: dict[str, Any]) -> dict[str, Any]:
    profile = PROFILES[spec["profile"]]
    info = [
        {"id": ident * 100 + 1, "item_type": "machine_behavior", "title": None, "body": spec["behavior"], "sort_order": 1, "review_status": "reviewed", "origin_ref": config["sources"][spec["source_ref"]]["document_ref"]},
        {"id": ident * 100 + 2, "item_type": "related_element", "title": None, "body": spec["title"], "sort_order": 2, "review_status": "reviewed", "origin_ref": config["sources"][spec["source_ref"]]["document_ref"]},
    ]
    for cause in profile["causes"]:
        info.append({"id": ident * 100 + len(info) + 1, "item_type": "cause", "title": None, "body": cause, "sort_order": len(info) + 1, "review_status": "reviewed", "origin_ref": config["sources"][spec["source_ref"]]["document_ref"]})
    for check in profile["checks"]:
        info.append({"id": ident * 100 + len(info) + 1, "item_type": "check", "title": None, "body": check, "sort_order": len(info) + 1, "review_status": "reviewed", "origin_ref": config["sources"][spec["source_ref"]]["document_ref"]})
    info.append({"id": ident * 100 + len(info) + 1, "item_type": "observation", "title": "Precaución", "body": profile["note"], "sort_order": len(info) + 1, "review_status": "reviewed", "origin_ref": config["sources"][spec["source_ref"]]["document_ref"]})
    default_context = {
        "code_display": spec["code"], "code_normalized": normalize(spec["code"]), "indication_type": spec["indication"],
        "display_location": "unidad o sistema", "family_hint": spec["family"],
        "relationship": "Código documentado para esta familia y punto de lectura.",
        "source_ref": spec["source_ref"], "source_document_ref": config["sources"][spec["source_ref"]]["document_ref"],
        "related_error_id": None,
    }
    contexts = [default_context, *spec["contexts"]]
    source_data = source_record(config, spec["source_ref"], spec["page"], f'Tabla de códigos — {spec["code"]}')
    return {
        "id": ident, "title": spec["title"], "description": f'{spec["code"]} en {spec["family"]}: {spec["title"]}.',
        "source_kind": "official", "confidence": "high", "review_status": "reviewed",
        "indication_contexts": contexts, "info_items": info,
        "operational_impacts": [{
            "stop_level": "warning" if spec["profile"] == "normal" else ("unit" if spec["scope"] in {"indoor", "outdoor"} else "system"),
            "summary": spec["behavior"], "affected_scope": f'Alcance documentado para {spec["family"]}.',
            "unaffected_scope": "No se presupone continuidad de otras unidades si la fuente no lo especifica.",
            "restart_behavior": "Corrija la causa y rearme únicamente con el procedimiento de esta familia.",
            "degraded_behavior": None, "notes": "No extrapolar el alcance a otra plataforma con el mismo código.",
        }],
        "datasets": [{
            "id": ident * 10 + 1, "name": f'{spec["code"]} — referencia técnica',
            "dataset_type": "technical_reference", "variable_name": "Comprobación", "variable_unit": None,
            "value_name": "Dato", "value_unit": None, "tolerance_text": f'Aplicar solo a {spec["family"]}.',
            "source_kind": "official", "calculation_method": None, "review_status": "reviewed",
            "notes": spec["technical"], "visible": 1,
            "points": [{"variable_value": None, "value_min": None, "value_nominal": None, "value_max": None, "value_text": spec["technical"], "sort_order": 1, "notes": None}],
            "sources": [source_record(config, spec["source_ref"], spec["page"], f'Valor técnico — {spec["code"]}')],
        }],
        "sources": [source_data],
    }


def build_errors(config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for spec in config["errors"]:
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
            interpretations.append(build_interpretation(config, interpretation_id, spec))
            interpretation_id += 1
        tags = sorted({
            token.lower() for spec in specs
            for token in normalize(f'{spec["title"]} {spec["family"]} {spec["profile"]}').split()
            if len(token) > 2
        })
        detail = {
            "id": error_id, "code_display": primary["code"], "code_normalized": key,
            "indication_type": "mixed" if len({x["indication"] for x in specs}) > 1 else primary["indication"],
            "unit_scope": "system" if len({x["scope"] for x in specs}) > 1 else primary["scope"],
            "short_label": primary["title"],
            "aliases": [{"alias_display": value, "alias_normalized": normalize(value)} for value in aliases],
            "tags": tags, "interpretations": interpretations, "media": [],
        }
        index_rows.append({
            "id": error_id, "code_display": primary["code"], "code_normalized": key,
            "indication_type": detail["indication_type"], "unit_scope": detail["unit_scope"],
            "short_label": primary["title"], "aliases": aliases, "tags": tags,
            "search_text": normalize(" ".join([primary["code"], *aliases, *tags, *(x["title"] for x in specs), *(x["family"] for x in specs)])),
            "interpretation_count": len(interpretations),
        })
        detail_rows.append(detail)
    return index_rows, detail_rows


def hydrate_topics(config: dict[str, Any]) -> list[dict[str, Any]]:
    category_map = {
        slug: {"id": ident, "slug": slug, "name": name, "description": description}
        for ident, (slug, name, description) in enumerate(CATEGORIES, start=1)
    }
    result, variant_id = [], 1
    for topic_id, spec in enumerate(config["topics"], start=1):
        cat = category_map[spec["category"]]
        variants = []
        for sort_order, row in enumerate(spec["variants"], start=1):
            hydrated = {**row, "id": variant_id, "topic_id": topic_id, "sort_order": sort_order, "visible": 1}
            hydrated["sources"] = [
                source_record(config, source["source_ref"], source["page"], row["title"])
                for source in row["sources"]
            ]
            variants.append(hydrated)
            variant_id += 1
        result.append({
            "id": topic_id, "brand_id": config["brand_id"], "category_id": cat["id"],
            "slug": spec["slug"], "title": spec["title"], "summary": spec["summary"],
            "active": 1, "category": cat, "variants": variants,
        })
    return result


def build_search(error_index: list[dict[str, Any]], details: list[dict[str, Any]], topics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    detail_by_id = {row["id"]: row for row in details}
    entries = []
    for row in error_index:
        detail = detail_by_id[row["id"]]
        parts = [row["code_display"], row["short_label"], *row["aliases"], *row["tags"]]
        for interpretation in detail["interpretations"]:
            parts.extend([interpretation["title"], interpretation["description"]])
            parts.extend(item["body"] for item in interpretation["info_items"])
            for context in interpretation["indication_contexts"]:
                parts.extend(str(context.get(key, "")) for key in ("display_location", "family_hint", "relationship", "counting_rule", "cycle_note", "sequence"))
                for led in context.get("led_indicators", []):
                    parts.extend([led.get("label", ""), led.get("color", ""), led.get("state", "")])
        entries.append({
            "type": "error", "id": row["id"], "code": row["code_display"], "title": row["short_label"],
            "subtitle": f'{row["interpretation_count"]} interpretación(es)', "haystack": normalize(" ".join(parts)),
        })
    for row_topic in topics:
        for row in row_topic["variants"]:
            parts = [row_topic["title"], row_topic["summary"], row["title"], row["recognition"], row["purpose"], row["summary"], row["system_type"]]
            parts.extend(section["body"] for section in row["sections"])
            parts.extend(step["instruction"] for step in row["steps"])
            for pattern in row.get("led_patterns", []):
                parts.extend([pattern.get("code_display", ""), pattern.get("relationship", ""), pattern.get("family_hint", ""), pattern.get("counting_rule", "")])
                for led in pattern.get("led_indicators", []):
                    parts.extend([led.get("label", ""), led.get("color", ""), led.get("state", "")])
            if row.get("controller"):
                parts.extend(str(value or "") for value in row["controller"].values())
            entries.append({
                "type": "variant", "id": row["id"], "topic_id": row_topic["id"],
                "title": row["title"], "subtitle": row_topic["title"], "haystack": normalize(" ".join(parts)),
            })
    return entries


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")


def build_one(slug: str) -> dict[str, int]:
    config = CONFIG_FACTORIES[slug]()
    brand_dir = ROOT / "data" / "brands" / slug
    web_dir = brand_dir / "web"
    if brand_dir.exists():
        shutil.rmtree(brand_dir)
    web_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    error_index, details = build_errors(config)
    topics = hydrate_topics(config)
    search = build_search(error_index, details, topics)
    write_json(web_dir / "errors" / "index.json", error_index)
    for row in details:
        write_json(web_dir / "errors" / "details" / f'{row["id"]}.json', row)
    for row in topics:
        write_json(web_dir / "topics" / f'{row["id"]}.json', row)
    write_json(web_dir / "search.json", search)
    write_json(web_dir / "variant_map.json", {str(row["id"]): item["id"] for item in topics for row in item["variants"]})
    by_category: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for item in topics:
        by_category[item["category_id"]].append({
            "id": item["id"], "slug": item["slug"], "title": item["title"], "summary": item["summary"],
            "active": 1, "variant_count": len(item["variants"]),
        })
    # "Errores" se mantiene porque la interfaz lo alimenta desde errors/index.json.
    # Las demás categorías sin documentación se omiten para no presentar menús vacíos.
    active_category_ids = {1, *by_category.keys()}
    nav_categories = []
    for ident, (category_slug, name, description) in enumerate(CATEGORIES, start=1):
        if ident not in active_category_ids:
            continue
        nav_categories.append({
            "id": ident, "slug": category_slug, "name": name, "description": description,
            "sort_order": ident * 10, "active": 1, "topics": by_category[ident],
        })
    write_json(web_dir / "navigation.json", {
        "metadata": {
            "schema_name": "Super Tecnico", "navigation_model": "brand_category_topic_variant",
            "schema_version": "2.3.0", "data_version": "1.0.0", "last_update_utc": now,
            "reference_brand": config["display_name"], "verification_warning": config["warning"],
        },
        "categories": nav_categories,
    })
    write_json(web_dir / "sources.json", [
        {
            "id": ident, "brand_id": config["brand_id"], "title": row["title"],
            "document_ref": row["document_ref"], "document_type": row["type"],
            "publication_date": row["year"], "language": row["language"],
            "source_url": row["source_url"], "status": "reviewed",
            "notes": f'Fuente revisada para {config["display_name"]} Referencia V1.',
        }
        for ident, row in enumerate(config["sources"].values(), start=1)
    ])
    write_json(web_dir / "coverage.json", [
        {
            "id": ident, "brand_id": config["brand_id"], "area_slug": category_slug, "area_name": name,
            "equipment_scope": config["scope"], "coverage_status": "reference_v1",
            "source_count": len(config["sources"]), "notes": description, "last_reviewed": "2026-07-29",
        }
        for ident, (category_slug, name, description) in enumerate(CATEGORIES, start=1)
        if ident in active_category_ids
    ])
    if config.get("provenance"):
        write_json(web_dir / "provenance.json", config["provenance"])
    counts = {
        "categories": len(nav_categories), "topics": len(topics),
        "variants": sum(len(item["variants"]) for item in topics),
        "errors": len(error_index), "search_entries": len(search),
    }
    write_json(brand_dir / "brand.json", {
        "slug": slug, "name": config["name"], "display_name": config["display_name"],
        "enabled": True, "web_data": "web", "media": "media", "publish_media": False,
        "static_site": True, "schema_version": "2.3.0", "data_version": "1.0.0",
        "exported_at_utc": now, "counts": counts, "notes": config["notes"],
    })
    write_quality(web_dir / "quality.json", audit_brand(brand_dir))
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("brands", nargs="*", choices=sorted(CONFIG_FACTORIES), default=list(CONFIG_FACTORIES))
    args = parser.parse_args()
    result = {slug: build_one(slug) for slug in args.brands}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
