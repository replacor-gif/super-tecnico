#!/usr/bin/env python3
"""Normaliza las variantes técnicas Fujitsu con pasos y explicaciones operativas."""

from __future__ import annotations

import json
from typing import Any

from audit_brand_quality import audit_brand, write as write_json
from enrich_fujitsu_indoor_valve_v2 import BRAND, WEB, load, normalize


VERSION = "2.20.0"


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


def section(section_type: str, title: str, body: str, collapsed: int = 0) -> dict[str, Any]:
    return {
        "section_type": section_type,
        "title": title,
        "body": body,
        "collapsed_default": collapsed,
    }


STEP_MAP: dict[int, list[dict[str, Any]]] = {
    9: [
        step("recognition", 1, "Identificar el mando instalado y confirmar en su manual que permite seleccionar número de función y valor."),
        step("prerequisites", 1, "Detener el equipo y anotar la configuración actual antes de entrar en Function Setting.", warning="caution"),
        step("procedure", 1, "Entrar en el modo de funciones siguiendo la combinación de teclas del mando concreto; este manual de unidad no define una combinación universal."),
        step("procedure", 2, "Seleccionar únicamente uno de los números documentados y un valor permitido en su tabla.", "El mando presenta la función y el valor elegidos."),
        step("procedure", 3, "Confirmar el ajuste, salir y reiniciar la alimentación solo si lo exige el procedimiento del mando."),
        step("verification", 1, "Comprobar el comportamiento asociado y conservar el valor anterior para poder revertirlo.", warning="caution"),
    ],
    11: [
        step("safety", 1, "Cortar la alimentación antes de conectar el terminal interior, CN47 o la PCB opcional.", warning="danger"),
        step("recognition", 1, "Distinguir entrada básica, salida CN47 y PCB opcional; no comparten necesariamente tipo de señal ni límites."),
        step("procedure", 1, "Para la entrada básica, usar cable trenzado 22 AWG, separado de potencia y con longitud máxima de 150 m."),
        step("procedure", 2, "Para CN47, respetar el máximo de 25 m y comprobar nivel alto 12 V CC ±2 V y nivel bajo 0 V."),
        step("procedure", 3, "En la PCB opcional, seleccionar correctamente contacto seco o tensión aplicada y después flanco o pulso.", warning="warning"),
        step("verification", 1, "Restablecer alimentación, activar una función cada vez y verificar la entrada o salida correspondiente."),
    ],
    12: [
        step("safety", 1, "Cortar alimentación antes de instalar o cablear la PCB opcional.", warning="danger"),
        step("recognition", 1, "Confirmar si la entrada utilizada es contacto seco o tensión aplicada; no intercambiar ambos tipos."),
        step("procedure", 1, "Configurar el tipo de señal como flanco o pulso según el dispositivo de mando externo."),
        step("procedure", 2, "Cablear la orden necesaria: marcha/paro, parada forzada o termostato externo OFF."),
        step("verification", 1, "En señal de pulso, enviar una orden y comprobar que prevalece la última recibida."),
        step("verification", 2, "En control de grupo, comprobar que todas las unidades siguen el mismo modo esperado."),
    ],
    13: [
        step("safety", 1, "Cortar alimentación antes de conectar P580, PA580, P590 o PA590.", warning="danger"),
        step("recognition", 1, "Identificar P580 como Low Noise, PA580 como Peak Cut, P590 como error y PA590 como estado del compresor."),
        step("procedure", 1, "En las entradas, usar un contacto con capacidad mínima 24 V CC / 10 mA y cable de hasta 10 m."),
        step("procedure", 2, "En las salidas, no superar 12 V CC, 50 mA ni 10 m de cableado."),
        step("verification", 1, "Restablecer alimentación y probar cada contacto por separado, observando el LED o estado correspondiente."),
    ],
    14: [
        step("procedure", 1, "Abrir Display Sensor Values en el mando táctil compatible."),
        step("procedure", 2, "Elegir el dispositivo 00 para interior o 01 para exterior."),
        step("procedure", 3, "Seleccionar el Sensor ID documentado y registrar valor, unidad y estado de funcionamiento."),
        step("interpretation", 1, "Comparar el valor con el rango de la fuente aplicable, sin trasladar un Sensor ID a otra familia."),
        step("record", 1, "Antes de sustituir un componente, anotar sus horas acumuladas; el contador no se reinicia con la pieza nueva."),
    ],
    15: [
        step("safety", 1, "Cortar alimentación antes de localizar o modificar el puente JM2.", warning="danger"),
        step("recognition", 1, "Registrar si JM2 está conectado o desconectado antes de intervenir."),
        step("procedure", 1, "Restablecer alimentación y esperar al menos 30 minutos desde la parada del compresor antes de evaluar el precalentamiento."),
        step("interpretation", 1, "Con JM2 conectado, usar -4 °C para activación y -2 °C para desactivación."),
        step("interpretation", 2, "Con JM2 desconectado, usar 5 °C para activación y 7 °C para desactivación."),
        step("verification", 1, "Comprobar la temperatura del intercambiador y el estado del precalentamiento sin cambiar JM2 como prueba improvisada."),
    ],
    16: [
        step("safety", 1, "Cortar alimentación antes de comprobar conector, bobina o cableado de la válvula.", warning="danger"),
        step("procedure", 1, "Al alimentar, comprobar mediante la herramienta compatible que la placa ordena 528 pulsos de cierre para inicializar."),
        step("interpretation", 1, "Durante el control normal, considerar documentado el recorrido de 52 a 480 pulsos."),
        step("verification", 1, "Si la orden existe pero la válvula no responde, revisar conector, bobina y bloqueo mecánico antes de atribuirlo a la PCB."),
        step("verification", 2, "Si no existe orden, continuar con alimentación, comunicación y control de la PCB según el manual."),
    ],
    17: [
        step("recognition", 1, "Identificar la capacidad de la variante antes de interpretar el número máximo de reintentos."),
        step("procedure", 1, "Ante una parada de protección, respetar la espera de 3 minutos antes de esperar un rearranque."),
        step("interpretation", 1, "En 07/09/12, comparar con 10 reintentos y 10 conjuntos; en 14, con 50 reintentos y 3 conjuntos."),
        step("interpretation", 2, "Durante un cambio de modo, esperar los 140 segundos documentados antes de condenar la válvula de 4 vías."),
        step("verification", 1, "Registrar tiempos y número de reintentos; si supera la secuencia aplicable, seguir el código o protección generado."),
    ],
    21: [
        step("observation", 1, "Cuando parpadee el LED de funcionamiento, leer en el display el número de unidad y el código mostrado automáticamente."),
        step("record", 1, "Anotar ambos datos sin traducir el código a otra generación de mando."),
        step("group", 1, "Si existen dos mandos, realizar el autodiagnóstico desde el principal; el secundario no dispone de esa función."),
        step("interpretation", 1, "Buscar el código en la tabla aplicable a esta interfaz polar de 3 hilos y seguir la ficha técnica correspondiente."),
    ],
    23: [
        step("safety", 1, "Cortar alimentación antes de modificar cableado o selección 2WIRE/3WIRE.", warning="danger"),
        step("recognition", 1, "Confirmar bornero Y1-Y2 o adaptador de dos conductores y placa ajustada en 2WIRE."),
        step("procedure", 1, "Usar dos conductores trenzados de 0,33 a 1,25 mm²; el bus no tiene polaridad."),
        step("procedure", 2, "En el adaptador representado, usar blanco y negro y cortar/aislar el rojo."),
        step("verification", 1, "Restablecer alimentación. Si el mando queda muerto, comprobar primero que la placa no esté ajustada en 3WIRE."),
    ],
    24: [
        step("safety", 1, "Cortar alimentación antes de modificar el bus o el selector 2WIRE/3WIRE.", warning="danger"),
        step("recognition", 1, "Confirmar bornero 1-2-3 o R-W-B y placa ajustada en 3WIRE."),
        step("procedure", 1, "Conectar 1 rojo, 2 blanco y 3 negro —o R-W-B— respetando polaridad."),
        step("verification", 1, "Al alimentar, comprobar que aparece 9C durante varios segundos y después el reloj."),
        step("diagnosis", 1, "Si no llega al reloj, revisar alimentación, colores, conector frontal, DIP y comunicación antes de sustituir el mando."),
    ],
    26: [
        step("record", 1, "Anotar el código completo, incluido el punto: por ejemplo 12.4, 15.4, 26.4 o 27.1."),
        step("classification", 1, "Comprobar si pertenece al propio mando y no al circuito frigorífico de la unidad interior."),
        step("interpretation", 1, "Buscar el significado exacto en la lista documentada; no agrupar códigos con el mismo primer número."),
        step("diagnosis", 1, "Antes de sustituir el mando, revisar alimentación, bus, dirección y Master/Slave según la ficha enlazada."),
        step("verification", 1, "Después de corregir, restablecer alimentación y confirmar que el mando completa el arranque normal."),
    ],
    27: [
        step("recognition", 1, "Determinar si el equipo está en frío/seco o en calor/ventilación/parada; la secuencia no es idéntica."),
        step("observation", 1, "Observar simultáneamente boya, bomba, compresor y ventiladores durante tres minutos."),
        step("cooling", 1, "En frío/seco, al actuar la boya comprobar que se detienen compresor y ventiladores mientras la bomba sigue funcionando."),
        step("timing", 1, "Si la boya libera antes de 3 minutos, comprobar la recuperación tras los retardos; si continúa ON, se genera el error."),
        step("other_modes", 1, "En calor/ventilación/parada, verificar el arranque de la bomba sin extrapolar una parada inmediata del compresor."),
        step("recovery", 1, "Eliminar atasco, suciedad u obstrucción antes de cortar y restablecer alimentación para liberar el enclavamiento.", warning="warning"),
    ],
    29: [
        step("safety", 1, "Cortar alimentación de todas las exteriores antes de cambiar SET3 o SET5.", warning="danger"),
        step("procedure", 1, "Asignar con SET3-1/2 exactamente una maestra y, como máximo, dos esclavas."),
        step("procedure", 2, "En la maestra, configurar con SET3-3/4 cuántas esclavas están conectadas."),
        step("procedure", 3, "En todas las exteriores, ajustar con SET5-1/2 el número total de unidades exteriores."),
        step("verification", 1, "Restablecer alimentación y comprobar que el display reconoce la cantidad y no presenta error de configuración."),
    ],
    30: [
        step("safety", 1, "Cortar la alimentación completa de la red antes de cambiar terminación o dirección.", warning="danger"),
        step("network", 1, "Identificar el segmento de transmisión y asegurar que existe exactamente una resistencia terminal activa."),
        step("procedure", 1, "Configurar SET5-4 en la unidad que debe terminar el segmento; dejar el resto sin terminación."),
        step("procedure", 2, "En la maestra, ajustar REF AD x10/x1 con una dirección de circuito frigorífico única entre 00 y 99."),
        step("verification", 1, "Comprobar terminación, direcciones duplicadas y comunicación antes de iniciar direccionamiento automático."),
    ],
    33: [
        step("safety", 1, "Desconectar el interruptor general de todas las unidades de la red antes de medir resistencia.", warning="danger"),
        step("measurement", 1, "Con el multímetro en ohmios, medir entre los dos terminales de transmisión del punto indicado."),
        step("interpretation", 1, "0-50 Ω: buscar cortocircuito o dos o más terminadores."),
        step("interpretation", 2, "Aproximadamente 190 Ω-1 kΩ: revisar mal contacto o longitud superior a 500 m."),
        step("interpretation", 3, "Más de 1 kΩ: buscar circuito abierto o ausencia de terminador; entre exteriores del mismo circuito se esperan aproximadamente 45-60 Ω."),
        step("verification", 1, "Corregir la anomalía antes de volver a alimentar; el manual advierte riesgo de daño de PCB."),
    ],
    35: [
        step("safety", 1, "Cortar alimentación antes de cablear CN131-CN137.", warning="danger"),
        step("recognition", 1, "Confirmar que se trabaja en la unidad maestra y comprobar la tabla de aplicabilidad del conector."),
        step("procedure", 1, "Elegir la entrada correcta: CN131 Low Noise, CN132 prioridad, CN133 Peak Cut, CN134 parada o CN135 contador."),
        step("procedure", 2, "Para CN136/CN137, instalar la fuente externa de 12-24 V CC con polaridad y límites indicados."),
        step("verification", 1, "Restablecer alimentación y probar una señal cada vez, verificando estado de error o funcionamiento."),
    ],
    38: [
        step("prerequisites", 1, "Confirmar compatibilidad del sistema, versión del software, adaptador USB y autorización para conectarse a la red VRF."),
        step("connection", 1, "Conectar el adaptador oficial en un punto permitido de la línea de transmisión y abrir Service Tool."),
        step("procedure", 1, "Detectar la red y guardar primero una referencia de unidades, direcciones y errores actuales/históricos."),
        step("monitoring", 1, "Registrar tendencias de temperaturas, presiones, sobrecalentamiento y estados durante la condición que se investiga."),
        step("record", 1, "Guardar el registro y documentar hora, modo y carga del sistema para poder compararlo."),
        step("interpretation", 1, "Usar el autodiagnóstico como orientación; confirmar la conclusión con mediciones y comprobaciones del técnico."),
    ],
    39: [
        step("prerequisites", 1, "Confirmar compatibilidad y dimensionar el servidor para el número de redes y unidades a supervisar."),
        step("connection", 1, "Conectar de forma permanente el equipo de monitorización a las redes VRF autorizadas."),
        step("procedure", 1, "Configurar acceso remoto y notificaciones según la política de red del cliente."),
        step("verification", 1, "Comprobar que cada red comunica estado, funcionamiento y errores antes de activar avisos."),
        step("interpretation", 1, "Usar avisos e históricos para mantenimiento preventivo y confirmar en campo cualquier diagnóstico."),
    ],
    44: [
        step("recognition", 1, "Confirmar que la unidad dispone exactamente de indicadores OPERATION y TIMER de esta generación."),
        step("observation", 1, "Contar por separado los parpadeos de OPERATION y TIMER y anotar la pausa de repetición."),
        step("record", 1, "Registrar si cada indicador está fijo, apagado o parpadeando y repetir el conteo al menos dos ciclos."),
        step("interpretation", 1, "Comparar el patrón con la tabla legacy de las páginas 14-15."),
        step("warning", 1, "No convertir directamente el patrón a un código E moderno si el manual no establece equivalencia.", warning="caution"),
    ],
    45: [
        step("prerequisites", 1, "Ejecutar el Test Run oficial y esperar una condición suficientemente estable antes de registrar valores."),
        step("measurement", 1, "Con instrumentación adecuada, comprobar baja presión en frío o alta presión en calor."),
        step("interpretation", 1, "Comparar con aproximadamente 0,8 MPa de baja en frío o 3,0 MPa de alta en calor."),
        step("measurement", 2, "Medir temperatura de entrada y salida y comparar una diferencia aproximada de 10 °C."),
        step("checklist", 1, "Comprobar también drenaje, ventiladores, arranque del compresor y ausencia de código de error."),
        step("warning", 1, "Tratar los valores como checklist de esa condición, no como presiones universales de carga.", warning="caution"),
    ],
    46: [
        step("recognition", 1, "Identificar primero si el mando y la PCB usan bus 2WIRE no polar o 3WIRE polar."),
        step("safety", 1, "Cortar alimentación para revisar continuidad, colores, bornes y selector 2WIRE/3WIRE.", warning="danger"),
        step("measurement", 1, "Restablecer alimentación y medir solo en los terminales indicados por la fuente de esa variante."),
        step("interpretation", 1, "Comparar con la alimentación documentada, aproximadamente 12-13 V CC según la familia, sin generalizar un único valor."),
        step("isolation", 1, "Si es seguro y el manual lo permite, aislar temporalmente mando y cable para distinguir cortocircuito de falta de salida de la PCB."),
        step("diagnosis", 1, "Con tensión correcta al final del cable y configuración correcta, continuar con el mando; sin tensión en origen, continuar con la placa interior."),
    ],
}


