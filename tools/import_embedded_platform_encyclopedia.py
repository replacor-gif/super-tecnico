#!/usr/bin/env python3
"""Import the 41 platform fiches from REPLACRO's 2026 embedded encyclopedia.

The source PDF remains outside the public build. Generated records retain a
page locator and a conservative review state so downstream tools can separate
transcription from an exact-board official verification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "embedded-platforms"
EXPECTED_SHA256 = "7f68105b7732fa4cb7fd408856cad8573225443ed0fd1330b701c1976c826b15"
FIRST_PDF_PAGE = 69
LAST_PDF_PAGE = 109

PLATFORM_META = {
    "Arduino Nano 33 BLE Sense Rev2": ("Arduino", "microcontroller_board", ["tinyml", "sensors", "ble", "audio", "motion"]),
    "Arduino Nano RP2040 Connect": ("Arduino", "microcontroller_board", ["pio", "wifi", "ble", "compact"]),
    "Arduino Nano Matter": ("Arduino", "microcontroller_board", ["matter", "thread", "ble", "smart-home"]),
    "Arduino Nano R4": ("Arduino", "microcontroller_board", ["renesas", "compact", "migration"]),
    "Arduino MKR WAN 1310": ("Arduino", "microcontroller_board", ["lora", "lorawan", "battery", "telemetry"]),
    "Arduino MKR NB 1500": ("Arduino", "microcontroller_board", ["lte-m", "nb-iot", "cellular", "telemetry"]),
    "Arduino Portenta C33": ("Arduino", "microcontroller_board", ["iot", "security", "wifi", "professional"]),
    "Portenta Machine Control": ("Arduino", "industrial_controller", ["24v", "machine-control", "can", "rs485", "ethernet"]),
    "Arduino Nicla Vision": ("Arduino", "microcontroller_board", ["vision", "tinyml", "camera", "compact"]),
    "Arduino Nicla Voice": ("Arduino", "microcontroller_board", ["audio", "wake-word", "ble", "low-power"]),
    "ESP32-S3-DevKitC-1": ("Espressif", "microcontroller_board", ["wifi", "ble", "usb", "tinyml", "hmi"]),
    "ESP32-C3-DevKitM-1": ("Espressif", "microcontroller_board", ["wifi", "ble", "risc-v", "low-cost"]),
    "ESP32-C6-DevKitC-1": ("Espressif", "microcontroller_board", ["wifi6", "ble", "matter", "thread", "zigbee"]),
    "ESP32-H2-DevKitM": ("Espressif", "microcontroller_board", ["ble", "thread", "zigbee", "matter", "no-wifi"]),
    "ESP32-P4 Function EV Board": ("Espressif", "evaluation_board", ["hmi", "vision", "display", "camera", "no-radio"]),
    "NodeMCU ESP8266": ("Espressif/community", "microcontroller_board", ["wifi", "legacy", "low-cost"]),
    "Raspberry Pi 5": ("Raspberry Pi", "single_board_computer", ["linux", "gateway", "vision", "edge-computing"]),
    "Raspberry Pi Zero 2 W": ("Raspberry Pi", "single_board_computer", ["linux", "wifi", "compact", "camera"]),
    "Raspberry Pi Compute Module 5": ("Raspberry Pi", "system_on_module", ["linux", "product", "pcie", "mipi"]),
    "Raspberry Pi Pico 2 W": ("Raspberry Pi", "microcontroller_board", ["wifi", "ble", "pio", "security"]),
    "STM32 Nucleo-F446RE": ("STMicroelectronics", "microcontroller_board", ["control", "dsp", "can", "stm32"]),
    "STM32 Nucleo-H743ZI2": ("STMicroelectronics", "microcontroller_board", ["high-performance", "ethernet", "can-fd", "stm32"]),
    "STM32 Nucleo-N657X0-Q": ("STMicroelectronics", "microcontroller_board", ["edge-ai", "vision", "camera", "stm32"]),
    "Teensy 4.1": ("PJRC", "microcontroller_board", ["real-time", "audio", "can", "ethernet", "fast"]),
    "BBC micro:bit v2": ("Micro:bit Educational Foundation", "microcontroller_board", ["education", "ble", "sensors", "simple"]),
    "Nordic nRF52840 DK": ("Nordic Semiconductor", "development_kit", ["ble", "thread", "zigbee", "nfc", "low-power"]),
    "Nordic nRF5340 DK": ("Nordic Semiconductor", "development_kit", ["ble", "thread", "zigbee", "le-audio", "security"]),
    "TI C2000 LaunchPad": ("Texas Instruments", "development_kit", ["motor-control", "pfc", "inverter", "power-control"]),
    "NXP FRDM-MCXN947": ("NXP", "development_kit", ["control", "security", "edge-ai", "ethernet", "can"]),
    "Microchip Curiosity Nano AVR128DA48": ("Microchip", "development_kit", ["avr", "8-bit", "analog", "education"]),
    "Infineon PSoC 6 Pioneer Kit": ("Infineon", "development_kit", ["mixed-signal", "touch", "ble", "configurable"]),
    "BeagleBone Black": ("BeagleBoard.org", "single_board_computer", ["linux", "industrial", "pru", "deterministic-io"]),
    "NVIDIA Jetson Orin Nano": ("NVIDIA", "edge_ai_computer", ["vision", "ai", "robotics", "gpu"]),
    "Google Coral Dev Board / USB Accelerator": ("Google Coral", "edge_ai_accelerator", ["tensorflow-lite", "edge-ai", "usb", "pcie"]),
    "Adafruit Feather RP2040": ("Adafruit", "microcontroller_board", ["rp2040", "battery", "compact", "featherwing"]),
    "Seeed XIAO ESP32C6": ("Seeed Studio", "microcontroller_board", ["matter", "thread", "zigbee", "wifi6", "compact"]),
    "M5Stack CoreS3": ("M5Stack", "integrated_controller", ["hmi", "touch", "audio", "wifi", "ble"]),
    "Particle Boron": ("Particle", "microcontroller_board", ["cellular", "lte-m", "nb-iot", "cloud", "ota"]),
    "Digilent Arty A7": ("Digilent", "fpga_board", ["fpga", "artix-7", "dsp", "soft-core"]),
    "Terasic DE10-Nano": ("Terasic", "soc_fpga_board", ["fpga", "linux", "heterogeneous", "vision"]),
    "Lattice iCE40 / UPduino": ("Lattice/community", "fpga_board", ["fpga", "open-source", "compact", "education"]),
}

OFFICIAL_SOURCES = [
    ("OFF-ARDUINO-DOCS", "Arduino Documentation", "https://docs.arduino.cc/"),
    ("OFF-ARDUINO-HARDWARE", "Arduino hardware documentation", "https://docs.arduino.cc/hardware/"),
    ("OFF-ESP-SOCS", "Espressif SoCs", "https://www.espressif.com/en/products/socs"),
    ("OFF-ESP-DOCS", "Espressif documentation", "https://docs.espressif.com/"),
    ("OFF-RPI-DOCS", "Raspberry Pi documentation", "https://www.raspberrypi.com/documentation/"),
    ("OFF-RPI-DATASHEETS", "Raspberry Pi datasheets", "https://datasheets.raspberrypi.com/"),
    ("OFF-MICROPYTHON", "MicroPython documentation", "https://docs.micropython.org/"),
    ("OFF-CIRCUITPYTHON", "CircuitPython documentation", "https://docs.circuitpython.org/"),
    ("OFF-ST-NUCLEO", "STMicroelectronics Nucleo boards", "https://www.st.com/en/evaluation-tools/stm32-nucleo-boards.html"),
    ("OFF-NORDIC-DK", "Nordic development kits", "https://www.nordicsemi.com/Products/Development-hardware"),
    ("OFF-PJRC-TEENSY", "PJRC Teensy", "https://www.pjrc.com/teensy/"),
    ("OFF-MICROBIT", "BBC micro:bit technical information", "https://tech.microbit.org/"),
    ("OFF-BEAGLEBOARD", "BeagleBoard documentation", "https://docs.beagleboard.org/"),
    ("OFF-NVIDIA-JETSON", "NVIDIA Jetson documentation", "https://docs.nvidia.com/jetson/"),
]


def clean(value: str) -> str:
    value = unicodedata.normalize("NFC", value or "")
    value = value.replace("\u2010", "-").replace("\u2011", "-").replace("\u00ad", "")
    value = re.sub(r"\bT eensy\b", "Teensy", value)
    value = re.sub(r"\bT erasic\b", "Terasic", value)
    value = re.sub(r"\bT elemetr", "Telemetr", value)
    value = re.sub(r"\bT ensorFlow\b", "TensorFlow", value)
    value = re.sub(r"\bIo T\b", "IoT", value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r" ?\n ?", " ", value)
    return value.strip()


def slug(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value)
    folded = "".join(char for char in folded if not unicodedata.combining(char)).lower()
    return re.sub(r"[^a-z0-9]+", "-", folded).strip("-")


def split_interfaces(value: str) -> list[str]:
    return [item.strip() for item in re.split(r",|;", value) if item.strip()]


def between(text: str, start: str, end: str) -> str:
    match = re.search(re.escape(start) + r"\s*(.*?)\s*" + re.escape(end), text, flags=re.S)
    if not match:
        raise ValueError(f"No se encontró el bloque {start!r} -> {end!r}")
    return clean(match.group(1))


def parse_page(raw: str, pdf_page: int) -> dict:
    raw = raw.replace("\r", "")
    title_match = re.search(r"^22\.(\d+)\s+(.+)$", raw, flags=re.M)
    if not title_match:
        raise ValueError(f"Página {pdf_page}: título de ficha no reconocido")
    entry_number = int(title_match.group(1))
    name = clean(title_match.group(2))
    if name not in PLATFORM_META:
        raise ValueError(f"Página {pdf_page}: plataforma sin curación: {name}")
    manufacturer, platform_class, tags = PLATFORM_META[name]
    architecture = between(raw, "Arquitectura", "Lógica/alimentación")
    logic_and_power = between(raw, "Lógica/alimentación", "Interfaces")
    interfaces = between(raw, "Interfaces", "Uso recomendado")
    recommended_use = between(raw, "Uso recomendado", "Criterio de selección")
    risk = between(raw, "Precaución", "Pruebas mínimas de recepción")
    return {
        "id": f"emb-{slug(name)}",
        "name": name,
        "manufacturer": manufacturer,
        "platform_class": platform_class,
        "architecture": architecture,
        "logic_and_power": logic_and_power,
        "interfaces": split_interfaces(interfaces),
        "recommended_use": recommended_use,
        "primary_risk": risk,
        "tags": tags,
        "source_refs": ["SRC-EMBEDDED-ENCYCLOPEDIA-2026"],
        "source_locator": {
            "pdf_page": pdf_page,
            "document_page": pdf_page - 7,
            "section": f"22.{entry_number}",
        },
        "review": {
            "status": "source_identified",
            "confidence": 0.82,
            "basis": "Ficha importada de la enciclopedia aportada; revisión oficial por modelo y revisión de placa aún pendiente.",
            "requires_exact_revision_check": True,
        },
    }


def write_json(name: str, value: dict) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--allow-different-source", action="store_true")
    args = parser.parse_args()
    raw_pdf = args.pdf.read_bytes()
    digest = hashlib.sha256(raw_pdf).hexdigest()
    if digest != EXPECTED_SHA256 and not args.allow_different_source:
        raise SystemExit(f"PDF no reconocido: SHA-256 {digest}")
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise SystemExit("Este importador requiere pypdf") from error
    reader = PdfReader(args.pdf)
    if len(reader.pages) != 115:
        raise SystemExit(f"Se esperaban 115 páginas y hay {len(reader.pages)}")
    records = [parse_page(reader.pages[page - 1].extract_text() or "", page) for page in range(FIRST_PDF_PAGE, LAST_PDF_PAGE + 1)]
    if len(records) != 41 or len({item["id"] for item in records}) != 41:
        raise SystemExit("El catálogo importado no contiene 41 fichas únicas")

    catalog = {
        "schema_version": "1.0",
        "catalog_version": "2026.08.1",
        "generated_at": "2026-08-23",
        "count": len(records),
        "review_policy": {
            "source_identified": "Dato trazado hasta una fuente entregada, todavía no contrastado ficha a ficha con la documentación oficial de la revisión exacta.",
            "reviewed": "Dato contrastado con documentación oficial del fabricante para el modelo y revisión indicados.",
            "selection_rule": "Una coincidencia orienta la preselección; nunca sustituye la verificación de pinout, alimentación, revisión, memoria, radio, carrier y condiciones ambientales.",
        },
        "shared_reception_checks": [
            "Identificar revisión, módulo y memoria montada.",
            "Medir rails y consumo durante reset y arranque.",
            "Cargar firmware mínimo y registrar el log de arranque.",
            "Verificar GPIO, UART, I2C/SPI y la conectividad declarada.",
            "Guardar versiones de bootloader, core o SDK y toolchain.",
        ],
        "shared_integration_requirements": [
            "Diseñar protección, puntos de prueba y conector de programación o depuración antes de cerrar PCB o carcasa.",
            "Definir desde el inicio una estrategia de actualización y recuperación.",
            "Validar RF, térmica, EMC y fabricación antes de sustituir un kit por módulo o diseño propio.",
            "No conectar señales industriales, red o 24 V a GPIO sin una interfaz adaptada, protegida y documentada.",
        ],
        "records": records,
    }
    sources = {
        "schema_version": "1.0",
        "sources": [{
            "id": "SRC-EMBEDDED-ENCYCLOPEDIA-2026",
            "title": "Enciclopedia profesional Arduino, ESP, Raspberry Pi y plataformas embebidas — Edición 2026",
            "publisher": "REPLACRO / Doctor Micro",
            "kind": "user_supplied_pdf",
            "sha256": digest,
            "page_count": 115,
            "catalog_pages": [69, 109],
            "official_sources_page": 114,
            "status": "source_identified",
            "redistribution": "metadata_and_structured_facts_only",
        }] + [{"id": source_id, "title": title, "kind": "official_reference", "url": url, "status": "pending_record_linking"} for source_id, title, url in OFFICIAL_SOURCES],
    }
    guides = {
        "schema_version": "1.0",
        "guide_version": "2026.08.1",
        "selection_questions": [
            "¿Necesita tiempo real determinista, Linux o ambos?",
            "¿Qué interfaces son obligatorias y con qué niveles eléctricos?",
            "¿Qué presupuesto de potencia, arranque y batería existe?",
            "¿Necesita radio y qué homologación, alcance y coexistencia exige?",
            "¿Qué ciclo de vida, trazabilidad, actualización y recuperación requiere el producto?",
            "¿El prototipo se quedará como kit o migrará a módulo o PCB propia?",
        ],
        "hard_stops": [
            "Modelo o revisión de placa desconocidos cuando el pinout o la tolerancia eléctrica condicionan la conexión.",
            "Conexión directa de 5 V a GPIO de 3,3 V sin tolerancia oficial confirmada.",
            "Conexión directa de 24 V, red, motores, contactores o cargas inductivas a una placa lógica.",
            "Presupuesto de corriente o secuencia de alimentación sin verificar.",
            "Uso como única función de seguridad sin arquitectura y certificación adecuadas.",
        ],
        "diagnostic_flow": [
            "Identificar exactamente placa, revisión, módulo, memoria y carrier.",
            "Separar alimentación, arranque, firmware, interfaz y carga externa.",
            "Medir los rails antes de conectar periféricos.",
            "Capturar el log de arranque y registrar versiones.",
            "Probar una interfaz cada vez con cableado corto y carga conocida.",
            "Documentar el resultado y la condición de prueba.",
        ],
    }
    manifest = {
        "schema_version": "1.0",
        "name": "super-tecnico-embedded-platforms",
        "title": "REPLACOR Core · Plataformas embebidas",
        "version": "0.1.0",
        "provider_neutral": True,
        "embedded_ai_model": False,
        "remote_execution": True,
        "browser_available": True,
        "purpose": "Búsqueda, consulta y preselección trazable de placas y plataformas embebidas.",
        "instructions": "Buscar primero; usar recommend solo como preselección. Conservar review.status, source_locator y primary_risk. No convertir source_identified en reviewed ni asumir compatibilidad por coincidencia de interfaz.",
        "public_data": ["catalog.json", "sources.json", "guides.json"],
        "tools": [
            {"name": "supertecnico_search_embedded_platforms", "description": "Busca por nombre, fabricante, arquitectura, interfaz o uso.", "state": "public_http_beta", "http_endpoint": "../../api/index.php?action=embedded-search", "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}, "input_schema": {"type": "object", "additionalProperties": False, "required": ["query"], "properties": {"query": {"type": "string", "minLength": 1, "maxLength": 160}, "manufacturer": {"type": "string", "maxLength": 80}, "platform_class": {"type": "string", "maxLength": 60}, "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 8}}}},
            {"name": "supertecnico_get_embedded_platform", "description": "Devuelve una ficha completa con riesgos, recepción, integración y procedencia.", "state": "public_http_beta", "http_endpoint": "../../api/index.php?action=embedded-get", "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}, "input_schema": {"type": "object", "additionalProperties": False, "required": ["platform_id"], "properties": {"platform_id": {"type": "string", "minLength": 3, "maxLength": 100}}}},
            {"name": "supertecnico_recommend_embedded_platforms", "description": "Ordena candidatos por caso de uso e interfaces sin declarar una selección definitiva.", "state": "public_http_beta", "http_endpoint": "../../api/index.php?action=embedded-recommend", "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}, "input_schema": {"type": "object", "additionalProperties": False, "required": ["use_case"], "properties": {"use_case": {"type": "string", "minLength": 3, "maxLength": 300}, "required_interfaces": {"type": "string", "maxLength": 200}, "needs_linux": {"type": "boolean", "default": False}, "limit": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5}}}},
        ],
        "limitations": [
            "No selecciona una placa final sin requisitos suficientes.",
            "No garantiza compatibilidad eléctrica, mecánica, normativa ni de software.",
            "Las fichas importadas requieren contraste oficial por revisión exacta antes de diseñar hardware.",
        ],
    }
    discovery = {
        "schema_version": "1.0",
        "id": "replacor-embedded-platform-core",
        "title": "Plataformas embebidas",
        "status": "public_browser_and_http_beta",
        "provider_neutral": True,
        "human_entry": "../../plataformas-embebidas.html",
        "machine_contract": "tool-manifest.json",
        "catalog": "catalog.json",
        "sources": "sources.json",
        "guides": "guides.json",
        "capabilities": ["platform_search", "traceable_platform_record", "documentary_preselection", "reception_checks", "integration_safety"],
        "http": {"search": "../../api/index.php?action=embedded-search", "get": "../../api/index.php?action=embedded-get", "recommend": "../../api/index.php?action=embedded-recommend"},
        "quality": {"records": 41, "record_status": "source_identified", "exact_revision_official_review": "pending"},
        "bulk_export": "not_offered_by_api",
    }
    openapi = {
        "openapi": "3.1.0",
        "info": {"title": "Super Técnico Embedded Platforms API", "version": "0.1.0-beta.1"},
        "servers": [{"url": "../../api/index.php"}],
        "paths": {
            "/?action=embedded-search": {"get": {"operationId": "supertecnico_search_embedded_platforms", "parameters": [{"name": "q", "in": "query", "required": True, "schema": {"type": "string", "maxLength": 160}}, {"name": "limit", "in": "query", "schema": {"type": "integer", "minimum": 1, "maximum": 20}}], "responses": {"200": {"description": "Coincidencias compactas y trazables"}}}},
            "/?action=embedded-get": {"get": {"operationId": "supertecnico_get_embedded_platform", "parameters": [{"name": "platform_id", "in": "query", "required": True, "schema": {"type": "string", "maxLength": 100}}], "responses": {"200": {"description": "Ficha completa"}, "404": {"description": "No encontrada"}}}},
            "/?action=embedded-recommend": {"get": {"operationId": "supertecnico_recommend_embedded_platforms", "parameters": [{"name": "use_case", "in": "query", "required": True, "schema": {"type": "string", "maxLength": 300}}, {"name": "required_interfaces", "in": "query", "schema": {"type": "string", "maxLength": 200}}, {"name": "needs_linux", "in": "query", "schema": {"type": "boolean"}}], "responses": {"200": {"description": "Preselección documental con advertencias"}}}},
        },
    }
    write_json("catalog.json", catalog)
    write_json("sources.json", sources)
    write_json("guides.json", guides)
    write_json("tool-manifest.json", manifest)
    write_json("discovery.json", discovery)
    write_json("discovery.openapi.json", openapi)
    print(json.dumps({"records": len(records), "sha256": digest, "output": str(OUTPUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
