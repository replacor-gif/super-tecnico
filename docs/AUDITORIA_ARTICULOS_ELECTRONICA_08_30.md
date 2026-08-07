# Auditoría e integración de artículos de electrónica 08–30

Fecha de revisión: 7 de agosto de 2026.

## Resultado

La colección se integra como una enciclopedia formativa independiente llamada **Enciclopedia de electrónica**. No se presenta en el orden numérico de los documentos: el técnico elige libremente un tema, un área de conocimiento o un capítulo, y utiliza la búsqueda solo como acceso secundario.

La versión generada contiene:

- 23 temas técnicos.
- 399 páginas de material fuente revisado.
- 678 apartados navegables.
- 397 figuras de contenido.
- 235 tablas útiles.
- 54.283 palabras indexadas, incluidas las tablas.
- 11 bloques funcionales.
- 5 enlaces directos a herramientas relacionadas de Super Técnico.

## Revisión realizada

- Extracción estructurada de títulos, texto, tablas e imágenes desde los DOCX.
- Renderizado y revisión visual de las 399 páginas para detectar cortes, páginas vacías o figuras defectuosas.
- Exclusión de portadas, índices repetidos y elementos meramente decorativos del contenido navegable.
- Normalización de conceptos repetidos y adición de advertencias editoriales cuando una regla no es universal.
- Relación de cada tema con componentes, comparador, calculadoras, simbología y averías reales.
- Adición de fuentes primarias de revisión para componentes y seguridad de medida cuando resultaba necesario.

## Criterio de organización

### Enciclopedia por temas

Los 23 temas aparecen como módulos de aprendizaje. Se ordenan pedagógicamente desde resistencias, diodos, transistores y magnéticos hasta fuentes, medida, control, comunicaciones, potencia, PFC, IPM y diagnóstico global.

### Entrada por área de conocimiento

Diagnóstico y método; fuentes y raíles; medida; comunicaciones; control y firmware; acondicionamiento de señal; aislamiento; salidas y actuadores; inverter y potencia; protección y compatibilidad electromagnética; y componentes pasivos.

La numeración original se conserva internamente para trazabilidad, pero no condiciona el recorrido del técnico.

## Decisiones editoriales importantes

- El PFC no se presenta como equivalente al IPM o a la salida trifásica U-V-W.
- El cruce por cero se trata como función dependiente del circuito y no como sinónimo universal de comunicación.
- EEPROM, Flash y microcontrolador se distinguen para evitar diagnósticos ambiguos.
- La retirada de condensadores de desacoplo solo se contempla como prueba temporal y condicionada.
- Las reglas generales quedan subordinadas al manual de servicio y a la hoja de datos exacta del componente.
- Se mantiene visible la separación HOT/COLD y la advertencia de no anular la tierra de protección del osciloscopio.

## Presentación en la aplicación

- La enciclopedia por temas es la pantalla inicial; el buscador queda en una pestaña secundaria y nunca abre automáticamente el primer resultado.
- Fichas por tema con nivel, contenido y progreso para evitar sobrecarga visual.
- Lector con índice lateral, selector de apartado, anterior/siguiente, guardados y progreso.
- Imágenes ampliables y tablas adaptables a móvil.
- Interfaz en español, inglés, portugués y francés; el contenido técnico permanece revisado en español en esta primera integración.
- Contador público discreto y espacio publicitario coherente con el resto de Super Técnico.

## Control de publicación

Los originales DOCX y PDF no forman parte de la compilación pública. Se publica únicamente la transformación web estructurada y los recursos de contenido necesarios para la consulta.

## Validación

- Compilación estática completada.
- 59 pruebas unitarias y de estructura superadas.
- Prueba funcional en Chrome superada: carga, búsqueda `ULN2003`, apertura del lector, filtros, traducción de interfaz y vista móvil.
- Comprobación visual de escritorio y móvil superada.
