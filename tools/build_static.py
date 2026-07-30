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
AD_PUBLISHER_RE = re.compile(r"^ca-pub-\d+$")
AD_SLOT_RE = re.compile(r"^\d+$")
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


def validate_advertising_configuration(source_root: Path, output: Path) -> dict[str, Any]:
    config = read_json(source_root / "data" / "ads-config.json")
    enabled = config.get("enabled") is True
    publisher_id = str(config.get("publisher_id") or "").strip()
    auto_ads = config.get("auto_ads") is True
    consent_provider = str(config.get("consent_provider") or "").strip()
    slots = config.get("slots") or {}

    if not isinstance(slots, dict):
        raise BuildError("La configuración publicitaria no contiene un mapa de espacios válido")
    invalid_slots = [
        name
        for name, value in slots.items()
        if str(value or "").strip() and not AD_SLOT_RE.fullmatch(str(value).strip())
    ]
    if invalid_slots:
        raise BuildError(
            "Identificadores de espacios publicitarios no válidos: "
            + ", ".join(sorted(invalid_slots))
        )
    if publisher_id and not AD_PUBLISHER_RE.fullmatch(publisher_id):
        raise BuildError("El identificador de editor de AdSense no tiene formato ca-pub-…")
    if enabled and not publisher_id:
        raise BuildError("No se puede activar AdSense sin identificador de editor")
    if enabled and consent_provider != "google-cmp":
        raise BuildError("La publicidad solo puede activarse con una CMP configurada")
    if enabled and not auto_ads and not any(str(value or "").strip() for value in slots.values()):
        raise BuildError("AdSense está activo, pero no hay anuncios automáticos ni espacios manuales")

    if publisher_id:
        ads_txt_publisher = publisher_id.removeprefix("ca-")
        (output / "ads.txt").write_text(
            f"google.com, {ads_txt_publisher}, DIRECT, f08c47fec0942fa0\n",
            encoding="utf-8",
            newline="\n",
        )

    return {
        "enabled": enabled,
        "publisher_configured": bool(publisher_id),
        "auto_ads": auto_ads,
        "consent_provider": consent_provider or None,
        "manual_slots": sum(bool(str(value or "").strip()) for value in slots.values()),
        "ads_txt": bool(publisher_id),
    }


def validate_smd_catalog(source_root: Path) -> tuple[dict[str, Any], dict[str, int]]:
    catalog = read_json(source_root / "data" / "smd" / "catalog.json")
    meta = catalog.get("meta") or {}
    candidates = catalog.get("candidates") or []
    if not isinstance(candidates, list):
        raise BuildError("El catálogo SMD no contiene una lista de candidatos válida")

    expected_candidates = 439
    expected_manufacturers = 6
    if int(meta.get("candidate_count") or 0) != expected_candidates:
        raise BuildError(
            f"Catálogo SMD: se esperaban {expected_candidates} candidatos y hay {len(candidates)}"
        )
    if len(candidates) != expected_candidates:
        raise BuildError("El recuento real de candidatos SMD no coincide con sus metadatos")
    if int(meta.get("manufacturer_count") or 0) != expected_manufacturers:
        raise BuildError("El catálogo SMD no contiene los seis fabricantes oficiales previstos")
    if int(meta.get("identification_ready") or 0) != expected_candidates:
        raise BuildError("Hay candidatos SMD que no están listos para identificación")

    candidate_ids = [str(item.get("id") or "") for item in candidates]
    if any(not candidate_id for candidate_id in candidate_ids):
        raise BuildError("Hay candidatos SMD sin identificador")
    if len(candidate_ids) != len(set(candidate_ids)):
        raise BuildError("Hay identificadores SMD duplicados")

    prohibited_fragments = ("smd codebook", "the smd codebook", "historical candidate")
    for item in candidates:
        quality = item.get("quality") or {}
        if (
            quality.get("level") != "identification_ready"
            or not all(
                quality.get(key) is True
                for key in (
                    "marking_verified",
                    "package_verified",
                    "pinout_verified",
                    "electrical_data_verified",
                )
            )
        ):
            raise BuildError(f"Candidato SMD no listo: {item.get('id')}")
        if not item.get("marking", {}).get("layouts"):
            raise BuildError(f"Candidato SMD sin diseño de marcaje: {item.get('id')}")
        if not item.get("package", {}).get("name") or not item.get("package", {}).get("pins"):
            raise BuildError(f"Candidato SMD sin encapsulado o patillas: {item.get('id')}")
        if not item.get("pinout"):
            raise BuildError(f"Candidato SMD sin patillaje: {item.get('id')}")
        if not item.get("parameters"):
            raise BuildError(f"Candidato SMD sin parámetros: {item.get('id')}")
        source = item.get("source") or {}
        for key in ("url", "datasheet_url"):
            if not str(source.get(key) or "").startswith("https://"):
                raise BuildError(f"Candidato SMD sin fuente HTTPS: {item.get('id')}")
        serialized = json.dumps(item, ensure_ascii=False).lower()
        if any(fragment in serialized for fragment in prohibited_fragments):
            raise BuildError(f"El catálogo SMD contiene una fuente histórica privada: {item.get('id')}")

    stats = {
        "candidates": len(candidates),
        "manufacturers": int(meta["manufacturer_count"]),
        "identification_ready": int(meta["identification_ready"]),
        "exact_ambiguity_groups": int(meta.get("exact_ambiguity_groups") or 0),
    }
    return catalog, stats


