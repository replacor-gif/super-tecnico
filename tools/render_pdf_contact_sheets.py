#!/usr/bin/env python3
"""Render low-resolution PDF contact sheets for collection-wide visual QA."""

from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--pdftoppm", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for pdf in sorted(args.source.rglob("*.pdf")):
        with tempfile.TemporaryDirectory() as temp:
            short_pdf = Path(temp) / "source.pdf"
            shutil.copy2(pdf, short_pdf)
            prefix = Path(temp) / "page"
            subprocess.run(
                [str(args.pdftoppm), "-png", "-r", "42", str(short_pdf), str(prefix)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            pages = sorted(Path(temp).glob("page-*.png"))
            columns = 6
            thumb_w, thumb_h, label_h, gap = 290, 410, 24, 12
            rows = math.ceil(len(pages) / columns)
            sheet = Image.new("RGB", (gap + columns * (thumb_w + gap), 54 + rows * (thumb_h + label_h + gap)), "#d8dee3")
            draw = ImageDraw.Draw(sheet)
            draw.text((gap, 12), f"{pdf.parent.name} - {len(pages)} paginas", fill="#102f42")
            for index, page_path in enumerate(pages):
                page = Image.open(page_path).convert("RGB")
                page.thumbnail((thumb_w, thumb_h))
                x = gap + (index % columns) * (thumb_w + gap)
                y = 48 + (index // columns) * (thumb_h + label_h + gap)
                sheet.paste(page, (x + (thumb_w - page.width) // 2, y))
                draw.text((x, y + thumb_h + 2), f"p. {index + 1}", fill="#102f42")
            output = args.output / f"{pdf.parent.name}.jpg"
            sheet.save(output, quality=85, optimize=True)
            print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
