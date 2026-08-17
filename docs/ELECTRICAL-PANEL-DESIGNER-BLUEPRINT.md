# Super Técnico · Diseñador integral de cuadros eléctricos

Estado: arquitectura base aprobada para desarrollo incremental

Fecha de revisión: 2026-08-17

Ámbito inicial: España y perfiles IEC, con capacidad futura para otros mercados

## 1. Objetivo

Crear una aplicación que transforme una necesidad técnica en un proyecto de cuadro eléctrico completo, verificable y fabricable. No será una calculadora ni un editor CAD aislado. El proyecto tendrá un único modelo de datos del que se derivarán:

- esquema unifilar;
- esquema multifilar y de mando;
- planos de bornas, conexiones, PLC y redes;
- implantación 2D y, posteriormente, gemelo 3D del armario;
- cálculos eléctricos y térmicos;
- lista de materiales, hilos, cables, punteras, etiquetas y mecanizados;
- documentación normativa y de verificación;
- lógica de automatización exportable cuando el controlador lo permita;
- documentación de montaje, puesta en marcha, mantenimiento y revisiones.

La regla principal será:

> La IA o el técnico expresa qué debe hacer el sistema; los motores deterministas calculan y verifican; ElectroIA documenta; una persona competente aprueba los aspectos reglamentarios y de seguridad.

## 2. Qué hacen hoy los referentes

| Producto | Fortaleza que debemos igualar | Límite que Super Técnico puede superar |
|---|---|---|
| EPLAN Electric P8 + Pro Panel | Esquema basado en datos, gemelo 3D, carriles, canaletas, taladros, rutas y longitudes de hilo, salida a fabricación | Curva de aprendizaje alta; el usuario debe saber estructurar el proyecto antes de obtener ayuda |
| WSCAD ELECTRIX AI | Generación asistida, disposición de armarios, comprobación de colisiones, llenado de canaletas y fabricación | La IA está centrada en su propio CAD y no ofrece el buscador normativo multidominio ni el contrato neutral que buscamos |
| Zuken E3.series / E3.panel | Coherencia instantánea entre esquema, panel 2D/3D, cableado, PLC y fabricación | Flujo de ingeniería profesional potente, pero no guiado desde la necesidad real de un técnico generalista |
| SOLIDWORKS Electrical | Integración bidireccional ECAD/MCAD, rutas 3D, interferencias y colaboración | Requiere un ecosistema CAD mecánico completo para aprovechar su mayor ventaja |
| AutoCAD Electrical | Bibliotecas extensas, numeración, referencias cruzadas, bornas, informes y generación de E/S PLC | El dibujo sigue teniendo mucho peso y el cálculo reglamentario profundo necesita herramientas adicionales |
| Siemens Electrical Designer / TIA Selection Tool | Dimensionado IEC 60204-1, cortocircuito, cables, arrancadores y documentación con combinaciones verificadas | Muy eficaz dentro del catálogo y flujo Siemens; no es neutral entre fabricantes ni cubre todo el proyecto documental |
| Schneider EcoStruxure Power Design | Red unifilar, cortocircuito, caída de tensión, selectividad, filiación y protección | El cálculo es fuerte, pero no sustituye un ECAD completo ni una plataforma neutral de automatización y fabricación |

Fuentes oficiales de la revisión:

- EPLAN Pro Panel: https://www.eplan.com/gb-en/products/eplan-pro-panel/
- WSCAD Cabinet Engineering: https://www.wscad.com/en/engineering-disciplines/cabinet-engineering/
- WSCAD ELECTRIX AI: https://www.wscad.com/en/electrix/
- Zuken E3.panel: https://www.zuken.com/us/product/e3series/electrical-control-panel-design/
- SOLIDWORKS Electrical 3D: https://www.solidworks.com/product/solidworks-electrical-3d
- AutoCAD Electrical: https://www.autodesk.com/uk/products/autocad/included-toolsets/autocad-electrical
- Siemens Electrical Designer: https://www.siemens.com/en-gb/industries/industrial-machinery/panel-building-electrical-designer/
- Schneider Ecodial: https://www.se.com/es/es/product-range/61013-ecostruxure-power-design-ecodial/

