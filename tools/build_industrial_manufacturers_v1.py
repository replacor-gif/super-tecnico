#!/usr/bin/env python3
"""Construye diez fabricantes HVAC comerciales e industriales.

La proyección pública contiene resúmenes técnicos y enlaces a documentación
del fabricante. No incorpora manuales, capturas ni bases privadas. Los códigos
se mantienen separados por controlador, familia y punto de lectura.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import build_manufacturer_wave_v1 as base


def E(
    code: str,
    title: str,
    profile: str,
    source_ref: str,
    page: str,
    family: str,
    scope: str = "system",
    behavior: str = "",
    technical: str = "",
    aliases: tuple[str, ...] = (),
) -> dict[str, Any]:
    if not behavior:
        if scope == "circuit":
            behavior = "Se detiene el circuito afectado; los demás pueden continuar si están disponibles."
        elif scope in {"indoor", "outdoor", "unit"}:
            behavior = "Se protege la unidad o el componente afectado según la persistencia de la alarma."
        else:
            behavior = "La respuesta puede ser aviso, funcionamiento limitado o parada general según la severidad indicada."
    return base.error(
        code,
        title,
        profile,
        source_ref,
        page,
        family,
        scope,
        behavior,
        technical,
        aliases,
    )


def industrial_topics(config: dict[str, Any]) -> list[dict[str, Any]]:
    brand = config["display_name"]
    family_small = config["family_small"]
    family_large = config["family_large"]
    ctrl = config["controller_name"]
    main_ref = "MAIN"
    controller_ref = "CTRL"
    service_ref = "SERVICE"
    topics = base.common_topics(
        brand,
        main_ref,
        controller_ref,
        service_ref,
        family_small,
        family_large,
    )
    topics.extend([
        base.topic("diagnostic_access", "read-current-alarms", "Obtener alarmas activas y su contexto",
                   "Antes de interpretar hay que registrar controlador, severidad, circuito y hora.", [
            base.variant(
                f"{ctrl}: alarmas activas",
                f"Terminal {ctrl} o pantalla integrada con menú de alarmas.",
                controller_ref,
                config["pages"]["alarm_access"],
                "Leer la alarma sin perder su contexto.",
                "Anote el texto completo, código, nivel, circuito y condición de rearme.",
                family_large,
                steps=[
                    "Identifique la pantalla y la versión del controlador antes de entrar en Alarmas.",
                    "Abra la lista de alarmas activas y recorra todos los registros sin borrar ninguno.",
                    "Anote código, texto, circuito, severidad, fecha y hora cuando estén disponibles.",
                    "Compruebe si la alarma es aviso, limitación, parada de circuito o parada de unidad.",
                ],
                controller={"name": ctrl, "interface_type": "display_integrado", "wires": "Según la familia"},
            ),
            base.variant(
                "Distinguir código interno, JBus/BACnet y texto",
                "La documentación muestra más de una columna o identificador para la misma alarma.",
                controller_ref,
                config["pages"]["alarm_table"],
                "Evitar buscar el número en una tabla equivocada.",
                "El índice interno, el código mostrado y el objeto de red no siempre coinciden.",
                family_large,
                steps=[
                    "Compruebe qué columna reproduce exactamente la pantalla del equipo.",
                    "Conserve también el identificador de red si el aviso procede del BMS.",
                    "No convierta un índice JBus, Enum o BACnet en código local sin una relación documentada.",
                ],
            ),
        ]),
        base.topic("history_reset", "alarm-log-reset", "Histórico, reconocimiento y rearme",
                   "Reconocer una alarma no equivale siempre a eliminar su causa ni a rearmarla.", [
            base.variant(
                f"{ctrl}: consultar histórico",
                "Menú Alarm History, Alarm Log, History o equivalente.",
                controller_ref,
                config["pages"]["history"],
                "Reconstruir la secuencia de fallos.",
                "El orden temporal ayuda a separar la causa inicial de las protecciones secundarias.",
                family_large,
                steps=[
                    "Lea primero alarmas activas y después el histórico.",
                    "Busque qué evento apareció primero y cuáles son consecuencia de la parada.",
                    "Guarde fecha, hora, estado y número de repeticiones antes de rearmar.",
                ],
            ),
            base.variant(
                "Rearme automático, manual y por ciclo de red",
                "La tabla de alarmas incluye Reset, Persistence o Latching.",
                controller_ref,
                config["pages"]["alarm_table"],
                "Aplicar el rearme correcto.",
                "Algunas alarmas se borran al normalizarse; otras requieren confirmación local o corte de alimentación.",
                family_large,
                steps=[
                    "Corrija la condición que originó la alarma.",
                    "Respete el tipo de rearme indicado: automático, manual local, remoto o ciclo de red.",
                    "Si reaparece, no repita rearmes: registre las variables y continúe el diagnóstico.",
                ],
            ),
        ]),
        base.topic("commissioning", "prestart-and-commissioning", "Puesta en marcha y comprobaciones previas",
                   "Orden de revisión antes de autorizar compresores y ventiladores.", [
            base.variant(
                "Comprobaciones sin tensión",
                "Equipo detenido y aislado para revisar instalación, ajustes y conexiones.",
                main_ref,
                config["pages"]["commissioning"],
                "Evitar que una configuración o instalación incorrecta genere alarmas.",
                "Se comprueban alimentación, aprietes, protecciones, agua/aire, válvulas, sensores y direcciones.",
                family_large,
                steps=[
                    "Aísle y verifique ausencia de tensión según el procedimiento de seguridad.",
                    "Revise aprietes, tierra, fases, fusibles, válvulas, filtros y caudal disponible.",
                    "Compare DIP, direcciones, capacidad y opciones con la documentación de la unidad.",
                    "Confirme que sensores y transductores están montados y conectados.",
                ],
            ),
            base.variant(
                "Comprobaciones con tensión y primer arranque",
                "Control energizado, pero compresores todavía inhibidos o en modo commissioning.",
                main_ref,
                config["pages"]["commissioning"],
                "Validar entradas y salidas antes de cargar el equipo.",
                "El técnico confirma valores coherentes, sentido de giro, comunicación y estados de seguridad.",
                family_large,
                steps=[
                    "Compruebe tensión y secuencia de fases bajo las condiciones del fabricante.",
                    "Revise desde el monitor las temperaturas, presiones, entradas y salidas.",
                    "Arranque bombas y ventiladores mediante el modo permitido y confirme caudal o prueba de aire.",
                    "Autorice los circuitos de uno en uno y registre las variables de estabilización.",
                ],
            ),
        ]),
        base.topic("service_modes", "manual-test-mode", "Modo manual, Test o Commissioning",
                   "Los modos de servicio no anulan necesariamente las protecciones.", [
            base.variant(
                "Activación segura del modo de prueba",
                "Menú Service, Commissioning, Test o Manual Control.",
                service_ref,
                config["pages"]["service_mode"],
                "Forzar únicamente las salidas previstas.",
                "El control puede mantener bloqueos de presión, caudal, temperatura, fase y seguridad.",
                family_large,
                steps=[
                    "Anote el estado normal y confirme que no hay alarmas activas críticas.",
                    "Entre con el nivel de acceso autorizado y seleccione una sola salida o etapa.",
                    "Vigile confirmaciones, corriente, presión, temperatura y caudal durante la prueba.",
                    "Devuelva todos los puntos a Auto y salga del nivel de servicio.",
                ],
            ),
            base.variant(
                "Qué no debe puentearse",
                "La prueba no arranca o una protección vuelve a detener el equipo.",
                service_ref,
                config["pages"]["service_mode"],
                "No convertir una prueba en una condición peligrosa.",
                "No se deben anular presostatos, caudal, humo, congelación, fase ni cadenas de seguridad.",
                family_large,
                steps=[
                    "Identifique la protección que impide la marcha.",
                    "Compruebe el elemento y su circuito, sin puentearlo para mantener la unidad funcionando.",
                    "Use simulación o sustitución únicamente cuando el manual la autorice y con límites controlados.",
                ],
            ),
        ]),
        base.topic("technical_values", "live-data-snapshot", "Lectura de variables y captura del fallo",
                   "Un registro previo al rearme conserva la información que desaparece al normalizarse.", [
            base.variant(
                "Variables frigoríficas e hidráulicas",
                "Pantalla de datos, monitor de servicio o BMS.",
                service_ref,
                config["pages"]["monitoring"],
                "Comparar lo que mide el control con instrumentos externos.",
                "Registrar entrada/salida de agua o aire, presiones, sobrecalentamiento, subenfriamiento y carga.",
                family_large,
                steps=[
                    "Registre consignas, temperaturas, presiones, frecuencia, corriente y apertura de válvulas.",
                    "Compare sensores del control con instrumentos calibrados.",
                    "Anote qué circuitos y etapas estaban activos cuando apareció la alarma.",
                ],
            ),
            base.variant(
                "Entradas, salidas y comunicaciones",
                "Menú I/O, Board Status, Network o equivalente.",
                service_ref,
                config["pages"]["monitoring"],
                "Separar un componente real de una orden o realimentación incorrecta.",
                "Compruebe orden, realimentación, valor bruto y estado de red antes de sustituir una placa.",
                family_large,
                steps=[
                    "Localice el punto de entrada o salida asociado a la alarma.",
                    "Compare orden y realimentación; mida físicamente cuando sea seguro.",
                    "Revise calidad y estado del bus antes de condenar el dispositivo remoto.",
                ],
            ),
        ]),
        base.topic("controllers_buses", "bms-network", "Buses, BMS y funcionamiento autónomo",
                   "La pérdida de supervisión no siempre detiene la producción local.", [
            base.variant(
                "Pérdida del BMS o gestor de sistema",
                "Alarma de comunicación con supervisor, master o gateway.",
                controller_ref,
                config["pages"]["network"],
                "Determinar si el equipo vuelve a modo autónomo.",
                "Algunas familias continúan localmente; otras pierden consignas, permisos o coordinación.",
                family_large,
                steps=[
                    "Compruebe si la alarma afecta al control local o solo al supervisor.",
                    "Verifique dirección, velocidad, polaridad/terminación y alimentación de cada nodo.",
                    "Confirme qué consigna y modo adopta la unidad durante la pérdida de red.",
                ],
            ),
            base.variant(
                "Maestro/secundario o varias unidades",
                "Instalación con dos o más equipos coordinados.",
                controller_ref,
                config["pages"]["network"],
                "Conservar servicio cuando la arquitectura lo permite.",
                "La documentación puede devolver equipos a modo independiente o parar solo el elemento incomunicado.",
                family_large,
                steps=[
                    "Identifique maestro, secundarios, dirección y terminación.",
                    "Compruebe alimentación y comunicación de todos los nodos.",
                    "Registre si la unidad vuelve a autónomo, mantiene bombas o pierde la secuencia.",
                ],
            ),
        ]),
        base.topic("component_checks", "water-flow-freeze", "Caudal de agua y protección antihielo",
                   "La secuencia de bomba y la protección del intercambiador son prioritarias.", [
            base.variant(
                "Fallo de caudal",
                "Alarma de flow switch, diferencial, caudalímetro o bomba.",
                main_ref,
                config["pages"]["water"],
                "Separar caudal real, sensor y lógica.",
                "Una unidad puede probar la bomba, esperar confirmación y después inhibir compresores.",
                family_large,
                steps=[
                    "Confirme válvulas abiertas, purgado, filtro limpio y bomba girando correctamente.",
                    "Mida caudal o presión diferencial y compare con el estado de la entrada.",
                    "Compruebe temporización y realimentación antes de cambiar la placa.",
                ],
            ),
            base.variant(
                "Antihielo",
                "Temperatura de salida baja o alarma de congelación.",
                main_ref,
                config["pages"]["water"],
                "Proteger el intercambiador sin interpretar la bomba como una avería adicional.",
                "El control puede parar compresores mientras mantiene bomba y resistencias.",
                family_large,
                steps=[
                    "Compruebe temperatura real, concentración de glicol, caudal y calibración de sondas.",
                    "Observe si la bomba y las resistencias se mantienen activas durante la protección.",
                    "No rearranque con hielo formado en el intercambiador.",
                ],
            ),
        ]),
        base.topic("configuration", "capacity-options-identity", "Identidad, capacidad y opciones del equipo",
                   "Una placa de recambio o configuración errónea puede bloquear el arranque.", [
            base.variant(
                "Antes de sustituir el controlador",
                "Placa original aún legible o equipo parcialmente operativo.",
                service_ref,
                config["pages"]["board"],
                "Conservar todos los datos no recuperables.",
                "Registrar software, variante de placa, capacidad, opciones, red y parámetros protegidos.",
                family_large,
                steps=[
                    "Fotografíe y anote etiquetas, software, DIP, jumpers y direcciones.",
                    "Exporte o copie la configuración solo mediante el método autorizado.",
                    "Compruebe compatibilidad exacta del recambio.",
                ],
            ),
            base.variant(
                "Después de sustituir el controlador",
                "Alarma de identidad, base de datos, opción o configuración.",
                service_ref,
                config["pages"]["board"],
                "Restaurar la identidad sin inventar valores.",
                "Algunas opciones necesitan clave, clonación, inicialización o intervención del servicio del fabricante.",
                family_large,
                steps=[
                    "Cargue la configuración y las opciones correspondientes a la unidad.",
                    "Restaure direcciones y confirme todos los módulos detectados.",
                    "Borre únicamente alarmas causadas por la intervención y ejecute la puesta en marcha.",
                ],
            ),
        ]),
        base.topic("normal_states", "degraded-redundant-operation", "Funcionamiento degradado y redundancia",
                   "En equipos multicircuito una alarma no siempre implica parada total.", [
            base.variant(
                "Pérdida de un circuito, ventilador o bomba",
                "Equipo con elementos redundantes o varios circuitos.",
                main_ref,
                config["pages"]["alarm_table"],
                "Determinar qué sigue funcionando.",
                "El control puede continuar con el circuito, ventilador o bomba disponible y limitar capacidad.",
                family_large,
                steps=[
                    "Lea el alcance exacto indicado por la alarma.",
                    "Compruebe qué componentes quedan disponibles y qué funciones se bloquean.",
                    "No suponga parada total si la tabla dice circuito, aviso o funcionamiento degradado.",
                ],
            ),
            base.variant(
                "Aviso sin parada",
                "La tabla indica Alert, Warning, View only o No action.",
                main_ref,
                config["pages"]["alarm_table"],
                "No confundir mantenimiento o aviso con bloqueo.",
                "Aunque la unidad continúe, el aviso debe investigarse y registrarse.",
                family_large,
                steps=[
                    "Confirme que el estado es aviso y no una alarma crítica asociada.",
                    "Registre la variable y la tendencia que lo provocó.",
                    "Planifique la corrección antes de que escale a bloqueo.",
                ],
            ),
        ]),
    ])
    return topics + config.get("extra_topics", [])


def make_config(
    *,
    slug: str,
    brand_id: int,
    name: str,
    display_name: str,
    family_small: str,
    family_large: str,
    controller_name: str,
    scope: str,
    sources: dict[str, dict[str, str]],
    errors: list[dict[str, Any]],
    pages: dict[str, str],
    notes: str,
    provenance: dict[str, Any] | None = None,
    extra_topics: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    config = {
        "slug": slug,
        "brand_id": brand_id,
        "name": name,
        "display_name": display_name,
        "family_small": family_small,
        "family_large": family_large,
        "controller_name": controller_name,
        "scope": scope,
        "sources": sources,
        "errors": errors,
        "pages": pages,
        "warning": "Verifique siempre familia, controlador, severidad y punto de lectura antes de intervenir.",
        "notes": notes,
        "provenance": provenance,
        "extra_topics": extra_topics or [],
    }
    config["topics"] = industrial_topics(config)
    return config


def carrier_config() -> dict[str, Any]:
    smartvu = "https://brandportal.carrier.com/m/5fe2951d17ac2a6/original/10788_CONTROL_11_2024_30XF-Z_SmartVu_400_2100.pdf"
    connect = "https://brandportal.carrier.com/m/6ff681f66780e6bf/original/10554_CONTROL_09_2024_30RB_RBP_30RQ_RQP_165R_1040R_SmartVu.pdf"
    pro = "https://brandportal.carrier.com/m/751a915fb86108ff/original/Regelung-30-RB-RQ-de.pdf"
    sources = {
        "MAIN": base.src("30RB/RQ AquaSnap Installation, Operation and Maintenance", "10004-IOM-30RB-RQ", "https://brandportal.carrier.com/m/cf37b0424b341754/original/10004_IOM_03_2024_30RB_30RQ_A_017-040.pdf", "iom", "2024"),
        "CTRL": base.src("30RB/RBP/30RQ/RQP SmartVu Controls", "10554-CONTROL", connect, "control_manual", "2024"),
        "SERVICE": base.src("30XF-Z SmartVu Controls", "10788-CONTROL", smartvu, "control_manual", "2024"),
        "PRODIALOG": base.src("30RB/30RQ Pro-Dialog+ Control Manual", "PRO-DIALOG-30RB-RQ", pro, "control_manual", "2011"),
    }
    rows: list[dict[str, Any]] = []
    fixed = [
        ("10001", "Protección antihielo del intercambiador de agua", "sensor", "56-62", "system", "La unidad se detiene y la bomba continúa funcionando.", "Falta de caudal o termistor defectuoso."),
        ("10005", "Baja temperatura saturada de aspiración — circuito A", "pressure", "62", "circuit", "", "Transductor, EXV o carga de refrigerante."),
        ("10006", "Baja temperatura saturada de aspiración — circuito B", "pressure", "62", "circuit", "", "Misma lógica aplicada al circuito B."),
        ("10008", "Sobrecalentamiento alto — circuito A", "pressure", "62", "circuit", "", "Revise presión, sonda, EXV y carga."),
        ("10009", "Sobrecalentamiento alto — circuito B", "pressure", "62", "circuit", "", "Revise presión, sonda, EXV y carga."),
        ("10011", "Sobrecalentamiento bajo — circuito A", "pressure", "62", "circuit", "", "Riesgo de retorno de líquido."),
        ("10012", "Sobrecalentamiento bajo — circuito B", "pressure", "62", "circuit", "", "Riesgo de retorno de líquido."),
        ("10014", "Interbloqueo de cliente activo", "power", "62", "system", "La unidad se detiene.", "Entrada de seguridad externa activada."),
        ("10028", "Fallo del cuadro eléctrico", "power", "62", "system", "La unidad se detiene.", "Alimentación principal o temperatura de cuadro."),
        ("10030", "Fallo de comunicación primario/secundario", "communication", "48/64", "system", "Se desactiva la coordinación y las unidades vuelven a modo independiente.", "Revise bus CCN y configuración."),
        ("10031", "Parada de emergencia de red", "power", "48/64", "system", "La unidad se detiene.", "Orden de emergencia recibida por red."),
        ("10032", "Fallo de bomba de agua 1", "power", "48/62", "unit", "Se intenta arrancar con la otra bomba; sin bomba disponible, se detiene la unidad.", "Bomba, térmico, conexión o caudal."),
        ("10033", "Fallo de bomba de agua 2", "power", "48/62", "unit", "Se intenta arrancar con la otra bomba; sin bomba disponible, se detiene la unidad.", "Bomba, térmico, conexión o caudal."),
        ("10037", "Temperatura de condensación fuera del mapa — circuito A", "pressure", "48", "circuit", "", "Transductor o intercambio de condensación."),
        ("10038", "Temperatura de condensación fuera del mapa — circuito B", "pressure", "48", "circuit", "", "Transductor o intercambio de condensación."),
        ("10050", "Detección de fuga de refrigerante", "pressure", "48", "system", "Aviso sin parada en la configuración documentada.", "Fuga real o detector defectuoso."),
        ("10067", "Baja presión de aceite — circuito A", "pressure", "48", "circuit", "Se detiene el compresor A.", "Sensor, cableado o filtro de aceite."),
        ("10068", "Baja presión de aceite — circuito B", "pressure", "48", "circuit", "Se detiene el compresor B.", "Sensor, cableado o filtro de aceite."),
        ("10070", "Máxima presión diferencial del filtro de aceite — A", "pressure", "48", "circuit", "", "Revise filtro y sensores de presión."),
        ("10071", "Máxima presión diferencial del filtro de aceite — B", "pressure", "48", "circuit", "", "Revise filtro y sensores de presión."),
        ("10075", "Nivel de aceite bajo — circuito A", "pressure", "48", "circuit", "", "Nivel bajo o detector defectuoso."),
        ("10076", "Nivel de aceite bajo — circuito B", "pressure", "48", "circuit", "", "Nivel bajo o detector defectuoso."),
        ("10078", "Temperatura de descarga alta — circuito A", "sensor", "48", "circuit", "", "Transductor, condensación o carga."),
        ("10079", "Temperatura de descarga alta — circuito B", "sensor", "48", "circuit", "", "Transductor, condensación o carga."),
        ("10081", "Presión de economizador baja o válvula de aspiración cerrada — A", "pressure", "48", "circuit", "", "Transductor o válvula."),
        ("10082", "Presión de economizador baja o válvula de aspiración cerrada — B", "pressure", "48", "circuit", "", "Transductor o válvula."),
        ("10084", "Caída de presión alta en filtro de aceite — A", "pressure", "48", "circuit", "Aviso sin parada.", "Revisar filtro de aceite."),
        ("10085", "Caída de presión alta en filtro de aceite — B", "pressure", "48", "circuit", "Aviso sin parada.", "Revisar filtro de aceite."),
        ("10090", "Configuración incorrecta del interruptor de caudal", "configuration", "48", "system", "No se permite arrancar.", "Control de caudal o cableado."),
        ("10091", "Fallo del interruptor de caudal", "pressure", "48", "system", "Se detienen compresores y bomba del evaporador.", "Caudal, sensor o cableado."),
        ("10097", "Sondas de entrada y salida de agua intercambiadas", "sensor", "48", "system", "La unidad se detiene.", "La lectura de salida resulta superior a la de entrada en la condición evaluada."),
        ("10110", "Sospecha de falta de refrigerante — circuito A", "pressure", "48", "circuit", "Aviso; puede escalar por repetición.", "Comprobar fugas y carga."),
        ("10111", "Sospecha de falta de refrigerante — circuito B", "pressure", "48", "circuit", "Aviso; puede escalar por repetición.", "Comprobar fugas y carga."),
        ("13005", "Revisión F-Gas necesaria", "normal", "61", "system", "Aviso de mantenimiento sin parada.", "Revisión reglamentaria."),
        ("13006", "Comprobar concentración de inhibidor de corrosión", "normal", "61", "system", "Aviso de mantenimiento sin parada.", "Analizar fluido hidráulico."),
        ("55001", "Fallo del módulo de base de datos", "pcb", "62/64", "system", "Según plataforma: aviso o parada; confirme la tabla exacta.", "Problema de software/controlador."),
        ("56001", "Fallo del módulo Lenscan", "pcb", "62/64", "system", "Según plataforma: aviso o parada; confirme la tabla exacta.", "Problema de software/controlador."),
        ("57020", "Fallo del motor paso a paso EXV principal — A", "valve", "62/65", "circuit", "", "Motor o conexión de la EXV."),
        ("57021", "Fallo del motor paso a paso EXV principal — B", "valve", "62/65", "circuit", "", "Motor o conexión de la EXV."),
        ("58000", "Pérdida de comunicación con filtro THDi", "communication", "62", "system", "Aviso sin parada.", "Bus o filtro THDi."),
        ("58001", "Fallo del filtro THDi", "power", "62", "system", "Por defecto es aviso, pero puede configurarse como parada.", "Fallo del filtro armónico."),
    ]
    for code, title, profile, page, scope, behavior, tech in fixed:
        rows.append(E(code, title, profile, "SERVICE", page, "SmartVu / Connect Touch", scope, behavior, tech))
    for code, title, profile in [
        ("10016", "Compresor A1 no arranca o no aumenta presión", "compressor"),
        ("10017", "Compresor A2 no arranca o no aumenta presión", "compressor"),
        ("10018", "Compresor A3 no arranca o no aumenta presión", "compressor"),
        ("10019", "Compresor A4 no arranca o no aumenta presión", "compressor"),
        ("10020", "Compresor B1 no arranca o no aumenta presión", "compressor"),
        ("10021", "Compresor B2 no arranca o no aumenta presión", "compressor"),
        ("10022", "Compresor B3 no arranca o no aumenta presión", "compressor"),
        ("10023", "Compresor B4 no arranca o no aumenta presión", "compressor"),
    ]:
        rows.append(E(code, title, profile, "CTRL", "62", "30RB/RQ SmartVu", "circuit", "Se detiene el compresor afectado.", "Revise fusible, contactor, orden y elevación de presión."))
    for code, title, scope in [
        ("17001", "Fallo VFD del compresor — circuito A", "circuit"),
        ("18001", "Fallo VFD del compresor — circuito B", "circuit"),
        ("20001", "Fallo VFD ventilador 1 — circuito A", "circuit"),
        ("21001", "Fallo VFD ventilador 2 — circuito A", "circuit"),
        ("24001", "Fallo VFD ventilador 1 — circuito B", "circuit"),
        ("25001", "Fallo VFD ventilador 2 — circuito B", "circuit"),
        ("28001", "Fallo VFD bomba 1 del kit hidrónico", "system"),
        ("29001", "Fallo VFD bomba 2 del kit hidrónico", "system"),
        ("30001", "Fallo VFD bomba 1 de free-cooling", "unit"),
        ("31001", "Fallo VFD bomba 2 de free-cooling", "unit"),
    ]:
        behavior = "Se desactiva el circuito o función asociado." if scope != "system" else "La unidad se detiene."
        rows.append(E(code, title, "power", "SERVICE", "61-62", "30XF-Z SmartVu", scope, behavior, "Consultar el subcódigo del variador."))
    pages = {"alarm_access": "26", "alarm_table": "48-65", "history": "26", "commissioning": "16-24", "service_mode": "29-33", "monitoring": "18-27", "network": "26, 32", "water": "18-20", "board": "40, 62-65"}
    return make_config(slug="carrier", brand_id=21, name="Carrier", display_name="Carrier", family_small="AquaSnap 30RB/30RQ", family_large="SmartVu / Connect Touch / Pro-Dialog+", controller_name="SmartVu / Connect Touch / Pro-Dialog+", scope="Enfriadoras, bombas de calor, rooftops y control industrial Carrier.", sources=sources, errors=rows, pages=pages, notes="Carrier Referencia V1: AquaSnap, SmartVu, Connect Touch, Pro-Dialog+, alarmas de circuito, bombas, aceite, VFD, EXV y red.")


def york_config() -> dict[str, Any]:
    faults_url = "https://docs.johnsoncontrols.com/ductedsystems/r/YORK/en-US/YORK-Sun-Premier-Rooftop-Units-25-Ton-to-150-Ton-Start-Up-and-Operation-Guide-R-454B/2024-10-23/Faults"
    ypal_url = "https://docs.johnsoncontrols.com/ductedsystems/r/YORK/en-US/YORK-50-ton-to-65-ton-YPAL-Design-Level-F-Single-Packaged-Rooftop-Units-Installation-Operation-and-Maintenance-Manual/2021-04-23/User-interface-control-center/User-interface-control-center/Menu-select-keys"
    sources = {
        "MAIN": base.src("YORK Sun Premier Rooftop Start-Up and Operation Guide", "5467002-YSG", faults_url, "operation_guide", "2024"),
        "CTRL": base.src("YORK Sun Premier — Faults list", "5467002-YSG-FAULTS", faults_url, "official_web", "2024"),
        "SERVICE": base.src("YORK YPAL Rooftop IOM — User Interface Control Center", "YPAL-DESIGN-F-IOM", ypal_url, "iom", "2021"),
        "CHILLER": base.src("YORK Commercial & Industrial HVAC", "YORK-CI-HVAC-2018", "https://www.johnsoncontrols.com/pl_pl/-/media/jci/global-capabilities/be/files/be_york_industrial_commercial_hvac_2018.pdf", "catalog", "2018"),
    }
    rows: list[dict[str, Any]] = []
    fault_rows = [
        ("186", "Circuito 1 bloqueado por cadena de seguridad", "power", "critical", "Se bloquea el circuito 1 tras tres aperturas."),
        ("187", "Circuito 2 bloqueado por cadena de seguridad", "power", "critical", "Se bloquea el circuito 2 tras tres aperturas."),
        ("184", "Circuito 1 bloqueado por baja presión", "pressure", "critical", "Se bloquea el circuito 1 tras tres disparos."),
        ("185", "Circuito 2 bloqueado por baja presión", "pressure", "critical", "Se bloquea el circuito 2 tras tres disparos."),
        ("230", "Alarma del detector de fuga A2L", "pressure", "critical", "La entrada BI8 del detector lee 0 V."),
        ("231", "Bloqueo por detector de fuga A2L", "pressure", "critical", "Se bloquea tras tres detecciones en dos horas."),
        ("127", "Parada por humo u otro evento crítico", "power", "critical", "Se detiene la unidad por apertura del circuito de shutdown."),
        ("167", "Fallo VFD ventilador extracción/retorno 1", "fan", "critical", "Se aplica la respuesta crítica de ventilación."),
        ("169", "Fallo VFD ventilador de impulsión 1", "fan", "critical", "Se protege la ventilación principal."),
        ("170", "Fallo VFD ventilador de impulsión 2", "fan", "critical", "Se protege la ventilación principal."),
        ("133", "Sin frío/calor por temperatura de zona no fiable", "sensor", "critical", "Se inhibe frío y calor por falta de referencia fiable."),
        ("155", "Fallo de comunicación con placa de opciones", "communication", "critical", "Se pierden las funciones de la placa de opciones."),
        ("156", "Fallo de comunicación con Customer Terminal Board", "communication", "critical", "Se pierden entradas/salidas del CTB."),
        ("157", "Fallo de comunicación con condensador 1", "communication", "critical", "Se pierde la placa de refrigeración 1."),
        ("158", "Fallo de comunicación con condensador 2", "communication", "critical", "Se pierde la placa de refrigeración 2."),
        ("120", "Salidas deshabilitadas por tensión de entrada baja", "power", "critical", "Se deshabilitan las salidas de 24 V CA."),
        ("121", "Salidas limitadas por brownout de 24 V", "power", "critical", "Se limita el funcionamiento por baja tensión."),
        ("188", "Frío bloqueado por desbordamiento de condensados", "drain", "critical", "Se bloquea la refrigeración."),
        ("130", "Unidad bloqueada por presión estática alta en conducto", "pressure", "critical", "Se bloquea la unidad."),
        ("171", "Bloqueo por falta de prueba de caudal de aire", "fan", "critical", "Se bloquea la unidad al no cerrar APS."),
        ("190", "Compresor C1A bloqueado por interruptor de aceite", "pressure", "critical", "Se bloquea C1A."),
        ("196", "C1A bloqueado por fallo del VFD", "inverter", "critical", "Se bloquea el compresor C1A."),
        ("197", "Parada por entrada de interruptor de seguridad", "power", "critical", "Se detiene toda la unidad."),
        ("198", "Protección antihielo deshabilitada por sonda defectuosa", "sensor", "critical", "La protección queda comprometida; se bloquea la función asociada."),
        ("199", "Parada por monitor de fases", "power", "critical", "Se detiene toda la unidad."),
        ("225", "Solicitud de parada recibida", "power", "critical", "La unidad se detiene por CTB o red."),
        ("149", "Circuito 1 detenido por baja presión", "pressure", "service_priority", "Se detiene el circuito 1."),
        ("150", "Circuito 2 detenido por baja presión", "pressure", "service_priority", "Se detiene el circuito 2."),
        ("151", "HGRH bloqueado: válvula atascada abierta", "valve", "service_priority", "Se bloquea el recalentamiento por gas caliente."),
        ("152", "HGRH bloqueado: válvula atascada cerrada", "valve", "service_priority", "Se bloquea el recalentamiento por gas caliente."),
        ("134", "Fallo de sonda DAT", "sensor", "service_priority", "Se limitan funciones que requieren temperatura de impulsión."),
        ("104", "Fallo de sonda OAT", "sensor", "service_priority", "Se limitan funciones dependientes del aire exterior."),
        ("105", "Fallo de sonda RAT", "sensor", "service_priority", "Se limitan funciones dependientes del retorno."),
        ("108", "Fallo de sonda de batería evaporadora 1", "sensor", "service_priority", "Se protege el circuito asociado."),
        ("159", "Fallo del ventilador de impulsión 1", "fan", "service_priority", "La unidad continúa si la estrategia lo permite."),
        ("160", "Fallo del ventilador de impulsión 2", "fan", "service_priority", "La unidad continúa si la estrategia lo permite."),
        ("413", "Circuito 1 detenido por cadena de seguridad", "power", "service", "Se detiene el circuito 1."),
        ("414", "Circuito 2 detenido por cadena de seguridad", "power", "service", "Se detiene el circuito 2."),
        ("390", "DAT no alcanza la consigna de frío", "sensor", "service", "Aviso de rendimiento sin bloqueo inmediato."),
        ("391", "DAT no alcanza la consigna de calor", "sensor", "service", "Aviso de rendimiento sin bloqueo inmediato."),
        ("100", "Economizador no actúa cuando debe", "valve", "service", "Aviso; compuerta posiblemente cerrada."),
        ("101", "Economizador actúa cuando no debe", "valve", "service", "Aviso; compuerta posiblemente abierta."),
        ("102", "Compuerta del economizador no modula", "valve", "service", "Aviso de modulación."),
        ("148", "Exceso de aire exterior", "fan", "service", "Aviso de caudal/compuerta."),
        ("313", "Alarma de temperatura de zona en calefacción", "sensor", "service", "La temperatura no alcanza el valor esperado."),
        ("403", "Caudal detectado con ventilador parado", "fan", "service", "Aviso; revisar APS/DPS."),
        ("404", "Lámpara UV necesita servicio", "normal", "service", "Aviso de mantenimiento."),
        ("421", "Demandas simultáneas de frío y calor", "configuration", "service", "La unidad recibe dos órdenes incompatibles."),
    ]
    for code, title, profile, level, behavior in fault_rows:
        rows.append(E(code, title, profile, "CTRL", "Faults table", f"Sun Premier — {level}", "system", behavior, "Compruebe la columna Caused by de la tabla oficial."))
    for code, comp in [("213", "C1A"), ("214", "C1B"), ("215", "C1C"), ("216", "C2A"), ("217", "C2B"), ("218", "C2C")]:
        rows.append(E(code, f"{comp} bloqueado por alta presión", "pressure", "CTRL", "Faults table", "Sun Premier — critical", "circuit", f"Se bloquea {comp} tras tres disparos.", "Revise condensador, ventilación, carga y presostato."))
    for code, comp in [("219", "C1A"), ("220", "C1B"), ("221", "C1C"), ("222", "C2A"), ("223", "C2B"), ("224", "C2C")]:
        rows.append(E(code, f"{comp} bloqueado por baja presión", "pressure", "CTRL", "Faults table", "Sun Premier — critical", "circuit", f"Se bloquea {comp} tras tres disparos.", "Revise caudal de aire, hielo, filtros y carga."))
    pages = {"alarm_access": "User interface / Faults", "alarm_table": "Faults table", "history": "History menu", "commissioning": "Pre start-up / Commissioning mode", "service_mode": "Commissioning mode / Service", "monitoring": "Status / Unit Data / Cooling", "network": "Communication / BACnet", "water": "Faults and safety chains", "board": "Control boards / Backup / Restore"}
    return make_config(slug="york", brand_id=22, name="YORK", display_name="YORK / Johnson Controls", family_small="YPAL / Sun Premier rooftop", family_large="YORK Applied y control JCI", controller_name="YORK Control Center / Smart Equipment", scope="Rooftops, enfriadoras y control aplicado YORK.", sources=sources, errors=rows, pages=pages, notes="YORK Referencia V1: Sun Premier, YPAL, severidades Critical/Service Priority/Service, control, BACnet y funcionamiento por circuito.")


def ciat_config() -> dict[str, Any]:
    connect = "https://intranet.ciat.com/fichiers/customtelechargement.php?f=10555control052024aquaciatpowerldild602r4000rconnecttouch.pdf"
    sources = {
        "MAIN": base.src("AQUACIATPOWER LD/ILD Installation and Operation", "AQUACIATPOWER-IOM", "https://www.ciat.com/en/eu/products-systems/heat-pumps-chillers/", "official_product", "2024"),
        "CTRL": base.src("AQUACIATPOWER Connect Touch Instruction Manual", "10555-CONTROL", connect, "control_manual", "2024"),
        "SERVICE": base.src("VECTIC rooftop control and supervision", "CIAT-VECTIC", "https://www.ciat.com/es/es/productos-y-sistemas/unidades-rooftop-y-sistemas-compactos/controles-para-sistemas-compactos/vectic/", "official_web", "current", "es"),
        "PRODUCTS": base.src("CIAT Products and Systems", "CIAT-PRODUCTS", "https://www.ciat.com/en/eu/products-systems/", "official_web", "current"),
    }
    rows: list[dict[str, Any]] = []
    items = [
        ("10029", "Pérdida de comunicación con System Manager", "communication", "65", "system", "La unidad vuelve a modo autónomo.", "Error de comunicación."),
        ("10122", "Modo de sustitución: faltan claves de activación", "configuration", "65", "system", "Las opciones protegidas pueden bloquearse tras siete días.", "Control sustituido sin claves."),
        ("8001", "Identificador de marca no válido", "configuration", "65", "system", "No se permite arrancar.", "Configuración de unidad incorrecta."),
        ("10052", "Fallo de caudal en recuperación de calor", "pressure", "65", "unit", "Aviso sin parada general.", "El flow switch permanece abierto cinco minutos."),
        ("10128", "Protección antihielo del condensador de recuperación", "sensor", "65", "unit", "Se detiene recuperación; la enfriadora continúa.", "Entrada o salida de agua por debajo de 1,1 °C en la condición documentada."),
        ("10129", "Temperatura de agua alta en recuperación", "sensor", "65", "system", "La unidad se detiene.", "Salida de recuperación superior a 95 °C durante tres minutos."),
        ("10054", "Fallo del controlador trifásico", "power", "65", "system", "Puede ser aviso o parada según PhCtrAct.", "Pérdida/secuencia de fase, tensión, asimetría o frecuencia."),
        ("59001", "Pérdida de comunicación con contador de energía", "communication", "65", "system", "Aviso sin parada.", "Bus, contador o comunicación."),
        ("55001", "Fallo del módulo de base de datos", "pcb", "64", "system", "La unidad se detiene.", "Problema de software."),
        ("56001", "Fallo del módulo Lenscan", "pcb", "64", "system", "La unidad se detiene.", "Problema de software."),
        ("57001", "Baja tensión SIOB/CIOB — circuito A", "power", "64", "system", "La unidad se detiene.", "Alimentación inestable o problema eléctrico."),
        ("57002", "Baja tensión SIOB/CIOB — circuito B", "power", "64", "system", "La unidad se detiene.", "Alimentación inestable o problema eléctrico."),
        ("57006", "Baja tensión SIOB/CIOB — EMM", "power", "64", "system", "La unidad se detiene.", "Alimentación inestable o problema eléctrico."),
        ("57020", "Fallo motor paso a paso EXV principal — A", "valve", "64", "circuit", "", "Motor EXV."),
        ("57021", "Fallo motor paso a paso EXV principal — B", "valve", "64", "circuit", "", "Motor EXV."),
        ("170nn", "Fallo VFD ventilador 1 — circuito A", "fan", "64", "circuit", "Con un solo drive se detiene A; con dos puede continuar con uno.", "El sufijo nn es el código del variador."),
        ("180nn", "Fallo VFD ventilador 2 — circuito A", "fan", "64", "circuit", "El circuito puede continuar si queda un drive disponible.", "El sufijo nn es el código del variador."),
        ("190nn", "Fallo VFD ventilador 1 — circuito B", "fan", "64", "circuit", "Con un solo drive se detiene B; con dos puede continuar con uno.", "El sufijo nn es el código del variador."),
        ("200nn", "Fallo VFD ventilador 2 — circuito B", "fan", "64", "circuit", "El circuito puede continuar si queda un drive disponible.", "El sufijo nn es el código del variador."),
        ("21nnn", "Fallo VFD bomba 1", "power", "64", "system", "Arranca la otra bomba; sin bombas disponibles se detiene la unidad.", "El sufijo nnn es el código del variador."),
        ("22nnn", "Fallo VFD bomba 2", "power", "64", "system", "Arranca la otra bomba; sin bombas disponibles se detiene la unidad.", "El sufijo nnn es el código del variador."),
        ("350nn", "Aviso VFD ventilador 1 — circuito A", "fan", "64", "circuit", "Aviso sin acción.", "Código de alerta del variador."),
        ("360nn", "Aviso VFD ventilador 2 — circuito A", "fan", "64", "circuit", "Aviso sin acción.", "Código de alerta del variador."),
        ("370nn", "Aviso VFD ventilador 1 — circuito B", "fan", "64", "circuit", "Aviso sin acción.", "Código de alerta del variador."),
        ("380nn", "Aviso VFD ventilador 2 — circuito B", "fan", "64", "circuit", "Aviso sin acción.", "Código de alerta del variador."),
        ("39nnn", "Aviso VFD bomba 1", "power", "64", "system", "Aviso sin acción.", "Código de alerta del variador."),
        ("40nnn", "Aviso VFD bomba 2", "power", "64", "system", "Aviso sin acción.", "Código de alerta del variador."),
    ]
    for code, title, profile, page, scope, behavior, tech in items:
        rows.append(E(code, title, profile, "CTRL", page, "AQUACIATPOWER Connect Touch", scope, behavior, tech))
    drive = [(1, "Sobrecorriente durante aceleración"), (2, "Sobrecorriente durante deceleración"), (3, "Sobrecorriente a velocidad constante"), (4, "Sobrecorriente al arranque"), (5, "Cortocircuito de rama"), (8, "Falta de fase de entrada"), (9, "Falta de fase de salida"), (10, "Sobretensión durante aceleración"), (11, "Sobretensión durante deceleración"), (12, "Sobretensión a velocidad constante"), (13, "Sobrecarga del inverter"), (14, "Sobrecarga del motor"), (16, "Sobretemperatura"), (18, "Fallo EEPROM de escritura"), (19, "Fallo EEPROM de lectura"), (21, "Fallo RAM"), (22, "Fallo ROM"), (23, "Fallo CPU"), (24, "Fallo de comunicación"), (26, "Fallo del detector de corriente"), (28, "Fallo de comunicación del teclado"), (30, "Subtensión del circuito principal"), (34, "Fallo a tierra"), (41, "Tipo de inverter incorrecto")]
    for number, title in drive:
        rows.append(E(f"VFD-{number}", title, "inverter", "CTRL", "66", "Connect Touch — subcódigo VFD", "unit", "Se aplica la acción del código contenedor 17/18/19/20/21/22.", f"Subcódigo {number}; confirme qué drive lo originó.", aliases=(str(number),)))
    pages = {"alarm_access": "45", "alarm_table": "54-67", "history": "45", "commissioning": "12-20", "service_mode": "46-52", "monitoring": "20-45", "network": "39-44", "water": "10-18, 54-65", "board": "40, 64-65"}
    return make_config(slug="ciat", brand_id=23, name="CIAT", display_name="CIAT", family_small="VECTIOS / VECTIC", family_large="AQUACIATPOWER / Connect Touch", controller_name="Connect Touch / VECTIC", scope="Rooftops, enfriadoras, bombas de calor y control CIAT.", sources=sources, errors=rows, pages=pages, notes="CIAT Referencia V1: Connect Touch, VECTIC, códigos JBus/alarma, acciones por circuito, funcionamiento degradado, VFD y recuperación de calor.")


def trane_config() -> dict[str, Any]:
    intellipak = "https://www.trane.com/content/dam/Trane/Commercial/global/products-systems/equipment/unitary/rooftop-systems/intellipak-i-20-to-130-tons/RT-SVP011G-EN_02112023.pdf"
    sources = {
        "MAIN": base.src("IntelliPak with Symbio 800 Programming Guide", "RT-SVP011G-EN", intellipak, "programming_guide", "2023"),
        "CTRL": base.src("Symbio Training and Troubleshooting", "TRANE-SYMBIO-TRAINING", "https://www.trane.com/commercial/north-america/us/en/education-training/symbio-training.html", "official_web", "current"),
        "SERVICE": base.src("Tracer TU and Controls Software", "TRANE-CONTROLS-SOFTWARE", "https://www.trane.com/commercial/north-america/us/en/products-systems/smart-building-technology/building-controls-solutions/trane-controls-software-downloads.html", "official_web", "current"),
        "CGAM": base.src("CGAM Air-Cooled Scroll Chiller", "TRANE-CGAM", "https://www.trane.com/commercial/north-america/us/en/products-systems/chillers/air-cooled-chillers/cgam.html", "official_product", "current"),
    }
    rows: list[dict[str, Any]] = []
    diagnostics = [
        ("AIRFLOW ASSEMBLY FAILURE", "Fallo del conjunto de caudal de aire", "fan", "89-91", "system", "La severidad determina si limita o detiene la unidad."),
        ("SUPPLY FAN PROVING FAILURE", "Fallo de confirmación del ventilador de impulsión", "fan", "89-94", "system", "Puede inhibir calefacción/frío o detener la unidad."),
        ("RETURN FAN PROVING FAILURE", "Fallo de confirmación del ventilador de retorno", "fan", "89-94", "system", "Se detiene o limita la función de retorno."),
        ("CONDENSER FAN PROVING FAILURE", "Fallo de confirmación del ventilador de condensación", "fan", "106-109", "circuit", "El circuito usa los ventiladores restantes o se detiene."),
        ("VFD FAULT SUPPLY FAN", "Fallo general VFD del ventilador de impulsión", "inverter", "109-111", "system", "Según redundancia, continúa con otro ventilador o se detiene."),
        ("VFD SUPPLY FAN MOTOR CURRENT OVERLOAD", "Sobrecarga de corriente del ventilador de impulsión", "inverter", "111, 129", "system", "Con otro ventilador disponible continúa sin calefacción; sin redundancia se detiene."),
        ("VFD SUPPLY FAN SHORT CIRCUIT", "Cortocircuito del ventilador de impulsión", "inverter", "111-112", "system", "No se recomienda volver a operar hasta eliminar el corto."),
        ("VFD SUPPLY FAN GROUND FAULT", "Fallo a tierra del ventilador de impulsión", "inverter", "128", "system", "Se bloquea el ventilador afectado."),
        ("VFD SUPPLY FAN IN HAND MODE", "VFD de impulsión en modo manual", "configuration", "128", "system", "Aviso sin enclavamiento; puede impedir la secuencia normal."),
        ("VFD RETURN FAN MOTOR CURRENT OVERLOAD", "Sobrecarga del VFD de retorno", "inverter", "111", "system", "Parada inmediata y enclavada de la unidad."),
        ("VFD RETURN FAN IN HAND MODE", "VFD de retorno en modo manual", "configuration", "111", "system", "Aviso; el modo manual altera arranque y regulación."),
        ("VFD FAULT CONDENSER FAN", "Fallo general del VFD de condensación", "inverter", "108-109", "circuit", "Los ventiladores restantes pasan a control de velocidad fija."),
        ("VFD CONDENSER FAN MOTOR CURRENT OVERLOAD", "Sobrecarga del ventilador de condensación", "inverter", "108, 125", "circuit", "Los ventiladores restantes mantienen el circuito si es posible."),
        ("VFD CONDENSER FAN SHORT CIRCUIT", "Cortocircuito del ventilador de condensación", "inverter", "126", "circuit", "Los ventiladores restantes mantienen el circuito si es posible."),
        ("VFD RELIEF FAN LOCKED MOTOR", "Motor del ventilador de alivio bloqueado", "fan", "110, 127", "system", "Con otros ventiladores no hay acción; sin ellos se cierra la compuerta y se desactiva economización."),
        ("VFD RELIEF FAN MOTOR OVERHEATED", "Motor del ventilador de alivio sobrecalentado", "fan", "127", "system", "Se aplica redundancia o se desactiva alivio/economización."),
        ("VFD RELIEF FAN POWER MODULE OVERHEATED", "Módulo de potencia del ventilador de alivio sobrecalentado", "inverter", "110, 127", "system", "Se aplica redundancia o se desactiva alivio/economización."),
        ("VFD RELIEF FAN SPEED PARAMETER FAILURE", "Parámetro de velocidad del ventilador de alivio incorrecto", "configuration", "110, 127", "system", "Puede requerir clonación EC."),
        ("VFD TORQUE LIMIT EXCEEDED CPRSR", "Límite de par del VFD de compresor excedido", "inverter", "Troubleshooting", "circuit", "Parada inmediata del circuito."),
        ("DRIVE TRIP LOCK", "Bloqueo interno del variador", "inverter", "107-111", "unit", "Puede requerir ciclo de alimentación tras corregir la causa."),
        ("TIME LOSS FROM POWER OUTAGE", "Pérdida de hora tras corte de red", "pcb", "130", "system", "Aviso de reloj/batería; no es una avería frigorífica."),
        ("TD7 AUTOMATIC REDISCOVER", "Redescubrimiento automático TD7", "normal", "130", "system", "Estado temporal de actualización de datos."),
        ("SENSOR FAILURE", "Fallo de sonda o entrada analógica", "sensor", "89-105", "system", "La respuesta depende de la función que utiliza la entrada."),
        ("LOW REFRIGERANT PRESSURE", "Presión de refrigerante baja", "pressure", "89-105", "circuit", "Se limita o detiene el circuito."),
        ("HIGH REFRIGERANT PRESSURE", "Presión de refrigerante alta", "pressure", "89-105", "circuit", "Se detiene el circuito."),
    ]
    for code, title, profile, page, scope, behavior in diagnostics:
        rows.append(E(code, title, profile, "MAIN", page, "IntelliPak / Symbio 800", scope, behavior, "Compruebe Target, Severity, Persistence, Condition/Response y Reset Level."))
    pages = {"alarm_access": "89", "alarm_table": "89-130", "history": "89, 130", "commissioning": "13-35", "service_mode": "35-88", "monitoring": "35-88", "network": "15-35, 130", "water": "CGAM product/IOM", "board": "130"}
    return make_config(slug="trane", brand_id=24, name="Trane", display_name="Trane", family_small="IntelliPak rooftop", family_large="Symbio 800 / CGAM / Tracer", controller_name="Symbio 800 / TD7 / Tracer TU", scope="Rooftops, enfriadoras y automatización Trane.", sources=sources, errors=rows, pages=pages, notes="Trane Referencia V1: diagnósticos textuales Symbio 800, severidad, persistencia, VFD, redundancia de ventiladores y herramientas Tracer.")


def lennox_config() -> dict[str, Any]:
    product = "https://lennox.lennoxemea.com/en/products/air-conditioning-and-heating/rooftops/flexair"
    sources = {
        "MAIN": base.src("Flexair Installation, Operation and Maintenance", "FLEXAIR-IOM-2022.03-EN", product, "iom", "2022"),
        "CTRL": base.src("CLIMATIC 60 Rooftop User Manual", "CL60-ROOFTOP-IOM-0412-E", product, "control_manual", "2012"),
        "SERVICE": base.src("DM Display User Manual for Flexair", "DM60-FLEXAIR", product, "controller_manual", "2022"),
        "BALTIC": base.src("Baltic Rooftop product and IOM resources", "LENNOX-BALTIC", "https://lennox.lennoxemea.com/en/products/air-conditioning-and-heating/rooftops/baltic", "official_product", "current"),
    }
    rows: list[dict[str, Any]] = []
    data = [
        ("001", "Corte de caudal del evaporador de agua", "pressure", "CL60 alarms", "system", "Se detienen compresores; confirme la bomba y el flow switch."),
        ("016", "Fallo de quemador de gas", "power", "44", "unit", "Se detiene el quemador y requiere rearme manual."),
        ("021", "Temperatura de impulsión por encima del límite", "sensor", "45", "system", "Se aplica el límite de seguridad."),
        ("022", "Temperatura de impulsión por debajo del límite", "sensor", "45", "system", "La primera etapa puede detener compresores."),
        ("023", "Temperatura ambiente por encima del límite", "sensor", "45", "system", "Alarma de límite de ambiente."),
        ("024", "Temperatura ambiente por debajo del límite", "sensor", "45", "system", "Alarma sin acción en la tabla documentada."),
        ("025", "Temperatura de agua del condensador alta", "sensor", "45", "system", "Se detienen compresores."),
        ("026", "Temperatura de agua del condensador baja", "sensor", "45", "system", "Se detienen compresores."),
        ("031", "Fallo del humidificador", "power", "46", "unit", "Se detiene el humidificador; rearme automático."),
        ("032", "Humedad ambiente baja", "sensor", "46", "system", "Aviso; rearme tras dos minutos en rango."),
        ("033", "Humedad ambiente alta", "sensor", "46", "system", "Aviso; rearme tras dos minutos en rango."),
        ("041", "Fallo eléctrico de la bomba 1", "power", "46", "unit", "Se detiene la bomba; rearme manual."),
        ("051", "Fallo del motor de recuperación", "fan", "47", "unit", "Se detiene el motor de recuperación."),
        ("052", "Fallo de la rueda de recuperación", "fan", "47", "unit", "Se detiene la rueda; el tercer disparo diario requiere rearme manual."),
        ("054", "Filtro de recuperación sucio", "normal", "47", "unit", "Aviso de mantenimiento."),
        ("061", "Placa CLIMATIC 60 maestra desconectada", "communication", "47", "system", "La unidad pasa inmediatamente a modo independiente."),
        ("062", "Placa CLIMATIC 60 esclava desconectada", "communication", "47", "system", "La unidad pasa inmediatamente a modo independiente."),
        ("070", "Fallo del reloj en tiempo real", "pcb", "48", "system", "Aviso de reloj/batería."),
        ("080", "Fallo del sensor de caudal de impulsión", "sensor", "50", "system", "Parada inmediata; el ventilador puede seguir según la secuencia."),
        ("081", "Fallo de sonda de temperatura ambiente", "sensor", "50", "system", "Parada inmediata; el ventilador sigue."),
        ("082", "Fallo del sensor de humedad ambiente", "sensor", "50", "system", "Parada inmediata; el ventilador sigue."),
        ("083", "Fallo de sonda de aire exterior", "sensor", "50", "system", "Parada inmediata; el ventilador sigue."),
        ("084", "Fallo del sensor de humedad exterior", "sensor", "50", "system", "Parada inmediata; el ventilador sigue."),
        ("085", "Fallo de sonda de impulsión", "sensor", "50", "system", "Parada inmediata; el ventilador sigue."),
        ("086", "Fallo de sonda de entrada de agua del condensador", "sensor", "50", "system", "Se detienen todos los circuitos."),
        ("087", "Fallo de sonda de salida de agua del condensador", "sensor", "50", "system", "Se detienen todos los circuitos."),
        ("089", "Fallo del sensor de calidad de aire", "sensor", "50", "system", "Aviso sin parada."),
        ("091", "Fallo del ventilador de impulsión o extracción", "fan", "51", "system", "Parada inmediata de toda la unidad."),
        ("092", "Fallo del inverter del ventilador de impulsión", "inverter", "51", "system", "Parada inmediata de toda la unidad."),
        ("094", "Fallo del inverter del ventilador de extracción", "inverter", "51", "system", "Parada inmediata de toda la unidad."),
        ("099", "Detección de fuego o humo", "power", "51", "system", "Parada inmediata y posición de compuerta según ajuste 3114."),
        ("103", "Fallo inverter del ventilador de condensador — circuito 1", "inverter", "51", "circuit", "Parada inmediata del circuito 1."),
        ("203", "Fallo inverter del ventilador de condensador — circuito 2", "inverter", "51", "circuit", "Parada inmediata del circuito 2."),
    ]
    for code, title, profile, page, scope, behavior in data:
        rows.append(E(code, title, profile, "CTRL", page, "CLIMATIC 60 rooftop", scope, behavior, "Respete la lógica de rearme y los contadores diarios."))
    sensor_map = {141: "presión alta C1", 142: "presión baja C1", 143: "temperatura de líquido C1", 144: "temperatura de aspiración C1", 241: "presión alta C2", 242: "presión baja C2", 243: "temperatura de líquido C2", 244: "temperatura de aspiración C2", 341: "presión alta C3", 342: "presión baja C3", 343: "temperatura de líquido C3", 344: "temperatura de aspiración C3"}
    for code, label in sensor_map.items():
        rows.append(E(str(code), f"Fallo de sensor: {label}", "sensor", "CTRL", "49-50", "CLIMATIC 60 rooftop", "circuit", "Se detiene inmediatamente el circuito correspondiente.", "Entrada abierta, en corto o sensor defectuoso."))
    for circuit in (1, 2, 3):
        prefix = "" if circuit == 1 else str(circuit)
        for suffix, title, profile in [("19", "Temperatura de condensación baja", "sensor"), ("29", "Temperatura de condensación alta", "sensor"), ("21", "Sobrecalentamiento alto", "pressure"), ("22", "Sobrecalentamiento bajo", "pressure"), ("23", "Subenfriamiento bajo", "pressure"), ("24", "Subenfriamiento alto", "pressure"), ("27", "MOP fuera de rango", "pressure"), ("28", "LOP fuera de rango", "pressure")]:
            code = f"{circuit}{suffix}" if circuit > 1 else f"1{suffix}"
            rows.append(E(code, f"{title} — circuito {circuit}", profile, "CTRL", "55-57", "CLIMATIC 60 rooftop", "circuit", "Aviso sin efecto directo sobre compresores en esta tabla.", "Puede escalar por repetición; revise ciclo frigorífico y EXV."))
    pages = {"alarm_access": "DM60 / Alarm list", "alarm_table": "44-57", "history": "CL60 alarm history", "commissioning": "Flexair IOM start-up", "service_mode": "CLIMATIC service menus", "monitoring": "DM60 / DS60 values", "network": "CL60 communication", "water": "Flexair IOM hydraulics", "board": "CL60 configuration"}
    return make_config(slug="lennox", brand_id=25, name="Lennox", display_name="Lennox", family_small="Baltic / Flexair rooftop", family_large="CLIMATIC 60 / DM60 / DS60", controller_name="CLIMATIC 60 / DM60", scope="Rooftops, unidades empaquetadas y control Lennox EMEA.", sources=sources, errors=rows, pages=pages, notes="Lennox Referencia V1: CLIMATIC 60, DM60, Baltic/Flexair, alarmas de sensores, ventiladores, recuperación y circuitos frigoríficos.")


def hitecsa_config() -> dict[str, Any]:
    manual = "https://www.hitecsa.com/files/products/es/iom_%C2%B5kr3bi_17a38_208536_210712_es_data_iom.pdf"
    sources = {
        "MAIN": base.src("µKr3Bi mini — Instalación y mantenimiento", "IOM-µKr3Bi-208536", manual, "iom", "2021", "es"),
        "CTRL": base.src("µKr3Bi mini — Termostato, control y alarmas", "IOM-µKr3Bi-CONTROL", manual, "control_manual", "2021", "es"),
        "SERVICE": base.src("Kubic / Kr3 — Soluciones comerciales y controles", "HITEC-SA-CONTROLS", "https://www.baxi.es/soluciones-comerciales/soluciones", "official_web", "current", "es"),
        "LEGACY": base.src("RCAZ Rooftop — terminal pCO y red LAN", "88392-REV102", "https://www.hitecsa.com/files/products/es/RCABZ_CT.pdf", "technical_catalog", "2005", "es"),
    }
    rows: list[dict[str, Any]] = []
    messages = [
        ("ERR SND AGUA ENTRADA", "Error de sonda de temperatura de entrada de agua", "sensor", "system", "Para toda la máquina."),
        ("ERR SND AGUA SALIDA", "Error de sonda de temperatura de salida de agua", "sensor", "system", "Para toda la máquina."),
        ("WARNING ANTIHIELO", "Aviso antihielo con máquina parada", "sensor", "system", "Arranca bomba y resistencias."),
        ("ALARMA ANTIHIELO C1", "Alarma antihielo del circuito 1", "sensor", "circuit", "Detiene C1, mantiene bomba y arranca resistencias."),
        ("ALTA PRESION C1", "Alta presión de descarga — circuito 1", "pressure", "circuit", "Se detiene el circuito 1."),
        ("BAJA PRESION C1", "Baja presión de aspiración — circuito 1", "pressure", "circuit", "Se detiene el circuito 1."),
        ("MIN PRESION C1", "Presión mínima de aspiración — circuito 1", "pressure", "circuit", "Se detiene el circuito 1."),
        ("FUGA REFRIGERANTE C1", "Fuga de refrigerante — circuito 1", "pressure", "circuit", "Se detiene el circuito 1."),
        ("ALTA TEMP DESCARGA C1", "Temperatura de descarga alta — circuito 1", "sensor", "circuit", "Se detiene el circuito 1."),
        ("CAUDAL FUERA LIMITES", "Caudal de agua fuera de límites", "pressure", "system", "Para toda la máquina."),
        ("PRESION AGUA FUERA LIMITES", "Presión de agua fuera de límites", "pressure", "system", "Para toda la máquina."),
        ("MASTER OFFLINE", "Unidad maestra sin comunicación", "communication", "system", "Se pierde coordinación; compruebe funcionamiento autónomo."),
        ("SLAVE BOARD OFFLINE", "Placa secundaria sin comunicación", "communication", "system", "Se pierde el módulo asociado."),
        ("EVD OFFLINE", "Driver de válvula EVD sin comunicación", "communication", "system", "Para toda la máquina."),
        ("ENERGY METER OFFLINE", "Contador de energía sin comunicación", "communication", "system", "Aviso sin parada indicada."),
        ("FAN 1 OFFLINE", "Ventilador 1 sin comunicación", "communication", "unit", "Se pierde el ventilador asociado."),
        ("FAN 2 OFFLINE", "Ventilador 2 sin comunicación", "communication", "unit", "Se pierde el ventilador asociado."),
        ("CPCOE OFFLINE", "Módulo c.pCOe sin comunicación", "communication", "system", "Se pierden las entradas/salidas asociadas."),
        ("GRAVE ALTA PRESION C1", "Alarma grave de alta presión — circuito 1", "pressure", "circuit", "Se detiene C1 y requiere rearme manual."),
        ("GRAVE BAJA PRESION C1", "Alarma grave de baja presión — circuito 1", "pressure", "circuit", "Se detiene C1 y requiere rearme manual."),
        ("GRAVE FUGA C1", "Alarma grave de fuga — circuito 1", "pressure", "circuit", "Rearme manual de fabricante."),
        ("GRAVE ALTA TEMP DESCARGA C1", "Alarma grave de descarga alta — circuito 1", "sensor", "circuit", "Se detiene C1 y requiere rearme manual."),
        ("GRAVE IF PDP", "Bomba activa sin caudal", "pressure", "system", "Parada general y rearme manual."),
        ("GRAVE BAJO RATIO COMPRESION C1", "Ratio de compresión bajo — circuito 1", "compressor", "circuit", "Se detiene C1 y requiere rearme manual."),
        ("GRAVE CAUDAL", "Alarma grave de caudal fuera de límites", "pressure", "system", "Parada general y rearme manual."),
        ("GRAVE ANTIHIELO", "Alarma grave antihielo", "sensor", "system", "Parada general y rearme manual."),
        ("GRAVE PRESION AGUA", "Alarma grave de presión de agua", "pressure", "system", "Parada general y rearme manual."),
    ]
    for code, title, profile, scope, behavior in messages:
        rows.append(E(code, title, profile, "CTRL", "30-31", "µKr3Bi / W-HiReg", scope, behavior, "Mensaje textual del controlador; confirme circuito y rearme."))
    pages = {"alarm_access": "24, 29-30", "alarm_table": "30-31", "history": "29-30", "commissioning": "22-23", "service_mode": "24-29", "monitoring": "23-29", "network": "23-31", "water": "18, 22-23, 30-31", "board": "23-29"}
    return make_config(slug="hitecsa", brand_id=26, name="Hitecsa", display_name="Hitecsa", family_small="Rooftop RCAZ / pCO", family_large="µKr3Bi / W-HiReg", controller_name="W-HiReg / pGD / pCO", scope="Rooftops, enfriadoras y bombas de calor Hitecsa.", sources=sources, errors=rows, pages=pages, notes="Hitecsa Referencia V1: µKr3Bi, W-HiReg, alarmas textuales, caudal, antihielo, EVD, pCO y red.")


def keyter_config() -> dict[str, Any]:
    persea = "https://www.keyter.com/es/persea/"
    sources = {
        "MAIN": base.src("PERSEA EVO — producto y controles", "KEYTER-PERSEA-EVO", persea, "official_product", "current", "es"),
        "CTRL": base.src("Anexo alarmas TH-Tune Aire-Aire", "MR_ANEXO_TH_TUNE_AA_2101_ES_ES", persea, "manufacturer_document_reference", "2021", "es"),
        "SERVICE": base.src("KEYTER Akademy — regulación y control", "KEYTER-AKADEMY-CONTROL", "https://www.keyter.com/akademy/", "official_web", "current", "es"),
        "KICONEX": base.src("KEYTER service and supervision", "KEYTER-SERVICE", "https://www.keyter.com/service/", "official_web", "current", "es"),
    }
    rows: list[dict[str, Any]] = []
    # TH-Tune combina un valor numérico grande con un texto de cuatro caracteres.
    hp_lp = [
        ("11/ALHP", "Presostato de alta — circuito 1", "pressure"),
        ("12/ALHP", "Transmisor de alta — circuito 1", "pressure"),
        ("13/ALHP", "Fallo por alta presión — circuito 1", "pressure"),
        ("11/ALLP", "Presostato de baja — circuito 1", "pressure"),
        ("12/ALLP", "Transmisor de baja — circuito 1", "pressure"),
        ("21/ALHP", "Presostato de alta — circuito 2", "pressure"),
        ("22/ALHP", "Transmisor de alta — circuito 2", "pressure"),
        ("23/ALHP", "Fallo por alta presión — circuito 2", "pressure"),
        ("21/ALLP", "Presostato de baja — circuito 2", "pressure"),
        ("22/ALLP", "Transmisor de baja — circuito 2", "pressure"),
        ("31/ALHP", "Presostato de alta — circuito 3", "pressure"),
        ("32/ALHP", "Transmisor de alta — circuito 3", "pressure"),
        ("33/ALHP", "Fallo por alta presión — circuito 3", "pressure"),
        ("31/ALLP", "Presostato de baja — circuito 3", "pressure"),
        ("32/ALLP", "Transmisor de baja — circuito 3", "pressure"),
        ("41/ALHP", "Presostato de alta — recuperación", "pressure"),
        ("42/ALHP", "Transmisor de alta — recuperación", "pressure"),
        ("43/ALHP", "Fallo por alta presión — recuperación", "pressure"),
        ("41/ALLP", "Presostato de baja — recuperación", "pressure"),
        ("42/ALLP", "Transmisor de baja — recuperación", "pressure"),
    ]
    for code, title, profile in hp_lp:
        rows.append(E(code, title, profile, "CTRL", "3", "CLIMANAGER / TH-Tune", "circuit", "Se protege el circuito indicado.", "Lea juntos el número y el texto; no use solo uno.", aliases=(code.replace("/", " "),)))
    sensors = [
        (1, "temperatura exterior"), (2, "temperatura ambiente"), (3, "temperatura de mezcla"),
        (4, "temperatura de impulsión"), (5, "presión de condensador 1"), (6, "presión de condensador 2"),
        (8, "presión de condensador 3"), (9, "temperatura de quemador de gas"),
        (11, "humedad interior"), (12, "humedad exterior"), (13, "calidad de aire CO2"),
        (14, "calidad de aire VOC"), (17, "presión de condensación de recuperación"),
        (19, "humedad de impulsión"), (20, "humedad posterior"), (21, "temperatura de impulsión auxiliar"),
        (22, "temperatura de retorno de agua"), (23, "demanda de caudal de aire"),
        (24, "temperatura de retorno"), (25, "humedad de retorno"),
    ]
    for number, label in sensors:
        rows.append(E(f"{number}/AL P", f"Fallo de sonda: {label}", "sensor", "CTRL", "3-5", "CLIMANAGER / TH-Tune", "system", "Se deshabilita o protege la función dependiente de la entrada.", "Entrada abierta, en corto o fuera de rango."))
        rows.append(E(f"{number}/AL H", f"Valor alto: {label}", "sensor", "CTRL", "3-5", "CLIMANAGER / TH-Tune", "system", "Se aplica el límite configurado.", "Compare lectura, valor real y umbral."))
        rows.append(E(f"{number}/AL L", f"Valor bajo: {label}", "sensor", "CTRL", "3-5", "CLIMANAGER / TH-Tune", "system", "Se aplica el límite configurado.", "Compare lectura, valor real y umbral."))
    specials = [
        ("1/ALFi", "Fallo de estado del ventilador de impulsión", "fan"),
        ("2/ALFi", "Fallo grave del ventilador de impulsión", "fan"),
        ("3/ALFi", "Fallo de caudal del ventilador interior", "fan"),
        ("4/ALFi", "Alarma del driver del ventilador de impulsión", "inverter"),
        ("5/ALFi", "Sin comunicación con driver de impulsión", "communication"),
        ("6/ALFi", "Fallo de señales KL/flujo del ventilador de impulsión", "fan"),
        ("1/ALFr", "Alarma del driver del ventilador de retorno", "inverter"),
        ("2/ALFr", "Sin comunicación con driver de retorno", "communication"),
        ("3/ALFr", "Fallo de caudal del ventilador de retorno", "fan"),
        ("99/ALFS", "Filtros de aire sucios", "normal"),
        ("1/ALAF", "Parada por antihielo en evaporador", "sensor"),
        ("1/ALSM", "Detección de humo", "power"),
        ("1/ALFL", "Alarma por inundación", "drain"),
        ("1/ALPE", "Parada de emergencia exterior", "power"),
        ("1/ALPC", "Alarma de bomba de condensados", "drain"),
        ("1/ALrr", "Alarma del recuperador rotativo", "fan"),
        ("5/ALFU", "Alarma de fuga de refrigerante", "pressure"),
        ("1/ALFE", "Sin conexión con driver de ventilador exterior", "communication"),
        ("2/ALFE", "Alarma del driver de ventilador exterior", "inverter"),
    ]
    for code, title, profile in specials:
        rows.append(E(code, title, profile, "CTRL", "5", "CLIMANAGER / TH-Tune", "system", "La acción depende del elemento; confirme en pGD si está disponible.", "TH-Tune muestra número y texto alternándolos."))
    pages = {"alarm_access": "2-3", "alarm_table": "3-5", "history": "2", "commissioning": "PERSEA controls", "service_mode": "CLIMANAGER / pGD", "monitoring": "pGD / kiconex", "network": "PERSEA controls", "water": "Product controls", "board": "CLIMANAGER"}
    return make_config(slug="keyter", brand_id=27, name="Keyter", display_name="Keyter", family_small="PERSEA / CLIMANAGER", family_large="TH-Tune / pGD / kiconex", controller_name="CLIMANAGER / TH-Tune / pGD", scope="Rooftops, autónomos y climatización industrial Keyter.", sources=sources, errors=rows, pages=pages, notes="Keyter Referencia V1: lectura combinada número/texto TH-Tune, presión por circuito, sondas, ventiladores, humo, condensados y CLIMANAGER.")


def aermec_config() -> dict[str, Any]:
    guide = "https://global.aermec.com/site/wp-content/uploads/Aermec_Product_Guide_2018_NA60_EN.pdf"
    sources = {
        "MAIN": base.src("Aermec Product Guide — hydronic equipment and controls", "AERMEC-PRODUCT-GUIDE-2018", guide, "product_guide", "2018"),
        "CTRL": base.src("WFN/WFI/WFGN/WFGI control and alarm management", "AERMEC-WF-CONTROL", "https://global.aermec.com/en/focus-prodotto/series-wfn-wfi-wfgn-and-wfgi/", "official_web", "current"),
        "SERVICE": base.src("Aermec Hydronic Systems Guide", "AERMEC-HYDRONIC-GUIDE", "https://global.aermec.com/wp-content/uploads/2026/02/Aermec_Guida_Idronica_EN.pdf", "technical_guide", "2026"),
        "NRB": base.src("Aermec hydronic applications — NRB/NRL/ANL", "AERMEC-HYDRONIC-APPLICATIONS", "https://global.aermec.com/dwnld/?id=8468", "technical_brochure", "current"),
    }
    # La documentación pública revisada describe alarmas textuales, no una
    # numeración universal. Se publican mensajes buscables sin inventar códigos.
    messages = [
        ("LOW EVAPORATOR PRESSURE", "Presión baja de evaporación", "pressure", "circuit"),
        ("HIGH CONDENSER PRESSURE", "Presión alta de condensación", "pressure", "circuit"),
        ("EVAPORATOR FLOW ALARM", "Fallo de caudal del evaporador", "pressure", "system"),
        ("CONDENSER FLOW ALARM", "Fallo de caudal del condensador", "pressure", "system"),
        ("FREEZE PROTECTION", "Protección antihielo", "sensor", "system"),
        ("COMPRESSOR THERMAL", "Protección térmica del compresor", "compressor", "circuit"),
        ("HIGH DISCHARGE TEMPERATURE", "Temperatura de descarga alta", "sensor", "circuit"),
        ("LOW WATER TEMPERATURE", "Temperatura de agua demasiado baja", "sensor", "system"),
        ("HIGH WATER TEMPERATURE", "Temperatura de agua demasiado alta", "sensor", "system"),
        ("INLET WATER SENSOR", "Fallo de sonda de entrada de agua", "sensor", "system"),
        ("OUTLET WATER SENSOR", "Fallo de sonda de salida de agua", "sensor", "system"),
        ("OUTDOOR AIR SENSOR", "Fallo de sonda exterior", "sensor", "system"),
        ("PRESSURE TRANSDUCER", "Fallo de transductor de presión", "sensor", "circuit"),
        ("EXV DRIVER OFFLINE", "Driver de expansión electrónica sin comunicación", "communication", "circuit"),
        ("PUMP 1 FAILURE", "Fallo de bomba 1", "power", "unit"),
        ("PUMP 2 FAILURE", "Fallo de bomba 2", "power", "unit"),
        ("MASTER SLAVE COMMUNICATION", "Fallo de comunicación maestro/esclavo", "communication", "system"),
        ("RS485 COMMUNICATION", "Fallo de comunicación RS485", "communication", "system"),
        ("PHASE MONITOR", "Fallo del monitor de fases", "power", "system"),
        ("DIRTY FILTER", "Aviso de filtro sucio", "normal", "system"),
        ("MAINTENANCE COMPRESSOR", "Mantenimiento de compresor", "normal", "circuit"),
        ("MAINTENANCE PUMP", "Mantenimiento de bomba", "normal", "unit"),
        ("EEPROM ERROR", "Fallo de memoria/configuración", "pcb", "system"),
        ("CLOCK ERROR", "Fallo de reloj", "pcb", "system"),
        ("UNIT CONFIGURATION", "Configuración de unidad incorrecta", "configuration", "system"),
    ]
    rows = [E(code, title, profile, "CTRL", "Control / alarm management", "Aermec hydronic controller", scope, "", "Mensaje textual: confirme el software y el manual específico de la unidad.") for code, title, profile, scope in messages]
    pages = {"alarm_access": "Control / alarm menu", "alarm_table": "Alarm management", "history": "Alarm log", "commissioning": "Product installation guide", "service_mode": "Control menu", "monitoring": "Control / AERNET", "network": "RS485 / Master-Slave", "water": "Hydronic guide", "board": "Control configuration"}
    return make_config(slug="aermec", brand_id=28, name="Aermec", display_name="Aermec", family_small="ANL / NRL / NRB / Moducontrol", family_large="WFN/WFI/WFGN/WFGI / pCO5", controller_name="Moducontrol / Aermec hydronic control / pGD1", scope="Enfriadoras y bombas de calor hidrónicas Aermec.", sources=sources, errors=rows, pages=pages, notes="Aermec Referencia V1: mensajes textuales de Moducontrol y control hidrónico, alarmas e histórico, pCO5, AERNET, Master/Slave y RS485. No se asignan números universales no publicados.")


def systemair_config() -> dict[str, Any]:
    sysaer = "https://shop.systemair.com/upload/assets/UM_AER_01-N-1GB.PDF"
    sources = {
        "MAIN": base.src("SysAer Regulation Manual", "UM_AER_01-N-1GB", sysaer, "control_manual", "2025"),
        "CTRL": base.src("Systemair Access — alarm documentation", "SYSTEMAIR-ACCESS-ALARMS", "https://access.systemair.com/Browsingalarms1.html", "official_web", "current"),
        "SERVICE": base.src("Systemair Access — reviewing alarms", "SYSTEMAIR-ACCESS-REVIEW", "https://access.systemair.com/Reviewingalarms.html", "official_web", "current"),
        "TOPVEX": base.src("Topvex Access operation and maintenance", "TOPVEX-ACCESS-IOM", "https://shop.systemair.com/upload/assets/INSTALLATION__OPERATION_AND_MAINTENANCE_INSTRUCTION_TOPVEX_SR__TR__EN_004.PDF", "iom", "2025"),
    }
    rows: list[dict[str, Any]] = []
    sysaer_rows = [
        ("AL01", "Térmico de compresores/ventiladores — circuito 1", "power", "circuit", "Se detiene el circuito 1."),
        ("AL02", "Térmico de compresores/ventiladores — circuito 2", "power", "circuit", "Se detiene el circuito 2."),
        ("AL03", "Bloqueo de alta presión — circuito 1", "pressure", "circuit", "Se detiene el circuito 1; rearme manual."),
        ("AL04", "Bloqueo de alta presión — circuito 2", "pressure", "circuit", "Se detiene el circuito 2; rearme manual."),
        ("AL05", "Antihielo de batería de agua caliente", "sensor", "system", "Cierra economizador y abre válvula de agua caliente."),
        ("AL06", "Temperatura ambiente alta", "sensor", "system", "Solo visualización."),
        ("AL07", "Temperatura ambiente baja", "sensor", "system", "Solo visualización."),
        ("AL08", "Bloqueo de baja presión — circuito 1", "pressure", "circuit", "Se detiene el circuito 1."),
        ("AL09", "Bloqueo de baja presión — circuito 2", "pressure", "circuit", "Se detiene el circuito 2."),
        ("AL15", "Bloqueo térmico del ventilador principal", "fan", "system", "Parada general."),
        ("AL16", "Filtro sucio", "normal", "system", "Aviso sin parada."),
        ("AL17", "Consigna verano menor que consigna invierno menos 2", "configuration", "system", "Se desactiva cambio automático."),
        ("AL18", "Fallo del presostato de aire", "fan", "system", "Parada general."),
        ("AL19", "Reloj averiado o ausente", "pcb", "system", "Solo visualización."),
        ("AL20", "Fallo de sonda B1", "sensor", "system", "Puede detener la función necesaria para EEV1."),
        ("AL21", "Fallo de sonda B2", "sensor", "system", "Puede detener la función necesaria para EEV2."),
        ("AL22", "Fallo de sonda B3 OCT1", "sensor", "circuit", "Detiene circuito 1 en invierno."),
        ("AL23", "Fallo de sonda B4 OCT2", "sensor", "circuit", "Detiene circuito 2 en invierno."),
        ("AL24", "Fallo de sonda B5 / detector de humo", "sensor", "system", "Detiene las funciones asociadas."),
        ("AL25", "Fallo de sonda B6 RAT", "sensor", "system", "Parada general."),
    ]
    for code, title, profile, scope, behavior in sysaer_rows:
        rows.append(E(code, title, profile, "MAIN", "36-alarms", "SysAer / CAREL", scope, behavior, "La tabla indica acción, rearme y retardo."))
    access_rows = [
        (11, "Alarma del ventilador de impulsión 1", "fan"),
        (12, "Alarma del ventilador de impulsión 2", "fan"),
        (16, "Alarma del ventilador de extracción 1", "fan"),
        (17, "Alarma del ventilador de extracción 2", "fan"),
        (35, "Fallo de bomba de calefacción", "power"),
        (36, "Fallo de bomba de refrigeración", "power"),
        (37, "Fallo de bomba del intercambiador", "power"),
        (38, "Fallo de compuerta cortafuegos", "valve"),
        (39, "Fallo de compuerta", "valve"),
        (43, "Fallo de calefacción SEQ-A", "power"),
        (44, "Fallo de intercambiador SEQ-B", "power"),
        (45, "Fallo de refrigeración SEQ-C", "power"),
        (46, "Fallo de recirculación 1 SEQ-D", "power"),
        (47, "Fallo de recirculación 2 SEQ-E", "power"),
        (48, "Fallo de compensación de consigna de ventilador", "fan"),
        (49, "Fallo de calefacción 2 SEQ-G", "power"),
        (50, "Fallo de refrigeración 2 SEQ-H", "power"),
        (51, "Fallo de intercambiador de extracción SEQ-I", "power"),
        (168, "Error de señal externa de control del ventilador de impulsión", "sensor"),
        (238, "Alarma de dispositivo interno", "communication"),
        (1000, "Filtro de impulsión sucio", "normal"),
        (1105, "Alarma de desescarche", "sensor"),
        (4005, "Fallo del motor del ventilador adicional 1", "fan"),
    ]
    for number, title, profile in access_rows:
        rows.append(E(str(number), title, profile, "CTRL", "Access alarm list", "Access / NaviPad", "system", "La acción y clase A/B/C son configurables.", "Busque el identificador en la lista categorizada."))
    pages = {"alarm_access": "Access alarm list / SysAer 36", "alarm_table": "SysAer 36-alarms / Access list", "history": "SysAer alarm history / Access reviewing alarms", "commissioning": "Topvex first start", "service_mode": "Access configuration", "monitoring": "Access Unit information", "network": "Topvex Access connect", "water": "SysAer alarm table", "board": "Access system information"}
    return make_config(slug="systemair", brand_id=29, name="Systemair", display_name="Systemair", family_small="SysAer rooftop", family_large="Topvex / Access / NaviPad", controller_name="Access / NaviPad / CAREL", scope="Rooftops, climatizadores, ventilación y enfriadoras Systemair.", sources=sources, errors=rows, pages=pages, notes="Systemair Referencia V1: SysAer ALxx, Access por identificador, NaviPad, alarmas configurables, ventilación y redundancia.")


def mcquay_config() -> dict[str, Any]:
    csm = "https://tahoeweb.daikinapplied.com/api/general/DownloadDocumentByName/media/OM_780-3.pdf/"
    sources = {
        "MAIN": base.src("McQuay MicroTech II Chiller System Manager", "OM-780-3", csm, "operation_manual", "2007"),
        "CTRL": base.src("McQuay MicroTech II Vertical Self-Contained Unit Controller", "IM-710-2", "https://tahoeweb.daikinapplied.com/api/general/DownloadDocumentByName/media/IM710_2.pdf/", "installation_manual", "2005"),
        "SERVICE": base.src("MicroTech II Water-Cooled Scroll Chiller", "IOM-1322-1", "https://tahoeweb.daikinapplied.com/api/general/DownloadDocumentByName/media/IOM1322.pdf/", "iom", "historical"),
        "BACNET": base.src("MicroTech II Chiller BACnet IP Communication", "IM-837-6", "https://tahoeweb.daikinapplied.com/api/general/DownloadDocumentByName/media/Daikin_IM_837-6_MicroTech_II_Chiller_BACnet_IP_Comm_Manual%2001-28-26.pdf/", "communication_manual", "2026"),
    }
    messages = [
        ("COMM LOSS", "Pérdida de comunicación con una enfriadora", "communication", "system", "Una enfriadora que estaba funcionando no se detiene automáticamente solo por perder CSM."),
        ("LOW EVAPORATOR PRESSURE", "Presión baja del evaporador", "pressure", "system", "Fallo de parada que debe borrarse localmente en el controlador."),
        ("HIGH CONDENSER PRESSURE SENSOR", "Alta presión de condensador por sensor", "pressure", "system", "Fallo de parada; no se borra desde CSM."),
        ("HIGH CONDENSER PRESSURE SWITCH", "Alta presión de condensador por presostato", "pressure", "system", "Fallo de parada; no se borra desde CSM."),
        ("LOW OIL PRESSURE", "Presión de aceite baja", "pressure", "system", "Fallo de parada; no se borra desde CSM."),
        ("FREEZE PROTECTION", "Protección antihielo", "sensor", "system", "Fallo de parada; no se borra desde CSM."),
        ("HIGH MOTOR TEMPERATURE", "Temperatura alta del motor", "sensor", "system", "Fallo de parada; no se borra desde CSM."),
        ("EVAPORATOR FLOW LOSS", "Pérdida de caudal del evaporador", "pressure", "system", "Se detiene la producción para proteger el intercambiador."),
        ("CONDENSER FLOW LOSS", "Pérdida de caudal del condensador", "pressure", "system", "Se detiene o limita la enfriadora."),
        ("PHASE VOLTAGE ALARM", "Fallo de fase o tensión", "power", "system", "Se inhibe el arranque o se detiene la unidad."),
        ("COMPRESSOR OVERLOAD", "Sobrecarga de compresor", "compressor", "circuit", "Se detiene el compresor/circuito afectado."),
        ("DISCHARGE TEMPERATURE HIGH", "Temperatura de descarga alta", "sensor", "circuit", "Se detiene el circuito afectado."),
        ("SUCTION TEMPERATURE SENSOR", "Fallo de sonda de aspiración", "sensor", "circuit", "Se protege el circuito asociado."),
        ("LEAVING WATER SENSOR", "Fallo de sonda de salida de agua", "sensor", "system", "Se pierde la referencia principal de control."),
        ("ENTERING WATER SENSOR", "Fallo de sonda de entrada de agua", "sensor", "system", "Se limita monitorización y secuencias asociadas."),
        ("OUTDOOR AIR SENSOR", "Fallo de sonda de aire exterior", "sensor", "system", "Se desactivan compensaciones dependientes."),
        ("CONTROLLER COMMUNICATION", "Comunicación entre placas MicroTech II", "communication", "system", "Se pierde el módulo o circuito asociado."),
        ("BAS COMMUNICATION", "Pérdida de comunicación BACnet/Modbus", "communication", "system", "El control local puede continuar; confirme permisos y consignas."),
        ("ALARM LOG FULL", "Registro de alarmas lleno", "normal", "system", "Aviso de gestión; conserve y exporte la secuencia."),
        ("REAL TIME CLOCK", "Fallo de reloj en tiempo real", "pcb", "system", "Puede afectar horarios y fecha de alarmas."),
        ("CONFIGURATION ERROR", "Configuración de unidad incorrecta", "configuration", "system", "Puede impedir el arranque."),
        ("NETWORK ADDRESS DUPLICATE", "Dirección de red duplicada", "configuration", "system", "Se pierde comunicación estable."),
        ("PUMP 1 FAILURE", "Fallo de bomba 1", "power", "unit", "Se usa la bomba disponible o se detiene el sistema."),
        ("PUMP 2 FAILURE", "Fallo de bomba 2", "power", "unit", "Se usa la bomba disponible o se detiene el sistema."),
        ("CHILLER NOT AVAILABLE", "Enfriadora no disponible para secuencia", "normal", "unit", "El gestor intenta cubrir carga con otra unidad."),
    ]
    rows = [E(code, title, profile, "MAIN" if code in {"COMM LOSS", "LOW EVAPORATOR PRESSURE", "HIGH CONDENSER PRESSURE SENSOR", "HIGH CONDENSER PRESSURE SWITCH", "LOW OIL PRESSURE", "FREEZE PROTECTION", "HIGH MOTOR TEMPERATURE"} else "SERVICE", "105-110 / alarm diagnostics", "McQuay MicroTech II", scope, behavior, "Mensaje textual histórico; confirme plataforma MicroTech II exacta.") for code, title, profile, scope, behavior in messages]
    pages = {"alarm_access": "105-110", "alarm_table": "105-110 / alarm diagnostics", "history": "105-110", "commissioning": "IOM start-up", "service_mode": "MicroTech II test mode", "monitoring": "CSM status and Misc", "network": "CSM architecture / BACnet", "water": "IOM equipment protection", "board": "Controller software/configuration"}
    provenance = {
        "policy": "Solo equipos documentados originalmente como McQuay o MicroTech II de la etapa histórica.",
        "accepted": [{"status": "accepted_historic_mcquay", "families": ["MicroTech II CSM", "Vertical Self-Contained", "Water-Cooled Scroll"]}],
        "excluded": [{"status": "excluded", "reason": "No duplicar equipos Daikin Applied modernos que ya no se identifican como McQuay."}],
    }
    return make_config(slug="mcquay-historica", brand_id=30, name="McQuay", display_name="McQuay (histórica)", family_small="McQuay MicroTech II unitario", family_large="MicroTech II Chiller System Manager", controller_name="MicroTech II / CSM", scope="Equipos históricos McQuay con control MicroTech II.", sources=sources, errors=rows, pages=pages, notes="McQuay histórica Referencia V1: MicroTech II, CSM, alarmas textuales, borrado local, red y secuenciación.", provenance=provenance)


CONFIG_FACTORIES = {
    "carrier": carrier_config,
    "york": york_config,
    "ciat": ciat_config,
    "trane": trane_config,
    "lennox": lennox_config,
    "hitecsa": hitecsa_config,
    "keyter": keyter_config,
    "aermec": aermec_config,
    "systemair": systemair_config,
    "mcquay-historica": mcquay_config,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("brands", nargs="*", choices=sorted(CONFIG_FACTORIES))
    args = parser.parse_args()
    brands = args.brands or list(CONFIG_FACTORIES)
    original = base.CONFIG_FACTORIES
    try:
        base.CONFIG_FACTORIES = CONFIG_FACTORIES
        result = {slug: base.build_one(slug) for slug in brands}
    finally:
        base.CONFIG_FACTORIES = original
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