SECTION_MAP: dict[int, list[dict[str, Any]]] = {
    2: [
        section("scope", "Qué fuerza realmente", "MANUAL AUTO inicia un modo automático local a 24 °C y ventilador AUTO; no selecciona una frecuencia fija del compresor ni anula las protecciones documentadas."),
        section("timing", "No confundir pulsaciones", "Más de 3 y menos de 10 segundos inicia el modo. Una pulsación cercana a 3 segundos detiene. Evitar mantener 10 segundos o más si la familia asigna otra función de servicio."),
    ],
    18: [
        section("scope", "Solo muestra el detalle", "ENTER no borra el error ni inicia una prueba: transforma el parpadeo rápido de ERROR en el patrón detallado de LED para consultarlo en la tabla."),
        section("record", "Registrar antes de reiniciar", "Anotar todos los LED encendidos, apagados o parpadeando antes de cortar alimentación; un reinicio puede eliminar la indicación activa."),
    ],
    22: [
        section("recognition", "Confirmación acústica", "Cada cambio produce un pitido corto. La coincidencia genera varios pitidos y parpadeo de todos los indicadores; en 00, esa confirmación significa que no se detecta error."),
        section("scope", "Límite del método", "El recorrido identifica el código que reconoce esa unidad receptora. No sustituye la lectura de subcódigos disponibles desde un mando cableado o PCB exterior."),
    ],
    32: [
        section("prerequisites", "Antes del direccionamiento", "Completar cableado, polaridad y terminación de la red; ejecutar este proceso antes del direccionamiento automático de las unidades interiores."),
        section("interpretation", "Resultado", "El número mostrado debe coincidir con los amplificadores instalados. Si aparece un error o una cantidad diferente, revisar alimentación, transmisión y terminación antes de continuar."),
    ],
    40: [
        section("recognition", "Cuándo usar este método", "Solo para el mando antiguo que posee SET TIME y TEMP./DAY y muestra EE:EE en la zona del reloj; no aplicar la combinación a mandos de dos hilos modernos."),
        section("record", "Lectura", "Anotar el código completo antes de salir o restablecer alimentación y compararlo con la tabla de la misma generación."),
    ],
    43: [
        section("safety", "Riesgo frigorífico", "No retirar tuberías con el compresor en marcha ni con válvulas abiertas. Si la secuencia no puede completarse, recuperar el refrigerante con el equipo apropiado.", 0),
        section("group", "Instalaciones en grupo", "Mantener alimentadas las unidades implicadas hasta que todas las exteriores hayan completado su pump down; la placa queda bloqueada hasta cortar alimentación."),
        section("recovery", "Si se interrumpe", "Abrir de nuevo las válvulas antes de repetir y respetar la espera de seguridad. No reiniciar con una válvula cerrada fuera de la secuencia."),
    ],
    7: [
        section("prerequisites", "Condición previa", "Realizar el ajuste con el equipo parado. Si se pierde la secuencia de SELECT/ENTER, pulsar EXIT y comenzar de nuevo desde la indicación normal."),
        section("machine_behavior", "Efecto", "MODE 1 reduce el ruido y MODE 2 aplica una reducción mayor. Otras protecciones y límites de corriente siguen teniendo prioridad cuando corresponda."),
    ],
    10: [
        section("scope", "Programación por funciones", "Seleccionar únicamente combinaciones incluidas en la tabla de esta familia. El mismo número puede tener otro significado en otra generación."),
        section("restart", "Aplicación del cambio", "Después de guardar y salir con RESET, cortar alimentación durante al menos 30 segundos antes de reconectar para aplicar la configuración."),
    ],
    34: [
        section("navigation", "Tres niveles", "Primero se selecciona F1/F2/F3, después el número de función y finalmente su valor. ENTER abre o confirma; SELECT recorre; MODE/EXIT regresa."),
        section("safety", "Antes de cambiar", "Detener la exterior, anotar el valor de fábrica y modificar una sola función cada vez. Una combinación incorrecta puede impedir la puesta en marcha o cambiar el alcance del sistema."),
    ],
    41: [
        section("reading", "Cabecera y número", "POWER/MODE parpadea dos veces como cabecera; el número que debe contarse para el fallo es el parpadeo de ERROR."),
        section("scope", "Tabla aplicable", "Usar el conteo únicamente con esta disposición de LED y consultar la tabla de la misma generación; no convertirlo automáticamente a un subcódigo decimal."),
    ],
}


