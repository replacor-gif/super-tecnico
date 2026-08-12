#!/usr/bin/env python3
"""Create a concise GitHub notification from the regulation update report."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_output(path: Path | None, name: str, value: str) -> None:
    if path is None:
        return
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(f"{name}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=ROOT / "data" / "regulations" / "update-report.json")
    parser.add_argument("--body", type=Path, default=ROOT / "regulation-alert.md")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    report = load_json(args.report)
    changes = [
        item for item in report.get("documents", [])
        if item.get("new_document") or item.get("changed")
    ]
    fingerprint_source = json.dumps(
        [(item["id"], item.get("content_sha256"), item.get("sha256")) for item in changes],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()[:12]
    review_count = sum(bool(item.get("review_required")) for item in changes)

    lines = [
        "## Vigilancia normativa de Super Técnico",
        "",
        f"Comprobación: `{report.get('generated_at_utc', 'desconocida')}`",
        "",
    ]
    if not changes:
        lines.append("No se han detectado cambios en las fuentes oficiales vigiladas.")
    else:
        lines.extend([
            f"Se han detectado cambios en **{len(changes)}** documentos; **{review_count}** requieren revisar reglas o cálculos dependientes.",
            "",
            "| Documento | Tipo de cambio | Herramientas afectadas | Fuente |",
            "|---|---|---|---|",
        ])
        for item in changes:
            kinds = []
            if item.get("new_document"):
                kinds.append("nuevo")
            if item.get("content_changed"):
                kinds.append("contenido")
            elif item.get("source_file_changed"):
                kinds.append("archivo")
            lines.append(
                "| {title} | {kind} | {tools} | [Abrir fuente]({url}) |".format(
                    title=item.get("short_title") or item["id"],
                    kind=", ".join(kinds) or "huella",
                    tools=", ".join(item.get("affected_tools") or []) or "sin asignar",
                    url=item.get("official_page_url"),
                )
            )
        lines.extend([
            "",
            "### Control de seguridad",
            "",
            "Los documentos e índices pueden actualizarse automáticamente. Las reglas técnicas y calculadoras afectadas no deben marcarse como vigentes hasta comprobar el cambio y registrar la revisión.",
            "",
            f"Identificador del aviso: `{fingerprint}`",
        ])

    args.body.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    write_output(args.github_output, "changes_detected", "true" if changes else "false")
    write_output(args.github_output, "review_required", "true" if review_count else "false")
    write_output(args.github_output, "fingerprint", fingerprint)
    write_output(args.github_output, "change_count", str(len(changes)))
    print(json.dumps({"changes": len(changes), "review_required": review_count, "fingerprint": fingerprint}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
