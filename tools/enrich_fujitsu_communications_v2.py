#!/usr/bin/env python3
"""Desarrolla comunicaciones, direccionamiento y mando de Fujitsu V2."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from audit_brand_quality import audit_brand, write as write_json
from enrich_fujitsu_vrf_v2 import MANUAL_ROOT, MANUAL_TITLE, ORIGIN, refresh_search, source


ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "data" / "brands" / "fujitsu-general"
WEB = BRAND / "web"
DETAILS = WEB / "errors" / "details"
COMM_ORIGIN = "FUJITSU_V2_COMMUNICATIONS"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


ENRICHMENTS: dict[int, dict[str, Any]] = {
    40: dict(
        page=110,
        description="En la variante VR-II, E31.3 indica cinco fallos consecutivos en la prueba de frecuencia de la alimentación de la unidad interior.",
        aliases=[("E: 31.3", "E313"), ("31.3", "313")],
        related=["Alimentación de unidad interior", "Cableado y magnetotérmico", "PCB controladora interior"],
        causes=["Caída de tensión, microcorte, ruido o fuga/contacto defectuoso en la alimentación.", "Cableado, magnetotérmico o instalación incorrectos.", "Conector suelto, cableado incorrecto, corrosión o cortocircuito en la PCB.", "PCB controladora interior defectuosa."],
        checks=["Reiniciar la alimentación y comprobar si reaparece.", "Revisar cable, magnetotérmico y conexiones de instalación.", "Medir 208-230 V CA entre los terminales 1 y 2 de la unidad interior.", "Revisar conectores, cableado, corrosión y cortocircuitos de la PCB.", "Si todo es correcto y se repite, sustituir la PCB y restaurar la dirección original."],
        behavior=["El código se fija cuando la prueba de frecuencia de red falla cinco veces consecutivas."],
        datasets=[dict(name="Alimentación interior VR-II", variable_name="Punto de medida", value_name="Tensión", units=(None, "V CA"), points=[dict(variable_value="Terminales 1-2", value_min=208.0, value_nominal=None, value_max=230.0, value_text="Rango indicado por el manual", sort_order=0, notes=None)], page=110, manual_page="04-26", section="Trouble shooting 17 — Indoor Power Frequency Abnormal")],
    ),
    54: dict(
        page=94,
        description="La unidad interior deja de recibir de forma repetida la misma señal del mando cableado o de otra interior del grupo.",
        aliases=[("E: 12.1", "E121"), ("12.1", "121")],
        related=["Mando cableado de 2 o 3 hilos", "Terminales del mando", "CNC01 y PCB interior"],
        causes=["Terminal flojo, cable abierto o cortocircuitado entre mando e interior o entre interiores.", "Mando cableado defectuoso.", "Alimentación/circuito de comunicación de la PCB interior defectuoso."],
        checks=["Cortar alimentación y revisar terminales, continuidad y cortocircuitos del bus.", "Medir la alimentación del mando en CNC01: aproximadamente 12 V CC indica que la PCB interior alimenta y el mando es sospechoso.", "Si CNC01 entrega 0 V, comprobar/sustituir la PCB interior.", "Después de corregir cableado o reconectar, volver a alimentar para reinicializar el sistema de mando."],
        behavior=["En bus de 3 hilos se detecta al no repetirse la señal durante más de 1 minuto; en bus de 2 hilos, durante más de 2,5 minutos."],
        datasets=[dict(name="Diagnóstico de alimentación del mando", variable_name="Medición en CNC01", value_name="Tensión", units=(None, "V CC"), points=[dict(variable_value="Alimentación presente", value_min=None, value_nominal=12.0, value_max=None, value_text="PCB interior alimenta; comprobar mando/cableado", sort_order=0, notes=None), dict(variable_value="Sin alimentación", value_min=None, value_nominal=0.0, value_max=None, value_text="Comprobar PCB interior", sort_order=1, notes=None)], page=94, manual_page="04-10", section="Trouble shooting 1 — Wired Remote Controller Communication")],
    ),
    55: dict(
        page=96,
        description="El grupo de mando de 2 hilos contiene más de 32 dispositivos entre unidades interiores y mandos.",
        aliases=[("E: 12.3", "E123"), ("12.3", "123")],
        related=["Grupo RC de 2 hilos", "Unidades interiores y mandos", "PCB interior"],
        causes=["Más de 32 unidades interiores y mandos en el mismo grupo RC.", "Cableado o agrupación RC incorrectos.", "PCB interior defectuosa."],
        checks=["Contar interiores y mandos del grupo: el total debe ser 32 o menos.", "Comparar el cableado y la agrupación con el manual de instalación.", "Corregir el grupo y volver a configurar direcciones.", "Si el recuento/cableado es correcto, comprobar la PCB interior y probar de nuevo tras sustituirla."],
        behavior=["El código se genera cuando el número de interiores más mandos de un grupo RC supera 32."],
        datasets=[dict(name="Límite de dispositivos del grupo RC", variable_name="Grupo", value_name="Máximo", units=(None, "dispositivos"), points=[dict(variable_value="Interiores + mandos de 2 hilos", value_min=None, value_nominal=32.0, value_max=None, value_text="No superar 32", sort_order=0, notes=None)], page=96, manual_page="04-12", section="Trouble shooting 3 — Number Excess of Devices")],
    ),
    58: dict(
        page=104,
        description="Dos dispositivos del mismo grupo de mando de 2 hilos utilizan la misma dirección.",
        aliases=[("E: 26.4", "E264"), ("26.4", "264")],
        related=["Direcciones de mando de 2 hilos", "Grupo RC", "Mando y PCB interior"],
        causes=["Cableado o agrupación RC incorrectos.", "Dirección repetida dentro del grupo.", "PCB interior o mando defectuosos."],
        checks=["Comprobar que el cableado une únicamente los equipos del grupo RC previsto.", "Revisar la lista de direcciones y eliminar cualquier duplicado.", "Volver a realizar la asignación de direcciones.", "Si la configuración es correcta, comprobar la PCB interior y el mando."],
        behavior=["La detección se produce cuando existe una dirección duplicada dentro del mismo grupo RC."],
    ),
    59: dict(
        page=105,
        description="En un mismo grupo RC se mezclan direcciones asignadas automáticamente con direcciones manuales, o la asignación no es coherente.",
        aliases=[("E: 26.5", "E265"), ("26.5", "265")],
        related=["Direcciones automáticas 00", "Direcciones manuales", "Grupo RC de 2 hilos"],
        causes=["Cableado o agrupación RC incorrectos.", "Mezcla de dirección automática 00 y direcciones manuales distintas de 00 en el mismo grupo.", "Direcciones introducidas desde la unidad interior no coherentes.", "PCB interior o mando defectuosos."],
        checks=["Comprobar el cableado del grupo RC.", "Elegir un único método de direccionamiento para todo el grupo: automático o manual.", "Verificar y corregir las direcciones configuradas desde las unidades interiores.", "Repetir la asignación; si persiste con configuración correcta, comprobar PCB y mando."],
        behavior=["El código aparece cuando conviven en un grupo direcciones automáticas y manuales incompatibles."],
    ),
    61: dict(
        page=97,
        description="La unidad maestra no reconoce el número de esclavas configurado o una esclava deja de recibir comunicación de la maestra durante al menos 10 segundos.",
        related=["Comunicación entre exteriores", "DIP SET5-1/SET5-2", "PCB principal exterior"],
        causes=["Ruido, microcorte o caída de tensión.", "Alimentación exterior defectuosa.", "Número de exteriores configurado incorrectamente.", "Línea de comunicación entre exteriores abierta o mal conectada.", "PCB principal defectuosa."],
        checks=["Comprobar tensión, cableado de potencia, puesta a tierra y ruido.", "Verificar la cantidad configurada con SET5-1/SET5-2.", "Con alimentación cortada, comprobar continuidad y conexión de la línea entre exteriores.", "Si ajustes y cableado son correctos, sustituir la PCB principal y restaurar la dirección."],
        behavior=["En la maestra, la cantidad de esclavas configurada y la reconocida por comunicación no coincide durante 10 s o más.", "En una esclava, no se recibe comunicación de la maestra durante 10 s o más tras iniciar el control."],
        datasets=[dict(name="Número de unidades exteriores", variable_name="Cantidad", value_name="SET5-1 / SET5-2", units=(None, None), points=[dict(variable_value=1, value_min=None, value_nominal=None, value_max=None, value_text="OFF / OFF", sort_order=0, notes=None), dict(variable_value=2, value_min=None, value_nominal=None, value_max=None, value_text="OFF / ON", sort_order=1, notes=None), dict(variable_value=3, value_min=None, value_nominal=None, value_max=None, value_text="ON / OFF", sort_order=2, notes=None)], page=97, manual_page="04-13", section="Trouble shooting 4 — Communication Between Outdoor Units")],
    ),
    62: dict(
        page=98,
        description="Con SET4-1 en OFF, la exterior deja de recibir durante 180 segundos a una interior/RB que anteriormente comunicaba, sin que exista E14.2.",
        related=["Red VRF", "Unidades interiores/RB", "Resistencia terminal", "PCB de comunicación"],
        causes=["Ruido, microcorte o caída de tensión.", "Interior o RB sin alimentación.", "Línea de comunicación abierta o mal conectada.", "Resistencia terminal mal configurada.", "PCB de comunicación mal montada/defectuosa o PCB de control defectuosa."],
        checks=["Comprobar alimentación de interiores y RB.", "Revisar continuidad, conexión y aislamiento de la red.", "Verificar que la resistencia terminal está configurada correctamente.", "Comprobar conectores y estado de las PCB de comunicación de exterior, interiores y RB.", "Sustituir la PCB afectada y restaurar la dirección si cableado y alimentación son correctos."],
        behavior=["Con SET4-1 en OFF, se fija después de 180 s sin comunicación de una unidad que había comunicado previamente, siempre que no exista el error de red exterior 2."],
    ),
    63: dict(
        page=99,
        description="La red exterior permanece sin comunicación durante 180 segundos según la lógica seleccionada por SET4-1.",
        related=["Red VRF", "SET4-1", "Resistencia terminal", "PCB de comunicación"],
        causes=["Ruido, microcorte o caída de tensión.", "Interior o RB sin alimentación.", "Línea de comunicación abierta o mal conectada.", "Resistencia terminal mal configurada.", "PCB de comunicación o PCB de control defectuosas."],
        checks=["Comprobar alimentación de interiores y RB.", "Revisar continuidad y conexión de la red.", "Verificar la resistencia terminal.", "Comprobar montaje y estado de las PCB de comunicación.", "Sustituir la placa afectada y restaurar ajustes si el resto es correcto."],
        behavior=["Con SET4-1 en ON (fábrica), basta perder durante 180 s una interior que ya había comunicado; con SET4-1 en OFF, deben perderse durante 180 s todas las interiores previamente reconocidas."],
    ),
    64: dict(
        page=101,
        description="El número de interiores comunicando permanece durante 180 segundos por debajo del máximo que la exterior había memorizado.",
        related=["Unidades interiores/RB", "Red de comunicación", "SET4-1", "Memoria del número máximo"],
        causes=["Interior o RB sin alimentación.", "Ruido, microcorte o caída de tensión.", "Línea de comunicación abierta.", "Resistencia terminal incorrecta.", "PCB de comunicación o control defectuosa."],
        checks=["Localizar con el esquema y Service Tool qué interior ha desaparecido.", "Comprobar alimentación de la interior/RB afectada.", "Revisar red, resistencia terminal y placas de comunicación.", "Si se ha eliminado intencionadamente una interior, ejecutar F3-41 para reiniciar el máximo memorizado.", "Tras alimentar todos los equipos, esperar al menos 5 minutos antes de diagnosticar: la secuencia de encendido puede causar una indicación temporal."],
        behavior=["Se detecta cuando el recuento permanece 180 s por debajo del máximo memorizado después de alimentar."],
        impacts=[dict(stop_level="all_system", summary="Con SET4-1 en ON (ajuste de fábrica), el sistema se detiene.", affected_scope="Sistema del circuito frigorífico", unaffected_scope=None, restart_behavior="Recuperar la unidad/comunicación ausente o corregir el máximo memorizado con F3-41.", degraded_behavior="Con SET4-1 en OFF, el manual indica que el sistema no se detiene.", notes="Una secuencia de alimentación desigual puede mostrar este error temporalmente; esperar 5 minutos con todos los equipos alimentados.")],
    ),
    65: dict(
        page=106,
        description="El direccionamiento automático recibe una respuesta anormal o ninguna respuesta de las interiores; tras direccionar RB también detecta direcciones fuera de 0-63 o memoria incorrecta.",
        related=["Direccionamiento automático", "Unidades interiores", "RB y PCB RB", "Red de comunicación"],
        causes=["Interior sin alimentación.", "Más de 64 interiores en el circuito frigorífico.", "Línea de comunicación incorrecta o interrumpida.", "Ruido o microcorte durante el direccionamiento.", "Dirección interior fuera de 0-63 o PCB RB defectuosa."],
        checks=["Comprobar alimentación de todas las interiores.", "Confirmar que el circuito no supera 64 interiores.", "Revisar terminales, continuidad y recorrido de la red.", "Repetir el proceso sin ruido ni interrupciones de alimentación.", "En direccionamiento RB, revisar direcciones interiores; si son válidas, sustituir la PCB controladora RB."],
        behavior=["Durante el autoaddress de interiores se genera si ninguna responde o llega una respuesta anormal; durante el autoaddress de RB se genera si aparece una dirección mayor de 63 o un valor memorizado incorrecto."],
    ),
    66: dict(
        page=107,
        description="El direccionamiento automático de amplificadores de señal recibe una respuesta anormal.",
        related=["Amplificadores de señal", "Alimentación y red", "Modo de filtro", "Unidades exteriores maestras"],
        causes=["Amplificador sin alimentación.", "Demasiados amplificadores conectados.", "Autoaddress iniciado simultáneamente desde varias exteriores maestras.", "Ruido, microcorte o caída de tensión durante el proceso."],
        checks=["Comprobar alimentación de todos los amplificadores.", "Verificar el límite: máximo 8 con filter mode OFF y 32 con filter mode ON.", "Asegurar que solo una exterior maestra ejecuta el autoaddress.", "Repetir el proceso con alimentación estable y sin fuentes de ruido."],
        behavior=["El error se genera cuando llega una respuesta anormal durante el autoaddress de amplificadores; no se muestra en Service Tool según este manual."],
        datasets=[dict(name="Límite de amplificadores de señal", variable_name="Modo", value_name="Máximo", units=(None, "amplificadores"), points=[dict(variable_value="Filter mode OFF", value_min=None, value_nominal=8.0, value_max=None, value_text=None, sort_order=0, notes=None), dict(variable_value="Filter mode ON", value_min=None, value_nominal=32.0, value_max=None, value_text=None, sort_order=1, notes=None)], page=107, manual_page="04-23", section="Trouble shooting 14 — Signal Amplifier Auto Address")],
    ),
}


def controller_sensor_enrichment() -> None:
    path = DETAILS / "52.json"
    detail = load(path)
    interpretation = detail["interpretations"][0]
    interpretation["description"] = "El sensor de temperatura integrado en el propio mando cableado informa de un valor inválido."
    interpretation["info_items"] = [
        row for row in interpretation.get("info_items") or []
        if row.get("origin_ref") != COMM_ORIGIN
    ]
    bodies = [
        ("related_element", "Sensor de temperatura integrado en el mando"),
        ("cause", "Sensor interno del mando dañado o lectura inválida."),
        ("check", "Abrir la confirmación de estado especial y consultar el elemento C1, que muestra la temperatura detectada por el propio mando."),
        ("check", "Si C1 muestra «--.-», el manual identifica el sensor como dañado."),
        ("check", "Si el error persiste después de reiniciar y el sensor sigue sin lectura, sustituir el mando; el manual no describe reparación interna del sensor."),
    ]
    for order, (item_type, body) in enumerate(bodies):
        interpretation["info_items"].append({
            "id": 30000 + 52 * 100 + order,
            "item_type": item_type,
            "title": None,
            "body": body,
            "sort_order": order,
            "review_status": "reviewed",
            "origin_ref": COMM_ORIGIN,
        })
    write_json(path, detail)


def dataset(error_id: int, index: int, spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": 5000 + error_id * 10 + index,
        "name": spec["name"],
        "dataset_type": "technical_values",
        "variable_name": spec["variable_name"],
        "variable_unit": spec["units"][0],
        "value_name": spec["value_name"],
        "value_unit": spec["units"][1],
        "tolerance_text": None,
        "source_kind": "official",
        "calculation_method": None,
        "review_status": "reviewed",
        "notes": spec.get("notes"),
        "visible": 1,
        "points": spec["points"],
        "sources": [source(spec["page"], spec["section"], spec["manual_page"])],
        "origin_ref": COMM_ORIGIN,
    }


def apply_error(error_id: int, enrichment: dict[str, Any]) -> None:
    path = DETAILS / f"{error_id}.json"
    detail = load(path)
    interpretation = detail["interpretations"][0]
    interpretation["description"] = enrichment["description"]
    interpretation["info_items"] = [
        row for row in interpretation.get("info_items") or []
        if row.get("origin_ref") != COMM_ORIGIN
    ]
    order = 0
    for item_type, key in (("related_element", "related"), ("cause", "causes"), ("check", "checks"), ("machine_behavior", "behavior")):
        for body in enrichment.get(key, []):
            interpretation["info_items"].append({
                "id": 30000 + error_id * 100 + order,
                "item_type": item_type,
                "title": None,
                "body": body,
                "sort_order": order,
                "review_status": "reviewed",
                "origin_ref": COMM_ORIGIN,
            })
            order += 1

    interpretation["operational_impacts"] = [
        row for row in interpretation.get("operational_impacts") or []
        if row.get("origin_ref") != COMM_ORIGIN
    ] + [
        {
            "id": 5000 + error_id * 10 + index,
            **impact,
            "review_status": "reviewed",
            "origin_ref": COMM_ORIGIN,
        }
        for index, impact in enumerate(enrichment.get("impacts", []))
    ]
    interpretation["datasets"] = [
        row for row in interpretation.get("datasets") or []
        if row.get("origin_ref") != COMM_ORIGIN
    ] + [dataset(error_id, index, spec) for index, spec in enumerate(enrichment.get("datasets", []))]
    interpretation["sources"] = [
        row for row in interpretation.get("sources") or []
        if row.get("document_ref") != ORIGIN
    ] + [source(enrichment["page"], f"Trouble shooting {enrichment['page'] - 93}")]

    existing_aliases = {(row.get("alias_display"), row.get("alias_normalized")) for row in detail.get("aliases") or []}
    for alias_display, alias_normalized in enrichment.get("aliases", []):
        if (alias_display, alias_normalized) not in existing_aliases:
            detail.setdefault("aliases", []).append({"alias_display": alias_display, "alias_normalized": alias_normalized})
    write_json(path, detail)


def main() -> int:
    for error_id, enrichment in sorted(ENRICHMENTS.items()):
        apply_error(error_id, enrichment)
    controller_sensor_enrichment()

    config_path = BRAND / "brand.json"
    config = load(config_path)
    config["data_version"] = "2.8.0"
    config["notes"] = "Fujitsu V2 en reconstrucción: comunicaciones y direccionamiento VR-II desarrollados; confirmaciones duplicadas consolidadas."
    write_json(config_path, config)

    coverage_path = WEB / "coverage.json"
    coverage = load(coverage_path)
    for row in coverage:
        if row.get("area_slug") == "controllers_buses":
            row["coverage_status"] = "partial"
            row["notes"] = "Incluye diagnóstico de bus 2/3 hilos, direcciones RC y comunicaciones VRF. Quedan códigos internos de algunos mandos cuyo manual solo enumera el significado."
        elif row.get("area_slug") == "commissioning":
            row["notes"] = "Incluye autoaddress de interiores, RB y amplificadores, límites y reacción ante unidades ausentes."
    write_json(coverage_path, coverage)

    refresh_search()
    report = audit_brand(BRAND)
    write_json(WEB / "quality.json", report)
    print(json.dumps({
        "communications_enriched": len(ENRICHMENTS),
        "controller_sensor_developed": True,
        "interpretations": report["errors"]["interpretations"],
        "statuses": report["errors"]["status_counts"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
