#!/usr/bin/env python3
"""Run structural and professional-coverage gates for the ElectroIA symbol engine."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "data" / "electroia" / "symbol-library.json"
REPORT = ROOT / "data" / "electroia" / "engine-audit-report.json"
EXAMPLES = ROOT / "data" / "electroia" / "examples"
VALID_SIDES = {"west", "east", "north", "south"}
VALID_ELECTRICAL_TYPES = {
    "passive", "input", "output", "bidirectional", "power_in", "power_out",
    "ground", "protective_earth", "functional_earth", "open_collector", "shield",
    "tri_state", "no_connect",
}

PROFESSIONAL_DOMAINS = {
    "automation": [f"SYM-{number:04d}" for number in range(461, 481)],
    "drives_and_motor_control": [f"SYM-{number:04d}" for number in range(481, 493)],
    "building_services_control": [f"SYM-{number:04d}" for number in range(493, 501)],
    "three_phase_power_interface": ["SYM-0501"],
}


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report() -> tuple[dict, list[str]]:
    library = read(LIBRARY)
    symbols = library["symbols"]
    public = [item for item in symbols if item.get("catalog_id")]
    internal = [item for item in symbols if not item.get("catalog_id")]
    failures: list[str] = []
    warnings: list[dict] = []
    ids = [item["id"] for item in symbols]
    if len(ids) != len(set(ids)):
        failures.append("duplicate_symbol_ids")
    if any(item.get("review_status") != "engine_reviewed" for item in public):
        failures.append("public_symbols_not_reviewed")
    if any(not item.get("ports") for item in symbols):
        failures.append("symbols_without_ports")

    off_grid: list[str] = []
    duplicate_coordinates: list[str] = []
    invalid_sides: list[str] = []
    invalid_types: list[str] = []
    ports_total = 0
    for symbol in symbols:
        seen: set[tuple[object, object]] = set()
        for name, terminal in symbol.get("ports", {}).items():
            ports_total += 1
            coordinate = (terminal.get("x"), terminal.get("y"))
            if any(not isinstance(value, int) for value in coordinate):
                off_grid.append(f"{symbol['id']}.{name}")
            if coordinate in seen:
                duplicate_coordinates.append(f"{symbol['id']}.{name}")
            seen.add(coordinate)
            if terminal.get("side") not in VALID_SIDES:
                invalid_sides.append(f"{symbol['id']}.{name}")
            if terminal.get("electrical_type") not in VALID_ELECTRICAL_TYPES:
                invalid_types.append(f"{symbol['id']}.{name}")
    for code, items in (
        ("off_grid_ports", off_grid),
        ("duplicate_port_coordinates", duplicate_coordinates),
        ("invalid_port_sides", invalid_sides),
        ("invalid_electrical_types", invalid_types),
    ):
        if items:
            failures.append(code)

    public_ids = {item["id"] for item in public}
    domain_coverage = {}
    for domain, required in PROFESSIONAL_DOMAINS.items():
        missing = sorted(set(required) - public_ids)
        domain_coverage[domain] = {
            "required": len(required),
            "available": len(required) - len(missing),
            "missing": missing,
        }
        if missing:
            failures.append(f"professional_domain_incomplete:{domain}")

    terminal_models = Counter(item.get("terminal_model", "explicit") for item in public)
    exact_model = [item["id"] for item in public if item.get("requires_exact_model")]
    example_files = sorted(path.name for path in EXAMPLES.glob("*.json"))
    symbols_by_id = {item["id"]: item for item in symbols}
    example_components = 0
    example_nets = 0
    example_failures: list[str] = []
    for filename in example_files:
        document = read(EXAMPLES / filename)
        prefix = f"{filename}:"
        for key in ("schema_version", "document_kind", "standard_profile", "title", "document_id", "revision"):
            if not document.get(key):
                example_failures.append(prefix + "missing_" + key)
        components = document.get("components") or []
        nets = document.get("nets") or []
        example_components += len(components)
        example_nets += len(nets)
        refs = [str(item.get("ref") or "") for item in components]
        if any(not ref for ref in refs) or len(refs) != len(set(refs)):
            example_failures.append(prefix + "invalid_component_refs")
        components_by_ref = {str(item.get("ref") or ""): item for item in components}
        for component in components:
            symbol = symbols_by_id.get(component.get("symbol_id"))
            if not symbol:
                example_failures.append(prefix + "unknown_symbol:" + str(component.get("symbol_id")))
                continue
            if symbol.get("requires_exact_model") and not any(component.get(key) for key in ("model", "part_number", "exact_model")):
                example_failures.append(prefix + "exact_model_missing:" + str(component.get("ref")))
        net_ids = [str(item.get("id") or "") for item in nets]
        if any(not net_id for net_id in net_ids) or len(net_ids) != len(set(net_ids)):
            example_failures.append(prefix + "invalid_net_ids")
        used_terminals: set[str] = set()
        for net in nets:
            connections = list(net.get("connections") or [])
            if len(connections) < 2 or len(connections) != len(set(connections)):
                example_failures.append(prefix + "invalid_net_connections:" + str(net.get("id")))
            for raw in connections:
                if "." not in str(raw):
                    example_failures.append(prefix + "invalid_connection:" + str(raw))
                    continue
                ref, port = str(raw).rsplit(".", 1)
                component = components_by_ref.get(ref)
                symbol = symbols_by_id.get(component.get("symbol_id")) if component else None
                if not component or not symbol or port not in (symbol.get("ports") or {}):
                    example_failures.append(prefix + "unknown_terminal:" + str(raw))
                    continue
                if (symbol["ports"][port].get("electrical_type") or "passive") == "no_connect":
                    example_failures.append(prefix + "no_connect_used:" + str(raw))
                if raw in used_terminals:
                    example_failures.append(prefix + "terminal_on_multiple_nets:" + str(raw))
                used_terminals.add(str(raw))
    if example_failures:
        failures.append("invalid_professional_examples")
    warnings.extend([
        {
            "id": "FUNCTIONAL_GROUPS_REQUIRE_MODEL",
            "severity": "controlled",
            "count": terminal_models["functional_group"],
            "message": "Los bloques funcionales no se convierten en pinout físico sin fabricante, modelo, variante y manual.",
        },
        {
            "id": "IEC_PROFILE_EXPERIMENTAL",
            "severity": "open",
            "message": "El motor mantiene un único perfil IEC experimental; faltan perfiles nacionales y reglas documentales específicas por oficio.",
        },
        {
            "id": "SINGLE_CANVAS_ONLY",
            "severity": "open",
            "message": "El núcleo genera un lienzo único. La paginación con referencias cruzadas queda para documentos realmente grandes.",
        },
    ])

    report = {
        "schema_version": "1.0",
        "updated_at": "2026-08-23",
        "engine_version_expected": "1.14.0-alpha.1",
        "status": "pass" if not failures else "fail",
        "release_class": "hardened_beta_engine",
        "summary": {
            "public_symbols": len(public),
            "internal_symbols": len(internal),
            "reviewed_public_symbols": sum(item.get("review_status") == "engine_reviewed" for item in public),
            "ports": ports_total,
            "terminal_models": dict(sorted(terminal_models.items())),
            "exact_model_required": len(exact_model),
            "professional_symbols": sum(item["available"] for item in domain_coverage.values()),
            "example_documents": len(example_files),
            "example_components": example_components,
            "example_nets": example_nets,
            "fatal_failures": len(failures),
        },
        "structural_gates": {
            "unique_symbol_ids": len(ids) == len(set(ids)),
            "all_public_symbols_reviewed": all(item.get("review_status") == "engine_reviewed" for item in public),
            "all_symbols_have_ports": all(bool(item.get("ports")) for item in symbols),
            "all_ports_on_integer_grid": not off_grid,
            "unique_port_coordinates_per_symbol": not duplicate_coordinates,
            "valid_port_sides": not invalid_sides,
            "valid_electrical_types": not invalid_types,
            "internal_automation_duplicates_removed": not any(item["id"].startswith("ST-AUTO-") for item in internal),
            "professional_examples_are_structurally_valid": not example_failures,
        },
        "professional_domain_coverage": domain_coverage,
        "known_limitations": warnings,
        "next_symbol_packs": [
            {
                "priority": 1,
                "domain": "ICT, seguridad y comunicaciones de edificios",
                "symbols": ["rack y patch panel", "switch PoE", "punto de acceso", "CCTV/NVR", "control de accesos", "interfonía", "fibra y repartidores"],
                "reason": "Necesarios para esquemas ICT y sistemas auxiliares completos, no solo control HVAC.",
            },
            {
                "priority": 2,
                "domain": "Energía distribuida y movilidad eléctrica",
                "symbols": ["cargador EV", "batería BESS", "BMS de batería", "contador bidireccional", "protección DC", "backup box", "grupo electrógeno"],
                "reason": "Completar unifilares actuales de autoconsumo, respaldo y recarga.",
            },
            {
                "priority": 3,
                "domain": "Hidráulica, neumática y P&ID",
                "symbols": ["válvulas de proceso", "actuadores", "filtros", "reguladores", "cilindros", "instrumentación ISA", "líneas de proceso"],
                "reason": "ElectroIA puede reutilizar el motor, pero necesita otro perfil gráfico y reglas de conectividad.",
            },
            {
                "priority": 4,
                "domain": "Documentación de cuadros",
                "symbols": ["borneros multinivel", "puentes de borna", "canaletas", "carril DIN", "envolvente", "ventilación de armario", "placas y reservas"],
                "reason": "Permiten pasar del esquema lógico al plano de fabricación y cableado.",
            },
        ],
        "failure_details": failures,
        "example_failure_details": example_failures,
        "samples": {
            "exact_model_required_ids": exact_model[:25],
            "example_files": example_files,
        },
    }
    return report, failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report, failures = build_report()
    content = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not REPORT.exists() or REPORT.read_text(encoding="utf-8") != content:
            raise SystemExit("data/electroia/engine-audit-report.json está desactualizado")
    else:
        REPORT.write_text(content, encoding="utf-8", newline="\n")
    if failures:
        raise SystemExit("Auditoría ElectroIA fallida: " + ", ".join(failures))
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
