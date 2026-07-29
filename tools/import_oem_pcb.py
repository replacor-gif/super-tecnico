#!/usr/bin/env python3
"""Create the public PCB OEM projection from the reviewed interchange package."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


OEM_BRAND_SLUGS = {
    "AUX": "aux-air",
    "Daikin": "daikin",
    "Fujitsu General": "fujitsu-general",
    "Gree": "gree",
    "Haier": "haier",
    "Hitachi": "hitachi",
    "Hisense": "hisense",
    "LG": "lg",
    "Midea": "midea",
    "Mitsubishi Electric": "mitsubishi-electric",
    "Mitsubishi Heavy Industries": "mitsubishi-heavy-industries",
    "Panasonic": "panasonic",
    "Samsung": "samsung",
    "Sanyo (legado)": "sanyo-historica",
    "Sharp": "sharp",
    "TCL": "tcl",
    "Toshiba": "toshiba",
    "Chigo": "chigo",
}

PRIMARY_SOURCE_OVERRIDES = {
    1: {
        "url": "https://www.toshiba-aircon.co.uk/wp-content/uploads/2017/09/Service_Manual_SHRMi_A12-006_MMY-MAP_4_FT8-E_080-100-120-140_EN_00.pdf",
        "title": "Toshiba SHRMi service manual A12-006",
        "kind": "manual_servicio_oficial",
        "authority": "primary",
    },
    6: {
        "url": "https://www.samsung.com/my/business/system-air-conditioners/parts-db92-05043d/",
        "title": "Samsung Air Conditioner PBA Main DB92-05043D",
        "kind": "fabricante_oem",
        "authority": "primary",
    },
    8: {
        "url": "https://www.lg.com/br/pecas-e-acessorios-de-ar-condicionado/ebr30056413/",
        "title": "LG placa principal de aire acondicionado EBR30056413",
        "kind": "fabricante_oem",
        "authority": "primary",
    },
}

AMBIGUOUS_MATCHERS = {
    "KFR-xx...": r"^KFR[-A-Z0-9/_.]{2,}$",
    "PCB...": r"^PCB[A-Z0-9/_.-]*$",
    "30xxxxxxxxxx": r"^30\d{4,}$",
    "1712xxxxxxxxxx": r"^1712\d{4,}$",
    "SX...": r"^SX[A-Z0-9]+$",
    "CJ...": r"^CJ[A-Z0-9]+$",
    "E12...": r"^E12[A-Z0-9 -]{0,8}$",
    "CB-/CR-": r"^(?:CB|CR)-[A-Z0-9-]*$",
    "405...": r"^405\d*$",
    "Axxxx-xxx": r"^A[A-Z0-9]{3,8}-[A-Z0-9-]{2,}$",
    "20xxxxxx": r"^20\d{4,}$",
    "651xxxxx": r"^651\d{3,}$",
    "436xxx / 452xxxx": r"^(?:436|452)\d{3,}$",
    "31101-/31201-": r"^(?:31101|31201)-?[A-Z0-9-]+$",
    "1PR03xxxx": r"^1PR03[A-Z0-9-]+$",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def evidence_authority(row: dict[str, Any]) -> str:
    if int(row["id"]) in PRIMARY_SOURCE_OVERRIDES:
        return "primary"
    if row.get("tipo_fuente") == "manual_servicio":
        return "documented"
    return "indirect"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "oem" / "pcb_patterns.json",
    )
    args = parser.parse_args()

    package = args.package.resolve()
    database = package / "base_datos"
    patterns = load_json(database / "SuperTecnico_Identificador_OEM_Placas.json")
    ambiguous = load_json(database / "SuperTecnico_Patrones_Ambiguos.json")
    stats = load_json(database / "estadisticas.json")

    if len(patterns) != 47 or len(ambiguous) != 15:
        raise SystemExit("El paquete OEM no contiene la cobertura v2.0 esperada")

    ids: set[int] = set()
    public_patterns: list[dict[str, Any]] = []
    for row in patterns:
        record_id = int(row["id"])
        if record_id in ids:
            raise SystemExit(f"Patrón OEM duplicado: {record_id}")
        ids.add(record_id)
        re.compile(str(row["regex"]), re.IGNORECASE)
        source = PRIMARY_SOURCE_OVERRIDES.get(record_id) or {
            "url": row["fuente_url"],
            "title": row["fuente_titulo"],
            "kind": row["tipo_fuente"],
            "authority": evidence_authority(row),
        }
        if urlparse(source["url"]).scheme != "https":
            raise SystemExit(f"Fuente OEM no segura: {record_id}")

        confidence = row["confianza"]
        explanation = row["explicacion"]
        exceptions = row["excepciones"]
        if record_id == 7:
            confidence = "media"
            explanation = (
                "DB93 es una familia de referencias Samsung que puede aparecer en placas, "
                "mandos y otros conjuntos; no identifica una PCB por sí sola."
            )
            exceptions = (
                "Aceptar la orientación Samsung únicamente si DB93 está impreso en la propia "
                "placa de climatización o el manual lo describe expresamente como PCB/PBA."
            )

        public_patterns.append({
            "id": record_id,
            "oem": row["fabricante_oem"],
            "brand_slug": OEM_BRAND_SLUGS.get(row["fabricante_oem"]),
            "visible_pattern": row["patron_visible"],
            "regex": row["regex"],
            "search_prefix": row["prefijo_busqueda"],
            "code_type": row["tipo_codigo"],
            "usual_location": row["ubicacion_habitual"],
            "confidence": confidence,
            "recommended_error_table": row["tabla_errores_recomendada"],
            "explanation": explanation,
            "exceptions": exceptions,
            "example": row["ejemplo"],
            "source": source,
            "reviewed_at": row["fecha_revision"],
        })

    public_ambiguous: list[dict[str, str]] = []
    for row in ambiguous:
        label = row["patron_ambiguo"]
        matcher = AMBIGUOUS_MATCHERS.get(label)
        if not matcher:
            raise SystemExit(f"Falta regla pública para el patrón ambiguo {label}")
        re.compile(matcher, re.IGNORECASE)
        public_ambiguous.append({
            "visible_pattern": label,
            "regex": matcher,
            "reason": row["motivo"],
            "recommended_action": row["accion_recomendada"],
        })

    data = {
        "meta": {
            "schema_version": "1.0",
            "data_version": str(stats["version"]),
            "reviewed_at": stats["fecha"],
            "pattern_count": len(public_patterns),
            "oem_count": len({row["oem"] for row in public_patterns}),
            "ambiguous_pattern_count": len(public_ambiguous),
            "high_confidence_count": sum(row["confidence"] == "alta" for row in public_patterns),
            "medium_confidence_count": sum(row["confidence"] == "media" for row in public_patterns),
            "warning": (
                "El código de placa orienta hacia una plataforma electrónica; no demuestra por "
                "sí solo el fabricante, el modelo ni que una tabla de errores sea aplicable."
            ),
        },
        "patterns": public_patterns,
        "ambiguous_patterns": public_ambiguous,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"Generados {len(public_patterns)} patrones, "
        f"{data['meta']['oem_count']} OEM y {len(public_ambiguous)} bloqueos ambiguos"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
