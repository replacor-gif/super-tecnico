#!/usr/bin/env python3
"""Build the traceable REPLACOR connector companion manual from catalog.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "connectors" / "catalog.json"
SOURCES_PATH = ROOT / "data" / "connectors" / "sources.json"
OUTPUT_PATH = ROOT / "recursos" / "catalogo-normalizado-conectores-replacor-edicion-9.pdf"

NAVY = colors.HexColor("#0A1017")
PANEL = colors.HexColor("#111B25")
PANEL_2 = colors.HexColor("#172432")
CYAN = colors.HexColor("#00E5FF")
YELLOW = colors.HexColor("#FFE438")
GREEN = colors.HexColor("#54FF82")
PINK = colors.HexColor("#FF3FA7")
ORANGE = colors.HexColor("#FF7A00")
WHITE = colors.HexColor("#F4F8FB")
MUTED = colors.HexColor("#A6B7C4")
LINE = colors.HexColor("#314657")
RED = colors.HexColor("#FF747A")

STATUS_LABELS = {
    "reviewed": "REVISADO",
    "source_identified": "FUENTE IDENTIFICADA",
    "pending_review": "PENDIENTE",
}
STATUS_COLORS = {"reviewed": GREEN, "source_identified": YELLOW, "pending_review": RED}
CATEGORY_LABELS = {
    "network": "RED",
    "usb": "USB",
    "video": "VÍDEO",
    "audio": "AUDIO",
    "serial_industrial": "SERIE / INDUSTRIAL",
    "automotive": "AUTOMOCIÓN",
    "storage": "ALMACENAMIENTO",
    "power": "POTENCIA",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def register_fonts() -> tuple[str, str]:
    candidates = [
        (Path("C:/Windows/Fonts/arial.ttf"), Path("C:/Windows/Fonts/arialbd.ttf")),
        (Path("C:/Windows/Fonts/calibri.ttf"), Path("C:/Windows/Fonts/calibrib.ttf")),
    ]
    for regular, bold in candidates:
        if regular.is_file() and bold.is_file():
            pdfmetrics.registerFont(TTFont("Replacor", str(regular)))
            pdfmetrics.registerFont(TTFont("Replacor-Bold", str(bold)))
            return "Replacor", "Replacor-Bold"
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = register_fonts()
PAGE_W, PAGE_H = A4


def paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    safe = (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return Paragraph(safe, style)


def rich_paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    """Render markup assembled in this script after escaping catalog values."""
    return Paragraph(text, style)


def page_frame(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setStrokeColor(LINE)
    canvas.line(16 * mm, 14 * mm, PAGE_W - 16 * mm, 14 * mm)
    canvas.setFont(FONT_BOLD, 7)
    canvas.setFillColor(CYAN)
    canvas.drawString(16 * mm, 8.5 * mm, "REPLACOR CORE · CONECTORES")
    canvas.setFillColor(MUTED)
    canvas.drawRightString(PAGE_W - 16 * mm, 8.5 * mm, f"EDICIÓN 9 · {doc.page:03d}")
    canvas.restoreState()


def cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(CYAN)
    canvas.rect(0, 0, 9 * mm, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#0E3547"))
    canvas.setFont(FONT_BOLD, 58)
    canvas.drawRightString(PAGE_W - 18 * mm, PAGE_H - 38 * mm, "01 02 03")
    canvas.setFillColor(YELLOW)
    canvas.setFont(FONT_BOLD, 12)
    canvas.drawString(23 * mm, PAGE_H - 57 * mm, "REPLACOR CORE · BASE TÉCNICA NORMALIZADA")
    canvas.setFillColor(WHITE)
    canvas.setFont(FONT_BOLD, 33)
    canvas.drawString(23 * mm, PAGE_H - 83 * mm, "CONECTORES")
    canvas.setFillColor(CYAN)
    canvas.drawString(23 * mm, PAGE_H - 98 * mm, "Y PINOUTS")
    canvas.setFillColor(WHITE)
    canvas.setFont(FONT_BOLD, 20)
    canvas.drawString(23 * mm, PAGE_H - 116 * mm, "Edición 9 · Catálogo normalizado")
    canvas.setFillColor(PANEL)
    canvas.roundRect(23 * mm, PAGE_H - 180 * mm, PAGE_W - 46 * mm, 45 * mm, 5 * mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont(FONT_BOLD, 11)
    canvas.drawString(31 * mm, PAGE_H - 149 * mm, "17 fichas · 185 contactos · orientación explícita")
    canvas.setFillColor(MUTED)
    canvas.setFont(FONT, 9.5)
    canvas.drawString(31 * mm, PAGE_H - 160 * mm, "Fuente conservada, datos estructurados y revisión visible.")
    canvas.drawString(31 * mm, PAGE_H - 169 * mm, "Preparado para técnicos, ElectroIA, SINAPSYS y motores externos.")
    canvas.setFillColor(YELLOW)
    canvas.roundRect(23 * mm, 33 * mm, 75 * mm, 14 * mm, 3 * mm, fill=1, stroke=0)
    canvas.setFillColor(NAVY)
    canvas.setFont(FONT_BOLD, 9)
    canvas.drawCentredString(60.5 * mm, 38 * mm, "BETA TÉCNICA · 22/08/2026")
    canvas.setFillColor(MUTED)
    canvas.setFont(FONT, 7.5)
    canvas.drawString(23 * mm, 21 * mm, "No sustituye la documentación del fabricante ni una comprobación de la vista física.")
    canvas.restoreState()


def styles():
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("H1", parent=base["Heading1"], fontName=FONT_BOLD, fontSize=24, leading=26, textColor=WHITE, spaceAfter=8),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], fontName=FONT_BOLD, fontSize=15, leading=18, textColor=WHITE, spaceBefore=5, spaceAfter=7),
        "h3": ParagraphStyle("H3", parent=base["Heading3"], fontName=FONT_BOLD, fontSize=9, leading=11, textColor=CYAN, spaceBefore=4, spaceAfter=4),
        "body": ParagraphStyle("Body", parent=base["BodyText"], fontName=FONT, fontSize=8.6, leading=12.2, textColor=MUTED, spaceAfter=6),
        "small": ParagraphStyle("Small", parent=base["BodyText"], fontName=FONT, fontSize=6.8, leading=8.6, textColor=MUTED),
        "small_white": ParagraphStyle("SmallWhite", parent=base["BodyText"], fontName=FONT, fontSize=6.8, leading=8.6, textColor=WHITE),
        "small_bold": ParagraphStyle("SmallBold", parent=base["BodyText"], fontName=FONT_BOLD, fontSize=6.8, leading=8.6, textColor=WHITE),
        "badge": ParagraphStyle("Badge", parent=base["BodyText"], fontName=FONT_BOLD, fontSize=6.6, leading=8, textColor=NAVY, alignment=TA_CENTER),
        "toc": ParagraphStyle("Toc", parent=base["BodyText"], fontName=FONT_BOLD, fontSize=8.3, leading=11, textColor=WHITE),
        "contact": ParagraphStyle("Contact", parent=base["BodyText"], fontName=FONT_BOLD, fontSize=6.6, leading=8.2, textColor=YELLOW),
        "signal": ParagraphStyle("Signal", parent=base["BodyText"], fontName=FONT_BOLD, fontSize=6.3, leading=8.1, textColor=WHITE),
        "desc": ParagraphStyle("Desc", parent=base["BodyText"], fontName=FONT, fontSize=6.3, leading=8.1, textColor=MUTED),
        "center": ParagraphStyle("Center", parent=base["BodyText"], fontName=FONT_BOLD, fontSize=9, leading=12, textColor=WHITE, alignment=TA_CENTER),
    }


def card_table(items, st):
    cells = []
    for label, value in items:
        cells.append([paragraph(label.upper(), st["small"]), paragraph(value, st["small_bold"])])
    table = Table(cells, colWidths=[34 * mm, 127 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("BOX", (0, 0), (-1, -1), .5, LINE),
        ("INNERGRID", (0, 0), (-1, -1), .35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def method_pages(catalog, st):
    counts = catalog["counts"]
    story = [paragraph("Qué se ha mejorado", st["h1"]), paragraph(
        "La edición 8 aportada contiene 160 páginas y una cobertura amplia. Su presentación es sólida, pero una enciclopedia visual no es todavía una base consumible por software: mezcla láminas, resúmenes, diagnóstico y pinouts; cita familias normativas sin conservar siempre edición, cláusula y vista; y su código generador depende de rutas externas. Esta edición 9 no oculta esas limitaciones: conserva el original y añade una capa estructurada, versionada y auditable.", st["body"]), Spacer(1, 3 * mm)]
    story.append(card_table([
        ("Original", "Edición 8 archivada íntegra como fuente aportada"),
        ("Núcleo actual", f"{counts['records']} fichas y {counts['contacts']} contactos normalizados"),
        ("Orientación", "Lado, perspectiva, llave y advertencia explícitos"),
        ("Calidad", "Reviewed, source_identified y pending_review son estados distintos"),
        ("Máquinas", "Contrato JSON neutral para ElectroIA, SINAPSYS y otras IAs"),
    ], st))
    story.extend([Spacer(1, 5 * mm), paragraph("Semáforo de revisión", st["h2"])])
    rows = [[paragraph("ESTADO", st["small_bold"]), paragraph("QUÉ PERMITE AFIRMAR", st["small_bold"]), paragraph("ACCIÓN", st["small_bold"])],
            [paragraph("REVISADO", st["small_bold"]), paragraph("Contacto, variante y orientación contrastados con fuente primaria exacta.", st["small"]), paragraph("Puede usarse manteniendo las advertencias.", st["small"])],
            [paragraph("FUENTE IDENTIFICADA", st["small_bold"]), paragraph("La norma u organización primaria está localizada, pero falta cerrar la tabla contacto por contacto.", st["small"]), paragraph("Útil para localizar; contrastar antes de cablear.", st["small"])],
            [paragraph("PENDIENTE", st["small_bold"]), paragraph("Hay variantes, asignaciones OEM o documentación insuficiente.", st["small"]), paragraph("No tratar como pinout universal.", st["small"])]]
    status_table = Table(rows, colWidths=[38 * mm, 78 * mm, 45 * mm], repeatRows=1)
    status_table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),PANEL_2),("TEXTCOLOR",(0,0),(-1,-1),WHITE),("BOX",(0,0),(-1,-1),.5,LINE),("INNERGRID",(0,0),(-1,-1),.35,LINE),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),("BACKGROUND",(0,1),(0,1),GREEN),("TEXTCOLOR",(0,1),(0,1),NAVY),("BACKGROUND",(0,2),(0,2),YELLOW),("TEXTCOLOR",(0,2),(0,2),NAVY),("BACKGROUND",(0,3),(0,3),RED),("TEXTCOLOR",(0,3),(0,3),NAVY)]))
    story.extend([status_table, PageBreak(), paragraph("Reglas del catálogo", st["h1"]), paragraph("Estas reglas son obligatorias tanto para la web como para cualquier IA que consulte la base.", st["body"])])
    rules = [
        ("01", "Identificar antes de responder", "Si el nombre, la forma o el número de contactos no separan dos variantes, se devuelven varios candidatos."),
        ("02", "La vista forma parte del dato", "Mating face, wiring side, plug y receptacle nunca se intercambian sin una transformación explícita."),
        ("03", "Conservar incertidumbre", "Source identified no se presenta como reviewed; pending review no se completa por intuición."),
        ("04", "Fuentes como trazabilidad", "El PDF aportado se conserva y cada ficha enlaza sus páginas y registros de fuente."),
        ("05", "Una base para varios motores", "ElectroIA puede usar contactos y conectores; otros motores podrán identificar cableado, cuadros, automatización o diagnóstico."),
        ("06", "Crecimiento incremental", "Los próximos documentos se importan con el mismo esquema y no obligan a rediseñar la aplicación."),
    ]
    rule_rows = []
    for number, title, text in rules:
        rule_rows.append([paragraph(number, st["center"]), rich_paragraph(f"<b>{escape(title)}</b><br/>{escape(text)}", st["body"])])
    rule_table = Table(rule_rows, colWidths=[20 * mm, 141 * mm])
    rule_table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),PANEL),("BOX",(0,0),(-1,-1),.5,LINE),("INNERGRID",(0,0),(-1,-1),.35,LINE),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("BACKGROUND",(0,0),(0,-1),colors.HexColor("#123747")),("TEXTCOLOR",(0,0),(-1,-1),WHITE),("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8)]))
    story.extend([rule_table, Spacer(1, 5 * mm), paragraph("Próxima revisión", st["h2"]), paragraph("La prioridad es elevar las fichas de uso más frecuente a reviewed con edición y ubicación exactas de sus fuentes primarias. Los registros de automoción, potencia y variantes OEM permanecen deliberadamente más conservadores.", st["body"]), PageBreak()])
    return story


def index_pages(records, st):
    story = [paragraph("Índice de fichas normalizadas", st["h1"]), paragraph("Cada ficha comienza por la identificación y la vista. Los contactos aparecen después; variantes, seguridad y procedencia cierran el registro.", st["body"]), Spacer(1, 2 * mm)]
    rows = [[paragraph("N.º", st["small_bold"]), paragraph("CONECTOR", st["small_bold"]), paragraph("FAMILIA", st["small_bold"]), paragraph("ESTADO", st["small_bold"])]]
    for number, record in enumerate(records, start=1):
        rows.append([
            paragraph(f"{number:02d}", st["contact"]),
            paragraph(record["canonical_name"], st["small_white"]),
            paragraph(CATEGORY_LABELS.get(record["category"], record["category"]), st["small"]),
            paragraph(STATUS_LABELS[record["review"]["status"]], st["small"]),
        ])
    table = Table(rows, colWidths=[14 * mm, 78 * mm, 36 * mm, 33 * mm], repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),PANEL_2),("BOX",(0,0),(-1,-1),.5,LINE),("INNERGRID",(0,0),(-1,-1),.3,LINE),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
    story.extend([table, PageBreak()])
    return story


def connector_page(record, number, source_map, st):
    status = record["review"]["status"]
    accent = STATUS_COLORS[status]
    story = [
        Table([[paragraph(f"FICHA {number:02d} · {CATEGORY_LABELS.get(record['category'], record['category'])}", st["badge"]), paragraph(STATUS_LABELS[status], st["badge"])]], colWidths=[112 * mm, 49 * mm], style=TableStyle([("BACKGROUND",(0,0),(0,0),CYAN),("BACKGROUND",(1,0),(1,0),accent),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)])),
        Spacer(1, 3 * mm),
        paragraph(record["canonical_name"], st["h1"]),
        paragraph(" · ".join(record.get("aliases") or []), st["body"]),
        card_table([
            ("Interfaz", record["interface"]),
            ("Formato", record["form_factor"]),
            ("Vista", record["view"]["orientation_note"]),
        ], st),
        Spacer(1, 3 * mm),
    ]
    contact_rows = [[paragraph("CONTACTO", st["small_bold"]), paragraph("SEÑAL", st["small_bold"]), paragraph("FUNCIÓN", st["small_bold"])]]
    for contact in record["contacts"]:
        contact_rows.append([paragraph(contact["id"], st["contact"]), paragraph(contact["signal"], st["signal"]), paragraph(contact["description"], st["desc"])])
    contacts = Table(contact_rows, colWidths=[22 * mm, 48 * mm, 91 * mm], repeatRows=1, hAlign="LEFT")
    contacts.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),PANEL_2),("BOX",(0,0),(-1,-1),.5,LINE),("INNERGRID",(0,0),(-1,-1),.28,LINE),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),3.5),("BOTTOMPADDING",(0,0),(-1,-1),3.5)]))
    story.extend([contacts, Spacer(1, 3 * mm)])
    variants = "<br/>".join(f"• {escape(item)}" for item in record.get("variants") or ["Sin variantes documentadas."])
    warnings = "<br/>".join(f"• {escape(item)}" for item in record.get("safety_notes") or ["Sin advertencias adicionales."])
    notes = Table([[paragraph("VARIANTES", st["h3"]), paragraph("SEGURIDAD", st["h3"])], [rich_paragraph(variants, st["small"]), rich_paragraph(warnings, st["small"]) ]], colWidths=[80.5 * mm, 80.5 * mm])
    notes.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),PANEL),("BOX",(0,0),(-1,-1),.5,LINE),("INNERGRID",(0,0),(-1,-1),.35,LINE),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
    story.extend([notes, Spacer(1, 3 * mm)])
    source_titles = [source_map[source_id]["title"] for source_id in record["source_ids"] if source_id in source_map]
    trace = f"Edición 8, páginas {', '.join(map(str, record['source_pdf']['pages']))}. Fuentes: {'; '.join(source_titles)}."
    story.append(KeepTogether([paragraph("TRAZABILIDAD Y LÍMITE", st["h3"]), paragraph(trace, st["small"]), paragraph(record["review"]["scope"], st["small"])]))
    story.append(PageBreak())
    return story


def final_page(catalog, st):
    return [
        paragraph("Una base que puede crecer sin romperse", st["h1"]),
        paragraph("Cada nuevo PDF, manual o tabla puede entrar por el mismo proceso: conservar el original, extraer registros, separar variantes, declarar la vista, identificar fuentes y publicar el estado real de revisión. Así la base gana valor para el técnico y, al mismo tiempo, resulta barata y segura de consultar para una IA.", st["body"]),
        Spacer(1, 5 * mm),
        card_table([
            ("Ahora", "Buscador móvil + 17 fichas JSON + edición 9 trazable"),
            ("Siguiente", "Verificación fuente por fuente y nuevas familias aportadas"),
            ("ElectroIA", "Conectores y terminales reutilizables en documentos electrotécnicos"),
            ("SINAPSYS", "Orquestación futura entre catálogo, normativa, motores y proyectos"),
            ("REPLACOR", "Marca progresiva del entorno técnico, sin migraciones bruscas"),
        ], st),
        Spacer(1, 10 * mm),
        paragraph("REGLA FINAL", st["h3"]),
        paragraph("Una base técnica profesional no es la que aparenta saberlo todo; es la que sabe exactamente qué está comprobado, qué variante describe y qué dato falta.", ParagraphStyle("quote", parent=st["h1"], fontSize=18, leading=23, textColor=YELLOW, alignment=TA_LEFT)),
        Spacer(1, 18 * mm),
        paragraph(f"Catálogo {catalog['catalog_version']} · {catalog['updated_at']} · app.replacor.com/super-tecnico/conectores.html", st["body"]),
    ]


def build(output_path: Path):
    catalog = load_json(CATALOG_PATH)
    sources = load_json(SOURCES_PATH)
    source_map = {source["id"]: source for source in sources["sources"]}
    st = styles()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4, rightMargin=24 * mm, leftMargin=24 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
        title="REPLACOR Core - Conectores y pinouts - Edición 9",
        author="REPLACOR · Super Técnico",
        subject="Catálogo normalizado y trazable de conectores",
        creator="REPLACOR Core",
    )
    story = [Spacer(1, 1), PageBreak()]
    story.extend(method_pages(catalog, st))
    story.extend(index_pages(catalog["records"], st))
    for number, record in enumerate(catalog["records"], start=1):
        story.extend(connector_page(record, number, source_map, st))
    story.extend(final_page(catalog, st))
    doc.build(story, onFirstPage=cover, onLaterPages=page_frame)


if __name__ == "__main__":
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else OUTPUT_PATH
    build(target)
    print(target)
