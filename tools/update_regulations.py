#!/usr/bin/env python3
"""Download official regulations and rebuild the browser search indexes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / "data" / "regulations" / "sources.json"
CATALOG_PATH = ROOT / "data" / "regulations" / "catalog.json"
INDEX_DIR = ROOT / "data" / "regulations" / "index"
USER_AGENT = "SuperTecnico-Regulations-Updater/1.0 (+https://app.replacor.com/super-tecnico/)"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_sha256(parts: list[str]) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def normalize_search(text: str) -> str:
    value = unicodedata.normalize("NFKD", text.casefold())
    value = "".join(character for character in value if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def download_pdf(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp_path = Path(temp.name)
    try:
        curl = shutil.which("curl") or shutil.which("curl.exe")
        if curl:
            subprocess.run(
                [curl, "--fail", "--location", "--silent", "--show-error", "--user-agent", USER_AGENT, "--output", str(temp_path), url],
                check=True,
                timeout=120,
            )
        else:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=90) as response, temp_path.open("wb") as output:
                shutil.copyfileobj(response, output)
        if temp_path.stat().st_size < 10_000 or temp_path.read_bytes()[:4] != b"%PDF":
            raise RuntimeError(f"La descarga no parece un PDF válido: {url}")
        PdfReader(str(temp_path), strict=False)
        temp_path.replace(destination)
    finally:
        temp_path.unlink(missing_ok=True)


def clean_page_text(text: str) -> str:
    text = text.replace("\x00", " ").replace("\u00ad", "")
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def page_chunks(text: str, target: int = 950, maximum: int = 1500) -> list[str]:
    paragraphs = [re.sub(r"\s+", " ", part).strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        paragraphs = [re.sub(r"\s+", " ", text).strip()] if text.strip() else []
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        pieces = [paragraph[index:index + maximum] for index in range(0, len(paragraph), maximum)]
        for piece in pieces:
            if current and len(current) + len(piece) + 1 > maximum:
                chunks.append(current)
                current = ""
            current = f"{current} {piece}".strip()
            if len(current) >= target:
                chunks.append(current)
                current = ""
    if current:
        chunks.append(current)
    return chunks


REGULATION_FOOTER = re.compile(
    r"^(?:BOLET[IÍ]N OFICIAL DEL ESTADO|LEGISLACI[OÓ]N CONSOLIDADA|P[aá]gina\s+\d+)$",
    re.IGNORECASE,
)
INSTRUCTION_HEADING = re.compile(
    r"^(?P<id>(?:ITC(?:-[A-Z]{2,6})?|IF|IT|DB[-\s]?(?:HS|HE|SI|SUA|HR))[-\s]?\d{1,3}(?:\.\d+)*)\s*[.:-]?\s*(?P<title>.*)$",
    re.IGNORECASE,
)
ARTICLE_HEADING = re.compile(
    r"^(?P<label>Art[ií]culo\s+(?:[uú]nico|\d+(?:\s*[a-z])?(?:\.\d+)*))(?:[.:-]\s*(?P<title>.*))?$",
    re.IGNORECASE,
)
NAMED_HEADING = re.compile(
    r"^(?P<label>(?:CAP[IÍ]TULO|T[IÍ]TULO|SECCI[OÓ]N|APARTADO|ANEJO|ANEXO|AP[EÉ]NDICE)\s+[A-Z0-9IVXLC.-]+)(?:[.:-]\s*(?P<title>.*))?$",
    re.IGNORECASE,
)
TABLE_HEADING = re.compile(
    r"^(?P<label>Tabla\s+[A-Z0-9.-]+)(?:[.:-]\s*(?P<title>.*))?$",
    re.IGNORECASE,
)
NUMBERED_HEADING = re.compile(
    r"^(?P<id>\d+(?:\.\d+){0,5})\.?\s+(?P<title>.{2,180})$"
)


def index_lines(text: str) -> list[str]:
    """Keep source order while removing repeated BOE page furniture."""
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        line = re.sub(r"BOLET[IÍ]N OFICIAL DEL ESTADO\s*$", "", line, flags=re.IGNORECASE).strip()
        line = re.sub(r"LEGISLACI[OÓ]N CONSOLIDADA\s+P[aá]gina\s+\d+\s*$", "", line, flags=re.IGNORECASE).strip()
        if not line or REGULATION_FOOTER.match(line):
            continue
        lines.append(line)
    return lines


def heading_record(line: str) -> dict | None:
    """Recognise conservative headings shared by BOE regulations and CTE documents."""
    if len(line) > 220:
        return None
    match = INSTRUCTION_HEADING.match(line)
    if match:
        identifier = re.sub(r"\s+", "-", match.group("id").upper()).replace("--", "-")
        return {"kind": "instruction", "id": identifier, "title": (match.group("title") or "").strip(), "label": line}
    match = ARTICLE_HEADING.match(line)
    if match:
        return {"kind": "article", "id": match.group("label"), "title": (match.group("title") or "").strip(), "label": line}
    match = NAMED_HEADING.match(line)
    if match:
        return {"kind": "named_section", "id": match.group("label"), "title": (match.group("title") or "").strip(), "label": line}
    match = TABLE_HEADING.match(line)
    if match:
        return {"kind": "table", "id": match.group("label"), "title": (match.group("title") or "").strip(), "label": line}
    match = NUMBERED_HEADING.match(line)
    if match:
        title = match.group("title").strip()
        if len(title.split()) <= 24:
            return {"kind": "section", "id": match.group("id"), "title": title, "label": line}
    return None


def heading_key(heading: dict) -> str:
    return normalize_search(f"{heading.get('id', '')} {heading.get('title', '')}")


def looks_like_toc_page(lines: list[str]) -> bool:
    headings = [heading_record(line) for line in lines]
    headings = [heading for heading in headings if heading]
    instruction_count = sum(1 for heading in headings if heading["kind"] == "instruction")
    dotted_entries = sum(1 for line in lines if re.search(r"\.{4,}\s*\d+\s*$", line))
    return instruction_count >= 3 or dotted_entries >= 3


def looks_uppercase_title(value: str) -> bool:
    letters = [character for character in value if character.isalpha()]
    return len(letters) >= 6 and sum(1 for character in letters if character.isupper()) / len(letters) >= 0.72


def confirmed_instruction_heading(lines: list[str], position: int, heading: dict) -> bool:
    title = re.sub(r"[.·\s]+\d*\s*$", "", heading.get("title", "")).strip(" .:-")
    if title and looks_uppercase_title(title):
        return True
    following = " ".join(lines[position + 1:position + 3])
    return looks_uppercase_title(following)


def enrich_instruction_heading(lines: list[str], position: int, heading: dict) -> dict:
    if heading.get("title"):
        return heading
    title_lines: list[str] = []
    for candidate in lines[position + 1:position + 3]:
        if heading_record(candidate) or not looks_uppercase_title(candidate):
            break
        title_lines.append(candidate.strip(" ."))
    if title_lines:
        heading = {**heading, "title": " ".join(title_lines)}
        heading["label"] = f"{heading['id']} {heading['title']}"
    return heading


def context_breadcrumb(context: dict, local_headings: list[dict]) -> str:
    parts: list[str] = []
    instruction = context.get("instruction")
    if instruction:
        parts.append(instruction["id"])
    persistent = [heading for heading in local_headings if heading["kind"] in {"article", "named_section", "section"}]
    heading = persistent[-1] if persistent else context.get("section") or context.get("article")
    if heading:
        label = " ".join(part for part in [heading.get("id", ""), heading.get("title", "")] if part).strip()
        if label and normalize_search(label) not in {normalize_search(part) for part in parts}:
            parts.append(label)
    table = next((heading for heading in reversed(local_headings) if heading["kind"] == "table"), None)
    if table:
        label = " ".join(part for part in [table.get("id", ""), table.get("title", "")] if part).strip()
        if label:
            parts.append(label)
    return " › ".join(parts)


def structured_page_records(document_id: str, page_number: int, text: str, context: dict, target: int = 1150, maximum: int = 1750) -> list[dict]:
    """Split a page near headings and inherit its regulation hierarchy across pages."""
    lines = index_lines(text)
    if looks_like_toc_page(lines):
        page_text = " ".join(lines).strip()
        page_headings = [heading for line in lines if (heading := heading_record(line))]
        records = []
        for chunk_number, piece in enumerate(page_chunks(page_text, target=target, maximum=maximum), start=1):
            records.append({
                "id": f"{document_id}-p{page_number:04d}-{chunk_number:02d}",
                "document_id": document_id,
                "page": page_number,
                "text": piece,
                "search": normalize_search(piece),
                "search_context": normalize_search(" ".join(heading["label"] for heading in page_headings)),
                "record_type": "index",
                "breadcrumb": "",
                "instruction_id": "",
                "section_id": "",
                "locators": list(dict.fromkeys(heading["label"] for heading in page_headings if heading["kind"] != "instruction")),
            })
        return records
    records: list[dict] = []
    segment_lines: list[str] = []
    segment_headings: list[dict] = []
    segment_is_index = bool(context.get("in_index"))

    def flush() -> None:
        nonlocal segment_lines, segment_headings, segment_is_index
        content = " ".join(segment_lines).strip()
        if not content:
            segment_lines = []
            segment_headings = []
            return
        pieces = page_chunks(content, target=target, maximum=maximum)
        breadcrumb = "" if segment_is_index else context_breadcrumb(context, segment_headings)
        locators = list(dict.fromkeys(heading["label"] for heading in segment_headings if heading["kind"] != "instruction"))
        kinds = {heading["kind"] for heading in segment_headings}
        if segment_is_index:
            record_type = "index"
        elif "table" in kinds:
            record_type = "table"
        elif len(content) < 220 and kinds:
            record_type = "heading"
        else:
            record_type = "body"
        for piece in pieces:
            records.append({
                "document_id": document_id,
                "page": page_number,
                "text": piece,
                "search": normalize_search(piece),
                "search_context": normalize_search(" ".join([breadcrumb, (context.get("instruction") or {}).get("title", ""), *(heading["label"] for heading in segment_headings)])),
                "record_type": record_type,
                "breadcrumb": breadcrumb,
                "instruction_id": (context.get("instruction") or {}).get("id", ""),
                "section_id": (context.get("section") or context.get("article") or {}).get("id", ""),
                "locators": locators,
            })
        segment_lines = []
        segment_headings = []

    for line_position, line in enumerate(lines):
        heading = heading_record(line)
        if heading and heading["kind"] == "instruction" and not confirmed_instruction_heading(lines, line_position, heading):
            heading = None
        elif heading and heading["kind"] == "instruction":
            heading = enrich_instruction_heading(lines, line_position, heading)
        previous_index_state = bool(context.get("in_index"))
        if heading and heading["kind"] == "instruction":
            if segment_lines:
                flush()
            context["instruction"] = heading
            context["article"] = None
            context["section"] = None
            context["in_index"] = False
            context["index_headings"] = set()
        elif heading and heading["kind"] == "section" and heading["id"] == "0" and normalize_search(heading["title"]) == "indice":
            if segment_lines:
                flush()
            context["in_index"] = True
            context["index_headings"] = set()
        elif heading and context.get("in_index"):
            key = heading_key(heading)
            seen = context.setdefault("index_headings", set())
            if key and key in seen and heading["kind"] != "table":
                if segment_lines:
                    flush()
                context["in_index"] = False
            elif key:
                seen.add(key)

        if bool(context.get("in_index")) != previous_index_state and segment_lines:
            flush()

        if heading and segment_lines and (len(" ".join(segment_lines)) >= 450 or any(item["kind"] == "table" for item in segment_headings)):
            flush()

        if not segment_lines:
            segment_is_index = bool(context.get("in_index"))
        segment_lines.append(line)
        if heading:
            segment_headings.append(heading)
            if not context.get("in_index"):
                if heading["kind"] == "article":
                    context["article"] = heading
                    context["section"] = None
                elif heading["kind"] in {"named_section", "section"}:
                    context["section"] = heading
        if len(" ".join(segment_lines)) >= target:
            flush()

    flush()
    for chunk_number, record in enumerate(records, start=1):
        record["id"] = f"{document_id}-p{page_number:04d}-{chunk_number:02d}"
    return records


def build_document_index(document: dict, pdf_path: Path) -> tuple[dict, dict]:
    reader = PdfReader(str(pdf_path), strict=False)
    records: list[dict] = []
    semantic_pages: list[str] = []
    pages_with_text = 0
    structure_context: dict = {"instruction": None, "article": None, "section": None, "in_index": False, "index_headings": set()}
    for page_number, page in enumerate(reader.pages, start=1):
        text = clean_page_text(page.extract_text() or "")
        semantic_pages.append(normalize_search(text))
        if text:
            pages_with_text += 1
        records.extend(structured_page_records(document["id"], page_number, text, structure_context))
    digest = sha256(pdf_path)
    content_digest = text_sha256(semantic_pages)
    index_payload = {
        "schema_version": "1.2.0",
        "document_id": document["id"],
        "source_sha256": digest,
        "source_content_sha256": content_digest,
        "page_count": len(reader.pages),
        "records": records,
    }
    metadata = {
        **document,
        "sha256": digest,
        "content_sha256": content_digest,
        "bytes": pdf_path.stat().st_size,
        "page_count": len(reader.pages),
        "pages_with_searchable_text": pages_with_text,
        "search_records": len(records),
        "structured_search_records": sum(1 for record in records if record.get("breadcrumb")),
        "record_types": {record_type: sum(1 for record in records if record.get("record_type") == record_type) for record_type in ("body", "table", "heading", "index")},
        "index_url": f"data/regulations/index/{document['id']}.json",
    }
    return metadata, index_payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--document", action="append", help="Actualizar solo uno o varios identificadores")
    parser.add_argument("--no-download", action="store_true", help="Regenerar índices usando los PDF locales")
    args = parser.parse_args()

    source_payload = load_json(SOURCES_PATH)
    selected = set(args.document or [])
    unknown = selected - {item["id"] for item in source_payload["documents"]}
    if unknown:
        parser.error(f"Documentos desconocidos: {', '.join(sorted(unknown))}")

    previous_catalog = load_json(CATALOG_PATH) if CATALOG_PATH.exists() else {"documents": []}
    previous = {item["id"]: item for item in previous_catalog.get("documents", [])}
    catalog_documents: list[dict] = []
    changes: list[dict] = []

    for document in source_payload["documents"]:
        pdf_path = ROOT / document["local_pdf"]
        should_process = not selected or document["id"] in selected
        old_document = previous.get(document["id"], {})
        existing_index = INDEX_DIR / f"{document['id']}.json"
        if selected and not should_process and old_document and existing_index.is_file():
            catalog_documents.append(old_document)
            changes.append({
                "id": document["id"],
                "short_title": document["short_title"],
                "official_page_url": document["official_page_url"],
                "new_document": False,
                "changed": False,
                "source_file_changed": False,
                "content_changed": False,
                "review_required": False,
                "previous_sha256": old_document.get("sha256"),
                "sha256": old_document.get("sha256"),
                "previous_content_sha256": old_document.get("content_sha256"),
                "content_sha256": old_document.get("content_sha256"),
                "affected_tools": document.get("related_tools", []),
            })
            continue
        if should_process and not args.no_download:
            print(f"Descargando {document['short_title']}...", flush=True)
            download_pdf(document["pdf_url"], pdf_path)
        if not pdf_path.is_file():
            raise RuntimeError(f"Falta {pdf_path}. Ejecuta sin --no-download.")

        metadata, index_payload = build_document_index(document, pdf_path)
        if should_process or not (INDEX_DIR / f"{document['id']}.json").exists():
            write_json(INDEX_DIR / f"{document['id']}.json", index_payload)
        old_hash = old_document.get("sha256")
        old_content_hash = old_document.get("content_sha256")
        source_file_changed = bool(old_hash and old_hash != metadata["sha256"])
        content_changed = bool(old_content_hash and old_content_hash != metadata["content_sha256"])
        changes.append({
            "id": document["id"],
            "short_title": document["short_title"],
            "official_page_url": document["official_page_url"],
            "new_document": not bool(old_document),
            "changed": source_file_changed or content_changed,
            "source_file_changed": source_file_changed,
            "content_changed": content_changed,
            "review_required": content_changed,
            "previous_sha256": old_hash,
            "sha256": metadata["sha256"],
            "previous_content_sha256": old_content_hash,
            "content_sha256": metadata["content_sha256"],
            "affected_tools": document.get("related_tools", []),
        })
        catalog_documents.append(metadata)

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    catalog = {
        "schema_version": "1.2.0",
        "generated_at_utc": generated_at,
        "jurisdiction": source_payload["jurisdiction"],
        "verified_at": source_payload["verified_at"],
        "notice": source_payload["notice"],
        "documents": catalog_documents,
        "referenced_not_stored": source_payload.get("referenced_not_stored", []),
    }
    write_json(CATALOG_PATH, catalog)
    write_json(ROOT / "data" / "regulations" / "update-report.json", {
        "generated_at_utc": generated_at,
        "documents": changes,
        "manual_rule_review_required_when_changed": True,
        "publication_policy": "Official source files and indexes may be refreshed automatically. Extracted engineering rules remain blocked until a human review is recorded.",
    })
    print(json.dumps({"documents": len(catalog_documents), "changes": changes}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
