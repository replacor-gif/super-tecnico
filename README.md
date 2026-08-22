# Super Técnico

Portal técnico estático con herramientas independientes. La publicación es:

`https://replacor-gif.github.io/super-tecnico/`

## Herramientas disponibles

- **Biblioteca técnica HVAC:** consulta por marca, código, categoría, tema y variante.
- **Identificador OEM de placas HVAC:** cuando falta la marca comercial, relaciona el código impreso en la PCB con 21 plataformas posibles y enlaza el error con la base del fabricante electrónico disponible.
- **Identificador SMD:** búsqueda por marcaje o referencia con filtros opcionales de encapsulado, patillas, fabricante, tipo y designador de placa.
- **Calculadoras técnicas:** 15 herramientas de electrónica y climatización con unidades, fórmulas, esquemas y advertencias; incluye LED, Zener, 555 y bus DC monofásico/trifásico.
- **Asistente frigorista:** conversión P/T, estudio progresivo y diagnóstico del ciclo medido mediante diagrama presión-entalpía (Mollier), sin exigir mediciones que el técnico no tenga.
- **Diseñador de conductos:** plano de estancias, trazado y dimensiones de la red de aire.
- **Desagües de condensados:** caudal acumulado, pendiente, caída y diámetro interior por tramo para varias unidades.
- **Normativa técnica:** búsqueda natural dentro de 18 reglamentos oficiales, con jerarquía de ITC, artículo, apartado y tabla cuando puede extraerse de forma fiable; pide contexto cuando la consulta no tiene una única respuesta aplicable.
- **Referencias de componentes:** consulta por referencia, marcado, fabricante, categoría, encapsulado y parámetros eléctricos.
- **Conectores y pinouts:** buscador móvil de conectores con contactos, variante, lado, orientación, seguridad, trazabilidad y una edición PDF normalizada; publica además un contrato neutral para motores e IAs.
- **Plataformas embebidas:** catálogo móvil de 41 placas Arduino, ESP, Raspberry Pi y plataformas profesionales, con ficha rápida, preselección guiada, riesgos de integración y procedencia verificable por página.
- **Comparador documental:** contraste lado a lado de referencias reales y búsqueda conservadora de candidatos MOSFET, IGBT y diodos rápidos revisados.
- **Averías reales por placa:** casos aportados por técnicos, buscables por referencia o explorables mediante filtros de marca y equipo; se publican únicamente tras moderación.
- **Ideas y mejoras:** propuestas públicas, apoyos de la comunidad y aportaciones privadas pendientes de revisión.

## Integración futura con sistemas de IA

`ia-integracion.html` y `data/ai/` forman la capa pública de descubrimiento de **Super Técnico para IAs**. Separan el futuro servicio de conocimiento técnico del motor gráfico ElectroIA y describen herramientas, niveles de respuesta, trazabilidad, seguridad y medición sin activar todavía un servicio remoto.

Estado actual:

- contratos públicos y `llms.txt` disponibles;
- comprobación de cobertura gratuita diseñada;
- respuestas autenticadas y por consumo todavía desactivadas;
- acceso directo a la base y exportación masiva no permitidos;
- publicación en registros MCP y catálogos de plataformas pendiente del servidor remoto y de su revisión de seguridad.

Para regenerar el inventario de preparación:

```bash
python tools/audit_ai_readiness.py
```

Los módulos de normativa, desagües, conectores y plataformas embebidas publican contratos específicos en `data/regulations/tool-manifest.json`, `data/condensate/tool-manifest.json`, `data/connectors/tool-manifest.json` y `data/embedded-platforms/tool-manifest.json`. Normativa, conectores y plataformas embebidas ya ofrecen consulta HTTP pública limitada; el resto de motores continúa sin ejecución remota.

El primer registro común de motores está en `data/core/motor-registry.json`. Usa **SINAPSYS** como nombre de la futura capa de orquestación y mantiene separados los estados reales: catálogo disponible en navegador, ElectroIA en vista previa privada y ejecución remota pendiente. La marca pública seguirá evolucionando gradualmente de Super Técnico hacia REPLACOR.

## Actualizar la normativa oficial

Las fuentes se administran desde `data/regulations/sources.json`. Para descargar de nuevo los PDF oficiales, extraer el texto y regenerar catálogo, índices y huellas digitales:

```bash
python tools/update_regulations.py
```

