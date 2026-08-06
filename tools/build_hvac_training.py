#!/usr/bin/env python3
"""Convert the Replacor HVAC technical collection into web-course data.

The DOCX files remain the editable source of truth.  This builder preserves the
document order, headings, lists, tables, warnings and figure positions while
producing a compact JSON data set for the public static application.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

from docx import Document
from docx.document import Document as DocumentObject
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph


FACETS: dict[str, tuple[str, ...]] = {
    "componentes": (
        "capilar", "txv", "eev", "válvula", "compresor", "ventilador",
        "motor", "sonda", "termistor", "presostato", "transductor",
        "termostato", "intercambiador", "evaporador", "condensador",
        "solenoide", "bomba", "sensor", "bobina", "ipm", "pfc",
    ),
    "tecnologías": (
        "inverter", "pmsm", "bldc", "psc", "foc", "sensorless", "pwm",
        "adc", "microcanal", "placas", "scroll", "rotary", "centrífugo",
        "tornillo", "electrónica", "firmware",
    ),
    "síntomas": (
        "no arranca", "no gira", "ruido", "vibración", "hielo", "escarcha",
        "sobrecalentamiento", "baja presión", "alta presión", "fuga",
        "bloqueo", "cortocircuito", "circuito abierto", "consumo",
        "caudal insuficiente", "retorno de líquido", "hunting",
    ),
    "mediciones": (
        "tensión", "voltaje", "corriente", "resistencia", "continuidad",
        "presión", "temperatura", "frecuencia", "capacidad", "aislamiento",
        "recalentamiento", "subenfriamiento", "caudal", "rpm", "pulsos",
    ),
    "instrumentos": (
        "multímetro", "pinza amperimétrica", "manómetro", "termómetro",
        "osciloscopio", "megóhmetro", "tacómetro", "analizador",
    ),
    "señales": (
        "bus dc", "señal hall", "realimentación", "back-emf", "pwm",
        "pulsos", "comunicación", "señal analógica", "señal digital",
    ),
    "control de placa": (
        "placa", "control", "protección", "algoritmo", "driver", "triac",
        "relé", "inversor", "microcontrolador", "entrada", "salida",
    ),
}


MODULE_DETAILS = {
    "01": {
        "summary": "Capilares, orificios fijos, TXV y EEV: funcionamiento, selección y diagnóstico.",
        "icon": "↘",
        "accent": "#0f7b79",
    },
    "02": {
        "summary": "Motores AC, PSC, BLDC y PMSM, sus señales y el control de ventilación.",
        "icon": "◉",
        "accent": "#256a8a",
    },
    "03": {
        "summary": "Sondas NTC/PTC, divisores, conversión ADC y comprobación en la máquina.",
        "icon": "ϑ",
        "accent": "#42705f",
    },
    "04": {
        "summary": "Termostatos, presostatos, transductores, caudal y lógica de desescarche.",
        "icon": "⌁",
        "accent": "#6f6a35",
    },
    "05": {
        "summary": "Válvulas de 2, 3 y 4 vías, solenoides, hidráulica y control electrónico.",
        "icon": "⋈",
        "accent": "#8b5a38",
    },
    "06": {
        "summary": "Intercambio térmico, baterías, microcanal, placas, ensuciamiento y fugas.",
        "icon": "▦",
        "accent": "#50658b",
    },
    "07": {
        "summary": "Familias de compresores y bloque avanzado de motores PMSM/IPM inverter.",
        "icon": "C",
        "accent": "#765486",
    },
}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def slugify(value: str) -> str:
    value = "".join(
        char for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    ).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:72] or "apartado"


def normalize(value: str) -> str:
    value = "".join(
        char for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    ).lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value)).strip()


def iter_blocks(document: DocumentObject) -> Iterator[Paragraph | Table]:
    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield Table(child, document)


def heading_level(paragraph: Paragraph) -> int | None:
    style_name = (paragraph.style.name if paragraph.style else "") or ""
    match = re.search(r"(?:Heading|Título|Titulo)\s*([1-6])", style_name, re.I)
    if match:
        return int(match.group(1))
    p_pr = paragraph._p.pPr
    outline = p_pr.find(qn("w:outlineLvl")) if p_pr is not None else None
    if outline is not None:
        return int(outline.get(qn("w:val"))) + 1
    return None


def is_list(paragraph: Paragraph) -> bool:
    p_pr = paragraph._p.pPr
    return bool(p_pr is not None and p_pr.find(qn("w:numPr")) is not None)


def paragraph_drawings(paragraph: Paragraph) -> int:
    return len(paragraph._p.xpath(".//a:blip"))


def classify_callout(text: str) -> str | None:
    lower = normalize(text)
    if re.match(r"^(advertencia|precaucion|peligro|seguridad|atencion)\b", lower):
        return "warning"
    if re.match(r"^(nota|importante|recuerda|criterio practico)\b", lower):
        return "note"
    if re.match(r"^(procedimiento|comprobacion|diagnostico|paso)\b", lower):
        return "procedure"
    return None


def extract_facets(text: str) -> dict[str, list[str]]:
    haystack = normalize(text)
    result: dict[str, list[str]] = {}
    for group, terms in FACETS.items():
        matches = [term for term in terms if normalize(term) in haystack]
        if matches:
            result[group] = sorted(set(matches))
    return result


def table_payload(table: Table) -> dict[str, Any] | None:
    rows = [
        [re.sub(r"\s+", " ", cell.text).strip() for cell in row.cells]
        for row in table.rows
    ]
    rows = [row for row in rows if any(row)]
    if not rows:
        return None
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    return {"type": "table", "headers": rows[0], "rows": rows[1:]}


def build_module(
    module_meta: dict[str, Any],
    module_dir: Path,
    public_assets: Path,
) -> tuple[dict[str, Any], dict[str, int]]:
    module_id = str(module_meta["id"])
    docx_files = sorted(module_dir.rglob("*.docx"))
    if len(docx_files) != 1:
        raise RuntimeError(f"El módulo {module_id} debe contener un único DOCX")
    document = Document(docx_files[0])
    source_figures = sorted((docx_files[0].parent / "figuras").glob("*.png"))
    figure_destination = public_assets / f"module-{module_id}"
    figure_destination.mkdir(parents=True, exist_ok=True)
    for source in source_figures:
        shutil.copy2(source, figure_destination / source.name)

    module = {
        "id": module_id,
        "title": module_meta["title"],
        "summary": MODULE_DETAILS[module_id]["summary"],
        "icon": MODULE_DETAILS[module_id]["icon"],
        "accent": MODULE_DETAILS[module_id]["accent"],
        "pages": int(module_meta.get("pages") or 0),
        "keywords": module_meta.get("keywords") or [],
        "chapters": [],
    }
    intro_blocks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    chapter_numbers: Counter[str] = Counter()
    figure_index = 0
    list_items: list[str] = []

    def destination_blocks() -> list[dict[str, Any]]:
        return current["blocks"] if current is not None else intro_blocks

    def flush_list() -> None:
        nonlocal list_items
        if list_items:
            destination_blocks().append({"type": "list", "items": list_items})
            list_items = []

    for block in iter_blocks(document):
        if isinstance(block, Table):
            flush_list()
            payload = table_payload(block)
            if payload:
                destination_blocks().append(payload)
            continue

        text = re.sub(r"\s+", " ", block.text).strip()
        style_name = (block.style.name if block.style else "") or ""
        if style_name.lower().startswith(("toc", "tabla de contenido")):
            continue
        level = heading_level(block)
        drawings = paragraph_drawings(block)

        if level and text:
            flush_list()
            clean_heading = re.sub(r"\s*\[Volver al índice\]\s*$", "", text, flags=re.I).strip()
            if level == 1:
                normalized_heading = normalize(clean_heading)
                if normalized_heading == normalize(module_meta["title"]):
                    continue
                if normalized_heading.startswith(("indice navegable", "indice de consulta")):
                    continue
                base = slugify(clean_heading)
                chapter_numbers[base] += 1
                suffix = "" if chapter_numbers[base] == 1 else f"-{chapter_numbers[base]}"
                current = {
                    "id": f"m{module_id}-{base}{suffix}",
                    "title": clean_heading,
                    "level": level,
                    "blocks": [],
                }
                module["chapters"].append(current)
            else:
                destination_blocks().append({"type": "subheading", "level": level, "text": clean_heading})
            continue

        if drawings:
            flush_list()
            for _ in range(drawings):
                if figure_index >= len(source_figures):
                    destination_blocks().append({
                        "type": "callout",
                        "kind": "note",
                        "text": "Figura presente en el documento original; recurso gráfico pendiente de asociar.",
                    })
                    continue
                figure = source_figures[figure_index]
                figure_index += 1
                destination_blocks().append({
                    "type": "figure",
                    "src": f"assets/training/module-{module_id}/{figure.name}",
                    "alt": figure.stem.replace("_", " "),
                    "caption": "",
                })

        if not text:
            continue
        if "caption" in style_name.lower() or "epígrafe" in style_name.lower() or re.match(r"^(figura|fig\.)\s*\d+", text, re.I):
            flush_list()
            blocks = destination_blocks()
            if blocks and blocks[-1].get("type") == "figure" and not blocks[-1].get("caption"):
                blocks[-1]["caption"] = text
            else:
                blocks.append({"type": "caption", "text": text})
            continue
        if is_list(block):
            list_items.append(text)
            continue

        flush_list()
        kind = classify_callout(text)
        destination_blocks().append(
            {"type": "callout", "kind": kind, "text": text}
            if kind else {"type": "paragraph", "text": text}
        )

    flush_list()
    if figure_index < len(source_figures):
        appendix = {
            "id": f"m{module_id}-figuras-complementarias",
            "title": "Figuras complementarias",
            "level": 1,
            "blocks": [],
        }
        for figure in source_figures[figure_index:]:
            appendix["blocks"].append({
                "type": "figure",
                "src": f"assets/training/module-{module_id}/{figure.name}",
                "alt": figure.stem.replace("_", " "),
                "caption": figure.stem.replace("_", " "),
            })
        figure_index = len(source_figures)
        module["chapters"].append(appendix)
    if intro_blocks:
        if module["chapters"]:
            module["chapters"][0]["blocks"] = intro_blocks + module["chapters"][0]["blocks"]
        else:
            module["chapters"].append({
                "id": f"m{module_id}-introduccion",
                "title": "Introducción",
                "level": 1,
                "blocks": intro_blocks,
            })

    # The source documents include a printed table of contents as ordinary
    # paragraphs in addition to real Word headings.  The web course already
    # provides a chapter selector and sidebar, so keeping those duplicates
    # makes the first chapter needlessly long and less useful on a phone.
    # Remove only exact heading repetitions and navigation boilerplate; all
    # explanatory and technical content remains untouched.
    heading_keys = {
        normalize(chapter["title"])
        for chapter in module["chapters"]
    }
    heading_keys.update(
        normalize(block["text"])
        for chapter in module["chapters"]
        for block in chapter["blocks"]
        if block.get("type") == "subheading" and block.get("text")
    )
    for chapter in module["chapters"]:
        cleaned_blocks: list[dict[str, Any]] = []
        for block in chapter["blocks"]:
            if block.get("type") != "paragraph":
                cleaned_blocks.append(block)
                continue
            key = normalize(block.get("text") or "")
            if key in heading_keys or key == "volver al indice":
                continue
            if key.startswith("pulse una entrada para ir directamente"):
                continue
            cleaned_blocks.append(block)
        chapter["blocks"] = cleaned_blocks

    for chapter in module["chapters"]:
        searchable: list[str] = [chapter["title"]]
        for block in chapter["blocks"]:
            if block["type"] == "table":
                searchable.extend(block["headers"])
                searchable.extend(cell for row in block["rows"] for cell in row)
            elif block["type"] == "list":
                searchable.extend(block["items"])
            else:
                searchable.append(str(block.get("text") or block.get("caption") or block.get("alt") or ""))
        full_text = " ".join(searchable)
        chapter["facets"] = extract_facets(full_text)
        chapter["search"] = normalize(full_text)
        chapter["word_count"] = len(full_text.split())

    stats = {
        "chapters": len(module["chapters"]),
        "figures_available": len(source_figures),
        "figures_linked": figure_index,
        "tables": sum(
            block["type"] == "table"
            for chapter in module["chapters"]
            for block in chapter["blocks"]
        ),
        "words": sum(chapter["word_count"] for chapter in module["chapters"]),
    }
    module["stats"] = stats
    return module, stats


def build(source_root: Path, project_root: Path) -> dict[str, Any]:
    manifest_path = source_root / "00_INTEGRACION" / "manifest_modulos.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expanded_root = source_root.parent.parent / "incoming_coleccion_expanded"
    if not expanded_root.is_dir():
        raise RuntimeError(f"No existe la colección expandida: {expanded_root}")

    assets_root = project_root / "assets" / "training"
    if assets_root.exists():
        shutil.rmtree(assets_root)
    assets_root.mkdir(parents=True)

    modules: list[dict[str, Any]] = []
    module_stats: dict[str, dict[str, int]] = {}
    for module_meta in manifest["modules"]:
        module_dir = expanded_root / module_meta["folder"]
        module, stats = build_module(module_meta, module_dir, assets_root)
        modules.append(module)
        module_stats[module["id"]] = stats

    chapter_count = sum(len(module["chapters"]) for module in modules)
    figure_count = sum(module["stats"]["figures_available"] for module in modules)
    table_count = sum(module["stats"]["tables"] for module in modules)
    word_count = sum(module["stats"]["words"] for module in modules)
    collection = {
        "schema_version": "1.0",
        "title": "Curso técnico de climatización Replacor",
        "language": "es-ES",
        "generated": manifest.get("generated"),
        "notice": "Contenido didáctico general. Los valores y secuencias específicos deben confirmarse con el manual OEM del equipo.",
        "stats": {
            "modules": len(modules),
            "pages": sum(int(module["pages"]) for module in modules),
            "chapters": chapter_count,
            "figures": figure_count,
            "tables": table_count,
            "words": word_count,
        },
        "facet_groups": list(FACETS),
        "modules": modules,
    }
    write_json(project_root / "data" / "training" / "collection.json", collection)
    report = {
        "collection": collection["stats"],
        "modules": module_stats,
        "manifest_figures": sum(int(item.get("figures") or 0) for item in manifest["modules"]),
    }
    write_json(project_root / "data" / "training" / "build-report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(build(args.source.resolve(), args.project.resolve()), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
