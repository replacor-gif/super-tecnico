# Plan continuo de normalización de símbolos de ElectroIA

Fecha de revisión: 2026-08-17

## Estado medible

- Catálogo público: 460 símbolos.
- Símbolos con estructura y terminales: 460.
- Símbolos revisados individualmente: 127.
- Borradores por familia pendientes de revisión gráfica: 333.
- Familias completas: conexiones y referencias; protecciones eléctricas; relés, interruptores y actuadores; máquinas y actuadores.
- Lote de sensores HVAC revisado: 17 símbolos de temperatura, presión, humedad, flujo, nivel, calidad de aire, seguridad y medida de corriente.
- Lote de señales y comunicaciones revisado: 10 símbolos de RS-485, CAN, Ethernet, 4-20 mA, 0-10 V, UART, JTAG/SWD, Modbus RTU, BACnet MS/TP y DALI.
- Base de automatización disponible en el motor: 11 bloques con canales explícitos para CPU de PLC, DI, DO, AI, AO, E/S remota, PLC de seguridad, HMI, fuente de 24 V, switch y pasarela industrial. Son elementos internos del motor hasta incorporarlos como familia pública del catálogo.

Un símbolo solo cambia a `engine_reviewed` cuando dispone de geometría propia, terminales identificados, anclajes sobre la rejilla común y una prueba de representación. Estar presente en el catálogo o compartir una plantilla provisional no equivale a estar revisado.

## Cola priorizada

1. Convertir la base interna de automatización en familia pública: revisar representación, variantes de canales, comunes, potenciales, aislamiento y borneros de CPU, DI/DO/AI/AO, E/S remota, seguridad, HMI, fuente, switch y pasarela.
2. Controladores abiertos e industriales: bloques de interfaz para Arduino de 5 V y 3,3 V, Arduino Opta, Portenta Machine Control, Raspberry Pi/Compute Module y controlador embebido genérico.
3. Componentes pasivos: condensadores polarizados, inductores, choque de modo común, MOV, PTC y transformadores con distintas tomas.
4. Completar sensores: proximidad, posición, vibración, encoders, gases y sensores de proceso pendientes.
5. Semiconductores discretos: BJT, MOSFET P, IGBT, SCR, TRIAC, Zener, TVS y puentes rectificadores.
6. Potencia y climatización: PFC, inverter, IPM, drivers, contactores de estado sólido y módulos de potencia.
7. Conectores, medida, aislamiento, lógica digital y bloques funcionales.

La base de automatización no se representará con una sola caja genérica. Cada bloque debe exponer sus canales reales, comunes, alimentaciones, potenciales, aislamiento, dirección de señal y correspondencia con borneros. Las capacidades y límites de cada ecosistema se definen en `data/electroia/controller-ecosystems.json`.

Arduino y Raspberry Pi se tratarán como controladores de supervisión o control no seguro salvo que exista un producto concreto, certificado y validado para la función de seguridad. Una marca, una librería o un programa no convierten por sí solos un controlador genérico en un elemento de seguridad.

## Puertas de aceptación por lote

- Ningún terminal fuera de la rejilla de 50 mil.
- Nombre y función inequívocos; variantes diferentes no comparten una geometría engañosa.
- Terminales eléctricos completos y con denominación consistente.
- El motor rechaza conexiones a terminales inexistentes.
- El SVG no muestra solapes, recortes ni la marca de borrador.
- Existe una prueba automática de contrato y una lámina visual de la familia.
- Se actualizan recuentos, descubrimiento para IAs y documentación en la misma revisión.

## Regla de trabajo

La normalización continuará por lotes pequeños mientras se desarrollan otros módulos. Cada lote debe quedar terminado y probado antes de comenzar el siguiente; no se aumentará artificialmente la cifra de revisados mediante cajas genéricas.
