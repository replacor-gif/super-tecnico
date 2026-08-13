#!/usr/bin/env python3
"""Build the public Frigorista catalog and deterministic P/T curves.

CoolProp is a build-time dependency only. The browser receives compact,
versioned curves and never needs to load or execute a thermodynamic library.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


COOLPROP_KEYS = {
    "R152a": "R152A",
    "R227ea": "R227EA",
    "R236fa": "R236FA",
    "R290": "n-Propane",
    "R600": "n-Butane",
    "R600a": "IsoButane",
    "R1270": "Propylene",
    "R170": "Ethane",
    "R1150": "Ethylene",
}

APPLICATION_FIXES = {
    "industrial_chillers": ["industrial", "chillers"],
}

BLOCKED_REFRIGERANTS = [
    {
        "id": "ref-r717",
        "designation": "R717",
        "family": "natural",
        "mixture_type": "pure",
        "catalog_status": "excluded_scope",
        "selectable": False,
        "pt_available": False,
        "excluded_reason": "Sistemas de amoniaco fuera del alcance de esta primera versión.",
    },
    {
        "id": "ref-r744",
        "designation": "R744",
        "family": "natural",
        "mixture_type": "pure",
        "catalog_status": "excluded_scope",
        "selectable": False,
        "pt_available": False,
        "excluded_reason": "Sistemas de CO₂ fuera del alcance de esta primera versión.",
    },
]

DATASET_VERSION = "2026.08.2"
MOLLIER_PRESSURE_ROWS = 18
MOLLIER_VAPOR_OFFSETS_K = (0.5, 2.0, 5.0, 10.0, 20.0, 40.0, 80.0, 120.0)
MOLLIER_LIQUID_OFFSETS_K = (0.5, 2.0, 5.0, 10.0, 20.0, 40.0, 60.0)


def slug(value: str) -> str:
    return (
        value.lower()
        .replace("(", "-")
        .replace(")", "")
        .replace("/", "-")
        .replace(" ", "-")
    )


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def application_codes(raw: str) -> list[str]:
    result: list[str] = []
    for code in filter(None, (item.strip() for item in raw.split("|"))):
        result.extend(APPLICATION_FIXES.get(code, [code]))
    return list(dict.fromkeys(result))


def curve_for_key(cp: Any, key: str) -> dict[str, Any] | None:
    bubble: list[list[float | int]] = []
    dew: list[list[float | int]] = []
    start_c = -100.0
    end_c = 80.0

    try:
        critical_c = float(cp.PropsSI("Tcrit", key)) - 273.15
        if math.isfinite(critical_c):
            end_c = min(end_c, math.floor((critical_c - 1.0) * 2.0) / 2.0)
    except Exception:
        critical_c = None

    steps = int(round((end_c - start_c) * 2)) + 1
    for index in range(max(steps, 0)):
        temperature_c = start_c + index * 0.5
        temperature_k = temperature_c + 273.15
        try:
            bubble_pa = float(cp.PropsSI("P", "T", temperature_k, "Q", 0, key))
            dew_pa = float(cp.PropsSI("P", "T", temperature_k, "Q", 1, key))
        except Exception:
            continue
        if not all(math.isfinite(value) and value > 0 for value in (bubble_pa, dew_pa)):
            continue
        bubble_pressure = round(bubble_pa, 3)
        dew_pressure = round(dew_pa, 3)
        if not bubble or bubble_pressure > bubble[-1][0]:
            bubble.append([bubble_pressure, temperature_c])
        if not dew or dew_pressure > dew[-1][0]:
            dew.append([dew_pressure, temperature_c])

    if len(bubble) < 20 or len(dew) < 20:
        return None

    return {
        "backend_key": key,
        "bubble": bubble,
        "dew": dew,
        "pressure_range_pa_abs": {
            "minimum": max(bubble[0][0], dew[0][0]),
            "maximum": min(bubble[-1][0], dew[-1][0]),
        },
        "temperature_range_c": {
            "minimum": max(bubble[0][1], dew[0][1]),
            "maximum": min(bubble[-1][1], dew[-1][1]),
        },
        "critical_temperature_c": round(critical_c, 3) if critical_c is not None else None,
    }


def logarithmic_pressures(minimum: float, maximum: float, count: int) -> list[float]:
    """Return stable logarithmic pressure nodes including both limits."""
    if minimum <= 0 or maximum <= minimum or count < 2:
        return []
    start = math.log(minimum)
    span = math.log(maximum) - start
    return [math.exp(start + span * index / (count - 1)) for index in range(count)]


def thermodynamic_state(cp: Any, key: str, pressure_pa: float, temperature_k: float) -> list[float] | None:
    """Return compact [enthalpy kJ/kg, entropy kJ/kg/K] or no point."""
    try:
        enthalpy, entropy = cp.PropsSI(
            ["Hmass", "Smass"],
            "P", pressure_pa,
            "T", temperature_k,
            key,
        )
    except Exception:
        return None
    if not all(math.isfinite(float(value)) for value in (enthalpy, entropy)):
        return None
    return [round(float(enthalpy) / 1000.0, 4), round(float(entropy) / 1000.0, 6)]


def mollier_for_key(cp: Any, key: str, curve: dict[str, Any]) -> dict[str, Any] | None:
    """Build a compact P-h lookup using offsets from bubble/dew saturation.

    The browser interpolates only inside a declared liquid or vapour region.
    This avoids interpolating straight across the saturation discontinuity.
    """
    pressure_range = curve["pressure_range_pa_abs"]
    minimum = max(float(pressure_range["minimum"]), 10_000.0)
    maximum = float(pressure_range["maximum"])
    rows: list[dict[str, Any]] = []

    for pressure_pa in logarithmic_pressures(minimum, maximum, MOLLIER_PRESSURE_ROWS):
        try:
            bubble_k = float(cp.PropsSI("T", "P", pressure_pa, "Q", 0, key))
            dew_k = float(cp.PropsSI("T", "P", pressure_pa, "Q", 1, key))
            bubble_hs = [float(value) for value in cp.PropsSI(
                ["Hmass", "Smass"], "P", pressure_pa, "Q", 0, key
            )]
            dew_hs = [float(value) for value in cp.PropsSI(
                ["Hmass", "Smass"], "P", pressure_pa, "Q", 1, key
            )]
        except Exception:
            continue
        if not all(math.isfinite(value) for value in (bubble_k, dew_k, *bubble_hs, *dew_hs)):
            continue

        vapor_states = []
        for offset_k in MOLLIER_VAPOR_OFFSETS_K:
            state = thermodynamic_state(cp, key, pressure_pa, dew_k + offset_k)
            if state:
                vapor_states.append([offset_k, *state])

        liquid_states = []
        for offset_k in MOLLIER_LIQUID_OFFSETS_K:
            state = thermodynamic_state(cp, key, pressure_pa, bubble_k - offset_k)
            if state:
                liquid_states.append([offset_k, *state])

        if len(vapor_states) < 3 or len(liquid_states) < 3:
            continue
        rows.append({
            "p": round(pressure_pa, 2),
            "bubble": [
                round(bubble_k - 273.15, 4),
                round(bubble_hs[0] / 1000.0, 4),
                round(bubble_hs[1] / 1000.0, 6),
            ],
            "dew": [
                round(dew_k - 273.15, 4),
                round(dew_hs[0] / 1000.0, 4),
                round(dew_hs[1] / 1000.0, 6),
            ],
            "vapor": vapor_states,
            "liquid": liquid_states,
        })

    if len(rows) < 12:
        return None
    return {
        "backend_key": key,
        "pressure_rows": rows,
        "pressure_range_pa_abs": {"minimum": rows[0]["p"], "maximum": rows[-1]["p"]},
        "vapor_offsets_k": list(MOLLIER_VAPOR_OFFSETS_K),
        "liquid_offsets_k": list(MOLLIER_LIQUID_OFFSETS_K),
    }


def mollier_worker(payload: tuple[str, dict[str, Any]]) -> tuple[str, dict[str, Any] | None]:
    """Calculate one refrigerant in an isolated process."""
    designation, curve = payload
    import CoolProp.CoolProp as cp
    return designation, mollier_for_key(cp, curve["backend_key"], curve)


def build(seed_path: Path, applications_path: Path, output_dir: Path) -> dict[str, Any]:
    try:
        import CoolProp.CoolProp as cp
    except ImportError as exc:
        raise SystemExit("CoolProp is required: python -m pip install CoolProp==8.0.0") from exc

    rows = read_rows(seed_path)
    applications = [
        {"code": row["code"], "name": row["name"]}
        for row in read_rows(applications_path)
    ]
    fluids = {name.lower(): name for name in cp.get_global_param_string("fluids_list").split(",")}
    mixtures = {
        name.lower(): name
        for name in cp.get_global_param_string("predefined_mixtures").split(",")
    }

    catalog: list[dict[str, Any]] = []
    curves: dict[str, Any] = {}
    mollier: dict[str, Any] = {}
    for row in rows:
        designation = row["designation"].strip()
        key = (
            COOLPROP_KEYS.get(designation)
            or fluids.get(designation.lower())
            or mixtures.get(f"{designation}.mix".lower())
        )
        curve = curve_for_key(cp, key) if key else None
        if curve:
            curves[designation] = curve
            mollier_data = mollier_for_key(cp, key, curve)
            if mollier_data:
                mollier[designation] = mollier_data

        catalog.append(
            {
                "id": f"ref-{slug(designation)}",
                "designation": designation,
                "family": row["family"].strip(),
                "mixture_type": row["mixture_type"].strip(),
                "safety_class": row["safety_class_seed"].strip() or None,
                "safety_status": "seed_pending_source_review",
                "catalog_status": row["catalog_status"].strip(),
                "applications": application_codes(row["application_tags"]),
                "notes": row["notes"].strip(),
                "selectable": row["selectable"].strip() == "1" and curve is not None,
                "pt_available": curve is not None,
                "thermodynamic_status": "computed_coolprop_8_0_0" if curve else "unsupported_pending_source",
                "backend_key": key if curve else None,
            }
        )

    catalog.extend(BLOCKED_REFRIGERANTS)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    coolprop_version = cp.get_global_param_string("version")
    git_revision = cp.get_global_param_string("gitrevision")
    available = sum(item["pt_available"] for item in catalog)

    public_catalog = {
        "schema_version": "1.0.0",
        "dataset_version": DATASET_VERSION,
        "generated_at": generated_at,
        "title": "Catálogo del Asistente Frigorista",
        "counts": {
            "catalog": len(catalog),
            "pt_available": available,
            "pt_pending": len(rows) - available,
            "blocked": len(BLOCKED_REFRIGERANTS),
            "applications": len(applications),
            "mollier_available": len(mollier),
        },
        "internal_units": {"pressure": "Pa_absolute", "temperature": "degC"},
        "defaults": {"atmospheric_pressure_pa": 101325, "pressure_reference": "gauge"},
        "sources": [
            {
                "id": "coolprop-8.0.0",
                "organization": "CoolProp",
                "title": "CoolProp 8.0.0 thermophysical property engine",
                "url": "https://coolprop.org/",
                "version": coolprop_version,
                "git_revision": git_revision,
                "purpose": "P/T curves generated at build time",
            },
            {
                "id": "ashrae-34-2024-review-pending",
                "organization": "ASHRAE",
                "title": "ANSI/ASHRAE Standard 34-2024",
                "url": "https://www.ashrae.org/technical-resources/standards-and-guidelines/titles-purposes-and-scopes",
                "version": "2024 with applicable addenda pending catalog review",
                "purpose": "Designation and safety-class review",
            },
        ],
        "applications": applications,
        "refrigerants": catalog,
    }
    public_curves = {
        "schema_version": "1.0.0",
        "dataset_version": public_catalog["dataset_version"],
        "engine": {"name": "CoolProp", "version": coolprop_version, "git_revision": git_revision},
        "temperature_step_c": 0.5,
        "pressure_reference": "absolute",
        "curves": curves,
    }
    public_mollier = {
        "schema_version": "1.0.0",
        "dataset_version": public_catalog["dataset_version"],
        "engine": {"name": "CoolProp", "version": coolprop_version, "git_revision": git_revision},
        "diagram": "pressure_enthalpy",
        "internal_units": {
            "pressure": "Pa_absolute",
            "temperature": "degC",
            "enthalpy": "kJ/kg",
            "entropy": "kJ/kg/K",
        },
        "reference_note": "Enthalpy and entropy are relative properties; compare differences within the same refrigerant and dataset.",
        "refrigerants": mollier,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "catalog.json").write_text(
        json.dumps(public_catalog, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "pt-curves.json").write_text(
        json.dumps(public_curves, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "mollier-data.json").write_text(
        json.dumps(public_mollier, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return public_catalog["counts"]


def build_mollier_only(output_dir: Path) -> dict[str, int]:
    """Add Mollier data while preserving the already reviewed P/T curves."""
    try:
        import CoolProp.CoolProp as cp
    except ImportError as exc:
        raise SystemExit("CoolProp is required: python -m pip install CoolProp==8.0.0") from exc

    catalog_path = output_dir / "catalog.json"
    curves_path = output_dir / "pt-curves.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    curves = json.loads(curves_path.read_text(encoding="utf-8"))
    mollier: dict[str, Any] = {}
    payloads = list(curves.get("curves", {}).items())
    with concurrent.futures.ProcessPoolExecutor(max_workers=min(4, len(payloads))) as executor:
        for designation, diagram in executor.map(mollier_worker, payloads, chunksize=1):
            if diagram:
                mollier[designation] = diagram
            print(f"Mollier {designation}: {'OK' if diagram else 'unsupported'}", flush=True)
    expected = set(curves.get("curves", {}))
    if set(mollier) != expected:
        missing = sorted(expected - set(mollier))
        raise SystemExit(f"Mollier coverage incomplete: {', '.join(missing)}")

    coolprop_version = cp.get_global_param_string("version")
    git_revision = cp.get_global_param_string("gitrevision")
    catalog["dataset_version"] = DATASET_VERSION
    catalog.setdefault("counts", {})["mollier_available"] = len(mollier)
    curves["dataset_version"] = DATASET_VERSION
    public_mollier = {
        "schema_version": "1.0.0",
        "dataset_version": DATASET_VERSION,
        "engine": {"name": "CoolProp", "version": coolprop_version, "git_revision": git_revision},
        "diagram": "pressure_enthalpy",
        "internal_units": {
            "pressure": "Pa_absolute",
            "temperature": "degC",
            "enthalpy": "kJ/kg",
            "entropy": "kJ/kg/K",
        },
        "reference_note": "Enthalpy and entropy are relative properties; compare differences within the same refrigerant and dataset version.",
        "refrigerants": mollier,
    }
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    curves_path.write_text(json.dumps(curves, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    (output_dir / "mollier-data.json").write_text(
        json.dumps(public_mollier, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return {"pt_available": len(expected), "mollier_available": len(mollier)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=Path)
    parser.add_argument("--applications", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mollier-only", action="store_true", help="Reuse the existing catalog and P/T curves")
    args = parser.parse_args()
    if args.mollier_only:
        counts = build_mollier_only(args.output)
    else:
        if not args.seed or not args.applications:
            parser.error("--seed and --applications are required unless --mollier-only is used")
        counts = build(args.seed, args.applications, args.output)
    print(json.dumps(counts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
