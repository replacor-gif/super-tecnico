#!/usr/bin/env python3
"""Finish the original catalog and publish the first professional ElectroIA pack."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "symbols" / "catalog.json"
SEEDS = ROOT / "data" / "electroia" / "symbol-reviewed-seeds.json"
INTERNAL_AUTOMATION_PREFIX = "ST-AUTO-"


def p(name: str, electrical_type: str = "passive") -> tuple[str, str]:
    return name, electrical_type


def block_ports(
    left: list[tuple[str, str]] | None = None,
    right: list[tuple[str, str]] | None = None,
    north: list[tuple[str, str]] | None = None,
    south: list[tuple[str, str]] | None = None,
    *,
    minimum_width: int = 8,
    minimum_height: int = 6,
) -> tuple[int, int, dict]:
    left, right, north, south = left or [], right or [], north or [], south or []
    width = max(minimum_width, 2 * max(len(north), len(south), 1) + 4)
    height = max(minimum_height, 2 * max(len(left), len(right), 1) + 2)
    if width % 2:
        width += 1
    if height % 2:
        height += 1
    half_w, half_h = width // 2, height // 2

    def offsets(count: int) -> list[int]:
        return [-(count - 1) + index * 2 for index in range(count)] if count else []

    ports: dict[str, dict] = {}
    for (name, kind), y in zip(left, offsets(len(left))):
        ports[name] = {"x": -half_w, "y": y, "side": "west", "electrical_type": kind}
    for (name, kind), y in zip(right, offsets(len(right))):
        ports[name] = {"x": half_w, "y": y, "side": "east", "electrical_type": kind}
    for (name, kind), x in zip(north, offsets(len(north))):
        ports[name] = {"x": x, "y": -half_h, "side": "north", "electrical_type": kind}
    for (name, kind), x in zip(south, offsets(len(south))):
        ports[name] = {"x": x, "y": half_h, "side": "south", "electrical_type": kind}
    return width, height, ports


FINAL_ORIGINAL: dict[str, dict] = {
    "SYM-0015": dict(kind="power_down", template="source_block", north=[p("-V", "power_out")]),
    "SYM-0016": dict(kind="cell", template="source_block", north=[p("+", "power_out")], south=[p("-", "power_out")]),
    "SYM-0017": dict(kind="battery", template="source_block", north=[p("+", "power_out")], south=[p("-", "power_out")]),
    "SYM-0020": dict(kind="source_current", template="source_block", left=[p("I+", "power_out")], right=[p("I-", "power_out")]),
    "SYM-0021": dict(kind="generator", template="source_block", right=[p("L", "power_out"), p("N", "power_out")], south=[p("PE", "protective_earth")]),
    "SYM-0022": dict(kind="solar_panel", template="source_block", right=[p("PV+", "power_out"), p("PV-", "power_out")], south=[p("PE", "protective_earth")]),
    "SYM-0432": dict(kind="dependent_voltage_source", template="source_block", left=[p("CTRL+", "input"), p("CTRL-", "input")], right=[p("OUT+", "power_out"), p("OUT-", "power_out")]),
    "SYM-0433": dict(kind="dependent_current_source", template="source_block", left=[p("CTRL+", "input"), p("CTRL-", "input")], right=[p("OUT+", "power_out"), p("OUT-", "power_out")]),
    "SYM-0300": dict(kind="bell", template="installation_block", left=[p("L", "power_in")], right=[p("N", "power_in")]),
    "SYM-0301": dict(kind="siren", template="installation_block", left=[p("+", "power_in")], right=[p("-", "power_in")]),
    "SYM-0302": dict(kind="smoke_detector", template="installation_block", left=[p("L+", "power_in"), p("L-", "power_in")], right=[p("ALARM", "output")], exact=True),
    "SYM-0303": dict(kind="pir_detector", template="installation_block", left=[p("V+", "power_in"), p("GND", "ground")], right=[p("OUT", "output")], exact=True),
    "SYM-0304": dict(kind="door_contact", template="installation_block", left=[p("COM")], right=[p("NC"), p("NO")]),
    "SYM-0383": dict(kind="timer_on_delay", template="installation_block", left=[p("A1", "power_in"), p("A2", "power_in")], right=[p("COM"), p("NO"), p("NC")], exact=True),
    "SYM-0384": dict(kind="timer_off_delay", template="installation_block", left=[p("A1", "power_in"), p("A2", "power_in")], right=[p("COM"), p("NO"), p("NC")], exact=True),
    "SYM-0389": dict(kind="socket_3phase", template="installation_block", left=[p("L1", "power_in"), p("L2", "power_in"), p("L3", "power_in"), p("N", "power_in")], south=[p("PE", "protective_earth")], exact=True),
    "SYM-0413": dict(kind="vacuum_diode", template="special_device_block", left=[p("A"), p("H1", "power_in")], right=[p("K"), p("H2", "power_in")]),
    "SYM-0414": dict(kind="vacuum_triode", template="special_device_block", left=[p("G", "input"), p("H1", "power_in")], right=[p("A"), p("K"), p("H2", "power_in")]),
    "SYM-0415": dict(kind="vacuum_pentode", template="special_device_block", left=[p("G1", "input"), p("G2", "input"), p("G3", "input"), p("H1", "power_in")], right=[p("A"), p("K"), p("H2", "power_in")]),
    "SYM-0416": dict(kind="fluorescent_lamp", template="special_device_block", left=[p("E1A"), p("E1B")], right=[p("E2A"), p("E2B")], exact=True),
    "SYM-0417": dict(kind="neon_lamp", template="special_device_block", left=[p("1")], right=[p("2")]),
}


PROFESSIONAL: dict[str, dict] = {
    "SYM-0461": dict(kind="plc_cpu", left=[p("L+", "power_in"), p("M", "ground"), p("IO_BUS", "bidirectional")], right=[p("ETH", "bidirectional"), p("FIELD_BUS", "bidirectional"), p("SERVICE", "bidirectional")]),
    "SYM-0462": dict(kind="safety_plc", left=[p("L+", "power_in"), p("M", "ground"), p("SAFE_IN", "input")], right=[p("SAFE_OUT", "output"), p("SAFE_BUS", "bidirectional"), p("DIAG", "output")]),
    "SYM-0463": dict(kind="plc_di_module", left=[p("I0", "input"), p("I1", "input"), p("I2", "input"), p("I3", "input")], right=[p("L+", "power_in"), p("M", "ground"), p("BACKPLANE", "bidirectional")]),
    "SYM-0464": dict(kind="plc_do_module", left=[p("L+", "power_in"), p("M", "ground"), p("BACKPLANE", "bidirectional")], right=[p("Q0", "output"), p("Q1", "output"), p("Q2", "output"), p("Q3", "output")]),
    "SYM-0465": dict(kind="plc_ai_module", left=[p("AI0+", "input"), p("AI0-", "input"), p("AI1+", "input"), p("AI1-", "input")], right=[p("L+", "power_in"), p("MANA", "ground"), p("BACKPLANE", "bidirectional")]),
    "SYM-0466": dict(kind="plc_ao_module", left=[p("L+", "power_in"), p("MANA", "ground"), p("BACKPLANE", "bidirectional")], right=[p("AQ0+", "output"), p("AQ0-", "output"), p("AQ1+", "output"), p("AQ1-", "output")]),
    "SYM-0467": dict(kind="remote_io_head", left=[p("L+", "power_in"), p("M", "ground"), p("FIELD_BUS", "bidirectional")], right=[p("BACKPLANE", "bidirectional"), p("AUX_OUT", "power_out")], south=[p("FE", "functional_earth")]),
    "SYM-0468": dict(kind="industrial_hmi", left=[p("L+", "power_in"), p("M", "ground")], right=[p("ETH", "bidirectional"), p("SERIAL", "bidirectional"), p("USB", "bidirectional")]),
    "SYM-0469": dict(kind="industrial_psu_24v", left=[p("L", "power_in"), p("N", "power_in")], right=[p("L+", "power_out"), p("M", "power_out"), p("DC_OK", "output")], south=[p("PE", "protective_earth")]),
    "SYM-0470": dict(kind="industrial_switch", left=[p("L+", "power_in"), p("M", "ground")], right=[p("ETH1", "bidirectional"), p("ETH2", "bidirectional"), p("ETH3", "bidirectional"), p("ETH4", "bidirectional")], south=[p("FE", "functional_earth")]),
    "SYM-0471": dict(kind="industrial_gateway", left=[p("L+", "power_in"), p("M", "ground"), p("NETWORK_A", "bidirectional")], right=[p("NETWORK_B", "bidirectional"), p("SERVICE", "bidirectional")]),
    "SYM-0472": dict(kind="arduino_5v", left=[p("VIN", "power_in"), p("5V", "power_in"), p("GND", "ground"), p("GPIO", "bidirectional")], right=[p("ADC", "input"), p("PWM", "output"), p("I2C", "bidirectional"), p("SPI_UART", "bidirectional")]),
    "SYM-0473": dict(kind="arduino_3v3", left=[p("VIN", "power_in"), p("3V3", "power_in"), p("GND", "ground"), p("GPIO", "bidirectional")], right=[p("ADC", "input"), p("PWM", "output"), p("I2C", "bidirectional"), p("SPI_UART", "bidirectional")]),
    "SYM-0474": dict(kind="arduino_opta", left=[p("L+", "power_in"), p("M", "ground"), p("DI_GROUP", "input"), p("AI_GROUP", "input")], right=[p("RELAY_GROUP", "output"), p("RS485", "bidirectional"), p("ETH", "bidirectional")]),
    "SYM-0475": dict(kind="portenta_machine_control", left=[p("L+", "power_in"), p("M", "ground"), p("DI_AI_GROUP", "input"), p("ENCODER", "input")], right=[p("DO_AO_GROUP", "output"), p("CAN", "bidirectional"), p("RS485", "bidirectional"), p("ETH", "bidirectional")]),
    "SYM-0476": dict(kind="raspberry_pi_controller", left=[p("5V", "power_in"), p("3V3", "power_out"), p("GND", "ground"), p("GPIO", "bidirectional")], right=[p("I2C_SPI", "bidirectional"), p("UART", "bidirectional"), p("USB", "bidirectional"), p("ETH", "bidirectional")]),
    "SYM-0477": dict(kind="esp32_controller", left=[p("VIN", "power_in"), p("3V3", "power_in"), p("GND", "ground"), p("GPIO", "bidirectional")], right=[p("ADC", "input"), p("PWM", "output"), p("I2C_SPI_UART", "bidirectional"), p("RADIO", "bidirectional")]),
    "SYM-0478": dict(kind="embedded_controller", left=[p("POWER", "power_in"), p("GND", "ground"), p("ANALOG_IN", "input"), p("DIGITAL_IO", "bidirectional")], right=[p("COMM", "bidirectional"), p("PROGRAM", "bidirectional"), p("TEST", "bidirectional")]),
    "SYM-0479": dict(kind="fieldbus_coupler", left=[p("L+", "power_in"), p("M", "ground"), p("FIELD_BUS", "bidirectional")], right=[p("BACKPLANE", "bidirectional"), p("AUX_OUT", "power_out")], south=[p("FE", "functional_earth")]),
    "SYM-0480": dict(kind="iolink_master", left=[p("L+", "power_in"), p("M", "ground"), p("PORT1_CQ", "bidirectional"), p("PORT2_CQ", "bidirectional")], right=[p("PORT3_CQ", "bidirectional"), p("PORT4_CQ", "bidirectional"), p("UPLINK", "bidirectional")], south=[p("FE", "functional_earth")]),

    "SYM-0481": dict(kind="variable_frequency_drive", left=[p("R_L1", "power_in"), p("S_L2", "power_in"), p("T_L3", "power_in"), p("DI_AI", "input"), p("STO", "input"), p("BUS", "bidirectional")], right=[p("U", "power_out"), p("V", "power_out"), p("W", "power_out"), p("AO_RELAY", "output"), p("DC_BUS", "bidirectional")], south=[p("PE", "protective_earth")]),
    "SYM-0482": dict(kind="soft_starter_3phase", left=[p("1L1", "power_in"), p("3L2", "power_in"), p("5L3", "power_in"), p("CONTROL", "input")], right=[p("2T1", "power_out"), p("4T2", "power_out"), p("6T3", "power_out"), p("STATUS", "output")], south=[p("PE", "protective_earth")]),
    "SYM-0483": dict(kind="servo_drive", left=[p("L1", "power_in"), p("L2", "power_in"), p("L3", "power_in"), p("ENCODER", "input"), p("STO", "input"), p("BUS", "bidirectional")], right=[p("U", "power_out"), p("V", "power_out"), p("W", "power_out"), p("BRAKE", "output"), p("DIAG", "output")], south=[p("PE", "protective_earth")]),
    "SYM-0484": dict(kind="industrial_stepper_drive", left=[p("DC+", "power_in"), p("DC-", "power_in"), p("STEP_DIR", "input"), p("ENABLE", "input")], right=[p("A+", "power_out"), p("A-", "power_out"), p("B+", "power_out"), p("B-", "power_out"), p("ALARM", "output")]),
    "SYM-0485": dict(kind="dc_motor_drive", left=[p("POWER_IN", "power_in"), p("FIELD_REF", "input"), p("SPEED_REF", "input"), p("FEEDBACK", "input")], right=[p("A+", "power_out"), p("A-", "power_out"), p("F+", "power_out"), p("F-", "power_out"), p("ALARM", "output")], south=[p("PE", "protective_earth")]),
    "SYM-0486": dict(kind="star_delta_starter", left=[p("L1", "power_in"), p("L2", "power_in"), p("L3", "power_in"), p("START_STOP", "input")], right=[p("U1", "power_out"), p("V1", "power_out"), p("W1", "power_out"), p("U2_V2_W2", "power_out"), p("STATUS", "output")]),
    "SYM-0487": dict(kind="reversing_starter", left=[p("L1", "power_in"), p("L2", "power_in"), p("L3", "power_in"), p("FWD_REV", "input")], right=[p("U", "power_out"), p("V", "power_out"), p("W", "power_out"), p("STATUS", "output")]),
    "SYM-0488": dict(kind="motor_protection_breaker", left=[p("1L1", "power_in"), p("3L2", "power_in"), p("5L3", "power_in")], right=[p("2T1", "power_out"), p("4T2", "power_out"), p("6T3", "power_out"), p("AUX", "output")]),
    "SYM-0489": dict(kind="safety_relay", left=[p("A1", "power_in"), p("A2", "ground"), p("CH1", "input"), p("CH2", "input"), p("RESET", "input")], right=[p("13_14", "output"), p("23_24", "output"), p("DIAG", "output")]),
    "SYM-0490": dict(kind="solid_state_contactor_3phase", left=[p("L1", "power_in"), p("L2", "power_in"), p("L3", "power_in"), p("CONTROL", "input")], right=[p("T1", "power_out"), p("T2", "power_out"), p("T3", "power_out"), p("ALARM", "output")], south=[p("PE", "protective_earth")]),
    "SYM-0491": dict(kind="automatic_transfer_switch", left=[p("NORMAL", "power_in"), p("RESERVE", "power_in"), p("CONTROL", "input")], right=[p("LOAD", "power_out"), p("STATUS", "output")], south=[p("PE_N", "protective_earth")]),
    "SYM-0492": dict(kind="ups_system", left=[p("INPUT", "power_in"), p("BYPASS", "power_in"), p("BATTERY", "bidirectional"), p("EPO", "input")], right=[p("OUTPUT", "power_out"), p("STATUS", "output"), p("COMM", "bidirectional")], south=[p("PE", "protective_earth")]),

    "SYM-0493": dict(kind="bms_ddc_controller", left=[p("24V", "power_in"), p("COM", "ground"), p("UI_GROUP", "input"), p("DI_GROUP", "input")], right=[p("UO_GROUP", "output"), p("DO_GROUP", "output"), p("RS485", "bidirectional"), p("ETH", "bidirectional")]),
    "SYM-0494": dict(kind="room_controller", left=[p("POWER", "power_in"), p("SENSOR", "input"), p("OCCUPANCY", "input")], right=[p("VALVE", "output"), p("FAN", "output"), p("BUS", "bidirectional")]),
    "SYM-0495": dict(kind="ahu_controller", left=[p("POWER", "power_in"), p("SENSORS", "input"), p("SAFETIES", "input"), p("BMS_BUS", "bidirectional")], right=[p("FANS_VFD", "output"), p("DAMPERS", "output"), p("COILS", "output"), p("ALARMS", "output")]),
    "SYM-0496": dict(kind="refrigeration_controller", left=[p("POWER", "power_in"), p("PROBES", "input"), p("DIGITAL_IN", "input"), p("BUS", "bidirectional")], right=[p("COMPRESSOR", "output"), p("FANS", "output"), p("DEFROST", "output"), p("EEV", "output"), p("ALARM", "output")]),
    "SYM-0497": dict(kind="burner_boiler_controller", left=[p("POWER", "power_in"), p("THERMOSTATS", "input"), p("PRESSOSTATS", "input"), p("FLAME", "input")], right=[p("FAN", "output"), p("IGNITION", "output"), p("VALVES", "output"), p("BUS", "bidirectional")]),
    "SYM-0498": dict(kind="booster_pump_controller", left=[p("POWER", "power_in"), p("PRESSURE", "input"), p("LEVEL", "input"), p("SAFETIES", "input")], right=[p("PUMP1", "output"), p("PUMP2", "output"), p("VFD_REF", "output"), p("ALARM_BUS", "bidirectional")]),
    "SYM-0499": dict(kind="fire_alarm_panel", left=[p("MAINS", "power_in"), p("BATTERY", "bidirectional"), p("LOOP_ZONES", "bidirectional")], right=[p("SOUNDERS", "output"), p("RELAYS", "output"), p("NETWORK", "bidirectional")], south=[p("PE", "protective_earth")]),
    "SYM-0500": dict(kind="knx_device", left=[p("KNX+", "bidirectional"), p("KNX-", "bidirectional"), p("AUX_POWER", "power_in")], right=[p("INPUTS", "input"), p("OUTPUTS", "output")]),
    "SYM-0501": dict(kind="source_3phase", right=[p("L1", "power_out"), p("L2", "power_out"), p("L3", "power_out"), p("N", "power_out")], south=[p("PE", "protective_earth")]),
}


def make_seed(record: dict, spec: dict, batch: str) -> dict:
    width, height, ports = block_ports(
        spec.get("left"),
        spec.get("right"),
        spec.get("north"),
        spec.get("south"),
        minimum_width=spec.get("width", 8),
        minimum_height=spec.get("height", 6),
    )
    professional = record["id"] in PROFESSIONAL
    exact_model = bool(spec.get("exact")) or professional
    return {
        "id": record["id"],
        "catalog_id": record["id"],
        "name": record["nombre"],
        "kind": spec["kind"],
        "geometry_template": spec["kind"],
        "designator": record.get("designador") or "X",
        "standard_profile": "IEC_EXPERIMENTAL",
        "grid_pitch_mil": 50,
        "width": width,
        "height": height,
        "ports": ports,
        "review_status": "draft",
        "normalization_batch": batch,
        "terminal_model": "functional_group" if professional else "explicit",
        "requires_exact_model": exact_model,
        "review_scope": (
            "Bloque funcional profesional con dominios de potencia, señal, comunicaciones, seguridad y tierra separados. "
            "No representa el pinout de un fabricante: el modelo, variante, manual y borneros exactos son obligatorios."
            if professional
            else "Geometría, anclajes, función y terminales explícitos revisados para el motor. La variante exacta debe confirmarse cuando el símbolo lo indique."
        ),
    }


def main() -> int:
    catalog_payload = json.loads(CATALOG.read_text(encoding="utf-8"))
    catalog = catalog_payload["symbols"]
    if len(catalog) != 501:
        raise SystemExit(f"Se esperaba el catálogo ampliado de 501 símbolos y hay {len(catalog)}")
    records = {item["id"]: item for item in catalog}
    payload = json.loads(SEEDS.read_text(encoding="utf-8"))
    targets = {**FINAL_ORIGINAL, **PROFESSIONAL}
    payload["symbols"] = [
        item for item in payload["symbols"]
        if not str(item["id"]).startswith(INTERNAL_AUTOMATION_PREFIX) and item["id"] not in targets
    ]
    missing_records = sorted(set(targets) - set(records))
    if missing_records:
        raise SystemExit("Faltan fichas en el catálogo: " + ", ".join(missing_records))
    additions = []
    for symbol_id, spec in targets.items():
        batch = "original_catalog_complete_2026_08" if symbol_id in FINAL_ORIGINAL else "professional_pack_automation_drives_buildings_2026_08"
        additions.append(make_seed(records[symbol_id], spec, batch))
    if len(additions) != 62:
        raise SystemExit(f"Se esperaban 62 semillas nuevas y se obtuvieron {len(additions)}")
    payload["symbols"].extend(additions)
    payload["symbols"].sort(key=lambda item: (item["id"].startswith("ST-"), item["id"]))
    SEEDS.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "added": len(additions),
        "removed_internal_automation": 11,
        "public_catalog": len(catalog),
        "seed_count": len(payload["symbols"]),
        "professional_symbols": len(PROFESSIONAL),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
