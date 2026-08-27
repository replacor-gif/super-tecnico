const OUTPUT_TYPES = new Set(["output", "power_out", "open_collector", "tri_state"]);
const INPUT_TYPES = new Set(["input", "power_in"]);
const IO_TYPES = new Set(["input", "output", "open_collector", "tri_state"]);

function text(value) {
  return String(value ?? "").trim();
}

function folded(value) {
  return text(value).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase();
}

function endpointParts(value) {
  const endpoint = text(value);
  const dot = endpoint.lastIndexOf(".");
  return dot > 0 ? { ref: endpoint.slice(0, dot), terminal: endpoint.slice(dot + 1) } : null;
}

function registryMap(registry) {
  return new Map((registry?.symbols || []).map((symbol) => [symbol.id, symbol]));
}

function finding(severity, code, message, subject = null) {
  return { severity, code, message, ...(subject ? { subject } : {}) };
}

function wirePrefix(role) {
  return {
    protective_earth: "PE",
    ground: "GND",
    power: "PWR",
    bus: "BUS",
    signal: "SIG",
  }[role] || "NET";
}

function componentDescription(component, symbol) {
  return text(component.value) || text(symbol?.name) || component.symbol_id;
}

function componentStatus(component) {
  if (text(component.part_number) || text(component.exact_model)) return "exact_reference";
  if (text(component.manufacturer) || text(component.model)) return "identified_model";
  if (text(component.value)) return "specified_value";
  return "generic_symbol";
}

function buildBom(components, symbols) {
  const groups = new Map();
  for (const component of components) {
    const symbol = symbols.get(component.symbol_id);
    const status = componentStatus(component);
    const key = [component.symbol_id, component.value, component.manufacturer, component.model, component.part_number, component.exact_model].map(text).join("|");
    if (!groups.has(key)) {
      groups.set(key, {
        item: groups.size + 1,
        quantity: 0,
        refs: [],
        symbol_id: component.symbol_id,
        description: componentDescription(component, symbol),
        manufacturer: text(component.manufacturer),
        model: text(component.model || component.exact_model),
        part_number: text(component.part_number),
        specification_status: status,
      });
    }
    const row = groups.get(key);
    row.quantity += 1;
    row.refs.push(component.display_ref || component.ref);
  }
  return [...groups.values()].map((row) => ({ ...row, refs: row.refs.sort((a, b) => a.localeCompare(b, "es", { numeric: true })) }));
}

function connectionRecord(endpoint, net, wireNumber, componentByRef, symbols) {
  const parts = endpointParts(endpoint);
  if (!parts) return null;
  const component = componentByRef.get(parts.ref);
  const symbol = component ? symbols.get(component.symbol_id) : null;
  const port = symbol?.ports?.[parts.terminal] || {};
  return {
    ref: parts.ref,
    terminal: parts.terminal,
    component: componentDescription(component || { symbol_id: "" }, symbol),
    symbol_id: component?.symbol_id || "",
    net_id: net.id,
    net_label: text(net.label) || net.id,
    wire_number: wireNumber,
    electrical_type: text(port.electrical_type) || "unknown",
    location: text(component?.location),
  };
}

function buildCrossReferences(components, terminalSchedule) {
  const byRef = new Map(components.map((component) => [component.ref, { ref: component.ref, nets: new Set(), connected_to: new Set() }]));
  const terminalsByNet = new Map();
  terminalSchedule.forEach((terminal) => {
    byRef.get(terminal.ref)?.nets.add(terminal.net_id);
    if (!terminalsByNet.has(terminal.net_id)) terminalsByNet.set(terminal.net_id, []);
    terminalsByNet.get(terminal.net_id).push(terminal.ref);
  });
  terminalsByNet.forEach((refs) => {
    const unique = [...new Set(refs)];
    unique.forEach((ref) => unique.filter((other) => other !== ref).forEach((other) => byRef.get(ref)?.connected_to.add(other)));
  });
  return [...byRef.values()].map((row) => ({
    ref: row.ref,
    nets: [...row.nets].sort(),
    connected_to: [...row.connected_to].sort((a, b) => a.localeCompare(b, "es", { numeric: true })),
  }));
}

