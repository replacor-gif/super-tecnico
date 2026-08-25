# Integración de ElectroIA con una IA

ElectroIA separa dos responsabilidades: la IA decide qué circuito necesita y el motor lo valida y dibuja. El motor no incluye un modelo de IA ni realiza cálculos eléctricos.

## Flujo recomendado

1. Llama a `electroia_get_capabilities` para conocer la versión y los límites.
2. Llama a `electroia_search_symbols` con palabras normales, una categoría o un estado de revisión.
3. Llama a `electroia_get_symbol` para obtener los nombres y tipos exactos de los terminales.
4. Construye un documento conforme a `diagram-document.schema.json`.
5. Llama a `electroia_render_diagram` y revisa los errores y advertencias antes de mostrar el SVG.

Los 501 símbolos públicos son `engine_reviewed`. Un bloque con `requires_exact_model=true` representa funciones, no un bornero físico: la IA debe aportar fabricante, modelo, variante y manual antes de expandir sus terminales reales.

El contrato impone 256 KiB por documento, 200 símbolos, 400 redes, 100 conexiones por red y 2.000 conexiones totales. Una entrada que supere esos límites se rechaza antes del renderizado.

## Uso local mediante MCP

Con Node.js 20 o posterior, instala las dependencias dentro de `electroia-tool-server` y ejecuta `node src/index.mjs`. El transporte actual es `stdio`.

La descripción `server.json` ya sigue el formato del MCP Registry. Durante la vista previa no contiene todavía una distribución instalable ni un transporte MCP remoto; se añadirán antes de solicitar la publicación en el registro.

`data/electroia/document-profiles.json` separa las reglas gráficas generales de las reglas experimentales para circuito, unifilar y multifilar. `data/electroia/public-execution-policy.json` define autenticación, cuotas, diagnósticos y apagado de emergencia para el futuro servicio; no activa la ejecución pública.

## Descubrimiento web

Una IA que conozca la dirección de Super Técnico puede comenzar por `/llms.txt` o por `/data/electroia/discovery.json`. Esos documentos enlazan el manifiesto de herramientas, el esquema del documento y la biblioteca normalizada sin incluir credenciales privadas.
