# Auditoría del paquete de integración — 31/07/2026

## Veredicto

El paquete aporta tres buenas maquetas de producto, pero no debe copiarse directamente a producción. Dos módulos necesitan una API y moderación real; el comparador utiliza referencias ficticias y un algoritmo demasiado simple para recomendar sustituciones con seguridad.

La integración debe conservar la cabecera común, el aviso BETA, los cuatro idiomas, los enlaces legales, la configuración publicitaria desactivada y el proceso actual de construcción y pruebas.

## 1. Enciclopedia de averías reales

### Qué se conserva

- Consulta por referencia o modelo de placa, con coincidencia exacta o parcial.
- Casos con síntoma, solución y apodo.
- Confirmaciones y soluciones alternativas.
- Sin cuentas para los técnicos.

### Mejoras necesarias

- Denominarla «Averías reales por placa» para no confundirla con la biblioteca HVAC de códigos oficiales.
- No mostrar todos los casos al abrir la página; primero se solicita la referencia de placa.
- Normalizar espacios, guiones, barras y mayúsculas en el servidor.
- Separar el caso observado de sus soluciones: un caso puede tener varias soluciones revisadas sin que una quede fijada para siempre como principal.
- Estados públicos claros: pendiente, revisado y publicado. Solo los publicados aparecen en la búsqueda pública.
- Detección de duplicados, límites de longitud, saneado, control de frecuencia y registro de moderación.
- No usar `localStorage` como base compartida; queda reservado para preferencias del dispositivo.

## 2. Comparador de componentes

### Problemas de la maqueta

- Sus 16 referencias `ST-*` son ficticias y no se pueden publicar.
- El porcentaje de coincidencia aparenta una precisión que los datos no permiten.
- Compara tensión, corriente, encapsulado y algunos parámetros sin conservar siempre las condiciones de ensayo.
- No distingue suficientemente polaridad, topología, diodo interno, aislamiento, límites térmicos y variantes de patillaje.

### Integración segura propuesta

- Usar exclusivamente la base real actual de 11.532 referencias.
- Cambiar «porcentaje de compatibilidad» por tres resultados: `descartado`, `requiere revisión` y `datos comparables`.
- Mostrar siempre una tabla lado a lado y la fuente de cada dato.
- Un dato ausente nunca se interpreta como compatible.
- La comparación manual puede admitir cualquier referencia, indicando qué campos faltan.
- Los candidatos automáticos se limitan inicialmente a registros revisados que tengan los parámetros mínimos de su familia.
- Primera cobertura real estimada con el criterio mínimo actual:
  - MOSFET: 106 registros.
  - IGBT: 10 registros.
  - Diodos rápidos, ultrarrápidos o Schottky: 48 registros.
- No proponer automáticamente IPM, integrados complejos, drivers, reguladores ni lógica.
- Para publicar candidatos automáticos hace falta además normalizar nombres de parámetros y revisar las reglas por familia.

## 3. Ideas, errores y mejoras

### Qué se conserva

- Tipos de aportación, apartado afectado, apodo, título, explicación y cambio sugerido.
- Consulta pública de propuestas aceptadas y botón «Me parece útil».
- Estados de trabajo y respuesta oficial.
- Exportación administrativa a JSON y CSV.

### Mejoras necesarias

- Sustituir el formulario de correo actual, no crear una segunda herramienta duplicada.
- El panel de moderación no puede formar parte de la web pública.
- Las propuestas nuevas deben permanecer privadas hasta su revisión.
- El apoyo debe impedir repeticiones razonables sin crear cuentas, sin prometer una identidad invulnerable.
- Incluir la página de origen automáticamente y conservar el idioma de la interfaz.
- Añadir protección antiabuso y validación de servidor.

## 4. Backend confirmado

La cuenta dispone de IONOS Deploy Now Afiliación Starter y un proyecto PHP. Se utilizará una API PHP con la MariaDB de 2 GB incluida:

- GitHub conserva el código y ejecuta las pruebas.
- Deploy Now publica la aplicación PHP e inyecta las credenciales de MariaDB sin guardarlas en el repositorio.
- MariaDB guarda casos, soluciones, confirmaciones, propuestas, apoyos y auditoría.
- El servidor valida y sanea todas las escrituras y aplica límites de frecuencia.
- El panel administrativo exige autenticación y no expone claves en JavaScript público.
- La web estática de GitHub Pages puede mantenerse durante las pruebas; la funcionalidad colaborativa se activa en el despliegue PHP.

## 5. Orden de implementación

1. Integrar el comparador manual seguro con datos reales y pruebas, sin candidatos automáticos todavía.
2. Preparar el esquema definitivo de la API PHP y la MariaDB de IONOS.
3. Reemplazar `feedback.html` por el módulo mejorado de propuestas.
4. Incorporar «Averías reales por placa».
5. Activar candidatos automáticos solo después de validar las reglas y cobertura de cada familia.
6. Ejecutar pruebas móviles, multilingües, de accesibilidad, seguridad y construcción estática.
7. Consultar y aprobar el resultado antes de publicar.

## 6. Defectos de empaquetado detectados

- `SHA256SUMS.txt` contiene rutas absolutas de Linux, por lo que no es portable a Windows.
- El manifiesto incluye su propio archivo de checksum.
- Cada módulo repite una copia del mismo logotipo.
- Las maquetas no reutilizan los estilos, traducciones, avisos legales ni configuración publicitaria de la aplicación principal.

Los 36 archivos de contenido comprobables sí coinciden con sus hashes después de corregir la ruta al verificarlos.
