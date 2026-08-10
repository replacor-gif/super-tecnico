# Integración de ElectroIA con una IA

ElectroIA separa dos responsabilidades: la IA decide qué circuito necesita y el motor lo valida y dibuja. El motor no incluye un modelo de IA ni realiza cálculos eléctricos.

## Flujo recomendado

1. Llama a `electroia_get_capabilities` para conocer la versión y los límites.
2. Llama a `electroia_search_symbols` con palabras normales, una categoría o un estado de revisión.
3. Llama a `electroia_get_symbol` para obtener los nombres y tipos exactos de los terminales.
4. Construye un documento conforme a `diagram-document.schema.json`.
5. Llama a `electroia_render_diagram` y revisa los errores y advertencias antes de mostrar el SVG.

Un símbolo `engine_reviewed` tiene geometría y terminales revisados. Un símbolo `auto_draft` es una estructura provisional por familia: puede usarse para desarrollar el documento, pero el motor siempre avisará de que falta revisión gráfica.

## Uso local mediante MCP

Con Node.js 20 o posterior, instala las dependencias dentro de `electroia-tool-server` y ejecuta `node src/index.mjs`. El transporte actual es `stdio`.

La descripción `server.json` ya sigue el formato del MCP Registry. Durante la vista previa no contiene todavía una distribución instalable ni un transporte MCP remoto; se añadirán antes de solicitar la publicación en el registro.

## Descubrimiento web

Una IA que conozca la dirección de Super Técnico puede comenzar por `/llms.txt` o por `/data/electroia/discovery.json`. Esos documentos enlazan el manifiesto de herramientas, el esquema del documento y la biblioteca normalizada sin incluir credenciales privadas.