export function buildTechnicalPackage(document, registry) {
  if (!document || typeof document !== "object" || !Array.isArray(document.components) || !Array.isArray(document.nets)) {
    throw new Error("Se necesita un documento ElectroIA con componentes y redes");
  }
  const symbols = registryMap(registry);
  const componentByRef = new Map(document.components.map((component) => [component.ref, component]));
  const findings = [];
  const usedEndpoints = new Map();
  const usedWireNumbers = new Map();
  const terminalSchedule = [];
  const counters = {};

  const wireSchedule = document.nets.map((net) => {
    const role = text(net.role) || "signal";
    counters[role] = (counters[role] || 0) + 1;
    const wireNumber = text(net.wire_number) || `${wirePrefix(role)}-${String(counters[role]).padStart(3, "0")}`;
    if (usedWireNumbers.has(wireNumber)) {
      findings.push(finding("error", "DUPLICATE_WIRE_NUMBER", `La numeración ${wireNumber} aparece en más de una red.`, net.id));
    }
    usedWireNumbers.set(wireNumber, net.id);
    const connections = net.connections.map((endpoint) => connectionRecord(endpoint, net, wireNumber, componentByRef, symbols)).filter(Boolean);
    connections.forEach((terminal) => {
      const endpoint = `${terminal.ref}.${terminal.terminal}`;
      if (usedEndpoints.has(endpoint)) {
        findings.push(finding("error", "TERMINAL_ON_MULTIPLE_NETS", `${endpoint} pertenece a ${usedEndpoints.get(endpoint)} y ${net.id}.`, endpoint));
      }
      usedEndpoints.set(endpoint, net.id);
      terminalSchedule.push(terminal);
    });
    if (connections.length < 2) findings.push(finding("warning", "OPEN_NET", `${net.id} solo tiene un punto conectado.`, net.id));

    const electricalTypes = connections.map((item) => item.electrical_type);
    const outputs = electricalTypes.filter((type) => OUTPUT_TYPES.has(type)).length;
    const inputs = electricalTypes.filter((type) => INPUT_TYPES.has(type)).length;
    if (outputs > 1 && role !== "bus") findings.push(finding("warning", "MULTIPLE_SOURCES", `${net.id} une varios terminales de salida; confirma que no exista contienda.`, net.id));
    if (inputs > 0 && outputs === 0 && role === "signal") findings.push(finding("warning", "SIGNAL_WITHOUT_SOURCE", `${net.id} no tiene una salida identificada en la biblioteca.`, net.id));
    if (role === "protective_earth" && connections.some((item) => !["protective_earth", "passive", "unknown"].includes(item.electrical_type))) {
      findings.push(finding("warning", "PE_TERMINAL_REVIEW", `${net.id} contiene un terminal que no está tipificado como PE; confirma la unión de protección.`, net.id));
    }

    return {
      wire_number: wireNumber,
      net_id: net.id,
      label: text(net.label) || net.id,
      role,
      conductors: Number.isInteger(net.conductors) ? net.conductors : 1,
      from: connections[0] ? `${connections[0].ref}.${connections[0].terminal}` : "",
      to: connections.slice(1).map((item) => `${item.ref}.${item.terminal}`),
      connections: connections.map((item) => `${item.ref}.${item.terminal}`),
      conductor_size_mm2: Number(net.conductor_size_mm2) || null,
      color: text(net.color),
      cable_id: text(net.cable_id),
      cable_type: text(net.cable_type),
      voltage: text(net.voltage),
      signal_type: text(net.signal_type),
      io_address: text(net.io_address),
    };
  });

  document.components.forEach((component) => {
    if (!terminalSchedule.some((terminal) => terminal.ref === component.ref)) {
      findings.push(finding("warning", "UNCONNECTED_COMPONENT", `${component.ref} no tiene ningún terminal conectado.`, component.ref));
    }
  });

  const ioSchedule = terminalSchedule
    .filter((terminal) => IO_TYPES.has(terminal.electrical_type))
    .map((terminal) => {
      const wire = wireSchedule.find((item) => item.net_id === terminal.net_id);
      return {
        ref: terminal.ref,
        channel: terminal.terminal,
        direction: terminal.electrical_type === "input" ? "input" : "output",
        signal: terminal.net_label,
        signal_type: wire?.signal_type || "",
        address: wire?.io_address || "",
        wire_number: terminal.wire_number,
        location: terminal.location,
      };
    });

  const cables = new Map();
  wireSchedule.filter((wire) => wire.cable_id).forEach((wire) => {
    if (!cables.has(wire.cable_id)) cables.set(wire.cable_id, { cable_id: wire.cable_id, cable_type: wire.cable_type, conductors: [] });
    cables.get(wire.cable_id).conductors.push({ wire_number: wire.wire_number, net_id: wire.net_id, section_mm2: wire.conductor_size_mm2, color: wire.color });
  });

  const bom = buildBom(document.components, symbols);
  const blocking = findings.filter((item) => item.severity === "error");
  const warnings = findings.filter((item) => item.severity === "warning");
  const specifiedWires = wireSchedule.filter((item) => item.conductor_size_mm2 || item.cable_type || item.voltage).length;
  return {
    schema_version: "1.0",
    package_kind: "electroia_technical_documentation",
    document: {
      document_id: text(document.document_id),
      title: text(document.title),
      revision: text(document.revision),
      document_kind: text(document.document_kind),
      standard_profile: text(document.standard_profile),
    },
    summary: {
      components: document.components.length,
      bom_items: bom.length,
      nets: document.nets.length,
      conductors: wireSchedule.reduce((total, item) => total + item.conductors, 0),
      connected_terminals: terminalSchedule.length,
      io_points: ioSchedule.length,
      explicit_cables: cables.size,
      specified_wires: specifiedWires,
      errors: blocking.length,
      warnings: warnings.length,
      status: blocking.length ? "blocked" : (warnings.length ? "review_required" : "ready"),
    },
    bom,
    wire_schedule: wireSchedule,
    terminal_schedule: terminalSchedule,
    cable_schedule: [...cables.values()],
    io_schedule: ioSchedule,
    cross_references: buildCrossReferences(document.components, terminalSchedule),
    quality: {
      status: blocking.length ? "blocked" : (warnings.length ? "review_required" : "ready"),
      findings,
      declarations: [
        "Las referencias y numeraciones automáticas son deterministas y deben revisarse antes de fabricar.",
        "ElectroIA no inventa secciones, colores, tipos de cable, direcciones de E/S ni protecciones: solo documenta los valores aportados por la IA o el proyectista.",
        "La documentación no sustituye la comprobación del modelo exacto, sus bornes, la normativa aplicable ni la validación profesional.",
      ],
    },
  };
}
