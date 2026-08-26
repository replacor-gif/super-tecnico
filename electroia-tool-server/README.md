# ElectroIA Tool Server

ElectroIA es un motor gráfico electrotécnico neutral. No contiene un modelo de IA,
no necesita una clave de un proveedor y no genera cargos de inferencia por sí mismo.

La IA conectada interpreta la intención del usuario o una fotografía y llama a una
de estas herramientas:

- `electroia_get_capabilities`
- `electroia_get_diagram_contract`
- `electroia_search_symbols`
- `electroia_get_symbol`
- `electroia_compile_diagram`
- `electroia_render_diagram`
- `electroia_analyze_request`
- `electroia_generate_relay_driver`
- `electroia_generate_temperature_fan`

La IA llamante decide la topología, los valores y los componentes. La herramienta
`electroia_compile_diagram` acepta nombres técnicos de símbolos, referencias locales y
alias seguros de terminales; ElectroIA los resuelve, asigna referencias, coloca, comprueba
la conectividad y devuelve el documento neutral y el SVG. `electroia_render_diagram`
continúa disponible cuando la IA necesita control exacto de bajo nivel.

Ejemplo reducido del compilador:

```json
{
  "tool": "electroia_compile_diagram",
  "arguments": {
    "spec": {
      "title": "Fuente, protección y carga",
      "components": [
        { "id": "source", "symbol_query": "fuente continua", "value": "24 V DC" },
        { "id": "load", "symbol_id": "ST-GENERIC-2P", "value": "Carga" }
      ],
      "nets": [
        { "id": "24V", "role": "power", "connections": [{ "component": "source", "port": "+" }, { "component": "load", "port": "1" }] },
        { "id": "0V", "role": "ground", "connections": ["source.-", "load.2"] }
      ]
    }
  }
}
```

La biblioteca externa contiene las 501 fichas revisadas del catálogo y 3 elementos auxiliares
del motor. Las 19 familias públicas tienen geometría y terminales revisados. Los 75 bloques
funcionales cuyo bornero depende de fabricante o variante no se convierten en pinout físico
sin indicar el modelo exacto y consultar su documentación.

La versión 0.15 añade límites deterministas antes del renderizado: 256 KiB por documento,
200 símbolos, 400 redes, 100 conexiones por red y 2.000 conexiones totales. La política del
futuro servicio remoto está publicada como datos legibles por máquinas, pero el transporte
HTTP de ejecución continúa desactivado hasta completar las pruebas de campo.

Los generadores de relé y ventilador se conservan como adaptadores de demostración.
No forman parte del núcleo gráfico y pueden ser sustituidos por cualquier IA que
entregue el contrato neutral `1.0`.

## Ejecutar como MCP

Requiere Node.js 20 o posterior.

```powershell
pnpm install
pnpm start
```

Configuración orientativa para un cliente MCP local:

```json
{
  "mcpServers": {
    "electroia": {
      "command": "node",
      "args": ["C:/ruta/super-tecnico/electroia-tool-server/src/index.mjs"]
    }
  }
}
```

## Ejecutar como herramienta JSON por línea de comandos

El adaptador CLI no necesita el SDK MCP. Recibe por `stdin`:

```json
{
  "tool": "electroia_generate_relay_driver",
  "arguments": {
    "relay_voltage": 12,
    "signal_voltage": 5,
    "controller": "arduino",
    "coil_type": "dc",
    "coil_current_ma": 80,
    "load_kind": "lámpara de 12 V",
    "load_current_a": 2,
    "isolation": false,
    "source": { "kind": "text" }
  }
}
```

La fotografía o el boceto pertenece a la capa de la IA que dispone de visión. Esa IA
extrae símbolos, terminales y redes; ElectroIA se ocupa de validarlos y dibujar el plano.

El Caso 002 admite ventiladores DC de dos cables entre 3 V y 30 V. La herramienta
recibe la temperatura de encendido y la histéresis deseada, y devuelve un circuito
con NTC, comparador, MOSFET y protección. El adaptador entrega ese circuito al nuevo
motor, que lo dibuja en un único lienzo normalizado.

## Validación de campo

El laboratorio privado permite guardar el SVG y el contrato JSON y registrar, desde móvil
u ordenador, si un plano es correcto o necesita cambios. Cada documento se identifica por
su huella SHA-256 y cuenta una sola vez. La apertura remota exige veinte planos distintos:
cinco de cuadros, cinco de automatización, cinco de electrónica HVAC y cinco de sistemas
embebidos.
