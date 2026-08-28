# Pendientes de perfeccionamiento del diseñador de conductos

Fecha de revisión: 2026-08-22

## Situación actual

El diseñador ya permite dibujar estancias poligonales, identificarlas sobre el plano, seleccionar las zonas climatizadas, situar la unidad interior, crear un trazado automático, mover rejillas y ramales con toque o arrastre y recalcular secciones en escalones de 5 cm. En móvil dispone además de plano ampliado, gesto de zoom, editor contextual de estancias y cancelación visible del ajuste.

Sigue siendo una propuesta de diseño previo basada en criterios prácticos. Todavía no debe presentarse como cálculo aerodinámico completo ni como plano de ejecución definitivo.

## Prioridad 1: comodidad real en móvil — realizada en 0.5.1

- Plano ampliado que utiliza casi toda la pantalla y conserva controles compactos.
- Zoom con dos dedos y desplazamiento del plano sin confundirlo con la colocación de puntos.
- Editor contextual inferior al tocar una estancia, sin selectores diminutos dentro del plano móvil.
- Instrucción única, selección activa de rejilla o ramal y botón visible para cancelar el movimiento.
- Prueba automatizada en un teléfono de 390 × 844 px; quedan pendientes más casos reales de estancias irregulares.

## Recorrido principal ajustable — realizado en 0.6.0

- El trazado automático sigue favoreciendo pasillos y distribuidores.
- El cuadrado turquesa permite mover el punto de paso del conducto principal; todos los ramales y secciones se recalculan.
- En móvil se puede tocar el cuadrado y después el paso real, sin arrastre de precisión.
- «Principal automático» elimina la corrección manual y recupera la propuesta del motor.

## Edición técnica móvil — realizada en 0.7.0

- Selección directa tocando cualquier tramo, además de los tiradores del principal y los ramales.
- Arrastre real y panel de ajuste con botones grandes para máquina, rejillas, principal y ramales.
- Entrada automática en plano grande al seleccionar un elemento desde el móvil.
- Rejillas deslizables por su pared y cambio de pared desde el panel, conservando siempre la alineación.
- Varios puntos de paso consecutivos en el principal y en cada ramal, con recálculo inmediato.
- Altura única de la red verificada tramo a tramo; únicamente cambia el ancho en escalones de 5 cm.
- Rótulos exteriores con líneas guía y búsqueda automática de un espacio que no tape ningún conducto.

## Prioridad 2: trazado profesional y editable

- Permitir marcar zonas preferentes de paso, zonas prohibidas, falsos techos disponibles, vigas y pasos entre habitaciones.
- Permitir bloquear tramos completos del conducto principal; los varios puntos de paso ya son ajustables desde 0.7.0.
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

- Guardar, nombrar y exportar proyectos además del almacenamiento local automático: disponible en la primera versión de Proyecto Técnico. Duplicado y sincronización entre dispositivos siguen pendientes.
- Generar una memoria resumida con plano, tramos, rejillas, advertencias y criterios utilizados.
- Incorporar cotas y una escala verificable en el PDF.
- Poder reabrir el plano en otro dispositivo sin reconstruirlo.
- Añadir casos reales de prueba aportados por técnicos antes de declarar una versión definitiva.

## Próximo incremento recomendado

El siguiente cambio debe concentrarse en dibujar zonas preferentes y prohibidas de paso, falsos techos, vigas y pasos disponibles. Los puntos múltiples de 0.7.0 ya permiten imponer el recorrido; las restricciones convertirán esas decisiones en reglas permanentes del plano.
