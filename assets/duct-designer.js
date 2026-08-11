(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.STDuctDesigner = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';

  const STORAGE_KEY = 'st.ductDesigner.v2';
  const CELL_PX = 44;
  const DEFAULTS = Object.freeze({
    schemaVersion: 2,
    projectName: 'Vivienda de prueba',
    systemMode: 'climate',
    cellSizeM: .5,
    gridCols: 24,
    gridRows: 18,
    ductHeightCm: 25,
    grilleHeightCm: 15,
    machineCapacityFg: 0,
    loadPerM2: 150,
    airflowPer9000: 1200,
    areaPer9000: 900,
    grilleMultiplier: 2,
    minimumDuctWidthCm: 10,
    minimumGrilleWidthCm: 20,
  });

  const ROOM_TYPES = Object.freeze({
    bedroom: { label: 'Dormitorio', short: 'DORMITORIO', conditioned: true },
    living: { label: 'Salón / comedor', short: 'SALÓN', conditioned: true },
    kitchen: { label: 'Cocina', short: 'COCINA', conditioned: true },
    office: { label: 'Oficina / despacho', short: 'OFICINA', conditioned: true },
    bathroom: { label: 'Baño', short: 'BAÑO', conditioned: false },
    hallway: { label: 'Pasillo / distribuidor', short: 'PASILLO', conditioned: false },
    utility: { label: 'Lavadero / técnico', short: 'TÉCNICO', conditioned: false },
    other: { label: 'Otra estancia', short: 'ESTANCIA', conditioned: true },
  });

  function finite(value, fallback = 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function clamp(value, minimum, maximum) {
    return Math.min(maximum, Math.max(minimum, value));
  }

  function roundUp(value, step = 1) {
    return Math.ceil((value - 1e-9) / step) * step;
  }

  function point(value, cols, rows) {
    return {
      x: clamp(Math.round(finite(value?.x)), 0, cols),
      y: clamp(Math.round(finite(value?.y)), 0, rows),
    };
  }

  function pointKey(value) {
    return `${value.x},${value.y}`;
  }

  function edgeKey(a, b) {
    const one = pointKey(a);
    const two = pointKey(b);
    return one < two ? `${one}|${two}` : `${two}|${one}`;
  }

  function normalizeEdge(edge, cols, rows) {
    const a = point(edge?.a, cols, rows);
    const b = point(edge?.b, cols, rows);
    if (Math.abs(a.x - b.x) + Math.abs(a.y - b.y) !== 1) return null;
    return pointKey(a) < pointKey(b) ? { a, b } : { a: b, b: a };
  }

  function routeEdgesFromPoints(startValue, endValue, horizontalFirst = true) {
    const start = { x: Math.round(finite(startValue?.x)), y: Math.round(finite(startValue?.y)) };
    const end = { x: Math.round(finite(endValue?.x)), y: Math.round(finite(endValue?.y)) };
    const edges = [];
    let cursor = { ...start };
    const walk = axis => {
      const target = end[axis];
      while (cursor[axis] !== target) {
        const next = { ...cursor, [axis]: cursor[axis] + Math.sign(target - cursor[axis]) };
        edges.push({ a: { ...cursor }, b: next });
        cursor = next;
      }
    };
    if (horizontalFirst) { walk('x'); walk('y'); }
    else { walk('y'); walk('x'); }
    return edges;
  }

  function normalizeState(input = {}) {
    const gridCols = clamp(Math.round(finite(input.gridCols, DEFAULTS.gridCols)), 8, 60);
    const gridRows = clamp(Math.round(finite(input.gridRows, DEFAULTS.gridRows)), 8, 50);
    const roomIds = new Set();
    const rooms = (Array.isArray(input.rooms) ? input.rooms : []).slice(0, 80).map((room, index) => {
      const x = clamp(Math.round(finite(room?.x)), 0, gridCols - 1);
      const y = clamp(Math.round(finite(room?.y)), 0, gridRows - 1);
      const w = clamp(Math.round(finite(room?.w, 2)), 1, gridCols - x);
      const h = clamp(Math.round(finite(room?.h, 2)), 1, gridRows - y);
      let id = String(room?.id || `room-${index + 1}`).slice(0, 60);
      while (roomIds.has(id)) id = `${id}-${index + 1}`;
      roomIds.add(id);
      const type = ROOM_TYPES[room?.type] ? room.type : 'other';
      return {
        id, type, x, y, w, h,
        name: String(room?.name || ROOM_TYPES[type].label).slice(0, 35),
        conditioned: room?.conditioned === undefined ? ROOM_TYPES[type].conditioned : Boolean(room.conditioned),
        ceilingHeightM: clamp(finite(room?.ceilingHeightM, 2.5), 1.8, 8),
        occupancy: clamp(Math.round(finite(room?.occupancy, 1)), 0, 100),
        manualAreaM2: Math.max(0, finite(room?.manualAreaM2, 0)),
        manualLoadFg: Math.max(0, finite(room?.manualLoadFg, 0)),
        ventilationRole: ['supply', 'extract', 'transfer', 'none'].includes(room?.ventilationRole) ? room.ventilationRole : 'none',
      };
    });

    const edgeMap = new Map();
    (Array.isArray(input.routeEdges) ? input.routeEdges : []).forEach(raw => {
      const edge = normalizeEdge(raw, gridCols, gridRows);
      if (edge) edgeMap.set(edgeKey(edge.a, edge.b), edge);
    });
    const outlets = (Array.isArray(input.outlets) ? input.outlets : [])
      .filter(outlet => outlet && roomIds.has(String(outlet.roomId)))
      .slice(0, rooms.length)
      .map((outlet, index) => ({
        id: String(outlet.id || `outlet-${index + 1}`).slice(0, 60),
        roomId: String(outlet.roomId),
        ...point(outlet, gridCols, gridRows),
      }));
    const uniqueOutlets = new Map();
    outlets.forEach(outlet => uniqueOutlets.set(outlet.roomId, outlet));

    return {
      schemaVersion: 2,
      projectName: String(input.projectName || DEFAULTS.projectName).slice(0, 70),
      systemMode: input.systemMode === 'ventilation' ? 'ventilation' : 'climate',
      cellSizeM: [.25, .5, 1].includes(finite(input.cellSizeM)) ? finite(input.cellSizeM) : DEFAULTS.cellSizeM,
      gridCols, gridRows,
      ductHeightCm: clamp(finite(input.ductHeightCm, DEFAULTS.ductHeightCm), 10, 80),
      grilleHeightCm: clamp(finite(input.grilleHeightCm, DEFAULTS.grilleHeightCm), 8, 80),
      machineCapacityFg: Math.max(0, finite(input.machineCapacityFg, 0)),
      loadPerM2: clamp(finite(input.loadPerM2, DEFAULTS.loadPerM2), 50, 350),
      airflowPer9000: clamp(finite(input.airflowPer9000, DEFAULTS.airflowPer9000), 500, 2500),
      areaPer9000: clamp(finite(input.areaPer9000, DEFAULTS.areaPer9000), 300, 1800),
      grilleMultiplier: clamp(finite(input.grilleMultiplier, DEFAULTS.grilleMultiplier), 1, 4),
      minimumDuctWidthCm: clamp(finite(input.minimumDuctWidthCm, DEFAULTS.minimumDuctWidthCm), 5, 40),
      minimumGrilleWidthCm: clamp(finite(input.minimumGrilleWidthCm, DEFAULTS.minimumGrilleWidthCm), 10, 60),
      rooms,
      machine: input.machine ? point(input.machine, gridCols, gridRows) : null,
      routeEdges: [...edgeMap.values()],
      outlets: [...uniqueOutlets.values()],
    };
  }

  function emptyState() {
    return normalizeState({ ...DEFAULTS, rooms: [], machine: null, routeEdges: [], outlets: [] });
  }

  function exampleState() {
    const paths = [
      [{ x: 9, y: 9 }, { x: 9, y: 6 }, { x: 6, y: 6 }],
      [{ x: 9, y: 6 }, { x: 18, y: 6 }],
      [{ x: 9, y: 9 }, { x: 14, y: 9 }],
    ];
    const routeEdges = [];
    paths.forEach(path => path.slice(1).forEach((end, index) => routeEdges.push(...routeEdgesFromPoints(path[index], end))));
    return normalizeState({
      ...DEFAULTS,
      rooms: [
        { id: 'bed-1', type: 'bedroom', name: 'Dormitorio principal', x: 1, y: 1, w: 7, h: 6, conditioned: true, ceilingHeightM: 2.5, occupancy: 2 },
        { id: 'bed-2', type: 'bedroom', name: 'Dormitorio 2', x: 8, y: 1, w: 7, h: 6, conditioned: true, ceilingHeightM: 2.5, occupancy: 1 },
        { id: 'kitchen', type: 'kitchen', name: 'Cocina', x: 15, y: 1, w: 8, h: 6, conditioned: true, ceilingHeightM: 2.5, occupancy: 2 },
        { id: 'bath', type: 'bathroom', name: 'Baño', x: 1, y: 7, w: 6, h: 5, conditioned: false, ceilingHeightM: 2.5, occupancy: 1, ventilationRole: 'extract' },
        { id: 'hall', type: 'hallway', name: 'Pasillo', x: 7, y: 7, w: 4, h: 10, conditioned: false, ceilingHeightM: 2.5, occupancy: 0, ventilationRole: 'transfer' },
        { id: 'living', type: 'living', name: 'Salón comedor', x: 11, y: 7, w: 12, h: 10, conditioned: true, ceilingHeightM: 2.6, occupancy: 4 },
      ],
      machine: { x: 9, y: 9 },
      routeEdges,
      outlets: [
        { id: 'out-bed-1', roomId: 'bed-1', x: 6, y: 6 },
        { id: 'out-bed-2', roomId: 'bed-2', x: 11, y: 6 },
        { id: 'out-kitchen', roomId: 'kitchen', x: 18, y: 6 },
        { id: 'out-living', roomId: 'living', x: 14, y: 9 },
      ],
    });
  }

  function airflowForLoad(loadFg, state) {
    return loadFg * state.airflowPer9000 / 9000;
  }

  function areaForLoad(loadFg, state) {
    return loadFg * state.areaPer9000 / 9000;
  }

  function sizeDuct(loadFg, input = {}) {
    const state = normalizeState(input);
    const requiredAreaCm2 = areaForLoad(loadFg, state);
    const rawWidthCm = requiredAreaCm2 / state.ductHeightCm;
    const widthCm = loadFg > 0 ? roundUp(Math.max(state.minimumDuctWidthCm, rawWidthCm), 1) : 0;
    const actualAreaM2 = widthCm * state.ductHeightCm / 10000;
    const airflowM3h = airflowForLoad(loadFg, state);
    const velocityMps = actualAreaM2 > 0 ? airflowM3h / (actualAreaM2 * 3600) : 0;
    return { widthCm, heightCm: state.ductHeightCm, requiredAreaCm2, airflowM3h, velocityMps };
  }

  function enrichRoom(room, state) {
    const geometricAreaM2 = room.w * state.cellSizeM * room.h * state.cellSizeM;
    const areaM2 = room.manualAreaM2 > 0 ? room.manualAreaM2 : geometricAreaM2;
    const loadFg = room.conditioned ? (room.manualLoadFg > 0 ? room.manualLoadFg : areaM2 * state.loadPerM2) : 0;
    const airflowM3h = airflowForLoad(loadFg, state);
    const branchDuct = sizeDuct(loadFg, state);
    const grilleAreaCm2 = branchDuct.requiredAreaCm2 * state.grilleMultiplier;
    const grilleWidthCm = loadFg > 0 ? roundUp(Math.max(state.minimumGrilleWidthCm, grilleAreaCm2 / state.grilleHeightCm), 5) : 0;
    return {
      ...room,
      typeLabel: ROOM_TYPES[room.type].label,
      geometricAreaM2,
      areaM2,
      volumeM3: areaM2 * room.ceilingHeightM,
      loadFg,
      airflowM3h,
      branchDuct,
      grille: { widthCm: grilleWidthCm, heightCm: state.grilleHeightCm },
      source: room.manualLoadFg > 0 ? 'manual-load' : room.manualAreaM2 > 0 ? 'manual-area' : 'plan',
    };
  }

  function buildGraph(edges) {
    const graph = new Map();
    const add = (from, to) => {
      if (!graph.has(from)) graph.set(from, []);
      graph.get(from).push(to);
    };
    edges.forEach(edge => {
      const a = pointKey(edge.a);
      const b = pointKey(edge.b);
      add(a, b);
      add(b, a);
    });
    return graph;
  }

  function shortestPath(graph, start, end) {
    if (start === end) return [start];
    if (!graph.has(start) || !graph.has(end)) return null;
    const queue = [start];
    const previous = new Map([[start, null]]);
    for (let index = 0; index < queue.length; index += 1) {
      const current = queue[index];
      for (const next of graph.get(current) || []) {
        if (previous.has(next)) continue;
        previous.set(next, current);
        if (next === end) {
          const path = [end];
          let cursor = current;
          while (cursor !== null) { path.push(cursor); cursor = previous.get(cursor); }
          return path.reverse();
        }
        queue.push(next);
      }
    }
    return null;
  }

  function roomOverlap(one, two) {
    return one.x < two.x + two.w && one.x + one.w > two.x && one.y < two.y + two.h && one.y + one.h > two.y;
  }

  function connectedComponents(edges) {
    const remaining = new Map(edges.map(edge => [edge.key, edge]));
    const components = [];
    while (remaining.size) {
      const first = remaining.values().next().value;
      remaining.delete(first.key);
      const component = [first];
      const nodes = new Set([pointKey(first.a), pointKey(first.b)]);
      let changed = true;
      while (changed) {
        changed = false;
        for (const [key, edge] of [...remaining.entries()]) {
          if (nodes.has(pointKey(edge.a)) || nodes.has(pointKey(edge.b))) {
            component.push(edge);
            nodes.add(pointKey(edge.a));
            nodes.add(pointKey(edge.b));
            remaining.delete(key);
            changed = true;
          }
        }
      }
      components.push(component);
    }
    return components;
  }

  function calculateProject(input = {}) {
    const state = normalizeState(input);
    const rooms = state.rooms.map(room => enrichRoom(room, state));
    const roomMap = new Map(rooms.map(room => [room.id, room]));
    const outletMap = new Map(state.outlets.map(outlet => [outlet.roomId, outlet]));
    const graph = buildGraph(state.routeEdges);
    const machineKey = state.machine ? pointKey(state.machine) : '';
    const assignments = new Map();
    const roomConnections = new Map();

    rooms.filter(room => room.conditioned).forEach(room => {
      const outlet = outletMap.get(room.id);
      const path = state.machine && outlet ? shortestPath(graph, machineKey, pointKey(outlet)) : null;
      const connected = Boolean(path);
      roomConnections.set(room.id, { connected, path: path || [], outlet: outlet || null });
      if (!path) return;
      for (let index = 1; index < path.length; index += 1) {
        const key = path[index - 1] < path[index] ? `${path[index - 1]}|${path[index]}` : `${path[index]}|${path[index - 1]}`;
        if (!assignments.has(key)) assignments.set(key, new Set());
        assignments.get(key).add(room.id);
      }
    });

    const activeEdges = state.routeEdges.map(edge => {
      const key = edgeKey(edge.a, edge.b);
      const roomIds = [...(assignments.get(key) || [])].sort();
      const loadFg = roomIds.reduce((sum, id) => sum + (roomMap.get(id)?.loadFg || 0), 0);
      return { ...edge, key, roomIds, loadFg, ...sizeDuct(loadFg, state) };
    });

    const buckets = new Map();
    activeEdges.filter(edge => edge.loadFg > 0).forEach(edge => {
      const signature = edge.roomIds.join('|');
      if (!buckets.has(signature)) buckets.set(signature, []);
      buckets.get(signature).push(edge);
    });
    const sections = [];
    buckets.forEach(edges => connectedComponents(edges).forEach(component => {
      const sample = component[Math.floor(component.length / 2)];
      const roomIds = sample.roomIds;
      const loadFg = roomIds.reduce((sum, id) => sum + (roomMap.get(id)?.loadFg || 0), 0);
      sections.push({
        id: '', roomIds, rooms: roomIds.map(id => roomMap.get(id)).filter(Boolean),
        edges: component, representative: sample,
        lengthM: component.length * state.cellSizeM,
        loadFg,
        ...sizeDuct(loadFg, state),
      });
    }));
    sections.sort((a, b) => b.loadFg - a.loadFg || b.lengthM - a.lengthM).forEach((section, index) => { section.id = `T${index + 1}`; });
    const sectionByEdge = new Map();
    sections.forEach(section => section.edges.forEach(edge => sectionByEdge.set(edge.key, section)));
    activeEdges.forEach(edge => { edge.sectionId = sectionByEdge.get(edge.key)?.id || ''; });

    const conditionedRooms = rooms.filter(room => room.conditioned);
    const connectedRooms = conditionedRooms.filter(room => roomConnections.get(room.id)?.connected);
    const loadFg = conditionedRooms.reduce((sum, room) => sum + room.loadFg, 0);
    const connectedLoadFg = connectedRooms.reduce((sum, room) => sum + room.loadFg, 0);
    const airflowM3h = conditionedRooms.reduce((sum, room) => sum + room.airflowM3h, 0);
    const warnings = [];
    if (!rooms.length) warnings.push({ level: 'info', text: 'Dibuja al menos una estancia para comenzar el proyecto.' });
    if (rooms.some((room, index) => rooms.slice(index + 1).some(other => roomOverlap(room, other)))) warnings.push({ level: 'danger', text: 'Hay estancias superpuestas. Corrige el plano antes de continuar.' });
    if (conditionedRooms.length && !state.machine) warnings.push({ level: 'warn', text: 'Falta colocar la unidad interior en el plano.' });
    if (state.machine && conditionedRooms.length && !state.routeEdges.length) warnings.push({ level: 'warn', text: 'Marca el recorrido de los conductos desde la unidad interior.' });
    conditionedRooms.forEach(room => {
      const connection = roomConnections.get(room.id);
      if (!connection?.outlet) warnings.push({ level: 'warn', text: `${room.name}: falta colocar la rejilla.` });
      else if (!connection.connected) warnings.push({ level: 'warn', text: `${room.name}: la rejilla no está unida a la máquina por el recorrido dibujado.` });
      if (room.grille.widthCm > 120) warnings.push({ level: 'warn', text: `${room.name}: conviene repartir el caudal entre dos salidas.` });
    });
    if (state.machineCapacityFg > 0 && state.machineCapacityFg < loadFg) warnings.push({ level: 'danger', text: `La máquina indicada queda aproximadamente ${formatNumber(loadFg - state.machineCapacityFg)} frg/h por debajo de la demanda estimada.` });
    sections.forEach(section => {
      if (section.velocityMps > 5.2) warnings.push({ level: 'warn', text: `${section.id}: velocidad elevada (${formatNumber(section.velocityMps, 1)} m/s).` });
      if (section.velocityMps > 0 && section.velocityMps < 1.6) warnings.push({ level: 'info', text: `${section.id}: velocidad baja (${formatNumber(section.velocityMps, 1)} m/s).` });
    });
    if (conditionedRooms.length && connectedRooms.length === conditionedRooms.length) warnings.unshift({ level: 'ok', text: 'Todas las estancias climatizadas están conectadas a la red.' });

    return {
      state, rooms, roomMap, outletMap, roomConnections, activeEdges, sections,
      totals: {
        rooms: rooms.length,
        conditionedRooms: conditionedRooms.length,
        connectedRooms: connectedRooms.length,
        areaM2: rooms.reduce((sum, room) => sum + room.areaM2, 0),
        conditionedAreaM2: conditionedRooms.reduce((sum, room) => sum + room.areaM2, 0),
        loadFg, connectedLoadFg, airflowM3h,
        suggestedCapacityFg: loadFg > 0 ? roundUp(loadFg, 500) : 0,
        mainDuct: sizeDuct(loadFg, state),
      },
      warnings: uniqueWarnings(warnings),
    };
  }

  function uniqueWarnings(warnings) {
    const seen = new Set();
    return warnings.filter(item => !seen.has(item.text) && seen.add(item.text));
  }

  function formatNumber(value, decimals = 0) {
    return finite(value).toLocaleString('es-ES', { maximumFractionDigits: decimals, minimumFractionDigits: decimals });
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));
  }

  function renderPlanSvg(result, options = {}) {
    const { state } = result;
    const width = state.gridCols * CELL_PX;
    const height = state.gridRows * CELL_PX;
    const selected = options.selected || {};
    const px = value => value * CELL_PX;
    const parts = [`<svg class="installation-plan" viewBox="0 0 ${width} ${height}" role="img" aria-label="Plano interactivo de ${escapeHtml(state.projectName)}">`,
      `<defs><pattern id="minorGrid" width="${CELL_PX}" height="${CELL_PX}" patternUnits="userSpaceOnUse"><path d="M ${CELL_PX} 0 L 0 0 0 ${CELL_PX}"/></pattern><filter id="planGlow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter><pattern id="notConditioned" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="12"/></pattern></defs>`,
      `<rect class="plan-background" width="${width}" height="${height}"/><rect class="plan-grid" width="${width}" height="${height}"/>`];

    result.rooms.forEach(room => {
      const x = px(room.x), y = px(room.y), w = px(room.w), h = px(room.h);
      const centerX = x + w / 2, centerY = y + h / 2;
      const selectedClass = selected.kind === 'room' && selected.id === room.id ? ' is-selected' : '';
      const small = w < 190 || h < 130;
      parts.push(`<g class="plan-room room-type-${room.type}${room.conditioned ? ' is-conditioned' : ' is-unconditioned'}${selectedClass}" data-kind="room" data-id="${escapeHtml(room.id)}" tabindex="0"><rect class="room-fill" x="${x + 2}" y="${y + 2}" width="${Math.max(1, w - 4)}" height="${Math.max(1, h - 4)}" rx="5"/><rect class="room-wall" x="${x + 2}" y="${y + 2}" width="${Math.max(1, w - 4)}" height="${Math.max(1, h - 4)}" rx="5"/>${room.conditioned ? '' : `<rect class="room-hatch" x="${x + 5}" y="${y + 5}" width="${Math.max(1, w - 10)}" height="${Math.max(1, h - 10)}"/>`}<text class="room-type-label" x="${centerX}" y="${centerY - (small ? 10 : 25)}" text-anchor="middle">${escapeHtml(ROOM_TYPES[room.type].short)}</text><text class="room-name-label" x="${centerX}" y="${centerY + (small ? 9 : 2)}" text-anchor="middle">${escapeHtml(room.name)}</text><text class="room-area-label" x="${centerX}" y="${centerY + (small ? 27 : 25)}" text-anchor="middle">${formatNumber(room.areaM2, 1)} m²${room.conditioned ? ` · ${formatNumber(room.loadFg)} frg/h` : ' · NO CLIMATIZADA'}</text>${small ? '' : `<text class="room-dimension-label" x="${centerX}" y="${y + h - 12}" text-anchor="middle">${formatNumber(room.w * state.cellSizeM, 2)} × ${formatNumber(room.h * state.cellSizeM, 2)} m</text>`}</g>`);
    });

    result.activeEdges.forEach(edge => {
      const section = result.sections.find(item => item.id === edge.sectionId);
      const active = edge.loadFg > 0;
      const widthPx = active ? clamp(7 + edge.widthCm * .28, 9, 24) : 6;
      const selectedClass = selected.kind === 'section' && selected.id === edge.sectionId ? ' is-selected' : '';
      parts.push(`<line class="route-edge${active ? ' is-active' : ' is-pending'}${selectedClass}" data-kind="edge" data-edge="${edge.key}" data-section-id="${edge.sectionId}" x1="${px(edge.a.x)}" y1="${px(edge.a.y)}" x2="${px(edge.b.x)}" y2="${px(edge.b.y)}" style="--route-width:${widthPx}px"><title>${section ? `${section.id}: ${section.widthCm} × ${section.heightCm} cm` : 'Recorrido sin carga'}</title></line>`);
    });

    result.sections.forEach(section => {
      const edge = section.representative;
      const x = px((edge.a.x + edge.b.x) / 2);
      const y = px((edge.a.y + edge.b.y) / 2);
      parts.push(`<g class="section-label" data-kind="section" data-id="${section.id}"><rect x="${x - 52}" y="${y - 15}" width="104" height="30" rx="8"/><text x="${x}" y="${y + 5}" text-anchor="middle">${section.id} · ${section.widthCm}×${section.heightCm}</text></g>`);
    });

    result.rooms.forEach(room => {
      const outlet = result.outletMap.get(room.id);
      if (!outlet) return;
      const connected = result.roomConnections.get(room.id)?.connected;
      const selectedClass = selected.kind === 'outlet' && selected.id === outlet.id ? ' is-selected' : '';
      parts.push(`<g class="plan-outlet${connected ? ' is-connected' : ' is-disconnected'}${selectedClass}" data-kind="outlet" data-id="${escapeHtml(outlet.id)}" data-room-id="${escapeHtml(room.id)}" tabindex="0" transform="translate(${px(outlet.x)} ${px(outlet.y)})"><rect x="-22" y="-8" width="44" height="16" rx="4"/><path d="M-15-3h30M-15 2h30"/><title>${escapeHtml(room.name)} · rejilla ${room.grille.widthCm} × ${room.grille.heightCm} cm</title></g>`);
    });

    if (state.machine) {
      const selectedClass = selected.kind === 'machine' ? ' is-selected' : '';
      parts.push(`<g class="plan-machine${selectedClass}" data-kind="machine" tabindex="0" transform="translate(${px(state.machine.x)} ${px(state.machine.y)})"><rect x="-35" y="-27" width="70" height="54" rx="12"/><circle cx="0" cy="0" r="15"/><path d="M0-15c9 3 11 8 5 14M15 0c-3 9-8 11-14 5M0 15c-9-3-11-8-5-14M-15 0c3-9 8-11 14-5"/><text x="0" y="-37" text-anchor="middle">UNIDAD INTERIOR</text></g>`);
    }

    if (options.roomStart) parts.push(`<g class="drawing-anchor"><circle cx="${px(options.roomStart.x)}" cy="${px(options.roomStart.y)}" r="12"/><text x="${px(options.roomStart.x) + 18}" y="${px(options.roomStart.y) - 16}">Primera esquina</text></g>`);
    if (options.routeAnchor) parts.push(`<g class="drawing-anchor route-anchor"><circle cx="${px(options.routeAnchor.x)}" cy="${px(options.routeAnchor.y)}" r="12"/><text x="${px(options.routeAnchor.x) + 18}" y="${px(options.routeAnchor.y) - 16}">Continúa el recorrido</text></g>`);
    parts.push(`<g class="scale-marker" transform="translate(${width - 150} ${height - 25})"><line x1="0" y1="0" x2="${CELL_PX * 2}" y2="0"/><path d="M0-6v12M${CELL_PX * 2}-6v12"/><text x="${CELL_PX}" y="-10" text-anchor="middle">${formatNumber(state.cellSizeM * 2, 2)} m</text></g>`);
    parts.push('</svg>');
    return { svg: parts.join(''), width, height };
  }

  function initBrowser() {
    if (typeof document === 'undefined' || !document.getElementById('planStage')) return;
    const $ = id => document.getElementById(id);
    const elements = {
      projectName: $('projectName'), cellSize: $('cellSize'), planWidth: $('planWidth'), planHeight: $('planHeight'), machineCapacity: $('machineCapacity'),
      ductHeight: $('ductHeight'), grilleHeight: $('grilleHeight'), loadPerM2: $('loadPerM2'), airflowPer9000: $('airflowPer9000'), areaPer9000: $('areaPer9000'), grilleMultiplier: $('grilleMultiplier'),
      saveState: $('saveState'), planProjectName: $('planProjectName'), activeToolLabel: $('activeToolLabel'), planScroll: $('planScroll'), planStage: $('planStage'),
      drawingMessage: $('drawingMessage'), finishRoute: $('finishRoute'), selectionPanel: $('selectionPanel'), resultStatus: $('resultStatus'), resultSummary: $('resultSummary'), alerts: $('ductAlerts'),
      roomCount: $('roomCount'), roomList: $('roomOverviewList'), networkResults: $('networkResults'), roomDialog: $('roomDialog'), roomForm: $('roomForm'), roomId: $('roomId'), roomType: $('roomType'), roomName: $('roomName'), roomConditioned: $('roomConditioned'), roomCeiling: $('roomCeiling'), roomOccupancy: $('roomOccupancy'), roomManualArea: $('roomManualArea'), roomManualLoad: $('roomManualLoad'), roomGeometrySummary: $('roomGeometrySummary'),
    };
    const toolLabels = { select: 'Seleccionar', room: 'Dibujar estancia', machine: 'Colocar máquina', duct: 'Trazar conducto', outlet: 'Colocar rejilla', erase: 'Borrar elemento' };
    let state = loadState();
    let result = calculateProject(state);
    let tool = 'select';
    let selected = { kind: 'project' };
    let roomStart = null;
    let routeAnchor = null;
    let draftRect = null;
    let zoom = 1;
    const history = [];
    const future = [];

    function loadState() {
      try {
        const saved = localStorage.getItem(STORAGE_KEY);
        return saved ? normalizeState(JSON.parse(saved)) : exampleState();
      } catch (_) {
        return exampleState();
      }
    }

    function saveState() {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        elements.saveState.textContent = 'Guardado';
        elements.saveState.classList.add('is-saved');
        setTimeout(() => elements.saveState.classList.remove('is-saved'), 500);
      } catch (_) {
        elements.saveState.textContent = 'Sin guardar';
      }
    }

    function snapshot(value) {
      return JSON.stringify(value);
    }

    function commit(next, nextSelection = selected) {
      history.push(snapshot(state));
      if (history.length > 60) history.shift();
      future.length = 0;
      state = normalizeState(next);
      selected = nextSelection;
      render();
    }

    function replace(next) {
      state = normalizeState(next);
      render();
    }

    function undo() {
      if (!history.length) return;
      future.push(snapshot(state));
      state = normalizeState(JSON.parse(history.pop()));
      selected = { kind: 'project' };
      roomStart = routeAnchor = null;
      render();
    }

    function redo() {
      if (!future.length) return;
      history.push(snapshot(state));
      state = normalizeState(JSON.parse(future.pop()));
      selected = { kind: 'project' };
      render();
    }

    function syncProjectInputs() {
      elements.projectName.value = state.projectName;
      elements.cellSize.value = String(state.cellSizeM);
      elements.planWidth.value = formatNumber(state.gridCols * state.cellSizeM, 2).replace(',', '.');
      elements.planHeight.value = formatNumber(state.gridRows * state.cellSizeM, 2).replace(',', '.');
      elements.machineCapacity.value = state.machineCapacityFg || '';
      elements.ductHeight.value = state.ductHeightCm;
      elements.grilleHeight.value = state.grilleHeightCm;
      elements.loadPerM2.value = state.loadPerM2;
      elements.airflowPer9000.value = state.airflowPer9000;
      elements.areaPer9000.value = state.areaPer9000;
      elements.grilleMultiplier.value = state.grilleMultiplier;
    }

    function updateProjectSettings() {
      const cellSizeM = finite(elements.cellSize.value, state.cellSizeM);
      const usedX = Math.max(8, state.machine?.x || 0, ...state.rooms.map(room => room.x + room.w), ...state.outlets.map(item => item.x), ...state.routeEdges.flatMap(edge => [edge.a.x, edge.b.x]));
      const usedY = Math.max(8, state.machine?.y || 0, ...state.rooms.map(room => room.y + room.h), ...state.outlets.map(item => item.y), ...state.routeEdges.flatMap(edge => [edge.a.y, edge.b.y]));
      const gridCols = Math.max(usedX, Math.round(clamp(finite(elements.planWidth.value, state.gridCols * cellSizeM), 4, 30) / cellSizeM));
      const gridRows = Math.max(usedY, Math.round(clamp(finite(elements.planHeight.value, state.gridRows * cellSizeM), 4, 25) / cellSizeM));
      replace({ ...state, projectName: elements.projectName.value, cellSizeM, gridCols, gridRows, machineCapacityFg: elements.machineCapacity.value, ductHeightCm: elements.ductHeight.value, grilleHeightCm: elements.grilleHeight.value, loadPerM2: elements.loadPerM2.value, airflowPer9000: elements.airflowPer9000.value, areaPer9000: elements.areaPer9000.value, grilleMultiplier: elements.grilleMultiplier.value });
    }

    function setTool(nextTool) {
      tool = nextTool;
      roomStart = null;
      if (tool !== 'duct') routeAnchor = null;
      document.querySelectorAll('[data-tool]').forEach(button => button.classList.toggle('is-active', button.dataset.tool === tool));
      elements.activeToolLabel.textContent = toolLabels[tool];
      elements.finishRoute.hidden = tool !== 'duct' || !routeAnchor;
      const messages = {
        select: 'Toca una estancia, rejilla, máquina o tramo para consultar y editar.',
        room: 'Toca la primera esquina de la estancia y después la esquina opuesta.',
        machine: 'Toca el punto del plano donde irá la unidad interior.',
        duct: 'Empieza en la máquina o en un conducto existente y marca los cambios de dirección.',
        outlet: 'Toca dentro de una estancia climatizada para colocar su rejilla.',
        erase: 'Toca el elemento que quieras retirar del plano.',
      };
      elements.drawingMessage.querySelector('p').textContent = messages[tool];
      renderPlan();
    }

    function renderPlan() {
      const rendered = renderPlanSvg(result, { selected, roomStart, routeAnchor });
      elements.planStage.innerHTML = rendered.svg;
      elements.planStage.dataset.width = rendered.width;
      elements.planStage.dataset.height = rendered.height;
      applyZoom();
    }

    function applyZoom() {
      const svg = elements.planStage.querySelector('svg');
      if (!svg) return;
      const width = finite(elements.planStage.dataset.width, 900);
      svg.style.width = `${Math.max(520, width * zoom)}px`;
      svg.style.maxWidth = 'none';
    }

    function fitPlan() {
      const width = finite(elements.planStage.dataset.width, 900);
      const available = Math.max(300, elements.planScroll.clientWidth - 12);
      zoom = clamp(available / width, .35, 1.35);
      applyZoom();
      requestAnimationFrame(() => {
        elements.planScroll.scrollLeft = Math.max(0, (elements.planScroll.scrollWidth - elements.planScroll.clientWidth) / 2);
      });
    }

    function summaryMetric(label, value, note, tone) {
      return `<article class="summary-metric metric-${tone}"><span>${label}</span><strong>${value}</strong><small>${note}</small></article>`;
    }

    function renderSummary() {
      const totals = result.totals;
      const machine = state.machineCapacityFg || totals.suggestedCapacityFg;
      elements.resultSummary.innerHTML = [
        summaryMetric('Superficie climatizada', `${formatNumber(totals.conditionedAreaM2, 1)} m²`, `${totals.conditionedRooms} de ${totals.rooms} estancias`, 'blue'),
        summaryMetric(state.machineCapacityFg ? 'Máquina indicada' : 'Máquina orientativa', `${formatNumber(machine)} frg/h`, `${formatNumber(totals.loadFg)} frg/h estimadas`, 'orange'),
        summaryMetric('Caudal total', `${formatNumber(totals.airflowM3h)} m³/h`, `${totals.connectedRooms}/${totals.conditionedRooms} estancias conectadas`, 'green'),
        summaryMetric('Conducto principal', totals.loadFg ? `${totals.mainDuct.widthCm} × ${totals.mainDuct.heightCm} cm` : '—', totals.loadFg ? `${formatNumber(totals.mainDuct.velocityMps, 1)} m/s` : 'Pendiente del plano', 'pink'),
      ].join('');
      const complete = totals.conditionedRooms > 0 && totals.connectedRooms === totals.conditionedRooms && state.machine;
      elements.resultStatus.textContent = complete ? 'RED CONECTADA' : totals.rooms ? 'EN PROCESO' : 'PLANO VACÍO';
      elements.resultStatus.className = `result-status${complete ? ' is-ready' : ''}`;
    }

    function renderAlerts() {
      elements.alerts.innerHTML = result.warnings.slice(0, 8).map(item => `<p class="duct-alert alert-${item.level}"><span>${item.level === 'ok' ? '✓' : item.level === 'danger' ? '!' : item.level === 'warn' ? '△' : 'i'}</span>${escapeHtml(item.text)}</p>`).join('');
    }

    function renderRoomList() {
      elements.roomCount.textContent = result.rooms.length;
      elements.roomList.innerHTML = result.rooms.length ? result.rooms.map(room => {
        const connection = result.roomConnections.get(room.id);
        const stateLabel = !room.conditioned ? 'No climatizada' : connection?.connected ? 'Conectada' : connection?.outlet ? 'Sin unir' : 'Sin rejilla';
        return `<button class="overview-room${room.conditioned ? '' : ' is-off'}" data-overview-room="${escapeHtml(room.id)}" type="button"><i class="room-dot room-type-${room.type}"></i><span><strong>${escapeHtml(room.name)}</strong><small>${formatNumber(room.areaM2, 1)} m² · ${stateLabel}</small></span><b>${room.conditioned ? `${formatNumber(room.loadFg)} frg/h` : '—'}</b></button>`;
      }).join('') : '<p class="empty-list">Todavía no has dibujado estancias.</p>';
    }

    function renderNetworkResults() {
      if (!result.sections.length) {
        elements.networkResults.innerHTML = '<div class="network-empty"><strong>La tabla aparecerá al conectar las rejillas</strong><p>Dibuja el recorrido desde la máquina y asegúrate de que pasa por cada rejilla.</p></div>';
        return;
      }
      const sections = result.sections.map(section => `<button class="network-row" type="button" data-network-section="${section.id}"><span class="network-id">${section.id}</span><span class="network-destination"><strong>${section.rooms.map(room => escapeHtml(room.name)).join(' · ')}</strong><small>${formatNumber(section.lengthM, 1)} m dibujados · ${formatNumber(section.airflowM3h)} m³/h</small></span><span class="network-size"><strong>${section.widthCm} × ${section.heightCm} cm</strong><small>${formatNumber(section.velocityMps, 1)} m/s</small></span></button>`).join('');
      const outlets = result.rooms.filter(room => room.conditioned).map(room => {
        const connected = result.roomConnections.get(room.id)?.connected;
        return `<div class="network-row outlet-result${connected ? '' : ' is-pending'}"><span class="network-id">▥</span><span class="network-destination"><strong>${escapeHtml(room.name)}</strong><small>${formatNumber(room.airflowM3h)} m³/h · ramal ${room.branchDuct.widthCm} × ${room.branchDuct.heightCm} cm</small></span><span class="network-size"><strong>${room.grille.widthCm} × ${room.grille.heightCm} cm</strong><small>${connected ? 'Rejilla conectada' : 'Pendiente de conexión'}</small></span></div>`;
      }).join('');
      elements.networkResults.innerHTML = `<article><header><strong>Tramos de la red</strong><span>Desde mayor a menor caudal</span></header>${sections}</article><article><header><strong>Salidas por estancia</strong><span>Ramal y rejilla recomendados</span></header>${outlets}</article>`;
    }

    function renderWorkflow() {
      const conditioned = result.totals.conditionedRooms;
      const states = [
        [$('workflowRooms'), result.totals.rooms > 0],
        [$('workflowMachine'), Boolean(state.machine)],
        [$('workflowRoute'), state.routeEdges.length > 0],
        [$('workflowOutlets'), conditioned > 0 && state.outlets.length >= conditioned],
        [$('workflowReview'), conditioned > 0 && result.totals.connectedRooms === conditioned],
      ];
      let currentFound = false;
      states.forEach(([element, complete]) => {
        element.classList.toggle('is-complete', complete);
        element.classList.remove('is-current');
        if (!complete && !currentFound) { element.classList.add('is-current'); currentFound = true; }
      });
      if (!currentFound) states.at(-1)[0].classList.add('is-current');
    }

    function renderInspector() {
      if (selected.kind === 'room') {
        const room = result.roomMap.get(selected.id);
        if (!room) { selected = { kind: 'project' }; return renderInspector(); }
        const connection = result.roomConnections.get(room.id);
        elements.selectionPanel.innerHTML = `<div class="selection-copy"><p class="duct-eyebrow">ESTANCIA SELECCIONADA</p><h3>${escapeHtml(room.name)}</h3><p>${room.typeLabel} · ${formatNumber(room.w * state.cellSizeM, 2)} × ${formatNumber(room.h * state.cellSizeM, 2)} m · volumen ${formatNumber(room.volumeM3, 1)} m³</p></div><div class="selection-values"><span><b>${formatNumber(room.areaM2, 1)} m²</b> superficie</span><span><b>${room.conditioned ? `${formatNumber(room.loadFg)} frg/h` : 'No'}</b> climatización</span><span><b>${connection?.connected ? 'Conectada' : connection?.outlet ? 'Sin unir' : 'Sin rejilla'}</b> salida</span></div><div class="selection-actions"><button data-selection-action="up" type="button">↑</button><button data-selection-action="left" type="button">←</button><button data-selection-action="right" type="button">→</button><button data-selection-action="down" type="button">↓</button><button data-selection-action="edit" type="button">Editar datos</button><button data-selection-action="delete" class="danger-action" type="button">Eliminar</button></div>`;
        return;
      }
      if (selected.kind === 'section') {
        const section = result.sections.find(item => item.id === selected.id);
        if (section) {
          elements.selectionPanel.innerHTML = `<div class="selection-copy"><p class="duct-eyebrow">TRAMO ${section.id}</p><h3>${section.widthCm} × ${section.heightCm} cm</h3><p>Alimenta ${section.rooms.map(room => escapeHtml(room.name)).join(', ')}.</p></div><div class="selection-values"><span><b>${formatNumber(section.airflowM3h)} m³/h</b> caudal</span><span><b>${formatNumber(section.velocityMps, 1)} m/s</b> velocidad</span><span><b>${formatNumber(section.lengthM, 1)} m</b> longitud dibujada</span></div>`;
          return;
        }
      }
      if (selected.kind === 'machine') {
        elements.selectionPanel.innerHTML = `<div class="selection-copy"><p class="duct-eyebrow">UNIDAD INTERIOR</p><h3>${state.machineCapacityFg ? `${formatNumber(state.machineCapacityFg)} frg/h indicadas` : `${formatNumber(result.totals.suggestedCapacityFg)} frg/h orientativas`}</h3><p>Origen de todos los recorridos de impulsión.</p></div><div class="selection-actions"><button data-selection-action="delete-machine" class="danger-action" type="button">Retirar máquina</button></div>`;
        return;
      }
      if (selected.kind === 'outlet') {
        const outlet = state.outlets.find(item => item.id === selected.id);
        const room = outlet ? result.roomMap.get(outlet.roomId) : null;
        if (room) {
          elements.selectionPanel.innerHTML = `<div class="selection-copy"><p class="duct-eyebrow">REJILLA DE ${escapeHtml(room.name)}</p><h3>${room.grille.widthCm} × ${room.grille.heightCm} cm</h3><p>Ramal ${room.branchDuct.widthCm} × ${room.branchDuct.heightCm} cm · ${formatNumber(room.airflowM3h)} m³/h.</p></div><div class="selection-actions"><button data-selection-action="delete-outlet" class="danger-action" type="button">Retirar rejilla</button></div>`;
          return;
        }
      }
      elements.selectionPanel.innerHTML = `<div class="selection-copy"><p class="duct-eyebrow">AYUDA DEL PLANO</p><h3>${toolLabels[tool]}</h3><p>${elements.drawingMessage.querySelector('p').textContent}</p></div><div class="selection-values"><span><b>${formatNumber(state.gridCols * state.cellSizeM, 1)} × ${formatNumber(state.gridRows * state.cellSizeM, 1)} m</b> área de trabajo</span><span><b>${formatNumber(state.cellSizeM, 2)} m</b> cada cuadrado</span></div>`;
    }

    function render() {
      result = calculateProject(state);
      elements.planProjectName.textContent = state.projectName || 'Proyecto sin nombre';
      syncProjectInputs();
      renderPlan();
      renderSummary();
      renderAlerts();
      renderRoomList();
      renderNetworkResults();
      renderWorkflow();
      renderInspector();
      $('undoProject').disabled = !history.length;
      $('redoProject').disabled = !future.length;
      elements.finishRoute.hidden = tool !== 'duct' || !routeAnchor;
      saveState();
    }

    function pointerPoint(event) {
      const svg = elements.planStage.querySelector('svg');
      if (!svg) return { x: 0, y: 0 };
      const svgPoint = svg.createSVGPoint();
      svgPoint.x = event.clientX;
      svgPoint.y = event.clientY;
      const local = svgPoint.matrixTransform(svg.getScreenCTM().inverse());
      return point({ x: local.x / CELL_PX, y: local.y / CELL_PX }, state.gridCols, state.gridRows);
    }

    function roomAt(position) {
      return result.rooms.slice().reverse().find(room => position.x >= room.x && position.x <= room.x + room.w && position.y >= room.y && position.y <= room.y + room.h);
    }

    function distanceToEdge(position, edge) {
      if (edge.a.x === edge.b.x) return Math.abs(position.x - edge.a.x) + (position.y < Math.min(edge.a.y, edge.b.y) ? Math.min(edge.a.y, edge.b.y) - position.y : position.y > Math.max(edge.a.y, edge.b.y) ? position.y - Math.max(edge.a.y, edge.b.y) : 0);
      return Math.abs(position.y - edge.a.y) + (position.x < Math.min(edge.a.x, edge.b.x) ? Math.min(edge.a.x, edge.b.x) - position.x : position.x > Math.max(edge.a.x, edge.b.x) ? position.x - Math.max(edge.a.x, edge.b.x) : 0);
    }

    function nearestEdge(position) {
      return state.routeEdges.map(edge => ({ edge, distance: distanceToEdge(position, edge) })).sort((a, b) => a.distance - b.distance)[0];
    }

    function openRoomDialog(room = null, rectangle = null) {
      draftRect = rectangle || (room ? { x: room.x, y: room.y, w: room.w, h: room.h } : null);
      if (!draftRect) return;
      $('roomDialogTitle').textContent = room ? 'Editar estancia' : 'Nueva estancia';
      elements.roomId.value = room?.id || '';
      elements.roomType.value = room?.type || 'bedroom';
      elements.roomName.value = room?.name || '';
      elements.roomConditioned.checked = room?.conditioned ?? true;
      elements.roomCeiling.value = room?.ceilingHeightM || 2.5;
      elements.roomOccupancy.value = room?.occupancy ?? 1;
      elements.roomManualArea.value = room?.manualAreaM2 || '';
      elements.roomManualLoad.value = room?.manualLoadFg || '';
      updateRoomGeometry();
      elements.roomDialog.showModal();
      setTimeout(() => elements.roomName.focus(), 40);
    }

    function updateRoomGeometry() {
      if (!draftRect) return;
      const widthM = draftRect.w * state.cellSizeM;
      const heightM = draftRect.h * state.cellSizeM;
      elements.roomGeometrySummary.innerHTML = `<span>Medida dibujada</span><strong>${formatNumber(widthM, 2)} × ${formatNumber(heightM, 2)} m</strong><b>${formatNumber(widthM * heightM, 1)} m²</b>`;
    }

    function removeRoom(id) {
      commit({ ...state, rooms: state.rooms.filter(room => room.id !== id), outlets: state.outlets.filter(outlet => outlet.roomId !== id) }, { kind: 'project' });
    }

    function moveRoom(id, dx, dy) {
      const room = state.rooms.find(item => item.id === id);
      if (!room) return;
      const moved = { ...room, x: clamp(room.x + dx, 0, state.gridCols - room.w), y: clamp(room.y + dy, 0, state.gridRows - room.h) };
      if (state.rooms.some(other => other.id !== id && roomOverlap(moved, other))) {
        elements.drawingMessage.querySelector('p').textContent = 'No se puede mover: esa posición invade otra estancia.';
        return;
      }
      const offsetX = moved.x - room.x, offsetY = moved.y - room.y;
      commit({ ...state, rooms: state.rooms.map(item => item.id === id ? moved : item), outlets: state.outlets.map(outlet => outlet.roomId === id ? { ...outlet, x: outlet.x + offsetX, y: outlet.y + offsetY } : outlet) }, selected);
    }

    function handleCanvas(event) {
      const position = pointerPoint(event);
      const target = event.target.closest('[data-kind]');
      if (tool === 'select') {
        if (!target) selected = { kind: 'project' };
        else if (target.dataset.kind === 'room') selected = { kind: 'room', id: target.dataset.id };
        else if (target.dataset.kind === 'machine') selected = { kind: 'machine' };
        else if (target.dataset.kind === 'outlet') selected = { kind: 'outlet', id: target.dataset.id };
        else if (target.dataset.kind === 'section' || target.dataset.kind === 'edge') selected = { kind: 'section', id: target.dataset.id || target.dataset.sectionId };
        render();
        return;
      }
      if (tool === 'room') {
        if (!roomStart) {
          roomStart = position;
          elements.drawingMessage.querySelector('p').textContent = 'Primera esquina marcada. Toca ahora la esquina opuesta.';
          renderPlan();
          return;
        }
        const rectangle = { x: Math.min(roomStart.x, position.x), y: Math.min(roomStart.y, position.y), w: Math.abs(position.x - roomStart.x), h: Math.abs(position.y - roomStart.y) };
        roomStart = null;
        if (!rectangle.w || !rectangle.h) { elements.drawingMessage.querySelector('p').textContent = 'La estancia necesita al menos un cuadrado de ancho y de fondo.'; renderPlan(); return; }
        if (state.rooms.some(room => roomOverlap(rectangle, room))) { elements.drawingMessage.querySelector('p').textContent = 'Ese espacio se superpone con otra estancia.'; renderPlan(); return; }
        openRoomDialog(null, rectangle);
        renderPlan();
        return;
      }
      if (tool === 'machine') {
        commit({ ...state, machine: position }, { kind: 'machine' });
        setTool('duct');
        routeAnchor = position;
        elements.finishRoute.hidden = false;
        elements.drawingMessage.querySelector('p').textContent = 'Máquina colocada. Marca ahora el recorrido del conducto.';
        renderPlan();
        return;
      }
      if (tool === 'duct') {
        if (!routeAnchor) { routeAnchor = position; elements.finishRoute.hidden = false; renderPlan(); return; }
        const additions = routeEdgesFromPoints(routeAnchor, position, true);
        const edgeMap = new Map(state.routeEdges.map(edge => [edgeKey(edge.a, edge.b), edge]));
        additions.forEach(edge => edgeMap.set(edgeKey(edge.a, edge.b), edge));
        routeAnchor = position;
        commit({ ...state, routeEdges: [...edgeMap.values()] }, selected);
        elements.finishRoute.hidden = false;
        return;
      }
      if (tool === 'outlet') {
        const room = roomAt(position);
        if (!room) { elements.drawingMessage.querySelector('p').textContent = 'La rejilla debe colocarse dentro de una estancia.'; return; }
        if (!room.conditioned) { elements.drawingMessage.querySelector('p').textContent = `${room.name} está marcada como no climatizada.`; return; }
        const outlet = { id: state.outlets.find(item => item.roomId === room.id)?.id || `outlet-${Date.now()}`, roomId: room.id, ...position };
        commit({ ...state, outlets: [...state.outlets.filter(item => item.roomId !== room.id), outlet] }, { kind: 'outlet', id: outlet.id });
        return;
      }
      if (tool === 'erase') {
        if (target?.dataset.kind === 'room') { removeRoom(target.dataset.id); return; }
        if (target?.dataset.kind === 'machine') { commit({ ...state, machine: null }, { kind: 'project' }); return; }
        if (target?.dataset.kind === 'outlet') { commit({ ...state, outlets: state.outlets.filter(item => item.id !== target.dataset.id) }, { kind: 'project' }); return; }
        const nearest = nearestEdge(position);
        if (nearest && nearest.distance <= .65) commit({ ...state, routeEdges: state.routeEdges.filter(edge => edgeKey(edge.a, edge.b) !== edgeKey(nearest.edge.a, nearest.edge.b)) }, { kind: 'project' });
      }
    }

    document.querySelectorAll('[data-tool]').forEach(button => button.addEventListener('click', () => setTool(button.dataset.tool)));
    elements.planStage.addEventListener('click', handleCanvas);
    elements.finishRoute.addEventListener('click', () => { routeAnchor = null; elements.finishRoute.hidden = true; elements.drawingMessage.querySelector('p').textContent = 'Recorrido finalizado. Puedes empezar otra derivación desde cualquier punto existente.'; renderPlan(); });
    $('undoProject').addEventListener('click', undo);
    $('redoProject').addEventListener('click', redo);
    $('zoomIn').addEventListener('click', () => { zoom = clamp(zoom + .12, .3, 2); applyZoom(); });
    $('zoomOut').addEventListener('click', () => { zoom = clamp(zoom - .12, .3, 2); applyZoom(); });
    $('zoomFit').addEventListener('click', fitPlan);
    $('helpToggle').addEventListener('click', () => $('toolHelp').classList.toggle('is-hidden'));
    [elements.projectName, elements.cellSize, elements.planWidth, elements.planHeight, elements.machineCapacity, elements.ductHeight, elements.grilleHeight, elements.loadPerM2, elements.airflowPer9000, elements.areaPer9000, elements.grilleMultiplier].forEach(input => {
      input.addEventListener(input === elements.projectName ? 'input' : 'change', updateProjectSettings);
    });

    elements.roomType.addEventListener('change', () => {
      const definition = ROOM_TYPES[elements.roomType.value];
      if (!elements.roomName.value.trim()) elements.roomName.value = definition.label;
      if (!elements.roomId.value) elements.roomConditioned.checked = definition.conditioned;
    });
    $('closeRoomDialog').addEventListener('click', () => elements.roomDialog.close());
    $('cancelRoom').addEventListener('click', () => elements.roomDialog.close());
    elements.roomDialog.addEventListener('click', event => { if (event.target === elements.roomDialog) elements.roomDialog.close(); });
    elements.roomForm.addEventListener('submit', event => {
      event.preventDefault();
      if (!draftRect) return;
      const id = elements.roomId.value || `room-${Date.now()}-${Math.random().toString(16).slice(2, 6)}`;
      const room = { id, ...draftRect, type: elements.roomType.value, name: elements.roomName.value.trim() || ROOM_TYPES[elements.roomType.value].label, conditioned: elements.roomConditioned.checked, ceilingHeightM: elements.roomCeiling.value, occupancy: elements.roomOccupancy.value, manualAreaM2: elements.roomManualArea.value, manualLoadFg: elements.roomManualLoad.value, ventilationRole: state.rooms.find(item => item.id === id)?.ventilationRole || 'none' };
      const others = state.rooms.filter(item => item.id !== id);
      if (others.some(item => roomOverlap(room, item))) { elements.roomGeometrySummary.textContent = 'La estancia se superpone con otra.'; return; }
      elements.roomDialog.close();
      commit({ ...state, rooms: [...others, room] }, { kind: 'room', id });
      draftRect = null;
      setTool('room');
    });

    elements.selectionPanel.addEventListener('click', event => {
      const action = event.target.closest('[data-selection-action]')?.dataset.selectionAction;
      if (!action) return;
      if (selected.kind === 'room') {
        if (action === 'edit') openRoomDialog(state.rooms.find(room => room.id === selected.id));
        if (action === 'delete') removeRoom(selected.id);
        if (action === 'up') moveRoom(selected.id, 0, -1);
        if (action === 'down') moveRoom(selected.id, 0, 1);
        if (action === 'left') moveRoom(selected.id, -1, 0);
        if (action === 'right') moveRoom(selected.id, 1, 0);
      }
      if (action === 'delete-machine') commit({ ...state, machine: null }, { kind: 'project' });
      if (action === 'delete-outlet') commit({ ...state, outlets: state.outlets.filter(outlet => outlet.id !== selected.id) }, { kind: 'project' });
    });
    elements.roomList.addEventListener('click', event => {
      const button = event.target.closest('[data-overview-room]');
      if (!button) return;
      selected = { kind: 'room', id: button.dataset.overviewRoom };
      setTool('select');
      render();
      elements.selectionPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
    elements.networkResults.addEventListener('click', event => {
      const button = event.target.closest('[data-network-section]');
      if (!button) return;
      selected = { kind: 'section', id: button.dataset.networkSection };
      setTool('select');
      render();
      elements.selectionPanel.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });

    $('loadExample').addEventListener('click', () => { if (!confirm('¿Cargar la vivienda de ejemplo y sustituir el proyecto actual?')) return; commit(exampleState(), { kind: 'project' }); setTimeout(fitPlan, 50); });
    $('clearProject').addEventListener('click', () => { if (!confirm('¿Empezar un plano vacío? El proyecto actual se podrá recuperar con Deshacer.')) return; commit(emptyState(), { kind: 'project' }); setTool('room'); });
    $('printProject').addEventListener('click', () => window.print());
    $('exportProject').addEventListener('click', () => {
      const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `${(state.projectName || 'proyecto-conductos').replace(/[^a-z0-9áéíóúñ_-]+/gi, '-').toLowerCase()}.json`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(link.href), 1000);
    });
    $('importProject').addEventListener('change', async event => {
      const file = event.target.files?.[0];
      if (!file) return;
      try {
        const imported = normalizeState(JSON.parse(await file.text()));
        commit(imported, { kind: 'project' });
        setTimeout(fitPlan, 50);
      } catch (_) {
        alert('El archivo no contiene un proyecto válido.');
      } finally {
        event.target.value = '';
      }
    });
    window.addEventListener('resize', () => { if (window.innerWidth < 760) fitPlan(); });
    window.addEventListener('keydown', event => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') { event.preventDefault(); event.shiftKey ? redo() : undo(); }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'y') { event.preventDefault(); redo(); }
      if (event.key === 'Escape') { roomStart = routeAnchor = null; renderPlan(); }
    });

    syncProjectInputs();
    render();
    requestAnimationFrame(fitPlan);
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initBrowser);
    else initBrowser();
  }

  return { DEFAULTS, ROOM_TYPES, normalizeState, emptyState, exampleState, sizeDuct, calculateProject, renderPlanSvg, routeEdgesFromPoints, roundUp, roomOverlap };
});
