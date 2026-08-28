#!/usr/bin/env python3
"""Incorpora la tabla Fujitsu legacy E00-E0F sin mezclar generaciones.

La biblioteca revisada contiene varias formas de mostrar el mismo bloque de
códigos (E:01, 01 y E1:00), pero también cambios de significado entre familias.
Este enriquecimiento conserva esas diferencias como interpretaciones separadas
y publica solo resúmenes técnicos y referencias de página.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from audit_brand_quality import audit_brand, write
from enrich_fujitsu_indoor_valve_v2 import load, refresh_catalogs


ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "data" / "brands" / "fujitsu-general"
WEB = BRAND / "web"
DETAILS = WEB / "errors" / "details"
VERSION = "2.21.0"
ORIGIN = "FUJITSU_LEGACY_E00_E0F_AUDIT"

ABYA_REF = "ABYA30_36LBT_AOYA30_36LFTL"
ABYA_TITLE = "Service Manual — Fujitsu ABYA30/36LBT / AOYA30/36LFTL"
AUU_REF = "AUU36_42RC_AOU36_42RC"
AUU_TITLE = "Service Manual — Fujitsu AUU36/42RC / AOU36/42RC"
OLD_DUCT_REF = "ARY_AOY_LEGACY_DUCT_OPERATING_ES"
OLD_DUCT_TITLE = "Manual de funcionamiento — Fujitsu ARY25/36/45 / AOY25/36/45"
ARYC_REF = "ARYC45LCTU"
ARYC_TITLE = "Service Manual - ARYC45/54LCTU / AOYA45/54LCTL"


def source(
    title: str,
    document_ref: str,
    page: str,
    section: str,
) -> dict[str, Any]:
    return {
        "title": title,
        "document_ref": document_ref,
        "source_url": None,
        "page_start": page,
        "page_end": page,
        "section": section,
    }


def source_abya() -> dict[str, Any]:
    return source(
        ABYA_TITLE,
        ABYA_REF,
        "PDF 17 / impresa 16",
        "Troubleshooting at the remote control LCD",
    )


def source_auu() -> dict[str, Any]:
    return source(
        AUU_TITLE,
        AUU_REF,
        "PDF 7",
        "Self diagnosis check — Table 1",
    )


def source_old_duct() -> dict[str, Any]:
    return source(
        OLD_DUCT_TITLE,
        OLD_DUCT_REF,
        "PDF 15 / Sp-15",
        "Localización de averías — autodiagnóstico",
    )


def source_aryc() -> dict[str, Any]:
    return source(
        ARYC_TITLE,
        ARYC_REF,
        "PDF 13 / impresa 12",
        "Error contents",
    )


def info_items(
    interpretation_id: int,
    related: list[str],
    causes: list[str],
    checks: list[str],
    behavior: str,
    observations: list[str] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    order = 1
    for item_type, bodies in (
        ("related_element", related),
        ("cause", causes),
        ("check", checks),
        ("machine_behavior", [behavior]),
        ("observation", observations or []),
    ):
        for body in bodies:
            rows.append({
                "id": 80000 + interpretation_id * 100 + order,
                "item_type": item_type,
                "title": None,
                "body": body,
                "sort_order": order,
                "review_status": "reviewed",
                "origin_ref": ORIGIN,
            })
            order += 1
    return rows


def interpretation(
    interpretation_id: int,
    title: str,
    description: str,
    related: list[str],
    causes: list[str],
    checks: list[str],
    behavior: str,
    sources: list[dict[str, Any]],
    observations: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": interpretation_id,
        "title": title,
        "description": description,
        "source_kind": "official",
        "confidence": "high",
        "review_status": "reviewed",
        "info_items": info_items(
            interpretation_id,
            related,
            causes,
            checks,
            behavior,
            observations,
        ),
        "operational_impacts": [],
        "datasets": [],
        "sources": sources,
    }


def sensor_interpretation(
    interpretation_id: int,
    title: str,
    description: str,
    sensor: str,
    fault: str,
    behavior: str,
    sources: list[dict[str, Any]],
    family_note: str,
) -> dict[str, Any]:
    if fault == "open":
        causes = [
            f"{sensor} desconectada o con circuito abierto.",
            "Conector flojo, cable cortado o terminal deteriorado.",
            "Entrada de medida de la PCB dañada.",
        ]
    elif fault == "short":
        causes = [
            f"{sensor} en cortocircuito.",
            "Cable pellizcado, humedad en el conector o aislamiento deteriorado.",
            "Entrada de medida de la PCB dañada.",
        ]
    else:
        causes = [
            f"{sensor} desconectada, en cortocircuito o fuera de su curva.",
            "Conector o cableado de la sonda deteriorado.",
            "Entrada de medida de la PCB dañada.",
        ]
    checks = [
        "Antes de desconectar conectores, cortar la alimentación y verificar ausencia de tensión.",
        f"Identificar el modelo y localizar el conector de la {sensor.lower()} en su esquema específico.",
        "Revisar conector y continuidad del cable sin puentear la entrada de la PCB.",
        "Medir la resistencia de la NTC y compararla con la curva del manual exacto de esa familia; no aplicar una tabla de otra generación.",
        "Si sonda y cableado son correctos, comprobar la entrada de la PCB según el manual de servicio.",
    ]
    return interpretation(
        interpretation_id,
        title,
        description,
        [sensor, "Cableado y conector de sonda", "PCB de control"],
        causes,
        checks,
        behavior,
        sources,
        [family_note],
    )


def communication_interpretation(
    interpretation_id: int,
    title: str,
    description: str,
    behavior: str,
    sources: list[dict[str, Any]],
    family_note: str,
) -> dict[str, Any]:
    return interpretation(
        interpretation_id,
        title,
        description,
        ["Comunicación interior-exterior", "Cable y bornes de interconexión", "PCB interior y exterior"],
        [
            "Unidad interior o exterior sin alimentación.",
            "Interconexión abierta, cruzada, floja o conectada a bornes incorrectos.",
            "Interferencias eléctricas o puesta a tierra deficiente.",
            "Fallo de la etapa de comunicación de una de las PCB.",
        ],
        [
            "Identificar primero la familia y la forma exacta en la que el mando presenta el código.",
            "Cortar la alimentación y revisar orden, apriete y continuidad de la interconexión según el esquema de la unidad.",
            "Confirmar las alimentaciones de interior y exterior con el procedimiento y márgenes del manual correspondiente.",
            "Separar el cable de control de fuentes de ruido y revisar la toma de tierra.",
            "Si alimentación y cableado son correctos, seguir el flujo de comunicación de la familia antes de condenar una PCB.",
        ],
        behavior,
        sources,
        [family_note],
    )


def aliases(code: str) -> list[dict[str, str]]:
    legacy_suffix = code[-1]
    old_display = f"E{legacy_suffix}:00"
    values = [
        (f"E: {code[1:]}", code),
        (code, code),
        (code[1:], code[1:]),
        (old_display, old_display.replace(":", "")),
    ]
    return [
        {"alias_display": display, "alias_normalized": normalized.upper()}
        for display, normalized in values
    ]


def standard_aliases(code: str) -> list[dict[str, str]]:
    return [
        {"alias_display": f"E: {code[1:]}", "alias_normalized": code},
        {"alias_display": code, "alias_normalized": code},
        {"alias_display": code[1:], "alias_normalized": code[1:]},
    ]


def error(
    error_id: int,
    code: str,
    scope: str,
    label: str,
    interpretations: list[dict[str, Any]],
    alias_rows: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "id": error_id,
        "code_display": f"E: {code[1:]}",
        "code_normalized": code,
        "indication_type": "remote_controller",
        "unit_scope": scope,
        "short_label": label,
        "aliases": alias_rows or aliases(code),
        "tags": ["legacy", "mando cableado", "tabla E00-E0F"],
        "interpretations": interpretations,
        "media": [],
    }


def build_errors() -> list[dict[str, Any]]:
    common_old_sensor_note = (
        "Significado documentado en las familias antiguas AUU36/42RC y ARY25/36/45. "
        "La misma cifra puede tener otro significado en series posteriores."
    )
    return [
        error(118, "E00", "indoor", "Comunicación entre unidad interior y mando cableado (legacy)", [
            interpretation(
                200,
                "Fallo de comunicación entre unidad interior y mando",
                "La unidad interior y el mando cableado antiguo no intercambian datos correctamente.",
                ["Mando cableado", "Bus de mando", "PCB interior"],
                ["Mando sin alimentación.", "Bus abierto, cruzado o con contacto deficiente.", "Dirección o configuración incompatible.", "Fallo del mando o de la PCB interior."],
                ["Identificar el mando y confirmar que pertenece a la tabla legacy E:00/E0:00.", "Cortar alimentación y revisar continuidad, polaridad cuando proceda y apriete del bus.", "Confirmar alimentación y configuración del mando con el manual de la unidad.", "Probar el mando/cableado antes de sustituir la PCB interior."],
                "El autodiagnóstico muestra E:00 o E0:00 cuando detecta el fallo de comunicación interior-mando.",
                [source_auu(), source_old_duct()],
                ["No confundir con subcódigos modernos de mandos de 2 hilos."],
            )
        ]),
        error(119, "E01", "general", "Comunicación o señal serie interior-exterior (según familia)", [
            communication_interpretation(
                201,
                "Fallo de comunicación entre unidad interior y exterior",
                "En las familias antiguas AUU/AOU y ARY/AOY, E:01 o E1:00 identifica una comunicación anormal entre las unidades.",
                "El mando registra E:01 o E1:00 cuando la comunicación interior-exterior no es válida.",
                [source_auu(), source_old_duct()],
                "Aplicación: AUU36/42RC-AOU36/42RC y ARY25/36/45-AOY25/36/45 documentados.",
            ),
            communication_interpretation(
                202,
                "Fallo de transferencia serie de retorno exterior a interior",
                "En ABYA30/36LBT con AOYA30/36LFTL, el código 01 se define específicamente como fallo de transferencia serie inversa.",
                "La tabla de esta familia asigna 01 al retorno de la señal serie desde la exterior hacia la interior.",
                [source_abya()],
                "Aplicación: familia ABYA30/36LBT-AOYA30/36LFTL; usar su flujo específico.",
            ),
            communication_interpretation(
                203,
                "Fallo de señal interior",
                "En ARYC45/54LCTU con AOYA45/54LCTL, 01 forma parte del grupo de errores de señal interior.",
                "La tabla agrupa 01 con los fallos de señal de la unidad interior.",
                [source_aryc()],
                "Aplicación: ARYC45/54LCTU-AOYA45/54LCTL; la dirección concreta debe confirmarse con el diagrama de diagnóstico del modelo.",
            ),
        ]),
        error(120, "E02", "indoor", "Sonda de temperatura ambiente interior (según familia)", [
            sensor_interpretation(
                204,
                "Sonda de temperatura ambiente interior en circuito abierto",
                "En las tablas antiguas E:02/E2:00 indica expresamente que la sonda ambiente interior está abierta.",
                "Sonda de temperatura ambiente interior",
                "open",
                "El autodiagnóstico registra E:02 o E2:00 al detectar circuito abierto en la entrada de la sonda ambiente.",
                [source_auu(), source_old_duct()],
                common_old_sensor_note,
            ),
            sensor_interpretation(
                205,
                "Fallo de sonda de temperatura ambiente interior",
                "En ABYA30/36LBT y ARYC45/54LCTU, 02 se publica como fallo de la sonda ambiente sin separar abierto y cortocircuito en el código principal.",
                "Sonda de temperatura ambiente interior",
                "generic",
                "La tabla de estas familias asigna 02 al fallo de la sonda ambiente interior.",
                [source_abya(), source_aryc()],
                "Aplicación: ABYA30/36LBT y ARYC45/54LCTU; no asumir circuito abierto sin medir.",
            ),
        ]),
        error(121, "E03", "indoor", "Sonda ambiente interior en cortocircuito (legacy)", [
            sensor_interpretation(206, "Sonda ambiente interior en cortocircuito", "La entrada de la sonda ambiente se detecta en cortocircuito.", "Sonda de temperatura ambiente interior", "short", "El autodiagnóstico muestra E:03 o E3:00 al detectar el cortocircuito.", [source_auu(), source_old_duct()], common_old_sensor_note)
        ]),
        error(122, "E04", "indoor", "Sonda del intercambiador interior (según familia)", [
            sensor_interpretation(207, "Sonda del intercambiador interior en circuito abierto", "La sonda del intercambiador interior se detecta abierta en la tabla legacy.", "Sonda del intercambiador interior", "open", "El autodiagnóstico muestra E:04 o E4:00 al detectar circuito abierto.", [source_auu(), source_old_duct()], common_old_sensor_note),
            sensor_interpretation(208, "Fallo de sonda central del intercambiador interior", "Las familias ABYA/ARYC asignan 04 al fallo de la sonda central del intercambiador interior sin separar abierto y corto.", "Sonda central del intercambiador interior", "generic", "La tabla de estas familias registra 04 como fallo de la sonda central del intercambiador interior.", [source_abya(), source_aryc()], "Aplicación: ABYA30/36LBT y ARYC45/54LCTU; verificar la posición física antes de medir."),
        ]),
        error(123, "E05", "indoor", "Sonda del intercambiador interior en cortocircuito (legacy)", [
            sensor_interpretation(209, "Sonda del intercambiador interior en cortocircuito", "La entrada de la sonda del intercambiador interior se detecta en cortocircuito.", "Sonda del intercambiador interior", "short", "El autodiagnóstico muestra E:05 o E5:00 al detectar el cortocircuito.", [source_auu(), source_old_duct()], common_old_sensor_note)
        ]),
        error(124, "E06", "outdoor", "Sonda del intercambiador exterior (según familia)", [
            sensor_interpretation(210, "Sonda del intercambiador exterior en circuito abierto", "La sonda del intercambiador exterior se detecta abierta en la tabla legacy.", "Sonda del intercambiador exterior", "open", "El autodiagnóstico muestra E:06 o E6:00 al detectar circuito abierto.", [source_auu(), source_old_duct()], common_old_sensor_note),
            sensor_interpretation(211, "Fallo de sonda de salida del intercambiador exterior", "Las familias ABYA/ARYC asignan 06 al fallo de la sonda de salida del intercambiador exterior.", "Sonda de salida del intercambiador exterior", "generic", "La tabla de estas familias registra 06 como fallo de la sonda de salida del intercambiador exterior.", [source_abya(), source_aryc()], "Aplicación: ABYA30/36LBT y ARYC45/54LCTU; confirmar con el esquema del modelo."),
        ]),
        error(125, "E07", "outdoor", "Sonda del intercambiador exterior en cortocircuito (legacy)", [
            sensor_interpretation(212, "Sonda del intercambiador exterior en cortocircuito", "La entrada de la sonda del intercambiador exterior se detecta en cortocircuito.", "Sonda del intercambiador exterior", "short", "El autodiagnóstico muestra E:07 o E7:00 al detectar el cortocircuito.", [source_auu(), source_old_duct()], common_old_sensor_note)
        ]),
        error(126, "E08", "general", "Conexión de alimentación incorrecta (legacy)", [
            interpretation(213, "Error de conexión de la alimentación", "La secuencia o conexión de alimentación no coincide con la esperada por la familia legacy.", ["Bornes de alimentación", "Interconexión interior-exterior", "PCB de control"], ["Cableado de alimentación o interconexión incorrecto.", "Falta de tensión en una unidad o tensión fuera del rango del modelo.", "Conector o borna floja.", "Circuito de detección de la PCB defectuoso."], ["No rearmar repetidamente: cortar alimentación y verificar ausencia de tensión.", "Comparar borne por borne con el esquema exacto del modelo.", "Medir la alimentación con el rango indicado en el manual y revisar protecciones.", "Corregir el cableado antes de valorar una PCB."], "El mando muestra E:08/E8:00 cuando el control detecta una conexión de alimentación anormal.", [source_auu(), source_old_duct()], ["No asumir pérdida de fase: estas fuentes incluyen también equipos monofásicos."])
        ]),
        error(127, "E09", "indoor", "Interruptor de flotador activado (legacy)", [
            interpretation(214, "Interruptor de flotador activado", "El nivel de condensados acciona el flotador o su entrada permanece en estado de alarma.", ["Bandeja de condensados", "Bomba de drenaje", "Interruptor de flotador", "Tubería de desagüe"], ["Desagüe obstruido, estrangulado o con pendiente incorrecta.", "Bomba de drenaje bloqueada o sin alimentación.", "Flotador atascado, conector flojo o cable defectuoso.", "Entrada de flotador de la PCB dañada."], ["Cortar alimentación y comprobar bandeja, sifón, pendiente y ausencia de obstrucciones.", "Comprobar que el flotador se mueve libremente y conmuta eléctricamente.", "Verificar bomba, conector y cableado siguiendo el esquema del modelo.", "Realizar una prueba controlada de drenaje antes de cerrar la unidad."], "El autodiagnóstico registra E:09/E9:00 cuando la entrada del flotador indica nivel alto o anomalía de drenaje.", [source_auu(), source_old_duct()], ["Corregir primero la causa hidráulica; puentear el flotador elimina una protección."])
        ]),
        error(128, "E0A", "outdoor", "Sonda de temperatura exterior (según familia)", [
            sensor_interpretation(215, "Sonda de temperatura exterior en circuito abierto", "La sonda de aire exterior se detecta abierta en la tabla legacy.", "Sonda de temperatura exterior", "open", "El autodiagnóstico muestra E:0A/EA:00 al detectar circuito abierto.", [source_auu(), source_old_duct()], common_old_sensor_note),
            sensor_interpretation(216, "Fallo de sonda de temperatura exterior", "Las familias ABYA/ARYC asignan 0A al fallo de la sonda de aire exterior sin separar abierto y corto.", "Sonda de temperatura exterior", "generic", "La tabla de estas familias registra 0A como fallo de la sonda de temperatura exterior.", [source_abya(), source_aryc()], "Aplicación: ABYA30/36LBT y ARYC45/54LCTU; no asumir circuito abierto sin medir."),
        ]),
        error(129, "E0B", "outdoor", "Sonda de temperatura exterior en cortocircuito (legacy)", [
            sensor_interpretation(217, "Sonda de temperatura exterior en cortocircuito", "La entrada de la sonda de aire exterior se detecta en cortocircuito.", "Sonda de temperatura exterior", "short", "El autodiagnóstico muestra E:0B/Eb:00 al detectar el cortocircuito.", [source_auu(), source_old_duct()], common_old_sensor_note)
        ]),
        error(130, "E0C", "outdoor", "Sonda de descarga del compresor (según familia)", [
            sensor_interpretation(218, "Sonda de descarga en circuito abierto", "La sonda de temperatura del tubo de descarga se detecta abierta en la tabla legacy.", "Sonda de temperatura de descarga", "open", "El autodiagnóstico muestra E:0C/EC:00 al detectar circuito abierto.", [source_auu(), source_old_duct()], common_old_sensor_note),
            sensor_interpretation(219, "Fallo de sonda de temperatura de descarga", "Las familias ABYA/ARYC asignan 0C al fallo de la sonda de descarga sin separar abierto y corto.", "Sonda de temperatura de descarga", "generic", "La tabla de estas familias registra 0C como fallo de la sonda de descarga.", [source_abya(), source_aryc()], "Aplicación: ABYA30/36LBT y ARYC45/54LCTU; confirmar curva y conector del modelo."),
        ]),
        error(131, "E0D", "outdoor", "Sonda de descarga en cortocircuito (legacy)", [
            sensor_interpretation(220, "Sonda de descarga en cortocircuito", "La entrada de la sonda de temperatura de descarga se detecta en cortocircuito.", "Sonda de temperatura de descarga", "short", "El autodiagnóstico muestra E:0D/Ed:00 al detectar el cortocircuito.", [source_auu(), source_old_duct()], common_old_sensor_note)
        ]),
        error(132, "E0E", "outdoor", "Alta presión o sonda del disipador (según familia)", [
            interpretation(221, "Presión exterior anormalmente alta", "En las familias antiguas AUU/AOU y ARY/AOY, E:0E o EE:00 corresponde a alta presión exterior anormal.", ["Presostato o protección de alta", "Intercambiador exterior", "Ventiladores exteriores", "Circuito frigorífico"], ["Caudal de aire exterior insuficiente por suciedad, obstrucción o ventilador defectuoso.", "Válvula cerrada, restricción frigorífica o sobrecarga de refrigerante.", "Presostato, cableado o entrada de protección defectuosos.", "Temperatura exterior o condiciones de trabajo fuera del rango de la unidad."], ["Detener la unidad y comprobar que las válvulas de servicio están abiertas.", "Revisar limpieza del intercambiador, paso de aire y funcionamiento de los ventiladores.", "Medir presiones y temperaturas con instrumental adecuado y dentro del rango del modelo.", "Comprobar presostato y cableado con la alimentación desconectada antes de intervenir en la PCB."], "La protección registra E:0E/EE:00 cuando detecta una condición de alta presión exterior.", [source_auu(), source_old_duct()], ["No confundir con 0E de algunas unidades inverter posteriores, donde el código identifica la sonda del disipador."]),
            sensor_interpretation(222, "Fallo de la sonda del disipador inverter", "En ARYC45/54LCTU-AOYA45/54LCTL, 0E se asigna a la sonda del disipador de la electrónica inverter.", "Sonda de temperatura del disipador inverter", "generic", "La tabla de esta familia registra 0E como fallo de la sonda del disipador inverter.", [source_aryc()], "Aplicación: ARYC45/54LCTU-AOYA45/54LCTL. No diagnosticar alta presión solo por ver 0E."),
        ]),
        error(133, "E0F", "outdoor", "Temperatura de descarga anormal (legacy)", [
            interpretation(223, "Temperatura del tubo de descarga anormal", "La protección detecta una temperatura de descarga anormalmente alta o incompatible con el funcionamiento previsto.", ["Compresor", "Sonda de descarga", "Carga y circulación de refrigerante", "Intercambiadores y ventiladores"], ["Carga insuficiente, fuga o circulación de refrigerante deficiente.", "Intercambiadores sucios o caudal de aire insuficiente.", "Sonda de descarga fuera de curva o mal fijada.", "Compresor trabajando fuera de sus condiciones admisibles."], ["Detener la unidad si la temperatura sigue aumentando y dejarla estabilizar.", "Comprobar fijación y lectura de la sonda de descarga con la curva del modelo.", "Revisar caudales de aire, intercambiadores, ventiladores y válvulas de servicio.", "Medir presiones, sobrecalentamiento y subenfriamiento antes de corregir la carga.", "Localizar y reparar cualquier fuga antes de añadir refrigerante."], "El autodiagnóstico muestra E:0F/EF:00 cuando actúa la protección por temperatura de descarga anormal.", [source_auu(), source_old_duct()], ["No añadir refrigerante basándose únicamente en el código; confirmar el estado termodinámico del sistema."])
        ]),
        error(134, "E11", "general", "Modelo o configuración de unidad anormal (legacy)", [
            interpretation(224, "Modelo o configuración de unidad anormal", "En AUU36/42RC-AOU36/42RC, E:11 identifica una incoherencia de modelo; no es el E11 de comunicación serie de generaciones posteriores.", ["Datos de modelo", "PCB interior y exterior", "Puentes o ajustes de configuración"], ["PCB de recambio no correspondiente al modelo.", "Ajustes, puentes o memoria de modelo incompatibles.", "Datos internos de la PCB corruptos.", "Combinación interior-exterior no admitida."], ["Confirmar el modelo completo de interior y exterior antes de interpretar E11.", "Cortar alimentación y comprobar referencias de las PCB contra el despiece del modelo.", "Revisar puentes y ajustes únicamente con el procedimiento del manual específico.", "Si la configuración es correcta, seguir el procedimiento de sustitución de PCB sin copiar ajustes de otra familia."], "Esta familia muestra E:11 cuando detecta información de modelo anormal.", [source_auu()], ["No usar el flujo moderno de comunicación E11 sin confirmar previamente la generación."])
        ], standard_aliases("E11")),
        error(135, "E12", "indoor", "Ventilador interior anormal (legacy)", [
            interpretation(225, "Funcionamiento anormal del ventilador interior", "En AUU36/42RC-AOU36/42RC, E:12 corresponde al ventilador interior; en equipos posteriores E12 suele referirse al mando cableado.", ["Motor ventilador interior", "Turbina y rodamientos", "Condensador o etapa de accionamiento", "PCB interior"], ["Turbina bloqueada o rodamientos dañados.", "Motor, condensador o cableado defectuoso.", "Conector flojo o realimentación de velocidad ausente.", "Etapa de accionamiento de la PCB averiada."], ["Confirmar modelo y generación antes de aplicar este significado.", "Cortar alimentación y comprobar que la turbina gira libremente y sin roces.", "Revisar conectores, cableado y componentes del motor con los valores del manual.", "Si mecánica y motor son correctos, comprobar la etapa de accionamiento de la PCB."], "Esta familia muestra E:12 cuando detecta funcionamiento anormal del ventilador interior.", [source_auu()], ["No confundir con el E12 moderno de comunicación con el mando cableado."])
        ], standard_aliases("E12")),
        error(136, "E13", "outdoor", "Señal de unidad exterior anormal (legacy)", [
            communication_interpretation(226, "Señal procedente de la unidad exterior anormal", "En AUU36/42RC-AOU36/42RC, E:13 identifica una señal anormal de la unidad exterior.", "Esta familia registra E:13 cuando la señal exterior recibida no es válida.", [source_auu()], "Aplicación: AUU36/42RC-AOU36/42RC. En otras generaciones, consultar su tabla de errores antes de intervenir.")
        ], standard_aliases("E13")),
        error(137, "E14", "outdoor", "Memoria EEPROM exterior anormal (legacy)", [
            interpretation(227, "Datos EEPROM de la unidad exterior anormales", "La unidad exterior no puede utilizar correctamente los datos almacenados en su memoria EEPROM.", ["EEPROM exterior", "PCB principal exterior", "Datos de modelo y configuración"], ["Datos de memoria corruptos.", "PCB de recambio incorrecta o sin la configuración del modelo.", "Alimentación inestable durante la escritura o el arranque.", "Fallo interno de la PCB exterior."], ["Confirmar el modelo completo y la referencia exacta de la PCB instalada.", "Realizar un único reinicio controlado después de comprobar alimentación y conexiones.", "Revisar los ajustes de modelo solo si el manual de servicio documenta el procedimiento.", "No intentar copiar o reprogramar la memoria sin procedimiento y datos oficiales del modelo.", "Si el error persiste con alimentación correcta, seguir el criterio de sustitución de la PCB exterior."], "Esta familia muestra E:14 cuando detecta datos EEPROM exteriores anormales.", [source_auu()], ["Conservar o registrar todos los ajustes antes de sustituir una placa cuando el procedimiento del modelo lo permita."])
        ], standard_aliases("E14")),
    ]


def add_sources() -> int:
    path = WEB / "sources.json"
    rows = [
        row for row in load(path)
        if row.get("document_ref") not in {ABYA_REF, AUU_REF, OLD_DUCT_REF}
    ]
    next_rows = [
        {
            "id": 23,
            "title": ABYA_TITLE,
            "document_ref": ABYA_REF,
            "publication_date": "2010-05-07",
            "language": "en",
            "document_type": "service_manual",
            "source_url": None,
            "status": "reviewed",
            "notes": "Copia del manual oficial conservada en la biblioteca del usuario; tabla de autodiagnóstico revisada en PDF 17.",
        },
        {
            "id": 24,
            "title": AUU_TITLE,
            "document_ref": AUU_REF,
            "publication_date": None,
            "language": "en",
            "document_type": "service_manual",
            "source_url": None,
            "status": "reviewed",
            "notes": "Copia del manual oficial conservada en la biblioteca del usuario; tabla E:00-E:0F y E11-E14 revisada en PDF 7.",
        },
        {
            "id": 25,
            "title": OLD_DUCT_TITLE,
            "document_ref": OLD_DUCT_REF,
            "publication_date": None,
            "language": "es",
            "document_type": "technical_manual",
            "source_url": None,
            "status": "reviewed",
            "notes": "Manual oficial escaneado; las 20 páginas se revisaron visualmente y la tabla E0:00-EF:00 se verificó en Sp-15.",
        },
    ]
    rows.extend(next_rows)
    rows.sort(key=lambda row: int(row["id"]))
    write(path, rows)
    return len(rows)


def write_audit_manifest() -> None:
    write(WEB / "manual_audit.json", {
        "schema_version": "1.0",
        "brand": "Fujitsu / General",
        "reviewed_on": "2026-08-28",
        "scope": "Biblioteca manuales fujitsu.zip aportada por el usuario",
        "corpus": {
            "pdf_files": 54,
            "pages": 1617,
            "pages_with_extractable_text": 1573,
            "scanned_pdf_files_reviewed_visually": 2,
            "exact_duplicate_pairs": 4,
        },
        "scanned_documents": [
            "arg25rla_aog25rzal.compr.pdf",
            "MANDO_GENERAL-FUTJISU_(VIEJO).pdf",
        ],
        "duplicate_pairs": [
            ["ary30luan (2).pdf", "ary30luan.pdf"],
            ["asy9lsacw (1).pdf", "asy9lsacw.pdf"],
            ["EN-J02.121.46-AOYG-KLCA-Inverter-outdoor-unit (1).pdf", "EN-J02.121.46-AOYG-KLCA-Inverter-outdoor-unit.pdf"],
            ["manual fujitsu rc-30la-le.pdf", "manual fujitsu rc-30la.pdf"],
        ],
        "findings": [
            "E01 y E02 sí están documentados en manuales oficiales de la biblioteca.",
            "E01 cambia entre comunicación interior-exterior, transferencia serie inversa y señal interior según familia.",
            "E02 puede significar sonda ambiente abierta o fallo genérico de la misma sonda según generación.",
            "E0E puede ser alta presión en equipos legacy o sonda de disipador inverter en una familia posterior.",
            "E11 y E12 cambian de significado respecto a generaciones modernas; E13 y E14 completan la extensión legacy documentada.",
            "Las formas E:01, 01 y E1:00 deben buscarse como alias, no tratarse como tablas universales.",
        ],
        "publication_policy": "Se publican resúmenes y referencias de página; no se incorporan páginas ni imágenes de los manuales.",
    })


def update_metadata(error_count: int, search_count: int, source_count: int) -> None:
    navigation_path = WEB / "navigation.json"
    navigation = load(navigation_path)
    navigation["metadata"].update({
        "data_version": VERSION,
        "latest_phase": "Fujitsu V2 — auditoría documental legacy E00-E0F",
        "last_processed_manual": "Biblioteca Fujitsu: 54 PDF / 1.617 páginas",
        "technical_library_review": "E00-E0F y E11-E14 legacy normalizados con separación explícita por familia; E01, E02, E0E, E11 y E12 conservan sus significados alternativos.",
        "last_update_utc": "2026-08-28T18:30:00Z",
    })
    write(navigation_path, navigation)

    coverage_path = WEB / "coverage.json"
    coverage = load(coverage_path)
    for row in coverage:
        row["source_count"] = source_count
        if row.get("area_slug") == "errors":
            row["notes"] = "Incluye E00-E0F y E11-E14 legacy, con alias de los mandos E0:00-EF:00 y significados alternativos separados por familia; no se extrapolan códigos entre generaciones."
        elif row.get("area_slug") == "diagnostic_access":
            row["notes"] = "Métodos modernos y mandos cableados históricos, incluido el formato de autodiagnóstico E0:00-EF:00."
    write(coverage_path, coverage)

    brand_path = BRAND / "brand.json"
    brand = load(brand_path)
    brand["data_version"] = VERSION
    brand["counts"].update({
        "errors": error_count,
        "search_entries": search_count,
    })
    brand["notes"] = "Fujitsu V2.21: auditoría de 54 manuales y tabla legacy E00-E0F/E11-E14 normalizada sin mezclar generaciones."
    write(brand_path, brand)


def update_feed() -> None:
    path = ROOT / "data" / "updates" / "feed.json"
    feed = load(path)
    entry_id = "UPD-20260828-FUJITSU-LEGACY-AUDIT-221"
    feed["entries"] = [row for row in feed["entries"] if row.get("id") != entry_id]
    feed["entries"].insert(0, {
        "id": entry_id,
        "date": "2026-08-28",
        "title": "Fujitsu recupera E01, E02 y la tabla legacy completa",
        "summary": "Se han auditado 54 manuales y 1.617 páginas, incluidas dos publicaciones escaneadas revisadas visualmente. La base incorpora 20 códigos antiguos —E00-E0F y E11-E14—, sus formatos alternativos de mando y separa por familia los significados que cambian, especialmente E01, E02, E0E, E11 y E12.",
        "areas": ["Fujitsu", "Códigos de error", "Documentación", "Diagnóstico"],
        "kind": "content_improvement",
        "author": {"type": "maintainer", "label": "Administrador"},
    })
    feed["updated_at"] = "2026-08-28"
    rendered = json.dumps(feed, ensure_ascii=False, indent=2)
    rendered = re.sub(
        r'"areas": \[\n\s+((?:"[^"]+",?\n\s*)+)\]',
        lambda match: '"areas": [' + " ".join(
            part.strip() for part in match.group(1).splitlines() if part.strip()
        ) + ']',
        rendered,
    )
    rendered = re.sub(
        r'"author": \{\n\s+"type": "([^"]+)",\n\s+"label": "([^"]+)"\n\s+\}',
        r'"author": {"type": "\1", "label": "\2"}',
        rendered,
    )
    rendered = re.sub(
        r'("id": "UPD-20260822-PROJECTS-MOBILE-AUTOMATION".*?"author": )\{"type": "maintainer", "label": "Administrador"\}',
        r'\1{ "type": "maintainer", "label": "Administrador" }',
        rendered,
        flags=re.DOTALL,
    )
    path.write_text(
        rendered + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    for row in build_errors():
        write(DETAILS / f"{row['id']}.json", row)
    source_count = add_sources()
    write_audit_manifest()
    error_count, search_count = refresh_catalogs()
    update_metadata(error_count, search_count, source_count)
    report = audit_brand(BRAND)
    write(WEB / "quality.json", report)
    update_feed()
    print(json.dumps({
        "version": VERSION,
        "errors": error_count,
        "search_entries": search_count,
        "sources": source_count,
        "interpretations": report["errors"]["interpretations"],
        "technical_interpretations": report["errors"]["technical_interpretations"],
        "statuses": report["errors"]["status_counts"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
