# ElectroIA Tool Server

ElectroIA es un motor gráfico electrotécnico neutral. No contiene un modelo de IA,
no necesita una clave de un proveedor y no genera cargos de inferencia por sí mismo.

La IA conectada interpreta la intención del usuario o una fotografía y llama a una
de estas herramientas:

- `electroia_get_capabilities`
- `electroia_get_diagram_contract`
- `electroia_search_symbols`
- `electroia_get_symbol`
- `electroia_render_diagram`
- `electroia_analyze_request`
- `electroia_generate_relay_driver`
- `electroia_generate_temperature_fan`

La IA llamante decide la topología, los valores y los componentes. La herramienta
`electroia_render_diagram` recibe símbolos, terminales y redes ya decididos, comprueba
su conectividad y devuelve un SVG sobre una rejilla común.

La biblioteca externa contiene las 460 fichas del catálogo y 3 elementos auxiliares
del motor. Cada definición indica su calidad: 127 símbolos del catálogo tienen geometría
revisada individualmente y 333 son borradores normalizados por familias. Las familias
de conexiones y referencias, protecciones eléctricas, relés, interruptores y actuadores,
y máquinas y actuadores ya están revisadas por completo. También hay 17 sensores HVAC
y de medida revisados individualmente. El motor
los distingue gráficamente y avisa cuando se utiliza uno pendiente de revisión.

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
