# Pendientes de perfeccionamiento del diseñador de conductos

Fecha de revisión: 2026-08-17

## Situación actual

El diseñador ya permite dibujar estancias poligonales, identificarlas sobre el plano, seleccionar las zonas climatizadas, situar la unidad interior, crear un trazado automático, mover rejillas y ramales con toque o arrastre y recalcular secciones en escalones de 5 cm.

Sigue siendo una propuesta de diseño previo basada en criterios prácticos. Todavía no debe presentarse como cálculo aerodinámico completo ni como plano de ejecución definitivo.

## Prioridad 1: comodidad real en móvil

- Crear un modo de plano ampliado que utilice casi toda la pantalla y deje las acciones en una barra inferior compacta.
- Añadir zoom con dos dedos y desplazamiento del plano sin confundirlo con la colocación de puntos.
- Sustituir los selectores que quedan dentro de estancias pequeñas por un editor contextual inferior al tocar la estancia.
- Mantener siempre visible una instrucción única y la siguiente acción, ocultando información secundaria mientras se dibuja.
- Hacer más clara la selección activa de rejilla o ramal e incorporar un botón visible para cancelar el movimiento.
- Probar el recorrido completo en teléfonos estrechos y con estancias pequeñas o irregulares.

## Prioridad 2: trazado profesional y editable

- Permitir marcar zonas preferentes de paso, zonas prohibidas, falsos techos disponibles, vigas y pasos entre habitaciones.
- Permitir fijar y mover también el conducto principal, no solo una guía de cada ramal.
- Conservar los tramos bloqueados por el técnico cuando se recalcula el resto de la red.
- Evitar recorridos con demasiados giros y mostrar por qué se eligió un trazado.
- Añadir transiciones, derivaciones, codos y reducciones como elementos identificables.
- Detectar ramales imposibles, cruces fuera de techo y salidas que no alcanzan la red principal.

## Prioridad 3: cálculo y comprobaciones

- Incorporar velocidad del aire, pérdida de carga lineal, pérdidas singulares y presión disponible del ventilador cuando se conozca.
- Diferenciar criterios de impulsión, retorno, ventilación y extracción.
- Comprobar relación de aspecto, velocidad, ruido orientativo y dimensiones comerciales.
- Permitir varias rejillas por estancia y definir impulsión y retorno de forma separada.
- Mantener el método práctico actual como modo rápido, diferenciándolo de un futuro modo de cálculo detallado.

## Prioridad 4: proyecto y trabajo de campo

- Guardar, duplicar, nombrar y exportar proyectos además del almacenamiento local automático.
- Generar una memoria resumida con plano, tramos, rejillas, advertencias y criterios utilizados.
- Incorporar cotas y una escala verificable en el PDF.
- Poder reabrir el plano en otro dispositivo sin reconstruirlo.
- Añadir casos reales de prueba aportados por técnicos antes de declarar una versión definitiva.

## Próximo incremento recomendado

El siguiente cambio debe concentrarse en el modo de plano ampliado para móvil y el editor contextual de estancias. Es la mejora con mayor impacto inmediato y prepara después la edición avanzada del conducto principal y de las restricciones de paso.