def update_variants() -> tuple[int, int]:
    touched_steps = 0
    touched_sections = 0
    for path in sorted((WEB / "topics").glob("*.json"), key=lambda item: int(item.stem)):
        topic = load(path)
        changed = False
        for variant in topic.get("variants") or []:
            variant_id = int(variant["id"])
            if variant_id in STEP_MAP:
                variant["steps"] = STEP_MAP[variant_id]
                touched_steps += 1
                changed = True
            if variant_id in SECTION_MAP:
                variant["sections"] = SECTION_MAP[variant_id]
                touched_sections += 1
                changed = True
        if changed:
            write_json(path, topic)
    return touched_steps, touched_sections


def update_search() -> int:
    topics: dict[int, dict[str, Any]] = {
        int(path.stem): load(path) for path in (WEB / "topics").glob("*.json")
    }
    search = load(WEB / "search.json")
    target_ids = set(STEP_MAP) | set(SECTION_MAP)
    for row in search:
        if int(row.get("id") or 0) not in target_ids or not row.get("topic_id"):
            continue
        topic = topics[int(row["topic_id"])]
        variant = next(item for item in topic["variants"] if int(item["id"]) == int(row["id"]))
        parts = [
            topic["title"], topic["summary"], variant["title"], variant["recognition"],
            variant["purpose"], variant["summary"],
        ]
        parts.extend(item.get("title") or "" for item in variant.get("sections") or [])
        parts.extend(item.get("body") or "" for item in variant.get("sections") or [])
        parts.extend(item.get("instruction") or "" for item in variant.get("steps") or [])
        parts.extend(item.get("expected_result") or "" for item in variant.get("steps") or [])
        for parameter in variant.get("parameters") or []:
            parts.extend([parameter.get("parameter_code") or "", parameter.get("name") or "", parameter.get("description") or ""])
            for option in parameter.get("options") or []:
                parts.extend([option.get("option_value") or "", option.get("option_label") or "", option.get("effect") or ""])
        row["summary"] = variant["summary"]
        row["haystack"] = normalize(" ".join(parts))
    write_json(WEB / "search.json", search)
    return len(search)


