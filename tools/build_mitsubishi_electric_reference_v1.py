#!/usr/bin/env python3
"""Construye Mitsubishi Electric Referencia V1 para Super Técnico.

La proyección pública contiene resúmenes técnicos, referencias y páginas
verificadas. Los PDF, capturas y bases privadas no se copian a la web.
"""

from __future__ import annotations

import json
import re
import shutil
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BRAND_DIR = ROOT / "data" / "brands" / "mitsubishi-electric"
WEB_DIR = BRAND_DIR / "web"
BRAND_ID = 4


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def normalize(value: str) -> str:
    value = "".join(
        char
        for char in unicodedata.normalize("NFD", str(value or ""))
        if unicodedata.category(char) != "Mn"
    ).upper()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9]+", " ", value)).strip()


def split_items(value: str) -> list[str]:
    return [item.strip() for item in value.split("|") if item.strip()]


LIBRARY = "https://library.mitsubishielectric.co.uk/pdf/download_full/"
SOURCES: dict[str, dict[str, Any]] = {
    "MSZ": {
        "title": "Manual de servicio — MSZ-LN18/25/35/50/60VG",
        "document_ref": "OBH766B",
        "publication_date": "2018",
        "language": "en",
        "document_type": "service_manual",
        "source_url": f"{LIBRARY}3404",
        "notes": "Split mural: emergencia, memoria de averías y diagnóstico interior.",
    },
    "MUZ": {
        "title": "Manual de servicio — MUZ-LN25/35/50/60VG",
        "document_ref": "OBH767",
        "publication_date": "2017",
        "language": "en",
        "document_type": "service_manual",
        "source_url": f"{LIBRARY}3405",
        "notes": "Exterior residencial inverter: recall, LED, protecciones y componentes.",
    },
    "MXZ": {
        "title": "Manual de servicio — MXZ-2F/3F/4F/5F/6F",
        "document_ref": "OBH790P",
        "publication_date": "2024",
        "language": "en",
        "document_type": "service_manual",
        "source_url": f"{LIBRARY}5366",
        "notes": "Multisplit de dos a seis conexiones: ajustes, corrección automática y diagnóstico.",
    },
    "PLAM": {
        "title": "Manual de servicio — PLA-M35/50/60/71/100/125/140EA",
        "document_ref": "OCH697",
        "publication_date": "2018",
        "language": "en",
        "document_type": "service_manual",
        "source_url": f"{LIBRARY}3942",
        "notes": "Cassette moderna: códigos, autocheck, drenaje, emergencia y valores eléctricos.",
    },
    "PLARP": {
        "title": "Manual de servicio — PLA-RP35/50/60/71/100/125/140BA",
        "document_ref": "OCH416D",
        "publication_date": "2012",
        "language": "en",
        "document_type": "service_manual",
        "source_url": f"{LIBRARY}1318",
        "notes": "Cassette de generación anterior: secuencias P4/P5/PA y diagnóstico A-Control.",
    },
    "PUZZM": {
        "title": "Manual de servicio — PUZ-ZM100/125/140V(Y)DA",
        "document_ref": "OCH832B",
        "publication_date": "2024",
        "language": "en",
        "document_type": "service_manual",
        "source_url": f"{LIBRARY}5247",
        "notes": "Mr. Slim comercial: tabla de códigos, monitor de operación y Service Tool.",
    },
    "PUMY": {
        "title": "Manual de servicio — PUMY-P200YKM2",
        "document_ref": "OCH675E",
        "publication_date": "2020",
        "language": "en",
        "document_type": "service_manual",
        "source_url": f"{LIBRARY}4401",
        "notes": "City Multi compacto: Test Run, M-NET, códigos dobles y diagnóstico detallado.",
    },
    "CITY": {
        "title": "Service Handbook — CITY MULTI PUHY/PUY-P200~P650YGM-A",
        "document_ref": "PUHY-P-YGM-A-SH",
        "publication_date": "2004",
        "language": "en",
        "document_type": "service_handbook",
        "source_url": f"{LIBRARY}2015",
        "notes": "VRF de gran potencia: red M-NET, prueba, estados, códigos y emergencia.",
    },
    "CITYLEG": {
        "title": "Service Handbook — CITY MULTI PUHY/PURY-YMF-C y BC Controller",
        "document_ref": "PUHY-PURY-YMF-C-SH",
        "publication_date": "2000",
        "language": "en",
        "document_type": "service_handbook",
        "source_url": f"{LIBRARY}1747",
        "notes": "Generación VRF anterior con alcance de parada por unidad, BC y exterior.",
    },
    "PAR41": {
        "title": "Manual de instalación — mando cableado PAR-41MAA",
        "document_ref": "WT09534X02",
        "publication_date": "2025",
        "language": "en",
        "document_type": "installation_manual",
        "source_url": f"{LIBRARY}5618",
        "notes": "Mando cableado actual: TB5/TB15, historial, self-check, funciones y prueba.",
    },
    "PAR21": {
        "title": "Manual de instrucciones — mando cableado PAR-21MAA",
        "document_ref": "WT05000X01",
        "publication_date": "2017",
        "language": "en",
        "document_type": "instruction_book",
        "source_url": f"{LIBRARY}3478",
        "notes": "Mando cableado clásico con CHECK/CLEAR, TEST y selección Main/Sub.",
    },
    "PACYT52": {
        "title": "Manual de instrucciones — Simple MA Remote Controller PAC-YT52CRA",
        "document_ref": "WT06591X01",
        "publication_date": "2017",
        "language": "en",
        "document_type": "instruction_book",
        "source_url": f"{LIBRARY}408",
        "notes": "Mando simplificado: diferencias de visualización Mr. Slim y CITY MULTI.",
    },
}


def source(ref: str, page: str, section_name: str, page_end: str | None = None) -> dict[str, Any]:
    row = SOURCES[ref]
    return {
        "title": row["title"],
        "document_ref": row["document_ref"],
        "source_url": row["source_url"],
        "page_start": page,
        "page_end": page_end or page,
        "section": section_name,
    }


CATEGORIES = [
    (1, "errors", "Errores y protecciones", "Códigos, indicaciones LED, subcódigos y efectos separados por familia."),
    (2, "diagnostic_access", "Obtención de códigos y subcódigos", "Procedimientos desde mandos inalámbricos, cableados y placas."),
    (3, "history_reset", "Historial y borrado", "Consulta, diagnóstico preliminar, borrado y recall de averías."),
    (4, "service_modes", "Modos de servicio", "Emergencia, marcha forzada, Test Run y recogida de refrigerante."),
    (5, "configuration", "Configuración y programación", "Function Settings, DIP switch, selectores y opciones de placa."),
    (6, "controllers_buses", "Mandos y buses", "Cableado MA, M-NET, tensiones, arranque y diagnóstico del propio mando."),
    (7, "drainage_overflow", "Drenaje y desbordamiento", "Bomba, boya, P4, P5, PA y diferencias entre frío y calor."),
    (8, "commissioning", "Puesta en marcha", "Pruebas previas, Test Run y comprobaciones posteriores."),
    (9, "multisplit", "Multisplit", "Corrección de tuberías/cableado y ajustes de exteriores MXZ."),
    (10, "city_multi_network", "CITY MULTI y red M-NET", "Direcciones, topología, tensión, forma de onda y alcance de paradas."),
    (11, "component_checks", "Comprobación de componentes", "Sondas, bomba, boya, ventiladores, válvulas, presión e inverter."),
    (12, "technical_values", "Valores técnicos", "Curvas NTC, tensiones de buses y puntos de prueba."),
    (13, "normal_states", "Comportamientos normales", "Esperas, retardos y estados que pueden parecer avería."),
    (14, "service_tools_boards", "Herramientas y placas", "Service Tool, monitor de operación y trabajo tras sustituir PCB."),
    (15, "system_architecture", "Arquitectura de sistemas", "Pistas para reconocer M-Series, Mr. Slim, MXZ y CITY MULTI."),
]

CATEGORY_BY_SLUG = {
    slug: {"id": ident, "slug": slug, "name": name, "description": description}
    for ident, slug, name, description in CATEGORIES
}


NTC_15K = [
    (0, 15.0), (10, 9.6), (20, 6.3), (25, 5.4), (30, 4.3), (40, 3.0),
]
NTC_10K = [
    (0, 32.6), (10, 19.9), (20, 12.5), (25, 10.0), (30, 8.1), (40, 5.3),
]


def curve_dataset(dataset_id: int, name: str, points: list[tuple[float, float]], ref: str, page: str) -> dict[str, Any]:
    return {
        "id": dataset_id,
        "name": name,
        "dataset_type": "sensor_curve",
        "variable_name": "Temperatura",
        "variable_unit": "°C",
        "value_name": "Resistencia",
        "value_unit": "kΩ",
        "tolerance_text": "Aplicar solo a la familia y al tipo de sonda indicados.",
        "source_kind": "official",
        "calculation_method": None,
        "review_status": "reviewed",
        "notes": "Puntos resumidos de la curva oficial; medir la sonda desconectada.",
        "visible": 1,
        "points": [
            {
                "variable_value": temperature,
                "value_min": None,
                "value_nominal": resistance,
                "value_max": None,
                "value_text": None,
                "sort_order": order,
                "notes": None,
            }
            for order, (temperature, resistance) in enumerate(points)
        ],
        "sources": [source(ref, page, "Thermistor characteristic")],
    }


def datasets_for(code: str, interpretation_id: int, ref: str) -> list[dict[str, Any]]:
    if ref in {"PLAM", "PLARP"} and code in {"P1", "P2", "P9"}:
        return [curve_dataset(interpretation_id * 10 + 1, f"{code} — NTC 15 kΩ", NTC_15K, ref, "33" if ref == "PLAM" else "32")]
    if ref in {"MSZ", "MUZ", "MXZ"} and ("POWER" in code or code in {"U3", "U4"}):
        return [curve_dataset(interpretation_id * 10 + 1, "NTC residencial de referencia — 10 kΩ a 25 °C", NTC_10K, ref, "40" if ref == "MUZ" else "190")]
    return []


def operational_impact(behavior: str) -> dict[str, Any]:
    value = normalize(behavior)
    if "TODAS" in value or "TODO EL SISTEMA" in value:
        level = "all_system"
    elif "SOLO" in value or "AFECTADA" in value:
        level = "affected_unit"
    elif "CONTINUA" in value or "REINTENTA" in value or "LIMITA" in value:
        level = "warning"
    else:
        level = "protected_stop"
    return {
        "stop_level": level,
        "summary": behavior,
        "affected_scope": "El alcance indicado para esta familia documental.",
        "unaffected_scope": None,
        "restart_behavior": "Corregir la causa y aplicar el rearme o repetición de prueba descritos en el manual.",
        "degraded_behavior": None,
        "notes": "No se generaliza este comportamiento a otra familia Mitsubishi Electric.",
    }


def error_spec(
    code: str,
    title: str,
    scope: str,
    ref: str,
    page: str,
    description: str,
    causes: str,
    checks: str,
    behavior: str,
    aliases: str = "",
) -> dict[str, str]:
    return {
        "code": code,
        "title": title,
        "scope": scope,
        "ref": ref,
        "page": page,
        "description": description,
        "causes": causes,
        "checks": checks,
        "behavior": behavior,
        "aliases": aliases,
    }


