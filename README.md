# Super Técnico

Guía técnica estática para consulta por marca, código, categoría, tema y variante. La publicación prevista es:

`https://replacor-gif.github.io/super-tecnico/`

## Marcas disponibles

- **Fujitsu / General:** referencia ampliada de split, multisplit, cassette y Airstage VRF.
- **Daikin:** Sky Air, cassette, multisplit, VRV y mandos BRC/Madoka.
- **Gree:** split, U-Match, FLEXX, GMV y mandos cableados.
- **Midea:** AtomX R454B, V6 VRF, split, multisplit, cassette, conductos y WDC-120T2; distingue códigos del mando, display local y placa.
- **Mitsubishi Electric:** M-Series, MXZ, Mr. Slim y CITY MULTI.
- **Panasonic:** RAC, PACi, multisplit, cassette y ECOi/VRF.

## Qué se publica

- Interfaz HTML, CSS y JavaScript.
- Proyecciones JSON preparadas para la web.
- Manifiesto automático de marcas.
- Únicamente imágenes propias o con autorización expresa.

No se publican bases SQLite, PHP, herramientas internas, manuales ni capturas de manuales no autorizadas.

## Prueba local

```bash
python -m unittest discover -s tests -v
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

## Integración con REPLACOR

En IONOS MyWebsite Now, crear un elemento de navegación llamado **Super Técnico** y enlazarlo a la dirección de GitHub Pages. La aplicación se abre como página independiente; no utiliza iframe ni subdominio.

## Libro técnico

La portada incorpora un acceso reservado para:

**Gree y Midea: esquemas y documentación de reparación — edición española de consulta.**

El libro no se publica ni se incorpora al repositorio. El bloque se mantiene como presentación de un futuro producto técnico y el acceso se definirá después de estudiar su comercialización, precio, entrega y protección. Nunca debe enlazarse directamente el archivo PDF desde la versión pública de GitHub Pages.

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
