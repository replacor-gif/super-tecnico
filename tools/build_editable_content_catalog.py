#!/usr/bin/env python3
"""Build the stable catalog used by the private plain-text editor."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from html import unescape
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "content" / "editable-catalog.json"
PRIVATE_PAGES = {"analitica-privada.html", "bitacora-privada.html", "editor-contenidos.html", "moderacion.html"}
SKIP_TAGS = {"head", "script", "style", "template", "svg", "noscript"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
TEXT_TAGS = {
    "a", "b", "button", "dd", "dt", "em", "figcaption", "h1", "h2", "h3", "h4",
    "h5", "h6", "i", "label", "legend", "li", "option", "p", "small", "span",
    "strong", "summary", "td", "th",
}
LETTER_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]")


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value)).strip()


def editable(value: str) -> bool:
    return len(value) >= 3 and LETTER_RE.search(value) is not None


def fnv1a(value: str) -> str:
    current = 2166136261
    encoded = value.encode("utf-16-le")
    for index in range(0, len(encoded), 2):
        # JavaScript charCodeAt() recorre unidades UTF-16, también para emoji.
        current ^= encoded[index] | (encoded[index + 1] << 8)
        current = (current * 16777619) & 0xFFFFFFFF
    return f"{current:08x}"


def page_slug(path: Path) -> str:
    return "inicio" if path.stem == "index" else re.sub(r"[^a-z0-9-]", "-", path.stem.lower())


def field_label(kind: str, tag: str, value: str) -> str:
    names = {
        "h1": "Título principal", "h2": "Título de sección", "h3": "Título de bloque",
        "h4": "Título secundario", "p": "Párrafo", "a": "Enlace", "button": "Botón",
        "label": "Etiqueta", "li": "Elemento de lista", "summary": "Desplegable",
        "option": "Opción", "placeholder": "Texto de ayuda", "aria": "Nombre accesible",
    }
    prefix = names.get(tag if kind == "text" else kind, "Texto")
    preview = value if len(value) <= 68 else value[:65].rstrip() + "…"
    return f"{prefix} · {preview}"


class EditableParser(HTMLParser):
    def __init__(self, path: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.path = path
        self.slug = page_slug(path)
        self.stack: list[tuple[str, bool]] = []
        self.body_depth = 0
        self.title_depth = 0
        self.title_parts: list[str] = []
        self.raw: list[dict[str, str]] = []

    def blocked(self) -> bool:
        return any(item[1] for item in self.stack)

    def add(self, kind: str, tag: str, value: str) -> None:
        value = clean_text(value)
        if editable(value):
            self.raw.append({"kind": kind, "tag": tag, "default": value})

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        blocked = (
            self.blocked()
            or tag in SKIP_TAGS
            or values.get("aria-hidden", "").lower() == "true"
            or "data-i18n" in values
        )
        self.stack.append((tag, blocked))
        if tag == "body":
            self.body_depth += 1
        if tag == "title":
            self.title_depth += 1
        if self.body_depth and not blocked:
            if values.get("placeholder") and "data-i18n-placeholder" not in values:
                self.add("placeholder", tag, values["placeholder"])
            if values.get("aria-label") and "data-i18n-aria" not in values:
                self.add("aria", tag, values["aria-label"])
        if tag in VOID_TAGS:
            self.stack.pop()

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        if self.title_depth:
            self.title_parts.append(data)
        if not self.body_depth or self.blocked() or not self.stack:
            return
        tag = self.stack[-1][0]
        if tag in TEXT_TAGS:
            self.add("text", tag, data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.title_depth = max(0, self.title_depth - 1)
        if tag == "body":
            self.body_depth = max(0, self.body_depth - 1)
        if self.stack:
            self.stack.pop()

    def entries(self) -> list[dict[str, str]]:
        occurrences: Counter[tuple[str, str]] = Counter()
        page_title = clean_text(" ".join(self.title_parts)).split("|")[0].strip() or self.path.stem
        result = []
        for item in self.raw:
            digest = fnv1a(f"{item['kind']}|{item['default']}")
            occurrence_key = (item["kind"], digest)
            occurrences[occurrence_key] += 1
            key = f"page.{self.slug}.{item['kind']}.{digest}.{occurrences[occurrence_key]}"
            result.append({
                "key": key,
                "page": self.path.name,
                "page_slug": self.slug,
                "page_title": page_title,
                "kind": item["kind"],
                "tag": item["tag"],
                "label": field_label(item["kind"], item["tag"], item["default"]),
                "default": item["default"],
            })
        return result


def build(root: Path = ROOT) -> dict:
    entries: list[dict[str, str]] = []
    pages = [path for path in sorted(root.glob("*.html")) if path.name not in PRIVATE_PAGES]
    for path in pages:
        parser = EditableParser(path)
        parser.feed(path.read_text(encoding="utf-8"))
        entries.extend(parser.entries())
    keys = [item["key"] for item in entries]
    if len(keys) != len(set(keys)):
        raise RuntimeError("El catálogo editable contiene claves duplicadas")
    return {
        "schema_version": "1.0",
        "summary": {"pages": len(pages), "editable_fields": len(entries)},
        "entries": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    catalog = build(ROOT)
    content = json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not args.output.is_file() or args.output.read_text(encoding="utf-8") != content:
            raise SystemExit("El catálogo editable está desactualizado")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8", newline="\n")
    print(json.dumps(catalog["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
