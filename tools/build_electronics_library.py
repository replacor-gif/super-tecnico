#!/usr/bin/env python3
"""Build the interactive electronics-board library from Replacor DOCX sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any, Iterator

from docx import Document
from docx.document import Document as DocumentObject
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph


MODULE_DETAILS: dict[str, dict[str, Any]] = {
    "08": {"group": "alimentacion", "icon": "SMPS", "level": "intermedio", "summary": "Arranque, VCC, PWM, flyback, feedback, protecciones y diagnóstico por síntoma."},
    "09": {"group": "proteccion", "icon": "EMI", "level": "intermedio", "summary": "Filtros de red y señal, ruido común/diferencial, condensadores X/Y y chokes."},
    "10": {"group": "potencia", "icon": "PFC", "level": "avanzado", "summary": "PFC pasivo y activo, bus DC, señales de control, protecciones y diferenciación del inverter."},
    "11": {"group": "comunicacion", "icon": "BUS", "level": "avanzado", "summary": "Arquitecturas de comunicación, paso por cero, cableado, medidas y diagnóstico completo."},
    "12": {"group": "medicion", "icon": "V", "level": "intermedio", "summary": "Divisores, ADC, referencias, bus DC, red y cadenas de medida de tensión."},
    "13": {"group": "medicion", "icon": "A", "level": "avanzado", "summary": "Shunts, Hall, CT, amplificación, muestreo y falsas sobrecorrientes."},
    "14": {"group": "control", "icon": "MCU", "level": "avanzado", "summary": "Alimentación, reset, reloj, memorias, firmware, buses y prueba de vida del micro."},
    "15": {"group": "senal", "icon": "CMP", "level": "intermedio", "summary": "Umbral, histéresis, salidas open-collector, protecciones y sustitución."},
    "16": {"group": "salidas", "icon": "ULN", "level": "intermedio", "summary": "Arrays Darlington, COM, cargas inductivas, fallos por canal y límites térmicos."},
    "17": {"group": "alimentacion", "icon": "C", "level": "intermedio", "summary": "Desacoplo, bypass, bulk, ESR/ESL, cortos de rail y diagnóstico con osciloscopio."},
    "18": {"group": "aislamiento", "icon": "OPTO", "level": "intermedio", "summary": "CTR, pull-up, optos rápidos, fuentes, comunicación y prueba dinámica."},
    "19": {"group": "senal", "icon": "OP", "level": "intermedio", "summary": "Buffers, ganancia, modo común, offset, filtrado y acondicionamiento para ADC."},
    "20": {"group": "salidas", "icon": "AC", "level": "intermedio", "summary": "TRIAC, SCR, optotriac, cruce por cero, snubber y control de cargas AC."},
    "21": {"group": "salidas", "icon": "K", "level": "basico", "summary": "Relés, contactores, bobinas, contactos, drivers y fallos mecánicos/eléctricos."},
    "22": {"group": "alimentacion", "icon": "DC", "level": "intermedio", "summary": "Reguladores lineales, LDO, buck/boost, estabilidad, rails hundidos y secuencias."},
    "23": {"group": "proteccion", "icon": "D", "level": "basico", "summary": "Rectificadores, Schottky, ultrafast, zéner, TVS, clamps y pruebas de fuga."},
    "24": {"group": "salidas", "icon": "Q", "level": "basico", "summary": "BJT y MOSFET de señal, low/high-side, adaptación de nivel y pinout."},
    "25": {"group": "potencia", "icon": "IGBT", "level": "avanzado", "summary": "MOSFET/IGBT, gate charge, SOA, pérdidas, shoot-through y sustitución."},
    "26": {"group": "potencia", "icon": "DRV", "level": "avanzado", "summary": "Drivers low/high-side, bootstrap, UVLO, dead-time, DESAT y medidas flotantes."},
    "27": {"group": "potencia", "icon": "IPM", "level": "avanzado", "summary": "Puente trifásico, entradas PWM, FAULT, shunts, arranque y diagnóstico IPM-compresor."},
    "28": {"group": "pasivos", "icon": "R", "level": "basico", "summary": "Códigos, potencia, TCR, divisores, shunts, precarga, descarga y redes."},
    "29": {"group": "pasivos", "icon": "L", "level": "intermedio", "summary": "Inductores, transformadores, saturación, espiras en corto, LCR y ring tester."},
    "30": {"group": "diagnostico", "icon": "PCB", "level": "intermedio", "summary": "Método universal para mapear alimentación, control, entradas, salidas e inverter."},
}

# Orden didáctico: fundamentos y componentes, bloques de señal y control,
# potencia/inverter y, al final, el método global de diagnóstico.
PEDAGOGICAL_ORDER = [
    "28", "23", "24", "29", "21", "17", "22", "08", "12", "13", "15",
    "19", "18", "16", "20", "09", "14", "11", "25", "26", "10", "27", "30",
]

GROUPS = [
    {"id": "diagnostico", "title": "Diagnóstico y método", "summary": "Empieza aquí cuando no tienes esquema o todavía no sabes qué bloque falla."},
    {"id": "alimentacion", "title": "Alimentación y rails", "summary": "Desde la fuente auxiliar hasta los reguladores locales y el desacoplo."},
    {"id": "medicion", "title": "Medición de tensión y corriente", "summary": "Cómo la placa convierte magnitudes eléctricas en señales que entiende el micro."},
    {"id": "comunicacion", "title": "Comunicaciones", "summary": "Interconexión, buses, paso por cero, cableado, ruido y diagnóstico."},
    {"id": "control", "title": "Control, memorias y firmware", "summary": "Secuencia de arranque y comprobaciones para demostrar si el control está vivo."},
    {"id": "senal", "title": "Tratamiento de señal", "summary": "Comparadores, operacionales, referencias y acondicionamiento analógico."},
    {"id": "aislamiento", "title": "Aislamiento", "summary": "Optoacopladores y separación entre dominios eléctricos."},
    {"id": "salidas", "title": "Salidas y actuadores", "summary": "Drivers, transistores, relés, TRIAC y caminos de mando hacia la carga."},
    {"id": "potencia", "title": "Potencia e inverter", "summary": "PFC, semiconductores, drivers e IPM de la etapa trifásica."},
    {"id": "proteccion", "title": "Protección, EMI y EMC", "summary": "Filtros y dispositivos que limitan ruido, transitorios y daños."},
    {"id": "pasivos", "title": "Componentes pasivos", "summary": "Resistencias, redes y magnéticos vistos desde la reparación."},
]

RELATED: dict[str, list[str]] = {
    "08": ["17", "18", "22", "23", "28", "29"], "09": ["11", "17", "29", "30"],
    "10": ["12", "13", "25", "26", "27"], "11": ["09", "14", "18", "30"],
    "12": ["15", "17", "19", "28"], "13": ["15", "19", "25", "27", "28"],
    "14": ["11", "17", "18", "22", "30"], "15": ["12", "13", "19", "23", "28"],
    "16": ["21", "23", "24", "28"], "17": ["08", "12", "14", "22"],
    "18": ["08", "11", "20", "26"], "19": ["12", "13", "15", "17"],
    "20": ["18", "21", "23", "28"], "21": ["16", "20", "23", "24"],
    "22": ["08", "17", "23", "28", "29"], "23": ["08", "20", "22", "25", "26"],
    "24": ["16", "21", "22", "28"], "25": ["10", "13", "26", "27"],
    "26": ["10", "18", "23", "25", "27"], "27": ["10", "13", "25", "26"],
    "28": ["08", "12", "13", "15", "16", "21"], "29": ["08", "09", "10", "13"],
    "30": ["08", "11", "12", "13", "14", "21", "27"],
}

ROUTES = [
    {"id": "placa-muerta", "title": "La placa no da señales de vida", "summary": "Entrada, protección, bus, fuente auxiliar, rails, reset y micro.", "modules": ["30", "09", "23", "08", "22", "17", "14"]},
    {"id": "funde-fusible", "title": "Funde fusible o limita la lámpara serie", "summary": "Aísla el cortocircuito antes de sustituir componentes.", "modules": ["30", "09", "23", "08", "10", "25", "27"]},
    {"id": "arranca-se-para", "title": "Arranca, se para o se reinicia", "summary": "VCC, UVLO, carga, rizado, reset, watchdog y señales obligatorias.", "modules": ["08", "17", "22", "14", "11"]},
    {"id": "comunicacion", "title": "Error de comunicación", "summary": "Alimentaciones, cable provisional, interfaz, forma de onda, ruido y protocolo.", "modules": ["11", "09", "18", "14", "30"]},
    {"id": "sobrecorriente", "title": "Sobrecorriente real o falsa", "summary": "Compara corriente real, cadena de medida, comparador e inverter.", "modules": ["13", "15", "25", "26", "27", "12"]},
    {"id": "salida-no-actua", "title": "Relé, válvula o carga no actúa", "summary": "Orden del micro, driver, alimentación, protección y estado de la carga.", "modules": ["30", "16", "24", "21", "20", "23"]},
    {"id": "inverter", "title": "El compresor inverter no arranca", "summary": "Bus, PFC, medida de corriente, driver, IPM, compresor y firmware.", "modules": ["10", "12", "13", "25", "26", "27", "14"]},
    {"id": "intermitente", "title": "Avería intermitente, ruido o fallos fantasma", "summary": "Rizado, desacoplo, EMC, soldaduras, temperatura y registro temporal.", "modules": ["30", "17", "09", "08", "11", "14", "29"]},
]

TOOLS = [
    {"href": "componentes.html", "title": "Buscar una referencia", "summary": "Consulta encapsulado, fabricante, parámetros y documentación disponible."},
    {"href": "comparador.html", "title": "Comparar componentes", "summary": "Contrasta dos referencias sin asumir que son equivalentes."},
    {"href": "calculadoras.html", "title": "Abrir calculadoras", "summary": "Divisores, shunts, bus DC, RC, LED, zéner, 555 y otras ayudas."},
    {"href": "simbolos.html", "title": "Consultar símbolos y esquemas", "summary": "Reconoce símbolos y sigue una señal dentro del circuito."},
    {"href": "averias.html", "title": "Ver averías reales", "summary": "Busca experiencias confirmadas mediante la referencia de la placa."},
]

EDITORIAL_NOTES: dict[str, list[str]] = {
    "08": ["No energices una fuente sin identificar antes el dominio HOT/COLD y descargar el bus.", "Una tensión correcta en vacío no demuestra que la fuente entregue potencia bajo carga."],
    "09": ["No sustituyas condensadores X/Y por condensadores de propósito general: la clase de seguridad forma parte del componente."],
    "10": ["El PFC acondiciona la entrada y eleva/regula el bus; no genera por sí mismo las fases U-V-W del compresor."],
    "11": ["No existe una tensión de comunicación universal. La prueba decisiva del cable es sustituir temporalmente todo el recorrido por uno nuevo conocido."],
    "12": ["Toda medida necesita una referencia. En un osciloscopio de banco la pinza de masa suele estar unida a tierra de protección."],
    "13": ["Contrasta la corriente que mide la placa con una medida independiente antes de aceptar una sobrecorriente como real."],
    "14": ["Actividad en PWM, UART, I²C o SPI demuestra ejecución de código, pero no garantiza que todo el firmware sea correcto."],
    "15": ["Open-collector necesita pull-up y su estado depende también de referencia, alimentación y rango de modo común."],
    "16": ["Los 500 mA se especifican por canal y bajo condiciones concretas; la disipación total del encapsulado limita varios canales activos."],
    "17": ["Retirar un desacoplo puede servir como prueba temporal solo si hay redundancia demostrada; no es una reparación definitiva."],
    "18": ["Un LED interno que conduce no garantiza CTR suficiente ni velocidad adecuada en funcionamiento real."],
    "19": ["Comprueba alimentación, referencia y rango de modo común antes de culpar al operacional."],
    "20": ["Un optotriac de cruce por cero no sirve para cualquier control por ángulo de fase. Verifica la función y la carga."],
    "21": ["Mide la tensión entre los dos terminales de la bobina: 12 V respecto a masa en ambos lados equivalen a 0 V sobre ella."],
    "22": ["Al inyectar tensión en un rail, aísla el regulador si puede retroalimentarse y limita la corriente desde el primer instante."],
    "23": ["La prueba en modo diodo no revela siempre fugas a alta tensión ni el comportamiento de recuperación en conmutación."],
    "24": ["El encapsulado y el marcaje corto no garantizan el pinout; confirma la referencia exacta y la topología de la placa."],
    "25": ["Superar una prueba estática no demuestra SOA, velocidad, pérdidas ni comportamiento térmico durante la conmutación."],
    "26": ["HO y VS flotan con la fase. Usa medida diferencial o instrumento aislado con categoría y tensión adecuadas."],
    "27": ["No condenes el IPM solo por un código: valida alimentación, entradas, FAULT, shunt, montaje térmico y compresor."],
    "28": ["Además del valor óhmico, conserva potencia, tensión de trabajo, tolerancia, TCR y capacidad de pulso."],
    "29": ["La continuidad de un bobinado no descarta espiras en corto ni saturación bajo corriente."],
    "30": ["Si no puedes identificar la referencia, el dominio eléctrico o el procedimiento seguro, detén la prueba y busca documentación."],
}

PRIMARY_ADDITIONS = [
    {"title": "Tektronix: medidas flotantes y protección del operador", "url": "https://www.tek.com/en/documents/technical-brief/floating-oscilloscope-measurements-and-operator-protection", "scope": ["08", "10", "11", "12", "13", "20", "25", "26", "27", "30"]},
    {"title": "Texas Instruments: ULN2003A", "url": "https://www.ti.com/product/ULN2003A", "scope": ["16"]},
    {"title": "Texas Instruments: LM393", "url": "https://www.ti.com/product/LM393", "scope": ["15"]},
]


def normalize(value: str) -> str:
    value = "".join(c for c in unicodedata.normalize("NFD", value) if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value)).strip()


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalize(value)).strip("-")[:80] or "apartado"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")


def iter_blocks(document: DocumentObject) -> Iterator[Paragraph | Table]:
    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield Table(child, document)


def heading_level(paragraph: Paragraph) -> int | None:
    style = (paragraph.style.name if paragraph.style else "") or ""
    match = re.search(r"(?:Heading|Título|Titulo)\s*([1-6])", style, re.I)
    if match:
        return int(match.group(1))
    p_pr = paragraph._p.pPr
    outline = p_pr.find(qn("w:outlineLvl")) if p_pr is not None else None
    return int(outline.get(qn("w:val"))) + 1 if outline is not None else None


def paragraph_kind(paragraph: Paragraph, text: str) -> str | None:
    style = normalize((paragraph.style.name if paragraph.style else "") or "")
    key = normalize(text)
    if any(word in key[:90] for word in ("peligro", "seguridad", "advertencia", "precaucion", "atencion")) or "warning" in style:
        return "warning"
    if any(key.startswith(word) for word in ("regla de oro", "importante", "idea central", "criterio de sustitucion")):
        return "important"
    if any(key.startswith(word) for word in ("truco de taller", "nota", "recuerda", "punto clave")):
        return "tip"
    return None


def is_list(paragraph: Paragraph) -> bool:
    p_pr = paragraph._p.pPr
    return bool(p_pr is not None and p_pr.find(qn("w:numPr")) is not None)


def table_payload(table: Table) -> dict[str, Any] | None:
    rows = [[re.sub(r"\s+", " ", cell.text).strip() for cell in row.cells] for row in table.rows]
    rows = [row for row in rows if any(row)]
    if not rows:
        return None
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    return {"type": "table", "headers": rows[0], "rows": rows[1:]}


def extract_figures(paragraph: Paragraph, document: DocumentObject, destination: Path, module_id: str, counter: list[int]) -> list[dict[str, Any]]:
    figures = []
    for blip in paragraph._p.xpath(".//a:blip"):
        rel_id = blip.get(qn("r:embed"))
        if not rel_id or rel_id not in document.part.related_parts:
            continue
        part = document.part.related_parts[rel_id]
        blob = part.blob
        digest = hashlib.sha1(blob).hexdigest()[:10]
        counter[0] += 1
        filename = f"{counter[0]:03d}-{digest}.png"
        target = destination / f"module-{module_id}" / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(blob)
        figures.append({"type": "figure", "src": f"assets/electronics/module-{module_id}/{filename}", "alt": "Diagrama técnico", "caption": ""})
    return figures


def extract_module(meta: dict[str, Any], source: Path, project: Path) -> dict[str, Any]:
    module_id = f"{int(meta['numero']):02d}"
    details = MODULE_DETAILS[module_id]
    docx = source / meta["docx"]
    document = Document(docx)
    chapters: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    used_ids: dict[str, int] = {}
    skip_toc = False
    started = False
    list_items: list[str] = []
    figure_counter = [0]
    assets = project / "assets" / "electronics"

    def destination() -> list[dict[str, Any]]:
        return current["blocks"] if current is not None else []

    def flush_list() -> None:
        nonlocal list_items
        if list_items and current is not None:
            current["blocks"].append({"type": "list", "items": list_items})
        list_items = []

    for block in iter_blocks(document):
        if isinstance(block, Table):
            if not started or skip_toc or current is None:
                continue
            flush_list()
            payload = table_payload(block)
            if payload:
                current["blocks"].append(payload)
            continue

        text = re.sub(r"\s+", " ", block.text).strip()
        level = heading_level(block)
        if level and normalize(text).startswith(("indice", "table of contents")):
            skip_toc = True
            continue
        if level and skip_toc:
            skip_toc = False
            started = True
        if skip_toc:
            continue
        if level and text:
            flush_list()
            clean = re.sub(r"\s*(?:Back to TOC|Volver al índice|Índice)\s*$", "", text, flags=re.I).strip()
            if level == 1:
                base = slugify(clean)
                used_ids[base] = used_ids.get(base, 0) + 1
                suffix = "" if used_ids[base] == 1 else f"-{used_ids[base]}"
                current = {"id": f"e{module_id}-{base}{suffix}", "title": clean, "blocks": []}
                chapters.append(current)
            elif current is not None:
                current["blocks"].append({"type": "subheading", "level": level, "text": clean})
            continue
        if not started or current is None:
            continue

        figures = extract_figures(block, document, assets, module_id, figure_counter)
        if figures:
            flush_list()
            current["blocks"].extend(figures)
        if not text:
            continue
        style = normalize((block.style.name if block.style else "") or "")
        if "caption" in style or "epigrafe" in style or re.match(r"^(Figura|Fig\.)\s*\d+", text, re.I):
            flush_list()
            if current["blocks"] and current["blocks"][-1].get("type") == "figure":
                current["blocks"][-1]["caption"] = text
                current["blocks"][-1]["alt"] = re.sub(r"^Figura\s*\d+\.?\s*", "", text, flags=re.I)
            else:
                current["blocks"].append({"type": "caption", "text": text})
            continue
        if is_list(block):
            list_items.append(text)
            continue
        flush_list()
        kind = paragraph_kind(block, text)
        current["blocks"].append({"type": "callout", "kind": kind, "text": text} if kind else {"type": "paragraph", "text": text})
    flush_list()

    for chapter in chapters:
        parts = [chapter["title"]]
        for block in chapter["blocks"]:
            if block["type"] == "table":
                parts.extend(block["headers"])
                parts.extend(cell for row in block["rows"] for cell in row)
            elif block["type"] == "list":
                parts.extend(block["items"])
            else:
                parts.append(str(block.get("text") or block.get("caption") or block.get("alt") or ""))
        chapter["search"] = normalize(" ".join(parts))
        chapter["word_count"] = len(" ".join(parts).split())

    urls = []
    for paragraph in document.paragraphs:
        for url in re.findall(r"https?://[^\s<>()]+", paragraph.text):
            url = url.rstrip(".,;)")
            if url not in urls:
                urls.append(url)
    sources = [{"title": url, "url": url} for url in urls]
    for item in PRIMARY_ADDITIONS:
        if module_id in item["scope"] and item["url"] not in urls:
            sources.append({"title": item["title"], "url": item["url"], "editorial_addition": True})

    return {
        "id": module_id,
        "title": meta["titulo"],
        "version": meta["version"],
        "pages": int(meta["paginas"]),
        "group": details["group"],
        "icon": details["icon"],
        "level": details["level"],
        "summary": details["summary"],
        "related": RELATED[module_id],
        "editorial_notes": EDITORIAL_NOTES[module_id],
        "sources": sources,
        "chapters": chapters,
        "stats": {
            "chapters": len(chapters),
            "figures": sum(block["type"] == "figure" for chapter in chapters for block in chapter["blocks"]),
            "tables": sum(block["type"] == "table" for chapter in chapters for block in chapter["blocks"]),
            "words": sum(chapter["word_count"] for chapter in chapters),
        },
    }


def build(source: Path, project: Path) -> dict[str, Any]:
    manifest = json.loads((source / "00_INTEGRACION" / "manifest_modulos.json").read_text(encoding="utf-8"))
    assets = project / "assets" / "electronics"
    if assets.exists():
        shutil.rmtree(assets)
    assets.mkdir(parents=True)
    modules = [extract_module(meta, source, project) for meta in manifest["modulos"]]
    order = {module_id: index for index, module_id in enumerate(PEDAGOGICAL_ORDER)}
    modules.sort(key=lambda module: order.get(module["id"], len(order)))
    collection = {
        "schema_version": "1.0",
        "title": "Enciclopedia práctica de electrónica de placas",
        "language": "es-ES",
        "source_date": manifest.get("fecha_paquete"),
        "notice": "Biblioteca general de reparación. El manual de servicio y el datasheet exactos prevalecen sobre cualquier orientación general.",
        "safety": "Hay tensiones letales y nodos flotantes. Descarga condensadores, identifica HOT/COLD y utiliza instrumentos, sondas y categoría de medida adecuados. Nunca anules la tierra de protección del osciloscopio.",
        "groups": GROUPS,
        "routes": ROUTES,
        "tools": TOOLS,
        "stats": {
            "modules": len(modules),
            "pages": sum(module["pages"] for module in modules),
            "chapters": sum(module["stats"]["chapters"] for module in modules),
            "figures": sum(module["stats"]["figures"] for module in modules),
            "tables": sum(module["stats"]["tables"] for module in modules),
            "words": sum(module["stats"]["words"] for module in modules),
        },
        "modules": modules,
    }
    write_json(project / "data" / "electronics" / "collection.json", collection)
    report = {"collection": collection["stats"], "modules": {module["id"]: module["stats"] for module in modules}}
    write_json(project / "data" / "electronics" / "build-report.json", report)
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
