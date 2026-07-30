#!/usr/bin/env python3
"""Import a broad, minimal reference index from official manufacturer catalogues.

The detailed component records remain untouched.  This importer adds catalogue
references with only the fields that are safe to derive from an official
selection guide: part number, manufacturer, broad family and source page.

Current source:
    Nexperia Selection Guide 2025
    Texas Instruments Enhanced Product Selection Guide
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pdfplumber

from build_component_expansion_v2 import (
    OUTPUT,
    load_existing_pairs,
    normalize,
    validate,
)


GENERATION = "component-reference-index-v4"
RETRIEVED_DATE = "2026-07-30"
NEXPERIA_GUIDE_URL = (
    "https://assets.nexperia.com/documents/selection-guide/"
    "Nexperia_Selection_Guide_2025.pdf"
)
TI_GUIDE_URL = "https://www.ti.com/lit/sg/sgzt005c/sgzt005c.pdf"


@dataclass(frozen=True)
class Section:
    first_page: int
    last_page: int
    category: str
    subtype: str
    prefixes: frozenset[str]


TRANSISTOR_PREFIXES = frozenset(
    {
        "2PA", "2PB", "2PC", "2PD",
        "BC", "BCM", "BCP", "BCV", "BCW", "BCX", "BF", "BFS", "BSP",
        "BSR", "BSS", "BST", "MJD", "MJPE", "MMBT", "MMBTA", "NCR",
        "NHDTA", "NHDTC", "NHUMB", "NHUMD", "NHUMH", "NMB", "PBHV",
        "PBLS", "PBRN", "PBRP", "PBSM", "PBSS", "PDTA", "PDTB", "PDTC",
        "PDTD", "PHPT", "PIMC", "PIMN", "PIMP", "PIMT", "PIMZ", "PMBS",
        "PMBT", "PMBTA", "PMD", "PMMT", "PMP", "PMSS", "PMST", "PMSTA",
        "PQMB", "PQMD", "PQMH", "PRMB", "PRMD", "PRMH", "PSSI", "PUMB",
        "PUMD", "PUMH", "PUMT", "PUMX", "PUMZ", "PXT", "PXTA", "PZT",
        "PZTA", "TL", "TLVH",
    }
)

DIODE_PREFIXES = frozenset(
    {
        "1PS", "BAL", "BAS", "BAT", "BAV", "BAW", "BZB", "BZT", "BZV",
        "BZX", "MM", "PLVA", "PMBD", "PMEG", "PNE", "PNS", "PNU", "PSC",
        "PZU", "RB", "SZMM",
    }
)

PROTECTION_PREFIXES = frozenset(
    {
        "BZA", "IP", "MMBZ", "NUP", "PCMF", "PESD", "PHDMI", "PRTR",
        "PTVS", "PUSB",
    }
)

MOSFET_PREFIXES = frozenset(
    {
        "2N", "BSH", "BSN", "BSS", "BUK", "BXK", "NX", "NXV", "PMCA",
        "PMCB", "PMCM", "PMCPB", "PMCXB", "PMDPB", "PMDXB", "PMF", "PMG",
        "PMGD", "PMH", "PMN", "PMPB", "PMV", "PMX", "PMXB", "PMZ", "PMZB",
        "PSMN", "PSMNR", "PSMP", "PXN", "PXP",
    }
)

LOGIC_PREFIXES = frozenset(
    {
        "74ABT", "74ABTH", "74AHC", "74AHCT", "74AHCU", "74AHCV",
        "74ALVC", "74ALVCH", "74ALVT", "74AUP", "74AVC", "74AVCH",
        "74AXP", "74CB", "74CBTLV", "74CBTLVD", "74HC", "74HCT", "74HCU",
        "74LV", "74LVC", "74LVCH", "74LVCU", "74LVCV", "74LVT", "74LVTH",
        "74LVTN", "74VHC", "74VHCT", "AXP", "CBT", "CBTD", "HEF", "LSF",
        "NCA", "NMUX", "NXB", "NXS", "NXT", "NXU", "PCA", "XC", "XS",
    }
)

SECTIONS = (
    Section(22, 46, "Transistor BJT", "Transistores bipolares", TRANSISTOR_PREFIXES),
    Section(50, 70, "Diodo", "Diodos y rectificadores", DIODE_PREFIXES),
    Section(74, 95, "Diodo", "Protección ESD y TVS", PROTECTION_PREFIXES),
    Section(98, 128, "MOSFET", "MOSFET de silicio", MOSFET_PREFIXES),
    Section(132, 132, "MOSFET", "MOSFET de carburo de silicio", frozenset({"NSF"})),
    Section(137, 137, "GaN FET", "Transistores de potencia GaN", frozenset({"GAN", "GANB", "GANE"})),
    Section(140, 140, "IGBT", "IGBT de potencia", frozenset({"NGW"})),
    Section(144, 196, "Circuito integrado", "Circuitos analógicos y lógica", LOGIC_PREFIXES),
)

TOKEN_RE = re.compile(r"(?<![A-Za-z0-9])[A-Z0-9][A-Z0-9_-]{2,}(?![A-Za-z0-9])")
OPTIONAL_Q_RE = re.compile(r"\b([A-Z0-9][A-Z0-9-]{2,})\s*\(-Q\)")


def token_prefix(value: str) -> str:
    match = re.match(r"(?:[0-9]+)?[A-Z]+", value)
    return match.group(0) if match else ""


def valid_token(value: str, prefixes: frozenset[str]) -> bool:
    if not 4 <= len(value) <= 40:
        return False
    if value.endswith("-") or "--" in value:
        return False
    if not re.search(r"[A-Z]", value) or not re.search(r"\d", value):
        return False
    prefix = token_prefix(value)
    if prefix not in prefixes:
        return False
    if prefix == "IP" and len(value) < 7:
        return False
    if value in {"2XNPN", "2XPNP", "Q100"}:
        return False
    # PDF extraction occasionally joins two adjacent part numbers.
    if sum(value.count(marker) for marker in ("PESD", "PHDMI", "PUSB", "PCMF")) > 1:
        return False
    if value.startswith("PHDMI") and "USB3" in value:
        return False
    return True


def extract_section(pdf: pdfplumber.PDF, section: Section) -> dict[str, int]:
    references: dict[str, int] = {}
    for printed_page in range(section.first_page, section.last_page + 1):
        text = pdf.pages[printed_page - 1].extract_text() or ""
        tokens = set(TOKEN_RE.findall(text))
        tokens.update(match.group(1) for match in OPTIONAL_Q_RE.finditer(text))
        for token in sorted(tokens):
            if not valid_token(token, section.prefixes):
                continue
            references.setdefault(token, printed_page)
            if re.search(rf"\b{re.escape(token)}\s*\(-Q\)", text):
                references.setdefault(f"{token}-Q", printed_page)
    return references


def minimal_record(
    part_number: str,
    category: str,
    subtype: str,
    page: int,
    *,
    manufacturer: str = "Nexperia",
    guide_url: str = NEXPERIA_GUIDE_URL,
    guide_title: str = "Nexperia Selection Guide 2025",
) -> dict[str, Any]:
    source_title = f"{guide_title}, página {page}"
    description = (
        f"Referencia incluida en el índice oficial de {manufacturer} dentro de "
        f"«{subtype}». Ficha mínima destinada a identificación y búsqueda."
    )
    return {
        "part_number": part_number,
        "manufacturer": manufacturer,
        "category": category,
        "subtype": subtype,
        "description": description,
        "packages": [],
        "markings": [],
        "aliases": [],
        "quality": "oficial_indice",
        "quality_rank": 5,
        "confidence": 0.98,
        "official": True,
        "generic": False,
        "record_level": "indice",
        "voltage_max_v": None,
        "current_max_a": None,
        "power_max_w": None,
        "rds_on_max_ohm": None,
        "frequency_hz": None,
        "lifecycle_status": "Incluido en el catálogo oficial de selección 2025",
        "notes": (
            "Ficha de índice: confirma el sufijo, encapsulado, patillaje y límites "
            "en la ficha de producto antes de comprobar o sustituir el componente."
        ),
        "datasheet_url": guide_url,
        "specifications": [],
        "package_details": [],
        "marking_details": [],
        "pinouts": [],
        "applications": [],
        "equivalents": [],
        "verification": [],
        "source": {
            "title": source_title,
            "publisher": manufacturer,
            "url": guide_url,
            "type": "catálogo oficial del fabricante",
            "authority": 5,
            "retrieved_date": RETRIEVED_DATE,
            "page": page,
        },
        "generation": GENERATION,
    }


def extract_candidates(pdf_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with pdfplumber.open(pdf_path) as pdf:
        if len(pdf.pages) != 240:
            raise RuntimeError(
                f"Se esperaban 240 páginas en Nexperia Selection Guide 2025; "
                f"se encontraron {len(pdf.pages)}"
            )
        for section in SECTIONS:
            references = extract_section(pdf, section)
            for part, page in references.items():
                category = section.category
                subtype = section.subtype
                if part.startswith(("TL431", "TLVH431")):
                    category = "Regulador / referencia"
                    subtype = "Reguladores shunt ajustables"
                rows.append(minimal_record(part, category, subtype, page))
        # These three type numbers are split across two lines in the printed table.
        for part in ("NXF6505ADA-Q100", "NXF6505BDA-Q100", "NXF6501DC-Q100"):
            rows.append(
                minimal_record(
                    part,
                    "Circuito integrado",
                    "Driver de transformador para alimentación aislada",
                    196,
                )
            )
    return rows


TI_PAGE_GROUPS = (
    (7, 11, "Amplificador / comparador", "Amplificadores y comparadores"),
    (13, 13, "Circuito integrado", "Circuitos de audio"),
    (15, 15, "Circuito integrado", "Reloj y temporización"),
    (17, 18, "Circuito integrado", "Convertidores de datos"),
    (20, 24, "Circuito integrado", "Interfaces y comunicaciones"),
    (26, 33, "Circuito integrado", "Lógica digital"),
    (35, 35, "Driver de potencia", "Control y drivers de motor"),
    (37, 40, "Circuito integrado", "Procesadores y controladores"),
    (42, 45, "Regulador / referencia", "Reguladores lineales"),
    (46, 50, "Controlador de fuente", "Gestión y conversión de potencia"),
    (51, 51, "Regulador / referencia", "Referencias y supervisores"),
    (52, 53, "Controlador de fuente", "Alimentación y drivers"),
    (55, 55, "Sensor", "Sensores"),
    (57, 57, "Circuito integrado", "Interruptores y multiplexores"),
)
TI_EP_RE = re.compile(r"\b[A-Z][A-Z0-9-]{2,}-EP\b")


def extract_ti_candidates(pdf_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with pdfplumber.open(pdf_path) as pdf:
        if len(pdf.pages) != 59:
            raise RuntimeError(
                f"Se esperaban 59 páginas en TI Enhanced Product Selection Guide; "
                f"se encontraron {len(pdf.pages)}"
            )
        for first_page, last_page, category, subtype in TI_PAGE_GROUPS:
            for printed_page in range(first_page, last_page + 1):
                text = pdf.pages[printed_page - 1].extract_text() or ""
                for part in sorted(set(TI_EP_RE.findall(text))):
                    rows.append(
                        minimal_record(
                            part,
                            category,
                            subtype,
                            printed_page,
                            manufacturer="Texas Instruments",
                            guide_url=TI_GUIDE_URL,
                            guide_title="TI Enhanced Product Selection Guide",
                        )
                    )
    return rows


def select_new_rows(
    candidates: Iterable[dict[str, Any]],
    existing_pairs: set[tuple[str, str]],
    preserved_pairs: set[tuple[str, str]],
) -> tuple[list[dict[str, Any]], list[str]]:
    selected: list[dict[str, Any]] = []
    skipped: list[str] = []
    seen: set[tuple[str, str]] = set()
    for row in sorted(candidates, key=lambda item: normalize(item["part_number"])):
        key = (normalize(row["part_number"]), normalize(row["manufacturer"]))
        if key in seen:
            continue
        seen.add(key)
        if key in existing_pairs or key in preserved_pairs:
            skipped.append(row["part_number"])
            continue
        selected.append(row)
    return selected, skipped


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path, help="SQLite maestro privado")
    parser.add_argument("nexperia_pdf", type=Path, help="Nexperia Selection Guide 2025")
    parser.add_argument(
        "ti_pdf",
        type=Path,
        help="TI Enhanced Product Selection Guide",
    )
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    existing_pairs, maximum_id = load_existing_pairs(args.database)
    prior = json.loads(args.output.read_text(encoding="utf-8")) if args.output.is_file() else []
    preserved = [row for row in prior if row.get("generation") != GENERATION]
    preserved_pairs = {
        (normalize(row["part_number"]), normalize(row.get("manufacturer") or ""))
        for row in preserved
    }

    candidates = extract_candidates(args.nexperia_pdf) + extract_ti_candidates(args.ti_pdf)
    selected, skipped = select_new_rows(candidates, existing_pairs, preserved_pairs)
    next_id = max([maximum_id, *[int(row["id"]) for row in preserved]], default=0) + 1
    for row in selected:
        row["id"] = next_id
        next_id += 1

    output = sorted(preserved + selected, key=lambda row: int(row["id"]))
    validate(output)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    by_category: dict[str, int] = {}
    for row in selected:
        by_category[row["category"]] = by_category.get(row["category"], 0) + 1
    report = {
        "sources": [
            {"url": NEXPERIA_GUIDE_URL, "pages": 240},
            {"url": TI_GUIDE_URL, "pages": 59},
        ],
        "extracted_unique": len({normalize(row["part_number"]) for row in candidates}),
        "preserved": len(preserved),
        "added": len(selected),
        "skipped_existing": len(skipped),
        "categories": dict(sorted(by_category.items())),
        "first_id": selected[0]["id"] if selected else None,
        "last_id": selected[-1]["id"] if selected else None,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
