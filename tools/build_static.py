#!/usr/bin/env python3
"""Build and validate the public, static Super Técnico site."""

from __future__ import annotations

import argparse
import hashlib
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


def validate_frigorista_data(source_root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, int]]:
    catalog = read_json(source_root / "data" / "frigorista" / "catalog.json")
    curves = read_json(source_root / "data" / "frigorista" / "pt-curves.json")
    mollier = read_json(source_root / "data" / "frigorista" / "mollier-data.json")
    if len({catalog.get("dataset_version"), curves.get("dataset_version"), mollier.get("dataset_version")}) != 1:
        raise BuildError("Frigorista: el catálogo, las curvas P/T y Mollier tienen versiones diferentes")

    refrigerants = catalog.get("refrigerants") or []
    curve_map = curves.get("curves") or {}
    if not isinstance(refrigerants, list) or not isinstance(curve_map, dict):
        raise BuildError("Frigorista: catálogo o curvas P/T no válidos")
    ids = [item.get("id") for item in refrigerants]
    designations = [item.get("designation") for item in refrigerants]
    if len(ids) != len(set(ids)) or len(designations) != len(set(designations)):
        raise BuildError("Frigorista: hay identificadores o designaciones duplicadas")

    available = {
        item["designation"]
        for item in refrigerants
        if item.get("selectable") is True and item.get("pt_available") is True
    }
    if available != set(curve_map):
        raise BuildError("Frigorista: la cobertura del catálogo no coincide con las curvas publicadas")
    if len(available) < 50:
        raise BuildError(f"Frigorista: cobertura P/T insuficiente ({len(available)})")
    mollier_map = mollier.get("refrigerants") or {}
    if set(mollier_map) != available:
        raise BuildError("Frigorista: la cobertura Mollier no coincide con las curvas publicadas")

    for designation, curve in curve_map.items():
        for phase in ("bubble", "dew"):
            points = curve.get(phase) or []
            if len(points) < 20 or any(len(point) != 2 or point[0] <= 0 for point in points):
                raise BuildError(f"Frigorista: curva {phase} inválida para {designation}")
            pressures = [point[0] for point in points]
            if pressures != sorted(pressures) or len(pressures) != len(set(pressures)):
                raise BuildError(f"Frigorista: presiones no crecientes en {designation} ({phase})")

    for designation, diagram in mollier_map.items():
        rows = diagram.get("pressure_rows") or []
        if len(rows) < 12:
            raise BuildError(f"Frigorista: diagrama Mollier insuficiente para {designation}")
        pressures = [row.get("p") for row in rows]
        if any(not isinstance(value, (int, float)) or value <= 0 for value in pressures):
            raise BuildError(f"Frigorista: presión Mollier inválida para {designation}")
        if pressures != sorted(pressures) or len(pressures) != len(set(pressures)):
            raise BuildError(f"Frigorista: presiones Mollier no crecientes en {designation}")
        for row in rows:
            if len(row.get("bubble") or []) != 3 or len(row.get("dew") or []) != 3:
                raise BuildError(f"Frigorista: saturación Mollier incompleta en {designation}")
            if len(row.get("vapor") or []) < 3 or len(row.get("liquid") or []) < 3:
                raise BuildError(f"Frigorista: estados Mollier incompletos en {designation}")

    blocked = sum(
        item.get("selectable") is False and bool(item.get("excluded_reason"))
        for item in refrigerants
    )
    return catalog, curves, mollier, {
        "catalog": len(refrigerants),
        "pt_available": len(available),
        "pt_pending_or_blocked": len(refrigerants) - len(available),
        "blocked": blocked,
        "mollier_available": len(mollier_map),
    }


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def validate_regulations_data(source_root: Path) -> tuple[dict[str, Any], dict[str, int]]:
    catalog = read_json(source_root / "data" / "regulations" / "catalog.json")
    documents = catalog.get("documents") or []
    if catalog.get("jurisdiction") != "ES" or len(documents) < 18:
        raise BuildError("Normativa: el catálogo oficial está incompleto")
    ids = [str(document.get("id") or "") for document in documents]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise BuildError("Normativa: hay identificadores vacíos o duplicados")

    totals = {"documents": len(documents), "pages": 0, "search_records": 0, "bytes": 0}
    for document in documents:
        document_id = document["id"]
        if not str(document.get("official_page_url") or "").startswith("https://"):
            raise BuildError(f"Normativa: fuente oficial insegura para {document_id}")
        if not str(document.get("storage_policy") or "").startswith("public_official_text"):
            raise BuildError(f"Normativa: política de almacenamiento no publicable para {document_id}")

        pdf_relative = Path(str(document.get("local_pdf") or ""))
        if pdf_relative.parts[:2] != ("recursos", "normativa") or pdf_relative.suffix.lower() != ".pdf":
            raise BuildError(f"Normativa: ruta PDF insegura para {document_id}")
        pdf_path = source_root / pdf_relative
        if not pdf_path.is_file() or pdf_path.stat().st_size != int(document.get("bytes") or 0):
            raise BuildError(f"Normativa: PDF ausente o tamaño incorrecto para {document_id}")
        digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        if digest != document.get("sha256"):
            raise BuildError(f"Normativa: la huella del PDF ha cambiado para {document_id}")
        content_digest = str(document.get("content_sha256") or "")
        if len(content_digest) != 64:
            raise BuildError(f"Normativa: falta la huella semántica para {document_id}")

        index_relative = Path(str(document.get("index_url") or ""))
        if index_relative.parts[:3] != ("data", "regulations", "index") or index_relative.suffix != ".json":
            raise BuildError(f"Normativa: ruta de índice insegura para {document_id}")
        index = read_json(source_root / index_relative)
        records = index.get("records") or []
        if (
            index.get("document_id") != document_id
            or index.get("source_sha256") != digest
            or index.get("source_content_sha256") != content_digest
        ):
            raise BuildError(f"Normativa: índice desincronizado para {document_id}")
        if int(index.get("page_count") or 0) != int(document.get("page_count") or 0):
            raise BuildError(f"Normativa: páginas desincronizadas para {document_id}")
        if len(records) != int(document.get("search_records") or 0):
            raise BuildError(f"Normativa: recuento de búsquedas incorrecto para {document_id}")
        if not records or any(
            record.get("document_id") != document_id
            or int(record.get("page") or 0) < 1
            or not record.get("text")
            or not record.get("search")
            for record in records
        ):
            raise BuildError(f"Normativa: registros no válidos para {document_id}")
        totals["pages"] += int(document["page_count"])
        totals["search_records"] += len(records)
        totals["bytes"] += pdf_path.stat().st_size

    if totals["pages"] < 1000 or totals["search_records"] < 2500:
        raise BuildError("Normativa: cobertura documental insuficiente")
    return catalog, totals


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


