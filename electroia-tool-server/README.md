# ElectroIA Tool Server

ElectroIA es un motor electrónico neutral. No contiene un modelo de IA, no necesita
una clave de un proveedor y no genera cargos de inferencia por sí mismo.

La IA conectada interpreta la intención del usuario o una fotografía y llama a una
de estas herramientas:

- `electroia_get_capabilities`
- `electroia_analyze_request`
- `electroia_generate_relay_driver`
- `electroia_generate_temperature_fan`

El resultado incluye el modelo eléctrico estructurado, la lista de componentes,
las conexiones, las advertencias y el manifiesto de símbolos necesario para dibujar.

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
extrae los campos anteriores y ElectroIA se ocupa de validarlos y generar el circuito.

El Caso 002 admite ventiladores DC de dos cables entre 3 V y 30 V. La herramienta
recibe la temperatura de encendido y la histéresis deseada, y devuelve un circuito
con NTC, comparador, MOSFET, protección y esquema dividido en bloques legibles.
