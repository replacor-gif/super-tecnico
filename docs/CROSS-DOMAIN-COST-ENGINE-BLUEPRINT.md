# Motor transversal de mediciones y costes de Super Técnico

## Objetivo

Todas las herramientas técnicas deben poder producir una medición neutral y estable. Una capa privada posterior asociará esas mediciones con precios unitarios trazables para obtener una horquilla económica orientativa de instalaciones de agua, saneamiento, electricidad, climatización, refrigeración, ventilación, PCI e ICT.

## Separación obligatoria

1. El motor técnico decide soluciones y cantidades.
2. El motor de mediciones normaliza partidas, unidades y especificaciones.
3. La base privada de precios aporta materiales, mano de obra, maquinaria y auxiliares.
4. El estimador aplica edición, ubicación, fecha, mermas e indirectos y devuelve rango bajo, referencia y rango alto.

Los precios nunca deben formar parte de los motores públicos ni de sus respuestas para IAs. Las herramientas públicas pueden entregar mediciones sin precio.

## Trazabilidad mínima de cada precio

- Código estable y unidad.
- Descripción y especificación técnica.
- Fecha base y edición.
- Ámbito geográfico.
- Material, mano de obra, maquinaria y auxiliares separados.
- Fuente, licencia y política de publicación.
- Confianza y fecha de revisión.

## Fuentes admitidas

- Bases de precios de proyecto con licencia vigente.
- Bases abiertas de administraciones públicas.
- Base propia del técnico.
- Ofertas verificadas de proveedores.
- Tarifas verificadas de mano de obra.

Una fuente no publicable puede utilizarse internamente si su licencia lo permite, pero no se expondrá mediante la web ni una API.

## Integración progresiva

Cada motor nuevo debe devolver `bill_of_quantities` con códigos neutrales. El diseñador de tuberías frigoríficas es el primer módulo que aplica este contrato. Después se incorporarán conductos, ventilación, desagües, fontanería y cuadros eléctricos.

## Resultado futuro para el técnico

- Mediciones completas.
- Partidas sin precio que necesitan revisión.
- Coste directo e indirecto.
- Horquilla orientativa, nunca presupuesto vinculante.
- Fecha, zona y fuente utilizadas.
- Exportación a hoja de cálculo y formatos de intercambio de mediciones cuando se definan sus licencias y contratos.
