#!/usr/bin/env python3
"""Build the reviewed component supplement used by the public catalogue.

The private SQLite database remains the master source.  This script adds a
curated, reproducible layer for common power modules, MOSFETs and array
drivers that are especially useful when repairing HVAC electronics.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "component_additions.json"
GENERATION = "component-expansion-v2"
RETRIEVED_DATE = "2026-07-29"


def normalize(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", value.upper())


def specification(
    key: str,
    name: str,
    *,
    maximum: float | None = None,
    typical: float | None = None,
    minimum: float | None = None,
    text: str | None = None,
    unit: str | None = None,
    conditions: str = "",
    confidence: float = 0.96,
) -> dict[str, Any]:
    return {
        "spec_key": key,
        "name_es": name,
        "minimum_value": minimum,
        "typical_value": typical,
        "maximum_value": maximum,
        "text_value": text,
        "unit": unit,
        "conditions": conditions,
        "confidence_score": confidence,
        "notes": None,
    }


def component(
    part: str,
    manufacturer: str,
    category: str,
    *,
    subtype: str,
    description: str,
    source_title: str,
    source_url: str,
    packages: Iterable[str] = (),
    aliases: Iterable[str] = (),
    voltage: float | None = None,
    current: float | None = None,
    power: float | None = None,
    resistance: float | None = None,
    topology: str | None = None,
    applications: Iterable[str] = (),
    datasheet_url: str | None = None,
    quality: str = "oficial_serie",
) -> dict[str, Any]:
    package_list = list(dict.fromkeys(packages))
    specifications: list[dict[str, Any]] = []
    if voltage is not None:
        specifications.append(
            specification(
                "voltage_max",
                "Tensión máxima documentada",
                maximum=voltage,
                unit="V",
            )
        )
    if current is not None:
        specifications.append(
            specification(
                "current_max",
                "Corriente nominal o máxima documentada",
                maximum=current,
                unit="A",
                conditions="Consulta las condiciones exactas en la fuente oficial.",
            )
        )
    if power is not None:
        specifications.append(
            specification(
                "power",
                "Potencia de motor orientativa documentada",
                maximum=power,
                unit="W",
                conditions="Valor de selección del fabricante; depende de la aplicación.",
            )
        )
    if resistance is not None:
        specifications.append(
            specification(
                "rds_on",
                "Resistencia en conducción documentada",
                typical=resistance,
                unit="Ω",
                conditions="Comprueba si el fabricante la expresa como típica o máxima.",
            )
        )
    if topology:
        specifications.append(
            specification(
                "topology",
                "Configuración",
                text=topology,
                confidence=0.98,
            )
        )

    return {
        "part_number": part,
        "manufacturer": manufacturer,
        "category": category,
        "subtype": subtype,
        "description": description,
        "packages": package_list,
        "markings": [],
        "aliases": list(dict.fromkeys(aliases)),
        "quality": quality,
        "quality_rank": 7 if quality == "oficial" else 6,
        "confidence": 0.98 if quality == "oficial" else 0.96,
        "official": True,
        "generic": False,
        "voltage_max_v": voltage,
        "current_max_a": current,
        "power_max_w": power,
        "rds_on_max_ohm": resistance,
        "frequency_hz": None,
        "lifecycle_status": "Consultar estado y sufijo exacto con el fabricante",
        "notes": (
            "Referencia documental para identificación. Confirma sufijo, encapsulado, "
            "patillaje, límites térmicos y condiciones del datasheet antes de sustituir."
        ),
        "datasheet_url": datasheet_url or source_url,
        "specifications": specifications,
        "package_details": [
            {
                "name": package,
                "family": package.split("-")[0] if "-" in package else package,
                "pin_count": None,
                "mount_type": None,
                "pinout_variant": None,
                "primary_package": int(index == 0),
                "notes": "Confirma la variante mecánica y el sufijo exacto.",
            }
            for index, package in enumerate(package_list)
        ],
        "marking_details": [],
        "pinouts": [],
        "applications": list(applications),
        "equivalents": [],
        "verification": [],
        "source": {
            "title": source_title,
            "publisher": manufacturer,
            "url": source_url,
            "type": "documentación oficial del fabricante",
            "authority": 5,
            "retrieved_date": RETRIEVED_DATE,
        },
        "generation": GENERATION,
    }


def driver_components() -> list[dict[str, Any]]:
    ti_source = "https://www.ti.com/product/ULN2003A"
    ti_compare = (
        "https://www.ti.com/compare-products/?id=105&mode=compare-gpn"
        "&partList=ULN2003A%2CTPL7407LA%2CULN2003AI%2CULQ2003A&type=GPT"
    )
    toshiba_source = (
        "https://toshiba.semicon-storage.com/info/"
        "TBD62004AFG_datasheet_en_20150724.pdf?did=29886&prodName=TBD62004AFG"
    )
    rows = [
        component(
            "ULN2003A",
            "Texas Instruments",
            "Driver de potencia",
            subtype="Matriz Darlington de siete canales",
            description="Matriz de siete transistores Darlington de baja salida para cargas inductivas.",
            source_title="ULN2003A 50-V, 7-channel Darlington transistor array",
            source_url=ti_source,
            datasheet_url="https://www.ti.com/lit/ds/symlink/uln2003a.pdf",
            packages=("PDIP-16", "SOIC-16", "TSSOP-16"),
            aliases=("ULN2003", "ULN2003AD", "ULN2003AN", "ULN2003APW"),
            voltage=50,
            current=0.5,
            topology="7 canales Darlington de salida abierta con diodos de rueda libre",
            applications=("Relés", "Electroválvulas", "Motores paso a paso", "Indicadores"),
            quality="oficial",
        ),
        component(
            "ULN2003AI",
            "Texas Instruments",
            "Driver de potencia",
            subtype="Matriz Darlington industrial de siete canales",
            description="Versión industrial de la matriz Darlington de siete canales y 50 V.",
            source_title="Comparador oficial ULN2003A, ULN2003AI, ULQ2003A y TPL7407LA",
            source_url=ti_compare,
            packages=("SOIC-16", "TSSOP-16"),
            aliases=("ULN2003AIPW", "ULN2003AID"),
            voltage=50,
            current=0.5,
            topology="7 canales Darlington",
        ),
        component(
            "ULQ2003A",
            "Texas Instruments",
            "Driver de potencia",
            subtype="Matriz Darlington cualificada para automoción",
            description="Matriz Darlington de siete canales y 50 V para entornos exigentes.",
            source_title="Comparador oficial ULN2003A, ULN2003AI, ULQ2003A y TPL7407LA",
            source_url=ti_compare,
            packages=("SOIC-16", "TSSOP-16"),
            aliases=("ULQ2003AD", "ULQ2003APW"),
            voltage=50,
            current=0.5,
            topology="7 canales Darlington",
        ),
        component(
            "TPL7407LA",
            "Texas Instruments",
            "Driver de potencia",
            subtype="Matriz NMOS de siete canales",
            description="Driver de lado bajo con siete canales NMOS para cargas inductivas.",
            source_title="TPL7407LA 30-V 7-channel NMOS low-side driver",
            source_url="https://www.ti.com/product/TPL7407LA",
            packages=("TSSOP-16",),
            aliases=("TPL7407LAPW",),
            voltage=30,
            current=0.6,
            topology="7 canales NMOS de lado bajo",
            quality="oficial",
        ),
        component(
            "ULN2803A",
            "Texas Instruments",
            "Driver de potencia",
            subtype="Matriz Darlington de ocho canales",
            description="Matriz de ocho transistores Darlington para relés, lámparas y motores.",
            source_title="TI peripheral drivers selection guide including ULN2803A",
            source_url="https://www.ti.com/lit/an/slva927a/slva927a.pdf",
            datasheet_url="https://www.ti.com/lit/ds/symlink/uln2803a.pdf",
            packages=("PDIP-18", "SOIC-18"),
            aliases=("ULN2803", "ULN2803ADW", "ULN2803AN"),
            voltage=50,
            current=0.5,
            topology="8 canales Darlington de salida abierta con diodos de rueda libre",
            quality="oficial",
        ),
    ]
    for part, package, aliases in (
        ("TBD62003AFG", "SOP-16", ("TBD62003A",)),
        ("TBD62003AFWG", "SSOP-16", ()),
        ("TBD62003APG", "DIP-16", ()),
        ("TBD62004AFG", "SOP-16", ("TBD62004A",)),
        ("TBD62004AFWG", "SSOP-16", ()),
        ("TBD62004APG", "DIP-16", ()),
    ):
        rows.append(
            component(
                part,
                "Toshiba Electronic Devices & Storage",
                "Driver de potencia",
                subtype="Matriz DMOS de siete canales",
                description="Matriz de siete salidas DMOS de lado bajo para cargas inductivas.",
                source_title="TBD62003A and TBD62004A series official datasheet",
                source_url=toshiba_source,
                packages=(package,),
                aliases=aliases,
                voltage=50,
                topology="7 canales DMOS de lado bajo",
                quality="oficial_serie",
            )
        )
    return rows


def ipm_components() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    infineon_source = "https://www.infineon.com/product-table/intelligent-power-modules-ipm"
    infineon = [
        ("IM818-SCC", 1200, 5, 1400, "DIP 36x23D", "CIPOS Maxi; IGBT; trifásico, emisor abierto"),
        ("IM818-MCC", 1200, 10, 2200, "DIP 36x23D", "CIPOS Maxi; IGBT; trifásico, emisor abierto"),
        ("IM818-LCC", 1200, 15, 3000, "DIP 36x23D", "CIPOS Maxi; IGBT; trifásico, emisor abierto"),
        ("IM12B10CC1", 1200, 10, 2200, "DIP 36x23D", "CIPOS Maxi; IGBT; trifásico, emisor abierto"),
        ("IM12B15CC1", 1200, 15, 3000, "DIP 36x23D", "CIPOS Maxi; IGBT; trifásico, emisor abierto"),
        ("IM12B20EC1", 1200, 20, 4000, "DIP 36x23DA", "CIPOS Maxi; IGBT; trifásico, emisor abierto"),
        ("IM12S60EA2", 1200, 25, 7600, "DIP 36x23DA", "CIPOS Maxi; CoolSiC; trifásico"),
        ("IM241-M6S1B", 600, 4, 325, "SOP 29x12", "CIPOS Micro; IGBT; trifásico, emisor abierto"),
        ("IM241-L6S1B", 600, 6, 450, "SOP 29x12", "CIPOS Micro; IGBT; trifásico, emisor abierto"),
        ("IM323-L6G", 600, 15, 1200, "CIPOS Tiny", "CIPOS Tiny; IGBT; trifásico, emisor abierto"),
        ("IKCM10L60GA", 600, 10, 1200, "DIP 36x21", "CIPOS Mini; IGBT; trifásico, emisor abierto"),
        ("IKCM15F60GA", 600, 15, 1600, "DIP 36x21", "CIPOS Mini; IGBT; trifásico, emisor abierto"),
        ("IKCM15L60GA", 600, 15, 1600, "DIP 36x21", "CIPOS Mini; IGBT; trifásico, emisor abierto"),
        ("IKCM15L60GD", 600, 15, 2200, "DIP 36x21D", "CIPOS Mini; IGBT; trifásico, emisor abierto"),
        ("IKCM20L60GA", 600, 20, 1800, "DIP 36x21", "CIPOS Mini; IGBT; trifásico, emisor abierto"),
        ("IKCM20L60GD", 600, 20, 2400, "DIP 36x21D", "CIPOS Mini; IGBT; trifásico, emisor abierto"),
        ("IKCM30F60GA", 600, 30, 2000, "DIP 36x21", "CIPOS Mini; IGBT; trifásico, emisor abierto"),
        ("IKCM30F60GD", 600, 30, 2600, "DIP 36x21D", "CIPOS Mini; IGBT; trifásico, emisor abierto"),
        ("IGCM10F60GA", 600, 10, 1000, "DIP 36x21", "CIPOS Mini; IGBT; trifásico, emisor abierto"),
        ("IGCM15F60GA", 600, 15, 1200, "DIP 36x21", "CIPOS Mini; IGBT; trifásico, emisor abierto"),
        ("IGCM20F60GA", 600, 20, 1600, "DIP 36x21", "CIPOS Mini; IGBT; trifásico, emisor abierto"),
        ("IKCM10H60GA", 600, 10, 1000, "DIP 36x21", "CIPOS Mini; IGBT; trifásico, emisor abierto"),
        ("IKCM15H60GA", 600, 15, 1200, "DIP 36x21", "CIPOS Mini; IGBT; trifásico, emisor abierto"),
        ("IGCM04G60HA", 600, 4, 600, "CIPOS Mini", "CIPOS Mini; IGBT; trifásico, emisor abierto"),
        ("IFCM10P60GD", 600, 10, 1200, "DIP 36x21D", "CIPOS Mini; PFC integrado"),
        ("IFCM15P60GD", 600, 15, 1800, "DIP 36x21D", "CIPOS Mini; PFC integrado"),
        ("IFCM20U65GD", 650, 20, 4400, "DIP 36x21D", "CIPOS Mini; PFC intercalado"),
        ("IKCM20R60GD", 600, 20, 2400, "DIP 36x21D", "CIPOS Mini; inversor asimétrico bifásico"),
        ("IM564-X6D", 600, 20, 2400, "DIP 36x21D", "CIPOS Mini; PFC integrado"),
        ("IM535-U6D", 600, 30, 3000, "DIP 36x21D", "CIPOS Mini; trifásico, emisor abierto"),
        ("IM06B15AC1", 600, 15, 2000, "DIP 36x23", "CIPOS Maxi; IGBT; trifásico"),
        ("IM06B20AC1", 600, 20, 2400, "DIP 36x23", "CIPOS Maxi; IGBT; trifásico"),
        ("IM06B30AC1", 600, 30, 2600, "DIP 36x23", "CIPOS Maxi; IGBT; trifásico"),
        ("IM06B50GC1", 600, 50, 6000, "DIP 36x23", "CIPOS Maxi; IGBT; trifásico"),
    ]
    for part, voltage, current, power, package, topology in infineon:
        rows.append(
            component(
                part,
                "Infineon Technologies",
                "Módulo de potencia IPM",
                subtype="Módulo inteligente de potencia CIPOS",
                description=f"IPM {topology}, {voltage} V y {current} A.",
                source_title="Infineon intelligent power modules official product table",
                source_url=infineon_source,
                packages=(package,),
                voltage=voltage,
                current=current,
                power=power,
                topology=topology,
                applications=("Compresores inverter", "Motores trifásicos", "Climatización y bombas de calor"),
            )
        )

    st_source = "https://www.st.com/en/power-modules-and-ipm/sllimm-2nd-series/products.html"
    st_rows = [
        ("STGIPN3H60", 600, 3, "NDIP-26L", "IGBT trifásico SLLIMM-nano"),
        ("STGIPQ8C60T-HZ", 600, 8, "N2DIP-26L tipo Z", "IGBT trifásico SLLIMM-nano"),
        ("STGIK10M120T", 1200, 10, "SDIPHP-30L", "IGBT trifásico SLLIMM"),
        ("STGIB10CH60TS-L", 600, 15, "SDIP2F-26L", "IGBT trifásico SLLIMM 2"),
        ("STGIB20M60S-X", 600, 25, "SDIP2B-26L", "IGBT trifásico SLLIMM 2"),
        ("STGIB15CH60S-L", 600, 20, "SDIP2F-26L", "IGBT trifásico SLLIMM 2"),
        ("STGIB30M60S-X", 600, 35, "SDIP2B-26L", "IGBT trifásico SLLIMM 2"),
        ("STIB1560DM2-Z", 600, 15, "NDIP-26L tipo Z", "MOSFET trifásico SLLIMM 2"),
        ("STIB1060DM2T-LZ", 600, 10, "NDIP-26L tipo Z", "MOSFET trifásico SLLIMM 2"),
        ("STIB1560DM2T-LZ", 600, 15, "NDIP-26L tipo Z", "MOSFET trifásico SLLIMM 2"),
        ("STGIF7CH60TS-L", 600, 10, "SDIP2F-26L", "IGBT trifásico SLLIMM 2"),
        ("STGIB30M60S-L", 600, 35, "SDIP2F-26L", "IGBT trifásico SLLIMM 2"),
        ("STGIB8CH60TS-E", 600, 12, "SDIP2F-26L", "IGBT trifásico SLLIMM 2"),
        ("STGIB8CH60TS-L", 600, 12, "SDIP2F-26L", "IGBT trifásico SLLIMM 2"),
        ("STGIF7CH60TS-X", 600, 10, "SDIP2B-26L", "IGBT trifásico SLLIMM 2"),
        ("STGIF5CH60TS-X", 600, 8, "SDIP2B-26L", "IGBT trifásico SLLIMM 2"),
        ("STGIF5CH60TS-L", 600, 8, "SDIP2F-26L", "IGBT trifásico SLLIMM 2"),
        ("STGIB20M60TS-L", 600, 25, "SDIP2F-26L", "IGBT trifásico SLLIMM 2"),
        ("STGIB30M60TS-L", 600, 35, "SDIP2F-26L", "IGBT trifásico SLLIMM 2"),
        ("STGIF10CH60TS-L", 600, 15, "SDIP2F-26L", "IGBT trifásico SLLIMM 2"),
        ("STGIB15CH60TS-L", 600, 20, "SDIP2F-26L", "IGBT trifásico SLLIMM 2"),
        ("STGIF5CH60S-X", 600, 8, "SDIP2B-26L", "IGBT trifásico SLLIMM 2"),
        ("STGIF10CH60S-L", 600, 15, "SDIP2F-26L", "IGBT trifásico SLLIMM 2"),
        ("STGIPS10K60", 600, 10, "SDIP-25L", "IGBT trifásico SLLIMM"),
        ("STGIPS14K60", 600, 14, "SDIP-25L", "IGBT trifásico SLLIMM"),
        ("STGIPS20K60", 600, 18, "SDIP-25L", "IGBT trifásico SLLIMM"),
        ("STGIPL20K60", 600, 20, "SDIP-38L", "IGBT trifásico SLLIMM"),
        ("STGIPS40W60L1", 600, 40, "SDIP2F-26L", "IGBT monofásico SLLIMM"),
    ]
    st_exact = {
        "STGIPN3H60": "https://www.st.com/en/power-modules-and-ipm/stgipn3h60.html",
        "STGIPQ8C60T-HZ": "https://www.st.com/resource/en/datasheet/stgipq8c60t-hz.pdf",
        "STGIK10M120T": "https://www.st.com/resource/en/datasheet/stgik10m120t.pdf",
        "STGIPS40W60L1": "https://www.st.com/en/power-modules-and-ipm/stgips40w60l1.html",
    }
    for part, voltage, current, package, topology in st_rows:
        url = st_exact.get(part, st_source)
        rows.append(
            component(
                part,
                "STMicroelectronics",
                "Módulo de potencia IPM",
                subtype="Módulo inteligente de potencia SLLIMM",
                description=f"IPM {topology}, {voltage} V y {current} A.",
                source_title="STPOWER SLLIMM intelligent modules official documentation",
                source_url=url,
                datasheet_url=url,
                packages=(package,),
                voltage=voltage,
                current=current,
                topology=topology,
                applications=("Compresores inverter", "Motores trifásicos", "Climatización"),
            )
        )

    onsemi_source = (
        "https://www.onsemi.com/design/tools-software/"
        "product-recommendation-tools-plus/ipm/products"
    )
    onsemi = [
        ("FSB50250AS", 500, 2.5, "SMD-023"),
        ("FSB50250AT", 500, 2.5, "SMD-023"),
        ("FSB50250BS", 500, 2.5, "SMD-023"),
        ("FSB50450AS", 500, 4, "SMD-023"),
        ("FSB50550BB", 500, 3, "DIP-021"),
        ("FSB50550BS", 500, 3, "SMD-023"),
        ("FSBB20CH60D", 600, 20, "SPM27"),
        ("FSBB30CH60C", 600, 30, "SPM27"),
    ]
    for part, voltage, current, package in onsemi:
        datasheet = {
            "FSBB20CH60D": "https://www.onsemi.com/download/data-sheet/pdf/fsbb20ch60d-d.pdf",
            "FSBB30CH60C": "https://www.onsemi.com/pdf/datasheet/fsbb30ch60c-d.pdf",
        }.get(part)
        rows.append(
            component(
                part,
                "onsemi",
                "Módulo de potencia IPM",
                subtype="Módulo inteligente de potencia Motion SPM",
                description=f"IPM trifásico para motor, {voltage} V y {current} A.",
                source_title="onsemi Intelligent Power Module official selector",
                source_url=datasheet or onsemi_source,
                datasheet_url=datasheet or onsemi_source,
                packages=(package,),
                voltage=voltage,
                current=current,
                topology="Inversor trifásico con etapa de control integrada",
                applications=("Compresores inverter", "Motores trifásicos", "Electrodomésticos"),
            )
        )

    mitsubishi_source = (
        "https://www.mitsubishielectric.com/semiconductors/powerdevices/"
        "products/ipm-dipipm/compact_dipipm/"
    )
    for part, current in (("PSS30SF1F6", 30), ("PSS50SF1F6", 50)):
        rows.append(
            component(
                part,
                "Mitsubishi Electric",
                "Módulo de potencia IPM",
                subtype="Compact DIPIPM",
                description=f"Módulo inteligente de potencia Compact DIPIPM, 600 V y {current} A.",
                source_title="Mitsubishi Electric Compact DIPIPM official product page",
                source_url=mitsubishi_source,
                packages=("Compact DIPIPM",),
                voltage=600,
                current=current,
                topology="Inversor trifásico IGBT con driver y protecciones",
                applications=("Climatización", "Bombas de calor", "Accionamientos de motor"),
            )
        )
    return rows


def mosfet_components() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    st_source = (
        "https://www.st.com/en/power-transistors/"
        "stpower-n-channel-mosfets-gt-200-v-to-700-v/products.html"
    )
    st = [
        ("STW48N60DM2", 600, 40, 0.065, "TO-247"),
        ("STP33N65M2", 650, 24, 0.117, "TO-220"),
        ("STFH24N60M2", 600, 18, 0.168, "TO-220FP"),
        ("STD12N50DM2", 500, 11, 0.299, "DPAK"),
        ("STP13NK60Z", 600, 13, 0.48, "TO-220"),
        ("STB42N60M2-EP", 600, 34, 0.076, "D2PAK"),
        ("STP12NM50", 500, 12, 0.30, "TO-220"),
        ("STF12N65M2", 650, 8, 0.42, "TO-220FP"),
        ("STD12N65M2", 650, 8, 0.42, "DPAK"),
        ("STW50N65DM6", 650, 33, 0.074, "TO-247"),
        ("STW25N60M2-EP", 600, 18, 0.175, "TO-247"),
        ("STP11NM60", 600, 11, 0.40, "TO-220"),
        ("STW35N60DM2", 600, 28, 0.094, "TO-247"),
        ("STF11N60DM2", 600, 10, 0.37, "TO-220FP"),
        ("STP11N60DM2", 600, 10, 0.37, "TO-220"),
        ("STD11N60DM2", 600, 10, 0.37, "DPAK"),
        ("STF40N65M2", 650, 32, 0.087, "TO-220FP"),
        ("STW40N65M2", 650, 32, 0.087, "TO-247"),
        ("STP40N65M2", 650, 32, 0.087, "TO-220"),
        ("STP25N60M2-EP", 600, 18, 0.175, "TO-220"),
        ("STF25N60M2-EP", 600, 18, 0.175, "TO-220FP"),
        ("STP9NK50Z", 500, 7.2, 0.72, "TO-220"),
        ("STP9NK60Z", 600, 7, 0.85, "TO-220"),
        ("STF11NM50N", 500, 8.5, 0.40, "TO-220FP"),
        ("STD11NM50N", 500, 8.5, 0.40, "DPAK"),
        ("STP13NM60N", 600, 11, 0.28, "TO-220"),
        ("STD7NM60N", 600, 5, 0.80, "DPAK"),
        ("STF16N50M2", 500, 13, 0.24, "TO-220FP"),
        ("STD16N50M2", 500, 13, 0.24, "DPAK"),
        ("STP7NK40Z", 400, 5.4, 0.85, "TO-220"),
        ("STW28NM50N", 500, 21, 0.135, "TO-247"),
        ("STP28NM50N", 500, 21, 0.135, "TO-220"),
        ("STF12N50M2", 500, 10, 0.325, "TO-220FP"),
        ("STP12N50M2", 500, 10, 0.325, "TO-220"),
        ("STF28N65M2", 650, 20, 0.15, "TO-220FP"),
        ("STP28N65M2", 650, 20, 0.15, "TO-220"),
        ("STW28N65M2", 650, 20, 0.15, "TO-247"),
        ("STL16N60M2", 600, 8, 0.29, "PowerFLAT 8x8 HV"),
        ("STD16N60M2", 600, 12, 0.28, "DPAK"),
        ("STF16N65M2", 650, 11, 0.32, "TO-220FP"),
        ("STU16N65M2", 650, 11, 0.32, "IPAK"),
        ("STP16N65M2", 650, 11, 0.32, "TO-220"),
        ("STP6NK60Z", 600, 6, 1.0, "TO-220"),
        ("STD5NM60T4", 600, 5, 0.9, "DPAK"),
        ("STP45N60DM6", 600, 30, 0.085, "TO-220"),
        ("STW48N60M2", 600, 42, 0.06, "TO-247"),
        ("STP20NK50Z", 500, 17, 0.23, "TO-220"),
        ("STP20NM60", 600, 20, 0.25, "TO-220"),
        ("STP20NM60FD", 600, 20, 0.26, "TO-220"),
        ("STP24N60M6", 600, 17, 0.162, "TO-220"),
        ("STW20NM60", 600, 20, 0.25, "TO-247"),
    ]
    for part, voltage, current, resistance, package in st:
        exact_url = (
            "https://www.st.com/en/power-transistors/stp20nm60.html"
            if part == "STP20NM60"
            else st_source
        )
        rows.append(
            component(
                part,
                "STMicroelectronics",
                "MOSFET",
                subtype="MOSFET de potencia de canal N y alta tensión",
                description=(
                    f"MOSFET de canal N, {voltage} V, {current} A y "
                    f"RDS(on) documentada de {resistance:g} Ω."
                ),
                source_title="STPOWER N-channel MOSFET official product table",
                source_url=exact_url,
                packages=(package,),
                voltage=voltage,
                current=current,
                resistance=resistance,
                applications=("Fuentes conmutadas", "PFC", "Inversores", "Accionamientos"),
            )
        )

    infineon_p6 = (
        "https://www.infineon.com/assets/row/public/documents/24/42/"
        "infineon-application-note--600v-coolmos-p6-applicationnotes-en.pdf"
    )
    infineon_p7 = (
        "https://www.infineon.com/assets/row/public/documents/24/66/"
        "infineon-coolmos-best-in-class-rdson-per-package-products-"
        "productselectionguide-en.pdf"
    )
    prefix_package = {
        "IPD": "DPAK",
        "IPB": "D2PAK",
        "IPP": "TO-220",
        "IPA": "TO-220 FullPAK",
        "IPW": "TO-247",
        "IPZ": "TO-247 4-pin",
        "IPL": "ThinPAK",
    }
    p6_groups = [
        (0.600, ("IPP60R600P6",)),
        (0.380, ("IPD60R380P6", "IPB60R380P6", "IPP60R380P6", "IPA60R380P6")),
        (0.330, ("IPB60R330P6", "IPP60R330P6", "IPA60R330P6", "IPW60R330P6")),
        (0.280, ("IPB60R280P6", "IPP60R280P6", "IPA60R280P6", "IPW60R280P6")),
        (0.230, ("IPB60R230P6", "IPP60R230P6", "IPA60R230P6", "IPW60R230P6")),
        (0.190, ("IPP60R190P6", "IPA60R190P6", "IPW60R190P6")),
        (0.160, ("IPB60R160P6", "IPP60R160P6", "IPA60R160P6", "IPW60R160P6")),
        (0.125, ("IPP60R125P6", "IPA60R125P6", "IPW60R125P6", "IPZ60R125P6")),
        (0.099, ("IPP60R099P6", "IPA60R099P6", "IPW60R099P6", "IPZ60R099P6")),
        (0.070, ("IPW60R070P6", "IPZ60R070P6")),
        (0.041, ("IPW60R041P6", "IPZ60R041P6")),
    ]
    p7_groups = [
        (600, 0.180, ("IPD60R180P7",)),
        (600, 0.045, ("IPB60R045P7", "IPW60R045P7", "IPZA60R045P7")),
        (600, 0.037, ("IPW60R037P7", "IPZA60R037P7")),
        (600, 0.024, ("IPW60R024P7", "IPZA60R024P7")),
        (600, 0.180, ("IPD60R180C7",)),
        (600, 0.065, ("IPL60R065C7",)),
        (600, 0.040, ("IPB60R040C7", "IPP60R040C7")),
        (600, 0.060, ("IPP60R060C7", "IPA60R060C7")),
        (600, 0.017, ("IPW60R017C7", "IPZ60R017C7")),
        (650, 0.190, ("IPD65R190C7",)),
        (650, 0.045, ("IPB65R045C7", "IPP65R045C7")),
        (650, 0.065, ("IPA65R065C7",)),
        (650, 0.019, ("IPW65R019C7", "IPZ65R019C7")),
    ]
    for resistance, parts in p6_groups:
        for part in parts:
            package = next(
                (value for prefix, value in prefix_package.items() if part.startswith(prefix)),
                "Consultar fabricante",
            )
            rows.append(
                component(
                    part,
                    "Infineon Technologies",
                    "MOSFET",
                    subtype="MOSFET de potencia CoolMOS P6",
                    description=f"MOSFET CoolMOS P6 de 600 V y RDS(on) de {resistance:g} Ω.",
                    source_title="600 V CoolMOS P6 official application and selection guide",
                    source_url=infineon_p6,
                    packages=(package,),
                    voltage=600,
                    resistance=resistance,
                    applications=("PFC", "Fuentes conmutadas", "Inversores"),
                )
            )
    for voltage, resistance, parts in p7_groups:
        for part in parts:
            package = next(
                (value for prefix, value in prefix_package.items() if part.startswith(prefix)),
                "Consultar fabricante",
            )
            rows.append(
                component(
                    part,
                    "Infineon Technologies",
                    "MOSFET",
                    subtype="MOSFET de potencia CoolMOS P7/C7",
                    description=f"MOSFET CoolMOS de {voltage} V y RDS(on) de {resistance:g} Ω.",
                    source_title="CoolMOS official product selection guide",
                    source_url=infineon_p7,
                    packages=(package,),
                    voltage=voltage,
                    resistance=resistance,
                    applications=("PFC", "Fuentes conmutadas", "Inversores"),
                )
            )

    toshiba_sources = {
        "dtmos_vi": (
            "https://toshiba.semicon-storage.com/ap-en/company/news/"
            "new-products-share/transistor/mosfet-20180119-1d.html"
        ),
        "dtmos_vi_more": (
            "https://toshiba.semicon-storage.com/ap-en/company/news/"
            "new-products-share/transistor/mosfet-20180926-1d.html"
        ),
        "tk12": (
            "https://toshiba.semicon-storage.com/ap-en/semiconductor/"
            "product/mosfets/400v-900v-mosfets/detail.TK12A60D.html"
        ),
    }
    toshiba = [
        ("TK650A60F", 600, 11, 0.65, "TO-220SIS", "dtmos_vi"),
        ("TK750A60F", 600, 10, 0.75, "TO-220SIS", "dtmos_vi"),
        ("TK1K2A60F", 600, 6, 1.2, "TO-220SIS", "dtmos_vi"),
        ("TK1K9A60F", 600, 3.7, 1.9, "TO-220SIS", "dtmos_vi"),
        ("TK11A60D", 600, 11, 0.65, "TO-220SIS", "dtmos_vi"),
        ("TK10A60D", 600, 10, 0.75, "TO-220SIS", "dtmos_vi"),
        ("TK6A60D", 600, 6, 1.2, "TO-220SIS", "dtmos_vi"),
        ("TK4A60DB", 600, 3.7, 1.9, "TO-220SIS", "dtmos_vi"),
        ("TK1K0A60F", 600, 7.5, 1.0, "TO-220SIS", "dtmos_vi_more"),
        ("TK1K7A60F", 600, 4, 1.7, "TO-220SIS", "dtmos_vi_more"),
        ("TK2K2A60F", 600, 3.5, 2.2, "TO-220SIS", "dtmos_vi_more"),
        ("TK4K1A60F", 600, 2, 4.1, "TO-220SIS", "dtmos_vi_more"),
        ("TK12A60D", 600, 12, 0.55, "TO-220SIS", "tk12"),
    ]
    for part, voltage, current, resistance, package, source_key in toshiba:
        url = toshiba_sources[source_key]
        rows.append(
            component(
                part,
                "Toshiba Electronic Devices & Storage",
                "MOSFET",
                subtype="MOSFET de potencia DTMOS",
                description=(
                    f"MOSFET DTMOS de canal N, {voltage} V, {current} A y "
                    f"RDS(on) de {resistance:g} Ω."
                ),
                source_title="Toshiba DTMOS official product documentation",
                source_url=url,
                packages=(package,),
                voltage=voltage,
                current=current,
                resistance=resistance,
                applications=("Fuentes conmutadas", "PFC", "Inversores"),
            )
        )

    vishay_source = "https://www.vishay.com/en/mosfets/single/"
    vishay_400 = "https://www.vishay.com/en/mosfets/v-ds-gteq-251-v-lteq-400-v/"
    vishay = [
        ("IRF630", 200, 9, 0.40, "TO-220AB", vishay_source),
        ("IRF640", 200, 18, 0.18, "TO-220AB", vishay_source),
        ("IRF730", 400, 5.5, 1.0, "TO-220AB", vishay_400),
        ("IRF740", 400, 10, 0.55, "TO-220AB", vishay_400),
        ("IRF820", 500, 2.5, 3.0, "TO-220AB", vishay_source),
        ("IRF830", 500, 4.5, 1.5, "TO-220AB", "https://www.vishay.com/docs/91063/91063.pdf"),
        ("IRF840A", 500, 8, 0.85, "TO-220AB", vishay_source),
        ("IRFP250N", 200, 30, 0.075, "TO-247AC", vishay_source),
        ("IRFP260N", 200, 50, 0.04, "TO-247AC", vishay_source),
        ("IRFP350", 400, 16, 0.30, "TO-247AC", vishay_400),
        ("IRFP360", 400, 23, 0.20, "TO-247AC", vishay_400),
        ("IRFP450", 500, 14, 0.40, "TO-247AC", vishay_source),
        ("IRFP460", 500, 20, 0.27, "TO-247AC", "https://www.vishay.com/en/product/91237/"),
    ]
    for part, voltage, current, resistance, package, url in vishay:
        rows.append(
            component(
                part,
                "Vishay Siliconix",
                "MOSFET",
                subtype="MOSFET de potencia de canal N",
                description=(
                    f"MOSFET de canal N, {voltage} V, {current} A y "
                    f"RDS(on) de {resistance:g} Ω."
                ),
                source_title="Vishay power MOSFET official product documentation",
                source_url=url,
                packages=(package,),
                voltage=voltage,
                current=current,
                resistance=resistance,
                applications=("Fuentes conmutadas", "Inversores", "Accionamientos"),
            )
        )

    rows.append(
        component(
            "FQPF9N50C",
            "onsemi",
            "MOSFET",
            subtype="MOSFET de potencia de canal N y alta tensión",
            description="MOSFET de canal N, 500 V, 9 A y RDS(on) máxima de 0,8 Ω.",
            source_title="FQPF9N50C official datasheet",
            source_url="https://www.onsemi.com/download/data-sheet/pdf/fqpf9n50c-d.pdf",
            packages=("TO-220F",),
            voltage=500,
            current=9,
            resistance=0.8,
            applications=("Fuentes conmutadas", "PFC", "Inversores"),
            quality="oficial",
        )
    )
    return rows


def load_existing_pairs(database: Path) -> tuple[set[tuple[str, str]], int]:
    connection = sqlite3.connect(f"file:{database.resolve().as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT c.component_id, c.part_number, COALESCE(m.canonical_name,'') manufacturer
            FROM components c
            LEFT JOIN manufacturers m ON m.manufacturer_id=c.manufacturer_id
            """
        )
        pairs = {
            (normalize(str(row["part_number"])), normalize(str(row["manufacturer"])))
            for row in rows
        }
        maximum_id = int(
            connection.execute("SELECT COALESCE(MAX(component_id),0) FROM components").fetchone()[0]
        )
        return pairs, maximum_id
    finally:
        connection.close()


