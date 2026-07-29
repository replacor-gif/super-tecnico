#!/usr/bin/env python3
"""Expand the component supplement with common logic and control ICs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from build_component_expansion_v2 import (
    OUTPUT,
    component,
    load_existing_pairs,
    normalize,
    specification,
    validate,
)


GENERATION = "component-ic-expansion-v3"
TI_LOGIC_GUIDE = "https://www.ti.com/lit/pdf/sdyu001"
NEXPERIA_LOGIC = "https://www.nexperia.com/products/analog-logic-ics/logic/family/HC-T"
NEXPERIA_SELECTION = (
    "https://assets.nexperia.com/documents/selection-guide/Nexperia_Selection_Guide_2025.pdf"
)
ST_LOGIC = "https://www.st.com/en/automotive-logic-ics.html"


LOGIC_FUNCTIONS: dict[str, str] = {
    "00": "Cuatro puertas NAND de dos entradas",
    "02": "Cuatro puertas NOR de dos entradas",
    "04": "Seis inversores",
    "08": "Cuatro puertas AND de dos entradas",
    "10": "Tres puertas NAND de tres entradas",
    "11": "Tres puertas AND de tres entradas",
    "14": "Seis inversores con entrada Schmitt",
    "20": "Dos puertas NAND de cuatro entradas",
    "21": "Dos puertas AND de cuatro entradas",
    "27": "Tres puertas NOR de tres entradas",
    "30": "Puerta NAND de ocho entradas",
    "32": "Cuatro puertas OR de dos entradas",
    "42": "Decodificador BCD a decimal",
    "47": "Decodificador BCD a siete segmentos para ánodo común",
    "48": "Decodificador BCD a siete segmentos",
    "51": "Puertas AND-OR-INVERT multifunción",
    "73": "Dos biestables JK con borrado",
    "74": "Dos biestables D con preset y borrado",
    "75": "Cuatro latches biestables",
    "76": "Dos biestables JK con preset y borrado",
    "85": "Comparador de magnitud de cuatro bits",
    "86": "Cuatro puertas XOR de dos entradas",
    "90": "Contador de décadas",
    "92": "Contador divisor por 12",
    "93": "Contador binario de cuatro bits",
    "107": "Dos biestables JK con borrado y flanco negativo",
    "123": "Dos multivibradores monoestables redisparables",
    "125": "Cuatro buffers triestado con habilitación activa baja",
    "126": "Cuatro buffers triestado con habilitación activa alta",
    "132": "Cuatro puertas NAND con entrada Schmitt",
    "133": "Puerta NAND de trece entradas",
    "137": "Latch y decodificador/demultiplexor de 3 a 8",
    "138": "Decodificador/demultiplexor de 3 a 8",
    "139": "Dos decodificadores/demultiplexores de 2 a 4",
    "147": "Codificador de prioridad decimal a BCD",
    "148": "Codificador de prioridad de 8 a 3",
    "151": "Multiplexor de ocho entradas",
    "153": "Dos multiplexores de cuatro entradas",
    "154": "Decodificador/demultiplexor de 4 a 16",
    "157": "Cuatro multiplexores de dos entradas",
    "158": "Cuatro multiplexores inversores de dos entradas",
    "160": "Contador síncrono de décadas",
    "161": "Contador binario síncrono de cuatro bits",
    "162": "Contador síncrono de décadas con borrado síncrono",
    "163": "Contador binario síncrono con borrado síncrono",
    "164": "Registro de desplazamiento serie-paralelo de ocho bits",
    "165": "Registro de desplazamiento paralelo-serie de ocho bits",
    "166": "Registro de desplazamiento paralelo-serie de ocho bits",
    "173": "Registro D de cuatro bits con salida triestado",
    "174": "Seis biestables D con borrado",
    "175": "Cuatro biestables D con salidas complementarias",
    "181": "Unidad aritmético-lógica de cuatro bits",
    "191": "Contador binario síncrono ascendente/descendente",
    "192": "Contador BCD síncrono ascendente/descendente",
    "193": "Contador binario síncrono ascendente/descendente",
    "194": "Registro de desplazamiento universal de cuatro bits",
    "195": "Registro de desplazamiento paralelo de cuatro bits",
    "221": "Dos multivibradores monoestables",
    "237": "Latch y decodificador/demultiplexor de 3 a 8",
    "238": "Decodificador/demultiplexor de 3 a 8 con salidas activas altas",
    "240": "Buffer inversor óctuple triestado",
    "241": "Buffer no inversor óctuple triestado",
    "242": "Transceptor inversor cuádruple triestado",
    "243": "Transceptor no inversor cuádruple triestado",
    "244": "Buffer no inversor óctuple triestado",
    "245": "Transceptor de bus bidireccional óctuple",
    "251": "Multiplexor de ocho entradas con salida triestado",
    "253": "Dos multiplexores de cuatro entradas con salida triestado",
    "257": "Cuatro multiplexores de dos entradas con salida triestado",
    "258": "Cuatro multiplexores inversores con salida triestado",
    "259": "Latch direccionable de ocho bits",
    "266": "Cuatro puertas XNOR de colector abierto",
    "273": "Ocho biestables D con borrado",
    "280": "Generador/comprobador de paridad de nueve bits",
    "283": "Sumador binario completo de cuatro bits",
    "293": "Contador binario de cuatro bits",
    "298": "Multiplexor cuádruple de dos entradas con almacenamiento",
    "299": "Registro de desplazamiento universal de ocho bits",
    "365": "Seis buffers triestado",
    "366": "Seis buffers inversores triestado",
    "367": "Seis buffers no inversores triestado",
    "368": "Seis buffers inversores triestado",
    "373": "Latch transparente óctuple con salida triestado",
    "374": "Ocho biestables D con salida triestado",
    "377": "Ocho biestables D con habilitación",
    "390": "Dos contadores de décadas",
    "393": "Dos contadores binarios de cuatro bits",
    "4017": "Contador Johnson de décadas con diez salidas decodificadas",
    "4040": "Contador binario asíncrono de doce etapas",
    "4060": "Contador binario de catorce etapas con oscilador",
    "4066": "Cuatro interruptores analógicos bilaterales",
    "4094": "Registro de desplazamiento serie-paralelo de ocho bits",
    "4511": "Latch y decodificador BCD a siete segmentos",
    "4538": "Dos multivibradores monoestables de precisión",
    "595": "Registro serie-paralelo de ocho bits con registro de salida",
    "597": "Registro paralelo-serie de ocho bits con registro de entrada",
}


CMOS_FUNCTIONS: dict[str, str] = {
    "4001B": "Cuatro puertas NOR de dos entradas",
    "4002B": "Dos puertas NOR de cuatro entradas",
    "4006B": "Registro de desplazamiento de 18 etapas",
    "4007UB": "Par complementario de inversores y transistores CMOS",
    "4008B": "Sumador completo de cuatro bits",
    "4009UB": "Seis buffers/inversores",
    "4010B": "Seis buffers no inversores",
    "4011B": "Cuatro puertas NAND de dos entradas",
    "4012B": "Dos puertas NAND de cuatro entradas",
    "4013B": "Dos biestables D",
    "4014B": "Registro de desplazamiento de ocho etapas",
    "4015B": "Dos registros de desplazamiento de cuatro etapas",
    "4016B": "Cuatro interruptores analógicos bilaterales",
    "4017B": "Contador Johnson de décadas con diez salidas",
    "4018B": "Contador programable divisor por N",
    "4019B": "Cuatro selectores AND/OR",
    "4020B": "Contador binario de catorce etapas",
    "4021B": "Registro paralelo-serie de ocho etapas",
    "4022B": "Contador Johnson divisor por ocho",
    "4023B": "Tres puertas NAND de tres entradas",
    "4024B": "Contador binario de siete etapas",
    "4025B": "Tres puertas NOR de tres entradas",
    "4027B": "Dos biestables JK",
    "4028B": "Decodificador BCD a decimal",
    "4029B": "Contador binario/decimal ascendente-descendente",
    "4030B": "Cuatro puertas XOR",
    "4035B": "Registro de desplazamiento paralelo de cuatro bits",
    "4040B": "Contador binario de doce etapas",
    "4041B": "Cuatro buffers CMOS",
    "4042B": "Cuatro latches con reloj",
    "4043B": "Cuatro latches R/S con salidas triestado",
    "4044B": "Cuatro latches R/S con salidas triestado",
    "4046B": "Bucle de enganche de fase PLL",
    "4047B": "Multivibrador monoestable/astable",
    "4049UB": "Seis inversores/buffers",
    "4050B": "Seis buffers no inversores",
    "4051B": "Multiplexor/demultiplexor analógico de ocho canales",
    "4052B": "Dos multiplexores/demultiplexores analógicos de cuatro canales",
    "4053B": "Tres multiplexores/demultiplexores analógicos dobles",
    "4060B": "Contador de catorce etapas con oscilador",
    "4066B": "Cuatro interruptores analógicos bilaterales",
    "4068B": "Puerta NAND/AND de ocho entradas",
    "4069UB": "Seis inversores no bufferizados",
    "4070B": "Cuatro puertas XOR",
    "4071B": "Cuatro puertas OR de dos entradas",
    "4072B": "Dos puertas OR de cuatro entradas",
    "4073B": "Tres puertas AND de tres entradas",
    "4075B": "Tres puertas OR de tres entradas",
    "4077B": "Cuatro puertas XNOR",
    "4078B": "Puerta NOR/OR de ocho entradas",
    "4081B": "Cuatro puertas AND de dos entradas",
    "4082B": "Dos puertas AND de cuatro entradas",
    "4085B": "Dos puertas AND-OR-INVERT",
    "4086B": "Puerta AND-OR-INVERT expandible",
    "4093B": "Cuatro puertas NAND con entrada Schmitt",
    "4094B": "Registro serie-paralelo de ocho etapas",
    "40106B": "Seis inversores con entrada Schmitt",
    "40109B": "Cuatro desplazadores de nivel",
    "40110B": "Contador decimal y driver de siete segmentos",
    "40147B": "Codificador de prioridad decimal a BCD",
    "40160B": "Contador decimal síncrono",
    "40161B": "Contador binario síncrono",
    "40162B": "Contador decimal síncrono",
    "40163B": "Contador binario síncrono",
    "4510B": "Contador BCD ascendente/descendente",
    "4511B": "Latch y decodificador BCD a siete segmentos",
    "4512B": "Selector de datos de ocho canales",
    "4514B": "Latch y decodificador de 4 a 16",
    "4515B": "Latch y decodificador de 4 a 16 con salidas invertidas",
    "4516B": "Contador binario ascendente/descendente",
    "4518B": "Dos contadores BCD",
    "4520B": "Dos contadores binarios",
    "4521B": "Divisor de frecuencia de 24 etapas",
    "4522B": "Contador decimal programable divisor por N",
    "4528B": "Dos multivibradores monoestables",
    "4532B": "Codificador de prioridad de ocho bits",
    "4536B": "Temporizador programable",
    "4538B": "Dos multivibradores monoestables de precisión",
    "4541B": "Temporizador programable",
}


def add_supply_specs(
    row: dict[str, Any],
    minimum: float,
    maximum: float,
    family: str,
) -> None:
    row["voltage_max_v"] = maximum
    row["specifications"] = [
        specification(
            "supply_voltage",
            "Rango de alimentación de la familia",
            minimum=minimum,
            maximum=maximum,
            unit="V",
            conditions="Confirma el rango del sufijo y fabricante exactos.",
            confidence=0.96,
        ),
        specification(
            "logic_family",
            "Familia lógica",
            text=family,
            confidence=0.98,
        ),
    ]


def logic_component(
    part: str,
    manufacturer: str,
    function: str,
    family: str,
    source_url: str,
    minimum: float,
    maximum: float,
    aliases: Iterable[str],
    packages: Iterable[str],
) -> dict[str, Any]:
    row = component(
        part,
        manufacturer,
        "Circuito integrado",
        subtype=f"Lógica digital {family}",
        description=f"{function}. Familia {family}; alimentación documentada de {minimum:g} a {maximum:g} V.",
        source_title=f"{family} official logic family documentation",
        source_url=source_url,
        packages=packages,
        aliases=aliases,
        voltage=maximum,
        topology=function,
        applications=("Control digital", "Temporización", "Interfaz y acondicionamiento lógico"),
    )
    add_supply_specs(row, minimum, maximum, family)
    row["generation"] = GENERATION
    return row


def logic_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    hc_keys = [
        "00", "02", "04", "08", "10", "11", "14", "20", "21", "27", "30",
        "32", "42", "51", "74", "85", "86", "107", "123", "125", "126", "132",
        "137", "138", "139", "147", "148", "151", "153", "154", "157", "158",
        "160", "161", "162", "163", "164", "165", "166", "173", "174", "175",
        "191", "192", "193", "194", "195", "221", "237", "238", "240", "241",
        "242", "243", "244", "245", "251", "253", "257", "258", "259", "266",
        "273", "280", "283", "298", "299", "365", "366", "367", "368", "373",
        "374", "377", "390", "393", "4017", "4040", "4060", "4066", "4094",
        "4511", "4538", "595", "597",
    ]
    for prefix, minimum, maximum, family in (
        ("74HC", 2.0, 6.0, "74HC"),
        ("74HCT", 4.5, 5.5, "74HCT"),
    ):
        for key in hc_keys:
            part = f"{prefix}{key}"
            rows.append(
                logic_component(
                    part,
                    "Nexperia",
                    LOGIC_FUNCTIONS[key],
                    family,
                    NEXPERIA_LOGIC,
                    minimum,
                    maximum,
                    aliases=(f"{part}D", f"{part}PW", f"{part}BQ"),
                    packages=("SO", "TSSOP", "DHVQFN"),
                )
            )
            ti_part = f"SN{part}"
            rows.append(
                logic_component(
                    ti_part,
                    "Texas Instruments",
                    LOGIC_FUNCTIONS[key],
                    family,
                    TI_LOGIC_GUIDE,
                    minimum,
                    maximum,
                    aliases=(
                        part,
                        f"{ti_part}N",
                        f"{ti_part}D",
                        f"{ti_part}DR",
                        f"{ti_part}PW",
                    ),
                    packages=("PDIP", "SOIC", "TSSOP"),
                )
            )

    ls_keys = [
        "00", "02", "04", "08", "10", "11", "14", "20", "21", "27", "30",
        "32", "42", "47", "48", "51", "73", "74", "75", "76", "85", "86",
        "90", "92", "93", "107", "123", "125", "126", "132", "138", "139",
        "147", "148", "151", "153", "154", "157", "160", "161", "163", "164",
        "165", "166", "173", "174", "175", "181", "191", "192", "193", "194",
        "221", "240", "241", "244", "245", "247", "251", "253", "257", "259",
        "266", "273", "280", "283", "293", "298", "299", "365", "366", "367",
        "368", "373", "374", "390", "393",
    ]
    LOGIC_FUNCTIONS["247"] = "Decodificador BCD a siete segmentos"
    for key in ls_keys:
        part = f"SN74LS{key}"
        rows.append(
            logic_component(
                part,
                "Texas Instruments",
                LOGIC_FUNCTIONS[key],
                "74LS",
                TI_LOGIC_GUIDE,
                4.5,
                5.5,
                aliases=(f"74LS{key}", f"{part}N", f"{part}D", f"{part}DR"),
                packages=("PDIP", "SOIC"),
            )
        )

    for key, function in CMOS_FUNCTIONS.items():
        part = f"CD{key}"
        rows.append(
            logic_component(
                part,
                "Texas Instruments",
                function,
                "CD4000B",
                f"https://www.ti.com/product/{part}",
                3.0,
                18.0,
                aliases=(part.removesuffix("B"), f"{part}E", f"{part}M", f"{part}PW"),
                packages=("PDIP", "SOIC", "TSSOP"),
            )
        )

    hef_keys = [
        "4001B", "4011B", "4013B", "4014B", "4015B", "4016B", "4017B",
        "4020B", "4021B", "4024B", "4027B", "4028B", "4029B", "4040B",
        "4046B", "4047B", "4049B", "4050B", "4051B", "4052B", "4053B",
        "4060B", "4066B", "4069UB", "4070B", "4071B", "4073B", "4075B",
        "4077B", "4081B", "4082B", "4093B", "4094B", "40106B", "4510B",
        "4511B", "4514B", "4515B", "4518B", "4520B", "4528B", "4538B",
        "4541B",
    ]
    for key in hef_keys:
        function = CMOS_FUNCTIONS.get(key) or CMOS_FUNCTIONS[key.replace("4049B", "4049UB")]
        part = f"HEF{key}"
        rows.append(
            logic_component(
                part,
                "Nexperia",
                function,
                "HEF4000B",
                NEXPERIA_SELECTION,
                3.0,
                15.0,
                aliases=(part.removesuffix("B"), f"{part}P", f"{part}T"),
                packages=("SO", "TSSOP"),
            )
        )

    hcf_keys = [
        "4001B", "4011B", "4013B", "4015B", "4016B", "4017B", "4020B",
        "4021B", "4024B", "4027B", "4028B", "4029B", "4040B", "4046B",
        "4047B", "4049UB", "4050B", "4051B", "4052B", "4053B", "4060B",
        "4066B", "4069UB", "4070B", "4071B", "4073B", "4075B", "4077B",
        "4081B", "4082B", "4093B", "4094B", "40106B", "4510B", "4511B",
        "4514B", "4515B", "4518B", "4520B", "4528B", "4538B", "4541B",
    ]
    for key in hcf_keys:
        base = key[:-1] if key.endswith("B") else key
        part = f"HCF{base}"
        rows.append(
            logic_component(
                part,
                "STMicroelectronics",
                CMOS_FUNCTIONS[key],
                "HCF4000B",
                ST_LOGIC,
                3.0,
                20.0,
                aliases=(f"HCF{key}", f"{part}BEY", f"{part}BM1"),
                packages=("PDIP", "SOIC"),
            )
        )
    return rows


def general_ic(
    part: str,
    manufacturer: str,
    category: str,
    description: str,
    *,
    source_url: str,
    minimum: float | None = None,
    maximum: float | None = None,
    packages: Iterable[str] = (),
    aliases: Iterable[str] = (),
    subtype: str = "Circuito integrado de control",
) -> dict[str, Any]:
    row = component(
        part,
        manufacturer,
        category,
        subtype=subtype,
        description=description,
        source_title=f"{part} official product documentation",
        source_url=source_url,
        packages=packages,
        aliases=aliases,
        voltage=maximum,
        topology=description,
        applications=("Control electrónico", "Fuentes y placas de climatización"),
        quality="oficial",
    )
    if minimum is not None and maximum is not None:
        add_supply_specs(row, minimum, maximum, subtype)
    row["generation"] = GENERATION
    return row


def analog_and_driver_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    ti = [
        ("NE555", "Circuito integrado", "Temporizador de precisión simple", 4.5, 16, ("PDIP-8", "SOIC-8")),
        ("SA555", "Circuito integrado", "Temporizador de precisión para rango industrial", 4.5, 16, ("PDIP-8", "SOIC-8")),
        ("SE555", "Circuito integrado", "Temporizador de precisión para amplio rango térmico", 4.5, 18, ("PDIP-8", "SOIC-8")),
        ("TLC555", "Circuito integrado", "Temporizador CMOS de bajo consumo", 2, 15, ("PDIP-8", "SOIC-8")),
        ("LMC555", "Circuito integrado", "Temporizador CMOS de muy bajo consumo", 1.5, 15, ("PDIP-8", "SOIC-8")),
        ("LM556", "Circuito integrado", "Temporizador doble de precisión", 4.5, 16, ("PDIP-14", "SOIC-14")),
        ("LM358B", "Amplificador / comparador", "Amplificador operacional doble", 3, 36, ("PDIP-8", "SOIC-8")),
        ("LM324B", "Amplificador / comparador", "Amplificador operacional cuádruple", 3, 36, ("PDIP-14", "SOIC-14")),
        ("LM393B", "Amplificador / comparador", "Comparador doble de colector abierto", 2, 36, ("PDIP-8", "SOIC-8")),
        ("LM339B", "Amplificador / comparador", "Comparador cuádruple de colector abierto", 2, 36, ("PDIP-14", "SOIC-14")),
        ("LM311", "Amplificador / comparador", "Comparador de tensión de alta velocidad", 3.5, 30, ("PDIP-8", "SOIC-8")),
        ("TL071", "Amplificador / comparador", "Amplificador operacional JFET simple", 7, 36, ("PDIP-8", "SOIC-8")),
        ("TL072", "Amplificador / comparador", "Amplificador operacional JFET doble", 7, 36, ("PDIP-8", "SOIC-8")),
        ("TL074", "Amplificador / comparador", "Amplificador operacional JFET cuádruple", 7, 36, ("PDIP-14", "SOIC-14")),
        ("TL081", "Amplificador / comparador", "Amplificador operacional JFET simple", 7, 36, ("PDIP-8", "SOIC-8")),
        ("TL082", "Amplificador / comparador", "Amplificador operacional JFET doble", 7, 36, ("PDIP-8", "SOIC-8")),
        ("TL084", "Amplificador / comparador", "Amplificador operacional JFET cuádruple", 7, 36, ("PDIP-14", "SOIC-14")),
        ("UA741", "Amplificador / comparador", "Amplificador operacional de propósito general", 10, 36, ("PDIP-8", "SOIC-8")),
        ("RC4558", "Amplificador / comparador", "Amplificador operacional doble de propósito general", 10, 30, ("PDIP-8", "SOIC-8")),
        ("NE5532", "Amplificador / comparador", "Amplificador operacional doble de bajo ruido", 6, 30, ("PDIP-8", "SOIC-8")),
        ("NE5534", "Amplificador / comparador", "Amplificador operacional simple de bajo ruido", 6, 30, ("PDIP-8", "SOIC-8")),
        ("SG3525A", "Controlador de fuente", "Controlador PWM de modo tensión", 8, 35, ("PDIP-16", "SOIC-16")),
        ("UC3825A", "Controlador de fuente", "Controlador PWM de alta velocidad", 9, 30, ("PDIP-16", "SOIC-16")),
        ("UCC28019A", "Controlador de fuente", "Controlador PFC de conducción continua", 10, 21, ("SOIC-8",)),
        ("DRV8871", "Driver de potencia", "Driver de motor de continua en puente H", 6.5, 45, ("HTSSOP-8",)),
        ("DRV8301", "Driver de potencia", "Driver trifásico de puertas MOSFET", 6, 60, ("HTSSOP-56",)),
    ]
    for part, category, description, minimum, maximum, packages in ti:
        rows.append(
            general_ic(
                part,
                "Texas Instruments",
                category,
                description,
                source_url=f"https://www.ti.com/product/{part}",
                minimum=minimum,
                maximum=maximum,
                packages=packages,
                aliases=(f"{part}D", f"{part}N", f"{part}P"),
                subtype=description,
            )
        )

    st = [
        ("L7805CV", "Regulador / referencia", "Regulador lineal positivo fijo de 5 V", 7, 35, ("TO-220",)),
        ("L7808CV", "Regulador / referencia", "Regulador lineal positivo fijo de 8 V", 10.5, 35, ("TO-220",)),
        ("L7812CV", "Regulador / referencia", "Regulador lineal positivo fijo de 12 V", 14.5, 35, ("TO-220",)),
        ("L7815CV", "Regulador / referencia", "Regulador lineal positivo fijo de 15 V", 17.5, 35, ("TO-220",)),
        ("L7824CV", "Regulador / referencia", "Regulador lineal positivo fijo de 24 V", 27, 40, ("TO-220",)),
        ("L7905CV", "Regulador / referencia", "Regulador lineal negativo fijo de -5 V", 7, 35, ("TO-220",)),
        ("L7908CV", "Regulador / referencia", "Regulador lineal negativo fijo de -8 V", 10.5, 35, ("TO-220",)),
        ("L7912CV", "Regulador / referencia", "Regulador lineal negativo fijo de -12 V", 14.5, 35, ("TO-220",)),
        ("L7915CV", "Regulador / referencia", "Regulador lineal negativo fijo de -15 V", 17.5, 35, ("TO-220",)),
        ("L7924CV", "Regulador / referencia", "Regulador lineal negativo fijo de -24 V", 27, 40, ("TO-220",)),
        ("LM317T", "Regulador / referencia", "Regulador lineal positivo ajustable", 3, 40, ("TO-220",)),
        ("LM337T", "Regulador / referencia", "Regulador lineal negativo ajustable", 3, 40, ("TO-220",)),
        ("L293D", "Driver de potencia", "Cuatro drivers push-pull con diodos; doble puente H", 4.5, 36, ("PDIP-16", "SOIC-20")),
        ("L298", "Driver de potencia", "Driver doble de puente completo para motores", 4.5, 46, ("Multiwatt-15", "PowerSO-20")),
        ("L6203", "Driver de potencia", "Driver DMOS de puente completo", 12, 48, ("Multiwatt-11",)),
        ("L6205", "Driver de potencia", "Driver DMOS doble de puente completo", 8, 52, ("PowerDIP-20", "PowerSO-20")),
        ("L6206", "Driver de potencia", "Driver DMOS doble de puente completo con control de corriente", 8, 52, ("PowerDIP-24", "PowerSO-36")),
        ("L6207", "Driver de potencia", "Driver DMOS doble de puente completo con PWM", 8, 52, ("PowerDIP-24", "PowerSO-36")),
        ("L6225", "Driver de potencia", "Driver DMOS dual para motor paso a paso", 8, 52, ("PowerDIP-20", "PowerSO-20")),
        ("L6234", "Driver de potencia", "Driver DMOS trifásico", 7, 52, ("PowerDIP-20", "PowerSO-20")),
        ("VIPER12A", "Controlador de fuente", "Convertidor offline con MOSFET integrado", 9, 38, ("DIP-8", "SOIC-8")),
        ("VIPER22A", "Controlador de fuente", "Convertidor offline con MOSFET integrado", 9, 38, ("DIP-8", "SOIC-8")),
        ("VIPER27H", "Controlador de fuente", "Convertidor offline de alta tensión", 8.5, 23.5, ("SOIC-16",)),
        ("VIPER35", "Controlador de fuente", "Convertidor offline de alta tensión", 8.5, 23.5, ("SOIC-16",)),
        ("VIPER50A", "Controlador de fuente", "Convertidor offline con MOSFET integrado", 8, 15, ("Pentawatt",)),
        ("VIPER53", "Controlador de fuente", "Convertidor offline con MOSFET integrado", 8.4, 19, ("DIP-8", "SOIC-8")),
    ]
    for part, category, description, minimum, maximum, packages in st:
        slug = part.lower()
        family_path = "motor-drivers" if category == "Driver de potencia" else "ac-dc-converters"
        if category == "Regulador / referencia":
            family_path = "linear-voltage-regulators"
        rows.append(
            general_ic(
                part,
                "STMicroelectronics",
                category,
                description,
                source_url=f"https://www.st.com/en/{family_path}/{slug}.html",
                minimum=minimum,
                maximum=maximum,
                packages=packages,
                aliases=(part.removesuffix("CV"), part.removesuffix("A")),
                subtype=description,
            )
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path, help="SQLite maestro privado")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    existing_pairs, maximum_id = load_existing_pairs(args.database)
    prior = json.loads(args.output.read_text(encoding="utf-8")) if args.output.is_file() else []
    preserved = [row for row in prior if row.get("generation") != GENERATION]
    preserved_pairs = {
        (normalize(row["part_number"]), normalize(row.get("manufacturer") or ""))
        for row in preserved
    }

    candidates = logic_rows() + analog_and_driver_rows()
    candidates.sort(
        key=lambda row: (
            normalize(row["category"]),
            normalize(row["manufacturer"]),
            normalize(row["part_number"]),
        )
    )
    selected: list[dict[str, Any]] = []
    skipped: list[str] = []
    seen_candidate_pairs: set[tuple[str, str]] = set()
    for row in candidates:
        key = (normalize(row["part_number"]), normalize(row["manufacturer"]))
        if key in seen_candidate_pairs:
            raise RuntimeError(f"Candidato repetido: {key}")
        seen_candidate_pairs.add(key)
        if key in existing_pairs or key in preserved_pairs:
            skipped.append(f"{row['part_number']} ({row['manufacturer']})")
            continue
        selected.append(row)

    next_id = max([maximum_id, *[int(row["id"]) for row in preserved]], default=0) + 1
    for row in selected:
        row["id"] = next_id
        for index, spec in enumerate(row["specifications"], 1):
            spec["specification_id"] = f"SUP-V3-{next_id}-{index}"
        next_id += 1

    output = preserved + selected
    output.sort(key=lambda row: int(row["id"]))
    validate(output)
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
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