# A-Control / Mr. Slim. Las páginas 24–30 de OCH697 desarrollan los códigos
# interiores; OCH832B 67–68 reúne la tabla completa de interior y exterior.
A_CONTROL_ERRORS = [
    error_spec("P1", "Sonda de aire de retorno interior", "indoor", "PLAM", "24", "La entrada TH1 se detecta abierta o en cortocircuito.", "Sonda TH1 defectuosa|Conector o cable abierto|Entrada de PCB interior defectuosa", "Medir TH1 desconectada y comparar con la curva 15 kΩ|Revisar conector y continuidad|Descartar PCB", "La unidad interior se detiene; puede reanudar tras tres minutos si la lectura vuelve a rango."),
    error_spec("P2", "Sonda de tubería líquida TH2", "indoor", "PLAM", "24", "La sonda TH2 se detecta abierta o en cortocircuito.", "Sonda TH2 defectuosa|Contacto térmico deficiente|Cable o PCB defectuosos", "Medir TH2 y comparar con la curva|Comprobar fijación a la tubería|Revisar entrada de placa", "La unidad interior detiene la operación protegida y vuelve a comprobar la entrada."),
    error_spec("P4", "Conector de boya CN4F abierto", "indoor", "PLARP", "24", "La placa no detecta cerrado el circuito de la boya al alimentar o durante control.", "Conector CN4F desconectado|Boya o cable abierto|PCB interior defectuosa", "Cortar alimentación antes de manipular CN4F|Comprobar continuidad de la boya arriba/abajo|Revisar conector y placa", "La unidad inhibe la operación que podría producir condensación."),
    error_spec("P5", "Anomalía de bomba o desbordamiento", "indoor", "PLARP", "24", "La boya permanece bajo agua durante 1 min 30 s con la bomba activada; la repetición confirma el fallo.", "Bomba de drenaje defectuosa|Tubo obstruido o con mala pendiente|Boya bloqueada|PCB interior defectuosa", "Comprobar agua real y desagüe|Alimentar y comprobar la bomba según el manual|Verificar señal de boya y CN4F", "Durante la detección se detienen compresor y ventilador interior; la bomba sigue intentando evacuar. Requiere reset de alimentación tras reparar."),
    error_spec("P5", "Bloqueo del motor de bomba — cassette moderna", "indoor", "PLAM", "25", "La bomba se detiene durante 5 segundos mientras está ordenada; la placa aplaza el error y confirma P5 si la condición se repite cuatro veces.", "Motor de bomba bloqueado|Conector CNP flojo|Salida de 13 VDC ausente|PCB interior defectuosa", "Accionar SWE y medir CNP1-CNP3|Con 13 VDC y sin giro, sustituir bomba|Sin 13 VDC, revisar PCB interior", "La placa mantiene una fase de aplazamiento; al repetirse cuatro veces confirma P5 y detiene la operación protegida."),
    error_spec("P6", "Protección antihielo o sobretemperatura", "indoor", "PLARP", "25", "La temperatura de tubería entra en condición de congelación en frío o sobrecalentamiento en calor.", "Caudal de aire insuficiente|Filtro o batería sucios|Carga o expansión anómala|Sonda incorrecta", "Comprobar filtros, batería y ventilador|Contrastar la sonda|Revisar circuito frigorífico", "La unidad detiene temporalmente el compresor y aplica protección; la lógica distingue frío y calor."),
    error_spec("P8", "Temperatura de tubería incoherente", "indoor", "PLARP", "25", "La evolución de la temperatura de tubería no corresponde al modo solicitado.", "Falta de refrigerante|Válvula de cuatro vías anómala|Sonda o contacto térmico defectuoso|Compresor sin rendimiento", "Esperar los tiempos mínimos de detección: 9 min en frío y 27 min en calor|No valorar durante desescarche|Medir temperaturas y presiones", "La anomalía se evalúa después de los tiempos de estabilización y detiene la demanda si persiste."),
    error_spec("P9", "Sonda de condensador/evaporador TH5", "indoor", "PLAM", "24", "La sonda TH5 se detecta abierta o en cortocircuito.", "Sonda TH5 defectuosa|Cableado o conector defectuoso|PCB interior defectuosa", "Medir resistencia y comparar con la curva|Comprobar ubicación y contacto|Revisar placa", "La unidad interior detiene o limita el control dependiente de TH5."),
    error_spec("PA", "Fuga de agua / parada forzada de compresor", "indoor", "PLARP", "27", "La combinación de diferencia anormal TH1–TH2 y boya bajo agua confirma una fuga o drenaje anormal.", "Fuga de agua|Bomba o desagüe defectuosos|Boya bloqueada|Sondas TH1/TH2 incorrectas", "Revisar bandeja y tubería|Comprobar bomba y boya|Contrastar TH1 y TH2", "El compresor queda bloqueado para evitar más condensación; el código solo se borra cortando y restableciendo alimentación."),
    error_spec("PB", "Motor de ventilador interior", "indoor", "PLAM", "28", "No se obtiene la rotación esperada del ventilador interior.", "Rotor bloqueado|Motor o conector defectuoso|Alimentaciones VDC/VCC incorrectas|PCB interior defectuosa", "Con alimentación desconectada comprobar giro libre|Revisar CNMF|Medir 310–340 VDC y 15 VDC solo con procedimiento seguro", "El ventilador y la operación de la unidad interior se detienen."),
    error_spec("PL", "Circuito frigorífico anormal", "system", "PLARP", "27", "La relación de temperaturas y estado del circuito no confirma un ciclo frigorífico normal.", "Falta de refrigerante|Válvula de cuatro vías defectuosa|Válvula cerrada|Sonda incorrecta", "Comprobar válvulas y carga|Verificar inversión de ciclo|Medir temperaturas y presiones", "El sistema detiene el compresor y requiere reset de alimentación tras corregir."),
    error_spec("E0", "Error de recepción del mando", "controller", "PLARP", "26", "El mando no recibe telegramas válidos de la unidad interior.", "Cable MA abierto o con ruido|Mando incorrectamente configurado Main/Sub|PCB interior o mando defectuosos", "Comprobar TB5 y tensión del mando|Revisar cable separado de potencia|Ejecutar Remote controller check si está disponible", "La orden desde ese mando no es fiable; la unidad afectada puede quedar sin control."),
    error_spec("E1", "Fallo de la placa del mando", "controller", "PLARP", "27", "La autocomprobación interna del mando detecta memoria o circuito de control anormal.", "PCB del mando defectuosa|Alimentación o cableado anómalos", "Comprobar tensión y cable|Reiniciar|Sustituir el mando si reaparece", "El mando deja de controlar correctamente la unidad."),
    error_spec("E2", "Fallo de la placa del mando", "controller", "PLARP", "27", "La autocomprobación interna del mando no finaliza correctamente.", "PCB del mando defectuosa|Ruido o alimentación inestable", "Revisar alimentación y bus|Reiniciar y repetir autocomprobación|Sustituir mando si persiste", "El mando no completa su inicialización o pierde el control."),
    error_spec("E3", "Error de transmisión del mando", "controller", "PLARP", "26", "El mando no consigue enviar telegramas válidos a la unidad interior.", "Cortocircuito o ruido en bus MA|Varios mandos configurados Main|Mando o PCB interior defectuosos", "Comprobar cable, polaridad cuando aplique y configuración Main/Sub|Aislar otros mandos|Ejecutar controller check", "El mando no puede gobernar la unidad interior."),
    error_spec("E4", "Error de recepción mando–interior", "controller", "PLARP", "26", "La unidad interior o el mando no recibe la comunicación esperada.", "Cable de mando abierto|Conector flojo|Dirección o Main/Sub incorrectos|PCB defectuosa", "Medir tensión en el bus|Revisar continuidad y separación de potencia|Probar con un mando conocido", "La unidad asociada queda sin control desde el mando afectado."),
    error_spec("E5", "Error de transmisión mando–interior", "controller", "PLARP", "26", "La transmisión del enlace MA no se completa.", "Cortocircuito o ruido|Dos mandos Main|Mando o PCB defectuosos", "Revisar bus y configuración|Desconectar accesorios para aislar la avería|Repetir Remote controller check", "El control por mando queda interrumpido."),
    error_spec("E6", "Recepción interior–exterior", "system", "PLARP", "27", "La unidad interior no recibe respuesta válida de la exterior por S1/S2/S3.", "Cableado S1/S2/S3 incorrecto|Falta de alimentación exterior|Ruido|PCB interior o exterior defectuosa", "Comprobar 220–240 VAC entre S1-S2|Revisar S2-S3 y el orden de bornes|Comprobar LED y fusibles exteriores", "La unidad interior no permite marcha del compresor; otras unidades no implicadas dependen de la arquitectura."),
    error_spec("E7", "Transmisión interior–exterior", "system", "PLARP", "27", "La unidad interior transmite pero no completa la comunicación con la exterior.", "Cableado S1/S2/S3 defectuoso|Cruce de líneas|PCB interior o exterior defectuosa", "Confirmar orden S1/S2/S3 extremo a extremo|Medir alimentación|Aislar cableado y placas", "La demanda de esa pareja interior/exterior se detiene."),
    error_spec("E8", "Error de recepción de señal exterior", "outdoor", "PUZZM", "67", "La exterior no recibe la señal de control esperada.", "Línea de control abierta|Conector o PCB defectuosos|Ruido eléctrico", "Revisar esquema y cableado|Comprobar alimentación de ambas placas|Observar monitor de operación", "La unidad exterior detiene la operación protegida."),
    error_spec("E9", "Comunicación interior–exterior anormal", "system", "PUZZM", "67", "El intercambio de datos A-Control no se establece de forma válida.", "S1/S2/S3 incorrectos|Interior o exterior sin alimentación|PCB defectuosa|Ruido", "Verificar bornes y tensión|Comprobar continuidad|Revisar historial y LED exterior", "La pareja de unidades queda parada hasta recuperar comunicación."),
    error_spec("EA", "Número o conexión de interiores incorrectos", "system", "PUZZM", "67", "La exterior detecta una combinación o cantidad de unidades no válida.", "Cableado o combinación incorrecta|Dirección o ajuste anómalo|PCB defectuosa", "Comparar instalación con la combinación admitida|Revisar conexiones y alimentación", "La puesta en marcha se bloquea."),
    error_spec("EB", "Cableado interior/exterior incorrecto", "system", "PUZZM", "67", "La secuencia o correspondencia del cableado no es válida.", "Bornes cruzados|Cableado abierto|Unidad incompatible", "Comparar S1/S2/S3 en ambos extremos|Corregir con alimentación desconectada", "El sistema no inicia para evitar una operación incorrecta."),
    error_spec("EC", "Tiempo de arranque de comunicación excedido", "system", "PUZZM", "67", "La red A-Control no queda estable dentro del tiempo previsto.", "Unidad sin alimentación|Cableado largo o defectuoso|PCB no inicializa", "Esperar el arranque normal|Revisar alimentación y cableado|Comprobar placas", "La puesta en marcha se interrumpe."),
    error_spec("ED", "Error de transmisión serie entre placas", "outdoor", "PUZZM", "67", "Las placas de control y potencia de la exterior no intercambian datos.", "Conector entre placas suelto|PCB de control o potencia defectuosa|Alimentación anormal", "Revisar conectores con tensión cortada|Comprobar fuentes|Seguir diagnóstico de PCB", "La exterior detiene compresor y ventiladores."),
    error_spec("EE", "Error de combinación interior/exterior", "system", "PUZZM", "67", "La capacidad o familia conectada no coincide con la exterior.", "Combinación no admitida|Ajuste de capacidad incorrecto|PCB sustituida sin configurar", "Confirmar tablas de combinación|Revisar ajustes y placa de recambio", "La operación queda bloqueada."),
    error_spec("EF", "Error de configuración o combinación", "system", "PUZZM", "68", "La unidad detecta una configuración no compatible.", "Capacidad total incorrecta|Número de unidades excesivo|Dirección o combinación incompatible", "Consultar el subcódigo City Multi cuando exista|Revisar capacidades y direcciones", "El sistema no completa la puesta en marcha."),
    error_spec("F3", "Sensor de baja presión anormal", "outdoor", "PUZZM", "67", "La señal de baja presión está fuera del rango aceptado.", "Sensor defectuoso|Conector abierto|Presión realmente fuera de rango|PCB defectuosa", "Comparar presión real con lectura de monitor|Revisar sensor y cableado", "La exterior detiene o limita el compresor."),
    error_spec("F5", "Sensor o presostato de alta presión", "outdoor", "PUZZM", "67", "La entrada de alta presión es anormal o activa la protección.", "Alta presión real|Sensor/presostato defectuoso|Cable o conector abierto", "Medir presión con instrumental|Comparar con monitor|Revisar conector", "La protección detiene el compresor."),
    error_spec("FC", "Anomalía de presión o circuito exterior", "outdoor", "PUZZM", "67", "La lógica exterior detecta una condición de presión no válida.", "Carga o circulación anormal|Sensor de presión|PCB exterior", "Revisar presiones y válvulas|Comprobar sensores|Seguir subdiagnóstico de la familia", "La exterior protege el circuito frigorífico."),
    error_spec("U1", "Alta presión / presostato 63H", "outdoor", "PUZZM", "68", "La alta presión supera el límite o actúa 63H.", "Intercambiador sucio|Ventilador anormal|Válvula cerrada|Sobrecarga de refrigerante", "Comprobar ventilación y limpieza|Abrir válvulas|Medir presión|Revisar 63H", "El compresor se detiene por protección."),
    error_spec("U2", "Temperatura de descarga alta o falta de refrigerante", "outdoor", "PUZZM", "68", "La temperatura de descarga o la relación frigorífica entra en condición anormal.", "Falta de refrigerante|Válvula cerrada|Sonda de descarga|Expansión anormal", "Buscar fugas y confirmar carga|Comprobar válvulas|Contrastar sonda y presiones", "La exterior reduce frecuencia y, si persiste, detiene el compresor."),
    error_spec("U3", "Sondas exteriores abiertas o en corto", "outdoor", "PUZZM", "68", "Una sonda exterior no entrega una lectura válida.", "NTC defectuosa|Cable o conector abierto|PCB exterior", "Identificar la sonda con monitor/LED|Medir resistencia|Revisar placa", "La exterior detiene o limita la función dependiente de esa sonda."),
    error_spec("U4", "Sonda exterior específica abierta o en corto", "outdoor", "PUZZM", "68", "La entrada de temperatura indicada por la familia está fuera de rango.", "Sonda defectuosa|Conector o cable|PCB", "Consultar el subcódigo o monitor|Medir y comparar con curva|Revisar conector", "La exterior protege la operación."),
    error_spec("U5", "Temperatura de disipador o PCB elevada", "outdoor", "PUZZM", "68", "El disipador del inverter supera su límite.", "Ventilación exterior insuficiente|Disipador sucio|Sonda TH8|Módulo de potencia", "Comprobar ventiladores y suciedad|Contrastar TH8|Revisar montaje del módulo", "La frecuencia se limita o el compresor se detiene."),
    error_spec("U6", "Módulo de potencia / sobrecorriente", "outdoor", "PUZZM", "68", "El inverter detecta sobrecorriente o fallo de módulo.", "Compresor bloqueado|Cable U/V/W anormal|Módulo de potencia|Alimentación", "Cortar alimentación y comprobar bobinados/aislamiento|Revisar U/V/W|Seguir prueba del módulo", "El compresor se detiene inmediatamente."),
    error_spec("U7", "Sobrecalentamiento de descarga insuficiente", "outdoor", "PUZZM", "68", "La descarga permanece demasiado fría para la condición de marcha.", "Sobrecarga de refrigerante|Válvula de expansión demasiado abierta|Sonda de descarga|Retorno de líquido", "Comparar presiones y temperaturas|Comprobar EEV|Contrastar sonda", "La exterior protege el compresor y detiene la operación si persiste."),
    error_spec("U8", "Motor de ventilador exterior", "outdoor", "PUZZM", "68", "No se detecta velocidad o corriente normal del ventilador.", "Aspa bloqueada|Motor o conector defectuoso|PCB exterior", "Comprobar giro libre sin tensión|Medir 310–350 VDC, 15 VDC y señal solo con procedimiento seguro|Revisar motor", "La exterior detiene el compresor para evitar alta presión."),
    error_spec("U9", "Tensión, fase o sincronismo de alimentación", "outdoor", "PUZZM", "68", "El inverter detecta sobretensión, subtensión, fase abierta o señal de sincronismo anormal.", "Red fuera de rango|Fase abierta|Conexión floja|Circuito PAM/PCB", "Medir tensión entre fases|Revisar bornes y fusibles|Consultar monitor de bus DC", "La exterior bloquea el inverter."),
    error_spec("UD", "Protección de alta presión / unidad exterior", "outdoor", "PUZZM", "68", "La exterior activa una protección asociada a presión o temperatura.", "Caudal de aire insuficiente|Válvula cerrada|Carga anormal|Sensor", "Comprobar intercambiador y ventilador|Medir presión|Revisar sensores", "El compresor se detiene por protección."),
    error_spec("UF", "Compresor bloqueado o sobrecorriente al arrancar", "outdoor", "PUZZM", "68", "El inverter no consigue hacer girar el compresor.", "Compresor bloqueado|U/V/W incorrectos|Módulo de potencia|Presiones no igualadas", "Comprobar bobinados y aislamiento|Revisar cableado|Esperar igualación y repetir", "El intento de arranque se cancela."),
    error_spec("UH", "Sensor de corriente", "outdoor", "PUZZM", "68", "La lectura del transformador o sensor de corriente no es coherente.", "Sensor de corriente|Cableado|PCB de potencia", "Consultar monitor|Revisar conexión del sensor|Seguir diagnóstico de placa", "El inverter se bloquea o limita."),
    error_spec("UL", "Baja presión / falta de refrigerante", "outdoor", "PUZZM", "68", "La presión de aspiración cae por debajo del rango permitido.", "Fuga o falta de refrigerante|Válvula cerrada|Restricción|Sensor", "Buscar fugas|Abrir válvulas|Medir presiones|Revisar expansión y sensor", "El compresor se detiene para protegerse."),
    error_spec("UP", "Sobrecorriente del compresor", "outdoor", "PUZZM", "68", "La corriente del compresor supera el límite.", "Compresor bloqueado|Presiones anormales|Alimentación incorrecta|Módulo inverter", "Medir tensión y corriente|Comprobar presiones|Revisar compresor e inverter", "La exterior detiene el compresor."),
]


