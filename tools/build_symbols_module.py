#!/usr/bin/env python3
"""Build the public symbol library and course data from the reviewed source."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "symbols" / "source.json"
PROFESSIONAL_EXPANSION = ROOT / "data" / "symbols" / "professional-expansion.json"
OUT = ROOT / "data" / "symbols"
ASSETS = ROOT / "assets" / "symbols"


def slug(text: str) -> str:
    replacements = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    return re.sub(r"[^a-z0-9]+", "-", text.translate(replacements).lower()).strip("-")


def symbol_svg(title: str, kind: str, terminals: str = "") -> str:
    label = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    terminal_label = terminals.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    drawings = {
        "no_connect": '<path d="M35 70h42"/><path d="M77 59l22 22m0-22L77 81"/>',
        "net_tie": '<path d="M28 70h42m40 0h42"/><rect x="70" y="61" width="40" height="18" rx="4"/><text x="90" y="75">NT</text>',
        "kelvin": '<path d="M24 48h55m0 0h55M24 92h55m0 0h55"/><circle cx="79" cy="48" r="4"/><circle cx="79" cy="92" r="4"/><path d="M79 48v44"/>',
        "barrier": '<rect x="37" y="40" width="42" height="60" rx="5"/><rect x="121" y="40" width="42" height="60" rx="5"/><path d="M92 30v80m16-80v80" stroke-dasharray="5 5"/><path d="M20 70h17m42 0h42m42 0h17"/>',
        "dependent_v": '<path d="M100 28l52 42-52 42-52-42z"/><text x="100" y="62">+</text><text x="100" y="88">−</text><path d="M20 70h28m104 0h28"/>',
        "dependent_i": '<path d="M100 28l52 42-52 42-52-42z"/><path d="M100 88V51m0 0l-10 12m10-12l10 12"/><path d="M20 70h28m104 0h28"/>',
        "probe_v": '<path d="M25 70h60"/><circle cx="110" cy="70" r="25"/><text x="110" y="77">V</text><path d="M85 70h-8m58 0h40"/>',
        "probe_i": '<path d="M25 70h60"/><circle cx="110" cy="70" r="25"/><text x="110" y="77">A</text><path d="M85 70h-8m58 0h40"/>',
        "ptc_fuse": '<path d="M25 70h45m60 0h45"/><rect x="70" y="58" width="60" height="24"/><path d="M82 88l36-36"/><text x="100" y="105">PTC</text>',
        "spark": '<path d="M25 70h55l10-13m20 26l10-13h55"/><path d="M96 49l8 9-9 5 9 9-8 9"/>',
        "coil": '<path d="M20 70h35c0-18 22-18 22 0s22 18 22 0 22-18 22 0 22 18 22 0h37"/>',
        "sensor": '<circle cx="100" cy="70" r="42"/><path d="M58 70H20m160 0h-38"/><path d="M77 86l14-34 13 34 15-34"/>',
        "motor": '<circle cx="100" cy="70" r="42"/><text x="100" y="78">M</text><path d="M20 70h38m84 0h38"/>',
        "compressor": '<circle cx="100" cy="70" r="44"/><text x="100" y="64">COMP</text><text x="100" y="84">C R S</text><path d="M20 70h36m88 0h36"/>',
        "protector": '<path d="M20 70h45m70 0h45"/><rect x="65" y="48" width="70" height="44" rx="20"/><text x="100" y="76">TH</text>',
        "semiconductor": '<path d="M20 70h40m80 0h40"/><rect x="60" y="35" width="80" height="70" rx="6"/><text x="100" y="65">POWER</text><text x="100" y="84">DEVICE</text>',
        "opto_pv": '<rect x="45" y="38" width="110" height="64" rx="5"/><path d="M93 34v72" stroke-dasharray="5 5"/><path d="M58 70h24m36 0h24"/><path d="M78 55l14 10m-14 20l14-10"/><path d="M107 54v32m14-26v20"/>',
        "module": '<path d="M20 70h35m90 0h35"/><rect x="55" y="32" width="90" height="76" rx="8"/><text x="100" y="65">MODULE</text><text x="100" y="86">POWER</text>',
        "signal": '<path d="M20 70h45m70 0h45"/><rect x="65" y="42" width="70" height="56" rx="6"/><text x="100" y="68">SIGNAL</text><text x="100" y="87">I/O</text>',
        "bus": '<path d="M20 50h40m80 0h40M20 90h40m80 0h40"/><rect x="60" y="30" width="80" height="80" rx="7"/><text x="100" y="65">BUS</text><text x="100" y="86">DATA</text>',
        "controller_block": '<path d="M20 45h35m90 0h35M20 70h35m90 0h35M20 95h35m90 0h35"/><rect x="55" y="27" width="90" height="86" rx="7"/><path d="M72 43h56M72 58h56M72 73h35M72 88h45"/><text x="100" y="106">CTRL</text>',
        "drive_block": '<path d="M20 45h35m-35 25h35m-35 25h35m90-50h35m-35 25h35m-35 25h35"/><rect x="55" y="27" width="90" height="86" rx="7"/><path d="M72 91l18-42 20 42 18-42"/><text x="100" y="108">DRIVE</text>',
        "building_control": '<path d="M20 50h35m-35 40h35m90-40h35m-35 40h35"/><rect x="55" y="28" width="90" height="84" rx="7"/><path d="M72 91V58l28-18 28 18v33M84 91V71h32v20"/><text x="100" y="106">BMS</text>',
    }
    drawing = drawings[kind]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 150" role="img" aria-labelledby="title desc">
<title id="title">{label}</title><desc id="desc">Representación didáctica: {label}</desc>
<rect width="200" height="150" fill="#f8fafc"/><g fill="none" stroke="#132f3f" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">{drawing}</g>
<g fill="#132f3f" font-family="Arial,sans-serif" font-size="13" font-weight="700" text-anchor="middle"><text x="100" y="18">{label}</text>{f'<text x="100" y="137">{terminal_label}</text>' if terminal_label else ''}</g></svg>'''


def new_symbol(number: int, name: str, category: str, subcategory: str, kind: str, **fields: str) -> dict:
    ident = f"SYM-{number:04d}"
    filename = f"{ident}_{slug(name)}.svg"
    record = {
        "id": ident,
        "nombre": name,
        "alias": fields.get("alias", ""),
        "categoria": category,
        "subcategoria": subcategory,
        "tipo_dibujo": kind,
        "variante": fields.get("variante", "Representación funcional"),
        "designador": fields.get("designador", ""),
        "norma": fields.get("norma", "Común / educativa"),
        "nivel": fields.get("nivel", "Intermedio"),
        "descripcion": fields.get("descripcion", ""),
        "interpretacion": fields.get("interpretacion", ""),
        "terminales": fields.get("terminales", ""),
        "errores_comunes": fields.get("errores_comunes", ""),
        "aplicaciones": fields.get("aplicaciones", ""),
        "relacionados": fields.get("relacionados", ""),
        "etiquetas": fields.get("etiquetas", ""),
        "climatizacion": fields.get("climatizacion", "No"),
        "fuente": fields.get("fuente", "https://gitlab.com/kicad/libraries/kicad-symbols/"),
        "label": fields.get("label", name),
        "archivo_svg": f"assets/symbols/{filename}",
        "archivo_png": "",
    }
    (ASSETS / filename).write_text(symbol_svg(name, kind, record["terminales"]), encoding="utf-8")
    return record


EXTRA = [
    (428, "Marca de no conectado", "Conexiones y referencias", "Conectividad", "no_connect", dict(alias="NC, no connect, pin sin usar", designador="NC", nivel="Básico", descripcion="Indica que un terminal se deja intencionadamente sin conexión.", interpretacion="La cruz señala una decisión de diseño, no una pista rota.", terminales="Terminal marcado", errores_comunes="Confundirlo con un punto de prueba o una rotura.", aplicaciones="Pines no usados de circuitos integrados", etiquetas="nc no conectado pin libre")),
    (429, "Net tie / unión controlada de redes", "Conexiones y referencias", "Nodos", "net_tie", dict(alias="net tie, unión de masas", designador="NT", descripcion="Une dos redes con nombres distintos en un punto físico controlado.", interpretacion="Permite separar masas o dominios en el esquema y unirlos en una ubicación concreta.", terminales="Red A y red B", errores_comunes="Eliminarla o puentear redes en otro punto creando bucles.", aplicaciones="AGND/DGND, potencia y señal", etiquetas="net tie masas union controlada")),
    (430, "Conexión Kelvin de cuatro hilos", "Conexiones y referencias", "Medida", "kelvin", dict(alias="Kelvin, four-wire, sense", descripcion="Separa los conductores de corriente de los de medida para evitar la caída de los cables.", interpretacion="Los dos hilos finos de sense llegan directamente a los extremos del elemento medido.", terminales="I+, I−, S+, S−", errores_comunes="Unir sense lejos del shunt o compartir pista de potencia.", aplicaciones="Shunts, resistencias de precisión, fuentes remotas", etiquetas="kelvin 4 hilos sense shunt medida")),
    (431, "Barrera de aislamiento galvánico", "Conexiones y referencias", "Aislamiento", "barrier", dict(alias="isolation barrier, barrera primaria secundaria", descripcion="Marca una separación sin conexión conductora directa entre dominios eléctricos.", interpretacion="Toda señal que cruza la barrera debe hacerlo mediante un elemento de aislamiento.", errores_comunes="Medir ambos lados con una masa común o unirlos accidentalmente.", aplicaciones="Fuentes conmutadas, comunicaciones aisladas", etiquetas="barrera aislamiento primario secundario seguridad", relacionados="Optoacoplador, transformador digital")),
    (432, "Fuente de tensión dependiente", "Fuentes y alimentación", "Fuentes controladas", "dependent_v", dict(alias="VCVS, CCVS, fuente controlada", designador="E/H", descripcion="Fuente cuyo valor depende de otra tensión o corriente del circuito.", interpretacion="La relación de control se indica junto al rombo o mediante una ecuación.", terminales="Salida +/− y variable de control", aplicaciones="Modelos equivalentes y simulación", etiquetas="fuente dependiente controlada tension vcvs ccvs")),
    (433, "Fuente de corriente dependiente", "Fuentes y alimentación", "Fuentes controladas", "dependent_i", dict(alias="VCCS, CCCS, fuente controlada", designador="G/F", descripcion="Fuente de corriente gobernada por otra magnitud del circuito.", interpretacion="La flecha define el sentido de referencia de la corriente de salida.", terminales="Salida y variable de control", aplicaciones="Modelos de transistores y amplificadores", etiquetas="fuente dependiente controlada corriente vccs cccs")),
    (434, "Sonda de tensión", "Medida e indicación", "Sondas", "probe_v", dict(alias="voltage probe, punto de medida", designador="TP", nivel="Básico", descripcion="Indica un nodo previsto para medir tensión respecto a una referencia definida.", interpretacion="Comprueba siempre la masa o referencia indicada antes de medir.", terminales="Punto y referencia", errores_comunes="Usar PE o chasis como referencia cuando el nodo está aislado.", aplicaciones="Diagnóstico y osciloscopio", etiquetas="sonda tension probe medida referencia")),
    (435, "Sonda de corriente", "Medida e indicación", "Sondas", "probe_i", dict(alias="current probe, lazo de corriente", designador="IP", nivel="Básico", descripcion="Representa un punto o lazo previsto para observar la corriente de una rama.", interpretacion="La flecha o polaridad define el signo de la lectura.", terminales="Rama medida", errores_comunes="Abrir un circuito energizado para insertar el instrumento sin procedimiento seguro.", aplicaciones="Diagnóstico, pinza y sonda de corriente", etiquetas="sonda corriente probe medida")),
    (436, "Fusible rearmable PTC", "Protecciones eléctricas", "Sobrecorriente", "ptc_fuse", dict(alias="polyfuse, PPTC, polyswitch", designador="F/RT", descripcion="Protección resistiva que aumenta fuertemente su resistencia al calentarse por sobrecorriente.", interpretacion="No se abre como un fusible convencional; queda en alta resistencia hasta enfriarse.", terminales="Entrada y salida", errores_comunes="Dar por bueno el componente porque tiene continuidad en frío.", aplicaciones="USB, baterías y baja tensión", etiquetas="pptc polyfuse fusible rearmable ptc")),
    (437, "Descargador de chispa", "Protecciones eléctricas", "Sobretensión", "spark", dict(alias="spark gap, gap de descarga", designador="SG", descripcion="Dos electrodos separados que conducen al superar su tensión de cebado.", interpretacion="Normalmente está abierto y deriva impulsos de alta energía al producirse el arco.", terminales="Dos electrodos", errores_comunes="Confundir la separación prevista con una pista dañada.", aplicaciones="Entrada de red, alta tensión y protección de transitorios", etiquetas="spark gap chispa arco sobretension")),
    (438, "Bobina Rogowski", "Sensores y transductores", "Corriente", "coil", dict(alias="Rogowski coil, sensor de corriente flexible", designador="CT", descripcion="Bobina sin núcleo ferromagnético que entrega una señal proporcional a la derivada de corriente.", interpretacion="Necesita integrador o acondicionamiento para reconstruir la corriente.", terminales="Bobina e integrador", errores_comunes="Interpretar la salida directamente como corriente sin integrar.", aplicaciones="Corrientes AC y pulsos de potencia", etiquetas="rogowski corriente bobina integrador")),
    (439, "Sensor de corriente aislado por shunt", "Sensores y transductores", "Corriente", "sensor", dict(alias="isolated shunt current sensor", designador="U/RSH", descripcion="Mide la caída en un shunt y transmite el valor a través de aislamiento.", interpretacion="Distingue el lado de potencia del lado lógico y sus alimentaciones separadas.", terminales="IN+, IN−, alimentación primaria/secundaria, OUT", errores_comunes="Referir la salida a la masa del shunt.", aplicaciones="Inverter, PFC y accionamientos", etiquetas="shunt aislado sensor corriente inverter", climatizacion="Sí")),
    (440, "Encoder absoluto", "Sensores y transductores", "Posición", "sensor", dict(alias="absolute encoder, SSI, BiSS", designador="ENC", descripcion="Entrega una palabra digital única para cada posición angular.", interpretacion="A diferencia del incremental conserva la posición sin contar pulsos desde cero.", terminales="Alimentación, datos y reloj/bus", errores_comunes="Confundir códigos Gray y binario o invertir líneas diferenciales.", aplicaciones="Servos y posicionamiento", etiquetas="encoder absoluto posicion gray ssi biss")),
    (441, "Resolver", "Sensores y transductores", "Posición", "sensor", dict(alias="resolver síncrono, sin/cos", designador="RES", descripcion="Transductor rotativo que entrega señales seno y coseno relacionadas con el ángulo.", interpretacion="Requiere excitación y un convertidor resolver-digital.", terminales="Excitación, SIN, COS", errores_comunes="Medir sin considerar amplitud, fase y referencia de excitación.", aplicaciones="Motores industriales y servos", etiquetas="resolver sin cos posicion motor")),
    (442, "Motor PSC con condensador permanente", "Máquinas y actuadores", "Motores AC", "motor", dict(alias="permanent split capacitor, motor condensador", designador="M", descripcion="Motor monofásico con bobinado auxiliar y condensador conectado de forma permanente.", interpretacion="El esquema muestra bobinado principal, auxiliar y condensador de marcha.", terminales="Común, marcha, auxiliar y condensador", errores_comunes="Cambiar el condensador sin comprobar bobinados y alimentación.", aplicaciones="Ventiladores y bombas", etiquetas="motor psc condensador permanente ventilador", climatizacion="Sí")),
    (443, "Motor de polo sombreado", "Máquinas y actuadores", "Motores AC", "motor", dict(alias="shaded pole motor", designador="M", descripcion="Motor monofásico sencillo cuyo anillo de sombra crea el desfase de arranque.", interpretacion="Normalmente no utiliza condensador ni bobinado auxiliar accesible.", terminales="Alimentación AC", errores_comunes="Buscar un condensador de marcha inexistente.", aplicaciones="Ventiladores pequeños", etiquetas="motor polo sombreado ventilador")),
    (444, "Motor EC", "Máquinas y actuadores", "Motores electrónicos", "motor", dict(alias="electronically commutated motor, ECM", designador="M", descripcion="Motor BLDC con electrónica de conmutación integrada.", interpretacion="Además de potencia puede recibir una orden 0-10 V, PWM o bus.", terminales="Potencia, referencia y control", errores_comunes="Probarlo como un motor AC convencional sin identificar la entrada de mando.", aplicaciones="Ventiladores HVAC y bombas", etiquetas="motor ec ecm bldc integrado control", climatizacion="Sí")),
    (445, "Compresor monofásico C-R-S", "Máquinas y actuadores", "Compresores", "compressor", dict(alias="common run start, compresor hermético monofásico", designador="COMP", nivel="Básico", descripcion="Representa los terminales común, marcha y arranque de un compresor monofásico.", interpretacion="La mayor resistencia suele medirse entre R y S; C-R y C-S corresponden a cada bobinado.", terminales="C, R, S", errores_comunes="Identificar terminales solo por posición física o energizar sin protección.", aplicaciones="Climatización y refrigeración", etiquetas="compresor C R S comun marcha arranque", climatizacion="Sí")),
    (446, "PTC de arranque de compresor", "Potencia y climatización", "Arranque de compresor", "ptc_fuse", dict(alias="relé PTC de arranque, posistor", designador="PTC", descripcion="Alimenta inicialmente el bobinado de arranque y eleva su resistencia al calentarse.", interpretacion="En frío conduce; tras el arranque reduce la corriente del bobinado auxiliar.", terminales="Línea, marcha y arranque según conjunto", errores_comunes="Rearmar repetidamente sin dejarlo enfriar o confundirlo con protector térmico.", aplicaciones="Compresores monofásicos", etiquetas="ptc arranque compresor posistor", climatizacion="Sí")),
    (447, "Protector térmico Klixon", "Protecciones eléctricas", "Protección térmica", "protector", dict(alias="overload, klixon, protector compresor", designador="OL", descripcion="Contacto térmico que abre por temperatura o sobrecorriente.", interpretacion="Puede rearmarse automáticamente al enfriarse y aparentar una avería intermitente.", terminales="Entrada y salida", errores_comunes="Medir continuidad cuando aún está caliente o puentearlo para prueba prolongada.", aplicaciones="Compresores y motores", etiquetas="klixon overload termico compresor", climatizacion="Sí")),
    (448, "MOSFET SiC canal N", "Semiconductores discretos", "Semiconductores de banda ancha", "semiconductor", dict(alias="silicon carbide MOSFET", designador="Q", descripcion="MOSFET de carburo de silicio para alta tensión y conmutación rápida.", interpretacion="El símbolo puede añadir diodo de cuerpo; verifica tensiones de puerta y condiciones del fabricante.", terminales="G, D, S", errores_comunes="Sustituirlo por silicio sin revisar driver, pérdidas y sobretensiones.", aplicaciones="PFC, inverter y fuentes de potencia", etiquetas="sic mosfet carburo silicio potencia", climatizacion="Sí")),
    (449, "Transistor GaN HEMT", "Semiconductores discretos", "Semiconductores de banda ancha", "semiconductor", dict(alias="gallium nitride HEMT, eGaN", designador="Q", descripcion="Transistor de nitruro de galio para conmutación de alta frecuencia.", interpretacion="La tensión de puerta admisible y la referencia Kelvin pueden ser críticas.", terminales="G, D, S", errores_comunes="Aplicar niveles de puerta propios de un MOSFET de silicio.", aplicaciones="Fuentes compactas y convertidores rápidos", etiquetas="gan hemt nitruro galio potencia")),
    (450, "MOSFET de deplexión canal N", "Semiconductores discretos", "MOSFET", "semiconductor", dict(alias="depletion mode MOSFET, normally on", designador="Q", descripcion="MOSFET normalmente conductor a VGS=0.", interpretacion="Necesita tensión de puerta adecuada para reducir o cortar la corriente.", terminales="G, D, S", errores_comunes="Tratarlo como un MOSFET de enriquecimiento normalmente abierto.", aplicaciones="Arranque de fuentes y fuentes de corriente", etiquetas="mosfet depletion deplexion normally on")),
    (451, "Optoacoplador fotovoltaico", "Optoelectrónica y aislamiento", "Optoacopladores", "opto_pv", dict(alias="photovoltaic optocoupler, photovoltaic isolator", designador="U", descripcion="Una matriz fotovoltaica aislada genera tensión para controlar una puerta MOSFET.", interpretacion="La salida entrega tensión con corriente pequeña y puede necesitar tiempo de descarga.", terminales="LED de entrada, salida fotovoltaica", errores_comunes="Esperar una conmutación tan rápida como la de un opto lógico.", aplicaciones="Relés MOSFET y high-side aislado", etiquetas="opto fotovoltaico aislador mosfet gate")),
    (452, "Módulo de tiristores SCR", "Potencia y climatización", "Módulos de potencia", "module", dict(alias="thyristor module, módulo SCR", designador="TM", descripcion="Encapsula uno o varios tiristores de potencia, a veces en configuración doble.", interpretacion="Comprueba el esquema interno: ánodo común, cátodo común o serie.", terminales="A, K y G por dispositivo", errores_comunes="Asumir el mismo conexionado interno en módulos de aspecto idéntico.", aplicaciones="Control de potencia y arrancadores", etiquetas="modulo scr tiristor potencia")),
    (453, "Módulo de diodos de potencia", "Potencia y climatización", "Módulos de potencia", "module", dict(alias="power diode module, dual diode", designador="DM", descripcion="Conjunto de diodos de potencia en un encapsulado aislado o de base conductora.", interpretacion="El dibujo interno determina polaridad y terminal común.", terminales="Ánodos y cátodos según topología", errores_comunes="No comprobar si la base está eléctricamente aislada.", aplicaciones="Rectificadores e inverter", etiquetas="modulo diodos potencia rectificador")),
    (454, "Lazo de corriente 4-20 mA", "Conectores y comunicaciones", "Señales industriales", "signal", dict(alias="current loop, 4-20mA", designador="AI/AO", descripcion="Interfaz analógica que representa la variable mediante corriente; 4 mA suele ser el cero vivo.", interpretacion="Distingue transmisor de dos, tres o cuatro hilos y quién alimenta el lazo.", terminales="Loop + y Loop −", errores_comunes="Medir como tensión sin resistencia de carga o invertir fuente y receptor.", aplicaciones="Sensores, PLC y control industrial", etiquetas="4-20ma current loop transmisor analogico")),
    (455, "Señal analógica 0-10 V", "Conectores y comunicaciones", "Señales industriales", "signal", dict(alias="0-10V, 2-10V control", designador="AI/AO", descripcion="Interfaz de mando analógico referida a una masa o común.", interpretacion="Comprueba si la entrada es 0-10 V o 2-10 V y si el común está aislado.", terminales="Signal y COM", errores_comunes="Unir comunes de equipos con distinto potencial.", aplicaciones="Ventiladores EC, variadores y válvulas", etiquetas="0-10v 2-10v señal analogica control", climatizacion="Sí")),
    (456, "Puerto UART", "Conectores y comunicaciones", "Servicio digital", "bus", dict(alias="serial TTL, TX RX", designador="UART", descripcion="Interfaz serie asíncrona de nivel lógico.", interpretacion="TX de un equipo suele conectarse a RX del otro y ambos comparten referencia si no hay aislamiento.", terminales="TX, RX, GND y opcional VCC", errores_comunes="Conectarlo directamente a RS-232 o usar una tensión lógica incorrecta.", aplicaciones="Diagnóstico, programación y módulos", etiquetas="uart serial ttl tx rx servicio")),
    (457, "Interfaz JTAG / SWD", "Conectores y comunicaciones", "Programación y depuración", "bus", dict(alias="debug port, programming header", designador="JTAG/SWD", descripcion="Interfaz para programar y depurar microcontroladores.", interpretacion="Identifica reloj, datos, reset, referencia de tensión y masa antes de conectar la herramienta.", terminales="TCK/SWCLK, TMS/SWDIO, GND, VTREF y opcionales", errores_comunes="Alimentar la placa desde dos fuentes o invertir el conector.", aplicaciones="Firmware y diagnóstico de placa", etiquetas="jtag swd debug programacion microcontrolador")),
    (458, "Bus Modbus RTU sobre RS-485", "Conectores y comunicaciones", "Buses industriales", "bus", dict(alias="Modbus RTU, RS485", designador="BUS", descripcion="Protocolo maestro/servidor transportado habitualmente por un par diferencial RS-485.", interpretacion="Además de A/B deben revisarse dirección, velocidad, paridad, polarización y terminación.", terminales="A, B y referencia/blindaje según instalación", errores_comunes="Invertir A/B o terminar todos los nodos.", aplicaciones="HVAC, variadores y control industrial", etiquetas="modbus rtu rs485 direccion baud paridad", fuente="https://www.modbus.org/modbus-specifications", climatizacion="Sí")),
    (459, "Bus BACnet MS/TP", "Conectores y comunicaciones", "Buses de edificios", "bus", dict(alias="BACnet MSTP, RS485 building automation", designador="BUS", descripcion="Red de automatización de edificios basada en token sobre RS-485.", interpretacion="Revisa MAC, velocidad, polaridad, terminadores y número máximo de maestros configurado.", terminales="A/+, B/− y referencia/blindaje según fabricante", errores_comunes="Confundir dirección MAC con instancia de dispositivo.", aplicaciones="Climatización centralizada y BMS", etiquetas="bacnet mstp rs485 bms hvac mac", fuente="https://bacnet.org/", climatizacion="Sí")),
    (460, "Bus DALI", "Conectores y comunicaciones", "Control de iluminación", "bus", dict(alias="Digital Addressable Lighting Interface", designador="DA", descripcion="Bus digital de dos hilos para control direccionable de iluminación.", interpretacion="Los dos conductores del bus suelen ser no polarizados, pero no deben confundirse con alimentación de red.", terminales="DA, DA", errores_comunes="Aplicar tensión de red o superar la alimentación permitida del bus.", aplicaciones="Iluminación técnica y edificios", etiquetas="dali iluminacion bus direccionable", fuente="https://www.dali-alliance.org/dali/")),
]


MODULES = [
    {"id":"M01","title":"Fundamentos de lectura","level":"Básico","summary":"Aprende a seguir líneas, nodos, referencias y masas sin perderte entre páginas.","lessons":["LEC-001","LEC-024","LEC-003","LEC-009"]},
    {"id":"M02","title":"Entrada de red y rectificación","level":"Básico","summary":"Reconoce protecciones, filtro, puente rectificador y bus DC antes de medir.","lessons":["LEC-023","LEC-002","LEC-004","LEC-010"]},
    {"id":"M03","title":"Señales, sensores y control","level":"Intermedio","summary":"Interpreta divisores, NTC, comparadores, relés y señales activas a nivel bajo.","lessons":["LEC-005","LEC-006","LEC-012","LEC-021","LEC-020"]},
    {"id":"M04","title":"Fuentes conmutadas","level":"Intermedio","summary":"Separa primario y secundario y sigue el camino de energía y realimentación.","lessons":["LEC-011","LEC-014","LEC-013","LEC-015"]},
    {"id":"M05","title":"Potencia inverter y climatización","level":"Avanzado","summary":"Analiza IPM, BLDC, válvulas EEV y comunicaciones entre unidades.","lessons":["LEC-016","LEC-017","LEC-018","LEC-019"]},
    {"id":"M06","title":"Comunicaciones y diagnóstico","level":"Avanzado","summary":"Sigue buses diferenciales, identifica referencias y planifica medidas seguras.","lessons":["LEC-022","LEC-007","LEC-008"]},
]


QUIZZES = {
    "LEC-001":[{"q":"¿Qué confirma normalmente una unión eléctrica entre líneas?","options":["Un punto sólido","El color de la línea","Que se crucen en ángulo recto"],"answer":0,"explanation":"El nodo sólido confirma la conexión; los cruces pueden no estar unidos."}],
    "LEC-024":[{"q":"¿Por qué no debes asumir que GND, chasis y PE son el mismo nodo?","options":["Porque pueden pertenecer a dominios y funciones diferentes","Porque todos son señales digitales","Porque PE siempre es negativo"],"answer":0,"explanation":"Solo el esquema o el diseño confirma dónde y cómo se unen."}],
    "LEC-003":[{"q":"En el símbolo del diodo, la barra identifica…","options":["El cátodo","El ánodo","La puerta"],"answer":0,"explanation":"La barra corresponde al cátodo K."}],
    "LEC-009":[{"q":"Los contactos de un relé se dibujan normalmente en estado…","options":["De reposo, sin energizar","Energizado","Indeterminado"],"answer":0,"explanation":"La convención habitual representa la bobina sin energizar."}],
    "LEC-023":[{"q":"¿Qué componente suele estar en paralelo con la red para limitar sobretensiones?","options":["MOV","Fusible","NTC de arranque"],"answer":0,"explanation":"El MOV deriva el transitorio; fusible y NTC suelen ir en serie."}],
    "LEC-002":[{"q":"Tras el puente rectificador, ¿qué elemento almacena energía en el bus DC?","options":["Condensador de bus","Choque de modo común","Relé de salida"],"answer":0,"explanation":"El condensador suaviza la tensión rectificada y mantiene el bus."}],
    "LEC-004":[{"q":"¿Cuántos diodos conducen normalmente en cada semiciclo de un puente monofásico?","options":["Dos","Uno","Cuatro"],"answer":0,"explanation":"Conduce una pareja diagonal en cada semiciclo."}],
    "LEC-010":[{"q":"El diodo de rueda libre está normalmente…","options":["Inversamente polarizado","En cortocircuito","En serie con la bobina"],"answer":0,"explanation":"Solo conduce el pico de corriente cuando se desconecta la bobina."}],
    "LEC-005":[{"q":"¿Dónde aparece la tensión dividida?","options":["En el nodo entre las dos resistencias","Solo en la alimentación","En ambos extremos a la vez"],"answer":0,"explanation":"El nodo central alimenta normalmente ADC o comparador."}],
    "LEC-006":[{"q":"Una NTC correcta a temperatura ambiente garantiza que el circuito de medida funciona?","options":["No, también hay que comprobar divisor, referencia y entrada","Sí, siempre","Solo si mide 10 kΩ"],"answer":0,"explanation":"La placa puede fallar aunque la NTC cambie correctamente."}],
    "LEC-012":[{"q":"¿Qué pista sugiere un operacional trabajando de forma lineal?","options":["Realimentación negativa","Salida sin conexiones","Una bobina en la entrada"],"answer":0,"explanation":"La realimentación negativa fija la ganancia y mantiene la región lineal."}],
    "LEC-021":[{"q":"Una entrada /RESET se activa normalmente con…","options":["Nivel bajo","Nivel alto","Señal analógica"],"answer":0,"explanation":"La barra, barra inclinada, n o burbuja suelen indicar activo bajo."}],
    "LEC-020":[{"q":"¿Respecto a qué punto debes medir la salida de un sensor de presión de tres hilos?","options":["Su GND de referencia","PE siempre","Cualquier chasis"],"answer":0,"explanation":"La salida se interpreta respecto a la masa del propio sensor."}],
    "LEC-011":[{"q":"¿Qué debes conservar al medir un optoacoplador entre primario y secundario?","options":["La separación de masas","Una masa común","El puente entre ambos lados"],"answer":0,"explanation":"Unir las masas puede anular el aislamiento y ser peligroso."}],
    "LEC-014":[{"q":"El primario de una flyback aislada está referido normalmente a…","options":["La red rectificada","La masa secundaria","PE directamente"],"answer":0,"explanation":"El primario permanece eléctricamente ligado al bus de red."}],
    "LEC-013":[{"q":"¿Qué suele cruzar la información de regulación al primario?","options":["Optoacoplador o acoplamiento aislado","Cable de PE","Condensador de bus"],"answer":0,"explanation":"La realimentación mantiene la barrera de aislamiento."}],
    "LEC-015":[{"q":"Una etapa PFC boost suele…","options":["Elevar y regular el bus DC","Reducir el bus a 5 V","Alimentar directamente el motor"],"answer":0,"explanation":"Controla corriente de entrada y eleva el bus."}],
    "LEC-016":[{"q":"¿Qué salidas forman el puente inversor trifásico?","options":["U, V y W","L, N y PE","TX, RX y GND"],"answer":0,"explanation":"Tres medios puentes generan U, V y W."}],
    "LEC-017":[{"q":"¿Qué información necesita un control BLDC para conmutar correctamente?","options":["Posición o realimentación del rotor","Solo temperatura ambiente","Únicamente PE"],"answer":0,"explanation":"La posición puede obtenerse por Hall, FG o estimación sensorless."}],
    "LEC-018":[{"q":"Una EEV paso a paso se mueve mediante…","options":["Una secuencia de excitación de bobinas","Tensión DC fija en una bobina","Un relé térmico"],"answer":0,"explanation":"El orden de fases determina sentido y pasos."}],
    "LEC-019":[{"q":"Antes de medir una comunicación interior-exterior debes saber…","options":["Si está aislada o referida a red","Solo el color del cable","La potencia del compresor"],"answer":0,"explanation":"La referencia eléctrica determina la seguridad y el método de medida."}],
    "LEC-022":[{"q":"En RS-485 la información se obtiene principalmente de…","options":["La diferencia entre A y B","La tensión de A respecto a PE","La corriente de alimentación"],"answer":0,"explanation":"Es una transmisión diferencial."}],
    "LEC-007":[{"q":"¿Qué limita la corriente de base de un BJT usado como interruptor?","options":["La resistencia de base","El diodo de cuerpo","El condensador de bus"],"answer":0,"explanation":"La resistencia protege la salida de control y fija corriente de base."}],
    "LEC-008":[{"q":"En un MOSFET N de lado bajo, la carga queda normalmente entre…","options":["Positivo y drenador","Puerta y masa","Fuente y puerta"],"answer":0,"explanation":"La fuente va a masa y el drenador conmuta el retorno de la carga."}],
}


DEEP_DIVES = {
    "LEC-002":{"measure":"Con el equipo aislado, identifica continuidad desde L/N hasta el puente. Energizado, solo personal cualificado debe medir AC y bus DC con categoría y rango adecuados.","diagnosis":"Si hay AC antes del fusible pero no después, revisa fusible y causa de su apertura. Si llega AC al puente y no aparece bus, comprueba puente, precarga y cortocircuitos del bus.","safety":"El bus puede conservar energía después de desconectar. Verifica tensión real antes de tocar."},
    "LEC-006":{"measure":"Mide primero la NTC desconectada y su temperatura. Después, con esquema y referencia segura, comprueba alimentación del divisor y tensión del nodo.","diagnosis":"Una lectura clavada en 0 V o en la alimentación puede indicar cortocircuito, circuito abierto, resistencia fija o entrada dañada.","safety":"No apliques tensión externa a la entrada ADC sin conocer sus límites."},
    "LEC-014":{"measure":"Distingue masa caliente y masa secundaria. Sigue arranque del PWM, conmutación de puerta, drenador, secundario y realimentación.","diagnosis":"Sin salida: comprueba bus, alimentación de arranque, VCC del PWM y cortos secundarios antes de sustituir el controlador.","safety":"Un osciloscopio con tierra puede cortocircuitar el primario. Usa el método de aislamiento apropiado."},
    "LEC-016":{"measure":"Con bus descargado, compara P-N, P-U/V/W y N-U/V/W en modo diodo. Energizado, verifica fuentes de driver y órdenes antes del IPM.","diagnosis":"No condenes el módulo solo por ausencia de salida: revisa enable, fault, PWM, bootstrap, corriente y compresor.","safety":"El bus P/N es letal. No conectes instrumentación no aislada sin procedimiento específico."},
    "LEC-019":{"measure":"Identifica si el bus comparte conductor con red, usa optoacopladores o es un par diferencial aislado. Solo entonces decide la referencia del instrumento.","diagnosis":"Comprueba alimentación de ambos extremos, continuidad, polaridad, terminación y actividad antes de culpar a una placa.","safety":"Algunos terminales de comunicación tienen potencial de red aunque su tensión aparente sea baja."},
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    symbols = data["simbolos"]
    lessons = data["lecciones"]
    if len(symbols) != 427 or len(lessons) != 24:
        raise RuntimeError("Unexpected source counts")

    existing_ids = {item["id"] for item in symbols}
    for number, name, category, subcategory, kind, fields in EXTRA:
        record = new_symbol(number, name, category, subcategory, kind, **fields)
        if record["id"] in existing_ids:
            raise RuntimeError(f"Duplicate ID: {record['id']}")
        existing_ids.add(record["id"])
        symbols.append(record)

    professional = json.loads(PROFESSIONAL_EXPANSION.read_text(encoding="utf-8"))
    for item in professional["symbols"]:
        fields = dict(item.get("fields", {}))
        fields.setdefault("norma", "Bloque funcional IEC experimental / modelo exacto requerido")
        fields.setdefault(
            "interpretacion",
            "El bloque representa funciones y grupos; el bornero físico depende del fabricante, modelo y variante exactos.",
        )
        if str(fields.get("fuente") or "").startswith("data/"):
            fields["fuente"] = ""
        record = new_symbol(
            int(item["number"]),
            item["name"],
            item["category"],
            item["subcategory"],
            item["kind"],
            **fields,
        )
        if record["id"] in existing_ids:
            raise RuntimeError(f"Duplicate ID: {record['id']}")
        existing_ids.add(record["id"])
        symbols.append(record)
    if len(symbols) != 501:
        raise RuntimeError(f"Expected 501 symbols after professional expansion, found {len(symbols)}")

    # Public lessons use their reviewed SVG files copied into assets/symbols.
    for lesson in lessons:
        lesson["archivo_svg"] = "assets/symbols/" + Path(lesson["archivo_svg"]).name
    for symbol in symbols[:427]:
        symbol["archivo_svg"] = "assets/symbols/" + Path(symbol["archivo_svg"]).name
        symbol["archivo_png"] = ""

    categories = sorted({item["categoria"] for item in symbols})
    subcategories = sorted({item["subcategoria"] for item in symbols if item.get("subcategoria")})
    catalog = {
        "version": "1.2",
        "generated_from": "Base Simbología Eléctrica y Electrónica Replacor",
        "count": len(symbols),
        "lesson_count": len(lessons),
        "categories": categories,
        "subcategories": subcategories,
        "symbols": symbols,
    }
    lesson_by_id = {item["id"]: item for item in lessons}
    course_modules = []
    for module in MODULES:
        enriched = dict(module)
        enriched["lessons"] = []
        for lesson_id in module["lessons"]:
            lesson = dict(lesson_by_id[lesson_id])
            lesson["steps"] = [part.strip() for part in re.split(r"\d+\.\s*", lesson.pop("pasos")) if part.strip()]
            lesson["quiz"] = QUIZZES.get(lesson_id, [])
            lesson["deep_dive"] = DEEP_DIVES.get(lesson_id, {})
            enriched["lessons"].append(lesson)
        course_modules.append(enriched)
    course = {
        "version": "1.0",
        "title": "Interpretación práctica de diagramas y esquemas",
        "description": "Curso progresivo orientado al diagnóstico de placas electrónicas y equipos de climatización.",
        "module_count": len(course_modules),
        "lesson_count": sum(len(module["lessons"]) for module in course_modules),
        "modules": course_modules,
    }
    (OUT / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (OUT / "course.json").write_text(json.dumps(course, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (OUT / "index.json").write_text(json.dumps({"version":"1.2","symbols":len(symbols),"lessons":course["lesson_count"],"modules":len(course_modules)}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Built {len(symbols)} symbols, {course['lesson_count']} lessons and {len(course_modules)} modules")


if __name__ == "__main__":
    main()
