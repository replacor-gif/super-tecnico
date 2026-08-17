# ElectroIA Diagram Engine

## Objetivo

ElectroIA Diagram Engine es un motor gráfico neutral para agentes de IA. Recibe una descripción estructurada de un sistema ya decidido por la IA llamante y devuelve un documento electrotécnico legible, comprobado y trazable.

El motor no calcula valores, no selecciona referencias comerciales y no decide la topología eléctrica. Esas responsabilidades pertenecen a la IA o aplicación que lo invoque.

```text
IA o aplicación
  -> documento neutral: símbolos + terminales + redes + tipo de plano
  -> ElectroIA Diagram Engine
       1. valida el contrato y la conectividad
       2. resuelve símbolos normalizados
       3. coloca sobre una rejilla común
       4. enruta conductores ortogonales
       5. comprueba uniones, cruces, etiquetas y legibilidad
  -> SVG + diagnóstico + trazabilidad
```

## Principios obligatorios

1. Un circuito se representa en un único lienzo. Solo se divide en hojas cuando el límite de legibilidad o el formato documental lo exige.
2. Todos los terminales, símbolos, conductores y nodos se ajustan a la misma rejilla lógica.
3. La conectividad procede de una lista de redes; nunca se deduce de la proximidad visual.
4. Un cruce y una unión son entidades diferentes. Las uniones llevan nodo; los cruces no conectados no lo llevan.
5. El símbolo es semántico: contiene identificador, caja, terminales tipados, orientación y geometría normalizada.
6. La presentación se separa del contenido. El mismo modelo puede producir un esquema electrónico, un unifilar o un multifilar mediante perfiles distintos.
7. El motor rechaza entradas ambiguas o incompletas en vez de inventar conexiones.

## Base normativa

La primera implementación adopta un perfil IEC experimental. No se declara certificación normativa: los textos completos de varias normas y la base IEC 60617 requieren licencia. La conformidad formal necesitará una revisión con copias autorizadas.

| Referencia | Función dentro del motor |
| --- | --- |
| IEC 61082-1:2014 | Reglas generales de presentación de documentos, diagramas, dibujos y tablas electrotécnicas. |
| IEC 60617 DB | Identidad y significado de los símbolos gráficos para diagramas. |
| ISO 81714-1:2010 | Reglas básicas para diseñar símbolos gráficos. |
| IEC 81714-2:2006 | Modelo de símbolos legible por ordenador e intercambio entre herramientas. |
| IEC 81714-3:2004 | Clasificación de nodos de conexión y redes. |
| IEC 81346-1:2022 | Estructuración y designaciones de referencia. |
| IEC 61666:2010 + AMD1:2021 | Identificación de terminales dentro de un sistema. |
| IEC 60375:2018 | Sentidos de referencia y polaridades de corrientes y tensiones. |
| IEC 81355-1:2024 | Clasificación de la información y de sus contenedores. |
| ISO 7200:2004 | Campos de cartuchos y cabeceras de documentos técnicos. |
| ISO 5457:1999 | Tamaños y disposición de hojas técnicas. |
| ISO 128-2:2022 | Convenciones generales para líneas. |

Fuentes públicas oficiales:

- https://webstore.iec.ch/en/publication/4469
- https://webstore.iec.ch/en/publication/2723
- https://www.iso.org/standard/42100.html
- https://webstore.iec.ch/en/publication/7506
- https://webstore.iec.ch/en/publication/7507
- https://webstore.iec.ch/en/publication/64021
- https://webstore.iec.ch/en/publication/5705
- https://webstore.iec.ch/en/publication/34065
- https://webstore.iec.ch/en/publication/68281
- https://www.iso.org/standard/35446.html

## Rejilla

El contrato almacena coordenadas en unidades lógicas, no en píxeles. El perfil inicial utiliza como referencia una rejilla primaria de 50 mil (1,27 mm), igual que la recomendación de colocación y conexión de KiCad. La salida SVG transforma cada unidad lógica a una escala visual apropiada sin modificar la conectividad.

Los símbolos pueden emplear una subrejilla para su geometría interna, pero todos sus terminales deben terminar en puntos de la rejilla primaria.

## Contrato de responsabilidades

La IA llamante aporta:

- clase de documento;
- objetos y símbolos deseados;
- referencias y valores ya decididos;
- terminales y redes eléctricas;
- restricciones funcionales o de colocación, si existen.

El motor aporta:

- validación estructural y eléctrica del documento;
- normalización de escala y orientación;
- colocación determinista;
- enrutado ortogonal;
- nodos, cruces, etiquetas, marco y cartucho;
- SVG y diagnóstico legible por máquinas.

## Clases documentales previstas

- `circuit_diagram`: esquema electrónico o de control.
- `single_line_diagram`: representación unifilar; una línea puede resumir varios conductores.
- `multi_line_diagram`: representación multifilar; cada conductor se modela como red independiente.
- `connection_diagram`: conexiones entre bornes, conectores y equipos; fase posterior.
- `installation_diagram`: posición e instalación física; fase posterior.

## Biblioteca actual

La base educativa de Super Técnico conserva 460 fichas y sus SVG de consulta. No todos esos SVG son todavía símbolos CAD: muchos carecen de terminales tipados y puntos de conexión normalizados.

La versión 1.8 dispone de 127 símbolos revisados individualmente. Además de las cuatro familias completas, incorpora un lote HVAC de 17 sensores y otro de 10 señales y comunicaciones industriales: RS-485, CAN, Ethernet, 4-20 mA, 0-10 V, UART, JTAG/SWD, Modbus RTU, BACnet MS/TP y DALI. Los 333 símbolos restantes conservan terminales y estructura provisional, pero el motor los marca como borradores hasta su revisión gráfica.

El primer patrón unifilar representa una alimentación monofásica, contador, protección general, diferencial y tres circuitos derivados. Cada red declara explícitamente cuántos conductores resume la línea.

La migración se realiza sin perder la ficha existente:

1. se enlaza el `catalog_id` actual;
2. se añade una definición CAD con caja, terminales, anclajes y geometría;
3. se valida orientación, escala y conexión sobre la rejilla;
4. se marca la definición como `draft`, `reviewed` o `licensed`;
5. solo los símbolos normalizados pueden entrar en un diagrama generado.

## Criterios de aceptación del núcleo

- cero terminales fuera de rejilla;
- cero conexiones a terminales inexistentes;
- cero referencias duplicadas;
- ninguna unión inferida solo por cruce visual;
- un único lienzo salvo división explícita y justificada;
- resultado determinista para la misma entrada;
- diagnóstico estructurado de errores, advertencias y métricas.
