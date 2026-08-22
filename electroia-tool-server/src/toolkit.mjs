import { createRequire } from "node:module";
import { readFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const SERVER_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const PROJECT_ROOT = resolve(SERVER_ROOT, "..");
const ROUTE = "archivo-tecnico-47097e44267b9cb111636b84823f1d47";
const engine = require(join(PROJECT_ROOT, ROUTE, "engine.js"));
const diagramCore = require(join(PROJECT_ROOT, ROUTE, "diagram-core.js"));

const manifestPath = join(PROJECT_ROOT, "data", "electroia", "tool-manifest.json");
const componentPath = join(PROJECT_ROOT, "data", "components", "catalog.json");
const symbolPath = join(PROJECT_ROOT, "data", "symbols", "catalog.json");
const connectorPath = join(PROJECT_ROOT, "data", "connectors", "catalog.json");

export const manifest = JSON.parse(await readFile(manifestPath, "utf8"));

let resourcesPromise;
let connectorsPromise;

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

async function loadConnectors() {
  if (!connectorsPromise) {
    connectorsPromise = readFile(connectorPath, "utf8").then(JSON.parse);
  }
  return connectorsPromise;
}

function ensureObject(value, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${label} debe ser un objeto JSON`);
  }
  return value;
}

function folded(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function symbolSummary(symbol) {
  return {
    id: symbol.id,
    name: symbol.name,
    kind: symbol.kind,
    designator: symbol.designator,
    category: symbol.category || "",
    subcategory: symbol.subcategory || "",
    aliases: symbol.aliases || "",
    review_status: symbol.review_status,
    terminals: Object.entries(symbol.ports || {}).map(([name, definition]) => ({
      name,
      side: definition.side,
      electrical_type: definition.electrical_type,
    })),
  };
}

function connectorSummary(record) {
  return {
    id: record.id,
    canonical_name: record.canonical_name,
    aliases: record.aliases,
    category: record.category,
    interface: record.interface,
    form_factor: record.form_factor,
    gender: record.gender,
    contact_count: record.contacts.length,
    view: record.view,
    review: record.review,
    source_ids: record.source_ids,
  };
}

export async function callElectroIATool(tool, rawArguments = {}) {
  const name = String(tool || "");
  const args = ensureObject(rawArguments, "arguments");

  if (name === "electroia_get_capabilities") {
    return { ok: true, tool: name, manifest };
  }

  if (name === "electroia_get_diagram_contract") {
    return {
      ok: true,
      tool: name,
      contract: diagramCore.getContract(),
      symbol_registry: diagramCore.getRegistry(),
    };
  }

  if (name === "electroia_search_symbols") {
    const query = folded(args.query).trim();
    if (!query) throw new Error("query debe contener al menos un término de búsqueda");
    const category = folded(args.category).trim();
    const status = String(args.review_status || "").trim();
    const limit = Math.max(1, Math.min(50, Number.isInteger(args.limit) ? args.limit : 12));
    const matches = diagramCore.getRegistry().symbols.filter((symbol) => {
      const haystack = folded([
        symbol.id, symbol.name, symbol.kind, symbol.designator,
        symbol.category, symbol.subcategory, symbol.catalog_drawing_type,
        symbol.aliases, symbol.keywords, symbol.description, symbol.interpretation,
      ].join(" "));
      if (!haystack.includes(query)) return false;
      if (category && !folded(`${symbol.category} ${symbol.subcategory}`).includes(category)) return false;
      if (status && symbol.review_status !== status) return false;
      return true;
    });
    return {
      ok: true,
      tool: name,
      query: args.query,
      total: matches.length,
      symbols: matches.slice(0, limit).map(symbolSummary),
    };
  }

  if (name === "electroia_get_symbol") {
    const symbolId = String(args.symbol_id || "").trim().toUpperCase();
    const symbol = diagramCore.getRegistry().symbols.find((item) => item.id === symbolId);
    if (!symbol) throw new Error(`Símbolo no encontrado: ${symbolId || "vacío"}`);
    return { ok: true, tool: name, symbol };
  }

  if (name === "supertecnico_search_connectors") {
    const query = folded(args.query).trim();
    if (!query) throw new Error("query debe contener al menos un término de búsqueda");
    const category = folded(args.category).trim();
    const status = String(args.review_status || "").trim();
    const limit = Math.max(1, Math.min(20, Number.isInteger(args.limit) ? args.limit : 8));
    const catalog = await loadConnectors();
    const matches = catalog.records.filter((record) => {
      const haystack = folded([record.id, record.canonical_name, record.category, record.interface, record.form_factor, ...(record.aliases || []), ...(record.search_terms || []), ...record.contacts.flatMap((contact) => [contact.id, contact.signal])].join(" "));
      if (!haystack.includes(query)) return false;
      if (category && !folded(record.category).includes(category)) return false;
      if (status && record.review.status !== status) return false;
      return true;
    });
    return {ok: true, tool: name, query: args.query, total: matches.length, items: matches.slice(0, limit).map(connectorSummary)};
  }

  if (name === "supertecnico_get_connector") {
    const connectorId = String(args.connector_id || "").trim();
    const catalog = await loadConnectors();
    const record = catalog.records.find((item) => item.id === connectorId);
    if (!record) throw new Error(`Conector no encontrado: ${connectorId || "vacío"}`);
    return {ok: true, tool: name, record};
  }

  if (name === "supertecnico_resolve_connector_contact") {
    const connectorId = String(args.connector_id || "").trim();
    const query = folded(args.contact_or_signal).trim();
    const catalog = await loadConnectors();
    const record = catalog.records.find((item) => item.id === connectorId);
    if (!record) throw new Error(`Conector no encontrado: ${connectorId || "vacío"}`);
    const contacts = record.contacts.filter((contact) => folded(`${contact.id} ${contact.signal} ${contact.description}`).includes(query));
    return {ok: true, tool: name, connector_id: connectorId, view: record.view, review: record.review, contacts};
  }

  if (name === "electroia_render_diagram") {
    return { ok: true, tool: name, diagram: diagramCore.render(args.document) };
  }

  if (name === "electroia_analyze_request") {
    return engine.callTool(name, args);
  }

  if (["electroia_generate_relay_driver", "electroia_generate_temperature_fan"].includes(name)) {
    const resources = await loadResources();
    return engine.callTool(name, args, resources);
  }

  throw new Error(`Herramienta desconocida: ${name}`);
}
