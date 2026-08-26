const DOCUMENT_KINDS = new Set(["circuit_diagram", "single_line_diagram", "multi_line_diagram"]);
const NET_ROLES = new Set(["signal", "power", "ground", "protective_earth", "bus"]);
const REF_PATTERN = /^[A-Za-z][A-Za-z0-9_.-]{0,31}$/;
const ID_PATTERN = /^[A-Za-z][A-Za-z0-9_-]{0,31}$/;

function text(value) {
  return String(value ?? "").trim();
}

function folded(value) {
  return text(value).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase();
}

function portToken(value) {
  return folded(value).replace(/\s+/g, "");
}

function diagnostic(code, message, subject = null) {
  return { code, message, subject };
}

function requireArray(value, name, minimum = 0, maximum = Infinity) {
  if (!Array.isArray(value) || value.length < minimum || value.length > maximum) {
    throw new Error(`${name} debe contener entre ${minimum} y ${maximum} elementos`);
  }
  return value;
}

function resolveSymbol(component, registry, rankSymbol, strictResolution, warnings) {
  const requestedId = text(component.symbol_id).toUpperCase();
  if (requestedId) {
    const exact = registry.symbols.find((symbol) => symbol.id === requestedId);
    if (!exact) throw new Error(`${component.id}: símbolo no encontrado: ${requestedId}`);
    return { symbol: exact, mode: "symbol_id", query: requestedId, alternatives: [] };
  }

  const query = text(component.symbol_query);
  if (!query) throw new Error(`${component.id}: indica symbol_id o symbol_query`);
  const candidates = registry.symbols.flatMap((symbol) => {
    if (symbol.review_status !== "engine_reviewed") return [];
    const match = rankSymbol(symbol, query);
    return match ? [{ symbol, match }] : [];
  }).sort((left, right) => right.match.score - left.match.score || left.symbol.id.localeCompare(right.symbol.id));
  if (!candidates.length) throw new Error(`${component.id}: ningún símbolo revisado coincide con «${query}»`);

  const best = candidates[0];
  const alternatives = candidates.slice(1, 4).map((item) => ({
    symbol_id: item.symbol.id,
    name: item.symbol.name,
    score: Math.round(item.match.score),
  }));
  const closeAlternatives = candidates.slice(1).filter((item) => item.match.score >= best.match.score * 0.95);
  if (closeAlternatives.length) {
    const choices = [best, ...closeAlternatives.slice(0, 3)].map((item) => `${item.symbol.id} ${item.symbol.name}`).join(", ");
    if (strictResolution) throw new Error(`${component.id}: «${query}» es ambiguo (${choices}); usa symbol_id`);
    warnings.push(diagnostic("AMBIGUOUS_SYMBOL_RESOLUTION", `${component.id}: se eligió ${best.symbol.id} entre coincidencias próximas; confirma el símbolo.`, component.id));
  }
  return { symbol: best.symbol, mode: "ranked_query", query, score: Math.round(best.match.score), alternatives };
}

const CONCEPTUAL_PORTS = Object.freeze({
  positive: ["+", "POS", "POSITIVE", "POSITIVO", "V+", "VCC", "VDD", "L+"],
  negative: ["-", "NEG", "NEGATIVE", "NEGATIVO", "V-", "VSS", "L-", "0V"],
  ground: ["GND", "GROUND", "MASA", "COM0V", "0V"],
  earth: ["PE", "EARTH", "TIERRA", "PROTECTIVEEARTH"],
  neutral: ["N", "NEUTRAL", "NEUTRO"],
  line: ["L", "LINE", "LINEA", "FASE"],
  input: ["IN", "INPUT", "ENTRADA"],
  output: ["OUT", "OUTPUT", "SALIDA"],
  common: ["COM", "COMMON", "COMUN", "C"],
  normally_open: ["NO", "NA", "NORMALLYOPEN", "NORMALMENTEABIERTO"],
  normally_closed: ["NC", "NORMALLYCLOSED", "NORMALMENTECERRADO"],
});

function conceptualPort(value) {
  const token = portToken(value);
  return Object.entries(CONCEPTUAL_PORTS).find(([, aliases]) => aliases.includes(token))?.[0] || null;
}