Puede limitarse a una fuente con `--document rebt` o reconstruir los índices desde las copias guardadas con `--no-download`. Si cambia una huella, `data/regulations/update-report.json` obliga a revisar manualmente las reglas de cálculo que dependan de ese documento. Los textos UNE, UNE-EN e IEC no se almacenan ni distribuyen sin licencia.

Los índices de búsqueda separan texto normativo, tablas, encabezados e índices documentales. Conservan la ruta del resultado y penalizan los índices para que una referencia del sumario no se confunda con el contenido aplicable.

El identificador SMD publica 439 candidatos de seis fabricantes, todos con marcaje, encapsulado, patillaje, parámetros eléctricos y una fuente oficial. Cuando un código tiene varios significados, muestra todos los candidatos cerrados y no selecciona ninguno automáticamente.

La base de referencias publica 11.532 componentes y 8.363 parámetros. Separa 8.205 fichas oficiales, revisadas o confirmadas en índices de fabricante de 3.327 candidatos históricos pendientes de contrastar. Para priorizar cobertura, admite dos niveles: ficha desarrollada y ficha índice oficial. La primera contiene parámetros cuando están documentados; la segunda confirma referencia, fabricante, familia, categoría, catálogo y página sin inventar valores que todavía no se hayan extraído. La ampliación masiva inicial incorpora 6.551 referencias de los catálogos oficiales de Nexperia y Texas Instruments, además de IPM, MOSFET, lógica, temporizadores, operacionales, reguladores y drivers ya desarrollados. Ninguna coincidencia se presenta como sustitución automática.

## Versión beta e idiomas

El alcance, las puertas de salida y el trabajo pendiente de la primera versión se mantienen en `docs/V1-COMPETENCE-AUDIT.md`, separado del informe de preparación comercial para IAs.

Super Técnico se publica expresamente como una **beta en construcción**. Todas las pantallas incluyen:

- aviso permanente de revisión y uso responsable;
- selector persistente de español, inglés, portugués y francés;
- acceso al formulario de errores, sugerencias, traducciones e información faltante;
- formulario moderado cuando la aplicación está desplegada en IONOS y enlace alternativo a `info@replacor.com` cuando se consulta la versión estática.

La interfaz es multilingüe. Las fichas técnicas conservan durante la beta el texto español revisado hasta que cada traducción técnica se valide, evitando que una traducción automática altere valores, protecciones o procedimientos.

## Publicidad

La integración de AdSense está centralizada en `data/ads-config.json` y permanece
desactivada mientras no exista un identificador real `ca-pub-…`. La aplicación
no descarga scripts publicitarios ni muestra espacios vacíos en ese estado.

Al configurar el editor, el constructor valida la CMP, los identificadores de
espacio y genera `ads.txt` automáticamente. Los anuncios están reservados para
las páginas de contenido técnico; el formulario de sugerencias no contiene
emplazamientos publicitarios.

## Marcas disponibles