CITY_CODES = [
    ("0403", "Comunicación serie entre placa de control y placa de potencia", "outdoor", "43", "Conector entre placas o PCB defectuosa", "Revisar conectores y alimentaciones con tensión cortada", "La unidad exterior detiene su funcionamiento.", "Ed"),
    ("1102", "Temperatura de descarga del compresor", "outdoor", "45", "Falta de refrigerante, válvula cerrada, TH4 o expansión anormal", "Confirmar que TH4 no supera 110 °C durante 5 min ni 125 °C; revisar carga y válvulas", "El compresor se detiene y puede reintentar tras protección.", "U2"),
    ("1302", "Alta presión", "outdoor", "47", "Presostato 63H, sensor 63HS, caudal o carga anormal", "Comprobar 63H 4,15 MPa y 63HS; revisar ventiladores, válvulas y carga", "El compresor se detiene por alta presión.", "UE"),
    ("1500", "Sobrecalentamiento de descarga demasiado bajo", "outdoor", "48", "Retorno de líquido, sobrecarga o EEV abierta", "Comparar presión y temperatura de descarga; revisar EEV y carga", "La exterior protege el compresor.", "U7"),
    ("1501", "Falta de refrigerante o válvula cerrada en frío", "system", "49", "Fuga, carga insuficiente o válvula de servicio cerrada", "Buscar fugas, confirmar carga y abrir válvulas", "El circuito afectado se detiene.", "U2"),
    ("1503", "Congelación de Branch Box o unidad interior", "system", "50", "Caudal de aire insuficiente, expansión o sonda", "Revisar filtros, ventiladores, EEV y sondas", "La unidad o rama afectada se protege.", "P6"),
    ("1508", "Válvula de cuatro vías anormal en calefacción", "outdoor", "51", "Bobina, válvula, cableado o circuito frigorífico", "Comprobar bobina y cambio de presiones/temperaturas", "La calefacción se detiene.", "EF"),
    ("4100", "Compresor bloqueado", "outdoor", "53", "Compresor mecánicamente bloqueado o U/V/W incorrectos", "Comprobar bobinados, aislamiento y cableado al inverter", "El compresor no arranca.", "UF"),
    ("4114", "Motor de ventilador interior", "indoor", "54", "Motor bloqueado, cable o PCB interior", "Comprobar giro, conector y alimentaciones", "Solo la unidad interior afectada se detiene.", "PB"),
    ("4210", "Sobrecorriente del compresor", "outdoor", "55", "Carga mecánica, presión, alimentación o inverter", "Medir corriente/tensión y revisar circuito frigorífico", "El compresor se detiene.", "UP"),
    ("4220", "Tensión PAM, fase abierta o sincronismo", "outdoor", "56", "Alimentación fuera de rango, fase o PCB", "Medir red y bus DC; revisar bornes y fusibles", "El inverter queda bloqueado.", "U9"),
    ("4230", "Temperatura de disipador", "outdoor", "57", "Ventilación, TH8 o módulo de potencia", "Comprobar ventilador, disipador y TH8", "El compresor se limita o detiene.", "U5"),
    ("4250", "Módulo de potencia", "outdoor", "65", "Módulo, compresor, U/V/W o alimentación", "Usar el diagnóstico SW7-1 y devolverlo a OFF al terminar; comprobar compresor", "El compresor se detiene inmediatamente.", "U6"),
    ("4400", "Motor de ventilador exterior", "outdoor", "66", "Motor, conector, alimentación o PCB", "Comprobar 310–350 VDC, 15 VDC y señal 0–6,5 V con seguridad", "La exterior detiene o limita el circuito.", "U8"),
    ("5101", "Sonda de descarga TH4", "outdoor", "67", "TH4 abierta ≤3 °C o en corto ≥217 °C", "Medir TH4 y revisar conector/placa", "La exterior detiene la función protegida.", "U3"),
    ("5102", "Sonda de tubería de líquido TH6", "outdoor", "68", "TH6 abierta ≤−40 °C o en corto ≥90 °C", "Comparar lectura de monitor con resistencia real", "La exterior protege el circuito.", "U4"),
    ("5105", "Sonda de líquido exterior TH3", "outdoor", "69", "TH3 abierta ≤−40 °C o en corto ≥90 °C", "Medir sonda y cableado", "La operación dependiente de TH3 se detiene.", "U4"),
    ("5106", "Sonda de aire exterior TH7", "outdoor", "70", "TH7 abierta ≤−40 °C o en corto ≥90 °C", "Contrastar temperatura real y lectura", "La exterior limita o detiene la regulación.", "U4"),
    ("5109", "Sonda de tubería HIC TH2", "outdoor", "71", "TH2 abierta ≤−40 °C o en corto ≥90 °C", "Medir sonda, conector y PCB", "La exterior protege el HIC.", "U4"),
    ("5110", "Sonda de disipador TH8", "outdoor", "72", "TH8 abierta ≤−35,1 °C o en corto ≥170,3 °C", "Contrastar TH8 y revisar montaje del disipador", "El inverter queda limitado o detenido.", "U4"),
    ("5201", "Sensor de alta presión 63HS", "outdoor", "73", "Señal de presión fuera de rango, conector o sensor", "Comparar manómetro con monitor; revisar alimentación y señal", "El compresor se detiene.", "F5"),
    ("5202", "Sensor de baja presión 63LS", "outdoor", "74", "Señal de baja fuera de rango, sensor o cable", "Comparar presión real con monitor y revisar sensor", "El compresor se protege.", "F3"),
    ("5300", "Sensor de corriente", "outdoor", "75", "Sensor o placa no detectan corriente coherente", "Revisar sensor, conectores y PCB de potencia", "El inverter queda bloqueado.", "UH"),
    ("6600", "Dirección M-NET duplicada", "network", "76", "Dos dispositivos comparten dirección", "Localizar duplicidad y reasignar; reiniciar red", "Los dispositivos implicados no comunican correctamente.", "A0"),
    ("6602", "Hardware de transmisión M-NET", "network", "77", "Circuito de transmisión o bus anormal", "Medir 17–30 VDC y aislar tramos/dispositivos", "El nodo afectado queda fuera de la red.", "A2"),
    ("6603", "Bus M-NET ocupado", "network", "78", "Colisión continua, cortocircuito o ruido", "Comprobar forma de onda, tensión y topología", "La comunicación de la red queda degradada o parada.", "A3"),
    ("6606", "Procesador de comunicaciones M-NET", "network", "79", "Procesador o PCB de transmisión defectuosos", "Reiniciar y aislar el nodo; sustituir PCB si persiste", "El dispositivo afectado deja de comunicar.", "A6"),
    ("6607", "Sin ACK en M-NET", "network", "80", "Destino sin alimentación, dirección errónea o línea abierta", "Comprobar atributo/dirección de origen y destino antes de sustituir una unidad", "Puede detenerse el objeto al que no llega confirmación sin que ese objeto sea necesariamente defectuoso.", "A7"),
    ("6608", "Sin respuesta M-NET", "network", "81", "Destino no responde, bus abierto o dirección incorrecta", "Verificar alimentación, dirección, tensión y continuidad", "La unidad o grupo relacionado puede quedar detenido.", "A8"),
    ("6831", "Mando MA: error de recepción", "controller", "82", "Cable MA, mando o PCB interior", "Medir 8,5–12 VDC en el mando y ejecutar controller check", "El mando afectado pierde el control.", "E0"),
    ("6832", "Mando MA: error de transmisión", "controller", "82", "Ruido, cortocircuito o mando defectuoso", "Revisar línea y otros mandos; controller check muestra E3/6832 ante ruido o dispositivo anómalo", "El mando no transmite órdenes.", "E3"),
    ("6833", "Unidad interior: recepción desde mando MA", "controller", "82", "Cableado, configuración Main/Sub o PCB", "Revisar TB5, mandos y configuración", "La unidad asociada queda sin control.", "E5"),
    ("6834", "Unidad interior: transmisión al mando MA", "controller", "82", "Línea o PCB interior defectuosa", "Comprobar cable y probar con mando conocido", "El mando no recibe estado de la unidad.", "E4"),
    ("7100", "Capacidad total conectada incorrecta", "system", "83", "Suma de capacidades fuera del rango", "Recalcular capacidad y revisar ajustes", "La puesta en marcha queda bloqueada.", "EF"),
    ("7101", "Código de capacidad incorrecto", "system", "83", "Placa o ajuste de capacidad no corresponde", "Verificar código y placa de sustitución", "La unidad no inicia.", "EF"),
    ("7102", "Demasiadas unidades o Branch Boxes", "system", "83", "Número conectado supera el permitido", "Contar unidades y comprobar topología", "El sistema no completa la inicialización.", "EF"),
    ("7105", "Dirección de unidad incorrecta", "network", "83", "Dirección fuera de rango o incompatible", "Revisar direcciones interior, exterior y refrigerante", "La unidad direccionada incorrectamente no entra en servicio.", "EF"),
    ("7130", "Combinación de unidades incompatible", "system", "83", "Familias o capacidades no admitidas", "Comparar con tabla de combinación", "El sistema bloquea la puesta en marcha.", "EF"),
]


RESIDENTIAL_FLASH = [
    ("POWER continuo 0,5 s", "Avería recordada en unidad interior o exterior", "system", "25", "Existe una avería memorizada; el patrón continuo confirma el recall.", "Consultar después el número de parpadeos y si hay 3 s encendido antes del patrón", "El modo recall no fuerza una nueva avería; solo recupera memoria.", "MSZ"),
    ("POWER ×1", "Sonda de ambiente interior TH1", "indoor", "25", "En el recall de la unidad interior, un parpadeo identifica TH1.", "Medir TH1 y comprobar CN20/cableado", "La unidad interior se detiene o limita la regulación.", "MSZ"),
    ("POWER ×2", "Sondas de batería interior TH2/TH5", "indoor", "25", "En el recall interior, dos parpadeos identifican las sondas de tubería.", "Medir TH2/TH5, comprobar contacto térmico y cableado", "La unidad interior protege el ciclo.", "MSZ"),
    ("POWER ×3", "Comunicación serie interior–exterior", "system", "25", "En el recall interior, tres parpadeos identifican la comunicación serie.", "Comprobar alimentación y cable entre interior y exterior", "La pareja interior/exterior queda sin marcha normal.", "MSZ"),
    ("POWER ×4", "Sobrecorriente o fallo de arranque del compresor", "outdoor", "36", "La exterior detecta sobrecorriente o sincronismo anormal.", "Revisar compresor, U/V/W, alimentación y módulo", "El compresor se detiene.", "MUZ"),
    ("POWER ×5", "Temperatura de descarga elevada", "outdoor", "36", "La descarga supera el límite de la familia.", "Comprobar refrigerante, válvulas y sonda; el manual permite reintento al bajar a 100 °C tras el retardo", "La exterior detiene el compresor y puede reintentar tras tres minutos.", "MUZ"),
    ("POWER ×6", "Protección de alta presión", "outdoor", "37", "La temperatura/presión de condensación entra en protección.", "Comprobar caudal de aire, ventilador, suciedad y carga", "El compresor se detiene temporalmente."),
    ("POWER ×7", "Temperatura de disipador o PCB elevada", "outdoor", "37", "El inverter o su placa supera el límite térmico.", "Revisar ventilación, disipador y sonda", "La exterior limita o detiene el compresor.", "MUZ"),
    ("POWER ×8", "Motor de ventilador exterior", "outdoor", "37", "La exterior no detecta rotación normal.", "Comprobar giro, conector, motor y PCB", "El compresor se detiene para evitar presión alta.", "MUZ"),
    ("POWER ×9", "Memoria o módulo de potencia exterior", "outdoor", "37", "La autocomprobación de PCB/módulo no es correcta.", "Reiniciar, revisar alimentación y placa de potencia", "La exterior queda bloqueada.", "MUZ"),
    ("POWER ×10", "Temperatura de descarga demasiado baja", "outdoor", "38", "La descarga no alcanza el sobrecalentamiento previsto.", "Revisar carga, EEV, retorno de líquido y sonda", "La exterior protege el compresor.", "MUZ"),
    ("POWER ×11", "Motor de ventilador interior", "indoor", "25", "En el recall interior, once parpadeos identifican el ventilador.", "Comprobar giro, motor, conector y PCB interior", "La unidad interior se detiene.", "MSZ"),
    ("POWER ×12", "Placa de control interior", "indoor", "25", "La PCB interior no supera su autocomprobación.", "Revisar alimentación, conectores y PCB", "La unidad interior se detiene.", "MSZ"),
    ("POWER ×14+", "Válvula de servicio, cuatro vías o falta de refrigerante", "outdoor", "38", "Los patrones altos agrupan anomalías de circuito frigorífico.", "Confirmar el conteo exacto y revisar válvulas, carga y cambio de ciclo", "La exterior detiene o limita el compresor.", "MUZ"),
]


RESIDENTIAL_OUTDOOR_EXTRA = [
    error_spec("POWER ×1", "Comunicación serie — diagnóstico exterior", "system", "MUZ", "36", "Tras tres segundos de POWER encendido, un parpadeo corresponde a la comunicación con la interior.", "Cableado interior/exterior|Interior sin alimentación|PCB interior o exterior", "Comprobar cable, alimentación y placas|No confundir con TH1 del recall interior", "La pareja interior/exterior queda detenida."),
    error_spec("POWER ×2", "Alimentación o sincronismo exterior", "outdoor", "MUZ", "36", "Tras la indicación de origen exterior, dos parpadeos corresponden a alimentación.", "Tensión fuera de rango|Conexión floja|Fase o sincronismo de red", "Medir alimentación y revisar bornes/fusibles|No confundir con TH2/TH5 interior", "La exterior no permite el arranque del inverter."),
    error_spec("POWER ×3", "Termistores exteriores", "outdoor", "MUZ", "36", "Tras la indicación de origen exterior, tres parpadeos agrupan sondas exteriores.", "Sonda abierta o en corto|Conector o cable|PCB exterior", "Usar el LED exterior para concretar|Medir la sonda y comparar con curva", "La exterior detiene o limita la función afectada."),
    error_spec("POWER ×11", "Bus de continua o sensor de corriente exterior", "outdoor", "MUZ", "38", "Tras la indicación de origen exterior, once parpadeos corresponden al bus DC o lectura de corriente.", "Alimentación|Circuito PAM|Sensor de corriente|PCB de potencia", "Medir red y bus con seguridad|Revisar sensor y placa|No confundir con ventilador interior", "El inverter queda bloqueado."),
]


LIVE_LED_ERRORS = [
    error_spec("LED exterior ×17", "Sobrecorriente del compresor durante marcha", "outdoor", "MUZ", "39", "La corriente supera el umbral durante funcionamiento.", "Presión o carga elevada|Compresor|Alimentación|Inverter", "Medir corriente y tensión|Comprobar presiones|Revisar compresor", "La exterior detiene el compresor."),
    error_spec("LED exterior ×18", "Protección de temperatura de descarga", "outdoor", "MUZ", "39", "La descarga supera el límite de protección.", "Falta de refrigerante|Sonda|Válvula cerrada|Expansión", "Contrastar sonda|Revisar carga y válvulas", "El compresor se detiene y puede reintentar."),
    error_spec("LED exterior ×19", "Protección de alta presión", "outdoor", "MUZ", "39", "La condición de condensación es excesiva.", "Intercambiador sucio|Ventilador|Sobrecarga", "Revisar caudal, limpieza y carga", "La exterior detiene el compresor."),
    error_spec("LED exterior ×20", "Protección del módulo inverter", "outdoor", "MUZ", "39", "El módulo detecta temperatura o corriente anormal.", "Disipación|Módulo|Compresor|Alimentación", "Revisar disipador, módulo y compresor", "El inverter queda bloqueado."),
]


def build_interpretation(interpretation_id: int, spec: dict[str, str]) -> dict[str, Any]:
    ref = spec["ref"]
    info: list[dict[str, Any]] = []
    item_id = interpretation_id * 100

    def add(item_type: str, body: str) -> None:
        nonlocal item_id
        item_id += 1
        info.append({
            "id": item_id,
            "item_type": item_type,
            "title": None,
            "body": body,
            "sort_order": len(info) + 1,
            "review_status": "reviewed",
            "origin_ref": SOURCES[ref]["document_ref"],
        })

    add("machine_behavior", spec["behavior"])
    add("related_element", spec["title"])
    for row in split_items(spec["causes"]):
        add("cause", row)
    for row in split_items(spec["checks"]):
        add("check", row)
    add(
        "observation",
        f"Variante documentada en {SOURCES[ref]['document_ref']}. "
        "Confirme familia, forma de indicación y subcódigo antes de aplicar la prueba.",
    )
    return {
        "id": interpretation_id,
        "title": spec["title"],
        "description": spec["description"],
        "source_kind": "official",
        "confidence": "high",
        "review_status": "reviewed",
        "info_items": info,
        "operational_impacts": [operational_impact(spec["behavior"])],
        "datasets": datasets_for(spec["code"], interpretation_id, ref),
        "sources": [
            source(
                ref,
                spec["page"],
                f"Diagnóstico — {spec['code']}: {spec['title']}",
            )
        ],
        "_aliases": split_items(spec.get("aliases", "")),
        "_scope": spec["scope"],
    }