def update_metadata(search_count: int) -> None:
    navigation_path = WEB / "navigation.json"
    navigation = load(navigation_path)
    navigation["metadata"].update({
        "data_version": VERSION,
        "latest_phase": "Fujitsu V2 — normalización de procedimientos técnicos",
        "last_processed_manual": "Fuentes ya vinculadas a las 71 variantes técnicas",
        "technical_library_review": "Todas las variantes tienen fuente, página, pasos o parámetros y explicación operativa; no quedan variantes desarrolladas, parciales ni de referencia.",
        "last_update_utc": "2026-07-16T16:30:00Z",
    })
    write_json(navigation_path, navigation)

    coverage_path = WEB / "coverage.json"
    coverage = load(coverage_path)
    for row in coverage:
        if row.get("coverage_level") in {"partial", "reference"}:
            row["notes"] = (row.get("notes") or "") + " La presentación se ha normalizado con pasos, alcance y advertencias cuando la fuente los permite."
    write_json(coverage_path, coverage)

    config_path = BRAND / "brand.json"
    config = load(config_path)
    config["data_version"] = VERSION
    config["counts"]["search_entries"] = search_count
    config["notes"] = "Fujitsu V2.20: las 71 variantes técnicas tienen presentación completa, trazable y desplegable."
    write_json(config_path, config)


def main() -> int:
    touched_steps, touched_sections = update_variants()
    search_count = update_search()
    update_metadata(search_count)
    report = audit_brand(BRAND)
    write_json(WEB / "quality.json", report)
    print(json.dumps({
        "version": VERSION,
        "variants_with_steps_added": touched_steps,
        "variants_with_sections_added": touched_sections,
        "search_entries": search_count,
        "variant_statuses": report["technical_variants"]["status_counts"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
