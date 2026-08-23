#!/usr/bin/env python3
"""Audit public structure, local references, copy freshness and text integrity."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data" / "core" / "app-quality-audit.json"
PRIVATE_PAGES = {"analitica-privada.html", "bitacora-privada.html", "moderacion.html"}
SKIP_SCHEMES = {"http", "https", "mailto", "tel", "data", "javascript", "blob"}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.refs: list[tuple[str, str]] = []
        self.images_without_alt = 0
        self.external_blank_without_rel: list[str] = []
        self.empty_interactive: list[str] = []
        self._interactive: list[dict] = []
        self._headings: list[dict] = []
        self.empty_headings = 0
        self._template_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "template":
            self._template_depth += 1
        if values.get("id"):
            self.ids.append(values["id"])
        for attribute in ("href", "src"):
            if values.get(attribute):
                self.refs.append((attribute, values[attribute]))
        if tag == "img" and "alt" not in values:
            self.images_without_alt += 1
        if tag == "a" and values.get("target") == "_blank":
            rel = set(values.get("rel", "").lower().split())
            if "noopener" not in rel:
                self.external_blank_without_rel.append(values.get("href", ""))
        if tag in {"a", "button"}:
            self._interactive.append({"tag": tag, "text": "", "label": values.get("aria-label", ""), "title": values.get("title", ""), "template": self._template_depth > 0})
        if re.fullmatch(r"h[1-6]", tag):
            self._headings.append({"tag": tag, "text": "", "id": values.get("id", ""), "template": self._template_depth > 0})

    def handle_data(self, data: str) -> None:
        if self._interactive:
            self._interactive[-1]["text"] += data
        if self._headings:
            self._headings[-1]["text"] += data

    def handle_endtag(self, tag: str) -> None:
        if tag in {"a", "button"} and self._interactive:
            item = self._interactive.pop()
            if not item["template"] and not (item["text"].strip() or item["label"].strip() or item["title"].strip()):
                self.empty_interactive.append(tag)
        if re.fullmatch(r"h[1-6]", tag) and self._headings:
            item = self._headings.pop()
            if not item["template"] and not item["id"] and not item["text"].strip():
                self.empty_headings += 1
        if tag == "template":
            self._template_depth = max(0, self._template_depth - 1)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def local_target(page: Path, value: str) -> Path | None:
    if value.startswith("#") or value.startswith("//"):
        return None
    parsed = urlsplit(value)
    if parsed.scheme.lower() in SKIP_SCHEMES or parsed.netloc:
        return None
    clean = unquote(parsed.path)
    if not clean:
        return None
    target = (page.parent / clean).resolve()
    if clean.endswith("/"):
        target /= "index.html"
    return target


def build_report() -> tuple[dict, list[dict]]:
    findings: list[dict] = []
    pages = sorted(ROOT.glob("*.html"))
    local_refs = 0
    for page in pages:
        text = page.read_text(encoding="utf-8")
        parser = PageParser()
        parser.feed(text)
        duplicates = sorted(key for key, count in Counter(parser.ids).items() if count > 1)
        if duplicates:
            findings.append({"severity": "error", "code": "DUPLICATE_IDS", "file": page.name, "details": duplicates})
        if parser.images_without_alt:
            findings.append({"severity": "error", "code": "IMAGE_ALT_MISSING", "file": page.name, "count": parser.images_without_alt})
        if parser.external_blank_without_rel:
            findings.append({"severity": "error", "code": "NOOPENER_MISSING", "file": page.name, "details": parser.external_blank_without_rel})
        if parser.empty_interactive:
            findings.append({"severity": "error", "code": "UNNAMED_INTERACTIVE", "file": page.name, "count": len(parser.empty_interactive)})
        if parser.empty_headings:
            findings.append({"severity": "error", "code": "EMPTY_HEADING", "file": page.name, "count": parser.empty_headings})
        for attribute, value in parser.refs:
            target = local_target(page, value)
            if target is None:
                continue
            local_refs += 1
            try:
                target.relative_to(ROOT)
            except ValueError:
                findings.append({"severity": "error", "code": "REFERENCE_OUTSIDE_PUBLIC_ROOT", "file": page.name, "value": value})
                continue
            if not target.exists():
                findings.append({"severity": "error", "code": "BROKEN_LOCAL_REFERENCE", "file": page.name, "value": value})
        if page.name not in PRIVATE_PAGES and 'assets/page-counter.js' not in text:
            findings.append({"severity": "error", "code": "COMMON_FEEDBACK_MISSING", "file": page.name})
        for required in ('lang="', 'name="viewport"', '<title>'):
            if required not in text:
                findings.append({"severity": "error", "code": "PAGE_METADATA_MISSING", "file": page.name, "value": required})
        if 'href="#"' in text:
            findings.append({"severity": "warning", "code": "PLACEHOLDER_LINK", "file": page.name})

    integrity_roots = [ROOT / "assets", ROOT / "data" / "core", ROOT / "data" / "electroia", ROOT / "data" / "regulations"]
    replacement_files: list[dict] = []
    for base in integrity_roots:
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".html", ".js", ".css", ".json", ".md", ".txt", ".xml"}:
                continue
            text = path.read_text(encoding="utf-8")
            count = text.count("\ufffd")
            if count:
                replacement_files.append({"file": str(path.relative_to(ROOT)).replace("\\", "/"), "count": count})
    if replacement_files:
        findings.append({"severity": "error", "code": "DAMAGED_UNICODE", "details": replacement_files})

    components = read_json(ROOT / "data" / "components" / "catalog.json")["meta"]["counts"]["components"]
    readiness = read_json(ROOT / "data" / "ai" / "readiness-report.json")["readiness_score_percent"]
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    competence = (ROOT / "docs" / "V1-COMPETENCE-AUDIT.md").read_text(encoding="utf-8")
    if f"{components:,}".replace(",", ".") not in readme:
        findings.append({"severity": "error", "code": "STALE_COMPONENT_COUNT", "expected": components})
    if f"{readiness} %" not in competence and f"{readiness}%" not in competence:
        findings.append({"severity": "error", "code": "STALE_AI_READINESS", "expected": readiness})

    errors = [item for item in findings if item["severity"] == "error"]
    warnings = [item for item in findings if item["severity"] == "warning"]
    report = {
        "schema_version": "1.0",
        "updated_at": str(date.today()),
        "status": "pass" if not errors else "fail",
        "scope": "Super Técnico root pages, public references, shared UX, critical copy and published text integrity",
        "summary": {
            "root_pages": len(pages),
            "public_pages_with_common_feedback": sum(page.name not in PRIVATE_PAGES for page in pages),
            "local_references_checked": local_refs,
            "fatal_findings": len(errors),
            "warnings": len(warnings),
            "component_count_verified": components,
            "ai_readiness_verified_percent": readiness,
        },
        "quality_gates": {
            "local_references_exist": not any(item["code"] == "BROKEN_LOCAL_REFERENCE" for item in errors),
            "unique_dom_ids": not any(item["code"] == "DUPLICATE_IDS" for item in errors),
            "interactive_controls_are_named": not any(item["code"] == "UNNAMED_INTERACTIVE" for item in errors),
            "images_have_alt_attributes": not any(item["code"] == "IMAGE_ALT_MISSING" for item in errors),
            "external_tabs_are_isolated": not any(item["code"] == "NOOPENER_MISSING" for item in errors),
            "published_text_has_no_replacement_characters": not any(item["code"] == "DAMAGED_UNICODE" for item in errors),
            "authoritative_counts_match_copy": not any(item["code"] in {"STALE_COMPONENT_COUNT", "STALE_AI_READINESS"} for item in errors),
        },
        "findings": findings,
        "known_product_limits": [
            "La beta no sustituye manuales, normativa aplicable ni criterio profesional.",
            "Las pantallas privadas y su contenido dependen del backend PHP/MariaDB de IONOS.",
            "Las comprobaciones estructurales no sustituyen la validación visual y táctil en dispositivos reales.",
        ],
    }
    return report, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report, errors = build_report()
    content = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not REPORT.exists() or REPORT.read_text(encoding="utf-8") != content:
            raise SystemExit("data/core/app-quality-audit.json está desactualizado")
    else:
        REPORT.write_text(content, encoding="utf-8", newline="\n")
    print(json.dumps(report["summary"], ensure_ascii=False))
    if errors:
        raise SystemExit("Auditoría general fallida: " + ", ".join(item["code"] for item in errors))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