def build_errors() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    specs = list(A_CONTROL_ERRORS)
    for code, title, scope, page, cause, check, behavior, alias in CITY_CODES:
        specs.append(error_spec(
            code,
            title,
            scope,
            "PUMY",
            page,
            f"Subcódigo CITY MULTI {code}; en el display corto puede aparecer como {alias}.",
            cause,
            check,
            behavior,
            alias,
        ))
        # El código corto se conserva como otra forma de búsqueda y como
        # interpretación de la familia City Multi, sin sustituir la de Mr. Slim.
        specs.append(error_spec(
            alias,
            f"{title} — variante CITY MULTI {code}",
            scope,
            "PUMY",
            page,
            f"El display corto {alias} corresponde al subcódigo completo {code} en esta familia.",
            cause,
            check,
            behavior,
            code,
        ))

    for row in RESIDENTIAL_FLASH:
        if len(row) == 8:
            code, title, scope, page, description, checks, behavior, ref = row
        else:
            code, title, scope, page, description, checks, behavior = row
            ref = "MUZ"
        specs.append(error_spec(
            code,
            title,
            scope,
            ref,
            page,
            description,
            "Sonda, cableado, componente o condición descritos por el patrón",
            checks,
            behavior,
        ))
    specs.extend(RESIDENTIAL_OUTDOOR_EXTRA)
    specs.extend(LIVE_LED_ERRORS)

    by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    interpretation_id = 0
    for spec in specs:
        interpretation_id += 1
        by_code[spec["code"]].append(build_interpretation(interpretation_id, spec))

    indexes: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    for error_id, code in enumerate(sorted(by_code, key=normalize), start=1):
        interpretations = by_code[code]
        scopes = {item.pop("_scope") for item in interpretations}
        scope = next(iter(scopes)) if len(scopes) == 1 else "system"
        alias_values = {code}
        for interpretation in interpretations:
            alias_values.update(interpretation.pop("_aliases"))
        aliases = [
            {"alias_display": alias, "alias_normalized": normalize(alias).replace(" ", "")}
            for alias in sorted(alias_values, key=normalize)
        ]
        short_label = interpretations[0]["title"] if len(interpretations) == 1 else f"{len(interpretations)} interpretaciones documentadas"
        tags = sorted({
            token.lower()
            for interpretation in interpretations
            for token in normalize(interpretation["title"] + " " + interpretation["description"]).split()
            if len(token) >= 4
        })[:18]
        search_blob = " ".join(
            [code, short_label]
            + [row["alias_display"] for row in aliases]
            + [
                " ".join(
                    [item["title"], item["description"]]
                    + [row["body"] for row in item["info_items"]]
                )
                for item in interpretations
            ]
        )
        index = {
            "id": error_id,
            "code_display": code,
            "code_normalized": normalize(code).replace(" ", ""),
            "indication_type": "display_led_or_controller",
            "unit_scope": scope,
            "short_label": short_label,
            "interpretation_count": len(interpretations),
            "search_text": normalize(search_blob),
        }
        detail = {
            **{key: value for key, value in index.items() if key != "interpretation_count" and key != "search_text"},
            "aliases": aliases,
            "tags": tags,
            "interpretations": interpretations,
            "media": [],
        }
        indexes.append(index)
        details.append(detail)
    return indexes, details


def section(section_type: str, title: str, body: str, open_by_default: bool = False) -> dict[str, Any]:
    return {
        "section_type": section_type,
        "title": title,
        "body": body,
        "collapsed_default": 0 if open_by_default else 1,
    }


def step(phase: str, number: int, instruction: str, expected: str | None = None, warning: str = "none") -> dict[str, Any]:
    return {
        "phase": phase,
        "step_no": number,
        "instruction": instruction,
        "expected_result": expected,
        "warning_level": warning,
    }


def controller(
    family: str,
    wires: str,
    polarity: str,
    voltage: str | None,
    terminals: str,
    startup: str,
    notes: str,
    cable_spec: str = "Cable de control separado de potencia.",
) -> dict[str, Any]:
    return {
        "interface_type": "mando cableado",
        "controller_family": family,
        "wire_count": wires,
        "polarity": polarity,
        "nominal_voltage": voltage,
        "terminals": terminals,
        "cable_colors": None,
        "cable_spec": cable_spec,
        "startup_behavior": startup,
        "maximum_scope": "Una unidad o grupo compatible según la familia.",
        "notes": notes,
    }


def option(value: str, label: str, effect: str, factory: bool = False) -> dict[str, Any]:
    return {"option_value": value, "option_label": label, "effect": effect, "is_factory": factory}


def parameter(
    code: str,
    name: str,
    description: str,
    options: list[dict[str, Any]],
    factory: str | None = None,
    dependencies: str | None = None,
    warnings: str | None = None,
) -> dict[str, Any]:
    return {
        "parameter_code": code,
        "name": name,
        "description": description,
        "factory_value": factory,
        "dependencies": dependencies,
        "warnings": warnings,
        "options": options,
    }


def variant(
    variant_id: int,
    topic_id: int,
    title: str,
    recognition: str,
    system_type: str,
    unit_scope: str,
    purpose: str,
    summary: str,
    sections: list[dict[str, Any]],
    steps: list[dict[str, Any]],
    source_ref: str,
    page: str,
    source_section: str,
    *,
    page_end: str | None = None,
    refrigerant: str | None = None,
    controller_profile: dict[str, Any] | None = None,
    parameters: list[dict[str, Any]] | None = None,
    monitoring_points: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": variant_id,
        "topic_id": topic_id,
        "title": title,
        "recognition": recognition,
        "system_type": system_type,
        "unit_scope": unit_scope,
        "refrigerant": refrigerant,
        "purpose": purpose,
        "summary": summary,
        "source_kind": "official",
        "review_status": "reviewed",
        "sort_order": variant_id,
        "visible": 1,
        "sections": sections,
        "steps": steps,
        "parameters": parameters or [],
        "controller": controller_profile,
        "monitoring_points": monitoring_points or [],
        "media": [],
        "sources": [source(source_ref, page, source_section, page_end)],
    }


TOPIC_DEFS = [
    (1, "diagnostic_access", "obtain-error-codes", "Cómo obtener códigos y subcódigos", "Cinco métodos reconocibles desde mandos, receptor inalámbrico, PCB y display."),
    (2, "history_reset", "history-and-reset", "Historial, self-check y borrado", "Memoria PAR-41 y recall residencial con salida segura."),
    (3, "controllers_buses", "ma-controllers", "Mandos MA: cableado y arranque", "PAR-41, PAR-21 y PAC-YT52 con sus diferencias visibles."),
    (4, "controllers_buses", "controller-communication", "Fallo de comunicación del mando", "Tensión, controller check, Main/Sub y aislamiento de la avería."),
    (5, "service_modes", "emergency-operation", "Funcionamiento de emergencia", "Variantes mural, cassette y CITY MULTI."),
    (6, "commissioning", "test-run", "Test Run y prueba de puesta en marcha", "Procedimientos actual, Mr. Slim, PUMY y CITY MULTI antiguo."),
    (7, "service_modes", "pump-down", "Pump Down y recogida de refrigerante", "Variantes multisplit y CITY MULTI sin presentar una como universal."),
    (8, "configuration", "function-settings", "Programación desde mando", "Function Settings de Mr. Slim y CITY MULTI."),
    (9, "configuration", "board-switches", "DIP switch, selectores y opciones de placa", "Ajustes MXZ, cassette y exterior."),
    (10, "drainage_overflow", "cassette-drainage", "Cassette: bomba, boya y desbordamiento", "Secuencias P4, P5 y PA en dos generaciones."),
    (11, "multisplit", "automatic-line-correction", "Corrección automática de tuberías y cableado", "Dos procedimientos MXZ claramente diferenciados."),
    (12, "multisplit", "mxz-service-settings", "Ajustes técnicos MXZ", "Bloqueo de modo, bajo consumo, bajo ruido, corriente y tubería."),
    (13, "city_multi_network", "mnet-network", "Red M-NET: cableado, direcciones y medidas", "Topología, tensión, terminación y forma de onda."),
    (14, "city_multi_network", "city-multi-operation", "CITY MULTI: alcance, estados y emergencia", "Qué se detiene y cuándo puede trabajar con un compresor."),
    (15, "service_tools_boards", "service-tools", "Herramientas y monitorización", "A-Control Service Tool y monitor de operación."),
    (16, "component_checks", "sensors-and-drain", "Sondas, bomba y boya", "Curvas NTC y señales de drenaje."),
    (17, "component_checks", "fans-inverter-pressure", "Ventiladores, inverter y presión", "Valores de ventilador, sensores y protecciones."),
    (18, "technical_values", "quick-electrical-values", "Tensiones y valores rápidos", "Puntos de prueba sin mezclar familias."),
    (19, "normal_states", "normal-waits", "Esperas y estados normales", "Mensajes y tiempos que pueden confundirse con averías."),
    (20, "system_architecture", "family-recognition", "Cómo reconocer la familia técnica", "Pistas visibles antes de elegir un procedimiento."),
    (21, "errors", "error-interpretation-rules", "Cómo usar códigos repetidos", "Reglas para no mezclar A-Control, CITY MULTI y patrones LED."),
    (22, "service_tools_boards", "after-board-replacement", "Después de sustituir una placa", "Ajustes, memoria y comprobaciones que deben recuperarse."),
]