function resolvePort(symbol, requested) {
  const raw = text(requested);
  const names = Object.keys(symbol.ports || {});
  const exact = names.find((name) => portToken(name) === portToken(raw));
  if (exact) return { name: exact, mode: "exact" };

  const concept = conceptualPort(raw);
  if (concept) {
    const matches = names.filter((name) => conceptualPort(name) === concept);
    if (matches.length === 1) return { name: matches[0], mode: `alias:${concept}` };
    if (matches.length > 1) throw new Error(`${symbol.id}: el terminal «${raw}» puede ser ${matches.join(", ")}`);
  }

  const contains = names.filter((name) => portToken(name).includes(portToken(raw)) || portToken(raw).includes(portToken(name)));
  if (contains.length === 1) return { name: contains[0], mode: "partial" };
  throw new Error(`${symbol.id}: terminal «${raw}» no resuelto. Disponibles: ${names.join(", ")}`);
}

function referenceFor(component, symbol, counters, used) {
  const explicit = text(component.ref);
  if (explicit) {
    if (!REF_PATTERN.test(explicit)) throw new Error(`${component.id}: referencia no válida: ${explicit}`);
    if (used.has(explicit)) throw new Error(`Referencia repetida: ${explicit}`);
    used.add(explicit);
    return explicit;
  }
  let base = folded(symbol.designator || "X").replace(/[^A-Z0-9]/g, "") || "X";
  if (!/^[A-Z]/.test(base)) base = `X${base}`;
  counters[base] = (counters[base] || 0) + 1;
  let candidate = `${base}${counters[base]}`.slice(0, 32);
  while (used.has(candidate)) {
    counters[base] += 1;
    candidate = `${base}${counters[base]}`.slice(0, 32);
  }
  used.add(candidate);
  return candidate;
}

function endpointParts(endpoint) {
  if (endpoint && typeof endpoint === "object" && !Array.isArray(endpoint)) {
    return { component: text(endpoint.component), port: text(endpoint.port) };
  }
  const value = text(endpoint);
  const dot = value.lastIndexOf(".");
  return dot > 0 ? { component: value.slice(0, dot), port: value.slice(dot + 1) } : null;
}

function inferNetRole(net) {
  if (NET_ROLES.has(net.role)) return net.role;
  const value = folded(`${net.id} ${net.label || ""}`);
  if (/\b(PE|PROTECTIVE EARTH|TIERRA DE PROTECCION)\b/.test(value)) return "protective_earth";
  if (/\b(GND|GROUND|MASA|0V)\b/.test(value)) return "ground";
  if (/\b(BUS|MODBUS|CAN|RS485|ETHERNET|M BUS|KNX)\b/.test(value)) return "bus";
  if (/\b(POWER|POTENCIA|ALIMENTACION|VCC|VDD|L1|L2|L3|24V|230V|400V)\b/.test(value)) return "power";
  return "signal";
}