- **Aermec:** enfriadoras y bombas de calor con controles Moducontrol, pCO y plataformas WFN/WFI; separa mensajes textuales cuando el fabricante no publica un número universal.
- **AUX:** split, Light Commercial, cassette/conductos, multisplit, mando XK y ARV/VRF; separa display interior, mando, pilotos exteriores D1/D2/D3, placa comercial y código ARV por indicadores.
- **Carrier:** AquaSnap, 30XF-Z, SmartVu, Connect Touch y Pro-Dialog+; incluye alarmas de circuito, VFD, EXV, bombas, caudal, aceite y comunicaciones.
- **CIAT:** Aquaciat Power, Connect Touch y Vectic; incluye alarmas de enfriadoras, subcódigos VFD, free-cooling, hidráulica y programación.
- **Fujitsu / General:** referencia ampliada de split, multisplit, cassette y Airstage VRF.
- **Daikin:** Sky Air, cassette, multisplit, VRV y mandos BRC/Madoka.
- **Gree:** split, U-Match, FLEXX, GMV y mandos cableados.
- **Haier:** Advanced Plus, Arctic Multi, FlexFit Multi/Pro, cassette, MRV-S y mandos YR-E17/YR-E16B; relaciona códigos distintos entre unidad, mando y placa.
- **Hitachi:** RAC/PAC, H-LINK, Central Station y SET FREE; separa alarmas de unidad, red, control central y funcionamiento degradado.
- **Hisense:** split, comercial, cassette, multisplit, controles HYXE/HYRE y Hi-FLEXi VRF; separa códigos de mando, display interior, piloto/tubo digital exterior y red H-NET.
- **Hitecsa:** rooftops, enfriadoras y controles µKR3/pCO; contempla circuitos, bombas, antihielo, caudal, maestro/esclavo e historial.
- **Keyter:** enfriadoras y bombas de calor con PERSEA y TH-Tune; incluye códigos numéricos, textos de alarma, circuitos, ventiladores, bombas y configuración.
- **Lennox:** rooftops Baltic/Flexair con CLIMATIC 60; incluye alarmas de unidad, circuito, sensores, ventilación, economizador y comportamiento degradado.
- **LG:** Single Zone, Multi F/Multi F MAX, cassette, MULTI V 5, mandos PREMTB/PREMTC y LGMV.
- **McQuay (histórica):** equipos acreditados de la etapa McQuay con MicroTech II y Chiller System Manager; no mezcla equipos Daikin Applied posteriores.
- **Midea:** AtomX R454B, V6 VRF, split, multisplit, cassette, conductos y WDC-120T2; distingue códigos del mando, display local y placa.
- **Mitsubishi Electric:** M-Series, MXZ, Mr. Slim y CITY MULTI.
- **Mitsubishi Heavy Industries:** RAC SRK/SRC, PAC, cassette/conductos, SCM multisplit, mandos RC-EX3 y KX/KXZ VRF; separa pilotos RUN/TIMER, códigos del mando, LED de la exterior y subcódigos de siete segmentos.
- **Panasonic:** RAC, PACi, multisplit, cassette y ECOi/VRF.
- **Roca (histórica):** AVO/BLI/BCI/BVI, termostato DPC-1 y enfriadoras YLCC/YCSA de la etapa Clima Roca York. Solo se admiten familias con fabricación o procedencia industrial acreditada; se excluyen equipos modernos de origen dudoso.
- **Samsung:** RAC, FJM, DVM S/S2, MCU, mandos y herramientas; incluye tablas visuales separadas de pilotos exteriores 9K/12K y 18K/24K/30K.
- **SANYO (histórica):** W-2WAY, 2WAY y 3-WAY ECO-i documentadas como SANYO; incluye mandos, dos pilotos, direccionamiento y respaldo sin mezclar Panasonic posterior.
- **Sharp:** códigos principal–subcódigo, obtención por mando, Wire Check multisplit, comunicación serie, servicio y valores eléctricos.
- **Systemair:** climatizadores Access/Topvex y enfriadoras SysAer; incluye clases de alarma, identificación numérica, alarmas AL01–AL25, historial y rearme.
- **TCL:** split inverter, comercial, cassette, conductos, Free Match, portátil y TMV6+ VRF; relaciona display, mando, cuatro pilotos cassette y tabla exterior de 1–17 destellos.
- **Toshiba:** SEIYA/RAC, multisplit, RAV, cassette y SMMSe/SMMS-u VRF; relaciona códigos de mando con tablas visuales D800–D805 sin mezclar familias.
- **Trane:** IntelliPak/Symbio 800, Tracer y enfriadoras CGAM; distingue diagnósticos informativos, bloqueo de circuito, bloqueo de unidad y rearme.
- **YORK / Johnson Controls:** Sun Premier, YPAL y controles de rooftop; incluye alarmas y fallos por código, severidad, circuito, economizador y condensados.
- **Chigo:** split, cassette, DC inverter y multisplit; conserva todos los significados alternativos de E1/E2/E3/E5/E8 según plataforma y punto de lectura.

## Qué se publica

- Interfaz HTML, CSS y JavaScript.
- Proyecciones JSON preparadas para la web.
- Manifiesto automático de marcas.
- Catálogo SMD público formado únicamente por registros contrastados y autorizados.
- Proyección pública de referencias de componentes, dividida en fragmentos para cargar cada ficha bajo demanda.
- Proyección pública de 47 patrones OEM de placas y 15 formatos ambiguos bloqueados.
- Copias oficiales públicas de la normativa registrada, con edición, procedencia, huella e índice por página.
- Únicamente imágenes propias o con autorización expresa.

Los candidatos históricos se publican únicamente como índices factuales de localización, con su procedencia y una advertencia visible de verificación. No se publican bases SQLite, PHP, herramientas internas, manuales ni capturas de manuales no autorizadas.