def validate_connectors_catalog(source_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    connectors_root = source_root / "data" / "connectors"
    catalog = read_json(connectors_root / "catalog.json")
    sources = read_json(connectors_root / "sources.json")
    records = catalog.get("records") or []
    source_records = sources.get("sources") or []
    if not isinstance(records, list) or len(records) < 17:
        raise BuildError("El catálogo de conectores no contiene las 17 fichas iniciales")
    ids = [str(record.get("id") or "") for record in records]
    if any(not connector_id for connector_id in ids) or len(ids) != len(set(ids)):
        raise BuildError("El catálogo de conectores contiene identificadores vacíos o duplicados")
    source_ids = {str(source.get("id") or "") for source in source_records}
    if not source_ids or "" in source_ids or len(source_ids) != len(source_records):
        raise BuildError("El registro de fuentes de conectores es inválido")
    allowed_statuses = {"reviewed", "source_identified", "pending_review"}
    contact_count = 0
    status_counts = {status: 0 for status in allowed_statuses}
    for record in records:
        contacts = record.get("contacts") or []
        contact_ids = [str(contact.get("id") or "") for contact in contacts]
        if not contacts or any(not item for item in contact_ids) or len(contact_ids) != len(set(contact_ids)):
            raise BuildError(f"Contactos vacíos o duplicados en {record.get('id')}")
        if any(not contact.get("signal") or not contact.get("description") for contact in contacts):
            raise BuildError(f"Contacto incompleto en {record.get('id')}")
        view = record.get("view") or {}
        if not view.get("perspective") or not view.get("orientation_note"):
            raise BuildError(f"Vista incompleta en {record.get('id')}")
        review = record.get("review") or {}
        status = review.get("status")
        if status not in allowed_statuses or not review.get("scope"):
            raise BuildError(f"Revisión incompleta en {record.get('id')}")
        missing_sources = set(record.get("source_ids") or []) - source_ids
        if missing_sources:
            raise BuildError(f"Fuentes inexistentes en {record.get('id')}: {sorted(missing_sources)}")
        contact_count += len(contacts)
        status_counts[status] += 1
    counts = catalog.get("counts") or {}
    expected = {
        "records": len(records),
        "contacts": contact_count,
        **status_counts,
    }
    if any(int(counts.get(key) or 0) != value for key, value in expected.items()):
        raise BuildError(f"Metadatos de conectores incoherentes: esperado {expected}, obtenido {counts}")
    for source in source_records:
        url = str(source.get("url") or "")
        if not (url.startswith("https://") or url.startswith("recursos/")):
            raise BuildError(f"Fuente de conector insegura: {source.get('id')}")
    return catalog, {**expected, "sources": len(source_records)}


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
        "proyectos.html",
        "climatizacion.html",
        "frigorista.html",
        "desagues-condensados.html",
        "tuberias-frigorificas.html",
        "normativa.html",
        "smd.html",
        "calculadoras.html",
        "conductos.html",
        "ventilacion.html",
        "analitica-privada.html",
        "bitacora-privada.html",
        "componentes.html",
        "conectores.html",
        "plataformas-embebidas.html",
        "comparador.html",
        "averias.html",
        "feedback.html",
        "actualizaciones.html",
        "electroia.html",
        "ia-integracion.html",
        "llms.txt",
        "robots.txt",
        "sitemap.xml",
        "manifest.webmanifest",
        "service-worker.js",
        "archivo-tecnico-47097e44267b9cb111636b84823f1d47/index.html",
        "archivo-tecnico-47097e44267b9cb111636b84823f1d47/styles.css",
        "archivo-tecnico-47097e44267b9cb111636b84823f1d47/engine.js",
        "archivo-tecnico-47097e44267b9cb111636b84823f1d47/diagram-symbol-library.js",
        "archivo-tecnico-47097e44267b9cb111636b84823f1d47/diagram-core.js",
        "archivo-tecnico-47097e44267b9cb111636b84823f1d47/diagram.js",
        "archivo-tecnico-47097e44267b9cb111636b84823f1d47/app.js",
        "electroia-tool-server/package.json",
        "electroia-tool-server/pnpm-lock.yaml",
        "electroia-tool-server/server.json",
        "electroia-tool-server/src/cli.mjs",
        "electroia-tool-server/src/index.mjs",
        "electroia-tool-server/src/toolkit.mjs",
        "simbolos.html",
        "formacion-climatizacion.html",
        "electronica-placas.html",
        "assets/app.js",
        "assets/app-shell.js",
        "assets/app-theme.css",
        "assets/project-core.js",
        "assets/project-manager.js",
        "assets/project-manager.css",
        "assets/ads.js",
        "assets/calculations.js",
        "assets/calculators.css",
        "assets/calculators.js",
        "assets/frigorista.css",
        "assets/frigorista-engine.js",
        "assets/frigorista.js",
        "assets/condensate-drain.css",
        "assets/condensate-drain-engine.js",
        "assets/condensate-drain.js",
        "assets/refrigerant-piping.css",
        "assets/refrigerant-piping-engine.js",
        "assets/refrigerant-piping.js",
        "assets/regulations.css",
        "assets/regulations-search.css",
        "assets/regulations.js",
        "assets/duct-designer.css",
        "assets/duct-designer.js",
        "assets/ventilation-designer.css",
        "assets/ventilation-designer.js",
        "assets/ventilation-rules.js",
        "assets/analytics.css",
        "assets/analytics.js",
        "assets/backlog.css",
        "assets/backlog.js",
        "assets/common.css",
        "assets/components.css",
        "assets/components.js",
        "assets/connectors.css",
        "assets/connectors.js",
        "assets/embedded-platforms.css",
        "assets/embedded-platforms.js",
        "assets/datasheet-finder.js",
        "assets/comparator.css",
        "assets/comparator.js",
        "assets/community-api.js",
        "assets/faults.css",
        "assets/faults-browse.css",
        "assets/faults.js",
        "assets/feedback.css",
        "assets/feedback.js",
        "assets/updates.css",
        "assets/updates.js",
        "assets/electronics.css",
        "assets/electronics.js",
        "assets/electroia-public.css",
        "assets/electroia-public.js",
        "assets/i18n.js",
        "assets/ai-integration.css",
        "assets/page-counter.js",
        "assets/portal.css",
        "assets/smd.css",
        "assets/smd.js",
        "assets/symbols.css",
        "assets/symbols.js",
        "assets/training.css",
        "assets/training.js",
        "assets/styles.css",
        "assets/super-tecnico-logo.png",
        "assets/libro-electronica-inverter-replacor-portada.png",
        "data/ads-config.json",
        "data/frigorista/catalog.json",
        "data/frigorista/pt-curves.json",
        "data/frigorista/mollier-data.json",
        "data/ventilation/discovery.json",
        "data/ventilation/tool-manifest.json",
        "data/updates/feed.json",
        "data/refrigerant-piping/discovery.json",
        "data/refrigerant-piping/tool-manifest.json",
        "data/refrigerant-piping/design-rules.json",
        "data/refrigerant-piping/property-grid.json",
        "data/electroia/controller-ecosystems.json",
        "data/electroia/public-gallery.json",
        "data/connectors/connector-record.schema.json",
        "data/connectors/sources.json",
        "data/connectors/tool-manifest.json",
        "data/connectors/discovery.json",
        "data/connectors/discovery.openapi.json",
        "data/embedded-platforms/catalog.json",
        "data/embedded-platforms/sources.json",
        "data/embedded-platforms/guides.json",
        "data/embedded-platforms/tool-manifest.json",
        "data/embedded-platforms/discovery.json",
        "data/embedded-platforms/discovery.openapi.json",
        "data/core/motor-registry.json",
        "data/core/project-roadmap.json",
        "data/core/app-quality-audit.json",
        "data/electrical-panels/examples/motor-pump-dol-auto-manual.json",
        "data/electrical-panels/panel-project.schema.json",
        "data/electrical-panels/standards-registry.json",
        "data/electrical-panels/tool-manifest.json",
        "data/projects/technical-project.schema.json",
        "data/projects/tool-manifest.json",
        "recursos/libro-electronica-inverter-replacor.pdf",
        "recursos/enciclopedia-conectores-pinouts-edicion-8-origen.pdf",
        "recursos/catalogo-normalizado-conectores-replacor-edicion-9.pdf",
    ):
        source = source_root / required
        if not source.is_file():
            raise BuildError(f"Falta {required}")
        target = output / required
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    symbols_catalog = read_json(source_root / "data" / "symbols" / "catalog.json")
    symbols_course = read_json(source_root / "data" / "symbols" / "course.json")
    symbols = symbols_catalog.get("symbols") or []
    modules = symbols_course.get("modules") or []
    lessons = [lesson for module in modules for lesson in (module.get("lessons") or [])]
    if len(symbols) < 501 or len({item.get("id") for item in symbols}) != len(symbols):
        raise BuildError("La biblioteca pública de símbolos está incompleta o contiene ID duplicados")
    if len(modules) < 6 or len(lessons) < 24 or len({item.get("id") for item in lessons}) != len(lessons):
        raise BuildError("El curso de esquemas está incompleto o contiene lecciones duplicadas")
    for item in symbols:
        if not all(item.get(key) for key in ("id", "nombre", "categoria", "descripcion", "interpretacion", "archivo_svg")):
            raise BuildError(f"Ficha de símbolo incompleta: {item.get('id')}")
        source = str(item.get("fuente") or "")
        if source and not source.startswith("https://"):
            raise BuildError(f"Fuente no segura en {item.get('id')}")
        asset = source_root / str(item["archivo_svg"])
        if not asset.is_file():
            raise BuildError(f"Falta la imagen de {item.get('id')}: {item['archivo_svg']}")
    for lesson in lessons:
        if not lesson.get("steps") or not lesson.get("quiz") or not (source_root / str(lesson.get("archivo_svg"))).is_file():
            raise BuildError(f"Lección interactiva incompleta: {lesson.get('id')}")
    write_json(output / "data" / "symbols" / "catalog.json", symbols_catalog)
    write_json(output / "data" / "symbols" / "course.json", symbols_course)
    write_json(output / "data" / "symbols" / "index.json", read_json(source_root / "data" / "symbols" / "index.json"))
    symbols_asset_output = output / "assets" / "symbols"
    symbols_asset_output.mkdir(parents=True, exist_ok=True)
    for path in sorted((source_root / "assets" / "symbols").glob("*.svg")):
        shutil.copy2(path, symbols_asset_output / path.name)

    training = read_json(source_root / "data" / "training" / "collection.json")
    training_stats = training.get("stats") or {}
    expected_training = {
        "modules": 7,
        "pages": 209,
        "chapters": 167,
        "figures": 158,
        "tables": 132,
    }
    for key, expected in expected_training.items():
        if int(training_stats.get(key) or 0) != expected:
            raise BuildError(
                f"Curso de climatización: {key} esperado={expected}, obtenido={training_stats.get(key)}"
            )
    training_modules = training.get("modules") or []
    training_chapters = [
        chapter
        for module in training_modules
        for chapter in (module.get("chapters") or [])
    ]
    chapter_ids = [str(chapter.get("id") or "") for chapter in training_chapters]
    if len(chapter_ids) != len(set(chapter_ids)) or any(not value for value in chapter_ids):
        raise BuildError("El curso de climatización contiene capítulos sin ID o duplicados")
    figure_paths = {
        str(block.get("src"))
        for chapter in training_chapters
        for block in (chapter.get("blocks") or [])
        if block.get("type") == "figure"
    }
    if len(figure_paths) != expected_training["figures"]:
        raise BuildError("El curso no referencia exactamente las 158 figuras publicables")
    for figure in figure_paths:
        if not figure.startswith("assets/training/") or not (source_root / figure).is_file():
            raise BuildError(f"Figura de formación ausente o insegura: {figure}")
    write_json(output / "data" / "training" / "collection.json", training)
    write_json(
        output / "data" / "training" / "build-report.json",
        read_json(source_root / "data" / "training" / "build-report.json"),
    )
    training_assets = output / "assets" / "training"
    training_assets.mkdir(parents=True, exist_ok=True)
    for path in sorted((source_root / "assets" / "training").rglob("*.png")):
        target = training_assets / path.relative_to(source_root / "assets" / "training")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)

    electronics = read_json(source_root / "data" / "electronics" / "collection.json")
    electronics_stats = electronics.get("stats") or {}
    expected_electronics = {
        "modules": 23,
        "pages": 399,
        "chapters": 678,
        "figures": 397,
        "tables": 235,
    }
    for key, expected in expected_electronics.items():
        if int(electronics_stats.get(key) or 0) != expected:
            raise BuildError(
                f"Electrónica de placas: {key} esperado={expected}, obtenido={electronics_stats.get(key)}"
            )
    electronics_modules = electronics.get("modules") or []
    electronics_chapters = [
        chapter
        for module in electronics_modules
        for chapter in (module.get("chapters") or [])
    ]
    electronics_ids = [str(chapter.get("id") or "") for chapter in electronics_chapters]
    if len(electronics_ids) != len(set(electronics_ids)) or any(not value for value in electronics_ids):
        raise BuildError("La biblioteca de electrónica contiene apartados sin ID o duplicados")
    electronics_figures = {
        str(block.get("src"))
        for chapter in electronics_chapters
        for block in (chapter.get("blocks") or [])
        if block.get("type") == "figure"
    }
    if len(electronics_figures) != expected_electronics["figures"]:
        raise BuildError("La biblioteca de electrónica no referencia exactamente sus 397 figuras")
    for figure in electronics_figures:
        if not figure.startswith("assets/electronics/") or not (source_root / figure).is_file():
            raise BuildError(f"Figura de electrónica ausente o insegura: {figure}")
    if len(electronics.get("routes") or []) < 8 or len(electronics.get("groups") or []) < 10:
        raise BuildError("Faltan rutas o bloques funcionales en electrónica")
    write_json(output / "data" / "electronics" / "collection.json", electronics)
    write_json(
        output / "data" / "electronics" / "build-report.json",
        read_json(source_root / "data" / "electronics" / "build-report.json"),
    )
    electronics_assets = output / "assets" / "electronics"
    electronics_assets.mkdir(parents=True, exist_ok=True)
    for path in sorted((source_root / "assets" / "electronics").rglob("*.png")):
        target = electronics_assets / path.relative_to(source_root / "assets" / "electronics")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)

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
    connectors_catalog, connectors_stats = validate_connectors_catalog(source_root)
    write_json(output / "data" / "connectors" / "catalog.json", connectors_catalog)
    frigorista_catalog, frigorista_curves, frigorista_mollier, frigorista_stats = validate_frigorista_data(source_root)
    write_json(output / "data" / "frigorista" / "catalog.json", frigorista_catalog)
    write_json(output / "data" / "frigorista" / "pt-curves.json", frigorista_curves)
    write_json(output / "data" / "frigorista" / "mollier-data.json", frigorista_mollier)
    write_json(
        output / "data" / "frigorista" / "discovery.json",
        read_json(source_root / "data" / "frigorista" / "discovery.json"),
    )
    write_json(
        output / "data" / "frigorista" / "tool-manifest.json",
        read_json(source_root / "data" / "frigorista" / "tool-manifest.json"),
    )
    regulations_catalog, regulations_stats = validate_regulations_data(source_root)
    write_json(output / "data" / "regulations" / "catalog.json", regulations_catalog)
    write_json(
        output / "data" / "regulations" / "tool-manifest.json",
        read_json(source_root / "data" / "regulations" / "tool-manifest.json"),
    )
    write_json(
        output / "data" / "regulations" / "update-report.json",
        read_json(source_root / "data" / "regulations" / "update-report.json"),
    )
    write_json(
        output / "data" / "regulations" / "rule-record.schema.json",
        read_json(source_root / "data" / "regulations" / "rule-record.schema.json"),
    )
    for document in regulations_catalog["documents"]:
        index_relative = Path(document["index_url"])
        write_json(output / index_relative, read_json(source_root / index_relative))
        pdf_relative = Path(document["local_pdf"])
        pdf_target = output / pdf_relative
        pdf_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_root / pdf_relative, pdf_target)
    write_json(
        output / "data" / "condensate" / "tool-manifest.json",
        read_json(source_root / "data" / "condensate" / "tool-manifest.json"),
    )
    write_json(
        output / "data" / "electroia" / "tool-manifest.json",
        read_json(source_root / "data" / "electroia" / "tool-manifest.json"),
    )
    write_json(
        output / "data" / "electroia" / "diagram-document.schema.json",
        read_json(source_root / "data" / "electroia" / "diagram-document.schema.json"),
    )
    write_json(
        output / "data" / "electroia" / "discovery.json",
        read_json(source_root / "data" / "electroia" / "discovery.json"),
    )
    write_json(
        output / "data" / "electroia" / "discovery.openapi.json",
        read_json(source_root / "data" / "electroia" / "discovery.openapi.json"),
    )
    write_json(
        output / "data" / "electroia" / "symbol-library.json",
        read_json(source_root / "data" / "electroia" / "symbol-library.json"),
    )
    write_json(
        output / "data" / "electroia" / "symbol-normalization-report.json",
        read_json(source_root / "data" / "electroia" / "symbol-normalization-report.json"),
    )
    write_json(
        output / "data" / "electroia" / "engine-audit-report.json",
        read_json(source_root / "data" / "electroia" / "engine-audit-report.json"),
    )
    write_json(
        output / "data" / "electroia" / "public-release-readiness.json",
        read_json(source_root / "data" / "electroia" / "public-release-readiness.json"),
    )
    write_json(
        output / "data" / "electroia" / "document-profiles.json",
        read_json(source_root / "data" / "electroia" / "document-profiles.json"),
    )
    write_json(
        output / "data" / "electroia" / "public-execution-policy.json",
        read_json(source_root / "data" / "electroia" / "public-execution-policy.json"),
    )
    write_json(
        output / "data" / "electroia" / "ai-bridge.json",
        read_json(source_root / "data" / "electroia" / "ai-bridge.json"),
    )
    for path in sorted((source_root / "data" / "electroia" / "examples").glob("*.json")):
        write_json(output / "data" / "electroia" / "examples" / path.name, read_json(path))
    electroia_gallery = read_json(source_root / "data" / "electroia" / "public-gallery.json")
    write_json(output / "data" / "electroia" / "public-gallery.json", electroia_gallery)
    if int(electroia_gallery.get("count") or 0) != 5 or len(electroia_gallery.get("items") or []) != 5:
        raise BuildError("La galería pública de ElectroIA no contiene los cinco planos patrón")
    for item in electroia_gallery["items"]:
        if item.get("single_canvas") is not True or any(int(value or 0) for value in (item.get("validation") or {}).values()):
            raise BuildError(f"Plano público de ElectroIA no apto: {item.get('id')}")
        image_relative = Path(str(item.get("image") or ""))
        source_relative = Path(str(item.get("source") or ""))
        if image_relative.suffix.lower() != ".svg" or not (source_root / image_relative).is_file():
            raise BuildError(f"Imagen de ElectroIA ausente o insegura: {image_relative}")
        if source_relative.suffix.lower() != ".json" or not (source_root / source_relative).is_file():
            raise BuildError(f"Documento de ElectroIA ausente o inseguro: {source_relative}")
        target = output / image_relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_root / image_relative, target)
    for filename in (
        "discovery.json",
        "tool-manifest.json",
        "knowledge-record.schema.json",
        "knowledge-api-contract.openapi.json",
        "readiness-report.json",
        "benchmark-plan.json",
        "tool-strategy.json",
        "storage-policy.json",
    ):
        write_json(
            output / "data" / "ai" / filename,
            read_json(source_root / "data" / "ai" / filename),
        )
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
        "connectors": connectors_stats,
        "frigorista": frigorista_stats,
        "regulations": regulations_stats,
        "oem_pcb": oem_stats,
        "symbols": {"symbols": len(symbols), "lessons": len(lessons), "modules": len(modules)},
        "training": training_stats,
        "electronics": electronics_stats,
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