## 3. Nuestra ventaja diferencial

Super Técnico ya dispone de activos que normalmente están separados:

1. Buscador de reglamentos oficiales con procedencia, huella de versión y detección de cambios.
2. ElectroIA como motor gráfico neutral con rejilla común, símbolos, terminales, redes y diagnósticos.
3. Base de componentes y características técnicas.
4. Motores de cálculo deterministas y trazables.
5. Conocimiento de climatización, refrigeración, ventilación, instalaciones y mantenimiento.
6. Contratos pensados para usuarios humanos, programas externos y cualquier IA.

La diferenciación no será «dibujar más rápido», sino mantener unidos intención, cálculo, norma, componente, esquema, armario, programa y mantenimiento. Una modificación debe propagarse a todas las vistas y volver a verificarse.

## 4. Los cinco tipos de proyecto iniciales

La aplicación preguntará primero qué se está construyendo porque la normativa y los controles cambian:

1. **Cuadro de distribución para uso ordinario (DBO)**: vivienda, pequeño comercio o instalación equivalente.
2. **Cuadro de potencia y control industrial (PSC)**: distribución, motores, variadores, bombas, ventiladores y procesos.
3. **Equipo eléctrico de una máquina**: mando, potencia, paradas, resguardos, accionamientos y seguridad funcional.
4. **Automatización de edificio o HVAC**: climatización, ventilación, salas técnicas, BMS y señales de campo.
5. **Control embebido o IoT**: Arduino, Raspberry Pi, microcontroladores, gateways y placas específicas.

Un proyecto puede combinar varios tipos, pero siempre tendrá un perfil principal y subperfiles explícitos.

## 5. Experiencia de uso

### 5.1 Modo guiado para el técnico

El técnico no empezará dibujando. La aplicación le pedirá solo datos que no pueda deducir:

1. Qué debe hacer el cuadro.
2. Alimentación disponible y lugar de instalación.
3. Cargas: motores, resistencias, iluminación, electrónica y servicios auxiliares.
4. Sensores, mandos y actuadores.
5. Secuencia de funcionamiento expresada con frases o bloques sencillos.
6. Preferencia o existencia de PLC, Arduino, Raspberry Pi u otro controlador.
7. Condiciones especiales: humedad, polvo, exterior, temperatura, pública concurrencia, incendio, seguridad de máquina o continuidad de servicio.

Con esos datos propone una solución completa y marca únicamente las decisiones que necesitan confirmación.

### 5.2 Espacio de trabajo continuo

El proyecto se mostrará como una sola aplicación con vistas coordinadas:

- **Resumen**: qué hace, estado y advertencias críticas.
- **Potencia**: cargas, protecciones, cables, cortocircuito y selectividad.
- **Control**: secuencia, señales, relés, PLC y redes.
- **Esquemas**: unifilar, multifilar, mando, bornas y cableado.
- **Armario**: envolvente, carriles, canaletas, puerta, reservas, calor y rutas.
- **Materiales**: componentes, alternativas compatibles y disponibilidad de datos.
- **Normativa**: reglas aplicadas, evidencia, versión y aspectos por revisar.
- **Fabricación**: listas de corte, hilos, punteras, etiquetas, taladros y exportaciones.
- **Puesta en marcha**: verificaciones, medidas, pruebas funcionales y documento final.

Las vistas no son proyectos separados: son representaciones del mismo grafo técnico.

### 5.3 Tres niveles de interacción

- **Guiado**: el sistema decide la presentación y pregunta lo mínimo.
- **Profesional**: permite fijar fabricante, aparato, curva, sección, posición, borna y ruta.
- **IA/API**: una IA externa envía y recibe el proyecto estructurado sin depender de la interfaz humana.

## 6. Arquitectura funcional

