#!/usr/bin/env python3
"""Add three reviewed geometry batches to ElectroIA's deterministic seed registry."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "symbols" / "catalog.json"
SEEDS = ROOT / "data" / "electroia" / "symbol-reviewed-seeds.json"
TARGET_CATEGORIES = {
    "Componentes pasivos": "passive_components_2026_08",
    "Semiconductores discretos": "discrete_semiconductors_2026_08",
    "Optoelectrónica y aislamiento": "opto_isolation_2026_08",
}


def port(x: int, y: int, side: str, electrical_type: str = "passive") -> dict:
    return {"x": x, "y": y, "side": side, "electrical_type": electrical_type}


def horizontal(names: tuple[str, str] = ("1", "2"), electrical_type: str = "passive") -> tuple[int, int, dict]:
    return 6, 4, {names[0]: port(-3, 0, "west", electrical_type), names[1]: port(3, 0, "east", electrical_type)}


def vertical_control(names: tuple[str, str, str]) -> tuple[int, int, dict]:
    return 6, 7, {
        names[0]: port(-3, 0, "west", "input"),
        names[1]: port(0, -3, "north"),
        names[2]: port(0, 3, "south"),
    }


def block(left: list[tuple[str, str]], right: list[tuple[str, str]], width: int = 8) -> tuple[int, int, dict]:
    count = max(len(left), len(right), 1)
    height = max(6, count * 2 + 2)
    offsets = [-(count - 1) + index * 2 for index in range(count)]
    ports = {}
    for index, (name, electrical_type) in enumerate(left):
        ports[name] = port(-(width // 2), offsets[index], "west", electrical_type)
    for index, (name, electrical_type) in enumerate(right):
        ports[name] = port(width // 2, offsets[index], "east", electrical_type)
    return width, height, ports


def passive_geometry(drawing: str) -> tuple[str, int, int, dict]:
    if drawing in {"resistor_var", "trimmer"}:
        width, height, ports = block([("1", "passive")], [("2", "passive")], 6)
        ports["W"] = port(0, -3, "north")
        return "potentiometer", 6, 6, ports
    if drawing in {"ntc", "ptc", "varistor"}:
        width, height, ports = horizontal()
        return "thermistor_ntc", width, height, ports
    if drawing == "resistor_array":
        width, height, ports = block([("1", "passive"), ("2", "passive")], [("3", "passive"), ("4", "passive")])
        return "generic_4p", width, height, ports
    if drawing.startswith("capacitor") or drawing in {"supercap", "feedthrough_cap", "mic_cap"}:
        names = ("+", "-") if drawing in {"capacitor_polar", "supercap", "mic_cap"} else ("1", "2")
        width, height, ports = horizontal(names)
        return "capacitor", width, height, ports
    if drawing == "common_mode":
        width, height, ports = block([("L1", "power_in"), ("L2", "power_in")], [("R1", "power_out"), ("R2", "power_out")])
        return "transformer", width, height, ports
    if drawing == "transformer_ct":
        width, height, ports = block([("P1", "power_in"), ("P2", "power_in")], [("S1", "power_out"), ("CT", "power_out"), ("S2", "power_out")])
        return "transformer", width, height, ports
    if drawing == "autotransformer":
        width, height, ports = block([("A", "power_in")], [("TAP", "power_out"), ("B", "power_out")])
        return "transformer", width, height, ports
    if drawing in {"current_transformer", "pulse_transformer", "coupled_inductors"}:
        width, height, ports = block([("P1", "power_in"), ("P2", "power_in")], [("S1", "power_out"), ("S2", "power_out")])
        return "transformer", width, height, ports
    if drawing == "resonator":
        width, height, ports = block([("1", "passive")], [("2", "passive")], 6)
        ports["GND"] = port(0, 3, "south", "ground")
        return "crystal", 6, 6, ports
    if drawing == "emi_filter":
        width, height, ports = block([("IN+", "power_in"), ("IN-", "power_in")], [("OUT+", "power_out"), ("OUT-", "power_out")])
        return "generic_4p", width, height, ports
    width, height, ports = horizontal()
    template = "inductor" if drawing.startswith("inductor") else "crystal" if drawing == "crystal" else "resistor_iec"
    return template, width, height, ports


def semiconductor_geometry(drawing: str, symbol_id: str) -> tuple[str, int, int, dict]:
    if drawing in {"dual_diode_k", "dual_diode_a"}:
        names = ([("A1", "passive"), ("A2", "passive")], [("K", "passive")]) if drawing.endswith("_k") else ([("A", "passive")], [("K1", "passive"), ("K2", "passive")])
        width, height, ports = block(*names)
        return "dual_diode", width, height, ports
    if drawing == "bridge":
        width, height, ports = block([("AC1", "power_in"), ("AC2", "power_in")], [("+", "power_out"), ("-", "power_out")])
        return "bridge_rectifier", width, height, ports
    if drawing in {"npn", "darlington_npn", "digital_npn", "phototransistor"}:
        names = ("IN", "C", "E") if drawing == "digital_npn" else ("B", "C", "E")
        return ("bjt_npn", *vertical_control(names))
    if drawing in {"pnp", "darlington_pnp", "digital_pnp"}:
        names = ("IN", "C", "E") if drawing == "digital_pnp" else ("B", "C", "E")
        return ("bjt_pnp", *vertical_control(names))
    if drawing in {"nmos", "pmos", "nmos_body", "pmos_body", "njfet", "pjfet", "semiconductor"}:
        return ("mosfet_n", *vertical_control(("G", "D", "S")))
    if drawing == "dual_gate_mos":
        width, height, ports = block([("G1", "input"), ("G2", "input")], [("D", "passive"), ("S", "passive")])
        return "mosfet_n", width, height, ports
    if drawing in {"igbt_n", "igbt_diode"}:
        return ("bjt_npn", *vertical_control(("G", "C", "E")))
    if drawing == "ujt":
        return ("bjt_npn", *vertical_control(("E", "B1", "B2")))
    if drawing in {"scr", "gto"}:
        return ("thyristor", *vertical_control(("G", "A", "K")))
    if drawing == "scs":
        width, height, ports = block([("GA", "input"), ("GK", "input")], [("A", "passive"), ("K", "passive")])
        return "thyristor", width, height, ports
    if drawing == "triac":
        return ("triac", *vertical_control(("G", "MT2", "MT1")))
    if drawing in {"optotriac", "optotriac_zero"}:
        width, height, ports = block([("A", "input"), ("K", "input")], [("MT1", "output"), ("MT2", "output")])
        return "optocoupler", width, height, ports
    if drawing in {"diac", "sidac", "tvs_bi"}:
        width, height, ports = horizontal(("1", "2"))
        return "diode", width, height, ports
    width, height, ports = horizontal(("A", "K"))
    if drawing in {"led", "laser_diode"}:
        return "diode_emit", width, height, ports
    if drawing in {"photodiode"}:
        return "diode_receive", width, height, ports
    return "diode", width, height, ports


def opto_geometry(drawing: str) -> tuple[str, int, int, dict]:
    if drawing in {"opto_transistor", "opto_darlington"}:
        width, height, ports = block([("A", "input"), ("K", "input")], [("C", "output"), ("E", "output")])
    elif drawing == "opto_logic":
        width, height, ports = block([("A", "input"), ("K", "input"), ("VCC1", "power_in"), ("GND1", "ground")], [("VCC2", "power_in"), ("GND2", "ground"), ("OUT", "output")])
    elif drawing == "opto_linear":
        width, height, ports = block([("A", "input"), ("K", "input")], [("PD1+", "output"), ("PD1-", "output"), ("PD2+", "output"), ("PD2-", "output")])
    elif drawing in {"photomos", "ssr_ac", "ssr_dc", "opto_pv"}:
        width, height, ports = block([("IN+", "input"), ("IN-", "input")], [("OUT1", "output"), ("OUT2", "output")])
    elif drawing == "digital_isolator":
        width, height, ports = block([("VDD1", "power_in"), ("GND1", "ground"), ("IN", "input")], [("VDD2", "power_in"), ("GND2", "ground"), ("OUT", "output")])
    else:
        width, height, ports = block([("LOGIC", "input"), ("GND1", "ground")], [("BUS", "output"), ("GND2", "ground")])
    return "optocoupler", width, height, ports


def build_seed(record: dict) -> dict:
    drawing = str(record.get("tipo_dibujo") or "generic_2p")
    category = record["categoria"]
    if category == "Componentes pasivos":
        template, width, height, ports = passive_geometry(drawing)
    elif category == "Semiconductores discretos":
        template, width, height, ports = semiconductor_geometry(drawing, record["id"])
    else:
        template, width, height, ports = opto_geometry(drawing)
    return {
        "id": record["id"],
        "catalog_id": record["id"],
        "name": record.get("nombre") or record["id"],
        "kind": drawing,
        "geometry_template": template,
        "designator": record.get("designador") or "X",
        "standard_profile": "IEC_EXPERIMENTAL",
        "grid_pitch_mil": 50,
        "width": width,
        "height": height,
        "ports": ports,
        "review_status": "draft",
        "normalization_batch": TARGET_CATEGORIES[category],
        "review_scope": "Geometría, anclajes y terminales revisados para el motor experimental; no equivale a certificación normativa del símbolo.",
    }


def main() -> int:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))["symbols"]
    payload = json.loads(SEEDS.read_text(encoding="utf-8"))
    existing = {item["id"] for item in payload["symbols"]}
    additions = [build_seed(record) for record in catalog if record.get("categoria") in TARGET_CATEGORIES and record["id"] not in existing]
    payload["symbols"].extend(additions)
    payload["symbols"].sort(key=lambda item: (item["id"].startswith("ST-"), item["id"]))
    SEEDS.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {category: sum(record.get("categoria") == category for record in catalog) for category in TARGET_CATEGORIES}
    print(json.dumps({"added": len(additions), "target_categories": counts, "seed_count": len(payload["symbols"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
