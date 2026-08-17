#!/usr/bin/env python3
"""Build compact thermodynamic states for the browser piping engine."""

from __future__ import annotations

import argparse
import json
import math
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "frigorista" / "catalog.json"
OUTPUT_PATH = ROOT / "data" / "refrigerant-piping" / "property-grid.json"

SUPPORTED = [
    "R22", "R32", "R134a", "R290", "R404A", "R407A", "R407C", "R407F",
    "R410A", "R417A", "R422D", "R448A", "R449A", "R452A", "R452B",
    "R454A", "R454B", "R454C", "R455A", "R507A", "R513A", "R1234yf",
    "R1234ze(E)", "R600a",
]
EVAPORATING_C = [-40, -30, -20, -10, 0, 5, 10, 15]
CONDENSING_C = [25, 30, 35, 40, 45, 50, 55, 60]
SUPERHEAT_K = 8.0
SUBCOOLING_K = 5.0


def rounded(value: float, digits: int = 5) -> float:
    return round(float(value), digits)


def saturation_pressure(CP, state, temperature_c: float, quality: int) -> float:
    state.update(CP.QT_INPUTS, quality, temperature_c + 273.15)
    return float(state.p())


def evaporating_state(CP, state, temperature_c: float) -> dict | None:
    try:
        pressure = saturation_pressure(CP, state, temperature_c, 1)
        state.update(CP.PT_INPUTS, pressure, temperature_c + 273.15 + SUPERHEAT_K)
        enthalpy = float(state.hmass())
        density = float(state.rhomass())
        viscosity = float(state.viscosity())
        pressure_plus = saturation_pressure(CP, state, temperature_c + 0.5, 1)
        pressure_minus = saturation_pressure(CP, state, temperature_c - 0.5, 1)
        if not all(math.isfinite(item) for item in (pressure, enthalpy, density, viscosity)):
            return None
        return {
            "te_c": temperature_c,
            "h_suction_kj_kg": rounded(enthalpy / 1000, 3),
            "p_evap_bar_abs": rounded(pressure / 100_000, 4),
            "dpdt_evap_kpa_k": rounded((pressure_plus - pressure_minus) / 1000, 3),
            "suction_density_kg_m3": rounded(density, 4),
            "suction_viscosity_pa_s": rounded(viscosity, 9),
        }
    except (ValueError, OverflowError):
        return None


def condensing_state(CP, state, temperature_c: float) -> dict | None:
    try:
        pressure = saturation_pressure(CP, state, temperature_c, 0)
        state.update(CP.PT_INPUTS, pressure, temperature_c + 273.15 - SUBCOOLING_K)
        enthalpy = float(state.hmass())
        liquid_density = float(state.rhomass())
        liquid_viscosity = float(state.viscosity())
        discharge_reference_c = temperature_c + 35.0
        state.update(CP.PT_INPUTS, pressure, discharge_reference_c + 273.15)
        discharge_density = float(state.rhomass())
        discharge_viscosity = float(state.viscosity())
        pressure_plus = saturation_pressure(CP, state, temperature_c + 0.5, 0)
        pressure_minus = saturation_pressure(CP, state, temperature_c - 0.5, 0)
        values = (pressure, enthalpy, liquid_density, liquid_viscosity, discharge_density, discharge_viscosity)
        if not all(math.isfinite(item) for item in values):
            return None
        return {
            "tc_c": temperature_c,
            "h_liquid_kj_kg": rounded(enthalpy / 1000, 3),
            "p_cond_bar_abs": rounded(pressure / 100_000, 4),
            "dpdt_cond_kpa_k": rounded((pressure_plus - pressure_minus) / 1000, 3),
            "liquid_density_kg_m3": rounded(liquid_density, 3),
            "liquid_viscosity_pa_s": rounded(liquid_viscosity, 9),
            "discharge_density_kg_m3": rounded(discharge_density, 4),
            "discharge_viscosity_pa_s": rounded(discharge_viscosity, 9),
            "discharge_reference_temperature_c": rounded(discharge_reference_c, 2),
        }
    except (ValueError, OverflowError):
        return None


def build() -> dict:
    try:
        import CoolProp
        import CoolProp as CP
    except ImportError as exc:
        raise SystemExit(
            "CoolProp is required. Set PYTHONPATH=.codex-deps or install CoolProp==8.0.0"
        ) from exc

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    by_designation = {
        item["designation"]: item
        for item in catalog["refrigerants"]
        if item.get("selectable") and item.get("pt_available") and item.get("backend_key")
    }
    fluids = []
    for designation in SUPPORTED:
        source = by_designation.get(designation)
        if not source:
            continue
        state = CP.AbstractState("HEOS", source["backend_key"])
        evap_states = [item for te in EVAPORATING_C if (item := evaporating_state(CP, state, te))]
        cond_states = [item for tc in CONDENSING_C if (item := condensing_state(CP, state, tc))]
        if not evap_states or not cond_states:
            continue
        fluids.append({
            "designation": designation,
            "backend_key": source["backend_key"],
            "safety_class": source.get("safety_class"),
            "mixture_type": source.get("mixture_type"),
            "catalog_status": source.get("catalog_status"),
            "applications": source.get("applications", []),
            "molar_mass_kg_mol": rounded(state.molar_mass(), 7),
            "evaporating_states": evap_states,
            "condensing_states": cond_states,
        })

    return {
        "schema_version": "1.0.0",
        "dataset_version": date.today().isoformat(),
        "engine": {
            "name": "CoolProp",
            "version": CoolProp.__version__,
            "purpose": "Build-time thermophysical properties; no runtime dependency",
        },
        "cycle_assumptions": {"superheat_k": SUPERHEAT_K, "subcooling_k": SUBCOOLING_K},
        "grid": {
            "evaporating_c": EVAPORATING_C,
            "condensing_c": CONDENSING_C,
            "interpolation": "linear_between_valid_neighbours_or_nearest_valid_state",
        },
        "sources": [
            {"id": "coolprop-8", "title": "CoolProp thermophysical property engine", "url": "https://coolprop.org/", "kind": "calculation_engine"},
            {"id": "super-tecnico-frigorista-catalog", "title": "Catálogo normalizado del Asistente Frigorista", "path": "../frigorista/catalog.json", "kind": "internal_normalized_catalog"},
        ],
        "excluded_regimes": [
            "R717 ammonia systems",
            "R744 transcritical and subcritical CO2 systems",
            "secondary refrigerant and pumped liquid recirculation systems",
        ],
        "fluids": fluids,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    payload = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "fluids": len(payload["fluids"]),
        "states": sum(len(item["evaporating_states"]) + len(item["condensing_states"]) for item in payload["fluids"]),
        "engine": payload["engine"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
