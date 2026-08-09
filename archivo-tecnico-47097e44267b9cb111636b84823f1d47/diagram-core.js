"use strict";

const ElectroDiagramCore = (() => {
  const ENGINE_VERSION = "1.0.0-alpha.1";
  const CONTRACT_VERSION = "1.0";
  const GRID_PITCH_MIL = 50;
  const UNIT = 24;

  const SYMBOLS = Object.freeze({
    "SYM-0010": symbol("SYM-0010", "Masa de señal", "ground", "GND", 4, 4, {
      "1": port(0, -2, "north", "passive"),
    }),
    "SYM-0014": symbol("SYM-0014", "Alimentación positiva", "power_port", "V", 4, 4, {
      "1": port(0, 2, "south", "power_out"),
    }),
    "SYM-0018": symbol("SYM-0018", "Fuente de tensión continua", "source_dc", "PS", 5, 6, {
      "+": port(0, -3, "north", "power_out"),
      "-": port(0, 3, "south", "power_out"),
    }),
    "SYM-0023": symbol("SYM-0023", "Resistencia IEC", "resistor_iec", "R", 6, 2, {
      "1": port(-3, 0, "west", "passive"),
      "2": port(3, 0, "east", "passive"),
    }),
    "SYM-0026": symbol("SYM-0026", "Potenciómetro", "potentiometer", "RV", 6, 6, {
      "1": port(0, -3, "north", "passive"),
      "2": port(-3, 0, "west", "passive"),
      "3": port(0, 3, "south", "passive"),
    }),
    "SYM-0031": symbol("SYM-0031", "Termistor NTC", "thermistor_ntc", "TH", 6, 3, {
      "1": port(-3, 0, "west", "passive"),
      "2": port(3, 0, "east", "passive"),
    }),
    "SYM-0035": symbol("SYM-0035", "Condensador no polarizado", "capacitor", "C", 6, 3, {
      "1": port(-3, 0, "west", "passive"),
      "2": port(3, 0, "east", "passive"),
    }),
    "SYM-0057": symbol("SYM-0057", "Diodo rectificador", "diode", "D", 6, 3, {
      A: port(-3, 0, "west", "passive"),
      K: port(3, 0, "east", "passive"),
    }),
    "SYM-0080": symbol("SYM-0080", "MOSFET N", "mosfet_n", "Q", 6, 7, {
      G: port(-3, 0, "west", "input"),
      D: port(0, -3, "north", "passive"),
      S: port(0, 3, "south", "passive"),
    }),
    "SYM-0097": symbol("SYM-0097", "Optoacoplador de fototransistor", "optocoupler", "U", 8, 8, {
      A: port(-4, -2, "west", "input"),
      K: port(-4, 2, "west", "input"),
      C: port(4, -2, "east", "output"),
      E: port(4, 2, "east", "output"),
    }),
    "SYM-0119": symbol("SYM-0119", "Relé — bobina", "relay_coil", "K", 6, 3, {
      A1: port(-3, 0, "west", "passive"),
      A2: port(3, 0, "east", "passive"),
    }),
    "SYM-0120": symbol("SYM-0120", "Relé — contacto normalmente abierto", "contact_no", "K", 7, 3, {
      COM: port(-3, 0, "west", "passive"),
      NO: port(3, 0, "east", "passive"),
    }),
    "SYM-0156": symbol("SYM-0156", "Ventilador", "fan", "FAN", 7, 7, {
      "+": port(0, -3, "north", "power_in"),
      "-": port(0, 3, "south", "power_in"),
    }),
    "SYM-0184": symbol("SYM-0184", "Comparador", "comparator", "U", 7, 7, {
      "-": port(-3, -1, "west", "input"),
      "+": port(-3, 1, "west", "input"),
      OUT: port(3, 0, "east", "open_collector"),
      VCC: port(0, -3, "north", "power_in"),
      GND: port(0, 3, "south", "power_in"),
    }),
    "ST-GENERIC-2P": symbol("ST-GENERIC-2P", "Carga genérica", "generic_2p", "X", 7, 5, {
      "1": port(-3, 0, "west", "passive"),
      "2": port(3, 0, "east", "passive"),
    }),
    "ST-CONTROL-PORT": symbol("ST-CONTROL-PORT", "Puerto de control", "connector_2p", "PORT", 7, 5, {
      OUT: port(3, -1, "east", "output"),
      GND: port(3, 1, "east", "power_in"),
    }),
    "ST-LOAD-PORT": symbol("ST-LOAD-PORT", "Puerto del circuito de carga", "connector_2p", "PORT", 7, 5, {
      IN: port(3, -1, "east", "passive"),
      RETURN: port(3, 1, "east", "passive"),
    }),
  });

  function port(x, y, side, electricalType) {
    return { x, y, side, electrical_type: electricalType };
  }

  function symbol(id, name, kind, designator, width, height, ports) {
    return {
      id,
      catalog_id: id.startsWith("SYM-") ? id : null,
      name,
      kind,
      designator,
      standard_profile: "IEC_EXPERIMENTAL",
      grid_pitch_mil: GRID_PITCH_MIL,
      width,
      height,
      ports,
      review_status: id.startsWith("SYM-") ? "draft" : "internal",
    };
  }

  function escapeXml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&apos;");
  }

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function getRegistry() {
    return {
      version: "0.1",
      engine_version: ENGINE_VERSION,
      standard_profile: "IEC_EXPERIMENTAL",
      grid_pitch_mil: GRID_PITCH_MIL,
      symbols: Object.values(SYMBOLS).map(clone),
    };
  }

  function splitConnection(value) {
    const text = String(value || "");
    const dot = text.lastIndexOf(".");
    if (dot < 1 || dot === text.length - 1) return null;
    return { ref: text.slice(0, dot), port: text.slice(dot + 1) };
  }

  function validate(document) {
    const errors = [];
    const warnings = [];
    if (!document || typeof document !== "object" || Array.isArray(document)) {
      return { valid: false, errors: [diagnostic("DOCUMENT_REQUIRED", "Se necesita un documento JSON.")], warnings };
    }
    if (document.schema_version !== CONTRACT_VERSION) {
      errors.push(diagnostic("SCHEMA_VERSION", `schema_version debe ser ${CONTRACT_VERSION}.`));
    }
    if (!["circuit_diagram", "single_line_diagram", "multi_line_diagram"].includes(document.document_kind)) {
      errors.push(diagnostic("DOCUMENT_KIND", "El tipo de documento no está soportado."));
    }
    if (document.standard_profile !== "IEC_EXPERIMENTAL") {
      errors.push(diagnostic("STANDARD_PROFILE", "El primer núcleo solo admite IEC_EXPERIMENTAL."));
    }
    const components = Array.isArray(document.components) ? document.components : [];
    const nets = Array.isArray(document.nets) ? document.nets : [];
    if (!components.length) errors.push(diagnostic("COMPONENTS_REQUIRED", "El documento no contiene símbolos."));
    if (!nets.length) errors.push(diagnostic("NETS_REQUIRED", "El documento no contiene redes."));

    const byRef = new Map();
    for (const component of components) {
      const ref = String(component?.ref || "").trim();
      if (!ref) {
        errors.push(diagnostic("REFERENCE_REQUIRED", "Todos los símbolos necesitan una referencia."));
        continue;
      }
      if (byRef.has(ref)) errors.push(diagnostic("DUPLICATE_REFERENCE", `La referencia ${ref} está repetida.`, ref));
      byRef.set(ref, component);
      const definition = SYMBOLS[component.symbol_id];
      if (!definition) errors.push(diagnostic("UNKNOWN_SYMBOL", `El símbolo ${component.symbol_id || "vacío"} no está normalizado.`, ref));
      if (component.position) {
        if (!Number.isInteger(component.position.x) || !Number.isInteger(component.position.y)) {
          errors.push(diagnostic("OFF_GRID", `${ref} no está colocado en coordenadas enteras de rejilla.`, ref));
        }
      }
      if (component.rotation !== undefined && ![0, 90, 180, 270].includes(component.rotation)) {
        errors.push(diagnostic("ROTATION", `${ref} tiene una rotación no válida.`, ref));
      }
    }

    const terminalUse = new Map();
    const netIds = new Set();
    for (const net of nets) {
      const netId = String(net?.id || "").trim();
      if (!netId) errors.push(diagnostic("NET_ID_REQUIRED", "Todas las redes necesitan un identificador."));
      if (netIds.has(netId)) errors.push(diagnostic("DUPLICATE_NET", `La red ${netId} está repetida.`, netId));
      netIds.add(netId);
      const connections = Array.isArray(net?.connections) ? net.connections : [];
      if (connections.length < 2) warnings.push(diagnostic("OPEN_NET", `La red ${netId || "sin nombre"} solo tiene un terminal.`, netId));
      if (document.document_kind === "single_line_diagram" && !Number.isInteger(net.conductors)) {
        warnings.push(diagnostic("CONDUCTOR_COUNT", `La red ${netId} no declara cuántos conductores resume.`, netId));
      }
      for (const rawConnection of connections) {
        const connection = splitConnection(rawConnection);
        if (!connection) {
          errors.push(diagnostic("CONNECTION_FORMAT", `Conexión no válida: ${rawConnection}.`, netId));
          continue;
        }
        const component = byRef.get(connection.ref);
        if (!component) {
          errors.push(diagnostic("MISSING_COMPONENT", `${rawConnection} menciona un símbolo inexistente.`, netId));
          continue;
        }
        const definition = SYMBOLS[component.symbol_id];
        if (definition && !definition.ports[connection.port]) {
          errors.push(diagnostic("MISSING_PORT", `${rawConnection} menciona un terminal inexistente.`, connection.ref));
        }
        if (terminalUse.has(rawConnection) && terminalUse.get(rawConnection) !== netId) {
          errors.push(diagnostic("PORT_ON_MULTIPLE_NETS", `${rawConnection} pertenece a más de una red.`, rawConnection));
        }
        terminalUse.set(rawConnection, netId);
      }
    }

    for (const component of components) {
      const definition = SYMBOLS[component.symbol_id];
      if (!definition) continue;
      for (const portName of Object.keys(definition.ports)) {
        const key = `${component.ref}.${portName}`;
        if (!terminalUse.has(key)) warnings.push(diagnostic("UNCONNECTED_PORT", `${key} está sin conectar.`, key));
      }
    }
    for (const relationship of Array.isArray(document.relationships) ? document.relationships : []) {
      if (!byRef.has(relationship.from) || !byRef.has(relationship.to)) {
        errors.push(diagnostic("RELATIONSHIP_REFERENCE", `La relación ${relationship.from} → ${relationship.to} menciona una referencia inexistente.`));
      }
    }
    return { valid: errors.length === 0, errors, warnings };
  }

  function diagnostic(code, message, subject = null) {
    return { code, message, subject };
  }

  function normalizeDocument(rawDocument) {
    const document = clone(rawDocument);
    document.title = String(document.title || "Diagrama sin título");
    document.document_id = String(document.document_id || "ELECTROIA-DIAGRAM");
    document.revision = String(document.revision || "A");
    document.notes = Array.isArray(document.notes) ? document.notes.map(String) : [];
    document.relationships = Array.isArray(document.relationships) ? document.relationships : [];
    document.grid = { pitch_mil: GRID_PITCH_MIL, show: false, ...(document.grid || {}) };
    document.layout = { direction: "left_to_right", single_canvas: true, ...(document.layout || {}) };
    autoPlace(document);
    for (const component of document.components) {
      component.rotation = component.rotation ?? 0;
      component.mirror = component.mirror === true;
      component.value = String(component.value || "");
    }
    for (const net of document.nets) {
      net.role = net.role || "signal";
      net.label = String(net.label || net.id);
      net.show_label = net.show_label !== false;
    }
    return document;
  }

  function autoPlace(document) {
    const unplaced = document.components.filter((item) => !item.position);
    if (!unplaced.length) return;
    const byRef = new Map(document.components.map((item) => [item.ref, item]));
    const adjacency = new Map(document.components.map((item) => [item.ref, new Set()]));
    for (const net of document.nets || []) {
      if (["power", "ground", "protective_earth"].includes(net.role)) continue;
      const refs = [...new Set((net.connections || []).map(splitConnection).filter(Boolean).map((item) => item.ref))];
      for (let index = 0; index < refs.length; index += 1) {
        for (let other = index + 1; other < refs.length; other += 1) {
          if (byRef.has(refs[index]) && byRef.has(refs[other])) {
            adjacency.get(refs[index]).add(refs[other]);
            adjacency.get(refs[other]).add(refs[index]);
          }
        }
      }
    }
    const ordered = [...document.components].sort((a, b) => naturalCompare(a.ref, b.ref));
    const anchor = ordered.find((item) => /^(PS|V|IN|J)/i.test(item.ref)) || ordered[0];
    const rank = new Map([[anchor.ref, 0]]);
    const queue = [anchor.ref];
    while (queue.length) {
      const current = queue.shift();
      for (const next of adjacency.get(current) || []) {
        if (!rank.has(next)) {
          rank.set(next, rank.get(current) + 1);
          queue.push(next);
        }
      }
    }
    let disconnectedRank = Math.max(0, ...rank.values()) + 1;
    for (const component of ordered) {
      if (!rank.has(component.ref)) rank.set(component.ref, disconnectedRank++);
    }
    const rowsByRank = new Map();
    for (const component of ordered) {
      const column = rank.get(component.ref);
      const row = rowsByRank.get(column) || 0;
      rowsByRank.set(column, row + 1);
      if (!component.position) {
        component.position = document.layout?.direction === "top_to_bottom"
          ? { x: 5 + row * 9, y: 5 + column * 8 }
          : { x: 5 + column * 9, y: 5 + row * 8 };
      }
    }
  }

  function naturalCompare(left, right) {
    return String(left).localeCompare(String(right), undefined, { numeric: true, sensitivity: "base" });
  }

  function transformPoint(pointValue, component) {
    let x = component.mirror ? -pointValue.x : pointValue.x;
    let y = pointValue.y;
    const rotation = component.rotation || 0;
    if (rotation === 90) [x, y] = [-y, x];
    if (rotation === 180) [x, y] = [-x, -y];
    if (rotation === 270) [x, y] = [y, -x];
    return { x: component.position.x + x, y: component.position.y + y };
  }

  function terminalMap(document) {
    const map = new Map();
    for (const component of document.components) {
      const definition = SYMBOLS[component.symbol_id];
      for (const [name, terminal] of Object.entries(definition.ports)) {
        map.set(`${component.ref}.${name}`, transformPoint(terminal, component));
      }
    }
    return map;
  }

  function routeDocument(document) {
    const terminals = terminalMap(document);
    const allTerminalPoints = [...terminals.values()];
    const minTerminalY = Math.min(...allTerminalPoints.map((item) => item.y));
    const maxTerminalY = Math.max(...allTerminalPoints.map((item) => item.y));
    const segments = [];
    const junctions = [];
    const labels = [];

    for (let netIndex = 0; netIndex < document.nets.length; netIndex += 1) {
      const net = document.nets[netIndex];
      const points = net.connections.map((item) => terminals.get(item)).filter(Boolean);
      if (!points.length) continue;
      if (["power", "ground", "protective_earth"].includes(net.role)) {
        const railY = net.role === "power" ? minTerminalY - 4 - netIndex % 2 : maxTerminalY + 4 + netIndex % 2;
        const minX = Math.min(...points.map((item) => item.x));
        const maxX = Math.max(...points.map((item) => item.x));
        addSegment(segments, net, { x: minX, y: railY }, { x: maxX, y: railY });
        for (const pointValue of points) addSegment(segments, net, pointValue, { x: pointValue.x, y: railY });
        if (net.show_label) labels.push({ net, point: net.label_position || { x: minX, y: railY }, position: "rail" });
        continue;
      }
      if (points.length === 1) {
        if (net.show_label) labels.push({ net, point: net.label_position || points[0], position: "terminal" });
        continue;
      }
      if (points.length === 2) {
        routePair(segments, net, points[0], points[1], netIndex);
        if (net.show_label) labels.push({ net, point: net.label_position || midpoint(points[0], points[1]), position: "signal" });
        continue;
      }
      const sortedX = points.map((item) => item.x).sort((a, b) => a - b);
      const trunkX = sortedX[Math.floor(sortedX.length / 2)];
      const minY = Math.min(...points.map((item) => item.y));
      const maxY = Math.max(...points.map((item) => item.y));
      addSegment(segments, net, { x: trunkX, y: minY }, { x: trunkX, y: maxY });
      for (const pointValue of points) {
        addSegment(segments, net, pointValue, { x: trunkX, y: pointValue.y });
        junctions.push({ net, x: trunkX, y: pointValue.y });
      }
      if (net.show_label) labels.push({ net, point: net.label_position || { x: trunkX, y: minY }, position: "signal" });
    }
    const crossings = findCrossings(segments);
    return { segments, junctions: uniquePoints(junctions), labels, crossings };
  }

  function routePair(segments, net, first, second, netIndex) {
    if (first.x === second.x || first.y === second.y) {
      addSegment(segments, net, first, second);
      return;
    }
    const preferVerticalChannel = Math.abs(first.x - second.x) >= Math.abs(first.y - second.y);
    if (preferVerticalChannel) {
      let channelX = Math.round((first.x + second.x) / 2);
      if (channelX === first.x || channelX === second.x) channelX += netIndex % 2 ? 1 : -1;
      addSegment(segments, net, first, { x: channelX, y: first.y });
      addSegment(segments, net, { x: channelX, y: first.y }, { x: channelX, y: second.y });
      addSegment(segments, net, { x: channelX, y: second.y }, second);
    } else {
      let channelY = Math.round((first.y + second.y) / 2);
      if (channelY === first.y || channelY === second.y) channelY += netIndex % 2 ? 1 : -1;
      addSegment(segments, net, first, { x: first.x, y: channelY });
      addSegment(segments, net, { x: first.x, y: channelY }, { x: second.x, y: channelY });
      addSegment(segments, net, { x: second.x, y: channelY }, second);
    }
  }

  function addSegment(collection, net, start, end) {
    if (start.x === end.x && start.y === end.y) return;
    collection.push({ net, start: { ...start }, end: { ...end } });
  }

  function midpoint(first, second) {
    return { x: Math.round((first.x + second.x) / 2), y: Math.round((first.y + second.y) / 2) };
  }

  function uniquePoints(points) {
    const seen = new Set();
    return points.filter((pointValue) => {
      const key = `${pointValue.net.id}:${pointValue.x}:${pointValue.y}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  function findCrossings(segments) {
    const crossings = [];
    for (let index = 0; index < segments.length; index += 1) {
      for (let other = index + 1; other < segments.length; other += 1) {
        const a = segments[index];
        const b = segments[other];
        if (a.net.id === b.net.id) continue;
        const aHorizontal = a.start.y === a.end.y;
        const bHorizontal = b.start.y === b.end.y;
        if (aHorizontal === bHorizontal) continue;
        const horizontal = aHorizontal ? a : b;
        const vertical = aHorizontal ? b : a;
        const x = vertical.start.x;
        const y = horizontal.start.y;
        const insideHorizontal = betweenStrict(x, horizontal.start.x, horizontal.end.x);
        const insideVertical = betweenStrict(y, vertical.start.y, vertical.end.y);
        if (insideHorizontal && insideVertical) crossings.push({ x, y, horizontal });
      }
    }
    return uniqueCrossings(crossings);
  }

  function betweenStrict(value, first, second) {
    const min = Math.min(first, second);
    const max = Math.max(first, second);
    return value > min && value < max;
  }

  function uniqueCrossings(items) {
    const seen = new Set();
    return items.filter((item) => {
      const key = `${item.x}:${item.y}:${item.horizontal.net.id}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  function render(rawDocument) {
    const validation = validate(rawDocument);
    if (!validation.valid) {
      const error = new Error(`Documento de diagrama no válido: ${validation.errors.map((item) => item.message).join(" ")}`);
      error.diagnostics = validation;
      throw error;
    }
    const document = normalizeDocument(rawDocument);
    const routing = routeDocument(document);
    const extents = documentExtents(document, routing);
    const svg = renderSvg(document, routing, extents);
    return {
      engine_version: ENGINE_VERSION,
      contract_version: CONTRACT_VERSION,
      document,
      svg,
      diagnostics: {
        valid: true,
        errors: [],
        warnings: validation.warnings,
        metrics: {
          symbols: document.components.length,
          nets: document.nets.length,
          terminals: [...terminalMap(document).keys()].length,
          bridged_crossings: routing.crossings.length,
          off_grid_terminals: 0,
          pages: 1,
          single_canvas: true,
        },
      },
    };
  }

  function documentExtents(document, routing) {
    const points = [];
    for (const component of document.components) {
      const definition = SYMBOLS[component.symbol_id];
      const rotated = [90, 270].includes(component.rotation || 0);
      const halfWidth = (rotated ? definition.height : definition.width) / 2 + 2;
      const halfHeight = (rotated ? definition.width : definition.height) / 2 + 3;
      points.push({ x: component.position.x - halfWidth, y: component.position.y - halfHeight });
      points.push({ x: component.position.x + halfWidth, y: component.position.y + halfHeight });
    }
    for (const segment of routing.segments) points.push(segment.start, segment.end);
    return {
      minX: Math.floor(Math.min(...points.map((item) => item.x))) - 2,
      minY: Math.floor(Math.min(...points.map((item) => item.y))) - 2,
      maxX: Math.ceil(Math.max(...points.map((item) => item.x))) + 2,
      maxY: Math.ceil(Math.max(...points.map((item) => item.y))) + 2,
    };
  }

  function renderSvg(document, routing, extents) {
    const titleHeight = 84;
    const width = Math.max(760, (extents.maxX - extents.minX) * UNIT);
    const drawingHeight = Math.max(430, (extents.maxY - extents.minY) * UNIT);
    const height = drawingHeight + titleHeight;
    const mapX = (x) => (x - extents.minX) * UNIT;
    const mapY = (y) => (y - extents.minY) * UNIT;
    const gridPattern = document.grid.show
      ? `<defs><pattern id="electro-grid" width="${UNIT}" height="${UNIT}" patternUnits="userSpaceOnUse"><circle cx="1.2" cy="1.2" r="1.2" fill="#d7dcd8"/></pattern></defs><rect x="12" y="12" width="${width - 24}" height="${drawingHeight - 12}" fill="url(#electro-grid)"/>`
      : "";
    const wires = routing.segments.map((segment) => {
      const className = `wire net-${escapeXml(segment.net.role || "signal")}`;
      return `<path class="${className}" data-net="${escapeXml(segment.net.id)}" d="M${mapX(segment.start.x)} ${mapY(segment.start.y)}L${mapX(segment.end.x)} ${mapY(segment.end.y)}"/>`;
    }).join("");
    const junctions = routing.junctions.map((item) =>
      `<circle class="junction" data-net="${escapeXml(item.net.id)}" cx="${mapX(item.x)}" cy="${mapY(item.y)}" r="4"/>`
    ).join("");
    const crossings = routing.crossings.map((item) => {
      const x = mapX(item.x);
      const y = mapY(item.y);
      return `<path class="bridge-gap" d="M${x - 9} ${y}q9 -13 18 0"/><path class="wire bridge" data-net="${escapeXml(item.horizontal.net.id)}" d="M${x - 9} ${y}q9 -13 18 0"/>`;
    }).join("");
    const labels = routing.labels.map((item) => renderNetLabel(item, mapX, mapY, document.document_kind)).join("");
    const relationships = renderRelationships(document, mapX, mapY);
    const symbols = document.components.map((component) => renderComponent(component, mapX, mapY)).join("");
    const titleBlockWidth = Math.min(470, width * 0.48);
    const titleBlockX = width - titleBlockWidth - 12;
    const titleBlockY = drawingHeight + 8;
    return `<svg class="electrical-diagram electroia-core-diagram" viewBox="0 0 ${width} ${height}" role="img"
      data-engine-version="${ENGINE_VERSION}" data-contract-version="${CONTRACT_VERSION}"
      data-document-kind="${escapeXml(document.document_kind)}" data-standard-profile="${escapeXml(document.standard_profile)}"
      data-grid-pitch-mil="${GRID_PITCH_MIL}" data-pages="1" aria-label="${escapeXml(document.title)}">
      <style>
        .sheet{fill:#fff;stroke:#222a27;stroke-width:2}.wire{fill:none;stroke:#26302c;stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round}.net-protective_earth{stroke-width:3}.junction{fill:#26302c}.bridge-gap{fill:none;stroke:#fff;stroke-width:8}.relationship{fill:none;stroke:#7d8782;stroke-width:2;stroke-dasharray:8 6}.symbol-line{fill:none;stroke:#202824;stroke-width:2.6;stroke-linecap:round;stroke-linejoin:round}.symbol-fill{fill:#fff;stroke:#202824;stroke-width:2.6}.symbol-accent{fill:none;stroke:#202824;stroke-width:2}.component-ref{font:700 15px Inter,Arial,sans-serif;fill:#202824;text-anchor:middle}.component-value{font:500 12px Inter,Arial,sans-serif;fill:#58625d;text-anchor:middle}.net-label{font:700 11px ui-monospace,SFMono-Regular,Consolas,monospace;fill:#47504c;paint-order:stroke;stroke:#fff;stroke-width:5;stroke-linejoin:round}.polarity{font:800 14px Inter,Arial,sans-serif;fill:#202824;text-anchor:middle}.title-main{font:800 13px Inter,Arial,sans-serif;fill:#202824}.title-small{font:600 10px Inter,Arial,sans-serif;fill:#59635e}.title-rule{stroke:#202824;stroke-width:1.4}.standard-note{font:700 10px Inter,Arial,sans-serif;fill:#606a65;letter-spacing:.8px}.document-note{font:800 10px Inter,Arial,sans-serif;fill:#8a3d25}
      </style>
      <rect class="sheet" x="8" y="8" width="${width - 16}" height="${height - 16}"/>
      ${gridPattern}
      <text class="standard-note" x="24" y="30">IEC EXPERIMENTAL · REJILLA ${GRID_PITCH_MIL} mil · LIENZO ÚNICO</text>
      <g class="relationships">${relationships}</g>
      <g class="wires">${wires}${junctions}${crossings}${labels}</g>
      <g class="symbols">${symbols}</g>
      <line class="title-rule" x1="8" y1="${drawingHeight}" x2="${width - 8}" y2="${drawingHeight}"/>
      <g class="title-block">
        <rect class="symbol-line" x="${titleBlockX}" y="${titleBlockY}" width="${titleBlockWidth}" height="64"/>
        <line class="title-rule" x1="${titleBlockX + titleBlockWidth * 0.7}" y1="${titleBlockY}" x2="${titleBlockX + titleBlockWidth * 0.7}" y2="${titleBlockY + 64}"/>
        <line class="title-rule" x1="${titleBlockX + titleBlockWidth * 0.7}" y1="${titleBlockY + 32}" x2="${titleBlockX + titleBlockWidth}" y2="${titleBlockY + 32}"/>
        <text class="title-main" x="${titleBlockX + 12}" y="${titleBlockY + 26}">${escapeXml(document.title)}</text>
        <text class="title-small" x="${titleBlockX + 12}" y="${titleBlockY + 48}">${escapeXml(document.document_id)}</text>
        <text class="title-small" x="${titleBlockX + titleBlockWidth * 0.7 + 10}" y="${titleBlockY + 20}">REV. ${escapeXml(document.revision)}</text>
        <text class="title-small" x="${titleBlockX + titleBlockWidth * 0.7 + 10}" y="${titleBlockY + 52}">HOJA 1 / 1</text>
      </g>
      <text class="title-small" x="24" y="${drawingHeight + 34}">ElectroIA Diagram Engine ${ENGINE_VERSION}</text>
      <text class="title-small" x="24" y="${drawingHeight + 52}">${escapeXml(document.document_kind)} · ${escapeXml(document.standard_profile)}</text>
      ${document.notes.slice(0, 1).map((note) => `<text class="document-note" x="24" y="${drawingHeight + 70}">${escapeXml(note)}</text>`).join("")}
    </svg>`;
  }

  function renderRelationships(document, mapX, mapY) {
    const byRef = new Map(document.components.map((item) => [item.ref, item]));
    return document.relationships.map((relationship) => {
      const from = byRef.get(relationship.from)?.position;
      const to = byRef.get(relationship.to)?.position;
      if (!from || !to) return "";
      const points = [from, ...(relationship.via || []), to];
      const path = points.map((pointValue, index) => `${index ? "L" : "M"}${mapX(pointValue.x)} ${mapY(pointValue.y)}`).join("");
      return `<path class="relationship" data-relationship="${escapeXml(relationship.kind)}" d="${path}"/>`;
    }).join("");
  }

  function renderNetLabel(item, mapX, mapY, documentKind) {
    const conductorText = documentKind === "single_line_diagram" && item.net.conductors
      ? ` · ${item.net.conductors} conductores`
      : "";
    const x = mapX(item.point.x) + 7;
    const y = mapY(item.point.y) - 7;
    return `<text class="net-label" data-net-label="${escapeXml(item.net.id)}" x="${x}" y="${y}">${escapeXml(item.net.label)}${escapeXml(conductorText)}</text>`;
  }

  function renderComponent(component, mapX, mapY) {
    const definition = SYMBOLS[component.symbol_id];
    const x = mapX(component.position.x);
    const y = mapY(component.position.y);
    const scaleX = component.mirror ? -1 : 1;
    const body = drawSymbolBody(definition.kind);
    const rotated = [90, 270].includes(component.rotation || 0);
    const halfWidth = (rotated ? definition.height : definition.width) / 2;
    const halfHeight = (rotated ? definition.width : definition.height) / 2;
    const labelPosition = component.label_position || "below";
    const label = componentLabel(component, x, y, halfWidth, halfHeight, labelPosition);
    return `<g class="component" data-ref="${escapeXml(component.ref)}" data-symbol-id="${escapeXml(component.symbol_id)}">
      <g transform="translate(${x} ${y}) rotate(${component.rotation || 0}) scale(${scaleX} 1)">${body}</g>
      ${label}
    </g>`;
  }

  function componentLabel(component, x, y, halfWidth, halfHeight, position) {
    const value = shortText(component.value, 28);
    if (position === "inside") {
      return `<text class="component-ref" x="${x}" y="${y - 4}">${escapeXml(component.ref)}</text>${value ? `<text class="component-value" x="${x}" y="${y + 14}">${escapeXml(value)}</text>` : ""}`;
    }
    if (position === "left" || position === "right") {
      const right = position === "right";
      const labelX = x + (right ? 1 : -1) * (halfWidth + 0.8) * UNIT;
      const anchor = right ? "start" : "end";
      return `<text class="component-ref" style="text-anchor:${anchor}" x="${labelX}" y="${y - 3}">${escapeXml(component.ref)}</text>${value ? `<text class="component-value" style="text-anchor:${anchor}" x="${labelX}" y="${y + 15}">${escapeXml(value)}</text>` : ""}`;
    }
    const above = position === "above";
    const firstY = y + (above ? -1 : 1) * (halfHeight + 0.8) * UNIT;
    const valueY = above ? firstY - 17 : firstY + 17;
    return `${value ? `<text class="component-value" x="${x}" y="${valueY}">${escapeXml(value)}</text>` : ""}<text class="component-ref" x="${x}" y="${firstY}">${escapeXml(component.ref)}</text>`;
  }

  function shortText(value, limit) {
    const text = String(value || "");
    return text.length > limit ? `${text.slice(0, limit - 1)}…` : text;
  }

  function drawSymbolBody(kind) {
    const u = UNIT;
    const line = (x1, y1, x2, y2, className = "symbol-line") => `<path class="${className}" d="M${x1 * u} ${y1 * u}L${x2 * u} ${y2 * u}"/>`;
    if (kind === "resistor_iec") {
      return `${line(-3, 0, -1.35, 0)}<rect class="symbol-fill" x="${-1.35 * u}" y="${-0.62 * u}" width="${2.7 * u}" height="${1.24 * u}"/>${line(1.35, 0, 3, 0)}`;
    }
    if (kind === "thermistor_ntc") {
      return `${line(-3, 0, -1.35, 0)}<rect class="symbol-fill" x="${-1.35 * u}" y="${-0.62 * u}" width="${2.7 * u}" height="${1.24 * u}"/>${line(1.35, 0, 3, 0)}${line(-1.55, 1.05, 1.55, -1.05, "symbol-accent")}`;
    }
    if (kind === "capacitor") {
      return `${line(-3, 0, -0.28, 0)}${line(-0.28, -1.05, -0.28, 1.05)}${line(0.28, -1.05, 0.28, 1.05)}${line(0.28, 0, 3, 0)}`;
    }
    if (kind === "diode") {
      return `${line(-3, 0, -1.25, 0)}<path class="symbol-line" d="M${-1.25 * u} ${-1.1 * u}L${1.05 * u} 0L${-1.25 * u} ${1.1 * u}Z"/>${line(1.25, -1.1, 1.25, 1.1)}${line(1.25, 0, 3, 0)}`;
    }
    if (kind === "source_dc") {
      return `${line(0, -3, 0, -1.55)}<circle class="symbol-fill" cx="0" cy="0" r="${1.55 * u}"/>${line(0, 1.55, 0, 3)}<text class="polarity" x="0" y="${-0.55 * u}">+</text><text class="polarity" x="0" y="${0.85 * u}">−</text>`;
    }
    if (kind === "ground") {
      return `${line(0, -2, 0, -0.55)}${line(-1.2, -0.55, 1.2, -0.55)}${line(-0.78, 0, 0.78, 0)}${line(-0.35, 0.55, 0.35, 0.55)}`;
    }
    if (kind === "power_port") {
      return `${line(0, 2, 0, 0)}<path class="symbol-line" d="M${-0.7 * u} 0L0 ${-0.85 * u}L${0.7 * u} 0"/>`;
    }
    if (kind === "potentiometer") {
      return `${line(0, -3, 0, -1.35)}<rect class="symbol-fill" x="${-0.62 * u}" y="${-1.35 * u}" width="${1.24 * u}" height="${2.7 * u}"/>${line(0, 1.35, 0, 3)}${line(-3, 0, -0.7, 0)}<path class="symbol-line" d="M${-0.95 * u} ${-0.36 * u}L${-0.62 * u} 0L${-0.95 * u} ${0.36 * u}"/>`;
    }
    if (kind === "comparator") {
      return `<path class="symbol-fill" d="M${-2.15 * u} ${-2 * u}V${2 * u}L${2.15 * u} 0Z"/>${line(-3, -1, -2.15, -1)}${line(-3, 1, -2.15, 1)}${line(2.15, 0, 3, 0)}${line(0, -3, 0, -1)}${line(0, 1, 0, 3)}<text class="polarity" x="${-1.7 * u}" y="${-0.72 * u}">−</text><text class="polarity" x="${-1.7 * u}" y="${1.28 * u}">+</text>`;
    }
    if (kind === "mosfet_n") {
      return `${line(-3, 0, -1.25, 0)}${line(-1.15, -1.55, -1.15, 1.55)}${line(-0.35, -1.25, -0.35, 1.25)}${line(-0.35, -1.05, 0, -1.05)}${line(0, -3, 0, -1.05)}${line(-0.35, 1.05, 0, 1.05)}${line(0, 1.05, 0, 3)}<path class="symbol-line" d="M${0.25 * u} ${0.7 * u}L${1.05 * u} ${1.25 * u}L${0.25 * u} ${1.8 * u}Z"/><path class="symbol-line" d="M${1.25 * u} ${0.65 * u}V${1.85 * u}"/>`;
    }
    if (kind === "fan") {
      return `${line(0, -3, 0, -1.55)}<circle class="symbol-fill" cx="0" cy="0" r="${1.55 * u}"/>${line(0, 1.55, 0, 3)}<circle cx="0" cy="0" r="4" fill="#202824"/><path class="symbol-accent" d="M0 -4c6 -31 38 -24 32 -2c-4 14 -19 16 -32 8zM4 0c31 6 24 38 2 32c-14 -4 -16 -19 -8 -32zM0 4c-6 31 -38 24 -32 2c4 -14 19 -16 32 -8z"/>`;
    }
    if (kind === "relay_coil") {
      return `${line(-3, 0, -1.35, 0)}<rect class="symbol-fill" x="${-1.35 * u}" y="${-0.8 * u}" width="${2.7 * u}" height="${1.6 * u}" rx="4"/>${line(1.35, 0, 3, 0)}`;
    }
    if (kind === "contact_no") {
      return `${line(-3, 0, -1.15, 0)}${line(1.15, 0, 3, 0)}<circle cx="${-1.15 * u}" cy="0" r="4" fill="#202824"/><circle cx="${1.15 * u}" cy="0" r="4" fill="#202824"/>${line(-1.05, -0.08, 0.85, -1.25)}`;
    }
    if (kind === "optocoupler") {
      return `<rect class="symbol-fill" x="${-2.7 * u}" y="${-2.65 * u}" width="${5.4 * u}" height="${5.3 * u}" rx="5"/>${line(0, -2.35, 0, 2.35, "symbol-accent")}${line(-4, -2, -2.25, -2)}${line(-4, 2, -2.25, 2)}<path class="symbol-line" d="M${-2.25 * u} ${-2.65 * u}V${-1.35 * u}L${-1.2 * u} ${-2 * u}Z"/>${line(-1.1, -2.65, -1.1, -1.35)}${line(-1.7, -1.15, -0.45, -0.35, "symbol-accent")}${line(-1.7, 0, -0.45, 0.8, "symbol-accent")}${line(2.25, -2, 4, -2)}${line(2.25, 2, 4, 2)}${line(1.15, -1.1, 2.25, -2)}${line(1.15, 1.1, 2.25, 2)}${line(1.15, -1.1, 1.15, 1.1)}`;
    }
    if (kind === "connector_2p") {
      return `<rect class="symbol-fill" x="${-2.3 * u}" y="${-2 * u}" width="${4.6 * u}" height="${4 * u}" rx="5"/>${line(2.3, -1, 3, -1)}${line(2.3, 1, 3, 1)}<circle cx="${2.05 * u}" cy="${-1 * u}" r="4" fill="#202824"/><circle cx="${2.05 * u}" cy="${1 * u}" r="4" fill="#202824"/>`;
    }
    return `${line(-3, 0, -1.65, 0)}<rect class="symbol-fill" x="${-1.65 * u}" y="${-1.35 * u}" width="${3.3 * u}" height="${2.7 * u}" rx="5"/>${line(1.65, 0, 3, 0)}`;
  }

  function getContract() {
    return {
      schema_version: CONTRACT_VERSION,
      engine_version: ENGINE_VERSION,
      responsibility: "render_only",
      calculates_values: false,
      selects_components: false,
      document_kinds: ["circuit_diagram", "single_line_diagram", "multi_line_diagram"],
      standard_profiles: ["IEC_EXPERIMENTAL"],
      grid_pitch_mil: GRID_PITCH_MIL,
      single_canvas_default: true,
      connection_format: "REFERENCE.PORT",
    };
  }

  return { render, validate, getRegistry, getContract };
})();

if (typeof globalThis !== "undefined") globalThis.ElectroDiagramCore = ElectroDiagramCore;
if (typeof module !== "undefined" && module.exports) module.exports = ElectroDiagramCore;