## Prueba local

```bash
python -m unittest discover -s tests -v
node tests/test_calculations.js
node tests/test_datasheet_finder.js
node tests/condensate_drain_engine.test.js
python tools/build_static.py --source . --output dist
python -m http.server 8080 --directory dist
```

Abrir `http://127.0.0.1:8080/`.

## Añadir otra marca

1. Crear `data/brands/<marca>/`.
2. Añadir `brand.json` y la carpeta `web/` con la misma estructura que Fujitsu/General.
3. Mantener `publish_media` en `false` salvo que todas las imágenes de la carpeta estén autorizadas.
4. Ejecutar las pruebas y el constructor.
5. Subir los cambios a `main`.

El constructor recorre automáticamente las carpetas de marca, valida sus recuentos y genera `data/brands/index.json`. No hay que modificar la interfaz.

## GitHub Pages

El flujo `.github/workflows/pages.yml`:

1. Ejecuta las pruebas.
2. Construye `dist/`.
3. Comprueba que no existan archivos privados o de servidor.
4. Publica el artefacto mediante GitHub Pages.

En el repositorio, seleccionar **Settings → Pages → Source: GitHub Actions** una sola vez.

GitHub Pages recibe exclusivamente el resultado estático: no contiene PHP, panel de moderación, esquema SQL, credenciales ni bases privadas. El comparador funciona allí con los datos públicos; los módulos colaborativos muestran un aviso hasta utilizar el despliegue PHP.

## IONOS Deploy Now PHP

La versión completa utiliza el contrato **IONOS Deploy Now PHP Project** y su MariaDB incluida. La carpeta `.deploy-now/` contiene la plantilla de configuración y ejecuta la migración del esquema después de cada despliegue.

Las credenciales de MariaDB se inyectan automáticamente por IONOS. En el proyecto deben configurarse además, como variables protegidas:

- `ST_APP_SECRET`: cadena aleatoria larga para anonimizar apoyos y aplicar límites.
- `ST_ADMIN_PASSWORD_HASH`: resultado de `password_hash` de la contraseña de moderación.
- `ST_ALLOWED_ORIGINS`: orígenes adicionales separados por comas; puede quedar vacío si todo se sirve desde el mismo dominio.
- `ST_TURNSTILE_SECRET` y `ST_REQUIRE_TURNSTILE`: opcionales; la beta comienza con límites de frecuencia del servidor.

El panel privado está en `moderacion.html`, lleva `noindex`, exige sesión segura y no se enlaza desde la web pública. Permite revisar, publicar, rechazar y exportar registros a JSON o CSV.

## Integración con REPLACOR

En IONOS MyWebsite Now, crear un elemento de navegación llamado **Super Técnico** y enlazarlo a la dirección de GitHub Pages. La aplicación se abre como página independiente; no utiliza iframe ni subdominio.

## Libro técnico

La portada incorpora un acceso reservado para:

**Gree y Midea: esquemas y documentación de reparación — edición española de consulta.**

El libro se publica gratuitamente en la portada de Super Técnico:

`recursos/libro-electronica-inverter-replacor.pdf`

La edición web contiene 501 páginas y está optimizada para lectura y descarga desde el navegador.

## Preparación para publicidad — edición 3

La interfaz incluye dos contenedores publicitarios semánticos y ocultos: uno después de los accesos principales y otro al terminar el contenido técnico. No se carga ninguna red publicitaria, cookie ni rastreador en la versión actual.

Antes de activarlos:

1. Migrar la aplicación a un alojamiento apto para un proyecto comercial.
2. Configurar privacidad, consentimiento y cookies según corresponda.
3. Reservar dimensiones fijas para evitar saltos de pantalla.
4. No insertar anuncios dentro de advertencias, procedimientos, tablas ni entre interpretaciones de un mismo error.

GitHub Pages seguirá utilizándose para desarrollo y pruebas públicas. Sus condiciones indican que no está pensado como alojamiento gratuito para operar un negocio en línea o proporcionar software comercial como servicio: https://docs.github.com/es/pages/getting-started-with-github-pages/github-pages-limits

## Límites de esta versión

- Aplicación pública, gratuita y sin cuentas, formularios ni pagos.
- GitHub Pages no debe utilizarse para convertirla en un SaaS comercial.
- La base SQLite maestra se mantiene fuera del repositorio y se usa únicamente para generar nuevas proyecciones web.
