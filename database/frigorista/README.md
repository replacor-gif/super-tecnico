# Asistente Frigorista

La interfaz y el futuro acceso para IAs comparten un único motor determinista.

## Capas

1. `seed_refrigerants.csv` y `seed_applications.csv`: catálogo de trabajo revisable.
2. `tools/build_frigorista_data.py`: verifica el soporte de CoolProp y genera las curvas públicas versionadas.
3. `data/frigorista/catalog.json` y `pt-curves.json`: datos mínimos para el navegador.
4. `data/frigorista/mollier-data.json`: campana de saturación y propiedades P-h versionadas para vapor y líquido, sin interpolar entre fases.
5. `assets/frigorista-engine.js`: conversión P/T, recalentamiento, subenfriamiento, puntos Mollier, balance específico y siguiente medición.
6. `data/frigorista/tool-manifest.json`: contratos neutrales para la futura API/MCP.

La base maestra no se publica. `schema.sql` separa fuentes, estado regulatorio, medidas, valores derivados y resultados diagnósticos para preservar trazabilidad.

## Reglas esenciales

- Presión interna siempre absoluta en Pa.
- Presión de manómetro convertida con la presión atmosférica de la sesión.
- Rocío para recalentamiento; burbuja para subenfriamiento.
- Nunca extrapolar fuera de una curva válida.
- `observed_estimate` no se convierte en `measured`.
- Una presión aislada no confirma carga ni avería.
- El ciclo Mollier solo une puntos medidos o derivados mediante una transformación declarada, como la expansión isoentálpica.
- La entalpía y la entropía son relativas; se comparan diferencias del mismo refrigerante y versión de datos.
- El análisis puede terminar como no concluyente.