def build_topics() -> list[dict[str, Any]]:
    topics: dict[int, dict[str, Any]] = {}
    for topic_id, category_slug, slug, title, summary in TOPIC_DEFS:
        category = CATEGORY_BY_SLUG[category_slug]
        topics[topic_id] = {
            "id": topic_id,
            "brand_id": BRAND_ID,
            "category_id": category["id"],
            "slug": slug,
            "title": title,
            "summary": summary,
            "active": 1,
            "category": category,
            "variants": [],
        }

    def add(item: dict[str, Any]) -> None:
        topics[item["topic_id"]]["variants"].append(item)

    vid = 0

    def v(
        topic_id: int,
        title: str,
        recognition: str,
        system_type: str,
        unit_scope: str,
        purpose: str,
        summary: str,
        sections: list[dict[str, Any]],
        steps: list[dict[str, Any]],
        ref: str,
        page: str,
        source_section: str,
        **kwargs: Any,
    ) -> None:
        nonlocal vid
        vid += 1
        add(variant(
            vid, topic_id, title, recognition, system_type, unit_scope,
            purpose, summary, sections, steps, ref, page, source_section, **kwargs,
        ))

    # Obtención de códigos y subcódigos.
    v(1, "Cassette — autocheck inalámbrico por pitidos",
      "Mando inalámbrico con botón CHECK hundido y receptor con lámpara OPERATION.",
      "Mr. Slim cassette", "controller",
      "Obtener el código sin desmontar la unidad.",
      "El receptor confirma inicio con dos pitidos; el número de pitidos y parpadeos identifica el código.",
      [
          section("patterns", "Patrón A: interior", "1=P1; 2=P2/P9; 3=E6/E7; 4=P4; 5=P5/PA; 6=P6; 7=EE; 8=P8; 9=E4/E5; 11=PB; 12=FB; 14=PL.", True),
          section("patterns", "Patrón B: exterior", "1=E9; 2=UP; 3=U3/U4; 4=UF; 5=U2; 6=U1/UD; 7=U5; 8=U8; 9=U6; 10=U7; 11=U9/UH; 14=otros."),
          section("invalid", "Dirección no válida", "Tres pitidos continuos después de los dos iniciales indican una dirección de refrigerante incorrecta."),
      ],
      [
          step("prepare", 1, "Detenga la unidad y desactive el temporizador semanal."),
          step("procedure", 1, "Mantenga CHECK durante 5 segundos.", "El mando entra en self-check."),
          step("procedure", 2, "Seleccione la dirección de refrigerante/M-NET con el botón indicado."),
          step("procedure", 3, "Pulse el botón de operación y cuente pitidos y parpadeos."),
          step("exit", 1, "Pulse ON/OFF para salir."),
      ],
      "PLAM", "21", "Self-diagnosis with wireless remote controller", page_end="23")

    v(1, "PAR-41MAA — Self check por dirección",
      "Mando cableado con pantalla retroiluminada y teclas MENU, RETURN, SELECT y F1–F4.",
      "Mr. Slim / CITY MULTI", "controller",
      "Consultar la avería de una dirección concreta.",
      "El menú Diagnosis muestra código, unidad y atributo; permite reiniciar el historial de self-check.",
      [section("result", "Resultado", "Se muestran dirección de refrigerante/M-NET, código, unidad y atributo.", True),
       section("scope", "No confundir", "Error history y Self check son funciones distintas: una recorre memoria y la otra consulta una dirección.")],
      [step("procedure", 1, "Abra Service menu → Diagnosis → Self check."),
       step("procedure", 2, "Introduzca la dirección de refrigerante/M-NET."),
       step("procedure", 3, "Pulse SELECT y espere el resultado."),
       step("exit", 1, "Use RETURN para salir; el reset del historial es una acción separada.")],
      "PAR41", "29", "Self check")

    v(1, "PAR-21MAA — CHECK/CLEAR",
      "Mando cableado clásico con botones físicos CHECK/CLEAR y TEST.",
      "Mr. Slim / CITY MULTI anterior", "controller",
      "Reconocer y consultar un error desde una generación anterior de mando.",
      "Con una anomalía, el código parpadea; CHECK abre la información disponible de unidad y error.",
      [section("recognition", "Cómo reconocerlo", "Botones CHECK/CLEAR y TEST impresos en la carcasa.", True),
       section("difference", "Según sistema", "CITY MULTI y Mr. Slim no presentan exactamente la misma dirección ni la misma longitud de código.")],
      [step("procedure", 1, "Con el código parpadeando, pulse CHECK/CLEAR."),
       step("procedure", 2, "Anote código, dirección y unidad antes de borrar nada."),
       step("exit", 1, "Pulse de nuevo o vuelva a la pantalla normal según el estado del mando.")],
      "PAR21", "4", "Button layout and error indication", page_end="18")

    v(1, "PAC-YT52CRA — interpretar dirección y código",
      "Mando MA simplificado sin el menú completo del PAR-41.",
      "Mr. Slim / CITY MULTI", "controller",
      "Distinguir el formato del error según arquitectura.",
      "Mr. Slim muestra dirección de refrigerante de 2 dígitos y código; CITY MULTI muestra dirección de unidad de 3 dígitos y código de 4.",
      [section("mrslim", "Mr. Slim", "Dirección de refrigerante de 2 dígitos + código.", True),
       section("city", "CITY MULTI", "Dirección de unidad de 3 dígitos + código de 4 dígitos."),
       section("continued", "Error con marcha", "Si solo parpadea el código y el indicador de alimentación permanece encendido, la operación puede continuar aunque exista error.")],
      [step("procedure", 1, "Identifique primero si la instalación es Mr. Slim o CITY MULTI."),
       step("procedure", 2, "Anote todos los dígitos y el estado del indicador de alimentación."),
       step("procedure", 3, "Busque el código completo y después su alias corto.")],
      "PACYT52", "8", "Error display")

    v(1, "M-Series — recuperar avería con el mando inalámbrico",
      "Mando de split con OPERATION SELECT, TEMP y orificio RESET.",
      "M-Series split mural", "controller",
      "Leer la memoria de averías interior y exterior.",
      "La unidad entra en failure mode recall; el POWER continuo confirma memoria y los parpadeos dan el detalle.",
      [section("indoor", "Origen interior", "El patrón empieza directamente después de la confirmación.", True),
       section("outdoor", "Origen exterior", "Tres segundos de POWER encendido antes de los parpadeos identifican la avería exterior."),
       section("setpoint", "Consigna", "El manual interior usa 24 °C; el diagnóstico exterior detallado indica 25 °C.")],
      [step("prepare", 1, "Con el mando parado, mantenga OPERATION SELECT y TEMP mientras pulsa RESET."),
       step("procedure", 1, "Suelte RESET y mantenga los otros dos botones 3 segundos hasta ver todos los segmentos."),
       step("procedure", 2, "Ajuste la consigna indicada por el manual de la unidad y envíe ON/OFF."),
       step("procedure", 3, "Cuente el patrón POWER y, si existe, el LED exterior."),
       step("exit", 1, "Salga cortando alimentación o pulsando RESET en el mando.")],
      "MSZ", "22", "Failure mode recall function", page_end="25")

    # Historial, borrado y recall.
    v(2, "PAR-41MAA — historial de 16 registros",
      "Menú Service → Diagnosis → Error history.",
      "Mr. Slim / CITY MULTI", "controller",
      "Consultar y borrar memoria sin confundirla con errores activos.",
      "Guarda hasta 16 registros; Mr. Slim añade preliminary error history de hasta 32.",
      [section("capacity", "Capacidad", "Error history: 16. Preliminary error history en Mr. Slim: hasta 32.", True),
       section("warning", "Antes de borrar", "Fotografíe o anote dirección, código y orden del registro.")],
      [step("procedure", 1, "Abra Error history desde Diagnosis."),
       step("procedure", 2, "Recorra registros con F1/F2 y anote toda la información."),
       step("clear", 1, "Seleccione Delete solo después de documentar y confirmar la reparación."),
       step("exit", 1, "Vuelva con RETURN.")],
      "PAR41", "28", "Error history and preliminary error history")

    v(2, "M-Series — borrar la memoria después de reparar",
      "Split mural ya situado en failure mode recall.",
      "M-Series", "controller",
      "Eliminar el registro solo después de confirmar la reparación.",
      "El borrado se inicia desde recall y requiere accionar EMERGENCY OPERATION.",
      [section("warning", "No borrar primero", "El patrón memorizado es una pista diagnóstica; regístrelo antes.", True),
       section("exit", "Salida", "Power cycle o RESET del mando terminan el modo recall.")],
      [step("prepare", 1, "Entre en failure mode recall y anote el patrón."),
       step("clear", 1, "Pulse ON/OFF y después el interruptor EMERGENCY OPERATION de la unidad."),
       step("verify", 1, "Repita el recall para confirmar que la memoria se ha borrado."),
       step("exit", 1, "Restablezca el mando con RESET si es necesario.")],
      "MSZ", "24", "Deleting the memorized abnormal condition")

    # Mandos y buses.
    v(3, "PAR-41MAA en CITY MULTI — TB15 sin polaridad",
      "Mando PAR-41 conectado a terminales TB15 de una unidad CITY MULTI.",
      "CITY MULTI", "controller",
      "Cablear correctamente el mando MA.",
      "Dos hilos sin polaridad; longitud máxima documentada 200 m.",
      [section("cable", "Cable", "2 conductores, 0,3 mm² / AWG22, apantallado según instalación.", True),
       section("limit", "Longitud", "Máximo 200 m para la línea del mando.")],
      [step("prepare", 1, "Corte la alimentación de todas las unidades."),
       step("procedure", 1, "Conecte los dos conductores a TB15; no hay polaridad."),
       step("procedure", 2, "Separe la línea de cables de potencia y fuentes de ruido."),
       step("verify", 1, "Alimente y espere la inicialización antes de valorar errores.")],
      "PAR41", "5", "Connecting to CITY MULTI", page_end="6",
      controller_profile=controller("PAR-41MAA / bus MA", "2", "sin polaridad", "8,5–12 VDC en diagnóstico del mando", "TB15", "Inicializa y adquiere datos de la unidad.", "Longitud máxima 200 m.", "0,3 mm² AWG22, 2 conductores"))

    v(3, "PAR-41MAA en Mr. Slim — TB5 y grupos",
      "Mando PAR-41 conectado a TB5 de una interior Mr. Slim.",
      "Mr. Slim", "controller",
      "Cablear uno o dos mandos y un grupo de refrigerante.",
      "Dos hilos sin polaridad; hasta 16 sistemas en grupo. Con un mando, total 500 m; con dos, 200 m.",
      [section("group", "Grupo", "Hasta 16 sistemas de refrigerante compatibles.", True),
       section("controllers", "Mandos", "Máximo dos; deben configurarse Main y Sub."),
       section("length", "Longitud", "Un mando: total 500 m. Dos mandos: total 200 m.")],
      [step("prepare", 1, "Corte alimentación."),
       step("procedure", 1, "Conecte los dos hilos sin polaridad a TB5."),
       step("procedure", 2, "Si hay dos mandos, configure uno Main y otro Sub."),
       step("verify", 1, "Alimente y confirme que ambos terminan el arranque.")],
      "PAR41", "7", "Connecting to Mr. Slim",
      controller_profile=controller("PAR-41MAA / bus MA", "2", "sin polaridad", "8,5–12 VDC en controller check", "TB5", "Puede tardar en adquirir información tras alimentar.", "Hasta 16 refrigerant systems; máximo dos mandos.", "0,3 mm² AWG22, 2 conductores"))

    v(3, "PAR-21MAA — mando clásico Main/Sub",
      "Mando rectangular con tapa y botones CHECK/CLEAR y TEST.",
      "Mr. Slim / CITY MULTI anterior", "controller",
      "Reconocer una generación anterior y evitar duplicar el mando principal.",
      "La selección Main/Sub y las funciones se realizan de modo distinto al PAR-41.",
      [section("recognition", "Pistas", "Botones físicos CHECK/CLEAR y TEST; pantalla segmentada.", True),
       section("main_sub", "Main/Sub", "En un sistema con dos mandos no configure ambos como principal.")],
      [step("prepare", 1, "Identifique el mando y la arquitectura antes de usar un procedimiento moderno."),
       step("procedure", 1, "Revise la selección Main/Sub."),
       step("verify", 1, "Alimente y confirme comunicación antes de programar funciones.")],
      "PAR21", "4", "Names of parts and Main/Sub setting",
      controller_profile=controller("PAR-21MAA", "2", "según bus MA", None, "TB5/TB15 según sistema", "Muestra su pantalla inicial tras adquirir comunicación.", "No aplicar menús del PAR-41."))

    v(4, "PAR-41MAA — Remote controller check",
      "El mando enciende pero no controla, reinicia o muestra errores de comunicación.",
      "Mr. Slim / CITY MULTI", "controller",
      "Separar fallo del mando, ruido de línea y falta de alimentación.",
      "El menú devuelve OK, E3/6832, NG (ALL0/ALL1) o ERC.",
      [section("supply", "Alimentación", "Si no aparece ni una línea en pantalla, comprobar 8,5–12 VDC y cableado.", True),
       section("results", "Resultados", "OK: mando correcto. E3/6832: ruido u otro dispositivo. NG ALL0/ALL1: circuito envío/recepción del mando. ERC: discrepancia de bits, normalmente ruido."),
       section("reboot", "Final", "SELECT termina la prueba y reinicia automáticamente el mando.")],
      [step("procedure", 1, "Abra Diagnosis → Remote controller check."),
       step("procedure", 2, "Pulse SELECT para iniciar."),
       step("procedure", 3, "Interprete el resultado antes de sustituir componentes."),
       step("exit", 1, "Pulse SELECT; el mando se reinicia.")],
      "PAR41", "31", "Remote controller check",
      controller_profile=controller("PAR-41MAA", "2", "sin polaridad", "8,5–12 VDC", "TB5/TB15", "Se reinicia al finalizar el check.", "E3/6832 no condena automáticamente el mando."))

    v(4, "E0/E3/E4/E5 y 6831–6834 — aislar el enlace MA",
      "El código menciona transmisión o recepción entre mando e interior.",
      "Mr. Slim / CITY MULTI", "controller",
      "Diagnosticar el enlace sin cambiar placas por descarte.",
      "El origen puede ser mando, interior, otro mando, cable o ruido; el sentido del código ayuda a aislarlo.",
      [section("direction", "Sentido", "E0/E4: recepción; E3/E5: transmisión. CITY MULTI añade 6831–6834.", True),
       section("noise", "Ruido", "No tender el bus junto a potencia; desconectar accesorios por tramos ayuda a localizar la fuente."),
       section("main_sub", "Dos mandos", "Confirmar un Main y un Sub.")],
      [step("procedure", 1, "Anote código completo y qué dispositivo lo muestra."),
       step("procedure", 2, "Mida la alimentación del mando."),
       step("procedure", 3, "Revise continuidad, empalmes y separación de potencia."),
       step("procedure", 4, "Aísle segundo mando y accesorios; repita controller check."),
       step("verify", 1, "Sustituya un componente solo si el fallo sigue al componente.")],
      "PLARP", "26", "Remote controller transmission and reception errors", page_end="27")

    # Emergencia y prueba.
    v(5, "Split mural — EMERGENCY OPERATION",
      "Unidad interior con pulsador EMERGENCY OPERATION.",
      "M-Series", "indoor",
      "Hacer funcionar la unidad si el mando no está disponible.",
      "Los primeros 30 min son Test Run; después regula a 24 °C, ventilador medio y protección antihielo activa.",
      [section("settings", "Ajustes fijos", "24 °C, ventilador medio y lama horizontal en automático.", True),
       section("protection", "Protecciones", "La protección antihielo de batería sigue activa."),
       section("duration", "Duración", "Continúa hasta una nueva pulsación; los primeros 30 min son Test Run.")],
      [step("procedure", 1, "Pulse EMERGENCY OPERATION para elegir modo según la secuencia de la unidad."),
       step("verify", 1, "Observe ventilador y respuesta de la exterior durante los primeros 30 min."),
       step("exit", 1, "Pulse de nuevo hasta detener.")],
      "MSZ", "21", "Emergency operation")

    v(5, "Cassette — botones de emergencia de la rejilla",
      "Rejilla de cassette con botones físicos de frío y calor.",
      "Mr. Slim cassette", "indoor",
      "Arrancar sin mando normal.",
      "Mantener más de 2 s inicia frío o calor a 24 °C y ventilador alto.",
      [section("cool", "Frío", "24 °C, ventilador alto, lama horizontal.", True),
       section("heat", "Calor", "24 °C, ventilador alto, lama hacia abajo; durante desescarche puede salir aire frío."),
       section("limit", "Limitaciones", "Las lamas pueden no funcionar en emergencia.")],
      [step("procedure", 1, "Mantenga el botón COOL o HEAT de la rejilla más de 2 segundos."),
       step("verify", 1, "Confirme el indicador y la respuesta de la exterior."),
       step("exit", 1, "Pulse el botón de parada de emergencia.")],
      "PLAM", "31", "Emergency operation from grille")

    v(5, "Cassette — SWE en la PCB interior",
      "Placa interior con interruptor SWE documentado.",
      "Mr. Slim cassette", "indoor",
      "Probar ventilador interior y bomba desde la placa.",
      "SWE fuerza ventilador alto y bomba; no inicia si hay fallo exterior, de ventilador o de drenaje.",
      [section("loads", "Elementos activados", "Ventilador interior en alta y bomba de drenaje.", True),
       section("inhibitions", "Qué lo impide", "Fallo exterior, fallo de ventilador interior o fallo de bomba detectado."),
       section("limit", "Límite", "La emergencia en frío se limita a 10 horas.")],
      [step("prepare", 1, "Asegure panel instalado y zona eléctrica protegida."),
       step("procedure", 1, "Accione SWE según la posición indicada en la placa."),
       step("verify", 1, "Compruebe ventilador y evacuación."),
       step("exit", 1, "Devuelva SWE a su posición normal.")],
      "PLAM", "31", "Emergency operation by indoor controller board")

    v(5, "CITY MULTI grande — emergencia con un compresor",
      "Exterior de doble compresor P450–P650 con uno de los códigos permitidos.",
      "CITY MULTI VRF", "outdoor",
      "Mantener servicio temporal con el compresor sano.",
      "Después de los resets indicados, la máquina puede usar el compresor restante durante 4 h en frío o 2 h en calor.",
      [section("allowed", "Códigos permitidos", "4230, 4250, 4240, 4260, 4220, 5301, 4200, 5110, 0403 y 4108, según compresor.", True),
       section("duration", "Duración", "Máximo 4 h en frío o 2 h en calor."),
       section("stop", "Finalización", "Termina por tiempo, por un error no permitido o por corte de alimentación; es una medida temporal.")],
      [step("prepare", 1, "Confirme modelo de doble compresor y código incluido en la lista."),
       step("procedure", 1, "Rearme y deje que la unidad repita la detección según la secuencia del manual."),
       step("procedure", 2, "Si se cumplen las condiciones, confirme funcionamiento del compresor restante."),
       step("exit", 1, "Repare el origen; corte alimentación para finalizar correctamente el modo.")],
      "CITY", "74", "Emergency operation with one compressor", page_end="75")

    v(6, "PAR-41MAA — Test Run desde Service menu",
      "Mando PAR-41 con acceso a Service menu.",
      "Mr. Slim / CITY MULTI compatible", "controller",
      "Ejecutar prueba de frío/calor y observar datos disponibles.",
      "El menú permite Test Run y prueba de bomba de drenaje; las protecciones de máquina siguen activas.",
      [section("password", "Contraseña", "Contraseña de mantenimiento de fábrica: 9999; F1 durante 10 s restablece una contraseña olvidada.", True),
       section("protection", "Protecciones", "Test Run no anula protecciones eléctricas, de presión, temperatura o comunicación.")],
      [step("prepare", 1, "Compruebe instalación, válvulas y alimentación."),
       step("procedure", 1, "Abra Service menu → Test run."),
       step("procedure", 2, "Seleccione modo y arranque."),
       step("verify", 1, "Observe temperaturas, drenaje y respuesta de las unidades."),
       step("exit", 1, "Finalice desde el menú; no corte tensión como método normal de salida.")],
      "PAR41", "22", "Service menu — Test run")

    v(6, "PUMY — condiciones previas y Test Run",
      "Exterior CITY MULTI compacto con mando PAR-4xMAA.",
      "CITY MULTI compacto", "system",
      "Realizar puesta en marcha sin omitir aislamiento, válvulas ni precalentamiento.",
      "La prueba fuerza demanda y termina automáticamente a las 2 h; la temperatura de líquido puede monitorizarse.",
      [section("insulation", "Aislamiento", "500 V y más de 1,0 MΩ en potencia; nunca aplicar megóhmetro a transmisión ni mando.", True),
       section("preheat", "Precalentamiento", "Alimentar la exterior al menos 12 h antes."),
       section("auto_stop", "Final", "Test Run termina automáticamente después de 2 h.")],
      [step("prepare", 1, "Complete instalación, paneles, prueba de fugas/drenaje y abra válvulas."),
       step("prepare", 2, "Compruebe tierra, potencia, transmisión y mando."),
       step("prepare", 3, "Alimente la exterior al menos 12 h."),
       step("procedure", 1, "Inicie Test Run desde el mando PAR-4xMAA."),
       step("verify", 1, "Compruebe temperatura de tubería líquida y todas las unidades."),
       step("exit", 1, "Detenga desde el mando o espere el límite de 2 h.")],
      "PUMY", "41", "Test run prerequisites and procedure", page_end="42")

    v(6, "CITY MULTI antiguo — botón TEST dos veces",
      "Mando cableado antiguo con botón TEST.",
      "CITY MULTI generación anterior", "controller",
      "Ejecutar prueba sin aplicar el menú de un mando moderno.",
      "Dos pulsaciones de TEST inician la prueba; finaliza automáticamente a las 2 h.",
      [section("monitor", "Lectura", "El mando permite comprobar temperatura de tubería líquida durante la prueba.", True),
       section("duration", "Duración", "Parada automática a las 2 h.")],
      [step("prepare", 1, "Compruebe válvulas, direcciones y alimentación."),
       step("procedure", 1, "Pulse TEST dos veces."),
       step("verify", 1, "Compruebe unidades y temperatura de tubería."),
       step("exit", 1, "Detenga desde el mando o espere la parada automática.")],
      "CITYLEG", "76", "Test run from legacy remote controller")

    # Pump down.
    v(7, "MXZ — Pump Down desde interruptor de placa",
      "Exterior multisplit MXZ con procedimiento Pump Down impreso/documentado en placa.",
      "M-Series multisplit", "outdoor",
      "Recoger refrigerante sin confundirlo con la corrección automática SW871.",
      "La variante exacta cambia con la placa; se deben abrir/cerrar válvulas y accionar el interruptor en el orden del manual.",
      [section("warning", "Alta presión y riesgo eléctrico", "Trabajar con manómetros adecuados y no tocar partes energizadas.", True),
       section("not_universal", "No universal", "El nombre y posición del pulsador varían; identifique la placa antes de actuar."),
       section("protections", "Protecciones", "La máquina mantiene protecciones de compresor, corriente y temperatura.")],
      [step("prepare", 1, "Identifique el esquema de la placa y conecte manómetro."),
       step("procedure", 1, "Arranque la función de recogida según el interruptor documentado."),
       step("procedure", 2, "Cierre primero la válvula de líquido y observe la presión."),
       step("procedure", 3, "Cierre gas y detenga antes de entrar en vacío profundo."),
       step("exit", 1, "Corte alimentación y verifique válvulas cerradas.")],
      "MXZ", "170", "Pump down operation")

    v(7, "CITY MULTI — recogida por SW3-6 y Test Run",
      "Exterior CITY MULTI con banco SW3 y posición 3-6 documentada.",
      "CITY MULTI", "outdoor",
      "Recoger refrigerante haciendo participar las interiores del circuito.",
      "El procedimiento usa Test Run en frío y una función de placa; no debe aplicarse a una MXZ.",
      [section("scope", "Participación", "Las unidades interiores del circuito deben estar preparadas para la prueba en frío.", True),
       section("limit", "No mezclar", "La posición SW3-6 pertenece a la familia documentada; confirme serigrafía y manual.")],
      [step("prepare", 1, "Confirme circuito, válvulas, comunicaciones y posibilidad de frío."),
       step("procedure", 1, "Seleccione la función indicada mediante SW3-6."),
       step("procedure", 2, "Ejecute Test Run en frío en las interiores necesarias."),
       step("procedure", 3, "Cierre válvulas siguiendo presión y secuencia del manual."),
       step("exit", 1, "Detenga la prueba y restaure todos los interruptores.")],
      "CITY", "93", "Refrigerant recovery / pump down")

    # Function settings and switches.
    v(8, "PAR-41MAA — Function Setting Mr. Slim",
      "Mando PAR-41 conectado por TB5 a Mr. Slim.",
      "Mr. Slim", "controller",
      "Programar funciones sin desmontar la placa interior.",
      "Permite seleccionar dirección, número de unidad, número de modo y valor.",
      [section("modes", "Funciones frecuentes", "01 recuperación tras corte; 02 termistor; 03 LOSSNAY; 04 tensión; 05 Auto; 07 filtro; 08 ventilador/techo; 09 salidas; 10 filtro opcional; 11 lama.", True),
       section("warning", "Registrar antes", "Anote todos los valores originales antes de modificar.")],
      [step("procedure", 1, "Abra Service menu → Function setting."),
       step("procedure", 2, "Seleccione dirección y número de unidad."),
       step("procedure", 3, "Elija modo y valor; confirme con SELECT."),
       step("verify", 1, "Reinicie si el ajuste lo exige y pruebe la función.")],
      "PAR41", "24", "Function setting for Mr. Slim", page_end="26",
      parameters=[
          parameter("01", "Recuperación tras corte", "Comportamiento después de volver la alimentación.", [option("1", "No", "Permanece parado", True), option("2", "Sí", "Recupera el estado permitido")]),
          parameter("02", "Selección de termistor", "Fuente de temperatura ambiente.", [option("1", "Unidad interior", "Usa retorno", True), option("2", "Mando", "Usa sensor del mando"), option("3", "Promedio", "Combina fuentes cuando sea compatible")]),
          parameter("08", "Velocidad / techo alto", "Adapta caudal a la instalación.", [option("1", "Estándar", "Curva estándar", True), option("2", "Techo alto 1", "Aumenta caudal"), option("3", "Techo alto 2", "Aumenta más")]),
      ])

    v(8, "PAR-41MAA — Function Setting CITY MULTI",
      "Mando PAR-41 conectado por TB15 a una red CITY MULTI.",
      "CITY MULTI", "controller",
      "Programar una unidad o grupo por dirección M-NET.",
      "La navegación se parece a Mr. Slim, pero la selección se hace por dirección y atributos M-NET.",
      [section("address", "Dirección", "Confirme dirección de unidad y atributo antes de enviar.", True),
       section("scope", "Alcance", "Un ajuste puede afectar una unidad o grupo; no lo aplique a toda la red por suposición.")],
      [step("procedure", 1, "Abra Function setting para CITY MULTI."),
       step("procedure", 2, "Seleccione dirección y función."),
       step("procedure", 3, "Lea el valor actual antes de escribir."),
       step("procedure", 4, "Cambie un único ajuste y confirme."),
       step("verify", 1, "Reinicie o pruebe según el efecto del parámetro.")],
      "PAR41", "24", "Function setting for CITY MULTI", page_end="25")

    v(9, "Cassette — capacidad, pareja y opciones de PCB",
      "Placa interior cassette con DIP switch y puentes J41/J42.",
      "Mr. Slim cassette", "indoor",
      "Restaurar configuraciones al sustituir placa o adaptar opciones.",
      "La placa conserva selecciones de capacidad, pareja inalámbrica y funciones opcionales.",
      [section("record", "Antes de tocar", "Fotografíe todos los DIP, puentes y conectores.", True),
       section("replacement", "Placa nueva", "Copie solo los ajustes documentados para la capacidad y opción instaladas.")],
      [step("prepare", 1, "Corte alimentación y espere descarga."),
       step("procedure", 1, "Registre posiciones de DIP, J41/J42 y código de capacidad."),
       step("procedure", 2, "Compare con tabla de la familia."),
       step("verify", 1, "Alimente y ejecute Test Run; compruebe mando y opciones.")],
      "PLAM", "35", "Indoor controller board switches")

    v(9, "MXZ — bloqueo de modo y bajo consumo",
      "Exterior MXZ con bancos SW1/SW2 y, en algunas familias, jumper SC751.",
      "M-Series multisplit", "outdoor",
      "Configurar prioridad frío/calor y standby sin impedir por error el arranque.",
      "La combinación equivocada entre SC751 y SW1-2 puede dejar la exterior sin funcionar.",
      [section("lock", "Bloqueo de modo", "SW1 selecciona el modo permitido en las familias indicadas.", True),
       section("standby", "Bajo consumo", "Low standby necesita combinación compatible de jumper y SW1-2."),
       section("warning", "Riesgo", "No cambiar interruptores energizados salvo indicación expresa.")],
      [step("prepare", 1, "Corte alimentación y registre posiciones."),
       step("procedure", 1, "Identifique si la placa incorpora SC751."),
       step("procedure", 2, "Aplique solo la combinación de la tabla de la familia."),
       step("verify", 1, "Restablezca y compruebe que la exterior inicia.")],
      "MXZ", "173", "Operation mode lock and low standby")

    # Drainage.
    v(10, "Cassette antigua — P5 por boya durante 90 segundos",
      "Cassette PLA-RP con boya CN4F y bomba.",
      "Mr. Slim cassette", "indoor",
      "Entender la secuencia exacta antes de culpar a la placa.",
      "Boya bajo agua 1 min 30 s con bomba activa genera anomalía suspensiva; si se repite, confirma P5.",
      [section("sequence", "Detección", "Bomba ON + boya bajo agua 90 s → anomalía suspensiva. Repetición durante ese estado → P5.", True),
       section("loads", "Qué se detiene", "Compresor y ventilador interior se detienen; la bomba continúa intentando evacuar."),
       section("reset", "Rearme", "Después de reparar, requiere cortar y restablecer alimentación.")],
      [step("procedure", 1, "Compruebe si hay agua real en bandeja."),
       step("procedure", 2, "Revise pendiente, obstrucción y retorno."),
       step("procedure", 3, "Compruebe bomba y estado mecánico de la boya."),
       step("procedure", 4, "Compruebe CN4F y PCB."),
       step("verify", 1, "Rearme y pruebe drenaje con agua.")],
      "PLARP", "24", "P5 drain pump malfunction")

    v(10, "Cassette moderna — bomba 13 VDC y realimentación",
      "Cassette PLA-M con bomba de tres hilos rojo, morado y negro.",
      "Mr. Slim cassette", "indoor",
      "Comprobar bomba, alimentación y señal de giro.",
      "Rojo-negro 13 VDC arranca el motor; morado-negro entrega onda 0–13 V, 5 pulsos por vuelta.",
      [section("supply", "Alimentación", "Rojo–negro: 13 VDC.", True),
       section("feedback", "Realimentación", "Morado–negro: onda cuadrada 0–13 V, 5 pulsos/rotación."),
       section("ten_minutes", "Control", "Si no drena, confirmar si P5 aparece dentro de los 10 min posteriores al arranque.")],
      [step("prepare", 1, "Acceda con medidas de seguridad y compruebe que la boya se mueve."),
       step("procedure", 1, "Compruebe 13 VDC rojo-negro cuando la placa ordena bomba."),
       step("procedure", 2, "Compruebe señal pulsante morado-negro."),
       step("procedure", 3, "Verifique físicamente que sale agua."),
       step("verify", 1, "Si hay tensión y pulsos anómalos, aislar bomba; si no hay tensión, revisar placa y lógica.")],
      "PLAM", "32", "Drain pump and float switch checks")

    v(10, "Cassette moderna — P5 por parada repetida del motor",
      "Cassette PLA-M con bomba DC y señal de rotación, distinta de la lógica antigua de 90 segundos de boya.",
      "Mr. Slim cassette", "indoor",
      "Entender cómo confirma la placa un bloqueo real de la bomba.",
      "Si el motor se detiene 5 s con orden de bomba, la placa aplaza el error; cuatro repeticiones confirman P5.",
      [section("sequence", "Secuencia", "Parada de bomba durante 5 s → aplazamiento. Repetido cuatro veces → P5 confirmado.", True),
       section("voltage", "Separación bomba/placa", "Con SWE activo: 13 VDC en CNP1-CNP3 apunta a bomba; sin 13 VDC apunta a la salida de placa."),
       section("difference", "No confundir generaciones", "La cassette antigua usa boya bajo agua durante 1 min 30 s; esta variante vigila la rotación de la bomba.")],
      [step("procedure", 1, "Compruebe si hay agua, obstrucción o bloqueo mecánico."),
       step("procedure", 2, "Accione SWE y mida CNP1-CNP3."),
       step("procedure", 3, "Con 13 VDC, compruebe bomba y realimentación; sin tensión, revise PCB."),
       step("verify", 1, "Repare, rearme y confirme drenaje real durante más de 10 min.")],
      "PLAM", "25", "Drain pump lock protection operation")

    v(10, "PA — fuga de agua detectada por temperaturas y boya",
      "Cassette PLA-RP que muestra PA tras una anomalía prolongada.",
      "Mr. Slim cassette", "indoor",
      "Distinguir PA de un simple conector P4.",
      "TH1–TH2 menor de −10 °C durante 30 min acumulados y boya bajo agua más de 15 min fuerza parada del compresor.",
      [section("logic", "Lógica", "Diferencia térmica anormal acumulada + boya bajo agua confirma riesgo de fuga.", True),
       section("modes", "Frío y calor", "La detección depende de condensación, bomba y estado de las sondas; no interpretar solo por presencia de agua."),
       section("reset", "Rearme", "Solo power reset después de corregir.")],
      [step("procedure", 1, "Inspeccione bandeja, tubería y fugas."),
       step("procedure", 2, "Compruebe bomba y boya."),
       step("procedure", 3, "Contraste TH1 y TH2."),
       step("verify", 1, "Repare, seque, rearme y pruebe en frío.")],
      "PLARP", "27", "PA forced compressor stop due to water leakage")

    v(10, "PAR-41MAA — prueba independiente de bomba",
      "Mando PAR-41 con Service menu.",
      "Cassette compatible", "controller",
      "Comprobar evacuación sin arrancar un ciclo normal completo.",
      "El menú de servicio permite accionar la bomba en equipos compatibles.",
      [section("water", "Prueba real", "Añada agua de forma controlada; oír la bomba no confirma que el tubo evacúe.", True),
       section("exit", "Final", "Salga desde el menú y compruebe que la bomba se detiene según la lógica.")],
      [step("prepare", 1, "Proteja componentes eléctricos y prepare agua controlada."),
       step("procedure", 1, "Abra Service menu → Test run → Drain pump."),
       step("procedure", 2, "Active y compruebe evacuación completa."),
       step("exit", 1, "Desactive desde el menú y revise retorno de agua.")],
      "PAR41", "22", "Drain pump test")

    # Multisplit.
    v(11, "MXZ de 2 conexiones — corrección por 30 min en frío",
      "Exterior MXZ-2F con SW2 en display PCB.",
      "M-Series multisplit 2 puertos", "outdoor",
      "Detectar y corregir cruce entre A y B.",
      "Una interior funciona en COOL durante 30 min; la placa corrige A/B en software.",
      [section("conditions", "Cuándo puede fallar", "Fuga de gas, válvula cerrada, LEV defectuosa o temperaturas interior/exterior desfavorables.", True),
       section("disable", "Deshabilitación", "No funciona si SW2-2 está OFF."),
       section("record", "Historial", "SW2-3: un parpadeo = no corregido; tres = corregido.")],
      [step("prepare", 1, "Abra válvulas y confirme carga, EEV y temperaturas compatibles."),
       step("procedure", 1, "Haga funcionar una interior en COOL durante 30 min."),
       step("verify", 1, "Compruebe el resultado y correspondencia A/B."),
       step("history", 1, "Con alimentación cortada, active SW2-3; alimente y lea 1 o 3 parpadeos."),
       step("exit", 1, "Corte alimentación, devuelva SW2-3 a OFF y vuelva a alimentar.")],
      "MXZ", "176", "Automatic line correcting — 2-port")

    v(11, "MXZ de 3–6 conexiones — botón SW871",
      "Exterior MXZ con pulsador PIPING/WIRING CORRECTION SW871 y LED rojo/amarillo/verde.",
      "M-Series multisplit 3–6 puertos", "outdoor",
      "Corregir correspondencia de tubos y cables por todos los puertos.",
      "La detección dura 10–15 minutos; detiene las interiores y no funciona a 0 °C o menos.",
      [section("conditions", "Requisitos", "Exterior >0 °C; válvulas abiertas; cableado correcto; alimentar y esperar al menos 1 min.", True),
       section("result", "Resultado", "Rojo encendido, amarillo apagado y verde encendido: completado. Los tres a un parpadeo: no completado."),
       section("history", "Historial", "Mantener SW871 más de 5 s muestra registro 30 s: rojo/amarillo 1 vez = no corregido; 3 veces = corregido."),
       section("operation", "Efecto", "Las interiores no pueden funcionar durante la detección; si estaban en marcha, se detienen.")],
      [step("prepare", 1, "Compruebe temperatura exterior, válvulas y tuberías no aplastadas."),
       step("prepare", 2, "Alimente y espere 1 min."),
       step("procedure", 1, "Pulse SW871 sin tocar partes energizadas."),
       step("procedure", 2, "Espere 10–15 min y lea los tres LED."),
       step("exit", 1, "Pulse el botón para cancelar solo si es necesario; pruebe todas las interiores al finalizar.")],
      "MXZ", "177", "Automatic line correcting — SW871")

    v(12, "MXZ — Low Noise y límite de corriente",
      "Exterior con SW1/SW2 y tabla de opciones en la tapa o manual.",
      "M-Series multisplit", "outdoor",
      "Reducir ruido o limitar demanda eléctrica sin confundirlo con avería.",
      "La posición cambia según tamaño: algunas familias usan SW1-3, otras SW1-5; el límite de corriente está solo en ciertos modelos.",
      [section("noise", "Low Noise", "SW1-3 en familias pequeñas o SW1-5 en otras; confirme la tabla.", True),
       section("current", "Límite de corriente", "SW2 solo está disponible en modelos concretos y reduce capacidad máxima."),
       section("symptom", "Efecto visible", "La máquina puede parecer que rinde poco aunque no tenga avería.")],
      [step("prepare", 1, "Registre posiciones y corte alimentación."),
       step("procedure", 1, "Compare placa y tabla de la familia."),
       step("procedure", 2, "Cambie una sola opción."),
       step("verify", 1, "Alimente y compruebe ruido, corriente y capacidad.")],
      "MXZ", "175", "Low noise and current limit")

    v(12, "MXZ — tubería larga y tubería existente sobredimensionada",
      "Exterior con opciones SW1-6 y SW2-6 documentadas.",
      "M-Series multisplit", "outdoor",
      "Adaptar control a una instalación especial.",
      "SW1-6 se usa para tubería larga; SW2-6 para tubería existente sobredimensionada en familias compatibles.",
      [section("long", "Tubería larga", "SW1-6 modifica el control para la longitud indicada.", True),
       section("oversize", "Tubería existente", "SW2-6 solo cuando el diámetro y la familia están expresamente admitidos."),
       section("warning", "No compensar defectos", "No usar estas opciones para ocultar carga incorrecta, estrangulamientos o pérdidas.")],
      [step("prepare", 1, "Mida longitud, desnivel y diámetros."),
       step("procedure", 1, "Confirme que la combinación está permitida."),
       step("procedure", 2, "Corte alimentación y ajuste el switch indicado."),
       step("verify", 1, "Compruebe presiones, temperaturas y capacidad en prueba.")],
      "MXZ", "178", "Evaporating temperature, long piping and existing pipe")

    # M-NET and CITY MULTI.
    v(13, "M-NET — tensión y aislamiento por tramos",
      "Red de transmisión CITY MULTI con conectores y direcciones M-NET.",
      "CITY MULTI", "network",
      "Separar falta de alimentación, cortocircuito, línea abierta y dispositivo defectuoso.",
      "La tensión normal documentada en diagnóstico es 17–30 VDC; se debe medir y aislar por segmentos.",
      [section("voltage", "Tensión", "17–30 VDC en la familia PUMY/CITY MULTI documentada.", True),
       section("no_megger", "Advertencia", "Nunca aplicar megóhmetro a transmisión ni mando."),
       section("scope", "Método", "Desconectar ramales con alimentación cortada y volver a medir evita condenar todas las placas.")],
      [step("prepare", 1, "Anote direcciones y corte alimentación antes de desconectar."),
       step("procedure", 1, "Mida tensión M-NET en el punto de alimentación."),
       step("procedure", 2, "Si es anormal, divida la red por tramos."),
       step("procedure", 3, "Revise polaridad/continuidad según esquema, empalmes, pantallas y dispositivos."),
       step("verify", 1, "Reconecte por etapas y confirme comunicación.")],
      "PUMY", "76", "M-NET transmission troubleshooting")

    v(13, "M-NET — direccionamiento y rangos de PUMY",
      "PUMY con unidades interiores y, cuando aplica, Sub/main M-NET.",
      "CITY MULTI compacto", "network",
      "Evitar duplicidades y direcciones derivadas incorrectas.",
      "La familia documenta direcciones 101–150 para Main M-NET y 151–200 para Sub, derivadas de la interior principal.",
      [section("main", "Main", "101–150 = dirección de interior principal +100.", True),
       section("sub", "Sub", "151–200 = dirección de interior principal +150."),
       section("distance", "Distancias", "Recorrido máximo vía exterior 500 m; segmento más largo 200 m; cable de mando 200 m.")],
      [step("prepare", 1, "Haga una tabla de todos los dispositivos y direcciones."),
       step("procedure", 1, "Compruebe duplicados y rangos."),
       step("procedure", 2, "Verifique longitudes y derivaciones."),
       step("verify", 1, "Reinicie la red y confirme que desaparecen 6600/6607/6608.")],
      "PUMY", "30", "M-NET addresses and wiring length")

    v(13, "M-NET — forma de onda, ruido y pantalla",
      "Instalación CITY MULTI grande con fallos intermitentes o 6603/6607/6608.",
      "CITY MULTI VRF", "network",
      "Comprobar calidad de señal, no solo tensión DC.",
      "Lógica 0: VHL ≥2,0 V; lógica 1: VBN ≤1,3 V; bit 104 µs ±1 % y sin ruido menor de 52 µs.",
      [section("wave", "Criterios", "VHL ≥2,0 V; VBN ≤1,3 V; 104 µs ±1 % por bit; sin pulsos de ruido <52 µs.", True),
       section("cable", "Cable", "CVVS/CPEVS 1,25 mm² o más; máximo 200 m; pantalla a tierra en un único punto."),
       section("power", "Alimentación", "La documentación muestra 30 V en CNS1/CNS2 de la familia.")],
      [step("prepare", 1, "Use osciloscopio aislado y procedimiento seguro."),
       step("procedure", 1, "Mida tensión DC y después forma de onda."),
       step("procedure", 2, "Busque reflexiones, ruido y múltiples puntos de tierra."),
       step("procedure", 3, "Aísle ramales y repetidores."),
       step("verify", 1, "Confirme niveles y ausencia de errores después de corregir.")],
      "CITY", "131", "M-NET waveform and noise", page_end="132")

    v(14, "Alcance de parada: interior frente a BC/exterior",
      "CITY MULTI con unidades interiores, BC Controller y exterior.",
      "CITY MULTI R2 / VRF", "system",
      "Saber si una avería debe parar una sola unidad o todo el sistema.",
      "La documentación de la generación indica: fallo interior, solo la interior afectada; fallo BC o exterior, todas las interiores, BC y exterior.",
      [section("indoor", "Fallo interior", "Se detiene únicamente la unidad interior relacionada.", True),
       section("bc_outdoor", "Fallo BC o exterior", "Se detienen todas las interiores, BC Controller y exterior."),
       section("warning", "Familia concreta", "No extrapolar este alcance a cualquier CITY MULTI sin comprobar la arquitectura.")],
      [step("procedure", 1, "Anote dirección y atributo del origen del error."),
       step("procedure", 2, "Distinga Indoor, BC y Outdoor."),
       step("verify", 1, "Compare qué unidades siguen funcionando con el alcance documentado.")],
      "CITYLEG", "94", "System stop range by error source")

    v(14, "Estados normales del display exterior",
      "Exterior CITY MULTI con display de dos caracteres.",
      "CITY MULTI", "outdoor",
      "No confundir estados de control con códigos de avería.",
      "El display puede mostrar funcionamiento, espera, desescarche o recuperación sin que exista un fallo.",
      [section("states", "Estados", "Revise la tabla de estados normales antes de abrir una ficha de error.", True),
       section("context", "Contexto", "Modo, temperatura y etapa de puesta en marcha determinan el estado.")],
      [step("procedure", 1, "Anote exactamente los caracteres y si están fijos o parpadean."),
       step("procedure", 2, "Compare con la tabla Normal operation display."),
       step("verify", 1, "Solo trate como avería los códigos incluidos en la tabla de error correspondiente.")],
      "CITY", "86", "Normal operation display")

    # Tools and components.
    v(15, "A-Control Service Tool PAC-SK52ST",
      "Placa exterior Mr. Slim con conector CNM y herramienta de display de dos dígitos.",
      "Mr. Slim", "outdoor",
      "Leer monitor de operación y códigos desde la exterior.",
      "La herramienta se conecta a CNM y ofrece display de dos dígitos; no es un conector genérico.",
      [section("connector", "Conexión", "CNM en las placas compatibles.", True),
       section("use", "Uso", "Código, historial/estado y monitor de operación según la familia."),
       section("warning", "Compatibilidad", "No conectar a otro conector parecido; confirmar referencia de placa.")],
      [step("prepare", 1, "Identifique CNM y compatibilidad con PAC-SK52ST."),
       step("procedure", 1, "Conecte con la alimentación en el estado indicado por el manual."),
       step("procedure", 2, "Seleccione el número de monitor/código."),
       step("verify", 1, "Compare lectura con medidas reales antes de condenar un sensor.")],
      "PUZZM", "67", "A-Control Service Tool and check table")

    v(15, "PUMY — monitor de operación y subcódigo completo",
      "Exterior PUMY con display/switches de servicio.",
      "CITY MULTI compacto", "outdoor",
      "Pasar del alias corto al subcódigo técnico de cuatro dígitos.",
      "El alias U2, U4, EF, etc. no basta; el subcódigo identifica la sonda o condición concreta.",
      [section("examples", "Ejemplos", "U2 puede ser 1102 o 1501; U4 puede ser 5102, 5105, 5106, 5109 o 5110.", True),
       section("address", "Dirección/atributo", "En 6607/6608, revise origen, destino y atributo antes de sustituir la unidad indicada.")],
      [step("procedure", 1, "Lea alias corto y subcódigo de cuatro dígitos."),
       step("procedure", 2, "Anote dirección y atributo."),
       step("procedure", 3, "Abra la ficha del subcódigo completo."),
       step("verify", 1, "Contraste monitor con mediciones físicas.")],
      "PUMY", "43", "Check code and detailed code table")

    v(16, "Cassette — NTC 15 kΩ y tolerancia",
      "Sondas TH1, TH2 y TH5 de la familia PLA-M documentada.",
      "Mr. Slim cassette", "indoor",
      "Comprobar una sonda con temperatura real conocida.",
      "R0=15 kΩ ±3 % y B=3480 ±2 %; puntos: 0 °C 15 kΩ, 10 °C 9,6 kΩ, 20 °C 6,3 kΩ, 25 °C 5,4 kΩ, 30 °C 4,3 kΩ, 40 °C 3,0 kΩ.",
      [section("curve", "Puntos", "0:15; 10:9,6; 20:6,3; 25:5,4; 30:4,3; 40:3,0 kΩ.", True),
       section("method", "Método", "Desconecte la sonda, mida temperatura en el propio cuerpo y espere estabilidad.")],
      [step("prepare", 1, "Corte alimentación y desconecte la sonda."),
       step("procedure", 1, "Mida temperatura y resistencia."),
       step("procedure", 2, "Compare con curva y tolerancia."),
       step("verify", 1, "Mueva el cable y caliente/enfríe para detectar cortes intermitentes.")],
      "PLAM", "33", "Thermistor characteristics")

    v(16, "Boya de cassette — continuidad arriba/abajo",
      "Boya magnética conectada a CN4F.",
      "Mr. Slim cassette", "indoor",
      "Distinguir atasco mecánico, contacto y cableado.",
      "En la familia PLA-M: parte móvil arriba = corto; abajo = abierto.",
      [section("states", "Estados", "UP: corto. DOWN: abierto.", True),
       section("mechanical", "Mecánica", "La continuidad puede ser correcta en banco y la boya quedarse trabada dentro de la bandeja.")],
      [step("prepare", 1, "Desconecte CN4F con alimentación cortada."),
       step("procedure", 1, "Mueva la boya lentamente y mida continuidad."),
       step("procedure", 2, "Compruebe suciedad, imán y libertad mecánica."),
       step("verify", 1, "Monte y pruebe con agua real.")],
      "PLAM", "32", "Drain float switch")

    v(17, "Ventilador exterior PUMY — alimentación y señal",
      "Motor de ventilador DC de exterior PUMY.",
      "CITY MULTI compacto", "outdoor",
      "Separar motor, cableado y PCB.",
      "Valores de la familia: 310–350 VDC, 15 VDC y señal de control 0–6,5 V.",
      [section("values", "Valores", "Bus motor 310–350 VDC; control 15 VDC; señal 0–6,5 V.", True),
       section("safety", "Seguridad", "Alta tensión continua; medir solo con instrumental y procedimiento adecuados.")],
      [step("prepare", 1, "Corte alimentación y compruebe giro libre."),
       step("procedure", 1, "Revise conector y cableado."),
       step("procedure", 2, "Con condiciones seguras, mida las tres referencias."),
       step("verify", 1, "Compare orden de marcha, señal y rotación.")],
      "PUMY", "66", "Outdoor fan motor check")

    v(17, "Sensores de presión 63HS/63LS",
      "PUMY con monitor de presión y sensores de alta/baja.",
      "CITY MULTI compacto", "outdoor",
      "Comparar lectura electrónica con presión real.",
      "5201 identifica alta y 5202 baja; una lectura fuera de rango puede ser presión real, alimentación, sensor o PCB.",
      [section("high", "Alta", "5201 / F5 — sensor 63HS.", True),
       section("low", "Baja", "5202 / F3 — sensor 63LS."),
       section("method", "Contraste", "No condene el sensor sin comparar manómetro y monitor.")],
      [step("prepare", 1, "Conecte manómetros adecuados al refrigerante."),
       step("procedure", 1, "Lea presión en monitor de operación."),
       step("procedure", 2, "Compare con presión real y revise alimentación/señal."),
       step("verify", 1, "Repita a otra presión para comprobar linealidad.")],
      "PUMY", "73", "High and low pressure sensor checks", page_end="74")

    v(18, "Cassette PLA-M — puntos de prueba",
      "Placa interior de cassette PLA-M.",
      "Mr. Slim cassette", "indoor",
      "Localizar tensiones útiles sin confundir conectores.",
      "CN4F boya; CNP bomba 13 VDC; CN3C comunicación 0–24 VDC; TB5 mando 10,4–14,6 VDC; CNMF 310–340 VDC y 15 VDC.",
      [section("values", "Referencias", "CNP 13 VDC; CN3C 0–24 VDC; TB5 10,4–14,6 VDC; CN01 220–240 VAC; CNMF 310–340 VDC +15 VDC; CN51 pulso 13 V.", True),
       section("warning", "No universal", "Son puntos de la familia OCH697; confirme placa y conector.")],
      [step("prepare", 1, "Identifique serigrafía y esquema."),
       step("procedure", 1, "Mida primero alimentaciones de baja tensión."),
       step("procedure", 2, "Use categoría e aislamiento adecuados para red y bus motor."),
       step("verify", 1, "Relacione cada tensión con la orden de funcionamiento.")],
      "PLAM", "34", "Indoor controller board test points")

    v(18, "A-Control S1/S2/S3 y mando TB5",
      "Mr. Slim con alimentación y comunicación por S1/S2/S3.",
      "Mr. Slim", "system",
      "Comprobar alimentación y bus ante E6/E7/E9.",
      "S1–S2: 220–240 VAC en la familia; TB5 del mando: 10,4–14,6 VDC en la cassette documentada.",
      [section("power", "S1–S2", "220–240 VAC.", True),
       section("controller", "TB5", "10,4–14,6 VDC en PLA-M; controller check PAR-41 indica 8,5–12 VDC en el propio mando."),
       section("warning", "Diferentes puntos", "No confundir tensión en bornes interiores con la medida dentro del mando.")],
      [step("prepare", 1, "Identifique esquema y categoría de medida."),
       step("procedure", 1, "Compruebe S1–S2."),
       step("procedure", 2, "Compruebe orden y continuidad de S1/S2/S3."),
       step("procedure", 3, "Mida TB5 o el propio mando según el diagnóstico."),
       step("verify", 1, "Aísle cable y placas antes de sustituir.")],
      "PLARP", "28", "Indoor/outdoor connecting wire check")

    # Normal states.
    v(19, "PLEASE WAIT durante unos 2 minutos",
      "Mando cableado alimentado después de cortar corriente.",
      "Mr. Slim", "controller",
      "Distinguir inicialización normal de un error de comunicación.",
      "PLEASE WAIT durante aproximadamente 2 min es normal; después, un código apunta a fase/cableado. Sin mensaje, revisar S1/S2/S3 o corto del mando.",
      [section("normal", "Normal", "PLEASE WAIT hasta unos 2 minutos después de alimentar.", True),
       section("after", "Si no termina", "Código posterior: revisar alimentación/fases/cableado. Pantalla sin mensaje: revisar S1/S2/S3 y mando."),
       section("function", "Tras Function Selection", "Hasta unos 30 s sin aceptar órdenes puede ser normal.")],
      [step("procedure", 1, "Cronometre desde la alimentación."),
       step("procedure", 2, "No intervenga durante los primeros 2 min salvo olor, ruido o riesgo."),
       step("verify", 1, "Si persiste, anote el mensaje exacto y mida alimentación/comunicación.")],
      "PLAM", "23", "Remote controller startup indications")

    v(19, "Precalentamiento exterior de 12 horas",
      "PUMY recién alimentada antes de Test Run.",
      "CITY MULTI compacto", "outdoor",
      "Evitar diagnósticos falsos y daño por arrancar sin precalentamiento.",
      "La exterior debe permanecer alimentada al menos 12 h antes de la prueba.",
      [section("reason", "Motivo", "Precalentamiento del compresor y estabilización del sistema.", True),
       section("not_fault", "No es avería", "La espera forma parte de la puesta en marcha.")],
      [step("prepare", 1, "Alimente la exterior con válvulas y cableado ya comprobados."),
       step("procedure", 1, "Espere al menos 12 h."),
       step("verify", 1, "Después ejecute Test Run y registre temperaturas/presiones.")],
      "PUMY", "41", "Crankcase heater energization")

    v(19, "CITY MULTI — espera de hasta 30 minutos en frío exterior",
      "Sistema grande arrancado dentro de las 2 h posteriores a la alimentación y con baja temperatura exterior.",
      "CITY MULTI VRF", "system",
      "No confundir una espera controlada con fallo de arranque.",
      "La lógica puede mantener espera hasta 30 min en esas condiciones.",
      [section("conditions", "Condiciones", "Arranque dentro de las 2 h de alimentar + temperatura exterior baja.", True),
       section("limit", "Tiempo", "Hasta 30 min en la familia documentada.")],
      [step("procedure", 1, "Anote hora de alimentación y temperatura exterior."),
       step("procedure", 2, "Observe display y no reinicie repetidamente."),
       step("verify", 1, "Si supera el tiempo, consulte estado/código y alimentación.")],
      "CITY", "74", "Initial startup waiting control")

    # Recognition and rules.
    v(20, "M-Series / MXZ",
      "Split mural o multisplit con mando inalámbrico y exterior MUZ/MXZ.",
      "M-Series", "general",
      "Elegir recall, LED y switches correctos.",
      "M-Series usa failure mode recall y patrones POWER; MXZ añade bancos SW y corrección de tuberías.",
      [section("indoor", "Interior", "Mando inalámbrico y EMERGENCY OPERATION.", True),
       section("outdoor", "Exterior", "MUZ de una conexión o MXZ con varias válvulas/puertos.")],
      [step("procedure", 1, "Cuente puertos frigoríficos y identifique serigrafía MUZ/MXZ."),
       step("procedure", 2, "Use recall solo si el mando y la unidad coinciden con la variante.")],
      "MXZ", "2", "Model lineup and construction")

    v(20, "Mr. Slim A-Control",
      "S1/S2/S3, mando MA en TB5 y códigos P/E/U de dos caracteres.",
      "Mr. Slim", "general",
      "Elegir diagnóstico A-Control, cassette y PAR.",
      "Las unidades comerciales PLA/PUZ usan códigos cortos y buses distintos de CITY MULTI.",
      [section("terminals", "Bornes", "S1/S2/S3 entre interior/exterior; TB5 para mando.", True),
       section("codes", "Códigos", "P1–P9, PA/PB/PL, E0–E9, U/F.")],
      [step("procedure", 1, "Confirme bornes S1/S2/S3 y TB5."),
       step("procedure", 2, "Identifique cassette/conductos y mando."),
       step("procedure", 3, "Busque el código corto y cualquier detalle disponible.")],
      "PUZZM", "6", "System configuration")

    v(20, "CITY MULTI / PUMY",
      "Red M-NET, direcciones, display de cuatro dígitos y posible BC Controller.",
      "CITY MULTI", "general",
      "Elegir subcódigo, alcance de red y puesta en marcha VRF.",
      "Los alias U2/U4/EF deben completarse con 1102/1501/510x/710x.",
      [section("network", "Red", "M-NET con direcciones y atributos.", True),
       section("codes", "Códigos", "Subcódigos de cuatro dígitos y alias corto."),
       section("architecture", "Elementos", "Exterior modular, múltiples interiores y posible BC Controller.")],
      [step("procedure", 1, "Identifique M-NET y tipo de exterior."),
       step("procedure", 2, "Lea código completo, dirección y atributo."),
       step("procedure", 3, "Determine si el origen es Indoor, BC o Outdoor.")],
      "PUMY", "10", "System construction")

    v(21, "Un mismo código no significa lo mismo en todas las familias",
      "La búsqueda muestra varias interpretaciones para E/U/P y alias CITY MULTI.",
      "todas las familias", "general",
      "Evitar aplicar una comprobación correcta a la máquina equivocada.",
      "Primero arquitectura, después forma de indicación, código completo, unidad de origen y comportamiento.",
      [section("order", "Orden", "1) familia; 2) mando/placa; 3) código y subcódigo; 4) dirección/atributo; 5) efecto.", True),
       section("example", "Ejemplo U2", "En Mr. Slim agrupa descarga/carga; en CITY MULTI puede concretarse como 1102 o 1501."),
       section("flash", "Patrones POWER", "El mismo número cambia entre recall interior y exterior.")],
      [step("procedure", 1, "Abra Cómo reconocer la familia."),
       step("procedure", 2, "Anote todos los dígitos y parpadeos."),
       step("procedure", 3, "Compare solo variantes compatibles."),
       step("procedure", 4, "Use causas y medidas de esa variante.")],
      "PUMY", "43", "Check code and detailed code table")

    v(22, "MXZ — verificar historial de corrección después de cambiar PCB",
      "Exterior MXZ con SW871 o SW2-3 y placa sustituida.",
      "M-Series multisplit", "outdoor",
      "Evitar que una placa nueva pierda la correspondencia de tuberías.",
      "Los registros previos se borran al sustituir la PCB; el manual exige confirmar la corrección automática.",
      [section("record", "Placa nueva", "El historial anterior no está disponible.", True),
       section("verify", "Comprobación", "Ejecute o consulte la corrección correspondiente a 2 puertos o 3–6 puertos.")],
      [step("prepare", 1, "Copie switches y conectores con alimentación cortada."),
       step("procedure", 1, "Identifique el tipo de corrección de la placa nueva."),
       step("procedure", 2, "Ejecute la detección o consulte el registro."),
       step("verify", 1, "Pruebe cada interior y confirme que tubo y cable coinciden.")],
      "MXZ", "177", "Confirmation after replacing outdoor controller board")

    v(22, "Cassette — copiar capacidad, DIP y puentes",
      "PCB interior de recambio para PLA-M.",
      "Mr. Slim cassette", "indoor",
      "Evitar errores de capacidad, mando u opciones después del cambio.",
      "El repuesto debe recuperar los ajustes de capacidad, DIP, J41/J42 y conexiones opcionales documentadas.",
      [section("before", "Antes", "Fotografíe placa, conectores, DIP, puentes y etiqueta de capacidad.", True),
       section("after", "Después", "Compruebe mando, ventilador, bomba, lamas, sensores y Test Run.")],
      [step("prepare", 1, "Corte alimentación y espere descarga."),
       step("procedure", 1, "Transfiera solo los ajustes documentados."),
       step("procedure", 2, "Revise todos los conectores y tierra."),
       step("verify", 1, "Alimente; compruebe código de capacidad y ejecute Test Run.")],
      "PLAM", "35", "Indoor controller board replacement settings")

    return [topics[key] for key in sorted(topics)]


