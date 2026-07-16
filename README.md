# Super Técnico

Biblioteca técnica estática para consulta por marca, categoría, tema y variante. La publicación prevista es:

`https://replacor-gif.github.io/super-tecnico/`

## Marcas disponibles

- **Fujitsu / General:** marca de referencia principal.
- **Daikin:** Referencia V1 de prueba con 16 registros técnicos. Quince registros mantienen visible la advertencia de página o manual pendiente de verificar.

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

## Límites de esta versión

- Aplicación pública, gratuita y sin cuentas, formularios ni pagos.
- GitHub Pages no debe utilizarse para convertirla en un SaaS comercial.
- La base SQLite maestra se mantiene fuera del repositorio y se usa únicamente para generar nuevas proyecciones web.
