(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.STDuctDesigner = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';

  const STORAGE_KEY = 'st.ductDesigner.v3';
  const LEGACY_STORAGE_KEY = 'st.ductDesigner.v2';
  const CELL_PX = 44;

  /* Criterios internos del método práctico. No forman parte de la interfaz. */
  const DESIGN = Object.freeze({
    loadPerM2: 150,
    airflowPer9000: 1200,
    areaPer9000: 900,
    ductHeightCm: 25,
    grilleHeightCm: 15,
    grilleMultiplier: 2,
    minimumDuctWidthCm: 10,
    minimumGrilleWidthCm: 20,
  });

  const DEFAULTS = Object.freeze({
    schemaVersion: 3,
    workflowStep: 1,
    projectName: 'Vivienda',
    systemMode: 'climate',
    cellSizeM: .5,
    gridCols: 24,
    gridRows: 18,
  });

  const ROOM_TYPES = Object.freeze({
    bedroom: { label: 'Dormitorio', short: 'DORMITORIO', grille: false, color: '#00c8ff' },
    living: { label: 'Salón / comedor', short: 'SALÓN', grille: false, color: '#ffe438' },
    kitchen: { label: 'Cocina', short: 'COCINA', grille: false, color: '#ff7a00' },
    office: { label: 'Oficina / despacho', short: 'OFICINA', grille: false, color: '#00ead0' },
    bathroom: { label: 'Baño', short: 'BAÑO', grille: false, color: '#7f8fa5' },
    hallway: { label: 'Pasillo / distribuidor', short: 'PASILLO', grille: false, color: '#63758d' },
    utility: { label: 'Lavadero / zona técnica', short: 'TÉCNICO', grille: false, color: '#ff3fa7' },
    other: { label: 'Otra estancia', short: 'ESTANCIA', grille: false, color: '#51ff7d' },
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

  function parsePointKey(value) {
    const [x, y] = String(value).split(',').map(Number);
    return { x, y };
  }

  function edgeKey(a, b) {
    const one = pointKey(a);
    const two = pointKey(b);
    return one < two ? `${one}|${two}` : `${two}|${one}`;
  }

  function normalizeState(input = {}) {
    const gridCols = clamp(Math.round(finite(input.gridCols, DEFAULTS.gridCols)), 8, 60);
    const gridRows = clamp(Math.round(finite(input.gridRows, DEFAULTS.gridRows)), 8, 50);
    const ids = new Set();
    const rooms = (Array.isArray(input.rooms) ? input.rooms : []).slice(0, 80).map((room, index) => {
      const type = ROOM_TYPES[room?.type] ? room.type : 'other';
      const x = clamp(Math.round(finite(room?.x)), 0, gridCols - 1);
      const y = clamp(Math.round(finite(room?.y)), 0, gridRows - 1);
      const w = clamp(Math.round(finite(room?.w, 2)), 1, gridCols - x);
      const h = clamp(Math.round(finite(room?.h, 2)), 1, gridRows - y);
      let id = String(room?.id || `room-${index + 1}`).slice(0, 60);
      while (ids.has(id)) id = `${id}-${index + 1}`;
      ids.add(id);
      return {
        id, type, x, y, w, h,
        name: String(room?.name || ROOM_TYPES[type].label).slice(0, 35),
        conditioned: room?.conditioned === undefined ? ROOM_TYPES[type].grille : Boolean(room.conditioned),
        ceilingHeightM: 2.5,
        ventilationRole: room?.ventilationRole || (type === 'bathroom' || type === 'kitchen' ? 'extract' : type === 'hallway' ? 'transfer' : 'none'),
      };
    });
    return {
      ...DEFAULTS,
      workflowStep: clamp(Math.round(finite(input.workflowStep, input.machine ? 3 : 1)), 1, 3),
      projectName: String(input.projectName || DEFAULTS.projectName).slice(0, 70),
      cellSizeM: [.25, .5, 1].includes(finite(input.cellSizeM)) ? finite(input.cellSizeM) : DEFAULTS.cellSizeM,
      gridCols,
      gridRows,
      rooms,
      machine: input.machine ? point(input.machine, gridCols, gridRows) : null,
    };
  }

  function emptyState() {
    return normalizeState({ ...DEFAULTS, rooms: [], machine: null, workflowStep: 1 });
  }

  function exampleState() {
    return normalizeState({
      ...DEFAULTS,
      workflowStep: 3,
      rooms: [
        { id: 'bed-1', type: 'bedroom', name: 'Dormitorio 1', x: 1, y: 1, w: 7, h: 6, conditioned: true },
        { id: 'bed-2', type: 'bedroom', name: 'Dormitorio 2', x: 8, y: 1, w: 7, h: 6, conditioned: true },
        { id: 'kitchen', type: 'kitchen', name: 'Cocina', x: 15, y: 1, w: 8, h: 6, conditioned: false },
        { id: 'bath', type: 'bathroom', name: 'Baño', x: 1, y: 7, w: 6, h: 5, conditioned: false },
        { id: 'hall', type: 'hallway', name: 'Pasillo', x: 7, y: 7, w: 4, h: 10, conditioned: false },
        { id: 'living', type: 'living', name: 'Salón comedor', x: 11, y: 7, w: 12, h: 10, conditioned: true },
      ],
      machine: { x: 9, y: 9 },
    });
  }

  function roomOverlap(one, two) {
    return one.x < two.x + two.w && one.x + one.w > two.x && one.y < two.y + two.h && one.y + one.h > two.y;
  }

  function roomArea(room, state) {
    return room.w * state.cellSizeM * room.h * state.cellSizeM;
  }

  function airflowForLoad(loadFg) {
    return loadFg * DESIGN.airflowPer9000 / 9000;
  }

  function sizeDuct(loadFg) {
    const requiredAreaCm2 = loadFg * DESIGN.areaPer9000 / 9000;
    const rawWidthCm = requiredAreaCm2 / DESIGN.ductHeightCm;
    const widthCm = loadFg > 0 ? roundUp(Math.max(DESIGN.minimumDuctWidthCm, rawWidthCm), 1) : 0;
    const actualAreaM2 = widthCm * DESIGN.ductHeightCm / 10000;
    const airflowM3h = airflowForLoad(loadFg);
    const velocityMps = actualAreaM2 > 0 ? airflowM3h / (actualAreaM2 * 3600) : 0;
    return { widthCm, heightCm: DESIGN.ductHeightCm, requiredAreaCm2, airflowM3h, velocityMps };
  }

  function enrichRoom(room, state) {
    const areaM2 = roomArea(room, state);
    const loadFg = room.conditioned ? areaM2 * DESIGN.loadPerM2 : 0;
    const airflowM3h = airflowForLoad(loadFg);
    const branchDuct = sizeDuct(loadFg);
    const grilleAreaCm2 = branchDuct.requiredAreaCm2 * DESIGN.grilleMultiplier;
    const grilleWidthCm = loadFg > 0 ? roundUp(Math.max(DESIGN.minimumGrilleWidthCm, grilleAreaCm2 / DESIGN.grilleHeightCm), 5) : 0;
    return {
      ...room,
      typeLabel: ROOM_TYPES[room.type].label,
      areaM2,
      volumeM3: areaM2 * room.ceilingHeightM,
      loadFg,
      airflowM3h,
      branchDuct,
      grille: { widthCm: grilleWidthCm, heightCm: DESIGN.grilleHeightCm },
    };
  }

  function boundaryPoints(room) {
    const points = [];
    for (let x = room.x; x <= room.x + room.w; x += 1) {
      points.push({ x, y: room.y }, { x, y: room.y + room.h });
    }
    for (let y = room.y + 1; y < room.y + room.h; y += 1) {
      points.push({ x: room.x, y }, { x: room.x + room.w, y });
    }
    return points;
  }

  function pointInsideRoom(value, room) {
    return value.x > room.x && value.x < room.x + room.w && value.y > room.y && value.y < room.y + room.h;
  }

  function routeCost(a, b, rooms, existingEdges) {
    const key = edgeKey(a, b);
    if (existingEdges.has(key)) return .18;
    const midpoint = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
    const crossed = rooms.find(room => pointInsideRoom(midpoint, room));
    if (!crossed) return 1.8;
    if (crossed.type === 'hallway') return .42;
    if (crossed.type === 'utility' || crossed.type === 'bathroom') return .85;
    return crossed.conditioned ? 12 : 1.2;
  }

  function findAutomaticPath(state, targetRoom, existingEdges) {
    const start = state.machine;
    if (!start) return null;
    const targets = boundaryPoints(targetRoom);
    const targetKeys = new Set(targets.map(pointKey));
    const heuristic = value => targets.reduce((minimum, target) => Math.min(minimum, Math.abs(value.x - target.x) + Math.abs(value.y - target.y)), Infinity);
    const startKey = pointKey(start);
    const open = [{ key: startKey, point: start, score: heuristic(start) }];
    const openKeys = new Set([startKey]);
    const cost = new Map([[startKey, 0]]);
    const previous = new Map();
    while (open.length) {
      open.sort((one, two) => one.score - two.score);
      const current = open.shift();
      openKeys.delete(current.key);
      if (targetKeys.has(current.key)) {
        const path = [current.point];
        let cursor = current.key;
        while (previous.has(cursor)) {
          cursor = previous.get(cursor);
          path.push(parsePointKey(cursor));
        }
        return path.reverse();
      }
      const neighbours = [
        { x: current.point.x + 1, y: current.point.y }, { x: current.point.x - 1, y: current.point.y },
        { x: current.point.x, y: current.point.y + 1 }, { x: current.point.x, y: current.point.y - 1 },
      ].filter(item => item.x >= 0 && item.y >= 0 && item.x <= state.gridCols && item.y <= state.gridRows);
      neighbours.forEach(next => {
        const nextKey = pointKey(next);
        const nextCost = cost.get(current.key) + routeCost(current.point, next, state.rooms, existingEdges);
        if (nextCost >= (cost.get(nextKey) ?? Infinity)) return;
        cost.set(nextKey, nextCost);
        previous.set(nextKey, current.key);
        const score = nextCost + heuristic(next);
        const existing = open.find(item => item.key === nextKey);
        if (existing) { existing.point = next; existing.score = score; }
        else if (!openKeys.has(nextKey)) { open.push({ key: nextKey, point: next, score }); openKeys.add(nextKey); }
      });
    }
    return null;
  }

  function automaticNetwork(input = {}) {
    const state = normalizeState(input);
    if (!state.machine) return { routeEdges: [], outlets: [] };
    const selectedRooms = state.rooms.filter(room => room.conditioned).sort((one, two) => {
      const distance = room => Math.abs((room.x + room.w / 2) - state.machine.x) + Math.abs((room.y + room.h / 2) - state.machine.y);
      return distance(two) - distance(one);
    });
    const edges = new Map();
    const outlets = [];
    selectedRooms.forEach((room, index) => {
      const path = findAutomaticPath(state, room, edges);
      if (!path?.length) return;
      for (let pointIndex = 1; pointIndex < path.length; pointIndex += 1) {
        const a = path[pointIndex - 1];
        const b = path[pointIndex];
        edges.set(edgeKey(a, b), pointKey(a) < pointKey(b) ? { a, b } : { a: b, b: a });
      }
      outlets.push({ id: `outlet-${index + 1}-${room.id}`, roomId: room.id, ...path.at(-1) });
    });
    return { routeEdges: [...edges.values()], outlets };
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
    const generated = automaticNetwork(state);
    const outletMap = new Map(generated.outlets.map(outlet => [outlet.roomId, outlet]));
    const graph = buildGraph(generated.routeEdges);
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

    const activeEdges = generated.routeEdges.map(edge => {
      const key = edgeKey(edge.a, edge.b);
      const roomIds = [...(assignments.get(key) || [])].sort();
      const loadFg = roomIds.reduce((sum, id) => sum + (roomMap.get(id)?.loadFg || 0), 0);
      return { ...edge, key, roomIds, loadFg, ...sizeDuct(loadFg) };
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
      sections.push({ id: '', roomIds, rooms: roomIds.map(id => roomMap.get(id)).filter(Boolean), edges: component, representative: sample, lengthM: component.length * state.cellSizeM, loadFg, ...sizeDuct(loadFg) });
    }));
    sections.sort((one, two) => two.loadFg - one.loadFg || two.lengthM - one.lengthM).forEach((section, index) => { section.id = `T${index + 1}`; });
    const sectionByEdge = new Map();
    sections.forEach(section => section.edges.forEach(edge => sectionByEdge.set(edge.key, section)));
    activeEdges.forEach(edge => { edge.sectionId = sectionByEdge.get(edge.key)?.id || ''; });

    const selectedRooms = rooms.filter(room => room.conditioned);
    const connectedRooms = selectedRooms.filter(room => roomConnections.get(room.id)?.connected);
    const loadFg = selectedRooms.reduce((sum, room) => sum + room.loadFg, 0);
    const airflowM3h = selectedRooms.reduce((sum, room) => sum + room.airflowM3h, 0);
    const warnings = [];
    if (!rooms.length) warnings.push({ level: 'info', text: 'Dibuja las estancias para comenzar.' });
    if (rooms.some((room, index) => rooms.slice(index + 1).some(other => roomOverlap(room, other)))) warnings.push({ level: 'danger', text: 'Hay estancias superpuestas.' });
    if (rooms.length && !selectedRooms.length) warnings.push({ level: 'warn', text: 'Marca al menos una habitación con rejilla.' });
    if (selectedRooms.length && !state.machine) warnings.push({ level: 'info', text: 'Toca en el plano la posición de la unidad interior.' });
    if (state.machine && connectedRooms.length === selectedRooms.length && selectedRooms.length) warnings.push({ level: 'ok', text: 'El recorrido automático conecta todas las rejillas seleccionadas.' });
    sections.forEach(section => {
      if (section.velocityMps > 5.2) warnings.push({ level: 'warn', text: `${section.id}: velocidad elevada (${formatNumber(section.velocityMps, 1)} m/s).` });
    });
    return {
      state, rooms, roomMap, outletMap, roomConnections, activeEdges, sections,
      totals: {
        rooms: rooms.length,
        selectedRooms: selectedRooms.length,
        connectedRooms: connectedRooms.length,
        areaM2: rooms.reduce((sum, room) => sum + room.areaM2, 0),
        conditionedAreaM2: selectedRooms.reduce((sum, room) => sum + room.areaM2, 0),
        loadFg,
        airflowM3h,
        suggestedCapacityFg: loadFg > 0 ? roundUp(loadFg, 500) : 0,
        mainDuct: sizeDuct(loadFg),
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
    const step = options.step || state.workflowStep;
    const width = state.gridCols * CELL_PX;
    const height = state.gridRows * CELL_PX;
    const px = value => value * CELL_PX;
    const parts = [`<svg class="installation-plan" viewBox="0 0 ${width} ${height}" role="img" aria-label="Plano de ${escapeHtml(state.projectName)}">`,
      `<defs><pattern id="minorGrid" width="${CELL_PX}" height="${CELL_PX}" patternUnits="userSpaceOnUse"><path d="M ${CELL_PX} 0 L 0 0 0 ${CELL_PX}"/></pattern><filter id="planGlow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter><pattern id="notSelected" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="12"/></pattern></defs>`,
      `<rect class="plan-background" width="${width}" height="${height}"/><rect class="plan-grid" width="${width}" height="${height}"/>`];

    result.rooms.forEach(room => {
      const x = px(room.x), y = px(room.y), w = px(room.w), h = px(room.h);
      const centerX = x + w / 2, centerY = y + h / 2;
      const small = w < 180 || h < 125;
      parts.push(`<g class="plan-room room-type-${room.type}${room.conditioned ? ' has-grille' : ' no-grille'}" data-kind="room" data-id="${escapeHtml(room.id)}"><rect class="room-fill" x="${x + 2}" y="${y + 2}" width="${Math.max(1, w - 4)}" height="${Math.max(1, h - 4)}" rx="5"/><rect class="room-wall" x="${x + 2}" y="${y + 2}" width="${Math.max(1, w - 4)}" height="${Math.max(1, h - 4)}" rx="5"/>${step >= 2 && !room.conditioned ? `<rect class="room-hatch" x="${x + 5}" y="${y + 5}" width="${Math.max(1, w - 10)}" height="${Math.max(1, h - 10)}"/>` : ''}<text class="room-type-label" x="${centerX}" y="${centerY - (small ? 10 : 24)}" text-anchor="middle">${escapeHtml(ROOM_TYPES[room.type].short)}</text><text class="room-name-label" x="${centerX}" y="${centerY + (small ? 9 : 1)}" text-anchor="middle">${escapeHtml(room.name)}</text><text class="room-area-label" x="${centerX}" y="${centerY + (small ? 27 : 24)}" text-anchor="middle">${formatNumber(room.areaM2, 1)} m²${step >= 2 ? room.conditioned ? ' · CON REJILLA' : ' · SIN REJILLA' : ''}</text>`);
      if (step === 1) parts.push(`<g class="room-delete" data-kind="room-delete" data-id="${escapeHtml(room.id)}" transform="translate(${x + w - 20} ${y + 20})"><circle class="room-delete-hit" r="28"/><circle class="room-delete-button" r="13"/><path d="M-4-4l8 8M4-4l-8 8"/></g>`);
      if (step === 2) parts.push(`<g class="zone-toggle${room.conditioned ? ' is-checked' : ''}" data-kind="zone-toggle" data-id="${escapeHtml(room.id)}" transform="translate(${x + w - 25} ${y + 25})"><rect class="zone-hit" x="-30" y="-30" width="60" height="60" rx="14"/><rect class="zone-box" x="-17" y="-17" width="34" height="34" rx="8"/><path d="M-8 0l6 7L9-8"/><title>${room.conditioned ? 'Quitar rejilla' : 'Poner rejilla'} en ${escapeHtml(room.name)}</title></g>`);
      parts.push('</g>');
    });

    if (step === 3) {
      result.activeEdges.forEach(edge => {
        const routeWidth = clamp(7 + edge.widthCm * .28, 9, 24);
        parts.push(`<line class="route-edge" x1="${px(edge.a.x)}" y1="${px(edge.a.y)}" x2="${px(edge.b.x)}" y2="${px(edge.b.y)}" style="--route-width:${routeWidth}px"><title>${edge.sectionId}: ${edge.widthCm} × ${edge.heightCm} cm</title></line>`);
      });
      result.sections.forEach(section => {
        const edge = section.representative;
        const x = px((edge.a.x + edge.b.x) / 2), y = px((edge.a.y + edge.b.y) / 2);
        parts.push(`<g class="section-label"><rect x="${x - 51}" y="${y - 15}" width="102" height="30" rx="8"/><text x="${x}" y="${y + 5}" text-anchor="middle">${section.id} · ${section.widthCm}×${section.heightCm}</text></g>`);
      });
      result.rooms.forEach(room => {
        const outlet = result.outletMap.get(room.id);
        if (!outlet) return;
        parts.push(`<g class="plan-outlet" transform="translate(${px(outlet.x)} ${px(outlet.y)})"><rect x="-22" y="-8" width="44" height="16" rx="4"/><path d="M-15-3h30M-15 2h30"/><title>${escapeHtml(room.name)} · rejilla ${room.grille.widthCm} × ${room.grille.heightCm} cm</title></g>`);
      });
      if (state.machine) parts.push(`<g class="plan-machine" transform="translate(${px(state.machine.x)} ${px(state.machine.y)})"><rect x="-35" y="-27" width="70" height="54" rx="12"/><circle cx="0" cy="0" r="15"/><path d="M0-15c9 3 11 8 5 14M15 0c-3 9-8 11-14 5M0 15c-9-3-11-8-5-14M-15 0c3-9 8-11 14-5"/><text x="0" y="-37" text-anchor="middle">UNIDAD INTERIOR</text></g>`);
    }

    if (options.roomStart) parts.push(`<g class="drawing-anchor"><circle cx="${px(options.roomStart.x)}" cy="${px(options.roomStart.y)}" r="12"/><text x="${px(options.roomStart.x) + 18}" y="${px(options.roomStart.y) - 16}">Ahora marca la esquina opuesta</text></g>`);
    parts.push(`<g class="scale-marker" transform="translate(${width - 150} ${height - 25})"><line x1="0" y1="0" x2="${CELL_PX * 2}" y2="0"/><path d="M0-6v12M${CELL_PX * 2}-6v12"/><text x="${CELL_PX}" y="-10" text-anchor="middle">${formatNumber(state.cellSizeM * 2, 2)} m</text></g>`);
    parts.push('</svg>');
    return { svg: parts.join(''), width, height };
  }

  function initBrowser() {
    if (typeof document === 'undefined' || !document.getElementById('planStage')) return;
    const $ = id => document.getElementById(id);
    const elements = {
      roomType: $('roomType'), cellSize: $('cellSize'), stepOne: $('stepOneControls'), stepTwo: $('stepTwoControls'), stepThree: $('stepThreeControls'),
      message: $('assistantMessage'), planStatus: $('planStatus'), planScroll: $('planScroll'), planStage: $('planStage'), planSummary: $('planSummary'), continueButton: $('continueButton'),
      automaticResult: $('automaticResult'), networkStatus: $('networkStatus'), resultSummary: $('resultSummary'), alerts: $('ductAlerts'), networkResults: $('networkResults'), roomResults: $('roomResults'),
      undo: $('undoProject'), redo: $('redoProject'),
    };
    let state = loadState();
    let result = calculateProject(state);
    let roomStart = null;
    let zoom = 1;
    const history = [];
    const future = [];

    function loadState() {
      try {
        const saved = localStorage.getItem(STORAGE_KEY) || localStorage.getItem(LEGACY_STORAGE_KEY);
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
      if (history.length > 50) history.shift();
      future.length = 0;
      state = normalizeState(next);
      roomStart = null;
      render();
    }

    function undo() {
      if (!history.length) return;
      future.push(JSON.stringify(state));
      state = normalizeState(JSON.parse(history.pop()));
      roomStart = null;
      render();
    }

    function redo() {
      if (!future.length) return;
      history.push(JSON.stringify(state));
      state = normalizeState(JSON.parse(future.pop()));
      roomStart = null;
      render();
    }

    function setStep(step) {
      if (step === 2 && !state.rooms.length) return;
      if (step === 3 && !state.rooms.some(room => room.conditioned)) return;
      commit({ ...state, workflowStep: step, machine: step < 3 ? null : state.machine });
      if (step === 3 && !state.machine) {
        elements.planScroll.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }

    function nameForType(type) {
      const definition = ROOM_TYPES[type];
      const count = state.rooms.filter(room => room.type === type).length + 1;
      const repeated = ['bedroom', 'bathroom', 'office', 'other'].includes(type);
      return repeated ? `${definition.label} ${count}` : count > 1 ? `${definition.label} ${count}` : definition.label;
    }

    function pointerPoint(event) {
      const svg = elements.planStage.querySelector('svg');
      const svgPoint = svg.createSVGPoint();
      svgPoint.x = event.clientX;
      svgPoint.y = event.clientY;
      const local = svgPoint.matrixTransform(svg.getScreenCTM().inverse());
      return point({ x: local.x / CELL_PX, y: local.y / CELL_PX }, state.gridCols, state.gridRows);
    }

    function renderPlan() {
      const rendered = renderPlanSvg(result, { step: state.workflowStep, roomStart });
      elements.planStage.innerHTML = rendered.svg;
      elements.planStage.dataset.width = rendered.width;
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
      const minimumZoom = window.innerWidth < 760 ? .55 : .34;
      zoom = clamp(Math.max(300, elements.planScroll.clientWidth - 12) / width, minimumZoom, 1.35);
      applyZoom();
      requestAnimationFrame(() => { elements.planScroll.scrollLeft = Math.max(0, (elements.planScroll.scrollWidth - elements.planScroll.clientWidth) / 2); });
    }

    function renderSteps() {
      document.querySelectorAll('[data-go-step]').forEach(button => {
        const step = Number(button.dataset.goStep);
        button.disabled = step === 2 ? !state.rooms.length : step === 3 ? !state.rooms.some(room => room.conditioned) : false;
        button.classList.toggle('is-active', step === state.workflowStep);
        button.classList.toggle('is-complete', step < state.workflowStep || (step === 3 && Boolean(state.machine)));
      });
      elements.stepOne.hidden = state.workflowStep !== 1;
      elements.stepTwo.hidden = state.workflowStep !== 2;
      elements.stepThree.hidden = state.workflowStep !== 3;
      elements.cellSize.value = String(state.cellSizeM);
    }

    function renderMessage() {
      const marker = elements.message.querySelector('span');
      const copy = elements.message.querySelector('p');
      marker.textContent = state.workflowStep;
      if (state.workflowStep === 1) {
        copy.innerHTML = roomStart ? '<strong>Primera esquina marcada.</strong> Toca ahora la esquina opuesta.' : '<strong>Elige una estancia y toca dos esquinas.</strong> Se añadirá al plano sin pedir más datos.';
        elements.planStatus.textContent = roomStart ? 'Cerrando estancia' : 'Preparado para dibujar';
      } else if (state.workflowStep === 2) {
        copy.innerHTML = '<strong>Activa o desactiva las casillas del plano.</strong> Solo las habitaciones marcadas recibirán caudal y rejilla.';
        elements.planStatus.textContent = `${result.totals.selectedRooms} habitaciones con rejilla`;
      } else if (!state.machine) {
        copy.innerHTML = '<strong>¿Dónde irá la unidad interior?</strong> Toca su posición y calcularemos automáticamente toda la red.';
        elements.planStatus.textContent = 'Esperando posición de la máquina';
      } else {
        copy.innerHTML = '<strong>Diseño terminado.</strong> Puedes tocar otra posición para comparar un recorrido diferente.';
        elements.planStatus.textContent = 'Recorrido automático calculado';
      }
    }

    function renderFoot() {
      elements.planSummary.innerHTML = `<span><b>${result.totals.rooms}</b> estancias</span><span><b>${formatNumber(result.totals.areaM2, 1)} m²</b> dibujados</span>${state.workflowStep >= 2 ? `<span><b>${result.totals.selectedRooms}</b> con rejilla</span>` : ''}`;
      if (state.workflowStep === 1) {
        elements.continueButton.disabled = !state.rooms.length;
        elements.continueButton.innerHTML = 'Ya he dibujado el plano <span>→</span>';
      } else if (state.workflowStep === 2) {
        elements.continueButton.disabled = !state.rooms.some(room => room.conditioned);
        elements.continueButton.innerHTML = 'Ya he marcado las rejillas <span>→</span>';
      } else if (!state.machine) {
        elements.continueButton.disabled = true;
        elements.continueButton.innerHTML = 'Toca la posición de la máquina';
      } else {
        elements.continueButton.disabled = false;
        elements.continueButton.innerHTML = 'Ver resultados <span>↓</span>';
      }
    }

    function metric(label, value, note, color) {
      return `<article style="--metric-color:${color}"><span>${label}</span><strong>${value}</strong><small>${note}</small></article>`;
    }

    function renderResults() {
      const visible = state.workflowStep === 3 && state.machine && result.totals.selectedRooms > 0;
      elements.automaticResult.hidden = !visible;
      if (!visible) return;
      elements.networkStatus.textContent = result.totals.connectedRooms === result.totals.selectedRooms ? 'RED COMPLETA' : 'REVISAR RECORRIDO';
      elements.resultSummary.innerHTML = [
        metric('Superficie con rejilla', `${formatNumber(result.totals.conditionedAreaM2, 1)} m²`, `${result.totals.selectedRooms} estancias`, '#00c8ff'),
        metric('Necesidad estimada', `${formatNumber(result.totals.suggestedCapacityFg)} frg/h`, 'Dato para seleccionar la máquina', '#ff7a00'),
        metric('Caudal de impulsión', `${formatNumber(result.totals.airflowM3h)} m³/h`, 'Distribuido entre las rejillas', '#51ff7d'),
        metric('Salida principal', `${result.totals.mainDuct.widthCm} × ${result.totals.mainDuct.heightCm} cm`, `${formatNumber(result.totals.mainDuct.velocityMps, 1)} m/s`, '#ff3fa7'),
      ].join('');
      elements.alerts.innerHTML = result.warnings.filter(item => item.level !== 'info').map(item => `<p class="alert-${item.level}"><span>${item.level === 'ok' ? '✓' : '!'}</span>${escapeHtml(item.text)}</p>`).join('');
      elements.networkResults.innerHTML = result.sections.map(section => `<div class="result-row"><b>${section.id}</b><span><strong>${section.rooms.map(room => escapeHtml(room.name)).join(' · ')}</strong><small>${formatNumber(section.lengthM, 1)} m · ${formatNumber(section.airflowM3h)} m³/h</small></span><em>${section.widthCm} × ${section.heightCm} cm</em></div>`).join('');
      elements.roomResults.innerHTML = result.rooms.filter(room => room.conditioned).map(room => `<div class="result-row room-result"><b>▥</b><span><strong>${escapeHtml(room.name)}</strong><small>${formatNumber(room.airflowM3h)} m³/h · ramal ${room.branchDuct.widthCm} × ${room.branchDuct.heightCm} cm</small></span><em>${room.grille.widthCm} × ${room.grille.heightCm} cm</em></div>`).join('');
    }

    function render() {
      result = calculateProject(state);
      renderSteps();
      renderMessage();
      renderPlan();
      renderFoot();
      renderResults();
      elements.undo.disabled = !history.length;
      elements.redo.disabled = !future.length;
      save();
    }

    function handlePlanClick(event) {
      const target = event.target.closest('[data-kind]');
      if (state.workflowStep === 1 && target?.dataset.kind === 'room-delete') {
        commit({ ...state, rooms: state.rooms.filter(room => room.id !== target.dataset.id) });
        return;
      }
      if (state.workflowStep === 2 && target?.dataset.kind === 'zone-toggle') {
        commit({ ...state, rooms: state.rooms.map(room => room.id === target.dataset.id ? { ...room, conditioned: !room.conditioned } : room) });
        return;
      }
      const position = pointerPoint(event);
      if (state.workflowStep === 1) {
        if (!roomStart) { roomStart = position; render(); return; }
        const rectangle = { x: Math.min(roomStart.x, position.x), y: Math.min(roomStart.y, position.y), w: Math.abs(position.x - roomStart.x), h: Math.abs(position.y - roomStart.y) };
        roomStart = null;
        if (!rectangle.w || !rectangle.h) { render(); return; }
        if (state.rooms.some(room => roomOverlap(rectangle, room))) {
          elements.message.querySelector('p').innerHTML = '<strong>Esa zona invade otra estancia.</strong> Elige dos esquinas diferentes.';
          renderPlan();
          return;
        }
        const type = elements.roomType.value;
        const id = `room-${Date.now()}-${Math.random().toString(16).slice(2, 6)}`;
        commit({ ...state, rooms: [...state.rooms, { id, type, name: nameForType(type), ...rectangle, conditioned: ROOM_TYPES[type].grille }] });
        return;
      }
      if (state.workflowStep === 3) {
        commit({ ...state, machine: position });
        setTimeout(() => elements.automaticResult.scrollIntoView({ behavior: 'smooth', block: 'start' }), 250);
      }
    }

    document.querySelectorAll('[data-go-step]').forEach(button => button.addEventListener('click', () => setStep(Number(button.dataset.goStep))));
    elements.planStage.addEventListener('click', handlePlanClick);
    elements.continueButton.addEventListener('click', () => {
      if (state.workflowStep < 3) setStep(state.workflowStep + 1);
      else if (state.machine) elements.automaticResult.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    elements.cellSize.addEventListener('change', () => commit({ ...state, cellSizeM: elements.cellSize.value }));
    elements.undo.addEventListener('click', undo);
    elements.redo.addEventListener('click', redo);
    $('zoomIn').addEventListener('click', () => { zoom = clamp(zoom + .12, .3, 2); applyZoom(); });
    $('zoomOut').addEventListener('click', () => { zoom = clamp(zoom - .12, .3, 2); applyZoom(); });
    $('zoomFit').addEventListener('click', fitPlan);
    $('loadExample').addEventListener('click', () => { if (state.rooms.length && !confirm('¿Sustituir el plano actual por el ejemplo?')) return; commit(exampleState()); setTimeout(fitPlan, 40); });
    $('clearProject').addEventListener('click', () => { if (state.rooms.length && !confirm('¿Empezar un plano nuevo?')) return; commit(emptyState()); });
    $('printProject').addEventListener('click', () => window.print());
    $('moveMachine').addEventListener('click', () => { commit({ ...state, workflowStep: 3, machine: null }); elements.planScroll.scrollIntoView({ behavior: 'smooth', block: 'center' }); });
    $('editZones').addEventListener('click', () => setStep(2));
    window.addEventListener('resize', () => { if (window.innerWidth < 760) fitPlan(); });
    window.addEventListener('keydown', event => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') { event.preventDefault(); event.shiftKey ? redo() : undo(); }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'y') { event.preventDefault(); redo(); }
      if (event.key === 'Escape' && roomStart) { roomStart = null; render(); }
    });

    render();
    requestAnimationFrame(fitPlan);
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initBrowser);
    else initBrowser();
  }

  return { DESIGN, DEFAULTS, ROOM_TYPES, normalizeState, emptyState, exampleState, sizeDuct, automaticNetwork, calculateProject, renderPlanSvg, roundUp, roomOverlap };
});
