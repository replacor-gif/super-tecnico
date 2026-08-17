(function (root, factory) {
  const duct = root?.STDuctDesigner || (typeof require === 'function' ? require('./duct-designer.js') : null);
  const rules = root?.STVentilationRules || (typeof require === 'function' ? require('./ventilation-rules.js') : null);
  const api = factory(duct, rules);
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.STVentilationDesigner = api;
})(typeof window !== 'undefined' ? window : globalThis, function (Duct, Rules) {
  'use strict';

  if (!Duct?.geometry || !Rules?.PROFILES) throw new Error('Ventilation designer dependencies are missing.');

  const G = Duct.geometry;
  const STORAGE_KEY = 'st.ventilationDesigner.v1';
  const CELL_PX = 44;
  const DEFAULTS = Object.freeze({
    projectName: 'Ventilación y extracción',
    phase: 'draw',
    profileId: 'cte_dwelling',
    systemMode: 'balanced',
    cellSizeM: .5,
    defaultHeightM: 2.5,
    customAch: 6,
    gridCols: 24,
    gridRows: 18,
  });
  const SYSTEM_MODES = Object.freeze({
    extract: Object.freeze({ label: 'Solo extracción', short: 'EXTRACCIÓN', kinds: ['extract'] }),
    supply: Object.freeze({ label: 'Solo impulsión', short: 'IMPULSIÓN', kinds: ['supply'] }),
    balanced: Object.freeze({ label: 'Impulsión + extracción', short: 'DOBLE FLUJO', kinds: ['supply', 'extract'] }),
  });

  function finite(value, fallback = 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function clamp(value, minimum, maximum) {
    return Math.min(maximum, Math.max(minimum, value));
  }

  function round(value, decimals = 3) {
    const factor = 10 ** decimals;
    return Math.round((finite(value) + Number.EPSILON) * factor) / factor;
  }

  function formatNumber(value, decimals = 0) {
    return finite(value).toLocaleString('es-ES', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  }

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>'"]/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));
  }

  function roomAtPoint(rooms, value) {
    return rooms.find(room => Duct.pointInPolygon(value, room.points, true)) || null;
  }

  function normalizeRoom(room, index, state) {
    const points = (Array.isArray(room?.points) ? room.points : []).map(item => G.point(item, state.gridCols, state.gridRows));
    const cleanPoints = points.filter((item, pointIndex) => pointIndex === 0 || G.pointKey(item) !== G.pointKey(points[pointIndex - 1]));
    const type = Rules.ROOM_TYPES[room?.type] ? room.type : 'unassigned';
    return {
      id: String(room?.id || `room-${index + 1}`).slice(0, 80),
      name: String(room?.name || '').slice(0, 80),
      type,
      points: cleanPoints,
      heightM: clamp(round(finite(room?.heightM, state.defaultHeightM), 2), 1.8, 15),
      occupants: clamp(Math.round(finite(room?.occupants, 0)), 0, 5000),
      parkingSpaces: clamp(Math.round(finite(room?.parkingSpaces, 0)), 0, 5000),
    };
  }

  function renumberRooms(rooms) {
    const totals = rooms.reduce((map, room) => map.set(room.type, (map.get(room.type) || 0) + 1), new Map());
    const counts = new Map();
    return rooms.map((room, index) => {
      counts.set(room.type, (counts.get(room.type) || 0) + 1);
      const definition = Rules.ROOM_TYPES[room.type];
      const generated = room.type === 'unassigned' ? `Estancia ${index + 1}`
        : totals.get(room.type) > 1 ? `${definition.label} ${counts.get(room.type)}` : definition.label;
      return { ...room, name: room.name || generated };
    });
  }

  function normalizeState(input = {}) {
    const profileId = Rules.PROFILES[input.profileId] ? input.profileId : DEFAULTS.profileId;
    const profile = Rules.PROFILES[profileId];
    const gridCols = clamp(Math.round(finite(input.gridCols, DEFAULTS.gridCols)), 10, 60);
    const gridRows = clamp(Math.round(finite(input.gridRows, DEFAULTS.gridRows)), 8, 50);
    const base = {
      projectName: String(input.projectName || DEFAULTS.projectName).slice(0, 100),
      phase: ['draw', 'configure', 'equipment'].includes(input.phase) ? input.phase : DEFAULTS.phase,
      profileId,
      systemMode: SYSTEM_MODES[input.systemMode] ? input.systemMode : profile.defaultMode,
      cellSizeM: [0.25, 0.5, 1].includes(finite(input.cellSizeM)) ? finite(input.cellSizeM) : DEFAULTS.cellSizeM,
      defaultHeightM: clamp(round(finite(input.defaultHeightM, DEFAULTS.defaultHeightM), 2), 1.8, 15),
      customAch: clamp(round(finite(input.customAch, DEFAULTS.customAch), 1), .1, 60),
      gridCols,
      gridRows,
    };
    const roomIds = new Set();
    const rooms = renumberRooms((Array.isArray(input.rooms) ? input.rooms : []).slice(0, 100)
      .map((room, index) => normalizeRoom(room, index, base))
      .filter(room => room.points.length >= 3 && Duct.polygonArea(room.points) >= .5)
      .map((room, index) => {
        let id = room.id;
        while (roomIds.has(id)) id = `${room.id}-${index + 1}`;
        roomIds.add(id);
        return { ...room, id };
      }));
    const terminalIds = new Set();
    const terminals = (Array.isArray(input.terminals) ? input.terminals : []).slice(0, 300).map((terminal, index) => {
      let id = String(terminal?.id || `terminal-${index + 1}`).slice(0, 80);
      while (terminalIds.has(id)) id = `${id}-${index + 1}`;
      terminalIds.add(id);
      const position = G.point(terminal, gridCols, gridRows);
      const room = roomAtPoint(rooms, position);
      return {
        id,
        kind: terminal?.kind === 'supply' ? 'supply' : 'extract',
        roomId: room?.id || '',
        ...position,
      };
    }).filter(terminal => terminal.roomId && SYSTEM_MODES[base.systemMode].kinds.includes(terminal.kind));
    const fanIds = new Set();
    const fans = (Array.isArray(input.fans) ? input.fans : []).slice(0, 30).map((fan, index) => {
      let id = String(fan?.id || `fan-${index + 1}`).slice(0, 80);
      while (fanIds.has(id)) id = `${id}-${index + 1}`;
      fanIds.add(id);
      return {
        id,
        kind: fan?.kind === 'supply' ? 'supply' : 'extract',
        ...G.point(fan, gridCols, gridRows),
      };
    }).filter(fan => SYSTEM_MODES[base.systemMode].kinds.includes(fan.kind));
    return { ...base, rooms, terminals, fans };
  }

  function emptyState(overrides = {}) {
    return normalizeState({ ...DEFAULTS, ...overrides });
  }

  function exampleState() {
    return normalizeState({
      ...DEFAULTS,
      phase: 'equipment',
      profileId: 'cte_dwelling',
      systemMode: 'balanced',
      rooms: [
        { id: 'main-bed', type: 'bedroom_main', points: [{ x: 1, y: 1 }, { x: 8, y: 1 }, { x: 8, y: 7 }, { x: 1, y: 7 }] },
        { id: 'bed', type: 'bedroom', points: [{ x: 8, y: 1 }, { x: 15, y: 1 }, { x: 15, y: 7 }, { x: 8, y: 7 }] },
        { id: 'living', type: 'living', points: [{ x: 15, y: 1 }, { x: 23, y: 1 }, { x: 23, y: 10 }, { x: 15, y: 10 }] },
        { id: 'hall', type: 'hallway', points: [{ x: 1, y: 7 }, { x: 15, y: 7 }, { x: 15, y: 11 }, { x: 1, y: 11 }] },
        { id: 'bath', type: 'bathroom', points: [{ x: 1, y: 11 }, { x: 7, y: 11 }, { x: 7, y: 17 }, { x: 1, y: 17 }] },
        { id: 'kitchen', type: 'kitchen', points: [{ x: 7, y: 11 }, { x: 15, y: 11 }, { x: 15, y: 17 }, { x: 7, y: 17 }] },
      ],
      terminals: [
        { id: 'sup-main', kind: 'supply', x: 4, y: 4 },
        { id: 'sup-bed', kind: 'supply', x: 11, y: 4 },
        { id: 'sup-living', kind: 'supply', x: 19, y: 5 },
        { id: 'ext-bath', kind: 'extract', x: 4, y: 14 },
        { id: 'ext-kitchen', kind: 'extract', x: 11, y: 14 },
      ],
      fans: [
        { id: 'fan-supply', kind: 'supply', x: 2, y: 9 },
        { id: 'fan-extract', kind: 'extract', x: 14, y: 9 },
      ],
    });
  }

  function roomAreaM2(room, state) {
    return Duct.polygonArea(room.points) * state.cellSizeM * state.cellSizeM;
  }

  function flowByMode(flowLps, mode) {
    return {
      supplyLps: mode === 'extract' ? 0 : flowLps,
      extractLps: mode === 'supply' ? 0 : flowLps,
    };
  }

  function calculateBaseRooms(state) {
    return state.rooms.map(room => {
      const areaM2 = roomAreaM2(room, state);
      const volumeM3 = areaM2 * room.heightM;
      const definition = Rules.ROOM_TYPES[room.type];
      return {
        ...room,
        typeLabel: definition.label,
        role: definition.role,
        areaM2,
        volumeM3,
        supplyLps: 0,
        extractLps: 0,
        demandBasis: '',
      };
    });
  }

  function dwellingDemands(rooms, systemMode) {
    const bedrooms = rooms.filter(room => ['bedroom_main', 'bedroom'].includes(room.type));
    const tier = bedrooms.length <= 1
      ? { living: 6, wetTotal: 12, wetMinimum: 6 }
      : bedrooms.length === 2
        ? { living: 8, wetTotal: 24, wetMinimum: 7 }
        : { living: 10, wetTotal: 33, wetMinimum: 8 };
    const wetRooms = rooms.filter(room => room.role === 'wet');
    const wetTarget = wetRooms.length ? Math.max(tier.wetTotal, wetRooms.length * tier.wetMinimum) : 0;
    const wetFlow = wetRooms.length ? wetTarget / wetRooms.length : 0;
    return rooms.map(room => {
      let supplyLps = 0;
      let extractLps = 0;
      let demandBasis = 'Sin caudal asignado por HS 3';
      if (room.type === 'bedroom_main') { supplyLps = 8; demandBasis = 'Dormitorio principal · 8 l/s'; }
      else if (room.type === 'bedroom') { supplyLps = 4; demandBasis = 'Resto de dormitorios · 4 l/s'; }
      else if (room.type === 'living' || room.type === 'office') { supplyLps = tier.living; demandBasis = `Sala seca · ${tier.living} l/s`; }
      else if (room.role === 'wet') { extractLps = wetFlow; demandBasis = `Local húmedo · ${formatNumber(wetFlow, 1)} l/s`; }
      if (systemMode === 'extract') supplyLps = 0;
      if (systemMode === 'supply') extractLps = 0;
      return { ...room, supplyLps, extractLps, demandBasis };
    });
  }

  function calculateRoomDemands(input = {}) {
    const state = normalizeState(input);
    const profile = Rules.PROFILES[state.profileId];
    const baseRooms = calculateBaseRooms(state);
    if (profile.method === 'cte_dwelling') return { state, profile, rooms: dwellingDemands(baseRooms, state.systemMode) };
    const rooms = baseRooms.map(room => {
      let flowLps = 0;
      let demandBasis = '';
      if (room.type === 'unassigned' || room.role === 'neutral') return { ...room, demandBasis: 'Zona de paso o sin identificar' };
      if (profile.method === 'people') {
        flowLps = room.occupants * profile.lpsPerPerson;
        demandBasis = `${room.occupants} personas × ${formatNumber(profile.lpsPerPerson, 1)} l/s`;
      } else if (profile.method === 'area') {
        flowLps = room.areaM2 * profile.lpsPerM2;
        demandBasis = `${formatNumber(room.areaM2, 1)} m² × ${formatNumber(profile.lpsPerM2, 2)} l/s`;
      } else if (profile.method === 'parking') {
        flowLps = room.parkingSpaces * profile.lpsPerSpace;
        demandBasis = `${room.parkingSpaces} plazas × ${formatNumber(profile.lpsPerSpace)} l/s`;
      } else if (profile.method === 'fixed_per_room') {
        flowLps = room.type === 'kitchen' ? profile.lpsPerRoom : 0;
        demandBasis = room.type === 'kitchen' ? `${formatNumber(profile.lpsPerRoom)} l/s por cocina` : 'Solo se asigna a cocinas';
      } else if (profile.method === 'ach') {
        flowLps = room.volumeM3 * state.customAch / 3.6;
        demandBasis = `${formatNumber(room.volumeM3, 1)} m³ × ${formatNumber(state.customAch, 1)} renovaciones/h`;
      }
      return { ...room, ...flowByMode(flowLps, state.systemMode), demandBasis };
    });
    return { state, profile, rooms };
  }

  function chooseRectangularSize(flowLps, targetVelocityMps = 4) {
    const requiredAreaCm2 = flowLps > 0 ? flowLps * 10 / targetVelocityMps : 0;
    if (!flowLps) return { widthCm: 0, heightCm: 0, areaCm2: 0, requiredAreaCm2: 0, velocityMps: 0 };
    let best = null;
    for (let heightCm = 10; heightCm <= 100; heightCm += 5) {
      for (let widthCm = heightCm; widthCm <= 200; widthCm += 5) {
        if (widthCm / heightCm > 4) continue;
        const areaCm2 = widthCm * heightCm;
        if (areaCm2 + 1e-9 < requiredAreaCm2) continue;
        const excess = areaCm2 - requiredAreaCm2;
        const score = excess * 100 + Math.abs(widthCm - heightCm) + heightCm * .02;
        if (!best || score < best.score) best = { widthCm, heightCm, areaCm2, score };
      }
    }
    const selected = best || { widthCm: 200, heightCm: 100, areaCm2: 20000 };
    const velocityMps = flowLps / 1000 / (selected.areaCm2 / 10000);
    return {
      widthCm: selected.widthCm,
      heightCm: selected.heightCm,
      areaCm2: selected.areaCm2,
      requiredAreaCm2,
      velocityMps,
      cteMechanicalMinimumCm2: flowLps * 2.5,
    };
  }

  function chooseGrilleSize(flowLps, targetVelocityMps = 2) {
    const requiredAreaCm2 = flowLps > 0 ? flowLps * 10 / targetVelocityMps : 0;
    if (!flowLps) return { widthCm: 0, heightCm: 0, areaCm2: 0, requiredAreaCm2: 0, velocityMps: 0 };
    let best = null;
    for (let heightCm = 10; heightCm <= 60; heightCm += 5) {
      for (let widthCm = Math.max(15, heightCm); widthCm <= 150; widthCm += 5) {
        if (widthCm / heightCm > 5) continue;
        const areaCm2 = widthCm * heightCm;
        if (areaCm2 + 1e-9 < requiredAreaCm2) continue;
        const score = (areaCm2 - requiredAreaCm2) * 100 + Math.abs(widthCm - heightCm) * .5;
        if (!best || score < best.score) best = { widthCm, heightCm, areaCm2, score };
      }
    }
    const selected = best || { widthCm: 150, heightCm: 60, areaCm2: 9000 };
    return {
      widthCm: selected.widthCm,
      heightCm: selected.heightCm,
      areaCm2: selected.areaCm2,
      requiredAreaCm2,
      velocityMps: flowLps / 1000 / (selected.areaCm2 / 10000),
    };
  }

  function enrichTerminals(state, rooms) {
    const roomMap = new Map(rooms.map(room => [room.id, room]));
    const counts = new Map();
    state.terminals.forEach(terminal => {
      const key = `${terminal.roomId}:${terminal.kind}`;
      counts.set(key, (counts.get(key) || 0) + 1);
    });
    return state.terminals.map(terminal => {
      const room = roomMap.get(terminal.roomId);
      const demandLps = terminal.kind === 'supply' ? room?.supplyLps || 0 : room?.extractLps || 0;
      const count = counts.get(`${terminal.roomId}:${terminal.kind}`) || 1;
      const airflowLps = demandLps / count;
      return {
        ...terminal,
        airflowLps,
        airflowM3h: airflowLps * 3.6,
        grille: chooseGrilleSize(airflowLps),
      };
    });
  }

  function routeState(state, rooms) {
    return {
      gridCols: state.gridCols,
      gridRows: state.gridRows,
      rooms: rooms.map(room => ({ ...room, conditioned: false })),
    };
  }

  function pathMetric(path) {
    if (!path?.length) return Infinity;
    let length = 0;
    for (let index = 1; index < path.length; index += 1) {
      const current = typeof path[index] === 'string' ? G.parsePointKey(path[index]) : path[index];
      const previous = typeof path[index - 1] === 'string' ? G.parsePointKey(path[index - 1]) : path[index - 1];
      length += Math.abs(current.x - previous.x) + Math.abs(current.y - previous.y);
    }
    return length;
  }

  function assignTerminalsToFans(state, rooms, terminals) {
    const routing = routeState(state, rooms);
    const assigned = new Map(state.fans.map(fan => [fan.id, []]));
    const unassigned = [];
    terminals.filter(terminal => terminal.airflowLps > 0).forEach(terminal => {
      const candidates = state.fans.filter(fan => fan.kind === terminal.kind).map(fan => {
        const path = G.findPath(routing, [fan], [terminal]);
        return { fan, path, score: pathMetric(path) };
      }).sort((one, two) => one.score - two.score || one.fan.id.localeCompare(two.fan.id));
      const winner = candidates[0];
      if (!winner || !Number.isFinite(winner.score)) unassigned.push(terminal);
      else assigned.get(winner.fan.id).push(terminal);
    });
    return { routing, assigned, unassigned };
  }

  function buildFanNetwork(fan, terminals, routing, state) {
    const ordered = [...terminals].sort((one, two) => pathMetric(G.findPath(routing, [fan], [two])) - pathMetric(G.findPath(routing, [fan], [one])));
    const edges = new Map();
    const nodes = new Map([[G.pointKey(fan), { x: fan.x, y: fan.y }]]);
    ordered.forEach((terminal, index) => {
      const starts = index ? [...nodes.values()] : [fan];
      const path = G.findPath(routing, starts, [terminal]);
      if (path?.length) G.addPathToNetwork(path, edges, nodes);
    });
    const rawEdges = [...edges.values()];
    const graph = G.buildGraph(rawEdges);
    const assignments = new Map();
    const connections = new Map();
    terminals.forEach(terminal => {
      const path = G.shortestPath(graph, G.pointKey(fan), G.pointKey(terminal));
      connections.set(terminal.id, path || []);
      if (!path) return;
      for (let index = 1; index < path.length; index += 1) {
        const key = G.edgeKey(G.parsePointKey(path[index - 1]), G.parsePointKey(path[index]));
        if (!assignments.has(key)) assignments.set(key, new Set());
        assignments.get(key).add(terminal.id);
      }
    });
    const terminalMap = new Map(terminals.map(terminal => [terminal.id, terminal]));
    const activeEdges = rawEdges.map(edge => {
      const key = G.edgeKey(edge.a, edge.b);
      const terminalIds = [...(assignments.get(key) || [])].sort();
      const airflowLps = terminalIds.reduce((sum, id) => sum + (terminalMap.get(id)?.airflowLps || 0), 0);
      const crossed = G.roomAtMidpoint(edge.a, edge.b, routing.rooms);
      return {
        ...edge,
        key,
        fanId: fan.id,
        kind: fan.kind,
        terminalIds,
        airflowLps,
        airflowM3h: airflowLps * 3.6,
        environment: crossed?.type || 'open',
        ...chooseRectangularSize(airflowLps),
      };
    }).filter(edge => edge.airflowLps > 0);
    const buckets = new Map();
    activeEdges.forEach(edge => {
      const signature = edge.terminalIds.join('|');
      if (!buckets.has(signature)) buckets.set(signature, []);
      buckets.get(signature).push(edge);
    });
    const sections = [];
    buckets.forEach(bucket => G.connectedComponents(bucket).forEach(component => {
      const sample = component[0];
      sections.push({
        id: '',
        fanId: fan.id,
        kind: fan.kind,
        terminalIds: sample.terminalIds,
        airflowLps: sample.airflowLps,
        airflowM3h: sample.airflowM3h,
        widthCm: sample.widthCm,
        heightCm: sample.heightCm,
        velocityMps: sample.velocityMps,
        lengthM: component.reduce((sum, edge) => sum + G.edgeLengthGrid(edge), 0) * state.cellSizeM,
        edges: component,
        isMain: sample.terminalIds.length > 1,
      });
    }));
    let main = 0;
    let branch = 0;
    sections.sort((one, two) => Number(two.isMain) - Number(one.isMain) || two.airflowLps - one.airflowLps)
      .forEach(section => { section.id = section.isMain ? `P${main += 1}` : `R${branch += 1}`; });
    const connectedTerminalIds = new Set([...connections].filter(([, path]) => path.length).map(([id]) => id));
    const airflowLps = terminals.reduce((sum, terminal) => sum + terminal.airflowLps, 0);
    const longestRunM = Math.max(0, ...[...connections.values()].map(path => pathMetric(path) * state.cellSizeM));
    return {
      fan: { ...fan, airflowLps, airflowM3h: airflowLps * 3.6, connectedTerminals: connectedTerminalIds.size, longestRunM },
      activeEdges,
      sections,
      connections,
    };
  }

  function uniqueWarnings(warnings) {
    const seen = new Set();
    return warnings.filter(item => !seen.has(item.text) && seen.add(item.text));
  }

  function calculateProject(input = {}) {
    const demand = calculateRoomDemands(input);
    const { state, profile, rooms } = demand;
    const roomMap = new Map(rooms.map(room => [room.id, room]));
    const terminals = enrichTerminals(state, rooms);
    const terminalMap = new Map(terminals.map(terminal => [terminal.id, terminal]));
    const assignment = assignTerminalsToFans(state, rooms, terminals);
    const networks = state.fans.map(fan => buildFanNetwork(fan, assignment.assigned.get(fan.id) || [], assignment.routing, state));
    const activeEdges = networks.flatMap(network => network.activeEdges);
    let supplyNetworkIndex = 0;
    let extractNetworkIndex = 0;
    const sections = networks.flatMap(network => {
      const networkIndex = network.fan.kind === 'supply' ? ++supplyNetworkIndex : ++extractNetworkIndex;
      const networkId = `${network.fan.kind === 'supply' ? 'I' : 'E'}${networkIndex}`;
      return network.sections.map(section => ({ ...section, id: `${networkId}-${section.id}` }));
    });
    const fanResults = networks.map(network => network.fan);
    const supplyLps = rooms.reduce((sum, room) => sum + room.supplyLps, 0);
    const extractLps = rooms.reduce((sum, room) => sum + room.extractLps, 0);
    const warnings = [];
    if (!rooms.length) warnings.push({ level: 'info', text: 'Dibuja los recintos para comenzar.' });
    if (rooms.some(room => room.type === 'unassigned')) warnings.push({ level: 'warn', text: 'Falta identificar algún recinto.' });
    if (profile.method === 'people' && rooms.some(room => room.role !== 'neutral' && room.type !== 'unassigned' && room.occupants < 1)) warnings.push({ level: 'warn', text: 'Indica la ocupación prevista en todos los recintos ocupados.' });
    if (profile.method === 'parking' && rooms.some(room => room.type !== 'unassigned' && room.role !== 'neutral' && room.parkingSpaces < 1)) warnings.push({ level: 'warn', text: 'Indica el número de plazas del aparcamiento.' });
    rooms.forEach(room => {
      ['supply', 'extract'].forEach(kind => {
        const required = kind === 'supply' ? room.supplyLps : room.extractLps;
        if (required > 0 && !terminals.some(terminal => terminal.roomId === room.id && terminal.kind === kind)) warnings.push({ level: 'warn', text: `${room.name}: falta colocar una rejilla de ${kind === 'supply' ? 'impulsión' : 'extracción'}.` });
      });
    });
    SYSTEM_MODES[state.systemMode].kinds.forEach(kind => {
      const relevant = terminals.filter(terminal => terminal.kind === kind && terminal.airflowLps > 0);
      if (relevant.length && !state.fans.some(fan => fan.kind === kind)) warnings.push({ level: 'warn', text: `Falta colocar la turbina de ${kind === 'supply' ? 'impulsión' : 'extracción'}.` });
    });
    assignment.unassigned.forEach(terminal => warnings.push({ level: 'warn', text: `La rejilla ${terminal.id} no ha podido conectarse a una turbina compatible.` }));
    if (profile.method === 'cte_dwelling' && rooms.some(room => room.type === 'kitchen')) warnings.push({ level: 'info', text: 'La extracción general de la cocina no sustituye la extracción independiente mínima de 50 l/s en la zona de cocción.' });
    if (profile.method === 'cte_dwelling' && state.systemMode === 'extract') warnings.push({ level: 'info', text: 'En extracción mecánica deben comprobarse también las aberturas de admisión en locales secos y las aberturas de paso hacia los locales húmedos.' });
    if (profile.method === 'cte_dwelling' && state.systemMode === 'supply') warnings.push({ level: 'warn', text: 'La impulsión por sí sola no completa el esquema general de HS 3: debe garantizarse la extracción desde los locales húmedos.' });
    if (state.profileId === 'cte_garage') {
      const spaces = rooms.reduce((sum, room) => sum + room.parkingSpaces, 0);
      const areaM2 = rooms.reduce((sum, room) => sum + room.areaM2, 0);
      const extractFans = state.fans.filter(fan => fan.kind === 'extract').length;
      if (spaces > 5 || areaM2 > 100) warnings.push({ level: 'warn', text: 'El CTE HS 3 exige detección de CO en garajes de más de 5 plazas o más de 100 m² útiles.' });
      if (spaces >= 15 && extractFans < 2) warnings.push({ level: 'warn', text: 'Con 15 o más plazas deben disponerse al menos dos redes de extracción por planta.' });
    }
    if (profile.method === 'people') warnings.push({ level: 'info', text: 'El método RITE por persona presupone actividad próxima a 1,2 met, baja emisión de otros contaminantes y ausencia de humo.' });
    if (profile.method === 'ach') warnings.push({ level: 'info', text: 'Las renovaciones/hora son un criterio indicado por el técnico y no justifican por sí solas el cumplimiento reglamentario.' });
    if (activeEdges.length) warnings.push({ level: 'ok', text: 'La red se ha trazado desde las posiciones reales indicadas y prioriza pasillos y zonas de servicio.' });
    if (fanResults.some(fan => fan.airflowLps > 0)) warnings.push({ level: 'info', text: 'La turbina debe seleccionarse para el caudal calculado a la presión necesaria para vencer pérdidas, accesorios, filtros y rejillas.' });
    return {
      state,
      profile,
      source: Rules.SOURCES[profile.source],
      rooms,
      roomMap,
      terminals,
      terminalMap,
      fanResults,
      networks,
      activeEdges,
      sections,
      warnings: uniqueWarnings(warnings),
      totals: {
        rooms: rooms.length,
        identifiedRooms: rooms.filter(room => room.type !== 'unassigned').length,
        areaM2: rooms.reduce((sum, room) => sum + room.areaM2, 0),
        volumeM3: rooms.reduce((sum, room) => sum + room.volumeM3, 0),
        supplyLps,
        extractLps,
        supplyM3h: supplyLps * 3.6,
        extractM3h: extractLps * 3.6,
        terminals: terminals.length,
        fans: state.fans.length,
        connectedTerminals: fanResults.reduce((sum, fan) => sum + fan.connectedTerminals, 0),
      },
    };
  }

  function pathData(points, px) {
    return points.map((item, index) => `${index ? 'L' : 'M'} ${px(item.x)} ${px(item.y)}`).join(' ') + ' Z';
  }

  function renderPlanSvg(result, options = {}) {
    const state = result.state;
    const selectedRoomId = options.selectedRoomId || '';
    const selectedPlacement = options.selectedPlacement || null;
    const drawingPoints = options.drawingPoints || [];
    const width = state.gridCols * CELL_PX;
    const height = state.gridRows * CELL_PX;
    const px = value => value * CELL_PX;
    const patterns = Object.entries(Rules.ROOM_TYPES).map(([type, definition]) => `<pattern id="ventHatch-${type}" width="13" height="13" patternUnits="userSpaceOnUse" patternTransform="rotate(35)"><line x1="0" y1="0" x2="0" y2="13" stroke="${definition.color}" stroke-width="4" opacity=".28"/></pattern>`).join('');
    const parts = [
      `<svg class="installation-plan ventilation-plan" viewBox="0 0 ${width} ${height}" role="img" aria-label="Plano de ventilación y extracción">`,
      `<defs><pattern id="ventGrid" width="${CELL_PX}" height="${CELL_PX}" patternUnits="userSpaceOnUse"><path d="M ${CELL_PX} 0 L 0 0 0 ${CELL_PX}"/></pattern><filter id="ventGlow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>${patterns}</defs>`,
      `<rect class="plan-background" width="${width}" height="${height}"/><rect class="plan-grid" width="${width}" height="${height}" fill="url(#ventGrid)"/>`,
    ];
    result.rooms.forEach((room, index) => {
      const center = G.nearestInteriorPoint(room, G.polygonCentroid(room.points));
      const bounds = G.polygonBounds(room.points);
      const d = pathData(room.points, px);
      parts.push(`<g class="plan-room room-type-${room.type}${selectedRoomId === room.id ? ' is-selected' : ''}" data-kind="vent-room" data-id="${escapeHtml(room.id)}"><path class="room-fill" d="${d}" fill="url(#ventHatch-${room.type})"/><path class="room-wall" d="${d}"/>`);
      if (state.phase === 'draw') {
        const deleteX = px(bounds.x + bounds.width) - 18;
        const deleteY = px(bounds.y) + 18;
        parts.push(`<text class="room-number-label" x="${px(center.x)}" y="${px(center.y) + 5}" text-anchor="middle">${index + 1}</text><g class="room-delete" data-kind="vent-room-delete" data-id="${escapeHtml(room.id)}" transform="translate(${deleteX} ${deleteY})"><circle class="room-delete-hit" r="26"/><circle class="room-delete-button" r="13"/><path d="M-4-4l8 8M4-4l-8 8"/></g>`);
      } else {
        const demand = room.supplyLps || room.extractLps;
        parts.push(`<text class="room-name-label" x="${px(center.x)}" y="${px(center.y) - 7}" text-anchor="middle">${escapeHtml(room.name.toUpperCase())}</text><text class="room-demand-label" x="${px(center.x)}" y="${px(center.y) + 14}" text-anchor="middle">${formatNumber(room.volumeM3, 1)} m³${demand ? ` · ${formatNumber(demand, 1)} l/s` : ''}</text>`);
      }
      parts.push('</g>');
    });
    if (state.phase === 'equipment') {
      result.activeEdges.forEach(edge => {
        const visualWidth = clamp(5 + Math.sqrt(edge.widthCm * edge.heightCm) * .25, 7, 23);
        parts.push(`<line class="vent-route route-${edge.kind}${edge.environment === 'hallway' ? ' through-hallway' : ''}" x1="${px(edge.a.x)}" y1="${px(edge.a.y)}" x2="${px(edge.b.x)}" y2="${px(edge.b.y)}" style="--route-width:${visualWidth}px"><title>${edge.kind === 'supply' ? 'Impulsión' : 'Extracción'} · ${formatNumber(edge.airflowM3h)} m³/h · ${edge.widthCm} × ${edge.heightCm} cm</title></line>`);
      });
      result.terminals.forEach(terminal => {
        const label = terminal.kind === 'supply' ? 'I' : 'E';
        const selected = selectedPlacement?.kind === 'terminal' && selectedPlacement.id === terminal.id;
        parts.push(`<g class="vent-terminal terminal-${terminal.kind}${selected ? ' is-selected' : ''}" data-kind="vent-terminal" data-id="${escapeHtml(terminal.id)}" transform="translate(${px(terminal.x)} ${px(terminal.y)})"><circle class="placement-hit" r="24"/><rect x="-17" y="-11" width="34" height="22" rx="5"/><path d="M-11-5h22M-11 0h22M-11 5h22"/><text x="0" y="-18" text-anchor="middle">${label}</text><title>Rejilla de ${terminal.kind === 'supply' ? 'impulsión' : 'extracción'} · ${formatNumber(terminal.airflowM3h)} m³/h · ${terminal.grille.widthCm} × ${terminal.grille.heightCm} cm</title></g>`);
      });
      result.fanResults.forEach(fan => {
        const selected = selectedPlacement?.kind === 'fan' && selectedPlacement.id === fan.id;
        parts.push(`<g class="vent-fan fan-${fan.kind}${selected ? ' is-selected' : ''}" data-kind="vent-fan" data-id="${escapeHtml(fan.id)}" transform="translate(${px(fan.x)} ${px(fan.y)})"><circle class="placement-hit" r="31"/><circle class="fan-body" r="23"/><path d="M0-5c-7-16 4-22 11-14 5 6 0 14-7 19M5 0c16-7 22 4 14 11-6 5-14 0-19-7M0 5c7 16-4 22-11 14-5-6 0-14 7-19"/><circle r="3"/><text x="0" y="-31" text-anchor="middle">${fan.kind === 'supply' ? 'TURBINA I' : 'TURBINA E'}</text><title>${formatNumber(fan.airflowM3h)} m³/h · recorrido más largo ${formatNumber(fan.longestRunM, 1)} m</title></g>`);
      });
    }
    if (state.phase === 'draw' && drawingPoints.length) {
      parts.push(`<polyline class="drawing-line" points="${drawingPoints.map(item => `${px(item.x)},${px(item.y)}`).join(' ')}"/>`);
      drawingPoints.forEach((item, index) => parts.push(`<g class="drawing-point${index === 0 ? ' first-point' : ''}" ${index === 0 && drawingPoints.length >= 3 ? 'data-kind="vent-close-polygon"' : ''} transform="translate(${px(item.x)} ${px(item.y)})"><circle class="point-hit" r="28"/><circle class="point-dot" r="${index === 0 ? 10 : 7}"/>${index === 0 && drawingPoints.length >= 3 ? '<text x="0" y="-17" text-anchor="middle">CERRAR</text>' : ''}</g>`));
    }
    parts.push(`<g class="scale-marker" transform="translate(${width - 150} ${height - 25})"><line x1="0" y1="0" x2="${CELL_PX * 2}" y2="0"/><path d="M0-6v12M${CELL_PX * 2}-6v12"/><text x="${CELL_PX}" y="-10" text-anchor="middle">${formatNumber(state.cellSizeM * 2, 2)} m</text></g>`);
    parts.push('</svg>');
    return { svg: parts.join(''), width, height };
  }

  function initBrowser() {
    if (typeof document === 'undefined' || !document.getElementById('ventPlanStage')) return;
    const $ = id => document.getElementById(id);
    const elements = {
      profile: $('ventProfile'), system: $('ventSystemMode'), defaultHeight: $('ventDefaultHeight'), customAch: $('ventCustomAch'), achField: $('ventAchField'), cellSize: $('ventCellSize'),
      phaseBadge: $('ventPhaseBadge'), message: $('ventAssistantMessage'), status: $('ventPlanStatus'), stage: $('ventPlanStage'), scroll: $('ventPlanScroll'), summary: $('ventPlanSummary'), phaseAction: $('ventPhaseAction'),
      roomEditor: $('ventRoomEditor'), roomName: $('ventRoomName'), roomType: $('ventRoomType'), roomHeight: $('ventRoomHeight'), occupantsField: $('ventOccupantsField'), occupants: $('ventRoomOccupants'), parkingField: $('ventParkingField'), parking: $('ventRoomParking'),
      toolbar: $('ventPlacementToolbar'), results: $('ventAutomaticResult'), resultSummary: $('ventResultSummary'), alerts: $('ventAlerts'), networks: $('ventNetworkResults'), rooms: $('ventRoomResults'), fans: $('ventFanResults'), networkStatus: $('ventNetworkStatus'),
      undo: $('ventUndo'), redo: $('ventRedo'), example: $('ventLoadExample'), clear: $('ventClearProject'), print: $('ventPrintProject'),
    };
    let state = loadState();
    let result = calculateProject(state);
    let drawingPoints = [];
    let selectedRoomId = '';
    let selectedPlacement = null;
    let activeTool = '';
    let transientMessage = '';
    let zoom = 1;
    const history = [];
    const future = [];

    function loadState() {
      try {
        const saved = localStorage.getItem(STORAGE_KEY);
        return saved ? normalizeState(JSON.parse(saved)) : emptyState();
      } catch (_) {
        return emptyState();
      }
    }

    function save() {
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (_) {}
    }

    function commit(next) {
      history.push(JSON.stringify(state));
      if (history.length > 60) history.shift();
      future.length = 0;
      state = normalizeState(next);
      transientMessage = '';
      render();
    }

    function undo() {
      if (drawingPoints.length) { drawingPoints.pop(); render(); return; }
      if (!history.length) return;
      future.push(JSON.stringify(state));
      state = normalizeState(JSON.parse(history.pop()));
      render();
    }

    function redo() {
      if (!future.length || drawingPoints.length) return;
      history.push(JSON.stringify(state));
      state = normalizeState(JSON.parse(future.pop()));
      render();
    }

    function pointerGridPoint(event) {
      const svg = elements.stage.querySelector('svg');
      const svgPoint = svg.createSVGPoint();
      svgPoint.x = event.clientX;
      svgPoint.y = event.clientY;
      const local = svgPoint.matrixTransform(svg.getScreenCTM().inverse());
      return G.point({ x: local.x / CELL_PX, y: local.y / CELL_PX }, state.gridCols, state.gridRows);
    }

    function closePolygon() {
      if (drawingPoints.length < 3) return;
      if (Duct.polygonArea(drawingPoints) < 1 || Duct.polygonSelfIntersects(drawingPoints)) {
        transientMessage = '<strong>Revisa el contorno.</strong> La estancia debe tener superficie y no puede cruzarse consigo misma.';
        render();
        return;
      }
      const candidate = { points: [...drawingPoints] };
      if (state.rooms.some(room => Duct.roomOverlap(candidate, room))) {
        transientMessage = '<strong>Las estancias no pueden superponerse.</strong> Pueden compartir paredes.';
        render();
        return;
      }
      const id = `room-${Date.now()}-${Math.random().toString(16).slice(2, 6)}`;
      drawingPoints = [];
      commit({ ...state, rooms: [...state.rooms, { id, type: 'unassigned', heightM: state.defaultHeightM, points: candidate.points }] });
    }

    function place(kind, position) {
      if (kind.startsWith('terminal-')) {
        const room = roomAtPoint(state.rooms, position);
        if (!room) { transientMessage = '<strong>La rejilla debe quedar dentro de una estancia.</strong>'; render(); return; }
        const terminalKind = kind.endsWith('supply') ? 'supply' : 'extract';
        const id = `terminal-${terminalKind}-${Date.now()}-${Math.random().toString(16).slice(2, 5)}`;
        commit({ ...state, terminals: [...state.terminals, { id, kind: terminalKind, roomId: room.id, ...position }] });
      } else if (kind.startsWith('fan-')) {
        const fanKind = kind.endsWith('supply') ? 'supply' : 'extract';
        const id = `fan-${fanKind}-${Date.now()}-${Math.random().toString(16).slice(2, 5)}`;
        commit({ ...state, fans: [...state.fans, { id, kind: fanKind, ...position }] });
      }
    }

    function moveSelectedPlacement(position) {
      if (!selectedPlacement) return;
      if (selectedPlacement.kind === 'terminal') {
        const room = roomAtPoint(state.rooms, position);
        if (!room) { transientMessage = '<strong>La rejilla debe quedar dentro de una estancia.</strong>'; render(); return; }
        const id = selectedPlacement.id;
        selectedPlacement = null;
        commit({ ...state, terminals: state.terminals.map(item => item.id === id ? { ...item, roomId: room.id, ...position } : item) });
      } else {
        const id = selectedPlacement.id;
        selectedPlacement = null;
        commit({ ...state, fans: state.fans.map(item => item.id === id ? { ...item, ...position } : item) });
      }
    }

    function handlePlanClick(event) {
      const target = event.target.closest('[data-kind]');
      if (state.phase === 'draw') {
        if (target?.dataset.kind === 'vent-room-delete') {
          commit({ ...state, rooms: state.rooms.filter(room => room.id !== target.dataset.id) });
          return;
        }
        if (target?.dataset.kind === 'vent-close-polygon') { closePolygon(); return; }
        const position = pointerGridPoint(event);
        if (drawingPoints.length >= 3 && G.pointKey(position) === G.pointKey(drawingPoints[0])) { closePolygon(); return; }
        if (!drawingPoints.length || G.pointKey(position) !== G.pointKey(drawingPoints.at(-1))) drawingPoints.push(position);
        render();
        return;
      }
      if (state.phase === 'configure') {
        if (target?.dataset.kind === 'vent-room') {
          selectedRoomId = target.dataset.id;
          render();
        }
        return;
      }
      if (state.phase !== 'equipment') return;
      if (activeTool === 'delete') {
        if (target?.dataset.kind === 'vent-terminal') commit({ ...state, terminals: state.terminals.filter(item => item.id !== target.dataset.id) });
        else if (target?.dataset.kind === 'vent-fan') commit({ ...state, fans: state.fans.filter(item => item.id !== target.dataset.id) });
        else { transientMessage = '<strong>Toca una rejilla o turbina para borrarla.</strong>'; render(); }
        return;
      }
      if (!activeTool && target?.dataset.kind === 'vent-terminal') {
        selectedPlacement = { kind: 'terminal', id: target.dataset.id };
        transientMessage = '<strong>Rejilla seleccionada.</strong> Toca ahora su nueva posición dentro del plano.';
        render();
        return;
      }
      if (!activeTool && target?.dataset.kind === 'vent-fan') {
        selectedPlacement = { kind: 'fan', id: target.dataset.id };
        transientMessage = '<strong>Turbina seleccionada.</strong> Toca ahora su nueva posición dentro del plano.';
        render();
        return;
      }
      if (!activeTool && selectedPlacement) {
        moveSelectedPlacement(pointerGridPoint(event));
        return;
      }
      if (!activeTool) { transientMessage = '<strong>Elige abajo qué quieres colocar.</strong>'; render(); return; }
      place(activeTool, pointerGridPoint(event));
    }

    function applyZoom() {
      elements.stage.style.width = `${result.state.gridCols * CELL_PX * zoom}px`;
    }

    function fitPlan() {
      const available = Math.max(280, elements.scroll.clientWidth - 10);
      zoom = clamp(available / (state.gridCols * CELL_PX), .28, 1.35);
      applyZoom();
    }

    function renderSetup() {
      elements.profile.value = state.profileId;
      elements.system.value = state.systemMode;
      elements.defaultHeight.value = state.defaultHeightM;
      elements.customAch.value = state.customAch;
      elements.cellSize.value = state.cellSizeM;
      elements.achField.hidden = result.profile.method !== 'ach';
    }

    function renderRoomEditor() {
      const room = state.rooms.find(item => item.id === selectedRoomId) || (state.phase === 'configure' ? state.rooms[0] : null);
      if (room && !selectedRoomId) selectedRoomId = room.id;
      elements.roomEditor.hidden = state.phase !== 'configure' || !room;
      if (!room) return;
      elements.roomName.value = room.name || '';
      elements.roomType.value = room.type;
      elements.roomHeight.value = room.heightM;
      elements.occupantsField.hidden = result.profile.method !== 'people';
      elements.parkingField.hidden = result.profile.method !== 'parking';
      elements.occupants.value = room.occupants;
      elements.parking.value = room.parkingSpaces;
      elements.roomEditor.querySelector('[data-room-editor-title]').textContent = room.name || 'Estancia seleccionada';
    }

    function renderControls() {
      const phases = {
        draw: ['DIBUJANDO RECINTOS', 'He terminado el plano'],
        configure: ['IDENTIFICANDO RECINTOS', 'Colocar rejillas y turbinas'],
        equipment: ['COLOCANDO LA INSTALACIÓN', 'Editar recintos'],
      };
      elements.phaseBadge.textContent = phases[state.phase][0];
      elements.phaseAction.querySelector('span').textContent = phases[state.phase][1];
      elements.phaseAction.disabled = state.phase === 'draw' && (!state.rooms.length || drawingPoints.length > 0);
      elements.toolbar.hidden = state.phase !== 'equipment';
      elements.toolbar.querySelectorAll('[data-place-tool]').forEach(button => {
        const kind = button.dataset.placeTool;
        const direction = kind.endsWith('supply') ? 'supply' : kind.endsWith('extract') ? 'extract' : '';
        button.hidden = direction && !SYSTEM_MODES[state.systemMode].kinds.includes(direction);
        button.classList.toggle('is-active', activeTool === kind);
      });
      elements.undo.disabled = !history.length && !drawingPoints.length;
      elements.redo.disabled = !future.length || drawingPoints.length > 0;
    }

    function renderMessage() {
      if (transientMessage) {
        elements.message.innerHTML = `<span>✦</span><p>${transientMessage}</p>`;
        return;
      }
      if (state.phase === 'draw') elements.message.innerHTML = '<span>1</span><p><strong>Toca todas las esquinas de cada recinto.</strong> Cierra volviendo al primer punto.</p>';
      else if (state.phase === 'configure') elements.message.innerHTML = '<span>2</span><p><strong>Toca una estancia y completa su ficha.</strong> La altura permite calcular su volumen real.</p>';
      else elements.message.innerHTML = `<span>3</span><p><strong>Elige una rejilla o una turbina y toca su posición real.</strong> ${activeTool ? 'Herramienta activa: ' + escapeHtml(activeTool.replace('-', ' ')) + '.' : 'El recorrido y las medidas aparecen automáticamente.'}</p>`;
    }

    function renderPlan() {
      elements.stage.innerHTML = renderPlanSvg(result, { drawingPoints, selectedRoomId, selectedPlacement }).svg;
      applyZoom();
      elements.status.textContent = state.phase === 'draw' ? `${state.rooms.length} recintos dibujados` : state.phase === 'configure' ? `${result.totals.identifiedRooms} de ${result.totals.rooms} identificados` : `${result.totals.connectedTerminals} de ${result.totals.terminals} rejillas conectadas`;
      elements.summary.innerHTML = `<span><b>${result.totals.rooms}</b> recintos</span><span><b>${formatNumber(result.totals.areaM2, 1)}</b> m²</span><span><b>${formatNumber(result.totals.volumeM3, 1)}</b> m³</span><span><b>${result.totals.terminals}</b> rejillas</span><span><b>${result.totals.fans}</b> turbinas</span>`;
    }

    function metric(label, value, detail, color) {
      return `<article style="--metric-color:${color}"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong><small>${escapeHtml(detail)}</small></article>`;
    }

    function renderResults() {
      const ready = state.phase === 'equipment' && result.totals.terminals > 0;
      elements.results.hidden = !ready;
      if (!ready) return;
      const requiredTerminalsPlaced = result.rooms.every(room => (
        (!room.supplyLps || result.terminals.some(terminal => terminal.roomId === room.id && terminal.kind === 'supply'))
        && (!room.extractLps || result.terminals.some(terminal => terminal.roomId === room.id && terminal.kind === 'extract'))
      ));
      const activeTerminalCount = result.terminals.filter(terminal => terminal.airflowLps > 0).length;
      const complete = requiredTerminalsPlaced && activeTerminalCount > 0 && result.totals.connectedTerminals === activeTerminalCount;
      elements.networkStatus.textContent = complete ? 'RED CALCULADA' : 'FALTA COMPLETAR';
      elements.resultSummary.innerHTML = [
        metric('Volumen dibujado', `${formatNumber(result.totals.volumeM3, 1)} m³`, `${formatNumber(result.totals.areaM2, 1)} m² útiles`, '#00c8ff'),
        metric('Impulsión', `${formatNumber(result.totals.supplyM3h)} m³/h`, `${formatNumber(result.totals.supplyLps, 1)} l/s`, '#51ff7d'),
        metric('Extracción', `${formatNumber(result.totals.extractM3h)} m³/h`, `${formatNumber(result.totals.extractLps, 1)} l/s`, '#ff3fa7'),
        metric('Criterio', result.profile.short, result.profile.reference, '#ffe438'),
      ].join('');
      elements.alerts.innerHTML = result.warnings.map(item => `<p class="alert-${item.level}"><span>${item.level === 'ok' ? '✓' : item.level === 'warn' ? '!' : 'i'}</span>${escapeHtml(item.text)}</p>`).join('');
      elements.networks.innerHTML = result.sections.length ? result.sections.map(section => `<div class="result-row ${section.isMain ? 'main-section' : ''}"><b>${escapeHtml(section.id)}</b><span><strong>${section.kind === 'supply' ? 'Impulsión' : 'Extracción'} · ${section.isMain ? 'principal' : 'ramal'}</strong><small>${formatNumber(section.lengthM, 1)} m · ${formatNumber(section.airflowM3h)} m³/h · ${formatNumber(section.velocityMps, 1)} m/s</small></span><em>${section.widthCm} × ${section.heightCm} cm</em></div>`).join('') : '<p class="empty-result">Coloca las rejillas y turbinas para generar la red.</p>';
      elements.rooms.innerHTML = result.rooms.filter(room => room.type !== 'unassigned').map(room => {
        const supply = result.terminals.filter(terminal => terminal.roomId === room.id && terminal.kind === 'supply');
        const extract = result.terminals.filter(terminal => terminal.roomId === room.id && terminal.kind === 'extract');
        const terminal = supply[0] || extract[0];
        const flow = room.supplyLps || room.extractLps;
        return `<div class="result-row room-result"><b>${room.supplyLps ? 'I' : room.extractLps ? 'E' : '·'}</b><span><strong>${escapeHtml(room.name)}</strong><small>${formatNumber(room.volumeM3, 1)} m³ · ${escapeHtml(room.demandBasis)}</small></span><em>${flow && terminal ? `${terminal.grille.widthCm} × ${terminal.grille.heightCm} cm` : 'Sin rejilla'}</em></div>`;
      }).join('');
      elements.fans.innerHTML = result.fanResults.length ? result.fanResults.map(fan => `<div class="result-row"><b>${fan.kind === 'supply' ? 'I' : 'E'}</b><span><strong>${fan.kind === 'supply' ? 'Turbina de impulsión' : 'Turbina de extracción'}</strong><small>${fan.connectedTerminals} rejillas · recorrido más largo ${formatNumber(fan.longestRunM, 1)} m</small></span><em>${formatNumber(fan.airflowM3h)} m³/h</em></div>`).join('') : '<p class="empty-result">Todavía no hay turbinas colocadas.</p>';
      const sourceLink = $('ventSourceLink');
      sourceLink.textContent = result.source.label;
      sourceLink.href = result.source.url || '#';
      sourceLink.hidden = !result.source.url;
      $('ventSourceReference').textContent = `${result.profile.reference}. Verificación interna: ${result.source.checked}.`;
    }

    function render() {
      result = calculateProject(state);
      renderSetup();
      renderControls();
      renderMessage();
      renderRoomEditor();
      renderPlan();
      renderResults();
      save();
    }

    elements.stage.addEventListener('click', handlePlanClick);
    elements.profile.addEventListener('change', () => {
      const profile = Rules.PROFILES[elements.profile.value];
      activeTool = '';
      selectedPlacement = null;
      commit({ ...state, profileId: elements.profile.value, systemMode: profile.defaultMode });
    });
    elements.system.addEventListener('change', () => { activeTool = ''; selectedPlacement = null; commit({ ...state, systemMode: elements.system.value }); });
    elements.defaultHeight.addEventListener('change', () => {
      const previous = state.defaultHeightM;
      const next = finite(elements.defaultHeight.value, previous);
      commit({ ...state, defaultHeightM: next, rooms: state.rooms.map(room => room.heightM === previous ? { ...room, heightM: next } : room) });
    });
    elements.customAch.addEventListener('change', () => commit({ ...state, customAch: elements.customAch.value }));
    elements.cellSize.addEventListener('change', () => commit({ ...state, cellSizeM: elements.cellSize.value }));
    elements.phaseAction.addEventListener('click', () => {
      if (state.phase === 'draw') {
        if (!state.rooms.length || drawingPoints.length) return;
        selectedRoomId = state.rooms[0]?.id || '';
        commit({ ...state, phase: 'configure' });
      } else if (state.phase === 'configure') {
        if (state.rooms.some(room => room.type === 'unassigned')) { transientMessage = '<strong>Identifica todos los recintos antes de continuar.</strong>'; render(); return; }
        activeTool = SYSTEM_MODES[state.systemMode].kinds.includes('extract') ? 'terminal-extract' : 'terminal-supply';
        commit({ ...state, phase: 'equipment' });
        setTimeout(() => elements.scroll.scrollIntoView({ behavior: 'smooth', block: 'center' }), 80);
      } else {
        activeTool = '';
        selectedRoomId = state.rooms[0]?.id || '';
        commit({ ...state, phase: 'configure' });
      }
    });
    elements.roomEditor.addEventListener('change', () => {
      const id = selectedRoomId;
      if (!id) return;
      commit({ ...state, rooms: state.rooms.map(room => room.id === id ? {
        ...room,
        name: elements.roomName.value,
        type: elements.roomType.value,
        heightM: elements.roomHeight.value,
        occupants: elements.occupants.value,
        parkingSpaces: elements.parking.value,
      } : room) });
    });
    elements.toolbar.addEventListener('click', event => {
      const button = event.target.closest('[data-place-tool]');
      if (!button || button.hidden) return;
      activeTool = activeTool === button.dataset.placeTool ? '' : button.dataset.placeTool;
      selectedPlacement = null;
      render();
    });
    elements.undo.addEventListener('click', undo);
    elements.redo.addEventListener('click', redo);
    elements.example.addEventListener('click', () => {
      if (state.rooms.length && !confirm('¿Sustituir el plano actual por el ejemplo?')) return;
      drawingPoints = [];
      selectedRoomId = '';
      activeTool = '';
      selectedPlacement = null;
      commit(exampleState());
      setTimeout(fitPlan, 40);
    });
    elements.clear.addEventListener('click', () => {
      if (state.rooms.length && !confirm('¿Empezar un proyecto nuevo?')) return;
      drawingPoints = [];
      selectedRoomId = '';
      activeTool = '';
      selectedPlacement = null;
      commit(emptyState({ profileId: state.profileId, systemMode: Rules.PROFILES[state.profileId].defaultMode }));
    });
    elements.print.addEventListener('click', () => window.print());
    $('ventZoomIn').addEventListener('click', () => { zoom = clamp(zoom + .12, .28, 2); applyZoom(); });
    $('ventZoomOut').addEventListener('click', () => { zoom = clamp(zoom - .12, .28, 2); applyZoom(); });
    $('ventZoomFit').addEventListener('click', fitPlan);
    window.addEventListener('resize', () => { if (window.innerWidth < 760) fitPlan(); });
    window.addEventListener('keydown', event => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') { event.preventDefault(); event.shiftKey ? redo() : undo(); }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'y') { event.preventDefault(); redo(); }
      if (event.key === 'Escape') { drawingPoints = []; activeTool = ''; selectedPlacement = null; render(); }
    });
    render();
    requestAnimationFrame(fitPlan);
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initBrowser);
    else initBrowser();
  }

  return {
    DEFAULTS,
    SYSTEM_MODES,
    normalizeState,
    emptyState,
    exampleState,
    calculateRoomDemands,
    chooseRectangularSize,
    chooseGrilleSize,
    calculateProject,
    renderPlanSvg,
  };
});
