#!/usr/bin/env python3
"""Normalize three large ElectroIA families with named functional terminals."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "symbols" / "catalog.json"
SEEDS = ROOT / "data" / "electroia" / "symbol-reviewed-seeds.json"
TARGETS = {
    "Circuitos integrados funcionales": ("functional_block", "functional_ics_2026_08"),
    "Electrónica digital": ("digital_block", "digital_electronics_2026_08"),
    "Potencia y climatización": ("power_block", "power_hvac_2026_08"),
}


def pin(name: str, electrical_type: str = "passive") -> tuple[str, str]:
    return name, electrical_type


def make_ports(left: list[tuple[str, str]], right: list[tuple[str, str]], north: list[tuple[str, str]] | None = None, south: list[tuple[str, str]] | None = None) -> tuple[int, int, dict]:
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


def digital_signature(drawing: str) -> tuple[list, list, list, list]:
    two_gate = {"gate_and", "gate_nand", "gate_or", "gate_nor", "gate_xor", "gate_xnor", "gate_iec"}
    one_gate = {"gate_not", "gate_buffer", "gate_schmitt", "open_collector", "open_drain"}
    if drawing in two_gate:
        return [pin("A", "input"), pin("B", "input")], [pin("Q", "output")], [], []
    if drawing in one_gate:
        return [pin("A", "input")], [pin("Q", "output")], [], []
    if drawing == "gate_tristate":
        return [pin("A", "input"), pin("OE", "input")], [pin("Q", "tri_state")], [], []
    signatures = {
        "flipflop_d": ([pin("D", "input"), pin("CLK", "input"), pin("SET", "input"), pin("RESET", "input")], [pin("Q", "output"), pin("nQ", "output")]),
        "flipflop_jk": ([pin("J", "input"), pin("K", "input"), pin("CLK", "input")], [pin("Q", "output"), pin("nQ", "output")]),
        "flipflop_t": ([pin("T", "input"), pin("CLK", "input")], [pin("Q", "output")]),
        "latch_sr": ([pin("S", "input"), pin("R", "input")], [pin("Q", "output"), pin("nQ", "output")]),
        "latch_d": ([pin("D", "input"), pin("EN", "input")], [pin("Q", "output")]),
        "counter": ([pin("CLK", "input"), pin("RESET", "input")], [pin("Q[]", "output")]),
        "register": ([pin("D[]", "input"), pin("CLK", "input")], [pin("Q[]", "output")]),
        "shift_register": ([pin("SER", "input"), pin("CLK", "input"), pin("LOAD", "input")], [pin("Q[]", "output")]),
        "digital_mux": ([pin("D[]", "input"), pin("SEL[]", "input")], [pin("Q", "output")]),
        "digital_demux": ([pin("D", "input"), pin("SEL[]", "input")], [pin("Q[]", "output")]),
        "encoder_block": ([pin("IN[]", "input")], [pin("CODE[]", "output")]),
        "decoder_block": ([pin("CODE[]", "input")], [pin("OUT[]", "output")]),
        "digital_comparator": ([pin("A[]", "input"), pin("B[]", "input")], [pin("A_GT_B", "output"), pin("A_EQ_B", "output"), pin("A_LT_B", "output")]),
        "adder": ([pin("A[]", "input"), pin("B[]", "input"), pin("CIN", "input")], [pin("SUM[]", "output"), pin("COUT", "output")]),
        "rom": ([pin("ADDR[]", "input"), pin("CE", "input")], [pin("DATA[]", "output")]),
        "ram": ([pin("ADDR[]", "input"), pin("DATA_IN[]", "input"), pin("WE", "input")], [pin("DATA_OUT[]", "tri_state")]),
        "eeprom": ([pin("BUS", "bidirectional"), pin("WP", "input")], [pin("READY", "output")]),
        "flash": ([pin("SPI_QSPI", "bidirectional"), pin("CS", "input")], [pin("READY", "output")]),
        "mcu": ([pin("GPIO_A", "bidirectional"), pin("BUS_A", "bidirectional"), pin("RESET", "input")], [pin("GPIO_B", "bidirectional"), pin("BUS_B", "bidirectional"), pin("DEBUG", "bidirectional")]),
        "cpu": ([pin("ADDR[]", "output"), pin("DATA[]", "bidirectional"), pin("RESET", "input")], [pin("CONTROL[]", "bidirectional"), pin("IRQ", "input")]),
        "dsp": ([pin("DATA_IN", "input"), pin("BUS", "bidirectional")], [pin("DATA_OUT", "output"), pin("PERIPH", "bidirectional")]),
        "fpga": ([pin("IO_BANK_A", "bidirectional"), pin("CONFIG", "input")], [pin("IO_BANK_B", "bidirectional"), pin("DEBUG", "bidirectional")]),
        "cpld": ([pin("IO_A", "bidirectional"), pin("CLK", "input")], [pin("IO_B", "bidirectional")]),
        "rtc": ([pin("BUS", "bidirectional"), pin("XTAL", "passive")], [pin("IRQ", "output")]),
        "display_driver": ([pin("BUS", "input"), pin("CONTROL", "input")], [pin("SEGMENTS", "output"), pin("COMMONS", "output")]),
        "io_expander": ([pin("I2C_SPI", "bidirectional"), pin("IRQ", "output")], [pin("GPIO[]", "bidirectional")]),
        "rs232": ([pin("TX_LOGIC", "input"), pin("RX_LOGIC", "output")], [pin("TX_LINE", "output"), pin("RX_LINE", "input")]),
        "rs485": ([pin("DI", "input"), pin("DE", "input"), pin("nRE", "input"), pin("RO", "output")], [pin("A", "bidirectional"), pin("B", "bidirectional")]),
        "can": ([pin("TXD", "input"), pin("RXD", "output")], [pin("CANH", "bidirectional"), pin("CANL", "bidirectional")]),
        "lin": ([pin("TXD", "input"), pin("RXD", "output")], [pin("LIN", "bidirectional")]),
        "level_shifter": ([pin("A[]", "bidirectional"), pin("OE", "input")], [pin("B[]", "bidirectional")]),
        "bus_isolator": ([pin("BUS_1", "bidirectional")], [pin("BUS_2", "bidirectional")]),
        "monostable": ([pin("TRIG", "input"), pin("RC", "passive")], [pin("Q", "output")]),
        "freq_divider": ([pin("CLK", "input"), pin("RESET", "input")], [pin("OUT", "output")]),
        "edge_detector": ([pin("IN", "input")], [pin("OUT", "output")]),
        "alu": ([pin("A[]", "input"), pin("B[]", "input"), pin("OP[]", "input")], [pin("RESULT[]", "output"), pin("FLAGS", "output")]),
        "bus_transceiver": ([pin("BUS_A", "bidirectional"), pin("DIR", "input"), pin("OE", "input")], [pin("BUS_B", "bidirectional")]),
        "line_driver": ([pin("IN", "input")], [pin("OUT", "output")]),
        "line_receiver": ([pin("IN+", "input"), pin("IN-", "input")], [pin("OUT", "output")]),
        "debounce": ([pin("SW_IN", "input")], [pin("OUT", "output")]),
        "clock_gen": ([pin("REF", "input")], [pin("CLK[]", "output")]),
        "clock_buffer": ([pin("CLK_IN", "input")], [pin("CLK_OUT[]", "output")]),
        "sram": ([pin("ADDR[]", "input"), pin("DATA[]", "bidirectional"), pin("CE", "input"), pin("OE", "input"), pin("WE", "input")], [pin("READY", "output")]),
        "dram": ([pin("ADDR[]", "input"), pin("DATA[]", "bidirectional"), pin("RAS", "input"), pin("CAS", "input")], [pin("READY", "output")]),
        "fram": ([pin("BUS", "bidirectional"), pin("CS", "input")], [pin("READY", "output")]),
        "nvram": ([pin("ADDR[]", "input"), pin("DATA[]", "bidirectional"), pin("CONTROL", "input")], [pin("READY", "output")]),
        "fifo": ([pin("DATA_IN[]", "input"), pin("WR_CLK", "input")], [pin("DATA_OUT[]", "output"), pin("RD_CLK", "input"), pin("FLAGS", "output")]),
        "keyboard_ctrl": ([pin("ROWS[]", "bidirectional"), pin("COLS[]", "bidirectional")], [pin("BUS", "bidirectional")]),
        "touch_ctrl": ([pin("ELECTRODES[]", "input")], [pin("BUS", "bidirectional"), pin("IRQ", "output")]),
        "crc": ([pin("DATA[]", "input"), pin("CLK", "input")], [pin("CRC[]", "output")]),
        "dma": ([pin("BUS_IN", "bidirectional"), pin("REQUEST", "input")], [pin("BUS_OUT", "bidirectional"), pin("ACK", "output")]),
        "bus_bridge": ([pin("BUS_A", "bidirectional")], [pin("BUS_B", "bidirectional")]),
        "usb_ctrl": ([pin("INTERNAL_BUS", "bidirectional"), pin("VBUS", "power_in")], [pin("D+", "bidirectional"), pin("D-", "bidirectional")]),
        "ethernet_ctrl": ([pin("MII_RMII", "bidirectional")], [pin("TX_PAIR", "output"), pin("RX_PAIR", "input")]),
    }
    if drawing not in signatures:
        raise ValueError(f"Firma digital pendiente: {drawing}")
    left, right = signatures[drawing]
    return left, right, [pin("VCC", "power_in")], [pin("GND", "ground")]


def functional_signature(drawing: str) -> tuple[list, list, list, list]:
    if drawing in {"opamp", "comparator", "instrumentation_amp", "difference_amp", "current_amp", "transimpedance", "log_amp", "window_comp"}:
        left = [pin("IN+", "input"), pin("IN-", "input")]
        if drawing == "instrumentation_amp": left.append(pin("REF", "input"))
        if drawing == "window_comp": left = [pin("IN", "input"), pin("LOW", "input"), pin("HIGH", "input")]
        return left, [pin("OUT", "output")], [pin("VCC+", "power_in")], [pin("VCC-", "power_in")]
    signatures = {
        "isolation_amp": ([pin("IN+", "input"), pin("IN-", "input"), pin("GND1", "ground")], [pin("OUT", "output"), pin("GND2", "ground")]),
        "buffer_analog": ([pin("IN", "input")], [pin("OUT", "output")]),
        "analog_switch": ([pin("IN_OUT_A", "bidirectional"), pin("CTRL", "input")], [pin("IN_OUT_B", "bidirectional")]),
        "analog_mux": ([pin("IN[]", "input"), pin("SEL[]", "input")], [pin("COMMON", "bidirectional")]),
        "analog_demux": ([pin("COMMON", "bidirectional"), pin("SEL[]", "input")], [pin("OUT[]", "output")]),
        "adc": ([pin("AIN[]", "input"), pin("REF", "input")], [pin("DIGITAL_BUS", "output")]),
        "dac": ([pin("DIGITAL_BUS", "input"), pin("REF", "input")], [pin("AOUT", "output")]),
        "voltage_ref": ([pin("IN", "power_in")], [pin("VREF", "power_out")]),
        "linear_reg": ([pin("VIN", "power_in"), pin("ADJ", "input")], [pin("VOUT", "power_out")]),
        "ldo": ([pin("VIN", "power_in"), pin("EN", "input")], [pin("VOUT", "power_out")]),
        "buck": ([pin("VIN", "power_in"), pin("FB", "input")], [pin("SW", "power_out")]),
        "boost": ([pin("VIN", "power_in"), pin("FB", "input")], [pin("SW", "power_out")]),
        "buckboost": ([pin("VIN", "power_in"), pin("FB", "input")], [pin("SW1", "power_out"), pin("SW2", "power_out")]),
        "flyback_ctrl": ([pin("FB", "input"), pin("CS", "input")], [pin("GATE", "output")]),
        "llc_ctrl": ([pin("FB", "input"), pin("PROTECT", "input")], [pin("HO", "output"), pin("LO", "output")]),
        "pfc_ctrl": ([pin("VRECT", "input"), pin("CS", "input"), pin("ZCD", "input"), pin("FB", "input")], [pin("GATE", "output")]),
        "pwm_ctrl": ([pin("FB", "input"), pin("CS", "input"), pin("RT_CT", "passive")], [pin("OUT", "output")]),
        "timer555": ([pin("TRIG", "input"), pin("THRESH", "input"), pin("RESET", "input")], [pin("OUT", "output"), pin("DISCH", "open_collector")]),
        "oscillator_block": ([], [pin("OUT", "output")]),
        "pll": ([pin("REF", "input"), pin("VCO_IN", "input")], [pin("OUT", "output"), pin("CONTROL", "output")]),
        "zero_cross": ([pin("AC_IN", "input")], [pin("OUT", "output")]),
        "rms_detector": ([pin("IN", "input")], [pin("OUT", "output")]),
        "supervisor": ([pin("SENSE", "input")], [pin("RESET", "output")]),
        "watchdog": ([pin("WDI", "input")], [pin("RESET", "output")]),
        "pga": ([pin("IN", "input"), pin("GAIN", "input")], [pin("OUT", "output")]),
        "audio_amp": ([pin("IN", "input")], [pin("OUT", "output")]),
        "rf_amp": ([pin("RF_IN", "input"), pin("BIAS", "power_in")], [pin("RF_OUT", "output")]),
        "mixer": ([pin("RF", "input"), pin("LO", "input")], [pin("IF", "output")]),
        "modulator": ([pin("SIGNAL", "input"), pin("CARRIER", "input")], [pin("OUT", "output")]),
        "demodulator": ([pin("MODULATED_IN", "input")], [pin("OUT", "output")]),
        "envelope_detector": ([pin("IN", "input")], [pin("OUT", "output")]),
        "sample_hold": ([pin("IN", "input"), pin("SAMPLE", "input")], [pin("OUT", "output")]),
        "vco": ([pin("VCTRL", "input")], [pin("OUT", "output")]),
        "constant_current": ([pin("IN", "power_in"), pin("SENSE", "input")], [pin("IOUT", "power_out")]),
        "current_mirror": ([pin("IREF", "input")], [pin("IOUT", "output")]),
        "shunt_reg": ([pin("REF", "input"), pin("A", "ground")], [pin("K", "output")]),
        "precision_rect": ([pin("IN", "input")], [pin("OUT", "output")]),
        "charge_pump": ([pin("VIN", "power_in"), pin("CAP+", "passive"), pin("CAP-", "passive")], [pin("VOUT", "power_out")]),
        "agc": ([pin("IN", "input"), pin("CONTROL", "input")], [pin("OUT", "output")]),
        "active_lpf": ([pin("IN", "input")], [pin("OUT", "output")]),
        "active_hpf": ([pin("IN", "input")], [pin("OUT", "output")]),
        "active_bpf": ([pin("IN", "input")], [pin("OUT", "output")]),
    }
    if drawing not in signatures:
        raise ValueError(f"Firma funcional pendiente: {drawing}")
    left, right = signatures[drawing]
    return left, right, [pin("VCC", "power_in")], [pin("GND", "ground")]


def power_signature(drawing: str) -> tuple[list, list, list, list]:
    three_phase = {"inverter3", "ipm", "igbt_module", "pim", "rectifier3"}
    if drawing in three_phase:
        left = [pin("DC+", "power_in"), pin("DC-", "power_in"), pin("CONTROL", "input")]
        right = [pin("U_R", "power_out"), pin("V_S", "power_out"), pin("W_T", "power_out"), pin("FAULT", "output")]
        return left, right, [], [pin("PE", "protective_earth")]
    two_wire = {"crankcase_heater", "tray_heater", "ntc_room", "ntc_indoor_coil", "ntc_outdoor_coil", "ntc_discharge", "ntc_suction", "ntc_ambient", "fan_capacitor", "drain_float", "defrost_thermostat", "four_way_coil", "compressor_heater", "compressor_thermal", "input_reactor", "dc_reactor", "precharge_resistor", "ptc_fuse"}
    if drawing in two_wire:
        return [pin("1", "passive")], [pin("2", "passive")], [], []
    signatures = {
        "hbridge": ([pin("VIN", "power_in"), pin("CTRL_A", "input"), pin("CTRL_B", "input")], [pin("OUT1", "power_out"), pin("OUT2", "power_out")]),
        "halfbridge": ([pin("DC+", "power_in"), pin("DC-", "power_in"), pin("HIN", "input"), pin("LIN", "input")], [pin("SW", "power_out")]),
        "pfc_stage": ([pin("RECTIFIED", "power_in"), pin("GATE", "input"), pin("SENSE", "output")], [pin("DC_BUS", "power_out")]),
        "flyback_stage": ([pin("PRIMARY", "power_in"), pin("CONTROL", "input")], [pin("SECONDARY", "power_out"), pin("FEEDBACK", "output")]),
        "noniso_supply": ([pin("MAINS_BUS", "power_in"), pin("CONTROL", "input")], [pin("OUTPUT", "power_out")]),
        "gate_driver": ([pin("HIN", "input"), pin("LIN", "input"), pin("BOOT", "power_in")], [pin("HO", "output"), pin("LO", "output"), pin("COM", "ground")]),
        "bldc_driver": ([pin("PWM", "input"), pin("HALL_BEMF", "input")], [pin("U", "power_out"), pin("V", "power_out"), pin("W", "power_out")]),
        "stepper_driver": ([pin("STEP", "input"), pin("DIR", "input")], [pin("A+", "power_out"), pin("A-", "power_out"), pin("B+", "power_out"), pin("B-", "power_out")]),
        "eev_driver": ([pin("CONTROL", "input")], [pin("A+", "power_out"), pin("A-", "power_out"), pin("B+", "power_out"), pin("B-", "power_out")]),
        "compressor_ctrl": ([pin("SENSORS", "input"), pin("CURRENT", "input"), pin("COMM", "bidirectional")], [pin("PWM_GATE", "output"), pin("FAULT", "output")]),
        "fan_ctrl": ([pin("PWM", "input"), pin("HALL", "input")], [pin("PHASES", "power_out"), pin("FG", "output")]),
        "hvac_comm": ([pin("INDOOR_BUS", "bidirectional")], [pin("OUTDOOR_BUS", "bidirectional")]),
        "mains_filter": ([pin("L_IN", "power_in"), pin("N_IN", "power_in")], [pin("L_OUT", "power_out"), pin("N_OUT", "power_out")]),
        "dc_bus": ([pin("RECTIFIER+", "power_in"), pin("RECTIFIER-", "power_in")], [pin("P", "power_out"), pin("N", "power_out"), pin("MID", "power_out")]),
        "brake_chopper": ([pin("P", "power_in"), pin("N", "power_in"), pin("GATE", "input")], [pin("BRAKE_R", "power_out")]),
        "phase_current": ([pin("PHASES", "power_in")], [pin("SENSE[]", "output")]),
        "mains_zero": ([pin("L", "power_in"), pin("N", "power_in")], [pin("LOGIC_OUT", "output")]),
        "ntc_chain": ([pin("NTC[]", "input")], [pin("ADC[]", "output"), pin("REF_GND", "ground")]),
        "pressure_switch_pair": ([pin("HP_COM", "passive"), pin("LP_COM", "passive")], [pin("HP_OUT", "output"), pin("LP_OUT", "output")]),
        "refrig_pressure": ([pin("PRESSURE", "input"), pin("VCC", "power_in")], [pin("SIGNAL", "output"), pin("GND", "ground")]),
        "defrost_block": ([pin("SENSORS", "input")], [pin("HEATER", "power_out"), pin("FAN", "power_out")]),
        "soft_start": ([pin("POWER_IN", "power_in"), pin("CONTROL", "input")], [pin("POWER_OUT", "power_out")]),
        "hot_swap": ([pin("IN", "power_in"), pin("SENSE", "input")], [pin("OUT", "power_out"), pin("GATE", "output")]),
        "sync_rect": ([pin("AC_PULSE", "power_in"), pin("GATE", "input")], [pin("DC_OUT", "power_out")]),
        "isolated_gate_driver": ([pin("LOGIC_IN", "input"), pin("VCC1", "power_in")], [pin("GATE", "output"), pin("EMITTER", "output"), pin("VCC2", "power_in")]),
        "forward_stage": ([pin("PRIMARY", "power_in"), pin("RESET", "input")], [pin("SECONDARY", "power_out")]),
        "push_pull": ([pin("GATE_A", "input"), pin("GATE_B", "input"), pin("PRIMARY_CT", "power_in")], [pin("SECONDARY", "power_out")]),
        "halfbridge_supply": ([pin("BUS", "power_in"), pin("CONTROL", "input")], [pin("TRANSFORMER", "power_out")]),
        "fullbridge_supply": ([pin("BUS", "power_in"), pin("CONTROL", "input")], [pin("TRANSFORMER", "power_out")]),
        "active_clamp": ([pin("MAIN_GATE", "input"), pin("CLAMP_GATE", "input"), pin("PRIMARY", "power_in")], [pin("SECONDARY", "power_out")]),
        "solar_inverter": ([pin("PV+", "power_in"), pin("PV-", "power_in")], [pin("AC_L", "power_out"), pin("AC_N", "power_out")]),
        "battery_charger": ([pin("INPUT", "power_in"), pin("SENSE", "input")], [pin("BAT+", "power_out"), pin("BAT-", "power_out")]),
        "bms": ([pin("CELLS[]", "input"), pin("SHUNT", "input")], [pin("PACK+", "power_out"), pin("PACK-", "power_out"), pin("FET_DRIVE", "output")]),
        "cell_balancer": ([pin("CELL_TAPS[]", "input")], [pin("BALANCE[]", "power_out")]),
        "regen_brake": ([pin("MOTOR", "power_in"), pin("CONTROL", "input")], [pin("DC_BUS", "power_out"), pin("BRAKE", "power_out")]),
        "compressor_contactor": ([pin("A1", "input"), pin("A2", "input"), pin("L1", "power_in"), pin("L2", "power_in"), pin("L3", "power_in")], [pin("T1", "power_out"), pin("T2", "power_out"), pin("T3", "power_out")]),
        "fan_relay": ([pin("A1", "input"), pin("A2", "input"), pin("COM", "passive")], [pin("NO", "passive"), pin("NC", "passive")]),
        "high_pressure_sensor": ([pin("PRESSURE", "input"), pin("VCC", "power_in")], [pin("SIGNAL", "output"), pin("GND", "ground")]),
        "low_pressure_sensor": ([pin("PRESSURE", "input"), pin("VCC", "power_in")], [pin("SIGNAL", "output"), pin("GND", "ground")]),
        "powerline_hvac": ([pin("MAINS_IN", "power_in"), pin("TX", "input")], [pin("MAINS_OUT", "power_out"), pin("RX", "output")]),
        "precharge_relay": ([pin("A1", "input"), pin("A2", "input"), pin("COM", "power_in")], [pin("NO", "power_out")]),
        "module": ([pin("ANODE_IN", "power_in"), pin("GATE", "input")], [pin("CATHODE_OUT", "power_out")]),
    }
    if drawing not in signatures:
        raise ValueError(f"Firma de potencia pendiente: {drawing}")
    left, right = signatures[drawing]
    return left, right, [], []


def build_seed(record: dict) -> dict:
    category = record["categoria"]
    geometry_template, batch = TARGETS[category]
    drawing = str(record.get("tipo_dibujo") or "")
    if category == "Electrónica digital":
        left, right, north, south = digital_signature(drawing)
    elif category == "Circuitos integrados funcionales":
        left, right, north, south = functional_signature(drawing)
    else:
        left, right, north, south = power_signature(drawing)
    width, height, ports = make_ports(left, right, north, south)
    return {
        "id": record["id"],
        "catalog_id": record["id"],
        "name": record.get("nombre") or record["id"],
        "kind": drawing,
        "geometry_template": geometry_template,
        "designator": record.get("designador") or "U",
        "standard_profile": "IEC_EXPERIMENTAL",
        "grid_pitch_mil": 50,
        "width": width,
        "height": height,
        "ports": ports,
        "review_status": "draft",
        "normalization_batch": batch,
        "review_scope": "Bloque funcional, anclajes y nombres de terminal revisados para el motor experimental; los grupos no representan el pinout físico de un modelo concreto ni una certificación normativa.",
    }


def main() -> int:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))["symbols"]
    payload = json.loads(SEEDS.read_text(encoding="utf-8"))
    existing = {item["id"] for item in payload["symbols"]}
    additions = [build_seed(record) for record in catalog if record.get("categoria") in TARGETS and record["id"] not in existing]
    payload["symbols"].extend(additions)
    payload["symbols"].sort(key=lambda item: (item["id"].startswith("ST-"), item["id"]))
    SEEDS.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    expected = sum(1 for record in catalog if record.get("categoria") in TARGETS and record["id"] not in existing)
    if len(additions) != expected:
        raise SystemExit("La tanda no quedó completa")
    print(json.dumps({"added": len(additions), "seed_count": len(payload["symbols"]), "categories": list(TARGETS)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
