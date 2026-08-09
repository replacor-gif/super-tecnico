import { createRequire } from "node:module";
import { readFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const SERVER_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const PROJECT_ROOT = resolve(SERVER_ROOT, "..");
const ROUTE = "archivo-tecnico-47097e44267b9cb111636b84823f1d47";
const engine = require(join(PROJECT_ROOT, ROUTE, "engine.js"));

const manifestPath = join(PROJECT_ROOT, "data", "electroia", "tool-manifest.json");
const componentPath = join(PROJECT_ROOT, "data", "components", "catalog.json");
const symbolPath = join(PROJECT_ROOT, "data", "symbols", "catalog.json");

export const manifest = JSON.parse(await readFile(manifestPath, "utf8"));

let resourcesPromise;

async function loadResources() {
  if (!resourcesPromise) {
    resourcesPromise = Promise.all([
      readFile(componentPath, "utf8").then(JSON.parse),
      readFile(symbolPath, "utf8").then(JSON.parse),
    ]).then(([componentCatalog, symbolCatalog]) => ({
      components: componentCatalog.components,
      component_meta: componentCatalog.meta || {},
      symbols: symbolCatalog.symbols,
      symbol_meta: {
        version: symbolCatalog.version,
        count: symbolCatalog.count,
        generated_from: symbolCatalog.generated_from,
      },
    }));
  }
  return resourcesPromise;
}

function ensureObject(value, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${label} debe ser un objeto JSON`);
  }
  return value;
}

export async function callElectroIATool(tool, rawArguments = {}) {
  const name = String(tool || "");
  const args = ensureObject(rawArguments, "arguments");

  if (name === "electroia_get_capabilities") {
    return { ok: true, tool: name, manifest };
  }

  if (name === "electroia_analyze_request") {
    return engine.callTool(name, args);
  }

  if (name === "electroia_generate_relay_driver") {
    const resources = await loadResources();
    return engine.callTool(name, args, resources);
  }

  throw new Error(`Herramienta desconocida: ${name}`);
}
