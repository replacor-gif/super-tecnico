#!/usr/bin/env python3
"""Aplica consolidaciones Fujitsu V2 revisadas manualmente."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from audit_brand_quality import audit_brand, write as write_json


ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "data" / "brands" / "fujitsu-general"
WEB = BRAND / "web"

# Un registro mínimo que solo confirma el mismo significado se incorpora como
# fuente de la interpretación desarrollada. No se fusionan significados distintos.
CONFIRMATION_MERGES = {
    3: {3: [41]},   # E12: el manual ABYG confirma el mismo fallo de mando.
    5: {5: [44]},   # E22: confirmación de capacidad interior.
    9: {9: [49]},   # E35: confirmación del pulsador MANUAL AUTO.
    11: {11: [50]}, # E41: confirmación de sonda ambiente.
    12: {12: [51]}, # E42: confirmación de sonda de intercambiador.
    13: {13: [52]}, # E51: confirmación del motor ventilador interior.
    14: {14: [53]}, # E53: confirmación de bomba de drenaje.
    16: {16: [57]}, # E63: confirmación del error de inverter.
    17: {17: [58]}, # E64: confirmación del circuito PFC.
    18: {18: [59]}, # E65: confirmación de la señal de disparo IPM.
    19: {19: [61]}, # E71: confirmación de sonda de descarga.
    20: {20: [62]}, # E72: confirmación de sonda de compresor.
    21: {21: [63]}, # E73: confirmación de sondas del intercambiador exterior.
    22: {22: [64]}, # E74: confirmación de sonda ambiente exterior.
    23: {23: [67]}, # E77: confirmación de sonda del disipador.
    25: {25: [71]}, # E86: confirmación de error de presión.
    26: {26: [72]}, # E94: confirmación de disparo por sobrecorriente.
    28: {28: [74]}, # E97: confirmación de motor ventilador exterior.
    29: {29: [76]}, # E99: confirmación de válvula de cuatro vías.
    30: {30: [78]}, # EA1: confirmación de temperatura de descarga.
    31: {31: [79]}, # EA3: confirmación de temperatura de compresor.
    32: {32: [81]}, # EA5: confirmación de baja presión.
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def source_key(source: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(source.get("document_ref") or source.get("title") or ""),
        str(source.get("page_start") or ""),
        str(source.get("section") or ""),
    )


def merge_confirmation_sources(error_id: int, target_id: int, source_ids: list[int]) -> int:
    path = WEB / "errors" / "details" / f"{error_id}.json"
    error = load(path)
    interpretations = error.get("interpretations") or []
    by_id = {int(item["id"]): item for item in interpretations}
    target = by_id.get(target_id)
    if not target:
        raise RuntimeError(f"No existe la interpretación destino {target_id} en el error {error_id}")

    existing = {source_key(source) for source in (target.get("sources") or [])}
    removed = 0
    for source_id in source_ids:
        confirmation = by_id.get(source_id)
        if not confirmation:
            continue
        confirmation_info = confirmation.get("info_items") or []
        developed_types = {row.get("item_type") for row in confirmation_info} - {"related_element", "observation"}
        if developed_types or confirmation.get("operational_impacts") or confirmation.get("datasets"):
            raise RuntimeError(f"La interpretación {source_id} contiene desarrollo y no puede consolidarse como confirmación")
        existing_info = {
            (row.get("item_type"), str(row.get("body") or "").strip().casefold())
            for row in (target.get("info_items") or [])
        }
        for row in confirmation_info:
            key = (row.get("item_type"), str(row.get("body") or "").strip().casefold())
            if key not in existing_info:
                target.setdefault("info_items", []).append(row)
                existing_info.add(key)
        for source in confirmation.get("sources") or []:
            key = source_key(source)
            if key not in existing:
                target.setdefault("sources", []).append(source)
                existing.add(key)
        interpretations.remove(confirmation)
        removed += 1

    if removed:
        write_json(path, error)
    return removed


def main() -> int:
    removed = 0
    for error_id, targets in CONFIRMATION_MERGES.items():
        for target_id, source_ids in targets.items():
            removed += merge_confirmation_sources(error_id, target_id, source_ids)

    index_path = WEB / "errors" / "index.json"
    index = load(index_path)
    for row in index:
        detail = load(WEB / "errors" / "details" / f"{int(row['id'])}.json")
        row["interpretation_count"] = len(detail.get("interpretations") or [])
    write_json(index_path, index)

    config_path = BRAND / "brand.json"
    config = load(config_path)
    version = tuple(int(part) for part in str(config.get("data_version") or "0.0.0").split(".")[:3])
    if version < (2, 6, 0):
        config["data_version"] = "2.6.0"
        config["notes"] = "Fujitsu V2 en reconstrucción: las confirmaciones documentales duplicadas se consolidan en la interpretación técnica correspondiente."
    write_json(config_path, config)

    report = audit_brand(BRAND)
    write_json(WEB / "quality.json", report)
    print(json.dumps({
        "confirmations_merged": removed,
        "interpretations": report["errors"]["interpretations"],
        "statuses": report["errors"]["status_counts"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