```text
Necesidad del usuario / IA
        ↓
Normalizador de requisitos
        ↓
Perfil de aplicabilidad normativa
        ↓
Grafo único del proyecto
   ├── Motor de cargas y alimentación
   ├── Motor de protecciones y conductores
   ├── Motor de automatización y E/S
   ├── Motor de seguridad funcional
   ├── Motor térmico y envolvente
   ├── Motor de implantación y cableado
   ├── Selector de componentes
   └── Registro de evidencias y decisiones
        ↓
ElectroIA + documentos + fabricación + exportaciones
```

### 6.1 Grafo único del proyecto

Cada objeto tendrá una identidad estable y varias representaciones:

- una bobina de contactor, sus contactos y su pieza física son el mismo dispositivo;
- un canal de PLC enlaza señal de campo, borna, conductor, dirección, variable y lógica;
- una protección enlaza cálculo, componente, símbolo, huella física y evidencia normativa;
- toda borna distingue lado de campo, lado de cuadro, puente, reserva y destino;
- cualquier cambio invalida solo los cálculos o documentos que dependan de él.

### 6.2 Motores deterministas

La IA no debe inventar resultados numéricos. Los motores versionados cubrirán progresivamente:

- intensidad de diseño y simultaneidad;
- secciones, caída de tensión y capacidad térmica del conductor;
- corrientes de cortocircuito y poder de corte;
- coordinación, selectividad y protección de respaldo;
- protección diferencial y contra sobretensiones;
- circuitos de motor y categorías de empleo;
- transformadores y fuentes de control;
- balance de potencia de 24 V, 5 V y 3,3 V;
- pérdidas térmicas, temperatura interior y ventilación del armario;
- llenado de canaletas y ocupación de carriles;
- longitudes de hilos y segregación de potencia, mando, analógica y comunicaciones;
- reserva de espacio, E/S, bornas y potencia.

Cada resultado contendrá entradas, versión de motor, regla o fuente, validez y advertencias. La interfaz principal mostrará resultados; los detalles quedarán disponibles para auditoría.

## 7. Normativa y conformidad

La herramienta seleccionará un perfil de aplicabilidad; nunca marcará «cumple» solo porque exista un cálculo.

### 7.1 Base legal inicial

- REBT, Real Decreto 842/2002 e ITC, texto consolidado y listado de normas actualizado.
- Directiva 2014/35/UE de baja tensión cuando sea aplicable al producto.
- Directiva 2014/30/UE de compatibilidad electromagnética.
- Real Decreto 1644/2008 para máquinas durante su vigencia.
- Reglamento (UE) 2023/1230 sobre máquinas desde su fecha general de aplicación, 20/01/2027.
- Normativa autonómica, local, de actividad y de emplazamiento que corresponda.

### 7.2 Familias técnicas de referencia

- IEC 61439-1 y parte aplicable: conjuntos de aparamenta de baja tensión.
- IEC 61439-2: conjuntos de potencia y control para personal instruido o cualificado.
- IEC 61439-3: cuadros de distribución operados por personas ordinarias.
- IEC 60204-1: equipo eléctrico de máquinas.
- IEC TR 60890: cálculo de elevación de temperatura cuando resulte aplicable.
- IEC 60947: aparamenta, interruptores, contactores y arrancadores.
- IEC 60529: grados de protección IP.
- IEC 61082-1: preparación de documentación electrotécnica.
- IEC 81346-1: estructura y designaciones de referencia.
- IEC 60617: símbolos gráficos para diagramas.
- IEC 61131-3 e IEC 61131-10: programación e intercambio de proyectos PLC.
- IEC 62714 / AutomationML: intercambio de datos de ingeniería.
- ISO 13849-1 o IEC 62061: funciones de seguridad de máquinas, según el método elegido.
- IEC 62443: ciberseguridad de automatización y control industrial cuando exista conectividad.

Las normas UNE, EN, IEC e ISO protegidas se registrarán por referencia, edición, alcance y estado. No se almacenará ni publicará su texto íntegro sin licencia. La edición aplicable en España se verificará contra el listado reglamentario y la adopción UNE vigente.

### 7.3 Niveles de evidencia