def validate_components_catalog(source_root: Path) -> tuple[dict[str, Any], dict[str, int]]:
    components_root = source_root / "data" / "components"
    catalog = read_json(components_root / "catalog.json")
    meta = catalog.get("meta") or {}
    components = catalog.get("components") or []
    if not isinstance(components, list):
        raise BuildError("El catálogo de componentes no contiene una lista válida")

    minimum = {
        "components": 11532,
        "specifications": 8363,
        "markings": 3862,
        "reviewed": 8205,
        "historical": 3327,
    }
    counts = meta.get("counts") or {}
    for key, value in minimum.items():
        if int(counts.get(key) or 0) < value:
            raise BuildError(
                f"Catálogo de componentes: {key} mínimo={value}, obtenido={counts.get(key)}"
            )
    if len(components) != int(counts.get("components") or 0):
        raise BuildError("El índice público de componentes no coincide con sus metadatos")

    component_ids = {int(item["id"]) for item in components}
    if len(component_ids) != len(components):
        raise BuildError("Hay identificadores de componente duplicados")

    chunk_count = int(meta.get("chunk_count") or 0)
    if chunk_count != 64:
        raise BuildError(f"Número de fragmentos de componentes inesperado: {chunk_count}")
    detail_ids: set[int] = set()
    for chunk_id in range(chunk_count):
        chunk = read_json(components_root / "details" / f"{chunk_id}.json")
        if not isinstance(chunk, dict):
            raise BuildError(f"Fragmento de componentes no válido: {chunk_id}")
        for key, detail in chunk.items():
            component_id = int(key)
            if component_id in detail_ids or int(detail.get("id") or -1) != component_id:
                raise BuildError(f"Detalle de componente duplicado o incoherente: {component_id}")
            if component_id % chunk_count != chunk_id:
                raise BuildError(f"Componente {component_id} guardado en un fragmento incorrecto")
            for url_key in ("datasheet_url",):
                url = detail.get(url_key)
                if url and not str(url).startswith("https://"):
                    raise BuildError(f"URL pública no segura en componente {component_id}")
            source_url = (detail.get("source") or {}).get("url")
            if source_url and not str(source_url).startswith("https://"):
                raise BuildError(f"Fuente pública no segura en componente {component_id}")
            detail_ids.add(component_id)
    if detail_ids != component_ids:
        raise BuildError("Los detalles públicos no coinciden con el índice de componentes")

    return catalog, {
        **{key: int(counts.get(key) or 0) for key in minimum},
        "manufacturers": int(counts.get("manufacturers") or 0),
        "packages": int(counts.get("packages") or 0),
        "chunks": chunk_count,
    }


