#!/usr/bin/env python3
"""Build and validate the public, static Super Técnico site."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
PUBLIC_MEDIA_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
FORBIDDEN_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".php", ".py", ".md"}
FORBIDDEN_NAMES = {".htaccess"}


class BuildError(RuntimeError):
    pass


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BuildError(f"Falta el archivo requerido: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BuildError(f"JSON no válido en {path}: {exc}") from exc


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sanitize_media(node: Any, publish_media: bool, counters: dict[str, int]) -> Any:
    if isinstance(node, list):
        return [sanitize_media(item, publish_media, counters) for item in node]
    if not isinstance(node, dict):
        return node

    result: dict[str, Any] = {}
    for key, value in node.items():
        if key == "media" and isinstance(value, list) and not publish_media:
            counters["media_references_removed"] += len(value)
            result[key] = []
        else:
            result[key] = sanitize_media(value, publish_media, counters)
    return result


def validate_brand(source_dir: Path, slug: str, config: dict[str, Any]) -> dict[str, int]:
    web_dir = source_dir / str(config.get("web_data") or "web")
    navigation = read_json(web_dir / "navigation.json")
    categories = navigation.get("categories") or []
    if not isinstance(categories, list):
        raise BuildError(f"navigation.json de {slug} no contiene categories válidas")

    topic_refs = [topic for category in categories for topic in (category.get("topics") or [])]
    topic_ids = [int(topic["id"]) for topic in topic_refs]
    if len(topic_ids) != len(set(topic_ids)):
        raise BuildError(f"Hay temas duplicados en la navegación de {slug}")

    variant_ids: set[int] = set()
    for topic_ref in topic_refs:
        topic_id = int(topic_ref["id"])
        topic = read_json(web_dir / "topics" / f"{topic_id}.json")
        variants = topic.get("variants") or []
        if len(variants) != int(topic_ref.get("variant_count") or 0):
            raise BuildError(f"El recuento de variantes no coincide en el tema {topic_id}")
        for variant in variants:
            variant_id = int(variant["id"])
            if variant_id in variant_ids:
                raise BuildError(f"Variante duplicada: {variant_id}")
            variant_ids.add(variant_id)

    variant_map = read_json(web_dir / "variant_map.json")
    if {int(key) for key in variant_map} != variant_ids:
        raise BuildError(f"variant_map.json no coincide con las variantes de {slug}")

    errors = read_json(web_dir / "errors" / "index.json")
    error_ids = {int(item["id"]) for item in errors}
    detail_ids = {
        int(path.stem)
        for path in (web_dir / "errors" / "details").glob("*.json")
        if path.stem.isdigit()
    }
    if error_ids != detail_ids:
        missing = sorted(error_ids - detail_ids)
        extra = sorted(detail_ids - error_ids)
        raise BuildError(f"Fichas de error inconsistentes en {slug}; faltan={missing}, sobran={extra}")

    search_entries = read_json(web_dir / "search.json")
    counts = {
        "categories": len(categories),
        "topics": len(topic_ids),
        "variants": len(variant_ids),
        "errors": len(errors),
        "search_entries": len(search_entries),
    }
    expected = config.get("counts") or {}
    for key, value in counts.items():
        if key in expected and int(expected[key]) != value:
            raise BuildError(f"Recuento {key} de {slug}: esperado {expected[key]}, obtenido {value}")
    return counts


def copy_brand(source: Path, destination: Path, config: dict[str, Any], counters: dict[str, int]) -> None:
    publish_media = config.get("publish_media") is True
    public_config = dict(config)
    public_config.pop("database", None)
    public_config.pop("database_sha256", None)
    public_config["media_published"] = publish_media
    write_json(destination / "brand.json", public_config)

    source_web = source / str(config.get("web_data") or "web")
    destination_web = destination / "web"
    for path in sorted(source_web.rglob("*.json")):
        relative = path.relative_to(source_web)
        data = read_json(path)
        write_json(destination_web / relative, sanitize_media(data, publish_media, counters))
        counters["json_files"] += 1

    if not publish_media:
        return

    media_dir = source / str(config.get("media") or "media")
    if not media_dir.is_dir():
        raise BuildError(f"{config['slug']} permite imágenes, pero no existe {media_dir}")
    for path in sorted(media_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in PUBLIC_MEDIA_SUFFIXES:
            raise BuildError(f"Tipo de imagen no permitido: {path}")
        target = destination / "media" / path.relative_to(media_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        counters["media_files"] += 1


def validate_public_tree(output: Path) -> None:
    for path in output.rglob("*"):
        if not path.is_file():
            continue
        if path.name.lower() in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise BuildError(f"El artefacto contiene un archivo prohibido: {path.relative_to(output)}")
        if path.suffix.lower() == ".json":
            read_json(path)


def build(source_root: Path, output: Path) -> dict[str, Any]:
    source_root = source_root.resolve()
    output = output.resolve()
    if output == Path(output.anchor) or output == source_root:
        raise BuildError("Directorio de salida inseguro")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    for required in ("index.html", "assets/app.js", "assets/styles.css"):
        source = source_root / required
        if not source.is_file():
            raise BuildError(f"Falta {required}")
        target = output / required
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    (output / ".nojekyll").write_text("", encoding="utf-8")
    brands_root = source_root / "data" / "brands"
    manifest: list[dict[str, Any]] = []
    counters = {"json_files": 0, "media_files": 0, "media_references_removed": 0}

    for directory in sorted(brands_root.iterdir()):
        if not directory.is_dir() or not SLUG_RE.fullmatch(directory.name):
            continue
        config_path = directory / "brand.json"
        if not config_path.is_file():
            continue
        config = read_json(config_path)
        if config.get("enabled") is not True:
            continue
        if config.get("slug") != directory.name:
            raise BuildError(f"El slug de {config_path} no coincide con su carpeta")
        counts = validate_brand(directory, directory.name, config)
        config["counts"] = counts
        copy_brand(directory, output / "data" / "brands" / directory.name, config, counters)
        manifest.append({
            "slug": directory.name,
            "name": config.get("name") or directory.name,
            "display_name": config.get("display_name") or config.get("name") or directory.name,
            "schema_version": config.get("schema_version"),
            "data_version": config.get("data_version"),
            "counts": counts,
            "notes": config.get("notes"),
            "media_published": config.get("publish_media") is True,
        })

    if not manifest:
        raise BuildError("No hay ninguna marca habilitada")

    generated_at = datetime.now(timezone.utc).isoformat()
    write_json(output / "data" / "brands" / "index.json", {
        "schema_version": "1.0",
        "generated_at_utc": generated_at,
        "brands": manifest,
    })
    report = {
        "project": "Super Técnico estático",
        "generated_at_utc": generated_at,
        "brands": manifest,
        "checks": counters,
    }
    write_json(output / "build-report.json", report)
    validate_public_tree(output)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("dist"))
    args = parser.parse_args()
    report = build(args.source, args.output)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
