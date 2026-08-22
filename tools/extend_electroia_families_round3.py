#!/usr/bin/env python3
"""Normalize sensors, measurement and connector families for ElectroIA."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "symbols" / "catalog.json"
SEEDS = ROOT / "data" / "electroia" / "symbol-reviewed-seeds.json"
TARGETS = {
    "Sensores y transductores": ("sensor_block", "sensors_complete_2026_08"),
    "Medida e indicación": ("meter_block", "measurement_complete_2026_08"),
    "Conectores y comunicaciones": ("connector_block", "connectors_complete_2026_08"),
}


def pin(name: str, electrical_type: str = "passive") -> tuple[str, str]:
    return name, electrical_type


def make_ports(
    left: list[tuple[str, str]],
    right: list[tuple[str, str]],
    north: list[tuple[str, str]] | None = None,
    south: list[tuple[str, str]] | None = None,
) -> tuple[int, int, dict]:
    north = north or []
    south = south or []
    rows = max(len(left), len(right), 1)
    width = max(8, 2 * max(len(north), len(south), 1) + 4)
    height = max(6, rows * 2 + 2)
    half_w, half_h = width // 2, height // 2

    def offsets(count: int) -> list[int]:
        return [-(count - 1) + index * 2 for index in range(count)] if count else []

    ports = {}
    for (name, kind), y in zip(left, offsets(len(left))):
        ports[name] = {"x": -half_w, "y": y, "side": "west", "electrical_type": kind}
    for (name, kind), y in zip(right, offsets(len(right))):
        ports[name] = {"x": half_w, "y": y, "side": "east", "electrical_type": kind}
    for (name, kind), x in zip(north, offsets(len(north))):
        ports[name] = {"x": x, "y": -half_h, "side": "north", "electrical_type": kind}
    for (name, kind), x in zip(south, offsets(len(south))):
        ports[name] = {"x": x, "y": half_h, "side": "south", "electrical_type": kind}
    return width, height, ports


def powered_sensor(output: str = "OUT") -> tuple[list, list, list, list]:
    return [], [pin(output, "output")], [pin("VCC", "power_in")], [pin("GND", "ground")]


def sensor_signature(record: dict) -> tuple[list, list, list, list]:
    drawing = str(record.get("tipo_dibujo") or "")
    if record["id"] == "SYM-0440":
        return [pin("CLOCK", "input")], [pin("DATA", "output")], [pin("VCC", "power_in")], [pin("GND", "ground")]
    if record["id"] == "SYM-0441":
        return [pin("REF+", "passive"), pin("REF-", "passive")], [pin("SIN+", "output"), pin("SIN-", "output"), pin("COS+", "output"), pin("COS-", "output")], [], []
    signatures = {
        "hall_switch": powered_sensor(),
        "hall_linear": powered_sensor(),
        "prox_ind": powered_sensor(),
        "prox_cap": powered_sensor(),
        "encoder": ([], [pin("A", "output"), pin("B", "output"), pin("Z", "output")], [pin("VCC", "power_in")], [pin("GND", "ground")]),
        "tachogenerator": ([pin("SIG+", "passive")], [pin("SIG-", "passive")], [], []),
        "vibration": powered_sensor(),
        "light_sensor": powered_sensor(),
        "ir_receiver": powered_sensor(),
        "gas_sensor": ([pin("H+", "passive"), pin("H-", "passive")], [pin("SIG+", "output"), pin("SIG-", "output")], [], []),
        "strain_gauge": ([pin("EXC+", "passive"), pin("EXC-", "passive")], [pin("SIG+", "output"), pin("SIG-", "output")], [], []),
        "load_cell": ([pin("EXC+", "power_in"), pin("EXC-", "power_in")], [pin("SIG+", "output"), pin("SIG-", "output")], [], []),
        "piezo_sensor": ([pin("+", "passive")], [pin("-", "passive")], [], []),
        "ultrasonic": ([pin("TX", "passive")], [pin("RX", "passive")], [], []),
        "thermopile": ([pin("+", "passive")], [pin("-", "passive")], [], []),
        "position_pot": ([pin("A", "passive")], [pin("W", "output"), pin("B", "passive")], [], []),
        "lvdt": ([pin("PRI+", "passive"), pin("PRI-", "passive")], [pin("S1+", "output"), pin("S1-", "output"), pin("S2+", "output"), pin("S2-", "output")], [], []),
        "magnetoresistive": ([], [pin("OUT+", "output"), pin("OUT-", "output")], [pin("VCC", "power_in")], [pin("GND", "ground")]),
        "gyroscope": ([pin("BUS", "bidirectional")], [pin("IRQ", "output")], [pin("VCC", "power_in")], [pin("GND", "ground")]),
        "accelerometer": ([pin("BUS", "bidirectional")], [pin("IRQ", "output")], [pin("VCC", "power_in")], [pin("GND", "ground")]),
        "color_sensor": ([pin("BUS", "bidirectional")], [pin("OUT", "output")], [pin("VCC", "power_in")], [pin("GND", "ground")]),
        "ph_sensor": ([pin("ELECTRODE", "input"), pin("REF", "input")], [pin("SIGNAL", "output")], [], []),
        "conductivity": ([pin("E1", "passive"), pin("E2", "passive")], [pin("SENSE", "output")], [pin("EXC", "power_in")], []),
    }
    if drawing not in signatures:
        raise ValueError(f"Firma de sensor pendiente: {drawing}")
    return signatures[drawing]


def meter_signature(drawing: str) -> tuple[list, list, list, list]:
    signatures = {
        "voltmeter": ([pin("V+", "input")], [pin("V-", "input")], [], []),
        "ammeter": ([pin("I+", "passive")], [pin("I-", "passive")], [], []),
        "ohmmeter": ([pin("Ω+", "output")], [pin("Ω-", "input")], [], []),
        "wattmeter": ([pin("I+", "passive"), pin("V+", "input")], [pin("I-", "passive"), pin("V-", "input")], [], []),
        "freqmeter": ([pin("IN+", "input")], [pin("IN-", "input")], [], []),
        "scope": ([pin("CH1", "input")], [pin("REF", "ground")], [], []),
        "lamp": ([pin("+", "passive")], [pin("-", "passive")], [], []),
        "buzzer": ([pin("+", "passive")], [pin("-", "passive")], [], []),
        "speaker": ([pin("+", "passive")], [pin("-", "passive")], [], []),
        "sevenseg": ([pin("SEGMENTS[]", "input")], [pin("COMMON[]", "passive")], [pin("VCC", "power_in")], [pin("GND", "ground")]),
        "probe_v": ([pin("TIP", "input")], [pin("REF", "ground")], [], []),
        "probe_i": ([pin("IP+", "passive")], [pin("IP-", "passive")], [], []),
    }
    if drawing not in signatures:
        raise ValueError(f"Firma de medida pendiente: {drawing}")
    return signatures[drawing]


def connector_signature(drawing: str) -> tuple[list, list, list, list]:
    signatures = {
        "connector_male": ([], [pin("1", "passive")], [], []),
        "connector_female": ([pin("1", "passive")], [], [], []),
        "connector_multi": ([pin("PINS[]", "bidirectional")], [pin("SHIELD", "shield")], [], []),
        "coax": ([pin("CENTER", "bidirectional")], [pin("SHIELD", "shield")], [], []),
        "twisted_pair": ([pin("A_IN", "bidirectional"), pin("B_IN", "bidirectional")], [pin("A_OUT", "bidirectional"), pin("B_OUT", "bidirectional")], [], []),
        "shielded_cable": ([pin("LINES_IN[]", "bidirectional"), pin("SHIELD_IN", "shield")], [pin("LINES_OUT[]", "bidirectional"), pin("SHIELD_OUT", "shield")], [], []),
        "antenna": ([pin("RF", "passive")], [], [], []),
        "usb": ([pin("VBUS", "power_in"), pin("D+", "bidirectional"), pin("D-", "bidirectional")], [pin("GND", "ground"), pin("SHIELD", "shield")], [], []),
        "differential_line": ([pin("P_IN", "bidirectional"), pin("N_IN", "bidirectional")], [pin("P_OUT", "bidirectional"), pin("N_OUT", "bidirectional")], [], []),
        "fiber": ([pin("OPT_IN", "input")], [pin("OPT_OUT", "output")], [], []),
    }
    if drawing not in signatures:
        raise ValueError(f"Firma de conexión pendiente: {drawing}")
    return signatures[drawing]


def build_seed(record: dict) -> dict:
    category = record["categoria"]
    geometry_template, batch = TARGETS[category]
    drawing = str(record.get("tipo_dibujo") or "")
    if category == "Sensores y transductores":
        left, right, north, south = sensor_signature(record)
    elif category == "Medida e indicación":
        left, right, north, south = meter_signature(drawing)
    else:
        left, right, north, south = connector_signature(drawing)
    width, height, ports = make_ports(left, right, north, south)
    return {
        "id": record["id"],
        "catalog_id": record["id"],
        "name": record.get("nombre") or record["id"],
        "kind": drawing,
        "geometry_template": geometry_template,
        "designator": record.get("designador") or "X",
        "standard_profile": "IEC_EXPERIMENTAL",
        "grid_pitch_mil": 50,
        "width": width,
        "height": height,
        "ports": ports,
        "review_status": "draft",
        "normalization_batch": batch,
        "review_scope": "Geometría funcional, anclajes y terminales eléctricos revisados para el motor experimental. Los grupos de terminales representan la función; el pinout físico y la variante exacta deben confirmarse con la ficha del equipo.",
    }


def main() -> int:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))["symbols"]
    payload = json.loads(SEEDS.read_text(encoding="utf-8"))
    existing = {item["id"] for item in payload["symbols"]}
    additions = [build_seed(record) for record in catalog if record.get("categoria") in TARGETS and record["id"] not in existing]
    if len(additions) != 47:
        raise SystemExit(f"Se esperaban 47 símbolos nuevos y se obtuvieron {len(additions)}")
    payload["symbols"].extend(additions)
    payload["symbols"].sort(key=lambda item: (item["id"].startswith("ST-"), item["id"]))
    SEEDS.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"added": len(additions), "seed_count": len(payload["symbols"]), "categories": list(TARGETS)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
