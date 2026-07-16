#!/usr/bin/env python3
"""Relaciona códigos paraguas Fujitsu con subcódigos ya desarrollados."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from audit_brand_quality import audit_brand, write as write_json
from enrich_fujitsu_vrf_v2 import refresh_search


ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "data" / "brands" / "fujitsu-general"
WEB = BRAND / "web"
DETAILS = WEB / "errors" / "details"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


GROUPS = {
    44: {
        "interpretation_id": 65,
        "description": "Código paraguas de sonda de aspiración. La variante VRF documentada utiliza el subcódigo E75.1.",
        "routing_note": "Abre E75.1 para consultar causas, comprobaciones y curva de la sonda de gas de aspiración.",
        "related_errors": [(84, "E: 75.1", "Sonda de temperatura de gas de aspiración")],
    },
    47: {
        "interpretation_id": 69,
        "description": "Código paraguas de sondas de tubería de líquido. En VRF se separa en los subcódigos E83.1 y E83.2.",
        "routing_note": "Selecciona la sonda de líquido 1 o 2 indicada por la unidad exterior; ambas fichas contienen diagnóstico y curva oficial.",
        "related_errors": [(87, "E: 83.1", "Sonda de tubería de líquido 1"), (88, "E: 83.2", "Sonda de tubería de líquido 2")],
    },
    49: {
        "interpretation_id": 77,
        "description": "Código paraguas de bobinas de válvula de expansión exterior. En VRF se identifica la bobina mediante E9A.1, E9A.2 o E9A.3.",
        "routing_note": "Abre la bobina señalada por el subcódigo para ver resistencias de devanado, alimentación, conexiones y prueba de la válvula.",
        "related_errors": [(99, "E: 9A.1", "Bobina 1 de válvula de expansión"), (100, "E: 9A.2", "Bobina 2 de válvula de expansión"), (101, "E: 9A.3", "Bobina 3 de válvula de expansión")],
    },
    50: {
        "interpretation_id": 80,
        "description": "Código paraguas de alta presión. Las variantes VRF documentadas distinguen alta presión E A4.1 y acción de protección E A4.2.",
        "routing_note": "Abre E A4.1 o E A4.2 según el subcódigo mostrado; las fichas separan detección, protección, causas y comprobaciones.",
        "related_errors": [(105, "E: A4.1", "Alta presión exterior"), (106, "E: A4.2", "Acción de protección de alta presión 1")],
    },
}


def main() -> int:
    for error_id, spec in GROUPS.items():
        path = DETAILS / f"{error_id}.json"
        detail = load(path)
        interpretation = next(row for row in detail["interpretations"] if int(row["id"]) == spec["interpretation_id"])
        interpretation["entry_role"] = "grouping_reference"
        interpretation["description"] = spec["description"]
        interpretation["routing_note"] = spec["routing_note"]
        interpretation["related_errors"] = [
            {"id": target_id, "code_display": code, "label": label}
            for target_id, code, label in spec["related_errors"]
        ]
        write_json(path, detail)

    config_path = BRAND / "brand.json"
    config = load(config_path)
    config["data_version"] = "2.11.0"
    config["notes"] = "Fujitsu V2: códigos paraguas enlazados a sus subcódigos técnicos sin duplicar diagnósticos."
    write_json(config_path, config)

    refresh_search()
    report = audit_brand(BRAND)
    write_json(WEB / "quality.json", report)
    print(json.dumps({
        "grouping_codes": len(GROUPS),
        "interpretations": report["errors"]["interpretations"],
        "technical_interpretations": report["errors"]["technical_interpretations"],
        "statuses": report["errors"]["status_counts"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
