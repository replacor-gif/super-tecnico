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
  const server = new McpServer({ name: "electroia-tools", version: "0.1.0" });

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
console.error("ElectroIA MCP listo: motor electrónico neutral, sin IA integrada.");
