#!/usr/bin/env python3
"""Estructura los criterios de detección ya documentados en las fichas Fujitsu."""

from __future__ import annotations

import json
from typing import Any

from audit_brand_quality import audit_brand, write as write_json
from enrich_fujitsu_indoor_valve_v2 import BRAND, DETAILS, WEB, load, refresh_catalogs


VERSION = "2.19.0"


# Cada texto procede de la descripción y de la página oficial ya asociada a la
# interpretación. La lista es explícita para evitar convertir automáticamente
# una explicación editorial en un comportamiento de máquina.
BEHAVIORS: dict[tuple[int, int], tuple[str, str]] = {
    (1, 1): ("La unidad interior genera el error si no recibe el retorno serie de la exterior durante más de 2 minutos tras alimentar o durante más de 15 segundos en funcionamiento normal.", "AOEG22KATA"),
    (2, 2): ("La unidad exterior genera el error si no recibe la señal serie de la interior durante más de 10 segundos.", "AOEG22KATA"),
    (3, 92): ("La unidad interior declara el fallo cuando la recepción correcta desde el mando cableado falta durante 1 minuto o más.", "AUXG30_54LRLB_SERVICE_INSTRUCTION"),
    (3, 3): ("Durante el funcionamiento normal, la unidad interior genera E12 si no recibe señal del mando cableado durante más de 1 minuto.", "AOEG22KATA"),
    (4, 4): ("Durante el ajuste automático, el error se genera si hay giro cuando debería estar parado, no se alcanza la velocidad objetivo en 2 minutos o la potencia de entrada queda fuera del margen previsto.", "AOEG22KATA"),
    (5, 5): ("La exterior evalúa la capacidad total comunicada por las interiores durante los primeros 3 minutos después de aplicar alimentación y genera el error si la combinación no está admitida.", "AOEG22KATA"),
    (6, 6): ("La exterior genera el error al recibir una identificación de refrigerante, serie o compatibilidad que no corresponde a una combinación permitida.", "AOEG22KATA"),
    (7, 7): ("La comprobación se realiza al alimentar: la PCB interior detecta información de modelo incorrecta o imposibilidad de acceder a la EEPROM.", "AOEG22KATA"),
    (8, 8): ("El error se activa cuando la tensión o corriente detectada en el motor ventilador interior queda fuera de los límites previstos durante el control automático.", "AOEG22KATA"),
    (9, 9): ("La unidad considera anómalo que MANUAL AUTO permanezca activado durante 60 segundos o más.", "AOEG22KATA"),
    (10, 10): ("La detección se produce ante un corte momentáneo de alimentación del motor o cuando el ventilador interior no inicia el giro.", "AOEG22KATA"),
    (13, 13): ("El error se genera cuando la velocidad real permanece por debajo de un tercio de la velocidad objetivo durante más de 56 segundos.", "AOEG22KATA"),
    (14, 14): ("La condición de desbordamiento queda confirmada cuando el interruptor de flotador permanece activado durante más de 3 minutos.", "AOEG22KATA"),
    (15, 15): ("La comprobación se ejecuta al alimentar: la PCB exterior detecta información de modelo incorrecta o no puede acceder a su EEPROM.", "AOEG22KATA"),
    (16, 16): ("La PCB principal exterior presenta E63 cuando recibe una información de fallo procedente de la PCB inverter.", "AOEG22KATA"),
    (17, 17): ("La protección se activa si el bus de continua supera el umbral documentado durante más de 3 segundos; tras 5 (cinco) repeticiones, el compresor queda detenido permanentemente hasta el rearme.", "AOEG22KATA"),
    (18, 18): ("La detección se produce si la señal de fallo del IPM permanece a nivel bajo, aproximadamente 0 V, mientras el compresor está parado.", "AOEG22KATA"),
    (20, 20): ("La PCB detecta la sonda del compresor abierta o en cortocircuito al aplicar alimentación o con el compresor funcionando.", "AOEG22KATA"),
    (25, 25): ("La PCB comprueba el presostato durante los 10 segundos posteriores a la alimentación y genera el error si permanece abierto.", "AOEG22KATA"),
    (26, 26): ("El código aparece después de 10 paradas consecutivas por sobrecorriente una vez completado el arranque del compresor inverter.", "AOEG22KATA"),
    (28, 28): ("Si el ventilador exterior queda por debajo de 100 rpm durante los primeros 20 segundos, la unidad detiene el intento; las repeticiones sucesivas terminan deteniendo compresor y ventilador.", "AOEG22KATA"),
    (31, 31): ("La protección se consolida cuando se producen 2 paradas en 24 horas porque la temperatura del compresor alcanza o supera 108 °C.", "AOEG22KATA"),
    (32, 32): ("La condición de presión indicada por el manual debe mantenerse 5 minutos y repetirse 5 veces dentro de 24 horas para generar la protección.", "AOEG22KATA"),
    (34, 34): ("Después de recibir inicialmente al adaptador WLAN, la interior genera el fallo si deja de recibir la misma señal durante 15 segundos.", "AOEH09KMCG"),
    (34, 35): ("Esta variante se presenta cuando coinciden el fallo interior-adaptador WLAN y el fallo de comunicación adaptador-router.", "AOEH09KMCG"),
    (34, 36): ("El indicador WLAN permanece apagado cuando la PCB interior no entrega 12 V CC al adaptador o cuando el adaptador no funciona pese a recibir esa alimentación.", "AOEH09KMCG"),
    (41, 54): ("Tras ordenar abrir o cerrar la compuerta, la PCB no recibe la confirmación esperada del final de carrera correspondiente.", "AOHG18_24KBTA3_SERVICE"),
    (41, 144): ("La PCB genera esta variante cuando recibe simultáneamente las confirmaciones de compuerta abierta y cerrada.", "AOHG18_24KBTA3_SERVICE"),
    (52, 83): ("El propio mando informa CC.1 cuando su sensor de temperatura integrado entrega un valor inválido.", "UTY_RLRY_IM_9373328384"),
    (53, 84): ("El propio mando de 2 hilos presenta C2.1 para identificar un fallo de su PCB de transmisión; no es un código frigorífico de la unidad interior.", "UTY_RLRY_IM_9373328384"),
    (56, 87): ("En un arranque normal aparecen todos los segmentos y después Monitor Mode; 12.4 indica que el mando no ha completado correctamente esa inicialización.", "UTY_RCRYZ1_IM_9373328483"),
    (57, 88): ("El mando presenta 15.4 cuando no consigue adquirir correctamente los datos de la unidad interior seleccionada.", "UTY_RLRY_IM_9373328384"),
    (60, 91): ("El grupo genera 27.1 cuando la relación Master/Slave no cumple la regla de que exista exactamente un mando configurado como Master.", "UTY_RCRYZ1_IM_9373328483"),
    (111, 146): ("El sistema detecta direcciones de mando duplicadas o una mezcla incompatible de asignación automática y manual.", "AOHG18_24KBTA3_SERVICE"),
    (112, 147): ("El error aparece cuando el número de unidades interiores del grupo de mando supera el límite admitido por esa configuración.", "AOHG18_24KBTA3_SERVICE"),
    (113, 148): ("La unidad interior detecta una pérdida de comunicación entre el microprocesador de la PCB principal y la PCB de comunicación del mando.", "AOHG18_24KBTA3_SERVICE"),
    (115, 151): ("La PCB interior genera E58 si detecta abierto el microinterruptor de seguridad de la rejilla mientras el compresor está funcionando.", "AOHG18_24KBTA3_SERVICE"),
}


