#!/usr/bin/env python3
"""Build the public Frigorista catalog and deterministic P/T curves.

CoolProp is a build-time dependency only. The browser receives compact,
versioned curves and never needs to load or execute a thermodynamic library.
"""

from __future__ import annotations

import argparse
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
        "dataset_version": "2026.08.1",
        "generated_at": generated_at,
        "title": "Catálogo del Asistente Frigorista",
        "counts": {
            "catalog": len(catalog),
            "pt_available": available,
            "pt_pending": len(rows) - available,
            "blocked": len(BLOCKED_REFRIGERANTS),
            "applications": len(applications),
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
    return public_catalog["counts"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=Path, required=True)
    parser.add_argument("--applications", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    counts = build(args.seed, args.applications, args.output)
    print(json.dumps(counts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
