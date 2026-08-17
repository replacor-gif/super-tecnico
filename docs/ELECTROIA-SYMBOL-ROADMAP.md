# Plan continuo de normalización de símbolos de ElectroIA

Fecha de revisión: 2026-08-17

## Estado medible

- Catálogo público: 460 símbolos.
- Símbolos con estructura y terminales: 460.
- Símbolos revisados individualmente: 100.
- Borradores por familia pendientes de revisión gráfica: 360.
- Familias completas: conexiones y referencias; protecciones eléctricas; relés, interruptores y actuadores; máquinas y actuadores.

Un símbolo solo cambia a `engine_reviewed` cuando dispone de geometría propia, terminales identificados, anclajes sobre la rejilla común y una prueba de representación. Estar presente en el catálogo o compartir una plantilla provisional no equivale a estar revisado.

## Cola priorizada

1. Sensores HVAC: temperatura, presión, humedad, flujo, nivel, escarcha, fugas de agua y corriente.
2. Componentes pasivos: condensadores polarizados, inductores, choque de modo común, MOV, PTC y transformadores con distintas tomas.
3. Semiconductores discretos: BJT, MOSFET P, IGBT, SCR, TRIAC, Zener, TVS y puentes rectificadores.
4. Potencia y climatización: PFC, inverter, IPM, drivers, contactores de estado sólido y módulos de potencia.
5. Conectores, medida, aislamiento, lógica digital y bloques funcionales.

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
