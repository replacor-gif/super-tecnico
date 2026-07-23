#!/usr/bin/env python3
"""Construye la proyección pública Daikin Referencia V2.

La fuente maestra sigue siendo documental y privada. Este generador publica
únicamente resúmenes técnicos estructurados, referencias y páginas verificadas.
No copia PDFs, capturas, bases SQLite ni identificadores privados de Drive.
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
BRAND_DIR = ROOT / "data" / "brands" / "daikin"
WEB_DIR = BRAND_DIR / "web"


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


SOURCES: dict[str, dict[str, Any]] = {
    "RZQS": {
        "title": "Manual de servicio — Daikin Sky Air RZQS71~125B7V3B",
        "document_ref": "ESiES06-07",
        "publication_date": "2006",
        "language": "es",
        "document_type": "service_manual",
        "source_url": None,
        "notes": "Manual de servicio Sky Air R-410A; referencia documental privada, no se publica el PDF.",
    },
    "FCQ": {
        "title": "Manual de servicio — Daikin Sky Air interiores FCQ/FFQ",
        "document_ref": "ESiEN05-04",
        "publication_date": "2005",
        "language": "en",
        "document_type": "service_manual",
        "source_url": None,
        "notes": "Manual de servicio de interiores y cassette; referencia documental privada, no se publica el PDF.",
    },
    "MXL": {
        "title": "Manual de servicio — Daikin Multi-Split 2MXL/3MXL-Q",
        "document_ref": "SiUS121602E",
        "publication_date": "2016",
        "language": "en",
        "document_type": "service_manual",
        "source_url": None,
        "notes": "Manual de servicio multisplit; referencia documental privada, no se publica el PDF.",
    },
    "VRV4": {
        "title": "Guía de referencia — Daikin VRV IV, tabla de errores y subcódigos",
        "document_ref": "4P370475-1",
        "publication_date": "2014",
        "language": "es",
        "document_type": "installer_reference",
        "source_url": None,
        "notes": "Extracto oficial de tabla de códigos; referencia documental privada, no se publica el PDF.",
    },
    "CTXA": {
        "title": "Manual de operación — Daikin CTXA/FTXA",
        "document_ref": "CTXA_FTXA_OM",
        "publication_date": None,
        "language": "en",
        "document_type": "operation_manual",
        "source_url": None,
        "notes": "Referencia residencial R32; no se publica el PDF.",
    },
    "WIRING": {
        "title": "Esquema de cableado — Daikin Sky Air moderno",
        "document_ref": "4D109863A",
        "publication_date": None,
        "language": "es",
        "document_type": "wiring_diagram",
        "source_url": None,
        "notes": "Esquema técnico de una familia concreta; no se publica la imagen.",
    },
    "BRC1E": {
        "title": "Manual de instalación — Daikin BRC1E52A7",
        "document_ref": "4PW71264-1",
        "publication_date": "2011-10",
        "language": "en",
        "document_type": "installation_manual",
        "source_url": (
            "https://www.daikin.eu/content/dam/document-library/installation-manuals/ctrl/"
            "BRC1E52A7_4PW71264-1_Installation%20manuals_English.pdf"
        ),
        "notes": "Mando cableado con menú de servicio, historial y prueba.",
    },
    "MADOKA": {
        "title": "Guía de instalador y usuario — Daikin Madoka BRC1H52",
        "document_ref": "4P596266-1B",
        "publication_date": "2022-02",
        "language": "en",
        "document_type": "installer_reference",
        "source_url": (
            "https://www.daikin.eu/content/dam/document-library/Installer-reference-guide/ctrl/"
            "individual-control-systems/BRC1H52K_S_W_Installer%20and%20user%20reference%20guide_"
            "4PEN596266-1B_English.pdf"
        ),
        "notes": "Mando Madoka de dos hilos y aplicación Madoka Assistant.",
    },
    "RZAG": {
        "title": "Guía de referencia del instalador — Daikin Sky Air RZAG-M",
        "document_ref": "4P486046-1C",
        "publication_date": "2019-04",
        "language": "es",
        "document_type": "installer_reference",
        "source_url": (
            "https://www.daikin.eu/content/dam/document-library/Installer-reference-guide/ac/"
            "sky-air/RZAG-MV1%2C%20RZAG-MY1_4PES486046-1C_2019_04_"
            "Installer%20reference%20guide_Spanish.pdf"
        ),
        "notes": "Sky Air Alpha de potencia comercial; prueba y bombeo de vacío.",
    },
}


def source(ref: str, page: str, section: str, page_end: str | None = None) -> dict[str, Any]:
    base = SOURCES[ref]
    return {
        "title": base["title"],
        "document_ref": base["document_ref"],
        "source_url": base["source_url"],
        "page_start": page,
        "page_end": page_end or page,
        "section": section,
    }


CATEGORIES = [
    (1, "errors", "Errores y protecciones", "Códigos, subcódigos, causas y comprobaciones separadas por familia."),
    (2, "diagnostic_access", "Obtención de códigos y subcódigos", "Métodos para extraer errores desde mandos, display y placas."),
    (3, "history_reset", "Historial y borrado", "Consulta, interpretación y borrado de memorias de avería."),
    (4, "service_modes", "Modos de servicio", "Prueba, marcha forzada, pump down y comprobaciones de puesta en marcha."),
    (5, "configuration", "Configuración y programación", "Ajustes de campo desde mandos y placas."),
    (6, "controllers_buses", "Mandos y buses", "Cableado, arranque, principal/secundario y fallos de comunicación."),
    (7, "drainage_overflow", "Drenaje y desbordamiento", "Secuencias de bomba, boya y recuperación del sistema."),
    (8, "commissioning", "Puesta en marcha", "Pruebas previas, test y reconocimiento de instalaciones."),
    (9, "vrf_network", "VRV y redes", "Subcódigos, cableado de transmisión y alcance de las incidencias."),
    (10, "component_checks", "Comprobación de componentes", "Sondas, presiones, ventiladores, inverter y actuadores."),
    (11, "technical_values", "Valores técnicos", "Curvas y valores de referencia documentados."),
    (12, "normal_states", "Comportamientos normales", "Estados que pueden parecer avería y condiciones de protección."),
    (13, "system_architecture", "Arquitectura de sistemas", "Pistas para distinguir Sky Air, multisplit, cassette y VRV."),
]

CATEGORY_BY_SLUG = {
    slug: {"id": ident, "slug": slug, "name": name, "description": description}
    for ident, slug, name, description in CATEGORIES
}


def split_items(text: str) -> list[str]:
    return [item.strip() for item in text.split("|") if item.strip()]


RZQS_ERROR_SPECS = [
    ("A1", "Fallo de la PCB interior", "indoor", "3-42",
     "La unidad interior detecta una anomalía de su placa electrónica.",
     "PCB interior defectuosa|Memoria o circuito de alimentación de la placa anómalo",
     "Cortar y restablecer alimentación; si reaparece, revisar alimentación y PCB interior|Comprobar conectores antes de sustituir la placa",
     "La unidad interior detiene el funcionamiento y comunica A1 al mando."),
    ("A3", "Nivel de agua de drenaje anormal", "indoor", "3-43",
     "La boya indica nivel alto o el sistema de drenaje no evacua correctamente.",
     "Bomba de drenaje defectuosa|Tubería obstruida o mal instalada|Boya o conector X15A defectuoso|PCB interior defectuosa",
     "Comprobar nivel real, pendiente y obstrucciones|Verificar bomba, boya y conexión X15A|Comprobar la salida de bomba indicada por el manual",
     "La placa fuerza la parada del termostato para proteger la bandeja y mantiene la gestión de drenaje."),
    ("AF", "Anomalía del sistema de drenaje con compresor parado", "indoor", "3-45",
     "La boya cambia a condición de nivel alto cuando el compresor está parado.",
     "Retorno de agua o sifón incorrecto|Tubería de drenaje obstruida|Boya bloqueada|PCB interior defectuosa",
     "Comprobar si el agua retorna al detener la bomba|Revisar altura y longitud del desagüe|Comprobar boya y bomba",
     "El sistema memoriza una condición de drenaje anormal aunque no exista demanda de compresor."),
    ("A6", "Ventilador interior bloqueado o con sobrecorriente", "indoor", "3-47",
     "No se detecta la rotación esperada del ventilador interior.",
     "Motor bloqueado|Cableado o conector defectuoso|PCB interior o circuito de mando defectuoso",
     "Comprobar giro libre con alimentación desconectada|Revisar conectores y tensión de mando según el esquema|Comprobar motor y PCB",
     "La unidad interior detiene el ventilador y la operación protegida."),
    ("A7", "Motor de aleta oscilante bloqueado", "indoor", "3-49",
     "La placa no obtiene el movimiento esperado de la aleta.",
     "Aleta atascada|Motor swing o cableado defectuoso|PCB interior defectuosa",
     "Comprobar movimiento mecánico sin forzar engranajes|Revisar conector y motor de aleta|Reiniciar y observar la inicialización",
     "La placa limita o detiene el movimiento de la aleta y registra A7."),
    ("AJ", "Ajuste de capacidad interior incorrecto", "indoor", "3-51",
     "La memoria no contiene un código de capacidad válido o falta el adaptador correspondiente.",
     "Adaptador de capacidad ausente o incorrecto|PCB de sustitución sin capacidad programada|Conexión X23A defectuosa",
     "Comprobar el adaptador de capacidad y X23A|Confirmar que corresponde a la capacidad de la unidad|Reiniciar tras corregir",
     "La unidad bloquea la puesta en marcha al no poder identificar su capacidad."),
    ("C4", "Sonda del intercambiador interior", "indoor", "3-53",
     "Sonda de batería interior abierta, en cortocircuito o fuera de rango.",
     "Sonda NTC defectuosa|Cable o conector abierto|Entrada de medida de la PCB defectuosa",
     "Medir resistencia con la sonda desconectada|Comparar con la curva oficial a la temperatura real|Revisar cableado y PCB",
     "La placa sustituye o limita el control basado en esa temperatura y registra C4."),
    ("C5", "Sonda de tubería de gas interior", "indoor", "3-53",
     "Sonda de tubería interior abierta, en cortocircuito o fuera de rango.",
     "Sonda NTC defectuosa|Cableado o conector defectuoso|PCB interior defectuosa",
     "Medir la resistencia y comparar con la curva|Revisar contacto térmico y conector|Comprobar la entrada de la PCB",
     "La unidad pierde una referencia de batería y protege el funcionamiento."),
    ("C9", "Sonda de aire de retorno interior", "indoor", "3-53",
     "La sonda de aire de aspiración no entrega un valor válido.",
     "Sonda NTC abierta o cortocircuitada|Conector o cable defectuoso|PCB interior defectuosa",
     "Comparar resistencia con temperatura ambiente|Revisar ubicación y flujo de aire|Comprobar continuidad hasta la PCB",
     "La regulación de temperatura ambiente queda afectada y la unidad registra C9."),
    ("CJ", "Sonda de ambiente del mando", "controller", "3-55",
     "El termistor incorporado en el mando cableado entrega un valor anormal.",
     "Termistor o PCB del mando defectuoso|Cableado del mando anómalo|Ajuste de sensor incompatible",
     "Comprobar si el control puede usar la sonda de retorno interior|Revisar cable y mando|Confirmar el ajuste de termostato",
     "La unidad puede continuar utilizando la sonda de aire interior, según la configuración documentada."),
    ("CC", "Sensor de humedad interior", "indoor", "3-56",
     "El sensor de humedad o su circuito entrega una señal anormal.",
     "Sensor de humedad defectuoso|Cableado o conector defectuoso|PCB interior defectuosa",
     "Revisar sensor y conector|Comprobar alimentación y señal según el esquema de la familia|Descartar PCB",
     "Las funciones dependientes de humedad quedan limitadas y se registra CC."),
    ("E1", "Fallo de la PCB exterior", "outdoor", "3-58",
     "La unidad exterior detecta una anomalía interna de control.",
     "PCB exterior defectuosa|Alimentación anómala|Conector o memoria de capacidad incorrectos",
     "Comprobar alimentación, fusibles y conectores|Restablecer alimentación y observar HAP|Verificar ajustes antes de sustituir PCB",
     "La unidad exterior detiene el compresor y comunica E1."),
    ("E3", "Protección de alta presión", "outdoor", "3-59",
     "El sistema activa la protección de alta presión.",
     "Válvula de cierre cerrada|Intercambiador o filtro sucio|Ventilación insuficiente|Sobrecarga de refrigerante|Presostato o cableado defectuoso",
     "Confirmar válvulas abiertas|Comprobar caudal de aire y limpieza|Medir presión con instrumental adecuado|Revisar presostato",
     "La protección detiene el compresor para evitar presión excesiva."),
    ("E4", "Protección o lectura anormal de baja presión", "outdoor", "3-61",
     "La presión de aspiración cae fuera del rango o la detección de baja presión es anormal.",
     "Falta de refrigerante|Válvula cerrada|Restricción en tubería o expansión|Sensor de baja presión o cableado defectuoso",
     "Confirmar válvulas abiertas|Buscar fugas y comprobar carga|Revisar restricciones y sensor de baja presión",
     "La protección detiene el compresor cuando la baja presión persiste."),
    ("E5", "Compresor bloqueado o cableado anormal", "outdoor", "3-65",
     "La etapa inverter detecta que el compresor no puede arrancar correctamente.",
     "Compresor bloqueado|Cableado U/V/W incorrecto o abierto|Módulo inverter o PCB defectuoso",
     "Cortar alimentación y revisar conexiones del compresor|Comprobar bobinados y aislamiento|Seguir la prueba del inverter del manual",
     "La unidad detiene el intento de arranque para proteger compresor e inverter."),
    ("E7", "Ventilador exterior bloqueado", "outdoor", "3-67",
     "No se detecta la velocidad esperada o aparece sobrecorriente instantánea del ventilador exterior.",
     "Motor bloqueado|Aspas obstruidas|Cableado o conector defectuoso|PCB exterior defectuosa",
     "Comprobar giro libre con alimentación desconectada|Revisar conectores|Verificar motor y salida de la PCB",
     "La unidad exterior detiene el funcionamiento protegido."),
    ("E9", "Válvula de expansión electrónica exterior", "outdoor", "3-69",
     "La placa detecta una anomalía de bobina, conexión o movimiento de la válvula electrónica.",
     "Bobina desconectada o abierta|Conector defectuoso|Cuerpo de válvula bloqueado|PCB exterior defectuosa",
     "Revisar conector y bobinas|Comprobar resistencia de devanados según la familia|Escuchar/inferir inicialización al alimentar",
     "La regulación de refrigerante queda fuera de control y la unidad se protege."),
    ("F3", "Temperatura de descarga excesiva", "outdoor", "3-71",
     "La sonda de descarga supera el límite de protección.",
     "Falta de refrigerante|Restricción o válvula cerrada|Sonda de descarga defectuosa|Compresor sobrecalentado",
     "Comprobar válvulas, carga y fugas|Comparar sonda con la curva de descarga|Revisar expansión y ventilación",
     "La placa reduce capacidad y puede detener el compresor si la temperatura sigue aumentando."),
    ("H3", "Sistema del presostato de alta", "outdoor", "3-73",
     "La entrada del presostato de alta no presenta el estado esperado.",
     "Presostato activado|Cableado o conector abierto|Presostato defectuoso|Presión realmente alta",
     "Medir presión antes de puentear o sustituir componentes|Comprobar continuidad con alimentación desconectada|Revisar circuito frigorífico",
     "La unidad impide el funcionamiento del compresor mientras la cadena de alta no sea segura."),
    ("H4", "Sistema de baja presión", "outdoor", "3-74",
     "La detección de baja presión no corresponde con el estado esperado.",
     "Falta de refrigerante|Sensor o presostato de baja defectuoso|Cableado abierto|Válvula cerrada",
     "Comprobar presión real y válvulas|Revisar cableado y sensor|Buscar fugas si la presión es realmente baja",
     "La unidad protege el compresor ante una condición de aspiración insegura."),
    ("H9", "Sonda de aire exterior", "outdoor", "3-76",
     "La sonda de ambiente exterior está abierta, cortocircuitada o fuera de rango.",
     "Sonda NTC defectuosa|Cableado o conector defectuoso|PCB exterior defectuosa",
     "Medir resistencia y comparar con la curva|Comprobar conector y ubicación|Revisar entrada de la PCB",
     "Los controles dependientes de temperatura exterior se limitan y se registra H9."),
    ("J3", "Sonda de tubo de descarga", "outdoor", "3-76",
     "La sonda de descarga no entrega un valor válido.",
     "Sonda de descarga defectuosa|Cableado abierto o en corto|Contacto térmico deficiente|PCB exterior defectuosa",
     "Medir resistencia y comparar con la curva de alta temperatura|Revisar fijación y aislamiento|Comprobar conector",
     "La protección de descarga pierde su referencia y la unidad detiene o limita el compresor."),
    ("J5", "Sonda de tubo de aspiración", "outdoor", "3-76",
     "La sonda de aspiración está abierta, cortocircuitada o fuera de rango.",
     "Sonda NTC defectuosa|Cableado o conector defectuoso|PCB exterior defectuosa",
     "Comparar resistencia con la curva|Revisar contacto con la tubería|Comprobar continuidad",
     "La regulación basada en aspiración queda afectada y se registra J5."),
    ("J6", "Sonda del intercambiador exterior", "outdoor", "3-76",
     "La sonda de batería exterior no entrega un valor válido.",
     "Sonda NTC defectuosa|Cableado o conector defectuoso|PCB exterior defectuosa",
     "Comparar resistencia con la curva|Revisar ubicación y fijación|Comprobar entrada de la PCB",
     "Desescarche y control de condensación quedan afectados; la unidad se protege."),
    ("JC", "Sensor de presión de aspiración", "outdoor", "3-77",
     "La señal del sensor de baja presión está fuera del rango esperado.",
     "Sensor de presión defectuoso|Cableado o alimentación del sensor anómalos|Presión real fuera de rango|PCB exterior defectuosa",
     "Comparar presión real con la lectura|Revisar alimentación, señal y conector|Comprobar circuito frigorífico",
     "La unidad detiene o limita el compresor al perder una lectura fiable de aspiración."),
    ("L4", "Temperatura excesiva del disipador inverter", "outdoor", "3-79",
     "El disipador del módulo de potencia supera el límite.",
     "Ventilación exterior deficiente|Disipador sucio|Temperatura ambiente elevada|Sonda de aletas o módulo defectuoso",
     "Comprobar ventilador y paso de aire|Limpiar disipador|Verificar sonda y pasta térmica según el manual",
     "La etapa inverter reduce carga o detiene el compresor para proteger los semiconductores."),
    ("L5", "Sobrecorriente instantánea del inverter", "outdoor", "3-80",
     "El módulo de potencia detecta una corriente de salida excesiva.",
     "Compresor bloqueado o defectuoso|Cableado U/V/W anómalo|Módulo inverter defectuoso|Presión diferencial excesiva",
     "Revisar cableado y bobinados con alimentación desconectada|Comprobar condiciones de arranque|Seguir la prueba de módulo de potencia",
     "El inverter corta inmediatamente la salida al compresor."),
    ("L8", "Protección térmica electrónica del compresor", "outdoor", "3-82",
     "La corriente estimada del compresor permanece elevada.",
     "Sobrecarga mecánica|Presiones anormales|Tensión de alimentación baja|Compresor o inverter defectuoso",
     "Comprobar tensión y corriente|Revisar presiones, ventilación y carga|Comprobar compresor e inverter",
     "La frecuencia se limita y el compresor se detiene si la sobrecarga persiste."),
    ("L9", "Prevención de bloqueo del compresor", "outdoor", "3-84",
     "El control no logra mantener la rotación prevista del compresor.",
     "Compresor bloqueado|Diferencial de presión alto|Cableado defectuoso|Inverter defectuoso",
     "Esperar igualación de presiones y reintentar|Revisar terminales y bobinados|Comprobar inverter y compresor",
     "La unidad cancela el arranque y aplica la secuencia de reintento/protección."),
    ("LC", "Comunicación entre PCB de control e inverter", "outdoor", "3-86",
     "Las placas exterior principal e inverter dejan de intercambiar datos.",
     "Conector o cable entre placas defectuoso|Alimentación de una PCB ausente|PCB principal o inverter defectuosa|Ruido eléctrico",
     "Revisar conectores y alimentaciones con seguridad|Comprobar HAP y fusibles|Descartar interferencias y sustituir por diagnóstico",
     "La unidad exterior detiene el compresor al perder el control del inverter."),
    ("P1", "Falta de fase o desequilibrio de alimentación", "outdoor", "3-88",
     "La alimentación trifásica presenta fase ausente, invertida o desequilibrada.",
     "Fase ausente|Conexión floja|Desequilibrio excesivo|Circuito detector de la PCB defectuoso",
     "Medir todas las fases y tensión entre líneas|Revisar bornes y protecciones|Confirmar orden y equilibrio",
     "La unidad bloquea el arranque para proteger rectificador e inverter."),
    ("P4", "Sonda del disipador inverter", "outdoor", "3-90",
     "La sonda del módulo de potencia está abierta, en corto o fuera de rango.",
     "Sonda del disipador defectuosa|Conector o cable defectuoso|PCB inverter defectuosa",
     "Comparar resistencia con la curva oficial|Revisar fijación térmica y conector|Comprobar PCB",
     "La etapa inverter pierde la referencia térmica y detiene la salida."),
    ("PJ", "Ajuste de capacidad exterior incorrecto", "outdoor", "3-91",
     "La placa exterior no identifica una capacidad válida.",
     "Adaptador o memoria de capacidad incorrectos|PCB de sustitución sin configurar|Conexión defectuosa",
     "Comprobar código/adaptador de capacidad|Copiar los ajustes documentados antes de sustituir PCB|Reiniciar tras corregir",
     "La unidad impide el funcionamiento con una configuración de capacidad no válida."),
    ("U0", "Falta de refrigerante o aspiración anormal", "system", "3-92",
     "El control deduce falta de refrigerante a partir de temperaturas y presión de aspiración.",
     "Fuga o carga insuficiente|Válvula de cierre parcialmente cerrada|Restricción frigorífica|Sonda o sensor incorrectos",
     "Buscar fugas y confirmar carga por procedimiento oficial|Comprobar válvulas y restricciones|Contrastar sondas y presión",
     "La unidad limita capacidad y puede detenerse si se confirma la condición de bajo refrigerante."),
    ("U2", "Tensión de alimentación anormal", "outdoor", "3-93",
     "La tensión del circuito principal cae o supera el rango permitido.",
     "Tensión de red anormal|Conexión floja o fase ausente|Rectificador o condensadores defectuosos|PCB inverter defectuosa",
     "Medir tensión de entrada y bus con procedimiento seguro|Revisar bornes y protecciones|Comprobar rectificador e inverter",
     "El inverter detiene la salida para proteger el circuito de potencia."),
    ("U4", "Comunicación interior–exterior", "system", "3-96",
     "La unidad interior y la exterior no intercambian datos correctamente.",
     "Cableado de transmisión abierto, cruzado o en corto|Alimentación ausente en una unidad|PCB interior o exterior defectuosa|Ruido eléctrico",
     "Comprobar alimentación de ambas unidades|Revisar continuidad y bornes de transmisión|Observar LED HAP y aislar la placa sin comunicación",
     "El sistema no puede coordinar compresor y unidad interior y detiene la operación."),
    ("UF", "Cableado o transmisión incorrectos durante la instalación", "system", "3-96",
     "La prueba detecta una combinación de tubería, cableado o transmisión no válida.",
     "Cableado interior–exterior incorrecto|Válvula de cierre cerrada|Combinación de unidades no válida",
     "Verificar bornes y correspondencia|Confirmar válvulas abiertas|Repetir la prueba después de corregir",
     "La puesta en marcha no se completa y el sistema permanece bloqueado."),
    ("U5", "Comunicación entre unidad interior y mando", "controller", "3-98",
     "El microprocesador no recibe comunicación normal del mando durante el tiempo establecido.",
     "Mando defectuoso|PCB interior defectuosa|Cable multicore o interferencias|Dos mandos configurados como principal",
     "Comprobar cable independiente de dos conductores|Configurar un mando como secundario si hay dos|Reiniciar y aislar mando/PCB",
     "El mando no controla la unidad; en grupos puede quedar afectada la unidad asociada."),
    ("U8", "Comunicación entre mando principal y secundario", "controller", "3-99",
     "Dos mandos de una misma unidad no mantienen una relación principal/secundario válida.",
     "Ambos mandos en principal o ambos en secundario|Cableado entre mandos/unidad defectuoso|PCB de mando defectuosa",
     "Dejar exactamente un mando principal y otro secundario|Cortar alimentación y reiniciar|Probar cada mando por separado",
     "La unidad no puede resolver qué mando tiene prioridad y registra U8."),
    ("UA", "Ajuste de campo o combinación de sistema incorrectos", "system", "3-100",
     "La combinación pair/twin/triple/double-twin o su configuración no coincide.",
     "Ajuste de número de interiores incorrecto|Capacidades incompatibles|Cableado interior–interior o interior–exterior incorrecto|PCB defectuosa",
     "Revisar combinaciones y ajustes de campo|Comprobar cableado del sistema simultáneo|Confirmar adaptadores de capacidad",
     "La puesta en marcha se bloquea hasta que la combinación sea coherente."),
    ("UC", "Dirección de control central incorrecta", "system", "3-102",
     "La dirección de control central no es válida o está duplicada.",
     "Dirección duplicada|Dirección no configurada|Cableado de control central defectuoso",
     "Revisar direcciones de grupo y AirNet|Eliminar duplicados|Comprobar el bus centralizado",
     "La unidad local puede quedar sin supervisión central o el sistema centralizado marca UC."),
]


MULTI_ERROR_SPECS = [
    ("A1", "PCB interior — familia residencial/multisplit", "indoor", "114",
     "La PCB interior no supera su autocomprobación.", "PCB interior defectuosa|Alimentación o conector anómalos",
     "Reiniciar y observar indicadores|Comprobar alimentación y PCB", "La unidad interior afectada se detiene."),
    ("A3", "Control de nivel de drenaje — cassette FFQ", "indoor", "126",
     "La boya o bomba no mantiene el nivel de drenaje.", "Bomba o boya defectuosa|Desagüe obstruido|PCB interior defectuosa",
     "Comprobar evacuación, bomba y boya|Revisar conectores", "La cassette detiene la demanda y mantiene la protección de drenaje."),
    ("A5", "Protección antihielo / limitación de calefacción", "indoor", "116",
     "La batería interior alcanza una condición de congelación o pico térmico.", "Caudal de aire insuficiente|Filtro o batería sucios|Carga o expansión anómalas|Sonda incorrecta",
     "Comprobar flujo de aire y limpieza|Contrastar sonda y circuito frigorífico", "La frecuencia se reduce o el compresor se detiene temporalmente."),
    ("A6", "Motor de ventilador interior — multisplit", "indoor", "117",
     "No se detecta la rotación prevista del ventilador.", "Motor o rotor bloqueado|Cableado defectuoso|PCB interior defectuosa",
     "Comprobar giro libre y conectores|Verificar motor y PCB", "La unidad interior afectada se detiene."),
    ("AF", "Sistema de drenaje — cassette FFQ", "indoor", "128",
     "Se detecta una condición anormal de drenaje.", "Retorno de agua|Bomba o boya defectuosa|Tubería fuera de especificación",
     "Comprobar altura, longitud y sifón|Revisar bomba, boya y desagüe", "La cassette protege la bandeja incluso con el compresor parado."),
    ("C4", "Sonda 1 del intercambiador interior", "indoor", "129",
     "La sonda de batería 1 está abierta o en corto.", "Sonda o cable defectuoso|PCB interior defectuosa",
     "Medir resistencia|Revisar conector y PCB", "La unidad afectada detiene o limita su operación."),
    ("C5", "Sonda 2 del intercambiador interior", "indoor", "129",
     "La sonda de batería 2 está abierta o en corto.", "Sonda o cable defectuoso|PCB interior defectuosa",
     "Medir resistencia|Revisar conector y PCB", "La unidad afectada detiene o limita su operación."),
    ("C9", "Sonda de ambiente interior — multisplit", "indoor", "129",
     "La sonda de retorno está abierta o en corto.", "Sonda o cable defectuoso|PCB interior defectuosa",
     "Medir resistencia|Revisar ubicación y conector", "La regulación de la unidad afectada queda limitada."),
    ("CJ", "Sonda incorporada en el mando", "controller", "130",
     "El sensor de ambiente del mando no entrega un valor válido.", "Sensor o PCB del mando defectuosos|Cableado anómalo",
     "Comprobar mando y cable|Usar la sonda interior si la configuración lo permite", "El control puede continuar con la sonda de la unidad interior."),
    ("U5", "Comunicación mando–interior — cassette FFQ", "controller", "131",
     "No hay transmisión normal entre mando e interior.", "Mando o PCB interior defectuosos|Cableado/ruido|Dos mandos principales",
     "Revisar cable independiente|Configurar principal/secundario|Reiniciar", "La unidad asociada no recibe órdenes válidas."),
    ("U8", "Principal/secundario incorrecto — cassette FFQ", "controller", "132",
     "Los dos mandos no tienen una configuración principal/secundario válida.", "Dos secundarios o dos principales|Mando defectuoso|Cableado anómalo",
     "Dejar un principal y un secundario|Reiniciar y probar mandos", "El control por dos mandos queda bloqueado."),
    ("UA", "Ajuste de campo anormal — multisplit", "system", "133",
     "La configuración de campo no coincide con el sistema.", "Combinación o tensión no especificada|Ajuste incorrecto|Cableado incompatible",
     "Verificar combinación y tensión|Revisar ajustes y cableado", "La puesta en marcha se bloquea."),
    ("U0", "Falta de refrigerante — multisplit", "system", "134",
     "El control detecta condiciones compatibles con carga insuficiente.", "Fuga o carga baja|Válvula cerrada|Restricción",
     "Buscar fugas y comprobar carga|Revisar válvulas y tuberías", "El sistema limita o detiene el compresor."),
    ("U2", "Baja o alta tensión — multisplit", "outdoor", "136",
     "La tensión del circuito de potencia queda fuera de rango.", "Red anómala|Conexión floja|PCB de potencia defectuosa",
     "Medir alimentación|Revisar bornes y PCB", "La exterior detiene el inverter."),
    ("U3", "Comprobación de cableado no ejecutada", "system", "138",
     "La memoria indica que la función de verificación de cableado no se ha completado.", "PCB sustituida|Comprobación inicial pendiente|Proceso cancelado",
     "Ejecutar Wiring Error Check con las condiciones del manual|Confirmar resultado en LED", "El sistema exige completar la puesta en marcha."),
    ("UH", "Protección antihielo en otras habitaciones", "system", "139",
     "Otra unidad interior entra en protección antihielo durante el funcionamiento multisplit.", "Caudal de aire insuficiente|Carga/expansión anómalas|Condición de baja temperatura",
     "Identificar la unidad afectada|Comprobar aire, sondas y circuito frigorífico", "Otras habitaciones pueden quedar en espera o con capacidad limitada."),
    ("E1", "PCB exterior — multisplit", "outdoor", "142",
     "La PCB exterior detecta una anomalía interna.", "PCB exterior defectuosa|Alimentación anómala",
     "Reiniciar y observar LED|Comprobar alimentación y PCB", "La exterior detiene el sistema."),
    ("E5", "Sobrecarga del compresor (OL)", "outdoor", "143",
     "Se activa la protección de sobrecarga del compresor.", "Compresor sobrecargado|Presiones anormales|Alimentación baja|Protector OL defectuoso",
     "Comprobar presiones, tensión y corriente|Revisar compresor y protector", "La exterior detiene el compresor."),
    ("E6", "Compresor bloqueado — multisplit", "outdoor", "145",
     "El inverter no logra hacer girar el compresor.", "Compresor bloqueado|Cableado U/V/W anómalo|Módulo de potencia defectuoso",
     "Revisar conexiones y bobinados|Seguir la prueba de módulo", "El arranque se cancela."),
    ("E7", "Ventilador DC exterior bloqueado", "outdoor", "146",
     "No se detecta la rotación del ventilador DC.", "Aspas bloqueadas|Motor o cableado defectuosos|PCB exterior defectuosa",
     "Comprobar giro libre|Revisar motor, conector y PCB", "La exterior detiene o limita el compresor."),
    ("E8", "Sobrecorriente de entrada", "outdoor", "147",
     "La corriente absorbida por la unidad exterior supera el límite.", "Sobrecarga de compresor|Tensión anómala|Circuito inverter defectuoso",
     "Medir tensión y corriente|Comprobar compresor, presiones e inverter", "La salida inverter se detiene."),
    ("EA", "Válvula de cuatro vías anormal", "outdoor", "148",
     "Las temperaturas no corresponden con la posición ordenada de la válvula de cuatro vías.", "Bobina o válvula defectuosa|Conector/cableado anómalo|Falta de refrigerante|Sondas incorrectas",
     "Comprobar bobina y señal|Comparar temperaturas y carga|Revisar sondas", "El cambio frío/calor no se valida y el sistema se protege."),
    ("F3", "Control de temperatura de descarga — multisplit", "outdoor", "150",
     "La descarga alcanza una condición de protección.", "Falta de refrigerante|Restricción|Sonda o compresor anómalos",
     "Comprobar carga, fugas y válvulas|Contrastar sonda", "La frecuencia se reduce o el compresor se detiene."),
    ("F6", "Control de alta presión en refrigeración", "outdoor", "151",
     "La condensación alcanza una condición de alta presión.", "Sobrecarga|Ventilación deficiente|Válvula cerrada|Sonda anómala",
     "Comprobar aire, válvulas y carga|Medir presiones", "El sistema reduce capacidad o detiene el compresor."),
    ("H0", "Sistema de sensores del compresor", "outdoor", "152",
     "Las señales usadas para controlar el compresor no son coherentes.", "Sensor o cableado defectuoso|PCB exterior defectuosa",
     "Revisar sensores y conectores|Comprobar PCB", "La exterior detiene el compresor."),
    ("H6", "Sensor de posición del compresor", "outdoor", "154",
     "El inverter no detecta correctamente la posición del rotor.", "Compresor o cableado defectuosos|Módulo de potencia defectuoso",
     "Revisar U/V/W y bobinados|Comprobar módulo y compresor", "El arranque se cancela."),
    ("H8", "Transformador/sensor de corriente", "outdoor", "156",
     "La lectura de corriente no corresponde con el estado del compresor.", "CT o circuito de medida defectuoso|Cableado/PCB anómalos",
     "Comprobar conexiones y lectura|Revisar PCB exterior", "La regulación de corriente se invalida y el compresor se detiene."),
    ("H9", "Sonda de aire exterior — multisplit", "outdoor", "158",
     "La sonda exterior está abierta o en corto.", "Sonda/cable defectuoso|PCB exterior defectuosa",
     "Medir resistencia|Revisar conector", "El control dependiente de ambiente se limita."),
    ("J3", "Sonda de descarga — multisplit", "outdoor", "158",
     "La sonda de descarga está abierta o en corto.", "Sonda/cable defectuoso|PCB exterior defectuosa",
     "Medir resistencia|Revisar fijación y conector", "La exterior detiene o limita el compresor."),
    ("J6", "Sonda de batería exterior — multisplit", "outdoor", "158",
     "La sonda del intercambiador exterior está abierta o en corto.", "Sonda/cable defectuoso|PCB exterior defectuosa",
     "Medir resistencia|Revisar ubicación y conector", "Desescarche y control de presión se limitan."),
    ("J8", "Sonda de tubería líquida", "outdoor", "158",
     "La sonda de líquido está abierta o en corto.", "Sonda/cable defectuoso|PCB exterior defectuosa",
     "Medir resistencia|Identificar qué puerto/unidad causa el error", "El manual indica parada del sistema si todas las unidades se juzgan con J8."),
    ("J9", "Sonda de tubería de gas", "outdoor", "158",
     "La sonda de gas está abierta o en corto.", "Sonda/cable defectuoso|PCB exterior defectuosa",
     "Medir resistencia|Identificar puerto afectado", "La capacidad de la rama afectada queda limitada o protegida."),
    ("P4", "Sonda del disipador — multisplit", "outdoor", "158",
     "La sonda térmica del disipador está abierta o en corto.", "Sonda/PCB defectuosas|Conector anómalo",
     "Medir resistencia|Revisar PCB y contacto térmico", "El inverter detiene la salida."),
    ("L3", "Temperatura alta de la caja eléctrica", "outdoor", "160",
     "La temperatura interna de la caja eléctrica supera el límite.", "Ventilación deficiente|Temperatura exterior alta|PCB o sonda anómalas",
     "Comprobar flujo de aire y suciedad|Revisar sonda y montaje", "La capacidad se limita o el compresor se detiene."),
    ("L4", "Temperatura alta del disipador — multisplit", "outdoor", "161",
     "El disipador inverter supera su límite.", "Ventilación deficiente|Disipador sucio|Módulo defectuoso",
     "Comprobar ventilador y disipador|Revisar módulo", "El inverter se protege."),
    ("L5", "Sobrecorriente de salida — multisplit", "outdoor", "162",
     "La corriente de salida del inverter supera el límite.", "Compresor bloqueado|Cableado U/V/W|Módulo defectuoso",
     "Revisar cableado y compresor|Seguir prueba de módulo", "La salida se corta inmediatamente."),
]


VRV_INTERPRETATIONS = [
    ("E3", "E3-01/03/05 — presostato de alta activado", "outdoor", "55",
     "La unidad maestra o una esclava activa S1PH/S2PH.", "Válvula cerrada|Tubería obstruida|Caudal de aire insuficiente|Presión alta real",
     "Comprobar válvulas, tubería y flujo de aire|Medir presión y revisar el presostato",
     "La exterior afectada detiene el compresor; el subcódigo identifica maestra, esclava 1 o esclava 2.",
     "E3-01|E3-03|E3-05"),
    ("E3", "E3-02/04/06/18 — sobrecarga o válvula cerrada", "system", "55",
     "La lógica VRV detecta sobrecarga o una válvula de cierre sin abrir.", "Sobrecarga de refrigerante|Válvula de cierre cerrada",
     "Comprobar carga y abrir válvulas|Repetir la comprobación después de corregir",
     "La prueba/operación se detiene; los subcódigos 02/04/06 sitúan la exterior y 18 corresponde al sistema.",
     "E3-02|E3-04|E3-06|E3-18"),
    ("E3", "E3-13/14/15 — válvula de líquido cerrada", "outdoor", "55",
     "La unidad detecta la válvula de cierre de líquido cerrada.", "Válvula de líquido cerrada|Paso de líquido bloqueado",
     "Abrir la válvula de líquido|Comprobar la línea si ya estaba abierta",
     "El subcódigo distingue maestra y esclavas y bloquea el funcionamiento.",
     "E3-13|E3-14|E3-15"),
    ("E4", "E4-01/02/03 — protección de baja presión", "outdoor", "55",
     "La aspiración cae por debajo del límite o la detección de baja es anormal.", "Válvula cerrada|Falta de refrigerante|Fallo interior|Sensor/presostato de baja",
     "Abrir válvulas y comprobar carga|Consultar errores interiores y transmisión|Verificar la detección de baja",
     "La exterior identificada por el subcódigo detiene el compresor.",
     "E4-01|E4-02|E4-03"),
    ("E9", "E9-01/05/08 — EEV de subenfriamiento Y2E", "outdoor", "56",
     "Fallo de la válvula Y2E conectada a A1P X21A.", "Bobina o conector defectuoso|Válvula bloqueada|PCB A1P defectuosa",
     "Revisar X21A y bobina Y2E|Comprobar movimiento e inicialización",
     "La exterior afectada no controla el subenfriamiento y se protege.",
     "E9-01|E9-05|E9-08"),
    ("E9", "E9-04/07/10 — EEV principal Y1E", "outdoor", "56",
     "Fallo de la válvula principal Y1E conectada a A1P X23A.", "Bobina/conector defectuoso|Válvula bloqueada|PCB defectuosa",
     "Revisar X23A y bobina Y1E|Comprobar inicialización",
     "La exterior afectada detiene o limita la circulación de refrigerante.",
     "E9-04|E9-07|E9-10"),
    ("E9", "E9-03/06/09 — EEV del receptor Y3E", "outdoor", "56",
     "Fallo de la válvula Y3E conectada a A1P X22A.", "Bobina/conector defectuoso|Válvula bloqueada|PCB defectuosa",
     "Revisar X22A y bobina Y3E|Comprobar inicialización",
     "La exterior afectada pierde el control del receptor.",
     "E9-03|E9-06|E9-09"),
    ("F3", "F3-01/03/05 — descarga R21T/R22T demasiado alta", "outdoor", "56",
     "La temperatura de descarga supera el límite.", "Válvula cerrada|Falta de refrigerante|Restricción|Sonda incorrecta",
     "Comprobar válvulas, carga y fugas|Contrastar R21T/R22T",
     "La exterior identificada reduce frecuencia y detiene el compresor si persiste.",
     "F3-01|F3-03|F3-05"),
    ("F3", "F3-20/21/22 — carcasa de compresor R8T alta", "outdoor", "56",
     "La temperatura de la carcasa del compresor supera el límite.", "Válvula cerrada|Falta de refrigerante|Refrigeración del compresor insuficiente",
     "Comprobar válvulas, carga y R8T|Revisar retorno de refrigerante",
     "La exterior correspondiente protege el compresor.",
     "F3-20|F3-21|F3-22"),
    ("F6", "F6-02 — sobrecarga o válvula cerrada", "system", "56",
     "La lógica de alta presión en refrigeración detecta sobrecarga o cierre de válvula.", "Sobrecarga|Válvula de cierre cerrada",
     "Comprobar carga y válvulas|Medir presiones",
     "El sistema limita o detiene la operación en refrigeración.",
     "F6-02"),
    ("H9", "H9-01/02/03 — sonda ambiente R1T", "outdoor", "56",
     "La sonda R1T de la exterior indicada está abierta o en corto.", "Sonda/cable defectuoso|Entrada A1P X18A defectuosa",
     "Revisar X18A y medir R1T|Comprobar PCB",
     "La exterior afectada pierde la referencia de ambiente y se protege.",
     "H9-01|H9-02|H9-03"),
    ("J3", "J3 — sondas de descarga R21T/R22T y carcasa R8T", "outdoor", "56",
     "Los subcódigos distinguen sonda y condición abierta/cortocircuitada.", "Sonda abierta o en corto|Cable/conector defectuoso|PCB defectuosa",
     "Usar el subcódigo para seleccionar R21T, R22T o R8T|Medir la sonda y revisar cableado",
     "La exterior identificada detiene o limita su compresor.",
     "J3-16|J3-17|J3-18|J3-19|J3-22|J3-23|J3-24|J3-25|J3-28|J3-29|J3-30|J3-31|J3-47|J3-48|J3-49|J3-50|J3-51|J3-52"),
    ("J5", "J5-01/03/05 — sonda de aspiración R3T", "outdoor", "56",
     "La sonda de aspiración R3T está abierta o en corto.", "Sonda/cable defectuoso|PCB defectuosa",
     "Medir R3T y revisar conector|Identificar exterior por subcódigo",
     "La exterior afectada pierde la referencia de aspiración.",
     "J5-01|J5-03|J5-05"),
    ("J6", "J6-01/02/03 — sonda de desescarche R7T", "outdoor", "56",
     "La sonda R7T de desescarche está abierta o en corto.", "Sonda/cable defectuoso|PCB defectuosa",
     "Medir R7T y revisar conector|Identificar exterior por subcódigo",
     "El desescarche de la exterior afectada no puede controlarse normalmente.",
     "J6-01|J6-02|J6-03"),
    ("J7", "J7-06/07/08 — líquido después del subenfriador R5T", "outdoor", "56",
     "La sonda R5T está abierta o en corto.", "Sonda/cable defectuoso|PCB defectuosa",
     "Medir R5T y revisar conector|Identificar exterior por subcódigo",
     "El control de subenfriamiento de la exterior afectada se limita.",
     "J7-06|J7-07|J7-08"),
    ("J8", "J8-01/02/03 — sonda de líquido de batería R4T", "outdoor", "56",
     "La sonda R4T está abierta o en corto.", "Sonda/cable defectuoso|PCB defectuosa",
     "Medir R4T y revisar conector|Identificar exterior por subcódigo",
     "La exterior afectada pierde la referencia de líquido de batería.",
     "J8-01|J8-02|J8-03"),
    ("J9", "J9-01/02/03 — gas después del subenfriador R6T", "outdoor", "56",
     "La sonda R6T está abierta o en corto.", "Sonda/cable defectuoso|PCB defectuosa",
     "Medir R6T y revisar conector|Identificar exterior por subcódigo",
     "El control de subenfriamiento queda limitado.",
     "J9-01|J9-02|J9-03"),
    ("JA", "JA-06/08/10 y 07/09/11 — sensor de alta S1NPH", "outdoor", "56",
     "El sensor de alta presión está abierto o en corto.", "Sensor/cable defectuoso|Alimentación/señal de sensor anómala|PCB defectuosa",
     "Usar el subcódigo para distinguir abierto/corto y exterior|Comparar lectura con manómetro",
     "La exterior afectada detiene el compresor al perder la lectura de alta.",
     "JA-06|JA-07|JA-08|JA-09|JA-10|JA-11"),
    ("JC", "JC-06/08/10 y 07/09/11 — sensor de baja S1NPL", "outdoor", "57",
     "El sensor de baja presión está abierto o en corto.", "Sensor/cable defectuoso|Alimentación/señal anómala|PCB defectuosa",
     "Usar el subcódigo para distinguir abierto/corto y exterior|Comparar lectura con manómetro",
     "La exterior afectada detiene el compresor al perder la lectura de baja.",
     "JC-06|JC-07|JC-08|JC-09|JC-10|JC-11"),
    ("LC", "LC-14/19/24/30 — comunicación de inverter y ventiladores", "outdoor", "57",
     "Se pierde comunicación con INV1, FAN1, FAN2 o INV2.", "Cable/conector entre placas|Alimentación ausente|PCB de control, inverter o ventilador defectuosa",
     "Usar el subcódigo para identificar el módulo|Revisar alimentación y conectores",
     "El módulo afectado se detiene y puede bloquear la exterior.",
     "LC-14|LC-19|LC-24|LC-30"),
    ("P1", "P1-01/02/03 y 07/08/09 — desequilibrio de alimentación", "outdoor", "57",
     "INV1 o INV2 detecta desequilibrio de alimentación.", "Fase ausente|Tensión desequilibrada|Bornes flojos|Detector defectuoso",
     "Medir fases y revisar bornes|Identificar inverter por subcódigo",
     "El inverter identificado no arranca.",
     "P1-01|P1-02|P1-03|P1-07|P1-08|P1-09"),
    ("U1", "U1-01/04/05/06/07/08 — fase invertida", "outdoor", "57",
     "La secuencia de fases no es válida.", "Fases invertidas|Cableado de alimentación incorrecto",
     "Comprobar secuencia de fases|Corregir cableado con alimentación desconectada",
     "La exterior impide el arranque.",
     "U1-01|U1-04|U1-05|U1-06|U1-07|U1-08"),
    ("U2", "U2 — ausencia o pérdida de fase en INV1/INV2", "outdoor", "57",
     "Los subcódigos separan ausencia de alimentación y pérdida de fase en cada inverter.", "Fase ausente|Protección abierta|Conexión floja|PCB de potencia defectuosa",
     "Usar subcódigo para identificar INV1/INV2|Medir alimentación y revisar protecciones",
     "El inverter afectado se detiene.",
     "U2-01|U2-02|U2-08|U2-09|U2-11|U2-12|U2-22|U2-23|U2-25|U2-26|U2-28|U2-29"),
    ("U3", "U3-02 — prueba de fugas/carga no realizada", "system", "57",
     "La comprobación exigida no se ha ejecutado, pero el manual indica que la operación es posible.", "Puesta en marcha incompleta|Comprobación omitida",
     "Ejecutar la prueba indicada para la instalación|Revisar historial al terminar",
     "Advertencia: el sistema puede funcionar, pero la puesta en marcha no está validada.",
     "U3-02"),
    ("U3", "U3-03 — prueba del sistema no realizada", "system", "57",
     "La prueba obligatoria del sistema no se ha completado.", "Test de puesta en marcha pendiente|Proceso cancelado o anormal",
     "Ejecutar la prueba del sistema|Corregir errores y repetir",
     "La operación es imposible hasta completar correctamente la prueba.",
     "U3-03"),
    ("U4", "U4-01/03 — transmisión Q1/Q2 o interior–exterior", "system", "57",
     "El cableado Q1/Q2 o la transmisión interior–exterior es incorrecto.", "Cableado abierto, cruzado o en corto|Alimentación ausente|PCB defectuosa",
     "Revisar Q1/Q2 y transmisión|Comprobar alimentación y topología",
     "El sistema no puede coordinar unidades y se detiene.",
     "U4-01|U4-03"),
    ("U4", "U4-04 — prueba finalizada anormalmente", "system", "57",
     "El Test Run terminó con un resultado anormal.", "Error activo durante prueba|Cableado, válvula o configuración incorrectos",
     "Consultar historial/subcódigo|Corregir la causa y repetir Test Run",
     "La puesta en marcha no queda aceptada.",
     "U4-04"),
    ("U7", "U7-01/02 — transmisión entre exteriores Q1/Q2", "system", "57",
     "Advertencia o error de transmisión entre unidades exteriores.", "Q1/Q2 abierto, cruzado o en corto|Exterior sin alimentación|Dirección/configuración incorrecta",
     "Revisar Q1/Q2, alimentación y configuración maestra/esclava",
     "U7-01 es advertencia; U7-02 bloquea la comunicación entre exteriores.",
     "U7-01|U7-02"),
    ("U7", "U7-11 — demasiadas interiores o fallo F1/F2", "system", "57",
     "La red F1/F2 supera la capacidad o contiene un error de cableado.", "Demasiadas unidades interiores|F1/F2 abierto, cruzado o en corto|Topología incorrecta",
     "Contar unidades y revisar F1/F2|Comprobar ramificaciones y terminación",
     "El reconocimiento de interiores falla y la red no se pone en marcha.",
     "U7-11"),
    ("U9", "U9-01 — combinación de sistema o error interior", "system", "58",
     "La exterior recibe una combinación no válida o un fallo originado en una interior.", "Combinación incorrecta|Unidad interior en error|Configuración incompatible",
     "Consultar códigos interiores|Revisar combinación y configuración",
     "El sistema bloquea la puesta en marcha o la rama afectada.",
     "U9-01"),
    ("UA", "UA-03/18/31/49 — combinación incorrecta", "system", "58",
     "Los subcódigos distinguen conexión/tipo interior y combinación múltiple.", "Tipo o capacidad incompatible|Conexión incorrecta|Combinación múltiple no autorizada",
     "Usar el subcódigo para identificar la regla incumplida|Revisar combinación documental",
     "La puesta en marcha queda bloqueada.",
     "UA-03|UA-18|UA-31|UA-49"),
    ("UH", "UH-01 — identificación automática inconsistente", "system", "58",
     "El reconocimiento automático no coincide con las unidades realmente conectadas.", "Unidad sin alimentación|Transmisión defectuosa|Dirección o combinación incorrecta",
     "Comprobar alimentación y red|Repetir identificación después de corregir",
     "La red no valida su topología.",
     "UH-01"),
    ("UF", "UF-01 — identificación automática inconsistente", "system", "58",
     "La identificación automática devuelve una topología incoherente.", "Cableado/transmisión incorrectos|Unidad ausente|Configuración no válida",
     "Revisar red y unidades conectadas|Repetir identificación",
     "La puesta en marcha no se completa.",
     "UF-01"),
    ("UF", "UF-05 — válvula cerrada o incorrecta durante Test Run", "system", "58",
     "La prueba detecta una válvula de cierre cerrada o en posición incorrecta.", "Válvula de gas o líquido cerrada|Circuito frigorífico bloqueado",
     "Abrir válvulas correctas|Repetir Test Run",
     "La prueba se detiene para proteger el compresor.",
     "UF-05"),
    ("P2", "P2 — aspiración baja durante carga automática", "system", "58",
     "La presión de aspiración cae durante Auto Charge.", "Carga insuficiente temporal|Válvula/restricción|Condiciones de operación inadecuadas",
     "Comprobar válvulas y condiciones|Seguir el procedimiento de carga",
     "La carga automática se pausa o cancela.",
     "P2"),
    ("P8", "P8 — prevención de congelación interior durante carga", "system", "58",
     "Una unidad interior entra en protección antihielo durante Auto Charge.", "Caudal de aire insuficiente|Temperatura interior baja|Condición frigorífica anómala",
     "Comprobar interiores y caudal|Reanudar solo en condiciones válidas",
     "La carga automática se pausa para evitar congelación.",
     "P8"),
    ("PE", "PE — carga automática casi finalizada", "system", "58",
     "Estado informativo de Auto Charge próximo a terminar.", "Proceso normal de carga automática",
     "Esperar finalización y no interpretar como avería", "El sistema continúa el proceso de carga automática.",
     "PE"),
    ("P9", "P9 — carga automática completada", "system", "58",
     "Estado que confirma la finalización de Auto Charge.", "Proceso normal finalizado",
     "Registrar el resultado y salir según el procedimiento", "La carga automática ha finalizado.",
     "P9"),
    ("E-1", "E-1 — sistema no preparado para detección de fugas", "system", "58",
     "No se cumplen las condiciones previas para Leak Detection.", "Puesta en marcha incompleta|Condiciones de temperatura/configuración no válidas",
     "Completar la puesta en marcha|Revisar condiciones y repetir",
     "La prueba de fugas no comienza.",
     "E-1"),
    ("E-2", "E-2 — interiores fuera del rango térmico para detección de fugas", "system", "58",
     "La temperatura de una o más interiores no permite ejecutar Leak Detection.", "Temperatura interior fuera del rango permitido",
     "Acondicionar los locales y repetir la prueba", "La detección de fugas queda aplazada.",
     "E-2"),
    ("A0-11", "Alarma de detección de fuga de refrigerante R32", "controller", "128",
     "Madoka muestra la unidad o dirección supervisada que origina la alarma.", "Fuga de refrigerante detectada|Sensor o sistema de detección activado",
     "Detener la alarma durante 3 segundos y localizar la unidad indicada|Reparar la fuga antes de rearmar",
     "El mando genera alarma; en modo Supervisor solo muestra la primera dirección que elevó el error.",
     "A0-11"),
]


STANDARD_CURVE = [
    (-20, 197.81), (-10, 111.99), (0, 65.84), (10, 39.96),
    (20, 25.01), (25, 20.00), (30, 16.10), (40, 10.63),
    (50, 7.18), (60, 4.96), (70, 3.50), (80, 2.51),
]
FIN_CURVE = [
    (-20, 192.08), (-10, 108.96), (0, 64.17), (10, 39.01),
    (20, 24.45), (25, 19.56), (30, 15.76), (40, 10.41),
    (50, 7.04), (60, 4.87), (70, 3.44), (80, 2.47),
]
DISCHARGE_CURVE = [
    (0, 806.5), (20, 292.9), (40, 118.7), (60, 52.8), (80, 25.4),
    (100, 13.1), (120, 7.1), (140, 4.1), (160, 2.5), (180, 1.5),
]


def dataset_curve(dataset_id: int, name: str, points: list[tuple[float, float]], page: str) -> dict[str, Any]:
    return {
        "id": dataset_id,
        "name": name,
        "dataset_type": "sensor_curve",
        "variable_name": "Temperatura",
        "variable_unit": "°C",
        "value_name": "Resistencia",
        "value_unit": "kΩ",
        "tolerance_text": "Usar la curva de la familia indicada; no extrapolar a otra sonda por el mismo código.",
        "source_kind": "official",
        "calculation_method": None,
        "review_status": "reviewed",
        "notes": "Puntos transcritos de la tabla del manual de servicio.",
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
        "sources": [source("RZQS", page, "Thermistor resistance check")],
    }


def datasets_for_code(code: str, interpretation_id: int, ref: str) -> list[dict[str, Any]]:
    if ref != "RZQS":
        return []
    base = interpretation_id * 10
    if code in {"C4", "C5", "C9", "H9", "J5", "J6"}:
        return [dataset_curve(base + 1, f"{code} — curva NTC de la familia", STANDARD_CURVE, "3-107")]
    if code == "P4":
        return [dataset_curve(base + 1, "P4 — sonda de temperatura del módulo", FIN_CURVE, "3-107")]
    if code == "J3":
        return [dataset_curve(base + 1, "J3 — sonda de descarga de alta temperatura", DISCHARGE_CURVE, "3-108")]
    return []


def error_source(ref: str, code: str, page: str, title: str) -> dict[str, Any]:
    if ref == "RZQS":
        return source(ref, page, f"Detección de averías — {code}: {title}")
    if ref == "MXL":
        return source(ref, page, f"Service Diagnosis — {code}: {title}")
    if ref == "MADOKA":
        return source(ref, page, "Refrigerant leak detection")
    return source(ref, page, f"Tabla de códigos y subcódigos — {code}: {title}")


def operational_impact(behavior: str) -> dict[str, Any]:
    lowered = behavior.lower()
    if "puede funcionar" in lowered or "continúa" in lowered:
        level = "warning"
    elif "unidad interior afectada" in lowered or "exterior afectada" in lowered or "módulo afectado" in lowered:
        level = "affected_unit"
    elif "sistema" in lowered and any(word in lowered for word in ("detiene", "bloque", "imposible")):
        level = "all_system"
    else:
        level = "protected_stop"
    return {
        "stop_level": level,
        "summary": behavior,
        "affected_scope": "La unidad, módulo o sistema descrito por esta variante documental.",
        "unaffected_scope": None,
        "restart_behavior": "Corregir la causa y seguir el rearme o la repetición de prueba indicados por el manual.",
        "degraded_behavior": None,
        "notes": "No se generaliza el alcance a otras familias Daikin.",
    }


def build_interpretation(
    interpretation_id: int,
    *,
    code: str,
    title: str,
    scope: str,
    page: str,
    description: str,
    causes: str,
    checks: str,
    behavior: str,
    ref: str,
    aliases: str = "",
) -> dict[str, Any]:
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

    add("machine_behavior", behavior)
    add("related_element", title)
    for row in split_items(causes):
        add("cause", row)
    for row in split_items(checks):
        add("check", row)
    add(
        "observation",
        f"Variante documentada en {SOURCES[ref]['document_ref']}; "
        "el mismo código puede tener otro significado en otra familia Daikin.",
    )
    return {
        "id": interpretation_id,
        "title": title,
        "description": description,
        "source_kind": "official",
        "confidence": "high",
        "review_status": "reviewed",
        "info_items": info,
        "operational_impacts": [operational_impact(behavior)],
        "datasets": datasets_for_code(code, interpretation_id, ref),
        "sources": [error_source(ref, code, page, title)],
        "_aliases": split_items(aliases),
        "_scope": scope,
    }


def build_errors() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    interpretation_id = 0

    for ref, specs in (("RZQS", RZQS_ERROR_SPECS), ("MXL", MULTI_ERROR_SPECS)):
        for code, title, scope, page, description, causes, checks, behavior in specs:
            interpretation_id += 1
            by_code[code].append(build_interpretation(
                interpretation_id,
                code=code,
                title=title,
                scope=scope,
                page=page,
                description=description,
                causes=causes,
                checks=checks,
                behavior=behavior,
                ref=ref,
            ))

    for code, title, scope, page, description, causes, checks, behavior, aliases in VRV_INTERPRETATIONS:
        interpretation_id += 1
        ref = "MADOKA" if code == "A0-11" else "VRV4"
        by_code[code].append(build_interpretation(
            interpretation_id,
            code=code,
            title=title,
            scope=scope,
            page=page,
            description=description,
            causes=causes,
            checks=checks,
            behavior=behavior,
            ref=ref,
            aliases=aliases,
        ))

    def sort_key(code: str) -> tuple[int, str]:
        return (1 if code.startswith("E-") else 0, normalize(code))

    indexes: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    for error_id, code in enumerate(sorted(by_code, key=sort_key), start=1):
        interpretations = by_code[code]
        scopes = {item.pop("_scope") for item in interpretations}
        scope = next(iter(scopes)) if len(scopes) == 1 else "system"
        alias_values = {code}
        for interpretation in interpretations:
            alias_values.update(interpretation.pop("_aliases"))
        aliases = [
            {"alias_display": alias, "alias_normalized": normalize(alias).replace(" ", "")}
            for alias in sorted(alias_values)
        ]
        short_label = (
            interpretations[0]["title"]
            if len(interpretations) == 1
            else f"{len(interpretations)} interpretaciones documentadas"
        )
        tags = sorted({
            token.lower()
            for interpretation in interpretations
            for token in normalize(
                " ".join([interpretation["title"], interpretation["description"]])
            ).split()
            if len(token) >= 4
        })[:16]
        search_blob = " ".join(
            [code, short_label]
            + [alias["alias_display"] for alias in aliases]
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
            "indication_type": "remote_controller",
            "unit_scope": scope,
            "short_label": short_label,
            "interpretation_count": len(interpretations),
            "search_text": normalize(search_blob),
        }
        detail = {
            "id": error_id,
            "code_display": code,
            "code_normalized": index["code_normalized"],
            "indication_type": "remote_controller",
            "unit_scope": scope,
            "short_label": short_label,
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


def step(
    phase: str,
    number: int,
    instruction: str,
    expected: str | None = None,
    warning: str = "none",
) -> dict[str, Any]:
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
) -> dict[str, Any]:
    return {
        "interface_type": "mando cableado",
        "controller_family": family,
        "wire_count": wires,
        "polarity": polarity,
        "nominal_voltage": voltage,
        "terminals": terminals,
        "cable_colors": None,
        "cable_spec": "Cable de control separado del cableado de potencia; respetar la sección indicada por la instalación.",
        "startup_behavior": startup,
        "maximum_scope": "Una unidad o grupo compatible, según la familia.",
        "notes": notes,
    }


def option(value: str, label: str, effect: str, factory: bool = False) -> dict[str, Any]:
    return {
        "option_value": value,
        "option_label": label,
        "effect": effect,
        "is_factory": factory,
    }


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


def build_topics() -> list[dict[str, Any]]:
    topics: list[dict[str, Any]] = []

    def add_topic(
        topic_id: int,
        category_slug: str,
        slug: str,
        title: str,
        summary: str,
        variants: list[dict[str, Any]],
    ) -> None:
        category = CATEGORY_BY_SLUG[category_slug]
        topics.append({
            "id": topic_id,
            "brand_id": 3,
            "category_id": category["id"],
            "slug": slug,
            "title": title,
            "summary": summary,
            "active": 1,
            "category": category,
            "variants": variants,
        })

    add_topic(1, "diagnostic_access", "obtain-error-codes", "Cómo obtener códigos y subcódigos",
              "Métodos reconocibles desde mandos antiguos, inalámbricos, Madoka y display VRV.", [
        variant(
            1, 1, "Mando cableado clásico — modo de inspección",
            "Mando Daikin antiguo con botón INSPECTION/TEST; muestra código, modelo interior y exterior.",
            "Sky Air / cassette", "controller",
            "Acceder al código activo desde el mando cableado sin desmontar la unidad.",
            "Una pulsación entra en inspección; una pulsación adicional vuelve al modo normal. Mantener más de 4 segundos abre el modo de servicio.",
            [
                section("recognition", "Cómo reconocerlo", "Botón físico INSPECTION/TEST y pantalla segmentada.", True),
                section("modes", "Diferencia entre modos", "Una pulsación: inspección. Más de 4 segundos: servicio. Tras 10 segundos en Test Run se fuerza el termostato."),
            ],
            [
                step("procedure", 1, "Con la unidad en modo normal, pulse una vez INSPECTION/TEST."),
                step("procedure", 2, "Lea el código mostrado y, si procede, el código de modelo interior o exterior.", "La pantalla entra en modo de inspección."),
                step("procedure", 3, "Anote el código antes de borrar o reiniciar."),
                step("exit", 1, "Pulse de nuevo INSPECTION/TEST para regresar al modo normal."),
            ],
            "RZQS", "3-26", "Procedimiento de diagnóstico automático mediante mando cableado",
        ),
        variant(
            2, 1, "ARC452 — TIMER CANCEL y confirmación acústica",
            "Mando inalámbrico ARC452 con botón TIMER CANCEL.",
            "residencial / multisplit", "controller",
            "Buscar el código con la lista secuencial del mando.",
            "Mantener TIMER CANCEL 5 segundos muestra 00; la pulsación repetida recorre códigos hasta oír un pitido largo.",
            [
                section("beeps", "Significado de los pitidos", "Pitido corto o dos pitidos: código no coincidente. Pitido largo: código confirmado.", True),
                section("limits", "Si no aparece", "El método 1 no recorre todos los códigos; utilizar el método de dígitos TEMP/MODE."),
            ],
            [
                step("procedure", 1, "Mantenga TIMER CANCEL durante 5 segundos.", "Aparece 00 en la pantalla de temperatura."),
                step("procedure", 2, "Pulse TIMER CANCEL repetidamente para recorrer los códigos."),
                step("procedure", 3, "Deténgase cuando suene un pitido largo.", "El código mostrado coincide con la avería."),
                step("exit", 1, "Mantenga TIMER CANCEL 5 segundos o deje el mando sin tocar 60 segundos."),
            ],
            "MXL", "100", "ARC452 Series Remote Controller — Method 1",
        ),
        variant(
            3, 1, "ARC452 — búsqueda por dígito con TEMP y MODE",
            "Mando inalámbrico ARC452 con dos botones TEMP y botón MODE.",
            "residencial / multisplit", "controller",
            "Encontrar códigos que no aparecen en la lista corta de TIMER CANCEL.",
            "El mando separa dígito izquierdo y derecho y confirma cada coincidencia con pitidos.",
            [
                section("beeps", "Interpretación acústica", "Un pitido: no coincide el dígito izquierdo. Dos pitidos: coincide el izquierdo. Pitido largo: coinciden ambos.", True),
                section("timeout", "Salida automática", "Sin pulsaciones durante 60 segundos, el mando vuelve al modo normal."),
            ],
            [
                step("procedure", 1, "Pulse simultáneamente TEMP arriba, TEMP abajo y MODE.", "Parpadea el dígito izquierdo."),
                step("procedure", 2, "Cambie el dígito con TEMP hasta oír dos pitidos o un pitido largo."),
                step("procedure", 3, "Pulse MODE para hacer parpadear el dígito derecho."),
                step("procedure", 4, "Cambie el dígito con TEMP hasta oír el pitido largo.", "Los dos dígitos mostrados forman el código."),
                step("exit", 1, "Pulse MODE para salir y después ON/OFF dos veces para volver a la pantalla normal."),
            ],
            "MXL", "101", "ARC452 Series Remote Controller — Method 2", page_end="102",
        ),
        variant(
            4, 1, "BRC7E830 — Service Check por unidad y dos dígitos",
            "Mando inalámbrico de cassette con INSPECTION/TEST, UNIT, MODE, UP y DOWN.",
            "cassette FFQ", "controller",
            "Seleccionar una unidad del grupo y confirmar código principal/subcódigo mediante pitidos.",
            "El procedimiento selecciona primero la unidad, después el dígito superior y finalmente el inferior.",
            [
                section("beeps", "Confirmaciones", "Tres pitidos: seguir todos los pasos. Un pitido: continuar hasta confirmación. Pitido continuo: código completo confirmado.", True),
                section("upper", "Dígito superior", "Dos pitidos cortos indican que coincide el dígito superior; uno corto indica que no coincide."),
            ],
            [
                step("procedure", 1, "Pulse INSPECTION/TEST para entrar en inspección.", "Parpadea 0 en UNIT No."),
                step("procedure", 2, "Cambie UNIT No. con UP/DOWN hasta que el receptor emita el patrón acústico."),
                step("procedure", 3, "Pulse MODE para hacer parpadear el dígito superior."),
                step("procedure", 4, "Cambie el dígito superior con UP/DOWN hasta obtener dos pitidos o un pitido continuo."),
                step("procedure", 5, "Pulse MODE y cambie el dígito inferior hasta oír el pitido continuo.", "Código completo confirmado."),
                step("exit", 1, "Pulse MODE; sin pulsaciones, el mando sale automáticamente al minuto."),
            ],
            "MXL", "108", "BRC7E830 Service Check", page_end="111",
        ),
        variant(
            5, 1, "Madoka — abrir la pantalla de error",
            "Mando Madoka BRC1H52 con indicador de estado y pantalla de iconos.",
            "Sky Air / R32 compatible", "controller",
            "Mostrar el código y, en modo Supervisor, la dirección de la estancia supervisada.",
            "El acceso cambia según el modo visual Normal, Hotel 1 u Hotel 2.",
            [
                section("normal", "Modo de indicador Normal", "Con el icono de error visible en inicio, una pulsación abre la pantalla de error.", True),
                section("hotel", "Modos Hotel 1 y Hotel 2", "Mantener pulsado para abrir Información y volver a mantener para abrir Error."),
                section("supervisor", "Modo Supervisor", "Añade la dirección supervisada de la interior; ante varias fugas muestra la primera dirección que elevó el error."),
            ],
            [
                step("normal", 1, "Compruebe que el icono de error está visible en la pantalla de inicio."),
                step("normal", 2, "En modo Normal, pulse el botón indicado para abrir directamente el error."),
                step("hotel", 1, "En Hotel 1/2, mantenga pulsado hasta abrir Información."),
                step("hotel", 2, "Mantenga de nuevo el botón indicado.", "Aparece la pantalla de error."),
            ],
            "MADOKA", "126", "Error codes of the indoor unit", page_end="127",
        ),
    ])

    add_topic(2, "history_reset", "error-history-reset", "Historial y borrado de errores",
              "Consulta del histórico en mandos BRC y memoria de servicio.", [
        variant(
            6, 2, "BRC1E52 — historial de los 10 últimos errores",
            "Mando BRC1E52 con botones Cancel y Menu/Enter.",
            "Sky Air / cassette", "controller",
            "Consultar código, número de unidad y orden cronológico.",
            "El menú separa RC Error History e Indoor Unit Error History y conserva diez registros.",
            [
                section("capacity", "Capacidad del historial", "Muestra diez entradas, de la más reciente a la más antigua.", True),
                section("scope", "Dos historiales", "RC Error History y Indoor Unit Error History se consultan por separado."),
            ],
            [
                step("procedure", 1, "Mantenga Cancel durante 4 segundos en la pantalla básica.", "Aparece Service Settings."),
                step("procedure", 2, "Seleccione Error History y pulse Menu/Enter."),
                step("procedure", 3, "Seleccione RC Error History o Indoor Unit Error History."),
                step("procedure", 4, "Anote código y número de unidad; la entrada 01 es la más reciente."),
                step("exit", 1, "Pulse Cancel tres veces para volver a la pantalla básica."),
            ],
            "BRC1E", "19", "Checking procedure of Error History",
        ),
        variant(
            7, 2, "BRC1E52 — borrar el registro mostrado tras una reparación",
            "Pantalla Maintenance Information del mando BRC1E52.",
            "Sky Air", "controller",
            "Borrar el registro después de comprobar y corregir la causa.",
            "El borrado se realiza desde Maintenance Information manteniendo ON/OFF; no sustituye la reparación.",
            [
                section("warning", "Antes de borrar", "Anote el código y la unidad. El manual pide solucionar primero la causa.", True),
                section("normal", "Comprobación final", "Una pantalla de Maintenance Information sin registro de error indica estado normal tras la prueba."),
            ],
            [
                step("procedure", 1, "Abra Main menu > Maintenance Information."),
                step("procedure", 2, "Compruebe y anote el código y la unidad."),
                step("procedure", 3, "Repare la causa según el manual de la unidad."),
                step("erase", 1, "Mantenga ON/OFF durante 4 segundos en Maintenance Information.", "El registro mostrado se borra."),
            ],
            "BRC1E", "18", "Failure diagnosis method and error record erase",
        ),
        variant(
            8, 2, "Mando cableado clásico — memoria y código 00",
            "Mando antiguo con botón INSPECTION/TEST y acceso a Service Mode.",
            "Sky Air RZQS", "controller",
            "Consultar el historial y borrar la memoria del mando.",
            "El modo de servicio proporciona historial de códigos y datos de temperatura.",
            [
                section("service", "Modo de servicio", "Mantener INSPECTION/TEST más de 4 segundos abre datos de servicio, entre ellos historial y temperaturas.", True),
                section("erase", "Borrado", "La memoria se borra manteniendo ON/OFF durante al menos 5 segundos en inspección; aparece 00."),
            ],
            [
                step("procedure", 1, "Mantenga INSPECTION/TEST más de 4 segundos."),
                step("procedure", 2, "Seleccione el historial y anote el código almacenado."),
                step("erase", 1, "En el modo de inspección, mantenga ON/OFF al menos 5 segundos.", "La indicación 00 confirma memoria sin avería."),
                step("exit", 1, "Pulse INSPECTION/TEST para regresar al modo normal."),
            ],
            "RZQS", "3-33", "Indicación y borrado del historial de averías",
        ),
    ])

    add_topic(3, "controllers_buses", "wired-controllers", "Mandos cableados, bus y arranque",
              "Dos generaciones Daikin P1/P2 y su configuración principal/secundario.", [
        variant(
            9, 3, "BRC1E52 — P1/P2 y secuencia de arranque",
            "Mando rectangular BRC1E52 con Menu/Enter, Cancel y cuatro flechas.",
            "Sky Air / cassette", "controller",
            "Distinguir una espera normal de arranque de un fallo U5.",
            "Tras alimentar muestra “Checking the connection — Please stand by”; puede permanecer así hasta 90 segundos sin ser avería.",
            [
                section("startup", "Espera normal", "Hasta 90 segundos de “Please stand by” después de alimentar no se considera fallo.", True),
                section("fault", "Cuándo investigar", "Si no aparece la pantalla básica después del límite, cortar alimentación y revisar P1/P2, interior y mando."),
            ],
            [
                step("safety", 1, "Con la alimentación cortada, revise que el cableado interior/exterior esté terminado.", warning="warning"),
                step("procedure", 1, "Conecte el mando a P1/P2 según el esquema de la unidad."),
                step("procedure", 2, "Alimente el sistema y espere hasta 90 segundos.", "Aparece la pantalla básica."),
                step("check", 1, "Si continúa en espera o no hay pantalla, corte alimentación y revise cable, PCB interior y mando."),
            ],
            "BRC1E", "12", "Power-on and connection check",
            controller_profile=controller(
                "BRC1E52", "2", "P1/P2 sin polaridad en la red compatible", None, "P1/P2",
                "Checking the connection — Please stand by; hasta 90 s puede ser normal.",
                "No aplicar tensiones de otro tipo de bus.",
            ),
        ),
        variant(
            10, 3, "Madoka BRC1H52 — bus P1/P2 no polarizado",
            "Mando Madoka compacto con aro/indicador de estado; conexión P1/P2.",
            "Sky Air / R32 compatible", "controller",
            "Cablear y reconocer la inicialización automática del mando.",
            "El mando se alimenta desde la unidad interior y arranca automáticamente al conectar P1/P2.",
            [
                section("wiring", "Cableado", "P1 y P2 no tienen polaridad. Mantener el cable de control alejado del cableado de potencia.", True),
                section("startup", "Primera puesta en marcha", "Si es el primer y único mando, se designa automáticamente como principal Normal."),
            ],
            [
                step("safety", 1, "Corte alimentación antes de conectar el mando.", warning="warning"),
                step("procedure", 1, "Conecte P1/P2 del mando a P1/P2 de la unidad interior; no hay polaridad."),
                step("procedure", 2, "Separe el tendido del cableado de potencia para reducir ruido."),
                step("procedure", 3, "Alimente la interior.", "El mando arranca automáticamente y se designa principal si es el único."),
            ],
            "MADOKA", "40", "Connecting the electrical wiring and startup", page_end="43",
            controller_profile=controller(
                "Madoka BRC1H52", "2", "No polarizado", None, "P1/P2",
                "Se alimenta desde la interior y se inicia automáticamente.",
                "Solo se admite principal/secundario del mismo tipo.",
            ),
        ),
        variant(
            11, 3, "BRC1E52 — configurar principal y secundario al alimentar",
            "Dos BRC1E52 conectados a una unidad; durante la pantalla de comprobación.",
            "Sky Air / cassette", "controller",
            "Evitar U5 cuando se instalan dos mandos.",
            "La selección del secundario debe hacerse durante “Checking the connection”.",
            [
                section("fault", "Síntoma típico", "Si no se designa secundario, aparece U5 durante la comprobación de conexión.", True),
                section("timeout", "Comprobación", "Si la pantalla básica no aparece dos minutos después de “Sub RC”, cortar alimentación y revisar cableado."),
            ],
            [
                step("procedure", 1, "Alimente ambos mandos y espere a “Checking the connection”."),
                step("procedure", 2, "En el mando que será secundario, mantenga Operation mode selector 4 segundos.", "La pantalla cambia de Main RC a Sub RC."),
                step("check", 1, "Espere la pantalla básica."),
                step("check", 2, "Si tarda más de 2 minutos, corte alimentación y revise P1/P2."),
            ],
            "BRC1E", "12", "Main and sub remote controller designation",
        ),
        variant(
            12, 3, "Madoka — designar un segundo mando como esclavo",
            "Dos Madoka del mismo tipo conectados; el segundo muestra U5 o U8 al arrancar.",
            "Sky Air / R32 compatible", "controller",
            "Asignar el segundo mando sin confundir el error transitorio con una avería de unidad.",
            "El segundo mando se designa desde la pantalla U5/U8; después de reasignar es necesario reiniciar la alimentación.",
            [
                section("compatibility", "Compatibilidad", "Principal y esclavo deben ser del mismo tipo. Con adaptador digital BRP7A5* no se permite un segundo mando.", True),
                section("timeout", "Pantalla de inicio", "Si el esclavo no muestra inicio dos minutos después de designarlo, cortar alimentación y revisar cableado."),
            ],
            [
                step("procedure", 1, "Con un principal ya conectado, conecte el segundo mando."),
                step("procedure", 2, "Espere a que aparezca U5 o U8."),
                step("procedure", 3, "Mantenga pulsado el botón indicado hasta que aparezca 2.", "El mando queda designado como esclavo."),
                step("restart", 1, "Reinicie la alimentación después de reasignar."),
            ],
            "MADOKA", "43", "Controller designation", page_end="44",
        ),
    ])

    add_topic(4, "service_modes", "forced-operation-pump-down", "Marcha forzada y recogida de refrigerante",
              "Variantes separadas para Sky Air antiguo, Alpha y multisplit.", [
        variant(
            13, 4, "RZQS serie B — funcionamiento de emergencia",
            "Interior y exterior con interruptor SS1 Emergency; exterior con selector COOL/HEAT.",
            "Sky Air RZQS", "system",
            "Hacer funcionar el sistema cuando el mando falla, manteniendo las protecciones documentadas.",
            "No regula temperatura: en frío funciona 20 min y para 10; en calor fuerza 3 min de desescarche cada hora.",
            [
                section("active", "Elementos activos", "Interior: ventilador y bomba. Exterior: compresor y ventiladores.", True),
                section("safety", "Protecciones", "Si actúa un dispositivo de seguridad, todos los actuadores se apagan."),
                section("display", "Indicación", "El mando muestra 88 mientras la interior está en emergencia."),
            ],
            [
                step("safety", 1, "Corte la alimentación antes de mover cualquier SS1.", warning="danger"),
                step("procedure", 1, "Ponga SS1 de la PCB interior en Emergency."),
                step("procedure", 2, "Ponga SS1 de la PCB exterior en Emergency."),
                step("procedure", 3, "Seleccione COOL o HEAT en el selector exterior."),
                step("procedure", 4, "Restablezca la alimentación.", "Arrancan los actuadores de emergencia sin regulación de ambiente."),
                step("exit", 1, "Para finalizar, corte alimentación y devuelva ambos SS1 a Normal."),
            ],
            "RZQS", "2-6", "Modo de funcionamiento forzado", page_end="2-7", refrigerant="R410A",
        ),
        variant(
            14, 4, "RZQS serie B — Pump Down con BS1",
            "PCB exterior con pulsador BS1 identificado como descongelación forzada / bombeo de vacío.",
            "Sky Air RZQS", "outdoor",
            "Recoger el refrigerante en la exterior antes de mover o retirar la instalación.",
            "BS1 inicia compresor y ventilador; la secuencia dura de 3 a 5 minutos.",
            [
                section("warning", "Riesgo", "Los ventiladores pueden arrancar automáticamente al pulsar BS1.", True),
                section("restart", "Después de finalizar", "El mando puede quedar en blanco o mostrar U4. Cortar alimentación antes de intentar arrancar de nuevo."),
            ],
            [
                step("safety", 1, "Confirme que no hay fuga que permita entrada de aire y que ambas válvulas están abiertas.", warning="danger"),
                step("procedure", 1, "Inicie Solo ventilador desde el mando."),
                step("procedure", 2, "Pulse BS1 en la PCB exterior.", "Arrancan compresor y ventilador exterior."),
                step("procedure", 3, "Tras 3–5 minutos, cierre primero la válvula de líquido y después la de gas."),
                step("exit", 1, "Corte alimentación; antes de reutilizar el equipo vuelva a abrir ambas válvulas."),
            ],
            "RZQS", "2-18", "Funcionamiento de bombeo de vacío", refrigerant="R410A",
        ),
        variant(
            15, 4, "RZAG-M — Pump Down automático con BS2",
            "Sky Air Alpha, PCB exterior con BS2; unidades RZAG71~140M.",
            "Sky Air Alpha", "outdoor",
            "Recoger refrigerante con parada automática por baja presión.",
            "BS2 mantenido 8 segundos inicia compresor y ventilador; líquido se cierra a los 2 min y gas al detenerse.",
            [
                section("leak", "No usar si existe una fuga", "La entrada de aire al compresor puede causar combustión o explosión; utilizar recuperación independiente.", True),
                section("limit", "Longitud de tubería", "No usar si la longitud total supera la longitud sin carga; puede quedar refrigerante en el circuito."),
                section("restart", "Rearme", "Después del proceso el mando puede mostrar una indicación y la interior seguir; cortar y restablecer alimentación para reiniciar."),
            ],
            [
                step("safety", 1, "Confirme que no hay fuga y que el procedimiento automático es aplicable.", warning="danger"),
                step("procedure", 1, "Alimente y confirme abiertas las válvulas de gas y líquido."),
                step("procedure", 2, "Mantenga BS2 al menos 8 segundos.", "Arrancan compresor y ventilador exterior; el interior puede arrancar."),
                step("procedure", 3, "Aproximadamente 2 minutos después del arranque, cierre la válvula de líquido."),
                step("procedure", 4, "Cuando el compresor se detenga entre 2 y 5 minutos, cierre gas antes de 3 minutos."),
                step("exit", 1, "Desconecte alimentación; antes de reutilizar vuelva a abrir ambas válvulas."),
            ],
            "RZAG", "31", "Bombeo de vacío", page_end="32", refrigerant="R32",
        ),
        variant(
            16, 4, "2MXL/3MXL-Q — refrigeración forzada y Pump Down",
            "PCB monitor exterior con SW1, SW2, SW5 y SW6.",
            "multisplit 2/3MXL-Q", "outdoor",
            "Recoger refrigerante de una instalación multisplit mediante refrigeración forzada.",
            "SW1 arranca a 30 Hz; termina al volver a pulsarlo o automáticamente a los 60 minutos.",
            [
                section("sequence", "Cierre de válvulas", "Después de 5–10 min cierre líquido; 2–3 min después cierre gas y detenga la refrigeración.", True),
                section("board", "Preparación de placa", "Con alimentación cortada, todos los SW5/SW6 en OFF y SW2 en COOL."),
            ],
            [
                step("safety", 1, "Corte alimentación antes de manipular SW2, SW5 o SW6.", warning="danger"),
                step("procedure", 1, "Retire la tapa, deje SW5/SW6 en OFF y ponga SW2 en COOL."),
                step("procedure", 2, "Cierre la tapa, alimente y espere el retardo de 3 minutos."),
                step("procedure", 3, "Pulse SW1.", "Refrigeración forzada a 30 Hz."),
                step("procedure", 4, "Tras 5–10 minutos cierre líquido; 2–3 minutos después cierre gas."),
                step("exit", 1, "Pulse SW1 de nuevo para detener."),
            ],
            "MXL", "176", "Pump Down Operation",
        ),
    ])

    add_topic(5, "commissioning", "test-operation", "Prueba de funcionamiento",
              "Test Run desde BRC1E, Madoka y mandos residenciales.", [
        variant(
            17, 5, "BRC1E52 — Test Operation en refrigeración",
            "Mando con Service Settings y opción Test Operation.",
            "Sky Air / cassette", "system",
            "Comprobar funcionamiento y aletas después de instalación o reparación.",
            "Requiere 6 horas de alimentación previa y válvulas abiertas; la prueba se comprueba durante 3 minutos.",
            [
                section("prerequisites", "Antes de empezar", "Cableado, tuberías y drenaje terminados; tapas cerradas; alimentación al menos 6 horas; gas y líquido abiertos.", True),
                section("after", "Comprobación final", "Revisar Maintenance Information y resolver cualquier registro de error."),
            ],
            [
                step("procedure", 1, "Seleccione refrigeración en la pantalla básica."),
                step("procedure", 2, "Mantenga Cancel 4 segundos y seleccione Test Operation."),
                step("procedure", 3, "Pulse ON/OFF dentro de 10 segundos.", "Comienza la prueba."),
                step("procedure", 4, "Compruebe el funcionamiento durante 3 minutos y verifique la dirección de aire."),
                step("exit", 1, "Vuelva a Service Settings > Test Operation para terminar."),
                step("check", 1, "Revise Maintenance Information y el historial."),
            ],
            "BRC1E", "16", "Test operation method", page_end="18",
        ),
        variant(
            18, 5, "RZAG-M — Test Run y detección de válvulas cerradas",
            "Sky Air Alpha con BRC1E52; exterior RZAG71~140M.",
            "Sky Air Alpha", "system",
            "Validar cableado, refrigerante, drenaje y apertura de válvulas.",
            "Aunque el mando se ponga en calor, la unidad empieza 2–3 minutos en frío para detectar válvulas cerradas.",
            [
                section("normal", "Comportamiento normal inicial", "Puede indicar calefacción y funcionar 2–3 min en refrigeración antes de pasar a calor.", True),
                section("codes", "Códigos durante prueba", "E3, E4 o L8 pueden aparecer con válvulas de cierre cerradas."),
            ],
            [
                step("safety", 1, "Alimente al menos 6 horas y confirme ambas válvulas abiertas.", warning="warning"),
                step("procedure", 1, "Seleccione solo refrigeración en el mando."),
                step("procedure", 2, "Mantenga Cancel 4 segundos y seleccione Operación Test."),
                step("procedure", 3, "Pulse ON/OFF dentro de 10 segundos."),
                step("procedure", 4, "Compruebe durante 3 minutos y verifique aletas/flujo."),
                step("exit", 1, "Entre de nuevo en Operación Test para volver a funcionamiento normal."),
            ],
            "RZAG", "28", "Cómo realizar una prueba de funcionamiento", page_end="30",
        ),
        variant(
            19, 5, "Madoka Assistant — Test Operation",
            "Mando BRC1H52 emparejado con la aplicación Madoka Assistant.",
            "Sky Air", "system",
            "Activar la prueba, recorrer posiciones de aleta y revisar errores.",
            "La prueba finaliza automáticamente a los 30 minutos y solo está disponible para interiores Sky Air.",
            [
                section("prerequisites", "Antes de activar", "Tubería frigorífica, drenaje y cableado terminados; alimentación 6 horas; válvulas abiertas.", True),
                section("duration", "Final automático", "Test Operation termina a los 30 minutos aunque no se pulse Stop."),
            ],
            [
                step("procedure", 1, "Abra Madoka Assistant y seleccione el mando/unidades."),
                step("procedure", 2, "Ponga refrigeración y abra Unit settings > Maintenance > Test operation."),
                step("procedure", 3, "Pulse Start test operation.", "La operación normal queda bloqueada durante el test."),
                step("procedure", 4, "Recorra las cinco posiciones fijas de aleta y compruebe el movimiento."),
                step("exit", 1, "Pulse Stop test operation."),
                step("check", 1, "Revise el historial y repita después de corregir cualquier error."),
            ],
            "MADOKA", "121", "Test operation with Madoka Assistant", page_end="122",
        ),
        variant(
            20, 5, "ARC452 / ARC466 — prueba residencial",
            "Mando inalámbrico residencial con TEMP y MODE.",
            "residencial / multisplit", "system",
            "Forzar una prueba cuando la temperatura ambiente impediría la demanda normal.",
            "La prueba termina automáticamente a los 30 minutos y vuelve al modo normal.",
            [
                section("setpoints", "Consignas de comprobación", "Frío: mínimo programable 18 °C. Calor: máximo 30 °C.", True),
                section("protection", "Retardo", "Después de parar, el sistema no arranca durante 3 minutos."),
            ],
            [
                step("procedure", 1, "Encienda el sistema."),
                step("procedure", 2, "ARC452: pulse ambos TEMP y MODE; pulse MODE dos veces hasta mostrar T."),
                step("procedure", 3, "ARC466: pulse el centro de TEMP y MODE, seleccione T y confirme con MODE."),
                step("procedure", 4, "Seleccione frío o calor y compruebe funcionamiento."),
                step("exit", 1, "Pulse ON/OFF para salir o espere 30 minutos."),
            ],
            "MXL", "179", "Trial Operation — ARC452/ARC466", page_end="180",
        ),
    ])

    add_topic(6, "drainage_overflow", "cassette-drainage-control", "Cassette: bomba, boya y desbordamiento",
              "Secuencia exacta de bomba y diferencias entre A3 y AF.", [
        variant(
            21, 6, "Control normal y actuación de boya en refrigeración",
            "Cassette FCQ/FFQ con bomba M1P y boya 33H/S1L conectada a X15A.",
            "cassette", "indoor",
            "Entender qué hace la máquina antes de sustituir bomba, boya o placa.",
            "La bomba arranca con el compresor y continúa 5 minutos tras pararlo. Ante nivel alto fuerza termostato OFF.",
            [
                section("normal", "Funcionamiento normal", "Bomba ON al arrancar compresor; OFF cinco minutos después de que el compresor se detenga.", True),
                section("float", "Boya activa", "Termostato forzado OFF y bomba durante al menos 10 minutos, aunque el nivel se recupere antes."),
                section("recovery", "Recuperación rápida", "Si la boya vuelve a normal antes de 80 segundos, el frío puede reiniciar dentro del periodo de recuperación de 10 minutos."),
            ],
            [
                step("check", 1, "Observe si la bomba arranca simultáneamente con el compresor."),
                step("check", 2, "Al parar el compresor, confirme que la bomba mantiene 5 minutos de residual."),
                step("check", 3, "Eleve la boya de forma controlada.", "El termostato se fuerza OFF y la bomba sigue al menos 10 minutos."),
                step("check", 4, "Libere la boya antes de 80 segundos.", "El frío puede recuperarse dentro de la ventana documentada."),
            ],
            "FCQ", "2-17", "Drain Pump Control", page_end="2-18",
        ),
        variant(
            22, 6, "A3 — diagnóstico de nivel alto",
            "Cassette o conductos con bomba conectada a X25A y boya/puente en X15A.",
            "cassette / conductos", "indoor",
            "Separar obstrucción, bomba, boya, puente X15A y PCB.",
            "A3 se genera cuando el agua alcanza el límite superior y la boya cambia a OFF.",
            [
                section("causes", "Causas del manual", "Bomba, tubería mal ejecutada u obstruida, boya, PCB o puente X15A.", True),
                section("voltage", "Salida de bomba", "El flujo de diagnóstico comprueba la salida X25A en modo de emergencia; la tensión depende de la familia y debe confirmarse en su esquema."),
            ],
            [
                step("safety", 1, "Corte alimentación antes de desconectar X15A o X25A.", warning="danger"),
                step("check", 1, "Compruebe si el nivel de agua es realmente alto y si el desagüe está obstruido."),
                step("check", 2, "Compruebe que bomba y boya están conectadas."),
                step("check", 3, "Revise continuidad de la boya o del puente X15A según equipamiento."),
                step("check", 4, "Compruebe la salida X25A siguiendo el esquema de la unidad."),
                step("check", 5, "Solo después de descartar drenaje, bomba, boya y cableado, continúe con la PCB."),
            ],
            "FCQ", "3-33", "Malfunction of Drain Water Level System (A3)", page_end="3-34",
        ),
        variant(
            23, 6, "AF — boya cambia con el compresor parado",
            "Cassette con posibilidad de retorno de agua o kit de elevación.",
            "cassette / conductos", "indoor",
            "Detectar boya pegada, sifón incorrecto o agua que retorna después de parar la bomba.",
            "AF aparece si la boya pasa de ON a OFF mientras el compresor está parado.",
            [
                section("difference", "Diferencia frente a A3", "AF está ligado a una activación con compresor OFF; A3 corresponde a nivel alto durante el control normal.", True),
                section("hydraulic", "Puntos hidráulicos", "Altura de elevación, longitud horizontal, sifón, retorno y caudal residual después de parar."),
            ],
            [
                step("check", 1, "Observe si el agua retorna a la bandeja cuando la bomba se detiene."),
                step("check", 2, "Compruebe altura de elevación, longitud y sifón contra la instalación."),
                step("check", 3, "Revise obstrucción de desagüe y de la bomba."),
                step("check", 4, "Compruebe que la boya se mueve libremente y cambia eléctricamente."),
                step("check", 5, "Si el sistema hidráulico y la boya son correctos, continúe con la PCB."),
            ],
            "FCQ", "3-35", "Malfunctioning Drain System (AF)",
        ),
    ])

    add_topic(7, "configuration", "controller-field-settings", "Programación desde mandos",
              "Acceso, guardado y ejemplos de ajustes de campo BRC1E y Madoka.", [
        variant(
            24, 7, "BRC1E52 — acceso y guardado de Field Settings",
            "Mando BRC1E52 con Cancel, Menu/Enter y flechas.",
            "Sky Air / cassette", "controller",
            "Cambiar modo, FIRST CODE y SECOND CODE sin confundir ajuste de grupo e individual.",
            "Los modos 20/21/22/23/25 se usan para ajustes individuales; el mando reinicializa al guardar.",
            [
                section("group", "Grupo o unidad", "En modo individual se selecciona Indoor unit No.; “-” indica que la función no existe.", True),
                section("restart", "Después de guardar", "Aparece “Checking the connection — Please stand by” durante la reinicialización."),
            ],
            [
                step("procedure", 1, "Mantenga Cancel 4 segundos y seleccione Field Settings."),
                step("procedure", 2, "Seleccione Mode No. y, si es individual, Indoor unit No."),
                step("procedure", 3, "Seleccione FIRST CODE y el SECOND CODE deseado."),
                step("save", 1, "Confirme Save the settings? > Yes."),
                step("exit", 1, "Pulse Cancel dos veces y espere la reinicialización."),
            ],
            "BRC1E", "13", "Field settings", page_end="15",
            parameters=[
                parameter("10(20)-2", "Sensor del termostato en el mando",
                          "Selecciona si se usa el termistor del mando.",
                          [option("01", "Usar", "Usa la sonda del mando", True), option("02", "No usar", "Usa la lógica de la unidad interior")],
                          "01"),
                parameter("11(21)-0", "Número de interiores en operación simultánea",
                          "Pair, Twin, Triple o Double twin.",
                          [option("01", "Pair", "Una interior", True), option("02", "Twin", "Dos interiores"),
                           option("03", "Triple", "Tres interiores"), option("04", "Double twin", "Cuatro interiores")],
                          "01"),
                parameter("13(23)-6", "Presión estática exterior",
                          "Adapta conductos a resistencia conectada.",
                          [option("01", "Normal", "Presión estándar", True), option("02", "Alta", "Alta presión estática"),
                           option("03", "Baja", "Baja presión estática")], "01"),
            ],
        ),
        variant(
            25, 7, "Madoka — entrar en Installer Menu",
            "Mando BRC1H52; acceso desde Information mediante dos teclas simultáneas.",
            "Sky Air / R32 compatible", "controller",
            "Acceder a ajustes de pantalla, indicador, unidad interior y mando.",
            "El menú incluye Indoor unit field settings, Remote controller field settings, direcciones, entrada externa, Force fan ON y maestro frío/calor.",
            [
                section("available", "Bloques disponibles", "Pantalla, indicador de estado, ajustes de campo, direcciones, entrada externa, ventilador forzado, maestro frío/calor y prueba de alarma de fuga.", True),
                section("scope", "No universal", "La presencia de opciones depende de la unidad y del modo del mando."),
            ],
            [
                step("procedure", 1, "Desde inicio, mantenga pulsado hasta abrir Information."),
                step("procedure", 2, "Desde Information, mantenga simultáneamente las dos teclas indicadas."),
                step("procedure", 3, "Seleccione el grupo de ajustes requerido.", "Está dentro de Installer Menu."),
                step("exit", 1, "Salga al inicio y compruebe que la unidad acepta el ajuste."),
            ],
            "MADOKA", "68", "Installer menu",
        ),
    ])

    add_topic(8, "commissioning", "multisplit-wiring-check", "Multisplit: comprobación automática de cableado",
              "Función SW3 que relaciona cada tubería con la habitación conectada.", [
        variant(
            26, 8, "2MXL/3MXL-Q — Wiring Error Check con SW3",
            "PCB monitor exterior con SW3 y LED 1–5.",
            "multisplit 2/3MXL-Q", "system",
            "Detectar y autocorregir cruces entre cableado de habitación y puerto frigorífico.",
            "La prueba dura 15–20 minutos y enfría sucesivamente cada intercambiador interior.",
            [
                section("not_available", "Cuándo no funciona", "Durante retardo de 3 minutos, exterior <5 °C, interior averiada o fallo de transmisión en todas las habitaciones.", True),
                section("results", "Lectura de LED", "Secuencia: autocorrección completada. Todos parpadeando: imposible. Un LED fijo: parada de emergencia."),
                section("limits", "Límite", "No corrige líquido y gas emparejados de forma incorrecta."),
            ],
            [
                step("procedure", 1, "Confirme que no existe ningún caso de inhibición y pulse SW3."),
                step("procedure", 2, "Espere 15–20 minutos sin interrumpir el proceso."),
                step("check", 1, "Lea los LED: secuencia, todos parpadeando o alguno fijo."),
                step("check", 2, "Relacione el primer LED que parpadea con Port A y el segundo con Port B."),
                step("exit", 1, "Para cancelar, vuelva a pulsar SW3; la memoria vuelve a la correspondencia inicial."),
                step("after", 1, "Después de sustituir la PCB exterior, ejecute esta función antes de fijar la habitación prioritaria."),
            ],
            "MXL", "177", "Wiring Error Check Function", page_end="178",
        ),
    ])

    add_topic(9, "vrf_network", "vrv-subcodes-operation", "VRV IV: subcódigos y alcance",
              "Uso del subcódigo para saber qué exterior, inverter, ventilador, sonda o válvula está implicado.", [
        variant(
            27, 9, "VRV IV — leer siempre código y subcódigo",
            "Display de la PCB exterior que presenta código principal y número de subcódigo.",
            "VRV IV", "system",
            "Evitar diagnósticos genéricos como “E9 = válvula” sin identificar Y1E, Y2E o Y3E.",
            "Los subcódigos sitúan maestra/esclavas y, en algunos códigos, el componente exacto.",
            [
                section("examples", "Ejemplos", "E9-01/05/08: Y2E X21A. E9-04/07/10: Y1E X23A. LC-14: INV1; LC-19: FAN1; LC-24: FAN2; LC-30: INV2.", True),
                section("effect", "Alcance", "El subcódigo puede limitar el alcance a una exterior o identificar una condición de todo el sistema."),
            ],
            [
                step("procedure", 1, "Anote el código principal completo."),
                step("procedure", 2, "Anote el subcódigo de dos dígitos; no lo omita."),
                step("procedure", 3, "Busque la interpretación exacta en la ficha del código."),
                step("procedure", 4, "Identifique maestra/esclava o módulo antes de medir."),
                step("check", 1, "Consulte también errores de interiores cuando la tabla lo ordene."),
            ],
            "VRV4", "55", "Tablas de códigos y subcódigos", page_end="58",
        ),
        variant(
            28, 9, "VRV IV — estados de Auto Charge y Leak Detection",
            "Display exterior durante carga automática o comprobación de fugas.",
            "VRV IV", "system",
            "Distinguir P2/P8 de los estados informativos PE/P9 y de las inhibiciones E-1/E-2.",
            "PE y P9 describen avance/finalización; E-1/E-2 indican que no se cumplen condiciones para Leak Detection.",
            [
                section("charge", "Carga automática", "P2: aspiración baja. P8: antihielo interior. PE: casi finalizada. P9: completada.", True),
                section("leak", "Detección de fugas", "E-1: sistema no preparado. E-2: interiores fuera del rango de temperatura."),
            ],
            [
                step("procedure", 1, "Anote el estado completo mostrado."),
                step("check", 1, "Con P2, revise válvulas, presión y condiciones de carga."),
                step("check", 2, "Con P8, revise temperatura y caudal de las interiores."),
                step("check", 3, "Con E-1/E-2, corrija las condiciones previas antes de repetir."),
                step("exit", 1, "Con P9, finalice el procedimiento siguiendo la guía de instalación."),
            ],
            "VRV4", "58", "Auto Charge and Leak Detection status codes",
        ),
    ])

    add_topic(10, "component_checks", "thermistors", "Comprobación de sondas NTC",
              "Curvas de sondas estándar, módulo y descarga de la familia RZQS.", [
        variant(
            29, 10, "Sondas de aire y batería — curva RZQS",
            "Sondas R1T/R2T/R4T de la familia RZQS documentada.",
            "Sky Air RZQS", "general",
            "Comparar la resistencia medida con la temperatura real.",
            "Curva de alta resistencia: 20,00 kΩ a 25 °C en la familia documentada.",
            [
                section("points", "Puntos útiles", "0 °C: 65,84 kΩ; 20 °C: 25,01 kΩ; 25 °C: 20,00 kΩ; 40 °C: 10,63 kΩ; 60 °C: 4,96 kΩ.", True),
                section("warning", "No extrapolar", "Una sonda Daikin con el mismo código puede usar otra curva en otra familia."),
            ],
            [
                step("safety", 1, "Corte alimentación y desconecte la sonda de la PCB.", warning="warning"),
                step("check", 1, "Mida la temperatura real junto a la sonda."),
                step("check", 2, "Mida resistencia sin tensión."),
                step("check", 3, "Compare con la curva y observe continuidad al calentar/enfriar."),
                step("check", 4, "Si la sonda es correcta, revise cableado y entrada de PCB."),
            ],
            "RZQS", "3-107", "Thermistor resistance check",
        ),
        variant(
            30, 10, "Sonda de descarga — curva de alta temperatura",
            "Sonda R3T de tubo de descarga en la familia RZQS.",
            "Sky Air RZQS", "outdoor",
            "Comprobar J3 y diferenciar sonda defectuosa de temperatura realmente alta.",
            "La resistencia cae desde 806,5 kΩ a 0 °C hasta 13,1 kΩ a 100 °C y 1,5 kΩ a 180 °C.",
            [
                section("points", "Puntos útiles", "40 °C: 118,7 kΩ; 60 °C: 52,8 kΩ; 80 °C: 25,4 kΩ; 100 °C: 13,1 kΩ; 120 °C: 7,1 kΩ.", True),
                section("contact", "Montaje", "Comprobar fijación y contacto térmico antes de declarar la sonda defectuosa."),
            ],
            [
                step("safety", 1, "Espere a que la tubería sea segura y corte alimentación.", warning="danger"),
                step("check", 1, "Desconecte R3T y mida resistencia."),
                step("check", 2, "Mida la temperatura de la tubería con instrumento fiable."),
                step("check", 3, "Compare con la curva de alta temperatura."),
                step("check", 4, "Revise conector, cable y contacto térmico."),
            ],
            "RZQS", "3-108", "Discharge pipe thermistor resistance",
        ),
    ])

    add_topic(11, "technical_values", "thermistor-reference-tables", "Tablas rápidas de resistencia",
              "Valores clave para las tres curvas RZQS documentadas.", [
        variant(
            31, 11, "Resumen de curvas RZQS: estándar, módulo y descarga",
            "Solo para la familia cuyas sondas aparecen en ESiES06-07.",
            "Sky Air RZQS", "general",
            "Localizar rápidamente el orden de magnitud antes de abrir la ficha de error.",
            "Estándar: 20,00 kΩ a 25 °C. Módulo R5T: 19,56 kΩ a 25 °C. Descarga: 13,1 kΩ a 100 °C.",
            [
                section("standard", "Curva estándar", "0 °C 65,84 kΩ; 25 °C 20,00 kΩ; 50 °C 7,18 kΩ.", True),
                section("module", "Curva del módulo R5T", "0 °C 64,17 kΩ; 25 °C 19,56 kΩ; 50 °C 7,04 kΩ."),
                section("discharge", "Curva de descarga", "60 °C 52,8 kΩ; 100 °C 13,1 kΩ; 140 °C 4,1 kΩ."),
            ],
            [
                step("check", 1, "Identifique primero qué sonda y curva indica el manual de la unidad."),
                step("check", 2, "Mida temperatura y resistencia en el mismo momento."),
                step("check", 3, "Use la tabla como referencia inicial, no como curva universal Daikin."),
            ],
            "RZQS", "3-107", "Thermistor resistance values", page_end="3-108",
        ),
    ])

    add_topic(12, "normal_states", "normal-protection-behavior", "Estados normales que pueden parecer avería",
              "Retardos y secuencias documentadas durante arranque, prueba y protección.", [
        variant(
            32, 12, "Sky Air: espera, precalentamiento y arranque inicial",
            "Unidades Sky Air con calentador de cárter e interfaz BRC.",
            "Sky Air", "system",
            "Evitar confundir esperas normales con una avería.",
            "Daikin exige al menos 6 horas de alimentación antes de la prueba; en RZAG el inicio puede permanecer 2–3 minutos en frío aunque se haya seleccionado calor.",
            [
                section("controller", "Mando", "BRC1E puede mostrar “Please stand by” hasta 90 segundos sin que sea fallo.", True),
                section("compressor", "Compresor", "El calentador de cárter necesita 6 horas antes de puesta en marcha o Test Run."),
                section("mode", "Cambio a calefacción", "Durante una prueba, RZAG puede iniciar 2–3 minutos en frío para detectar válvulas cerradas."),
            ],
            [
                step("check", 1, "Compruebe cuánto tiempo lleva alimentado el equipo."),
                step("check", 2, "Espere 90 segundos antes de declarar fallo de comunicación en el arranque del BRC1E."),
                step("check", 3, "Durante Test Run en calor, observe si cambia automáticamente después de 2–3 minutos."),
                step("check", 4, "Si excede los tiempos o aparece código, continúe con la ficha correspondiente."),
            ],
            "RZAG", "28", "Precauciones durante la puesta en marcha",
        ),
    ])

    add_topic(13, "system_architecture", "family-recognition", "Cómo reconocer la familia técnica",
              "Pistas visibles para no aplicar un procedimiento incompatible.", [
        variant(
            33, 13, "Mapa de familias Daikin incluidas en Referencia V2",
            "Seleccione por placa, mando y tipo de sistema; el modelo se conserva solo como trazabilidad.",
            "Sky Air / cassette / multisplit / VRV", "general",
            "Elegir la variante que físicamente coincide con la máquina.",
            "La base incluye RZQS Sky Air antiguo, RZAG Alpha, cassette FCQ/FFQ, 2MXL/3MXL-Q, VRV IV, BRC1E y Madoka.",
            [
                section("skyair_old", "Sky Air RZQS", "PCB con BS1 de descongelación/pump down y SS1 de emergencia.", True),
                section("skyair_new", "Sky Air RZAG", "PCB con BS2 para Pump Down automático y guía R32."),
                section("multi", "Multisplit 2MXL/3MXL", "Monitor con SW1, SW2, SW3, SW5/SW6 y LED por habitaciones."),
                section("vrv", "VRV IV", "Código principal más subcódigo que identifica exterior, inverter, ventilador, sonda o EEV."),
            ],
            [
                step("procedure", 1, "Identifique tipo de sistema: individual, simultáneo, multisplit o VRV."),
                step("procedure", 2, "Observe nombre de pulsadores, DIP, cantidad de LED y tipo de mando."),
                step("procedure", 3, "Abra la variante que coincida con esos rasgos."),
                step("check", 1, "Confirme la fuente/familia antes de mover un switch o medir un conector."),
            ],
            "RZQS", "1-32", "Diagrama de cableado y elementos de placa",
        ),
    ])

    add_topic(14, "errors", "error-interpretation-rules", "Cómo usar códigos repetidos",
              "Reglas para elegir entre distintas interpretaciones de un mismo código Daikin.", [
        variant(
            34, 14, "Código principal repetido: elegir por familia y subcódigo",
            "La búsqueda devuelve todas las interpretaciones; no selecciona automáticamente una.",
            "todas las familias", "general",
            "Evitar aplicar la comprobación de un Sky Air a un multisplit o VRV solo porque coincide el código.",
            "E3, E4, E9, F3, U2, U4, UA y otros códigos tienen interpretaciones o componentes diferentes según familia y subcódigo.",
            [
                section("order", "Orden recomendado", "1) tipo de sistema; 2) tipo de mando/placa; 3) código; 4) subcódigo; 5) comportamiento de la máquina.", True),
                section("vrv", "En VRV", "El subcódigo es imprescindible: por ejemplo E9 separa Y1E, Y2E y Y3E."),
                section("scope", "Efecto", "La ficha indica si afecta a una unidad, un módulo o a la puesta en marcha completa cuando el manual lo documenta."),
            ],
            [
                step("procedure", 1, "Busque el código principal."),
                step("procedure", 2, "Compare “Cómo reconocerla” y el tipo de sistema."),
                step("procedure", 3, "Si existe, introduzca o localice el subcódigo completo."),
                step("procedure", 4, "Abra causas y comprobaciones solo de la variante compatible."),
            ],
            "VRV4", "55", "Estructura de código y subcódigo", page_end="58",
        ),
    ])

    return topics


def build_search(
    topics: list[dict[str, Any]],
    error_indexes: list[dict[str, Any]],
    error_details: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    def with_synonyms(value: str) -> str:
        normalized = normalize(value)
        additions = []
        if "BOYA" in normalized:
            additions.append("flotador float switch")
        if "BOMBEO DE VACIO" in normalized or "RECOGIDA DE REFRIGERANTE" in normalized:
            additions.append("pump down")
        if "MANDO" in normalized:
            additions.append("control remoto remote controller")
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
                item["title"],
                item.get("recognition") or "",
                item.get("purpose") or "",
                item.get("summary") or "",
                " ".join(row.get("body") or "" for row in item.get("sections", [])),
                " ".join(
                    " ".join([row.get("instruction") or "", row.get("expected_result") or ""])
                    for row in item.get("steps", [])
                ),
                parameter_text,
                controller_text,
                category["name"],
                topic["title"],
            ])
            entries.append({
                "type": "variant",
                "id": item["id"],
                "topic_id": topic["id"],
                "category_slug": category["slug"],
                "category": category["name"],
                "title": item["title"],
                "summary": item["summary"],
                "haystack": normalize(with_synonyms(body)),
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
            "haystack": normalize(with_synonyms(body)),
        })
    return entries


def main() -> int:
    brand_root = BRAND_DIR.resolve()
    expected_root = (ROOT / "data" / "brands" / "daikin").resolve()
    if brand_root != expected_root:
        raise RuntimeError(f"Destino inesperado: {brand_root}")

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

    source_rows = []
    for source_id, (key, row) in enumerate(SOURCES.items(), start=1):
        source_rows.append({
            "id": source_id,
            "title": row["title"],
            "document_ref": row["document_ref"],
            "publication_date": row["publication_date"],
            "language": row["language"],
            "document_type": row["document_type"],
            "source_url": row["source_url"],
            "status": "reviewed",
            "notes": row["notes"],
        })
    write_json(WEB_DIR / "sources.json", source_rows)

    coverage_notes = {
        "errors": "Códigos Sky Air, cassette, multisplit y VRV con interpretaciones separadas por familia y subcódigo.",
        "diagnostic_access": "Mando cableado clásico, ARC452 por dos métodos, BRC7E830 y Madoka.",
        "history_reset": "Historial BRC1E de diez registros, borrado y memoria clásica.",
        "service_modes": "Emergencia, Pump Down en tres generaciones y condiciones de protección.",
        "configuration": "Field Settings BRC1E y menú de instalador Madoka.",
        "controllers_buses": "P1/P2, arranque, espera normal y principal/secundario BRC1E/Madoka.",
        "drainage_overflow": "Secuencia de bomba y boya, A3 y AF con diferencias de detección.",
        "commissioning": "Test Run BRC1E, RZAG, Madoka, ARC y Wiring Error Check multisplit.",
        "vrf_network": "Subcódigos VRV IV por exterior, inverter, ventilador, sensor y EEV.",
        "component_checks": "Sondas NTC estándar, módulo y descarga.",
        "technical_values": "Curvas RZQS con puntos de resistencia transcritos.",
        "normal_states": "Espera de mando, calentador de cárter y secuencia inicial de Test Run.",
        "system_architecture": "Pistas físicas para elegir Sky Air, cassette, multisplit o VRV.",
    }
    coverage = [
        {
            "id": category_id,
            "brand_id": 3,
            "area_slug": slug,
            "area_name": name,
            "equipment_scope": "Daikin — corpus Referencia V2",
            "coverage_status": "reference_v2",
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
            "data_version": "2.0.0",
            "last_update_utc": now,
            "reference_brand": "Daikin",
            "verification_warning": (
                "Completa respecto al corpus Referencia V2. "
                "El significado puede variar en familias Daikin no incluidas."
            ),
        },
        "categories": navigation_categories,
    }
    write_json(WEB_DIR / "navigation.json", navigation)

    brand = {
        "slug": "daikin",
        "name": "Daikin",
        "display_name": "Daikin",
        "enabled": True,
        "web_data": "web",
        "media": "media",
        "publish_media": False,
        "static_site": True,
        "schema_version": "2.2.0",
        "data_version": "2.0.0",
        "exported_at_utc": now,
        "counts": counts,
        "notes": (
            "Daikin Referencia V2: base documentada para Sky Air, cassette, "
            "multisplit, VRV, BRC1E y Madoka. No contiene PDFs ni capturas."
        ),
    }
    write_json(BRAND_DIR / "brand.json", brand)

    from audit_brand_quality import audit_brand

    quality = audit_brand(BRAND_DIR)
    write_json(WEB_DIR / "quality.json", quality)
    print(json.dumps({
        "brand": "daikin",
        "counts": counts,
        "interpretations": quality["errors"]["interpretations"],
        "error_quality": quality["errors"]["status_counts"],
        "variant_quality": quality["technical_variants"]["status_counts"],
        "sources": len(SOURCES),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