def add_behaviors() -> int:
    added = 0
    for (error_id, interpretation_id), (body, origin_ref) in BEHAVIORS.items():
        path = DETAILS / f"{error_id}.json"
        detail = load(path)
        interpretation = next(
            row for row in detail["interpretations"]
            if int(row["id"]) == interpretation_id
        )
        rows = interpretation.setdefault("info_items", [])
        existing = [row for row in rows if row.get("item_type") == "machine_behavior"]
        if existing:
            existing[0].update({"body": body, "origin_ref": origin_ref, "review_status": "reviewed"})
        else:
            rows.append({
                "id": 910000 + interpretation_id,
                "item_type": "machine_behavior",
                "title": None,
                "body": body,
                "sort_order": max((int(row.get("sort_order") or 0) for row in rows), default=0) + 1,
                "review_status": "reviewed",
                "origin_ref": origin_ref,
            })
            added += 1
        write_json(path, detail)
    return added


def add_explicit_impacts() -> None:
    impacts = {
        (17, 17): {
            "id": 1701,
            "stop_level": "permanent_stop",
            "summary": "Después de cinco repeticiones, el compresor queda detenido permanentemente hasta el rearme.",
            "affected_scope": "Compresor y funcionamiento del sistema",
            "unaffected_scope": None,
            "restart_behavior": "Corregir la causa y restablecer la alimentación.",
            "degraded_behavior": None,
            "notes": "El umbral principal difiere ligeramente entre los manuales incorporados; se conserva cada valor en su ficha.",
            "review_status": "reviewed",
        },
        (28, 28): {
            "id": 2801,
            "stop_level": "protective_stop",
            "summary": "Las repeticiones sucesivas detienen el compresor y el ventilador exterior.",
            "affected_scope": "Compresor y ventilador exterior",
            "unaffected_scope": None,
            "restart_behavior": "Revisar motor, cableado y PCB antes de repetir el arranque.",
            "degraded_behavior": None,
            "notes": None,
            "review_status": "reviewed",
        },
    }
    for (error_id, interpretation_id), impact in impacts.items():
        path = DETAILS / f"{error_id}.json"
        detail = load(path)
        interpretation = next(row for row in detail["interpretations"] if int(row["id"]) == interpretation_id)
        interpretation["operational_impacts"] = [impact]
        write_json(path, detail)