- **Fuente oficial localizada**: texto legal o referencia técnica encontrada.
- **Regla revisada**: interpretación estructurada, alcance definido y revisión humana.
- **Resultado determinista**: cálculo efectuado con regla revisada y motor versionado.
- **Verificación pendiente**: falta dato, ensayo, tabla de fabricante, licencia o criterio profesional.

La aplicación mostrará por separado:

- requisitos satisfechos por cálculo;
- requisitos cubiertos por selección de producto;
- verificaciones de diseño aún pendientes;
- ensayos y comprobaciones de rutina;
- decisiones que debe firmar el proyectista, fabricante del conjunto o integrador.

## 8. PLC, Arduino, Raspberry Pi y automatización

### 8.1 Modelo neutral de controlador

Todo controlador se describirá mediante:

- alimentación y consumo;
- CPU, firmware y entorno de programación;
- módulos y canales de E/S;
- tipo eléctrico de cada canal;
- comunes, aislamiento y protección;
- direcciones físicas y variables simbólicas;
- buses y topología de red;
- ciclo, watchdog, retentividad y comportamiento al arrancar o fallar;
- nivel de seguridad permitido;
- huella física, temperatura, montaje y disipación;
- artefactos exportables y procedimiento de copia de seguridad.

Esto permite tratar por igual un PLC Siemens, Schneider, Wago, Beckhoff, Omron, Mitsubishi, Allen-Bradley, un objetivo CODESYS o un controlador específico sin deformar el proyecto alrededor de una marca.

### 8.2 Programación PLC

El sistema diseñará primero una especificación neutral:

- lista de E/S;
- tabla de símbolos y direcciones;
- secuencia funcional;
- estados, interbloqueos y alarmas;
- modos manual, automático, mantenimiento y fallo;
- temporizaciones, contadores y parámetros;
- matriz causa-efecto;
- pruebas funcionales.

Después generará, cuando sea técnicamente posible:

- Structured Text, Ladder o FBD basados en IEC 61131-3;
- PLCopen XML / IEC 61131-10;
- AutomationML para intercambio con herramientas de ingeniería;
- tablas CSV/XLSX compatibles con entornos propietarios;
- documentación aunque el código final deba completarse en la herramienta del fabricante.

### 8.3 Arduino

Se distinguirán dos clases:

1. **Placa de desarrollo**: Uno, Nano, Mega, Portenta u otra placa con GPIO de 5 V o 3,3 V. Necesita interfaces, aislamiento, protección, fuente, borneras y envolvente apropiadas antes de conectarse a señales industriales.
2. **Arduino industrial**: Opta y Portenta Machine Control, con perfiles de E/S, comunicaciones y montaje específicos.

Arduino CLI permite compilar y cargar proyectos desde una interfaz de máquina. Arduino PLC IDE permite programar Opta y Portenta Machine Control con lenguajes IEC 61131-3. Super Técnico podrá generar el proyecto fuente, verificar el mapa de pines, compilar en un entorno aislado y devolver diagnósticos; la carga física requerirá autorización expresa del técnico.

### 8.4 Raspberry Pi

Raspberry Pi se modelará principalmente como:

- ordenador de borde;
- HMI o servidor local;
- gateway OPC UA, MQTT, Modbus u otras redes;
- registrador, analizador o sistema de visión;
- controlador no seguro cuando se utilice una arquitectura adecuada.

Para producto o uso industrial se priorizarán Compute Module 4/5 y portadoras industriales. Se verificarán fuente, almacenamiento, temperatura, refrigeración, watchdog, pérdida de energía, arranque, actualizaciones, ciberseguridad y aislamiento de E/S.

### 8.5 Regla de seguridad obligatoria

Una placa Arduino genérica o Raspberry Pi no se aceptará por defecto como elemento que ejecuta una función de seguridad. Parada de emergencia, resguardos y otras funciones de reducción de riesgo necesitarán arquitectura y componentes evaluados según ISO 13849-1 o IEC 62061: relé de seguridad, PLC de seguridad u otra solución validada. La informática convencional podrá supervisar, registrar o solicitar acciones, pero no anular la cadena segura.