export function compileDiagramSpec(rawSpec, services) {
  if (!rawSpec || typeof rawSpec !== "object" || Array.isArray(rawSpec)) throw new Error("spec debe ser un objeto JSON");
  const registry = services.registry;
  const componentsInput = requireArray(rawSpec.components, "components", 1, 200);
  const netsInput = requireArray(rawSpec.nets, "nets", 1, 400);
  const title = text(rawSpec.title);
  if (!title || title.length > 160) throw new Error("title debe tener entre 1 y 160 caracteres");
  const documentKind = text(rawSpec.document_kind || "circuit_diagram");
  if (!DOCUMENT_KINDS.has(documentKind)) throw new Error(`document_kind no soportado: ${documentKind}`);
  const strictResolution = rawSpec.strict_resolution === true;
  const warnings = [];
  const counters = {};
  const usedRefs = new Set();
  const byId = new Map();
  const resolutions = [];

  const components = componentsInput.map((component) => {
    if (!component || typeof component !== "object" || Array.isArray(component)) throw new Error("Cada componente debe ser un objeto");
    const id = text(component.id);
    if (!ID_PATTERN.test(id)) throw new Error(`Identificador de componente no válido: ${id || "vacío"}`);
    if (byId.has(id)) throw new Error(`Identificador de componente repetido: ${id}`);
    const resolution = resolveSymbol(component, registry, services.rankSymbol, strictResolution, warnings);
    const ref = referenceFor(component, resolution.symbol, counters, usedRefs);
    const output = {
      ref,
      symbol_id: resolution.symbol.id,
      ...(component.value ? { value: text(component.value).slice(0, 120) } : {}),
      ...(component.position ? { position: component.position } : {}),
      ...(component.rotation !== undefined ? { rotation: component.rotation } : {}),
      ...(component.mirror === true ? { mirror: true } : {}),
      ...(component.role ? { role: text(component.role).slice(0, 60) } : {}),
      ...(component.manufacturer ? { manufacturer: text(component.manufacturer).slice(0, 80) } : {}),
      ...(component.model ? { model: text(component.model).slice(0, 120) } : {}),
      ...(component.part_number ? { part_number: text(component.part_number).slice(0, 120) } : {}),
      ...(component.exact_model ? { exact_model: text(component.exact_model).slice(0, 120) } : {}),
    };
    byId.set(id, { id, ref, symbol: resolution.symbol, output });
    resolutions.push({
      component_id: id,
      ref,
      requested: resolution.query,
      mode: resolution.mode,
      symbol_id: resolution.symbol.id,
      symbol_name: resolution.symbol.name,
      ...(resolution.score ? { score: resolution.score } : {}),
      alternatives: resolution.alternatives,
    });
    return output;
  });

  let totalConnections = 0;
  const portResolutions = [];
  const nets = netsInput.map((net, netIndex) => {
    if (!net || typeof net !== "object" || Array.isArray(net)) throw new Error("Cada red debe ser un objeto");
    const id = text(net.id || `N${netIndex + 1}`);
    if (!/^[A-Za-z0-9_+.-]{1,64}$/.test(id)) throw new Error(`Identificador de red no válido: ${id}`);
    const endpoints = requireArray(net.connections, `${id}.connections`, 1, 100);
    totalConnections += endpoints.length;
    if (totalConnections > 2000) throw new Error("Las conexiones totales superan el límite de 2.000");
    const connections = endpoints.map((endpoint) => {
      const parts = endpointParts(endpoint);
      if (!parts?.component || !parts.port) throw new Error(`${id}: conexión no válida; usa {component, port} o COMPONENTE.PUERTO`);
      const component = byId.get(parts.component);
      if (!component) throw new Error(`${id}: componente inexistente: ${parts.component}`);
      const port = resolvePort(component.symbol, parts.port);
      portResolutions.push({ net_id: id, component_id: component.id, requested: parts.port, resolved: `${component.ref}.${port.name}`, mode: port.mode });
      return `${component.ref}.${port.name}`;
    });
    return {
      id,
      ...(net.label ? { label: text(net.label).slice(0, 80) } : {}),
      show_label: net.show_label !== false,
      role: inferNetRole(net),
      ...(Number.isInteger(net.conductors) ? { conductors: net.conductors } : {}),
      connections,
    };
  });

  const relationships = requireArray(rawSpec.relationships || [], "relationships", 0, 400).map((relationship) => {
    const from = byId.get(text(relationship.from));
    const to = byId.get(text(relationship.to));
    if (!from || !to) throw new Error(`Relación con componente inexistente: ${relationship.from} → ${relationship.to}`);
    if (!["mechanical", "functional"].includes(relationship.kind)) throw new Error(`Relación no soportada: ${relationship.kind}`);
    return { from: from.ref, to: to.ref, kind: relationship.kind, ...(relationship.via ? { via: relationship.via } : {}) };
  });

  const document = {
    schema_version: "1.0",
    document_kind: documentKind,
    standard_profile: "IEC_EXPERIMENTAL",
    title,
    ...(rawSpec.document_id ? { document_id: text(rawSpec.document_id).slice(0, 80) } : {}),
    ...(rawSpec.revision ? { revision: text(rawSpec.revision).slice(0, 20) } : {}),
    ...(Array.isArray(rawSpec.notes) ? { notes: rawSpec.notes.slice(0, 6).map((item) => text(item).slice(0, 160)) } : {}),
    components,
    nets,
    ...(relationships.length ? { relationships } : {}),
    layout: {
      direction: rawSpec.layout?.direction === "top_to_bottom" ? "top_to_bottom" : "left_to_right",
      single_canvas: true,
    },
  };
  const diagram = services.render(document);
  return {
    document,
    diagram,
    resolution: {
      strict: strictResolution,
      components: resolutions,
      ports: portResolutions,
      warnings,
      summary: {
        requested_components: componentsInput.length,
        resolved_symbols: resolutions.length,
        resolved_ports: portResolutions.length,
        automatic_symbol_matches: resolutions.filter((item) => item.mode === "ranked_query").length,
        ambiguity_warnings: warnings.filter((item) => item.code === "AMBIGUOUS_SYMBOL_RESOLUTION").length,
      },
    },
  };
}
