import { McpServer } from "@modelcontextprotocol/server";
import { serveStdio } from "@modelcontextprotocol/server/stdio";
import * as z from "zod/v4";
import { callElectroIATool } from "./toolkit.mjs";

function toolResult(result) {
  return {
    content: [{ type: "text", text: JSON.stringify(result) }],
    structuredContent: result,
  };
}

function toolError(error) {
  return {
    content: [{ type: "text", text: `ElectroIA no pudo completar la operación: ${error.message}` }],
    isError: true,
  };
}

function createServer() {
  const server = new McpServer({ name: "electroia-tools", version: "0.6.0" });

  server.registerTool(
    "electroia_get_capabilities",
    {
      description: "Describe las topologías, entradas y límites de ElectroIA sin invocar ningún modelo de IA.",
      inputSchema: z.object({}),
    },
    async () => {
      try {
        return toolResult(await callElectroIATool("electroia_get_capabilities", {}));
      } catch (error) {
        return toolError(error);
      }
    }
  );

  server.registerTool(
    "electroia_get_diagram_contract",
    {
      description: "Devuelve el contrato neutral del motor gráfico, la rejilla y los símbolos que ya tienen terminales normalizados.",
      inputSchema: z.object({}),
    },
    async () => {
      try {
        return toolResult(await callElectroIATool("electroia_get_diagram_contract", {}));
      } catch (error) {
        return toolError(error);
      }
    }
  );

  server.registerTool(
    "electroia_search_symbols",
    {
      description: "Busca símbolos normalizados por nombre, tipo o categoría y devuelve sus terminales y estado de revisión.",
      inputSchema: z.object({
        query: z.string().min(1).max(100),
        category: z.string().min(1).max(100).optional(),
        review_status: z.enum(["engine_reviewed", "auto_draft", "engine_internal"]).optional(),
        limit: z.number().int().min(1).max(50).optional(),
      }),
    },
    async (args) => {
      try {
        return toolResult(await callElectroIATool("electroia_search_symbols", args));
      } catch (error) {
        return toolError(error);
      }
    }
  );

  server.registerTool(
    "electroia_get_symbol",
    {
      description: "Devuelve la definición exacta, dimensiones y terminales de un símbolo normalizado.",
      inputSchema: z.object({ symbol_id: z.string().min(3).max(64) }),
    },
    async (args) => {
      try {
        return toolResult(await callElectroIATool("electroia_get_symbol", args));
      } catch (error) {
        return toolError(error);
      }
    }
  );

  const positionSchema = z.object({ x: z.number().int().min(0).max(500), y: z.number().int().min(0).max(500) });
  const diagramDocumentSchema = z.object({
    schema_version: z.literal("1.0"),
    document_kind: z.enum(["circuit_diagram", "single_line_diagram", "multi_line_diagram"]),
    standard_profile: z.literal("IEC_EXPERIMENTAL"),
    title: z.string().min(1).max(160),
    document_id: z.string().max(80).optional(),
    revision: z.string().max(20).optional(),
    notes: z.array(z.string().max(160)).max(6).optional(),
    grid: z.object({ pitch_mil: z.literal(50).optional(), show: z.boolean().optional() }).optional(),
    components: z.array(z.object({
      ref: z.string().min(1).max(32),
      display_ref: z.string().max(32).optional(),
      device_id: z.string().max(32).optional(),
      symbol_id: z.string().min(3).max(64),
      value: z.string().max(120).optional(),
      position: positionSchema.optional(),
      rotation: z.union([z.literal(0), z.literal(90), z.literal(180), z.literal(270)]).optional(),
      mirror: z.boolean().optional(),
      label_position: z.enum(["below", "above", "left", "right", "inside"]).optional(),
      role: z.string().max(60).optional(),
    })).min(1),
    nets: z.array(z.object({
      id: z.string().min(1).max(64),
      label: z.string().max(80).optional(),
      show_label: z.boolean().optional(),
      label_position: positionSchema.optional(),
      role: z.enum(["signal", "power", "ground", "protective_earth", "bus"]).optional(),
      conductors: z.number().int().min(1).max(99).optional(),
      connections: z.array(z.string().min(3).max(80)).min(1),
    })).min(1),
    relationships: z.array(z.object({
      from: z.string().min(1).max(32),
      to: z.string().min(1).max(32),
      kind: z.enum(["mechanical", "functional"]),
      via: z.array(positionSchema).optional(),
    })).optional(),
    layout: z.object({
      direction: z.enum(["left_to_right", "top_to_bottom"]).optional(),
      single_canvas: z.literal(true).optional(),
    }).optional(),
  });

  server.registerTool(
    "electroia_render_diagram",
    {
      description: "Valida símbolos, terminales y redes y genera un plano SVG sobre una rejilla común. No calcula ni selecciona componentes.",
      inputSchema: z.object({ document: diagramDocumentSchema }),
    },
    async (args) => {
      try {
        return toolResult(await callElectroIATool("electroia_render_diagram", args));
      } catch (error) {
        return toolError(error);
      }
    }
  );

  server.registerTool(
    "electroia_analyze_request",
    {
      description: "Distingue los Casos 001 y 002 y devuelve los datos detectados y las preguntas pendientes.",
      inputSchema: z.object({
        request: z.string().min(8).max(500),
      }),
    },
    async (args) => {
      try {
        return toolResult(await callElectroIATool("electroia_analyze_request", args));
      } catch (error) {
        return toolError(error);
      }
    }
  );

  server.registerTool(
    "electroia_generate_relay_driver",
    {
      description: "Genera un controlador de relé DC y devuelve circuito estructurado, BOM, conexiones y advertencias.",
      inputSchema: z.object({
        request: z.string().max(500).optional(),
        relay_voltage: z.number().positive().max(1000),
        signal_voltage: z.number().positive().max(100),
        controller: z.enum(["arduino", "micro_3v3", "sensor", "unknown"]),
        coil_type: z.enum(["dc", "ac", "unknown"]),
        coil_current_ma: z.number().positive().max(5000).nullable().optional(),
        load_kind: z.string().min(2).max(180),
        load_current_a: z.number().positive().max(1000).nullable().optional(),
        isolation: z.boolean(),
        source: z.object({
          kind: z.enum(["text", "image_analysis", "hand_drawn_sketch_analysis"]),
          note: z.string().max(500).optional(),
        }).optional(),
      }),
    },
    async (args) => {
      try {
        return toolResult(await callElectroIATool("electroia_generate_relay_driver", args));
      } catch (error) {
        return toolError(error);
      }
    }
  );

  server.registerTool(
    "electroia_generate_temperature_fan",
    {
      description: "Genera un controlador de ventilador DC por temperatura con histéresis y devuelve esquema, BOM y advertencias.",
      inputSchema: z.object({
        request: z.string().max(500).optional(),
        fan_voltage: z.number().min(3).max(30),
        fan_current_a: z.number().positive().max(20).nullable().optional(),
        turn_on_temperature_c: z.number().positive().max(120),
        hysteresis_c: z.number().min(1).max(20),
        fan_type: z.enum(["dc_2wire", "unknown"]),
        source: z.object({
          kind: z.enum(["text", "image_analysis", "hand_drawn_sketch_analysis"]),
          note: z.string().max(500).optional(),
        }).optional(),
      }),
    },
    async (args) => {
      try {
        return toolResult(await callElectroIATool("electroia_generate_temperature_fan", args));
      } catch (error) {
        return toolError(error);
      }
    }
  );

  return server;
}

void serveStdio(createServer);
console.error("ElectroIA MCP listo: motor gráfico electrotécnico neutral, sin IA integrada.");
