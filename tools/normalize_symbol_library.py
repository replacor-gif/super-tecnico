#!/usr/bin/env python3
"""Build ElectroIA's deterministic CAD symbol registry from the 460-row catalog."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "symbols" / "catalog.json"
SEEDS_PATH = ROOT / "data" / "electroia" / "symbol-reviewed-seeds.json"
LIBRARY_PATH = ROOT / "data" / "electroia" / "symbol-library.json"
REPORT_PATH = ROOT / "data" / "electroia" / "symbol-normalization-report.json"
JS_PATH = ROOT / "archivo-tecnico-47097e44267b9cb111636b84823f1d47" / "diagram-symbol-library.js"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def folded(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(char for char in text if not unicodedata.combining(char)).lower()


def port(x: int, y: int, side: str, electrical_type: str) -> dict:
    return {"x": x, "y": y, "side": side, "electrical_type": electrical_type}


def ports_for_names(names: list[str]) -> tuple[int, int, dict]:
    cleaned = []
    for name in names:
        candidate = re.sub(r"[^A-Za-z0-9_+.-]", "", name)[:20] or str(len(cleaned) + 1)
        if candidate in cleaned:
            candidate = f"{candidate}{len(cleaned) + 1}"
        cleaned.append(candidate)
    if len(cleaned) <= 1:
        return 6, 4, {cleaned[0] if cleaned else "1": port(-3, 0, "west", "passive")}
    if len(cleaned) == 2:
        return 6, 4, {
            cleaned[0]: port(-3, 0, "west", "passive"),
            cleaned[1]: port(3, 0, "east", "passive"),
        }
    left_count = max(1, len(cleaned) // 2)
    right_count = len(cleaned) - left_count
    height = max(6, max(left_count, right_count) * 2 + 2)
    half_width = 4

    def offsets(count: int) -> list[int]:
        if count == 1:
            return [0]
        return [-(count - 1) + index * 2 for index in range(count)]

    result = {}
    for name, y in zip(cleaned[:left_count], offsets(left_count)):
        result[name] = port(-half_width, y, "west", "input")
    for name, y in zip(cleaned[left_count:], offsets(right_count)):
        result[name] = port(half_width, y, "east", "output")
    return half_width * 2, height, result


def inferred_terminal_names(record: dict) -> list[str]:
    drawing = folded(record.get("tipo_dibujo"))
    terminals = folded(record.get("terminales"))
    name = folded(record.get("nombre"))
    combined = f"{drawing} {terminals} {name}"
    if any(token in drawing for token in ("diode", "zener", "schottky", "rectifier")):
        return ["A", "K"]
    if any(token in drawing for token in ("mosfet", "jfet")):
        return ["G", "D", "S"]
    if "igbt" in drawing:
        return ["G", "C", "E"]
    if any(token in drawing for token in ("transistor", "bjt", "darlington")):
        return ["B", "C", "E"]
    if "opto" in drawing and "logic" not in drawing:
        return ["A", "K", "C", "E"]
    if any(token in drawing for token in ("gate_", "gateand", "gatenand", "gateor", "gatenor", "gatexor")) or drawing.startswith("gate"):
        return ["A", "B", "Q"]
    if "flipflop" in drawing:
        return ["D", "CLK", "Q", "nQ"]
    if any(token in drawing for token in ("opamp", "comparator", "difference_amp", "instrumentation_amp")):
        return ["IN+", "IN-", "OUT", "VCC", "GND"]
    if "motor_3" in drawing or "inverter3" in drawing or "rectifier3" in drawing:
        return ["U", "V", "W", "PE"]
    if "relay" in drawing and "coil" not in drawing:
        return ["COM", "NO", "NC"]
    if "coil" in drawing or "solenoid" in drawing:
        return ["A1", "A2"]
    if any(token in combined for token in ("vcc", "gnd", "salida", " output", " out")):
        return ["VCC", "GND", "OUT"]
    if any(token in drawing for token in ("connector_multi", "bus", "module", "mcu", "cpu", "fpga", "cpld", "dsp")):
        return ["IN1", "IN2", "OUT1", "OUT2"]
    return ["1", "2"]


def family_for(record: dict, terminal_count: int) -> str:
    category = folded(record.get("categoria"))
    drawing = folded(record.get("tipo_dibujo"))
    if "conexion" in category or "conector" in category:
        return "generic_1p" if terminal_count == 1 else "connector_block"
    if "electronica digital" in category:
        return "digital_block"
    if "circuitos integrados" in category:
        return "functional_block"
    if "sensor" in category:
        return "sensor_block"
    if "semiconductor" in category:
        return "semiconductor_block"
    if "maquinas" in category:
        return "machine_block"
    if "protecciones" in category:
        return "protection_block"
    if "potencia" in category:
        return "power_block"
    if "optoelectronica" in category:
        return "isolation_block"
    if "instalaciones" in category:
        return "installation_block"
    if "medida" in category:
        return "meter_block"
    if any(token in drawing for token in ("source", "battery", "cell", "generator")):
        return "source_block"
    if terminal_count == 1:
        return "generic_1p"
    if terminal_count == 2:
        return "generic_2p"
    if terminal_count == 3:
        return "generic_3p"
    return "generic_4p"


def normalize_record(record: dict, reviewed: dict | None) -> dict:
    if reviewed:
        result = dict(reviewed)
        result.update({
            "catalog_id": record["id"],
            "name": record.get("nombre") or reviewed.get("name") or record["id"],
            "designator": record.get("designador") or reviewed.get("designator") or "X",
            "category": record.get("categoria") or "",
            "subcategory": record.get("subcategoria") or "",
            "aliases": record.get("alias") or "",
            "keywords": record.get("etiquetas") or "",
            "description": record.get("descripcion") or "",
            "interpretation": record.get("interpretacion") or "",
            "catalog_standard": record.get("norma") or "",
            "catalog_drawing_type": record.get("tipo_dibujo") or "",
            "source_asset": record.get("archivo_svg") or "",
            "review_status": "engine_reviewed",
            "geometry_source": "reviewed_seed",
        })
        return result

    names = inferred_terminal_names(record)
    width, height, ports = ports_for_names(names)
    family = family_for(record, len(names))
    return {
        "id": record["id"],
        "catalog_id": record["id"],
        "name": record.get("nombre") or record["id"],
        "kind": family,
        "geometry_template": family,
        "designator": record.get("designador") or "X",
        "category": record.get("categoria") or "",
        "subcategory": record.get("subcategoria") or "",
        "aliases": record.get("alias") or "",
        "keywords": record.get("etiquetas") or "",
        "description": record.get("descripcion") or "",
        "interpretation": record.get("interpretacion") or "",
        "catalog_standard": record.get("norma") or "",
        "catalog_drawing_type": record.get("tipo_dibujo") or "",
        "standard_profile": "IEC_EXPERIMENTAL",
        "grid_pitch_mil": 50,
        "width": width,
        "height": height,
        "ports": ports,
        "review_status": "auto_draft",
        "geometry_source": "family_template",
        "source_asset": record.get("archivo_svg") or "",
    }


def serialized(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def build_outputs() -> tuple[str, str, str]:
    catalog = read_json(CATALOG_PATH).get("symbols", [])
    seeds = {item["id"]: item for item in read_json(SEEDS_PATH).get("symbols", [])}
    if len(catalog) != 460:
        raise SystemExit(f"Se esperaban 460 fichas y hay {len(catalog)}")
    ids = [item.get("id") for item in catalog]
    if len(ids) != len(set(ids)):
        raise SystemExit("El catálogo contiene identificadores duplicados")
    catalog_ids = set(ids)
    internal_seeds = {key: value for key, value in seeds.items() if key.startswith("ST-")}
    unknown_seeds = sorted(set(seeds) - catalog_ids - set(internal_seeds))
    if unknown_seeds:
        raise SystemExit(f"Semillas fuera del catálogo: {', '.join(unknown_seeds)}")

    catalog_symbols = [normalize_record(record, seeds.get(record["id"])) for record in catalog]
    internal_symbols = []
    for symbol_id in sorted(internal_seeds):
        item = dict(internal_seeds[symbol_id])
        item.update({
            "catalog_id": None,
            "review_status": "engine_internal",
            "geometry_source": "internal_seed",
        })
        internal_symbols.append(item)
    symbols = catalog_symbols + internal_symbols
    status_counts = Counter(item["review_status"] for item in symbols)
    catalog_status_counts = Counter(item["review_status"] for item in catalog_symbols)
    family_counts = Counter(item.get("geometry_template") or item["kind"] for item in catalog_symbols)
    category_quality = {}
    for item in catalog_symbols:
        quality = category_quality.setdefault(item["category"], {"total": 0, "engine_reviewed": 0, "auto_draft": 0})
        quality["total"] += 1
        quality[item["review_status"]] += 1
    library = {
        "schema_version": "1.0",
        "library_version": "0.5",
        "engine_contract_version": "1.0",
        "standard_profile": "IEC_EXPERIMENTAL",
        "grid_pitch_mil": 50,
        "catalog_symbol_count": len(catalog),
        "engine_symbol_count": len(symbols),
        "reviewed_catalog_symbol_count": catalog_status_counts["engine_reviewed"],
        "auto_draft_catalog_symbol_count": catalog_status_counts["auto_draft"],
        "internal_template_count": len(internal_symbols),
        "symbols": symbols,
    }
    report = {
        "schema_version": "1.0",
        "catalog_symbols": len(catalog),
        "normalized_catalog_symbols": len(catalog_symbols),
        "engine_symbols": len(symbols),
        "symbols_with_ports": sum(bool(item["ports"]) for item in symbols),
        "status_counts": dict(sorted(status_counts.items())),
        "catalog_status_counts": dict(sorted(catalog_status_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "category_quality": dict(sorted(category_quality.items())),
        "fully_reviewed_categories": sorted(
            category for category, quality in category_quality.items() if quality["auto_draft"] == 0
        ),
        "coverage_percent": 100,
        "quality_policy": {
            "engine_reviewed": "Geometría y terminales revisados en el motor experimental.",
            "auto_draft": "Definición provisional por familia; el motor debe advertir antes de usarla.",
            "engine_internal": "Elemento auxiliar del motor que no pertenece al catálogo público.",
        },
    }
    js = (
        '"use strict";\n\n'
        f"const ElectroDiagramSymbols = Object.freeze({json.dumps({item['id']: item for item in symbols}, ensure_ascii=False, indent=2)});\n\n"
        'if (typeof globalThis !== "undefined") globalThis.ElectroDiagramSymbols = ElectroDiagramSymbols;\n'
        'if (typeof module !== "undefined" && module.exports) module.exports = ElectroDiagramSymbols;\n'
    )
    return serialized(library), serialized(report), js


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if generated files are stale")
    args = parser.parse_args()
    library, report, js = build_outputs()
    outputs = ((LIBRARY_PATH, library), (REPORT_PATH, report), (JS_PATH, js))
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, content in outputs if not path.exists() or path.read_text(encoding="utf-8") != content]
        if stale:
            raise SystemExit("Archivos de símbolos desactualizados: " + ", ".join(stale))
    else:
        for path, content in outputs:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
