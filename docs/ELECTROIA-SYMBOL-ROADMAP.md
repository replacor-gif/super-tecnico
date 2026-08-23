# Plan continuo de normalización de símbolos de ElectroIA

Fecha de revisión: 2026-08-23

## Estado medible

- Catálogo público: 501 símbolos.
- Símbolos con estructura y terminales: 501.
- Símbolos revisados individualmente: 501.
- Borradores por familia pendientes de revisión gráfica: 0.
- Familias completas: 19 de 19.
- Lote de sensores HVAC revisado: 17 símbolos de temperatura, presión, humedad, flujo, nivel, calidad de aire, seguridad y medida de corriente.
- Lote de señales y comunicaciones revisado: 10 símbolos de RS-485, CAN, Ethernet, 4-20 mA, 0-10 V, UART, JTAG/SWD, Modbus RTU, BACnet MS/TP y DALI.
- Pack profesional público: 41 símbolos para PLC, E/S, HMI, comunicaciones, Arduino/ESP/Raspberry, variadores, arrancadores, seguridad, maniobra y control técnico de edificios.

Un símbolo solo cambia a `engine_reviewed` cuando dispone de geometría propia, terminales identificados, anclajes sobre la rejilla común y una prueba de representación. Estar presente en el catálogo o compartir una plantilla provisional no equivale a estar revisado.

## Cola priorizada

1. Ampliar las pruebas de sistemas completos de automatismos, cuadros, electrónica HVAC y control embebido.
2. Añadir ICT, seguridad, comunicaciones de edificios, energía distribuida, almacenamiento y recarga eléctrica.
3. Crear perfiles gráficos separados para hidráulica, neumática y P&ID, sin confundirlos con el perfil electrotécnico.
4. Incorporar documentación física de cuadros: borneros multinivel, puentes, carril DIN, canaletas, envolventes y reservas.
5. Preparar la interpretación de foto o boceto como entrada separada, conservando revisión humana antes de generar conectividad definitiva.

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

El catálogo inicial está normalizado por completo. Las ampliaciones continuarán por lotes profesionales cerrados y probados; no se aumentará artificialmente la cifra de revisados mediante cajas genéricas. Cuando un equipo varía por fabricante o modelo, el símbolo usa grupos funcionales y el motor obliga a indicar el modelo exacto antes de convertirlo en bornes físicos.
