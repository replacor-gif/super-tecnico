#!/usr/bin/env python3
"""Semantic validation for the electrical-panel project foundation.

JSON Schema checks shape. This validator checks relationships between devices,
controller channels, evidence and safety boundaries without selecting products
or claiming regulatory conformity.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "data" / "electroia" / "controller-ecosystems.json"


def _issue(code: str, severity: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "path": path, "message": message}


def _duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    return {value for value in values if value in seen or seen.add(value)}


def validate_project(project: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    ecosystems = {item["id"]: item for item in registry.get("ecosystems", [])}
    signal_types = {item["id"] for item in registry.get("signal_types", [])}

    collections = {
        "loads": project.get("loads", []),
        "field_devices": project.get("field_devices", []),
        "controllers": project.get("control_system", {}).get("controllers", []),
        "io_points": project.get("control_system", {}).get("io_points", []),
    }
    all_ids: list[str] = []
    for name, items in collections.items():
        ids = [str(item.get("id", "")) for item in items if item.get("id")]
        for duplicate in sorted(_duplicates(ids)):
            issues.append(_issue("DUPLICATE_ID", "error", name, f"El identificador {duplicate} está repetido en {name}."))
        all_ids.extend(ids)
    for duplicate in sorted(_duplicates(all_ids)):
        issues.append(_issue("DUPLICATE_GLOBAL_ID", "error", "project", f"El identificador {duplicate} se usa en más de una colección."))

    field_devices = {item.get("id"): item for item in collections["field_devices"]}
    controllers = {item.get("id"): item for item in collections["controllers"]}
    controller_modules: dict[str, dict[str, Any]] = {}

    for index, controller in enumerate(collections["controllers"]):
        path = f"control_system.controllers[{index}]"
        ecosystem_id = controller.get("ecosystem_id")
        ecosystem = ecosystems.get(ecosystem_id)
        if not ecosystem:
            issues.append(_issue("UNKNOWN_CONTROLLER_ECOSYSTEM", "error", f"{path}.ecosystem_id", f"No existe el ecosistema {ecosystem_id}."))
            continue
        safety_role = controller.get("safety_role")
        if safety_role not in ecosystem.get("allowed_safety_roles", []):
            issues.append(_issue("UNSUPPORTED_SAFETY_ROLE", "error", f"{path}.safety_role", f"{ecosystem_id} no admite el papel {safety_role}."))
        if safety_role == "safety_control":
            missing = [key for key in ("manufacturer", "model", "firmware") if not controller.get(key)]
            if missing:
                issues.append(_issue("INCOMPLETE_SAFETY_CONTROLLER", "error", path, "Un controlador de seguridad necesita fabricante, modelo y firmware exactos."))
            if not controller.get("source_evidence_ids"):
                issues.append(_issue("SAFETY_CONTROLLER_WITHOUT_EVIDENCE", "error", path, "Falta evidencia oficial del controlador de seguridad."))
        module_ids = [module.get("id") for module in controller.get("io_modules", []) if module.get("id")]
        for duplicate in sorted(_duplicates(module_ids)):
            issues.append(_issue("DUPLICATE_MODULE_ID", "error", f"{path}.io_modules", f"El módulo {duplicate} está repetido."))
        controller_modules[controller.get("id")] = {module.get("id"): module for module in controller.get("io_modules", [])}

    used_channels: set[tuple[str, str, str]] = set()
    used_addresses: set[tuple[str, str]] = set()
    for index, point in enumerate(collections["io_points"]):
        path = f"control_system.io_points[{index}]"
        electrical_standard = point.get("electrical_standard")
        if electrical_standard not in signal_types:
            issues.append(_issue("UNKNOWN_SIGNAL_TYPE", "error", f"{path}.electrical_standard", f"No existe el tipo de señal {electrical_standard}."))
        controller_id = point.get("controller_id")
        controller = controllers.get(controller_id)
        if controller_id and not controller:
            issues.append(_issue("UNKNOWN_CONTROLLER", "error", f"{path}.controller_id", f"No existe el controlador {controller_id}."))
        if controller:
            module_id = point.get("module_id")
            module = controller_modules.get(controller_id, {}).get(module_id)
            if module_id and not module:
                issues.append(_issue("UNKNOWN_IO_MODULE", "error", f"{path}.module_id", f"El controlador {controller_id} no contiene el módulo {module_id}."))
            channel = point.get("channel")
            if module and isinstance(channel, int) and channel >= module.get("channel_count", 0):
                issues.append(_issue("CHANNEL_OUT_OF_RANGE", "error", f"{path}.channel", f"El canal {channel} no existe en {module_id}."))
            channel_key = (str(controller_id), str(module_id), str(channel))
            if channel is not None and channel_key in used_channels:
                issues.append(_issue("CHANNEL_ALREADY_ASSIGNED", "error", path, f"El canal {controller_id}/{module_id}/{channel} está asignado más de una vez."))
            used_channels.add(channel_key)
            if electrical_standard and electrical_standard not in controller.get("interfaces", []):
                issues.append(_issue("SIGNAL_NOT_SUPPORTED_BY_CONTROLLER", "error", f"{path}.electrical_standard", f"{controller_id} no declara la interfaz {electrical_standard}."))
            address = point.get("address")
            address_key = (str(controller_id), str(address))
            if address and address_key in used_addresses:
                issues.append(_issue("ADDRESS_ALREADY_ASSIGNED", "error", f"{path}.address", f"La dirección {address} está repetida en {controller_id}."))
            if address:
                used_addresses.add(address_key)

        field_device_id = point.get("field_device_id")
        device = field_devices.get(field_device_id)
        if field_device_id and not device:
            issues.append(_issue("UNKNOWN_FIELD_DEVICE", "error", f"{path}.field_device_id", f"No existe el equipo de campo {field_device_id}."))
        connection_id = point.get("field_connection_id")
        if device and connection_id:
            connections = {connection.get("id") for connection in device.get("connections", [])}
            if connection_id not in connections:
                issues.append(_issue("UNKNOWN_FIELD_CONNECTION", "error", f"{path}.field_connection_id", f"{field_device_id} no contiene la conexión {connection_id}."))
        if point.get("direction") in {"DO", "AO", "SAFETY_DO"} and not point.get("fail_state"):
            issues.append(_issue("OUTPUT_WITHOUT_FAIL_STATE", "error", f"{path}.fail_state", "Toda salida necesita un estado definido ante fallo."))

    valid_safety_objects = set(field_devices) | set(controllers)
    for index, function in enumerate(project.get("safety", {}).get("safety_functions", [])):
        path = f"safety.safety_functions[{index}]"
        references = (
            function.get("input_device_ids", [])
            + function.get("logic_controller_ids", [])
            + function.get("output_device_ids", [])
        )
        for reference in references:
            if reference not in valid_safety_objects:
                issues.append(_issue("UNKNOWN_SAFETY_OBJECT", "error", path, f"La función de seguridad referencia {reference}, que no existe."))
        if function.get("status") == "validated" and not function.get("validation_record_id"):
            issues.append(_issue("VALIDATED_SAFETY_WITHOUT_RECORD", "error", path, "Una función validada necesita su registro de validación."))

    evidence_ids = {item.get("id") for item in project.get("evidence", [])}
    for collection_name in ("loads",):
        for index, item in enumerate(project.get(collection_name, [])):
            for evidence_id in item.get("source_evidence_ids", []):
                if evidence_id not in evidence_ids:
                    issues.append(_issue("UNKNOWN_EVIDENCE", "error", f"{collection_name}[{index}].source_evidence_ids", f"No existe la evidencia {evidence_id}."))
    for evidence_id in project.get("supply", {}).get("source_evidence_ids", []):
        if evidence_id not in evidence_ids:
            issues.append(_issue("UNKNOWN_EVIDENCE", "error", "supply.source_evidence_ids", f"No existe la evidencia {evidence_id}."))
    for index, controller in enumerate(collections["controllers"]):
        for evidence_id in controller.get("source_evidence_ids", []):
            if evidence_id not in evidence_ids:
                issues.append(_issue("UNKNOWN_EVIDENCE", "error", f"control_system.controllers[{index}].source_evidence_ids", f"No existe la evidencia {evidence_id}."))

    lifecycle = project.get("lifecycle", {})
    blocking_checks = [check for check in lifecycle.get("open_checks", []) if check.get("blocks_manufacture")]
    if lifecycle.get("state") in {"approved_for_manufacture", "as_built"} and blocking_checks:
        issues.append(_issue("MANUFACTURE_STATE_WITH_BLOCKERS", "error", "lifecycle.state", "El proyecto no puede aprobarse para fabricación mientras tenga comprobaciones bloqueantes."))

    errors = sum(issue["severity"] == "error" for issue in issues)
    warnings = sum(issue["severity"] == "warning" for issue in issues)
    return {
        "validator": "super_tecnico.panel_semantic_validator",
        "validator_version": "0.1.0",
        "project_id": project.get("project_id"),
        "valid": errors == 0,
        "summary": {"errors": errors, "warnings": warnings, "open_checks": len(lifecycle.get("open_checks", [])), "blocking_checks": len(blocking_checks)},
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an electrical-panel project and its cross-references.")
    parser.add_argument("project", type=Path)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    project = json.loads(args.project.read_text(encoding="utf-8"))
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    report = validate_project(project, registry)
    print(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
