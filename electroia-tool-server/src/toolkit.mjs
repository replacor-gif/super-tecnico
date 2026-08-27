import { createRequire } from "node:module";
import { readFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { compileDiagramSpec } from "./compiler.mjs";
import { symbolSearchRank } from "./symbol-ranking.mjs";

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
const embeddedPlatformPath = join(PROJECT_ROOT, "data", "embedded-platforms", "catalog.json");
const aiBridgePath = join(PROJECT_ROOT, "data", "electroia", "ai-bridge.json");

export const manifest = JSON.parse(await readFile(manifestPath, "utf8"));

let resourcesPromise;
let connectorsPromise;
let embeddedPlatformsPromise;
let aiBridgePromise;

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

async function loadEmbeddedPlatforms() {
  if (!embeddedPlatformsPromise) {
    embeddedPlatformsPromise = readFile(embeddedPlatformPath, "utf8").then(JSON.parse);
  }
  return embeddedPlatformsPromise;
}

async function loadAiBridge() {
  if (!aiBridgePromise) aiBridgePromise = readFile(aiBridgePath, "utf8").then(JSON.parse);
  return aiBridgePromise;
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

function searchFolded(value) {
  return folded(value).replace(/[^a-z0-9]+/g, " ").trim();
}

const EMBEDDED_IGNORED_TERMS = new Set(["a", "al", "de", "del", "la", "las", "el", "los", "y", "o", "u", "con", "para", "por", "en", "un", "una", "unos", "unas", "que", "como", "quiero", "necesito", "the", "and", "with", "for", "from", "to", "an", "of", "on", "in"]);

function embeddedTerms(value) {
  return [...new Set(folded(value).split(/\s+/).filter((term) => term.length >= 2 && !EMBEDDED_IGNORED_TERMS.has(term)))];
}

function symbolSummary(symbol, match = null) {
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
    ...(match ? {matched_terms: match.matchedTerms, term_coverage: Number(match.coverage.toFixed(3)), relevance_score: Number(Math.min(1, match.score / 700).toFixed(3))} : {}),
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

function embeddedPlatformSummary(record) {
  return {
    id: record.id,
    name: record.name,
    manufacturer: record.manufacturer,
    platform_class: record.platform_class,
    architecture: record.architecture,
    logic_and_power: record.logic_and_power,
    interfaces: record.interfaces,
    recommended_use: record.recommended_use,
    primary_risk: record.primary_risk,
    tags: record.tags,
    review: record.review,
    source_refs: record.source_refs,
    source_locator: record.source_locator,
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

  if (name === "electroia_prepare_design_brief") {
    const request = String(args.request || "").trim();
    if (request.length < 8 || request.length > 2000) throw new Error("request debe tener entre 8 y 2000 caracteres");
    const bridge = await loadAiBridge();
    return {
      ok: true,
      tool: name,
      bridge: {
        provider_neutral: bridge.provider_neutral === true,
        status: bridge.status,
        contract: bridge.architecture.single_contract,
      },
      brief: {
        schema_version: "1.0",
        kind: "electroia_design_brief",
        request,
        language: String(args.language || "es").slice(0, 5),
        document_kind: args.document_kind || null,
        responsibility_boundary: bridge.architecture,
        resources: bridge.public_resources,
        mandatory_process: [
          "Pregunta solo los requisitos técnicos imprescindibles que falten.",
          "Calcula y selecciona los componentes antes de dibujar.",
          "Entrega una especificación de alto nivel a electroia_compile_diagram; usa la búsqueda exacta solo si la resolución necesita confirmación.",
          "Revisa la resolución de símbolos, terminales y los diagnósticos antes de aceptar el SVG.",
          "Mantén los bloques de modelo exacto como no ejecutables hasta disponer de documentación del fabricante.",
        ],
        expected_output: bridge.response_contract,
      },
    };
  }

  if (name === "electroia_search_symbols") {
    const query = searchFolded(args.query);
    if (!query) throw new Error("query debe contener al menos un término de búsqueda");
    const category = searchFolded(args.category);
    const status = String(args.review_status || "").trim();
    const limit = Math.max(1, Math.min(50, Number.isInteger(args.limit) ? args.limit : 12));
    const matches = diagramCore.getRegistry().symbols.flatMap((symbol) => {
      if (category && !searchFolded(`${symbol.category} ${symbol.subcategory}`).includes(category)) return [];
      if (status && symbol.review_status !== status) return [];
      const match = symbolSearchRank(symbol, query);
      return match ? [{symbol, match}] : [];
    }).sort((left, right) => right.match.score - left.match.score || left.symbol.id.localeCompare(right.symbol.id));
    return {
      ok: true,
      tool: name,
      query: args.query,
      total: matches.length,
      search_mode: "ranked_terms",
      symbols: matches.slice(0, limit).map(({symbol, match}) => symbolSummary(symbol, match)),
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

  if (name === "supertecnico_search_embedded_platforms") {
    const query = folded(args.query).trim();
    if (!query) throw new Error("query debe contener al menos un término de búsqueda");
    const manufacturer = folded(args.manufacturer).trim();
    const platformClass = folded(args.platform_class).trim();
    const limit = Math.max(1, Math.min(20, Number.isInteger(args.limit) ? args.limit : 8));
    const catalog = await loadEmbeddedPlatforms();
    const queryTerms = embeddedTerms(query);
    const matches = catalog.records.filter((record) => {
      const haystack = folded([record.id, record.name, record.manufacturer, record.platform_class, record.architecture, record.logic_and_power, record.recommended_use, record.primary_risk, ...(record.interfaces || []), ...(record.tags || [])].join(" "));
      if (!queryTerms.every((term) => haystack.includes(term))) return false;
      if (manufacturer && !folded(record.manufacturer).includes(manufacturer)) return false;
      if (platformClass && folded(record.platform_class) !== platformClass) return false;
      return true;
    });
    return {ok: true, tool: name, catalog_version: catalog.catalog_version, query: args.query, total: matches.length, items: matches.slice(0, limit).map(embeddedPlatformSummary)};
  }

  if (name === "supertecnico_get_embedded_platform") {
    const platformId = String(args.platform_id || "").trim();
    const catalog = await loadEmbeddedPlatforms();
    const record = catalog.records.find((item) => item.id === platformId);
    if (!record) throw new Error(`Plataforma no encontrada: ${platformId || "vacía"}`);
    return {ok: true, tool: name, catalog_version: catalog.catalog_version, record, reception_checks: catalog.shared_reception_checks, integration_requirements: catalog.shared_integration_requirements};
  }

  if (name === "supertecnico_recommend_embedded_platforms") {
    const useCase = folded(args.use_case).trim();
    if (useCase.length < 3) throw new Error("use_case debe describir el objetivo del proyecto");
    const requiredInterfaces = folded((args.required_interfaces || []).join(" "));
    const terms = embeddedTerms(`${useCase} ${requiredInterfaces}`);
    const catalog = await loadEmbeddedPlatforms();
    const linuxClasses = new Set(["single_board_computer", "system_on_module", "edge_ai_computer", "soc_fpga_board"]);
    const needsLinux = args.needs_linux === true || terms.includes("linux");
    const ranked = catalog.records.flatMap((record) => {
      if (needsLinux && !linuxClasses.has(record.platform_class)) return [];
      const haystack = folded([record.id, record.name, record.manufacturer, record.platform_class, record.architecture, record.recommended_use, ...(record.interfaces || []), ...(record.tags || [])].join(" "));
      const matchedTerms = terms.filter((term) => haystack.includes(term));
      const score = matchedTerms.length * 10 + (needsLinux && linuxClasses.has(record.platform_class) ? 8 : 0);
      return score ? [{score, matched_terms: matchedTerms, platform: embeddedPlatformSummary(record)}] : [];
    }).sort((a, b) => b.score - a.score || a.platform.name.localeCompare(b.platform.name));
    const limit = Math.max(1, Math.min(10, Number.isInteger(args.limit) ? args.limit : 5));
    const items = ranked.slice(0, limit);
    return {
      ok: true,
      tool: name,
      catalog_version: catalog.catalog_version,
      decision_status: items.length ? "preselection_only" : "insufficient_context",
      total: items.length,
      items,
      warnings: [
        "La puntuación solo ordena coincidencias documentales; no demuestra que una placa sea adecuada.",
        "Confirma revisión exacta, pinout, niveles, memoria, radio, carrier, software, ciclo de vida y condiciones ambientales.",
      ],
    };
  }

  if (name === "electroia_render_diagram") {
    return { ok: true, tool: name, diagram: diagramCore.render(args.document) };
  }

  if (name === "electroia_compile_diagram") {
    const compiled = compileDiagramSpec(args.spec, {
      registry: diagramCore.getRegistry(),
      rankSymbol: symbolSearchRank,
      render: diagramCore.render,
    });
    return { ok: true, tool: name, ...compiled };
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