def validate_oem_pcb_catalog(source_root: Path) -> tuple[dict[str, Any], dict[str, int]]:
    catalog = read_json(source_root / "data" / "oem" / "pcb_patterns.json")
    meta = catalog.get("meta") or {}
    patterns = catalog.get("patterns") or []
    ambiguous = catalog.get("ambiguous_patterns") or []

    expected = {"patterns": 47, "oems": 21, "ambiguous_patterns": 15}
    if len(patterns) != expected["patterns"]:
        raise BuildError("El identificador OEM no contiene los 47 patrones revisados")
    if len({item.get("oem") for item in patterns}) != expected["oems"]:
        raise BuildError("El identificador OEM no contiene las 21 plataformas previstas")
    if len(ambiguous) != expected["ambiguous_patterns"]:
        raise BuildError("El identificador OEM no contiene los 15 bloqueos ambiguos")

    ids = [int(item.get("id") or 0) for item in patterns]
    if any(record_id < 1 for record_id in ids) or len(ids) != len(set(ids)):
        raise BuildError("Hay identificadores OEM vacíos o duplicados")

    for item in patterns:
        record_id = int(item["id"])
        if item.get("confidence") not in {"alta", "media"}:
            raise BuildError(f"Confianza OEM no válida: {record_id}")
        source = item.get("source") or {}
        if not str(source.get("url") or "").startswith("https://"):
            raise BuildError(f"Patrón OEM sin fuente HTTPS: {record_id}")
        if source.get("authority") not in {"primary", "documented", "indirect"}:
            raise BuildError(f"Nivel de evidencia OEM no válido: {record_id}")
        brand_slug = item.get("brand_slug")
        if brand_slug and not SLUG_RE.fullmatch(str(brand_slug)):
            raise BuildError(f"Marca enlazada no válida en patrón OEM: {record_id}")
        try:
            matcher = re.compile(str(item["regex"]), re.IGNORECASE)
        except re.error as exc:
            raise BuildError(f"Regex OEM no válida: {record_id}") from exc
        example = re.sub(r"\s+", "", str(item.get("example") or "").upper())
        if not matcher.fullmatch(example):
            raise BuildError(f"El ejemplo OEM no coincide con su patrón: {record_id}")

    for item in ambiguous:
        try:
            re.compile(str(item["regex"]), re.IGNORECASE)
        except re.error as exc:
            raise BuildError(
                f"Regex ambigua no válida: {item.get('visible_pattern')}"
            ) from exc
        if not item.get("reason") or not item.get("recommended_action"):
            raise BuildError("Hay un patrón ambiguo sin explicación o siguiente paso")

    if int(meta.get("pattern_count") or 0) != expected["patterns"]:
        raise BuildError("Los metadatos del identificador OEM no coinciden")
    if int(meta.get("oem_count") or 0) != expected["oems"]:
        raise BuildError("El recuento de OEM no coincide con sus metadatos")
    if int(meta.get("ambiguous_pattern_count") or 0) != expected["ambiguous_patterns"]:
        raise BuildError("El recuento de patrones ambiguos no coincide con sus metadatos")

    return catalog, expected


def build(source_root: Path, output: Path) -> dict[str, Any]:
    source_root = source_root.resolve()
    output = output.resolve()
    if output == Path(output.anchor) or output == source_root:
        raise BuildError("Directorio de salida inseguro")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    for required in (
        "index.html",
        "climatizacion.html",
        "smd.html",
        "calculadoras.html",
        "componentes.html",
        "feedback.html",
        "assets/app.js",
        "assets/ads.js",
        "assets/calculations.js",
        "assets/calculators.css",
        "assets/calculators.js",
        "assets/common.css",
        "assets/components.css",
        "assets/components.js",
        "assets/feedback.css",
        "assets/feedback.js",
        "assets/i18n.js",
        "assets/portal.css",
        "assets/smd.css",
        "assets/smd.js",
        "assets/styles.css",
        "assets/super-tecnico-logo.png",
        "assets/libro-electronica-inverter-replacor-portada.png",
        "data/ads-config.json",
        "recursos/libro-electronica-inverter-replacor.pdf",
    ):
        source = source_root / required
        if not source.is_file():
            raise BuildError(f"Falta {required}")
        target = output / required
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    (output / ".nojekyll").write_text("", encoding="utf-8")
    advertising = validate_advertising_configuration(source_root, output)
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
    smd_catalog, smd_stats = validate_smd_catalog(source_root)
    write_json(output / "data" / "smd" / "catalog.json", smd_catalog)
    components_catalog, components_stats = validate_components_catalog(source_root)
    write_json(output / "data" / "components" / "catalog.json", components_catalog)
    components_details = source_root / "data" / "components" / "details"
    for path in sorted(components_details.glob("*.json")):
        write_json(output / "data" / "components" / "details" / path.name, read_json(path))
    oem_catalog, oem_stats = validate_oem_pcb_catalog(source_root)
    write_json(output / "data" / "oem" / "pcb_patterns.json", oem_catalog)
    report = {
        "project": "Super Técnico estático",
        "generated_at_utc": generated_at,
        "brands": manifest,
        "smd": smd_stats,
        "components": components_stats,
        "oem_pcb": oem_stats,
        "advertising": advertising,
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
