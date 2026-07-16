#!/usr/bin/env python3
"""Enriquece los subcódigos AIRSTAGE VR-II con datos del manual de servicio.

El documento del fabricante está consultado mediante un visor público. Solo se
publican resúmenes técnicos, valores y referencias de página; no se copian sus
imágenes ni el manual.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from audit_brand_quality import audit_brand, write as write_json


ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "data" / "brands" / "fujitsu-general"
WEB = BRAND / "web"
DETAILS = WEB / "errors" / "details"
ORIGIN = "AIRSTAGE_VRII_SERVICE"
MANUAL_TITLE = "Service Manual — Fujitsu AIRSTAGE VR-II Series"
MANUAL_ROOT = "https://www.manualslib.com/manual/1612084/Fujitsu-Airstage-Vr-Ii-Series.html"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(value: str) -> str:
    value = "".join(
        char for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    ).upper()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9]+", " ", value)).strip()


def source(page: int, section: str, manual_page: str | None = None) -> dict[str, Any]:
    if manual_page is None:
        manual_page = f"04-{page - 84:02d}"
    return {
        "title": MANUAL_TITLE,
        "document_ref": ORIGIN,
        "source_url": f"{MANUAL_ROOT}?page={page}",
        "page_start": manual_page,
        "page_end": manual_page,
        "section": section,
    }


THERMISTOR_A = [
    (0, 168.6), (5, 129.8), (10, 100.9), (15, 79.1), (20, 62.6),
    (25, 49.8), (30, 40.0), (40, 26.3), (50, 17.8), (60, 12.3),
    (70, 8.7), (80, 6.3), (90, 4.6), (100, 3.4), (110, 2.6), (120, 2.0),
]
THERMISTOR_B = [
    (-10, 27.8), (-5, 21.0), (0, 16.1), (5, 12.4), (10, 9.6),
    (15, 7.6), (20, 6.0), (25, 4.8), (30, 3.8), (40, 2.5),
    (50, 1.7), (60, 1.2),
]
THERMISTOR_C = [
    (-20, 105.4), (-10, 58.2), (-5, 44.0), (0, 33.6), (5, 25.9),
    (10, 20.2), (15, 15.8), (20, 12.5), (25, 10.0), (30, 8.0),
    (40, 5.3), (50, 3.6),
]
THERMISTOR_D = [
    (-10, 27.4), (-5, 20.7), (0, 15.8), (5, 12.2), (10, 9.5),
    (15, 7.5), (20, 5.9), (25, 4.7), (30, 3.8), (40, 2.5),
    (50, 1.7), (60, 1.2), (70, 0.8), (80, 0.6), (90, 0.4), (100, 0.3),
]
DISCHARGE_PRESSURE = [
    (0.0, 0.50), (0.1, 0.58), (0.2, 0.66), (0.3, 0.74), (0.4, 0.82),
    (0.5, 0.90), (0.7, 1.06), (0.8, 1.14), (0.9, 1.22), (1.0, 1.30),
    (1.2, 1.46), (1.4, 1.62), (1.6, 1.78), (1.8, 1.94), (2.0, 2.10),
    (2.2, 2.26), (2.4, 2.42), (2.6, 2.58), (2.8, 2.74), (3.0, 2.90),
    (3.2, 3.06), (3.4, 3.22), (3.6, 3.38), (3.8, 3.54), (4.0, 3.70),
    (4.2, 3.86), (4.4, 4.02), (4.6, 4.18), (4.8, 4.34), (5.0, 4.50),
]
SUCTION_PRESSURE = [
    (0.0, 0.50), (0.1, 0.68), (0.2, 0.85), (0.3, 1.03), (0.4, 1.21),
    (0.5, 1.38), (0.7, 1.74), (0.8, 1.91), (0.9, 2.09), (1.0, 2.27),
    (1.1, 2.44), (1.2, 2.62), (1.3, 2.79), (1.4, 2.97), (1.5, 3.15),
    (1.6, 3.32), (1.7, 3.50),
]


def curve(name: str, points: list[tuple[float, float]], dataset_id: int) -> dict[str, Any]:
    return {
        "id": dataset_id,
        "name": name,
        "dataset_type": "sensor_curve",
        "variable_name": "Temperatura",
        "variable_unit": "°C",
        "value_name": "Resistencia",
        "value_unit": "kΩ",
        "tolerance_text": None,
        "source_kind": "official",
        "calculation_method": None,
        "review_status": "reviewed",
        "notes": "Valores transcritos de la tabla de termistores del manual VR-II. Use únicamente la curva que corresponda físicamente a la sonda instalada.",
        "visible": 1,
        "points": [
            {
                "variable_value": temperature,
                "value_min": None,
                "value_nominal": resistance,
                "value_max": None,
                "value_text": None,
                "sort_order": order,
                "notes": None,
            }
            for order, (temperature, resistance) in enumerate(points)
        ],
        "sources": [source(206, "Service Parts Information 25 — Thermistor", "04-117")],
        "origin_ref": ORIGIN,
    }


def pressure_curve(name: str, points: list[tuple[float, float]], dataset_id: int) -> dict[str, Any]:
    return {
        "id": dataset_id,
        "name": name,
        "dataset_type": "sensor_curve",
        "variable_name": "Presión",
        "variable_unit": "MPa",
        "value_name": "Tensión de salida",
        "value_unit": "V CC",
        "tolerance_text": None,
        "source_kind": "official",
        "calculation_method": None,
        "review_status": "reviewed",
        "notes": "Medir con el sensor conectado entre los pines de señal y masa indicados en la ficha.",
        "visible": 1,
        "points": [
            {
                "variable_value": pressure,
                "value_min": None,
                "value_nominal": voltage,
                "value_max": None,
                "value_text": None,
                "sort_order": order,
                "notes": None,
            }
            for order, (pressure, voltage) in enumerate(points)
        ],
        "sources": [source(205, "Service Parts Information 23 — Pressure sensors", "04-116")],
        "origin_ref": ORIGIN,
    }


def value_dataset(
    dataset_id: int,
    name: str,
    variable_name: str,
    value_name: str,
    points: list[dict[str, Any]],
    page: int,
    manual_page: str,
    section: str,
    units: tuple[str | None, str | None] = (None, None),
    notes: str | None = None,
) -> dict[str, Any]:
    return {
        "id": dataset_id,
        "name": name,
        "dataset_type": "technical_values",
        "variable_name": variable_name,
        "variable_unit": units[0],
        "value_name": value_name,
        "value_unit": units[1],
        "tolerance_text": None,
        "source_kind": "official",
        "calculation_method": None,
        "review_status": "reviewed",
        "notes": notes,
        "visible": 1,
        "points": points,
        "sources": [source(page, section, manual_page)],
        "origin_ref": ORIGIN,
    }


SENSORS = {
    77: dict(page=128, label="temperatura de descarga 1", connector="CN162, pines 1-2", board="PCB principal", curves=[("Termistor A VR-II", THERMISTOR_A)], behavior="El cortocircuito se detecta directamente; el circuito abierto se confirma después de que el compresor 1 haya funcionado continuamente durante al menos 5 minutos."),
    78: dict(page=129, label="temperatura del compresor 1", connector="CN162, pines 3-4", board="PCB principal", curves=[("Termistor A VR-II", THERMISTOR_A)], behavior="El cortocircuito se detecta directamente; el circuito abierto se confirma después de que el compresor 1 haya funcionado continuamente durante al menos 5 minutos."),
    79: dict(page=130, label="gas del intercambiador exterior 1", connector="CN163, pines 3-4", board="PCB principal", curves=[("Termistor B VR-II", THERMISTOR_B)], behavior="La placa detecta circuito abierto o cortocircuito en la sonda de gas del intercambiador exterior 1."),
    80: dict(page=131, label="líquido del intercambiador exterior 1", connector="CN163, pines 1-2", board="PCB principal", curves=[("Termistor B VR-II", THERMISTOR_B)], behavior="La placa detecta circuito abierto o cortocircuito en la sonda de líquido del intercambiador exterior 1."),
    81: dict(page=132, label="gas del intercambiador exterior 2", connector="CN164, pines 3-4", board="PCB principal", curves=[("Termistor B VR-II", THERMISTOR_B)], behavior="La placa detecta circuito abierto o cortocircuito en la sonda de gas del intercambiador exterior 2."),
    82: dict(page=133, label="líquido del intercambiador exterior 2", connector="CN164, pines 1-2", board="PCB principal", curves=[("Termistor B VR-II", THERMISTOR_B)], behavior="La placa detecta circuito abierto o cortocircuito en la sonda de líquido del intercambiador exterior 2."),
    83: dict(page=134, label="aire exterior", connector="CN144, pines 1-3", board="PCB principal", curves=[("Termistor B VR-II", THERMISTOR_B), ("Termistor C VR-II", THERMISTOR_C)], behavior="La placa detecta circuito abierto o cortocircuito en la sonda de temperatura exterior. El manual contempla dos curvas para esta función según la variante física de sonda."),
    84: dict(page=135, label="gas de aspiración", connector="CN165, pines 1-3", board="PCB principal", curves=[("Termistor B VR-II", THERMISTOR_B)], behavior="La placa detecta circuito abierto o cortocircuito en la sonda de temperatura de gas de aspiración."),
    85: dict(page=136, label="disipador del inverter", connector="CN360, pines 1-2", board="PCB inverter", curves=[("Termistor D VR-II", THERMISTOR_D)], behavior="La PCB inverter detecta circuito abierto o cortocircuito en la sonda del disipador."),
    86: dict(page=137, label="salida de gas del subenfriador", connector="CN142, pines 7-8", board="PCB principal", curves=[("Termistor B VR-II", THERMISTOR_B)], behavior="La placa detecta circuito abierto o cortocircuito en la sonda de salida de gas del intercambiador de subenfriamiento."),
    87: dict(page=138, label="tubería de líquido 1", connector="CN142, pines 1-2", board="PCB principal", curves=[("Termistor B VR-II", THERMISTOR_B)], behavior="La placa detecta circuito abierto o cortocircuito en la sonda de tubería de líquido 1."),
    88: dict(page=139, label="tubería de líquido 2", connector="CN142, pines 3-4", board="PCB principal", curves=[("Termistor B VR-II", THERMISTOR_B)], behavior="La placa detecta circuito abierto o cortocircuito en la sonda de tubería de líquido 2."),
}


ENRICHMENTS: dict[int, dict[str, Any]] = {
    69: dict(
        page=120,
        description="La protección de secuencia de fases detecta fase invertida al alimentar o una entrada de red anormal/fase abierta después del arranque.",
        related=["Alimentación trifásica y orden de fases", "PCB de filtro principal", "PCB principal exterior"],
        causes=["Orden de fases invertido, fase ausente o conductor de alimentación abierto.", "Caída de tensión, microcorte o ruido eléctrico.", "Defecto de la PCB de filtro principal o de la PCB principal exterior."],
        checks=["Comprobar tensión de red, presencia de las tres fases, secuencia y continuidad del cableado.", "Revisar puesta a tierra, microcortes y equipos próximos capaces de introducir ruido.", "Si la alimentación es correcta, comprobar la PCB de filtro principal y la PCB principal según la sección de componentes del manual."],
        behavior=["La detección actúa al alimentar si la secuencia está invertida y también después del arranque si aparece una fase abierta."],
    ),
    70: dict(
        page=121,
        description="La PCB principal exterior no puede acceder correctamente a su memoria EEPROM después de iniciar la unidad.",
        related=["EEPROM y PCB principal exterior"],
        causes=["Ruido eléctrico, caída de tensión o microcorte.", "Fallo de acceso a la EEPROM o defecto de la PCB principal."],
        checks=["Cortar y restablecer la alimentación para comprobar si el error reaparece.", "Revisar microcortes, cargas grandes en el mismo circuito, puesta a tierra y fuentes de ruido.", "Si se repite, sustituir la PCB principal y restaurar la dirección/configuración original."],
        behavior=["El código se registra cuando falla el acceso a EEPROM después de que la unidad exterior haya arrancado."],
    ),
    71: dict(
        page=122,
        description="La PCB principal exterior deja de recibir comunicación de la PCB inverter durante 10 segundos o más.",
        related=["PCB principal exterior", "PCB inverter", "Cableado de comunicación entre ambas placas"],
        causes=["Ruido eléctrico.", "Conector suelto o cable abierto entre PCB principal y PCB inverter.", "PCB principal o PCB inverter defectuosa."],
        checks=["Reiniciar y comprobar si el error vuelve.", "Revisar tierra y posibles fuentes de ruido próximas a la alimentación.", "Comprobar conectores, continuidad y estado del cableado entre PCB principal e inverter.", "Comprobar la PCB principal; si está correcta, sustituir la PCB inverter."],
        behavior=["Se genera cuando no se recibe comunicación desde la PCB inverter durante 10 segundos o más."],
        impacts=[dict(stop_level="degraded", summary="Puede existir funcionamiento de respaldo solo en sistemas con varias exteriores.", affected_scope="Unidad exterior cuyo inverter no comunica", unaffected_scope="Otra unidad exterior activa del mismo sistema, si la configuración lo permite", restart_behavior="Corregir la causa y restablecer la configuración normal.", degraded_behavior="El manual permite activar respaldo con DIP SW 4-2 únicamente si existe otra exterior activa; no es válido en una exterior independiente.", notes="El respaldo reduce prestaciones, puede acortar la vida del compresor activo y no debe mantenerse durante largo tiempo.")],
    ),
    72: dict(
        page=123,
        description="La suma de comprobación calculada con los ajustes leídos no coincide con la almacenada en la EEPROM exterior.",
        related=["EEPROM", "Ajustes F2", "PCB principal exterior"],
        causes=["Corrupción de los ajustes almacenados.", "Ruido, caída de tensión o microcorte durante el acceso a memoria.", "PCB principal defectuosa."],
        checks=["Ejecutar el borrado completo de ajustes de campo F3-35, cortar alimentación y volver a alimentar.", "Reconfigurar los ajustes F2 y comprobar si el error reaparece.", "Revisar tierra, microcortes y fuentes de ruido.", "Si persiste, sustituir la PCB principal y restaurar la dirección/configuración original."],
        behavior=["La protección compara la suma memorizada con la calculada a partir de los ajustes F2 leídos de EEPROM."],
    ),
    73: dict(
        page=124,
        description="La PCB principal recibe una condición de error procedente de la PCB inverter.",
        related=["PCB inverter", "PCB principal", "PCB de filtro inverter", "Relé magnético y resistencia de cemento"],
        causes=["Ruido, caída de tensión o microcorte.", "Cableado de potencia o comunicación abierto entre filtro, inverter y PCB principal.", "Circuito del relé magnético defectuoso.", "Resistencia de cemento abierta.", "PCB principal, filtro inverter o PCB inverter defectuosa."],
        checks=["Comprobar si también aparecen E67.2 o E68.2 y seguir primero su diagnóstico específico.", "Revisar conectores y continuidad de potencia y comunicación.", "Medir la resistencia de cemento: el manual indica 5,3 a 6,0 Ω.", "Comprobar las placas de filtro e inverter según la sección de componentes."],
        behavior=["E63.1 agrupa información de error recibida desde la PCB inverter; puede aparecer simultáneamente con la detección de interrupción o la protección de la resistencia de irrupción."],
        datasets=[dict(name="Resistencia de cemento del inverter", variable_name="Componente", value_name="Resistencia", units=(None, "Ω"), points=[dict(variable_value="Resistencia de cemento", value_min=5.3, value_nominal=None, value_max=6.0, value_text=None, sort_order=0, notes=None)], page=124, manual_page="04-40", section="Trouble shooting 31 — Inverter Error")],
    ),
    74: dict(
        page=125,
        description="La PCB inverter comunica una interrupción corta de su alimentación o circuito de potencia.",
        related=["PCB inverter", "PCB principal", "Relé magnético del inverter", "Cableado de potencia"],
        causes=["Ruido, microcorte o caída de tensión.", "Cableado abierto en la bobina del relé magnético o en la alimentación del filtro/inverter.", "PCB principal o PCB inverter defectuosa."],
        checks=["Comprobar tensión, microcortes, puesta a tierra y ruido.", "Revisar conector y continuidad de la bobina del relé magnético.", "Revisar el cableado de potencia entre filtro inverter y PCB inverter.", "Comprobar PCB principal y, si es correcta, sustituir PCB inverter."],
        behavior=["El código aparece cuando la PCB principal recibe la señal de 'short interruption' desde la PCB inverter."],
    ),
    75: dict(
        page=126,
        description="La protección por calentamiento de la resistencia limitadora de corriente de irrupción se ha generado dos veces.",
        related=["Relé magnético del inverter", "PCB principal", "PCB inverter", "Cableado CN138-CN330"],
        causes=["Cableado abierto en la bobina del relé magnético.", "Alimentación o circuito de activación del relé defectuoso.", "Cableado entre PCB principal e inverter abierto.", "Salida de la PCB principal o PCB inverter defectuosa."],
        checks=["Revisar conectores y continuidad de la bobina del relé y de la alimentación del inverter.", "Comprobar la orden de 12 V CC del circuito de activación según el diagrama del manual.", "Comprobar el cableado entre CN138 de la PCB principal y CN330 de la PCB inverter.", "Comprobar 208-230 V CA en CN130 de la PCB principal.", "Después de reparar y reiniciar alimentación, ejecutar Error Reset F3-40."],
        behavior=["El error se fija después de dos paradas por detección de temperatura elevada en la resistencia limitadora de irrupción."],
        impacts=[dict(stop_level="permanent_stop", summary="Requiere recuperación manual tras corregir la causa.", affected_scope="Unidad exterior afectada", unaffected_scope="Otra exterior activa puede asumir respaldo en un sistema múltiple compatible", restart_behavior="Reiniciar alimentación y ejecutar Error Reset F3-40 después de reparar.", degraded_behavior="Respaldo mediante DIP SW 4-2 solo si existe otra exterior activa.", notes="No es aplicable a una exterior independiente y no debe usarse como solución prolongada.")],
    ),
    76: dict(
        page=127,
        description="La comunicación paralela entre la PCB principal exterior y la PCB de transmisión se reinicia repetidamente por encima del límite admitido.",
        related=["PCB de transmisión exterior", "PCB principal exterior", "Conector entre placas"],
        causes=["Ruido eléctrico.", "Conexión floja entre la PCB de transmisión y la PCB principal.", "PCB de transmisión o PCB principal defectuosa."],
        checks=["Reiniciar y comprobar si reaparece.", "Revisar puesta a tierra y fuentes de ruido.", "Comprobar el asiento del conector y daños visibles en la PCB de transmisión.", "Sustituir primero la PCB de transmisión; si continúa, sustituir la PCB principal restaurando los ajustes originales."],
        behavior=["Si ocurre en una exterior esclava, E69.1 se transmite a los dispositivos de la red.", "Si ocurre en la exterior maestra, las interiores pueden mostrar 14/14.3 y Service Tool 14.1 por pérdida de comunicación exterior."],
    ),
    89: dict(
        page=140,
        description="La lectura del sensor de corriente del inverter es incoherente con el estado o la velocidad del compresor.",
        related=["Sensor de corriente integrado en PCB de filtro inverter", "PCB de filtro inverter", "PCB inverter", "Cableado CT y de potencia"],
        causes=["Alimentación o cable de potencia defectuoso.", "Conector/cableado del sistema CT abierto entre filtro e inverter.", "Cableado de potencia entre filtro e inverter abierto.", "PCB de filtro inverter o PCB inverter defectuosa."],
        checks=["Comprobar alimentación, fusibles y continuidad del cable de potencia.", "Revisar conectores y continuidad del cableado CT entre filtro e inverter.", "Revisar el cableado de potencia entre ambas placas.", "Comprobar las placas de filtro e inverter según la sección de componentes.", "Después de reparar y reiniciar alimentación, ejecutar Error Reset F3-40."],
        behavior=["Se detecta una lectura de 0 A mientras el inverter trabaja a 20 rps durante 1 minuto, o una lectura máxima con el inverter detenido; la protección debe producirse dos veces para fijar el error."],
        replace_impacts=True,
        impacts=[dict(stop_level="permanent_stop", summary="La protección queda bloqueada hasta realizar el reset técnico.", affected_scope="Unidad exterior y circuito frigorífico asociado", unaffected_scope="Otra exterior activa puede trabajar en respaldo si el sistema múltiple lo permite", restart_behavior="Corregir la causa, reiniciar alimentación y ejecutar Error Reset F3-40.", degraded_behavior="Respaldo con DIP SW 4-2 solo en sistema con otra exterior activa.", notes="El respaldo no es posible en una exterior independiente y no debe prolongarse.")],
    ),
    90: dict(
        page=141,
        description="La señal del sensor de presión de descarga queda fuera del rango eléctrico válido después del arranque de la alimentación.",
        related=["Sensor de presión de descarga", "CN118", "PCB principal exterior"],
        causes=["Conector desconectado o cable abierto.", "Sensor de presión defectuoso.", "Entrada analógica o alimentación de 5 V de la PCB principal defectuosa."],
        checks=["Revisar conector y continuidad del sensor.", "Comparar la tensión de salida con la tabla presión-tensión oficial.", "Con el sensor desconectado, comprobar 5,0 V CC entre los pines 1-3 de CN118.", "Si no aparecen 5 V, sustituir la PCB principal y restaurar sus ajustes."],
        behavior=["Treinta segundos después de alimentar, la lógica comprueba los umbrales eléctricos anómalos de 0,3 V mantenidos durante 30 s y 5,0 V indicados por el manual."],
        pressure_curve=("Sensor de presión de descarga VR-II", DISCHARGE_PRESSURE),
    ),
    91: dict(
        page=142,
        description="La señal del sensor de presión de aspiración queda fuera del rango eléctrico válido después del arranque de la alimentación.",
        related=["Sensor de presión de aspiración", "CN119", "PCB principal exterior"],
        causes=["Conector desconectado o cable abierto.", "Sensor de presión defectuoso.", "Entrada analógica o alimentación de 5 V de la PCB principal defectuosa."],
        checks=["Revisar conector y continuidad del sensor.", "Comparar la tensión de salida con la tabla presión-tensión oficial.", "Con el sensor desconectado, comprobar 5,0 V CC entre los pines 1-3 de CN119.", "Si no aparecen 5 V, sustituir la PCB principal y restaurar sus ajustes."],
        behavior=["Treinta segundos después de alimentar, la lógica comprueba los umbrales eléctricos anómalos de 0,06 V mantenidos durante 30 s y 5,0 V indicados por el manual."],
        pressure_curve=("Sensor de presión de aspiración VR-II", SUCTION_PRESSURE),
    ),
    92: dict(
        page=143,
        description="El presostato de alta 1 se detecta abierto durante la puesta en tensión.",
        related=["Presostato de alta 1", "Cableado del presostato", "PCB principal exterior"],
        causes=["Conector suelto o cable abierto.", "Presostato fuera de características.", "Circuito de entrada de la PCB principal defectuoso."],
        checks=["Comprobar conexión y continuidad del cableado.", "Verificar el cambio de contacto con los umbrales oficiales del presostato.", "Si cableado y presostato son correctos, sustituir la PCB principal y restaurar sus ajustes."],
        behavior=["La placa genera el error si detecta abierto el presostato de alta 1 al alimentar."],
        datasets=[dict(name="Presostato de alta 1 — umbrales", variable_name="Transición", value_name="Presión", units=(None, "MPa"), points=[dict(variable_value="Cerrado → abierto", value_min=4.1, value_nominal=4.2, value_max=4.3, value_text="609 ± 14,5 psi", sort_order=0, notes=None), dict(variable_value="Abierto → cerrado", value_min=3.05, value_nominal=3.2, value_max=3.35, value_text="464 ± 21,8 psi", sort_order=1, notes=None)], page=206, manual_page="04-117", section="Service Parts Information 24 — Pressure switch")],
    ),
    93: dict(
        page=144,
        description="Se repiten las paradas por sobrecorriente durante el arranque del compresor inverter hasta alcanzar el límite de bloqueo.",
        related=["Compresor inverter", "PCB inverter", "Cableado U-V-W"],
        causes=["Cableado entre PCB inverter y compresor suelto o abierto.", "PCB inverter defectuosa.", "Compresor bloqueado o bobinado en cortocircuito."],
        checks=["Revisar conexiones y continuidad entre inverter y compresor.", "Comprobar la PCB inverter según Service Parts Information 4.", "Medir bobinados y comprobar bloqueo mecánico del compresor.", "Después de reparar y reiniciar, ejecutar Error Reset F3-40."],
        behavior=["La protección cuenta 60 reinicios consecutivos por sobrecorriente en dos series (120 en total); el tiempo mínimo hasta fijar el error es de unos 130 minutos.", "No reinicia si ninguna interior del circuito tiene demanda y no inicia la segunda serie hasta que todos los compresores del circuito se hayan detenido temporalmente."],
        impacts=[dict(stop_level="permanent_stop", summary="El compresor queda bloqueado tras alcanzar el límite de reintentos.", affected_scope="Compresor y unidad exterior afectados", unaffected_scope="Otra exterior activa puede asumir respaldo en un sistema múltiple compatible", restart_behavior="Corregir la causa, reiniciar alimentación y ejecutar Error Reset F3-40.", degraded_behavior="Respaldo con DIP SW 4-2 solo si existe otra exterior activa.", notes="No usar el respaldo durante periodos prolongados.")],
    ),
    94: dict(
        page=145,
        description="El inverter detecta sobrecorriente cinco veces consecutivas después de completar el arranque del compresor.",
        related=["Ventilador e intercambiador exterior", "PCB inverter", "Compresor inverter"],
        causes=["Paso de aire obstruido, batería sucia, ventilador defectuoso o recirculación de descarga.", "Temperatura ambiente elevada por otras fuentes.", "PCB inverter defectuosa.", "Compresor bloqueado o con bobinado en cortocircuito."],
        checks=["Comprobar obstáculos, limpieza de batería, ventilador y recirculación de aire.", "Comprobar la PCB inverter.", "Medir bobinados y comprobar bloqueo mecánico del compresor.", "Después de reparar y reiniciar, ejecutar Error Reset F3-40."],
        behavior=["Se fija tras cinco paradas consecutivas por sobrecorriente después del arranque; el contador se reinicia si pasan 40 s tras un rearranque sin nueva protección."],
        impacts=[dict(stop_level="permanent_stop", summary="La unidad queda bloqueada al repetirse cinco disparos consecutivos.", affected_scope="Compresor y unidad exterior afectados", unaffected_scope="Otra exterior activa puede asumir respaldo si el sistema lo permite", restart_behavior="Corregir la causa, reiniciar alimentación y ejecutar Error Reset F3-40.", degraded_behavior="Respaldo limitado mediante DIP SW 4-2 en sistemas múltiples.", notes="No disponible en una exterior independiente.")],
    ),
    95: dict(
        page=146,
        description="La PCB inverter pierde la sincronización del motor del compresor cinco veces consecutivas.",
        related=["PCB inverter", "Compresor inverter"],
        causes=["PCB inverter defectuosa.", "Compresor bloqueado o con problema mecánico."],
        checks=["Comprobar la PCB inverter según la sección de componentes.", "Comprobar bloqueo y estado eléctrico/mecánico del compresor.", "Después de reparar y reiniciar, ejecutar Error Reset F3-40."],
        behavior=["Se fija después de cinco pérdidas de sincronismo consecutivas; el contador vuelve a cero si transcurren 40 s después del rearranque sin nueva detección."],
        impacts=[dict(stop_level="permanent_stop", summary="El compresor queda bloqueado tras cinco pérdidas de sincronismo.", affected_scope="Compresor y exterior afectados", unaffected_scope="Otra exterior activa puede asumir respaldo si el sistema múltiple lo permite", restart_behavior="Corregir la causa, reiniciar alimentación y ejecutar Error Reset F3-40.", degraded_behavior="Respaldo mediante DIP SW 4-2 solo con otra exterior activa.", notes="No válido para una exterior independiente.")],
    ),
    96: dict(
        page=147,
        description="El ventilador exterior no alcanza 100 rpm dentro de los 20 segundos posteriores a su arranque.",
        related=["Motor ventilador exterior", "PCB driver", "PCB principal", "Fusible de ventilador 5 A"],
        causes=["Aspas bloqueadas por un objeto.", "Conector, cableado o fusible de 5 A abierto.", "Motor bloqueado o bobinado abierto.", "PCB driver o PCB principal defectuosa."],
        checks=["Girar el ventilador a mano y retirar obstáculos.", "Revisar conectores, continuidad y fusible de 5 A.", "Medir bobinados y realizar la prueba del motor indicada en Service Parts Information 22.", "Sustituir primero la PCB driver y probar; si persiste, sustituir/configurar la PCB principal.", "Después de reparar y reiniciar, ejecutar Error Reset F3-40."],
        behavior=["Cada detección detiene ventilador y compresor; si se repite cuatro veces consecutivas después de los rearranques, ambos quedan detenidos permanentemente."],
        impacts=[dict(stop_level="permanent_stop", summary="Tras cuatro repeticiones se detienen permanentemente ventilador y compresor.", affected_scope="Unidad exterior afectada", unaffected_scope="Otra exterior activa puede mantener respaldo en un sistema múltiple compatible", restart_behavior="Corregir la causa, reiniciar alimentación y ejecutar Error Reset F3-40.", degraded_behavior="Respaldo con DIP SW 4-2 solo con otra exterior activa.", notes=None)],
    ),
    97: dict(
        page=148,
        description="El motor ventilador exterior no puede trabajar a 470 rpm o más y la protección térmica se repite.",
        related=["Ventilador exterior", "PCB driver", "Intercambiador", "Ajuste de presión estática"],
        causes=["Ventilador bloqueado por un objeto.", "Intercambiador obstruido o recirculación de aire caliente.", "Temperatura ambiente excesiva.", "Presión estática ajustada por encima del valor permitido.", "PCB driver defectuosa."],
        checks=["Comprobar giro libre del ventilador.", "Limpiar la batería y eliminar obstrucciones/recirculación.", "Comprobar temperatura ambiente y fuentes de calor próximas.", "Revisar el ajuste y el valor real de presión estática.", "Comprobar montaje de la PCB driver, sustituirla y verificar con Test Run.", "Después de reparar y reiniciar, ejecutar Error Reset F3-40."],
        behavior=["La primera detección detiene ventilador y compresor. Si vuelve a no alcanzar 470 rpm o se repite tres veces dentro de 60 minutos, ambos quedan detenidos permanentemente."],
        impacts=[dict(stop_level="permanent_stop", summary="Tres repeticiones en 60 minutos provocan parada permanente.", affected_scope="Ventilador, compresor y exterior afectados", unaffected_scope="Otra exterior activa puede mantener respaldo si la configuración lo permite", restart_behavior="Corregir la causa, reiniciar alimentación y ejecutar Error Reset F3-40.", degraded_behavior="Respaldo limitado en sistemas con varias exteriores.", notes=None)],
    ),
    98: dict(
        page=149,
        description="La PCB driver del ventilador informa de fallo propio, fallo de motor, salida CC anormal o pérdida de conexión.",
        related=["PCB driver de ventilador", "Motor ventilador", "PCB principal", "CN759 y fusible 5 A"],
        causes=["PCB driver defectuosa.", "Motor ventilador con cortocircuito entre espiras.", "Salida de 15 V CC de la PCB principal anormal.", "Conector/cableado suelto o abierto."],
        checks=["Revisar cableado motor-driver, driver-condensador y principal-driver, además del fusible de 5 A.", "Comprobar en CN759 una entrada de 15 V CC ±10 %; si es anormal, sustituir/configurar la PCB principal.", "Sustituir la PCB driver y verificar mediante Test Run.", "Medir bobinados del motor; sustituirlo si el fallo reaparece.", "Después de reparar y reiniciar, ejecutar Error Reset F3-40."],
        behavior=["La PCB driver genera la señal de error ante fallo de driver, cortocircuito interno del motor, salida CC anormal de la principal o pérdida de cableado."],
        datasets=[dict(name="Alimentación de la PCB driver de ventilador", variable_name="Punto", value_name="Tensión", units=(None, "V CC"), points=[dict(variable_value="CN759", value_min=13.5, value_nominal=15.0, value_max=16.5, value_text="15 V ±10 %", sort_order=0, notes=None)], page=149, manual_page="04-65", section="Trouble shooting 56 — Fan Motor Driver Abnormal")],
    ),
    102: dict(
        page=153,
        description="La unidad maestra recibe una señal de error desde una unidad exterior esclava del mismo circuito frigorífico.",
        related=["Unidad exterior maestra", "Unidad exterior esclava", "Display de 7 segmentos y Service Tool"],
        causes=["Existe una avería activa en una exterior esclava; E9U.2 no identifica por sí solo la causa primaria."],
        checks=["Leer el display de 7 segmentos de la unidad esclava.", "Consultar en Service Tool el código concreto que conserva la unidad esclava.", "Aplicar el diagnóstico correspondiente al código primario, no sustituir componentes basándose únicamente en E9U.2."],
        behavior=["E9U.2 aparece únicamente en la exterior maestra; la esclava y Service Tool muestran el código de error real que originó la señal."],
    ),
    103: dict(
        page=154,
        description="La temperatura de descarga del compresor 1 alcanza 115 °C y la parada de protección se repite dos veces dentro de 40 minutos.",
        related=["Sonda de descarga 1", "EEV y filtros", "Circuito frigorífico", "Ventilador/intercambiador exterior"],
        causes=["Válvula de servicio de 3 vías cerrada.", "EEV defectuosa o filtro/strainer obstruido.", "Ventilación exterior deficiente o batería obstruida.", "Sonda de descarga defectuosa.", "Falta de refrigerante."],
        checks=["Confirmar que la válvula de 3 vías está completamente abierta.", "Comprobar EEV1, EEV2, EEV3 y filtros; en frío también la EEV interior.", "Comprobar ventilador, paso de aire y limpieza del intercambiador.", "Comparar la sonda de descarga con la curva Termistor A.", "Buscar fugas y verificar la carga de refrigerante.", "Después de reparar y reiniciar, ejecutar Error Reset F3-40."],
        behavior=["Cada vez que la sonda alcanza 115 °C durante el funcionamiento del compresor 1 se produce una parada; dos paradas en 40 minutos fijan el código."],
        replace_impacts=True,
        impacts=[dict(stop_level="permanent_stop", summary="Dos protecciones por 115 °C en 40 minutos bloquean la exterior.", affected_scope="Compresor 1 y unidad exterior afectada", unaffected_scope="Otra exterior activa puede trabajar en respaldo en un sistema múltiple compatible", restart_behavior="Eliminar la causa, reiniciar alimentación y ejecutar Error Reset F3-40.", degraded_behavior="Respaldo por DIP SW 4-2 solo si existe otra exterior activa.", notes="El respaldo puede reducir prestaciones y no debe mantenerse a largo plazo.")],
        datasets=[dict(name="Umbral de protección de descarga 1", variable_name="Condición", value_name="Temperatura", units=(None, "°C"), points=[dict(variable_value="Parada de protección", value_min=None, value_nominal=115.0, value_max=None, value_text="239 °F", sort_order=0, notes="Dos detecciones dentro de 40 minutos fijan el error.")], page=154, manual_page="04-70", section="Trouble shooting 61 — Discharge Temperature 1 Abnormal")],
    ),
    104: dict(
        page=155,
        description="La temperatura de carcasa del compresor 1 alcanza 115 °C y la parada de protección se repite dos veces dentro de 40 minutos.",
        related=["Sonda de temperatura del compresor 1", "EEV y filtros", "Circuito frigorífico", "Ventilador/intercambiador exterior"],
        causes=["Válvula de servicio de 3 vías cerrada.", "EEV defectuosa o filtro obstruido.", "Ventilación exterior deficiente o batería obstruida.", "Sonda de compresor defectuosa.", "Falta de refrigerante."],
        checks=["Confirmar que la válvula de 3 vías está abierta.", "Comprobar EEV y filtros; en frío también la EEV interior.", "Comprobar ventilador, paso de aire y limpieza del intercambiador.", "Comparar la sonda del compresor con la curva Termistor A.", "Buscar fugas y verificar la carga de refrigerante.", "Después de reparar y reiniciar, ejecutar Error Reset F3-40."],
        behavior=["Cada vez que la sonda alcanza 115 °C durante el funcionamiento del compresor 1 se produce una parada; dos paradas en 40 minutos fijan el código."],
        datasets=[dict(name="Umbral de protección de temperatura del compresor 1", variable_name="Condición", value_name="Temperatura", units=(None, "°C"), points=[dict(variable_value="Parada de protección", value_min=None, value_nominal=115.0, value_max=None, value_text="239 °F", sort_order=0, notes="Dos detecciones dentro de 40 minutos fijan el error.")], page=155, manual_page="04-71", section="Trouble shooting 62 — Compressor 1 Temperature Abnormal")],
    ),
    105: dict(
        page=156,
        description="El sensor de descarga detecta presión igual o superior a 4,00 MPa durante el funcionamiento y la protección se repite tres veces dentro de 60 minutos.",
        related=["Sensor de presión de descarga", "EEV y filtros", "Válvulas de 3 y 4 vías", "Ventilador/intercambiador exterior", "Carga de refrigerante"],
        causes=["Válvula de 3 vías cerrada.", "Ventilador defectuoso, batería obstruida, alta temperatura o recirculación.", "EEV/filtro, válvula solenoide o válvula de 4 vías defectuosa.", "Sensor de descarga defectuoso.", "Exceso de refrigerante."],
        checks=["Confirmar la apertura de la válvula de 3 vías.", "Comprobar ventilador, batería, temperatura ambiente y recirculación.", "Comprobar EEV/filtros, válvulas solenoides y válvulas de 4 vías según el modo frío/calor.", "Comparar el sensor con la curva presión-tensión.", "Verificar que la carga de refrigerante no sea excesiva."],
        behavior=["La protección actúa a 4,00 MPa (580 psi) durante el funcionamiento de cualquier compresor; tres detecciones en 60 minutos fijan el código."],
        datasets=[dict(name="Umbral de alta presión por sensor", variable_name="Condición", value_name="Presión", units=(None, "MPa"), points=[dict(variable_value="Parada de protección", value_min=None, value_nominal=4.0, value_max=None, value_text="580 psi", sort_order=0, notes="Tres detecciones dentro de 60 minutos fijan el error.")], page=156, manual_page="04-72", section="Trouble shooting 63 — High Pressure Abnormal")],
    ),
    106: dict(
        page=157,
        description="El presostato de alta 1 actúa durante el funcionamiento del compresor 1 y la protección se repite tres veces dentro de 60 minutos.",
        related=["Presostato de alta 1", "EEV y filtros", "Válvulas de 3 y 4 vías", "Válvulas solenoides y antirretorno", "Carga de refrigerante"],
        causes=["Válvula de 3 vías cerrada.", "Ventilador defectuoso, batería obstruida, alta temperatura o recirculación.", "EEV/filtro, válvula de 4 vías, solenoide o antirretorno defectuosos.", "Presostato de alta fuera de características.", "Exceso de refrigerante."],
        checks=["Confirmar la apertura de la válvula de 3 vías.", "Comprobar ventilador, batería, temperatura ambiente y recirculación.", "Comprobar EEV/filtros y válvulas según el modo de trabajo.", "Comprobar la válvula antirretorno de salida del separador de aceite del compresor 1.", "Verificar el presostato con sus umbrales de apertura/cierre.", "Verificar la carga de refrigerante."],
        behavior=["Tres actuaciones del presostato de alta 1 durante el funcionamiento del compresor 1 dentro de 60 minutos fijan el código."],
    ),
    107: dict(
        page=158,
        description="La presión de aspiración permanece demasiado baja y la protección se repite cinco veces dentro de 3 horas.",
        related=["Sensor de presión de aspiración", "EEV y filtros", "Válvulas de 3 y 4 vías", "Circuito frigorífico"],
        causes=["Válvula de 3 vías cerrada.", "Temperatura exterior por debajo del rango en calefacción.", "Ventilador/batería exterior defectuosos u obstruidos.", "EEV, filtro o solenoide defectuosos.", "Válvula de 4 vías defectuosa.", "Sensor de baja fuera de características o falta de refrigerante."],
        checks=["Confirmar la apertura de la válvula de 3 vías.", "En calefacción, verificar rango de temperatura exterior y funcionamiento de ventilador/batería.", "Comprobar EEV y filtros: interior en frío, exteriores en calor.", "Comprobar solenoide y válvula de 4 vías.", "Comparar el sensor con la curva presión-tensión.", "Buscar fugas y verificar carga.", "Después de reparar y reiniciar, ejecutar Error Reset F3-40."],
        behavior=["La protección usa 0,10 MPa mantenidos durante 10 minutos o 0,05 MPa durante el funcionamiento de cualquier compresor; cinco detecciones en 3 horas fijan el error."],
        impacts=[dict(stop_level="permanent_stop", summary="Cinco protecciones de baja presión en 3 horas bloquean la unidad.", affected_scope="Circuito frigorífico y exterior afectados", unaffected_scope=None, restart_behavior="Eliminar la causa, reiniciar alimentación y ejecutar Error Reset F3-40.", degraded_behavior=None, notes=None)],
        datasets=[dict(name="Umbrales de protección de baja presión", variable_name="Condición", value_name="Presión", units=(None, "MPa"), points=[dict(variable_value="Presión baja mantenida 10 min", value_min=None, value_nominal=0.10, value_max=None, value_text="15 psi", sort_order=0, notes=None), dict(variable_value="Presión mínima con compresor en marcha", value_min=None, value_nominal=0.05, value_max=None, value_text="7,25 psi", sort_order=1, notes=None)], page=158, manual_page="04-74", section="Trouble shooting 65 — Low Pressure Abnormal")],
    ),
    108: dict(
        page=159,
        description="La sonda de gas del intercambiador 1, usado como condensador, queda anormalmente fría respecto a la temperatura de saturación de alta durante al menos 4 minutos.",
        related=["Sonda TH7", "Válvula de 4 vías 1", "EEV1", "PCB principal"],
        causes=["Sonda TH7 mal colocada o defectuosa.", "Bobina/válvula de 4 vías 1 defectuosa.", "EEV1 o su bobina defectuosa.", "PCB principal defectuosa."],
        checks=["Comprobar fijación y posición de TH7.", "Comparar TH7 con la curva Termistor B.", "Comprobar montaje de bobinas de las válvulas de 4 vías.", "Comprobar bobina/conector de EEV1 y conectores de EEV1-EEV3.", "Comprobar PCB principal y, si procede, sustituir/configurar.", "Si se sustituye la válvula de 4 vías, recuperar refrigerante, hacer vacío y reponer la cantidad recuperada.", "Después de reparar y reiniciar, ejecutar Error Reset F3-40."],
        behavior=["Con la batería 1 actuando como condensador (4WV1 OFF y EEV1 abierta), la diferencia anómala respecto a la saturación de alta mantenida 4 minutos genera el error."],
    ),
    109: dict(
        page=160,
        description="La sonda de gas del intercambiador 2, usado como condensador, queda anormalmente fría respecto a la temperatura de saturación de alta durante al menos 4 minutos.",
        related=["Sonda TH8", "Válvula de 4 vías 2", "EEV2", "PCB principal"],
        causes=["Sonda TH8 mal colocada o defectuosa.", "Bobina/válvula de 4 vías 2 defectuosa.", "EEV2 o su bobina defectuosa.", "PCB principal defectuosa."],
        checks=["Comprobar fijación y posición de TH8.", "Comparar TH8 con la curva Termistor B.", "Comprobar montaje de bobinas de las válvulas de 4 vías.", "Comprobar bobina/conector de EEV2 y conectores de EEV1-EEV3.", "Comprobar PCB principal y, si procede, sustituir/configurar.", "Si se sustituye la válvula de 4 vías, recuperar refrigerante, hacer vacío y reponer la cantidad recuperada.", "Después de reparar y reiniciar, ejecutar Error Reset F3-40."],
        behavior=["Con la batería 2 actuando como condensador (4WV2 OFF y EEV2 abierta), la diferencia anómala respecto a la saturación de alta mantenida 4 minutos genera el error."],
    ),
    110: dict(
        page=161,
        description="La temperatura del disipador alcanza 91 °C y la parada de protección se repite tres veces dentro de 60 minutos.",
        related=["Disipador de potencia", "Sonda del disipador", "Intercambiador y ventilación exterior"],
        causes=["Disipador sucio u obstruido.", "Intercambiador exterior obstruido, temperatura ambiente alta o recirculación.", "Sonda del disipador defectuosa."],
        checks=["Limpiar y comprobar el disipador.", "Limpiar la batería, comprobar paso de aire, fuentes de calor y recirculación.", "Comparar la sonda con la curva Termistor D."],
        behavior=["Cada detección a 91 °C produce una parada de protección; tres detecciones dentro de 60 minutos fijan el código."],
        datasets=[dict(name="Umbral de temperatura del disipador", variable_name="Condición", value_name="Temperatura", units=(None, "°C"), points=[dict(variable_value="Parada de protección", value_min=None, value_nominal=91.0, value_max=None, value_text="195,8 °F", sort_order=0, notes="Tres detecciones dentro de 60 minutos fijan el error.")], page=161, manual_page="04-77", section="Trouble shooting 68 — Heat Sink Temperature Abnormal")],
    ),
}


def add_eev(error_id: int, page: int, connector: str, number: int) -> None:
    ENRICHMENTS[error_id] = dict(
        page=page,
        description=f"La PCB principal detecta circuito abierto en el driver o bobina de la válvula de expansión exterior EEV{number}.",
        related=[f"Bobina EEV{number}", f"Conector {connector}", "PCB principal exterior", "Cableado de la válvula"],
        causes=[f"Conector {connector} flojo.", "Cable cortado, pellizcado o dañado.", "Bobina de EEV abierta o fuera de valor.", "Salida de 12 V CC de la PCB principal anormal.", "Ruido, microcorte o caída de tensión."],
        checks=[f"Comprobar el asiento del conector {connector} y el estado del cable.", "Medir cada devanado de la bobina respecto al hilo rojo: 46 ±4 Ω (ohmios) a 20 °C.", f"Con la bobina desconectada, comprobar 12 V CC entre el pin 1 de {connector} y el pin 2 de CN132 (GND).", "Si falta la salida de 12 V, sustituir la PCB principal; si el devanado es anormal, sustituir la bobina."],
        behavior=[f"El código se genera cuando el circuito driver de la bobina EEV{number} se detecta abierto."],
        datasets=[dict(name=f"Bobina EEV{number} exterior", variable_name="Medición", value_name="Resistencia", units=(None, "Ω"), points=[dict(variable_value="Cada devanado respecto al hilo rojo", value_min=42.0, value_nominal=46.0, value_max=50.0, value_text="46 ±4 Ω a 20 °C", sort_order=0, notes=None)], page=196 + number, manual_page=f"04-{107 + number}", section=f"Service Parts Information {14 + number} — Outdoor EEV{number}")],
    )


add_eev(99, 150, "CN116", 1)
add_eev(100, 151, "CN117", 2)
add_eev(101, 152, "CN160", 3)


def sensor_enrichment(error_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "page": spec["page"],
        "description": f"La placa detecta la sonda de {spec['label']} abierta o en cortocircuito.",
        "related": [f"Sonda de {spec['label']}", "Cableado y conector", spec["board"]],
        "causes": ["Conector suelto o cable abierto.", "Sonda abierta, en cortocircuito o fuera de curva.", f"Circuito de lectura/alimentación de {spec['board']} defectuoso."],
        "checks": [f"Comprobar conexión y continuidad en {spec['connector']}.", "Desconectar la sonda y comparar su resistencia con la curva oficial aplicable.", f"Con la sonda desconectada, comprobar aproximadamente 5,0 V CC en {spec['connector']}.", f"Si no aparece la alimentación de 5 V, sustituir {spec['board']} y restaurar sus ajustes cuando corresponda."],
        "behavior": [spec["behavior"]],
        "curves": spec["curves"],
    }


for sensor_error_id, sensor_spec in SENSORS.items():
    ENRICHMENTS[sensor_error_id] = sensor_enrichment(sensor_error_id, sensor_spec)


def build_items(error_id: int, enrichment: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    order = 0
    for item_type, key in (
        ("related_element", "related"),
        ("cause", "causes"),
        ("check", "checks"),
        ("machine_behavior", "behavior"),
        ("observation", "observations"),
        ("safety", "safety"),
    ):
        for body in enrichment.get(key, []):
            rows.append({
                "id": 10000 + error_id * 100 + order,
                "item_type": item_type,
                "title": None,
                "body": body,
                "sort_order": order,
                "review_status": "reviewed",
                "origin_ref": ORIGIN,
            })
            order += 1
    return rows


def build_datasets(error_id: int, enrichment: dict[str, Any]) -> list[dict[str, Any]]:
    datasets: list[dict[str, Any]] = []
    base_id = 2000 + error_id * 10
    for index, (name, points) in enumerate(enrichment.get("curves", [])):
        datasets.append(curve(name, points, base_id + index))
    if enrichment.get("pressure_curve"):
        name, points = enrichment["pressure_curve"]
        datasets.append(pressure_curve(name, points, base_id + len(datasets)))
    for spec in enrichment.get("datasets", []):
        datasets.append(value_dataset(
            base_id + len(datasets),
            spec["name"],
            spec["variable_name"],
            spec["value_name"],
            spec["points"],
            spec["page"],
            spec["manual_page"],
            spec["section"],
            spec.get("units", (None, None)),
            spec.get("notes"),
        ))
    return datasets


def build_impacts(error_id: int, enrichment: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": 2000 + error_id * 10 + index,
            **impact,
            "review_status": "reviewed",
            "origin_ref": ORIGIN,
        }
        for index, impact in enumerate(enrichment.get("impacts", []))
    ]


def refresh_search() -> None:
    index_path = WEB / "errors" / "index.json"
    index = load(index_path)
    by_id = {int(row["id"]): row for row in index}
    search_path = WEB / "search.json"
    search = load(search_path)
    search_by_id = {
        int(row["id"]): row for row in search if row.get("type") == "error"
    }

    for error_id, row in by_id.items():
        detail = load(DETAILS / f"{error_id}.json")
        text: list[str] = [
            str(detail.get("code_display") or ""),
            str(detail.get("code_normalized") or ""),
            str(detail.get("short_label") or ""),
        ]
        for alias in detail.get("aliases") or []:
            text.extend([str(alias.get("alias_display") or ""), str(alias.get("alias_normalized") or "")])
        for interpretation in detail.get("interpretations") or []:
            text.extend([str(interpretation.get("title") or ""), str(interpretation.get("description") or "")])
            text.extend(str(item.get("body") or "") for item in interpretation.get("info_items") or [])
            for impact in interpretation.get("operational_impacts") or []:
                text.extend(str(impact.get(key) or "") for key in ("summary", "affected_scope", "unaffected_scope", "restart_behavior", "degraded_behavior", "notes"))
            for dataset in interpretation.get("datasets") or []:
                text.extend([str(dataset.get("name") or ""), str(dataset.get("notes") or "")])
        row["interpretation_count"] = len(detail.get("interpretations") or [])
        row["search_text"] = normalize(" ".join(text))

        search_row = search_by_id.get(error_id)
        if search_row is not None:
            search_row["title"] = detail.get("short_label")
            first = (detail.get("interpretations") or [{}])[0]
            search_row["summary"] = first.get("description") or detail.get("short_label")
            search_row["haystack"] = row["search_text"]

    write_json(index_path, index)
    write_json(search_path, search)


def main() -> int:
    if set(ENRICHMENTS) != set(range(69, 111)):
        missing = sorted(set(range(69, 111)) - set(ENRICHMENTS))
        extra = sorted(set(ENRICHMENTS) - set(range(69, 111)))
        raise RuntimeError(f"Mapa VR-II incompleto. Faltan={missing}; sobran={extra}")

    for error_id, enrichment in sorted(ENRICHMENTS.items()):
        path = DETAILS / f"{error_id}.json"
        detail = load(path)
        interpretations = detail.get("interpretations") or []
        if len(interpretations) != 1:
            raise RuntimeError(f"El subcódigo {error_id} no tiene una interpretación única")
        interpretation = interpretations[0]
        interpretation["description"] = enrichment["description"]
        interpretation["info_items"] = [
            row for row in interpretation.get("info_items") or []
            if row.get("origin_ref") != ORIGIN
        ] + build_items(error_id, enrichment)
        interpretation["datasets"] = [
            row for row in interpretation.get("datasets") or []
            if row.get("origin_ref") != ORIGIN
            and not any(src.get("document_ref") == ORIGIN for src in row.get("sources") or [])
        ] + build_datasets(error_id, enrichment)

        if enrichment.get("replace_impacts"):
            interpretation["operational_impacts"] = []
        else:
            interpretation["operational_impacts"] = [
                row for row in interpretation.get("operational_impacts") or []
                if row.get("origin_ref") != ORIGIN
            ]
        interpretation["operational_impacts"] += build_impacts(error_id, enrichment)

        interpretation["sources"] = [
            row for row in interpretation.get("sources") or []
            if row.get("document_ref") != ORIGIN
        ]
        page = int(enrichment["page"])
        interpretation["sources"].append(source(page, f"Trouble shooting {page - 93}"))
        write_json(path, detail)

    sources_path = WEB / "sources.json"
    sources = [row for row in load(sources_path) if row.get("document_ref") != ORIGIN]
    sources.append({
        "id": 15,
        "title": MANUAL_TITLE,
        "document_ref": ORIGIN,
        "publication_date": None,
        "language": "en",
        "document_type": "service_manual",
        "source_url": MANUAL_ROOT,
        "status": "reviewed",
        "notes": "Documento técnico del fabricante conservado en un archivo público. Se han resumido las páginas de diagnóstico 04-36 a 04-77 y las tablas de componentes 04-108 a 04-117; no se publican páginas ni imágenes del manual.",
    })
    write_json(sources_path, sources)

    coverage_path = WEB / "coverage.json"
    coverage = load(coverage_path)
    source_count = len(sources)
    for row in coverage:
        row["source_count"] = source_count
        if row.get("area_slug") == "errors":
            row["coverage_status"] = "partial"
            row["notes"] = "Los 42 subcódigos exteriores VR-II disponen de causas, comprobaciones y comportamiento documentado. Siguen pendientes de desarrollar códigos de mando y otros subcódigos VRF que solo están enumerados por manuales de instalación."
        elif row.get("area_slug") == "component_checks":
            row["notes"] = "Incluye curvas de termistores y presión, presostato, EEV, ventilador, inverter y valores asociados; falta ampliar componentes de otras generaciones."
    write_json(coverage_path, coverage)

    config_path = BRAND / "brand.json"
    config = load(config_path)
    config["data_version"] = "2.7.0"
    config["notes"] = "Fujitsu V2 en reconstrucción: 42 subcódigos AIRSTAGE VR-II enriquecidos desde manual de servicio con diagnóstico, reacción de la máquina y valores técnicos."
    write_json(config_path, config)

    refresh_search()
    report = audit_brand(BRAND)
    write_json(WEB / "quality.json", report)
    print(json.dumps({
        "vrf_codes_enriched": len(ENRICHMENTS),
        "interpretations": report["errors"]["interpretations"],
        "statuses": report["errors"]["status_counts"],
        "coverage": report["errors"]["component_coverage"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