def validate(rows: list[dict[str, Any]]) -> None:
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (normalize(row["part_number"]), normalize(row["manufacturer"]))
        if key in seen:
            raise RuntimeError(f"Referencia suplementaria duplicada: {key}")
        seen.add(key)
        for url in (row.get("datasheet_url"), (row.get("source") or {}).get("url")):
            if not str(url or "").startswith("https://"):
                raise RuntimeError(f"Fuente no HTTPS para {row['part_number']}: {url}")
        if row.get("equivalents"):
            raise RuntimeError(
                f"La expansión no debe declarar sustitutos automáticos: {row['part_number']}"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path, help="SQLite maestro privado")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    existing_pairs, maximum_id = load_existing_pairs(args.database)
    prior: list[dict[str, Any]] = []
    if args.output.is_file():
        prior = json.loads(args.output.read_text(encoding="utf-8"))
    preserved = [row for row in prior if row.get("generation") != GENERATION]
    preserved_pairs = {
        (normalize(row["part_number"]), normalize(row.get("manufacturer") or ""))
        for row in preserved
    }

    candidates = driver_components() + ipm_components() + mosfet_components()
    candidates.sort(
        key=lambda row: (
            normalize(row["category"]),
            normalize(row["manufacturer"]),
            normalize(row["part_number"]),
        )
    )
    selected: list[dict[str, Any]] = []
    skipped: list[str] = []
    for row in candidates:
        key = (normalize(row["part_number"]), normalize(row["manufacturer"]))
        if key in existing_pairs or key in preserved_pairs:
            skipped.append(f"{row['part_number']} ({row['manufacturer']})")
            continue
        selected.append(row)

    next_id = max([maximum_id, *[int(row["id"]) for row in preserved]], default=0) + 1
    for row in selected:
        row["id"] = next_id
        for index, spec in enumerate(row["specifications"], 1):
            spec["specification_id"] = f"SUP-V2-{next_id}-{index}"
        next_id += 1

    output = preserved + selected
    output.sort(key=lambda row: int(row["id"]))
    validate(output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    by_category: dict[str, int] = {}
    for row in selected:
        by_category[row["category"]] = by_category.get(row["category"], 0) + 1
    print(
        json.dumps(
            {
                "preserved": len(preserved),
                "added": len(selected),
                "skipped_existing": len(skipped),
                "categories": by_category,
                "first_id": selected[0]["id"] if selected else None,
                "last_id": selected[-1]["id"] if selected else None,
                "output": str(args.output),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
