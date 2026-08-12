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


def build_document_index(document: dict, pdf_path: Path) -> tuple[dict, dict]:
    reader = PdfReader(str(pdf_path), strict=False)
    records: list[dict] = []
    semantic_pages: list[str] = []
    pages_with_text = 0
    for page_number, page in enumerate(reader.pages, start=1):
        text = clean_page_text(page.extract_text() or "")
        semantic_pages.append(normalize_search(text))
        if text:
            pages_with_text += 1
        for chunk_number, chunk in enumerate(page_chunks(text), start=1):
            records.append({
                "id": f"{document['id']}-p{page_number:04d}-{chunk_number:02d}",
                "document_id": document["id"],
                "page": page_number,
                "text": chunk,
                "search": normalize_search(chunk),
            })
    digest = sha256(pdf_path)
    content_digest = text_sha256(semantic_pages)
    index_payload = {
        "schema_version": "1.1.0",
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
        if should_process and not args.no_download:
            print(f"Descargando {document['short_title']}...", flush=True)
            download_pdf(document["pdf_url"], pdf_path)
        if not pdf_path.is_file():
            raise RuntimeError(f"Falta {pdf_path}. Ejecuta sin --no-download.")

        metadata, index_payload = build_document_index(document, pdf_path)
        if should_process or not (INDEX_DIR / f"{document['id']}.json").exists():
            write_json(INDEX_DIR / f"{document['id']}.json", index_payload)
        old_document = previous.get(document["id"], {})
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
        "schema_version": "1.1.0",
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
