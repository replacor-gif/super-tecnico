from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import CoolProp.CoolProp as CP


ROOT = Path(__file__).resolve().parents[1]


def interpolate(points: list[list[float]], pressure_pa: float) -> float:
    low = 0
    high = len(points) - 1
    while low <= high:
        middle = (low + high) // 2
        if points[middle][0] < pressure_pa:
            low = middle + 1
        elif points[middle][0] > pressure_pa:
            high = middle - 1
        else:
            return points[middle][1]
    lower = points[low - 1]
    upper = points[low]
    fraction = (pressure_pa - lower[0]) / (upper[0] - lower[0])
    return lower[1] + fraction * (upper[1] - lower[1])


catalog = json.loads((ROOT / "data/frigorista/catalog.json").read_text(encoding="utf-8"))
curves = json.loads((ROOT / "data/frigorista/pt-curves.json").read_text(encoding="utf-8"))
mollier = json.loads((ROOT / "data/frigorista/mollier-data.json").read_text(encoding="utf-8"))

assert catalog["dataset_version"] == curves["dataset_version"] == mollier["dataset_version"]
assert catalog["counts"]["pt_available"] == 56
assert catalog["counts"]["mollier_available"] == 56
assert len(curves["curves"]) == 56
assert len(mollier["refrigerants"]) == 56

for designation, backend_key in {
    "R32": "R32",
    "R407C": "R407C",
    "R449A": "R449A.mix",
    "R290": "n-Propane",
}.items():
    for phase, quality in (("bubble", 0), ("dew", 1)):
        expected_c = 3.25
        pressure_pa = CP.PropsSI("P", "T", expected_c + 273.15, "Q", quality, backend_key)
        actual_c = interpolate(curves["curves"][designation][phase], pressure_pa)
        assert abs(actual_c - expected_c) < 0.03, (designation, phase, actual_c)

    rows = mollier["refrigerants"][designation]["pressure_rows"]
    assert len(rows) >= 12
    row = rows[len(rows) // 2]
    pressure_pa = row["p"]
    for phase, quality in (("bubble", 0), ("dew", 1)):
        expected_h = CP.PropsSI("Hmass", "P", pressure_pa, "Q", quality, backend_key) / 1000
        expected_s = CP.PropsSI("Smass", "P", pressure_pa, "Q", quality, backend_key) / 1000
        assert abs(row[phase][1] - expected_h) < 0.02, (designation, phase, "h")
        assert abs(row[phase][2] - expected_s) < 0.00002, (designation, phase, "s")

connection = sqlite3.connect(":memory:")
connection.executescript((ROOT / "database/frigorista/schema.sql").read_text(encoding="utf-8"))
tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
assert {"refrigerants", "pt_points", "system_sessions", "measurements", "diagnostic_results"} <= tables
connection.close()

print("Frigorista data and schema validation: OK")