def build_search(
    topics: list[dict[str, Any]],
    error_indexes: list[dict[str, Any]],
    error_details: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    def synonyms(value: str) -> str:
        normalized = normalize(value)
        additions: list[str] = []
        if "BOYA" in normalized:
            additions.append("flotador float switch desbordamiento")
        if "RECOGIDA" in normalized:
            additions.append("pump down")
        if "MANDO" in normalized:
            additions.append("remote controller control remoto")
        if "M NET" in normalized:
            additions.append("bus datos transmision")
        if "CORRECCION AUTOMATICA" in normalized:
            additions.append("wiring piping correction SW871")
        return " ".join([value] + additions)

    for topic in topics:
        category = topic["category"]
        for item in topic["variants"]:
            parameter_text = " ".join(
                " ".join([
                    str(row.get("parameter_code") or ""),
                    str(row.get("name") or ""),
                    str(row.get("description") or ""),
                    " ".join(
                        " ".join([
                            str(opt.get("option_value") or ""),
                            str(opt.get("option_label") or ""),
                            str(opt.get("effect") or ""),
                        ])
                        for opt in row.get("options", [])
                    ),
                ])
                for row in item.get("parameters", [])
            )
            controller_text = " ".join(str(value or "") for value in (item.get("controller") or {}).values())
            body = " ".join([
                item["title"], item.get("recognition") or "", item.get("purpose") or "",
                item.get("summary") or "",
                " ".join(row.get("body") or "" for row in item.get("sections", [])),
                " ".join(
                    " ".join([row.get("instruction") or "", row.get("expected_result") or ""])
                    for row in item.get("steps", [])
                ),
                parameter_text, controller_text, category["name"], topic["title"],
            ])
            entries.append({
                "type": "variant",
                "id": item["id"],
                "topic_id": topic["id"],
                "category_slug": category["slug"],
                "category": category["name"],
                "title": item["title"],
                "summary": item["summary"],
                "haystack": normalize(synonyms(body)),
            })

    details_by_id = {item["id"]: item for item in error_details}
    for index in error_indexes:
        detail = details_by_id[index["id"]]
        body = " ".join(
            [index["search_text"]]
            + [
                " ".join(
                    [row["title"], row["description"]]
                    + [info["body"] for info in row["info_items"]]
                    + [
                        " ".join([
                            dataset["name"],
                            dataset.get("notes") or "",
                            " ".join(
                                f"{point.get('variable_value')} {point.get('value_nominal')}"
                                for point in dataset.get("points", [])
                            ),
                        ])
                        for dataset in row.get("datasets", [])
                    ]
                )
                for row in detail["interpretations"]
            ]
        )
        entries.append({
            "type": "error",
            "id": index["id"],
            "topic_id": None,
            "category_slug": "errors",
            "category": CATEGORY_BY_SLUG["errors"]["name"],
            "title": f"{index['code_display']} — {index['short_label']}",
            "summary": detail["interpretations"][0]["description"],
            "haystack": normalize(synonyms(body)),
        })
    return entries


def main() -> int:
    expected_root = (ROOT / "data" / "brands" / "mitsubishi-electric").resolve()
    if BRAND_DIR.resolve() != expected_root:
        raise RuntimeError(f"Destino inesperado: {BRAND_DIR}")

    error_indexes, error_details = build_errors()
    topics = build_topics()
    search_entries = build_search(topics, error_indexes, error_details)
    now = datetime.now(timezone.utc).isoformat()

    if WEB_DIR.exists():
        shutil.rmtree(WEB_DIR)
    WEB_DIR.mkdir(parents=True, exist_ok=True)

    topics_by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    variant_map: dict[str, int] = {}
    for topic in topics:
        category_slug = topic["category"]["slug"]
        topics_by_category[category_slug].append({
            "id": topic["id"],
            "slug": topic["slug"],
            "title": topic["title"],
            "summary": topic["summary"],
            "active": 1,
            "variant_count": len(topic["variants"]),
        })
        for item in topic["variants"]:
            variant_map[str(item["id"])] = topic["id"]
        write_json(WEB_DIR / "topics" / f"{topic['id']}.json", topic)

    navigation_categories = []
    for sort_order, (category_id, slug, name, description) in enumerate(CATEGORIES, start=1):
        navigation_categories.append({
            "id": category_id,
            "slug": slug,
            "name": name,
            "description": description,
            "sort_order": sort_order * 10,
            "active": 1,
            "topics": topics_by_category.get(slug, []),
        })

    for detail in error_details:
        write_json(WEB_DIR / "errors" / "details" / f"{detail['id']}.json", detail)
    write_json(WEB_DIR / "errors" / "index.json", error_indexes)
    write_json(WEB_DIR / "search.json", search_entries)
    write_json(WEB_DIR / "variant_map.json", variant_map)

    source_rows = [
        {
            "id": source_id,
            "title": row["title"],
            "document_ref": row["document_ref"],
            "publication_date": row["publication_date"],
            "language": row["language"],
            "document_type": row["document_type"],
            "source_url": row["source_url"],
            "status": "reviewed",
            "notes": row["notes"],
        }
        for source_id, row in enumerate(SOURCES.values(), start=1)
    ]
    write_json(WEB_DIR / "sources.json", source_rows)

    coverage_notes = {
        "errors": "A-Control, M-Series, Mr. Slim y CITY MULTI con códigos cortos, subcódigos y patrones LED.",
        "diagnostic_access": "Autocheck inalámbrico, PAR-41, PAR-21, PAC-YT52 y recall residencial.",
        "history_reset": "Historial de 16/32 registros, self-check, borrado y memoria M-Series.",
        "service_modes": "Emergencia mural/cassette/VRF y recogida de refrigerante por variantes.",
        "configuration": "Function Settings, DIP, puentes y switches MXZ/PLA.",
        "controllers_buses": "PAR-41/PAR-21/PAC-YT52, TB5/TB15, Main/Sub y controller check.",
        "drainage_overflow": "P4/P5/PA, bomba 13 VDC, señal de giro y boya.",
        "commissioning": "Test Run moderno, PUMY y CITY MULTI de generación anterior.",
        "multisplit": "Corrección automática de 2 puertos y SW871, Low Noise y tubería.",
        "city_multi_network": "M-NET, direcciones, tensión, forma de onda, alcance y emergencia.",
        "component_checks": "NTC, bomba, boya, ventiladores y sensores de presión.",
        "technical_values": "Puntos de prueba PLA, A-Control y M-NET.",
        "normal_states": "PLEASE WAIT, 30 s, precalentamiento 12 h y espera VRF de 30 min.",
        "service_tools_boards": "PAC-SK52ST, monitor, subcódigos y trabajo tras PCB.",
        "system_architecture": "Pistas para M-Series, Mr. Slim y CITY MULTI.",
    }
    coverage = [
        {
            "id": category_id,
            "brand_id": BRAND_ID,
            "area_slug": slug,
            "area_name": name,
            "equipment_scope": "Mitsubishi Electric — corpus Referencia V1",
            "coverage_status": "reference_v1",
            "source_count": len(SOURCES),
            "notes": coverage_notes[slug],
            "last_reviewed": now[:10],
        }
        for category_id, slug, name, _ in CATEGORIES
    ]
    write_json(WEB_DIR / "coverage.json", coverage)

    counts = {
        "categories": len(navigation_categories),
        "topics": len(topics),
        "variants": len(variant_map),
        "errors": len(error_indexes),
        "search_entries": len(search_entries),
    }
    navigation = {
        "metadata": {
            "schema_name": "Super Tecnico",
            "navigation_model": "brand_category_topic_variant",
            "schema_version": "2.2.0",
            "data_version": "1.0.0",
            "last_update_utc": now,
            "reference_brand": "Mitsubishi Electric",
            "verification_warning": (
                "Completa respecto al corpus Mitsubishi Electric Referencia V1. "
                "Confirme siempre familia, mando, forma de indicación y subcódigo."
            ),
        },
        "categories": navigation_categories,
    }
    write_json(WEB_DIR / "navigation.json", navigation)

    brand = {
        "slug": "mitsubishi-electric",
        "name": "Mitsubishi Electric",
        "display_name": "Mitsubishi Electric",
        "enabled": True,
        "web_data": "web",
        "media": "media",
        "publish_media": False,
        "static_site": True,
        "schema_version": "2.2.0",
        "data_version": "1.0.0",
        "exported_at_utc": now,
        "counts": counts,
        "notes": (
            "Mitsubishi Electric Referencia V1: M-Series, MXZ, Mr. Slim, cassette, "
            "PUMY, CITY MULTI, PAR-41/PAR-21 y red M-NET. Sin PDFs ni capturas."
        ),
    }
    write_json(BRAND_DIR / "brand.json", brand)

    from audit_brand_quality import audit_brand

    quality = audit_brand(BRAND_DIR)
    write_json(WEB_DIR / "quality.json", quality)
    print(json.dumps({
        "brand": brand["slug"],
        "counts": counts,
        "interpretations": quality["errors"]["interpretations"],
        "error_quality": quality["errors"]["status_counts"],
        "variant_quality": quality["technical_variants"]["status_counts"],
        "sources": len(SOURCES),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