def update_metadata(error_count: int, search_count: int) -> None:
    navigation_path = WEB / "navigation.json"
    navigation = load(navigation_path)
    navigation["metadata"].update({
        "data_version": VERSION,
        "latest_phase": "Fujitsu V2 — criterios y comportamiento de errores",
        "last_processed_manual": "Fuentes Fujitsu ya vinculadas a cada interpretación",
        "technical_library_review": "Todos los errores técnicos tienen causas, comprobaciones, página y comportamiento o efecto documentado; los agrupadores siguen separados.",
        "last_update_utc": "2026-07-16T16:00:00Z",
    })
    write_json(navigation_path, navigation)

    coverage_path = WEB / "coverage.json"
    coverage = load(coverage_path)
    for row in coverage:
        if row.get("area_slug") == "errors":
            row["notes"] = "Todas las interpretaciones técnicas incluyen causas, comprobaciones, página exacta y criterio/comportamiento documentado; los nueve códigos paraguas enlazan a sus subcódigos."
    write_json(coverage_path, coverage)

    config_path = BRAND / "brand.json"
    config = load(config_path)
    config["data_version"] = VERSION
    config["counts"]["errors"] = error_count
    config["counts"]["search_entries"] = search_count
    config["notes"] = "Fujitsu V2.19: criterios de detección y comportamiento estructurados en las 118 interpretaciones técnicas."
    write_json(config_path, config)


def main() -> int:
    added = add_behaviors()
    add_explicit_impacts()
    error_count, search_count = refresh_catalogs()
    update_metadata(error_count, search_count)
    report = audit_brand(BRAND)
    write_json(WEB / "quality.json", report)
    print(json.dumps({
        "version": VERSION,
        "behaviors_added": added,
        "behavior_map_entries": len(BEHAVIORS),
        "errors": error_count,
        "search_entries": search_count,
        "error_statuses": report["errors"]["status_counts"],
        "coverage": report["errors"]["component_coverage"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
