# Super Técnico para IAs

## Objetivo del producto

Super Técnico no debe competir con una IA en razonamiento general. Debe ofrecerle una herramienta especializada que reduzca el trabajo repetitivo y caro: localizar manuales, distinguir variantes, extraer datos, contrastar fuentes, normalizar componentes y dibujar diagramas.

La promesa correcta es:

> Una IA consulta Super Técnico porque obtiene en una sola llamada una respuesta técnica compacta, aplicable, versionada y trazable, por menos coste que reconstruirla desde fuentes dispersas.

No se venderá una copia de la base de datos. Se venderá acceso controlado a resultados concretos.

## Dos motores, una sola puerta de entrada

Super Técnico para IAs agrupa dos servicios diferentes:

1. **Super Técnico Knowledge**: errores HVAC, procedimientos, valores, componentes, electrónica y casos reales de campo.
2. **ElectroIA Diagram Engine**: símbolos normalizados, validación de terminales y redes, enrutado y generación determinista de SVG.

La IA conserva el razonamiento general y elige qué quiere hacer. Super Técnico aporta el conocimiento estructurado y ElectroIA ejecuta el trabajo gráfico que conviene resolver de forma determinista.

## Flujo económico de consulta

```text
IA
 └─ 1. Comprobar cobertura (gratis y muy breve)
     ├─ Sin cobertura → terminar sin coste
     └─ Con cobertura
         └─ 2. Pedir el nivel mínimo necesario
             ├─ Básico: dato concreto
             ├─ Diagnóstico: causas, pruebas, valores y seguridad
             ├─ Campo: averías y reparaciones confirmadas
             └─ Diagrama: validación y SVG con ElectroIA
```

Cada respuesta debe llevar ID estable, versión, confianza, procedencia, advertencias y datos desconocidos. Los resultados deben ser compactos y aptos para caché. La facturación futura se asociará a la herramienta y al nivel de resultado, no al tamaño interno de la base.

## Cómo descubre una IA que existe

Una IA no descubre ni contrata por sí sola un servicio desconocido. Tiene que ocurrir al menos una de estas cosas:

1. Un desarrollador conecta explícitamente la URL MCP o la API a su agente.
2. El servicio se publica en un registro MCP que consultan directorios y plataformas.
3. Se publica como plugin o integración dentro del catálogo de una plataforma de IA.
4. La documentación pública, `llms.txt`, el manifiesto y la página de integración permiten que buscadores, personas y herramientas de desarrollo lo encuentren y entiendan.

Por eso el lanzamiento se divide en dos planos: **ser encontrable** y **ser conectable**. Esta versión deja preparado el primero. El segundo requiere un servidor remoto, autenticación, medición, condiciones comerciales y revisión de seguridad.

## Superficies públicas preparadas

- `/ia-integracion.html`: explicación comercial y técnica para desarrolladores y empresas.
- `/llms.txt`: índice corto para agentes y rastreadores.
- `/data/ai/discovery.json`: manifiesto neutral de producto y estado.
- `/data/ai/tool-manifest.json`: herramientas, objetivos, esquemas y niveles de consumo.
- `/data/ai/knowledge-record.schema.json`: contrato de trazabilidad.
- `/data/ai/knowledge-api-contract.openapi.json`: contrato de diseño; ejecución desactivada.
- `/data/ai/readiness-report.json`: auditoría automática del estado real.
- `/data/ai/benchmark-plan.json`: pruebas necesarias para demostrar el ahorro.

## Límites de seguridad

- Ningún archivo público contiene claves, PIN ni secretos.
- La base de datos interna nunca se entrega directamente.
- La futura API devolverá proyecciones mínimas por objetivo, no filas maestras.
- La comprobación de cobertura podrá ser gratuita, pero las respuestas de valor requerirán un cliente autenticado.
- Se aplicarán cuotas, límites por herramienta, caché, detección de enumeración y auditoría de consumo.
- Los casos aportados por técnicos se publicarán únicamente después de moderación y con el nivel de confirmación visible.
- Una respuesta sin contexto suficiente debe devolver `insufficient_context`; no debe adivinar.

## Orden de construcción recomendado

1. Consolidar IDs, versiones, fuentes y confianza en las familias con más demanda.
2. Implementar el gateway remoto únicamente con `get_capabilities` y `check_coverage`.
3. Abrir un piloto autenticado con resolución HVAC y componentes.
4. Añadir métricas de coste, latencia, caché, utilidad y caso resuelto.
5. Ejecutar el benchmark frente a búsquedas independientes.
6. Incorporar casos de campo y ElectroIA cuando la trazabilidad y el control de extracción estén probados.
7. Publicar el servidor en el registro MCP y presentar las integraciones a los catálogos de cada plataforma.

## Criterio para activar ventas

No se debe anunciar un porcentaje de ahorro hasta medirlo. El acceso comercial estará listo cuando:

- el servidor remoto sea estable y autenticado;
- todas las respuestas de pago tengan procedencia;
- se registre el consumo por cliente y herramienta;
- exista un conjunto de evaluación ciego;
- las tasas de respuesta inventada y mezcla de variantes estén por debajo de los umbrales definidos;
- estén publicados privacidad, términos, soporte y condiciones de uso para máquinas.
