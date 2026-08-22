# Auditoría de competencia de la versión 1

Fecha de revisión: 2026-08-23

## Alcance de la primera versión

La versión 1 es una beta pública gratuita orientada a consulta técnica y uso en campo. No pretende ser todavía el servicio comercial completo para IAs ni sustituir el criterio profesional, el proyecto, el manual exacto o la comprobación de la norma aplicable.

Se considera competente cuando:

- las herramientas principales funcionan en móvil y ordenador;
- los resultados técnicos muestran límites y procedencia sin inventar datos;
- la normativa devuelve evidencia localizable y pide contexto ante preguntas ambiguas;
- la navegación, el feedback y la analítica permiten observar el uso real;
- existe una vía pública y documentada para que otras IAs prueben al menos una herramienta;
- la compilación pública no incluye bases privadas, credenciales ni archivos internos.

## Puertas de salida superadas

- Aplicación unificada con navegación y estética común.
- 30 marcas HVAC, 2.538 códigos de avería y 1.717 variantes técnicas.
- 38.618 referencias de componentes; la ficha básica sigue siendo el flujo principal.
- 71 refrigerantes, 56 con P/T y ciclo Mollier disponible.
- Diseñador móvil de conductos con ajuste táctil de rejillas y ramales y recálculo inmediato.
- Desagües de condensados, calculadoras y biblioteca electrónica con motores deterministas.
- 18 reglamentos, 2.050 páginas y 8.147 fragmentos estructurados y compactados.
- Buscador normativo con sinónimos, preguntas naturales, detección de contexto insuficiente, jerarquía ITC/artículo/apartado/tabla, página, huellas y enlace oficial.
- API gratuita de normativa para personas, software e IAs, con límites y medición anónima.
- Vigilancia de cambios de fuentes oficiales y bloqueo de reglas dependientes hasta revisión.
- Más de 119 pruebas Python, motores JavaScript, pruebas PHP, compilación estática y recorridos reales en navegador superados.

## Límites que deben seguir visibles

- Una coincidencia normativa es evidencia documental, no una conclusión automática sobre aplicabilidad.
- Todavía no hay una biblioteca suficiente de reglas normativas revisadas para contestar directamente todos los dimensionados.
- ElectroIA conserva 460 símbolos normalizados: 439 tienen revisión gráfica y terminales funcionales y 21 siguen marcados como borrador. Todavía no debe prometer diagramas perfectos para cualquier instalación.
- La entrada por foto o boceto está prevista en el contrato, pero no es una función terminada.
- El diseñador de conductos ofrece un diseño previo práctico y editable; todavía no calcula toda la pérdida de carga, los accesorios, el ruido ni la presión disponible necesarios para considerarlo un plano de ejecución definitivo.
- Normativa, conectores y plataformas embebidas ofrecen consultas HTTP públicas limitadas. Frigorista, desagües, componentes y diagramas siguen siendo motores de navegador o vista previa privada.
- El 63 % del informe de preparación para IAs mide el proyecto comercial futuro (MCP remoto, autenticación, cuotas, validadores y benchmark económico), no la competencia de esta beta para técnicos.

## Siguiente orden de trabajo

1. Publicar esta candidata y recoger búsquedas, aperturas, votos y comentarios reales.
2. Convertir las consultas normativas más repetidas en reglas revisadas con ámbito, excepciones y fuente exacta.
3. Revisar por familias los símbolos de ElectroIA y ampliar las pruebas visuales de esquemas completos.
4. Afinar conductos y frigorista con casos de campo aportados por técnicos.
5. Abrir una segunda herramienta gratuita para IAs cuando su contrato, límites y trazabilidad igualen al buscador normativo.
6. Medir coste y ahorro por consulta antes de decidir autenticación o cobro.

## Criterio de publicación

Esta versión puede publicarse como **primera versión competente en beta** si el despliegue real reproduce las pruebas locales, la API de normativa responde y la comprobación móvil no muestra errores ni desbordamiento horizontal.