## 9. Documentos y fabricación

La salida mínima de un proyecto competente será:

1. Portada, índice, revisiones y datos de proyecto.
2. Descripción funcional y lista de cargas.
3. Esquema unifilar.
4. Esquemas de potencia y mando.
5. Tabla de E/S y red de automatización.
6. Diagrama de bornas y conexiones externas.
7. Implantación del armario y puerta.
8. Lista de materiales con alternativas controladas.
9. Lista de hilos, cables, punteras y etiquetas.
10. Memoria de cálculo y verificaciones.
11. Requisitos normativos aplicados y pendientes.
12. Plan de pruebas y puesta en marcha.
13. Copia de seguridad de lógica y parámetros.
14. Paquete de mantenimiento y versión «as built».

Para proyectos grandes, ElectroIA usará un lienzo de proyecto continuo con división automática en hojas cuando sea necesario. Las hojas conservarán referencias cruzadas, continuidad de redes y navegación directa; nunca serán dibujos independientes sin relación.

## 10. Fases de construcción

### Fase 0 · Cimientos

- contrato único de proyecto;
- registro de normas y aplicabilidad;
- catálogo neutral de controladores y tipos de E/S;
- nuevas familias de símbolos ElectroIA para automatización;
- registro de decisiones, evidencias y versiones.

### Fase 1 · Primer cuadro completo y útil

Caso patrón: cuadro trifásico de motor o bomba con protección, contactor, relé térmico, marcha/parada, automático/manual, seta de emergencia, señales, borneras y controlador opcional.

Debe generar cálculos básicos, todos los esquemas, lista de materiales, bornas, hilos, plano 2D y verificación guiada.

### Fase 2 · Automatización profesional

- PLC y módulos de E/S;
- redes industriales;
- secuencias, alarmas y matriz causa-efecto;
- exportación PLCopen XML, ST/Ladder/FBD y tablas de fabricante;
- Arduino industrial y Raspberry Pi como perfiles controlados.

### Fase 3 · Armario inteligente

- colocación automática en carriles y puerta;
- colisiones, distancias, reserva y canaletas;
- cálculo térmico;
- rutas y longitudes de hilos;
- preparación de taladros y fabricación.

### Fase 4 · Gemelo 3D e interoperabilidad

- geometrías 3D de fabricantes;
- importación/exportación AutomationML, STEP, DXF/DWG y formatos de fabricación permitidos;
- realidad aumentada para montaje y mantenimiento;
- colaboración, revisiones y comparación de versiones.

## 11. Criterios que definirán «la mejor»

No se medirá por el número de botones. La aplicación debe demostrar:

- un técnico nuevo completa un cuadro sencillo sin formación CAD especializada;
- ningún cambio deja esquema, BOM, bornas o armario incoherentes;
- toda cifra crítica identifica motor, entradas, versión y evidencia;
- las dudas normativas se muestran; no se ocultan bajo una falsa marca de cumplimiento;
- el mismo proyecto sirve a una persona, a una IA y a fabricación;
- el sistema admite fabricantes diferentes y evita dependencia innecesaria;
- los modos móviles permiten revisar, confirmar, mover y anotar con precisión;
- los artefactos exportados se pueden validar automáticamente;
- la seguridad funcional y la ciberseguridad tienen límites explícitos;
- los proyectos reales alimentan métricas de errores, tiempo ahorrado y correcciones.

## 12. Primer bloque de desarrollo recomendado

Antes de dibujar una interfaz extensa, el siguiente bloque debe ser:

1. normalizar símbolos de PLC, CPU, fuentes, módulos DI/DO/AI/AO, seguridad, HMI y buses;
2. crear el motor de lista de E/S y asignación de bornas;
3. enlazar cada canal con ElectroIA y con una huella física provisional;
4. implementar el caso patrón de motor/bomba;
5. validar el proyecto con un técnico desde móvil y escritorio;
6. solo después añadir colocación automática del armario.

Esta secuencia conserva la esencia de Super Técnico: primero un resultado útil y comprensible; después profundidad profesional desplegable.
