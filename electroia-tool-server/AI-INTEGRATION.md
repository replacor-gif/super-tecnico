# Integración de ElectroIA con una IA

ElectroIA separa dos responsabilidades: la IA decide qué circuito necesita y el motor lo valida y dibuja. El motor no incluye un modelo de IA ni realiza cálculos eléctricos.

## Flujo recomendado

1. Llama a `electroia_get_capabilities` para conocer la versión y los límites.
2. Llama a `electroia_prepare_design_brief` y completa los requisitos técnicos que falten.
3. Construye una especificación conforme a `diagram-spec.schema.json`: puede usar `symbol_query` y conexiones por identificador local y nombre de terminal.
4. Llama a `electroia_compile_diagram`; revisa la resolución, los errores y las advertencias antes de mostrar el SVG.
5. Si una coincidencia necesita confirmación, usa `electroia_search_symbols` y `electroia_get_symbol` y repite con `symbol_id`.
6. Usa `electroia_render_diagram` con `diagram-document.schema.json` cuando necesites posiciones y terminales exactos de bajo nivel.

Los 501 símbolos públicos son `engine_reviewed`. Un bloque con `requires_exact_model=true` representa funciones, no un bornero físico: la IA debe aportar fabricante, modelo, variante y manual antes de expandir sus terminales reales.

El contrato impone 256 KiB por documento, 200 símbolos, 400 redes, 100 conexiones por red y 2.000 conexiones totales. Una entrada que supere esos límites se rechaza antes del renderizado.

## Uso local mediante MCP

Con Node.js 20 o posterior, instala las dependencias dentro de `electroia-tool-server` y ejecuta `node src/index.mjs`. El transporte actual es `stdio`.

La descripción `server.json` ya sigue el formato del MCP Registry. Durante la vista previa no contiene todavía una distribución instalable ni un transporte MCP remoto; se añadirán antes de solicitar la publicación en el registro.

`data/electroia/document-profiles.json` separa las reglas gráficas generales de las reglas experimentales para circuito, unifilar y multifilar. `data/electroia/public-execution-policy.json` define autenticación, cuotas, diagnósticos y apagado de emergencia para el futuro servicio; no activa la ejecución pública.

## Descubrimiento web

Una IA que conozca la dirección de Super Técnico puede comenzar por `/llms.txt` o por `/data/electroia/discovery.json`. Esos documentos enlazan el manifiesto de herramientas, el esquema del documento y la biblioteca normalizada sin incluir credenciales privadas.
